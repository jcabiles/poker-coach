# Report — R9-LOOSEFIT rev 4 measurement

slice: `R9-LOOSEFIT` (rev 4) · initiative: persona-realism · code pin: `origin/main` = b63dfaa
source: `docs/ai-dlc/specs/r9-loosefit-rev4.md` + `docs/ai-dlc/ledger/r9-loosefit.md` ("Rev-4 BUILD"
section). This report is the population evidence the spec's files-to-touch item 4 requires; it does
not restate the spec's derivation in full, only the numbers a reader needs without opening the
spec.

**One-line result:** `nit`'s `postflop.call_looseness` moved 0.6 → 0.45 (nothing else changed).
At five hand-picked, correctly-priced nodes the nit now folds visibly more against itself at the
old value; across the 970-cell canonical population it folds strictly more than `tag` at every
non-degenerate cell (up from 384/970 at HEAD). The claim is **pairwise** — nit against tag only;
nothing here ranks the nit against lag, maniac, passive_fish or the calling station.

## 1. The panel — five constructed nodes, correctly priced

All five nodes assert, before their numbers are trusted, that the engine's own computed faced
fraction equals both `to_call / (pot_bb − contribution)` (to 1e-12) and the fraction the node is
labelled with (to 1e-9). This was built to catch a documented bug: an earlier revision's naive
pricing read a 3-bb-into-24-bb node as faced fraction 1.00 instead of the intended 0.50.

| id | hole | board | street | legal | pot | to_call | opp | faced frac | **self-difference** |
|---|---|---|---|---|---|---|---|---|---|
| P1 | 9h 4c | Kc 9s 3h | flop | F/C/R | 24 | 12 | 1 | 1.000 | **+0.0697** |
| P2 | 9h 4c | Kc 9s 3h 2d | turn | F/C/R | 24 | 12 | 3 | 1.000 | **+0.0717** |
| P3 | Ah 8d | Kc 9s 3h | flop | F/C/R | 18 | 6 | 1 | 0.500 | **+0.0718** |
| P4 | 9h 4c | Kc 9s 3h 2d | turn | F/C/R | 18 | 6 | 1 | 0.500 | **+0.0595** |
| C5 (control) | 9h 4c | Kc 9s 3h 2d | turn | F/C only | 24 | 12 | 1 | 1.000 | **+0.0707** |

"Self-difference" is P(fold | nit at 0.45) − P(fold | nit at 0.60) at the same node — the nit
compared against itself, not against tag. **Binding node: P4 at +0.0595, 1.49× the pre-registered
0.040 floor.** C5 has no raise branch available (fold/call only); it exists to prove the lever
still moves the bot with the raise leg absent, and passes at +0.0707.

The panel deliberately does **not** carry an identity leg (nit-vs-tag at these five nodes). An
earlier draft did; it was removed because `identity = self + HEAD_gap` is an exact algebraic
identity and `HEAD_gap` (the pre-existing fold-rate gap created by tag's higher `aggression`) is
fixed and untouched by this slice — so a build that clears the self floor *automatically* clears
the identity floor too, and the identity leg could never fail independently of the self leg. The
cross-persona (nit-vs-tag) claim is instead carried entirely by the sweep, section 2.

## 2. The sweep — the population evidence

Four hand-picked nodes cannot support a general claim, so the slice also enumerates the canonical
1,728-cell grid (`_nlogit_cells()`), re-priced to the fractions it was always intended to test
(⅓, ⅔, 1, 2× pot) because the grid's own built-in prices are broken (see §3's note on
`N-NLOGITPRICE`). A cell counts only if all three packs being compared — shipped nit, nit rebuilt
at the pre-slice 0.60, and tag — keep every legal action's probability inside [0.01, 0.99]; that
is what "non-degenerate" means below, and the count is reported rather than assumed for exactly
that reason.

| | at HEAD (nit @ 0.60) | after the move (nit @ 0.45) |
|---|---|---|
| non-degenerate cells (denominator) | 970 of 1,728 | 970 of 1,728 |
| nit folds strictly more than tag | 384 (39.6%) | **970 (100.0%)** |
| … by more than 0.02 | 300 (30.9%) | **826 (85.2%)** |
| nit folds LESS than tag | — | **0** |

Gate floors, pre-registered before any result was seen: at least 800/970 folding strictly more
(measured 970 → 1.21× margin; HEAD reads 384 → red by 2.08×), and at least 650/970 by more than
0.02 (measured 826 → 1.27× margin; HEAD reads 300 → red by 2.17×).

**Revert check:** restoring nit to 0.6 reverts the "strictly more" count to **396 of 982**, not
384 of 970 — a different mask, not a typo. Under the revert, the shipped pack and the pre-slice
comparison pack are byte-identical, so the three-pack validity mask (which requires all three
packs to stay non-degenerate) admits 12 more cells than it does when the two nit packs differ.
The gate reports its own denominator each time rather than asserting a fixed number, for exactly
this reason.

## 3. The ceiling — why 0.0718 is close to the largest number this lever can ever produce

