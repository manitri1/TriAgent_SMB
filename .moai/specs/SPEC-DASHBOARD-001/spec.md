---
id: SPEC-DASHBOARD-001
title: "SMB Dashboard MVP — Orders/Inventory/Reservations/Sales/Approvals 웹 UI"
version: "0.1.0"
status: in-progress
created: 2026-08-29
updated: 2026-08-29
author: manit
priority: P1
phase: "v0.2.0 target"
module: "smb-dashboard"
lifecycle: spec-anchored
tags: "dashboard, ui-surface, frontend, backend, fastapi, react, approvals, hitl, mock-pos-proxy"
tier: L
---

> **UI 화면이 포함된 SPEC.** 이 SPEC은 프론트엔드 모듈(`smb-dashboard/frontend`, React 18 + TypeScript + Vite)에 다섯 개의 구체적인 화면 산출물(§4)을 정의한다. 표준 워크플로우인 plan → run → sync가 아니라 **plan → design → run** 경로를 따른다: 디자인 단계(`manager-design`이 주도)는 plan-audit PASS와 Implementation Kickoff Approval 이후, run 단계의 M1 커밋 이전에 진입한다. 이 단계가 전달받는 디자인 의도 초안은 `design.md`를 참고한다.

## HISTORY

| Date | Change | Author |
|------|--------|--------|
| 2026-08-29 | 초기 SPEC 작성. 이미 구현되어 있는 `smb-dashboard` 기능(백엔드 + 프론트엔드 소스는 디스크에 존재하나 git에는 아직 추적되지 않음)과, 검증된 두 가지 미해결 격차(주문 상태 필터, 프록시 라우터 테스트 커버리지), 그리고 Problem→Hypothesis→Metric→Build→Measure→Learn 워크숍 구조에 따른 새로운 Success Metrics 프레이밍을 포착한다. | manager-spec |
| 2026-08-29 | `language.yaml` 변경(`documentation: ko`)에 따라 SPEC 문서 전체를 한국어로 번역. 번역과 함께 plan-audit 리포트(`SPEC-DASHBOARD-001-review-1.md`)의 D4 결함(AC-011의 "정확히 1회 요청" 과잉 주장 — Sales Summary 화면은 실제로는 `Promise.all`을 통해 동시에 3회 요청함)을 수정하고, 경미한 선택적 결함 D1/D2/D3/D5/D6도 함께 반영. 요구사항의 실제 의미·범위는 변경하지 않음. | manager-spec |

## 1. 개요

`docs/13-mvp-dashboard-design.md`(사용자가 이미 검토·승인한 문서)는 이 기능에 대한 권위 있는 디자인 소스이며, 이 SPEC 전반에서 규범적 기준으로 취급된다. 기존 서비스를 재사용하지 않고 새로운 전용 백엔드가 필요한 이유는 두 가지 구조적 격차 때문이다:

- **Mock POS(`mock-pos/`)**는 이미 완전한 REST API(주문, 재고, 예약, 결제, 매출 리포트)를 제공하지만 `CORSMiddleware`가 없어 브라우저에서 직접 호출할 수 없다. 따라서 서버 사이드 프록시가 필요하다.
- **Hermes 게이트웨이**에는 상태 조회용 REST API가 없다. 프로필 실행은 오직 CLI 서브프로세스(`hermes chat --profile <role> -q "..."`)를 통해서만 이루어지며, HITL 승인 상태는 지금까지 Discord 대화 기록 안에만 존재해왔고 구조화되어 조회 가능한 저장소는 없었다. 이 SPEC의 `data/approvals.json` 저장소는 **이 프로젝트가 HITL 상태를 위해 구축하는 최초의 구조화된 영속 계층**이다.

결과적인 아키텍처는 브라우저 → `smb-dashboard`(FastAPI + React/Vite, 단일 컨테이너, 포트 8652) → `mock-pos`(읽기 전용 프록시)로 이어지는 3계층 구성이며, 여기에 `smb-dashboard` ↔ `hermes` 승인 채널이 추가된다. 이 채널은 기존 Discord 기반 HITL 플로우(docs/06)를 **대체하지 않고 그와 병행하여** 동작한다.

### 1.1 현재 구현 현황 (추측이 아닌 소스 코드 검증 기준)

