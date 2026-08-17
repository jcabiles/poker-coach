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
it. Measured in live play, the best accuracy an observer could reach naming the
bettor's CLASS from one bet size falls 0.557 → 0.441 against a chance floor of
0.333, and the maniac's "80.7% large or overbet" tell falls to 58.5%. Hero
grading coverage did not measurably change. What is NOT fixed: an overbet is
still a maniac tell, P(maniac | a 1.5× bet) = 0.77 with real base rates, and
that is now a disclosed exemption rather than a solved problem. One thing found
during the build was not in the ticket and changes how this file should be read:
a persona's own bet-size distribution scales its bluff rate, so a sizing ticket
is also an aggression ticket.**

⚠️ **Every number in this section is measured at the BRANCH TIP** (three review
rounds), against `ed4d108`. Two earlier versions of it quoted the first
commit's packs after later commits had changed them — twice — which is how a
coverage verdict of "exactly flat" survived into a commit whose own test file
recorded the opposite. Numbers are stated once, here, and the pack `_doc`
entries point at this section instead of copying it.

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

### Measured in live play, 12,000 self-play hands

**The counting rule, stated because three reviewers measured this three ways and
got three answers.** Every postflop BET or RAISE made by a bot at a nine-seat
all-bot table (`table.play.bot_decision`, the live path, three seeds ×
4,000 hands), bucketed by RES-E cutoffs on the size it ACTUALLY BET as a
fraction of the pot before the action. Clamped and off-grid bets are bucketed,
not excluded. That last choice is the one that matters and it is deliberate: a
bet clamped to all-in is an overbet to anyone watching, whatever fraction it was
drawn from, and this roster is being measured against an observer. Excluding
them — the earlier convention — halves the OVERBET column and makes the roster
look better than it plays.

| persona | SMALL | MEDIUM | LARGE | OVERBET |
|---|---|---|---|---|
| calling_station | 55.1 → 42.1 | 28.4 → 34.0 | 14.0 → 21.0 | 2.5 → 2.9 |
| passive_fish | 43.2 → 28.6 | 25.7 → 30.1 | 24.4 → 30.6 | 6.8 → 10.7 |
| tag | 19.5 → 21.6 | 26.7 → 29.0 | 43.3 → 39.4 | 10.5 → 10.1 |
| nit | 11.0 → 20.8 | 27.6 → 26.3 | 48.6 → 44.4 | 12.9 → 8.6 |
| lag | 15.0 → 17.7 | 22.2 → 29.4 | 49.7 → 41.2 | 13.0 → 11.7 |
| maniac | 6.6 → 13.7 | 12.6 → 27.8 | 54.0 → 43.0 | 26.7 → 15.5 |
| **TABLE** | **20.3 → 21.2** | **19.5 → 29.4** | **43.3 → 37.7** | **16.9 → 11.7** |

MEDIUM was the least-used band by a wide margin and is now the second most used:
its gap behind LARGE closes from 23.8 points to 8.0. The maniac makes 45% of
every bet at this table, which is why its row moves the table row so much and
why it was the right place to spend the effort.

### The tell statistic, and the test that carries it

Neither statistical gate can see any of this, so the goal needed its own
measure. Two are used, and the distinction between them is the single most
important correction the reviews forced.

**The claim is a CLASS read.** The 2026-08-05 finding is "SMALL meant station or
fish, LARGE meant tag/lag/nit, OVERBET meant maniac" — a statement about three
archetype classes, not six packs. A per-persona statistic is diluted by exactly
what the finding is about (the two recreationals being near-identical to each
other, the three regulars likewise), so an edit that blurs the regulars among
themselves improves the per-persona number while leaving the class read intact.
The first draft of the gate made that mistake; the second fixed it for the
accuracy statistic and left it in the posterior.

Measured on realised play, uniform prior over classes (chance 0.333):

| statistic, realised | `ed4d108` | first commit | branch tip |
|---|---|---|---|
| class tell | 0.557 | 0.443 | **0.441** |
| persona tell (chance 0.167) | 0.286 | 0.239 | **0.235** |
| P(maniac \| 1.5× bet), real base rates | 0.885 | 0.800 | **0.768** |
| class posterior, `cbet_wet` @ 0.33 | 0.994 | 0.985 | **0.717** |
| class posterior, `river_value` @ 0.33 | 0.843 | 0.782 | **0.582** |
| class posterior, `turn_barrel` @ 0.33 | 0.929 | 0.714 | **0.718** |

**`backend/tests/test_persona_size_ecology.py` reads the AUTHORED distributions,
and that is a regression guard rather than a measurement.** The realised
distribution is not the authored one — the bluff-size coupling tilts the weights
and the legal-bracket clamp moves the amount — so the table above is the claim
and the test file is what stops a future pack edit from undoing it. Four gates,
each with a negative case that fails for the reason it names:

| gate | ceiling | basis | roster's worst |
|---|---|---|---|
| class accuracy | 0.667 | 2× chance (1/3) | 0.556 `cbet_wet` |
| persona accuracy | 0.333 | 2× chance (1/6) | 0.297 `cbet_wet` |
| persona posterior | 0.70 | certainty line, not chance | 0.647 `turn_barrel` @ 1.5 |
| class posterior | 0.85 | certainty line, not chance | 0.800 `cbet_wet` @ 0.33 |

The two posterior ceilings are judgement calls and are labelled as such in the
file. They stop a size being PROOF of identity, not evidence of it; a posterior
has no chance floor to derive from, because its floor depends on how many packs
author the size at all. Claiming one principle covered all four — which an
earlier version of that file did — dressed a chosen number as a derived one.

The class posterior gate scores only the multi-member classes. The maniac is a
class of one, so its class posterior is its persona posterior wearing a
different hat, and gating it twice would turn the file into a list of
exemptions for the archetype that is supposed to be recognisable.

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
seed  separation  labels  determinism  nit's deterministic-context share
601   1.935172    6/6     ok           0.161
602   1.640092    6/6     ok           0.170
603   1.737261    6/6     ok           0.148
604   1.873787    6/6     ok           0.178
605   1.880487    6/6     ok           0.152
                  required separation 1.254429 · determinism ceiling 0.20
