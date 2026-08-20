# T1 — the α ceiling for naked ace-high facing a BET, at 1, 2 and 3 opponents

**Bottom line: α as currently written does not discriminate a good tip from a bad
one on this hand class, so it cannot pass or fail T1. The naked-ace-high fold
rate already exceeds α = f/(1+f) at 15 of 24 persona-and-size cells BEFORE the
change, at a single opponent, on the untouched engine. `_CATCHER_BUCKETS`
excludes ace-high from the α contract deliberately, on the stated ground that
ace-high loses to part of a balanced bettor's bluff half and so is not a
bluff-catcher. Whether α should be asserted over this bucket at all is an open
question and is referred to the owner; nothing here settles it. What T1 can be
judged on is the size of the move it makes — reported below on BOTH gated
streets — and the fact that the catcher range the α contract IS asserted over
stays byte-identical at every opponent count, which is now a test.**

Ticket acceptance criterion 6. Produced by `alpha_measure.py` beside this file.

**UPDATE 2026-08-19 — the open question above is answered, and this file's
measurements still stand.** The owner ruled that α DOES apply to the ACE_HIGH
bucket. Every number below is unchanged and reproduces at HEAD; what changes is
that "whether α should be asserted over this bucket" is no longer open, so read
the sentences below that refer it as historical. The ruling, the RIVER street
this file never swept, and the full violation map are in
`alpha-acehigh-ruling.md` beside this file.

## What was measured, and one thing that nearly broke the measurement

1,250 naked-ace-high spots (`StrengthBucket.ACE_HIGH` + `DrawCategory.NONE`),
dealt at seed 20260721, facing a FOLD/CALL/RAISE decision with a bet of
`frac × 6bb` into a 6bb pot, 100bb stacks, per-cell decision seed
`20260721 + 100·persona_index + frac_index`. Node, seeds and sampler call are
the ones `catcher_fold_by_size` uses, so the two tables are directly comparable.

**`street` had to be passed explicitly, and this is the trap.** Both existing
price fixtures (`fold_by_size`, `catcher_fold_by_size`) omit `street`, so they
measure at `street=None` — outside the damp's `street in (FLOP, TURN)` gate. A
first version of this measurement copied them and produced before/after tables
that were byte-identical, i.e. it measured nothing. The `street=none` block below
is retained as a control: it is identical before and after, which is what proves
the flop and turn blocks' movement is T1's and not noise.

**Both gated streets are measured.** An earlier version of this file swept only
FLOP, which covered half the predicate's surface. One honest caveat about the
TURN block: the sampler is given the same three-card board with `street` set to
`Street.TURN`, so it exercises the street GATE faithfully but not a genuine
four-card turn texture. That is the right scope for a question about the gate,
and it is not evidence about turn boards.

## The pre-existing multiway effect, which is NOT T1's

`_MW_CATCH_TIGHTEN` (`personas_postflop.py:539`, applied at `:969-970`) already
multiplies ACE_HIGH's FOLD merit by `1.15 ** (opponents - 1)`, so naked ace-high
was never byte-identical across opponent counts. That is the entire content of
the `street=none` control block: fold rises with opponents there, before and
after, with T1 contributing nothing. **T1 adds a multiway effect on the CALL
side; the fold side already had one.** Any claim that T1 "introduced multiway
tightening" would be wrong.

## Control — street = None (outside the damp's street gate)

Identical before and after. Fold still rises with opponents; that rise is
`_MW_CATCH_TIGHTEN`, not T1.

