""""오늘 데이터 없음" 자가치유 — 서버 기동 시 + 주기 점검 시 자동으로 채워 넣는다.

`scripts/seed_manicafe_month.py`는 "한 번 실행하는 히스토리 시드"이고 멱등적이지
않다(카탈로그 재등록 시 409, 스크립트 자체 docstring 참고). mock-pos는 인메모리라
컨테이너를 재시작하지 않고 여러 날 켜 두면(2026-09-14 실측: 9/12에 시드하고
재시작 없이 이틀 경과) 시드 시점 이후의 "오늘"은 항상 주문이 0건이라 대시보드
매출/정산/인기메뉴가 0으로 보인다 — reports.py의 period 계산 자체는 정상이고,
데이터가 실제로 없을 뿐이다.

이 모듈은 그 간극만 메운다. 카탈로그/고객 등록은 절대 하지 않는다 — 그건
seed_manicafe_month.py(사장님의 하루 스토리보드에 맞춘 커스텀 시나리오: 아메리카노
품절, 시즌 메뉴 24일차 출시, 환불 데모 등)의 몫이고, 여기서 먼저 손대면 그 스크립트를
나중에 수동 실행할 때 카탈로그 409로 실패한다. 그래서:
  - 카탈로그가 비어 있으면(seed 스크립트를 아직 실행하지 않음) 아무것도 하지 않고
    조용히 넘어간다.
  - 카탈로그는 있는데 주문이 하나도 없으면(드문 경우) 최근 BACKFILL_DAYS_IF_EMPTY일치
    히스토리를 이미 등록된 품목/고객만으로 채운다.
  - 마지막 주문일과 오늘 사이에 빈 날짜가 있으면(이번에 겪은 문제) 그 사이 날짜를
    하루치씩 채운다.
  - 오늘 날짜는 "지금까지 지난 영업시간 비율"에 비례한 만큼만 채워, 점검이 반복돼도
    중복 생성 없이 하루가 진행될수록 자연스럽게 누적되게 한다.
  - 오늘 날짜의 확정 예약이 하나도 없으면(등록된 고객이 있을 때만) 몇 건 추가해,
    예약 관리 화면도 "오늘"이 비어 보이지 않게 한다.

docker-compose에서 MOCK_POS_SELF_HEAL_ENABLED=true로만 켠다(기본 비활성) — 테스트
스위트는 이 환경변수를 설정하지 않으므로 영향받지 않는다.
"""
from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from mock_pos.store import StoreData, store

CHECK_INTERVAL_SECONDS = 3600  # 1시간마다 점검 — 자정이 지나면 다음 점검 때 바로 채워짐
BACKFILL_DAYS_IF_EMPTY = 14  # 카탈로그는 있는데 주문이 하나도 없을 때만 채우는 기간
MONTH_SEED_DAYS = 35  # mock_pos/seed.py의 "한 달 시뮬레이션" 모드가 채우는 기간
# 이 매장의 영업시간(OPEN_HOUR~CLOSE_HOUR)은 실제 한국 카페의 로컬 시각이다
# (docs/14 "영업시간: 매일 08:00~22:00"). datetime.now(timezone.utc)의 .hour를
# 그대로 쓰면 UTC 08~22시(=KST 17시~다음날 07시, 한국 기준 저녁~새벽)에만 "영업
# 중"으로 계산되어, 정작 한국 낮 시간(UTC 00~08시)에 점검하면 elapsed_ratio가
# 항상 0으로 나와 "오늘" 매출이 계속 0건으로 보이는 버그가 있었다(2026-09-15
# 실측). 아래 KST 변환은 이 버그를 막기 위한 것 — 저장되는 시각 자체는 여전히
# 시간대 인식(aware) datetime이라 절대 시점은 정확하다.
KST = timezone(timedelta(hours=9))
WALKIN_PROBABILITY = 0.30
HOUR_CLUSTERS = [(8, 10, 3.0), (10, 12, 2.0), (12, 14, 3.0), (14, 17, 2.5), (17, 19, 2.5), (19, 22, 1.5)]
DOW_MULTIPLIER = {0: 0.80, 1: 0.85, 2: 0.90, 3: 0.95, 4: 1.15, 5: 1.35, 6: 1.25}
BASE_DAILY_ORDERS = 20
OPEN_HOUR, CLOSE_HOUR = 8, 22
RESERVATION_SERVICES = ["단체석(4인) 예약", "스터디룸 예약", "단체석(6인) 예약", "노트북 작업석 예약"]


def _pick_customer(data: StoreData) -> str | None:
    if random.random() < WALKIN_PROBABILITY or not data.customers:
        return None
    return random.choice(list(data.customers.keys()))


def _pick_line_items(data: StoreData) -> list[dict]:
    item_ids = list(data.catalog.keys())
    if not item_ids:
        return []
    n_items = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
    picks = random.sample(item_ids, k=min(n_items, len(item_ids)))
    return [{"item_id": item_id, "quantity": random.choices([1, 2, 3], weights=[80, 18, 2])[0]} for item_id in picks]


