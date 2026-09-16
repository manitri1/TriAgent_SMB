title: 아메리카노 50개 긴급 재입고 요청
assignee: inventory-agent
status: blocked
created: 2026-09-15
details:
  - 품목: 아메리카노
  - 수량: 50개
  - 사유: 원두 완전 품절, 긴급 대량 재입고 필요
  - HITL: 대량 발주 확정 전 사장님 승인 필요
verification:
  - action_plan: workspace/inventory/americano-restock-2026-09-15-action-plan.md
  - evidence_file: workspace/inventory/americano-restock-2026-09-15-evidence.json
  - direct_check: GET http://mock-pos:8080/v1/stores/store_demo/inventory/menu_americano
  - confirmed_current_stock: 0
  - confirmed_low_stock_threshold: 5
  - side_effects: 실제 발주 확정 및 POS 재고 변경 미수행
blocker:
  - 사장님 명시 승인 대기: 아메리카노(menu_americano) 50개 긴급 재입고 및 승인 후 POS +50 반영
