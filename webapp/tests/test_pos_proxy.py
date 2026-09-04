import httpx

from webapp_bff.main import app
from webapp_bff.pos_client import pos_client


def _fake_response(json_body, status_code=200):
    request = httpx.Request("GET", "http://mock-pos-test.invalid/")
    return httpx.Response(status_code=status_code, json=json_body, request=request)


def test_inventory_passthrough(client, auth_headers, monkeypatch):
    captured = {}

    def fake_get(path, params=None):
        captured["path"] = path
        captured["params"] = params
        return _fake_response([{"item_id": "menu_americano", "stock_quantity": 0, "low_stock_threshold": 5}])

    monkeypatch.setattr(pos_client, "get", fake_get)

    resp = client.get("/api/pos/inventory", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()[0]["item_id"] == "menu_americano"
    assert captured["path"] == "/inventory"


def test_reports_sales_forwards_period_param(client, auth_headers, monkeypatch):
    captured = {}

    def fake_get(path, params=None):
        captured["path"] = path
        captured["params"] = params
        return _fake_response({"order_count": 2, "total_sales": 9000})

    monkeypatch.setattr(pos_client, "get", fake_get)

    resp = client.get("/api/pos/reports/sales?period=week", headers=auth_headers)
    assert resp.status_code == 200
    assert captured["path"] == "/reports/sales"
    assert captured["params"] == {"period": "week"}


def test_upstream_error_propagates_status(client, auth_headers, monkeypatch):
    def fake_get(path, params=None):
        return _fake_response({"detail": "Inventory record not found"}, status_code=404)

    monkeypatch.setattr(pos_client, "get", fake_get)

    resp = client.get("/api/pos/inventory/menu_unknown", headers=auth_headers)
    assert resp.status_code == 404


def test_pos_proxy_never_registers_a_write_route():
    """구조적 보증: /api/pos/* 아래에 GET 외의 메서드가 하나라도 있으면 실패한다."""
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", set()) or set()
        if path.startswith("/api/pos"):
            assert methods <= {"GET", "HEAD"}, f"쓰기 메서드가 등록됨: {path} {methods}"
