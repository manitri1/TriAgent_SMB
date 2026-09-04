from fastapi.testclient import TestClient

from mock_pos.main import app

client = TestClient(app)
HEADERS = {"X-API-Key": "test-key"}
STORE = "store_test_margin"


def test_margin_computed_from_cost():
    client.post(
        f"/v1/stores/{STORE}/catalog/items",
        headers=HEADERS,
        json={
            "item_id": "menu_margin_americano",
            "name": "아메리카노",
            "unit_price": 3500,
            "cost": 800,
            "initial_stock": 10,
        },
    )
    order = client.post(
        f"/v1/stores/{STORE}/orders",
        headers=HEADERS,
        json={"line_items": [{"item_id": "menu_margin_americano", "quantity": 1}]},
    ).json()
    client.post(
        f"/v1/stores/{STORE}/payments", headers=HEADERS, json={"order_id": order["order_id"]}
    )

    resp = client.get(f"/v1/stores/{STORE}/reports/margin", headers=HEADERS, params={"period": "all"})
    assert resp.status_code == 200
    margin = resp.json()
    assert margin["total_revenue"] == 3500
    assert margin["total_cost"] == 800
    assert margin["gross_margin"] == 2700
    assert abs(margin["margin_rate"] - (2700 / 3500)) < 1e-6


def test_margin_defaults_to_zero_cost_when_unregistered():
    client.post(
        f"/v1/stores/{STORE}/catalog/items",
        headers=HEADERS,
        json={"item_id": "menu_margin_nocatalogcost", "name": "무원가메뉴", "unit_price": 2000, "initial_stock": 5},
    )
    order = client.post(
        f"/v1/stores/{STORE}/orders",
        headers=HEADERS,
        json={"line_items": [{"item_id": "menu_margin_nocatalogcost", "quantity": 1}]},
    ).json()
    client.post(
        f"/v1/stores/{STORE}/payments", headers=HEADERS, json={"order_id": order["order_id"]}
    )

    resp = client.get(f"/v1/stores/{STORE}/reports/margin", headers=HEADERS, params={"period": "all"})
    margin = resp.json()
    assert margin["total_cost"] >= 0


def test_top_items_includes_cost_and_margin():
    client.post(
        f"/v1/stores/{STORE}/catalog/items",
        headers=HEADERS,
        json={
            "item_id": "menu_margin_latte",
            "name": "라떼",
            "unit_price": 5000,
            "cost": 1500,
            "initial_stock": 10,
        },
    )
    order = client.post(
        f"/v1/stores/{STORE}/orders",
        headers=HEADERS,
        json={"line_items": [{"item_id": "menu_margin_latte", "quantity": 2}]},
    ).json()
    client.post(
        f"/v1/stores/{STORE}/payments", headers=HEADERS, json={"order_id": order["order_id"]}
    )

    resp = client.get(
        f"/v1/stores/{STORE}/reports/top-items", headers=HEADERS, params={"period": "all", "limit": 10}
    )
    items = resp.json()
    latte = next(i for i in items if i["item_id"] == "menu_margin_latte")
    assert latte["cost"] == 3000  # 1500 * 2
    assert latte["margin"] == 7000  # 10000 - 3000
