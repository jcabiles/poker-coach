# Spec — S1, the 6-max table option

status: **rev 1, APPROVED (pre-authorized by John's `/ai-org:spec --auto-build` invocation, 2026-09-18)**
slice of: `../roadmap/phone-and-6max.md` (rev 4, NOW lane, slice S1)
contract map: `../contracts/simulate-6max.md`
finding ledger: `../ledger/phone-and-6max.md`

## Bottom line

Let the owner start a Simulate session at a six-seat table instead of a nine-seat one, and change
nothing else. The seat count is chosen when the session starts, stored on the session row, and read
from there by every piece of code that currently assumes nine. Nine-max play must come out
byte-identical, and a test proves it.

The work is wider than it sounds. The seat count is not one constant — it is about twenty-five
places across nine files, and the contract scan found that the grading layer builds its own
canonical nine-seat picture of every hand regardless of the real table. Getting that last part
wrong is the expensive failure: the spaced-repetition key hashes the table size, so a 6-max spot
that still reports nine seats collides with its 9-max twin and the two formats quietly merge their
review history. That is the exact opposite of what the owner decided.

**What is deliberately not in this slice:** any change to how the bots play, any new strategy
content, and any retuning of the felt's geometry. Six-max borrows the six latest nine-max
positions, which is sound because the number of players still to act behind each seat is identical
at both table sizes — that is the roadmap's bet, and the contract scan confirmed the grading lookup
is keyed on position, not on player count.

## Goal

One line: a Simulate session can be started at six seats, plays and grades correctly at every
6-max position, and leaves 9-max untouched.

## What the owner decided, and is not re-asked

- **D1 — 6-max spots are keyed `table_size=6`.** They start their own spaced-repetition history so
  the later research can tell the formats apart. Decided 2026-09-18.
- **D2 — the five bots at a 6-max table are fixed, not drawn.** Nit, TAG, TAG, LAG, calling
  station. Decided 2026-09-18 in this session's interview. A fixed lineup means the owner's
  first-session verdict is not a coin flip. No passive fish and no maniac sit at six seats.
- **No new strategy content.** The 6-max felt shows one static line saying the ranges are 9-max
  ranges. Per-format pack values are the NEXT-lane research, not this slice.

## Behaviour

### 1. Table size is chosen at session start and stored on the session

Imitate `mode` exactly — it is the same shape, shipped in the previous slice.

- `backend/app/schemas/simulate.py` gains `TableSize = Literal[6, 9]` beside the existing `SimMode`
  (`:20-29`), and `CreateSessionRequest` gains `table_size: TableSize = 9`. A literal union, never a
  bare `int`, so an invalid value is rejected at the edge.
- `backend/app/db/models.py` — `SimSession` gains `table_size: int = Field(default=9)`.
- A new Alembic migration `0016_sim_session_table_size.py`, imitating
  `backend/alembic/versions/0015_sim_session_mode.py` line for line: one additive **nullable**
  column with `server_default="9"`, no backfill, downgrade through `batch_alter_table` because
  SQLite cannot drop a column in place. Every pre-existing session must read back as nine.
- `backend/app/api/v1/simulate.py:76-81` passes it through to
  `sim_session.create_session(db, owner_id=..., mode=..., table_size=...)`.
- `SessionView` carries `table_size` out to the frontend so the felt can label itself.

**Readers must treat a NULL column as 9**, the same way `mode` treats NULL as `training`. Every
session created before this migration predates the column.

### 2. The seat count becomes a parameter of the pure domain

`backend/app/domain/` has no web and no database imports, and a test enforces it
(`backend/tests/test_domain_purity.py`). So the seat count is threaded as an argument. There is no
module-level context object and this slice does not introduce one.

- `backend/app/domain/table/deck.py` — `_ROTATION` stays the frozen nine-long clockwise list and
  gains a six-long sibling **derived from it by removing UTG, UTG1 and UTG2**, preserving clockwise
  order: BTN, SB, BB, LJ, HJ, CO. Deriving rather than retyping is what keeps the nine-max worked
  example at `backend/tests/test_table.py:52-63` byte-identical. `positions_for_button` and the
  dealing function take the seat count.
- `backend/app/domain/table/engine.py` — every use of `_SEATS` (`:81-82`, `:88`, `:122`, `:140`,
  `:243-245`, `:313-314`, `:363`, `:370`, `:372`) reads the count from the state it was handed.
  **Prefer `len(state.seats)` over a new parameter wherever the state is already in scope** — it
  cannot go stale and it makes restoring an old hand safe by construction.
- `backend/app/domain/table/range_estimate.py` — the fixed-length arrays (`:156-157`, `:192`) and
  the opponent count (`:237`) size themselves from the hand being estimated. Left at nine, a 6-max
  hand counts three opponents that were never dealt in and every posterior it produces is wrong,
  silently.
- `backend/app/domain/table/play.py:44-61` — `LINEUP` becomes two named tuples: the existing eight
  for nine seats, and the five from D2 for six seats. `assign_lineup` takes the seat count and
  shuffles the right one across the right number of non-hero seats. Seat 0 remains the hero.

### 3. The session service stops counting to nine

`backend/app/services/sim_session.py` has three hardcoded sites, and its module docstring at `:1`
still says "9-max".

- `:358` — the Challenge-mode blind-check seat pool, `[seat for seat in range(9) if seat != HERO_SEAT]`.
- `:947` — the seat-row creation loop.
- `:1532` — button rotation, `(session.button_seat + 1) % 9`.

`BLIND_CHECK_SEAT_COUNT` stays 3 (`backend/app/schemas/simulate.py:185`). Three of five non-hero
seats is still a sensible blind check at six seats, so only the pool changes. A blind check must
never name a seat that does not exist.

### 4. Grading learns the real table size

This is the part the contract scan flagged as the expensive one.

Twelve sites construct a poker situation with the literal `table_size=9` baked in:
`backend/app/domain/scenarios.py:275,442,520,611,692,770,856,946` and
`backend/app/domain/table/grade_map_postflop.py:127,386,455,1708`. None of them reads the live
session. Each must take the real seat count.

**Why it matters, concretely:** `spot_signature()` (`backend/app/domain/srs.py:63`) hashes
`str(spot.game.table_size)`. That function is frozen — changing how it hashes orphans every
existing review item, and this slice does not touch it. But passing it a truthful 6 instead of a
stale 9 is the whole point of decision D1. Leave these literals alone and a 6-max spot and a 9-max
spot at the same node and position produce the same key, and the formats merge.

**A test must prove D1 directly:** the same hero hand, at the same position and node, produces
*different* signatures at six and nine seats.

### 5. What stays canonical, on purpose

`backend/app/domain/scenarios.py:36-46` defines the canonical preflop order as all nine positions
and `_nine_seats` (`:141-151`) builds one player per entry, always. At six seats that means UTG,
UTG1 and UTG2 appear in the canonical spot as folded players who never had a seat.

**This slice leaves that alone,** and the reasoning is recorded here so nobody re-derives it:

- The grading lookup is keyed on node type and hero position, not on player count —
  `_find_entry(NodeContext.RFI, hero.position, None)` at
  `backend/app/domain/table/grade_map_preflop.py:96`. Phantom folded seats do not reach it.
- The six 6-max positions are the six *latest* 9-max positions, so players-behind is identical. LJ
  has HJ, CO, BTN, SB and BB behind it at both table sizes. Opening width is governed by
  players-behind, so the range transfers.
- Rewriting the canonical order is a change to code every 9-max hand also runs through. The
  byte-identical requirement makes that a bad trade for zero grading benefit.

**One known exception, deferred with evidence.** `backend/app/domain/scenarios.py:73` sets
`_LIMP_SEATS = [UTG, LJ, HJ, CO]` and `:215` slices it. At six seats the first limper canonicalises
onto UTG, which has no seat. The roadmap already names this as a known soft spot. This slice
**documents current behaviour in a test rather than changing it**, so that whoever picks up the
6-max research finds the shape of the problem instead of rediscovering it.

### 6. The felt shows six pods and says so

The frontend is more resilient than expected and this is a small change.

- `frontend/src/components/simulate/SimTable.tsx:139` already filters the ring by whether the
  backend sent that position, and `:19-24` computes seat geometry from the number of seats it was
  given rather than a fixed divisor. Six seats should render as six pods with **no geometry
  change**. If they do not, that is a finding for slice P2's design review, not a licence to retune
  the ring here.
- `frontend/src/components/simulate/SimTable.tsx:147` hardcodes "9-max" in the context strip. It
  reads the session's table size instead.
- One static line on the 6-max felt says the ranges shown are 9-max ranges.
- `frontend/src/api/types.ts` gains `table_size` on the session view, and its comments at `:218`
  and `:349` claiming all nine seats are present are corrected. Types here are hand-maintained;
  there is no generated file.
- **Practice and Quiz are untouched.** They use a separate ring and geometry copy at
  `frontend/src/components/PokerTable.tsx:11,47`. The two share only CSS classes, and those carry
  no seat-count assumptions. Any CSS edit at all is out of scope for this slice.

## Out of scope

No new ranges, bands or pack values. No 6-max-specific bot behaviour or persona retuning. No change
to `spot_signature()` itself. No felt geometry retuning — that is slice P2's design review. No
change to Practice or Quiz. No CSS changes. No new dependency. No touching the paused
persona-realism lane.

## Constraints

- `backend/app/domain/` has no web or DB imports — test-enforced by `backend/tests/test_domain_purity.py`.
- `spot_signature()` is frozen; changing its hashing orphans spaced-repetition history.
- Grading results are frequency and EV, never boolean.
- Grading stays behind the one async `StrategyProvider`.
- Strategy lives in versioned `content/` data, not code.
- Every schema change ships an Alembic migration.
- CSS values come from design tokens only — and this slice writes no CSS.
- Frontend API types are hand-maintained in `frontend/src/api/types.ts`.
- EVs stay labelled approximate.
- This repository is public.

## Golden-path files to imitate

| New thing | Imitate |
|---|---|
| The migration | `backend/alembic/versions/0015_sim_session_mode.py` |
| The request-schema literal union | `SimMode` in `backend/app/schemas/simulate.py:20-29` |
| The service signature | `create_session(..., mode=...)` in `backend/app/services/sim_session.py` |
| The route passthrough | `backend/app/api/v1/simulate.py:76-81` |
| The parity / rotation test | `backend/tests/test_table.py` — its every-button-seat set-equality pattern |
| The backend gate test | `backend/tests/test_two_mode_simulate_gate.py` |

## Verify-by

Ordered, and each step starts from the state it claims to test.

1. `make check` green — format, lint, types and tests, both halves.
2. The full existing 9-max suite passes **unchanged**, with no test edited to accommodate six seats.
3. A fixed seed at nine seats produces the identical deal, position map, button rotation and grades
   as before the change. This is the byte-identical claim; prove it, do not assert it.
4. A 6-max session deals six hands, seeds and rotates the button through six seats only, and posts
   blinds correctly.
5. It seats exactly five bots, and they are the five from D2.
6. Hero decisions grade at every 6-max position.
7. A session survives restore mid-hand, at both table sizes, including a session row written before
   the migration (which must read back as nine).
8. A Challenge-mode blind check names only seats that exist.
9. The villain-range panel counts live opponents out of six, not nine.
10. A signature assertion proves D1: the same hero hand at six and at nine seats produces different
    spaced-repetition keys.
11. A test documents the limped-pot canonicalisation onto a nonexistent UTG seat, so the deferral is
    visible rather than folklore.

## Definition of done

Done means every acceptance criterion above passes, `make check` exits clean, nothing outside the
files this spec names has changed, and any document this change invalidates is updated in the same
change. The roadmap's S1 box is **not** ticked by the build — the owner ticks it after playing.
