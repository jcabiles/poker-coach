# Findings — coach-math roadmap and the 2026-10-03 bot-realism-6max amendment
scheme: 2026-09-26

**Bottom line:** one blind reviewer found 11 issues in the two roadmaps; all 11 were valid and
all are fixed in the roadmap text. No finding is open.

- **Pass 1, 2026-10-03:** Codex Sol (cross-family), blind. Checklist: the roadmap guardrails
  (§D), a plan challenge, and goal coverage against the owner's stated goal and rulings, pasted
  verbatim. Raw report: `docs/ai-dlc/reviews/coach-math-roadmap-r1-sol.md`.
- **Note:** the brief quoted a 300-line cap; the project owner raised the cap to 350 lines
  during the pass. No finding depended on it.
- whole-branch review: skipped — roadmap only, no code.

| ID | Target | Severity | Finding | Evidence | Status | Resolution test |
|----|--------|----------|---------|----------|--------|-----------------|
| R1 | coach-math Lane 2 and NEXT | major | The agreed "price check on every faced bet" had no complete lane. | Review R1; lane 2 sub-slices named draws only | fixed: 2a now covers every graded faced bet (made hands and draws); NEXT lane 3 carries the price on ungraded bets, cut to NEXT by the owner's "cut to fit 2 weeks" ruling | Lane 2 and lane 3 text name both graded and ungraded faced bets |
| R2 | coach-math north star, Lane 0 | major | 25 fixed spots prove only those spots; the 20-spot minimum weakened the owner's 25. | Review R2 | fixed: pass/fail requires 25 spots; spots are spread across streets, bet sizes, SPR bands and textures; every verify phase regrades a seeded sample and explains flips; a "what it does not prove" line was added | North star and lane 0 pass/fail say 25 and name the regrade sample |
| R3 | coach-math Lane 1 research | major | Counting hole cards in the best five does not decide whether a hand beats the board; flop and turn have no five-card board hand. | Review R3; `domain/equity.py:66` returns a rank tuple | fixed: river rule compares the hero's best five with the board's five; flop and turn get separate rules | Lane 1 research states both rules |
| R4 | coach-math NEXT stack depth | major | The SPR one-pair rules were stated as absolute teaching rules. | Review R4; audit finding 6 shows only that grades ignore SPR | fixed: recast as hypotheses needing sources and counterexample spots, with SPR as one input among several | Lane 4 says "hypotheses to test, not rules to teach" |
| R5 | coach-math Lane 2 research | minor | "Count the river card only when all-in" was too broad. | Review R5 | fixed: all-in guarantees both cards at today's price; otherwise later betting is modelled through implied odds and realization | Lane 2 research wording |
| R6 | bot-realism-6max out-of-scope, rake | major | Rake changes later bot decisions through carried-over stacks, so "not bot decisions" was wrong. | Review R6; stack carry-over (#239); `personas_postflop.py:1889` reads stack ÷ pot | fixed: exception reworded in the roadmap and the audit record; the rake item defines the 9-max check (identical to the first raked pot, later divergence traced to stacks) | Out-of-scope block and rake item carry the new wording |
| R7 | bot-realism-6max NEXT rake | minor | The owner's rake default (about 10%, $5 + $1 cap, no flop no drop) was missing. | Review R7; audit owner rulings | fixed: default stated as the build target; other rules are configuration | Rake item names the default |
| R8 | coach-math Lane 1 ideate | minor | The agreed grader-side adapter was one of three equal candidates. | Review R8 | fixed: the adapter is the default; (b) or (c) replaces it only on recorded evidence; template phase 3 states the rule for all lanes | Lane 1 ideate and template phase 3 |
| R9 | coach-math Lane 1 assumption | minor | The label-patch test had no numeric threshold. | Review R9 | fixed: any residual failure adds sub-slice 1d; more than 2 of 8 stops the lane for an owner ruling | Lane 1 cheapest-test text |
| R10 | coach-math NOW appetite | minor | The 2-week cut had no named fallback. | Review R10; lanes total about 8 days | fixed: deferral order stated (2c first, then 1c) | NOW header names the order |
| R11 | bot-realism-6max L1 and L2 | minor | L1 and L2 skipped phases without the written reason the template requires. | Review R11 | fixed: L1 is the research phase and L2 the evaluate phase of the live-table item, which owns ideate, plan and build | Template note above L1 says so |
| F1 | coach-math lane numbering | minor | Fidelity pass: NOW used lanes 0, 1, 2, 6 while the NEXT items had no numbers. | Director fidelity pass | fixed: NEXT items numbered 3–5 in the owner's fix order (price check, stack depth, preflop), then 7–9 | NEXT headings carry lane numbers |
| F2 | coach-math Lanes 0 and 6 | minor | Fidelity pass: plan and ideate phases were missing without a written reason. | Director fidelity pass | fixed: each lane states its plan phase or the reason it is skipped | Lane 0 and 6 text |
| F3 | bot-realism-6max NEXT rake research | minor | Fidelity pass: research was called done though the per-player cost is unsourced. | Audit finding 17 | fixed: research marked "mostly done" with the top-up named | Rake item research line |
| F4 | bot-realism-6max NEXT commitment bug | minor | Fidelity pass: the item lacked the six-phase detail the owner asked for. | Owner instruction, 2026-10-03 | fixed: evidence, research, evaluate, ideate and sub-slices added | Commitment item text |
