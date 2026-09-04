# 17. VS Code Remote-SSH로 VPS 컨테이너 개발환경에 접속

> ✅ **2026-09-04 실제 배포로 검증 완료**: 이 절차대로 실제 VPS에 Remote-SSH로 접속해
> 포트 포워딩까지 확인했습니다. 지금 이 프로젝트가 배포된 VPS의 실제 접속 정보(IP·경로·
> 포트)는 [18-vps-connect-and-use.md](18-vps-connect-and-use.md)를 바로 참고하세요 — 이
> 문서는 처음부터 새 VPS에 접속을 설정하는 범용 절차입니다.

## 1. 확장 설치 & SSH 등록

1. VS Code에 **Remote - SSH** 확장(Microsoft 제공)을 설치합니다.
2. [16장](16-vps-deployment.md)에서 만든 SSH 키를 재사용해 `~/.ssh/config`(Windows는
   `C:\Users\<사용자>\.ssh\config`)에 Host를 등록합니다:
   ```
   Host triagent-smb-vps
       HostName <VPS_IP>
       User deploy
       IdentityFile ~/.ssh/id_ed25519
   ```

## 2. 원격 접속 & 저장소 열기

1. 명령 팔레트(`Ctrl+Shift+P`) → **Remote-SSH: Connect to Host** → `triagent-smb-vps` 선택
2. 새로 열리는 원격 창에서 **Open Folder** → `~/TriAgent_SMB`(16장에서 clone한 경로)
3. 원격 창의 통합 터미널은 VPS 위에서 직접 실행되므로, [16장](16-vps-deployment.md)의
   `docker compose` 명령(빌드/기동/로그/`hermes doctor`, [08장](08-docker-deployment.md)의
   챗 명령 등)을 그대로 입력할 수 있습니다 — 로컬/원격 구분 없이 동일한 명령입니다.

## 3. 포트 포워딩 — 대시보드/webapp 브라우저 접속

`docker-compose.yml` 설계상 대시보드(`127.0.0.1:9128`)와 webapp(`127.0.0.1:9130`)은
VPS 자체에서도 localhost로만 노출됩니다(외부 직접 접근 불가 — [16장](16-vps-deployment.md)
3절 참고). VS Code Remote-SSH로 접속하면 이 포트들을 로컬 브라우저로 그대로 가져올 수
있습니다.

**방법 A — VS Code `PORTS` 패널 (권장)**

1. 원격 창 하단의 **PORTS** 탭 → **Forward a Port**
2. `9128`(대시보드), `9130`(webapp) 각각 추가
3. 로컬 브라우저에서 `http://localhost:9128`, `http://localhost:9130`으로 그대로 접속
   (VS Code가 자동으로 SSH 터널을 유지)

**방법 B — 수동 SSH 터널** (VS Code 없이도 가능):

```bash
ssh -L 9128:127.0.0.1:9128 -L 9130:127.0.0.1:9130 deploy@<VPS_IP>
```

## 4. (참고) Dev Containers로 컨테이너 내부까지 들어가기

`hermes`/`webapp` 컨테이너 내부 파일을 직접 보고 싶다면 **Dev Containers** 확장으로
실행 중인 컨테이너에 attach할 수 있습니다(명령 팔레트 → **Dev Containers: Attach to
Running Container**). 다만 `HERMES_HOME`(`.hermes/`)은 bind mount이므로 **원격 창에서
저장소 폴더를 여는 것만으로 이미 같은 파일을 편집할 수 있습니다** — 대부분의 경우
컨테이너에 별도로 attach할 필요는 없습니다(불필요한 절차 지양).

## 5. 트러블슈팅

- **Windows에서 SSH 키 권한 오류**: OpenSSH는 개인키 파일의 권한이 너무 열려 있으면
  거부합니다. PowerShell에서 `icacls`로 현재 사용자만 읽기 권한을 갖도록 제한하세요.
- **접속이 안 될 때**: VPS 방화벽이 22번 포트를 막고 있는지 (`sudo ufw status`),
  `~/.ssh/config`의 `IdentityFile` 경로가 맞는지, VPS 쪽 `~/.ssh/authorized_keys`에
  공개키가 등록됐는지 확인합니다.
- **PORTS 패널에 포워딩한 포트가 응답 없음**: 컨테이너가 실제로 떠 있는지
  (`docker compose ps`), [08-docker-deployment.md](08-docker-deployment.md)에서 다룬
  "Up인데 내부는 죽어 있는" 대시보드 크래시 루프 함정인지 로그로 확인하세요.
