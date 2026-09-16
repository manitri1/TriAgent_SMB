let catalogNameById = {};

const inventoryActionBoard = createInsightBoard("inventory-actions", "inventory-actions-empty", {
  onAfterSend: loadInventory,
});
const inventoryLog = createActionLog("inventory-log");
const inventoryAccordion = createRowActionAccordion("inventory-accordion", {
  profile: "coordinator",
  storageKeyPrefix: "conversation_id_inventory_row",
  onAfterSend: loadInventory,
});

async function loadCatalog() {
  const res = await fetch("/api/pos/catalog/items");
  if (!res.ok) return [];
  const items = await res.json();
  catalogNameById = Object.fromEntries(items.map((i) => [i.item_id, i.name]));
  return items;
}

function renderRestockQuickChips(items) {
  const bar = document.getElementById("restock-quick-chips");
  if (!bar) return;
  const concerning = items
    .map((item) => ({ item, severity: stockSeverity(item.stock_quantity, item.low_stock_threshold ?? 5) }))
    .filter(({ severity }) => severity.level > 0)
    .sort((a, b) => b.severity.level - a.severity.level);

  bar.innerHTML = "";
  if (!concerning.length) return;
  const label = document.createElement("span");
  label.className = "chip-row-label";
  label.textContent = "빠른 선택";
  bar.appendChild(label);
  concerning.forEach(({ item, severity }) => {
    const name = catalogNameById[item.item_id] ?? item.item_id;
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = `quick-chip ${severity.level === 2 ? "quick-chip--danger" : "quick-chip--warning"}`;
    chip.textContent = name;
    chip.addEventListener("click", () => {
      const select = document.getElementById("restock-item");
      if (select && [...select.options].some((o) => o.value === name)) select.value = name;
      document.getElementById("restock-qty").focus();
    });
    bar.appendChild(chip);
  });
}

function inventoryAccordionRows(items, etaDaysById, velocityById) {
  return items.map((item) => {
    const threshold = item.low_stock_threshold ?? 5;
    const severity = stockSeverity(item.stock_quantity, threshold);
    const name = catalogNameById[item.item_id] ?? item.item_id;
    const etaDays = etaDaysById[item.item_id];
    const velocity = velocityById[item.item_id] || 0;
    const cellsHtml = `
      <div class="acc-col-name">${name}</div>
      <div class="acc-col-fig"${severity.level > 0 ? ' style="color: var(--danger); font-weight: 700;"' : ""}>${item.stock_quantity} / ${threshold}</div>
      <div class="acc-col-pill">${statusPill(severity.label, severity.level === 2 ? "danger" : severity.level === 1 ? "warning" : "success")}</div>
    `;
    const factsHtml = `
      <div class="detail-kv"><span class="detail-kv-k">현재 재고</span><span class="detail-kv-v">${item.stock_quantity}개 (임계치 ${threshold}개)</span></div>
      <div class="detail-kv"><span class="detail-kv-k">일평균 판매량</span><span class="detail-kv-v">${velocity > 0 ? `${velocity.toFixed(1)}개 / 일` : "최근 판매 데이터 없음"}</span></div>
      <div class="detail-kv"><span class="detail-kv-k">소진 예상</span><span class="detail-kv-v">${etaDays != null ? `최근 판매 속도 기준 약 ${etaDays.toFixed(1)}일 후` : "판매 속도 데이터 부족"}</span></div>
      <div class="detail-kv"><span class="detail-kv-k">마지막 갱신</span><span class="detail-kv-v">${new Date(item.updated_at).toLocaleString("ko-KR", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" })}</span></div>
    `;
    return {
      id: item.item_id,
      cellsHtml,
      factsHtml,
      contextLabel: `재고 · ${name}`,
      editPlaceholder: `예: ${name} 재고 수량을 다시 세어보니 달라요, 수정해줘`,
      actions: [
        {
          label: "재입고 요청",
          tone: "primary",
          message: `품목 ${name} 재입고를 요청합니다. 적정 재입고 수량은 재고/판매 데이터를 참고해 판단해주세요.`,
        },
        {
          label: "재고 수량 직접 수정",
          tone: "ghost",
          prefill: true,
          message: `품목 ${name}의 재고 수량을 __개로 수정해주세요.`,
        },
        {
          label: "품절 처리",
          tone: "danger",
          confirm: `${name}을(를) 품절 처리할까요?`,
          message: `품목 ${name}을(를) 품절 처리해주세요.`,
        },
      ],
    };
  });
}

