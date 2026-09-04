# 18. VS Code에서 VPS 배포 앱 연결·사용 가이드

> ✅ **실제 배포 완료 (2026-09-04)**: 이 문서는 **이미 배포가 끝난 뒤**, 다음부터 VS Code로 이
> VPS의 TriAgent_SMB에 다시 접속해서 쓸 때 보는 문서입니다. 처음부터 새로 배포하는 절차는
> [16-vps-deployment.md](16-vps-deployment.md), 일반적인 VS Code Remote-SSH 사용법은
> [17-vscode-remote-connection.md](17-vscode-remote-connection.md)를 참고하세요. 아래 정보는
> `docker compose up -d` + `hermes doctor` + Discord 로그인까지 실제로 확인된 값입니다.

## 이 배포의 현재 정보

| 항목 | 값 |
|---|---|
| VPS | Hostinger VPS 1923951 (KVM 2) — `TriAgent_ADCreator`와 같은 서버 |
| 공인 IP | `72.61.214.250` |
| SSH 사용자 | `root` |
| `~/.ssh/config` Host 별칭 | `smb-vps` (`adcreator-vps`와 동일 서버를 가리키는 별도 별칭) |
| 배포 경로 | `/opt/smb` |
| 게이트웨이 컨테이너 | `hermes-triagent-smb` (포트 `8651`) |
| 대시보드 컨테이너 | `hermes-triagent-smb-dashboard` (포트 `127.0.0.1:9128`, VPS 내부에서만 접근 가능) |
| Mock POS 컨테이너 | `hermes-triagent-smb-mock-pos` (포트 `8080`) |
| Webapp 컨테이너 | `hermes-triagent-smb-webapp` (포트 `127.0.0.1:9131` — 로컬/문서 기본값 9130이 아님, 아래 참고) |
| Discord 봇 | TriAgent SMB Coordinator#6071 (이미 연결됨, 별도 조작 불필요) |

> ⚠️ **webapp 포트가 9130이 아니라 9131입니다**: 같은 VPS에 이미 떠 있던
> `hermes-adcreator-dashboard`가 `127.0.0.1:9130`을 선점하고 있어, 이 VPS의
> `docker-compose.yml` 사본만 `9131`로 바꿨습니다(레포에 커밋된 기본값 9130은 로컬 배포용으로
> 그대로 유지). 이 VPS에 다른 프로젝트를 추가 배포할 계획이라면
> `e:\work\Hermes\PROJECT_REGISTRY.md`의 점유 포트 목록을 먼저 확인하세요.

> 로컬 Windows Docker Desktop의 `hermes` 컨테이너는 VPS 배포 후 **중지**했습니다(같은 Discord
> 봇 토큰이 두 곳에서 동시에 연결되면 충돌하기 때문 — [15-discord-integration.md](15-discord-integration.md)
> 트러블슈팅 참고). `mock-pos`/`webapp`/`dashboard`처럼 Discord와 무관한 로컬 서비스는 계속 써도
> 됩니다.

---

## 한눈에 보기 (다음에 다시 쓸 때)

- [ ] 1. VS Code에서 저장된 SSH 접속으로 연결(최초 1회만 등록 필요)
- [ ] 2. 통합 터미널에서 바로 `hermes chat` 또는 Discord로 사용
- [ ] 3. 대시보드/webapp이 필요하면 Ports 탭으로 포워딩
- [ ] 4. 코드/설정을 고쳤으면 git pull → 필요시 재기동

---

## 1. VS Code에서 SSH 연결

### 최초 1회 — Host 등록

VS Code에 **Remote - SSH** 확장이 없다면 먼저 설치합니다(Extensions에서 검색 → Install, 또는
`code --install-extension ms-vscode-remote.remote-ssh`).

`~/.ssh/config`에 이미 아래 블록이 등록돼 있습니다(이 프로젝트 배포 시 자동으로 추가됨):

```text
Host smb-vps
  HostName 72.61.214.250
  User root
  IdentityFile ~/.ssh/id_ed25519
```

### 매번 — 연결

1. VS Code 왼쪽 아래 원격 아이콘(`><`) 클릭 → **Connect to Host...** → `smb-vps` 선택.
2. 새 창이 열리면 **Open Folder** → `/opt/smb` 입력(또는 찾아보기)해서 엽니다.
3. 이 창의 **터미널(Terminal → New Terminal)은 이제 VPS 위에서 직접 실행됩니다** — 로컬 PC가
   아닙니다.

---

## 2. 바로 사용하기

### 터미널에서 coordinator와 대화

```bash
docker exec hermes-triagent-smb hermes chat --profile coordinator -q "지금 상태 확인해줘"
```

특정 전문 프로필을 직접 테스트하고 싶을 때만 `-p`(또는 `--profile`)를 명시합니다:

```bash
docker exec hermes-triagent-smb hermes chat --profile inventory-agent -q "..."
```

### Discord에서 사용

별도 절차가 없습니다 — 봇이 이미 온라인이므로 평소처럼 `#smb-ops` 채널에서
`@TriAgent SMB Coordinator`로 멘션하거나 DM을 보내면 됩니다. 서버 채널에서 보낸 메시지는
`auto_thread` 정책에 따라 **새 스레드 안에서** 응답합니다 — 채널 메인 타임라인이 아니라
**Threads** 탭을 확인하세요([15-discord-integration.md](15-discord-integration.md) 참고).

