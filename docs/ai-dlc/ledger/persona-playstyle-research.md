# Findings — persona-playstyle-research

Pass 1 — 2026-07-28 · 3 Claude sonnet refuters (cross-family vs Codex-authored dossiers) · locked checklist: fabricated/misread sources · unsupported leaps · missing counter-evidence · staleness · template completeness · internal contradictions · poker-math sanity. No web access (sandbox) — source-existence checks are plausibility-only.

| ID | Target | Severity | Finding | Evidence | Status | Resolution test |
|----|--------|----------|---------|----------|--------|-----------------|
| R2-L1 | lag.md#19 | major | RFI-by-position table and aggregate VPIP target don't reconcile — naive wiring overshoots VPIP 25-31 | RFI midpoints UTG→SB avg ≈32.75% before adding cold-calls/BB defense | open | derive aggregate from per-position table before use; state opportunity weighting |
| R2-L2 | lag.md#19 | major | Sizing splits / bluff-eligibility / postflop freq tables synthesized to satisfy "numbers not adjectives" — zero citation; §18 admits "no info found" for the same stats | lag.md:339 vs :253; :375,382 uncited | open | treat §19 as structured prior, re-derive empirically vs sim output |
| R2-L3 | lag.md#13 | minor | Source concentration: one vendor (Poker Copilot) under many sub-URLs poses as diversity | §14 admits editorial heuristics | open | weight as single source in synthesis |
| R2-L4 | lag.md#13 | minor | Suspiciously exact figures attributed to blog posts; URLs unverifiable in sandbox | e.g. "Hand2Note documents 71% fold-to-c-bet" lag.md:117 | open | human URL spot-check if a number becomes load-bearing |
| R2-L5 | lag.md#3 | minor | No engagement with LAG-cohort rarity at 2026 low stakes | — | open | note in synthesis; doesn't gate parameters |
| R2-M1 | maniac.md#19 | major | Independently-sampled VPIP 48-62 and PFR 36-50 ranges permit PFR>VPIP (impossible) | maniac.md:389-391; ratio row 0.70-0.88 is the real constraint | open | derive PFR = VPIP × ratio, never sample both |
| R2-M2 | maniac.md#3/#18 | major | Persistent stable maniac may not exist in nature (mostly short-lived/tilt); dossier assumes 100k-hand-stable archetype | maniac.md:11-12 carve-outs; :364 | open | OWNER question: app personas are deliberately idealized-distinct caricatures (theory contract §1) — likely accepted-by-design |
| R2-M3 | maniac.md#19 | major* | Aggregate AF 4.0-10.0 likely unreachable once 65%-weight "sticky" subtype (call-heavy) is applied; no AF adjustment row | maniac.md:395 vs :159-164,:577-584 | open | check AF math if subtypes ever implemented |
| R2-M4 | maniac.md#17vs19/20 | minor | 0.35-0.40 self-rated confidence presented as exact tables/predictions | maniac.md:352-354 vs :548,:618 | open | carry confidence marks into synthesis |
| R2-M5 | maniac.md#13 | minor | Poker Copilot concentration (7/12 sources); Beat The Fish anchors core signature at low-med quality | maniac.md:265-269,:289 | open | as R2-L3 |
| R2-M6 | maniac.md#12 | minor | (No contradiction — LAG/maniac boundary consistent across dossiers; noted for completeness) | maniac.md:257 vs lag.md#19 | accepted | — |

