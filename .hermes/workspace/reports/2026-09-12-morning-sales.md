아침 브리핑용 매출/정산/마진 요약

작성 시각: 2026-09-12 06:05:39 UTC
작업 카드: /opt/data/workspace/kanban/2026-09-12-morning-briefing-sales.md
대상 매장: store_demo
통화: KRW

1. 오늘(today) 요약

- 매출: 0원
- 주문 수: 0건
- 정산 총매출: 0원
- 결제 건수: 0건
- 환불: 0원 / 0건
- 부분환불: 0원 / 0건
- 마진 매출 기준액: 0원
- 원가: 0원
- 매출총이익: 0원
- 마진율: 0.0%

판단: 오늘(today) 기준 조회값은 매출, 주문, 정산, 환불, 마진 모두 0입니다. 현재 조회 시점 기준으로 오늘 반영된 주문/결제 데이터가 없습니다.

2. 기간별 참고 지표

| 기간 | 매출(total_sales) | 주문 | 정산 총매출(gross_sales) | 결제 | 환불(refunded_amount/count) | 부분환불 | 매출총이익 | 마진율 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| today | 0원 | 0건 | 0원 | 0건 | 0원 / 0건 | 0원 / 0건 | 0원 | 0.0% |
| week | 159,300원 | 22건 | 161,300원 | 22건 | 3,000원 / 1건 | 2,000원 / 1건 | 120,800원 | 75.8% |
| month | 159,300원 | 22건 | 161,300원 | 22건 | 3,000원 / 1건 | 2,000원 / 1건 | 120,800원 | 75.8% |
| all | 159,300원 | 22건 | 161,300원 | 22건 | 3,000원 / 1건 | 2,000원 / 1건 | 120,800원 | 75.8% |

3. 비교/추세 기준

- 비교 기준: Mock POS API가 제공하는 period=today, week, month, all 조회값 간 비교입니다. 전일/전주 동일 시각의 별도 스냅샷은 이번 조회 결과에 포함되지 않아 전일 대비나 전주 대비 증감률은 산출하지 않았습니다.
- week/month/all 값은 현재 모두 동일합니다: 매출 159,300원, 주문 22건, 정산 총매출 161,300원, 매출총이익 120,800원, 마진율 75.8%.
- today는 week/month 누계 대비 신규 반영분이 없습니다. 따라서 오늘 아침 기준 신규 매출 흐름은 아직 발생하지 않은 상태로 확인됩니다.

4. 원천/조회 기준

- 원천 시스템: Mock POS API
- Base URL: http://mock-pos:8080
- Store ID: store_demo
- 인증 헤더: X-API-Key 사용(dev-key)
- 조회 엔드포인트:
  - GET /v1/stores/store_demo/reports/sales?period=today|week|month|all
  - GET /v1/stores/store_demo/reports/settlement?period=today|week|month|all
  - GET /v1/stores/store_demo/reports/margin?period=today|week|month|all
- 주요 필드 기준:
  - 매출: sales.total_sales
  - 주문 수: sales.order_count
  - 정산 총매출: settlement.gross_sales
  - 결제 건수: settlement.payment_count
  - 환불: settlement.refunded_amount, settlement.refunded_count
  - 부분환불: settlement.partial_refund_amount, settlement.partial_refund_count
  - 마진: margin.gross_margin, margin.margin_rate
- 마진 유의사항: Mock POS 마진 API는 원가 미등록 품목을 cost=0으로 계산할 수 있으므로, 원가 등록 누락이 있으면 마진율이 실제보다 높게 표시될 수 있습니다.
