# W3R-6 — One-pair RAISE damp facing action, pre-river (#9) + ace-high float damp (#5, re-routed)

**Slice of:** `docs/ai-dlc/roadmap/persona-realism.md` → W3R (bot-review remediation). Fixes **#9** (made one-pair
re-raises into heavy action, pre-river) and **ABSORBS #5** (naked ace-high float, re-routed out of W3R-3 by owner
decision 2026-07-24). From the 2026-07-24 hand-history review: TAG **H117** (99 on J-J-7 raising, and the same hand's
naked-ace-high float side), **H32** (88), **H107** (TPTK); maniac shows the same shape. Fixes review item **M7**.

> **ONE slice, two damps.** They ship together because they share the same mechanic — a **facing-action-scoped merit
> damp on the flop/turn** — and one fixture re-record / one AF+band re-measure. The ace-high half is the *scoped*
> version of the fix whose GLOBAL form was **measured and REFUTED in W3R-3**; the engine carries a "do NOT re-attempt"
> note at `personas_postflop.py:242–251` pointing here.

## Goal (one line)
Made one-pair (MIDDLE/TOP) stops raising into flop/turn action, and naked ace-high stops floating a **raise**, without
cutting any global base and without pushing any persona past its α fold-ceiling or out of a frozen band.

## Why (the gap / root cause)
1. **#9 — the raise floor is RIVER-ONLY.** `_RIVER_RAISE_FLOOR` (`personas_postflop.py:294–298`) zeroes the one-pair
   value raise **only** when `street is Street.RIVER` (`:745–746`). Pre-river the facing-branch raise merit is the bare
   `(_RAISE_BASE[bucket] + _DRAW_RAISE_BONUS[draw]·street_mult) · agg_scale` (`:741–744`), and `_RAISE_BASE`
   (`:274–282`) gives TOP_PAIR `0.10` / MIDDLE_PAIR `0.05`. With `agg_scale` up to the `_AGGRESSION_CAP` 5.6, a
   maniac's bare top pair carries ~0.56 raise merit — the same order as its CALL merit — so it re-raises bare one pair
   into a flop/turn bet-raise war (H117/H32/H107). Nothing in the engine reads "there is heavy action on this street"
   on the raise side pre-river.
