"""mock-pos 읽기 전용 프록시.

이 라우터는 GET 핸들러만 등록한다 — mock-pos의 쓰기(POST/PATCH) 엔드포인트를
호출하는 코드 경로는 이 파일에 존재하지 않는다. 이건 관례가 아니라 구조적
제약이다: 이 파일에 @router.post/@router.patch가 추가된다면 그 자체로
docs/12-web-gui-demo.md의 "대시보드는 조회 전용" 원칙을 깨는 버그다. 쓰기는
반드시 routers/agent.py를 거쳐 에이전트(coordinator)에게 위임한다.
"""
from fastapi import APIRouter, Depends, HTTPException

from webapp_bff.auth import require_auth
from webapp_bff.pos_client import pos_client

router = APIRouter(prefix="/api/pos", tags=["pos-proxy"], dependencies=[Depends(require_auth)])


def _relay(path: str, params: dict | None = None):
    resp = pos_client.get(path, params=params)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@router.get("/inventory")
def inventory():
    return _relay("/inventory")


@router.get("/inventory/{item_id}")
def inventory_item(item_id: str):
    return _relay(f"/inventory/{item_id}")


@router.get("/orders")
def orders(status: str | None = None, customer_id: str | None = None):
    params = {k: v for k, v in {"status": status, "customer_id": customer_id}.items() if v}
    return _relay("/orders", params)


@router.get("/catalog/items")
def catalog_items():
    return _relay("/catalog/items")


@router.get("/reservations")
def reservations(date: str | None = None, status: str | None = None):
    params = {k: v for k, v in {"date": date, "status": status}.items() if v}
    return _relay("/reservations", params)


@router.get("/reports/sales")
def reports_sales(period: str = "today"):
    return _relay("/reports/sales", {"period": period})


@router.get("/reports/settlement")
def reports_settlement(period: str = "today"):
    return _relay("/reports/settlement", {"period": period})


@router.get("/reports/top-items")
def reports_top_items(period: str = "today", limit: int = 5):
    return _relay("/reports/top-items", {"period": period, "limit": limit})


@router.get("/reports/sales/daily")
def reports_sales_daily(days: int = 7):
    return _relay("/reports/sales/daily", {"days": days})


@router.get("/reports/margin")
def reports_margin(period: str = "today"):
    return _relay("/reports/margin", {"period": period})


@router.get("/reports/repeat-customers")
def reports_repeat_customers(period: str = "all", min_orders: int = 2):
    return _relay("/reports/repeat-customers", {"period": period, "min_orders": min_orders})
