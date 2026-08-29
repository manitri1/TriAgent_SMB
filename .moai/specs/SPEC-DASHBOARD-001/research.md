# Research — SPEC-DASHBOARD-001

`spec.md` §1.1의 "구현 완료 vs 미해결 격차" 분류를 뒷받침하는 심층 코드베이스 분석. 실제 소스 코드(설계 문서의 서술만이 아니라)에 대한 두 차례 독립적인 읽기가 이 문서의 근거이며 — 아래의 발견 사항들은 docs/13의 서술로부터 가정한 것이 아니라 특정 파일과 라인 단위 동작에 대한 인용에 근거한다.

## 1. 읽은 소스 파일

**Backend** (`smb-dashboard/backend/app/`): `main.py`, `auth.py`, `mock_pos_client.py`, `approvals_store.py`, `models.py`, `routers/{orders,inventory,reservations,reports,approvals}.py`.
**Backend tests** (`smb-dashboard/backend/tests/`): `test_approvals.py`.
**Frontend** (`smb-dashboard/frontend/src/`): `App.tsx`, `api.ts`, `pages/*.tsx`(5개 파일).
**Integration point**: `.hermes/profiles/coordinator/skills/orchestration/task_dispatch_and_verification/SKILL.md`(승인 큐를 호출하는 Hermes 측 코드).
**Deployment**: `docker-compose.yml`, `.moai/project/tech.md`(Build and Deployment 섹션).

## 2. Finding 1 — 주문 상태 필터는 실제로 누락되어 있음

`docs/13-mvp-dashboard-design.md` §4는 Orders 화면의 명시된 기능으로 "상태별 필터(OPEN/COMPLETED/CANCELED/REFUNDED)"를 나열하고 있다. 소스 코드로 확인한 결과는 다음과 같다:

- `orders.py`(`get_today_orders`): 날짜로만 필터링하며(`_parse_date(o["created_at"]) == today`), status 파라미터는 받지도 참조하지도 않는다.
- `mock_pos_client.py`(`list_orders`): 쿼리 파라미터 없이 `_get("/orders")`를 호출한다 — 클라이언트 계층에도 상태 전달 기능이 전혀 없다.
- `OrdersPage.tsx`(여기서는 전체를 보여주지 않았지만 `api.ts`를 통해 확인됨, `api.ts`의 `todayOrders: () => request<Order[]>("/api/orders/today")`): API 클라이언트 함수가 어떤 인수도 받지 않으므로, 프론트엔드 호출 체인 어디에도 필터 파라미터가 연결되어 있지 않음을 확인했다.

**결론**: 이는 문서상의 불일치가 아니라 실제로 구현되지 않은 격차다. 이를 해소하려면 세 계층에 걸친 변경이 필요하다: `mock_pos_client.py`는 영향받지 **않는다**(Mock POS 자체의 orders 엔드포인트에도 서버 사이드 상태 필터가 없다 — docs/13에 이미 orders 엔드포인트가 "전체 목록만" 반환한다고 명시되어 있으며, 상태에 관계없이 필터링은 기존 날짜 필터와 마찬가지로 클라이언트 쪽인 `orders.py`에서 이루어진다), `orders.py`의 `get_today_orders`에는 새로운 선택적 `status` 파라미터가 필요하며, `api.ts` + `OrdersPage.tsx`에는 fetch/렌더링 연결이 필요하다.

## 3. Finding 2 — 네 개 프록시 라우터에 테스트 커버리지가 전혀 없음

- `smb-dashboard/backend/requirements-dev.txt`는 `pytest-httpx`를 개발 의존성으로 선언하고 있다.
- `smb-dashboard/backend/tests/test_approvals.py`가 존재하는 유일한 테스트 파일이다. 이 파일은 `fastapi.testclient.TestClient`를 로컬 JSON 파일 기반 `approvals_store`에 직접 사용하며 — `httpx` 호출은 전혀 하지 않으므로 `mock_pos_client.py`의 프록시 로직은 전혀 실행하지 않는다.
- `smb-dashboard/backend/tests/`를 grep한 결과 `orders`, `inventory`, `reservations`, `reports`를 참조하는 테스트 파일이 하나도 없음을 확인했다.
- `pytest-httpx`가 `requirements-dev.txt`에 존재하지만 사용처가 없다는 것은, 이것이 우연히 빠진 의존성이 아니라 의도적으로 예상되었지만 끝까지 이어지지 않은 작업임을 확인해 준다.

