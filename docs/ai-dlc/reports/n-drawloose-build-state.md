# N-DRAWLOOSE — build record (COMPLETE)

**Built 2026-08-04/05 on `feat/n-drawloose`, base `b0a6a4e`. Ten commits.**
Final: **1430 passed, 1 skipped, 0 failed** · ruff clean · `BACKEND VERIFY OK`.

The authoritative description of what shipped is `docs/ai-dlc/specs/n-drawloose.md` (rev 3).
The adjudicated review findings are `docs/ai-dlc/ledger/n-drawloose.md`. This file records
how the build actually went, including what went wrong — that is the part that does not
survive in the code.

## Shape of the build

Seven tickets, strictly serial (five of them wrote the same test file, so one-file-one-owner
forced it), then a three-reviewer fan-in that **failed the slice**, then a four-wave fold
round that changed the engine again.

| | what | outcome |
|---|---|---|
| T1 | the engine change | `4b0cb31` |
| T2+T3 | raise-leg coupling gate + G-DRAW | `9d5da73` |
| T4 | absolute band + station pin | `948a980` |
| T5 | two fixture re-records | `0bb18cb` |
| T6 | the two owner rulings | `55e7d9f` |
| T7 | stale-comment sweep | `09c2364` |
| **fan-in** | refuter + Codex Sol + theory reviewer | **all three FAIL** |
| R1 | raise leg reformulated; predicate `looseness < 1.0` | `eb34e60` |
| R2 | gates rebuilt — 10 items from reviewer findings | `db1f278` |
| R3 | three fixtures re-recorded against the final engine | `5d2a7c9` |
| R4 | final comment sweep | `488255f` |

## What the fan-in changed about the product

The reviewed build was **not** what shipped. Two substantive defects came out of review:

1. **Aggressive bots had stopped semi-bluff raising.** The reference merit was computed with
   the floored expression, so the floor's growth cancelled out of the raise scale and every
   bit of freed fold mass landed on CALL. Lag's raise probability on a monster draw fell
   0.4718 → 0.3884. Fixed by computing the reference unfloored; `P(raise∣continue)` now
   matches the base engine to `1.11e-16`.
2. **The "structural, not arithmetical" claim was false**, and re-introduced the exact 1-ulp
   exposure the design existed to avoid. Fixed by predicating the branch on
   `looseness < 1.0`, so any dial ≥ 1 falls through to the untouched original expression.

The first was found only by the domain reviewer; the gate-based reviewer passed the slice.

## Traps found here — do not relearn them

1. **A script run outside the worktree measures the WRONG engine.** `sys.path[0]` is the
   script's own directory, so `app` resolves through the venv's editable-install `.pth` to
   `/Users/johncabiles/.../backend`. Both worktrees print identical numbers and nothing
   warns you. Force `PYTHONPATH=<worktree>/backend`, or run under `pytest` (its
   `pyproject.toml` sets `pythonpath = ["."]`, which is why suite readings are trustworthy).
   Always print `personas_postflop.__file__` and check it.
2. **A stale `.pyc` silently returns another mutant's numbers** when two variants write files
   of identical byte length in the same second. Use `PYTHONDONTWRITEBYTECODE=1` and purge
   `__pycache__` between mutation measurements.
3. **`rscale` divides the LIVE post-damp CALL entry**, which silently requires the N-LOGIT
   block to stay *below* the commit block. Filed as `N-DRAWORDER`. The reorder is caught
   today by G1 + G3, so it is a naming gap rather than an exposure.
4. **Asking a worker to "assert X still holds" where X is asserted elsewhere manufactures a
   vacuous gate.** My own brief did this and Codex caught it. Ask instead what a gate can
   fail on that no sibling covers, and make every gate prove it by killing a named mutant.
5. **A reviewer with write access will write.** Codex edited the engine to run mutants
   despite an explicit review-only brief. It restored correctly, but verify the tree.
6. **The Bash sandbox deny-list grows without bound with registered git worktrees** and
   eventually exceeds the OS argument limit, killing every command mid-session. 138 of them
   crossed it here. `git worktree prune` from outside Claude Code, then restart. Clean up at
   the end of a slice.

## Housekeeping

- Build worktree `/private/tmp/claude-501/wt-drawloose` and control `/private/tmp/claude-501/wt-drawbase`
  can both be removed once the PR merges. `wt-drawalt` and `wt-drawmeas` were removed during
  the build. The build worktree carries an untracked `backend/.venv` symlink and scratch
  `*.txt` run logs — none of them committed.
- Pushing to GitHub from this sandbox was never proven; the owner ran the push.
