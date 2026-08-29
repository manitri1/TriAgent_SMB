import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app

AUTH = ("owner", "test-pass")
MOCK_POS_SALES_URL = "http://mock-pos:8080/v1/stores/store_demo/reports/sales"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("DASHBOARD_BASIC_AUTH_USER", "owner")
    monkeypatch.setenv("DASHBOARD_BASIC_AUTH_PASSWORD", "test-pass")
    return TestClient(app)


def test_sales_summary_defaults_to_today_period(client, httpx_mock):
    """REQ-004: omitting period defaults to 'today'."""
    httpx_mock.add_response(
        url=f"{MOCK_POS_SALES_URL}?period=today",
        json={"period": "today", "order_count": 5, "total_sales": 50000, "currency": "KRW"},
    )
    resp = client.get("/api/reports/sales", auth=AUTH)
    assert resp.status_code == 200
    assert resp.json()["period"] == "today"


def test_sales_summary_period_param_passed_through(client, httpx_mock):
    """REQ-004/AC-004: an explicit period overrides the 'today' default."""
    httpx_mock.add_response(
        url=f"{MOCK_POS_SALES_URL}?period=week",
        json={"period": "week", "order_count": 20, "total_sales": 200000, "currency": "KRW"},
    )
    resp = client.get("/api/reports/sales", auth=AUTH, params={"period": "week"})
    assert resp.status_code == 200
    assert resp.json()["period"] == "week"


def test_sales_summary_upstream_failure_returns_502(client, httpx_mock):
    """REQ-010/AC-010: an upstream connection failure is translated to a
    user-facing 502, not the raw Mock POS error."""
    httpx_mock.add_exception(httpx.ConnectError("boom"), url=f"{MOCK_POS_SALES_URL}?period=today")
    resp = client.get("/api/reports/sales", auth=AUTH)
    assert resp.status_code == 502
