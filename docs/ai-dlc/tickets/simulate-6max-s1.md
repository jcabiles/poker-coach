# Tickets — S1, the 6-max table option

status: **rev 1, APPROVED** — pre-authorized by John's `/ai-org:spec --auto-build` invocation,
2026-09-18. The approval covers T1–T6 exactly as written below and nothing else. The roadmap's S1
box is not ticked by this build; the owner ticks it after playing a 6-max session.
spec: `../specs/simulate-6max-s1.md` · contract map: `../contracts/simulate-6max.md` ·
roadmap: `../roadmap/phone-and-6max.md` (rev 4, NOW lane, slice S1)

## Shape of the work

Six tickets. One new database column, one new migration, a seat count threaded through the pure
domain, and a test suite whose main job is proving that nine-max play did not move.

```
T2 (deck + engine)      ─┐
T3 (range + lineup)     ─┼─→ T1 (persistence + service) ─→ T5 (frontend) ─┐
T4 (grading table_size) ─┘                                                 ├─→ T6 (tests)
                                                                           │
```

T2, T3 and T4 touch disjoint files and may run in parallel. T1 depends on T2 because the session
service calls the dealing and rotation functions whose signatures T2 changes. T6 runs last and is
the ticket that can actually fail the slice.

**Build in a worktree.** The shared checkout is in use by another session and the owner's dev stack
is running from it.

**Baseline first.** Record what `make check` reports before any edit, so "unchanged" has a number
behind it. Run it once, from the main checkout, because the Python interpreter lives there
(`backend/.venv`) and worktrees do not have one.

**The one rule that outranks the others:** nine-max play must come out byte-identical. If a change
makes a 9-max test need editing, the change is wrong — fix the change, not the test.

---

### T1 — The seat count is chosen, stored, and read back

- **Owns:** `backend/app/db/models.py`, `backend/app/schemas/simulate.py`,
  `backend/app/api/v1/simulate.py`, `backend/alembic/versions/0016_sim_session_table_size.py` (new),
  `backend/app/services/sim_session.py`.
- **Depends on:** T2.
- **Imitate:** `mode` from the previous slice, end to end. It is the same shape, already shipped —
  `SimMode` at `backend/app/schemas/simulate.py:20-29`, the column on `SimSession`, the route
  passthrough at `backend/app/api/v1/simulate.py:76-81`, and the migration
  `backend/alembic/versions/0015_sim_session_mode.py`.
- **Do:**
  1. `TableSize = Literal[6, 9]` beside `SimMode`. A literal union, never a bare `int`, so a bad
     value is rejected at the edge rather than deep in the engine.
  2. `CreateSessionRequest` gains `table_size: TableSize = 9`. `SessionView` carries `table_size`
     out, so the felt can label itself.
  3. `SimSession` gains `table_size: int = Field(default=9)`.
  4. Migration `0016`, additive **nullable** with `server_default="9"`, no backfill. Downgrade
     through `batch_alter_table` because SQLite cannot drop a column in place. **Readers treat NULL
     as 9** — every session created before this migration predates the column, exactly as `mode`
     treats NULL as `training`.
  5. Thread it through `create_session` and fix the three hardcoded sites in the service: the
     Challenge-mode blind-check seat pool at `:358`, the seat-row creation loop at `:947`, and the
     button rotation `(session.button_seat + 1) % 9` at `:1532`.
  6. `BLIND_CHECK_SEAT_COUNT` stays 3 (`backend/app/schemas/simulate.py:185`) — three of five
     non-hero seats is still a sensible check. Only the pool changes. **A blind check must never
     name a seat that does not exist.**
  7. The module docstring at `backend/app/services/sim_session.py:1` still says "9-max". Fix it.
- **Acceptance:** a session created with no `table_size` is a 9-max session; one created with
  `table_size=6` stores 6 and reads back 6; a row written before the migration reads back as 9;
  `table_size=7` is rejected by the schema with a 422, not by the engine with a crash.
- **Done:** `alembic upgrade head` then `downgrade` then `upgrade` runs clean against a scratch
  database — never against `backend/data/poker_coach.db`.

