# 2026-09-14 매출 요약

데이터 소스: Mock POS API
- 매출: GET /v1/stores/store_demo/reports/sales?period=today
- 정산: GET /v1/stores/store_demo/reports/settlement?period=today
- 통화: KRW

## 요약

- 총매출: 24,900원
- 매출 리포트 기준 total_sales: 24,900원
- 주문 건수: 4건
- 결제 건수: 4건
- 환불액: 0원 (0건)
- 부분 환불액: 0원 (0건)
- 순매출: 24,900원

## 원본 응답

### /reports/sales?period=today

```json
{
  "store_id": "store_demo",
  "period": "today",
  "order_count": 4,
  "total_sales": 24900,
  "currency": "KRW"
}
```

### /reports/settlement?period=today

```json
{
  "store_id": "store_demo",
  "period": "today",
  "gross_sales": 24900,
  "payment_count": 4,
  "refunded_amount": 0,
  "refunded_count": 0,
  "partial_refund_amount": 0,
  "partial_refund_count": 0,
  "currency": "KRW"
}
```
