# 19. Hermes Desktop 앱을 VPS 배포 인스턴스에 연동하기

이 문서는 로컬 PC에 설치한 **Hermes Desktop(Electron) 앱**을, VPS에 Docker Compose로
배포된 이 저장소의 Hermes Agent 인스턴스(`hermes-triagent-smb*` 컨테이너들)에 원격으로
연동하는 방법을 정리합니다. `docker exec`로 컨테이너 내부의 실제 CLI(`hermes --help`)와
소스(`hermes_cli/main.py`, `config_defaults.py`)를 직접 확인해 검증한 내용입니다.

> 함께 보기: [08-docker-deployment.md](08-docker-deployment.md)(포트/컨테이너 구성),
> [09-users-guide.md](09-users-guide.md)(챗 사용법), [12-web-gui-demo.md](12-web-gui-demo.md)
> (브라우저로 대시보드 접속), [20-vps-deployment-notes.md](20-vps-deployment-notes.md)
> (이 VPS 전반의 운영 기준 — 공유 Traefik, 백업, 재부팅 복구 등)

## 1. 먼저 알아야 할 것 — 연동 대상은 "게이트웨이"가 아니라 "대시보드"

이 저장소의 `docker-compose.yml`은 서로 다른 역할의 컨테이너 2개를 띄웁니다. Hermes
Desktop 앱이 실제로 붙는 곳은 **대시보드 컨테이너**입니다.

| 컨테이너 | 실행 명령 | 역할 | 호스트 노출 |
|---|---|---|---|
| `hermes-triagent-smb` | `gateway run` | Discord/Telegram 등 **메시징 봇** 게이트웨이 | `0.0.0.0:18651 → 8642` |
| `hermes-triagent-smb-dashboard` | `dashboard --host 0.0.0.0 --no-open` | 브라우저 대시보드 **+ Desktop 앱이 붙는 JSON-RPC/WebSocket 백엔드** | `127.0.0.1:19128 → 9119` |

컨테이너 내부 코드를 보면 `dashboard`와 `serve`(Desktop 전용 headless 백엔드) 명령은
**같은 함수(`cmd_dashboard`)를 공유**하고, `serve`는 브라우저 UI를 안 띄우는 옵션만 켠
버전입니다. 즉 지금 떠 있는 대시보드 컨테이너를 그대로 Desktop 앱의 연동 대상으로 쓸 수
있으며, 별도로 `hermes serve`를 새로 띄울 필요가 없습니다.

문제는 대시보드가 **`127.0.0.1:19128`로만 노출**되어 있다는 점입니다(`docs/08` 참고 —
`0.0.0.0`으로 열면 인증 provider 없이는 아예 바인딩을 거부해서 크래시 루프가 났던
이력이 있어 로컬 전용으로 좁혀뒀습니다). VPS 로컬에서만 접근 가능하므로, 내 PC의 Hermes
Desktop 앱에서 붙으려면 아래 2번 또는 3번 방법으로 "터널" 또는 "공개 노출 + 인증"을
선택해야 합니다.

## 2. 사전 준비 확인

```bash
# VPS에서
cd /opt/smb   # 이 저장소 경로
docker compose ps
```

`hermes-triagent-smb-dashboard`가 `Up`인지, 그리고 실제로 살아있는지 확인합니다
(`Up`이어도 내부 크래시 루프일 수 있다는 게 08장에서 실측된 함정입니다):

```bash
curl -sI http://127.0.0.1:19128/ | head -1
# 302(로그인 리다이렉트) 또는 200이면 정상. Empty reply면 로그를 확인하세요:
docker compose logs dashboard --tail=50
```

`dashboard.basic_auth`(사용자명 + scrypt 해시 + 서명 시크릿)가 이미 설정돼 있어야
합니다 — 이 저장소는 공개 저장소라 2026-09-07부터 그 값을 `.hermes/config.yaml`이
아니라 `.hermes/.env`의 `HERMES_DASHBOARD_BASIC_AUTH_USERNAME`/`_PASSWORD_HASH`/
`_SECRET`로 관리합니다. Desktop 앱 로그인 시 그 파일에 적힌 사용자명/비밀번호를
그대로 사용합니다.

## 3. 방법 A — SSH 터널 (1인 운영/개발 중 권장, 가장 간단)

VPS에 SSH로 접속할 수 있다면 별도 리버스 프록시나 TLS 인증서 없이 가장 안전하게 붙을 수
있습니다. 대시보드가 이미 루프백 전용이라 별다른 설정 변경도 필요 없습니다.

