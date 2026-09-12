title: 카푸치노 3잔 주문 — 결제 처리 요청
assignee: order-payment-agent
status: todo
created: 2026-09-05
details:
  - 고객 주문: 카푸치노 3잔
  - 결제/처리 작업 순서:
    1. POS에 주문 생성(상품 코드, 수량, 총액 입력)
    2. 결제 처리(고객 현장 카드 / 결제 링크 / 현금 등 선택된 방식으로)
    3. 결제 영수증(이미지/PDF) 또는 결제 승인 코드 저장
    4. 주문 및 결제 영수증을 workspace/orders/<timestamp>-order.json 및 workspace/orders/<timestamp>-receipt.* 에 저장
    5. coordinator에게 Active Verification용 산출물(주문 ID, 결제 승인 코드 또는 영수증 파일 경로)을 제출
verification:
  - required:
    * POS 주문 ID
    * 결제 승인 코드 또는 영수증(PDF/이미지)
    * 저장된 주문 JSON 경로
notes:
  - order-payment-agent가 결제를 실제로 실행하고 영수증/결제증빙을 workspace/orders/에 저장하면 coordinator가 직접 파일을 열어 확인한 뒤 카드 상태를 'done'으로 승인합니다.
  - 환불/취소 등 민감한 결제 변경은 HITL 게이트(사장님 승인)가 필요합니다.
