title: 오늘 아침 브리핑
assignee: sales-analytics-agent
status: done
created: 2026-09-13
details:
  - 사장님께 오늘 아침 기준 매출/주문/재고 상황을 간단히 보고한다.
  - sales-analytics-agent가 매출/주문/환불/인기메뉴를 정리했다.
  - inventory-agent가 저재고/품절 위험 품목을 정리했다.
verification:
  - verification_file: /opt/data/workspace/sales/2026-09-13.md
  - verification_summary: 오늘 매출 0원, 주문 0건, 환불/부분환불 0건 0원, Top 3 메뉴 없음
  - verification_file: /opt/data/workspace/inventory/2026-09-13.md
  - verification_summary: 재고 경고 품목 없음, menu_americano 품절(재고 0, 임계치 5) — 발주 검토 필요
