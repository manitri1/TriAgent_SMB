# 14. 웹앱 사용 가이드 — 마니카페 운영 콘솔

> 2026-09-04: `webapp/`를 실제로 빌드·배포하고, 4화면 전부 실제 컨테이너 환경에서
> curl/pytest로 검증했습니다(pytest 30건 통과). 화면 2(주문 접수)에서 실제로 "카푸치노
> 1잔" 주문을 넣어 mock-pos에 반영되고 대시보드 매출에 합산되는 것까지 end-to-end로
> 확인했습니다. Playwright(headless Chromium)로 4화면 + 다크모드 스크린샷까지 촬영해
> 시각적으로도 확인했습니다 — Pretendard 웹폰트, 마니카페 브랜드 팔레트(에스프레소
> 브라운 accent), 아이콘 내비게이션이 정상 렌더링됩니다. 설계 배경 전체는
> `curried-percolating-ocean.md`(plan 문서) 참고.
>
> **2026-09-11 추가**: 5번째 화면(`/reservations`, 예약 관리)을 추가했습니다.
> `reservation-agent`와 mock-pos `/reservations` API는 이미 검증된 상태였으므로,
> 화면 2(주문 접수)와 동일한 패턴(자유 채팅 → `coordinator` → 오늘 예약 표 갱신)으로
> 화면만 새로 얹었습니다. pytest 42건 전체 통과는 확인했으나, 컨테이너 환경에서
> 실제 채팅으로 예약을 생성해 mock-pos에 반영되는 것까지 확인하는 e2e 검증은
> 아직 남아있습니다([webapp/README.md](../webapp/README.md) 빌드 상태 참고).
>
> **2026-09-11 추가 2**: 6번째 화면(`/live-demo`, 라이브 데모)을 추가했습니다.
> [21-live-demo-plan.md](21-live-demo-plan.md) P2 표의 12개 타임라인(①~⑫)을 시간
> 순서대로 한 화면에 모아, 장면마다 미리 채워진 프롬프트를 클릭 한 번으로 전송하고
> 응답을 받으면 자동으로 다음 장면으로 넘어가도록 만들었습니다(기존 화면들의
> "데모 큐" 패턴과 동일한 방식). 장면마다 관련 화면(재고/예약/주문/고객문의/
> 대시보드)으로 이동해 결과를 확인할 수 있는 링크도 함께 표시됩니다. Discord/CLI/
> mock-pos 대시보드가 실제 채널인 장면(①②⑦⑧⑩⑪⑫)은 동일한 프롬프트를
> `coordinator`에게 보내 webapp에서 대체 시연합니다 — `/api/agent/message`가
> `coordinator`/`customer-service-agent` 외 profile을 허용하지 않기 때문입니다
> (`webapp_bff/routers/agent.py`).

## 1. 이게 뭔가요 — 기존 Hermes 대시보드(`:19128`)와 차이

`http://localhost:19128`의 기존 Hermes 대시보드는 **7개 프로필을 전환해가며 자유
채팅**하는 범용 UI입니다. 이 웹앱(`http://localhost:19131`)은 그 대신 **업무별로
설계된 6개 화면**을 제공합니다 — 사장님/직원이 "어떤 프로필에게 뭐라고 말해야
하는지" 고민할 필요 없이, 화면 자체가 용도를 알려줍니다.

> ⚠️ **포트 번호 주의**: `docker-compose.yml`의 실제 호스트 포트는 `19131`입니다
> (`127.0.0.1:19131:8090`) — 2026-09-07 이전에는 `9131`이었고(그 이전에는 한때
> `9130`으로 잘못 기재된 적도 있었습니다), VPS의 다른 서비스와 4자리 포트가 겹칠
> 여지를 없애기 위해 1xxxx 대역으로 재배치했습니다. 스크립트나 북마크에 옛 포트를
> 하드코딩했다면 `19131`로 다시 확인하세요.

| 화면 | URL | 연결된 에이전트 | 쓰기 여부 |
|---|---|---|---|
| 고객 문의 상담 | `/support` | `customer-service-agent` | 없음(FAQ/불만 접수만) |
| 주문 접수 | `/orders` | `coordinator` | 있음(주문+결제) |
| 재고 파악/주문관리 | `/inventory` | 읽기는 직접, 재입고는 `coordinator` | 재입고만 |
| 예약 관리 | `/reservations` | 읽기는 직접, 예약 생성·변경·취소는 `coordinator` | 예약 생성·변경·취소 |
| 실시간 대시보드 | `/dashboard` | 없음(mock-pos 리포트만 조회) | 없음 |
| 라이브 데모(사장님의 하루) | `/live-demo` | 장면별로 `coordinator` 또는 `customer-service-agent` | 장면에 따라 다름(원 화면과 동일) |

