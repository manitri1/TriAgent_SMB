"""목업 데이터 초기화·시뮬레이션 — 데모/리허설 준비 전용.

mock_pos/routers/admin.py가 호출하는 두 모드:
  - "quick" : `scripts/seed_manicafe_demo.sh`와 동일한 스냅샷(메뉴 12종·고객
    6명·오늘 주문/결제 21건·환불 2건, 아메리카노 재고 0 포함) — 라이브 데모
    대본(docs/21-live-demo-plan.md)이 그대로 재현된다.
  - "month" : 카탈로그·고객은 동일하되 아메리카노도 다른 커피 메뉴처럼 정상
    재고로 시작한 뒤, `self_heal.seed_month_history()`로 지난 `days`일치
    요일별 패턴 + 오늘 진행분을 채운다 — `scripts/seed_manicafe_month.py`의
    "한 달 운영된 것처럼 보이는" 효과를 버튼 하나로 재현한다(단, 시즌 메뉴
    출시·특정 컴플레인 고객 지정 같은 그 스크립트의 세부 스토리라인까지는
    재현하지 않는다 — 대시보드 차트를 채우는 범용 시뮬레이션이 목적이다).

기존 스크립트들과 달리 컨테이너 재시작이 필요 없다 — `store.reset()`으로
인메모리 데이터를 그 자리에서 비우고 다시 채운다. mock-pos 라우터 함수를
HTTP를 거치지 않고 파이썬에서 직접 호출해 카탈로그/주문/결제 검증 로직(가격
계산, 재고 차감, 환불 규칙)을 그대로 재사용한다 — 별도로 복제하지 않는다.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Response

from mock_pos import self_heal
from mock_pos.models import (
    CatalogItemCreate,
    CustomerCreate,
    OrderCreate,
    OrderLineItemIn,
    PaymentCreate,
    RefundRequest,
)
from mock_pos.routers import catalog, customers, orders, payments
from mock_pos.store import store

_CATALOG_BASE = [
    {"item_id": "menu_americano", "name": "아메리카노", "unit_price": 3500, "cost": 800, "category": "coffee", "initial_stock": 0, "low_stock_threshold": 5},
    {"item_id": "menu_latte", "name": "라떼", "unit_price": 4500, "cost": 1000, "category": "coffee", "initial_stock": 45, "low_stock_threshold": 10},
    {"item_id": "menu_cappuccino", "name": "카푸치노", "unit_price": 4700, "cost": 1100, "category": "coffee", "initial_stock": 38, "low_stock_threshold": 10},
    {"item_id": "menu_espresso", "name": "에스프레소", "unit_price": 3000, "cost": 700, "category": "coffee", "initial_stock": 60, "low_stock_threshold": 10},
    {"item_id": "menu_coldbrew", "name": "콜드브루", "unit_price": 5200, "cost": 1200, "category": "coffee", "initial_stock": 30, "low_stock_threshold": 8},
    {"item_id": "menu_matcha_latte", "name": "말차라떼", "unit_price": 5200, "cost": 1200, "category": "tea", "initial_stock": 25, "low_stock_threshold": 8},
    {"item_id": "menu_chai_latte", "name": "차이라떼", "unit_price": 4800, "cost": 1100, "category": "tea", "initial_stock": 22, "low_stock_threshold": 8},
    {"item_id": "menu_muffin", "name": "블루베리 머핀", "unit_price": 2800, "cost": 500, "category": "bakery", "initial_stock": 18, "low_stock_threshold": 10},
    {"item_id": "menu_croissant", "name": "크루아상", "unit_price": 3000, "cost": 600, "category": "bakery", "initial_stock": 16, "low_stock_threshold": 10},
    {"item_id": "menu_sandwich", "name": "햄&치즈 샌드위치", "unit_price": 6500, "cost": 1800, "category": "sandwich", "initial_stock": 12, "low_stock_threshold": 5},
    {"item_id": "menu_smoothie", "name": "딸기 스무디", "unit_price": 5500, "cost": 1300, "category": "smoothie", "initial_stock": 14, "low_stock_threshold": 6},
    {"item_id": "menu_cake", "name": "시즌 케이크(딸기)", "unit_price": 6000, "cost": 2000, "category": "dessert", "initial_stock": 9, "low_stock_threshold": 5},
]

_CUSTOMERS = [
    {"customer_id": "cust_minji", "name": "김민지", "phone": "010-1234-5678"},
    {"customer_id": "cust_junho", "name": "이준호", "phone": "010-2345-6789"},
    {"customer_id": "cust_soyeon", "name": "박소연", "phone": "010-3456-7890"},
    {"customer_id": "cust_donghyun", "name": "최동현", "phone": "010-4567-8901"},
    {"customer_id": "cust_yuna", "name": "정유나", "phone": "010-5678-9012"},
    {"customer_id": "cust_taemin", "name": "강태민", "phone": "010-6789-0123"},
]

# (line_items, customer_id) — scripts/seed_manicafe_demo.sh와 동일한 21건.
_QUICK_ORDERS: list[tuple[list[dict], str]] = [
    ([{"item_id": "menu_latte", "quantity": 2}], "cust_minji"),
    ([{"item_id": "menu_cappuccino", "quantity": 1}, {"item_id": "menu_muffin", "quantity": 1}], "cust_minji"),
    ([{"item_id": "menu_latte", "quantity": 1}], "cust_minji"),
    ([{"item_id": "menu_cappuccino", "quantity": 1}], "cust_minji"),
    ([{"item_id": "menu_coldbrew", "quantity": 1}], "cust_junho"),
    ([{"item_id": "menu_croissant", "quantity": 2}], "cust_junho"),
    ([{"item_id": "menu_matcha_latte", "quantity": 1}, {"item_id": "menu_cake", "quantity": 1}], "cust_soyeon"),
    ([{"item_id": "menu_latte", "quantity": 1}, {"item_id": "menu_muffin", "quantity": 1}], "cust_soyeon"),
    ([{"item_id": "menu_sandwich", "quantity": 1}, {"item_id": "menu_smoothie", "quantity": 1}], "cust_donghyun"),
    ([{"item_id": "menu_espresso", "quantity": 2}], "cust_donghyun"),
    ([{"item_id": "menu_chai_latte", "quantity": 1}], "cust_yuna"),
    ([{"item_id": "menu_latte", "quantity": 3}], "cust_yuna"),
    ([{"item_id": "menu_cappuccino", "quantity": 2}], "cust_taemin"),
    ([{"item_id": "menu_muffin", "quantity": 2}, {"item_id": "menu_croissant", "quantity": 1}], "cust_taemin"),
    ([{"item_id": "menu_smoothie", "quantity": 1}], "cust_minji"),
    ([{"item_id": "menu_latte", "quantity": 1}], "cust_junho"),
    ([{"item_id": "menu_cake", "quantity": 1}], "cust_soyeon"),
    ([{"item_id": "menu_coldbrew", "quantity": 2}], "cust_yuna"),
    ([{"item_id": "menu_cappuccino", "quantity": 1}, {"item_id": "menu_sandwich", "quantity": 1}], "cust_taemin"),
    ([{"item_id": "menu_matcha_latte", "quantity": 1}], "cust_donghyun"),
    ([{"item_id": "menu_muffin", "quantity": 1}], "cust_minji"),
]


def _seed_catalog_and_customers(store_id: str, *, americano_stock: int) -> None:
    for item in _CATALOG_BASE:
        payload = dict(item)
        if payload["item_id"] == "menu_americano":
            payload["initial_stock"] = americano_stock
        catalog.create_item(store_id, CatalogItemCreate(**payload))
    for cust in _CUSTOMERS:
        customers.upsert_customer(store_id, CustomerCreate(**cust), Response())


def _order_and_pay(store_id: str, line_items: list[dict], customer_id: str) -> tuple[str, str]:
    order = orders.create_order(
        store_id,
        OrderCreate(line_items=[OrderLineItemIn(**li) for li in line_items], customer_id=customer_id),
    )
    payment = payments.create_payment(store_id, PaymentCreate(order_id=order.order_id))
    return order.order_id, payment.payment_id


def _result(store_id: str, mode: str, days_simulated: int) -> dict:
    data = store.get(store_id)
    return {
        "mode": mode,
        "catalog_items": len(data.catalog),
        "customers": len(data.customers),
        "orders": len(data.orders),
        "payments": len(data.payments),
        "days_simulated": days_simulated,
    }


def run_quick_seed(store_id: str) -> dict:
    store.reset(store_id)
    _seed_catalog_and_customers(store_id, americano_stock=0)
    for line_items, customer_id in _QUICK_ORDERS:
        _order_and_pay(store_id, line_items, customer_id)

    # 환불 데모 — 전액 1건 + 부분 1건(seed_manicafe_demo.sh와 동일)
    _, refund1_payment_id = _order_and_pay(store_id, [{"item_id": "menu_croissant", "quantity": 1}], "cust_junho")
    payments.refund_payment(store_id, refund1_payment_id, RefundRequest(reason="고객 단순 변심"))

    _, refund2_payment_id = _order_and_pay(store_id, [{"item_id": "menu_cake", "quantity": 1}], "cust_soyeon")
    payments.refund_payment(store_id, refund2_payment_id, RefundRequest(amount=2000, reason="케이크 일부 파손"))

    return _result(store_id, "quick", 1)


def _recent_week_quantity_by_item(data, now) -> dict[str, int]:
    start = now - timedelta(days=7)
    totals: dict[str, int] = {}
    for payment in data.payments.values():
        if payment["status"] not in ("COMPLETED", "PARTIALLY_REFUNDED"):
            continue
        if payment["created_at"] < start:
            continue
        order = data.orders.get(payment["order_id"])
        if not order:
            continue
        for li in order["line_items"]:
            totals[li["item_id"]] = totals.get(li["item_id"], 0) + li["quantity"]
    return totals


def _engineer_dashboard_insights(store_id: str) -> None:
    """한 달 시뮬레이션 직후 대시보드 "오늘 확인해야 할 것"에 서로 다른 종류의
    카드가 최소 몇 개는 반드시 보이도록 몇 가지 상태를 의도적으로 만든다.

    무작위 backfill만으로는 재고 임계치·단골 이탈 같은 조건이 우연에 맡겨져
    매번 다르게(때로는 0~1개만) 나타난다 — 리허설 때마다 버튼을 눌러도 보여줄
    카드가 없으면 데모 가치가 떨어진다. 실제 매출/재고 데이터를 조작하는 게
    아니라, 이미 만들어진 데이터 중 일부(품목 재고 수량, 한 고객의 최근 주문
    귀속)를 데모에 유리한 상태로 조정하는 것뿐이다 — coordinator/webapp의
    "확인해야 할 것" 계산 로직(webapp_bff/static/{common,dashboard}.js)은
    건드리지 않는다."""
    data = store.get(store_id)
    now = datetime.now(timezone.utc)

    non_americano_ids = [i["item_id"] for i in _CATALOG_BASE if i["item_id"] != "menu_americano"]
    if len(non_americano_ids) < 3:
        return
    critical_item, low_item = non_americano_ids[0], non_americano_ids[1]

    # 1) 재고 위험 1개 + 재고 부족 1개 — 서로 다른 두 품목에 강제 지정한다.
    critical_threshold = data.inventory[critical_item]["low_stock_threshold"]
    data.inventory[critical_item]["stock_quantity"] = max(0, critical_threshold // 3)
    low_threshold = data.inventory[low_item]["low_stock_threshold"]
    data.inventory[low_item]["stock_quantity"] = low_threshold  # 임계치 딱 이하("부족" 밴드)

    # 2) 소진 임박/예상 — 최근 7일 판매 속도 대비 재고를 얕게 남기되, 원가
    # 임계치는 넘겨서 위 두 카드와 겹치지 않는 별개의 카드로 뜨게 한다. 판매
    # 속도가 낮은 품목은 "threshold보다 재고가 많으면서 daysLeft<=3"을 동시에
    # 만족시킬 수 없으므로(속도*3일 < threshold), 남은 품목 중 이번 주 판매량이
    # 가장 많은(=가장 자주 빠지는) 품목을 골라야 안정적으로 이 밴드에 들어간다.
    weekly_qty_by_item = _recent_week_quantity_by_item(data, now)
    eta_candidates = [iid for iid in non_americano_ids if iid not in (critical_item, low_item)]
    eta_item = max(eta_candidates, key=lambda iid: weekly_qty_by_item.get(iid, 0), default=None)
    if eta_item:
        eta_threshold = data.inventory[eta_item]["low_stock_threshold"]
        velocity_per_day = weekly_qty_by_item.get(eta_item, 0) / 7
        if velocity_per_day > 0:
            target_days_left = 2.0  # "3일 내 품절 예상" 밴드에 들어가도록
            data.inventory[eta_item]["stock_quantity"] = max(
                eta_threshold + 1, round(velocity_per_day * target_days_left)
            )

    # 3) 이탈 위험 단골 — 3건 이상(14일 이전 기준) 주문한 고객 한 명을 골라,
    # 최근 14일 이내 주문은 walk-in(고객 미지정)으로 돌려 "재방문 없음"으로
    # 보이게 한다. 실제 매출액·건수는 그대로 유지된다(고객 귀속만 바꾼다).
    cutoff = now - timedelta(days=14)
    old_order_counts: dict[str, int] = {}
    for order in data.orders.values():
        customer_id = order.get("customer_id")
        if customer_id and order["created_at"] < cutoff:
            old_order_counts[customer_id] = old_order_counts.get(customer_id, 0) + 1
    churn_candidate = max(old_order_counts, key=old_order_counts.get, default=None)
    if churn_candidate and old_order_counts[churn_candidate] >= 3:
        for order in data.orders.values():
            if order.get("customer_id") == churn_candidate and order["created_at"] >= cutoff:
                order["customer_id"] = None

    # 4) "오늘 예약"은 self_heal.seed_month_history가 이미 채워준다(고객이
    # 있으면 항상 2~3건) — 여기서 손댈 필요 없다.


def run_month_seed(store_id: str, days: int = self_heal.MONTH_SEED_DAYS) -> dict:
    store.reset(store_id)
    # "한 달 시뮬레이션"은 특정 결품 장면이 아니라 대시보드 차트용 일반 이력이
    # 목적이라, 아메리카노도 다른 커피 메뉴처럼 정상 재고로 시작해 자연스럽게
    # 팔리게 한다("quick" 모드의 재고 0은 라이브 데모 대본 전용 장치).
    _seed_catalog_and_customers(store_id, americano_stock=40)
    self_heal.seed_month_history(store_id, days=days)
    _engineer_dashboard_insights(store_id)

    return _result(store_id, "month", days)
