# Spec — invest-then-fold (phase-3 ruling A, improvement slice 2)

**Bottom line: the defect is real, ruling A's named cause is wrong, and the
sharpest thing wrong with these hands is not that the bot folds — it is that it
folds with probability exactly 1.000. Forty-six percent of invest-then-fold
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

Fifty thousand hands at the shipped tip, seed 20260817, on the **ratified**
nine-seat lineup `tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac`
— the lineup the gate, the frozen baseline artifact and the 2026-08-05 re-measure
all use. Scored with the definition that re-measure used: a fold where the seat
has already committed at least 25bb and is being offered pot odds of at least
5:1. **One thousand one hundred and forty-seven events.**

> **CORRECTION, 2026-08-18.** The first version of this spec measured on the
> exporter's default lineup, which is alphabetical and carries two calling
> stations, two LAGs and two maniacs instead of three TAGs and two passive fish.
> `../reports/flywheel-s4-acceptance.md` states plainly that the default is not
> ratified. Every count in that version was therefore incomparable with the gate
> and with the 2026-08-05 baseline. Two independent reviewers found it. **Every
> mechanism finding below survived the re-measure; every count changed.** The
> diagnosis script now reads the export manifest and refuses to let a reader
> mistake one lineup for the other.

**The rate has not moved, and this is now a comparable claim.** Per thousand
hands: maniac 6.40, calling station 4.60, passive fish 2.77, LAG 2.48, TAG 1.23,
nit 0.22, against a 2026-08-05 baseline on the same lineup of 7.0, 5.58, 2.60,
2.22, 1.19, 0.38. Four fell, two rose slightly. Different seed and a changed
roster, so nothing is attributed to de-robotization either way — but it plainly
did not fix this.

### 1.1 Forty-seven percent of the events are not decisions at all

At 524 of the 1,147 the bot has exactly one action with any weight behind it, so
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

Ninety-three percent of the time the declined call would put the seat's entire
remaining stack in. Median pot 253bb — two and a half buy-ins. In 97 percent of
them at least one seat in the hand finishes all-in and in 53 percent two or more
do, counted over the whole hand, so some of those land after the fold.

Those pots exist because 20.2 percent of hands at this tip see at least one seat
all-in. Nine seats, each re-bought to about 100bb before every hand, no rake, no
stack progression. **Ruling A cut engine and stack work from this phase, so the
largest single contributor to this statistic is out of reach by ruling.** It is
named because a judge watching a nine-handed 100bb table would notice an all-in
in nearly a third of hands long before noticing anyone's fold.

### 1.3 The fold itself is right, and this was checked hand by hand

The reviewer working from the data alone enumerated the remaining boards against
the actual holdings. The caller needs a median of 11 percent equity. **84 percent
of the holdings do not have it and 66 percent are drawing dead**; 16 percent do
clear the price.

Two limits on that number, both load-bearing. It is a **post-hoc** check — it asks
whether folding was right given what was actually out there, not given what the
bot could know. And that enumeration was run on the earlier default-lineup export,
so the shares are quotable and the counts are not.

**What this slice does not fix, stated so the 84 percent does not read as an
acquittal:** the 16 percent where the price is genuinely there, and **264 folds
holding a made pair (23 percent — 234 middle pair, 30 top pair)**. Equity
arithmetic is invisible to someone reading hands; a seat folding a made pair at
long odds is not.

### 1.4 The money went in as a call, not as a bluff

Split by the action at the seat's single largest chip commitment:

| action | events | share |
|---|---:|---:|
| call | 715 | 62.3% |
| raise | 284 | 24.8% |
| bet | 148 | 12.9% |

The most common single path is calling a big turn bet holding naked ace-high:
245 events, 21.4 percent of the total. The largest commitment lands on the turn
59 percent of the time and on the flop 35 percent.

`_CALL_BASE[ACE_HIGH] = 0.40` is multiplied by persona looseness with no equity
term and no street term, and the damp that exists for naked ace-high
(`_ACE_HIGH_FLOAT_RAISE_DAMP`, `personas_postflop.py:980-986`) fires **only when
facing a raise**. Facing an ordinary multiway bet, ace-high floats at full
weight — including at the calling station's looseness of 4.0.

### 1.5 "Build a pot with aggression, then fold" is false for most of it

Thirty-eight percent of the seats never bet or raised at all in the hand, and the
median seat put in three quarters of its money by calling. Mean share of the
investment that went in aggressively:

| persona | events | aggressive share | reading |
|---|---:|---:|---|
| maniac | 320 | 0.71 | aggression |
| LAG | 124 | 0.57 | aggression |
| TAG | 185 | 0.42 | mixed |
| passive fish | 277 | 0.25 | calling |
| nit | 11 | 0.20 | calling |
| calling station | 230 | 0.03 | calling |

The three calling-driven personas account for **518 events, 45.2 percent**.

**That share is not an ownership claim, and an earlier draft wrongly made it
one.** The conditional rate is flat across all six personas (§1.6), which is
evidence of a *shared* node rather than a calling-specific mechanism; ticket T1
already reduces these personas' counts; and the split is a property of the table
composition. See §6.2 for where the slice boundary actually falls.

