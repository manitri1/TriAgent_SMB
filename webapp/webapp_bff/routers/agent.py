"""에이전트 릴레이 엔드포인트.

브라우저는 여기로만 메시지를 보내고, 실제 hermes CLI 호출은 hermes_client.py가
담당한다. 화면이 어떤 profile을 요청하든 화이트리스트 밖이면 coordinator로
강제한다 — 이건 방어적 기본값이 아니라 설계 원칙이다: order-payment-agent/
inventory-agent는 승인을 요청할 수단(clarify/messaging 툴)이 없어 직접 호출하면
HITL이 조용히 무력화된다(curried-percolating-ocean.md "설계 편차" 참고). 쓰기가
필요한 화면(주문 접수, 재고 재입고)은 전부 coordinator로 수렴해야 한다.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from webapp_bff.auth import require_auth
from webapp_bff.conversation_store import conversation_store
from webapp_bff.hermes_client import agent_client

router = APIRouter(prefix="/api/agent", tags=["agent"], dependencies=[Depends(require_auth)])

_ALLOWED_PROFILES = {"customer-service-agent", "coordinator"}
_DEFAULT_PROFILE = "coordinator"


class MessageIn(BaseModel):
    profile: str
    message: str
    conversation_id: str


class MessageOut(BaseModel):
    status: str
    text: str
    conversation_id: str


@router.post("/message", response_model=MessageOut)
async def send_message(payload: MessageIn) -> MessageOut:
    profile = payload.profile if payload.profile in _ALLOWED_PROFILES else _DEFAULT_PROFILE
    session_id = conversation_store.get_session_id(payload.conversation_id)

    reply = await agent_client.send(profile, payload.message, session_id)

    if reply.session_id:
        conversation_store.set_session_id(payload.conversation_id, reply.session_id)

    return MessageOut(status=reply.status, text=reply.text, conversation_id=payload.conversation_id)
