## Bottom line

**Outcome (added in commit 3; the text below this paragraph is unchanged from commit 1).** The retune passes four of the six frozen items outright and misses one seat of the first. Items 3 (raise rate when bet into: 18.1%, 846 faced bets), 4 (raise size: 5.9% at 4x or more, median 2.66x, 153 raises), 5 (9-max unchanged, proven hand by hand) and 6 (no other bot touched) pass. Item 1 (opening rates) passes at LJ, HJ, BTN and SB and fails at CO on the judged seed (28.5% [25.2%, 32.1%] against 33); the project owner waived that miss on 2026-10-01 because the held-out seeds 1-5 and 6-10 give 33.5% at CO, and the frozen check stays as written. Item 2 is reported: VPIP is inside its range, PFR (18.5%) is under the 20 floor, a known gap that does not block the pull request. Not settled: the LAG also opens less than the unchanged TAG at CO on the judged seed (the project owner accepted this only at LJ and HJ); the raise-rate and raise-size bands are approximate, not sourced; the LAG's flop c-bet and showdown rate have no sourced range, so the roadmap's full supporting check is not claimed as passed; and the project owner's 200-hand Challenge verdict happens after merge.

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

**Result: the LAG's opening rates, raise rate and raise size now land in their frozen targets, except the CO opening rate on the judged seed (waived); every figure below is copied from a saved simulation output.** Section 6 holds the pass/fail table. Sections 1 to 5 hold the measurements behind it, and sections 7 to 9 say what is reported but not judged.

### 1. Judged runs

**Result: both judged runs are deterministic, because each was run twice and the two outputs were byte-identical.**

- **Conditions.** `sixmax_baseline`, seed 20260926, 6,000 simulated hands, stacks 95-105bb, real session `4b35736f...` up to hand 201 (201 hands), as in M1.
- **Commit 1 (before any decision change).** Two runs, byte-identical (`c1-run1.txt` equals `c1-run2.txt`).
- **Commit 3 (the retune).** Two runs, byte-identical (`c3-run1.txt` equals `c3-run2.txt`).
- **Provenance.** The saved commit-1 judged run ran on the then-uncommitted commit-1 tree on top of the spec-revision commit, so its header names that commit (`1676ac1`), not commit 1's SHA (`09d25b0`). The saved commit-3 runs ran on the working tree that became commit 3, so their header names commit 2's SHA (`c333e5a`). A repeat on the committed head is compared byte for byte (header line aside) before the pull request opens, and its result is stated in the pull request.

### 2. Per-bot tables

**Result: the LAG moved as intended; the other bots' figures also shifted, but only because they now face a different LAG, and nothing is judged on them.** Cells read: chances n, then rate with its Wilson 95% interval. A Wilson interval is the Wilson score confidence interval for a proportion. "Stand-in" is the simulated stand-in for the real session's seat 0.

#### Commit 1 (before the retune and before the board-made-hand fix), seed 20260926, 6,000 hands

| stat | nit | lag | tag | station | stand-in tag (seat 0) |
|---|---|---|---|---|---|
| VPIP | n=5917 · 9.5% [8.7%, 10.2%] | n=5879 · 33.6% [32.4%, 34.8%] | n=11828 · 22.6% [21.9%, 23.4%] | n=5895 · 50.7% [49.5%, 52.0%] | n=5913 · 21.3% [20.3%, 22.4%] |
| PFR | n=5917 · 6.7% [6.1%, 7.4%] | n=5879 · 28.3% [27.1%, 29.4%] | n=11828 · 17.9% [17.2%, 18.6%] | n=5895 · 0.5% [0.3%, 0.7%] | n=5913 · 17.0% [16.1%, 18.0%] |
| RFI LJ | n=1000 · 10.4% [8.7%, 12.4%] | n=1000 · 37.7% [34.7%, 40.7%] | n=2000 · 28.6% [26.7%, 30.7%] | n=1000 · 1.0% [0.5%, 1.8%] | n=1000 · 29.4% [26.7%, 32.3%] |
| RFI HJ | n=706 · 12.5% [10.2%, 15.1%] | n=886 · 47.0% [43.7%, 50.2%] | n=1359 · 29.9% [27.5%, 32.4%] | n=691 · 1.2% [0.6%, 2.3%] | n=514 · 28.8% [25.0%, 32.9%] |
| RFI CO | n=366 · 15.8% [12.5%, 19.9%] | n=615 · 48.6% [44.7%, 52.6%] | n=911 · 31.6% [28.7%, 34.7%] | n=512 · 0.6% [0.2%, 1.7%] | n=370 · 29.5% [25.0%, 34.3%] |
| RFI BTN | n=261 · 26.8% [21.8%, 32.5%] | n=304 · 56.9% [51.3%, 62.4%] | n=631 · 45.6% [41.8%, 49.5%] | n=308 · 1.0% [0.3%, 2.8%] | n=261 · 45.6% [39.7%, 51.7%] |
| RFI SB | n=142 · 13.4% [8.7%, 20.0%] | n=185 · 51.9% [44.7%, 59.0%] | n=296 · 36.5% [31.2%, 42.1%] | n=178 · 0.6% [0.1%, 3.1%] | n=153 · 45.8% [38.1%, 53.7%] |
| flop c-bet | n=148 · 22.3% [16.3%, 29.7%] | n=714 · 48.7% [45.1%, 52.4%] | n=940 · 41.4% [38.3%, 44.6%] | n=7 · 28.6% [8.2%, 64.1%] | n=322 · 46.3% [40.9%, 51.7%] |
| WTSD | n=464 · 58.6% [54.1%, 63.0%] | n=1404 · 53.0% [50.4%, 55.6%] | n=2224 · 55.5% [53.4%, 57.5%] | n=2805 · 64.8% [63.1%, 66.6%] | n=762 · 46.7% [43.2%, 50.3%] |
| raise when bet into (flop) | n=145 · 11.7% [7.5%, 18.0%] | n=422 · 32.9% [28.6%, 37.6%] | n=711 · 26.7% [23.6%, 30.1%] | n=1293 · 2.9% [2.1%, 4.0%] | n=307 · 20.8% [16.7%, 25.7%] |
| raise when bet into (flop+turn+river) | n=353 · 15.3% [11.9%, 19.4%] | n=949 · 28.7% [25.9%, 31.6%] | n=1527 · 24.3% [22.2%, 26.5%] | n=3297 · 3.3% [2.8%, 4.0%] | n=653 · 22.2% [19.2%, 25.6%] |
| raise multiple | n=54 · median 2.83x · mean 2.95x · p90 4.67x · >=4x 25.9% | n=272 · median 3.00x · mean 3.04x · p90 4.77x · >=4x 22.4% | n=371 · median 3.00x · mean 3.07x · p90 4.77x · >=4x 25.3% | n=110 · median 2.32x · mean 2.41x · p90 3.50x · >=4x 6.4% | n=145 · median 3.00x · mean 3.02x · p90 4.77x · >=4x 22.8% |
| non-aggressor bet (pot fraction) | n=96 · mean 0.61 of pot | n=419 · mean 0.59 of pot | n=595 · mean 0.59 of pot | n=912 · mean 0.49 of pot | n=213 · mean 0.58 of pot |

