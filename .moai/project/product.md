# 제품

## 이름

**TriAgent_SMB** — 중소상공인(SMB)을 위한 AX(AI Transformation, AI 전환) 자동화 시스템.

## 설명

TriAgent_SMB는 에이전트형 코디네이터/워커 런타임([Nous Research Hermes Agent](https://github.com/NousResearch/hermes-agent) CLI 기반)과 모의(simulated) POS 백엔드, 그리고 전용 웹 대시보드를 결합하여 카페, 레스토랑, 미용실, 편의점 같은 소상공인의 일상 운영을 자동화한다. 단일 `coordinator` 에이전트가 사장님의 자연어 요청을 받아, 각각 독립된 Hermes Agent 프로필(고유한 페르소나·스킬·메모리를 가진)로 실행되는 6개의 전문 워커 에이전트(주문/결제, 재고, 예약, 고객 응대, 매출 분석, 마케팅/CRM)에 위임한다.

Hermes Agent는 POS 시스템에 대한 사전 지식이 없기 때문에, 이 프로젝트는 `mock-pos/`를 제공한다 — 에이전트들이 `code_execution` 스킬을 통해 호출하는, 실제 POS를 모사한 FastAPI REST 시뮬레이터(주문, 결제, 재고, 예약, 매출 리포트)다. 여기에 더해 `smb-dashboard/`(진행 중, SPEC-DASHBOARD-001)는 사장님이 채팅 인터페이스를 거치지 않고 동일한 데이터를 확인하고 조작할 수 있는 전용 웹 UI를 추가하며, 기존의 Discord 기반 승인 흐름과 나란히 동작하는 구조화된 승인 대기열도 함께 제공한다.

## 대상 사용자

주문/결제 처리, 재고 관리, 예약, 고객 응대, 매출 리포팅, 마케팅/CRM 자동화가 필요하지만 IT 인력이나 POS 벤더 통합 예산이 없는 소규모 단일 매장(카페, 레스토랑, 미용실, 편의점) 사장님과 직원. 주요 페르소나는 다수의 이해관계자로 구성된 조직이 아니라, 민감한 작업(프로모션, 대량 재주문, 환불)을 직접 승인하는 단일 의사결정자(사장님)다.

## 핵심 기능

### 에이전트 런타임 (`.hermes/`)
- **coordinator** — 유일한 대화형 진입점. `delegate_task`가 아닌 동기식 `terminal` 호출을 통해 워커에게 작업을 위임하고, 워커 출력에 대한 능동 검증(Active Verification)을 수행하며, 3개의 HITL(Human-In-The-Loop) 승인 게이트를 관리한다.
- **order-payment-agent** — 주문 접수, 결제 처리, 환불/취소 처리 (HITL 게이트 3).
- **inventory-agent** — 재고 추적 및 재주문 권고. 대량 재주문은 HITL 게이트 2가 필요하다.
- **reservation-agent** — 예약 생성/취소 (HITL 게이트 없음 — 고객이 직접 발생시키는 저위험 작업).
- **customer-service-agent** — 고객 문의 응대.
- **sales-analytics-agent** — 매출 리포팅 및 요약.
- **marketing-crm-agent** — 프로모션 문구 및 캠페인 초안 작성. 실행 시 HITL 게이트 1이 필요하다.

### 모의 POS 시뮬레이션 계층 (`mock-pos/`)
실제 POS 벤더(토스플레이스 / 카카오페이 급 통합은 아직 구축되지 않음)를 대신하는 FastAPI REST API로, `store_id` 단위로 범위가 지정된 주문, 결제(환불 포함), 재고, 예약, 매출 리포트를 제공한다. CORS를 지원하지 않으므로 호출자는 반드시 서버 사이드여야 하며, 이 때문에 대시보드 백엔드가 브라우저 대신 직접 이를 프록시한다.

### SMB 대시보드 (`smb-dashboard/`, 진행 중 — SPEC-DASHBOARD-001)
웹 UI(FastAPI 백엔드 + React/Vite 프론트엔드, 하나의 컨테이너에 정적 파일로 번들링)로, 사장님에게 다음을 하나의 화면에서 제공한다:
- **주문(Orders)** — 오늘의 주문을 상태 배지가 표시된 단일 테이블로 나열 (상태 필터는 아직 구현되지 않음. 상태 기반 필터링은 향후 로드맵 항목이며 docs/13 §4 참조)
- **재고(Inventory)** — 재고 수준과 저재고 강조 표시 (전역 `LOW_STOCK_THRESHOLD` 사용, 항목별 임계값은 아직 없음)
- **예약(Reservations)** — 날짜별 캘린더 형식 목록
- **매출 요약(Sales summary)** — 오늘/이번 주/이번 달 매출 및 주문 건수 위젯
- **승인(Approvals)** — 프로모션/재주문/환불에 대한 승인 대기 큐, 승인/거절 버튼 제공. 이 프로젝트 최초의 구조화된 HITL 영속 계층인 새 JSON 스토어(`data/approvals.json`)가 이를 뒷받침한다.

이는 기존 Discord 대화형 승인 흐름(docs/06)과 나란히 존재하는 **두 번째 병렬 HITL 채널**이다 — 두 채널 중 어느 쪽이든 먼저 승인을 처리한 쪽이 우선하며, 반대편은 `PATCH /api/approvals/{id}`를 통해 동기화된다.

## 현재 상태

- **검증된 동작 기준선(2026-08-19)**: `hermes doctor`에서 7개 Hermes Agent 프로필 모두 인식 확인; `terminal`(`delegate_task` 아님)을 통한 coordinator 위임이 엔드투엔드로 확인됨; `code_execution`이 실행 중인 `mock-pos` 컨테이너를 호출하여 주문/결제/환불/재고 조정을 수행함을 확인; 3개의 HITL 승인 게이트 모두 coordinator의 명시적 승인 없이는 차단됨을 확인. 전체 배포는 Docker Compose(`hermes`, `dashboard` [포트 9128의 Hermes 자체 내장 CLI 대시보드 — `smb-dashboard`와는 별개], `mock-pos`, `smb-dashboard`)로 실행된다.
- **진행 중**: `smb-dashboard` 웹 UI(SPEC-DASHBOARD-001) — 백엔드와 프런트엔드 소스는 존재하지만(주문/재고/예약/리포트/승인용 FastAPI 라우터, 동일한 5개 화면용 React 페이지) 아직 SPEC 라이프사이클을 완료하지 않았다.
- **실제 테스트에서 확인된 기존 제약사항**: `code_execution` 샌드박스는 프로필의 `.env`를 상속하지 않는다(통합 스크립트는 대신 하드코딩된 개발용 기본값을 사용); `terminal` 위임 호출은 예측 불가능하게 타임아웃(60~120초)될 수 있고 타임아웃 이후 상태가 일관되지 않아, coordinator는 타임아웃을 실패로 간주하지 않고 항상 재검증한다; `kanban` 네이티브 도구는 coordinator에서 동작하지 않는다; 웹/검색 도구는 비활성 상태다(검색 API 키 미설정); 실제 POS 벤더는 아직 통합되지 않았다(Mock POS만 존재).

## 로드맵

- **진행 중**: SPEC-DASHBOARD-001 — SMB 대시보드 MVP(백엔드 프록시 + 승인 스토어 + 5개 화면 프런트엔드 + 양방향 채널 HITL 동기화) 완성. 이 SPEC의 라이프사이클을 진행하려면 `/moai plan` / `/moai run` / `/moai sync`를 사용한다. 이 문서 자체는 SPEC을 정의하지 않는다.
- **향후 계획 / 현재 MVP 범위에서 명시적으로 제외**(docs/13 §8 기준): 항목별 저재고 임계값(현재는 단일 전역 상수), WebSocket/SSE를 통한 실시간 승인 대기열 갱신(현재는 폴링만), 다중 매장 또는 다국어 지원(단일 `store_id`, i18n 없음).
- **장기 계획**(docs/07 기준): 실제 POS 벤더(토스플레이스 / 카카오페이 급) 통합을 통해 Mock POS를 대체.
