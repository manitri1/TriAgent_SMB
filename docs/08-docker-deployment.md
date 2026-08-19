# 08. Docker 배포 — 포트/볼륨 조사와 운영 명령어

## 조사 방법론

`e:/work/Hermes/` 아래 모든 형제 프로젝트의 `docker-compose.yml`을 정적으로 스캔했습니다.
이 방법론은 `TriAgent_Planner`/`TriAgent_MICE`의 `docs/08-docker-deployment.md`와
동일합니다.

## 조사 시점(2026-08-19) 점유 현황

| 프로젝트 | 호스트 게이트웨이 포트 | 호스트 대시보드 포트 | 컨테이너명 |
|---|---|---|---|
| HermesPPTAutoAgent | 8000 | — | (unnamed) |
| HermesMICEAgents | 8642 | 9119 | `hermes-mice`, `hermes-mice-dashboard` |
| HermesSMBStaff | 8643 | 127.0.0.1:9120 | `hermes-smb`, `hermes-smb-dashboard` |
| HermesContentsMarketingAgent | 8642(host network) | 127.0.0.1:8765 | (unnamed) |
| HermesLandAssetAgent | 8742 | 9219 | `hermes-realestate`, `hermes-policy-db` |
| TriAgent_Planner | 8644 | 127.0.0.1:9121 | `hermes-triplanner`, `hermes-triplanner-dashboard` |
| TriAgent_ContentCreator | 8647 | 127.0.0.1:9124 | `hermes-contentcreator`, `hermes-contentcreator-dashboard` |
| TriAgent_MICE | 8648 | 127.0.0.1:9125 | `hermes-triagent-mice`, `hermes-triagent-mice-dashboard` |
| TriAgent_IR | 8649 | 127.0.0.1:9126 | `hermes-triagent-ir`, `hermes-triagent-ir-dashboard` |
| TriAgent_HigsSuper | 8650 | 127.0.0.1:9127 | `hermes-higssuper`, `hermes-higssuper-dashboard` |

점유된 전체 호스트 포트: `8000, 8642, 8643, 8644, 8647, 8648, 8649, 8650, 8742, 8765, 9119,
9120, 9121, 9124, 9125, 9126, 9127, 9219`.

## `TriAgent_SMB` 선택 값

- **게이트웨이:** 호스트 `8651` → 컨테이너 `8642`
- **대시보드:** 호스트 `127.0.0.1:9128` → 컨테이너 `9119`
- **컨테이너명:** `hermes-triagent-smb`, `hermes-triagent-smb-dashboard`
- **Mock POS:** 호스트 `8080` → 컨테이너 `8080` (형제 프로젝트 중 8080을 쓰는 곳이 없어
  기존 값 유지)

> ⚠️ **이름 혼동 주의:** `TriAgent_SMB`는 기존 `HermesSMBStaff`(포트 8643/9120, 컨테이너명
> `hermes-smb*`)와 **이름이 비슷한 완전히 별개의 프로젝트**입니다. 컨테이너명을
> `hermes-smb*`로 짓지 않고 `hermes-triagent-smb*`로 명시적으로 구분한 것은 이 혼동을
> 방지하기 위함입니다 — `TriAgent_MICE`가 `HermesMICEAgents`와 구분한 것과 동일한 패턴입니다.

- Compose 프로젝트명: 최상단 `name: hermes-triagent-smb`로 고정.
- 볼륨: named volume이 아니라 `./.hermes:/opt/data` bind mount — 데이터가 이 저장소가
  위치한 드라이브(E:)에 남습니다.
- 이미지: `mock-pos`는 `./mock-pos/Dockerfile`로 빌드. `hermes`는 Playwright/Chromium이
  필요한 프로필이 없으므로(웹 리서치는 `web`/`search`로 충분) **base 이미지
  `nousresearch/hermes-agent:latest`를 그대로 사용**합니다 — `TriAgent_MICE`처럼 커스텀
  Dockerfile을 만들지 않습니다.

## 운영 명령어

```bash
# 최초 배포 (7개 프로필 전체)
cp .hermes/.env.example .hermes/.env   # OPENAI_API_KEY, MOCK_POS_API_KEY 채우기
for name in coordinator order-payment-agent inventory-agent reservation-agent customer-service-agent sales-analytics-agent marketing-crm-agent; do
  grep -E "^(OPENAI_API_KEY|MOCK_POS_BASE_URL|MOCK_POS_API_KEY)=" .hermes/.env > ".hermes/profiles/$name/.env"
done

docker compose build
docker compose up -d
docker compose ps
docker compose exec hermes hermes doctor

# 챗
docker compose exec hermes hermes chat --profile coordinator -q "..."
docker compose exec -it hermes hermes chat --profile coordinator

# 중지
docker compose down
```