#### Commit 3 (after the retune), seed 20260926, 6,000 hands

| stat | nit | lag | tag | station | stand-in tag (seat 0) |
|---|---|---|---|---|---|
| VPIP | n=5896 · 9.6% [8.9%, 10.4%] | n=5895 · 24.8% [23.7%, 25.9%] | n=11799 · 23.9% [23.1%, 24.6%] | n=5849 · 52.1% [50.9%, 53.4%] | n=5886 · 20.5% [19.5%, 21.5%] |
| PFR | n=5896 · 7.3% [6.7%, 8.0%] | n=5895 · 18.5% [17.6%, 19.6%] | n=11799 · 19.9% [19.2%, 20.6%] | n=5849 · 0.4% [0.3%, 0.7%] | n=5886 · 16.4% [15.5%, 17.4%] |
| RFI LJ | n=1000 · 12.1% [10.2%, 14.3%] | n=1000 · 19.7% [17.4%, 22.3%] | n=2000 · 28.1% [26.2%, 30.2%] | n=1000 · 0.6% [0.3%, 1.3%] | n=1000 · 25.4% [22.8%, 28.2%] |
| RFI HJ | n=746 · 12.9% [10.7%, 15.5%] | n=872 · 22.2% [19.6%, 25.1%] | n=1524 · 30.0% [27.7%, 32.3%] | n=716 · 1.1% [0.6%, 2.2%] | n=516 · 33.9% [30.0%, 38.1%] |
| RFI CO | n=341 · 14.4% [11.0%, 18.5%] | n=645 · 28.5% [25.2%, 32.1%] | n=1241 · 32.7% [30.2%, 35.4%] | n=504 · 1.2% [0.5%, 2.6%] | n=338 · 31.7% [26.9%, 36.8%] |
| RFI BTN | n=231 · 23.4% [18.4%, 29.2%] | n=290 · 50.3% [44.6%, 56.1%] | n=921 · 43.9% [40.7%, 47.1%] | n=375 · 0.3% [0.0%, 1.5%] | n=259 · 44.0% [38.1%, 50.1%] |
| RFI SB | n=145 · 25.5% [19.1%, 33.2%] | n=174 · 40.8% [33.8%, 48.2%] | n=399 · 37.6% [33.0%, 42.4%] | n=262 · 0.0% [0.0%, 1.4%] | n=177 · 41.2% [34.3%, 48.6%] |
| flop c-bet | n=158 · 27.8% [21.4%, 35.3%] | n=483 · 53.4% [49.0%, 57.8%] | n=1131 · 43.2% [40.4%, 46.1%] | n=3 · 33.3% [6.1%, 79.2%] | n=321 · 45.8% [40.4%, 51.3%] |
| WTSD | n=517 · 61.5% [57.2%, 65.6%] | n=1161 · 55.0% [52.2%, 57.9%] | n=2343 · 56.3% [54.3%, 58.3%] | n=2899 · 65.9% [64.1%, 67.6%] | n=807 · 49.4% [46.0%, 52.9%] |
| raise when bet into (flop) | n=172 · 15.7% [11.0%, 21.9%] | n=366 · 18.0% [14.4%, 22.3%] | n=671 · 27.3% [24.0%, 30.8%] | n=1306 · 2.5% [1.7%, 3.4%] | n=327 · 28.1% [23.5%, 33.2%] |
| raise when bet into (flop+turn+river) | n=400 · 18.2% [14.8%, 22.3%] | n=846 · 18.1% [15.6%, 20.8%] | n=1485 · 23.6% [21.5%, 25.9%] | n=3362 · 3.3% [2.7%, 4.0%] | n=653 · 25.7% [22.5%, 29.2%] |
| raise multiple | n=73 · median 3.00x · mean 3.09x · p90 4.77x · >=4x 24.7% | n=153 · median 2.66x · mean 2.62x · p90 3.52x · >=4x 5.9% | n=351 · median 3.00x · mean 3.06x · p90 4.77x · >=4x 25.9% | n=111 · median 2.43x · mean 2.64x · p90 4.00x · >=4x 11.7% | n=168 · median 2.67x · mean 2.93x · p90 4.77x · >=4x 19.0% |
| non-aggressor bet (pot fraction) | n=118 · mean 0.59 of pot | n=443 · mean 0.48 of pot | n=578 · mean 0.59 of pot | n=851 · mean 0.48 of pot | n=244 · mean 0.59 of pot |

