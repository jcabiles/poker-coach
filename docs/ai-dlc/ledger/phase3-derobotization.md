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


## T3 + T4 build record and dual review (2026-08-15) — PR-2

**Bottom line: shipped after a three-reviewer round returned fail / fail /
needs-work, whose findings changed the packs rather than the wording. Two
reviewers independently found that the first draft re-introduced an any-two
cold-call the F11 audit had already struck, and the theory reviewer found the
big blind defending the same as the button. Both are fixed. The roster stays
distinguishable — separation 1.68 to 2.04 across five seeds against a required
1.254429 — and hero's grading coverage, re-measured at the tip, is flat.**

Commits: `d4a66df` (T4, seat gradients), `f214e76` (T3, edge softening),
`60a7e5c` (docs), then the review rework. The ticket sequences T3 before T4;
the order was swapped because T4 restructures the very nodes T3 softens.

### What shipped, stated precisely

The earlier draft of this section said all three facings are answered per seat
"in all six packs". That was wrong, and both a reviewer and this pack's own
`_doc` entries contradicted it. What actually shipped:

| pack | `vs_rfi` | `vs_limpers` | `vs_3bet` |
|---|---|---|---|
| tag | BB · SB · CO+BTN · rest | CO+BTN · rest | CO+BTN · SB+BB · rest |
| lag | BB · SB · CO+BTN · rest | CO+BTN · rest | SB+BB · rest (opener stratum only) |
| nit | BB · SB · CO+BTN · rest | CO+BTN · rest | CO+BTN · SB+BB · rest |
| maniac | BB · SB · CO+BTN · rest | already positional before this slice | SB+BB · rest (opener stratum only) |
| calling_station | BB · SB · rest | position-blind, deliberately | position-blind, deliberately |
| passive_fish | BB · SB · rest | position-blind, deliberately | position-blind, deliberately |

The recreationals' exclusions are archetype reasoning, not omissions: over-
limping and calling down are where a weak player adjusts least, and
`fold_to_3bet` is those two packs' single strongest separating statistic (7.8
and 5.5 against a next-lowest of 28.8), so it is the worst place to spend
separation headroom for the least realism.

`vs_4bet` is excluded from the split everywhere. The theory reviewer supplied
affirmative evidence rather than agreement: because the upstream 3-bet range is
now seat-dependent, that node already inherits a per-seat conditional spread
for free — conditional fold-to-4bet runs 63.6 to 73.7 across seats for the tag
and 64.5 to 78.2 for the lag, in the right direction, because the big blind's
3-bet range is the most value-heavy. Splitting it would double-count.

### The design rule, and the way the first draft applied it wrongly

**Hold each persona's frequency; change only where it comes from.** Four of the
separation floor's ten statistics are driven by these nodes, so a slice that
widened ranges would spend headroom for nothing.

The rule is right. The first draft applied it by spreading the pre-existing
FLAT value symmetrically around itself, which makes the flat number the centre
of the shape — and produced a tag whose big blind defended 20.17% against its
button's 20.15%. The seat that pays 2bb into 4.5 and closes the action is not
the same seat as the one paying 3bb with two players behind it.

Corrected by deriving the SHAPE first (big blind widest by a clear margin, then
CO/BTN, then early, then the small blind, which is worst) and then scaling to
the held aggregate. The constraint was far looser than the draft treated it:
the big blind carries about 18% of `vs_rfi` volume, so a realistic widening
moves the node aggregate by under 2pp against 0.5 of separation headroom.

| persona | BB ÷ CO+BTN, first draft | shipped |
|---|---|---|
| tag | 1.00 | 1.42 |
| lag | 1.11 | 1.43 |
| nit | 1.55 | 1.55 |

The nit was flagged in the brief as a possible cop-out and is in fact the best
of the three: judged by ratio rather than percentage points, its big blind is
2.14× its small blind, the largest relative spread on the roster.

### Two metrics, and which one the claim is about

The first draft claimed "table-realised frequency is HELD" while reporting a
number that is nothing of the kind. Both are reported here, labelled.

**Realised** — measured from self-play, 12,000 hands across three seeds at the
pinned lineup, counting what actually arrives at each node. This is the claim
that matters and the one a detector would see.

