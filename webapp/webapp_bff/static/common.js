/**
 * 여러 화면(대시보드 인사이트, 재입고 요청, 주문/예약 확정 등)이 공유하는
 * 유틸 — conversation_id 관리와 "간단 결과" 렌더링. chat.js도 conversationId
 * 로직을 여기 위임한다(중복 제거).
 */

function getConversationId(storageKey) {
  let id = localStorage.getItem(storageKey);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(storageKey, id);
  }
  return id;
}

function firstLineOrTruncate(text, maxChars) {
  const firstLine = (text || "").split("\n").find((l) => l.trim()) || "";
  const truncated = firstLine.length > maxChars;
  const headline = truncated ? firstLine.slice(0, maxChars) + "…" : firstLine;
  return { headline, truncated };
}

/**
 * 원문 텍스트를 그대로 덤프하지 않고, 헤드라인(첫 줄/최대 길이) + 상태색 +
 * 필요할 때만 펼쳐보는 "전체 보기" 토글로 보여준다.
 * container: 통째로 새로 채울 엘리먼트.
 * status: "pending" | "ok" | "timeout" | "error"
 * text: 전체 원문(또는 대기 중 안내 문구).
 */
function renderCompactResult(container, { status, text, headlineChars = 80 } = {}) {
  if (!container) return;
  container.className = `compact-result compact-result--${status}`;
  container.innerHTML = "";
  const { headline: headlineText, truncated } = firstLineOrTruncate(text, headlineChars);
  const headline = document.createElement("div");
  headline.className = "compact-result-headline";
  headline.textContent = headlineText;
  container.appendChild(headline);

  const hasMoreLines = (text || "").trim() !== (text || "").trim().split("\n").find((l) => l.trim());
  if (text && (truncated || hasMoreLines)) {
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "compact-result-toggle";
    toggle.textContent = "전체 보기";
    const full = document.createElement("div");
    full.className = "compact-result-full";
    full.hidden = true;
    full.textContent = text;
    toggle.addEventListener("click", () => {
      full.hidden = !full.hidden;
      toggle.textContent = full.hidden ? "전체 보기" : "접기";
    });
    container.appendChild(toggle);
    container.appendChild(full);
  }
}

/**
 * 버튼 클릭으로 자동 구성된 문구를 보내는 화면(재입고 요청, 대시보드 승인/의견
 * 입력 등)에서, 실제로 무슨 문구가 coordinator에게 보내졌는지 보여준다 —
 * 자유 채팅(chat.js)은 사용자 말풍선으로 이미 보이지만, 버튼 한 번으로 바로
 * 전송되는 화면들은 보낸 내용이 어디에도 안 보였다.
 */
function renderSentPrompt(container, message) {
  if (!container) return;
  container.className = "sent-prompt";
  container.innerHTML = "";
  const label = document.createElement("span");
  label.className = "sent-prompt-label";
  label.textContent = "보낸 요청:";
  container.appendChild(label);
  container.appendChild(document.createTextNode(message));
}

function statusPill(label, tone) {
  return `<span class="pill pill-${tone}">${label}</span>`;
}

/**
 * 재고 위험/부족 + 소진 예상일 인사이트. 원래 dashboard.js에만 있던 로직을
 * 재고 관리 화면(inventory.js)도 그대로 쓸 수 있게 뺐다. dashboard에서 쓸
 * 때는 "재고 관리로 이동" 링크가 필요하지만, 재고 관리 화면 자체에서 쓸
 * 때는 자기 자신으로 가는 링크라 불필요하므로 `withLink=false`로 끈다.
 */
/** 재고 심각도 3단계 — 위험(임계치 절반 이하) > 부족(임계치 이하) > 정상. */
function stockSeverity(stockQty, threshold) {
  if (stockQty <= threshold * 0.5) return { label: "위험", cls: "pill-danger", level: 2 };
  if (stockQty <= threshold) return { label: "부족", cls: "pill-warning", level: 1 };
  return { label: "정상", cls: "pill-success", level: 0 };
}

