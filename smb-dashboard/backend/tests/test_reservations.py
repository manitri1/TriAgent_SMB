import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app

AUTH = ("owner", "test-pass")
MOCK_POS_RESERVATIONS_URL = "http://mock-pos:8080/v1/stores/store_demo/reservations"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("DASHBOARD_BASIC_AUTH_USER", "owner")
    monkeypatch.setenv("DASHBOARD_BASIC_AUTH_PASSWORD", "test-pass")
    return TestClient(app)


def test_reservations_date_and_status_filters_passed_through(client, httpx_mock):
    """REQ-003/AC-003: both optional filters, when present, are forwarded
    verbatim to Mock POS."""
    httpx_mock.add_response(
        url=f"{MOCK_POS_RESERVATIONS_URL}?date=2026-08-29&status=BOOKED",
        json=[
            {
                "reservation_id": "r1",
                "customer_id": "c1",
                "datetime": "2026-08-29T10:00:00Z",
                "status": "BOOKED",
            }
        ],
    )
    resp = client.get("/api/reservations", auth=AUTH, params={"date": "2026-08-29", "status": "BOOKED"})
    assert resp.status_code == 200
    assert resp.json()[0]["reservation_id"] == "r1"


def test_reservations_no_filters_returns_full_list(client, httpx_mock):
    """Happy path with neither optional filter supplied."""
    httpx_mock.add_response(url=MOCK_POS_RESERVATIONS_URL, json=[])
    resp = client.get("/api/reservations", auth=AUTH)
    assert resp.status_code == 200
    assert resp.json() == []


def test_reservations_upstream_failure_returns_502(client, httpx_mock):
    """REQ-010/AC-010: an upstream connection failure is translated to a
    user-facing 502, not the raw Mock POS error."""
    httpx_mock.add_exception(httpx.ConnectError("boom"), url=MOCK_POS_RESERVATIONS_URL)
    resp = client.get("/api/reservations", auth=AUTH)
    assert resp.status_code == 502
