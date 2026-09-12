title: 아메리카노 원두(또는 완성 음료) 재입고 요청 — 50개
assignee: inventory-agent
status: todo
created: 2026-09-11
requester: 사장님
details:
  - 품목: 아메리카노 50개 분량(원두 기준 또는 즉시 제공 가능한 완성 음료 재고 표기)
  - 수량 요청: 50
  - 사유: 원두 완전 품절로 판매 불가, 긴급 대량 재입고 필요
  - 긴급도: 높음(영업 영향 즉시)
  - 요구사항:
      1) 공급사별(최소 2곳) 견적(단가, 최소주문수량, 배송비 포함 총액)
      2) 리드타임(발주→입고 예정일) 및 재고 확보 가능 여부(50개 확보 가능 여부)
      3) 대체안(당장 영업 가능한 임시 대체품/임대/이웃 매장 협조 등) 권고
      4) 추천 발주수량(안전재고 고려) 및 비용 차이 설명
      5) 발주(결제) 절차 요약 — 절대 사장님 명시 승인 없이는 발주 진행하지 말 것(HITL 게이트)
  - 우선응답기한: 2시간 내 회신 요청
verification:
  - verification_file: workspace/kanban/2026-09-11-restock-americano-50.md
  - verification_steps: "inventory-agent가 견적·리드타임을 card에 업데이트하고, 실제 주문을 진행하기 전 사장님 승인(명시적 yes)이 필요함"
notes:
  - coordinator: 카드를 생성하고 inventory-agent에 위임함. 발주 확정(결제)은 사장님 허가 전 진행하지 않음.
