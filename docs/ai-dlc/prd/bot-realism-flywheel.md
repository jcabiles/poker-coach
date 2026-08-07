# PRD — bot-realism-flywheel (rev 2, post dual review 2026-08-05)

Owner-approved direction 2026-08-05. Living hypothesis, not a frozen contract. Companion
roadmap: `../roadmap/bot-realism-flywheel.md` (rev 2). Review adjudication:
`../ledger/bot-realism-flywheel-roadmap-review.md`.

## 1. Context & problem

The villain bots run on a dial architecture (levers × merit tables over versioned `content/`
packs — NOT a simple 5-dim box: coupled optional levers, frozen references, sizing
distributions, per-node overrides, preflop mix tables; see
`backend/app/domain/content/models.py`). The 2026-08-05 re-measure
(`docs/ai-dlc/research/persona-realism-artifacts/remeasure-2026-08-05/SYNTHESIS.md`) scored
the roster **4.8/10** after a week of persona-fix work that started at 4.2. Root problems:

- **Iteration is priced in agent fleets** — each fix→measure loop costs token-millions.
- **The architecture's ceiling is unknown** — further tuning may be climbing toward ~5.5.
- **Targets are soft** — literature bands, not measured human play; and the saturated 1–10
  archetype ratings no longer measure "would a human believe this is a person."

Why now: the owner halted all persona-fix work pending a ceiling verdict; the work doubles as
analytics/DS portfolio evidence (poker-analytics) during an active job search.

## 2. Goal & non-goals

**Goal:** a calibration **flywheel** — computable realism score + seeded sweep harness +
preregistered detection protocol — that (a) prices any candidate bot change in **minutes of
compute, zero tokens**, and (b) delivers an **operational-ceiling verdict (REACHABLE /
NOT-REACHABLE / INCONCLUSIVE, within a declared search space and compute budget) with
mechanism diagnosis**, feeding the phase-3 fix-vs-overhaul gate.

**Non-goals:** no persona-fix code or committed pack changes; no architecture rebuild; no
stack-size gameplay; no corpus ingestion before the NLHE gate clears; no per-decision-LLM
policy; no solver tables; no detection optimization outside the Goodhart constraint set
(roadmap north-star section).

## 3. Affected files / interfaces

- **poker-coach (producer):** `backend/tools/export_analytics.py` extended for batch runs
  driven by a **versioned counterfactual-config schema** (ephemeral override layer validated
  through the real pack model — "read-only" means no COMMITTED production-value changes;
  validated temporary counterfactuals are the sweep mechanism). Measurement reference:
  `remeasure-2026-08-05/stage0.py` (post-Sol-A remediation).
- **poker-analytics (judgment):** scorer package + target registry + stat-battery models +
  methodology docs (+ eventually the corpus). Pattern: the PR #161 producer/consumer split.
- **Interface:** the export contract extended with a batch manifest (engine sha · seed ·
  config hash · scorer version · target-registry version · row counts).

## 4. Requirements

- **R0 — methods & estimand contract** (S2a; BLOCKS the design of R1–R4). One dual-reviewed
  doc: search-space & estimand contract (swept parameters, bounds, coupled constraints,
  persona treatment, the REACHABLE/NOT-REACHABLE/INCONCLUSIVE rule, operational-ceiling
  framing) · target registry (per-stat definitions, source compatibility, uncertainty,
  confidence grades; graded distance, covariance-aware weights — no hard in/out cliffs) ·
  counterfactual-config schema · detection-protocol preregistration (judgment unit, exposure
  length, balanced priors, matched information, balanced accuracy/AUC/d′, leak controls,
  cluster-aware CIs) · score-validation plan (below) · compute budget with a one-config
  benchmark. Consumes the DS-methodology research lane.
- **R1 — realism score v0.** A TWO-TIER score, both tiers graded distances over the R0
  registry: a pool-level (table-wide) score that is the verdict's ONLY anchor, plus a
  per-persona tier that is **reported, never gating** — avg = the progress metric, floor =
  worst persona = a non-gating diagnostic. (**The per-persona gate was deleted by owner
  ruling 2026-08-06**: the binding-bounds analysis showed it could only ever bind on PFR
  and 3-bet, so a constraint that reads as protection without being any was removed rather
  than shipped. The R0 constraint set keeps its five rules.) AC:
  deterministic given seed; <5 min per 50k-hand run; validation executed per the R0 plan
  as amended — the validation legs run on the PER-PERSONA score —
  where the n=12 persona-level expert ratings (6 personas × 2 campaigns; the table-level
  rating is excluded as a different unit) are **directional-only**: report Spearman ρ with
  CI and p-value plus a tie-corrected Kendall τ-b concordance leg, each requiring the
  correct sign. **Validation is pre-labeled RETROSPECTIVE face-validity** (owner ruling
  2026-08-06) — outcomes are `retrospective-pass` / `retrospective-fail`, and
  "confirmatory" is reserved for a future campaign whose ratings are collected fresh and
  blind to scores. At most ONE pre-registered revision; on failure the **stop-gate**
  fires: the score remains an "exploratory surrogate," R3 may not issue a score-only verdict,
  and convergent evidence (R4 pilot) is required. **Until validation passes, scores are
  non-authoritative for any conclusion** — R2 may use them only as reproducibility smoke data
  (this sentence is mirrored in the roadmap).
