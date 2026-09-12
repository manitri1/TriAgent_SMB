README: POS 주문/결제 스크립트 (2026-09-05)

파일 위치:
 - /opt/data/workspace/scripts/run_pos_order_2026-09-05.sh
 - 영수증 출력 디렉터리: /opt/data/workspace/orders/

설명:
 - 이 스크립트는 Mock POS(또는 실제 POS)가 REST API를 제공하는 환경에서
   아래 순서로 작업을 수행합니다:
   1) 카탈로그 조회(아메리카노 품목 탐색)
   2) 총액 확인(단가 x 수량)
   3) 주문 생성(POS에 order 생성)
   4) 카드 결제 요청
   5) 결제 승인 시 영수증 JSON을 /opt/data/workspace/orders/2026-09-05-order-<order_id>.json에 저장

사용 방법:
 1) 스크립트 편집: BASE_URL, API_KEY, STORE_ID 값을 귀하의 POS 환경에 맞게 수정하세요.
 2) 실행 권한 부여: chmod +x run_pos_order_2026-09-05.sh
 3) 실행: sudo bash ./run_pos_order_2026-09-05.sh
 4) 스크립트는 실행 중 사용자에게 최종 확인(y/n)을 요청합니다.

결과 확인:
 - 성공 시 터미널에 RESULT: order_id=... transaction_id=... receipt_path=/opt/data/workspace/orders/2026-09-05-order-<order_id>.json 형태로 출력됩니다.
 - Coordinator(저)가 영수증 JSON을 열어 확인하면 카드를 `done`으로 전환합니다.

주의:
 - 이 세션에서 제가 직접 원격 POS를 호출할 수 없는 제한 때문에, 안전하게 사용자가 직접 실행하도록 스크립트를 제공드립니다.
 - 실행 시 네트워크/방화벽/인증 정보가 필요합니다. API 키는 절대 이 채팅에 공유하지 마십시오.

원하시면 제가 이 스크립트를 더 간단한 curl-only 버전으로 줄 수도 있고, 실행 결과(콘솔 출력 또는 생성된 JSON 파일)를 붙여넣어 주시면 제가 파일 내용을 검증해 드립니다.
