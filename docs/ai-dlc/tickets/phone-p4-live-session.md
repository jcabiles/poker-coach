# Tickets — P4, one live session across devices

status: **approved (pre-authorized by --auto-build invocation, 2026-09-22)** — covers T1–T3 exactly
as written and nothing else. spec: `../specs/phone-p4-live-session.md` · contract map:
`../contracts/phone-p4-live-session.md` · ledger: `../ledger/phone-and-6max.md` · roadmap:
`../roadmap/phone-and-6max.md` (slice P4).

## Shape of the work

Two code tickets that own disjoint files and run together, then one docs ticket the Director does.
The API shape (token field, query parameter, 409, current route) is fixed in the spec, so the
frontend does not wait for the backend.

```
T1 (backend)  ─┐
               ├─→ fan-in: make check + blind refuter ─→ T3 (docs, Director) ─→ PR
T2 (frontend) ─┘
```

Build in the worktree `$TMPDIR/wt-p4` on branch `feat/phone-p4-live-session` (node_modules and
`.venv` are symlinked from the main checkout). Baseline `make check` on the untouched worktree is
green (frontend and backend, 2026-09-22).

---

### T1 — state token, staleness refusal, compare-and-set, current-session route (backend)

- **Owns:** `backend/app/services/sim_session.py`, `backend/app/schemas/simulate.py`,
  `backend/app/api/v1/simulate.py`, new `backend/app/services/sim_current.py`, new
  `backend/tests/test_live_session.py`, and the three route-level test files that call the action,
  hand or leave routes and must now pass the token they just received: `backend/tests/test_simulate_api.py`,
  `backend/tests/test_two_mode_simulate.py`, `backend/tests/test_two_mode_simulate_blind_check.py`.
  Service-level tests (~59 calls across 10 files) are NOT touched: the service parameter is optional
  and `None` skips the check (spec item 2).
- **Imitate:** route + 409 → `api/v1/simulate.py:113-133` (blind-check route); compare-and-set →
  `sim_session.py:1644-1673`; API test with temp DB → `tests/test_simulate_api.py:21-36`; driving
  real play → `tests/test_sim_session.py:80-90`.
- **Do:** spec items 1–6a. `state_token` on `SessionView`; route-required, service-optional
  `state_token` on the action, hand and leave routes; `StaleState` raised before the turn guard when
  the token mismatches; the hand-state write replaced by one Core `UPDATE ... WHERE state_json =
  :observed` whose `rowcount` is read BEFORE commit, with `db.rollback()` and `StaleState` on 0;
  `GET /session/current` declared before `/session/{session_id}`, resolved in `sim_current.py` by
  most recent hand activity; router maps `StaleState` → 409 `"stale state"`.
- **Acceptance:** tests in `test_live_session.py` prove Verify-by legs (a)–(f) of the spec. Leg (c)
  is the one that matters: two tasks on one event loop with `_grading_provider` monkeypatched to a
  fake that awaits an `asyncio.Event`, asserting one 200, one 409, and a single `sim_decision` row
  at that `(sim_hand_id, street, ordinal)`; the worker's report states that this test fails when
  the compare-and-set is commented out. Every existing test still passes; route-level tests are
  updated to pass the token they just received — never by loosening the check.
- **Done-condition:** `make check-backend` exits 0 from the worktree.
- **Do not:** add a column or migration; touch `backend/app/domain/`; change `Decision`; grow
  `sim_session.py` beyond the token check and the compare-and-set (the current-session lookup
  lives in `sim_current.py`).

### T2 — boot from the server's current session, token on writes, 409 notice (frontend)

- **Owns:** `frontend/src/components/SimulateView.tsx`, `frontend/src/api/client.ts` (the three
  fetchers gain a token argument; `getCurrentSession` joins `getSession`), `frontend/src/api/types.ts`,
  `frontend/src/styles/app.css` (the notice's rules only), new
  `frontend/src/components/simulate/staleState.ts` + `staleState.test.ts`.
- **Imitate:** pure module + test → `simulate/handCount.ts` and `handCount.test.ts`; error-status
  branching → `isSessionNotFound` at `SimulateView.tsx:117-119` and its use at `:672-681`.
- **Do:** spec items 7–12. `SessionView.state_token` in `types.ts`; boot via `getCurrentSession`
  with the 404 → sit-down and other-failure → stored-id fallback; `?state_token=` on every action,
  deal and leave call, and in the Watch-off fold path the deal sends `folded.state_token` from the
  fold response (spec item 9 — this is the finding that would otherwise break every such fold and
  the Challenge hand-200 gate); the 409 branch that refetches, adopts, and shows "Acted elsewhere —
  table refreshed." as a `role="status"` line, cleared on the next successful write; placement per
  spec item 12 (in flow above the action bar on desktop; fixed just above the dock under the phone
  gate, taking no layout space); the pure module `staleState.ts` with `isStaleState(err)` and
  `withStateToken(path, token)`.
- **Acceptance:** `staleState.test.ts` proves the 409 detector (409 → true, 404/400/500 → false,
  non-Error → false) and that `withStateToken` encodes the token and keeps existing query strings.
  The report cites the line where the Watch-off deal takes its token from the fold response, and
  the line where a fold's 409 prevents the deal. Desktop layout at 1280px unchanged; the phone dock's
  buttons do not move when the notice appears; the notice meets AA contrast in both themes using
  tokens only.
- **Done-condition:** `make check-frontend` exits 0 from the worktree.
- **Do not:** touch `App.tsx`, `hashRoute.ts`, or any file outside the owned list; add a
  dependency; read error bodies (the client drops them by design); change `json<T>`'s error shape.

### T3 — roadmap reconciliation, ledger, log, Resume (Director, after fan-in)

- **Owns:** `docs/ai-dlc/roadmap/phone-and-6max.md`, `docs/ai-dlc/ledger/phone-and-6max.md`,
  `docs/ai-dlc/log.md`, `docs/ai-dlc/profile.md`, `docs/ai-dlc/START-HERE.md` if it names P2 as next.
- **Do:** spec item 13.
- **Done-condition:** the roadmap's P1, S1 and P2 entries carry their build status; P4's entry
  carries the probe verdict and rulings; the ledger has the P1(c) entry and the P4 review round with
  every finding adjudicated; Resume block points at P3b as the next action.