```

Run at the branch tip, after two review rounds. Two earlier runs in this slice
also passed and are superseded: 1.744–1.936 before the first review, 1.779–1.934
after it. The shared config hash across all five seeds is how each run proves
pack content did not move under it — an earlier run was discarded for exactly
that.

**The nit's column is recorded because this gate went RED once during the second
review round, on determinism rather than separation, and only for that pack.**
It is the one persona for which the 20% ceiling is a live constraint; the rest
run between 0.029 and 0.140. Anything that reduces how often the nit bets should
expect to be measured against it. The account is under **Accepted, and the packs
changed as a result**.

**Separation did not merely survive; the worst seed improved twice** (1.683556
at the T3/T4 tip → 1.744374 before review → 1.779513 after the review's pack
corrections). That is the expected result rather than a
lucky one: rule 1 scores ten frequency statistics and none of them is a bet
size, so overlapping the six size distributions costs the floor nothing. The
theory review said as much at T2b — "stop treating sizing as an identity axis
at all" — and this is the measurement behind that claim.

### Hero grading coverage — no measurable change, and the sample says why

Measured with the committed `measure_split()` at 2,000 hands across six seeds
(20260718–20260723), because the committed 400-hand fixture cannot resolve a
point in either direction.

| | `ed4d108` | branch tip |
|---|---|---|
| preflop | 0.569755 | 0.571013 |
| postflop | 0.032769 | 0.032944 |
| **overall** | **0.250770** | **0.251215** |

**Coverage did not measurably change, and this quantity's history in this slice
is the argument.** Five readings of it were taken: +0.52pp (one seed, 400
hands), −0.34pp (three seeds), +0.02pp (six seeds), −0.12pp (six seeds, after
the second review's first pack attempt) and +0.04pp (six seeds, the shipped
packs). The sign moved every time the sample or the packs moved. The per-seed
overall ratios at the tip run 0.203, 0.240, 0.258, 0.260, 0.266, 0.279 — a
spread of 7.6 points around a difference of 0.04. There is no effect here to
report in either direction.

**Do not use "both components moved the same way" as evidence, and this slice
produced the counterexample.** An earlier version of this section preferred a
six-seed reading over a three-seed one on exactly that reasoning. At the pack
values this round first tried, preflop rose to 0.570682 and postflop to
0.033492 while the overall ratio FELL to 0.249577 — both components up, the
ratio down. It is not a paradox: postflop decisions grade at about 3% and
preflop ones at about 57%, so moving decisions toward the postflop streets
lowers the overall ratio while improving both halves of it. The overall figure
is a ratio over a different denominator, not an average of the two components,
so their agreeing tells you nothing. (At the SHIPPED values all three happen to
rise, which is why the counterexample is quoted from the intermediate state
where it was measured rather than from the table above.)

**A claim made earlier in this build and withdrawn:** that fewer off-grid bets
would raise postflop coverage. Postflop grading is gated on spot shape long
before bet size is examined (the open `T-cover` item), so the two are only
loosely coupled and the unrecognisable-bet share is not a coverage measurement.

### `line_sensitivity` and `_R9D_S5_ORDER` — both escalations closed

**Owner ruling 2026-08-16: close both, restore the gate, no re-fit.**

> ⚠️ **HALF OF THAT RULING WAS LATER WITHDRAWN, AND THE OWNER SHOULD KNOW WHY.**
> "Restore the gate" was ruled on the evidence set out below, and the evidence
> was wrong — not the ruling. The next review round showed the four-tier order
> fails on independent seeds, so the restoration was withdrawn and the gate is
> back at three tiers, which is where `ed4d108` already had it. "Close both" and
> "no re-fit" stand unchanged. The account is under **Accepted, and a gate
> change was WITHDRAWN**; the section below is left in place because it is what
> the ruling was made on, and deleting it would hide that.

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
- **A re-record script overwrote the population BANDS with golden-stat
  triples.** Third instance of the same root cause as the pack-patcher bug
  above, and the one that got furthest: the script found its target with
  `next(line for line in file if line.startswith(f'"{persona}": ('))`, which
  matches the FIRST such line in a 10,000-line file. `BANDS` is defined at line
  2567 and `_GOLDEN_STATS_N200` at 3645, so all six band rows were replaced by
  three-float tuples and `af_band` became a float. It surfaced as six
  `TypeError: cannot unpack non-iterable float object` failures rather than as
  an assertion, which is the only reason it was obvious — a scripted edit that
  had happened to write well-formed bands would have silently re-anchored six
  population gates.

  The lesson, now applied to every re-record helper in this slice: **anchor a
  scripted edit on the enclosing STRUCTURE, not on a line prefix.** The fixed
  version indexes from `text.index("_GOLDEN_STATS_N200 = {")` and rewrites
  between that brace and its match. Line prefixes are not unique and a file
  this size guarantees it.

### Dual review of T5, and what it changed

**Three reviewers, nineteen findings, and the review overturned a change rather
than polishing one. The headline positive test was measuring the wrong thing,
one gate change was withdrawn entirely, and three factual claims in this ledger
were wrong. All of that is below; none of it was folded in silently.**

Reviewers: the `refuter` (Opus, verdict FAIL), Codex `gpt-5.6-sol` at high
effort (four confirmed defects), and the `persona-realism-theory-reviewer`
(verdict NEEDS-WORK). Each was briefed on the diff alone, not on this ledger's
reasoning.

#### Accepted, and the pack values changed as a result

**1. The positive test scored the wrong population (refuter, HIGH).** The
2026-08-05 finding is a CLASS read — "SMALL meant station or fish, LARGE meant
tag/lag/nit, OVERBET meant maniac". The test scored per-PERSONA accuracy, which
is diluted by exactly the thing the finding is about: the two recreationals
being near-identical to each other, and the three regulars to each other. So an
edit that blurred the regulars AMONG THEMSELVES would have lowered the number
while leaving the class read untouched — a no-op-shaped pass. The class
statistic is now the headline gate and the per-persona one is a supporting
check. Measured, chance 1/3:

| node | class tell before | after |
|---|---|---|
| flat | 0.650 | 0.451 |
| cbet_dry | 0.539 | 0.407 |
| cbet_wet | 0.694 | 0.568 |
| cbet_mono | 0.533 | 0.402 |
| turn_barrel | 0.678 | 0.516 |
| river_value | 0.711 | 0.546 |
| ~~raise~~ | ~~0.756~~ | ~~0.612~~ |

⚠️ **The `raise` row is struck out and the sentence that followed it is
withdrawn.** It read "the class read is weakened, not removed: `raise` still
runs at 1.8× chance." The next review round proved that node unreachable — no
bot can read a `raise` sizing block — so both the row and the conclusion drawn
from it were about a distribution nothing plays. The worst REACHABLE node is
`cbet_wet`. See the second review below.

**2. A rare size can be a perfect tell that no average can see (Codex, HIGH).**
Both accuracy statistics average over sizes, so a size used by exactly one
persona contributes only that persona's small weight while being a certain
giveaway whenever it occurs. True of the shipped packs, not merely possible: the
1.5 was authored by the maniac ALONE at `flat`, `cbet_wet` and `turn_barrel`
(posterior 1.000), and no regular authored a 0.33 at `river_value`, so a
third-pot river bet named "station or fish" with certainty. Three pack fixes
followed — lag's existing overbet extended to `cbet_wet` and `turn_barrel`, and
a 0.33 added to all four regulars' `river_value`. A new gate scores the
posterior directly. The one remaining certainty cell, the maniac's overbet LEAD,
is allowlisted by name: an overbet lead is not a habit of any other archetype,
and authoring one purely to flatten a statistic is the trade this slice refuses.

⚠️ **Half of that fix was withdrawn by the next round.** The `cbet_wet` half of
the overbet extension was a fitted value and weak poker, and it is gone; the
`turn_barrel` half stays. The new gate it describes was ALSO scored on the wrong
population — per-persona, the very dilution item 1 above is about — so it could
not see a size that names a CLASS outright, which two cells still did. Both are
handled in the second review below. The `river_value` additions stand.

**3. T5 moved one node the wrong way and nothing caught it (refuter, MED).**
tag `cbet_dry` LARGE went 0.10 → 0.06 as a side effect of holding the pinned
dry-board mean under 0.45. Restored to 0.10 with the mean at 0.4366.

#### Accepted, and a gate change was WITHDRAWN

**4. The `_R9D_S5_ORDER` restoration does not survive independent seeds
(refuter and Codex, independently).** The four-tier order was restored on two
claims, and both were bad. "It does not reproduce" was true only of the specific
fish-above-tag inversion; the four-tier order fails at the T3/T4 tip too, for a
different reason (tag .0464 below lag .0561). And "the margin grows with N
(+0.0122 at 24000, +0.0195 at 48000)" is a two-point read on ONE seed pair whose
48000 sample CONTAINS the 24000 one — the seed schedule is a prefix, so it is an
extension, not a replication. Measured on genuinely independent seed pairs at
N=24000:

| seed pair | four-tier | three-tier |
|---|---|---|
| 20260802 / 20260803 | PASS | PASS |
| 31415926 / 27182818 | **FAIL** | PASS |
| 99887766 / 11223344 | PASS | PASS |

Seed-to-seed spread swamps the N trend. **The restoration is withdrawn and the
three-tier order stands.** The sample-size raise (8000 → 24000) is kept on
separate evidence: at 8000 even the three-tier order turns over, because `nit`
reaches only 55 in-scope nodes.

This also revises what was reported to the owner. The 2026-08-16 ruling ("close
both, restore the gate, no re-fit") was given on the strength of a measurement
that has not held up. The no-re-fit half is unaffected and stands; the
restoration half is withdrawn on evidence that arrived after the ruling.

#### Accepted as corrections to this ledger's own claims

**5. "Every AF falls" is false.** The three packs that now bet smaller lose
aggression; the two that bet larger gain it (station 0.391 → 0.396, fish 0.873 →
0.991). Corrected in `test_personas_postflop.py`.

**6. The six bluff-mass percentages are FLAT-BLOCK figures, not persona-wide
(Codex, MED).** Four packs carry `sizing_by_node`, where the sign can reverse:
nit `cbet_dry` +3.2%, lag `cbet_mono` +2.3%, tag `river_value` −3.9%. The
percentages are correct for the distributions the re-pinned fixtures actually
measure; the persona-level framing was too broad.

**7. "A nit given a 1.5 would overbet-BLUFF more often than it overbet for
value" is false (theory reviewer, LOW).** It is a COUNT claim, and value bets
swamp bluffs about 10:1 at that node — a nit with an authored 1.5 would overbet
mostly for value. The tilt is real but it is a ~1.4× weight multiplier on a
bluff cell, not a reordering. The DECISION is unaffected and rests on the
simpler ground the reviewer supplied: low-stakes nits, tags, stations and fish
essentially never overbet, so authoring one is a realism loss regardless of the
bluff/value split.

**8. "82.5% falls to 51.8%" is a cross-measurement (refuter, LOW).** The 82.4%
figure is from the 2026-08-05 re-measure at a different commit over 50,000
hands. Within this slice's own measurement the maniac's LARGE+OVERBET moves
79.4 → 51.8.

**9. The threshold sat on a floating-point boundary (refuter, MED).** The old
ceiling of 0.35 was set exactly on two measured pre-ticket values, whose verdict
turned on 3e-17 of accumulation order — through the shipped loader they read
0.35000000000000003 and failed, recomputed in another order they read exactly
0.35 and passed. The docstring also named four nodes as three. All three
ceilings are now set from principle (2× chance for the class gate) and the
measured margins are stated.

**10. One negative case was vacuous (refuter, LOW).** For six identical
normalised distributions the accuracy is 1/n for ANY shape, so
`test_a_flat_roster_reads_at_chance` pinned that weights sum to 1 and nothing
about the statistic's direction. Replaced with a maximally-telling roster that
must score near the top of the range.

**11. The coverage re-record chain entry was missing (refuter and theory
reviewer, independently).** Sixth occurrence of the pattern that file already
logs. Appended, with the cumulative line against the immutable snapshot
(339/1294 = 26.20% against 349/1233 = 28.30%, −2.10pp, inside the adjudicated
`T-cover` mapper dip and a recovery from T3/T4's −2.62pp), and with
`measure_split()` committed so the claim is reproducible.

#### Accepted as findings, recorded and filed rather than fixed here

**12. Estimator parity widened, unremarked (theory reviewer, MED).**
`range_estimate._postflop_action_dist` never passes `is_aggressor`
(`range_estimate.py:386`), so `_sizing_dist` hands it the FLAT block while the
live aggressor uses `sizing_by_node`. Because `bluff_mass` is scaled by
`E_s[_bluff_size_factor(s)]` over that distribution, the estimator's bluff-cell
probabilities differ from the live bot's. Pre-existing since R2 — but T5 moved
the flat and node blocks by different amounts and so changed the gap's SIZE:
mean |live − estimator| P(raise) 5.31% → 7.01%. `range_estimate.py` is not in
T5's owned files. **Filed for the owner: thread `is_aggressor` into `_Ctx` and
add the parity test the invariant requires.** The harm the invariant names is
exactly this — "else the villain-range reveal silently lies".

**13. `bluff_freq` is now an un-refit constant (theory reviewer, MED).** It is
the LEVEL lever and was calibrated against the MEDIUM reference
(`_BLUFF_SHARE_REF`), so re-weighting a pack's size mix re-scales the level and
leaves the fit stale. Measured: maniac AF 3.214 → 3.060 and fold-to-c-bet 0.333
→ 0.285 at n=4000; the maniac/lag AF gap narrowed 0.575 → 0.454. Every persona's
AF/FtC/WTSD still sits inside `BANDS`, so nothing is red — but the persona whose
§5 AF target the engine was ALREADY about a unit below is the one that lost
13.1% of its bluff mass. **Owner decision wanted:** re-fit maniac `bluff_freq`
upward to hold its measured AF, or accept the reduction and record that the next
aggression-spending slice (invest-then-fold, calldown) starts from a smaller
budget than the pre-T5 numbers imply.

**14. The tell statistic is one-sided, and that is a defect in the theory rather
than in the numbers (theory reviewer, MED, CONTRACT-DEFECT).** The ceiling
rewards overlap and the band floor rewards spread, so both gates push the same
way — and the metric's optimum is a six-way-identical uniform-random roster,
which is the least human-like roster it is possible to author. Measured
consequence at the branch tip: the effective number of distinct sizes per node
rose 2.611 → **3.358** (maniac `river_value` 2.971 → **4.561**), and the draw
is i.i.d. per decision, so a seat's flop/turn/river sizes within one hand are
uncorrelated. Real players have size habits; a seat that never repeats a size is
a machine signature of a different kind. This slice self-limits — the ceiling is
2× chance, not chance — but **the limit is a comment, not a gate**, and the next
slice inherits a metric that pays for uniformity. **Recorded so it cannot be
read as "lower is better", and filed: pair the ceiling with a concentration
floor or a within-hand size-correlation check before the next sizing edit.**

**15. lag's opener fold-to-3bet is green on a straddling interval (theory
reviewer, MED).** Already disclosed in the test and above; the reviewer's point
is that an unqualified green still reads as "in band" when the honest reading is
"we cannot tell". **Owner decision wanted:** leave it green, or make it
report-only until the lag `vs_3bet` re-tune lands.

#### Checked and clean

Both the refuter and Codex independently confirmed: `ruff` clean; every authored
postflop fraction on `RECOGNIZED_BET_FRACS`, with the invariant covering both
`sizing` and `sizing_by_node`; no continuous jitter and no `backend/app/domain/`
change at all; all six distributions sum to 1.0; the `bluff_mass *= E[factor]`
mechanism and direction correct as described; the size-tell table reproduces
exactly; the n3bstrata re-power is NOT laundering a regression (all four quoted
numbers reproduce, and T5 is +0.0024 versus pre-T5 at n=36000); and the limper
and buy-in fixtures are consistent with stream and identity displacement. The
theory reviewer separately confirmed the packs are good poker and that all six
archetypes survive on every axis the engine measures — the maniac is still first
on AF, on air c-bet and on overbet rate.

### Second dual review of T5 — the remediation was itself reviewed

The commit that responded to the review above went out unreviewed, and the three
reviewers were run on it separately. All three returned FAIL or NEEDS-WORK. This
section adjudicates that round; every finding was re-verified against the code
before being accepted, and three were narrowed.

**Why a second round was not optional.** The remediation was not a documentation
pass. It changed four pack values, rewrote the whole gate file around three new
statistics, withdrew a gate change the first commit had made, and repaired a bug
introduced during the remediation itself. And the slice's own record was the
argument: every positive test written in it was gameable on first draft, three
times running, each caught by someone else.

#### The finding that mattered most: a whole node was a phantom

**The packs author a `raise` sizing block and no bot can ever use it.** Proof,
not sampling. `postflop_node_key` returns `"raise"` only when a CALL is legal —
that is, only when the seat is facing chips. `_sizing_dist` consults
`sizing_by_node` only when `is_aggressor` is true. And `is_aggressor` means
"this seat made the most recent bet or raise". A seat facing a wager cannot be
the seat that made it, so the two conditions are mutually exclusive. Measured to
agree: across 10,834 postflop facing-a-bet decisions, zero had `is_aggressor`
true; of 4,557 realised raise-node bets, zero were sized from the `raise` block.
Every real raise draws from the FLAT block.

Three consequences, all of them corrections to claims made above:

* The headline "0.756 → 0.612 at the worst node" quoted a node no bot plays. The
  worst reachable node is `cbet_wet`, and dropping the phantom is what let both
  accuracy ceilings move to a single stated principle — 2× chance — instead of
  the two different multiples the previous draft used and described as one.
* One of the two remaining class-certainty cells was at that node, so it was
  notional. Realised it reads 0.41, near chance, because 65% of raise sizes are
  clamped off the grid to the minimum raise.
* 23.9% of all postflop aggression is sized by the flat block through this path,
  and the flat block is the one this slice deliberately declined to change.

**Filed, not fixed** — see the owner items below. Removing the dead blocks and
fixing the `is_aggressor` semantics are different decisions with different blast
radii, and neither belongs in a sizing ticket.

#### Accepted, and the packs changed as a result

**A bet size still named a CLASS with certainty, and no gate scored that.** The
posterior gate the first remediation added was per-persona — the population that
same commit had just declared diluted. Two authored cells read class posterior
1.000 while reading 0.525 per persona and passing: `cbet_wet @ 0.33` and
`raise @ 0.33`, both naming "recreational", because the station and the fish
reach those nodes through their flat block and no regular authored a third-pot
bet there. Measured in play, `cbet_wet @ 0.33` was a real 0.99-confidence tell;
the `raise` one was the phantom above.

Fixed by giving the regulars a third-pot bet on wet flops — the tag at 14% and
lag at 16%, the nit at nothing. Realised class posterior at that cell falls
**0.985 → 0.717**. A fourth gate, the class posterior, now scores what nothing
scored before.

**The first attempt at that fix failed the five-seed gate, and how it failed is
the more useful record.** It spread the same class-level requirement across all
three regulars — tag 10%, nit 8%, lag 12% — and seed 604 came back red on the
DETERMINISM guard, not on separation. The nit's share of near-unanimous decision
contexts went **17.6% → 21.1%** against a 20% ceiling; every other pack sat
between 2.9% and 14.0%. Cause confirmed by swapping only the three changed size
blocks back and re-running the same seed, rather than by inference.

The mechanism is the F2 joint law again, in a place nobody was watching: an 8%
third-pot share cost the nit 2.8% of its wet-flop bluff mass, so it bet less and
checked more, and three contexts that were already near-unanimous tipped over
0.98. **The nit is the one pack on the roster with no room for that.** Measured
across the five seeds at the shipped values its share runs 0.148–0.178, so the
20% ceiling is a live constraint for that persona and slack for everyone else.

The fix is structural rather than a tuned number, and the distinction matters
because the round's own headline finding was a fitted value. The tell is a
property of the CLASS, so what has to move is the regulars' AVERAGE weight at
that cell; how that average is split between the three members is a separate,
per-persona question. Two independent arguments put the nit's share at zero — a
nit taking a cheap stab on a coordinated board is the least characteristic of
the three, and it is the only pack whose determinism headroom cannot pay for it.
The tag and lag carry the whole class share instead. The class average, and
therefore the class posterior, is **identical at 0.800** either way.

**lag's wet-flop overbet was fitted, and withdrawn.** The theory reviewer found
that the two overbet weights the first remediation added and the ceiling that
admitted them were a matched pair: the minimum weights clearing the ceiling were
6.86% and 4.71%, and they were authored at 8% and 6%. The poker was also weak —
a flop overbet is a static-board, nut-advantage tool, and a wet coordinated
board is where correct sizing shrinks. Worse, the slice had refused a flat-block
overbet for lag *on realism grounds* in the same breath, so the principle was
being applied at one node and set aside at another without distinguishing them.
The `cbet_wet` overbet is withdrawn; `turn_barrel` stays, because turn overbets
on scare cards are a genuine lag habit. `cbet_wet @ 1.5` is now a named
exemption rather than a fixed cell, and the residual is disclosed: realised
**P(maniac | a 1.5× bet) = 0.768** with real base rates. The overbet is still a
maniac tell.

**The maniac's third-pot river bet was challenged and KEPT.** The theory review
was right that it is off-archetype and that the tell it closes was phrased about
regulars. It stays because removing it makes a third-pot river bet a *stronger*
recreational tell — the class posterior goes 0.714 → 0.816 — and 7% of one
node's bets is a smaller cost to the maniac's identity than that is to the
ticket's goal. The trade is now recorded in the pack rather than left silent.

#### Accepted as corrections to this ledger and to the shipped packs

**Numbers written about packs that had already changed, for the second time.**
The bottom line, the bucket table, the tell table, the entropy figures and the
coverage verdict all described the first commit after four packs had moved under
them. The coverage line was the worst: this section said "exactly flat" while
the same commit's own test file recorded −0.34pp. Every number above is now
measured at the branch tip, and the pack `_doc` entries point here instead of
carrying copies — three reviewers measured the bucket table three ways and got
three answers, so the counting rule is now stated once, with the table.

**One of those stale numbers was understating a defect filed for the owner.**
The size-entropy figure inside the one-sided-metric contract defect was recorded
as maniac `river_value` 2.97 → 3.88 and a roster mean of 2.6 → 3.3. Measured, it
is 2.971 → **4.561** and 2.611 → **3.358**. The drift toward uniform sizing that
the defect warns about is worse than the warning said.

**The gate could be evaded by spelling.** All three statistics looked sizes up
from a literal string grid, while the pack invariant compares `float(key)` — so
`"0.50"`, `"1.00"` and `"0.330"` are legal authored keys that every statistic
silently dropped. A maximally telling roster spelled `"0.50"` scored 0.0 and
passed every ceiling. The version this replaced took the union of authored keys
and could not miss it, so the rewrite had traded an un-evadable gate for an
evadable one. Sizes are now canonicalised on read. Fixing this exposed a second
bug of the same shape in the fix itself: `%g` renders `1.0` as `"1"`, which
silently stopped matching the band table.

**Both negative controls were wrong, one of them vacuously.** The case arguing
for the posterior gate claimed its fixture "stays invisible to both accuracy
gates" — measured, both gates fire on it (class 0.733, persona 0.400) — and its
only assertion about them was `_class_tell(...) > 0.0`, which cannot fail
because the statistic's floor is 1/3. That is the same mathematical vacuity the
previous round said this draft had removed: fourth draft, same failure mode. The
other case blamed the pre-ticket river failure on a certainty cell; delete that
cell and the score does not move (0.711 either way), because the whole shape was
disjoint. Both are rebuilt to fail for the reason they name, and the new
fixtures are constructed so that the gate under test is the *only* one that
fires.

**Contradictions left next to the code they contradict.** The sample-size block
still argued that the ordering "is stable" and that its margin "GROWS with N —
the signature of an effect emerging from noise", sixty lines above the block
that demolishes exactly that argument. The ordering test's own docstring still
said the four-tier order was "Asserted". Both corrected.

#### Narrowed rather than accepted

**"No committed gate can see this commit" — true, and inherited.** `_persona_stats`
runs `context_aware=False`, so `_sizing_dist` never reaches a node override and
the frozen sampler only ever reads the flat block. Every `sizing_by_node` edit
in this slice is therefore invisible to the AF, fold-to-c-bet and WTSD bands, and
a green suite is not evidence about them. Accepted as a **disclosure** defect and
recorded here; rejected as a defect in the change, because it is engine plumbing
that predates the branch. Live-path AF is what actually moved, and it is in the
theory review's report.

**"Two rosters ship under one pack version" — wrong on its own terms.** `_doc` is
not a model field, so it never enters `config_hash` and cannot change what a
version denotes. The defect was that the documentation was false, not that the
version was. It was false: lag's entry said its overbet thinned "1.8 → 1.3" two
lines above announcing that the overbet had been extended to two more nodes.

**"Six seeds fix the sign" — the reviewers were right and the fix went further.**
Re-measured at the tip, both components rose while the overall ratio fell, which
is the counterexample to the discriminator the previous draft used. The section
now says coverage did not measurably change, which is what the evidence supports.

#### Filed for the owner — three new items

1. **The dead `raise` sizing block.** Four packs author one and no bot reads it.
   Two ways to resolve it and they are not equivalent: delete the blocks, or
   change `_sizing_dist` so a facing-a-bet seat can read a raise-sizing policy.
   The second is the better poker — raise sizing is a distinct skill and the
   packs clearly meant to express one — but it is a behaviour change touching
   23.9% of postflop aggression and needs its own validation. Until then, 23.9%
   of aggression is sized by a block written for leading out.
2. **The overbet is still a maniac tell.** Realised P(maniac | 1.5×) = 0.768,
   down from 0.885 but not close to gone, and now carried as two named
   exemptions rather than as a fix. Closing it needs a decision about whether
   another archetype should overbet at all, which is a realism question rather
   than a statistics one.
3. **The ecology gate reads authored distributions and weights nodes equally.**
   Realised node occupancy is nothing like equal — flat 33.0%, raise 23.9%,
   turn_barrel 15.4%, cbet_dry 11.6%, river_value 9.9%, cbet_wet 5.2%,
   cbet_mono 1.0% —
   so the gate spends as much of its budget on a 1% node as on a 33% one. It is
   the right shape for a regression guard and the wrong shape for a measurement,
   which is why the measurement now lives in this ledger. Occupancy weighting is
   worth considering before the next sizing edit.

These join the three already filed above (estimator parity widened, `bluff_freq`
un-refit, the tell statistic one-sided).

## T2b build record — preflop size values

**Bottom line: every persona opened one size, share 1.000, from all eight
opening seats; all six now mix, and the three regulars mix differently by seat.
The load-bearing precondition in the ticket turned out to be a phantom — the
2.8 three-bet rung it wanted to bank creates no hero coverage, because the app
never offers hero the open size that would need rescuing — so the effort went
into the open instead. The five-seed gate passes with room. Hero coverage shows
no change the six-seed measurement can distinguish from zero, but one component
of it moved consistently and against us, and that is filed rather than papered
over.**

⚠️ **Every number here is measured at the branch tip**, over 4,000 hands at seed
601 through the committed `backend/tools/preflop_size_report.py`, unless it says
otherwise. The pack `_doc` entries state only their own values and point here.

### The ticket's own precondition is wrong, and the rung was dropped

Ticket item 3 banks what it calls a mirror-image win: at the vs-3-bet spot the
cap is 3.5 × the CANONICAL open for hero's seat, so a hero who opens 3.0bb from
a 2.5-canonical seat faces a cap of 8.75 that every shipped multiplier exceeds,
and a 2.8 rung would create coverage that does not exist today. The arithmetic
is right. The conclusion does not follow, because the app never offers hero a
3.0bb open from those seats.

Hero's preflop raise sizes are server-offered, not free-form:
`sim_session._hero_preflop_size_bb` reads the content entry's `sizing_bb`, and
`_preflop_two_sizes` synthesises a second option at +1.0bb for an open. The RFI
entries carry exactly the canonical size — 3.0 at UTG/UTG+1/UTG+2/LJ/SB, 2.5 at
HJ/CO/BTN — so hero's two options at any seat are `canonical` and
`canonical + 1`. Over every seat that has vs-3-bet content:

| hero seat | canonical | hero opens | open band [2.0, 3.0] | 3-bet cap | gradeable multipliers |
|---|---|---|---|---|---|
| UTG, UTG+1, UTG+2, LJ | 3.0 | 3.0 | pass | 10.5 | all six (3.0–3.5) |
| UTG, UTG+1, UTG+2, LJ | 3.0 | 4.0 | FAIL | 10.5 | none, at any multiplier |
| HJ, CO, BTN | 2.5 | 2.5 | pass | 8.75 | all six |
| HJ, CO, BTN | 2.5 | 3.5 | FAIL | 8.75 | none, at any multiplier |

No cell a 2.8 rung rescues exists. Whenever hero's open passes the band it IS
the canonical, and then every multiplier at or under 3.5 is inside the cap;
whenever it fails the band the hand is refused before the multiplier is read.
So the only live constraint on a 3-bet multiplier is "at or under 3.5", which
`test_every_3bet_mix_stays_at_or_under_the_grading_cap` now pins.

This is the third time in this slice that a value was authored, or nearly
authored, against a node no one can reach. The pattern is worth naming: the
grader's constants are readable and the paths that consume them are not, so
arithmetic against a constant looks like evidence and is not.

### What was built

The ticket is not a pack-data ticket, as its own text warns. `preflop_raise_to`
had no `position` parameter, so a seat-conditional open needed engine work
first:

- `PersonaSizing.open_bb_mix_by_position` — one mix per opening seat. The
  validator requires ALL eight and refuses a BB entry. Completeness is required
  rather than defaulted because a missing seat would fall back to the scalar and
  go on playing one fixed size from that chair, which is the exact defect the
  field exists to remove and which nothing else would report. Authoring both
  open forms is refused too: either precedence order silently discards half of
  what the author wrote.
- `preflop_raise_to(..., position=...)`, resolving the open mix through
  `_open_mix`. Only the open and the iso built on it are seat-keyed; the 3-bet
  and 4-bet multiples of the raise faced stay seat-blind.
- `play._preflop_decision` threads the seat it already had.
- `content/schema/persona.schema.json` regenerated.

### The values, and the constraint that bounded them

Two grading bounds decided the shape more than taste did.

**Opens stay at or under 3.0 for the three regulars.** `_map_vs_3bet` and
`_map_vs_4bet` both require the opener's own open to be inside
`_STD_OPEN_CAP` = 3.0, so a bigger rung would buy size variety by deleting
hero's feedback on the whole hand. The three recreationals already open above
it as their shipped identity (3.5 / 4.0 / 4.5) and are grandfathered;
`test_a_regulars_open_never_exceeds_the_hero_3bet_lines_cap` holds the line for
the other three.

**3-bet rungs stay at or under 3.5**, per the table above.

Regulars get a seat table, recreationals a flat mix. That split is the theory
review's, and the measurement backs it: opens come overwhelmingly from EARLY
seats, because a pot is unopened far more often when an early seat acts. Per-seat
open counts over 4,000 hands, before the change:

| persona | UTG | UTG+1 | UTG+2 | LJ | HJ | CO | BTN | SB | share at 3.0-canonical seats |
|---|---|---|---|---|---|---|---|---|---|
| lag | 229 | 147 | 112 | 91 | 75 | 46 | 29 | 12 | 79.8% |
| maniac | 300 | 242 | 180 | 101 | 79 | 54 | 37 | 7 | 83.0% |
| tag | 70 | 75 | 53 | 35 | 34 | 14 | 5 | 4 | 81.7% |
| nit | 31 | 24 | 22 | 16 | 5 | 6 | 4 | 1 | 86.2% |
| passive_fish | 15 | 9 | 6 | 9 | 1 | 3 | 1 | 0 | 88.6% |
| calling_station | 2 | 3 | 2 | 0 | 1 | 2 | 0 | 0 | 70.0% |

A persona-global mix emitting 2.5bb at 20–35% would therefore have put most of
that mass under the gun, which no competent full-ring regular does. The seat
table reaches the same aggregate by conditioning on the thing a human conditions
on.

### Measured effect, 4,000 hands, seed 601

| persona | opens | open mean before → after | modal share before → after | rungs |
|---|---|---|---|---|
| calling_station | 10 → 25 | 3.500 → 3.480 | 1.000 → 0.480 | 1 → 3 |
| lag | 741 → 724 | 3.000 → 2.832 | 1.000 → 0.678 | 1 → 3 |
| maniac | 1000 → 1042 | 4.500 → 4.348 | 1.000 → 0.697 | 1 → 2 |
| nit | 109 → 115 | 3.000 → 2.917 | 1.000 → 0.713 | 1 → 3 |
| passive_fish | 44 → 40 | 4.000 → 3.925 | 1.000 → 0.425 | 1 → 4 |
| tag | 290 → 267 | 3.000 → 2.873 | 1.000 → 0.745 | 1 → 2 |

The 3-bet MULTIPLIER was a constant for every persona and is not any more:

| persona | n after | mean before → after | modal share before → after | rungs |
|---|---|---|---|---|
| calling_station | 7 | 3.000 → 2.943 | 1.000 → 0.714 | 1 → 2 |
| lag | 248 | 3.500 → 3.305 | 1.000 → 0.444 | 1 → 3 |
| maniac | 708 | 3.300 → 3.377 | 1.000 → 0.617 | 1 → 2 |
| nit | 32 | 3.500 → 3.453 | 1.000 → 0.844 | 1 → 2 |
| passive_fish | 18 | 3.000 → 3.083 | 1.000 → 0.833 | 1 → 2 |
| tag | 108 | 3.500 → 3.352 | 1.000 → 0.704 | 1 → 2 |

The absolute 3-bet SIZE already varied before this change, because the open it
answered did. A detector reading the ratio saw a constant, which is why the
multiplier is the number in the table.

**How to read a per-seat histogram.** There are 48 cells and most carry few
opens, so near-1.000 readings appear from sampling alone. In the after run
tag@UTG+2 reads 0.982 at n=57 against an authored 0.90 — roughly a one-in-eighty
excursion, and about one such cell is expected across 48. The claim that no cell
plays as one number is made instead by
`test_every_persona_mixes_its_open_at_every_seat`, which draws 600 times per
cell against a 0.95 ceiling.

### The two gates

**Five-seed gate PASS**, seeds 601–605: minimum pairwise separation 1.694,
1.864, 1.807, 1.756, 1.778 against the required 1.254429; labels 6/6 at every
seed; determinism clear at every seat.

Per-persona determinism shares at seed 604, the seed that went red during T5:
nit 16/91 = 0.176, station 15/114 = 0.132, lag 0.040, maniac 0.035, tag 0.033,
fish 0.022, against a 0.20 ceiling. The nit's number sits exactly where the T5
record left it (0.148–0.178), which is expected — rule 4 groups on action type
and cannot see a bet size — and it remains the constraint any later edit that
changes how often the nit ACTS is measured against first.

### Hero coverage — no detectable change, and one thing that is not noise

Six seeds, 2,000 hands each, through the committed `measure_split`:

    preflop   0.571013 → 0.573595   (+0.26pp)
    postflop  0.032944 → 0.031588   (−0.14pp)
    overall   0.251215 → 0.247432   (−0.38pp)

The overall move is not distinguishable from zero: the six per-seed deltas are
−0.375, +0.846, −0.244, −0.215, −1.147 and −1.101 pp, mean −0.373pp with a
standard error of 0.298pp, about 1.25 standard errors from no change. That is
the sixth reading in this slice to land there.

**The postflop denominator rose at every one of the six seeds** — 3717, 3572,
3645, 3718, 3576, 3415 becoming 3767, 3654, 3749, 3731, 3803, 3615, about +3.1%
— while the postflop graded count stayed flat, 713 → 705. Hero faces more
postflop decisions. The mechanism is direct: the regulars now open 2.5bb from
the hijack round instead of 3.0bb, a cheaper open is called by more seats, and
more seats seeing a flop means more multiway pots, which this repo's mappers
largely do not cover.

That is a genuine tension with spec §7.1, which reads the ratio and forbids
reducing it. The ratio cannot tell "grading broke" apart from "more poker
happened", and this ticket produced the second: over the same six seeds the
graded COUNT rose, 9148 → 9177. Filed below rather than resolved — and
deliberately not mitigated, because shrinking the change until the ratio held
would be fitting values to a gate, the defect both T5 review rounds caught.

### There is no F2 analogue preflop, but there is an SPR one

T5's lesson was that a pack's own size mix scales its bluff rate, so a sizing
edit is also an aggression edit. Preflop has no equivalent inside the decision
logic: `play._preflop_facing` keys on the raise COUNT and never the size, so
nothing reads an open size to set a frequency. Verified by reading every
consumer of the three sizing scalars.

What preflop sizing does change is the POT, and through it the stack-to-pot
ratio that `personas_postflop` uses for the commitment ramp
(`stack_bb / pot_bb <= pf.spr_commit`, lines ~1110 and ~1123). Smaller opens
mean smaller pots, higher SPR and less commitment; more callers per pot mean
more multiway flops. Both reshape which hands reach which street. That is why
all six rows of `_GOLDEN_STATS_N200` moved, in both directions, with no
per-persona sign to explain — ordinary stream displacement, but with a named
mechanism rather than a shrug. Aggression staying in range is asserted by
`test_persona_postflop_bands` at population n, which passes unchanged, not by
those n=200 numbers.

### Deliberately not done, with the volumes that decided it

**No 4-bet mix on any pack.** Four-bets per 4,000 hands: maniac 184, lag 57,
tag 27, fish 2, nit 0, station 0. The maniac's multiplier is 3.0 against a 2.4
grading cap, so its four-bets are already ungradeable for hero and any rung
would be a reduction — a change to the persona rather than to its sizing, and
excluded by T2's original text. The tag's and the lag's sit exactly ON the 2.4
cap, so a mix could only lower the mean, changing how those packs deny odds in
exchange for variety at a node almost nobody reaches. Recorded in
`test_no_pack_authors_a_4bet_mix` so a later slice that wants it has to say what
changed.

**The size-blind preflop defence gap is still open** (ticket item 4). Response
keys on the raise count, never the size, so fold-to-open is flat across open
sizes by construction — a tell created by this fix. Engine work is out of scope
by the ruling. The mitigation is the narrow spread the regulars ship, which is a
second reason for the low-entropy design; escalate only if a measurement shows
it is detectable.

**The maniac's open mean falls 4.5 → 4.35, authored not accidental.** At a lever
already on the grading cap, one-sided variance and a preserved mean are
arithmetically incompatible, so a real maniac's upward variance — 5×, 6×, jam —
cannot be expressed at all. This persona gets the least realism per unit of risk
of the six.

**The station's and fish's mixes are nearly unobservable.** 10 and 44 opens per
4,000 hands. They are authored for completeness and the pack `_doc` entries say
so, rather than letting the width read as a measured effect. Their new 3.0 rungs
do buy a sliver of hero coverage that does not exist today — a 3.0 open is inside
`_STD_OPEN_CAP` where a 3.5 or 4.0 is not — but at that volume it is a fraction
of a hand per thousand.

#### Filed for the owner — one new item

7. **Spec §7.1's coverage criterion cannot distinguish a grading regression from
   more poker being played.** It reads the graded/total ratio and forbids
   reducing it. This ticket left the graded count higher (9148 → 9177 over six
   seeds) and the ratio lower (−0.38pp, inside noise), because it moved
   decisions toward the postflop streets, which grade at about 3% against
   preflop's 57%. Any future change that makes pots more multiway will look like
   a coverage regression by this measure. Choosing a better one — graded count
   per hand, or the two street ratios separately with no pooled figure — is a
   spec decision.

This joins the six already filed above (the dead `raise` sizing block, the
overbet residual, the ecology gate's equal node weighting, estimator parity
widened, `bluff_freq` un-refit, the tell statistic one-sided).
