# W3R-6 tickets — one-pair RAISE damp facing action + ace-high facing-raise float damp (#9, #5)

Spec: `docs/ai-dlc/specs/persona-realism-w3r-6.md`. Single owner/worker — both damps are facing-action-scoped edits to
the ONE `personas_postflop.py` facing branch, sharing one plumbing seam, one AF/band re-measure and one fixture
re-record. Both constants are **FIT SEEDS** — measured to a target, never dropped in. **#5 is the RE-ROUTED scoped
form; do NOT cut the global `_CALL_BASE[ACE_HIGH]`** (measured and refuted in W3R-3, §9 ledger). NO new lever/bucket,
no `_made_bucket` edit, grader + `spot_signature()` frozen.

Owned files: `backend/app/domain/table/postflop_context.py` (new `facing_raise` helper only),
`backend/app/domain/personas_postflop.py` (`:593–607` signature, `:731`, `:741–744`, the `:242–251` comment, two new
constants), `backend/app/domain/table/play.py` (`:130–160`, `:218–230`),
`backend/app/domain/table/range_estimate.py` (`:86–98`, `:167–178`, `:278–289`),
`backend/tests/test_personas_postflop.py`, `backend/tests/test_postflop_context.py`,
`backend/tests/test_range_estimate.py`, the re-recorded fixture data files.

## T1 — `facing_raise` plumbing (minimal seam)
Add a pure `facing_raise(action_history, street) -> bool` to `postflop_context.py` next to `bet_prev_street`
(`:88–105`): true iff **≥2** actions in `(BET, RAISE)` sit on the CURRENT street (postflop, the first aggressive
action is a BET, so ≥2 means the outstanding wager is a raise). Preflop raises never count — the `h.street is street`
filter excludes them. Add `facing_raise: bool = False` as a kwarg on `sample_postflop_decision` (`:593–607`), sibling
to `street`/`is_aggressor`. **HARD-STOP on design drift:** do NOT add this as a `PostflopContext` field — the
estimator must opt into this signal ALONE; building a `PostflopContext` there would apply the `in_position=False`
default to W3-b's `_position_agg_mult` (`:586–590`) and silently change the villain-range reveal. `play.bot_decision`
(`:218–230`) derives it and `_postflop_decision` (`:130–160`) forwards it.
- **Done-condition:** unit tests in `test_postflop_context.py` pin the rule (bet-only → False; bet+raise → True;
  preflop 3-bet then flop bet → False; re-raise → True). With `facing_raise` unread by any branch yet, the whole
  suite is BYTE-IDENTICAL (no consumer, no rng displacement) — prove it before T2/T3 land.
- **Owned:** `postflop_context.py` (new helper), `personas_postflop.py:593–607`, `play.py:130–160` + `:218–230`,
  `test_postflop_context.py`.

## T2 — #9 one-pair RAISE damp, flop/turn, facing action
At `personas_postflop.py:741–744`, multiply the **`_RAISE_BASE[bucket]` term ONLY** by a new
`_ONE_PAIR_RAISE_DAMP` when `bucket in _VULNERABLE_ONE_PAIR` (`:342`, already exactly MIDDLE_PAIR + TOP_PAIR) and
`street in (Street.FLOP, Street.TURN)`. Leaving `_DRAW_RAISE_BONUS[draw] * _draw_agg_street_mult(...)` outside the
multiplication IS the "spare semi-bluff raises" mechanic. Never floor to 0 (floors are the river-only device).
**`OVERPAIR_TPTK` stays UNDAMPED** — the bucket bundles true overpairs, and damping it repeats the §9 #7 error;
H107 (TPTK) is therefore only partially addressed here, the rest is W3R-7. FIT SEED: tune inside **`[0.25, 0.55]`**
(seed `0.35`, strictly > 0).
- **Done-condition:** exact-path (`_dist_for_pack`, `:999`, extended with `street=`/`facing_raise=`) tests show, for
  `tag` and `maniac`, MIDDLE_PAIR and TOP_PAIR (draw NONE) facing FOLD/CALL/RAISE: `P(RAISE)` at FLOP and TURN
  strictly below the `street=None` status quo (pin the measured drop); a one-pair-plus-STRONG-draw hand keeps a
  strictly higher `P(RAISE)` than the same bucket with no draw; a pure flopped draw is byte-identical; MONSTER /
  TWO_PAIR_PLUS / OVERPAIR_TPTK are byte-identical at FLOP and TURN.
- **HARD-STOP:** if no value in `[0.25, 0.55]` both passes those legs AND keeps every persona in band **and** keeps
  the fish arrival-range α ceiling (T4), STOP and report — a band re-anchor is an owner decision (§7).
- **Authorized narrowing (NOT a band move, use only on a measured α bust in T4):** narrow this gate from "facing
  chips" to "facing a **raise**" (reuse T1's flag). The α curve is a facing-a-BET curve, so this removes the
  interaction entirely and still covers H117/H32/H107. Prefer the wider gate; report which one shipped.
- **Owned:** `personas_postflop.py:741–744` + the new constant, `test_personas_postflop.py`.
- **Depends-on:** T1 (only for the narrowing fallback).

