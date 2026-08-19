mani cafe — 샌드박스(Usecase) 테스트 설정 및 실행 가이드

파일 위치 요약
- mani cafe 테스트 플랜: .hermes/plans/2026-08-19_140928-mani-cafe-usecase-test-plan.md
- 테스트 데이터: manicafe/test-data/
  - products.csv
  - sample_orders.csv

빠른 시작
1) Shopify dev-store 생성
   - Shopify Partner 계정에서 "Create development store" 클릭
   - 스토어 세팅에서 결제/지역/통화 확인

2) 상품 업로드
   - Shopify Admin > Products > Import
   - manicafe/test-data/products.csv 업로드 후 필드 매핑 확인

3) 결제 테스트(Stripe)
   - Stripe 계정 > Developers > API keys에서 테스트 키 확인
   - Shopify에서 외부 결제 게이트웨이(Stripe) 연동(테스트 키 사용)
   - 테스트 카드: 4242 4242 4242 4242 등 Stripe 테스트 카드 사용

4) 샘플 주문(수동 또는 자동)
   - 수동: 스토어 프론트에서 상품을 주문
   - 자동: sample_orders.csv를 참조해 주문 생성 스크립트(사용자 환경에 맞춰 구현)

5) 체크리스트 실행
   - .hermes/plans/2026-08-19_140928-mani-cafe-usecase-test-plan.md의 테스트 케이스를 따름

문제 발견 시 기록 방식
- 발견된 이슈: 제목, 재현 단계, 기대 결과, 실제 결과, 스크린샷/로그(가능 시)
- 우선순위: P0(블로킹) / P1(주요) / P2(완화 가능)

다음(옵션)
- 자동화: Shopify Admin API + Stripe API를 사용한 주문 생성 스크립트 제공 가능(원하시면 제가 템플릿 스크립트를 작성해 드립니다).
- POS 연동 테스트가 필요하면 사용중인 POS 이름을 알려주세요. 해당 POS의 sandbox 가이드에 맞춰 추가 설정 가이드를 만들어 드립니다.

보안 주의
- API 키/토큰은 절대 이 저장소에 커밋하지 마세요.
- 테스트 중 실제 결제가 발생하면(라이브 키 사용 시) 즉시 거래를 취소하고 라이브 키를 교체하세요.

원하시면 다음 작업을 진행하겠습니다:
- (A) Shopify Admin API + Stripe를 이용한 주문 자동화 스크립트(파이썬) 템플릿 작성
- (B) 테스트 케이스 실행표(구글 시트/CSV) 생성
- (C) POS 벤더별 sandbox 세팅 가이드 작성

원하시는 항목(A/B/C)을 알려주세요.