두 대시보드는 서로 대체 관계가 아니라 **공존**합니다 — 기존 대시보드는 관리자용
범용 콘솔(`/profiles`, `/config`, `/logs` 등)로, 이 웹앱은 매장 직원이 매일 쓰는
업무 화면으로 역할이 다릅니다.

### 1.1 데모 매장 — 마니카페 연남점

이 시스템의 7개 프로필(coordinator 포함)은 전부 가상의 카페 **"마니카페 연남점"**을
전제로 설정되어 있습니다(`.hermes/profiles/*/USER.md`, `workspace/customer-service/faq.md`).

- **컨셉**: 스페셜티 원두와 시즌 디저트를 파는 동네 카페, 좌석 18석(전 좌석 콘센트·
  와이파이 완비) — 인근 직장인·재택근무자의 작업 카페로 자리잡음
- **위치**: 서울 마포구 연남동 / **영업시간**: 매일 08:00~22:00(명절 당일 휴무)
- **메뉴**: 커피 5종(아메리카노·라떼·카푸치노·에스프레소·콜드브루), 티 2종(말차라떼·
  차이라떼), 베이커리·디저트 5종(블루베리 머핀·크루아상·햄&치즈 샌드위치·딸기 스무디·
  시즌 케이크) — 총 12종, `mock-pos/scripts/seed_manicafe_demo.sh`가 실제로 등록
- **사장님**: 박서준

에이전트에게 "우리 매장", "오늘 영업시간" 등을 물으면 이 정보를 기준으로 답합니다.

## 2. 사전 준비

- **로컬(Windows/Mac) 개발**: Docker Desktop이 실행 중이어야 한다.
- **VPS 운영**: Docker Desktop이 아니라 Docker Engine + `docker compose` 플러그인이면
  충분하다(GUI 불필요). `systemctl is-active docker`로 확인 — 대부분의 VPS는 이미
  `docker.service`가 `enabled`·`active` 상태로 설치돼 있다. 자세한 VPS 운영 기준은
  [20-vps-deployment-notes.md](20-vps-deployment-notes.md) 참고.
- `mock-pos` 컨테이너가 떠 있어야 한다(주문/재고/매출 데이터 원본).
- 웹앱 자체 로그인 비밀번호 해시가 `.env`(저장소 루트, gitignore됨)에 설정돼
  있어야 한다.

## 3. 최초 배포

```bash
# 1) 웹앱 로그인 비밀번호 해시 생성
cd webapp
python -m venv .venv && . .venv/Scripts/activate   # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python scripts/hash_password.py '원하는비밀번호'
```

출력된 `scrypt$16384$8$1$...$...` 문자열을 저장소 루트 `.env`에 넣습니다.

> ⚠️ **`$` 이스케이프 주의**: docker compose는 `.env` 값 안의 `$`도 변수 치환
> 문법으로 해석합니다. scrypt 해시엔 `$`가 5개 들어있으므로, `.env`에 넣을 때는
> `$`를 전부 `$$`로 이스케이프해야 합니다 — 안 그러면 `variable is not set` 경고와
> 함께 해시가 잘려서 **로그인이 항상 실패**합니다(2026-09-04 실측으로 확인된 함정).

```bash
# .env 예시
WEBAPP_BASIC_AUTH_PASSWORD_HASH=scrypt$$16384$$8$$1$$<salt>$$<hash>
```

```bash
# 2) 빌드 및 기동 (저장소 루트에서)
docker compose build webapp
docker compose up -d webapp

# 3) 확인
curl http://localhost:19131/health
```

`{"status":"ok"}`가 나오면 정상입니다.

### 3.1 데모 데이터 채우기 (마니카페)

mock-pos는 인메모리 저장소라 비어 있는 상태로 시작합니다. 데모/시연 전에 아래
스크립트로 **마니카페 연남점** 메뉴(12종) + 재고 + 고객 6명 + 주문·결제 20여 건 +
환불 2건을 채워 넣으면 대시보드의 모든 카드(정산, 원가/마진, 인기 메뉴 TOP5, 재고
현황, 재방문 고객)가 실제 데이터로 채워집니다.

```bash
cd mock-pos/scripts
./seed_manicafe_demo.sh
```

인메모리라 컨테이너를 재시작하면 초기화됩니다 — 재시연 전엔
`docker compose restart mock-pos` 후 다시 실행하세요(멱등적이지 않음, 재시작 없이
두 번 실행하면 카탈로그 409가 납니다). "카페 한 화면(4분할 영상용) 최소 데이터"만
필요하면 대신 `mock-pos/scripts/seed_demo_video.sh`를 쓰세요(`docs/13-demo-video-script.md`
참고) — 두 스크립트는 용도가 다를 뿐 서로 대체 관계가 아닙니다.

