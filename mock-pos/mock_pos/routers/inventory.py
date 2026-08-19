from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from mock_pos.auth import verify_api_key
from mock_pos.models import InventoryAdjust, InventoryItem
from mock_pos.store import store

router = APIRouter(
    prefix="/v1/stores/{store_id}/inventory",
    tags=["inventory"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("", response_model=list[InventoryItem])
def list_inventory(store_id: str):
    data = store.get(store_id)
    return list(data.inventory.values())


@router.get("/{item_id}", response_model=InventoryItem)
def get_inventory(store_id: str, item_id: str):
    data = store.get(store_id)
    record = data.inventory.get(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    return record


@router.post("/{item_id}/adjust", response_model=InventoryItem)
def adjust_inventory(store_id: str, item_id: str, payload: InventoryAdjust):
    data = store.get(store_id)
    record = data.inventory.get(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Inventory record not found")

    new_quantity = record["stock_quantity"] + payload.delta
    if new_quantity < 0:
        raise HTTPException(status_code=400, detail="Resulting stock quantity cannot be negative")

    record["stock_quantity"] = new_quantity
    record["updated_at"] = datetime.now(timezone.utc)
    return record