/** 재고 관리 화면 상단 요약 카드 3개(정상/위험/소진임박)를 위한 집계 —
 * computeInventoryInsights와 같은 판정 기준을 쓰되 카드 문구가 아닌 개수만 낸다. */
function summarizeInventoryStatus(inventory, topItemsWeek) {
  let normal = 0;
  let risk = 0;
  const flaggedItemIds = new Set();
  (inventory || []).forEach((item) => {
    const sev = stockSeverity(item.stock_quantity, item.low_stock_threshold ?? 5);
    if (sev.level === 0) normal++;
    else {
      risk++;
      flaggedItemIds.add(item.item_id);
    }
  });
  let etaSoon = 0;
  if (inventory && inventory.length && topItemsWeek && topItemsWeek.length) {
    const velocityById = Object.fromEntries(topItemsWeek.map((i) => [i.item_id, i.quantity / 7]));
    inventory.forEach((item) => {
      if (flaggedItemIds.has(item.item_id)) return;
      const velocity = velocityById[item.item_id] || 0;
      if (velocity <= 0) return;
      if (item.stock_quantity / velocity <= 3) etaSoon++;
    });
  }
  return { normal, risk, etaSoon };
}

function computeInventoryInsights({ inventory, nameById, topItemsWeek, withLink = true }) {
  const insights = [];
  const flaggedItemIds = new Set(); // 이미 위험/부족 카드에 나온 품목 — 소진예상 카드에서 중복 방지
  const link = withLink ? { actionLabel: "재고 관리로 이동", actionHref: "/inventory" } : {};

  if (inventory && inventory.length) {
    const critical = [];
    const low = [];
    inventory.forEach((item) => {
      const threshold = item.low_stock_threshold ?? 5;
      const name = nameById[item.item_id] ?? item.item_id;
      if (item.stock_quantity <= threshold * 0.5) { critical.push(name); flaggedItemIds.add(item.item_id); }
      else if (item.stock_quantity <= threshold) { low.push(name); flaggedItemIds.add(item.item_id); }
    });
    if (critical.length) {
      insights.push({
        level: "critical", icon: "🔴", title: `재고 위험 ${critical.length}개 품목 — 즉시 발주 필요`,
        detail: `${critical.join(", ")} — 임계치의 절반 이하로 떨어졌습니다.`,
        ...link,
        insightKey: "stock-critical",
        approveMessage: `재고 위험 품목(${critical.join(", ")})의 재입고를 진행해주세요. 적정 재입고 수량은 재고/판매 데이터를 참고해 판단해주세요.`,
      });
    }
    if (low.length) {
      insights.push({
        level: "warning", icon: "🟠", title: `재고 부족 ${low.length}개 품목 — 발주 검토`,
        detail: `${low.join(", ")} — 임계치 이하입니다.`,
        ...link,
        insightKey: "stock-low",
        approveMessage: `재고 부족 품목(${low.join(", ")})의 재입고를 진행해주세요. 적정 재입고 수량은 재고/판매 데이터를 참고해 판단해주세요.`,
      });
    }
  }

  if (inventory && inventory.length && topItemsWeek && topItemsWeek.length) {
    const velocityById = Object.fromEntries(topItemsWeek.map((i) => [i.item_id, i.quantity / 7]));
    const soon = [];
    const imminent = [];
    inventory.forEach((item) => {
      if (flaggedItemIds.has(item.item_id)) return;
      const velocity = velocityById[item.item_id] || 0;
      if (velocity <= 0) return;
      const daysLeft = item.stock_quantity / velocity;
      const name = nameById[item.item_id] ?? item.item_id;
      if (daysLeft <= 1) imminent.push(`${name}(약 ${daysLeft.toFixed(1)}일)`);
      else if (daysLeft <= 3) soon.push(`${name}(약 ${daysLeft.toFixed(1)}일)`);
    });
    if (imminent.length) {
      insights.push({
        level: "critical", icon: "🔴", title: `재고 소진 임박 ${imminent.length}개 품목 — 1일 내 품절 예상`,
        detail: `최근 판매 속도 기준: ${imminent.join(", ")}. 아직 임계치엔 안 걸렸지만 곧 끊깁니다.`,
        ...link,
        insightKey: "stock-eta-imminent",
        approveMessage: `1일 내 품절 예상 품목(${imminent.join(", ")})의 재입고를 진행해주세요. 수량은 최근 판매 속도를 참고해 판단해주세요.`,
      });
    }
    if (soon.length) {
      insights.push({
        level: "warning", icon: "🟠", title: `재고 소진 예상 ${soon.length}개 품목 — 3일 내 품절 예상`,
        detail: `최근 판매 속도 기준: ${soon.join(", ")}. 다음 입고 전 발주를 검토하세요.`,
        ...link,
        insightKey: "stock-eta-soon",
        approveMessage: `3일 내 품절 예상 품목(${soon.join(", ")})의 재입고를 진행해주세요. 수량은 최근 판매 속도를 참고해 판단해주세요.`,
      });
    }
  }

  return insights;
}

