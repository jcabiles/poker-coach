# Whole-branch review, standards lens (Claude `refuter`, Sonnet), branch head ee93bd7, 2026-10-01

Raw report as returned by the reviewer.

**Verdict: PASS-WITH-ISSUES** (no blocker, no major). `docs/CONVENTIONS.md` does not exist in this repo, so section 2a had no repo file to check; the reviewer used `~/.claude/rules/engineering-standards.md` and the 2b/2c lists. The gate was not re-run, per the brief.

## Clean checks
- Voice and secrets: `git grep -i` for the owner's name and a word grep over every added or modified file returned nothing. A grep for machine paths, scratch folders, temp variables and key prefixes also returned nothing.
- Scratch artifacts: none among the 11 added files.
- Swallowed errors: no new `except` blocks.
- Duplicated implementation: only the two minor items below.
- Content scope: `git diff main...HEAD -- content/personas` lists only the two new LAG files.
- Tests assert real output: `test_board_made_hands.py` and the `test_table_stats.py` additions call the real functions on scripted rows. The `SimpleNamespace` hand stand-in is test input, not a mock of the code under test.

## Issues
- {severity: minor, file: backend/tests/test_sixmax_baseline.py:~175, finding: possible tautological assertion. `assert counts[sb.NON_AGGRESSOR_BET]["n"] >= 0` (the count is a non-negative length) can never fail. Fix: delete it; the two `sum(...) > 0` lines already cover it.}
- {severity: minor, file: backend/tools/sixmax_baseline.py:~108-145 and ~236-256, finding: possible primitive obsession. `measure` returns tuples for most stats and dicts for the summary rows, and `_summary_cell` tells the shapes apart by sniffing keys (`"median" in v`). `_summarise_multiples` is annotated `dict[str, float]` yet returns `{"n": 0}`. The non-aggressor summary is built inline in `measure`, while the raise multiple has its own helper. Fix: two small named summary types or one shared helper, and drop the key sniffing.}
- {severity: minor, file: backend/tools/table_stats.py:~326-331, finding: possible duplicated code. The definition of "a raise into a bet", `a["action"] == "raise" and a["to_call"] > 0`, lives in two places: `stats_for` (`{street}_raise_vs_bet`) and `raise_multiples`. Fix: one predicate both call.}
- {severity: minor, file: backend/tests/test_rr_emit.py:429-476, finding: possible duplicated code, and growth of an oversized file. The three `lag6_*` tests and `_load_lag6_spec` repeat the base LAG tests line for line; the file grows from 555 to 604 lines, past the ~500 aim, without a flag. Fix: parametrize the shared tests over the two specs, or move the 6-max block to its own file.}
- {severity: minor, file: backend/tests/test_buyin_spread.py:345-360, backend/tests/test_limper_coverage_belt.py:541-557, backend/tests/test_bot_decisions_golden.py:20-26, finding: possible narration comment. The comments re-list the old digests and old counts and say the re-pin dates twice; git history already keeps that. Fix: keep only the constraint.}
- {severity: minor, file: backend/app/domain/personas_postflop.py (2,226 lines) and backend/tests/test_personas_postflop.py (14,340 lines), finding: a pre-existing oversized file grows again (+3 and +8 net lines), unflagged. Fix: note it in the PR, or split in the cleanup project.}
- {severity: minor, file: backend/tests/test_table_stats.py:~257 and backend/tests/test_board_made_hands.py:6, finding: bare internal labels with no gloss in committed text. Fix: say what the thing is in plain words, or drop the label.}
- {severity: minor, file: docs/ai-dlc/escapes.md:5, finding: the placeholder `PR #TBD` is committed. Fix: fill in the PR number after opening, or write "this PR".}
- {severity: optional, file: docs/ai-dlc/research/bot-realism-6max/m2-lag-retune.md (580 lines), finding: past the ~500-line aim. Engineering standards also route measured results to `docs/FINDINGS.md`, but the repo's existing pattern is a per-slice research file.}

## Stated requirements the branch does not carry
- Spec §7 item 1 (CO 95% interval must contain 33) is not met: 28.5% [25.2, 32.1] on the judged seed. The report and roadmap say the project owner waived this on 2026-10-01; the reviewer could not verify the waiver.
- The owner decision "LAG opening fewer hands than the TAG from LJ and HJ is accepted" covers only LJ and HJ; the report says the LAG also opens less than the TAG at CO.
- The remaining items trace to the diff: the three build commits, item 2 reported as a known gap, items 3 to 6 pass, and the ledger file is present. The report does not claim the full supporting check passed.

## Could not check
The owner waiver of the CO miss; the ledger and prior reviews (withheld by instruction); the tests and simulations (not run); whether the retuned LAG feels right (the owner's post-merge verdict).
