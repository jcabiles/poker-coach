# Ledger — R9-DEFENCE-a

Base `origin/main` `8cc6c38`. Spec `docs/ai-dlc/specs/r9-defence-a.md`. Contract map
`docs/ai-dlc/contracts/r9-defence-a.md`.

---

## S-0 · Contract-scan stage (2026-08-02)

**S-0.1 — the `contract-mapper` scan read a stale tree. REJECTED headline, findings kept.**
It reported "N-LOGIT is not present in this checkout" and returned line numbers that matched nothing at
base. Cause: it read the **shared working tree**, whose local `main` sat at `61efc42`, six commits behind
`origin/main`. Verified by me: `git grep continue_ref origin/main -- backend/app/domain/content/models.py`
→ 7 hits; the working tree → 0.
**Standing fix for this lane: pin every review/scan sub-agent to base explicitly** (`git show origin/main:`
or its own detached worktree) and say so in the brief. Both spec reviewers were briefed that way and both
independently re-verified base; neither repeated the error.

---

## SPEC FAN-IN REVIEW (2026-08-02) — rev 1 → rev 2

Two independent reviewers, both GIT-READ-ONLY, run concurrently on spec rev 1 + the contract map:
`refuter` (Opus) and Codex Sol (`gpt-5.6-sol`, effort high).

**Both returned FAIL.** Neither found a defect in the *mechanism*. Both broke the *gates* — independently,
by different routes, and both routes work. Rev 1's acceptance harness would have admitted a no-op.

Every finding below was reproduced against base before adjudication. Findings are numbered `R-n`; the
originating reviewer is named.

### Accepted

**R-1 (both; refuter HIGH-1, Codex 6) — `_LINE_DELTA` was never given a value, and no criterion pinned a
minimum effect size. ACCEPTED.**
`λ_p = _LINE_DELTA · line_sensitivity` with `_LINE_DELTA` unspecified, and criterion 1 asking only for
"strictly greater". The refuter set `_LINE_DELTA = 1e-12` and **measured** the resulting no-op passing
criteria 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12 — eleven of twelve. This is N-LOGIT rev 1 reproduced inside a
spec written by someone who had just adjudicated N-LOGIT rev 1.
Its two mentions were also 4× inconsistent: §3.1 said "mirrors `_POSITION_AGG_DELTA`" (`= 0.25`), while §5's
"`le=2.0` ⇒ odds cut ≥ 7×" is only true at `_LINE_DELTA = 1.0`.
**Resolution:** pin `_LINE_DELTA = 1.0`. Independently corroborated — at `1.0` the refuter measured nit
MIDDLE_PAIR `ΔP(fold) = +0.131`, which reproduces the design pass's own §6 predicted table (`+0.1312`) to
three decimals; at `0.25` it gives `+0.030`, which does not. Add a **minimum effect size at a named
reference node, written as a literal in the spec** and never derived from the module constant.

**R-2 (both; refuter MED-3, Codex 2) — the claim that a `fold_merit`-only implementation cannot pass the
raise-neutrality gate is FALSE. ACCEPTED; the spec's §3.2 was wrong.**
`normalize(F, C·s, R·t·s) = normalize(F/s, C, R·t)` — the fold-side form is *projectively identical*.
Both reviewers measured it independently to bit equality (refuter: max |Δ| `1.11e-16` on two real frozen
base vectors; Codex: bit-equal on a synthetic probe). The design pass had already conceded this in passing
(`r9-defence-design.md:318-320`) and rev 1 contradicted it.
Note the *other* half of the claim survives: a **`call_merit`-only** multiplier is exactly the N-LOGIT
misroute and genuinely does move the raise share. Only the fold-side clause was false.
**Resolution:** delete the false clause; state the equivalence explicitly. Since no *output* test can
distinguish the two forms, the C/R-only prescription is enforced **structurally, on the raw merits before
normalization**, not behaviourally. Keep C/R-only as the prescribed form for auditability against the A1
no-fold-floor guardrail — the fold merit stays an untouched input.

**R-3 (Codex 3, sharpened by me) — criteria 3 and 4 are undefined on legal in-scope cells, and criterion 2
constrains only the anchor, so a continuation-COLLAPSE mutant still passes. ACCEPTED.**
On the river, `bluff_cell` hard-zeroes `call_merit` (`personas_postflop.py:884-885`, verified by me) and
RAISE is appended only when legal (`:887`). So `C + R = 0` is reachable on an in-scope cell: criterion 3
computes `0/0`, criterion 4 computes `logit(0)`.
Worse, rev 1's criterion 2 — added specifically to close N-LOGIT's G1 collapse hole — pinned
non-degeneracy of the **anchor** only. Codex measured a mutant setting `C' = R' = 0` from a non-degenerate
anchor (continue mass `0.588`): fold rose to `1.0`, so it passed criteria 1 **and** 2. **The anti-collapse
gate did not stop the collapse.** This is the N-LOGIT G1 defect reproduced one level down.
**Resolution:** criteria 3/4 apply only to cells with strictly positive continue mass at **both** the anchor
and the tuned point; zero-continue cells are pinned separately as inert; a cell may never be *skipped*
silently — skip counts are reported and floored per persona.

