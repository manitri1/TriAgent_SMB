# 21. 마니카페 "사장님의 하루" — 헤르메스 에이전트 라이브 시연 환경 구축 계획

> 이 문서는 `course/260912_마니카페_사장님의_하루.md` 타임라인을 실제 VPS 배포(TriAgent_SMB) 위에서
> 라이브로 시연하기 위한 실행 계획이다. 아직 실행 전 단계이며, 각 항목이 실행되면 이 문서에
> 결과(✅/❌ + 날짜)를 갱신한다.

## Context

`course/260912_마니카페_사장님의_하루.md`(및 아티팩트)에서 만든 12개 타임라인 비교 스토리를,
실제로 VPS에 배포되어 있는 TriAgent_SMB(coordinator + 6개 에이전트, mock-pos, webapp,
Discord 봇) 위에서 **발표자가 본인 노트북 화면 공유로 12개 전체를 라이브 시연**할 수
있게 만드는 것이 목표다.

탐색 결과 이 시스템은 이미 실제로 배포되어 2일 이상 가동 중이고(Hostinger VPS,
`72.61.214.250`), CLI 챗/webapp 콘솔/mock-pos 대시보드/HITL 게이트 3곳이 과거에
실측 검증된 상태다. 하지만 "이미 검증됨"과 "청중 앞에서 안정적으로 재현 가능"은
다르다 — 특히 다음 3가지가 현재 확인되지 않은 리스크다:

1. **Hermes v0.21.0의 위험 명령 승인 차단**(`docs/07-roadmap.md` §11) — `code_execution`/
   `terminal`이 기본적으로 사람의 승인 없이는 mock-pos 호출을 막는다. CLI는 `--yolo`로
   해결 확인됐지만, **시연의 핵심 채널인 Discord에서 동일하게 막히는지는 아직 아무도
   확인하지 않았다.** 막힌다면 12개 타임라인 중 POS 호출이 필요한 절반이 Discord에서
   전부 실패한다.
2. **reservation-agent / sales-analytics-agent / marketing-crm-agent 3개 프로필은
   단독으로 한 번도 실행된 적이 없다**(runtime 디렉터리 없음) — coordinator 위임으로만
   간접 실행됐다. 청중 앞 첫 실행에서 예상 못한 오류가 날 위험이 있다.
3. **VPS의 mock-pos는 현재 시드 데이터가 비어 있다**(`catalog`/`inventory` 모두 `[]`,
   `docs/07-roadmap.md` §11 하단) — 로컬에서 쌓인 테스트 데이터는 VPS에 없다. 지금
   상태로는 재고 조회든 매출 조회든 전부 "데이터 없음"으로 나온다.

사용자 확인 사항(4가지 질문 응답):
- 시연 형식: **발표자 본인 노트북 화면공유** (원격/심사위원 직접조작 아님)
- 시연 범위: **12개 타임라인 전체**
- 공개 노출: **SSH 터널만 유지** — Traefik 공개 서브도메인 추가하지 않음
- "카카오톡" 표기: **문서를 Discord로 수정** (실제 연동은 Discord뿐)

추가로, Hermes Agent CLI 자체의 MCP 지원 여부를 조사했다. **1차 조사(이 저장소의
문서/스크립트만 grep)에서는 "MCP 미지원"으로 잘못 결론 냈으나, 사용자가 "설치
요청한 도구는 Hermes Agent 안에서 쓰는 도구"라고 정정**해, VPS에서 직접
`hermes mcp --help`를 실행해보니 **실제로 존재하는 네이티브 기능**이었다
(`hermes mcp add/list/catalog/install/login/reauth` 등, 프로필별 스코프 `-p <role>`
로도 동작 확인). 카탈로그에는 **Notion은 있지만 Gmail/Sheets/Drive는 없다** — 자세한
내용과 정정된 접근은 P6 참고. 사용자는 Gmail(공급사 견적 초안 발송)/Google Sheets
(마감 매출 리포트)/Notion(칸반 대체) **전부를 이번 시연 환경에 실제로 연동**하고,
**사전에 결과를 받아 보관해서 보여주는 것과 시연 중 실제 시도 둘 다** 원한다고
확인했다.

---

## P0 — 시연 전 반드시 해결해야 할 블로커

### B1. Discord 경로에서 위험 명령 차단이 실제로 걸리는지 확인 (최우선, 미확인 상태)

- VPS SSH 접속(`ssh smb-vps`) 후 CLI로 먼저 회귀 재현:
  `docker exec hermes-triagent-smb hermes chat --profile inventory-agent -q "아메리카노 재고 얼마나 남았어?"`
  → 차단 메시지(`[BLOCKED: ...]`) 재현 확인.
