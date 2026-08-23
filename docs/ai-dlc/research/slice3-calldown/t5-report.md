# Report — S3-T5, the late-street bet lever

**Bottom line.** The lever works on the thing it was built to move and barely
moves the thing the ticket gated on. Hands that check all the way down to a
showdown fall for all three tuned personas — the TAG by 3.0 points, the nit by
0.7, the LAG by 0.7, measured over 12,000 hands — while went-to-showdown falls
by an amount only the nit's exceeds this instrument's noise. The 50,000-hand
export agrees on direction for all six personas and moves the pool 53.4% →
53.2%. Every hard band is green, all five ordering legs hold, the five-seed
de-robotization gate passes 5 of 5 with more separation than before, and the
interim ceiling ratchet tightens three ceilings. Nothing here is a
stop-and-report, and one acceptance criterion is not met: went-to-showdown does
not measurably fall for the TAG or the LAG.

Ticket: S3-T5, the fifth ticket of improvement slice 3 (the calling-and-showdown
slice of the bot-realism flywheel), admitted by owner ruling on 2026-08-22.
Spec: `../../specs/flywheel-slice3-t5-checkdown.md`. Pre-registration and the
registered floors: `t5-preregistration.md`. Built at `72322d0`.

## 1. What shipped

One pack field, `late_street_bet`, in `[0, 1]` and absent by default. At an
unopened turn or river, on the non-bluff BET leg only, it multiplies the
aggressive candidate's merit by `1 + late_street_bet * _LATE_STREET_GAIN[street]`
with gains of 0.60 on the turn and 1.00 on the river. Values: **nit 0.5, TAG 1.0,
LAG 1.0**; the maniac, the calling station and the passive fish do not author it
and are byte-identical to their pre-ticket selves.

The gains come from a scan of four candidate pairs on the nit at 12,000 hands
(§4.1). The dials come from the per-persona sweep (§4.2). The nit's 0.5 is the
one value that is not simply the deepest admissible dial, and §4.2 says why.

## 2. Did it work

### The gate, went-to-showdown

Combined roster, band harness, pinned seed 20260710, all three dials in at once.

| persona | 4,000 hands (the sample CI asserts at) | 12,000 hands | one standard deviation at 4,000 |
|---|---|---|---|
| nit | 0.6173 → 0.5894 (**−2.79pp**) | 0.6144 → 0.5775 (**−3.69pp**) | 1.57pp |
| tag | 0.5528 → 0.5709 (+1.81pp) | 0.5697 → 0.5625 (−0.71pp) | 1.22pp |
| lag | 0.5769 → 0.5704 (−0.65pp) | 0.5683 → 0.5651 (−0.32pp) | 1.00pp |
| maniac | 0.5945 → 0.5848 | 0.5954 → 0.5908 | 0.78pp |
| calling_station | 0.7010 → 0.7055 | 0.7020 → 0.7005 | 0.62pp |
| passive_fish | 0.5204 → 0.5166 | 0.5108 → 0.5112 | 0.77pp |

**Only the nit's movement is bigger than the noise, and the TAG's changes sign
between the two sample sizes.** That is the honest reading and the ticket does
not dress it up: the gate is met for the nit and is not established for the TAG
or the LAG.

### The 50,000-hand export, the second instrument

Ratified nine-seat lineup, seed 20260817, showdowns divided by flops seen.

| persona | before | after | change | flops seen |
|---|---|---|---|---|
| nit | 0.5788 | 0.5716 | −0.72pp | 3,485 |
| tag | 0.5003 | 0.4932 | −0.71pp | 20,919 |
| lag | 0.5107 | 0.5084 | −0.23pp | 9,711 |
| maniac | 0.5263 | 0.5261 | −0.02pp | 18,329 |
| calling_station | 0.6635 | 0.6622 | −0.13pp | 22,158 |
| passive_fish | 0.4763 | 0.4748 | −0.15pp | 33,282 |
| **pooled** | **0.5343** | **0.5319** | **−0.24pp** | 107,884 |

All six move down, which is worth noting because the two instruments have
disagreed in sign on earlier tickets of this slice. The falls are small, and at
these sample sizes the TAG's −0.71pp is about two standard errors while the
LAG's and the maniac's are inside one.

### The diagnostic the lever actually moves

