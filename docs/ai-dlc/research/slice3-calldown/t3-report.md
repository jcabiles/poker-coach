# S3-T3 — the stack-to-pot value lever, built and measured

**Bottom line. The lever ships, all five acceptance criteria pass, and the
headline is a measurement rather than a win: the composition defect the ticket
was aimed at is 5.45 percentage points wide, and the whole of this lever moves
0.10 of it. The reason is now measured rather than argued — the gap is mostly
ARRIVAL, not policy. Bots reach stack-capped decisions holding stronger hands
(they went there to get all in), and no multiplier at the merit layer can change
who arrives. What the lever does buy is real but narrow: the value side of the
bluff-share formula is no longer a constant in stack depth, made-hand betting
falls 0.84 points at capped decisions, the bluff side does not move by a single
bit anywhere, and every decision at or above a persona's `spr_commit` is
bit-identical over 266,776 measured nodes. The five-seed de-robotization gate
passes 5 of 5, the LAG's went-to-showdown ceiling holds with 1.13 points of
headroom, and three stream-displacement fixtures were re-recorded, each with an
attribution check that reproduces its old value.**

S3-T3 is ticket 3 of improvement slice 3 (the calldown slice) of the bot-realism
flywheel. "Stack-to-pot ratio" (SPR) is a seat's remaining stack divided by the
pot. A "capped" or "cap-exposed" decision is one where the seat cannot wager its
own largest authored bet size, because its stack is smaller than that size. "Went
to showdown" is the share of hands a persona takes to showdown out of the hands
where it saw the flop.

Companion documents: the directions this ticket registered before the multiplier
existed are in `t3-preregistration.md` beside this file; the contract map is
`../../contracts/flywheel-slice3-t3-valueside.md`; what was filed rather than
fixed is in `../../ledger/flywheel-slice3-calldown.md`.

