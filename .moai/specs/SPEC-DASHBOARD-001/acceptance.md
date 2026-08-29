# Acceptance Criteria — SPEC-DASHBOARD-001

이 문서는 검증 계층이다: 모든 항목은 참/거짓으로 판정 가능한(binary-testable) `AC-XXX`이며 `Given … When … Then …` 형식으로 라벨링되어 있고, spec.md의 GEARS `REQ-XXX` 항목(요구사항 계층)과는 구분된다. 여기에는 어떠한 GEARS 요구사항 문구도 시나리오로 재서술되지 않는다.

## §D AC Matrix (AC 매트릭스)

### §D.1 구현 완료 기능 — 검증 시나리오

- **AC-001** (verifies REQ-001): Given Mock POS에 오늘 생성된 주문과 이전 날짜에 생성된 주문이 모두 존재하는 상태에서, When 클라이언트가 유효한 Basic Auth와 함께 `GET /api/orders/today`를 호출하면, Then 응답에는 `created_at` 날짜가 현재 UTC 날짜와 일치하는 주문만 포함된다.
- **AC-002** (verifies REQ-002): Given Mock POS 재고에 `stock_quantity`가 `LOW_STOCK_THRESHOLD` 미만인 항목 하나와 초과인 항목 하나가 존재하는 상태에서, When 클라이언트가 `GET /api/inventory`를 호출하면, Then 임계값 미만 항목의 응답 객체는 `low_stock: true`를, 초과 항목은 `low_stock: false`를 갖는다.
- **AC-003** (verifies REQ-003): Given 여러 날짜와 상태에 걸쳐 예약이 존재하는 상태에서, When 클라이언트가 `GET /api/reservations?date=2026-08-29&status=BOOKED`를 호출하면, Then 응답에는 두 필터 모두와 일치하는 예약만 포함된다.
- **AC-004** (verifies REQ-004): Given Mock POS에 매출 데이터가 존재하는 상태에서, When 클라이언트가 `GET /api/reports/sales?period=week`를 호출하면, Then 응답은 `today` 기본값이 아니라 `week` 기간의 요약을 반영한다.
- **AC-005** (verifies REQ-005): Given 이전에 생성된 승인 레코드가 없는 상태에서, When 클라이언트가 유효한 승인 페이로드로 `/api/approvals`에 POST를 요청하면, Then 응답은 HTTP 201이며 `status: "pending"`, 생성된 `approval_id`, `created_at` 타임스탬프를 포함한다.
- **AC-006** (verifies REQ-006): Given `pending`, `approved`, `rejected` 상태의 승인 레코드가 존재하는 상태에서, When 클라이언트가 `GET /api/approvals?status=pending`을 호출하면, Then `pending` 레코드만 반환되며 `created_at` 최신순으로 정렬된다.
- **AC-007** (verifies REQ-007): Given `pending` 상태의 승인 레코드가 존재하는 상태에서, When 클라이언트가 `{"status": "approved", "reason": "..."}`로 PATCH를 요청하면, Then 응답은 HTTP 200이며 `status: "approved"`, non-null `decided_by`, non-null `decided_at`을 포함한다.
- **AC-008** (verifies REQ-008): Given 이미 `approved` 상태인 승인 레코드가 존재하는 상태에서, When 동일한 `approval_id`에 대해 두 번째 PATCH가 `{"status": "rejected"}`를 시도하면, Then 응답은 HTTP 409이며 레코드의 `status`는 `"approved"`로 변경 없이 유지된다.
- **AC-009** (verifies REQ-009): Given Authorization 헤더가 전혀 제공되지 않은 상태에서, When 클라이언트가 `/health`를 제외한 임의의 라우트(정적 프론트엔드 자산 경로 포함)를 호출하면, Then 응답은 HTTP 401이며 `WWW-Authenticate: Basic` 헤더를 포함한다.
- **AC-010** (verifies REQ-010): Given Mock POS에 접근할 수 없는 상태(연결 거부 또는 타임아웃)에서, When 클라이언트가 `/api/orders/today`, `/api/inventory`, `/api/reservations`, `/api/reports/sales` 중 하나를 호출하면, Then 응답은 HTTP 502이며 사용자 대상 메시지를 포함한다(원본 스택 트레이스나 Mock POS 오류 본문이 아님).
- **AC-011** (verifies REQ-011): Given 유효한 자격 증명으로 브라우저에서 대시보드 프론트엔드가 로드된 상태에서, When 사장님이 다섯 개의 탭 라벨을 각각 클릭하면, Then 각 화면은 정상적으로 렌더링되며 대응하는 `/api/*` 라우트로 최소 한 번 이상 요청을 보낸다 — 단, Sales Summary 화면은 예외적으로 오늘/이번 주/이번 달 세 기간에 대해 `Promise.all`을 통해 동시에 3회 요청을 보내며, 그 외 네 화면(Orders, Inventory, Reservations, Approvals)은 각각 정확히 1회만 요청을 보낸다.
- **AC-012** (verifies REQ-012): Given 승인 레코드가 `data/approvals.json`에 존재하는 상태에서, When `smb-dashboard` 컨테이너가 재시작되면, Then 재시작 후 `GET /api/approvals`는 재시작 전에 존재하던 것과 동일한 레코드를 반환한다.
- **AC-013** (verifies REQ-013): Given `docker compose up`이 실행된 상태에서, When `docker ps`를 확인하면, Then `hermes-triagent-smb-dashboard-ui`라는 이름의 컨테이너가 정확히 하나 존재하며, 이는 기존 Hermes CLI 대시보드 컨테이너인 `hermes-triagent-smb-dashboard`와는 구분되고, `curl http://127.0.0.1:8652/health`는 HTTP 200과 `{"status": "ok"}`를 반환한다.

