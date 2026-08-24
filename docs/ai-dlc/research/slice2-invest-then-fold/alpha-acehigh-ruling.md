# The α ceiling on naked ace-high, after the owner's 2026-08-19 ruling

> ⛔ **WITHDRAWN 2026-08-24 — the ruling this document applies is no longer in
> force. Read this as a historical measurement record, never as current law.**
>
> On 2026-08-24 the owner ruled that **α = f/(1+f) bounds a defender's WHOLE
> RANGE and nothing smaller**, and **withdrew** the 2026-08-19 ruling that it
> bounds the `ACE_HIGH` hand-strength class. Applied to one class the identity is
> wrong in both directions at once — too strict at large bets, too loose at small
> ones. **No test, ticket, band or review finding may assert a per-class α
> obligation again.**
>
> **Read the replacement here:** theory contract
> `../../contracts/persona-realism-theory-contract.md`, amendment **A9** (the
> ruling and its scope) and §9 ledger entry 18 (the index of all six 2026-08-24
> decisions). The evidence behind it is the slice-3 finding ledger
> `../../ledger/flywheel-slice3-calldown.md`, items **Filed 9 and Filed 10**,
> which are closed together.
>
> **The guard test named below no longer exists.**
> `test_ace_high_alpha_holds_for_the_station_pre_river` was deleted on 2026-08-24
> together with the river guard ticket S3-T4 later added and that guard's
> non-vacuity proof — deleted rather than softened, because softening a guard
> that measures a quantity the contract does not bound is the exact move the
> W3R-1 rule exists to prevent. `_ACE_HIGH_RIVER_CALL_DAMP` is untouched and
> stays at 0.06; it is a lever, not a bound.
>
> **What still stands.** Everything below is a valid record of what was measured
> on this engine, at these nodes, under the old ruling. The numbers reproduce and
> the reasoning about *why* the cells read as they do is unaffected — only the
> obligation they were measured against has been withdrawn. Nothing below has
> been rewritten. The same applies to the companion measurement script
> `alpha_acehigh_measure.py` beside this file, which still runs and still
> reproduces these tables, and which now carries the same withdrawal banner in
> its docstring.

**Bottom line: under the ruling that α = f/(1+f) DOES bound the ACE_HIGH bucket,
today's engine breaks the bound nearly everywhere, and the calling station on
pre-river streets is the only part of the surface that holds. Above the river,
15 to 20 of 24 persona-and-size cells exceed α depending on street and opponent
count. On the RIVER every one of the 72 cells exceeds it, at every opponent
count. T3's new river call leg does not close a single α cell — it cuts the
river fold rate by up to 42 points and the whole map still violates, because
even with the leg fully undamped 18 of 24 cells are still over. Closing the
river cells needs the ace-high river call merit multiplied by about 3, roughly
fifty times the shipped constant, which is far outside what the frozen
went-to-showdown bands admit. So this document ships the baseline and one guard
test, and NO engine change.**

## What was ruled, and what this document is

The owner ruled on **2026-08-19** that the α bound **applies to the ACE_HIGH
strength bucket**. That answers the question T1's build round referred up
(`docs/ai-dlc/ledger/phase3-invest-then-fold.md`, finding 3 and the first open
item), which the engine had been reporting rather than settling.

Applying the ruling as a runtime calibration is **out of scope here and is not
attempted**. Extending the grader's `_calibrate_catcher_fold` treatment to
ace-high would raise ace-high call rates and would breach the frozen
went-to-showdown bands that capped T3's constant at 0.06 — a separate owner
decision, in progress. What this document is instead:

1. the measured violation map, so the future engine-fix ticket has a baseline;
2. the reasoning for the one assertion that can honestly be pinned today.

The guard test is
`backend/tests/test_personas_postflop.py::test_ace_high_alpha_holds_for_the_station_pre_river`.

## How it was measured

`docs/ai-dlc/research/slice2-invest-then-fold/alpha_acehigh_measure.py`, beside
this file, prints every table below. Run it from `backend/`:

    cd backend && PYTHONPATH=. python \
        ../docs/ai-dlc/research/slice2-invest-then-fold/alpha_acehigh_measure.py

The node is the α guard's own (`catcher_fold_by_size`): pot-before-bet 6bb,
100bb stacks, a fresh aggressor betting `frac × 6bb`, deal seed 20260721,
per-cell decision seed `20260721 + 100·persona_index + frac_index`, n = 1250.
Three things differ from that fixture — the range filter is `StrengthBucket
.ACE_HIGH` with `DrawCategory.NONE`, `opponents` is swept over 1/2/3 instead of
pinned to 1, and `street` is passed explicitly.

