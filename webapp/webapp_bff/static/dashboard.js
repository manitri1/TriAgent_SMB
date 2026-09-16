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

/**
 * 사장님이 오늘 확인해야 할 것 — 이미 화면에 흩어져 있는 지표(재고, 매출 추이,
 * 환불율, 마진율, 재방문 고객, 오늘 예약)를 규칙 기반으로 훑어서 "결정이 필요한
 * 것"만 카드로 뽑아낸다. 서버 쪽 새 계산 없이 기존 리포트 API 응답만으로 판단한다.
 */
function computeInsights({
  inventory, nameById, daily15, settlementWeek, marginToday, repeatCustomers, reservationsToday,
  topItemsWeek, reservationsAll,
}) {
  const insights = [...computeInventoryInsights({ inventory, nameById, topItemsWeek })];

  // 2) 매출 추이: 최근 완결된 7일 vs 그 이전 7일. 오늘은 아직 영업이 끝나지 않아
  // 항상 매출이 적게 잡히므로 비교에서 제외한다(days=15 중 마지막=오늘은 버림).
  if (daily15 && daily15.length === 15) {
    const complete = daily15.slice(0, 14); // 오늘 제외, 오래된 순
    const prevWeek = complete.slice(0, 7).reduce((sum, d) => sum + d.total_sales, 0);
    const recentWeek = complete.slice(7, 14).reduce((sum, d) => sum + d.total_sales, 0);
    if (prevWeek > 0) {
      const pct = ((recentWeek - prevWeek) / prevWeek) * 100;
      if (pct <= -15) {
        insights.push({
          level: "critical", icon: "🔴", title: `매출 급감 — 이전 주 대비 ${pct.toFixed(0)}%`,
          detail: `최근 7일 매출 ${recentWeek.toLocaleString()}원, 이전 7일 ${prevWeek.toLocaleString()}원. 원인 점검이 필요합니다.`,
          insightKey: "sales-trend-crash",
        });
      } else if (pct <= -5) {
        insights.push({
          level: "warning", icon: "🟠", title: `매출 하락세 — 이전 주 대비 ${pct.toFixed(0)}%`,
          detail: `최근 7일 매출 ${recentWeek.toLocaleString()}원, 이전 7일 ${prevWeek.toLocaleString()}원.`,
          insightKey: "sales-trend-down",
        });
      } else if (pct >= 15) {
        insights.push({
          level: "good", icon: "🟢", title: `매출 상승세 — 이전 주 대비 +${pct.toFixed(0)}%`,
          detail: `최근 7일 매출 ${recentWeek.toLocaleString()}원, 이전 7일 ${prevWeek.toLocaleString()}원.`,
          insightKey: "sales-trend-up",
        });
      }
    }
  }

  // 3) 환불율 (이번 주 기준 — 하루치보다 표본이 안정적).
  if (settlementWeek && settlementWeek.gross_sales > 0) {
    const refundTotal = settlementWeek.refunded_amount + settlementWeek.partial_refund_amount;
    const rate = refundTotal / settlementWeek.gross_sales;
    if (rate >= 0.10) {
      insights.push({
        level: "critical", icon: "🔴", title: `이번 주 환불율 ${(rate * 100).toFixed(1)}% — 원인 확인 필요`,
        detail: `환불 ${settlementWeek.refunded_count + settlementWeek.partial_refund_count}건, 환불액 ${refundTotal.toLocaleString()}원.`,
        insightKey: "refund-rate-critical",
      });
    } else if (rate >= 0.05) {
      insights.push({
        level: "warning", icon: "🟠", title: `이번 주 환불율 ${(rate * 100).toFixed(1)}% — 응대/품질 점검 권장`,
        detail: `환불 ${settlementWeek.refunded_count + settlementWeek.partial_refund_count}건, 환불액 ${refundTotal.toLocaleString()}원.`,
        insightKey: "refund-rate-warning",
      });
    }
  }

  // 4) 마진율 (오늘 결제가 있을 때만 — 표본이 없으면 판단 보류).
  if (marginToday && marginToday.total_revenue > 0 && marginToday.margin_rate < 0.55) {
    insights.push({
      level: "warning", icon: "🟠", title: `오늘 마진율 ${(marginToday.margin_rate * 100).toFixed(1)}% — 평소보다 낮음`,
      detail: `원가 비중이 높은 메뉴 위주로 팔린 날일 수 있습니다. 인기 메뉴 원가율을 확인해 보세요.`,
      insightKey: "margin-rate-low",
    });
  }

  // 5) 단골 이탈 위험: 3건 이상 주문했던 고객인데 최근 14일 이상 안 옴.
  if (repeatCustomers && repeatCustomers.length) {
    const now = Date.now();
    const churnRisk = repeatCustomers.filter((c) => {
      if (c.order_count < 3 || !c.last_order_at) return false;
      const daysSince = (now - new Date(c.last_order_at).getTime()) / 86400000;
      return daysSince >= 14;
    });
    if (churnRisk.length) {
      const names = churnRisk.slice(0, 5).map((c) => c.name ?? c.customer_id);
      insights.push({
        level: "info", icon: "🔵", title: `이탈 위험 단골 ${churnRisk.length}명 — 안부 메시지 검토`,
        detail: `${names.join(", ")}${churnRisk.length > 5 ? ` 외 ${churnRisk.length - 5}명` : ""} — 최근 14일 이상 재방문이 없습니다.`,
        actionLabel: "고객 문의 화면으로 이동", actionHref: "/support",
        insightKey: "churn-risk",
      });
    }
  }

  // 6) 오늘 예약: 결정 사항이라기보다 "확인" 알림 — 시간 순으로 안내.
  if (reservationsToday && reservationsToday.length) {
    const times = reservationsToday
      .slice()
      .sort((a, b) => new Date(a.datetime) - new Date(b.datetime))
      .map((r) => new Date(r.datetime).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }));
    insights.push({
      level: "info", icon: "🔵", title: `오늘 예약 ${reservationsToday.length}건`,
      detail: `${times.join(", ")} — 자리/인력 배치를 미리 확인하세요.`,
      actionLabel: "예약 관리로 이동", actionHref: "/reservations",
      insightKey: "today-reservations",
    });
  }

  // 7) 마진 기준 워스트 메뉴: 이번 주에 어느 정도(5개↑) 팔렸는데 평균보다 마진율이
  // 뚜렷이(15%p↑) 낮은 품목 — 매출 TOP만 봐서는 안 보이는 수익성 문제를 짚는다.
  if (topItemsWeek && topItemsWeek.length >= 3) {
    const withVolume = topItemsWeek.filter((i) => i.quantity >= 5 && i.revenue > 0);
    const totalRevenue = withVolume.reduce((sum, i) => sum + i.revenue, 0);
    const totalMargin = withVolume.reduce((sum, i) => sum + i.margin, 0);
    const avgRate = totalRevenue > 0 ? totalMargin / totalRevenue : 0;
    let worst = null;
    withVolume.forEach((i) => {
      const rate = i.margin / i.revenue;
      if (rate < avgRate - 0.15 && (!worst || rate < worst.rate)) worst = { ...i, rate };
    });
    if (worst) {
      insights.push({
        level: "info", icon: "🔵", title: `${worst.name} — 많이 팔리지만 마진율 낮음 (${(worst.rate * 100).toFixed(0)}%)`,
        detail: `이번 주 ${worst.quantity}개 판매, 전체 평균 마진율 ${(avgRate * 100).toFixed(0)}% 대비 낮습니다. 가격/원가 재검토를 고려해보세요.`,
        insightKey: "margin-laggard",
      });
    }
  }

  // 8) 노쇼/미확인 예약
  insights.push(...computeReservationNoShowInsights({ reservationsAll }));

  const order = { critical: 0, warning: 1, good: 2, info: 3 };
  insights.sort((a, b) => order[a.level] - order[b.level]);
  return insights;
}

