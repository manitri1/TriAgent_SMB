from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter

from app.mock_pos_client import list_orders

router = APIRouter(prefix="/api/orders", tags=["orders"])

# REQ-014: stricter than reservations.py's unconstrained Optional[str] — this
# is the first proxy router to validate the filter value itself (FastAPI
# rejects an out-of-range value with a 422, per AC-018).
OrderStatus = Literal["OPEN", "COMPLETED", "CANCELED", "REFUNDED"]


@router.get("/today")
async def get_today_orders(status: Optional[OrderStatus] = None):
    orders = await list_orders(status=status)
    today = datetime.now(timezone.utc).date()
    return [o for o in orders if _parse_date(o["created_at"]) == today]


def _parse_date(value: str):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
