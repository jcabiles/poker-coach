# M1 — 6-max baseline report

**Bottom line.**
- **The simulation matches your table (verdict PASS).** In all 10 checks, the simulated bots enter and raise pots at rates consistent with what you saw in your 201 real hands, with no misses. The simulator can stand in for your play when tuning pre-flop behaviour. How the bots play after the flop has not been checked against your hands.
- **Several bots sit outside real 6-max ranges.** How often each bot plays and raises overall is in range for every bot except the calling station, which almost never raises.
  - **Opening by seat:** the TAG and LAG open far too many hands, most of all from the early seats. The TAG opens 29% from the first seat against a sourced 14%, and the LAG opens 38% against 20%. The calling station raises about 1% from every seat against a sourced 8–14%. The nit is in range except in the small blind, where it opens slightly too few hands.
  - **After the flop:** the nit and both TAGs reach showdown about twice as often as real players of their type. The TAG continuation-bets about 41% of the time against a sourced 60–70%.

## Run details

- **Command** (from `backend/`): `PYTHONPATH=. .venv/bin/python -m tools.sixmax_baseline --session 4b35736fa8c7438eb57ca9d09874f8dc --max-hand-no 201 --db /Users/johncabiles/Documents/Github/poker-coach/backend/data/poker_coach.db`
- **Seed:** 20260926 (default). **Simulated hands:** 6,000 (default). **Real session:** `4b35736fa8c7438eb57ca9d09874f8dc`, `--max-hand-no 201`, which gives 201 hands.
- **Git SHA:** `e12e244`, on branch `feat/m1-6max-baseline`. The tool prints `git SHA: unknown` when run inside a worktree, so the SHA was taken from `git rev-parse --short HEAD`.
- **Date:** 2026-09-26. The tool's own UTC date line reads 2026-09-27.
- **Reproducibility:** the command was run twice, and the two outputs were byte-identical. Every number below is copied from that output.
- **Conditions:** the seats copy the real session. Seat 0, which you occupy in real play, holds a TAG stand-in. Seats 3 and 4 are both TAGs and are pooled into one row in the simulation. Each simulated hand draws fresh 95–105bb stacks.

## Each bot against real 6-max ranges