### 상태·로그 확인

```bash
docker compose ps
docker exec hermes-triagent-smb hermes doctor
docker logs -f hermes-triagent-smb          # 실시간 로그, Ctrl+C로 종료
tail -f /opt/smb/.hermes/logs/gateway.log   # 게이트웨이/Discord 연결 로그
```

**Docker 확장**(`ms-azuretools.vscode-docker`)이 설치돼 있다면 왼쪽 사이드바 고래 아이콘에서
`hermes-triagent-smb`를 우클릭 → **View Logs** 또는 **Attach Shell**로 같은 작업을 GUI로 할 수
있습니다.

---

## 3. 대시보드 / Webapp 접속

두 서비스 모두 VPS의 `127.0.0.1`에만 열려 있어 인터넷에서 직접 접근할 수 없습니다(의도된 설계).

**방법 A — VS Code Ports 탭 (권장)**

1. Remote-SSH로 연결된 창에서 하단 **Ports** 탭 → **Forward a Port**.
2. 대시보드는 `9128`, webapp 운영 콘솔은 `9131`을 각각 추가.
3. 로컬 브라우저에서 `http://127.0.0.1:9128`(대시보드) 또는 `http://127.0.0.1:9131`(webapp)
   접속. 로그인 계정은 VPS 배포 시 새로 발급한 값을 사용하세요(로컬 개발용 기본값과 다릅니다 —
   [16-vps-deployment.md](16-vps-deployment.md) 참고).

**방법 B — 수동 SSH 터널**

```powershell
ssh -L 9128:127.0.0.1:9128 -L 9131:127.0.0.1:9131 smb-vps
```

---

## 4. 코드·설정을 고친 뒤 반영하기

로컬 PC에서 평소처럼 편집 → `git commit` → `git push` 한 다음, VPS 쪽에 반영합니다.
Remote-SSH 터미널에서:

```bash
cd /opt/smb
git pull
```

- **SOUL.md / USER.md / MEMORY.md / skills 파일 수정** → 바인드 마운트라 `git pull`만으로 즉시
  반영됩니다. 재기동 불필요.
- **`docker-compose.yml` / `Dockerfile` 수정, 또는 새 프로필 폴더 추가** → 재기동이 필요합니다.
  단, `git pull`이 `docker-compose.yml`을 덮어쓰면 이 VPS 전용 webapp 포트 수정(9130→9131)이
  git의 원본 값(9130)으로 되돌아갈 수 있으니, `git pull` 후에는 항상 포트 줄을 다시 확인하세요:
  ```bash
  grep -n '9130\|9131' docker-compose.yml
  # 9130으로 되돌아갔다면: sed -i 's/127.0.0.1:9130:8090/127.0.0.1:9131:8090/' docker-compose.yml
  docker compose up -d --build
  ```
- **`.hermes/.env` / `profiles/*/.env` / 대시보드·webapp 비밀번호**는 git에 없으므로 `git pull`로
  따라오지 않습니다. 로컬에서 값을 바꿨다면 VPS 쪽 해당 파일도 직접 고치거나 `scp`로 다시
  옮겨야 합니다.

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| Remote-SSH 연결이 안 됨 | 네트워크 문제이거나 VPS가 꺼져있음 | 일반 터미널에서 `ssh smb-vps`로 먼저 원인 확인 |
| `docker: permission denied` | root가 아닌 다른 계정으로 접속함 | `~/.ssh/config`의 `User root` 확인, 또는 명령 앞에 `sudo` |
| 대시보드/webapp Ports 탭에 안 뜸 | 자동 감지가 항상 되진 않음 | **Forward a Port**로 직접 추가(대시보드 9128, webapp 9131) |
| Discord 봇이 응답 없음 | 컨테이너가 죽었거나, 로컬 PC에서 같은 봇을 동시에 띄웠음 | `docker compose ps`로 상태 확인. 로컬에서 `docker compose up`을 했다면 반드시 `docker compose stop hermes`로 내리세요 — 같은 토큰이 두 곳에서 동시에 연결되면 충돌합니다 |
| `#smb-ops`에서 메시지를 보냈는데 응답이 안 보임 | `auto_thread`로 새 스레드에 응답이 감 | 채널의 **Threads** 탭에서 새로 생긴 스레드를 확인하세요 |
| `git pull` 후 webapp이 안 뜸(포트 충돌) | `docker-compose.yml`이 9130(레포 기본값)으로 되돌아감 | 위 "4. 코드·설정을 고친 뒤 반영하기"의 포트 재확인 명령 실행 |
| `kanban dispatcher: cannot load config ... Permission denied` 경고 | bind mount 권한 이슈, coordinator는 애초에 kanban을 쓰지 않음 | 무시해도 무방 — [03-hermes-agent-integration.md](03-hermes-agent-integration.md)에서 coordinator는 kanban 미사용으로 설계됨 |

## 참고

- 처음부터 새로 배포하는 절차: [16-vps-deployment.md](16-vps-deployment.md)
- Discord 설정: [15-discord-integration.md](15-discord-integration.md)
- 이 VPS를 포함한 전체 프로젝트 현황 기록: `e:\work\Hermes\PROJECT_REGISTRY.md`
