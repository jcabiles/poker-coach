# Report — S3-T5, the late-street bet lever

**Bottom line.** One persona ships the lever and two do not. The LAG's
`late_street_bet` goes to 1.0, which lowers its went-to-showdown by 1.80
points and the share of its showdown hands that are checked all the way down by
1.42, both larger than the harness's noise. The nit and the TAG were dialled in
an earlier round of this ticket and are withdrawn: after the measurement method
was repaired, neither persona's showdown frequency moves in a direction the
evidence supports, and the ship rule registered before the pack values says a
persona that does not clear the gate does not get the lever. Every hard band is
green, no ceiling moves, all five ordering legs hold, the five-seed
de-robotization gate passes 5 of 5, and the unopened river bet is measurably
less value-pure than it was before this ticket rather than more.

Ticket: S3-T5, the fifth ticket of improvement slice 3 (the calling-and-showdown
slice of the bot-realism flywheel), admitted by owner ruling on 2026-08-22.
Spec: `../../specs/flywheel-slice3-t5-checkdown.md`. Pre-registration rev 2,
which fixes the method, the gains and the ship rule:  `t5-preregistration.md`.
Built across `2834b60`..`HEAD` on `feat/slice3-t5-late-street-bet`; the
lever-off tip that every "before" below is measured at is `9d4adc0`.

## 1. What the first round got wrong, and what fixed it

The build passed a refuter, then failed a triple review — the persona-realism
theory reviewer on composition, Codex Sol on measurement and on the gate. Three
findings, all folded in.

**The sweeps were not paired.** The band harness draws its deals and its bots'
actions from one generator, so the first decision that flips changes every later
hand. With NOTHING changed, the nit's went-to-showdown reads 0.6173, 0.5876,
0.6225, 0.5876 and 0.6019 across five seeds; the first round registered floors
against a 2.8-point "effect" measured inside that spread. Policy is now read by
a zero-variance paired probe (§5) and arrival is pooled over five seeds with a
two-sample standard error (§2).

**The lever was half a lever.** Raising the value side alone made the unopened
river bet value-pure. The bluff cell now rises through its own mass on the same
one pack dial, fitted so no persona's realised bluff share falls (§5).

**The gate was treated as a floor.** The first round shipped a persona whose
went-to-showdown had risen, on the owner's shortfall rule. That rule covers
registered floors, not the gate. The ship rule in §3 replaces it.

## 2. Did it work

Band harness, five seeds (20260710 — the pinned one — plus 20260711 to
20260714) at 4,000 hands each, lever-off against the shipped packs. The
two-sample standard error is in the last column; "SE" in the text means
multiples of it.

| persona | went to showdown | Δ | checked down | Δ | never faced a wager Δ | SE (WTSD) |
|---|---|---|---|---|---|---|
| **lag** | 0.5762 → 0.5583 | **−1.80pp (2.8 SE)** | 14.46% → 13.04% | **−1.42pp (2.4 SE)** | −0.59pp | 0.64pp |
| nit | 0.6033 → 0.6167 | +1.33pp (1.4 SE) | 31.69% → 31.78% | +0.09pp | +0.07pp | 0.97pp |
| tag | 0.5648 → 0.5777 | +1.30pp (1.7 SE) | 19.77% → 18.34% | −1.43pp (1.8 SE) | −0.27pp | 0.78pp |
| maniac | 0.5950 → 0.5945 | −0.05pp | 16.78% → 16.51% | −0.27pp | −0.47pp | 0.49pp |
| passive_fish | 0.5174 → 0.5163 | −0.11pp | 23.11% → 23.15% | +0.05pp | −0.52pp | 0.49pp |
| calling_station | 0.7072 → 0.7009 | −0.63pp (1.6 SE) | 18.06% → 17.55% | −0.52pp | −0.56pp | 0.39pp |

