# 01. `refs/idea.md` 재검토 — 실제 Hermes Agent CLI 기능 대조

`refs/idea.md`는 Docker 컨테이너, Discord 봇, OpenAI 함수콜 루프를 "우리가 처음부터 다
만들어야 하는 것"처럼 다루고 있습니다. 실제로는 Nous Research가 공개한 실존 오픈소스 CLI
에이전트(`hermes-agent`)이며, 상당한 기능을 이미 내장하고 있습니다. 이번 장은 idea.md의 각
항목을 "이미 있음 / 커스텀 필요"로 재분류합니다. (이 대조 방법론은 형제 프로젝트
`TriAgent_MICE`의 `docs/01-review-of-idea.md`에서 실제로 검증된 내용을 SMB 도메인에 맞게
재적용한 것입니다.)

## 대조표

| idea.md 항목 | idea.md의 가정 | 실제 Hermes Agent CLI | 결론 |
|---|---|---|---|
| Discord 인터페이스 | `discord.py`로 봇을 직접 구현해야 함 | `hermes gateway setup`으로 Telegram/Discord/Slack/WhatsApp/Email 등 20+ 플랫폼 기본 지원 | **이미 있음** — 설정만 하면 됨, `hermes-core/app/discord_bot.py`는 전량 불필요 |
| LLM 함수콜 루프 (Orchestrator/Agent) | OpenAI `chat.completions` tool-calling을 직접 구현 | Hermes Agent 런타임이 프로필별 System Prompt(SOUL.md) + 툴 실행을 자체 관리 | **이미 있음** — `hermes-core/app/agents/base.py`의 tool-calling 루프는 전량 불필요 |
| 세션/대화 컨텍스트 (Memory 단기) | 자체 `session_store.py` | Hermes 프로필별 세션이 CLI가 자체 관리 | **이미 있음** |
| 장기 지식(FAQ/정책/고객이력) | 자체 `knowledge_store.py` | 프로필별 `MEMORY.md`(에이전트가 자동 관리) + `file` 툴셋으로 `workspace/`에 파일로 축적 | **이미 있음(구조는 있음)** — 실제 내용은 각 매장 운영 데이터로 채워야 함 |
| Web Search / 경쟁사 리서치 (marketing-crm-agent) | 별도 MCP 서버 구축 필요로 가정 | 내장 `web`/`search` 툴셋 | **이미 있음** |
| 다중 에이전트 오케스트레이션 (coordinator) | 우리가 별도 오케스트레이터를 만들어야 함 | 내장 `terminal`(프로필 동기 호출), `kanban`(다중 프로필 작업큐) | **이미 있음** — 단, `delegate_task`는 대상 프로필의 SOUL/USER/MEMORY/skills를 로드하지 않는 함정임이 `TriAgent_Planner`/`TriAgent_MICE`에서 실측 확인됨 → `terminal` 동기 호출로 대체, [02장](02-architecture.md) 참고 |
| 승인 지점 (HITL) | 별도 승인 절차를 새로 설계해야 함 | 게이트웨이의 `/approve`/`/deny`는 **쉘 명령 승인**용(`approvals.mode`) — 프로모션 집행·환불처럼 도메인 특화된 승인과는 다름 | **부분적** — 메커니즘은 있지만 용도가 다름. `messaging`/`clarify` 툴셋으로 도메인 승인 대화를 직접 설계해야 함 ([06장](06-hitl-approval-design.md)) |
| 기억 구조 (Profile/SOUL/MEMORY) | idea.md 자체 설계 | Hermes Agent의 Profile 시스템(`~/.hermes/profiles/<name>/`)과 정확히 대응 | **설계 그대로 유효** — 파일 배치 방식만 실제 CLI 컨벤션에 맞춤 |
| **POS 연동**(주문/결제/재고/예약/매출) | Python으로 직접 구현 예정이었음 | 내장 기능 없음(POS는 Hermes가 모르는 외부 도메인) | **커스텀 필요 — 이미 구현됨.** `mock-pos/`(FastAPI, Square API 참조 모델)가 이미 존재하므로 새로 만들 필요는 없고, 각 Profile의 Skill이 `code_execution`으로 이 REST API를 호출하도록 재배선만 하면 됨 |
| 실 POS 벤더(토스플레이스/카카오페이) 연동 | Python으로 직접 구현 예정이었음 | 내장 기능 없음 | **커스텀 필요** — 계약·인증 정보 확보 후 진행([07장](07-roadmap.md)) |

## `hermes-core/`와의 관계

이전 버전(`hermes-core/` + `discord.py` + OpenAI 함수콜 루프)은 이 표의 왼쪽 절반
("이미 있음" 항목들)을 처음부터 다시 구현한 것이었습니다. 실제 Hermes Agent CLI가 이를
이미 제공한다는 것을 확인했으므로 `hermes-core/`는 **전량 폐기**했습니다. 유일하게 계속
필요했던 것은 오른쪽 절반("커스텀 필요") 중 POS 연동이었고, 이는 `mock-pos/`로 이미
구현되어 있어 그대로 재사용합니다 — 다만 호출 주체가 `hermes-core/app/skills/pos_client.py`
(커스텀 Python)에서 각 Profile의 `code_execution` Skill로 바뀝니다([05장](05-skills-and-tools.md)).

## 핵심 결론

1. **idea.md의 "Soul + Skill + Memory 분리" 철학은 그대로 유효합니다.** 좋은 설계이며 수정할
   필요가 없습니다.
2. **idea.md가 "직접 구현해야 한다"고 가정했던 인프라(Discord 봇, 함수콜 루프, 웹 리서치,
   오케스트레이션)의 대부분은 Hermes Agent가 이미 제공**합니다. 이번 재구축은 이 내장 기능을
   "어떻게 켜고 어떻게 SOUL.md/SKILL.md에서 지시할지"를 정의하는 데 집중합니다
   ([03장](03-hermes-agent-integration.md)).
3. **여전히 커스텀 구현이 필요한 것**: POS 연동(완료, `mock-pos/`), 실 POS 벤더 연동(미착수),
   도메인 단위 HITL 승인 대화 설계(이미 있는 `messaging`/`clarify` 툴셋으로 지금
   설계·문서화, [06장](06-hitl-approval-design.md)).
4. **오케스트레이션은 `terminal` 동기 호출 방식으로 처음부터 확정합니다.** `TriAgent_Planner`/
   `TriAgent_MICE`가 `delegate_task`를 먼저 써봤다가 대상 프로필을 전혀 로드하지 않는다는
   것을 뒤늦게 발견하고 교체한 시행착오를 이 저장소는 반복하지 않습니다 — 다만 이 결정 자체는
   아직 이 저장소에서 실제로 구동해 재검증하지는 않았습니다([10장](10-usecase-tests.md) 참고).