- 같은 질문을 `--yolo` 추가해 재실행 → mock-pos 실제 호출 성공 확인(단, 이 시점엔
  아직 시드 전이라 재고 자체는 "없음"으로 나올 수 있음 — 정상).
- **핵심 미확인 항목**: 실제 Discord `#smb-ops` 채널에서 `inventory-agent`나
  `order-payment-agent`에게 재고/주문 조회를 요청해보고 `[BLOCKED: ...]`가 뜨는지
  직접 관찰. `hermes chat --help`로 프로필 config.yaml 레벨에서 `--yolo`에 대응하는
  상시 설정 키(`yolo`/`auto_approve_risky` 등)가 있는지도 확인 — 있다면 데모 관련
  프로필들의 `config.yaml`에 미리 켜두는 것이 매번 `--yolo`를 챗 명령에 붙이는 것보다
  Discord/webapp 경로에도 일관되게 적용될 가능성이 높다.
- 결과에 따라 분기:
  - Discord도 정상 동작 → 원래 계획대로 다수 타임라인을 Discord로 시연.
  - Discord에서 막힘 → POS 호출이 필요한 타임라인(②⑥⑦⑩, 아래 표 참고)은 Discord
    대신 CLI 또는 webapp으로 옮기고, Discord는 텍스트 요약/승인 확인용(①⑫)으로만 사용.
- 확인 결과를 `docs/10-usecase-tests.md`와 `docs/07-roadmap.md` §11에 날짜 붙여 기록.

### B2. 한 번도 단독 실행 안 된 3개 프로필 사전 스모크 테스트

시드 데이터 투입(B3) 후, 데모 최소 하루 전에:
- `hermes chat --profile reservation-agent -q "내일 오후 2시에 김민수 고객 예약 잡아줘"`
- `hermes chat --profile sales-analytics-agent -q "오늘 매출 어때?"`
- `hermes chat --profile marketing-crm-agent -q "단호박 라떼 홍보 문구 초안 써줘"`

각각 정상 응답 여부와 실제 소요 시간을 기록. 실패 시 SOUL.md/SKILL.md/`.env` 누락을
그 자리에서 고칠 시간을 확보하기 위해 데모 당일이 아니라 최소 하루 전에 실행.

### B3. mock-pos 시드 + 대시보드 로그인 확인

- VPS mock-pos가 비어있으므로 반드시 시드 필요. 아래 P1의 새 시드 스크립트 실행.
- 대시보드(`:19128`) basic_auth는 로컬에 커밋되지 않은 상태로 로테이션되어 있어
  현재 비밀번호를 알 수 없다. `webapp/scripts/hash_password.py`와 동일한 방식으로
  새 scrypt 해시를 생성해 `.hermes/config.yaml`의 `dashboard.basic_auth.password_hash`를
  덮어쓰고 `docker compose restart dashboard` 후 SSH 터널로 로그인 확인.
  (새 비밀번호는 이 작업 중 사용자에게 알려드림.)

---

## P1 — 재현 가능한 시연 데이터

### 새 시드 스크립트: `mock-pos/scripts/seed_manicafe_dayinlife.sh`

기존 `seed_manicafe_demo.sh`(12개 메뉴, 아메리카노 `initial_stock=0`, 고객 6명, 주문
20여건, 환불 2건 — 이미 webapp 대시보드용으로 검증됨)를 **그대로 재사용(subprocess
호출)**하고, 12개 타임라인 스토리에 빠진 두 가지만 얹는 얇은 래퍼로 작성한다(기존
스크립트를 포크하지 않아 검증된 동작을 깨지 않음):

1. **예약 데이터**(③번 타임라인용) — `POST /reservations`로 오늘 예약 1건 + "내일
   오후 2시 김민수" 예약 1건(B2의 스모크 테스트 프롬프트와 동일 인물로 맞춤).
2. **컴플레인용 주문**(⑨번 타임라인용) — 특정 고객(예: `cust_donghyun`) 앞으로 주문 1건을
   추가하고, 발표 중 "이 손님 음료가 잘못 나갔다고 전화 왔다"고 구두로 지목할 수 있게
   스크립트 마지막에 해당 고객명/주문ID를 echo로 출력.

스크립트 마지막에 검증용 curl 3종(아메리카노 재고=0, 오늘 예약 목록, 오늘 매출 리포트)을
출력해 발표자가 시연 전 조용히 셀프 점검할 수 있게 한다.

