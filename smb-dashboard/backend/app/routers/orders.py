from datetime import datetime, timezone

from fastapi import APIRouter

from app.mock_pos_client import list_orders

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("/today")
async def get_today_orders():
    orders = await list_orders()
    today = datetime.now(timezone.utc).date()
    return [o for o in orders if _parse_date(o["created_at"]) == today]


def _parse_date(value: str):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
