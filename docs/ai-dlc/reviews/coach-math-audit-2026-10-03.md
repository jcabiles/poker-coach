# Coach math and table realism audit — 2026-10-03

**Bottom line.**
- **The coach teaches some wrong lessons.** It misreads the wheel straight and board-made hands, prices calls with the wrong formula, and ignores stack depth.
- **The bot table is shaped like an online game,** not a live $1/$2 card room.
- **The engine has one betting-rule bug.**

Three read-only audits found these issues. Nine independent refuters (six Codex, two Opus, one Sonnet) then checked them, and most of the refuters ran the code. Every finding below survived that check, or was corrected by it as noted. The `coach-math` and `bot-realism-6max` roadmaps cite this record.

## How it was checked
- **The grounding.** Each refuter got the same primer of No-Limit Hold'em (NLHE) math and live low-stakes facts, plus the numbered claims.
- **Run commands where possible.** Each refuter was told to run code where it could and to label evidence "ran" or "read". The commands below come from those runs.
- **Run location.** Run them from `backend/` with `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python`.

## Coach (hero grading) — confirmed
1. **The wheel is not a straight to the coach.**
   - `_hand_category` builds straights from high-ace ranks only (`backend/app/domain/postflop.py:271`).
   - A made wheel is labelled "draw", and on the river "draw" becomes "air".
   - Result: calling a river bet with A2 on 3-4-5-K-9 grades **BLUNDER** (ran).
2. **Board-made hands count as strong.**
   - 22 on 5-6-7-8-9 and KQ with no heart on a five-heart board are "strong", and RAISE is the best action (ran).
   - The bots' classifier (`personas_postflop.py:121-125`) handles this correctly.
3. **Counterfeited and underpair two pair count as strong** in both classifiers.
   - Examples: 54 on 5-4-Q-Q-J; TT on A-J-8-8 (ran).
   - So switching the coach to the bots' classifier does not fix this.
4. **"Price" is the wrong formula.**
   - The graders use bet ÷ (pot including the bet). That is alpha, how often a bluff must work, though a comment calls it pot odds (`postflop.py:826`).
   - Pot odds is call ÷ (pot + call). For 50 into 100 the coach uses 33%; the correct required equity is 25%.
5. **Draws are never priced against the call.**
   - A flush draw (about 19.6% on one card) facing a 1.5×-pot turn bet needs 37.5%, yet CALL is graded best: call 1.0 against fold 0.98 (ran).
   - A gutshot plus overcards (AK on Q-J-3) is labelled a "draw".
   - 97 on J-8-5, a double gutshot with 8 outs, is labelled "air".
6. **No grader reads stack depth.** QQ and KK facing a check-raise grade the same at SPR (stack-to-pot ratio) 1.2, 3.9 and 13.0 (ran). The mapper uses stack only to decide whether a spot can be graded at all.
7. **Preflop off-chart plays grade too softly.**
   - Opening A6o, K9o or 55 under the gun, and calling K2o in the big blind against a button open, all grade ACCEPTABLE (ran).
   - Correction from review: a KTo 3-bet against an under-the-gun open is ACCEPTABLE only from the cutoff; from the button it already grades MISTAKE.
   - Caveat from review: 55 under the gun may be a fine live play when games run deep and multiway.
8. **Open sizes up to 4.5bb are graded at the 2.5bb price.**
   - Defending the big blind against 2.5bb needs 27.3% equity; against 4.5bb it needs 36.8% (`grade_map_preflop.py:115`, `scenarios.py:201`).
9. **"−X bb" is a penalty score, not chips.**
   - Fold scores above zero.
   - Preflop penalties do not scale with the pot.
   - `services/stats.py` adds them up as "bb given up".
