# 재입고 요청: 아메리카노 30개
사유: 재고 소진, 긴급 재입고 필요

첨부(API 응답/재고 스냅샷):
- workspace/kanban/2026-09-08-restock-americano-30_inventory.json
- workspace/kanban/2026-09-08-restock-americano-30_matched.json

요청자: 매장 재고 담당 에이전트
상태: pending

---

1) Mock POS 재고 확인 결과 (원본 API 응답 요약):

- 조회 엔드포인트: GET http://mock-pos:8080/v1/stores/store_demo/inventory
- 매칭 항목:
  - item_id: menu_americano
  - stock_quantity: 0
  - low_stock_threshold: 5
  - updated_at: 2026-09-08T09:23:34.153546Z

(자세한 전체 응답은 첨부된 JSON 파일을 확인하세요.)

2) 공급처 후보 (견적, 단가, ETA)

- 후보 A: CafeSupplyCo (지역 소규모 납품업체) — 단가 2,500원/개
  - 수량: 30개
  - 총액: 75,000원
  - 예상 납기(ETA): 당일 또는 익일(같은 날 픽업 가능)
  - 비고: 소규모 즉시 구매로 비용이 낮아 즉시 발주 가능하지만, 요청에 따라 사장님 승인 전까지 보류합니다.

- 후보 B: CoffeePack (도매 온라인 납품) — 단가 3,500원/개
  - 수량: 30개
  - 총액: 105,000원
  - 예상 납기(ETA): 1~2 영업일
  - 비고: 총액이 즉시진행 한도(150,000원)를 초과하지 않아 HITL 불필요.

(추가 공급처가 필요하면 지정해 주세요 — 업체별 거래조건(최소주문수량, 반품정책 등)을 추가로 확인해 견적 업데이트하겠습니다.)

3) 발주 정책/다음 단계

- 비용/납기 확인 완료. 총액이 USER.md 기준 즉시진행 한도(150,000원) 이내이므로 HITL(게이트2) 불필요.
- 사용자의 지시대로 실제 결제/발주는 사장님(박서준) 승인 전까지 보류합니다.
- 사장님 승인 시 아래 중 하나를 수행하겠습니다:
  1. 즉시 소규모 구매(CafeSupplyCo)로 발주 및 POS 재고 +30 반영(POST /adjust)
  2. 도매(예: CoffeePack)로 발주(발주서 초안 제공), 결제 후 POS 재고 반영

4) 로그 및 증거 파일

- API 원본 응답: workspace/kanban/2026-09-08-restock-americano-30_inventory.json
- 매칭 항목(아메리카노): workspace/kanban/2026-09-08-restock-americano-30_matched.json

요청: 사장님 승인 여부를 알려주세요. 승인 시 원하는 공급처(후보 A / 후보 B / 다른 업체)를 지정해 주세요.


(에이전트 서명)
inventory-agent
