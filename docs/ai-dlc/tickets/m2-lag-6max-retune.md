# Tickets — M2, retune the LAG at 6-max (plus the board-straight fix)
status: draft

## Bottom line
- Five tickets in four waves build the spec `../specs/m2-lag-6max-retune.md`: two new
  measurement stats, a sourcing pass for the LAG's raise targets, the board-made-hand bug fix, the
  LAG's 6-max settings file, and the results report.
- Every ticket leaves `make check` green and lands as its own commit, in the order the spec's §2
  requires (stats → sources → fix → retune → report), so each part's effect is measurable.
- Waves: T1 and T3 run together (disjoint files); T2, T4 and T5 run alone, in that order.

## Dependency graph
```
Wave 1:  T1 (stats)  ∥  T3 (sources)
Wave 2:  T2 (board fix)          needs T1 committed
Wave 3:  T4 (LAG 6-max settings) needs T2 and T3 committed
Wave 4:  T5 (report + bookkeeping) needs T4 committed
then the whole-branch review, the merge gate, the PR
```

## Shared conditions for every ticket
- Worktree: the branch `feat/m2-lag-retune`. Python: `backend/.venv` (linked from the main
  checkout). Never run two `make check` or `./scripts/verify.sh` at once (the latter migrates the
  local database).
- **Simulation command** (from `backend/`):
  `PYTHONPATH=. .venv/bin/python -m tools.sixmax_baseline --session 4b35736fa8c7438eb57ca9d09874f8dc --max-hand-no 201 --db <main checkout>/backend/data/poker_coach.db`
  (defaults: 6,000 hands, seed 20260926). Each sim-running ticket saves its output twice to the
  session scratch folder `m2-sim/<ticket>-run{1,2}.txt` and confirms the two are byte-identical.
- Never delete or loosen an assertion, and never add a skip or xfail marker. Randomness in tests
  uses a fixed seed. New tests must fail before the change and pass after.

## T1 — Two new stats in the 6-max measurement tool (commit 1)
- **What:** `stats_for` gains the raise-multiple accumulation; `sixmax_baseline.measure()` and its
  printed tables surface raise-when-bet-into (flop alone, and flop+turn+river pooled, with Wilson
  intervals) and raise multiple (n, median, mean) per bot (spec §3).
- **Owned files:** `backend/tools/table_stats.py`, `backend/tools/sixmax_baseline.py`,
  `backend/tests/test_sixmax_baseline.py`, the existing `table_stats` test module.
- **Golden path:** the `raise_vs_bet` accumulation at `table_stats.py:289-301`; tests in
  `test_sixmax_baseline.py`.
- **Done-condition:** `make check` exits 0; both golden digests in
  `test_bot_decisions_golden.py` unchanged; the simulation command prints both new stats for every
  bot (saved as `m2-sim/T1-run{1,2}.txt`, identical).
- **Agent:** `implementer` (Sonnet, medium pin). `gemini-ok`.

## T3 — Sourcing pass for the LAG's raise targets (docs commit, before T4)
- **What:** search for verified 6-max figures for a LAG's post-flop raise-when-bet-into rate and
  raise size as a multiple of the bet, by the M1 method (direct fetch, `(format, pool, source)`
  triples, VERIFIED / DERIVED / UNVERIFIED labels, no full-ring figure in a 6-max cell). Create the
  report with its `## Bottom line`, a "Ranges and sources" section, and a "Frozen targets" section
  stating the five RFI points, the VPIP/PFR ranges, and the two raise targets (sourced range, or the
  approximate bands 10–20% and 2.5–3.5×, labelled approximate).
- **Owned files:** `docs/ai-dlc/research/bot-realism-6max/m2-lag-retune.md` (these sections only).
- **Golden path:** the "Ranges and sources" section of `m1-baseline.md`.
- **Done-condition:** the file exists, opens with a Bottom line, every figure carries a label, and
  the frozen-targets section names a value or band for each §7 item.
