# Tickets — S1, the 6-max table option

status: **rev 2, APPROVED** — rev 1 pre-authorized by John's `/ai-org:spec --auto-build`
invocation, 2026-09-18; rev 2 rewritten after a blind review returned FAIL and the owner ruled on
its four escalations the same day. The approval covers T0–T7 as written and nothing else. The
roadmap's S1 box is not ticked by this build.
spec: `../specs/simulate-6max-s1.md` (rev 2) · contract map: `../contracts/simulate-6max.md` ·
ledger: `../ledger/simulate-6max-s1.md` (round 1) · roadmap: `../roadmap/phone-and-6max.md`

## Shape of the work

Eight tickets. One database column, one migration, a seat count threaded through the pure domain,
a four-room sit-down screen, and a test suite whose main job is proving nine-max did not move.

```
T0 (capture parity fixture — MUST be first, on origin/main)
     │
     ├─→ T2 (deck + engine) ─┐
     ├─→ T3 (range + lineup) ─┼─→ T1 (persistence + service + sim key) ─┬─→ T5 (sit-down screen) ─┐
     └─→ T4 (grading)        ─┘                                          └─→ T6 (felt + blind check) ─┤
                                                                                                      └─→ T7 (tests + sweep)
```

T2, T3 and T4 touch disjoint files and may run in parallel. T5 and T6 are both frontend but own
different files. T7 runs last and is the ticket that can actually fail the slice.

**Build in a worktree.** The shared checkout is used by other sessions and the owner's stack runs
from it. The Python interpreter lives in the main checkout at `backend/.venv`; worktrees have none,
so symlink it rather than creating a second one.

**Never touch `backend/data/poker_coach.db`.** Print `app.db.session.DB_PATH` and stop unless it is
under the worktree, *before* running Alembic and *before* starting any server.

**The rule that outranks the others:** nine-max play comes out byte-identical. If a change makes a
9-max test need editing, the change is wrong — fix the change, not the test.

---

### T0 — Capture the byte-identical fixture, before anything else

- **Owns:** `backend/tests/fixtures/ninemax_parity.json` (new).
- **Do:** on a clean checkout of `origin/main`, run a fixed seed through the deal, the position map
  for every button seat, a full button rotation, and the grades for a set of hero decisions. Commit
  the captured output as a fixture.
- **Why this is a separate ticket and why it is first:** the spec's second-strongest claim is that
  9-max is unchanged. If the fixture is generated *after* the change, it records the new behaviour
  and the test compares the new code to itself — it passes whether or not parity holds. The
  reviewer flagged rev 1's version of this step as unfalsifiable, and it was.
- **Acceptance:** the fixture exists, is committed, and was demonstrably produced on `origin/main` —
  say in the pull request which commit it came from.

---

### T1 — The seat count is chosen, stored, read back, and keys Simulate's attempts

- **Owns:** `backend/app/db/models.py`, `backend/app/schemas/simulate.py`,
  `backend/app/api/v1/simulate.py`, `backend/alembic/versions/0016_sim_session_table_size.py` (new),
  `backend/app/services/sim_session.py`.
- **Depends on:** T2.
- **Imitate:** `mode`, end to end — `SimMode` at `backend/app/schemas/simulate.py:20-29`, the column
  on `SimSession`, the route passthrough at `backend/app/api/v1/simulate.py:76-81`, and migration
  `backend/alembic/versions/0015_sim_session_mode.py`.