**Passing `street` is the trap this measurement exists to avoid.** Both standing
price fixtures omitted it until PR #203 made them street-aware, so they measured
at `street=None`, outside every street gate. A first version of T1's α table
copied them and produced byte-identical before-and-after numbers, i.e. measured
nothing.

**Board length is not a variable for this bucket, and that is measured rather
than assumed.** Section 4 below reports the largest difference between a 3-card
and a genuine 5-card board over the 24 river cells at one opponent: **0.0000**.
The facing branch reads ace-high's merits off the bucket, the draw category, the
price, the persona and the opponent count; the only board-dependent damps in
`personas_postflop.py` gate on made pairs, which excludes this bucket. So the
river numbers are river numbers, not an artifact of re-using flop boards.

**One honest limit on the reach of the whole table.** This is a uniform-deal
naked-ace-high range at a single node, not any persona's real arrival range and
not a closed-loop population statistic. It bounds what the *decision rule* does
on this bucket. It does not say how often bots arrive there.

## 1. The violation map

### street = None

| persona | frac | α | opp=1 | opp=2 | opp=3 |
|---|---:|---:|---:|---:|---:|
| calling_station | 0.33 | 0.2481 | 0.0768 | 0.0808 | 0.0936 |
| calling_station | 0.5 | 0.3333 | 0.0888 | 0.1048 | 0.1192 |
| calling_station | 1.0 | 0.5000 | 0.1520 | 0.1712 | 0.1880 |
| calling_station | 1.5 | 0.6000 | 0.2056 | 0.2312 | 0.2632 |
| lag | 0.33 | 0.2481 | 0.2176 | **0.2608** | **0.3000** |
| lag | 0.5 | 0.3333 | **0.3888** | **0.4512** | **0.5160** |
| lag | 1.0 | 0.5000 | **0.5240** | **0.5904** | **0.6408** |
| lag | 1.5 | 0.6000 | **0.6664** | **0.7288** | **0.7784** |
| maniac | 0.33 | 0.2481 | 0.1576 | 0.1976 | 0.2216 |
| maniac | 0.5 | 0.3333 | **0.3392** | **0.3968** | **0.4280** |
| maniac | 1.0 | 0.5000 | 0.4736 | **0.5240** | **0.5688** |
| maniac | 1.5 | 0.6000 | **0.6320** | **0.6824** | **0.7304** |
| nit | 0.33 | 0.2481 | **0.2920** | **0.3264** | **0.3536** |
| nit | 0.5 | 0.3333 | **0.5288** | **0.5656** | **0.6072** |
| nit | 1.0 | 0.5000 | **0.6536** | **0.6976** | **0.7248** |
| nit | 1.5 | 0.6000 | **0.7784** | **0.8056** | **0.8296** |
| passive_fish | 0.33 | 0.2481 | 0.2440 | **0.3000** | **0.3416** |
| passive_fish | 0.5 | 0.3333 | **0.5072** | **0.5800** | **0.6224** |
| passive_fish | 1.0 | 0.5000 | **0.6496** | **0.7176** | **0.7512** |
| passive_fish | 1.5 | 0.6000 | **0.7856** | **0.8240** | **0.8456** |
| tag | 0.33 | 0.2481 | 0.2136 | **0.2520** | **0.3008** |
| tag | 0.5 | 0.3333 | **0.3928** | **0.4544** | **0.5152** |
| tag | 1.0 | 0.5000 | **0.5368** | **0.5864** | **0.6496** |
| tag | 1.5 | 0.6000 | **0.6688** | **0.7288** | **0.7624** |

### street = FLOP

