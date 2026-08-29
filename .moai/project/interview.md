# Project Interview

## Stage A Round 1: Ownership, Purpose, and Goal
Question: Who maintains this project, what problem domain does it sit in, and what is the primary goal going forward?
Answer: Active product being developed further.
Domain: ax-automation-smb (auto-populated from codebase analysis — multi-agent AX automation platform for small businesses, composed of a Hermes coordinator/worker agent runtime, a Mock POS REST API, and a new customer-facing SMB dashboard web app)
Goal: Ship the SMB dashboard MVP (SPEC-DASHBOARD-001) as the current in-progress feature, giving SMB owners a single web screen for orders/inventory/reservations/sales and a dual-channel (web + Discord) HITL approval queue.

## Stage A Round 2: Constraints and Non-Goals
Question: What are the known constraints, technical debts, or things this project intentionally does NOT do?
Answer: No known critical constraints.
Constraints: none known beyond what docs/13 §8 already scopes out (no per-item low-stock threshold, no realtime WebSocket/SSE — polling only, single store_id / no multi-store or i18n support for the MVP).

## Stage A Round 3: Scope, Boundaries, and Documentation Priority
Question: What is in scope versus explicitly out of scope for this project, and which aspect must the documentation capture most accurately?
Answer: Architecture and module boundaries (documentation priority). Scope limited to docs/13 MVP dashboard design scope.
Scope: In scope — Hermes coordinator + 6 worker profiles, Mock POS REST API (orders/inventory/reservations/payments/reports), and the new smb-dashboard (FastAPI backend proxying Mock POS + owning the approvals JSON store, React/Vite frontend). Out of scope — multi-store/multi-language support, realtime WebSocket/SSE updates, per-item low-stock thresholds (all per docs/13 §8 MVP boundaries).

## Stage B Round 4: Verification, Surfaces, and Sharing
Verification: pytest (mock-pos: `pytest` in mock-pos/, config in pytest.ini; smb-dashboard backend: `pytest` in backend/, using pytest-httpx to mock Mock POS calls) — auto-populated from codebase analysis, confirmed via Round 1/2 answers.
UI surface: has-ui (smb-dashboard is a React/Vite web frontend served by FastAPI StaticFiles; Hermes itself is agent/CLI-driven, headless) — auto-populated from codebase analysis.
External systems: Mock POS REST API (http://mock-pos:8080, proxied by smb-dashboard backend), Hermes gateway/coordinator (writes/polls the approvals queue via code_execution), Discord (existing parallel HITL channel, unchanged) — auto-populated from codebase analysis.
Team sharing: solo — explicitly answered by user.
