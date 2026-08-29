# 기술

## 기술 스택

| 구성 요소 | 언어 / 프레임워크 | 버전 | 비고 |
|---|---|---|---|
| Hermes 런타임 | Nous Research Hermes Agent CLI | `latest` (이미지 `nousresearch/hermes-agent:latest`) | 이 프로젝트가 빌드하는 언어 런타임이 아니라 사전 빌드된 CLI 에이전트 이미지 — 프로필은 코드가 아니라 설정 + 프롬프트 데이터임 |
| Mock POS 백엔드 | Python + FastAPI | Python 3.11 (Dockerfile 베이스), FastAPI `0.115.0` | REST 시뮬레이터: 주문, 재고, 예약, 결제, 매출 리포트 |
| Mock POS 서버 | uvicorn | `0.30.6` (`[standard]` extra) | ASGI 서버 |
| Mock POS 검증 | Pydantic | `2.9.2` | 요청/응답 모델 |
| 대시보드 백엔드 | Python + FastAPI | Python 3.11, FastAPI `0.115.0` | mock-pos를 프록시하고, 승인 JSON 스토어를 소유하며, 빌드된 프런트엔드를 정적 파일로 서빙 |
| 대시보드 백엔드 서버 | uvicorn | `0.30.6` (`[standard]` extra) | ASGI 서버 |
| 대시보드 백엔드 검증 | Pydantic | `2.9.2` | 요청/응답 모델 |
| 대시보드 백엔드 HTTP 클라이언트 | httpx | `0.27.2` | 서버 사이드에서 mock-pos를 호출하는 데 사용됨 (브라우저는 mock-pos에 대한 CORS 접근 권한이 없음) |
| 대시보드 프런트엔드 | React + TypeScript | React `18.3.1`, TypeScript `5.5.4` | 라우팅 라이브러리 없음 — 페이지 선택은 `App.tsx`에서 수작업으로 처리; CSS 프레임워크 없음 — 순수 `styles.css` |
| 대시보드 프런트엔드 빌드 도구 | Vite | `5.4.1` (`@vitejs/plugin-react` `4.3.1`) | `npm run build` → `tsc -b && vite build`, 백엔드가 서빙하는 정적 번들 생성 |
| 테스트 (Python 백엔드 양쪽) | pytest | `requirements-dev.txt`에 프로젝트 고정 버전으로 명시 | mock-pos: `mock-pos/tests/test_flow.py`, 설정은 `mock-pos/pytest.ini`(`pythonpath = .`); 대시보드 백엔드: `smb-dashboard/backend/tests/test_approvals.py`는 `/api/approvals*` 엔드포인트만 커버함(순수 로컬 JSON 스토어, httpx 호출 없음). `pytest-httpx`는 `requirements-dev.txt`에 선언되어 있지만 아직 어떤 테스트에서도 사용되지 않음. httpx로 mock-pos를 호출하는 라우터들(`orders.py`, `inventory.py`, `reservations.py`, `reports.py`)은 현재 테스트 커버리지가 없음. |
| 테스트 (프런트엔드) | — | — | `smb-dashboard/frontend/package.json`에 아직 테스트 스크립트가 구성되지 않음 (`dev` / `build` / `preview`만 존재) |

## 선정 근거

- **양쪽 백엔드 모두 FastAPI 선택**: 비동기 네이티브 지원, Pydantic과 통합된 요청/응답 검증, 무료로 제공되는 OpenAPI 문서 생성 — 이해하기 쉽고 Hermes의 `code_execution` 스킬이 호출하기 쉬워야 하는 두 개의 작고 초점이 명확한 REST 서비스(POS 벤더 API를 시뮬레이션하는 mock-pos; 프록시 + 소규모 CRUD 스토어 역할을 하는 대시보드 백엔드)에 적합한 선택이다.
- **프런트엔드에 React + Vite 선택**: 대시보드는 완전한 애플리케이션이 아니라 경량 커스텀 웹 UI로 명확히 범위가 정해져 있으며(docs/12 "옵션 C"), 다섯 개의 단순하고 대체로 독립적인 화면(Orders / Inventory / Reservations / Sales Summary / Approvals)에는 라우터나 상태 관리 라이브러리를 도입하지 않아도 Vite의 빠른 개발/빌드 사이클과 React의 컴포넌트 모델만으로 충분하다.
- **CSS 프레임워크 없음, 라우터 없음**: MVP 범위에 맞춰 의도적으로 최소화한 것으로 — `src/api.ts`는 수작업으로 작성한 fetch 클라이언트이고, 페이지 전환은 `App.tsx`에서 직접 처리한다. 단일 매장, 관심사별 단일 페이지 MVP를 위해 프런트엔드 번들을 작고 의존성이 적게 유지한다.
- **하나의 컨테이너에 정적 파일로 번들링**: 프런트엔드는 Docker 이미지 빌드 시점에 빌드되어 FastAPI의 `StaticFiles`로 서빙되며, 별도의 nginx/리버스 프록시 컨테이너를 피한다 — 이는 `mock-pos/Dockerfile`이 이 프로젝트에서 이미 확립한 것과 동일한 패턴이다.
- **승인용 JSON 파일 스토어 (`data/approvals.json`)**: 대시보드는 이 프로젝트에서 구조화된 영속 HITL 상태가 필요한 첫 번째 구성 요소다(이전에는 승인이 Discord 대화 이력 안에만 존재했음). 호스트에 바인드 마운트된 플랫 JSON 파일이면 단일 매장, 단독 관리자 MVP에는 충분하며 데이터베이스 의존성 도입을 피할 수 있다.

