# Tickets — M2, retune the LAG at 6-max (plus the board-straight fix)
status: proposed (awaiting the project owner's go; the --auto-build pre-approval was voided because the spec review needed owner rulings)

## Bottom line
- Five tickets in four waves build spec rev 2 (`../specs/m2-lag-6max-retune.md`) as three build
  commits:
  - commit 1: the stats and the frozen targets;
  - commit 2: the bug fix;
  - commit 3: the LAG's 6-max settings and the results report.
- Every ticket leaves `make check` green. T1 and T3 run together on disjoint files; T2, T4 and T5 run
  alone, in that order.
- One scratch script, the matched replay (each hand on its own random stream, so a change in one hand
  cannot move another), is written in T2, reused in T4, and inlined in the report by T5. It is never
  committed as a tool.

## Dependency graph
```
Wave 1:  T1 (stats)  ∥  T3 (sources + frozen targets)   → commit 1
Wave 2:  T2 (board fix + matched replays)               → commit 2
Wave 3:  T4 (LAG 6-max settings)                         ┐
Wave 4:  T5 (report results + bookkeeping)               ┘→ commit 3
then the whole-branch review, the merge gate, the PR
```

## Shared conditions for every ticket
- **Worktree:** the branch `feat/m2-lag-retune`.
- **Python:** `backend/.venv`, linked from the main checkout.
- **Never run two at once:** two `make check` runs, or two `./scripts/verify.sh` runs (it migrates
  the local database).
- **Judged simulation command** (from `backend/`):
  `PYTHONPATH=. .venv/bin/python -m tools.sixmax_baseline --session 4b35736fa8c7438eb57ca9d09874f8dc --max-hand-no 201 --db <main checkout>/backend/data/poker_coach.db`
  - The defaults are 6,000 hands at seed 20260926.
  - Outputs go to the session scratch folder `m2-sim/`, run twice each, and the two runs must be
    byte-identical.
- **Never weaken a test.** Never delete or loosen an assertion, and never add a skip or xfail marker.
- **Tests and randomness:** randomness in tests uses a fixed seed, and a new test must fail before the
  change and pass after.

## T1 — Three new stats in the 6-max measurement tool (commit 1)
- **What:** spec §3, adding three stats per bot.
  - **Raise-when-bet-into:** the flop alone, and flop, turn and river pooled, with Wilson intervals.
  - **Raise multiple:** n, median, mean, 90th percentile, and the share at 4× or more. It comes from
    a new `raise_multiples` function in `table_stats.py`; `stats_for` and its four callers stay
    unchanged.
  - **Non-aggressor bet size:** n, and the mean as a fraction of the pot.
  - All three are surfaced in `sixmax_baseline.measure()` and its printed tables.
- **Owned files:** `backend/tools/table_stats.py`, `backend/tools/sixmax_baseline.py`,
  `backend/tests/test_sixmax_baseline.py`, `backend/tests/test_table_stats.py`.
- **Golden path:** the `raise_vs_bet` accumulation at `table_stats.py:289-301`; existing tests in
  `test_table_stats.py`.
- **Done-condition:**
  - `make check` exits 0;
  - both golden digests in `test_bot_decisions_golden.py` are unchanged;
  - the judged simulation prints the three stats for every bot, saved as `m2-sim/c1-run{1,2}.txt`
    (identical). The LAG baseline should show about 272 raises with a 3.00× median.
- **Agent:** `implementer` (Sonnet, medium pin). `gemini-ok`.

## T3 — Sourcing pass and frozen targets (commit 1)
- **What:** spec §5's sourcing pass and §7's frozen targets. Create the report with these sections:
  - a `## Bottom line`;
  - "Ranges and sources": the M1 method, matching definitions only;
  - "Frozen targets": every §7 item with its value or band, the minimum samples, the owner's three
    2026-09-30 rulings (openings win; the LAG-vs-TAG inversion is accepted; the tail target with
    smaller leads), and which items are approximate.
- **Owned files:** `docs/ai-dlc/research/bot-realism-6max/m2-lag-retune.md` (these sections only).
- **Golden path:** the "Ranges and sources" section of `m1-baseline.md`.
- **Done-condition:**
  - the file exists and opens with a Bottom line;
  - every figure carries a VERIFIED / DERIVED / UNVERIFIED label;
  - every source states its definition;
  - the frozen-targets section covers §7 items 1–6;
  - `grep` finds no personal name.
- **Agent:** `general-purpose` (Sonnet; needs web search and fetch). `claude-only` (source judgement).

## T2 — The board-made-hand fix and matched replays (commit 2)
- **What:** spec §4.
  - Add the rule to `_made_bucket`.
  - Add the unit tests: five that change to middle pair, four guard tests that stay monster.
  - Re-pin both golden digests and `_GOLDEN_STATS_N200`, plus any other 9-max pin only if it fails,
    with its reason.
  - Write `m2-sim/matched_replay.py`, which works in two steps: it dumps per-hand action fingerprints
    and export rows, at 9 or 6 seats, with each hand seeded `random.Random(hand_seed + 1)`; then it
    compares two dumps and attributes each difference.
  - Run it before and after the fix: 4,000 9-max hands (the attribution check) and 6,000 6-max hands
    (the fix's share).
- **Owned files:** `backend/app/domain/personas_postflop.py` (`_made_bucket` only),
  `backend/tests/test_board_made_hands.py` (new), `backend/tests/test_bot_decisions_golden.py`
  (digest constants), `backend/tests/test_personas_postflop.py` (stat pins only), and the scratch
  folder `m2-sim/`.
- **Golden path:** the board-trips branch and F7 comment at `personas_postflop.py:123-140`; direct
  bucket calls as in `test_mw_catch_toppair.py:185`.
- **Done-condition:**
  - `make check` exits 0;
  - each new middle-pair test fails before the fix (shown by running it with the rule removed) and
    passes after;
  - the 9-max matched replay reports changed hands > 0 and 0 unattributed hands or rows, saved as
    `m2-sim/c2-attribution-9max.txt`;
  - the 6-max fix-share output is saved as `m2-sim/c2-share-6max.txt`.
- **Agent:** `heavy-worker` (Opus, high pin). `claude-only` (decision-engine logic).

## T4 — The LAG's 6-max settings (commit 3, with T5)
- **What:** spec §5.
  - Author `ladders/six_max/lag.unopened.json` with the seats LJ, HJ, CO, BTN, SB and BB. `raise_pct`
    equals the emitted width, and the targets go in `_doc`.
  - Emit its nodes into the new `six_max/lag.json` `preflop.unopened`.
  - Calibrate SB on pooled seeds 1–5.
  - Override `postflop.sizing` and `postflop.continue_ref`, starting from `continue_ref` 2.0 and
    {0.33: 0.45, 0.5: 0.35, 0.75: 0.10, 1.0: 0.10}.
  - Extend the drift, annotation and monotone tests; edit the range-lint inventory only if it moves.
  - Re-pin the 6-max digest.
  - Run the matched replay before and after (the retune's share).
  - No other dial moves. If §7 items 1, 3 and 4 cannot all be met, stop and report.
- **Owned files:** `content/personas/ladders/six_max/lag.unopened.json` (new),
  `content/personas/six_max/lag.json` (new), `backend/tests/test_rr_emit.py`,
  `backend/tests/test_pack_range_lint.py` (inventory only), `backend/tests/test_bot_decisions_golden.py`
  (6-max digest only), and the scratch folder `m2-sim/`.
- **Golden path:** `content/personas/ladders/lag.unopened.json`; the base-LAG block at
  `test_rr_emit.py:313-436`; the fixture override in `backend/tests/persona_override_fixture.py`.
- **Done-condition:**
  - `make check` exits 0;
  - the judged simulation (`m2-sim/c3-run{1,2}.txt`, identical) meets spec §7 items 1, 3 and 4, and
    reports item 2;
  - the 9-max golden digest is unchanged from commit 2;
  - `git diff --stat` over `content/personas/` shows only the two new files;
  - the retune-share output is saved as `m2-sim/c3-share-6max.txt`.
- **Agent:** `heavy-worker` (Opus, high pin). `claude-only` (iterative tuning against targets).

## T5 — Results report and bookkeeping (commit 3, with T4)
- **What:** spec §6 and §9.
  - Add the report's results from the saved `m2-sim/` outputs:
    - per-bot tables at commits 1 and 3;
    - each part's share, from the matched replays;
    - the LAG-versus-TAG table by seat;
    - the non-aggressor bet size before and after;
    - the §7 pass/fail table, with the item-2 known gap if any;
    - the attribution result and the §4 known near-ties;
    - an appendix with the matched-replay script inlined.
  - Update the roadmap's M2 entry: built note and measured result, box unticked.
  - Create `escapes.md` with row E1.
  - Remove the `## Resume` block from `profile.md`.
- **Owned files:** `docs/ai-dlc/research/bot-realism-6max/m2-lag-retune.md` (results sections and
  appendix), `docs/ai-dlc/roadmap/bot-realism-6max.md` (M2 entry), `docs/ai-dlc/escapes.md` (new),
  `docs/ai-dlc/profile.md` (Resume block removal only).
- **Golden path:** `m1-baseline.md`, and the escape-log columns: ID, Found, Defect, Path, Commits,
  Category, Question that should have caught it, Asked?, Promoted to.
- **Done-condition:**
  - every §7 item appears in the pass/fail table with its number and verdict;
  - every number matches the saved outputs;
  - `make check` exits 0.
- **Agent:** `implementer` (Sonnet, medium pin). `gemini-ok`.