- **R2 — batch sweep runner.** N configs (R0 schema) → N seeded runs → N scores, one command,
  manifest-pinned. AC: same (seed, config) reproduces identical scores; one-config benchmark
  recorded against the R0 compute budget.
- **R3 — reachability study.** Pilot response surface over the R0-declared space + DoE-style
  mechanism probes (per-dial and interaction effects for each failing stat) + winner's-curse
  guard (top configs re-run on fresh seeds before any "reachable" claim). AC: verdict doc per
  the R0 estimand contract, verdict ∈ {REACHABLE, NOT-REACHABLE, INCONCLUSIVE}, framed as an
  operational ceiling, dual-adversarially reviewed. Confirmatory study only if the pilot is
  ambiguous (appetite valve).
- **R4 — detection feasibility pilot.** The R0-preregistered protocol executed once: mixed
  corpus of bot seats + the owner's live HERO hands as the v0 human class. AC: result
  reported as a SINGLE-PLAYER PILOT, with the single-subject / session / opponent-composition
  biases and their expected direction of effect named in the write-up; judges see opaque IDs
  only. **Explicitly NOT the north-star baseline** — the multi-player baseline and the
  owner's target are a roadmap NEXT item.
- **R5 — research dossiers.** Three lanes in session R (academic incl. Alberta CPRG lineage ·
  commercial practice · NLHE-corpus gate brief ending GO/PARTIAL/NO-GO with licensing
  assessment) PLUS a consumption map: each conclusion → scorer / sweep methodology /
  detection protocol / architecture option / corpus decision / explicitly-rejected, with an
  evidence grade. (The DS-methodology lane moved into R0.)
- **R6 — cross-repo working agreement.** Ownership manifest, interface contract, versioning
  rules, two-parallel-session protocol (session R docs-only/no-git; session F owns code,
  worktree-isolated), S6∥S5 scheduling note. AC: doc in both repos; walking-skeleton scorer
  stub invoked from poker-coach end-to-end against the sim50k export.

## 5. Constraints

- ✅ **Always:** seeded, reproducible sims · every artifact manifest-pinned (engine sha ·
  seed · config hash · scorer version · target-registry version · dependency lockfile ·
  artifact checksums) · targets from external human evidence only · scripts replay
  `state_json`/Parquet, never rendered text · methodology + limitations documented in the
  portfolio repo as it happens (dataset/model cards at publication).
- ⚠️ **Ask-first:** new backend dependencies · export-contract version bumps · anything
  touching bot-policy code or committed pack values · making any repo public · downloading
  any external dataset (licensing review first).
- 🚫 **Never:** per-decision-LLM bot policy (real-time + ~500 hands/sec sim throughput) ·
  persona-fix changes before the phase-3 gate · corpus data in poker-coach · unlicensed data
  anywhere public · solver tables · detection optimized outside the Goodhart constraint set.

## 6. Milestones

| # | Objective | Output | Done-check |
|---|---|---|---|
| M1 | Working agreement + skeleton (R6) | contract doc ×2 repos + stub scorer wired | stub runs end-to-end from poker-coach |
| M2 | Methods & estimand contract (R0) | the S2a contract doc | dual review passed; downstream slices cite it |
| M3 | Research wave (R5, parallel session) | 3 dossiers + consumption map | GO/PARTIAL/NO-GO stated; map complete |
| M4 | Score v0 + validation (R1) | scorer + validation report | plan executed; status (validated/surrogate) recorded |
| M5 | Sweep runner (R2) | batch CLI + manifests | smoke batch reproducible; benchmark recorded |
| M6 | Operational-ceiling verdict (R3) | ceiling report + diagnosis | dual review passed; verdict ∈ 3 outcomes |
| M7 | Detection pilot (R4) | protocol run + pilot write-up | biases named; blinding held |

Appetite CAP: ~2–3 weeks part-time to the phase-3 gate; scope valves (roadmap) fire in
declared order rather than the gate slipping.

## 7. Verification (end-to-end)

One command drives config-batch → sim → scores → reachability report on pinned inputs; the
validation artifact reports ρ + CI + p + sign agreement and the score's resulting status; the
detection pilot write-up names its biases; all dossiers + consumption map delivered with the
NLHE gate verdict; and `git diff` over `backend/app/domain/` + `content/` is EMPTY across the
whole initiative (the no-fix boundary held — ephemeral counterfactuals never commit).
