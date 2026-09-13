/**
 * 고객 셀프 주문 화면(/customer/order). 메뉴 칩 클릭 → 수량 칩 클릭 → 장바구니
 * 담기를 반복하다가 "주문 확정하기"를 누르면 이름 입력 후 실제로
 * coordinator에게 주문 메시지를 전송한다(mock-pos에 실제 주문 레코드 생성).
 * 결제까지 포함된 요청이라 coordinator가 HITL 승인을 요구할 수 있다 — 그건
 * 정상 동작이며, 이 화면은 요청 접수까지만 책임진다.
 */
let catalog = [];
const cart = []; // [{item_id, name, unit_price, qty}]
let pendingItem = null;

function conversationId() {
  return getConversationId("conversation_id_customer_order");
}

async function loadCatalog() {
  const grid = document.getElementById("order-menu-grid");
  try {
    const res = await fetch("/api/pos/catalog/items");
    if (!res.ok) throw new Error("failed");
    catalog = await res.json();
    if (!catalog.length) {
      grid.innerHTML = '<p class="hint">등록된 메뉴가 없습니다.</p>';
      return;
    }
    renderMenu();
  } catch (err) {
    grid.innerHTML = '<p class="hint">메뉴를 불러오지 못했습니다.</p>';
  }
}

function renderMenu() {
  const grid = document.getElementById("order-menu-grid");
  grid.innerHTML = "";
  catalog.forEach((item) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "menu-chip";
    chip.innerHTML = `<span class="menu-chip-name">${item.name}</span><span class="menu-chip-price">${item.unit_price.toLocaleString()}원</span>`;
    chip.addEventListener("click", () => selectItemForQty(item));
    grid.appendChild(chip);
  });
}

function selectItemForQty(item) {
  pendingItem = item;
  document.getElementById("order-qty-item-name").textContent = item.name;
  const qtyGrid = document.getElementById("order-qty-grid");
  qtyGrid.innerHTML = "";
  for (let qty = 1; qty <= 5; qty++) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "qty-chip";
    chip.textContent = `${qty}잔`;
    chip.addEventListener("click", () => addToCart(item, qty));
    qtyGrid.appendChild(chip);
  }
  document.getElementById("order-qty-step").hidden = false;
}

function addToCart(item, qty) {
  const existing = cart.find((line) => line.item_id === item.item_id);
  if (existing) {
    existing.qty += qty;
  } else {
    cart.push({ item_id: item.item_id, name: item.name, unit_price: item.unit_price, qty });
  }
  pendingItem = null;
  document.getElementById("order-qty-step").hidden = true;
  renderCart();
}

function renderCart() {
  const step = document.getElementById("order-cart-step");
  const summary = document.getElementById("order-cart-summary");
  if (!cart.length) {
    step.hidden = true;
    return;
  }
  step.hidden = false;
  const total = cart.reduce((sum, line) => sum + line.unit_price * line.qty, 0);
  summary.innerHTML =
    cart.map((line) => `<div class="cart-line"><span>${line.name} x${line.qty}</span><span>${(line.unit_price * line.qty).toLocaleString()}원</span></div>`).join("") +
    `<div class="cart-line cart-line-total"><span>합계</span><span>${total.toLocaleString()}원</span></div>`;
}

function showCheckout() {
  document.getElementById("order-checkout-step").hidden = false;
  document.getElementById("order-cart-step").hidden = true;
}

function backToCart() {
  document.getElementById("order-checkout-step").hidden = true;
  renderCart();
}

async function submitOrder() {
  const name = document.getElementById("order-customer-name").value.trim();
  let message = cart.map((line) => `${line.name} ${line.qty}잔`).join(", ") + " 주문할게요.";
  if (name) message += ` 이름: ${name}.`;

  const submitBtn = document.getElementById("order-checkout-submit");
  submitBtn.disabled = true;
  renderSentPrompt(document.getElementById("order-sent-prompt"), message);
  renderCompactResult(document.getElementById("order-result"), { status: "pending", text: "주문을 접수하는 중…" });

  try {
    const res = await fetch("/api/agent/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: "coordinator", message, conversation_id: conversationId() }),
    });
    const data = await res.json();
    renderCompactResult(document.getElementById("order-result"), { status: data.status === "ok" ? "ok" : data.status, text: data.text });
  } catch (err) {
    renderCompactResult(document.getElementById("order-result"), { status: "error", text: "네트워크 오류가 발생했습니다. 다시 시도해 주세요." });
  } finally {
    submitBtn.disabled = false;
  }
}

document.getElementById("order-cart-add-more").addEventListener("click", () => {
  document.getElementById("order-cart-step").hidden = true;
});
document.getElementById("order-cart-confirm").addEventListener("click", showCheckout);
document.getElementById("order-checkout-back").addEventListener("click", backToCart);
document.getElementById("order-checkout-submit").addEventListener("click", submitOrder);

loadCatalog();
