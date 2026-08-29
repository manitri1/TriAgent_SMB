# SPEC Review Report: SPEC-DASHBOARD-001
Stream: run-gate (Phase 1 Plan Audit Gate date-file — distinct from the plan-phase review-N stream)
Prior plan-phase review: `.moai/reports/plan-audit/SPEC-DASHBOARD-001-review-1.md` (iteration 1/3, PASS, score 0.92)
Verdict: PASS
Overall Score: 1.00

Reasoning context ignored per M1 Context Isolation. This gate check is based solely on `.moai/specs/SPEC-DASHBOARD-001/{spec,plan,acceptance,design,research,progress,spec-compact}.md` (Tier L — all 5 required artifacts present, plus progress.md and spec-compact.md), cross-referenced directly against the repository source (`smb-dashboard/backend/app/*`, `smb-dashboard/frontend/src/*`). The claim in the delegation prompt that D4 and D1–D6 were fixed during a Korean translation pass was NOT taken on trust — every claim below is independently re-derived from the current artifact text and, where applicable, from the actual source files.

## Why This Gate Check Was Necessary

Per the Plan Audit Gate skip-eligibility contract (`spec-workflow.md` § Phase 1 Plan Audit Gate), a skip requires (1) prior verdict PASS, (2) score ≥ tier threshold, AND (3) artifact-hash unchanged since that verdict. Condition (3) fails here: all plan artifacts were rewritten to Korean after iteration-1, so the plan-artifact hash changed. A fresh gate check is mandatory — this is that check.

## Plausible Failure Modes Checked (M2 pre-read list)

Translation-introduced factual drift (numbers, thresholds, field names silently altered in translation); REQ/AC identifier loss or renumbering during translation; broken GEARS pattern structure post-translation; frontmatter corruption; reintroduction of previously-fixed defects; new defects introduced by the edit pass; unresolved `[NEEDS CLARIFICATION]` markers; cross-SPEC / syscall D7/D8 concerns.

## Must-Pass Results

- [PASS] MP-1 REQ number consistency: `spec.md:L83-106` — REQ-001 through REQ-018, sequential, no gaps, no duplicates, consistent 3-digit zero-padding, identical numbering to iteration 1. `acceptance.md:L9-35` — AC-001 through AC-021, same consistency (verified via `grep -n '^\- \*\*REQ-'` / `'^\- \*\*AC-'` — 18 and 21 matches respectively, monotonically increasing).
- [PASS] MP-2 EARS/GEARS format compliance (requirement layer — `REQ-XXX` in `spec.md` only; `AC-XXX` Given-When-Then entries in `acceptance.md` are the correct verification-layer format and are NOT graded here): all 18 REQs still match a GEARS pattern after translation (Ubiquitous: REQ-001–004, 006, 009, 011, 013, 014, 016–018; Event-driven: REQ-005, 007, 012, 015; Event-detected/unwanted: REQ-008, 010). REQ-012 was reclassified from `Where` to `Event-driven` (`spec.md:L94`, "컨테이너가 재시작될 때... 승인 저장소는 ... 보존한다") — this is the D3 fix landing correctly, not a regression. No informal language, no Given-When-Then scenario presented as a REQ.
- [PASS] MP-3 YAML frontmatter validity: `spec.md:L1-15` — all 12 canonical fields present with correct types verified against `.claude/rules/moai/development/spec-frontmatter-schema.md`: `id`, `title` (quoted), `version: "0.1.0"`, `status: draft`, `created`/`updated: 2026-08-29`, `author: manit`, `priority: P1`, `phase: "v0.2.0 target"` (not a prohibited lifecycle token), `module: "smb-dashboard"`, `lifecycle: spec-anchored`, `tags:` (comma-separated). No rejected snake_case aliases. Optional `tier: L` present and consistent with the delivered 5-artifact Tier L set. `updated: 2026-08-29` correctly reflects the translation edit.
- [N/A] MP-4 Section 22 language neutrality: single-language project scope (Python/FastAPI + TypeScript/React for one application), not multi-language dev-tooling. Auto-pass per the single-language-scope exemption.
- [PASS] MP-5 D7 cross-SPEC reconciliation: `grep -Eo 'SPEC-([A-Z][A-Z0-9]+-)+[0-9]+' .moai/specs/SPEC-DASHBOARD-001/*.md` returns matches only for `SPEC-DASHBOARD-001` itself, across all 7 files. `ls .moai/specs/` shows only `SPEC-DASHBOARD-001/` — no other SPEC exists to reconcile against. No BLOCKING finding possible.
- [PASS] MP-6 D8 cross-platform discipline: `grep -c 'syscall' .moai/specs/SPEC-DASHBOARD-001/*.md` → 0 matches across all 7 files. Auto-PASS per D8-4.
- [PASS] MP-7 clarification gate: `grep -rn '\[NEEDS CLARIFICATION' .moai/specs/SPEC-DASHBOARD-001/plan.md .moai/specs/SPEC-DASHBOARD-001/research.md` → 0 matches (exit code 1, no hits).

