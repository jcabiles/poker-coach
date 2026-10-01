# Deep-stack strategy: what published sources support

- **Date:** 2026-10-01
- **Slice:** R1, the research step of the bot-realism-at-6-max roadmap (`docs/ai-dlc/roadmap/bot-realism-6max.md`). It feeds the later deep-stack work.
- **Labels:** every figure is **SOURCED** (a named source states it) or **APPROXIMATE** (computed or rounded by us; the basis is given). A "Re-opened" mark means the cited page was opened and the quote or figure confirmed on 2026-10-01.

## Bottom line

Published sources give firm numbers for two things and only directions for everything else.

- **Firm:** the stack-to-pot ratio (SPR, the stack behind divided by the pot) at which each hand type should commit its stack: about 3 for one pair, 5 for two pair and 10 for a set. Also firm: the SPR each pot type reaches at 100bb to 455bb, which is arithmetic.
- **Directions only:** deeper stacks make late-position opens slightly wider, make big-blind 3-bets more polar, drop JJ to TT from 4-bets, and make an in-position 4-bettor check the flop back more often. No source gives percentages.
- **Missing:** public population statistics by stack depth do not exist in anything found, and no source gives numbers above 300bb, although live stacks here reach 455bb.

The bots read stack depth in exactly one place, the post-flop commit rule driven by `spr_commit` (1.2 to 3.3 across the six bots). Every preflop decision, every raise size and the grader are fixed at about 100bb.

Two next steps follow from this.

1. **Give the commit rule one threshold per hand type** (one pair about 3, two pair about 5, set about 10). Gain: it matches the sources and stops a set being treated like a pair once stacks are deep. Cost: it changes decision code, not settings, so it falls outside the roadmap's current no-code-change rule and needs the project owner's approval; to keep 100bb play byte-identical it must switch on only above roughly 150bb.
2. **Measure before tuning anything else.** Run the simulator with deep starting stacks and count commitments that go wrong, which is already the first step of the roadmap's deep-stack item. Gain: it is the only route to depth-specific numbers, since none are published. Cost: one simulation run and its analysis.

## Where the app uses stack depth today

In plain words: the bots are built for 100bb, but stacks now carry over between hands, so a seat can hold anywhere from 50bb to about 455bb. Only one rule notices.

| Where | What it does | Re-read |
|---|---|---|
| `backend/app/domain/personas_postflop.py:1889` | When `stack_bb / pot_bb <= spr_commit`, strong made hands (overpair or top pair top kicker, or better) and unopposed strong draws get the commit shift: fold weight zeroed, bet and raise boosted. | yes |
| `personas_postflop.py:1902` | Below the draw-equity threshold, a draw keeps its fold and its call bonus is damped by how committed the seat is. | yes |
| `content/personas/*.json`, field `spr_commit` | Values: nit 1.2, passive_fish 1.4, calling_station 1.5, tag 2.5, lag 3.0, maniac 3.3. The 6-max override files do not change it. | yes (values); scan (6-max) |
| `backend/app/domain/table/play.py:300` | The gate is fed the acting seat's own stack and the total pot, not the smaller of the two stacks. | call site only |
| `backend/app/services/sim_session.py:138-139, 240-251` | Stacks start at 100bb, a seat below 50bb is topped up to 100bb, and nothing caps the top. This is where 455bb comes from. | yes |
| `docs/ai-dlc/research/bot-realism-6max/m1-baseline.md:246` | The simulated baseline used 95 to 105bb stacks; the bots' preflop decisions do not read stack size. | yes |
| Preflop decisions, open/3-bet/4-bet sizes, post-flop bet sizes, the hero grader | Fixed at about 100bb; they never read depth. The grader computes SPR for display only. | scan only |

Eight committed research documents mention deep stacks. All are unsourced or rest on a community forum thread (for example `docs/research/preflop-3bet-4bet-5bet.md:205-216`); none contradicts the sources below.

## Stack-to-pot ratio by depth

In plain words: doubling the stacks roughly doubles the SPR in the same kind of pot, so a deep-stacked 4-bet pot looks like a 100bb 3-bet pot.

Figures are **APPROXIMATE** (computed). Assumptions: single-raised pot is a 2.5bb open called by the big blind with the small blind folded (pot 5.5bb); 3-bet pot is a 3bb open, a 3-bet to 10bb and a call (pot 20.5bb); 4-bet pot is a 4-bet to 24bb and a call (pot 48.5bb). SPR is the stack behind divided by the pot at the start of the flop.

| Effective stack | Single-raised pot | 3-bet pot | 4-bet pot |
|---|---|---|---|
| 100bb | 17.7 | 4.4 | 1.6 |
| 200bb | 35.9 | 9.3 | 3.6 |
| 300bb | 54.1 | 14.1 | 5.7 |
| 455bb | 82.3 | 21.7 | 8.9 |

What this means for the bots: the commit gate (1.2 to 3.3) is closed on the flop in single-raised and 3-bet pots at every depth shown. At 100bb it opens on the flop only in 4-bet pots (SPR 1.6, so for tag, lag and maniac). At 200bb even a 4-bet pot (SPR 3.6) is above the loosest bot's threshold. Past the flop the pot grows and SPR falls, so the gate can still open on later streets.