### 3. Each part's share

**Result: the board-made-hand fix is small (19 of 6,000 6-max hands changed); the retune changes 973 of 6,000 hands and accounts for the LAG's shift.** Each share comes from a matched replay: the same hands are replayed twice, before and after a change, each hand with its own random stream, so a change in one hand cannot move another. The script is in the appendix.

#### The board-made-hand fix (commit 1 against commit 2)

| Run | Hands compared | Hands changed | Attributed to the fix | Unattributed | Export rows changed (attributed) |
|---|---|---|---|---|---|
| 9-max, 4,000 hands | 4000 | 13 | 13 | 0 | 161 (161) |
| 6-max, 6,000 hands | 6000 | 19 | 19 | 0 | 225 (225) |

On 6-max the first differing action was bet to check 17 times, raise to call once and raise to fold once (`c2-share-6max.txt`). The LAG's river stats on the 6-max matched sample, before to after the fix (LAG seat 2):

| Stat | Before | After |
|---|---|---|
| river aggression share (bet+raise / seen) | 39.41% | 38.33% |
| river raise when bet into | 22.33% | 20.10% |
| river fold when bet into | 42.23% | 43.72% |
| river call share (call / seen) | 7.93% | 7.82% |

#### The retune (commit 2 against commit 3), 6-max, 6,000 matched hands

Hands changed: 973 of 6,000. Decision rows differing (including later knock-on effects in the same hand): 5199. Export rows changed: 18798. The fix's attribution rule does not apply to the retune, so the tool's attribution lines are not used here. Instead, who made each changed hand's first differing action:

| Persona | Pre-flop | Flop | Turn | River |
|---|---|---|---|---|
| lag | 534 | 215 | 131 | 26 |
| tag | 35 | 11 | 1 | 0 |
| calling_station | 6 | 6 | 0 | 3 |
| nit | 2 | 2 | 0 | 1 |

Non-LAG first differences arise because one random stream per hand feeds every decision in it: a LAG decision that draws differently, even with the same action, shifts later draws. The LAG on the matched sample, before (commit 2) to after (commit 3):

| Stat | Before | After |
|---|---|---|
| VPIP | n=5882 · 35.0% [33.8%, 36.2%] | n=5882 · 26.0% [24.9%, 27.1%] |
| PFR | n=5882 · 29.0% [27.9%, 30.2%] | n=5882 · 20.0% [19.0%, 21.1%] |
| RFI LJ | n=1000 · 38.6% [35.6%, 41.7%] | n=1000 · 20.9% [18.5%, 23.5%] |
| RFI HJ | n=859 · 48.5% [45.2%, 51.9%] | n=859 · 23.3% [20.6%, 26.2%] |
| RFI CO | n=619 · 50.6% [46.6%, 54.5%] | n=619 · 36.0% [32.3%, 39.9%] |
| RFI BTN | n=326 · 58.0% [52.6%, 63.2%] | n=326 · 47.9% [42.5%, 53.3%] |
| RFI SB | n=196 · 43.9% [37.1%, 50.9%] | n=196 · 38.3% [31.7%, 45.2%] |
| flop c-bet | n=737 · 47.5% [43.9%, 51.1%] | n=482 · 49.6% [45.1%, 54.0%] |
| WTSD | n=1471 · 54.3% [51.8%, 56.8%] | n=1159 · 51.9% [49.0%, 54.7%] |
| raise when bet into (flop) | n=487 · 36.6% [32.4%, 40.9%] | n=383 · 21.7% [17.8%, 26.1%] |
| raise when bet into (flop+turn+river) | n=1045 · 31.8% [29.0%, 34.7%] | n=840 · 18.9% [16.4%, 21.7%] |
| raise multiple | n=332 · median 3.00x · mean 3.14x · p90 4.77x · >=4x 23.5% | n=159 · median 2.67x · mean 2.74x · p90 3.52x · >=4x 5.7% |
| non-aggressor bet (pot fraction) | n=423 · mean 0.61 of pot | n=426 · mean 0.49 of pot |

The TAG's matched-sample figures also moved (for example its VPIP 21.9% to 23.2% and PFR 17.1% to 19.2%) because its table changed; nothing is judged on them.

