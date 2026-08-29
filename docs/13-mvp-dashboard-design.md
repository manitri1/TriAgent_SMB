# 13. SMB 대시보드 MVP 설계 (SPEC-DASHBOARD-001)

`docs/12-mvp-window-options.md`에서 채택한 **옵션 C(경량 커스텀 웹 UI)** 의 상세 설계입니다.
Hermes 내장 CLI 대시보드(`http://127.0.0.1:9128`) 대신, SMB 사장님이 주문/재고/예약/매출/
승인 현황을 한눈에 보고 조작할 수 있는 전용 웹 화면(`smb-dashboard/`)을 새로 만듭니다.

## 1. 왜 새 백엔드가 필요한가

- **Mock POS(`mock-pos/`)는 이미 완전한 REST API**(주문/재고/예약/결제/매출)를 제공하지만
  `CORSMiddleware`가 설정되어 있지 않아 브라우저가 직접 호출할 수 없습니다. 새 백엔드가
  서버 사이드에서 프록시해야 합니다.
- **Hermes gateway는 상태 조회용 REST API가 없습니다.** 프로필 실행은 CLI 서브프로세스
  (`docker compose exec hermes hermes chat --profile <role> -q "..."`)로만 가능하고, HITL
  승인 상태는 Discord 대화 안에만 존재하며 구조화된 저장소가 전혀 없습니다. 따라서 승인
  대기열을 웹에 노출하려면 **이 프로젝트가 처음으로 만드는 구조화 저장소**가 필요합니다.

## 2. 아키텍처

```
                    ┌───────────────────────────────┐
   브라우저  ───────▶│  smb-dashboard (신규, :8652)   │
 (사장님)            │  FastAPI + React/Vite 정적빌드  │
                    │                                 │
                    │  routers/orders,inventory,       │
                    │  reservations,reports  ──────────┼───▶ mock-pos:8080 (기존, 프록시만)
                    │                                 │
                    │  routers/approvals  ────────────┼───▶ data/approvals.json (신규 저장소)
                    └───────────────────────────────┘
                                   ▲
                                   │ POST/GET (code_execution)
                    ┌───────────────────────────────┐
                    │ hermes (coordinator + 워커 6개)  │
                    │ HITL 스킬 3개가 승인 레코드 생성/폴링│
                    └───────────────────────────────┘
                                   │
                                   ▼
                              Discord (기존, 병행 유지)
```

프론트엔드는 빌드타임에 정적 파일로 번들되어 FastAPI가 `StaticFiles`로 서빙합니다 —
별도 nginx 컨테이너 없이 컨테이너 1개로 끝냅니다(`mock-pos/Dockerfile` 스타일 계승).

## 3. API 계약

모든 엔드포인트는 basic-auth(또는 세션 쿠키) 뒤에 있으며, 프론트는 자기 백엔드(`/api/*`)만
호출합니다. 아래 표의 "Mock POS 매핑"은 백엔드가 내부적으로 호출하는 원본 엔드포인트입니다.

### 3.1 주문 / 재고 / 예약 / 매출 (Mock POS 프록시, 읽기 전용)

| 메서드 | 경로 | 설명 | Mock POS 매핑 |
|---|---|---|---|
| GET | `/api/orders/today` | 오늘자 주문 목록 | `GET /v1/stores/{store_id}/orders` (클라이언트에서 날짜 필터) |
| GET | `/api/inventory` | 재고 목록 + 저재고 플래그 | `GET /v1/stores/{store_id}/inventory` |
| GET | `/api/reservations?date=YYYY-MM-DD` | 예약 캘린더용 목록 | `GET /v1/stores/{store_id}/reservations?date=...` |
| GET | `/api/reports/sales?period=today\|week\|month` | 매출 요약 | `GET /v1/stores/{store_id}/reports/sales?period=...` |

> Mock POS `Order`에 날짜별 조회 파라미터가 없으므로(전체 목록만 반환), `/api/orders/today`는
> 백엔드가 전체를 가져온 뒤 `created_at`이 오늘인 항목만 필터링합니다. 데이터가 늘어나
> 성능 문제가 되면 추후 Mock POS 쪽에 `?date=` 파라미터를 추가하는 것으로 개선합니다(MVP
> 범위 밖).

### 3.2 승인 큐 (신규 저장소, 읽기/쓰기)

| 메서드 | 경로 | 설명 | 호출 주체 |
|---|---|---|---|
| POST | `/api/approvals` | 승인 대기 레코드 생성 | coordinator 산하 HITL 스킬 (code_execution) |
| GET | `/api/approvals?status=pending` | 대기열 목록 | 프론트(대시보드 화면) |
| GET | `/api/approvals/{id}` | 단건 상태 조회 | HITL 스킬 폴링 + 프론트 |
| PATCH | `/api/approvals/{id}` | 승인/반려 결정 기록 | 프론트("승인"/"반려" 버튼) |

**요청/응답 필드**

```jsonc
// POST /api/approvals 요청 (HITL 스킬 → 대시보드)
{
  "type": "promo" | "reorder" | "refund",
  "summary": "한 줄 요약 (예: '아메리카노 원두 500개 재입고, 예상 350만원')",
  "details": "전문 — 채널/대상/금액/사유 등 (docs/06 게이트별 요구 항목 포함)",
  "requested_by": "inventory-agent"
}
// 응답: 201, {approval_id, status: "pending", created_at, ...위 필드}

// PATCH /api/approvals/{id} 요청 (사장님 → 대시보드)
{ "status": "approved" | "rejected", "reason": "선택 사유" }
// 응답: 200 정상, 409 이미 결정된 레코드 재결정 시도
```

