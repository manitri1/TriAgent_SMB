title: 라떼 2잔, 아메리카노 1잔 주문 및 결제 처리
assignee: order-payment-agent
status: blocked
created: 2026-09-13
details:
  - 사장님 구두 요청: "라떼 2잔, 아메리카노 1잔 주문 들어왔고 결제까지 처리해줘"
  - 작업 범위: Mock POS에 주문 생성 후, 전액 결제 완료까지 처리
  - 품목: 라떼 2잔, 아메리카노 1잔 (메뉴 카탈로그 기준 매핑은 agent에서 결정)
  - 결제 수단: 기본값(예: 카드 결제) 사용 가능, 필요 시 내부 정책에 맞게 선택
  - 산출물: workspace/orders/2026-09-13-latte2-ame1.md
verification:
  - verification_file: workspace/orders/2026-09-13-latte2-ame1.md
  - 확인 항목: 주문 ID, 품목/수량(라떼2, 아메리카노1), 결제 상태 PAID 또는 이에 준하는 완료 상태