- **Do:**
  1. `TableSize = Literal[6, 9]` beside `SimMode`; `CreateSessionRequest` gains
     `table_size: TableSize = 9`; `SessionView` carries it out.
  2. `SimSession` gains `table_size: int = Field(default=9)`.
  3. Migration `0016`: additive **nullable**, `server_default="9"`, no backfill, downgrade via
     `batch_alter_table`.
  4. **Fix all five hardcoded sites**, not three:
     - `:262` — `deal_hand(random.Random(seed))` must pass the seat count. **Silent if missed:** six
       seats would pop eighteen hole cards before the board, drawing it from a different deck offset.
     - `:358` — Challenge blind-check seat pool.
     - `:931` — **button seeding, `secrets.randbelow(9)`.** Out of range a third of the time at six
       seats, and the bad value persists onto the row and out over the wire.
     - `:947` — seat-row creation loop.
     - `:1532` — button rotation, `% 9`.
  5. **`_sim_signature` (`:1051-1058`) carries the seat count for non-nine sizes only** — 6-max
     keys `sim:6:RFI:LJ`, while nine-max keeps its original `sim:RFI:LJ` unchanged. This is
     decision D1, built where Simulate's key actually lives.
     **Do not touch `spot_signature()`** (`backend/app/domain/srs.py:63`) — it is frozen, and
     Simulate does not call it; `:1018` says so in a comment.
  6. Fix the "9-max" module docstring at `:1`.
- **Why only the new format is prefixed** (owner refinement, 2026-09-19): prefixing both would
  separate them just as well, but would split every 9-max key at the change date and break the
  continuity of a history the owner has been building since before 6-max existed. It would also
  force edits to four assertions in `backend/tests/test_grade_map_turn_river.py` that pin the old
  string — and no 9-max test may be edited. Asymmetry is the price, and it is the cheaper one.
- **Acceptance:** a session created with no table size is 9-max; one created with 6 stores and reads
  back 6; a pre-migration row reads back 9; `table_size=7` is rejected with a 422 by the schema, not
  by the engine with a crash; a 6-max session's button seeds inside 0–5 across many creations.
- **Done:** `alembic upgrade head`, `downgrade`, `upgrade` clean against a scratch database.

---

### T2 — The table deals and rotates for six seats

- **Owns:** `backend/app/domain/table/deck.py`, `backend/app/domain/table/engine.py`.
- **Depends on:** T0.
- **Do:**
  1. `_ROTATION` (`deck.py:16-29`) stays the frozen nine-long list and gains a six-long sibling
     **derived from it** by removing UTG, UTG1 and UTG2. Derive, do not retype — deriving preserves
     the 9-max worked example at `backend/tests/test_table.py:52-63`, and a typed list hides typos.
  2. `positions_for_button` and the dealing function take the seat count, **defaulting to 9.**
  3. Every `_SEATS` use in `engine.py` (`:81-82`, `:88`, `:122`, `:140`, `:243-245`, `:313-314`,
     `:363`, `:370`, `:372`) stops reading the module constant. Where a `HandState` is in scope,
     derive from `len(state.seats)`. **`start_hand` has none** — `:81-82`, `:88` and `:122` are
     inside it, so those derive from `len(stacks_bb)` or take the parameter.
- **Every new parameter defaults to 9.** Roughly 150 existing call sites pass no seat count, e.g.
  `test_table.py:53` calling `positions_for_button(0)` bare, and no 9-max test may be edited.
- **Watch for:** the wraparound. `% 9` → `% table_size` is the easy half; the hard half is
  `range(1, _SEATS + 1)` at `engine.py:313`, which walks to find the next actor.
- **Acceptance:** at six seats the button rotates through six seats only and wraps; blinds post to
  the right two seats at every button position; the round closes correctly when folds leave two
  players; `positions_for_button` at nine returns exactly today's answer for every button seat.

---

### T3 — Six seats get five bots, and the estimator counts them right

- **Owns:** `backend/app/domain/table/play.py`, `backend/app/domain/table/range_estimate.py`.
- **Depends on:** T0.
- **Do:**
  1. `LINEUP` (`play.py:44-61`) becomes two named tuples: the existing eight for nine seats, and for
     six seats **nit, TAG, TAG, LAG, calling station** (owner decision D2, 2026-09-18). No passive
     fish and no maniac sit at six seats. Two TAGs is deliberate — regulars are the most common seat
     at real 6-max. `assign_lineup` takes the seat count, defaulting to 9.
  2. **Which five is fixed; only their seating is shuffled.** A drawn roster would make the owner's
     first-session verdict a coin flip.
  3. `range_estimate.py` — the arrays at `:156-157` and `:192` and the opponent count at `:237` size
     themselves from the hand being estimated, not from `_SEATS` (`:58`).
