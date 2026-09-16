import httpx

from webapp_bff.main import app
from webapp_bff.pos_client import pos_client


def _fake_response(json_body, status_code=200):
    request = httpx.Request("POST", "http://mock-pos-test.invalid/")
    return httpx.Response(status_code=status_code, json=json_body, request=request)


def test_seed_mock_data_relays_mode_to_pos_client(client, auth_headers, monkeypatch):
    captured = {}

    def fake_post(path, json=None):
        captured["path"] = path
        captured["json"] = json
        return _fake_response(
            {"mode": "quick", "catalog_items": 12, "customers": 6, "orders": 23, "payments": 23, "days_simulated": 1}
        )

    monkeypatch.setattr(pos_client, "post", fake_post)

    resp = client.post("/api/admin/seed-mock-data", headers=auth_headers, json={"mode": "quick"})
    assert resp.status_code == 200
    assert resp.json()["orders"] == 23
    assert captured["path"] == "/admin/seed"
    assert captured["json"] == {"mode": "quick"}


def test_seed_mock_data_defaults_to_quick_mode(client, auth_headers, monkeypatch):
    captured = {}

    def fake_post(path, json=None):
        captured["json"] = json
        return _fake_response({"mode": "quick", "catalog_items": 12, "customers": 6, "orders": 23, "payments": 23, "days_simulated": 1})

    monkeypatch.setattr(pos_client, "post", fake_post)

    resp = client.post("/api/admin/seed-mock-data", headers=auth_headers, json={})
    assert resp.status_code == 200
    assert captured["json"] == {"mode": "quick"}


def test_seed_mock_data_rejects_unknown_mode(client, auth_headers):
    resp = client.post("/api/admin/seed-mock-data", headers=auth_headers, json={"mode": "bogus"})
    assert resp.status_code == 400


def test_seed_mock_data_propagates_upstream_error(client, auth_headers, monkeypatch):
    def fake_post(path, json=None):
        return _fake_response({"detail": "mode must be 'quick' or 'month'"}, status_code=400)

    monkeypatch.setattr(pos_client, "post", fake_post)

    resp = client.post("/api/admin/seed-mock-data", headers=auth_headers, json={"mode": "month"})
    assert resp.status_code == 400


def test_seed_mock_data_requires_auth(client):
    resp = client.post("/api/admin/seed-mock-data", json={"mode": "quick"})
    assert resp.status_code == 401


def test_admin_router_never_forwards_to_business_write_paths():
    """구조적 보증: /api/admin/* 아래 라우트는 전부 POST이며 mock-pos의 admin
    엔드포인트 하나만 호출해야 한다 — coordinator 위임을 우회해 mock-pos의
    주문/결제/재고 쓰기 엔드포인트를 직접 두드리는 새 라우트가 실수로 추가되지
    않도록 막는 것이 목적이다."""
    admin_paths = {
        getattr(route, "path", "") for route in app.routes if getattr(route, "path", "").startswith("/api/admin")
    }
    assert admin_paths == {"/api/admin/seed-mock-data"}
