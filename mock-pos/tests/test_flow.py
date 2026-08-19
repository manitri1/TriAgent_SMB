from fastapi.testclient import TestClient

from mock_pos.main import app

client = TestClient(app)
HEADERS = {"X-API-Key": "test-key"}
STORE = "store_test_cafe"


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_requires_api_key():
    resp = client.get(f"/v1/stores/{STORE}/catalog/items")
    assert resp.status_code == 401


def test_end_to_end_order_flow():
    # 1. 카탈로그 등록 (초기 재고 10개)
    resp = client.post(
        f"/v1/stores/{STORE}/catalog/items",
        headers=HEADERS,
        json={"item_id": "menu_americano", "name": "아메리카노", "unit_price": 4500, "initial_stock": 10},
    )
    assert resp.status_code == 201

    # 2. 재고 확인
    resp = client.get(f"/v1/stores/{STORE}/inventory/menu_americano", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["stock_quantity"] == 10

    # 3. 주문 생성 (재고는 아직 차감되지 않음)
    resp = client.post(
        f"/v1/stores/{STORE}/orders",
        headers=HEADERS,
        json={"line_items": [{"item_id": "menu_americano", "quantity": 2}]},
    )
    assert resp.status_code == 201
    order = resp.json()
    assert order["status"] == "OPEN"
    assert order["total_amount"] == 9000

    resp = client.get(f"/v1/stores/{STORE}/inventory/menu_americano", headers=HEADERS)
    assert resp.json()["stock_quantity"] == 10

    # 4. 결제 생성 -> 주문 COMPLETED 전환 + 재고 차감
    resp = client.post(
        f"/v1/stores/{STORE}/payments",
        headers=HEADERS,
        json={"order_id": order["order_id"]},
    )
    assert resp.status_code == 201
    payment = resp.json()
    assert payment["amount"] == 9000
    assert payment["status"] == "COMPLETED"

    resp = client.get(f"/v1/stores/{STORE}/orders/{order['order_id']}", headers=HEADERS)
    assert resp.json()["status"] == "COMPLETED"

    resp = client.get(f"/v1/stores/{STORE}/inventory/menu_americano", headers=HEADERS)
    assert resp.json()["stock_quantity"] == 8

    # 5. 매출 리포트에 반영
    resp = client.get(f"/v1/stores/{STORE}/reports/sales", headers=HEADERS, params={"period": "today"})
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["order_count"] == 1
    assert summary["total_sales"] == 9000


def test_insufficient_stock_rejected():
    resp = client.post(
        f"/v1/stores/{STORE}/catalog/items",
        headers=HEADERS,
        json={"item_id": "menu_latte", "name": "라떼", "unit_price": 5000, "initial_stock": 1},
    )
    assert resp.status_code == 201

    resp = client.post(
        f"/v1/stores/{STORE}/orders",
        headers=HEADERS,
        json={"line_items": [{"item_id": "menu_latte", "quantity": 5}]},
    )
    order = resp.json()

    resp = client.post(
        f"/v1/stores/{STORE}/payments",
        headers=HEADERS,
        json={"order_id": order["order_id"]},
    )
    assert resp.status_code == 409


def test_refund_restores_inventory_and_marks_order_refunded():
    resp = client.post(
        f"/v1/stores/{STORE}/catalog/items",
        headers=HEADERS,
        json={"item_id": "menu_croissant", "name": "크루아상", "unit_price": 3500, "initial_stock": 5},
    )
    assert resp.status_code == 201

    resp = client.post(
        f"/v1/stores/{STORE}/orders",
        headers=HEADERS,
        json={"line_items": [{"item_id": "menu_croissant", "quantity": 2}]},
    )
    order = resp.json()

    resp = client.post(
        f"/v1/stores/{STORE}/payments",
        headers=HEADERS,
        json={"order_id": order["order_id"]},
    )
    payment = resp.json()
    assert payment["status"] == "COMPLETED"

    resp = client.get(f"/v1/stores/{STORE}/inventory/menu_croissant", headers=HEADERS)
    assert resp.json()["stock_quantity"] == 3  # 5 - 2

    resp = client.post(f"/v1/stores/{STORE}/payments/{payment['payment_id']}/refund", headers=HEADERS)
    assert resp.status_code == 200
    refunded = resp.json()
    assert refunded["status"] == "REFUNDED"
    assert refunded["refunded_at"] is not None

    resp = client.get(f"/v1/stores/{STORE}/orders/{order['order_id']}", headers=HEADERS)
    assert resp.json()["status"] == "REFUNDED"

    resp = client.get(f"/v1/stores/{STORE}/inventory/menu_croissant", headers=HEADERS)
    assert resp.json()["stock_quantity"] == 5  # 재고 복구됨

    # 이미 환불된 결제를 다시 환불하면 거부
    resp = client.post(f"/v1/stores/{STORE}/payments/{payment['payment_id']}/refund", headers=HEADERS)
    assert resp.status_code == 409


def test_refunded_payment_excluded_from_sales_but_shown_in_settlement():
    resp = client.post(
        f"/v1/stores/{STORE}/catalog/items",
        headers=HEADERS,
        json={"item_id": "menu_bagel", "name": "베이글", "unit_price": 3000, "initial_stock": 5},
    )
    assert resp.status_code == 201

    resp = client.post(
        f"/v1/stores/{STORE}/orders",
        headers=HEADERS,
        json={"line_items": [{"item_id": "menu_bagel", "quantity": 1}]},
    )
    order = resp.json()

    resp = client.post(
        f"/v1/stores/{STORE}/payments", headers=HEADERS, json={"order_id": order["order_id"]}
    )
    payment = resp.json()

    resp_before = client.get(f"/v1/stores/{STORE}/reports/sales", headers=HEADERS, params={"period": "all"})
    sales_before = resp_before.json()["total_sales"]

    resp = client.post(f"/v1/stores/{STORE}/payments/{payment['payment_id']}/refund", headers=HEADERS)
    assert resp.status_code == 200

    resp_after = client.get(f"/v1/stores/{STORE}/reports/sales", headers=HEADERS, params={"period": "all"})
    sales_after = resp_after.json()["total_sales"]
    assert sales_after == sales_before - 3000  # 환불된 3000원은 매출에서 빠져야 함

    resp = client.get(f"/v1/stores/{STORE}/reports/settlement", headers=HEADERS, params={"period": "all"})
    settlement = resp.json()
    assert settlement["refunded_amount"] >= 3000
    assert settlement["refunded_count"] >= 1


def test_list_reservations_filters_by_status():
    resp = client.post(
        f"/v1/stores/{STORE}/reservations",
        headers=HEADERS,
        json={"customer_id": "cust_1", "datetime": "2026-08-20T14:00:00+09:00", "service": "컷트"},
    )
    resv1 = resp.json()

    resp = client.post(
        f"/v1/stores/{STORE}/reservations",
        headers=HEADERS,
        json={"customer_id": "cust_2", "datetime": "2026-08-21T10:00:00+09:00", "service": "펌"},
    )
    resv2 = resp.json()

    resp = client.patch(
        f"/v1/stores/{STORE}/reservations/{resv2['reservation_id']}",
        headers=HEADERS,
        json={"status": "CANCELED"},
    )
    assert resp.status_code == 200

    resp = client.get(f"/v1/stores/{STORE}/reservations", headers=HEADERS, params={"status": "BOOKED"})
    assert resp.status_code == 200
    ids = {r["reservation_id"] for r in resp.json()}
    assert resv1["reservation_id"] in ids
    assert resv2["reservation_id"] not in ids

    resp = client.get(f"/v1/stores/{STORE}/reservations", headers=HEADERS, params={"date": "2026-08-20"})
    ids = {r["reservation_id"] for r in resp.json()}
    assert ids == {resv1["reservation_id"]}