/**
 * 노쇼/미확인 예약 인사이트 — dashboard.js와 예약 관리 화면(reservations.js)이
 * 공유한다. mock-pos 예약 모델엔 "완료" 상태가 없어 BOOKED|CANCELED뿐이라,
 * 오래된 과거 예약까지 검사하면 정상 이용 건도 "노쇼"로 오탐하므로 최근
 * 24시간으로 한정한다.
 */
function computeReservationNoShowInsights({ reservationsAll, withLink = true }) {
  const insights = [];
  const link = withLink ? { actionLabel: "예약 관리로 이동", actionHref: "/reservations" } : {};
  if (reservationsAll && reservationsAll.length) {
    const now = Date.now();
    const dayMs = 24 * 60 * 60 * 1000;
    const overdue = reservationsAll.filter((r) => {
      if (r.status !== "BOOKED") return false;
      const t = new Date(r.datetime).getTime();
      return t < now && t >= now - dayMs;
    });
    if (overdue.length) {
      const list = overdue
        .slice()
        .sort((a, b) => new Date(b.datetime) - new Date(a.datetime))
        .slice(0, 5)
        .map((r) => new Date(r.datetime).toLocaleString("ko-KR", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }));
      insights.push({
        level: "warning", icon: "🟠", title: `노쇼/미확인 예약 ${overdue.length}건`,
        detail: `${list.join(", ")}${overdue.length > 5 ? ` 외 ${overdue.length - 5}건` : ""} — 이용 여부를 확인하고 처리해 주세요.`,
        ...link,
        insightKey: "reservation-noshow",
        approveMessage: `다음 미확인 예약을 확인 처리해주세요: ${list.join(", ")}. 고객과 연락이 닿지 않으면 노쇼로 판단해 취소 처리해주세요.`,
      });
    }
  }
  return insights;
}

/**
 * "사장님이 오늘 확인해야 할 것" 인사이트 카드 보드 — 원래 dashboard.js
 * 전용이었던 걸 화면 여러 개가 각자 인스턴스를 띄울 수 있게 일반화했다.
 * containerId: 카드 목록을 채울 엘리먼트. emptyId: 카드가 하나도 없을 때
 * 보여줄 엘리먼트(둘 다 이 화면 안에 이미 있어야 함).
 * onAfterSend: 승인/의견 전송 후(성공이든 실패든) 호출 — 보통 화면 데이터
 * 재조회 함수를 넘긴다(Active Verification: 타임아웃이어도 실제로는 처리가
 *끝났을 수 있어서다).
 */
