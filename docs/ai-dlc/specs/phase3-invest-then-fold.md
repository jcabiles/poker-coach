# Spec — invest-then-fold (phase-3 ruling A, improvement slice 2)

**Bottom line: the defect is real, ruling A's named cause is wrong, and the
sharpest thing wrong with these hands is not that the bot folds — it is that it
folds with probability exactly 1.000. Forty-seven percent of invest-then-fold
events are a decision with only one non-zero option, because the engine zeroes
the call and the rules make the raise illegal. Of the rest, the fold is usually
correct poker and the error is upstream, in money the bot put in with a hand
that could not win. Two tickets attack that upstream money. Both were proposed
by reviewers, not by the first draft of this spec, and one of them is already
measured.**

Roadmap: `../roadmap/bot-realism-flywheel.md`, improvement phase, slice 2.
Ruling: `phase3-decision-matrix.md` §4 (ruling A, 2026-08-15).
Previous slice, for house style and its nine open owner items:
`phase3-derobotization.md` · `../tickets/phase3-derobotization.md`.
Evidence: `../research/slice2-invest-then-fold/measurements.txt`, reproducible
with the script beside it.

**Review provenance, because it changed the answer.** Two independent reviewers
saw this work: one given only the data and the code and asked to derive the
mechanism with no sight of any conclusion, one given the draft spec and asked to
break it. Between them they refuted the fix the first draft proposed, corrected
two of its numbers, showed one of its exclusion reasons to be backwards, and
supplied both tickets below. Findings and adjudication:
`../ledger/phase3-invest-then-fold.md`.

## 1. What was measured

Fifty thousand hands at the shipped tip (`d619535`, seed 20260817, the default
nine-seat lineup), scored with the definition the 2026-08-05 re-measure used: a
fold where the seat has already committed at least 25bb in the hand and is being
offered pot odds of at least 5:1. Two thousand and fifteen events.

**The rate has not moved.** Per thousand hands: maniac 7.88, calling station
6.48, passive fish 3.52, LAG 2.94, TAG 1.64, nit 0.54, against a 2026-08-05
baseline of 7.0, 5.58, 2.60, 2.22, 1.19, 0.38. Same ordering, same order of
magnitude. Different seed and a changed roster, so the small rise is not
attributed to anything. De-robotization did not touch this.

### 1.1 Forty-seven percent of the events are not decisions at all

At 950 of the 2,015 the bot has exactly one action with any weight behind it, so
it folds with probability 1.000. Three facts compose to produce that:

- The seat is facing a bet at least as large as its remaining stack, so
  `table/engine.py:204-206` does not offer a raise at all — `can_raise` requires
  headroom above the current bet, and there is none.
- The hand is air or ace-high with no draw on the river, so
  `personas_postflop.py:1010` sets `call_merit = 0.0` outright.
- Fold is therefore the only candidate with non-zero merit.

**This, not the fold rate, is the machine tell.** A bot that folds these spots
80 percent of the time is playing a defensible strategy; a bot that folds them
1000 times out of 1000 is a lookup table. It is the same defect class slice 1
spent seven pull requests removing from bet sizing, sitting untouched in the
call/fold decision.

### 1.2 The events are all-in refusals in pots the environment inflates

Ninety-four percent of the time the declined call would put the seat's entire
remaining stack in. Median pot 258bb — two and a half buy-ins. In 97 percent of
them at least one seat in the hand finishes all-in and in 56 percent two or more
do, counted over the whole hand, so some of those land after the fold.

Those pots exist because 30.9 percent of hands at this tip see at least one seat
all-in. Nine seats, each re-bought to about 100bb before every hand, no rake, no
stack progression. **Ruling A cut engine and stack work from this phase, so the
largest single contributor to this statistic is out of reach by ruling.** It is
named because a judge watching a nine-handed 100bb table would notice an all-in
in nearly a third of hands long before noticing anyone's fold.

### 1.3 The fold itself is right, and this was checked hand by hand

The reviewer working from the data alone enumerated the remaining boards against
the actual holdings. The caller needs a median of 11 percent equity. **1,692 of
the 2,015 holdings (84 percent) do not have it, and 1,330 (66 percent) are
drawing dead.** Only 323 clear the price; on the river only 45 of 1,152 do.

