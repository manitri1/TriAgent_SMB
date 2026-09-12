title: 라떼 1잔 + 블루베리 머핀 1개 주문 — 결제 처리 요청
assignee: order-payment-agent
status: todo
created: 2026-09-05
details:
  - 고객 주문: 라떼 1잔, 블루베리 머핀 1개
  - 결제 작업 순서:
    1. POS에 주문 생성(상품 코드, 수량, 금액 기입)
    2. 결제 수단 안내/확인(고객 현장 카드 / 결제 링크 / 현금)
    3. 결제 처리 실행 및 영수증(또는 결제 링크) 저장
    4. 결제 성공/실패 증빙을 workspace/orders/<timestamp>-order.json에 저장
    5. coordinator에게 Active Verification을 위한 산출물(주문 ID, 결제 영수증 경로 또는 결제 링크) 제출
  - 우선 검증 항목:
    * POS 주문 ID
    * 결제 영수증(이미지/PDF) 또는 결제 승인 코드
    * 저장된 주문 JSON 경로
notes:
  - order-payment-agent가 결제를 수행하고 결과 파일을 workspace/orders/에 저장하면 coordinator가 직접 열어 확인한 뒤 최종 완료 처리합니다.
  - 결제 환불/취소 관련 작업은 HITL(인간 승인) 항목이므로 별도 확인 없이 진행하지 마십시오.
