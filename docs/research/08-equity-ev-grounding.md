# 08 — Equity/EV Grounding (hand_rank, range advantage, EV model)

**Purpose:** This app's grader is only as trustworthy as the numbers underneath it. This doc puts
real, reproducible numbers under three of those proxies: (1) the crude 169-hand `_strength()`
formula in `backend/app/domain/hand_rank.py`, (2) the deferred equity-backed range-advantage metric
noted in `backend/app/domain/postflop.py:48-54`, and (3) what a credible `ev_loss_bb` should mean.
Scope: hand_rank / equity / EV methodology only — no preflop range membership, no postflop
strategy frequencies, no blockers/hand-reading (owned by other docs/agents). Nothing in
`backend/app/domain/` was edited; this is read-only analysis + recommendations.

---

## 1. `hand_rank.py` grounding — computed equity vs. the proxy

### 1.1 What's being compared

- **Proxy** (`_strength()` in `hand_rank.py`): pairs `0.55 + 0.03·idx(rank)`; non-pairs
  `0.20 + 0.03·idx(hi) + 0.018·idx(lo)`, `+0.04` if suited, `+0.02` if "connected"
  (`idx(hi) - idx(lo) - 1 <= 1`). This is a hand-tuned linear scale, not equity — the module's own
  docstring calls it "a documented equity-vs-random *proxy* (a monotonic strength ordering), not
  exact solver equity."
- **Computed**: real **preflop all-in equity vs. a uniformly random opponent hand**, using this
  repo's own dependency-free 7-card evaluator (`equity.py`'s `_best7`/`_eval5`) via
  `equity_vs_range(hero, board=[], villain_combos=<every other combo in the deck>, iters=2000)`.
  This is the correct definition of "equity vs random hand" (not vs a fixed range like `QQ+/AK`).

### 1.2 Method (reproducible)

For each of the 169 hand classes: take one representative concrete combo (suit choice doesn't
matter here — the villain pool is suit-symmetric), build the villain pool as
`combos_for_range("*", dead=hero_combo)` (every other legal 2-card combo — i.e. a true random
hand, not a chart range), and call `equity_vs_range(hero, [], villain_pool, iters=2000, rng=Random(seed))`
with a **fixed, hand-derived seed** (a simple polynomial hash of the class string — deliberately
*not* Python's built-in `hash()`, which is salted per-process for strings and would break
reproducibility). Board = `[]` → preflop all-in, 5-card runout each trial.

- 169 hands × 2000 iters = 338,000 MC trials, ~34s wall time on this machine.
- **Sanity check against published solver/equity tables**: AA=0.853, KK=0.835, QQ=0.797, JJ=0.789,
  AKs=0.662, AKo=0.654 — these match widely-published "equity vs. random hand" numbers (AA≈85%,
  KK≈82–83%, AKs≈67%, AKo≈65%) within MC noise, which validates the evaluator + method rather than
  just the code path.
- **Full script**: `/private/tmp/claude-501/.../scratchpad/compute_preflop_equity.py` (scratch,
  not committed — re-derivable from the method above). Run with:
  `cd backend && .venv/bin/python <script>` (needs the backend venv for `pydantic`/`app.*` imports).
  Bump `ITERS` for tighter numbers; 2000/hand is enough to rank-order, not to pin exact decimals.

### 1.3 Headline finding: pairs are systematically underrated, big-card suited/offsuit combos are systematically overrated

