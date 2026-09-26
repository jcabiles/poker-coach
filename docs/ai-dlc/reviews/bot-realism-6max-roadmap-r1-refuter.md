# Bot Realism at 6-max roadmap — blind review, round 1 (2026-09-25)

**Bottom line:** the reviewer approved the draft with fixes. All three blocking findings were
verified against the code and accepted. Two of them need owner rulings. Of the remaining
findings, four were folded in, one was treated as a date correction, and one was dropped.

- **Reviewer:** Claude `refuter` on Opus. This is the labelled fail-open fallback, a same-family
  reviewer: Codex is installed but cannot run inside this repo's sandbox.
- **Input:** blind — the roadmap and the repo only, without the interview record.
- **Verdict:** approve-with-fixes.

## Findings and adjudication

**1. Blocking — ACCEPTED (verified).**
- **Finding:** the "LAG first-seat contradiction" does not exist.
- **Evidence:** at 6-max the first seat is LJ (`deck.py:34-38`), and the LAG's LJ `raise_pct` is
  37.62 in `lag.unopened.json`, which matches the observed 39%. The draft's "15–19%" was a
  misread of that file's changelog notes.
- **Action:** fixed in the Evidence section. The seat-bug branches were removed from M1 and M2.

**2. Blocking — ACCEPTED (verified).**
- **Finding:** no 6-max-only settings path exists.
- **Evidence:** one pack per persona, with no format selection in `bot_decision`
  (`personas.py:41-54`, `play.py:234`). `(format, pool, source)` is a provenance check, not an
  override.
- **Action:** added slice M1b (settings that can differ by table size). Whether to build it, or
  to accept that 9-max changes, is an owner ruling.

**3. Blocking — ACCEPTED (verified).**
- **Finding:** some all-ins come from code, not settings.
- **Evidence:** `_made_bucket` returns MONSTER for any straight or better, including one the
  board makes alone (`personas_postflop.py:121-122`). Retuning cannot fix it.
- **Action:** added to Evidence. Including the fix in M2 is an owner ruling, because it touches
  every bot and changes 9-max.

**4. Should-fix — ACCEPTED.**
- **Finding:** M1's cheapest test was too loose.
- **Action:** pre-registered the three stats (VPIP, PFR, flop c-bet), a confidence-interval rule
  and a failure threshold (2 or more of 15 comparisons outside the interval), and named the
  stand-in hero (a TAG).

**5. Should-fix — ACCEPTED.**
- **Finding:** the simulator starts every seat at 95–105bb, so a count of stacks over 150bb
  would come back near zero.
- **Action:** that metric moved to the deep-stack lane, and M1 runs at the existing spread.

**6. Should-fix — ACCEPTED.**
- **Finding:** no slice sources the real 6-max ranges.
- **Action:** sourcing them with provenance is now an M1 deliverable.

**7. Should-fix — ACCEPTED.**
- **Finding:** the `active:` pointer and the flywheel close were not stated.
- **Action:** added a Bookkeeping section. The switch of `active:` awaits the owner.

**8. Optional.**
- **Separation-guard test — ACCEPTED as a one-line clarification:** it is checked through the
  owner's verdict.
- **Dates — ACCEPTED:** corrected to 2026-09-25, the owner's local date. The session's
  timestamps are UTC, which is why they read as the 26th.
