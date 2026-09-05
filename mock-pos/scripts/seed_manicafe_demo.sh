#!/usr/bin/env bash
# 마니카페 연남점 데모용 풀 시드 스크립트 — 12개 메뉴 + 재고 + 고객 6명 + 주문/결제
# 20여 건 + 환불 2건까지 심어서, 웹앱 대시보드(정산/원가·마진/인기메뉴/재고/재방문고객)의
# 모든 카드가 실제 데이터로 채워지게 한다.
#
# mock-pos는 인메모리 저장소라 컨테이너를 재시작하면 초기화되므로, 데모 세션마다
# 다시 실행하면 된다(멱등적이지 않음 — 재시작 없이 두 번 실행하면 카탈로그 409로
# 조용히 실패한다. 재실행 전엔 `docker compose restart mock-pos`로 초기화할 것).
#
# 사용법: mock-pos 컨테이너가 떠 있는 상태에서
#   cd mock-pos/scripts && ./seed_manicafe_demo.sh
#
# 참고: mock-pos의 Order.created_at은 항상 "지금"으로 기록되고 API로 과거 날짜를
# 지정할 수 없다 — 그래서 "매출 추이(최근 7일)" 차트는 오늘 하루에만 데이터가
# 몰려서 보인다. 이건 mock-pos 자체의 알려진 제약이며 이 스크립트가 고칠 수 있는
# 부분이 아니다(docs/14-webapp-users-guide.md 참고).
set -euo pipefail

BASE="${MOCK_POS_BASE_URL:-http://localhost:8080}"
KEY="${MOCK_POS_API_KEY:-dev-key}"
STORE="${MOCK_POS_STORE_ID:-store_demo}"

api() {
  # 본문은 임시 파일을 거쳐 --data-binary로 전달한다(-d로 직접 넘기면 Git Bash +
  # 네이티브 curl.exe 조합에서 한글 등 비ASCII 인자가 깨지는 경우가 있음).
  if [ -n "${3:-}" ]; then
    local tmp
    tmp=$(mktemp)
    printf '%s' "$3" > "$tmp"
    curl -sSf -X "$1" "$BASE/v1/stores/$STORE$2" \
      -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
      --data-binary "@$tmp"
    rm -f "$tmp"
  else
    curl -sSf -X "$1" "$BASE/v1/stores/$STORE$2" \
      -H "X-API-Key: $KEY" -H "Content-Type: application/json"
  fi
}

order_and_pay() {
  # $1: line_items JSON 배열, $2: customer_id
  local order_id
  order_id=$(api POST /orders "{\"line_items\":$1,\"customer_id\":\"$2\"}" \
    | python3 -c "import sys,json;print(json.load(sys.stdin)['order_id'])")
  api POST /payments "{\"order_id\":\"$order_id\"}" > /dev/null
  echo "$order_id"
}

echo "== 카탈로그 등록 (마니카페 연남점 메뉴 12종) =="
# 아메리카노는 initial_stock=0으로 등록 — "재고 파악/주문관리" 화면에서
# inventory-agent가 재고부족을 바로 확인할 수 있게 한다.
api POST /catalog/items '{"item_id":"menu_americano","name":"아메리카노","unit_price":3500,"cost":800,"category":"coffee","initial_stock":0,"low_stock_threshold":5}' > /dev/null
api POST /catalog/items '{"item_id":"menu_latte","name":"라떼","unit_price":4500,"cost":1000,"category":"coffee","initial_stock":45,"low_stock_threshold":10}' > /dev/null
api POST /catalog/items '{"item_id":"menu_cappuccino","name":"카푸치노","unit_price":4700,"cost":1100,"category":"coffee","initial_stock":38,"low_stock_threshold":10}' > /dev/null
api POST /catalog/items '{"item_id":"menu_espresso","name":"에스프레소","unit_price":3000,"cost":700,"category":"coffee","initial_stock":60,"low_stock_threshold":10}' > /dev/null
api POST /catalog/items '{"item_id":"menu_coldbrew","name":"콜드브루","unit_price":5200,"cost":1200,"category":"coffee","initial_stock":30,"low_stock_threshold":8}' > /dev/null
api POST /catalog/items '{"item_id":"menu_matcha_latte","name":"말차라떼","unit_price":5200,"cost":1200,"category":"tea","initial_stock":25,"low_stock_threshold":8}' > /dev/null
api POST /catalog/items '{"item_id":"menu_chai_latte","name":"차이라떼","unit_price":4800,"cost":1100,"category":"tea","initial_stock":22,"low_stock_threshold":8}' > /dev/null
api POST /catalog/items '{"item_id":"menu_muffin","name":"블루베리 머핀","unit_price":2800,"cost":500,"category":"bakery","initial_stock":18,"low_stock_threshold":10}' > /dev/null
api POST /catalog/items '{"item_id":"menu_croissant","name":"크루아상","unit_price":3000,"cost":600,"category":"bakery","initial_stock":16,"low_stock_threshold":10}' > /dev/null
api POST /catalog/items '{"item_id":"menu_sandwich","name":"햄&치즈 샌드위치","unit_price":6500,"cost":1800,"category":"sandwich","initial_stock":12,"low_stock_threshold":5}' > /dev/null
api POST /catalog/items '{"item_id":"menu_smoothie","name":"딸기 스무디","unit_price":5500,"cost":1300,"category":"smoothie","initial_stock":14,"low_stock_threshold":6}' > /dev/null
api POST /catalog/items '{"item_id":"menu_cake","name":"시즌 케이크(딸기)","unit_price":6000,"cost":2000,"category":"dessert","initial_stock":9,"low_stock_threshold":5}' > /dev/null

