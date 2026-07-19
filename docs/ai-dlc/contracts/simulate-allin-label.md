# Contracts — Simulate all-in labeling

## All-in source of truth
- `PlayerStatus.ALLIN` set in `backend/app/domain/table/engine.py:209-215` `_pay()` when `stack_bb <= _EPS`. Single source of truth.
- Surfaced to FE as `SeatView.status: "in"|"folded"|"allin"` (`frontend/src/api/types.ts:214`, backend `sim_session.py:641` `status=eng.status.value`).
- Already rendered: felt stack-line tag `.sim-allin` via `allin = revealed && seat.status === "allin"` (`SimTable.tsx:148/259-262`); CSS `app.css:2776` `var(--gold-bright)`.

## Event log path (the gap)
- `ActionEvent` frozen dataclass: `backend/app/domain/table/play.py:55` — fields seat/position/action/amount_bb/street. Built in playout loop `play.py:~234` AFTER `state = apply(state, decision)` — so `state.seats[seat].status` is post-action truth.
- `EventView` schema `backend/app/schemas/simulate.py:36-41` (mirror `types.ts:231-237`) — no status/all-in field.
- Assembled `sim_session.py:681-689` (`_view`), copies seat_index/position/action/amount_bb/street only.
- `SimEventLog.tsx:12-29` `verb()` renders the line. No all-in case today.
- Hero actions NOT in `events` (POST /act returns `events=[]` at `sim_session.py:742`; log narrates bot actions since hero's last decision). Hero all-in → chips puck only (hero pod ungated `SimTable.tsx:146`).

## Chips puck
- `SimTable.tsx:163-168` renders `fmtBb(seat.invested_street_bb)}bb`, gated `revealed && invested_street_bb>0 && !folded`. No all-in tag.

## Reveal timing (DO NOT TOUCH)
- `engine.py:218-235` `_close_street()`: `len(in_seats) <= 1` → auto-runout to river + `hand_over`. Domain-pure, frozen business rule. This is WHY hands go face-up early; the fix is labeling, not retiming.
- Lockstep FE gate: `SimulateView.tsx:297-301` `revealAt`; `SimTable.tsx:100-105` `isRevealed`; `SimEventLog` `stagedIndex` prefix. Any new tag must respect it.

## Migration / privacy
- `EventView`/`SeatView`/`ShowdownSeatView` are response-only Pydantic reconstructed from `HandState` (`state_json`) — adding a derived bool is NOT a persisted-column change → no Alembic migration. (Double-check `SimSeat`/`SimHand` ORM columns to confirm.)
- Villain hole cards only via `ShowdownSeatView` + R1 `RevealedSeatView` — do not add a third channel.

## Consumers / risk
- `SeatView`/`EventView` consumed in `SimTable.tsx`, `SimEventLog.tsx`, orchestrated by `SimulateView.tsx`.
- `grading.py`, `spot_signature()`, `App.tsx`, `tokens.css` — not implicated.
- Risk: FE-side seat join for all-in is fragile (current-status coincidence) → backend field chosen instead.