### 1.6 The mechanism is shared; only the arrival differs

Given a seat has already folded after investing 25bb, the chance it was getting
5:1 or better is 21.2 to 26.8 percent for every persona — a span of five points
across archetypes that differ wildly in everything else. The per-hand rate spans
nearly thirtyfold, from the nit's 0.22 to the maniac's 6.40. One shared node, six
arrival frequencies.

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
   ordinary bet with more than one opponent. This is the 62.3 percent channel.
   **Already measured, on the ratified lineup at seed 20260817:** events
   1,147 → 1,084 (−5.5 percent), pool went-to-showdown 54.5 → 54.1 percent, hands
   containing an all-in 10,121 → 10,043. Reproduced independently before being
   written into this spec. (On the earlier default lineup the same change measured
   −6.7 percent; the effect is real but its size depends on how multiway the table
   is, which is exactly why the lineup is pinned now.)
2. **Price the bluff-size factor on the size the seat can actually bet.**
   `_bluff_size_factor` is applied to the *authored* pot-fraction key at
   `personas_postflop.py:1374-1375`, and the resulting bet is only clamped to the
   stack afterwards at `:1382`. A maniac with 20bb behind in a 258bb pot
   therefore sets its bluff frequency as though making a two-thirds-pot bet while
   actually making an eighth-pot one. The frequency and the size disagree; the
   theory contract's own bluff-share identity says they must not. This is the
   24.0 + 16.4 percent channel, and it is a bug fix rather than a new lever.
3. **Remove ACE_HIGH from the river call zero, per §6's ruling.** Restores a
   mixed strategy to 413 of the 550 events in that cell. Ships last, measured on
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
- **The calling personas' residual continuation.** Slice 3's, on the boundary in
  §6.2 — not because of who they happen to, but because they are arrival at nodes
  that already mix. The specific ace-high multiway float stays here as ticket 1.
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
could lose its entire postflop identity without breaching the floor. **Corrected
2026-08-19, owner-authorised (ledger finding 9 of the T1 build round): this
paragraph said ticket 1 "damps the LAG's 294 events and barely touches TAG's 82",
and the committed evidence says LAG 124 and TAG 185.** Ticket 1 in fact removes
more TAG events in absolute count (185 → 168) than LAG (124 → 114). The 294 and
82 figures were default-lineup survivors that the 2026-08-18 re-measure missed.
**The prediction built on them was also wrong**: T1 moved the binding pair APART,
1.8469 → 1.9852, not together. Watch that pair specifically anyway, and watch the
determinism guard, which is the other rule with something to say here.

**A known interaction, not a surprise if it fires.** A slice-1 owner item records
that the LAG's frozen showdown band has about 0.8 standard errors of headroom and
that the next change lowering pot sizes trips it. Both tickets lower pot sizes.
If the band breaches, report and stop — whether the band is right is the owner's
call, not a value to fit around.

## 6. The owner's ruling on the river call hard-zero

**The river call hard-zero is the biggest thing here and this spec deliberately
does not resolve it.** Two facts make it a decision rather than a ticket.

It manufactures determinism. It is the direct cause of the 524 forced folds in
§1.1.

**But not because a judge will catch it, and this spec should not pretend
otherwise.** 524 events across 50,000 hands is 524 of 450,000 seat-hands. A judge
reading a 30-hand bundle from one seat expects **0.03 of these events** — roughly
one per thirty judged sessions. The direct detectability is not weak, it is
absent. Two reasons that do hold: it is the same lookup-table signature slice 1
spent seven pull requests removing from bet sizing, and leaving it in the
call/fold decision while having removed it from sizing is internally
inconsistent; and any statistical detector sees it at once, which is why it is a
good regression statistic even though it is a poor detection argument.

And the cell is wider than its own stated rationale. `bluff_cell` at
`personas_postflop.py:893` bundles ACE_HIGH together with AIR, while every
comment around the rule says "air never bluff-calls the river". **Of the 550
events in that cell, 413 are ace-high, not air** — a hand that is a legitimate
river bluff-catcher, folded at up to 12:1. **This is the argument the ruling
turns on, and it is a poker argument, not a detection one.**

The cost of opening it, measured, and stated as the upper bound it is: converting
**every** such fold to a call moves pool went-to-showdown from 54.5 percent to
58.3 percent for the ace-high half alone, or 60.5 percent for both. The real
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
refutes, and its slice 3 entry does not know about the boundary in §6.2 or the
share of these events it implies. This spec does not edit the roadmap.

### 6.2 Where the slice boundary actually falls

An earlier draft claimed the calling personas' events "belong to" slice 3 on the
strength of who they happen to occur to. Both reviewers rejected that, and they
were right: persona membership is not ownership, the conditional rate is flat
across all six, and T1 — a slice-2 ticket — already reduces those same personas.

The boundary that survives is drawn on the **defect**, not on the persona and not
on the showdown direction:

> **Slice 2 owns decisions that are degenerate or mis-invested. Slice 3 owns the
> continuation frequency at decisions that already mix.**