---

### T2 — The table deals and rotates for six seats

- **Owns:** `backend/app/domain/table/deck.py`, `backend/app/domain/table/engine.py`.
- **Imitate:** the files' own style. Pure domain — no web imports, no DB imports, enforced by
  `backend/tests/test_domain_purity.py`.
- **Do:**
  1. `_ROTATION` (`deck.py:16-29`) stays the frozen nine-long clockwise list and gains a six-long
     sibling **derived from it by removing UTG, UTG1 and UTG2**. Do not retype the six by hand:
     deriving is what keeps the nine-max worked example at `backend/tests/test_table.py:52-63`
     byte-identical, and a typed list is a place for a typo to hide.
  2. `positions_for_button` and the dealing function take the seat count.
  3. Every use of `_SEATS` in `engine.py` reads the count from the state it was handed —
     `:81-82` (blind seats), `:88` (seat construction), `:122` (first to act), `:140` (invested
     map), `:243-245` (betting-round closure), `:313-314`, `:363`, `:370`, `:372`.
  4. **Prefer `len(state.seats)` over a new parameter wherever the state is already in scope.** It
     cannot go stale, and it makes restoring a hand dealt under the other table size safe by
     construction.
- **Acceptance:** at six seats the button rotates through six seats only and wraps correctly; blinds
  post to the right two seats at every button position; the betting round closes correctly when
  folds leave two players; `positions_for_button` at nine seats returns exactly what it returns
  today, for every button seat.
- **Watch for:** the wraparound. `% 9` becoming `% table_size` is the easy half; the hard half is
  any loop that counts `range(1, _SEATS + 1)` (`engine.py:313`) to find the next actor.

---

### T3 — Six seats get five bots, and the villain-range estimator counts them correctly

- **Owns:** `backend/app/domain/table/play.py`, `backend/app/domain/table/range_estimate.py`.
- **Do:**
  1. `LINEUP` (`play.py:44-61`) becomes two named tuples: the existing eight personas for nine
     seats, and **for six seats the five the owner fixed on 2026-09-18 — nit, TAG, TAG, LAG,
     calling station.** No passive fish and no maniac sit at a six-seat table. `assign_lineup`
     takes the seat count and shuffles the right tuple across the right number of non-hero seats.
     Seat 0 stays the hero.
  2. The lineup is **fixed, not drawn** — which five personas appear is decided, so the owner's
     first-session verdict is not a coin flip. Shuffling *positions* is still correct; changing
     *which five* is not.
  3. `range_estimate.py` — the fixed-length arrays at `:156-157` and `:192`, and the opponent count
     at `:237`, size themselves from the hand being estimated rather than from `_SEATS` (`:58`).
- **Acceptance:** a 6-max session seats exactly five bots and they are exactly the five above; the
  villain-range panel reports opponents out of six, never nine; the nine-max lineup is unchanged.
- **Why the estimator matters:** left at nine, a 6-max hand counts three opponents that were never
  dealt in, and every posterior it produces is wrong **with no error raised**. Silent wrongness is
  the failure mode to test for.

---

### T4 — Grading learns the real table size

- **Owns:** `backend/app/domain/scenarios.py`, `backend/app/domain/table/grade_map_postflop.py`.
- **Do:** thread the real seat count into the twelve sites that bake in the literal `table_size=9`
  — `scenarios.py:275,442,520,611,692,770,856,946` and
  `grade_map_postflop.py:127,386,455,1708`.
- **Do NOT:** change `spot_signature()` (`backend/app/domain/srs.py:63`). It is frozen; changing how
  it hashes orphans every existing spaced-repetition item. Passing it a truthful 6 is the whole
  point. Changing the function is a different, forbidden thing.
- **Do NOT:** rewrite the canonical nine-position order at `scenarios.py:36-46` or `_nine_seats`
  at `:141-151`. At six seats those leave UTG, UTG1 and UTG2 in the canonical spot as folded
  phantoms, and **that is accepted on purpose** — the grading lookup is keyed on node type and hero
  position (`grade_map_preflop.py:96`), not on player count, so the phantoms never reach it.
  Rewriting it would change code every 9-max hand also runs through, for zero grading benefit.