이 기능은 **이례적으로 진척이 앞서 있다**: docs/13에 정의된 설계 대부분이 이미 `smb-dashboard/` 하위 디스크에 존재한다(FastAPI 백엔드 앱 + 라우터 + 승인 저장소 + 인증 미들웨어; 다섯 개 화면 전부에 대한 프론트엔드 React 페이지; 멀티스테이지 Dockerfile; docker-compose 서비스 항목) — 다만 이 디렉터리 전체가 아직 git에 추적되지 않은 상태다(`git status`에서 새 파일, 미푸시 작업으로 표시됨). 실제 소스 코드를 두 차례 독립적으로 읽은 결과 다음이 확인되었다:

- **이미 구현되어 정상 동작 중인 항목**: 승인 큐 CRUD(`/api/approvals`에 대한 `POST`/`GET`/`GET {id}`/`PATCH`), 듀얼 채널 선착순 결정 시맨틱(재결정 시 409), 네 개의 읽기 전용 Mock POS 프록시 엔드포인트의 정상 경로(주문/재고/예약/리포트), 다섯 개 프론트엔드 화면 전체의 기본 렌더링, 모든 라우트(`/health` 제외)를 보호하는 HTTP Basic Auth 미들웨어, docker-compose 4개 서비스 토폴로지, 승인 데이터에 대한 바인드 마운트 JSON 영속화.
- **검증된 두 가지 미해결 격차** (§3.2, §3.3): Orders 화면에 상태 필터가 없음(docs/13 §4에는 명시되어 있으나 `orders.py` / `mock_pos_client.py` / `OrdersPage.tsx` 어디에도 구현되어 있지 않음), 그리고 네 개의 Mock-POS 프록시 라우터(`orders.py`, `inventory.py`, `reservations.py`, `reports.py`)에 테스트 커버리지가 전혀 없음(존재하는 테스트는 `test_approvals.py`뿐이며, `pytest-httpx`는 선언만 되어 있고 사용되지 않는 개발 의존성이다).

따라서 이 SPEC의 요구사항은 **검증 요구사항**(§3.1 — 이미 구현된 동작이 명세를 충족하는지 확인하며, 새로운 구현은 기대하지 않음)과 **신규 작업 요구사항**(§3.2–§3.3 — 두 가지 격차이며, run 단계에서 실제로 해결해야 할 미해결 인수 기준)으로 나뉜다.

## 2. 성공 지표 (Success Metrics)

`docs/13-mvp-dashboard-design.md`는 가설이나 성공 지표를 제시하지 않고 곧바로 기술적인 Build 설명으로 넘어간다. 이 섹션은 Problem → Hypothesis → Metric → Build → Measure → Learn 프레임워크를 적용하여 그 공백을 메운다.

### 2.1 Problem (문제)

SMB 사장님이 HITL 승인(프로모션 실행, 대량 재주문, 환불)을 확인할 수 있는 유일한 채널은 Discord 대화이며, 대기 중인 결정 사항에 대한 구조화되고 영속적이며 필터 가능한 뷰가 없다 — 사장님은 무엇이 자신의 결정을 기다리고 있는지 찾기 위해 채팅 기록을 일일이 스크롤해야 한다.

### 2.2 Hypothesis (가설)

기존 Discord 플로우와 함께 승인 큐를 웹 대시보드에 노출하면, SMB 사장님이 Discord 전용 기준선보다 더 빠르게 대기 중인 승인을 결정할 수 있을 것이다. 웹 채널은 채팅 기록을 스크롤해서 결정할 것을 찾을 필요 없이 영속적이고 구조화된 큐(정렬 가능, 항상 보이는 대기 건수)를 제공하기 때문이다.

### 2.3 Primary metric (핵심 지표)

**승인 생성 시점부터 승인 결정 시점까지의 중앙값 시간을, 결정 채널(웹 vs Discord)별로 나눈 지표.** 웹 채널의 중앙값과 Discord 채널의 중앙값을 직접 비교하면 가설을 그대로 검증할 수 있다: 웹 결정이 일관되게 더 빠르다면 가설이 뒷받침된다.

- **오늘 시점의 계측 상태: 계측 불가능.** `approvals_store.py`의 `decide_approval()`은 이미 `created_at`(생성 시)과 `decided_at`(결정 시)을 기록하고 있어 — 시간 차이 계산 자체는 가능하다 — 그러나 모든 호출에서 `decided_by: str = "owner"`가 하드코딩되어 있고, `ApprovalDecision`(PATCH 요청 모델)도 `approvals.py` 라우터도 "어느 채널이 결정했는가"를 나타내는 필드를 받거나 전달하지 않는다. `task_dispatch_and_verification` Hermes 스킬의 Discord 결정 동기화 호출(`PATCH /api/approvals/{id}`, `status`/`reason`만 전송)도 동일한 격차를 가지고 있다. **후속 과제**(이 SPEC의 범위 밖, §5 참조): `ApprovalDecision`에 `decided_via: "web" | "discord"` 필드를 추가하고 양쪽 호출부에 전달되도록 연결한다.