#### Commit-level deltas from the judged runs (dominated by reshuffled hands)

The judged runs use one shared random stream per table, so any changed decision reshuffles every later hand. These deltas mix the fix, the retune and that reshuffling; the matched replays above are the measure of each part's share. The LAG, commit 1 against commit 3:

| stat | LAG at commit 1 (before) | LAG at commit 3 (after) |
|---|---|---|
| VPIP | n=5879 · 33.6% [32.4%, 34.8%] | n=5895 · 24.8% [23.7%, 25.9%] |
| PFR | n=5879 · 28.3% [27.1%, 29.4%] | n=5895 · 18.5% [17.6%, 19.6%] |
| RFI LJ | n=1000 · 37.7% [34.7%, 40.7%] | n=1000 · 19.7% [17.4%, 22.3%] |
| RFI HJ | n=886 · 47.0% [43.7%, 50.2%] | n=872 · 22.2% [19.6%, 25.1%] |
| RFI CO | n=615 · 48.6% [44.7%, 52.6%] | n=645 · 28.5% [25.2%, 32.1%] |
| RFI BTN | n=304 · 56.9% [51.3%, 62.4%] | n=290 · 50.3% [44.6%, 56.1%] |
| RFI SB | n=185 · 51.9% [44.7%, 59.0%] | n=174 · 40.8% [33.8%, 48.2%] |
| flop c-bet | n=714 · 48.7% [45.1%, 52.4%] | n=483 · 53.4% [49.0%, 57.8%] |
| WTSD | n=1404 · 53.0% [50.4%, 55.6%] | n=1161 · 55.0% [52.2%, 57.9%] |
| raise when bet into (flop) | n=422 · 32.9% [28.6%, 37.6%] | n=366 · 18.0% [14.4%, 22.3%] |
| raise when bet into (flop+turn+river) | n=949 · 28.7% [25.9%, 31.6%] | n=846 · 18.1% [15.6%, 20.8%] |
| raise multiple | n=272 · median 3.00x · mean 3.04x · p90 4.77x · >=4x 22.4% | n=153 · median 2.66x · mean 2.62x · p90 3.52x · >=4x 5.9% |
| non-aggressor bet (pot fraction) | n=419 · mean 0.59 of pot | n=443 · mean 0.48 of pot |

### 4. LAG versus TAG opening rates by seat

**Result: the LAG opens fewer hands than the unchanged TAG at LJ and HJ (accepted), and on the judged seed also at CO, and its PFR is below the TAG's.** The project owner accepted the LAG opening fewer hands than the TAG at LJ and HJ only. On the judged seed the LAG also opens less than the TAG at CO (28.5% against 32.7%), and its PFR is below the TAG's (18.5% against 19.9%; pooled seeds 1-5: 19.4% against 19.6%). This goes to the post-merge verdict record: whether the project owner can still name each bot's type.

#### Judged run, commit 3, seed 20260926, 6,000 hands

| Stat | LAG | TAG |
|---|---|---|
| RFI LJ | n=1000 · 19.7% [17.4%, 22.3%] | n=2000 · 28.1% [26.2%, 30.2%] |
| RFI HJ | n=872 · 22.2% [19.6%, 25.1%] | n=1524 · 30.0% [27.7%, 32.3%] |
| RFI CO | n=645 · 28.5% [25.2%, 32.1%] | n=1241 · 32.7% [30.2%, 35.4%] |
| RFI BTN | n=290 · 50.3% [44.6%, 56.1%] | n=921 · 43.9% [40.7%, 47.1%] |
| RFI SB | n=174 · 40.8% [33.8%, 48.2%] | n=399 · 37.6% [33.0%, 42.4%] |
| VPIP | n=5895 · 24.8% [23.7%, 25.9%] | n=11799 · 23.9% [23.1%, 24.6%] |
| PFR | n=5895 · 18.5% [17.6%, 19.6%] | n=11799 · 19.9% [19.2%, 20.6%] |

#### Pooled seeds, commit 3, 6,000 hands per seed (seeds 1-5 are the calibration seeds; seeds 6-10 were never used to tune)

| Stat | LAG seeds 1-5 | TAG seeds 1-5 | LAG seeds 6-10 | TAG seeds 6-10 |
|---|---|---|---|---|
| RFI LJ | 19.9% [18.8%, 21.0%] | 27.6% [26.7%, 28.5%] | 19.2% [18.1%, 20.3%] | 27.9% [27.0%, 28.8%] |
| RFI HJ | 23.6% [22.4%, 24.9%] | 30.0% [29.0%, 31.1%] | 23.6% [22.4%, 24.9%] | 29.9% [28.9%, 31.0%] |
| RFI CO | 33.5% [31.8%, 35.2%] | 31.4% [30.2%, 32.5%] | 33.5% [31.9%, 35.2%] | 30.4% [29.3%, 31.6%] |
| RFI BTN | 50.4% [47.9%, 53.0%] | 45.7% [44.3%, 47.2%] | 51.0% [48.5%, 53.6%] | 45.0% [43.5%, 46.4%] |
| RFI SB | 44.4% [41.3%, 47.5%] | 35.4% [33.2%, 37.6%] | 41.7% [38.6%, 44.9%] | 35.9% [33.7%, 38.1%] |
| VPIP | 25.3% [24.8%, 25.8%] | 23.7% [23.4%, 24.1%] | 25.1% [24.6%, 25.6%] | 23.6% [23.2%, 23.9%] |
| PFR | 19.4% [18.9%, 19.8%] | 19.6% [19.3%, 19.9%] | 19.2% [18.7%, 19.6%] | 19.6% [19.3%, 19.9%] |