**No must-pass failure. The M5 firewall does not block this SPEC.**

## Category Scores (0.0-1.0, rubric-anchored)

| Dimension | Score | Rubric Band | Evidence |
|-----------|-------|-------------|----------|
| Clarity | 1.0 | 1.0 — single unambiguous interpretation, measurable ACs | `spec.md:L83-106` (18 REQs with concrete values: `LOW_STOCK_THRESHOLD` default 10, exact HTTP codes, exact endpoint paths, preserved verbatim through translation); `acceptance.md:L9-35` (21 Given-When-Then ACs with concrete expected values). No pronoun-reference ambiguity found post-translation. |
| Completeness | 1.0 | 1.0 — all required sections + frontmatter present | HISTORY (`spec.md:L19-24`, now with a second row documenting the translation + D4/D1-D6 fix pass), WHY (`spec.md §2`), WHAT (`spec.md §1`, `§4`), REQUIREMENTS (`spec.md §3`, 18 REQs), ACCEPTANCE CRITERIA (`acceptance.md`, correctly externalized per Tier L two-layer architecture), Out of Scope (`spec.md:L118-136`, 5 distinct `### Out of Scope — <topic>` H3 sub-headings each with `-` bullets). Frontmatter complete (MP-3). |
| Testability | 1.0 | 1.0 — every AC binary-testable, no weasel words | **AC-011** (`acceptance.md:L19`) was re-verified directly against `smb-dashboard/frontend/src/pages/SalesSummaryPage.tsx:L16` — `Promise.all(PERIODS.map((p) => api.salesSummary(p.key)))` issues exactly 3 concurrent requests (today/week/month). AC-011 now states this precisely: "Sales Summary 화면은 예외적으로 ... 세 기간에 대해 `Promise.all`을 통해 동시에 3회 요청을 보내며, 그 외 네 화면 ... 각각 정확히 1회만 요청을 보낸다" — this is an exact, binary-testable match to the delivered code, closing D4. No weasel words ("적절한"/"합리적인"/"충분한" or equivalents) found scanning all 21 ACs. |
| Traceability | 1.0 | 1.0 — every REQ has ≥1 AC, every AC references a valid, existing REQ, no orphans | Full bidirectional mapping unchanged and intact post-translation: REQ-001→AC-001 … REQ-013→AC-013 (1:1), REQ-014→AC-014/015/017/018, REQ-015/016→AC-016, REQ-017→AC-019/020, REQ-018→AC-021. Every REQ-XXX cited in `acceptance.md` exists in `spec.md §3`. |

**Aggregate (harmonic mean, per the skeptical-evaluation stance):** 4 / (1/1.0 + 1/1.0 + 1/1.0 + 1/1.0) = **1.00**. Exceeds the Tier L PASS threshold of 0.85.

## Translation-Integrity Spot-Check (per the run-gate's explicit verification ask)

Re-verified a sample of the "already-delivered" REQs against actual source, independent of the Korean prose, to confirm translation did not silently drift the facts:

| REQ | Korean claim (translated) | Source re-verified this session | Match? |
|-----|---------------------------|----------------------------------|--------|
| REQ-001 | `GET /api/orders/today`는 오늘 UTC 날짜와 일치하는 주문만 반환 | `orders.py:L11-14` — `today = datetime.now(timezone.utc).date()`; filters `_parse_date(o["created_at"]) == today`. `grep -c "status" orders.py` → 0 (confirms REQ-014's "no status handling yet" gap claim still holds verbatim). | Exact match |
| REQ-002 | `LOW_STOCK_THRESHOLD`(기본값 10) 기준 `low_stock` 계산 | `inventory.py:L12-14` — `threshold = int(os.environ.get("LOW_STOCK_THRESHOLD", "10"))`; `"low_stock": item["stock_quantity"] < threshold`. | Exact match |
| REQ-009 | `/health` 제외 전체 라우트에 Basic Auth 미들웨어 강제 | `auth.py:L29-44` — `BasicAuthMiddleware.dispatch` exempts only `/health` (`L31-32`), returns 401 with `WWW-Authenticate: Basic` otherwise (`L44`, matches `UNAUTHORIZED_HEADERS` at `L18`). | Exact match |
| REQ-011 / AC-011 | 5 screens fetch on mount; Sales Summary is the 3-concurrent-fetch exception | `SalesSummaryPage.tsx:L16` — `Promise.all(PERIODS.map(...))` over 3 periods. | Exact match (re-confirmed independently this session, not carried over from iteration 1) |

No translation-introduced factual drift found in any sampled REQ/AC.

## Regression Check (against iteration-1 defects D1-D6)

- **D1** (RQ-4-implementation-detail-leak, REQ-017 named `pytest-httpx` in the requirement text) — **RESOLVED**: `spec.md:L105` REQ-017 now reads "각각 하위의 Mock POS HTTP 호출을 모킹하는 자동화된 테스트 커버리지를 가지며..." — no library name in the REQ text. The `pytest-httpx` citation moved to `acceptance.md:L33-34` (AC-019/020, the correct verification layer) and `plan.md:L15`.
- **D2** (RQ-4-implementation-detail-leak, REQ-018 embedded the `quality.yaml constitution.test_coverage_target` config path) — **PARTIALLY RESOLVED, not blocking**: `spec.md:L106` still carries "(목표치 정의: `.moai/config/sections/quality.yaml`의 `constitution.test_coverage_target`)" inside the REQ-018 sentence, now parenthetical rather than inline, but not fully moved to a footnote or exclusively to `plan.md §D` as the iteration-1 fix instruction suggested. This remains a cosmetic implementation-detail citation inside a GEARS requirement — it does NOT break the GEARS pattern match (REQ-018 still parses as Ubiquitous: "커버리지는 ... 충족한다" = "The `<subject>` shall meet..."), so it is not an MP-2 failure. Classified **optional / minor**, unchanged severity from iteration 1, does not block this gate.
- **D3** (GEARS-modality-mismatch, REQ-012 labeled `Where` for a restart event) — **RESOLVED**: `spec.md:L94` REQ-012 is now labeled `(Event-driven)` and phrased "컨테이너가 재시작될 때... 보존한다" ("When the container restarts... shall preserve"), matching the recommended fix exactly.
- **D4** (AC-overclaim, AC-011 falsely claimed "exactly one fetch" for all 5 screens) — **RESOLVED**: verified above, both textually and against `SalesSummaryPage.tsx` source. This was the one `blocking`-classified defect from iteration 1 and is the primary reason this gate check was required; it is now closed.
- **D5** (Precision/overclaim, Approvals screen's `window.prompt()` mechanism undocumented in design.md) — **RESOLVED**: `design.md:L33` now lists it explicitly as open design decision #4: "Approvals 화면의 사유 입력 메커니즘... 브라우저 네이티브 `window.prompt()` 블로킹 대화상자를 통해... `ApprovalsPage.tsx:L22-23`."
- **D6** (Internal-consistency nit, `plan.md` falsely claimed the new `status` filter pattern "matches" `reservations.py`) — **RESOLVED**: `plan.md:L28` now correctly states the `Literal`-constrained validation "differs from" `reservations.py`'s existing unconstrained `Optional[str]` pattern, and is "처음 적용되는 사례" (the first such stricter case), not a match.

**5 of 6 iteration-1 defects fully resolved; D2 partially resolved but remains optional/minor and does not affect the gate verdict.** No new defects introduced by the translation pass were found in this review.

## Defects Found (structured defect-list)

D1 (carried, downgraded). RQ-4-residual-implementation-detail — `spec.md:L106` (REQ-018) — the config-path citation `.moai/config/sections/quality.yaml`'s `constitution.test_coverage_target` remains embedded (now parenthetically) inside the GEARS requirement text rather than moved fully to `plan.md §D` or a footnote as iteration-1's D2 recommended. — Severity: minor — Class: optional — Required fix (optional, non-blocking): drop the parenthetical from REQ-018 entirely; `plan.md:L30` already restates the 85% target and its config source.

No blocking defects found.

## Recommendation

**Verdict: PASS** (aggregate score 1.00 ≥ Tier L threshold 0.85; all 7 must-pass criteria clear; no unresolved BLOCKING finding).

This SPEC is cleared to proceed past the Phase 1 Plan Audit Gate into the design → run route (per the UI-surfaced conditional route declared in `spec.md`'s header note and `design.md`). The translation pass held up under independent scrutiny: REQ/AC identifiers, numbering, and GEARS structure survived intact, no factual drift was introduced into any of the four independently re-sampled REQ/AC pairs, and the one `blocking`-classified defect from iteration 1 (D4, AC-011's false "exactly one fetch" claim) is now demonstrably accurate against the actual `SalesSummaryPage.tsx` implementation. The residual D2 citation-placement nit is optional and does not gate implementation.

Verdict: PASS
