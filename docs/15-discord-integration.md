# 15. Discord 연동 — 앱 생성부터 봇 응답 확인까지

> ✅ **자매 프로젝트 실측 반영 (2026-09-04)**: 이 문서는 같은 `e:/work/Hermes/` 아래
> [`TriAgent_ADCreator`](../../TriAgent_ADCreator)가 실제로 Discord 봇을 연결해 운영 중인
> 절차(`TriAgent_ADCreator/docs/08-discord-deployment.md`)를 그대로 참조해 맞췄습니다.
> 다만 **TriAgent_SMB 자체의 `DISCORD_BOT_TOKEN`은 아직 비어 있어 이 저장소에서
> end-to-end로 실행 검증하지는 않았습니다** — 아래 절차 자체는 검증된 방식이지만, 이
> 프로젝트에서 실제로 봇을 연결하면 이 상태 표시와 [07-roadmap.md](07-roadmap.md)/
> [10-usecase-tests.md](10-usecase-tests.md)를 갱신하세요.

이 프로젝트는 Discord 연동을 위해 **커스텀 봇 코드를 작성하지 않습니다.** 과거
`hermes-core/app/discord_bot.py`(`discord.py` 기반 커스텀 봇)가 있었으나, 실제 Hermes
Agent CLI가 게이트웨이/Discord 플랫폼 어댑터(`plugins/platforms/discord/`)를 내장
제공한다는 것을 확인하고 전량 폐기했습니다([01-review-of-idea.md](01-review-of-idea.md)
참고). 봇은 아웃바운드로만 Discord에 연결하므로 이 컴퓨터/VPS의 방화벽에 포트를 열
필요도 없습니다.

## 한눈에 보기

- [ ] 1단계 — Discord Developer Portal에서 앱·봇 만들고 Intent 켜기, 토큰 발급
- [ ] 2단계 — 서버 준비 및 봇 초대
- [ ] 3단계 — 내 Discord 사용자 ID 확인
- [ ] 4단계 — `.hermes/.env` 한 파일에 토큰·허용 사용자 채우기
- [ ] 5단계 — 컨테이너 재기동
- [ ] 6단계 — `hermes doctor`로 확인 후 실제로 말 걸어보기
- [ ] (선택) 홈 채널 지정

> ⚠️ **이 문서에는 실제 값을 적지 마세요.** 이 문서는 git에 커밋됩니다. 진짜 토큰·ID는
> 항상 **4단계에서 `.hermes/.env`에만** 넣으세요.

---

## 1단계 — Discord Developer Portal에서 봇 만들기

