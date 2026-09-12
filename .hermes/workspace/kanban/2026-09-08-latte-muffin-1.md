title: 라떼 1잔 + 블루베리 머핀 1개 주문 결제
assignee: order-payment-agent
status: in_progress
created_at: 2026-09-08T00:00:00Z
details: |
  고객 요청: 라떼(Latte) 1잔, 블루베리 머핀 1개 결제까지 처리
  요구사항:
  - POS 카탈로그에서 해당 품목의 item_id와 단가(unit_price) 조회
  - 수량에 따른 총액 계산
  - 카드 결제로 결제 시도(등록된 카드 사용 우선). 고객 식별자(customer_id)가 필요한 경우 요청
  - 결제 성공 시 POS 주문 ID, 결제 트랜잭션 ID, 결제 상태(success/failed), 영수증 URL(가능하면) 확보
  - 작업 완료 후 이 파일의 status를 done/failed로 업데이트하고 details에 POS 응답 포함
notes: "Coordinator: agent 보고 후 coordinator가 POS에서 직접 주문/결제 내역을 조회해 최종 검증합니다. 결제 처리 전 사용자 확인(총액/고객ID) 필요하면 즉시 문의하세요."