| persona | frac | α | opp=1 | opp=2 | opp=3 |
|---|---:|---:|---:|---:|---:|
| calling_station | 0.33 | 0.2481 | 0.0768 | 0.1352 | 0.1520 |
| calling_station | 0.5 | 0.3333 | 0.0888 | 0.1712 | 0.1992 |
| calling_station | 1.0 | 0.5000 | 0.1520 | 0.2672 | 0.2920 |
| calling_station | 1.5 | 0.6000 | 0.2056 | 0.3488 | 0.3776 |
| lag | 0.33 | 0.2481 | 0.2176 | **0.3416** | **0.4000** |
| lag | 0.5 | 0.3333 | **0.3888** | **0.5792** | **0.6344** |
| lag | 1.0 | 0.5000 | **0.5240** | **0.6968** | **0.7464** |
| lag | 1.5 | 0.6000 | **0.6664** | **0.8064** | **0.8480** |
| maniac | 0.33 | 0.2481 | 0.1576 | **0.2504** | **0.2872** |
| maniac | 0.5 | 0.3333 | **0.3392** | **0.4560** | **0.5032** |
| maniac | 1.0 | 0.5000 | 0.4736 | **0.5968** | **0.6432** |
| maniac | 1.5 | 0.6000 | **0.6320** | **0.7592** | **0.7896** |
| nit | 0.33 | 0.2481 | **0.2920** | **0.4688** | **0.5104** |
| nit | 0.5 | 0.3333 | **0.5288** | **0.7064** | **0.7416** |
| nit | 1.0 | 0.5000 | **0.6536** | **0.8096** | **0.8360** |
| nit | 1.5 | 0.6000 | **0.7784** | **0.8888** | **0.9040** |
| passive_fish | 0.33 | 0.2481 | 0.2440 | **0.4280** | **0.4832** |
| passive_fish | 0.5 | 0.3333 | **0.5072** | **0.7056** | **0.7472** |
| passive_fish | 1.0 | 0.5000 | **0.6496** | **0.8088** | **0.8496** |
| passive_fish | 1.5 | 0.6000 | **0.7856** | **0.8856** | **0.9016** |
| tag | 0.33 | 0.2481 | 0.2136 | **0.3512** | **0.4008** |
| tag | 0.5 | 0.3333 | **0.3928** | **0.6000** | **0.6504** |
| tag | 1.0 | 0.5000 | **0.5368** | **0.7232** | **0.7600** |
| tag | 1.5 | 0.6000 | **0.6688** | **0.8136** | **0.8448** |

### street = TURN

| persona | frac | α | opp=1 | opp=2 | opp=3 |
|---|---:|---:|---:|---:|---:|
| calling_station | 0.33 | 0.2481 | 0.0768 | 0.1360 | 0.1528 |
| calling_station | 0.5 | 0.3333 | 0.0896 | 0.1712 | 0.1992 |
| calling_station | 1.0 | 0.5000 | 0.1520 | 0.2672 | 0.2920 |
| calling_station | 1.5 | 0.6000 | 0.2056 | 0.3488 | 0.3784 |
| lag | 0.33 | 0.2481 | 0.2408 | **0.3728** | **0.4248** |
| lag | 0.5 | 0.3333 | **0.4208** | **0.6072** | **0.6696** |
| lag | 1.0 | 0.5000 | **0.5568** | **0.7224** | **0.7768** |
| lag | 1.5 | 0.6000 | **0.7024** | **0.8320** | **0.8648** |
| maniac | 0.33 | 0.2481 | 0.1904 | **0.2912** | **0.3320** |
| maniac | 0.5 | 0.3333 | **0.3920** | **0.5016** | **0.5640** |
| maniac | 1.0 | 0.5000 | **0.5216** | **0.6520** | **0.7024** |
| maniac | 1.5 | 0.6000 | **0.6792** | **0.7904** | **0.8176** |
| nit | 0.33 | 0.2481 | **0.2920** | **0.4720** | **0.5136** |
| nit | 0.5 | 0.3333 | **0.5344** | **0.7096** | **0.7424** |
| nit | 1.0 | 0.5000 | **0.6560** | **0.8112** | **0.8368** |
| nit | 1.5 | 0.6000 | **0.7824** | **0.8888** | **0.9040** |
| passive_fish | 0.33 | 0.2481 | **0.2560** | **0.4368** | **0.4832** |
| passive_fish | 0.5 | 0.3333 | **0.5304** | **0.7208** | **0.7528** |
| passive_fish | 1.0 | 0.5000 | **0.6704** | **0.8184** | **0.8512** |
| passive_fish | 1.5 | 0.6000 | **0.7992** | **0.8880** | **0.9032** |
| tag | 0.33 | 0.2481 | 0.2296 | **0.3632** | **0.4136** |
| tag | 0.5 | 0.3333 | **0.4264** | **0.6216** | **0.6640** |
| tag | 1.0 | 0.5000 | **0.5552** | **0.7384** | **0.7672** |
| tag | 1.5 | 0.6000 | **0.6920** | **0.8304** | **0.8560** |

