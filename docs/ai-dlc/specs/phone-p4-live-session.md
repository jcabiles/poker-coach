# Spec — P4, one live session across devices

status: **rev 1, APPROVED** — pre-authorized by the owner's `/ai-org:spec --auto-build` invocation,
2026-09-22, after a frontloaded interview (rulings recorded in the roadmap's P4 entry and below).
slice of: `../roadmap/phone-and-6max.md`, slice P4 (the phone and the Mac open the same table).
contract map: `../contracts/phone-p4-live-session.md` · probe evidence: `../ledger/phone-and-6max.md`,
"P1 measurement (c)" · tickets: `../tickets/phone-p4-live-session.md`.

## Bottom line

The phone and the Mac will open the same Simulate table, and a stale tab can no longer corrupt a
hand. Two changes do it: the server answers "what is the current session" (the newest one that has
not ended), and every hero action and every deal carries a token naming the state the client saw.
A token that no longer matches is refused with HTTP 409, the client refetches, and one line says
"Acted elsewhere — table refreshed." No migration, no accounts, no websockets.

The probe proved the danger is real today: a stale "call" was applied to the **next hand** and
graded as that hand's decision, and a stale "call 1.0bb" charged the hero **4.5bb**, both with
HTTP 200. Two simultaneous submits both succeeded and graded one decision twice.

## Goal (one line)

On page load the client asks the server for the current session instead of browser storage, and a
hero action or deal against a state the client did not see is refused with 409 and refreshed.

## What changes

### Backend

1. **`SessionView.state_token: str`** (`backend/app/schemas/simulate.py`). Derived, never stored:
   `f"{hand.hand_no}.{len(state.action_history)}"`, built in the one place that assembles a
   `SessionView` from a hand state. It changes whenever any seat acts (villain raise, hero action)
   and whenever a new hand is dealt, which covers every corrupting case in the probe. If
   `action_history` turns out not to grow on villain actions, use the count of all actions recorded
   in the hand state; the ticket's test decides, not the worker's assumption.
2. **`state_token` query parameter** on `POST /session/{id}/action` and `POST /session/{id}/hand`
   (`backend/app/api/v1/simulate.py`). Required. It is a query parameter, not a body field, because
   the action body is `app.domain.action.Decision`, domain core shared with Practice grading.
3. **Staleness check** in `apply_hero_action` and `deal_next_hand` (`sim_session.py`), BEFORE the
   turn guard and the legality check: token mismatch raises a new `StaleState` exception (its own
   class, not a `ValueError`, so the router can map it to 409 while illegal actions stay 400).
4. **Compare-and-set at write time** in `apply_hero_action`: the hand-state write becomes an
   `UPDATE sim_hand SET ... WHERE id = :id AND state_json = :observed` and a `rowcount` of 0 raises
   `StaleState` after rolling back the transaction, so the decision and attempt rows written in the
   same transaction are discarded. Golden path: the blind check's compare-and-set at
   `sim_session.py:1644-1673`. This closes the `await` window at `:1023` regardless of whether the
   grading provider ever starts doing I/O.
5. **`GET /session/current`** → the newest session with `status == "active"` for the owner, ordered
   by `created_at desc, id desc`, rendered through the existing `restore_session`. 404 when there is
   no active session or the newest one cannot be restored. Declared BEFORE `/session/{session_id}`
   in the router so the literal path wins. Resolution lives in a new small module
   `backend/app/services/sim_current.py`; the router stays the HTTP translation layer.
6. Router: `StaleState` → `HTTPException(409, "stale state")`.

### Frontend

7. **`frontend/src/api/types.ts`**: `SessionView.state_token: string`.
8. **Boot** (`SimulateView.tsx`): on mount, GET `/session/current`. 200 → adopt it and write the
   localStorage key as today. 404 → clear the key and show the sit-down screen (the same path as
   today's session-not-found). Any other failure → fall back to today's behaviour (GET
   `/session/{stored id}`), so a broken current-route never strands the player on the generic
   error panel.
9. **Actions and deals** send `?state_token=<view.state_token>` from the view currently rendered.
10. **409 branch** beside `isSessionNotFound` in `run`'s catch: refetch `/session/{id}`, adopt, and
    set a one-line notice "Acted elsewhere — table refreshed." rendered as `role="status"` above the
    action dock; it clears on the next successful action or deal. The Watch-off fold path (fold then
    deal in one handler) needs no extra code: the fold's 409 throws before the deal call, and the
    ticket's test proves the deal is not sent.
11. New pure module `frontend/src/components/simulate/staleState.ts` (+ `.test.ts`): `isStaleState`
    (409 detector, mirrors `isSessionNotFound`) and `withStateToken(path, token)`.
12. CSS for the notice in `app.css`, tokens only, both themes, AA contrast.

### Docs, same PR

13. Roadmap: tick P1 and S1 with build notes (#229, #230); mark P2 replaced by the P3a fix (#231);
    note P3b promoted to NOW by the owner on 2026-09-22; P4 entry gains the probe verdict and the
    rulings (newest active session; reject-and-refetch; no migration). Ledger: the P1(c) probe entry
    and the P4 review round. `log.md` and the profile's Resume block.

## Out of scope

Accounts, multi-user, websockets or push, any Alembic migration, ending older sessions when a new
one is created (two devices that each start a session keep two live sessions; the newest wins on
reload), replaying a dropped action, changes to `App.tsx`, and anything on Practice or Quiz.

## Constraints (from the profile)

Domain core `backend/app/domain/` gains nothing and imports nothing new. Results stay frequency +
EV. Grading stays behind the one `StrategyProvider`. No schema change, so no migration. FE types are
hand-maintained in `types.ts`. CSS values from tokens only; AA contrast and visible focus in both
themes. `sim_session.py` (1753 lines) grows only by the token check and the compare-and-set; the
current-session resolution goes in the new module. `spot_signature()` untouched.

## Golden paths

Route: `backend/app/api/v1/simulate.py` (the blind-check route's 409 at `:128-129`). Service module:
imitate the shape of `backend/app/services/sim_session.py`'s public functions, in a new small file.
Compare-and-set: `sim_session.py:1644-1673`. Backend API test: `backend/tests/test_simulate_api.py:21-36`.
Backend play test: `backend/tests/test_sim_session.py:80-90`. Frontend pure module + test:
`frontend/src/components/simulate/handCount.ts` and `handCount.test.ts`.

## Verify-by

`make check` green in the worktree. Backend tests prove: (a) the probe's situation (ii), stale call
after the other client dealt the next hand → 409 and no decision row for the new hand; (b) situation
(iii-a), stale call after a villain re-raise on the same street → 409 and the hero's stack unchanged;
(c) two simultaneous submits with the same token → exactly one 200 and one 409, exactly one decision
row at that ordinal; (d) `GET /session/current` returns the newest active session, 404 with none,
and is not shadowed by `/session/{id}`; (e) a stale deal → 409. Frontend tests prove the 409
detector and the token URL helper. Manual: two Mac tabs on one session, act in one, act in the
other → the notice appears and the table matches the first tab.

## Definition of done

Done = every Verify-by leg passes AND `make check` exits clean AND nothing outside the files named in
the tickets changed AND the roadmap, ledger, log and Resume block are updated in the same PR.