| persona | frac | α | opp=1 | opp=2 | opp=3 |
|---|---:|---:|---:|---:|---:|
| calling_station | 0.33 | 0.2481 | 0.0768 | 0.0808 | 0.0936 |
| calling_station | 0.5 | 0.3333 | 0.0888 | 0.1048 | 0.1192 |
| calling_station | 1.0 | 0.5000 | 0.1520 | 0.1712 | 0.1880 |
| calling_station | 1.5 | 0.6000 | 0.2056 | 0.2312 | 0.2632 |
| lag | 0.33 | 0.2481 | 0.2176 | 0.2608 | 0.3000 |
| lag | 0.5 | 0.3333 | 0.3888 | 0.4512 | 0.5160 |
| lag | 1.0 | 0.5000 | 0.5240 | 0.5904 | 0.6408 |
| lag | 1.5 | 0.6000 | 0.6664 | 0.7288 | 0.7784 |
| maniac | 0.33 | 0.2481 | 0.1576 | 0.1976 | 0.2216 |
| maniac | 0.5 | 0.3333 | 0.3392 | 0.3968 | 0.4280 |
| maniac | 1.0 | 0.5000 | 0.4736 | 0.5240 | 0.5688 |
| maniac | 1.5 | 0.6000 | 0.6320 | 0.6824 | 0.7304 |
| nit | 0.33 | 0.2481 | 0.2920 | 0.3264 | 0.3536 |
| nit | 0.5 | 0.3333 | 0.5288 | 0.5656 | 0.6072 |
| nit | 1.0 | 0.5000 | 0.6536 | 0.6976 | 0.7248 |
| nit | 1.5 | 0.6000 | 0.7784 | 0.8056 | 0.8296 |
| passive_fish | 0.33 | 0.2481 | 0.2440 | 0.3000 | 0.3416 |
| passive_fish | 0.5 | 0.3333 | 0.5072 | 0.5800 | 0.6224 |
| passive_fish | 1.0 | 0.5000 | 0.6496 | 0.7176 | 0.7512 |
| passive_fish | 1.5 | 0.6000 | 0.7856 | 0.8240 | 0.8456 |
| tag | 0.33 | 0.2481 | 0.2136 | 0.2520 | 0.3008 |
| tag | 0.5 | 0.3333 | 0.3928 | 0.4544 | 0.5152 |
| tag | 1.0 | 0.5000 | 0.5368 | 0.5864 | 0.6496 |
| tag | 1.5 | 0.6000 | 0.6688 | 0.7288 | 0.7624 |

## The measurement — street = FLOP (inside the damp's street gate)

`before` is the pre-T1 predicate; because this is a facing-a-BET curve and the
old gate was `facing_raise`, the pre-T1 engine is reproduced exactly by
neutralizing `_ACE_HIGH_FLOAT_RAISE_DAMP` to 1.0 (`--pre-t1`). Heads-up
(`opp=1`) is byte-identical before and after and is shown once.

| persona | frac | α | opp=1 (unchanged) | opp=2 before | opp=2 after | Δ | opp=3 before | opp=3 after | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| calling_station | 0.33 | 0.2481 | 0.0768 | 0.0808 | 0.1352 | +0.0544 | 0.0936 | 0.1520 | +0.0584 |
| calling_station | 0.5 | 0.3333 | 0.0888 | 0.1048 | 0.1712 | +0.0664 | 0.1192 | 0.1992 | +0.0800 |
| calling_station | 1.0 | 0.5000 | 0.1520 | 0.1712 | 0.2672 | +0.0960 | 0.1880 | 0.2920 | +0.1040 |
| calling_station | 1.5 | 0.6000 | 0.2056 | 0.2312 | 0.3488 | +0.1176 | 0.2632 | 0.3776 | +0.1144 |
| lag | 0.33 | 0.2481 | 0.2176 | 0.2608 | 0.3416 | +0.0808 | 0.3000 | 0.4000 | +0.1000 |
| lag | 0.5 | 0.3333 | 0.3888 | 0.4512 | 0.5792 | +0.1280 | 0.5160 | 0.6344 | +0.1184 |
| lag | 1.0 | 0.5000 | 0.5240 | 0.5904 | 0.6968 | +0.1064 | 0.6408 | 0.7464 | +0.1056 |
| lag | 1.5 | 0.6000 | 0.6664 | 0.7288 | 0.8064 | +0.0776 | 0.7784 | 0.8480 | +0.0696 |
| maniac | 0.33 | 0.2481 | 0.1576 | 0.1976 | 0.2504 | +0.0528 | 0.2216 | 0.2872 | +0.0656 |
| maniac | 0.5 | 0.3333 | 0.3392 | 0.3968 | 0.4560 | +0.0592 | 0.4280 | 0.5032 | +0.0752 |
| maniac | 1.0 | 0.5000 | 0.4736 | 0.5240 | 0.5968 | +0.0728 | 0.5688 | 0.6432 | +0.0744 |
| maniac | 1.5 | 0.6000 | 0.6320 | 0.6824 | 0.7592 | +0.0768 | 0.7304 | 0.7896 | +0.0592 |
| nit | 0.33 | 0.2481 | 0.2920 | 0.3264 | 0.4688 | +0.1424 | 0.3536 | 0.5104 | +0.1568 |
| nit | 0.5 | 0.3333 | 0.5288 | 0.5656 | 0.7064 | +0.1408 | 0.6072 | 0.7416 | +0.1344 |
| nit | 1.0 | 0.5000 | 0.6536 | 0.6976 | 0.8096 | +0.1120 | 0.7248 | 0.8360 | +0.1112 |
| nit | 1.5 | 0.6000 | 0.7784 | 0.8056 | 0.8888 | +0.0832 | 0.8296 | 0.9040 | +0.0744 |
| passive_fish | 0.33 | 0.2481 | 0.2440 | 0.3000 | 0.4280 | +0.1280 | 0.3416 | 0.4832 | +0.1416 |
| passive_fish | 0.5 | 0.3333 | 0.5072 | 0.5800 | 0.7056 | +0.1256 | 0.6224 | 0.7472 | +0.1248 |
| passive_fish | 1.0 | 0.5000 | 0.6496 | 0.7176 | 0.8088 | +0.0912 | 0.7512 | 0.8496 | +0.0984 |
| passive_fish | 1.5 | 0.6000 | 0.7856 | 0.8240 | 0.8856 | +0.0616 | 0.8456 | 0.9016 | +0.0560 |
| tag | 0.33 | 0.2481 | 0.2136 | 0.2520 | 0.3512 | +0.0992 | 0.3008 | 0.4008 | +0.1000 |
| tag | 0.5 | 0.3333 | 0.3928 | 0.4544 | 0.6000 | +0.1456 | 0.5152 | 0.6504 | +0.1352 |
| tag | 1.0 | 0.5000 | 0.5368 | 0.5864 | 0.7232 | +0.1368 | 0.6496 | 0.7600 | +0.1104 |
| tag | 1.5 | 0.6000 | 0.6688 | 0.7288 | 0.8136 | +0.0848 | 0.7624 | 0.8448 | +0.0824 |

