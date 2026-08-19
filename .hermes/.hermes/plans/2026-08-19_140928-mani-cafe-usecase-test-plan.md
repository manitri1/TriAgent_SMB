# mani cafe — Usecase 테스트 계획

생성일: 2026-08-19 14:09:28
작성자: Hermes Agent

목표
- mani cafe(샌드박스)에서 Usecase에 적힌 주요 기능(주문/결제/환불/리포트/재고/멤버십)을 검증할 수 있도록 필요한 산출물(설정 가이드, CSV 템플릿, 테스트 케이스)을 준비한다.

산출물(이 작업에서 생성됨)
- .hermes/plans/2026-08-19_140928-mani-cafe-usecase-test-plan.md (이 파일)
- ./manicafe/test-data/products.csv (상품 업로드 템플릿, 12개 샘플)
- ./manicafe/test-data/sample_orders.csv (샘플 주문/환불 데이터, 30건 예시)
- ./manicafe/README_TEST_SETUP.md (샌드박스 세팅·실행 가이드)

전제·가정
- 우선 Shopify dev-store + Stripe 테스트 모드 + 로컬 CSV 업로드 시나리오를 기준으로 한다.
- 실제 결제(실거래)는 하지 않으며 Stripe/Shopify의 테스트 모드를 사용해 시뮬레이션한다.
- API 토큰·상점 연결 등 민감정보는 사용자가 별도로 입력한다.

우선순위 테스트 범위 (MVP)
1) 결제 흐름: 결제 승인, 결제 실패, 부분 환불, 전체 환불
2) 주문 흐름: 주문 생성 → 상태 변경(준비/픽업/배송) → 취소/환불
3) 재고: SKU별 재고감소, 재고부족 시 경고/주문 차단
4) 리포트: 기간별 총매출, 카테고리별 매출, 환불 차감 전/후 매출
5) 멤버십/할인: 쿠폰 적용, 포인트 또는 할인 코드 중복 처리
6) POS 연동 시나리오(선택): 오프라인 주문 동기화 테스트

샌드박스 세팅 개요 (빠른 가이드)
- Shopify
  1. Shopify Partner 계정 생성 → 개발용 dev-store 생성
  2. Products 메뉴에서 CSV 업로드(또는 Admin API)로 products.csv 업로드
  3. 결제는 테스트용 결제 게이트웨이(Shopify Payments 테스트 모드) 또는 Stripe 연동(테스트 키)
  4. 앱/웹훅(필요 시) 설정: 주문 생성/변경 이벤트 수신

- Stripe
  1. Stripe 계정 생성 → Developers > API keys에서 테스트 키 사용
  2. 결제 테스트 카드(예: 4242 4242 4242 4242)로 결제 시나리오 실행
  3. Webhook(예: payment_intent.succeeded) 테스트 엔드포인트 등록(ngrok 필요 시 사용)

- POS/오프라인(선택)
  - 사용하려는 POS 벤더의 ‘sandbox’/test mode 문서에 따라 로케이션 생성 및 주문 동기화 테스트

테스트 데이터
- 경로: ./manicafe/test-data/
  - products.csv
  - sample_orders.csv

테스트 케이스 체크리스트 (우선순위)
- [ ] 결제 승인(정상 카드) - 주문 상태: paid
- [ ] 결제 실패(카드 거부) - 주문 생성/결제 실패 후 주문 보류 또는 취소
- [ ] 부분 환불 - 환불금액만큼 재무 리포트 반영
- [ ] 전체 환불 - 주문 상태: refunded, 재고 복원(상품 정책에 따라)
- [ ] 주문 취소(결제 전) - 재고 복원, 알림
- [ ] 쿠폰/할인 적용(중복 방지) - 할인 계산 로직 검증
- [ ] 재고 부족 주문 차단 - 재고가 없을 때 주문 불가
- [ ] 리포트: 기간별 총매출(환불 전/후) 비교
- [ ] 리포트: 상품/카테고리별 매출 추출
- [ ] 멤버십 포인트 적립/사용(있을 경우) - 적립/차감 검증

운영 전환 체크포인트
- 고객·주문 데이터(이메일/포인트/주문 히스토리) 마이그레이션 전략 수립
- 세무·회계 기록 보존: 주문·환불 관련 원장 보관 방식 합의
- 재고 SKU 정합성 확인(공유 SKU vs 개별 SKU)

다음 단계(권장 실행 흐름)
1. Shopify dev-store 생성(사용자 수행) — 인증 정보 준비
2. CSV 업로드(./manicafe/test-data/products.csv)
3. Stripe 테스트 키 연결, 결제 플로우 시나리오 실행(샘플 주문 불러오기)
4. 테스트 케이스 체크리스트를 따라 시나리오 실행 및 결과 기록
5. 문제 발견 시 재현 스크립트(샘플 주문 CSV -> API) 작성

파일 위치(생성됨)
- .hermes/plans/2026-08-19_140928-mani-cafe-usecase-test-plan.md
- ./manicafe/test-data/products.csv
- ./manicafe/test-data/sample_orders.csv
- ./manicafe/README_TEST_SETUP.md

문의: 실제 Shopify/Stripe 연동(토큰 입력 등)을 제가 대신 실행하길 원하시면, 필요한 인증 정보와 명확한 범위를 알려주세요(보안상 토큰은 직접 입력하셔야 합니다).