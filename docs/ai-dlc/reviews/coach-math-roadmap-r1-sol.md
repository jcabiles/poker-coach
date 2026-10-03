The roadmaps cover most of the owner’s requests and put the baseline test before the coach fixes. I found one agreed deliverable without a complete lane—the price check on every faced bet—and several claims that could make the coach’s math tests or later guidance wrong. The 25-spot target is useful as a fixed regression gate, but it cannot by itself establish that the coach’s poker math is correct.

**R1 · mandate 3 · severity: major**  
**Where:** [coach-math.md](docs/ai-dlc/roadmap/coach-math.md:150), Lane 2 and NEXT.  
**Finding:** The agreed “price check on every faced bet” has no complete lane. Lane 2 compares draws with a call price; NEXT proposes showing a price where the coach cannot grade, but neither commits to checking made-hand calls and every other faced bet.  
**Evidence:** Lane 2’s build steps specify draws in step 2b. The [audit](docs/ai-dlc/reviews/coach-math-audit-2026-10-03.md:44) reports that only 3.5% of postflop decisions receive a grade.  
**Suggested fix:** Add a lane or explicit sub-slice that defines and tests the price check across faced-bet situations, including the rule for decisions the coach cannot grade.

**R2 · mandate 2 · severity: major**  
**Where:** [coach-math.md](docs/ai-dlc/roadmap/coach-math.md:16), north star and Lane 0.  
**Finding:** Zero failures in about 25 fixed spots establishes correctness on those spots, not correctness of the coach’s poker math across bet sizes, streets, stack depths, and board textures. The permitted minimum of 20 spots also weakens the owner’s “about 25” target.  
**Evidence:** Lane 0 fixes the cases in one test file, while the audit shows very low postflop grading coverage and several distinct failure types.  
**Suggested fix:** Keep the owner’s 25-spot target, require roughly 25 cases with zero remaining expected failures, and add a held-out or stratified check of graded decisions.

**R3 · mandate 2 · severity: major**  
**Where:** [coach-math.md](docs/ai-dlc/roadmap/coach-math.md:99), Lane 1 research and evaluation.  
**Finding:** The number of hole cards used in a five-card hand does not decide whether that hand beats the board. A hole card can replace a board card and make the same-ranked hand; on the flop and turn, there is no five-card board hand to compare.  
**Evidence:** On a mixed-suit 5-6-7-8-9 board, a hero’s other 9 can appear in an equally ranked straight that still ties the board. The cited [evaluator](backend/app/domain/equity.py:66) returns a rank tuple for seven cards, not a count of hole cards in a chosen five.  
**Suggested fix:** Compare ranked hands directly on the river and define separate flop and turn reference classifications.

**R4 · mandate 2 · severity: major**  
**Where:** [coach-math.md](docs/ai-dlc/roadmap/coach-math.md:243), NEXT stack-depth candidate rules.  
**Finding:** “One pair raises” at a stack-to-pot ratio (SPR) of 3 or below, calls from 3 to 6, and may always fold above 6 is too absolute to teach as a strategy rule. The correct action also depends on the bet, ranges, board, position, and whether a raise is legal.  
**Evidence:** The roadmap states these as candidate action rules without those conditions; the [audit](docs/ai-dlc/reviews/coach-math-audit-2026-10-03.md:33) establishes only that current grades fail to vary with SPR.  
**Suggested fix:** Treat SPR as one input to sourced, situation-specific rules and test counterexamples before promoting these candidates.

**R5 · mandate 2 · severity: minor**  
**Where:** [coach-math.md](docs/ai-dlc/roadmap/coach-math.md:161), Lane 2 research.  
**Finding:** The statement that a flop caller may count the river card *only* when all-in is too broad. Two-card equity cannot be used as a guaranteed immediate-call payoff when another bet may come, but a model of future betting and equity realization can account for river outcomes.  
**Evidence:** The same lane calls for implied odds and an equity-realization factor, both of which concern outcomes after the immediate call.  
**Suggested fix:** Say that an all-in guarantees both cards at the current price; otherwise model later betting and realization explicitly.

**R6 · mandate 2 · severity: major**  
**Where:** [bot-realism-6max.md](docs/ai-dlc/roadmap/bot-realism-6max.md:268), out-of-scope exceptions.  
**Finding:** Rake is described as changing settlement “but not bot decisions.” Because stacks carry over, taking rake changes later stack sizes and can change later bot decisions, so the stated nine-seat byte-identity exception is narrower than the actual effect.  
**Evidence:** The roadmap records stack carry-over at line 80; the [bot commitment code](backend/app/domain/personas_postflop.py:1889) uses stack divided by pot.  
**Suggested fix:** Define the rake exception to include attributable downstream decisions and test the first divergence and its cause.

**R7 · mandate 3 · severity: minor**  
**Where:** [bot-realism-6max.md](docs/ai-dlc/roadmap/bot-realism-6max.md:209), NEXT rake lane.  
**Finding:** The lane carries rake but does not state the owner’s requested live default: about 10%, capped at $5 plus $1, with no flop, no drop. Its listed alternatives include a flat drop, so the build target is unclear.  
**Evidence:** The precise ruling appears in the [audit](docs/ai-dlc/reviews/coach-math-audit-2026-10-03.md:95), while NEXT lists configurable options.  
**Suggested fix:** Put the approved default and its settlement checks in the rake lane; retain configuration as an implementation choice.