### §D.2 신규 작업 — 주문 상태 필터 시나리오

- **AC-014** (verifies REQ-014): Given 오늘의 주문에 `OPEN`, `COMPLETED`, `CANCELED`, `REFUNDED` 상태가 혼재되어 있는 상태에서, When 클라이언트가 `GET /api/orders/today?status=REFUNDED`를 호출하면, Then 오늘 날짜의 `REFUNDED` 주문만 반환된다.
- **AC-015** (verifies REQ-014, edge case): Given 오늘의 주문 중 `CANCELED` 상태인 주문이 하나도 없는 상태에서, When 클라이언트가 `GET /api/orders/today?status=CANCELED`를 호출하면, Then 응답은 빈 목록(HTTP 200)이며 오류가 아니다.
- **AC-016** (verifies REQ-015, REQ-016): Given Orders 화면이 "전체(All)" 주문을 보여주는 상태로 로드된 상태에서, When 사장님이 "OPEN" 필터 옵션을 선택하면, Then 프론트엔드는 `/api/orders/today?status=OPEN`으로 새로운 요청을 보내고 `OPEN` 주문만 보여주도록 다시 렌더링한다.
- **AC-017** (verifies REQ-014, regression): Given 필터 기능이 추가된 상태에서, When 클라이언트가 `status` 파라미터 없이 `GET /api/orders/today`를 호출하면, Then 동작은 필터 도입 이전과 동일하다 — 상태와 무관하게 오늘의 모든 주문이 반환된다.
- **AC-018** (edge case, verifies REQ-014): Given 클라이언트가 `GET /api/orders/today?status=INVALID_VALUE`를 호출하는 상태에서, When 요청이 처리되면, Then 응답은 HTTP 422이다(범위를 벗어난 `Literal` 값에 대한 FastAPI의 표준 검증 오류 응답이며, 파라미터가 조용히 무시되지 않는다).

### §D.3 신규 작업 — 테스트 커버리지 시나리오