### 3.3 인증 / 헬스체크

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/health` | 인증 없이 상태 확인(컨테이너 헬스체크용) |
| * | 그 외 전부 | basic-auth 필수 (`DASHBOARD_BASIC_AUTH_USER`/`_PASSWORD`) |

## 4. 화면 구성

| 화면 | 내용 | 데이터 소스 |
|---|---|---|
| 주문 현황 | 오늘자 주문 목록, 상태별 필터(OPEN/COMPLETED/CANCELED/REFUNDED) | `/api/orders/today` |
| 재고 알림 | 전체 재고, `LOW_STOCK_THRESHOLD`(기본 10) 미만 항목 빨간색 강조 | `/api/inventory` |
| 예약 캘린더 | 날짜별 예약 목록(BOOKED/CANCELED) | `/api/reservations` |
| 매출 요약 | 오늘/이번주/이번달 매출·건수 위젯 | `/api/reports/sales` |
| **승인 대기열** | pending 레코드 카드 목록, 각 카드에 "승인"/"반려" 버튼 + 사유 입력 | `/api/approvals` |

## 5. 승인 큐 이중 채널 흐름

기존 [docs/06-hitl-approval-design.md](06-hitl-approval-design.md)의 Discord 대화 흐름은
그대로 유지하고, 대시보드 승인 큐를 **병행 채널**로 추가합니다(대체 아님):

```
[워커 프로필: 임계치 감지]
        │
        ├──▶ POST /api/approvals (대기 레코드 생성)
        │
        ├──▶ Discord 메시지 발송 ("웹 대시보드에서도 승인 가능" 안내 포함)
        │
        ▼
   GET /api/approvals/{id} 폴링 (터미널 호출 타임아웃 60~120초 이내, 수초 간격)
        │
        ├── 웹에서 먼저 결정됨 ──▶ 그 결과로 즉시 진행/중단
        │
        └── 타임아웃까지 미결 ──▶ 기존처럼 Discord 응답 대기 (clarify)
                                        │
                                        ▼
                          결정 시 PATCH /api/approvals/{id}로도 기록
                          (Discord로 결정된 경우도 대시보드 상태를 동기화)
```

두 채널 중 **먼저 도달한 결정이 유효**하며, 동일 레코드에 대한 재결정 시도는 409로
거부됩니다(수용 기준 4, SPEC-DASHBOARD-001 참고). 모든 결정은 기존과 동일하게
`coordinator/MEMORY.md`의 "확정된 승인/반려 이력"에도 한 줄 남습니다.

## 6. 포트 / 네트워크 / 영속성

- **호스트 포트**: `127.0.0.1:8652` (잠정 — `docs/08-docker-deployment.md`의 형제 프로젝트
  점유 목록과 정적으로는 겹치지 않으나, **배포 직전 `docker ps`로 재확인 필수**. 이
  프로젝트가 이미 겪은 "Up인데 내부는 죽어있음" 함정을 반복하지 않기 위해, 기동 후
  `curl http://127.0.0.1:8652/health` 실제 응답까지 확인합니다.)
- **컨테이너명**: `hermes-triagent-smb-dashboard-ui` (기존 `hermes-triagent-smb-dashboard`는
  Hermes 내장 CLI 대시보드가 이미 쓰고 있으므로 이름 충돌 방지를 위해 `-ui` 접미사 사용).
- **영속성**: 승인 레코드는 컨테이너 재시작에도 유지되어야 하므로 named volume이 아닌
  `./smb-dashboard/data:/data` bind mount로 호스트(E:) 드라이브에 저장합니다(`.hermes`
  bind mount와 동일한 이유 — [docker-compose.yml](../docker-compose.yml) 주석 참고).
- **의존성**: `mock-pos` 서비스에 `depends_on`.

## 7. 오류 처리

- Mock POS 호출 실패(타임아웃/4xx/5xx) 시, 원본 오류를 그대로 노출하지 않고 `502`와 함께
  "재고 서비스에 일시적으로 연결할 수 없습니다" 등 사용자 친화적 메시지로 변환합니다.
- 이미 결정된 승인 레코드에 대한 재 PATCH는 `409`를 반환하고 상태를 변경하지 않습니다.

## 8. MVP 범위 밖 (향후 과제)

- Mock POS `InventoryItem`에 품목별 최소재고 필드가 없어, 저재고 임계치는 전역 상수
  (`LOW_STOCK_THRESHOLD`)로 시작합니다. 품목별 임계치는 Mock POS 스키마 확장이 필요해
  이번 MVP 범위에서 제외합니다.
- 승인 큐 실시간 갱신(WebSocket/SSE)은 MVP에서 폴링(수 초 간격)으로 시작하고, 필요 시
  추후 개선합니다.
- 다국어/다중 매장(`store_id`) 지원은 현재 단일 매장 가정으로 미포함.

## 관련 문서

- [docs/12-mvp-window-options.md](12-mvp-window-options.md) — 3가지 MVP 방안 비교, 옵션 C 채택 근거
- [docs/06-hitl-approval-design.md](06-hitl-approval-design.md) — 기존 Discord 기반 HITL 설계 (이 문서의 §5가 확장)
- [docs/05-skills-and-tools.md](05-skills-and-tools.md) — Mock POS 연동 방식(code_execution)
- [docs/08-docker-deployment.md](08-docker-deployment.md) — 포트/컨테이너명 조사 방법론
</content>
