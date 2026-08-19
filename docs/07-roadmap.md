# 07. 로드맵 — 남은 작업

이번 단계(설계 문서 + Profile 스캐폴드 + Mock POS)에서 의도적으로 범위 밖에 두었거나 아직
검증하지 못한 항목입니다.

## 1. `code_execution → mock-pos` 네트워크 접근 가능 여부 실측 (완료)

**✅ 2026-08-19 실측 완료.** Docker가 실제로 설치·구동 중임을 확인한 뒤(`docker version`
정상 응답), `docker compose build && docker compose up -d`로 3개 컨테이너(hermes,
dashboard, mock-pos)를 실제로 기동했습니다. `order-payment-agent`에게 실제 챗으로 "아메리카노
2잔 주문해줘"를 요청한 결과, `code_execution` 샌드박스가 `http://mock-pos:8080`으로 실제
HTTP 호출을 보내 주문(`order_523290cde122`)과 결제(`pay_e0415289766d`, COMPLETED)를
생성했고, mock-pos API를 별도로 재조회해 재고가 20→18로 정확히 차감된 것까지 독립
검증했습니다.

다만 접속 정보 주입은 계획과 달랐습니다: **`code_execution` 샌드박스는 프로필의 `.env`를
자동으로 물려받지 않습니다.** 첫 시도에서 에이전트가 "세션에 MOCK_POS_BASE_URL/
MOCK_POS_API_KEY가 없다"며 값을 되물었습니다. 조치: 4개 POS 스킬의 레퍼런스 스크립트
기본값을 실제 배포 값(`http://mock-pos:8080`/`dev-key`/`store_demo`)으로 하드코딩했습니다
(Mock POS 키는 개발용 고정 키라 안전). [03장](03-hermes-agent-integration.md) 참고.

## 2. 위임 메커니즘(`terminal` 동기 호출) 실측 검증 (완료, 새 이슈 발견)

**✅ 2026-08-19 실측 완료.** `coordinator`에게 "베이글 1개 주문 들어왔어, 담당 에이전트한테
위임해서 처리해줘"를 요청한 결과, coordinator는 정확히 `terminal(command='/opt/hermes/bin/
hermes -p order-payment-agent chat -q "..."')` 형태로(설계대로 `delegate_task`가 아닌
방식으로) 위임했고, Mock POS에 실제 주문(`order_cce4fb24d44a`)과 결제(`pay_b8ddc57b5c00`,
COMPLETED)가 생성된 것을 coordinator 스스로 파일을 열어 검증(Active Verification)한 뒤
보고했습니다 — 검증 파일과 mock-pos API 값 모두 독립적으로 재확인해 일치함을 확인했습니다.

새로 발견한 두 가지:
1. **`terminal` 호출이 약 120초 후 타임아웃됩니다**(`exit 124`). 위 테스트에서 실제로
   타임아웃이 발생했지만, 하위 프로필(`order-payment-agent`) 프로세스는 백그라운드에서
   계속 실행되어 결과를 완성했고 고아 프로세스로 남지 않았습니다(`ps aux`로 확인). 이
   시나리오를 SOUL.md/SKILL.md에 반영해, coordinator가 타임아웃 응답만으로 실패를 단정하지
   말고 Active Verification으로 재확인하도록 이미 수정했습니다 — 실제로 coordinator는
   이렇게 행동했습니다.
