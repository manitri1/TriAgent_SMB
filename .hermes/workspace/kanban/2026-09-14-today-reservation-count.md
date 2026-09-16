title: 오늘 예약 건수 확인
assignee: reservation-agent
status: done
created: 2026-09-14
details:
  - 2026-09-14 오늘 예약이 몇 건인지 확인한다.
result:
  - Mock POS GET /v1/stores/store_demo/reservations?date=2026-09-14 조회 결과 전체 1건, BOOKED 1건, CANCELED 0건.
  - 산출물: /opt/data/workspace/reservations/2026-09-14.md
verification:
  - done
