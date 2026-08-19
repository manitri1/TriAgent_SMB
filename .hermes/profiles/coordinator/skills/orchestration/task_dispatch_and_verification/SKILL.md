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
4. 프로모션 집행 / 대량 발주 확정 / 환불·취소 처리 — 이 3개 HITL 게이트에 도달하면
   `messaging`/`clarify`로 사장님에게 검토를 요청하고, 명시적 승인 없이는 진행하지 않는다.
5. "오늘 브리핑" 같은 종합 요청은 `sales-analytics-agent`와 `inventory-agent`를 순서대로
   호출해 결과를 종합한 뒤 간결하게 보고한다.

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
