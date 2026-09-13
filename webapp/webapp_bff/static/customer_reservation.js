/**
 * 고객 셀프 예약 화면(/customer/reservation). 날짜·시간·인원 칩을 고르면
 * 요약이 즉시 갱신되고, 이름까지 입력하면 "예약 확정" 버튼이 활성화된다.
 * 확정을 누르면 coordinator에게 예약 메시지를 전송한다(reservation-agent로
 * 위임되어 mock-pos에 실제 예약 레코드 생성).
 */
const selection = { date: null, time: null, party: null };

function conversationId() {
  return getConversationId("conversation_id_customer_reservation");
}

function selectChip(grid, chip) {
  grid.querySelectorAll(".wizard-chip").forEach((btn) => btn.classList.remove("wizard-chip--selected"));
  chip.classList.add("wizard-chip--selected");
}

function updateSummary() {
  const name = document.getElementById("reservation-customer-name").value.trim();
  const summary = document.getElementById("reservation-summary");
  const submitBtn = document.getElementById("reservation-submit");
  const { date, time, party } = selection;
  if (!date || !time || !party) {
    summary.textContent = "날짜·시간·인원을 먼저 선택해주세요.";
    submitBtn.disabled = true;
    return;
  }
  summary.textContent = `${date} ${time}에 ${party}명${name ? ` · 예약자: ${name}` : ""}`;
  submitBtn.disabled = false;
}

function wireChipGrid(gridId, key) {
  const grid = document.getElementById(gridId);
  grid.querySelectorAll(".wizard-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      selectChip(grid, chip);
      selection[key] = chip.dataset[key];
      updateSummary();
    });
  });
}

async function submitReservation() {
  const name = document.getElementById("reservation-customer-name").value.trim();
  const { date, time, party } = selection;
  let message = `${date} ${time}에 ${party}명 예약할게요.`;
  if (name) message += ` 이름: ${name}.`;

  const submitBtn = document.getElementById("reservation-submit");
  submitBtn.disabled = true;
  renderSentPrompt(document.getElementById("reservation-sent-prompt"), message);
  renderCompactResult(document.getElementById("reservation-result"), { status: "pending", text: "예약을 접수하는 중…" });

  try {
    const res = await fetch("/api/agent/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: "coordinator", message, conversation_id: conversationId() }),
    });
    const data = await res.json();
    renderCompactResult(document.getElementById("reservation-result"), { status: data.status === "ok" ? "ok" : data.status, text: data.text });
  } catch (err) {
    renderCompactResult(document.getElementById("reservation-result"), { status: "error", text: "네트워크 오류가 발생했습니다. 다시 시도해 주세요." });
  } finally {
    submitBtn.disabled = false;
  }
}

wireChipGrid("reservation-date-grid", "date");
wireChipGrid("reservation-time-grid", "time");
wireChipGrid("reservation-party-grid", "party");
document.getElementById("reservation-customer-name").addEventListener("input", updateSummary);
document.getElementById("reservation-submit").addEventListener("click", submitReservation);
