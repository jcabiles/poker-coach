# Pre-registration — S3-T5, the late-street bet lever

**status: revision 2, 2026-08-22 — supersedes revision 1 of the same date, whose
sweeps were not paired and whose floors are therefore withdrawn. Written after
the repaired measurements and BEFORE any pack value was set; the pack values
land in the commit after this one.**

**Bottom line.** About a third of the nit's showdown hands, a fifth of the TAG's
and a seventh of the LAG's are checked all the way down — no seat wagers on any
postflop street — and the calling dial this slice has been tuning cannot reach
them, because a hand nobody bets at contains no calling decision. S3-T5 adds one
bounded pack lever that makes a bot more willing to bet an unopened turn or
river, on both the value and the bluff side so the resulting betting range is
not value-pure. This document fixes, in advance of any pack value: which
statistic is the target, how it is measured, what the lever's constants are and
how they were fitted, how much of a fall counts as success, and — new in this
revision — the rule that decides which personas get the lever at all.

## 0. What revision 1 got wrong

Three findings from the review of `c498088`, all folded in below.

**The sweeps were not paired, so the floors derived from them are withdrawn.**
The band harness draws its deals and the bots' actions from ONE
`random.Random`. The moment a bot checks where it used to bet, it consumes a
different number of draws, and every later hand of that run is a different hand.
A "before and after" on that harness is therefore two independent samples, not a
paired comparison, and differences of a point or two — which is what revision 1
registered floors against — are the size of the seed-to-seed spread. Measured:
the nit's went-to-showdown reads 0.6173, 0.5876, 0.6225, 0.5876 and 0.6019
across five seeds with NOTHING changed, a spread of 3.5 points, against the
2.8-point "effect" revision 1 reported from one seed.

**The lever was half a lever.** Raising the value side alone made the unopened
river bet value-pure: at a dial of 1.0 the TAG's naked air bet 7.4% of the time
while its top pair and better bet 85–97%. A judge reading that table learns "if
this bot bets the river it has top pair or better", which is a worse tell than
the passivity the ticket set out to fix. The bluff cell is now driven by the
same one pack dial through its own gains (§4).

**Two different statistics were being quoted as one.** "Never faced a wager"
(the persona met no wager) and "checked down" (NO seat wagered) differ by about
twenty points on the nit, and only the second is what the ticket's prose
describes. §1 fixes which is the target.

## 1. The instruments

**Primary target — `checked_down`.** The share of a persona's showdown hands in
which no seat wagered on any postflop street. This is what "the hand checked
through to a showdown" means, it is the population the calling dial cannot
reach, and it is what this lever acts on directly: a bot that bets no longer
produces a checked-down hand, whatever the opponent then does.

**Secondary, disclosed — `never_faced_wager`.** The share of showdown hands in
which the persona itself met no wager. It is the statistic revision 1 was
written against and the one the earlier tickets of this slice quoted, so it is
reported rather than dropped. It responds to this lever only indirectly: it
falls when somebody wagers AT the persona, which the persona's own bet can
cause by being raised, and which its own bet can also PRE-EMPT — a hand it now
bets and gets called on is a showdown it did not face a wager in, exactly as the
check-down it replaced was. Which of the two effects dominates is a per-persona
empirical question, and §5 registers no magnitude against it.

Both are DIRECTIONAL diagnostics under the theory contract. Neither is a gate.

**The gate — went-to-showdown**, one of the three statistics the contract marks
HARD-today, asserted at the harness's pinned seed and 4,000 hands.

**How each is measured.**

- **Policy** — how often a bot bets a given node — by
  `backend/tools/late_street_probe.py`: the hands are played once and each arm
  is read off the SAME node with a capture rng, so a difference is the lever and
  carries no sampling variance at all. Every composition and bluff-share figure
  below comes from it, at 4,000 hands × three seeds (601, 20260817, 20260818).
- **Arrival** — went-to-showdown, `checked_down`, `never_faced_wager` — by the
  band harness pooled over FIVE seeds (20260710, the pinned one, plus 20260711
  to 20260714) at 4,000 hands each, with a two-sample binomial standard error,
  because the two arms are independent runs and cannot be paired. The probe
  cannot measure these: turning the lever on changes which nodes exist, and no
  pairing can show that.

