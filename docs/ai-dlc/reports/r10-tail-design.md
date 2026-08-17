# `R10-TAIL` design pass — absolute-price tail + multiway continue thresholds

**Status: DESIGN PASS. No code changed. Nothing filed.** Answers the two design questions in
`docs/ai-dlc/roadmap/persona-realism.md:2056-2072` (`R10-TAIL`) with measured attribution first, then
mechanism proposals and ready-to-file ticket sketches. Sibling pass to `R9-DEFENCE`
(`persona-realism.md:1868-1905`); the seam between the two is decided in §B5.

---

## 0. Pin, method, and what is trustworthy here

**Pinned commit: `803e9dc9ee605eb1702bf7f823b28f5a7aaf596b`** (branch `feat/persona-realism-wave-a-w2`,
`git rev-parse HEAD`). Every number below is reproducible at that commit. Working tree at pin time had
only doc-side modifications (`docs/ai-dlc/profile.md`, `docs/ai-dlc/roadmap/persona-realism.md`) plus
untracked docs — **no domain file is dirty**, so the pin is honest for engine behavior.

**Instrument — the DIRECT constructed-policy grid**, per the `R9-DEFENCE` question-5 grid pin
(`persona-realism.md:1893-1897`: "never a simulator-derived or live-corpus grid"). Two mutually
validating layers:

1. **Live sampler capture.** `sample_postflop_decision` is called on hand-built spots with a capture rng
   that records the FIRST `rng.choices` weights. Those weights are *already normalized*
   (`personas_postflop.py:929`), so the probe reads exact **normalized probability vectors** with zero
   domain instrumentation and zero sampling variance — the `backend/tests/node_trace.py:51-66` pattern.
2. **Independent closed form.** The facing-branch merit assembly (`personas_postflop.py:745-824`) was
   re-implemented in the probe from the module's own constants. **Every cell of the Part A price sweep
   matched the live sampler to < 1e-12 (`OK` on all 54 rows).** Counterfactual toggles are then pure
   arithmetic on the validated closed form — no monkeypatching, no domain edit.

**Fixed across the sweeps** (varying one axis at a time): hole cards + board (hence bucket and draw
class), street (FLOP), legal-action set, `is_aggressor=False`, and `latest_aggressor_contribution_bb`
set equal to the bet so that `faced_frac == bet / pot_before_bet` **exactly** (the W1-b branch,
`personas_postflop.py:776`). Fixtures:

| label | hole | board | classified bucket / draw |
|---|---|---|---|
| AIR | 7h 2s | Ks Qd 8c | `AIR` / `NONE` |
| ACE_HIGH | Ah 2s | Ks Qd 8c | `ACE_HIGH` / `NONE` |
| MIDDLE_PAIR | 3h 3d | Qs 7c 2d | `MIDDLE_PAIR` / `NONE` |
| TOP_PAIR | Ah Th | As 7d 2c | `TOP_PAIR` / `NONE` |
| OVERPAIR | Ah Ad | Ks 7d 2c | `OVERPAIR_TPTK` / `NONE` |
| AIR+draw | Jh Th | 9h 8c 2h | `AIR` / `STRONG` |
| 99 on 88x | 9h 9d | 8s 8c 3d | `TWO_PAIR_PLUS` / `NONE` |
| 44 on 88x | 4h 4d | 8s 8c 3d | `MIDDLE_PAIR` / `NONE` |

Probes live outside the repo at
`/private/tmp/claude-501/…/scratchpad/probe_r10tail.py` and `probe_mech.py`, run with
`cd backend && .venv/bin/python`.

**Live lever values at the pin** (`content/personas/*.json` → `_price_exponent`,
`personas_postflop.py:563-580`):

| persona | `size_elasticity` | `stickiness` | `call_looseness` | resolved price exponent | branch |
|---|---|---|---|---|---|
| calling_station | **0.55** | — | **4.0** | **1.2100** | DIRECT (W2-a) |
| passive_fish | 1.3 | — | 0.42 | 2.8600 | DIRECT (W2-a) |
| nit | — | 0.6 | 0.6 | 2.3752 | LEGACY inverse |
| tag | — | 0.6 | 0.6 | 2.3752 | LEGACY inverse |
| lag | — | 0.55 | 0.55 | 2.4064 | LEGACY inverse |
| maniac | — | 0.55 | — | 2.4064 | LEGACY inverse |

⚠️ **Note for any future fitting slice:** the station's exponent (1.21) is the *lowest in the roster* and
roughly **half** the four legacy-branch personas'. The elasticity split did what it says — but it also
means the station is the persona least able to express *any* price mechanism keyed on that exponent.

---

# PART A — the OVERBET tail

## A1. Root cause: the price curve is a 4-step staircase whose top step never ends

`_price_factor` (`personas_postflop.py:554-560`) is the engine's entire price response:

```
fold_merit = _FOLD_BASE[bucket] * _PRICE_LEVEL * (α_bucket / α_ref) ** exponent      (:777, :560)
```

Its `α` input is **not** the faced price. It is a **table lookup keyed on a 4-way bucket**
(`_BUCKET_ALPHA`, `:456-461`) via `size_bucket` (`:64-73`), whose top bucket is
`OVERBET = "overbet"  # > 1.10` (`:61`) with **no upper edge**:

```python
_BUCKET_ALPHA = {SMALL: 0.25, MEDIUM: 0.375, LARGE: 0.47,
                 OVERBET: 0.60}   # :460 — comment: "1.5× pot (the engine's only overbet size)"
_ALPHA_REF   = _BUCKET_ALPHA[MEDIUM]   # :464 = 0.375
```

Therefore **`α` is constant for every faced price above 1.10× pot**, and the fold merit — the only
price-carrying term in the whole facing branch — is constant with it. A 1.11×-pot bet, a 2.33×-pot raise,
and a 10×-pot jam are the **same node**.

`size_elasticity` cannot repair this, and this is the correction the roadmap asked for. The exponent acts
on a ratio `α/α_ref` that **stops growing at 1.10× pot**. So:

> **`size_elasticity` sets the HEIGHT of the top step. It cannot create a slope where the ratio it is
> applied to is constant.** The station's 0.55 is not being "eaten" by some competing term — it is being
> applied to a variable that has already saturated.