function createInsightBoard(containerId, emptyId, { profile = "coordinator", onAfterSend } = {}) {
  const insightByKey = new Map();
  const resultCache = new Map();
  const sentCache = new Map();

  function render(insights) {
    const list = document.getElementById(containerId);
    const empty = emptyId ? document.getElementById(emptyId) : null;
    if (!list) return;
    list.innerHTML = "";
    insightByKey.clear();
    if (!insights.length) {
      if (empty) empty.hidden = false;
      return;
    }
    if (empty) empty.hidden = true;
    insights.forEach((insight) => {
      if (insight.insightKey) insightByKey.set(insight.insightKey, insight);
      const card = document.createElement("div");
      card.className = `insight-card insight-card--${insight.level}`;
      card.innerHTML = `
        <span class="insight-icon">${insight.icon}</span>
        <div style="flex: 1; min-width: 0;">
          <div class="insight-title">${insight.title}</div>
          <div class="insight-detail">${insight.detail}</div>
          ${insight.actionHref ? `<a class="insight-action" href="${insight.actionHref}">${insight.actionLabel} →</a>` : ""}
          ${insight.approveMessage ? `
          <div class="insight-actions">
            <button type="button" class="btn-primary btn-ghost--sm insight-approve-btn" data-insight-key="${insight.insightKey}">승인</button>
            <button type="button" class="btn-ghost btn-ghost--sm insight-comment-toggle" data-insight-key="${insight.insightKey}">의견 입력</button>
          </div>
          <div class="insight-comment-box" hidden>
            <textarea class="insight-comment-input" rows="2" placeholder="의견을 입력하세요"></textarea>
            <button type="button" class="btn-primary btn-ghost--sm insight-comment-submit" data-insight-key="${insight.insightKey}">전송</button>
          </div>
          <div class="sent-prompt" id="${containerId}-sent-${insight.insightKey}"></div>
          <div class="compact-result" id="${containerId}-result-${insight.insightKey}"></div>
          ` : ""}
        </div>
      `;
      list.appendChild(card);
      if (insight.approveMessage && sentCache.has(insight.insightKey)) {
        renderSentPrompt(document.getElementById(`${containerId}-sent-${insight.insightKey}`), sentCache.get(insight.insightKey));
      }
      if (insight.approveMessage && resultCache.has(insight.insightKey)) {
        renderCompactResult(document.getElementById(`${containerId}-result-${insight.insightKey}`), resultCache.get(insight.insightKey));
      }
    });
  }

  async function sendMessage(insightKey, message) {
    const resultEl = document.getElementById(`${containerId}-result-${insightKey}`);
    sentCache.set(insightKey, message);
    renderSentPrompt(document.getElementById(`${containerId}-sent-${insightKey}`), message);
    const pending = { status: "pending", text: "coordinator에게 전달하는 중…" };
    resultCache.set(insightKey, pending);
    renderCompactResult(resultEl, pending);

    const conversation_id = getConversationId(`conversation_id_${containerId}_${insightKey}`);
    try {
      const res = await fetch("/api/agent/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile, message, conversation_id }),
      });
      const data = await res.json();
      const result = { status: data.status === "ok" ? "ok" : data.status, text: data.text };
      resultCache.set(insightKey, result);
      renderCompactResult(document.getElementById(`${containerId}-result-${insightKey}`), result);
    } catch (err) {
      const result = { status: "error", text: "네트워크 오류가 발생했습니다. 다시 시도해 주세요." };
      resultCache.set(insightKey, result);
      renderCompactResult(document.getElementById(`${containerId}-result-${insightKey}`), result);
    } finally {
      if (onAfterSend) onAfterSend();
    }
  }

  function handleAction(e) {
    const approveBtn = e.target.closest(".insight-approve-btn");
    if (approveBtn) {
      const key = approveBtn.dataset.insightKey;
      const insight = insightByKey.get(key);
      if (insight && insight.approveMessage) sendMessage(key, insight.approveMessage);
      return;
    }
    const commentToggle = e.target.closest(".insight-comment-toggle");
    if (commentToggle) {
      const box = commentToggle.closest(".insight-actions").nextElementSibling;
      box.hidden = !box.hidden;
      return;
    }
    const commentSubmit = e.target.closest(".insight-comment-submit");
    if (commentSubmit) {
      const key = commentSubmit.dataset.insightKey;
      const box = commentSubmit.closest(".insight-comment-box");
      const textarea = box.querySelector(".insight-comment-input");
      const text = textarea.value.trim();
      if (!text) return;
      sendMessage(key, text);
      textarea.value = "";
      box.hidden = true;
    }
  }

  const listEl = document.getElementById(containerId);
  if (listEl) listEl.addEventListener("click", handleAction);

  return { render };
}