## T3 — #5 naked ace-high float damp, facing a RAISE, flop/turn
At `personas_postflop.py:731`, multiply the **`_CALL_BASE[ACE_HIGH]` term ONLY** by a new
`_ACE_HIGH_FLOAT_RAISE_DAMP` when `bucket is ACE_HIGH` and `draw is DrawCategory.NONE` and `facing_raise` and
`street in (Street.FLOP, Street.TURN)`. `_DRAW_CALL_BONUS[draw]` stays outside the damped term (naked only). **Do NOT
boost the FOLD merit** — the fold share rises through normalization (A1 guardrail: never an asserted fold floor). Do
NOT touch the ace-high `bluff_cell` polar raise (`:736–737`). Rewrite the `:242–251` comment from "re-routed to a
later slice" to the landed node-scoped mechanic, keeping the "the global cut stays refuted" warning. FIT SEED: tune
inside **`[0.35, 0.65]`** (seed `0.55`, i.e. effective in-node base `0.40 × 0.55 = 0.22` — the W3R-3 magnitude that
was directionally right and failed only on scope; strictly > 0).
- **Done-condition:** for `tag` AND `passive_fish`, ACE_HIGH + no draw, flop and turn, facing chips:
  `P(FOLD | facing_raise=True) − P(FOLD | facing_raise=False) ≥ 0.05` and `P(CALL)` strictly falls. Byte-identical for:
  the same spot with `facing_raise=False`, any ace-high WITH a draw, and the RIVER (already `call_merit = 0` via the
  bluff-cell river gate at `:732–733`).
- **HARD-STOP:** as T2, if no value in `[0.35, 0.65]` clears the `≥ 0.05` leg without busting a band or the α ceiling.
- **Owned:** `personas_postflop.py:731` + the new constant + the `:242–251` comment, `test_personas_postflop.py`.
- **Depends-on:** T1.

## T4 — Estimator parity + α ceiling + band re-measure + fixture re-record
1. **Estimator parity (REQUIRED — the live bot now diverges from the streetless policy):** add `facing_raise` to
   `_Ctx` (`range_estimate.py:86–98`), set it in the `_Ctx(...)` build (`:167–178`) from the SAME ≥2-postflop-
   aggressive-actions rule over the existing replay walk, and pass it at `_postflop_action_dist` (`:278–289`). Pass
   ONLY this flag — no `PostflopContext` (see T1's HARD-STOP). New parity test in `test_range_estimate.py`: for a
   replayed history where the target seat faces a postflop raise, the estimator's captured distribution equals
   `sample_postflop_decision(..., facing_raise=True)`, and the replay-derived flag equals
   `postflop_context.facing_raise(...)` on the equivalent `HandState` (the rule is implemented twice — this test is
   what pins them equal).
2. **α ceiling:** `test_fold_to_bet_respects_alpha_ceiling` (`test_personas_postflop.py:603`) passes UNCHANGED
   including the `passive_fish` arrival-range leg — **no tolerance change, no range re-scope**. Report the four
   measured values vs `α + 0.05` (current headroom is only 0.022 at ½-pot / 0.012 at 1.5×).
3. **Bands:** `test_persona_postflop_bands` (`:2429`) green against `BANDS` (`:2014`) with NO re-anchor. Watch AF
   FLOORS (raises are the AF numerator — maniac 2.4, lag 1.5, tag 1.4) and fold-to-c-bet TOPS (fish 0.549, maniac
   0.61).
4. **Fixtures:** re-record the seeded fixtures T2 moves (golden / `coverage_baseline.json` / limper belt), P1/P2a
   precedent; report the cumulative graded-coverage delta vs `coverage_baseline.persona-realism-start.json`.
   `test_bot_decision_parity_with_harness` (`test_sim_session.py:247`) stays green.
- **Done-condition:** `./scripts/verify.sh` green; `ruff check .` clean; `content/` JSON validates; domain-purity test
  green. Report both fitted constants + the stat each was fitted to, the shipped damp-1 gate, per-persona AF/ftc/WTSD
  with the in-band verdict, the fish α row, moved fixtures, coverage delta, and the explicit note that H107 (TPTK) is
  only partially fixed pending W3R-7. **HARD-STOP** as in T2/T3 if any band or the α ceiling busts.
- **Depends-on:** T1, T2, T3.

## Sequencing
T1 (plumbing, byte-identical — prove it) → {T2 one-pair raise damp, T3 ace-high float damp} co-measured (same file,
same normalization node, one fixture re-record) → T4 (parity + α + bands + re-record + verify). Single owner/worker;
serial, not parallel — both damps land in the same facing branch and their combined effect on the shared normalizer is
what gets calibrated (§7 stacked-multiplier joint calibration), so they must be fit together, not independently.

**Cross-slice note:** W3R-5 (#8, defense-side fold brake) edits the SAME facing branch and also owes estimator context
threading. If W3R-5 lands first, reuse its threading rather than adding a second seam; if this slice lands first,
W3R-5 inherits the `facing_raise` kwarg + parity test. Do not build them concurrently.
