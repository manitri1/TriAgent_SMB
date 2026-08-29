# SPEC-DASHBOARD-001 (Compact) — SMB Dashboard MVP

> plan 단계에서 자동 생성된 축약본으로, run 단계 로딩용이다(전체 spec.md 대비 약 30% 토큰 절감). 폴백: 이 파일을 사용할 수 없거나 오래된 경우 run 단계는 전체 `spec.md`를 로드할 수 있다.

## 요구사항 (GEARS)

### 구현 완료 — 검증 전용
- **REQ-001** (Ubiquitous): 대시보드 백엔드는 `GET /api/orders/today`를 Mock POS로 프록시하며 오늘(UTC) 생성된 주문만 반환한다.
- **REQ-002** (Ubiquitous): 대시보드 백엔드는 `GET /api/inventory`를 프록시하며 `LOW_STOCK_THRESHOLD`(기본값 10) 기준으로 항목에 `low_stock`을 주석으로 추가한다.
- **REQ-003** (Ubiquitous): 대시보드 백엔드는 `GET /api/reservations`를 프록시하며 선택적 `date`/`status` 파라미터를 전달한다.
- **REQ-004** (Ubiquitous): 대시보드 백엔드는 `GET /api/reports/sales`를 프록시하며 `period`(`today`|`week`|`month`)를 전달한다.
- **REQ-005** (Event-driven): 유효한 페이로드로 `POST /api/approvals`가 요청되면, 승인 저장소는 `pending` 레코드를 생성하고 HTTP 201로 응답한다.
- **REQ-006** (Ubiquitous): 승인 저장소는 선택적 `status`로 필터링되고 `created_at` 내림차순으로 정렬된 레코드 목록을 제공한다.
- **REQ-007** (Event-driven): `PATCH /api/approvals/{id}`가 `pending` 레코드를 대상으로 하면, 승인 저장소는 이를 전이시키고 HTTP 200으로 응답한다.
- **REQ-008** (Event-detected/unwanted): PATCH가 이미 결정된 레코드를 대상으로 하면, 승인 저장소는 HTTP 409로 응답하며 이를 수정하지 않는다.
- **REQ-009** (Ubiquitous): 대시보드 백엔드는 `/health`를 제외한 모든 라우트에 Basic Auth를 요구한다.
- **REQ-010** (Event-detected/unwanted): Mock POS 프록시 호출이 실패하면, 대시보드 백엔드는 사용자 대상 메시지와 함께 HTTP 502로 응답한다.
- **REQ-011** (Ubiquitous): 프론트엔드는 탭으로 선택 가능한 5개 화면(Orders/Inventory/Reservations/Sales/Approvals)을 렌더링한다.
- **REQ-012** (Event-driven): 컨테이너가 재시작될 때, 승인 저장소는 바인드 마운트된 `data/approvals.json`을 통해 레코드를 보존한다.
- **REQ-013** (Ubiquitous): compose 토폴로지는 `smb-dashboard`를 `127.0.0.1:8652`의 네 번째 서비스로 실행하며 `depends_on: mock-pos`이다.

### 신규 작업 — 주문 필터 (미해결 격차 #1)
- **REQ-014** (Ubiquitous): `GET /api/orders/today`는 선택적 `status`(`OPEN|COMPLETED|CANCELED|REFUNDED`)를 받아 그에 맞게 필터링한다.
- **REQ-015** (Event-driven): 사장님이 필터를 선택하면, 프론트엔드는 `status`와 함께 다시 요청하여 일치하는 것만 렌더링한다.
- **REQ-016** (Ubiquitous): Orders 화면은 4개의 명시적 상태와 함께 "전체" 옵션을 제공한다.

### 신규 작업 — 테스트 커버리지 (미해결 격차 #2)
- **REQ-017** (Ubiquitous): `orders`/`inventory`/`reservations`/`reports` 라우터는 각각 하위 Mock POS HTTP 호출을 모킹하는 자동화된 테스트 커버리지를 가지며, 정상 경로와 502 경로를 다룬다.
- **REQ-018** (Ubiquitous): `app/`에 대한 합산 백엔드 커버리지는 프로젝트의 85% 목표치를 충족해야 한다.

## 인수 기준 (Given-When-Then, ID만 — 전체 내용은 acceptance.md 참고)

AC-001..AC-013은 REQ-001..REQ-013(구현 완료 기능)을 검증한다. AC-014..AC-018은 REQ-014/016(주문 필터, 엣지 케이스 포함: 빈 결과 집합 AC-015, 잘못된 열거값 AC-018)을 검증한다. AC-019..AC-021은 REQ-017/018(테스트 커버리지 + 85% 게이트)을 검증한다.

## 수정 대상 파일

- `smb-dashboard/backend/app/routers/orders.py` — `status` 쿼리 파라미터 추가 (REQ-014)
- `smb-dashboard/frontend/src/api.ts` — `todayOrders()`가 선택적 status 인수를 받도록 확장
- `smb-dashboard/frontend/src/pages/OrdersPage.tsx` — 필터 컨트롤 UI (REQ-015–016, 배치는 디자인 단계에서 결정)
- `smb-dashboard/backend/tests/test_orders.py` (신규) — REQ-017
- `smb-dashboard/backend/tests/test_inventory.py` (신규) — REQ-017
- `smb-dashboard/backend/tests/test_reservations.py` (신규) — REQ-017
- `smb-dashboard/backend/tests/test_reports.py` (신규) — REQ-017

## 제외 사항 (구축하지 않을 것)

- 항목별 재고 부족 임계값 없음(전역 `LOW_STOCK_THRESHOLD`만 사용).
- 실시간 WebSocket/SSE 없음(폴링만 사용).
- 다중 매장/i18n 지원 없음(단일 `store_id`).
- Success-Metric 계측 없음(`decided_via` 채널 필드, 대시보드 오픈 로깅, 409/502 카운터) — 향후 SPEC으로 명시적으로 연기.
- 실제 POS 벤더 연동 없음(Mock POS가 계속 백엔드 저장소 역할).
- 최종 시각/CSS 디자인 결정 없음 — run 단계에서 임의로 만들지 않고 디자인 단계(`manager-design`)를 거친다.
