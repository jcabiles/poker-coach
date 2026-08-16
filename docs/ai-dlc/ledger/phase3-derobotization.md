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

## PR-0 diff review (2026-08-15, second dual review)

Reviewers: Claude `refuter` (verdict **pass**, 1 low + 1 optional) · Codex
`gpt-5.6-sol` at high effort (8 findings: 1 high, 4 med, 3 low). Both ran the
targeted suites; both confirmed independently that `measure()` aggregates seats
to personas identically to `run_checks`. **All ten findings accepted and
fixed.**

| # | Source | Sev | Finding | Fix |
|---|---|---|---|---|
| 14 | Sol | high | The gate cannot establish that a change made progress — the unchanged defective roster passes both rules, so any behavioural no-op passes. Concrete example: a change confined to the BB `unopened` node, documented as structurally unreachable in organic play, would preserve every invariant and measure byte-identically. | **ACCEPTED as reinforcement**, not a new defect — the spec and the T0 record already say this. Sol's unreachable-node example is added to the ledger because it is sharper than the general argument. Mitigation is unchanged: per-ticket positive tests carry the goal. |
| 15 | Sol | med | The self-test proves nothing about `rule4_determinism`: the artifact stores no determinism answer, so a broken query or a wrong context-to-persona mapping still passes. | **ACCEPTED.** The docstring now states the asymmetry plainly instead of claiming both rules are covered. Rule 4 keeps its own pass/fail unit tests upstream. |
| 16 | Sol | med | **The self-test's two checks are both positive, so a `measure()` that ignored the batch and echoed `baseline["raw_vectors"]` would satisfy both — and then certify every future candidate as unchanged.** | **ACCEPTED — the most valuable finding of this round.** Added a metamorphic check: permuting the seat-to-persona map must move the measured vectors. Permutation is free (no re-export), and an echoing checker fails it while passing everything else. Verified live: the check runs and passes. |
| 17 | Sol | med | `run_check` converts malformed output into PASS — `{"pass": "false"}` is a truthy string — and never checks that the exit code agrees with the verdict, so a checker that crashed after printing a stale verdict reads as PASS. | **ACCEPTED.** Only a boolean `pass` is believed, and the exit code must agree with it. Six new tests. Writing them exposed a further bug: the error path itself crashed on a non-object result, which is now handled. |
| 18 | Sol | med | The analytics checkout is selected by a marker file alone, with no provenance binding. Since both the pins and the comparison values are read from that one checkout, a stale one would be internally self-consistent and pass. | **ACCEPTED.** `read_pins` binds to the expected baseline `artifact_id`; a substituted artifact fails loudly and names the pin. |
| 19 | Sol | low | The contiguous `0..N` seat check is too weak — `run_export` always plays nine seats and wraps a shorter lineup, so a shorter contiguous map would be measured under seats the checker never sees. | **ACCEPTED.** Exactly `0..8` is required, and the returned manifest's seed and hand count are verified against the requested pins rather than trusted. |
| 20 | Sol | low | `zip` over `raw_vectors` is non-strict: a longer stored vector is silently truncated and can pass on its prefix. Tolerance 5e-6 is looser than the 5e-7 implied by six-decimal rounding. | **ACCEPTED.** Length is validated explicitly, `zip(..., strict=True)`, tolerance tightened to 5e-7. The 50k self-test still reproduces every value at the tighter bound. |
| 21 | Sol | low | The shadowing invariant accepts an empty combo set, which is permanently dead but never reported. | **ACCEPTED.** An empty expansion is now reported as its own violation. |
| 22 | both | low | `_check_position_coverage` groups strictly by `(facing, role)` and only credits a full wildcard toward role-tagged strata, so an untagged node with an explicit position list is not credited to the strata it actually answers. Fails safe (false positive) and does not affect the shipped packs. | **ACCEPTED.** Rewritten to ask the runtime question directly — for each facing, each reachable role, and each seat, would any node match, using the predicate copied from `sample_preflop_action`. Correct by construction rather than by reasoning about wildcards. |
| 23 | refuter | opt | Same as 22, independently found. | Folded into 22. |

**No findings rejected.** Both reviewers verified the aggregation equivalence
independently, which is the single claim the whole gate rests on.

## T2a diff review (2026-08-15, third dual review)

Reviewers: Claude `refuter` (pass-with-issues — 2 med, 1 low, 1 optional) ·
Codex `gpt-5.6-sol` at high effort (6 findings, 4 med). Both independently
confirmed the byte-identity claim by probing the RNG stream directly, and both
independently found the same two gaps. **All accepted.**