On the pooled seeds the LAG opens fewer hands than the TAG at LJ and HJ only, as the project owner accepted, and opens more at CO, BTN and SB. Its pooled PFR is a little below the TAG's on both seed sets.

### 5. Non-aggressor bet size before and after

**Result: the LAG's non-aggressor bets (leads, probes and stabs) shrank from 0.59 to 0.48 of the pot on the judged seed, the side effect the project owner accepted.** The sizing block that shrinks its raises also sizes these bets.

| Measure | Commit 1 | Commit 3 |
|---|---|---|
| Judged run, LAG, seed 20260926, 6,000 hands | n=419 · mean 0.59 of pot | n=443 · mean 0.48 of pot |
| Pooled seeds 1-5, LAG, commit 3 | not measured at commit 1 | n=2150 · mean 0.487 |
| Pooled seeds 6-10, LAG, commit 3 | not measured at commit 1 | n=2043 · mean 0.487 |

The matched replay compares commit 2 with commit 3 instead:

| Measure | Commit 2 | Commit 3 |
|---|---|---|
| Matched replay, LAG | n=423 · mean 0.61 of pot | n=426 · mean 0.49 of pot |

### 6. Pass/fail table (spec items 1 to 6, frozen in commit 1)

**Result: items 3, 4, 5 and 6 pass; item 1 passes at four of five seats and fails at CO on the judged seed (waived); item 2 is reported with PFR a known gap.** All figures are commit 3, seed 20260926, 6,000 hands, unless stated.

| Item | Target | Measured | Verdict |
|---|---|---|---|
| 1. Opening rates, LJ | interval contains 20 | 19.7% [17.4%, 22.3%] | pass |
| 1. HJ | contains 23 | 22.2% [19.6%, 25.1%] | pass |
| 1. CO | contains 33 | 28.5% [25.2%, 32.1%] | **FAIL, waived** |
| 1. BTN | contains 50 | 50.3% [44.6%, 56.1%] | pass |
| 1. SB | contains 43 | 40.8% [33.8%, 48.2%] | pass |
| 2. VPIP (reported, non-blocking) | against 24-40 | 24.8% [23.7%, 25.9%] | inside |
| 2. PFR (reported, non-blocking) | against 20-35 | 18.5% [17.6%, 19.6%] | below the floor: known gap |
| 3. Raise rate when bet into, flop+turn+river | at least 300 faced bets; interval overlaps 10-20% (approximate) | n=846 · 18.1% [15.6%, 20.8%] | pass |
| 4. Raise size, share at 4x or more | at most 10% (approximate); at least 100 raises | n=153 · 5.9% | pass |
| 4. Raise size, median | inside 2.5-3.5x (approximate) | 2.66x (mean 2.62x, p90 3.52x) | pass |
| 5. 9-max unchanged: matched replay | more than 0 changed, 0 unattributed hands and rows | 4000 compared, 13 changed, 13 attributed, 0 unattributed; 161 of 161 export rows attributed | pass |
| 5. 9-max golden digest equals commit 2's | the 9-max digest line is unchanged | `git diff` of the golden test file against commit 2 changes only the 6-max digest line; the 9-max digest line is not in the diff | pass |
| 6. No other bot touched | `content/personas/` shows only the two new LAG files | `git status --short -uall content/personas` lists only `content/personas/ladders/six_max/lag.unopened.json` and `content/personas/six_max/lag.json` | pass |

**Item 1, CO.** The waiver is the project owner's, dated 2026-10-01: the judged-seed miss is a low draw on one seed, and the frozen check was kept as written. The held-out figures sit beside it:

| CO opening rate | Measured | Contains 33? |
|---|---|---|
| Judged seed 20260926, 6,000 hands | n=645 · 28.5% [25.2%, 32.1%] | no |
| Pooled seeds 1-5 (calibration seeds) | n=3008 · 33.5% [31.8%, 35.2%] | yes |
| Pooled seeds 6-10 (held out, never used to tune) | n=3093 · 33.5% [31.9%, 35.2%] | yes |

On the held-out seeds 6-10 every seat contains its target: LJ 19.2% [18.1%, 20.3%], HJ 23.6% [22.4%, 24.9%], CO 33.5% [31.9%, 35.2%], BTN 51.0% [48.5%, 53.6%] and SB 41.7% [38.6%, 44.9%]. On seeds 1-5 every seat also contains its target: LJ 19.9%, HJ 23.6%, CO 33.5%, BTN 50.4% and SB 44.4% (intervals in section 4).

**Item 2.** The PFR interval tops out at 19.6%, under the 20 floor. By the project owner's "openings win" ruling (2026-09-30), a PFR just under its floor because the sourced openings were matched is a known gap and does not block the pull request. Pooled PFR is 19.4% on seeds 1-5 and 19.2% on seeds 6-10.

