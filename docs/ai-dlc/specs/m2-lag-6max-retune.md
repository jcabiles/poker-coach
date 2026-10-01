# Spec — M2, retune the LAG at 6-max (plus the board-straight fix) (rev 2, 2026-09-30)

## Bottom line
- **What gets built, in three build commits:**
  1. the 6-max measurement tool learns how often a bot raises when bet into, how big its raises are
     against the bet, and how big its other bets are; the sourced targets are frozen in the same
     commit;
  2. a bug fix at both table sizes: a bot whose own cards add nothing to a straight, flush, full
     house or quads the board already makes now plays that hand like a bluff-catcher, not a monster;
  3. a 6-max-only settings file for the loose-aggressive (LAG) bot (tighter opening ranges by seat,
     smaller raises, fewer raises when bet into), with the results report.
- **How it passes:** the simulated LAG's opening rate by seat matches the sourced figures, its raise
  rate and its share of 4×-or-bigger raises land in their target bands, and 9-max play is unchanged
  apart from hands the bug fix changes, proven hand by hand.
- **What it does not settle:** whether the LAG now *feels* right. The project owner plays about 200
  Challenge hands after merge, and the roadmap box stays unticked until that verdict. As the roadmap
  says: the owner judges both changes together, so a pass is not proof that settings alone suffice;
  the separate commit lets the simulation report each part's share.

