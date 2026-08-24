# Bot-Realism Flywheel Roadmap — updated 2026-08-23 (rev 6)
status: approved (owner, 2026-08-05 — PR #169 merged). Rev-4 wording is pending owner review;
the rulings it records were made 2026-08-09 through 2026-08-13. *(It was described here as
uncommitted until 2026-08-17; it has in fact been committed since PR #180. Corrected in
passing.)* Two edits on 2026-08-17: the improvement-phase block was added to the NOW lane,
and the same day's audit and owner ruling were recorded against it. One edit on 2026-08-19:
slice 2's ticket-merge status recorded (T1 #198, T2 #199, T3 #200 all merged) — the slice
itself stays OPEN, since the owner's blind play session, not a ticket count, is what closes it
(superseded by the next sentence: the play session has since happened and slice 2 is CLOSED).
**Four owner rulings recorded 2026-08-21 (rev 5):** slice 2 (invest-then-fold, the second
improvement slice — bots giving up on a hand for no visible reason) is now **CLOSED** on the
owner's blind play-session acceptance; the scope-valve contradiction between the improvement-
phase block header and slice 3's entry is **RULED** — slice 3 (calldown, the third improvement
slice — how often a bot keeps calling instead of folding) is core scope, not the cut-first
valve; the Stage-1 stack-commitment brake (`W4-a`, a persona-realism-roadmap slice that lets a
bot fold a made hand when the call size is huge relative to its remaining stack) is **DEFERRED**
past the phase-3 finale as a named post-finale slice, with a reopening trigger; and the
Stage-0 interim went-to-showdown band regime (grounded floors, a one-way downward ceiling
ratchet, and the maniac's went-to-showdown assertion restored at a ratcheted ceiling — it has
been skipped since 2026-08-01) is **RATIFIED**, landing
in a parallel PR to the theory contract. See the NOW banner, the improvement-phase block
header, and the slice 2 and slice 3 entries below for where each lands.
**Rev 6 (2026-08-23): slice 3's five-ticket chain is BUILT AND MERGED** (S3-T1/T1b #211/#212,
S3-T2 #215, S3-T3 #216 — lever withdrawn, instrument shipped, S3-T4 #217, S3-T5 #218 — a fifth
ticket admitted by owner ruling 2026-08-22, LAG-only ship) **and the close packet is committed**
(`../research/slice3-calldown/close-packet.md`: chain-wide measurements, six filed owner
decisions, finale-readiness packet, play-session checklist). The slice stays OPEN until the
owner's blind play session — that session, not the gate numbers, closes it (standing 2026-08-17
ruling). The S6 execution checklist's §5 pre-screen was aligned to ratified §g.5 clause C (all
four judge slots), and `flywheel-s6-control-redesign.md` was closed as superseded by PR #184 +
§g.5 A.

## Bottom line

We are finding out whether the poker bots can be made to play like humans at all, before
spending weeks trying to make them. The big search finished its first stage and was then
**stopped early on purpose**: 730 settings tried, none good enough, and the most powerful dial
already pushed to the edge of what it is allowed. There is no verdict — the owner stopped the
study before the stages that would produce one, judging the diagnosis already sufficient to
decide what comes next. What it bought is that diagnosis, written up in poker-analytics at
`docs/methods/reachability-verdict-s5.md`. Read that, not this paragraph, for what was found.

> **Read first — governing initiative for all bot-realism work.** Supersedes the NOW-lane of
> `persona-realism.md` (paused 2026-08-05; its history and contracts remain authoritative for
> what shipped). PRD: `../prd/bot-realism-flywheel.md`. Evidence base:
> `../research/persona-realism-artifacts/remeasure-2026-08-05/SYNTHESIS.md`. Cross-repo:
> poker-coach produces data, **poker-analytics** produces judgment. Standing rulings on
> durability, the end-of-initiative cleanup obligation, the resume rule, contract-map
> pointers, and the full rev-3/rev-4 amendment log all live in
> `bot-realism-flywheel-archive.md` — they have not changed, they were moved there to keep this
> file readable.

## North-star outcome

- **Outcome: blind bot-detection rate** (judges label anonymized seats human vs bot) —
  *long-run* north star. Under the preregistered protocol (S2a) with balanced priors, perfect
  realism ⇒ detection at chance; the protocol defines the exact statistic (balanced
  accuracy / AUC, cluster-aware CIs), judgment unit, and exposure length.
- **v0 measures a single-player detection PILOT** (S6 — owner's HERO hands as the human class;
  conditional on this player/session, biases disclosed). The TRUE multi-player baseline and
  the owner-set target are a NEXT item — the pilot proves the protocol and gives a first
  conditional number, no more.
- Secondary diagnostic: roster realism rating, baseline 4.8/10; realism score (S3) is the
  free inner-loop metric — **an exploratory surrogate until its validation plan passes**.
- **Goodhart guard:** detection may only be optimized inside a constraint set — poker-legality
  / red-flag-line limits, an archetype-separation floor (blind-ID must stay high), coaching
  usefulness, and runtime/reproducibility budgets. A bot that gets "harder to detect" by going
  bland fails the initiative.
- **Two different things, never to be conflated (clarified 2026-08-09, qualified 2026-08-13).**
  *Recognisable as a type* — a judge can tell that seat is playing like a maniac — is DESIRABLE;
  real players are readable, and a table of unreadable mush would be worse training and worse
  poker. *Recognisable as a machine* — folding 48 times out of 49 in the same spot, folding
  identically regardless of seat, investing then folding for no reason — is the defect. Every
  finding in remeasure SYNTHESIS §B/§C is the second kind, and none of them is about
  readability.
- **The separation floor is a BAND, and it is not yet measurable (added 2026-08-13).** Two
  honest limits on the bullet above. First, the guard says only that blind identification must
  stay "high", with no threshold and no human comparator — a one-sided floor cannot be passed or
  failed, and taken literally it makes *more* identifiable monotonically better, which is the
  mirror image of the Goodhart failure the guard exists to prevent. A seat identifiable with
  certainty from a short sample is itself a machine tell; real players are readable *and* drift.
  Second, the "56 of 56" result does not carry the weight first placed on it: per
  `remeasure-2026-08-05/PROTOCOL.md:41-44` that was a **closed-set** task — judges were told the
  roster composition and matched eight seats to six known labels — not human-versus-bot
  detection, with no preregistered threshold. Before this floor can gate anything it needs a
  declared band measured under the S2a exposure regime against a human comparator. Until then
  treat it as an interpretive principle, not a pass/fail criterion.

