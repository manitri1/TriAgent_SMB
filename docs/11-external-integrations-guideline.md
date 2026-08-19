# 11. 외부 연동 가이드라인 — Shopify / Stripe 테스트 자동화

이 문서는 아래 3개 작업을 실제로 구현하기 **전에** 필요한 준비물, 안전 원칙, 단계별
절차를 정리한 가이드라인입니다. 세 작업 모두 API 키/테스트 키가 필요하며 아직 확보되지
않았으므로, 이 문서 자체는 실행 코드가 아니라 **키가 준비된 뒤 바로 구현에 들어갈 수
있도록 하는 체크리스트**입니다.

1. Shopify dev-store에 `products.csv` 자동 업로드 (Shopify Admin API 스크립트)
2. Stripe 테스트 결제 시나리오 자동화 (결제 생성/환불 스크립트)
3. 샘플 주문을 Shopify 또는 로컬 데모 DB에 삽입하는 스크립트 (테스트 모드, 선택적)

## 이 프로젝트(TriAgent_SMB)와의 관계

현재 TriAgent_SMB는 `mock-pos/`(자체 FastAPI Mock POS)를 POS 시뮬레이터로 사용하고
있고, 실 벤더 연동 후보로는 국내 POS(토스플레이스/카카오페이)를 [07-roadmap.md](07-roadmap.md)
5번에 적어뒀습니다. Shopify/Stripe는 그것과는 별도의 이커머스/결제 플랫폼입니다 —
이 문서는 Shopify/Stripe 자체를 다루는 **독립적인 가이드라인**이며, TriAgent_SMB의
Hermes 프로필/Skill에 실제로 연결할지는 아직 결정된 바 없습니다. 연동하기로 결정되면
`docs/07-roadmap.md`에 별도 항목으로 추가하고, 해당 Skill의 REST 호출 대상만 교체하는
어댑터 방식(Mock POS를 다룰 때와 동일한 패턴)을 권장합니다.

## 공통 안전 원칙

- **테스트/개발 환경에서만 수행합니다** — Shopify Development Store, Stripe **Test
  mode**만 사용하고 실 스토어·실 결제(live key)는 절대 사용하지 않습니다.
- API 키는 `.env`에만 저장하고 절대 커밋하지 않습니다 — 이 저장소의 `.gitignore`가
  `.env` 패턴을 이미 광범위하게 제외하고 있으니, 새 키 변수를 추가할 때도 반드시
  `.env.example`에는 빈 템플릿만, 실제 값은 `.env`(커밋 대상 아님)에만 넣습니다.
- 각 스크립트는 실행 전 사용자에게 무엇을 하는지(생성/삭제/환불 등) 명확히 알리고,
  파괴적이거나 되돌리기 어려운 호출(실 주문 취소, 대량 삭제 등)은 만들지 않습니다.
- Shopify Admin API는 호출 빈도 제한(rate limit)이 있으므로 대량 업로드 시 재시도/
  백오프 로직이 필요합니다.

## 1) Shopify `products.csv` 자동 업로드

### 필요한 것
- Shopify Partner 계정 + Development Store (무료)
- Store 안에서 만든 Custom App의 Admin API access token, scope: `write_products`
  (읽기 확인용으로 `read_products`도 함께)

