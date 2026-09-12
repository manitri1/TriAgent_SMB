/**
 * 화면 6(라이브 데모). docs/21-live-demo-plan.md P2 표의 12개 타임라인 전체를
 * 하나의 화면에서 순서대로 진행한다. 다른 화면의 demoQueue(단일 profile, 단일
 * 채팅창)와 달리 이 화면은 profile이 장면마다 바뀌고(coordinator/
 * customer-service-agent), 일부 장면은 프롬프트가 아예 없는(읽기 전용) 구조라
 * chat.js의 initChatWidget을 그대로 재사용하지 않고 별도 큐 상태 머신을 둔다.
 * 전송 경로 자체는 동일하게 /api/agent/message 하나로 수렴한다
 * (curried-percolating-ocean.md).
 *
 * 장면마다 "결과 확인" 패널을 함께 둔다 — 새 탭으로 다른 화면을 열지 않아도
 * mock-pos에 실제로 반영된 데이터(재고/주문/예약/매출)를 이 화면 안에서 바로
 * 볼 수 있게, /api/pos/* 프록시(읽기 전용)를 직접 호출해 렌더링한다. 장면을
 * 고를 때마다(왼쪽 목록 클릭 포함) 매번 새로 조회하므로 "처음 봤을 때"가 아니라
 * "지금 상태"를 보여준다.
 */
const TIMEOUT_POLL_INTERVAL_MS = 15000;
const TIMEOUT_POLL_MAX_ATTEMPTS = 5;
const SLOW_HINT_THRESHOLD_SECONDS = 20;

const ORDER_STATUS_LABEL = {
  OPEN: ["대기", "pill-warning"],
  COMPLETED: ["완료", "pill-success"],
  CANCELED: ["취소", "pill-danger"],
  PARTIALLY_REFUNDED: ["부분환불", "pill-warning"],
  REFUNDED: ["환불", "pill-danger"],
};
const RESERVATION_STATUS_LABEL = {
  BOOKED: ["예약됨", "pill-success"],
  CANCELED: ["취소", "pill-danger"],
};

