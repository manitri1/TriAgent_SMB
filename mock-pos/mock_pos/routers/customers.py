from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response

from mock_pos.auth import verify_api_key
from mock_pos.models import Customer, CustomerCreate
from mock_pos.store import StoreData, store

router = APIRouter(
    prefix="/v1/stores/{store_id}/customers",
    tags=["customers"],
    dependencies=[Depends(verify_api_key)],
)


def compute_customer_stats(data: StoreData, customer_id: str) -> dict:
    """주문/결제 데이터로부터 order_count/total_spent/last_order_at을 계산한다.

    Customer 레코드에는 저장하지 않고 조회 시마다 계산한다(MVP 범위 — docs/12 참고).
    """
    order_count = 0
    total_spent = 0
    last_order_at = None
    for payment in data.payments.values():
        if payment["status"] not in ("COMPLETED", "PARTIALLY_REFUNDED"):
            continue
        order = data.orders.get(payment["order_id"])
        if not order or order.get("customer_id") != customer_id:
            continue
        order_count += 1
        total_spent += payment["amount"] - payment["refunded_amount"]
        created_at = order["created_at"]
        if last_order_at is None or created_at > last_order_at:
            last_order_at = created_at
    return {"order_count": order_count, "total_spent": total_spent, "last_order_at": last_order_at}


@router.post("", response_model=Customer)
def upsert_customer(store_id: str, payload: CustomerCreate, response: Response):
    data = store.get(store_id)
    existed = payload.customer_id in data.customers
    record = data.customers.get(payload.customer_id) or {"created_at": datetime.now(timezone.utc)}
    record["customer_id"] = payload.customer_id
    record["name"] = payload.name
    record["phone"] = payload.phone
    record["notes"] = payload.notes
    data.customers[payload.customer_id] = record

    response.status_code = 200 if existed else 201
    return Customer(**record, **compute_customer_stats(data, payload.customer_id))


@router.get("", response_model=list[Customer])
def list_customers(store_id: str):
    data = store.get(store_id)
    return [
        Customer(**record, **compute_customer_stats(data, customer_id))
        for customer_id, record in data.customers.items()
    ]


@router.get("/{customer_id}", response_model=Customer)
def get_customer(store_id: str, customer_id: str):
    data = store.get(store_id)
    record = data.customers.get(customer_id)
    stats = compute_customer_stats(data, customer_id)

    if not record:
        if stats["order_count"] == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
        record = {
            "customer_id": customer_id,
            "name": None,
            "phone": None,
            "notes": None,
            "created_at": datetime.now(timezone.utc),
        }

    return Customer(**record, **stats)