### 절차
1. [Shopify Partners](https://www.shopify.com/partners) 계정 생성 → Development
   Store 생성(테스트 전용, 실제 과금 없음).
2. 스토어 관리자 화면 → **Settings → Apps and sales channels → Develop apps** →
   커스텀 앱 생성 → Admin API scope에 `write_products`(+ `read_products`) 부여.
3. 발급된 Admin API access token을 `.env`의 `SHOPIFY_STORE_DOMAIN`,
   `SHOPIFY_ADMIN_API_TOKEN`으로 저장.
4. 업로드할 `products.csv`가 Shopify 표준 스키마(예: `Handle`, `Title`, `Body (HTML)`,
   `Vendor`, `Variant SKU`, `Variant Price`, `Variant Inventory Qty` 등)를 따르는지
   확인.
5. 구현 방식 선택:
   - 소량(수십~수백 건): REST Admin API `POST /admin/api/{version}/products.json`을
     품목마다 반복 호출.
   - 대량: GraphQL Admin API의 `bulkOperationRunMutation` + staged upload를 권장
     (Shopify가 대량 CSV 임포트에 이 방식을 공식 권장함).
6. 검증: 스토어 관리자 화면의 Products 목록에서 업로드분 확인, 또는 API로 방금 만든
   상품을 다시 `GET`해 필드 일치 여부 확인.

### 참고
- [Shopify Admin API 문서](https://shopify.dev/docs/api/admin-rest)

## 2) Stripe 테스트 결제 시나리오 자동화

### 필요한 것
- Stripe 계정 (Test mode는 기본 제공, 별도 신청 불필요)
- Test Secret Key (`sk_test_...`) — **`sk_live_...`는 이 작업에서 절대 사용하지
  않습니다.**

### 절차
1. Stripe Dashboard 우측 상단 **Test mode** 토글이 켜져 있는지 확인.
2. **Developers → API keys**에서 Test Secret Key 발급 → `.env`의
   `STRIPE_SECRET_KEY`(`sk_test_`로 시작하는지 반드시 확인)로 저장.
3. 결제 생성 시나리오: `stripe.PaymentIntent.create(...)`로 PaymentIntent를 만들고,
   [Stripe 공식 테스트 카드](https://stripe.com/docs/testing)(예: `4242 4242 4242
   4242`, 임의의 미래 만료일/CVC)로 confirm.
4. 환불 시나리오: `stripe.Refund.create(payment_intent=<id>)` 호출.
5. 실패/거절 시나리오도 함께 다루고 싶다면 Stripe가 제공하는 거절 전용 테스트 카드
   (예: `4000 0000 0000 0002`)로 결제 실패 처리 경로도 검증.
6. 검증: Stripe Dashboard의 **Payments** 탭에서 테스트 결제/환불 내역 확인, 또는 API로
   `stripe.PaymentIntent.list(...)`/`stripe.Refund.list(...)` 재조회.

### 참고
- [Stripe 테스트 카드 목록](https://stripe.com/docs/testing)
- [Stripe API Keys 관리](https://dashboard.stripe.com/test/apikeys)

## 3) 샘플 주문 삽입 스크립트 (선택적)

### 목적
리포트/분석 로직(매출 집계, 재고 반영 등)을 검증하기 위해 테스트 환경에 샘플 주문
데이터를 채워 넣습니다.

### 옵션 A — Shopify Order API
Development Store에서는 실제 결제 없이 주문 레코드만 만들 수 있습니다. Admin API
`POST /admin/api/{version}/orders.json`으로 샘플 주문을 생성합니다(품목은 1번에서
업로드한 상품 참조).

### 옵션 B — 이 프로젝트의 Mock POS 재사용 (권장)
Shopify 계정/키가 없어도 지금 바로 테스트할 수 있는 더 간단한 방법입니다. 이 저장소의
`mock-pos/`가 이미 동일한 목적(주문 생성 → 결제 → 재고 반영)의 REST API를 제공합니다.

```bash
# mock-pos/README.md 참고
curl -s -X POST "$BASE/v1/stores/$STORE/orders" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"line_items":[{"item_id":"menu_americano","quantity":2}]}'
```

**권장 순서**: 먼저 옵션 B(Mock POS)로 리포트/분석 로직을 검증하고, Shopify 연동이
실제로 필요해지는 시점에만 옵션 A로 전환하는 것을 권장합니다 — 키 발급을 기다릴 필요
없이 지금 바로 시작할 수 있습니다.

## 준비 체크리스트

- [ ] Shopify Partner 계정 생성
- [ ] Shopify Development Store 생성
- [ ] Shopify Custom App 생성 + Admin API 토큰 발급 (`write_products`, 필요 시
      `write_orders`)
- [ ] Stripe 계정 생성 (Test mode 확인)
- [ ] Stripe Test Secret Key(`sk_test_...`) 발급
- [ ] `.env`에 `SHOPIFY_STORE_DOMAIN`, `SHOPIFY_ADMIN_API_TOKEN`, `STRIPE_SECRET_KEY`
      저장, `.gitignore`로 커밋 제외 확인
- [ ] `products.csv` 스키마 확정
- [ ] Stripe 공식 테스트 카드 번호 확보

## 다음 단계

API 키가 준비되면 위 절차대로 스크립트를 구현·실행하고, 이 문서의 "검증" 단계로 결과를
확인합니다. TriAgent_SMB와의 실제 연동 여부(Hermes 프로필의 Skill로 노출할지, 또는
독립 도구로만 둘지)는 키 확보 이후 별도로 결정합니다.