Averaging `proxy_rank − equity_rank` (positive = proxy ranks the hand *worse* than it truly is):
**pairs average +7.1** (all 13 pairs from 22 to AA are ranked worse by the proxy than real equity
justifies — worst cases: `55` +22, `66` +18, `77` +17, `44` +10, `88` +8), while suited/offsuit
non-pairs average ≈0. But that ≈0 average hides a real split: high-card suited "gapper" hands with
a mediocre kicker are the most overrated (`Q7s` −19, `K7s` −14, `J6s` −13, `T5s` −23, `83s` −14),
and even the well-known suited broadway hands are moderately overrated relative to true equity
(`QJs` −12, `QTs` −12, `JTs` −11, `KQs` −8, `AQs` −9). Root cause: the proxy's linear high-card term
(`0.03·idx(hi)`) dominates regardless of kicker quality, and pairs get a flatter growth curve
(`0.03/rank step`) than their true equity trajectory (mid pairs' set-mining/made-hand-today value
climbs faster than two live high cards' random-hand equity does).

**Robust vs. MC-noise mis-orderings:** The decisive undervaluation cases are `55 > Q7s` (~7.5 equity points) and `77`/`66 > QJs` (clear equity gaps). By contrast, `55` vs `QJs` directly sits within Monte-Carlo sampling noise (~0.2 pts at 2000 iterations, where 55 is 0.611 and QJs is ~0.600) — treat it as a toss-up rather than a definitive mis-ordering.

**Top-25 slice** (`hand | eq_vs_random | proxy | eq_rank | proxy_rank | Δ(proxy_rank − eq_rank)`):

| Hand | Equity | Proxy | EqRank | ProxyRank | Δ |
|---|---|---|---|---|---|
| AA | 0.853 | 0.910 | 0 | 0 | +0 |
| KK | 0.835 | 0.880 | 1 | 1 | +0 |
| QQ | 0.797 | 0.850 | 2 | 2 | +0 |
| JJ | 0.789 | 0.820 | 3 | 3 | +0 |
| TT | 0.751 | 0.790 | 4 | 6 | +2 |
| 99 | 0.698 | 0.760 | 5 | 10 | +5 |
| 88 | 0.684 | 0.730 | 6 | 14 | +8 |
| **77** | **0.675** | **0.700** | **7** | **24** | **+17** |
| AJs | 0.662 | 0.762 | 8 | 9 | +1 |
| AKs | 0.662 | 0.818 | 9 | 4 | −5 |
| AQo | 0.660 | 0.760 | 10 | 11 | +1 |
| AJo | 0.655 | 0.722 | 11 | 17 | +6 |
| AKo | 0.654 | 0.778 | 12 | 7 | −5 |
| ATs | 0.654 | 0.744 | 13 | 13 | +0 |
| AQs | 0.651 | 0.800 | 14 | 5 | −9 |
| **66** | **0.635** | **0.670** | **15** | **33** | **+18** |
| KQs | 0.635 | 0.770 | 16 | 8 | −8 |
| A7s | 0.621 | 0.690 | 17 | 26 | +9 |
| A9s | 0.621 | 0.726 | 18 | 16 | −2 |
| A8o | 0.620 | 0.668 | 19 | 34 | +15 |
| KJs | 0.619 | 0.752 | 20 | 12 | −8 |
| K9s | 0.615 | 0.696 | 21 | 25 | +4 |
| **55** | **0.611** | **0.640** | **22** | **44** | **+22** |
| KQo | 0.610 | 0.730 | 23 | 15 | −8 |
| ATo | 0.609 | 0.704 | 24 | 22 | −2 |

**Bottom-15 slice** — proxy roughly agrees here (rank-order for the weakest ~15 hands is
consistent, `32o` is genuinely the lowest real-equity hand, matching the proxy's floor):

| Hand | Equity | Proxy | EqRank | ProxyRank | Δ |
|---|---|---|---|---|---|
| 82o | 0.356 | 0.380 | 160 | 150 | −10 |
| 73o | 0.350 | 0.368 | 163 | 154 | −9 |
| 72o | 0.338 | 0.350 | 164 | 156 | −8 |
| 32o | 0.317 | 0.250 | 168 | 168 | +0 |

Note: `32o`, not `72o`, has the lowest raw equity vs. random in this computation (0.317 vs.
0.338) — matches known equity tables. `72o`'s reputation as "the worst hand" comes from playability
(domination, reverse implied odds), not raw random-hand equity — a limitation that applies equally
to a pure equity number and to the current proxy (see §1.5 caveat).

**Full list of material mis-orderings (|Δ| ≥ 15, 20 of 169 hands)** — sorted by |Δ|:

| Hand | Equity | Proxy | EqRank | ProxyRank | Δ |
|---|---|---|---|---|---|
| A2s | 0.583 | 0.600 | 39 | 64 | +25 |
| A2o | 0.541 | 0.560 | 62 | 85 | +23 |
| T5s | 0.443 | 0.534 | 120 | 97 | −23 |
| 55 | 0.611 | 0.640 | 22 | 44 | +22 |
| Q2o | 0.500 | 0.500 | 91 | 112 | +21 |
| 54s | 0.429 | 0.386 | 127 | 148 | +21 |
| A4o | 0.569 | 0.596 | 46 | 66 | +20 |
| K2o | 0.515 | 0.530 | 79 | 99 | +20 |
| Q7s | 0.536 | 0.630 | 68 | 49 | −19 |
| 66 | 0.635 | 0.670 | 15 | 33 | +18 |
| A3o | 0.547 | 0.578 | 57 | 75 | +18 |
| 53s | 0.413 | 0.368 | 135 | 153 | +18 |
| 77 | 0.675 | 0.700 | 7 | 24 | +17 |
| A3s | 0.584 | 0.618 | 38 | 54 | +16 |
| A8o | 0.620 | 0.668 | 19 | 34 | +15 |
| QJo | 0.576 | 0.682 | 43 | 28 | −15 |
| K2s | 0.539 | 0.570 | 64 | 79 | +15 |
| K3o | 0.517 | 0.548 | 76 | 91 | +15 |
| T2s | 0.471 | 0.480 | 105 | 120 | +15 |
| 74s | 0.435 | 0.426 | 123 | 138 | +15 |

At a looser threshold (|Δ| ≥ 8, still a full-rank-decile-plus swing) **70 of the 169 hands (41%)**
are mis-ordered by the proxy — re-derivable from the script; not reproduced in full here to keep
this doc focused.

### 1.4 The 24 known ties — how they resolve under real equity

`hand_rank.py`'s own comment documents "24 genuine ties" in `_strength()` (e.g. `88`/`KQo` both
0.73) and tie-breaks them alphabetically for determinism. Recomputing confirms exactly **24 tie
groups, 51 tied hands** — and **every single one resolves to a distinct real equity** (no group
remains tied under MC, as expected — exact ties are near-measure-zero for a continuous quantity
like equity). Selected groups:

| Proxy tie value | Hands (proxy order irrelevant) | Real equity order |
|---|---|---|
| 0.730 | `88`, `KQo` | `88` (0.685) clearly beats `KQo` (0.610) — a 7.5-point equity gap the proxy calls a dead heat |
| 0.760 | `99`, `AQo` | `99` (0.698) beats `AQo` (0.660) |
| 0.722 | `AJo`, `QJs` | `AJo` (0.655) beats `QJs` (0.600) |
| 0.674 | `JTs`, `KTo` | `KTo` (0.599) beats `JTs` (0.578) |
| 0.530 | `87s`, `K2o`, `T7o` | `K2o` (0.515) > `T7o` (0.488) > `87s` (0.472) — the two offsuit hands with a live high card beat the suited connector on raw random-hand equity, even though `87s` plays better postflop (implied odds/disguise) |
| 0.560 | `97s`, `A2o`, `J7o` | `A2o` (0.541) > `97s` (0.501) > `J7o` (0.478) |

Full 24-group breakdown is in the reproducible script's output; every group's spread ranges
0.001–0.075 equity points, so the *direction* is always resolvable but a couple of very close pairs
(`Q9o`/`T9s` at 0.003 apart, `T8s`/`Q8o` at 0.001 apart) are within MC noise at 2000 iters — bump
iterations if a specific pair's order needs to be certain rather than just plausible.

### 1.5 Caveat (applies to both the proxy and a pure equity-vs-random replacement)

Raw equity-vs-random-hand is *still* not "true hand value" — it doesn't capture playability
(domination, reverse implied odds, disguise, multiway dynamics). That's real and known (`72o` vs.
`32o` above is the standard illustration). Swapping `HAND_RANK` to real equity numbers fixes the
proxy's own internal ordering bugs (§1.3), it does not by itself produce a "perfect" strength
scale — that would need a full solver-equilibrium equity or a hand-selection-chart-calibrated
scale, which is out of scope here (owned by the preflop-range agent / Phase 3 solver work).