| # | Source | Sev | Finding | Fix |
|---|---|---|---|---|
| 24 | Sol | med | **"Enumerating sizes keeps every value inside hero's grading bands by construction" is false.** `PersonaSizing` validates positivity, weight sum and nothing else — a test in the same commit literally proves a 9bb open is accepted. The docstring also cited an invariant test that did not exist. | **ACCEPTED — the claim was simply wrong.** Reworded to "enumeration permits safe authoring"; the invariant it falsely cited now exists (`test_authored_preflop_sizes_stay_gradeable`), reads its caps from the grader so a drift there fails here, and carries a negative test. Its docstring states plainly that the caps are the outer envelope and that grading is path-dependent. |
| 25 | Sol | med | A misspelled mix field (`open_bb_mxi`) loads cleanly — pydantic allows extra fields by default — leaving the real field None and silently turning the feature into a no-op nothing reports. | **ACCEPTED.** `extra="forbid"` on `PersonaSizing`, plus a test. |
| 26 | Sol | med | Non-finite values accepted: `"nan"` and `"inf"` are legal JSON keys and `float()` takes both. A NaN size passes the engine's `<`/`>` legality checks — every comparison against NaN is False — and poisons the pot. | **ACCEPTED.** Finiteness enforced for keys and weights, four new cases. Ordering matters: shape is validated first so a non-numeric key still reports the readable message. |
| 27 | both | med | **The ordering test did not exercise the changed code.** It called `sample_preflop_action` directly, so it would pass if `rng=rng` were deleted from `play.py`, or if sizing were reordered ahead of the action draw. With no pack authoring a mix, such a regression would be invisible today and would surface only once values ship. | **ACCEPTED — the sharpest finding of this round.** Replaced with tests that drive `_preflop_decision` itself, with mixes authored so the size draw is reachable, across open, iso, 3-bet and 4-bet, asserting the action population is drawn first and that a size draw actually happened. A separate test asserts the 5-bet jam draws the action only. |
| 28 | Sol | low | The byte-identity test compared only returned values, so an implementation that drew a number and then returned the scalar would pass while shifting every later hand in the seeded harnesses. | **ACCEPTED.** It now compares `rng.getstate()` before and after, with a mirror test proving a mix does consume from the stream — otherwise both tests would pass on a feature that never drew at all. |
| 29 | refuter | med | `content/schema/persona.schema.json` does not match what pydantic emits, and unlike its sibling `contentpack.schema.json` it has no sync test, so drift is silent and nothing in the app reads the file. | **ACCEPTED.** Schema regenerated from the model; sync test added, mirroring `test_content.py::test_checked_in_schema_matches_model`. |
| 30 | refuter | low | Validator error text says "pot fraction" for preflop mixes, whose keys are bb amounts and multipliers — sends a pack author looking in the wrong place. | **ACCEPTED.** The shared helper takes the noun; a test asserts a rejected mix does not mention pot fractions. |
| 31 | refuter | opt | The `getattr(..., None)` duck-typing fallback masks the very failure mode it guards against. | **ACCEPTED**, converging with 25. Direct attribute access now; the one stand-in in `test_bet_sizing.py` declares `*_mix = None` explicitly. |

**Process note.** The refuter observed uncommitted edits appearing in its
worktree mid-review — that was this session applying Codex's fixes to the same
tree while the review ran. Its verdict was against the committed `HEAD` and is
unaffected, but the overlap was avoidable and should not recur.

## T-control diff review (2026-08-15, fourth dual review)

Reviewers: Claude `refuter` (pass-with-issues — 1 med, 2 optional) · Codex
`gpt-5.6-sol` at high effort (6 findings: 3 med, 3 low). **All accepted.** Both
independently verified the blinding split, the RNG-consumption equivalence of
the `replay_run` signature change, and that the probe's de-duplicated loop
produces identical stimuli.