**How to read these tables.** Each cell gives the number of chances the bot had, its rate, and the 95% interval, which is the Wilson score interval (the range the bot's true rate very likely lies in, given the sample). "Cited range" is the combined range from the verified sources in the "Ranges and sources" section below. The judgement follows these rules:
- **Combined range:** the lowest low to the highest high of that cell's VERIFIED figures. A single-point figure counts as that point. A one-sided figure such as "≤16" runs from 0, and one such as "32+" runs to 100. S12, whose format is unstated, may widen the range only when a source that states 6-max is also present. UNVERIFIED figures never count.
- **inside:** the simulated 95% interval overlaps the combined range. **outside:** it does not. **unsourced:** no verified source exists for that cell.

WTSD (went to showdown) is showdowns divided by flops seen, and a bot that is all-in when the board is dealt counts as having seen the flop. Flop c-bet (continuation bet) counts the flops where the last pre-flop raiser bets when it is first to act on an unbet flop.

### Nit

| Stat | Chances | Rate | 95% interval | Cited range | Judgement |
|---|---|---|---|---|---|
| VPIP | 5917 | 9.5% | 8.7–10.2% | 0–16 (S1, S5, S6, S7, S9, S10) | inside |
| PFR | 5917 | 6.7% | 6.1–7.4% | 0–14 (S5, S6, S7) | inside |
| RFI LJ | 1000 | 10.4% | 8.7–12.4% | 11 (S1) | inside |
| RFI HJ | 706 | 12.5% | 10.2–15.1% | 13 (S1) | inside |
| RFI CO | 366 | 15.8% | 12.5–19.9% | 16 (S1) | inside |
| RFI BTN | 261 | 26.8% | 21.8–32.5% | 23 (S1) | inside |
| RFI SB | 142 | 13.4% | 8.7–20.0% | 21 (S1) | outside (too tight) |
| Flop c-bet | 148 | 22.3% | 16.3–29.7% | unsourced (S14 is UNVERIFIED) | unsourced |
| WTSD | 464 | 58.6% | 54.1–63.0% | 0–25 (S10, S11) | outside (too high) |

### LAG

| Stat | Chances | Rate | 95% interval | Cited range | Judgement |
|---|---|---|---|---|---|
| VPIP | 5879 | 33.6% | 32.4–34.8% | 24–40 (S3, S5, S6, S7, S8) | inside |
| PFR | 5879 | 28.3% | 27.1–29.4% | 20–35 (S5, S6, S7, S8) | inside |
| RFI LJ | 1000 | 37.7% | 34.7–40.7% | 20 (S3) | outside (too loose) |
| RFI HJ | 886 | 47.0% | 43.7–50.2% | 23 (S3) | outside (too loose) |
| RFI CO | 615 | 48.6% | 44.7–52.6% | 33 (S3) | outside (too loose) |
| RFI BTN | 304 | 56.9% | 51.3–62.4% | 50 (S3) | outside (too loose) |
| RFI SB | 185 | 51.9% | 44.7–59.0% | 43 (S3) | outside (too loose) |
| Flop c-bet | 714 | 48.7% | 45.1–52.4% | unsourced | unsourced |
| WTSD | 1404 | 53.0% | 50.4–55.6% | unsourced | unsourced |

### TAG (seats 3 and 4 pooled)

| Stat | Chances | Rate | 95% interval | Cited range | Judgement |
|---|---|---|---|---|---|
| VPIP | 11828 | 22.6% | 21.9–23.4% | 17–28 (S2, S5, S6, S7, S8, S9, S11, S13, S12) | inside |
| PFR | 11828 | 17.9% | 17.2–18.6% | 16–24 (S5, S6, S7, S8, S9, S11, S12) | inside |
| RFI LJ | 2000 | 28.6% | 26.7–30.7% | 14 (S2) | outside (too loose) |
| RFI HJ | 1359 | 29.9% | 27.5–32.4% | 17 (S2) | outside (too loose) |
| RFI CO | 911 | 31.6% | 28.7–34.7% | 23 (S2) | outside (too loose) |
| RFI BTN | 631 | 45.6% | 41.8–49.5% | 37 (S2) | outside (too loose) |
| RFI SB | 296 | 36.5% | 31.2–42.1% | 37 (S2) | inside |
| Flop c-bet | 940 | 41.4% | 38.3–44.6% | 60–70 (S11; S9 and S12 alongside it) | outside (too low) |
| WTSD | 2224 | 55.5% | 53.4–57.5% | 22–28 (S10, S11) | outside (too high) |

S9's c-bet line and S12 carry no stated format, so they widen the TAG c-bet range only because S11 states 6-max. S2's SB figure may be a copy error on the source page (see the TAG ranges table), so the SB "inside" is weak evidence.

### Calling station

| Stat | Chances | Rate | 95% interval | Cited range | Judgement |
|---|---|---|---|---|---|
| VPIP | 5895 | 50.7% | 49.5–52.0% | 30–100 (S4, S5, S7, S9, S10) | inside |
| PFR | 5895 | 0.5% | 0.3–0.7% | 4–15 (S5, S7, S9, S10) | outside (too low) |
| RFI LJ | 1000 | 1.0% | 0.5–1.8% | 8 (S4) | outside (too low) |
| RFI HJ | 691 | 1.2% | 0.6–2.3% | 9 (S4) | outside (too low) |
| RFI CO | 512 | 0.6% | 0.2–1.7% | 9 (S4) | outside (too low) |
| RFI BTN | 308 | 1.0% | 0.3–2.8% | 11 (S4) | outside (too low) |
| RFI SB | 178 | 0.6% | 0.1–3.1% | 14 (S4) | outside (too low) |
| Flop c-bet | 7 | 28.6% | 8.2–64.1% | unsourced | unsourced |
| WTSD | 2805 | 64.8% | 63.1–66.6% | 30–100 (S10; S12 alongside it) | inside |

A station's open-limps count toward VPIP but not RFI, so a low RFI does not by itself mean the bot plays too few hands; its VPIP is in range. S4's RFI figures are raise-only too, though, so the comparison is like for like: S4's station raises 8–14% of first-in hands on top of limping, and this bot raises about 1%. This tool does not measure limp rate.

### Stand-in TAG (seat 0, your seat in real play)

This bot sits in the seat you occupy in real play. It is reported on its own and is not part of the fidelity check.

| Stat | Chances | Rate | 95% interval | Cited range | Judgement |
|---|---|---|---|---|---|
| VPIP | 5913 | 21.3% | 20.3–22.4% | 17–28 (as TAG) | inside |
| PFR | 5913 | 17.0% | 16.1–18.0% | 16–24 (as TAG) | inside |
| RFI LJ | 1000 | 29.4% | 26.7–32.3% | 14 (S2) | outside (too loose) |
| RFI HJ | 514 | 28.8% | 25.0–32.9% | 17 (S2) | outside (too loose) |
| RFI CO | 370 | 29.5% | 25.0–34.3% | 23 (S2) | outside (too loose) |
| RFI BTN | 261 | 45.6% | 39.7–51.7% | 37 (S2) | outside (too loose) |
| RFI SB | 153 | 45.8% | 38.1–53.7% | 37 (S2) | outside (too loose) |
| Flop c-bet | 322 | 46.3% | 40.9–51.7% | 60–70 (as TAG) | outside (too low) |
| WTSD | 762 | 46.7% | 43.2–50.3% | 22–28 (as TAG) | outside (too high) |

## Does the simulation match the real session? (fidelity check)

The rule was fixed before the run. A comparison is eligible if the real hands gave it at least 30 chances. Fewer than 8 eligible comparisons gives "can't tell yet". Otherwise the result is PASS with at most 1 miss, and FAIL with 2 or more. A comparison passes if the real rate falls inside the "pass range", which is the simulated 95% interval widened by the real sample's own interval. Each real TAG seat is compared with the pooled simulated TAG.

| Real bot | Stat | Real | Sim (compared group) | Pass range | Eligible | Result |
|---|---|---|---|---|---|---|
| nit | VPIP | n=193 · 11.4% [7.6%, 16.7%] | n=5917 · 9.5% [8.7%, 10.2%] | [4.2%, 14.7%] | yes | pass |
| nit | PFR | n=193 · 9.3% [6.0%, 14.3%] | n=5917 · 6.7% [6.1%, 7.4%] | [2.0%, 11.6%] | yes | pass |
| lag | VPIP | n=198 · 36.4% [30.0%, 43.3%] | n=5879 · 33.6% [32.4%, 34.8%] | [25.7%, 41.4%] | yes | pass |
| lag | PFR | n=198 · 29.8% [23.9%, 36.5%] | n=5879 · 28.3% [27.1%, 29.4%] | [20.8%, 35.7%] | yes | pass |
| tag seat 3 | VPIP | n=195 · 18.5% [13.6%, 24.5%] | n=11828 · 22.6% [21.9%, 23.4%] | [16.5%, 28.8%] | yes | pass |
| tag seat 3 | PFR | n=195 · 13.3% [9.3%, 18.8%] | n=11828 · 17.9% [17.2%, 18.6%] | [12.4%, 23.3%] | yes | pass |
| tag seat 4 | VPIP | n=197 · 18.3% [13.5%, 24.3%] | n=11828 · 22.6% [21.9%, 23.4%] | [16.5%, 28.8%] | yes | pass |
| tag seat 4 | PFR | n=197 · 13.2% [9.2%, 18.6%] | n=11828 · 17.9% [17.2%, 18.6%] | [12.5%, 23.3%] | yes | pass |
| station | VPIP | n=195 · 54.4% [47.4%, 61.2%] | n=5895 · 50.7% [49.5%, 52.0%] | [42.5%, 58.9%] | yes | pass |
| station | PFR | n=195 · 1.5% [0.5%, 4.4%] | n=5895 · 0.5% [0.3%, 0.7%] | [-1.6%, 2.6%] | yes | pass |

**Verdict: PASS** — 10 eligible, 0 miss(es).

The two real TAG seats sit close to the bottom of their pass ranges (VPIP about 18% against a simulated 22.6%, PFR about 13% against 17.9%). Both pass, but this is the closest the check came to a miss.

## Flop c-bet — not tested against real play

The real session gave too few c-bet chances for any bot except the LAG to be eligible, and c-bet was excluded from the check by owner ruling. These counts are reported only to show how thin the real sample is.

| Real bot | Real c-bet chances | Real c-bet |
|---|---|---|
| nit | 10 | n=10 · 20.0% [5.7%, 51.0%] |
| lag | 30 | n=30 · 50.0% [33.2%, 66.8%] |
| tag seat 3 | 9 | n=9 · 22.2% [6.3%, 54.7%] |
| tag seat 4 | 13 | n=13 · 46.2% [23.2%, 70.9%] |
| station | 0 | n=0 · — |


## Ranges and sources

**Summary.** Pre-flop stats (VPIP, PFR, and raise-first-in by seat) are sourced for all four bot types from pages fetched on 2026-09-26, though the only per-seat source never states its table format outright. Post-flop stats are thin: flop c-bet is sourced only for the TAG, and showdown rate (WTSD) is sourced for TAG and calling station, with the nit's WTSD resting on a label mapping and the LAG's WTSD and c-bet missing entirely.

- **Date:** 2026-09-26
- **Method:** Web search, then a direct fetch of every page cited as VERIFIED. Search-result snippets were never used as evidence. Each page's format claim was re-checked in a second fetch, because a full-ring figure must never enter a 6-max cell.
- **Labels.** VERIFIED means the figure appears on a page fetched directly on 2026-09-26. DERIVED means arithmetic on sourced figures, with the arithmetic shown. UNVERIFIED means recall or snippet hearsay; it may be shown but is **never usable for judging**. `unsourced` means no source was found.
- **Seat mapping.** 6-max sources name the five opening seats UTG, MP or HJ, CO, BTN (or BU), SB. This project's 6-max seats are LJ, HJ, CO, BTN, SB, so source "UTG" is read as LJ and source "MP"/"HJ" as HJ. That is a naming match, not arithmetic.
- **Stat glosses.** VPIP is the % of hands where the player voluntarily puts money in pre-flop. PFR is the % of hands raised pre-flop. RFI (raise first in) is the % of hands opened with a raise when everyone before has folded. Flop c-bet is the % of flops where the pre-flop raiser bets. WTSD is the % of flops seen that reach showdown.

### Provenance triples

| ID | (format, pool, source) | Verification | Applicability |
|----|------------------------|--------------|---------------|
| S1 | (6-max **inferred**, NL10 online, PokerStrategy "Average Pre-flop Ranges: Nit" — pokerstrategy.com/strategy/bss/average-pre-flop-ranges-nit/) | VERIFIED, fetched 2026-09-26 | USABLE WITH CAVEAT. Page says the ranges "have been determined by experts using tracking software"; the series lesson (pokerstrategy.com/strategy/bss/average-range/) says "database analysis of a couple million hands". The page never writes "6-max"; format is inferred from its six-seat set UTG, MP, CO, BU, SB, BB. Updated 12 Mar 2026, PokerStrategy Editorial. |
| S2 | (same series, "Average Pre-flop Ranges: TAG" — …/average-pre-flop-ranges-tag/) | VERIFIED, fetched 2026-09-26 | Same caveat as S1. |
| S3 | (same series, "Average Pre-flop Ranges: LAG" — …/average-pre-flop-ranges-lag/) | VERIFIED, fetched 2026-09-26 | Same caveat as S1. |
| S4 | (same series, "Average Pre-flop Ranges: Calling Station" — …/average-pre-flop-ranges-calling-station/) | VERIFIED, fetched 2026-09-26 | Same caveat as S1. |
| S5 | (6-max online cash, unstated pool, FreeBetRange "VPIP and PFR in Poker", K. Abbakumov, 2026-07-10 — freebetrange.com/academy/vpip-and-pfr-what-these-stats-tell-you-about-every-player-at-the-table/) | VERIFIED, fetched 2026-09-26 | APPLICABLE (states 6-max; says full ring runs ~3–8 VPIP lower). Coaching bands, not measured. |
| S6 | (6-max, unstated pool, PokerAlpha "How Do You Categorize Poker Players?", 2026-04-04 — poker-alpha.com/en/insights/player-categorization/) | VERIFIED, fetched 2026-09-26 | APPLICABLE. Nit band credited to PokerTracker stats; TAG/LAG bands credited to Upswing Poker. Second-hand. |
| S7 | (6-max tables, unstated pool, Beasts of Poker "Types of poker players", 2021-04-16 — beastsofpoker.com/types-of-poker-players/) | VERIFIED, fetched 2026-09-26 | APPLICABLE. Single "~" points, not bands; no data source. |
| S8 | (6-max, unstated pool, 888poker "How to play loose aggressive poker", T. Allin, 2026-09-19 — 888poker.com/magazine/strategy/how-to-play-loose-aggressive-poker) | VERIFIED, fetched 2026-09-26 | APPLICABLE. Coaching prose. |
| S9 | (6-max cash, unstated pool, PokerCoaching.com "Poker stats" + "VPIP poker stat", J. Little, 2024-07 — pokercoaching.com/blog/poker-stats/ and pokercoaching.com/blog/vpip-poker-stat/) | VERIFIED, fetched 2026-09-26 | APPLICABLE for VPIP/PFR (6-max stated). The c-bet "about 70 … solid player" line carries no format. |
| S10 | (6-max NLHE cash ~100bb, unstated pool, Poker Skill glossary: VPIP and WTSD pages — pokerskill.com/poker-glossary/vpip/ and pokerskill.com/poker-glossary/wtsd/) | VERIFIED, fetched 2026-09-26 | APPLICABLE (both pages state 6-max; WTSD page states ~100bb). Undated. Labels are "tight folder / standard reg / sticky reg / station", not bot-type names. |
| S11 | (6-max small-stakes cash NL2–NL25, author guidance, BlackRain79 "Best poker HUD stats" + "What is a good WTSD" — blackrain79.com/2017/10/what-are-the-best-poker-hud-stats.html and blackrain79.com/2019/10/what-is-good-wtsd-in-poker.html) | VERIFIED, fetched 2026-09-26 | APPLICABLE for the 6-max column only. Describes an ideal *winning* player (20/17, c-bet 70, WTSD 27), read here as TAG. His full-ring column (15/12, WTSD 25) is NOT-APPLICABLE and not imported. |
| S12 | (cash, **format unstated**, DeepFold "HUD stats guide", 2025-11-05 upd. 2026-05-02 — deepfold.co/en/blog/hud-stats-guide) | VERIFIED, fetched 2026-09-26 | WEAK. The page never says 6-max or full ring. Shown only beside 6-max-stated sources, never alone. |
| S13 | (6-max, "most regulars", PokerListings "Interpreting your opponents' stats", upd. 2026-07-24 — pokerlistings.com/strategy/interpreting-your-opponents-stats) | VERIFIED, fetched 2026-09-26 | APPLICABLE for VPIP only ("For 6-max no-limit hold'em most regulars fall between 19-25% VPIP"). Its WTSD 20–32 and c-bet 55–88 are for "most players" with no format and no type, so they are not used. |
| S14 | (—, —, search-result snippet "nits … c-bet more than around 60%") | UNVERIFIED. The snippet was attributed to pokercoaching.com, but the fetched page does not contain it. | Never usable for judging. |

### Nit

| Stat | Range (triple, label) |
|------|-----------------------|
| VPIP | ≤16 (S1, VERIFIED); 8–15 (S5, VERIFIED); <15 (S6, VERIFIED); ~16 (S7, VERIFIED); ≤14 (S9, VERIFIED); 0–15 (S10, VERIFIED); 15 (S12, VERIFIED, format unstated) |
| PFR | 7–13 (S5, VERIFIED); <12 (S6, VERIFIED); ~14 (S7, VERIFIED); 12 (S12, VERIFIED, format unstated) |
| RFI LJ | 11 (S1, VERIFIED) |
| RFI HJ | 13 (S1, VERIFIED) |
| RFI CO | 16 (S1, VERIFIED) |
| RFI BTN | 23 (S1, VERIFIED) |
| RFI SB | 21 (S1, VERIFIED) |
| Flop c-bet | >~60 (S14, UNVERIFIED — never usable) |
| WTSD | 0–22 (S10, VERIFIED; source label "tight folder", mapping to nit is ours); <25 (S11, VERIFIED; source label "tight poker player") |

### TAG (tight-aggressive)

| Stat | Range (triple, label) |
|------|-----------------------|
| VPIP | 17–25 (S2, VERIFIED); 20–28 (S5, VERIFIED); 18–22 (S6, VERIFIED); ~21 (S7, VERIFIED); ~23 (S8, VERIFIED); 22–28 "solid/winning player" (S9, VERIFIED); 20 (S11, VERIFIED); 19–25 "most regulars" (S13, VERIFIED); 22 (S12, VERIFIED, format unstated) |
| PFR | 17–24 (S5, VERIFIED); 16–20 (S6, VERIFIED); ~19 (S7, VERIFIED); ~18 (S8, VERIFIED); 17–22 "aggressive regular" (S9, VERIFIED); 17 (S11, VERIFIED); 19 (S12, VERIFIED, format unstated) |
| RFI LJ | 14 (S2, VERIFIED) |
| RFI HJ | 17 (S2, VERIFIED) |
| RFI CO | 23 (S2, VERIFIED) |
| RFI BTN | 37 (S2, VERIFIED) |
| RFI SB | 37 (S2, VERIFIED; the SB hand list on the page is identical to its BTN list, which looks like a copy error on the page) |
| Flop c-bet | 70 (S11, VERIFIED; ideal winning 6-max player); ~70 "solid player" (S9, VERIFIED, format not attached to this line); ~60 (S12, VERIFIED, format unstated) |
| WTSD | 27 (S11, VERIFIED; 6-max winning regulars); 22–28 "standard reg" (S10, VERIFIED) |

### LAG (loose-aggressive)

| Stat | Range (triple, label) |
|------|-----------------------|
| VPIP | 26–35 (S3, VERIFIED); 28–40 (S5, VERIFIED); 24–30 (S6, VERIFIED); ~28 (S7, VERIFIED); 25–35 (S8, VERIFIED); 28 (S12, VERIFIED, format unstated) |
| PFR | 24–35 (S5, VERIFIED); 20–26 (S6, VERIFIED); ~26 (S7, VERIFIED); 20–25, "within about five points of VPIP" (S8, VERIFIED); 24 (S12, VERIFIED, format unstated) |
| RFI LJ | 20 (S3, VERIFIED) |
| RFI HJ | 23 (S3, VERIFIED) |
| RFI CO | 33 (S3, VERIFIED) |
| RFI BTN | 50 (S3, VERIFIED) |
| RFI SB | 43 (S3, VERIFIED) |
| Flop c-bet | unsourced |
| WTSD | unsourced |

### Calling station

| Stat | Range (triple, label) |
|------|-----------------------|
| VPIP | 30–100 (S4, VERIFIED); 40–70+ "fish/passive caller" (S5, VERIFIED); ~40 (S7, VERIFIED); 35 "loose-passive station" example (S10, VERIFIED); 40 "fish" example (S9, VERIFIED) |
| PFR | 4–10 "fish/passive caller" (S5, VERIFIED); ~15 (S7, VERIFIED); 8 example (S10, VERIFIED); 12 example (S9, VERIFIED) |
| RFI LJ | 8 (S4, VERIFIED; the same seat also limps 41%) |
| RFI HJ | 9 (S4, VERIFIED; limps 43%) |
| RFI CO | 9 (S4, VERIFIED; limps 43%) |
| RFI BTN | 11 (S4, VERIFIED; limps 43%) |
| RFI SB | 14 (S4, VERIFIED; limps 64%) |
| Flop c-bet | unsourced |
| WTSD | 32+ "station / call-down" (S10, VERIFIED); >30 (S12, VERIFIED, format unstated) |

A station's RFI is a raise-only rate. Its open-limps are VPIP but not RFI, so a bot that limps where S4 limps is on-profile even though its RFI is low.

### Balanced-play reference (solver-style; NOT a range for any bot type)

These are published solver-derived 6-max 100bb opening charts, the same T2 triple recorded in `rfi-seat-provenance.md` (the 9-max provenance note, where they were flagged not-applicable to full ring). Here they apply in format but describe balanced play only. None may stand in for a nit, TAG, LAG or station cell. All three were re-fetched on 2026-09-26.

| Source | LJ | HJ | CO | BTN | SB |
|--------|----|----|----|-----|----|
| B1 Preflop Wizard, preflopwizard.app/blog/preflop-charts (solver, 100bb, upd. Aug 2026) — VERIFIED | ~15 | ~19 | ~27 | ~43 | ~36 |
| B2 GTO Gecko, gtogecko.com/blog/preflop-charts-opening-ranges (solver, 100bb, 2026-06-11) — VERIFIED | ~18 | ~22 | ~28 | ~43 | ~40 raise (~48 incl. limp) |
| B3 nlh.poker "6-Max RFI Ranges", nlh.poker/articles/six-max-rfi-range-guide-en (solver, ~100bb, 2026-06-12) — VERIFIED | ~17 | ~21 | ~28 | ~43 | ~24 raise (+~38 limp) |

B3's SB mixes raises and limps, so its raise-only 24 is not comparable to B1's raise-or-fold 36.

### What could not be sourced

- **LAG flop c-bet and LAG WTSD.** No fetched page gives either figure for a loose-aggressive player in any format.
- **Calling-station flop c-bet.** Pages describe stations only as "low fold-to-c-bet" (how often they fold when someone else c-bets), which is a different stat.
- **Nit flop c-bet.** The only figure (S14) is a search snippet the cited page did not contain, so it stays UNVERIFIED.
- **A 6-max source that states its format and gives per-seat opens by player type.** S1–S4 are the only per-type per-seat source; the format is inferred from the seat names, and the method is "experts using tracking software" with no sample stated beyond "a couple million hands".
- **Measured pool data.** Every VERIFIED figure is coaching guidance or an expert estimate; none is a published hand-database measurement split by player type. Pages that fetched with HTTP 403 and were not used: the PokerStrategy forum thread "6 max stats for identifying player types", the TwoPlusTwo "Classifying different player types" thread, and VIP-Grinders "fish".

## Known limits

- **The stand-in TAG sat in your seat.** In the real session you, not a bot, occupied seat 0, so the other bots faced a different opponent there than in the simulation.
- **Stack depth differs.** Simulated stacks were 95–105bb each hand, while the real session carried stacks over between hands, up to about 455bb. The bots' pre-flop decisions do not read stack size, so the VPIP and PFR comparisons are unaffected. Post-flop stats (c-bet, WTSD) may be affected.
- **The real sample is 201 hands.** That gives each bot about 195 VPIP/PFR chances and only 5 to 34 chances per seat for opening, which is why only VPIP and PFR could be checked against real play.
- **The ranges are coaching guidance, not measured pool data.** No verified source is a published hand-database measurement split by player type. The only per-seat opening source (S1–S4) never states that it is 6-max; its format is inferred from its seat names.
- **WTSD is compared across definitions.** This tool counts an all-in player who sees the board as having seen the flop. Tracking software may count this case differently; the size of that effect was not measured.
