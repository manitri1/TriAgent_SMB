# 02. 아키텍처 — 프로필 관계와 오케스트레이션

## 프로필 관계도

```
                                    사장님/직원(Discord)
                                         │
                                         ▼
                              ┌───────────────────┐
                              │    coordinator     │  ← 유일한 대화 진입점
                              │  (총괄 코디네이터)   │
                              └─────────┬─────────┘
                                        │ terminal(hermes -p <role> chat -q "...") 동기 호출
     ┌───────────┬───────────┬─────────┼─────────┬───────────┐
     ▼           ▼           ▼         ▼         ▼           ▼
order-      inventory-  reservation- customer- sales-      marketing-
payment-    agent       agent        service-  analytics-  crm-agent
agent       (재고)      (예약)       agent     agent       (마케팅/CRM)
(주문/결제)              (고객응대)   (매출분석)
     │           │           │         │         │           │
     └───────────┴───────────┴─────────┴─────────┴───────────┘
                                        │
                              산출물 반환 (파일 경로 / 요약)
                                        │
                                        ▼
                              coordinator: Active Verification
                              (Mock POS 재조회 / 파일 직접 열람)
                                        │
                              HITL 게이트 대상이면 ↓
                                        ▼
                              🛑 사장님 승인 (Discord)
```

`coordinator`가 유일한 대화 진입점이며, 나머지 6개는 `coordinator`가 위임할 때만 구동되는
실행 전문 프로필입니다(총 7개 프로필). 실행 프로필 사이에는 직접적인 프로필 간 호출이
없습니다 — 모든 조정은 `coordinator`를 거칩니다(중앙집중형 오케스트레이션).

`docs/agents.md`(구버전)에 있던 "사장님 비서(운영) 에이전트"는 별도 프로필로 두지 않고
`coordinator`가 직접 흡수합니다 — 하위 프로필 호출 결과를 종합해 "오늘 브리핑" 같은 보고를
만드는 것도 결국 coordinator 본연의 역할(위임 + 검증 + 보고)이기 때문입니다.

## 왜 외부 파이썬 오케스트레이터를 만들지 않는가

`hermes-core/`(폐기됨)처럼 OpenAI 함수콜 루프와 라우팅 로직을 파이썬으로 직접 짜는 대신,
이 프로젝트는 사장님의 요청이 비선형적이고 대화형이라는 특성에 맞춰 **`coordinator` 프로필
안의 LLM 스스로가** 어떤 하위 프로필에 무엇을 위임할지 판단하게 합니다. 이 판단은
`coordinator`의 SOUL.md 원칙(요청을 하위 태스크로 분해 → 담당 프로필 판단 → 위임 → 검증)으로
유도합니다.

## 위임 메커니즘: `terminal` 동기 호출 (`delegate_task` 아님)

Hermes Agent에는 서브에이전트 위임용 내장 툴 `delegate_task`가 있지만, 형제 프로젝트
`TriAgent_Planner`/`TriAgent_MICE`에서 실측한 결과 **`delegate_task`는 대상 프로필의
SOUL.md/USER.md/MEMORY.md/skills를 전혀 로드하지 않고, 같은 세션 안에서 이름 없는 범용
서브에이전트를 띄우는 함정**임이 확인되었습니다. 이 프로젝트는 처음부터 이 함정을 피해 다음
방식을 채택합니다:

```
terminal(command='/opt/hermes/bin/hermes -p <role> chat -q "<위임 내용>"')
```

- **반드시 동기(foreground)로 실행합니다** — `background=true`로 실행하면 부모 프로세스가
  자식을 죽이는 문제가 있습니다.
- 절대경로(`/opt/hermes/bin/hermes`)를 사용합니다 — 컨테이너 내부 `PATH`에 하위 `hermes`
  호출이 없을 수 있기 때문입니다.
- 진행 상황은 `workspace/kanban/<날짜>-<슬러그>.md` 파일 카드로 사람이 볼 수 있게 병행
  기록합니다 — 카드에 `title`, `assignee`, `status`, `details`를 채웁니다.

> 이 결정은 `TriAgent_Planner`/`TriAgent_MICE`가 겪은 실제 시행착오(delegate_task → 문제
> 발견 → terminal로 교체 → 재검증)를 이 저장소에서 반복하지 않기 위해 설계 단계에서부터
> 확정한 것입니다.