## When to commit, by hand type

In plain words: the stronger the hand, the higher the SPR at which it is still right to put the whole stack in.

| Hand | Cutoff | Label | (format, depth, source type) | Source | As of | Re-opened |
|---|---|---|---|---|---|---|
| Top pair, overpair | Stack off by default at SPR 0 to 3; "not an auto-stack off" at 6 and above | SOURCED | (cash NLHE, 100bb examples, named author on an operator site) | Cluff, 888poker, `https://www.888poker.com/magazine/strategy/spr-in-poker` | 2020-02 | yes |
| Any single pair | "Above SPR 4, stacking off with a single pair, no matter how strong, starts to get dicey." | SOURCED | (article mixes MTT examples at 14bb and 30bb; the sentence is general; solver-vendor author) | Brokos, GTO Wizard, `https://blog.gtowizard.com/stack-to-pot-ratio/` | 2022-11 | yes |
| Overpair at deep stacks | "There will be many run-outs where you have to fold your overpair at or before the river." | SOURCED | (live cash, $1,500 stacks, small blind versus a cold-caller, named coach) | Jones, PokerCoaching, `https://pokercoaching.com/blog/how-to-play-overpairs-out-of-position-in-cash-games/` | 2023-06 | quote only |
| Two pair | Stack off at about SPR 5 | SOURCED | as the first row | Cluff, as above | 2020-02 | yes |
| Set | Stack off at about SPR 10; at SPR 100 a set "should expect to be up against only higher sets" | SOURCED | first row; second part is an MTT illustration | Cluff; Brokos, as above | 2020-02; 2022-11 | yes |

The sources agree within a band: one pair commits up to about SPR 3, becomes doubtful from 4 to 6, and two pair or better is the usual stack-off beyond that. They are guidelines, not cutoffs; the tighter statement (4) and the looser one (6) differ.

Fit with the bots: every `spr_commit` value except maniac (3.3) sits inside the one-pair range. But the gate applies one threshold to every strong hand, so a set at SPR 8 gets no commit shift, even though the sources put set commitment near 10.

## Preflop changes with depth

In plain words: deeper stacks reward position and speculative hands, and punish big pairs that used to be easy 4-bets. The sources say how, not how much.

| # | Finding | Label | (format, depth, source type) | Source | As of | Re-opened |
|---|---|---|---|---|---|---|
| 1 | The 6-max first seat (LJ) generally prefers a 2bb open to 3bb at 200bb; "not much different at 100bb". | SOURCED | (6-max cash, 100 to 200bb, solver-vendor author) | Brokos, GTO Wizard, `https://blog.gtowizard.com/preflop-raise-sizing-examining-2-key-factors/` | 2024-03 | yes |
| 2 | From 125bb to 300bb the CO opens "slightly wider"; the BTN calls and 3-bets slightly more; the blinds 3-bet less and call slightly more. No percentages given. | SOURCED | (cash, 125 to 300bb, raked and unraked comparisons, solver-vendor author) | Brokos, GTO Wizard, `https://blog.gtowizard.com/how-to-respond-to-large-preflop-raises-in-poker/` | 2025-02 | yes |
| 3 | From 100bb to 200bb the big blind's 3-bet range becomes more polar (strong hands plus selected weak ones). | SOURCED | (6-max cash, 100 to 200bb, solver-vendor author) | Brokos, GTO Wizard, `https://blog.gtowizard.com/ip-4-betting-in-deep-stacked-cash-games/` | 2025-01 | yes |
| 4 | CO versus BTN usually 4-bets TT to QQ at 100bb, but at 200bb "rarely 4-bets JJ-TT and never the weaker pairs". | SOURCED | (cash, 100 and 200bb, solver-vendor author) | Brokos, GTO Wizard, `https://blog.gtowizard.com/oop-4-betting-in-deep-stacked-cash-games/` | 2025-01 | yes |
| 5 | At 250bb and deeper, call 3-bets with JJ, QQ and AK instead of 4-betting; at 200bb play 7-6 suited and small pairs from the CO or BTN but fold them from the first two seats. | SOURCED | (deep cash, 200 to 300bb+, named coach) | Little, PokerCoaching, `https://pokercoaching.com/blog/deep-stack-poker-strategy/` | 2023-12 | yes |
| 6 | Set-mining needs implied odds (stack behind to call) of 15 to 1 against a maniac or in a 4-bet pot, 20 to 1 against a tight player, in a 3-bet pot or multiway, 30 to 1 against a typical 35% steal range, and 40 to 1 against a 50%-plus steal range. Depth helps meet the ratio; it does not lower it. | SOURCED | (cash, ratio by opponent type, named author) | James, `https://automaticpoker.com/strategy/set-mining-in-poker-definition-odds-and-strategy/` | 2020-02 | yes |

Not found: any percentage series by position for opens, 3-bets or 4-bets at 100, 200 and 300bb; any HJ-specific comparison; any figure above 300bb.