2. **#5 — the ace-high float is a FACING-A-RAISE bug, not a base-constant bug.** `call_merit =
   (_CALL_BASE[bucket] + _DRAW_CALL_BONUS[draw]) · looseness` (`:731`) with `_CALL_BASE[ACE_HIGH] = 0.40` (`:271`) is
   street- and action-blind, so naked A-high floats a *raise* exactly as it floats a bare c-bet. W3R-3 tried the
   global cut `0.40 → ~0.22` and **HARD-STOPPED**: ace-high is ~35% of the passive fish's real arrival range and W3R-2
   parked the fish ON its α = f/(1+f) ceiling, so any meaningful global cut folds the fish PAST the exploitability
   ceiling. The scoped fix is safe **for a structural reason, not a lucky measurement**: the α-ceiling contract is
   measured over a **facing-a-BET** curve (`test_personas_postflop.py:580–599`, the W3R-0 arrival harness), so a damp
   gated on **facing a RAISE** is off that measurement node by construction.
3. **No facing-a-raise signal exists.** `sample_postflop_decision` derives facing state from the `legal` shapes only
   (`:623–624`, `ActionType.FOLD in by_kind` at `:690`) — that says "facing chips", it cannot say bet-vs-raise.
   `PostflopContext` (`table/postflop_context.py:41–47`) carries `in_position` / `bet_prev_street` / `busted_draw`
   only. **New plumbing is required for damp 2** (damp 1 needs none — "facing chips" + street suffices).

## Scope / files to touch
- `backend/app/domain/table/postflop_context.py` — NEW pure helper `facing_raise(action_history, street) -> bool`,
  sibling to `bet_prev_street` (`:88–105`), reusing the same `h.street is street` filter shape. **ONE definition of
  the rule:** postflop, the first aggressive action on a street is a BET, so
  `facing_raise ⇔ count(h.action in (BET, RAISE) and h.street is <current street>) >= 2`. Preflop raises never count
  (street filter). **Do NOT add a field to `PostflopContext`** — see the seam decision below.
- `backend/app/domain/personas_postflop.py` —
  - NEW kwarg `facing_raise: bool = False` on `sample_postflop_decision` (`:593–607`), a sibling of `street` /
    `is_aggressor`, **not** a `PostflopContext` field. **Seam decision (load-bearing):** the estimator must be able to
    opt into *this signal alone*. If it were a context field, `range_estimate` would have to build a
    `PostflopContext`, whose `in_position=False` default would newly activate W3-b's OOP damp
    (`_position_agg_mult`, `:586–590`) and silently change the villain-range reveal. A flat kwarg keeps the
    default-off byte-identity law exact.
  - NEW constant `_ONE_PAIR_RAISE_DAMP` (FIT SEED, see below) applied to **`_RAISE_BASE[bucket]` only** at `:741–744`
    when `bucket in _VULNERABLE_ONE_PAIR` (`:342` — already exactly `(MIDDLE_PAIR, TOP_PAIR)`) **and**
    `street in (Street.FLOP, Street.TURN)`. Multiplies the `_RAISE_BASE` term ONLY, so
    `_DRAW_RAISE_BONUS[draw]·_draw_agg_street_mult(...)` is untouched — **that is the "spare semi-bluff raises"
    mechanic**. Never floored to 0 (a floor is a river-only device; a damp is a direction, A1 guardrail).
  - NEW constant `_ACE_HIGH_FLOAT_RAISE_DAMP` (FIT SEED) applied to the `_CALL_BASE[ACE_HIGH]` term of `call_merit`
    (`:731`) when `bucket is ACE_HIGH` **and** `draw is DrawCategory.NONE` **and** `facing_raise` **and**
    `street in (Street.FLOP, Street.TURN)`. `_DRAW_CALL_BONUS[draw]` is not in the damped term (naked only).
    **The FOLD merit is never boosted** — the fold share rises through normalization (no asserted fold floor).
  - Replace the `:242–251` "re-routed to a later slice" note with the landed, node-scoped mechanic + why the global
    cut stays refuted.
- `backend/app/domain/table/play.py` — `bot_decision` (`:218–230`) derives `facing_raise(state.action_history,
  state.street)` and `_postflop_decision` (`:130–160`) forwards it.
- `backend/app/domain/table/range_estimate.py` — **estimator parity is REQUIRED** (see below): add `facing_raise` to
  `_Ctx` (`:86–98`), set it in the `_Ctx(...)` build (`:167–178`) from the same ≥2-postflop-aggressive-actions rule
  over the replay walk, and pass it at `_postflop_action_dist` (`:278–289`).
- `backend/tests/test_personas_postflop.py` — new exact-path tests (below); `_dist_for_pack` (`:999`) grows
  `street=` / `facing_raise=` kwargs; re-pin only assertions the fit legitimately moves.
- `backend/tests/test_range_estimate.py` — the parity test.
- Re-record the seeded fixtures damp 1 moves (golden / `coverage_baseline.json` / limper belt), P1/P2a precedent;
  report the cumulative graded-coverage delta vs `coverage_baseline.persona-realism-start.json`.
- **NO new lever, no new bucket, no `_made_bucket`/taxonomy edit, no global base cut, grader frozen.**

## FIT SEEDS (magnitudes are targets to MEASURE INTO, never drop-ins — §2 softmax law)
- **`_ONE_PAIR_RAISE_DAMP` — fit inside `[0.25, 0.55]`, seed `0.35`, strictly `> 0`.** Shape argument: the river
  already *kills* this line (floor 0.0), so pre-river it must be rare but alive — a protection/merge raise is a real
  line. At 0.35 a TAG's TOP_PAIR raise term falls `0.10·3.0 → 0.035·3.0` and a maniac's `0.56 → 0.196`, i.e. a ~3×
  cut in the pre-normalization raise share, which is where the softmax law says the observable movement lives (the
  raise is a *marginal*, non-saturated candidate here).
- **`_ACE_HIGH_FLOAT_RAISE_DAMP` — fit inside `[0.35, 0.65]`, seed `0.55`, strictly `> 0`.** Anchored deliberately so
  the effective in-node base `0.40 × 0.55 = 0.22` **equals the W3R-3 global target that was directionally right and
  only failed on scope** — the same magnitude, now off the α-measured node. Fitted range spans effective base
  `0.14–0.26`.
- **HARD-STOP (both):** if NO value inside the stated range simultaneously (a) passes the new spot tests and (b) keeps
  **every** persona's AF / fold-to-c-bet / WTSD band and the fish arrival-range α ceiling intact, **STOP and report**.
  A band re-anchor is an owner decision (§7; the only authorized mid-spine exception to date is W3R-2's fish+station
  WTSD).
- **Authorized narrowing (NOT a band move) if damp 1 busts the fish α ceiling:** narrow damp 1's gate from "facing
  chips" to "facing a **raise**" (reuse `facing_raise`). The arrival-range α curve is a facing-a-BET curve, so the
  narrowing removes the interaction entirely while still covering every cited hand (H117/H32/H107 are raise-war
  spots). Prefer the wider gate; narrow only on a measured bust; report which gate shipped.

## Pass/fail (HARD)
All spot legs use the exact-path capture-weights helper (`_dist_for_pack`, `test_personas_postflop.py:999`) — exact
normalized probabilities, **no sampling noise**, `test_size_elasticity_steeper_*` style.

1. **One-pair raise damped pre-river.** For `tag` and `maniac`, a made MIDDLE_PAIR and a made TOP_PAIR (draw NONE)
   facing FOLD/CALL/RAISE: normalized `P(RAISE)` at `street=Street.FLOP` and `street=Street.TURN` is **strictly below**
   the status-quo value (the `street=None` identity path, which is a clean A/B for a no-draw made hand — `flop`'s
   `_STREET_AGG_MULT` is 1.0 and `_draw_agg_street_mult` is a no-op at `DrawCategory.NONE`). Pin the measured drop.
   Cites H117 (99 on J-J-7) / H32 (88) / H107 (TPTK — see the OVERPAIR_TPTK carve-out below).
2. **Semi-bluff raises spared.** (a) A one-pair hand WITH a STRONG draw keeps a strictly larger `P(RAISE)` than the
   same bucket with `DrawCategory.NONE` at `Street.FLOP`; (b) a pure flopped draw (bucket AIR/ACE_HIGH, draw
   STRONG/WEAK) facing chips is **byte-identical** to status quo at every street.
3. **Two-pair+ value raises UNTOUCHED (regression guard).** MONSTER / TWO_PAIR_PLUS / **OVERPAIR_TPTK** facing chips at
   FLOP and TURN are **byte-identical** to status quo.
4. **Naked ace-high folds to a raise.** ACE_HIGH + `DrawCategory.NONE`, flop and turn, facing chips: for `tag` AND
   `passive_fish`, `P(FOLD | facing_raise=True) − P(FOLD | facing_raise=False) ≥ 0.05` and `P(CALL)` strictly falls.
   (H117's float side. Fit the constant to make this true.)
5. **Facing a BET is byte-identical** (the α-safety proof for damp 2). The same ace-high spot with
   `facing_raise=False`, and every ace-high spot with a draw, and every ace-high spot with `facing_raise=True` on the
   RIVER (already `call_merit = 0` via the bluff-cell river gate at `:732–733`), are byte-identical to status quo.
6. **Fish α fold-ceiling NOT busted.** `test_fold_to_bet_respects_alpha_ceiling`
   (`test_personas_postflop.py:603`) passes UNCHANGED, including the `passive_fish` arrival-range leg, with **no
   tolerance change and no range re-scope**. This holds because §9 landed the AUTHORIZED NARROWING: damp 1 fires only
   `facing_raise` (not merely "facing chips"), so it is structurally OFF the facing-a-BET node the arrival harness
   measures — the wider gate was tried first and measured a real bust (fish fold-to-bet 0.6528 vs the α + 0.05 ceiling
   0.650). The narrowed gate is now locked by
   `test_one_pair_raise_damp_does_not_fire_facing_a_bare_bet` (`test_personas_postflop.py`), a regression test that
   fails if the gate is ever re-widened to fire on a bare bet.
7. **Every persona IN its existing frozen band.** `test_persona_postflop_bands` (`:2429`) green against `BANDS`
   (`:2014`) with **no re-anchor**. Watch the AF FLOORS (raises are the AF numerator: maniac 2.4, lag 1.5, tag 1.4) and
   the fold-to-c-bet TOPS (raise merit shifting onto fold: fish 0.549, maniac 0.61). **HARD-STOP** if any busts.
8. **Estimator parity.** `range_estimate` produces the SAME action distribution as the live sampler for a replayed
   facing-a-raise postflop node; and the estimator's replay-derived flag equals
   `postflop_context.facing_raise(...)` on the equivalent `HandState`. Divergence without parity is a §11.9 FAIL.
9. **Live/harness parity holds.** `test_bot_decision_parity_with_harness` (`test_sim_session.py:247`) green.
10. `./scripts/verify.sh` green; `ruff check .` clean; `content/` JSON validates; domain purity test green.

## Out of scope
- **`OVERPAIR_TPTK` is deliberately NOT damped pre-river** even though H107 is TPTK: the bucket bundles true overpairs
  (AA-on-K) with TPTK, and damping it would damp real overpairs — the exact error §9 #7 forbids. The river floor can
  afford the coarseness (nobody value-raises the river with one pair); a pre-river damp cannot. **H107 is therefore
  only partially addressed here; the rest lands in W3R-7's bucket split.** Say so in the build report.
- No global `_CALL_BASE[ACE_HIGH]` cut (refuted, §9 ledger) · no `_RAISE_BASE` table value edit (the damp is a gated
  multiplier, the table stays) · no `_RIVER_RAISE_FLOOR` / `_RIVER_BET_FLOOR` change · no ace-high **bluff-raise**
  change (the `bluff_cell` polar raise at `:736–737` stays) · no fold-merit boost (that is W3R-5, #8) · no
  `_made_bucket` / taxonomy edit (W3R-4b, W3R-7) · no band re-anchor (in-band or STOP) · grader and
  `spot_signature()` frozen · the W3R-1 "band sampler is context-blind" gap stays open (deferred to W4-b).

## Invariants honored
Softmax law (both constants are FIT SEEDS measured to a target, ranges stated, never dropped in) · merits clamped ≥0,
normalized, `rng.choices` never argmax · action draw stays the FIRST `rng.choices` (both damps act on merits before
the draw) · default-off byte-identity (`facing_raise=False` and `street=None` reproduce today exactly) · domain purity
(`postflop_context.py` / `personas_postflop.py` stay web/DB-free) · estimator-parity law (§7, §11.9) satisfied by
threading `facing_raise` + a parity test · A1 guardrail (a damp/direction, never an asserted fold floor) · α
fold-ceiling law (structurally protected for damp 2, measured for damp 1) · frozen bands respected (in-band or
HARD-STOP; §7's only authorized exception remains W3R-2 fish+station WTSD) · anti-sizing-tell untouched ·
`spot_signature()` frozen · results freq+EV.

## Verify-by
`./scripts/verify.sh` green; the ten pass/fail legs above; `ruff check .` clean. Report: the two **fitted** constants
and the measured stat each was fitted to, which damp-1 gate shipped (facing-chips vs the narrowed facing-raise
fallback), per-persona re-measured AF / fold-to-c-bet / WTSD with the in-band verdict, the fish arrival-range α
numbers vs `α + 0.05`, which fixtures moved, and the cumulative graded-coverage delta vs the immutable snapshot.
