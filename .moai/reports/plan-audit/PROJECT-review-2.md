# SPEC Review Report: PROJECT (.moai/project/{product,structure,tech}.md)
Iteration: 2/3
Verdict: FAIL
Overall Score: 0.6

Reasoning context ignored per M1 Context Isolation. This audit reads only the three target documents (`.moai/project/product.md`, `.moai/project/structure.md`, `.moai/project/tech.md`) and the underlying repository files they describe (README.md, docs/*, mock-pos/, smb-dashboard/, .hermes/, docker-compose.yml, git working-tree diff).

## Scope Note (document type: project, not SPEC)

These three files are project-overview documents produced by the `moai-workflow-project` skill (`/moai project`), not a SPEC (`spec.md`/`plan.md`/`acceptance.md`). As established in iteration 1, they carry no YAML frontmatter and no `REQ-XXX`/`AC-XXX` entries, so the SPEC-specific must-pass criteria (MP-1, MP-2, MP-3, MP-4, MP-6, MP-7) and Groups 1/3/4/5/7 remain **N/A by document-type mismatch**. Per the Retry Loop Contract this iteration is scoped to (a) the regression check on iteration-1's two defects, plus (b) a normal fresh check of the rest of the documents against current repository state.

## Must-Pass Results

- [N/A] MP-1 REQ number consistency: no `REQ-XXX` entries exist in project docs by design
- [N/A] MP-2 EARS/GEARS format compliance: no `REQ-XXX` entries exist
- [N/A] MP-3 YAML frontmatter validity: none of the three files carries YAML frontmatter (confirmed unchanged: all three still open directly with `# Product` / `# Structure` / `# Tech`)
- [N/A] MP-4 Section 22 language neutrality: tech.md's stack table names a single accurate tech stack (Python/FastAPI, React/TypeScript, Node.js), not multi-language-tooling SPEC content in scope of the MP-4 enumeration rule
- [N/A] MP-5 D7 cross-SPEC reconciliation: no cross-reference to an already-existing, differently-numbered SPEC was found (`.moai/specs/` remains empty — `Glob .moai/specs/**` re-verified empty this iteration)
- [N/A] MP-6 D8 cross-platform discipline: the literal substring `syscall` does not appear in any of the three files (re-verified: no match)
- [N/A] MP-7 clarification gate: neither `plan.md` nor `research.md` exists alongside these project docs

## Category Scores (0.0-1.0, rubric-anchored, adapted to project-doc scope)

| Dimension | Score | Rubric Band | Evidence |
|-----------|-------|-------------|----------|
| Clarity | 0.85 | Minor ambiguity in one or two statements | product.md:L33's Orders bullet now reads "today's orders, listed in a single table with a status badge (no status filter implemented yet; status-based filtering is a planned roadmap item, see docs/13 §4)" — a clear implemented-vs-planned distinction, closing iteration-1 D1's ambiguity. |
| Completeness | 0.9 | One non-critical section missing or sparse | Unchanged from iteration 1: all expected sections present in all three docs; the same minor gap remains (tech.md does not flag zero-coverage on the httpx-calling proxy routers as a headline caveat, though it is now stated in the stack-table row — see Testability). |
| Testability (claim-verifiability) | 0.5 | Several claims contain unverifiable or contradicted specifics | D1 (Orders filter) is now verified TRUE against the code. D2 (pytest-httpx) is **only partially fixed**: the stack-table row (tech.md:L17) was corrected, but the dedicated "Test Tooling" section (tech.md:L58) still asserts the original false claim verbatim — see D2 (regressed) below. A document that asserts both "not yet used" and "used" for the same fact fails claim-verifiability at the document level. |
| Consistency (cross-doc + intra-doc) | 0.35 | Multiple statements lack internal support | tech.md now directly contradicts itself within the same file: L17 states `pytest-httpx` "is declared in `requirements-dev.txt` but is not yet used in any test," while L58 states `pytest-httpx` "used in `smb-dashboard/backend/tests/test_approvals.py` to mock outbound HTTP calls to `mock-pos`." These two sentences describe the same fact and cannot both be true; the code confirms L17 is correct and L58 is false (see D2 below). This is a strictly worse intra-doc consistency failure than iteration 1's single wrong statement, because the document now asserts both the true and the false version of the same claim. |

## Defects Found (structured defect-list)

D1. `PROJECT-FACT-001` (iteration-1 defect) — **RESOLVED**. `.moai/project/product.md:L33` now reads "**Orders** — today's orders, listed in a single table with a status badge (no status filter implemented yet; status-based filtering is a planned roadmap item, see docs/13 §4)". Re-verified against the code: `smb-dashboard/backend/app/routers/orders.py` (`GET /today`, no `status` param), `smb-dashboard/backend/app/mock_pos_client.py::list_orders()` (no filter arg), and `smb-dashboard/frontend/src/pages/OrdersPage.tsx` (renders all returned orders in one table with a status badge, no filter UI/state) all confirm the corrected wording is now accurate. No remaining issue.

D2. `PROJECT-FACT-002` (iteration-1 defect) — **UNRESOLVED (regressed to a new location)**. The specific sentence originally flagged in the stack table (tech.md, then-L17) was corrected, but `.moai/project/tech.md:L58` (the "## Test Tooling" section) still contains the identical false claim: "**pytest-httpx** — used in `smb-dashboard/backend/tests/test_approvals.py` to mock outbound HTTP calls to `mock-pos` without a live dependency." Re-verified against the code this iteration: `Grep 'httpx_mock|pytest_httpx'` over `smb-dashboard/backend/` returns zero matches; `Read smb-dashboard/backend/tests/test_approvals.py` (the only test file present) shows no `httpx_mock` fixture and every test hits only `/api/approvals*`, which is pure local JSON I/O with no outbound HTTP call to mock. `pytest-httpx` therefore remains an unused dev-dependency exactly as iteration 1 found. Because the fix corrected the stack-table row (L17) but left the dedicated Test Tooling section's near-identical prose (L58) unchanged, the document now internally contradicts itself — L17 says "not yet used in any test," L58 says "used ... to mock outbound HTTP calls." This is the same defect class flagged in iteration 1 (a specific, falsifiable tooling claim that does not match the code), not a newly-introduced issue, and per the Retry Loop Contract an unresolved defect from a prior iteration is an automatic FAIL regardless of other scores. — Severity: major — Class: blocking — Required fix: correct `.moai/project/tech.md:L58` to match the (now-correct) L17 wording — state that `pytest-httpx` is declared but not yet used, that `test_approvals.py` covers only the approvals endpoints (no httpx calls), and that the routers which do call mock-pos over httpx (`orders.py`, `inventory.py`, `reservations.py`, `reports.py`) have no test coverage. Search the whole file for any other repetition of the old claim before closing.

No other defects found this iteration. Fresh spot-checks of claims not previously flagged — docker-compose.yml's 4-service topology (names, ports, `depends_on`, env vars, bind mounts), `smb-dashboard/Dockerfile` (Node 20-slim build stage, Python 3.11-slim runtime, `EXPOSE 8652`), `smb-dashboard/frontend/package.json` (React 18.3.1, TypeScript 5.5.4, Vite 5.4.1, no test script, no router/CSS-framework dependency), `approvals_store.py`'s default `/data/approvals.json` path against the compose bind mount, `mock_pos_client.py`'s read-only (`_get`-only) proxy shape against structure.md's "read-only proxy" diagram label, and the top-level directory list in structure.md (`.github`, `.git_hooks`, `refs/`, `.claude/`, `.moai/` all present) — were all verified accurate against the current repository state.

## Regression Check (Iteration 2+ only)

Defects from previous iteration (PROJECT-review-1.md):
- D1 (`PROJECT-FACT-001`, product.md Orders-filter claim): **RESOLVED** — wording now matches the code (no filter implemented; correctly marked planned).
- D2 (`PROJECT-FACT-002`, tech.md pytest-httpx claim): **UNRESOLVED** — the stack-table instance (old L17) was fixed, but the Test Tooling section instance (L58) still asserts the false claim verbatim, and now directly contradicts the corrected line elsewhere in the same file. This is not a fresh defect appearing "in all three iterations unchanged" (only 2 iterations exist so far), but it is the same root defect surviving under a different citation — flag per the stagnation-detection intent: the underlying false fact was not fully purged from the document, only partially edited.

## Recommendation

1. Fix D2 (still open): edit `.moai/project/tech.md:L58` to state that `pytest-httpx` is an unused dev-dependency, that `test_approvals.py` tests only the approvals endpoints with no outbound HTTP calls, and that the httpx-calling proxy routers (`orders.py`, `inventory.py`, `reservations.py`, `reports.py`) have zero test coverage — matching the already-correct wording at L17. Grep the whole file (`grep -n pytest-httpx .moai/project/tech.md`) before closing, to confirm no third instance of the old claim survives.
2. Once D2 is fixed, re-run a targeted regression check (iteration 3) rather than a from-scratch audit, per the Retry Loop Contract's delta-scoped re-audit rule.
3. No action needed on D1 — confirmed resolved and accurate.

### Evidence index (commands run, verbatim findings this report cites)

- `Read .moai/reports/plan-audit/PROJECT-review-1.md` — iteration-1 defect baseline
- `Read .moai/project/{product,structure,tech}.md` — full document text, both D1 and D2 locations
- `Grep 'httpx_mock|pytest_httpx' smb-dashboard/backend` — 0 matches (re-confirmed)
- `Read smb-dashboard/backend/tests/test_approvals.py` — full file, no httpx_mock/pytest_httpx reference, all tests hit `/api/approvals*` only
- `Read smb-dashboard/backend/app/routers/orders.py` — `GET /today`, no status param (D1 re-confirmed)
- `Read smb-dashboard/frontend/src/pages/OrdersPage.tsx` — no filter UI/state (D1 re-confirmed)
- `Bash git status --short` / `git diff --stat` / `git diff -- mock-pos/mock_pos/routers/orders.py` — working-tree state unchanged from iteration 1 (orders.py's `status`-filter addition to mock-pos itself remains uncommitted and still not wired to the dashboard)
- `Read README.md`, `docker-compose.yml`, `smb-dashboard/Dockerfile`, `smb-dashboard/frontend/package.json` — cross-checked ports, service names, env vars, versions against structure.md/tech.md tables
- `Glob smb-dashboard/backend/app/routers/*.py` + `Grep '@router\.(get|post|patch|put|delete)'` — confirmed all dashboard-backend proxy routers are GET-only except `approvals.py` (POST/GET/PATCH on its own local store), consistent with structure.md's "read-only proxy" label
- `Read smb-dashboard/backend/app/mock_pos_client.py` — only a `_get` helper exists; no outbound POST/PATCH to mock-pos
- `Grep 'APPROVALS_DATA_FILE|approvals.json' smb-dashboard/backend/app/approvals_store.py` — default `/data/approvals.json`, consistent with the compose bind mount `./smb-dashboard/data:/data`
- `Bash ls .github .git_hooks refs .claude .moai` — all present, consistent with structure.md's directory tree
- `Glob .moai/specs/**` — empty (re-confirmed, MP-5 still N/A)

### Residual-risk

- This iteration did not re-verify the deeper runtime/behavioral claims in product.md's "Current Status" section (HITL gates blocking, `terminal` delegation timeouts, etc.) — those were not implicated by either flagged defect and are unchanged since iteration 1, where they were cross-checked only against README.md's narrative, not a live run.
- `mock-pos/mock_pos/routers/orders.py` and `mock-pos/tests/test_flow.py` remain uncommitted working-tree changes; this audit reads working-tree state (correct for auditing current doc claims), but the status-filter capability added there is still not surfaced anywhere in the three project docs as even a partial/in-progress capability — this is consistent with, not contradictory to, D1's now-correct "not implemented in the dashboard" wording, since the uncommitted change is in mock-pos, not in the dashboard's proxy or UI.
- A third instance of the retired pytest-httpx claim was not found by a repo-wide search of the three files beyond the two locations checked (old L17, now-fixed; L58, still broken); if any other project doc (outside the three audited here) repeats the same claim, it was out of this audit's scope.

Verdict: FAIL
