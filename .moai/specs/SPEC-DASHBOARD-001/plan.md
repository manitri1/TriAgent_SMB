# Plan — SPEC-DASHBOARD-001

## §A Context (맥락)

이 SPEC은 이미 상당히 진척된 기능을 공식화한다: `smb-dashboard/`가 디스크에 존재하며(FastAPI 백엔드 + React/Vite 프론트엔드, git에는 아직 추적되지 않음) `docs/13-mvp-dashboard-design.md`의 설계 대부분을 구현하고 있다. plan 단계의 역할은 그린필드 구축보다 좁다 — (1) 이미 동작하는 부분을 명시하여 run 단계가 재구현이 아닌 검증을 수행하도록 하고, (2) 검증된 두 가지 미해결 격차를 실제 신규 작업 마일스톤으로 범위화하는 것이다.

이는 **독립형(standalone) SPEC**이다(현재 다중 SPEC Epic 그룹화는 없음). 이 SPEC은 UI 화면을 정의하므로(spec.md §4: 다섯 개의 구체적인 프론트엔드 화면 산출물) **plan → design → run** 경로를 따른다. 팀 공유 방식은 `solo`이며(`.moai/project/interview.md` Stage B Round 4 기준) — 팀원 간 파일 소유권 분할은 필요하지 않다.

개발 방법론: `constitution.development_mode: ddd`(`.moai/config/sections/quality.yaml`) — ANALYZE-PRESERVE-IMPROVE가 여기에 적합한 방법론이다. `smb-dashboard/` 하위 코드베이스 대부분이 이미 존재하며, run 단계의 역할은 개선(REQ-014–018)에 앞서 기존 동작(REQ-001–013)을 특징화(characterize)하고 보존하는 것이 대부분이기 때문이다.

## §B Known Issues (알려진 이슈)

- **Git 미추적 상태**: `smb-dashboard/` 디렉터리 전체가 현재 git에 추적되지 않은 상태다(`git status`로 확인됨). run 단계의 첫 번째 커밋이 이 코드가 버전 관리에 처음 들어가는 시점이 된다 — 특징화 테스트는 가정된 이전 git 이력이 아니라 현재 디스크 상의 실제 동작을 기준으로 작성해야 한다.
- **`decided_by`가 항상 `"owner"`로 하드코딩됨**: `approvals_store.decide_approval()`은 `decided_by: str = "owner"`를 기본값으로 지정하며, 어느 호출부(`approvals.py` 라우터도, Hermes `task_dispatch_and_verification` 스킬의 Discord 동기화 PATCH도)도 이를 재정의하지 않는다. 이는 Success Metrics 분석(spec.md §2.3)에서 드러난 실제 한계이지만, 이 SPEC의 해결 범위는 명시적으로 아니다(spec.md § Out of Scope — Success-Metric Instrumentation 참조).
- **`pytest-httpx`가 선언만 되어 있고 사용되지 않음**: `requirements-dev.txt`에 이미 개발 의존성으로 등록되어 있으며, REQ-017에서 처음으로 사용된다. 새로운 의존성 추가는 필요 없고 — 새 테스트 파일만 추가하면 된다.
- **프론트엔드에는 테스트 도구가 설정되어 있지 않음**(`package.json`에는 `dev`/`build`/`preview`만 정의됨). 따라서 REQ-015–016(주문 필터의 프론트엔드 측)은 자동화된 프론트엔드 테스트 스위트가 아니라 렌더링된 DOM에 대한 특징화/수동 스모크 체크로 검증한다 — 테스트 스위트를 새로 구축하는 것은 이 SPEC의 범위 밖이다.

## §C Pre-flight (사전 점검)

M1을 시작하기 전, run 단계는 다음을 확인해야 한다:
- `smb-dashboard/backend`가 문제없이 설치되며(`pip install -r requirements.txt -r requirements-dev.txt`) 기존 `test_approvals.py`에서 `pytest`가 정상 통과한다(DDD의 "이전(before)" 기준선을 확립).
- `smb-dashboard/frontend`가 문제없이 빌드되며(`npm ci && npm run build`) — 필터 UI가 추가되기 전 현재 TypeScript가 오류 없이 컴파일됨을 확인한다.
- Docker Compose가 4개 서비스를 모두 정상 기동하고 `curl http://127.0.0.1:8652/health`가 `{"status": "ok"}`를 반환한다(docs/13 §6에 명시된 "컨테이너는 떠 있지만 내부적으로는 죽어 있는" 사례에 대한 명확한 경고에 따라 — 컨테이너 상태뿐 아니라 실제 런타임 응답을 검증한다).

## §D Constraints (제약 조건)

- 항목별 재고 부족 임계값 없음, 실시간 WebSocket/SSE 없음, 단일 `store_id` / 다중 매장 또는 i18n 없음(docs/13 §8, spec.md § Out of Scope에도 명시 — 이는 해소해야 할 격차가 아니라 사전 승인된 MVP 경계다).
- 주문 필터에는 새로운 백엔드 의존성을 추가하지 않는다 — `status`는 `Literal` 타입 제약이 적용된 일반 FastAPI 쿼리 파라미터이며, 이는 `reservations.py`의 기존 패턴(검증 없는 `Optional[str]`)과는 다른, 프록시 라우터 중 이러한 엄격한 검증 스타일이 처음 적용되는 사례다.
- CSS 프레임워크 없음, 프론트엔드 라우터 없음 — 필터 UI는 기존의 손으로 작성된 `App.tsx` 탭 전환 + 순수 `styles.css` 관례를 따라야 한다(TRUST 5 Readable: 기존 파일 스타일과 일치시킬 것).
- 커버리지 목표: 85%(`quality.yaml`의 `constitution.test_coverage_target`)는 신규 라우터 테스트 파일(REQ-017–018)에 적용된다.