1. [Discord Developer Portal](https://discord.com/developers/applications)에 로그인 →
   **New Application** → 이름 입력(예: "TriAgent SMB") → **Create**.
2. 왼쪽 메뉴 **Bot** 클릭. **Public Bot**은 켜진 상태로 둡니다(끄면 아래 2단계의 간편
   초대 링크를 못 씁니다).
3. **⚠️ 가장 중요한 단계** — 같은 Bot 페이지에서 **Privileged Gateway Intents**를 찾아
   다음 두 개를 반드시 **켜세요(ON)**:
   - **Message Content Intent** — 꺼져 있으면 봇이 온라인으로는 보이는데 **메시지
     내용을 아예 읽지 못합니다**("봇이 응답을 안 해요" 문제의 90% 원인).
   - **Server Members Intent** — 허용 사용자 확인에 필요합니다.
   - 켠 뒤 **Save Changes**를 누르는 걸 잊지 마세요.
4. 같은 페이지 **Token** 항목에서 **Reset Token** → 토큰 복사(**한 번만 표시**됩니다).
   절대 다른 사람과 공유하거나 Git에 커밋하지 마세요.

## 2단계 — 서버 준비 및 봇 초대

이미 봇을 초대할 서버가 있다면 채널 준비로 건너뛰세요. 없다면 Discord 앱 왼쪽 서버
목록 맨 아래 **`+`** → **Create My Own**으로 새로 만듭니다.

승인 알림·노쇼 리마인더를 받을 **운영 채널 하나**(예: `#smb-ops`)를 만들어두면
편합니다 — 아래 "홈 채널 지정"에서 이 채널을 지정합니다.

**봇 초대**:

1. Developer Portal 왼쪽 메뉴 **Installation** → **Guild Install** 활성화 →
   **Install Link**를 "Discord Provided Link"로.
2. **Default Install Settings**에서:
   - **Scopes**: `bot`, `applications.commands`
   - **Permissions**: `View Channels`, `Send Messages`, `Embed Links`, `Attach Files`,
     `Read Message History`(+ 여유 있게 `Send Messages in Threads`, `Add Reactions`)
3. 뜨는 초대 URL을 브라우저에서 열고 → 서버 선택 → **Continue** → **Authorize**.

수동으로 초대 URL을 만들고 싶다면(1단계에서 얻은 Application ID 필요):

```text
https://discord.com/oauth2/authorize?client_id=<APPLICATION_ID>&scope=bot+applications.commands&permissions=274878286912
```

## 3단계 — 내 Discord 사용자 ID 확인

1. Discord 앱 → **설정(User Settings)** → **고급(Advanced)** → **개발자 모드
   (Developer Mode)** ON.
2. 내 이름(아무 메시지나 프로필)을 우클릭 → **ID 복사(Copy User ID)**.
3. 역할(Role) 단위로 허용하고 싶다면 역할을 우클릭 → **Copy Role ID**로 동일하게 얻습니다.

## 4단계 — `.hermes/.env` 채우기

`coordinator`가 컨테이너의 라이브(최상위) 프로필이므로, Discord 설정은 **최상위
`.hermes/.env` 한 곳**이면 충분합니다 — `profiles/*/.env`에 중복으로 넣지 않아도 됩니다.

```bash
cp .hermes/.env.example .hermes/.env   # 아직 안 했다면
```

`.hermes/.env`에서 아래 두 줄을 채웁니다(자리는 이미 마련돼 있습니다 —
`.hermes/.env.example` 참고):

```bash
DISCORD_BOT_TOKEN=<1단계에서 발급받은 봇 토큰>
DISCORD_ALLOWED_USERS=<3단계에서 확인한 내 사용자 ID>
```

- 여러 명을 허용하려면 쉼표로 구분: `DISCORD_ALLOWED_USERS=111...,222...`
- 역할 단위로 허용하려면 `DISCORD_ALLOWED_ROLES=<역할 ID>`를 대신 또는 함께 씁니다.
- **`DISCORD_ALLOWED_USERS`/`DISCORD_ALLOWED_ROLES`/`DISCORD_ALLOW_ALL_USERS` 중
  최소 하나는 반드시 채워야 합니다.** 비워두면 Hermes가 안전을 위해 모든 사용자를
  기본 거부합니다(버그가 아니라 0.18+ 의도된 정책) — 토큰·Intent가 전부 맞아도 이
  값이 없으면 봇이 아무에게도 응답하지 않습니다.

## 5단계 — 재기동

```bash
docker compose restart hermes
```

`docker-compose.yml`의 `hermes` 서비스 `command`가 이미 `["gateway", "run"]`이므로,
`.hermes/.env`에 채운 값은 컨테이너가 재시작될 때 자동으로 반영됩니다 — 별도의
`hermes gateway setup` 같은 대화형 명령을 실행할 필요는 없습니다.

## 6단계 — 확인

```bash
docker compose exec hermes hermes doctor
```

출력에서 `discord`가 더 이상 "missing DISCORD_BOT_TOKEN"으로 뜨지 않는지 확인한 뒤,
Discord 앱에서 봇에게 **DM**을 보내거나 초대한 서버 채널에서 **`@봇이름`**으로
멘션하며 말을 걸어보세요. 별도로 프로필을 지정할 필요 없이 이 봇은 바로
**coordinator**로 응답합니다(coordinator가 컨테이너의 라이브 프로필이기 때문 —
[03-hermes-agent-integration.md](03-hermes-agent-integration.md) 참고).

## (선택) 홈 채널 지정

coordinator가 **먼저 말을 거는** 능동적 메시지(HITL 승인 알림, 일일 요약 등)를 받을
채널을 정해두면 좋습니다.

**방법 A — 슬래시 커맨드 (가장 쉬움)**: 홈으로 쓸 채널(예: `#smb-ops`)에서
`/sethome`을 입력·전송하면 끝입니다. `.env`를 건드릴 필요도, 재기동도 필요 없습니다.

**방법 B — `.env`에 직접 지정**: 채널을 우클릭 → **Copy Channel ID**(개발자 모드
필요) → `.hermes/.env`에 추가:

```bash
DISCORD_HOME_CHANNEL=<채널 ID>
DISCORD_HOME_CHANNEL_NAME="#smb-ops"
```

방법 A와 달리 이 방법은 `docker compose restart hermes`가 필요합니다. 채널 ID는
토큰과 달리 그 자체로는 접근 권한을 주지 않는 식별자라 이 문서에 메모해도 괜찮지만,
시크릿은 항상 `.env`에만 넣는 습관은 유지하세요.

## 이 게이트웨이를 사용하는 곳

- `coordinator`의 HITL 승인 알림(프로모션/캠페인 집행, 대량 발주, 환불/주문 취소) —
  [06-hitl-approval-design.md](06-hitl-approval-design.md). `clarify` 호출이 Discord에서
  버튼(선택지 1/2/3/Other)으로 자동 렌더링되므로 "사람이 명시적으로 예/아니오를 누르는"
  UX가 코드 없이 만족됩니다.
- `reservation-agent`의 노쇼 방지 리마인더(승인 불필요, 저위험 알림으로 직접 발송) —
  [04-agents-and-souls.md](04-agents-and-souls.md), [05-skills-and-tools.md](05-skills-and-tools.md)
- (설계됐으나 미검증) `coordinator`의 일일 요약 메시지 — [05-skills-and-tools.md](05-skills-and-tools.md)

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 봇은 온라인인데 메시지에 반응이 없다 | Message Content Intent가 꺼져 있음(가장 흔함) | Developer Portal → Bot → Privileged Gateway Intents → Message Content Intent ON → Save → `docker compose restart hermes` |
| "User not allowed" 또는 아예 무반응 | 내 사용자 ID가 `DISCORD_ALLOWED_USERS`에 없음(또는 아예 미설정) | `.hermes/.env`에 내 ID 추가 후 재기동 |
| 특정 채널에서만 안 읽음 | 봇 역할에 해당 채널 View Channel 권한이 없음 | 채널 설정 → 권한 → 봇 역할에 View Channel, Read Message History 추가 |
| 403 Forbidden | 초대 시 권한이 부족했음 | 2단계 초대 URL로 다시 초대하거나 서버 설정에서 봇 역할 권한 조정 |
| 봇이 아예 오프라인 | 게이트웨이 컨테이너가 안 떠 있거나 토큰이 틀림 | `docker compose ps`로 `hermes-triagent-smb` 상태 확인, `.hermes/.env`의 `DISCORD_BOT_TOKEN` 재확인 |
| 로컬과 VPS에서 동시에 응답이 꼬임/끊김 | 같은 봇 토큰이 두 곳(로컬 Docker Desktop + [16-vps-deployment.md](16-vps-deployment.md)의 VPS)에서 동시에 연결됨 | 한쪽만 띄우기 — 개발 중에는 로컬을 내리고 VPS만(또는 반대) 운영 |

## 환경변수 참고 (심화)

기본 설정은 4단계 두 줄이면 충분합니다. 아래는 필요할 때만 참고하세요(모두
`.hermes/.env.example`에 자리가 마련돼 있습니다).

- `DISCORD_ALLOW_ALL_USERS` — 모든 사용자 허용(신뢰된 소규모 서버에서만). 기본 `false`.
- `DISCORD_REQUIRE_MENTION` — 서버 채널에서 멘션 필요 여부. 기본 `true`.
- `DISCORD_AUTO_THREAD` — 멘션마다 새 스레드를 자동 생성할지. 여러 건을 동시에
  다룰 때(예: 여러 주문/예약 문의가 겹칠 때) 대화가 섞이지 않게 해줍니다.
- `DISCORD_ALLOW_MENTION_EVERYONE` / `_ROLES` — 기본 `false`로 둡니다. LLM이 실수로
  `@everyone` 문자열을 출력해도 실제 알림이 가지 않도록 하는 안전장치입니다.
- `DISCORD_MAX_ATTACHMENT_BYTES` — 첨부파일 크기 상한(기본 32MiB).

이 값들을 `.env` 대신 `.hermes/config.yaml`의 `discord:` 섹션(`require_mention`,
`auto_thread` 등)으로 고정해둘 수도 있습니다 — 형식은
[03-hermes-agent-integration.md](03-hermes-agent-integration.md) 상단의 `config.yaml`
설명 참고. 전체 옵션 목록은 Hermes 공식 문서
(`website/docs/user-guide/messaging/discord.md`, 자매 프로젝트 vendor 경로 예:
`HermesContentsMarketingAgent/vendor/hermes-agent/website/docs/user-guide/messaging/discord.md`)를
참고하세요.
