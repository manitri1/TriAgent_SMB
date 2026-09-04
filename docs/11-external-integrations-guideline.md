# 11. 외부 연동 가이드라인 — Shopify / Stripe 테스트 자동화

이 문서는 아래 4개 작업을 실제로 구현하기 **전에** 필요한 준비물, 안전 원칙, 단계별
절차를 정리한 가이드라인입니다. 앞의 세 작업은 API 키/테스트 키가 필요하며 아직
확보되지 않았으므로, 이 문서 자체는 실행 코드가 아니라 **키가 준비된 뒤 바로 구현에
들어갈 수 있도록 하는 체크리스트**입니다. 4번은 키가 필요 없어 지금 바로 시작할 수
있습니다.

1. Shopify dev-store에 `products.csv` 자동 업로드 (Shopify Admin API 스크립트)
2. Stripe 테스트 결제 시나리오 자동화 (결제 생성/환불 스크립트)
3. 샘플 주문을 Shopify 또는 로컬 데모 DB에 삽입하는 스크립트 (테스트 모드, 선택적)
4. 글로벌 오픈스펙 Mock 서버 활용 (Square POS API 공식 OpenAPI 스펙 + Prism Mock
   도구로 계약/스키마 호환성 테스트, API 키 불필요)

## 이 프로젝트(TriAgent_SMB)와의 관계

현재 TriAgent_SMB는 `mock-pos/`(자체 FastAPI Mock POS)를 POS 시뮬레이터로 사용하고
있고, 실 벤더 연동 후보로는 국내 POS(토스플레이스/카카오페이)를 [07-roadmap.md](07-roadmap.md)
5번에 적어뒀습니다. Shopify/Stripe는 그것과는 별도의 이커머스/결제 플랫폼입니다 —
이 문서는 Shopify/Stripe 자체를 다루는 **독립적인 가이드라인**이며, TriAgent_SMB의
Hermes 프로필/Skill에 실제로 연결할지는 아직 결정된 바 없습니다. 연동하기로 결정되면
`docs/07-roadmap.md`에 별도 항목으로 추가하고, 해당 Skill의 REST 호출 대상만 교체하는
어댑터 방식(Mock POS를 다룰 때와 동일한 패턴)을 권장합니다.

4번(Square OpenAPI + Prism)은 성격이 다릅니다 — `mock-pos/`를 대체하는 게 아니라
**보완**하는 용도입니다.

| | `mock-pos/` (자체 구현) | Square OpenAPI + Prism (4번) |
|---|---|---|
| 무엇을 검증하나 | 실제 비즈니스 로직(주문→결제→재고차감→매출반영) | 요청/응답 스키마가 실제 업체 스펙과 호환되는가(계약 테스트) |
| 상태 유지 | 유지함(주문 후 재고가 실제로 줄어듦) | 유지 안 함(스펙의 example 값을 그대로 반환) |
| 용도 | 에이전트 Skill의 end-to-end 동작 검증(현재 주력) | 스키마 오독 버그 조기 발견(`docs/07-roadmap.md`에서 실제로 겪은 필드명 오독 버그 같은 것을 실 업체 스펙 기준으로도 미리 확인) |

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

> ⚠️ **2026-08-23 웹 조사로 갱신**: Shopify REST Admin API는 **2024-10-01부로
> legacy(레거시) 지정**되었고, 2025-10부터 일부 REST 엔드포인트(`products/count.json`
> 등)가 단계적으로 폐지(sunset)되기 시작해 **2026년에도 매년 추가 폐지 웨이브가
> 이어지는 중**입니다. 커스텀 앱이 변형(variant) 100개를 초과하는 상품을 다뤄야
> 한다면 REST 상품/변형 엔드포인트는 이미 GraphQL로 전면 이전이 요구된 상태입니다.
> **아래 절차는 원래 "소량은 REST, 대량은 GraphQL"로 작성돼 있었으나, 소량이라도
> 새로 자동화를 만든다면 지금은 GraphQL을 쓰는 것이 맞습니다** — REST 신규 사용은
> 권장하지 않습니다.