**R-4 (Codex 4) — the paired sensitivity run cannot share a deal sequence. ACCEPTED; §6.1's design was
unbuildable as written.**
`_persona_stats` constructs a single `random.Random(20260710)` and uses it **both** to draw each hand's
seed **and** as the action/sizing RNG inside `_play_hand` (`tests/test_personas_postflop.py:2524-2538`,
verified by me). The instant line-aware play changes any draw count, the next `hand_seed` diverges and the
two arms are no longer playing the same hands — so the paired comparison measures deal noise, not the
mechanism. Since §6.1 made this run the *only* gate standing between the spec and R-1's no-op, this is
decisive.
**Resolution:** pre-generate immutable hand seeds from a **dedicated deal RNG**, hold every non-line input
identical across arms, and state numeric tolerances and occurrence floors. Also demoted: the paired run is
a **population consequence check**, not the decisive mechanism gate — R-1's reference-node effect-size
floor is.

**R-5 (Codex 1) — RED-FIRST was demanded of criteria that are green at base by construction. ACCEPTED.**
Rev 1's §7 preamble required *every* HARD criterion to be demonstrated failing at base. But criteria 5, 7,
9 and 10 are **regression pins** — flop byte-identity, the frozen price vectors, no-band-exit, inertness —
all of which pass at base and must *keep* passing. Demanding they fail is incoherent, and worse, it invites
a builder to weaken a pin until it does.
**Resolution:** split §7 into two explicitly labelled classes — **SENSITIVITY gates** (must be RED at base;
they are the proof the change does something) and **REGRESSION PINS** (must be GREEN at base and stay
green). RED-FIRST binds only the first class.

**R-6 (refuter HIGH-2, extended by me) — the scope predicate was undefined over the `(bucket, draw)`
product, and one resolution makes two other sections of the spec vacuous. ACCEPTED, with a finding the
reviewer did not reach.**
`StrengthBucket` and `DrawCategory` are **independent axes** (`personas_postflop.py:33-51`); rev 1's §4
listed both in one "excluded" column and never said what happens to `MIDDLE_PAIR` **with** a flush draw.
Extending it myself: with the predicate resolved as `draw is DrawCategory.NONE`, then for every in-scope
bucket `made = _RUNG[bucket] >= _RUNG[OVERPAIR_TPTK]` is **False** (in-scope rungs are 0–3, the threshold
is 4) and `drawing` is **False** — so `value_commit` is **always False** and the `elif facing and drawing`
B5b branch never runs (`:983-1007`, verified by me).
**Consequences rev 1 got wrong:** §3.3's "attach after the commit block because B5b subtracts absolute
quantities" is **moot** — B5b cannot co-occur with an in-scope cell. And §3.4's "declared no-reach zone on
SPR-committed nodes", plus criterion 10 which pinned it, describe a combination that **cannot occur**: the
mechanism is scoped *away* from those nodes, not inert on them. A gate on an impossible combination always
passes.
**Resolution:** state the predicate explicitly as `bucket ∈ {MIDDLE_PAIR, TOP_PAIR, ACE_HIGH, AIR} and
draw is DrawCategory.NONE`; justify the attach point solely as "inside the facing branch, before the single
normalization"; replace the no-reach section with a scope statement; and rewrite criterion 10 as **every
out-of-scope `(bucket, draw)` cell is byte-identical** — which is a real gate, and which R-6 shows rev 1
had no equivalent of.

**R-7 (refuter MED-7, verified by me) — the attach point as specified lands in the COMMON path, and the
facing-chips restriction existed only in prose. ACCEPTED.**
Rev 1 anchored positionally ("after `:1007`, before `:1059`"). Verified by reading indentation at base: that
region sits at function-body indentation, **outside** any facing branch — which is exactly why N-LOGIT
re-guards with its own `if ActionType.FOLD in by_kind:` at `:1066`. An implementation following rev 1
literally would also scale the RAISE entry on matched-with-option (`CHECK+RAISE`) shapes. No criterion
asserted non-facing nodes were unchanged.
**Resolution:** restore the explicit `ActionType.FOLD in by_kind` gate to the mechanism statement, and add a
regression pin that unopened (`CHECK+BET`) and matched-with-option (`CHECK+RAISE`) nodes are byte-identical.

**R-8 (refuter MED-4) — two criteria demanded bit-identity that IEEE arithmetic forbids. ACCEPTED.**
Measured over 200k random draws: `(R·k)·s` vs `(R·s)·k` mismatch **34.9%** of the time; the committed-node
comparison mismatches **42.0%**. A *correct* implementation would fail rev 1's criteria 3b and 10 roughly a
third of the time. The precedent is in base source: N-LOGIT rev 2's 1-ulp residue broke 6 of the 23 frozen
vectors (`personas_postflop.py:1033-1036`).
**Resolution:** explicit relative tolerance (`1e-12`) on any criterion comparing two computed orderings.
Criterion 5's "byte-identical" stands unchanged and is safe — `line = 0 ⇒ line_mult == 1.0` exactly, and
`m * 1.0 == m` bitwise.

