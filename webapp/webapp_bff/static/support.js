/**
 * 화면 1(고객 문의 상담)의 "접수 내역" 목록. 문의는 mock-pos에 저장되지 않고
 * 이 화면 자체가 기록이라, 주고받은 메시지를 그대로 한 줄씩 쌓는다 — 서버
 * 재조회가 아니라 이 화면의 상태 자체가 데이터 소스다. 페이지를 열면 오늘
 * 오전 중 이미 처리된 것으로 가정한 이력(INITIAL_INQUIRIES)이 먼저 보이고,
 * 위 채팅으로 새로 주고받는 문의가 그 위에 쌓인다. initChatWidget 호출
 * (demoQueue 포함)은 support.html에 그대로 남아있고, 그 onReply가 여기 정의된
 * addInquiry를 불러 목록에 한 줄을 추가한다.
 *
 * INITIAL_INQUIRIES는 "사장님의 하루" 데모 큐(11:20 단체 주문, 17:10 컴플레인)
 * 와 겹치지 않는 시간대·주제로만 채운다 — 겹치면 발표자가 데모 큐를 눌렀을 때
 * "이미 나온 문의"처럼 보여 혼란을 줄 수 있다.
 */
let inquirySeq = 0;
const INITIAL_INQUIRIES = [
  { time: "오전 8:20", channel: "카카오톡 채널 챗봇", question: "혹시 반려동물 동반 가능한가요?", answer: "죄송하지만 위생상 반려동물 동반은 어렵습니다. 양해 부탁드려요.", resolved: true },
  { time: "오전 9:05", channel: "카카오톡 채널 챗봇", question: "포장 컵 사이즈가 어떻게 되나요?", answer: "톨(355ml)과 그란데(473ml) 두 가지 사이즈가 있습니다.", resolved: true },
  { time: "오전 10:12", channel: "카카오톡 채널 챗봇", question: "매장에 콘센트 있나요?", answer: "네, 창가 좌석 위주로 콘센트가 마련되어 있습니다.", resolved: true },
  { time: "오후 12:40", channel: "전화 상담 → 수기 입력", question: "생일 케이크 예약도 가능한가요?", answer: "네, 3일 전까지 예약해주시면 준비해드립니다.", resolved: false },
  { time: "오후 2:05", channel: "카카오톡 채널 챗봇", question: "포인트 적립은 어떻게 하나요?", answer: "카카오톡 채널을 추가하시면 자동으로 적립됩니다.", resolved: true },
];
// 최신이 위로 오도록(addInquiry의 unshift와 같은 순서) 시간 역순으로 초기화한다.
const inquiries = INITIAL_INQUIRIES.slice()
  .reverse()
  .map((inq, i) => ({ id: `inq-seed-${i}`, status: "ok", ...inq }));

const supportAccordion = createRowActionAccordion("support-accordion", {
  profile: "customer-service-agent",
  storageKeyPrefix: "conversation_id_support_row",
  onAfterSend: renderInquiries,
});

function inquiryStatusPill(inquiry) {
  if (inquiry.resolved) return statusPill("완료", "success");
  if (inquiry.status === "timeout") return statusPill("확인 필요", "warning");
  if (inquiry.status === "error") return statusPill("오류", "danger");
  return statusPill("신규", "success");
}

function renderInquiries() {
  const container = document.getElementById("support-accordion");
  if (!inquiries.length) {
    container.innerHTML = '<p class="hint" style="padding:16px 18px;margin:0;">아직 접수된 문의가 없습니다. 위 채팅으로 문의를 보내보세요.</p>';
    return;
  }
  const rows = inquiries.map((inq) => {
    const summary = inq.question.length > 44 ? `${inq.question.slice(0, 44)}…` : inq.question;
    const cellsHtml = `
      <div class="acc-col-time">${inq.time}</div>
      <div class="acc-col-name">"${summary}"</div>
      <div class="acc-col-pill">${inquiryStatusPill(inq)}</div>
    `;
    const factsHtml = `
      <div class="detail-kv"><span class="detail-kv-k">문의 원문</span><span class="detail-kv-v">${inq.question}</span></div>
      <div class="detail-kv"><span class="detail-kv-k">접수 채널</span><span class="detail-kv-v">${inq.channel || "웹 채팅"}</span></div>
      <div class="detail-kv"><span class="detail-kv-k">접수 시각</span><span class="detail-kv-v">${inq.time}</span></div>
      <div class="detail-kv"><span class="detail-kv-k">답변</span><span class="detail-kv-v">${inq.answer}</span></div>
    `;
    return {
      id: inq.id,
      cellsHtml,
      factsHtml,
      contextLabel: `문의 · "${summary}"`,
      editPlaceholder: "예: 이 답변에 안내를 하나 더 추가해줘",
      actions: inq.resolved
        ? [{ label: "다시 확인 필요로 표시", tone: "ghost", handler: () => { inq.resolved = false; renderInquiries(); } }]
        : [{ label: "완료로 표시", tone: "primary", handler: () => { inq.resolved = true; renderInquiries(); } }],
    };
  });
  supportAccordion.render(rows);
}

function addInquiry(question, reply) {
  inquiries.unshift({
    id: `inq-${++inquirySeq}`,
    time: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
    channel: "웹 채팅",
    question,
    answer: reply.text,
    status: reply.status,
    resolved: false,
  });
  renderInquiries();
}

document.addEventListener("DOMContentLoaded", renderInquiries);