/**
 * 마케팅·CRM 제안 — "확인해야 할 것" 인사이트와 달리 문제가 아니라 기회를
 * 짚는다(감사 인사, 재유치, 판매 저조 품목 홍보, 인기 메뉴 프로모션). 자동으로
 * 카드에 끼워넣지 않고, 버튼을 눌렀을 때만 팝업으로 보여준다 — 매번 볼 필요는
 * 없지만 원할 때 근거 데이터와 함께 골라 진행할 수 있게 한다. 승인해도
 * marketing-crm-agent는 문구 "초안"만 작성한다(발송 수단이 없음, SOUL.md 참고) —
 * approveMessage는 항상 coordinator로 보낸다(웹앱은 coordinator/customer-service-agent
 * 외 profile을 허용하지 않는다, agent.py 참고).
 */
function buildMarketingSuggestions({ repeatCustomers, topItemsWeek }) {
  const suggestions = [];

  if (repeatCustomers && repeatCustomers.length) {
    const vips = repeatCustomers.slice().sort((a, b) => b.total_spent - a.total_spent).slice(0, 5);
    if (vips.length) {
      const names = vips.map((c) => c.name ?? c.customer_id);
      suggestions.push({
        id: "vip-thanks", icon: "💜", title: `VIP 단골 ${vips.length}명 — 감사 혜택 문구 검토`,
        detail: `${names.join(", ")} — 누적 결제액 상위 고객입니다.`,
        approveMessage: `다음 VIP 고객에게 보낼 감사 혜택/쿠폰 홍보 문구 초안을 작성해주세요: ${names.join(", ")}.`,
      });
    }

    const now = Date.now();
    const churnRisk = repeatCustomers.filter((c) => {
      if (c.order_count < 3 || !c.last_order_at) return false;
      return (now - new Date(c.last_order_at).getTime()) / 86400000 >= 14;
    });
    if (churnRisk.length) {
      const names = churnRisk.slice(0, 5).map((c) => c.name ?? c.customer_id);
      suggestions.push({
        id: "churn-winback", icon: "🔵", title: `이탈 위험 단골 ${churnRisk.length}명 — 재유치 문구 검토`,
        detail: `${names.join(", ")}${churnRisk.length > 5 ? ` 외 ${churnRisk.length - 5}명` : ""} — 최근 14일 이상 재방문이 없습니다.`,
        approveMessage: `최근 14일 이상 재방문이 없는 단골 고객(${names.join(", ")})에게 보낼 재유치 메시지 초안을 작성해주세요.`,
      });
    }
  }

  if (topItemsWeek && topItemsWeek.length >= 3) {
    const withVolume = topItemsWeek.filter((i) => i.quantity > 0);
    if (withVolume.length >= 3) {
      const avgQty = withVolume.reduce((sum, i) => sum + i.quantity, 0) / withVolume.length;
      const worst = withVolume.slice().sort((a, b) => a.quantity - b.quantity)[0];
      if (worst.quantity <= avgQty * 0.5) {
        suggestions.push({
          id: "slow-item-promo", icon: "🟠", title: `${worst.name} — 이번 주 판매 저조, 홍보 검토`,
          detail: `이번 주 ${worst.quantity}개 판매(평균 ${avgQty.toFixed(1)}개). 홍보로 수요를 끌어올릴 수 있는지 검토해보세요.`,
          approveMessage: `${worst.name}의 판매를 늘리기 위한 홍보 문구 초안을 작성해주세요 (SNS/카카오톡 채널용).`,
        });
      }
      const best = withVolume.slice().sort((a, b) => b.quantity - a.quantity)[0];
      if (best.quantity > 0) {
        suggestions.push({
          id: "top-item-bundle", icon: "🟢", title: `${best.name} — 이번 주 1위, 세트 프로모션 검토`,
          detail: `이번 주 ${best.quantity}개 판매. 인기를 살린 세트/시즌 프로모션을 고려해보세요.`,
          approveMessage: `${best.name}를 활용한 세트/시즌 프로모션 홍보 문구 초안을 작성해주세요.`,
        });
      }
    }
  }

  return suggestions;
}

