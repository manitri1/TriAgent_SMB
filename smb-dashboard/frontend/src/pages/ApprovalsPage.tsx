import { useEffect, useState } from "react";

import { api, Approval } from "../api";

const TYPE_LABEL: Record<Approval["type"], string> = {
  promo: "프로모션 집행",
  reorder: "대량 재입고",
  refund: "환불/취소",
};

export function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const reload = () => api.pendingApprovals().then(setApprovals).catch((e) => setError(e.message));

  useEffect(() => {
    reload();
  }, []);

  const decide = async (id: string, status: "approved" | "rejected") => {
    const reason = window.prompt(status === "approved" ? "승인 사유(선택)" : "반려 사유(선택)") ?? undefined;
    setBusyId(id);
    try {
      await api.decideApproval(id, status, reason);
      await reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusyId(null);
    }
  };

  if (error) return <p className="error">{error}</p>;
  if (!approvals) return <p>불러오는 중...</p>;
  if (approvals.length === 0) return <p>대기 중인 승인 요청이 없습니다.</p>;

  return (
    <div className="approval-list">
      {approvals.map((a) => (
        <div className="approval-card" key={a.approval_id}>
          <div className="approval-header">
            <span className="badge">{TYPE_LABEL[a.type]}</span>
            <span className="approval-requester">요청: {a.requested_by}</span>
          </div>
          <p className="approval-summary">{a.summary}</p>
          <p className="approval-details">{a.details}</p>
          <div className="approval-actions">
            <button
              disabled={busyId === a.approval_id}
              onClick={() => decide(a.approval_id, "approved")}
            >
              승인
            </button>
            <button
              disabled={busyId === a.approval_id}
              className="button-secondary"
              onClick={() => decide(a.approval_id, "rejected")}
            >
              반려
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
