# Finding ledger — parallel wave 4: N-M4BET · N-TAGCOMP (2026-07-31)

> **LANDED 2026-08-01 as ONE COMBINED BRANCH `feat/persona-realism-wave4` (tip `3dcdeac`), stacked
> on wave-3's `e25abde`** — lane D tip `087e019` + lane C commits cherry-picked (zero conflicts) +
> the single-recorder fixture re-record: coverage **1269/317 = 25.0% cumulative vs the immutable
> 28.3% start (−3.3pp, recovering from wave 3's −3.8pp; graded ratchet 322→317 disclosed)**, all
> six goldens (maniac n=200 AF 3.27→4.82 = small-n composition, provenance in-file), all nine
> limper fires. One extra landing item: the BTN unopened-arrival DIRECTIONAL ceiling tripped
> (0.0784 vs 0.075) — a 10-seed PAIRED sweep attributed a REAL +0.0108 rise (t≈2.7) to the tag
> width trim (dossier-correct direction, not noise, not a collapse) → ceiling re-derived
> 0.075→0.11 per the W5-b4 precedent, floor kept, provenance in-file. Final full suite
> **1337 passed / 2 skipped, ZERO reds**, ruff clean. Push + PR pending network.

> Orchestration: two parallel worktree lanes ($TMPDIR/wt-m4bet, $TMPDIR/wt-tagcomp), both branches
> STACKED on the unmerged wave-3 tip `e25abde` (owner decision — GitHub unreachable from their
> location, so wave 3 is landed locally as `feat/persona-realism-wave3` and wave 4 builds on top;
> stack rebases with the `--onto` recipe if the wave-3 PR changes before merge). Owner approved
> "start both" 2026-07-31. Single-recorder law: builders leave fixtures untouched; orchestrator
> re-records once at landing on whichever tip lands last. Codex review + pushes may trail until
> network returns; both lanes still get refuter + persona-realism-theory-reviewer at fan-in.
> Tickets from the wave-3 filings block in the roadmap: `N-M4BET` (maniac vs_4bet arrival-weighted
> fold 0.814/call 0.046/jam 0.140 vs dossier 25/35/40 — ~74% of arriving combos have NO mix),
> `N-TAGCOMP` (tag suited/offsuit composition inverted; constant-width swap per the N-LAGLADDER
> lesson — the width axis is blocked on the §5 joint-consistency filing).

## Lane C — N-M4BET

Build (commit `d28001d`): maniac vs_4bet re-authored 6→13 first-match tiers, FULL coverage of the
arriving 3-bet range (explicit `*` catch-all), arrival-weighted aggregate 0.8143/0.0408/0.1449 →
0.2606/0.3359/0.4034 vs dossier 25/35/40. Arrival = own vs_rfi 3-bet mass = 284.4 combos = 21.45%
(refuter reproduced exactly; sits at the top edge of the dossier's own 14–22% 3-bet prediction —
theory confirmed the triple is being applied to a range equal-or-narrower than its source assumes,
so the fold level is conservative, not sticky). maniac.json 1.3.0→1.4.0.

Reviews: refuter PASS-WITH-ISSUES (2 MED + 3 LOW) · theory GO-WITH-ISSUES (1 HIGH + 3 MED + 2 LOW)
· Codex FAIL (1 HIGH = the deferred golden fixture, adjudicated process-correct + 1 MED + 1 LOW).

| ID | Sev | Finding | Adjudication |
|---|---|---|---|
| T-H1+C-M1+R-M1 | HIGH (3-way convergent, magnitudes reconciled) | the gate's arrival claim overreaches: `_preflop_facing` labels vs_4bet on raise-count n≥3, so the node also serves RE-ENTRANT strata (own 4-bet range facing a 5-bet; `5bet_shove` a misnomer there). Production-sizing measurement: modeled channel = **74.1%** of real maniac vs_4bet decisions (theory's 9.4% figure was a HARNESS-SIZING ARTIFACT — see R-L2). Codex added a vs_limpers iso→two-reraises arrival scenario; refuter disputes reachability — builder to settle by trace | **FIXED** — gate re-labeled as the conditional it is (the dossier row literally reads "facing a 4-bet after 3-betting", so the CONDITIONAL is the right target); "EXACTLY" deleted; stratified n=3 vs n≥4 REPORTED reading added; vs_limpers reachability settled + documented |
| T-M2 | MED | the dossier triple is an author-asserted calibration band (maniac.md:383 "do NOT present as measured") made a HARD two-sided gate — violates the never-HARD-while-unverified law; CONTRACT-DEFECT: no registry covers persona-dossier targets at all (now the de-facto target source of the whole preflop lane) | **FIXED** in-slice (one-sided red-first bounds fold<0.40 / call>0.15 / jam>0.25 + exact triple demoted to printed REPORT + provenance line) · registry extension **FILED** (joins the wave-3/4 contract filings) |
| T-M3 | MED | 77-99 jam 0.40→0.75 overturned a wave-3-theory-endorsed level on a fold-budget argument arithmetic refutes (holding 22-99 at {.4/.6}: aggregate fold ≈0.288, inside every bound); one scalar constraint cannot pin a 13-tier vector | **FIXED** — pairs 22-99 restored to flat {5bet_shove 0.40, fold 0.60}; kills T-L1's 99→TT jam inversion as a side effect; pins/gates updated |
| T-M4 | MED | the "pairs are JAM-OR-FOLD (no set-mining price)" law is inconsistent (AA-TT have call legs at the same SPR) and cites the wrong identity — §3 T3 direct-price math (~28% needed) says 77-99 CAN call | **PARTIAL + FILED** — law's scope narrowed to 22-66 with the T3 arithmetic stated; the 77-99 call-leg question filed as follow-up (no new unfit magnitudes this pass) |
| R-M2 | MED | the `*` catch-all permanently blinds RR-LINT's row-gap lint for the whole node and makes the coverage gate unable to ever fail again (observability traded for one 10-class pin) | **FIXED** — tail-mass tripwire added (`*` claims ≤0.15 of arriving mass; currently ~0.118) + the trade documented in gate + lint comments |
| R-M3 | LOW | hidden cross-node coupling: the gate reads vs_rfi to build weights — a future vs_rfi rewrite (R10 lane actively does this) reds the gate pointing at the wrong node; helpers ignore positions/role | **FIXED** — single-node asserts + by-design coupling documented ("re-derive arrival") |
| R-L2 | LOW | harness `_preflop_decision` sizes every raise at min_bb (production 5bet = all-in) → min-raise ping-pong wars in the harness only (5+ raise hands 0.30%→1.65% harness, 0.00% production) — a pre-existing instrument divergence this node amplifies; explains the theory-vs-refuter traffic-split discrepancy | **FILED** — instrument owner (harness sizing should mirror `preflop_raise_to`); noted in gate docstring |
| R-L3+C-L1+T-L2 | LOW | stale lint comment (quoted a mix two revisions old); red-first count at HEAD~1 is 4 (incl. the updated T-F3 pin) not 3; `_doc` "strength-ordered/strongest-first" inaccurate (two deliberate continue-mass inversions) | **FIXED** (comment corrected; counting documented; _doc reworded "authored priority (first-match-wins)" + inversions named) |
| C-H1 | HIGH→process | golden fixture not re-recorded in-slice | **NOT-A-DEFECT** — single-recorder law, orchestrator re-records at wave landing (refuter independently verified all three fixture reds are benign stream drift; coverage ratio actually IMPROVES 24.51→25.45%) |

