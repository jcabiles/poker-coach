# Finding ledger — S5 (reachability study)

## Spec dual review, 2026-08-08 (rev 1 → rev 3)

Reviewers: Claude `refuter` (Sonnet) — NEEDS-WORK, 6 findings; Codex `gpt-5.6-sol`
(high effort) — NEEDS-WORK, 13 findings. Every finding adjudicated against code/contract
before disposition; convergent findings noted. Spec rev 3 folds all ACCEPTED items.

### Claude refuter

| # | Sev | Finding | Adjudication | Disposition |
|---|---|---|---|---|
| R-1 | HIGH | §a.4 pins ≥3 fresh-seed Σ_sim re-estimation but `covariance.py:147-149` refuses <5 replicates — confirmation unexecutable as preregistered | Verified in code + contract. Convergent with C-5 | ACCEPTED → owner ruling **R2** (recommend §g amendment to 5 seeds); spec carries both figures |
| R-2 | MED | Spec's "NROY on all fresh confirmation seeds" is a per-seed conjunction; §a.4 line 215 pins ONE check "using the confirmatory mean" | Verified verbatim. Convergent with C-4 | ACCEPTED → spec reworded; analysis layer computes confirmatory-mean D importing scorer functions |
| R-3 | MED | Verify-by item 4 assumed a validate-only sweep_runner CLI path; none exists (main() runs run_sweep unconditionally) | Verified sweep_runner.py:830-866. Convergent with C-12 | ACCEPTED → verify via imported `load_spec` + `counterfactual.load_config` per config |
| R-4 | MED | Probe deferral contradicts roadmap S5 pass/fail wording ("mechanism probes… for each failing stat") without naming it | Tension real; Gate-1 owner decision supersedes for this slice | ACCEPTED → tension named explicitly in spec (surfaced, not silently reconciled) |
| R-5 | LOW | Dry-run SRRC on 4 points × 11–13 predictors is rank-deficient; adequacy check can't be exercised there | Correct by construction | ACCEPTED → dry-run SRRC = smoke only; correctness via synthetic-fixture unit tests |
| R-6 | LOW | ≈2-day build estimate optimistic for six net-new pieces | Judgment call; flagged honestly | ACCEPTED as disclosure → appetite section carries the flag + valve order |

### Codex Sol

