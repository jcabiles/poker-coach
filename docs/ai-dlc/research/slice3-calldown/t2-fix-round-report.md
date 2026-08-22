# S3-T2 fix round — the calling-dial retune, built and measured

**Bottom line. The retune ships. Both registered reduction floors are MET on the
gating instrument: the nit's went-to-showdown rate falls 1.80 percentage points
against a floor of 1.0, and the TAG's falls 6.15 against a floor of 3.5. The
LAG's floor was withdrawn before building, on the owner's ruling, because its
dial is not that archetype's lever. Two guards that were silently measuring the
calling dial rather than their own claim were repaired first, and both are
STRONGER afterwards, not weaker — one now fails a mechanism regression it could
not previously see at all, and the other now asserts a quantity that is exactly
invariant to the dial. The five-seed de-robotization gate passes 5 of 5 with the
binding pair LAG–TAG at 1.765554 against a floor of 1.254429. Eight pinned
fixtures were re-recorded, every one with an attribution check that reverts the
two pack files and shows the old value returning.**

"Went to showdown" is the share of hands a persona takes to showdown out of the
hands where it saw the flop. S3-T2 is ticket 2 of improvement slice 3 (calldown)
of the bot-realism flywheel: the retune of the per-persona `call_looseness` pack
values, which govern how often a bot continues when it faces a wager. The "band
harness" is the pinned six-persona population inside
`backend/tests/test_personas_postflop.py`; it is the gating instrument. The
50,000-hand export is diagnostic only.

Companion documents: the target and its derivation are in
`t2-preregistration.md` (revision 3) beside this file; the reason the first
attempt was blocked is in `t2-findings.md`; the three items filed rather than
fixed are in `../../ledger/flywheel-slice3-calldown.md`.

Branch `feat/slice3-t2-fix-round`, based on `aaaee50` (the merge of the blocked
S3-T2 findings, pull request #213).

## 1. What shipped

| file | change |
|---|---|
| `content/personas/nit.json` | `call_looseness` 0.45 → 0.32, version 1.10.0 → 1.11.0 |
| `content/personas/tag.json` | `call_looseness` 0.6 → 0.38, version 1.10.0 → 1.11.0 |
| `backend/tests/test_personas_postflop.py` | guard A repaired; two went-to-showdown ceilings ratcheted; five fixtures re-recorded; one stale band re-centred |
| `backend/tests/test_range_estimate.py` | guard C re-expressed in log-odds |
| `backend/tests/test_limper_coverage_belt.py` | `_PRE_M3_FIRES` re-recorded |
| `backend/tests/test_buyin_spread.py` | four export digests re-recorded |
| `backend/tests/test_coverage_baseline.py` data fixture | coverage baseline re-recorded |
| `backend/tests/test_counterfactual.py` | worked example reads the shipped dial |
| `backend/app/domain/personas_postflop.py` | one comment sentence corrected; NO logic change |

No engine logic was touched. `content/personas/lag.json` and the other three
packs are byte-identical to `aaaee50`.

## 2. Registered versus achieved

Registered in `t2-preregistration.md` before any pack value was changed, and
measured on the band harness at its pinned seed (`random.Random(20260710)`) and
its stable sample (`_WTSD_ORDER_N` = 4,000 hands).

| persona | registered floor | achieved | verdict |
|---|---|---|---|
| nit | ≥ 1.0pp | **−1.80pp** (0.6353 → 0.6173) | **MET** |
| tag | ≥ 3.5pp | **−6.15pp** (0.6144 → 0.5528) | **MET** |
| lag | WITHDRAWN (owner ruling 11, 2026-08-22) | not tuned; +1.05pp as a composition effect | withdrawn, filed |

The dial values are not set by the reduction target. The nit's is set by the α
fold-ceiling — `α = f/(1+f)` is how often a bluff-catcher may fold facing a bet
of `f` times the pot before a balanced bettor's bluffs become free money — which
admits no dial below about 0.31. The TAG's is set by the deterministic
1,728-cell nit-versus-TAG separation sweep, which stops it collapsing onto the
nit. Both caps were re-measured on this branch and reproduce the
pre-registration cell for cell.

## 3. Went-to-showdown, before and after, on both instruments

The band harness is the gating instrument. The 50,000-hand pooled export is
diagnostic context, run on the ratified nine-seat lineup
(`tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac`) at seed
20260817, before and after, with nothing but the two pack files differing.

| persona | harness before | harness after | change | export before | export after | change |
|---|---|---|---|---|---|---|
| nit | 0.6353 | 0.6173 | **−1.80pp** | 58.9% | 57.9% | −1.0pp |
| tag | 0.6144 | 0.5528 | **−6.15pp** | 53.9% | 50.0% | −3.9pp |
| lag | 0.5664 | 0.5769 | +1.05pp | 52.1% | 51.1% | −1.0pp |
| maniac | 0.5887 | 0.5945 | +0.59pp | 53.4% | 52.6% | −0.8pp |
| calling_station | 0.7060 | 0.7010 | −0.50pp | 66.4% | 66.3% | −0.1pp |
| passive_fish | 0.5324 | 0.5204 | −1.20pp | 48.8% | 47.6% | −1.2pp |
| **pool** | — | — | — | **54.9%** | **53.4%** | **−1.5pp** |

**The two instruments disagree about the LAG, and the disagreement is real
rather than a mistake.** They play different tables: the export plays the
ratified lineup, the harness plays six persona-weighted lineups at its own
pinned seed. A composition effect of one point is free to differ in sign between
them. The harness is what the bands assert against, so the harness number is the
one that governs; the export number is reported because the ticket asks for it.

**Two personas whose packs were not touched moved anyway**, and the mechanism is
worth stating once: the calling dial scales the WHOLE continue side of a facing
node — RAISE included, through the `rscale` coupling — so a tighter nit and a
tighter TAG also RAISE less often, and every persona they face meets less
aggression, folds less in response, and rides more hands to showdown. The
calling station's own decision function is bitwise unchanged (its dial is 4.0,
above the strong-draw split's predicate, and
`test_nd_t4_calling_station_byte_identical_on_strong_draw` still passes
untouched); only the hands it is dealt into changed.

