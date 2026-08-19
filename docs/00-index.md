# TriAgent_SMB 설계 문서

`refs/idea.md`에서 제안한 소상공인(카페/식당/미용실/편의점) AX 자동화 아이디어를, **실제
[Nous Research Hermes Agent](https://github.com/NousResearch/hermes-agent) CLI** 위에서
동작하는 7-Profile(coordinator + 6개 실행 에이전트) 세트로 구체화한 설계 문서 세트입니다.

## 문서 구성

| 문서 | 내용 |
|---|---|
| [01-review-of-idea.md](01-review-of-idea.md) | 원본 아이디어 검토 — idea.md가 가정한 커스텀 연동 중 Hermes Agent가 이미 내장 제공하는 것과 실제로 새로 만들어야 하는 것 구분 |
| [02-architecture.md](02-architecture.md) | 7개 프로필의 관계도와 데이터 흐름, 오케스트레이션 방식 |
| [03-hermes-agent-integration.md](03-hermes-agent-integration.md) | 실제 Hermes Agent CLI로 프로필을 만들고 배포하는 방법, 프로필별 필요 툴셋 |
| [04-agents-and-souls.md](04-agents-and-souls.md) | 7개 에이전트의 SOUL(SOUL.md) 전체 초안 |
| [05-skills-and-tools.md](05-skills-and-tools.md) | 에이전트별 Skill(SKILL.md) 정의, Mock POS 연동 방식 |
| [06-hitl-approval-design.md](06-hitl-approval-design.md) | coordinator가 관리하는 3개 Human-in-the-Loop 승인 게이트 상세 설계 |
| [07-roadmap.md](07-roadmap.md) | 이번 단계 이후 남은 작업 (실 POS 벤더 연동, 오케스트레이션·HITL 실측) |
| [08-docker-deployment.md](08-docker-deployment.md) | Windows Docker Compose 배포 — 형제 프로젝트 포트/볼륨 조사 결과 |
| [09-users-guide.md](09-users-guide.md) | 실행/운영 가이드 (챗 중심) — 프로필별 대화 진입점, 흔한 함정, 트러블슈팅 |
| [10-usecase-tests.md](10-usecase-tests.md) | Usecase 테스트 목록 — 현재는 전부 미검증(⬜) 상태 |

## 한 줄 요약

- 원본 아이디어의 **역할별 페르소나(Profile) + 절차적 지식(Skill) 분리 철학**은 그대로 채택합니다.
- `hermes_agent`는 가상의 패키지가 아니라 Nous Research가 실제로 공개한 CLI 에이전트이며,
  인스턴스(Profile)당 페르소나 1개만 가질 수 있습니다. 그래서 idea.md의 여러 전문 역할을
  **7개의 격리된 Hermes Agent Profile**(coordinator + 6개 실행 에이전트)로 만듭니다.
- idea.md가 "Discord 봇을 직접 구현해야 한다"고 가정했던 인터페이스, "OpenAI 함수콜 루프를
  직접 짜야 한다"고 가정했던 오케스트레이션은 **Hermes Agent가 이미 내장 게이트웨이/툴셋으로
  제공**합니다([01장](01-review-of-idea.md) 참고). 반대로 POS 연동은 Hermes가 모르는 외부
  API라 여전히 커스텀이 필요한데, 이 부분은 이미 `mock-pos/`로 구현되어 있어 그대로 재사용하고
  호출 방식만 `code_execution` Skill로 바꿉니다.
- 다중 프로필 간 작업 조정(coordinator의 역할)은 외부 파이썬 오케스트레이터를 새로 짜는
  대신, Hermes Agent 내장 `terminal`(프로필 동기 호출)과 `kanban`(진행 상황 트래커) 기능으로
  구현합니다([02장](02-architecture.md)). 이 설계는 형제 프로젝트 `TriAgent_MICE`가 겪은
  `delegate_task` 관련 시행착오(대상 프로필을 전혀 로드하지 않는 버그)를 처음부터 피해
  `terminal` 동기 호출 방식으로 설계했습니다.
- **설계 문서 + 실행 가능한 Profile 스캐폴드**(`config.yaml`/`SOUL.md`/`USER.md`/`MEMORY.md`/
  `skills/*/SKILL.md`)까지 작성했습니다. Windows Docker Compose 배포([08장](08-docker-deployment.md))
  파일도 준비했지만, **아직 실제로 빌드·구동·챗 스모크 테스트는 하지 않았습니다** — 남은
  작업은 [07-roadmap.md](07-roadmap.md)와 [10-usecase-tests.md](10-usecase-tests.md)에
  미검증 항목으로 정리되어 있습니다.

## 이전 버전과의 차이

이 문서 세트 이전에는 `hermes-core/`라는 커스텀 Python 구현(자체 OpenAI 함수콜 루프,
`discord.py` 봇, 인메모리 세션/지식 스토어)으로 "Hermes 에이전트"를 흉내 냈습니다. 형제
프로젝트 `TriAgent_MICE`를 검토한 결과 실제 Hermes Agent CLI가 이 대부분을 이미 내장
제공한다는 것을 확인해([01장](01-review-of-idea.md)), `hermes-core/`는 폐기하고 실제 CLI
Profile 구조로 전면 재구축했습니다. `mock-pos/`(Mock POS REST 시뮬레이터)는 코드 변경 없이
그대로 유지하며, 호출 주체만 `hermes-core/`의 커스텀 클라이언트에서 각 Profile의 `code_execution`
Skill로 바뀝니다.
