# Tickets — Simulate all-in labeling

Spec: `docs/ai-dlc/specs/simulate-allin-label.md`. Small, mostly sequential chain. Build top-to-bottom.

## T1 — Domain: thread `all_in` onto `ActionEvent`
- **Owns:** `backend/app/domain/table/play.py`
- Add `all_in: bool` field to the `ActionEvent` frozen dataclass (~line 54-55). In the bot-playout loop where `ActionEvent(...)` is constructed (~line 234, after `state = apply(state, decision)`), compute `all_in = state.seats[seat].status is PlayerStatus.ALLIN` and pass it.
- **Done:** `cd backend && python -m pytest tests/test_domain_purity.py -q` passes (domain stays import-pure); existing playout tests still green.
- **Deps:** none.

## T2 — Schema + service: surface `all_in` on `EventView`
- **Owns:** `backend/app/schemas/simulate.py`, `backend/app/services/sim_session.py`
- Add `all_in: bool = False` to `EventView` (schemas ~line 36). In `_view`'s `EventView(...)` construction (sim_session ~line 682) pass `all_in=e.all_in`.
- **Done:** `cd backend && ruff check .` clean; app boots (`./scripts/serve.sh start`).
- **Deps:** T1.

## T3 — Backend test: assert `all_in` truth
- **Owns:** a backend test file (new or extend an existing simulate/playout test — NOT the files owned by T1/T2).
- Assert `EventView.all_in` (or `ActionEvent.all_in`) is `True` for an action that exhausts a seat's stack (bet/raise/call-to-zero) and `False` for a normal action + fold/check. Use a crafted `HandState` / seeded playout.
- **Done:** `./scripts/verify.sh` → "BACKEND VERIFY OK".
- **Deps:** T1, T2.

## T4 — FE type: add `all_in` to `EventView`
- **Owns:** `frontend/src/api/types.ts`
- Add `all_in: boolean;` to the `EventView` interface (~line 231).
- **Done:** `cd frontend && npm run typecheck` green.
- **Deps:** T2 (wire contract).

## T5 — FE log: all-in verbs in `SimEventLog`
- **Owns:** `frontend/src/components/simulate/SimEventLog.tsx`
- `verb()` gains an `allIn` param. When true: `bet` → "shoves all-in Xbb"; `raise` → "raises all-in to Xbb"; `call` → "calls all-in Xbb" (skip the `≤1 → limps` branch); `post` → "posts all-in Xbb". Call site passes `e.all_in`.
- **Done:** `cd frontend && npm run typecheck && npm run build` green; a hand where a villain shoves reads "…all-in…" in the log.
- **Deps:** T4. Parallel-safe with T6 (disjoint file).

## T6 — FE felt: "ALL IN" tag on chips puck in `SimTable`
- **Owns:** `frontend/src/components/simulate/SimTable.tsx`
- Add an "ALL IN" tag to the chips-in-front puck (~lines 163-168) when the existing `allin` var (~line 148) is true. Reuse `.sim-allin` (re-grep: `app.css:2776`). Keep the existing stack-line tag. Must stay behind the same `revealed` lockstep gate.
- **Done:** `cd frontend && npm run typecheck && npm run build` green; felt bet puck shows "ALL IN" in lockstep, both themes AA (design-reviewer if any new CSS).
- **Deps:** T4. Parallel-safe with T5 (disjoint file).

## DAG
```
T1 → T2 → T3
        └→ T4 → { T5 ‖ T6 }
```
T5 and T6 are the only parallelizable pair (disjoint files). Everything else sequential. Hotspots touched: `frontend/src/api/types.ts` (T4, single owner), `backend/app/services/sim_session.py` (T2). No migration. No `App.tsx`/`tokens.css`/`grading.py` touch.
