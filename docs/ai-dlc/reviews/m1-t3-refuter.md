# M1 T3 review — the opening-rate, c-bet and Wilson stats (2026-09-26)

**Bottom line:** approve-with-fixes.
- The new stats count correctly under the spec's definitions. An independent recount over
  1,200 simulated hands matched with zero mismatches.
- The one real gap was a test: nothing pinned the rule that the *last* pre-flop raiser gets the
  c-bet chance.

- **Reviewer:** Claude `refuter` on Opus, reviewing commit `841bcd7`, blind to the planning
  interview.
- **Deterministic checks:**
  - `test_table_stats.py`: 10 passed.
  - The export_session output is identical to the pre-change capture.
  - An independent recount of RFI and c-bet from raw `action_history`, over 600 hands at 100bb
    plus 600 hands with short stacks, gave 0 mismatches.
  - For every seat, rfi ≤ rfi_opp and cbet ≤ cbet_opp ≤ saw_flop.
- **Mutation testing,** which means breaking the code on purpose to see whether a test notices:
  5 of 7 mutants were caught. The two survivors were "first raiser instead of last" and
  "remove the BB guard".
- **Judgement on non-reopening all-in raises:** the engine records these as raises, so a short
  stack that shoves becomes the pre-flop aggressor, and the earlier opener gets no c-bet chance.
  The reviewer judged this correct: it matches the spec text and how hand trackers define the
  aggressor. C-bet is not part of the fidelity check either.

## Findings
1. **should-fix:** there is no 3-bet-pot test, so the "last pre-flop raise" rule is unguarded.
   The `pre_raises[0]` mutant passed.
2. **optional:** the `pos != "BB"` guard has no test, and its comment is inaccurate. The case
   is reachable only with an all-in small blind.
3. **optional:** the Wilson bounds drift outside [0, 1] by floating-point error.
4. **optional, from the T2 move:** `mypy tools/table_stats.py` flags `Hand` being passed an
   `int | None` id. The gate only type-checks `app/`.
