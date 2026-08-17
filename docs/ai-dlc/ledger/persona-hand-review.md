# Findings — persona-hand-review

Pass 1 — 2026-07-29 · TWO Opus adversarial auditors (cross-family vs 12 Codex-authored + 1 Sonnet-authored lane reports) · locked checklists: fact verification vs raw hands · precedence-ladder violations · rubric misattribution · unsupported leaps · cross-lane consistency · math recomputation. Full finding text: `playstyle-research/lane-reports/audit-bot.md` (AB-1..27) and `audit-hero-themes.md` (AH-1..21).

## Director adjudication (all findings reviewed with pushback; none auto-folded)

**Audit A (bot lanes): 3 blockers, 8 majors, 15 minors, 3 info — ALL ACCEPTED.** Spot-verified on pushback: AB-1 (h336 fish holds aces-up = value, not value-light — §5a withdrawn), AB-3 (h403 TAG defended own open, item is cold-call-only; and UTG1 is IP vs SB — §5a withdrawn), AB-8 (lane 6 denominator ~3× wrong — lane 6 quantitative claims excluded; its per-hand narratives individually re-verified by auditor stand).

**Audit B (hero+themed): 0 blockers, 8 majors, 13 minors — ALL ACCEPTED.** All are prose/exhibit errors; every computed table reproduced cell-for-cell against the auditor's independent parser. Verdict-level effects: theme-draws' headline exhibit H473 re-based (AA = strong-value row, defect is SIZE not the marginal-pair cell); H306 withdrawn as TAG failure (live flush draw omitted); fish barrel-rate clause demoted (n=10 vs DIRECTIONAL band, protocol §10); hero-preflop H527 re-priced (31.6% not 21% — downgraded from clean mistake to borderline).

## Director rulings on the three cross-lane inconsistencies (AB-20/21, audit A systemic §5)

