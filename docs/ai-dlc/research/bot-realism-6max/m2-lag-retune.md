## Bottom line

The retune of the loose-aggressive (LAG) bot at 6-max is judged against targets frozen in this file, before any tuning. Opening rates by seat, VPIP and PFR come from sources already verified in the M1 baseline report. The two new post-flop stats have no verified source: the sourcing pass found no published 6-max figure for how often a LAG raises when bet into, or for its raise size as a multiple of the bet. Both therefore use approximate bands (raise rate 10-20%; raises of 4x the bet or more at most 10% with a median of 2.5-3.5x). The LAG's flop c-bet and showdown rate stay unsourced, so the roadmap's full supporting check cannot be claimed as passed. The project owner's 200-hand Challenge verdict is not judged here.

Glossary for first use. M1 is the earlier 6-max baseline measurement (`m1-baseline.md`). M2 is this slice, the LAG retune at 6-max. RFI (raise first in) is the share of hands a seat opens with a raise when everyone before has folded. VPIP is the share of hands where a player voluntarily puts money in pre-flop; PFR is the share raised pre-flop. A Wilson interval is the Wilson score 95% confidence interval for a proportion, as used in M1. WTSD is the share of flops seen that reach showdown. "Inside" means the simulated 95% interval overlaps the cited range, or contains the cited single point.

These targets freeze when this file lands in commit 1 of the M2 work. Later commits may add a `## Results` section but may not edit anything above it.

## Ranges and sources

**Result: no verified source was found for either new stat, so both fall back to approximate bands.** The pass was run on 2026-09-30 with web searches followed by direct fetches of every page considered. Search snippets were never used as evidence. No host was blocked by the network filter.

**Labels.** VERIFIED means the figure appears on a page fetched directly. DERIVED means arithmetic on sourced figures. UNVERIFIED means recall or snippet hearsay, never usable for judging. Every source is recorded as a `(format, pool, source)` triple, and no full-ring (9-handed) figure is placed in a 6-max cell.

**Definitions the tool uses (a source counts only if its definition matches).**
- Raise-when-bet-into: any raise when the amount to call is above zero, counted per street and pooled over flop, turn and river.
- Raise multiple: `(street_inv_before + amount) / (street_inv_before + to_call)`, the bot's total street investment after raising divided by the bettor's total after the bet.
- A "raise flop c-bet" or "check-raise flop" figure may be compared only with the flop-only rate, or used as approximate. It is never compared with the pooled rate.

### New post-flop stats

| Stat | Source examined | (format, pool, source) | Definition on the page | Finding | Label |
|---|---|---|---|---|---|
| (a) Raise rate when bet into | BlackRain79, "What Are The Best Poker HUD Stats" (blackrain79.com/2017/10/what-are-the-best-poker-hud-stats.html) | (6-max and full ring both covered, unstated pool, author guidance) | Covers VPIP, PFR, 3-bet, 4-bet ratio, ATS and flop/turn/river c-bet and fold-to-c-bet. | Contains no raise-when-bet-into or check-raise figure. | unsourced |
| (a) | Poker Copilot user guide, "Poker HUD Statistics" (pokercopilot.com/userguide/7/en/topic/hud-statistics) | (tracker software manual, no format, no pool) | Defines check-raise per street as check, opponent bets, then raise. Gives no benchmark values and no definition matching the tool's raise-when-bet-into. | No LAG value. | unsourced |
| (a) | PokerTracker forum thread on "raise flop c-bet" (pokertracker.com/forums/viewtopic.php?t=102502&p=369982) | (forum, no format) | Discussion of building custom tracker stats. | No benchmark. | unsourced |
| (a) and (b) | PokerStrategy "Average Pre-flop Ranges: LAG" (pokerstrategy.com/strategy/bss/average-pre-flop-ranges-lag/) | (see M1 triple S3) | Pre-flop opening, calling and 3-bet ranges only. | No post-flop raise rate and no raise sizing. | unsourced |
| (b) Raise size as a multiple of the bet | Search for 6-max raise-size databases and articles; results were article series and spreadsheets on pre-flop sizing and general strategy | not fetched as evidence | none verified | No page was found that reports a measured post-flop raise multiple for a LAG or any 6-max player type. | unsourced |

A search-result summary mentioned 6-max aggression-factor bands and a "fold to flop c-bet" ideal; neither matches the tool's stats, and neither was fetched, so neither is used.