**Only the LAG's pack changed, and only the LAG's numbers move further than the
noise.** The other five rows are the same bots meeting a table with one more
bettor in it; the nit's and the TAG's +1.3 points are 1.4 and 1.7 standard
errors and are not read as effects here, which is the discipline the first round
lacked.

At the pinned seed alone — the sample the gate is asserted at — the LAG reads
0.5769 → 0.5639, a fall, so both halves of the ship rule hold for it.

**Against the registered floors, the LAG falls short and it is recorded.** The
floors (checked down ≥ 1.9pp, never faced a wager ≥ 0.3pp) were registered off
an arm with all three personas dialled, where the LAG delivered 2.51pp and
1.20pp. Shipping alone it delivers **1.42pp and 0.59pp** — the second clears,
the first misses by 0.5 points. Under the owner's rule of 2026-08-22 the
admissible value ships and the miss is written down. The mechanism is not
mysterious: a checked-down hand needs EVERY seat to check, so two of the three
bettors leaving the table takes back part of the effect the third was credited
with. A floor registered on a configuration that does not ship is a defect in
the registration and is filed as one in the slice ledger.

### The 50,000-hand export, the second instrument

Ratified nine-seat lineup, seed 20260817, showdowns divided by flops seen.

| persona | before | after | change | flops seen |
|---|---|---|---|---|
| lag | 0.5107 | 0.5088 | −0.19pp | 9,711 |
| nit | 0.5788 | 0.5712 | −0.76pp | 3,485 |
| tag | 0.5003 | 0.4988 | −0.15pp | 20,919 |
| maniac | 0.5263 | 0.5252 | −0.11pp | 18,329 |
| calling_station | 0.6635 | 0.6622 | −0.13pp | 22,158 |
| passive_fish | 0.4763 | 0.4779 | +0.16pp | 33,282 |
| **pooled** | **0.5343** | **0.5338** | **−0.05pp** | 107,884 |

Five of six fall and the pool is flat. Read the sizes rather than the signs:
one binomial standard error on the LAG at this sample is 0.51pp and on the
pooled row 0.15pp, so nothing here is separable from zero except possibly the
nit's −0.76pp at 0.84pp of error — and the nit's pack did not change. **The
export and the band harness agree that the roster-wide effect of this ticket is
small; they disagree about the LAG**, which the harness resolves at 2.8 standard
errors and the export cannot resolve at all, because the LAG occupies one seat
of the ratified nine and sees a third as many flops there as the TAG does. The
harness is the gating instrument for exactly this reason; the export is
diagnostic context.

## 3. Why the nit and the TAG do not ship

The ship rule, fixed in the pre-registration before any pack value: a persona
gets the lever only if its went-to-showdown falls at the pinned seed AND the
five-seed pooled estimate agrees in sign.

| configuration measured | nit pooled Δ | tag pooled Δ | lag pooled Δ |
|---|---|---|---|
| all three dialled | −0.31pp ± 0.97 | +0.06pp ± 0.78 | −2.20pp ± 0.64 |
| nit + lag dialled | +0.28pp ± 0.97 | — | −1.71pp ± 0.64 |
| lag alone (**shipped**) | +1.33pp ± 0.97 | +1.30pp ± 0.78 | −1.80pp ± 0.64 |

**The TAG fails on both halves in every configuration** — its pinned-seed
reading rises 0.75 points and its pooled estimate is +0.06 ± 0.78. **The nit's
pooled sign is configuration-dependent and never distinguishable from zero**:
−0.31 with the TAG in the arm, +0.28 without it. It passed the rule on the
first arm measured and failed it on the arm that would actually have shipped,
so it does not ship.

This costs the ticket its motivating persona — the nit has the worst
checked-down share on the roster at 31.7% — and that is the honest outcome
rather than a reason to soften the rule. What the ticket can say about the nit
is narrower and still worth having: at these gains the lever raises its
unopened late-street betting exactly as designed (§5), and that policy change
does not reach its showdown frequency.

## 4. Bands, ordering and the ratchet

All HARD bands green at the 4,000-hand pinned sample the test asserts at.