### street = RIVER

| persona | frac | α | opp=1 | opp=2 | opp=3 |
|---|---:|---:|---:|---:|---:|
| calling_station | 0.33 | 0.2481 | **0.5584** | **0.5960** | **0.6256** |
| calling_station | 0.5 | 0.3333 | **0.6520** | **0.6896** | **0.7168** |
| calling_station | 1.0 | 0.5000 | **0.7520** | **0.7776** | **0.8072** |
| calling_station | 1.5 | 0.6000 | **0.7936** | **0.8080** | **0.8344** |
| lag | 0.33 | 0.2481 | **0.6392** | **0.7200** | **0.7944** |
| lag | 0.5 | 0.3333 | **0.8048** | **0.8648** | **0.9016** |
| lag | 1.0 | 0.5000 | **0.8848** | **0.9224** | **0.9464** |
| lag | 1.5 | 0.6000 | **0.9336** | **0.9624** | **0.9744** |
| maniac | 0.33 | 0.2481 | **0.5176** | **0.5888** | **0.6400** |
| maniac | 0.5 | 0.3333 | **0.7264** | **0.7776** | **0.8232** |
| maniac | 1.0 | 0.5000 | **0.8336** | **0.8720** | **0.8944** |
| maniac | 1.5 | 0.6000 | **0.9024** | **0.9216** | **0.9416** |
| nit | 0.33 | 0.2481 | **0.8432** | **0.8840** | **0.9000** |
| nit | 0.5 | 0.3333 | **0.9488** | **0.9600** | **0.9664** |
| nit | 1.0 | 0.5000 | **0.9672** | **0.9736** | **0.9768** |
| nit | 1.5 | 0.6000 | **0.9832** | **0.9856** | **0.9888** |
| passive_fish | 0.33 | 0.2481 | **0.7640** | **0.8528** | **0.8936** |
| passive_fish | 0.5 | 0.3333 | **0.9072** | **0.9400** | **0.9528** |
| passive_fish | 1.0 | 0.5000 | **0.9368** | **0.9584** | **0.9688** |
| passive_fish | 1.5 | 0.6000 | **0.9648** | **0.9768** | **0.9840** |
| tag | 0.33 | 0.2481 | **0.6800** | **0.7544** | **0.8232** |
| tag | 0.5 | 0.3333 | **0.8432** | **0.8928** | **0.9224** |
| tag | 1.0 | 0.5000 | **0.9008** | **0.9336** | **0.9472** |
| tag | 1.5 | 0.6000 | **0.9480** | **0.9664** | **0.9776** |

## 2. Cells above α, per street and opponent count

| street | opp=1 | opp=2 | opp=3 |
|---|---:|---:|---:|
| street = None | 15/24 | 19/24 | 19/24 |
| street = FLOP | 15/24 | 20/24 | 20/24 |
| street = TURN | 17/24 | 20/24 | 20/24 |
| street = RIVER | 24/24 | 24/24 | 24/24 |

## 3. T3's river call leg against α, swept over its constant

| `_ACE_HIGH_RIVER_CALL_DAMP` | cells above α at opp=1 | station ⅓-pot | nit ½-pot |
|---|---:|---:|---:|
| 0.0 | 24/24 | 0.9744 | 0.9832 |
| 0.06 (shipped) | 24/24 | 0.5584 | 0.9488 |
| 0.45 | 20/24 | 0.1432 | 0.7168 |
| 1.0 | 18/24 | 0.0768 | 0.5344 |
| 1.5 | 12/24 | 0.0568 | 0.4400 |
| 2.0 | 6/24 | 0.0432 | 0.3752 |
| 2.5 | 1/24 | 0.0360 | 0.3320 |
| 3.0 | 0/24 | 0.0312 | 0.2936 |

## 4. Board length is not a variable for this bucket

Largest |3-card − 5-card| river fold-rate difference over the 24 opp=1 cells: 0.0000

## 5. Reading it

**T1's headline figure reproduces exactly.** `alpha-multiway-t1.md` reported
naked ace-high above α at **15 of 24 cells at one opponent on the untouched
engine**, and section 1's `street = None` column at `opp=1` reads 15/24 with
every individual cell matching that file to the fourth decimal (nit 0.2920 vs
0.2481 facing ⅓-pot; passive fish 0.5072 vs 0.3333 at ½-pot). The engine has
changed twice since — T1 and T3 — and neither touched this column, which is what
a control is for.

