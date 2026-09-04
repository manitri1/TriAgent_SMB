title: 라떼 1잔 + 블루베리 머핀 1개 주문 및 결제
assignee: order-payment-agent
status: requested
created: 2026-09-04
details: |
  고객 주문: 라떼 1잔, 블루베리 머핀 1개
  작업 요청:
    1) POS에서 메뉴명을 조회해 적절한 item_id를 사용하여 주문 생성
    2) 즉시 결제 처리(기본 수단: 카드)
    3) 주문 결과(order JSON)와 결제 영수증(payment receipt)을 각각
       workspace/orders/ 및 workspace/receipts/에 파일로 저장
    4) coordinator에게 주문ID, 결제상태, 저장된 파일 절대경로를 리턴
  비고: 고객 정보 없음(테이크아웃 가정). 결제 실패 시 실패 사유와 원인 로그를
       함께 보고해 주세요.
