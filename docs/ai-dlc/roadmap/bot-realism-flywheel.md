# Bot-Realism Flywheel Roadmap — updated 2026-08-05 (rev 2, post dual review)
status: approved (owner, 2026-08-05 — PR #169 merged + explicit handoff instruction; next action: /ai-org:spec S1)

> **Governing initiative for all bot-realism work.** Supersedes the NOW-lane of
> `persona-realism.md` (paused by owner ruling 2026-08-05: *no further persona-fix work until
> the ceiling verdict*; its history and contracts remain authoritative for what shipped).
> PRD: `../prd/bot-realism-flywheel.md`. Evidence base: `../research/persona-realism-artifacts/
> remeasure-2026-08-05/SYNTHESIS.md`. Cross-repo: poker-coach produces data; **poker-analytics**
> produces judgment (scorer, targets, corpus, methodology docs — also the portfolio surface).
> Contract maps: the dial engine is mapped by the theory contract +
> `docs/research/12-persona-engine-and-realism-fixes.md`; the export interface by the analytics
> contract (PR #161); the measurement instrument by remeasure SYNTHESIS §5 — no new
> contract-mapper pass needed.
> **Rev 2** folds the dual roadmap review (refuter NEEDS-WORK + Codex Sol FAIL; adjudication
> ledger: `../ledger/bot-realism-flywheel-roadmap-review.md`).
> **Durability (owner rulings 2026-08-05):** this roadmap, the PRD, the review ledger, and
> START-HERE.md are COMMITTED (PR #169 — exception to the docs-stay-uncommitted practice).
> The remeasure SYNTHESIS/PROTOCOL stay LOCAL (never-push artifacts dir upheld; their public
> form gets authored fresh in poker-analytics). Orientation: `../START-HERE.md`.
> **Cleanup obligation (owner ruling 2026-08-05):** when this roadmap completes, run a cleanup
> slice — delete or banner every artifact that is no longer needed (superseded reports, stale
> spot lists, sim exports, interim status docs, stale memory entries) so the repo doesn't
> accumulate misleading history.
> Resume rule: work slices in order; verify a pass/fail ACTUALLY passes before `[x]`. On any
> conflict between this roadmap and another doc/ticket, STOP and surface it to the owner
> (tripwires in `.claude/CLAUDE.md`).

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

## NOW (in order — appetite CAP: ~2–3 wk part-time to the phase-3 gate; scope valves below)

- [x] **S1 — Cross-repo working agreement + walking skeleton** *(2026-08-05: agreement in
      both repos + stub pipe verified — exact per-persona counts, dual fan-in review; ledger
      `../ledger/flywheel-s1.md`)* — problem: two repos + two
      parallel sessions, no collision protocol; loop must span repos in one command ·
      outcome-link: enables everything · pass/fail: agreement doc committed in BOTH repos
      (ownership manifest, interface, versioning, session-R/session-F protocol, S6∥S5
      scheduling note) AND a stub scorer in poker-analytics runs end-to-end from one
      poker-coach command against the **sim50k export**
      (`remeasure-2026-08-05/sim50k/`, local/gitignored) · appetite: 1–2 days · no-gos: no
      real scoring logic; no bot-code changes.
- [x] **S2a — Methods & estimand contract** *(2026-08-05: `poker-analytics:docs/methods/
      estimand-contract.md` v2.3 — dual review PASSED after 4 rounds; ledger
      `../ledger/flywheel-s2a.md`; P1/P2 artifacts in `../research/flywheel-s2a/`)*
      (BLOCKS the design of S3/S4/S5/S6) — problem:
      score, sweep, and detection specs were being written before the methodology that must
      shape them (Sol HIGH-8); "dial space" and "reachable" are undefined against a config
      model that is NOT a 5-dim box (coupled optional levers, frozen references, sizing
      distributions, preflop mix tables — `backend/app/domain/content/models.py`) ·
      outcome-link: trustworthiness of the ceiling verdict · pass/fail: one contract doc,
      dual-reviewed, containing (a) **search-space & estimand contract** — swept parameters +
      bounds + coupled constraints + persona joint-vs-independent treatment + the
      REACHABLE / NOT-REACHABLE / INCONCLUSIVE decision rule, with the verdict explicitly
      framed as an *operational ceiling within declared space and compute budget*; (b)
      **target registry** — per-stat numerator/denominator, source, population/format
      compatibility, uncertainty, confidence grade; graded distance + covariance-aware
      weighting (no hard in/out cliffs); (c) **counterfactual-config schema** — ephemeral
      override layer validated through the real pack model; "read-only" = no committed
      production-value changes, validated temporary counterfactuals allowed; (d) **detection
      protocol preregistration** — judgment unit, exposure length, balanced priors, matched
      information, statistic (balanced accuracy/AUC/d′), leak controls, cluster-aware CIs;
      (e) **score-validation plan** — n=13 is directional-only: report Spearman ρ WITH CI and
      p-value + sign-agreement check; at most ONE pre-registered score revision; if it still
      fails → STOP-GATE: score stays "exploratory surrogate," S5 may NOT issue a score-only
      verdict, convergent evidence (detection pilot) required; (f) **compute budget** — one
      full config benchmarked, N chosen from the budget · appetite: 3–4 days (consumes the
      DS-methodology research, pulled INTO this slice from the research wave) · no-gos: no
      implementation.
- [ ] **S2b — Research wave (parallel session R; may launch ONLY after S1 completes — the
      session-R protocol it depends on is S1's deliverable)** *(progress 2026-08-06: session R
      DELIVERED — four dossiers + completion note in `../research/realism-architecture/`,
      uncommitted; the corpus-gate owner ruling is obtained and recorded in the NEXT item
      below. Remaining before `[x]`: director fan-in review, commit accepted dossiers from a
      worktree, and check whether the consumption map forces amendments to the S2a estimand
      contract)* — problem: architecture bet needs
      evidence; prior planning missed known prior art (Alberta CPRG); NLHE-corpus existence
      unknown · outcome-link: phase-3 gate quality + corpus bet · pass/fail: 3 dossiers in
      `docs/ai-dlc/research/realism-architecture/` (academic incl. Alberta lineage ·
      commercial practice · NLHE-corpus gate brief ending GO/PARTIAL/NO-GO with licensing
      assessment; on PARTIAL/NO-GO the brief must evaluate the owner-agreed **fallback
      ladder**: (i) limit-era data for era-stable shape parameters only, each with explicit
      justification, (ii) modern tracker-site population statistics (aggregates, not hands),
      (iii) spot-level expert/LLM elicitation panels, (iv) literature bands as the floor) PLUS
      a **consumption map** (each conclusion → scorer / sweep / detection / architecture
      option / corpus decision / explicitly-rejected, with evidence grade) · appetite: ~1 wk
      in session R, parallel to S2a–S4 · no-gos: docs-only session (no git, no code, no sims);
      no data downloads without licensing review.
- [x] **S3 — Realism score v0 + validation (per S2a plan)** — ✅ 2026-08-07. Built +
      dual-reviewed end-to-end (scorer 0.71 s/50k batch, byte-identical; five §a.5
      checkers; both campaigns scored incl. a July-engine reconstruction). **Validation
      outcome: retrospective-FAIL on all three legs under F0 AND the one-shot F1 —
      every statistic NEGATIVE-signed (F0 ρ=−0.20, F1 ρ=−0.38; two independent
      reviewers reproduced every number from scratch, zero mismatches; sign negative
      within each campaign independently). The §e.3 stop-gate fired as preregistered:
      score status = exploratory-surrogate; S5 may not issue a score-only verdict; §e.3
      is spent.** The slice's own pass/fail (below) is met — the deliverable was honest
      execution with the stop-gate honored, and it held. — problem: measurement costs
      agent fleets; no computable objective exists · outcome-link: flywheel inner loop ·
      pass/fail: the TWO-TIER score (graded distance over the S2a target registry) runs on the
      sim50k export in <5 min, deterministic given seed — pool-level D(x) is the ONLY verdict
      anchor; the per-persona tier is reported, never gating: avg = the progress metric,
      floor = worst persona = a non-gating diagnostic (**the per-persona gate was deleted by
      owner ruling 2026-08-06** — it could only ever bind on PFR/3-bet; §a.5 keeps five rules,
      not six); validation executed EXACTLY per S2a plan (e) as amended — the legs run on the
      per-persona score — with its stop-gate honored, and the score's status recorded in the
      output as **retrospective-pass / retrospective-fail / exploratory-surrogate**
      (validation is pre-labeled RETROSPECTIVE face-validity by owner ruling 2026-08-06;
      "confirmatory" is reserved for a future campaign with fresh blind ratings)
      · appetite: 5–7 days (re-costed 2026-08-06: the two-tier ruling added the
      per-persona tier and the registry swap to pinned external data) · no-gos: no internal-theory-
      contract bands; no rendered-text parsing; **scores are non-authoritative for any
      conclusion until validation passes** (S4 may use them only as reproducibility smoke
      data — stated identically in the PRD).
- [ ] **S4 — Batch sweep runner + counterfactual-config layer** — problem: no way to price N
      dial configs · outcome-link: reachability + all future tuning · pass/fail: one command:
      N configs (S2a schema) → N seeded runs → N scores, manifest-pinned (engine sha · seed ·
      config hash · scorer version · registry version); 10-config smoke batch reproduces
      byte-identical scores; one-config benchmark recorded against the S2a compute budget ·
      appetite: 2–3 days · no-gos: configs sweep the S2a-declared space only — no policy-code
      edits, no committed pack changes.
- [ ] **S5 — Reachability study + operational-ceiling verdict** — problem: unknown whether
      ANY declared-space config reaches human-band behavior (the owner's gate question) ·
      outcome-link: decides phase 3 · pass/fail: verdict doc per the S2a estimand contract:
      pilot response surface + DoE-style mechanism probes (per-dial and interaction effects
      for each failing stat), **winner's-curse guard** (top configs re-run on fresh seeds
      before any "reachable" claim), verdict ∈ {REACHABLE, NOT-REACHABLE, INCONCLUSIVE}
      framed as operational-ceiling-within-declared-space, dual-adversarially reviewed ·
      appetite: 4–5 days (pilot; a confirmatory study runs ONLY if the pilot is ambiguous —
      that is the appetite scope valve) · no-gos: no fix recommendations smuggled in; no
      score-only verdict if the S3 stop-gate fired.
- [ ] **S6 — Detection-protocol feasibility pilot** — problem: the north star has no working
      protocol and no number of any kind · outcome-link: the north star itself · pass/fail:
      the S2a-preregistered protocol executed once on a mixed corpus (bot seats + owner HERO
      hands as the v0 human class); result reported as a SINGLE-PLAYER PILOT with the
      single-subject/session/opponent-composition biases and their expected direction named
      in the write-up; judges see opaque IDs only (remeasure blinding lessons applied) ·
      appetite: 2–3 days, runs in parallel with S5 (after S2a + S3) · no-gos: this number is
      NOT the baseline for target-setting; no judge sees labels or seat maps.

**Scope valves (appetite is a cap — cut scope, not quality):** S5 confirmatory study deferred
unless the pilot is ambiguous · S2b commercial lane is the first research cut · S6 pilot may
shrink judge count, never blinding. Critical path S1→S2a→S3→S4→S5 ≈ 15–21 working days with
S2b and S6 in parallel; if that exceeds the part-time window, the valves fire in the order
listed rather than the gate slipping silently.

## NEXT (validated problems, not yet spec'd)

- **True detection baseline + owner target** — evidence: S6 is single-player by design; a
  target set on pilot numbers would inherit its biases · candidate slices: multi-player human
  sample (licensed corpus per S2b verdict, and/or recruited sessions), matched-environment
  extraction, baseline measurement, owner sets the target · open questions: corpus licensing,
  how many players suffice.
- **Phase-3 gate packet & decision** — evidence: S5 + S6 outputs; the fix-vs-overhaul decision
  the owner ruled must precede any persona work · candidate slices: **preregistered decision
  matrix** (score/detection attainability · which failures are structurally unreachable ·
  effort/risk of current-engine fixes · the out-of-scope capability gaps (stacks, session
  memory, multiway pricing, economy) · runtime constraints · confidence, with an INCONCLUSIVE
  path); if FIX → re-scope A1–A4 (SYNTHESIS §4 families) as flywheel-priced slices; if
  OVERHAUL → architecture design brief **ingesting the stack/multiway/state-awareness
  requirements so the architecture is designed once** · open questions: owner's decision
  weights.
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
- **Bet: detection-rate as the portfolio centerpiece** (before/after curves) · confidence:
  med · assumptions: S2a protocol credible to a technical interviewer; multi-player baseline
  exists · review-by: first post-fix detection measurement.
- **Bet: `T-agentcoach` unblock** (teacher-rework dependency) · confidence: med · assumptions:
  post-gate roster clears the owner's bar · review-by: next re-measure after fixes.

## Out of scope / no-gos (global)

- 🚫 Persona-fix code or COMMITTED pack-value changes before the phase-3 gate (verification:
  clean `git diff` on `backend/app/domain/` + `content/`; S4's ephemeral counterfactual
  configs are explicitly not commits).
- 🚫 Per-decision-LLM bot policy (latency + throughput constraints).
- 🚫 Corpus data in poker-coach; unlicensed data anywhere public.
- 🚫 Flywheel v0 blocking on the corpus (registry v0 = graded literature bands by design).
- 🚫 Detection optimization outside the Goodhart constraint set (north-star section).
- 🚫 Standing repo no-gos: no solver tables · no auth/hosting/billing · no hand-history
  imports as an APP feature (research corpora in poker-analytics are distinct and allowed).
- Owner-parked: owner-plays-personas calibration sessions (revisit only if a node lacks any
  trustworthy target; nit/TAG/LAG only, ~100–200 hands).
