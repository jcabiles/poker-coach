# Spec — P4, one live session across devices

status: **rev 2, APPROVED** — pre-authorized by the owner's `/ai-org:spec --auto-build` invocation,
2026-09-22, after a frontloaded interview (rulings recorded in the roadmap's P4 entry and below).
Rev 2 folds the blind review (`../reviews/phone-p4-live-session-r1-claude.md`, FAIL, 12 findings,
adjudicated in the ledger): the deal after a Watch-off fold carries the fold response's token; the
compare-and-set reads `rowcount` before commit and replaces the ORM write; "current" is ordered by
most recent hand activity; the leave route takes the token; the notice's placement is fixed; the
concurrency test gates the grading provider so it fails without the compare-and-set.
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
2. **`state_token` query parameter** on `POST /session/{id}/action`, `POST /session/{id}/hand` and
   `POST /session/{id}/leave` (`backend/app/api/v1/simulate.py`). Required at the route (a missing
   token is a 422, the schema's usual posture). At the service the parameter is optional
   (`expected_token: str | None = None`, `None` skips the check) so the ~59 existing service-level
   test calls stay valid; the router always passes it. It is a query parameter, not a body field,
   because the action body is `app.domain.action.Decision`, domain core shared with Practice grading.
3. **Staleness check** in `apply_hero_action`, `deal_next_hand` and `leave_session`
   (`sim_session.py`), BEFORE the turn guard and the legality check: token mismatch raises a new
   `StaleState` exception (its own class, not a `ValueError`, so the router can map it to 409 while
   illegal actions stay 400). A stale Leave is refused, not retried: the client refetches and the
   player presses Leave again if they still mean it.
4. **Compare-and-set at write time** in `apply_hero_action`. The ORM assignment
   `hand.state_json = ...` at `:1067` is REPLACED (not supplemented — with it in place autoflush
   writes the new value first and the compare fails every time, measured by the reviewer) by one
   Core statement `UPDATE sim_hand SET state_json = :new, status = :status WHERE id = :id AND
   state_json = :observed`. Its `rowcount` is read BEFORE `db.commit()`: 1 → commit as today;
   0 → `db.rollback()` (which discards the decision and attempt rows added earlier in the same
   request) and raise `StaleState`. The blind check's compare-and-set at `sim_session.py:1644-1673`
   is the golden path for the statement shape only; it commits before reading `rowcount`, which is
   exactly the order this slice must not copy. After a successful update, do not assign `state_json`
   or `status` on the ORM `hand` object; expire it if anything later reads it. This closes the
   `await` window at `:1023` regardless of whether the grading provider ever starts doing I/O.
5. **`GET /session/current`** → the owner's session with `status == "active"` that was played most
   recently: order by the newest `SimHand.created_at` of each active session, descending, then by
   `SimSession.created_at` descending (the id is a uuid and cannot break ties). Rendered through the
   existing `restore_session`. 404 when there is no active session or that one cannot be restored.
   Declared BEFORE `/session/{session_id}` in the router so the literal path wins (measured: order
   decides). Resolution lives in a new small module `backend/app/services/sim_current.py`; the
   router stays the HTTP translation layer. Ordering by activity rather than creation is a Director
   refinement inside the owner's "newest active" ruling: it keeps an orphaned older session (a
   pre-P4 table whose browser key was lost) from outranking the table actually being played.
6. Router: `StaleState` → `HTTPException(409, "stale state")`.
6a. **Not covered by the token, by design:** answering the Challenge blind check writes
    `SimSession.blind_check_json` only, so the token does not move. That flow already has
    first-write-wins and its own "Answered in another window" rendering, which is the correct
    behaviour for two devices; nothing changes there.

### Frontend

7. **`frontend/src/api/types.ts`**: `SessionView.state_token: string`.
8. **Boot** (`SimulateView.tsx`): on mount, GET `/session/current`. 200 → adopt it and write the
   localStorage key as today. 404 → clear the key and show the sit-down screen (the same path as
   today's session-not-found). Any other failure → fall back to today's behaviour (GET
   `/session/{stored id}`), so a broken current-route never strands the player on the generic
   error panel.
9. **Actions, deals and Leave** send `?state_token=` — normally `view.state_token` from the view
   currently rendered. The one exception is the Watch-off fold path (`SimulateView.tsx:702-718`),
   which folds and deals in one handler without adopting the fold response: its deal MUST send
   `folded.state_token` from the fold response, never the pre-fold token, or every such fold would
   refuse its own deal and the Challenge hand-200 gate (which `deal_next_hand` returns in place of
   a new hand) would never appear. The fetchers in `frontend/src/api/client.ts` (`postHeroAction`,
   `postNextHand`, `leaveSession`) gain the token argument, and a `getCurrentSession` fetcher joins
   `getSession` there so the error shape `errorStatus` parses stays the one `json<T>` produces.
10. **409 branch** beside `isSessionNotFound` in `run`'s catch: refetch `/session/{id}`, adopt, and
    set a one-line notice "Acted elsewhere — table refreshed." rendered with `role="status"`. It
    clears on the next successful write. If the fold in the Watch-off path returns 409, the deal is
    never sent because the `await` throws first; the ticket proves this by reading the path and by
    the pure-module test of the token helper.
11. New pure module `frontend/src/components/simulate/staleState.ts` (+ `.test.ts`): `isStaleState`
    (409 detector, mirrors `isSessionNotFound`) and `withStateToken(path, token)`.
12. **Notice placement** (`app.css`, tokens only, both themes, AA contrast): on desktop, in flow
    directly above the action bar. Under the phone gate (where the dock is `position: fixed` and the
    page reserves its strip), the notice is a fixed, non-interactive line anchored just above the
    dock — it takes no layout space, so the buttons do not move under the thumb (the regression
    `app.css:6947-6952` records), and it cannot scroll off screen. Never inside the dock frame.

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
themes. `sim_session.py` (1962 lines) grows only by the token checks and the compare-and-set; the
current-session resolution goes in the new module. `spot_signature()` untouched. The sit-down
screen is never offered while an active session exists (boot lands on it), so a second live
session cannot be created from the UI without leaving the first, which ends it.

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
(c) two concurrent submits with the same token → exactly one 200 and one 409 and exactly one
decision row at that ordinal — run as two tasks on ONE event loop with `sim_session._grading_provider`
monkeypatched to a fake whose `evaluate` awaits a test-controlled `asyncio.Event`, so both requests
are inside the read-modify-write window together; this test must FAIL with the compare-and-set
removed (two TestClients on two threads never reach the window and prove nothing); (d) `GET
/session/current` returns the most recently played active session (an older active session with a
newer hand outranks a newer session with no hands), 404 with none, and is not shadowed by
`/session/{id}`; (e) a stale deal → 409 and a stale leave → 409 with the session still active;
(f) `test_simulate_api.py`'s unknown-session case still gets 404 when a token is supplied. Frontend
tests prove the 409 detector and the token URL helper. Manual: two Mac tabs on one session, act in one, act in the
other → the notice appears and the table matches the first tab.

## Definition of done

Done = every Verify-by leg passes AND `make check` exits clean AND nothing outside the files named in
the tickets changed AND the roadmap, ledger, log and Resume block are updated in the same PR.
