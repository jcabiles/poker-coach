# Contracts — 6-max table option (slice S1)

> Read-only scan, 2026-09-18, for `../roadmap/phone-and-6max.md` slice S1. Planned change: a
> Simulate session carries a table size of 6 or 9, chosen at session start and stored on the
> session row; every hardcoded 9 reads the seat count from the session instead. 6-max seats carry
> the six latest 9-max positions (LJ, HJ, CO, BTN, SB, BB). 9-max stays byte-identical.
>
> **Findings below are adjudicated, not raw.** Each carries a verdict: CONFIRMED (I reproduced it),
> NARROWED (real, but less severe than first reported), or UNVERIFIED (reported, not yet checked).

## Bottom line

The seat count is not one constant, it is roughly twenty-five. Three module-level `_SEATS = 9`
constants, a frozen nine-long position rotation, an eight-persona lineup hardcoded to seats 1
through 8, three `range(9)`/`% 9` sites in the session service, and about a dozen places that
construct a poker situation with the literal `table_size=9` baked in. Missing any one of them
produces a 6-max hand that misdeals, mis-grades, or crashes.

**The one that would be easy to miss and expensive to get wrong** is the last group: the grading
layer builds its own canonical nine-seat picture of a hand regardless of what the real table looks
like. If it keeps writing `table_size=9` for 6-max hands, then the spaced-repetition key — which
hashes the table size — makes a 6-max spot and a 9-max spot collide, and the two formats silently
pollute each other's review history. That is the opposite of what the owner decided in D1.

**The good news, checked rather than assumed:** grading verdicts themselves transfer correctly.
The lookup is keyed on the hero's position and the node type, not on how many players are at the
table, and the six 6-max positions are the six latest 9-max ones, so the number of players still
to act behind each is identical. The roadmap's central bet survives contact.

## 1. The seat-count blast radius

**Conclusion: about twenty-five sites across nine files, in four groups.** Grouped by what breaks.

**Group A — the module constants.** Each drives real arithmetic, not just array sizes.
- `backend/app/domain/table/engine.py:28` — and its uses at `:81-82` (blind seats), `:88` (seat
  construction), `:122` (first to act), `:140` (invested map), `:243-245` (betting round closure),
  `:313-314`, `:363`, `:370`, `:372`.
- `backend/app/domain/table/deck.py:16` — uses at `:55` (hole-card dealing) and `:66` (rotation).
- `backend/app/domain/table/range_estimate.py:58` — uses at `:156-157`, `:192`, `:237`.

**Group B — the session service.** `backend/app/services/sim_session.py:358` (Challenge-mode blind
check seat pool), `:947` (seat-row creation), `:1532` (button rotation, `% 9`). The file's own
docstring at `:1` still says "9-max".

**Group C — the bot lineup.** `backend/app/domain/table/play.py:44-61`. `LINEUP` is a fixed
eight-persona tuple and `assign_lineup` hardcodes seats 1 through 8.

**Group D — the literal `table_size=9`.** `backend/app/domain/scenarios.py:275,442,520,611,692,770,856,946`
and `backend/app/domain/table/grade_map_postflop.py:127,386,455,1708`. Twelve sites. None of them
reads the live session.

## 2. Position semantics

**Conclusion: the rotation must be sliced, not rewritten.** `deck.py:16-29` holds `_ROTATION`, a
frozen clockwise list starting at the button: BTN, SB, BB, UTG, UTG1, UTG2, LJ, HJ, CO.
`positions_for_button` returns `_ROTATION[(seat - button_seat) % _SEATS]`.

A 6-max rotation is BTN, SB, BB, LJ, HJ, CO — the same list with the three UTG entries removed,
preserving clockwise order. Deriving it that way keeps the 9-max worked example pinned by
`backend/tests/test_table.py:52-63` byte-identical, which rewriting from scratch would not.

**CONFIRMED — the grading layer enumerates all nine positions unconditionally.**
`backend/app/domain/scenarios.py:36-46` defines `_SEAT_ORDER` as all nine, and `_nine_seats`
(`:141-151`) builds one `PlayerState` per entry in it, always. At a 6-max table the canonical spot
would therefore contain UTG, UTG1 and UTG2 as phantom folded players who never had a seat.

## 3. Persistence and restore

**Conclusion: derive the seat count from the data you loaded, never from a module constant.**

- `backend/app/db/models.py:79-92` — `sim_hand` holds one current `state_json` blob, and it is
  **not versioned**. Nothing tags a stored hand with the table size it was dealt under.
- `backend/app/db/models.py:66-76` — `sim_seat` has a composite primary key and a comment saying
  "9 rows per session". `seat_index` has no bound enforced in code.
- Only the session row would carry the new table-size column. So every reader that loads seats or
  hand state must resolve the count from the parent session row, or from `len(state.seats)` of what
  it just loaded — never from `_SEATS`.
- Old 9-max rows stay safe as long as no code path hardcodes 9 while indexing a 6-seat state.

## 4. Grading reachability

**Conclusion: verdicts transfer; the canonical picture does not. NARROWED from the raw scan.**

The scan reported that grading a 6-max hand against 9-max content is a silent strategy-correctness
defect. **I checked this and it is overstated.** `backend/app/domain/table/grade_map_preflop.py:96`
looks up `_find_entry(NodeContext.RFI, hero.position, None)` — keyed on node type and hero
position, with no player count involved. And because the six 6-max seats are the six *latest*
9-max seats, the count of players still to act behind each is identical: LJ has HJ, CO, BTN, SB and
BB behind it at both table sizes. Opening-range width is governed by players-behind. The transfer
is sound, which is exactly the roadmap's stated bet.