The `:460` comment is the provenance of the defect, and it is honest about it: the α table was authored as
a **chosen-size** taxonomy ("the engine's only overbet size" = the 1.5× the packs author), then reused as
a **faced-price** taxonomy. Chosen sizes are bounded by the authored sizing distributions — measured
maximum across all six packs is **1.5** (`content/personas/{maniac,lag}.json`, `sizing_by_node` key
`"1.5"`). Faced prices are **not** bounded: `raise_to = current_bet_to + f·(pot + to_call)` (`:688-691`)
compounds, so a raise routinely presents the next seat with 1.5×–3×+ the pre-aggression pot. The taxonomy
was correct for its original domain and silently wrong for its reused one.

## A2. Measured price sweep — the tail is EXACTLY flat

Normalized probability vectors, `AIR`/`NONE`, heads-up, flop, SPR 10 (commit gate off), facing a raise.
Live sampler; closed form agreed on every row.

| faced f (× pot) | station P(fold) | **station P(call)** | station P(raise) | nit P(call) | fish P(call) |
|---|---|---|---|---|---|
| 0.30 | 0.3290 | 0.6551 | 0.0159 | 0.2971 | 0.2286 |
| 0.40 | 0.3290 | 0.6551 | 0.0159 | 0.2971 | 0.2286 |
| 0.41 | 0.4447 | 0.5421 | 0.0132 | 0.1482 | 0.1027 |
| 0.70 | 0.4447 | 0.5421 | 0.0132 | 0.1482 | 0.1027 |
| 0.71 | 0.5128 | 0.4757 | 0.0115 | 0.0941 | 0.0594 |
| 1.10 | 0.5128 | 0.4757 | 0.0115 | 0.0941 | 0.0594 |
| **1.11** | 0.5858 | **0.4044** | 0.0098 | 0.0556 | 0.0314 |
| **1.45** *(h579)* | 0.5858 | **0.4044** | 0.0098 | 0.0556 | 0.0314 |
| **1.50** *(h81/h385)* | 0.5858 | **0.4044** | 0.0098 | 0.0556 | 0.0314 |
| 1.80 | 0.5858 | **0.4044** | 0.0098 | 0.0556 | 0.0314 |
| **2.33** *(h588)* | 0.5858 | **0.4044** | 0.0098 | 0.0556 | 0.0314 |
| 4.00 | 0.5858 | **0.4044** | 0.0098 | 0.0556 | 0.0314 |
| 10.00 | 0.5858 | **0.4044** | 0.0098 | 0.0556 | 0.0314 |

**All three R10-2 exhibit prices (1.45×, 1.50×, 2.33×) evaluate to a single identical node.** The
station calls air there **40.4%** of the time, at any price, forever. The step boundaries at 0.40/0.70/1.10
are visible and exact, which is the positive control that the sweep is reading the real curve.

The same holds for `ACE_HIGH` facing a raise (where `_ACE_HIGH_FLOAT_RAISE_DAMP` is active, `:374`,
`:791-797`) — and it is far worse in level:

| faced f | station P(fold) | **station P(call)** | nit P(call) |
|---|---|---|---|
| 0.55 | 0.1913 | 0.8016 | 0.3715 |
| 1.10 | 0.2371 | 0.7562 | 0.2617 |
| 1.45 | 0.2947 | **0.6992** | 0.1678 |
| 2.33 | 0.2947 | **0.6992** | 0.1678 |
| 10.00 | 0.2947 | **0.6992** | 0.1678 |

R10-2's tail class is "air / ace-high / busted-draw"; the ace-high half plateaus at **~70% calls vs any
overbet**, which is the larger of the two numbers and should be the mechanism's primary target.

## A3. Contribution decomposition — separate FLATNESS from HEIGHT

The requested contributions, measured at the worst exhibit price (station, `AIR`/`NONE`, f = 2.33, HU,
flop). Raw merits at that node: `fold = 0.4636` (= `_FOLD_BASE[AIR]` 0.75 × `pfac` 0.6181),
`call = 0.3200` (= `_CALL_BASE[AIR]` 0.08 × `call_looseness` 4.0), `raise = 0.0078`.

**Two orthogonal quantities must be attributed separately, and conflating them is how this defect stayed
unattributed for two reviews:**

**(i) FLATNESS** — measured as `P(call | f=4.00) − P(call | f=1.11)`:

| configuration | P(call) at 1.11 | P(call) at 4.00 | flatness |
|---|---|---|---|
| **HEAD** | 0.4044 | 0.4044 | **0.0000 — exactly flat** |
| exponent raised 1.21 → 2.86, staircase kept | 0.2398 | 0.2398 | **0.0000 — still exactly flat** |
| staircase replaced by continuous `α = f/(1+f)`, exponent unchanged | 0.4438 | 0.3251 | −0.1187 |

⇒ **100% of the tail flatness is attributable to `_BUCKET_ALPHA`'s open-ended top bucket
(`:456-461` + `:64-73` + `:554-560`). `size_elasticity` contributes 0% of it, at any value.** This is a
structural fact, not a fit.

**(ii) HEIGHT of the plateau** — single-lever counterfactuals from HEAD at f = 2.33, P(call) = 0.4044:

| lever switched off / changed | P(call) | Δ vs HEAD | verdict |
|---|---|---|---|
| `call_looseness` 4.0 → 1.0 | 0.1451 | **−0.2593** | **dominant contributor to the level** |
| exponent 1.21 → 2.86 (fish's elasticity), staircase kept | 0.2398 | −0.1646 | second; level only, not slope |
| staircase → continuous `α`, exponent unchanged | 0.3611 | −0.0433 | slope, weak alone at e = 1.21 |
| staircase → continuous `α` **and** exponent 2.86 | 0.1693 | −0.2351 | the two compose usefully |
| RAISE leg removed from the legal set | 0.4084 | **+0.0040** | raise-path leakage ≈ **0.4 pts, negligible** |
| SPR moved below `spr_commit` (1.5) | 0.4044 | **0.0000** | **commit gate is inert here — see A4** |

**Raise-path leakage, per persona** (share of non-fold mass sitting on RAISE at f = 2.33, `AIR`):
station `R/(R+C)` = 0.0098/0.4142 = **2.4%** (negligible); nit 21.8%; **passive_fish 48.0%**;
maniac 82.2%. So "raise-path leakage" is a non-issue for the *station's* tail but is the majority of the
fish's and maniac's non-fold mass — which is R10-4's `N-logit` finding restated at this node, and it is
the reason §A6's direction proof matters.

## A4. The SPR commit gate is REFUTED as a cause of the R10-2 air/ace-high tail

Measured: station, `AIR`/`NONE`, at SPR 10 / 1.4 / 0.8 (`spr_commit` = 1.5, so the last two are *inside*
the gate):

| f | SPR 10 | SPR 1.40 | SPR 0.80 |
|---|---|---|---|
| 0.55 | F0.4447 / C0.5421 / R0.0132 | **identical** | **identical** |
| 1.45 | F0.5858 / C0.4044 / R0.0098 | **identical** | **identical** |
| 2.33 | F0.5858 / C0.4044 / R0.0098 | **identical** | **identical** |

**Reason, from the code** (`:899-921`): `value_commit` requires `made` (`_RUNG[bucket] >=
_RUNG[OVERPAIR_TPTK]`, i.e. rung ≥ 4) or `drawing`. `AIR`/`NONE` is rung 0 with `draw is NONE`, so both
`value_commit` and the `elif facing and drawing` B5b branch are False and `entries` passes through
untouched. **A no-pair-no-draw hand can never enter the commit region.** The R9-1 confounder warning does
not apply to R10-2's exhibits; it applies to Part B's (see §B4).

Bonus positive control — the commit gate's EV logic **works correctly at the tail** for drawing hands
(`AIR`/`STRONG`, station):

| f | SPR 10 | SPR 1.40 | SPR 0.80 |
|---|---|---|---|
| 0.55 | F0.0915 | **F0.0000** (T1 = 0.262 ≤ e 0.36 → commits) | **F0.0000** |
| 1.45 | F0.1511 | F0.1565 (T1 = 0.372 > 0.36 → no commit, B5b damp instead) | F0.1994 |
| 2.33 | F0.1511 | F0.1565 | F0.1994 |

W2-b's `_value_commit_threshold` (`:601-607`) correctly **refuses** to stack a flush draw off against an
overbet and the B5b damp correctly *raises* fold as commitment deepens. Do not touch it.

## A5. The hard ceiling — what price-curve reshaping alone can and cannot achieve

`α` is a probability-like quantity bounded above by 1.0. The best possible fold merit from *any* reshaping
of the α curve is `_FOLD_BASE[bucket] × _PRICE_LEVEL × (1.0/0.375)**exponent`. Because `call_merit` is
**completely price-blind** (`:790-798` — no price term exists on the call side at all), the resulting
P(call) has an **asymptotic floor**:

Measured by setting `_BUCKET_ALPHA[OVERBET] = 1.0` in-process and re-reading the **live sampler** at
f = 2.33, HU, facing a raise:

| persona | bucket | P(call) at HEAD | floor as α → 1.0 | P(fold) at that floor |
|---|---|---|---|---|
| calling_station | AIR | 0.4044 | **0.2694** | 0.7241 |
| calling_station | ACE_HIGH | 0.6992 | **0.5584** | 0.4366 |
| passive_fish | AIR | 0.0314 | 0.0076 | 0.9853 |
| passive_fish | ACE_HIGH | 0.0995 | 0.0257 | 0.9657 |
| nit | AIR | 0.0556 | 0.0174 | 0.9778 |
| nit | ACE_HIGH | 0.1678 | 0.0573 | 0.9369 |

*(Facing a BET instead — `_ACE_HIGH_FLOAT_RAISE_DAMP` inactive — the station's ace-high floor is worse
still: HEAD 0.8086 → α=1 floor **0.6969**.)*

⇒ **At `size_elasticity = 0.55`, no α-bounded price mechanism can push the station's air-vs-overbet call
below ~0.27, or its ace-high call below ~0.56 (~0.70 facing a first bet).** Any mechanism that must beat
those numbers has to leave the α-ratio formulation — i.e. use an **unbounded** price argument in the tail
segment. This is the single most load-bearing constraint on the mechanism choice and it kills the naive
"just make α continuous" fix.

*(Deliberately NOT proposed: adding a price term to the call merit. On a 2-candidate node it is
algebraically the same change as scaling fold, and on the 3-candidate node it is strictly worse — it cuts
call mass directly, which is the `N-logit` pathology the roadmap forbids at `:2065`. Recorded here so a
reviewer does not have to ask.)*

## A6. Reframing — R10-2 bundles TWO defects, and only one is a "tail"

The measurement forces a severing the roadmap item does not currently make:

- **The engine's own authored maximum bet is 1.5× pot** (`maniac.json` / `lag.json` sizing keys). So
  faced prices in **(1.10, 1.50]** are *inside the engine's designed size vocabulary*.
- Two of R10-2's three exhibits (1.45×, 1.50×) sit in that window. Calling air there 40% of the time is a
  **plateau-HEIGHT defect** — driven by `call_looseness = 4.0` (−0.2593 when neutralised) and the low
  station exponent. That is a **dial-fitting** problem, owned by `R9-LOOSEFIT` / `W4-b`'s single
  re-anchor, not by a new mechanism.
- Only **f > 1.5** is a genuine *absolute-price tail* defect: prices the engine can only ever *face*
  (from compounded raises/jams), never *choose*, and where the response is provably a flat line.

**Both are real. They need different owners.** Filing one ticket for both re-imports the level question
into a structural fix and guarantees a band re-anchor fight with `W4-b`.

## A7. The α-ceiling constraint that fixes the mechanism's gate

There is a hard, already-measured reason the mechanism cannot simply start at 1.11×. From
`personas_postflop.py:344-346` (the W3R-6 measurement, in-tree):

> "…pushing its 1.5×-overbet fold-to-bet to **0.6528** vs the α + 0.05 ceiling of **0.650** (undamped
> baseline **0.6422** — only **0.0078** of headroom)."

The passive fish has **0.78 points of headroom** against the RES-D α fold-ceiling at 1.5× pot, on the
W3R-0 arrival-range facing-a-**BET** curve. **Any unconditional fold-merit increase at a faced 1.5×
breaches it.** Two structural escapes already have precedent in this exact file:

1. **Anchor the tail strictly above the measured node** (`f > 1.5`) — the α-measured node stays
   byte-identical by construction.
