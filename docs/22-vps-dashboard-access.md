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
| **TriAgent_SMB** | `/opt/smb` | 공개 | `18651` | `127.0.0.1:19128` | `https://smb-dashboard.srv1923951.hstgr.cloud` | `.hermes/.env`의 `HERMES_DASHBOARD_BASIC_AUTH_*` | ✅ 완료·검증됨 |
| **TriAgent_MICE** | `/opt/mice` | 공개 | `18648` | `127.0.0.1:19125`(예정) | `https://mice-dashboard.srv1923951.hstgr.cloud`(예정) | 이미 `.hermes/.env`에 있음(수정 불필요) | ⬜ 안내만 함, 미적용 |
| **TriAgent_ADCreator** | `/opt/adcreator` | 비공개 | `18652`(예정, 기존 `8652`도 localhost 전용이라 긴급도 낮음) | `127.0.0.1:19130`(이미 1xxxx) | `https://adcreator-dashboard.srv1923951.hstgr.cloud`(예정) | `.hermes/config.yaml`→`.hermes/.env`로 이전 필요 | ⬜ 안내만 함, 미적용 |

Mock POS(`18080`)·webapp(`19131`)은 SMB 전용 서비스라 다른 프로젝트에는 해당 없음.

Hostinger hPanel이 관리하는 `hermes-agent-q66p`/`hermes-agent-htjj`(포트 `32769`/`32770`,
컨테이너 내부 `4860`)와 공유 Traefik 자체는 건드리지 않았다 — 관리 체계가 달라 직접
손대면 hPanel의 자동 갱신/관리 흐름과 충돌할 수 있음.

## Hermes Desktop 앱에서 접속하기

1. Desktop 앱 로그인 화면에서 "원격 서버 추가"(또는 이에 준하는 메뉴) 선택
2. 서버 주소: 위 표의 "대시보드(HTTPS)" 열 값 (예: SMB는
   `https://smb-dashboard.srv1923951.hstgr.cloud`)
3. 계정: 해당 프로젝트의 `.hermes/.env`에 적힌 `HERMES_DASHBOARD_BASIC_AUTH_USERNAME`/
   비밀번호(평문 비밀번호를 직접 입력하는 원격 서버 쪽에선 `_PASSWORD_HASH`가 아니라
   실제 비밀번호가 필요 — `_PASSWORD_HASH`는 해시라서 로그인 폼에 넣을 수 없음.
   비밀번호 자체를 모른다면 아래 "비밀번호 재발급" 참고)
4. 로그인 성공 시 앱이 토큰을 OS 자격 증명 저장소에 저장하고 다음부터 자동 재연결

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

## MICE / ADCreator에 아직 적용 안 된 이유

`/opt/smb` 바깥 경로(다른 git 저장소) 파일 수정은 이 세션의 자동 모드 권한 분류기가
차단해, 정확한 변경 내용(설정 diff + 실행할 명령)만 안내하고 실제 적용은 사용자가
직접 하기로 했다(2026-09-07 대화 참고). 안내한 그대로 실행하면 위 표의 "예정" 값이
그대로 반영된다 — 안내 내용 요지:

- **MICE**: `docker-compose.yml`의 dashboard 포트를 `9125→19125`로, Traefik 라벨(라우터명
  `mice-dashboard`, 호스트 `mice-dashboard.srv1923951.hstgr.cloud`)을 추가하고
  `docker compose up -d` → 헬스체크 → `docker-compose.yml`만 git add/commit/push
  (이 저장소엔 무관한 대량의 pending 변경사항이 있어 그 파일만 골라 커밋해야 함).
- **ADCreator**: `.hermes/config.yaml`에 커밋돼 있던 `dashboard.basic_auth`
  (username/password_hash/secret)를 실제 값 그대로 `.hermes/.env`로 옮기고
  config.yaml에서는 삭제, 게이트웨이 포트를 `8652→18652`로, Traefik 라벨(라우터명
  `adcreator-dashboard`)을 추가 → `docker compose up -d` → 헬스체크 → `config.yaml`은
  basic_auth 삭제 hunk만 `git add -p`로 골라 커밋(같은 파일에 무관한 Notion MCP 서버
  추가가 섞여 있어 그 부분은 건드리지 않음), `docker-compose.yml`은 통째로 커밋.

## 헬스체크 명령 모음

```bash
# SMB
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:19128/
curl -s -o /dev/null -w "%{http_code}\n" https://smb-dashboard.srv1923951.hstgr.cloud/

# MICE (적용 후)
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:19125/
curl -s -o /dev/null -w "%{http_code}\n" https://mice-dashboard.srv1923951.hstgr.cloud/

# ADCreator (적용 후)
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:19130/
curl -s -o /dev/null -w "%{http_code}\n" https://adcreator-dashboard.srv1923951.hstgr.cloud/
```
`302`(로그인 리다이렉트) 또는 `200`이면 정상. `000`/빈 응답이면 `docker compose logs
dashboard --tail=50`으로 원인을 확인한다 — "Up" 상태만으로는 내부 크래시 루프를
알 수 없다는 게 이 프로젝트군에서 반복 확인된 함정이다([08장](08-docker-deployment.md)
참고).
