# Tickets — Two-mode Simulate (Training / Challenge)

status: **approved** — owner, 2026-08-26, at the `/ai-org:build` plan gate. All eight tickets
below are cleared to build, in the declared order. Approval covers building, running the
migration against the local development database, and committing to a feature branch. It does
**not** cover merging. Plan: `../plans/two-mode-simulate.md`. Spec:
`../specs/two-mode-simulate.md` (rev 2). Ledger: `../ledger/two-mode-simulate.md`.

## Shape of the work

Eight tickets in **one sequential chain** — nothing parallelises. Every backend ticket owns
`backend/app/services/sim_session.py` and every frontend ticket owns
`frontend/src/components/SimulateView.tsx`; both are single-owner files, so two tickets can
never be in flight at once. T5 is the hinge: the frontend cannot start until the API shape is
final.

`T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8`

**Run the whole backend suite at every barrier, not a name-filtered selection.** Corrected
2026-08-26 after review: `pytest -k "sim or simulate"` matches the *module filename*, so it
silently deselects `tests/test_grade_map_turn_river.py`, which drives more than two thousand
hands through `deal_next_hand()` — past the gate — and `tests/test_coach.py`, which posts to the
Simulate create route. A gate mis-fire in either would be invisible to the filtered run. Worse,
a new test module whose filename lacks both words is deselected entirely and the check reports
the unchanged baseline while running none of the new tests, which nearly happened during T3. The
filtered selection is fine while developing; the barrier uses `pytest -q` and costs ten minutes.

**Baseline before starting:** `./scripts/verify.sh` on `main` is **2 failed, 2189 passed** — two
pre-existing failures in `backend/tests/test_detection_probe.py`, unrelated to this work. Every
done-condition below means "no failure other than those two, and no drop in the passing count."

---

### T1 — Two nullable columns on the session, plus the migration

Add `mode` and `blind_check_json` to `SimSession`, both nullable, with `NULL` read as
`"training"`, and the Alembic migration that adds them.

- **Owns:** `backend/app/db/models.py`, `backend/alembic/versions/0015_*.py` (head is `0014`).
- **Imitate:** `DrillAttempt.source` (`models.py:38-42`) and migration `0010` — the repo's
  documented nullable add-column pattern.
- **Acceptance:** a database populated at revision `0014` containing an **active** session
  upgrades cleanly; that session afterwards reads as Training with its hand state unchanged.
- **Done:** `cd backend && PYTHONPATH=. .venv/bin/python -m pytest tests/test_db.py -q` green,
  plus the new populated-upgrade test.

### T2 — Mode accepted at creation and carried on every response

`create_session()` takes a mode defaulting to `"training"`; the create route accepts an optional
JSON body; `SessionView` carries `mode` and `blind_check`.

- **Owns:** `backend/app/schemas/simulate.py`, `backend/app/api/v1/simulate.py`,
  `backend/app/services/sim_session.py`.
- **Imitate:** `SeatView` / `VillainRangeView` for the schema; the existing routes at
  `simulate.py:71-108`.
- **Acceptance:** `mode` is a literal union, never a bare `str`; a create call with no body still
  works and yields Training; a Challenge session reports `mode="challenge"` and every villain row
  still has a populated `SimSeat.persona_type` in the database.
- **Depends:** T1.

### T3 — Correct the completed-hand count and bar the deal at the gate

Derive completed hands as `hand_no - (0 if hand_over else 1)`, and make `deal_next_hand()` refuse
to advance a Challenge session that has 200 completed hands and no stored check.

- **Owns:** `backend/app/services/sim_session.py`.
- **Acceptance:** the completed-hand derivation returns **199 while hand 200 is live and 200 once it
  settles**, so the gate fires at exactly the moment hand 200 settles and never at 199 completed hands; `deal_next_hand()` returns the settled hand unchanged at the
  gate and resumes once a check is stored, including via the skip path.
- **Why it is server-side:** `SimulateView.tsx:492-508` posts a fold and the next deal inside one
  handler when Watch is off, so no browser guard can interpose.
- **Depends:** T2.