Theory peer answers recorded: dossier's own 3-bet range ≥ pack's arrival (no category error on width);
A8o-A2o blocker-jam tier consistent with the wheel-ace polar family + T-F4; ±0.05 tolerance = the
source's granularity (correct, not false precision); Online row = right pool per contract §10.

## Lane D — N-TAGCOMP

Build (commit `7e8287b`): tag's nine `unopened` nodes re-emitted from NEW spec
`content/personas/ladders/tag.unopened.json` (third RR-EMIT spec) — constant-width offsuit→suited
swap, max per-seat total drift 0.45pp, pairs byte-identical, BTN suited-share 69.9→95.5%, offsuit
BTN 51→42%. Population VPIP 16.07→16.25 / PFR 12.80→12.83, both in §5. Emission STRING-identical
(refuter-verified); red-first at all nine seats on both new gate legs; wave-3 lag≥tag offsuit gate
untouched (comment-only), slack grew everywhere. tag.json 1.1.1→1.2.0.

Reviews: refuter **FAIL** (1 blocking HIGH + 1 MED + 3 LOW) · theory **GO-WITH-ISSUES** (2 HIGH:
1 in-slice-partial + 1 CONTRACT-DEFECT filed, 1 MED filed, 1 LOW) · Codex **PASS-WITH-ISSUES**
(1 MED + 1 LOW). Codex ran successfully despite the network outage (chatgpt.com intermittently
reachable).