Share of showdown hands in which NO seat wagered on any postflop street — a
hand genuinely checked down. Combined roster, 12,000 hands.

| persona | before | after | change |
|---|---|---|---|
| tag | 0.2044 | 0.1745 | **−3.00pp** |
| lag | 0.1448 | 0.1377 | −0.71pp |
| nit | 0.3073 | 0.3005 | −0.68pp |
| maniac | 0.1657 | 0.1516 | −1.41pp |
| calling_station | 0.1734 | 0.1602 | −1.33pp |
| passive_fish | 0.2333 | 0.2300 | −0.33pp |

The three untouched personas move too, because a check-down needs every seat to
check and three of the nine seats now bet more often.

**Why showdown frequency does not follow this point for point.** A bet that gets
called produces a showdown exactly as a check-down does; the hand simply has
money in it now. The lever converts check-downs into bet-and-called showdowns
and only removes a showdown when the bet takes the pot down. Both outcomes are
improvements in how the table reads; only one of them shows up in
went-to-showdown.

### The metric the ticket was written against

Share of showdown hands in which the persona itself never faced a wager,
12,000 hands: nit 0.5133 → 0.4974 (−1.59pp, clears its registered floor of
0.3pp), lag 0.4261 → 0.4054 (−2.07pp, direction only was registered), **tag
0.4562 → 0.4704 (+1.42pp, a rise)**.

The TAG's rise is the shortfall the pre-registration predicted and explained
before the pack values moved: this metric cannot fall when the bot is the one
putting the money in, because the bot still faced no wager. It is recorded here
rather than argued away, and the owner's shortfall rule was applied — the
admissible value ships and the shortfall is written down.

## 3. Aggression factor and fold-to-continuation-bet

All HARD bands green at the 4,000-hand sample the test asserts at.

| persona | aggression factor before → after | band | fold-to-c-bet before → after | band |
|---|---|---|---|---|
| nit | 1.461 → 1.528 | (0.6, 2.4) | 0.435 → 0.514 | (0.10, 0.90) |
| tag | 2.383 → 2.710 | (1.4, 3.6) | 0.326 → 0.366 | (0.0, 0.55) |
| lag | 2.629 → 2.778 | (1.5, 4.5) | 0.319 → 0.357 | (0.12, 0.64) |
| maniac | 3.147 → 3.212 | (2.4, 5.1) | 0.326 → 0.328 | (0.0, 0.61) |
| calling_station | 0.318 → 0.312 | (0.0, 1.056) | 0.176 → 0.164 | (0.0, 0.424) |
| passive_fish | 0.912 → 0.899 | (0.0, 1.560) | 0.446 → 0.449 | (0.0, 0.549) |

Fold-to-continuation-bet rises for the three tuned personas even though the
lever never touches a facing decision. The reason is the population it is
measured over: a persona that bets more late reaches the flop-continuation-bet
node with a different distribution of hands and opponents.

### Ordering legs, all five intact

Measured at 4,000 hands: `station > tag` 0.7055 > 0.5709; `station > lag`
0.7055 > 0.5704; `maniac < station` 0.5848 < 0.7055; `fish < tag`
0.5166 < 0.5709; `station − fish` 0.1889 > 0.10. No transition-scoped leg had
to be moved, so ruling 2's one-move allowance is untouched.

### Ceiling ratchet

Re-derived on the same harness, seed and 4,000-hand sample as the four ratchets
before it. Installed: nit 0.67 → **0.64**, maniac 0.62 → **0.61**, passive_fish
0.55 → **0.54**; tag, lag and calling_station capped by their incumbents at
0.59, 0.59 and 0.72. No measurement crosses its own ceiling — the closest is
the calling station at 0.7055 against 0.72 — so no stop-and-report fires. The
arithmetic is in `test_persona_postflop_bands`' docstring.

## 4. The sweep

### 4.1 The gains

Nit only, all other packs unedited, dial fixed at 1.0, 12,000 hands.

| gains (turn, river) | aggression factor | went to showdown | never faced a wager |
|---|---|---|---|
| — (baseline) | 1.514 | 0.6144 | 0.5133 |
| (0.60, 1.00) | 1.562 | **0.5854** | **0.4983** |
| (1.50, 2.50) | 1.745 | 0.5893 | 0.5052 |
| (2.00, 3.50) | 1.833 | 0.5894 | 0.5117 |
| (3.00, 5.00) | 1.959 | 0.5970 | 0.5076 |

