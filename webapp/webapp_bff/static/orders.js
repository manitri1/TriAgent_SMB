/**
 * 화면 2(주문 접수). 품목 선택 폼은 별도 쓰기 경로가 아니라, 자연어 메시지를
 * 자동 구성해 아래 채팅과 "동일한" /api/agent/message 릴레이로 보낸다 — 두
 * 방식 모두 하나의 쓰기 경로로 수렴한다(curried-percolating-ocean.md).
 */
const selectedQty = {}; // item_id -> quantity
let catalogNameById = {};

async function loadCatalog() {
  const container = document.getElementById("order-items");
  const res = await fetch("/api/pos/catalog/items");
  if (!res.ok) {
    container.innerHTML = '<p class="hint">품목을 불러오지 못했습니다.</p>';
    return [];
  }
  const items = await res.json();
  catalogNameById = Object.fromEntries(items.map((i) => [i.item_id, i.name]));
  if (!items.length) {
    container.innerHTML = '<p class="hint">등록된 품목이 없습니다.</p>';
    return items;
  }
  container.innerHTML = "";
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "order-item-row";
    row.innerHTML = `
      <span class="order-item-name">${item.name} <span class="order-item-price">${item.unit_price.toLocaleString()}원</span></span>
      <div class="qty-stepper">
        <button type="button" class="qty-btn" data-item="${item.item_id}" data-delta="-1">-</button>
        <span class="qty-value" id="qty-${item.item_id}">0</span>
        <button type="button" class="qty-btn" data-item="${item.item_id}" data-delta="1">+</button>
      </div>
    `;
    container.appendChild(row);
  });

  container.querySelectorAll(".qty-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const itemId = btn.dataset.item;
      const delta = Number(btn.dataset.delta);
      const next = Math.max(0, (selectedQty[itemId] || 0) + delta);
      selectedQty[itemId] = next;
      document.getElementById(`qty-${itemId}`).textContent = next;
      updateSubmitButton(items);
    });
  });
}

function updateSubmitButton(items) {
  const total = Object.values(selectedQty).reduce((sum, q) => sum + q, 0);
  const btn = document.getElementById("order-submit");
  btn.disabled = total === 0;
  btn.textContent = total === 0 ? "주문 접수 (품목을 선택하세요)" : `주문 접수 (${total}개 품목)`;
  btn.dataset.items = JSON.stringify(items);
}

function composeOrderMessage(items) {
  const parts = Object.entries(selectedQty)
    .filter(([, qty]) => qty > 0)
    .map(([itemId, qty]) => {
      const item = items.find((i) => i.item_id === itemId);
      return `${item ? item.name : itemId} ${qty}잔`;
    });
  let message = `다음 주문을 접수해 주세요: ${parts.join(", ")}. 결제까지 처리해 주세요.`;
  const name = document.getElementById("order-customer-name").value.trim();
  const note = document.getElementById("order-note").value.trim();
  if (name) message += ` 고객: ${name}.`;
  if (note) message += ` 메모: ${note}.`;
  return message;
}

async function loadRecentOrders() {
  const tbody = document.getElementById("orders-rows");
  const res = await fetch("/api/pos/orders");
  if (!res.ok) {
    tbody.innerHTML = '<tr><td colspan="4" class="empty">불러오지 못했습니다.</td></tr>';
    return;
  }
  const orders = await res.json();
  if (!orders.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="empty">주문 내역이 없습니다.</td></tr>';
    return;
  }
  const recent = orders.slice(-10).reverse();
  tbody.innerHTML = "";
  recent.forEach((order) => {
    const items = order.line_items
      .map((li) => `${catalogNameById[li.item_id] ?? li.item_id} x${li.quantity}`)
      .join(", ");
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${order.order_id}</td>
      <td>${items}</td>
      <td>${order.total_amount.toLocaleString()}원</td>
      <td>${order.status}</td>
    `;
    tbody.appendChild(tr);
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  await loadCatalog();
  loadRecentOrders();
  document.getElementById("refresh-orders").addEventListener("click", loadRecentOrders);

  initChatWidget({
    formId: "orders-form",
    inputId: "orders-input",
    threadId: "orders-thread",
    profile: "coordinator",
    storageKey: "conversation_id_orders",
    onReply: loadRecentOrders,
    demoBarId: "orders-demo-bar",
    demoQueue: [
      { label: "아메리카노 2잔 주문", message: "아메리카노 2잔 주문 들어왔어, 결제까지 처리해줘." },
      { label: "라떼+머핀 세트 주문", message: "라떼 1잔, 블루베리 머핀 1개 주문이요. 결제까지 부탁해." },
      { label: "카푸치노 3잔 주문", message: "카푸치노 3잔 주문 들어왔어, 결제까지 처리해줘." },
      { label: "환불 요청 (승인 필요)", message: "방금 카푸치노 주문 환불해줘, 고객이 취소를 요청했어." },
    ],
  });

  document.getElementById("order-submit").addEventListener("click", () => {
    const items = JSON.parse(document.getElementById("order-submit").dataset.items || "[]");
    const message = composeOrderMessage(items);
    const input = document.getElementById("orders-input");
    input.value = message;
    document.getElementById("orders-form").requestSubmit();
    Object.keys(selectedQty).forEach((k) => (selectedQty[k] = 0));
    document.querySelectorAll(".qty-value").forEach((el) => (el.textContent = "0"));
    updateSubmitButton(items);
    document.getElementById("order-customer-name").value = "";
    document.getElementById("order-note").value = "";
  });
});