| persona | aggression factor (pooled, off → on) | band | fold-to-c-bet | band |
|---|---|---|---|---|
| lag | 2.561 → 2.725 | (1.5, 4.5) | 0.306 → 0.334 | (0.12, 0.64) |
| nit | 1.531 → 1.524 | (0.6, 2.4) | 0.419 → 0.442 | (0.10, 0.90) |
| tag | 2.514 → 2.550 | (1.4, 3.6) | 0.355 → 0.363 | (0.0, 0.55) |
| maniac | 3.094 → 3.110 | (2.4, 5.1) | 0.292 → 0.300 | (0.0, 0.61) |
| passive_fish | 0.918 → 0.901 | (0.0, 1.560) | 0.453 → 0.449 | (0.0, 0.549) |
| calling_station | 0.314 → 0.314 | (0.0, 1.056) | 0.165 → 0.179 | (0.0, 0.424) |

**Ordering legs, all five intact** at the pinned seed: `station > tag`
0.7022 > 0.5732; `station > lag` 0.7022 > 0.5639; `maniac < station`
0.5993 < 0.7022; `fish < tag` 0.5262 < 0.5732; `station − fish` 0.1761 > 0.10.
No transition-scoped leg had to move, so ruling 2's one-move allowance is
untouched.

**Ceiling ratchet: no ceiling moves.** Every persona's re-derived
measurement-plus-three-standard-deviations value sits at or above the ceiling an
earlier slice earned, so all six are capped by their incumbents. No measurement
crosses its own ceiling — the closest is the passive fish at 0.5262 against
0.55. The arithmetic is in `test_persona_postflop_bands`' docstring.

## 5. Composition: is the betting range still a mix?

This is the finding that reshaped the lever, so it is reported at length. All
figures come from `backend/tools/late_street_probe.py` at 12,000 hands over
three seeds: the hands are played once and both arms are read off the SAME node,
so they carry **zero conditional action-sampling variance** — the two arms differ
only by the lever, never by which cards fell or which action was drawn. That is
not the same as no error. **The 1,257 turn and 879 river nodes are still a finite
sample of nodes**, so the LEVELS below carry the usual sampling error of a node
population; what is exact is the OFF-versus-ON comparison at each node.

### The headline

| persona | street | bet frequency off → on | realised bluff share off → on |
|---|---|---|---|
| lag | turn | 0.4783 → 0.5500 | 0.0909 → **0.0980** |
| lag | river | 0.3626 → 0.3914 | 0.1306 → **0.1501** |
| nit | turn | 0.2838 → 0.3419 | 0.0095 → 0.0097 |
| nit | river | 0.2645 → 0.3180 | 0.0145 → 0.0150 |
| tag | turn | 0.4104 → 0.4774 | 0.0531 → 0.0566 |
| tag | river | 0.3182 → 0.3471 | 0.0901 → 0.1025 |

**Per-seed spread, so the levels are not read as more precise than they are.**
Each seed is its own 4,000-hand node population; the lever's effect is read
within each.

| seed | turn share off → on | river share off → on |
|---|---|---|
| 601 | 0.1104 → 0.1183 | 0.1512 → 0.1724 |
| 20260817 | 0.0858 → 0.0933 | 0.1110 → 0.1286 |
| 20260818 | 0.0770 → 0.0828 | 0.1292 → 0.1482 |
| **pooled** | **0.0909 → 0.0980** | **0.1306 → 0.1501** |

The LEVEL swings by three points across seeds on the turn — the pooled 0.0909
is not a precise quantity — while the RISE is the same sign and roughly the same
size in all three, which is what the paired reading buys.

**The betting range gets MORE bluff-weighted, not less** — the opposite of the
first round, where the same table read 0.074 of naked air against 0.85 to 0.97
of top pair and better. The bluff gains are fitted to make that so: 0.24 on both
streets, the smallest at which no persona's share falls, with the nit binding
because its `bluff_freq` of 0.04 leaves it the least share to hold.

