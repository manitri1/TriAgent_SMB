let catalogNameById = {};

async function loadCatalog() {
  const res = await fetch("/api/pos/catalog/items");
  if (!res.ok) return [];
  const items = await res.json();
  catalogNameById = Object.fromEntries(items.map((i) => [i.item_id, i.name]));
  return items;
}

/** 재고 심각도 3단계 — 위험(임계치 절반 이하) > 부족(임계치 이하) > 정상. */
function stockSeverity(stockQty, threshold) {
  if (stockQty <= threshold * 0.5) return { label: "위험", cls: "pill-danger", level: 2 };
  if (stockQty <= threshold) return { label: "부족", cls: "pill-warning", level: 1 };
  return { label: "정상", cls: "pill-success", level: 0 };
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

async function loadInventory() {
  const tbody = document.getElementById("inventory-rows");
  const res = await fetch("/api/pos/inventory");
  if (!res.ok) {
    tbody.innerHTML = '<tr><td colspan="4" class="empty">불러오지 못했습니다.</td></tr>';
    return;
  }
  const items = await res.json();
  if (!items.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="empty">등록된 품목이 없습니다.</td></tr>';
    return;
  }
  tbody.innerHTML = "";
  items.forEach((item) => {
    const threshold = item.low_stock_threshold ?? 5;
    const severity = stockSeverity(item.stock_quantity, threshold);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${catalogNameById[item.item_id] ?? item.item_id}</td>
      <td>${item.stock_quantity}</td>
      <td>${threshold}</td>
      <td><span class="pill ${severity.cls}">${severity.label}</span></td>
    `;
    tbody.appendChild(tr);
  });
  renderRestockQuickChips(items);
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
  let id = localStorage.getItem("conversation_id_inventory_restock");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("conversation_id_inventory_restock", id);
  }
  return id;
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

async function submitRestockRequest(e) {
  e.preventDefault();
  const itemName = document.getElementById("restock-item").value;
  const qty = document.getElementById("restock-qty").value;
  const reason = document.getElementById("restock-reason").value.trim();
  if (!itemName || !qty) return;

  let message = `다음 품목 재입고를 요청합니다: ${itemName} ${qty}개.`;
  if (reason) message += ` 사유: ${reason}.`;

  const replyBox = document.getElementById("restock-reply");
  const submitBtn = e.target.querySelector("button[type=submit]");
  submitBtn.disabled = true;
  replyBox.className = "restock-reply restock-reply--pending";
  replyBox.textContent = "coordinator에게 전달하는 중…";

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
    replyBox.className = `restock-reply${data.status === "ok" ? "" : ` restock-reply--${data.status}`}`;
    replyBox.textContent = data.text;
  } catch (err) {
    replyBox.className = "restock-reply restock-reply--error";
    replyBox.textContent = "네트워크 오류가 발생했습니다. 다시 시도해 주세요.";
  } finally {
    submitBtn.disabled = false;
    // 상태와 무관하게 재조회 — 타임아웃이어도 실제로는 처리 중일 수 있다
    // (Phase 0 실측, Active Verification 원칙).
    loadInventory();
    restockDemoIndex++;
    loadRestockDemoStep();
  }
}

document.getElementById("refresh-inventory").addEventListener("click", loadInventory);
document.getElementById("restock-form").addEventListener("submit", submitRestockRequest);
loadCatalogIntoRestockSelect();
