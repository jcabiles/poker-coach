# RES-D — Theory→engine calibration: price-aware defense + size-linked bluff bands + re-derived S4

**Spike, Epic 4 (bot-math-fix). Output = decision doc + target numbers. NO app code.**
Created 2026-07-21. Consumes the vetted poker-math docs (Obsidian vault:
*Comprehensive Reference* §2–§3, *Calibration & Numbers (Spec)* §1/§3/§9,
*Persona & Multiway Modeling* §1–§3) and their Sol+Opus adversarial review
(`docs/ai-dlc/research/poker-math-review/SYNTHESIS.md` — **zero arithmetic errors**;
the A1 fold-ceiling guardrail below is their #1 finding).

Tags: **[SOLVED]** provable arithmetic · **[SOURCED]** cited · **[DERIVED]** we computed it
(α-anchored + exploit-direction), use as a design target not a truth.

---

## 0. What's actually broken (root cause, from the engine)

`backend/app/domain/personas_postflop.py::sample_postflop_decision`:

- **Price-blind defense [CONFIRMED].** Facing a bet (lines 288–292) the fold/call/raise
  merits are `_FOLD_BASE[bucket]`, `_CALL_BASE[bucket]`, `_RAISE_BASE[bucket]` — **functions
  of the hand bucket only.** Nothing reads the faced size, `to_call`, pot odds, or α. A bot
  folds the *same* to a ⅓-pot stab and a pot-sized barrel. → **F1 must make fold/call move
  with faced size.**
- **Bluff frequency decoupled from size [CONFIRMED].** `bluff_mass = pf.bluff_freq * noise *
  damp` (line 284) is flat; for a betting air hand `agg_merit = bluff_mass` (line 303); the
  **size is drawn independently afterward** (line 337, "independent of bucket"). So a persona
  bluffs at the same rate whether it picks ⅓-pot or 2×-pot. → **F2 must link bluff frequency
  to the chosen size.**
- **Maniac aggression saturation.** Levers below: maniac `aggression = 15.0` vs the next
  highest (lag) `3.2`. `agg_scale = pf.aggression * noise` multiplies one side of an
  un-normalized merit ratio → the bet/raise weight dominates the `rng.choices` mix → near-
  argmax (deterministic-feeling) spew. → **F3 must bound/renormalize aggression.**

### Current persona levers (postflop block) — the calibration starting point
| Persona | aggression | stickiness | bluff_freq | spr_commit | multiway_bluff_damp |
|---|---|---|---|---|---|
| nit | 0.6 | 0.6 | 0.04 | 1.2 | 0.3 |
| tag | 2.4 | 0.6 | 0.22 | 2.5 | 0.55 |
| lag | 3.2 | 0.55 | 0.35 | 3.0 | 0.65 |
| calling_station | 0.5 | 1.8 | 0.03 | 1.5 | 0.3 |
| passive_fish | 0.6 | 1.4 | 0.12 | 2.0 | 0.4 |
| **maniac** | **15.0** | 0.55 | 0.55 | 4.0 | 0.85 |

---

## 1. Theory reference lines (the yardstick F1/F2 calibrate to)

### 1a. Faced size → fold-ceiling (α) and break-even-to-call — **[SOLVED]** (Spec §1/§3)
| Faced bet (× pot) | MDF = P/(P+B) | **α = fold CEILING** | Break-even call equity |
|---|---|---|---|
| ⅓ | 75% | **25%** | 20% |
| ½ | 67% | **33%** | 25% |
| ⅔ | 60% | **40%** | 28.6% |
| ¾ | 57% | **43%** | 30% |
| pot | 50% | **50%** | 33% |
| 2× | 33% | **67%** | 40% |

### 1b. Chosen size → polar value:bluff and bluff share — **[SOLVED]** (Spec §3, Reference §3.3)
| Chosen bet (× pot) | value:bluff | **bluff share of betting range** |
|---|---|---|
| ⅓ | 4 : 1 | 20% |
| ½ | 3 : 1 | 25% |
| ⅔ | 2.5 : 1 | 28.6% |
| pot | 2 : 1 | 33% |
| 2× | 1.5 : 1 | 40% |

> Note the two tables move in **opposite** directions with size: a bigger bet lets the
> *defender* fold more (α ↑) AND lets the *bettor* run more bluffs (share ↑). Both are the
> right monotonic shape; the current engine has neither.

### ⭐ 1c. The A1 grading guardrail (Sol+Opus #1 finding) — **[SOURCED]**
α is a **fold-CEILING sanity check**, NOT a "fold ≈ MDF" defend-floor. `P/(P+B)` is the
flat-call form ("doesn't work with a raise" — GTO Wizard); real solver defense often sits
*below* raw MDF pre-river. **Rule for F1 and F5:** a bot/hero that folds the *same regardless
of size* is unambiguously wrong (that's the bug); but do **NOT** flag a fold as too tight
merely because it beat MDF on the flop/turn or vs a capped/polar bettor — there, price is
pot-odds-vs-*actual* value:bluff, not MDF.

---

## 2. Deliverable (a) — Faced-size → fold-to-bet target bands, per persona

**Design contract for F1:** realized fold-to-bet must be **monotone increasing in faced
size** for every persona (the currently-broken property), anchored to the α ceiling line
(§1a), with each persona offset from α by its *exploit direction* (from the modeling doc
player-type bands). TAG ≈ α (textbook); nit **over-folds** (> α, the exploitable leak);
station/fish/maniac **under-fold** (< α, call too much).

**Size buckets** (provisional; RES-E finalizes the cutoffs): **SMALL** ≤0.40p (α≈25%) ·
**MEDIUM** 0.41–0.70p (α≈33–40%) · **LARGE** 0.71–1.10p (α≈43–50%) · **OVERBET** >1.10p
(α≈67%).

Target **fold-to-bet frequency bands** — **[DERIVED — α-anchored + exploit-direction]**:

| Persona | SMALL (⅓) | MEDIUM (½–⅔) | LARGE (¾–pot) | OVERBET (2×) | vs α line |
|---|---|---|---|---|---|
| calling_station | 5–15% | 10–22% | 15–30% | 25–45% | **well under** (sticky 1.8) |
| passive_fish | 8–18% | 15–28% | 22–38% | 35–55% | under |
| maniac | 8–20% | 15–30% | 25–42% | 40–60% | under, erratic |
| lag | 15–25% | 25–37% | 35–48% | 50–65% | ≈α / slightly under |
| **tag** | **20–28%** | **30–42%** | **42–52%** | **60–70%** | **≈ α (textbook)** |
| nit | 25–38% | 38–52% | 52–66% | 68–82% | **over** α (the leak) |

**Invariants F1 must satisfy** (these, not the exact band edges, are the pass/fail):
1. **Monotone:** each persona's fold-to-bet rises across SMALL→OVERBET (the broken property).
2. **Ordering:** for any fixed size, fold-to-bet is `station < fish ≈ maniac < lag < tag < nit`.
3. **Ceiling respect:** no persona's fold-to-bet exceeds the α value for that size *because of
   the price logic* — only nit (deliberate over-fold leak) may sit above α, and that is a
   *persona choice*, not the engine asserting MDF.
4. Call/raise mass absorbs the complement; RAISE stays governed by `_RAISE_BASE × agg_scale`
   (F3-bounded), not by price.

---

## 3. Deliverable (b) — Chosen-size → bluff target, per persona

**Design contract for F2:** at a given *chosen* size, the persona's bluff cadence should track
the polar value:bluff for that size (§1b), **scaled by the persona**. The invariant is the
*shape* (bluff frequency changes with chosen size — currently flat); the persona sets the
*level* and how far it deviates from theory.

Target **value:bluff ratio at the chosen size** — **[DERIVED — polar-anchored + exploit-direction]**:

| Persona | ⅓ (theory 4:1) | ½ (3:1) | pot (2:1) | 2× (1.5:1) | vs theory |
|---|---|---|---|---|---|
| nit | 12:1 | 9:1 | 6:1 | 5:1 | **bluff-starved** (far wider) |
| calling_station | 15:1 | 12:1 | 8:1 | 6:1 | barely bluffs |
| passive_fish | 8:1 | 6:1 | 4:1 | 3:1 | under-bluffs |
| **tag** | **4:1** | **3:1** | **2:1** | **1.5:1** | **≈ theory (textbook)** |
| lag | 3:1 | 2.3:1 | 1.6:1 | 1.2:1 | slightly bluff-heavy |
| maniac | 2:1 | 1.6:1 | 1.2:1 | 1:1 | **over-bluffs at every size** |

**Invariants F2 must satisfy:**
1. **Size-linked:** for each persona, bluff *share* rises (value:bluff tightens toward 1:1) as
   chosen size rises — the broken property (currently flat `bluff_freq`).
2. **Ordering:** at any fixed size, bluff share is `station < nit < fish < tag < lag < maniac`.
3. **Anti-sizing-tell preserved:** F2 links bluff *frequency* to size; it must NOT make the
   chosen *size* a function of hand strength (strength→size stays decoupled — the no-go).
4. The maniac leak is specifically that today it bluffs ~flat-high across sizes; F2 keeps it
   the loosest persona but forces the frequency to *move* with size.

---

## 4. Deliverable (c) — Re-derived S4 bands (measure-then-anchor)

**Why the current bands are engine-anchored, not theory:** the S4 test
(`backend/tests/test_personas_postflop.py:540-570`) documents that WTSD runs **inflated**
(measured 0.40–0.54 vs PRD population 0.20–0.45) *because* the heuristic engine doesn't model
real fold pressure — i.e. **price-blind defense keeps pots alive to showdown.** F1 directly
attacks that cause. So the re-derivation is: **fold-to-cbet becomes size-conditional, and WTSD
should fall toward the PRD population bands once F1 lands.**

| Persona | fold-to-cbet: current single band → **F1 target** | WTSD: current engine-anchored → **post-F1 target (PRD)** |
|---|---|---|
| passive_fish | (0.0, 0.549) → size-conditional per §2 row | (0.450, 0.564) → **(0.30, 0.45)** |
| calling_station | (0.0, 0.424) → §2 row | (0.476, 0.573) → **(0.32, 0.48)** |
| nit | (0.289, 0.961) → §2 row | (0.422, 0.661) → **(0.24, 0.42)** |
| tag | (0.203, 0.797) → §2 row | (0.332, 0.521) → **(0.22, 0.40)** |
| lag | (0.163, 0.637) → §2 row | (0.315, 0.474) → **(0.20, 0.38)** |
| maniac | (0.0, 0.430) → §2 row | (0.228, 0.402) → keep (already honest PRD band) |

- **Method (locked):** F1 changes behavior, so exact WTSD landing can't be predicted a priori.
  **Re-anchor procedure:** (1) land F1's size-conditional fold logic; (2) re-run the S4 harness;
  (3) set each WTSD band to `measured ± 3σ` **and** assert it now overlaps the PRD population
  band above (if it doesn't, tune the §2 fold targets, not the test). The single flat
  fold-to-cbet band is **replaced** by the four size-bucket bands in §2 (a bot must fold more to
  OVERBET than to SMALL — the new regression must check the *slope*, not just a midpoint).
- **[DERIVED-ASSUMPTION]** the PRD WTSD targets are the population bands from
  `docs/ai-dlc/prd/simulate-table.md §8`; treated as the goal F1 moves toward, confirmed by
  measurement in F5, not asserted blind.

---

## 5. Deliverable (d) — A1 guardrail as an explicit grading rule (for F5)

The hero grader (behind the async `StrategyProvider`/`grade_map`) must:
1. **Catch price-blindness (the bug):** a hero fold/call that ignores the faced size is graded
   against the size — folding too much to a small bet, or calling too wide vs a big one, is a
   real leak worth flagging (this is the α-fold-*ceiling* / pot-odds test).
2. **Not over-correct (the A1 guardrail):** do **NOT** grade a hero fold as "too tight / below
   MDF" on the flop or turn, or vs a capped/polar bettor. There the price is
   pot-odds-vs-*actual* value:bluff (§1b), and correct solver defense routinely sits below raw
   MDF. Only the **fold-ceiling** direction (folding *more* than α to a *balanced* bettor, or
   folding identically across sizes) is gradeable-wrong from MDF alone.
3. Keep results **freq + EV, approximate** — never a boolean, never a solver-exact claim.

---

## 6. Multiway (F4 input) — direction only — **[SOLVED math / HEURISTIC implementation]**
Spec §9: the n-th-root fold relationship (√α per opponent) is a **symmetric-independent
idealization** (both reviewers). F4 encodes the *direction* only — **bluff less + value-lean**
per added opponent (the existing `multiway_bluff_damp` lever + `_apply_multiway`) — and must
**never** assert a per-opponent MDF/defense constant. No second multiway model.

---

## 7. Pass/fail for this spike (self-check)
- [x] (a) faced-size→{fold/call/raise} band per persona × size bucket, α-anchored, with the
      monotone + ordering + ceiling invariants F1 must reproduce.
- [x] (b) chosen-size→bluff (value:bluff) curve per persona, polar-anchored, with the
      size-linked + ordering + anti-tell invariants F2 must reproduce.
- [x] (c) re-derived S4 bands: fold-to-cbet → size-conditional; WTSD → PRD targets via a
      measure-then-anchor procedure keyed to F1.
- [x] (d) the A1 fold-ceiling guardrail written as a concrete F5 grading rule.
- [x] every number tagged SOLVED/SOURCED/DERIVED; **no app code touched.**

**Open calls handed to the build slices:** RES-E finalizes the size-bucket pot-fraction
cutoffs F1/F2 key on; F1 chooses the *mechanism* (a price multiplier on `_FOLD_BASE`/`_CALL_BASE`
vs a pot-odds gate) — this doc fixes the *targets*, not the code shape; the §2/§3 band **edges**
are DERIVED design targets (tune within them to hit the §4 WTSD overlap), while the **invariants**
(monotonicity, ordering, size-linkage, anti-tell, ceiling-not-floor) are the hard contract.