2. **`kanban` 네이티브 툴이 coordinator에는 로드되지 않습니다**(`hermes doctor`: "runtime-
   gated; loaded only for dispatcher-spawned workers"). coordinator는 실제로 `kanban`
   툴 대신 `workspace/kanban/*.md` 파일을 스스로 만들어 카드를 관리했습니다. 설계 문서를
   이 실측 결과에 맞춰 "kanban 트래커"에서 "파일 카드"로 전면 수정했습니다.

## 3. `web`/`search` 툴셋 활성화 (신규 발견, 미착수)

`hermes doctor` 결과 `web`/`search` 툴셋은 `EXA_API_KEY`/`PARALLEL_API_KEY`/
`TAVILY_API_KEY`/`FIRECRAWL_API_KEY` 중 하나가 없으면 비활성 상태입니다. 현재
`customer-service-agent`/`marketing-crm-agent`는 이 키 없이 배포되어 있어 웹 검색 없이
내부 지식(FAQ 파일 등)만으로 동작합니다. 검색 provider 계약/키 확보 후 `.hermes/.env`에
추가하면 됩니다.

## 4. HITL 승인 대화 실측

`docs/06-hitl-approval-design.md`의 3개 게이트는 설계만 되어 있고, 실제 게이트웨이(Discord)
연결 후 `messaging`/`clarify` 툴셋으로 승인 대화가 의도대로 동작하는지 검증이 필요합니다.
(2026-08-19 테스트는 게이트 대상이 아닌 저위험 작업만 다뤄 이 항목은 여전히 미검증입니다.)

## 5. 실 POS 벤더 연동

`mock-pos/`는 Square API 오브젝트 구조를 참조한 시뮬레이터입니다. 실제 매장에 연결하려면
국내 POS 벤더 연동이 필요합니다.
- **토스플레이스 Open API**: 주문/결제/상품 데이터 서버 간 연동
- **카카오페이 오프라인결제/VAN 연동**: 대부분의 국내 POS가 이미 VAN 모듈로 연동됨
- 계약·인증 정보 확보 후, [05장](05-skills-and-tools.md)에서 정의한 Skill 절차의 REST
  호출 대상만 Mock POS에서 실 벤더 API로 교체하는 어댑터 방식을 제안합니다(인터페이스
  계약은 유지).

## 6. Mock POS 기능 보강 (완료)

- ✅ 환불 엔드포인트(`POST /payments/{payment_id}/refund`) 추가 — 결제/주문을
  `REFUNDED`로 전환하고 재고를 원상 복구한다. 게이트 3(환불/취소) 승인 후
  `order-payment-agent`가 실제로 호출한다.
- ✅ 예약 목록 조회 엔드포인트(`GET /reservations?date=&status=`) 추가 —
  `reservation-agent`가 "오늘 예약 몇 건" 같은 질문에 답할 수 있다.
- ✅ 매출/정산 리포트가 `REFUNDED` 결제를 매출에서 제외하고, 정산 리포트에는
  `refunded_amount`/`refunded_count`로 별도 표시하도록 수정했다.
- mock-pos pytest 스위트 7건 전체 통과, 4개 POS 스킬 레퍼런스 스크립트로 로컬 서버에
  대해 실제 실행까지 검증했다(환불/예약목록 포함).

## 7. 배포 자동화 (완료, 실제 검증도 완료)

`docker-compose.yml` 작성 완료([08장](08-docker-deployment.md)). **✅ 2026-08-19: 실제
`docker compose build/up`을 실행해 hermes/dashboard/mock-pos 3개 컨테이너가 모두 정상
기동함을 확인했습니다.** 포트(8651/9128/8080)도 형제 프로젝트와 충돌 없이 실제로 사용
가능함을 `docker ps`로 재확인했습니다.

## 8. 프로필별 챗 스모크 테스트 (부분 완료)

7개 프로필 모두 실제 챗 세션으로 최소 1회 구동해 SOUL.md 지시를 안정적으로 따르는지
확인이 필요합니다([10-usecase-tests.md](10-usecase-tests.md)). **2026-08-19 기준 3개
검증 완료**: coordinator(TC-01, 페르소나대로 응답), order-payment-agent(TC-02, 확인
절차 준수 + 실제 Mock POS 호출), coordinator→order-payment-agent 위임(TC-08). 나머지
4개 프로필(inventory-agent, reservation-agent, customer-service-agent,
sales-analytics-agent, marketing-crm-agent)과 HITL 3개 게이트는 아직 미검증입니다.

## 9. `kanban` 기반 다단계 시나리오 실행

"오늘 아메리카노 2잔 주문 → 재고 자동 반영 → 마감 후 매출 브리핑" 같은 하루 흐름을
`coordinator`가 진행 카드(`workspace/kanban/*.md`)로 관리하며 순차 위임·검증하는 것을
처음부터 끝까지 실행하는 시나리오([10-usecase-tests.md](10-usecase-tests.md))는 아직
미실시입니다(단일 주문 위임만 검증됨, 다단계 파이프라인은 미검증).

## 10. 업종별 특화 확장

`refs/idea.md` 4장에서 제안한 업종별 확장(카페/식당 메뉴 추천·웨이팅, 미용실 스타일
이력·디자이너 스케줄, 편의점 자동 발주·유통기한 관리)은 공통 프로필이 안정화된 뒤 각
프로필의 SOUL.md/Skill을 확장하는 방식으로 진행합니다. 이번 단계는 4개 업종 공통 기능만
다룹니다.
