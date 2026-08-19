# 05. Skill과 Tool — 프로필별 SKILL.md 정의

각 프로필의 핵심 `SKILL.md` 전체 초안입니다. 실제 파일은
`.hermes/profiles/<role>/skills/<category>/<skill-name>/SKILL.md`에 동일한 내용으로
배치되어 있습니다.

## Mock POS 연동 공통 규칙

`order-payment-agent`, `inventory-agent`, `reservation-agent`, `sales-analytics-agent`는
`code_execution`(샌드박스 파이썬)에서 `requests`로 Mock POS REST API를 호출합니다.

- 접속 정보: 환경변수 `MOCK_POS_BASE_URL`(예: `http://mock-pos:8080`), `MOCK_POS_API_KEY`
- 인증: 모든 요청에 `X-API-Key` 헤더 필요
- 매장 식별: 이번 버전은 매장 1곳만 지원하므로 `STORE_ID`(환경변수, 기본 `store_demo`)를
  경로의 `{store_id}`에 고정 사용
- 주요 엔드포인트(전체는 `mock-pos/README.md` 참고):

| 리소스 | Method/Path | 용도 |
|---|---|---|
| 카탈로그 | `GET/POST /v1/stores/{store_id}/catalog/items` | 메뉴/상품 조회·등록 |
| 주문 | `POST /v1/stores/{store_id}/orders`, `GET .../orders/{order_id}` | 주문 생성/조회 |
| 결제 | `POST /v1/stores/{store_id}/payments` | 결제 생성 — 주문을 `COMPLETED`로 전환하며 재고 차감 |
| 환불 | `POST /v1/stores/{store_id}/payments/{payment_id}/refund` | 결제를 `REFUNDED`로 전환, 재고 원상 복구 (게이트 3 승인 후에만 호출) |
| 재고 | `GET /v1/stores/{store_id}/inventory[/{item_id}]`, `POST .../adjust` | 재고 조회·조정 |
| 예약 | `POST/GET/PATCH /v1/stores/{store_id}/reservations[/{id}]`, `GET .../reservations?date=&status=` | 예약 생성/조회/취소/목록 |
| 리포트 | `GET /v1/stores/{store_id}/reports/sales` 또는 `.../settlement?period=` | 매출/정산 요약(`period`: today/week/month/all) |

각 스킬 폴더에는 실제로 로컬 mock-pos 서버를 띄워 검증한 레퍼런스 스크립트가
`scripts/`에 들어 있습니다(예: `order-payment-agent/skills/pos/order_and_payment/
scripts/pos_order_and_payment.py`). 카탈로그 조회 → 주문 생성 → 결제(재고 자동 차감) →
매출 리포트 반영까지 4개 스킬을 연달아 실행해 교차 검증했습니다 — REST 호출 로직 자체는
정확합니다.

> ✅ **2026-08-19 실측 완료**: `code_execution` 샌드박스가 실제로 `mock-pos` 컨테이너에
> 네트워크 접근 가능함을 확인했습니다(`order-payment-agent`에게 실제 챗으로 주문을
> 요청해 Mock POS에 실제 주문/결제가 생성되고 재고가 차감되는 것까지 검증). 다만
> **`code_execution` 샌드박스는 프로필의 `.env`(`MOCK_POS_BASE_URL` 등)를 자동으로
> 물려받지 않습니다** — 그래서 레퍼런스 스크립트의 기본값을 배포 값으로 하드코딩해뒀습니다
> (Mock POS API Key는 개발용 고정 키라 하드코딩해도 안전). [07장](07-roadmap.md) 참고.

---

## coordinator — `orchestration/task_dispatch_and_verification`

```yaml
name: task-dispatch-and-verification
description: "사장님 요청을 하위 프로필에 배정하고, 완료 보고를 Active Verification으로 재확인한 뒤 HITL 게이트에서 승인을 받는다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, coordinator, orchestration, verification]
platforms: [Linux, macOS, Windows]
```

**사용 시점**: 사장님의 자연어 요청(주문/재고/예약/CS/매출/마케팅 관련 문의나 지시)을 받아
하위 프로필에 작업을 위임·검증해야 할 때.

**절차**:
1. 요청을 분류해 담당 프로필(`order-payment-agent`/`inventory-agent`/`reservation-agent`/
   `customer-service-agent`/`sales-analytics-agent`/`marketing-crm-agent`)을 정하고
   `workspace/kanban/<날짜>-<슬러그>.md` 파일 카드를 만든다. **네이티브 `kanban` 툴은
   coordinator에서 실제로 로드되지 않는다**(2026-08-19 실측) — 파일 카드가 정식 방법이다.