**Three streets read differently, for two separate mechanical reasons, and
neither is noise.**

- `street = None` and `street = FLOP` are identical at one opponent (15/24) and
  diverge from two opponents on (19/24 vs 20/24). That divergence is T1: its
  damp is gated `street in (FLOP, TURN)` and `facing_raise or opponents > 1`, so
  heads-up facing a bet is outside it by construction.
- `street = TURN` reads two cells worse than FLOP even at one opponent (17/24).
  That is not T1 — it is `_STREET_AGG_MULT` (FLOP 1.0, TURN 0.6, RIVER 0.33)
  scaling `bluff_mass`, which is the only input to ace-high's bluff-raise leg.
  A smaller raise merit means normalization hands a larger share to FOLD, so the
  fold rate climbs on later streets without any fold-side term moving.
- **Every added opponent makes it worse**, at every street. `_MW_CATCH_TIGHTEN`
  multiplies ace-high's fold merit by `1.15 ** (opponents - 1)` and has done
  since long before T1. The α bound as ruled is therefore breached hardest
  exactly where the engine's multiway logic is most active.

**The river is a wipeout, and T3 is not why.** All 24 cells exceed α at one
opponent, and all 72 across the three opponent counts. Section 3 sweeps T3's
constant to separate the leg from the ceiling:

- At **0.0** — the pre-T3 engine, where ace-high's river call merit was
  hard-zeroed with AIR's — the map is 24/24 over α, with fold rates up to
  0.9960.
- At the **shipped 0.06** the map is still **24/24 over α**. The leg is not
  cosmetic in level (the calling station's ⅓-pot river fold falls 0.9744 →
  0.5584, a 42-point cut) but it closes **zero α cells**.
- At **1.0**, the leg with no damp at all, **18 of 24 cells are still over α**.
  So the shipped constant is not what puts the river outside the bound. The
  bound is outside the reach of this branch's whole range.
- Zero cells violate only at a multiplier of about **3.0** — an effective
  ace-high river call base near 1.2, against the 0.024 that ships
  (`_CALL_BASE[ACE_HIGH]` 0.40 × 0.06). **Roughly fifty times the shipped
  value.** The frozen went-to-showdown bands already refused 0.45; they will
  not admit 3.0. That is the size of the gap between the ruling and the bands,
  stated in the currency of the one constant that could close it.

**What passes, and it is one persona.** The `calling_station` is α-compliant on
naked ace-high at all four prices, at one, two and three opponents, on
`street=None`, FLOP and TURN — 36 cells, no exceptions. No other persona has a
clean row on any street; no street has a clean column; the river has no clean
cell for anyone. The binding station cell is TURN, three opponents, ⅓-pot, at
**+9.53pp of headroom** (0.1528 against α 0.2481), which is about 7.8 binomial
standard errors at n = 1250.

That subset is what the guard test pins, and the honest description of it is a
**tripwire on the one part of the surface that still holds**, not a coverage
claim. It is worth pinning because the quantity is live and moving in the wrong
direction: T1 raised the station's own multiway flop fold rate by up to +0.1176
in a single slice (0.2312 → 0.3488 at 1.5× and two opponents), spending about a
third of that cell's headroom. Two more slices of that size and the last
compliant persona breaches too.

## 6. What this does NOT settle

- **No engine change is proposed or made here.** The violation map is a
  baseline, not a target list. Nothing in it is asserted as expected or correct.
- **The violated cells are deliberately NOT pinned**, in either direction. An
  expected-failure pin on a cell the ruling says is wrong would entrench the
  violation as the engine's specification, and a one-sided ratchet on 60-plus
  cells would be a re-record burden on every future slice for no protection the
  guard above does not already give.
- **The stale prose in `personas_postflop.py` is disclosed, not fixed.** The
  `_CALL_BASE` block at lines 295-320 still reads "WHETHER α SHOULD BE ASSERTED
  OVER ACE-HIGH AT ALL IS AN OPEN QUESTION referred to the owner". The owner has
  now ruled and that sentence is false. Correcting it belongs to the ticket that
  next edits the engine, because this slice ships no engine change at all and an
  engine diff here would have to be reviewed as one. Same for the matching open
  item in `docs/ai-dlc/ledger/phase3-invest-then-fold.md`.
- **The reconciliation between the ruling and the frozen went-to-showdown bands
  is the owner's**, and section 3 is the arithmetic it needs: closing the river
  costs about a 50× move in a constant two bands already refused at 7.5×.
