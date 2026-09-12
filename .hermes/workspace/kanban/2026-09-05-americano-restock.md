title: Restock: 아메리카노 x30
assignee: inventory-agent
status: in-progress
priority: urgent
created: 2026-09-05
details:
  - item: 아메리카노
  - quantity: 30
  - reason: 재고 소진, 긴급 재입고 필요
  - requested_by: 점주
  - actions: |
      inventory-agent: 공급사 확인, 단가·총액 견적, 예상 납기 제시, 드래프트 발주서(PO) 초안 작성 및 본 카드 업데이트.
      절대 주문 실행 금지 — 점주 승인(HITL) 후 발주 진행.
      카드 상태를 "in-progress"로 바꾼 뒤 진행 상황을 간결히 보고하십시오.

notes: "요청 수신: 즉시 확인 및 견적 요청(긴급)"

progress_log:
  - 2026-09-05T07:21:36+00:00 inventory-agent: 요청 접수 및 초기 처리 시작. Mock POS 라이브 조회 실패 — 가장 최근 스냅샷(/opt/data/workspace/inventory/2026-09-04-pos-snapshot-americano.json)을 사용하여 현 재고를 확인함.
  - 2026-09-05T07:30:00+00:00 inventory-agent: 공급사 2곳(빠른납기 옵션 1곳, 비용절감 옵션 1곳)에 견적 요청서(템플릿) 준비 완료 — 실제 발송을 위해 연락처 필요. 회신 받는 즉시 po_draft 업데이트 및 사장님 승인 요청 준비 예정.

inventory_snapshot:
  - path: /opt/data/workspace/inventory/2026-09-04-pos-snapshot-americano.json
  - item_id: menu_americano
  - stock_quantity: 0
  - snapshot_timestamp: 2026-09-04T04:39:18.643448Z

po_draft:
  title: PO Draft: 아메리카노 재입고 (초안)
  date: 2026-09-05
  prepared_by: inventory-agent
  status: draft  # 발주 실행 금지 — HITL 승인 필요
  item:
    - item_id: menu_americano
      description: 아메리카노
      requested_qty: 30

  suppliers_to_check:  # 실제 견적 수신 후 각 항목을 채워주세요. 네트워크/조회 도구 문제로 실시간 견적을 확보하지 못했습니다.
    - name: "지역 도매 유통사 (빠른납기 옵션)"
      contact: "(전화번호 또는 이메일 필요 — 사용자 제공)"
      quote_status: prepared  # prepared / requested / received
      quote_requested_at: null
      unit_price_ex_vat: "TBD"
      vat_rate: "TBD"
      shipping_fee: "TBD"
      moq: "TBD"
      lead_time_days_min: "TBD"
      lead_time_days_max: "TBD"
      estimated_delivery_date: "TBD"
      subtotal_ex_vat: "TBD"
      total_cost_including_tax_and_shipping: "TBD"
      quote_request_message: |
        안녕하세요. 마니카페 연남점 재고 담당자입니다.
        아메리카노(원두/베이스 포함) 재입고 관련 긴급 견적을 요청드립니다.
        요청 항목(회신 항목):
        1) 단가(unit price, VAT 제외)
        2) VAT율
        3) 수량: 30
        4) 소계(단가*수량, VAT 제외)
        5) 배송비
        6) MOQ(최소주문수량)
        7) 리드타임(영업일, 최소/최대)
        8) 예상 배송일(납품 가능일)
        9) 총지불액(세금·배송 포함)
        긴급 발주 고려 중이며, 회신 주시면 즉시 사장님 승인 요청(초안 포함)을 준비하겠습니다. 감사합니다.

    - name: "마니로스터리 (로스터 직거래 — 비용절감 옵션)"
      contact: "(전화번호 또는 이메일 필요 — 사용자 제공)"
      quote_status: prepared
      quote_requested_at: null
      unit_price_ex_vat: "TBD"
      vat_rate: "TBD"
      shipping_fee: "TBD"
      moq: "TBD"
      lead_time_days_min: "TBD"
      lead_time_days_max: "TBD"
      estimated_delivery_date: "TBD"
      subtotal_ex_vat: "TBD"
      total_cost_including_tax_and_shipping: "TBD"
      quote_request_message: |
        안녕하세요, 마니로스터리 담당자님. 마니카페 연남점입니다.
        아메리카노(원두/베이스 포함) 긴급 재입고 관련 견적 요청드립니다.
        요청 항목(회신 항목):
        - 단가(unit price, VAT 제외)
        - VAT율
        - 수량: 30
        - 소계(단가*수량, VAT 제외)
        - 배송비
        - MOQ
        - 리드타임(영업일, 최소/최대)
        - 예상 배송일
        - 총지불액(세금·배송 포함)
        회신 주시면 본 카드와 PO 초안을 바로 업데이트하여 사장님 승인 요청을 준비하겠습니다. 감사합니다.

  cost_breakdown_template:
    - unit_price_ex_vat: "단가(VAT 제외) * requested_qty"
    - subtotal_ex_vat: "단가 * 수량"
    - vat: "VAT율 적용(예: 10%)"
    - shipping_fee: "배송비(유무 및 금액)"
    - total_payable: "subtotal_ex_vat + vat + shipping_fee"

  notes:
    - "실제 단가·총액·납기·배송비는 공급사 회신(전화/이메일) 확인 후 업데이트합니다."
    - "USER.md의 즉시진행 한도(150,000원)를 초과하면 coordinator에게 HITL(게이트 2) 승인 요청을 합니다."

next_steps:
  - inventory-agent: 공급사 2곳에 준비된 견적 요청서(위 템플릿)를 발송할 연락처(전화번호 또는 이메일)를 제공해 주시거나, 제가 외부로 발신할 권한이 없으므로 사용자가 직접 발송해 주세요.
  - 회신 즉시 본 카드와 po_draft를 업데이트하여 사장님 승인 요청(사장님에게 보낼 승인 요청 메시지 초안 포함)을 준비합니다.
  - 주의: 절대 주문을 실행하지 마십시오 — 발주는 점주 승인(HITL) 후 진행.

concise_card_summary: "아메리카노 30잔 긴급 재입고 — 공급사 2곳에 견적 요청서(템플릿) 준비 완료. 연락처를 주시면 즉시 발송 또는 발송 지원합니다. 회신 즉시 PO 업데이트 및 사장님 승인 요청 준비합니다."