/**
 * 목록 행을 눌러서 그 자리에 상세를 펼치는 아코디언 — 채팅/모달 없이 "상세
 * 보기" 하나로 목록과 상세를 한 화면에 둔다. 한 번에 하나만 열린다.
 * rows: [{ cellsHtml, detailHtml, onExpand? }]. cellsHtml은 acc-row 안에
 * 그대로 삽입되는 칸들(예: `<div class="acc-col-name">...</div>`x n).
 */
function renderAccordion(containerId, rows) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = "";
  if (!rows.length) {
    container.innerHTML = '<p class="hint" style="padding:16px 18px;margin:0;">표시할 항목이 없습니다.</p>';
    return;
  }
  rows.forEach((row) => {
    const item = document.createElement("div");
    item.className = "acc-item";
    item.innerHTML = `
      <div class="acc-row">${row.cellsHtml}<div class="acc-toggle">상세 보기 ▾</div></div>
      <div class="acc-detail" hidden>${row.detailHtml}</div>
    `;
    const rowEl = item.querySelector(".acc-row");
    const detailEl = item.querySelector(".acc-detail");
    const toggleEl = item.querySelector(".acc-toggle");
    rowEl.addEventListener("click", () => {
      const isOpen = !detailEl.hidden;
      container.querySelectorAll(".acc-item").forEach((i) => {
        i.querySelector(".acc-detail").hidden = true;
        i.querySelector(".acc-row").classList.remove("open");
        i.querySelector(".acc-toggle").textContent = "상세 보기 ▾";
      });
      if (!isOpen) {
        detailEl.hidden = false;
        rowEl.classList.add("open");
        toggleEl.textContent = "접기 ▴";
        if (row.onExpand) row.onExpand(item);
      }
    });
    container.appendChild(item);
  });
}

/**
 * 채팅 스레드 대신 쓰는 접이식 처리 로그. 이 세션에서 실행한 액션을 한 줄로
 * 쌓아두고, 누르면 보낸 요청/응답이 펼쳐진다. 서버에 저장하지 않으므로
 * 새로고침하면 비워진다.
 */
function createActionLog(containerId) {
  const container = document.getElementById(containerId);
  const entries = [];
  let seq = 0;

  function render() {
    if (!container) return;
    if (!entries.length) {
      container.innerHTML = '<p class="hint" style="padding:16px 18px;margin:0;">아직 처리한 작업이 없습니다. 새로고침하면 로그가 초기화됩니다.</p>';
      return;
    }
    container.innerHTML = "";
    entries.forEach((entry) => {
      const item = document.createElement("div");
      item.className = "log-item";
      item.innerHTML = `
        <div class="log-row">
          <span class="log-time">${entry.time}</span>
          <span class="log-summary">${entry.summary}</span>
          ${entry.pillHtml || ""}
          <span class="log-toggle">펼쳐보기 ▾</span>
        </div>
        <div class="log-expand" hidden>
          ${entry.sentText ? `<div class="sent-line"><b>보낸 요청:</b> ${entry.sentText}</div>` : ""}
          ${entry.replyText ? `<div class="reply-line ${entry.replyTone || ""}">${entry.replyText}</div>` : ""}
        </div>
      `;
      const rowEl = item.querySelector(".log-row");
      const expandEl = item.querySelector(".log-expand");
      const toggleEl = item.querySelector(".log-toggle");
      rowEl.addEventListener("click", () => {
        const isOpen = !expandEl.hidden;
        expandEl.hidden = isOpen;
        rowEl.classList.toggle("open", !isOpen);
        toggleEl.textContent = isOpen ? "펼쳐보기 ▾" : "접기 ▴";
      });
      container.appendChild(item);
    });
  }

  function push(entry) {
    entries.unshift({
      time: entry.time || new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
      ...entry,
      id: ++seq,
    });
    render();
  }

  render();
  return { push };
}