| persona | `vs_rfi` | `vs_limpers` |
|---|---|---|
| calling_station | 65.97 → 65.41 | 60.32 → 58.69 |
| lag | 27.71 → 27.20 | 18.65 → 19.02 |
| maniac | 37.30 → 37.06 | 56.04 → 55.70 |
| nit | 5.62 → 6.68 | 16.26 → 14.87 |
| passive_fish | 51.26 → 49.87 | 39.22 → 37.38 |
| tag | 16.90 → 17.34 | 16.14 → 15.49 |

Every move is within 1.9pp, mean 0.9pp. **Before the review rework the same
measurement read −3.53pp for the station and −3.58pp for the fish** — the
reviewer's finding, and the reason the packs changed rather than the sentence.

**Authored width** — combo-weighted over the whole deck, then weighted by
measured seat volume. Useful for authoring, not a population claim, because the
arriving population at a node is not deck-uniform: early-seat `vs_rfi`
decisions are dominated by the limped-then-raised path, so they sit inside the
node's core. Shaving a core and repaying in a fringe the conditional population
rarely contains holds this number while moving the realised one.

| persona | `vs_rfi` | `vs_limpers` |
|---|---|---|
| tag | 16.94 → 17.01 | 8.97 → 9.16 |
| lag | 26.46 → 26.82 | 12.58 → 12.63 |
| nit | 5.82 → 6.21 | 4.13 → 4.56 |
| maniac | 38.13 → 37.58 | 48.25 → 48.26 |
| calling_station | 56.56 → 57.73 | 56.56 → 56.53 |
| passive_fish | 43.59 → 43.98 | 28.51 → 26.81 |

### Three defects caught before shipping, one of them twice

**The recreationals cold-called an open with any two cards.** Both independent
reviewers found it, and the committed theory contract settles it outright: F11
requires the `vs_rfi` `*` catch-all to be 3-bet-or-fold, so this was a contract
violation rather than an open question. The station was calling 32o from the
small blind one time in three. Removed; the defensible subset is authored
explicitly, exactly as the maniac's big blind already had it. That the same
slice congratulated itself for catching this in one pack while shipping it in
two others is the sharpest thing the review found.

**The maniac's big-blind catch-all** would have done the same, in a seat no
test covers — caught during the build by reading the authored numbers back.

**Four authoring slips the range lint caught**: bands playing Q9s while folding
QJs, 96s while folding 97s, A5s while folding A7s, and an AQo 3-bet below the
weaker tier beneath it. Fixed at source rather than inventoried.

### What the reviewers found in the tests, and what changed

Every positive test this slice added was gameable as first written, and all
three reviewers said so independently.

- **The gradient test scored the MAXIMUM per-hand difference**, so moving one
  hand class satisfied an entire seat pair while the other 168 stayed
  identical. Replaced with the share of a persona's own continuing mass played
  differently — scale-free, so a nit is judged against its own range rather
  than against a deck it never plays. Every declared pair now clears 15% with
  margin (19.7% to 70.2%), and a new negative case pins the exact evasion.
- **The width rule examined each mix separately**, so one 56%-wide
  deterministic block spelled as four sub-threshold mixes would have passed
  unchanged. Now summed per node and action, with a negative case that spells
  the station's old block six ways and must still fail.
- **The ramp test counted the untouched premium tier** toward its three
  required levels, so a node with exactly one softened step passed as a ramp.
  Now counts only levels strictly between 0 and 1.
- **`_opener_fold_to_3bet` was mathematically wrong.** It averaged the response
  policy across seats, aggregated the opening range across seats, and multiplied
  the two aggregates. E[policy] × E[range] is not E[policy × range] once both
  vary by seat. Now paired per seat. Every dossier pin it feeds still passes
  unchanged.
- **The "every pin passed unchanged" proof was weaker than claimed.** For the
  maniac and lag the `cold` stratum is a single position-blind node and every
  consumer defaults to it, and the arrival helper normalises the /9 away — so
  those pins return the old value by construction. The repair is still correct;
  the evidence offered for it was not, and is withdrawn.
- **"Reduces exactly to the old value" was false.** Sum-then-divide is exact
  only for dyadic weights; 0.45 comes back as 0.44999999999999996 on five of
  six base packs. Every gate reading it is a tolerance or a bound, so nothing
  breaks today — but the claim was wrong and is corrected in place.

