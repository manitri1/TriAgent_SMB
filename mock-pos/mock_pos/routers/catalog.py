from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from mock_pos.auth import verify_api_key
from mock_pos.models import CatalogItem, CatalogItemCreate
from mock_pos.store import store

router = APIRouter(
    prefix="/v1/stores/{store_id}/catalog/items",
    tags=["catalog"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("", response_model=list[CatalogItem])
def list_items(store_id: str):
    data = store.get(store_id)
    return list(data.catalog.values())


@router.get("/{item_id}", response_model=CatalogItem)
def get_item(store_id: str, item_id: str):
    data = store.get(store_id)
    item = data.catalog.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Catalog item not found")
    return item


@router.post("", response_model=CatalogItem, status_code=201)
def create_item(store_id: str, payload: CatalogItemCreate):
    data = store.get(store_id)
    if payload.item_id in data.catalog:
        raise HTTPException(status_code=409, detail="Catalog item already exists")

    item = CatalogItem(
        item_id=payload.item_id,
        name=payload.name,
        unit_price=payload.unit_price,
        category=payload.category,
    )
    data.catalog[item.item_id] = item.model_dump()

    data.inventory[item.item_id] = {
        "item_id": item.item_id,
        "stock_quantity": payload.initial_stock,
        "updated_at": datetime.now(timezone.utc),
    }
    return item
