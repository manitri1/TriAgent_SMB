---
name: pos-sales-reporting
description: "Mock POS 매출/정산 데이터를 조회해 기간별 요약과 추세를 보고한다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, pos, sales, analytics]
platforms: [Linux, macOS, Windows]
---

## 사용 시점
"오늘 매출 어때?", "이번 주 정산 리포트 줘" 같은 매출/정산 요청을 받았을 때.

## 접속 정보 (2026-08-19 실측 — 반드시 이대로 할 것)
`code_execution` 샌드박스는 이 프로필의 `.env`를 상속하지 않는다. **환경변수
(`os.environ`)로 접속 정보를 조회하려 하지 말고, 아래 값을 코드에 리터럴로 직접 써서
바로 호출한다** — 이 값이 실제 배포 값이며, Mock POS API Key는 개발용 고정 키(실제
비밀값 아님)라 하드코딩해도 안전하다:
```python
BASE_URL = "http://mock-pos:8080"
API_KEY = "dev-key"
STORE_ID = "store_demo"
HEADERS = {"X-API-Key": API_KEY}
```
`requests`가 없으면 `urllib.request`로 대체해도 된다. 참고용으로
`scripts/pos_sales_reporting.py`에 `get_sales_summary`/`get_settlement_report` 함수가
구현되어 있다(실제 mock-pos 서버로 검증됨 — order-payment-agent가 만든 주문/결제가
매출 리포트에 정확히 반영되는 것까지 확인) — 시간을 아끼려면 이 파일을 읽어 그대로
실행해도 된다.

## 응답 필드 (2026-08-19 실측 — 반드시 이 필드명을 그대로 쓸 것)
응답 JSON에서 필드명을 추측하거나 "숫자처럼 보이는 값"을 임의로 고르지 않는다
(실측에서 `order_count`를 매출로 잘못 보고한 사례가 있었다). 정확한 필드는:
- `GET /reports/sales?period=` → `{"order_count": <건수>, "total_sales": <매출액>, "currency": "KRW"}`
  — **매출액은 `total_sales`다. `order_count`는 건수이지 금액이 아니다.**
- `GET /reports/settlement?period=` → `{"gross_sales": <총매출>, "payment_count": <결제건수>,
  "refunded_amount": <환불액>, "refunded_count": <환불건수>, "currency": "KRW"}`

## 절차
1. `GET /v1/stores/{STORE_ID}/reports/sales?period=`와
   `GET /v1/stores/{STORE_ID}/reports/settlement?period=`를 조회한다(`period`:
   today/week/month/all).
2. 위 "응답 필드"의 정확한 키(`total_sales`, `gross_sales` 등)로 값을 읽는다. 요청한
   기간에 맞춰 요약하고, 추세를 언급할 때는 비교 기준을 명확히 밝힌다.
3. `workspace/sales/<날짜>.md`에 요약을 기록한다.

## 반환값
- 매출/정산 요약
- 산출물 파일 경로