## NOW (in order — appetite CAP: ~2–3 wk part-time to the phase-3 gate; scope valves below)

> **STATE, 2026-08-15: the phase-3 gate is DECIDED — ruling A (fix the current bots).**
> Owner ruling recorded in `docs/ai-dlc/specs/phase3-decision-matrix.md` §5, with the
> supporting judge-bias probe evidence attached; protocol changes consolidated and
> ratified as estimand-contract §g.5 (2026-08-15-A). The active work is now the
> improvement phase that ruling defines: de-robotization first, then invest-then-fold
> lines, ~~calldown as the scope valve~~ *(superseded 2026-08-21, calldown ruled core scope —
> see the improvement-phase block below)*; engine/stack work excluded; 2–3 weeks appetite;
> one finale detection run at the end under the new rule-breaker control, plus the
> preregistered owner blind play-test as product acceptance.
> **Slice-by-slice state for that phase is the improvement-phase block at the END of this
> lane (added 2026-08-17, updated 2026-08-19, updated 2026-08-21): slice 1 de-robotization
> is CLOSED, slice 2 (invest-then-fold) is **CLOSED 2026-08-21** — all three tickets merged
> (T1 #198, T2 #199, T3 #200) and the owner's blind play session, the primary acceptance
> evidence under the 2026-08-17 ruling, returned an acceptance verdict: the bots felt
> plausibly human at the table, nothing stood out as robotic — slice 3 (calldown) is core
> scope, ruled 2026-08-21, and spec'd and approved the same day (`docs/ai-dlc/specs/
> flywheel-slice3-calldown.md`). Resume with its ticket chain, not from this banner.**
> **Rev 6 update (2026-08-23): that ticket chain is now fully merged (#211–#218) and the close
> packet is committed — resume from `../research/slice3-calldown/close-packet.md`; the only
> open acceptance step is the owner's blind play session, and the owner decisions filed there.**
> *(Superseded banner, 2026-08-13, kept for provenance: every slice closed, S6 moved to
> NEXT, gate pending, do-not-start-NEXT.)* The evidence it
> rests on is the S5 close-out below; note that one of its two planned inputs, the detection
> pilot, is deliberately absent. *(Update 2026-08-14: the pilot was subsequently attempted —
> owner-initiated — and terminated at its control pre-screen as a protocol shakedown; see the
> S6 entry in NEXT. The gate still has no detection number, but it now has a finding about
> the instrument itself.)*

- [x] **S1–S4 complete** — cross-repo working agreement + walking skeleton (2026-08-05) ·
      methods & estimand contract v2.3 (2026-08-05) · research wave, corpus verdict PARTIAL
      (2026-08-06) · realism score v0, **validation retrospective-FAILED and the stop-gate
      fired** (2026-08-07) · batch sweep runner + counterfactual-config layer (2026-08-07).
      Full slice text, pass/fail wording, and the rulings each one produced:
      `bot-realism-flywheel-archive.md`. The two consequences that still bind everything
      downstream: the realism score is an **exploratory surrogate** and may never carry a
      verdict on its own, and configs may sweep only the S2a-declared space.
- [x] **S5 — Reachability study — CLOSED 2026-08-11, stopped early by owner ruling** —
      problem: unknown whether ANY declared-space config reaches human-band behaviour (the
      owner's gate question) · outcome-link: decides phase 3 · riskiest assumption:
      **tested-FAILED** — that the declared space contains a human-band config. Stage 1
      falsified it for the single-persona case; the multi-persona combination case was never
      run and remains untested (close-out §9.3).
      **PASS/FAIL AMENDED 2026-08-13, after results, deliberately and visibly.** The original
      condition required a verdict ∈ {REACHABLE, NOT-REACHABLE, INCONCLUSIVE}. That became
      unsatisfiable: `reachability_verdict()` refuses to run without stage-3 finalists, which
      were never produced, so the study has no verdict *at all* — not even INCONCLUSIVE.
      Ticking the original wording would have been false. Amended condition, met: **a
      close-out doc that fills every §a.4 slot from a real artifact or marks it
      never-evaluated, states plainly that no verdict exists and why, and delivers the
      mechanism diagnosis in its place — dual-adversarially reviewed.** Amending a success
      condition after seeing results is exactly what preregistration exists to prevent, so it
      is recorded here in the open with its reason rather than quietly reworded; a reader is
      entitled to discount the tick accordingly. · appetite: spent 800 of a 1,500-run budget
      · no-gos held: no fix recommendations smuggled in, no score-only verdict.
      **OUTCOME.** Zero of 730 configs were both close enough to human play and still
      recognisably their own persona. The dominant dial (`postflop.call_looseness`) is
      exhausted at its declared floor in every persona's best result. A mechanism probe then
      swept the one dial frozen out of that search, `postflop.continue_ref`, across its full
      declared range: it cannot rescue the result either, for an arithmetic reason. The
      distance measure is near-linear in the pooled share of flops reaching showdown
      (R² 0.993); the cutoff needs ~40 percentage points; any one persona is a single seat of
      nine, so zeroing `maniac`'s showdown rate entirely still leaves the pool at 44.92 —
      a distance of ~6.69 against a 5.1586 cutoff. **No single-persona config can reach the
      cutoff at any dial value.** That bounds single-persona probes only; a stage-3
      combination faces no seat-share ceiling, which is why §a.4 routes REACHABLE through
      stage 3. Owner declined widening the dial's declared range on 2026-08-13.
      **Close-out (every §a.4 slot filled or marked never-evaluated), and the disclosures
      that must travel with any quotation of this result:**
      `poker-analytics:docs/methods/reachability-verdict-s5.md`. Findings and three review
      rounds: `docs/ai-dlc/ledger/flywheel-s5-tprobe.md`, `docs/ai-dlc/ledger/flywheel-s5.md`.
      Execution history (build, pins, runner defects, the overnight-run amendment) is in
      `bot-realism-flywheel-archive.md`.
      **LIMITATION — carried into the close-out 2026-08-13, T7 now CLOSED (added
      2026-08-09, corrected and applied 2026-08-13).** Every wave swept the ratified nine-seat
      lineup, in which same-type seats are identical: three copies of one tag and two of one
      passive_fish (`poker-analytics:docs/methods/s5-study-pins.md:16` — not the exporter
      default, which duplicates different personas; confirmed independently in every run's
      covariance key). The study therefore says nothing about whether a table of *varied* bots
      of the same type reads as more human than a table of clones. **The cause is
      configuration, not the engine** — verified in source: the domain engine already accepts
      a per-seat strategy pack (`play.py:291,313`; no persona-name reads in
      `personas_postflop.py`), and the cloning is done by the callers, the persona-keyed
      override schema and the persistence column. Do not cite it as an architectural gap —
      see the phase-3 gate item in NEXT. This text now appears in
      `poker-analytics:docs/methods/reachability-verdict-s5.md` §8, so the T7 instruction in
      `docs/ai-dlc/tickets/flywheel-s5.md` is satisfied.
> ⚠️ **THE NORTH STAR IS CURRENTLY UNMEASURED, AND NOTHING IS SCHEDULED TO MEASURE IT.**
> How often a reader can tell a bot from a human has never been measured, not once, at any
> point in this initiative. S6 was the only planned measurement and it is deferred (below), so
> every number in the NOW lane above comes from the realism score — a surrogate that failed
> its own validation in S3 and may never carry a verdict alone. Read every finding here with
> that in mind, and do not let "the score improved" stand in for "fewer bots were spotted".

S6, the only planned measurement of it, is built but deferred — it now sits in NEXT.

### Improvement phase (ruling A) — three slices in order; two closed, the third built and awaiting the owner's play session

> **Why this block exists (added 2026-08-17).** Ruling A defines three improvement slices and
> the NOW lane had entries for none of them: the order lived in
> `../specs/phase3-decision-matrix.md` §4 and in the STATE banner at the top of this lane, but
> not as slices a fresh session could resume from — which is what the boot checklist in
> `.claude/CLAUDE.md` tells that session to do. The order is **(1) de-robotization →
> (2) invest-then-fold → (3) calldown**. ~~calldown being the declared scope valve, cut first
> if the appetite runs out.~~ **Superseded 2026-08-21 — see the scope-valve ruling below;
> calldown is core scope, not a valve.** Engine/stack work is cut from this phase entirely.
> Appetite: 2–3 weeks part-time, running since the ruling on 2026-08-15. Exactly ONE finale
> detection run at the end; a second requires a recorded amendment written before it fires. The
> ⚠️ warning above applies to everything here — **none of the numbers below is a detection
> number.** They come from the two statistical gates and from purpose-built tell statistics,
> which measure whether a specific mechanical signature is gone, not whether anyone was fooled.
>
> **OWNER RULING 2026-08-21 — the scope-valve contradiction is resolved: calldown (slice 3) is
> core scope, not the scope valve.** This block's own header, written 2026-08-17, called
> calldown "the declared scope valve, cut first if the appetite runs out"; slice 3's entry
> below had said since the same day that it was "no longer the first thing to cut" — a
> contradiction the entry flagged and left for the owner. Deciding fact: slice 3 is the only
> one of the three improvement slices that lowers the pool's went-to-showdown statistic (the
> share of hands reaching a showdown, the roster's worst-measured statistic against the theory
> contract's grounded targets), and slice 2's T3 ticket (the river-call-zero fix inside
> invest-then-fold) raised that same statistic by roughly one point. Cutting slice 3 for
> appetite would therefore ship the improvement phase with a net increase in the roster's worst
> statistic. If the appetite runs out, something else gets cut instead — not slice 3.

- [x] **Slice 1 — De-robotization of deterministic tells — CLOSED 2026-08-17** — problem: the
      roster's tells were mechanical rather than stylistic — every persona opened one fixed
      size from every seat, postflop bet size named the bettor's archetype class, and range
      edges were hard cutoffs (adjudicated defect list, remeasure SYNTHESIS §B/§C) · outcome-link:
      the north star **by assumption, not by measurement** — no detection number exists for this
      roster either before or after, so the link is the ruling's premise rather than a result ·
      riskiest assumption: **tested-HELD** — that removing size and range determinism would not
      collapse the archetype-separation floor. It did not; at seed 601, the one seed where the
      unchanged roster was also measured, the shipped roster separates slightly better
      · appetite: 8 tickets over 7 PRs (#182, #183,
      #184, #186, #187, #188, #189), 2026-08-15 to 2026-08-17 · no-gos held: no paid detection
      judging (the finale is owner-only and single-shot), no band re-anchoring to make a gate
      pass, no engine/stack work.
      **OUTCOME — what is verified.** Five-seed gate PASS at the shipped tip, seeds 601–605:
      minimum pairwise separation 1.745–1.995 against a required 1.254429, archetype labels 6/6
      at every seed, determinism guard clear everywhere (worst persona share 0.141 against a
      0.20 ceiling). At seed 601, where the unchanged roster measured 1.792042, the shipped
      roster measures 1.847.
      **What actually changed, measured in live play rather than asserted from the pack JSON.**
      Preflop: before this slice every persona opened **one** size from **every** seat at a
      modal share of 1.000; shipped shares are 0.405–0.839 across three or four sizes. Worst-case
      identifiability from a single observed open size is now 0.986, against **three** cells that
      were certainties at 1.000 before (3.5bb ⇒ station, 4.0bb ⇒ fish, 4.5bb ⇒ maniac). Postflop:
      the class read — "small means recreational, large means regular, overbet means maniac" —
      falls from 0.557 to 0.441 against a chance floor of 0.333, and P(maniac | a 1.5× pot bet)
      from 0.885 to 0.768.
      **THE HONEST LIMIT — spec §7.1's coverage clause is NOT met, and is not claimed to be.**
      The clause forbids the hero's graded-decision ratio from falling. Paired over six seeds ×
      2,000 hands it fell: overall 0.25387 → 0.25125 (−0.26pp). **Both component ratios are
      flat** — preflop 0.57397 → 0.57448, postflop 0.03515 → 0.03458 — and the pooled figure
      moved only because the street mix did: hero postflop decisions rose 1.5% against a flat
      preflop count, and postflop grades at ~3% where preflop grades at ~57%. Hands go further,
      which is the metric failing to distinguish a grading regression from a deeper hand. Filed
      for the owner rather than fixed here, because shrinking the change until the ratio held
      would be fitting values to a gate.
      **Nine items are filed for the owner and none is resolved** — six from the postflop
      sizing work and three from the preflop sizing work, listed in the ledger under
      "Filed for the owner". Two of them bear on this phase's remaining slices: §7.1's coverage
      metric needs replacing before it gates anything else, and the lag's frozen showdown band
      has ~0.8 standard errors of headroom left, so the next change that lowers pot sizes trips
      it and will need a band decision rather than a value one.
      **The durable lesson, worth more than the status.** Three reviewers reviewed the last
      ticket and **each found something the other two missed** — a whole feature cell that
      silently kept a fixed size (the big blind's isolation raises, 300 of 300 draws at one
      size, hidden behind a validator that made the fix unauthorable and a report that never
      printed that node), and two declared sweep axes killed dead in a tool the ticket did not
      own. Neither was reachable from the ticket's own acceptance criteria.
      **Tickets and full build record:** `../tickets/phase3-derobotization.md` ·
      `../ledger/phase3-derobotization.md`.
> ⚠️ **AUDIT 2026-08-17 — ruled by owner the same day. Read this before touching any slice
> below.** Full record: `local/audit-2026-08-17-stage1.md` (machine-local). Two independent
> reviews plus a third adversarial review of the resulting plan. **The audit's own headline
> finding was retracted under review; what follows is what survived.**
>
> **RETRACTED, recorded because it was acted on for several hours.** The audit first claimed
> frequency tells are worth about 1.3:1 to a judge at 30 hands while bet-size structure is
> worth up to 16:1, and concluded that frequency work should stop. That comparison was
> unsound — it set the weakest frequency case (a hypothetical six-point error on the
> best-behaved persona) against the maximum cell of the structural table. Using the roster's
> REALIZED errors (station VPIP 63 against a 38 target, maniac PFR 37 against 14) the two
> channels are the same order, roughly 3:1 to 13:1. **Neither channel dominates, and no slice
> should be cut on the strength of that claim.**
>
> **What survives, and it is the important one: the bots' bet-size grid IS the grader's
> grid.** `backend/app/domain/table/sizing.py:58` pins
> `RECOGNIZED_BET_FRACS = (0.33, 0.5, 0.75, 1.0, 1.5)`, and
> `backend/app/domain/table/grade_map_reject.py` carries an explicit `BET_FRACTION_OFF_GRID`
> rejection for any bet off
> it. Varying bet sizes to look human therefore makes those hands ungradeable, against a
> coverage clause already failing at −0.26pp. **Realism and the teaching function are in
> direct architectural conflict on bet sizing, and no slice on this roadmap addresses it.**
> Escalated to the owner as a standing item; do not attempt size jitter until it is resolved.
>
> **Also surviving, with one correction (2026-08-18): de-robotization changed preflop opens
> and the postflop size ECOLOGY, not preflop only** — slice 1's own outcome above records the
> postflop class read falling from 0.557 to 0.441. What remains untouched is narrower than
> "everything postflop": the postflop fractions themselves, the isolation ladder and 4-bet
> sizing all still take single exact values. And the
> project's only real judge observation cuts against ranking tells by detectability at all —
> the judge explicitly noticed a control bot's "always 3x opens" and called it human anyway.
>
> **OWNER RULING 2026-08-17: stop building measurement apparatus. Ship improvements and
> accept the owner's own table judgement as the verdict.** The initiative has delivered five
> milestones of machinery and neither of the two measurements that were its point; a proposed
> measurement slice was rejected as the same failure mode repeating. The blind play-test is
> now the primary acceptance evidence, not a supplement to a detection number.

- [x] **Slice 2 — Invest-then-fold lines — CLOSED 2026-08-21.** SPEC'D + REVIEWED 2026-08-18;
      all three tickets merged 2026-08-19 (T1 #198, T2 #199, T3 #200); the six close-out pull
      requests (#201–#206) are also merged. **What closes it: the owner played the blind play
      session and the verdict was acceptance** — the bots felt plausibly human at the table,
      nothing stood out as robotic. Under the 2026-08-17 ruling the owner's table impressions
      at that session are the primary acceptance evidence for this phase, outranking the two
      statistical gates rather than supplementing them, so this play-session verdict is what
      closes the slice, not the merged ticket count on its own. Close-out record:
      `../ledger/phase3-invest-then-fold.md`. Spec
      `../specs/phase3-invest-then-fold.md` · tickets · ledger · contract map
      `../contracts/phase3-invest-then-fold.md` · evidence `../research/slice2-invest-then-fold/`.
      **The problem statement this entry used to carry was wrong.** It said bots abandon pots
      "for no reason a human would recognise". The reason is recognisable — they have nothing.
      Enumerated against the real boards, 84% of the folded holdings lack the price and 66%
      are drawing dead, so the slice does not try to make the fold go away. Two things ARE
      defective, and neither is the fold.
      **(1) Half the folds are forced, not chosen.** 524 of 1,147 events (46%) have exactly one
      weighted action: the river rule zeroes the call (`personas_postflop.py:1010`) and the
      engine offers no raise when the faced bet exceeds the stack
      (`table/engine.py:204-206`). The hypothesis this entry recorded on 2026-08-17 was
      right about the node and wrong in two details worth keeping: the raise is *illegal*,
      not merely unattractive, and two thirds of the cell is **ace-high, not air** (413 of
      550) — which is what produced the owner ruling below. **This is not a detection
      argument.** 524 events across 450,000 seat-hands is 0.03 per 30-hand judged bundle; it
      matters because it is the same lookup-table signature slice 1 removed from bet sizing.
      **(2) The money goes in as a CALL 62% of the time**, a raise 25%, a bet 13% — and 38% of
      the seats never bet or raised at all, which refutes the "build a pot with aggression"
      description inherited from remeasure SYNTHESIS §B.
      **Ceiling caveat — expect a small number, not zero.** 93% of events are refusals to call
      an all-in in pots averaging 253bb, and a fifth of hands see an all-in. That is the
      environment, which ruling A cut from this phase. T1's measured effect is −5.5%.
      **Measured at the shipped tip**, seed 20260817, ratified lineup: maniac 6.40 per 1,000
      hands, station 4.60, fish 2.77, **LAG 2.48** (missing from this entry's earlier list),
      tag 1.23, nit 0.22 — against the 2026-08-05 baseline of 7.0 / 5.58 / 2.60 / 2.22 / 1.19
      / 0.38. Four fell, two rose slightly; de-robotization did not fix this.
      **OWNER RULING 2026-08-18 — remove ACE_HIGH from the river call zero, keep AIR**
      (ticket T3). Deciding reason, recorded as a standing principle: the change is correct
      poker independently of the realism goal, so it cannot be Goodharted. When a realism
      change is *also* sound play, that asymmetry belongs in the options.
      **Tickets, as merged.** T1 (#198) ace-high stops floating multiway bets — measured
      1,147 → 1,084, showdown flat 54.5 → 54.1. T2 (#199): the bluff-frequency repricing this
      ticket was written to build was **withdrawn on an owner ruling** — measured against the
      betting-range identity the contract actually states, it moved stack-capped nodes further
      from target (0.4762 → 0.4022 against a 0.5168 uncapped norm) and flipped sign in the
      small-bet band. What shipped instead is a single test class, an estimator-parity guard
      that can now catch the villain-range estimator and the live sampler disagreeing; engine
      behaviour is byte-identical to T1. T3 (#200) is the ruling above, branched from T1 and
      measured on top of it: it ships at a damp of 0.06, not the ~0.46 the minimum-defence
      arithmetic derived, because a further owner ruling on 2026-08-19 capped it inside two
      frozen went-to-showdown bands. Measured: invest-then-fold events 1,084 → 1,015, pool
      went-to-showdown +0.94 points (54.14 → 55.09), inside the spec's 3.78-point bound.
- [ ] **Slice 3 — Calldown — BUILT 2026-08-22, close packet committed 2026-08-23; stays OPEN
      until the owner's blind play session.** All five tickets merged: S3-T1/T1b (#211/#212,
      price-conditioned strong-draw split), S3-T2 (#215, nit 0.45→0.32 and TAG 0.60→0.38 calling
      dials; LAG withdrawn on coupling), S3-T3 (#216, stack-to-pot value damp WITHDRAWN under
      triple review — instrument and contract limits shipped, engine byte-identical), S3-T4
      (#217, α guard over river ace-high as a strict-xfail tripwire; 24/24 cells breach, filed
      for ruling), S3-T5 (#218, late-street bet lever, admitted 2026-08-22 by owner ruling —
      only the LAG ships it under the pre-registered per-persona gate). **Measured chain-wide**
      (baseline `d351150` → tip `0561e8f`): pooled went-to-showdown −0.98pp on the band harness
      and −1.5pp on the 50k export; TAG −4.0/−4.3pp; every HARD band, ordering leg, and the
      five-seed de-robotization gate green. As the corrected entry below predicted, that is far
      short of the ~12-point counterfactual cutoff move — the slice's standing justification is
      the visibility argument, not that number. Close packet, filed owner decisions (six),
      finale-readiness packet, and play-session checklist:
      `../research/slice3-calldown/close-packet.md`. Original entry follows.
      **CORE SCOPE (owner-ruled 2026-08-21), and its headline number was
      wrong** *(corrected 2026-08-18)*. An earlier draft of the 2026-08-17 audit recommended
      cutting it; that was withdrawn under review, and the scope-valve question the withdrawal
      left open is now settled — see the ruling below. **Spec'd and approved by the owner,
      2026-08-21.** Spec: `docs/ai-dlc/specs/flywheel-slice3-calldown.md`. Tickets (S3-T1
      through S3-T4, a serial chain of four): `docs/ai-dlc/tickets/flywheel-slice3-calldown.md`.
      Contract map: `docs/ai-dlc/contracts/flywheel-slice3-calldown.md`. Measured against the
      Stage-0 interim went-to-showdown band regime (the grounded floors and one-way ceiling
      ratchet ratified 2026-08-21, landing in the parallel theory-contract PR), not the old
      frozen bands T3 above was capped inside of.
      ⚠️ **CORRECTION: this entry said the roster's went-to-showdown was "near 45". It is
      54.85.** The 44.92 figure came from the S5 close-out, where it is a *counterfactual* —
      the pool with the maniac's showdown rate driven to zero, constructed to prove no
      single-persona configuration reaches the cutoff. It was never the roster's value. The
      real one is recorded in
      `poker-analytics:analysis/output/score-campaign2-august-F1.json` under
      `canonical.pool_tier`: 59,907 showdowns over 109,214 seat-hands seeing the flop, seed
      20260805, ratified lineup — the 2026-08-05 run itself.
      **What that changes.** The pool distance clears its 5.1586 cutoff only if
      went-to-showdown falls to roughly 42.7. From "45" that reads as a two-point move and
      makes calldown look like it could close the ceiling. From 54.85 it is a **twelve-point**
      move. Went-to-showdown is about 91% of the pool distance squared, so calldown is still
      by far the largest available lever on that number — **and it will not be enough.** For
      scale: eliminating the calling station's showdowns entirely buys about 13 points.
      **The reason to keep it that does not depend on that metric:** showdowns are what make
      other tells visible to a judge at all. That argument stands on its own and does not rest
      on a study closed without a verdict, or on a surrogate score that failed its own
      validation. Treat it as the primary reason.
      **What it inherits from slice 2.** Under the boundary in that slice's spec §6.2 —
      slice 2 owns degenerate or mis-invested decisions, slice 3 owns continuation frequency
      at nodes that already mix — the calling personas' residual continuation is slice 3's.
      That is roughly 45% of the invest-then-fold events. It is NOT "these events belong to
      calldown because they happen to calling personas": the conditional rate is flat across
      all six, and slice 2's own T1 already reduces those personas. The boundary is drawn on
      the defect, not the persona.
      ⚠️ **Scope-valve contradiction — RULED 2026-08-21, kept for provenance.** *(Superseded
      text, kept because it is the record of the open question.)* ~~Scope-valve status needs
      an owner decision. The block header above still calls calldown "the declared scope
      valve, cut first if the appetite runs out", while this entry has said since 2026-08-17
      that it is "no longer the first thing to cut". Those contradict.~~ **Owner ruling:
      calldown (slice 3) is core scope, not the scope valve.** Deciding fact: slice 3 is the
      only slice on this roadmap that lowers pooled went-to-showdown, and slice 2's T3 raised
      it by roughly one point (54.14 → 55.09, see the slice 2 entry above). Cutting slice 3 for
      appetite would ship the improvement phase with a net increase in the roster's worst
      statistic. If the appetite runs out, something else gets cut instead — not slice 3. See
      the same ruling recorded in full at the improvement-phase block header above.
      **Now spec'd**, per the pointers above — it carries a post-T1/T2/T3 baseline on the
      ratified lineup, a defect definition sharper than "went-to-showdown is high", named code
      nodes, and the draw-floor decision below as a PREREQUISITE ticket (S3-T1), not a sibling,
      because that floor holds part of the strong-draw calling weight fixed no matter how far
      `call_looseness` tightens, and `call_looseness` is calldown's principal dial.
- [x] **Draw-floor bug — bots cannot fold a strong draw at any dial setting** *(NEW
      2026-08-17; assigned to slice 3 as a PREREQUISITE, 2026-08-18; **BUILT** as S3-T1,
      PR #211, merged 2026-08-21, and **price-conditioned** as S3-T1b, 2026-08-22)* — the
      floor is gone **as an unconditional floor**, which is the precise claim: at nodes
      whose price the draw's own equity pays for — the protected share clamps to 1.0, which
      is about 33% of strong-draw decisions in the band harness's organic population — the
      branch still reproduces the old floor **bitwise, by design**, and that is the property
      the original N-DRAWLOOSE fix existed for. What is gone is the floor applying at every
      price regardless. S3-T1 replaced it with a split that protects a flat 0.7 of the bonus
      from the calling dial and hands 0.3 to it; theory review then measured that a FLAT
      share is anti-protective where protection matters most — at the trace node, a 15-out
      combo draw getting 2.5-to-1, the nit's fold rate rose 0.2608 → 0.2945 — so S3-T1b made
      the protected share the share of the call the draw's own equity pays for at the price
      it faces (`_strong_draw_protected_share`), which restores those readings exactly and
      leaves the chase on the dial. S3-T1b also re-derived G-DRAW's cap: it is per node and
      derived from the price now, not a flat chosen budget of 0.030. **The design question
      below is CLOSED**; the three objections it records are answered in that helper's
      docstring. Original text follows. — `personas_postflop.py:1006-1007` floors the 0.55 strong-draw call bonus
      at `max(looseness, 1.0)`, so it does not shrink when `call_looseness` tightens. Five of
      six personas run below 1.0 (tag 0.60, lag 0.55, nit 0.45, fish 0.42, maniac 0.55 via
      fallback), so the floor is live for all of them and a large share of their calling
      weight is untunable · **do NOT simply delete the floor.** It was added deliberately as
      N-DRAWLOOSE so that nits would stop folding big draws, which is a defensible realism
      judgement; deleting it regresses that fix. Making it price-conditional was reviewed and
      found not implementable as first described — `_draw_equity` returns 0.0 on the river
      while STRONG is reachable there, the rule-of-4 heuristic is calibrated for the all-in
      node and self-declares uncalibrated, and the same predicate recurs at `:1128` and
      `:1351` · **the design question is open; ticket this before building** ·
      `../tickets/phase3-derobotization.md` records the related owner-filed items.

> **OWNER RULING 2026-08-21 — Stage-1 stack-commitment brake (`W4-a`) is DEFERRED past the
> phase-3 finale, as a named post-finale slice.** `W4-a` is a slice from the persona-realism
> roadmap (paused 2026-08-05 in favour of this flywheel initiative; see the top of this file)
> that would let a bot fold a made hand when the call it faces is huge relative to its
> remaining stack — the mechanism this file elsewhere calls the "commit-gated pots" gap. Its
> contract definitions, amendment blocks A1–A3, were ratified 2026-08-21 and are being
> committed to the theory contract in a parallel pull request; the mechanism itself stays out
> of this phase's engine/stack freeze. **Reopening trigger, attached to the ruling rather than
> left implicit:** if slice 3 (calldown) work stalls with any persona clearly outside its
> grounded went-to-showdown band and the residual is attributable to commit-gated pots, the
> scope question reopens at that moment rather than being re-argued from scratch.
>
> **OWNER RULING 2026-08-21 — Stage-0 interim went-to-showdown band regime is RATIFIED.** The
> interim regime has three components: grounded floors, a one-way downward ceiling ratchet
> (bands may only tighten, never loosen, as the roster improves), and the maniac's
> went-to-showdown assertion restored at a ratcheted ceiling — it has been skipped since
> 2026-08-01. It replaces the old frozen went-to-showdown bands that capped slice 2's T3 ticket
> above. It lands in the same parallel theory-contract pull request as the `W4-a` amendment
> blocks. Slice 3 (calldown) will be spec'd and measured against this interim regime, not the
> old frozen bands; see the slice 3 entry above.

**Scope valves (appetite is a cap — cut scope, not quality):** S5 confirmatory study deferred
unless the pilot is ambiguous · S2b commercial lane is the first research cut · S6 pilot may
shrink judge count, never blinding. Critical path S1→S2a→S3→S4→S5 ≈ 15–21 working days with
S2b and S6 in parallel; if that exceeds the part-time window, the valves fire in the order
listed rather than the gate slipping silently.

## NEXT (validated problems, not yet spec'd)

- **S6 — Detection pilot: MEASUREMENT ATTEMPTED 2026-08-14 (owner-initiated, overriding
  the 2026-08-13 deferral) → PROTOCOL SHAKEDOWN, terminated at the control pre-screen.**
  The harness ran end-to-end on live vendor APIs, but the pre-screen judge labelled the
  T1 control bot `human` twice (second time at full reasoning effort, while explicitly
  noticing its "always 3x opens" tell), so the paid run was stopped at ~4¢ of spend —
  under §d.2's 4-of-4 control rule a full run was near-certain to be invalidated. Full
  record: `poker-analytics:docs/methods/detection-pilot-s6.md` §5 + §7. Two consequences:
  (i) any future S6 execution first needs a stronger control —
  `docs/ai-dlc/tickets/flywheel-s6-control-redesign.md`, gated on phase-3; (ii) the
  phase-3 gate's open question about this metric now has a second, sharper edge —
  see the amended bullet below. Original entry follows for provenance:
  ~~BUILT AND MERGED, MEASUREMENT DEFERRED (owner, 2026-08-13)~~ —
  outcome-link: the north star itself · what exists: corpus builder, renderer, judging harness
  and statistics all merged (coach PRs #176, #177), stub-judge dry run passed; only the live
  judging run is outstanding (API keys + ~330 model calls) · why deferred: it cannot unlock the
  S5 verdict on its own, since §a.4's ladder fails for independent reasons (stages 2 and 3 were
  never run), and the measurement **recurs every time the bots change** while today's answer is
  predictable from S5 and expires at the next change · **run it when there is a changed bot
  worth measuring** · cost basis and panel pinning: the owner execution checklist
  `docs/ai-dlc/specs/flywheel-s6-execution-checklist.md` (cost band + the §g.3 4-judge/2-vendor
  panel; the older ticket `docs/ai-dlc/tickets/flywheel-s6.md` predates the §g.3 panel
  amendment — trust the checklist);
  substituting a model family is an amendment, permitted only before the first call fires ·
  **open question for the phase-3 gate, now two-edged (second edge added 2026-08-14): (a)
  cost — single-digit to low-tens of dollars per measurement (checklist cost band; recompute
  at live prices, and thinking tokens are now a real Anthropic output-cost line) recurring
  each cycle may be too expensive for the flywheel's north-star metric; (b) sensitivity — the shakedown showed a
  strong LLM judge reading the registry's most degenerate possible bot as human over a
  30-hand window, so the protocol may be unable to distinguish bots this initiative could
  plausibly build; settle both before building an iteration loop around it** · no-gos unchanged: not the baseline for
  target-setting; no judge sees labels or seat maps; scope frozen.
- **True detection baseline + owner target** — evidence: S6 is single-player by design; a
  target set on pilot numbers would inherit its biases · candidate slices: multi-player human
  sample (licensed corpus per S2b verdict, and/or recruited sessions), matched-environment
  extraction, baseline measurement, owner sets the target · open questions: corpus licensing,
  how many players suffice.
- **Phase-3 gate packet & decision** — evidence: S5 + S6 outputs; the fix-vs-overhaul decision
  the owner ruled must precede any persona work · candidate slices: **preregistered decision
  matrix** (score/detection attainability · which failures are structurally unreachable ·
  effort/risk of current-engine fixes · the out-of-scope capability gaps (stacks, session
  memory, multiway pricing, economy, **and within-archetype variation — added 2026-08-09**) ·
  runtime constraints · confidence, with an INCONCLUSIVE path); if FIX → re-scope A1–A4
  (SYNTHESIS §4 families) as flywheel-priced slices; if OVERHAUL → architecture design brief
  **ingesting the stack/multiway/state-awareness requirements so the architecture is designed
  once** · open questions: owner's decision weights.
  - **Within-archetype variation — evidence pointing at FIX, not overhaul (corrected
    2026-08-13).** An earlier draft of this roadmap filed "two seats of the same type cannot
    differ" in the structurally-unreachable column. That was wrong, and the correction points
    the opposite way. The **policy engine is already seat-keyed**: `advance_to_hero` takes a
    `dict[int, PersonaPack]` and hands each seat its own pack
    (`backend/app/domain/table/play.py:291,313`), `bot_decision` receives a pack as an argument
    rather than looking one up (`play.py:209`), the live app already builds a seat→pack map
    (`backend/app/services/sim_session.py:188`), and nothing in postflop behaviour branches on
    which archetype a seat is (`personas_postflop.py` contains no `pack.persona` reads). What is
    missing sits **outside** the domain core: the export tools bind packs by persona name
    (`tools/export_analytics.py:329`), a seat has nowhere to persist a variant identity, and the
    counterfactual override document is persona-keyed rather than seat-keyed (an S2a contract
    change). Only one narrow case genuinely needs domain edits — adding a *seventh named
    archetype*, because `PersonaPack.persona` is a `VillainType` enum
    (`app/domain/content/models.py:336`) and packs load by that enum (`personas.py:40-52`).
    **Weigh this as configuration and persistence work on an engine that already supports the
    behaviour, not as an architectural gap** — and re-open whether the product lane's third
    slice is blocked at all.
- **Training-app table controls (persona labels · table picker · roster chooser)** *(new
  2026-08-09, from owner observation; **FROZEN until the phase-3 gate by owner ruling** — see
  the no-gos block)* — problem: the app names each opponent's type on screen, so the player
  never practises forming a read; and there is one fixed nine-seat lineup, so every session is
  spent against the same table · **outcome-link: none — this is owner-stated product quality,
  tracked as a bet, not as movement on a north-star metric** (corrected 2026-08-13: an earlier
  draft linked it to "coaching usefulness", a phrase this roadmap never defines, baselines, or
  measures — claiming it as an outcome-link was an outcome-in-costume) · candidate slices, one
  line each, to be specified properly only if the test below passes: **(1) persona-label
  toggle** — hide every persona name and badge in Simulate, opt-in reveal after the session;
  **(2) random table picker** — choose between up to three freshly generated rosters,
  regenerated on restart and on leaving a table, each reproducible from a stored seed;
  **(3) custom roster chooser** — the player specifies the archetype mix.
  · riskiest assumption: *hiding labels and varying the roster measurably improves training
  value* — **untested**. Cheapest test, rewritten 2026-08-13 because the first version was
  unusable: it proposed hiding labels to test the value of hiding labels, which is slice 1 and
  therefore inside the freeze, and it scored the result on one person's unaided impression with
  no criterion. Replacement: **before each reveal the owner writes down a predicted archetype
  for three named seats; pass = at least four of six predictions correct across two sessions,
  plus a written judgement that the session played differently from the labelled baseline.**
  That still needs labels hidden, so name the execution path explicitly at the gate — either a
  local uncommitted hide (nothing committed, nothing shipped) or the test simply starts when the
  freeze lifts. Per the assumption-first rule the test goes first and alone; the three slices
  stay in NEXT until it reports · no-gos: no change to persona policy code or committed pack
  values (that is the global freeze) · **re-opened 2026-08-13:** the fourth thing the owner asked
  for — bots of the same type differing slightly — was excluded from this lane on the false
  grounds that the engine could not express it. The engine can (see the phase-3 gate item). It
  stays out of this lane only because the gate owns the config/persistence decision it depends
  on, not because it is impossible · open questions: whether table choice persists across
  restarts; whether hidden labels should also hide the post-hand grader's references to
  opponent type.
- **Population-statistics ingestion + target-registry upgrade** *(RE-SCOPED 2026-08-06 by owner
  ruling on S2b's gate brief — was "Corpus ingestion"; the acquire-hands framing is CLOSED)* —
  evidence: S2b verdict **PARTIAL**
  (`../research/realism-architecture/03-nlhe-corpus-gate-brief.md`) — **NO-GO on a licensing-clean
  corpus of human NLHE *hands*** (every candidate of adequate size traces to ToS-prohibited
  datamining; a downstream CC-BY licence does not cure an upstream terms violation — this is a
  **policy/ethics** NO-GO, not a legal ruling), but modern human NLHE **statistics** are
  obtainable, and statistics are what the registry actually consumes · **owner ruling 2026-08-06:
  use the published GGPoker pool aggregates AND disclose the provenance gap openly**, under four
  binding conditions — record each value with its exact filter combination (stake · segment ·
  statistic) + retrieval date, since the source is a rolling 12-month window and a date alone
  cannot reproduce it; grade every derived target low-confidence (no sample size or methodology is
  published); **construct and justify the strata→persona mapping** (regulars/recreationals are
  profitability-and-VPIP strata, **not** TAG/LAG/nit/station/maniac); state the limitation in the
  registry and in any public write-up · candidate slices: pinned aggregate ingestion into
  poker-analytics, strata→archetype mapping with written justification, registry swap off
  literature bands (verified to be uncited author opinion), expert-elicitation panel (SHELF/Delphi)
  **only** for stats the aggregates do not cover · **the only credible route back to actual hands
  remains a formal operator data-sharing agreement** — the Entain/PMC9325659 precedent proves the
  pathway exists, but it delivered financial aggregates, so any agreement must be scoped in writing
  to hand-level or play-style data plus rights to publish derived statistics; **keep it listed, do
  not pursue it now** · open questions: era-drift validity (no quantified NLHE trend line exists),
  single-site bias (GGPoker only), how to pin a rolling-window source reproducibly.
- **Portfolio publication path** — evidence: dual-purpose mandate; poker-analytics currently
  private · **strategy (owner-ratified 2026-08-05): curated narrative public, raw exhaust
  private.** Public = README front door + 2–3 polished methodology write-ups (score design +
  validation incl. failures, detection protocol, reachability study), decision records,
  limitations sections. Private/stripped = ai-dlc ledgers, ticket adjudications, agent-fleet
  mechanics, hand-history data. The remeasure SYNTHESIS/PROTOCOL stay local in poker-coach
  (owner ruling — never-push dir); their PUBLIC form is authored fresh in poker-analytics ·
  candidate slices: publication-readiness review **including a hiring-manager red-team**
  (adversarial review of the public repo from a skeptical senior-AE persona, before
  visibility flips), write-ups, dataset/model cards (reproducibility pins per PRD §5) · open
  questions: exact strip list at flip time.

## LATER (bets — no dates)

- **Bet: architecture overhaul to a modeled policy** · segment: whole roster · confidence: med
  (pending S5) · assumptions to test: operational ceiling confirmed and diagnosed structural;
  learned policy meets real-time + ~500 hands/sec sim throughput; trainable from available
  data · review-by: at the phase-3 gate.
- **Bet: stack-persistence gameplay + state-aware personas** (heater fear H5, effective
  stacks, multiway pricing) · confidence: hi on desirability, unknown on architecture fit ·
  assumptions: architecture decision ingests these requirements first · review-by: after the
  phase-3 decision (phases 4–5 of the owner's plan).
- **Bet: per-seat identity — bots of the same type that differ from one another** *(new
  2026-08-09)* · segment: whole roster · owner's own examples: a table of three maniacs where
  one opens a much tighter preflop range and another bluffs less often · confidence: hi on
  desirability (owner-stated), unknown on architecture fit · assumptions to test: that a varied
  table reads as more human than a clone table at all (no evidence either way today); that
  per-seat pack binding is cheap in whatever architecture the phase-3 gate chooses; that
  varying within a type does not blur the archetype-separation floor the Goodhart guard
  protects · review-by: at the phase-3 gate, together with the capability-gap evidence in the
  gate item above.
- **Bet: detection-rate as the portfolio centerpiece** (before/after curves) · confidence:
  med · assumptions: S2a protocol credible to a technical interviewer; multi-player baseline
  exists · review-by: first post-fix detection measurement.
- **Bet: `T-agentcoach` unblock** (teacher-rework dependency) · confidence: med · assumptions:
  post-gate roster clears the owner's bar · review-by: next re-measure after fixes.

## Out of scope / no-gos (global)

- 🚫 Persona-fix code or COMMITTED pack-value changes before the phase-3 gate (verification:
  clean `git diff` on `backend/app/domain/` + `content/`; S4's ephemeral counterfactual
  configs are explicitly not commits).
- 🚫 **The training-app table-controls lane, in full, before the phase-3 gate** (owner ruling
  2026-08-09). This is stricter than the rule above it: the label toggle and the table picker
  touch only frontend and table composition, so the persona-code freeze would not have caught
  them. The owner froze all three anyway to keep attention on the gate. Known consequence
  (2026-08-13): the lane's own falsification test needs labels hidden, which is slice 1, so the
  freeze also freezes the test that would justify the lane — resolve that at the gate rather
  than by quietly exempting one slice.
- 🚫 Per-decision-LLM bot policy (latency + throughput constraints).
- 🚫 Corpus data in poker-coach; unlicensed data anywhere public.
- 🚫 Flywheel v0 blocking on the corpus (registry v0 = graded literature bands by design).
- 🚫 Detection optimization outside the Goodhart constraint set (north-star section).
- 🚫 Standing repo no-gos: no solver tables · no auth/hosting/billing · no hand-history
  imports as an APP feature (research corpora in poker-analytics are distinct and allowed).
- 🚫 Treating archetype separation *per se* as a defect — being recognisable as a type is
  wanted, not broken (north-star section). Narrowed 2026-08-13: this bans the reflex, NOT the
  finding. A future, evidenced result that identifiability above the human rate is itself a
  detection signal is permitted and should be reported; the earlier wording banned an
  interpretation of future data, which has no place in an initiative built on preregistration.
- Owner-parked: owner-plays-personas calibration sessions (revisit only if a node lacks any
  trustworthy target; nit/TAG/LAG only, ~100–200 hands).