### Verification at the shipped tip

- Suite 2027 passed, 3 skipped. `ruff check .` clean.
- Five-seed gate: PASS at every seed — 1.947995 / 1.683556 / 2.002838 /
  1.806508 / 2.041750 at seeds 601-605, against a required 1.254429; labels
  6/6 and determinism ok at all five. All five carry the same config hash
  `c609bd6458872`, which is how the run proves the packs did not move under
  it — an earlier run of this gate was discarded precisely because pack
  metadata was edited while it was in flight.
- Hero grading coverage, re-measured at 2,000 hands across three seeds:
  overall 0.2475 → 0.2467 (−0.08pp, flat), preflop 0.5718 → 0.5634. The
  400-hand single-seed fixture reads 0.2753 → 0.2568, which is the instrument,
  not the effect — its preflop ratio spans about 14pp across seeds at 2,000
  hands.
- Realised per-node rates: table above, all within 1.9pp.

### Escalated

**1. `line_sensitivity` is out of fit, not an open question.** ⛔ CLOSED 2026-08-16 — this did not reproduce at the shipped tip; see T5's section below for the re-measurement and the owner ruling. Kept as written because the reasoning below is what the ruling overturned, and deleting it would hide that.

**Original text:** The theory
reviewer corrected the earlier framing. Its closed-loop statistic moved about
40% (tag .0867 → .0570, nit .1563 → .0918 at the pinned N), which by the theory
contract's §2 makes it an un-refit constant. A NEW inversion also appeared that
the weakened `_R9D_S5_ORDER` tier would otherwise absorb, and it is named here
rather than left implicit: **at N=24,000 the tag now reads .0429 against the
passive_fish's .0515**, where the tag was above the fish at every pre-slice
sample. A fish reacting to a persistent hostile line more than a tag is
backwards for both archetypes. The λ mechanism is untouched and its node-level
gate still passes, so this is a re-fit of one seed against the new arrival
distribution, not a mechanism change. **Owner call.**

**2. The `_R9D_S5_ORDER` weakening was done before that owner decision** ⛔ CLOSED 2026-08-16 — the four-tier order is RESTORED; see T5's section. Original text:, which
a reviewer fairly objected to, and the evidence offered for it was thinner than
presented — the pre-slice reversal it cited is 0.0016 between lag and tag, with
no uncertainty attached. It stands as the only way to ship green, and it is
disclosed in the test's own source, but it should be re-examined with item 1.

**3. The coverage-ratio criterion still needs restating even though this slice
now meets it.** §7.1 says a ticket must not reduce the ratio and also says a
moved baseline is refreshed with a recorded reason; those pull against each
other the moment bots fold less, because extra postflop decisions land in a
zone graded at about 7%. This slice comes out flat at adequate sample, so
nothing is being waved through — but the next improvement slice will hit the
same wall, and the criterion should say per-street or per-count before it does.

**4. Uniform nine-seat weighting is used in two test helpers while this ledger
escalates exactly that flaw for `test_personas.py::_stats`.** It gives UTG a
ninth of the weight at `vs_rfi`, a facing UTG can never see. Re-weighting the
nm4bet legs by measured volume moves them under a point and flips no bound, so
nothing is wrong today. The inconsistency is real and should be settled once,
in one place, rather than per helper.

### One incidental finding, recorded because it will confuse someone

**A pack `version` bump re-writes `hand_id` in every exported table.**
`config_hash` covers the pack model including `version`, `run_id` embeds
`config_hash`, and `hand_id` embeds `run_id` — so editing a version string
moves all four export digests while the cards and actions stay byte-identical.
Verified by dropping the `hand_id` column: a version-only change then leaves
the decisions digest unchanged. It cost time here, twice, and the note now
lives in `test_buyin_spread.py` where it will be read.

---

## T5 build record and dual review — postflop sizing ecology

