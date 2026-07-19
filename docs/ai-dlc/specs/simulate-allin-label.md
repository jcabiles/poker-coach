# Delta spec — Simulate all-in labeling

**Slice of:** `docs/ai-dlc/roadmap/simulate-table.md` (Epic 3 — Simulate table). Inherits its no-gos (no solver tables, heuristic-only; EVs approximate) and invariants.

## Goal
Make an all-in legible in Simulate playback so a bet that shoves a player in reads as "all-in" — not as an ordinary big BB bet — at the exact moment it happens, so the auto-runout that reveals hands before the river is no longer a surprise.

**Problem being fixed:** when a player (hero or villain) goes all-in, the UI shows only the total-BB amount with no all-in marker. Because the engine auto-runs the board to the river once ≤1 seat is still `IN`, hands go face-up early and the user doesn't realize why.

## Direction (locked)
Label the *action*. Two surfaces:
1. **Event log** narrates the shove ("shoves all-in / calls all-in / raises all-in to Xbb").
2. **Felt chips-in-front puck** gets an "ALL IN" tag on the visible bet amount.

Not doing: a separate reveal-moment banner; changing when hands go face-up.

## Files / interfaces to touch
Backend (pure domain + schema + assembly — no migration):
- `backend/app/domain/table/play.py` — add `all_in: bool` field to the `ActionEvent` frozen dataclass (~line 55). In the bot-playout loop where `ActionEvent(...)` is built (~line 234, immediately after `state = apply(state, decision)`), compute `all_in = state.seats[seat].status is PlayerStatus.ALLIN` and pass it. Domain-internal, no web/DB import — purity preserved.
- `backend/app/schemas/simulate.py` — add `all_in: bool = False` to `EventView` (~line 36). Default keeps the field additive/back-compatible; response-only Pydantic shape, **no persisted column → no Alembic migration**.
- `backend/app/services/sim_session.py` — in the `_view` `EventView(...)` construction (~line 682), pass `all_in=e.all_in`.

Frontend (types + two components; no token/App.tsx changes):
- `frontend/src/api/types.ts` — add `all_in: boolean;` to `EventView` (~line 231). Hand-maintained per invariant.
- `frontend/src/components/simulate/SimEventLog.tsx` — `verb()` gains an all-in branch. Signature becomes `verb(action, amount, allIn)`. When `allIn`:
  - `bet` → `` `shoves all-in ${amount}bb` ``
  - `raise` → `` `raises all-in to ${amount}bb` ``
  - `call` → `` `calls all-in ${amount}bb` `` (bypass the `amount <= 1 → "limps"` branch)
  - `post` → `` `posts all-in ${amount}bb` `` (a short stack whose blind exhausts it — keeps the log consistent with the felt tag, which is status-driven; see refuter note below)
  - `fold`/`check` → unchanged (cannot be all-in).
  Call site passes `e.all_in`.
- `frontend/src/components/simulate/SimTable.tsx` — the chips puck (~lines 163-168) gains an "ALL IN" tag when `allin` (the existing `revealed && seat.status === "allin"` var at ~line 148) is true. Reuse `.sim-allin` (re-grep its line — currently `app.css:2776`, not 2766). Existing stack-line tag (~line 261) stays.

## Refuter findings folded (verdict: PASS, no blockers)
- **Cross-surface consistency (was: descoped):** the felt "ALL IN" tag is driven by `seat.status === "allin"` regardless of which action caused it (`SimTable.tsx:148`), so a blind-post that exhausts a stack already shows "ALL IN" on the felt. To avoid the felt saying ALL IN while the log says only "posts Xbb", the `post` verb now also gets all-in wording (above). Rare but keeps the two surfaces in agreement.
- **Line-number drift:** implementer must re-grep before editing — `.sim-allin` is at `app.css:2776`; other cited lines are `~` approximate and verified close.
- **No migration confirmed stronger than stated:** `ActionEvent` is constructed once (`play.py:234`), consumed transiently per-request, never stored in `state_json` or any ORM column — so there is no legacy event shape to be back-compat with. Additive field is safe.

## Out of scope
- No change to reveal *timing* / the `_close_street` early-runout business rule (`backend/app/domain/table/engine.py`) — frozen.
- No banner / no new playback beat.
- No all-in indicator on `ShowdownSeatView` / showdown settlement rows.
- No R1 on-demand-reveal (hero-fold) path changes.
- No new wire channel for hole cards; privacy gates untouched.
- No `ShowdownSeatView` change (settlement rows carry no all-in indicator).

## Constraints (from profile invariants)
- `backend/app/domain/table/` stays pure — no web/DB imports; `all_in` computed from `PlayerStatus` only.
- Results stay frequency + EV — not touched (this is table-state rendering, not grading).
- `spot_signature()` frozen — not touched.
- CSS from design tokens only — reuse existing `.sim-allin` (already `var(--gold-bright)`); no raw hex/px.
- WCAG AA contrast + visible focus, both themes — the "ALL IN" tag must meet 3:1/4.5:1 in Day + Night (verify via design-reviewer if styling added).
- Lockstep reveal gate is load-bearing — the chips-puck tag must sit behind the same `revealed`/`stagedIndex` gate so it never jumps ahead of the narrated log.
- FE types hand-maintained in `types.ts`.

## Verify-by (end-to-end)
1. Backend: `./scripts/verify.sh` → "BACKEND VERIFY OK" (pytest + boot probe). Add/extend a backend test asserting `EventView.all_in` is `True` for an action that exhausts a seat's stack and `False` otherwise (crafted `HandState` / playout).
2. Lint: `cd backend && ruff check .` clean.
3. FE: `cd frontend && npm run typecheck && npm run build` green.
4. Manual (`./scripts/serve.sh start`): play Simulate hands until a villain shoves; the event log reads "shoves all-in Xbb" and the felt chips puck shows "ALL IN", both appearing in lockstep with the narrated action; when the board then runs out and hands turn face-up, the all-in is already visible as the cause.