### 필요한 것
- Shopify Partner 계정 + Development Store (무료)
- Store 안에서 만든 Custom App의 Admin API access token, scope: `write_products`
  (쓰기 권한은 읽기 권한을 자동으로 포함하므로 `read_products`를 별도로 추가할
  필요는 없습니다 — Shopify 공식 문서 기준)

### 절차
1. [Shopify Partners](https://www.shopify.com/partners) 계정 생성 → Development
   Store 생성(테스트 전용, 실제 과금 없음).
2. 스토어 관리자 화면 → **Settings → Apps and sales channels → Develop apps** →
   커스텀 앱 생성 → Admin API scope에 `write_products` 부여.
3. 발급된 Admin API access token을 `.env`의 `SHOPIFY_STORE_DOMAIN`,
   `SHOPIFY_ADMIN_API_TOKEN`으로 저장.
4. 업로드할 `products.csv`가 Shopify 표준 스키마(예: `Handle`, `Title`, `Body (HTML)`,
   `Vendor`, `Variant SKU`, `Variant Price`, `Variant Inventory Qty` 등)를 따르는지
   확인. (참고: 자동화가 아니라 1회성 수동 업로드라면 Shopify 관리자 화면의
   **Products → Import** 네이티브 CSV 임포터가 이 스키마를 그대로 받아들이므로
   API/토큰 없이도 가능합니다 — 이 문서는 반복 가능한 자동화가 목적이므로 아래
   GraphQL 절차를 계속 다룹니다.)
5. 구현 방식 — **REST 대신 GraphQL Admin API 사용**:
   - 소량(수십~수백 건): 품목마다 `productCreate` 뮤테이션 호출(상품 + 첫 번째
     변형 생성) → 변형이 여러 개면 `productVariantsBulkCreate`로 추가 → **주의**:
     `productCreate`로 만든 상품은 기본적으로 미게시(unpublished) 상태이므로
     `publishablePublish` 호출까지 해야 스토어에 실제로 노출됩니다(REST 시절에는
     없던 단계이니 스크립트에서 누락하지 않도록 주의).
   - 대량: GraphQL Admin API의 `bulkOperationRunMutation` + `stagedUploadsCreate`
     (staged upload)를 사용합니다. 업로드 파일은 CSV가 아니라 **JSONL**이어야
     하고(한 줄에 뮤테이션 변수 하나, `mimeType: "text/jsonl"`) — `products.csv`를
     이 JSONL 형식으로 먼저 변환하는 단계가 필요합니다. API 버전 2026-01부터는
     매장당 동시 bulk mutation 작업을 최대 5개까지 허용합니다.
6. 검증: 스토어 관리자 화면의 Products 목록에서 업로드분 확인, 또는 API로 방금 만든
   상품을 다시 `GET`(GraphQL `product` 쿼리)해 필드 일치 여부 확인 — `productCreate`
   경로를 썼다면 게시 상태(published)까지 함께 확인.

### 참고
- [Shopify GraphQL Admin API — productCreate](https://shopify.dev/docs/api/admin-graphql/latest/mutations/productCreate)
- [Shopify — 대량 데이터 임포트(Bulk operations)](https://shopify.dev/docs/api/usage/bulk-operations/imports)
- [Shopify — REST API 폐지(Deprecated API calls)](https://shopify.dev/docs/api/admin-rest/latest/resources/deprecated-api-calls)
- [Shopify Access scopes 문서](https://shopify.dev/docs/api/usage/access-scopes) (`write_products`가 읽기 권한도 포함함을 확인)

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

## 4) 글로벌 오픈스펙 Mock 서버 활용 (Square OpenAPI + Prism)

### 목적
우리가 직접 설계한 `mock-pos/` 스키마가 아니라, 실제 글로벌 POS 업체(Square)가
공개한 공식 OpenAPI 스펙을 그대로 로드한 Mock 서버를 세워, 에이전트 Skill의 요청/응답
파싱이 **실 업체 스펙 기준으로도** 깨지지 않는지 계약(schema) 수준에서 확인합니다.
API 키·계정이 필요 없어 지금 바로 시작할 수 있습니다.

### 필요한 것
- Square 공식 OpenAPI 스펙 파일(계정/키 불필요, 공개 저장소에서 다운로드)
- Docker (이미 이 프로젝트에서 사용 중)
- `stoplight/prism` Docker 이미지

### 절차
1. Square 공식 저장소 [`square/connect-api-specification`](https://github.com/square/connect-api-specification)에서
   OpenAPI 스펙(`api.json`)을 다운로드하고, 재현성을 위해 커밋 해시나 태그로 버전을
   고정합니다.
2. Prism으로 스펙을 로드해 Mock 서버를 띄웁니다:
   ```bash
   docker run --init -p 4010:4010 stoplight/prism:4 mock -h 0.0.0.0 <다운로드한 api.json 경로 또는 URL>
   ```
   이 프로젝트의 `docker-compose.yml`에 서비스로 추가하는 것도 가능합니다 — 다만
   포트는 실제 구현 시점에 `docs/08-docker-deployment.md`의 조사 방법론(형제 프로젝트
   `docker ps` 재스캔)으로 다시 정합니다(이 문서 단계에서는 고정값을 정하지 않음).
3. Mock 서버의 주요 엔드포인트(Catalog 목록 조회, Order 생성, Payment 생성 등)를
   `code_execution`으로 호출하는 **스키마 호환성 스모크 테스트**를 작성합니다 —
   실제 비즈니스 검증이 아니라 "우리 Skill 코드가 Square의 실제 필드명/구조를 정확히
   파싱하는가"만 확인하는 목적임을 스크립트 주석에 명시합니다(`sales-analytics-agent`
   가 `order_count`를 매출로 잘못 읽었던 실측 버그 — `docs/07-roadmap.md` — 같은
   필드명 오독을 이 단계에서 조기에 잡아내는 것이 핵심 가치입니다).
4. 검증: Prism이 반환한 응답이 Square 공식 스펙의 스키마(필드명, 타입, 필수 여부)와
   일치하는지 확인. Prism 자체가 스펙 기반으로 응답을 생성하므로, 우리 파싱 코드가
   Prism 응답을 문제없이 처리하면 곧 Square 실 스펙과도 호환된다는 뜻입니다.

### 한계 (반드시 인지할 것)
Prism 응답은 스펙의 example 값을 그대로 반환하는 **무상태(stateless)** 목입니다.
"주문을 만들면 재고가 실제로 줄어든다" 같은 상태 변화는 재현되지 않습니다 — 이런
비즈니스 로직/흐름 검증은 계속 이 프로젝트의 `mock-pos/`가 담당합니다(위 표 참고).
상태 유지가 정말 필요해지면 WireMock 등 다른 도구로의 전환을 별도 검토합니다.

### 참고
- [Square 공식 OpenAPI 스펙 저장소](https://github.com/square/connect-api-specification)
- [Prism Docker 이미지](https://hub.docker.com/r/stoplight/prism)

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
- [ ] Square 공식 OpenAPI 스펙(`api.json`) 다운로드 및 버전(커밋 해시) 고정
- [ ] `stoplight/prism` 이미지 pull 확인 (`docker pull stoplight/prism:4`)

## 다음 단계

API 키가 준비되면 1~3번은 위 절차대로 스크립트를 구현·실행하고, 이 문서의 "검증"
단계로 결과를 확인합니다. 4번(Square OpenAPI + Prism)은 키가 필요 없으므로 바로 착수
가능하며, 실제로 구현하기로 결정되면 `docs/07-roadmap.md`에 별도 항목으로 옮겨
진행 상태를 추적하는 것을 권장합니다. TriAgent_SMB와의 실제 연동 여부(Hermes 프로필의
Skill로 노출할지, 또는 독립 도구로만 둘지)는 각 작업의 준비가 끝난 뒤 별도로
결정합니다.
