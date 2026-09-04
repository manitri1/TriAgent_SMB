from fastapi.testclient import TestClient

from mock_pos.main import app

client = TestClient(app)
HEADERS = {"X-API-Key": "test-key"}
STORE = "store_test_customers"


def _completed_order_for(customer_id: str, item_id: str, unit_price: int):
    client.post(
        f"/v1/stores/{STORE}/catalog/items",
        headers=HEADERS,
        json={"item_id": item_id, "name": item_id, "unit_price": unit_price, "initial_stock": 50},
    )
    order = client.post(
        f"/v1/stores/{STORE}/orders",
        headers=HEADERS,
        json={"line_items": [{"item_id": item_id, "quantity": 1}], "customer_id": customer_id},
    ).json()
    client.post(f"/v1/stores/{STORE}/payments", headers=HEADERS, json={"order_id": order["order_id"]})
    return order


def test_register_customer_round_trip():
    resp = client.post(
        f"/v1/stores/{STORE}/customers",
        headers=HEADERS,
        json={"customer_id": "cust_reg_1", "name": "김철수", "phone": "010-0000-0000"},
    )
    assert resp.status_code == 201
    customer = resp.json()
    assert customer["name"] == "김철수"
    assert customer["order_count"] == 0

    resp = client.get(f"/v1/stores/{STORE}/customers/cust_reg_1", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["phone"] == "010-0000-0000"

    resp = client.post(
        f"/v1/stores/{STORE}/customers",
        headers=HEADERS,
        json={"customer_id": "cust_reg_1", "name": "김철수(수정)"},
    )
    assert resp.status_code == 200  # 이미 존재 -> upsert


def test_unregistered_customer_with_orders_still_queryable():
    _completed_order_for("cust_walkin_1", "menu_cust_walkin_item", 4000)

    resp = client.get(f"/v1/stores/{STORE}/customers/cust_walkin_1", headers=HEADERS)
    assert resp.status_code == 200
    customer = resp.json()
    assert customer["name"] is None
    assert customer["order_count"] == 1
    assert customer["total_spent"] == 4000


def test_unknown_customer_without_orders_returns_404():
    resp = client.get(f"/v1/stores/{STORE}/customers/cust_never_existed", headers=HEADERS)
    assert resp.status_code == 404


def test_repeat_customers_filters_by_min_orders():
    _completed_order_for("cust_repeat_1", "menu_cust_repeat_a", 3000)
    _completed_order_for("cust_repeat_1", "menu_cust_repeat_b", 3000)
    _completed_order_for("cust_repeat_2", "menu_cust_repeat_c", 5000)  # only 1 order

    resp = client.get(
        f"/v1/stores/{STORE}/reports/repeat-customers",
        headers=HEADERS,
        params={"period": "all", "min_orders": 2},
    )
    assert resp.status_code == 200
    ids = {c["customer_id"] for c in resp.json()}
    assert "cust_repeat_1" in ids
    assert "cust_repeat_2" not in ids


def test_list_orders_filters_by_customer_id():
    order = _completed_order_for("cust_filter_1", "menu_cust_filter_item", 2000)

    resp = client.get(
        f"/v1/stores/{STORE}/orders", headers=HEADERS, params={"customer_id": "cust_filter_1"}
    )
    assert resp.status_code == 200
    ids = {o["order_id"] for o in resp.json()}
    assert order["order_id"] in ids

    resp = client.get(
        f"/v1/stores/{STORE}/orders", headers=HEADERS, params={"customer_id": "cust_no_such_customer"}
    )
    assert resp.json() == []