## 개발 환경 요구사항

- **Python 3.11** — `mock-pos`와 `smb-dashboard/backend` 모두 이 버전을 대상으로 함 (각 `Dockerfile` 참조)
- **Node.js 20** (또는 Vite 5 / TypeScript 5.5와 호환되는 버전) — `smb-dashboard/frontend` 빌드에 필요
- **Docker + Docker Compose** — Windows에서 별도의 로컬 Hermes CLI 설치 없이 전체 4개 서비스 스택을 실행하는 지원되는 방법
- Docker를 대신하는 로컬 개발 반복 방법:
  - Mock POS 단독 실행: `cd mock-pos && pip install -r requirements-dev.txt && pytest && uvicorn mock_pos.main:app --reload --port 8080`
  - Hermes 단독 실행: `export HERMES_HOME="$(pwd)/.hermes" && hermes -p coordinator chat` (로컬 Hermes Agent CLI 설치 필요)

## 빌드 및 배포

`docker-compose.yml`은 compose 프로젝트 이름 `hermes-triagent-smb` 아래 4개 서비스를 정의한다:

| 서비스 | 이미지 / 빌드 | 컨테이너 이름 | 호스트 포트 | 의존 관계 |
|---|---|---|---|---|
| `hermes` | `nousresearch/hermes-agent:latest`, 명령어 `gateway run` | `hermes-triagent-smb` | `8651:8642` | `mock-pos` |
| `dashboard` | `nousresearch/hermes-agent:latest`, 명령어 `dashboard --host 0.0.0.0 --no-open` | `hermes-triagent-smb-dashboard` | `127.0.0.1:9128:9119` | `hermes` |
| `mock-pos` | `./mock-pos`로부터 빌드 | `hermes-triagent-smb-mock-pos` | `8080:8080` | — |
| `smb-dashboard` | `./smb-dashboard`로부터 빌드 (멀티스테이지 Dockerfile, 프런트엔드 빌드 → FastAPI 이미지) | `hermes-triagent-smb-dashboard-ui` | `127.0.0.1:8652:8652` | `mock-pos` |

비고:
- `dashboard`(포트 9128)는 Hermes Agent 자체의 내장 CLI 대시보드로 — 이 프로젝트가 만드는 커스텀 웹 UI인 `smb-dashboard`(포트 8652)와는 별개다. 컨테이너 이름은 `docker ps`에서 혼동을 피하기 위해 의도적으로 `-ui` 접미사로 구분된다.
- `.hermes/`는 (네임드 볼륨이 아닌) 바인드 마운트로 설정되어 `HERMES_HOME` 데이터가 호스트 드라이브에 유지된다.
- `smb-dashboard/data/`도 같은 이유로 바인드 마운트되어 — 승인 JSON 스토어가 컨테이너 재시작 후에도 유지된다.
- `smb-dashboard`용 환경 설정: `MOCK_POS_BASE_URL`, `MOCK_POS_API_KEY`, `STORE_ID`, `LOW_STOCK_THRESHOLD`, `DASHBOARD_BASIC_AUTH_USER`, `DASHBOARD_BASIC_AUTH_PASSWORD`(`docker-compose.yml`에 개발용 기본값 제공됨; 로컬 환경이 아닌 배포 전에는 반드시 재정의해야 함).
- 포트는 동일 호스트에 있는 다른 Hermes 기반 프로젝트들과의 충돌을 피하기 위해 선택되었다(`docs/08-docker-deployment.md` 참조). 실제 배포 전에는 `docker ps` 검증이 필수로 요구된다.

## 테스트 도구

- **pytest** — 두 Python 백엔드 모두를 위한 유일한 테스트 러너. 각 프로젝트 디렉토리(`mock-pos/`, `smb-dashboard/backend/`) 안에서 실행하며, 각각 자체 `pytest.ini`를 정의한다.
- **pytest-httpx** — `requirements-dev.txt`에 선언되어 있지만 아직 어떤 테스트에서도 사용되지 않는다. `test_approvals.py`는 `/api/approvals*` 엔드포인트만 커버한다(순수 로컬 JSON 스토어, httpx 호출 없음); httpx로 mock-pos를 호출하는 라우터들(`orders.py`, `inventory.py`, `reservations.py`, `reports.py`)은 현재 테스트 커버리지가 없다.
- **프런트엔드** — `smb-dashboard/frontend/package.json`에 아직 테스트 스크립트가 존재하지 않는다; 이는 문서화된 제외 항목이 아니라 공백(gap)이다 (아래 Findings 참조).