## 2. Baseline, before any pack value

Pooled over the five seeds, all six packs unauthored, at commit `9d4adc0`.

| persona | checked down | never faced a wager | went to showdown | aggression factor |
|---|---|---|---|---|
| nit | 31.69% | 51.51% | 0.6033 | 1.531 |
| tag | 19.77% | 46.91% | 0.5648 | 2.514 |
| lag | 14.46% | 40.67% | 0.5762 | 2.561 |

At the pinned seed alone the nit's checked-down share reads 31.33% and its
went-to-showdown 0.6173; the five-seed pool is the number to quote.

## 3. The value gains, and why the smallest candidate pair

Four candidate pairs, read on the same node population by the paired probe at a
dial of 1.0, with the bluff companion at its fitted value. Bet frequency is the
mean probability of betting an unopened node; bluff share is the fraction of
that betting contributed by the bluff cell.

| pair (turn, river) | nit turn bet freq | nit turn bluff share | tag turn bluff share | lag river bluff share |
|---|---|---|---|---|
| lever off | 0.2838 | 0.00945 | 0.05307 | 0.13064 |
| **(0.60, 1.00)** | 0.3419 | **0.00973** | **0.05658** | **0.15013** |
| (1.50, 2.50) | 0.3985 | 0.00832 | 0.05043 | 0.14680 |
| (2.00, 3.50) | 0.4221 | 0.00787 | 0.04832 | 0.14570 |
| (3.00, 5.00) | 0.4598 | 0.00723 | 0.04544 | 0.14483 |

**Only the smallest pair keeps every persona's bluff share at or above its
lever-off value.** Every larger pair drives the betting range MORE value-pure,
which is the defect the companion exists to prevent — the companion is fitted at
the shipped pair, and a bigger value gain outruns it. That is the reason the
pair is chosen, and it is a measured one rather than the "larger gains cost
aggression factor for no showdown reduction" argument revision 1 gave, which
rested on unpaired readings and is withdrawn as evidence (the aggression-factor
costs it reported — 1.56, 1.75, 1.83, 1.96 at dial 1.0 — are large relative to
their own error and still stand as a secondary reason).

**The turn-to-river ratio is DIRECTIONAL and was never swept.** Both gains keep
the river above the turn on the reasoning that the river is the last chance to
win without showing down. Nothing here tests that ordering against its reverse;
a scan of the ratio is filed, not done.

## 4. The bluff-side companion, fitted

The bluff cell is an exact-frequency cell — its two merits sum to one, so its
bet probability IS the mass the dial scales — while the value side scales an
odds ratio. The two therefore need different constants to move a range by the
same proportion, which is why they are two constants and not one.

**Fitting rule, fixed before the scan: the smallest gain at which no candidate
persona's realised unopened bluff share falls below its lever-off value at a
dial of 1.0, taken per street as the maximum over the three personas.** Scanned
over the real node population at 12,000 hands:

| street | nit binds at | tag binds at | lag binds at | **installed** |
|---|---|---|---|---|
| turn | 0.24 | ≤ 0.20 | ≤ 0.20 | **0.24** |
| river | 0.24 | ≤ 0.20 | ≤ 0.20 | **0.24** |

The nit binds both streets because its `bluff_freq` is 0.04 — bluffs are about
1% of its bets at these nodes, so it needs the largest proportional lift to hold
that share. A first pass at 7,500 hands read 0.20; the larger population moved
it one grid step and is what the constants are set from.

## 5. Which personas get the lever, and the registered floors

