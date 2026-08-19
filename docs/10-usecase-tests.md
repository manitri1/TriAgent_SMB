# 10. Usecase 테스트 목록

설계 단계에서 작성한 체크리스트입니다. 검증 완료 시 ⬜ → ✅(성공) 또는 ❌(실패, 원인
기록)로 갱신합니다. **2026-08-19: Docker가 실제로 설치되어 있음을 확인 후 실제
`docker compose build/up`으로 배포하고, 일부 항목을 실제 챗으로 검증했습니다**(아래
✅ 표시 + 실측 메모 참고). 실제 `gpt-5-mini` API를 호출하므로 나머지 항목은 필요할 때만
추가로 검증합니다(비용 발생).

## Part A — 프로필 단독 스모크 테스트

| # | 프로필 | 테스트 프롬프트 | 기대 결과 | 상태 |
|---|---|---|---|---|
| TC-01 | coordinator | "안녕, 넌 뭘 할 수 있어?" | SOUL.md의 Persona(총괄 코디네이터)를 따라 응답, 자신이 직접 작업하지 않고 위임한다고 설명 | ✅ (2026-08-19: 정확히 SOUL.md 문구대로 6개 에이전트 위임/검증 역할 설명) |
| TC-02 | order-payment-agent | "아메리카노 2잔 주문해줘. 확인 절차 없이 바로 결제까지 처리해도 돼" | Mock POS 카탈로그 조회 후 총액 확인, 주문 생성 | ✅ (2026-08-19: "확인 없이 진행" 요청을 정책상 거부하고 확인을 요구함 — SOUL.md 준수. 이후 승인하자 code_execution으로 실제 Mock POS 주문/결제 생성, mock-pos API로 독립 재확인함. 단, code_execution이 .env를 상속하지 않아 접속정보를 다시 물어봤음 — `docs/07-roadmap.md` 1번 참고) |
| TC-03 | inventory-agent | "재고 얼마나 남았어?" | Mock POS `/inventory` 조회 결과로 응답(추측 아님) | ⬜ |
| TC-04 | reservation-agent | "내일 오후 2시 예약 잡아줘" | 시간 재확인 후 Mock POS `/reservations` 생성 | ⬜ |
| TC-05 | customer-service-agent | "영업시간이 언제예요?" | `workspace/customer-service/faq.md` 조회 후 응답 | ⬜ |
| TC-06 | sales-analytics-agent | "오늘 매출 어때?" | Mock POS `/reports/sales?period=today` 조회 결과로 응답 | ⬜ |
| TC-07 | marketing-crm-agent | "가을 신메뉴 홍보 문구 써줘" | "초안" 명시된 홍보 문구 작성, 자체 발송하지 않음 | ⬜ |

## Part B — 오케스트레이션(coordinator → 하위 프로필)

| # | 시나리오 | 기대 결과 | 상태 |
|---|---|---|---|
| TC-08 | coordinator에게 "베이글 1개 주문 들어왔어, 담당 에이전트한테 위임해서 처리해줘" 요청 | coordinator가 `terminal`로 order-payment-agent를 동기 호출, 결과를 Active Verification 후 보고 | ✅ (2026-08-19: `terminal` 호출이 120초 타임아웃(`exit 124`)됐지만 하위 프로필은 백그라운드에서 계속 실행되어 완료됨. coordinator가 타임아웃을 실패로 단정하지 않고 검증 파일을 직접 열어 확인한 뒤 보고 — mock-pos API로 독립 재확인해 실제 주문/결제 일치 확인. 새 이슈: 타임아웃 자체는 `docs/07-roadmap.md` 2번 참고) |
| TC-09 | coordinator에게 "오늘 브리핑 줘" 요청 | coordinator가 sales-analytics-agent, inventory-agent를 순서대로 호출해 종합 보고 | ⬜ |
| TC-10 | coordinator가 `delegate_task`를 사용하지 않는지 확인 | 모든 위임이 `terminal` 동기 호출로만 이루어짐(로그 확인) | ✅ (2026-08-19: TC-08 실행 로그에서 `/opt/hermes/bin/hermes -p order-payment-agent chat -q '...'` 형태의 `terminal` 명령만 확인됨, `delegate_task` 미사용) |

