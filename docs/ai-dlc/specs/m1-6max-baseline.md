# Spec — M1, measure the 6-max baseline (rev 1, 2026-09-26)

**Bottom line:**
- **What gets built:** a script that plays 6,000 simulated 6-max hands with the same bots you
  play against, and measures how each bot plays.
- **What comes out:** a report that sets each bot's stats against cited real 6-max ranges, and
  checks that the simulation matches your 200 real hands.
- **What does not change:** any bot, any settings file, or any 9-max output.
- **If the check fails,** M1 stops and reports, and no tuning starts.

- **Roadmap:** `../roadmap/bot-realism-6max.md`, slice M1. M1 feeds the roadmap's stats check
  and tests its riskiest assumption: that simulated bot-vs-bot hands reproduce what the owner
  sees at the table.
- **Contracts:** `../contracts/m1-6max-baseline.md`.
- **Owner decisions (2026-09-26, do not re-ask):**
  - Build on the existing simulator; do not drive the live Simulate service, and do not write a
    second simulator.
  - The fidelity check runs on the 10 pre-flop comparisons that qualify. C-bet is reported, but
    labelled as never tested against real play.

## 1. What changes

| File | Change |
|---|---|
| `backend/tools/export_analytics.py` | `play_one_hand` and `_draw_buyin_targets` work at any table size, and `play_one_hand` also returns the final `HandState` under the key `"state"`. The default call is unchanged. `run_export` is **not** changed. |
| `backend/tools/table_stats.py` (new) | New home for `Hand`, `load`, `settle_hand`, `replay` and `stats_for`, moved from `export_session.py` without changing behaviour. It gains opening rate by seat and flop c-bet, plus a Wilson 95% interval helper. |
| `backend/tools/export_session.py` | Imports those names from `table_stats.py` instead of defining them. The printed output is unchanged. |
| `backend/tools/sixmax_baseline.py` (new) | Runs the 6-max simulation, loads your session, computes both sides through `table_stats`, runs the fidelity check, and prints Markdown tables. |
| `backend/tests/test_table_stats.py`, `backend/tests/test_sixmax_baseline.py` (new) | Tests. |
| `docs/ai-dlc/research/bot-realism-6max/m1-baseline.md` (new) | The report. |
| `docs/ai-dlc/roadmap/bot-realism-6max.md` | Tick M1 only if it passes. Record the assumption's status either way. |

## 2. Rules and the one module that owns each

- **Every stat definition lives in `tools/table_stats.py` and nowhere else.** Real and simulated
  hands both go through `Hand` → `replay` → `settle_hand` → `stats_for`, so both sides use one
  definition. `export_session.py` keeps no copy.
- **Definitions,** each counted per seat per hand:
  - **VPIP / PFR** — unchanged from `stats_for` today. The chance is a hand where the seat made
    a real pre-flop decision. VPIP means it called or raised; PFR means it raised.
  - **Opening rate by seat (RFI, "raise first in")** — the chance is a hand where every earlier
    pre-flop decision was a fold and the seat is not the BB. An open means the seat's first
    action is a raise. Limps are counted separately and are not opens. This is reported for
    LJ, HJ, CO, BTN and SB.
  - **Flop c-bet** — the chance is a hand where the seat made the last pre-flop raise, saw the
    flop, and nobody bet on the flop before its first flop action. A c-bet means that first
    action is a bet. Heads-up and multiway pots are pooled.
  - **WTSD** — unchanged: showdown count over hands where the seat saw the flop, using
    `settle()`'s `showdown_seats` and the revealed board.
  - **95% interval** — the Wilson score interval, stdlib only.
