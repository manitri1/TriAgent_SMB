import importlib
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("APPROVALS_DATA_FILE", str(tmp_path / "approvals.json"))
    monkeypatch.setenv("DASHBOARD_BASIC_AUTH_USER", "owner")
    monkeypatch.setenv("DASHBOARD_BASIC_AUTH_PASSWORD", "test-pass")

    from app import approvals_store

    importlib.reload(approvals_store)

    from app import main

    importlib.reload(main)

    return TestClient(main.app)


AUTH = ("owner", "test-pass")


def test_health_requires_no_auth(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_approvals_require_auth(client):
    resp = client.get("/api/approvals")
    assert resp.status_code == 401


def test_create_list_and_decide_approval(client):
    resp = client.post(
        "/api/approvals",
        auth=AUTH,
        json={
            "type": "reorder",
            "summary": "원두 500개 재입고",
            "details": "예상 350만원",
            "requested_by": "inventory-agent",
        },
    )
    assert resp.status_code == 201
    approval = resp.json()
    assert approval["status"] == "pending"

    resp = client.get("/api/approvals", auth=AUTH, params={"status": "pending"})
    assert resp.status_code == 200
    assert any(a["approval_id"] == approval["approval_id"] for a in resp.json())

    resp = client.patch(
        f"/api/approvals/{approval['approval_id']}",
        auth=AUTH,
        json={"status": "approved", "reason": "예산 승인"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


def test_double_decision_rejected_with_409(client):
    resp = client.post(
        "/api/approvals",
        auth=AUTH,
        json={"type": "refund", "summary": "환불 요청", "details": "상세", "requested_by": "order-payment-agent"},
    )
    approval_id = resp.json()["approval_id"]

    resp = client.patch(f"/api/approvals/{approval_id}", auth=AUTH, json={"status": "approved"})
    assert resp.status_code == 200

    resp = client.patch(f"/api/approvals/{approval_id}", auth=AUTH, json={"status": "rejected"})
    assert resp.status_code == 409


def test_decide_unknown_approval_returns_404(client):
    resp = client.patch("/api/approvals/appr_unknown", auth=AUTH, json={"status": "approved"})
    assert resp.status_code == 404
