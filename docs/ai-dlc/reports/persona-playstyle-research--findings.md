# Persona playstyle research — findings + engine verdict (Director report, full tier)

Initiative: persona-playstyle-research · 2026-07-28 · gated plan `plans/persona-playstyle-research.md` (approved) · ledger `ledger/persona-playstyle-research.md`

## 1. Executive summary

Six independent Codex-Sol dossiers (one per persona, blind to the implementation, low-stakes live+online anchor) were cross-checked against an exact computation of what the engine's persona packs actually do preflop and a mechanism map of the postflop merit engine. **The engine's architecture is largely RIGHT — the roster's identity ordering, street decay, multiway damping, elasticity split, and draw-based semi-bluffing all match research. The engine's NUMBERS are wrong in four big, systematic ways:** (1) the tight personas open ~2× too many hands (nit VPIP ~28 vs research 8–13); (2) every persona is a pushover against 3-bets/4-bets (engine folds 84–99% where research says 25–65%, persona-dependent — the single least-differentiated axis in the roster); (3) the maniac is *tighter* than the LAG (VPIP 33.7 vs 43.1) and folds AA/KK preflop 15–30% of the time via an authoring artifact; (4) WTSD (how often a bot reaches showdown) runs roughly double the research bands for the passive personas (station pinned 66–72% vs research 36–48%; fish 50–57% vs 20–28%).

## 2. Objective & scope

Ground-truth audit of the 6 bot personas ahead of the owner's 500-hand review (explicitly OUT of scope, awaiting owner command). No code changed.

## 3. Teams used

Wave A: 2 Claude sonnet extraction agents (preflop closed-form computation; postflop mechanism map). Wave B: 6 Codex gpt-5.6-sol lanes, high reasoning, web search, sealed 20-item briefs. Wave C: 3 Claude sonnet refuters, locked checklist, cross-family. Director (this session): adjudication, one empirical refutation, synthesis.

## 4. Work completed

- 6 dossiers at `research/persona-realism-artifacts/playstyle-research/{nit,tag,lag,maniac,calling_station,passive_fish}.md` (~40–47KB each, 20 sections, sourced).
- Engine extractions: `engine-preflop-extraction.md` (exact combo-weighted stats) + `engine-postflop-extraction.md` (mechanism + levers), both adjudicated.
- 32-row finding ledger from 3 refuter passes; all six dossiers SOUND-WITH-FINDINGS, none fabricated.
- Director empirical check: refuted Wave A2's "check-raise structurally unreachable" claim by driving the engine (check → bet → RAISE is legal).

## 5. Key decisions

- Research anchored to low-stakes live+online, both reported (owner choice).
- Research agents sealed from implementation (owner choice) — dossier #19 parameters are independent ground truth, mapped to engine levers only here.
- Ledger severities adjudicated: cross-dossier station/fish boundary set to SIBLINGS split by fold-to-c-bet/WTSD (fish = fit-or-fold, low WTSD; station = never-fold, high WTSD) — matches the app's roster intent and the fish dossier's framing.

## 6. Evidence — research consensus vs engine (online 9-max column; engine numbers are exact pack computations)

| Stat | nit | TAG | LAG | maniac | station | fish |
|---|---|---|---|---|---|---|
| VPIP research | 8–13 | 12–18 | 25–31 | 48–62 | 43–56 | 40–50 |
| VPIP engine* | **28.4** | **34.0** | **43.1** | **33.7** | 46.5 ✓ | 40.9 ✓ |
| PFR research | 6–11 | 10–16 | 21–27 | 36–50 | 4–10 | 5–10 |
| PFR engine | 27.4 | 34.0 | 43.1 | 33.7 | **0.6** | 3.6 |
| 3-bet research | 2–5 | 5–9 | 9–13 | 14–22 | 0.5–1.8 | 1.5–3 |
| 3-bet engine | 1.49 | 6.67 ✓ | 8.84 ✓ | 12.58 ~ | 0.18 | 0.90 |
| Fold-to-3bet research (after opening) | ~high | 52–65 | 43–53 | sticky (−10pp) | 25–40 | 20–30 |
| Fold-to-3bet engine | **99.1** | **95.1** | **91.6** | **83.6** | **97.9** | **97.4** |
| AF research | 2.0–4.0 | 2.5–3.5 | 3.0–4.8 | 4.0–9.0 | 0.5–1.2 | 0.6–1.0 |
| AF engine (measured/pop) | — | ✓ in band | ~2.1–2.5 low | **~3.2–3.3 low** | ✓ low | ✓ low |
| WTSD research | 18–24 | 24–30 | 25–30 | 27–36 | 36–48 | 20–28 |
| WTSD engine pinned band | 37–80 | 41–65 | 37–59 | 34–50 ~ | **66–72** | **50–57** |

