// 브라우저가 최상위 문서 요청 시 basic-auth 다이얼로그에서 받은 자격증명을 같은 오리진의
// fetch 요청에도 자동으로 재사용하므로, 여기서 별도로 Authorization 헤더를 다루지 않는다
// (docs/13-mvp-dashboard-design.md §3.3 / smb-dashboard/backend/app/auth.py 참고).

async function request<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) {
    throw new Error(`${path} 요청 실패: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export interface OrderLineItem {
  item_id: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export interface Order {
  order_id: string;
  status: "OPEN" | "COMPLETED" | "CANCELED" | "REFUNDED";
  line_items: OrderLineItem[];
  total_amount: number;
  currency: string;
  created_at: string;
}

export interface InventoryItem {
  item_id: string;
  stock_quantity: number;
  low_stock: boolean;
  updated_at: string;
}

export interface Reservation {
  reservation_id: string;
  customer_id: string;
  datetime: string;
  service?: string;
  status: "BOOKED" | "CANCELED";
  note?: string;
}

export interface SalesSummary {
  period: string;
  order_count: number;
  total_sales: number;
  currency: string;
}

export type ApprovalType = "promo" | "reorder" | "refund";
export type ApprovalStatus = "pending" | "approved" | "rejected";

export interface Approval {
  approval_id: string;
  type: ApprovalType;
  summary: string;
  details: string;
  requested_by: string;
  status: ApprovalStatus;
  reason?: string;
  decided_by?: string;
  created_at: string;
  decided_at?: string;
}

export const api = {
  todayOrders: () => request<Order[]>("/api/orders/today"),
  inventory: () => request<InventoryItem[]>("/api/inventory"),
  reservations: (date?: string) =>
    request<Reservation[]>(`/api/reservations${date ? `?date=${date}` : ""}`),
  salesSummary: (period: string) => request<SalesSummary>(`/api/reports/sales?period=${period}`),
  pendingApprovals: () => request<Approval[]>("/api/approvals?status=pending"),
  decideApproval: async (id: string, status: "approved" | "rejected", reason?: string) => {
    const res = await fetch(`/api/approvals/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status, reason }),
    });
    if (!res.ok) {
      throw new Error(`승인 처리 실패: ${res.status}`);
    }
    return res.json() as Promise<Approval>;
  },
};
