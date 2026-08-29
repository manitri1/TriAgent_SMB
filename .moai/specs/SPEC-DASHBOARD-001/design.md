# Design Intent — SPEC-DASHBOARD-001

> **범위 참고.** 이 plan 단계 `design.md`는 plan-audit PASS와 Implementation Kickoff Approval 이후에 이어지는 디자인 단계를 위한 초안이다(UI 화면 포함 조건부 경로: plan → design → run). 이미 시각적/상호작용 측면에서 구현되어 있는 것을 목록화하고, `manager-design`이 해결해야 할 미결정 디자인 사항을 명시한다 — 최종 시각 디자인을 규정하지는 않는다(spec.md § Out of Scope — Design-Phase Visual Refinement).

## UI 화면 선언

- **UI 화면 포함 여부**: 예. 프론트엔드 모듈: `smb-dashboard/frontend`(React 18 + TypeScript + Vite 5, 라우터 없음, CSS 프레임워크 없음 — 순수 `styles.css`).
- **경로**: plan → design → run (표준 plan → run → sync가 아님).
- **충족된 판단 기준**: `spec.md §4`(다섯 개 화면)와 `acceptance.md`(AC-011, AC-016)에 명시적인 프론트엔드 컴포넌트/뷰/페이지 산출물이 정의되어 있다 — Tier-L + 프론트엔드 모듈 판단 기준과는 별개로, `spec-workflow.md` § Conditional Design Route의 첫 번째 UI 화면 판단 기준을 만족한다.

## 현재 구현 인벤토리 (as-built, 소스 코드 확인 기준)

| Element | Current state | File |
|---|---|---|
| App shell | 헤더 + 탭 내비게이션 + `<main class="content">`로 구성된 단일 `<div class="app">` | `frontend/src/App.tsx` |
| Tab navigation | 손으로 작성한 `<button>` 목록, `tab`/`tab-active` 클래스, `useState<Tab>` | `frontend/src/App.tsx` |
| Orders screen | 상태 배지가 있는 당일 주문 테이블; **아직 필터 컨트롤 없음** | `frontend/src/pages/OrdersPage.tsx` |
| Inventory screen | `low_stock: true` 항목에 빨간색 강조가 적용된 목록 | `frontend/src/pages/InventoryPage.tsx` |
| Reservations screen | 날짜 필터링된 목록 | `frontend/src/pages/ReservationsPage.tsx` |
| Sales Summary screen | 오늘/이번 주/이번 달 위젯 | `frontend/src/pages/SalesSummaryPage.tsx` |
| Approvals screen | 승인/거절 버튼과 브라우저 네이티브 `window.prompt()` 대화상자를 통한 사유 입력이 있는 대기 레코드 카드 | `frontend/src/pages/ApprovalsPage.tsx` |
| Styling | 디자인 토큰이나 컴포넌트 라이브러리 없이 순수 `styles.css` | `frontend/src/` |
| API client | `api.ts`의 손으로 작성한 `fetch` 래퍼, 화면별 타입 인터페이스 | `frontend/src/api.ts` |

## 미결정 디자인 사항 (디자인 단계에서 해결)

1. **주문 필터 컨트롤의 배치와 상호작용 패턴.** docs/13 §4는 "상태별 필터(OPEN/COMPLETED/CANCELED/REFUNDED)"를 명시하지만 별도의 시각적 목업은 없다. 기존의 손으로 작성한, 프레임워크 없는 관례와 일치하는 후보 패턴은 다음과 같다:
   - `App.tsx`의 기존 탭 버튼 스타일과 시각적으로 일관된 토글형 버튼 행 — 각 상태별 버튼 하나씩과 "전체" 버튼.
   - 네이티브 `<select>` 드롭다운(시각적 비중이 낮고 새로운 CSS 규칙이 적음).
   - **manager-design이 검토할 권장안**: 토글 버튼 패턴. 새로운 컨트롤 유형을 도입하는 대신 기존 `.tab`/`.tab-active` CSS 클래스에 새로운 수정자(modifier) 클래스를 추가하는 방식으로 재사용할 수 있어 새로운 CSS 표면을 최소화한다(단순성 강화 원칙).
2. **필터 선택 지속 여부**: 탭을 재진입할 때 선택된 필터를 "전체"로 초기화할지, 세션 동안 유지할지. 이를 규정하는 요구사항은 없으며, 디자인 단계에서 결정해야 한다.
3. **빈 상태(empty-state) 처리** — AC-015(일치하는 주문이 0건인 필터 선택)에 대해 단순한 빈 테이블을 보여줄지, 아니면 "이 필터와 일치하는 주문이 없습니다"와 같은 명시적 메시지를 보여줄지. 현재 다섯 개 화면 어디에도 빈 상태 패턴이 존재하지 않아 참고할 만한 기존 사례가 없다.
4. **Approvals 화면의 사유 입력 메커니즘.** 현재 구현은 인라인 폼 필드가 아니라 브라우저 네이티브 `window.prompt()` 블로킹 대화상자를 통해 거절/승인 사유를 입력받는다(`ApprovalsPage.tsx:L22-23`). 이는 spec.md §4의 "사유 입력"이라는 표현이 일반적으로 시사하는 것보다 상당히 원시적인(primitive) UX이다. manager-design은 이를 그대로 유지할지, 아니면 인라인 필드로 교체할지 평가해야 한다.

## 디자인 단계로 이어지는 제약 조건

- CSS 프레임워크 없음, 라우터 라이브러리 없음(tech.md 근거: "MVP 범위에 맞게 의도적으로 최소화").
- 하나의 컨트롤을 위해 새로운 시각 체계를 도입하기보다 기존 `.tab`/`.tab-active` 시각 언어를 따를 것.
- 한국어 UI 문구 관례(기존 다섯 개 화면의 모든 라벨과 메시지는 한국어로 작성되어 있음; 새 필터 라벨도 동일한 관례를 따라야 한다 — 예: "All"에 대해 "전체").

## H1–H9 핸드오프 계약 포인터

전체 H1–H9 디자인 단계 핸드오프 계약(시각 명세 형식, 컴포넌트 경계 정의, 접근성 검토, 반응형 동작)은 `manager-design`이 Implementation Kickoff Approval 이후 호출하는 `.claude/skills/moai/workflows/design.md`의 D1–D5 파이프라인이 소유한다. 이 문서는 디자인 단계의 시작 인벤토리와 미결정 사항 목록(위)을 제공할 뿐, D1–D5를 직접 실행하지는 않는다.