| ID | Sev | Finding | Adjudication |
|---|---|---|---|
| R-1 | HIGH (blocking) | UNDISCLOSED 4th red: `test_four_bet_line_strict_subset_and_hand_computed_posterior` — UTG suited now A2s+, so A4s is reachable from the UTG open and (correctly) enters the 4-bet posterior via the vs_3bet A5s/A4s bluff tier; the test's own R10-3BET law says "update the pin, never carve the range", and the comment now asserts the opposite of reality | **FIXED** — pin re-recorded w/ A4s + comment rewritten |
| T-D1 | HIGH | three seeded fixtures red, no re-record, no cumulative delta in the commit | **NOT-A-SLICE-DEFECT** — single-recorder law: builders leave fixtures; orchestrator re-records ONCE at wave landing with the cumulative delta (same as waves 1–3); noted the wave's own parent commit is exactly such a re-record |
| T-D2 | HIGH | CONTRACT-DEFECT (ARRIVAL class): the width freeze is justified by metric #3 aggregate PFR, which measured arrival (UTG 1.000 … CO 0.120 / BTN 0.066 / SB 0.026) shows is ~85% an EP statistic and near-blind to late-seat width; authored widths sit OVER the tag dossier at 7 of 8 opening seats (CO 48.4 vs 25-29, BTN 58.2 vs 42-48 — ships K5o/Q7o/J7o button opens); a two-sided width pin would force the future trim to delete a green gate; theory estimates the dossier-ward trim costs only ~0.5pp PFR (12.98→~12.4, still in §5) | **PARTIAL-FIX + FILED** — in-slice: pin made ONE-SIDED (rise-ceiling only) + annotated. Filed forward: **`N-TAGWIDTH`** (trim tag per-seat width toward the dossier envelope — affordable per the arrival math) · contract filing: §5 needs a per-seat RFI row or an explicit statement that authored per-seat width is dossier-governed (metric #3 cannot police it) · the nit's W-ARR no-widening standing order EXTENDED to the tag |
| R-2+T-D3 | MED (convergent) | NEW roster inversion on the SUITED axis: tag now plays more suited than lag at CO (19.00 vs 17.01), BTN (22.47 vs 19.91), SB (18.25 vs 17.01) — structurally T-M2 with personas swapped; ungated (lag suited floor omits CO/BTN/SB) | **ACCEPT-AND-FILE → `N-LAGCOMP2`** (theory: the defect is the LAG's — its late-seat width sits in offsuit; a wider range should be a near-superset in suited; capping the tag would re-open T-M2). Extend `_LAG_SUITED_FLOOR` to CO/BTN/SB when it runs |
| C-1 | MED | pair-preservation gate checks aggregate % only, not the byte-identity the pack `_doc` promises (membership/weight swaps at constant mass would pass) | **FIXED** — per-class pair weights pinned exactly |
| C-2 | LOW | ±1.0pp total-width belt looser than the 0.45pp actual; permits simultaneous suited+offsuit trims (BTN counterexample constructed) | **FIXED** — subsumed by the T-D2 one-sided rise-ceiling |
| R-3+T-D4 | LOW | truncated `_doc` sentence in tag.json (dropped clause, dangling colon); §5 cite in pack without triple (pointer-style, spec has it) | **FIXED** — sentence repaired, §5 mention made an explicit cross-ref |
| R-4 | LOW | `_STATS_EXT_CACHE` keyed on (persona, n) only — an in-process before/after sweep silently returns the first reading for both sides (evidence-integrity hazard; the shipped claim survived a separate-process re-run) | **FILED** — joins the instrument ticket (add pack-identity to the cache key); not this lane's file |
| R-5 | LOW | tag `_stats` docstring sweep figures stale (pre-date several slices); continue row now 17.25 vs recorded sweep top 16.31 (in band) | **FIXED** — one-line staleness note |

Theory peer answers recorded: BTN 95.5% suited = solver-plausible SHAPE (a real 45% BTN opens
~the whole suited universe); the unrealism is the frozen WIDTH (→ N-TAGWIDTH). Fold-to-3bet
report drift 0.824→0.696 = mechanically necessary (suited opens hit the hand-keyed vs_3bet
continue rows more), direction toward dossier, still a REPORT.

**Folds commit `16c84aa`** — all five fixes applied; fix 2 (one-sided width gate) FORCED content
re-authoring (five suited edge classes dropped at UTG2/LJ/SB so no seat rises; suited floors still
clear by ≥0.7pp) → **DELTA RE-REVIEWED: PASS-WITH-ISSUES (4 doc-level)**. Refuter verified the
renamed gate BITES on the pre-fold content (three seats rose 0.15-0.45pp > the 0.1pp ceiling), the
per-class pair pin catches weight mutations the old aggregate missed, the A4s posterior re-pin is
arithmetically exact, no stale figure survived repo-wide, full suite = exactly the three fixture
reds. Delta issues D1 (contradictory width-gate docstrings), D2 (overstated suited-floor claim),
D3 (pre-existing (6,7)→(6,8) band mis-cite), D4 (no in-repo reproduction for the _doc sweep) —
ALL FIXED by the orchestrator in **`087e019`** (docstrings reconciled, cite fixed, report-only
`test_ntagcomp_tag_vpip_pfr_reported_not_gated` added). **Lane D CLOSED, tip `087e019`.**