- **Roadmap:** `../roadmap/bot-realism-6max.md`, slice M2 (retune the LAG only, at 6-max only).
  Outcome link: it moves one bot toward the north star (every 6-max bot "plays like its type" in the
  owner's 200-hand session) and tests the roadmap's bet that settings changes can fix the bots.
- **Contracts:** `../contracts/m2-lag-6max-retune.md`. Correction to its §E: the 9-max golden harness
  passes one shared random stream through every hand (`test_bot_decisions_golden.py:55-59`), so one
  changed decision moves every later hand. **Evidence:** `../research/bot-realism-6max/m1-baseline.md`
  (M1, the 6-max baseline measurement) and `../reviews/bot-review-200-hands-2026-09-25.md`.
- **Owner decisions (2026-09-30, do not re-ask):**
  - Shape: pre-flop opening ranges plus two raise dials (size and frequency) plus the bug fix.
    Limper play is not in this slice.
  - A board-made hand the bot's cards do not improve is classed **middle pair** (a bluff-catcher).
  - If no verified source exists for the raise stats, the targets are approximate bands.
  - **Openings win:** if the sourced opens push VPIP or PFR just under their floors, the miss is
    reported as a known gap and does not block the PR.
  - **The LAG opening fewer hands than the unchanged TAG from LJ and HJ is accepted for now.** The
    report shows it, and the post-merge verdict records whether each bot's type is still nameable.
  - **Raise size is judged on its tail:** raises of 4× the bet or more fall from about 22% to at most
    10%. The LAG's leads and probe bets get smaller too, because they share the same sizing block.
  - The owner's 200-hand verdict happens after merge.
  - Close-out of the merged M1 and M1b working files is deferred to the cleanup project's
    docs-distillation slice.
- **Review:** `../ledger/bot-realism-6max.md`, created by this slice. It is the roadmap's ledger,
  which the merge guard reads (`merge-guard.py` reads `ledger/<active>.md`). Rev 2 folds in round 1's
  26 findings.

## 1. What changes

| File | Change | Commit |
|---|---|---|
| `backend/tools/table_stats.py` | A new `raise_multiples` function beside `stats_for`, sharing its row-walking helpers, plus the non-aggressor bet-size measure (§3). `stats_for`'s signature and its four callers stay unchanged. | 1 |
| `backend/tools/sixmax_baseline.py` | `measure()` surfaces the three stats per bot; the printed tables gain their rows. | 1 |
| `backend/tests/test_sixmax_baseline.py`, `backend/tests/test_table_stats.py` | Tests for the three stats on hand-built action sequences. | 1 |
| `docs/ai-dlc/research/bot-realism-6max/m2-lag-retune.md` (new) | Bottom line, sources section and frozen targets (§5). Results are added in commit 3. | 1, 3 |
| `backend/app/domain/personas_postflop.py` | `_made_bucket`: the board-made-hand rule (§4). One function, a few lines. | 2 |
| `backend/tests/test_board_made_hands.py` (new) | Unit tests for the rule (§4). | 2 |
| `backend/tests/test_bot_decisions_golden.py` | Re-pin both digests (commit 2), then the 6-max digest again (commit 3). | 2, 3 |
| `backend/tests/test_personas_postflop.py` | Re-pin `_GOLDEN_STATS_N200` (the review's in-memory run showed it moves), and any other 9-max stat pin that fails, each with a one-line reason. | 2 |
| `content/personas/ladders/six_max/lag.unopened.json` (new) | The 6-max curve spec for the LAG's opening ranges, `emits: content/personas/six_max/lag.json`. | 3 |
| `content/personas/six_max/lag.json` (new) | The first real 6-max override: `preflop.unopened` (emitted from the spec), `postflop.continue_ref`, `postflop.sizing`. | 3 |
| `backend/tests/test_rr_emit.py` | Drift gate, annotation test and strict-monotone test extended to the 6-max spec (§5). | 3 |
| `backend/tests/test_pack_range_lint.py` | Inventory edited only if the new ranges change it. | 3 |
| `docs/ai-dlc/roadmap/bot-realism-6max.md` | M2 entry: built note and measured result; box stays unticked. | 3 |
| `docs/ai-dlc/escapes.md` (new) | Row E1 for the board-straight bug (§9). | 3 |
| `docs/ai-dlc/profile.md` | Remove the committed `## Resume` block (it lives in the git-ignored `local/resume.md`). | 3 |

**Single owners of each new rule:**
- the board-made-hand rule lives only in `personas_postflop._made_bucket`;
- the raise-multiple and non-aggressor bet-size definitions live only in `tools/table_stats.py`, so
  real-session reports and the simulation can share them;
- the LAG's 6-max values live only in `content/personas/six_max/lag.json`, and its opening ranges
  are generated only from `ladders/six_max/lag.unopened.json`.

## 2. Ordering (three build commits)
- **Commit 1, stats and frozen targets.** It changes no decision, so the tool run at commit 1 is the
  before-picture. The targets are committed before any tuning, which makes "pass/fail fixed before
  tuning" provable from history.
- **Commit 2, the fix**, measured alone.
- **Commit 3, the retune and the results report.**
- Each commit leaves `make check` green. Docs-only commits for the spec and ledger sit outside these
  three.

## 3. Commit 1 — three new stats in the measurement tool
- **Raise-when-bet-into rate.** Use `stats_for`'s existing per-street `raise_vs_bet` and `faced_bet`
  counts. Report per bot the flop alone, and flop, turn and river pooled, with Wilson 95% intervals
  (the Wilson score interval, as in M1). The report states the exact definition (any raise when
  `to_call > 0`).
- **Raise size as a multiple of the bet.** For each post-flop raise by the bot:
  `(street_inv_before + amount) / (street_inv_before + to_call)`, from replay rows
  (table_stats.py:160-168). For example, the station's 1.98bb lead raised to 9.45bb is 4.77×. Report
  n, median, mean, 90th percentile, and the share of raises at 4× or more.
- **Non-aggressor bet size.** For each post-flop bet the bot makes when it is not the last
  aggressor (leads, probes, stabs): the bet as a fraction of the pot. Report n and mean. It exists
  to show the side effect of the sizing change (§5).
- No decision changes: both golden digests are unchanged by this commit.

## 4. Commit 2 — the board-made-hand fix (both table sizes)
- **Rule.** In `_made_bucket`, return `StrengthBucket.MIDDLE_PAIR` when all three hold: the best five
  of hole cards plus board is a straight or better (`cat >= 4`); the board has five cards; and
  `_best5(board)` equals that best five. The hole cards then add nothing. Otherwise keep `MONSTER`.
  - Boards with fewer than five cards (the flop's three, the turn's four) are never affected.
  - A hole card that improves the hand at all keeps `MONSTER`. The report names the known near-ties
    this leaves as monsters: a low flush card that only beats the board's fifth card, a quads kicker
    one rank above the board's, and quads on a four-card turn board with a weak kicker.
  - Imitate the board-trips rule at :123-124 and its comment style.
  - Middle pair is not a busted-draw bucket (`postflop_context.py:229-230` needs AIR or ACE_HIGH)
    and does not reach the low stack-to-pot commit (`personas_postflop.py:1887` needs
    OVERPAIR_TPTK or better), so the fix creates no new bluffs or jams.
- **Tests to add, each failing on commit 1 and passing after (→ MIDDLE_PAIR):**
  - AQo on 9♠8♣6♠5♣7♠ (hand #134's board);
  - KJo on 5♠6♥7♣9♣8♠ (hand #30);
  - a hole 6 on 9-8-6-5-7 (in the straight but adds nothing);
  - board quads where the fifth board card is the best kicker;
  - a hole 7 on 8-8-8-7-7.
- **Guard tests to add (stay MONSTER):**
  - a hole T on 5-6-7-8-9;
  - the ace of the suit on a five-card flush board without it;
  - a hole 99 on 8-8-8-7-7;
  - any straight on a four-card board.
- **Re-pin** both golden digests and `_GOLDEN_STATS_N200`; re-pin any other 9-max stat pin only if
  it fails, with the reason.
- **Matched replay: the 9-max attribution check.** The script stays in scratch; the report inlines
  it in an appendix so it can be re-run.
  - **Method.** 4,000 9-max hands derived like `_nine_max_states` (seed 20260927, the same lineup
    and button rotation). Each hand gets its own decision stream, `random.Random(hand_seed + 1)`, in
    place of the shared one, so a change in one hand cannot move another.
  - **Run.** Dump each hand's action fingerprint and export rows on the tree before the fix
    (= commit 1), apply the fix, dump again, compare.
  - **Pass** only if every changed hand's first differing action is a river decision by a bot whose
    hole cards add nothing to a board-made straight or better, and every changed export row lies in
    such a hand.
  - **Report:** hands compared, hands changed (must be above 0, or the check proves nothing), hands
    attributed, hands and rows unattributed (must be 0).
- **Matched replay: the fix's 6-max share.** The same method on 6,000 6-max hands
  (`run_baseline`'s lineup, seed 20260926). Report the hands and decisions changed and the LAG's
  river stats on the matched sample.

## 5. Commit 1 (targets) and commit 3 (settings) — the LAG's 6-max values
- **Sourcing pass, in commit 1, before any tuning.**
  - **What to find:** verified 6-max figures for a LAG's (a) raise rate when bet into post-flop and
    (b) raise size against the bet.
  - **Method (M1's):** fetch every cited page directly; record a `(format, pool, source)` triple;
    label each figure VERIFIED / DERIVED / UNVERIFIED; never put a full-ring figure in a 6-max cell.
  - **Matching definitions only.** A source counts only if its definition matches the tool's stat.
    A "raise flop c-bet" or "check-raise flop" figure may be compared with the flop-only rate, or
    used as approximate; it is never compared with the pooled rate.
  - **Output:** the report's sources section plus the frozen targets (§7). The targets freeze when
    commit 1 lands.
- **Opening ranges.**
  - **Seats.** Author `ladders/six_max/lag.unopened.json` in the format of `ladders/lag.unopened.json`,
    with the same tier ladder (the LAG's edge identity). Use the seats LJ, HJ, CO, BTN, SB and BB,
    with BB copied from the base spec and no UTG seats; `monotone_seats` is LJ, HJ, CO, BTN.
  - **Depths and annotations.** Depths are authored per row, never fitted by a width scalar.
    `raise_pct` equals the emitted width (rr_emit's annotation contract, ±0.005); the sourced targets
    go in `_doc`.
  - **Emit and paste.** Run `cd backend && PYTHONPATH=. .venv/bin/python -m tools.rr_emit ../content/personas/ladders/six_max/lag.unopened.json`
    and paste the nodes into the override's `preflop.unopened`. Do not change rr_emit.
  - **Targets.** The target is the measured RFI (raise first in: the share of hands opened when
    everyone before has folded): LJ 20, HJ 23, CO 33, BTN 50, SB 43. The authored width may differ
    from the target where calibration requires, which matters most at SB.
  - **Calibration.** Calibrate on pooled seeds 1–5 (6,000 hands each), never on the judged seed
    20260926.
- **Raise size.** Override `postflop.sizing` (the flat block, replaced whole) toward 0.33 and 0.5.
  - At a one-third-pot lead the multiple is about `1 + 5f`: 0.33 gives 2.7×, 0.5 gives 3.5×.
  - The block must keep at least 0.10 on small (0.33), medium (0.5) and large (0.75 + 1.0), and must
    pass every size-ecology gate at 6-max.
  - **Side effect, accepted by the owner:** this block also sizes the LAG's leads, probes and stabs,
    which shrink too.
  - Do not touch `sizing_by_node` (its `raise` node is never read by bots) or the pre-flop `sizing`
    block (LAG pins 3.0 / 3.5 / 2.4).
- **Raise frequency.** Raise `postflop.continue_ref` (facing nodes only; c-bets unaffected; allowed
  range [0.05, 8.0]).
- **Starting point (review evidence, in-memory):** `continue_ref` 2.0 with flat sizing
  {0.33: 0.45, 0.5: 0.35, 0.75: 0.10, 1.0: 0.10} gave a raise-when-bet-into rate of 16.4%
  (14.2–18.9%) and a median of 2.66×, and passed every size-ecology and pack-invariant test at 6-max.
- **No other dial moves.** If the targets cannot be met with these three changes, stop and report.
  Do not reach for `aggression`, `bluff_freq` or any other dial.
- **Override file.** `id`, `version` (start `1.0.0`), `domain: "persona_override"`,
  `persona: "lag"` and `table_size: 6`, plus a `_doc` that cites the source triple (or
  "approximate") for every value and states that leads and probes shrink with the sizing block.
- **Drift gate.** Extend `test_rr_emit.py`:
  - the override's `preflop.unopened` must equal what the 6-max spec emits;
  - the spec's `emits` resolution is pinned to `content/personas/six_max/lag.json`, the same guard
    the base spec has at :319-330;
  - the annotation test and the strict-monotone test also run on the 6-max spec.
- **Re-pin** the 6-max golden digest. The whole 9-max golden digest must equal commit 2's.
- **Matched replay: the retune's share.** The §4 6-max method, run on the tree before and after
  the retune.

## 6. The report (`docs/ai-dlc/research/bot-realism-6max/m2-lag-retune.md`)
- **Form.** Opens with a `## Bottom line` and follows the M1 report's conventions: Wilson intervals;
  "inside" means the simulated 95% interval overlaps the cited range or contains the cited point;
  the point estimate is always shown beside the verdict.
- **Judged runs.** `sixmax_baseline` at commits 1 and 3 with M1's settings: 6,000 hands, seed
  20260926, real session `4b35736f…` up to hand 201, and the database in the main checkout. Each
  run twice; the two outputs must be byte-identical.
- **Each part's share** comes from the matched replays (§4, §5). Commit-level deltas also appear but
  are labelled as dominated by reshuffled hands.
- **Tables:**
  - per-bot tables for all five bots and the stand-in, with every stat including the three new ones;
  - a LAG-versus-TAG opening table by seat (the separation guard);
  - the LAG's non-aggressor bet size before and after.
- **Also in the report:**
  - the §7 pass/fail table, the 9-max attribution result, and the §4 known near-ties;
  - the matched-replay script, inlined in an appendix;
  - other bots' stats will shift because they face a different LAG; report it, judge nothing on it.

## 7. Pass/fail (frozen in commit 1; judged on the commit-3 run unless stated)
1. **Opening rates.** LAG RFI at LJ, HJ, CO, BTN and SB: the simulated 95% interval contains 20, 23,
   33, 50 and 43.
2. **VPIP and PFR (reported, not blocking — owner ruling).** LAG VPIP against 24–40 and PFR against
   20–35, M1's combined cited ranges. A miss is recorded as a known gap.
3. **Raise rate when bet into.** The LAG's rate, flop, turn and river pooled, needs at least 300
   faced bets. Its 95% interval must overlap a definition-matched sourced range, else the
   approximate band 10–20%. Fewer than 300 faced bets is inconclusive, which counts as a fail.
4. **Raise size** (approximate unless sourced). The LAG's share of raises at 4× the bet or more must
   be at most 10% (baseline about 22%), and its median must sit inside 2.5–3.5×. It needs at least
   100 raises; fewer is inconclusive, which counts as a fail.
5. **9-max unchanged.** The commit-2 matched replay has more than 0 changed hands and 0 unattributed
   hands and rows, and commit 3's 9-max golden digest equals commit 2's.
6. **No other bot touched.** `git diff` over `content/personas/` shows only the two new LAG files.

**Reported, not judged:**
- LAG flop c-bet and WTSD (went to showdown) have no sourced range. They stay outstanding, so the
  report may not claim the roadmap's full supporting check passed.

**Not judged here:** the owner's 200-hand verdict (the roadmap's third pass/fail line). It includes
the separation guard: whether the owner can still name each bot's type.

## 8. Changed contracts and how dependents are regenerated
- **Bot decisions.** The fix changes them at both table sizes; the retune at 6-max only. Golden
  digests and `_GOLDEN_STATS_N200` are re-pinned in the same commit.
- **The LAG's 6-max leads, probes and stabs** get smaller, through the shared flat sizing block. The
  owner accepted this; the PR states it.
- **Villain-range view.** `range_estimate.py` reads the same bucket, so board-made hands now estimate
  as middle pair. No test pins the old value.
- **Analytics export.** The Parquet `hand_class_bucket` value for board-made hands changes from
  `monster|…` to `middle_pair|…`, with no schema change. The PR body states it for the analytics
  repo.
- **Persona content.** Every 6-max-parametrised settings test validates the new override. The
  range-lint inventory is edited in the same commit if it moves.
- **Untouched:** no migration, no FE type change, and `spot_signature()` stays as it is.

## 9. Bookkeeping in commit 3
- **`docs/ai-dlc/escapes.md`**, created with row E1:
  - found 2026-09-25 by the blind 200-hand review;
  - defect: "a straight or better the board makes alone is classed as a monster";
  - path `reviewed`;
  - commits `7718c0d` (PR #30) → `PR #<this PR>`;
  - category: logic bug;
  - question that should have caught it: "does the hand class credit the bot for cards that play
    for everyone?";
  - asked: no;
  - promoted to the §4 unit tests.
- **Roadmap M2 entry:** built note, measured result and assumption status; the box stays unticked.
- **`profile.md`:** the `## Resume` block is removed.

## 10. Test seams
- **Board rule:** call `strength_bucket` / `_made_bucket` directly with literal cards, as
  `test_mw_catch_toppair.py:185` does. No mocks.
- **Stats:** feed `stats_for` and `raise_multiples` hand-built replay rows; feed `measure()` a small
  deterministic `run_baseline` sample.
- **Override:** load through `load_persona_packs(table_size=6)` with the real files. The drift test
  calls `rr_emit.emit_nodes` on the committed spec.
- **Decisions:** the golden digests and the matched replays, with the real engine and fixed seeds.

## 11. Constraints (repo invariants that apply)
- `backend/app/domain/` stays free of web and database imports.
- Strategy lives in versioned `content/` data; the only code change to decisions is §4.
- `spot_signature()` is frozen; nothing here touches it.
- Results stay frequency plus EV; grading stays behind the one `StrategyProvider`, untouched.
- No new dependency.
- No file grows past ~500 lines without being flagged. `personas_postflop.py`, `sim_session.py`
  and `test_personas_postflop.py` are already far over; add nothing avoidable, so new tests go in
  new files.
- Committed text never names the repo owner; write "the project owner" where a person must be named.

## 12. Golden-path pointers
- **Board rule:** the board-trips branch and the F7 comment at `personas_postflop.py:123-140`.
- **Override file:** the fixture override in `backend/tests/persona_override_fixture.py`.
- **Curve spec:** `content/personas/ladders/lag.unopened.json`.
- **Drift, annotation and monotone tests:** the base-LAG block at `backend/tests/test_rr_emit.py:313-436`.
- **New stats:** the `raise_vs_bet` accumulation at `table_stats.py:289-301`.
- **Report:** `docs/ai-dlc/research/bot-realism-6max/m1-baseline.md`.

## 13. Out of scope
- limper play (the roadmap's NEXT item);
- any other bot's settings, the TAG's opens included;
- `spr_commit` and stack-depth behaviour (the deep-stack lane waits on R1, the stack-depth research);
- opponent-aware logic ("raise the station less" needs code);
- `aggression`, `bluff_freq` and any dial not named in §5;
- splitting oversized files;
- the 9-max tools;
- committing the matched-replay script as a tool;
- the owner's 200-hand session.

## 14. Verify-by
From the worktree:
- `make check` is green at every commit;
- the §6 judged runs at commits 1 and 3 are each run twice and are byte-identical;
- the §4 and §5 matched replays are run;
- the report's pass/fail table shows every §7 item.

## 15. Definition of Done
- §7 items 1, 3, 4, 5 and 6 pass, and item 2 is reported;
- `make check` exits clean at the final commit;
- nothing outside §1's files changed;
- every doc this change invalidates is updated in the same change;
- every measured claim names its conditions: seed, hands, stacks of 95–105bb, commit.

A §7 item that cannot be met is recorded as an `open: awaiting project owner` ledger row, which
blocks the PR. The owner's 200-hand verdict is the roadmap's check, not this PR's; the PR lists it
under "Not in this PR".
