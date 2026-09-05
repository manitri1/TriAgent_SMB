# 16. 원격 VPS 배포 — Docker Compose

> ✅ **2026-09-04 실제 배포로 검증 완료**: 이 절차대로 Hostinger VPS(`72.61.214.250`,
> `/opt/smb`)에 실제 배포해 4개 컨테이너 기동과 Discord 연결까지 확인했습니다. 그 배포의
> 실제 IP·경로·포트·트러블슈팅은 [18-vps-connect-and-use.md](18-vps-connect-and-use.md)에
> 정리돼 있습니다 — 아래는 처음부터 새 VPS에 배포할 때 따라가는 범용 절차(Ubuntu
> 22.04/24.04 기준)입니다.

## 0. 08장과의 차이

| | [08장](08-docker-deployment.md) | 이 문서(16장) |
|---|---|---|
| 대상 | 로컬 Windows + Docker Desktop | 원격 Linux VPS |
| 접속 | 로컬 터미널 | SSH |
| 네트워크 노출 | 방화벽 개념 없음(로컬호스트) | 방화벽(`ufw`) 필수 |
| `docker-compose.yml`/포트/컨테이너명 | 동일 | **동일** — 파일을 바꾸지 않고 그대로 사용 |

이미지·포트·컨테이너명·bind mount 전략은 08장에서 정한 값을 그대로 재사용합니다
(게이트웨이 `8651`→`8642`, 대시보드 `127.0.0.1:9128`→`9119`, mock-pos `8080`, webapp
`127.0.0.1:9130`→`8090`, 컨테이너명 `hermes-triagent-smb*`).

## 1. VPS 준비

- 최소 권장 스펙: 2 vCPU / 4GB RAM 이상(hermes + dashboard + mock-pos + webapp 4개
  컨테이너 동시 구동 기준)
- OS: Ubuntu 22.04 LTS 이상
- SSH 키 접속을 먼저 설정하고, 배포 작업은 `root`가 아닌 sudo 권한을 가진 일반 사용자로
  수행합니다:
  ```bash
  adduser deploy
  usermod -aG sudo deploy
  # 로컬에서 공개키를 등록
  ssh-copy-id deploy@<VPS_IP>
  ```
- 이후 절차는 `ssh deploy@<VPS_IP>`로 접속한 상태를 기준으로 합니다.

## 2. Docker 설치

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER   # 재로그인 후 docker 명령에 sudo 불필요
sudo systemctl enable --now docker
docker compose version   # Compose plugin 포함 확인
```

## 3. 방화벽 (`ufw`)

이 프로젝트의 설계상 대시보드(9128)와 webapp(9130)은 원래도 `127.0.0.1` 전용으로만
노출됩니다 — 즉 **VPS 자체 방화벽 이전에 이미 외부 접근이 불가능**합니다. 이 두 서비스는
[17-vscode-remote-connection.md](17-vscode-remote-connection.md)의 SSH 포트 포워딩으로
접근합니다.

```bash
sudo ufw allow OpenSSH
sudo ufw allow 8651/tcp   # 게이트웨이(Discord 등)를 실제로 외부에 노출해야 할 때만
sudo ufw enable
sudo ufw status
```

> 게이트웨이 자체는 Discord 같은 아웃바운드 연결 방식이면 8651을 굳이 외부에 열 필요가
> 없는 경우가 많습니다. 웹훅 등 인바운드 채널을 쓰지 않는다면 8651도 열지 말고
> SSH(22)만 허용하는 것이 가장 안전합니다.

## 4. 저장소 배포

```bash
git clone <this-repo-url> TriAgent_SMB
cd TriAgent_SMB

cp .hermes/.env.example .hermes/.env
# OPENAI_API_KEY, DISCORD_BOT_TOKEN(15장 참고), MOCK_POS_API_KEY 등을 채운다

for name in coordinator order-payment-agent inventory-agent reservation-agent customer-service-agent sales-analytics-agent marketing-crm-agent; do
  grep -E "^(OPENAI_API_KEY|MOCK_POS_BASE_URL|MOCK_POS_API_KEY)=" .hermes/.env > ".hermes/profiles/$name/.env"
done

# webapp 기본 인증 비밀번호 해시 생성 (root .env, docker-compose.yml 참고)
python3 webapp/scripts/hash_password.py
cp .env.example .env   # WEBAPP_BASIC_AUTH_PASSWORD_HASH 등을 채운다 ($ 는 $$ 로 이스케이프)

docker compose build
docker compose up -d
docker compose ps
docker compose exec hermes hermes doctor
```

Discord 게이트웨이 연결은 [15-discord-integration.md](15-discord-integration.md)를 그대로
따르면 됩니다 — `.hermes/.env`에 `DISCORD_BOT_TOKEN`/`DISCORD_ALLOWED_USERS`를 채운 뒤
`docker compose restart hermes`.

> ⚠️ **같은 봇 토큰을 로컬(08장)과 VPS(이 문서)에 동시에 띄우지 마세요** — 한쪽만
> 운영합니다. 로컬 개발 중에는 로컬 컨테이너를 내려두고 VPS 쪽만 살아있게 하는 것을
> 권장합니다([15장](15-discord-integration.md) 트러블슈팅 참고).

## 5. 재부팅 시 자동 기동

`docker-compose.yml`의 모든 서비스에 이미 `restart: unless-stopped`가 설정되어 있으므로,
**별도 systemd 유닛을 새로 만들 필요는 없습니다.** VPS가 재부팅되면 Docker daemon이
컨테이너를 자동으로 다시 올립니다. 확인할 것은 Docker daemon 자체가 부팅 시 켜지는지
뿐입니다:

```bash
sudo systemctl is-enabled docker   # enabled 여야 함 (2번 단계의 enable --now 로 이미 설정됨)
```

## 6. (선택) 외부 도메인 + TLS

게이트웨이(8651)를 도메인으로 외부에 노출해야 하는 경우(예: 웹훅 기반 채널)에는 앞단에
리버스 프록시를 두고 TLS를 종료시킵니다. 예를 들어 [Caddy](https://caddyserver.com/)를
쓰면 `Caddyfile` 하나로 Let's Encrypt 인증서 발급까지 자동 처리됩니다:

```
gateway.example.com {
    reverse_proxy localhost:8651
}
```

이 구성(별도 `docker-compose.yml` 서비스 추가 또는 호스트에 Caddy 직접 설치)은 이번
문서의 범위 밖입니다 — 실제로 인바운드 웹훅 채널이 필요해지면 별도 문서로 확장하세요.

## 7. 운영 명령어

08장과 동일합니다(원격이므로 SSH 세션 안에서 실행):

```bash
docker compose logs -f hermes
docker compose exec -it hermes hermes chat --profile coordinator
docker compose restart dashboard
docker compose down
```

대시보드/webapp의 "Up인데 실제로는 죽어 있는" 함정과 `dashboard.basic_auth` 설정은
[08-docker-deployment.md](08-docker-deployment.md)의 내용이 원격 VPS에도 동일하게
적용되니 함께 참고하세요.
