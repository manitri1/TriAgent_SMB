---
name: promo-and-segment
description: "트렌드를 조사해 홍보 문구 초안을 작성하고, 실제 집행 전 승인 절차를 안내한다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, marketing, crm]
platforms: [Linux, macOS, Windows]
---

## 사용 시점
프로모션/홍보 문구 작성 요청, 캠페인 아이디어 요청, 또는 "단골 고객 세그먼트 알려줘"
같은 재방문 고객 조회 요청을 받았을 때.

## 접속 정보 (Mock POS 고객 세그먼트 조회 시 — 반드시 이대로 할 것)
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
참고용으로 `scripts/pos_customer_segment.py`에 `get_repeat_customers` 함수가
구현되어 있다 — 시간을 아끼려면 이 파일을 읽어 그대로 실행해도 된다. 이 프로필은
Mock POS를 **읽기 전용(GET)**으로만 호출한다 — `messaging` 툴셋은 부여되어 있지
않으므로(게이트 1 유지) 이 절차로는 아무것도 발송할 수 없다.

## 절차
1. `web`/`search`로 트렌드·경쟁 매장 정보를 조사한다.
2. 매장 톤앤매너(`USER.md` 참고)에 맞춰 홍보 문구 초안을 작성하고, 반드시 "초안"임을
   명시한다.
3. `workspace/marketing/<날짜>.md`에 저장한다.
4. 유료 광고나 대량 발송 집행 의사가 확인되면 coordinator에게 게이트 1(프로모션 집행)
   승인이 필요함을 안내한다 — 이 프로필 자체는 발송하지 않는다.
5. "단골 고객 세그먼트" 같은 요청에는 `code_execution`으로
   `GET /v1/stores/{STORE_ID}/reports/repeat-customers?period=all&min_orders=2`를
   호출해 실제 결과를 그대로 보고한다. 결과가 비어 있으면 "현재 2회 이상 재구매한
   고객이 없다"고 있는 그대로 답한다 — 데이터가 없다고 추측하거나 지어내지 않는다.

## 반환값
- 홍보 문구 초안 (해당 시)
- 재방문 고객 목록 (해당 시)
- 산출물 파일 경로
- HITL 게이트 필요 여부
