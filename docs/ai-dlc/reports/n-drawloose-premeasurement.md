# N-DRAWLOOSE — pre-spec measurement

> ## ⛔ CORRECTIONS — read before citing anything below
>
> Sections 1-4 and 6 stand. **§5 and §7 were failed by both reviewers and are superseded**
> by §9 at the foot of this file. Specifically:
>
> 1. **§5.1's impossibility claim is FALSE.** The raise-share invariant *is* recoverable —
>    set `rscale := C(L)/C(ref)`. Both reviewers refuted it independently; one built and ran
>    it. The owner chose that counter-formulation (option B) at Gate 2. The true statement is
>    "unrecoverable while the raise leg keeps its shipped `looseness/continue_ref` form".
> 2. **§5's failure table, §5.2 and §5.3 quote the STRONG+WEAK variant**, which the spec had
>    already rejected. Real STRONG-only numbers: `_PRE_M3_FIRES` UTG2¹ 74 → **70** (not 84);
>    coverage fails on the **`total`** assertion, 1288 → **1233**, graded **323** (not
>    "total equal, graded 332").
> 3. **§5.1's explanation was fabricated.** It said the grid's `weak_draw` cells "are
>    classified by the engine as STRONG". They are not — an existing passing test
>    (`test_personas_postflop.py:7104-7132`) asserts the templates classify as labelled.
> 4. **§5.2's causal story is withdrawn.** The fish band is a coin-flip tripwire at HEAD
>    (breaches on 2 of 8 reseeds); the paired effect of the change is mean −0.0020 with the
>    sign flipping twice. It is not a band this slice broke.
> 5. **§7's turn claim is withdrawn.** 0.18 is `_draw_equity`'s flat nine-out proxy, not the
>    hand: a 15-out combo draw has ≈15/46 = 32.6 % on the turn, which **beats** the 28.6 %
>    price. The proxy defect is now filed as `N-DRAWEQUITY`.
>
> Root cause of 2 and 3: the STRONG+WEAK variant was measured first, its failure detail
> harvested, the worktree switched to STRONG-only, re-run — and only the summary line read.
> Both runs said "5 failed", which is not evidence the five are the same five.

**Date:** 2026-08-04 · **Base:** `origin/main` = `b0a6a4e` (R9-LOOSEFIT rev 4, PR #167,
verified byte-identical to the 1419-green tip `b7faa01`).
**Method:** three detached worktrees off `b0a6a4e` — `wt-drawbase` (unchanged),
`wt-drawmeas` (rev-1 candidate, call side only) and `wt-drawalt` (**the shipping variant**,
option B in branch form). None is a build branch; all are detached and retained until the
build lands, then removed. `wt-drawalt` is the reference implementation for ticket T1. Node readings use a price-asserting instrument modelled on
`_r9lf_priced_dist`: the engine's own `_price_factor` is wrapped and the faced fraction
it computed is compared to the fraction the node declares, so a mispriced reading cannot
leave the function. It fired twice during this work and rejected two of my own nodes
(a rounded `0.6667`, and a node I had labelled ½-pot that the engine priced at pot).

---

## 1. The defect, re-measured

`personas_postflop.py:979`

```python
call_merit = (call_base + _DRAW_CALL_BONUS[draw]) * looseness
```

`looseness` is the persona's `call_looseness` (falling back to `stickiness`). It scales
the draw bonus as well as the made-hand base, so tightening an archetype tightens it
against hands nobody folds. Confirmed at the trace node
(`node_trace.py:188`, JhTh on 9h8c2h, ⅔-pot, HU, SPR 10):

| persona | dial | P(fold) on a 15-out combo draw |
|---|---|---|
| nit | 0.45 | **0.4217** |
| passive_fish | 0.42 | 0.4173 |
| tag | 0.60 | 0.2504 |
| lag | 0.55 | 0.2277 |
| maniac | 0.55 | 0.1682 |
| calling_station | 4.00 | 0.0915 |

Price at that node: 28.6 % equity needed; the heuristic draw equity is 0.36. The nit is
the roster's heaviest folder of a hand that is a favourite to make by the river.

## 2. Shape comparison (all six personas, correctly priced)