**R-9 (Codex 5 + refuter MED-5, reconciled) — the estimator parity gate was an identity gate, and a naive
implementation passes heads-up while being wrong multiway. ACCEPTED.**
Rev 1 required "a parity test proving the reveal matches the live policy" but never required the fixture to
**contain a line = 1 node** — so an estimator that keeps passing `False` matches everywhere and the gate is
green. Codex adds the sharper case: a mutant reading "*any* aggression on the previous street" passes a
heads-up barrel test and is wrong multiway, where a *different* seat bet the previous street.
**Resolution:** the parity gate must require (a) a fixture node with `aggressor_barrel_run(...) >= 1`,
(b) the estimator's distribution at that node **differs** from the line-blind one, and (c) explicit
discriminators: same-seat true · different-seat false in multiway · broken consecutive line · flop false.

**R-10 (Codex 6, second half) — criterion 4 demanded STRICT monotonicity over a ladder containing an
authored tie. ACCEPTED.** §5 authors `lag = passive_fish = 0.35`. Strict monotonicity over that ladder is
unsatisfiable.
**Resolution:** declare `{lag, passive_fish}` an explicit tie tier; require strict ordering *between* tiers
and equality *within*. Also add a **lever sweep** over several `line_sensitivity` values (including
`model_copy`-injected ones) so a hard-coded per-persona response table cannot pass.

**R-11 (Codex 7) — "the flop is structurally unchanged" holds for production-derived callers only.
ACCEPTED, narrowed.** `aggressor_barrel_run` returns 0 on the flop structurally, but
`sample_postflop_decision` takes a flat unconstrained boolean, so a direct caller can pass `True` with
`street=FLOP`.
**Resolution:** narrow criterion 5 to the production-derived path and pin the derivation's flop-zero
property directly (an R9-SIGNAL test already covers it). **Rejected sub-recommendation:** neutralising
`True` on FLOP *inside the sampler* — that would put a street term in the mechanic, which is precisely what
keeps this slice outside the roadmap's `street → scalar` prohibition. The flat kwarg stays honest; the
guarantee lives with the derivation.

**R-12 (Codex 8) — criterion 3b could be satisfied by test-local algebra rather than the coded path.
ACCEPTED.** A test that recomputes both orderings itself passes regardless of where production actually
attaches.
**Resolution:** 3b must exercise the production transform, or a counterfactual reordered copy of it.

**R-13 (refuter LOW-8, my error) — wrong line anchor. ACCEPTED.** The sizing draw is at
`personas_postflop.py:1088`, not `:1082` (`:1082` is inside a comment). Verified: `grep -n rng.choices` at
base returns exactly `:1076` and `:1088`. Both the spec and the contract map carried the wrong number — in
a document whose own opening warns about stale anchors. Corrected in both.

**R-14 (refuter LOW-9) — misquoted precedent. ACCEPTED.** `position_sensitivity` is bounded `le=1.0`
(`content/models.py:230`), not `2.0`. Rev 1 cited it as precedent in a way that implied the bound value
carried over. It is precedent for **bounding explicitly**, not for the number. Corrected.

### Rejected / narrowed

**R-15 (Codex 7 sub-recommendation) — REJECTED**, see R-11: adding a street check inside the sampler would
introduce the very `street → scalar` term the design pass spent a section proving this mechanism avoids.

**R-16 (reviewer disagreement on estimator size) — RESOLVED IN THE REFUTER'S FAVOUR, narrowly.**
The refuter called §6.2's "new logic, not plumbing" **overstated**: `aggressor_barrel_run` reads only
`h.street`, `h.position`, `h.action`, and the replay already reads all three. Codex called §6.2
**correct** ("new replay logic"). Verified by me: `PublicAction` (`range_estimate.py:66-76`) carries
`street`, `position`, `action` — structurally compatible with `HistoryAction` (`spot.py:113`) for exactly
the fields the derivation touches. So the derivation is **reusable as-is**; what is genuinely missing is one
tracked value — the current street's aggressor seat — which `_Ctx` does not store.
**Both reviewers are partly right and the resolution is the same either way:** budget it as *reuse the
shipped derivation + track one new value*, and **forbid re-deriving the run rule** (the R9-SIGNAL docstring
explicitly warns against a second taxonomy, `postflop_context.py:185-186`). Codex's multiway discriminator
(R-9) is what proves the tracked value is the *seat* and not merely "someone".

---

## BUILD STAGE

**B-1 — wave 1 (T1, the lever) landed `0c05d10`.** Independently re-verified by the Director, not taken on
the worker's report: `1386 passed, 1 skipped`, exit 0, read from a file. Two comment inaccuracies the worker
introduced were corrected in integration rather than passed downstream — it framed a low seed as "an
intended leak" (the spec says calling_station's 0.10 is the **archetype**), and justified the `le=2.0` bound
as "2× the largest seed", which is both wrong arithmetic and the wrong reason (the real reason is the ≥7×
odds cut at `_LINE_DELTA = 1.0`). This repo treats a stale or wrong comment as a defect.

**B-2 — the worktree/doc trap.** The T1 worker reported that the spec and ticket files "do not exist
anywhere in the worktree". Correct: every `docs/ai-dlc/` artefact in this initiative is **untracked**, so a
fresh worktree cut from `origin/main` contains none of them. It completed anyway on a self-contained brief.
Fixed for all later waves by pointing briefs at main-tree absolute paths for reading. **Standing note: an
untracked-docs repo cannot hand a worker its own spec by worktree path.**

