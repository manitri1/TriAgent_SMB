title: 아메리카노 재고 위험 품목 재입고 판단 및 진행
assignee: inventory-agent
status: done
created: 2026-09-14
details:
  - 재고 위험 품목인 아메리카노의 현재 재고와 최근 판매 데이터를 확인한다.
  - 적정 재입고 수량을 산정한다.
  - 재입고 수량이 대량 발주에 해당하면 확정 전 coordinator에게 HITL 승인 필요로 보고한다.
  - 대량 발주가 아니라면 재입고 처리를 진행하고 결과 근거를 남긴다.
verification:
  - completed: Mock POS 재고 조회, 최근 7일 주문/취소 데이터 산정, HITL 기준 확인 후 delta=15 입고 처리 완료
  - before_stock: 0
  - after_stock: 15
  - result_file: workspace/inventory/2026-09-14-americano-restock-result.json