**Bigger gains buy nothing and cost aggression factor.** The smallest pair
gives the largest fall on both statistics; beyond it the effect saturates and
then reverses, while the aggression factor climbs steadily toward the band. So
the shipped pair is the smallest one tested, (0.60, 1.00).

### 4.2 The dials

One persona at a time, the other five packs unedited, gains (0.60, 1.00).
At 4,000 hands across the whole dial ladder, then at 12,000 hands at the two
dials the choice came down to.

| persona | dial | aggression factor | went to showdown | never faced a wager | checked down |
|---|---|---|---|---|---|
| nit | — | 1.514 | 0.6144 | 0.5133 | 0.3073 |
| nit | 0.5 | 1.537 | 0.5862 | 0.4941 | 0.2936 |
| nit | 1.0 | 1.562 | 0.5854 | 0.4983 | 0.2963 |
| tag | — | 2.410 | 0.5697 | 0.4562 | 0.2044 |
| tag | 0.5 | 2.655 | 0.5720 | 0.4744 | 0.1870 |
| tag | 1.0 | 2.720 | 0.5527 | 0.4807 | 0.1855 |
| lag | — | 2.670 | 0.5683 | 0.4261 | 0.1448 |
| lag | 0.5 | 2.692 | 0.5663 | 0.4170 | 0.1366 |
| lag | 1.0 | 2.743 | 0.5550 | 0.3994 | — |

**The nit ships 0.5 because its response saturates there.** The two dials are
indistinguishable on both statistics — 0.5862 against 0.5854 on showdown
frequency — so the deeper dial would buy aggression factor and a flatter
per-bucket betting spread and no showdown reduction. The TAG and the LAG do not
saturate: 0.5 leaves both flat and 1.0 moves both, so both ship at 1.0.

The 4,000-hand ladder (all four dials, both candidate gain pairs, three
personas) is in the run log and adds nothing the two rows above do not; at that
sample every difference between adjacent dials is inside one standard error.

## 5. The tell check

Exact bet frequency at an unopened node, by strength bucket, on the fixed probe
board — the diagnostic the spec asked for so a reviewer can see whether the
policy narrowed into a uniform stab rate. Columns are air, middle pair, top
pair, overpair, two pair plus, monster.

| persona | street | before | after |
|---|---|---|---|
| nit | turn | .065 .162 .423 .583 .643 .773 | .083 .201 .488 .645 .701 .816 |
| nit | river | .014 .000 .423 .583 .643 .773 | .014 .000 .524 .677 .730 .836 |
| tag | turn | .218 .436 .746 .849 .878 .932 | .308 .552 .824 .900 .920 .956 |
| tag | river | .074 .000 .746 .849 .878 .932 | .074 .000 .854 .918 .935 .965 |
| lag | turn | .270 .507 .796 .882 .906 .948 | .372 .622 .862 .923 .939 .967 |
| lag | river | .118 .000 .796 .882 .906 .948 | .118 .000 .887 .937 .951 .973 |

**No leg is flattened, and the ordering is exactly preserved.** The lever
multiplies odds by one constant, so in log-odds every bucket it touches keeps
its previous separation to the last decimal — checked directly: the TAG's turn
odds ratio is 1.600 at air and 1.601 at monster against a designed 1.600.

Two effects a reviewer should still look at. On the **river the policy becomes
more polarized, not less**: the bluff cell is untouched by design, so pure air
stays at .074 for the TAG while its value bets rise. On the **turn, the
probability-scale gap between thin value and a monster narrows** — the TAG's
top pair goes from 80% of its monster's bet rate to 86% — which is arithmetic
saturation at the top of the scale rather than a policy change, but it is real
in the numbers a judge would see. The absolute spread is still wide (the TAG
bets a monster .956, middle pair .552, air .308).

## 6. Checks

| command | result |
|---|---|
| `./scripts/verify.sh` | **BACKEND VERIFY OK** (2191 passed, 2 skipped, 6 xfailed) |
| `cd backend && ruff check .` | clean |
| `python -m tools.derobo_gate --check --all-seeds` | **GATE PASS 5/5** |
| `pytest -k "persona_postflop_bands or wtsd_ordering or late_street"` | 10 passed |