**B-3 — wave 2 (T2, the mechanism) landed `cb00dc6`, measured, not asserted.** At the reference node
(nit / MIDDLE_PAIR / turn / HU / SPR 20 / faced 0.5-pot): `ΔP(fold) = +0.131190` against the design pass's
predicted `+0.1312`; raise-share drift `1.11e-16` (one ulp) across all 2592 in-scope facing cells; realized
log-odds shift `0.6000000000000001` against `λ = 0.60`. A 46,656-cell probe found zero scope violations,
byte-identity on all 1296 out-of-scope facing cells and all 3888 non-facing cells, and an unchanged
first-`rng.choices` position. The worker also re-measured `_LINE_DELTA` at `0.25` (`+0.030138`) and `1e-12`
(`+0.000000`) rather than quoting the ledger — correct discipline, since the code comment asserts them.

**B-4 — the worker hit the STOP condition and stopped. Three tests moved; it re-recorded none.** That is
the behaviour the brief demanded and it was right to block.

**B-5 — OWNER RULING (2026-08-02): the spec's blanket "no fixture re-records" was MY error, and is
corrected.** Rev 2 §8 banned all re-records. That conflated two genuinely different classes:
- **Never move:** `test_price_tail.py`'s 23 frozen exact-equality vectors · the population `BANDS` · the
  golden persona statistics. A move is a defect → escalate.
- **Documented per-slice re-pin protocol:** `test_coverage_baseline.py` and `test_limper_coverage_belt.py`
  record how bots play a fixed deal sequence. Since `play.py` already derives and threads the barrel signal,
  **any** working version of this mechanism displaces the shared seeded rng stream and moves them by
  construction. Both files carry an explicit re-record convention with 11+ precedents.
**Ruling: re-pinning those two is authorized for this slice** under the protocol those files define —
attribution proven by revert, every coverage shape verified still firing, movement reported not laundered.
Filed as ticket **T2b**, added mid-build; spec §8 amended.

**B-6 — OWNER RULING (2026-08-02): the graded-coverage dip is FLAGGED, not blocking.** Graded coverage
moves `27.70% → 26.01%` in the fixed-hand simulation. Cause is not lost grading capability: more realistic
villains steer hero into a different mix of spots and the **unchanged** mapper grades that mix slightly
less. Attributed to the mapper track (`T-cover` owns this number), consistent with the last several slices.
**Correction to the T2 worker's report:** it called this "the largest dip in the file's history". Verified
false — `R10-PRE2` moved it `28.0% → 26.3%`, the same magnitude. The claim was reported to the owner with
that correction attached rather than passed on as stated.

**B-7 — wave 3 dispatched with three concurrent workers** (T2b Sonnet · T3 Opus · T4 Opus — two concurrent
Opus at high effort, the limit, so ungated per GATE.md). Each worker verifies **only its own test module**,
with `-p no:cacheprovider`; the Director runs the full suite at the barrier. Running the full suite inside a
worker would race the other two, which share the worktree.

**B-8 — RED-REF.** Red-first evidence is measured against a second detached worktree at `0c05d10`
(**dial authored, engine untouched**), not against bare base. At bare base the gates would raise
`AttributeError` — evidence of a missing attribute, not evidence of a missing mechanism. At RED-REF they
fail on their assertions and produce the table that means something: `ΔP(fold) = 0.000000` per persona
against a gate demanding `≥ 0.05`. Verified before dispatch: the dial is present and `_LINE_DELTA` is
absent in that worktree.

**B-9 — T2b landed the re-pin under the protocol, and surfaced a FIFTH lost-record.** Attribution was
**proven, not assumed**: restoring only this slice's three changed files to their base contents made both
tests pass again, and putting them back reproduced the failure. All nine `_WANT_*` coverage shapes still
fire (BB¹ 40 · BB² 25 · BB³ 10 among them), which is what separates stream displacement from a real
coverage regression.

The worker flagged that the docstring chain's final entry (1275/338) does not match the fixture on disk at
base (1224/339), and correctly treated the fixture as ground truth rather than trying to reconcile it.
**Director follow-up, traced not guessed:** `git log` on the fixture shows `6e73bbf` (wave-6 lane A, #155 —
pack-keyed stats caches + production-faithful harness sizing) moved it `1275/338 → 1224/339` and appended
**no docstring entry**. That is the **fifth** occurrence of the lost-record pattern in this initiative (four
are already logged in `test_limper_coverage_belt.py`). A bridging note was added to the docstring recording
the discontinuity, its cause, and the rule that follows from it: **compute the "old" side of a re-pin from
the FIXTURE, never from the tail of the prose chain** — deriving it from prose is exactly how one of these
gets lost. No fixture value was changed by that note.