전제(기존 스크립트와 동일한 제약, 스크립트 상단에 주석으로 명시):
- mock-pos는 인메모리라 재실행 전 `docker compose restart mock-pos` 필요(멱등적이지 않음).

### 기존 workspace 파일 정리

`.hermes/workspace/{kanban,po,inventory,orders,receipts}`에 2026-09-04/05 실제 실행
흔적(untracked 파일 다수)이 남아있어, 새로 시연할 때 에이전트가 옛 날짜 데이터를
언급하며 혼란을 줄 수 있다. 삭제 대신 이동:
`.hermes/workspace/_archive_2026-09/`로 날짜 있는 산출물 파일들을 옮기고,
`customer-service/faq.md`, `customer-service/complaints.md` 같은 정적 참조 파일은
그대로 둔다. 데모 당일 직전에 새로 쌓인 파일이 있으면 한 번 더 반복.

---

## P2 — 타임라인별 채널 매핑 (12개 전체, B1 결과 확정 전까지는 보수적 가정)

| # | 시간 · 장면 | 채널 | 비고 |
|---|---|---|---|
| ① | 05:30 아침 브리핑 | Discord `#smb-ops` | 텍스트 요약, POS 호출 불필요 — B1 결과 무관하게 안전 |
| ② | 06:30 재고 스냅샷 | CLI(+`--yolo`) 또는 webapp 재고 화면 | POS 호출 필요 — B1에서 Discord 막히면 여기로 |
| ③ | 07:00 예약 응대 | **webapp `/reservations`** (2026-09-11 화면 신설로 갱신 — 기존 "CLI 전용" 주석은 무효) | 데모 큐 "07:00 전화 예약 응대" 버튼 재사용, B2에서 리허설한 프롬프트와 동일 |
| ④ | 09:10 [게이트2] 결품+발주초안 | CLI 또는 webapp 재고 화면 | **공급사 견적 부분은 정직하게 서술** — 실제 API가 없으므로 "에이전트가 권한 밖이라 스스로 멈추고 초안만 작성"을 보여주는 것 자체가 데모 포인트 |
| ⑤ | 11:20 단체 문의 | webapp 고객문의 화면 또는 Discord | POS 의존 없음 |
| ⑥ | 12:00 [게이트3] 결제/환불 | webapp 주문접수 화면 | 2026-09-04 실측 검증된 경로(카푸치노 주문) 그대로 재사용 |
| ⑦ | 14:30 "오늘 매출 어때?" | CLI 또는 대시보드(`:19128`) `/chat` | 즉답 애널리틱스 — 브라우저 탭 유지 시 대시보드 chat 권장 |
| ⑧ | 15:30 [게이트1] 홍보초안 | CLI 또는 대시보드 `/chat` | marketing-crm-agent는 `messaging` 툴 자체가 없어 구조적으로 게이트1 우회 불가능함을 강조 |
| ⑨ | 17:10 컴플레인 | webapp 고객문의 화면 | P1에서 심어둔 컴플레인용 주문/고객 재사용 |
| ⑩ | 19:40 마감 정산 | mock-pos 대시보드(`:18080/dashboard`) + CLI "마감 리포트 정리해줘" | 유일하게 차트로 시각적 임팩트를 주는 지점 |
| ⑪ | 21:00 다음날 브리핑 초안 | Discord 또는 CLI | ①과 대칭, POS 의존 없음 |
| ⑫ | 23:00 승인 3건 확인 | Discord `#smb-ops` | 이미 온 메시지를 읽고 승인/거부만 하는 것이라 실행 리스크가 가장 낮음 |

전체적으로 3개 "거점"(webapp: ②④⑤⑥⑨ / CLI·대시보드챗: ①③⑦⑧⑪ / Discord: ①⑫)을
탭 2~3개로 왔다갔다 하는 정도로 최소화. 12개 전체를 다 보여주기로 했으므로 발표
시간이 상당히 필요함 — 사전 리허설로 각 장면 소요 시간을 재서 총 러닝타임을 확인할 것.

*(공개 URL을 추가하지 않기로 했으므로, 발표 전 SSH 터널(`ssh -L 19128:127.0.0.1:19128
-L 19131:127.0.0.1:19131 smb-vps`)이 켜져 있는지 프리플라이트에서 반드시 확인.)*

---

## P2.1 — 웹앱 데모 큐로 체크하는 시나리오 순서 (2026-09-11 추가)