**✅ 2026-08-19 실측 완료**: 이 저장소에서 실제로 `docker compose exec`로 `coordinator`가
`order-payment-agent`를 `terminal`로 위임하는 것을 검증했습니다. `delegate_task`가 아니라
정확히 이 `terminal` 명령을 사용했고, Mock POS에 실제 주문/결제가 생성됐습니다(독립적으로
mock-pos API 재조회로 확인). 다만 두 가지를 이번에 새로 발견했습니다:

1. **`terminal` 호출이 약 120초 후 타임아웃될 수 있습니다**(`exit 124`). 하위 프로필이
   code_execution/skill 로딩까지 하는 복잡한 작업이면 시간이 걸립니다. 타임아웃 후에도
   하위 프로필 프로세스는 백그라운드에서 계속 실행되어 결과를 완성했습니다(고아 프로세스로
   남지는 않음) — 그래서 coordinator는 타임아웃 응답만으로 실패를 단정하지 말고 반드시
   Active Verification(산출물 재확인)으로 실제 완료 여부를 판단해야 합니다. 실측에서
   coordinator는 실제로 이렇게 행동했습니다(타임아웃 후 검증 파일을 직접 열어 확인).
2. **`kanban` 네이티브 툴은 coordinator에서 로드되지 않습니다** — `hermes doctor`가
   "kanban은 dispatcher가 생성한 워커 전용"이라고 명시했고, 실제 대화에서도 coordinator는
   `kanban` 툴 대신 `workspace/kanban/*.md` 파일을 스스로 만들어 카드를 관리했습니다. 위
   설명은 이 실측 결과를 반영해 애초 설계("kanban 트래커")를 "파일 카드"로 수정한
   것입니다.

## 데이터 흐름

```
[사장님 요청: "아메리카노 2잔 주문 들어왔어" / "재고 얼마나 남았어?" / "오늘 매출 어때?"]
   │
   ▼
coordinator: 요청 분류 → 담당 프로필 판단
   │
   ├──▶ order-payment-agent: pos_order_and_payment
   │       (Mock POS에 주문/결제 생성 → workspace/orders/<date>/에 요약 기록)
   │
   ├──▶ inventory-agent: pos_stock_and_reorder
   │       (Mock POS 재고 조회, 임계치 이하 시 발주 요청 → workspace/inventory/)
   │       — order-payment-agent가 만든 주문이 결제 완료되면 자동 반영(Mock POS 사양)
   │
   ├──▶ reservation-agent: pos_reservation_management
   │       (Mock POS에 예약 생성/취소, 리마인더 발송 → workspace/reservations/)
   │
   ├──▶ customer-service-agent: faq_and_complaint
   │       (workspace/customer-service/faq.md 조회, 불만 접수 기록)
   │
   ├──▶ sales-analytics-agent: pos_sales_reporting
   │       (Mock POS 매출/정산 리포트 조회·요약 → workspace/sales/)
   │
   └──▶ marketing-crm-agent: promo_and_segment
           (홍보 문구 초안 작성 → workspace/marketing/, 실제 발송 전 HITL 게이트)
   │
   ▼
   ── 게이트 대상(프로모션 집행·대량 발주·환불/취소)이면 승인 후 진행 ──
   ▼
coordinator: Active Verification (Mock POS 재조회 또는 workspace 파일 직접 열람) → 사장님 보고
```

모든 산출물은 `workspace/{orders,inventory,reservations,customer-service,sales,marketing,
reports}/` 아래에 누적되며, 진행 상황은 `coordinator`의 `MEMORY.md`에서 추적합니다.

## 최소 권한 원칙

`coordinator`는 주문 생성·프로모션 발송 등 **구현 도구를 직접 실행하는 용도로 쓰지
않습니다** — 산출물 확인(Active Verification)을 위한 읽기 목적으로만 `file` 툴셋을 사용하고,
실제 작성/실행은 항상 하위 프로필에 위임합니다. 이는 Hermes CLI가 `file` 툴셋을 read/write로
세분화해서 끌 수 없기 때문에 **기술적 강제가 아니라 SOUL.md의 행동 규범으로 강제**합니다
(`marketing-crm-agent`가 "초안까지만" 원칙을 SOUL.md로 강제하는 것과 동일한 패턴).
