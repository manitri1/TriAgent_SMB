#!/bin/bash
# run_pos_order_2026-09-05.sh
# Usage: edit BASE_URL, API_KEY, STORE_ID as needed, then run: sudo bash ./run_pos_order_2026-09-05.sh
# Creates receipt JSON at /opt/data/workspace/orders/2026-09-05-order-<order_id>.json

set -euo pipefail
BASE_URL="http://mock-pos:8080"   # <-- replace with your POS base URL
API_KEY="dev-key"                  # <-- REPLACE with your real X-API-Key
STORE_ID="store_demo"              # <-- replace with your store id
ITEM_KEYWORDS=("americano" "아메리카노")
QTY=2
DATE="2026-09-05"
OUTDIR="/opt/data/workspace/orders"
mkdir -p "$OUTDIR"

# 1) Fetch catalog
catalog_json=$(curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/v1/stores/$STORE_ID/catalog/items")
if [ -z "$catalog_json" ]; then
  echo "ERROR: 카탈로그를 불러오지 못했습니다. BASE_URL/API_KEY/STORE_ID를 확인하세요."
  exit 1
fi

# 2) Find americano item
item_json=$(python3 - <<PY
import sys, json
c = json.loads('''"""$catalog_json"""''')
for it in c:
    name = (it.get('name') or '').lower()
    if any(k in name for k in ["americano","아메리카노"]):
        print(json.dumps(it, ensure_ascii=False))
        sys.exit(0)
print('')
PY
)

if [ -z "$item_json" ]; then
  echo "ERROR: POS 카탈로그에서 아메리카노 품목을 찾을 수 없습니다. 카탈로그 샘플:"
  echo "$catalog_json" | head -c 4000
  exit 1
fi

# Extract fields
item_id=$(echo "$item_json" | python3 -c "import sys,json; j=json.load(sys.stdin); print(j.get('item_id') or j.get('id') or '')")
unit_price=$(echo "$item_json" | python3 -c "import sys,json; j=json.load(sys.stdin); print(j.get('price') or j.get('unit_price') or 0)")
currency=$(echo "$item_json" | python3 -c "import sys,json; j=json.load(sys.stdin); print(j.get('currency') or 'KRW')")

if [ -z "$item_id" ] || [ "$unit_price" = "0" ]; then
  echo "ERROR: 상품 정보 불충분: item_id=$item_id unit_price=$unit_price"
  exit 1
fi

total_amount=$(python3 - <<PY
print(float($unit_price) * $QTY)
PY
)

echo "단가: $unit_price $currency  수량: $QTY  총액: $total_amount $currency"
read -p "이대로 주문을 생성하고 결제 진행할까요? (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
  echo "사용자 취소: 주문을 생성하지 않습니다."
  exit 0
fi

# 3) Create order
order_payload=$(python3 - <<PY
import json
payload = {"line_items":[{"item_id": "$item_id", "quantity": $QTY}]}
print(json.dumps(payload))
PY
)

order_resp=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" -d "$order_payload" "$BASE_URL/v1/stores/$STORE_ID/orders")
http_code=$(echo "$order_resp" | tail -n1)
order_body=$(echo "$order_resp" | sed '$d')
if [ "$http_code" != "200" ] && [ "$http_code" != "201" ]; then
  echo "ERROR: 주문 생성 실패 ($http_code):"
  echo "$order_body"
  exit 1
fi
order_id=$(echo "$order_body" | python3 -c "import sys,json; j=json.load(sys.stdin); print(j.get('order_id') or j.get('id') or '')")
if [ -z "$order_id" ]; then
  echo "ERROR: 주문 생성 응답에 order_id가 없습니다:" 
  echo "$order_body"
  exit 1
fi

echo "주문 생성됨: order_id=$order_id  기대총액=$total_amount $currency"

# 4) Payment (CARD)
pay_payload=$(python3 - <<PY
import json
print(json.dumps({"order_id": "$order_id", "method":"CARD"}))
PY
)

pay_resp=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" -d "$pay_payload" "$BASE_URL/v1/stores/$STORE_ID/payments")
pay_code=$(echo "$pay_resp" | tail -n1)
pay_body=$(echo "$pay_resp" | sed '$d')
if [ "$pay_code" != "200" ] && [ "$pay_code" != "201" ]; then
  echo "PAYMENT_FAILED code=$pay_code"
  echo "$pay_body"
  exit 1
fi

transaction_id=$(echo "$pay_body" | python3 -c "import sys,json; j=json.load(sys.stdin); print(j.get('payment_id') or j.get('transaction_id') or j.get('id') or '')")
approved_amount=$(echo "$pay_body" | python3 -c "import sys,json; j=json.load(sys.stdin); print(j.get('amount') or j.get('approved_amount') or 0)")
timestamp=$(echo "$pay_body" | python3 -c "import sys,json; j=json.load(sys.stdin); print(j.get('timestamp') or j.get('created_at') or '')")
method=$(echo "$pay_body" | python3 -c "import sys,json; j=json.load(sys.stdin); print(j.get('method') or '')")

if [ -z "$transaction_id" ]; then
  echo "ERROR: 결제 응답에서 transaction_id를 찾을 수 없습니다. 응답 본문:" 
  echo "$pay_body"
  exit 1
fi

echo "결제 승인: transaction_id=$transaction_id 승인금액=$approved_amount $currency method=$method"

# 5) Save receipt JSON
receipt_path="$OUTDIR/$DATE-order-$order_id.json"
python3 - <<PY > "$receipt_path"
import json, sys
pay_body = json.loads('''"""$pay_body"""''') if '$pay_body' else {}
r = {
  "order_id": "$order_id",
  "transaction_id": "$transaction_id",
  "amount": float($approved_amount),
  "currency": "$currency",
  "timestamp": "$timestamp",
  "payment_method": "$method",
  "receipt_text": pay_body
}
json.dump(r, sys.stdout, ensure_ascii=False, indent=2)
PY

echo "영수증 저장됨: $receipt_path"
echo "RESULT: order_id=$order_id transaction_id=$transaction_id amount=$approved_amount receipt_path=$receipt_path"

exit 0