def _create_order_and_payment(data: StoreData, store_id: str, order_time: datetime) -> None:
    resolved = []
    total_amount = 0
    for li in _pick_line_items(data):
        catalog_item = data.catalog.get(li["item_id"])
        if not catalog_item:
            continue
        subtotal = catalog_item["unit_price"] * li["quantity"]
        total_amount += subtotal
        resolved.append({**li, "note": None, "unit_price": catalog_item["unit_price"], "subtotal": subtotal})
    if not resolved:
        return

    order_id = f"order_{uuid.uuid4().hex[:12]}"
    order = {
        "order_id": order_id, "store_id": store_id, "status": "OPEN", "line_items": resolved,
        "total_amount": total_amount, "currency": "KRW", "customer_id": _pick_customer(data),
        "created_at": order_time, "updated_at": order_time,
    }
    data.orders[order_id] = order

    has_stock = all(data.inventory.get(li["item_id"], {}).get("stock_quantity", 0) >= li["quantity"] for li in resolved)
    if not has_stock:
        order["status"] = "CANCELED"  # 실제 handler와 동일 원칙: 재고 부족 시 취소 처리(품절 신호는 보존)
        return

    for li in resolved:
        data.inventory[li["item_id"]]["stock_quantity"] -= li["quantity"]
        data.inventory[li["item_id"]]["updated_at"] = order_time

    payment_time = order_time + timedelta(minutes=random.randint(0, 2))
    order["status"] = "COMPLETED"
    order["updated_at"] = payment_time
    payment_id = f"pay_{uuid.uuid4().hex[:12]}"
    data.payments[payment_id] = {
        "payment_id": payment_id, "store_id": store_id, "order_id": order_id, "amount": total_amount,
        "currency": "KRW", "status": "COMPLETED", "method": "CARD", "refunded_amount": 0,
        "created_at": payment_time, "refunded_at": None,
    }


def _orders_on_date(data: StoreData, day) -> list[dict]:
    return [o for o in data.orders.values() if o["created_at"].astimezone(KST).date() == day]


def _backfill_full_day(data: StoreData, store_id: str, day: datetime) -> int:
    """day 하루 전체(00:00~24:00)를 실제 영업 패턴대로 채운다 — 완전히 지나간 날짜용."""
    target = round(BASE_DAILY_ORDERS * DOW_MULTIPLIER[day.weekday()] * random.uniform(0.85, 1.15))
    created = 0
    for _ in range(max(target, 0)):
        cluster = random.choices(HOUR_CLUSTERS, weights=[c[2] for c in HOUR_CLUSTERS])[0]
        start_h, end_h, _ = cluster
        offset = random.randint(0, (end_h - start_h) * 60 - 1)
        order_time = day.replace(hour=start_h, minute=0, second=0, microsecond=0) + timedelta(minutes=offset)
        _create_order_and_payment(data, store_id, order_time)
        created += 1
    return created


def _top_up_today(data: StoreData, store_id: str, now: datetime) -> int:
    """오늘은 "지금까지 지난 영업시간 비율"만큼만 채운다 — 반복 점검해도 중복
    생성 없이, 하루가 진행될수록 매출이 자연스럽게 쌓이는 것처럼 보이게 한다.
    "지금"과 "영업시간"은 반드시 같은 시간대(KST)로 비교해야 한다(파일 상단
    KST 상수 설명 참고)."""
    now_kst = now.astimezone(KST)
    today_start = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    existing = len(_orders_on_date(data, now_kst.date()))

    now_frac = now_kst.hour + now_kst.minute / 60
    elapsed_ratio = min(1.0, max(0.0, (now_frac - OPEN_HOUR) / (CLOSE_HOUR - OPEN_HOUR)))
    full_day_target = round(BASE_DAILY_ORDERS * DOW_MULTIPLIER[now_kst.weekday()])
    expected_so_far = round(full_day_target * elapsed_ratio)
    missing = expected_so_far - existing
    if missing <= 0:
        return 0

    candidates = [c for c in HOUR_CLUSTERS if c[0] < now_frac]
    created = 0
    for _ in range(missing):
        if not candidates:
            break
        cluster = random.choices(candidates, weights=[c[2] for c in candidates])[0]
        start_h, end_h, _ = cluster
        end_h = min(end_h, int(now_frac) + 1)
        total_minutes = max(1, (end_h - start_h) * 60)
        offset = random.randint(0, total_minutes - 1)
        order_time = min(today_start.replace(hour=start_h) + timedelta(minutes=offset), now)
        _create_order_and_payment(data, store_id, order_time)
        created += 1
    return created


