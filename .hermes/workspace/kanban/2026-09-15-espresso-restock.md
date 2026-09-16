title: 에스프레소 3일 내 품절 예상 재입고
assignee: inventory-agent
status: done
created: 2026-09-15
details:
  - 품목: 에스프레소
  - 현재 예측: 약 2.8일 내 품절 예상
  - 최근 판매 속도를 참고해 적정 재입고 수량 판단
  - 정상 범위의 재입고는 진행하되, 대량 발주에 해당하면 확정 전 coordinator에게 승인 요청
result:
  - 처리 완료: 예상 금액 80,500원으로 USER.md 대량 발주 승인 임계치 150,000원 이하
  - Mock POS 입고 조정: menu_espresso +115개
  - 검증 재고: 183개
verification:
  - workspace/inventory/2026-09-15.md
  - workspace/inventory/espresso-restock-2026-09-15-evidence.json
