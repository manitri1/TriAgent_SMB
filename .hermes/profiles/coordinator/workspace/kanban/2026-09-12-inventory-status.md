title: 오늘 재고 상황 확인
assignee: inventory-agent
status: done
created: 2026-09-12
details:
  - 사장님 요청: 오늘 현재 재고 상황을 요약해서 보고
  - 요구사항: 품목별 재고 수량, 저재고/품절 품목을 구분해서 정리
  - 처리 내용: inventory-agent가 Mock POS(store_demo) 재고 API를 조회해 /opt/data/workspace/inventory/2026-09-12.md에 기록
verification:
  - verification_file: /opt/data/workspace/inventory/2026-09-12.md
  - 품절: menu_americano 재고 0개 (임계치 5개 이하)
  - 정상 재고: 나머지 12개 품목은 모두 임계치 초과로 정상 상태