// /api/agent/message는 coordinator/customer-service-agent만 허용한다
// (agent.py — 다른 profile은 HITL 승인 수단이 없어 직접 호출하면 게이트가
// 무력화됨). 그래서 Discord/CLI/대시보드가 실제 채널인 장면도 이 두 profile
// 중 하나로 대체 시연한다. result.kind가 있는 장면은 아래 결과 패널에서
// 해당 mock-pos 데이터를 바로 조회해 보여준다(없으면 채팅 응답 자체가 결과).
const DAY_STEPS = [
  {
    time: "05:30", title: "아침 브리핑",
    channel: "실제 채널: Discord #smb-ops (텍스트 요약 · POS 호출 없음)",
    type: "chat", profile: "coordinator",
    message: "오늘 아침 브리핑 정리해줘.",
  },
  {
    time: "06:30", title: "재고 스냅샷",
    channel: "실제 채널: webapp 재고 관리 화면 (읽기 전용 — 프롬프트 없음)",
    type: "link",
    result: { kind: "inventory", href: "/inventory", label: "재고 관리 화면" },
  },
  {
    time: "07:00", title: "예약 응대",
    channel: "실제 채널: webapp 예약 관리 화면",
    type: "chat", profile: "coordinator",
    message: "방금 전화로 예약 문의가 왔어요. 오늘 오후 6시 4명 예약 등록해주세요.",
    result: { kind: "reservations", href: "/reservations", label: "예약 관리 화면" },
  },
  {
    time: "09:10", title: "[게이트2] 결품 발견 + 발주 초안",
    channel: "실제 채널: webapp 재고 관리 화면 또는 CLI · 승인이 필요할 수 있음",
    type: "chat", profile: "coordinator",
    message: "다음 품목 재입고를 요청합니다: 아메리카노 50개. 사유: 원두 완전 품절, 긴급 대량 재입고 필요.",
    result: { kind: "inventory", href: "/inventory", label: "재고 관리 화면" },
  },
  {
    time: "11:20", title: "단체 문의",
    channel: "실제 채널: webapp 고객 문의 화면",
    type: "chat", profile: "customer-service-agent",
    message: "20인분 단체 주문인데 오늘 오후 3시 픽업 가능할까요?",
    result: { kind: "support-note", href: "/support", label: "고객 문의 화면" },
  },
  {
    time: "12:00", title: "[게이트3] 결제/환불",
    channel: "실제 채널: webapp 주문 접수 화면",
    type: "chat", profile: "coordinator",
    message: "라떼 2잔, 아메리카노 1잔 주문 들어왔어, 결제까지 처리해줘.",
    result: { kind: "orders", href: "/orders", label: "주문 접수 화면" },
  },
  {
    time: "14:30", title: "\"오늘 매출 어때?\"",
    channel: "실제 채널: CLI 또는 대시보드(:19128) /chat",
    type: "chat", profile: "coordinator",
    message: "오늘 매출 어때?",
    result: { kind: "sales", href: "/dashboard", label: "대시보드" },
  },
  {
    time: "15:30", title: "[게이트1] 홍보 초안",
    channel: "실제 채널: CLI 또는 대시보드 /chat · marketing-crm-agent는 게시 기능 자체가 없음",
    type: "chat", profile: "coordinator",
    message: "단호박 라떼 홍보 문구 초안 써줘.",
  },
  {
    time: "17:10", title: "컴플레인 응대",
    channel: "실제 채널: webapp 고객 문의 화면",
    type: "chat", profile: "customer-service-agent",
    message: "아까 주문한 라떼가 다른 음료로 잘못 나왔어요.",
    result: { kind: "support-note", href: "/support", label: "고객 문의 화면" },
  },
  {
    time: "19:40", title: "마감 정산",
    channel: "실제 채널: mock-pos 대시보드(:18080/dashboard) + CLI",
    type: "chat", profile: "coordinator",
    message: "오늘 마감 리포트 정리해줘.",
    result: { kind: "settlement", href: "/dashboard", label: "대시보드" },
  },
  {
    time: "21:00", title: "다음날 브리핑 초안",
    channel: "실제 채널: Discord 또는 CLI",
    type: "chat", profile: "coordinator",
    message: "내일 아침 브리핑 초안 써줘.",
  },
  {
    time: "23:00", title: "승인 대기 3건 확인",
    channel: "실제 채널: Discord #smb-ops",
    type: "chat", profile: "coordinator",
    message: "오늘 승인 대기 중인 항목 정리해줘.",
  },
];

let currentIndex = 0;
let busy = false;
const done = new Array(DAY_STEPS.length).fill(false);
let catalogNameById = {};
let resultRequestToken = 0; // 결과 패널이 겹쳐 조회될 때 먼저 시작한 조회가 늦게 도착해 새 장면 위에 덮어쓰는 것을 막는다

async function loadCatalogNames() {
  try {
    const res = await fetch("/api/pos/catalog/items");
    if (!res.ok) return;
    const items = await res.json();
    catalogNameById = Object.fromEntries(items.map((i) => [i.item_id, i.name]));
  } catch (err) {
    // 결과 패널은 품목명이 없으면 item_id로 대체 표시하므로 조용히 넘어간다.
  }
}

function conversationIdFor(profile) {
  const key = profile === "customer-service-agent" ? "conversation_id_live_demo_support" : "conversation_id_live_demo_coordinator";
  let id = localStorage.getItem(key);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(key, id);
  }
  return id;
}

function isApprovalPrompt(role, text, statusClass) {
  return role === "agent" && !statusClass && /승인/.test(text);
}

