# Tickets — invest-then-fold (phase-3 ruling A, improvement slice 2)

**Bottom line: three tickets, three pull requests. T1 stops naked ace-high
floating multiway bets and already has its answer — a measured 2,015 → 1,879
events with showdown frequency flat. T2 makes a bot's bluff frequency reflect
the bet it can actually make rather than the one its pack authored. T3 is the
important one: it restores a mixed strategy to 659 river decisions the engine
currently makes with probability 1.000, on the owner's ruling of 2026-08-18.**

Spec: `../specs/phase3-invest-then-fold.md`.
Evidence: `../research/slice2-invest-then-fold/measurements.txt`.
Gate runner, built by slice 1 and reused unchanged:
`backend/tools/derobo_gate.py`.

## Dependency order

```
T1 (ace-high multiway float damp)      [PR-1] ──> T3 (river call zero: air only) [PR-3]
T2 (bluff frequency on effective size) [PR-2]
```

T2 is independent and branches from `main`. **T3 branches from T1 and must be
measured on top of it**, because T1 reduces how often ace-high reaches the river
at all — measuring T3 against the unchanged roster would credit it with T1's
work. Whichever of T1 and T2 lands second is test-merged against the first, and
any real conflict is reported rather than resolved quietly. There is no T0: the
gate runner and the five-seed set already exist and are not modified.

---

## T1 — Naked ace-high stops floating multiway bets

**Do:** Extend an existing damp to the case it always should have covered.

`_ACE_HIGH_FLOAT_RAISE_DAMP` already exists, is already calibrated, and already
applies to naked ace-high on the flop and turn — but only when facing a *raise*
(`personas_postflop.py:980-986`). Facing an ordinary bet with several opponents
live, ace-high floats at full `_CALL_BASE` weight. That single node is the
largest contributor to invest-then-fold: 457 events, 22.7 percent of the total,
and calls are 59.6 percent of all the money that gets abandoned.

The change is the predicate: fire the damp when facing a raise **or** when more
than one opponent is live. Heads-up facing-a-bet calibration is untouched, and
so is every river decision.

**This ticket has a number to hit, not a direction.** The counterfactual was run
on the same 50,000 hands at seed 20260817 and reproduced independently:

| | before | after |
|---|---:|---:|
| events | 2,015 | **1,879** |
| pool went-to-showdown | 58.46% | 58.43% |
| hands containing an all-in | 15,473 | 15,272 |
| maniac per 1,000 hands | 7.88 | 7.69 |
| calling station per 1,000 | 6.48 | 6.00 |
| nit per 1,000 | 0.54 | 0.30 |

If the implementation does not land on 1,879 at that seed, it is not this
change and the difference must be explained before the pull request opens.

**Do not:**
- Alter `_ACE_HIGH_FLOAT_RAISE_DAMP`'s value. Its magnitude was reasoned
  separately; only its predicate is wrong.
- Touch the river. The damp is gated to flop and turn and stays that way — the
  river cell is spec §6's owner decision.
- Touch the draw bonus. The damp is on the `_CALL_BASE` term only, naked hands
  only, and that stays true.
- Change any persona pack value, any bet size, or `_price_factor`.

**Acceptance:**
1. The measured table above reproduces at seed 20260817.
2. `python -m tools.derobo_gate --check` passes at seed 601 — separation above
   `1.254429`, determinism below `0.20`. `a5_baseline_z.json` is not rebuilt.
3. **Report the LAG–TAG pairwise distance explicitly, not just the minimum.** It
   is the binding pair at 1.7920, and this ticket damps 294 LAG events against
   82 TAG events, which pushes exactly that pair together. The overall PASS line
   is not sufficient evidence here.
4. A behavioural test: naked ace-high on the flop, facing a bet, three opponents
   live, calls less than the same hand heads-up. Seen to fail before the change.
5. Heads-up facing-a-bet behaviour is byte-identical on an existing seeded test.
6. Full diagnosis output attached before and after; `./scripts/verify.sh` green;
   `ruff check .` clean.

**Done-condition:**
`cd backend && PYTHONPATH=. python -m tools.derobo_gate --check && cd .. && ./scripts/verify.sh`

**Owns:** `backend/app/domain/personas_postflop.py` (the ace-high float predicate),
`backend/tests/`.

---

## T2 — A bluff's frequency reflects the bet it can actually make

**Do:** Feed `_bluff_size_factor` the stack-capped size rather than the authored
pot-fraction key.

At `personas_postflop.py:1374-1375` the bluff-size weighting is applied to the
authored fraction, and only afterwards, at `:1382`, is the resulting bet clamped
to what the seat can afford. The theory contract's bluff-share identity ties
bluff frequency to bet size; here the two disagree whenever the stack binds. A
maniac with 20bb behind in a 258bb pot prices its bluff frequency as if betting
two-thirds of the pot and then bets an eighth of it — bluffing at roughly three
times the frequency its own contract prescribes for the bet it made.

That is the aggression channel: raises and bets are 40.4 percent of the money
abandoned in this statistic, and air raising alone is 9.1 percent.

- Compute the effective fraction from the bracket's own maximum, which already
  carries the stack cap, and weight with that.
- Where the stack does not bind, behaviour must be byte-identical. That is the
  bulk of hands and it is the safety property of this ticket.

**Do not:**
- Add a second, separate "commitment" lever. That design was reviewed and
  withdrawn — spec §3, *Withdrawn from the first draft*. This ticket corrects an
  existing calculation; it does not introduce a new dial.
- Break multiply-then-complement in the betting branch. `check_merit` is formed
  as `1 - bluff_bet_mass` and the air cell is an exact-frequency cell whose two
  merits sum to one. Applying anything after the complement is the W3-b bug and
  it silently breaks `bluff_freq` as a frequency lever.
