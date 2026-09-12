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
| [08-docker-deployment.md](08-docker-deployment.md) | Windows Docker Compose 배포(원 설계) + 실제 VPS 배포 현황(2026-09-05 실측, 이 VPS의 실제 포트/컨테이너 점유) — 형제 프로젝트 포트/볼륨 조사 결과 |
| [09-users-guide.md](09-users-guide.md) | 실행/운영 가이드 (챗 중심) — 프로필별 대화 진입점, 흔한 함정, 트러블슈팅 |
| [10-usecase-tests.md](10-usecase-tests.md) | Usecase 테스트 목록 — 2026-08-19 실제 배포로 Part A~C(프로필 단독/오케스트레이션/HITL 게이트) 전부 검증 완료 |
| [11-external-integrations-guideline.md](11-external-integrations-guideline.md) | Shopify/Stripe 테스트 자동화 가이드라인(별도 작업, API 키 확보 전 준비 문서) — TriAgent_SMB 본체와는 독립적 |
| [12-web-gui-demo.md](12-web-gui-demo.md) | 웹 GUI 시연 방안 — 채팅은 기존 Hermes 대시보드(`/chat`) 재사용, 실적 그래픽 분석은 mock-pos에 신규 페이지 추가 필요(아직 미구현, 절차만 정리됨) |
| [13-demo-video-script.md](13-demo-video-script.md) | 4분할 동시 재생 10초 데모 영상 촬영·조립 스크립트 — 촬영/합성은 로컬(docker+ffmpeg) 환경 필요, `mock-pos/scripts/seed_demo_video.sh` + `scripts/build_demo_video.sh` 사용 |
| [14-webapp-users-guide.md](14-webapp-users-guide.md) | `webapp/`(마니카페 운영 콘솔) 사용 가이드 — 고객 문의/주문 접수/재고 관리/예약 관리/대시보드 5화면, 기존 Hermes 대시보드와의 차이, 배포·트러블슈팅 |
| [15-discord-integration.md](15-discord-integration.md) | Discord 앱 생성부터 `hermes gateway` 연결까지 — 봇 토큰 발급, `.env` 설정, 검증 방법 (미검증 설계 가이드) |
| [16-vps-deployment.md](16-vps-deployment.md) | 원격 VPS(Linux)에 Docker Compose로 배포 — 08장(로컬 Windows)과 별도, SSH/방화벽/재부팅 자동기동 (미검증 설계 가이드) |
| [17-vscode-remote-connection.md](17-vscode-remote-connection.md) | VS Code Remote-SSH로 VPS 컨테이너 개발환경에 접속 — 포트 포워딩 포함 (미검증 설계 가이드) |
| [18-vps-connect-and-use.md](18-vps-connect-and-use.md) | 실제 VPS 배포(Hostinger, 2026-09-04) 접속·사용 가이드 — 현재 배포 정보, 포트, 트러블슈팅 (실측 완료) |
| [19-hermes-desktop-vps-guide.md](19-hermes-desktop-vps-guide.md) | Hermes Desktop(Electron) 앱을 VPS에 배포된 이 저장소 인스턴스에 원격 연동하는 방법 — SSH 터널/리버스 프록시+TLS/이 VPS의 공유 Traefik, 인증(basic_auth/OAuth) 설정, 트러블슈팅 |
| [20-vps-deployment-notes.md](20-vps-deployment-notes.md) | 08~19장의 Windows 로컬 개발 전제와 실제 Linux VPS 배포의 차이 정리 — 이 VPS의 실체(호스팅사/방화벽/디스크), 공유 Traefik 라벨 활용법, 백업 대상, 재부팅 복구 |
| [21-live-demo-plan.md](21-live-demo-plan.md) | "마니카페 사장님의 하루"(`course/`) 타임라인을 실제 VPS 배포 위에서 라이브 시연하기 위한 실행 계획 — 블로커(Discord 명령 차단 미확인, 미실행 프로필 3개, 빈 mock-pos 시드), 재현 가능한 시연 데이터, 타임라인별 채널 매핑, Gmail/Sheets/Notion 실제 연동 (실행 전, 계획 단계) |
| [22-vps-dashboard-access.md](22-vps-dashboard-access.md) | 이 VPS의 Hermes 프로젝트 3개(SMB/MICE/ADCreator) 대시보드 접속 한눈에 보기 — 2026-09-07 포트 1xxxx 이전 + 자격증명 `.env` 이전 + 공유 Traefik HTTPS 상시 접속. SMB는 적용·검증 완료, MICE/ADCreator는 안내만 하고 적용은 대기 중 |
| [24-review-reply-design.md](24-review-reply-design.md) | 리뷰 자동 응답 기능 설계(신규, 2026-09-11) — `customer-service-agent`에 `review-reply-draft` 스킬 추가, 리뷰는 수동 입력·답글은 초안만 생성(게시는 사람), 실제 챗 검증은 아직 남음 |
| [25-token-optimization.md](25-token-optimization.md) | 토큰 사용량 점검·최적화(2026-09-11) — 설계 문서 대비 실제 활성 툴셋/번들 스킬이 과도했던 것을 발견해 7개 프로필 전체 정리, `hermes prompt-size` 실측 기준 신규 세션 고정 프롬프트 32.8% 절감(API 호출 없이 오프라인으로 진행) |

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
