# Delta spec — S5: reachability study + operational-ceiling verdict (rev 3, post dual review)

Slice S5 of `../roadmap/bot-realism-flywheel.md` (NOW lane). Gate 1 confirmed 2026-08-08.
Rev 3 folds all accepted findings from the dual review (Claude refuter: 6; Codex Sol: 13;
ledger `../ledger/flywheel-s5.md` has every finding + disposition).
Contract map: `../contracts/flywheel-s5.md` (READ FIRST).
Governing preregistration: `poker-analytics:docs/methods/estimand-contract.md` §a.4/§a.5/
§a.6/§f/§g.1.6/§g.1.7. **S3's stop-gate is spent: the realism score is
exploratory-surrogate and S5 may NOT issue a score-only verdict.**

## Goal (one line)

Execute the §a.6 three-stage design over the declared axis space and deliver a
dual-reviewed verdict — **REACHABLE / NOT-REACHABLE / INCONCLUSIVE** — on whether any
declared-space config reaches human-band behavior, framed strictly as an
operational-ceiling-within-declared-space claim.

## Owner rulings — RULED 2026-08-08 (Gate 2 approved same day)

**R1 ruled: benchmark fewer workers first.** Owner also stated speed itself is not a
priority ("open to just letting the simulations run longer") — so if the 3-worker
benchmark fails to clear 350 hands/sec, the fallback preference is serial execution
(passes rule 5 honestly; ~7.5 nights; the 6-night §f escalation simply surfaces and the
owner accepts it) or amendment (c), decided at that fork. The rule itself stays: it is
an engine-health guard (an abnormally slow batch flags pathological engine states, making
that batch's data suspect), not a throughput preference.

**R2 ruled: amend to 5 fresh seeds × 10 configs.** Pre-study §g amendment to be recorded
in the estimand contract BEFORE wave 1 (+20 runs; budget table's parenthesized figures
now govern: total 1,193–1,412 of the 1,500 cap).

Original ruling context (retained for the record):

**R1 — runtime constraint vs parallel sweeps (review finding, code-verified).** §a.5
rule 5 requires ≥350 hands/sec measured from each batch's own `_TIMING.json`
(`constraints.py`); under the 5-worker loaded sweep the measured rate is ~230–257
hands/sec — **every loaded batch would fail rule 5 and nothing could ever be NROY.**
Options: (a) drop to fewer workers until per-batch rate clears 350 (throughput cost
unknown — needs a one-evening benchmark first); (b) serial exports (≈413 hands/sec,
passes — but ≈7.5 nights, breaching the 6-night escalation threshold); (c) record a §g
amendment redefining rule-5 evidence as an unloaded benchmark of the pinned (engine sha,
config) rather than the loaded batch's own timing. Recommendation: benchmark (a) first;
if 3 workers clears 350 at ≥1.8× speedup, take (a); else (c) with the amendment recorded
before wave 1.

**R2 — confirmation seeds: the contract contradicts itself (review finding,
code-verified).** §a.4 re-estimates each finalist's Σ_sim from "≥3 fresh-seed runs" and
§f pins "exactly 3 seeds × exactly 10 configs unless amended" — but §a.3's own floor
(enforced in `covariance.py:147-149`) refuses Σ_sim from fewer than **5** replicates.
3-seed confirmation is unexecutable as preregistered. Recommendation: record a §g
amendment (pre-study, before any wave) setting confirmation to **5 fresh seeds × 10
configs** (+20 runs, budget still fits — see table); the alternative (a 3-replicate
covariance mode) would violate §a.3 and touch scorer code.

## Owner decisions (Gate 1, 2026-08-08)

1. Overnight sweep waves are **owner-launched** (S6-checklist style). Agents never start
   an 8-hour run unprompted.
   *Amended 2026-08-09 (owner ruling): waves run one per invocation (~2.0–2.5h each),
   not batched into overnight blocks — the owner cannot reliably leave the machine awake
   that long. Owner-launched is unchanged and is the load-bearing half of this decision.
   Execution-schedule only: no pin, seed, config, run count, or §f figure moves. Runbook:
   execution checklist §3.1.*
2. New statistics layer lives in **poker-analytics** (`analysis/` + Makefile targets);
   wave specs + launch checklist in poker-coach.
3. **Mechanism-probe config path DEFERRED** — built mid-slice (≈0.5 day) only if stage
   results put NOT-REACHABLE in play. **Named tension:** the roadmap's S5 pass/fail line
   lists mechanism probes as part of the deliverable; this Gate-1 deferral supersedes
   that wording for this slice — if NOT-REACHABLE becomes live the probes get built and
   the roadmap bar is met; otherwise §a.4 never required them.

## Enforced budget manifest (checked before every wave launch — cap is a gate, not prose)

d per persona (current packs): 12+12+12+13+13+11 = 73. All §a.6 bounds:

| Stage | Runs (floor) | Runs (§f upper bound) |
|---|---|---|
| Baseline Σ_sim replicates (rebuild, see below) | 5 | 5 |
| Stage 1 (6 waves, 10×d–12×d) | 730 | 876 |
| Stage 2 (6 waves, 5×d–6×d) | 365 | 438 |
| Stage 3 combinations | 20 | 20 |
| Confirmation (10 × 3 seeds; **10 × 5 under R2**) | 30 (50) | 30 (50) |
| Rerun checks (N+1 per sweep invocation: 6+6+1+10) | 23 | 23 |
| Pre-study dry-run wave (real 2-persona mini-sweep, 16 + 1 rerun; added 2026-08-09 per wave-3 review) | 17 | 17 |
| **Total** | **1,190 (1,210)** | **1,409 (1,429)** |

Cap: **1,500 including any probes** → headroom 71–290 runs. Nights at 404.7 configs/night
(the ONLY valid capacity figure): 2.90–3.49. The analysis layer maintains a running
`budget-manifest.json` (planned vs executed per stage); a wave whose launch would exceed
the cap is refused, which IS the §f escalation trigger surfacing.

## Design rules (binding — violations are defects)

**Pre-study setup (once, before wave 1):**
- **Freeze the study checkout**: record the poker-coach engine sha; the whole study runs
  at it. The pinned S4 covariance artifact (`cov-4a718ef1…`) is keyed to engine sha
  `e7c1b38` and the scorer refuses a mismatch — **rebuild the baseline Σ_sim artifact at
  the frozen sha** (5 baseline replicates, budgeted above) and pin the NEW artifact id in
  every stage-1/2 wave spec.
- Build + pin `a5_baseline_z.json` once from the designated baseline batch; never rebuilt
  mid-study.

**Config generation (new: poker-analytics `analysis/lhd_generator.py`):**
- Valid under `counterfactual.py`: §a.2 paths only; persona-aware axis sets (d per table
  above); `base_pack_hash` from the frozen checkout's live packs.
- **Maximin LHD** (§a.6 pins maximin, not any LHD): construction criterion pinned in code
  (best-of-K seeded candidates by minimum pairwise distance, K recorded); acceptance test
  asserts the maximin score beats a random-LHD baseline at the same seed.
- Seeded + deterministic: same (master seed, stage, persona) → byte-identical config set.
  Stage 1: N ≥ 10×d per persona, one persona varied, others canonicalized baseline
  (`empty_override_config` semantics). Stage 2: N ≥ 5×d on stage-1's top-decile box.
  Stage 3: 20 roster combos from per-persona top deciles (not argmax).
- Probe paths (`continue_ref`, `sizing_by_node`) hard-refused by the generator (deferral
  guard).

**Sweep execution (existing `sweep_runner.py`; SUPERSEDED 2026-08-09 — one narrow code
change owner-ruled):** the original "no code changes" line is superseded by the R1
resolution: the owner chose the 2-worker path (picker, 2026-08-09), which requires an
optional `workers` field in the sweep-spec schema (int 1–5, default 5 — S4 specs load
unchanged). The knob commit re-freezes the study sha once; everything else in this
section stands.
- Every wave spec: explicit `--lineup` (ratified 9-seat lineup, NEVER the exporter
  default) · the rebuilt pinned cov artifact (stages 1–2) · one shared seed list per wave
  (common random numbers) · `n_hands` 50k · **`--keep-raw`** (a5-check needs the Parquet
  — see next bullet). Worker count per ruling R1.
- **§a.5 execution path (review finding — the runner never runs a5-check):** after each
  wave completes, the analysis layer runs `make a5-check` per batch against the retained
  Parquet, THEN retires the raw data. Peak transient disk = one wave × ~50MB ≈ 6–8GB for
  the largest stage-1 wave; steady state ~0. The wave checklist orders this explicitly.
- Partial manifests expected at scale: consume per-run `run_status`/`failed_step`;
  failed runs re-launched only via a fresh spec that the budget manifest counts.

**Analysis layer (new: poker-analytics `analysis/reachability.py` + Makefile targets):**
- **NROY join**: config is NROY iff `canonical.pool_tier.D < canonical.pool_tier.cutoff_c`
  (exact JSON paths) AND all five §a.5 rules pass from that batch's a5 output. The
  deleted per-persona floor is NEVER a gate; `floor_S_p` echoed as diagnostic only.
- **SRRC screening** per stat family per persona: |SRRC| ≥ 0.10 materiality; rank-R² ≥
  0.3 adequacy; inadequate screen collapses that family's NOT-REACHABLE path to
  INCONCLUSIVE.
- **Fail closed on identity (review finding — reject, don't surface):** analysis REFUSES
  any run whose (formula_id, registry sha, stat_definition_version) triple, contract
  citation string, or ODCS window doesn't match the study's pinned set. No
  warn-and-proceed path exists.
- **Forced-INCONCLUSIVE branches enumerated in the analysis schema, each with a test**
  (§a.4's named cases): λ-sensitivity `pool_verdict_flip` on a would-be winner ·
  confirmation contradicting design evaluation · stage-1/2 coverage shortfall (incl. any
  fired persona-deferral valve) · refinement trajectory still strictly downward at wave
  end.
- **Stage-3 confirmation is a two-phase workflow (review finding — the runner can't do it
  in one pass):** phase 1: export + gate the fresh-seed batches (`--keep-raw`, throwaway
  scoring against the wave-wide artifact is IGNORED for the verdict); phase 2: build the
  per-finalist Σ_sim (`make covariance BATCHES=…`), then score each batch directly
  (`make score DIR=… COV=<finalist artifact>`), run a5-check, retire raw data.
  **Confirmatory-mean NROY** (§a.4 verbatim — ONE check on the mean of the fresh-seed
  stat vectors, never a per-seed conjunction): computed by `reachability.py` **importing
  the scorer's own distance functions** (never reimplementing the formula — §g.1.7
  formula identity), using the finalist's Σ_sim.

**Verdict (new: poker-analytics `docs/methods/reachability-verdict-s5.md`):**
- §a.4 conditions as an explicit checklist; every claim cites its artifacts. REACHABLE =
  stage-3 config NROY on design evaluation AND on the confirmatory mean. NOT-REACHABLE =
  full ladder (floor met · stage-2 empty · endpoint/no-leverage evidence with adequate
  screens · fresh-seed confirmation of the 10 closest). Every enumerated
  forced-INCONCLUSIVE branch reported explicitly, not collapsed into "anything else."
- Vocabulary per §g.1.6/§g.1.7: never "validated"/"confirmed"; citation string untouched;
  convergent evidence beside every distance statement; **no fix recommendations**.

## Files / interfaces to touch

poker-analytics: `analysis/lhd_generator.py` (NEW), `analysis/reachability.py` (NEW),
`Makefile` (targets `lhd-gen`, `nroy-join`, `srrc-screen`, `confirm-cov`, `budget-check`),
tests beside each, `docs/methods/reachability-verdict-s5.md` (NEW, template first),
`docs/FLYWHEEL-STATUS.md`, one §g amendment per rulings R1(c)/R2 if taken.
poker-coach: `docs/ai-dlc/specs/flywheel-s5-execution-checklist.md` (NEW), wave spec JSONs
under gitignored `docs/ai-dlc/research/persona-realism-artifacts/reachability-s5/`,
roadmap tick at close. **No changes to counterfactual.py, export_analytics.py,
scorer/*, backend/app/, or content/.** (sweep_runner.py exception: the owner-ruled
`workers` field only — see the superseded note in Sweep execution above.)

## Out of scope (explicit)

Mechanism-probe plumbing (trigger: NOT-REACHABLE in play) · emulator fallback (§f
escalation only) · bot-policy/pack/domain-core changes · fix recommendations · S6 ·
committing winning configs · registry/scorer code changes · new §e validation runs.

## Constraints

Declared axis space only. All repo invariants per profiles. Every artifact traceable to
(frozen engine sha, seed, config_hash). Owner launches every overnight wave. Structured
outputs only.

## Appetite & scope valves (semantics fixed per review)

**4–5 days** (build ≈2 — reviewer-flagged as tight; slippage fires valves, never
stretches silently — waves ≈3–4 owner nights, analysis+verdict ≈1.5, overlapping).
Valves, in order, with their §a.4 consequences stated honestly:
1. Defer lowest-priority personas' stage-1 waves → **coverage shortfall: the verdict is
   then FORCED-INCONCLUSIVE (partial coverage), never NOT-REACHABLE.** This valve buys
   time, not a verdict.
2. Drop B-grade diagnostics (ordinal-shape tables) from the verdict doc — no §a.4 impact.
3. Defer the follow-on **confirmatory STUDY** (the roadmap's own valve — a second study
   that fires only if this pilot is ambiguous). **Distinct from stage-3 fresh-seed
   confirmation, which is part of §a.4's ladder and is NEVER cut.**

## Verify-by (what /verify-change checks)

1. poker-analytics test suite green (generator/analysis/budget tests included);
   poker-coach `./scripts/verify.sh` green (untouched — no coach code changes).
2. **Dry run end-to-end:** mini-LHD (2 personas × 4 points, 2 seeds) → generator →
   sweep_runner (`--keep-raw`) → score + a5-check → NROY join + SRRC screen → tables;
   re-run at the same master seed byte-identical (canonical comparison). The dry run's
   SRRC step is a does-not-crash smoke test ONLY (4 points vs 11–13 predictors is
   rank-deficient); SRRC correctness (materiality, R² adequacy, INCONCLUSIVE collapse)
   is proven by unit tests on synthetic fixtures with known coefficients.
3. Generator rejection tests: wrong-persona axis · non-registry path · probe path
   (deferral guard) · duplicate config_hash · non-maximin regression (maximin score must
   beat random-LHD baseline at same seed).
4. Wave-1 spec files + execution checklist exist and validate via a test that imports
   `sweep_runner.load_spec()` AND runs `counterfactual.load_config` over every referenced
   config (load_spec alone does NOT validate configs; sweep_runner has NO validate-only
   CLI — never "validate" by invoking it).
5. Verdict template: full §a.4 checklist incl. every enumerated forced-INCONCLUSIVE
   branch, each mapped to its evidencing artifact.
6. Budget manifest: `make budget-check` passes on the planned program and refuses a
   synthetic over-cap wave (test).
7. Both R1/R2 rulings recorded (and their §g amendments committed, if amendments were
   the chosen resolutions) BEFORE wave 1 launches.

## Registered interpretations (recorded pre-study, 2026-08-09 — before any sweep run)

Where §a.4/§a.5 prose left the confirmation stage under-specified, the following
readings were adjudicated during the wave-2 dual review and are registered here BEFORE
any study run (the owner may veto any of them before wave 1; a veto after wave 1 would
itself need a §g amendment):

1. **a5 rules at confirmation are ANDed across the 5 fresh seeds.** The a5 constraint
   checkers are per-batch pass/fail with no defined "mean" formulation (determinism and
   runtime checks are inherently per-batch); §a.4's "one check using the confirmatory
   mean, never a per-seed conjunction" is scoped to the D(x) distance only.
2. **"Confirmation contradicts design" is either-direction disagreement** between the
   design-stage NROY result and the confirmatory-mean NROY result, forcing INCONCLUSIVE
   for that finalist (both reviewers found §a.4's wording unrestricted; Codex explicitly
   endorsed this reading).
3. **λ-sensitivity at confirmation is computed on the confirmatory-mean D** across the
   payload λ grid {1.0, 0.8, 0.5, 0.0} — the decision quantity — not by OR-ing per-seed
   flip flags (which are retained as diagnostics). The design payload's own flip guards
   the design-stage claim.
4. **§e.3 stop-gate enforcement is structural:** the verdict function refuses to emit
   anything stronger than INCONCLUSIVE without a well-formed detection-pilot evidence
   reference (verbatim §e.3, estimand contract lines 663–667). Consequence, made
   explicit: **the S6 detection pilot must have executed before S5 can deliver a
   REACHABLE or NOT-REACHABLE verdict** — INCONCLUSIVE-so-far remains deliverable at
   any time.
5. **Any verdict stronger than INCONCLUSIVE requires exactly 10 confirmed finalists**
   (§a.6/§g.4's pinned confirmation set), per-family adequate SRRC screening evidence
   for NOT-REACHABLE, and per-finalist (not global) scoping of forced-INCONCLUSIVE
   branches for the existential REACHABLE claim.

6. **Verdict precedence: a clean confirmed winner yields REACHABLE regardless of the
   study-level downward-trajectory or design-floor flags** — §a.4's trajectory clause is
   the residual case for when nothing was found; once a finalist is confirmed NROY on
   design AND confirmatory mean, "still trending downward, never crossed c" is factually
   false for that config. Study-level flags gate only the no-clean-winner paths
   (NOT-REACHABLE and INCONCLUSIVE routing). (Adjudicated from the verification review's
   textual analysis, 2026-08-09, pre-study.)