| Item | Slice | Why |
|---|---|---|
| T1 — ace-high stops floating multiway bets | 2 | money invested with a hand that cannot win |
| T2 — bluff frequency priced on the bettable size | 2 | frequency and size disagree; a coherence bug |
| T3 — ace-high out of the river call zero | 2 | turns a probability-1.000 decision into a mixed one |
| The calling personas' residual continuation | 3 | arrival at nodes that already mix, driven by looseness |
| Draw floor at `personas_postflop.py:1006-1007` | 3 | it makes a mixing node untunable, and tunability is calldown's dial |

T3 was the counterexample that killed an earlier version of this principle, which
was drawn on showdown direction. Under this one T3 is unproblematic: it removes a
certainty, and its showdown cost is a number to report rather than a classifier.

The boundary also assigns the draw-floor entry, which currently sits on the
roadmap owned by nobody — and it is a **prerequisite** for slice 3, not a
sibling. The floor holds part of the strong-draw calling weight fixed no matter
how far `call_looseness` tightens, and `call_looseness` is calldown's principal
dial.

## 7. Acceptance

### Per ticket

1. Gate passes at seed 601 on both rules.
2. `./scripts/verify.sh` green; `cd backend && ruff check .` clean.
3. Diagnosis script re-run at the same seed, full output attached to the pull
   request before and after.
4. A targeted test that has been seen to fail without the change.
5. **The measured delta is reported, not a direction.** Ticket 1 has a
   pre-committed number to hit: 1,084 events on the ratified lineup at seed
   20260817. Ticket 2 lands on an
   exact-frequency cell where the bet probability *is* the merit, so its constant
   is not diluted by normalization and its effect must be stated as a measured
   frequency change, not as a directional seed.

### Slice

1. Five-seed gate set passes, with the LAG–TAG pair reported explicitly.
2. The determinism guard IMPROVES, not merely passes. T3's whole purpose is to
   turn forced folds into mixed decisions, and a guard reading that does not move
   is evidence the change did not reach the node it was aimed at.

   **Corrected 2026-08-19: this criterion cannot do the job it was written for,
   and the "659" was a default-lineup figure.** **The mechanism, derived from the
   rule's own definition and from the five-seed gate output rather than assumed:
   the guard does see these contexts and flags them, but it is a share-of-contexts
   rule and a handful of flagged river contexts cannot move it.** The rule keys a
   context as `(persona, street, engine_node_key, hand_class_bucket)`, qualifies it
   at 50 or more observations, calls it deterministic when its modal action share
   reaches 0.98, and fails a persona only when more than 20 percent of that
   persona's qualifying contexts are deterministic. River naked-ace-high contexts
   clear the observation threshold easily and are flagged: at the merged tip the
   nit's river `flat` / `ace_high|none` context reads a 0.9864 modal share over 220
   observations at seed 601, and the equivalent calling-station context reads 0.9907
   over 2,266 — **flagged after T3, exactly as they were before it.** They are a
   couple of entries among the nit's 91 qualifying contexts, so they sit far below
   the 20 percent allowance whether they are deterministic or not. Two further
   reasons the reading is insensitive: `engine_node_key` does not encode "faced a
   bet at least the seat's remaining stack", so the fold surface this slice targets
   is a thin slice inside a broader context rather than a context of its own; and a
   damp of 0.06 does not lift these contexts back under the 0.98 threshold. The
   guard's own readings wandered between 0.12 and 0.16 across the slice on counts of
   11–15 out of 85–115, which is churn in which contexts clear the 50-observation
   threshold. **The instrument that does measure the property is the diagnosis
   script's count of folds that are probability-1.000 by construction: 524 at slice
   start, 495 after T1, 144 at the merged tip.** Read that, not the guard.

   **An earlier revision of this correction said the rule "keys its contexts
   without any hand class" and was therefore blind to the cell. That was false in
   both halves** — the key's fourth element *is* `hand_class_bucket`, and the cell
   *is* among the rule's flagged contexts. The claim came from PR #200's body and
   was repeated here without being checked against the rule's source. The
   conclusion survives the correction and is in fact firmer: a guard that flags
   these contexts identically before and after T3 says nothing about whether T3
   worked.
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
  measured effect is a 5.5 percent reduction. Ninety-four percent of the events
  are all-in refusals in pots that only exist because a fifth of hands see an
  all-in — an environment ruling A put out of reach. Note what is *not* claimed:
  no counterfactual has been run that removes the cascade, so "the environment
  causes the rate" is an inference, not a measurement. T3 is the largest single lever and it targets the determinism rather
  than the count — it may barely move this statistic while fixing the thing that
  actually matters. Nobody should expect the number near zero at slice end.
- **Ticket 1 pushes the binding separation pair together.** See §5.
- **Ticket 2 changes bluff frequency wherever stacks are short,** which is far
  more hands than the 1,147 counted here. It is judged on the whole diagnosis
  output and the gate, not on the headline rate.
- **Both tickets came from reviewers rather than from the author of this spec.**
  That is recorded, not hidden: the first draft's own fix was refuted on the
  poker and on the arithmetic, and a spec that had shipped as drafted would have
  built a lever with no measured effect and a contested rationale.