내 PC(로컬)에서:

```bash
# -N: 셸을 열지 않고 포워딩만, -L 로컬포트:대상호스트:대상포트
ssh -N -L 19128:127.0.0.1:19128 <ssh사용자>@<VPS_IP_또는_도메인>
```

터널이 연결된 상태를 유지한 채, Hermes Desktop 앱에서 원격 서버 주소로
`http://127.0.0.1:19128`을 등록하고 `.hermes/config.yaml`의 `dashboard.basic_auth`
사용자명/비밀번호로 로그인합니다(연동 화면 세부 절차는 6번 참고).

이 방법은 VPS의 방화벽/보안그룹을 전혀 열 필요가 없다는 것이 장점입니다. 반대로 터널이
끊기면 앱 연결도 끊어지므로, 상시 원격 접속(모바일 등)이 필요하면 방법 B를 쓰세요.

## 4. 방법 B — 리버스 프록시 + TLS로 공개 노출 (상시/다중 클라이언트용)

여러 기기(다른 PC, 노트북 등)에서 터널 없이 상시 접속하려면 도메인 + HTTPS로 앞단을
막아야 합니다. Hermes Agent는 `0.0.0.0` 바인딩을 감지하면 인증 provider가 없는 한
바인딩 자체를 거부하도록 하드코딩돼 있으므로(위 크래시 루프 사례), **인증을 켜지 않은
채로는 애초에 공개 노출이 불가능**합니다 — 즉 이 문서 2번의 `basic_auth` 설정이 전제
조건입니다.

1. `docker-compose.yml`에서 대시보드 포트 바인딩을 루프백 전용에서 공개로 바꿉니다
   (직접 여는 대신 아래 3번의 리버스 프록시만 공개하는 편이 더 안전합니다 — 대시보드
   컨테이너 포트 자체는 계속 `127.0.0.1`로 두고, nginx/Caddy만 공인 IP에 바인딩):

   ```yaml
   dashboard:
     ports:
       - "127.0.0.1:19128:9119"   # 그대로 유지 — 외부는 프록시를 통해서만 접근
   ```

2. VPS에 nginx 또는 Caddy로 TLS 종료 + 리버스 프록시를 구성합니다. WebSocket
   업그레이드(`/api/ws`, `/api/pty`)를 반드시 통과시켜야 합니다(nginx 예시):

   ```nginx
   server {
       listen 443 ssl;
       server_name hermes.example.com;
       # ssl_certificate ...; ssl_certificate_key ...; (Let's Encrypt 등)

       location / {
           proxy_pass http://127.0.0.1:19128;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_set_header X-Forwarded-Host $host;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

3. 프록시가 `X-Forwarded-Host`/`X-Forwarded-Proto`를 위처럼 전달하지 못하는 환경이라면,
   대시보드 컨테이너 환경변수로 `HERMES_DASHBOARD_PUBLIC_URL=https://hermes.example.com`을
   직접 지정해야 합니다(OAuth 리다이렉트 URI와 Origin 검증에 사용됨) — `docker-compose.yml`
   의 `dashboard` 서비스 `environment:`에 추가하세요.

4. Hermes Desktop 앱에서는 `https://hermes.example.com`을 원격 서버 주소로 등록하고
   `basic_auth` 자격증명(또는 아래 8번의 OAuth)으로 로그인합니다.

방법 B를 쓴다면 반드시 7번을 먼저 확인하세요 — 인터넷에 노출되는 서비스의 로그인
자격증명이 공개 저장소에 커밋돼 있으면 위험합니다.

## 5. 방법 C — Traefik 라벨로 자동 HTTPS (이 VPS 권장)

이 VPS(Hostinger)에는 hPanel이 기본 제공하는 **공유 Traefik**이 이미 컨테이너로
떠서 `80`/`443` 포트를 점유하고 있고, `*.srv1923951.hstgr.cloud` 서브도메인은 DNS
설정 없이 이 VPS로 자동 라우팅됩니다. nginx를 직접 설치·관리해야 하는 방법 B 대신,
Docker 라벨 몇 줄만 추가하면 동일한 결과(도메인 + 자동 TLS)를 얻을 수 있습니다 —
**이 VPS에서는 방법 B보다 이 방법을 먼저 검토하세요.**

