# Spec — Simulate Hand-History + Replay ("Hand replayer")

Roadmap slice: `docs/ai-dlc/roadmap/simulate-table.md:1295` (NEXT → this delivers it).
Contract map: `docs/ai-dlc/contracts/sim-hand-replayer.md`. Inception 2026-07-22.

## Goal (one line)
Browse every past Simulate hand grouped by calendar day and step-replay any hand
action-by-action with the graded verdicts, staged card reveals, and a "mistakes only" filter.

## Requirements (locked in interview)
1. **Stepped replay log** — pick a hand → Next/Prev through each action in `action_history`
   order; board reveals per street; each hero decision surfaces its verdict inline. NOT the
   live animated felt (no reuse of `SimTable` live-pacing / `simPlayback.ts`).
   **All-in auto-runout board (Codex MED):** the engine can auto-run straight to the river without
   emitting per-street actions (`engine.py:225-235`), so a step's board must NOT be derived solely
   from the acting street. Rule: intermediate steps show the street-derived board; the **terminal
   step** (when `state.hand_over` and `showdown_seats` non-empty) shows the FINAL `state.board`
   (all dealt community cards), so a preflop/flop all-in still reveals the complete runout at
   showdown.
2. **Persist verdict text** — migration `0013` adds tier + reasoning TEXT to `sim_decision`,
   written at play time. Replay shows exactly what the hero saw. Pre-migration rows: text NULL →
   replay shows tier + EV-loss + coverage only (never fabricate reasoning).
   **Honor the live `graded` gate (refuter MED3):** the live wire suppresses tiers when
   `result.coverage == Coverage.NOT_FOUND` (`sim_session.py:799,830` — `graded = result is not
   None and coverage != NOT_FOUND`; `last_grade = _grade_view(row, result.tiers if graded else
   None)`). The new write persists `result.tiers` text **only when `graded`**, else NULL — so
   replay never shows verdict prose the live UI withheld for the same decision. (Feasibility
   confirmed: `result.tiers` is in-hand at the `apply_hero_action` write point.)
3. **Scope** — all sessions for the local owner (`owner_id == ""`), grouped by calendar day.
4. **Per-day ordinal** — "2026-07-22 Hand 32" = the **32nd COMPLETED hand** created that UTC
   calendar day across sessions, computed at query time from `created_at ASC, id ASC`; NOT
   `hand_no`, NOT a stored column. **Defined over complete hands only (Codex MED):** since
   abandoned hands stay `in_progress` forever with no resume path, they never later complete and
   re-number an already-shown list, so numbering is stable in practice; we accept the "Nth
   completed hand" definition rather than leave gaps. **UTC bucketing (Codex LOW):** SQLite may
   return `created_at` without `tzinfo` (see `tests/test_stats.py:80-88`); normalize before
   `.date()` — treat naive values as UTC, convert aware values to UTC — and test rows straddling
   midnight with both naive-UTC and non-UTC-aware inputs.
5. **Staged reveal (redesigned per refuter HIGH1 — no per-street reveal model exists).** There is
   NO per-step reveal rule in the engine to "mirror": `settle()` returns a flat
   `showdown_seats: set[int]` with no per-action granularity. So define the rule explicitly and
   simply: **all villains' hole cards stay hidden through every intermediate step; only at the
   TERMINAL showdown step are exactly `settle(state).showdown_seats`' cards revealed** (players who
   folded mucked — never revealed, matching live). Hero's own cards are always visible. This needs
   NO new domain scan — it derives from the existing `settle()` set applied at the last step. A
   villain's cards therefore NEVER appear in any `ReplayStepView` before the final step (NO-PEEK).
6. **List filter** — day-grouped, newest-first; a "mistakes only" toggle (hands containing any
   `correctness` in **{mistake, blunder}** — the losing tiers; the enum is
   `optimal/acceptable/mistake/blunder`, `domain/evaluation.py:18-21` — NOT "inaccuracy", which does
   not exist, refuter/Codex MED). Client-side on loaded tier data.
7. **Entry points** — (a) new top-nav **History** view + hash route; (b) a "replay last hand"
   shortcut inside `SimulateView` that opens the just-completed hand in the replayer.

## Files / interfaces to touch
### Backend
- `backend/alembic/versions/0013_*.py` — **new migration**: add `sim_decision.verdict_tier_text`
  (str|None) + `sim_decision.reasoning_text` (str|None); add index on `sim_hand.created_at`
  (day-grouped history query). `down_revision = "0012"`. **Downgrade MUST use
  `op.batch_alter_table` to drop the columns (SQLite limitation — refuter LOW/MED6; follow the
  0012 downgrade precedent exactly)** AND **explicitly `op.drop_index(...)` the `sim_hand.created_at`
  index (Codex MED)** — it lives on a different table than the batch-altered `sim_decision`, so the
  column-drop batch will NOT remove it and a re-upgrade would fail recreating a duplicate. Test
  up→down→up on SQLite AND assert the index is absent after downgrade.
