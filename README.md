# TriAgent_SMB

카페·식당·미용실·편의점 등 소상공인의 주문/결제, 재고관리, 예약, 고객응대, 매출분석,
마케팅/CRM을 자동화하는, [Nous Research Hermes Agent](https://github.com/NousResearch/hermes-agent)
CLI 기반 7-역할(coordinator / order-payment-agent / inventory-agent / reservation-agent /
customer-service-agent / sales-analytics-agent / marketing-crm-agent) AX(AI Transformation)
자동화 시스템입니다.

설계 배경과 아키텍처는 [docs/](docs/00-index.md)를 먼저 읽어보세요 — 특히
[docs/01-review-of-idea.md](docs/01-review-of-idea.md)(원본 아이디어 `refs/idea.md` 대비
실제 Hermes Agent CLI가 이미 제공하는 기능과 커스텀 구현이 필요한 부분 구분)를 확인하세요.

> **현재 상태 (2026-08-19)**: 설계 문서(`docs/00~10`)와 실행 가능한 Profile 스캐폴드
> (`.hermes/profiles/<role>/{config.yaml, SOUL.md, USER.md, MEMORY.md, skills/}`)를
> 작성했고, **실제로 `docker compose build/up`을 실행해 배포한 뒤 실제 `gpt-5-mini` 챗으로
> 핵심 경로를 검증했습니다**: `hermes doctor`에서 7개 프로필 모두 정상 인식, coordinator가
> `terminal`로 order-payment-agent를 위임(설계대로 `delegate_task` 미사용), 그 결과
> `code_execution`이 실제로 `mock-pos` 컨테이너를 호출해 주문/결제/재고차감이 발생하는
> 것까지 mock-pos API로 독립 재확인했습니다. 이 과정에서 실측으로만 알 수 있었던 이슈
> 2건(코드 실행 샌드박스가 `.env`를 상속하지 않음, `terminal` 위임이 ~120초 타임아웃될
> 수 있음 — 하위 프로세스는 계속 실행되어 완료됨)을 발견해 문서와 스크립트에 반영했습니다.
> 자세한 실측 기록은 [docs/07-roadmap.md](docs/07-roadmap.md), [docs/10-usecase-tests.md](docs/10-usecase-tests.md)
> 참고. 나머지 4개 프로필과 HITL 3개 게이트는 아직 미검증입니다.
>
> 이 저장소는 이전에 `hermes-core/`라는 커스텀 Python 구현(자체 OpenAI 함수콜 루프,
> `discord.py` 봇)으로 "Hermes 에이전트"를 흉내 냈으나, 형제 프로젝트
> [`TriAgent_MICE`](../TriAgent_MICE)를 검토한 결과 실제 Hermes Agent CLI가 이 대부분을
> 이미 내장 제공한다는 것을 확인해 전면 재구축했습니다 — 자세한 내용은
> [docs/01-review-of-idea.md](docs/01-review-of-idea.md) 참고.

## 디렉터리 구조

```
refs/idea.md          원본 설계 아이디어 (보존, 수정하지 않음)
docs/                 설계 문서 세트 (00~10, 09=운영가이드, 10=유스케이스 테스트)
docker-compose.yml    Windows Docker Compose 배포 (docs/08-docker-deployment.md 참고)
.hermes/              idea.md의 Soul/Skill/Memory 구조를 실제 Hermes Agent CLI 컨벤션으로 옮긴 실행 가능한 Profile 소스
├── config.yaml       메인 Hermes Agent 설정 (기본 모델 등)
├── .env.example       OPENAI_API_KEY/DISCORD_BOT_TOKEN/MOCK_POS_* 템플릿 (.env는 커밋 대상 아님)
├── profiles/         각 <role>/{config.yaml, SOUL.md, USER.md, MEMORY.md, skills/*}
└── workspace/        orders/ inventory/ reservations/ customer-service/ sales/ marketing/ reports/ inputs/
mock-pos/             Mock POS REST 시뮬레이터 (FastAPI) — code_execution Skill이 호출
```

## 로컬 배포 방법

`.hermes/`는 `refs/idea.md`의 Soul/Skill/Memory 개념을 실제 Hermes CLI 경로로 옮긴
것이므로, 두 가지 방법으로 실행할 수 있습니다 (자세한 내용은
[docs/03-hermes-agent-integration.md](docs/03-hermes-agent-integration.md)):

**방법 A — `HERMES_HOME`을 이 저장소로 직접 지정** (가장 간단, 개발 중 권장):

```bash
export HERMES_HOME="$(pwd)/.hermes"
hermes -p coordinator chat
```

**방법 B — Docker Compose** (Windows에서 별도 로컬 `hermes` 설치 없이 운영, 권장):

```bash
cp .hermes/.env.example .hermes/.env   # OPENAI_API_KEY, MOCK_POS_API_KEY 채우기
# 7개 프로필 각각에도 같은 키 복사 — 필수 (top-level .env는 프로필에 상속되지 않음)
for name in coordinator order-payment-agent inventory-agent reservation-agent customer-service-agent sales-analytics-agent marketing-crm-agent; do
  grep -E "^(OPENAI_API_KEY|MOCK_POS_BASE_URL|MOCK_POS_API_KEY)=" .hermes/.env > ".hermes/profiles/$name/.env"
done

docker compose build
docker compose up -d
docker compose exec -it hermes hermes -p coordinator chat
```

`e:/work/Hermes/` 아래 다른 형제 Hermes 프로젝트와 포트/컨테이너명이 겹치지 않도록 조사해
구성했습니다(게이트웨이 `8651`, 대시보드 `127.0.0.1:9128`, 컨테이너명
`hermes-triagent-smb*` — 기존 `HermesSMBStaff`의 `hermes-smb*`/8643/9120과는 별개입니다).
조사 근거와 운영 명령어 전체는 [docs/08-docker-deployment.md](docs/08-docker-deployment.md),
챗 사용법은 [docs/09-users-guide.md](docs/09-users-guide.md) 참고.

기본 모델은 OpenAI `gpt-5-mini`(`provider: openai-api`, `OPENAI_API_KEY` 환경변수 필요)입니다.

사용 시작은 대화 진입점인 `coordinator` 프로필로 합니다:

```bash
hermes -p coordinator chat
> "아메리카노 2잔, 크루아상 1개 주문 들어왔어. 결제까지 처리해줘."
```

## Mock POS 단독 실행/테스트

Hermes/Docker 없이 POS 시뮬레이터만 검증하려면:

```bash
cd mock-pos
pip install -r requirements-dev.txt
pytest
uvicorn mock_pos.main:app --reload --port 8080
```

## 사용 전 체크리스트

- `.hermes/profiles/*/USER.md`의 "(예시)" 표시가 남은 항목을 실제 매장/사장님 정보로 채웠는지 확인
- `hermes tools enable ...`로 각 프로필에 필요한 툴셋을 켰는지 확인
  ([docs/03-hermes-agent-integration.md](docs/03-hermes-agent-integration.md)의 매핑표 참고)
- `hermes gateway setup`으로 Discord 등 승인 채널을 실제로 연결했는지 확인
  ([docs/06-hitl-approval-design.md](docs/06-hitl-approval-design.md) 참고)

## 알려진 제약 ([docs/07-roadmap.md](docs/07-roadmap.md), [docs/10-usecase-tests.md](docs/10-usecase-tests.md) 참고)

- **`code_execution` 샌드박스는 프로필의 `.env`를 자동으로 물려받지 않습니다** —
  실측으로 발견한 이슈입니다. 4개 POS 연동 스킬(`order_and_payment`/`stock_and_reorder`/
  `reservation_management`/`sales_reporting`)의 레퍼런스 스크립트는 이 때문에 접속
  정보(`http://mock-pos:8080` / `dev-key` / `store_demo`)를 하드코딩된 기본값으로
  바꿔뒀습니다(Mock POS 키는 개발용 고정 키라 안전).
- **`terminal` 위임 호출이 약 120초 후 타임아웃될 수 있습니다**(`exit 124`) — 하위
  프로필이 code_execution까지 수행하는 복잡한 작업일 때 발생했습니다. 타임아웃 후에도
  하위 프로세스는 백그라운드에서 계속 실행되어 완료되므로(고아 프로세스로 남지 않음),
  coordinator는 타임아웃 응답만으로 실패를 단정하지 않고 Active Verification으로
  재확인하도록 설계·검증했습니다.
- **`kanban` 네이티브 툴은 coordinator에서 동작하지 않습니다**(dispatcher가 생성한 워커
  전용). coordinator는 `workspace/kanban/*.md` 파일 카드로 진행 상황을 관리합니다 —
  이것이 정식 방법입니다.
- **`web`/`search` 툴셋은 별도 검색 API 키**(`EXA_API_KEY`/`TAVILY_API_KEY`/
  `FIRECRAWL_API_KEY` 등)가 없으면 비활성입니다. 현재 이 키 없이 배포되어 있어
  `customer-service-agent`/`marketing-crm-agent`는 웹 검색 없이 내부 지식만으로
  동작합니다.
- 실 POS 벤더(토스플레이스/카카오페이) 연동은 아직 없습니다 — 현재는 Mock POS로 기능
  검증까지만 수행합니다.
- HITL 승인 게이트는 총 3개입니다(프로모션/캠페인 집행·재고 대량 발주·결제 환불/주문
  취소) — [docs/06-hitl-approval-design.md](docs/06-hitl-approval-design.md) 참고.
  이 3개 게이트가 실제 대화에서 걸리는지는 아직 미검증입니다.
- `coordinator`가 다른 프로필에 작업을 위임하는 실제 메커니즘은 `delegate_task`가 아니라
  `terminal` 동기 호출입니다 — **2026-08-19 실제로 구동해 검증 완료**(위 현재 상태 참고).
- 7개 프로필 중 3개(coordinator, order-payment-agent, 그리고 이 둘 사이의 위임)만
  실제 챗으로 검증했습니다. 나머지 4개 프로필과 HITL 3개 게이트는
  [docs/10-usecase-tests.md](docs/10-usecase-tests.md)에 미검증(⬜)으로 남아 있습니다.
