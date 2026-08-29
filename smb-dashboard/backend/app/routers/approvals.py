from typing import Optional

from fastapi import APIRouter, HTTPException

from app import approvals_store
from app.models import ApprovalCreate, ApprovalDecision

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.post("", status_code=201)
def create_approval(payload: ApprovalCreate):
    return approvals_store.create_approval(payload.model_dump())


@router.get("")
def list_approvals(status: Optional[str] = None):
    return approvals_store.list_approvals(status=status)


@router.get("/{approval_id}")
def get_approval(approval_id: str):
    record = approvals_store.get_approval(approval_id)
    if not record:
        raise HTTPException(status_code=404, detail="Approval not found")
    return record


@router.patch("/{approval_id}")
def decide_approval(approval_id: str, payload: ApprovalDecision):
    try:
        return approvals_store.decide_approval(approval_id, payload.status, payload.reason)
    except approvals_store.ApprovalNotFoundError:
        raise HTTPException(status_code=404, detail="Approval not found")
    except approvals_store.AlreadyDecidedError:
        raise HTTPException(status_code=409, detail="Approval already decided")
