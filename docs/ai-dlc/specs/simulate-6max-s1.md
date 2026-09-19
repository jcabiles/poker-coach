# Spec — S1, the 6-max table option

status: **rev 2, APPROVED** — rev 1 was pre-authorized by John's `/ai-org:spec --auto-build`
invocation, 2026-09-18; rev 2 folds in a blind review that returned FAIL and four owner rulings
taken the same day.
slice of: `../roadmap/phone-and-6max.md` (NOW lane, slice S1)
contract map: `../contracts/simulate-6max.md`
finding ledger: `../ledger/simulate-6max-s1.md` (round 1)

## Bottom line

Let the owner start a Simulate session at a six-seat table instead of a nine-seat one, and change
nothing else. The seat count is chosen on the sit-down screen, stored on the session row, and read
from there by every piece of code that currently assumes nine. Nine-max play must come out
byte-identical, and a captured fixture proves it.

**Rev 2 exists because a blind reviewer found rev 1's headline argument was false.** Rev 1 said the
expensive hazard was twelve places baking in `table_size=9`, because the spaced-repetition key
hashes that value. It does — but **Simulate never calls that function.** Simulate keys its own
attempts with `_sim_signature` (`backend/app/services/sim_session.py:1051-1058`), whose parts are
node type, hero position and what the hero faces. No table size. Its docstring says the omission is
deliberate: *"sim rows never enter SRS."* So rev 1's central edit would have produced no observable
difference anywhere.

The owner ruled on 2026-09-18 that the separation is worth having and should be built where it
actually lives: **the seat count goes into `_sim_signature`.**

Rev 2 also shrinks the slice in one place and widens it in three. It shrinks because seven of those
twelve sites turned out to serve Practice and Quiz only, where the key genuinely is
spaced-repetition and must stay at nine. It widens because rev 1 had no way for the owner to
*choose* six seats, missed the button-seeding site, and would have shipped a Challenge screen that
states a false roster.

## Goal

One line: the owner can sit down at a six-seat table from the Simulate screen, play and be graded
correctly at every 6-max position, and nine-max is untouched.

## Owner decisions — settled 2026-09-18, not to be re-asked

- **D1, corrected.** 6-max and 9-max Simulate attempts are separated by putting the seat count in
  `_sim_signature`: `sim:9:rfi:LJ` and `sim:6:rfi:LJ`. Existing rows keep their old `sim:rfi:LJ`
  key forever, so there is **one seam in the history at today's date**, accepted knowingly.
- **D2.** The five bots at a 6-max table are fixed, not drawn: **nit, TAG, TAG, LAG, calling
  station.** Two TAGs is deliberate — regulars are the most common seat at real 6-max. The
  roadmap's "five *distinct* personas" wording is amended in this change to "five personas from a
  fixed roster", because the spec and the roadmap must not disagree about an acceptance criterion.
- **D3.** The table size is chosen on the sit-down screen as **four cards**: Training 9-max,
  Training 6-max, Challenge 9-max, Challenge 6-max. This keeps that screen's existing rule that
  nothing is pre-selected.
- **D4.** The Challenge blind check's disclosed roster becomes table-size aware, so a 6-max check
  names the five bots actually seated.
- **No new strategy content.** The 6-max felt carries one static line saying the ranges shown are
  9-max ranges. Per-format pack values are the NEXT-lane research.

## Behaviour

### 1. Table size is chosen at session start and stored on the session

Imitate `mode` exactly — the same shape shipped in the previous slice.

- `backend/app/schemas/simulate.py` gains `TableSize = Literal[6, 9]` beside `SimMode` (`:20-29`),
  and `CreateSessionRequest` gains `table_size: TableSize = 9`. A literal union, never a bare `int`,
  so a bad value is rejected at the edge with a 422 rather than deep in the engine.
- `backend/app/db/models.py` — `SimSession` gains `table_size: int = Field(default=9)`.
- A new migration `0016_sim_session_table_size.py`, imitating
  `backend/alembic/versions/0015_sim_session_mode.py`: one additive **nullable** column with
  `server_default="9"`, no backfill, downgrade through `batch_alter_table` because SQLite cannot
  drop a column in place. Pre-existing sessions read back as nine.
- `backend/app/api/v1/simulate.py:76-81` passes it to `create_session`.
- `SessionView` carries `table_size` out to the frontend.