**Items 3 and 4 are approximate.** No verified source exists for either stat (see the sources section above), so a pass shows the LAG sits inside a plausible band, not that it matches measured 6-max play. For comparison only, the flop-alone raise rate when bet into is n=366 · 18.0% [14.4%, 22.3%]. Pooled seeds 1-5 give a raise rate of 18.2% [17.0%, 19.5%] (n=3891) and a raise multiple with n=709, median 2.66x and 4.5% at 4x or more; seeds 6-10 give 16.6% [15.5%, 17.8%] (n=3996) and n=664, median 2.66x, 5.9% at 4x or more.

### 7. Reported, not judged

**Result: the LAG's flop c-bet and showdown rate have no sourced range, so this report does not claim the roadmap's full supporting check ("each bot's stats in real 6-max ranges") passed.** The measured values, commit 3, seed 20260926, 6,000 hands:

| Stat | Commit 1 | Commit 3 |
|---|---|---|
| LAG flop c-bet | n=714 · 48.7% [45.1%, 52.4%] | n=483 · 53.4% [49.0%, 57.8%] |
| LAG WTSD (went to showdown, as a share of flops seen) | n=1404 · 53.0% [50.4%, 55.6%] | n=1161 · 55.0% [52.2%, 57.9%] |

Pooled seeds 1-5 give a flop c-bet of 53.5% [51.5%, 55.6%] and WTSD of 52.9% [51.6%, 54.2%]; seeds 6-10 give 51.9% [49.8%, 53.9%] and 53.2% [51.9%, 54.5%].

### 8. Attribution detail and the known near-ties

**Result: the fix's attribution is clean on 9-max (13 of 13 changed hands, 161 of 161 export rows), and the near-ties the spec names remain monsters by design.** On 9-max, the first differing action was bet to check 12 times and raise to fold once. By persona the first differing actions were calling_station 5, lag 3, passive_fish 3, maniac 1 and tag 1. Of the 6-max export rows changed by the fix, 3 were relabels of the hand class from monster to middle pair with the action unchanged (none on 9-max).

The rule leaves three near-ties as monsters, because the bot's own card improves the hand at all:
- a low flush card that only beats the board's fifth card;
- a quads kicker one rank above the board's;
- quads on a four-card turn board with a weak kicker.

The near-tie scan (`c2-near-ties.txt`) counts river decisions where the hole cards improve a board-made hand and so keep the monster class. It does not split out the three cases above by name, so separate counts for them are not measured. Its categories and counts:

| Run | Category | Decisions |
|---|---|---|
| 9-max | board flush, hole flush card | 4 |
| 9-max | board quads, hole kicker 2 or more ranks above | 10 |
| 9-max | board straight, higher straight | 1 |
| 6-max | board boat, better boat | 3 |
| 6-max | board flush, hole flush card | 3 |
| 6-max | board straight, higher straight | 2 |

### 9. Not judged here

**The project owner's 200-hand Challenge verdict happens after merge, and the roadmap box stays unticked until then.** It includes whether the project owner can still name each bot's type, given the LAG now opens fewer hands than the TAG at LJ and HJ (accepted) and, on the judged seed, also at CO, with a PFR below the TAG's (section 4). A pass here is also not proof that settings alone suffice: the project owner judges the settings change and the board-made-hand fix together, and the matched replays above only report each part's share.

### Appendix: the matched-replay script

Run from `backend/`: `dump` writes each hand's action fingerprint and export rows to a file, and `compare` diffs two dumps. The commands used are in the header of each saved output: `python m2-sim/matched_replay.py dump --seats 6 --hands N --out FILE`, then `compare BEFORE AFTER [--lag-seat 2]`.