- **Acceptance:** a 6-max session seats exactly those five; the villain-range panel reports
  opponents out of six; the nine-max lineup is unchanged.
- **Why the estimator matters:** left at nine, a 6-max hand counts three opponents never dealt in
  and every posterior is wrong **with no error raised.** Silent wrongness is the failure to test for.

---

### T4 — Grading learns the real table size, at five sites

- **Owns:** `backend/app/domain/table/grade_map_preflop.py`, `backend/app/domain/scenarios.py`,
  `backend/app/domain/table/grade_map_postflop.py`.
- **Depends on:** T0.
- **Do:**
  1. **`grade_map_preflop.py:63-70` — `_preflop_spot` passes the seat count into `build_spot`.**
     This is the single funnel for every Simulate preflop spot (called from `:99,128,158,192,227`)
     and it holds the `HandState`. Rev 1 omitted this file entirely, which would have made the whole
     ticket unreachable: `scenarios.py:275` is inside `build_spot`, which has no state of its own.
  2. `scenarios.py:275` takes the value from its caller.
  3. `grade_map_postflop.py:127,386,455,1708` — all four have a `HandState` in scope, so
     `len(state.seats)`.
- **Do NOT touch** `scenarios.py:442,520,611,692,770,856,946`. Those seven builders are reached only
  from `backend/app/api/v1/drill.py` — Practice and Quiz. Practice is the one surface that genuinely
  calls `spot_signature()` (`drill.py:334,446`), which genuinely hashes `table_size`, so **any value
  but nine reaching there orphans real spaced-repetition history.** `grade_map_postflop.py` mentions
  those builders only in comments (`:33-34,104,375,422,531`); its import pulls `_combos_for` and
  `_find_entry` and nothing else.
- **Do NOT touch** `spot_signature()`, or the canonical nine-position order at `scenarios.py:36-46`
  and `_nine_seats` at `:141-151`. The phantom folded seats at six are accepted: the lookup is
  position-keyed (`grade_map_preflop.py:96`) and never sees them.
- **Acceptance:** a 6-max spot reports `table_size=6`; a 9-max spot still reports 9; Practice spots
  still report 9; no existing 9-max grading test needs editing.

---

### T5 — Four rooms on the sit-down screen

- **Owns:** `frontend/src/api/client.ts`, `frontend/src/components/simulate/SimModeChoice.tsx`,
  `frontend/src/components/SimulateView.tsx`.
- **Depends on:** T1.
- **Do:** per owner decision D3, offer **Training 9-max, Training 6-max, Challenge 9-max, Challenge
  6-max**. `postSimulateSession` (`client.ts:108-116`) takes the table size alongside the mode;
  `SimModeChoice`'s `onChoose` carries both; `SimulateView.tsx:1466-1470` passes them through.
- **Keep the screen's existing rule that nothing is pre-selected.** That rule is argued for in the
  file's own header comment. Four equal cards preserve it; a defaulted toggle would not.
- **Why this ticket exists:** rev 1 had no control at all. The slice would have shipped green with
  6-max reachable only by hand-writing an HTTP request — and S1's own pass/fail is the owner playing
  a 6-max session.
- **Acceptance:** four rooms render; choosing "Training 6-max" starts a six-seat session; the 9-max
  rooms behave exactly as the two cards do today; `npm run typecheck` and `npm run lint` clean.

---

### T6 — The felt and the blind check stop claiming nine

- **Owns:** `frontend/src/components/simulate/SimTable.tsx`,
  `frontend/src/components/simulate/blindCheck.ts`,
  `frontend/src/components/simulate/SimBlindCheck.tsx`, `frontend/src/api/types.ts`.
