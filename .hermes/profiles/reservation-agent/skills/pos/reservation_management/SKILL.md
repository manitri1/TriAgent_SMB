---
name: pos-reservation-management
description: "Mock POS에 예약을 생성·변경·취소하고 노쇼 방지 리마인더를 발송한다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, pos, reservation]
platforms: [Linux, macOS, Windows]
---

## 사용 시점
예약 생성/변경/취소 요청, 또는 예정된 예약의 리마인더를 보내야 할 때.

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
`scripts/pos_reservation_management.py`에 `create_reservation`/`get_reservation`/
`cancel_reservation`/`list_reservations` 함수가 구현되어 있다(실제 mock-pos 서버로
검증됨) — 시간을 아끼려면 이 파일을 읽어 그대로 실행해도 된다.

## 절차
1. 날짜·시간·고객 정보를 확인한 뒤 `POST /v1/stores/{STORE_ID}/reservations`
   (`customer_id`, `datetime`, `service?`, `note?`)를 호출한다.
2. 예약일 전 `messaging` 툴셋으로 Discord에 리마인더를 직접 발송한다(HITL 게이트 대상
   아님).
3. 취소/변경 요청은 `PATCH /v1/stores/{STORE_ID}/reservations/{id}`로 즉시 반영한다.
4. "오늘 예약 몇 건" 같은 질문에는 `GET /v1/stores/{STORE_ID}/reservations?date=&status=`
   로 목록을 조회해 답한다(coordinator의 브리핑 요청도 이 경로로 응답한다).
5. `workspace/reservations/<날짜>.md`에 예약 현황을 기록한다.

## 반환값
- 예약 결과(성공/실패)
- 리마인더 발송 여부
- 산출물 파일 경로
