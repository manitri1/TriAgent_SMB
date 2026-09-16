title: 오늘 매출 확인
assignee: sales-analytics-agent
status: done
created: 2026-09-14
details:
  - 사장님 요청: "오늘 매출 얼마예요?"
  - 기준일: 2026-09-14
  - 오늘 총매출과 주문 건수를 확인해 보고한다.
verification:
  - verification_file: /opt/data/workspace/reports/2026-09-14-sales-summary.md
  - direct_check: Mock POS GET /v1/stores/store_demo/reports/sales?period=today
  - direct_check: Mock POS GET /v1/stores/store_demo/reports/settlement?period=today
  - confirmed_total_sales: 24900 KRW
  - confirmed_order_count: 4
  - confirmed_refunded_amount: 0 KRW
  - confirmed_net_sales: 24900 KRW