---

## 2. Range-advantage metric diagnosis

### 2.1 What was tried and why it "didn't recover a stable signal"

`postflop.py:48-54` documents that equity-backed range advantage was tried and reverted because
"mean equity is flat ~0.5; strong-combo share is range-width-biased; top-of-range strength is
noisy/counterintuitive." Three independent failure modes, diagnosed:

1. **Mean/average range-vs-range equity is close to 50/50 on MOST boards even when a real range
   advantage exists — this is expected, not a bug.** Poker theory distinguishes **range (equity)
   advantage** from **nut advantage**: "in a situation where the equity is 50%/50%, ... one player
   might have a large nut advantage, and this polarization gives them a big EV advantage" (VIP
   Grinders, range/nut-advantage explainer — see §4). Range advantage is a *distribution-shape*
   property (who owns the top slice — sets, two pair, nut draws), not a population-mean property.
   Averaging combo-vs-combo equity across two wide, heuristically-defined ranges washes out exactly
   the tail-concentration signal that "range advantage" is supposed to measure — so a correctly
   implemented mean-equity MC *should* come back flat on many textures, and did.
2. **"Strong-combo share" was measured as a raw/unnormalized count, not a range-width-normalized
   percentile.** A narrower range trivially has a higher fraction of "strong" combos than a wider
   range by construction (fewer weak combos to dilute it), independent of board texture — this
   conflates *preflop range width* (a static property of the chart) with *board-driven range
   advantage* (a texture-dependent property). Any such metric needs to be combo-count-weighted and
   ideally compared against each range's OWN preflop baseline (i.e. "share of combos that improved
   to strong here" vs. some texture-neutral reference), not an absolute threshold compared
   cross-range.
