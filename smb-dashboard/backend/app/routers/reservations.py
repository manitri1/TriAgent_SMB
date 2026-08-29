from typing import Optional

from fastapi import APIRouter

from app.mock_pos_client import list_reservations

router = APIRouter(prefix="/api/reservations", tags=["reservations"])


@router.get("")
async def get_reservations(date: Optional[str] = None, status: Optional[str] = None):
    return await list_reservations(date=date, status=status)
