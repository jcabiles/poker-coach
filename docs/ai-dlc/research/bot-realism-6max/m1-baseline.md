# M1 — 6-max baseline report

<!-- summary, results and fidelity sections are written by T6 -->

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
