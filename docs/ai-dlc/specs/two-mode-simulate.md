# Spec — Two-mode Simulate (Training / Challenge)

status: **approved rev 2** — owner, 2026-08-26, at the `/ai-org:build` plan gate. Cleared to
build. Merging is a separate confirmation.
slice of: `../roadmap/bot-realism-flywheel.md` (rev 9, NOW lane, "Two-mode Simulate")
contract map: `../contracts/persona-label-toggle.md`
reviews: `../reviews/two-mode-simulate-r1-claude.md`, `../reviews/two-mode-simulate-r1-sol.md`
finding ledger: `../ledger/two-mode-simulate.md`
design: canvas "Simulate — Training vs Challenge", five screens, direction "Two rooms"

## Bottom line

The player chooses a mode when they sit down at a Simulate table, and it is fixed for that
session. **Training** is the app exactly as it stands today. **Challenge** withholds every
on-screen reference to an opponent's archetype from hand 1; at 200 completed hands the deal
stops until the player names three seats, after which the labels open and stay controllable for
the rest of the session.

Nothing about how the bots play changes. Nothing about what is recorded changes — every hand
keeps its archetype in the database in both modes. This is a display gate, one new API route,
and two new columns.

**Rev 2 (2026-08-26)** rewrites this spec after both blind reviewers returned REJECT. Eleven
findings were verified against the code and accepted; the ledger records each one with its
evidence. The three that changed the design rather than just the wording: the completed-hand
arithmetic was wrong at the exact transition the gate depends on, the pause has to be enforced
on the server rather than in the browser, and the ledger's Player column cannot fall back to
position because position already has its own column and rotates every hand.

## Goal

One line: let a player choose, at sit-down, between a Simulate session that names its opponents
and one that makes them earn the read over 200 hands.

## Behaviour

### Choosing the mode

1. The Simulate route opens on a mode-choice screen whenever there is no session to restore.
   Two cards, side by side, no pre-selection: **Training** (plain) and **Challenge** (accented).
2. Choosing either creates the session with that mode. The mode is **fixed for the session**.
   Leaving the table and sitting down again is the only way to change it.
3. Restoring an existing session restores its stored mode, and never re-asks.
4. **All three paths that currently create a session eagerly must route through the choice
   screen instead** — first boot, the 404 recovery at `SimulateView.tsx:462-470`, and Leave
   Table at `:549-566`. Left alone, each silently creates a Training session, which is how a
   Challenge player would lose their mode without being told.

### Training mode

5. Identical to the app as it stands: archetype plate on every non-hero seat, range chip on
   every live non-hero seat, preflop exploit note showing.
6. The only addition is a quiet outlined **Training** stamp beside the "Simulate" heading.

### Challenge mode, before the unlock

7. From hand 1 until the unlock, none of the four archetype display sites render: the seat plate
   and its `title=` tooltip, the ledger's Player column, the villain-range panel header, and the
   preflop exploit note. The note is suppressed **whole** — stripping the archetype name from
   its lines would leave the read intact ("a LAG opens too many hands" still says LAG).
8. The villain-range **button** does not render, so the panel cannot be opened.
9. The ledger's Player column shows a **stable neutral seat identity derived from
   `seat_index`** — "Seat 3". It must not show `seat.position`: position is already the
   adjacent Seat column (`SimLedger.tsx:59`) and it rotates every hand
   (`sim_session.py:1407`), so using it would both duplicate a column and destroy the running
   per-opponent profit attribution, which is the exact faculty these 200 hands exist to train.
   It must not show `"You"`, which is what today's null-safe helper returns for a null persona
   (`SimLedger.tsx:17-18`).
10. The heading carries a gold **Challenge** stamp, and the hand counter reads `Hand N / 200`
    with a progress bar beneath it.

### The unlock at 200

11. **Completed hands = `hand_no - 1` while a hand is live, and `hand_no` once it is over.**
    `deal_next_hand()` early-returns without incrementing while `status == "in_progress"`, and
    increments only after the hand settles (`sim_session.py:1398-1412`). Both `hand_no` and
    `hand.hand_over` are already on the wire, so the derivation is
    `hand_no - (0 if hand_over else 1)`. **No new counter column.** A naive `hand_no - 1` fires
    the gate only after hand 201 has been dealt and shows "Hand 201 / 200".
12. **The pause is enforced on the server.** While a Challenge session has 200 completed hands
    and no stored blind check, `deal_next_hand()` refuses to advance and returns the settled
    hand unchanged. A browser-side guard is not sufficient: with Watch off, a hero fold posts
    the action and the next deal back to back inside one handler
    (`SimulateView.tsx:492-508`), so nothing in the frontend can interpose a dialog.
13. When the gate is open and no check is stored, the client shows a dialog asking the player to
    name the archetype of **three seats**, six options each: nit, TAG, LAG, maniac, calling
    station, passive fish.
14. **The three seats are chosen from a stable digest of the session id** — `hashlib.sha256`,
    not Python's built-in `hash()`, which is salted per process and would pick different seats
    after a restart. Sampled **without replacement** from the eight non-hero seats, so the three
    are always distinct and never the hero.
