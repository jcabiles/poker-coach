# Tickets — M1, measure the 6-max baseline

status: **proposed** — awaiting the owner's approval at the build gate. Nothing below is
cleared to build.
- Spec: `../specs/m1-6max-baseline.md`.
- Contracts: `../contracts/m1-6max-baseline.md`.
- Ledger: `../ledger/m1-6max-baseline.md`.

## Shape of the work

Six tickets. The code chain is T1 → T2 → T3 → T4 → T6. T5 (range research, docs only) runs
alongside T1–T4, and T6 needs both.

- **Barrier:** before T1, run `make check` on `main` and record the pass and fail counts.
  - At every later barrier, run the whole suite, not a name-filtered selection.
  - "Clean" means no failure beyond that baseline, and no drop in the passing count.
- **Session ID** used below: `S=4b35736fa8c7438eb57ca9d09874f8dc`.
- **Before T2:** capture `python -m tools.export_session --session $S > $TMPDIR/es-before.txt`
  on `origin/main`, from `backend/` with the main checkout's venv.

---

### T1 — Let the simulator's single-hand function play any table size
- **What:**
  - `_draw_buyin_targets(hand_seed, n=9)` draws `n` targets.
  - `play_one_hand` takes its seat count from `len(stacks_bb)`, keeps the 9 × 100bb default,
    and adds `"state": state`, the final `HandState`, to its return value.
  - `run_export` is untouched.
- **Owns:** `backend/tools/export_analytics.py`, plus one new test in
  `backend/tests/test_buyin_spread.py`.
  - The new test only adds: `_draw_buyin_targets(seed, 6)` returns 6 targets, equal to the first
    6 of the 9-target draw.
  - No existing line in that file changes.
- **Imitate:** the frozen-oracle test already in `test_buyin_spread.py`.
- **Done when:**
  - `git diff origin/main -- backend/tests/test_buyin_spread.py` shows additions only;
  - `pytest tests/test_buyin_spread.py tests/test_export_analytics_schema.py tests/test_capped_composition_probe.py`
    passes;
  - the four pinned digests still match.

### T2 — Move the stats code into `tools/table_stats.py` (no behaviour change)
- **What:**
  - Move `Hand`, `load`, `settle_hand`, `replay`, `stats_for`, `resolve_db_path` and their private
    helpers from `export_session.py` into the new `tools/table_stats.py`.
  - `Hand.__init__` becomes `(hand_no, hand_id, state)`.
  - `export_session.py` imports them.
  - First re-grep `backend/` and `scripts/` for importers of these names from `export_session`,
    and update any found.
- **Owns:** `backend/tools/table_stats.py` (new), `backend/tools/export_session.py`,
  `backend/tests/test_table_stats.py` (new).
- **Tests:** characterization tests on a few seeded 6-max hands from T1's `"state"`:
  - `replay` reconciles;
  - `stats_for` returns the same counts as a hand-computed expectation for 2 hand-built hands.
- **Imitate:** `export_session.py` itself — this is a move, not a rewrite.
- **Done when:**
  - `diff $TMPDIR/es-before.txt <(python -m tools.export_session --session $S)` is empty;
  - `wc -l tools/export_session.py` is under 500;
  - the full backend suite is clean.

### T3 — Add opening rate by seat, flop c-bet and the Wilson interval
- **What:**
  - Extend `stats_for` per the spec's definitions (section 2), keeping per-position chance and
    open counts.
  - Add `wilson(k, n) -> (lo, hi)`.
  - The existing keys and `export_session`'s printed output stay unchanged.
- **Owns:** `backend/tools/table_stats.py`, `backend/tests/test_table_stats.py`.
- **Tests:** one hand-built `HandState` action sequence per rule:
  - folded to LJ, which raises: an RFI chance and an open;
  - a limp: a chance, but not an open;
  - a BB walk: no chance;
  - raiser checked to on the flop, then bets: a c-bet;
  - a donk bet before the raiser acts: no c-bet chance;
  - a fold-out before the flop: no flop and no c-bet chance;
  - `wilson(0, 0)` handled without dividing by zero, plus a known value, for example
    `wilson(20, 100)` ≈ (0.133, 0.289).
- **Done when:**
  - `pytest tests/test_table_stats.py` passes;
  - the `export_session` diff from T2 is still empty.

### T4 — `tools/sixmax_baseline.py`: the 6-max run and the fidelity check
- **What:** the CLI `--hands 6000 --seed 20260926 --session <id> [--db path]`. It holds:
  - `run_baseline(n_hands, seed)`, using the spec's seat map, `i % 6` rotation,
    `_draw_buyin_targets(hand_seed, 6)` and the raw packs;
  - `load` for the real session;
  - `fidelity_check(real, sim) -> {verdict, rows}` per the spec's section 2;
  - Markdown tables printed to stdout.
- The tool never writes Parquet and never calls `run_export`.
- **Owns:** `backend/tools/sixmax_baseline.py` (new), `backend/tests/test_sixmax_baseline.py`
  (new).
- **Imitate:** `export_session.py` `main()` for the CLI, and `test_buyin_spread.py` for the
  oracle and determinism tests.
- **Tests:**
  - `fidelity_check` gives `PASS` with 0 misses and with 1 miss, `FAIL` with 2, and `CANT_TELL`
    with 7 eligible;
  - a comparison with 29 real chances is excluded;
  - `run_baseline(60, 1)` is identical across two calls, and every position is one of the six
    6-max labels.
- **Done when:**
  - the tests pass;
  - `python -m tools.sixmax_baseline --hands 600 --session $S` completes and prints every
    table;
  - the full suite and `make check` are clean.

### T5 — Source the real 6-max ranges (research, docs only; runs alongside T1–T4)
- **What:** for each bot type (nit, TAG, LAG, calling station), find cited real 6-max ranges for
  VPIP, PFR, RFI at LJ, HJ, CO, BTN and SB, flop c-bet and WTSD.
  - Record each as a `(format, pool, source)` triple, with VERIFIED only for a directly fetched
    page, DERIVED for arithmetic on sourced figures, and UNVERIFIED otherwise.
  - Reuse `rfi-seat-provenance.md`'s T2 6-max opening charts.
  - A stat with no source is written `unsourced`, never filled with a guess.
- **Owns:** the "Ranges and sources" section of
  `docs/ai-dlc/research/bot-realism-6max/m1-baseline.md` (it creates the file with that section
  only).
- **Imitate:** `docs/ai-dlc/research/rfi-seat-provenance.md`.
- **Done when:**
  - every (bot type, stat) cell has a range with a triple, or `unsourced`;
  - every VERIFIED cell names the URL and fetch date.

### T6 — Run it and write the report
- **What:**
  - Run `python -m tools.sixmax_baseline --session $S` at the defaults (6,000 hands, seed
    20260926).
  - Write the rest of `m1-baseline.md` per spec section 6: summary first, the per-bot tables
    against T5's ranges, the fidelity table and verdict, c-bet labelled untested, and known
    limits.
  - Update the roadmap:
    - on `PASS`, tick M1 and set the assumption status to "tested — held for pre-flop play";
    - on `FAIL` or `CANT_TELL`, leave M1 unticked, record the result, and **stop**. Report to
      the owner; do not start M1b or M2.
- **Owns:** `docs/ai-dlc/research/bot-realism-6max/m1-baseline.md` (all but T5's section),
  `docs/ai-dlc/roadmap/bot-realism-6max.md`.
- **Done when:**
  - re-running the command reproduces the report's numbers exactly;
  - the report states its command, seed, SHA and date;
  - `make check` is clean.
