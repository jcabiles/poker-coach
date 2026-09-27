# Finding ledger — M1, the 6-max baseline measurement

**Bottom line:** one blind review round of the spec approved it with fixes. All eight findings
were checked against the code and folded in:
- the three blocking ones are fixed, one of them by an owner ruling;
- the two should-fix ones are fixed;
- two of the three optional ones were accepted, and the third, the missing ledger, is answered
  by this file.

- **Reviewer:** Claude `refuter` on Opus, 2026-09-26. This is the labelled fail-open fallback,
  a same-family reviewer: Codex cannot run inside this repo's sandbox.
- **Input:** blind — the spec, tickets, contracts and roadmap only, without the interview record.
- **Verdict:** approve-with-fixes.

| # | Severity | Finding | Status |
|---|---|---|---|
| 1 | blocking | The `export_session` output-equality check can never pass, because the `tool SHA` line changes with every commit. Verified at `export_session.py:507`. | fixed — both sides are filtered with `grep -v 'tool SHA'` and pinned with `--max-hand-no 201 --db` |
| 2 | blocking | The spec says `test_buyin_spread.py` stays unedited, while T1 (making the simulator's single-hand function work at any table size) added a test to it. | fixed — T1's tests move to a new `test_export_analytics_table_size.py` |
| 3 | blocking | The spec's "1 miss passes" filled a gap in the roadmap's rule without an owner ruling. | fixed — owner ruled 1 miss = pass (2026-09-26); recorded in the spec and the roadmap |
| 4 | should-fix | A fifth 9-seat assumption: `play_one_hand` deals without a table size (`export_analytics.py:192`), unlike the live table (`sim_session.py:266`). Verified. | fixed — T1 passes `len(stacks_bb)`; the contracts file is updated |
| 5 | should-fix | The real session can still grow (hand 202 is saved mid-hand), so reruns may not reproduce. | fixed — `--max-hand-no 201` is pinned and recorded in the report |
| 6 | optional | A raiser all-in before the flop was counted as a missed c-bet. | accepted — the c-bet chance now requires a flop action; a test was added |
| 7 | optional | The solver 6-max charts are balanced play, not per-type ranges. | accepted — T5 (range research) labels them as a balanced reference only |
| 8 | optional | The ledger file did not exist. | fixed — this file |

The reviewer also confirmed:
- the engine runs 6 seats (600 hands in under 1s);
- all 10 comparisons have 193–198 real chances;
- stack depth cannot bias VPIP or PFR, because the bots' pre-flop policy never reads the stack
  (`play.py:237-252`);
- no importers of `export_session` exist.

## Build fan-in records

- **T1 (simulator plays any table size), 2026-09-26:** Tier 0, checks green, no reviewer.
  - **Worker:** implementer on Sonnet.
  - **The Director re-ran the done-condition in a fresh process:**
    - 43 passed across the new table-size tests, `test_buyin_spread.py`,
      `test_export_analytics_schema.py` and `test_capped_composition_probe.py`;
    - the four pinned 9-max digests still match;
    - `git diff origin/main -- backend/tests/test_buyin_spread.py` is empty;
    - ruff is clean.
  - **Why no reviewer:** the diff is 26 lines, and the pinned digests fully prove the ticket's
    risk, 9-max byte identity.
  - **Deviation from the announced plan,** which listed an Opus reviewer here: the exemption
    applies because the deterministic checks cover every acceptance criterion.
  - **File size:** `export_analytics.py` is now 544 lines, up from 536. This is the known excess
    the spec flags.
- **T5 (sourcing real 6-max ranges), 2026-09-26:** accepted, with the Director's spot-check as
  the check. The final reviewer re-checks it at T6.
  - **Worker:** general-purpose on Opus.
  - **Result:** 32 of 36 cells VERIFIED, 1 UNVERIFIED, and 3 unsourced (LAG c-bet, LAG WTSD,
    station c-bet).
  - **Director re-fetch:**
    - PokerStrategy "Average Pre-flop Ranges: LAG" (S3) gives 20/23/33/50/43, matching the file;
    - BlackRain79's WTSD page (S11) gives "27 in 6max" and "25 in full ring", matching the file,
      and the full-ring column was correctly excluded.
  - **Caveats carried into the report:**
    - The S1–S4 format is inferred from a six-seat position list, which is 6-max.
    - Post-flop type labels are mapped by us.
    - Every figure is coaching guidance, not measured pool data. So T6 treats the spread across
      sources as the tolerance, not any single point.
- **T2 (moving the stats code into `tools/table_stats.py`), 2026-09-26:** Tier 0, checks green,
  no reviewer. It was stopped mid-run by the owner, then re-verified by the Director on resume.
  - **Output unchanged:** `export_session` prints the same 4,879 lines before and after once the
    `tool SHA` line is removed (`diff` exit 0).
  - **Checks:** `test_table_stats.py` 2 passed; ruff, format and mypy clean.
  - **No duplicates or importers:** no definition remains in `export_session.py`, which now
    imports from `table_stats`, and nothing else imports those names.
  - **File sizes:** `export_session.py` is 429 lines and `table_stats.py` 269.
  - **Full suite deferred:** the ~8-minute run moves to the T3 barrier, because T2 changes only
    `tools/` files that no existing test imports.
- **T3 (opening rate by seat, c-bet and Wilson intervals), 2026-09-26:**
  - **Worker:** implementer on Opus. The full suite passed with 2323 passed, 2 skipped, and the
    export output was identical.
  - **Review:** Opus `refuter`, verdict approve-with-fixes
    (`../reviews/m1-t3-refuter.md`). Findings:
    - (1) should-fix, no 3-bet-pot test for the last-raiser rule — accepted, fix in progress;
    - (2) optional, the BB-guard test and comment — accepted;
    - (3) optional, the Wilson clamp — accepted;
    - (4) optional, the mypy `Hand` id type — accepted.
  - **Status:** all four fixed (Sonnet worker, Director re-ran the checks): test_table_stats
    12 passed; mypy on `app` and `tools/table_stats.py` clean; the export output is unchanged; the new
    3-bet test fails against the first-raiser mutant.
- **T4 (the `sixmax_baseline` tool and the fidelity check), 2026-09-26:**
  - **Worker:** implementer on Opus.
  - **Checks:** `test_sixmax_baseline.py` 9 passed; full suite 2332 passed, 2 skipped, 0
    failed; ruff and mypy clean. The 6,000-hand run takes about 10 seconds.
  - **Provisional result:** the 600-hand smoke run gives PASS, with 10 eligible and 0 misses.
  - **Spec amended:** `fidelity_check(pairs)`, a single list, replaces
    `fidelity_check(real_rows, sim_rows)`.
  - **Known wrinkle:** the header's git SHA reads `unknown` in a linked worktree, because
    `export_session._git_sha` reads `.git/`. T6 records the SHA from `git rev-parse` instead.
  - **Review:** folded into one final Opus review covering T4 and T6 together, a deviation from
    the announced plan made to save the owner's usage.
- **T6 (running the tool and writing the report), 2026-09-26:**
  - **Worker:** implementer on Opus.
  - **Verdict:** PASS, with 10 of 10 comparisons eligible and 0 misses. M1 is ticked.
  - **Checks:** `make check` green, with 2334 backend and 135 frontend tests passing. All 45
    report cells match a fresh run.
- **Final review of T4 and T6,** by an Opus `refuter`, verdict approve-with-fixes
  (`../reviews/m1-t4-t6-refuter.md`):
  - (1) the bottom line overstated the result — fixed by the Director: it now names what was
    and was not tested, and the near-miss when the real TAG seats are pooled;
  - (2) the wrong reason was given for testing only VPIP and PFR — fixed by the Director;
  - (3) the stale roadmap test description — fixed by the Director: the narrowing ruling and
    the LAG c-bet result are recorded, and the Next action is refreshed;
  - (4) the missing pairing guard — fixed: `build_pairs()` was extracted, with 4 tests that
    fail against both mutants;
  - (5) the SHA import — fixed: the tool now uses `export_analytics._git_sha`, which works in a
    worktree;
  - (6) the annotation — fixed: `Hand` id is typed `int | str | None`;
  - for (4)–(6): a Sonnet worker made the changes and the Director checked them. The tool
    output is identical to the reviewer's fresh run apart from the SHA and date lines;
  - (7) the ambiguous "both TAGs" — fixed by the Director.
