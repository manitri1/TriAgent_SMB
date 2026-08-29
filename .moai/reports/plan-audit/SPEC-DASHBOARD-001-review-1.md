# SPEC Review Report: SPEC-DASHBOARD-001
Iteration: 1/3
Verdict: PASS
Overall Score: 0.92

Reasoning context ignored per M1 Context Isolation. This audit is based solely on `.moai/specs/SPEC-DASHBOARD-001/{spec,plan,acceptance,design,research,progress,spec-compact}.md` (Tier L — all 5 required artifacts present, plus progress.md and spec-compact.md) cross-referenced directly against the repository source (`smb-dashboard/backend/app/*`, `smb-dashboard/frontend/src/*`, `docker-compose.yml`, `docs/13-mvp-dashboard-design.md`, `docs/06-hitl-approval-design.md`, `.hermes/profiles/coordinator/skills/orchestration/task_dispatch_and_verification/SKILL.md`).

## Plausible Failure Modes Checked (M2 pre-read list)

REQ numbering gaps/dupes; informal/GEARS-noncompliant REQs; frontmatter field/type errors; HOW-not-WHAT leakage into REQs; broken REQ↔AC traceability; hardcoded language-specific tool names; missing/vague Out of Scope; contradictory requirements; unmarked deprecated IF/THEN usage; unresolved `[NEEDS CLARIFICATION]` markers; **and, per the task's explicit instruction, overclaiming of already-delivered behavior against actual source code**.

## Must-Pass Results

- [PASS] MP-1 REQ number consistency: `spec.md:L82-105` — REQ-001 through REQ-018, sequential, no gaps, no duplicates, consistent 3-digit zero-padding (`REQ-001` … `REQ-018`). `acceptance.md:L9-35` — AC-001 through AC-021, same consistency.
- [PASS] MP-2 EARS/GEARS format compliance (requirement layer — `REQ-XXX` in `spec.md` only, per M3 § Scope; AC-XXX Given-When-Then entries in `acceptance.md` are the correct verification-layer format and are NOT graded here): all 18 REQs match a GEARS pattern (Ubiquitous: REQ-001–004, 006, 009, 011, 013, 014, 016–018; Event-driven: REQ-005, 007, 015; Event-detected/unwanted (When…shall / shall not): REQ-008, 010; Where/capability-gate: REQ-012). No informal language, no G/W/T scenario presented as a REQ. One semantic quibble noted below (D3) does not amount to a format violation — REQ-012 is syntactically GEARS-compliant.
- [PASS] MP-3 YAML frontmatter validity: `spec.md:L1-15` — all 12 canonical fields present with correct types verified against `.claude/rules/moai/development/spec-frontmatter-schema.md`: `id: SPEC-DASHBOARD-001`, `title` (quoted string), `version: "0.1.0"` (quoted semver), `status: draft` (valid enum), `created`/`updated: 2026-08-29` (ISO date), `author: manit`, `priority: P1` (valid enum), `phase: "v0.2.0 target"` (release-target label, not a prohibited lifecycle token), `module: "smb-dashboard"`, `lifecycle: spec-anchored` (valid enum), `tags:` (comma-separated string). No rejected snake_case aliases (`created_at`/`updated_at`/`labels`/`spec_id`) present. Optional `tier: L` also present and consistent with the 5-artifact Tier L set actually delivered.
- [N/A] MP-4 Section 22 language neutrality: this SPEC is scoped to a single-language project stack (Python/FastAPI backend + TypeScript/React frontend for one specific application), not multi-language dev-tooling. Auto-pass per the single-language-scope exemption.
- [PASS] MP-5 D7 cross-SPEC reconciliation: `grep -rn 'SPEC-([A-Z][A-Z0-9]+-)+[0-9]+' .moai/specs/SPEC-DASHBOARD-001/` returns matches only for `SPEC-DASHBOARD-001` itself (self-references in titles/frontmatter/trackability text across all 7 artifact files). No other SPEC-ID is referenced anywhere in the SPEC body, so there is nothing to reconcile and no BLOCKING finding is possible. `.moai/specs/` contains no other SPEC directory (`ls .moai/specs/` shows only `SPEC-DASHBOARD-001/`).
- [PASS] MP-6 D8 cross-platform discipline: `grep -c 'syscall' .moai/specs/SPEC-DASHBOARD-001/*.md` → 0 matches across all artifacts. Auto-PASS per D8-4 (syscall does not appear).
- [PASS] MP-7 clarification gate: `grep -rn '\[NEEDS CLARIFICATION' .moai/specs/SPEC-DASHBOARD-001/plan.md .moai/specs/SPEC-DASHBOARD-001/research.md` → 0 matches. (Also verified 0 matches across the full SPEC directory, all 7 files.)

**No must-pass failure. The M5 firewall does not block this SPEC.**