### 2.4 Supporting metrics (보조 지표)

- **채널 구분 없는 결정 소요 시간 중앙값** (created_at → decided_at, 채널 무관). Primary metric과 달리 이 지표는 코드 변경 없이 기존 `approvals.json` 필드로부터 **오늘 당장 계측 가능**하다 — 채널별 후속 과제가 진행되는 동안 참고할 기준선 트렌드로 유용하다.
- **일일 대시보드 오픈 횟수** 및 **화면별 조회 빈도**(Orders / Inventory / Reservations / Sales / Approvals). `main.py`, `BasicAuthMiddleware`, `App.tsx` 어디에도 접근 로깅이나 프론트엔드 분석 기능이 없어 **오늘 당장은 계측 불가능**하다. **후속 과제**: 라우트별 요청 카운트 로그, 또는 최소한의 프론트엔드 조회 추적 호출.

### 2.5 Guardrail metrics (가드레일 지표)

- **승인 결정 번복율.** "번복"(이미 결정된 레코드를 다시 결정하려는 시도)은 `AlreadyDecidedError` → HTTP 409(REQ-008)에 의해 현재 **구조적으로 방지**되어 있다 — 저장소는 두 번째 결정이 첫 번째 결정을 덮어쓰도록 절대 허용하지 않으므로, 이 가드레일은 사후 모니터링이 아니라 구조 자체로 강제된다.
- **`PATCH /api/approvals/{id}`에 대한 409 응답 비율**(듀얼 채널 경합 빈도의 프록시 지표 — 두 채널이 동일한 레코드를 결정하려 시도하는 빈도). 409는 발생 시 반환은 되지만 카운트되거나 로깅되지 않으므로 **오늘 당장은 계측 불가능**하다. **후속 과제**: `approvals.py`의 `AlreadyDecidedError` except 분기에 카운터 증가 또는 구조화 로그 라인을 추가한다.
- **Mock POS 프록시 502 오류율**(`orders`/`inventory`/`reservations`/`reports` 프록시 실패). `mock_pos_client.py`의 `_get()`는 `httpx.RequestError`와 `httpx.HTTPStatusError` 모두에서 `HTTPException(502, ...)`를 발생시키지만 발생 건을 로깅하거나 카운트하지 않으므로 **오늘 당장은 계측 불가능**하다. **후속 과제**: 각 `HTTPException(502, ...)` 발생 지점에 구조화 로그 라인(또는 카운터)을 추가한다.

### 2.6 Disposition (처리 방침)

위의 계측 후속 과제들은 이 SPEC의 구현 범위가 아니다(§ Out of Scope — Success-Metric Instrumentation 참조). 이 프로젝트의 "추정보다 검증" 원칙에 따라, 격차를 조용히 이미 해결된 것처럼 가정하지 않고 여기에 명시적으로 기록해 가시화한다.

## 3. 요구사항 (GEARS notation)

### 3.1 구현 완료 기능 — 검증 요구사항

다음 요구사항들은 소스 코드 검토 결과 이미 구현되어 있는 것으로 확인된 동작을 기술한다. run 단계에서는 이를 새로 구축하는 것이 아니라 (테스트, 수동 스모크 체크를 통해) 검증한다.

