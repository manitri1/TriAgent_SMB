import os

from fastapi import APIRouter

from app.mock_pos_client import list_inventory

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("")
async def get_inventory():
    threshold = int(os.environ.get("LOW_STOCK_THRESHOLD", "10"))
    items = await list_inventory()
    return [{**item, "low_stock": item["stock_quantity"] < threshold} for item in items]
