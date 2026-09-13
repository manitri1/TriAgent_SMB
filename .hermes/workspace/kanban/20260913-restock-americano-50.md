title: 아메리카노 50개 재입고 검토
assignee: inventory-agent
status: done
created: 2026-09-13
details:
  - 품목: 아메리카노 (menu_americano)
  - 요청 수량: 50개
  - 사유: 원두 완전 품절, 긴급 대량 재입고 필요 (사장님 요청)
  - 수행 내용: Mock POS 재고·안전재고·원가 조회, 50개 재입고 시 예상 발주금액 산출, USER 상한(150,000원) 대비 여부 판단
  - 주의: 실제 발주/입고 등록은 아직 수행하지 않고, 제안/견적만 정리
verification:
  - verification_file: /opt/data/workspace/inventory/proposals/2026-09-13-restock-americano-50.md
  - menu_americano 현재 재고 0개, 안전재고 5개, 원가 800원/개 확인
  - 50개 재입고 예상 발주금액 40,000원 (= 50 × 800원), USER 상한 150,000원 이내 확인 (게이트2 금액 기준 초과 아님)