- **Acceptance:** a 6-max spot reports `table_size=6`; a 9-max spot still reports 9; no existing
  9-max grading test needs editing.
- **Why this is the expensive one to get wrong:** `spot_signature()` hashes the table size. Leave
  these literals alone and a 6-max spot and its 9-max twin produce the same spaced-repetition key,
  and the two formats silently merge their review history — the opposite of owner decision D1.

---

### T5 — The felt shows six pods and says which game it is

- **Owns:** `frontend/src/components/simulate/SimTable.tsx`, `frontend/src/api/types.ts`.
- **Depends on:** T1 (the wire field must exist first).
- **Do:**
  1. `types.ts` gains `table_size` on the session view. Types here are **hand-maintained** — edit
     the file; there is no generated one. Correct the stale comments at `:218` and `:349` claiming
     all nine seats are present.
  2. `SimTable.tsx:147` hardcodes "9-max" in the context strip. Read the session's table size.
  3. Add one static line on the 6-max felt saying the ranges shown are 9-max ranges.
- **Do NOT:** write any CSS, retune the ring geometry, or touch
  `frontend/src/components/PokerTable.tsx` (Practice and Quiz use their own ring and geometry copy
  at `:11,47`). `SimTable.tsx:139` already filters the ring by what the backend sent and `:19-24`
  computes geometry from the number of seats given, so six pods should render with no layout
  change. **If they do not, stop and report it** — that is a finding for slice P2's design review,
  not a licence to retune the felt here.
- **Acceptance:** a 6-max session renders six pods and the strip says 6-max; a 9-max session is
  pixel-identical to before; Practice and Quiz are untouched; `npm run typecheck` and
  `npm run lint` clean.

---

### T6 — Prove nine-max did not move, and that six-max works

- **Owns:** `backend/tests/test_simulate_6max.py` (new), and any new frontend test file.
- **Depends on:** T1, T2, T3, T4, T5.
- **Imitate:** `backend/tests/test_table.py` — small and direct, and its
  `test_positions_for_button_every_seat_valid_and_exactly_one_btn` pattern (loop every button seat,
  assert set-equality of the positions produced) generalises straight to a 6-max rotation test.
  Also `backend/tests/test_two_mode_simulate_gate.py` for the shape of a slice gate test.
- **Do — each of these is a named test:**
  1. **The byte-identical claim.** A fixed seed at nine seats produces the identical deal, position
     map, button rotation and grades as before the change. Prove it; do not assert it.
  2. The full existing nine-max suite passes **with no test edited**.
  3. A 6-max session deals six hands, rotates the button through six seats only, posts blinds
     correctly.
  4. It seats exactly five bots, and they are nit, TAG, TAG, LAG and calling station.
  5. Hero decisions grade at every 6-max position.
  6. Restore mid-hand works at both table sizes, **including a session row written before the
     migration**, which must read back as nine.
  7. A Challenge-mode blind check names only seats that exist.
  8. The villain-range estimator counts opponents out of six.
  9. **The D1 assertion:** the same hero hand at six and at nine seats produces *different*
     spaced-repetition signatures.
  10. **The deferral, documented as a test:** at six seats a limped pot canonicalises its first
      limper onto UTG, a seat that does not exist (`scenarios.py:73,215`). Write a test that
      records current behaviour, named so it is obviously a documented gap and not a passing
      feature. Whoever picks up the 6-max research should find the shape of the problem rather than
      rediscover it.
- **Acceptance:** `make check` green; every test above present and passing; no pre-existing test
  modified.
- **Done:** `make check` output pasted into the pull request, and the working tree contains nothing
  outside the files these six tickets name.

---

## What would make this slice fail

Stated plainly so the build knows what it is defending:

- A nine-max test that needed editing. That means 9-max moved, and byte-identical was the promise.
- A 6-max spot that still reports `table_size=9`. That silently merges two formats' review history
  and is invisible until months of spaced repetition are already polluted.
- A blind check naming a seat that does not exist.
- The villain-range estimator counting phantom opponents — wrong numbers, no error.