- Add any random draw. Slice 1's spec §6.1 binds: no new draw may precede the
  action draw, or every seeded test in the repository shifts.
- Change any bet size. This changes how often a bluff fires, never how big it is.
- Touch the value-betting path or any draw bonus.

**Acceptance:**
1. Deep-stacked behaviour byte-identical on existing seeded tests — the stack
   cap does not bind there, so nothing may move.
2. A behavioural test at a shallow stack showing the bluff frequency now
   matching the effective size rather than the authored key. Seen to fail first.
3. The effect is reported as a **measured frequency change**, not as a
   directional seed. `_PRICE_TAIL_K`'s precedent does not transfer: that constant
   lands on a merit that normalization dilutes, whereas here `P(bet)` *is*
   `bluff_bet_mass`, so the change is visible undiluted and must be quantified.
4. The two-stage sizing law stays coherent. Stage one scales `bluff_mass` by the
   expected factor over the sizing distribution and stage two tilts the size
   draw; changing the input to one and not the other breaks the joint law. Check
   `test_personas_postflop.py` around the sizing-law tests before assuming
   otherwise.
5. Gate passes at seed 601, LAG–TAG reported explicitly.
6. Full diagnosis output attached before and after; `./scripts/verify.sh` green;
   `ruff check .` clean.

**Note on a perverse channel, measured and bounded.** Where the river bluff cell
does offer a raise, damping it moves mass to fold — and a fold is the counted
event. Only 29 bluff-cell raises in 50,000 hands already satisfy the counted
precondition, 8 of them on the river, against 2,015 counted folds; at 94 percent
of the events a raise is not legal at all. Converting every one would raise the
statistic by 1.4 percent. Confirm the direction; if the statistic rises, the
change is firing in the wrong place rather than merely too hard.

**Done-condition:** as T1.

**Owns:** `backend/app/domain/personas_postflop.py` (the bluff sizing-weight
path), `backend/tests/`.

---

## T3 — Ace-high may call the river again

**Do:** Narrow the river call zero at `personas_postflop.py:1010` so it applies
to AIR only, leaving ACE_HIGH free to call.

The rule reads `if bluff_cell and street is Street.RIVER: call_merit = 0.0`, and
`bluff_cell` at `:893` bundles ACE_HIGH with AIR. Every comment around the rule
describes it as "air never bluff-CALLS the river". Ace-high is not air — it beats
a busted draw and it beats a bluff, which is the definition of a river
bluff-catcher, and real players call with it. **659 of the 985 blocked decisions
are ace-high.**

The consequence today is not merely over-folding, it is determinism. When the
faced bet is at least the seat's remaining stack the engine offers no raise
(`table/engine.py:204-206`), so a zeroed call leaves fold as the only weighted
candidate and the bot folds 1000 times out of 1000. That is the machine tell this
whole initiative exists to remove, and it fires 950 times per 50,000 hands.

- Change the predicate at the call-zero only. Use the made-hand bucket and draw
  directly rather than `bluff_cell`, so the change is visibly scoped to the call.
- **Leave `bluff_cell` itself alone.** It also drives the bluff bet and bluff
  raise mass; ace-high must keep its ability to bluff-raise the river. This
  ticket unblocks one action, not a hand class.

**Do not:**
- Touch AIR. "Air never calls the river" survives this ticket intact; it is the
  half of the rule that was always right.
- Touch `_CALL_BASE[ACE_HIGH]`, the flop/turn float damp (T1's territory), or
  any persona pack.
- Reach for a revert if the showdown cost overshoots. The next move in that case
  is a river-specific damp on ace-high's call term, keeping the mixing while
  lowering its weight — the point of the ticket is that the decision is *mixed*,
  not that ace-high calls often.

**Acceptance:**
1. **The determinism improves and is reported as a number.** Re-run the
   diagnosis script: the count of river air/ace-high folds facing a bet at least
   the stack should fall from 950 toward roughly 300 — the AIR-only residual.
   This is the ticket's real acceptance criterion; the event count is secondary.
2. Pool went-to-showdown rises by no more than the **3.66 point upper bound** in
   spec §6, measured on top of T1 rather than against the unchanged roster.
   Exceeding the bound means something other than this change moved.
3. `python -m tools.derobo_gate --check` passes at seed 601, with the LAG–TAG
   pair reported explicitly and the determinism rule's measured value reported
   whether or not it passes.
4. A behavioural test: ace-high with no draw, on the river, facing a bet, returns
   a genuinely mixed call/fold distribution rather than fold at 1.0. Air in the
   same spot still never calls. Seen to fail before the change.
5. Full diagnosis output attached before and after; `./scripts/verify.sh` green;
   `ruff check .` clean.

**Done-condition:** as T1.

**Owns:** `backend/app/domain/personas_postflop.py` (the river call-zero
predicate), `backend/tests/`.

---

## Slice close-out

Owed before the slice is marked complete:

- The five-seed gate set, `--all-seeds`, at the final tip, with LAG–TAG and the
  determinism rule's measured value both reported.
- A ledger at `../ledger/phase3-invest-then-fold.md` recording what each reviewer
  found and how it was adjudicated. Both tickets came from review and the first
  draft's own proposal was withdrawn; that belongs on the record.
- The out-of-scope findings written up as filed items: the all-in cascade at
  30.9 percent of hands, the residual AIR-only deterministic folds, the bottom-bucket
  price saturation, the maniac's preflop 4-bet catch-all, and the 851 events
  belonging to the calling personas that are slice 3's to fix.
- The owner's blind play session. Under the 2026-08-17 ruling it is the primary
  acceptance evidence for the slice, not a supplement to the gate.
