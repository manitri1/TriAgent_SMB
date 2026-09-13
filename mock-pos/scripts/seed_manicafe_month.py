#!/usr/bin/env python3
"""마니카페 연남점 — "한 달 이상 운영 중"인 것처럼 보이는 현실적 목업 데이터 시드.

`seed_manicafe_demo.sh`(스냅샷 20여 건, 전부 "지금" 시각)와 달리 이 스크립트는
mock-pos의 `POST /orders`, `POST /payments`에 새로 추가된 선택적 `created_at`
필드(과거 시각 지정, docs/14-webapp-users-guide.md 4번 각주였던 제약 해소)를 써서
개업일(오늘로부터 약 5주 전)부터 오늘까지 매일의 주문/결제를 실제 타임스탬프로
채워 넣는다. 그 결과 대시보드의 "매출 추이(최근 7/30일)", "인기 메뉴",
"재방문 고객", "정산" 카드가 하루치가 아니라 진짜 한 달 치 히스토리로 보인다.

재현성: 고정 시드(RNG_SEED)를 쓰므로 매번 실행해도 같은 형태의 데이터가 나온다
(정확히 같은 order_id/시각까지는 아니지만 분포·규모는 동일).

mock-pos는 인메모리라 컨테이너 재시작 시 초기화된다 — 재실행 전엔
`docker compose restart mock-pos`로 비운 뒤 실행할 것(멱등적이지 않음, 두 번
실행하면 카탈로그 409로 실패한다).

사용법:
    cd mock-pos/scripts
    python3 seed_manicafe_month.py
"""
from __future__ import annotations

import json
import os
import random
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

BASE = os.environ.get("MOCK_POS_BASE_URL", "http://localhost:18080")
KEY = os.environ.get("MOCK_POS_API_KEY", "dev-key")
STORE = os.environ.get("MOCK_POS_STORE_ID", "store_demo")
RNG_SEED = int(os.environ.get("SEED_RNG_SEED", "20260912"))
OPERATING_DAYS = int(os.environ.get("SEED_OPERATING_DAYS", "38"))  # 개업일로부터 오늘까지

random.seed(RNG_SEED)


