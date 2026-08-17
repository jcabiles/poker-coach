# Director report — persona-hand-review (full tier; gate fired)

Initiative: persona-hand-review · Closed 2026-07-29 · Plan: `plans/persona-hand-review.md` (approved with owner amendments) · Ledger: `ledger/persona-hand-review.md` (2 passes)

## 1. Executive summary
The owner's 756-hand session was fully graded for bot-persona realism and, separately, for the quality of the owner's own play. Both deliverables shipped: `research/persona-realism-artifacts/playstyle-research/report-bot-realism.md` and `report-hero-play.md` (local/uncommitted per standing owner decision). Headline results: (1) the four positional personas (nit/TAG/maniac/LAG) raise first-in within an 8-point band (23.1–31.0%) — effectively one preflop bot, with the maniac folding premiums unopened; (2) the owner's call-down complaint is confirmed, driven by the station/fish supplying 75% of call-downs with a genuine no-floor tail (queen-high vs 2.33×-pot); (3) the draw-fear complaint is mostly confirmed (76.8% aggressor barrel-through on draw-completing cards); (4) the passive fish's value-light raises are the second-largest hard-failure class; (5) the app grader's issued verdicts are 100% sound but its 470-decision blind zone hides owner mistakes at 4–8× the covered rate.

## 2. Objective & scope
Per REVIEW-HANDOFF.md + owner scope decisions: all complete hands of session 8c04aa55 (pinned at 756; the in-progress 757th excluded); two separate reports; owner's per-concept simple-then-technical format; three named defects specifically investigated.

## 3. Teams used
16 workers, 3 waves (owner-amended roster): 8 Codex Sol (high) grading lanes · 2 Codex Sol themed specialists (draws, call-downs) · 2 Codex Sol hero postflop lanes + 1 Sonnet hero preflop lane · 2 Opus adversarial auditors · 1 blind Opus cross-checker. Director (session, Fable): data pinning, exports, deterministic extractors, aggregate stats, adjudication, report authoring. No Fable subagents.

## 4. Work completed
756 hands exported + chunked; ~10k bot decisions two-layer graded; 229 call-down + 109 draw-card spots deterministically extracted and exhaustively analyzed; per-persona aggregates computed (stats_756.txt); 1,102 hero decisions re-reviewed incl. fresh grading of the 470 the app could not grade; two audits; ledgered adjudication; blind cross-check of the drafts; 34 fixes applied; final reports.

## 5. Key decisions
Owner: Codex Sol as primary graders; Opus cross-checker (cross-family flip); 2 Opus auditors. Director rulings (ledger): maniac unopened-fold red-flag scope = UTG-family only; first-in limps stripped from cross-lane totals; LAG flop-bet red flag not applicable to raises; lane 6 quantitatively excluded (AB-8); §5a tallies replaced by the measured first-in instrument (AB-9/9b).

## 6. Evidence
Every headline number derived 2–3× by independent implementations (Director script, auditor parser, cross-checker parser): first-in table (18/18 cells), stats citations, coverage splits, 1/229 formal count, draw denominators. 24+40+24 hand exhibits re-read against raw state across the three verification layers.

## 7. Review & refutation
Pass 1: two Opus audits (AB-1..27, AH-1..21) — 3 blockers, 16 majors total; all accepted; withdrawals/downgrades applied. Pass 2: blind cross-check of the drafts themselves (CC-1..34) — 2 blockers (provenance overclaim; one inverted counter-evidence exhibit), both fixed. Maker≠checker held at every stage; no finding auto-folded.

## 8. Validation results
Post-fix grep sweeps confirm no stale pre-fix numbers. All quantitative claims in the final reports trace to a reproduced computation or an audit-confirmed hand read.

## 9. Disagreements & resolutions
Lane-6 denominator (resolved: mislabel, excluded); maniac §5a positional scope split across lanes (resolved by Director ruling); draw-lane's fish verdict clause (resolved: demoted, n=10 vs directional band); hero "~10×" density claim (resolved: recomputed 4–8× with denominators).

## 10. Known limitations
Single-session P/L uninformative (±~700bb one-sd/seat); arrival gate exercised on only 1/229 call-down spots (cheap hardening left undone); n≤5 rows in scare-card persona splits; dossier URLs still human-unverified; rubric red-flag lists bound what counts as "formal" failure.

## 11. Residual risks
Exhibit-layer narratives remain the least reliable layer (8/24 carried errors pre-fix); any future quotation of single hands should re-check against hands_756.txt.

## 12. Deferred work
Engine remediation tickets from the five defect classes (owner sequencing via the persona-realism roadmap R8/Wave A); optional /ai-org:quant formalization of aggregate stats; systematic arrival pass over spot lists.

## 13. Recommendation
Feed the five bot defect classes into the persona-realism roadmap as calibration targets — the highest-leverage single fix is persona-differentiated first-in raise rates (data-file change, not engine change). For the owner's own game: raise more first-in (10 confirmed folds of profitable steals), never limp big pairs, and cut river bluffing vs the station/fish.

## 14. Go / no-go / needs-decision
Delivered; no open decision required. Next initiative sequencing is owner's call.

## 15. Links
`playstyle-research/report-bot-realism.md` · `report-hero-play.md` · `lane-reports/` (13 lanes + 2 audits + cross-check) · `stats_756.txt` · `hands_756.txt` · `spots_*.txt` · `ledger/persona-hand-review.md` · `plans/persona-hand-review.md` · log.md 2026-07-28/29 entries.
