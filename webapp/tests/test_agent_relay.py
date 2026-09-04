"""POST /api/agent/message 릴레이 테스트.

실제 docker exec는 절대 수행하지 않는다 — hermes_client.agent_client.send를
목(mock) 처리해 라우팅/화이트리스트/상태 전달 로직만 검증한다.
"""
from webapp_bff.hermes_client import AgentReply
from webapp_bff.routers import agent as agent_router


def test_message_requires_auth(client):
    resp = client.post(
        "/api/agent/message", json={"profile": "coordinator", "message": "hi", "conversation_id": "c1"}
    )
    assert resp.status_code == 401


def test_happy_path_returns_agent_reply(client, auth_headers, monkeypatch):
    async def fake_send(profile, message, session_id=None):
        assert profile == "customer-service-agent"
        assert session_id is None
        return AgentReply(status="ok", text="영업시간은 09:00~21:00입니다.", session_id="sess-1")

    monkeypatch.setattr(agent_router.agent_client, "send", fake_send)

    resp = client.post(
        "/api/agent/message",
        headers=auth_headers,
        json={"profile": "customer-service-agent", "message": "영업시간?", "conversation_id": "conv-1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "09:00" in body["text"]


def test_second_call_reuses_stored_session_id(client, auth_headers, monkeypatch):
    calls = []

    async def fake_send(profile, message, session_id=None):
        calls.append(session_id)
        return AgentReply(status="ok", text="답변", session_id="sess-42")

    monkeypatch.setattr(agent_router.agent_client, "send", fake_send)

    client.post(
        "/api/agent/message",
        headers=auth_headers,
        json={"profile": "coordinator", "message": "첫 메시지", "conversation_id": "conv-2"},
    )
    client.post(
        "/api/agent/message",
        headers=auth_headers,
        json={"profile": "coordinator", "message": "두번째 메시지", "conversation_id": "conv-2"},
    )
    assert calls == [None, "sess-42"]


def test_unknown_profile_falls_back_to_coordinator(client, auth_headers, monkeypatch):
    seen = {}

    async def fake_send(profile, message, session_id=None):
        seen["profile"] = profile
        return AgentReply(status="ok", text="답변", session_id=None)

    monkeypatch.setattr(agent_router.agent_client, "send", fake_send)

    client.post(
        "/api/agent/message",
        headers=auth_headers,
        json={"profile": "order-payment-agent", "message": "환불해줘", "conversation_id": "conv-3"},
    )
    assert seen["profile"] == "coordinator"


def test_timeout_status_is_relayed_as_is(client, auth_headers, monkeypatch):
    async def fake_send(profile, message, session_id=None):
        return AgentReply(status="timeout", text="아직 처리 중일 수 있습니다.", session_id=None)

    monkeypatch.setattr(agent_router.agent_client, "send", fake_send)

    resp = client.post(
        "/api/agent/message",
        headers=auth_headers,
        json={"profile": "coordinator", "message": "주문", "conversation_id": "conv-4"},
    )
    assert resp.json()["status"] == "timeout"