- `backend/app/db/models.py` — `SimDecision`: two new nullable text fields (match migration).
- `backend/app/services/sim_session.py`:
  - `apply_hero_action` — when writing the `SimDecision` row, also persist the tier text +
    reasoning string the grader produced this turn (currently only in the live `_grade_view`).
  - **new** `list_history(db, owner_id="") -> HistoryListView` — join `sim_hand`→`sim_session`
    by owner, `status=="complete"` only, order **`created_at ASC, id ASC`** (refuter MED4 —
    `id` tiebreaker for stable per-day ordinals under `created_at` ties); bucket by UTC calendar
    day; assign per-day ordinal (1..N within each day, by that stable order); each item =
    {sim_hand_id, day, day_ordinal, hand_no, session_id, created_at, hero seat/position, worst
    tier present, has_mistake, n_decisions}. No `state_json` on wire.
  - **new** `get_hand_replay(db, sim_hand_id, owner_id="") -> HandReplayView` — load the hand,
    verify owner + `status=="complete"`; build a **scrubbed** ordered step list from
    `state_json.action_history`. **Seat derivation (refuter HIGH2):** `HistoryAction` carries
    `position` only, no `seat` — build a `position→seat_index` map once per hand from
    `state.seats[]` (each `SeatState` knows its seat + position under the hand's `button_seat`);
    resolve each step's seat through that map (add a unit test the map is total + correct).
    **Hero-verdict correlation (refuter HIGH2 + Codex HIGH):** filter `action_history` to the hero
    seat's own **non-POST** actions in chronological order (blinds/posts appear in history but
    generate NO `SimDecision` row), then zip against `_hand_decisions(sim_hand_id)` sorted by
    `ordinal`. For any **post-0010 hand** every accepted hero action writes exactly one decision in
    the same commit (`engine.py:299-306` + `sim_session.py:784-830`) → `len(hero_non_post) ==
    len(decisions)` holds; attach each verdict to its hero step. **Do NOT hard-assert equality
    blindly (Codex HIGH):** `sim_hand` predates `sim_decision` (migrations 0009 vs 0010) — a
    legacy 0009-era completed hand can carry hero actions with ZERO decision rows. So: correlate up
    to `min(len)`, treat a hero action with no matching decision as an **ungraded** step (tier+EV
    absent, same as NOT_FOUND display), and only raise on an *impossible surplus* (more decisions
    than hero non-POST actions) or an ordinal/action mismatch on the overlapping prefix. (Note: the
    live DB was fully wiped 2026-07-22, so no legacy rows exist today — this is defensive only.)
    Reuse `_grade_view` shape; persisted text feeds the reasoning when present, else tier+EV only.
    404 (`SessionNotFound`-style) if hand missing / not owned / not complete.
    **Staged reveal:** each step exposes hero cards always; villain cards only in the final
    (showdown) step and only for `settle(state).showdown_seats` — never earlier (server enforces).
- `backend/app/schemas/simulate.py` — **new** view types built field-by-field (privacy):
  `HistoryListItemView`, `HistoryListView`, `ReplayStepView`, `HandReplayView`. EV stays
  `ev_loss_bb` ≈approximate; verdict keeps tier + coverage, never boolean.
- `backend/app/api/v1/simulate.py` — **2 new routes**:
  `GET /simulate/history` → `list_history`; `GET /simulate/hand/{sim_hand_id}/replay` →
  `get_hand_replay`. Both owner-scoped to the `""` sentinel like existing routes.

### Frontend
- `frontend/src/api/types.ts` — **manually** add matching types for the 2 new responses.
- `frontend/src/lib/hashRoute.ts` — add `"history"` to the `View` union + a hand-id param carrier
  for `#/history` and an in-view selected-hand state (route need not encode the id if selection is
  component state; encode if deep-linking wanted — keep minimal).
- `frontend/src/App.tsx` — nav entry (`VIEWS`) + view switch case for History.
- `frontend/src/components/HistoryView.tsx` — **new**: fetch `/simulate/history`, render
  day-grouped list (date headers, per-day "Hand N" labels, worst-tier chip), "mistakes only"
  toggle, select → open replay.
- `frontend/src/components/simulate/HandReplay.tsx` — **new**: fetch replay, Next/Prev stepper,
  board strip, per-seat cards under staged reveal, inline hero verdict panel (reuse recap tier
  styling). Reuse existing card/seat presentational bits where static; do NOT wire live pacing.