**한 달 이상 운영된 것처럼 보이는 히스토리 데이터**가 필요하면(대시보드의 "매출
추이" 그래프가 오늘 하루가 아니라 실제 추이처럼 보이도록) 대신 이걸 쓰세요:

```bash
docker compose restart mock-pos   # 기존 데이터 초기화
cd mock-pos/scripts
python3 seed_manicafe_month.py
```

개업일(오늘로부터 약 38일 전)부터 오늘까지 매일 요일별 패턴(주말↑)과 성장 곡선
(소프트오픈 → 정상화 → 완만한 성장)을 반영해 주문/결제 약 700여 건, 주간 입고,
시즌 메뉴 출시(24일차), 환불 7건, 예약 8건을 생성합니다. 고정 시드를 쓰므로 여러
번 실행해도 규모·분포는 동일합니다. `POST /orders`, `POST /payments`에 추가된
선택적 `created_at` 필드(과거 시각 지정 가능)로 동작하며, 이 필드를 생략하면
기존과 동일하게 "지금"이 기록됩니다 — 즉 `seed_manicafe_demo.sh`/
`seed_demo_video.sh`를 포함한 기존 호출부는 변경 없이 그대로 동작합니다.

## 4. 로그인

`http://localhost:19131` 접속 → HTTP Basic Auth 팝업에 아이디(기본 `admin`)와
2단계에서 정한 비밀번호 입력. 로그인은 웹앱 전체(화면 + API)에 공통으로
적용되며, 기존 Hermes 대시보드 계정과는 **별개**입니다.

> VPS에서 이 화면을 사장님/직원 개인 기기로 열려면 `localhost`가 아니라 SSH 터널
> 또는 Traefik 서브도메인이 필요합니다 — [20-vps-deployment-notes.md](20-vps-deployment-notes.md)
> "웹앱·대시보드를 외부에 노출하기" 참고.

## 5. 화면별 사용법

### 5.1 고객 문의 상담 (`/support`)

채팅창에 손님 문의를 그대로 입력합니다. 예:

```
오늘 영업시간이 몇시부터야?
주차 가능한가요?
```

`customer-service-agent`가 `workspace/customer-service/faq.md`를 확인해
답합니다. FAQ에 없는 내용은 "담당자에게 확인해 드릴까요?"처럼 되묻습니다 —
승인 절차는 없으니 편하게 대화하면 됩니다.

### 5.2 주문 접수 (`/orders`)

두 가지 방법이 있고, 결과는 동일합니다(둘 다 `coordinator`에게 전달됩니다):

1. **품목으로 만들기**: 위쪽에서 품목별 수량을 +/-로 고르고 "주문 접수" 클릭.
   고객 이름·메모는 선택 입력입니다.
2. **채팅으로 요청**: 아래 채팅창에 자유롭게 입력. 예:
   ```
   아메리카노 2잔, 크루아상 1개 주문 들어왔어. 결제까지 처리해줘.
   ```

응답은 세 가지 중 하나로 옵니다:
- **완료 확인** — 주문 ID, 금액 등이 포함된 정상 응답.
- **확인 질문** — 예: 금액이 큰 주문이라 승인이 필요한 경우. 입력창이 계속
  열려 있으니 같은 대화창에 "네, 승인합니다"처럼 답하면 이어집니다.
- **"아직 처리 중일 수 있습니다"** — 응답이 오래 걸려 타임아웃된 경우입니다.
  **주문이 실패했다는 뜻이 아닙니다** — 아래 "최근 주문" 표를 새로고침해
  실제로 들어갔는지 확인하세요(2026-09-04 실측: 실제 주문 처리에 최대 3~4분
  걸린 사례가 있었고, 그래도 결국 정상 완료됐습니다).

### 5.3 재고 파악/주문관리 (`/inventory`)

- 위쪽 표는 현재 재고 현황입니다(저재고 품목은 빨간색으로 강조). "새로고침"
  버튼으로 즉시 갱신됩니다.
- 아래 "재입고 요청" 폼으로 품목·수량·사유(선택)를 입력해 제출하면
  `coordinator`에게 전달됩니다. 수량이 기준치를 넘으면 승인 확인 질문이 올 수
  있습니다 — 응답 상자에 그대로 표시됩니다.

### 5.4 예약 관리 (`/reservations`)

채팅으로 신규 예약·시간 변경·취소를 자유롭게 요청합니다. 예:

```
내일 오후 2시에 김민수 고객 4명 예약 잡아줘.
김민수 고객 예약을 오후 3시로 변경해줘.
김민수 고객 예약 취소해줘.
```

`coordinator`가 `reservation-agent`에게 위임해 처리하고, 아래 "오늘 예약" 표는
mock-pos `/reservations` API를 직접 조회해 갱신됩니다. 예약은 결제와 달리
금전이 오가지 않아 HITL 승인 게이트 대상이 아닙니다 — 요청하면 곧바로
반영됩니다.

> ⚠️ 2026-09-11 기준 이 화면은 pytest(단위 테스트)만 통과한 상태이고, 컨테이너
> 환경에서 실제 채팅으로 예약을 만들어 mock-pos 반영까지 확인하는 e2e 검증은
> 아직 하지 않았습니다.

### 5.5 실시간 매장 대시보드 (`/dashboard`)

읽기 전용 화면입니다. 매출 요약, 정산, 원가/마진, 매출 추이(7일), 인기 메뉴
TOP5, 재고 현황, 오늘 예약, 재방문 고객 TOP를 한 화면에서 봅니다. "새로고침"
버튼 또는 "10초마다 자동 새로고침" 체크박스로 갱신하며, 주문 접수 화면에서
방금 만든 주문이 바로 반영되는 걸 확인할 수 있습니다.

## 6. 알아둘 점

- **응답이 느릴 수 있습니다.** 특히 `coordinator`를 거치는 주문 접수·재입고
  요청은 실측 기준 25초~4분 정도 걸립니다(하위 에이전트 위임 + 검증 과정 때문).
  로딩 중에는 "생각하는 중…" 표시가 나옵니다.
- **타임아웃 ≠ 실패입니다.** 채팅 화면 밖에서 요청이 계속 처리되고 있을 수
  있으므로, 타임아웃 메시지가 나와도 곧바로 재시도하지 말고 먼저 재고/주문
  표를 새로고침해 실제로 반영됐는지 확인하세요.
- **쓰기 작업은 전부 `coordinator`를 거칩니다.** 이 웹앱의 어떤 화면도 재고
  조정이나 주문 생성을 mock-pos에 직접 요청하지 않습니다 — 가격 검증과 승인
  절차(HITL)가 항상 적용되게 하기 위한 설계입니다.

## 7. 트러블슈팅

| 증상 | 원인/조치 |
|---|---|
| 로그인이 계속 실패한다 | `.env`의 `WEBAPP_BASIC_AUTH_PASSWORD_HASH`에서 `$`를 `$$`로 이스케이프했는지 확인(3절 참고). `docker compose up -d webapp` 후 경고 로그에 `variable is not set`이 있는지 확인. |
| 화면이 401을 반환한다 | Basic Auth 자격 증명이 틀렸거나 브라우저가 캐시한 옛 자격 증명을 쓰고 있음 — 새 시크릿 탭으로 재시도. |
| 대시보드/재고 화면에 데이터가 안 보인다 | `mock-pos` 컨테이너가 떠 있는지(`docker compose ps`), `MOCK_POS_BASE_URL`/`MOCK_POS_API_KEY`가 맞는지 확인. |
| 채팅 응답이 몇 분째 안 온다 | 비정상이 아닐 수 있음 — `coordinator` 위임은 오래 걸리는 게 정상(6절 참고). `docker compose logs webapp`으로 에러 여부 확인. |
| 재입고 요청/주문이 승인 질문 없이 그냥 진행됐다 | 정상입니다 — HITL 게이트는 금액·수량이 `.hermes/profiles/*/USER.md`의 기준치를 넘을 때만 발동합니다(`docs/06-hitl-approval-design.md`). |
| 채팅 요청이 **평소보다 훨씬 빨리(1초 이내)** 응답하고 내용이 비어있거나 이상하다 | OpenAI 크레딧 소진 가능성이 높음(2026-09-11 실측: `docker exec hermes-triagent-smb hermes -p coordinator chat -Q --source tool --yolo -q "..."`로 직접 실행 시 `API call failed after 3 retries: You have no credits remaining.` 확인). 정상 응답은 25초~4분 걸리므로, 1초 이내 완료는 실패 신호. [OpenAI 조직 결제 페이지](https://platform.openai.com/settings/organization/billing/)에서 크레딧 확인 후 충전. |

## 참고

- 설계 배경/아키텍처 결정: `curried-percolating-ocean.md`(plan 문서, 로컬 파일)
- HITL 승인 게이트 상세: `docs/06-hitl-approval-design.md`
- 코드/테스트: `webapp/README.md`
