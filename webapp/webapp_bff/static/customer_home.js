/**
 * 고객 홈(/customer)의 퀵 액션 위젯. home.js(사장님 화면)와 완전히 같은
 * 패턴 — 화면엔 칩만 보이고, 클릭하면 미리 정해진 질문이 숨겨진 채팅 엔진
 * (initChatWidget)을 통해 /api/agent/message(coordinator)로 전송된다.
 * 보낸 문구는 sent-prompt로, 결과는 한 줄(compact-result)로 보여주고,
 * 옆의 바로가기 버튼은 방금 고른 액션에 맞는 정식 화면으로 목적지를 바꾼다.
 */
const CUSTOMER_QUICK_ACTIONS = [
  { label: "문의하기", message: "오늘 영업시간이 어떻게 되나요?", gotoHref: "/customer/faq", gotoLabel: "문의하기에서 계속 →" },
  { label: "주문하기", message: "아메리카노 1잔 주문할게요.", gotoHref: "/customer/order", gotoLabel: "주문하기에서 계속 →" },
  { label: "예약하기", message: "내일 오후 2시에 2명 예약할 수 있어?", gotoHref: "/customer/reservation", gotoLabel: "예약하기에서 계속 →" },
];

document.addEventListener("DOMContentLoaded", () => {
  const chipContainer = document.getElementById("customer-quick-chips");
  const gotoLink = document.getElementById("customer-quick-goto");
  const resultEl = document.getElementById("customer-quick-result");
  const sentEl = document.getElementById("customer-quick-sent");
  const form = document.getElementById("customer-quick-form");
  const input = document.getElementById("customer-quick-input");
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

  CUSTOMER_QUICK_ACTIONS.forEach((action) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "quick-chip";
    chip.textContent = action.label;
    chip.addEventListener("click", () => runAction(action));
    chipContainer.appendChild(chip);
  });

  initChatWidget({
    formId: "customer-quick-form",
    inputId: "customer-quick-input",
    threadId: "customer-quick-thread",
    profile: "coordinator",
    storageKey: "conversation_id_customer_quick",
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