15. The dialog is skippable. **A skip stores a result too** (`{"skipped": true}`), because the
    gate re-fires until something is stored — otherwise the unlock un-does itself on the next
    reload and the deal stays barred forever.
16. Submitting scores the guesses against `SimSeat.persona_type` and stores the result. The score
    is displayed once, on the next screen, and thereafter lives only in the record.
17. **The lineup is a fixed multiset** — two passive fish, two TAGs, one calling station, one
    nit, one LAG, one maniac (`backend/app/domain/table/play.py:44-54`). The six options are
    therefore not equiprobable and this is a closed-set task, the same limitation this
    initiative's roadmap already records against the "56 of 56" blind-identification result. The
    score is a keepsake for the player, not a measurement, and no document may cite it as one.

### Challenge mode, after the unlock

18. All four display sites return, and the villain-range button returns with them.
19. The counter drops the `/ 200` and its progress bar.
20. A two-way **Labels: Shown / Hidden** control appears in the top control cluster and governs
    all four sites at will for the rest of the session. It is **absent** before the unlock — not
    present-and-disabled.
21. **Hiding labels again must close any villain-range panel that is already open**, and discard
    an in-flight range response. The panel is mounted independently of the button
    (`SimulateView.tsx:839-847`), so gating only the button leaves an open panel and its persona
    header on screen.
22. The mode stamp never becomes a switch. It still reads Challenge, because the session is one.
23. The toggle is **tab-local**: it survives a reload within the session but two tabs may differ.
    The blind check is the opposite — **session-wide and server-authoritative** — so a tab
    holding a stale dialog learns the check was answered from its next response.

## Wire contract

- `POST /api/v1/simulate/session` gains an optional JSON body `{"mode": "training" |
  "challenge"}`, defaulting to `"training"` when absent so existing callers keep working. Typed
  as a literal union, never a bare `str`.
- `SessionView` gains `mode: Literal["training","challenge"]` and
  `blind_check: BlindCheckView | None`.
- `POST /api/v1/simulate/session/{session_id}/blind-check` — **singular `/session/`**, matching
  every existing route (`simulate.py:71-108`). Body: three `{seat_index, guess}` entries, or
  `{"skipped": true}`. Response: the scored `BlindCheckView`.
- **Idempotency: first write wins.** A duplicate or conflicting submission does not overwrite;
  it returns the stored result with `200`. A submission before the gate opens returns `409`. A
  submission naming seats other than the three the digest selects returns `400`.

## Files and interfaces to touch

### Backend

- `backend/app/db/models.py` — two columns on `SimSession`: `mode` and `blind_check_json`, both
  **nullable**, with `NULL` read as `"training"`. This follows the repo's documented
  add-column pattern (`models.py:40-42`) and avoids a non-null add-column against a populated
  SQLite table.
- `backend/alembic/versions/0015_*.py` — one migration adding both columns. Head is `0014`.
- `backend/app/schemas/simulate.py` — `SessionView` gains the two fields; new `BlindCheckView`,
  a create-request model, and a submission model.
- `backend/app/services/sim_session.py` — `create_session()` takes a mode; `_view()` carries the
  new fields; `_blind_check_seats(session_id)` for the stable digest pick; `submit_blind_check()`
  scoring against `SimSeat.persona_type`; and the deal barrier inside `deal_next_hand()`.
- `backend/app/api/v1/simulate.py` — the create route accepts a body; one new route.

### Frontend

- `frontend/src/api/types.ts` — hand-maintained: the two `SessionView` fields, `BlindCheckView`,
  and the request/response types.
- `frontend/src/api/client.ts` — `postSimulateSession()` currently takes no argument (`:105-107`)
  and must send the mode; plus a client call for the blind check.
- `frontend/src/components/SimulateView.tsx` — the mode-choice gate on all three creation paths;
  computes one `labelsVisible: boolean` and threads it down; owns the toggle state, the dialog,
  and the panel-close on re-hide.
- **New** `frontend/src/components/simulate/SimModeChoice.tsx` — the two-card sit-down screen.
- **New** `frontend/src/components/simulate/SimBlindCheck.tsx` — the hand-200 dialog.
- **New** `frontend/src/components/simulate/SimLabelsToggle.tsx` — the two-way pill.
- `frontend/src/components/simulate/SimTable.tsx` — gate the plate and the range button.
- `frontend/src/components/simulate/SimLedger.tsx` — the neutral seat identity of §9.
- `frontend/src/components/simulate/SimRangeChart.tsx` — suppress the exploit note.
- `frontend/src/styles/app.css` — styles for the three new components, design tokens only.

### Also in scope, and named here because the definition of done forbids unnamed files

`backend/tests/` (new test modules) · `docs/ai-dlc/roadmap/bot-realism-flywheel.md` (tick the
slice) · `docs/ai-dlc/ledger/two-mode-simulate.md`.

## Golden paths to imitate

