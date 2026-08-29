from fastapi import APIRouter

from app.mock_pos_client import sales_summary

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/sales")
async def get_sales_summary(period: str = "today"):
    return await sales_summary(period=period)
