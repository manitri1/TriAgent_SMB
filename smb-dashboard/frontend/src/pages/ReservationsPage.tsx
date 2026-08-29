import { useEffect, useState } from "react";

import { api, Reservation } from "../api";

function todayISODate(): string {
  return new Date().toISOString().slice(0, 10);
}

export function ReservationsPage() {
  const [date, setDate] = useState(todayISODate());
  const [reservations, setReservations] = useState<Reservation[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setReservations(null);
    api.reservations(date).then(setReservations).catch((e) => setError(e.message));
  }, [date]);

  return (
    <>
      <label>
        날짜: <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </label>
      {error && <p className="error">{error}</p>}
      {!reservations && !error && <p>불러오는 중...</p>}
      {reservations && reservations.length === 0 && <p>해당 날짜 예약이 없습니다.</p>}
      {reservations && reservations.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>고객</th>
              <th>일시</th>
              <th>서비스</th>
              <th>상태</th>
            </tr>
          </thead>
          <tbody>
            {reservations.map((r) => (
              <tr key={r.reservation_id}>
                <td>{r.customer_id}</td>
                <td>{new Date(r.datetime).toLocaleString("ko-KR")}</td>
                <td>{r.service ?? "-"}</td>
                <td>{r.status === "BOOKED" ? "예약됨" : "취소됨"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
