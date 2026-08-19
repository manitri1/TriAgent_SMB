import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from mock_pos.auth import verify_api_key
from mock_pos.models import Order, OrderCreate, OrderLineItem, OrderUpdate
from mock_pos.store import store

router = APIRouter(
    prefix="/v1/stores/{store_id}/orders",
    tags=["orders"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("", response_model=Order, status_code=201)
def create_order(store_id: str, payload: OrderCreate):
    data = store.get(store_id)

    if not payload.line_items:
        raise HTTPException(status_code=400, detail="line_items must not be empty")

    line_items: list[OrderLineItem] = []
    total_amount = 0
    for line in payload.line_items:
        catalog_item = data.catalog.get(line.item_id)
        if not catalog_item:
            raise HTTPException(status_code=404, detail=f"Catalog item not found: {line.item_id}")
        if line.quantity <= 0:
            raise HTTPException(status_code=400, detail="quantity must be positive")

        subtotal = catalog_item["unit_price"] * line.quantity
        total_amount += subtotal
        line_items.append(
            OrderLineItem(
                item_id=line.item_id,
                quantity=line.quantity,
                note=line.note,
                unit_price=catalog_item["unit_price"],
                subtotal=subtotal,
            )
        )

    order = Order(
        order_id=f"order_{uuid.uuid4().hex[:12]}",
        store_id=store_id,
        line_items=line_items,
        total_amount=total_amount,
        customer_id=payload.customer_id,
    )
    data.orders[order.order_id] = order.model_dump()
    return order


@router.get("/{order_id}", response_model=Order)
def get_order(store_id: str, order_id: str):
    data = store.get(store_id)
    order = data.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}", response_model=Order)
def update_order(store_id: str, order_id: str, payload: OrderUpdate):
    data = store.get(store_id)
    order = data.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if payload.status is None:
        return order

    if payload.status not in ("COMPLETED", "CANCELED"):
        raise HTTPException(status_code=400, detail="status must be COMPLETED or CANCELED")
    if order["status"] != "OPEN":
        raise HTTPException(status_code=409, detail=f"Order is already {order['status']}")

    if payload.status == "COMPLETED":
        _deduct_inventory(data, order)

    order["status"] = payload.status
    order["updated_at"] = datetime.now(timezone.utc)
    return order


def _deduct_inventory(data, order: dict) -> None:
    for line in order["line_items"]:
        record = data.inventory.get(line["item_id"])
        if not record or record["stock_quantity"] < line["quantity"]:
            raise HTTPException(
                status_code=409,
                detail=f"Insufficient stock for item {line['item_id']}",
            )

    for line in order["line_items"]:
        record = data.inventory[line["item_id"]]
        record["stock_quantity"] -= line["quantity"]
        record["updated_at"] = datetime.now(timezone.utc)