## §E Self-Verification (자기 검증)

run 단계 완료를 선언하기 전에 다음 사항이 (주장이 아니라) 근거를 갖고 명확히 참이어야 한다:

- `smb-dashboard/backend/`에서 실행한 `pytest`가 네 개의 프록시 라우터(`orders`, `inventory`, `reservations`, `reports`) 모두에 대해 `pytest-httpx`로 모킹된 테스트 케이스를 보여주며, 커버리지 리포트가 `app/`에 대해 85% 이상을 나타낸다.
- 수동 또는 스크립트 기반 체크로 `GET /api/orders/today?status=OPEN`(및 `COMPLETED`/`CANCELED`/`REFUNDED` 각각)이 일치하는 주문만 반환하고, `GET /api/orders/today`(파라미터 없음)는 현재 동작과 변함이 없음을 확인한다(회귀 없음).
- Orders 화면이 필터 컨트롤을 렌더링하고 선택 시 다시 데이터를 가져옴을 확인한다(프론트엔드 테스트 하니스가 없으므로 브라우저/개발 서버 스모크 체크로 검증).
- 기존 `test_approvals.py`가 수정 없이 여전히 통과한다(REQ-005–008 동작에 대한 특징화 테스트 — M1/M2가 승인 플로우를 회귀시키지 않았음을 증명).

## §F Milestones (마일스톤, 우선순위 기반, 의사결정 가역성 순으로 정렬)

마일스톤은 되돌리기 가장 어렵고 결과가 큰 결정을 먼저 검토하도록 정렬되어 있다. 기계적/검증 작업은 마지막으로 미룬다.

1. **M1 — 주문 상태 필터: API 계약 결정** (우선순위: High). `GET /api/orders/today`에 대한 `status` 쿼리 파라미터 형태(REQ-014)와 이에 대응하는 프론트엔드 fetch/렌더링 로직(REQ-015–016)을 결정하고 구현한다. 이는 재검토가 필요할 가능성이 가장 높은 마일스톤이다 — 기존 엔드포인트에 대한 공개 API 표면 변경(새 쿼리 파라미터)이자 새로운 프론트엔드 상태(선택된 필터) 항목이므로, 조정 비용이 가장 저렴할 때 먼저 검토한다.
2. **M2 — 프록시 라우터 테스트 커버리지** (우선순위: High). `orders.py`, `inventory.py`, `reservations.py`, `reports.py`에 대해 `pytest-httpx` 기반 테스트를 추가한다(REQ-017–018). 기계적이고 부가적인 작업이며 프로덕션 코드의 인터페이스 변경이 없다 — M1 이후로 배치한 이유는 M1의 새로운 `status` 파라미터도 자체 테스트 케이스가 필요하므로, M2가 자연스럽게 M1의 표면도 함께 커버하기 때문이다.
3. **M3 — 전체 시스템 검증 패스** (우선순위: Medium). 이미 구현된 기능에 대한 검증 요구사항(REQ-001–013)을 실제로 기동 중인 docker-compose 스택을 대상으로 실행한다: 인증 미들웨어, 502 변환, 승인 듀얼 채널 409 동작, 다섯 개 화면 전체의 렌더링을 확인한다. 여기서는 새 코드가 생성될 것으로 기대하지 않는다 — FAIL이 나온다면 docs/13 대비 실제 회귀가 드러난 것이며, 이는 M1/M2에 조용히 흡수되지 않고 그 자체로 새로운 블로커가 된다.

## §G Anti-Patterns (안티패턴)

- REQ-001–013 중 어느 것도 처음부터 다시 구현하지 **않는다** — 코드는 이미 존재하고 동작하고 있다. DDD ANALYZE-PRESERVE-IMPROVE 사이클을 적용한다(테스트로 현재 동작을 특징화한 뒤, 실제 결함이 발견된 경우에만 손을 댄다).
- `decided_via` 채널 필드, 대시보드 오픈 로깅, 409/502 카운터를 이 SPEC의 일부로 추가하지 **않는다** — Success Metrics 분석에서 드러났음에도 불구하고 명시적으로 범위 밖이다(spec.md § Out of Scope — Success-Metric Instrumentation).
- 필터 UI를 만들기 위해 CSS 프레임워크나 라우터 라이브러리를 도입하지 **않는다** — 기존의 손으로 작성된 관례를 따른다.
- 필터 컨트롤의 배치와 스타일링에 관한 시각/디자인 결정을 임의로 건너뛰지 **않는다** — 이는 (UI 화면 포함 조건부 경로에 따라) 임의의 run 단계 결정이 아니라 디자인 단계(`manager-design`)를 거쳐야 한다.

## §H Cross-References (교차 참조)

- `docs/13-mvp-dashboard-design.md` — 위에서 참조한 모든 섹션의 권위 있는 설계 소스
- `docs/06-hitl-approval-design.md` — 이 SPEC의 승인 큐가 병행하여 동작하는 기존 Discord HITL 플로우
- `.hermes/profiles/coordinator/skills/orchestration/task_dispatch_and_verification/SKILL.md` — 승인 큐에 대한 Hermes 측 통합 지점(§ "구조화 승인 큐 연동")
- `.moai/project/{product,structure,tech}.md` — 이 SPEC의 용어와 기술 스택 인용의 출처가 되는 프로젝트 문서
- `design.md` — manager-design 핸드오프를 위한 디자인 의도 초안(UI 화면 포함 조건부 경로)
- `research.md` — spec.md §1.1의 "구현 완료 vs 미해결 격차" 분류에 대한 코드베이스 분석 근거 자료