def api(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{BASE}/v1/stores/{STORE}{path}"
    data = json.dumps(body, default=str).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("X-API-Key", KEY)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raise HTTPFailure(exc.code, exc.read().decode("utf-8", errors="replace")) from None


class HTTPFailure(Exception):
    def __init__(self, status: int, detail: str) -> None:
        super().__init__(f"HTTP {status}: {detail}")
        self.status = status
        self.detail = detail


# ---------------------------------------------------------------------------
# 1. 카탈로그 — seed_manicafe_demo.sh와 동일 12종 + 시즌 신메뉴 1종(운영 24일차 추가)
# ---------------------------------------------------------------------------

CATALOG = [
    # item_id, name, unit_price, cost, category, initial_stock, low_stock_threshold
    ("menu_americano", "아메리카노", 3500, 800, "coffee", 0, 5),  # 원두 수급 이슈로 계속 품절 상태(의도됨)
    ("menu_latte", "라떼", 4500, 1000, "coffee", 130, 10),
    ("menu_cappuccino", "카푸치노", 4700, 1100, "coffee", 110, 10),
    ("menu_espresso", "에스프레소", 3000, 700, "coffee", 150, 10),
    ("menu_coldbrew", "콜드브루", 5200, 1200, "coffee", 95, 8),
    ("menu_matcha_latte", "말차라떼", 5200, 1200, "tea", 75, 8),
    ("menu_chai_latte", "차이라떼", 4800, 1100, "tea", 60, 8),
    ("menu_muffin", "블루베리 머핀", 2800, 500, "bakery", 65, 10),
    ("menu_croissant", "크루아상", 3000, 600, "bakery", 58, 10),
    ("menu_sandwich", "햄&치즈 샌드위치", 6500, 1800, "sandwich", 48, 5),
    ("menu_smoothie", "딸기 스무디", 5500, 1300, "smoothie", 50, 6),
    ("menu_cake", "시즌 케이크(딸기)", 6000, 2000, "dessert", 40, 5),
]
SEASONAL_ITEM = ("menu_grapefruit_ade", "아이스 자몽에이드", 5000, 1100, "ade", 60, 8)
SEASONAL_INTRO_DAY = 24  # 운영 24일차부터 판매 시작

# 위 카탈로그(계절 메뉴 제외)에 대응하는 판매 가중치. 아메리카노는 재고 0이라
# 계속 "품절" 실패를 겪는 손님을 재현하려고 낮은 가중치로 남겨둔다.
ITEM_WEIGHTS = {
    "menu_americano": 4,
    "menu_latte": 20,
    "menu_cappuccino": 15,
    "menu_espresso": 10,
    "menu_coldbrew": 10,
    "menu_matcha_latte": 8,
    "menu_chai_latte": 6,
    "menu_muffin": 8,
    "menu_croissant": 7,
    "menu_sandwich": 6,
    "menu_smoothie": 6,
    "menu_cake": 5,
}
SEASONAL_WEIGHT = 10

# 5일 간격 입고되는 델리버리 — 아메리카노는 의도적으로 제외.
RESTOCK_DAYS = {5, 10, 15, 20, 25, 30, 35}
RESTOCK_DELTA = {
    "menu_latte": 55, "menu_cappuccino": 45, "menu_espresso": 60, "menu_coldbrew": 38,
    "menu_matcha_latte": 30, "menu_chai_latte": 24, "menu_muffin": 28, "menu_croissant": 25,
    "menu_sandwich": 20, "menu_smoothie": 22, "menu_cake": 16, "menu_grapefruit_ade": 30,
}

# ---------------------------------------------------------------------------
# 2. 고객 — 단골 6명(원래 데모와 동일) + 신규 10명
# ---------------------------------------------------------------------------

CORE_CUSTOMERS = [
    ("cust_minji", "김민지", "010-1234-5678"),
    ("cust_junho", "이준호", "010-2345-6789"),
    ("cust_soyeon", "박소연", "010-3456-7890"),
    ("cust_donghyun", "최동현", "010-4567-8901"),
    ("cust_yuna", "정유나", "010-5678-9012"),
    ("cust_taemin", "강태민", "010-6789-0123"),
]
OCCASIONAL_CUSTOMERS = [
    ("cust_haeun", "이하은", "010-1111-2222"),
    ("cust_jihoon", "오지훈", "010-2222-3333"),
    ("cust_yeonwoo", "서연우", "010-3333-4444"),
    ("cust_gaeul", "한가을", "010-4444-5555"),
    ("cust_subin", "배수빈", "010-5555-6666"),
    ("cust_minjae", "조민재", "010-6666-7777"),
    ("cust_areum", "윤아름", "010-7777-8888"),
    ("cust_taeyang", "임태양", "010-8888-9999"),
    ("cust_daeun", "신다은", "010-9999-0000"),
    ("cust_bora", "황보라", "010-0000-1111"),
]

# 주문 배정 시 단골이 occasional보다 3배 자주 뽑히고, 30%는 손님 정보 없는 워크인.
WALKIN_PROBABILITY = 0.30
CORE_WEIGHT = 3
OCCASIONAL_WEIGHT = 1

# ---------------------------------------------------------------------------
# 3. 시간대/요일 가중치 — 카페 통행 패턴(08:00~22:00 영업)
# ---------------------------------------------------------------------------

# (start_hour, end_hour, weight)
HOUR_CLUSTERS = [
    (8, 10, 3.0),
    (10, 12, 2.0),
    (12, 14, 3.0),
    (14, 17, 2.5),
    (17, 19, 2.5),
    (19, 22, 1.5),
]
# 월=0 ... 일=6
DOW_MULTIPLIER = {0: 0.80, 1: 0.85, 2: 0.90, 3: 0.95, 4: 1.15, 5: 1.35, 6: 1.25}
BASE_DAILY_ORDERS = 20


def ramp_multiplier(day_index: int) -> float:
    """개업 초기 소프트오픈(0.45배)에서 열흘에 걸쳐 정상화, 이후 입소문으로 완만히 성장."""
    if day_index < 10:
        return 0.45 + 0.055 * day_index
    return min(1.15, 1.0 + 0.005 * (day_index - 10))


def pick_order_time(day: datetime) -> datetime:
    cluster = random.choices(HOUR_CLUSTERS, weights=[c[2] for c in HOUR_CLUSTERS])[0]
    start_h, end_h, _ = cluster
    total_minutes = (end_h - start_h) * 60
    offset = random.randint(0, total_minutes - 1)
    return day.replace(hour=start_h, minute=0, second=0, microsecond=0) + timedelta(minutes=offset)


def pick_customer() -> str | None:
    if random.random() < WALKIN_PROBABILITY:
        return None
    pool = [c[0] for c in CORE_CUSTOMERS] * CORE_WEIGHT + [c[0] for c in OCCASIONAL_CUSTOMERS] * OCCASIONAL_WEIGHT
    return random.choice(pool)


def _weighted_sample_without_replacement(weights: dict[str, float], k: int) -> list[str]:
    """random.sample()은 가중치를 받지 않으므로(균등 추출) 직접 구현한다 —
    매번 남은 후보에서 random.choices(weights=...)로 하나씩 뽑아 제거하는 방식."""
    remaining = dict(weights)
    picks: list[str] = []
    for _ in range(min(k, len(remaining))):
        keys = list(remaining.keys())
        chosen = random.choices(keys, weights=[remaining[key] for key in keys], k=1)[0]
        picks.append(chosen)
        del remaining[chosen]
    return picks


def pick_line_items(seasonal_available: bool) -> list[dict]:
    weights = dict(ITEM_WEIGHTS)
    if seasonal_available:
        weights[SEASONAL_ITEM[0]] = SEASONAL_WEIGHT

    n_items = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
    item_ids = _weighted_sample_without_replacement(weights, n_items)
    line_items = []
    for item_id in item_ids:
        qty = random.choices([1, 2, 3], weights=[80, 18, 2])[0]
        line_items.append({"item_id": item_id, "quantity": qty})
    return line_items


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def main() -> None:
    now = datetime.now(timezone.utc)
    opening_day = (now - timedelta(days=OPERATING_DAYS - 1)).replace(hour=0, minute=0, second=0, microsecond=0)

    print(f"== 마니카페 연남점 시드: {opening_day.date()} 개업 ~ {now.date()} (오늘, {OPERATING_DAYS}일 운영) ==")

    print("-- 카탈로그 등록 (12종 + 시즌 메뉴는 나중에 추가) --")
    for item_id, name, price, cost, category, stock, threshold in CATALOG:
        api("POST", "/catalog/items", {
            "item_id": item_id, "name": name, "unit_price": price, "cost": cost,
            "category": category, "initial_stock": stock, "low_stock_threshold": threshold,
        })

    print(f"-- 고객 등록 ({len(CORE_CUSTOMERS) + len(OCCASIONAL_CUSTOMERS)}명) --")
    for customer_id, name, phone in CORE_CUSTOMERS + OCCASIONAL_CUSTOMERS:
        api("POST", "/customers", {"customer_id": customer_id, "name": name, "phone": phone})

    total_orders = 0
    total_paid = 0
    total_stockout_skips = 0
    completed_payment_ids: list[str] = []
    seasonal_introduced = False

    for day_index in range(OPERATING_DAYS):
        day = opening_day + timedelta(days=day_index)
        dow = day.weekday()

        if day_index == SEASONAL_INTRO_DAY and not seasonal_introduced:
            item_id, name, price, cost, category, stock, threshold = SEASONAL_ITEM
            api("POST", "/catalog/items", {
                "item_id": item_id, "name": name, "unit_price": price, "cost": cost,
                "category": category, "initial_stock": stock, "low_stock_threshold": threshold,
            })
            seasonal_introduced = True
            print(f"   [{day.date()}] 시즌 메뉴 출시: {name}")

        if day_index in RESTOCK_DAYS:
            for item_id, delta in RESTOCK_DELTA.items():
                if item_id == SEASONAL_ITEM[0] and not seasonal_introduced:
                    continue
                try:
                    api("POST", f"/inventory/{item_id}/adjust", {"delta": delta, "reason": "정기 입고"})
                except HTTPFailure:
                    pass
            print(f"   [{day.date()}] 주간 입고 완료")

        target = round(BASE_DAILY_ORDERS * DOW_MULTIPLIER[dow] * ramp_multiplier(day_index) * random.uniform(0.85, 1.15))

        for _ in range(max(target, 0)):
            order_time = pick_order_time(day)
            if order_time > now:
                continue  # 오늘 미래 시각은 건너뜀
            customer_id = pick_customer()
            line_items = pick_line_items(seasonal_available=seasonal_introduced)

            try:
                order = api("POST", "/orders", {
                    "line_items": line_items, "customer_id": customer_id, "created_at": iso(order_time),
                })
            except HTTPFailure:
                continue  # 카탈로그 조회 실패 등 — 건너뜀
            total_orders += 1

            payment_time = order_time + timedelta(minutes=random.randint(0, 2))
            try:
                payment = api("POST", "/payments", {
                    "order_id": order["order_id"], "created_at": iso(payment_time),
                })
                total_paid += 1
                completed_payment_ids.append(payment["payment_id"])
            except HTTPFailure as exc:
                if exc.status == 409:
                    total_stockout_skips += 1
                # 결제 실패(재고 부족 등) — 실제 매장이라면 응대 직원이 취소 처리했을
                # 것이므로, OPEN 상태로 방치하지 않고 CANCELED로 정리한다.
                try:
                    api("PATCH", f"/orders/{order['order_id']}", {"status": "CANCELED"})
                except HTTPFailure:
                    pass

        if (day_index + 1) % 7 == 0 or day_index == OPERATING_DAYS - 1:
            print(f"   [{day.date()}] 누적 주문 {total_orders}건 / 결제 {total_paid}건 (품절 스킵 {total_stockout_skips}건)")

    print(f"-- 주문/결제 생성 완료: 총 {total_orders}건 주문, {total_paid}건 결제 --")

    print("-- 환불 데모 (전액 4건 + 부분 3건, 여러 주에 걸쳐 분산) --")
    random.shuffle(completed_payment_ids)
    refund_targets = completed_payment_ids[:7]
    full_reasons = ["고객 단순 변심", "주문 실수(다른 메뉴 요청)", "음료에서 이물질 발견", "직원 실수로 중복 결제"]
    partial_reasons = ["케이크 일부 파손", "샌드위치 빵 눅눅함 — 부분 보상", "스무디 양 부족 컴플레인"]
    for i, payment_id in enumerate(refund_targets):
        try:
            if i < 4:
                api("POST", f"/payments/{payment_id}/refund", {"reason": full_reasons[i % len(full_reasons)]})
            else:
                api("POST", f"/payments/{payment_id}/refund", {
                    "amount": random.choice([1500, 2000, 2500]),
                    "reason": partial_reasons[(i - 4) % len(partial_reasons)],
                })
        except HTTPFailure:
            continue
    print(f"   환불 처리 시도 {len(refund_targets)}건")

    print("-- 예약 등록 (카페 단체석/스터디룸 등 8건, 과거~향후 1주) --")
    reservation_services = ["단체석(4인) 예약", "스터디룸 예약", "생일파티 케이크 예약", "단체석(6인) 예약", "노트북 작업석 예약"]
    reservation_customers = [c[0] for c in CORE_CUSTOMERS]
    for offset_days in [-5, -3, -1, 0, 1, 2, 4, 7]:
        resv_time = (now + timedelta(days=offset_days)).replace(
            hour=random.choice([11, 14, 16, 19]), minute=random.choice([0, 30]), second=0, microsecond=0
        )
        body = {
            "customer_id": random.choice(reservation_customers),
            "datetime": iso(resv_time),
            "service": random.choice(reservation_services),
        }
        try:
            resv = api("POST", "/reservations", body)
            if offset_days in (-5, -3) and random.random() < 0.4:
                api("PATCH", f"/reservations/{resv['reservation_id']}", {"status": "CANCELED"})
        except HTTPFailure:
            continue
    print("   예약 등록 완료")

    print("== 완료 ==")
    print(f"확인: curl -s -H \"X-API-Key: {KEY}\" \"{BASE}/v1/stores/{STORE}/reports/sales/daily?days=30\" | python3 -m json.tool")
    print(f"확인: curl -s -H \"X-API-Key: {KEY}\" \"{BASE}/v1/stores/{STORE}/inventory/menu_americano\"  # stock_quantity == 0 이어야 함")


if __name__ == "__main__":
    try:
        main()
    except HTTPFailure as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        sys.exit(1)
