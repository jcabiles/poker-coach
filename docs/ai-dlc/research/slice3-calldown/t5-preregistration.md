# Pre-registration — S3-T5, the late-street bet lever

**Bottom line.** Half of the nit's showdown hands and about 45% of the TAG's
still reach showdown without anyone ever wagering a chip at them, measured on a
committed instrument for the first time. S3-T5 (the fifth ticket of improvement
slice 3, the calling-and-showdown slice of the bot-realism flywheel) adds one
bounded pack lever, `late_street_bet`, that makes a bot more willing to bet an
unopened turn or river. This document records the before-state and the sweep
that fixes the lever's size, and it is written in two passes: the baseline table
below landed with the instrument, before any engine or pack change; the
registered floors in §3 landed after the sweep and before any pack value moved.

## 1. The instrument

`_persona_stats` in `backend/tests/test_personas_postflop.py` now returns a
seventh value, `never_faced_wager`: the share of a persona's showdown hands in
which that persona never met a wager on any postflop street. It counts a hand as
having met a wager when the persona took a postflop FOLD, CALL or RAISE, which
is the same event the earlier ticket's prose figures counted
(`t2-preregistration.md` §4), so the two are comparable. The one known impurity
is the rare matched-with-option RAISE, a node where a raise is legal without a
wager outstanding; it was counted in the prose figures and is counted here.

The counter is a DIRECTIONAL diagnostic under the persona-realism theory
contract, never a HARD gate. Only three statistics may be gated hard today —
aggression factor, fold-to-continuation-bet, and went-to-showdown — and
went-to-showdown remains this ticket's gate.

## 2. Baseline, before any engine or pack change

Measured at the band harness's pinned seed (20260710) with all six persona packs
unedited, at the tip of improvement slice 3 after its tickets 2, 3 and 4 merged
(commit 72322d0). Two sample sizes are reported: 600 hands per persona, which is
the size continuous integration asserts the bands at, and 4,000 hands, which is
the size the slice's research figures are quoted at.

### 4,000 hands per persona

| persona | never faced a wager | went to showdown | aggression factor | fold to c-bet | showdown hands |
|---|---|---|---|---|---|
| nit | 50.33% | 0.6173 | 1.461 | 0.4350 | 600 |
| tag | 44.97% | 0.5528 | 2.383 | 0.3258 | 905 |
| lag | 42.44% | 0.5769 | 2.629 | 0.3189 | 1,395 |
| passive_fish | 33.90% | 0.5204 | 0.912 | 0.4457 | 2,180 |
| calling_station | 24.71% | 0.7010 | 0.318 | 0.1755 | 3,941 |
| maniac | 42.08% | 0.5945 | 3.147 | 0.3256 | 2,355 |

### 600 hands per persona

| persona | never faced a wager | went to showdown | aggression factor | fold to c-bet |
|---|---|---|---|---|
| nit | 52.17% | 0.5897 | 1.343 | 0.4286 |
| tag | 46.97% | 0.5714 | 2.446 | 0.2889 |
| lag | 51.23% | 0.5953 | 2.850 | 0.3871 |
| passive_fish | 37.86% | 0.5510 | 0.922 | 0.4141 |
| calling_station | 25.92% | 0.7019 | 0.322 | 0.2033 |
| maniac | 48.03% | 0.6086 | 3.042 | 0.3721 |

The nit's, TAG's and LAG's figures sit a little above the 47.7 / 44.1 / 41.6%
the earlier ticket quoted, which is the expected direction: ticket 2 of this
slice tightened those three personas' calling dials, so fewer of the hands that
DO face a wager survive to showdown, and the checked-through population is a
larger share of what remains.

Reading the roster column, the counter behaves the way the archetypes predict,
which is the evidence that it measures what it claims: the calling station,
which continues against almost anything, meets a wager in three showdowns out of
four, while the nit — which folds most of what it holds and bets only a narrow
value range — reaches half its showdowns with no chips in the middle.

## 3. Registered floors

**Not yet registered at this commit — deliberately.** The specification fixes
the derivation rule but forbids inventing the numbers: each floor is the fall
the deepest aggression-admissible dial delivers in the single-persona sweep,
minus one binomial standard error on that persona's showdown sample. The sweep
has not run at this commit, so this section is filled in by the commit that
registers the floors, which lands before any pack value moves.

Fixed in advance and not revisable by the sweep:

- The nit and the TAG get a magnitude floor on the fall in the
  never-faced-a-wager share; the LAG gets a direction only, because ticket 2 of
  this slice could not trace its showdown excess to a lever and no defensible
  magnitude can be predicted for it.
- Went-to-showdown must fall for all three, and that is the gate; the
  never-faced-a-wager fall is the diagnostic.
- Shortfall rule, from the owner's answer of 2026-08-22: if the admissible dials
  cannot clear a floor, ship the admissible value and record the shortfall
  rather than tuning past an aggression band.
