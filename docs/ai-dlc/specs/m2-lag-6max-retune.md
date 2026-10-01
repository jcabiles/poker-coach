# Spec — M2, retune the LAG at 6-max (plus the board-straight fix) (rev 1, 2026-09-30)

## Bottom line
- **What gets built, in three commits:**
  1. the 6-max measurement tool learns two stats: how often a bot raises when bet into, and how big
     its raises are as a multiple of the bet;
  2. a bug fix at both table sizes: a bot whose own cards add nothing to a straight, flush, full
     house or quads the board already makes now plays that hand like a bluff-catcher, not a monster;
  3. a 6-max-only settings file for the loose-aggressive (LAG) bot: tighter opening ranges by seat,
     smaller raises, and fewer raises when bet into.
- **How it passes:** the simulated LAG's opening rate by seat matches the sourced figures, its
  overall play and raise rates stay in their sourced ranges, its two raise stats land in their
  target bands, and 9-max play is unchanged apart from hands the bug fix changes.
- **What it does not settle:** whether the LAG now *feels* right. The project owner plays about 200
  Challenge hands after merge, and the roadmap box stays unticked until that verdict.

- **Roadmap:** `../roadmap/bot-realism-6max.md`, slice M2 (retune the LAG only, at 6-max only).
  Outcome link: it moves one bot toward the north star (every 6-max bot "plays like its type" in
  the owner's 200-hand session) and tests the roadmap's bet that settings, not decision code, fix
  the bots.
- **Contracts:** `../contracts/m2-lag-6max-retune.md`. **Evidence:** `../research/bot-realism-6max/m1-baseline.md`
  (M1, the 6-max baseline measurement) and `../reviews/bot-review-200-hands-2026-09-25.md`.
- **Owner decisions (2026-09-30, do not re-ask):**
  - Shape: pre-flop opening ranges plus two raise dials (size and frequency) plus the bug fix.
    Limper play is not in this slice.
  - A board-made hand the bot's cards do not improve is classed **middle pair** (a bluff-catcher:
    calls modest bets, rarely raises).
  - If no verified source exists for the two raise stats, the targets are **approximate bands**:
    raise-when-bet-into 10–20%, median raise 2.5–3.5× the bet.
  - The owner's 200-hand verdict happens after merge.
  - Close-out of the merged M1 and M1b working files is deferred to the cleanup project's
    docs-distillation slice (its rule: nothing is deleted before `docs/FINDINGS.md` is exhaustive).