*R2-M3 reported as "medium"; ledger normalizes to major (affects a #19 parameter).

| R3-C1 | both#13 | major | Same Hand2Note URL dated "undated" in station dossier but "2024-08" in fish dossier — one is wrong; all month-precise Hand2Note dates suspect | calling_station.md L177 vs passive_fish.md L186 | open | human URL check before trusting dated citations |
| R3-C2 | both#4/#19 | major | Backbone stat pair (47-48% limp range, ~2.6-3% limp-reraise) attributed to 3 nominally distinct Hand2Note posts across dossiers — possible conflation/recycling | station L48 vs fish L51 | open | human URL check; treat as ONE source |
| R3-C3 | both#12 | major | Station/fish boundary drawn two ways: station doc says station is SUBTYPE of fish; fish doc says SIBLINGS split by fold-to-cbet/WTSD | station L166 vs fish L177 | open | Director adjudicates in synthesis (sibling reading fits app roster) |
| R3-C4 | both#19 | major | Fish 4-bets 8-12% after open-facing-3bet vs station 1-4% in same spot — backwards vs both docs' own passivity ordering | station L321 vs fish L338 | open | do not wire fish 4-bet range as-is |
| R3-C5 | both#19 | major | WWSF vs (WTSD×W$SD) gap requires non-showdown wins their own stated AFq/PFR can't generate — jointly-infeasible band class (same class as W4-b incident) | station L281-283 arithmetic | open | joint-feasibility check vs engine action tree before any target adoption |
| R3-F1 | fish#19 | major* | Hand-family rows (limp/raise/fold) don't sum to 100 at bounds (80-125%) — independent sampling hazard | fish L317 | open | normalize rows before use |
| R3-F2 | fish#19 | major* | 5-bet 35-60% in limp-reraise-facing-4bet corner vs AF 0.5-1.0 framing — unreconciled spike | fish L339-340 | open | cap or justify before wiring |
| R3-C6 | both#7vs19 | major* | Both docs say "no sizing-distribution evidence found" then present precise sizing tables uncited | station L92 vs L382-395; fish L114 vs L404-419 | open | sizing tables = hypothesis only |
| R3-C7 | station#19 | minor | limp+RFI ranges don't bound stated VPIP (±1-2pp slop) | station L291 | open | arithmetic-normalize |
| R3-C8 | both#13 | minor | Load-bearing live anchor is a 2015-2017 PokerNews article; staleness undiscussed | station L179 | open | note in synthesis |

*reported "medium"; normalized major (affects #19 parameters).

| R1-N1 | nit.md#19 | major | "Attempt to steal 18-28%" mathematically unreachable from its own CO/BTN/SB RFI table (best-case avg ~17.3, BTN ceiling 21) | steal row vs RFI table | open | recompute steal from RFI components |
| R1-N2 | nit+tag#19 | major* | VPIP/PFR bands sampleable independently permit PFR>VPIP; gap row must be the joint constraint | nit 8-13/6-11; tag live 18-27/14-21 | open | always derive PFR via gap/ratio |
| R1-T1 | tag.md#1/#13vs19 | major | Own best source (Hand2Note 242-TAG live db: AF 1.6, 3bet 13%) EXCLUDED by the doc's own live bands (AF floor 1.7, 3bet ceiling 10) — unreconciled | #19 AF 1.7-2.5, 3bet 6-10 | open | human URL check; treat live bands as unsettled |
| R1-T2 | tag.md#13 | major | Live 3-bet 13% claim inconsistent with live-passivity narrative and online 5-9% benchmark — possible denominator misread | — | open | human URL check |
| R1-T3 | tag.md#6vs19 | major* | OOP c-bet candidate band 28-45 vs cited source baseline 0-30 — 2pt overlap only | — | open | prefer cited baseline |
| R1-T4 | tag.md#20 | major* | "BTN>=3.2x UTG RFI" prediction fails its own ranges (38/12=3.17) | #19 RFI table | open | fix threshold to match ranges |
| R1-T5 | tag.md#1vs19 | minor | #19 silently widens beyond #1 anchor (VPIP 16->18, PFR 14->16) | — | open | note |
| R1-T6 | nit+tag#19 | minor | 3-bet-range allocation % semantics ambiguous (per-class mix vs share-of-range) | — | open | read as per-class mixing freq (solver convention) in synthesis |
| R1-T7 | nit#14 | minor | nit doc omits staleness caveat tag doc applies to the same 2016-17 Poker Copilot source | — | open | apply staleness caveat to both |
| R1-T8 | tag#4/#19 | major* | Load-bearing per-seat RFI table rests on single unaudited "Preflop Wizard" chart (undisclosed solver config, missing MP row) | tag#14 self-note | open | treat per-seat numbers as directional |
| R1-T9 | nit+tag#19 | minor | Sizing splits & bluff-composition tables uncited/self-admitted invented | nit#9 admission | open | hypothesis only (same as R3-C6) |

*reported "medium"; normalized where it affects #19 parameters.

Verdicts pass 1 (all 6): every dossier SOUND-WITH-FINDINGS; none fabricated; all #19 tables = structured calibration HYPOTHESES requiring joint-feasibility + empirical re-derivation, never direct wiring. Cross-cutting: (a) PFR-vs-VPIP joint-sampling hazard in 3 dossiers; (b) sizing tables invented in all 6; (c) source concentration (Poker Copilot + Hand2Note blogs); (d) station/fish boundary drawn inconsistently (R3-C3).

---

Pass 2 — 2026-07-28 · ONE Opus refuter (owner-directed, high effort) over the 7 RUBRIC files (`playstyle-research/rubrics/`) · new question: fitness of the distilled rubrics for 500-hand grading (attribution fidelity, poker correctness, gradeability, cross-rubric discrimination, baseline math, coverage).

Findings O-1..O-28 (full text in session transcript; fix text supplied by reviewer). Verdicts: baseline-good-play UNRELIABLE (O-1 blocker: jam-commit threshold `E≥B/(P+2B)` misapplied as thin-value-bet bar — correct bar is E>50% vs calling range) · passive_fish UNRELIABLE (O-2 blocker: the pass-1-corrected WTSD mislabel SURVIVED in red-flag 9) · calling_station UNRELIABLE (O-3 blocker: station's size-elasticity numbers are the FISH's sample; contract says station INELASTIC 3-15→18-40) · nit/tag/lag/maniac SOUND-WITH-FINDINGS.

Director adjudication: ALL 28 ACCEPTED (no finding refuted on pushback; O-1/O-2/O-3 independently re-verified — O-1 math re-derived, O-2 line 85 confirmed in file, O-3 dossier L90 quote confirmed). ONE modification: O-18's shared size ladder uses the ENGINE's RES-E cutoffs (SMALL ≤0.40 · MED 0.41–0.70 · LARGE 0.71–1.10 · OVERBET >1.10 pot), not the reviewer's 33/66/100 — graded hands will be measured against engine sizes and contract §5's elasticity slopes are RES-E-bucketed. O-13 fixed via the caveat (cell re-derivation deferred — calibration work, not rubric work). Coverage gaps 1–9 accepted → new shared `rubrics/grading-protocol.md` (two-layer method, precedence rules, size ladder, limped-pot norms, BvB position [BB is IP vs SB — contract §9 #11], facing check-raise, river-raise defaults, arrival boundaries for the loose personas). Status of all O-findings: **fixed** (4-agent apply wave + Director fan-in, 2026-07-28). Fan-in corrections on top of the wave: (1) the O-28 verbatim-copied table-size note carried nit-specific claims into station/maniac/fish — rewritten (recreational archetypes were NOT moved by ledger #14; fish VPIP moved UP); LAG's copy was factually fine and kept. (2) tag.md's 5a bucket re-sorted 2→5 single-hand flags (open-limp, river-raise call w/ one pair, EP cold-call of 3-bet), 5b renumbered 6–18, cross-refs fixed. (3) grading-protocol.md precedence/§10 aligned to the real 5a/5b/5c headers (it was written before the splits landed). (4) baseline §2.5 worked-example arithmetic Director-verified (12 vs 11bb; 2 vs 6bb — correct). Final set: 8 files, 1186 lines, greps clean.

---

Post-pass-2 spot-check (Director, 2026-07-28): the two most load-bearing dossier quotes the Opus reviewer was trusted on were verified against the dossiers directly — O-3's "passive-fish sample folded 60% to river overbets vs 31–38%" appears verbatim in calling_station.md (dossier §7), confirming the station-rubric fix; R1-T1's Hand2Note 242-TAG figures (AF 1.6, 3-bet 13%) appear verbatim in tag.md §1 with the dossier's own "direction, not a direct target" caveat. Reviewer's source-reading: CONFIRMED on both. Remaining unverified residue: external URLs only (no web access).