## 4. Ordering legs and bands

No HARD ordering leg is breached, and neither transition-scoped leg needed its
one authorized move — so no authorization was spent.

| leg | kind | reading | verdict |
|---|---|---|---|
| station > tag | HARD | 0.7010 > 0.5528 | holds |
| station > lag | HARD | 0.7010 > 0.5769 | holds |
| maniac < station | HARD | 0.5945 < 0.7010 | holds |
| fish < tag | transition-scoped | 0.5204 < 0.5528 | holds, not moved |
| station − fish > 0.10 | transition-scoped | 0.1806 | holds, not moved |

Every aggression-factor and fold-to-continuation-bet reading stays inside its
band; the bands themselves are untouched by this ticket. The nit's
fold-to-continuation-bet rises 0.3563 → 0.4350 and the TAG's 0.2715 → 0.3258,
both toward the contract's grounded direction and both still inside their band.

## 5. The two guard repairs

Both were mandated by owner ruling 11 of 2026-08-22, after a theory review
reproduced the blockage. Neither weakens a claim.

### Guard A — the trace-node draw-fold ceiling, now a computed comparator

`test_s3t1b_trace_node_folds_no_more_than_the_protected_engine_did` used to
compare the live engine against six FROZEN CONSTANTS harvested at the calling
dials of the day, with a 1e-12 tolerance. At that node — a 15-out combo draw
facing 4 into a live pot of 10 — the price mandates the whole strong-draw call
bonus, so the bonus term is dial-independent, but the bucket's base call merit
is `call_base * L` and the fold merit does not depend on the dial at all. The
constants were therefore a strictly decreasing function of the dial, and the
guard forbade every downward retune: a cut of one thousandth breached it.

The comparator is now COMPUTED — the legacy expression `max(looseness, 1.0)`
evaluated at the pack's own current dial, reproduced in-process by replacing
`_strong_draw_protected_share` with one that returns 1.0. Measured on this
branch:

| probe | expected | measured |
|---|---|---|
| shipped engine, shipped dials | GREEN | GREEN, headroom exactly 0.0 for all six personas |
| dial cut to 0.10 for nit, tag and lag | GREEN (a dial change is not this guard's business) | GREEN |
| protected share regressed to 0.99 | RED | RED for all five dialled personas; the calling station is exempt by construction (dial 4.0 never takes the branch) |

**The claim it keeps is the claim S3-T1b actually made** — that a protected share
may not come back below 1.0 at a node whose price mandates the whole bonus — and
it now catches that regression, which the constant form could not see at all.
What it no longer pretends to catch is a persona being tuned tighter, which has
its own gates: the α ceiling, the went-to-showdown ceilings, and the separation
floor.

### Guard C — the estimator's price response, now in log-odds

`test_estimator_prices_the_faced_bet` asked for 0.20 of PROBABILITY span between
a half-pot bet and a three-times-pot bet, on both a middle pair and an air hand.
The air leg saturates: at three-times-pot the air hand already folds 0.965, so
under 0.035 of room is left above it, and anything that makes the TAG fold more
at the SMALL price eats the margin without weakening the price response at all.

| tag dial | air probability span | air log-odds span |
|---|---|---|
| 0.60 | 0.2698 | 2.502646490 |
| 0.45 | 0.2209 | 2.502646490 |
| 0.42 | 0.2100 | 2.502646490 |
| 0.40 | 0.2025 | 2.502646490 |
| **0.38 (shipped)** | **0.1948** | **2.502646490** |
| 0.37 | 0.1909 | 2.502646490 |
| 0.30 | 0.1619 | 2.502646490 |

**The log-odds span is exactly invariant to the dial, to nine decimal places,
and that is a fact about the mechanism rather than a lucky measurement.** The
dial multiplies the whole continue side of the merit vector, so the
fold-versus-continue odds carry a factor of `L` common to every price, and it
cancels in a span between two prices. The threshold of 2.0 therefore has a fixed
0.50 of margin no retune can spend, while the defect this test was written for —
an estimator that builds CALL with no price, making all three distributions
identical — still reads EXACTLY 0.0. The probability-span form is kept on the
middle-pair hole, which does not saturate.

## 6. The ceiling ratchet

The interim regime moves each ceiling to the measurement plus three binomial
standard deviations, rounded outward to the nearest hundredth, never above the
incumbent. `n` is each persona's flop-seen count in the 4,000-hand sample;
`sd = sqrt(p * (1 - p) / n)`.

| persona | measured | n | 3 sd | p + 3sd | ratchet | incumbent | INSTALLED | what happened |
|---|---|---|---|---|---|---|---|---|
| nit | 0.6173 | 972 | 0.046770 | 0.664054 | 0.67 | 0.68 | **0.67** | tightens 1 point |
| tag | 0.5528 | 1637 | 0.036866 | 0.589707 | 0.59 | 0.65 | **0.59** | tightens 6 points |
| lag | 0.5769 | 2418 | 0.030141 | 0.607064 | 0.61 | 0.59 | 0.59 | capped by the incumbent |
| maniac | 0.5945 | 3961 | 0.023404 | 0.617950 | 0.62 | 0.62 | 0.62 | unchanged |
| calling_station | 0.7010 | 5622 | 0.018318 | 0.719314 | 0.72 | 0.72 | 0.72 | unchanged |
| passive_fish | 0.5204 | 4189 | 0.023157 | 0.543567 | 0.55 | 0.55 | 0.55 | unchanged |

No persona ships above its ratcheted ceiling: the two that moved UP are the LAG
at 0.5769 against 0.59 and the maniac at 0.5945 against 0.62. The ratchet does
not apply to a persona that moved up; the arithmetic is shown anyway so a reader
can see it was computed rather than skipped.

## 7. The five-seed de-robotization gate

`PYTHONPATH=. python -m tools.derobo_gate --check --all-seeds` — **PASS 5/5**,
baseline artifact `a5baseline-98abd160f03a501b`, candidate configuration hash
`c4debe87dfeb7f` on every seed.

| seed | min pairwise distance | binding pair | second-tightest pair | labels | determinism |
|---|---|---|---|---|---|
| 601 | 1.853360 | **LAG–TAG** | nit–TAG 2.089428 | 6/6 | pass |
| 602 | 1.792393 | **LAG–TAG** | nit–TAG 2.561841 | 6/6 | pass |
| 603 | **1.765554** (tightest) | **LAG–TAG** | nit–TAG 2.073777 | 6/6 | pass |
| 604 | 2.008972 | **LAG–TAG** | nit–TAG 2.155674 | 6/6 | pass |
| 605 | 1.958660 | **LAG–TAG** | nit–TAG 2.766218 | 6/6 | pass |

Required on every seed: 1.254429 (0.70 of the frozen baseline's 1.792042). The
binding pair is LAG–TAG on all five seeds. **The gate's JSON does not name the
pair**, so it was recomputed from the report's own per-persona measured vectors
and the frozen baseline's mean and standard-deviation scales; each recomputation
reproduces the reported minimum exactly, which is what makes the pair name
evidence rather than an assumption. The separation floor never came close to
binding, so ruling 3's stop-and-report did not fire.

## 8. Every re-record, with provenance and attribution

**The attribution check is one experiment, run once, covering all eight.** With
`content/personas/nit.json` and `content/personas/tag.json` reverted to
`aaaee50` and EVERY OTHER edit on this branch left in place, each quantity below
recomputes to its OLD value; restoring the packs reproduces the NEW one. No
tolerance was widened anywhere.

| fixture | file | old → new | why it moved |
|---|---|---|---|
| `_GOLDEN_STATS_N200` | `test_personas_postflop.py` | all six rows move | n=200 tripwire; both dials move and the shared random stream displaces from the first changed decision |
| `_ND_C5_BASE_VECTORS` | `test_personas_postflop.py` | 4 of 12 cells move | the base engine reads the dial off the strong-draw branch too (`call_base * L`) |
| `_W3R6_RAISE_DROP` | `test_personas_postflop.py` | the two TAG rows move | normalized raise shares at a facing node; a smaller CALL merit re-weights the vector |
| went-to-showdown ceilings | `test_personas_postflop.py` `BANDS` | nit 0.68→0.67, tag 0.65→0.59 | the ratchet of §6, not a re-record |
| `_PRE_M3_FIRES` | `test_limper_coverage_belt.py` | all nine pairs move | production `bot_decision`; different actions displace the shared stream |
| coverage baseline | `tests/data/coverage_baseline.json` | total 1228→1239, graded 318→337 | same displacement, different sweep |
| export digests (4) | `test_buyin_spread.py` | all four move | every byte of a seeded export changes; the manifest moves because `config_hash` covers the loaded pack models and both version strings |
| `_ND_LO_LOOSENESS` | `test_personas_postflop.py` | literal → read from the pack | not a re-record: a transcribed dial turned every gate below it into an assertion that the dial had not changed |

**Two controls inside the re-records say the cause is the packs and nothing
else.** In `_ND_C5_BASE_VECTORS`, re-harvesting all twelve cells moved EXACTLY
the nit's and the TAG's four — the eight belonging to untouched personas are
byte-identical. In `_W3R6_RAISE_DROP`, the maniac's two rows are byte-identical
while the TAG's two move; that fixture is a single-node unit measurement with no
shared random stream to displace, so it isolates the pack edit from the
displacement effect. The damp ratio that fixture is really about is unchanged to
three decimals on both TAG rows (0.398 → 0.390 middle pair, 0.438 → 0.432 top
pair): the residual is re-normalization, not a change in the damp.

### One band was re-centred, and it is not a re-record

`test_preflop_node_occupancy_arrival_grid`'s roster-wide unopened-arrival watch
moved from `[0.275, 0.335]` to `[0.295, 0.355]` — **the same width, a new
centre**. `call_looseness` is read only by `sample_postflop_decision`, so a
calling-dial retune cannot change a single preflop decision's policy; it reaches
this number only by displacing the shared random stream. A 12-seed PAIRED sweep
(identical seeds on both arms, only the two dials differing) confirms that and
also shows the old centre had gone stale:

| arm | mean | sd | min | max |
|---|---|---|---|---|
| baseline dials | 0.3256 | 0.0112 | 0.3123 | **0.3534** |
| shipped dials | 0.3240 | 0.0070 | 0.3170 | 0.3361 |

Paired delta −0.0016, sd 0.0096, t = −0.58 — no effect. The BASELINE arm alone
reads 0.3534 on one of the twelve seeds, outside the old band with none of this
ticket in it. New centre 0.325, the pooled mean of both arms. This is the same
method and the same justification the 2026-07-31 re-centring used.

## 9. What was filed rather than fixed

All three are in `../../ledger/flywheel-slice3-calldown.md`.

1. **CONTRACT DEFECT (MEDIUM): α bounds an archetype the contract asks to
   over-fold.** At the shipped 0.32 the nit folds to continuation bets 43.5
   percent of the time against a grounded band floor of 60, and it cannot go
   further: at a dial of 0.31 its α headroom is 0.0021 and at 0.30 it breaches.
   The α test stays RAW and was not edited (owner ruling 10).
2. **The LAG's floor, withdrawn.** Its showdown rate on this harness is not a
   function of its own dial: the cross-persona term is the same size as the
   own-dial term, and a LAG cut deep enough to matter hands nearly half of the
   TAG's gain back. The measurements are in the pre-registration §5.
3. **`_DRAW_FREE_RIVER_PROB` stays at 0.30**, filed against theory contract §4
   row P6/F7 (the draw-bonus equity gate).

## 10. Acceptance criteria

| # | criterion | verdict |
|---|---|---|
| 1 | went-to-showdown reduced by the pre-registered amount for nit, tag, lag | **PASS for nit and tag** (−1.80 against ≥1.0; −6.15 against ≥3.5). The LAG's floor was WITHDRAWN before building under owner ruling 11 and is filed. |
| 2 | no aggression-factor or fold-to-continuation-bet leg leaves its band | **PASS** — `test_persona_postflop_bands` green for all six personas |
| 3 | five-seed gate green, LAG–TAG reported explicitly | **PASS** — 5/5, LAG–TAG binding on every seed, tightest 1.765554 vs 1.254429 |
| 4 | pooled export went-to-showdown reported before/after | **PASS** — §3, pool 54.9% → 53.4% |
| 5 | any HARD ordering breach is a stop-and-report | **N/A, none breached** — §4 |

## 11. Checks

| command | result |
|---|---|
| `./scripts/verify.sh` | BACKEND VERIFY OK |
| `cd backend && ruff check .` | clean |
| `python -m tools.derobo_gate --check --all-seeds` | GATE PASS (5/5) |
| `pytest -k "persona_postflop_bands or wtsd_ordering"` | green |

## 12. What a reviewer should press on

- **Guard A's repair is the load-bearing judgement of this round.** It is a gate
  whose comparator is now computed from the engine it guards. The argument that
  this keeps force is in §5 and in the test's own docstring; the counter-argument
  — that the two engines are identical by construction at this node, so the
  guard's force against a dial change is gone deliberately — is stated there
  too, because the owner's ruling says to state it rather than bury it.
- **The LAG moves in opposite directions on the two instruments.** §3 argues
  that is a composition effect and that the harness governs. Both numbers are
  reported so the claim can be checked rather than taken.
- **The nit's movement is inside its own noise.** Its flop-seen sample is the
  roster's smallest at 972 hands, so one binomial standard deviation is about
  1.5 points and the measured 1.80 is 1.2 of them. The registered floor was set
  at 1.0 for exactly that reason, and the shortfall against the 2.52-point
  first-order prediction is reported rather than hidden.
- **`test_range_estimate.py` is outside the ticket's nominal file list.** It was
  edited because owner ruling 11 names guard C by test and mandates the log-odds
  re-expression; the change is confined to that one assertion.