**Caveat on M1's per-seat source.** In this pass, a fetch of the LAG page (M1's S3) returned a summary that guessed "full-ring" because the page never states its format. M1 already recorded that the page never says "6-max" and inferred the format from its six-seat set. That caveat stands; it is the reason the pre-flop figures below stay "USABLE WITH CAVEAT", and nothing in this file strengthens the inference.

### Carried forward from M1 (not re-derived)

Source triples S3 and S5-S8 and S12 are defined in `m1-baseline.md`, "Ranges and sources".

| Stat | Range | M1 label and triple |
|---|---|---|
| RFI, LJ (the earliest opening seat at 6-max; M1 reads the source's "UTG" as LJ) | 20 | VERIFIED (S3: 6-max inferred, NL10 online, PokerStrategy) |
| RFI, HJ (hijack) | 23 | VERIFIED (S3) |
| RFI, CO (cutoff) | 33 | VERIFIED (S3) |
| RFI, BTN (button) | 50 | VERIFIED (S3) |
| RFI, SB (small blind) | 43 | VERIFIED (S3) |
| VPIP | 24-40 | VERIFIED; the union of the M1 cited LAG ranges (S3 26-35, S5 28-40, S6 24-30, S7 ~28, S8 25-35), each from a page fetched on 2026-09-26 |
| PFR | 20-35 | VERIFIED; the union of the M1 cited LAG ranges (S5 24-35, S6 20-26, S7 ~26, S8 20-25) |
| Flop c-bet | none | unsourced in M1; still unsourced |
| WTSD | none | unsourced in M1; still unsourced |

## Frozen targets

Items 1 to 6 are the spec's pass/fail list, frozen here. The baseline for the LAG is about 22% of raises at 4x or more (DERIVED: the project's own simulated run, 22.4% of 272 raises at 4x or more, 6,000 hands, seed 20260926). The judged run is the commit-3 run unless stated.

1. **Opening rates (judged).** LAG RFI at LJ, HJ, CO, BTN and SB: the simulated 95% Wilson interval contains 20, 23, 33, 50 and 43 respectively. Source figures are VERIFIED with the M1 caveat above.
2. **VPIP and PFR (reported, non-blocking).** LAG VPIP against 24-40 and PFR against 20-35, VERIFIED ranges from M1. A miss is recorded as a known gap and does not block the pull request.
3. **Raise rate when bet into (judged, APPROXIMATE).** Flop, turn and river pooled, at least 300 faced bets, and the simulated 95% Wilson interval must overlap the band 10-20%. This band is an approximate target, not a sourced figure: no verified definition-matched range was found, so the band is a judgement-based fallback. Fewer than 300 faced bets is inconclusive and counts as a fail. The flop-alone rate is also reported, for comparison only.
4. **Raise size (judged, APPROXIMATE).** The share of the LAG's raises at 4x the bet or more must be at most 10%, and the median multiple must sit inside 2.5-3.5x. At least 100 raises are required; fewer is inconclusive and counts as a fail. Both thresholds are approximate because no source was found.
5. **9-max unchanged (judged).** The commit-2 matched replay shows more than 0 changed hands, 0 unattributed hands and 0 unattributed rows, and commit 3's 9-max golden digest equals commit 2's.
6. **No other bot touched (judged).** `git diff` over `content/personas/` shows only the two new LAG files.

**Approximate items, stated plainly:** items 3 and 4. Neither has a verified source, so passing them shows the LAG sits inside a plausible band, not that it matches measured 6-max play.

**Reported, not judged.** The LAG's flop c-bet and WTSD have no sourced range and stay outstanding. The report may therefore not claim that the roadmap's full supporting check ("each bot's stats in real 6-max ranges") passed. The non-aggressor bet size (the bot's leads, probes and stabs as a fraction of the pot) is reported only to show the side effect of the sizing change.

**Not judged here.** The project owner's 200-hand Challenge verdict, including whether the owner can still name each bot's type, happens after merge. The roadmap box stays unticked until then.

**Project owner rulings, 2026-09-30.**
- Openings win: if the sourced opens push VPIP or PFR just under their floors, the miss is reported as a known gap and is non-blocking.
- The LAG opening fewer hands than the unchanged TAG (tight-aggressive bot) from LJ and HJ is accepted for now. The results report shows it, and the post-merge verdict records whether each bot's type is still nameable.
- Raise size is judged on its tail, with the 4x-or-more share falling from about 22% to at most 10%. The LAG's smaller leads and probe bets, which share the same sizing block, are disclosed as a side effect.

## Results

Added in commit 3.