- **The 6-max simulation** is owned by `tools/sixmax_baseline.py`:
  - **Seats:** 0 = TAG (the stand-in for the owner), 1 = NIT, 2 = LAG, 3 = TAG, 4 = TAG,
    5 = CALLING_STATION. This is the same seat map as session `4b35736f`.
  - **Button:** rotates `i % 6`.
  - **Hands:** 6,000 by default, a multiple of 6 so every seat holds every position equally.
  - **Seed:** 20260926 by default.
  - **Stacks:** each hand draws fresh stacks with `_draw_buyin_targets(hand_seed, 6)`, between
    95 and 105bb, following the roadmap. There is no carry-over.
  - **Hand seed:** derived as `run_export` does, with `rng.randrange(1_000_000_000)` from
    `random.Random(seed)`. The same `rng` is passed to `play_one_hand`.
  - **Packs:** the raw as-loaded packs from `load_persona_packs()`.
  - **Output:** the tool writes no Parquet and never calls `run_export`, `derobo_gate`,
    `sweep_runner` or the data-contract check.
- **Per-bot grouping:**
  - **Simulated TAG:** seats 3 and 4 pooled. The seat-0 stand-in is reported on its own row and
    never pooled.
  - **Real bots:** each seat is its own row (nit, LAG, TAG seat 3, TAG seat 4, station). Both
    real TAG seats are compared with the pooled simulated TAG.
- **The fidelity check** is a pure function in `sixmax_baseline.py`, fixed before the run:
  - **Comparisons:** VPIP and PFR for each of the 5 real bot seats, which makes 10.
  - **Eligibility:** a comparison counts only if the real side has 30 or more chances.
  - **Too few:** under 8 eligible comparisons gives the result `CANT_TELL`.
  - **Per-comparison test:** it passes if the real rate lies in `[sim_lo − h, sim_hi + h]`.
    `sim_lo` and `sim_hi` are the simulation's Wilson bounds, and `h` is the half-width of the
    real rate's own Wilson interval, `(real_hi − real_lo) / 2`.
  - **Result:** `PASS` with 0 or 1 misses, `FAIL` with 2 or more.
  - **C-bet:** listed as "not tested against real play", with its real chance counts shown.

## 3. Contracts this slice changes, and how their dependents stay correct

- **The `play_one_hand` return value** gains one key, `"state"`. `run_export` and
  `capped_composition_probe` read only `hand`, `seats` and `decisions`, so their output is
  unchanged. The pinned digests in `test_buyin_spread.py:347-358` prove it and must pass
  **unedited**.
- **The `_draw_buyin_targets` signature** gains `n: int = 9`. Existing callers pass nothing, so
  the draw is identical. `test_buyin_spread.py`'s frozen oracle must pass unedited.
- **The `play_one_hand` stacks default** becomes `[STACKS_BB] * 9` when `stacks_bb` is None.
  That is unchanged, and table size comes from `len(stacks_bb)`.
- **The `export_session.py` import surface:** anything that imported `stats_for`, `Hand` and so
  on from `export_session` would break. The contract scan found no importers, and the move ticket
  re-greps to confirm.
- **`Hand.__init__`** changes from `(sim_hand, state)` to `(hand_no, hand_id, state)`, and
  `load()` passes `row.hand_no, row.id`. Simulated hands pass `(i, f"sim-{i}", state)`.
- **Nothing changes** in any schema, API, frontend type, content pack, `spot_signature()` or the
  data contract.

## 4. Test seams
- **`table_stats`:** tests go through its public functions on real `HandState` objects. They
  cover:
  - hand-built action sequences, one per new definition and each edge case: a limp is not an
    open; a BB walk is not an RFI chance; a c-bet chance is lost when someone donk-bets (leads
    into the pre-flop raiser); a fold-out before the flop is not "saw the flop";
  - `Hand` built from `play_one_hand(...)["state"]` for a few seeded 6-max hands, checking that
    `replay`'s reconciliation assertion holds.
- **Characterization:** `python -m tools.export_session --session <4b35736f…>` prints
  byte-identical output before and after the move. This is a done-condition, not a pytest test,
  because it reads the local database.