1. **Maniac §5a item 1 positional scope = UTG-family only** (lane 8/lane 4's strict reading). HJ/LJ/BTN folds of playable hands are POLICY notes. Moot for the headline: the Director-level claim uses the sample-level instrument (below), not the §5a count.
2. **First-in limps** (lane 7's 39 logged deviations): stripped from cross-lane totals; limping frequency is an aggregate matter and in-character for station/fish. No cross-lane policy-deviation totals are reported anywhere — narratives and classes only.
3. **LAG §5a item 4 applies to flop BETS only** (its own wording); the three raise/check-raise applications (h697, h726, h216) downgraded to POLICY. The hands remain exhibits on baseline grounds.

## Headline evidence adopted (Director-verified independently where marked ✓)

- **One-preflop-bot finding (replaces the "66 maniac §5a" tally):** first-in raise rates over all 756 hands — nit 23.1% · TAG 24.2% · maniac 27.2% · LAG 31.0% ✓ (Director recomputation reproduced the auditor's numbers exactly; opps 268/517/320/284). Maniac open-limps 0%. Minimal-repro exemplars all audit-CONFIRMED: h318 (AK folded unopened UTG2), h713 (JJ folded LJ), h714 (77), h302 (KTo), h743 (A4o).
- **Call-down class survives audit "essentially intact":** h81, h68, h45, h473, h357, h516, h522, h579, h588, h425, h726, h697 all recomputed exact. Formal rubric red-flag count 1/229 (h336 TAG) independently re-swept and confirmed; the class is persona-policy/degree, concentrated in station (30/104 air/ace-high/busted-draw tail) — consistent with station flop fold-vs-bet 13.1% ✓ (stats_756.txt).
- **Draw-fear: PARTIALLY CONFIRMED.** 76.8% (53/69) aggressor barrel-through on draw-completing cards; caller-response table 123/167 continue; 16/69 genuine slowdowns exist (H88, H586, H628, 4 maniac check-folds) so "never" is refuted. Two showcase exhibits weakened (h338 nut FD missed; h507 texture miscounts) — class real but slightly weaker than lanes reported.
- **Fish aggression inversion:** ~30 fish §5a-4 citations (value-light raises/check-raises) minus AB-4's withdrawal (h510 set) — largest surviving hard-failure class. Clean exemplars: h127, h639, h259, h286, h492, h497, h514.
- **Hero grader-coverage finding:** 174/775 preflop + 125/154 flop + 171/173 turn-river decisions share the identical unmappable signature (verified 100%, not sampled); fresh passes found 7 preflop (→ ~5-6 after AH-10 downgrade) + 14 flop + 24 turn/river mistakes/blunders in territory the app scored zero. App's own 632 verdicts: zero overturns (independently re-swept).

| Ruling summary | Status |
|---|---|
| AB-1, AB-3, AB-4, AB-5 (withdraw specific §5a) | fixed-in-adjudication |
| AB-6, AB-7, AB-19, AB-22, AB-27 (downgrade to POLICY) | fixed-in-adjudication |
| AB-8 (lane 6 quantitative exclusion) | accepted — standing rule for reports |
| AB-9/9b (RFI instrument replaces §5a count) | accepted — Director verified ✓ |
| AB-20/21 + LAG-scope (cross-lane harmonisation) | ruled above |
| AB-10..18, AB-23..24 (fact corrections) | accepted — folded into report prose |
| AH-1..21 | accepted — folded into report prose; no verdict flips except H473 re-base, H306 withdrawal, fish-clause demotion, H527 downgrade |

Unresolved: none blocking report writing. Residue: dossier URLs still unverifiable (sandbox); hero W$SD not computable (no payouts in state_json).

---

Pass 2 — 2026-07-29 · ONE blind Opus cross-checker over the two DRAFT reports (fresh context, locked checklist: faithful transmission · audit-correction compliance · hand-fact spot-checks · unsupported leaps · precedence · internal consistency). Full text: `playstyle-research/lane-reports/crosscheck-reports.md` (CC-1..CC-34: 2 blockers, 10 major, 22 minor). Verdicts: both drafts SHIP-WITH-FIXES.

Director adjudication: **ALL 34 ACCEPTED** (each verified against raw data where checkable; the cross-checker's own 24-hand re-read confirmed 16 exact / 8 with errors, 1 meaning-inverting). Notable: CC-2 (hand 708 counter-evidence belonged to the maniac; the station in it is a defect instance — fixed and disclosed in report §3), CC-1 (blanket audit-provenance guarantee replaced with the audits' actual reliability contract in both preambles), CC-7 (hero "~10×" recomputed to 4–8× with explicit denominators), CC-9 (both clone P/L gaps + ±700bb one-sd band now stated; §8 demoted to "consistent-with"), CC-12 (call-down lane's per-persona verdicts incl. maniac-REFUTED added), CC-5 (expectation bands re-labeled directional; flatness claim re-anchored to the measured spread). All 34 fixes applied to `report-bot-realism.md` and `report-hero-play.md` 2026-07-29; post-fix grep sweep confirms no stale pre-fix numbers remain. Cross-check also independently reproduced (third derivation) the first-in table — all 18 cells — and every stats_756.txt citation.

Status: both reports FINAL. Review-loop stop condition reached (audit → fix → clean verification; a further pass requires a new question/method/counterexample).

---

Pass 3 — 2026-07-29 · THREE reviewers on the R10 ROADMAP correction pass (`roadmap/persona-realism.md`), owner-opted dual challenge · Codex Sol guardrail (locked checklist; verdict DO-NOT-SHIP pre-fix: 2 blockers, 3 majors, 2 minors) · Codex Sol plan-challenge (11 findings: 3 blockers, 8 majors) · Claude refuter (1 high, 2 med, 1 low; SHIP-WITH-FIXES). Full texts: `playstyle-research/lane-logs/r10-{guardrail,challenge}.log` + refuter result in-session.

Director adjudication (every load-bearing claim independently re-verified before acceptance):
- **CONFIRMED by Director verification and ACCEPTED:** both R10-3BET gates passed at HEAD (nit.json authors AA/KK continues; the 20 DB fold-holdings incl. QQ/AK/TT supplied the true failing gate) · R10-PRESEP four-way ordering gate unsatisfiable in scope (nit's 29.1% wildcard is W5-b3's cell) · station `size_elasticity` = 0.55 at HEAD, not 0.0 (W3R-2; my citation was stale — tail attribution rewritten) · maniac premium fold weights 0.70–0.85 varying by seat · "below TAG from LJ on" annotation false (below LAG everywhere; below TAG at UTG/BTN/SB only) · softmax misattributed to the categorical preflop sampler · W-ARR-a counts occupancy not actions (new lane slice R10-COUNT) · PRESEP causal bundling (split into R10-PRE1/PRE2 + un-absorbed W5-b4) · "after T-ANCHOR" insufficient lane boundary (revised to after T-STICKY, per the #118/#119 precedent) · stratification confound on the aggregate z-test (Director computed EP/MP/LATE strata — finding SHARPENS at EP, maniac tightest of four) · stale-claim supersessions (W3R-2 tail reopened; N-maniac corpus-labeled; R9-N2 qualified to slope; arrival-and-policy-separable framing).
- **PARTIALLY REJECTED (recorded):** challenge #10 — the hard `maniac > lag` per-seat ordering gate is RETAINED, justified from the roster's definitional archetype ordering (contract §1; same basis as the pinned `bluff_freq` ordering test), NOT from the soft dossier bands; absolute levels stay REPORTED. Challenge #7 accept-MODIFIED: one `R10-TAIL` design item with severable sub-questions, not two items. Challenge #1 partially accepted: R9-4's owner-locked spine order stands; its parallelism argument folded into the revised R10-8.
- All fixes applied to the roadmap 2026-07-29; stale-reference sweep clean.
