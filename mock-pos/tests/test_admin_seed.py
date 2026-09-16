from datetime import datetime, timezone

from fastapi.testclient import TestClient

from mock_pos.main import app

client = TestClient(app)
HEADERS = {"X-API-Key": "test-key"}


def test_quick_seed_fills_catalog_customers_and_demo_orders():
    store = "store_test_admin_quick"
    resp = client.post(f"/v1/stores/{store}/admin/seed", headers=HEADERS, json={"mode": "quick"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "quick"
    assert body["catalog_items"] == 12
    assert body["customers"] == 6
    assert body["orders"] == 23  # 21건 + 환불용 2건(seed_manicafe_demo.sh와 동일)
    assert body["days_simulated"] == 1

    americano = client.get(f"/v1/stores/{store}/inventory/menu_americano", headers=HEADERS).json()
    assert americano["stock_quantity"] == 0  # 라이브 데모 대본용 결품 상태 재현

    settlement = client.get(
        f"/v1/stores/{store}/reports/settlement", headers=HEADERS, params={"period": "all"}
    ).json()
    assert settlement["refunded_count"] == 1
    assert settlement["partial_refund_count"] == 1


def test_quick_seed_is_repeatable_without_409():
    """멱등적이지 않은 curl 시드 스크립트와 달리, 버튼 재클릭은 항상 초기화 후
    다시 채운다 — 재실행해도 카탈로그 409가 나면 안 된다."""
    store = "store_test_admin_repeat"
    first = client.post(f"/v1/stores/{store}/admin/seed", headers=HEADERS, json={"mode": "quick"})
    second = client.post(f"/v1/stores/{store}/admin/seed", headers=HEADERS, json={"mode": "quick"})
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["orders"] == first.json()["orders"]


def test_month_seed_fills_multiple_distinct_days_with_sales():
    store = "store_test_admin_month"
    resp = client.post(f"/v1/stores/{store}/admin/seed", headers=HEADERS, json={"mode": "month"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "month"
    assert body["days_simulated"] > 30
    assert body["orders"] > 200
    assert body["payments"] > 0  # 재고 소진 없이 대부분 결제까지 이어져야 한다(재입고 없으면 0에 가까움)

    daily = client.get(
        f"/v1/stores/{store}/reports/sales/daily", headers=HEADERS, params={"days": 7}
    ).json()
    assert len(daily) == 7
    assert sum(d["order_count"] for d in daily) > 0  # 최근 7일 중 최소 일부는 매출이 있어야 한다
    assert daily[-1]["order_count"] > 0  # 오늘(가장 마지막 날짜)도 0건이면 안 된다 — KST 변환 버그 회귀 방지

    today_sales = client.get(
        f"/v1/stores/{store}/reports/sales", headers=HEADERS, params={"period": "today"}
    ).json()
    assert today_sales["order_count"] > 0
    assert today_sales["total_sales"] > 0


def test_month_seed_engineers_a_variety_of_dashboard_insight_conditions():
    """대시보드 "오늘 확인해야 할 것"이 최소 4가지 서로 다른 종류로 뜨도록,
    한 달 시뮬레이션이 보장해야 하는 데이터 상태를 직접 확인한다(재고 위험·
    재고 부족·소진 임박/예상·이탈 위험 단골·오늘 예약). 무작위 요소가 섞여
    있으므로 여러 번 반복해 매번 성립하는지 확인한다."""
    for i in range(5):
        store = f"store_test_admin_insights_{i}"
        client.post(f"/v1/stores/{store}/admin/seed", headers=HEADERS, json={"mode": "month"})

        inventory = client.get(f"/v1/stores/{store}/inventory", headers=HEADERS).json()
        by_id = {item["item_id"]: item for item in inventory}

        critical = [
            it for it in inventory
            if it["item_id"] != "menu_americano" and it["stock_quantity"] <= it["low_stock_threshold"] * 0.5
        ]
        low = [
            it for it in inventory
            if it["item_id"] != "menu_americano"
            and it["low_stock_threshold"] * 0.5 < it["stock_quantity"] <= it["low_stock_threshold"]
        ]
        assert critical, f"[{store}] 재고 위험 품목이 하나도 없음"
        assert low, f"[{store}] 재고 부족 품목이 하나도 없음"

        top_week = client.get(
            f"/v1/stores/{store}/reports/top-items", headers=HEADERS, params={"period": "week", "limit": 20}
        ).json()
        qty_by_item = {t["item_id"]: t["quantity"] for t in top_week}
        eta_hit = False
        for item_id, inv in by_id.items():
            if item_id == "menu_americano" or inv["stock_quantity"] <= inv["low_stock_threshold"]:
                continue
            velocity = qty_by_item.get(item_id, 0) / 7
            if velocity > 0 and inv["stock_quantity"] / velocity <= 3:
                eta_hit = True
                break
        assert eta_hit, f"[{store}] 소진 임박/예상 밴드에 들어가는 품목이 하나도 없음"

        reservations = client.get(f"/v1/stores/{store}/reservations", headers=HEADERS).json()
        assert reservations, f"[{store}] 오늘 예약이 하나도 없음"

        repeat_customers = client.get(
            f"/v1/stores/{store}/reports/repeat-customers",
            headers=HEADERS,
            params={"period": "all", "min_orders": 2},
        ).json()
        now = datetime.now(timezone.utc)
        churn_risk = [
            c for c in repeat_customers
            if c["order_count"] >= 3
            and c["last_order_at"] is not None
            and (now - datetime.fromisoformat(c["last_order_at"])).days >= 14
        ]
        assert churn_risk, f"[{store}] 이탈 위험 후보(3건 이상 주문 + 14일 이상 재방문 없음)가 하나도 없음"


def test_seed_rejects_unknown_mode():
    store = "store_test_admin_badmode"
    resp = client.post(f"/v1/stores/{store}/admin/seed", headers=HEADERS, json={"mode": "bogus"})
    assert resp.status_code == 400


def test_seed_requires_api_key():
    resp = client.post("/v1/stores/store_test_admin_noauth/admin/seed", json={"mode": "quick"})
    assert resp.status_code == 401


def test_seed_does_not_affect_other_stores():
    other_store = "store_test_admin_untouched"
    client.post(
        f"/v1/stores/{other_store}/catalog/items",
        headers=HEADERS,
        json={"item_id": "menu_keepme", "name": "지켜야 할 품목", "unit_price": 1000, "initial_stock": 3},
    )

    target_store = "store_test_admin_target"
    client.post(f"/v1/stores/{target_store}/admin/seed", headers=HEADERS, json={"mode": "quick"})

    kept = client.get(f"/v1/stores/{other_store}/catalog/items/menu_keepme", headers=HEADERS)
    assert kept.status_code == 200
    assert kept.json()["name"] == "지켜야 할 품목"