| # | Sev | Finding | Adjudication | Disposition |
|---|---|---|---|---|
| C-1 | HIGH | a5-check needs Parquet; sweep_runner deletes it post-score and never runs a5-check | Verified (runner Phase B = validate+score only; constraints.py reads Parquet) | ACCEPTED → `--keep-raw` on every wave; a5-check-then-retire pass per wave; ~6–8GB peak transient disk stated |
| C-2 | HIGH | §a.5 rule 5 (≥350 hands/sec from the batch's own `_TIMING.json`) fails by construction under 5-worker load (~230–257 h/s measured) — nothing could ever be NROY | Verified constraints.py + estimand:276 + S4 acceptance benchmark | ACCEPTED → owner ruling **R1** (benchmark fewer workers; else §g amendment on rule-5 evidence). Wave 1 blocked until ruled |
| C-3 | HIGH | Pinned cov artifact `cov-4a718ef1…` keyed to engine sha `e7c1b38`; checkout now `6fa679d`; scorer refuses mismatch | Verified artifact key + score_realism.py:150-158 | ACCEPTED → pre-study step: freeze study sha, re-export 5 baseline replicates, rebuild + pin new artifact (runs already budgeted) |
| C-4 | HIGH | Confirmatory-mean rule + no scorer interface for it | Convergent with R-2 | ACCEPTED (merged with R-2); analysis layer imports scorer distance functions — never reimplements (§g.1.7) |
| C-5 | HIGH | §f pins "exactly 3 seeds × 10 configs unless amended" vs covariance ≥5 floor | Verified estimand:688-691 — sharpens R-1: an amendment IS required either way | ACCEPTED (merged with R-1 → ruling R2) |
| C-6 | HIGH | Confirmation covariance is circular through sweep_runner (spec must name a pre-existing artifact; the per-finalist artifact is built FROM those batches) | Verified load_spec requires cov_artifact; runner scores immediately | ACCEPTED → two-phase confirmation workflow in spec (export+gate → build cov → direct score/a5 → retire) |
| C-7 | HIGH | Spec said triple drift "surfaced" — §g.1.7 requires REJECT, never warn-and-proceed | Verified estimand:1384-1389 | ACCEPTED → analysis fails closed on triple/citation/ODCS mismatch |
| C-8 | HIGH | Cap quoted but not enforced; run arithmetic left implicit | Verified §f bounds; Codex's arithmetic reproduced (floor 1,173 / upper 1,392 / +20 under R2) | ACCEPTED → enforced budget-manifest table in spec + `make budget-check` gate + test |
| C-9 | MED | §a.6 pins **maximin** LHD; spec said only "LHD" | Verified estimand:283 | ACCEPTED → maximin construction pinned + acceptance test vs random-LHD baseline |
| C-10 | HIGH | Valve 1 (defer personas) cuts §a.6-mandatory coverage while promising a full verdict; valve 3 wording conflated stage-3 confirmation with the confirmatory study | Partially verified: coverage point correct; conflation was wording — roadmap's valve is the follow-on STUDY | PARTIALLY ACCEPTED → valve 1 now states it forces INCONCLUSIVE; valve 3 reworded to distinguish study vs stage-3 confirmation (never cut) |
| C-11 | MED | Forced-INCONCLUSIVE branches (λ-flip, confirmation contradiction, coverage shortfall, downward trajectory) not enumerated | Verified §a.4:229-231 + `pool_verdict_flip` field | ACCEPTED → enumerated in analysis schema, each with a branch test + verdict-template slot |
| C-12 | HIGH | Validate-only CLI does not exist; load_spec doesn't validate configs | Convergent with R-3, adds the load_config gap | ACCEPTED (merged) → test imports both |
| C-13 | LOW | JSON paths are `canonical.pool_tier.D` / `cutoff_c`, not `pool_tier.D`/`cutoff` | Verified score_realism.py:285-291,445 | ACCEPTED → exact paths in spec |

**Process note:** the two reviewers converged independently on the confirmation-seeds
contradiction (R-1/C-5), the confirmatory-mean rule (R-2/C-4), and the missing
validate-only path (R-3/C-12) — consistent with every prior slice: convergent findings
are the real ones. Codex's C-2 (runtime rule vs contention) is the slice's highest-value
catch: without it, every sweep batch would silently fail §a.5 rule 5 and the study would
have produced a guaranteed-INCONCLUSIVE at full compute cost.

## Wave-1 code dual review, 2026-08-09 (commit 8845a4a)

Reviewers: Claude `refuter` (Sonnet, high pin) — NEEDS-WORK, 5 findings; Codex
`gpt-5.6-sol` (high effort) — NEEDS-WORK, 7 findings. Orchestrator independently
reproduced the top finding before adjudication (47/120 emitted nit stage-1 configs
rejected by the real `counterfactual.load_config`).

| # | Sev | Finding | Adjudication | Disposition |
|---|---|---|---|---|
| W1-1 | HIGH | `_simplex_weights` clip-then-renormalize emits weights outside simplex bounds; real validator rejects 39–77% of stage-1 configs per persona (refuter #1 + Codex #1, convergent; orchestrator-reproduced) | CONFIRMED three ways | ACCEPTED → T1-fix: deterministic bounded-simplex projection + all-weights-in-bounds test |
| W1-2 | HIGH | Stage-2 box reinterprets probability-space bounds as log-weight bounds — refinement misses the region stage 1 found (Codex #2) | Verified in code (lines 468–480) | ACCEPTED → T1-fix: unit-cube box contract end-to-end + `top_decile_box` helper + tests |
| W1-3 | MED | Stage 3 accepts degenerate/out-of-bounds pools; singleton pools emit 20 duplicate configs `load_spec` rejects (Codex #3) | Consistent with code; test used singleton pools | ACCEPTED → T1-fix: pool value validation + duplicate refusal + realistic-pool test |
| W1-4 | HIGH | a5 payload never identity-bound to the score payload/manifest record; score `producer_run` not checked against manifest either (Codex #4, binding part) | Verified: `check_a5_identity` checks citation only | ACCEPTED → T2-fix: bind all available identity fields, mismatch aborts join. The same finding's claim that excluding `run_status: failed` runs is warn-and-proceed was REJECTED — that exclusion is the spec's partial-manifest rule; the runner already failed those closed |
| W1-5 | HIGH | Budget gate advisory where it must be hard: cap read from mutable manifest, no per-stage §f bounds, missing manifest degrades to zero-run pass, no probes stage (Codex #5) | Consistent with maker's own disclosure of a minimal CLI | ACCEPTED → T2-fix: cap as code constant, §f stage bounds enforced, missing manifest = hard error, probes stage added |
| W1-6 | MED | Inadequate SRRC screen leaves `material_axes` populated — invites the exact misuse §a.4 forbids (refuter #4 + Codex #6, convergent; both reproduced) | CONFIRMED | ACCEPTED → T3-fix (DONE): `material_axes` structurally empty when inadequate; coefficients stay diagnostic-only |
| W1-7 | MED | §g.4 amendment lacked the file's conventional inline callouts at the three other stale 3-seed passages (§a.3:194, §a.6:307, §f:689) (refuter #2) | Verified against the file's own amendment convention; Codex explicitly found §g.4's clause coverage sufficient — conflict resolved as "text valid, callouts missing" | ACCEPTED → orchestrator added the three inline callouts (DONE) |
| W1-8 | MED | Pins doc omitted the four identity fields the gate actually enforces; no frozen human-diffable snapshot (refuter #3) | Verified | ACCEPTED → orchestrator recorded FORMULA_ID F0, registry sha b83043ae…, statdef-2026-08-06, ODCS 1.2.0 in s5-study-pins.md (DONE) |
| W1-9 | LOW | Maximin acceptance test is in-sample/selection-tautological (Codex #7); refuter judged it non-vacuous — reviewers CONFLICTED | Codex's mutation argument is structurally right; refuter right that baseline is a genuine random LHD. | PARTIALLY ACCEPTED → T1-fix: independent random baseline across ≥5 seeds + LHD geometry check |
| W1-10 | LOW | Stale `PERSONA_DOF` order comment (refuter #5) | Verified | ACCEPTED → T1-fix |

Clean per both reviewers: exact `canonical.pool_tier.D`/`cutoff_c` paths; fail-closed
triple/citation/ODCS gate with no warn-and-proceed path; budget table arithmetic
(1,193/1,412/1,500); `PERSONA_SIMPLEX_KEYS`/`PERSONA_DOF` match live packs; §g.4 covers
both contradicting clauses. Process note: the reviewers CONFLICTED on the maximin test
(W1-9) and on whether failed-run exclusion violates fail-closed (W1-4) — both conflicts
adjudicated against source rather than picking a reviewer.

**Fix wave landed (commit 66f55be, 2026-08-09):** all ten W1 findings closed. Orchestrator
re-verified the load-bearing one end-to-end: 730/730 stage-1 configs across all six
personas now accepted by poker-coach's real `counterfactual.load_config` (pre-fix: 47/120
rejected for nit alone). Suites green: analysis 90, scorer 119. Residual notes carried
forward for the wave-2 review: (a) T1-fix's float-precision safety net in
`_project_to_simplex_bounds` never fires in tests (converges ~1e-16 up to k=4);
(b) T2-fix's config_hash comparison is stricter than the pre-S4 key-absence convention
(could reject a legacy batch — no such batch exists in S5's frozen-sha study);
(c) stage-3's `pool[perm[i % len(pool)]]` draw scheme has an index-cycle-alignment
artifact worked around in test fixtures, not changed.

## Wave-2 code dual review, 2026-08-09 (commits 66f55be + a13de7f)

Reviewers: Claude `refuter` (Sonnet, high pin) — FAIL, 6 findings; Codex `gpt-5.6-sol`
(high) — NEEDS-WORK, 9 findings. Suites green both sides (analysis 107, scorer 119) —
every accepted defect below is invisible to the suite, which is the point of the review.
W1 closure per Codex: W1-1/2/6-10 hold; W1-3/4/5 partially reopened (see W2-4/6/7).

| # | Sev | Finding | Adjudication | Disposition |
|---|---|---|---|---|
| W2-1 | HIGH | §e.3 stop-gate not enforced: REACHABLE emitted with exploratory-surrogate score and no detection-pilot evidence (Codex 1) | Orchestrator verified §e.3 verbatim (estimand:663-667): detection-pilot convergent evidence required for ANY verdict stronger than INCONCLUSIVE | ACCEPTED → required detection_pilot_evidence param; verdict capped INCONCLUSIVE + STOP_GATE branch without it. **Owner note: S6 execution now gates S5's final verdict** |
| W2-2 | HIGH | Any finalist's forced branch blocks a clean winner's REACHABLE — contradicts §a.4's existential clause AND the function's own docstring (refuter 1) | Verified reading; §a.4 "some config x*" is existential | ACCEPTED → per-finalist scoping for REACHABLE; any-branch-blocks for NOT-REACHABLE (universal claim); study-level branches stay global |
| W2-3 | HIGH | λ-flip ORs per-seed flags, never computed on the confirmatory-mean D — the decision quantity (Codex 5 + refuter 5, convergent; Codex numeric repro: mean flips at λ=0.5, all flags false) | Math verified | ACCEPTED → λ grid computed on the mean via imported scorer mechanism; per-seed flags demoted to diagnostics |
| W2-4 | HIGH | finalist_config_hash a bare label; None==None passes; duplicate seeds allowed; lineup/engine sha ignored (Codex 4 + refuter 2, convergent) | Verified | ACCEPTED → hard binding of every payload to the finalist hash; 5 distinct seeds; absent required identity fields raise |
| W2-5 | MED | Confirmation Σ_sim a bare ndarray — config-specific artifact requirement (§a.3) never verified; covariance_artifact absent from every check (Codex 2 + refuter 3, convergent) | Verified (zero grep hits outside docstrings) | ACCEPTED → artifact-metadata input with key/config_hash/seed_set/engine-sha/artifact_id cross-checks; design payload must NOT cite the finalist artifact. Codex 2's broader ingredient pinning partially accepted (stat list + λ from scorer constants); full registry loading remains T5/T6 CLI wiring |
| W2-6 | HIGH→MED | NOT-REACHABLE ladder reducible to three unverifiable booleans + arbitrary finalist count (Codex 3) | Verified; downgraded MED — caller is our own runbook, but structure must still enforce | ACCEPTED → exactly-10-finalists rule for any strong verdict; per-family srrc ScreeningVerdict evidence; STAGE_COVERAGE_SHORTFALL branch (also closes Codex 9) |
| W2-7 | MED | Budget: negative/missing-stage counters accepted; record_executed ungated (Codex 6) | Verified plausible; low real-world risk, cheap fix | ACCEPTED → strict manifest shape, nonneg ints, bounds on record |
| W2-8 | MED | Stage-3 partial sizing overrides pass generator, rejected by real validator (Codex 7, reviewer-reproduced live) | Trusted repro (same validator harness as W1-1) | ACCEPTED → all-keys-or-none + sum-to-1 pool validation |
| W2-9 | MED | top_decile_box zero-width at n≤10 + stage-2 silent duplicate configs — dry run WILL hit this (refuter 4, reproduced) | Verified | ACCEPTED → explicit raises on degenerate box and duplicates |
| W2-10 | LOW/ruling | a5 ANDing across 5 seeds is an unregistered tightening (Codex 8 + refuter, convergent meta-point); Codex confirmed the either-direction contradiction reading is fine | Interpretation defensible (a5 rules have no mean formulation) but must be RECORDED pre-study | ACCEPTED as registration → spec addendum records the interpretation (orchestrator, DONE below); owner may veto before wave 1 |
| W2-11 | LOW | Fable co-author trailer on commits (refuter 6) | Trailer is harness-mandated attribution for orchestrator-authored commits; all workers Sonnet; session model is owner-selected | NO ACTION — recorded for owner visibility |

**Wave-2 fix verification (commit 61711c0, fresh refuter, adversarial re-open attempts):**
W2-1/3/4/6/7/8/9/10 CLOSED with reproductions run both directions. Two residuals:
(V-1, HIGH, ACCEPTED) covariance seed-set check fires on the RAW runs before status
filtering — a legitimate 4-seed artifact (one export failure) crashes with IdentityError
instead of returning COVERAGE_SHORTFALL; the shipped test masked it with an internally
inconsistent fixture (artifact seed_set padded despite failed_step="export"). Fix worker
dispatched. (V-2, MED, ACCEPTED AS DOC FIX) module docstring + this ledger's W2-2 wording
claimed DOWNWARD_TRAJECTORY/STAGE_COVERAGE_SHORTFALL "block regardless of scoping";
the CODE's actual precedence (a clean confirmed winner short-circuits study-level flags)
was adjudicated CONTRACT-CORRECT — §a.4's trajectory clause is the residual no-winner
case, so a confirmed NROY finalist cannot be trumped by "still trending downward".
CORRECTION to W2-2's disposition above: study-level branches gate only the
no-clean-winner paths. Recorded as registered interpretation #6 in the spec.

**R1 RESOLVED by benchmark (2026-08-09):** 3 simultaneous export workers measured
341.6–345.4 hands/sec (FAIL vs the 350 floor); 2 workers measured 398.9–400.3 (PASS).
Owner chose the 2-worker path: a `workers` field is added to the sweep-spec schema
(default 5, unchanged S4 behavior), the knob commit re-freezes the study sha once, and
the owner re-runs the ~15-minute baseline rebuild at the post-knob sha. No §g amendment
needed — rule 5 is cleared honestly per batch. Study runtime ≈3.5–4 nights, under the
6-night §f escalation. T0 pins recorded interim at sha 6fa679d / artifact
cov-b637fbc20b001a24 (analytics commit 7c590e6); both re-pin once after the knob merge.
Study master seed pinned: 20260809.

## Wave-3 code dual review, 2026-08-09 (T5+T6: ae4d621 + 4897367 analytics, 7033121 coach)

Reviewers: Claude `refuter` (Sonnet, high pin) — NEEDS-WORK, 4 findings; Codex
`gpt-5.6-sol` (high) — NEEDS-WORK, 8 findings. Both ran the FULL coach backend suite
(1,901 passed) and re-derived the budget arithmetic; the T0 artifacts verified clean
field-by-field on both sides.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| W3-1 | HIGH | Dry run never touches the real pipeline (spec Verify-by 2 pins a real mini-sweep); fixtures used retired sha + wrong lineup (Codex 1) | PARTIALLY ACCEPTED → real mini-sweep added as a pre-study runbook step (17 runs, new "dryrun" budget stage — spec table updated, totals 1,210/1,429, headroom 71–290); in-suite test stays synthetic (sweeps are launch-gated); fixtures corrected to frozen-sha form + ratified lineup |
| W3-2 | HIGH | Verdict template cannot substantiate NOT-REACHABLE (missing §a.4(ii) clause slots + the verbatim scope qualifier) (Codex 2) | ACCEPTED → template slots added for every clause + literal qualifier string |
| W3-3 | HIGH | Checklist budget gate not executable: no manifest init, bare budget-check, no STAGE/RUNS projection; N+1 rerun never counted (Codex 3 + refuter 3, convergent) | ACCEPTED → `--init` CLI flag added; checklist commands made copy-paste real; N+1 counting rule written in |
| W3-4 | HIGH | a5-check run without OUT= discards required evidence; no run_status filtering or failed-run relaunch procedure (Codex 4) | ACCEPTED → OUT= per batch, ok-only filtering, fresh-spec relaunch procedure |
| W3-5 | HIGH | Checklist gen-waves command invalid (make flags vs variables) + missing required variables + untracked owner-run.sh reference (Codex 5) | ACCEPTED → exact variable forms per stage; owner-run.sh reworded as local-only, orchestrator-provided |
| W3-6 | MED | gen-waves forwards empty strings for required identities (Codex 6) | ACCEPTED → empty-string rejection + Makefile unset-variable guards |
| W3-7 | MED | No confirmation-stage spec generation / 5 fresh seeds path (Codex 7) | ACCEPTED → `--stage confirm`: 1 finalist config × 5 fresh seeds (distinct sha256 role ⇒ disjoint from selection seeds by construction), called once per finalist |
| W3-8 | MED | workers knob contradicts the spec's own "no sweep_runner changes" line (Codex 8) | ACCEPTED → spec line superseded in place, citing the owner's 2026-08-09 2-worker ruling (governance fix, not code) |
| W3-9 | HIGH | Compose test (only automated proof of Verify-by 4) hardcodes the ephemeral scratch worktree path — silent permanent skip after teardown (refuter 1) | ACCEPTED → env override + durable-checkout default; import failure = FAILURE not skip; only the workers-field assertion may skip pre-merge, loudly |
| W3-10 | MED | Verdict template glossed NROY as "no region of youth" — wrong; it is "not ruled out yet" (refuter 2) | ACCEPTED → corrected |
| W3-11 | LOW | Stale "5-worker" docstring/comment in sweep_runner (refuter 4) | ACCEPTED → corrected |

Clean on both sides: workers knob (bool rejected, S4 specs unchanged, run_sweep consumes
it, full suite green); budget arithmetic vs §a.6/§f; sha256 seed derivation platform-
stable; one-seed-per-wave consistent with the CRN clause; byte-determinism asserted on
bytes; enum lockstep tests genuine; cov-b637fbc20b001a24 + a5_baseline_z verified
field-by-field.
