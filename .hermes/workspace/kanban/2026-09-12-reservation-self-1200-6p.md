title: 2026-09-12 12:00 단체석(6인) 고객 셀프 예약
assignee: reservation-agent
status: done
created: 2026-09-12
created_by: coordinator
details:
  - 예약자명: 셀프 예약 고객
  - 인원: 6명
  - 일시: 2026-09-12 12:00 (고객 셀프 예약, 이름으로 확인)
  - 좌석: 단체석(6인)
  - 채널: 셀프 예약 (매장 안내에 따라 고객 직접 입력)
verification: |
  - reservation_id: resv_3b112a8a6aa7
  - datetime: 2026-09-12T12:00:00Z
  - party_size: 6
  - name: '셀프 예약 고객'
  - api_create: POST /v1/stores/store_demo/reservations -> 201
  - api_get: GET /v1/stores/store_demo/reservations/resv_3b112a8a6aa7 -> 200
  - verification_file: workspace/reservations/2026-09-12-reservation-self-1200-6p.json