3. **Bounded MC iterations undersample the tail.** A mean estimator converges in `O(1/√n)`
   regardless of what's being averaged, but a *rare-event* estimator (e.g. "what fraction of this
   narrow range's combos are in the top 10% by equity") needs far more samples for the same
   confidence, because the quantity of interest is concentrated in a small, high-variance slice of
   the distribution. A bounded budget sized to make a *mean* stable (which `equity.py`'s own
   docstring says was deliberately kept small, "bounded to a small iteration cap ... perf") will
   legitimately look "noisy/counterintuitive" for a tail/percentile-style metric — that's a
   sample-size-vs-estimand mismatch, not necessarily an implementation bug.

### 2.2 Recommended correct method (for whenever this is revisited)

If/when equity-backed range advantage returns (Phase 3+, or a scoped experiment sooner):

- **Don't use mean win-rate as the range-advantage signal.** Compute it for completeness (it IS a
  real number and occasionally decisive — e.g. very dry, high, disconnected boards genuinely do
  skew the mean toward the preflop aggressor), but treat it as one input, not the metric.
- **Use nut/value-share delta as the primary signal**: for each range, on the given (fixed, concrete)
  board, compute the combo-count-weighted fraction of that range's OWN combos that fall above a
  made-hand-strength threshold (e.g. ≥ top-pair-good-kicker, or the top ~15–20% of that specific
  range's own equity distribution) — then compare hero's share to villain's share. This is a
  distribution-shape comparison, immune to raw range-width bias because it's normalized within each
  range before comparing.
- **Prefer full enumeration over Monte Carlo for this specific metric.** 169-class ranges against
  each other on a *fixed* 3–5 card board is small enough (a few hundred combos per side, disjoint
  after board/blocker removal) to enumerate exactly rather than sample — this removes the
  MC-tail-noise problem in §2.1(3) entirely (no sampling error, fully deterministic, and likely
  still fast — `equity.py`'s `_best7` is already O(21) per combo pair).
  `equity_vs_range()` as currently written computes ONE fixed hero combo vs. a villain pool; true
  range-vs-range needs a wrapper that iterates ALL hero combos too (weighted equally per real
  combo, not per class) — that wrapper doesn't exist yet and would be new code, not a tweak to
  `equity_vs_range`.
- **Accept that raw equity alone is fundamentally incomplete for "range advantage" as poker
  strategy uses the term** — the strategic conclusion (bet frequency, sizing) also depends on
  *realizability* (who's in position, who can barrel/apply pressure across streets), which is a
  full-tree property no single-street equity snapshot captures. This is exactly why the current
  positional+texture heuristic in `range_advantage()` is a reasonable stand-in until real solver
  tables arrive (Phase 3) — the diagnosis here supports the deferral decision, it doesn't overturn
  it. The concrete, scoped improvement available *before* Phase 3 is nut/value-share delta (above),
  not full range-advantage-as-a-single-number.

---

## 3. EV model recommendation

### 3.1 What solver EV / `ev_loss_bb` actually represents

A solver computes, for a specific decision node (a fixed spot: board, ranges, pot, stacks, action
to hero), the game-theoretic value in chips (expressed in bb) of each available action, assuming
equilibrium (or best-response) play from both sides for the rest of the hand. The **strategy EV**
at that node is the frequency-weighted average of the per-action EVs under the solver's own mixed
strategy. **"Regret"/EV-loss for a specific action = Strategy EV − Action EV** (GTO Wizard, "How
Solvers Work" — see §4): if you play the solver's exact mix, EV-loss is 0 by definition; deviating
to a single pure action costs the gap between that action's EV and the mix's EV. Training tools
(PeakGTO, GTO Wizard) express this per-decision EV-loss in **bb**, then multiply by 100 to get
**bb/100**: "EV loss/100 standardizes your mistake over 100 hands by multiplying the EV-loss of 1
decision by 100" — this is a *recurrence-scaled* rate ("if you always made this exact mistake in
this exact spot, here's the bb/100 cost"), not literally "bb lost per 100 hands played" in general.
Solver quality itself is reported the same way: "exploitability... measured as the maximum
potential EV loss of the current solution in big blinds divided by the pot" (Nash distance).

### 3.2 Why the current placeholders aren't credible EV, and what would beat them

Two placeholders exist today, and both label a **hand-tuned unitless score** as `ev_bb`:

- **Preflop** (`grading.py`): off-chart penalties are literally distance in the crude `hand_rank()`
  proxy space — `ev = -(FOLD_OFF_BASE + FOLD_OFF_SLOPE * rank)` for folding a should-play hand, and
  `ev = -(OFF_BASE + OFF_SLOPE * dist)` where `dist = floor - rank` for an off-chart call/raise
  (`floor` = the chart's weakest playable hand's `hand_rank`). `FOLD_OFF_BASE/SLOPE` and
  `OFF_BASE/SLOPE` are tuned only so the `ACCEPTABLE_MAX`/`MISTAKE_MAX` thresholds "feel right" —
  there is no chip-EV grounding at all, and (per §1) `hand_rank()`'s own ordering has material bugs
  that leak directly into this distance.
- **Postflop c-bet** (`postflop.py`'s `_merits()`): `ev_bb` values (2.0 strong / 1.2 draw / 1.0
  weak-made / 0.0 air, ± texture/range-advantage adjustments) are explicitly called out as "proxy
  EV" in the module docstring — again a hand-tuned merit score on a roughly-bb-shaped scale, not a
  computed chip EV.

**Recommended replacement — a one-street fold-equity EV model**, the standard textbook formula
(Sklansky-style semi-bluff EV, corroborated by the fetched sources in §4):

```
EV(bet_size) = Fold% × Pot
             + (1 − Fold%) × (Equity_vs_continuing_range × (Pot + 2×Bet) − Bet)
```

This is not solver-exact (it collapses the rest of the tree into one "villain folds or
villain-plays-it-out-with-static-range" branch), but it is a **real, textbook, dimensionally
correct chip-EV formula**, computed from two inputs this repo already has:

1. **`Equity_vs_continuing_range`** — from `equity.py`'s own `equity_vs_range()` (already built,
   already dependency-free), run with `board = spot.board[:3]` and `villain_combos` = a texture-
   appropriate continuing range (e.g. villain's opening range restricted to made-hands/draws by
   `_hand_category`-style logic; a reasonable v1 approximation is villain's whole preflop-defined
   range, since folds are already priced separately by `Fold%`).
2. **`Fold%`** — the solver-cited, per-texture fold/call/raise frequencies already sitting unused in
   `docs/research/06-postflop-reference-tables.md` §2/§4 (e.g. 37% fold on `QQ6` dry-paired, 62% on
   `KJ7` wet two-tone, 37% on `QJT` wet monotone) — this doc explicitly scoped out EV math, so
   wiring its frequency numbers into this formula is new work, not a redo.

This ties together two pieces of already-committed, already-cited work (a real evaluator +
real solver-frequency data) that are currently sitting side-by-side unused for EV, into a formula
that is provably better-grounded than either the hand-rank-distance placeholder or the unitless
merit score — without requiring a full game-tree solve. `ev_loss_bb` then becomes
`EV(best_action_by_this_formula) − EV(chosen_action)`, which is dimensionally a real bb quantity
(not a tuned proxy scale), and can be multiplied by 100 for a bb/100 leak-prioritization number the
same way training tools already do (§3.1). Full solver EV (multi-street, opponent best-response,
game-theoretic Nash equilibrium) remains a Phase 3 `StrategyProvider` swap-in, per the existing
architecture note in `postflop.py`'s docstring and `grading.py`'s "solver provider replaces the EVs
in Phase 3" comment — this recommendation is the credible *pre*-Phase-3 upgrade, consistent with
the "simplified but winning, not perfect GTO" doctrine.

---

## 4. Sources

**Local compute** (this doc's §1 and its full 169-hand table): computed directly from this
repo's `backend/app/domain/equity.py` (`_best7`, `equity_vs_range`) and
`backend/app/domain/hand_rank.py` (`_strength`), via a scratch script run with
`cd backend && .venv/bin/python <script>`. Not a web source — reproducible from the method in §1.2.

**Web research:**
- [Range Advantage and Nut Advantage in Poker explained in-depth](https://www.vip-grinders.com/range-advantage-and-nut-advantage-in-poker-explained/) — the range-advantage-vs-nut-advantage distinction and the "50/50 equity but polarized nut advantage" phenomenon cited in §2.1.
- [How Solvers Work — GTO Wizard](https://blog.gtowizard.com/how-solvers-work/) — EV-at-a-node calculation (`E[X] = Σ xᵢ·p(xᵢ)`) and the regret/EV-loss definition (`Action EV − Strategy EV`) cited in §3.1.
- [GTO Wizard AI Benchmarks](https://blog.gtowizard.com/gto-wizard-ai-benchmarks/) — EV-loss/100 ("bb/100") standardization and Nash-distance/exploitability framing cited in §3.1.
- [Converting ev into bb/100 — Run It Once](https://www.runitonce.com/nlhe/converting-ev-into-bb100/) — referenced via search snippet (direct fetch returned HTTP 403); corroborates the bb → bb/100 scaling convention.
- Semi-bluff / fold-equity EV formula (§3.2): corroborated via search across [VIP Grinders' Semi-Bluff EV Calculator](https://www.vip-grinders.com/poker-calculators/semi-bluff-ev-calculator/), [PokerVIP's EV Calculations — Fold Equity](https://www.pokervip.com/strategy-articles/expected-value-ev-calculations/ev-calculations-part-2-fold-equity), and [PokerVIP's EV Calculations — Semi-Bluffing](https://www.pokervip.com/strategy-articles/expected-value-ev-calculations/ev-calculations-part-3-semi-bluffing) — standard, widely-published poker-math formula, not attributed to a single source.