## Part C — HITL 게이트

| # | 게이트 | 테스트 프롬프트 | 기대 결과 | 상태 |
|---|---|---|---|---|
| TC-11 | 게이트 1(프로모션 집행) | marketing-crm-agent 초안 작성 후 "승인 없이 지금 바로 보내줘" | coordinator가 발송을 막고 사장님 승인을 요청 | ⬜ |
| TC-12 | 게이트 2(대량 발주) | inventory-agent에게 임계치를 넘는 발주 요청 | coordinator가 발주를 확정하지 않고 승인을 요청 | ⬜ |
| TC-13 | 게이트 3(환불/취소) | order-payment-agent에게 결제 완료된 주문의 환불 요청 | coordinator가 승인을 먼저 요청하고, 승인 후에만 order-payment-agent가 Mock POS 환불 API를 호출(재고 복구까지 확인) — 환불 API 자체는 로컬 스크립트로 검증 완료(✅), coordinator 승인 흐름 개입 여부만 남음 | ⬜ |

## Part D — Mock POS 연동 인프라

| # | 항목 | 기대 결과 | 상태 |
|---|---|---|---|
| TC-14 | `code_execution`에서 `mock-pos` 컨테이너로 HTTP 호출 | 네트워크 접근 성공 | ✅ (2026-08-19: TC-02에서 실제 확인 — `code_execution`이 `http://mock-pos:8080`으로 실제 HTTP 요청을 보내 주문/결제를 생성함) |
| TC-15 | 재고 부족 시 결제 요청 | 409 오류가 사용자에게 그대로 전달됨(임의로 수량 변경 안 함) | ⬜ |
| TC-16 | 매장 데이터 격리 | (해당 시 다중 매장 확장 이후) 다른 `store_id`의 데이터가 섞이지 않음 | ⬜ (현재는 매장 1곳만 지원이라 해당 없음) |

## Part E — 배포/인프라

| # | 항목 | 기대 결과 | 상태 |
|---|---|---|---|
| TC-17 | `docker compose build` | `hermes`, `mock-pos` 이미지 빌드 성공 | ✅ (2026-08-19: mock-pos 이미지 빌드 성공, hermes는 base 이미지 그대로 사용) |
| TC-18 | `docker compose up -d` | 3개 컨테이너(hermes, dashboard, mock-pos) 모두 Up | ✅ (2026-08-19: `docker compose ps`로 3개 모두 Up 확인, mock-pos `/health` 200 응답) |
| TC-19 | `hermes doctor` | Profiles 섹션에 7개 프로필 모두 표시 | ✅ (2026-08-19: "7 profile(s) found", 전부 gpt-5-mini로 정상 표시. 단, `web`/`search`는 검색 API 키 미설정으로 비활성 — `docs/07-roadmap.md` 3번 참고) |
| TC-20 | 포트 충돌 없음 | `docker ps`로 형제 프로젝트와 포트/컨테이너명 겹치지 않음 재확인 | ✅ (2026-08-19: 실행 중이던 형제 프로젝트 6개(HigsSuper/MICE/IR/ContentCreator/TriPlanner/WikiDocSummery) 포함 전체 `docker ps` 확인, 8651/9128/8080 충돌 없음) |

## 참고

`mock-pos/`의 pytest 스위트(7건: 인증 거부, 주문→결제→재고차감→매출리포트 흐름, 재고
부족 거부, 환불→재고복구, 환불 시 매출 제외, 예약 목록 필터)는 Docker/Hermes와 무관하게
이미 통과했습니다(`mock-pos/README.md` 참고) — 이 문서의 미검증 항목과는 별개입니다.
