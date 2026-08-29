import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app

AUTH = ("owner", "test-pass")
MOCK_POS_INVENTORY_URL = "http://mock-pos:8080/v1/stores/store_demo/inventory"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("DASHBOARD_BASIC_AUTH_USER", "owner")
    monkeypatch.setenv("DASHBOARD_BASIC_AUTH_PASSWORD", "test-pass")
    return TestClient(app)


def test_inventory_low_stock_flag_computed_from_threshold(client, httpx_mock, monkeypatch):
    """REQ-002/AC-002: an item below LOW_STOCK_THRESHOLD is annotated
    low_stock=true; an item at/above it is low_stock=false."""
    monkeypatch.setenv("LOW_STOCK_THRESHOLD", "10")
    httpx_mock.add_response(
        url=MOCK_POS_INVENTORY_URL,
        json=[
            {"item_id": "item_a", "stock_quantity": 3, "updated_at": "2026-08-29T00:00:00Z"},
            {"item_id": "item_b", "stock_quantity": 50, "updated_at": "2026-08-29T00:00:00Z"},
        ],
    )
    resp = client.get("/api/inventory", auth=AUTH)
    assert resp.status_code == 200
    body = {item["item_id"]: item for item in resp.json()}
    assert body["item_a"]["low_stock"] is True
    assert body["item_b"]["low_stock"] is False


def test_inventory_upstream_failure_returns_502(client, httpx_mock):
    """REQ-010/AC-010: an upstream connection failure is translated to a
    user-facing 502, not the raw Mock POS error."""
    httpx_mock.add_exception(httpx.ConnectError("boom"), url=MOCK_POS_INVENTORY_URL)
    resp = client.get("/api/inventory", auth=AUTH)
    assert resp.status_code == 502