```python
"""Matched replay (M2 spec section 4): per-hand dumps + before/after attribution.

Each hand has its OWN decision stream `random.Random(hand_seed + 1)`, and the hand
seeds are drawn up front from a seed-only master stream, so a changed decision in
one hand can never move another hand. Run from `backend/` with PYTHONPATH=.

  dump:    python matched_replay.py dump --seats 9 --hands 4000 --out before9.jsonl
  compare: python matched_replay.py compare before9.jsonl after9.jsonl [--lag-seat 2]

9-max: lineup DEFAULT_LINEUP[i % len] over 9 seats, button i % 9, flat 100bb stacks,
master seed 20260927 (as `_nine_max_states` in tests/test_bot_decisions_golden.py).
6-max: `sixmax_baseline.SEATS`, button i % 6, `_draw_buyin_targets(hand_seed, 6)`
stacks, master seed 20260926 (as `run_baseline`).
Export rows are `play_one_hand`'s own rows (hand, seats, decisions), the same path
`export_analytics.run_export` writes to Parquet.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter

from app.domain.personas import load_persona_packs
from app.domain.personas_postflop import _best5
from tools import export_analytics as ea
from tools.sixmax_baseline import SEATS as SIXMAX_SEATS
from tools.table_stats import Hand, replay, settle_hand, stats_for

MASTER_SEED = {9: 20260927, 6: 20260926}


def adds_nothing(hole: list[str], board: list[str]) -> bool:
    """The fix's target, computed independently of `_made_bucket`: a five-card
    board, a straight-or-better best five, and the hole cards add nothing."""
    if len(board) != 5:
        return False
    best = _best5(list(hole) + list(board))
    return best[0] >= 4 and best == _best5(list(board))


def dump(seats: int, n_hands: int, out: str) -> None:
    if seats == 9:
        packs = load_persona_packs()
        lineup = {i: ea.DEFAULT_LINEUP[i % len(ea.DEFAULT_LINEUP)] for i in range(9)}
    elif seats == 6:
        packs = load_persona_packs(table_size=6)
        lineup = dict(SIXMAX_SEATS)
    else:
        raise ValueError(f"unsupported seats {seats}")
    master = random.Random(MASTER_SEED[seats])
    hand_seeds = [master.randrange(1_000_000_000) for _ in range(n_hands)]
    hands: list[Hand] = []
    with open(out, "w") as fh:
        for i, hand_seed in enumerate(hand_seeds):
            stacks = ea._draw_buyin_targets(hand_seed, 6) if seats == 6 else None
            res = ea.play_one_hand(
                random.Random(hand_seed + 1), hand_seed, i % seats, lineup, packs, stacks_bb=stacks
            )
            state = res["state"]
            pos_to_seat = {s.position: s.seat for s in state.seats}
            actions = [
                [pos_to_seat[h.position], h.position.value, h.street.value, h.action.value,
                 h.amount_bb]
                for h in state.action_history
            ]
            rec = {
                "i": i,
                "hand_seed": hand_seed,
                "board": list(state.full_board) if state.full_board else list(state.board),
                "holes": {str(s.seat): list(s.hole_cards) for s in state.seats},
                "personas": {str(k): v for k, v in lineup.items()},
                "actions": actions,
                "hand_row": res["hand"],
                "seat_rows": res["seats"],
                "decision_rows": res["decisions"],
            }
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
            hands.append(Hand(i, f"mr-{i}", state))
    # Per-seat river stats via the shared stat definitions (table_stats.stats_for).
    replays = {h.hand_no: replay(h) for h in hands}
    settles = {h.hand_no: settle_hand(h) for h in hands}
    nets = {k: v[0] for k, v in settles.items()}
    shows = {k: v[1] for k, v in settles.items()}
    summary = {}
    for seat in range(seats):
        st, _ = stats_for([seat], lineup, hands, replays, nets, shows)
        summary[str(seat)] = {k: v for k, v in st.items() if k.startswith("river_") or k in (
            "hands", "saw_flop", "wtsd_num", "vpip", "pfr")}
    with open(out + ".stats.json", "w") as fh:
        json.dump(summary, fh, sort_keys=True, indent=1)


def _load(path: str) -> list[dict]:
    with open(path) as fh:
        return [json.loads(line) for line in fh]


def _row_key(kind: str, row: dict) -> str:
    return json.dumps([kind, row], sort_keys=True)


def compare(before_path: str, after_path: str, lag_seat: int | None) -> int:
    before, after = _load(before_path), _load(after_path)
    assert len(before) == len(after), "dumps differ in hand count"
    out: list[str] = []
    n = len(before)
    exposed_hands = 0  # hands with >= 1 river decision by an adds-nothing bot (before)
    exposed_decisions = 0
    changed_hands = attributed_hands = 0
    unattributed_hands: list[str] = []
    changed_rows = attributed_rows = 0
    unattributed_rows: list[str] = []
    label_only_rows = 0
    decisions_changed = 0  # aligned decision rows (non-post) whose action/amount differ
    first_diff_kinds: Counter = Counter()
    first_diff_by_persona: Counter = Counter()
    for b, a in zip(before, after, strict=True):
        assert b["hand_seed"] == a["hand_seed"] and b["holes"] == a["holes"]
        board = b["board"]
        river_dec = [
            r for r in b["decision_rows"] if r["street"] == "river" and r["action"] != "post"
        ]
        exp = [r for r in river_dec if adds_nothing(b["holes"][str(r["seat"])], board)]
        if exp:
            exposed_hands += 1
            exposed_decisions += len(exp)
        hand_attributed = False
        if b["actions"] != a["actions"]:
            changed_hands += 1
            pairs = list(zip(b["actions"], a["actions"]))
            k = next((j for j, (x, y) in enumerate(pairs) if x != y), len(pairs))
            fb = b["actions"][k] if k < len(b["actions"]) else None
            fa = a["actions"][k] if k < len(a["actions"]) else None
            actor = (fb or fa)
            seat, street = actor[0], actor[2]
            ok = (
                fb is not None and fa is not None and fb[0] == fa[0] and street == "river"
                and adds_nothing(b["holes"][str(seat)], board)
            )
            if ok:
                attributed_hands += 1
                hand_attributed = True
                first_diff_kinds[f"{fb[3]}->{fa[3]}"] += 1
                first_diff_by_persona[b["personas"][str(seat)]] += 1
            else:
                unattributed_hands.append(
                    f"hand {b['i']} seed {b['hand_seed']}: first diff #{k} before={fb} "
                    f"after={fa} hole={b['holes'].get(str(seat))} board={board}"
                )
            bd = [r for r in b["decision_rows"] if r["action"] != "post"]
            ad = [r for r in a["decision_rows"] if r["action"] != "post"]
            decisions_changed += sum(
                1 for x, y in zip(bd, ad)
                if (x["seat"], x["action"], x["raise_to_bb"]) != (y["seat"], y["action"], y["raise_to_bb"])
            ) + abs(len(bd) - len(ad))
        # Row-level diff (multiset per hand, so knock-on reorders count once per row).
        rows_b = Counter(
            [_row_key("hand", b["hand_row"])]
            + [_row_key("seat", r) for r in b["seat_rows"]]
            + [_row_key("decision", r) for r in b["decision_rows"]]
        )
        rows_a = Counter(
            [_row_key("hand", a["hand_row"])]
            + [_row_key("seat", r) for r in a["seat_rows"]]
            + [_row_key("decision", r) for r in a["decision_rows"]]
        )
        diff = (rows_b - rows_a) + (rows_a - rows_b)
        n_diff = sum(diff.values())
        if not n_diff:
            continue
        changed_rows += n_diff
        if hand_attributed:
            attributed_rows += n_diff
            continue
        if b["actions"] != a["actions"]:
            unattributed_rows.append(f"hand {b['i']}: {n_diff} rows in an unattributed hand")
            continue
        # Same actions: only a hand_class_bucket relabel on an adds-nothing river row passes.
        for rb, ra in zip(b["decision_rows"], a["decision_rows"], strict=True):
            if rb == ra:
                continue
            only_label = {k for k in rb if rb[k] != ra[k]} == {"hand_class_bucket"}
            ok = (
                only_label and rb["street"] == "river"
                and adds_nothing(b["holes"][str(rb["seat"])], board)
                and rb["hand_class_bucket"].startswith("monster|")
                and ra["hand_class_bucket"].startswith("middle_pair|")
            )
            if ok:
                attributed_rows += 2  # the before row and the after row
                label_only_rows += 1
            else:
                unattributed_rows.append(f"hand {b['i']} seq {rb['seq']}: {rb} -> {ra}")
        if b["hand_row"] != a["hand_row"] or b["seat_rows"] != a["seat_rows"]:
            unattributed_rows.append(f"hand {b['i']}: hand/seat rows differ with same actions")

    out.append(f"before: {before_path}")
    out.append(f"after:  {after_path}")
    out.append(f"hands compared: {n}")
    out.append(
        f"hands with >=1 river decision by a bot whose hole cards add nothing to a board-made "
        f"straight-or-better (before): {exposed_hands} ({exposed_decisions} decisions)"
    )
    out.append(f"hands changed (action fingerprint differs): {changed_hands}")
    out.append(f"hands attributed (first differing action = such a river decision): {attributed_hands}")
    out.append(f"hands unattributed: {len(unattributed_hands)}")
    out.append(f"decision rows differing (aligned, incl. later knock-on in the same hand): {decisions_changed}")
    out.append(
        f"export rows changed (before+after rows, multiset diff): {changed_rows}; attributed: "
        f"{attributed_rows}; unattributed: {len(unattributed_rows)}"
    )
    out.append(f"  of which hand_class_bucket relabels with unchanged action (monster->middle_pair): {label_only_rows}")
    out.append(f"first differing action, before->after: {dict(sorted(first_diff_kinds.items()))}")
    out.append(f"first differing action by persona: {dict(sorted(first_diff_by_persona.items()))}")
    for line in unattributed_hands[:50]:
        out.append("UNATTRIBUTED HAND " + line)
    for line in unattributed_rows[:50]:
        out.append("UNATTRIBUTED ROW " + line)
    if lag_seat is not None:
        sb = json.load(open(before_path + ".stats.json"))[str(lag_seat)]
        sa = json.load(open(after_path + ".stats.json"))[str(lag_seat)]
        out.append(f"LAG (seat {lag_seat}) river stats on the matched sample, before -> after:")
        for key in sorted(set(sb) | set(sa)):
            out.append(f"  {key}: {sb.get(key, 0):g} -> {sa.get(key, 0):g}")
        for label, num, den in (
            ("river aggression share (bet+raise / seen)", "river_agg", "river_seen"),
            ("river raise when bet into", "river_raise_vs_bet", "river_faced_bet"),
            ("river fold when bet into", "river_fold_vs_bet", "river_faced_bet"),
            ("river call share (call / seen)", "river_call", "river_seen"),
        ):
            fb = sb.get(num, 0) / sb[den] if sb.get(den) else 0.0
            fa = sa.get(num, 0) / sa[den] if sa.get(den) else 0.0
            out.append(f"  {label}: {100 * fb:.2f}% -> {100 * fa:.2f}%")
    passed = changed_hands > 0 and not unattributed_hands and not unattributed_rows
    out.append(f"ATTRIBUTION: {'PASS' if passed else 'FAIL'}")
    print("\n".join(out))
    return 0 if passed else 1


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dump")
    d.add_argument("--seats", type=int, required=True)
    d.add_argument("--hands", type=int, required=True)
    d.add_argument("--out", required=True)
    c = sub.add_parser("compare")
    c.add_argument("before")
    c.add_argument("after")
    c.add_argument("--lag-seat", type=int, default=None)
    args = p.parse_args()
    if args.cmd == "dump":
        dump(args.seats, args.hands, args.out)
    else:
        sys.exit(compare(args.before, args.after, args.lag_seat))


if __name__ == "__main__":
    main()
```