2. **Gate on `facing_raise`** — the α-ceiling contract is measured over a facing-a-BET curve, so a
   facing-a-RAISE gate is *off the measurement node by construction*. This is the identical structural
   argument the file already used twice and documented as "safe for a structural reason, not a lucky
   measurement" (`:253-257` for `_ACE_HIGH_FLOAT_RAISE_DAMP`, `:359-365` for `_ONE_PAIR_RAISE_DAMP`).

And the decisive fact: **all three R10-2 exhibits are calls of RAISES**, not of first bets
(`persona-realism.md:437-439`: "audit-verified calls of 1.45×-, 1.50×- and 2.33×-pot **raises**"). So
gate (2) covers 3/3 of the evidence at zero α-ceiling risk.

⚠️ **Scope-purity note the reviewer will raise.** `R10-TAIL` is filed as "an absolute-price defect, not a
line response" (`:2057-2058`). Using `facing_raise` as a **gate** does not make this a line response: the
*response variable* remains the absolute price `f`, and `facing_raise` is only a fence keeping the
mechanic off the α-measured curve. It is already a HEAD kwarg (`:657`, `:673-676`) used by two damps for
exactly this reason. The distinction is real but it is thin, and it should be stated in the ticket rather
than discovered in review.

## A8. Mechanism proposal — `M3`: a piecewise price ladder above the OVERBET representative

**Shape.** Keep `_price_factor` exactly as-is up to the anchor, then let the merit keep climbing with the
*unbounded* price ratio:

```
f_top = 1.5                        # the engine's own maximum authored bet size; the α-measured node
e     = _price_exponent(pf)        # unchanged — persona identity still lives here
K     = shared mechanic constant   # the tail steepness (a FIT SEED)

price_factor(f) = _price_factor(f, e)                     for f <= f_top
                = _price_factor(f, e) * (f / f_top) ** K   for f >  f_top
```

Gate: `f > f_top` **OR** (`f > 1.10` **AND** `facing_raise`), per §A7.

**Why `e + K` (additive in the exponent) and not `e · k` (multiplicative).** The tail factor's ratio
between two personas is `(f/f_top) ** (e₁ − e₂)` under the additive form — the tail's persona dispersion
equals the head's. Under `e·k` it is `(f/f_top) ** (k(e₁−e₂))`: **dispersion is multiplied by k**, which
amplifies the exponent spread the elasticity split deliberately set (station 1.21 vs legacy 2.41).
Measured collateral at nominal strength 2.0, f = 2.33: the maniac's `AIR` raise share falls to
**0.0290 (0.15 × HEAD) under the multiplicative form** but only to **0.0923 (0.48 × HEAD) under the
additive form** — a 3.2× difference in collateral for the same nominal knob. The maniac's resistance
behavior is a persona whose defect claim R10-2's specialist adjudication explicitly **refuted** (0/15,
`persona-realism.md:449-450`), so this collateral is a real cost, not a bonus. **Recommend additive.**

**Measured `K` sweep, additive form** (station, `AIR`/`NONE`, HU, flop; ⚠️ these are SEEDS on a normalized
vector, not a fitted target — the target itself is not sourced, see §D1):

| f | HEAD | K=1.0 | K=1.5 | **K=2.0** | K=2.5 | K=3.5 |
|---|---|---|---|---|---|---|
| 1.51 | 0.4044 | 0.4028 | 0.4020 | 0.4012 | 0.4005 | 0.3989 |
| 1.80 | 0.4044 | 0.3620 | 0.3415 | 0.3215 | 0.3022 | 0.2655 |
| 2.33 | 0.4044 | 0.3054 | 0.2612 | **0.2213** | 0.1859 | 0.1284 |
| 4.00 | 0.4044 | 0.2046 | 0.1364 | **0.0883** | 0.0560 | 0.0218 |

The curve is **continuous at `f_top`** (the factor is ×1 there), monotone increasing in `f`, and
byte-identical at and below it. K ≈ 2.0 is the mildest seed that produces a visible, non-cosmetic slope
without collapsing the maniac.

**Law compliance:**

| law | how `M3` satisfies it |
|---|---|
| **Softmax law** (contract §2, `:21-40`) — no flat multipliers | `M3` is a *function of the faced price*, not a constant. The reported effects are all **post-normalization probability deltas**; nothing was read off a raw-merit ratio. |
| **No-fold-floor law** (`:2064`; contract §4 row P3 "a direction, never an asserted floor") | `M3` only *scales a merit*. No branch asserts `fold >= x`. Fold probability remains an emergent normalization outcome, and stays strictly < 1 at every measured cell. |
| **Cut call mass routes to FOLD, not RAISE** (`N-logit`, `:2065`) | **Satisfied by construction, and measured.** See below. |

**`N-logit` direction proof — measured, not asserted.** Because `M3` *raises the FOLD merit* rather than
cutting the CALL merit, normalization lowers *every* other candidate's share. Live sampler, additive
K = 2.0, `AIR`/`NONE`, HU, flop, facing a raise:

| persona | f | HEAD F/C/R | with `M3` F/C/R | **ΔP(raise)** |
|---|---|---|---|---|
| calling_station | 1.45 | 0.5858/0.4044/0.0098 | 0.5858/0.4044/0.0098 | +0.0000 (byte-identical) |
| calling_station | 2.33 | 0.5858/0.4044/0.0098 | 0.7734/**0.2213**/0.0054 | **−0.0044** |
| passive_fish | 2.33 | 0.9396/0.0314/0.0290 | 0.9741/**0.0135**/0.0125 | **−0.0165** |
| maniac | 2.33 | 0.7664/0.0415/0.1922 | 0.8878/**0.0199**/0.0923 | **−0.0999** |

Contrast — **the forbidden shape**, cutting the call merit instead (`call_looseness × 0.4`, f = 2.33):

| persona | HEAD F/C/R | cut-call F/C/R | **ΔP(raise)** |
|---|---|---|---|
| calling_station | 0.5858/0.4044/0.0098 | 0.7735/0.2136/0.0130 | **+0.0031 (1.32×)** |
| passive_fish | 0.9396/0.0314/0.0290 | 0.9577/0.0128/0.0296 | +0.0006 (1.02×) |
| maniac | 0.7664/0.0415/0.1922 | 0.7859/0.0170/0.1971 | +0.0049 (1.03×) |