- **Review:** `../ledger/bot-realism-6max.md` (the roadmap's ledger, which the merge guard reads).

## 1. What changes

| File | Change | Commit |
|---|---|---|
| `backend/tools/table_stats.py` | `stats_for` gains the raise-multiple accumulation (§3). The existing `{street}_raise_vs_bet` / `{street}_faced_bet` counts are reused unchanged. | 1 |
| `backend/tools/sixmax_baseline.py` | `measure()` surfaces both stats per bot; the printed tables gain two rows. | 1 |
| `backend/tests/test_sixmax_baseline.py` (and the existing `table_stats` test module) | Tests for both stats on hand-built action sequences. | 1 |
| `backend/app/domain/personas_postflop.py` | `_made_bucket`: the board-made-hand rule (§4). One function, a few lines. | 2 |
| `backend/tests/test_personas_postflop.py` (or a new `test_board_made_hands.py` if that file cannot take more) | Unit tests for the rule (§4). `test_personas_postflop.py` is far over 500 lines; prefer the new file. | 2 |
| `backend/tests/test_bot_decisions_golden.py` | Re-pin both digests (commit 2), then the 6-max digest again (commit 3). | 2, 3 |
| Any 9-max stat pin that the fix moves (`_GOLDEN_STATS_N200`, `BANDS` in `test_personas_postflop.py`) | Re-pin only if it fails, with a one-line reason at the pin. | 2 |
| `content/personas/ladders/six_max/lag.unopened.json` (new) | The 6-max curve spec for the LAG's opening ranges, `emits: content/personas/six_max/lag.json`. | 3 |
| `content/personas/six_max/lag.json` (new) | The first real 6-max override: `preflop.unopened` (emitted from the spec), `postflop.continue_ref`, `postflop.sizing`. | 3 |
| `backend/tests/test_rr_emit.py` | The drift gate extended to the 6-max spec and override (§5). | 3 |
| `backend/tests/test_pack_range_lint.py` | Inventory edited only if the new ranges change it (exact-equality inventory). | 3 |
| `docs/ai-dlc/research/bot-realism-6max/m2-lag-retune.md` (new) | Sources section (written before tuning), then results (§6). | 3, 4 |
| `docs/ai-dlc/roadmap/bot-realism-6max.md` | M2 entry: built note and measured result; box stays unticked. | 4 |
| `docs/ai-dlc/escapes.md` (new) | Row E1 for the board-straight bug (§9). | 4 |
| `docs/ai-dlc/profile.md` | Remove the committed `## Resume` block (it moves to the git-ignored `local/resume.md`). | 4 |

**Single owners of each new rule:**
- the board-made-hand rule lives only in `personas_postflop._made_bucket`;
- the raise-multiple definition lives only in `table_stats.stats_for`, so real-session reports and
  the simulation share it;
- the LAG's 6-max values live only in `content/personas/six_max/lag.json`, and its opening ranges
  are generated only from `ladders/six_max/lag.unopened.json`.

## 2. Ordering (why three commits, in this order)
Commit 1 (stats) changes no decision, so running the tool at commit 1 gives the before-picture
with the new stats. Commit 2 (fix) is then measured alone, and commit 3 (retune) on top. This is
what lets the report give each part's share, as the roadmap requires. Each commit leaves
`make check` green.

## 3. Commit 1 — two new stats in the measurement tool
- **Raise-when-bet-into rate.** Use `stats_for`'s existing per-street `raise_vs_bet` and
  `faced_bet` counts, state their exact definition in the report, and report per bot: flop alone,
  and flop, turn and river pooled. Wilson 95% interval as for every other stat.
- **Raise size as a multiple of the bet.** For each post-flop raise by the bot: its street total
  after raising divided by the street total it faced (`current_bet_to` at that decision; the
  station's 1.98bb lead raised to 9.45bb is 4.8×). Derived from replay rows (`amount`, `to_call`,
  `street_inv_before`, table_stats.py:160-168). Report n, median and mean per bot.
- No decision changes: both golden digests are unchanged by this commit.

## 4. Commit 2 — the board-made-hand fix (both table sizes)
- **Rule.** In `_made_bucket`, when the best five of hole cards plus board is a straight or better
  (`cat >= 4`) **and** the board has five cards **and** `_best5(board)` equals that best five, the
  hole cards add nothing, so return `StrengthBucket.MIDDLE_PAIR`. Otherwise keep `MONSTER`.
  - Four-card boards (flop, turn) are never affected: with fewer than five board cards a hole card
    always plays.
  - A hole card that improves the hand at all, even slightly (a higher straight, a bigger flush card,
    a better quads kicker), keeps `MONSTER`. That is the literal rule; finer grading is not in this
    slice.
  - Imitate the existing board-trips rule at :123-124 and its comment style (state the constraint,
    cite one example hand).
  - Middle pair is not a busted-draw bucket (`postflop_context.py:229-230` needs AIR or ACE_HIGH),
    so the fix creates no new river bluffs.
- **Tests (each fails on `main`, passes after):**
  - AQo on 9♠8♣6♠5♣7♠ (hand #134's board) → MIDDLE_PAIR;
  - KJo on 5♠6♥7♣9♣8♠ (hand #30) → MIDDLE_PAIR;
  - a hole 6 on 9-8-6-5-7 → MIDDLE_PAIR (in the straight but adds nothing);
  - board quads with the fifth board card the best kicker → MIDDLE_PAIR.
- **Tests that must keep passing unchanged (prove no over-reach):** a hole T on 5-6-7-8-9 → MONSTER;
  the ace of the board's flush suit on a five-flush board → MONSTER; any straight on a four-card
  board → MONSTER.
- **Re-pin** both golden digests. Re-pin a 9-max stat pin only if it fails, with the reason.
- **9-max attribution check (one-shot; the script stays in scratch, its result goes in the report).**
  Compute `per_hand_digests(9)` at commit 1 and at commit 2. For every hand that differs, replay
  both versions and find the first differing action. It passes only if every such action is a
  river decision by a bot whose hole cards add nothing to a board-made straight or better.
  Report: hands compared, hands changed, hands attributed, hands unattributed (must be 0).
  - If the 9-max harness turns out to share one random-number stream across hands (so one change
    moves later hands), stop and report rather than loosen the check.

## 5. Commit 3 — the LAG's 6-max settings
- **Before any tuning: the sourcing pass.** Look for verified 6-max figures for a LAG's (a) raise
  rate when bet into post-flop and (b) raise size as a multiple of the bet, under the M1 method
  (direct fetch of every cited page, `(format, pool, source)` triple, VERIFIED / DERIVED /
  UNVERIFIED labels; a full-ring figure never enters a 6-max cell). Write the result as the
  report's sources section, together with the frozen targets below. **Targets freeze when the
  sources section is committed; tuning starts after.**
- **Opening ranges.** Author `ladders/six_max/lag.unopened.json` in the same format as
  `ladders/lag.unopened.json` (same tier ladder, which is the LAG's edge identity), with
  `raise_pct` annotations equal to the targets LJ 20, HJ 23, CO 33, BTN 50, SB 43. Depths are
  authored per row, never fitted by a width scalar (rr_emit.py's docstring). Emit with
  `python -m tools.rr_emit` and paste the nodes into the override's `preflop.unopened`. If
  `rr_emit`'s validation requires all nine seats, give UTG, UTG1 and UTG2 the LJ depths (never
  dealt at 6-max). Do not change `rr_emit`'s curve model. SB's authored share and its measured RFI
  differed by about 5 points in M1, so calibrate SB by the simulation.
- **Raise size.** Override `postflop.sizing` (the flat block, replaced whole) toward 0.33 and 0.5.
  At a one-third-pot lead the multiple is about `1 + 5f` (0.33 → 2.7×, 0.5 → 3.5×). It must keep at
  least 0.10 on small (0.33), medium (0.5) and large (0.75 + 1.0), and pass every size-ecology
  gate at 6-max. Do not touch `sizing_by_node` (its `raise` node is never read by bots) or the
  pre-flop `sizing` block (its LAG pins are 3.0 / 3.5 / 2.4).
- **Raise frequency.** Raise `postflop.continue_ref` (facing nodes only; c-bets unaffected).
  Allowed range [0.05, 8.0].
- **No other dial moves.** If the targets cannot be met with these three changes, stop and report;
  do not reach for `aggression`, `bluff_freq` or any other dial.
- **Override file:** `id`, `version` (start `1.0.0`), `domain: "persona_override"`,
  `persona: "lag"`, `table_size: 6`, and a `_doc` that cites the source triple (or "approximate")
  for every value.
- **Drift gate.** Extend `test_rr_emit.py` so the override's `preflop.unopened` must equal what
  the 6-max spec emits, with the spec's `emits` resolution pinned to
  `content/personas/six_max/lag.json` (the same guard the base spec has at :319-330).
- **Re-pin** the 6-max golden digest. The 9-max per-hand digests must equal commit 2's exactly.

## 6. The report (`docs/ai-dlc/research/bot-realism-6max/m2-lag-retune.md`)
Opens with a `## Bottom line`. Same conventions as the M1 report (Wilson intervals; "inside" means
the simulated 95% interval overlaps the cited range or contains the cited point).
- **Runs:** `sixmax_baseline` at commits 1, 2 and 3 with M1's settings (6,000 hands, seed
  20260926, real session `4b35736f…` up to hand 201, the database in the main checkout). Each run
  twice; the outputs must be byte-identical.
- **Per-bot tables** for all five bots and the stand-in, every stat including the two new ones, at
  each commit. The LAG's change from commit 1 → 2 is the fix's share; 2 → 3 is the retune's.
- **Pass/fail table** for §7, the 9-max attribution result (§4), the sources section (§5).
- Other bots' stats will shift because they face a different LAG and the fix; report it, judge
  nothing on it.

## 7. Pass/fail (fixed now, judged on the commit-3 run)
1. LAG RFI at LJ, HJ, CO, BTN, SB: the simulated 95% interval contains 20, 23, 33, 50, 43.
2. LAG VPIP inside 24–40 and PFR inside 20–35 (M1's combined cited ranges).
3. LAG raise-when-bet-into rate (flop, turn and river pooled): its 95% interval overlaps the sourced
   range if the sourcing pass found one, else the approximate band 10–20%.
4. LAG median raise multiple inside the sourced range, else the approximate band 2.5–3.5×.
5. 9-max: the attribution check at commit 2 has 0 unattributed hands, and commit 3's 9-max
   per-hand digests equal commit 2's.
6. No other bot's settings file changes (`git diff` over `content/personas/` shows only the two new
   LAG files).
- If items 1 and 2 conflict (tight enough opens push PFR below 20), report it and do not loosen the
  opens to rescue PFR: the stats are the supporting check, and the owner's verdict decides.
- **Not judged here:** the owner's verdict. The roadmap's third pass/fail line waits for the
  post-merge session.

## 8. Changed contracts and how dependents are regenerated
- **Bot decisions** (both sizes for the fix; 6-max only for the retune) → golden digests re-pinned in
  the same commit; 9-max stat pins re-pinned only on failure, each with its reason.
- **Villain-range view** (`range_estimate.py` reads the same bucket) → board-made hands now estimate
  as middle pair; no test pins the old value.
- **Analytics export** → the Parquet `hand_class_bucket` value for board-made hands changes from
  `monster|…` to `middle_pair|…`; no schema change. The PR body states it for the analytics repo.
- **Persona content** → the new override is validated by every 6-max-parametrised settings test;
  the range-lint inventory is edited in the same commit if it moves.
- **No migration, no FE type change, `spot_signature()` untouched** (contracts §D).

## 9. Bookkeeping in commit 4
- `docs/ai-dlc/escapes.md` created with row E1: found 2026-09-25 by the blind 200-hand review;
  defect "a straight or better the board makes alone is classed as a monster"; path `reviewed`;
  commits `7718c0d` (PR #30) → `PR #<this PR>`; category logic bug; question "does the hand class
  credit the bot for cards that play for everyone?"; asked no; promoted to the §4 unit tests.
- Roadmap M2 entry: built note, measured result, assumption status; the box stays unticked.
- `profile.md`: the `## Resume` block is removed (it lives in the git-ignored `local/resume.md`).

## 10. Test seams
- Board rule: call `strength_bucket` / `_made_bucket` directly with literal cards (as
  `test_mw_catch_toppair.py:185` already does). No mocks.
- Stats: feed `stats_for` hand-built replay rows; feed `measure()` a small deterministic
  `run_baseline` sample.
- Override: load through `load_persona_packs(table_size=6)` (real files); the drift test calls
  `rr_emit.emit_nodes` on the committed spec.
- Decisions: the golden digests and the per-hand attribution replay; real engine, real seeds.

## 11. Constraints (repo invariants that apply)
- `backend/app/domain/` stays free of web and database imports.
- Strategy lives in versioned `content/` data; the only code change to decisions is §4.
- `spot_signature()` is frozen; nothing here touches it.
- Results stay frequency plus EV; grading stays behind the one `StrategyProvider` (untouched).
- No new dependency. No file grows past ~500 lines without being flagged (`personas_postflop.py`,
  `sim_session.py` and `test_personas_postflop.py` are already far over; add nothing avoidable).
- Committed text never names the repo owner; "the project owner" where a person must be named.

## 12. Golden-path pointers
- Board rule: the board-trips branch and the F7 comment at `personas_postflop.py:123-140`.
- Override file: the fixture override in `backend/tests/persona_override_fixture.py`.
- Curve spec: `content/personas/ladders/lag.unopened.json`.
- Drift gate: the base-LAG block at `backend/tests/test_rr_emit.py:313-398`.
- Stat in `stats_for`: the existing `raise_vs_bet` accumulation at `table_stats.py:289-301`.
- Report: `docs/ai-dlc/research/bot-realism-6max/m1-baseline.md`.

## 13. Out of scope
Limper play (the roadmap's NEXT item), any other bot's settings, `spr_commit` and stack-depth
behaviour (the deep-stack lane waits on R1, the stack-depth research), opponent-aware logic
("raise the station less" needs code), `aggression` / `bluff_freq` / any dial not named in §5,
splitting oversized files, the 9-max tools, and the owner's 200-hand session.

## 14. Verify-by
From the worktree: `make check` green at every commit. Then the §6 runs at commits 1, 2 and 3, each
twice and byte-identical, and the §4 attribution check at commit 2. The report's pass/fail table
shows every §7 item.

## 15. Definition of Done
All §7 items 1–6 pass (or a conflict is reported per §7's rule and recorded as an `open: awaiting
project owner` ledger row, which blocks the PR) AND `make check` exits clean at the final commit
AND nothing outside §1's files changed AND every doc this change invalidates is updated in the same
change AND every measured claim names its conditions (seed, hands, stacks 95–105bb, commit). The
owner's 200-hand verdict is the roadmap's check, not this PR's; it is listed under the PR's "Not in
this PR".