## Category Scores (0.0-1.0, rubric-anchored)

| Dimension | Score | Rubric Band | Evidence |
|-----------|-------|-------------|----------|
| Clarity | 1.0 | 1.0 — single unambiguous interpretation, measurable ACs | `spec.md:L82-105` (18 REQs, all with specific values/params: `LOW_STOCK_THRESHOLD` default 10, HTTP status codes, exact endpoint paths); `acceptance.md:L9-35` (21 Given-When-Then ACs with concrete expected values). No pronoun-reference ambiguity found. |
| Completeness | 1.0 | 1.0 — all required sections + frontmatter present | HISTORY (`spec.md:L19-23`), WHY (`spec.md §1 Overview` + `§2 Success Metrics`), WHAT (`spec.md §1`, `§4 Screens`), REQUIREMENTS (`spec.md §3`, 18 REQs), ACCEPTANCE CRITERIA (`acceptance.md`, correctly externalized per the Tier L two-layer architecture — M3 § Scope), Out of Scope (`spec.md:L117-135`, 5 distinct `### Out of Scope — <topic>` H3 sub-headings each with `-` bullets). Frontmatter complete (MP-3). |
| Testability | 0.75 | 0.75 — one AC not precisely binary-testable, measurable with minor interpretation | **AC-011** (`acceptance.md:L19`) asserts "each corresponding screen renders and issues **exactly one fetch** to its associated `/api/*` route" — this is FALSE as literally worded for the Sales Summary screen. `SalesSummaryPage.tsx:L15-23` issues **three concurrent fetches** via `Promise.all(PERIODS.map((p) => api.salesSummary(p.key)))` (one call to `/api/reports/sales?period=today`, one for `week`, one for `month`) on mount — not "exactly one fetch." See D4 below. |
| Traceability | 1.0 | 1.0 — every REQ has ≥1 AC, every AC references a valid, existing REQ, no orphans | Verified full bidirectional mapping: REQ-001→AC-001 … REQ-013→AC-013 (1:1), REQ-014→AC-014/015/017/018, REQ-015/016→AC-016, REQ-017→AC-019/020, REQ-018→AC-021. Every REQ-XXX cited in `acceptance.md` exists in `spec.md §3`. No orphaned ACs, no uncovered REQs. |

**Aggregate (harmonic mean, per the skeptical-evaluation stance — not a plain average):** 4 / (1/1.0 + 1/1.0 + 1/0.75 + 1/1.0) = 4 / 4.333 = **0.92**. Exceeds the Tier L PASS threshold of 0.85.

## Task-Specific Verification (per the audit brief)

### 1. Do the 13 "already-delivered" requirements (REQ-001–013) match the code? — Verified, no REQ-level overclaiming found

All 13 were checked line-by-line against source, not assumed from `spec.md`'s own prose:

| REQ | Claim | Source verified | Match? |
|-----|-------|------------------|--------|
| REQ-001 | proxy orders, filter to today (UTC) | `orders.py:L11-14` — `today = datetime.now(timezone.utc).date()`, filters `_parse_date(o["created_at"]) == today` | Exact match |
| REQ-002 | proxy inventory, annotate `low_stock` vs `LOW_STOCK_THRESHOLD` (default 10) | `inventory.py:L11-14` — `threshold = int(os.environ.get("LOW_STOCK_THRESHOLD", "10"))`, `"low_stock": item["stock_quantity"] < threshold` | Exact match |
| REQ-003 | proxy reservations, forward `date`/`status` | `reservations.py:L10-12` — both forwarded to `list_reservations(date=date, status=status)` | Exact match |
| REQ-004 | proxy sales report, forward `period` | `reports.py:L8-10` — `sales_summary(period=period)`, default `"today"` | Exact match |
| REQ-005 | POST creates `pending` record, 201 | `approvals.py:L11-13` + `approvals_store.py:L51-64` | Exact match |
| REQ-006 | list filtered by `status`, sorted `created_at` desc | `approvals_store.py:L37-43` — `records.sort(key=lambda r: r["created_at"], reverse=True)` | Exact match |
| REQ-007 | PATCH pending → approved/rejected, 200 | `approvals.py:L29-32` + `approvals_store.py:L75-90` | Exact match |
| REQ-008 | PATCH on decided record → 409, no mutation | `approvals_store.py:L81-82` — `AlreadyDecidedError` raised before any field write | Exact match |
| REQ-009 | Basic Auth on all routes except `/health` via middleware | `auth.py:L29-44` + `main.py:L14` (middleware added before router registration) | Exact match |
| REQ-010 | 502 with user-facing message on proxy failure | `mock_pos_client.py:L20-28` — both `RequestError` and `HTTPStatusError` → `HTTPException(502, ...)` with Korean user-facing text | Exact match |
| REQ-011 | 5 tab screens, each fetches its `/api/*` route on mount, client-side tabs, no router | `App.tsx:L9-47` (5 `TABS`, `useState<Tab>`, no `react-router` import); all 5 page components use `useEffect(() => { api.X().then(...) }, [])` | Exact match — REQ-011's own wording ("each fetching ... on mount") holds; see Testability finding (D4) for a downstream AC-level overclaim |
| REQ-012 | persist approvals to bind-mounted `data/approvals.json`, survive restart | `approvals_store.py:L17` (`_DATA_FILE` env-configurable, default `/data/approvals.json`) + `docker-compose.yml` volumes: `./smb-dashboard/data:/data` | Exact match (see D3 for a modality-labeling nit, not a factual defect) |
| REQ-013 | 4th compose service, `depends_on: mock-pos`, `127.0.0.1:8652`, container `hermes-triagent-smb-dashboard-ui` | `docker-compose.yml` `smb-dashboard:` block — exact match on all four claims | Exact match |

