# 아메리카노 50개 긴급 재입고 조치안

- 관련 coordinator 카드: `workspace/kanban/2026-09-15-restock-americano-50.md`
- 요청: 아메리카노 50개 재입고
- 사유: 원두 완전 품절, 긴급 대량 재입고 필요
- 처리 시각: 2026-09-15T16:25:37+09:00
- 처리 원칙: 대량 발주/재고 반영 HITL 게이트가 있으므로 실제 발주 확정 및 POS 재고 수량 변경은 하지 않음.

## 현재 재고 및 품목 식별

경고: 아메리카노는 현재 Mock POS 재고가 0개입니다. 품목 임계치 5개 이하이므로 즉시 보수적 조치가 필요한 위험 상태입니다.

- 매장: `store_demo`
- Mock POS 조회: `GET /v1/stores/store_demo/inventory`, `GET /v1/stores/store_demo/inventory/menu_americano`
- 품목명: 아메리카노
- 품목 ID: `menu_americano`
- 현재 재고: 0개
- POS 저재고 임계치: 5개
- POS updated_at: 2026-09-15T07:20:37.515015Z

## 요청 수량 및 금액 참고

- 요청 재입고 수량: 50개
- 기존 카탈로그 스냅샷 참고: 아메리카노 판매가 3,500원, 원가 800원
- 참고 예상 원가: 40,000원 = 50개 × 800원
- 주의: `/inventory` 응답에는 단가/원가가 없으므로 위 금액은 기존 카탈로그 스냅샷 기반 참고값입니다. 실제 발주 확정 금액은 승인 게이트에서 공급처 단가 확인 후 확정해야 합니다.
- USER.md 즉시 진행 가능 금액 상한: 150,000원

## 필요한 조치안

1. 게이트 2에서 사장님/코디네이터 승인 여부 확인
   - 대상: 아메리카노 `menu_americano` 50개 긴급 재입고
   - 사유: 현재 재고 0개, 저재고 임계치 5개 이하
2. 승인 전에는 발주 확정 금지
3. 승인 전에는 Mock POS 재고 변경 금지
4. 승인 후 처리 절차
   - 공급처 단가 및 총액 확정
   - 승인 범위와 수량이 50개로 일치하는지 확인
   - `POST /v1/stores/store_demo/inventory/menu_americano/adjust` 에 `delta: +50`으로 입고 반영
   - 반영 후 `GET /v1/stores/store_demo/inventory/menu_americano` 재조회로 수량 및 `updated_at` 검증

## 수행하지 않은 작업

- 실제 발주 확정: 미수행
- Mock POS 재고 수량 변경: 미수행

## 검증 근거

- coordinator 카드 원문: `workspace/kanban/2026-09-15-restock-americano-50.md`
- 정책 원문: `/opt/data/profiles/inventory-agent/USER.md`
- Mock POS 조회 결과: `menu_americano` 재고 0개, 임계치 5개, updated_at 2026-09-15T07:20:37.515015Z
- 상세 증빙 JSON: `workspace/inventory/americano-restock-2026-09-15-evidence.json`
