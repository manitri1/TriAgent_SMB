import { useState } from "react";

import { ApprovalsPage } from "./pages/ApprovalsPage";
import { InventoryPage } from "./pages/InventoryPage";
import { OrdersPage } from "./pages/OrdersPage";
import { ReservationsPage } from "./pages/ReservationsPage";
import { SalesSummaryPage } from "./pages/SalesSummaryPage";

type Tab = "orders" | "inventory" | "reservations" | "sales" | "approvals";

const TABS: { key: Tab; label: string }[] = [
  { key: "orders", label: "주문 현황" },
  { key: "inventory", label: "재고 알림" },
  { key: "reservations", label: "예약 캘린더" },
  { key: "sales", label: "매출 요약" },
  { key: "approvals", label: "승인 대기열" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("orders");

  return (
    <div className="app">
      <header className="app-header">
        <h1>SMB 대시보드</h1>
      </header>
      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.key}
            className={t.key === tab ? "tab tab-active" : "tab"}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </nav>
      <main className="content">
        {tab === "orders" && <OrdersPage />}
        {tab === "inventory" && <InventoryPage />}
        {tab === "reservations" && <ReservationsPage />}
        {tab === "sales" && <SalesSummaryPage />}
        {tab === "approvals" && <ApprovalsPage />}
      </main>
    </div>
  );
}