| # | Source | Sev | Finding | Fix |
|---|---|---|---|---|
| 32 | both | med | **The control's identity was a hand-typed label with nothing verifying the policy.** Editing `rule_breaker_decision` — the bet size, the never-fold rule — would silently change what the control *is* while every stamp and test still reported the deck as the pinned protocol control. The refuter added that the governing ticket explicitly requires "the chosen design's exact generator config (hash-pinned like T1 was)", so the diff fell short of a written acceptance bar. | **ACCEPTED — the most important finding.** Added `CONTROL_POLICY_DIGEST`, a behavioural fingerprint over a fixed 12-hand replay, asserted at build time by `assert_control_policy_pinned`. Behavioural rather than a source hash on purpose: a source hash breaks on a comment edit and says nothing about play, while this changes if and only if the control's play changes. Measured and pinned as **pack-independent**, which is what makes it a legitimate pin for a control that must outlive pack edits. Three tests including a negative case. |
| 33 | Sol | med | `run_s6_dryrun.py:224` still read the removed `pins["control"]["config_hash"]`, so the official dry run would have died with a `KeyError`. The full suite missed it because nothing exercises that script. | **ACCEPTED — a genuine break.** Updated to the new keys, along with two stale "pinned control config" messages in the same file. |
| 34 | Sol | med | Governing documents still defined the old control: `flywheel-s6.md` §Design rules and its appendix, and the execution checklist's reading of `non_protocol`. | **ACCEPTED.** Marked superseded rather than overwritten — the original text stays for the record with a dated supersession note above it, which is the amendment convention the research on preregistration practice specifically endorses. |
| 35 | Sol | low | `test_the_control_survives_a_persona_pack_change` patches `detection_corpus.load_persona_packs`, but the OLD code path loaded its baseline independently through `counterfactual`, so the test would have passed against the old implementation too. | **ACCEPTED.** The claim it was making is instead carried by an end-to-end check: all six packs were genuinely edited on disk and the full corpus suite ran — 89 passed, where 24 had failed before the change. That is the real proof the blocker is gone; the monkeypatch test remains as a cheap guard. |
| 36 | Sol | low | The replay test compared only action histories, so boards and stacks were unverified, and "actually rule-breaking" was established only as "different from production" — any deterministic policy would pass. | **ACCEPTED.** Now compares whole terminal states, and asserts the two traits that make this a usable control: it never folds, and its aggression lands on the fixed 7.77 size. |
| 37 | Sol | low | The leak-check forbidden list gained `CONTROL_POLICY_ID` but not the policy's source path, also newly secret. | **ACCEPTED.** Added `CONTROL_POLICY_SOURCE` as a constant, used in both secret records and added to the forbidden list. |
| 38 | refuter | opt | `replay_run` now passes the real persona pack to a custom `decision_fn`, where the probe's old copied loop passed `None`. Harmless today (the one custom policy ignores it) but undocumented. | **ACCEPTED.** Noted in the docstring for whoever writes the next custom policy. |

**No findings rejected.** The convergence is worth noting: both reviewers
independently landed on the identity-pinning gap, and both independently
cleared the blinding split — which is the property that would have been most
expensive to get wrong.

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

## T3 + T4 build record (2026-08-15) — PR-2

**Bottom line: the seat split and the edge softening both shipped, both gates
pass, and the roster stayed distinguishable — separation 1.75071 against a
required 1.254429, from a pre-slice baseline of 1.792042. Twenty-one pinned
tests moved across the two commits and every one was adjudicated. Three things
could not be settled inside this slice and are escalated below rather than
absorbed.**

Commits: `d4a66df` (T4, seat gradients) then `f214e76` (T3, edge softening).
The ticket sequences T3 before T4; the order was swapped because T4 restructures
the very nodes T3 softens, so softening first would have meant authoring the
same edges twice. Nothing else about either ticket changed.

### What was built

**T4 — seat gradients.** `vs_rfi`, `vs_limpers` and `vs_3bet` are answered per
seat in all six packs. `vs_4bet` is deliberately excluded: facing a 4-bet the
decision is hand strength and stack depth, and position barely moves it, so a
gradient there would be manufacturing a distinction real players do not make.

Regulars get four seat bands, recreationals two. A player who does not adjust
to position IS the archetype for the station and the fish, so those two respond
to money already invested — wider from the blinds — and stay seat-blind
elsewhere. This is the same principle the theory review established for T2b's
sizing values, applied to ranges.

**T3 — edge softening.** The recreationals' step functions are gone: blocks 19%
to 56% of the deck wide that played one way at weight 1.0 now play at 0.86-0.90
with an adjacent band outside them at 0.24-0.49. The regulars were left alone
because their boundaries are already ramps — emitted opening ladders carry a
0.4-0.5 tail band and their response nodes are tiered.

### The design rule that made both safe

**Hold each persona's table-realised frequency; change only where it comes
from.** Four of the separation floor's ten statistics (vpip, pfr, three_bet,
fold_to_3bet) are driven by exactly these nodes, so a slice that widened ranges
would have spent separation headroom on nothing. Every band was authored
against measured seat volumes — how often each seat actually faces each
decision, from a 6,000-hand export at seed 601 — and every fringe was sized to
return what shaving the core removed.

