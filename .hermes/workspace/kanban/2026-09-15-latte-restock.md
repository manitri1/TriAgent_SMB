title: 라떼 재고 위험 품목 재입고 판단 및 진행
assignee: inventory-agent
status: done
created: 2026-09-15
details:
  - 재고 위험 품목인 라떼의 적정 재입고 수량을 재고/판매 데이터를 참고해 판단한다.
  - 필요 시 재입고를 진행하되, 대량 발주 확정에 해당하면 사장님 승인 전 진행하지 않는다.
  - inventory-agent 처리 완료: 최근 판매/재고 기준 30개 재입고, 예상 원가 30,000원으로 게이트 2 대상 아님.
verification:
  - Mock POS `menu_latte` 재고 3개에서 33개로 입고 반영 확인(updated_at 2026-09-15T03:06:37.377082Z)
  - 기록: workspace/inventory/2026-09-15.md
  - 증빙: workspace/inventory/latte-restock-2026-09-15-evidence.json
