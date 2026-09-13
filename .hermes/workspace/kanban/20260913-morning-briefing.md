title: 2026-09-13 아침 브리핑 정리
assignee: coordinator (sales-analytics-agent, inventory-agent)
status: done
created: 2026-09-13
details:
  - sales-analytics-agent로 오늘 현재까지 매출/주문/환불/마진 요약 조회
  - inventory-agent로 오늘 현재 기준 저재고·품절·발주 필요 품목 요약 조회
verification:
  - verification_file: /opt/data/workspace/sales/2026-09-13.md
  - verification_file: /opt/data/workspace/inventory/2026-09-13.md
  - Mock POS period=today 기준으로 두 에이전트가 직접 조회한 값을 사용해 브리핑 작성