- **REQ-001** (Ubiquitous): 대시보드 백엔드는 `GET /api/orders/today`를 Mock POS의 `GET /v1/stores/{store_id}/orders`로 프록시하며, `created_at` 날짜가 현재 UTC 날짜와 일치하는 주문만 반환한다.
- **REQ-002** (Ubiquitous): 대시보드 백엔드는 `GET /api/inventory`를 Mock POS의 `GET /v1/stores/{store_id}/inventory`로 프록시하며, `LOW_STOCK_THRESHOLD` 환경 변수(기본값 `10`)를 기준으로 계산한 `low_stock` 불리언 값을 각 반환 항목에 주석으로 추가한다.
- **REQ-003** (Ubiquitous): 대시보드 백엔드는 `GET /api/reservations`를 Mock POS의 `GET /v1/stores/{store_id}/reservations`로 프록시하며, 선택적 쿼리 파라미터 `date`와 `status`가 존재하는 경우 이를 그대로 전달한다.
- **REQ-004** (Ubiquitous): 대시보드 백엔드는 `GET /api/reports/sales`를 Mock POS의 `GET /v1/stores/{store_id}/reports/sales`로 프록시하며, `period` 쿼리 파라미터(`today` | `week` | `month`)를 전달한다.
- **REQ-005** (Event-driven): 워커 프로필 또는 프론트엔드가 유효한 `type`/`summary`/`details`/`requested_by` 페이로드와 함께 `POST /api/approvals`를 요청하면, 승인 저장소는 `status: pending`, 생성된 `approval_id`, `created_at` 타임스탬프를 가진 새 레코드를 생성하고 HTTP 201로 응답한다.
- **REQ-006** (Ubiquitous): 승인 저장소는 선택적 `status` 쿼리 파라미터로 필터링된 승인 레코드 목록 조회를 지원하며, `created_at` 기준 내림차순으로 정렬한다.
- **REQ-007** (Event-driven): 프론트엔드 또는 워커 프로필이 `status`가 `pending`인 레코드에 대해 `PATCH /api/approvals/{id}`를 요청하면, 승인 저장소는 해당 레코드를 `approved` 또는 `rejected`로 전이시키고 `decided_by`와 `decided_at`을 기록한 뒤 HTTP 200으로 응답한다.
- **REQ-008** (Event-detected / unwanted): 이미 `approved` 또는 `rejected` 상태인 레코드를 대상으로 `PATCH /api/approvals/{id}` 요청이 들어오면, 승인 저장소는 해당 요청을 HTTP 409로 거부하고 기존 레코드를 수정하지 않는다 — 듀얼 채널 "선착순 결정" 규칙(docs/13 §5)을 구현한 것이다.
- **REQ-009** (Ubiquitous): 대시보드 백엔드는 `GET /health`를 제외한 모든 라우트에 HTTP Basic Auth(`DASHBOARD_BASIC_AUTH_USER`/`_PASSWORD`)를 요구하며, 미들웨어를 통해 강제하여 서빙되는 프론트엔드 정적 번들도 API 라우트와 동일하게 보호되도록 한다.
- **REQ-010** (Event-detected / unwanted): Mock POS로의 프록시 호출이 실패하면(연결 오류, 타임아웃, 또는 2xx가 아닌 상태 코드), 대시보드 백엔드는 Mock POS의 원본 오류 상세를 그대로 전달하지 않고 HTTP 502와 사용자 대상 메시지로 응답한다.
- **REQ-011** (Ubiquitous): 프론트엔드는 탭으로 선택 가능한 다섯 개의 화면 — Orders, Inventory, Reservations, Sales Summary, Approvals — 을 렌더링하며, 각 화면은 마운트 시 대응하는 `/api/*` 라우트로부터 데이터를 가져오고, 탭 전환은 라우터 라이브러리 없이 클라이언트 사이드에서 처리한다.
- **REQ-012** (Event-driven): `smb-dashboard` 컨테이너가 재시작될 때, 승인 저장소는 인메모리 상태가 아니라 바인드 마운트된 `data/approvals.json` 파일에 영속화하는 방식으로 이전에 생성된 모든 레코드를 보존한다.
- **REQ-013** (Ubiquitous): 배포 토폴로지는 `smb-dashboard`를 네 번째 Docker Compose 서비스로 실행하며, `depends_on: mock-pos`, `127.0.0.1:8652`로 노출되고, 기존 Hermes CLI 대시보드 컨테이너와는 구분되는 컨테이너 이름(`hermes-triagent-smb-dashboard-ui`)을 가진다.

### 3.2 신규 작업 — 주문 상태 필터 (미해결 격차 #1)

- **REQ-014** (Ubiquitous): `GET /api/orders/today` 엔드포인트는 `OPEN | COMPLETED | CANCELED | REFUNDED`로 제한된 선택적 `status` 쿼리 파라미터를 받으며, 이 파라미터가 존재할 경우 해당 상태와도 일치하는 당일 주문만 반환한다.
- **REQ-015** (Event-driven): 사장님이 Orders 화면에서 상태 필터 옵션을 선택하면, 프론트엔드는 해당 `status` 파라미터와 함께 `/api/orders/today`를 다시 요청하고 일치하는 주문만 렌더링한다.
- **REQ-016** (Ubiquitous): Orders 화면은 docs/13 §4에 명시된 네 가지 명시적 상태 옵션과 함께 "전체(All)" 필터 옵션을 제공한다.

