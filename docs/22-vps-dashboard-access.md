# 22. VPS 대시보드 접속 가이드 — 포트/Traefik/자격증명 한눈에 보기

이 VPS(`srv1923951`, Hostinger)에는 같은 계정(`manitri1`) 소유의 Hermes 프로젝트가
여러 개 떠 있습니다. 2026-09-07에 **TriAgent_SMB**에서 두 가지 문제를 고치면서,
같은 VPS의 나머지 프로젝트에도 동일하게 적용하기로 했습니다:

1. **포트 충돌 방지**: 흔히 쓰는 4자리 포트(8xxx/9xxx)를 그대로 호스트에 노출하면
   이 VPS에 새 컨테이너가 계속 추가될 때 충돌 여지가 있음 → 호스트 포트를 전부
   **1xxxx 대역**(기존 값 + 10000)으로 이전. 컨테이너 **내부** 포트는 그대로 둔다.
2. **로그인 자격증명이 공개 저장소에 커밋되는 문제**: 대시보드 basic_auth의
   `username`/`password_hash`/`secret`이 git 추적 대상인 `.hermes/config.yaml`에
   커밋되어 있었음(TriAgent_SMB, TriAgent_ADCreator) → 실제 값은 그대로 유지한 채
   git 추적에서 제외된 `.hermes/.env`로 이전(`HERMES_DASHBOARD_BASIC_AUTH_USERNAME`/
   `_PASSWORD_HASH`/`_SECRET` 환경변수 — env가 config.yaml보다 항상 우선).
3. **SSH 터널 없는 상시 접속**: 이 VPS에 이미 떠 있는 공유 Traefik(`traefik-traefik-1`,
   `80`/`443` 점유, `*.srv1923951.hstgr.cloud` 서브도메인 자동 라우팅)에 라벨만 붙여
   각 프로젝트 대시보드를 HTTPS 서브도메인으로 노출. basic_auth는 그대로 유지되므로
   보호는 유지된다.

## 한눈에 보기

| 프로젝트 | 저장소 | 공개여부 | 게이트웨이 | 대시보드(로컬) | 대시보드(HTTPS, 터널 불필요) | 자격증명 위치 | 상태 |
|---|---|---|---|---|---|---|---|
| **TriAgent_SMB** | `/opt/smb` | 공개 | `18651`(⚠️ 내부 loopback 바인딩 문제로 현재 불통 — 8번 참고) | `127.0.0.1:19128` | `https://smb-dashboard.srv1923951.hstgr.cloud` | `.hermes/.env`의 `HERMES_DASHBOARD_BASIC_AUTH_*` | ✅ 완료·검증됨 |
| **TriAgent_MICE** | `/opt/mice` | 공개 | `18648` | `127.0.0.1:9125`(포트 변경 없이 그대로 사용) | `https://mice-dashboard.srv1923951.hstgr.cloud` | 이미 `.hermes/.env`에 있음(그대로 사용) | ✅ 완료·검증됨(2026-09-08) |
| **TriAgent_ADCreator** | `/opt/adcreator` | 비공개 | `8652`(localhost 전용이라 그대로 유지) | `127.0.0.1:19130` | `https://adcreator-dashboard.srv1923951.hstgr.cloud` | `.hermes/config.yaml`의 `dashboard.basic_auth`(⚠️ `.env`로 아직 안 옮김 — 8번 참고) | ✅ 완료·검증됨(2026-09-08) |

Mock POS(`18080`)·webapp(`19131`)은 SMB 전용 서비스라 다른 프로젝트에는 해당 없음.
webapp도 같은 방식으로 `https://smb-webapp.srv1923951.hstgr.cloud`가 이미 열려 있습니다
(단, Hermes Desktop 앱이 아니라 브라우저로 쓰는 커스텀 운영 콘솔이라 이 문서의 Desktop
연동 대상은 아닙니다 — [14-webapp-users-guide.md](14-webapp-users-guide.md) 참고).

Hostinger hPanel이 관리하는 `hermes-agent-q66p`/`hermes-agent-htjj`(포트 `32769`/`32770`,
컨테이너 내부 `4860`)와 공유 Traefik 자체는 건드리지 않았다 — 관리 체계가 달라 직접
손대면 hPanel의 자동 갱신/관리 흐름과 충돌할 수 있음.

## Hermes Desktop 앱에서 접속하기

2026-09-08 실측(버전 0.21.0) — 이 앱은 "여러 서버를 이름 붙여 목록에 저장"하는 구조가
**아닙니다**. `Settings → Gateway` 화면 하나에서 `Remote URL`을 직접 바꿔 끼우는 방식이라,
별도의 "이름/닉네임" 입력칸이 없습니다. 프로젝트를 바꾼다는 건 곧 이 URL 값을 바꾼다는
뜻입니다.

1. `Settings` → 왼쪽 메뉴 `Gateway`
2. **Applies to**: `All profiles`(기본값) 그대로 두거나, 특정 프로필에만 다른 원격지를
   쓰고 싶으면 그 프로필 칩만 선택
3. **Connection mode**: `Remote gateway` 카드 선택
4. **Remote URL**: 위 표의 "대시보드(HTTPS)" 열 값 (예: SMB는
   `https://smb-dashboard.srv1923951.hstgr.cloud`)
