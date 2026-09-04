from fastapi.testclient import TestClient

from mock_pos.main import app

client = TestClient(app)
HEADERS = {"X-API-Key": "test-key"}
STORE = "store_test_dashboard"


def _seed_order(item_id: str, name: str, unit_price: int, quantity: int, initial_stock: int = 20):
    client.post(
        f"/v1/stores/{STORE}/catalog/items",
        headers=HEADERS,
        json={"item_id": item_id, "name": name, "unit_price": unit_price, "initial_stock": initial_stock},
    )
    resp = client.post(
        f"/v1/stores/{STORE}/orders",
        headers=HEADERS,
        json={"line_items": [{"item_id": item_id, "quantity": quantity}]},
    )
    order = resp.json()
    resp = client.post(
        f"/v1/stores/{STORE}/payments",
        headers=HEADERS,
        json={"order_id": order["order_id"]},
    )
    return order, resp.json()


def test_dashboard_page_returns_html_with_markers():
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "실적 대시보드" in resp.text
    assert "chart.js" in resp.text.lower()


def test_list_orders_returns_all_and_filters_by_status():
    order, _ = _seed_order("menu_dashboard_espresso", "에스프레소", 3000, 1)

    resp = client.get(f"/v1/stores/{STORE}/orders", headers=HEADERS)
    assert resp.status_code == 200
    ids = {o["order_id"] for o in resp.json()}
    assert order["order_id"] in ids

    resp = client.get(f"/v1/stores/{STORE}/orders", headers=HEADERS, params={"status": "COMPLETED"})
    assert resp.status_code == 200
    assert all(o["status"] == "COMPLETED" for o in resp.json())

    resp = client.get(f"/v1/stores/{STORE}/orders", headers=HEADERS, params={"status": "CANCELED"})
    assert resp.json() == []


def test_top_items_ranks_by_revenue():
    _seed_order("menu_dashboard_latte", "라떼", 5000, 3)  # revenue 15000
    _seed_order("menu_dashboard_tea", "홍차", 4000, 1)  # revenue 4000

    resp = client.get(
        f"/v1/stores/{STORE}/reports/top-items", headers=HEADERS, params={"period": "all", "limit": 5}
    )
    assert resp.status_code == 200
    items = resp.json()
    names = [i["name"] for i in items]
    assert "라떼" in names
    assert items[0]["revenue"] >= items[-1]["revenue"]
    latte = next(i for i in items if i["item_id"] == "menu_dashboard_latte")
    assert latte["quantity"] == 3
    assert latte["revenue"] == 15000


def test_daily_sales_includes_today_bucket():
    _seed_order("menu_dashboard_croissant", "크루아상", 3500, 2)

    resp = client.get(f"/v1/stores/{STORE}/reports/sales/daily", headers=HEADERS, params={"days": 7})
    assert resp.status_code == 200
    days = resp.json()
    assert len(days) == 7

    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).date().isoformat()
    today_bucket = next(d for d in days if d["date"] == today)
    assert today_bucket["total_sales"] >= 7000


def test_inventory_reports_low_stock_threshold():
    client.post(
        f"/v1/stores/{STORE}/catalog/items",
        headers=HEADERS,
        json={
            "item_id": "menu_dashboard_bagel",
            "name": "베이글",
            "unit_price": 3000,
            "initial_stock": 2,
            "low_stock_threshold": 5,
        },
    )
    resp = client.get(f"/v1/stores/{STORE}/inventory/menu_dashboard_bagel", headers=HEADERS)
    assert resp.status_code == 200
    record = resp.json()
    assert record["low_stock_threshold"] == 5
    assert record["stock_quantity"] < record["low_stock_threshold"]