### The five-seed gate, with the separation numbers

| seed | minimum pairwise distance | required | pre-ticket reading |
|---|---|---|---|
| 601 | 2.087749 | 1.254429 | 1.853360 |
| 602 | 1.909912 | 1.254429 | 1.792393 |
| 603 | 1.914639 | 1.254429 | 1.765554 |
| 604 | 1.988509 | 1.254429 | 2.008972 |
| 605 | 1.818840 | 1.254429 | 1.958660 |

Label preservation is 6 of 6 on every seed and the determinism guard passes on
every seed. Separation rises on three seeds and falls on two, and every reading
clears the floor by at least 45%. **The separation floor did not bind, so
ruling 3's stop-and-report does not fire.**

**On the LAG–TAG pair, which the spec asks to be reported: the gate does not
name the pair that sets the minimum**, and no committed tool exposes it — the
constraint rule returns the minimum over all fifteen pairs and nothing else.
What the gate does expose is each candidate persona's distance to every baseline
centroid, at seed 601: the candidate LAG sits 1.194 from the baseline LAG and
2.036 from the baseline TAG; the candidate TAG sits 0.997 from the baseline TAG
and 2.001 from the baseline LAG. Both are labelled correctly and each is about
twice as far from the other archetype as from its own, so the axis the slice
spec warned about is not under pressure at this tip. Naming the binding pair
would need a probe that recomputes the candidate z-vectors, which is filed
rather than done here.

## 7. Acceptance criteria, verdict by verdict

| # | criterion | verdict |
|---|---|---|
| 1 | went-to-showdown falls for nit, TAG, LAG | **PARTIAL.** PASS for the nit (−2.79pp at 4,000 hands, −3.69 at 12,000, against a 1.57pp standard deviation). NOT ESTABLISHED for the TAG and the LAG: both move less than the noise and the TAG changes sign between sample sizes. The 50,000-hand export has all six falling. The diagnostic half — never-faced-a-wager against the registered floors — is PASS for the nit (−1.59pp against 0.3pp) and a recorded SHORTFALL for the TAG (+1.42pp), which the pre-registration predicted and explained before the values moved. |
| 2 | all HARD bands green, ordering legs, ratchet re-applied | **PASS.** §3. Three ceilings tighten, three are capped by their incumbents, no stop-and-report. |
| 3 | byte-identity with packs unedited, three named targeted tests | **PASS.** The identity run is recorded at the lever's own commit: all six personas reproduce every statistic to the last digit with the field unauthored. The three tests are named as the spec required. |
| 4 | five-seed gate green, LAG–TAG reported | **PASS on the gate**, 5 of 5. The pair is reported as far as the committed tooling allows — see §6. |
| 5 | estimator parity unchanged plus a new unopened parity test | **PASS.** `test_estimator_prices_the_faced_bet` and the PR #199 bracket guard are untouched and green; the new test asserts estimator-versus-sampler equality at an unopened turn and river with the lever on, and asserts the lever-off distribution differs first so the equality is not vacuous. |
| 6 | 50,000-hand export reported | **PASS.** §2. |
| 7 | slice-spec amendment lands in the same pull request | **PASS.** The slice-3 spec carries a dated owner-ruling note and the slice-3 ticket file carries the S3-T5 entry. |

## 8. What a reviewer should push on

1. **Criterion 1 is not fully met and the ticket ships anyway.** The judgement
   is that the checked-down share is the statistic the mechanism moves, that it
   moves decisively for the TAG, and that the owner's shortfall rule covers the
   registered floor. A reviewer may reasonably hold that a gate is a gate.
2. **The nit's dial is the one value chosen on a judgement rather than a rule.**
   Its two candidate dials are statistically indistinguishable and 0.5 was
   preferred as the cheaper one. If a reviewer prefers the deepest admissible
   dial for consistency with the TAG and the LAG, the evidence does not
   contradict them.
3. **The turn saturation in §5.** Thin value and monsters converge slightly in
   probability space. It is not flattening in the policy, but it is what a judge
   sees.
4. **Four seeded fixtures were re-recorded.** Each carries provenance and the
   revert-to-prove-attribution check, and no tolerance was widened.
