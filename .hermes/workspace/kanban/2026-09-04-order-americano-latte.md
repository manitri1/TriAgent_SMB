title: 주문 — Americano 1잔, Latte 1잔
assignee: order-payment-agent
status: awaiting-payment-method
created: 2026-09-04
priority: high

details:
  - 고객 요청: "Americano 1잔, Latte 1잔. 결제까지 처리해 주세요."
  - 작업 지시:
    1. POS 재고 확인 및 음료 제조 가능 여부 확인
    2. POS에 주문 생성(테이크아웃/매장: 고객 지시 대기)
    3. 결제 수단으로 고객이 지정한 방법으로 결제 처리(아래 결제 옵션 중 선택)
    4. 결제 승인/영수증을 받은 뒤 고객에게 확인 메시지 전달
    5. 작업 완료 후 이 카드에 결과(결제 승인번호, 영수증 파일 경로)를 기재하고 status를 done으로 변경

notes:
  - 현재 결제 수단 미지정: 사용자 확인 필요
  - HITL(인간 승인) 필요 항목: 결제 환불/취소는 사용자가 별도 승인해야 함(이번 요청에는 해당되지 않음)

next_action: "사장님, 결제하실 방법을 알려주세요 — 등록된 카드로 즉시 결제 / 카드 직접 입력(결제 링크) / 현금(현장결제) 중 선택하세요. 선택해 주시면 order-payment-agent에 결제 처리 지시하겠습니다."
