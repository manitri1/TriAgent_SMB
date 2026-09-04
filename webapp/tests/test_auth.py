def test_page_requires_auth(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 401


def test_page_accepts_correct_credentials(client, auth_headers):
    resp = client.get("/dashboard", headers=auth_headers)
    assert resp.status_code == 200


def test_wrong_password_rejected(client):
    import base64

    token = base64.b64encode(b"test-admin:wrong-password").decode()
    resp = client.get("/dashboard", headers={"Authorization": f"Basic {token}"})
    assert resp.status_code == 401


def test_api_pos_requires_auth(client):
    resp = client.get("/api/pos/inventory")
    assert resp.status_code == 401


def test_health_does_not_require_auth(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