Measured without editing the engine, by substituting `_DRAW_CALL_BONUS` with
`BONUS · g(L)/L`, which is algebraically exact for any `g`.

| shape | nit (was 0.4217) | calling_station (was 0.0915) |
|---|---|---|
| `g = 1` — exempt the dial entirely | 0.2838 | **0.2156 — regression** |
| `g = max(L, 1)` — floor at 1 | 0.2838 | 0.0915 — unchanged |
| `g = √L` — half force | 0.3528 | 0.1485 |

The plain exemption is disqualified: the calling station is the one persona whose dial
is above 1 (4.0), so removing the dial from the draw bonus *takes mass away* from the
bot that is supposed to call everything. The floor is identical to the exemption for
every persona below 1 and a no-op for the station. **Chosen: `g = max(L, 1)`.**

## 3. Scope: STRONG draws only

The engine's own comment at `:768-776` names `_DRAW_CALL_BONUS[WEAK]` as "the
un-equity-gated F7 defect" and records that a fix "must depend on F7's separate equity
gate landing first". Exempting the WEAK bonus from a tightening dial makes an
already-disclosed defect larger — naked gutshots would continue still more. So the
floor applies to `DrawCategory.STRONG` only; WEAK keeps today's behaviour and stays
with F7. Measured effect of the narrowing on the one band it moves: fish flop
0.33×pot fold **0.1761 (STRONG+WEAK) → 0.1933 (STRONG only)**.

## 4. Candidate change

```python
_draw_scale = max(looseness, 1.0) if draw is DrawCategory.STRONG else looseness
call_merit = call_base * looseness + _DRAW_CALL_BONUS[draw] * _draw_scale
```

plus the mirrored site inside the B5b SPR-commit damp (`:1098`), which subtracts
`_DRAW_CALL_BONUS[draw] * looseness * removed` and must subtract exactly what was
added or the damp over- or under-removes.

## 5. Full-suite result (candidate applied, 1419 collected)

**5 failed, 1414 passed, 1 skipped.** Identical failure set for both the STRONG+WEAK
and the STRONG-only variants.

| # | test | class |
|---|---|---|
| 1 | `test_nlogit_g1_orthogonality_raise_share_is_lever_invariant` | **hard blocker, predicted** |
| 2 | `test_persona_stats_byte_identical_after_log_refactor` (`_GOLDEN_STATS_N200`) | re-recordable fixture |
| 3 | `test_limper_coverage_fires_on_organic_play` (`_PRE_M3_FIRES`) | re-recordable fixture |
| 4 | `test_coverage_never_regresses` | **ratchet DECREASE — not a re-record** |
| 5 | `test_t4_flop_absolute_band[passive_fish-0.33-0.2-0.38]` | **authored band breach** |

