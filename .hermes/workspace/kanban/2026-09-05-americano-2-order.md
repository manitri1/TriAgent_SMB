title: 아메리카노 2잔 주문 — 결제 처리 요청
assignee: order-payment-agent
status: todo
created: 2026-09-05
details:
  - 고객 주문: 아메리카노 2잔
  - 요청 작업:
    1. POS에 주문 생성
    2. 결제 처리(사용자 지불 수단 확인 필요)
    3. 결제 영수증 또는 결제 확인서(workspace/orders/<timestamp>-order.json) 저장
    4. 최종 상태를 coordinator에게 보고(완료 전 Active Verification 필요)
  - 수락 기준:
    * POS에 주문 ID와 결제 영수증(또는 결제 상태)이 workspace/orders/ 아래에 저장되어 coordinator가 파일을 직접 확인할 수 있을 것
    * 단순 텍스트 보고나 터미널 타임아웃만으로 'done' 표시는 하지 않음
notes:
  - 결제 수단 미지정: order-payment-agent가 결제 수단을 확인해야 함. 사장님, 결제 방법을 알려주세요(예: 카드 결제 링크 전송, 카드 온 파일, 현금).