### By hand class and position — the LAG, the persona that ships

Mean probability of betting an unopened node, lever-off → lever-on. Naked air
here is the true bluff cell (air or ace-high with NO draw); a gutshot appears in
its own draw row, which the first round's table did not do.

| hand class | turn IP | turn OOP | river IP | river OOP |
|---|---|---|---|---|
| naked air | — | .155 → .192 | .194 → .240 | .125 → .155 |
| naked ace-high | .232 → .288 | .154 → .191 | .148 → .183 | .104 → .130 |
| air + strong draw | — | .481 → .592 | n/a | n/a |
| air + weak draw | — | .240 → .335 | n/a | n/a |
| middle pair | .417 → .531 | .336 → .446 | .000 → .000 | .000 → .000 |
| top pair | — | .722 → .805 | .794 → .885 | .713 → .831 |
| two pair plus | — | .912 → .943 | — | .934 → .966 |
| monster | — | .957 → .972 | .975 → .987 | .956 → .977 |

(Cells with fewer than 30 observed nodes are omitted rather than reported.)

**Read the RATIOS, which is where the tell would be.** On the river the naked
air cell rises by a factor of 1.24 and the monster by 1.02, so the gap between
what a bluff and a nut hand do NARROWS — the bot becomes harder to read, not
easier. The river's middle pair stays at zero throughout: that is the
pre-existing W1-a floor, untouched by this lever and visible here because the
table now shows it.

