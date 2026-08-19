---
name: pos-stock-and-reorder
description: "Mock POS 재고를 조회하고 임계치 이하 품목에 대해 발주를 제안·요청한다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, pos, inventory]
platforms: [Linux, macOS, Windows]
---

## 사용 시점
"재고 얼마나 남았어?", "발주해야 할 것 같은데" 같은 재고 관련 요청을 받았을 때.

## 접속 정보 (2026-08-19 실측 — 반드시 이대로 할 것)
`code_execution` 샌드박스는 이 프로필의 `.env`를 상속하지 않는다. **환경변수
(`os.environ`)로 접속 정보를 조회하려 하지 말고, 아래 값을 코드에 리터럴로 직접 써서
바로 호출한다** — 이 값이 실제 배포 값이며, Mock POS API Key는 개발용 고정 키(실제
비밀값 아님)라 하드코딩해도 안전하다:
```python
BASE_URL = "http://mock-pos:8080"
API_KEY = "dev-key"
STORE_ID = "store_demo"
HEADERS = {"X-API-Key": API_KEY}
```
`requests`가 없으면 `urllib.request`로 대체해도 된다. 참고용으로
`scripts/pos_stock_and_reorder.py`에 `list_inventory`/`get_inventory_item`/
`adjust_inventory`/`find_low_stock_items` 함수가 구현되어 있다(실제 mock-pos 서버로
검증됨) — 시간을 아끼려면 이 파일을 읽어 그대로 실행해도 된다.

## 절차
1. `GET /v1/stores/{STORE_ID}/inventory` 또는 `GET /v1/stores/{STORE_ID}/inventory/
   {item_id}`를 조회한다.
2. 재고가 임계치(기본 5개, `USER.md`에서 매장별 조정) 이하이면 먼저 경고하고 발주 여부를
   묻는다.
3. 발주 확정 시 예상 금액이 `USER.md`의 임계치를 넘으면 coordinator에게 게이트 2(대량 발주)
   승인을 요청한다. 임계치 이하 소액 발주는 즉시 진행하고
   `POST /v1/stores/{STORE_ID}/inventory/{item_id}/adjust`(양수 `delta`)로 입고를
   반영한다.
4. `workspace/inventory/<날짜>.md`에 재고 현황과 발주 이력을 기록한다.

## 반환값
- 현재 재고 수준
- 발주 필요 여부
- (해당 시) HITL 게이트 요청 여부
