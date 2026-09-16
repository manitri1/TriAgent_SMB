title: 라떼 2잔, 아메리카노 1잔 주문 및 결제 처리
assignee: order-payment-agent
status: blocked
created: 2026-09-15
details:
  - 주문: 라떼 2잔, 아메리카노 1잔
  - 요청: 주문 생성 및 결제 처리
  - HITL: 환불/주문 취소가 아니므로 승인 게이트 없음
verification:
  - order_id: order_ae6bf99d006a
  - direct_check: GET http://mock-pos:8080/v1/stores/store_demo/orders/order_ae6bf99d006a
  - confirmed_order_status: OPEN
  - confirmed_total_amount: 12500 KRW
  - confirmed_items: menu_latte x2, menu_americano x1
  - payment_status: FAILED
  - payment_error: HTTP 409 Insufficient stock for item menu_americano
  - order_log: workspace/orders/2026-09-15.md
blocker:
  - 아메리카노 재고 부족으로 결제 완료 불가
  - 기존 재입고 카드 workspace/kanban/2026-09-15-restock-americano-50.md 승인 대기 중
