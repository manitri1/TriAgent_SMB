from fastapi.testclient import TestClient

from mock_pos.main import app

client = TestClient(app)
HEADERS = {"X-API-Key": "test-key"}
STORE = "store_test_partial_refund"


def _seed_completed_order(item_id: str, unit_price: int, quantity: int, initial_stock: int = 20):
    client.post(
        f"/v1/stores/{STORE}/catalog/items",
        headers=HEADERS,
        json={"item_id": item_id, "name": item_id, "unit_price": unit_price, "initial_stock": initial_stock},
    )
    order = client.post(
        f"/v1/stores/{STORE}/orders",
        headers=HEADERS,
        json={"line_items": [{"item_id": item_id, "quantity": quantity}]},
    ).json()
    payment = client.post(
        f"/v1/stores/{STORE}/payments", headers=HEADERS, json={"order_id": order["order_id"]}
    ).json()
    return order, payment


def test_partial_refund_keeps_inventory_unchanged():
    order, payment = _seed_completed_order("menu_pr_bagel", 6000, 1)

    resp = client.post(
        f"/v1/stores/{STORE}/payments/{payment['payment_id']}/refund",
        headers=HEADERS,
        json={"amount": 2000, "reason": "품질 이슈"},
    )
    assert resp.status_code == 200
    refunded = resp.json()
    assert refunded["status"] == "PARTIALLY_REFUNDED"
    assert refunded["refunded_amount"] == 2000

    order_after = client.get(f"/v1/stores/{STORE}/orders/{order['order_id']}", headers=HEADERS).json()
    assert order_after["status"] == "PARTIALLY_REFUNDED"

    inv = client.get(f"/v1/stores/{STORE}/inventory/menu_pr_bagel", headers=HEADERS).json()
    assert inv["stock_quantity"] == 19  # 재고는 복구되지 않음


def test_second_refund_settles_remaining_balance_and_restores_inventory():
    order, payment = _seed_completed_order("menu_pr_croissant", 5000, 1)

    client.post(
        f"/v1/stores/{STORE}/payments/{payment['payment_id']}/refund",
        headers=HEADERS,
        json={"amount": 2000},
    )
    resp = client.post(
        f"/v1/stores/{STORE}/payments/{payment['payment_id']}/refund",
        headers=HEADERS,
        json={"amount": 3000},
    )
    assert resp.status_code == 200
    refunded = resp.json()
    assert refunded["status"] == "REFUNDED"
    assert refunded["refunded_amount"] == 5000

    order_after = client.get(f"/v1/stores/{STORE}/orders/{order['order_id']}", headers=HEADERS).json()
    assert order_after["status"] == "REFUNDED"

    inv = client.get(f"/v1/stores/{STORE}/inventory/menu_pr_croissant", headers=HEADERS).json()
    assert inv["stock_quantity"] == 20  # 전액 환불 완료 시 재고 복구


def test_refund_amount_exceeding_remaining_balance_rejected():
    _, payment = _seed_completed_order("menu_pr_muffin", 4000, 1)

    resp = client.post(
        f"/v1/stores/{STORE}/payments/{payment['payment_id']}/refund",
        headers=HEADERS,
        json={"amount": 5000},
    )
    assert resp.status_code == 400


def test_refund_already_fully_refunded_payment_rejected():
    _, payment = _seed_completed_order("menu_pr_tea", 3000, 1)

    resp = client.post(f"/v1/stores/{STORE}/payments/{payment['payment_id']}/refund", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "REFUNDED"

    resp = client.post(f"/v1/stores/{STORE}/payments/{payment['payment_id']}/refund", headers=HEADERS)
    assert resp.status_code == 409


def test_reports_reflect_net_amount_after_partial_refund():
    _, payment = _seed_completed_order("menu_pr_sandwich", 8000, 1)

    resp_before = client.get(
        f"/v1/stores/{STORE}/reports/sales", headers=HEADERS, params={"period": "all"}
    )
    before = resp_before.json()["total_sales"]

    client.post(
        f"/v1/stores/{STORE}/payments/{payment['payment_id']}/refund",
        headers=HEADERS,
        json={"amount": 3000},
    )

    resp_after = client.get(
        f"/v1/stores/{STORE}/reports/sales", headers=HEADERS, params={"period": "all"}
    )
    after = resp_after.json()["total_sales"]
    assert after == before - 3000

    settlement = client.get(
        f"/v1/stores/{STORE}/reports/settlement", headers=HEADERS, params={"period": "all"}
    ).json()
    assert settlement["partial_refund_amount"] >= 3000
    assert settlement["partial_refund_count"] >= 1