10. **Grading coverage is thin.** Seeded sweep, 9-max, scripted hero, 2026-10-03:
    - preflop 57.7% graded;
    - flop 8.3%;
    - turn 0.3%;
    - river 0.1%;
    - postflop overall 3.5%.

    Real owner sessions show 1 to 6% of postflop decisions graded. 80% of postflop rejections are "pot shape not covered":

    | Pot shape not covered | Share of rejections |
    |---|---|
    | 5+-way pots (and 4-way without the big blind) | 24% |
    | Heads-up 3-bet pots | 21% |
    | Limped 3-way+ pots | 20% |
    | 3-way pots | 18% |
    | Multiway 3-bet pots | 12% |

## Engine — confirmed
11. **The minimum re-raise after a short all-in is too small.**
    - Case: LJ raises to 10, CO goes all-in for 15. The engine lets BTN raise to 19; card-room rules require 15 + 9 = 24 (ran; `table/engine.py:297-301`).
    - Separately, several short all-ins that together make a full raise never reopen the betting (`engine.py:159-160`).
12. **Bots judge commitment from their own stack, not the effective stack** (`table/play.py:300`, `personas_postflop.py:1889`). The effect is small: in 1–4% of bot postflop decisions, the bot's own stack-to-pot ratio and the effective one point opposite ways (ran, 12 × 500 hands).

## Table realism — confirmed (Opus refuter, 6,000 simulated 6-max hands)
13. **The 6-max lineup is online-shaped.**
    - The lineup is nit, TAG, TAG, LAG, station: one recreational player out of five (`play.py:60`).
    - The roadmap's supporting stat ranges come from online tracking-software guides.
14. **Pots are mostly heads-up and rarely limped.**
    - Flops: 84.7% heads-up, 13.6% three-way, 1.7% four-way.
    - The station started 1,432 of the 1,452 limped pots.
15. **Opens are online-sized.**
    - TAG and LAG median open is 2.5bb; isolation raises are 4.0bb with one limper and 5.5bb with two.
    - The repo's research disagrees with itself: `01-preflop-strategy.md` says live opens are 4–6bb, while `10-bet-sizing-by-node-persona.md` §3 says 3bb.
16. **Stacks drift deep.**
    - Top-up below 50bb, with no cap: after 500 hands, 57% of seat-hands start above 150bb and 9% below 80bb.
17. **No rake.**
    - The rake field is a stub (`spot.py:103`), and the ledger is stack minus buy-ins.
    - Correction from review: the "35–60 bb/100" figure in `_final-review.md:57` is the whole table's drop, not one player's cost. Per player it is roughly 4–10 bb/100, and that figure is an estimate.

## Refuted or demoted
- **Bots over-bluff rivers: refuted.**
  - The share of bot river bets with no pair or only ace-high is: nit 0–6%, station 2–6%, TAG 4–12%, LAG 6–25%. All are below the 33% a balanced pot-size bet would have.
  - So "a big river bet means strength" already holds.
- **Sizing tells.**
  - Research doc §7 says sizes are drawn independently of hand strength. That is out of date: pure-air bluffs lean toward larger sizes (`personas_postflop.py:2214-2217`).
  - No change was recommended (owner ruling below).
- **bb/100 with a confidence interval.** After 200 hands the 95% interval is about ±125 bb/100, so it is noise. VPIP, PFR and WTSD are useful at that sample size.
- **Bot adaptation to the hero.** Real players rarely do it, so it is low value.

## Owner rulings, 2026-10-03
- **Live target.** The bots target live $1/$2 play, not online 6-max statistics.
- **Rake.** Add rake (about 10%, capped at $5 + $1, no flop no drop) at both table sizes. It is a named exception to 9-max byte-identity. It changes settlement directly, and later bot decisions only through the smaller stacks it leaves. The rake build waits in NEXT.
- **Effective-stack commitment.** The bot fix goes to NEXT, 6-max first.
- **Left alone:** sizing tells, bot adaptation to the hero, and bb/100 with a confidence interval.
- **Two roadmaps, both active.** `coach-math` and `bot-realism-6max`. Agents ask the owner which one to work on.
- **Six-phase template.** Every lane runs research, evaluate, ideate, plan, build and verify, with deep first-principles research.
- **Appetite.** Two weeks.