So a minority of these folds are individually mistakes, and forcing calls across
the board would be badly wrong poker — quite apart from what it would do to
showdown frequency.

### 1.4 The money went in as a call, not as a bluff

Split by the action at the seat's single largest chip commitment:

| action | events | share |
|---|---:|---:|
| call | 1,200 | 59.6% |
| raise | 484 | 24.0% |
| bet | 331 | 16.4% |

The most common single path is calling a big turn bet holding naked ace-high:
457 events, 22.7 percent of the total. The largest commitment lands on the turn
58 percent of the time and on the flop 37 percent.

`_CALL_BASE[ACE_HIGH] = 0.40` is multiplied by persona looseness with no equity
term and no street term, and the damp that exists for naked ace-high
(`_ACE_HIGH_FLOAT_RAISE_DAMP`, `personas_postflop.py:980-986`) fires **only when
facing a raise**. Facing an ordinary multiway bet, ace-high floats at full
weight — including at the calling station's looseness of 4.0.

### 1.5 "Build a pot with aggression, then fold" is false for most of it

Forty percent of the seats never bet or raised at all in the hand; 59 percent put
more than half their money in by calling. Mean share of the investment that went
in aggressively:

| persona | events | aggressive share | reading |
|---|---:|---:|---|
| maniac | 788 | 0.74 | aggression |
| LAG | 294 | 0.54 | aggression |
| TAG | 82 | 0.41 | mixed |
| nit | 27 | 0.26 | calling |
| passive fish | 176 | 0.21 | calling |
| calling station | 648 | 0.04 | calling |

The three calling-driven personas account for **851 events, 42.2 percent**.

### 1.6 The mechanism is shared; only the arrival differs

Given a seat has already folded after investing 25bb, the chance it was getting
5:1 or better is 26.2 to 33.4 percent for every persona. The per-hand rate spans
fifteen-fold. One shared node, six arrival frequencies.

### 1.7 Retracted from the first draft of this spec

The draft argued that the price term saturates in its bottom bucket and offered
as evidence that 100 percent of events fall in that bucket. **That evidence is a
tautology.** The counted events are filtered to pot odds of 5:1 or better, which
forces the faced fraction below 0.25, which is inside the bottom bucket by
construction. The filter produced the finding.

The underlying code fact survives on its own: `_BUCKET_ALPHA` assigns one
constant to every bet from zero to 40 percent of pot, and the mirror-image fix
at the top of the scale (`R10-TAIL-a1`) was never applied downward. But nothing
in this measurement is evidence about it, and §3 no longer relies on it.

## 2. Goal

Reduce how often a bot puts 25bb or more into a pot holding something that
cannot win it, without making it call all-ins it should fold and without pushing
showdown frequency up.

**Not the goal: making the fold go away.** See §1.3.

## 3. Scope

### In scope — three tickets

1. **Extend the naked-ace float damp to multiway bets.** The damp already exists
   and already has a reviewed constant; it simply never fires against an
   ordinary bet with more than one opponent. This is the 59.6 percent channel.
   **Already measured on the same 50,000 hands and seed:** events 2,015 → 1,879
   (−6.7 percent), pool went-to-showdown 58.46 → 58.43 percent, hands containing
   an all-in 15,473 → 15,272. Every persona falls. Reproduced independently
   before being written into this spec.
2. **Price the bluff-size factor on the size the seat can actually bet.**
   `_bluff_size_factor` is applied to the *authored* pot-fraction key at
   `personas_postflop.py:1374-1375`, and the resulting bet is only clamped to the
   stack afterwards at `:1382`. A maniac with 20bb behind in a 258bb pot
   therefore sets its bluff frequency as though making a two-thirds-pot bet while
   actually making an eighth-pot one. The frequency and the size disagree; the
   theory contract's own bluff-share identity says they must not. This is the
   24.0 + 16.4 percent channel, and it is a bug fix rather than a new lever.
3. **Remove ACE_HIGH from the river call zero, per §6's ruling.** Restores a
   mixed strategy to 659 of the 985 deterministic folds. Ships last, measured on
   top of ticket 1, because ticket 1 reduces how often ace-high reaches the
   river at all and the two effects must not be attributed to each other.

### Withdrawn from the first draft

