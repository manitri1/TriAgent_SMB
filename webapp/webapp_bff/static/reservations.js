/**
 * 화면 5(예약 관리). 신규 예약·변경·취소 모두 자연어 채팅으로 coordinator에게
 * 전달한다 — 별도 쓰기 폼을 두지 않고 orders.js/inventory.js와 동일하게
 * /api/agent/message 릴레이 하나로 수렴한다(curried-percolating-ocean.md
 * "설계 편차" 참고: reservation-agent는 승인을 요청할 수단이 없어 직접 호출하면
 * HITL이 조용히 무력화된다).
 */
const RESERVATION_STATUS_LABEL = {
  BOOKED: ["예약됨", "pill-success"],
  CANCELED: ["취소", "pill-danger"],
};

function renderReservationStatus(status) {
  const [label, cls] = RESERVATION_STATUS_LABEL[status] || [status, ""];
  return `<span class="pill ${cls}">${label}</span>`;
}

function todayISODate() {
  return new Date().toISOString().slice(0, 10);
}

const reservationsAccordion = createRowActionAccordion("reservations-accordion", {
  profile: "coordinator",
  storageKeyPrefix: "conversation_id_reservations_row",
  onAfterSend: loadReservations,
});

function reservationActionsFor(r) {
  if (r.status === "BOOKED") {
    return [
      { label: "시간 변경", tone: "ghost", prefill: true, message: `예약 ${r.reservation_id}을(를) __시 __분으로 변경해주세요.` },
      { label: "예약 취소", tone: "danger", confirm: `${r.customer_id} 고객의 예약을 취소할까요?`, message: `예약 ${r.reservation_id}을(를) 취소해주세요.` },
    ];
  }
  return [];
}

function reservationAccordionRows(reservations) {
  return reservations.map((r) => {
    const time = new Date(r.datetime).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
    const cellsHtml = `
      <div class="acc-col-time">${time}</div>
      <div class="acc-col-name">${r.customer_id}${r.service ? ` · ${r.service}` : ""}</div>
      <div class="acc-col-pill">${renderReservationStatus(r.status)}</div>
    `;
    const factsHtml = `
      <div class="detail-kv"><span class="detail-kv-k">서비스</span><span class="detail-kv-v">${r.service || "-"}</span></div>
      <div class="detail-kv"><span class="detail-kv-k">요청사항</span><span class="detail-kv-v">${r.note || "없음"}</span></div>
      <div class="detail-kv"><span class="detail-kv-k">접수 시각</span><span class="detail-kv-v">${new Date(r.created_at).toLocaleString("ko-KR", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" })}</span></div>
    `;
    return {
      id: r.reservation_id,
      cellsHtml,
      factsHtml,
      contextLabel: `예약 · ${r.customer_id} ${time}`,
      editPlaceholder: "예: 인원을 3명으로 늘려줘",
      actions: reservationActionsFor(r),
    };
  });
}

async function loadReservations() {
  const container = document.getElementById("reservations-accordion");
  const res = await fetch(`/api/pos/reservations?date=${todayISODate()}`);
  if (!res.ok) {
    container.innerHTML = '<p class="hint" style="padding:16px 18px;margin:0;">불러오지 못했습니다.</p>';
    return;
  }
  const reservations = await res.json();
  if (!reservations.length) {
    container.innerHTML = '<p class="hint" style="padding:16px 18px;margin:0;">오늘 등록된 예약이 없습니다.</p>';
    return;
  }
  const sorted = reservations.slice().sort((a, b) => new Date(a.datetime) - new Date(b.datetime));
  reservationsAccordion.render(reservationAccordionRows(sorted));
}

document.addEventListener("DOMContentLoaded", () => {
  loadReservations();
  document.getElementById("refresh-reservations").addEventListener("click", loadReservations);

  initChatWidget({
    formId: "reservations-form",
    inputId: "reservations-input",
    sentPromptId: "reservations-sent-prompt",
    resultId: "reservations-result",
    profile: "coordinator",
    storageKey: "conversation_id_reservations",
    onReply: loadReservations,
    demoBarId: "reservations-demo-bar",
    demoQueue: [
      { label: "07:00 전화 예약 응대 (사장님의 하루)", message: "방금 전화로 예약 문의가 왔어요. 오늘 오후 6시 4명 예약 등록해주세요." },
      { label: "신규 예약", message: "내일 오후 2시에 김민수 고객 4명 예약 잡아줘." },
      { label: "예약 시간 변경", message: "김민수 고객 예약을 오후 3시로 변경해줘." },
      { label: "예약 취소", message: "김민수 고객 예약 취소해줘." },
      { label: "오늘 예약 현황 확인", message: "오늘 예약 몇 건이야?" },
    ],
  });
});
