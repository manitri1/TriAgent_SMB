/**
 * 화면(손님 라이브 데모). live_demo.js("사장님의 하루")와 완전히 같은 큐
 * 상태 머신 구조를 재사용하되, 장면 내용만 손님 관점으로 바꾼다 — 손님이
 * 전화/카카오톡/매장 방문으로 문의·주문·예약·컴플레인을 하는 하루.
 * /api/agent/message가 coordinator/customer-service-agent만 허용하므로
 * (agent.py), 실제 POS 반영이 필요한 장면(주문·예약)은 coordinator로,
 * 단순 문의·컴플레인은 customer-service-agent로 보낸다 — support.html과
 * 동일한 프로필 배정 원칙.
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

const DAY_STEPS = [
  {
    time: "08:15", title: "영업시간 문의",
    channel: "실제 채널: 전화·카카오톡 문의 → 웹 고객 문의 창구로 대체 시연",
    type: "chat", profile: "customer-service-agent",
    message: "오늘 몇 시부터 문 열어요?",
  },
  {
    time: "08:20", title: "시즌 메뉴 문의",
    channel: "실제 채널: 전화·카카오톡 문의 → 웹 고객 문의 창구로 대체 시연",
    type: "chat", profile: "customer-service-agent",
    message: "요즘 시즌 메뉴로 나온 거 있어요?",
  },
  {
    time: "08:30", title: "포장 주문",
    channel: "실제 채널: 매장 방문·전화 주문 → webapp 주문 접수 화면으로 대체 시연",
    type: "chat", profile: "coordinator",
    message: "아메리카노 1잔, 라떼 1잔 포장으로 주문할게요. 15분 뒤에 찾으러 갈게요.",
    result: { kind: "orders", href: "/orders", label: "주문 접수 화면" },
  },
  {
    time: "12:40", title: "저녁 예약 문의",
    channel: "실제 채널: 전화 예약 → webapp 예약 관리 화면으로 대체 시연",
    type: "chat", profile: "coordinator",
    message: "오늘 저녁 7시에 2명 예약할 수 있을까요?",
    result: { kind: "reservations", href: "/reservations", label: "예약 관리 화면" },
  },
  {
    time: "13:10", title: "주차 문의",
    channel: "실제 채널: 전화·카카오톡 문의 → 웹 고객 문의 창구로 대체 시연",
    type: "chat", profile: "customer-service-agent",
    message: "혹시 가게 앞에 주차 가능한가요?",
  },
  {
    time: "18:50", title: "주문 오류 항의",
    channel: "실제 채널: 매장 방문·전화 항의 → 웹 고객 문의 창구로 대체 시연",
    type: "chat", profile: "customer-service-agent",
    message: "방금 포장 주문했는데 라떼가 아니라 아메리카노가 두 잔 나왔어요.",
  },
  {
    time: "19:05", title: "예약 재확인",
    channel: "실제 채널: 전화 문의 → 웹 고객 문의 창구로 대체 시연",
    type: "chat", profile: "customer-service-agent",
    message: "저 아까 저녁 7시로 예약한 사람인데, 예약이 잘 잡혔는지 확인할 수 있을까요?",
    result: { kind: "reservations", href: "/reservations", label: "예약 관리 화면" },
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
  const key = profile === "customer-service-agent" ? "conversation_id_customer_live_demo_support" : "conversation_id_customer_live_demo_coordinator";
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
      <div id="demo-day-sent" class="sent-prompt"></div>
      <div id="demo-day-summary" class="compact-result"></div>
      ${step.result ? `<a href="${step.result.href}" class="btn-ghost hero-quick-goto" target="_blank" rel="noopener">${step.result.label}에서 확인 →</a>` : ""}
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
    if (step.result.kind === "orders") {
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
  renderSentPrompt(document.getElementById("demo-day-sent"), message);
  renderCompactResult(document.getElementById("demo-day-summary"), { status: "pending", text: "coordinator에게 전달하는 중…" });
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
    if (index === currentIndex) {
      renderSentPrompt(document.getElementById("demo-day-sent"), message);
      renderCompactResult(document.getElementById("demo-day-summary"), { status: data.status === "ok" ? "ok" : data.status, text: data.text });
    }
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
    if (index === currentIndex) {
      renderSentPrompt(document.getElementById("demo-day-sent"), message);
      renderCompactResult(document.getElementById("demo-day-summary"), { status: "error", text: "네트워크 오류가 발생했습니다. 다시 시도해 주세요." });
    }
  } finally {
    clearInterval(elapsedTimer);
    busy = false;
    done[index] = true;
    if (index === currentIndex) {
      // 자동으로 다음 장면으로 넘어가지 않는다 — 방금 받은 결과(보낸 요청 +
      // 응답 요약)를 발표자가 이 자리에서 계속 볼 수 있어야 하기 때문이다.
      // renderDetail()을 다시 부르면 방금 채운 결과가 지워지므로, 입력창/버튼의
      // disabled만 직접 풀어준다. 다음 장면은 왼쪽 목록을 직접 클릭해 이동한다.
      const input = document.getElementById("demo-day-input");
      const submitBtn = document.querySelector("#demo-day-form button[type=submit]");
      if (input) input.disabled = false;
      if (submitBtn) submitBtn.disabled = false;
      if (step.result) await loadResultPanel(step);
      renderProgress();
      renderStepList();
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