It worked. Per-facing combo-weighted continue, before to after:

| facing | tag | lag | nit | maniac | station | fish |
|---|---|---|---|---|---|---|
| vs_rfi | 16.94→17.05 | 26.46→26.77 | 5.82→6.15 | 38.13→37.58 | 56.56→56.61 | 43.59→44.05 |
| vs_limpers | 8.97→8.98 | 12.58→12.63 | 4.13→4.45 | 45.48→45.50 | 56.56→56.53 | 28.51→28.49 |

Meanwhile the fold-to-a-raise SPREAD across seats, which was flat by
construction, is now 79.8–87.8 for the tag, 65.0–79.1 for the lag, 55.7–67.6
for the maniac, and 34.8–46.2 for the station.

### Two defects this slice introduced and fixed rather than shipped

**The maniac's big-blind catch-all would have flatted any two cards**, breaking
audit-F11 in a seat no test covers — the F11 gate checks the cutoff only. Found
by reading the authored numbers back rather than by a test. The defensible
subset is now authored explicitly.

**The range lint caught four authoring slips**: bands that played Q9s while
folding QJs, 96s while folding 97s, A5s while folding A7s, and an AQo 3-bet
sitting below the weaker tier beneath it. All fixed in the packs. Only the
pre-existing polar wheel-ace exception and the premium-first tiering idiom were
added to its inventory, and the two entries that MOVED (station 1.0 → 0.88) are
the softening working rather than a new defect.

### The finding worth carrying forward

**Several test helpers select a persona node with a first-match `next()`,
silently assuming one node per facing.** Once nodes split by seat, those helpers
returned whichever band happened to be authored first — so a pin could move
several points while every seat's behaviour was intact. Two dossier gates were
affected. Both now average over the nine seats, which is the population policy
they were always about and which reduces exactly to the old value for an unsplit
pack.

**The proof that this was a measurement bug and not a behaviour change: after
the repair, every pin they feed passed UNCHANGED** — maniac 0.3073, lag 0.6012,
and both nm4bet arrival gates. Nothing was re-recorded to make them green.

This is the same failure mode as the shadowed-mix trap, one layer up: the packs
grew an axis and the instruments reading them did not.

### Escalated — three things this slice could not settle

**1. The coverage-ratio criterion cannot be met by any slice that makes bots
fold less, and spec §7.1 states it as pass/fail.** Villains continuing more
often hands hero more POSTFLOP decisions, and postflop grading coverage is
about 7% — the `T-cover` defect — so the ratio falls even when nothing is lost.
Measured at 2,000 hands across three seeds: overall −0.73pp, preflop −0.91pp
and bracketing zero, against a preflop seed-to-seed spread of about 14pp. The
400-hand single-seed fixture reported −3.05pp, roughly four times the effect.
Recommend the criterion be restated per street, or against graded count at a
fixed sample, before the next improvement slice is judged by it.

**2. The `r9d_s5` fold-rate ladder was passing on a sample-specific
coincidence.** Its `nit > tag > {lag, fish, maniac} > station` ordering breaks
on the PRE-SLICE packs at three times the pinned sample. This slice narrowed
the assertion to what holds in all four measurements. Separately and more
importantly, the slice LOWERED the regulars' rise (tag .0867 → .0570, nit
.1563 → .0918 at the pinned N), with a plausible mechanism: they now defend the
blinds wider, so they reach barrel nodes with weaker holdings that were folding
anyway. The λ mechanism is untouched and its node-level gate still passes.
Whether the population effect should be re-fitted is an owner call.

**3. `test_personas.py::_stats` weights all nine seats equally**, including UTG,
which can never face `vs_rfi` because it acts first. While every node was
position-blind that was harmless; now it measures a different quantity from
table-realised frequency, and the two diverged by about 2pp for the tag. This
slice satisfied BOTH — the authored bands hold the pinned bands and the volume-
weighted aggregate — rather than changing the measurement to suit itself. The
measurement question is left open deliberately.

### Verification

- `./scripts/verify.sh` equivalent: 2022 passed, 3 skipped. `ruff check .` clean.
- Gate at seed 601 after T4: separation 1.747895, labels 6/6, determinism ok.
- Gate at seed 601 after T3: separation 1.75071, labels 6/6, determinism ok.
- Positive tests the gates cannot see: `test_persona_positional_gradients.py`
  (17 named seat pairs must play some hand materially differently, plus a
  negative case that flattens every band and must fail) and
  `test_persona_range_edges.py` (the width rule, plus a negative case that
  restores the station's 56% block).
