from pathlib import Path

import pytest

PAGES = ["/support", "/orders", "/inventory", "/dashboard"]


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
