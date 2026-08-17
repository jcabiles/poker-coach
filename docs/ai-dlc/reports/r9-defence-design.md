# R9-DEFENCE — design pass (answers to the five questions)

**Status:** DESIGN PASS. Not a build, not a ticket. No production file was edited; no test was added; no
band, lever, pack or fixture was touched. The only artifact is this report.

**Pinned commit (the grid instrument's pin):** `803e9dc9ee605eb1702bf7f823b28f5a7aaf596b`
(`fix(persona-realism): T-STICKY review C-1 — forbid explicitly-null stickiness by key presence`),
branch `feat/persona-realism-r10-count`, working tree clean apart from untracked/modified docs.
Every number below is reproducible at that commit. **T-ANCHOR (#131) and T-STICKY are both landed**, so
R9-4's prerequisite chain (`T-ANCHOR → T-STICKY → this design pass`) is satisfied.

**What this pass answers:** the five questions in `docs/ai-dlc/roadmap/persona-realism.md:1868-1902`
(`R9-DEFENCE`), in the order the item demands — question 5 (attribution) first, because it is the empirical
core and the other four depend on it.

**Boundary with the sibling item.** The OVERBET absolute-price tail and the multiway continue threshold are
`R10-TAIL` (`persona-realism.md:2056-2069`), not this item. This report measures both channels only far
enough to *subtract* them from the line question, and states where the boundary falls (§Q3).

---

## 1. Method

**Instrument: the DIRECT constructed-policy grid**, per the R10 grid-instrument pin
(`persona-realism.md:1889-1892`). Fixed cards, fixed legal set, fixed price, fixed context; one call to
`sample_postflop_decision` per cell; the **normalized action-probability vector** is captured through a
capture-rng that records the FIRST `rng.choices` call — the same zero-variance technique
`backend/tests/node_trace.py:51-66` uses, and it works because the sampler passes already-normalized
weights (`personas_postflop.py:929`). No simulator, no live corpus, no seeded population run: every number
is a policy read, not a sample, so there is no n and no CI.

**Judged on normalized probability vectors, never raw merits** (`persona-realism.md:1899-1901`).

**Price is stated exactly.** Every cell supplies `latest_aggressor_contribution_bb`, so
`faced_frac = to_call / (pot − contribution)` (`personas_postflop.py:776`) equals the intended pot-fraction
by construction. This matters — see the R9-1 label correction in §2.1.

**Card fixtures.** One board family grown with blanks, chosen so the bucket does not change across streets
(verified, not assumed — probe section A0):

| cell | hole | bucket on `Kd 7c 2h` / `+3s` / `+4d` |
|---|---|---|
| AIR | Qc Jd | `air / none` on all three streets |
| ACE_HIGH | Ac Qd | `ace_high / none` |
| MIDDLE_PAIR | 8h 8s | `middle_pair / none` (R9-1's own cell) |
| TOP_PAIR | Kc Th | `top_pair / none` |
| OVERPAIR_TPTK | Ah Kc | `overpair_tptk / none` |
| TWO_PAIR_PLUS | Kc 7d | `two_pair_plus / none` |
| MONSTER | 7h 7s | `monster / none` |
| STRONG_DRAW | Jh Th on `9h 8c 2h` / `+3d` | `air / strong` (flush draw + OESD) |

Scratch probes live in `$TMPDIR/.../scratchpad/r9_grid.py` and `r9_grid2.py` — **outside the repo**, by
instruction. They are throwaway; the report carries the outputs.

---

## 2. Q5 — ATTRIBUTION (done first)

### 2.1 R9-1 reproduces exactly at the pinned commit — but its price label is wrong

R9-1's published table (`persona-realism.md:253-264`) reproduces **digit-for-digit** at `803e9dc`, using its
literal call (`pot_bb = 10`, `to_call = 5`, no aggressor contribution, stack 200bb, HU, `middle_pair`):

| persona | flop | turn | river | R9-1 published (flop) |
|---|---|---|---|---|
| nit | F0.3798 C0.5658 R0.0544 | identical | F0.4017 C0.5983 R0.0000 | F0.380 C0.566 R0.054 ✓ |
| tag | F0.3265 C0.4864 R0.1871 | identical | F0.4017 C0.5983 R0.0000 | F0.327 C0.486 R0.187 ✓ |
| lag | F0.3211 C0.4354 R0.2436 | identical | F0.4245 C0.5755 R0.0000 | F0.321 C0.435 R0.244 ✓ |
| passive_fish | F0.4847 C0.4530 R0.0622 | identical | F0.5169 C0.4831 R0.0000 | F0.485 C0.453 R0.062 ✓ |
| calling_station | F0.0710 C0.9179 R0.0110 | identical | F0.0718 C0.9282 R0.0000 | F0.071 C0.918 R0.011 ✓ |
| maniac | F0.2715 C0.3681 R0.3604 | identical | F0.4245 C0.5755 R0.0000 | F0.271 C0.368 R0.360 ✓ |

Two things follow.

1. **The exhibit is stable across T-ANCHOR and T-STICKY.** R9-1 was taken at `b581b3d`; it is unchanged at
   `803e9dc`. T-ANCHOR's fix was aggressor-side (`personas_postflop.py:833-841`) and T-STICKY was
   authorship-only, so the facing node did not move. The R9-1 baseline may be cited as current.
2. **⚠️ CORRECTION TO THE RECORD — R9-1's "faced bet 5bb into 10bb (50% pot)" is read by the engine as a
   pot-sized bet, not a half-pot bet.** With no `latest_aggressor_contribution_bb`, the legacy denominator
   at `personas_postflop.py:774` computes `faced_frac = 5 / (10 − max(5, 5)) = 1.00`, which is the RES-E
   **LARGE** bucket (0.71–1.10, α 0.47), not MEDIUM. The true half-pot vector at the same node is materially
   different (nit F0.2637 vs F0.3798; fish F0.3303 vs F0.4847). R9-1's *conclusion* is untouched — the
   flop-vs-turn identity holds at every price — but **the acceptance harness must pass the contribution
   explicitly or its price labels will be wrong**, and this is the §7 denominator-unification trap
   (`persona-realism-theory-contract.md:260`) firing on an analysis probe rather than on production code.

### 2.2 The byte-identity is exact for made hands and FALSE for air / ace-high / draws

Extending R9-1's matched-street counterfactual to all seven buckets (frac 0.50, SPR 20, HU, faced BET):

| bucket class | worst flop-vs-turn deviation over all six personas |
|---|---|
| MIDDLE_PAIR, TOP_PAIR, OVERPAIR_TPTK, TWO_PAIR_PLUS, MONSTER | **0.000000** (exact) |
| ACE_HIGH | up to **0.1002** (maniac: F0.3313 → F0.3802) |
| AIR | up to **0.1142** (maniac: F0.5142 → F0.6121) |
| STRONG_DRAW | up to **0.1070** on the raise leg (maniac R0.6099 → R0.5029; fold +0.0461) |

**Cause, and it is entirely aggression-side.** For `AIR`/`ACE_HIGH` with no draw the cell is `bluff_cell`
(`:706-708`), so its RAISE merit is `_BLUFF_RAISE_FACTOR × bluff_mass` (`:804`) and `bluff_mass` already
carries `_STREET_AGG_MULT` (`:323`, applied `:738`). For draws, `_DRAW_RAISE_BONUS` is street-decayed
(`:820`). Removing raise merit lifts the normalized fold and call share **with no defensive change
whatsoever** — precisely the confounder R9-1 itself warns about (`persona-realism.md:277-283`).

**Consequence for the acceptance harness, and it is the sharpest one in this report:** a flop-vs-turn
identity test written on an AIR cell **already breaks at HEAD, by up to 11 points of fold probability, with
zero line awareness in the engine**. Such a test would certify a no-op as a fix — the exact R9-3 gate-design
defect. **The identity that must break under R9-DEFENCE has to be measured on the made-hand cells**
(MIDDLE_PAIR / TOP_PAIR), where it is exactly 0.000000 today, and the air cells must be asserted as a
*delta against mechanic-off*, never as an absolute street difference.

### 2.3 Channel-by-channel attribution

Each channel measured in isolation at the turn, `middle_pair` unless stated.

**(a) PRICE — the largest channel, and it is scale-free.** `P(fold)` by faced pot-fraction:

| cell | persona | 0.25× | 0.50× | 0.90× | 1.50× | span |
|---|---|---|---|---|---|---|
| MIDDLE_PAIR | nit | 0.1203 | 0.2637 | 0.3798 | 0.5224 | **+0.402** |
| MIDDLE_PAIR | passive_fish | 0.1339 | 0.3303 | 0.4847 | 0.6541 | **+0.520** |
| MIDDLE_PAIR | calling_station | 0.0344 | 0.0550 | 0.0710 | 0.0932 | +0.059 |
| ACE_HIGH | passive_fish | 0.2608 | 0.5294 | 0.6822 | 0.8119 | **+0.551** |
| TOP_PAIR | passive_fish | 0.0329 | 0.0978 | 0.1713 | 0.2936 | +0.261 |
| TOP_PAIR | calling_station | 0.0080 | 0.0131 | 0.0171 | 0.0229 | +0.015 |

Absolute pot size is **irrelevant** at fixed fraction and fixed SPR: pre-bet pot 10bb vs 40bb gives
`maxdev = 0.000000000` for every persona. So "the pot grew" is not a channel; **only the fraction is**, and
the fraction reaches the engine through `_price_factor` (`:554-560`) via the RES-E bucket.

**(a′) …and in live play the fraction DOES grow by street, from the packs' own authored ladders.** TAG's
`sizing_by_node` (`content/personas/tag.json`) means a defender faces mean fraction **0.423** on
`cbet_dry` and **0.700** on `turn_barrel`. Expected fold probability against those two ladders, same bucket,
same street logic, **no line term anywhere**:

| cell | station | nit | lag | fish | tag | maniac |
|---|---|---|---|---|---|---|
| MIDDLE_PAIR | +0.021 | **+0.150** | +0.131 | **+0.203** | +0.132 | +0.113 |
| ACE_HIGH | +0.042 | **+0.202** | +0.198 | **+0.245** | +0.197 | +0.189 |
| TOP_PAIR | +0.005 | +0.052 | +0.039 | +0.079 | +0.040 | +0.030 |

**This is the headline attribution result: 11–25 points of "the bots fold more on the turn" is pure price,
generated by the aggressor's authored size ladder, and it is LARGER than any plausible line effect** (§Q4's
directional ladder predicts +0.03…+0.15 on the same cells). Any fit of a line mechanism against a
per-street *aggregate* — R9-2's profile included — is therefore fitting the price channel and calling it a
line channel. R9-2 stays REPORTED, never a fit target (`persona-realism.md:305-307`, `R9-SHAPEGATE`).

**(b) SPR / commit gate — a fold-ZERO switch, not a gradient.** `P(fold)` is *exactly invariant* across
stack/pot ∈ {20, 4, 2.5, 1.5, 1} for AIR, ACE_HIGH, MIDDLE_PAIR and TOP_PAIR — SPR reaches the vector only
through the commit block (`:899-921`). Where it fires, fold is the literal `0.0`:

| cell | station (spr_commit 1.5) | nit (1.2) | fish (1.4) | tag (2.5) | lag (3.0) | maniac (3.3) |
|---|---|---|---|---|---|---|
| OVERPAIR_TPTK, SPR 2.5 | 0.0059 | 0.0298 | 0.0379 | **0.0000** | **0.0000** | **0.0000** |
| OVERPAIR_TPTK, SPR 1.0 | **0.0000** | **0.0000** | **0.0000** | **0.0000** | **0.0000** | **0.0000** |
| MONSTER, any SPR | **0.0000** | **0.0000** | **0.0000** | **0.0000** | **0.0000** | **0.0000** |

MONSTER folds 0.0 at every SPR because `_FOLD_BASE[MONSTER] = 0.0` (`:259`) — no gate needed.
**Any continue-side or fold-side multiplier is INERT wherever `P(fold) = 0`.** That is W4-a's documented
cannot-fail defect (`persona-realism.md:313-316`) and it applies to this item identically: R9-DEFENCE
**cannot** fix late-street stack-offs, and must not claim to. Those belong to W4-a / M6.

**(c) HEADCOUNT — reaches only three buckets.** ΔP(fold) from 1 → 3 opponents:

| cell | station | nit | lag | fish | tag | maniac |
|---|---|---|---|---|---|---|
| AIR | +0.073 | +0.053 | +0.125 | +0.071 | +0.103 | +0.112 |
| ACE_HIGH | +0.032 | +0.077 | +0.105 | +0.090 | +0.096 | +0.094 |
| MIDDLE_PAIR | +0.017 | +0.058 | +0.051 | +0.065 | +0.052 | +0.045 |
| TOP_PAIR / OVERPAIR_TPTK / TWO_PAIR_PLUS / MONSTER | **+0.000** | **+0.000** | **+0.000** | **+0.000** | **+0.000** | **+0.000** |

The only facing-side headcount term is `_MW_CATCH_TIGHTEN` on `_MW_CATCH_BUCKETS`
(`:519-520`, applied `:780-781`). **The exact zeros for TOP_PAIR and above are the direct measurement of
R10-5's finding** ("nothing raises the multiway CONTINUE threshold") — and they are **`R10-TAIL`(b)'s
subject, not this item's**. Recorded here as the boundary, not answered.

**(d) TAXONOMY — not a channel in this grid.** Every cell held its `(bucket, draw)` class on all three
streets (probe A0). Bucket recomputation *is* a real confounder in live corpora (a longer board changes
classes) but it is eliminated by construction here, which is the point of the direct grid.

### 2.4 The N-logit pathology, reproduced on the live code path

Halving each pack's effective call multiplier (`call_looseness`, or `stickiness` where the split lever is
unset — maniac) and re-reading the vector at the reference node:

| persona | cell | base | call ×0.5 | ΔFOLD | ΔRAISE |
|---|---|---|---|---|---|
| lag | TOP_PAIR | F0.0531 C0.5424 R0.4046 | F0.0729 C0.3721 R0.5551 | +0.020 | **+0.151** |
| tag | TOP_PAIR | F0.0560 C0.6240 R0.3200 | F0.0814 C0.4535 R0.4651 | +0.025 | **+0.145** |
| maniac | TOP_PAIR | F0.0407 C0.4161 R0.5432 | F0.0514 C0.2627 R0.6859 | +0.011 | **+0.143** |
| maniac | MIDDLE_PAIR | F0.1779 C0.4154 R0.4067 | F0.2246 C0.2621 R0.5133 | +0.047 | +0.107 |
| nit | MIDDLE_PAIR | F0.2637 C0.6717 R0.0646 | F0.3971 C0.5057 R0.0972 | +0.133 | +0.033 |
| fish | ACE_HIGH | F0.5294 C0.4236 R0.0470 | F0.6717 C0.2687 R0.0596 | +0.142 | +0.013 |

**Confirmed as documented, with the magnitude ordering that matters:** for the aggressive personas the freed
call mass goes **overwhelmingly to RAISE** (lag TOP_PAIR: +0.151 raise vs +0.020 fold — a 7.5:1 misroute).
This is the live corroboration R10-4 reports (`persona-realism.md:468-476`), now reproduced as a policy
read at a pinned commit. **Any mechanism that removes call mass without controlling the raise path makes
these bots wilder while appearing to tighten them.**

### 2.5 Movable room (the input to Q3's scope decision)

Reference node: turn, HU, SPR 20, faced BET at 0.50 pot.

| cell | station | nit | lag | fish | tag | maniac |
|---|---|---|---|---|---|---|
| AIR | F.447 C.545 R.008 | F.824 C.151 R.025 | F.703 C.118 R.179 | F.834 C.107 R.059 | F.749 C.137 R.114 | F.612 C.103 R.285 |
| ACE_HIGH | F.116 C.882 R.003 | F.459 C.524 R.018 | F.423 C.443 R.135 | F.529 C.424 R.047 | F.429 C.490 R.082 | F.380 C.398 R.222 |
| MIDDLE_PAIR | F.055 C.934 R.011 | F.264 C.672 R.065 | F.216 C.503 R.281 | F.330 C.589 R.081 | F.221 C.563 R.216 | F.178 C.415 R.407 |
| TOP_PAIR | F.013 C.971 R.016 | F.074 C.821 R.105 | F.053 C.542 R.405 | F.098 C.763 R.140 | F.056 C.624 R.320 | F.041 C.416 R.543 |
| OVERPAIR_TPTK | F.006 C.952 R.043 | F.030 C.715 R.255 | F.015 C.320 R.665 | F.038 C.637 R.325 | F.017 C.405 R.578 | F.010 C.214 R.777 |
| TWO_PAIR_PLUS | F.007 C.910 R.083 | F.030 C.562 R.409 | F.011 C.189 R.800 | F.036 C.473 R.491 | F.013 C.252 R.734 | F.007 C.118 R.875 |
| MONSTER | F.000 C.812 R.188 | F.000 C.350 R.650 | F.000 C.085 R.915 | F.000 C.274 R.726 | F.000 C.119 R.881 | F.000 C.050 R.950 |
| STRONG_DRAW | F.093 C.888 R.019 | F.372 C.535 R.093 | F.273 C.361 R.366 | F.443 C.446 R.111 | F.290 C.418 R.292 | F.214 C.283 R.503 |

Read: continue probability is ≥ 0.96 for every persona from OVERPAIR_TPTK upward, and MONSTER cannot fold at
all. **The only cells with room for a defensive response are AIR, ACE_HIGH, MIDDLE_PAIR, TOP_PAIR and the
draw class** — which is also what poker says should respond.

---

## 3. Q2 — STAGE (the core open design work)

### 3.1 Recommended mechanism

**RECOMMENDED — a line-keyed shift of the stage-1 continue-versus-fold LOG-ODDS, with stage 2 untouched.**

Let the facing node's assembled merits be `F` (fold), `C` (call), `R` (raise) — unchanged in construction
from today (`:777-824`). Define

```
   D            = C + R                        # stage-1 "continue" mass (defend)
   P(continue)  = D / (D + F)                  # stage 1
   P(raise|cont)= R / (C + R)                  # stage 2
   ---------------------------------------------------------------------------
   line term:   D'    = D · exp(−λ_p · g(line))         λ_p ≥ 0, g(0) = 0, g(1) = 1
   equivalently logit P'(continue) = logit P(continue) − λ_p · g(line)
   ---------------------------------------------------------------------------
   P'(fold)  = 1 − D'/(D'+F)
   P'(call)  = D'/(D'+F) · (1 − P(raise|cont))
   P'(raise) = D'/(D'+F) ·      P(raise|cont)
```

`λ_p` is the per-persona lever (§Q4); `g` is the line-state map (§Q1); `line = 0` reproduces today exactly.

**Where it attaches in the current merit assembly.** In the facing-chips branch of
`sample_postflop_decision`, **after** the SPR-commit block (`:899-921`) and **immediately before** the
normalization (`:923-929`). Concretely: one helper `_line_continue_mult(pf, aggressor_barrelled) -> float`
and one loop that multiplies the CALL and RAISE entries by it. Three reasons for that exact position:

- **After the commit block** because W2-b's B5b damp *subtracts absolute quantities* from the CALL and RAISE
  merits (`:916-919`). Scaling before the subtraction would change the subtraction's relative size and can
  drive a merit negative into the `max(m, 0)` clamp (`:924`); scaling after is the clean "shrink the whole
  defend candidate" semantics.
- **Before normalization** because the object being shaped is a merit, and the observed effect must be the
  softmax's own — no post-hoc probability surgery.
- **Never inside `_commit_transform`** (`:610-623`). Where the gate fires, `F` is the literal `0.0`, so
  `P(continue) = 1` and the factor is arithmetically inert (measured, §2.3(b)). That is a *declared*
  limitation, not a hidden one.

### 3.2 Why this cannot inflate raises — proved, not asserted

Scaling **both** defend merits by the same factor inside the single existing normalization is *algebraically
identical* to the stage-1 odds shift above, and leaves `P(raise | continue)` exactly invariant. Verified
numerically at the reference node: the two computations agree to **≤ 1.11e-16** for all six personas, and
`raise|continue` is bit-identical before and after (probe K, and the `raise|cont base/new` column of probe
H: `0.0119/0.0119`, `0.0877/0.0877`, `0.3587/0.3587`, `0.4947/0.4947`, …).

Three consequences worth stating plainly:

1. **The `N-logit` pathology cannot fire through this mechanism.** Unlike a `call_looseness` cut (§2.4,
   +0.151 raise for lag), the line term moves *nothing* into RAISE: the freed mass goes to FOLD by
   construction, in the exact proportion the odds shift dictates.
2. **The mechanism is AF-neutral at the node by construction.** AF is bets+raises over calls; scaling CALL
   and RAISE by the same factor leaves the node's raise:call ratio untouched. Population AF can still move
   through composition (fewer continued streets ⇒ a different downstream node mix), so AF stays a
   **no-regression** check, but no per-node AF damage is possible. One of the three HARD-today gates is
   structurally protected.
3. **It composes with `N-logit` rather than depending on its lever re-routing.** `N-logit`
   (`persona-realism.md:1786-1792`) splits the normalization into the same two stages and then routes
   `call_looseness` to stage 1 and `aggression` to stage 2. The line term lives in stage 1 in either world,
   and the stage split itself is an *identity* (`D = C + R` reproduces today's vector exactly), so the two
   items do not conflict at the mechanism level. **Keep `N-logit` first anyway**, for two reasons that
   survive the algebra: (i) fitting `λ_p` means fitting a *continue* probability, and the stage decomposition
   is what makes that quantity the object of measurement rather than a corner of a 3-way vector;
   (ii) `R9-LOOSEFIT` will be cutting call mass on the same node in the same programme, and until
   `_RAISE_BASE` is lever-controlled the facing node's raise share is not interpretable, so a defensive fit
   read against it would be reading someone else's error. **Recorded amendment:** `N-logit` is a
   prerequisite of the *fit*, not of the *mechanism*; if `N-logit` slips, R9-DEFENCE can still be built and
   shown correct in shape, but it may not be fit to a target.

### 3.3 Why this is not the forbidden object

The item forbids "a `street → scalar` map applied to `fold_merit` or `call_merit`"
(`persona-realism.md:1871-1874`), forbids a flat multiplier under the softmax law, and forbids an asserted
fold-probability floor. Point by point:

| Prohibition | Why the recommendation is outside it |
|---|---|
| `street → scalar` | **The mechanism reads no street variable at all.** Its only input is the opponent's action history (§Q1). It appears to act "from the turn onward" only because `line = 1` is unreachable on the flop by construction — a property of the *signal*, not a street term in the mechanic. |
| on `fold_merit` or `call_merit` | Fold merit is **never touched**; call merit is never touched *alone*. The factor applies to the **defend aggregate**, which is exactly what makes it raise-neutral (§3.2) and what a scalar on `call_merit` alone could not be. |
| "no flat multiplier" (softmax law) | The softmax objection is that a merit multiplier's observed frequency effect is unknown, so a dropped-in constant is cosmetic (`theory-contract.md:23-31`). Here the effect is a **closed form**: a binary stage's odds multiplier maps to probability exactly and invertibly, so `λ` can be *solved* for a target continue-rate change instead of guessed. Measured inversions for a −0.10 absolute drop in `P(continue)`: nit MIDDLE_PAIR `λ* = 0.4675`, tag `0.5108`, lag `0.5176`, fish `0.4262`, maniac `0.5757`, station `1.1480` — each verified to return the target to 4 decimal places. **This is the property that makes the mechanic fittable rather than cosmetic**, and it is the reason to prefer the odds form over any additive or probability-space shift. |
| no asserted fold floor (A1 guardrail) | No branch writes, clamps or lower-bounds a fold merit or fold probability. `P(fold)` rises only as the complement of a reduced continue mass — the same "the fold share rises through normalization" construction W3R-6 used (`:786-789`, `:359-365`). |

A useful free property: because a constant odds shift moves absolute probability least near the extremes,
**the station moves least before any per-persona lever is applied** (λ = 0.5 at the reference node: station
`P(continue)` 0.9450 → 0.9125, a −0.033 move, versus nit 0.7363 → 0.6287, −0.108). The shape already leans
the archetype-correct way; the lever then makes the ordering deliberate.

### 3.4 Rejected alternatives

- **A `street → scalar` on `fold_merit`** — forbidden by the item, and independently wrong: §2.2 shows the
  street already moves the air cells by up to 0.114 through the aggression side, so a street scalar would be
  fitted against a confound it cannot see, and it cannot distinguish a second barrel from a first turn stab.
- **A multiplier on `call_merit` alone** (the shape `_ACE_HIGH_FLOAT_RAISE_DAMP` uses, `:374`) — measured
  consequence is the `N-logit` misroute: §2.4 is exactly this experiment, and lag/tag/maniac send 7:1 more
  mass to RAISE than to FOLD. Fine for a narrow node-scoped damp on a persona that barely raises; wrong as
  the primary mechanism for a defensive concept.
- **An additive fold-merit boost** — same misroute in mirror image (it dilutes call and raise
  proportionally, which is raise-neutral, but it acts on the *fold* side, which brings the α-ceiling
  aggregate into play and is what HARD-STOPPED W3R-5's one-sided boost, `persona-realism.md:858-871`).
- **An absolute probability shift (`P(continue) −= δ`)** — not invertible near the boundaries, needs
  clamping, and a clamp *is* an asserted floor. Rejected on the A1 guardrail.
- **A mean-preserving line term** (W3R-5's α-neutral trick) — deliberately not adopted here.
  W3R-5's mechanic changes *which boards* you defend at constant aggregate frequency; R9-DEFENCE's whole
  claim is that aggregate continue frequency *should* fall as a line sustains. Mean-preservation would
  design the effect away. The α exposure is instead handled by scope (§Q1: `line = 0` on the flop keeps the
  α fixture's node byte-identical), which is a stronger argument than neutrality because it is structural.

---

## 4. Q1 — STATE

**RECOMMENDED: the minimal binary, with its semantics pinned to CONSECUTIVE POSTFLOP aggression.**

Signal: *did the seat whose wager I am facing also bet or raise on the immediately preceding **postflop**
street?* Working name from R9-SIGNAL kept: `aggressor_bet_prev_street`.

**Two pins that the design pass must add, because R9-SIGNAL as filed would get both wrong:**

1. **⚠️ PREFLOP MUST NOT COUNT.** The existing `bet_prev_street` maps `FLOP → PREFLOP`
   (`postflop_context.py:54-58`) and counts a preflop RAISE, by design and with a comment saying so. Measured
   at HEAD on a textbook HU single-raised pot (BTN raises, BB calls, BTN c-bets the flop):
   `bet_prev_street(history, FLOP, BTN) = True`. So a derivation that mirrors `_PREV_STREET` would label
   **the modal flop c-bet node as sustained aggression**, with two fatal consequences: the R9-1 flop-vs-turn
   identity would *not* break (both streets read `line = 1` whenever the c-bettor raised preflop), and the
   mechanic would fire on the flop facing-a-BET node — the α fixture's node class
   (`tests/test_personas_postflop.py:600-668`) and the fold-to-first-c-bet HARD gate's node. That is the
   architecture that HARD-STOPPED W3R-5. **Fix: the line state is postflop-only, so `line ≡ 0` on the flop
   by construction.** Preflop initiative is `R9-CBET`'s variable, and `bet_prev_street` stays untouched as
   the own-initiative signal (as R9-SIGNAL already requires).
2. **Consecutive, not cumulative.** "Bet the flop, checked the turn, bets the river" is a delayed stab, not
   a third barrel; a *count* of the aggressor's postflop aggressions would score it 2 and over-punish it. The
   binary on the immediately preceding street reads it correctly as `line = 0`.

**Derivation shape (mirrors a landed precedent).** Derive the run length —
`aggressor_barrel_run(history, street, aggressor_position) -> int` (0 on the flop; on the turn 1 if the
aggressor bet/raised the flop; on the river 2 if flop and turn, 1 if only the turn) — and have the consumer
threshold it at `>= 1` for v1, with `g(line) = 1` for any run ≥ 1. This is exactly how `facing_raise` was
rebuilt on `street_aggression_count` (`postflop_context.py:108-142`): one derivation, one taxonomy, a cheap
upgrade path. **The richer state then costs nothing later** — `g(run) = min(run, 2)` or `g(run) = run` is a
one-line change with a pre-registered test, and nothing has to be re-derived.

**Rejected:** (a) *the raw count of prior aggressions by the current aggressor* — non-monotone in
credibility (see pin 2), and there is no sourced target that could distinguish a 2-barrel from a 3-barrel
response, so the extra state buys behaviour we cannot judge; (b) *a `(street, binary)` pair keyed jointly* —
the pair is already implied by reachability (flop:0; turn:0/1; river:0/1) and keying on it explicitly would
re-introduce a street variable into the mechanic, which §3.3 depends on not existing.

**Container — one correction to R9-SIGNAL's plumbing.** R9-SIGNAL says to add the field to
`PostflopContext`. The *derivation* belongs in `table/postflop_context.py`, yes — but the **sampler parameter
should be a flat kwarg**, exactly like `facing_raise`, for the reason documented at
`postflop_context.py:133-140`: `range_estimate.py` must be able to opt into this signal **alone**, and
building a `PostflopContext` there would apply the `in_position=False` default and silently activate W3-b's
position damp in the villain-range reveal — an estimator-parity break. While the field is read by nobody
(R9-SIGNAL) the choice is byte-identical either way; R9-DEFENCE is the consumer that makes it matter, so it
should be decided now. **Recommendation: `aggressor_bet_prev_street: bool = False` as a flat kwarg on
`sample_postflop_decision`, derivation in `postflop_context.py`, `PostflopContext` untouched.**

---

## 5. Q3 — SCOPE

**RECOMMENDED buckets: `MIDDLE_PAIR`, `TOP_PAIR`, `ACE_HIGH`, `AIR` — the bluff-catch class plus the two
one-pair catcher rungs. Draws and rungs ≥ `OVERPAIR_TPTK` excluded in v1.**

Evidence and reasons, per exclusion:

- **MONSTER — mechanically inert.** `_FOLD_BASE[MONSTER] = 0.0` (`:259`) ⇒ `P(fold) = 0` at every price,
  SPR and headcount (§2.5). Including it would be a documented no-op; excluding it makes the scope honest.
- **TWO_PAIR_PLUS — no room, and wrong poker.** `P(fold)` is 0.007–0.036 across the roster; two pair does
  not fold more because the opponent barrelled again. Its continue is a value continue.
- **OVERPAIR_TPTK — excluded for the *bundling* reason the contract already ratified.** That bucket mixes
  true overpairs (AA on K-high, which must never fold to a barrel) with TPTK (which sometimes should).
  Damping it would damp real overpairs — the identical argument that keeps P2's overcard damp off this
  bucket (`theory-contract.md:61`, correction ledger #7 at `:288`, in-code note `:348-350`).
  **Pre-register its inclusion behind W3R-7's bucket split**, and say so in the ticket so the exclusion is
  not later read as an oversight.
- **Draws (`STRONG` / `WEAK`) — excluded in v1, deliberately.** A draw's continue is priced by equity and
  the T1 threshold, and that machinery already exists and already moves with street: `_DRAW_RAISE_BONUS` is
  street-decayed (`:820`), `_STREET_WEAK_DRAW_MULT` kills weak semi-bluffs (`:326`), and B5b damps the
  stack-off below T1 (`:911-921`). Measured at the reference node, the draw cell already shifts flop→turn by
  up to 0.107 on the raise leg (§2.2). Adding a line factor on top, un-jointly-calibrated, is the
  compounding mistake W3R-5 #2 records (`persona-realism.md:879-881`). Pre-register as extension v2 with the
  §7 joint-calibration requirement.
- **AIR / ACE_HIGH — included, with a flag.** They have the most room (station AIR continue 0.553; every
  other persona 0.10–0.30) and folding air to a second barrel is the most obviously correct behaviour in the
  set. **Flag:** these are the `bluff_cell` buckets whose RAISE merit is the polar bluff already carrying
  `_STREET_AGG_MULT` (`:804`, `:738`), so the line factor and the street decay compound on the same cell.
  The composition is *directionally* right (bluff-raising a sustained barrel should be rarer still) but it
  must be jointly calibrated and the air cells must be judged as a **delta vs mechanic-off**, per §2.2.
  Note also that `N-riverair` owns the river air-call absolute (`persona-realism.md:1809-1820`); R9-DEFENCE
  must not pre-empt it — where `call_merit` is already floored to 0 on the river (`:799-800`) the line term
  is inert on the call leg by construction.

**Facing a bet, a raise, or both: fire on ANY facing-chips node (bet or raise), and add no within-street
leg.** The line state is a *cross-street* property of the aggressor; whether the outstanding wager is a bare
bet or a raise is a different axis, already carrying two landed damps gated on `facing_raise`
(`:791-797`, `:812-817`). Stacking a third factor on that node without joint calibration is the collision
W3R-5's re-spec had to fix. **Required in the ticket:** where both fire (facing a turn *raise* from a seat
that bet the flop), document the joint product and show the α-relevant nodes untouched.

**The JAM axis — handed to this item by the sibling pass, and answered: OUT of v1 scope.**
`R10-TAIL`'s design report (`docs/ai-dlc/reports/r10-tail-design.md` §B3/§B5) proves the engine has **no
action-kind axis at all** and hands the bet/raise/**jam** split to R9-DEFENCE question 3, on the ground that
"someone bet and someone raised" is a line state. Two of its findings decide it:

- *A jam is byte-identical to a min-raise at the same price* — telling them apart needs a **new signal read
  off `legal`** (`min_bb == max_bb`), not a lever. That is a plumbing slice with its own derivation and its
  own parity obligation; bundling it into the line mechanism would make the first defensive fit
  unattributable, which is the failure mode question 5 exists to prevent. **Recommend: file the jam
  discriminator separately; R9-DEFENCE v1 treats a jam as the raise it legally is.**
- *`facing_raise` already exists as a HEAD kwarg with a documented α-safety argument* (`:253-257`,
  `:359-365`) — so if a within-street action-kind leg is ever added, it **reuses `facing_raise`** and never
  invents a second signal. Recorded; still not v1 (§ above).

**Explicit boundary with `R10-TAIL` — not answered here.** (a) The OVERBET absolute-price tail: §2.3(a)
measures the price channel but the mechanism for it is `R10-TAIL`(a). (b) The multiway continue threshold:
§2.3(c)'s exact zeros for TOP_PAIR-and-above quantify the gap, and it is `R10-TAIL`(b), whose recommended
move is adding `TOP_PAIR` to `_MW_CATCH_BUCKETS`. **Partition, agreed with that pass: `R10-TAIL`(b) owns the
headcount exponent `n`; `R9-DEFENCE` owns the line.** `λ_p` must **not** be fit to compensate for either —
that is precisely the "compensating error" question 5 exists to prevent.

**One correction to the sibling's collision note.** It records that the two items "act on the SAME
`fold_merit` expression (`:777-781`)". Under the mechanism recommended here that is **not** true: the line
factor multiplies the CALL and RAISE entries and never touches `fold_merit` (§3.1, §3.3). The interaction is
therefore a product of two independent factors on *different* merits inside one normalization — still a
joint-calibration case under §7, and the two slices should still **serialize** (whichever lands second
re-reads its fitted magnitude), but the coupling is weaker and cleaner than a shared-expression edit.

---

## 6. Q4 — PERSONA AXIS

**RECOMMENDED: one new optional pack lever, `line_sensitivity`, authored in `content/personas/*.json`, and
DIRECTIONAL-only.**

**Authorship location: pack JSON, not a code constant.** Non-negotiable under the S4 split — mechanics in
`personas_postflop.py`, every persona-differentiating number in the pack (`personas_postflop.py:5-10`,
`theory-contract.md:252`). A per-archetype table in code would be the same violation as hard-coding
`bluff_freq`.

**Shape.** `line_sensitivity: float | None = Field(default=None, ge=0.0, le=<bound>)` on
`PersonaPostflop`, `None → 0.0 → identity` (default-off byte-identity, `theory-contract.md:257`).
`λ_p = _LINE_DELTA · line_sensitivity`, with `_LINE_DELTA` the shared magnitude in code (the mechanic) and
`line_sensitivity` the per-persona scale (the identity) — mirroring `position_sensitivity` /
`_POSITION_AGG_DELTA` (`:626-639`). **Bound it explicitly**, as W3-b's reviewers forced for
`position_sensitivity` (`:189`): here the risk is not a sign flip (`exp(−λ) > 0` always) but an unbounded λ
degenerating the node to a near-pure fold; `le = 2.0` (⇒ `P(continue)` odds cut by ≥ 7×) is a safe ceiling
with the fitted region well inside.

**Directional ordering (DIRECTIONAL, unsourced — no §5 row exists for fold-to-second-barrel):**

```
nit  >  tag  >  lag ≈ passive_fish  >  maniac  >  calling_station ≈ 0
```

Poker rationale: the nit's whole identity is deference to sustained aggression; the TAG is disciplined but
price-driven; the LAG and the fish continue for different reasons (position/curiosity) but both give up to a
credible second barrel; the maniac responds to a barrel by contesting it, not by folding — its stage-2 raise
share is where its reaction lives, and stage 2 is untouched here; **the station's defining trait is a
line-blind call-down, so `line_sensitivity = 0` is the archetype, not a leak** (same reasoning as
`position_sensitivity = 0` for the recreational packs, `:181-186`, and `size_elasticity = 0` semantics in
W2-a, `:572-576`).

**Predicted effect of a directional seed ladder** (nit 0.60, tag 0.50, lag 0.35, fish 0.35, maniac 0.20,
station 0.10; computed exactly from the closed form, at the reference node — turn, HU, faced BET 0.50 pot,
SPR 20):

| cell | metric | station | nit | lag | fish | tag | maniac |
|---|---|---|---|---|---|---|---|
| MIDDLE_PAIR | ΔP(fold) | +0.0054 | **+0.1312** | +0.0650 | +0.0814 | +0.0977 | +0.0312 |
| TOP_PAIR | ΔP(fold) | +0.0014 | **+0.0529** | +0.0206 | +0.0355 | +0.0331 | +0.0086 |
| ACE_HIGH | ΔP(fold) | +0.0106 | **+0.1482** | +0.0869 | +0.0854 | +0.1243 | +0.0481 |
| AIR | ΔP(fold) | +0.0248 | +0.0710 | +0.0676 | +0.0430 | +0.0821 | +0.0463 |
| all | Δ raise\|continue | 0 | 0 | 0 | 0 | 0 | 0 |

Note the ordering in *probability* space is not the ordering of `λ` (nit > tag > fish > lag > maniac >
station on MIDDLE_PAIR) because base continue rates differ — which is why the **HARD** part of the
acceptance test must be stated in odds space (§7), and the probability table stays DIRECTIONAL.

**Rejected:** (a) *a per-archetype constant in `personas_postflop.py`* — violates the S4 split; (b) *reusing
`call_looseness` or `stickiness` as the line scale* — they are the flat call-merit levers that `N-vecfit`
and `R9-LOOSEFIT` are about to fit against different targets *[N-vecfit later reshaped to fitting rules
only — the fitting itself is `R9-LOOSEFIT`'s; see `reports/n-vecfit-premise.md`]*; overloading them re-couples what W2-a spent a
slice separating; (c) *a HARD per-persona target for fold-to-second-barrel* — no provenance row exists
(§5's turn-barrel row is the **aggressor** side and is DIRECTIONAL at `LOW` confidence,
`theory-contract.md:166`), so gating on a level would be the DIRECTIONAL-gating the project forbids.

---

## 7. Ready-to-file ticket sketch

> Two slices. Both are spine work on `personas_postflop.py`; they must serialize, and the whole pair must
> land after `R9-SIGNAL` and after `N-logit` (mechanism-independent, fit-dependent — §3.2).

### `R9-SIGNAL` — amendments this design pass requires (before it is built)

`R9-SIGNAL` is already filed as buildable. Three pins to add to it, all evidenced above:

1. **Postflop-only prior street.** `line ≡ 0` on the flop. Do *not* reuse `_PREV_STREET`
   (`postflop_context.py:54-58`) — measured: it returns `True` for a flop c-bet by the preflop raiser (§Q1).
2. **Derive the consecutive run length**, expose the `>= 1` boolean to the consumer
   (`street_aggression_count` → `facing_raise` precedent, `postflop_context.py:108-142`).
3. **Flat sampler kwarg, not a `PostflopContext` field** (estimator-parity reason, `postflop_context.py:133-140`).

Its own pass/fail is unchanged: derived, unit-tested, read by nobody, byte-identical, plus the
estimator-parity test proving no divergence.

### `R9-DEFENCE-a` — the stage-1 line response (the build)

**Files it may touch:** `backend/app/domain/personas_postflop.py`,
`backend/app/domain/content/models.py` (the lever), `content/personas/*.json` (six packs — obeys W5-B's
"one owner per JSON file" rule only if no preflop-lane slice holds them concurrently; **check the lane
state at filing time**), `backend/app/domain/table/range_estimate.py` + its parity test,
`backend/tests/test_personas_postflop.py` (new tests only — **no band edits**).

**Mechanism:** §3.1, attached after `:921` and before `:923`, scoped per §Q3, lever per §Q4.

**Pass/fail — the acceptance harness (extends R9-1's grid; hold bucket / draw / price / headcount / SPR /
legal set constant and vary only the LINE):**

1. **RED-FIRST (anti-R9-3).** The harness must be demonstrated failing at the pinned commit `803e9dc`
   (the parameter does not exist there), and the failure recorded in the PR. A test that cannot fail before
   the fix does not gate the fix.
2. **HARD — the R9-1 identity breaks, on the made-hand cells.** At `MIDDLE_PAIR` and `TOP_PAIR`, HU,
   deep (SPR ≥ 10), faced BET at a fixed fraction, the `line = 1` vector differs from the `line = 0` vector
   with `P(fold)` strictly greater, for every persona whose `line_sensitivity > 0`. Measured at HEAD this
   deviation is exactly `0.000000` (§2.2), so the assertion has a real zero to move off.
   **Must be measured with `latest_aggressor_contribution_bb` supplied** (§2.1).
3. **HARD — raise-neutrality.** `P(raise) / (P(call) + P(raise))` is invariant between `line = 0` and
   `line = 1` to within `1e-9` at every grid cell. This is the `N-logit`-proof assertion and it cannot be
   satisfied by a `call_merit`-only or `fold_merit`-only implementation (§2.4 shows both move it).
4. **HARD — the lever is the shift.** The realized log-odds change,
   `logit P(continue | line=0) − logit P(continue | line=1)`, equals `λ_p` to within `1e-9` at every cell,
   and is **strictly monotone** in the intended archetype ordering (nit > tag > lag ≈ fish > maniac >
   station). Asserting in odds space, not probability space, is what makes the ordering assertion valid at
   all (§Q4).
5. **HARD — the flop is byte-identical.** Every flop facing node, and the balanced-villain α fixture
   (`tests/test_personas_postflop.py:600-668`, which passes no `street` and no context), and the
   fold-to-first-c-bet band, are unchanged bit-for-bit. `line = 0` on the flop by construction makes this
   provable rather than lucky, and it is the reason the α HARD-STOP that killed W3R-5 does not apply here.
6. **HARD — default-off byte-identity + estimator parity.** `line_sensitivity` unset ⇒ identity; the flat
   kwarg defaults `False`; the action draw stays the FIRST `rng.choices`; `range_estimate.py` is threaded
   the same signal (its replay already walks per-seat actions and tracks street aggression,
   `range_estimate.py:112-200`, so it needs only a per-street aggressor-seat set) and a parity test proves
   the reveal still matches the live policy.
7. **DIRECTIONAL — the shape.** `ΔP(fold)` is positive and larger for the tighter archetypes at the
   reference node (the §Q4 table is the expectation, not a gate); the station's response is the smallest and
   may be ~0.
8. **NO-REGRESSION, not re-anchored — the three HARD-today gates.** Fold-to-first-c-bet is untouched by
   construction (criterion 5). AF is node-neutral by construction (§3.2) — assert no band exit. **WTSD will
   fall** (fewer turn/river continues ⇒ fewer showdowns), which is the direction §5's C6 re-anchor wants.
   **If any WTSD band exits, STOP** — do not widen it, do not re-scope the test; report and escalate to
   W4-b, the single authoritative re-anchor (`theory-contract.md:261`, §11 item 7). The station's pinned
   floor `0.66` (`tests/test_personas_postflop.py:2377`) is the tightest exposure, which is a second reason
   its `line_sensitivity` should be the smallest value in the ladder.
9. **Coverage delta** reported against the immutable snapshot, per the anti-laundering rule.
10. **Explicitly NOT claimed:** no change wherever the SPR commit gate fires (`P(fold) = 0` ⇒ inert,
    measured §2.3(b)); no multiway continue-threshold change (`R10-TAIL`(b)); no OVERBET tail fix
    (`R10-TAIL`(a)); no `OVERPAIR_TPTK`+ or draw-class response (v2/W3R-7); **no jam discriminator** — a jam
    is treated as the raise it legally is, and the `legal`-derived `min_bb == max_bb` signal is a separate
    slice (§Q3).

**Fit discipline.** `λ_p` seeds are DIRECTIONAL FIT SEEDS. They may be *set* from the closed-form inversion
(§3.3) against a stated continue-rate change at a named reference node — never dropped in, never fit against
a per-street aggregate (§2.3(a′) shows the price channel dominates any such aggregate).

### `R9-DEFENCE-b` (pre-registered, do not build yet)

Extensions, each severable and each needing joint calibration: `g(run) = min(run, 2)` for the river
third-barrel state; the draw class; `OVERPAIR_TPTK` after W3R-7's split; a stage-2 line term (a barrelled-at
bot should arguably also *raise* less often, or, for the maniac, more) — pre-registered so v1's stage-2
invariance is read as a deliberate attributability choice, not an omission.

---

## 8. Open risks

1. **⚠️ The R9-SIGNAL preflop trap is live right now.** `R9-SIGNAL` is filed as buildable and says "add it
   beside the existing derivations". The existing derivation counts preflop raises. If it ships that way,
   R9-DEFENCE becomes a partial no-op on its own headline exhibit *and* moves onto the α fixture's node
   class. This is the single highest-value output of this pass and it must be folded into `R9-SIGNAL`
   **before** that item is built.
2. **R9-1's price label is wrong in the roadmap** (LARGE / pot-sized, not ½-pot — §2.1). Harmless to its
   conclusion, harmful to anyone who reuses the numbers as a price-labelled baseline. The roadmap text
   should be corrected when `R9-DEFENCE` is filed (a doc edit, not this pass's to make).
3. **A naive acceptance test would certify a no-op.** Air/ace-high/draw cells already move by street through
   the aggression side (up to 0.114). Criterion 2 confines the identity assertion to made-hand cells for
   this reason; a reviewer should reject any harness that asserts an absolute street difference on an air
   cell.
4. **The station's WTSD floor (0.66) is a mid-spine trip hazard**, and it is already known to be the wrong
   band (R10-6). A defensive tightening pushes WTSD down toward it. Mitigation: smallest `λ` in the ladder;
   escalation path is W4-b, never a band widen.
5. **Several factors will share this node.** `R10-TAIL`(b)'s `_MW_CATCH_BUCKETS` widening lands on the same
   facing node (different merit — see §Q3's correction — but one normalization), and
   `_ACE_HIGH_FLOAT_RAISE_DAMP` (`:374`) and
   `_ONE_PAIR_RAISE_DAMP` (`:358`) fire facing a raise on flop/turn; W3R-5's fold-side texture boost is
   coming; `R9-LOOSEFIT` will move `call_looseness` on the same cells. §7's joint-calibration rule applies,
   and the *order* in which these land changes the fitted values. Sequencing R9-DEFENCE **before** W3R-5 and
   `R9-LOOSEFIT` keeps its own fit clean; sequencing it after means re-fitting it.
6. **No sourced target exists for the effect size.** Everything about `λ`'s *level* is DIRECTIONAL. The
   honest gates are the structural ones (criteria 3–6, all machine-checkable and none satisfiable by a
   cosmetic change); the behavioural claim stays a shape claim until a fold-to-second-barrel provenance row
   exists — which would be an `R9-SEATPROV`-shaped research slice, not a build.
7. **The mechanism is deliberately blind to what the opponent might hold.** A real player folds to a second
   barrel because the barrel *represents* something. This item buys the line-awareness rung
   (~7/10 on the roadmap's judgement ladder, `persona-realism.md:2092-2096`); it does not buy bluff-catching.
   Do not let a reviewer read the gap as a defect of this design — it is the committed `G1-b/c` ceiling.