async function loadInventory() {
  const container = document.getElementById("inventory-accordion");
  const [invRes, topItemsWeek] = await Promise.all([
    fetch("/api/pos/inventory"),
    fetch("/api/pos/reports/top-items?period=week&limit=50").then((r) => (r.ok ? r.json() : [])),
  ]);
  if (!invRes.ok) {
    container.innerHTML = '<p class="hint" style="padding:16px 18px;margin:0;">불러오지 못했습니다.</p>';
    return;
  }
  const items = await invRes.json();
  if (!items.length) {
    container.innerHTML = '<p class="hint" style="padding:16px 18px;margin:0;">등록된 품목이 없습니다.</p>';
    return;
  }

  const nameById = catalogNameById;
  const { normal, risk, etaSoon } = summarizeInventoryStatus(items, topItemsWeek);
  document.getElementById("inv-stat-normal").textContent = normal;
  document.getElementById("inv-stat-risk").textContent = risk;
  document.getElementById("inv-stat-eta").textContent = etaSoon;

  const velocityById = Object.fromEntries((topItemsWeek || []).map((i) => [i.item_id, i.quantity / 7]));
  const etaDaysById = {};
  items.forEach((item) => {
    const v = velocityById[item.item_id] || 0;
    if (v > 0) etaDaysById[item.item_id] = item.stock_quantity / v;
  });

  const rows = inventoryAccordionRows(items, etaDaysById, velocityById);
  inventoryAccordion.render(rows);

  const insights = computeInventoryInsights({ inventory: items, nameById, topItemsWeek, withLink: false });
  inventoryActionBoard.render(insights);

  renderRestockQuickChips(items);
}

function openRestockForm(itemName) {
  document.getElementById("restock-form-panel").hidden = false;
  document.getElementById("restock-form-toggle").hidden = true;
  if (itemName) {
    const select = document.getElementById("restock-item");
    if (select && [...select.options].some((o) => o.value === itemName)) select.value = itemName;
    document.getElementById("restock-qty").focus();
  }
}

function closeRestockForm() {
  document.getElementById("restock-form-panel").hidden = true;
  document.getElementById("restock-form-toggle").hidden = false;
}

async function loadCatalogIntoRestockSelect() {
  const select = document.getElementById("restock-item");
  const items = await loadCatalog();
  if (!items.length) {
    select.innerHTML = '<option value="">품목을 불러오지 못했습니다</option>';
    return;
  }
  select.innerHTML = items.map((i) => `<option value="${i.name}">${i.name}</option>`).join("");
  loadInventory();
  loadRestockDemoStep();
}

function restockConversationId() {
  return getConversationId("conversation_id_inventory_restock");
}

/**
 * 재입고 요청 데모 큐 — 품목/수량/사유가 폼에 미리 채워지고, 기존 "재입고 요청"
 * 버튼을 누르면 그대로 전송된다. 응답을 받으면 다음 데모가 자동으로 채워진다
 * (chat.js의 demoQueue와 동일한 패턴).
 */
const RESTOCK_DEMO_QUEUE = [
  { label: "09:10 원두 결품 발견 (사장님의 하루, 승인 필요할 수 있음)", item: "아메리카노", qty: 50, reason: "원두 완전 품절, 긴급 대량 재입고 필요" },
  { label: "아메리카노 재입고 (저재고)", item: "아메리카노", qty: 30, reason: "재고 소진, 긴급 재입고 필요" },
  { label: "콜드브루 재입고", item: "콜드브루", qty: 15, reason: "여름철 수요 증가 대비" },
  { label: "시즌 케이크 대량 발주 (승인 필요할 수 있음)", item: "시즌 케이크(딸기)", qty: 100, reason: "행사용 대량 발주" },
];
let restockDemoIndex = 0;

