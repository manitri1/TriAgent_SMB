---
name: task-dispatch-and-verification
description: "사장님 요청을 하위 프로필에 배정하고, 완료 보고를 Active Verification으로 재확인한 뒤 HITL 게이트에서 승인을 받는다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, coordinator, orchestration, verification]
platforms: [Linux, macOS, Windows]
---

## 사용 시점
사장님의 자연어 요청(주문/재고/예약/CS/매출/마케팅 관련 문의나 지시)을 받아 하위 프로필에
작업을 위임·검증해야 할 때.

## 절차
1. 요청을 분류해 담당 프로필(`order-payment-agent`/`inventory-agent`/`reservation-agent`/
   `customer-service-agent`/`sales-analytics-agent`/`marketing-crm-agent`)을 정하고,
   `file` 툴셋으로 `workspace/kanban/<날짜>-<슬러그>.md`에 카드를 만든다(`title`,
   `assignee`, `status: todo`, `details`를 포함한 마크다운 — 아래 "카드 형식" 참고).
   **`kanban` 네이티브 툴은 coordinator에서 실제로 동작하지 않는다**(2026-08-19 실측:
   `hermes doctor`가 "kanban은 dispatcher가 생성한 워커에만 로드됨"이라고 표시했고,
   실제 호출 시도에서도 coordinator에는 제공되지 않았다) — 그래서 이 파일 기반 방식이
   임시가 아니라 **정식 카드 관리 방법**이다.
2. `terminal(command='/opt/hermes/bin/hermes -p <role> chat -q "..."')`로 동기 호출해
   실제로 위임한다(`delegate_task` 사용 금지). **주의(2026-08-19 실측): `terminal` 호출은
   약 120초 후 타임아웃(`exit 124`)될 수 있다** — 하위 프로필이 code_execution/skill
   로딩까지 하는 복잡한 작업이면 시간이 걸린다. 타임아웃이 나도 하위 프로필 프로세스가
   백그라운드에서 계속 실행되어 결과를 남길 수 있으므로, 타임아웃 응답만으로 실패
   단정하지 말고 3단계(Active Verification)로 실제 산출물이 생겼는지 반드시 재확인한다.
3. 카드를 `done`으로 옮기기 전, Mock POS를 재조회하거나 `workspace/` 산출물 파일을 직접
   열어 확인한다. 텍스트 보고만으로, 또는 `terminal` 타임아웃만으로 완료/실패를 단정하지
   않는다. 확인 불가하면 카드 상태를 `blocked`로 유지하고 근거를 재요청한다.
4. 프로모션 집행 / 대량 발주 확정 / 환불·취소 처리 — 이 3개 HITL 게이트에 도달하면 아래
   "구조화 승인 큐 연동" 절차대로 대시보드에도 대기 레코드를 만들고, 기존과 동일하게
   `messaging`/`clarify`로 사장님에게 검토를 요청한다. 두 채널(Discord 대화 / 대시보드
   웹 UI) 중 **먼저 도달한 결정**을 유효한 것으로 삼으며, 명시적 승인 없이는 진행하지 않는다.
5. "오늘 브리핑" 같은 종합 요청은 `sales-analytics-agent`와 `inventory-agent`를 순서대로
   호출해 결과를 종합한 뒤 간결하게 보고한다.

## 구조화 승인 큐 연동 (신규, docs/13-mvp-dashboard-design.md §5)

기존에는 HITL 승인 상태가 Discord 대화 안에만 존재하고 구조화된 저장소가 없었다. 이제
`smb-dashboard`(신규 서비스)가 승인 큐 REST API를 제공하므로, 게이트 도달 시 다음을 추가로
수행한다.

**접속 정보 (다른 pos 스킬과 동일한 이유로 하드코딩 — code_execution 샌드박스는 `.env`를
상속하지 않는다):**
```python
DASHBOARD_BASE_URL = "http://smb-dashboard:8652"
DASHBOARD_AUTH = ("owner", "smb-dashboard-dev-2026")  # 개발용 기본값, 운영 전 교체 필요
```

1. 게이트 도달 즉시 `POST {DASHBOARD_BASE_URL}/api/approvals`로 대기 레코드를 만든다:
   `{"type": "promo"|"reorder"|"refund", "summary": "<한 줄 요약>", "details": "<채널/금액/사유 등 전문>", "requested_by": "<담당 프로필명>"}`.
   응답의 `approval_id`를 기억해둔다.
2. 기존과 동일하게 Discord 메시지를 보내되, "웹 대시보드(승인 대기열 탭)에서도 승인/반려할
   수 있습니다"를 안내에 포함한다.
3. `clarify` 응답을 기다리는 동안, 주기적으로(예: 몇 차례) `GET {DASHBOARD_BASE_URL}/api/approvals/{approval_id}`를
   폴링해 `status`가 `pending`이 아니게 되었는지 확인한다. 웹에서 먼저 결정되면 그 결과를
   즉시 반영하고 Discord 대화는 "이미 대시보드에서 처리됨"으로 마무리한다.
4. Discord 대화로 먼저 결정된 경우에도, `PATCH {DASHBOARD_BASE_URL}/api/approvals/{approval_id}`
   (`{"status": "approved"|"rejected", "reason": "..."}`)로 대시보드 쪽 상태를 동기화한다.
   이미 결정된 레코드에 재차 PATCH를 시도하면 409가 반환되는데, 이는 오류가 아니라
   "이미 다른 채널에서 처리됨"을 뜻하므로 그대로 진행한다.
5. 최종 결정은 기존과 동일하게 `coordinator/MEMORY.md`의 "확정된 승인/반려 이력"에 한 줄
   남긴다.

## 카드 형식 (`workspace/kanban/<날짜>-<슬러그>.md`)
```markdown
title: <요청 요약>
assignee: <담당 프로필명>
status: todo | done | blocked
created: <날짜>
details:
  - <요청 세부사항>
verification:
  - verification_file: <확인한 산출물 경로>
  - <확인한 핵심 값>
```

## 반환값
- 배정된 카드 목록과 상태(`workspace/kanban/` 파일 경로)
- Active Verification 결과(검증 방법과 확인 여부)
- HITL 게이트 통과 여부(승인/반려/대기)