let latestMarketingData = { repeatCustomers: [], topItemsWeek: [] };
const marketingSentCache = new Map();
const marketingResultCache = new Map();

function renderMarketingModal() {
  const list = document.getElementById("marketing-suggestion-list");
  const empty = document.getElementById("marketing-suggestion-empty");
  if (!list) return;
  const suggestions = buildMarketingSuggestions(latestMarketingData);
  list.innerHTML = "";
  if (!suggestions.length) {
    if (empty) empty.hidden = false;
    return;
  }
  if (empty) empty.hidden = true;
  suggestions.forEach((s) => {
    const card = document.createElement("div");
    card.className = "insight-card";
    card.innerHTML = `
      <span class="insight-icon">${s.icon}</span>
      <div style="flex: 1; min-width: 0;">
        <div class="insight-title">${s.title}</div>
        <div class="insight-detail">${s.detail}</div>
        <div class="insight-actions">
          <button type="button" class="btn-primary btn-ghost--sm" data-suggestion-id="${s.id}">이 문구 초안 요청하기</button>
        </div>
        <div class="sent-prompt" id="marketing-sent-${s.id}"></div>
        <div class="compact-result" id="marketing-result-${s.id}"></div>
      </div>
    `;
    list.appendChild(card);
    if (marketingSentCache.has(s.id)) {
      renderSentPrompt(document.getElementById(`marketing-sent-${s.id}`), marketingSentCache.get(s.id));
    }
    if (marketingResultCache.has(s.id)) {
      renderCompactResult(document.getElementById(`marketing-result-${s.id}`), marketingResultCache.get(s.id), {
        onFollowup: (msg) => sendMarketingMessage(s.id, msg),
      });
    }
    card.querySelector("[data-suggestion-id]").addEventListener("click", () => sendMarketingMessage(s.id, s.approveMessage));
  });
}

