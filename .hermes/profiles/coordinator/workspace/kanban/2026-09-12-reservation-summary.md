title: 오늘 예약 건수 확인
assignee: reservation-agent
status: done
created: 2026-09-12
details:
  - 사장님 요청: 오늘 예약이 몇 건인지 확인
  - 요구사항: 전체 예약 건수와 필요 시 시간대별 요약
  - 처리 내용: reservation-agent가 Mock POS(store_demo)에서 2026-09-12 예약 목록 조회 후 요약을 /opt/data/workspace/reservations/2026-09-12.md에 기록
verification:
  - verification_file: /opt/data/workspace/reservations/2026-09-12.md
  - total_booked: 2건 (status=BOOKED 기준)
  - slots_utc: 12:00 1건, 16:00 1건
