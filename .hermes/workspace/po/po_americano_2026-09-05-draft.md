PO Draft: 아메리카노 재입고 (초안)
date: 2026-09-05
prepared_by: inventory-agent
status: draft  # 발주 실행 금지 — HITL(사장님) 승인 필요
associated_kanban: /opt/data/profiles/coordinator/workspace/kanban/2026-09-05-americano-restock.md
associated_inventory_log: /opt/data/workspace/inventory/2026-09-05.md

item:
  - item_id: menu_americano
    description: 아메리카노
    requested_qty: 30
    current_stock_snapshot: 0
    snapshot_path: /opt/data/workspace/inventory/2026-09-04-pos-snapshot-americano.json

suppliers_to_check:
  - name: "공급사 A (빠른 납기 우선)"
    contact: "(전화 또는 이메일 필요)"
    unit_price_ex_vat: "(견적 대기)"
    vat_rate: "(예: 10%)"
    shipping_fee: "(견적 대기)"
    moq: "(견적 대기)"
    lead_time_days: "(견적 대기)"
    estimated_delivery_date: "(견적 수신 후 계산)"
    total_cost_including_tax_and_shipping: "(견적 대기)"
  - name: "공급사 B (비용 절감 우선)"
    contact: "(전화 또는 이메일 필요)"
    unit_price_ex_vat: "(견적 대기)"
    vat_rate: "(예: 10%)"
    shipping_fee: "(견적 대기)"
    moq: "(견적 대기)"
    lead_time_days: "(견적 대기)"
    estimated_delivery_date: "(견적 수신 후 계산)"
    total_cost_including_tax_and_shipping: "(견적 대기)"

notes:
  - 발주/결제는 사장님 승인 후 실행합니다. 이 문서는 단지 초안이며, 실제 결제는 절대 실행하지 마십시오.
  - 즉시 발송 가능한 공급처 연락처를 제공해 주시거나, 제가 외부로 발신할 권한을 가지면 즉시 견적요청을 발송하겠습니다.
  - 총액 예상이 USER.md에 정의된 승인 임계치(예: 150,000원)를 초과하면 coordinator에게 HITL 게이트(게이트2) 요청 예정.

change_log:
  - 2026-09-05T07:30:00Z inventory-agent: PO 초안 작성(스냅샷 기준 재고 0). 실제 단가/총액은 공급사 견적 수신 후 입력.
