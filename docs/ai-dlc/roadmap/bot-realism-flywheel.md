# Bot-Realism Flywheel Roadmap — updated 2026-08-17 (rev 4)
status: approved (owner, 2026-08-05 — PR #169 merged). Rev-4 wording is pending owner review;
the rulings it records were made 2026-08-09 through 2026-08-13. *(It was described here as
uncommitted until 2026-08-17; it has in fact been committed since PR #180. Corrected in
passing.)* The 2026-08-17 edit adds the improvement-phase block to the NOW lane and changes
nothing else.

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
> lines, calldown as the scope valve; engine/stack work excluded; 2–3 weeks appetite;
> one finale detection run at the end under the new rule-breaker control, plus the
> preregistered owner blind play-test as product acceptance.
> **Slice-by-slice state for that phase is the improvement-phase block at the END of this
> lane (added 2026-08-17): slice 1 de-robotization is CLOSED, slices 2 and 3 are unstarted
> and unspec'd. Resume there, not from this banner.**
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

### Improvement phase (ruling A) — three slices in order, one closed

> **Why this block exists (added 2026-08-17).** Ruling A defines three improvement slices and
> the NOW lane had entries for none of them: the order lived in
> `../specs/phase3-decision-matrix.md` §4 and in the STATE banner at the top of this lane, but
> not as slices a fresh session could resume from — which is what the boot checklist in
> `.claude/CLAUDE.md` tells that session to do. The order is **(1) de-robotization →
> (2) invest-then-fold → (3) calldown**, calldown being the declared scope valve, cut first if
> the appetite runs out. Engine/stack work is cut from this phase entirely. Appetite: 2–3 weeks
> part-time, running since the ruling on 2026-08-15. Exactly ONE finale detection run at the
> end; a second requires a recorded amendment written before it fires. The
> ⚠️ warning above applies to everything here — **none of the numbers below is a detection
> number.** They come from the two statistical gates and from purpose-built tell statistics,
> which measure whether a specific mechanical signature is gone, not whether anyone was fooled.

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
- [ ] **Slice 2 — Invest-then-fold lines** — problem: bots put money in and then abandon the
      pot for no reason a human would recognise (remeasure SYNTHESIS §B) · **not yet spec'd —
      needs `/ai-org:spec` before any build.**
- [ ] **Slice 3 — Calldown** — **this is the declared scope valve.** If the 2–3 week appetite
      runs out, this slice is cut, and cutting it is the planned outcome rather than a failure ·
      **not yet spec'd.**

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
