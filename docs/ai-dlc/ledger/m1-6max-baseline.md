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
