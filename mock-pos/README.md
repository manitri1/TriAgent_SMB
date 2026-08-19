# Mock POS

`docs/05-skills-and-tools.md`에 정의된 REST 스펙을 구현한 FastAPI 기반 Mock POS 서버.
`.hermes/profiles/{order-payment-agent,inventory-agent,reservation-agent,
sales-analytics-agent}/`의 `code_execution` Skill이 이 서버를 호출해 주문/재고/예약/매출
기능을 수행한다(자세한 아키텍처는 `docs/02-architecture.md`, `docs/03-hermes-agent-integration.md`
참고). Hermes와 무관하게 이 디렉터리 자체만으로도 독립 실행·테스트가 가능하다.

## 로컬 실행

```bash
cd mock-pos
python -m venv .venv
. .venv/Scripts/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

# 테스트 실행
pytest

# 서버 실행
uvicorn mock_pos.main:app --reload --port 8080
```

## Docker 실행

```bash
cd mock-pos
docker build -t mock-pos .
docker run -p 8080:8080 -e MOCK_POS_API_KEY=dev-key mock-pos
```

`MOCK_POS_API_KEY`를 지정하지 않으면 `X-API-Key` 헤더 존재 여부만 검증한다 (로컬 개발용).

## 인증

모든 엔드포인트는 `X-API-Key` 헤더가 필요하다.

## 예시 흐름 (curl)

```bash
BASE=http://localhost:8080
KEY="dev-key"
STORE="store_cafe_001"

# 1. 메뉴 등록 (초기 재고 20개)
curl -s -X POST "$BASE/v1/stores/$STORE/catalog/items" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"item_id":"menu_americano","name":"아메리카노","unit_price":4500,"initial_stock":20}'

# 2. 주문 생성
curl -s -X POST "$BASE/v1/stores/$STORE/orders" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"line_items":[{"item_id":"menu_americano","quantity":2}]}'

# 3. 결제 생성 (order_id는 위 응답값 사용) -> 주문 COMPLETED, 재고 차감
curl -s -X POST "$BASE/v1/stores/$STORE/payments" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"order_id":"<order_id>"}'

# 4. 재고 확인
curl -s "$BASE/v1/stores/$STORE/inventory/menu_americano" -H "X-API-Key: $KEY"

# 5. 매출 요약
curl -s "$BASE/v1/stores/$STORE/reports/sales?period=today" -H "X-API-Key: $KEY"

# 6. 환불 (payment_id는 3번 응답값 사용) -> 결제/주문 REFUNDED, 재고 원상 복구
curl -s -X POST "$BASE/v1/stores/$STORE/payments/<payment_id>/refund" -H "X-API-Key: $KEY"

# 7. 예약 목록 조회 (날짜/상태로 필터 가능)
curl -s "$BASE/v1/stores/$STORE/reservations?status=BOOKED" -H "X-API-Key: $KEY"
```

인터랙티브 API 문서는 서버 실행 후 `http://localhost:8080/docs`에서 확인할 수 있다 (FastAPI 자동 생성).

## 데이터 저장

프로세스 메모리에만 저장되며(`mock_pos/store.py`), 재시작 시 초기화된다. 매장(store_id)별로 카탈로그/재고/주문/결제/예약이 격리된다. 현재 Hermes 프로필 구성은 매장 1곳(`STORE_ID`, 기본 `store_demo`)만 사용한다.

## 구현 범위와 docs/05-skills-and-tools.md의 차이

- 주문은 결제가 발생하는 시점(`POST /payments`)에 `COMPLETED`로 전환되며, 이때 재고가 차감된다 (Square의 "주문 완료 시 자동 재고 반영" 동작을 단순화해 반영).
- `PATCH /orders/{order_id}`로 직접 `COMPLETED`/`CANCELED` 전환도 가능하다.
- `POST /payments/{payment_id}/refund`로 환불 처리 — 결제/주문이 `REFUNDED`로 전환되고 재고가 원상 복구된다. 이미 `REFUNDED`인 결제나 주문이 `COMPLETED` 상태가 아니면 409를 반환한다. 매출(`/reports/sales`)에서는 `REFUNDED` 결제가 자동 제외되고, 정산(`/reports/settlement`)에는 `refunded_amount`/`refunded_count`로 별도 집계된다.
- `GET /reservations?date=&status=`로 매장의 예약 목록을 조회할 수 있다(둘 다 생략하면 전체).
- 인증은 초안 수준(API Key)이며, 실 POS 전환 시 벤더별 OAuth로 교체될 예정이다 (`docs/07-roadmap.md` 참고).
