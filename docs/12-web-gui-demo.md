# 12. 웹 GUI 연동 — 채팅 + 실적 그래픽 분석 시연 방안

이 문서는 이 에이전트 시스템을 브라우저에서 **(1) 채팅**하고 **(2) 매출/재고 같은
실적을 그래픽으로** 볼 수 있게 만드는 시연(demo) 환경에 대한 가이드라인입니다. 아래
"실적 대시보드"는 **Tier 1·2·3 기능(원가/마진, 부분환불, 고객 CRM MVP 포함)까지
실제로 구현·검증 완료했습니다**(2026-08-23) — Discord 일일요약(Tier 3의 마지막
항목)만 `DISCORD_BOT_TOKEN` 미설정으로 설계까지만 완료하고 실제 발송은 미검증
상태입니다. 이 문서는 무엇이 이미 있고 무엇을 새로 만들어야 하는지 조사한 결과,
기능을 **어떤 순서로, 무엇부터** 만들면 소상공인 사장님께 실제로 도움이 되는지,
그리고 실제 구현·검증 결과를 정리한 것입니다.

## 1. 개요

목표를 두 요소로 나눠서 봅니다:

1. **채팅** — 사장님/직원이 브라우저에서 coordinator 등 7개 프로필과 대화
2. **실적 그래픽 분석** — 매출/재고 같은 매장 데이터를 그래프로 확인

두 요소를 하나의 새 앱으로 합쳐서 처음부터 만들기 전에, 이미 배포된 시스템에 뭐가
있는지부터 확인했습니다 — 그 결과 아래처럼 **범위가 크게 줄었습니다**.

## 2. 조사 결과 (설계를 결정한 핵심 발견)

`docs/08-docker-deployment.md`에서 크래시 루프를 고쳐 정상 기동시켜 둔 Hermes
대시보드(`docker-compose`의 `dashboard` 서비스, `http://localhost:19128`)가 **단순
설정 화면이 아니라 실제 채팅 UI를 내장하고 있다**는 것을 이번에 확인했습니다.
컨테이너 안에 번들된 웹 UI(`/opt/hermes/hermes_cli/web_dist/assets/*.js`)에서 프론트
엔드 라우트를 직접 뽑아보면:

```
/chat  /profiles  /sessions  /analytics  /config  /logs  /files  /mcp  /webhooks
/channels  /cron  /docs  /env  /models  /pairing  /plugins  /skills  /system  /profiles/new
```