`nit` authors `call_looseness = continue_ref = 0.6`. At a facing node the engine scales the CALL
merit by `looseness` and the RAISE merit by the same ratio (`rscale = looseness / continue_ref`),
so moving `call_looseness` from 0.6 to 0.45 scales **both** defend merits by the identical factor
`s = 0.45/0.6 = 0.75`. That means the whole continue-vs-fold odds ratio shifts by a **constant**
`ln(0.75) = −0.2877`, independent of the node — and the self-difference reduces to a one-variable
function of the base fold probability alone:

```
self(p₀) = p₀ / (p₀ + 0.75·(1 − p₀)) − p₀
```

This function has a **hard maximum of 0.071797**, attained at base fold probability p₀ = 0.4641
— derived by setting the derivative to zero, and confirmed numerically (max observed deviation
from the predicted value across 25 tested nodes: 1.11e-16; on drawing hands specifically the
deviation from a second, independent damp path — which should in principle break the common-factor
derivation — holds to 5.6e-17). The maximum observed self-difference across more than 2,600
measured cells was 0.071795, essentially touching the theoretical ceiling.

**Consequence: any self-leg threshold at or above 0.072 is unsatisfiable by this lever, by
construction** — no board, price, street, stack depth or opponent count can beat it. (For scale:
an earlier, withdrawn revision of this spec had proposed a 0.05 floor, already 70% of a ceiling
nobody had computed at the time.)

## Mutant kill table

Two mutants were run against the shipped gates, by an agent that had not written them:

| mutant | G-NODE self leg | G-SWEEP leg (a) | N-LOGIT's G1 gate | verdict |
|---|---|---|---|---|
| **no-op** (lever read, result discarded) | **KILLED** — reads 0.000000 at all five panel nodes | **KILLED** — reads 396/982 vs an 800-cell floor | passes (blind to it) | dies on this slice's gates only |
| **CALL scaled, RAISE left unscaled** (`rscale` forced to 1.0) | survives (worst case +0.0532, still positive but below what a correct implementation gives) | survives | **KILLED** — drift 0.3329 at every faced fraction | disclosed non-kill, ownership delegated to G1 |

The no-op row is the strongest single piece of evidence in the slice: the pre-existing N-LOGIT
invariance gate (G1) does **not** notice a lever that is read and discarded. Of the 1,419 tests in
the suite, only the two gates this slice ships catch that failure mode.

The CALL-only mutant (RAISE left unscaled) is caught by G1, but G1's own canonical grid runs at
broken prices (600× and 1200× pot — see below). The build therefore re-ran G1's statistic by hand
at both the broken prices and the correctly-priced construction this sweep uses, to confirm the
kill is not an artifact of the broken prices: clean-engine drift measured 0.000000000 in both
regimes; the CALL-only mutant's drift measured 0.332927–0.333332 at every faced fraction, sane and
broken alike (6,400 comparisons per persona per regime, zero degenerate cells). The reason is
structural, not luck: price only reaches the FOLD merit, and G1's statistic conditions FOLD away
entirely, so the mutant's signature is price-invariant by construction. `N-NLOGITPRICE` (filed
below) therefore stays a filed defect, not an escalated blocker.

## What still passes this whole 1,419-test suite while being wrong

(measured, not speculated — carried forward from the ledger's Rev-4 BUILD section)

- Scaling CALL without scaling RAISE — only G1 catches it; if G1 is ever skipped this slice has no
  defence of its own against that specific mutant.
- Any lever value at or below 0.48 — neither shipped gate imposes a lower bound; the real floor on
  this lever comes from elsewhere in the suite (`test_fold_to_bet_respects_alpha_ceiling[nit]`
  fails at 0.20, and R9-DEFENCE-a's ladder gate binds at roughly 0.42).
- Loosening `tag`'s `call_looseness` instead of tightening `nit`'s — this still reads green on the
  sweep gate, because the sweep only measures an ordering (nit folds more than tag), not which
  persona moved to produce it. Concretely: leaving nit at 0.60 and raising tag's
  `call_looseness` to 0.80 reads 982/982 and 772/982 — green on both legs, wrong cause. The panel's
  self-comparison (nit against itself, rebuilt at the pre-slice value) is what ties the movement to
  the nit specifically; the sweep alone cannot.
- Anything outside a facing node with a live FOLD leg — SPR-committed nodes are lever-inert by
  construction (the fold merit is zeroed there), and preflop/bet/check nodes are untouched by this
  slice.
- Computing the correct merit weights and then sampling from them incorrectly — both gates read the
  computed weight vector directly, never a drawn action, so a sampling-layer bug would not be
  caught by either.

## Known limits of this evidence

- The panel's headline numbers are all measured with `aggressor_bet_prev_street=False`. With the
  line-history signal turned on, the panel reads *better* (self-difference 0.0665–0.0707, up from
  0.0595–0.0718 with the signal off), but the sweep was not re-run under that posture.
- The sweep's four faced fractions (⅓, ⅔, 1, 2× pot) are the canonical grid's own intended labels,
  not the prices each pack's own bet-sizing ladder would actually produce in play; the ⅔ and ½
  fractions collapse into a single effective price bucket in places.
- The [0.01, 0.99] non-degeneracy window is an arbitrary constant, and the 970-cell denominator is
  sensitive to it — which is why the gate enumerates its own denominator each run rather than
  asserting a fixed number.
- Robustness was measured, not merely asserted: over a ±15% price band and ±1 opponent around each
  panel node, the worst self-difference observed was still +0.0595 (at P4).