## 검증 완료 / 아직 검증하지 않은 것

- ✅ 포트·컨테이너명이 다른 형제 프로젝트와 겹치지 않음을 정적 스캔으로 검증했습니다.
- ✅ **2026-08-19: 실제 `docker compose build`/`up`을 실행했습니다.** Docker Desktop이
  이미 설치·구동 중이었고(`docker version` 정상 응답), `docker ps`로 다른 형제 프로젝트
  6개(HigsSuper/MICE/IR/ContentCreator/TriPlanner/WikiDocSummery)가 실제로 실행 중임을
  확인한 뒤, 그 어떤 것과도 포트/컨테이너명이 겹치지 않고 3개 컨테이너
  (`hermes-triagent-smb`, `-dashboard`, `-mock-pos`)가 모두 정상 기동함을 확인했습니다.
- ✅ `hermes doctor`로 컨테이너 내부에서 7개 프로필이 모두 인식됨을 확인했습니다
  ([07-roadmap.md](07-roadmap.md) 8번, [10-usecase-tests.md](10-usecase-tests.md) TC-19).

## ⚠️ 발견한 함정 — 대시보드가 "Up"인데 실제로는 죽어 있었음 (2026-08-19)

배포 몇 시간 뒤 재점검하다가 `docker compose ps`에서는 `hermes-triagent-smb-dashboard`가
계속 `Up`으로 표시됐지만, `curl http://localhost:9128/`이 빈 응답(`Empty reply`)을
반환하는 것을 발견했습니다. 로그를 열어보니 원인은:

- Docker의 포트 포워딩이 작동하려면 컨테이너 **내부** 서비스가 `0.0.0.0`에 바인딩돼야
  합니다(`127.0.0.1`로 바인딩하면 컨테이너 네임스페이스 밖에서 도달 불가) — 그래서
  `docker-compose.yml`에 `command: ["dashboard", "--host", "0.0.0.0", ...]`를 이미
  넣어뒀습니다.
- 하지만 Hermes Agent는 `0.0.0.0` 바인딩을 감지하면 인증 provider(비밀번호 또는 OAuth)가
  설정돼 있지 않은 한 **바인딩 자체를 거부**합니다("Refusing to bind dashboard to
  0.0.0.0 — ... no auth providers are registered").
- 인증을 설정하지 않았기 때문에 컨테이너 내부의 s6 supervisor가 `dashboard` 서비스를
  계속 재시작→실패→재시작을 반복했습니다. **문제는 이 크래시 루프가 s6 레벨에서
  일어나서 컨테이너 프로세스 자체는 한 번도 종료되지 않았다는 것**입니다 — 그래서
  Docker의 `RestartCount`는 계속 `0`이었고 `docker compose ps`는 계속 `Up`으로만
  보였습니다. **"Up" 상태만으로는 내부 서비스가 실제로 살아있는지 알 수 없습니다** —
  로그를 열어보거나 실제로 엔드포인트를 호출해봐야 합니다.

**조치**: `.hermes/config.yaml`에 `dashboard.basic_auth`(사용자명 + scrypt 해시)를
추가했습니다. 대시보드가 호스트에서 `127.0.0.1:9128`로만 노출되므로(외부 접근 불가)
개발용 기본 비밀번호를 그대로 커밋했습니다 — 로컬 개발 외 용도로 쓰기 전에는 새
해시로 교체하세요(`.hermes/config.yaml`의 주석에 재생성 명령어 포함). 수정 후
`docker compose restart dashboard`로 재시작해 `HERMES_DASHBOARD_READY` 로그와
`curl` 302(로그인 리다이렉트) 응답을 확인했습니다.

**교훈**: 이 프로젝트의 `main` `hermes` 컨테이너와 `mock-pos`도 같은 방식(로그 전체를
`grep -icE "error|refus|traceback|exception"`, s6 서비스 재시작 횟수 확인)으로
재점검해 실제로 깨끗함을 확인했습니다 — 배포 직후 한 번 확인했다고 끝이 아니라, 시간이
지난 뒤에도 로그 기반으로 재점검하는 습관이 필요합니다.
