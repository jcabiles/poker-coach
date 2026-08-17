# Spec — flywheel-s2a: methods & estimand contract (rev 2, post dual spec review)

Slice S2a of `../roadmap/bot-realism-flywheel.md` (PRD R0). BLOCKS the design of S3–S6.
**Rev 2 folds the dual spec review** (refuter NEEDS-WORK + Codex Sol FAIL; adjudication:
`../ledger/flywheel-s2a.md`). Provenance: payload from the roadmap S2a entry; owner interview
2026-08-05 settled: dual review ON (spec AND contract) · doc lives in **poker-analytics**
(`docs/methods/estimand-contract.md`) · compute cap = **overnight ≈8h** per sweep batch ·
**S6 pilot judges = LLM panel** (see D-d below for how this respects the human-construct
north star). The benchmark-scope reading ("running existing tools to time them is
measurement, not implementation") is the spec author's interpretation of the roadmap's
no-implementation no-go, supported by the roadmap itself requiring a one-config benchmark.

## Goal (one line)

One dual-reviewed document that pins, before any scorer/sweep/detection code exists: what is
swept, what "reachable" means (as an executable decision rule), what the targets are, how
detection is measured, and how the score gets validated — so S3–S6 build against a
preregistered contract instead of improvising methodology.

## Problem & outcome-link (from the roadmap)

Score/sweep/detection specs were being written before the methodology that must shape them;
"dial space" and "reachable" are undefined against a config model that is NOT a 5-dim box.
Outcome-link: trustworthiness of the ceiling verdict. Appetite: 3–4 days. No-gos: no
implementation.

## Deliverable — the contract doc (poker-analytics `docs/methods/estimand-contract.md`)

Six sections. Each bullet below is a FORCING requirement (verify-by checks them):

- **(a) Search-space & estimand contract.**
  - Swept parameters + bounds + coupled constraints from the real config model (per P1's
    inventory — see the P1 column list; unbounded scalars get declared sweep bounds,
    simplex-valued distributions get a canonical parameterization, frozen references and
    structural fields get an explicit sweep/freeze/exclude disposition with rationale).
  - Persona joint-vs-independent treatment AND the S1-carried flag: duplicate personas
    across seats — pooled vs per-seat (S1's stub pooling is precedent, not a decision).
  - **Executable decision rule** for REACHABLE / NOT-REACHABLE / INCONCLUSIVE: tolerance
    (ROPE-style band per stat, consistent with (b)'s graded distance), uncertainty rule
    (how seed noise and CI width enter), multiplicity treatment, minimum search-coverage
    criterion, what evidence separates NOT-REACHABLE from INCONCLUSIVE, and the
    winner's-curse guard (fresh-seed re-runs) incorporated as a precondition of any
    REACHABLE verdict. Verdict framed as *operational ceiling within declared space and
    compute budget*.
  - **Goodhart constraint set operationalized** (roadmap north-star section): archetype-
    separation floor (blind-ID must stay high), poker-legality/red-flag limits, coaching
    usefulness, runtime/reproducibility budgets — stated as measurable side constraints a
    candidate config must satisfy for its verdict to count.
- **(b) Target registry.** Per-stat: numerator/denominator, source, population/format
  compatibility, uncertainty, confidence grade; graded distance + covariance-aware
  weighting with a NAMED covariance source or a preregistered shrinkage/fallback rule when
  joint data doesn't exist (VPIP/PFR/gap are known-dependent — theory contract §
  independence warnings carry over); NO hard in/out cliffs. **Coverage floor:** the registry
  must cover every stat family named as a defect family in the 2026-08-05 remeasure
  (calldown looseness, raise-merit, sizing ecology, determinism/variance, preflop identity)
  or justify each omission per stat. Targets from external human evidence only.
- **(c) Counterfactual-config schema.** Versioned; allowed override paths; unknown-field
  rejection; merge semantics (base pack + override); null-vs-absent behavior; immutable/
  frozen fields (e.g. the frozen continue reference) and what happens on attempted override;
  validation-after-merge through the real pack model; canonical serialization + config
  hashing. Includes a WORKED EXAMPLE (one valid counterfactual, one frozen-field violation
  with its expected rejection) — on paper, traced against `models.py` semantics; the
  runnable validator is S4's first ticket and the contract states the acceptance test S4
  must pass.
- **(d) Detection-protocol preregistration.** The estimand stays the PRD's human construct
  ("would a human believe this is a person"); the preregistered protocol is defined for
  human judges. The **S6 pilot executes it with an LLM panel as SURROGATE judges** (owner
  decision: cheap, blind-able; the owner cannot blind-judge his own hands), with the
  surrogate-vs-construct gap and its expected bias direction disclosed, and human-judge
  execution named as the upgrade path (alongside — not identical to — the multi-player
  human-baseline NEXT item, which concerns human HANDS). Protocol must pin: judgment unit,
  exposure length, balanced priors, matched information, statistic (balanced accuracy/AUC/
  d′ — with a calibrated continuous/confidence response elicited so AUC/d′ are valid), leak
  controls, cluster definition + cluster-aware CIs; and for the LLM panel specifically:
  model+version snapshots, exact prompts, decoding settings, retry/missing-response rules,
  confidence elicitation, panel aggregation rule, and cross-model dependence handling
  (shared-ancestry correlation — judges are not independent).
- **(e) Score-validation plan.** n=13 expert ratings are directional-only. Preregistered:
  Spearman ρ with CI method named, α, p-value; sign-agreement check with its threshold; the
  COMPOSITE pass rule (what combination passes); leave-one-out on the 13 points where
  usable (roadmap-review ledger row 28 promise); at most ONE pre-registered revision with
  ALLOWED revision content stated in advance; on failure the STOP-GATE fires verbatim
  (score stays "exploratory surrogate", S5 may NOT issue a score-only verdict, convergent
  detection evidence required).
- **(f) Compute budget.** Owner cap: one sweep batch ≤ **overnight (~8h)**. Benchmark
  protocol: ≥3 repetitions of one full config — 50k-hand seeded export + **full ingestion
  gate (`make validate`)** + stub scorer — wall-clock mean+variance, hardware/software
  manifest recorded; N derived with a stated safety factor, an uplift allowance for the
  real S3 scorer (bounded by its <5 min PRD acceptance), and a reserve for confirmatory
  fresh-seed re-runs (winner's-curse guard).

## Work phases

1. **P1 — config-model inventory (read-only).** Every tunable surface in
   `backend/app/domain/content/models.py` + shipped packs. Columns: name · type ·
   bounds/domain (semantic, not just type-level) · active predicate (when does it apply) ·
   structural-vs-numeric · coupling/constraints (incl. ordering/shadowing, absence-vs-null) ·
   personas using it · sweep/freeze/exclude disposition + rationale · canonical
   parameterization (for simplex/distribution values) · validation/read path.
   **Output: committed facts table** — section (a)'s substrate.
2. **P2 — methodology + evidence research memo.** Two halves, each conclusion
   evidence-graded: (i) methods — simulator calibration, DoE/response-surface for mechanism
   probes, detection statistics, small-n validation; (ii) **target evidence** — inventory +
   adjudication of the actual human-evidence sources per registry stat (theory-contract
   targets as INPUT, external-evidence-only rule enforced; low-confidence flags carried).
   **Output: committed memo; conclusions must land in sections (a), (b), (d), (e) — the
   doc's margins cite which memo conclusion each design choice came from.**
3. **P3 — one-config benchmark** per (f)'s protocol.
4. **P4 — draft the contract** (consumes P1–P3).
5. **P5 — dual adversarial review** (refuter + Codex Sol) of the finished contract;
   adjudicate; **review must PASS: every HIGH closed or explicitly owner-adjudicated** —
   "review ran" is not sufficient (PRD M2: "dual review passed").
6. **P6 — land:** owner commits the doc in poker-analytics; poker-coach worktree commit
   (`feat/flywheel-s2a`) for the pointer + roadmap + ledger + P1/P2 artifacts.

## Files touched (exhaustive)

| Repo | File | Action |
|---|---|---|
| poker-analytics | `docs/methods/estimand-contract.md` | new (owner commits) |
| poker-coach | `docs/ai-dlc/research/flywheel-s2a/config-inventory.md` | new (P1 output) |
| poker-coach | `docs/ai-dlc/research/flywheel-s2a/methods-evidence-memo.md` | new (P2 output) |
| poker-coach | `docs/ai-dlc/START-HERE.md` | add one reading-order line |
| poker-coach | `docs/ai-dlc/roadmap/bot-realism-flywheel.md` | S2a `[x]` after pass/fail verified |
| poker-coach | `docs/ai-dlc/ledger/flywheel-s2a.md` | new (spec + contract review adjudications) |

## Out of scope (explicit)

No scorer, sweep-runner, or detection code (S3/S4/S6). No machine-readable registry/schema
files (specified in the doc; implementation is S3/S4's first tickets, each with its
acceptance test stated in the contract). No corpus work. No changes under
`backend/app/domain/` or `content/`. No S2b lanes (academic/commercial/corpus — session R).
No pack edits — P1 is read-only. No estimand change: the human construct stays the north
star; the LLM panel is the pilot's surrogate execution, not a redefinition.

## Constraints (profile + PRD §5 + working agreement)

- **Self-containment rule:** the contract is portfolio-track. Numbers sourced from the
  remeasure are REPRODUCED INLINE (value + adjudication status), never cited by pointer —
  SYNTHESIS is a never-push local artifact an external reader cannot access. Internal
  jargon (S3/S5, phase-3 gate) is glossed in portfolio-neutral language; stop-gate and
  operational-ceiling language still matches the roadmap/PRD where quoted.
- Never parse rendered hand text; targets from external human evidence only.
- Git: poker-coach commits via worktree; poker-analytics commit owner-performed; never
  sweep foreign riders.

## Verify-by (end-to-end)

1. `docs/methods/estimand-contract.md` exists with sections (a)–(f); PRD R0's bullet list
   diffs clean against the doc (every R0 item has a home).
2. Section (a) contains the executable decision rule (tolerance, uncertainty, multiplicity,
   coverage criterion, NOT-REACHABLE vs INCONCLUSIVE conditions, winner's-curse
   precondition) AND the operationalized Goodhart constraint set AND the pooled-vs-per-seat
   ruling.
3. Section (b) meets the coverage floor (all remeasure defect-family stats present or
   per-stat justified) and names its covariance source or fallback rule.
4. Section (c) contains the full schema requirements list + the two worked examples.
5. Section (d) preserves the human construct as estimand, frames the LLM panel as pilot
   surrogate with bias direction, and pins every enumerated panel parameter.
6. Section (e) states the composite pass rule, α/CI/threshold, leave-one-out, allowed
   revision content, and quotes the stop-gate.
7. Section (f) reports ≥3 benchmark repetitions (mean, variance, hardware manifest) and
   derives N with safety factor + confirmatory reserve, under the 8h cap.
8. P1 facts table and P2 memo exist as committed artifacts; the contract's design choices
   cite memo conclusions (spot-check 5 citations resolve).
9. Dual review of the contract PASSED (every HIGH closed or owner-adjudicated), recorded in
   `docs/ai-dlc/ledger/flywheel-s2a.md`.
10. `git diff` (range + working tree) over `backend/app/domain/` + `content/` empty;
    roadmap S2a `[x]` only after 1–9; owner has committed the doc in poker-analytics.