P2 표 12개 중 **webapp 화면(②③④⑤⑥⑨)만 뽑아 실제 클릭 순서와 정확한 입력 프롬프트**를
정리한다. 각 화면 하단 "데모 n/총n" 버튼을 누르면 아래 문구가 입력창에 자동으로
채워지므로, 발표자는 타이핑 없이 버튼만 눌러가며 진행하면 된다(코드:
`webapp/webapp_bff/static/{orders,inventory,reservations}.js`,
`webapp/webapp_bff/templates/support.html`).

| 순서 | 시간 | 화면 | 데모 버튼 라벨 | 실제 입력 프롬프트 |
|---|---|---|---|---|
| 1 | 06:30 재고 스냅샷 | `/inventory` | (버튼 없음 — "새로고침" 클릭) | 프롬프트 없음, 읽기 전용 표 확인만 |
| 2 | 07:00 예약 응대 | `/reservations` | "07:00 전화 예약 응대 (사장님의 하루)" | `방금 전화로 예약 문의가 왔어요. 오늘 오후 6시 4명 예약 등록해주세요.` |
| 3 | 09:10 [게이트2] 결품+발주초안 | `/inventory` | "09:10 원두 결품 발견 (사장님의 하루, 승인 필요할 수 있음)" | 폼에 품목=아메리카노, 수량=50, 사유="원두 완전 품절, 긴급 대량 재입고 필요"가 채워지고, 제출 시 실제 전송 메시지는 `다음 품목 재입고를 요청합니다: 아메리카노 50개. 사유: 원두 완전 품절, 긴급 대량 재입고 필요.` |
| 4 | 11:20 단체 문의 | `/support` | "11:20 단체 주문 문의 (사장님의 하루)" | `20인분 단체 주문인데 오늘 오후 3시 픽업 가능할까요?` |
| 5 | 12:00 [게이트3] 결제 | `/orders` | "12:00 점심 피크 주문 (사장님의 하루)" | `라떼 2잔, 아메리카노 1잔 주문 들어왔어, 결제까지 처리해줘.` |
| 5-1 | (게이트3 환불 시연 이어서) | `/orders` | "환불 요청 (승인 필요)" | `방금 카푸치노 주문 환불해줘, 고객이 취소를 요청했어.` (기존 범용 데모 항목 재사용 — 5번 주문과 품목이 다르므로 발표 시 "다른 주문 건" 정도로 자연스럽게 언급) |
| 6 | 17:10 컴플레인 | `/support` | "17:10 컴플레인 응대 (사장님의 하루)" | `아까 주문한 라떼가 다른 음료로 잘못 나왔어요.` |

**주의**: 4·6번은 같은 `/support` 화면의 데모 큐(순차 진행)에 같이 들어있어, 4번을 먼저
누르고 응답을 받은 뒤 큐가 6번으로 자동 전진한다 — 중간에 "영업시간 문의"류의 기존
항목 2개(주차·와이파이)를 건너뛰려면 "처음부터" 버튼 옆 큐를 두 번 더 눌러 넘기거나,
직접 입력창에 타이핑해도 된다. 3번(재고)과 5번(주문)도 각 화면의 데모 큐 맨 앞/중간에
있으므로 마찬가지로 필요시 건너뛴다.

각 화면의 실제 데모 큐 전체 목록과 회귀 테스트는
`webapp/tests/test_pages.py::test_demo_queues_cover_manicafe_day_in_life_story` 참고.

**2026-09-11 추가**: 위 6개 화면별 데모 큐와는 별개로, **12개 타임라인 전체(①~⑫)를
한 화면에서 순서대로 진행**할 수 있는 `/live-demo` 화면을 신설했다(발표자가 탭을
옮겨다니지 않고 하나의 화면에서 전체 스토리를 이어갈 수 있게). 장면마다 프롬프트가
미리 채워져 있고, 전송하면 응답을 받은 뒤 자동으로 다음 장면으로 넘어간다(기존
demoQueue와 동일한 클릭-진행 방식). 장면별로 결과를 확인할 수 있는 화면(재고/예약/
주문/고객문의/대시보드) 링크도 함께 표시된다. Discord/CLI/mock-pos 대시보드가 실제
채널인 장면(①②⑦⑧⑩⑪⑫)은 `/api/agent/message`가 `coordinator`/
`customer-service-agent` 외 profile을 허용하지 않는 구조적 제약(`webapp_bff/routers/
agent.py`) 때문에 동일한 프롬프트를 `coordinator`에게 보내 webapp에서 대체
시연한다 — 실제 시연에서는 P2 표대로 원래 채널(Discord/CLI/대시보드)을 쓰고,
`/live-demo`는 리허설·백업용 단일 화면으로 우선 취급한다. 코드:
`webapp/webapp_bff/templates/live_demo.html`, `webapp/webapp_bff/static/live_demo.js`.
pytest는 통과했으나 컨테이너 환경에서 12개 전체를 실제로 눌러보는 리허설(P4)은
아직 미실행.