**Bottom line: the six packs' bet sizes now overlap instead of partitioning the
roster, so a single observed bet size is much weaker evidence of which bot made
it. Table-wide the MEDIUM band went from the least-used (21.1%) to level with
LARGE (34.0% against 37.2%), and the maniac's "82.5% large or overbet" tell fell
to 51.8%. Hero grading coverage came out exactly flat. One thing found during
the build was not in the ticket and changes how this file should be read: a
persona's own bet-size distribution scales its bluff rate, so a sizing ticket is
also an aggression ticket.**

### What the ticket asked for, and what the evidence asked for

The ticket named two moves — give 0.5 real presence, give the maniac a small
size. The evidence behind it (`remeasure-2026-08-05/report_table.md` §5) named
three defects, and the third is the one with teeth: "an observant hero can read
the bettor's archetype off the bet size alone with almost no error", because the
six size bands were disjoint.

Owner ruling 2026-08-16: fix the first two AND overlap the bands across SMALL,
MEDIUM and LARGE, but do **not** hand new overbets to packs that had none. The
reason for that limit is a real constraint rather than caution — the engine
draws size independently of hand strength on purpose (theory contract F14), and
`_bluff_size_factor` actively favours the larger size on a bluff cell, so a nit
or a fish given a 1.5 would overbet-BLUFF more often than it overbet for value.
That is a worse tell than the one it removes. Consequence accepted and recorded:
"only the maniac and lag ever overbet" survives this slice.

### Measured, at the pinned lineup over 12,000 self-play hands

Bets only, RES-E buckets, matching the re-measure's own convention.

| persona | SMALL | MEDIUM | LARGE | OVERBET | off-grid |
|---|---|---|---|---|---|
| calling_station | 61.9 → 45.9 | 29.3 → 37.3 | 8.8 → 16.8 | 0.0 → 0.0 | 12.75 → 11.81 |
| passive_fish | 62.6 → 42.9 | 29.5 → 32.8 | 7.9 → 24.3 | 0.0 → 0.0 | 9.76 → 10.52 |
| tag | 26.1 → 23.8 | 29.6 → 37.9 | 44.2 → 38.3 | 0.0 → 0.0 | 8.86 → 11.33 |
| nit | 14.2 → 22.7 | 32.6 → 33.3 | 53.2 → 44.0 | 0.0 → 0.0 | 11.94 → 12.33 |
| lag | 19.4 → 21.0 | 25.1 → 34.8 | 53.8 → 42.9 | 1.8 → 1.3 | 11.02 → 10.01 |
| maniac | 7.6 → 16.2 | 13.0 → 32.0 | 64.1 → 44.7 | 15.3 → 7.1 | 17.36 → 13.52 |
| **TABLE** | **25.4 → 25.3** | **21.1 → 34.0** | **46.1 → 37.2** | **7.4 → 3.5** | — |

The maniac makes 46% of every bet at this table, which is why its row moves the
table row so much and why it was the right place to spend the effort.

**The off-grid column is not uniformly good news, and is reported rather than
picked over.** It falls for the station, lag and the maniac and RISES for the
fish, tag and nit. It is the share of a pack's bets whose final amount is no
longer the fraction it was drawn from, because the legal-bet bracket clamped it
— a min-bet clamp at the small end, an all-in clamp at the large end. Moving
mass toward the middle relieves the large end and loads the small one, so the
three packs that gained the most SMALL presence pay a little there. It is not a
coverage measurement either way; see the coverage section.

### The tell statistic, and the test that carries it

Neither gate can see any of this, so the goal needed its own measure. The one
used is the best accuracy any observer could reach naming the persona from a
single bet size, under a uniform prior: `(1/6)·Σ_s max_i p_i(s)`. Chance is
0.167.

| node | before | after |
|---|---|---|
| flat | 0.342 | 0.238 |
| cbet_dry | 0.283 | 0.220 |
| cbet_wet | 0.350 | 0.297 |
| cbet_mono | 0.283 | 0.212 |
| turn_barrel | 0.350 | 0.270 |
| river_value | 0.392 | 0.312 |
| raise | 0.392 | 0.328 |

`backend/tests/test_persona_size_ecology.py` gates it at 0.35 per node, with
three negative cases: the real pre-ticket `river_value` distributions must fail
it, a six-way-identical roster must read exactly chance, and the maniac's old
flat block must fail the separate band-presence floor. The ceiling is set at
roughly twice chance rather than at just-above-the-diff, and the band floor
(0.10) is a "can this persona make this bet at all" line, not a fitted target.