- **`/chat` + `/profiles`가 이미 있습니다** — 즉 "웹에서 채팅"은 **새로 만들 필요가
  없습니다.** 우리 7개 프로필(coordinator, order-payment-agent 등)을 그대로 선택해
  브라우저에서 대화할 수 있을 것으로 보입니다. (주의: 로그인 세션이 필요해 이번
  조사에서는 번들 코드에서 라우트 존재만 확인했고, 실제 클릭까지 검증하지는
  못했습니다 — [9. 알려진 제약](#9-알려진-제약) 참고.)
- **`/analytics`도 있지만 용도가 다릅니다** — 이건 `hermes insights` CLI 명령(토큰
  사용량/비용 분석)과 같은 **Hermes 자체 사용량 분석**이지, 우리 매장의 매출/재고
  같은 **비즈니스 실적**이 아닙니다. 즉 "실적을 그래픽으로 분석"은 **여기 없고,
  새로 만들어야 합니다.**
- 필요한 비즈니스 데이터(매출/정산/재고/주문)는 전부 `mock-pos/`가 이미 REST로
  제공합니다(`/reports/sales`, `/reports/settlement`, `/inventory` 등 —
  `docs/05-skills-and-tools.md`, `docs/10-usecase-tests.md`에서 이미 실측
  검증됨) — 데이터 쪽은 이미 준비되어 있습니다.

## 3. 아키텍처 결정

| 요구사항 | 방법 | 이유 |
|---|---|---|
| 웹에서 채팅 | 기존 Hermes 대시보드 `/chat` 재사용 (`localhost:19128`) | 이미 구현되어 있음 — 새 코드 불필요 |
| 실적 그래픽 분석 | `mock-pos`에 `GET /dashboard` HTML 페이지 신규 추가 (Chart.js) | mock-pos 자신의 REST API를 같은 오리진(origin)에서 호출하므로 CORS 문제가 없고, 새 포트/서비스도 필요 없음 |

두 화면을 억지로 한 앱에 통합하지 않고 **URL 두 개**(`:19128` 채팅, `:18080/dashboard`
실적)로 시연하는 것을 권장합니다. 왜 합치지 않는가: 대시보드(채팅)는 Hermes가 소유한
번들 앱이라 우리가 그 안에 임의 페이지를 끼워 넣기 어렵고, 반대로 실적 페이지를
Hermes 인증 체계 안에 넣으려면 불필요하게 복잡해집니다. 대신 시연 시나리오 자체가
두 화면을 자연스럽게 이어줍니다 — 아래 7번 참고.

## 4. 채팅 화면 사용법 (구현 불필요 — 지금 바로 가능)

1. `http://localhost:19128` 접속 → 로그인(계정은 `.hermes/.env`의
   `HERMES_DASHBOARD_BASIC_AUTH_USERNAME`/`_PASSWORD_HASH` 참고, `docs/08-docker-deployment.md`
   에서 설정한 로컬 개발용 기본 계정 — 로컬 데모 외 용도로는 반드시 교체).
2. `/profiles`(또는 상단 네비게이션)에서 대화할 프로필 선택 — 시연 시작은
   `coordinator` 권장(`docs/03-hermes-agent-integration.md` 참고, 유일한 대화
   진입점으로 설계됨).
3. `/chat`에서 자연어로 대화. 예: "아메리카노 2잔 주문 들어왔어, 결제까지 처리해줘."

## 5. 실적 대시보드 — 기능 우선순위

"실적을 그래픽으로 본다"는 목표를 소상공인 사장님 관점에서 쪼개면, 기능마다 **지금
당장 만들 수 있는 것**과 **mock-pos를 조금 손봐야 하는 것**이 섞여 있습니다. 이
섹션은 무엇부터 만들지 우선순위를 정하기 위한 것이고, 실제 구현 절차는
[6. 구현 가이드](#6-실적-대시보드-구현-가이드)에서 다룹니다.

### 5.1 Tier 1 — 기존 API만으로 즉시 구현 가능

아래는 mock-pos 코드를 한 줄도 바꾸지 않고, `GET /dashboard` 페이지에서 기존
엔드포인트를 호출하기만 하면 되는 기능입니다. 사장님이 "오늘 장사 어땠나" 감을
잡는 데 필요한 최소 세트입니다.

| 기능 | 사용 엔드포인트 | 비고 |
|---|---|---|
| 매출 요약 카드 (오늘/이번 주/이번 달/전체) | `GET /reports/sales?period=today\|week\|month\|all` (4회 호출) | 이미 `docs/05`, `docs/10`에서 실측 검증됨 |
| 정산 요약 카드 (총매출·결제건수·환불액·환불건수) | `GET /reports/settlement?period=` | 위와 동일 엔드포인트 그룹 |
| 재고 현황 막대그래프 + 저재고 강조 | `GET /inventory` | 임계치는 페이지 안에 상수(예: 5)로 하드코딩 — **데모 전용**. 매장·품목별로 다른 임계치를 서버에 저장하는 것은 5.2 참고 |
| 오늘 예약 목록 | `GET /reservations?date=<오늘>&status=BOOKED` | 미용실/식당 시나리오에서 유용 |
| 새로고침 버튼 (+ 선택적 10초 자동 새로고침) | 위 엔드포인트 재호출 | 시연 중 채팅으로 만든 주문이 반영되는 걸 보여주는 용도 |

### 5.2 Tier 2 — mock-pos에 소규모 추가가 필요

아래 기능들은 "왜 안 되는지"가 명확했습니다 — mock-pos가 필요한 데이터를 아예 반환하지
않거나 저장하지 않았기 때문입니다. 각각 **기존 엔드포인트/모델을 변경하지 않고
추가만** 하는 방식으로 구현해, 기존 pytest 7건에는 영향이 없습니다.

| 기능 | 왜 지금 안 되나 | 무엇을 추가해야 하나 |
|---|---|---|
| 주문 이력 테이블 | `mock_pos/routers/orders.py`에 목록 조회(`GET ""`)가 없고 단건 조회(`GET /{order_id}`)만 있음 | `GET /v1/stores/{store_id}/orders` 신규 — `status` 필터 파라미터 제안 |
| 인기 메뉴 TOP5 (품목별 집계) | `mock_pos/routers/reports.py`는 결제 총액만 합산할 뿐, 주문의 `line_items`를 품목(`item_id`)별로 나눠 집계하지 않음 | `GET /v1/stores/{store_id}/reports/top-items?period=&limit=5` 신규 — 완료 상태 주문의 `line_items`를 `item_id`별로 합산해 수량·매출 내림차순 정렬 |
| 매출 추이 그래프 (일별 꺾은선) | 현재 `/reports/sales`는 today/week/month/all 4개의 **정적 합계 하나씩**만 반환 — 일자별 시계열이 없어 "추이"를 그릴 수 없음 | `GET /v1/stores/{store_id}/reports/sales/daily?days=7` 신규 — 결제 완료건을 `created_at.date()` 기준으로 날짜별 버킷화 |
| 서버 저장 저재고 임계치 | `mock_pos/models.py`의 `InventoryItem`에 임계치 필드가 없음 — 현재는 inventory-agent가 `.hermes/profiles/inventory-agent/USER.md`에 적힌 값을 코드 실행 중에만 참고하고, 대시보드는 이를 알 방법이 없음 | `CatalogItemCreate`(`mock_pos/routers/catalog.py`에서 사용)에 `low_stock_threshold: int = 5` 필드 추가 — 품목 생성 시점에 저장해 inventory-agent와 대시보드가 같은 값을 참조하도록 함 |

✅ **2026-08-23 실측 완료**: 위 4개 항목 모두 구현했습니다 — `mock_pos/routers/orders.py`의
`GET ""`(목록), `mock_pos/routers/reports.py`의 `GET /top-items`·`GET /sales/daily`,
`mock_pos/models.py`/`catalog.py`의 `low_stock_threshold` 필드. `mock-pos/tests/test_dashboard.py`
신규 테스트 5건 + 기존 7건 = 총 12건 pytest 통과, `docker compose build/up mock-pos` 후
실제 주문→결제를 curl로 흘려보내 인기 메뉴 TOP5·일별 매출·주문 목록·재고 임계치에
정확히 반영되는 것까지 확인했습니다.

### 5.3 Tier 3 — 원가/마진, 부분환불, 고객 CRM MVP, Discord 일일요약

✅ **2026-08-23 실측 완료**(Discord 제외): 아래 4개 항목 중 첫 3개(원가/마진,
부분환불, 고객 CRM MVP)는 실제로 구현하고 pytest·curl로 검증했습니다. Discord
일일요약은 설계/코드만 완료하고 실제 발송은 `DISCORD_BOT_TOKEN` 준비 후로 미룹니다.
구현 상세는 [6.5](#65-tier-3-mock-pos-변경-사항)를 참고하세요.

- **원가/마진 기반 수익 대시보드** — `.hermes/manicafe/test-data/products.csv`에
  이미 있던 `cost`(원가) 컬럼을 `CatalogItem`/`InventoryItem`에 반영하고,
  `GET /reports/margin?period=`을 신규 추가해 매출총이익/마진율을 계산합니다.
  원가 미등록 품목은 `cost=0`으로 계산되므로 마진이 과대 표시될 수 있다는 점을
  대시보드/스킬 양쪽에 명시했습니다.
- **부분환불 지원** — `.hermes/manicafe/test-data/sample_orders.csv`의
  `partially_refunded` 사례처럼, `POST /payments/{id}/refund`에 선택적 `amount`를
  추가해 잔액 일부만 환불할 수 있게 했습니다. 잔액이 남으면 `PARTIALLY_REFUNDED`로
  전환되고 **재고는 복구되지 않습니다**(현금 조정으로 취급 — 품목 단위 반품은 범위
  밖). 전액이 채워지는 순간에만 기존과 동일하게 `REFUNDED` + 재고 복구가 일어납니다.
  HITL 게이트는 새로 만들지 않고 기존 게이트 3(환불/취소)을 그대로 재사용합니다
  (`docs/06-hitl-approval-design.md`).
- **고객 엔티티 / 재방문 고객 분석(CRM MVP)** — 가벼운 `Customer` 레코드(이름/전화/
  메모)와 `GET /reports/repeat-customers?period=&min_orders=`를 추가했습니다.
  `order_count`/`total_spent`/`last_order_at`는 저장하지 않고 조회 시 주문 데이터로
  계산합니다. 세그멘테이션 엔진, 고객 수정/삭제, `Order.customer_id`의 FK 강제는
  **범위 밖**입니다. `marketing-crm-agent`가 이 엔드포인트를 읽기 전용으로 호출하도록
  스킬을 연결해 `docs/10-usecase-tests.md` TC-20("단골 고객 세그먼트 없음")의 갭을
  실제 데이터로 메웠습니다.
- **Discord로 일일 요약 자동 발송** — ⬜ **미검증**. `coordinator`의 SOUL.md/SKILL.md에
  절차와 메시지 템플릿을 추가했습니다(`reservation-agent`의 기존 노쇼 리마인더와
  동일하게 `messaging` 네이티브 툴 + Hermes 게이트웨이 경로만 사용, 별도 webhook
  없음). `DISCORD_BOT_TOKEN`이 아직 설정되지 않아 실제 발송은 `docs/07-roadmap.md`
  §4에 미검증으로 남아 있습니다. 매일 무인 자동 발송을 위한 트리거(Hermes 네이티브
  `/cron` vs 외부 OS 스케줄러)도 이번 라운드에서는 결정하지 않았습니다.

**대시보드에서 바로 "실행"하는 버튼(1-클릭 재주문, 환불 등)** — 위 4개와 별개로, 이건
우선순위 문제가 아니라 **하드 제약**입니다: 브라우저 JS가 mock-pos를 직접 호출해서는
안 되고, 반드시 기존 HITL 승인 게이트(`docs/06-hitl-approval-design.md`)를 통과하는
에이전트 위임 경로를 거쳐야 합니다. 대시보드는 계속 **조회 전용(read-only)**으로
유지합니다 — Tier 3 구현에서도 이 원칙을 지켰습니다(새 카드 4개 모두 GET 호출만).

## 6. 실적 대시보드 구현 가이드

✅ **2026-08-23 실측 완료**: 아래 Tier 1·2·3(Discord 제외) 절차 전체를 실제로
구현하고 [8. 검증 계획](#8-검증-계획)의 모든 단계를 통과시켰습니다.

### 6.1 mock-pos 변경 사항

**Tier 1만 구현할 경우** — mock-pos 코드 변경 없음. 아래 신규 파일 하나만 추가합니다.

- `mock-pos/mock_pos/routers/dashboard.py` (신규 파일)
- `mock-pos/mock_pos/main.py`에 새 라우터 등록 1줄
- Chart.js (CDN) — 별도 설치 불필요, `<script src="https://cdn.jsdelivr.net/npm/chart.js">`
  로 충분

**Tier 2까지 구현할 경우** — 위에 더해 아래 파일들에 **추가만** 합니다(기존 응답
스키마·엔드포인트 시그니처는 바꾸지 않음, 기존 pytest 7건 영향 없음):

- `mock-pos/mock_pos/models.py` — `low_stock_threshold` 필드, `TopItem`/`DailySales`
  응답 모델 추가
- `mock-pos/mock_pos/routers/reports.py` — `GET /top-items`, `GET /sales/daily`
  신규 엔드포인트 2개 추가
- `mock-pos/mock_pos/routers/orders.py` — `GET ""` (목록 조회) 신규 추가
- `mock-pos/mock_pos/routers/catalog.py` — `CatalogItemCreate`에 저재고 임계치
  필드 반영

### 6.2 `GET /dashboard` 페이지 구성

1. `GET /dashboard`가 자체 완결형 HTML(인라인 CSS/JS)을 반환하도록 구현합니다.
   페이지 섹션 구성:
   - **매출 추이**: Tier 1 단계에서는 `GET /reports/sales?period=today|week|month|all`
     4개를 막대/라인으로 비교. Tier 2 구현 후에는 `GET /reports/sales/daily?days=7`로
     실제 일별 꺾은선 그래프로 교체.
   - **정산 요약 카드**: `GET /reports/settlement?period=`의 `gross_sales`,
     `payment_count`, `refunded_amount`, `refunded_count`를 카드 형태로 표시.
   - **인기 메뉴 TOP5** (Tier 2): `GET /reports/top-items?period=&limit=5` 결과를
     표 또는 막대그래프로 표시.
   - **재고 현황**: `GET /inventory`를 막대그래프로, 임계치(Tier 1: 상수, Tier 2:
     `low_stock_threshold` 필드) 이하 품목은 색상으로 강조.
   - **오늘 예약**: `GET /reservations?date=&status=BOOKED`를 표로 표시.
   - **새로고침 버튼**(+ 선택적으로 10초 자동 새로고침) — 시연 중 채팅으로 만든
     주문이 반영되는 걸 보여주는 용도.
2. 인증은 기존 `mock-pos`의 `X-API-Key` 미들웨어(`mock_pos/auth.py`)와 동일 수준을
   유지하되, 이 페이지의 브라우저 JS에는 `dev-key`를 그대로 하드코딩합니다 —
   **로컬 데모 전용**이며 실제 배포용이 아니라는 점을 페이지 하단과 이 문서 모두에
   명시합니다.

### 6.3 테스트

- `mock-pos/tests/`에 `GET /dashboard` 200 응답 + 핵심 마커(예: 페이지 제목,
  Chart.js 스크립트 태그) 포함 여부를 확인하는 테스트를 추가합니다.
- Tier 2까지 구현하는 경우, 신규 엔드포인트 3개(`GET /orders`, `GET /reports/top-items`,
  `GET /reports/sales/daily`)에 대해 카탈로그/주문/결제를 미리 만들어 둔 뒤 응답
  스키마와 값을 확인하는 테스트를 기존 `test_flow.py`의 `TestClient` 패턴을 따라
  추가합니다.
- 기존 7건 pytest와 함께 통과시킵니다(`mock-pos/README.md`의 `pytest` 절차 참고).

### 6.4 재기동 절차

```bash
docker compose build mock-pos && docker compose up -d mock-pos
```

`hermes`/`dashboard` 컨테이너는 건드릴 필요 없음.

### 6.5 Tier 3 mock-pos 변경 사항

Tier 1/2와 동일하게 **추가만**(기존 응답 스키마·엔드포인트 시그니처 불변) 하는
방식으로 구현했습니다 — 기존 pytest 20건(Tier 1/2 시점)에 영향 없이 5건이
더 늘어 25건이 되었습니다.

- `mock-pos/mock_pos/models.py` — `CatalogItemCreate`/`CatalogItem.cost`,
  `TopItem.cost`/`margin`, 신규 `MarginSummary`; `Payment.refunded_amount`,
  신규 `RefundRequest`, `SettlementReport.partial_refund_amount`/
  `partial_refund_count`; 신규 `CustomerCreate`/`Customer`/`RepeatCustomer`.
- `mock-pos/mock_pos/routers/catalog.py` — 생성 시 `cost` 저장.
- `mock-pos/mock_pos/routers/payments.py` `refund_payment` — `amount`(선택, 생략
  시 잔액 전액)를 받아 부분/전액 환불 처리. 전액이 채워질 때만 `REFUNDED` + 재고
  복구, 그 전까지는 `PARTIALLY_REFUNDED` + 재고 불변.
- `mock-pos/mock_pos/routers/reports.py` — `GET /margin`, `GET /repeat-customers`
  신규; `get_sales_summary`/`get_settlement_report`/`get_top_items`가
  `PARTIALLY_REFUNDED` 결제도 순액 기준으로 반영하도록 확장.
- `mock-pos/mock_pos/routers/orders.py` — `list_orders`에 `customer_id` 선택
  필터 추가.
- `mock-pos/mock_pos/routers/customers.py` (신규 파일) — 고객 upsert/조회.
- `mock-pos/mock_pos/store.py` — `StoreData.customers` 딕셔너리 추가.
- `mock-pos/mock_pos/routers/dashboard.py` — 원가/마진 카드, 부분환불 행,
  재방문 고객 표 카드 추가(모두 GET 호출만).
- 신규 테스트: `test_margin.py`, `test_refund_partial.py`, `test_customers.py`.
- Hermes 프로필 측 변경: `sales-analytics-agent`(마진 조회 절차),
  `order-payment-agent`(부분환불 절차), `marketing-crm-agent`(재방문 고객 조회
  절차 + `scripts/pos_customer_segment.py` 신규), `coordinator`(Discord 일일요약
  절차, 설계만) — `docs/05-skills-and-tools.md`에 동일하게 반영.

### 참고
- 관련 기존 엔드포인트 전체 목록: `docs/05-skills-and-tools.md`
- Mock POS 실행/테스트 방법: `mock-pos/README.md`

## 7. 시연 스크립트

**Tier 1까지 구현 완료 후:**

1. `http://localhost:19128`에서 coordinator에게 채팅으로 주문 요청
   (예: "아메리카노 2잔 주문 들어왔어, 결제까지 처리해줘").
2. coordinator가 order-payment-agent에게 위임 → Mock POS에 실제 주문/결제 생성됨
   (`docs/10-usecase-tests.md` TC-22에서 이미 실측 검증된 경로).
3. `http://localhost:18080/dashboard`를 열거나 새로고침 → 방금 발생한 매출이 차트에
   반영된 것을 확인.
4. (선택) 재고가 임계치 이하로 떨어지는 시나리오를 만들어 재고 그래프의 강조 표시도
   함께 시연.

**Tier 2까지 구현 완료 후, 위 시나리오에 이어서:**

1. 서로 다른 메뉴로 여러 건 주문을 추가 발생시킴.
2. 대시보드를 새로고침해 **인기 메뉴 TOP5** 순위가 실제 주문 내역에 따라 바뀌는 것과,
   **매출 추이 그래프**가 하루 안에서도 여러 시점의 값을 반영해 갱신되는 것을 함께
   시연.

**Tier 3까지 구현 완료 후, 위 시나리오에 이어서:**

1. 원가가 등록된 메뉴로 주문을 발생시킨 뒤 대시보드의 **원가/마진** 카드에 매출총이익/
   마진율이 반영되는 것을 확인.
2. 결제 하나를 부분환불(예: 6,000원 중 2,000원)해 정산 카드의 **부분환불액**이
   올라가고, 재고는 그대로인 것을 확인(전액 환불과의 차이를 함께 시연).
3. 같은 고객으로 주문을 2건 이상 발생시켜 **재방문 고객 TOP** 표에 나타나는 것을
   확인 — coordinator에게 "단골 고객 세그먼트 알려줘"라고 물어 marketing-crm-agent가
   같은 데이터를 채팅으로도 보고하는지 함께 시연(가능하면).
4. (Discord 일일요약은 `DISCORD_BOT_TOKEN` 준비 전까지 이 시연에서 제외)

## 8. 검증 계획

각 단계는 **각 단계를 실제로 실행/클릭/curl로 확인하기 전까지는 "미구현"/"⬜" 상태로
남겨둔다**는 `docs/07-roadmap.md`와 같은 원칙을 따릅니다. 아래 1~4단계(pytest, docker
재기동, Tier 1/2 curl 검증, Tier 3 curl 검증)는 2026-08-23에 실제로 실행해 통과를
확인했습니다. 5단계(브라우저로 채팅→대시보드 시연)와 6단계(Discord 실제 발송)는 아직
**미검증**입니다 — 이 환경이 헤드리스라 curl/pytest로 mock-pos API 계층은 끝까지
확인했지만, Hermes 대시보드 `/chat` 화면을 실제로 클릭해 본 것도, `DISCORD_BOT_TOKEN`을
설정해 본 것도 아닙니다([9. 알려진 제약](#9-알려진-제약) 참고).

1. ✅ `cd mock-pos && pytest` — Tier 1/2 시점 12건 → Tier 3(원가/마진, 부분환불,
   고객 CRM MVP) 추가 후 총 **25건 전체 통과**.
2. ✅ `docker compose build mock-pos && docker compose up -d mock-pos` — 정상 재기동.
3. ✅ curl로 실제 흐름 확인: `GET /dashboard` → 200 + HTML/Chart.js 마커 확인,
   카탈로그 등록 → 주문 생성 → 결제 완료까지 curl로 흘려보낸 뒤
   `GET /reports/top-items`(품목·수량·매출 정확히 반영), `GET /reports/sales/daily`
   (해당 날짜 버킷에 매출 반영), `GET /orders`(방금 만든 주문 노출),
   `GET /inventory/{item_id}`(`low_stock_threshold` 필드 포함해 재고 차감 반영)까지
   모두 값이 맞는 것을 확인.
4. ✅ Tier 3 curl 검증: 원가 등록 → 주문/결제 → `GET /reports/margin`이
   `total_revenue=3500`/`total_cost=800`/`gross_margin=2700` 정확히 계산; 결제
   3,500원 중 1,000원 부분환불 → 응답 `status=PARTIALLY_REFUNDED`,
   `refunded_amount=1000`, 재고 불변(10개 등록 → 주문으로 9개 → 환불 후에도 9개
   그대로), `GET /reports/settlement`의 `partial_refund_amount`/`partial_refund_count`
   반영 확인; 동일 고객으로 2건 주문 후 `GET /reports/repeat-customers?min_orders=2`
   에 `order_count=2`/`total_spent`(부분환불 순액 반영)로 노출, 미등록
   `customer_id`도 `GET /customers/{id}`로 조회 가능함을 확인;
   `GET /dashboard` HTML에 "원가/마진", "부분환불액", "재방문 고객 TOP" 마커가
   모두 포함됨을 확인.
5. ⬜ 수동 시연: [7. 시연 스크립트](#7-시연-스크립트) 그대로 브라우저에서 실행 —
   채팅으로 주문 → 대시보드 새로고침 → 반영 확인. (미검증 — 위 참고)
6. ⬜ Discord 일일요약 실제 발송 — `DISCORD_BOT_TOKEN` 설정 후 진행 예정
   (`docs/07-roadmap.md` §4 참고). 이번 라운드에서는 시도하지 않음(사용자 결정).

## 9. 알려진 제약

- 실적 대시보드(`GET /dashboard`)는 브라우저 JS에 `X-API-Key`를 하드코딩하므로
  **로컬 데모 전용**입니다 — 외부에 노출하는 배포에는 적합하지 않습니다.
- Hermes 대시보드의 `/chat`이 실제로 프로필과 정상적으로 대화되는지는 이 환경이
  헤드리스(브라우저 도구 없음)라 직접 클릭까지 검증하지 못했습니다 — 번들된 프론트
  엔드 코드에서 라우트 존재만 코드 레벨로 확인했습니다. 실제 사용 전 한 번 직접
  로그인해 확인하는 것을 권장합니다.
- `/dashboard`는 Tier 1·2·3 기능까지 구현·curl 검증을 마쳤습니다(2026-08-23,
  [6번](#6-실적-대시보드-구현-가이드) 참고). 다만 브라우저로 직접 열어 차트가
  시각적으로 정상 렌더링되는지는 이 환경이 헤드리스라 확인하지 못했습니다 — 실제
  사용 전 한 번 `http://localhost:18080/dashboard`를 직접 열어 확인하는 것을
  권장합니다.
- Tier 2/3 신규 엔드포인트(주문 목록, 인기 메뉴 TOP5, 일별 매출, 마진, 고객,
  재방문 고객)도 mock-pos의 다른 데이터와 동일하게 **인메모리 저장소**를 사용하므로,
  프로세스(컨테이너) 재시작 시 함께 초기화됩니다 — 별도 영속화 계획은 없습니다.
- 저재고 임계치를 카탈로그 생성 시점(`POST /catalog/items`)에만 설정 가능하게 할
  경우, 이미 만들어진 품목의 임계치를 나중에 바꾸는 API는 이번 설계에 포함되지
  않습니다 — 필요해지면 `PATCH /inventory/{item_id}/threshold` 같은 별도 엔드포인트
  추가를 검토해야 합니다.
- **부분환불은 현금 조정으로만 처리됩니다** — 재고 단위 반품(예: "2개 중 1개만
  반품")은 지원하지 않습니다. 품목 단위 부분 반품이 필요해지면 `line_items`별
  환불 수량을 받는 확장이 필요합니다.
- **고객 CRM은 MVP 범위**입니다 — 세그멘테이션 엔진, 고객 정보 수정/삭제, 마케팅
  동의 관리, `Order.customer_id`의 FK 강제는 없습니다. `order_count`/`total_spent`는
  매 조회마다 전체 결제 내역을 스캔해 계산하므로, 결제 건수가 매우 많아지면 성능
  최적화가 필요할 수 있습니다(현재 데모 규모에서는 문제 없음).
- **Discord 일일요약은 미검증**입니다 — `DISCORD_BOT_TOKEN`이 설정되지 않아 실제
  발송을 확인하지 못했습니다(`docs/07-roadmap.md` §4). 매일 무인 자동 발송 트리거도
  아직 결정하지 않았습니다.
- 원가(`cost`) 미등록 품목은 마진 계산에서 `cost=0`으로 처리되어 마진이 실제보다
  높게 표시될 수 있습니다 — `sales-analytics-agent`가 이 점을 언급하도록 스킬에
  명시했지만, 대시보드 UI 자체에는 별도 경고 표시가 없습니다.
