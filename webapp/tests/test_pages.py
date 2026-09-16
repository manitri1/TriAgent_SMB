import re
from pathlib import Path

import pytest

PAGES = [
    "/support", "/orders", "/inventory", "/reservations", "/dashboard", "/live-demo", "/live-demo/customer",
    "/customer", "/customer/faq", "/customer/order", "/customer/reservation",
]


@pytest.mark.parametrize("path", PAGES)
def test_page_returns_html(client, auth_headers, path):
    resp = client.get(path, headers=auth_headers)
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_index_redirects_to_dashboard(client, auth_headers):
    resp = client.get("/", headers=auth_headers, follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/dashboard"


def test_dashboard_page_has_chart_and_nav_markers(client, auth_headers):
    resp = client.get("/dashboard", headers=auth_headers)
    assert "chart.js" in resp.text.lower()
    assert "고객 문의" in resp.text
    assert "재고 관리" in resp.text


def test_inventory_page_has_enabled_restock_form(client, auth_headers):
    resp = client.get("/inventory", headers=auth_headers)
    assert "재입고 요청" in resp.text
    assert 'id="restock-form"' in resp.text
    assert "disabled" not in resp.text


def test_support_page_has_chat_widget(client, auth_headers):
    resp = client.get("/support", headers=auth_headers)
    assert "initChatWidget" in resp.text
    assert "customer-service-agent" in resp.text


def test_support_page_has_demo_queue(client, auth_headers):
    resp = client.get("/support", headers=auth_headers)
    assert "demoBarId" in resp.text
    assert "demoQueue" in resp.text
    assert '"support-demo-bar"' in resp.text
    assert '<div id="support-demo-bar" class="demo-bar"></div>' in resp.text


def test_orders_page_has_item_picker_and_chat_and_recent_orders(client, auth_headers):
    resp = client.get("/orders", headers=auth_headers)
    assert "품목으로 주문 만들기" in resp.text
    assert 'src="/static/chat.js?v=' in resp.text
    assert 'src="/static/orders.js?v=' in resp.text
    assert "최근 주문" in resp.text


def test_orders_js_targets_coordinator():
    text = (Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "orders.js").read_text(
        encoding="utf-8"
    )
    assert 'profile: "coordinator"' in text


def test_orders_page_has_demo_queue(client, auth_headers):
    resp = client.get("/orders", headers=auth_headers)
    assert '<div id="orders-demo-bar" class="demo-bar"></div>' in resp.text


def test_orders_js_demo_queue_includes_refund_scenario():
    """환불 데모 항목이 있어야 HITL 게이트 3(환불/취소 승인)을 시연할 수 있다."""
    text = (Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "orders.js").read_text(
        encoding="utf-8"
    )
    assert "demoQueue" in text
    assert "환불" in text


def test_inventory_restock_js_targets_coordinator():
    """재입고 요청이 inventory-agent가 아니라 coordinator로 가야 HITL 게이트 2가
    발동할 기회를 갖는다(curried-percolating-ocean.md "설계 편차" 참고)."""
    text = (Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "inventory.js").read_text(
        encoding="utf-8"
    )
    assert 'profile: "coordinator"' in text


def test_inventory_page_has_demo_queue(client, auth_headers):
    resp = client.get("/inventory", headers=auth_headers)
    assert '<div id="inventory-demo-bar" class="demo-bar"></div>' in resp.text


def test_inventory_js_has_restock_demo_queue():
    text = (Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "inventory.js").read_text(
        encoding="utf-8"
    )
    assert "RESTOCK_DEMO_QUEUE" in text


def test_dashboard_page_has_demo_hint(client, auth_headers):
    resp = client.get("/dashboard", headers=auth_headers)
    assert "demo-bar" in resp.text
    assert "새로고침해서 확인" in resp.text


def test_reservations_page_has_chat_and_table(client, auth_headers):
    resp = client.get("/reservations", headers=auth_headers)
    assert 'id="reservations-sent-prompt"' in resp.text
    assert 'id="reservations-result"' in resp.text
    assert 'src="/static/chat.js?v=' in resp.text
    assert 'src="/static/reservations.js?v=' in resp.text
    assert "오늘 예약" in resp.text


def test_reservations_page_has_demo_queue(client, auth_headers):
    resp = client.get("/reservations", headers=auth_headers)
    assert '<div id="reservations-demo-bar" class="demo-bar"></div>' in resp.text


def test_demo_queues_cover_manicafe_day_in_life_story():
    """course/260912_마니카페_사장님의_하루.md의 타임라인 중 webapp 화면이 있는 4곳(예약·
    재고·고객문의·주문접수)은 각 화면 데모 큐에서 시연 가능해야 한다."""
    base = Path(__file__).resolve().parent.parent / "webapp_bff"
    support_html = (base / "templates" / "support.html").read_text(encoding="utf-8")
    orders_js = (base / "static" / "orders.js").read_text(encoding="utf-8")
    inventory_js = (base / "static" / "inventory.js").read_text(encoding="utf-8")
    reservations_js = (base / "static" / "reservations.js").read_text(encoding="utf-8")

    assert "11:20 단체 주문 문의" in support_html
    assert "17:10 컴플레인" in support_html
    assert "12:00 점심 피크 주문" in orders_js
    assert "09:10 원두 결품 발견" in inventory_js
    assert "07:00 전화 예약 응대" in reservations_js


def test_reservations_js_targets_coordinator():
    """reservation-agent는 승인을 요청할 수단이 없어 직접 호출하면 HITL이 조용히
    무력화된다 — 예약 쓰기도 반드시 coordinator로 수렴해야 한다."""
    text = (Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "reservations.js").read_text(
        encoding="utf-8"
    )
    assert 'profile: "coordinator"' in text


def test_nav_includes_reservations_link(client, auth_headers):
    resp = client.get("/dashboard", headers=auth_headers)
    assert 'href="/reservations"' in resp.text
    assert "예약 관리" in resp.text


def test_nav_includes_live_demo_link(client, auth_headers):
    resp = client.get("/dashboard", headers=auth_headers)
    assert 'href="/live-demo"' in resp.text
    assert "사장님 라이브" in resp.text


def test_live_demo_page_has_step_queue_and_log(client, auth_headers):
    resp = client.get("/live-demo", headers=auth_headers)
    assert 'id="demo-day-steps"' in resp.text
    assert 'id="demo-day-detail"' in resp.text
    assert 'id="demo-day-thread"' in resp.text
    assert 'src="/static/live_demo.js?v=' in resp.text


def test_live_demo_js_has_all_12_timeline_steps():
    """docs/21-live-demo-plan.md P2 표의 12개 타임라인(①~⑫)이 전부 큐에 있어야
    발표자가 한 화면에서 하루 전체를 시연할 수 있다."""
    text = (Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "live_demo.js").read_text(
        encoding="utf-8"
    )
    assert text.count('time: "') == 12
    for label in [
        "05:30", "06:30", "07:00", "09:10", "11:20", "12:00",
        "14:30", "15:30", "17:10", "19:40", "21:00", "23:00",
    ]:
        assert f'time: "{label}"' in text


def test_live_demo_js_only_uses_allowed_profiles():
    """/api/agent/message는 coordinator/customer-service-agent만 허용한다
    (agent.py) — 그 외 profile을 큐에 넣으면 서버가 조용히 coordinator로
    바꿔치기해 발표자가 의도한 에이전트가 응답하지 않는 것처럼 보인다."""
    text = (Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "live_demo.js").read_text(
        encoding="utf-8"
    )
    profiles = set(re.findall(r'profile: "([^"]+)"', text))
    assert profiles <= {"coordinator", "customer-service-agent"}
    assert profiles  # 비어있지 않아야 함(최소 하나는 실제로 채팅 전송함)


def test_live_demo_js_result_links_point_to_real_pages():
    text = (Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "live_demo.js").read_text(
        encoding="utf-8"
    )
    hrefs = set(re.findall(r'href: "([^"]+)"', text))
    assert hrefs <= {"/inventory", "/reservations", "/support", "/orders", "/dashboard"}
    assert hrefs


def test_live_demo_js_result_panel_fetches_pos_proxy_not_write_routes():
    """결과 패널은 /api/pos/*(읽기 전용 프록시)만 호출해야 한다 — 쓰기 경로가
    섞여 들어가면 pos_proxy.py의 "조회 전용" 원칙(agent.py로만 위임)이 webapp
    JS 쪽에서부터 깨진다."""
    text = (Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "live_demo.js").read_text(
        encoding="utf-8"
    )
    fetch_paths = re.findall(r'fetch\(`?"?(/api/[^`"\s)]*)', text)
    assert fetch_paths
    for path in fetch_paths:
        assert path.startswith("/api/pos/") or path.startswith("/api/agent/message")


def test_live_demo_js_result_kinds_match_available_pos_proxy_endpoints():
    text = (Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "live_demo.js").read_text(
        encoding="utf-8"
    )
    kinds = set(re.findall(r'kind: "([^"]+)"', text))
    assert kinds == {"inventory", "orders", "reservations", "sales", "settlement", "support-note"}


def test_nav_includes_customer_live_demo_link(client, auth_headers):
    resp = client.get("/dashboard", headers=auth_headers)
    assert 'href="/live-demo/customer"' in resp.text
    assert "고객 라이브" in resp.text


@pytest.mark.parametrize("path", ["/support", "/orders", "/inventory", "/reservations", "/dashboard", "/live-demo", "/live-demo/customer"])
def test_staff_nav_includes_customer_screen_link(client, auth_headers, path):
    """스태프 화면 어디에서든 메뉴바에서 바로 /customer(고객 화면)로 전환할 수
    있어야 한다 — view-switch pill만으로는 발견성이 낮다는 피드백에 따라
    아이콘 메뉴에도 동일한 링크를 추가했다."""
    resp = client.get(path, headers=auth_headers)
    assert 'href="/customer"' in resp.text
    assert "고객 화면" in resp.text


def test_customer_live_demo_page_has_step_queue_and_log(client, auth_headers):
    resp = client.get("/live-demo/customer", headers=auth_headers)
    assert 'id="demo-day-steps"' in resp.text
    assert 'id="demo-day-detail"' in resp.text
    assert 'id="demo-day-thread"' in resp.text
    assert 'src="/static/customer_live_demo.js?v=' in resp.text


def test_customer_live_demo_js_has_all_7_steps():
    text = (
        Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "customer_live_demo.js"
    ).read_text(encoding="utf-8")
    assert text.count('time: "') == 7
    for label in ["08:15", "08:20", "08:30", "12:40", "13:10", "18:50", "19:05"]:
        assert f'time: "{label}"' in text


def test_customer_live_demo_js_only_uses_allowed_profiles():
    """/api/agent/message는 coordinator/customer-service-agent만 허용한다
    (agent.py) — live_demo.js와 동일한 제약."""
    text = (
        Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "customer_live_demo.js"
    ).read_text(encoding="utf-8")
    profiles = set(re.findall(r'profile: "([^"]+)"', text))
    assert profiles <= {"coordinator", "customer-service-agent"}
    assert profiles


def test_customer_live_demo_js_result_panel_fetches_pos_proxy_not_write_routes():
    text = (
        Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "customer_live_demo.js"
    ).read_text(encoding="utf-8")
    fetch_paths = re.findall(r'fetch\(`?"?(/api/[^`"\s)]*)', text)
    assert fetch_paths
    for path in fetch_paths:
        assert path.startswith("/api/pos/") or path.startswith("/api/agent/message")


def test_customer_live_demo_js_result_kinds_match_available_pos_proxy_endpoints():
    text = (
        Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "customer_live_demo.js"
    ).read_text(encoding="utf-8")
    kinds = set(re.findall(r'kind: "([^"]+)"', text))
    assert kinds <= {"inventory", "orders", "reservations", "sales", "settlement", "support-note"}
    assert kinds


def test_home_page_has_view_switch_cards(client, auth_headers):
    resp = client.get("/home", headers=auth_headers)
    assert 'href="/customer"' in resp.text
    assert 'href="/live-demo/customer"' in resp.text
    assert "고객 화면" in resp.text
    assert "손님 라이브 데모" in resp.text


def test_customer_home_page_uses_customer_mode(client, auth_headers):
    resp = client.get("/customer", headers=auth_headers)
    assert 'class="mode-customer"' in resp.text
    assert "customer-preview-banner" in resp.text


def test_customer_faq_page_has_chat_widget(client, auth_headers):
    resp = client.get("/customer/faq", headers=auth_headers)
    assert "initChatWidget" in resp.text
    assert "customer-service-agent" in resp.text


def test_customer_order_page_has_wizard_steps(client, auth_headers):
    resp = client.get("/customer/order", headers=auth_headers)
    assert 'id="order-menu-grid"' in resp.text
    assert 'id="order-cart-step"' in resp.text
    assert 'id="order-checkout-step"' in resp.text


def test_customer_order_js_only_uses_allowed_profile():
    text = (Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "customer_order.js").read_text(
        encoding="utf-8"
    )
    assert '"coordinator"' in text
    assert "customer-service-agent" not in text


def test_customer_reservation_page_has_wizard_steps(client, auth_headers):
    resp = client.get("/customer/reservation", headers=auth_headers)
    assert 'id="reservation-date-grid"' in resp.text
    assert 'id="reservation-time-grid"' in resp.text
    assert 'id="reservation-party-grid"' in resp.text


def test_customer_reservation_js_only_uses_allowed_profile():
    text = (
        Path(__file__).resolve().parent.parent / "webapp_bff" / "static" / "customer_reservation.js"
    ).read_text(encoding="utf-8")
    assert '"coordinator"' in text
    assert "customer-service-agent" not in text
