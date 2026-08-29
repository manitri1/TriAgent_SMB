import { useEffect, useState } from "react";

import { api, Order } from "../api";

const STATUS_LABEL: Record<Order["status"], string> = {
  OPEN: "주문 접수",
  COMPLETED: "결제 완료",
  CANCELED: "취소됨",
  REFUNDED: "환불됨",
};

export function OrdersPage() {
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.todayOrders().then(setOrders).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!orders) return <p>불러오는 중...</p>;
  if (orders.length === 0) return <p>오늘 주문이 아직 없습니다.</p>;

  return (
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
  );
}