Conclusion: **no REQ-001–013 overclaiming found.** The one overclaim discovered (AC-011's "exactly one fetch") lives in the verification layer (`acceptance.md`), not in the requirement text itself — see D4.

### 2. Are the 5 open-gap requirements (REQ-014–018) accurately scoped with testable ACs?

Confirmed accurately scoped:
- **Orders status filter (REQ-014–016)**: `orders.py:L10-14` has zero status-parameter handling; `mock_pos_client.py:L31-32`'s `list_orders()` takes no params; `api.ts:L69` (`todayOrders: () => request<Order[]>("/api/orders/today")`) takes no arguments; `OrdersPage.tsx` has no filter UI. The gap is real at all three layers named in `research.md §2`.
- **Proxy router test coverage (REQ-017–018)**: `smb-dashboard/backend/tests/` contains only `test_approvals.py` (confirmed via `ls`); `requirements-dev.txt` declares `pytest-httpx==0.30.0` as an already-present, currently-unused dev dependency (confirmed via `cat requirements-dev.txt` — zero grep hits for `httpx_mock` or `pytest_httpx` anywhere in `tests/`).

ACs for both gaps (AC-014–021) are binary-testable Given-When-Then scenarios with concrete expected values (specific status codes, specific query values, an explicit 85% coverage gate). One internal-consistency nit found in the supporting `plan.md` rationale (not in the REQ/AC text itself) — see D6.

### 3. Is "web vs Discord decision channel is not currently instrumentable" (spec.md §2.3) actually true?

**Confirmed true**, verified directly rather than taken on the SPEC's word:
- `approvals_store.py:L75` — `decide_approval(approval_id, status, reason, decided_by: str = "owner")` — the default is never overridden.
- `approvals.py:L30-32` — the router's only call site: `approvals_store.decide_approval(approval_id, payload.status, payload.reason)` — `decided_by` is never passed, so it is always `"owner"`.
- `models.py:L22-24` — `ApprovalDecision` (the PATCH request model) has exactly two fields, `status` and `reason` — no channel/source field exists to receive one even if a caller wanted to supply it.
- `.hermes/profiles/coordinator/skills/orchestration/task_dispatch_and_verification/SKILL.md:L61-62` — the Hermes-side Discord-sync PATCH call sends only `{"status": ..., "reason": ...}` — confirming the identical gap on the Discord-decided path.
- `docs/06-hitl-approval-design.md:L9-10` independently corroborates that the dashboard's approvals store is "처음으로 구조화된 REST 저장소" (the first structured REST store) — consistent with `spec.md`'s framing.

No code path anywhere in the repository threads a channel identifier through to `decided_by` or any other field. The claim is accurate, not overclaimed.

## Defects Found (structured defect-list)

D1. RQ-4-implementation-detail-leak — `spec.md:L104` (REQ-017) — REQ-017 names specific test-library implementation choices ("pytest coverage using `pytest-httpx`") directly inside a GEARS requirement, which should describe WHAT/behavior rather than HOW/tooling. — Severity: minor — Class: optional — Required fix: rephrase to describe required behavior only (e.g., "shall each have automated test coverage that mocks the underlying Mock POS HTTP calls at the happy-path and 502-translation paths"), leaving the specific library choice to `plan.md §D` (which already states it).

D2. RQ-4-implementation-detail-leak — `spec.md:L105` (REQ-018) — REQ-018 embeds an internal config-file path (`.moai/config/sections/quality.yaml constitution.test_coverage_target`) directly in the requirement text. — Severity: minor — Class: optional — Required fix: state the 85% figure as the requirement and move the config-path citation to a footnote or to `plan.md §D` (which already restates it at L30).

D3. GEARS-modality-mismatch — `spec.md:L93` (REQ-012, labeled "Where / capability-gate") — the trigger condition ("the smb-dashboard container is restarted") is a discrete event, not a capability-gate/feature-flag/static-config condition per the GEARS canonical definition of `Where` (M3 rubric). The REQ is syntactically GEARS-compliant (matches the `Where [condition], the <subject> shall [response]` template verbatim), so this does NOT trigger an MP-2 format failure, but the chosen modality is semantically mismatched. — Severity: minor — Class: optional — Required fix: reclassify as Event-driven ("When the `smb-dashboard` container restarts, the approvals store shall retain...") or as Ubiquitous ("The approvals store shall persist all records across container restarts by...").

D4. AC-overclaim — `acceptance.md:L19` (AC-011) — asserts every screen "issues exactly one fetch to its associated `/api/*` route" on tab click. Verified FALSE for the Sales Summary screen: `SalesSummaryPage.tsx:L15-23` issues three concurrent fetches (`Promise.all` over `today`/`week`/`month`) to `/api/reports/sales` on mount, not one. As literally worded, AC-011 would FAIL when run against the actually-delivered Sales Summary screen (or requires an un-stated generous reinterpretation of "one fetch" to mean "one fetch per period"). — Severity: major — Class: blocking — Required fix: reword AC-011 to state "issues at least one fetch to its associated `/api/*` route (Sales Summary issues one fetch per period: today/week/month)" or split out a Sales-Summary-specific AC that states the 3-request pattern explicitly, so the verification-layer claim matches the actually-delivered behavior it is meant to verify.

D5. Precision/overclaim (UI description) — `spec.md:L115` (§4 Screens table) and `design.md:L21` both describe the Approvals screen as having "approve/reject buttons + reason input." The actual implementation (`ApprovalsPage.tsx:L22-23`) captures the reason via a blocking native `window.prompt()` dialog, not an inline form field — a materially more primitive UX than "reason input" would normally suggest, and not listed among design.md's 3 named open design decisions despite being a real, visible design gap. — Severity: minor — Class: optional — Required fix: either add the `window.prompt()` mechanism to design.md's "Current Implementation Inventory" table as a 4th open design decision for `manager-design` to evaluate (replace with inline field, or keep), or amend `spec.md §4` to describe it precisely as "reason capture via browser prompt."

D6. Internal-consistency nit — `plan.md:L28` (§D Constraints) claims the new orders `status` parameter design ("a plain FastAPI query parameter with a `Literal` type constraint") is "matching the existing pattern in `reservations.py`." Verified FALSE: `reservations.py:L11` (`status: Optional[str] = None`) uses an unconstrained `Optional[str]` with no `Literal` type and no validation — it would accept and silently pass through any string, unlike REQ-014/AC-018's required 422-on-invalid-enum behavior. The two patterns are not the same. — Severity: minor — Class: optional — Required fix: correct `plan.md §D` to state the `Literal`-constrained validation is a NEW pattern (first use of this stricter style among the proxy routers), not a match to `reservations.py`'s existing unconstrained parameter, or drop the comparison entirely.

## Regression Check (Iteration 2+ only)

N/A — this is iteration 1.

## Recommendation

**Verdict: PASS** (aggregate score 0.92 ≥ Tier L threshold 0.85; all 7 must-pass criteria clear).

The SPEC is well-evidenced: its "already delivered" claims for REQ-001–013 were independently verified against source and hold exactly as stated, its two open-gap justifications (orders filter, test coverage) are grounded in real, confirmed absences in the code, and its "not currently instrumentable" Success Metrics claim about the web-vs-Discord decision channel was independently re-derived from `approvals_store.py`, `models.py`, and the Hermes coordinator skill and confirmed true.

Six minor-to-major defects were found (D1–D6), none must-pass-blocking. **D4 is the one item manager-spec should fix before treating this SPEC as final** — it is classified `blocking` because it is a verification-layer claim ("exactly one fetch") that is demonstrably false against the delivered Sales Summary screen and would produce a false AC failure (or force an un-stated reinterpretation) when the run phase actually exercises it. D1, D2, D3, D5, D6 are `optional` per M6 — surfaced for the orchestrator's discretion, not required before proceeding.

Numbered fix list (for a re-audit or direct correction, in priority order):
1. Fix `acceptance.md:L19` (AC-011) to accurately describe the Sales Summary screen's 3-fetch-per-period behavior (D4 — blocking).
2. Consider correcting `plan.md:L28`'s inaccurate comparison to `reservations.py`'s pattern (D6 — optional).
3. Consider adding the `window.prompt()` reason-capture mechanism to `design.md`'s open-decision list (D5 — optional).
4. Consider rewording REQ-012's modality label from `Where` to `When`/Ubiquitous (D3 — optional).
5. Consider removing the specific `pytest`/`pytest-httpx`/config-path literal citations from REQ-017/018 (D1, D2 — optional).

Verdict: PASS