**The ship rule, fixed here before any pack value.** A persona's
`late_street_bet` is set ONLY if BOTH hold at the deepest aggression-admissible
dial: its went-to-showdown falls at the harness's pinned seed and 4,000 hands
(the gate's own sample), AND the five-seed pooled estimate agrees in sign.
Otherwise its field stays UNSET — the lever is simply off for that persona — and
the shortfall is recorded with the numbers. The gate is not a floor and the
owner's shortfall rule does not cover it; a persona that does not clear it does
not ship.

Measured at dial 1.0, which is aggression-admissible for all three (nit 1.581
against a band of (0.6, 2.4); tag 2.734 against (1.4, 3.6); lag 2.734 against
(1.5, 4.5)). **The arm below has all three dialled together** — the pooled
harness runner sets every persona it is asked about, and calling that a
"one persona at a time" sweep would be the same class of mislabelling this
revision exists to fix. The joint arm is the right one to read the ship rule
against anyway, because a joint configuration is what would ship:

| persona | pinned-seed went-to-showdown | pooled Δ (5 seeds) | verdict |
|---|---|---|---|
| nit | 0.6173 → 0.5865, **falls** | −0.31pp ± 0.97 | **SHIPS at 1.0** |
| lag | 0.5769 → 0.5638, **falls** | −2.20pp ± 0.64 | **SHIPS at 1.0** |
| tag | 0.5528 → 0.5603, **rises** | +0.06pp ± 0.78 | **DOES NOT SHIP** |

**AMENDED THE SAME DAY, BEFORE THE PACK VALUES WERE COMMITTED.** The rule has
to be applied to the configuration that actually ships, and applying it removed
the nit. Three configurations were measured, five seeds each:

| configuration | nit pooled Δ | tag pooled Δ | lag pooled Δ |
|---|---|---|---|
| all three dialled | −0.31pp ± 0.97 | +0.06pp ± 0.78 | −2.20pp ± 0.64 |
| nit + lag dialled | **+0.28pp ± 0.97** | — | −1.71pp ± 0.64 |
| lag alone (shipped) | — | — | **−1.80pp ± 0.64** |

**The nit's pooled sign is configuration-dependent and never distinguishable
from zero**, so it fails the second half of the rule the moment the TAG is
removed from the arm. Its checked-down fall shrinks with it, from 2.30pp to
1.20pp, and stops clearing one standard error. The nit therefore does NOT ship.
The LAG's effect is the same size in every configuration and clears in all of
them, so it does.

That the rule cost the ticket its motivating persona is not a reason to soften
it. The nit is the persona this lever was designed around, and the evidence
after repair says the lever does not move its showdown frequency either way.

**Registered floors**, on the primary diagnostic, for the persona that ships. Derivation rule, unchanged from revision 1 in form and repaired in
substance: the fall the shipped dial delivers in the five-seed pool, minus one
two-sample standard error.

| persona | quantity | measured fall | one standard error | registered floor |
|---|---|---|---|---|
| lag | checked down | 2.51pp | 0.58pp | **≥ 1.9pp** |
| lag | never faced a wager | 1.20pp | 0.84pp | **≥ 0.3pp** |
| ~~nit~~ | ~~checked down~~ | ~~2.30pp~~ | ~~1.18pp~~ | **withdrawn — does not ship** |

Both LAG floors are registered off the all-three arm, which is the arm that was
measured when they were written. The shipped configuration is the LAG alone, and
it delivers LESS: 1.42pp of checked-down and 0.59pp of never-faced-a-wager. That
is a **recorded shortfall against both floors** under the owner's rule of
2026-08-22 — the admissible value ships and the miss is written down. It is not
a surprise in hindsight and it is worth stating why: two of the three personas
that were dialled when the floor was set are no longer dialled, and a
checked-down hand needs EVERY seat to check, so removing two of the three
bettors from the table takes back part of the effect the third was credited
with. A floor registered on a configuration that does not ship is a defect in
the registration, and it is filed as one.

Shortfall rule, from the owner's answer of 2026-08-22, and it applies to these
floors and not to the gate: if the admissible dial cannot clear a floor, ship
the admissible value and record the shortfall.

## 6. What would falsify this before it ships

Any of these stops the ticket rather than being tuned around: a shipped
persona's aggression factor or fold-to-continuation-bet leaving its HARD band; a
went-to-showdown ordering leg weakening; the five-seed de-robotization gate's
separation floor binding; a shipped persona's realised unopened bluff share
falling below its lever-off value on the final packs; or the combined
configuration reversing the sign of a shipped persona's pinned-seed
went-to-showdown against the single-persona reading this section registered.
