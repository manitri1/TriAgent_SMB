# SPEC Review Report: PROJECT (.moai/project/{product,structure,tech}.md)
Iteration: 1/3
Verdict: FAIL
Overall Score: 0.55

Reasoning context ignored per M1 Context Isolation. This audit reads only the three target documents (`.moai/project/product.md`, `.moai/project/structure.md`, `.moai/project/tech.md`) and the underlying repository files they describe (README.md, docs/*, mock-pos/, smb-dashboard/, .hermes/, docker-compose.yml).

## Scope Note (document type: project, not SPEC)

These three files are project-overview documents produced by the `moai-workflow-project` skill (`/moai project`), not a SPEC (`spec.md`/`plan.md`/`acceptance.md`). They carry no YAML frontmatter, no `REQ-XXX`/`AC-XXX` entries, and are not required to. Consequently the SPEC-specific must-pass criteria MP-1 (REQ numbering), MP-2 (GEARS/EARS format), MP-3 (12-field frontmatter schema), MP-4 (Section 22 language neutrality — 16-language enumeration), MP-6 (D8 syscall/cross-platform), and MP-7 ([NEEDS CLARIFICATION] markers — no `plan.md`/`research.md` exists for this artifact set) are **N/A by document-type mismatch**, not by waiver. Groups 1, 3, 4, 5, and 7 of the checklist are correspondingly N/A for the same reason. This is stated explicitly per M4/M5 rather than silently skipped.

The audit instead applies the adversarial-verification spirit of M2/M4 to the one thing this document type can be judged on: **do the documents' factual claims match the actual repository state?** This is also the task's explicit instruction. Two claims were found to be false on direct inspection of the code they describe — see Defects Found.

## Must-Pass Results

- [N/A] MP-1 REQ number consistency: no `REQ-XXX` entries exist in project docs by design (product/structure/tech are narrative, not requirement-bearing)
- [N/A] MP-2 EARS/GEARS format compliance: no `REQ-XXX` entries exist
- [N/A] MP-3 YAML frontmatter validity: none of the three files carries a YAML frontmatter block (all three open directly with `# Product` / `# Structure` / `# Tech` — verified by reading line 1 of each file); frontmatter is not part of this artifact type's contract
- [N/A] MP-4 Section 22 language neutrality: tech.md's stack table names Python/FastAPI, React/TypeScript, and Node.js — this is an accurate description of a genuinely single-tech-stack project (confirmed: `mock-pos/requirements.txt`, `smb-dashboard/backend/requirements.txt`, `smb-dashboard/frontend/package.json` are all present and consistent with the stack table), not a multi-language-tooling SPEC in scope of the MP-4 enumeration rule
- [N/A] MP-5 D7 cross-SPEC reconciliation: no `SPEC-([A-Z][A-Z0-9]+-)+[0-9]+`-shaped cross-reference requiring reconciliation was found in these three files (the one SPEC-ID present, `SPEC-DASHBOARD-001`, is self-referential roadmap language, not a reference to a different, already-existing SPEC — confirmed `.moai/specs/` is empty, so there is nothing to reconcile against)
- [N/A] MP-6 D8 cross-platform discipline: the literal substring `syscall` does not appear in any of the three files (Grep confirmed no match)
- [N/A] MP-7 clarification gate: neither `plan.md` nor `research.md` exists alongside these project docs (this artifact type has no such companions) — N/A per the MP-7 precondition

## Category Scores (0.0-1.0, rubric-anchored, adapted to project-doc scope)

| Dimension | Score | Rubric Band | Evidence |
|-----------|-------|-------------|----------|
| Clarity | 0.75 | Minor ambiguity in one or two statements | The "Core Features" bullets under SMB Dashboard (product.md L31-39) are phrased as present-tense capability descriptions ("giving the owner a single screen for: Orders — today's orders, filterable by status...") without a clear "planned/target" qualifier, even though the parenthetical marks the whole section "in progress." A reader cannot tell from the text alone which bullets are already implemented and which are target design — see Defects D1/D2. |
| Completeness | 0.9 | One non-critical section missing or sparse | All three docs cover their expected sections fully (product.md: Name/Description/Target Audience/Core Features/Current Status/Roadmap; structure.md: Directory Tree/Architecture Pattern/Key File Locations; tech.md: Stack/Rationale/Dev Environment/Build & Deployment/Test Tooling — all verified present). Minor gap: tech.md's Testing row (tech.md:L17) does not disclose that `orders`/`inventory`/`reservations`/`reports` proxy routers have zero test coverage — only `approvals` is tested (verified: `Glob smb-dashboard/backend/tests/*` returns exactly one file, `test_approvals.py`). |
| Testability (claim-verifiability) | 0.5 | Several claims contain unverifiable or contradicted specifics | Two specific, falsifiable claims were checked against the code and found false — see D1 and D2. A specific claim naming exact enum values (`OPEN/COMPLETED/CANCELED/REFUNDED`) or a specific library (`pytest-httpx`) invites exactly this kind of verification, and both failed it. |
| Consistency (cross-doc + intra-doc) | 0.5 | Multiple statements lack internal support | product.md's own "Current Status" section (L44) says the dashboard "has not yet completed its SPEC lifecycle," which sits uneasily beside the unqualified, present-tense "Core Features" bullet list one paragraph above claiming a filter capability that does not exist in the code at all (not partially — zero implementation on either the frontend or the dashboard-backend API surface). |

## Defects Found (structured defect-list)

D1. `PROJECT-FACT-001` — `.moai/project/product.md:L33` — Claims "**Orders** — today's orders, filterable by status (OPEN/COMPLETED/CANCELED/REFUNDED)" as a Core Feature of the SMB Dashboard. Verified against the code: `smb-dashboard/backend/app/routers/orders.py` exposes only `GET /today` with no `status` query parameter; `smb-dashboard/backend/app/mock_pos_client.py`'s `list_orders()` takes no filter argument and is called with none; `smb-dashboard/frontend/src/pages/OrdersPage.tsx` renders every returned order in one table with a status *badge* but has no filter control, no filter state, and no filtered API call. (Note: the underlying `mock-pos` service does support a `status` query param on its own `GET /v1/stores/{store_id}/orders` per an uncommitted working-tree change to `mock-pos/mock_pos/routers/orders.py`, but this capability is not wired into the dashboard's proxy endpoint or its UI, so the SMB Dashboard screen the document describes cannot filter by status today.) — Severity: major — Class: blocking — Required fix: either (a) implement the status filter in `orders.py`'s dashboard router + `OrdersPage.tsx`, or (b) rewrite the bullet to state the filter is planned/not-yet-implemented (e.g., move it under Roadmap, or add "(planned)").

D2. `PROJECT-FACT-002` — `.moai/project/tech.md:L17` — Claims "dashboard backend: `smb-dashboard/backend/tests/test_approvals.py` using `pytest-httpx` to mock outbound calls to mock-pos." Verified against the code: `test_approvals.py` (the only test file under `smb-dashboard/backend/tests/`) contains no reference to `pytest_httpx` or the `httpx_mock` fixture anywhere in the file, and every test in it exercises only the `/api/approvals*` endpoints, which never call `mock_pos_client` / httpx at all (the approvals store is pure local JSON I/O). A repo-wide grep for `httpx_mock|pytest_httpx` under `smb-dashboard/backend/` returns zero matches, confirming the dependency (`pytest-httpx==0.30.0` in `requirements-dev.txt`) is currently unused. The routers that actually call mock-pos over httpx (`orders.py`, `inventory.py`, `reservations.py`, `reports.py`) have no test file at all. — Severity: major — Class: blocking — Required fix: correct tech.md to state that only the approvals endpoints are currently tested (no mock-pos-calling endpoint has test coverage), and either add the described pytest-httpx-backed tests for the proxy routers or remove the false claim.

No other defects found; all other checked claims (directory tree entries, docker-compose service/port/volume topology, dependency version pins in `requirements.txt`/`requirements-dev.txt`/`package.json`, HITL gate-to-agent mapping against docs/06, docs/13 §8 / docs/07 §5 cross-references, `.hermes/profiles/` count, CORS/auth behavior, `LOW_STOCK_THRESHOLD` single-global-constant claim, frontend "no router/no CSS framework" claim, "no test script in frontend package.json" claim) were verified accurate against the repository — see Residual-risk below for what was not independently re-verified.

## Regression Check (Iteration 2+ only)

N/A — this is iteration 1.

## Recommendation

1. Fix D1: `.moai/project/product.md:L33` — the Orders bullet overstates shipped functionality. Reconcile the "Core Features" bullet list with the actual current implementation state, or explicitly mark unimplemented sub-bullets as planned.
2. Fix D2: `.moai/project/tech.md:L17` — the testing-tooling claim about `test_approvals.py` and `pytest-httpx` is factually wrong; correct the row to reflect that only approvals has test coverage today, and that pytest-httpx is an unused dev-dependency until the proxy-router tests are written.
3. Consider tightening product.md's "Core Features" section overall: since the SMB Dashboard's individual bullets mix implemented and target-only capabilities under one "in progress" parenthetical, a reader cannot distinguish shipped from planned without reading the code — a short per-bullet status marker (e.g., "(implemented)"/"(planned)") would close this gap for the whole subsection, not just the Orders line.

### Evidence index (commands run, verbatim findings this report cites)

- `Read .moai/project/{product,structure,tech}.md` — full document text, no frontmatter present
- `Read smb-dashboard/backend/app/routers/orders.py` — single `GET /today` route, no status param
- `Read smb-dashboard/backend/app/mock_pos_client.py` — `list_orders()` takes no filter arg
- `Read smb-dashboard/frontend/src/pages/OrdersPage.tsx` — no filter UI/state
- `Read smb-dashboard/backend/tests/test_approvals.py` — full file, no `pytest_httpx`/`httpx_mock` reference
- `Grep 'httpx_mock|pytest_httpx' smb-dashboard/backend` — 0 matches
- `Glob smb-dashboard/backend/tests/*` — only `test_approvals.py` exists
- `Read docker-compose.yml`, `mock-pos/requirements.txt`, `smb-dashboard/backend/requirements*.txt`, `smb-dashboard/frontend/package.json`, `mock-pos/Dockerfile`, `smb-dashboard/Dockerfile` — all version/port/service claims in tech.md/structure.md confirmed
- `Read docs/06-hitl-approval-design.md`, `docs/07-roadmap.md`, `docs/12-mvp-window-options.md`, `docs/13-mvp-dashboard-design.md` (section-header greps) — all cross-document citations in product.md/tech.md (HITL gate numbering, "docs/13 §8", "docs/07", "docs/12 'Option C'") confirmed accurate
- `Glob .moai/specs/**` — empty; no reconciliation target exists for the self-referential `SPEC-DASHBOARD-001` mention

### Residual-risk

- Deeper runtime behavior (e.g., whether the coordinator's `terminal` delegation and the three HITL gates actually block as described) was not re-executed in this audit; the "Verified working baseline (2026-08-19)" claim in product.md was cross-checked only against README.md's matching narrative, not against a live run.
- `mock-pos/tests/test_flow.py` and `mock-pos/mock_pos/routers/orders.py` carry uncommitted working-tree changes (per `git status`); this audit read the working-tree state, not HEAD, which is the correct target for auditing current documentation claims but means the diff is not yet committed.
- The frontend's "calendar-style listing by date" (product.md:L35) description of `ReservationsPage.tsx` is generous (it is a single-date `<input type="date">` picker + table, not a calendar-grid widget) but not clearly false, since the screen does let the owner browse reservations by date; this was treated as an optional/stylistic finding, not folded into the defect list.

Verdict: FAIL