```yaml
# docker-compose.yml의 dashboard 서비스에 추가 (ports:는 그대로 둬도 무방)
  dashboard:
    labels:
      traefik.enable: "true"
      traefik.http.routers.smb-dashboard.entrypoints: websecure
      traefik.http.routers.smb-dashboard.rule: "Host(`smb-dashboard.srv1923951.hstgr.cloud`)"
      traefik.http.routers.smb-dashboard.tls.certresolver: letsencrypt
      traefik.http.services.smb-dashboard.loadbalancer.server.port: "9119"
```

```bash
docker compose up -d dashboard          # 라벨만 바뀌었으므로 재생성만 필요
curl -I https://smb-dashboard.srv1923951.hstgr.cloud/   # 302면 성공
```

Hermes Desktop 앱에는 이 `https://smb-dashboard.srv1923951.hstgr.cloud` 주소를 원격
서버로 등록하면 됩니다. 원리, 다른 컨테이너와의 라우터 이름 충돌 방지, 웹앱에 동일하게
적용하는 방법은 [20-vps-deployment-notes.md](20-vps-deployment-notes.md) 2번에 자세히
정리했습니다. Traefik은 TLS 종단만 담당하므로 `dashboard.basic_auth`는 방법 B와
동일하게 계속 켜져 있어야 합니다.

## 6. Hermes Desktop 앱에서 원격 서버 추가하기

2026-09-08 실측(버전 0.21.0 기준) — Desktop 앱은 "여러 서버를 목록에 저장해두고
이름으로 전환"하는 구조가 **아닙니다**. 대신 **Settings → Gateway** 화면 하나에서
연결 대상 URL을 직접 바꿔 끼우는 방식입니다. 별도의 "이름/닉네임" 입력칸은 없고,
`Remote URL`에 넣은 주소 자체가 지금 연결된 대상입니다.

1. 앱 상단/좌측 **Settings** → 왼쪽 메뉴 **Gateway** 선택
2. **Applies to**: 보통 `All profiles`(기본값, 모든 프로필에 적용)를 선택합니다.
   특정 프로필(예: `coordinator`)만 다른 원격지에 붙이고 싶을 때만 그 프로필 칩을
   따로 선택해서 개별 설정할 수 있습니다.
3. **Connection mode**: `Remote gateway` 카드 선택 (체크 표시로 확인)
4. **Remote URL**: `https://smb-dashboard.srv1923951.hstgr.cloud` 입력 (방법 C 기준.
   터널 경유라면 `http://127.0.0.1:19128`)
5. **Authentication**: `Sign in` 클릭 → `.hermes/.env`의
   `HERMES_DASHBOARD_BASIC_AUTH_USERNAME`(기본 `admin`)과 원본 비밀번호 입력
   (`_PASSWORD_HASH`는 그 비밀번호의 scrypt 해시라 로그인 폼에는 못 씁니다)
6. `Test remote`로 연결을 확인한 뒤 `Save and reconnect` 클릭
7. 로그인에 성공하면 `Authentication`이 `✓ Signed in`으로 바뀌고, 토큰이 OS
   자격 증명 저장소에 저장되어 다음 실행부터 자동 재연결됩니다. 연결되면 이 VPS의
   `.hermes/profiles/*`(coordinator 등 7개 프로필)를 채팅/세션 목록에서 선택해 쓸 수
   있습니다.

> **다른 VPS 프로젝트(ADCreator/MICE)로 전환하려면?** 같은 Gateway 화면에서
> `Remote URL`을 그 프로젝트의 도메인으로 바꾸고 다시 로그인하면 됩니다 — "회사
> 전환"은 이 URL을 바꾸는 것이고, 프로필 전환(직원 바꾸기)과는 다른 조작입니다.
> 세 프로젝트의 주소·계정 정리와 전환 방법은
> [22-vps-dashboard-access.md](22-vps-dashboard-access.md)를 참고하세요.
>
> Desktop 앱 UI 문구(메뉴명 등)는 버전에 따라 달라질 수 있습니다 — 위 절차는 0.21.0
> 기준 실측입니다.

## 7. 로그인 자격증명 보관 위치 — `.hermes/config.yaml`이 아니라 `.hermes/.env`

이 저장소는 **공개 GitHub 저장소**입니다. 초기에는 개발 편의상 `admin` / `smb-dev-2026`
기본 비밀번호 해시를 `.hermes/config.yaml`(git 추적 대상)에 직접 커밋했었는데,
2026-09-07에 이를 발견하고 방법 C(Traefik로 상시 HTTPS 노출)를 적용하면서 함께
정리했습니다 — `config.yaml`은 계속 공개 저장소에 커밋되므로, 실제 로그인
자격증명(사용자명/비밀번호 해시/서명 시크릿)은 그 파일에 두면 안 됩니다.