**R8 · mandate 3 · severity: minor**  
**Where:** [coach-math.md](docs/ai-dlc/roadmap/coach-math.md:122), Lane 1 ideation.  
**Finding:** The agreed grader-side adapter is one of three candidate designs, with no condition for choosing another. That leaves the prescribed deliverable contingent on a later design decision.  
**Evidence:** The roadmap lists the adapter, a new classifier, and a relative-strength reader as alternatives.  
**Suggested fix:** State the adapter as the intended design and require recorded test evidence to change it.

**R9 · mandate 1 · severity: minor**  
**Where:** [coach-math.md](docs/ai-dlc/roadmap/coach-math.md:143), Lane 1 assumption gate.  
**Finding:** The assumption test has no falsifying threshold: “if many” spots still fail does not say whether one, two, or more remaining wrong answers block the classifier build.  
**Evidence:** Lane 0 specifies a numerical one-third threshold, but Lane 1 leaves this gate qualitative.  
**Suggested fix:** Set the maximum acceptable residual failures before running the label-patching test.

**R10 · mandate 2 · severity: minor**  
**Where:** [coach-math.md](docs/ai-dlc/roadmap/coach-math.md:28), six-phase template and NOW appetites.  
**Finding:** The roughly two-week cut is tight without a stated fallback: four NOW lanes allow about eight workdays, yet require first-principles research, baseline evaluation, three designs and an owner choice per lane, specifications, nine build sub-slices, and verification. The owner choice is also a sequencing dependency.  
**Evidence:** The lane appetites are about 1, 3, 3, and 1 days; the listed build sub-slices total nine.  
**Suggested fix:** Name the first slice to defer if the research or owner decisions consume the remaining time.

**R11 · mandate 1 · severity: minor**  
**Where:** [bot-realism-6max.md](docs/ai-dlc/roadmap/bot-realism-6max.md:137), L1 and L2.  
**Finding:** The amendment says every new lane follows all six phases, but L1 is specified as research and L2 as evaluation, without written reasons for skipping the other phases. That conflicts with the owner’s recorded instruction for every lane.  
**Evidence:** The shared [template](docs/ai-dlc/roadmap/coach-math.md:28) permits a skipped phase only with a written reason.  
**Suggested fix:** Record which phases do not apply to these measurement lanes and why, or add the missing phase work.

### Goal coverage

“Covered” identifies a lane or recorded ruling; it does not override the findings above.

| Deliverable | Lane or ruling | Covered? |
|---|---|---|
| Realistic human play | Bot roadmap north star; live-table NEXT | Yes |
| Find defects that make the app wrong or weak for low-stakes training | Audit; both roadmaps’ NOW and NEXT | Yes |
| Focus on NLHE math and strategy | Coach roadmap NOW and NEXT | Yes |
| Hero classifier via grader-side adapter | Coach Lane 1, as a candidate; R8 | **No—design uncommitted** |
| Real pot odds, counted outs, stack-capped implied odds | Coach Lane 2 | Yes |
| Price check on every faced bet | Coach Lane 2 only partly; R1 | **No** |
| Stack-aware grading | Coach NEXT, “Stack depth is ignored” | Yes |
| Tighter preflop grading | Coach NEXT, “Preflop grading is too soft” | Yes |
| Engine minimum re-raise fix | Coach Lane 6 | Yes |
| Relabel “−X bb” as points | Coach Lane 6 | Yes |
| Live $1/$2 bot target | Bot L1, L2 and live-table NEXT | Yes |
| Rake at both table sizes, deferred beyond the two-week cut | Bot NEXT; audit ruling; R6–R7 | Yes |
| Bot effective-stack commitment fix, six-seat first | Bot NEXT | Yes |
| Leave sizing tells, hero adaptation, and confidence-interval bb/100 alone | Both out-of-scope blocks; audit ruling | Yes |
| Owner’s 200-hand retuned-LAG verdict before further tuning | Bot M2 and NEXT dependency | Yes |
| About 25 textbook spots, baseline, zero failing | Coach north star and Lane 0; R2 | Yes |
| About two-week appetite and a cut to fit | Coach NOW; R10 | Yes |
| Two active roadmaps; ask owner which to work on | [profile.md](docs/ai-dlc/profile.md:10); both bookkeeping blocks | Yes |
| Research, evaluation, ideation, planning, and implementation sub-slices for each lane | Shared six-phase template; bot L1/L2 exception gap in R11 | **Partly** |
| Deep first-principles work for every math and strategy concept | Coach lane research; bot L1 research; R3–R5 identify corrections needed | Yes |
| Nine-seat identity except named exceptions; domain and provider boundaries; frequency plus EV results; versioned strategy data; frozen `spot_signature()`; approximate EV labels; no solver tables, hand-history imports, or auth/hosting | Profile invariants and roadmap no-gos; rake exception gap in R6 | Yes |
