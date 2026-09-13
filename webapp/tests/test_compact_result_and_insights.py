import re
from pathlib import Path

import pytest

STATIC = Path(__file__).resolve().parent.parent / "webapp_bff" / "static"


def _read(name: str) -> str:
    return (STATIC / name).read_text(encoding="utf-8")


def test_common_js_defines_shared_helpers():
    text = _read("common.js")
    assert "function renderCompactResult" in text
    assert "function getConversationId" in text
    assert "function renderSentPrompt" in text


def test_inventory_js_shows_sent_prompt_before_sending():
    """"재입고 요청" 버튼을 눌렀을 때 실제로 보낸 문구가 화면에 보여야 한다."""
    text = _read("inventory.js")
    assert "renderSentPrompt(" in text


def test_common_js_insight_board_shows_sent_prompt_on_approve_and_comment():
    """"승인"/"의견 입력" 버튼도 보낸 문구를 보여줘야 한다 — 이 로직은 dashboard.js
    전용이 아니라 common.js의 createInsightBoard로 일반화되어 재고/예약 등 다른
    화면도 재사용한다."""
    text = _read("common.js")
    assert "function createInsightBoard" in text
    assert "renderSentPrompt(" in text
    assert "sentCache" in text


def test_chat_js_delegates_conversation_id_to_common():
    text = _read("chat.js")
    assert "getConversationId(storageKey)" in text


def test_inventory_js_uses_compact_result_helper_not_raw_dump():
    text = _read("inventory.js")
    assert "renderCompactResult(" in text
    assert "restock-reply--" not in text  # 예전 원문 텍스트 덤프 클래스는 완전히 제거되어야 함


def test_orders_js_uses_compact_result_helper_for_picker_confirm():
    text = _read("orders.js")
    assert "renderCompactResult(" in text
    assert "awaitingPickerConfirm" in text


def test_insight_rules_assign_approve_messages_to_five_actionable_rules():
    """재고 4종 + 노쇼 규칙은 common.js의 computeInventoryInsights/
    computeReservationNoShowInsights로 옮겨져 재고관리/예약관리 화면도
    재사용한다 — dashboard.js는 이제 진단성 규칙(실행 가능한 조치가 없는 것)만
    직접 정의한다."""
    common_text = _read("common.js")
    for key in ("stock-critical", "stock-low", "stock-eta-imminent", "stock-eta-soon", "reservation-noshow"):
        assert f'insightKey: "{key}"' in common_text
        assert "approveMessage" in common_text
    dashboard_text = _read("dashboard.js")
    # 진단성 정보 규칙들은 insightKey는 있어도 approveMessage는 없어야 한다(실행 가능한 조치가 없음).
    for key in ("sales-trend-crash", "refund-rate-critical", "margin-rate-low", "churn-risk", "today-reservations", "margin-laggard"):
        assert f'insightKey: "{key}"' in dashboard_text


def test_insight_board_actions_only_target_coordinator():
    """createInsightBoard의 기본 profile은 coordinator여야 하고, dashboard.js
    호출부는 이를 다른 profile로 덮어쓰지 않아야 한다 — 그래야 승인/의견 입력이
    HITL 게이트를 우회하지 않는다."""
    common_text = _read("common.js")
    assert 'profile = "coordinator"' in common_text
    dashboard_text = _read("dashboard.js")
    profiles = set(re.findall(r'profile:\s*"([^"]+)"', dashboard_text))
    assert profiles <= {"coordinator"}


def test_common_js_has_approve_and_comment_ui():
    text = _read("common.js")
    assert "insight-approve-btn" in text
    assert "insight-comment-toggle" in text
    assert "insight-comment-submit" in text
    assert "createInsightBoard" in text


def test_dashboard_html_loads_common_before_dashboard_js(client, auth_headers):
    resp = client.get("/dashboard", headers=auth_headers)
    common_pos = resp.text.find("/static/common.js")
    dashboard_pos = resp.text.find("/static/dashboard.js")
    assert common_pos != -1 and dashboard_pos != -1
    assert common_pos < dashboard_pos


@pytest.mark.parametrize(
    "path,js_file",
    [("/live-demo", "live_demo.js"), ("/live-demo/customer", "customer_live_demo.js")],
)
def test_live_demo_html_loads_common_before_its_js(client, auth_headers, path, js_file):
    """live_demo.js/customer_live_demo.js가 결과 요약에 renderSentPrompt/
    renderCompactResult(common.js)를 쓰므로, common.js가 먼저 로드돼야 한다."""
    resp = client.get(path, headers=auth_headers)
    common_pos = resp.text.find("/static/common.js")
    js_pos = resp.text.find(f"/static/{js_file}")
    assert common_pos != -1 and js_pos != -1
    assert common_pos < js_pos


@pytest.mark.parametrize("js_file", ["live_demo.js", "customer_live_demo.js"])
def test_live_demo_detail_has_result_summary_containers(js_file):
    """장면을 전송한 결과(보낸 요청 + 응답 요약)가 오른쪽 상세 패널 안에 남아있어야
    한다 — 채팅 로그로만 보여주면 자동 진행 없이는 결과를 놓치기 쉽다. 이 컨테이너는
    renderDetail()이 클라이언트에서 채워 넣으므로 정적 HTML이 아니라 JS 소스에서
    확인한다."""
    text = _read(js_file)
    assert 'id="demo-day-sent"' in text
    assert 'id="demo-day-summary"' in text
    assert "renderSentPrompt(" in text
    assert "renderCompactResult(" in text


@pytest.mark.parametrize("js_file", ["live_demo.js", "customer_live_demo.js"])
def test_live_demo_no_longer_auto_advances_after_response(js_file):
    """응답을 받은 뒤 결과 요약이 남아있어야 하므로, 더 이상 자동으로 다음 장면(advance)
    으로 넘어가지 않는다 — 다음 장면은 왼쪽 목록을 직접 클릭해야 한다."""
    text = _read(js_file)
    finally_block = text.split("} finally {", 1)[1]
    assert "advance();" not in finally_block