**A generic "damp the bluff by the fraction of stack it commits" lever.** Both
reviewers rejected it, on different grounds, and both were right. It keys on
commitment where the engine's bluff law keys on pot fraction, so it fights
`_bluff_size_factor` with an anti-correlated multiplier that cannot be jointly
calibrated. And the poker is contested: a 20bb shove into a 258bb pot needs only
about 7 percent fold equity to break even, so "short stack means bluff less" is
not the settled principle the draft treated it as. Ticket 2 achieves the intent
without taking a position on it.

### Explicitly out of scope, each with a corrected reason

- **Sub-`SMALL` price resolution.** The draft excluded it because it would send
  freed mass to the raise and make air jam the river. **That reason is refuted:**
  at these nodes the raise is illegal (§1.1), so a price change there is an exact
  no-op. It stays out for the reasons that do hold — off the river it converts
  folds into calls and pushes showdown up, its blast radius is every small-bet
  decision in the game, and per §1.7 this measurement is no evidence for it.
- **The river call hard-zero at `:1010`** — no longer out of scope. Ruled on
  2026-08-18 and ticketed as T3; see §6.
- **The all-in cascade and stack persistence.** Cut by ruling A. It is 94 percent
  of the surface.
- **The calling personas' bulk calldown.** Their 851 events are slice 3's, except
  for the specific ace-high multiway float in ticket 1, which belongs here
  because it is showdown-neutral and is the top single node in this statistic.
- **Bet-size variation.** The bots' grid is the grader's grid; escalated and
  unresolved.
- **The strong-draw call floor at `:1006-1007`.** Its own roadmap item.
- **The maniac's preflop 4-bet catch-all.** Twelve events, all the maniac calling
  or shoving any two cards in a re-entrant raise war
  (`content/personas/maniac.json`). Real, tiny, and a pack question.

## 4. Files and interfaces

Only `backend/app/domain/personas_postflop.py` changes behaviour. No grader, no
export, no analytics, no persona pack.

**`spot_signature()` is not at risk, and this was checked.** Its postflop path
uses `srs.faced_bet_bucket`, a binary split at half pot, and never calls
`personas_postflop.size_bucket`. No bet size and no hero-facing boundary moves.

## 5. Gates

Reuse slice 1's runner, `backend/tools/derobo_gate.py`, unchanged. No new
measurement apparatus, per the owner ruling of 2026-08-17.

- **Per ticket:** seed 601, both rules. Separation above the pinned floor of
  `1.254429`, determinism below its `0.20` ceiling. Never rebuild
  `a5_baseline_z.json`.
- **Slice:** the five-seed set, `--all-seeds`.
- **The tell statistic:** re-run the diagnosis script at the same seed and report
  its full output, not the headline. A change that relocates the events has not
  fixed them.

**Which gate can actually see this slice's damage, corrected.** The binding
separation pair is **LAG–TAG at 1.7920**, not anything involving the maniac —
maniac–LAG sits at 3.7247 with a preflop-only component of 2.774, so the maniac
could lose its entire postflop identity without breaching the floor. Ticket 1
damps the LAG's 294 events and barely touches TAG's 82, which pushes exactly the
binding pair together. Watch that pair specifically, and watch the determinism
guard, which is the other rule with something to say here.

**A known interaction, not a surprise if it fires.** A slice-1 owner item records
that the LAG's frozen showdown band has about 0.8 standard errors of headroom and
that the next change lowering pot sizes trips it. Both tickets lower pot sizes.
If the band breaches, report and stop — whether the band is right is the owner's
call, not a value to fit around.

## 6. The owner's ruling on the river call hard-zero

**The river call hard-zero is the biggest thing here and this spec deliberately
does not resolve it.** Two facts make it a decision rather than a ticket.

It manufactures determinism. It is the direct cause of the 950 forced folds in
§1.1 — the single largest identifiable machine tell this diagnosis found, in a
project whose north star is whether a judge can spot the machine.

And the cell is wider than its own stated rationale. `bluff_cell` at
`personas_postflop.py:893` bundles ACE_HIGH together with AIR, while every
comment around the rule says "air never bluff-calls the river". **Of the 985
events in that cell, 659 are ace-high, not air** — a hand that is a legitimate
river bluff-catcher, folded at up to 12:1.

