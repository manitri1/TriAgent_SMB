import { useEffect, useState } from "react";

import { api, InventoryItem } from "../api";

export function InventoryPage() {
  const [items, setItems] = useState<InventoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.inventory().then(setItems).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!items) return <p>불러오는 중...</p>;

  const lowStockCount = items.filter((i) => i.low_stock).length;

  return (
    <>
      {lowStockCount > 0 && (
        <p className="warning">저재고 품목 {lowStockCount}건 — 아래 표에서 강조 표시됩니다.</p>
      )}
      <table className="data-table">
        <thead>
          <tr>
            <th>품목 ID</th>
            <th>재고 수량</th>
          </tr>
        </thead>
        <tbody>
          {items.map((i) => (
            <tr key={i.item_id} className={i.low_stock ? "row-warning" : undefined}>
              <td>{i.item_id}</td>
              <td>{i.stock_quantity}{i.low_stock && " ⚠️"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