## The measurement — street = TURN (inside the damp's street gate)

`before` is the pre-T1 predicate; because this is a facing-a-BET curve and the
old gate was `facing_raise`, the pre-T1 engine is reproduced exactly by
neutralizing `_ACE_HIGH_FLOAT_RAISE_DAMP` to 1.0 (`--pre-t1`). Heads-up
(`opp=1`) is byte-identical before and after and is shown once.

| persona | frac | α | opp=1 (unchanged) | opp=2 before | opp=2 after | Δ | opp=3 before | opp=3 after | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| calling_station | 0.33 | 0.2481 | 0.0768 | 0.0808 | 0.1360 | +0.0552 | 0.0936 | 0.1528 | +0.0592 |
| calling_station | 0.5 | 0.3333 | 0.0896 | 0.1048 | 0.1712 | +0.0664 | 0.1192 | 0.1992 | +0.0800 |
| calling_station | 1.0 | 0.5000 | 0.1520 | 0.1712 | 0.2672 | +0.0960 | 0.1880 | 0.2920 | +0.1040 |
| calling_station | 1.5 | 0.6000 | 0.2056 | 0.2312 | 0.3488 | +0.1176 | 0.2632 | 0.3784 | +0.1152 |
| lag | 0.33 | 0.2481 | 0.2408 | 0.2768 | 0.3728 | +0.0960 | 0.3248 | 0.4248 | +0.1000 |
| lag | 0.5 | 0.3333 | 0.4208 | 0.4808 | 0.6072 | +0.1264 | 0.5392 | 0.6696 | +0.1304 |
| lag | 1.0 | 0.5000 | 0.5568 | 0.6080 | 0.7224 | +0.1144 | 0.6712 | 0.7768 | +0.1056 |
| lag | 1.5 | 0.6000 | 0.7024 | 0.7520 | 0.8320 | +0.0800 | 0.7896 | 0.8648 | +0.0752 |
| maniac | 0.33 | 0.2481 | 0.1904 | 0.2208 | 0.2912 | +0.0704 | 0.2624 | 0.3320 | +0.0696 |
| maniac | 0.5 | 0.3333 | 0.3920 | 0.4224 | 0.5016 | +0.0792 | 0.4712 | 0.5640 | +0.0928 |
| maniac | 1.0 | 0.5000 | 0.5216 | 0.5680 | 0.6520 | +0.0840 | 0.6080 | 0.7024 | +0.0944 |
| maniac | 1.5 | 0.6000 | 0.6792 | 0.7312 | 0.7904 | +0.0592 | 0.7616 | 0.8176 | +0.0560 |
| nit | 0.33 | 0.2481 | 0.2920 | 0.3280 | 0.4720 | +0.1440 | 0.3536 | 0.5136 | +0.1600 |
| nit | 0.5 | 0.3333 | 0.5344 | 0.5664 | 0.7096 | +0.1432 | 0.6080 | 0.7424 | +0.1344 |
| nit | 1.0 | 0.5000 | 0.6560 | 0.7008 | 0.8112 | +0.1104 | 0.7264 | 0.8368 | +0.1104 |
| nit | 1.5 | 0.6000 | 0.7824 | 0.8080 | 0.8888 | +0.0808 | 0.8296 | 0.9040 | +0.0744 |
| passive_fish | 0.33 | 0.2481 | 0.2560 | 0.3032 | 0.4368 | +0.1336 | 0.3424 | 0.4832 | +0.1408 |
| passive_fish | 0.5 | 0.3333 | 0.5304 | 0.5904 | 0.7208 | +0.1304 | 0.6264 | 0.7528 | +0.1264 |
| passive_fish | 1.0 | 0.5000 | 0.6704 | 0.7240 | 0.8184 | +0.0944 | 0.7544 | 0.8512 | +0.0968 |
| passive_fish | 1.5 | 0.6000 | 0.7992 | 0.8304 | 0.8880 | +0.0576 | 0.8480 | 0.9032 | +0.0552 |
| tag | 0.33 | 0.2481 | 0.2296 | 0.2632 | 0.3632 | +0.1000 | 0.3048 | 0.4136 | +0.1088 |
| tag | 0.5 | 0.3333 | 0.4264 | 0.4704 | 0.6216 | +0.1512 | 0.5256 | 0.6640 | +0.1384 |
| tag | 1.0 | 0.5000 | 0.5552 | 0.5992 | 0.7384 | +0.1392 | 0.6576 | 0.7672 | +0.1096 |
| tag | 1.5 | 0.6000 | 0.6920 | 0.7392 | 0.8304 | +0.0912 | 0.7712 | 0.8560 | +0.0848 |