Gates that were flagged at risk and **passed**: `test_r9lf_gsweep_nit_folds_more_than_tag_...`
(last slice's 970-cell population sweep), `test_r9lf_gnode_...`, `test_weak_draw_stops_stacking_off_at_high_commitment`,
`test_strong_draw_potcommitted_still_jams`, the whole R9-DEFENCE-a line-invariance suite,
and all 23 frozen vectors in `test_price_tail.py`. The contract map could not score the
population sweep statically; it is now measured green.

### 5.1 Failure 1 — the raise-share invariant, and why no fix can keep it

`test_personas_postflop.py:7135-7188` pins, to `1e-12`, that sweeping `call_looseness`
never changes `P(raise)/(P(call)+P(raise))`. That holds today only because CALL and
RAISE are *both* exactly proportional to `looseness` (RAISE via N-LOGIT's
`rscale = looseness/continue_ref`), so the dial cancels from the ratio. Once CALL is
`call_base·L + BONUS`, it is affine in `L` rather than proportional, and `L` cannot
cancel unless `BONUS == 0` — which is false exactly on draw cells.

Exempting the RAISE bonus too does **not** restore it: that gives `C = aL + b` against
`R = cL + d`, still not proportional. **The invariant is unrecoverable on draw nodes
under any shape of this fix.** Observed failures are all and only draw cells:

```
nit    0.0976  weak_draw/flop   price=4.0  x0.25
tag    0.2737  strong_draw/flop price=2.0  x0.25
lag    0.2767  strong_draw/flop price=2.0  x0.25
maniac 0.2992  weak_draw/flop   price=6.0  x0.25
fish   0.1108  weak_draw/flop   price=6.0  x4.0
```

(Note: `weak_draw` cells appear even under the STRONG-only scope, because the grid's
`weak_draw` template is classified by the engine, and the failing readings come from the
cells the engine calls STRONG. The gate re-scope must be written against
`DrawCategory`, not the grid's template name — see the spec's T2 note.)

### 5.2 Failure 5 — the fish band was already resting on the defect

`FLOP_BANDS` (`test_arrival_range_ftc.py:354-364`) requires `passive_fish` to fold
20-38 % to a ⅓-pot flop bet, sourced from "audit §5/F10", owner-included at W3R-2. The
file states these bands "assert stably at this N across repeated seeds", so this is a
behavioural reading, not sampling noise.

| | fish flop 0.33×pot fold |
|---|---|
| HEAD `b0a6a4e` | **0.2077** (floor 0.20 — margin **+0.0077**) |
| STRONG-only fix | **0.1933** |
| STRONG+WEAK fix | 0.1761 |

The band had 0.008 of headroom before this slice existed.

⅓-pot flop fold rate, by variant — **the two fix columns are different runs and must not
be read as one series**:

| persona | HEAD | STRONG+WEAK | STRONG-only |
|---|---|---|---|
| nit | 0.1400 | 0.1200 | 0.1400 |
| tag | 0.1083 | 0.1042 | not measured |
| lag | 0.1545 | 0.1500 | not measured |
| maniac | 0.1232 | 0.1066 | not measured |
| passive_fish | 0.2077 | 0.1761 | **0.1933** |

The fish moves furthest because its dial is the lowest below 1 (0.42), so it had the
most bonus suppressed. **The band's floor was being met partly by the very over-folding
this slice removes.** Its OVERBET row (0.60-0.80) still passes at 0.6392, so only the
small-price end moves. The three "not measured" cells are a known gap: only the fish row
is gated, so the STRONG-only rerun captured the gated persona and the nit; a builder
re-deriving the band should fill the column.

Calling-station rows are **byte-identical to four decimals** on every street, as the
floor-at-1 choice intends.

### 5.3 Failure 4 — coverage ratchet

`test_coverage_never_regresses` asserts `total` exactly equal (passed — the hand stream
did not drift) and `graded` monotone non-decreasing: **332 < 335**. A decrease is not a
re-record under the fixture protocol. Three graded decisions fewer, cause not yet
attributed; the initiative has adjudicated coverage dips to the mapper track before
(R10-PRE1/#137, wave-3, R10-TAIL-a1).

## 6. Gate evidence — self-difference by node class

The nit pack at `call_looseness` 0.45 against the same pack rebuilt at 0.60, at
correctly-priced facing nodes:

| class | node | HEAD self | with fix |
|---|---|---|---|
| DRAW | D1 combo draw, flop, ⅔-pot | +0.0682 | +0.0111 |
| DRAW | D2 flush draw, flop, pot | +0.0678 | +0.0211 |
| DRAW | D3 combo draw, turn, ½-pot | +0.0693 | +0.0090 |
| DRAW | D4 flush draw, flop, ½-pot, 3-way | +0.0628 | +0.0187 |
| MADE | M1 middle pair, flop, pot | +0.0697 | **+0.0697** |
| MADE | M2 middle pair, turn, pot | +0.0717 | **+0.0717** |

The made-hand readings are byte-identical to the records already in
`_R9LF_PANEL`'s comment block, independently confirming zero non-draw impact at node
level as well as at suite level.

## 7. A second defect found on the way, NOT fixed here

On the **turn**, the same combo draw has heuristic equity 0.18 against 0.2857 needed, so
continuing is not justified by immediate odds — yet every shape of this fix makes the
bot continue there *more*. The engine has no implied-odds model, so an immediate-odds
gate would itself be wrong. This is the price/equity gate the theory contract's §4
P6/F7 row has always wanted, and it is filed rather than built — one mechanism per
slice. See the spec's Filings table.

---

## 9. REV 2 — the shipping variant, measured end to end

Option B (owner-chosen 2026-08-04): floor the strong-draw call bonus **and** couple the
N-LOGIT raise scale to the call merit, in **branch** form so every non-STRONG path stays
bitwise on today's expression. Worktree `/private/tmp/claude-501/wt-drawalt`, detached at
`b0a6a4e`. Every number below is harvested from this variant's own output.

### 9.1 Full suite

**4 failed, 1415 passed, 1 skipped** · `ruff check .` → All checks passed.

| test | reading |
|---|---|
| `test_persona_stats_byte_identical_after_log_refactor` | `calling_station` AF 0.3277778 → 0.3667622 |
| `test_limper_coverage_fires_on_organic_play` | `('UTG2', 1)` 74 → **70** |
| `test_coverage_never_regresses` | **`hand stream drifted`** — 1233 ≠ 1288 (the *first* assertion) |
| `test_t4_flop_absolute_band[passive_fish-0.33]` | 0.193 outside [0.20, 0.38] |

The rev-1 blocker — `test_nlogit_g1_orthogonality_raise_share_is_lever_invariant` — is
**green, unmodified**. That is the whole point of option B: the `1e-12` guarantee is
preserved rather than narrowed.

### 9.2 Self-difference by node class (nit 0.45 vs the same pack at 0.60)

| class | node | HEAD | shipping |
|---|---|---|---|
| DRAW | D1 combo draw, flop, ⅔-pot | +0.0682 | +0.0040 |
| DRAW | D2 flush draw, flop, pot | +0.0678 | +0.0164 |
| DRAW | D3 combo draw, turn, ½-pot | +0.0693 | +0.0041 |
| DRAW | D4 flush draw, flop, ½-pot, **four-way** (`opponents=3`) | +0.0628 | +0.0146 |
| PAIR+DRAW | P1 middle pair + flush draw | +0.0380 | +0.0097 |
| PAIR+DRAW | P2 top pair + flush draw | +0.0134 | +0.0043 |
| MADE | M1 middle pair, flop, pot | +0.0697 | **+0.0697** |
| MADE | M2 middle pair, turn, pot | +0.0717 | **+0.0717** |

P2 is **already inside the 0.030 cap at HEAD**, so it is recorded and not pinned — a panel of
only high-fold naked draws would make the gate's redness a property of node selection. P1 is
the pair-plus-draw node rev 1 lacked entirely; bucket and draw are independent axes
(`personas_postflop.py:752-756`).

### 9.3 Levels

Trace node, nit P(fold): HEAD **0.4217** → shipping **0.2768**.
Middle pair + flush draw: 0.1765 → **0.1206** (−32 % relative) — disclosed, previously not.
Raise share on the trace node: 0.2125 → 0.1457, now guaranteed stable under the dial.

### 9.4 Coverage

`baseline 1288 / 335` · `current 1233 / 323` · graded **share 26.01 % → 26.20 %**.
The unchanged worktree reproduces the baseline exactly, so the drift is attributable.

### 9.5 Why a level gate exists

Floor-value sweep (algebraically exact substitution on the unmodified engine, reproducing
the D1/D3 HEAD readings to 4dp as a control):

| floor | D1 self | D3 self | nit trace P(fold) | passes a cap-only gate? |
|---|---|---|---|---|
| HEAD | +0.0682 | +0.0693 | 0.4217 | no (correctly red) |
| 0.60 | +0.0188 | +0.0156 | 0.3723 | **yes** |
| 1.00 (shipping) | +0.0111 | +0.0090 | 0.2838 | yes |
| 2.00 | +0.0044 | +0.0035 | 0.1780 | **yes** |
| 5.00 | +0.0010 | +0.0008 | 0.0840 | **yes** |

`floor = 5.0` more than doubles every persona's strong-draw bonus, loosens even the calling
station, and passes a sensitivity cap. Hence C2's two-sided absolute band.
(The middle column is the call-side-only variant, which is what the sweep instrument models;
the shipping variant's own readings are in §9.2.)