- `frontend/src/components/SimulateView.tsx` — add "replay last hand" control (opens the
  just-completed hand in the replayer). **ID gap (Codex MED):** the live wire exposes no
  `sim_hand_id` — `SessionView` has `session_id` (`schemas/simulate.py:162-165`) and
  `SimulateHandView` has `hand_no` (`:141-165`) but NO hand id. So resolve the hand by the unique
  `(session_id, hand_no)` pair the FE already holds: `get_hand_replay` (or a thin lookup) accepts
  that pair, OR the replay endpoint gains a `?session_id=&hand_no=` alias. Do NOT add `sim_hand_id`
  to the live `SimulateHandView` (would break the byte-unchanged live-output promise).
- `frontend/src/styles/app.css` — component styles, **tokens only**; AA + visible focus both themes.

## Out of scope (v1)
What-if branching / re-simulation (bot actions not RNG-reproducible — contract A4). Editing or
annotating hands. Hand-history import/export (hard no-go). Trend graphs / per-street analytics
(separate "Session analytics" slice) — only the mistakes-only toggle ships here. SRS seeding from
replay. Animated-felt replay. 5+-way anything. Turn/river GRADER changes (replay only re-displays
what was already graded). **Hands abandoned mid-play are excluded** (refuter LOW5): `leave_session`
ends the session but leaves the live hand at `status=="in_progress"`; only `"complete"` hands are
replayable, so an abandoned hand silently won't appear in history — accepted v1 behavior, not a bug.

## Constraints (invariants)
- **Domain purity**: any pure reconstruction helper takes plain `HandState`/action data and stays
  web/DB-import-free (`tests/test_domain_purity.py`); DB access lives in `services/`.
- **Wire privacy**: no endpoint returns `state_json`, `full_board`, or a raw `HandState`; both new
  views built field-by-field. Staged reveal enforced server-side (don't ship a hidden villain's
  cards before their reveal step) — a NO-PEEK-style assertion in tests.
- **freq+EV never boolean**; EVs labeled ≈approximate. Verdict = tier + EV-loss + coverage.
- **Every schema change ships a migration** (0013, reversible); `spot_signature()` frozen; sim
  rows keep using `_sim_signature()` — replay/history NEVER routes through SRS `record_attempt()`.
- **FE types hand-maintained** in `types.ts` (edit manually; no gen step).
- **CSS tokens only**, WCAG AA + visible focus both themes.
- Existing live Simulate outputs **byte-unchanged** (new read paths are additive; the only write
  change is persisting two extra text fields — assert existing `_view`/recap tests still green).

## Verify-by (what /verify-change checks)
1. `./scripts/verify.sh` green (backend pytest + boot) incl. new tests; `ruff check .` clean.
2. `cd frontend && npm run typecheck && npm run build` green.
3. **Migration**: `0013` applies and reverses cleanly (up→down→up); existing rows get NULL text.
4. **Replay fidelity**: a seeded/known completed hand reconstructs the correct ordered action
   list + per-street board reveal + final showdown; hero-decision verdicts align to the right
   hero turns. Test with a fixture hand.
5. **Per-day ordinal**: two sessions the SAME UTC day → hands numbered 1..N continuously by
   `created_at`; a new day restarts at 1. Asserted.
6. **Privacy / staged reveal**: new endpoints never emit `state_json`/`full_board`/raw HandState;
   a villain's hole cards appear ONLY in the terminal showdown step and ONLY for
   `settle().showdown_seats` — never in any earlier step, never for a folded seat (NO-PEEK test
   walks every step asserting no hidden card leaks). Field-by-field `schemas/simulate.py` discipline.
6a. **Seat + verdict correlation**: a fixture hand asserts the `position→seat` map is total/correct
    and each persisted verdict lands on the right hero turn (`len(hero_non_post_actions) ==
    len(decisions)`); a hero POST is never mistaken for a decision.
6b. **Graded-gate parity**: a NOT_FOUND-coverage hero decision persists NULL verdict text and
    replay shows tier+EV only — identical to what the live UI showed that turn.
7. **Mistakes-only filter** returns exactly the hands with an inaccuracy/blunder decision.
7a. **Mistakes-filter value**: filter matches `correctness` in {mistake, blunder} exactly (a
    `mistake`-tier hand IS included; "inaccuracy" is not a value). FE type mirrors the same set.
8. **Persisted verdict text**: a hand played AFTER 0013 shows its real reasoning text on replay;
   a pre-migration (NULL) hand shows tier+EV only, no fabricated prose.
9. Existing live Simulate view/recap tests unchanged (green); no `spot_signature()`/SRS drift.