- **AC-019** (verifies REQ-017): Given `pytest-httpx`로 Mock POS의 성공 응답을 모킹한 상태에서, When `orders.py`, `inventory.py`, `reservations.py`, `reports.py` 각각의 테스트 스위트를 실행하면, Then 각 라우터는 올바른 프록시/변환 응답 형태를 검증하는 정상 경로(happy-path) 테스트를 최소 하나 이상 통과시킨다.
- **AC-020** (verifies REQ-017): Given `pytest-httpx`로 Mock POS 연결 실패 또는 2xx가 아닌 응답을 모킹한 상태에서, When 대응하는 라우터의 502 경로 테스트를 실행하면, Then 테스트는 (원본 Mock POS 오류가 아니라) 사용자 대상 메시지와 함께 HTTP 502를 검증한다.
- **AC-021** (verifies REQ-018): Given 신규 라우터 테스트(AC-019, AC-020)와 기존 `test_approvals.py`가 모두 통과하는 상태에서, When `smb-dashboard/backend/`에서 `pytest --cov=app`을 실행하면, Then `app/`에 대해 보고되는 커버리지는 85% 이상이다.

## §D.4 완료 정의 (Definition of Done)

- [ ] AC-001부터 AC-021까지 모두 통과한다(실제 `pytest` 스위트를 실행하고 그 결과를 그대로 인용하여 검증 — 프로젝트의 추정보다 검증 원칙에 따라 단순 주장이 아니다).
- [ ] 기존 `test_approvals.py`(사전 존재)는 수정 없이 여전히 통과한다 — M1/M2로 인한 회귀 없음.
- [ ] `smb-dashboard/backend/app/`에 대한 커버리지 리포트가 85% 이상을 나타낸다(quality.yaml `constitution.test_coverage_target`).
- [ ] Docker Compose 스택(`docker compose up`)이 4개 서비스를 모두 기동하고 `curl http://127.0.0.1:8652/health`가 (단순 `docker ps`의 "Up" 상태가 아니라 — docs/13 §6에 명시된 과거 사례의 명확한 경고에 따라) 실제 `200 {"status": "ok"}` 응답을 반환한다.
- [ ] Orders 화면의 필터 컨트롤이 최종 확정되기 전에 (UI 화면 포함 조건부 경로에 따라) 배치/스타일링에 대해 디자인 단계(`manager-design`)를 거쳤다.
- [ ] Success Metrics 계측 격차(spec.md §2)는 이 SPEC에서 해소되지 않은 것으로 명시적으로 남아 있다 — 이 문서의 어떤 AC도 이를 포착했다고 주장하지 않는다.

## §D.5 품질 게이트 기준 (TRUST 5 정합)

- **Tested**: AC-019–021(85% 커버리지 목표, 기존 `test_approvals.py` 동작 보존에 대한 특징화 테스트).
- **Readable**: 신규 필터 코드와 신규 테스트 파일은 기존 파일의 네이밍/오류 처리/임포트 관례와 일치한다(plan.md §D).
- **Unified**: 새로운 포매터/린터를 도입하지 않는다 — 기존 `ruff`/`black`(Python) 관례가 변경 없이 적용된다.
- **Secured**: AC-009(인증 경계)와 AC-018(신규 `status` 파라미터에 대한 입력 검증)이 이 SPEC 범위에서 보안과 관련된 시나리오다.
- **Trackable**: run 단계 커밋은 `SPEC-DASHBOARD-001`을 참조하는 Conventional Commits 형식을 따른다.

## §D.6 간접 검증 / 추적성 참고

REQ-012(재시작 간 영속성)와 REQ-013(compose 토폴로지)은 `pytest`가 아니라 운영 측면(컨테이너 재시작 + `docker ps` + `curl`)에서 검증되는 인프라 수준 요구사항이다 — 이는 예상된 것이며 해당 요구사항에 유닛 테스트 커버리지가 누락되었음을 의미하지 않는다.

## §D.7 향후 점검 사항 (이 SPEC 종료를 막지 않음)

- `decided_via` 채널 필드(spec.md §2.3 후속 과제)가 향후 SPEC에서 추가되면, AC-007/AC-008을 확장하여 웹과 Discord 결정 경로 모두에서 해당 필드가 올바르게 채워지는지 검증해야 한다.
- 대시보드 오픈/화면별 조회 로깅(spec.md §2.4 후속 과제)이 갖춰지면, Supporting Metrics를 조회 가능하도록 로그 항목을 검증하는 새 AC를 추가해야 한다.