### 3.3 신규 작업 — Mock POS 프록시 라우터 테스트 커버리지 (미해결 격차 #2)

- **REQ-017** (Ubiquitous): `orders`, `inventory`, `reservations`, `reports` 라우터는 각각 하위의 Mock POS HTTP 호출을 모킹하는 자동화된 테스트 커버리지를 가지며, 최소한 정상 경로(happy-path) 응답 형태와 502 변환 경로(REQ-010)를 다룬다.
- **REQ-018** (Ubiquitous): 네 개의 Mock-POS 프록시 라우터에 대한 백엔드 테스트 커버리지는 기존 `test_approvals.py` 커버리지와 합산하여 `smb-dashboard/backend/app/`에 대해 프로젝트의 85% 커버리지 목표치를 충족한다(목표치 정의: `.moai/config/sections/quality.yaml`의 `constitution.test_coverage_target`).

## 4. 화면 (프론트엔드 산출물 — UI 화면 분류를 확정)

| Screen | Content | Data source | Status |
|---|---|---|---|
| Orders | 당일 주문 목록, 상태 배지, **상태 필터(신규, REQ-014–016)** | `/api/orders/today` | 필터 제외 구현 완료 |
| Inventory | 전체 재고 목록, `LOW_STOCK_THRESHOLD` 기준 빨간색 강조 표시 | `/api/inventory` | 구현 완료 |
| Reservations | 날짜 필터링된 예약 목록(BOOKED/CANCELED) | `/api/reservations` | 구현 완료 |
| Sales Summary | 오늘/이번 주/이번 달 매출 및 주문 건수 위젯 | `/api/reports/sales` | 구현 완료 |
| Approvals | 대기 중인 레코드 카드, 승인/거절 버튼 + 브라우저 네이티브 `window.prompt()` 대화상자를 통한 사유 입력 | `/api/approvals` | 구현 완료 |

## 5. 적용 범위 제외 (Out of Scope)

### Out of Scope — Per-Item Low-Stock Thresholds
- Mock POS의 `InventoryItem`에는 항목별 최소 재고 필드가 없으므로, 이 MVP에서는 재고 부족 플래그가 단일 전역 `LOW_STOCK_THRESHOLD` 상수를 기준으로 유지된다. 항목별 임계값을 도입하려면 Mock POS 스키마 확장이 필요하며, 이는 명시적으로 이후로 미룬다(docs/13 §8).

### Out of Scope — Realtime Approval-Queue Updates
- 승인 큐에 대한 WebSocket/SSE 푸시 업데이트는 구축하지 않는다. MVP는 폴링 방식을 사용한다(프론트엔드는 탭 포커스 시 / 수동 새로고침 시 다시 가져오며, Hermes 측 폴링 주기는 docs/13 §5에 문서화되어 있다). 이 SPEC은 푸시 채널을 추가하지 않는다.

### Out of Scope — Multi-Store / Internationalization
- 대시보드는 단일 `store_id`(`STORE_ID` 환경 변수)와 현재 작성된 그대로의 영어/한국어 혼용 UI 문구를 전제로 한다. 다중 매장 선택과 국제화(i18n)는 범위에 포함되지 않는다.

### Out of Scope — Success-Metric Instrumentation (Follow-up)
- §2에서 언급한 결정 채널 필드(`decided_via`), 대시보드 오픈/화면별 조회 로깅, 409/502 발생 카운터는 이 SPEC의 run 단계 구현 범위에 명시적으로 포함되지 않는다. 이들은 이 MVP의 핵심 격차(§3.2–§3.3)가 해소된 이후 향후 SPEC의 후속 과제 후보로 기록해 둔다.

### Out of Scope — Real POS Vendor Integration
- 이 SPEC에서는 Mock POS가 계속 백엔드 저장소 역할을 하며, 실제 POS 벤더(Toss Place / KakaoPay 등급) 연동은 장기 로드맵 항목이다(docs/07). 여기서는 범위 밖이다.

### Out of Scope — Design-Phase Visual Refinement
- 이 plan 단계 SPEC은 최종 시각 디자인(색상, 여백, "CSS 프레임워크 없음"을 넘어서는 컴포넌트 라이브러리 선택)을 규정하지 않는다. 이러한 결정은 UI 화면 포함 조건부 경로에 따라 plan-audit PASS와 Implementation Kickoff Approval 이후 진행되는 디자인 단계(`manager-design`, `design.md` 핸드오프)에서 이루어진다.