\* engine VPIP/PFR = unopened-node proxy (uniform position average, no cold-calls folded in) — understates true VPIP if anything, so the loose-trio misses are direction-safe. Theory-contract §5 targets (nit 10–14, TAG 15–20, LAG 21–27, maniac 45–58) independently agree with the research — **the engine misses its own committed targets, not just the new research.**

## 7. Review & refutation

3 cross-family refuter passes; 32 ledger findings. Highest-impact: maniac dossier's VPIP/PFR ranges permit impossible PFR>VPIP if sampled independently (derive PFR via the 0.70–0.88 ratio row); LAG per-position RFI table overshoots its own aggregate VPIP; nit's "attempt to steal 18–28%" unreachable from its own RFI table; TAG's own best source (Hand2Note live db, AF 1.6 / 3-bet 13%) excluded by its own live bands; station WWSF jointly infeasible with its stated aggression; fish 4-bet 8–12% claim is backwards vs station's 1–4% (do not adopt); every dossier's sizing tables are self-admitted inventions. All six #19 tables = **structured calibration hypotheses**, never direct wiring.

## 8. Validation results

Engine-side numbers are exact (closed-form over 1326 combos; loader-validated packs). Director refuted one extraction claim by execution (check-raise reachable). Research-side numbers NOT URL-verified (sandbox has no web access) — flagged rows need human spot-checks before any becomes a band.

## 9. Disagreements & resolutions

- Station-vs-fish boundary (nested vs sibling): resolved SIBLING (above).
- Fish `call_looseness` 0.42 < nit 0.6 looked absurd pre-research; research partially rehabilitates it — the fit-or-fold fish folds flop 55–65% (near nit's 60–72), and the elasticity split (fish scared of big bets, station size-blind) matches research exactly. Kept as calibration question, not defect.
- Maniac stability (refuter: real maniacs are transient/tilt-driven): resolved accepted-by-design — the app's personas are deliberately idealized-distinct caricatures (theory contract §1).

## 10. Known limitations

Engine preflop stats are first-in proxies, not arrival-weighted live VPIP. WTSD "engine" values are pinned test bands, not fresh sim runs. Research consensus is heavily blog/vendor-sourced (Poker Copilot + Hand2Note concentration; 2015–2017 live anchors); per-seat and sizing detail is invented-by-the-model and labeled so. No dossier URL was fetched for verification.

## 11. Residual risks

Wiring any #19 band directly (esp. WWSF, sizing, fish 4-bet) reproduces the W4-b-class jointly-infeasible-target failure. Single-author dependency of the theory contract's format evidence still stands.

## 12. Deferred work

500-hand owner review (awaits command). Human URL spot-checks of flagged citations. F18 opener-position defense (already deferred; research confirms it matters — TAG 3-bets value-heavy vs EP, bluffier vs LP). Slowplay/trap mechanic (research: minor for this roster). Strength-correlated sizing for recreational personas — conflicts with the F14 anti-sizing-tell intentional-leave; OWNER product decision, not a bug.

## 13. Recommendation

Fix order by damage-per-effort: (1) preflop pack re-authoring for nit/TAG/LAG open ranges + maniac unopened-fold artifact (pure JSON, no engine change); (2) vs-3bet/vs-4bet continuation ranges per persona (JSON; the flattest axis, station-call vs maniac-stick vs TAG-fold differentiation); (3) WTSD downward re-anchor — already scheduled as the C6/W4-b cluster re-anchor; research independently confirms its direction and rough magnitude; (4) maniac AF/looseness (needs the W2-a lever split it never got). All four slot into the existing R8/R9 persona-realism roadmap rather than a new initiative.

## 14. Go / no-go / needs-decision

GO for using the dossiers as calibration priors (with ledger caveats). NEEDS-DECISION (owner): F14 sizing-tell leave vs recreational realism; whether preflop re-authoring joins Wave A of R9 or waits.

## 15. Links

Dossiers + engine extractions: `docs/ai-dlc/research/persona-realism-artifacts/playstyle-research/` · Ledger: `docs/ai-dlc/ledger/persona-playstyle-research.md` · Plan: `docs/ai-dlc/plans/persona-playstyle-research.md` · Theory contract: `docs/ai-dlc/contracts/persona-realism-theory-contract.md` · Roadmap: `docs/ai-dlc/roadmap/persona-realism.md`
