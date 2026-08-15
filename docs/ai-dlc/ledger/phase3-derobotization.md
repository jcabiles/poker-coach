# Finding ledger — de-robotization spec (dual review, 2026-08-15)

**Bottom line: both reviewers returned FAIL on the first spec draft, and every
one of their thirteen findings was accepted. Three were structural: the
acceptance criterion measured hero grading coverage against a batch that
contains no hero decisions at all; the preflop "cap" model was a scalar
simplification of a path-dependent grading rule, and the sample-then-clamp
design it implied would have recreated determinism at the clamp boundary; and
the two reused gates are blind to both bet sizing and position, so they would
have passed a completely no-op implementation of this slice. The spec was
rewritten rather than patched.**

Reviewers: Claude `refuter` (verdict fail — 3 high, 2 med, 1 low, 1 optional) ·
Codex `gpt-5.6-sol` at high effort (verdict fail — 3 high, 4 med, 2 optional
corrections). Adjudicator: director session. Nothing was auto-folded; each
finding was re-verified against the code before acceptance.

## Findings

| # | Source | Sev | Finding | Status |
|---|---|---|---|---|
| 1 | both | high | Hero-coverage acceptance ("gradeable postflop decisions ≥ pre-change count") is undefined. One shared RNG drives deals *and* decisions, so an added draw changes which cards are dealt in every later hand — pre/post runs are different hand populations. Worse (Sol): `export_analytics.py` is nine-bot self-play with **zero** hero decisions, so the gate batch cannot measure hero coverage at all. | **ACCEPTED.** Verified: `grep -c hero export_analytics.py` = 0. Replaced with the repo's existing harness `test_coverage_baseline.py`, which already tracks the graded/total **ratio** and documents this exact drift problem in its own history. Spec §7.1. |
| 2 | both | high | "Both gates are already implemented and tested" overstates. The only tested entry point is `run_checks()`, which begins with `require_gated()` and runs all five rules; there is no tested path running rules 1 and 4 standalone. Calling them directly is new, untested glue that must assemble a duckdb connection, the lineup, and the ten-stat measured vectors by hand. | **ACCEPTED.** Verified `constraints.py:653-679`, `gate.py:79-119`. Spec §5.1 now states plainly that the runner is new code, explains why it bypasses `run_checks`, and requires two known-answer reproductions (baseline `min_pairwise_distance` 1.792042 and the artifact's stored `raw_vectors`) before the runner is trusted. |
| 3 | both | high | Missing dependencies under-stated and the cross-repo invocation mechanism unspecified. `numpy` is missing as well as `duckdb` (Sol adds `PyYAML`); `scorer.constraints` imports both at module level. The verify-by command implies in-process execution, which would require the whole analytics stack inside the coach venv. | **ACCEPTED.** Verified both absent. Spec §5.2: the coach runner shells out to poker-analytics' own interpreter and parses JSON. The analytics repo keeps its dependencies; the coach repo gains none. |
| 4 | Sol | high | The preflop cap model is wrong, not merely incomplete. Grading is path-dependent: a directly-faced villain open may reach 4.5bb, but in a hero-3-bet line the villain open must be ≤3.0 and the 3-bet cap is 3.5 × *canonical position open*, not the actual faced open; call+raise lines are rejected before sizing is read, so no gradeable iso band exists. Also: maniac's 4-bet at 3.0 jittered then clamped to 2.4 yields exactly 2.4 on every draw — full determinism plus a centre shift. Also: lag's `fourbet_mult` is at the cap and was omitted from the contract table. | **ACCEPTED in full.** Contract map corrected (lag added; path-dependence recorded as "the table is the outer envelope, not the full rule"). Spec §6.2 replaces sample-then-clamp with **draw from a pre-truncated valid interval**; at-cap levers draw one-sided downward; the maniac 4-bet is **excluded from the slice** and recorded as a pre-existing gap. |
| 5 | both | med | Neither gate measures bet sizing. Rule 1's ten statistics are all frequency/rate; rule 4 groups on action type, not size — and does not condition on position either. Both gates would pass a no-op implementation of this slice; the unchanged roster passes them by construction. | **ACCEPTED.** Verified `scorer/stats.py:53-64`, `constraints.py:440`. Spec §7.2 adds six positive tests carrying the actual goal: sizes vary, edge combos strictly mixed, no shadowed mixes, complete positional coverage with differing vectors, grid membership, core ranges pinned. |
| 6 | Sol | med | First-match-wins mix scanning plus no combo-overlap validation means a new fuzzy-edge mix placed after an existing hard mix is dead code, and nothing fails. Separately, node validation does not require complete position coverage — an omitted seat silently reaches the implicit-fold path and that persona folds 100% from that seat. | **ACCEPTED.** Verified `personas.py:100` (first-match scan) and `models.py:343-379` (validates node *position* overlap only, not mix combo overlap). Spec §6.4 and §6.5; tests 3 and 4 in §7.2. Named as the most likely way this slice silently accomplishes nothing. |
| 7 | Sol | med | "Existing-grid only" is asserted but unenforced — `_validate_bucket_dist` accepts any positive fraction whose weights sum to 1. | **ACCEPTED.** Verified `models.py:145`. Spec §6.3 adds a pack-wide invariant asserting grid membership for every authored postflop sizing key. |
| 8 | Sol | med | One 50k-hand seed is a deterministic smoke gate, not statistical proof. Rule 4 is discontinuous at both thresholds; the closest baseline pair (lag/tag, 1.792042) sits near a pass floor of ≈1.2544, so a marginal candidate can flip verdict on seed noise. The analytics repo already retains a five-seed design for exactly this. | **ACCEPTED.** Spec §5.3: seed 601 gates a ticket (~2.1 min); the existing five-seed set gates the slice, every seed required to pass (~11 min). The word "proof" is removed from the per-ticket gate. |
| 9 | refuter | low | The existing `_clamp(v, min_bb, max_bb)` bounds the *engine's* legal-raise bracket (up to the full stack, `engine.py:175`) and enforces no grading cap. An implementer skimming the call could assume otherwise. | **ACCEPTED.** Spec §4 and §6.2 state that a second, distinct bound is required, and that forced-jam brackets legitimately collapse and are excluded from any must-vary assertion. |
| 10 | Sol | opt | `_CaptureRng` is postflop-only; preflop estimation mirrors pack probabilities directly and never calls `sample_preflop_action`. The contract map's "either sampler" was overbroad. | **ACCEPTED as a precision correction.** Contract map §2 amended; the discipline still applies to both samplers, but the live breakage risk is postflop. |
| 11 | refuter | opt | Maniac's 4-bet is already ungradeable pre-slice; clamping cannot retroactively close that gap. | **ACCEPTED, informational.** Recorded in spec §3 out-of-scope so it is not mistaken for something this slice fixes. |
| 12 | Sol | opt | Measured runtime: ~121.1s for a 50k export plus ~2.4s ingestion, so one gate run is ~2.1 minutes and a five-seed run ~11 minutes. | **ACCEPTED.** Folded into spec §5.3 as the stated cadence cost, replacing an unstated assumption. |
| 13 | refuter | — | Contract-map factual claims verified: roughly twenty `file:line` citations independently checked, including the 75-deterministic-mix count recomputed by script (exact match), all four preflop caps, the six-persona sizing table, `_CANON_BET_TOL`, the merit-floor citations, the "no grader imports the persona samplers" claim, and the provenance diff. **No errors found** beyond items 4 and 10. | Recorded — the contract map's factual layer stands. |

## T0 — gate verification record (2026-08-15)

**The gate reproduces the baseline exactly and is therefore trusted to judge
changes.** Run from the `feat/derobo-gate` worktree against unchanged packs:

| Known answer | Expected | Measured | |
|---|---|---|---|
| `min_pairwise_distance` | 1.792042 | 1.792042 | ok |
| `raw_vectors`, all six personas | artifact values | match within 5e-6 | ok |
| candidate `run_id` | `run-s601-n50000-c9273b753b9de` | identical | ok |

The run id matching to the character is the strongest single signal here: it
carries the config hash derived from the persona packs, so the runner is
provably measuring the same packs, at the same seed and hand count, that the
S3/S4 pipeline measured when it built the artifact — via an entirely different
code path.

Gate verdict on the unchanged roster: **PASS** — separation 1.792042 against a
required 1.254429, label preservation 6/6, determinism guard pass.

### Empirical finding: the determinism guard is a regression guard, not a progress meter

**The current roster passes the determinism guard**, even though the 2026-08-05
re-measure documents that same roster as visibly deterministic (the station's
48-of-49 river fold, tag's 100% AQo continue, the flat by-seat fold constants).
The guard's threshold — modal share ≥0.98 in at most 20% of contexts observed
≥50 times — is simply not binding at this level of defect.

This confirms review findings 5 and 6 empirically rather than by argument: the
two reused gates cannot tell anyone whether this slice achieved its goal. They
answer only "did this change make things worse". The §7.2 positive tests carry
the actual goal, and a green gate run must never be reported as evidence that
de-robotization worked.

### Runtime, measured on this machine

253 hands/second, so the pinned 50,000-hand batch takes about 3.3 minutes per
seed — slower than the ~121 seconds recorded in the estimand contract, and
below the scorer's own 350 hands/second reference figure (that figure belongs
to rule 5, which this gate does not run). The five-seed slice-level set
therefore costs roughly 17 minutes, not the 11 estimated in the spec.

## Adjudication notes

**Nothing was rejected.** Both reviewers independently reached FAIL on the same
three structural problems (coverage estimand, gate-runner novelty, missing
dependencies), which raises confidence that these are real rather than
review-manufactured.

**The most valuable finding is #5 combined with #6.** Taken together they say:
the automated gates cannot see this slice's headline change, and the most
natural way to author the change (append a softer mix) produces dead code that
nothing complains about. Without the §7.2 positive tests, this slice could have
shipped entirely green while accomplishing nothing — the precise failure the
S6 shakedown and S3 contract defect already taught this project to expect from
a confident-but-blind instrument.

**Divergence between reviewers.** None material. Sol went deeper on the grading
mapper's path-dependence (#4) and on pack-validation gaps (#6, #7); the refuter
went deeper on the RNG-stream consequences for the coverage estimand (#1) and
verified the contract map's citation layer exhaustively (#13). The two sets are
complementary, not conflicting.
