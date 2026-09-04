"""로컬 데모 전용 실적 대시보드.

docs/12-web-gui-demo.md 설계에 따라 mock-pos 자신의 REST API를 같은 오리진에서
호출하는 자체 완결형 HTML 페이지를 반환한다. 브라우저 JS에 X-API-Key를
하드코딩하므로(dev-key) 외부에 노출하는 배포에는 적합하지 않다 — 로컬 시연 전용.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["dashboard"])

_PAGE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Mock POS 실적 대시보드 (데모)</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  body { font-family: -apple-system, "Malgun Gothic", sans-serif; margin: 24px; background: #f5f5f7; color: #1d1d1f; }
  h1 { font-size: 20px; }
  .warn { color: #b45309; font-size: 13px; margin-bottom: 16px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 24px; }
  .card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
  .card h2 { font-size: 14px; margin: 0 0 8px; color: #555; }
  .card .value { font-size: 24px; font-weight: 600; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #eee; }
  .low-stock { color: #b91c1c; font-weight: 600; }
  button { padding: 8px 14px; border-radius: 6px; border: 1px solid #ccc; background: #fff; cursor: pointer; }
  canvas { max-height: 260px; }
</style>
</head>
<body>
<h1>Mock POS 실적 대시보드 (데모)</h1>
<p class="warn">⚠️ 로컬 데모 전용입니다. 브라우저 코드에 X-API-Key가 하드코딩되어 있으므로 외부에 노출하지 마세요.</p>
<button id="refresh">새로고침</button>
<label style="margin-left:12px; font-size:13px;">
  <input type="checkbox" id="auto"> 10초마다 자동 새로고침
</label>

<div class="grid">
  <div class="card"><h2>오늘 매출</h2><div class="value" id="sales-today">-</div></div>
  <div class="card"><h2>이번 주 매출</h2><div class="value" id="sales-week">-</div></div>
  <div class="card"><h2>정산 요약 (오늘)</h2>
    <table>
      <tr><td>총매출</td><td id="settle-gross">-</td></tr>
      <tr><td>결제건수</td><td id="settle-count">-</td></tr>
      <tr><td>환불액</td><td id="settle-refund">-</td></tr>
      <tr><td>환불건수</td><td id="settle-refund-count">-</td></tr>
      <tr><td>부분환불액</td><td id="settle-partial-refund">-</td></tr>
      <tr><td>부분환불건수</td><td id="settle-partial-refund-count">-</td></tr>
    </table>
  </div>
  <div class="card"><h2>원가/마진 (오늘)</h2>
    <table>
      <tr><td>총매출</td><td id="margin-revenue">-</td></tr>
      <tr><td>총원가</td><td id="margin-cost">-</td></tr>
      <tr><td>매출총이익</td><td id="margin-gross">-</td></tr>
      <tr><td>마진율</td><td id="margin-rate">-</td></tr>
    </table>
  </div>
</div>

<div class="grid">
  <div class="card"><h2>매출 추이 (최근 7일)</h2><canvas id="chart-daily"></canvas></div>
  <div class="card"><h2>인기 메뉴 TOP5 (오늘)</h2><canvas id="chart-top"></canvas></div>
</div>

<div class="grid">
  <div class="card"><h2>재고 현황</h2><canvas id="chart-inventory"></canvas></div>
  <div class="card"><h2>오늘 예약</h2>
    <table id="table-reservations">
      <thead><tr><th>시간</th><th>고객</th><th>서비스</th></tr></thead>
      <tbody></tbody>
    </table>
  </div>
</div>

<div class="grid">
  <div class="card"><h2>재방문 고객 TOP (전체 기간, 2건 이상)</h2>
    <table id="table-repeat-customers">
      <thead><tr><th>고객</th><th>주문건수</th><th>누적 결제액</th></tr></thead>
      <tbody></tbody>
    </table>
  </div>
</div>

<script>
const BASE = "";
const KEY = "dev-key";           // 로컬 데모 전용 하드코딩 — docs/12 참고
const STORE = "store_demo";
const headers = { "X-API-Key": KEY };

async function getJSON(path) {
  const res = await fetch(BASE + path, { headers });
  if (!res.ok) return null;
  return res.json();
}

let dailyChart, topChart, inventoryChart;

function upsertChart(existing, ctx, config) {
  if (existing) { existing.destroy(); }
  return new Chart(ctx, config);
}

async function loadDashboard() {
  const salesToday = await getJSON(`/v1/stores/${STORE}/reports/sales?period=today`);
  const salesWeek = await getJSON(`/v1/stores/${STORE}/reports/sales?period=week`);
  const settlement = await getJSON(`/v1/stores/${STORE}/reports/settlement?period=today`);
  const margin = await getJSON(`/v1/stores/${STORE}/reports/margin?period=today`);
  const daily = await getJSON(`/v1/stores/${STORE}/reports/sales/daily?days=7`);
  const topItems = await getJSON(`/v1/stores/${STORE}/reports/top-items?period=today&limit=5`);
  const inventory = await getJSON(`/v1/stores/${STORE}/inventory`);
  const today = new Date().toISOString().slice(0, 10);
  const reservations = await getJSON(`/v1/stores/${STORE}/reservations?date=${today}&status=BOOKED`);
  const repeatCustomers = await getJSON(`/v1/stores/${STORE}/reports/repeat-customers?period=all&min_orders=2`);

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
        labels: daily.map(d => d.date.slice(5)),
        datasets: [{ label: "매출", data: daily.map(d => d.total_sales), borderColor: "#2563eb", tension: 0.2 }],
      },
      options: { plugins: { legend: { display: false } } },
    });
  }

  if (topItems) {
    topChart = upsertChart(topChart, document.getElementById("chart-top"), {
      type: "bar",
      data: {
        labels: topItems.map(i => i.name),
        datasets: [{ label: "매출", data: topItems.map(i => i.revenue), backgroundColor: "#16a34a" }],
      },
      options: { indexAxis: "y", plugins: { legend: { display: false } } },
    });
  }

  if (inventory) {
    inventoryChart = upsertChart(inventoryChart, document.getElementById("chart-inventory"), {
      type: "bar",
      data: {
        labels: inventory.map(i => i.item_id),
        datasets: [{
          label: "재고",
          data: inventory.map(i => i.stock_quantity),
          backgroundColor: inventory.map(i =>
            i.stock_quantity <= (i.low_stock_threshold ?? 5) ? "#dc2626" : "#94a3b8"
          ),
        }],
      },
      options: { plugins: { legend: { display: false } } },
    });
  }

  const tbody = document.querySelector("#table-reservations tbody");
  tbody.innerHTML = "";
  (reservations || []).forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${new Date(r.datetime).toLocaleTimeString("ko-KR", {hour: "2-digit", minute: "2-digit"})}</td><td>${r.customer_id}</td><td>${r.service ?? "-"}</td>`;
    tbody.appendChild(tr);
  });

  const repeatTbody = document.querySelector("#table-repeat-customers tbody");
  repeatTbody.innerHTML = "";
  (repeatCustomers || []).forEach(c => {
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
</script>
</body>
</html>
"""


@router.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    return HTMLResponse(content=_PAGE)