### T4 — The blind-check endpoint: seat pick, scoring, idempotency

`_blind_check_seats()` picks three seats from a `hashlib.sha256` digest of the session id,
without replacement; `submit_blind_check()` scores against `SimSeat.persona_type`; one new route
at `POST /api/v1/simulate/session/{session_id}/blind-check` — **singular**.

- **Owns:** `backend/app/services/sim_session.py`, `backend/app/api/v1/simulate.py`,
  `backend/app/schemas/simulate.py`.
- **Acceptance:** three **distinct** non-hero seats, identical across separate processes (assert
  against a hard-coded triple for a fixed session id — Python's `hash()` is salted and must not
  be used); scoring correct on a known roster; `409` before the gate; `400` for unexpected seat
  indices; a duplicate submission returns the first stored result rather than overwriting; a skip
  stores `{"skipped": true}`.
- **Depends:** T3.

### T5 — Frontend types and client calls

Hand-maintain the new API types and give the client its two new calls.

- **Owns:** `frontend/src/api/types.ts`, `frontend/src/api/client.ts`.
- **Note:** `postSimulateSession()` currently takes no argument (`client.ts:105-107`).
- **Acceptance:** types match the API exactly; there is no generated types file to regenerate.
- **Done:** `cd frontend && npm run typecheck`.
- **Depends:** T4.

### T6 — The mode-choice screen, on all three creation paths

A two-card sit-down screen, and routing every path that currently creates a session eagerly
through it.

- **Owns:** `frontend/src/components/simulate/SimModeChoice.tsx` (new),
  `frontend/src/components/SimulateView.tsx`, `frontend/src/styles/app.css`.
- **Acceptance:** first boot, the 404 recovery (`SimulateView.tsx:462-470`) and Leave Table
  (`:549-566`) all land on the choice screen rather than silently creating Training; restoring an
  existing session never re-asks; design tokens only, AA contrast and visible focus in both
  themes.
- **Depends:** T5.

### T7 — The display gate and the Labels toggle

One `labelsVisible` boolean threaded to the three rendering components, plus the two-way pill
that appears only after the unlock.

- **Owns:** `frontend/src/components/simulate/SimLabelsToggle.tsx` (new), `SimTable.tsx`,
  `SimLedger.tsx`, `SimRangeChart.tsx`, `frontend/src/components/SimulateView.tsx`,
  `frontend/src/styles/app.css`.
- **Imitate:** `SimGradingToggle.tsx` — real `<button>`, `aria-pressed`, gilt pressed state,
  never colour alone. Namespace its storage key by session id so the toggle re-arms on a new
  table. Note that the four existing storage keys at `SimulateView.tsx:47-50` are **not**
  namespaced — they are where storage keys are declared, not an example of the pattern to copy.
- **Acceptance:** in Challenge before the unlock, no seat plate or `title=`, no range button, no
  exploit note, and the ledger's Player column shows a stable `seat_index` identity — never
  `position` (already the adjacent column, and it rotates every hand) and never `"You"`. The
  toggle is absent from the DOM before the unlock, not disabled. Hiding labels again **closes any
  open range panel** and discards an in-flight range response.
- **Depends:** T6.

### T8 — The hand-200 dialog and its score

The dialog over the table, its submission, and the one-time score line afterwards.

- **Owns:** `frontend/src/components/simulate/SimBlindCheck.tsx` (new),
  `frontend/src/components/SimulateView.tsx`, `frontend/src/styles/app.css`.
- **Acceptance:** the dialog opens when the gate is open with no stored check, offers six options
  per seat, is skippable, and a tab holding a stale dialog learns from its next response that the
  check was answered. The score displays once and is never presented as a measurement — the
  lineup is a fixed multiset (`domain/table/play.py:44-54`), so this is a closed-set task.
- **Depends:** T7.

---

### Finish the slice

The last ticket also ticks this slice in `docs/ai-dlc/roadmap/bot-realism-flywheel.md` and
updates `docs/ai-dlc/ledger/two-mode-simulate.md`, both in the same change — the definition of
done forbids leaving an invalidated document behind.