Branch `feat/slice3-t3-spr-value`, based on `4f653ef` (the merge of S3-T2, pull
request #215).

## 1. What shipped

| file | change |
|---|---|
| `backend/app/domain/personas_postflop.py` | `_value_spr_mult` + `_VALUE_SPR_FLOOR` (0.88) + `_VALUE_SPR_BUCKETS`; one multiplication on the unopened made-value BET merit |
| `backend/tools/capped_composition_probe.py` | NEW — the instrument acceptance criterion 1 needed and did not have |
| `backend/tests/test_personas_postflop.py` | four new tests; `_GOLDEN_STATS_N200` re-recorded; two went-to-showdown ceilings ratcheted |
| `backend/tests/test_limper_coverage_belt.py` | `_PRE_M3_FIRES` re-recorded |
| `backend/tests/test_coverage_baseline.py` + its data fixture | coverage baseline re-recorded |
| `docs/ai-dlc/contracts/persona-realism-theory-contract.md` | §3 amendment A8 — the bluff-share formula's limits |

**No persona pack changed.** Every one of `content/personas/*.json` is
byte-identical to `4f653ef`.

**The lever, in one paragraph.** `_value_spr_mult(spr, spr_commit)` returns
exactly 1.0 at and above the pack's `spr_commit` and falls linearly to
`_VALUE_SPR_FLOOR` at a stack-to-pot ratio of zero — the same ramp shape the
existing below-commitment draw damp already uses, so the module's two
stack-keyed damps read the same geometry. It multiplies the made-value
aggressive merit on the unopened BET arm, for middle pair and better only. It
reads `stack_bb` and `pot_bb` and nothing else.

### The three scope decisions, stated rather than assumed

**BET only, not RAISE.** The binding rules allow the raising arm only on a
measurement that capped RAISE nodes carry most of the defect. **That
measurement was taken and says the opposite**: the probe finds the whole facing
population — every hand class, every action, capped and uncapped — moves by
exactly 0.0 under this lever, and the unopened BET population carries the entire
effect. BET-only also matches the precedent the two neighbouring multipliers set
(`pos_mult` and the multiway value damp are both BET-only on this arm), and a
raise's realised pot-fraction is not `stack_bb / pot_bb` — recovering it needs
the seat's street investment, which is not in this ticket.

**Made-value buckets only.** Middle pair and better. An air or ace-high hand
holding a draw also reaches this branch, and damping it would put the lever on
the semi-bluff side, which is not what "made-value aggression" means.

**Position in the sequence: after the multiway damp, before the texture damps,
and well before `pos_mult`, which stays last.** No existing multiplier moved.
Among pure multipliers the order is arithmetically irrelevant, so this is a
readability choice with one hard constraint behind it: everything further down
the block is either a texture term or a river floor that ZEROES the merit, and a
damp applied after a floor of 0.0 would be dead code. The design seed said
"before position and multiway"; the code already applies multiway inside this
block, so that instruction could not be followed literally and the position was
chosen explicitly instead.

## 2. Criterion 1 had no instrument, so this ticket built one

**No fixture, test or tool in this repository measured capped-versus-uncapped
composition.** The contract map searched for one and found nothing; the only
prior implementation lived in a design dossier that modified no repository file.

`backend/tools/capped_composition_probe.py` is the replacement, and its design
decision is that **the primary comparison carries zero sampling variance**. At
every postflop decision of a seeded playout it reads the sampler's normalized
action-probability vector twice — once with `_VALUE_SPR_FLOOR` forced to 1.0
(which is the pre-S3-T3 engine exactly, because multiplying by 1.0 is the
identity in floating point) and once at the shipped floor — using the capture-rng
pattern from `backend/tests/node_trace.py`, which records the weights of the
action draw without disturbing it. Both readings are taken at the SAME node on a
throwaway RNG, so the live playout is unchanged by being measured and the
difference between the two vectors is the policy's exact response rather than a
sample of it.

What still carries noise is WHICH nodes appear, which is why every figure below
is pooled over three seeds and the per-seed spread is shown.

    PYTHONPATH=. .venv/bin/python -m tools.capped_composition_probe \
        --hands 20000 --seeds 601,20260817,20260818

## 3. The probe, before and after — 60,000 hands, ratified lineup

### 3.1 The action mix, paired at each node

Expected probability of BET at unopened decisions, by hand class. Every figure is
an average over the stated node count of an exact per-node probability.

| population | nodes | P(bet) before | P(bet) after | change |
|---|---|---|---|---|
| **capped, made value** | 13,211 | 0.57984 | 0.57148 | **−0.836pp** |
| capped, bluff cell | 3,942 | 0.17515 | 0.17515 | **0.000** |
| capped, draw cell | 1,340 | 0.44706 | 0.44706 | **0.000** |
| uncapped, made value | 102,686 | 0.43481 | 0.43448 | −0.033pp |
| uncapped, bluff cell | 65,605 | 0.12483 | 0.12483 | **0.000** |
| uncapped, draw cell | 36,008 | 0.26096 | 0.26096 | **0.000** |

The freed mass goes to CHECK and nowhere else: at every row the CHECK delta is
the exact negative of the BET delta.

**The facing population does not move at all.** All six facing cells — bluff,
draw and made value, capped and uncapped, 119,543 nodes — read a delta of exactly
0.0 on every one of BET, RAISE, CHECK, CALL and FOLD. That is the BET-only scope
confirmed on the population rather than argued from the code.

**The uncapped made-value row moving by 0.033pp is the pre-registered side
effect, not a leak.** The ramp is keyed on `spr_commit` (1.2 to 3.3 across the
six packs) while a decision is cap-exposed only below the largest authored size
(1.0 for five packs, 1.5 for the maniac), so the lever fires on a superset of
capped decisions. Pre-registration §2 item 5 registered exactly this. It is 25
times smaller than the effect at the decisions the lever is aimed at, which is
the number that says the targeting is sound.

### 3.2 The composition statistic criterion 1 asks about

The bluff cell's share of the expected unopened betting range:

| population | before | after | change |
|---|---|---|---|
| capped | 0.0771 | 0.0781 | **+0.0010** |
| uncapped | 0.1316 | 0.1317 | +0.0001 |
| **ratio capped ÷ uncapped** | **0.5863** | **0.5933** | **+0.0070** |

Per seed, so the reader can see the sign is not one seed's luck:

| seed | ratio before | ratio after | change |
|---|---|---|---|
| 601 | 0.5953 | 0.6022 | +0.0069 |
| 20260817 | 0.5790 | 0.5858 | +0.0068 |
| 20260818 | 0.5847 | 0.5919 | +0.0072 |

**Three of three seeds move in the registered direction, and the spread between
them is 0.0004 against an effect of 0.0070** — the paired design is why that
ratio is 17 to 1 rather than the other way round. On unpaired realized counts at
this sample the effect would be invisible.

### 3.3 The finding that matters more than the lever

**The capped-versus-uncapped gap is 5.45 percentage points and this lever closes
0.10 of it — under two percent.** That is not a failure of the lever's strength;
it is what the gap is made of. Paired at the same node, the policy's whole
response is 0.0010. Everything else is composition: capped decisions are reached
by stronger ranges, because hands go to a capped decision in order to get all in.
`π`, how often a seat actually holds each hand class at a node, is arrival, and
the merit layer cannot see arrival at all.

**Consequence for future work, and it is the reason contract §3 was amended:** a
merit-layer lever moves this statistic toward calibration on a POOLED population
and can never satisfy the identity at a node. Anyone who reads "the value side
has a lever now" and retries the bluff-side repricing PR #199 withdrew will find
the same wall — roughly 25 percent of capped-node value betting would have to go,
against about 10 percent of total available motion.

## 4. Went-to-showdown, on both instruments

The band harness is the gating instrument (its own pinned seed, `_WTSD_ORDER_N` =
4,000 hands). The 50,000-hand pooled export at seed 20260817 on the ratified
nine-seat lineup is diagnostic.

| persona | harness before | harness after | change | ceiling | export before | export after | change |
|---|---|---|---|---|---|---|---|
| nit | 0.6173 | 0.6030 | −1.43pp | 0.65 | 57.9% | 58.4% | +0.5pp |
| tag | 0.5528 | 0.5545 | +0.17pp | 0.59 | 50.0% | 50.1% | +0.1pp |
| **lag** | **0.5769** | **0.5787** | **+0.18pp** | **0.59** | 51.1% | 51.5% | +0.4pp |
| maniac | 0.5945 | 0.5988 | +0.43pp | 0.62 | 52.6% | 52.2% | −0.4pp |
| calling_station | 0.7010 | 0.6916 | −0.94pp | 0.72 | 66.3% | 66.7% | +0.4pp |
| passive_fish | 0.5204 | 0.5098 | −1.06pp | 0.54 | 47.6% | 47.9% | +0.3pp |
| **pool** | — | — | — | — | **53.4%** | **53.6%** | **+0.2pp** |

**The two instruments disagree about the sign and this report says so rather than
quoting the one that flatters it.** The harness has four personas falling and two
rising; the export has five rising and one falling. The ticket pre-registered
that showdown frequency would RISE — a bet that becomes a check leaves more hands
alive — so the export agrees with the registration and the harness does not.
Both movements are small: the largest on either instrument is 1.4 points, and the
export's pooled +0.2pp is about 1.3 standard errors at 107,933 flop-seen
seat-hands. **The honest reading is that the effect on showdown frequency is too
small for either instrument to sign at these sample sizes.** No ceiling was moved
on the strength of a rise, which is what the regime requires anyway.

**The export's "before" arm reproduces S3-T2's shipped export numbers exactly,
persona for persona and on the pool** (nit 57.9, tag 50.0, lag 51.1, maniac 52.6,
station 66.3, fish 47.6, pool 53.4). That is not a coincidence to note in passing:
it is the proof that setting `_VALUE_SPR_FLOOR` to 1.0 recovers the pre-ticket
engine bit for bit, which is what every attribution check in §7 rests on.

### The LAG, the named risk

**The LAG holds, with 1.13 points of headroom against its 0.59 ceiling** — 0.5769
to 0.5787 on the harness. It was the ticket's registered risk for two reasons:
it had the least headroom on the roster after S3-T2 ratcheted its companions, and
its `spr_commit` of 3.0 is the second-widest ramp, so the lever fires at more of
its decisions than at any persona except the maniac. Its rise is 0.18 of one
binomial standard deviation at its own sample. **The ceiling was not moved and
the lever's floor was not weakened**, because neither was needed; the
pre-registration named raising the floor toward 1.0 as the response if it had
been.

## 5. Ordering legs and bands

No leg is breached and no transition-scoped leg needed its one authorized move.

| leg | kind | reading after | verdict |
|---|---|---|---|
| station > tag | HARD | 0.6916 > 0.5545 | holds |
| station > lag | HARD | 0.6916 > 0.5787 | holds |
| maniac < station | HARD | 0.5988 < 0.6916 | holds |
| fish < tag | transition-scoped | 0.5098 < 0.5545 | holds, not moved |
| station − fish > 0.10 | transition-scoped | 0.1818 | holds, not moved |

Every aggression-factor and fold-to-continuation-bet reading stays inside its
band, and no aggression-factor or fold-to-continuation-bet edge was touched:

| persona | AF before → after | AF band | fold-to-c-bet before → after | its band |
|---|---|---|---|---|
| nit | 1.4614 → 1.6390 | (0.6, 2.4) | 0.4350 → 0.4419 | (0.10, 0.90) |
| tag | 2.3829 → 2.5117 | (1.4, 3.6) | 0.3258 → 0.3669 | (0.0, 0.55) |
| lag | 2.6287 → 2.4552 | (1.5, 4.5) | 0.3189 → 0.3252 | (0.12, 0.64) |
| maniac | 3.1469 → 3.0946 | (2.4, 5.1) | 0.3256 → 0.3196 | (0.0, 0.61) |
| calling_station | 0.3177 → 0.3323 | (0.0, 1.056) | 0.1755 → 0.1728 | (0.0, 0.424) |
| passive_fish | 0.9120 → 0.9049 | (0.0, 1.560) | 0.4457 → 0.4273 | (0.0, 0.549) |

## 6. The ceiling ratchet

The interim regime (theory contract §5, amendment A4.2 item 2) moves a ceiling
after any slice that lowers a persona's showdown frequency, to the measurement
plus three binomial standard deviations, rounded outward to the nearest
hundredth, never above the incumbent. Three personas moved down, so three are
ratcheted; the other three are shown so a reader can see the arithmetic was
computed rather than skipped.

| persona | measured | n | 3 sd | p + 3sd | ratchet | incumbent | INSTALLED | what happened |
|---|---|---|---|---|---|---|---|---|
| nit | 0.6030 | 1010 | 0.046187 | 0.649157 | 0.65 | 0.67 | **0.65** | tightens 2 points |
| passive_fish | 0.5098 | 4166 | 0.023235 | 0.533077 | 0.54 | 0.55 | **0.54** | tightens 1 point |
| calling_station | 0.6916 | 5587 | 0.018536 | 0.710141 | 0.72 | 0.72 | 0.72 | unchanged |
| tag | 0.5545 | 1670 | 0.036487 | 0.590978 | — | 0.59 | 0.59 | moved up; no ratchet |
| lag | 0.5787 | 2440 | 0.029988 | 0.608677 | — | 0.59 | 0.59 | moved up; no ratchet |
| maniac | 0.5988 | 3993 | 0.023270 | 0.622068 | — | 0.62 | 0.62 | moved up; no ratchet |

**No persona ships above its ratcheted ceiling.** The tightest headroom on the
roster after this install is the maniac at 0.5988 against 0.62, then the LAG at
0.5787 against 0.59.

## 7. The five-seed de-robotization gate

`PYTHONPATH=. .venv/bin/python -m tools.derobo_gate --check --all-seeds` —
**GATE PASS, 5 of 5**, baseline artifact `a5baseline-98abd160f03a501b`, candidate
configuration hash `c4debe87dfeb7` on every seed (unchanged from S3-T2, because
no persona pack moved).

| seed | min pairwise distance | required | labels | determinism |
|---|---|---|---|---|
| 601 | 2.052617 | 1.254429 | 6/6 | pass |
| 602 | 1.778670 | 1.254429 | 6/6 | pass |
| 603 | **1.743322** (tightest) | 1.254429 | 6/6 | pass |
| 604 | 2.208862 | 1.254429 | 6/6 | pass |
| 605 | 1.861133 | 1.254429 | 6/6 | pass |

**The binding pair is LAG–TAG on all five seeds**, and that is evidence rather
than an assumption. The gate's JSON does not name the pair, so it was recomputed
from each seed's own per-persona measured vectors and the frozen baseline
artifact's mean and standard-deviation scales
(`a5_baseline_z.json`, ten stats, population standard deviation). **Every one of
the five recomputations reproduces the gate's reported minimum to the last
decimal it prints**, which is what makes the pair name checkable:

| seed | recomputed minimum | pair | second-tightest | pair | S3-T2's reading |
|---|---|---|---|---|---|
| 601 | 2.052617 | LAG–TAG | 2.282436 | nit–TAG | 1.853360 |
| 602 | 1.778670 | LAG–TAG | 2.410719 | nit–TAG | 1.792393 |
| 603 | 1.743322 | LAG–TAG | 2.273652 | nit–TAG | 1.765554 |
| 604 | 2.208862 | LAG–TAG | 2.344474 | nit–TAG | 2.008972 |
| 605 | 1.861133 | LAG–TAG | 2.563007 | nit–TAG | 1.958660 |

Three seeds tightened slightly and two loosened; the tightest reading moved from
1.765554 to 1.743322, a 1.3 percent change against a floor 39 percent below it.

**The separation floor never came close to binding** — the tightest seed sits 39
percent above it — so ruling 3's stop-and-report did not fire.

## 8. Every re-record, with provenance and attribution

**The attribution check is one experiment covering all three, and it is stronger
than a file revert.** Setting `_VALUE_SPR_FLOOR` to 1.0 makes the ramp return
exactly 1.0 at every stack depth, and multiplying by exactly 1.0 is the identity
in IEEE-754 — so that setting is the pre-S3-T3 engine bit for bit, with every
other edit on this branch left in place. Under it, each quantity below recomputes
to its OLD value; restoring 0.88 reproduces the NEW one. **No tolerance was
widened anywhere and no band edge was loosened.**

| fixture | file | old → new | why it moved |
|---|---|---|---|
| `_GOLDEN_STATS_N200` | `test_personas_postflop.py` | 4 of 6 rows move | n=200 stream-displacement tripwire |
| `_PRE_M3_FIRES` | `test_limper_coverage_belt.py` | all nine pairs move | production `bot_decision`; different actions displace the shared stream |
| coverage baseline | `tests/data/coverage_baseline.json` | total 1239→1210, graded 337→343 | same displacement, different sweep |
| went-to-showdown ceilings | `test_personas_postflop.py` `BANDS` | nit 0.67→0.65, fish 0.55→0.54 | the ratchet of §6, not a re-record |

**Two controls inside the re-records say the cause is this lever and nothing
else.** In `_GOLDEN_STATS_N200` the maniac's and the passive fish's rows are
BYTE-IDENTICAL while the other four move — their n=200 samples reach no unopened
made-value BET below `spr_commit`, so a lever confined to that cell cannot touch
them, and a lever that touched them would be out of its scope. And
`HEAD_VECTORS` in `backend/tests/test_price_tail.py` **did not move**, which the
design seed named as the specific test of whether the lever has leaked onto the
bluff path: its probes run at a stack-to-pot ratio of 10.0 on air and ace-high
fixtures, and both conditions independently keep it out of the lever's reach.
The four export digests in `backend/tests/test_buyin_spread.py` also did not
move, for the reason that fixture's own comments already record for a previous
ticket: at 25 hands and seed 777 the stream reaches no changed cell.

### The graded-coverage re-record, against the immutable snapshot

| tip | total decision points | graded | graded share |
|---|---|---|---|
| `coverage_baseline.persona-realism-start.json` (immutable) | 1233 | 349 | 28.31% |
| before this ticket (`4f653ef`) | 1239 | 337 | 27.20% |
| **after this ticket** | 1210 | **343** | **28.35%** |

**Graded coverage rose by 6 decision points and its SHARE is at the immutable
snapshot for the first time in this chain** — but the share moved partly because
the total fell by 29, so this ticket does not claim to have closed the level.
The absolute graded count is still 6 short of the snapshot's 349. The item that
owns the level is `T-cover`, whose measured root cause is the heads-up
single-raised-pot gate in `grade_map_postflop.py`, and it is blocked behind the
flywheel's phase-3 verdict — nothing here pre-empts it.

## 9. The contract §3 amendment

Amendment **A8**, dated 2026-08-22 and citing this ticket, sits inside §3 after
the bluff-share formula. It records four things, in this order of importance:

1. **The bluff-share formula prices only one side.** Until this ticket the engine
   had no lever at all that made value betting respond to bet size or stack
   depth; the only stack response on the value side was the commit block's single
   flat step on overpairs and better.
2. **The withdrawn repricing cannot be offset from the value side, and this
   lever does not change that** — about 25 percent of capped-node value betting
   would have to go, against roughly 10 percent of available motion, and that 10
   already includes deleting the commit boost outright.
3. **The formula is a property of a betting RANGE, not of a decision.** A
   per-node acceptance criterion of that shape is unsatisfiable by construction
   and must be rejected at review; a pooled one must be measured across seeds or
   paired.
4. **Most of the capped-versus-uncapped gap is arrival, not policy** — §3.3's
   numbers, so a future reader does not mistake the residual for an unfixed
   defect.

The amendment is confined to §3, as the ticket scopes it. It deliberately does
NOT add a row to §4's lever table: the ticket authorizes a §3 amendment only, and
the code comments cite §3 A8 rather than inventing a §4 row that no ratification
covers.

## 10. Acceptance criteria

| # | criterion | verdict |
|---|---|---|
| 1 | pooled capped-node composition moves toward the uncapped norm, in the pre-registered direction, pooled or paired — never one seed | **PASS on direction, with the magnitude reported as the headline finding.** Capped bluff share 0.0771 → 0.0781; ratio to uncapped 0.5863 → 0.5933; 3 of 3 seeds, paired at 222,792 unopened nodes. §3.3 states plainly that this is under 2 percent of a 5.45pp gap and why the rest is unreachable from the merit layer. |
| 2 | LAG went-to-showdown ceiling watched explicitly | **PASS** — 0.5769 → 0.5787 against 0.59, 1.13 points of headroom. Ceiling unchanged; §4. |
| 3 | five-seed de-robotization gate green | **PASS** — 5/5, tightest 1.743322 against 1.254429; §7. |
| 4 | byte-identity preserved wherever the stack does not bind | **PASS, and measured rather than argued** — 266,776 probe nodes at or above `spr_commit` with a maximum absolute probability delta of exactly 0.0, plus a per-persona test at each pack's own threshold. |
| 5 | contract §3 amendment lands in the same pull request | **PASS** — amendment A8; §9. |
| — | done-condition: a targeted test showing the multiplier firing shallow and not deep | **PASS** — `test_s3t3_made_value_bet_is_damped_shallow_and_bit_identical_deep`, which asserts the EXACT damped probability from a closed form, not an inequality. |

## 11. Checks

| command | result |
|---|---|
| `./scripts/verify.sh` | **BACKEND VERIFY OK** (2191 passed, 2 skipped — the two skips are the S6 detection probe, which needs a local artifact and is unrelated) |
| `cd backend && ruff check .` | clean |
| `python -m tools.derobo_gate --check --all-seeds` | GATE PASS (5/5) |
| `pytest -k "persona_postflop_bands or wtsd_ordering or spr"` | green |
| full backend suite | green |

## 12. What a reviewer should press on

- **The headline is a smallness, and it should be checked rather than taken.**
  §3.3 claims the capped-versus-uncapped gap is mostly arrival. The evidence is
  that the paired per-node policy delta is 0.0010 against a 0.0545 gap; the probe
  is 250 lines and the claim is falsifiable by running it.
- **The two showdown instruments disagree about the SIGN of this change.** §4
  reports both and argues neither is resolvable at these samples. A reviewer who
  thinks the harness's four falls are real should say what would distinguish them
  from displacement.
- **The floor of 0.88 was NOT tuned to the measurement.** It is the design seed,
  carried unchanged. The pre-registration registered only the weakening path
  (raise the floor if a guard fires); choosing a STRONGER floor after seeing that
  the effect was small would have been fitting to the result, and was declined.
  A reviewer may reasonably argue the opposite — that a 0.10pp movement does not
  earn its blast radius — and that argument is available on this evidence.
- **The BET-only scope rests on a measurement, not on precedent alone.** §1 gives
  it: every facing cell moves by exactly 0.0. If a reviewer believes capped RAISE
  nodes carry the defect, the probe already reports that population.
- **Two ceilings were tightened and none loosened**, but the ratchet also means
  S3-T4 inherits a nit ceiling of 0.65 and a fish ceiling of 0.54. That is the
  regime working as designed; it is worth knowing before the next ticket starts.
