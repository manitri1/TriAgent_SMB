/**
 * 홈 화면의 "사장님이 할 수 있는 일" 퀵 액션 위젯.
 * 화면엔 칩만 보이고, 클릭하면 미리 정해진 질문이 숨겨진 채팅 엔진
 * (initChatWidget)을 통해 /api/agent/message(coordinator)로 전송된다.
 * 보낸 문구는 sent-prompt로, 결과는 한 줄(compact-result)로 보여주고,
 * 옆의 바로가기 버튼은 방금 고른 액션에 맞는 화면으로 목적지를 바꾼다.
 */
const HOME_QUICK_ACTIONS = [
  { label: "오늘 매출", message: "오늘 매출 얼마예요?", gotoHref: "/dashboard", gotoLabel: "대시보드에서 확인 →" },
  { label: "재고 확인", message: "재고 상황 알려줘.", gotoHref: "/inventory", gotoLabel: "재고 관리에서 확인 →" },
  { label: "오늘 예약", message: "오늘 예약 몇 건이야?", gotoHref: "/reservations", gotoLabel: "예약 관리에서 확인 →" },
  { label: "오늘 주문", message: "오늘 주문 몇 건 들어왔어?", gotoHref: "/orders", gotoLabel: "주문 접수에서 확인 →" },
  { label: "고객 문의", message: "새로 들어온 고객 문의 있어?", gotoHref: "/support", gotoLabel: "고객 문의에서 확인 →" },
];

document.addEventListener("DOMContentLoaded", () => {
  const chipContainer = document.getElementById("home-quick-chips");
  const gotoLink = document.getElementById("home-quick-goto");
  const resultEl = document.getElementById("home-quick-result");
  const sentEl = document.getElementById("home-quick-sent");
  const form = document.getElementById("home-quick-form");
  const input = document.getElementById("home-quick-input");
  let busy = false;

  function runAction(action) {
    if (busy) return;
    gotoLink.href = action.gotoHref;
    gotoLink.textContent = action.gotoLabel;
    renderSentPrompt(sentEl, action.message);
    renderCompactResult(resultEl, { status: "pending", text: "확인하는 중…" });
    input.value = action.message;
    form.requestSubmit();
  }

  HOME_QUICK_ACTIONS.forEach((action) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "quick-chip";
    chip.textContent = action.label;
    chip.addEventListener("click", () => runAction(action));
    chipContainer.appendChild(chip);
  });

  initChatWidget({
    formId: "home-quick-form",
    inputId: "home-quick-input",
    threadId: "home-quick-thread",
    profile: "coordinator",
    storageKey: "conversation_id_home_quick",
    onReply: (data) => {
      renderCompactResult(resultEl, {
        status: data.status === "ok" ? "ok" : data.status,
        text: data.text,
      });
    },
    onBusyChange: (isBusy) => {
      busy = isBusy;
      chipContainer.querySelectorAll(".quick-chip").forEach((btn) => (btn.disabled = isBusy));
    },
  });
});
