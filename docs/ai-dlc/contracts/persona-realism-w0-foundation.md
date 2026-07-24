# Contracts Map — Persona-Realism W0 Foundation

> Read-only scan (contract-mapper, 2026-07-24) of the areas the W0 wave touches. Anchors are `file:line`.

## A. Pot / action reconstruction (W0-a)
- **Bot call site:** `backend/app/domain/table/play.py:175-215` (`bot_decision`). `pot_bb = sum(s.invested_total_bb
  for s in state.seats)` (`play.py:198`, pot AFTER all action). `is_aggressor` via `last_aggressor_position(...)`
  (`play.py:202`). Threads `current_bet_to`, `is_aggressor`, `street` into `sample_postflop_decision`.
- **`HistoryAction`** (`backend/app/domain/spot.py:113-117`): `{street: Street, position: Position, action: ActionType,
  amount_bb: float}`. **CORRECTION (verified `engine.py:288, 304`):** `amount_bb` is the per-action **INCREMENT** for
  ALL types — BET/RAISE store `min(size − invested_street, stack)` (NOT the bet-TO, as first scanned), CALL the call
  increment, POST the blind, CHECK/FOLD 0.0. So `sum(amount_bb) == total pot` and the latest aggressor's increment is
  read directly off the last BET/RAISE — **no chip-replay needed** (simpler than area-A first implied).
- **`HandState.action_history`** at `engine.py:62`; `current_bet_bb` (`engine.py:59`) = highest street investment.
- **Only existing pre-aggression logic** = inline `faced_frac = to_call_bb / max(pot_bb - max(current_bet_to,
  to_call_bb), 0.01)` at `personas_postflop.py:492`, with the documented self-re-raise over-subtraction bug (comment
  `personas_postflop.py:484-490`). No `pot_before_*` / increment helper exists.
- **Only action_history helper today:** `sizing.py:70-78 last_aggressor_position()` → returns a `Position`, no amount.
- **Reference walk:** `range_estimate._replay_contexts` / `.pay()` (`range_estimate.py:107-204`, `123-136`) is the
  correct per-`ActionType`, street-reset chip-walk pattern to model.
- **Risk:** helper must handle multi-street histories (reset on street change); naive `sum(amount_bb)` mis-reads by
  action type. Pure add in W0-a ⇒ byte-identical (no consumers).

## B. Realism/population harness (W0-b)
- **Entirely in `backend/tests/test_personas_postflop.py`** (~1140-1660). No separate harness module.
- `_play_hand` (`:1228-1294`) → `(state, settlement, log, saw_flop, had_limper, had_3bet_plus)`. `log` = **postflop-only**
  `(seat, street, action)` 3-tuples (`:1284`); **preflop not logged**. `saw_flop: set[int]`; `settlement.showdown_seats`.
- `_persona_stats` (`:1527-1593`), memoized `_STATS_CACHE` (`:1524`). AF = bet_raise/call over postflop `log`;
  fold-to-**first**-cbet (`:1574-1586`); WTSD = showdown/saw_flop (`:1590`). **≥30-occurrence floor → None** (`:1588-1590`).
- **Fixture:** on-the-fly `deal_hand(random.Random(hand_seed))`; stat RNG seeded literal **20260710** (`:1540`);
  `budget` fixture (`:1327-1334`) derives per-persona N from a 12s wall-clock budget (floor 150). No externalized fixture file.
- **Bands:** `BANDS` dict (`:1482-1521`, persona→(af,ftc,wtsd)); `test_persona_postflop_bands` (`:1596-1612`);
  `test_persona_wtsd_ordering_invariants` (`:1615-1653`, the relative-ordering pattern to reuse).
- **Reusable:** `size_bucket()` (`personas_postflop.py:62`) for metric #4; `settlement.deltas` (`engine.py:66-69`) for W$SD.
- **Risk:** `log` 3-tuple is unpacked **positionally in ≥3 places** (`:1563, 1575, 1581-1585`) → growing it silently
  breaks or corrupts AF. Fix: convert to a named tuple, update all consumers in lockstep. `_STATS_CACHE` has no schema
  versioning. VPIP/PFR/gap (#3) has **no existing logging hook** (new preflop path). #5/#6 read ~flat until W3 (correct pre-state).

## C. `range_estimate` parity (W0-a future / W0-c)
- `_Ctx` NamedTuple (`range_estimate.py:86-98`) — `{street, board, position, facing, kinds, pot_bb, stack_bb,
  opponents, current_bet_to, observed}`. **No `is_aggressor` / no increment field.** Rebuilt by `_replay_contexts`
  from `PublicActionHistory` (card-free/no-peek).
- Call site `_postflop_action_dist` (`:273-293`): `is_aggressor` **not threaded** (takes default `False`) — harmless
  today because it only affects sizing (post-action-draw), but fragile if a future slice makes it action-affecting.
- **`_CaptureRng`** (`:253-270`): `choices()` records `(population, weights)` on the FIRST call, returns `population[0]`
  — the mechanism enforcing "action draw is the FIRST `rng.choices`". **Its captured `weights` ARE the action merits**
  → W0-c's exact-merit source with no domain change.
- **Parity this wave:** W0-b test-only (none); W0-a unconsumed (none); W0-c uses capture-rng, not `range_estimate`
  (none). The parity work lands with **W1-b** (when the denominator is consumed): `_Ctx` has no increment field, so
  W1-b must extend `_Ctx` + `_replay_contexts` and add a parity test (positional `_Ctx` unpack in
  `test_range_estimate.py:250` breaks on a field add — update in lockstep).
- **River parity test precedent:** `test_range_estimate.py:405-458`.

## Top risks carried into the specs
1. `_Ctx` positional NamedTuple → field add is a fan-out shape change (deferred to W1-b).
2. W0-a helper needs raw `action_history` (self-re-raise increment not recoverable from scalars) → parity plumbing is
   W1-b's, not W0-a's.
3. `log` 3-tuple positional unpack in ≥3 places → convert to named tuple in W0-b.
4. VPIP/PFR/gap = new preflop logging path.
5. #5/#6 metrics read ~flat pre-W3 (correct, document it).
6. No new randomness before the action draw (`personas_postflop.py` action `rng.choices`) — protects `_CaptureRng`.
