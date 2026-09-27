# M1 final review — the 6-max tool (T4) and the report (T6) (2026-09-26)

**Bottom line:** approve-with-fixes, with nothing blocking. The check that the simulation
matches the owner's table pairs the right bots, uses the right hands and gives the right
answer, PASS. The four should-fix items were overstated report wording, a stale roadmap line,
and a missing test guard.

- **Reviewer:** Claude `refuter` on Opus, reviewing commits `e12e244` and `f0694d4`, blind to
  the interview.
- **What held:**
  - A fresh run matched every cell of the report, including all 10 fidelity rows and the
    verdict.
  - The simulated TAG row pools seats 3 and 4 only (n = 11,828), and the seat-0 stand-in is
    separate.
  - The real session holds 201 hands after the cap, none skipped, with the owner's seat
    excluded.
  - Challenge mode does not change bot policy, and no bot code changed after the session.
  - Six range judgements were spot-checked and found correct.
  - The 9-max guard file is untouched.
  - The full backend suite passes, 2334.
  - Planted breaks in the fidelity-check tests turned them red.
  - The M1 tick is warranted.

## Findings
1. **should-fix:** the bottom line said the simulator can stand in for all pre-flop tuning.
   Only overall VPIP and PFR were tested, and the pooled real TAG PFR (13.3%) would narrowly
   miss (the pass range starts at 13.86%).
2. **should-fix:** the report blamed sample size for testing only VPIP and PFR. The real cause
   is the pre-registered design: RFI at LJ reached 33–34 chances.
3. **should-fix:** the roadmap still described 15 comparisons including c-bet, and did not
   record the narrowing ruling. The LAG c-bet would have been an 11th eligible comparison, and
   it passes.
4. **should-fix:** no test guards the bot pairing or the rule that seat 0 is never pooled.
   Mutants of `REAL_ROWS` and `SIM_GROUPS` stayed green.
5. **optional:** the git SHA prints `unknown` in a worktree, because of the private
   `export_session._git_sha` import.
6. **optional:** `Hand` id annotation mismatch (a `str` is passed).
7. **optional:** "both TAGs" in the bottom line is ambiguous.
