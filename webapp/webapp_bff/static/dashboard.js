async function getJSON(path) {
  const res = await fetch(path);
  if (!res.ok) return null;
  return res.json();
}

let dailyChart, topChart, inventoryChart;

function upsertChart(existing, ctx, config) {
  if (existing) existing.destroy();
  return new Chart(ctx, config);
}

async function loadDashboard() {
  const catalog = await getJSON("/api/pos/catalog/items");
  const nameById = Object.fromEntries((catalog || []).map((i) => [i.item_id, i.name]));

  const salesToday = await getJSON("/api/pos/reports/sales?period=today");
  const salesWeek = await getJSON("/api/pos/reports/sales?period=week");
  const settlement = await getJSON("/api/pos/reports/settlement?period=today");
  const margin = await getJSON("/api/pos/reports/margin?period=today");
  const daily = await getJSON("/api/pos/reports/sales/daily?days=7");
  const topItems = await getJSON("/api/pos/reports/top-items?period=today&limit=5");
  const inventory = await getJSON("/api/pos/inventory");
  const today = new Date().toISOString().slice(0, 10);
  const reservations = await getJSON(`/api/pos/reservations?date=${today}&status=BOOKED`);
  const repeatCustomers = await getJSON("/api/pos/reports/repeat-customers?period=all&min_orders=2");

  if (salesToday) document.getElementById("sales-today").textContent = salesToday.total_sales.toLocaleString() + "원";
  if (salesWeek) document.getElementById("sales-week").textContent = salesWeek.total_sales.toLocaleString() + "원";
  if (settlement) {
    document.getElementById("settle-gross").textContent = settlement.gross_sales.toLocaleString() + "원";
    document.getElementById("settle-count").textContent = settlement.payment_count;
    document.getElementById("settle-refund").textContent = settlement.refunded_amount.toLocaleString() + "원";
    document.getElementById("settle-refund-count").textContent = settlement.refunded_count;
    document.getElementById("settle-partial-refund").textContent = settlement.partial_refund_amount.toLocaleString() + "원";
    document.getElementById("settle-partial-refund-count").textContent = settlement.partial_refund_count;
  }
  if (margin) {
    document.getElementById("margin-revenue").textContent = margin.total_revenue.toLocaleString() + "원";
    document.getElementById("margin-cost").textContent = margin.total_cost.toLocaleString() + "원";
    document.getElementById("margin-gross").textContent = margin.gross_margin.toLocaleString() + "원";
    document.getElementById("margin-rate").textContent = (margin.margin_rate * 100).toFixed(1) + "%";
  }

  if (daily) {
    dailyChart = upsertChart(dailyChart, document.getElementById("chart-daily"), {
      type: "line",
      data: {
        labels: daily.map((d) => d.date.slice(5)),
        datasets: [{ label: "매출", data: daily.map((d) => d.total_sales), borderColor: "#2563eb", tension: 0.2 }],
      },
      options: { plugins: { legend: { display: false } } },
    });
  }

  if (topItems) {
    topChart = upsertChart(topChart, document.getElementById("chart-top"), {
      type: "bar",
      data: {
        labels: topItems.map((i) => i.name),
        datasets: [{ label: "매출", data: topItems.map((i) => i.revenue), backgroundColor: "#16a34a" }],
      },
      options: { indexAxis: "y", plugins: { legend: { display: false } } },
    });
  }

  if (inventory) {
    inventoryChart = upsertChart(inventoryChart, document.getElementById("chart-inventory"), {
      type: "bar",
      data: {
        labels: inventory.map((i) => nameById[i.item_id] ?? i.item_id),
        datasets: [{
          label: "재고",
          data: inventory.map((i) => i.stock_quantity),
          backgroundColor: inventory.map((i) =>
            i.stock_quantity <= (i.low_stock_threshold ?? 5) ? "#dc2626" : "#94a3b8"
          ),
        }],
      },
      options: { plugins: { legend: { display: false } } },
    });
  }

  const tbody = document.getElementById("table-reservations");
  tbody.innerHTML = "";
  (reservations || []).forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${new Date(r.datetime).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })}</td><td>${r.customer_id}</td><td>${r.service ?? "-"}</td>`;
    tbody.appendChild(tr);
  });

  const repeatTbody = document.getElementById("table-repeat-customers");
  repeatTbody.innerHTML = "";
  (repeatCustomers || []).forEach((c) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${c.name ?? c.customer_id}</td><td>${c.order_count}</td><td>${c.total_spent.toLocaleString()}원</td>`;
    repeatTbody.appendChild(tr);
  });
}

document.getElementById("refresh").addEventListener("click", loadDashboard);

let autoTimer = null;
document.getElementById("auto").addEventListener("change", (e) => {
  if (e.target.checked) {
    autoTimer = setInterval(loadDashboard, 10000);
  } else if (autoTimer) {
    clearInterval(autoTimer);
  }
});

loadDashboard();