**THREE VALUE CELLS NOW CROSS THE MANIAC, and that is recorded rather than
buried.** Comparing each persona as it ships — the LAG with the lever on, the
maniac with it unauthored — the LAG bets three cells MORE often than the
roster's most aggressive persona: river top pair in position 0.885 against
0.843, turn middle pair in position 0.531 against 0.529, and river monster in
position 0.987 against 0.985. Two of the three are hairline and the third
(river top pair) is four points. No aggression-factor band or ordering leg is
affected — those are aggregates and all six are green — and the maniac remains
far ahead where the archetype is defined, at naked air on the turn (0.350
against the LAG's 0.192) and on the river (0.241 against 0.155). **What has
happened is that the LAG's late-street VALUE betting has caught the maniac while
its BLUFFING has not**, which is a partial-ordering wrinkle the aggregates
cannot see. It is not a defect the ticket's own boundary can fix — the maniac
does not author this field and giving it one is a pack change outside the ship
rule — and it is the second reason (after Filed 13) that the unopened
late-street node needs a contract row with a cross-persona ordering obligation
in it.

**What a reviewer should still push on:** the turn's strongest cells are
saturating (monster .957 → .972), so at a deeper dial the value side would
compress against its ceiling while the bluff side kept climbing. Nothing in the
shipped configuration is near that, but the fit that holds the share is a
property of these gains at this dial, not a guarantee at larger ones — which is
exactly why §3 of the pre-registration rejects the larger value-gain pairs.

## 6. Checks

| command | result |
|---|---|
| `./scripts/verify.sh` | **BACKEND VERIFY OK** — 2191 passed, 2 skipped, 6 xfailed |
| `cd backend && ruff check .` | clean |
| `python -m tools.derobo_gate --check --all-seeds` | **GATE PASS 5/5** (run at `d646882`; the commits after it change comments, documentation and one test only — `git diff` on the engine and the pack models is empty of code) |
| `pytest -k "persona_postflop_bands or wtsd_ordering or late_street"` | 12 passed |

### The five-seed gate, with the separation numbers

| seed | minimum pairwise distance | required | pre-ticket reading |
|---|---|---|---|
| 601 | 2.190574 | 1.254429 | 1.853360 |
| 602 | 1.921416 | 1.254429 | 1.792393 |
| 603 | 1.887987 | 1.254429 | 1.765554 |
| 604 | 1.821617 | 1.254429 | 2.008972 |
| 605 | 2.180375 | 1.254429 | 1.958660 |

Label preservation is 6 of 6 on every seed and the determinism guard passes on
every seed. Separation rises on three seeds and falls on two, and every reading
clears the floor by at least 45%. **The separation floor did not bind, so
ruling 3's stop-and-report does not fire.**

**The LAG–TAG pair, which the slice spec flags as the tightest axis.** The gate
does not name the pair that sets the minimum — the constraint rule returns the
minimum over all fifteen pairs and nothing else, and no committed tool exposes
more. What it does expose is each candidate persona's distance to every baseline
centroid. At seed 601: the candidate LAG sits **0.754** from the baseline LAG
and **1.963** from the baseline TAG; the candidate TAG sits **0.939** from the
baseline TAG and **2.098** from the baseline LAG. Both are labelled correctly
and each is more than twice as far from the other archetype as from its own, so
that axis is not under pressure at this tip. The LAG also sits CLOSER to its own
frozen pre-fix centroid than it did before this ticket, which is the direction
this work wants. Naming the pair that actually sets the minimum would need a
probe that recomputes the candidate z-vectors; it is filed rather than done.

## 7. Acceptance criteria, verdict by verdict

| # | criterion | verdict |
|---|---|---|
| 1 | went-to-showdown falls for nit, TAG, LAG | **PARTIAL, and the shortfall is in the ship list rather than in the numbers.** It falls for the LAG on both instruments and by 2.8 standard errors on the pooled harness estimate. It does not fall for the nit or the TAG, so under the pre-registered ship rule neither gets the lever and both are byte-identical to their pre-ticket selves. The diagnostic half: the LAG's checked-down fall of 1.42pp MISSES its registered floor of 1.9pp, recorded under the owner's shortfall rule, with the reason measured in §2. |
| 2 | all HARD bands green, ordering legs, ratchet re-applied | **PASS.** §4. No ceiling moves and no stop-and-report fires. |
| 3 | byte-identity with packs unedited, three named targeted tests | **PASS.** Commit `9d4adc0` is a whole-suite-green tip with the lever in the engine and no pack authoring it. The three tests keep their names and now cover both sides of the lever; the identity test was rewritten so it reads the shipped packs rather than hard-coded dials, and so it cannot go vacuous when the roster changes. |
| 4 | five-seed gate green, LAG–TAG reported | **PASS on the gate**, 5 of 5, with more separation than the pre-ticket reading on three seeds of five and the floor cleared by at least 45% on all of them. The LAG–TAG pair is reported as far as the committed tooling allows — see §6. |
| 5 | estimator parity unchanged plus a new unopened parity test | **PASS.** The PR #199 bracket guard and `test_estimator_prices_the_faced_bet` are untouched and green; the new test asserts estimator-versus-sampler equality at an unopened turn and river with the lever on, and builds its lever-off side explicitly so it cannot go vacuous when a pack authors the field. |
| 6 | 50,000-hand export reported | **PASS.** §2. |
| 7 | slice-spec amendment lands in the same pull request | **PASS.** The slice-3 spec carries the dated owner-ruling note, the slice-3 ticket file carries the S3-T5 entry and its own amendment note, and this ticket's spec marks the two paragraphs the rework superseded. |

## 8. What a reviewer should scrutinise

1. **One persona ships out of three proposed.** The ticket's value is a real but
   narrow result plus two measured negatives. Whether that clears the bar for
   merging is a judgement the report does not make for the reviewer.
2. **The registered floor was set on a configuration that did not ship**, and
   the LAG misses it by 0.5 points as a result. The fix for next time is to
   register floors per shipped configuration, filed in the ledger.
3. **The nit's result is a null, not a refutation.** The lever demonstrably
   changes its policy (§5) and demonstrably does not change its showdown
   frequency. Whether that is the lever's fault or the statistic's is open; §2 of
   the ledger's Filed 12 argues the latter is at least partly true.
4. **Three seeded fixtures were re-recorded**, each with provenance and a
   revert-to-prove-attribution check run in both directions. The coverage
   baseline did NOT move and was left alone.