### 2. The seat count becomes a parameter of the pure domain — defaulting to nine

`backend/app/domain/` has no web and no database imports, and a test enforces it. So the seat count
is threaded as an argument; there is no module-level context object.

**Every new domain parameter defaults to 9.** This is not a style preference: the contract scan
counted roughly 150 existing call sites that pass no seat count, including
`backend/tests/test_table.py:53` calling `positions_for_button(0)` bare. A required parameter would
break all of them, and this slice's second acceptance criterion forbids editing a single 9-max
test. The cost of the default is that a missed call site fails silently rather than loudly, which
is why §7's call-site list is exhaustive and why the parity fixture exists.

- `backend/app/domain/table/deck.py` — `_ROTATION` stays the frozen nine-long clockwise list and
  gains a six-long sibling **derived from it by removing UTG, UTG1 and UTG2**, preserving clockwise
  order: BTN, SB, BB, LJ, HJ, CO. Derive it; do not retype it. Deriving is what keeps the nine-max
  worked example at `backend/tests/test_table.py:52-63` byte-identical, and a hand-typed list is
  where a typo hides.
- `backend/app/domain/table/engine.py` — every use of `_SEATS` (`:81-82`, `:88`, `:122`, `:140`,
  `:243-245`, `:313-314`, `:363`, `:370`, `:372`) stops reading the module constant.
  **Where a `HandState` is in scope, derive from `len(state.seats)`** — it cannot go stale and
  makes restoring a hand dealt under the other size safe by construction. **`start_hand` has no
  `HandState`** (`:81-82`, `:88`, `:122` are inside it), so those derive from `len(stacks_bb)` or
  take the parameter. Rev 1 said all of them read from state; that was wrong.
- `backend/app/domain/table/range_estimate.py` — the arrays at `:156-157` and `:192` and the
  opponent count at `:237` size themselves from the hand being estimated, not from `_SEATS`
  (`:58`).
- `backend/app/domain/table/play.py:44-61` — `LINEUP` becomes two named tuples: the existing eight
  for nine seats, and the five from D2 for six. `assign_lineup` takes the seat count. Seat 0 stays
  the hero. **Which five is fixed; only their seating is shuffled.**

### 3. The session service stops counting to nine — four sites, not three

`backend/app/services/sim_session.py`:

- `:262` — `deal_hand(random.Random(seed))` must pass the seat count. **Missing this one is silent:**
  a six-seat table would pop eighteen hole cards before the board, drawing it from a different deck
  offset than a true 6-max deal. No crash, no wrong play, no test failure.
- `:358` — the Challenge blind-check seat pool, `[seat for seat in range(9) if seat != HERO_SEAT]`.
- `:931` — **button seeding, `button_seat=secrets.randbelow(9)`.** Rev 1 missed this and the
  contract map missed it too, though the roadmap named it. At six seats it lands out of range about
  a third of the time, and the bad value persists onto the session row and out over the wire.
- `:947` — the seat-row creation loop.
- `:1532` — button rotation, `(session.button_seat + 1) % 9`.

`BLIND_CHECK_SEAT_COUNT` stays 3 (`backend/app/schemas/simulate.py:185`) — three of five non-hero
seats is still a sensible check. A blind check must never name a seat that does not exist.

The module docstring at `:1` still says "9-max". Fix it.

### 4. Simulate's own attempt key learns the table size

**This is D1, built where it actually lives.**

`_sim_signature` (`backend/app/services/sim_session.py:1051-1058`) gains the seat count as its
second part, so a 6-max LJ open keys `sim:6:rfi:LJ` and its 9-max twin keys `sim:9:rfi:LJ`.

- **`spot_signature()` (`backend/app/domain/srs.py:63`) is not touched.** It is frozen; changing how
  it hashes orphans every Practice review item. It is also irrelevant here — Simulate does not call
  it, and `backend/app/services/sim_session.py:1018` says so in a comment.
- **Accepted cost, stated because the owner accepted it knowingly:** rows written before this change
  keep `sim:rfi:LJ`. Queries that group sim attempts by signature see a seam at this date. Nothing
  is lost; older rows simply do not distinguish the formats, because they could not.

### 5. Grading learns the real table size — five sites, not twelve

Rev 1 listed twelve. Seven of them were wrong to include.

