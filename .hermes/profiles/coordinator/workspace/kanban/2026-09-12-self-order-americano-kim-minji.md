title: 김민지 고객 셀프 주문 - 아메리카노 1잔 결제까지
assignee: order-payment-agent
status: blocked
created: 2026-09-12
details:
  - 고객: 김민지
  - 주문 유형: 고객 셀프 주문
  - 메뉴: 아메리카노 1잔
  - 결제 요청: 결제까지 완료
  - 현재 상태: 주문은 생성되었으나 재고 부족으로 결제 실패(결제 미진행)
verification:
  - verification_file: /opt/data/workspace/orders/2026-09-12.md
  - 확인 항목: order_id=order_ff92a8a4723f, 상태=OPEN, 결제 결과=409 Insufficient stock for item menu_americano (결제 실패, 청구 없음)
