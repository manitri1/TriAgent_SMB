from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


ApprovalType = Literal["promo", "reorder", "refund"]
ApprovalStatus = Literal["pending", "approved", "rejected"]


class ApprovalCreate(BaseModel):
    type: ApprovalType
    summary: str
    details: str
    requested_by: str


class ApprovalDecision(BaseModel):
    status: Literal["approved", "rejected"]
    reason: Optional[str] = None


class Approval(BaseModel):
    approval_id: str
    type: ApprovalType
    summary: str
    details: str
    requested_by: str
    status: ApprovalStatus = "pending"
    reason: Optional[str] = None
    decided_by: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    decided_at: Optional[datetime] = None