**In scope, because Simulate reaches them:**
- `backend/app/domain/table/grade_map_preflop.py:63-70` — `_preflop_spot`, the single funnel through
  which every Simulate preflop spot is built, called from `:99`, `:128`, `:158`, `:192` and `:227`.
  It has the `HandState`; it must pass the seat count into `build_spot`. **Rev 1 never named this
  file, which would have made the whole of §5 unreachable** — `scenarios.py:275` sits inside
  `build_spot`, which has no state of its own, so the value can only arrive from here.
- `backend/app/domain/scenarios.py:275` — inside `build_spot`, reached from `_preflop_spot`.
- `backend/app/domain/table/grade_map_postflop.py:127,386,455,1708` — all four have a `HandState` in
  scope, so `len(state.seats)` works directly.

**Explicitly out of scope, and why:** `scenarios.py:442,520,611,692,770,856,946` sit inside
`build_cbet_spot`, `build_vs_cbet_spot`, `build_check_raise_spot`, `build_turn_barrel_spot`,
`build_vs_turn_bet_spot`, `build_river_barrel_spot` and `build_vs_river_bet_spot`. Every caller of
those is `backend/app/api/v1/drill.py` — Practice and Quiz. `grade_map_postflop.py` only mentions
them in comments; its import line pulls `_combos_for` and `_find_entry` and nothing else. Practice
is the one surface that genuinely calls `spot_signature()` (`drill.py:334,446`), which genuinely
hashes `table_size`, so **any value but nine reaching there orphans real review history.** They stay
at nine. Touching them would also contradict this spec's own out-of-scope line.

### 6. What stays canonical, on purpose

`backend/app/domain/scenarios.py:36-46` defines the canonical preflop order as all nine positions,
and `_nine_seats` (`:141-151`) builds one player per entry, always. At six seats UTG, UTG1 and UTG2
appear as folded phantoms who never had a seat.

**This slice leaves that alone.** The reasoning, recorded so nobody re-derives it:

- The grading lookup keys on node type and hero position — `_find_entry(NodeContext.RFI,
  hero.position, None)` at `backend/app/domain/table/grade_map_preflop.py:96`. Phantom folded seats
  never reach it.
- The six 6-max positions are the six *latest* 9-max positions, so players-behind is identical: LJ
  has HJ, CO, BTN, SB and BB behind it at both sizes. Opening width is governed by players-behind.
- Rewriting the canonical order changes code every 9-max hand also runs through, for no grading
  benefit.

**One known exception, deferred with evidence.** `scenarios.py:73` sets
`_LIMP_SEATS = [UTG, LJ, HJ, CO]` and `:215` slices it, so at six seats the first limper
canonicalises onto UTG, which has no seat. §8 records this as a test rather than fixing it.

### 7. The sit-down screen offers four rooms

Per D3. Rev 1 had no control at all, which would have shipped a 6-max engine the owner could only
reach with a hand-written HTTP request.

- `frontend/src/api/client.ts:108-116` — `postSimulateSession` takes the table size alongside the
  mode.
- `frontend/src/components/simulate/SimModeChoice.tsx` — four cards: Training 9-max, Training 6-max,
  Challenge 9-max, Challenge 6-max. Its `onChoose` carries both values. **Keep the screen's existing
  rule that nothing is pre-selected** — that rule is argued for in the file's own header comment,
  and four equal cards preserve it where a defaulted toggle would not.
- `frontend/src/components/SimulateView.tsx:1466-1470` — passes both through.

### 8. The felt and the blind check stop claiming nine

- `frontend/src/components/simulate/SimTable.tsx:147` hardcodes "9-max" in the context strip. Read
  the session's table size. The ring itself needs no change: `:139` already filters by what the
  backend sent, and `slotStyle(i, n)` at `:42-49` is called with `ordered.length` at `:188` — rev 1
  cited `:19-24` for this, which is the constant and a comment, not the geometry.
- One static line on the 6-max felt says the ranges shown are 9-max ranges.
- **`frontend/src/components/simulate/blindCheck.ts:40-56` and
  `frontend/src/components/simulate/SimBlindCheck.tsx:39-48,201-206`** — per D4, the disclosed
  `HOUSE_LINEUP` and `HOUSE_SEATS` become table-size aware. Today they are hand-copied 9-max
  constants rendered as the card's fairness argument; at six seats the card would name eight seats
  including a maniac and two fish that are not there, and score the owner's guesses against that.
  The file's own comment warns about exactly this.