### The finding that was not in the ticket

**A persona's own size distribution scales its bluff rate.**
`personas_postflop` ~:910 multiplies `bluff_mass` by `E_s[_bluff_size_factor(s)]`
over the pack's authored sizing — the F2 joint law, "bigger bets carry
proportionally more bluffs". So re-weighting sizes moves action frequencies, not
just sizes, and T5 is not the pure data change the ticket implies.

| persona | E[factor] before → after | bluff mass |
|---|---|---|
| maniac | 1.236 → 1.074 | −13.1% |
| nit | 1.111 → 1.041 | −6.3% |
| lag | 1.063 → 1.022 | −3.8% |
| tag | 1.009 → 1.013 | +0.4% |
| calling_station | 0.863 → 0.924 | +7.1% |
| passive_fish | 0.863 → 0.950 | +10.0% |

This was **not** compensated, and the reason is that it is the engine working
rather than a side effect: a persona that bets smaller genuinely should bluff
less. It also happens to point the same way as the re-measure's other maniac
findings. It explains four of the eleven test failures this ticket produced,
including two that look alarming out of context — `test_price_tail`'s
"byte-identical" FACING-node vectors moved, and they moved for exactly the two
packs whose sizing shifted toward larger. Population AF stays in band
(`test_persona_postflop_bands` passes unchanged); the n=200 tripwire rows moved
and were re-recorded.

### Five-seed gate — PASS

```
seed 601  PASS  separation 1.774277   labels 6/6  determinism ok
seed 602  PASS  separation 1.908603   labels 6/6  determinism ok
seed 603  PASS  separation 1.841652   labels 6/6  determinism ok
seed 604  PASS  separation 1.744374   labels 6/6  determinism ok
seed 605  PASS  separation 1.935932   labels 6/6  determinism ok
                required 1.254429 · all five run_id c7efa1f14b572
```

The shared config hash across all five is how the run proves pack content did
not move under it — an earlier run in this slice was discarded for exactly that.

**Separation did not merely survive; the worst seed improved** (1.683556 →
1.744374 against the T3/T4 tip). That is the expected result rather than a
lucky one: rule 1 scores ten frequency statistics and none of them is a bet
size, so overlapping the six size distributions costs the floor nothing. The
theory review said as much at T2b — "stop treating sizing as an identity axis
at all" — and this is the measurement behind that claim.

### Hero grading coverage

Flat. Measured at 2,000 hands across three seeds, because the committed 400-hand
fixture cannot resolve a point in either direction.

| | before | after |
|---|---|---|
| preflop | 0.5642 | 0.5716 |
| postflop | 0.0347 | 0.0328 |
| **overall** | **0.2470** | **0.2470** |

Absolute graded decisions rose 4479 → 4521. **A claim made earlier in this build
and withdrawn:** that fewer off-grid bets would raise postflop coverage. It does
not — postflop grading is gated on spot shape long before bet size is examined
(the open `T-cover` item), so the unrecognisable-bet share and the coverage ratio
moved in opposite directions. The pack `_doc` entries state the narrow version.

### `line_sensitivity` and `_R9D_S5_ORDER` — both escalations closed

**Owner ruling 2026-08-16: close both, restore the gate, no re-fit.**

The T3/T4 escalation reported a new inversion (the fish out-reacting the tag to a
sustained barrel) and a ~40% collapse in the regulars' response. Re-measured at
the shipped tip, **the inversion does not exist**:

| packs | N | nit | tag | fish | lag | maniac | station |
|---|---|---|---|---|---|---|---|
| T3/T4 tip | 24000 | .0921 | .0464 | .0417 | .0561 | .0231 | .0055 |
| T5 | 24000 | .1017 | .0895 | .0445 | .0386 | .0288 | .0050 |
| T5 | 48000 | .0983 | .0788 | .0492 | .0418 | .0265 | .0057 |

The numbers the weakening rested on were taken mid-review, before the
recreationals' any-two cold-call fix landed — and that fix changed exactly which
hands those packs bring to a barrel node. A tier was dropped to accommodate a
measurement of packs that never shipped.