- **`sixmax_baseline`:**
  - `fidelity_check(real_rows, sim_rows)` is tested with hand-made counts for `PASS`, `FAIL`,
    `CANT_TELL`, the 30-chance cutoff and the 1-miss boundary;
  - `run_baseline(n_hands=60, seed=…)` is tested to be deterministic across two runs and to
    contain six seats with no 9-max position labels.
- **9-max guard:** `tests/test_buyin_spread.py` and `tests/test_export_analytics_schema.py` pass
  unedited.

## 5. Golden paths to imitate
- **The CLI tool:** `backend/tools/export_session.py` `main()`, for argparse, `--db`/`--session`
  handling and `resolve_db_path`.
- **The tool test:** `backend/tests/test_buyin_spread.py`, for a pure-function oracle and a
  seeded determinism check.
- **The research citations:** `docs/ai-dlc/research/rfi-seat-provenance.md`, for the
  `(format, pool, source)` triples and the VERIFIED, DERIVED and UNVERIFIED labels.

## 6. The report (`research/bot-realism-6max/m1-baseline.md`)
- **Opening:** a plain summary giving the fidelity verdict and which bots sit outside their
  ranges.
- **Then:**
  - the exact command, seed, hand count, git SHA and date;
  - one table per bot: VPIP, PFR, RFI at LJ, HJ, CO, BTN and SB, flop c-bet and WTSD, each with
    its chance count, rate and 95% interval, next to the cited real 6-max range, or
    `unsourced`;
  - the fidelity table, with all 10 comparisons, their eligibility and pass or miss, and the
    verdict;
  - c-bet's real chance counts, labelled "not tested against real play";
  - the ranges' sources, as `(format, pool, source)` triples with VERIFIED, DERIVED or
    UNVERIFIED on each figure. UNVERIFIED figures are shown, but never used for "inside or
    outside the range".
  - Known limits: the stand-in TAG sat in the owner's seat; stacks were 95–105bb, whereas the
    real session carried over up to 455bb; and the real sample is 201 hands.

## 7. Out of scope
- Any change to a persona pack, a ladder, `bot_decision` or anything else in `app/domain/`.
- `run_export`, its CLI, and any 6-max Parquet output.
- The data contract, `derobo_gate`, `sweep_runner` and `capped_composition_probe`.
- Deep-stack or carry-over simulation, which belongs to the deep-stack lane.
- Anything shown in the app.

## 8. Constraints
- **The domain core stays free of web and DB imports.** All new code lives in `backend/tools/`.
- **No new dependencies:** stdlib `math` only for the Wilson interval.
- **No solver tables.** Published solver-derived charts may be cited as ranges, labelled with
  their triple, as `rfi-seat-provenance.md` already does. Nothing solver-based is computed.
- **File size:**
  - `export_session.py` must shrink below 500 lines after the move.
  - `table_stats.py` and `sixmax_baseline.py` each stay under 500 lines.
  - `export_analytics.py` (536 lines) grows by at most a few lines, which is flagged as a known
    excess.
- **The real database is read-only:** `load()` opens it through `resolve_db_path` with no
  writes.

## 9. Verify by
1. `make check` passes with no failure beyond the baseline recorded before the first ticket.
2. `test_buyin_spread.py` passes with its pinned digests unedited:
   `git diff origin/main -- backend/tests/test_buyin_spread.py` is empty.
3. `python -m tools.export_session --session 4b35736fa8c7438eb57ca9d09874f8dc` prints output
   identical to `origin/main`.
4. `python -m tools.sixmax_baseline --session 4b35736fa8c7438eb57ca9d09874f8dc` runs to
   completion, is deterministic, and its tables match those in the report.

## 10. Definition of done
All of the following hold:
- every acceptance criterion in the tickets passes;
- `make check` exits clean against the baseline;
- nothing outside section 1 changed;
- the roadmap reflects the result, ticked only on `PASS`, with the assumption status updated on
  any result;
- every measured claim in the report names its command, seed and conditions.

The real-use condition is met by the fidelity check itself, which compares against the owner's
actual session. No phone or other device check applies.