| New thing | Imitate |
|---|---|
| The Labels toggle | `frontend/src/components/simulate/SimGradingToggle.tsx` — real `<button>`, `aria-pressed`, gilt pressed state, never colour alone. Its doc comment already states this feature's invariant. |
| Session-scoped client state | `SimulateView.tsx:47` `STORAGE_KEY` — namespace the toggle key by session id so it re-arms on a new table. |
| A new endpoint | the existing routes in `backend/app/api/v1/simulate.py`. |
| A new response schema | `SeatView` / `VillainRangeView` in `backend/app/schemas/simulate.py`. |
| A new migration | `backend/alembic/versions/0014_sim_decision_reasoning_parts.py`. |
| A nullable added column | `DrillAttempt.source` (`models.py:38-42`) and migration `0010`. |

## Out of scope

The random table picker and the custom roster chooser (still frozen) · any change to bot
behaviour, grading, stakes, or the persona engine · History and replay views, which carry no
persona field at all · `REVEAL_ENABLED` and showdown card reveal, which are an unrelated
feature · any edit to `content/` values · retro-fitting a mode onto sessions that already exist,
which the migration handles by reading them all as Training.

## Constraints

- The domain core `backend/app/domain/` gains nothing; the purity test stays green.
- `SimSeat.persona_type` is never nulled — not in the database, not on the wire. All hiding is
  view-layer, so history, replay and the analytics export stay attributable. This is clause (c)
  of the owner's ruling and it is the one thing that must not bend. It does mean the archetype
  rides the wire during Challenge and is visible in developer tools; that is the accepted trade,
  because nulling it breaks two consumers (see Known traps).
- Committed `content/` pack values are frozen. The exploit note is suppressed by a display gate.
- Grading stays behind the one async `StrategyProvider`; nothing here touches it.
- CSS values from design tokens only; WCAG AA contrast and a visible focus ring in both themes.
- The schema change ships its Alembic migration in the same change.
- `spot_signature()` is frozen and untouched.
- Frontend API types are hand-maintained; edit `types.ts` in the same change.
- No auth, accounts, or hosting.

## Known traps

- **`REVEAL_ENABLED` is not this feature's seam.** It gates showdown hole-card reveal
  (`sim_session.py:155-158`). The roadmap said otherwise until rev 9. Do not reuse or extend it.
- **Never hide by nulling `persona_type` on the wire.** Two consumers break: the villain-range
  button disappears with it (`SimTable.tsx:313`), and `personaLabel(null)` returns `"You"`
  (`SimLedger.tsx:17-18`), so every villain row would read "You".
- **The range panel header and the exploit note are independent server paths.** Hiding
  `SeatView.persona_type` would not hide them; they read `persona_type` server-side at
  `sim_session.py:1344` and `:1141`.
- **The range button is not a leak.** Every non-hero seat is a bot, so its presence reveals
  nothing. It is hidden because it opens a panel that does leak.
- **`./scripts/verify.sh` is already red on `main`.** Two pre-existing failures in
  `backend/tests/test_detection_probe.py` (`CorpusBuildError: no complete hands`, from a pinned
  local corpus), unrelated to this work. Baseline as of 2026-08-26: **2 failed, 2189 passed.**

## Verify by

1. `./scripts/verify.sh` — no failures beyond the two baseline ones named above, and no
   reduction in the passing count.
2. `cd backend && ruff check .`
3. `cd frontend && npm run typecheck && npm run build`
4. New backend tests, each failing before the change and passing after:
   - a Challenge session reports `mode="challenge"` and every villain row still has a populated
     `SimSeat.persona_type` in the database;
   - the completed-hand derivation returns **199 while hand 200 is live and 200 once it
     settles**, so the gate fires exactly when hand 200 settles and never at 199 completed
     hands;
   - `deal_next_hand()` refuses to advance a Challenge session at the gate with no stored check,
     and resumes once one is stored — including via the skip path;
   - the blind check scores a known roster correctly; rejects submission before the gate with
     `409`; rejects unexpected seat indices with `400`; and on a duplicate submission returns the
     first stored result rather than overwriting;
   - `_blind_check_seats()` returns three **distinct** non-hero seats, identical across separate
     processes (assert against a hard-coded expected triple for a fixed session id);
   - a database populated at revision `0014` with an **active** session upgrades cleanly, and
     that session restores as Training with its hand state unchanged.
5. End to end in the running app: start a Challenge session and confirm no plate, no range chip
   and no exploit note at hand 1; advance a test session to the gate and confirm the deal stops,
   the dialog appears, the score shows, the labels return, and the Labels toggle appears where it
   was previously absent from the DOM; then hide labels again with a range panel open and confirm
   the panel closes.

## Definition of done

Every acceptance criterion above passes · `./scripts/verify.sh` shows no failure other than the
two baseline ones, ruff is clean, and the frontend typechecks and builds · nothing outside the
files named in **Files and interfaces to touch** and **Also in scope** has changed · the slice is
ticked in the roadmap and the finding ledger is up to date, both in the same change.