- `frontend/src/api/types.ts` gains `table_size`, and its stale nine-seat claims at `:218`, `:221`,
  `:349` and `:585` are corrected. Types are hand-maintained; there is no generated file.
- **Practice and Quiz are untouched.** They use a separate ring and geometry copy at
  `frontend/src/components/PokerTable.tsx:11,47`, sharing only CSS classes, which carry no
  seat-count assumptions. **This slice writes no CSS.**
- A docstring sweep: `backend/app/db/models.py:68,79-81`, `backend/app/schemas/simulate.py:354`,
  `backend/app/services/sim_session.py:1,1455,1878`, `backend/app/domain/table/deck.py:1`,
  `backend/app/domain/table/engine.py:1,38,57,74`. A change that invalidates a doc updates it in the
  same change, and this repo already has one stale docstring that cost a session.

## Out of scope

No new ranges, bands or pack values. No 6-max-specific bot behaviour. No change to
`spot_signature()` or to the seven Practice-only spot builders. No felt geometry retuning — that is
P2's design review. No CSS. No new dependency. No change to Practice or Quiz. No touching the paused
persona-realism lane.

## Constraints

- `backend/app/domain/` has no web or DB imports — enforced by `backend/tests/test_domain_purity.py`.
- `spot_signature()` is frozen.
- Grading results are frequency and EV, never boolean.
- Grading stays behind the one async `StrategyProvider`.
- Strategy lives in versioned `content/` data.
- Every schema change ships an Alembic migration.
- CSS values come from design tokens only — and this slice writes none.
- Frontend API types are hand-maintained.
- EVs stay labelled approximate.
- This repository is public.

## Golden-path files to imitate

| New thing | Imitate |
|---|---|
| The migration | `backend/alembic/versions/0015_sim_session_mode.py` |
| The request-schema literal union | `SimMode`, `backend/app/schemas/simulate.py:20-29` |
| The service signature | `create_session(..., mode=...)` |
| The route passthrough | `backend/app/api/v1/simulate.py:76-81` |
| The rotation / parity test | `backend/tests/test_table.py` |
| The slice gate test | `backend/tests/test_two_mode_simulate_gate.py` |
| The sit-down card | the existing `ROOMS` entries in `SimModeChoice.tsx` |

## Verify-by

1. `make check` green — format, lint, types, tests, both halves.
2. The full existing 9-max suite passes **with no test edited**. A 9-max test that needed editing
   means 9-max moved, and the change is wrong — fix the change, not the test.
3. **The byte-identical fixture.** Before the branch does anything else, run a fixed seed on
   `origin/main` and commit the captured deal, position map, button rotation and grades as a
   fixture file. Then assert the new code reproduces it. Rev 1 said "identical as before the
   change" with no mechanism, which a test written afterwards would satisfy by comparing the new
   code to itself.
4. **The equality test the roadmap named as this slice's cheapest test:** a set of 6-max hands grade
   identically to the equivalent 9-max hands — same hole cards, same position, same node, same
   frequency and EV. This is the slice's central bet; rev 1 weakened it to "a grade exists".
5. A 6-max session deals six hands, seeds the button inside 0–5, rotates through six seats only, and
   posts blinds correctly at every button position.
6. It seats exactly five bots: nit, TAG, TAG, LAG, calling station.
7. Restore mid-hand works at both sizes, including a session row written before the migration, which
   reads back as nine.
8. A Challenge blind check names only seats that exist **and discloses the roster actually seated**.
9. The villain-range estimator counts opponents out of six.
10. **The D1 assertion:** the same hero hand at six and nine seats produces different
    `_sim_signature` values — `sim:6:…` and `sim:9:…`. This must assert on `_sim_signature`, not on
    `spot_signature`, which already differs and would pass with no code changed.
11. From the Simulate screen, four rooms are offered and choosing "Training 6-max" starts a six-seat
    session.
12. A test documents the limped-pot canonicalisation onto a nonexistent UTG seat, named so it reads
    as a recorded gap rather than a passing feature.

## Definition of done

Every criterion above passes, `make check` exits clean, nothing outside the files this spec names
has changed, and any document this change invalidates is updated in the same change — including the
roadmap's "five distinct personas" line, amended per D2. The roadmap's S1 box is **not** ticked by
the build; the owner ticks it after playing.
