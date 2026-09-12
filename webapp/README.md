# Webapp (마니카페 운영 콘솔)

Hermes 에이전트 7개 + Mock POS와 연동되는, 업무별로 설계된 6화면 웹앱
(고객 문의 상담 / 주문 접수 / 재고 파악·주문관리 / 예약 관리 / 실시간 대시보드 /
라이브 데모).
설계 배경과 아키텍처 결정은 `curried-percolating-ocean.md`(plan 문서) 참고.
기존 Hermes 대시보드(`:19128`)의 범용 채팅 UI를 대체하는 게 아니라, 그와
별개로 업무별 화면을 제공하는 것이 목적이다.

## 로컬 실행

```bash
cd webapp
python -m venv .venv
. .venv/Scripts/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

# 비밀번호 해시 생성 (최초 1회)
python scripts/hash_password.py '원하는비밀번호'
# 출력된 scrypt$... 문자열을 WEBAPP_BASIC_AUTH_PASSWORD_HASH에 설정

# 테스트 실행
pytest

# 서버 실행 (mock-pos가 로컬에서 :8080으로 떠 있어야 함)
export MOCK_POS_BASE_URL=http://localhost:8080
export MOCK_POS_API_KEY=dev-key
export WEBAPP_BASIC_AUTH_PASSWORD_HASH='scrypt$...'
uvicorn webapp_bff.main:app --reload --port 8090
```

## Docker 실행

`docker-compose.yml`에 `webapp` 서비스로 등록되어 있다:

```bash
docker compose build webapp
docker compose up -d webapp
curl -u admin:<비밀번호> http://localhost:19131/health
```

## 인증

전체 앱(페이지 + `/api/*`)이 HTTP Basic Auth로 보호된다. `.hermes/config.yaml`의
Hermes 대시보드 계정과는 별개의 자체 계정이다 — `scripts/hash_password.py`로
생성한 scrypt 해시를 `WEBAPP_BASIC_AUTH_PASSWORD_HASH`에 넣는다.

## 빌드 상태

✅ 4화면(고객문의/주문접수/재고/대시보드) 실제 컨테이너 환경에서 curl로
end-to-end 검증까지 마쳤다(2026-09-04). **5번째 화면(예약 관리)은 2026-09-11에
추가**했다 — `reservation-agent`가 이미 mock-pos `/reservations` API로 검증된
상태였으므로, 기존 4화면과 동일한 패턴(읽기는 mock-pos 프록시 직결, 쓰기는
`coordinator` 채팅 위임)으로 화면만 새로 얹었다. pytest 42건 전체 통과 확인,
브라우저 실측 확인은 아직 남아있다(아래 참고):

- **화면 1(고객 문의)** — `customer-service-agent` 직결 채팅. 세션 연속성
  (`--resume`)까지 실제 컨테이너에서 확인.
- **화면 2(주문 접수)** — 품목 선택 폼 + 자유 채팅, 둘 다 `coordinator`로
  수렴. 실제로 "카푸치노 1잔" 주문을 넣어 mock-pos에 `COMPLETED` 상태로
  반영되고, 오늘 매출에도 합산되는 것까지 확인(3분 39초 소요).
- **화면 3(재고)** — 읽기(재고 현황)는 mock-pos 프록시 직결, 쓰기(재입고 요청)는
  `coordinator`로 전달.
- **화면 4(대시보드)** — 읽기 전용, mock-pos 프록시를 거쳐 Chart.js로 렌더링.
  화면 2에서 만든 주문이 반영되는 것을 확인.
- **화면 5(예약 관리, 신규)** — 자유 채팅으로 신규 예약·시간 변경·취소를
  `coordinator`에게 위임(별도 폼 없이 orders.js와 동일한 릴레이 구조), 아래
  표는 mock-pos `/reservations?date=` 프록시로 오늘 예약만 조회. 아직 컨테이너
  환경 curl 검증은 하지 않음 — pytest(단위 테스트)만 통과한 상태.
- **화면 6(라이브 데모, 신규)** — `docs/21-live-demo-plan.md` P2 표의 12개
  타임라인(①~⑫)을 한 화면에서 순서대로 진행한다. 장면마다 미리 채워진 프롬프트를
  전송하면 자동으로 다음 장면으로 넘어가고(기존 화면들의 demoQueue와 동일한
  패턴), 장면별로 관련 화면(재고/예약/주문/고객문의/대시보드)으로 이동해 결과를
  볼 수 있는 링크가 함께 표시된다. 컨테이너 환경 실측은 아직 하지 않음(pytest만
  통과).
- mock-pos 쓰기 엔드포인트는 `/api/pos/*`에 구조적으로 존재하지 않는다
  (`tests/test_pos_proxy.py::test_pos_proxy_never_registers_a_write_route`).
- `hermes_client.py`(Docker SDK `exec_run`)가 Phase 0에서 확정한 방식 그대로
  구현되어 있다 — `-Q --source tool --resume` 조합, session_id/reasoning 잔여물
  파싱은 실전에서 2건의 실측 버그를 고쳐 회귀 테스트로 고정했다
  (`tests/test_hermes_client.py`).
- 테스트 42개 전부 통과(`cd webapp && pytest`).

⬜ 아직 사람이 직접 해야 하는 것: 브라우저로 직접 열어 시각적으로 확인(이
환경은 헤드리스라 브라우저 자동화 불가 — `docs/12-web-gui-demo.md` §8-9와 동일한
제약). **화면 5는 추가로 컨테이너 환경에서 실제 `coordinator` 채팅으로 예약
생성 → mock-pos 반영까지 curl/실채팅으로 검증하는 것도 남아있다**(화면 2가
2026-09-04에 받은 것과 동일한 수준의 실측).

## 쓰기 작업에 대한 원칙

브라우저 JS는 mock-pos의 쓰기(POST/PATCH) 엔드포인트를 직접 호출하지 않는다.
주문 생성·재고 재입고 같은 쓰기는 전부 `coordinator` 에이전트에게 위임되어
가격/재고 검증과 HITL 승인 게이트를 그대로 거친다(`docs/06-hitl-approval-design.md`).
`X-API-Key`도 서버(`pos_client.py`) 안에만 있고 브라우저에는 절대 노출되지 않는다 —
기존 `mock_pos/routers/dashboard.py` 데모 페이지가 브라우저 JS에 키를 하드코딩하는
문제를 반복하지 않는다.