The **sign** is the finding: raising fold merit ⇒ P(raise) always falls; cutting call merit ⇒ P(raise)
always rises. (Absolute inflation in the *air* cell is small because `_RAISE_BASE[AIR]` = 0.02 (`:287`);
the roadmap's dramatic 44.3% → 72.6% figure is a *monster* cell, and §B4 below reproduces the large
version at 0.2935 → 0.6048.)

**⇒ Consequence for sequencing, offered for adjudication:** the roadmap lists `N-logit` among
`R10-TAIL`'s shared prerequisites (`:2059`). **For a fold-merit-side mechanism, `N-logit` is not a
blocking prerequisite** — the pathology it guards against cannot occur, as measured above. It remains a
blocking prerequisite for any **call-merit-side** mechanism. If the owner accepts this, `R10-TAIL(a)` can
be filed without waiting for `N-logit`. This is an owner call, not the design pass's to take.

**Seam with `W4-a` (contract §4 row P3).** `M3` is a **pot-relative** price term. The **stack-relative**
tail (`c = to_call/stack`) is contract §4's P3 and is `W4-a`'s declared subject
(`persona-realism.md:1488-1495`) — and it is **not built at HEAD** (no `_commit_factor` exists anywhere in
`backend/app/domain/`). Do not duplicate it. But both act on the same `fold_merit` expression, so contract
§7's same-merit rule applies: **`M3` must land BEFORE `W4-a`** (already sequenced LAST) so `W4-a`'s
re-fit sees the final price curve, and `W4-a`'s ticket must say so.

---

# PART B — multiway continue thresholds

## B1. Exact attribution: what changes with headcount on the facing path

Full audit of `personas_postflop.py` for terms reading `opponents`:

| term | line | side | reaches |
|---|---|---|---|
| `_MW_CATCH_TIGHTEN ** max(opponents-1,0)` on `fold_merit` | **:780-781** | **facing** | `_MW_CATCH_BUCKETS = (AIR, ACE_HIGH, MIDDLE_PAIR)` (`:520`) **only** |
| `pf.multiway_bluff_damp ** max(opponents-1,0)` in `bluff_mass` | :709 | both | reaches the facing path only via the **bluff-cell RAISE** merit (`:804`) |
| `_BUSTED_RIVER_BLUFF × multiway_bluff_damp ** …` | :739-742 | unopened | river bet only |
| `_MW_VALUE_DAMP ** min(…, _MW_VALUE_CAP)` | :852-853 | **unopened BET only** | `_MW_VALUE_BUCKETS = (TOP_PAIR, MIDDLE_PAIR)` (`:535`) |

**⚠️ Correction to the roadmap's wording.** `R10-5` / `R10-TAIL(b)` say "nothing raises the multiway
CONTINUE threshold vs raises/jams" (`:483`, `:2066-2067`). That is **not quite right and the imprecision
matters**: `_MW_CATCH_TIGHTEN` (F4, `:505-520`) *does* raise the continue threshold — but only for
**3 of 7 buckets**, at a base of **1.15**, and **blind to whether the chips came from a bet, a raise, or
a jam**. The accurate defect statement is:

> **Every bucket at `TOP_PAIR` and above is byte-identical across opponents 1 → 4 on the facing node,**
> and for the three covered buckets the response is a small directional seed with no action-kind axis.

That is a narrower, provable claim, and it changes the scope of the fix.

## B2. Measured headcount sweep — facing a 1.37×-pot raise, flop, SPR 10 (gate off)

Normalized vectors; `n` = `opponents`.

| bucket | persona | n=1 | n=2 | n=3 | n=4 | ΔP(call) 1→4 |
|---|---|---|---|---|---|---|
| AIR | station | C0.4044 | C0.3741 | C0.3427 | C0.3121 | −0.0923 |
| AIR | fish | C0.0314 | C0.0279 | C0.0245 | C0.0214 | −0.0100 |
| ACE_HIGH | station | C0.6992 | C0.6724 | C0.6418 | C0.6093 | −0.0899 |
| MIDDLE_PAIR | station | C0.9024 | C0.8898 | C0.8758 | **C0.8603** | −0.0421 |
| MIDDLE_PAIR | fish | C0.3126 | C0.2839 | C0.2569 | C0.2315 | −0.0811 |
| MIDDLE_PAIR | nit | C0.4479 | C0.4145 | C0.3818 | C0.3500 | −0.0979 |
| **TOP_PAIR** | station | C0.9715 | C0.9715 | C0.9715 | C0.9715 | **0.0000** |
| **TOP_PAIR** | fish | C0.6428 | C0.6428 | C0.6428 | C0.6428 | **0.0000** |
| **TOP_PAIR** | nit | C0.7582 | C0.7582 | C0.7582 | C0.7582 | **0.0000** |
| **OVERPAIR** | station | C0.9473 | C0.9473 | C0.9473 | C0.9473 | **0.0000** |
| **OVERPAIR** | fish | C0.5752 | C0.5752 | C0.5752 | C0.5752 | **0.0000** |
| **OVERPAIR** | nit | C0.6737 | C0.6737 | C0.6737 | C0.6737 | **0.0000** |

Two readings of the h697/h726 pile-up class:

- The **station calls a 1.37×-pot raise four-way with an underpair 86.0% of the time**, down only 4.2
  points from heads-up. `_MW_CATCH_TIGHTEN` = 1.15 is present but, under the softmax law, cosmetic here —
  exactly the failure mode contract §2 (`:34-40`) says a reviewer must reject.
- **`TOP_PAIR` and above are perfectly headcount-blind.** Four-way, five-way, ten-way: identical vector.
  That is the clean, provable half of the defect.

## B3. Bet vs raise vs jam — there is no action-kind axis at all

| bucket | persona | facing | n=1 | n=4 |
|---|---|---|---|---|
| MIDDLE_PAIR | station | bet 0.75× | F0.0710/C0.9179/R0.0110 | F0.1042/C0.8852/R0.0106 |
| MIDDLE_PAIR | station | **raise 1.37×** | F0.0939/C0.9024/R0.0038 | F0.1361/C0.8603/R0.0036 |
| MIDDLE_PAIR | station | **jam 1.37×** | F0.0939/C0.9024/R0.0038 | F0.1361/C0.8603/R0.0036 |
| TOP_PAIR | fish | bet 0.75× | F0.1713/C0.7004/R0.1283 | F0.1713/C0.7004/R0.1283 |
| TOP_PAIR | fish | raise 1.37× | F0.3160/C0.6428/R0.0412 | F0.3160/C0.6428/R0.0412 |
| TOP_PAIR | fish | **jam 1.37×** | F0.3160/C0.6428/R0.0412 | F0.3160/C0.6428/R0.0412 |

