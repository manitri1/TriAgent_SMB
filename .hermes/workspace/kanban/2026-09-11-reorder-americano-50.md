title: 재입고 요청 — 아메리카노 50개
assignee: inventory-agent
status: todo
created: 2026-09-11
priority: urgent
details:
  - item: 아메리카노
  - sku: americano
  - qty_requested: 50
  - reason: 원두 완전 품절 — 긴급 대량 재입고 필요
  - requested_by: 사장님 (전화)
  - action: inventory-agent가 PO 초안(견적 포함)을 작성하고, 예상 총액/단가/공급사/리드타임을 제시하세요. 실제 발주는 절대 사용자(사장님)의 명시적 승인(HITL) 후에만 진행합니다.
verification:
  - verification_file: workspace/purchase_orders/2026-09-11-po-americano-50.md (inventory-agent가 PO 초안을 이 경로로 생성하면 coordinator가 열어 확인합니다)
  - verification_steps:
    - PO 초안 파일 존재 확인
    - 포함 항목: 공급사 1개 이상, 단가, 수량, 총액, ETA, 결제조건
    - coordinator가 사용자의 승인 요청 메시지를 받은 뒤 발주 진행 여부 결정
notes:
  - 이 작업은 "재고 대량 발주 확정 전" HITL 게이트 대상입니다. 발주는 에이전트의 제안(초안) 확인 후 사장님의 명시적 승인이 있어야 진행됩니다.
