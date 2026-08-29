import { useEffect, useState } from "react";

import { api, Order, OrderStatusFilter } from "../api";

const STATUS_LABEL: Record<Order["status"], string> = {
  OPEN: "주문 접수",
  COMPLETED: "결제 완료",
  CANCELED: "취소됨",
  REFUNDED: "환불됨",
};

// REQ-016: docs/13 §4의 네 가지 명시적 상태 옵션 + "전체" 필터.
const FILTER_OPTIONS: { key: OrderStatusFilter; label: string }[] = [
  { key: "ALL", label: "전체" },
  { key: "OPEN", label: "주문 접수" },
  { key: "COMPLETED", label: "결제 완료" },
  { key: "CANCELED", label: "취소됨" },
  { key: "REFUNDED", label: "환불됨" },
];

export function OrdersPage() {
  const [filter, setFilter] = useState<OrderStatusFilter>("ALL");
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setOrders(null);
    setError(null);
    api
      .todayOrders(filter === "ALL" ? undefined : filter)
      .then(setOrders)
      .catch((e) => setError(e.message));
  }, [filter]);

  return (
    <div>
      <div className="filter-row" role="group" aria-label="주문 상태 필터">
        {FILTER_OPTIONS.map((opt) => (
          <button
            key={opt.key}
            className={opt.key === filter ? "tab tab-active tab-filter" : "tab tab-filter"}
            onClick={() => setFilter(opt.key)}
          >
            {opt.label}
          </button>
        ))}
      </div>
      {error && <p className="error">{error}</p>}
      {!error && !orders && <p>불러오는 중...</p>}
      {!error && orders && orders.length === 0 && (
        <p>
          {filter === "ALL"
            ? "오늘 주문이 아직 없습니다."
            : "이 필터와 일치하는 주문이 없습니다."}
        </p>
      )}
      {!error && orders && orders.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>주문 ID</th>
              <th>상태</th>
              <th>품목 수</th>
              <th>금액</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.order_id}>
                <td>{o.order_id}</td>
                <td>
                  <span className={`badge badge-${o.status.toLowerCase()}`}>{STATUS_LABEL[o.status]}</span>
                </td>
                <td>{o.line_items.length}</td>
                <td>{o.total_amount.toLocaleString()} {o.currency}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