function renderRestockDemoBar() {
  const bar = document.getElementById("inventory-demo-bar");
  if (!bar) return;
  bar.innerHTML = "";
  const label = document.createElement("span");
  label.className = "demo-label";
  label.textContent =
    restockDemoIndex >= RESTOCK_DEMO_QUEUE.length
      ? "데모 완료"
      : `데모 ${restockDemoIndex + 1}/${RESTOCK_DEMO_QUEUE.length} · ${RESTOCK_DEMO_QUEUE[restockDemoIndex].label}`;
  bar.appendChild(label);
  const resetBtn = document.createElement("button");
  resetBtn.type = "button";
  resetBtn.className = "demo-reset";
  resetBtn.textContent = "처음부터";
  resetBtn.addEventListener("click", () => {
    restockDemoIndex = 0;
    loadRestockDemoStep();
  });
  bar.appendChild(resetBtn);
}

function loadRestockDemoStep() {
  renderRestockDemoBar();
  if (restockDemoIndex >= RESTOCK_DEMO_QUEUE.length) return;
  const step = RESTOCK_DEMO_QUEUE[restockDemoIndex];
  const select = document.getElementById("restock-item");
  if (select && [...select.options].some((o) => o.value === step.item)) {
    select.value = step.item;
  }
  document.getElementById("restock-qty").value = step.qty;
  document.getElementById("restock-reason").value = step.reason;
}

/** coordinator가 HITL 게이트 확인(수량/범위 등)을 되물으면, 그 카드의 칩을
 * 눌러 여기로 다시 들어온다 — submitRestockRequest와 동일한 전송/로그 경로를
 * 그대로 재사용해 같은 대화(conversation_id)에 후속 지시를 이어 보낸다. */
async function sendRestockMessage(message, summary) {
  const replyBox = document.getElementById("restock-reply");
  const submitBtn = document.querySelector("#restock-form button[type=submit]");
  if (submitBtn) submitBtn.disabled = true;
  renderSentPrompt(document.getElementById("restock-sent-prompt"), message);
  renderCompactResult(replyBox, { status: "pending", text: "coordinator에게 전달하는 중…" });

  try {
    const res = await fetch("/api/agent/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profile: "coordinator",
        message,
        conversation_id: restockConversationId(),
      }),
    });
    const data = await res.json();
    const result = { status: data.status === "ok" ? "ok" : data.status, text: data.text };
    renderCompactResult(replyBox, result, { onFollowup: (msg) => sendRestockMessage(msg, summary) });
    inventoryLog.push({
      summary,
      pillHtml: statusPill(result.status === "ok" ? "완료" : result.status === "timeout" ? "확인 필요" : "오류", result.status === "ok" ? "success" : "warning"),
      sentText: message,
      replyText: result.text,
      replyTone: result.status === "ok" ? "" : result.status === "error" ? "error" : "warn",
    });
  } catch (err) {
    renderCompactResult(replyBox, { status: "error", text: "네트워크 오류가 발생했습니다. 다시 시도해 주세요." });
  } finally {
    if (submitBtn) submitBtn.disabled = false;
    // 상태와 무관하게 재조회 — 타임아웃이어도 실제로는 처리 중일 수 있다
    // (Phase 0 실측, Active Verification 원칙).
    loadInventory();
    restockDemoIndex++;
    loadRestockDemoStep();
  }
}

async function submitRestockRequest(e) {
  e.preventDefault();
  const itemName = document.getElementById("restock-item").value;
  const qty = document.getElementById("restock-qty").value;
  const reason = document.getElementById("restock-reason").value.trim();
  if (!itemName || !qty) return;

  let message = `다음 품목 재입고를 요청합니다: ${itemName} ${qty}개.`;
  if (reason) message += ` 사유: ${reason}.`;
  const summary = `${itemName} 재입고 요청 (${qty}개)${reason ? ` · 사유: ${reason}` : ""}`;
  await sendRestockMessage(message, summary);
}

document.getElementById("refresh-inventory").addEventListener("click", loadInventory);
document.getElementById("restock-form").addEventListener("submit", submitRestockRequest);
document.getElementById("restock-form-toggle").addEventListener("click", () => openRestockForm());
document.getElementById("restock-form-close").addEventListener("click", closeRestockForm);
loadCatalogIntoRestockSelect();
