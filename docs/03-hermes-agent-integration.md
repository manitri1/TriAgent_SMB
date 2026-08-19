# 03. Hermes Agent CLI 연동 — 프로필 생성과 툴셋 매핑

## 프로필 생성/배포 방법

세 가지 방법이 있습니다 (자세한 실행 절차는 [README.md](../README.md)와
[09-users-guide.md](09-users-guide.md) 참고):

**A. `HERMES_HOME`을 이 저장소로 직접 지정** (개발 중 권장)

```bash
export HERMES_HOME="$(pwd)/.hermes"
hermes -p coordinator chat
```

**B. 실제 `~/.hermes`로 복사** (기존 `~/.hermes` 설정을 건드리지 않고 배포하고 싶을 때)

```bash
for name in coordinator order-payment-agent inventory-agent reservation-agent customer-service-agent sales-analytics-agent marketing-crm-agent; do
  mkdir -p "$HERMES_HOME/profiles/$name/skills"
  cp ".hermes/profiles/$name/config.yaml" "$HERMES_HOME/profiles/$name/config.yaml"
  cp ".hermes/profiles/$name/SOUL.md" "$HERMES_HOME/profiles/$name/SOUL.md"
  cp ".hermes/profiles/$name/USER.md" "$HERMES_HOME/profiles/$name/USER.md"
  cp ".hermes/profiles/$name/MEMORY.md" "$HERMES_HOME/profiles/$name/MEMORY.md"
  cp -r ".hermes/profiles/$name/skills/." "$HERMES_HOME/profiles/$name/skills/"
done
cp ".hermes/config.yaml" "$HERMES_HOME/config.yaml"
```

**C. Docker Compose** (Windows에서 별도 로컬 `hermes` 설치 없이 운영, 권장 —
[08-docker-deployment.md](08-docker-deployment.md) 참고)

각 방법 모두 실제 Hermes CLI(`hermes profile create <name>`으로 프로필 생성 후 생성된
디렉터리를 이 저장소의 파일로 덮어쓰는 방식도 가능)와 호환됩니다.

## 프로필별 필요 툴셋

각 프로필에는 역할에 필요한 툴셋만 켭니다(`hermes tools enable <toolset> --profile <role>`).
"이미 있음" 항목은 [01-review-of-idea.md](01-review-of-idea.md)에서 확인한 Hermes 내장
기능입니다.

| 프로필 | 필요 툴셋 | 이유 |
|---|---|---|
| `coordinator` | `terminal`, `clarify`, `messaging`, `file`(주로 읽기, 진행 카드는 예외적으로 쓰기) | 하위 프로필 위임(terminal), 진행 트래킹(`workspace/kanban/` 파일 카드), HITL 승인 대화(clarify/messaging), Active Verification(file). **`delegation`/`delegate_task`는 켜지 않습니다** — [02장](02-architecture.md) 참고. **`kanban`도 켜지 않습니다** — 2026-08-19 실측 결과 coordinator에는 로드되지 않는 워커 전용 기능입니다 |
| `order-payment-agent` | `code_execution`, `file` | Mock POS `/orders`, `/payments` REST 호출(샌드박스 파이썬), 주문 요약을 workspace에 기록 |
| `inventory-agent` | `code_execution`, `file` | Mock POS `/inventory` 조회·발주 요청 티켓 기록 |
| `reservation-agent` | `code_execution`, `file`, `messaging` | Mock POS `/reservations` 호출, 노쇼 방지 리마인더를 Discord로 직접 발송(HITL 대상 아님 — 저위험 알림) |
| `customer-service-agent` | `web`, `search`, `file` | FAQ 지식베이스(`workspace/customer-service/faq.md`) 조회·갱신, 필요 시 웹 검색으로 보완. **`web`/`search`는 별도 검색 API 키(EXA/TAVILY/FIRECRAWL 등)가 없으면 비활성 상태입니다** — 아래 참고 |
| `sales-analytics-agent` | `code_execution`, `file` | Mock POS `/reports/sales`, `/reports/settlement` 조회·집계 |
| `marketing-crm-agent` | `web`, `search`, `code_execution`, `file` | 트렌드/경쟁사 리서치, 홍보 문구 초안 작성. **`messaging` 미부여** — 발송은 승인 후 `coordinator` 경유. `web`/`search`는 위와 동일한 제약 |