async function sendMarketingMessage(suggestionId, message) {
  marketingSentCache.set(suggestionId, message);
  renderSentPrompt(document.getElementById(`marketing-sent-${suggestionId}`), message);
  renderCompactResult(document.getElementById(`marketing-result-${suggestionId}`), { status: "pending", text: "coordinator에게 전달하는 중…" });
  try {
    const res = await fetch("/api/agent/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profile: "coordinator",
        message,
        conversation_id: getConversationId(`conversation_id_marketing_${suggestionId}`),
      }),
    });
    const data = await res.json();
    const result = { status: data.status === "ok" ? "ok" : data.status, text: data.text };
    marketingResultCache.set(suggestionId, result);
    renderCompactResult(document.getElementById(`marketing-result-${suggestionId}`), result, {
      onFollowup: (msg) => sendMarketingMessage(suggestionId, msg),
    });
  } catch (err) {
    const result = { status: "error", text: "네트워크 오류가 발생했습니다. 다시 시도해 주세요." };
    marketingResultCache.set(suggestionId, result);
    renderCompactResult(document.getElementById(`marketing-result-${suggestionId}`), result);
  }
}

/** 카드 나열 대신 한눈에 읽는 한 줄 요약 — 오늘 매출 상태 + 확인 필요 건수. */
function buildBriefingLine(insights, salesToday) {
  const critical = insights.filter((i) => i.level === "critical").length;
  const warning = insights.filter((i) => i.level === "warning").length;
  const info = insights.filter((i) => i.level === "info").length;
  const good = insights.filter((i) => i.level === "good").length;

  const salesPart = salesToday && salesToday.total_sales > 0
    ? `오늘 매출 ${salesToday.total_sales.toLocaleString()}원(결제 ${salesToday.order_count}건)`
    : "오늘 매출이 아직 집계되지 않았습니다";

  let decisionPart;
  if (critical > 0) {
    decisionPart = `긴급 확인 ${critical}건${warning > 0 ? `, 주의 ${warning}건` : ""} 있습니다`;
  } else if (warning > 0) {
    decisionPart = `주의 확인 ${warning}건 있습니다`;
  } else if (good > 0) {
    decisionPart = "매출이 상승세입니다";
  } else if (info > 0) {
    decisionPart = `참고 알림 ${info}건 있습니다`;
  } else {
    decisionPart = "특별한 결정 사항 없이 순조롭습니다";
  }

  return `${salesPart}. ${decisionPart}.`;
}