- **Agent:** `general-purpose` (Sonnet; needs web search and fetch). `claude-only` (source
  judgement).

## T2 — The board-made-hand fix (commit 2)
- **What:** spec §4. `_made_bucket` returns `MIDDLE_PAIR` when a straight or better equals the
  board's own best five on a five-card board; unit tests; re-pin both golden digests; re-pin a
  9-max stat pin only if it fails, with its reason; run the one-shot 9-max attribution check (script
  in scratch, never committed).
- **Owned files:** `backend/app/domain/personas_postflop.py` (`_made_bucket` only),
  `backend/tests/test_board_made_hands.py` (new), `backend/tests/test_bot_decisions_golden.py`
  (digest constants), `backend/tests/test_personas_postflop.py` (stat pins only, only on failure).
- **Golden path:** the board-trips branch and F7 comment at `personas_postflop.py:123-140`; direct
  bucket calls as in `test_mw_catch_toppair.py:185`.
- **Done-condition:** `make check` exits 0; each new "→ MIDDLE_PAIR" test fails at commit 1 and
  passes after; the attribution check reports unattributed = 0 (output saved as
  `m2-sim/T2-attribution.txt`); simulation saved as `m2-sim/T2-run{1,2}.txt`, identical.
- **Agent:** `heavy-worker` (Opus, high pin). `claude-only` (decision-engine logic).

## T4 — The LAG's 6-max settings (commit 3)
- **What:** spec §5. Author `ladders/six_max/lag.unopened.json`, emit its nodes into the new
  `six_max/lag.json` `preflop.unopened`; override `postflop.sizing` and `postflop.continue_ref`;
  extend the drift gate; edit the range-lint inventory only if it moves; re-pin the 6-max digest.
  No other dial moves; if the targets cannot be met with these three changes, stop and report.
- **Owned files:** `content/personas/ladders/six_max/lag.unopened.json` (new),
  `content/personas/six_max/lag.json` (new), `backend/tests/test_rr_emit.py`,
  `backend/tests/test_pack_range_lint.py` (inventory only), `backend/tests/test_bot_decisions_golden.py`
  (6-max digest only).
- **Golden path:** `content/personas/ladders/lag.unopened.json`; the base-LAG drift block at
  `test_rr_emit.py:313-398`; the fixture override in `backend/tests/persona_override_fixture.py`.
- **Done-condition:** `make check` exits 0; the simulation (saved as `m2-sim/T4-run{1,2}.txt`,
  identical) meets spec §7 items 1–4; `per_hand_digests(9)` equals T2's list exactly;
  `git diff --stat` over `content/personas/` shows only the two new files.
- **Agent:** `heavy-worker` (Opus, high pin). `claude-only` (iterative tuning against targets).

## T5 — Results report and bookkeeping (commit 4)
- **What:** spec §6 and §9. Fill the report's results: per-bot tables at commits 1, 2 and 3 from
  the saved simulation outputs, the fix's share (1 → 2) and the retune's share (2 → 3), the §7
  pass/fail table, the attribution result; update the roadmap's M2 entry (built note, measured
  result, box unticked); create `escapes.md` row E1; remove the `## Resume` block from
  `profile.md`.
- **Owned files:** `docs/ai-dlc/research/bot-realism-6max/m2-lag-retune.md` (results sections),
  `docs/ai-dlc/roadmap/bot-realism-6max.md` (M2 entry), `docs/ai-dlc/escapes.md` (new),
  `docs/ai-dlc/profile.md` (Resume block removal only).
- **Golden path:** `m1-baseline.md`; the escape-log schema (columns: ID, Found, Defect, Path,
  Commits, Category, Question that should have caught it, Asked?, Promoted to).
- **Done-condition:** every §7 item appears in the pass/fail table with its number and verdict;
  every number matches the saved outputs; `make check` exits 0.
- **Agent:** `implementer` (Sonnet, medium pin). `gemini-ok`.
