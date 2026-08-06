# Ledger — flywheel-s2a (spec + contract reviews)

## Spec dual review (2026-08-05)

Reviewers over spec rev 1: Claude `refuter` (sonnet/high) → **NEEDS-WORK** (1 HIGH / 2 MED /
1 LOW); Codex `gpt-5.6-sol` (high) → **FAIL** (7 HIGH / 3 MED). Complementary, no conflicts.
Adjudicator: director. All folded into **spec rev 2**; zero rejections. Sol's FAIL
adjudicated fold-and-revise (every defect maps to a rev-2 change; none attacks the slice).

| # | src | sev | finding (compressed) | adjudication |
|---|-----|-----|---|---|
| 1 | ref | HIGH | Self-containment vs never-push SYNTHESIS citation contradiction. | **ACCEPT.** Constraints: remeasure numbers reproduced inline (value + adjudication status), never cited by pointer; internal jargon glossed portfolio-neutral. |
| 2 | ref | MED | P2 memo had no forced landing zone or verify check. | **ACCEPT.** P2 output committed; conclusions must land in (a)/(b)/(d)/(e) with margin citations; verify 8 spot-checks 5. |
| 3 | both | MED | Registry could pass verify-by with easy stats, skipping known failure points. | **ACCEPT.** (b) coverage floor: every remeasure defect-family stat present or per-stat justified; verify 3. |
| 4 | ref | LOW | Benchmark-scope gloss mislabeled as roadmap-sourced. | **ACCEPT.** Moved to provenance para, marked author interpretation. |
| 5 | sol | HIGH | LLM panel silently changed the north-star estimand (human construct); "true-baseline NEXT item" mislabeled (it concerns human hands, not judges). | **ACCEPT-NARROWED.** No estimand change: (d) defines the protocol for human judges (the construct); the S6 pilot executes it with an LLM SURROGATE panel (the owner's decision, correctly scoped to the pilot), gap + bias direction disclosed; NEXT-item reference corrected. |
| 6 | sol | HIGH | LLM-panel preregistration methodologically incomplete (pins, prompts, decoding, aggregation, correlated judges, AUC validity needs continuous response…). | **ACCEPT.** Full enumerated parameter list added to (d). |
| 7 | sol | HIGH | Goodhart constraint set (accepted roadmap-review remedy) absent from S2a. | **ACCEPT.** Operationalized constraint set forced into (a); verify 2. |
| 8 | sol | HIGH | "Reachable" lacked an executable statistical decision rule (tolerance, uncertainty, multiplicity, coverage, NR-vs-INCONCLUSIVE, winner's curse). | **ACCEPT.** All forced into (a); verify 2. |
| 9 | sol | HIGH | Score-validation pass/fail undefined (discretionary stop-gate); leave-one-out promise (roadmap ledger row 28) dropped. | **ACCEPT.** (e): composite pass rule, α/CI/threshold, leave-one-out, allowed revision content; verify 6. |
| 10 | sol | HIGH | P1 columns insufficient for the real config model (unbounded scalars, simplexes, first-match structures, frozen refs, absence-vs-null, shadowing). | **ACCEPT.** P1 column list extended (active predicate, semantic domain, structural-vs-numeric, disposition + rationale, canonical parameterization, validation path). |
| 11 | sol | HIGH | Counterfactual schema too thin to gate S4 (versioning, allowed paths, unknown-field rejection, merge/null semantics, frozen fields, canonical hash). | **ACCEPT-NARROWED.** Full requirements list + two worked paper examples in (c); runnable validator stays S4's first ticket with its acceptance test stated in the contract. |
| 12 | sol | MED | Target-evidence work unplanned; covariance-aware weighting hollow without a source or fallback. | **ACCEPT.** P2 gains the evidence half (per-stat source inventory + adjudication); (b) names covariance source or preregistered shrinkage/fallback. |
| 13 | sol | MED | Benchmark couldn't justify N (stub-only pipeline, no reps/variance/manifest/reserve). | **ACCEPT-NARROWED.** (f): ≥3 reps incl. full ingestion gate, mean+variance, hardware manifest, safety factor, S3-scorer uplift allowance (<5 min PRD bound), confirmatory reserve. |
| 14 | sol | MED | Verify-by hollow: "review ran" ≠ "review passed" (PRD M2); P1/P2 artifacts absent from file list. | **ACCEPT.** P5/verify 9 require PASS (every HIGH closed or owner-adjudicated); P1/P2 outputs added to files-touched + verify 8. |

Owner-decision checks (both reviewers): doc location, 8h cap consistent with roadmap/PRD;
LLM-panel ruling preserved but re-scoped as pilot surrogate (finding 5).

## Contract dual review (P5) — PASSED at v2.3 after 4 rounds (2026-08-05)

Reviewers: Claude `refuter` (sonnet/high) + Codex `gpt-5.6-sol` (high). Director
adjudicated; every finding accepted or accepted-narrowed; zero rejected as invalid.

**Round 1 (v1.0):** refuter FAIL (3 HIGH / 3 MED / 3 LOW) + Sol FAIL (12 HIGH / 2 MED).
Drivers: D(x) max-vs-covariance mathematically undefined; registry supplied words where
the formula needs numbers; pool-target-per-persona would drive the roster bland;
NOT-REACHABLE conditioned on screening axes the schema forbids (unsatisfiable); simplex
DoF undercount; superimposed wave contradicted the independent-persona estimand;
elasticity block unrepresentable by the schema; Goodhart floors not executable +
determinism guard missing; single-human-cluster CI impossible; panel/prompt/aggregation
unpinned; permutation exchangeability violated; tie-blind sign agreement; post-hoc
revision rule; false budget margins; fabricated memo attribution of the c=3.0 cutoff.
→ **v2.0 full redesign**: joint Mahalanobis D with χ² reference; pool-level primary
estimand + per-persona directional checks; one-persona-at-a-time waves; numeric
σ_target/σ_disc registry; ordinal rows out of D; nearest-centroid label preservation +
determinism guard; conditional-on-player bundle bootstrap; pinned prompt/panel/
aggregation; persona-label exact permutation; deterministic pinned revision; honest
parallel-required budget.

**Round 2 (verification of v2.0):** refuter NEEDS-WORK — headline: SIMULATED the exact
720-permutation null and proved the new ρ≥0.60 floor vacuous (exact critical ≈0.73 for
the assumed layout); also nights inconsistency, M4.9 citation. Sol FAIL — χ²₁₀ percentile
is 26.61 not 25.9; plug-in-Σ approximation must be disclosed; **Morris/Sobol are
design-incompatible with an LHD sample**; d = 11–13 not 12–15; counts, units, x-refs,
vendor pinning, revision wording. → **v2.1/v2.2**.

**Round 3:** refuter **PASS** (independently recomputed χ² quantile 26.611/5.1586 —
exact match; one LOW: SRRC provenance → fixed). Sol FAIL on five narrowed items, incl.
the round's sharpest catch: **any pre-stated permutation critical value is
score-layout-dependent and therefore false** (counterexample layouts 0.61–0.67) — a
direct CONFLICT with the refuter's 0.7316-based PASS, adjudicated in Sol's favor: the
contract now preregisters the PROCEDURE and reports realized criticals at validation
time. Also: truncated-simplex endpoints, SRRC materiality/adequacy thresholds, hard run
caps, full URLs. → **v2.3**.

**Round 4:** Sol **PASS** (simplex vertex arithmetic min(0.90, 1−(k−1)·0.05); URLs;
≤5 nights at floor counts / ≤6 at the 1,500-run cap — all confirmed).

**Outcome:** contract v2.3 PASSED dual adversarial review — every HIGH closed with
evidence, one reviewer-vs-reviewer conflict surfaced and adjudicated (recorded above),
per the PRD M2 "dual review passed" bar.