2. `terminal(command='/opt/hermes/bin/hermes -p <role> chat -q "..."')`로 동기 호출해
   실제로 위임한다(`delegate_task` 사용 금지). **`terminal`은 약 120초 후 타임아웃될 수
   있음**(2026-08-19 실측) — 타임아웃돼도 하위 프로필이 백그라운드에서 계속 실행되어
   결과를 남길 수 있으므로, 3번 절차(Active Verification)로 반드시 재확인한다.
3. 카드를 `done`으로 옮기기 전, Mock POS를 재조회하거나 `workspace/` 산출물 파일을 직접
   열어 확인한다. 텍스트 보고만으로 승인하지 않는다. 확인 불가하면 `blocked`로 유지하고
   근거를 재요청한다.
4. 프로모션 집행 / 대량 발주 확정 / 환불·취소 처리 — 이 3개 HITL 게이트에 도달하면
   `messaging`/`clarify`로 사장님에게 검토를 요청하고, 명시적 승인 없이는 진행하지 않는다.
5. "오늘 브리핑" 같은 종합 요청은 `sales-analytics-agent`와 `inventory-agent`를 순서대로
   호출해 결과를 종합한 뒤 간결하게 보고한다.

**반환값**: 배정된 kanban 카드 목록과 상태 / Active Verification 결과 / HITL 게이트 통과
여부(승인/반려/대기).

---

## order-payment-agent — `pos/order_and_payment`

```yaml
name: pos-order-and-payment
description: "Mock POS에 주문을 생성하고 결제를 처리하며, 재고 부족·환불 상황을 정확히 보고한다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, pos, order, payment]
platforms: [Linux, macOS, Windows]
```

**사용 시점**: "OO 2잔 주문 들어왔어", "결제 확인해줘" 같은 주문/결제 요청을 받았을 때.

**절차**:
1. `code_execution`으로 `GET /catalog/items`를 조회해 품목·가격을 확인한다.
2. 총액을 계산해 사용자에게 확인한 뒤 `POST /orders`로 주문을 생성한다(재고는 아직
   차감되지 않음).
3. 결제 확정 요청이 오면 `POST /payments`를 호출한다 — 성공 시 주문이 `COMPLETED`로
   전환되고 재고가 자동 차감된다. 재고 부족이면 409 오류를 그대로 전달한다.
4. 환불 요청이 오면 먼저 coordinator에게 게이트 3(환불/취소) 승인을 요청한다. **승인
   확인 후에만** `POST /payments/{payment_id}/refund`를 호출한다 — 성공 시 결제/주문이
   `REFUNDED`로 전환되고 재고가 원상 복구된다.
5. `workspace/orders/<날짜>.md`에 주문/환불 요약(품목, 수량, 금액, 상태)을 追記한다.

**반환값**: 주문/결제/환불 결과(성공/실패, 사유), 산출물 파일 경로. (레퍼런스 스크립트로
실제 mock-pos 서버에 대해 end-to-end 검증 완료 — `.hermes/profiles/order-payment-agent/
skills/pos/order_and_payment/scripts/pos_order_and_payment.py`)

---

## inventory-agent — `pos/stock_and_reorder`

```yaml
name: pos-stock-and-reorder
description: "Mock POS 재고를 조회하고 임계치 이하 품목에 대해 발주를 제안·요청한다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, pos, inventory]
platforms: [Linux, macOS, Windows]
```

**사용 시점**: "재고 얼마나 남았어?", "발주해야 할 것 같은데" 같은 재고 관련 요청을
받았을 때.

**절차**:
1. `code_execution`으로 `GET /inventory` 또는 `GET /inventory/{item_id}`를 조회한다.
2. 재고가 임계치(기본 5개, `USER.md`에서 매장별 조정) 이하이면 먼저 경고하고 발주 여부를
   묻는다.
3. 발주 확정 시 예상 금액이 `USER.md`의 임계치를 넘으면 coordinator에게 게이트 2(대량 발주)
   승인을 요청한다. 임계치 이하 소액 발주는 즉시 진행하고 `POST /inventory/{item_id}/adjust`
   (양수 delta)로 입고를 반영한다.
4. `workspace/inventory/<날짜>.md`에 재고 현황과 발주 이력을 기록한다.

