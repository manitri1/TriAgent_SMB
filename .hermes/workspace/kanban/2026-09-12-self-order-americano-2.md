title: 셀프 주문 - 아메리카노 2잔
assignee: order-payment-agent
status: blocked
created: 2026-09-12
details:
  - 고객: 셀프 주문 고객
  - 메뉴: 아메리카노 2잔
  - 요청: 고객 셀프 주문으로 접수하고 결제까지 처리
verification:
  - verification_file: /opt/data/workspace/orders/2026-09-12.md
  - 주문/결제 확인: 주문은 생성(order_id=order_bf4eb3633e91, 총액 7,000 KRW, 상태 OPEN)되었으나 결제는 재고 부족(409 Insufficient stock for item menu_americano)으로 실패하여 결제 ID 미생성