function appendMessage(role, text, statusClass) {
  const thread = document.getElementById("demo-day-thread");
  const approval = isApprovalPrompt(role, text, statusClass);
  const row = document.createElement("div");
  row.className = `chat-row chat-row--${role}${statusClass ? ` chat-row--${statusClass}` : ""}${approval ? " chat-row--approval" : ""}`;
  if (approval) {
    const label = document.createElement("div");
    label.className = "chat-approval-label";
    label.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 4h.01M10.3 3.9 2.5 17a1.6 1.6 0 0 0 1.4 2.4h16.2a1.6 1.6 0 0 0 1.4-2.4L13.7 3.9a1.6 1.6 0 0 0-2.8 1"/></svg>승인 필요';
    row.appendChild(label);
  }
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble";
  bubble.textContent = text;
  row.appendChild(bubble);
  thread.appendChild(row);
  thread.scrollTop = thread.scrollHeight;
  return row;
}

function appendStepDivider(step, index) {
  const thread = document.getElementById("demo-day-thread");
  const divider = document.createElement("div");
  divider.className = "demo-day-thread-divider";
  divider.textContent = `${index + 1}/${DAY_STEPS.length} · ${step.time} ${step.title}`;
  thread.appendChild(divider);
  thread.scrollTop = thread.scrollHeight;
}

function renderProgress() {
  document.getElementById("demo-day-progress-label").textContent = `${currentIndex + 1}/${DAY_STEPS.length}`;
  const doneCount = done.filter(Boolean).length;
  document.getElementById("demo-day-progress-fill").style.width = `${(doneCount / DAY_STEPS.length) * 100}%`;
}

function renderStepList() {
  const list = document.getElementById("demo-day-steps");
  list.innerHTML = "";
  DAY_STEPS.forEach((step, index) => {
    const li = document.createElement("li");
    li.className = `demo-day-step${index === currentIndex ? " demo-day-step--current" : ""}${done[index] ? " demo-day-step--done" : ""}`;
    li.innerHTML = `
      <span class="demo-day-step-badge">${done[index] ? "✓" : index + 1}</span>
      <span class="demo-day-step-meta">
        <span class="demo-day-step-time">${step.time}</span><br>
        <span class="demo-day-step-title">${step.title}</span>
      </span>
    `;
    li.addEventListener("click", () => {
      if (busy) return;
      currentIndex = index;
      renderAll();
    });
    list.appendChild(li);
  });
}

function resultPanelShellHtml(step) {
  if (!step.result) return "";
  return `
    <div class="demo-day-result">
      <div class="demo-day-result-head">
        <h3>지금 반영된 데이터</h3>
        <div class="demo-day-result-actions">
          <button type="button" id="demo-day-result-refresh" class="btn-ghost btn-ghost--sm">새로고침</button>
          <a class="demo-day-result-link" href="${step.result.href}" target="_blank" rel="noopener">
            ${step.result.label}에서 전체 보기
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.4"><path stroke-linecap="round" stroke-linejoin="round" d="M9 6l6 6-6 6"/></svg>
          </a>
        </div>
      </div>
      <div id="demo-day-result-body" class="demo-day-result-body"><p class="hint">불러오는 중…</p></div>
    </div>
  `;
}

function renderDetail() {
  const step = DAY_STEPS[currentIndex];
  const detail = document.getElementById("demo-day-detail");
  detail.innerHTML = `
    <div class="demo-day-detail-head">
      <span class="demo-day-detail-time">${step.time}</span>
      <span class="demo-day-detail-title">${step.title}</span>
    </div>
    <p class="demo-day-detail-channel">${step.channel}</p>
    ${step.type === "chat" ? `
      <form id="demo-day-form" class="demo-day-detail-form">
        <input id="demo-day-input" type="text" autocomplete="off" value="${step.message.replace(/"/g, "&quot;")}" ${busy ? "disabled" : ""}>
        <button type="submit" class="btn-primary" ${busy ? "disabled" : ""}>보내기</button>
      </form>
    ` : `
      <div class="demo-day-actions">
        <button type="button" id="demo-day-mark-done" class="btn-ghost">확인 완료 · 다음 장면</button>
      </div>
    `}
    ${resultPanelShellHtml(step)}
  `;

  if (step.type === "chat") {
    document.getElementById("demo-day-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const input = document.getElementById("demo-day-input");
      const message = input.value.trim();
      if (!message || busy) return;
      sendStep(step, currentIndex, message);
    });
  } else {
    document.getElementById("demo-day-mark-done").addEventListener("click", () => {
      done[currentIndex] = true;
      advance();
    });
  }

  if (step.result) {
    document.getElementById("demo-day-result-refresh").addEventListener("click", () => loadResultPanel(step));
  }
}

