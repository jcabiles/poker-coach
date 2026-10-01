# Whole-branch review, interaction lens (Claude `refuter`, Opus), branch head ee93bd7, 2026-10-01

Raw report as returned by the reviewer.

**Verdict: FAIL.** One major issue blocks a pass, and it is fixable with a docs-only edit. The code and content interactions hold up. The board-made-hand rule has one home and every consumer handles it. The 6-max override merges as intended, and 9-max reads nothing new. The results report, though, understates how far the retune blurs the LAG with the other bots.

**Checks run:** 160 targeted tests passed (board-made hands, rr_emit, table_stats, sixmax_baseline, golden digests, override, pack invariants, size ecology, table-size packs). I re-ran the judged simulation (6,000 hands, seed 20260926) and reproduced the report's LAG and TAG figures exactly.

## Issues

1. **major**, `docs/ai-dlc/research/bot-realism-6max/m2-lag-retune.md:200,311` and `docs/ai-dlc/roadmap/bot-realism-6max.md:189`
   - **Finding:** The separation write-up covers only pre-flop overlap (opening rate and PFR). After the retune the LAG's post-flop raising is below the unchanged TAG's and level with the nit's. The roadmap's separation guard ("fixes must not blur the types") rests on the project owner's verdict, and that verdict depends on this report.
   - **Evidence (my re-run):** raise when bet into: LAG 18.1% [15.6, 20.8], TAG 23.6% [21.5, 25.9], nit 18.2%. Raises of 4× or more: LAG 5.9%, TAG 25.9%. Median raise multiple: LAG 2.66×, TAG 3.00×. The numbers appear in the §2 table, but no conclusion states them.
   - **Fix:** Add one line to §4, §9 and the roadmap's known gaps. Gain: the owner's verdict is made with the full picture. Cost: about 3 lines of docs. Whether this is acceptable is the project owner's call.
2. **minor**, `backend/app/domain/postflop.py:271-274` (the "same bug nearby" search)
   - **Finding:** The hero-side grader `_hand_category` still calls any straight or flush across hole plus board "strong", even when the board makes it alone. The bot rule now says "bluff-catcher" for the same hand, so the two classifiers disagree. It feeds `grade_river_barrel` (:1631) and `grade_vs_river_bet` (:1750).
   - **Evidence:** `_hand_category(('Ac','2d'), [2h 5h 8h Jh Kh])` returns `strong`. It is latent: the project's CLAUDE.md says the river graders are not reached yet (the parked coverage issue).
   - **Fix:** A follow-up ticket, not this branch, because the roadmap bars other engine changes.
3. **optional**, `backend/app/domain/personas_postflop.py:123`
   - **Finding:** Two nearby cases still class MONSTER: a low hole flush card that barely beats a board flush (4h on Ah Kh Qh Jh 3h); quads on a four-card turn board with a hole-card kicker (Qd on 8888).
   - **Evidence:** Both confirmed by `strength_bucket`. The spec allows the first ("any improvement keeps MONSTER"). Both are rare.
4. **optional**, `content/personas/six_max/lag.json` (postflop sizing)
   - **Finding:** Dropping the 1.0 size lowers the bluff weighting on the LAG's leads and raises when it is not the aggressor. The size-weighted bluff factor goes from 1.022 to 0.954, about 7% fewer bluffs there. The file's notes do not mention it.
5. **optional**, `backend/tools/sixmax_baseline.py:435`
   - **Finding:** `POSTFLOP_STREETS` repeats a street tuple that `table_stats.stats_for` (:285) already writes inline.

## Interaction questions answered

- **(a) Who reads the old MONSTER class:** The villain-range view, the river "busted draw" context and the analytics export all read `strength_bucket`. Each handles MIDDLE_PAIR. The export contract's allowed values are unchanged, and only one poker-analytics artifact mentions `monster`. The four re-pinned 9-max pins are the only tests that relied on the old class.
- **(b) Override merge:** The whole `unopened` facing is replaced. BB is byte-equal to the base pack, and only one new open appears (T7o on the button, at weight 0.4). `sizing` is replaced whole. The `sizing_by_node.raise` node really is never read: a bot facing a bet cannot be the last aggressor. The size-ecology and pack-invariant tests run at 6-max and pass.
- **(c) 9-max:** Overrides load only at table size 6. The non-recursive file scans never read `ladders/six_max`, and the 9-max digest is unchanged in commit 3.
- **(d) Stats tool:** `stats_for` is unchanged. The new functions only add to it, and the fidelity check reads only tuple rows.

## Stated requirements the branch does not carry

- **Spec §7 item 1:** the LAG's CO opening rate misses on the judged seed (28.5% [25.2, 32.1] against 33). It rests on a project-owner waiver dated 2026-10-01 that only the report records. Awaiting project owner confirmation.
- **Owner decision "LAG opening fewer hands than the TAG is accepted at LJ and HJ":** on the judged seed the LAG also opens less at CO (28.5% against 32.7%), which that ruling does not cover. The report discloses this.

## What I could not check

- The matched-replay proof for item 5: its script lives only in the report's appendix and scratch, and I did not re-run it.
- Whether the waiver is genuine.
- The project owner's 200-hand verdict.
- A downstream poker-analytics re-ingest.