The cost of opening it, measured, and stated as the upper bound it is: converting
**every** such fold to a call moves pool went-to-showdown from 58.46 percent to
62.12 percent for the ace-high half alone, or 64.60 percent for both. The real
figure would be lower, because the merit law would mix rather than always call.
Showdown frequency is the binding term slice 3 must reduce, so this trades the
initiative's north star against its inner-loop metric, and that trade is the
owner's to make.

**RULED 2026-08-18 (owner): remove ACE_HIGH from the river call zero, keep
AIR.** It ships as ticket T3.

The two rejected options and why. Leaving it alone costs nothing but ends the
improvement phase without touching the diagnosis's largest finding, which would
be the prime suspect if the finale flags the roster. Giving both hands a small
non-zero call merit breaks the determinism everywhere but makes bots call river
bets with total garbage — the roadmap's Goodhart guard names that failure
explicitly ("a bot that gets harder to detect by going bland fails the
initiative").

**The ruling's deciding reason, recorded because it should govern later calls
too: this change is justified by poker theory independently of the realism
goal.** Ace-high is a river bluff-catcher; calling with it sometimes is correct
play, not merely less predictable play. A change defensible only as "makes
detection harder" is exactly what the Goodhart guard exists to catch, and this
one is not in that class. It also aligns the code with an intent its own
comments already state, rather than inventing a new principle.

The spec author initially declined to recommend, treating the trade as a pure
metric-against-metric judgement. That framing was wrong: the poker argument
breaks the tie, and it should have been surfaced as such the first time.

Separately, the roadmap's slice 2 entry still names a mechanism this measurement
refutes, and its slice 3 entry does not know that 851 of these events are its
own. This spec does not edit the roadmap.

## 7. Acceptance

### Per ticket

1. Gate passes at seed 601 on both rules.
2. `./scripts/verify.sh` green; `cd backend && ruff check .` clean.
3. Diagnosis script re-run at the same seed, full output attached to the pull
   request before and after.
4. A targeted test that has been seen to fail without the change.
5. **The measured delta is reported, not a direction.** Ticket 1 has a
   pre-committed number to hit: 1,879 events. Ticket 2 lands on an
   exact-frequency cell where the bet probability *is* the merit, so its constant
   is not diluted by normalization and its effect must be stated as a measured
   frequency change, not as a directional seed.

### Slice

1. Five-seed gate set passes, with the LAG–TAG pair reported explicitly.
2. The determinism guard IMPROVES, not merely passes. T3's whole purpose is to
   turn 659 forced folds into mixed decisions, and a guard reading that does not
   move is evidence the change did not reach the node it was aimed at.
3. Events fall materially and the aggressive-investment shares of the maniac and
   the LAG (0.74 and 0.54) fall with them.
4. Pool went-to-showdown rises by no more than T3's measured cost and by nothing
   at all from T1 or T2. The +3.66 point figure in §6 is an upper bound; the
   realised figure is reported, and if it exceeds the bound something other than
   T3 moved.
5. The hero's graded-decision coverage ratio is reported. Slice 1 left it failing
   at −0.26pp and its replacement is an unresolved owner item; this slice must
   not quietly make it worse.
6. The owner plays a blind session and says whether the table feels different.
   Under the 2026-08-17 ruling that is the primary acceptance evidence.

## 8. Verify-by

```
cd backend && PYTHONPATH=. python -m tools.derobo_gate --check
cd backend && PYTHONPATH=. python -m tools.derobo_gate --check --all-seeds
./scripts/verify.sh
cd backend && ruff check .
```

## 9. Risks

- **The slice's ceiling is low and that should be said plainly.** Ticket 1's
  measured effect is a 6.7 percent reduction. Ninety-four percent of the events
  are all-in refusals in pots inflated by an environment ruling A put out of
  reach. T3 is the largest single lever and it targets the determinism rather
  than the count — it may barely move this statistic while fixing the thing that
  actually matters. Nobody should expect the number near zero at slice end.
- **Ticket 1 pushes the binding separation pair together.** See §5.
- **Ticket 2 changes bluff frequency wherever stacks are short,** which is far
  more hands than the 2,015 counted here. It is judged on the whole diagnosis
  output and the gate, not on the headline rate.
- **Both tickets came from reviewers rather than from the author of this spec.**
  That is recorded, not hidden: the first draft's own fix was refuted on the
  poker and on the arithmetic, and a spec that had shipped as drafted would have
  built a lever with no measured effect and a contested rationale.