function renderAll() {
  const step = DAY_STEPS[currentIndex];
  renderProgress();
  renderStepList();
  renderDetail();
  if (step.result) loadResultPanel(step);
}

function advance() {
  if (currentIndex < DAY_STEPS.length - 1) {
    currentIndex += 1;
  }
  renderAll();
}

let timeoutPollTimer = null;
function clearTimeoutPolling() {
  if (timeoutPollTimer) {
    clearInterval(timeoutPollTimer);
    timeoutPollTimer = null;
  }
}

function compactTableHtml(headers, rows) {
  const head = headers.map((h) => `<th>${h}</th>`).join("");
  const body = rows.map((cells) => `<tr>${cells.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("");
  return `<table class="data-table data-table--compact"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

/** 장면의 result.kind에 맞춰 mock-pos 데이터를 조회해 결과 패널에 채운다. */
async function loadResultPanel(step) {
  const body = document.getElementById("demo-day-result-body");
  if (!body) return; // 그 사이 다른 장면으로 넘어가 패널 자체가 사라졌을 수 있음
  const token = ++resultRequestToken;
  const fail = () => {
    if (token !== resultRequestToken) return;
    body.innerHTML = '<p class="hint">불러오지 못했습니다.</p>';
  };
  try {
    if (step.result.kind === "inventory") {
      const res = await fetch("/api/pos/inventory");
      if (!res.ok) return fail();
      const items = await res.json();
      if (token !== resultRequestToken) return;
      if (!items.length) { body.innerHTML = '<p class="hint">등록된 품목이 없습니다.</p>'; return; }
      body.innerHTML = compactTableHtml(
        ["품목", "재고", "저재고 임계치"],
        items.map((i) => [catalogNameById[i.item_id] ?? i.item_id, i.stock_quantity, i.low_stock_threshold ?? 5])
      );
    } else if (step.result.kind === "orders") {
      const res = await fetch("/api/pos/orders");
      if (!res.ok) return fail();
      const orders = await res.json();
      if (token !== resultRequestToken) return;
      if (!orders.length) { body.innerHTML = '<p class="hint">주문 내역이 없습니다.</p>'; return; }
      const recent = orders.slice(-5).reverse();
      body.innerHTML = compactTableHtml(
        ["주문번호", "품목", "금액", "상태"],
        recent.map((o) => {
          const items = o.line_items.map((li) => `${catalogNameById[li.item_id] ?? li.item_id} x${li.quantity}`).join(", ");
          const [label, cls] = ORDER_STATUS_LABEL[o.status] || [o.status, ""];
          return [o.order_id, items, `${o.total_amount.toLocaleString()}원`, `<span class="pill ${cls}">${label}</span>`];
        })
      );
    } else if (step.result.kind === "reservations") {
      const today = new Date().toISOString().slice(0, 10);
      const res = await fetch(`/api/pos/reservations?date=${today}`);
      if (!res.ok) return fail();
      const list = await res.json();
      if (token !== resultRequestToken) return;
      if (!list.length) { body.innerHTML = '<p class="hint">오늘 등록된 예약이 없습니다.</p>'; return; }
      const sorted = list.slice().sort((a, b) => new Date(a.datetime) - new Date(b.datetime));
      body.innerHTML = compactTableHtml(
        ["시간", "고객", "상태"],
        sorted.map((r) => {
          const time = new Date(r.datetime).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
          const [label, cls] = RESERVATION_STATUS_LABEL[r.status] || [r.status, ""];
          return [time, r.customer_id, `<span class="pill ${cls}">${label}</span>`];
        })
      );
    } else if (step.result.kind === "sales") {
      const res = await fetch("/api/pos/reports/sales?period=today");
      if (!res.ok) return fail();
      const data = await res.json();
      if (token !== resultRequestToken) return;
      body.innerHTML = `<p class="demo-day-result-stat">오늘 매출 <strong>${data.total_sales.toLocaleString()}원</strong> · 주문 <strong>${data.order_count}</strong>건</p>`;
    } else if (step.result.kind === "settlement") {
      const res = await fetch("/api/pos/reports/settlement?period=today");
      if (!res.ok) return fail();
      const data = await res.json();
      if (token !== resultRequestToken) return;
      body.innerHTML = `<p class="demo-day-result-stat">총 매출 <strong>${data.gross_sales.toLocaleString()}원</strong> · 결제 <strong>${data.payment_count}</strong>건 · 환불 <strong>${data.refunded_count}</strong>건</p>`;
    } else if (step.result.kind === "support-note") {
      body.innerHTML = '<p class="hint">고객 문의는 mock-pos에 별도로 기록되지 않습니다 — 위 실행 로그의 응답이 곧 결과이며, 전체 대화는 고객 문의 화면에서 이어볼 수 있습니다.</p>';
    }
  } catch (err) {
    fail();
  }
}

async function sendStep(step, index, message) {
  clearTimeoutPolling();
  appendStepDivider(step, index);
  appendMessage("user", message);
  const pending = appendMessage("agent", "생각하는 중… (0초)", "pending");
  const pendingBubble = pending.querySelector(".chat-bubble");
  const startedAt = Date.now();
  const elapsedTimer = setInterval(() => {
    const secs = Math.floor((Date.now() - startedAt) / 1000);
    let text = `생각하는 중… (${secs}초)`;
    if (secs >= SLOW_HINT_THRESHOLD_SECONDS) {
      text += "\n보통 25초~4분 정도 걸려요. 잠시만 기다려 주세요.";
    }
    pendingBubble.textContent = text;
  }, 1000);

  busy = true;
  renderDetail();
  renderStepList();
  if (step.result) loadResultPanel(step); // 전송 직전 상태를 보여주고, 완료 후 finally에서 다시 한번 갱신한다
  try {
    const res = await fetch("/api/agent/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: step.profile, message, conversation_id: conversationIdFor(step.profile) }),
    });
    const data = await res.json();
    clearInterval(elapsedTimer);
    pending.remove();
    const statusClass = data.status === "ok" ? null : data.status;
    appendMessage("agent", data.text, statusClass);
    if (data.status === "timeout") {
      let attempts = 0;
      timeoutPollTimer = setInterval(() => {
        attempts++;
        if (attempts >= TIMEOUT_POLL_MAX_ATTEMPTS) clearTimeoutPolling();
      }, TIMEOUT_POLL_INTERVAL_MS);
    }
  } catch (err) {
    clearInterval(elapsedTimer);
    pending.remove();
    appendMessage("agent", "네트워크 오류가 발생했습니다. 다시 시도해 주세요.", "error");
  } finally {
    clearInterval(elapsedTimer);
    busy = false;
    done[index] = true;
    if (index === currentIndex) {
      // 다음 장면으로 넘어가기 전에, 방금 실행한 장면의 결과 패널을 최신 데이터로
      // 한 번 갱신해둔다 — 발표자가 왼쪽 목록에서 이 장면을 다시 클릭했을 때
      // 이미 최신 상태가 보이게.
      if (step.result) await loadResultPanel(step);
      advance();
    } else {
      renderProgress();
      renderStepList();
    }
  }
}

document.getElementById("demo-day-reset").addEventListener("click", () => {
  if (busy) return;
  currentIndex = 0;
  done.fill(false);
  renderAll();
});

loadCatalogNames();
renderAll();