**반환값**: 현재 재고 수준, 발주 필요 여부, (해당 시) HITL 게이트 요청 여부.

---

## reservation-agent — `pos/reservation_management`

```yaml
name: pos-reservation-management
description: "Mock POS에 예약을 생성·변경·취소하고 노쇼 방지 리마인더를 발송한다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, pos, reservation]
platforms: [Linux, macOS, Windows]
```

**사용 시점**: 예약 생성/변경/취소 요청, 또는 예정된 예약의 리마인더를 보내야 할 때.

**절차**:
1. 날짜·시간·고객 정보를 확인한 뒤 `code_execution`으로 `POST /reservations`를 호출한다.
2. 예약일 전 `messaging` 툴셋으로 Discord에 리마인더를 직접 발송한다(HITL 게이트 대상
   아님).
3. 취소/변경 요청은 `PATCH /reservations/{id}`로 즉시 반영한다.
4. "오늘 예약 몇 건" 같은 질문은 `GET /reservations?date=&status=`로 목록을 조회해
   답한다.
5. `workspace/reservations/<날짜>.md`에 예약 현황을 기록한다.

**반환값**: 예약 결과(성공/실패), 리마인더 발송 여부, 산출물 파일 경로. (레퍼런스
스크립트로 실제 mock-pos 서버에 대해 end-to-end 검증 완료 —
`.hermes/profiles/reservation-agent/skills/pos/reservation_management/scripts/pos_reservation_management.py`)

---

## customer-service-agent — `support/faq_and_complaint`

```yaml
name: faq-and-complaint
description: "매장 FAQ를 조회해 응대하고, 답을 찾지 못하면 웹 검색으로 보완하며 불만을 기록한다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, customer-service, faq]
platforms: [Linux, macOS, Windows]
```

**사용 시점**: 고객 문의(영업시간, 메뉴, 정책 등) 응대 또는 불만 접수가 필요할 때.

**절차**:
1. `file` 툴셋으로 `workspace/customer-service/faq.md`를 조회한다.
2. FAQ에 없으면 `web`/`search`로 일반 정보를 보완하되, 매장 고유 정책은 추측하지 않고
   담당자 확인이 필요하다고 안내한다.
3. 불만이 접수되면 `workspace/customer-service/complaints.md`에 날짜와 함께 기록하고,
   심각도가 높다고 판단되면 coordinator에게 보고한다.

**반환값**: 응대 답변, (해당 시) 불만 티켓 기록 여부.

---

## sales-analytics-agent — `pos/sales_reporting`

```yaml
name: pos-sales-reporting
description: "Mock POS 매출/정산 데이터를 조회해 기간별 요약과 추세를 보고한다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, pos, sales, analytics]
platforms: [Linux, macOS, Windows]
```

**사용 시점**: "오늘 매출 어때?", "이번 주 정산 리포트 줘" 같은 매출/정산 요청을 받았을 때.

**절차**:
1. `code_execution`으로 `GET /reports/sales?period=`와 `GET /reports/settlement?period=`를
   조회한다(`period`: today/week/month/all).
2. 요청한 기간에 맞춰 요약하고, 추세를 언급할 때는 비교 기준을 명확히 밝힌다.
3. `workspace/sales/<날짜>.md`에 요약을 기록한다.

**반환값**: 매출/정산 요약, 산출물 파일 경로.

---

## marketing-crm-agent — `marketing/promo_and_segment`

```yaml
name: promo-and-segment
description: "트렌드를 조사해 홍보 문구 초안을 작성하고, 실제 집행 전 승인 절차를 안내한다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, marketing, crm]
platforms: [Linux, macOS, Windows]
```

**사용 시점**: 프로모션/홍보 문구 작성 요청, 캠페인 아이디어 요청을 받았을 때.

**절차**:
1. `web`/`search`로 트렌드·경쟁 매장 정보를 조사한다.
2. 매장 톤앤매너(`USER.md` 참고)에 맞춰 홍보 문구 초안을 작성하고, 반드시 "초안"임을
   명시한다.
3. `workspace/marketing/<날짜>.md`에 저장한다.
4. 유료 광고나 대량 발송 집행 의사가 확인되면 coordinator에게 게이트 1(프로모션 집행)
   승인이 필요함을 안내한다 — 이 프로필 자체는 발송하지 않는다.

**반환값**: 홍보 문구 초안, 산출물 파일 경로, HITL 게이트 필요 여부.
