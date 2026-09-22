# Contract map — P4, one live session across devices

Scanned 2026-09-22 by a read-only contract-mapper (Opus) against `main` at `5557bae`, for the
roadmap slice P4 (the phone and the Mac open the same Simulate table). Line numbers are as of that
commit. Companion evidence: the two-client probe in `../ledger/phone-and-6max.md`, "P1 measurement (c)".

## Bottom line

- Nothing in the data model can tell a fresh client from a stale one: `SimHand` and `SimSession`
  carry no version and no `updated_at`. The only monotonic per-hand quantity that already exists is
  the count of `SimDecision` rows, read as `len(prior)` at `sim_session.py:1017`.
- The existing turn guard (`sim_session.py:1008-1009`) is a half-guard: it rejects a stale action
  only when the hero is no longer to act. When the other device's action leaves the hero to act
  again (villain raise back to hero, or a fresh hand) the stale decision is legal at the new spot,
  applies silently, and is graded against the wrong spot.
- A version token needs no migration: `(hand_no, decision count)` is derived from existing columns
  and `SessionView` is a response schema, not a table. It must NOT go into the request body's
  `Decision` model, which is domain core shared with Practice grading. A query parameter on the
  action route avoids both the domain leak and a wire-shape change.
- The interleave window is real (`await` at `sim_session.py:1023` between read `:1004-1007` and
  write `:1067`, one DB session per request). The compare-and-set pattern this file already uses for
  the blind check (`UPDATE ... WHERE ... IS NOT DISTINCT FROM <observed>` plus `rowcount`,
  `sim_session.py:1644-1673`) is the golden path for closing it.
- "Newest not-ended session" will resurrect abandoned tables: `status = "ended"` is set only by
  `leave_session` (`:1676-1682`); creating a session never ends the old one (`:952-983`).
- The client cannot read an error body, so the rejection rides on the status code alone. 409 is
  already this router's conflict vocabulary (`api/v1/simulate.py:128-129`); 400 is the bucket for
  every illegal action and must not be reused.
- Session identity is localStorage-only inside `SimulateView.tsx`; `App.tsx` mounts it propless and
  needs no change.

## 1. How the client finds and remembers its session

localStorage key `simulate.session_id` (`SimulateView.tsx:59`), written on sit-down (`:456-464`),
read on mount (`:619-625`), cleared on leave / 404 (`:534-541`); the live id is a ref (`:191`). The
hash route carries only view + drill mode (`frontend/src/lib/hashRoute.ts:38-52`); `App.tsx:474-475`
renders `<SimulateView />` with no props. On reload the client GETs `/session/{id}`; a 404 clears the
key and shows the sit-down screen (`isSessionNotFound`, `:117-119`). A non-404 failure on boot renders
the generic error panel and suppresses BOTH the table and the sit-down screen (`:644-646`,
`:1510-1523`), so a 500 from any new boot-time route strands the player.

## 2. The hero-action path

`POST /session/{id}/action` (`api/v1/simulate.py:93-104`) → `apply_hero_action` in `sim_session.py`:
state read `:1004-1007`, half-guard `:1008-1009`, prior decisions `:1017`, `await` grading `:1023`,
decision row + state write `:1067`, single commit `:1076`. One uvicorn process, no `--workers`
(`scripts/serve.sh:136`), one SQLModel session per request (`backend/app/db/session.py:18-20`). The
awaited provider chain does no I/O today, so the path serializes on one worker by accident, not by
design (see the probe). `SessionNotFound` → 404, `ValueError` → 400.

## 3. Request and response shapes

Action body = `app.domain.action.Decision` (`backend/app/domain/action.py:10-20`): `action`,
`size_bb?`, `size_fraction?`. Shared with Practice via `backend/app/schemas/drill.py:11,22`; do not
extend it. `SessionView` (`backend/app/schemas/simulate.py:258-263`) is where a token field belongs;
its FE twin is hand-maintained in `frontend/src/api/types.ts`. A real `version` column on `SimHand`
would force an Alembic file in the single-owner `backend/alembic/versions/` (currently `0016`).

## 4. Resumable states

`restore_session` (`sim_session.py:986-995`) already handles: a live hand with hero to act
(`legal_actions` only when `is_hero_turn`, `:929`); hand over awaiting Next hand (recap rebuilt from
`SimDecision` rows at `:994`, which lack the live verdict prose — a documented degradation at
`SimulateView.tsx:975-984` that P4 turns into the normal phone path); a Challenge session parked at
the hand-200 blind check (deal barred `:1543-1573`, block synthesised `:892-907`); an active session
whose current hand row is missing → `None` → 404 (`:990-992`). Mid-hand-with-villain-to-act is never
persisted: `advance_to_hero` runs to a hero boundary or hand end (`:295`, `:1066`).
`_blind_check_seats` must stay a pure function of the session id (`:360-385`); the blind check already
has first-write-wins plus the "Answered in another window" rendering (`SimulateView.tsx:919`,
`:1284-1291`).

## 5. Other consumers of session identity

Villain range, reveal, both charts, coach explain and blind check take the id explicitly from
`view.session_id` (`api/v1/simulate.py:200-278`; `SimulateView.tsx:1045`, `:1115`, `:1436-1456`).
Replay-by-key checks owner but not status (`sim_session.py:1768-1782`). History, per-hand
replay/reveal, street and leak reports are session-independent (`api/v1/simulate.py:139-197`).
`session_id` appears in the frontend only in `SimulateView.tsx`, `SimRangeChart.tsx` and one test.
A server-chosen current session breaks none of them.

## 6. Error contract

`json<T>` drops the body (`frontend/src/api/client.ts:35-38`); `errorStatus` regexes the status out
of the message (`SimulateView.tsx:109-112`). The stale-tab notice needs a sibling branch beside
`isSessionNotFound` in `run`'s catch (`:672-681`); the generic panel copy at `:1255-1259` ("Is the
backend running on :8008?") is wrong for it. Client trap: the Watch-off fold path fires two writes in
one handler — action then immediate deal (`:702-718`); a rejection of the first must stop the second.

## 7. Test surfaces

Backend: `backend/tests/test_simulate_api.py:21-36` (temp engine + `dependency_overrides` +
`TestClient`) for status codes; `backend/tests/test_sim_session.py:80-90` (`_play_current_hand`) for
real play; `backend/tests/test_two_mode_simulate_gate.py:56-70` (`_renumber`) for building session
state without playing. Frontend: no component testing library is installed (`package.json:18-31`);
every Simulate test is a pure-module test (`handCount.test.ts`, `blindCheck.test.ts`). New decidable
client logic goes in a small pure module beside those.

## Where new server logic can live

`sim_session.py` is 1753 lines. The router (`api/v1/simulate.py`, 279 lines) is the stated HTTP
translation layer and is where `GET /session/current` belongs; its resolution goes in a small new
service module. That module needs `_get_session` (`:400`) and `_current_hand` (`:315`), both private;
promoting those two names is a mechanical edit inside the hot file and beats duplicating the
`status == "active"` / `hand_no == session.hand_no` predicates. The version check itself cannot leave
`apply_hero_action`: it is the only place holding both the observed and the new state.

## Risks the plan must handle

- Stale-but-legal actions (the half-guard) — the token check must run before the legality check.
- The interleave window — close it with compare-and-set at write time, not only a check at read time.
- Newest-active resurrecting an abandoned or unrestorable session — a 404 from the current route must
  land the client on the sit-down screen, never the generic error panel.
- Fold-then-deal double write on the client.
- `created_at` is unindexed, naive from SQLite, and not unique — order by `created_at desc, id desc`.