## Post-flop aggression with depth

In plain words: sources describe 100bb baselines well and 200bb as worked examples, but no one publishes how overall c-bet or barrel rates change with depth.

| # | Finding | Label | (format, depth, source type) | Source | As of | Re-opened |
|---|---|---|---|---|---|---|
| 1 | 100bb baseline, BTN versus BB single-raised pot: check back 45.7%, small bet (31% pot) 36.9%, pot-sized bet 17.5%. The 54.4% c-bet rate is the sum of the last two (derived, not printed). | SOURCED; the sum is APPROXIMATE | (6-max online cash NL500, 100bb, solver report) | GTO Wizard, `https://blog.gtowizard.com/introducing_custom_aggregated_reports/` | 2025-06 | yes |
| 2 | Another 100bb baseline: check 27.9%, one-third pot 48%, three-quarter pot 17.8%, overbet 6.3% across 60 flops. | SOURCED | (6-max online cash, 100bb, solver study) | Kubak, Deepsolver, `https://content-blog.deepsolver.com/which-boards-should-you-c-bet-playing-cash-games/` | 2024-11 | yes |
| 3 | 200bb example on A-K-7 rainbow, BTN versus BB single-raised pot: a quarter-pot c-bet with the whole range "loses just .02bb in theory"; the most-used turn size for the strongest hands is about 3 times the pot. Sizing example, not a frequency. | SOURCED | (6-max cash, 200bb, solver-vendor author) | Brokos, GTO Wizard, `https://blog.gtowizard.com/maximizing-monsters-in-deep-stacked-scenarios/` | 2024-11 | yes |
| 4 | In 4-bet pots (not single-raised), "IP checks back the flop significantly more often with 200bb stacks than with 100bb stacks", where IP is the in-position 4-bettor, BTN versus BB. | SOURCED | (cash 4-bet pots, 100 and 200bb, solver-vendor author) | Brokos, GTO Wizard, `https://blog.gtowizard.com/ip-4-betting-in-deep-stacked-cash-games/` | 2025-01 | yes |

The two 100bb baselines disagree on check-backs (45.7% against 27.9%); their flop sets and allowed sizes differ, so neither is a target. The claim in `docs/research/11-postflop-ranges-by-node.md:90` that "deeper stacks barrel less" stays unsourced: nothing found confirms or refutes it for single-raised pots.

## Population evidence

In plain words: nobody publishes how real players' habits change with stack depth, so no bot frequency can be calibrated to a real population by depth.

The research lane that searched for studies and database reports found none that bin results by effective stack, online or live, and none for tight-versus-loose or passive-versus-aggressive types by depth. A separate search on 2026-10-01 found the same. Two database reports were found and set aside because they report no depth: a Hold'em Manager study (2008-06, 1,790 players with at least 5,000 hands, online 6-max) and a Hand2Note report (2026-03, recreational players grouped by VPIP). Both were reported by the lane and not re-opened. No academic paper quantifying equity realization against depth was found.

## What can become settings

| Item | Status | Basis |
|---|---|---|
| Commit threshold per hand type: pair about 3, two pair about 5, set about 10 | Usable as defaults | Cluff 2020-02 and Brokos 2022-11, re-opened; guidelines, not exact cutoffs |
| Set-mining implied-odds ratios 15, 20, 30, 40 to 1 by opponent type | Usable | One author (James 2020-02), re-opened |
| SPR by depth and pot type | Usable | Arithmetic, assumptions stated above |
| Wider CO and BTN opens, fewer JJ to TT 4-bets, more polar big-blind 3-bets, more in-position flop check-backs in 4-bet pots | Direction only | Brokos 2025-01 and 2025-02; no magnitudes |
| Percentage changes to open, 3-bet, 4-bet, c-bet or barrel rates | Not available | No source |
| Anything at 300bb to 455bb | Not available | Sources stop at 300bb |
| Population calibration by depth | Not available | No public data |

## Limits

- Most depth findings come from one solver-vendor author (Brokos, GTO Wizard). Solver output is spot-specific and is not a population, and the repository's no-solver-tables rule means only these aggregate statements are used, never charts.
- Three sources (rows 2 and 4 of the preflop table, and the stack-to-pot article) do not state a table size or mix formats; each is tagged where it applies.
- The commit table rests on strategy writing, not measurement. The 888poker and Brokos cutoffs differ by about 2 SPR.

## Method and verification

Four web lanes and one repository scan ran on 2026-10-01: three Codex lanes (preflop, studies and database reports, and one post-flop lane that stalled with no output after 13 minutes), then two narrower Codex lanes replacing it (commitment cutoffs, and c-bet and barrel sizing), and one Sonnet scan of the code. Eleven source pages were re-opened and their quotes confirmed. Three lane claims were corrected before use: the 54.4% c-bet rate is derived, not printed; a claim of a king-queen value shove at SPR 17.7 was rejected because the figures belonged to a different line in the article; and an SPR 5.6 figure for the deep-stack overpair example was not confirmed and was dropped.