def _ensure_today_reservations(data: StoreData, store_id: str, now: datetime) -> None:
    if not data.customers:
        return  # 어떤 고객 이름으로 만들지 알 수 없으면 만들지 않는다
    now_kst = now.astimezone(KST)
    today = now_kst.date()
    has_today = any(
        r["status"] == "BOOKED" and r["datetime"].astimezone(KST).date() == today
        for r in data.reservations.values()
    )
    if has_today:
        return
    customer_ids = list(data.customers.keys())
    for _ in range(random.choice([2, 3])):
        resv_id = f"resv_{uuid.uuid4().hex[:12]}"
        resv_time = now_kst.replace(
            hour=random.choice([11, 13, 16, 19]), minute=random.choice([0, 30]), second=0, microsecond=0
        )
        data.reservations[resv_id] = {
            "reservation_id": resv_id, "store_id": store_id, "customer_id": random.choice(customer_ids),
            "datetime": resv_time, "service": random.choice(RESERVATION_SERVICES), "status": "BOOKED",
            "note": None, "created_at": now,
        }


RESTOCK_INTERVAL_DAYS = 3  # seed_month_history 전용 — 실제 발주 승인 없이 정기 재입고를 근사


def _restock_all(data: StoreData) -> None:
    """카탈로그의 모든 품목을 넉넉한 수준으로 채운다 — "사장님이 정기적으로
    재입고했다"는 사실을 근사하는 시뮬레이션 전용 장치다(실제 발주 승인
    흐름을 재현하지 않는다). 이게 없으면 `_backfill_full_day`가 매일 임계치를
    보지 않고 무작위로 품목을 소진시켜, 며칠 안에 전 품목이 0으로 굳어버리고
    이후 모든 주문이 재고부족으로 CANCELED 처리된다(실측: 재입고 없이 35일
    역산했더니 최근 7일 매출이 전부 0으로 나왔다)."""
    for inv in data.inventory.values():
        threshold = inv.get("low_stock_threshold", 5)
        if inv["stock_quantity"] < threshold * 2:
            inv["stock_quantity"] = threshold * random.randint(4, 7)


def seed_month_history(store_id: str, days: int = MONTH_SEED_DAYS) -> int:
    """카탈로그·고객이 이미 채워진 빈 매장에 과거 `days`일치 영업 이력 + 오늘
    진행분을 채운다 — `run_self_heal_once`의 "주문이 하나도 없을 때" 분기와
    같은 엔진(요일별 배수·시간대 클러스터)을 쓰지만, 목업 데이터 시드 버튼
    (mock_pos/seed.py의 "한 달 시뮬레이션" 모드) 전용으로 독립 호출할 수 있게
    분리했다 — run_self_heal_once의 기존 동작·시간 간격 점검 로직은 건드리지
    않는다. `_restock_all`로 며칠마다 재고를 보충해 최근 날짜까지 매출이
    자연스럽게 이어지게 한다."""
    data = store.get(store_id)
    now = datetime.now(timezone.utc)
    now_kst = now.astimezone(KST)
    start_day = (now_kst - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    total = 0
    for i in range(days - 1):
        if i % RESTOCK_INTERVAL_DAYS == 0:
            _restock_all(data)
        total += _backfill_full_day(data, store_id, start_day + timedelta(days=i))
    _restock_all(data)  # 오늘 영업 시작 전 마지막 재입고
    total += _top_up_today(data, store_id, now)
    _ensure_today_reservations(data, store_id, now)
    return total


def run_self_heal_once(store_id: str) -> None:
    data = store.get(store_id)
    if not data.catalog:
        return  # 아직 seed_manicafe_month.py를 실행하기 전 — 카탈로그는 여기서 만들지 않는다

    now = datetime.now(timezone.utc)
    now_kst = now.astimezone(KST)
    total_created = 0

    if not data.orders:
        start_day = (now_kst - timedelta(days=BACKFILL_DAYS_IF_EMPTY - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
        for i in range(BACKFILL_DAYS_IF_EMPTY - 1):
            total_created += _backfill_full_day(data, store_id, start_day + timedelta(days=i))
    else:
        last_day = max(o["created_at"].astimezone(KST).date() for o in data.orders.values())
        d = last_day
        while d < now_kst.date() - timedelta(days=1):
            d += timedelta(days=1)
            day_dt = now_kst.replace(year=d.year, month=d.month, day=d.day, hour=0, minute=0, second=0, microsecond=0)
            total_created += _backfill_full_day(data, store_id, day_dt)

    total_created += _top_up_today(data, store_id, now)
    _ensure_today_reservations(data, store_id, now)

    if total_created:
        print(f"[self-heal] store={store_id} — 자동 생성 주문 {total_created}건 (기준 시각 {now.isoformat()})")


async def self_heal_loop(store_id: str) -> None:
    while True:
        try:
            run_self_heal_once(store_id)
        except Exception as exc:  # noqa: BLE001 — 데모용 백그라운드 작업이 서버 자체를 죽이면 안 된다
            print(f"[self-heal] 점검 중 오류(무시하고 계속): {exc!r}")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