What was real: the ordering genuinely does turn over at the gate's pinned
N=8000, where the nit reaches only 55 in-scope nodes. **The fix is the sample
size, not the claim.** `_R9D_S5_N` is raised 8000 → 24000 (nit reaches 131), the
four-tier order `nit > tag > {lag, fish, maniac} > station` is restored, and the
nit/tag margin GROWS with N — +0.0122 at 24000, +0.0195 at 48000 — which is an
effect emerging from noise rather than noise mined for a result. It is also
λ's own prediction, fixed in the packs long before any of this was sampled.
Cost: ~74s of suite time.

No re-fit of λ, for three reasons that compound: a re-fit needs a target and no
sourced population figure for fold-to-barrel exists in this repo; the softmax law
(theory contract §2) predicts the effect to SHRINK when a persona arrives with
more marginal holdings, which is what T3/T4 made the regulars do; and the
node-level λ-exact gate is green, so tuning λ upward to move an average would
break the claim that is actually true.

### Escalated — lag's opener fold-to-3bet is sitting on its dossier floor

Not T5's, not fixable inside T5, and it will bite the next preflop slice.

`test_n3bstrata_production_opener_blend_in_dossier_band` failed at n=12000 with
0.4295 against a [0.43, 0.53] band. T5 changes no preflop node, so it cannot move
this statistic's true value — and it does not:

| packs | n=12000 | n=36000 |
|---|---|---|
| pre-T5 | 0.4367 (clears by 0.0018) | 0.4318 |
| T5 | 0.4295 (fails) | 0.4342 |

At the settling n, T5 moves it +0.0024 — inside noise and in the opposite
direction from the failure. **What moved it is T3/T4**: the test's own history
records 0.4914 and 0.4722 for this blend, and the seat-split opening ranges
changed which hands arrive at the `vs_3bet` node, dragging it to ~0.433. Nobody
re-read it at a settling n at the time.

The gate is re-powered to n=36000 so it measures the pack rather than one draw
of the shared stream. **Green here is not comfortable and should not be read as
comfortable**: 0.4342 against a 0.43 floor is 0.4pp of margin, and the Wilson
interval straddles the floor at every n tried. The band was deliberately not
widened — that is the band-laundering §11 item 7 exists to catch — and the
sibling pin on lag's *authored* policy passes unchanged, which localises the
drift to the arriving mix rather than the policy.

**Owner decision wanted: a re-tune of lag's `vs_3bet` opener node is probably
owed.** It is a preflop edit, outside T5's scope, and T2b is the next thing to
touch that area.

### Fixtures re-recorded, once, with pack content frozen

Four files, all for stream displacement plus the six version bumps: the coverage
baseline (1289/331 → 1295/332), the limper-belt counts (all nine pairs), the four
buy-in export digests, and the n=200 golden stats. Two behaviour-pinned sets were
re-recorded for the bluff-mass coupling rather than for displacement: the
price-tail HEAD vectors and plateaus, and the N-LOGIT bluff-cell pins. In both
cases the DEFECT each file demonstrates is unchanged — the price-tail plateau is
still exactly flat across all five tail prices, asserted at re-record time rather
than assumed.

### Mistakes made in this build, recorded because the pattern repeats

- **The pack patcher's first version rewrote the wrong `sizing` block.** An
  unanchored `"sizing": {...}` regex matched the pack's TOP-LEVEL preflop lever
  block (`open_bb`, `threebet_mult`, `fourbet_mult`) and replaced it with pot
  fractions. Caught by reading the diff before running anything. The patcher now
  anchors on indentation and asserts exactly one match per key.
- **A measurement that compared two pack sets in one process returned the same
  answer twice.** `_OPENER_BLEND_CACHE` is keyed on `(persona, n, checkpoints)`
  and is pack-blind, so the second load silently read the first's result. It
  produced a confident and completely wrong conclusion ("T5 does not move this
  statistic, identical to four decimal places") that happened to agree with the
  right answer for the wrong reason. Re-run in separate processes.
- **The price-tail plateaus were first regenerated outside the `head` fixture**,
  which sets `_PRICE_TAIL_K = 0.0`. The tail grid sits above the anchor, so the
  values were the live ones, not the HEAD ones. Caught by noticing they
  disagreed with an earlier direct reading.
