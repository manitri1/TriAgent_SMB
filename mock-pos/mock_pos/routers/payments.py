import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from mock_pos.auth import verify_api_key
from mock_pos.models import Payment, PaymentCreate
from mock_pos.routers.orders import _deduct_inventory
from mock_pos.store import store

router = APIRouter(
    prefix="/v1/stores/{store_id}/payments",
    tags=["payments"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("", response_model=Payment, status_code=201)
def create_payment(store_id: str, payload: PaymentCreate):
    data = store.get(store_id)
    order = data.orders.get(payload.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order["status"] == "CANCELED":
        raise HTTPException(status_code=409, detail="Cannot pay a canceled order")

    if order["status"] == "OPEN":
        _deduct_inventory(data, order)
        order["status"] = "COMPLETED"
        order["updated_at"] = datetime.now(timezone.utc)

    payment = Payment(
        payment_id=f"pay_{uuid.uuid4().hex[:12]}",
        store_id=store_id,
        order_id=order["order_id"],
        amount=order["total_amount"],
        method=payload.method,
    )
    data.payments[payment.payment_id] = payment.model_dump()
    return payment


@router.get("/{payment_id}", response_model=Payment)
def get_payment(store_id: str, payment_id: str):
    data = store.get(store_id)
    payment = data.payments.get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/{payment_id}/refund", response_model=Payment)
def refund_payment(store_id: str, payment_id: str):
    data = store.get(store_id)
    payment = data.payments.get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment["status"] != "COMPLETED":
        raise HTTPException(status_code=409, detail=f"Payment is already {payment['status']}")

    order = data.orders.get(payment["order_id"])
    if not order or order["status"] != "COMPLETED":
        raise HTTPException(status_code=409, detail="Order is not in a refundable state")

    for line in order["line_items"]:
        record = data.inventory.get(line["item_id"])
        if record:
            record["stock_quantity"] += line["quantity"]
            record["updated_at"] = datetime.now(timezone.utc)

    order["status"] = "REFUNDED"
    order["updated_at"] = datetime.now(timezone.utc)
    payment["status"] = "REFUNDED"
    payment["refunded_at"] = datetime.now(timezone.utc)
    return payment