5. **Authentication** 쪽 `Sign in` 클릭 → 해당 프로젝트의 `HERMES_DASHBOARD_BASIC_AUTH_USERNAME`
   /실제 비밀번호 입력(`_PASSWORD_HASH`는 해시라 로그인 폼에 못 씀 — 모르면 아래 "비밀번호
   재발급" 참고)
6. `Test remote`로 확인 후 `Save and reconnect`
7. 성공하면 `Authentication`이 `✓ Signed in`으로 바뀌고, 토큰이 OS 자격 증명 저장소에
   저장되어 다음부터 자동 재연결됩니다.

**다른 프로젝트로 바꾸려면** 같은 Gateway 화면으로 돌아와 `Remote URL`만 다른 프로젝트
주소로 교체하고 다시 로그인하면 됩니다. 세 프로젝트를 동시에 쓰고 싶다면 PC마다(또는
프로필 칩별로) 원하는 프로젝트를 고정해두는 방식을 권장합니다.

SSH 터널이 여전히 필요 없다는 것이 핵심 — VPN/터널 프로그램을 매번 켤 필요가 없다.
(SSH 터널 방식 자체는 여전히 가능하며 [19장](19-hermes-desktop-vps-guide.md) 3번에
정리돼 있다.)

## 비밀번호를 모르거나 재발급하고 싶을 때

```bash
cd /opt/<프로젝트>   # smb, mice, adcreator 중 하나
docker compose exec dashboard /opt/hermes/.venv/bin/python3 -c "
import sys; sys.path.insert(0, '/opt/hermes')
from plugins.dashboard_auth.basic import hash_password
print(hash_password('새로운-강력한-비밀번호'))
"
```

출력된 `scrypt$...` 문자열을 해당 프로젝트의 `.hermes/.env`의
`HERMES_DASHBOARD_BASIC_AUTH_PASSWORD_HASH`에 넣고 `docker compose restart dashboard`.

## MICE / ADCreator 적용 내역 (2026-09-08)

`/opt/smb` 바깥 경로(다른 git 저장소) 파일 수정은 이 세션의 자동 모드 권한 분류기가
한 번 차단했지만, 사용자가 "계속 진행해"로 재승인해 두 프로젝트 모두 실제로 적용을
완료했다. 다만 애초에 계획했던 것보다 **범위를 최소화**했다 — 라우터 이름 충돌 여부만
확인 후 Traefik 라벨만 추가했고, 포트 재배치나 자격증명 이전 같은 부가 정리는 하지
않았다. 실제로 바뀐 것과 아직 남은 것을 구분해 둔다.

- **MICE**: `docker-compose.yml`의 `dashboard` 서비스에 Traefik 라벨(라우터명
  `mice-dashboard`, 호스트 `mice-dashboard.srv1923951.hstgr.cloud`)만 추가하고
  `docker compose up -d dashboard`로 재생성. **포트는 `9125` 그대로** — HTTPS 접속은
  포트 번호와 무관하므로 애초 계획했던 `19125` 재배치는 하지 않았다(불필요 판단).
  인증은 이미 `.hermes/.env`에 있던 값을 그대로 썼다. `https://mice-dashboard...`가
  `302`를 반환하는 것까지 확인함. **⬜ 남은 일**: `docker-compose.yml`의 이 변경사항
  git commit(다른 pending 변경과 섞여 있으니 그 파일만 골라서).
- **ADCreator**: `docker-compose.yml`의 `dashboard` 서비스에 Traefik 라벨(라우터명
  `adcreator-dashboard`)만 추가하고 재생성. **게이트웨이 포트(`8652`)와 인증 위치는
  손대지 않았다** — `dashboard.basic_auth`(username/password_hash/secret)가 여전히
  `.hermes/config.yaml`에 평문 해시로 커밋되어 있다(이 저장소는 비공개라 당장 위험도는
  낮지만, TriAgent_SMB에서 겪었던 것과 같은 패턴이므로 정리 권장). **⬜ 남은 일**:
  (1) `docker-compose.yml` 변경사항 git commit, (2) 원하면 `config.yaml`의
  `dashboard.basic_auth` 값을 `.hermes/.env`로 옮기고 config.yaml에서 삭제(SMB가
  했던 방식, [19장](19-hermes-desktop-vps-guide.md) 7번 참고).

두 프로젝트 모두 `docs/13-hermes-desktop-connect.md`(ADCreator 저장소, 세 프로젝트를
아우르는 Desktop 연동 가이드)에도 이번 HTTPS 방식을 반영해 두었다.

## 헬스체크 명령 모음

```bash
# SMB
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:19128/
curl -s -o /dev/null -w "%{http_code}\n" https://smb-dashboard.srv1923951.hstgr.cloud/

# MICE
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:9125/
curl -s -o /dev/null -w "%{http_code}\n" https://mice-dashboard.srv1923951.hstgr.cloud/

# ADCreator
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:19130/
curl -s -o /dev/null -w "%{http_code}\n" https://adcreator-dashboard.srv1923951.hstgr.cloud/
```
`302`(로그인 리다이렉트) 또는 `200`이면 정상. `000`/빈 응답이면 `docker compose logs
dashboard --tail=50`으로 원인을 확인한다 — "Up" 상태만으로는 내부 크래시 루프를
알 수 없다는 게 이 프로젝트군에서 반복 확인된 함정이다([08장](08-docker-deployment.md)
참고).