**결론**: REQ-017/018은 추측이 아닌 실제로 검증된 격차를 해소한다. 이 수정은 부가적(additive)이다 — 새 테스트 파일만 추가하면 되며, 이 테스트를 가능하게 하기 위해 프로덕션 코드를 변경할 필요는 없다. `mock_pos_client.py`가 각 함수 호출 내부에서 모듈 수준의 `httpx.AsyncClient`를 생성하는 방식은, 클라이언트가 어디서 인스턴스화되는지와 무관하게 트랜스포트 계층에서 요청을 가로채는 `pytest-httpx`의 `httpx_mock` 픽스처 패턴과 직접적으로 호환된다.

## 4. Finding 3 — Success-Metrics 계측 격차 (추측이 아닌 확인된 사실)

작업 프롬프트에서 데이터 수집 격차를 가정하기 전에 `approvals_store.py`/`models.py`를 먼저 확인하라고 명시적으로 지시한 데 따라:

- `models.py`의 `Approval` 모델은 이미 `created_at: datetime`(기본 팩토리 `utcnow`)과 `decided_at: Optional[datetime]`을 갖고 있다 — 따라서 채널 구분 없는 결정 소요 시간 지표(spec.md §2.4 supporting metric)는 코드 변경 없이 기존 저장 데이터로부터 완전히 계산 가능하다.
- `models.py`의 `ApprovalDecision`(PATCH 요청 모델)은 `status`와 `reason`만 가지고 있다 — 채널/소스 필드는 없다.
- `approvals_store.py`의 `decide_approval(approval_id, status, reason, decided_by: str = "owner")`는 기본값을 하드코딩하고 있으며, `approvals.py` 라우터에서 `(approval_id, payload.status, payload.reason)`으로만 호출된다 — `decided_by` 파라미터는 이 코드베이스의 유일한 호출부에서 **한 번도** 재정의되지 않는다.
- `task_dispatch_and_verification/SKILL.md`의 §"구조화 승인 큐 연동" 4단계에 있는 Hermes 측 동기화 호출은 `PATCH {DASHBOARD_BASE_URL}/api/approvals/{approval_id}`를 `{"status": ..., "reason": ...}`만 담아 전송한다 — Discord 채널 결정 경로도 웹 경로와 동일한 "채널 미기록" 격차를 갖고 있음을 확인했다.

**결론**: Primary Success Metric(채널별 결정 소요 시간 중앙값)은 오늘 시점에서 계측 불가능함이 확인되었다. 이는 후속 과제로 기록된다(spec.md § Out of Scope — Success-Metric Instrumentation) — 조용히 이미 해결된 것으로 취급하지 않는다.

## 5. Finding 4 — 배포 토폴로지가 `tech.md`와 대조 확인됨

`docker-compose.yml`(3회에 걸쳐 plan-auditor의 검증을 받은 `.moai/project/tech.md` § Build and Deployment 대비 교차 확인)은 4개 서비스를 확인해 준다: `hermes`, `dashboard`(Hermes 자체의 CLI 대시보드, 포트 9128 — 별개), `mock-pos`(포트 8080), `smb-dashboard`(포트 8652, `depends_on: mock-pos`, 컨테이너 이름 `hermes-triagent-smb-dashboard-ui`). 이 SPEC의 범위에서 설계 문서, `tech.md`, 실제 compose 파일 사이에 발견된 불일치는 없다.

## 6. 신뢰도와 남은 공백

- **High confidence**: Finding 1, 2, 4는 정확한 grep/라인 단위 인용과 함께 직접적인 소스 코드 확인에 근거한다.
- **High confidence**: Finding 3은 양쪽 호출부(웹 라우터 + Hermes 스킬 파일) 모두에 대한 직접적인 소스 코드 확인에 근거한다 — 한쪽만 보고 추론한 것이 아니라 두 쪽 모두 채널 계측이 없음을 확인했다.
- **이번 패스에서 독립적으로 재검증하지 않은 사항**: 작업 프롬프트에서 전달된 "두 차례의 독립적인 감사 패스가 이미 Findings 1–2를 확립했다"는 주장. 이 문서는 (세 번째) 독립적인 읽기를 자체적으로 수행하여 동일한 결론에 도달했다 — 이는 검증되지 않은 이전 주장을 재서술한 것이 아니라 보강(corroboration)으로 인용한 것이다.
- **이 리서치의 범위 밖**: 프론트엔드 빌드/런타임 동작은 실행하지 않았다(plan 단계 리서치 중 `npm run dev` / `npm run build`를 실행하지 않음) — 이는 정적 소스 읽기에 한정된다. run 단계의 §C Pre-flight(plan.md)는 구현 시작 전에 실제 빌드/런타임 검증을 명시적으로 예정하고 있다.
