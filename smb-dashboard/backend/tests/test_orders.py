from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app

AUTH = ("owner", "test-pass")
MOCK_POS_ORDERS_URL = "http://mock-pos:8080/v1/stores/store_demo/orders"

TODAY = datetime.now(timezone.utc)
YESTERDAY = TODAY - timedelta(days=1)


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("DASHBOARD_BASIC_AUTH_USER", "owner")
    monkeypatch.setenv("DASHBOARD_BASIC_AUTH_PASSWORD", "test-pass")
    return TestClient(app)


def _order(order_id: str, status: str, created_at: datetime) -> dict:
    return {
        "order_id": order_id,
        "status": status,
        "line_items": [],
        "total_amount": 1000,
        "currency": "KRW",
        "created_at": created_at.isoformat().replace("+00:00", "Z"),
    }


def test_today_orders_no_filter_returns_only_today(client, httpx_mock):
    """Characterization test (REQ-001, pre-existing behavior): without a status
    param, only orders whose created_at date matches today's UTC date are
    returned - regardless of status."""
    httpx_mock.add_response(
        url=MOCK_POS_ORDERS_URL,
        json=[
            _order("order_1", "OPEN", TODAY),
            _order("order_2", "COMPLETED", YESTERDAY),
        ],
    )
    resp = client.get("/api/orders/today", auth=AUTH)
    assert resp.status_code == 200
    ids = [o["order_id"] for o in resp.json()]
    assert ids == ["order_1"]


def test_today_orders_status_filter_passed_through(client, httpx_mock):
    """AC-014: a valid status filter is forwarded to Mock POS and only
    matching today's orders are returned."""
    httpx_mock.add_response(
        url=f"{MOCK_POS_ORDERS_URL}?status=REFUNDED",
        json=[_order("order_3", "REFUNDED", TODAY)],
    )
    resp = client.get("/api/orders/today", auth=AUTH, params={"status": "REFUNDED"})
    assert resp.status_code == 200
    assert [o["order_id"] for o in resp.json()] == ["order_3"]


def test_today_orders_status_filter_empty_result_is_not_an_error(client, httpx_mock):
    """AC-015 (edge case): a status filter with zero matches returns an empty
    200 list, not an error."""
    httpx_mock.add_response(url=f"{MOCK_POS_ORDERS_URL}?status=CANCELED", json=[])
    resp = client.get("/api/orders/today", auth=AUTH, params={"status": "CANCELED"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_today_orders_no_filter_still_unchanged_after_filter_added(client, httpx_mock):
    """AC-017 (regression): omitting status still behaves exactly as before
    the filter was introduced - all of today's orders, any status."""
    httpx_mock.add_response(
        url=MOCK_POS_ORDERS_URL,
        json=[
            _order("order_1", "OPEN", TODAY),
            _order("order_4", "CANCELED", TODAY),
        ],
    )
    resp = client.get("/api/orders/today", auth=AUTH)
    assert resp.status_code == 200
    ids = {o["order_id"] for o in resp.json()}
    assert ids == {"order_1", "order_4"}


def test_today_orders_invalid_status_value_returns_422(client, httpx_mock):
    """AC-018 (edge case): an out-of-range status value is rejected by
    FastAPI's Literal validation before any upstream call is made."""
    resp = client.get("/api/orders/today", auth=AUTH, params={"status": "INVALID_VALUE"})
    assert resp.status_code == 422


def test_today_orders_upstream_failure_returns_502(client, httpx_mock):
    """AC-010 / REQ-010: an upstream connection failure is translated to a
    user-facing 502, not the raw Mock POS error."""
    httpx_mock.add_exception(httpx.ConnectError("boom"), url=MOCK_POS_ORDERS_URL)
    resp = client.get("/api/orders/today", auth=AUTH)
    assert resp.status_code == 502