Direct jam-vs-min-raise control at identical price (station, `MIDDLE_PAIR`, 4-way, 60bb behind):

```
jam=False  fold=0.136082  call=0.860299  raise=0.003619
jam=True   fold=0.136082  call=0.860299  raise=0.003619      # byte-identical to 6dp
```

**Findings:**
1. **A jam is indistinguishable from a min-raise at the same price.** The merit assembly never reads the
   RAISE bracket's width, so `min_bb == max_bb` (the all-in signature, available in `legal`) is invisible.
   A jam response needs a **new signal**; it is not a tuning question. *(Handed to `R9-DEFENCE`
   question 3 — see §B5.)*
2. **Bet-vs-raise differs today only through (a) the price `f` and (b) the two `facing_raise` damps**
   (`_ACE_HIGH_FLOAT_RAISE_DAMP` `:791-797`, `_ONE_PAIR_RAISE_DAMP` `:812-817`). The visible RAISE-leg
   drop in the table above (0.0110 → 0.0038) is (b), not an action-kind term.

## B4. The SPR-commit confounder — separated, and it is bucket-dependent

Same headcount sweep, run **above and below** each persona's own `spr_commit`:

| bucket | persona | above | below | commit gate fires? |
|---|---|---|---|---|
| MIDDLE_PAIR | station (spr_commit 1.5) | F0.1361/C0.8603 (n=4) | **identical** | **NO** |
| MIDDLE_PAIR | fish (1.4) | F0.7574/C0.2315 (n=4) | **identical** | **NO** |
| TOP_PAIR | station | F0.0231/C0.9715 | **identical** | **NO** |
| TOP_PAIR | fish | F0.3160/C0.6428 | **identical** | **NO** |
| OVERPAIR | station | F0.0105/C0.9473/**R0.0423** | **F0.0000**/C0.8819/**R0.1181** | **YES** |
| OVERPAIR | fish | F0.1313/C0.5752/**R0.2935** | **F0.0000**/C0.3952/**R0.6048** | **YES** |

**Verdict — the confounder is REAL but confined to rung ≥ `OVERPAIR_TPTK` (and to draws that clear T1).**
`value_commit` needs `_RUNG[bucket] >= _RUNG[OVERPAIR_TPTK]` (`:900`), so:

- **For `MIDDLE_PAIR` / `TOP_PAIR` / `ACE_HIGH` / `AIR`, the commit gate can never fire.** h697's fish
  calling with `33` on `Q72` and h726's station `44` are `MIDDLE_PAIR` → **the commit gate is NOT the
  cause of those exhibits.** The confounder warning is refuted for that class.
- Where it *does* fire it is severe, and it is the **large-magnitude `N-logit` pathology in situ**: fold
  is zeroed and BET/RAISE get `_COMMIT_AGG_BOOST = 3.0` (`:313`, `:610-623`), so the **fish's raise share
  doubles, 0.2935 → 0.6048.** The bot gets *wilder* the deeper it is committed.
- **⚠️ Taxonomy trap that must be resolved per-exhibit before anyone cites h726.** A pocket pair on a
  paired board splits on `rank[1] == r1` (`:135-137`):

  | hand | bucket | above `spr_commit` | below |
  |---|---|---|---|
  | `99` on `8s 8c 3d` (pocket **above** the board pair) | **`TWO_PAIR_PLUS`** (rung 5) | F0.1247/C0.4293/**R0.4460** (fish) | **F0.0000**/C0.2429/**R0.7571** |
  | `44` on `8s 8c 3d` (pocket **below**) | `MIDDLE_PAIR` (rung 2) | F0.6724/C0.3126/R0.0150 | **identical** |

  R10-5 describes h726 as "station `44` + fish `99` call a 1.37×-pot shove on a **paired board**". If the
  board pair is below `99`, the fish's hand is `TWO_PAIR_PLUS` and **its call IS commit-gate-driven**,
  while the station's `44` is not. **The two seats in the same exhibit have different causes.** A
  fold-merit mechanism fixes one and is a literal no-op on the other (fold is already exactly `0.0` —
  the `W4-a` inertness lesson, `persona-realism.md:313-315`).

## B5. Scope proposal — and the `R9-DEFENCE` question-3 seam

**What is mine to decide (absolute-price and headcount thresholds):**

- **In scope for `R10-TAIL(b)`:** the **headcount** axis of the continue threshold — the bucket set the
  headcount exponent covers, and its base. Nothing else.
- **Out of scope, handed to `R9-DEFENCE` question 3:** the **bet / raise / jam** split. Rationale: §B3
  proves the engine has *no action-kind axis whatsoever*; introducing one means deciding what "facing a
  raise" *means as a state* — someone bet and someone raised — which is a **line** state, and
  `R9-DEFENCE` already owns line state (`aggressor_bet_prev_street`, question 1). Adding an action-kind
  term inside a headcount ticket would fork line-awareness across two owners.
- **Conversely, `R9-DEFENCE` must not touch the headcount exponent.** Clean partition: **`R10-TAIL(b)`
  owns `n`; `R9-DEFENCE` owns the line.**
- **⚠️ They act on the SAME `fold_merit` expression (`:777-781`)**, so contract §7's same-merit rule
  applies: **serialize them and re-fit the second.** They may not run as parallel waves.
- **Two facts `R9-DEFENCE` should take from this pass:** (i) a jam is byte-identical to a min-raise at
  the same price — a jam response requires a new signal from `legal` (`min_bb == max_bb`), not a dial;
  (ii) `facing_raise` already exists as a HEAD kwarg with a documented α-ceiling-safety argument
  (`:253-257`, `:359-365`) — reuse it rather than inventing a second one.

**Mechanism for `R10-TAIL(b)` — two severable moves on the existing term, no new multiplier:**

- **B-i (scope, HARD-shaped, the recommended slice):** add `TOP_PAIR` to `_MW_CATCH_BUCKETS`. It closes
  the exact byte-identity §B2 proves, and it makes the facing-side bucket set consistent with the
  bet-side one already shipped (`_MW_VALUE_BUCKETS = (TOP_PAIR, MIDDLE_PAIR)`, `:535`) — the current
  asymmetry between the two sets is undocumented and unexplained. **Do NOT add `OVERPAIR_TPTK` or
  above**: contract §4 rows P6 and P9 both exclude strong value, and §B4 shows a fold-merit change is
  *inert* there anyway (fold is already `0.0` inside the gate). Byte-identical heads-up (exponent 0).
- **B-ii (magnitude, DIRECTIONAL-only):** whether `_MW_CATCH_TIGHTEN = 1.15` is strong enough. Measured
  base + scope sweep, **live sampler** (constants monkeypatched in-process), facing a 1.37× raise, SPR 10,
  P(call):

  | bucket | persona | scope · base | n=1 | n=2 | n=3 | n=4 |
  |---|---|---|---|---|---|---|
  | MIDDLE_PAIR | station | today · 1.15 | 0.9024 | 0.8898 | 0.8758 | 0.8603 |
  | MIDDLE_PAIR | station | new · 1.30 | 0.9024 | 0.8776 | 0.8475 | 0.8112 |
  | MIDDLE_PAIR | station | new · 1.50 | 0.9024 | 0.8619 | 0.8076 | **0.7379** |
  | **TOP_PAIR** | station | **today · 1.15** | 0.9715 | 0.9715 | 0.9715 | **0.9715** |
  | **TOP_PAIR** | station | **new · 1.15** | 0.9715 | 0.9681 | 0.9643 | **0.9599** |
  | TOP_PAIR | station | new · 1.50 | 0.9715 | 0.9604 | 0.9442 | **0.9209** |
  | MIDDLE_PAIR | fish | today · 1.15 | 0.3126 | 0.2839 | 0.2569 | 0.2315 |
  | MIDDLE_PAIR | fish | new · 1.50 | 0.3126 | 0.2339 | 0.1698 | **0.1204** |
  | **TOP_PAIR** | fish | **today · 1.15** | 0.6428 | 0.6428 | 0.6428 | **0.6428** |
  | **TOP_PAIR** | fish | **new · 1.15** | 0.6428 | 0.6137 | 0.5833 | **0.5519** |
  | TOP_PAIR | fish | new · 1.50 | 0.6428 | 0.5551 | 0.4607 | **0.3672** |

  `P(raise)` falls monotonically in `n` in **every** row of that sweep (e.g. fish `TOP_PAIR` new · 1.15:
  0.0412 → 0.0393 → 0.0374 → 0.0354) — the `N-logit` guard holds for the scope change as well, for the
  same structural reason as §A8.

  **There is no sourced per-headcount defense target** (contract §4 row P9 is tagged
  "DIRECTIONAL-only (never gates a build)"; §5's bands are aggregates over headcount). So B-ii **may not
  be a HARD gate** and should be filed as a *reported* fit alongside `W4-b`'s single re-anchor, not as its
  own acceptance criterion. **Recommend: ship B-i's scope fix with the base left at 1.15, and hand the
  base to `W4-b`.** Moving both scope and base in one slice makes the observed band delta unattributable.
- **Explicit non-coverage, named in the ticket:** the `TWO_PAIR_PLUS`+ pile-up seat (§B4's `99` case) is
  **not** fixable by any fold-merit mechanism and belongs to `W4-a`/`M6` plus contract §4 row P6's
  pending amendment (`persona-realism.md:1529-1548`).

---

# C. Ready-to-file ticket sketches

Every pass/fail below asserts on **NORMALIZED probability vectors** captured with the
`node_trace.py:51-66` rng, never on raw merits (per `persona-realism.md:1903-1905`). Each has a
**DEFECT gate that FAILS at the pinned commit** (so the ticket cannot pass vacuously — the R9-3
cannot-fail-gate lesson) and **PRESERVATION checks** labeled as already-passing.

### `R10-TAIL-a1` — piecewise absolute-price tail above the OVERBET representative

*Scope:* `backend/app/domain/personas_postflop.py` (`_price_factor` + one new mechanic constant) and its
test file. **Nothing else.** Not a dial ticket; no pack JSON changes.

*Mechanism:* `M3` additive-exponent piecewise ladder, §A8. Gate: `f > 1.5` OR (`f > 1.10` AND
`facing_raise`). `K` = shared mechanic constant, seed 2.0, range [1.5, 2.5].

*Pass/fail — station, `AIR`/`NONE` (`7h2s` on `Ks Qd 8c`), HU, FLOP, SPR 10, `facing_raise=True`:*

| # | assertion | at HEAD |
|---|---|---|
| ① **DEFECT gate** | `P(call \| f=2.33) < P(call \| f=1.51) − 0.05` | **FAILS** — both exactly `0.4044` |
| ② **DEFECT gate** | `P(call \| f=4.00) < P(call \| f=2.33)` (strictly monotone tail) | **FAILS** — both `0.4044` |
| ③ **`N-logit` guard** | `P(raise \| f=2.33) <= P(raise \| f=1.51)` at every K in range | passes; must survive |
| ④ **no-fold-floor guard** | no literal fold clamp in the diff; `0 < P(fold) < 1` at every swept cell | passes; must survive |
| ⑤ **α-ceiling preservation** | (a) vector at `f ∈ {0.30, 0.55, 0.90, 1.10}` byte-identical to §A2 for **both** `facing_raise` values; (b) vector at `f ∈ {1.11, 1.45, 1.50}` byte-identical to §A2 **when facing a BET** — this is the leg that protects the fish's 0.78-pt α headroom (`:344-346`) | passes; must survive. ⚠️ If the owner picks the D4 fallback gate (`f > 1.5` only), (b) must hold for `facing_raise=True` as well — verified byte-identical at f = 1.45 in the probe. |
| ⑥ **persona-dispersion guard** | maniac `P(raise \| AIR, f=2.33)` ≥ **0.40 ×** its HEAD `0.1922` (= 0.0769) | **additive K=2.0 passes (0.0923 = 0.48×); multiplicative k=2.0 FAILS (0.0290 = 0.15×)** — this is the assertion that forces the additive form. Additive K=1.5 → 0.1119 (0.58×). |
| ⑦ **preservation** | `./scripts/verify.sh` green; AF / fold-to-c-bet / WTSD bands unchanged | (⑦ is the real regression risk — see D3) |

*Also required:* ace-high twin of ①/② (station `ACE_HIGH` HEAD plateau is `0.6992`, the larger defect).

### `R10-TAIL-b1` — multiway continue scope: add `TOP_PAIR` to `_MW_CATCH_BUCKETS`

*Scope:* one tuple (`personas_postflop.py:520`) + its comment + tests. Base stays **1.15**.

*Pass/fail — `TOP_PAIR`/`NONE` (`AhTh` on `As 7d 2c`), facing a 1.37×-pot raise, FLOP, SPR 10:*

| # | assertion | at HEAD |
|---|---|---|
| ① **DEFECT gate** | station `P(call \| n=4) < P(call \| n=1) − 0.005` | **FAILS** — both exactly `0.9715` |
| ② **DEFECT gate** | monotone: `P(fold)` strictly increasing over `n = 1,2,3,4` for station, fish, nit | **FAILS** — constant |
| ③ **`N-logit` guard** | `P(raise \| n=4) <= P(raise \| n=1)` for all six personas | must hold |
| ④ **HU byte-identity** | every persona's `n=1` vector byte-identical to §B2 | must hold (exponent 0) |
| ⑤ **confounder guard** | ① and ② also hold with SPR set **below** each persona's `spr_commit` | must hold — proves the mechanism is not riding the commit gate |
| ⑥ **documented non-coverage** | `OVERPAIR_TPTK` and `TWO_PAIR_PLUS` vectors byte-identical at all `n`, above **and** below `spr_commit`; a comment names `W4-a`/P6 as the owner | must hold — this ticket must not silently claim the pile-up class |
| ⑦ **preservation** | three HARD-today bands unchanged; sim fixtures re-recorded ONLY under the lane's fixture-ownership rule (`persona-realism.md:540-543`) | — |

### Not filed here (recorded, with owners)

| deferred question | owner |
|---|---|
| plateau **height** at f ∈ (1.10, 1.50] — the `call_looseness = 4.0` level | `R9-LOOSEFIT` + `W4-b` re-anchor (§A6) |
| stack-relative tail `c = to_call/stack` (contract §4 P3, **not built at HEAD**) | `W4-a` — must land **after** `R10-TAIL-a1` (§A8) |
| bet / raise / **jam** action-kind axis; jam signal from `min_bb == max_bb` | `R9-DEFENCE` question 3 (§B5) |
| `_MW_CATCH_TIGHTEN` base magnitude (1.15 → ?) | `W4-b`, reported not gated (§B5 B-ii) |
| `TWO_PAIR_PLUS`+ pile-up seats where fold is already `0.0` | `W4-a` / `M6` + contract §4 P6 amendment |

---

# D. Open risks

1. **⚠️ D1 — no sourced target for either mechanism.** Contract §7's citing gate (`:220`) requires a
   provenance triple for any cited target. There is **no sourced fold-to-overbet-raise frequency** and
   **no sourced per-headcount defense frequency** in the contract; §5's size-bucket FtC slope row is
   `HARD-pending #4`. Both `K` and the `_MW_CATCH_TIGHTEN` base are therefore **DIRECTIONAL seeds fitted
   to a shape argument, not to a measured target.** The tickets above are gated on *monotonicity and
   direction*, which is defensible; **any numeric level either ticket quotes is unsourced and must be
   labeled as such.**
2. **D2 — `size_elasticity` is now doing two jobs.** `M3` reuses the same exponent for head and tail. If
   a later slice re-fits `size_elasticity` against the aggregate FtC slope, it silently re-fits the tail
   too. Alternative (not recommended, recorded): a separate `tail_elasticity` lever — rejected here as
   lever proliferation against `N-vecfit`'s finding that the current lever set is already
   block-triangular, but a reviewer may reasonably prefer it.
3. **⚠️ D3 — band-regression risk is concentrated in `M3`, not in B-i.** `M3` raises fold merit in a
   region the arrival-range harness does sample (compounded raises reach f > 1.5 in real play), so
   fold-to-c-bet and WTSD **can** move even though the α-measured 1.5× node is byte-identical. The
   `facing_raise` gate limits but does not eliminate this. **`W4-b` is the single re-anchor
   (`persona-realism.md:466-467`) — neither ticket may re-anchor a band.** If `M3` moves a HARD-today
   band, the correct response is to reduce `K` or tighten the gate, not to re-anchor.
4. **D4 — the `facing_raise` gate is a thin scope fence.** §A7 argues it is a fence, not a line response,
   with two in-file precedents. A reviewer may still call it an `R9-DEFENCE` encroachment. The fallback
   (gate on `f > 1.5` only, no `facing_raise`) is fully α-safe but covers only **1 of 3** R10-2 exhibits
   (h588's 2.33×) — h579's 1.45× and h81/h385's 1.50× fall inside the engine's own authored size range
   and are then §A6's height defect, i.e. `W4-b`'s. **This fork is the one owner decision this pass
   cannot make alone.**
5. **D5 — exhibit boards were not re-read.** §B4's taxonomy trap (`99` vs `44` on a paired board) is
   demonstrated on constructed fixtures. **The actual h697 / h726 / h217 / h129 boards were not pulled**
   (they are in the gitignored 756-hand artifacts). Before `R10-TAIL-b1` cites those exhibits, someone
   must classify each seat's real bucket — a `TWO_PAIR_PLUS` seat is a `W4-a` exhibit, not a
   `R10-TAIL-b1` one, and mis-filing it makes the ticket unable to fix its own cited hand.
6. **D6 — the maniac's legacy exponent is an unexamined accident.** `maniac.json` has no
   `size_elasticity`, so it takes the LEGACY inverse branch and lands at **2.4064 — the steepest price
   response in the roster**, purely because its `stickiness` is low (0.55). Any tail mechanism keyed on
   that exponent hits the maniac hardest, and R10-2 explicitly refuted the defect claim for the maniac.
   Assertion ⑥ guards it; the underlying oddity (four of six personas never opted into W2-a) is worth its
   own look and is **not** this pass's to fix.
7. **D7 — `T-STICKY` precedence.** `R10-TAIL(a)`'s ticket touches the facing policy and would edit
   `backend/tests/test_personas_postflop.py`, which `T-STICKY` owns
   (`persona-realism.md:530-534`). Both tickets must wait for `T-STICKY` to land, per the roadmap's own
   ordering. This pass, being read-only, has no such constraint.