> ⚠️ **2026-08-19 실측**: `hermes doctor`로 확인한 결과 `web`/`search` 툴셋은 "이미 내장
> 제공"이 아니라 `EXA_API_KEY`/`PARALLEL_API_KEY`/`TAVILY_API_KEY`/`FIRECRAWL_API_KEY` 중
> 하나가 `.env`에 있어야 실제로 동작합니다. 이 키가 없으면 `customer-service-agent`/
> `marketing-crm-agent`는 웹 검색 없이 내부 지식(FAQ 파일 등)만으로 동작합니다 —
> [01-review-of-idea.md](01-review-of-idea.md)의 "이미 있음" 판단을 이 부분만 정정합니다.

## 게이트웨이 설정

```bash
hermes gateway setup     # Discord 등 채널 연결
hermes gateway run       # 게이트웨이 데몬 실행 (docker-compose.yml의 hermes 서비스가 이미 실행)
```

`coordinator`의 HITL 승인 알림과 `reservation-agent`의 리마인더는 이 게이트웨이를 통해
발송됩니다 — [06-hitl-approval-design.md](06-hitl-approval-design.md) 참고.

## Mock POS 연동 방식

`mock-pos/`(FastAPI, [상세는 05장](05-skills-and-tools.md) 참고)는 Hermes가 모르는 외부
도메인이므로 `code_execution` 샌드박스 파이썬에서 `requests`로 REST 호출합니다.

> ✅ **2026-08-19 실측 완료**: `code_execution` 샌드박스가 같은 Docker 네트워크의
> `mock-pos` 컨테이너(`http://mock-pos:8080`)로 아웃바운드 HTTP 호출을 실제로 허용함을
> 확인했습니다 — `order-payment-agent`에게 실제 챗으로 주문을 요청해 Mock POS에 진짜
> 주문/결제가 생성되고 재고가 정확히 차감되는 것까지 독립적으로(mock-pos API 직접 조회로)
> 검증했습니다. `TriAgent_MICE`에는 이 케이스에 대한 선례가 없어 이번이 최초 검증입니다.
>
> ⚠️ **다만 접속 정보 주입 방식은 계획과 다릅니다**: `code_execution` 샌드박스는 프로필의
> `.env`(`MOCK_POS_BASE_URL`, `MOCK_POS_API_KEY`)를 자동으로 물려받지 않습니다. 처음
> 시도에서는 에이전트가 "세션에 환경변수가 없다"며 사용자에게 값을 되물었습니다. 그래서
> 레퍼런스 스크립트(`skills/*/scripts/*.py`)의 기본값을 실제 배포 값
> (`http://mock-pos:8080` / `dev-key` / `store_demo`)으로 하드코딩해뒀습니다 — Mock POS
> API Key는 실서비스 비밀값이 아니라 개발용 고정 키라 하드코딩해도 안전합니다.

## idea.md 기억 구조 → 실제 Hermes 경로 매핑

| `refs/idea.md`의 개념 | 실제 Hermes Agent 경로 |
|---|---|
| Soul (페르소나) | `profiles/<role>/SOUL.md` |
| Memory (단기+장기) | `profiles/<role>/MEMORY.md`(Hermes 네이티브, 에이전트가 자동 관리) + `file` 툴셋으로 `workspace/`에 축적 |
| Skill (도메인 절차) | `profiles/<role>/skills/<category>/<skill-name>/SKILL.md` |
| Workspace | `workspace/{orders,inventory,reservations,customer-service,sales,marketing,reports}/` — Hermes 표준 경로는 아니며, 프로젝트 관례로 SOUL.md/SKILL.md에서 상대경로로 지시 |
| Config | `config.yaml`(top-level 모델 기본값) + `profiles/<role>/config.yaml`(프로필별 오버라이드) |

top-level `.env`는 프로필에 상속되지 않으므로, 각 `profiles/<role>/.env`에도 반드시
`OPENAI_API_KEY`, `MOCK_POS_BASE_URL`, `MOCK_POS_API_KEY`를 복사해야 합니다(README.md 배포
스크립트에 이미 반영).
