---
name: pos-order-and-payment
description: "Mock POS에 주문을 생성하고 결제를 처리하며, 재고 부족·환불 상황을 정확히 보고한다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, pos, order, payment]
platforms: [Linux, macOS, Windows]
---

## 사용 시점
"OO 2잔 주문 들어왔어", "결제 확인해줘" 같은 주문/결제 요청을 받았을 때.

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
`scripts/pos_order_and_payment.py`에 `list_catalog`/`create_order`/`pay_order`/
`get_order`/`refund_payment` 함수가 구현되어 있다(실제 mock-pos 서버로 end-to-end
검증됨: 카탈로그 조회 → 주문 생성 → 결제 → COMPLETED 전환 → 환불 → REFUNDED 전환 +
재고 복구까지 확인) — 시간을 아끼려면 이 파일을 읽어 그대로 실행해도 된다.

## 절차
1. `GET /v1/stores/{STORE_ID}/catalog/items`를 조회해 품목·가격을 확인한다.
2. 총액을 계산해 사용자에게 확인한 뒤 `POST /v1/stores/{STORE_ID}/orders`로 주문을
   생성한다(`line_items: [{item_id, quantity, note?}]`). 이 시점에는 재고가 차감되지
   않는다.
3. 결제 확정 요청이 오면 `POST /v1/stores/{STORE_ID}/payments`(`order_id`, `method`)를
   호출한다 — 성공 시 주문이 `COMPLETED`로 전환되고 재고가 자동 차감된다. 재고 부족이면
   409 오류를 그대로 전달한다.
4. 환불 요청이 오면 먼저 coordinator에게 게이트 3(환불/취소) 승인을 요청한다. **승인이
   확인된 뒤에만** `POST /v1/stores/{STORE_ID}/payments/{payment_id}/refund`를 호출한다
   — 성공 시 결제가 `REFUNDED`, 주문이 `REFUNDED`로 전환되고 재고가 원상 복구된다. 이미
   환불된 결제를 다시 호출하면 409 오류가 발생한다.
5. `workspace/orders/<날짜>.md`에 주문/환불 요약(품목, 수량, 금액, 상태)을 추가로 기록한다.

## 반환값
- 주문/결제/환불 결과(성공/실패, 사유)
- 산출물 파일 경로(`workspace/orders/<날짜>.md`)