## Flop against turn — the same story, and not averaged

The two gated streets are reported separately above because averaging them would
hide a difference if there were one. There is not one. Across all 48 moved cells
per street the flop deltas run +0.0528 to +0.1568 (mean +0.0977) and the turn
deltas +0.0552 to +0.1600 (mean +0.1009). Every cell moves in the same
direction on both streets, the largest flop-versus-turn disagreement in any
single cell is 0.0200, and the binding cell is passive_fish at ½-pot and three
opponents on both. Heads-up is exactly unchanged on both streets, at all 24
cells each.

## Reading it

- **Every cell moves in one direction and only at more than one opponent.**
  Heads-up is exactly unchanged at all 24 cells on each gated street, which is
  acceptance criterion 5 measured rather than asserted.
- **α is exceeded before the change and by more after it, and that is not by
  itself a failure.** At one opponent, on the untouched engine, 15 of the 24
  cells are already above α (nit 0.2920 vs 0.2481 facing ⅓-pot; passive fish
  0.5072 vs 0.3333 facing ½-pot). A bound the shipped engine already crosses
  cannot be the instrument that judges a change to it.
- **Why the α contract excludes this bucket, as the code states it.** α = f/(1+f)
  is the frequency at which a defender may fold and still make a balanced
  bettor's bluffs break even, and the identity applies to a range whose job is
  to catch those bluffs. `_CATCHER_BUCKETS` at
  `test_personas_postflop.py:622` excludes ace-high on the ground that it loses
  to part of the bluff half. The A1 guardrail is also explicit that α is a
  CEILING and never a floor (`test_personas_postflop.py:670`) — no lower bound on
  any fold rate exists in that file and none was added here. **Whether α should
  be asserted over ace-high at all is an open question for the owner**; this
  file reports the measurement and adds no assertion either way.
- **A collision the owner should see.** The `_CALL_BASE` block at
  `personas_postflop.py:243` records the W3R-3 refutation of a flat global cut,
  computing that at an effective base of 0.22 the fish's arrival-range
  fold-to-bet reaches 0.408 against an α+0.05 ceiling of 0.383 at ½-pot. T1
  ships exactly 0.22 effective (0.40 × 0.55) on multiway flop and turn
  facing-a-bet nodes. The refutation still stands as written — against a FLAT
  GLOBAL cut at every opponent count — but the two have not been reconciled by
  measurement, and this table is not that reconciliation: it is a
  uniform-deal naked-ace-high range, not the fish's arrival range.
- **What is and is not replaced.** W3R-6 claimed structural safety: a
  facing-a-raise gate cannot reach the facing-a-bet curve. T1 deletes that.
  `test_ace_high_multiway_damp_gate_lock` pins heads-up facing a bet, the river
  at any opponent count, and ace-high WITH a draw;
  `test_bluff_catcher_alpha_contract_untouched_at_multiple_opponents` pins the
  catcher range at one, two and three opponents. Together they are NARROWER than
  the old prose, which asserted every facing-a-bet decision for every bucket.
  Nothing replaces it at that width, and nothing should pretend to.

