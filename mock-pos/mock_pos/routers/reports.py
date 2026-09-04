from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from mock_pos.auth import verify_api_key
from mock_pos.models import (
    DailySales,
    MarginSummary,
    RepeatCustomer,
    SalesSummary,
    SettlementReport,
    TopItem,
)
from mock_pos.store import store

router = APIRouter(
    prefix="/v1/stores/{store_id}/reports",
    tags=["reports"],
    dependencies=[Depends(verify_api_key)],
)

_PERIODS = {"today", "week", "month", "all"}


def _period_start(period: str) -> datetime | None:
    now = datetime.now(timezone.utc)
    if period == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        return now - timedelta(days=7)
    if period == "month":
        return now - timedelta(days=30)
    return None  # "all"


def _payments_in_period(store_id: str, period: str) -> list[dict]:
    if period not in _PERIODS:
        raise HTTPException(status_code=400, detail=f"period must be one of {sorted(_PERIODS)}")

    data = store.get(store_id)
    start = _period_start(period)
    payments = list(data.payments.values())
    if start is not None:
        payments = [p for p in payments if p["created_at"] >= start]
    return payments


@router.get("/sales", response_model=SalesSummary)
def get_sales_summary(store_id: str, period: str = "today"):
    payments = [
        p for p in _payments_in_period(store_id, period) if p["status"] in ("COMPLETED", "PARTIALLY_REFUNDED")
    ]
    return SalesSummary(
        store_id=store_id,
        period=period,
        order_count=len({p["order_id"] for p in payments}),
        total_sales=sum(p["amount"] - p["refunded_amount"] for p in payments),
    )


@router.get("/settlement", response_model=SettlementReport)
def get_settlement_report(store_id: str, period: str = "today"):
    all_payments = _payments_in_period(store_id, period)
    completed = [p for p in all_payments if p["status"] in ("COMPLETED", "PARTIALLY_REFUNDED")]
    refunded = [p for p in all_payments if p["status"] == "REFUNDED"]
    partially_refunded = [p for p in all_payments if p["status"] == "PARTIALLY_REFUNDED"]
    return SettlementReport(
        store_id=store_id,
        period=period,
        gross_sales=sum(p["amount"] for p in completed),
        payment_count=len(completed),
        refunded_amount=sum(p["amount"] for p in refunded),
        refunded_count=len(refunded),
        partial_refund_amount=sum(p["refunded_amount"] for p in partially_refunded),
        partial_refund_count=len(partially_refunded),
    )


@router.get("/top-items", response_model=list[TopItem])
def get_top_items(store_id: str, period: str = "today", limit: int = 5):
    data = store.get(store_id)
    payments = [
        p for p in _payments_in_period(store_id, period) if p["status"] in ("COMPLETED", "PARTIALLY_REFUNDED")
    ]

    totals: dict[str, dict] = defaultdict(lambda: {"quantity": 0, "revenue": 0})
    for payment in payments:
        order = data.orders.get(payment["order_id"])
        if not order:
            continue
        for line in order["line_items"]:
            entry = totals[line["item_id"]]
            entry["quantity"] += line["quantity"]
            entry["revenue"] += line["subtotal"]

    items = []
    for item_id, agg in totals.items():
        unit_cost = data.catalog.get(item_id, {}).get("cost", 0)
        item_cost = unit_cost * agg["quantity"]
        items.append(
            TopItem(
                item_id=item_id,
                name=data.catalog.get(item_id, {}).get("name", item_id),
                quantity=agg["quantity"],
                revenue=agg["revenue"],
                cost=item_cost,
                margin=agg["revenue"] - item_cost,
            )
        )
    items.sort(key=lambda item: item.revenue, reverse=True)
    return items[:limit]


@router.get("/margin", response_model=MarginSummary)
def get_margin_summary(store_id: str, period: str = "today"):
    data = store.get(store_id)
    payments = [
        p for p in _payments_in_period(store_id, period) if p["status"] in ("COMPLETED", "PARTIALLY_REFUNDED")
    ]

    total_revenue = 0
    total_cost = 0
    for payment in payments:
        order = data.orders.get(payment["order_id"])
        if not order:
            continue
        # 매출은 부분환불액을 뺀 순액으로 계산한다(원가는 반품이 아니므로 그대로 유지).
        total_revenue += payment["amount"] - payment["refunded_amount"]
        for line in order["line_items"]:
            unit_cost = data.catalog.get(line["item_id"], {}).get("cost", 0)
            total_cost += unit_cost * line["quantity"]

    gross_margin = total_revenue - total_cost
    margin_rate = gross_margin / total_revenue if total_revenue else 0.0
    return MarginSummary(
        store_id=store_id,
        period=period,
        total_revenue=total_revenue,
        total_cost=total_cost,
        gross_margin=gross_margin,
        margin_rate=margin_rate,
    )


@router.get("/repeat-customers", response_model=list[RepeatCustomer])
def get_repeat_customers(store_id: str, period: str = "all", min_orders: int = 2):
    data = store.get(store_id)
    payments = [
        p for p in _payments_in_period(store_id, period) if p["status"] in ("COMPLETED", "PARTIALLY_REFUNDED")
    ]

    totals: dict[str, dict] = defaultdict(lambda: {"order_count": 0, "total_spent": 0, "last_order_at": None})
    for payment in payments:
        order = data.orders.get(payment["order_id"])
        customer_id = order.get("customer_id") if order else None
        if not customer_id:
            continue
        entry = totals[customer_id]
        entry["order_count"] += 1
        entry["total_spent"] += payment["amount"] - payment["refunded_amount"]
        created_at = order["created_at"]
        if entry["last_order_at"] is None or created_at > entry["last_order_at"]:
            entry["last_order_at"] = created_at

    customers = [
        RepeatCustomer(
            customer_id=customer_id,
            name=data.customers.get(customer_id, {}).get("name"),
            order_count=agg["order_count"],
            total_spent=agg["total_spent"],
            last_order_at=agg["last_order_at"],
        )
        for customer_id, agg in totals.items()
        if agg["order_count"] >= min_orders
    ]
    customers.sort(key=lambda c: (c.order_count, c.total_spent), reverse=True)
    return customers


@router.get("/sales/daily", response_model=list[DailySales])
def get_daily_sales(store_id: str, days: int = 7):
    if days <= 0:
        raise HTTPException(status_code=400, detail="days must be positive")

    data = store.get(store_id)
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=days - 1)

    buckets: dict[str, dict] = {
        (start_date + timedelta(days=offset)).isoformat(): {"order_count": 0, "total_sales": 0}
        for offset in range(days)
    }

    completed = [p for p in data.payments.values() if p["status"] == "COMPLETED"]
    for payment in completed:
        day_key = payment["created_at"].date().isoformat()
        if day_key in buckets:
            buckets[day_key]["order_count"] += 1
            buckets[day_key]["total_sales"] += payment["amount"]

    return [
        DailySales(date=day, order_count=counts["order_count"], total_sales=counts["total_sales"])
        for day, counts in sorted(buckets.items())
    ]
