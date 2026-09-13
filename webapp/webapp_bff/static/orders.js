/**
 * 화면 2(주문 접수). 품목 선택 폼은 별도 쓰기 경로가 아니라, 자연어 메시지를
 * 자동 구성해 아래 채팅과 "동일한" /api/agent/message 릴레이로 보낸다 — 두
 * 방식 모두 하나의 쓰기 경로로 수렴한다(curried-percolating-ocean.md).
 */
const selectedQty = {}; // item_id -> quantity
let catalogNameById = {};
let catalogItems = [];
// 자유 채팅과 품목-피커가 같은 conversation_id(=hermes 세션)를 공유하므로,
// 채팅 응답을 기다리는 동안 품목-피커로도 겹쳐 보내지 못하게 잠근다.
let chatBusy = false;
let awaitingPickerConfirm = false; // 자유채팅과 품목-피커가 conversation_id를 공유하므로, onReply가
// 온 결과가 "방금 피커로 보낸 확정" 응답인지 구분해서 #order-confirm-result에 따로 보여준다.

async function loadCatalog() {
  const container = document.getElementById("order-items");
  const res = await fetch("/api/pos/catalog/items");
  if (!res.ok) {
    container.innerHTML = '<p class="hint">품목을 불러오지 못했습니다.</p>';
    return [];
  }
  const items = await res.json();
  catalogItems = items;
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
      const plusBtn = container.querySelector(`.qty-btn[data-item="${itemId}"][data-delta="1"]`);
      if (plusBtn) plusBtn.classList.toggle("qty-btn--active", next > 0);
      updateSubmitButton(items);
    });
  });
}

function updateSubmitButton(items) {
  const itemCount = Object.values(selectedQty).reduce((sum, q) => sum + q, 0);
  const amount = items.reduce((sum, item) => sum + (selectedQty[item.item_id] || 0) * item.unit_price, 0);
  const btn = document.getElementById("order-submit");
  btn.disabled = itemCount === 0 || chatBusy;
  btn.dataset.items = JSON.stringify(items);

  const countEl = document.getElementById("cart-count");
  const totalEl = document.getElementById("cart-total");
  if (itemCount === 0) {
    countEl.textContent = "품목을 선택하세요";
    totalEl.textContent = "";
  } else {
    countEl.textContent = `총 ${itemCount}개 품목`;
    totalEl.textContent = `${amount.toLocaleString()}원`;
  }
}

const ORDER_STATUS_LABEL = {
  OPEN: ["대기", "pill-warning"],
  COMPLETED: ["완료", "pill-success"],
  CANCELED: ["취소", "pill-danger"],
  PARTIALLY_REFUNDED: ["부분환불", "pill-warning"],
  REFUNDED: ["환불", "pill-danger"],
};

function renderOrderStatus(status) {
  const [label, cls] = ORDER_STATUS_LABEL[status] || [status, ""];
  return `<span class="pill ${cls}">${label}</span>`;
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
      <td>${renderOrderStatus(order.status)}</td>
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
    onReply: (data) => {
      if (awaitingPickerConfirm) {
        awaitingPickerConfirm = false;
        renderCompactResult(document.getElementById("order-confirm-result"), {
          status: data.status === "ok" ? "ok" : data.status,
          text: data.text,
        });
      }
      loadRecentOrders();
    },
    onBusyChange: (busy) => {
      chatBusy = busy;
      updateSubmitButton(catalogItems);
    },
    demoBarId: "orders-demo-bar",
    demoQueue: [
      { label: "12:00 점심 피크 주문 (사장님의 하루)", message: "라떼 2잔, 아메리카노 1잔 주문 들어왔어, 결제까지 처리해줘." },
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
    awaitingPickerConfirm = true;
    renderCompactResult(document.getElementById("order-confirm-result"), {
      status: "pending", text: "coordinator에게 전달하는 중…",
    });
    document.getElementById("orders-form").requestSubmit();
    Object.keys(selectedQty).forEach((k) => (selectedQty[k] = 0));
    document.querySelectorAll(".qty-value").forEach((el) => (el.textContent = "0"));
    document.querySelectorAll(".qty-btn--active").forEach((el) => el.classList.remove("qty-btn--active"));
    updateSubmitButton(items);
    document.getElementById("order-customer-name").value = "";
    document.getElementById("order-note").value = "";
  });
});