**B-10 — T3 (estimator) landed `0fb3ea7`, with the multiway trap measured rather than assumed.** The
implementation tracks exactly one new value (the current street's aggressor **position**) and asks the
shipped `aggressor_barrel_run` about that seat — the run rule is not re-derived, per the derivation's own
"one taxonomy" warning. The discriminating evidence is a fixture PAIR differing only in *who* bets the turn:

| fixture | derived flag | naive "any aggression last street" |
|---|---|---|
| multiway, DIFFERENT seat bet the flop | **False** ✓ | **True** ✗ |
| same fixture, SAME seat bets the turn | True ✓ | True ✓ |

This confirms Codex's R-9 prediction concretely: the naive reading passes heads-up and is wrong multiway.
Reveal proven to move at a barrel node (tag, `line_sensitivity` 0.50): `P(fold)` 0.220920 line-blind →
0.318578 line-aware, matching the live line-aware policy exactly.

**B-11 — T3 surfaced a SECOND contradictory test nobody had scoped.**
`test_estimator_river_dist_equals_live_polarized_policy` was green at base and fails once the estimator is
line-aware: its fixture is three barrels by one seat, so its river node has `run == 2`, but its live
reference call defaulted the flag to `False`. Its *intent* is unchanged and still correct; only its
reference had stopped being production-faithful. The worker left it untouched (not its file) and reported
both resolutions; T6's ticket was amended mid-build so neither could be lost.

**B-12 — T4 (the node grid) landed `e518118`: 19 gates, 1121 insertions, 0 deletions.** RED at the red
reference with the table that matters (`ΔP(fold) = +0.000000` for all six packs, `0 of 288` cells rising,
against a gate demanding a **literal** `≥ 0.05`); on the branch, `+0.131190 / +0.097658 / +0.064975 /
+0.081425 / +0.031156 / +0.005434`, logit shift exactly λ, `288 of 288` cells rising. All six
counterfactual mutants caught **where the spec says they must be** — notably the fold-side form by **P-1
alone** and the scope-blind form by **P-2 alone**.

**Director check on P-1's fragility.** P-1 observes the raw pre-normalization merits by shadowing the
module-global `sum` for the duration of one sampler call. That is the only way to see them without
refactoring the engine for testability, but it fails silently if the engine stops calling `sum(weights)`
there — and a silent capture failure would make P-1 pass on an empty set, which is this initiative's
signature failure mode. **Verified not vacuous:** P-1 carries occupancy floors (`≥ 300` observations per
persona, `≥ 1800` total), so a dead capture fails loudly. Flagged for the fan-in reviewers anyway.

**B-13 — SPEC CORRECTION (T4, accepted): "every S-gate must be RED at base" was unsatisfiable and would
have corrupted two gates.** S-2 (anti-collapse) and S-3 (raise-neutrality) compare the anchor against the
*tuned* point; with the engine untouched those are the same vector, so both are trivially TRUE at the red
reference. Forcing them red would mean rewriting them into something else. **Amended rule: an S-gate must
be falsifiable by EITHER a red reading at the red reference OR a named mutant it demonstrably kills.**
Falsifiability was always the requirement; red-at-base was a proxy. Measured: S-3 kills the `call_merit`-only
misroute, S-2 kills the `C'=R'=0` collapse.

**B-14 — T4 also reported that spec §10.4's "catch (e) anywhere but P-1 is broken" constrains gate STYLE,
not just P-1.** Its first draft of the §4 joint-product gate read raw merits and therefore also caught the
fold-side mutant, which would have made the harness "broken" by that rule. It rewrote the gate to be purely
behavioural. Recorded because the constraint is non-obvious and the next author will hit it.

**B-15 — T6 landed `ae6f4ae` and self-checked its own gates, which is the discipline that matters.**
Reverting the estimator to line-blind fails 3 tests; injecting the naive any-seat mutant fails **exactly at
case 2** (multiway, different seat) while case 1 (heads-up) still passes — the trap reproduced and pinned.
`range_estimate.py` restored byte-for-byte, verified by an empty `git diff`. Both contradictory tests
resolved without deletion or weakening.

**B-16 — T5 threaded the harness with the default path provably untouched.** The signal reaches
`sample_postflop_decision` only under an explicit `line_aware` opt-in, so by default the keyword set is
*structurally* identical to before — pinned by a gate that spies the actual call kwargs in both states,
rather than argued statistically. Evidence the pins held: `BANDS` block byte-identical by sha256 against
`e518118`; an AST comparison of every module-level constant shows **0 moved, 0 dropped**; the whole diff
deletes exactly 2 lines, both function signatures, no numeric literal. The paired arms are *proved* paired,
not assumed: `aggressor_barrel_run` is 0 on the flop by construction, so flop-arrival counts must match
across arms, and a gate demands it. **No pinned band exited; W4-b was not triggered.**

**B-17 — T5 blocked on a FALSE SPEC LITERAL, and was right to. OWNER-RULED (2026-08-02).**
Spec S-5 demanded showdown frequency fall by `≥ 0.01`. T5 measured at four sample sizes and in three
configurations; the `N = 24000` asymptote is nit `−0.0121` · lag `−0.0072` · tag `−0.0061` ·
passive_fish `−0.0043` · maniac `−0.0031` · station `−0.0023`. **Five of six never reach it.** The literal
was set a priori by the spec author (me) before anything was measured.

The worker did the right thing three times over: it did not assert a number it had measured to be false, it
did not silently widen it, and it did not quietly substitute its own — it recorded the discrepancy in a
40-line flagged block and escalated. It also self-flagged that its interim floor was measure-anchored, which
is the habit this initiative distrusts.

**Diagnosis: not a mechanism defect — a badly chosen instrument.** Measured at the barrel node in the same
run, fold rate rises in clean ladder order (nit `+0.054` → station `+0.003`). Showdown frequency is a
heavily diluted read: 2,074 barrel nodes across 4,000 hands × 9 seats, only 37 of them nit's.

**Ruling: gate on the direct measure.** S-5 splits into **S-5a** (population fold-rate at barrel nodes —
decisive, literal floor `nit ≥ 0.03`, ladder ordering by tier) and **S-5b** (showdown frequency —
directional companion, floor `0.002`). The `0.03` must be documented in-module as a **floor with headroom,
not a fitted value**, with its derivation from the closed form; and the record must state that the
**unfitted** decisive effect-size gate is still S-1's literal `0.05`, which matched a prediction made before
measurement. The retired `0.01` and the evidence that killed it stay recorded.

**Rejected alternative:** re-setting the literal per persona to each measured value. That is fitting the
gate to the answer six times over — strictly worse than either shipping the honest floor or changing the
instrument.

**B-18 — T5 rebuilt S-5 under the ruling, and solved the comparison problem better than the ruling asked.**
The instruction was "gate on the direct measure". The worker noticed that comparing `P(fold)` between a
line-blind arm and a treated arm compares two *differently populated* samples unless the control also knows
where the barrel nodes were. It made `line_aware` **tri-state** — `False` (pinned default, derives nothing),
`_LINE_OBSERVE` (derives and **records** the node, threads **nothing**), `True` — so the comparison is
node-matched. Measured at `N = 8000`:

| persona | λ | in-scope nodes | P(fold) off | on | rise |
|---|---|---|---|---|---|
| nit | 0.60 | 41 | 0.2927 | 0.4390 | **+0.1463** |
| tag | 0.50 | 86 | 0.2791 | 0.3647 | +0.0856 |
| passive_fish | 0.35 | 270 | 0.4889 | 0.5299 | +0.0410 |
| lag | 0.35 | 206 | 0.3592 | 0.3961 | +0.0369 |
| maniac | 0.20 | 318 | 0.3774 | 0.4119 | +0.0346 |
| calling_station | 0.10 | 1621 | 0.2930 | 0.2971 | +0.0041 |

nit clears its `0.03` floor by **4.9×**. `N` was raised 4000 → 8000 because nit reaches only 14 in-scope
nodes at 4000, and a literal effect-size floor asserted over 14 observations is not worth asserting.

**It also declined to assert an ordering organic play does not support.** The `{lag, passive_fish} > maniac`
edge is unstable — at `N=4000` maniac beats lag outright; at `N=16000` the ladder returns. It asserted the
coarse order that IS stable at every `N` measured (`nit > tag > {lag, fish, maniac} > station`), documented
why the finer edge is unasserted, and **did not reach for a bigger N to manufacture the result**. The
λ-exact ordering claim stays where it is true: at the node, in odds space (T4's S-4).

**Director integration — a latent trap closed.** The tri-state dispatch used a truthy test (`if line_aware:`)
followed by an identity test (`is True`), so any truthy non-`True` value would have silently landed in
observe-mode: flag derived, node recorded, **nothing threaded** — a control arm masquerading as the
treatment, reporting `0.0` with no error. That is this initiative's signature failure mode wearing a new
costume. Rejected at the boundary with an explicit guard. The worker had self-flagged the risk.

**B-19 — T7 (independent mutant round) — ALL SIX CAUGHT, no harness defect.** Run by a different agent from
the ones that wrote the gates, one mutant at a time with byte-for-byte restoration between each:

| mutant | failing gates | expected | match |
|---|---|---|---|
| (a) `line_mult = 1.0` | 10 | fail | ✓ |
| (b) `_LINE_DELTA = 1e-12` | 9 incl. S-1's literal floor | fail | ✓ |
| (c) `call_merit`-only | 7 incl. **S-3** + P-1 | fail | ✓ |
| (d) `C' = R' = 0` collapse | 10 incl. **S-2** | fail | ✓ |
| (e) fold-side form | **1 — P-1 ALONE** (26 others pass) | P-1 alone | ✓ |
| (f) scope-blind | **1 — P-2 ALONE** (26 others pass) | P-2 | ✓ |

(b) and (d) are the two that defeated spec rev 1's gates during review; both are now dead. (e) confirms
P-1's structural check does work no behavioural gate can do — and that no other gate is wrongly reading raw
merits. Restoration verified: empty `git diff`, full suite green again (`1414 passed, 1 skipped`).

**B-20 — P-8 coverage delta, and a baseline clarification T7 raised.** Against the **immutable**
`persona-realism-start` snapshot: `349/1233 = 28.30%` → `335/1288 = 26.01%`, **−2.30pp**. Spec §8 cites
`27.70% → 26.01%`, which is the move against the **previous fixture**, not the immutable snapshot. Both
numbers are correct and consistent; they answer different questions. Recorded so a later reader does not
treat them as a contradiction. Owner-adjudicated as flagged mapper-track movement owned by `T-cover`
(B-6) — reported here, not re-judged.

---

## BUILD FAN-IN REVIEW (2026-08-02/03)

Three independent reviewers, all GIT-READ-ONLY and all pinned to base explicitly: `refuter` (Opus),
`persona-realism-theory-reviewer`, Codex Sol (`gpt-5.6-sol`, effort high). **Two returned FAIL, one
NEEDS-WORK.** None found a defect in the MECHANISM. All three broke, or corrected claims about, the GATES
and the documentation — for the **second time in this slice**, and at a deeper level than the spec review.

The first `refuter` attempt died on a connection error with no findings; the worktree was verified clean and
it was respawned. Recorded because a silently-dropped reviewer is indistinguishable from a clean pass.

### R-21 (Codex HIGH-1) — the SEVENTH mutant. ACCEPTED, reproduced, FIXED.
A mutant scaling CALL by `line_mult` and RAISE by `line_mult·(1 + 5e-13)`, skipping the perturbation when
`line_mult == 1.0` so the zero-lever bit-identity case still holds, **passed all 27 gates**. Reproduced by
me: my first attempt (perturbing unconditionally) was caught by the zero-lever bit-identity clause; adding
Codex's `== 1.0` guard reproduced its result exactly — `27 passed`.
It gets through because P-1 permits a `1e-12` factor spread, S-3 permits `1e-9` raise-share drift, S-4
permits `1e-12` composition error. **Those tolerances could not simply be tightened** — R-8 measured that
exact equality fails a *correct* implementation ~35% of the time.
**Owner-ruled FIX.** Extracted the transform into a production helper `_line_scaled` and added a gate that
grades it in isolation, bitwise. *(Superseded in scope by R-22 — see below; that fix alone was insufficient.)*

### R-22 (refuter HIGH-1) — P-1 never asserted the merits MOVED. ACCEPTED, FIXED. **The most serious finding of the slice.**
P-1 is the ONLY gate that can catch a fold-side implementation. It asserted: FOLD bitwise unchanged ·
CALL/RAISE ratios agree within `1e-12` · zero spread per persona · `≥300` observations. **None requires the
ratio to differ from `1.0`.** A vector in which *nothing moved* satisfies all four — fold unchanged, both
ratios exactly 1.0 so no split, spread 0. Confirmed by reading the gate; its own docstring claims "the
factor is `exp(-λ_p)`" and never asserts it.
Measured exploit: replace the entries scale with `pass`, apply the equivalent fold-side scale to `weights`
*after* `total = sum(weights)` — i.e. past the probe's capture instant. **Full suite `1414 passed`, exit 0,
while P-1 observed 0 differing merits and nit `ΔP(fold)` was `+0.13119`.**
**Director error, recorded.** I had earlier told the owner P-1 was non-vacuous because of its occupancy
floors. That was true and irrelevant: I verified the capture *fired*, never that what it captured had
*moved*. A gate can observe 1,800 things and learn nothing from any of them.

### R-23 (refuter HIGH-2) — the R-21 fix did NOT close it. ACCEPTED.
Measured: call `_line_scaled(...)` and **discard its result**, then apply the post-capture fold scale →
`28 passed`, including the new helper-isolation gate. Grading the helper in isolation proves nothing about
whether its return value reaches the normalization; the wiring spy proves only that it was *called*.

**THE FIX for R-21/R-22/R-23 — one assertion.** P-1 now pins each raw-merit ratio to the mechanism's own
predicted factor `exp(-λ_p)` and requires it strictly `< 1.0`. All three mutants die on it — independently
reproduced by me: *"720 of 720 raw-merit ratios are >= 1.0 — the prescribed transform did NOT move the
merits, so whatever moves the output is not it."* **Identity gate → sensitivity gate**, which is this
initiative's governing law and which P-1 was violating.
`rscale` cancellation **verified, not trusted**: all six shipped packs sit at their anchor so `rscale` is
exactly 1.0 and the grid would have proved nothing; a `model_copy` pack at `continue_ref = 0.37`
(`rscale = 1.6216`) returns relative error `0.000e+00` against `exp(-λ_p)`.

### R-24 (refuter MED-3) — S-6's discriminators missed the bug class they exist for. ACCEPTED, FIXED.
In all four fixtures the target seat acts *immediately* after the street's bettor, so the tracked aggressor
is never overwritten. Measured: adding `street_aggressor = a.position` to the CALL branch passes the entire
suite. **The shipped estimator is CORRECT** (2,456 organic nodes, 0 mismatches) — a gate hole, not a product
bug. Replaced with an **organic differential**: 96 live playouts, the replayed flag asserted node-for-node
against production. The mutant now fails at 5 of 1,528 nodes.

### R-25 (refuter MED-4) — three SHIPPED packs documented the dial as unread. ACCEPTED, FIXED.
`lag`/`maniac`/`tag` `_doc` entries still read "Nothing reads it yet — a later ticket…". True at T1, false
since T2, five commits earlier **in the same branch** — and committed data is the first thing a pack author
reads. Rewritten to present tense naming `_line_scaled`. `nit`/`passive_fish`/`calling_station` genuinely
carry no `_doc` array; the worker reported that rather than inventing version history, which is right.

### R-26 (theory MED-1) — the draw-exclusion REASON was false. ACCEPTED, corrected in code and spec.
Rev 2 excluded draws because "already priced by equity + the T1 threshold, and that machinery already moves
with street". **Both limbs false for the CALL leg**, verified by me: `_DRAW_CALL_BONUS` is a flat lookup
(`personas_postflop.py:293`) added flat at `:930` with no equity and no street term; the cited street-decay
machinery is aggression-side only. Measured: naked gutshot `P(call)` facing half-pot goes **UP** flop→turn
(nit `0.3556 → 0.3696`). **Exclusion stands, reason replaced** (F7's un-gated call bonus), and the known
consequence is now disclosed: a nit facing a second barrel continues MORE with a naked gutshot (`0.4224`)
than with ace-high (`0.3932`), inverted from `0.4224` vs `0.5415`.

### R-27 (theory MED-2) — the maniac's seed was justified by a channel v1 does not have. ACCEPTED, text fixed.
"Its reaction lives in the raise share, which this slice deliberately does not touch" is true of
`P(raise|continue)` and **false of `P(raise)` absolute**, which falls at every in-scope cell because both
defend merits scale together. Reproduced by me to four decimals: maniac AIR `0.2853 → 0.2513`, lag AIR
`0.1793 → 0.1385`. On the river polar cell there is no call leg, so the mechanism is a **pure bluff-raise
suppressor** (maniac `0.2041 → 0.1735`). So the maniac and LAG contest a barrel *less* — wrong sign for both
archetypes. **Documentation defect, not behaviour**: ratio-neutrality is the deliberate safety property and
the raise-side response is stage-2 (`R9-DEFENCE-b`, do-not-build). Justification struck; measured deltas
recorded so `R9-DEFENCE-b` inherits them.

### R-28 (Codex MED-3) — spec ordering criterion vs shipped gate. ACCEPTED, spec amended.
Spec required strict-between-tiers + equal-within-tie; the gate asserts a coarser order and documents why.
The ruling authorising that was given mid-build but never written into the spec — so spec and test
disagreed. Spec now records the coarse order as the requirement, with the unasserted edge and its reason.

### R-29 (Codex MED-2) — S-5 is NOT node-matched. ACCEPTED, label withdrawn.
The arms share a seed schedule and equal flop arrivals, but diverge after the first differing action —
in-scope node counts differ (tag 86/85, fish 270/268). An earlier ledger entry of mine called the comparison
"node-matched"; that claim was not earned. It is **seed-paired, end-to-end**. The measurement stands (the
`+0.1463` effect dwarfs a ≤1% node-count difference); the overclaim does not.

### R-30 (theory LOW) — "two independent checks" on `_LINE_DELTA` were not independent. ACCEPTED, reworded.
Check 1 tests that the implementation matches arithmetic the design performed *assuming* 1.0; check 2 is a
consistency relation between two authored numbers. Honest framing: **1.0 is a NORMALISATION** so
`line_sensitivity` reads as λ directly. The anti-`1e-12` argument is untouched and remains load-bearing.

### Accepted as forward-looking, no change to this slice
- **(theory MED-3)** The banded population run stays line-blind while production opts in, so the three
  HARD-today gates certify a bot that is not the one shipped. Owner-ruled acceptable (§6.1), and the risk is
  small — measured line-on WTSD deltas sit 5–25× inside the nearest band margin. **Added to W4-b's brief as
  a precondition: the single Wave-4 re-measure MUST run with `context_aware=True` AND `line_aware=True`, or
  it re-anchors the bands onto a counterfactual bot.** Two default-off harness levers now; a third must not
  be added silently.
- **(theory MED-4)** Arrival inverts against the ladder: nit (largest λ) reaches 41 in-scope barrel nodes
  per 8,000 hands, the station (smallest λ) reaches 1,619 — a ~40× spread, at most 2× of it seat count. So
  the roster-level gain from this slice is dominated by the station. This is the SYNTHESIS **arrival thesis**
  surfacing inside a policy slice; recorded as an arrival-class datum for `T-ARR`/`W-ARR`. A later slice must
  not read this slice's population effect size as evidence about the POLICY.
- **(theory MED-5)** No fold-to-second-barrel provenance row exists, so the COMBINED defender-side turn
  tightening (price channel `+0.11..+0.25` plus this slice's `+0.03..+0.15`) has no comparator. **Programme
  gate: no THIRD defender-side turn factor lands on this node without a joint re-read.**
- **(refuter LOW-7)** nit's decisive literal rests on 41 nodes, so the estimate moves in steps of `1/41 =
  0.0244` against a `0.03` floor — the gate is ~1.2 node-flips wide with ~6 flips of headroom. Deterministic
  under pinned seeds, so not flaky today. **Stated in the PR as a known fragility, not a stable literal.**
- **(refuter LOW-6, process)** The review worktree was a moving target and at one point contained my own
  planted mutant. The refuter took its measurements from a clean byte-copy and said so. **Standing rule:
  review the COMMIT, never the worktree**, and land in-flight work before crediting it.

### Reviewer accuracy on this round
Three reviewers, thirteen findings, **zero hallucinated line numbers** and zero findings I could not
reproduce. Each recorded what it could not verify. The two HIGH findings that mattered most came from the
reviewer that had to be respawned after dying — had I treated that death as a pass, both would have shipped.

**Score across the whole slice: the maker was wrong 30 times; the reviewers, on substance, zero.** The
mechanism never changed. Every round, the gates did.

---

### Reviewer accuracy note

Both reviewers independently re-verified base after being warned about the stale tree, and both recorded
what they could **not** verify — the refuter flagged that it could not confirm the suite-green claim and
that the contract map's "eight capture-rng consumers" count looked more like six modules; Codex flagged
nothing it had not read or measured. Neither hallucinated a line number. The one factual error in the whole
round was **mine** (R-13).

**Score: the maker was wrong 14 times and the reviewers 0 times on substance.** Rev 1's mechanism survived
unchanged; its acceptance harness did not survive at all.