const insightBoard = createInsightBoard("insight-list", "insight-empty", { onAfterSend: loadDashboard });

async function loadDashboard() {
  const catalog = await getJSON("/api/pos/catalog/items");
  const nameById = Object.fromEntries((catalog || []).map((i) => [i.item_id, i.name]));

  const salesToday = await getJSON("/api/pos/reports/sales?period=today");
  const salesWeek = await getJSON("/api/pos/reports/sales?period=week");
  const settlement = await getJSON("/api/pos/reports/settlement?period=today");
  const margin = await getJSON("/api/pos/reports/margin?period=today");
  const daily = await getJSON("/api/pos/reports/sales/daily?days=7");
  const daily15 = await getJSON("/api/pos/reports/sales/daily?days=15");
  const settlementWeek = await getJSON("/api/pos/reports/settlement?period=week");
  const topItems = await getJSON("/api/pos/reports/top-items?period=today&limit=5");
  const topItemsWeek = await getJSON("/api/pos/reports/top-items?period=week&limit=50");
  const inventory = await getJSON("/api/pos/inventory");
  const today = new Date().toISOString().slice(0, 10);
  const reservations = await getJSON(`/api/pos/reservations?date=${today}&status=BOOKED`);
  const reservationsAll = await getJSON("/api/pos/reservations?status=BOOKED");
  const repeatCustomers = await getJSON("/api/pos/reports/repeat-customers?period=all&min_orders=2");

  const insights = computeInsights({
    inventory: inventory || [],
    nameById,
    daily15: daily15 || [],
    settlementWeek,
    marginToday: margin,
    repeatCustomers: repeatCustomers || [],
    reservationsToday: reservations || [],
    topItemsWeek: topItemsWeek || [],
    reservationsAll: reservationsAll || [],
  });
  insightBoard.render(insights);
  const briefing = document.getElementById("briefing-line");
  if (briefing) briefing.textContent = buildBriefingLine(insights, salesToday);

  latestMarketingData = { repeatCustomers: repeatCustomers || [], topItemsWeek: topItemsWeek || [] };
  const marketingModalEl = document.getElementById("marketing-modal");
  if (marketingModalEl && marketingModalEl.open) renderMarketingModal();

  if (salesToday) {
    document.getElementById("sales-today").textContent = salesToday.total_sales.toLocaleString() + "원";
    document.getElementById("sales-today-count").textContent = `결제 ${salesToday.order_count}건`;
  }
  if (salesWeek) {
    document.getElementById("sales-week").textContent = salesWeek.total_sales.toLocaleString() + "원";
    document.getElementById("sales-week-count").textContent = `결제 ${salesWeek.order_count}건`;
  }
  const freshness = document.getElementById("dash-freshness");
  if (freshness) freshness.textContent = "마지막 업데이트 · 방금 전";
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
        datasets: [{ label: "매출", data: daily.map((d) => d.total_sales), borderColor: "#5b3df0", backgroundColor: "rgba(91,61,240,0.12)", fill: true, tension: 0.25 }],
      },
      options: { plugins: { legend: { display: false } } },
    });
  }

  if (topItems) {
    topChart = upsertChart(topChart, document.getElementById("chart-top"), {
      type: "bar",
      data: {
        labels: topItems.map((i) => i.name),
        datasets: [{ label: "매출", data: topItems.map((i) => i.revenue), backgroundColor: "#5b3df0" }],
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
            i.stock_quantity <= (i.low_stock_threshold ?? 5) ? "#d1373b" : "#b3aee0"
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

const marketingModal = document.getElementById("marketing-modal");
document.getElementById("marketing-suggest-btn").addEventListener("click", () => {
  renderMarketingModal();
  marketingModal.showModal();
});
document.getElementById("marketing-modal-close").addEventListener("click", () => marketingModal.close());
marketingModal.addEventListener("click", (e) => {
  if (e.target === marketingModal) marketingModal.close(); // 배경(backdrop) 클릭 시 닫기
});

/**
 * 목업 데이터 초기 세팅 — 시연·리허설 전 mock-pos를 리셋하고 다시 채운다
 * (webapp_bff/routers/admin.py 경유, coordinator를 거치지 않는다 — 업무
 * 결정이 아니라 환경 초기화이기 때문). 두 모드 다 파괴적 동작이라 실행 전
 * confirm으로 한 번 더 확인한다.
 */
const seedModal = document.getElementById("seed-modal");
document.getElementById("seed-data-btn").addEventListener("click", () => {
  document.getElementById("seed-sent").innerHTML = "";
  document.getElementById("seed-result").innerHTML = "";
  seedModal.showModal();
});
document.getElementById("seed-modal-close").addEventListener("click", () => seedModal.close());
seedModal.addEventListener("click", (e) => {
  if (e.target === seedModal) seedModal.close(); // 배경(backdrop) 클릭 시 닫기
});

const SEED_MODE_LABELS = { quick: "빠르게 채우기(오늘 스냅샷)", month: "한 달 시뮬레이션" };

async function runSeed(mode) {
  const label = SEED_MODE_LABELS[mode] || mode;
  if (!window.confirm(`${label}로 목업 데이터를 초기화할까요? 지금 있는 모든 주문·재고·고객 데이터가 사라집니다.`)) return;

  const sentEl = document.getElementById("seed-sent");
  const resultEl = document.getElementById("seed-result");
  renderSentPrompt(sentEl, `${label} 요청`);
  renderCompactResult(resultEl, {
    status: "pending",
    text: mode === "month" ? "5주치 데이터를 시뮬레이션하는 중… (잠시 걸릴 수 있습니다)" : "mock-pos 데이터를 새로 채우는 중…",
  });

  const optionButtons = document.querySelectorAll(".seed-option");
  optionButtons.forEach((btn) => (btn.disabled = true));
  try {
    const res = await fetch("/api/admin/seed-mock-data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "요청이 실패했습니다.");
    const days = data.days_simulated > 1 ? ` (최근 ${data.days_simulated}일치)` : "";
    renderCompactResult(resultEl, {
      status: "ok",
      text: `완료 — 메뉴 ${data.catalog_items}종, 고객 ${data.customers}명, 주문 ${data.orders}건, 결제 ${data.payments}건${days}. 대시보드를 새로고침했습니다.`,
    });
    loadDashboard();
  } catch (err) {
    renderCompactResult(resultEl, { status: "error", text: `초기화에 실패했습니다: ${err.message}` });
  } finally {
    optionButtons.forEach((btn) => (btn.disabled = false));
  }
}

document.querySelectorAll(".seed-option").forEach((btn) => {
  btn.addEventListener("click", () => runSeed(btn.dataset.mode));
});

let autoTimer = null;
document.getElementById("auto").addEventListener("change", (e) => {
  if (e.target.checked) {
    autoTimer = setInterval(loadDashboard, 10000);
  } else if (autoTimer) {
    clearInterval(autoTimer);
  }
});

loadDashboard();
