import { useEffect, useState } from "react";

import { api, SalesSummary } from "../api";

const PERIODS: { key: string; label: string }[] = [
  { key: "today", label: "오늘" },
  { key: "week", label: "이번 주" },
  { key: "month", label: "이번 달" },
];

export function SalesSummaryPage() {
  const [summaries, setSummaries] = useState<Record<string, SalesSummary>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all(PERIODS.map((p) => api.salesSummary(p.key)))
      .then((results) => {
        const map: Record<string, SalesSummary> = {};
        PERIODS.forEach((p, i) => (map[p.key] = results[i]));
        setSummaries(map);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="error">{error}</p>;

  return (
    <div className="summary-grid">
      {PERIODS.map((p) => {
        const s = summaries[p.key];
        return (
          <div className="summary-card" key={p.key}>
            <h3>{p.label}</h3>
            {s ? (
              <>
                <p className="summary-amount">{s.total_sales.toLocaleString()} {s.currency}</p>
                <p className="summary-count">{s.order_count}건</p>
              </>
            ) : (
              <p>불러오는 중...</p>
            )}
          </div>
        );
      })}
    </div>
  );
}