지금은 세 값 모두 `.hermes/.env`(`.gitignore`에 등록돼 있어 커밋되지 않음)에
환경변수로 들어 있습니다:

```
HERMES_DASHBOARD_BASIC_AUTH_USERNAME=...
HERMES_DASHBOARD_BASIC_AUTH_PASSWORD_HASH=scrypt$...
HERMES_DASHBOARD_BASIC_AUTH_SECRET=...
```

(env가 `config.yaml`보다 항상 우선합니다 — `plugins/dashboard_auth/basic/__init__.py`
참고.) 비밀번호를 새로 바꾸고 싶다면:

```bash
docker compose exec dashboard /opt/hermes/.venv/bin/python3 -c "
import sys; sys.path.insert(0, '/opt/hermes')
from plugins.dashboard_auth.basic import hash_password
print(hash_password('새로운-강력한-비밀번호'))
"
```

출력된 `scrypt$...` 문자열을 `.hermes/.env`의 `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD_HASH`에
넣고(`username`도 원하면 함께 교체) 재시작합니다:

```bash
docker compose restart dashboard
```

> 예전에 `config.yaml`에 커밋됐던 `admin`/`smb-dev-2026` 해시는 git 히스토리에 여전히
> 남아있지만, 그 해시는 위 정리 시점에 이미 새 값으로 교체되어 더 이상 유효한 로그인
> 자격증명이 아닙니다 — 다만 완전히 새 프로젝트로 이 구조를 복제한다면 처음부터
> `.env`에만 비밀번호를 두고 절대 `config.yaml`에 커밋하지 마세요.

## 8. OAuth로 대체하고 싶다면

비밀번호 대신 Nous Portal OAuth로 로그인하게 하려면:

```bash
docker compose exec dashboard hermes dashboard register
```

이 명령이 OAuth 클라이언트 ID를 `.env`에 기록합니다. 이후 Desktop 앱 로그인 화면에서
OAuth 옵션을 선택하면 됩니다. 두 방식(`basic_auth`/OAuth)은 동시에 켜둘 수 있습니다.

## 9. 트러블슈팅

- **`curl`이 빈 응답(Empty reply)을 반환한다** → `dashboard.basic_auth`가 비어 있는
  상태로 `--host 0.0.0.0`을 준 것입니다. 인증 provider가 없으면 Hermes가 바인딩 자체를
  거부하고 s6가 계속 재시작합니다(`docker compose ps`는 그래도 `Up`으로 보임 — 08장
  실측 사례). `docker compose logs dashboard`에서 `Refusing to bind dashboard to
  0.0.0.0` 메시지를 확인하고 2번을 다시 점검하세요.
- **Desktop 앱에서 로그인은 되는데 세션이 자꾸 끊긴다** → `dashboard.basic_auth.secret`이
  비어 있으면 프로세스 재시작마다 세션 서명 키가 랜덤으로 바뀝니다. 32바이트 이상의
  고정값을 `secret`에 넣어두세요.
- **SSH 터널로는 되는데 도메인으로는 WebSocket이 안 붙는다** → nginx/Caddy 설정에서
  `Upgrade`/`Connection` 헤더 전달(`/api/ws`, `/api/pty` 경로)이 빠진 경우가 흔합니다.
  4번의 nginx 예시를 확인하세요.
- **원격 로그인 후 특정 프로필(coordinator 등)이 안 보인다** → VPS 쪽 `hermes doctor`로
  프로필 7개가 정상 인식되는지 먼저 확인하세요(`docker compose exec dashboard hermes
  doctor`). Desktop 앱은 백엔드가 인식한 프로필만 보여줍니다.

## 10. 보안 체크리스트

- [ ] 공개 노출(방법 B) 전에는 반드시 6번으로 기본 비밀번호 교체
- [ ] 대시보드 컨테이너 포트(9119/19128)는 절대 직접 공인 IP에 바인딩하지 않고, 항상
      리버스 프록시(TLS 종료) 뒤에 두거나 SSH 터널로만 접근
- [ ] `dashboard.basic_auth.secret`을 32바이트 이상 랜덤값으로 고정
- [ ] 게이트웨이 포트(18651, 메시징 봇용)와 대시보드 포트(19128, Desktop/브라우저용)를
      혼동하지 말 것 — 서로 용도가 다름