**What is genuinely wrong is limped pots.** `backend/app/domain/scenarios.py:73` sets
`_LIMP_SEATS = [UTG, LJ, HJ, CO]` and `:215` slices `_LIMP_SEATS[:limper_count]`. At 6-max the
first limper canonicalises onto UTG, a seat that does not exist. The roadmap already names this as
a known soft spot; this scan confirms the mechanism and the line.

## 5. Villain range estimation

**Conclusion: fixed-length arrays sized by the constant, plus an opponent count that would include
phantoms.** `backend/app/domain/table/range_estimate.py:156-157` allocates `[0.0] * _SEATS`, `:192`
reallocates per street, and `:237` computes `opponents=sum(1 for j in range(_SEATS) if j != s and j
not in folded)`. Left at 9, a 6-max hand counts three opponents that were never dealt in, which
corrupts every posterior the estimator produces. Read by the villain-range endpoint.

## 6. Challenge mode

**Conclusion: only the pool needs fixing, the count is already fine.**
`backend/app/schemas/simulate.py:185` sets `BLIND_CHECK_SEAT_COUNT = 3`, independent of table size
and still valid at 6-max (three of five non-hero seats). Only the pool construction at
`backend/app/services/sim_session.py:358` — `[seat for seat in range(9) if seat != HERO_SEAT]` —
needs the table size threaded in.

## 7. The frontend contract

**Conclusion: more resilient than expected; the work is a label and a type, not a re-layout.**

- `frontend/src/components/simulate/SimTable.tsx:139` already filters the ring by whether the
  backend sent that position (`byPos.has(pos)`), and `:19-24` computes seat geometry from
  `ordered.length` rather than a fixed divisor. A backend that sends six seats should render six
  pods with no geometry change.
- `frontend/src/components/simulate/SimTable.tsx:147` hardcodes the string "9-max" in the context
  strip. That is a real change.
- **Practice and Quiz do not share this code.** `frontend/src/components/PokerTable.tsx:11,47` has
  its own separate ring and seat-geometry copy. They share only CSS classes (`.tablering`,
  `.tseat`, `.felt`, `.rail`), and those contain no `nth-child` seat-count assumptions. So a
  Simulate-side change should not bleed — but the shared-class hazard from
  `./simulate-table-size.md` still applies to any CSS edit.
- `frontend/src/api/types.ts:218,349` carry comments claiming all nine seats are present. Those go
  stale the moment the wire varies. Types are hand-maintained here; there is no generated file.

## 8. Test surface

**Conclusion: roughly 150 call sites assert 9-ness, concentrated in a handful of files.**
`backend/tests/test_engine.py`, `test_table.py`, `test_sim_session.py`, `test_range_estimate.py`,
`test_personas_postflop.py` (dozens), `test_grade_map*.py`, `test_detection_*.py`, plus the
standalone scripts in `backend/tools/` (`detection_corpus.py`, `sweep_runner.py`,
`late_street_probe.py`, `export_analytics.py`).

**Golden path to imitate for a new 6-vs-9 parity suite:** `backend/tests/test_table.py`. It is
small and direct, and its `test_positions_for_button_every_seat_valid_and_exactly_one_btn` pattern
— loop every button seat, assert set-equality of the positions produced — generalises straight to
a 6-max rotation test.

**Golden path for the migration:** `backend/alembic/versions/0015_sim_session_mode.py` — an
additive nullable column with a server default and no backfill, which is exactly the shape a
table-size column needs.

## Hazards ranked

1. **The literal `table_size=9` at twelve construction sites** (`scenarios.py:275,442,520,611,692,770,856,946`,
   `grade_map_postflop.py:127,386,455,1708`). If these are not threaded from the live session,
   `spot_signature()` (`backend/app/domain/srs.py:63`, which hashes the table size) gives a 6-max
   spot and a 9-max spot the same key, and the two formats silently merge their spaced-repetition
   history — directly contradicting owner decision D1. **CONFIRMED.**
2. **Phantom seats in the canonical spot** (`scenarios.py:36-46,141-151`). All nine positions are
   always constructed. **CONFIRMED** as a mechanism; **NARROWED** in effect — position-keyed
   lookups are unaffected (see §4), but anything counting players is not.
3. **`engine.py`'s `_SEATS`** driving blinds, rotation, betting closure and settlement
   (`:28,81-82,88,122,140,243-245,313-314,363,370,372`). A miss here is a misdeal, not a mis-grade.
4. **`deck.py`'s frozen `_ROTATION`** (`:16-29,66`). Must be sliced to preserve the 9-max worked
   example at `test_table.py:52-63`.
5. **`range_estimate.py`'s phantom opponents** (`:237`). Silent corruption of the villain-range
   posterior with no error raised.
6. **`play.py`'s eight-persona lineup on seats 1-8** (`:44-61`). Which five sit at 6-max is a
   product decision; the owner decided it on 2026-09-18 — nit, TAG, TAG, LAG, calling station.
7. **`sim_session.py`'s three hardcoded sites** (`:358`, `:947`, `:1532`).
8. **Limped pots canonicalising onto a nonexistent UTG** (`scenarios.py:73,215`). Known and named
   in the roadmap; confirmed here.
9. **Unversioned `state_json`** (`models.py:79-92`) with no table size stored on the hand or seat
   rows. Readers must resolve the count from the parent session.
10. **Stale frontend claims** — the "9-max" label at `SimTable.tsx:147` and the all-nine-seats
    comments at `types.ts:218,349`.
