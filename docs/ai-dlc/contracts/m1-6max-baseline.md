# Contracts — M1, the 6-max baseline measurement (2026-09-26)

**Bottom line:** the game engine already deals 6-max correctly. The blocker is the bot-vs-bot
simulator, `backend/tools/export_analytics.py`, which assumes 9 seats in four places. Four
other tools treat "exactly nine seats" as a correctness rule, so 6-max output must never reach
them. The one guard for "9-max output is unchanged" is a pinned-hash test.

Source: one read-only `contract-mapper` scan (Sonnet), 2026-09-26, with the main session's own
reads of `export_session.py` and `export_analytics.py`. Line numbers are at `origin/main` `cd543fe`.

## 1. What already supports 6-max
- **Positions:** `backend/app/domain/table/deck.py:22-40,74-81` maps a button seat to positions
  for 6 or 9 seats. At 6-max the seats are BTN, SB, BB, LJ, HJ and CO; the three UTG seats are
  dropped.
- **Dealing:** `engine.py:80-83` `start_hand` takes its table size from `len(stacks_bb)`.
- **Lineup:** `play.py:60-66` `LINEUP_6MAX = (NIT, TAG, TAG, LAG, CALLING_STATION)`, shuffled
  across seats 1–5 by `assign_lineup` (`play.py:71-76`). Seat 0 is the hero and has no bot, so
  a TAG in the hero seat is new to M1.
- **One decision path:** `bot_decision` (`play.py:234`) is used both by the live table (through
  `advance_to_hero`) and by `export_analytics.py:250`. A simulation measures the same code you
  play against.

## 2. Where `export_analytics.py` assumes 9 seats
- `:100-108` `_draw_buyin_targets` returns `range(9)` targets.
- `:191` `play_one_hand` defaults stacks to `[STACKS_BB] * 9`.
- `:349` `run_export` builds `persona_by_seat` over `range(9)`.
- `:369` `run_export` rotates the button with `i % 9`.
- `:192` `play_one_hand` calls `deal_hand(random.Random(hand_seed))` with no table size, so it
  deals in 9-seat card order. The live table passes `len(seats)` (`sim_session.py:266`), and
  `deck.py:61-63` warns that a mismatched size draws the board from the wrong place. Found by
  the spec review.
- `:114` `DEFAULT_LINEUP` is the 9-max roster.
- The per-seat row loop iterates `state.seats`, so it already works at any size.

## 3. Consumers that require exactly 9 seats — 6-max output must never reach them
- `tools/derobo_gate.py:21,110-113` (the de-robotization gate) hard-fails on anything that is
  not nine seats; `tests/test_derobo_gate.py:127-132` pins that.
- `tools/sweep_runner.py:331-341` `resolve_lineup_dict` wraps every lineup to 9 seats; a 6-max
  batch would silently mismatch its identity check.
- `tools/capped_composition_probe.py` calls `play_one_hand` directly with 9 seats and `i % 9`.
- `tools/poker_events.odcs.yaml:117,128,144-147,251-264,311` is the data contract shared with
  the `poker-analytics` repo. It asserts "exactly 9 rows per hand" as data-quality SQL.
  `export_analytics.py:438-468` runs it as an advisory check.

## 4. The byte-identical guard for 9-max
- `tests/test_buyin_spread.py:347-358` `test_default_path_matches_pinned_golden_digests` hashes
  the default export's manifest and all three Parquet tables against four pinned SHA-256 values.
  `:120-124` pins the flat 100bb default. These must pass **unchanged**; editing a pinned value
  is a failure of M1, not a fix.

## 5. Existing stats code (the canon M1 reuses)
- `tools/export_session.py` (676 lines, **no tests**) reads real Simulate hands:
  - `Hand` (`:123-147`), built from a `SimHand` row plus its parsed `HandState`, although it only
    uses the row's `hand_no` and `id`;
  - `load` (`:150-197`), which skips rows that fail to parse and rows saved mid-hand;
  - `settle_hand` (`:200-206`), which uses the domain `settle()`;
  - `replay` (`:209-245`);
  - `stats_for` (`:323-411`).
- Definitions M1 inherits:
  - A hand counts for VPIP and PFR only when the seat made a real pre-flop decision.
  - "Saw the flop" uses the revealed board, never the full runout.
  - WTSD counts `settle()`'s `showdown_seats`, over hands where the seat saw the flop.
- No true c-bet stat exists: `flop_agg` counts any flop bet or raise.
- Opening by seat is counted only in total (`open_raise`), with no chance count by position.
- `app/services/stats.py` is the drill-stats service, and does not compute table stats.

## 6. Real hands for the fidelity check
- Session `4b35736fa8c7438eb57ca9d09874f8dc` in `backend/data/poker_coach.db`, read with `load()`.
- Seats: 0 = owner, 1 = nit, 2 = LAG, 3 = TAG, 4 = TAG, 5 = station.
- About 201 settled hands, so about 201 VPIP and PFR chances per bot. Flop c-bet chances run
  from 0 to 13 per bot.

## 7. Sourced ranges already in the repo
- `docs/ai-dlc/research/rfi-seat-provenance.md` sets the `(format, pool, source)` rule. Every
  figure is VERIFIED (fetched directly), DERIVED or UNVERIFIED, and UNVERIFIED figures never
  gate anything.
- Its T2 triple holds 6-max, 100bb, solver-derived opening rates by seat, from Preflop Wizard
  and GTO Gecko. The doc bars them from 9-max targets only; M1 may cite them for 6-max.
- No VPIP, PFR, c-bet or WTSD ranges by player type exist anywhere in the repo.