echo "== 고객 등록 (6명) =="
api POST /customers '{"customer_id":"cust_minji","name":"김민지","phone":"010-1234-5678"}' > /dev/null
api POST /customers '{"customer_id":"cust_junho","name":"이준호","phone":"010-2345-6789"}' > /dev/null
api POST /customers '{"customer_id":"cust_soyeon","name":"박소연","phone":"010-3456-7890"}' > /dev/null
api POST /customers '{"customer_id":"cust_donghyun","name":"최동현","phone":"010-4567-8901"}' > /dev/null
api POST /customers '{"customer_id":"cust_yuna","name":"정유나","phone":"010-5678-9012"}' > /dev/null
api POST /customers '{"customer_id":"cust_taemin","name":"강태민","phone":"010-6789-0123"}' > /dev/null

echo "== 주문/결제 생성 (인기 메뉴·재방문 고객·정산 데이터를 위해 다양하게) =="
order_and_pay '[{"item_id":"menu_latte","quantity":2}]' cust_minji
order_and_pay '[{"item_id":"menu_cappuccino","quantity":1},{"item_id":"menu_muffin","quantity":1}]' cust_minji
order_and_pay '[{"item_id":"menu_latte","quantity":1}]' cust_minji
order_and_pay '[{"item_id":"menu_cappuccino","quantity":1}]' cust_minji
order_and_pay '[{"item_id":"menu_coldbrew","quantity":1}]' cust_junho
order_and_pay '[{"item_id":"menu_croissant","quantity":2}]' cust_junho
order_and_pay '[{"item_id":"menu_matcha_latte","quantity":1},{"item_id":"menu_cake","quantity":1}]' cust_soyeon
order_and_pay '[{"item_id":"menu_latte","quantity":1},{"item_id":"menu_muffin","quantity":1}]' cust_soyeon
order_and_pay '[{"item_id":"menu_sandwich","quantity":1},{"item_id":"menu_smoothie","quantity":1}]' cust_donghyun
order_and_pay '[{"item_id":"menu_espresso","quantity":2}]' cust_donghyun
order_and_pay '[{"item_id":"menu_chai_latte","quantity":1}]' cust_yuna
order_and_pay '[{"item_id":"menu_latte","quantity":3}]' cust_yuna
order_and_pay '[{"item_id":"menu_cappuccino","quantity":2}]' cust_taemin
order_and_pay '[{"item_id":"menu_muffin","quantity":2},{"item_id":"menu_croissant","quantity":1}]' cust_taemin
order_and_pay '[{"item_id":"menu_smoothie","quantity":1}]' cust_minji
order_and_pay '[{"item_id":"menu_latte","quantity":1}]' cust_junho
order_and_pay '[{"item_id":"menu_cake","quantity":1}]' cust_soyeon
order_and_pay '[{"item_id":"menu_coldbrew","quantity":2}]' cust_yuna
order_and_pay '[{"item_id":"menu_cappuccino","quantity":1},{"item_id":"menu_sandwich","quantity":1}]' cust_taemin
order_and_pay '[{"item_id":"menu_matcha_latte","quantity":1}]' cust_donghyun
order_and_pay '[{"item_id":"menu_muffin","quantity":1}]' cust_minji
echo "  주문/결제 20건 완료"

echo "== 환불 데모 (전액 1건 + 부분 1건) =="
order_id=$(api POST /orders '{"line_items":[{"item_id":"menu_croissant","quantity":1}],"customer_id":"cust_junho"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['order_id'])")
payment_id=$(api POST /payments "{\"order_id\":\"$order_id\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['payment_id'])")
api POST "/payments/$payment_id/refund" '{"reason":"고객 단순 변심"}' > /dev/null
echo "  전액환불 완료: $payment_id"

order_id=$(api POST /orders '{"line_items":[{"item_id":"menu_cake","quantity":1}],"customer_id":"cust_soyeon"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['order_id'])")
payment_id=$(api POST /payments "{\"order_id\":\"$order_id\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['payment_id'])")
api POST "/payments/$payment_id/refund" '{"amount":2000,"reason":"케이크 일부 파손"}' > /dev/null
echo "  부분환불 완료: $payment_id (2,000원)"

echo "== 완료 =="
echo "확인: curl -s -H \"X-API-Key: $KEY\" \"$BASE/v1/stores/$STORE/inventory/menu_americano\""
echo "     -> stock_quantity가 0이어야 '재고 파악 및 주문' 장면이 의도대로 나옵니다."
echo "확인: curl -s -H \"X-API-Key: $KEY\" \"$BASE/v1/stores/$STORE/reports/top-items?period=today&limit=5\""