⬜ **아직 실측 검증 전** — 위 6개 항목은 코드에 데모 프롬프트로 반영되고 pytest(구조
검증)는 통과했지만, 컨테이너 환경에서 실제로 coordinator/customer-service-agent가
정상 응답하는지까지 확인하는 것은 B2(3개 프로필 스모크 테스트)·P4(리허설) 단계에서
함께 진행한다.

---

## P3 — 문서 수정: "카카오톡" → "디스코드" (✅ 2026-09-11 완료)

`course/260912_마니카페_사장님의_하루.md`와 `.html` 양쪽에서 실제 연동과 다른 "카카오톡" 표기를
"디스코드"로 교체 (사용자 확인됨):
- hero 안내문: "확인은 카카오톡·디스코드·웹 콘솔 어디서든 가능합니다." → "확인은
  디스코드·웹 콘솔 어디서든 가능합니다."
- 05:30 행: "카카오톡에 도착해 있다" → "디스코드에 도착해 있다"
- 23:00 행: "카카오톡에 뜬 승인 대기 3건" → "디스코드에 뜬 승인 대기 3건"
- HTML의 동일 위치도 동기화.

**추가로 함께 정리한 것(사용자 요청 "이 앱/헤르메스 에이전트에서 구현 가능한 것으로
변경"에 따라 범위 확장)**:
- 07:00 예약 행: "예약 전화와 문의를 접수하고" → 전화 응대 자체는 여전히 사람이
  하고, 접수된 내용을 웹 콘솔에 입력하면 `reservation-agent`가 등록하는 흐름으로 수정
  (음성 인식 기능이 없으므로 AI가 전화를 직접 받는 것처럼 보이지 않게).
- 11:20 단체 문의 행: "카톡으로" → "전화와 문자로"(Before), "웹 고객문의 창구로
  들어온"(After) — 실제 채널(webapp 고객문의 화면)에 맞춤.
- 15:30 마케팅 행: "승인하면 바로 게시된다" → "승인하면 사장님이 직접 게시한다"로
  수정 — `marketing-crm-agent`는 광고 플랫폼 자동 게시 연동이 없고 승인 후에도
  "수동 집행 안내"만 한다는 실제 설계([06-hitl-approval-design.md](06-hitl-approval-design.md))와
  맞춤.
- 17:10 컴플레인 행: 채널을 "웹 고객문의 창구"로 명시.
- 하단에 "구현 가능 범위에 대한 참고" 각주 신설 — 전화/음성 응대는 사람 담당, 야간
  자동 브리핑(05:30/21:00)은 Hermes 프로필별 `cron`으로 구현 가능하나 아직 미검증임을
  명시.

---

## P4 — 리허설용 시연 진행표 (신규 문서)

`docs/22-live-demo-run-of-show.md` 작성: 12개 타임라인 각각에 대해
- 정확한 명령/클릭 순서 (P2 매핑 반영)
- 예상 응답(1~2줄 요약, 발표자가 성공 여부를 한눈에 알 수 있게)
- 실패/지연 시 대응 멘트(특히 ④는 "느린 게 아니라 여기서 멈추는 게 의도"라는 설명이
  곧 리커버리 멘트)

문서 맨 위에 프리플라이트 체크리스트: mock-pos 재시작 → `seed_manicafe_dayinlife.sh`
실행 → workspace 아카이빙 → 대시보드 로그인 확인 → SSH 터널 확인 → ②④⑥⑦⑩(POS
의존 구간) 무음 드라이런 1회.

---

## P5 — 사소한 문서 버그 정리

- `mock-pos/README.md:43` 예시의 `STORE="store_cafe_001"` → `STORE="store_demo"`로 수정
  (실제 배포값과 불일치, 그대로 따라하면 404).
- ~~`docs/17-vscode-remote-connection.md`의 포트포워딩 예시(`9130`)를 실제 `docker-compose.yml`
  바인딩값(`9131`)으로 수정~~ — 2026-09-07 포트 재배치(1xxxx 대역) 작업 때 `19131`로
  함께 갱신되어 해결됨.

---

## P6 — 실제 외부 연동 추가 (Gmail 초안 / Google Sheets / Notion)

**2026-09-07 정정**: 이전 버전은 "Hermes에는 MCP가 없다"고 결론 내렸는데, 이는 이
저장소 안의 문서/스크립트만 grep한 결과였다. VPS(이 세션이 직접 실행 중인 그 머신)의
`hermes-triagent-smb` 컨테이너에서 `docker exec hermes-triagent-smb hermes mcp --help`를
**직접 실행**해보니 `mcp`는 실제 top-level 명령이며(`add/remove/list/test/configure/
login/reauth/picker/catalog/install/serve`), Nous가 승인한 원클릭 카탈로그(`hermes mcp
catalog`)도 실제로 채워져 있다(airtable/notion/square/stripe 등 60여 개). **사용자가
말한 "설치 요청한 도구는 Hermes Agent 안에서 쓰는 도구"라는 정정이 맞았다** — 아래
내용을 이 사실에 맞춰 다시 쓴다.

확인된 사실(전부 VPS에서 직접 실행해 확인):
- `hermes mcp catalog`에 **`notion`은 있다**("Pages and databases from your Notion
  workspace") — `hermes mcp install notion` 한 줄로 설치 가능(OAuth 동의 절차 필요).
- `hermes mcp catalog`에 **Gmail/Google Sheets/Drive/Docs는 없다**(카탈로그 전체를
  "google/gmail/sheet/drive/docs" 키워드로 확인, 전부 무관한 항목만 매칭). 이 셋은
  `hermes mcp add <name> --command <cmd> --args ... --auth oauth` 형태로 **일반
  MCP 서버(예: 커뮤니티에서 배포하는 Google Workspace MCP 서버)를 수동 등록**해야
  한다 — 어떤 구체적인 서버 패키지를 쓸지는 아직 조사 전이라 다음 실행 단계에서
  확정해야 한다(추측으로 아무 npm 패키지명을 적지 않음).
- **프로필별 스코프**: `hermes profile show inventory-agent` → `Path: /opt/data/
  profiles/inventory-agent`. 각 프로필은 정말로 격리된 홈 디렉터리이고,
  `hermes -p <role> mcp list`처럼 `-p <role>`을 붙이면 그 프로필 스코프로 명령이
  실행된다(직접 실행해 확인 — `-p inventory-agent`로도 정상 동작, 빈 목록 반환).
  즉 "이 MCP 서버는 coordinator만 쓴다"처럼 프로필별로 다르게 붙일 수 있다.
- 각 프로필의 `config.yaml`을 grep해봐도 `mcp`/`plugins` 키가 전혀 없다 — 즉
  MCP 서버 설정은 `config.yaml`이 아니라 **`mcp add`/`install` 실행 시 새로 생기는
  별도 파일**에 저장되는 것으로 보인다. 아직 실제로 하나도 추가해본 적이 없어
  정확한 파일 경로/형식은 다음 실행 단계에서 실제로 `hermes -p <role> mcp add ...`를
  한 번 돌려보고 확인해야 한다 — **이때 그 파일이 `.gitignore`에 걸리는지도 반드시
  같이 확인**(현재 `.gitignore`의 `.hermes/**/*.lock` 등 패턴에 새 MCP 상태 파일이
  우연히 걸리는지는 검증되지 않았음 — 안 걸린다면 자격증명이 그대로 git에 노출될
  위험이 있으므로 실제로 파일이 생기는 걸 보기 전까지는 진짜 자격증명을 넣지 않는다).

### 결정: 카탈로그에 있는 것과 없는 것을 다르게 다룬다

- **Notion** → `hermes mcp install notion`(또는 대상 프로필에 `-p coordinator mcp
  install notion`)으로 **네이티브 MCP 경로**를 그대로 쓴다. OAuth 동의는 1회, 사람이
  개입해야 하므로 이 세션에서 브라우저 동의 화면까지는 대신 눌러줄 수 없다 —
  실행 단계에서 사용자에게 동의 링크를 전달하거나, 화면공유로 함께 진행한다.
- **Gmail / Google Sheets** → 카탈로그에 없으므로 두 가지 경로 중 선택해야 한다
  (실행 전 사용자 확인 필요):
  (a) `hermes mcp add`로 등록 가능한 **기성 커뮤니티 MCP 서버**를 찾아 쓴다(조사
  필요 — 신뢰할 수 있는 유지보수 상태인지 먼저 확인해야 함), 또는
  (b) 기존 계획대로 **code_execution 스킬이 REST API를 직접 호출**하는 방식(마니카페
  저장소가 mock-pos에 이미 쓰고 있는 패턴)을 유지한다.
  MCP 경로가 되면 "설치 요청한 도구=Hermes 안에서 쓰는 도구"라는 사용자 의도에 더
  맞고, 자격증명 저장/재인증(`hermes mcp login`/`reauth`)도 Hermes가 대신 관리해준다는
  장점이 있다 — 다음 실행 단계에서 커뮤니티 서버를 하나 찾아 실제로 `hermes mcp add`가
  붙는지 검증한 뒤 (a)/(b) 중 최종 확정한다.

### 보안: 자격증명은 git에 절대 커밋하지 않는다

MCP 경로든 code_execution 스킬 경로든 마찬가지로 지켜야 하는 원칙:
`.gitignore`를 확인한 결과 `.hermes/profiles/*/skills/*`는 기본적으로 전부
git-무시 대상이고, `orchestration`/`pos`/`support`/`marketing` 4개 카테고리만
예외로 추적된다. mock-pos의 `dev-key`는 가짜 개발용 키라 SKILL.md에 리터럴로
박아 넣고 커밋해도 안전했지만, **Gmail/Sheets/Notion 자격증명은 실제 계정 권한을
가진 진짜 비밀정보**라 같은 방식을 쓰면 안 된다.
- MCP 경로: `mcp add/install/login`이 실제로 만드는 파일이 어디인지 먼저 확인하고,
  `.gitignore`에 걸려있지 않으면 그 경로를 새로 추가한다(위 "확인된 사실" 참고 —
  아직 미검증).
- code_execution 스킬 경로로 가게 될 항목이 있다면: 새 스킬 카테고리 이름을
  `skills/integrations/`로 만들고 `.gitignore`에 예외 추가를 **하지 않는다** →
  자동으로 git-무시됨. 커밋되는 건 `docs/23-external-integrations.md`에 담을
  **자격증명을 뺀 설계 설명(placeholder 값)** 뿐이다.
- Gmail은 "발송"이 아니라 **초안(draft) 생성** 권한(`gmail.compose`)만 쓴다 —
  실수로 실제 이메일이 나가는 사고를 원천적으로 차단.

### 사용자가 준비해서 나에게 전달해야 하는 것

1. **Notion** — `hermes mcp install notion` 실행 시 뜨는 OAuth 동의 화면에서 본인
   워크스페이스로 로그인/승인(화면공유로 같이 진행하거나, 링크만 전달받아 사용자가
   직접 클릭). 시연용 데이터베이스/페이지는 사전에 만들어두면 좋음.
2. **Google Sheets / Gmail** — (a) 경로(MCP)로 갈지 (b) 경로(직접 REST)로 갈지
   다음 실행 단계에서 커뮤니티 MCP 서버 조사 후 확정 → 확정된 경로에 맞는 자격증명만
   요청(MCP면 그 서버가 요구하는 OAuth 클라이언트, 직접 REST면 이전 버전에 적었던
   서비스계정 JSON/OAuth 3종).

### 구현 (신규, VPS 로컬 전용 파일 — 최종 경로 확정 후 채움)

- `coordinator` 또는 지정 프로필에 `hermes -p <role> mcp install notion` 실행 +
  워크플로 중 어느 시점에 어떤 프로필이 Notion을 호출할지는 P2의 ①/⑪(브리핑) 지점
  유지.
- Gmail/Sheets는 (a)/(b) 확정 후 이 섹션을 갱신 — (b)로 가면 이전 버전에 적었던
  `skills/integrations/supplier_email_draft/SKILL.md`,
  `skills/integrations/sheets_report/SKILL.md` 그대로 유효.

### 사전 결과 확보 + 시연 시도 (사용자 요청: 둘 다)

각 스킬을 실제로 한 번 미리 실행해 결과를 남긴다:
1. 데모 최소 하루 전, 위 3개 스킬을 각각 CLI로 1회 트리거 → 실제로 생성된 Gmail
   초안 스크린샷, Notion 페이지 링크, Sheets에 기록된 행을 캡처.
2. 이 캡처들을 `course/`에 백업 자료로 저장(발표 중 API가 느리거나 실패해도 보여줄
   수 있는 안전망).
3. 실제 라이브 시연에서는 P2 표의 해당 지점(④ Gmail 초안, ⑩ Sheets 기록, ①/⑪ Notion
   미러링)에서 **실시간으로 다시 트리거를 시도** → 되면 라이브로 보여주고, 안 되면
   즉시 1번의 캡처로 전환("방금 전 미리 실행한 결과가 여기 있습니다"로 자연스럽게
   넘어가는 멘트를 P4 진행표에 포함).

### P2 채널 매핑 갱신

- ④ (게이트2, 발주초안): 기존 "공급사 견적 요청은 초안뿐" 서술에 **Gmail 초안 생성**
  단계를 추가 — "권한이 없어 못 보낸다"가 아니라 "초안까지 만들고, 발송은 사장님이
  버튼을 누른다"로 스토리가 한 단계 더 강해짐.
- ⑩ (마감 정산): mock-pos 대시보드 + CLI 리포트에 **Sheets 기록 확인** 단계 추가.
- ①/⑪ (브리핑): Discord 텍스트 요약에 **Notion 카드 동기화 확인** 단계 추가(브라우저
  탭에서 Notion 페이지를 잠깐 보여줌).

---

## 주요 신규/변경 파일

- `mock-pos/scripts/seed_manicafe_dayinlife.sh` (신규) — 기존 시드 재사용 + 예약/컴플레인 데이터 추가
- `docs/22-live-demo-run-of-show.md` (신규) — 리허설용 시연 진행표
- `docs/23-external-integrations.md` (신규) — Gmail/Sheets/Notion 연동 설계(자격증명 제외, placeholder)
- `.hermes/profiles/inventory-agent/skills/integrations/supplier_email_draft/SKILL.md` (신규, git-무시)
- `.hermes/profiles/sales-analytics-agent/skills/integrations/sheets_report/SKILL.md` (신규, git-무시)
- `.hermes/profiles/coordinator/skills/integrations/notion_kanban_mirror/SKILL.md` (신규, git-무시)
- `.hermes/config.yaml` — dashboard basic_auth 해시 로테이션
- `course/260912_마니카페_사장님의_하루.md` / `.html` — "카카오톡"→"디스코드" 표기 수정 + Gmail/Sheets/Notion 반영 + "웹앱에서 테스트하기" 표 신설(2026-09-11)
- `webapp/webapp_bff/templates/reservations.html`, `webapp/webapp_bff/static/reservations.js` (신규, 2026-09-11) — 예약 관리 화면(③번 타임라인용)
- `webapp/webapp_bff/templates/support.html`, `webapp/webapp_bff/static/{orders,inventory}.js` — "사장님의 하루" 시나리오에 맞춘 데모 큐 항목 추가(2026-09-11, P2.1 참고)
- `webapp/webapp_bff/templates/live_demo.html`, `webapp/webapp_bff/static/live_demo.js` (신규, 2026-09-11) — 12개 타임라인 전체를 한 화면에서 순서대로 진행하는 "라이브 데모" 화면(P2.1 하단 참고)
- `mock-pos/README.md`, `docs/17-vscode-remote-connection.md` — 사소한 버그 수정
- `.hermes/workspace/_archive_2026-09/` (신규 디렉터리) — 기존 실행 흔적 아카이빙

## 실행 순서 요약

1. B1 (Discord 차단 여부 확인) → 분기 결정 → P2 표 확정
2. P1 시드 스크립트 작성 + 실행, workspace 아카이빙
3. B3 대시보드 비밀번호 로테이션
4. B2 3개 프로필 스모크 테스트
5. P6 자격증명 수령(사용자로부터 Notion 토큰 / Sheets 서비스계정 JSON / Gmail
   OAuth 3종) → 3개 신규 스킬 작성 → 각 1회 실행해 사전 결과 캡처 → `course/`에 백업
6. P3 문서 표기 수정("카카오톡"→"디스코드", P2 갱신 내용 반영)
7. P5 사소한 버그 수정
8. P4 진행표 작성(Gmail/Sheets/Notion 라이브 시도 + 백업 전환 멘트 포함)
9. 전체 리허설 1회(가능하면 데모 전날) — 러닝타임 측정 포함

## 검증 방법

- B1: VPS Discord 채널에서 직접 질문 후 관찰(스크린샷/로그).
- B2/B3: 각 명령의 stdout 저장, `docs/10-usecase-tests.md`에 새 TC로 기록.
- P1: 시드 스크립트 실행 후 echo된 검증 curl 3종을 직접 실행해 기대값과 대조.
- P6: 3개 스킬 각각 실행 후 실제 Gmail 초안함/Google Sheet/Notion 페이지를 직접
  열어 내용이 일치하는지 확인(Active Verification과 동일한 원칙) — 캡처한 백업
  자료도 `course/`에 실제로 저장됐는지 확인.
- 전체: `docs/22-live-demo-run-of-show.md`를 처음부터 끝까지 실제로 따라가며 12개
  전부 완주 — 중간에 실패하는 지점이 있으면 그 지점만 재점검 후 문서 갱신.
