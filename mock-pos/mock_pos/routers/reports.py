from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from mock_pos.auth import verify_api_key
from mock_pos.models import SalesSummary, SettlementReport
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
    payments = [p for p in _payments_in_period(store_id, period) if p["status"] == "COMPLETED"]
    return SalesSummary(
        store_id=store_id,
        period=period,
        order_count=len({p["order_id"] for p in payments}),
        total_sales=sum(p["amount"] for p in payments),
    )


@router.get("/settlement", response_model=SettlementReport)
def get_settlement_report(store_id: str, period: str = "today"):
    all_payments = _payments_in_period(store_id, period)
    completed = [p for p in all_payments if p["status"] == "COMPLETED"]
    refunded = [p for p in all_payments if p["status"] == "REFUNDED"]
    return SettlementReport(
        store_id=store_id,
        period=period,
        gross_sales=sum(p["amount"] for p in completed),
        payment_count=len(completed),
        refunded_amount=sum(p["amount"] for p in refunded),
        refunded_count=len(refunded),
    )
