# SPEC Review Report: PROJECT (.moai/project/{product,structure,tech}.md)
Iteration: 3/3
Verdict: PASS
Overall Score: 0.9

Reasoning context ignored per M1 Context Isolation. This audit reads only the three target documents (`.moai/project/product.md`, `.moai/project/structure.md`, `.moai/project/tech.md`) and the underlying repository files they describe (README.md, docs/*, mock-pos/, smb-dashboard/, .hermes/, docker-compose.yml, git working-tree diff). No prior review's reasoning narrative was treated as evidence — only the defect citations were used to know what to re-check.

## Scope Note (document type: project, not SPEC)

These three files are project-overview documents produced by the `moai-workflow-project` skill (`/moai project`), not a SPEC (`spec.md`/`plan.md`/`acceptance.md`). As established in iterations 1-2, they carry no YAML frontmatter and no `REQ-XXX`/`AC-XXX` entries, so the SPEC-specific must-pass criteria (MP-1, MP-2, MP-3, MP-4, MP-6, MP-7) and Groups 1/3/4/5/7 remain **N/A by document-type mismatch**. Per the Retry Loop Contract, this iteration is scoped to (a) the regression check on iteration-2's single open defect (D2, the tech.md self-contradiction), plus (b) a fresh full check of all three documents against current repository state, per the task instruction.

## Must-Pass Results

- [N/A] MP-1 REQ number consistency: no `REQ-XXX` entries exist in project docs by design
- [N/A] MP-2 EARS/GEARS format compliance: no `REQ-XXX` entries exist
- [N/A] MP-3 YAML frontmatter validity: none of the three files carries YAML frontmatter (confirmed unchanged: all three still open directly with `# Product` / `# Structure` / `# Tech`)
- [N/A] MP-4 Section 22 language neutrality: tech.md's stack table names a single accurate tech stack (Python/FastAPI, React/TypeScript, Node.js), not multi-language-tooling SPEC content in scope of the MP-4 enumeration rule
- [N/A] MP-5 D7 cross-SPEC reconciliation: no cross-reference to an already-existing, differently-numbered SPEC was found (`.moai/specs/` remains empty this iteration — re-verified via `Glob .moai/specs/**` returning empty)
- [N/A] MP-6 D8 cross-platform discipline: the literal substring `syscall` does not appear in any of the three files (re-verified: no match)
- [N/A] MP-7 clarification gate: neither `plan.md` nor `research.md` exists alongside these project docs

## Category Scores (0.0-1.0, rubric-anchored, adapted to project-doc scope)

| Dimension | Score | Rubric Band | Evidence |
|-----------|-------|-------------|----------|
| Clarity | 0.9 | Minor ambiguity in one or two statements | product.md:L33's Orders bullet remains the corrected, unambiguous implemented-vs-planned wording confirmed in iteration 2 ("no status filter implemented yet; status-based filtering is a planned roadmap item, see docs/13 §4") — docs/13-mvp-dashboard-design.md §4 ("화면 구성") exists and is the correct citation target. No new clarity regressions found. |
| Completeness | 0.9 | One non-critical section missing or sparse | Unchanged from prior iterations: all expected sections present in all three docs. The docker-compose diff added a 4th service block (`smb-dashboard`) matching tech.md's Build and Deployment table exactly (image/build, container name, ports, depends_on, env vars) — no gap introduced. |
| Testability (claim-verifiability) | 0.9 | One claim not precisely binary-testable but measurable with minor interpretation | The iteration-2 D2 contradiction is now resolved — see Regression Check below. `Grep 'mock outbound\|used to mock\|pytest-httpx\|pytest_httpx\|httpx_mock'` over the whole of tech.md returns exactly one substantive hit (L58), and its wording is now the corrected "declared ... but not yet used" form, matching L17 verbatim in substance. No other claim in the three documents was found false against the current repository state. |
| Consistency (cross-doc + intra-doc) | 0.9 | Minor cross-doc phrasing variance, no factual contradiction | tech.md L17 and L58 now say the same thing about `pytest-httpx` in different words (stack-table cell vs. dedicated Test Tooling bullet) — no remaining self-contradiction. Cross-checked against `mock-pos/mock_pos/routers/orders.py` and `mock-pos/tests/test_flow.py`'s new (uncommitted) status-filter capability: this capability lives entirely in `mock-pos` and is correctly *not* claimed as dashboard-facing anywhere in the three docs, consistent with product.md's corrected Orders bullet. |

## Defects Found (structured defect-list)

No defects found.

## Regression Check (Iteration 2+ only)

Defects from previous iterations:

- D1 (`PROJECT-FACT-001`, product.md Orders-filter claim, iteration 1): **RESOLVED** (confirmed in iteration 2, unchanged this iteration). `product.md:L33` still reads "today's orders, listed in a single table with a status badge (no status filter implemented yet; status-based filtering is a planned roadmap item, see docs/13 §4)". Re-verified against `smb-dashboard/backend/app/routers/orders.py` (`GET /today`, no `status` param — read this iteration, unchanged) and `smb-dashboard/frontend/src/pages/OrdersPage.tsx` (no filter UI). Accurate.
- D2 (`PROJECT-FACT-002`, tech.md pytest-httpx self-contradiction, iteration 2): **RESOLVED**. `Grep` for the false-claim pattern (`mock outbound|used to mock|pytest-httpx|pytest_httpx|httpx_mock`) across the entire `tech.md` file now returns only line 58, and its text is: "**pytest-httpx** — declared in `requirements-dev.txt` but not yet used in any test. `test_approvals.py` covers only the `/api/approvals*` endpoints (pure local JSON store, no httpx calls); the routers that call mock-pos over httpx (`orders.py`, `inventory.py`, `reservations.py`, `reports.py`) currently have no test coverage." This matches L17's stack-table wording exactly in substance. Re-verified against the code this iteration: `Grep 'httpx_mock|pytest_httpx'` over `smb-dashboard/backend/` returns zero matches; `Glob smb-dashboard/backend/tests/*` returns only `test_approvals.py`. The self-contradiction flagged in iteration 2 no longer exists — no stagnation, the defect was fully purged on the first attempted fix following iteration 2's report.

No defect has appeared unresolved across all three iterations (stagnation-detection N/A).

## Fresh Full-Document Check (iteration 3, per task instruction)

Beyond the regression check, the following claims were freshly re-verified against the current repository state (including the working-tree diff since iteration 2 — `.gitignore`, `.hermes/config.yaml`, a coordinator SKILL.md, `docker-compose.yml`, `docs/00-index.md`, `docs/06-hitl-approval-design.md`, `mock-pos/mock_pos/routers/orders.py`, `mock-pos/tests/test_flow.py`):

- **docker-compose.yml's new `smb-dashboard` service block** (added since iteration 2's audit, `git diff` shows a clean 24-line addition, no other service touched): container name `hermes-triagent-smb-dashboard-ui`, port `127.0.0.1:8652:8652`, `depends_on: mock-pos`, env vars (`MOCK_POS_BASE_URL`, `MOCK_POS_API_KEY`, `STORE_ID`, `LOW_STOCK_THRESHOLD`, `DASHBOARD_BASIC_AUTH_USER`, `DASHBOARD_BASIC_AUTH_PASSWORD`), bind mount `./smb-dashboard/data:/data` — all match tech.md's Build and Deployment table (L39-53) and structure.md's architecture-diagram port label (`:8652`) exactly. No drift.
- **mock-pos's new `list_orders` status-filter endpoint and test** (uncommitted diff to `orders.py` / `test_flow.py`): this is a `mock-pos`-side capability only (`GET /v1/stores/{store_id}/orders?status=`), not wired into the dashboard's proxy (`smb-dashboard/backend/app/mock_pos_client.py` / `routers/orders.py`, both re-read this iteration, unchanged since iteration 2, still only `GET /today` with no filter). This is consistent with — not contradictory to — product.md's corrected Orders bullet, which still correctly states no dashboard-facing filter exists.
- **docs/00-index.md and docs/06-hitl-approval-design.md diffs**: add an index row for docs/12 and docs/13 (already cited in product.md's roadmap and Core Features sections) and a "structured approval queue is now a parallel channel" note in docs/06 — both are consistent with, and reinforce, product.md's existing "second, parallel HITL channel" framing (L39-40) and the docs/06 cross-reference. No new claim in the three project docs depends on text that changed here in a way that breaks the citation.
- **`.hermes/profiles/` directory**: `ls` confirms exactly 7 profile directories (`coordinator`, `customer-service-agent`, `inventory-agent`, `marketing-crm-agent`, `order-payment-agent`, `reservation-agent`, `sales-analytics-agent`), matching product.md's "all 7 Hermes Agent profiles" claim and structure.md's profile list.
- **`mock-pos/mock_pos/main.py`**: no CORS middleware registered, confirming product.md's / structure.md's "No CORS support — callers must be server-side" claim.
- **`LOW_STOCK_THRESHOLD`**: `smb-dashboard/backend/app/routers/inventory.py:L12` reads a single `os.environ.get("LOW_STOCK_THRESHOLD", "10")` value with no per-item override, confirming product.md's "global `LOW_STOCK_THRESHOLD`, no per-item threshold yet" claim.
- **Dashboard backend router set, frontend page set, Dockerfile stages, package.json versions, requirements.txt/requirements-dev.txt pins**: all re-read this iteration and unchanged from iteration 2's verified state — `orders.py`/`inventory.py`/`reservations.py`/`reports.py`/`approvals.py` routers; `OrdersPage.tsx`/`InventoryPage.tsx`/`ReservationsPage.tsx`/`SalesSummaryPage.tsx`/`ApprovalsPage.tsx` pages; multi-stage `node:20-slim` → `python:3.11-slim` Dockerfile with `EXPOSE 8652`; React 18.3.1/TypeScript 5.5.4/Vite 5.4.1; FastAPI 0.115.0/uvicorn 0.30.6/pydantic 2.9.2/httpx 0.27.2; pytest 8.3.3/pytest-httpx 0.30.0. All match tech.md's stack table verbatim.
- **`ReservationsPage.tsx`**: re-read this iteration; still a single-date `<input type="date">` picker + table (not a calendar-grid widget), consistent with the residual-risk noted in iteration 1 as a stylistic-not-false description; not folded into the defect list, per that prior finding.

No new defect was found in this fresh check.

## Recommendation

No fix action required. All prior defects (D1, D2) are confirmed resolved, no new defects were introduced by the working-tree changes since iteration 2, and a fresh full check of all three documents against the current repository state (including the newly-added docker-compose service block and the mock-pos status-filter capability) found no further false or contradictory claims. This iteration's PASS is grounded in direct re-verification, not in carrying forward iteration 2's assessment.

### Evidence index (commands run, verbatim findings this report cites)

- `Read .moai/reports/plan-audit/PROJECT-review-1.md`, `PROJECT-review-2.md` — prior defect baselines (reasoning narrative ignored per M1; only defect citations used)
- `Read .moai/project/{product,structure,tech}.md` — full document text, all three files
- `Grep 'mock outbound|used to mock|pytest-httpx|pytest_httpx|httpx_mock' .moai/project/tech.md` — exactly one match, at L58, now correct
- `Grep 'httpx_mock|pytest_httpx' smb-dashboard/backend` — 0 matches
- `Glob smb-dashboard/backend/tests/*` — only `test_approvals.py`
- `Bash git status --short` / `git diff --stat` — full working-tree diff enumerated since iteration 2 (8 modified files, several untracked directories)
- `Bash git diff -- docker-compose.yml` — full diff of the new `smb-dashboard` service block
- `Bash git diff -- mock-pos/mock_pos/routers/orders.py mock-pos/tests/test_flow.py` — full diff of the new status-filter endpoint + test
- `Bash git diff -- docs/06-hitl-approval-design.md docs/00-index.md` — full diff, both consistent with existing product.md claims
- `Read smb-dashboard/backend/app/routers/orders.py` — `GET /today`, no status param (D1 re-confirmed)
- `Read smb-dashboard/backend/app/routers/inventory.py` — single global `LOW_STOCK_THRESHOLD` env var, no per-item override
- `Read mock-pos/mock_pos/main.py` — no CORS middleware registered
- `Read smb-dashboard/frontend/src/pages/ReservationsPage.tsx` — single-date picker, unchanged
- `Bash ls -la .hermes/profiles/` — exactly 7 profile directories
- `Bash cat docker-compose.yml` — full file, all 4 services match tech.md's Build and Deployment table
- `Bash cat smb-dashboard/frontend/package.json`, `smb-dashboard/backend/requirements.txt`, `requirements-dev.txt` — all versions match tech.md's stack table
- `Read smb-dashboard/Dockerfile` — multi-stage `node:20-slim` → `python:3.11-slim`, `EXPOSE 8652`, matches structure.md/tech.md
- `Grep '^#|§4|§6|§8' docs/13-mvp-dashboard-design.md` — confirmed §4 ("화면 구성") exists, validating product.md's docs/13 §4 citation
- `Glob .moai/specs/**` — empty (re-confirmed, MP-5 still N/A)

### Residual-risk

- Deeper runtime/behavioral claims in product.md's "Current Status" section (HITL gates actually blocking, `terminal` delegation timeout behavior, `hermes doctor` output) were not re-executed live in this iteration; they are unchanged since iteration 1, where they were cross-checked only against README.md's narrative, not a live run. This risk has been carried unchanged across all three iterations and was out of scope for the two flagged defects.
- The mock-pos status-filter capability added in the uncommitted working-tree diff is not yet surfaced anywhere in the three project docs as even a partial/in-progress capability at the mock-pos layer specifically (only the dashboard-facing absence is documented). This is not a false claim — the docs make no claim about mock-pos's own filter capability — but if `mock-pos`'s API surface is later documented in more granular technical detail, this diff would be the natural addition point.
- This audit did not re-verify `.hermes/config.yaml`'s or the coordinator `SKILL.md`'s diffs line-by-line against product.md's Core Features bullets beyond confirming they do not contradict the existing HITL-gate / delegation-method claims already verified in iterations 1-2; both diffs are additive documentation/config changes, not behavioral rewrites, based on the diff stat sizes (48 and 34 lines respectively) and the file types involved.

Verdict: PASS