- **Depends on:** T1.
- **Do:**
  1. `types.ts` gains `table_size` on the session view; correct its stale nine-seat claims at
     `:218`, `:221`, `:349` and `:585`. Types are hand-maintained; there is no generated file.
  2. `SimTable.tsx:147` reads the session's table size instead of the hardcoded "9-max".
  3. One static line on the 6-max felt says the ranges shown are 9-max ranges.
  4. **Per owner decision D4, `blindCheck.ts:40-56`'s `HOUSE_LINEUP` and `HOUSE_SEATS` become
     table-size aware**, and `SimBlindCheck.tsx:39-48,201-206` renders the roster actually seated.
     Today they are hand-copied 9-max constants shown as the card's fairness argument; at six seats
     the card would name eight seats including a maniac and two fish that are not there, and score
     the owner's guesses against that. The file's own comment warns about exactly this.
- **Do NOT** write any CSS, retune the ring, or touch `frontend/src/components/PokerTable.tsx`
  (Practice and Quiz keep their own ring and geometry at `:11,47`). `SimTable.tsx:139` already
  filters by what the backend sent, and `slotStyle(i, n)` at `:42-49` is called with
  `ordered.length` at `:188`, so six pods should render with no layout change. **If they do not,
  stop and report it** — that is a finding for P2's design review, not a licence to retune here.
- **Acceptance:** a 6-max session renders six pods and the strip says 6-max; a 6-max blind check
  discloses the five seated bots; a 9-max session is pixel-identical to before.

---

### T7 — Prove nine-max did not move, and that six-max works

- **Owns:** `backend/tests/test_simulate_6max.py` (new), any new frontend test file,
  `docs/ai-dlc/roadmap/phone-and-6max.md`, and the docstring sweep.
- **Depends on:** T1–T6.
- **Imitate:** `backend/tests/test_table.py` — its
  `test_positions_for_button_every_seat_valid_and_exactly_one_btn` pattern generalises straight to a
  6-max rotation test. Also `backend/tests/test_two_mode_simulate_gate.py`.
- **Do — each is a named test unless stated:**
  1. The full existing 9-max suite passes **with no test edited**.
  2. **The parity fixture from T0** is reproduced exactly by the new code.
  3. **The grade-equality test the roadmap named as this slice's cheapest test:** a set of 6-max
     hands grade *identically* to the equivalent 9-max hands — same hole cards, same position, same
     node, same frequency and EV. This is the slice's central bet.
  4. A 6-max session deals six hands, seeds the button inside 0–5, rotates through six seats only,
     posts blinds correctly at every button position.
  5. It seats exactly nit, TAG, TAG, LAG, calling station.
  6. Restore mid-hand at both sizes, **including a session row written before the migration**, which
     must read back as nine.
  7. A Challenge blind check names only seats that exist **and discloses the roster actually
     seated**.
  8. The villain-range estimator counts opponents out of six.
  9. **The D1 assertion, on `_sim_signature` — not on `spot_signature`.** The same hero hand at six
     and nine seats yields `sim:6:…` and `sim:9:…`. Asserting on `spot_signature` would pass today
     with no code changed and would prove nothing.
  10. A test documenting the limped-pot canonicalisation onto a nonexistent UTG seat
      (`scenarios.py:73,215`), named so it reads as a recorded gap, not a passing feature.
  11. **Amend the roadmap:** change S1's pass/fail "seats five **distinct** personas" to "seats five
      personas from a fixed roster", per owner decision D2. The spec and the roadmap must not
      disagree about an acceptance criterion.
  12. **Docstring sweep** of the nine-seat claims this change invalidates:
      `backend/app/db/models.py:68,79-81`, `backend/app/schemas/simulate.py:354`,
      `backend/app/services/sim_session.py:1455,1878`, `backend/app/domain/table/deck.py:1`,
      `backend/app/domain/table/engine.py:1,38,57,74`.
- **Acceptance:** `make check` green; every test above present and passing; no pre-existing test
  modified.
- **Done:** `make check` output in the pull request, and the tree contains nothing outside the files
  these eight tickets name.

---

## What would make this slice fail

- A nine-max test that needed editing — 9-max moved, and byte-identical was the promise.
- A `table_size` other than 9 reaching Practice's `spot_signature()`, orphaning real review history.
- The owner unable to start a 6-max session from the Simulate screen.
- A Challenge blind check disclosing a roster that is not at the table.
- The villain-range estimator counting phantom opponents — wrong numbers, no error.
