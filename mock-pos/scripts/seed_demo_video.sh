#!/usr/bin/env bash
# 4분할 데모 영상 녹화 직전에 실행하는 시드 스크립트.
# mock-pos는 인메모리 저장소라 컨테이너를 재시작하면 초기화되므로, 녹화 세션마다
# 다시 실행하면 된다(멱등적이지 않음 — 재시작 없이 두 번 실행하면 카탈로그 409로
# 조용히 실패한다. 재실행 전엔 `docker compose restart mock-pos`로 초기화할 것).
#
# 사용법: mock-pos 컨테이너가 떠 있는 상태에서
#   cd mock-pos/scripts && ./seed_demo_video.sh
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

echo "== 카탈로그 등록 (.hermes/manicafe/test-data/products.csv 기준) =="
# 아메리카노는 initial_stock=0으로 등록 — "재고 파악 및 주문" 화면에서
# inventory-agent가 재고부족을 바로 확인할 수 있게 한다.
api POST /catalog/items '{"item_id":"menu_americano","name":"Americano","unit_price":3500,"cost":800,"category":"coffee","initial_stock":0,"low_stock_threshold":5}' > /dev/null
api POST /catalog/items '{"item_id":"menu_latte","name":"Latte","unit_price":4500,"cost":1000,"category":"coffee","initial_stock":147,"low_stock_threshold":10}' > /dev/null
api POST /catalog/items '{"item_id":"menu_cappuccino","name":"Cappuccino","unit_price":4700,"cost":1100,"category":"coffee","initial_stock":119,"low_stock_threshold":10}' > /dev/null
api POST /catalog/items '{"item_id":"menu_muffin","name":"Blueberry Muffin","unit_price":2800,"cost":500,"category":"bakery","initial_stock":54,"low_stock_threshold":10}' > /dev/null

echo "== 데모 고객 등록 =="
api POST /customers '{"customer_id":"cust_demo_01","name":"김민지","phone":"010-1234-5678"}' > /dev/null

echo "== 사전 주문/결제 생성 (대시보드 매출 추이 · 인기 메뉴 TOP5가 빈 화면이 아니게) =="
for line in \
  '[{"item_id":"menu_latte","quantity":2}]' \
  '[{"item_id":"menu_cappuccino","quantity":1}]' \
  '[{"item_id":"menu_muffin","quantity":3}]' \
  '[{"item_id":"menu_latte","quantity":1}]'
do
  order_id=$(api POST /orders "{\"line_items\":$line,\"customer_id\":\"cust_demo_01\"}" | python -c "import sys,json;print(json.load(sys.stdin)['order_id'])")
  api POST /payments "{\"order_id\":\"$order_id\"}" > /dev/null
  echo "  주문/결제 완료: $order_id"
done

echo "== 완료 =="
echo "확인: curl -s -H \"X-API-Key: $KEY\" \"$BASE/v1/stores/$STORE/inventory/menu_americano\""
echo "     -> stock_quantity가 0이어야 '재고 파악 및 주문' 장면이 의도대로 나옵니다."
