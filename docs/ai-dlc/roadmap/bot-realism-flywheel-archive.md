# Bot-realism flywheel — archive of completed slices and standing rulings

**Bottom line:** this file holds two things the live roadmap no longer has room for — the full
text of the finished slices, and the standing rulings that still bind but never change. Nothing
here is pending work. The live roadmap is `bot-realism-flywheel.md`. Read this when you need the
detail behind a completed slice, or when you need the exact wording of a standing ruling.

Archived 2026-08-09 when the live roadmap crossed the readability cap; extended 2026-08-13 with
the standing rulings and the amendment log. Slice text is reproduced verbatim as it stood at
completion; do not edit it to reflect later events — record those in the live roadmap instead.

## Standing rulings (still binding — moved here 2026-08-13, unchanged)

- **Durability (owner rulings 2026-08-05):** the roadmap, the PRD, the review ledger, and
  `START-HERE.md` are COMMITTED (PR #169 — an exception to the docs-stay-uncommitted practice).
  The remeasure SYNTHESIS/PROTOCOL stay LOCAL (never-push artifacts dir upheld; their public
  form gets authored fresh in poker-analytics). Orientation: `../START-HERE.md`.
- **Cleanup obligation (owner ruling 2026-08-05):** when the roadmap completes, run a cleanup
  slice — delete or banner every artifact no longer needed (superseded reports, stale spot
  lists, sim exports, interim status docs, stale memory entries) so the repo does not accumulate
  misleading history.
- **Resume rule:** work slices in order; verify a pass/fail ACTUALLY passes before `[x]`. On any
  conflict between the roadmap and another doc or ticket, STOP and surface it to the owner
  (tripwires in `.claude/CLAUDE.md`).
- **Contract maps:** the dial engine is mapped by the theory contract plus
  `docs/research/12-persona-engine-and-realism-fixes.md`; the export interface by the analytics
  contract (PR #161); the measurement instrument by remeasure SYNTHESIS §5.

## Amendment log

### Rev 3 (2026-08-09, owner-ruled) — three changes, later partly corrected

Raised in one conversation. None touched a pin, a seed, a config, or the run budget.

1. **A readable persona is a feature, not a defect.** The director had called the re-measure's
   "56 of 56 personas identified" result damning, contradicting the Goodhart guard's own
   archetype-separation floor. Landed in the north-star section and the no-gos block.
2. **Within-archetype variation was filed as a structural capability gap.** ⚠️ **This was
   wrong — see rev 4.**
3. **A training-app product lane was captured and frozen** — persona-label controls, table
   picker, roster chooser. Landed in NEXT with its own no-go.

### Rev 4 (2026-08-13) — corrections from a blind adversarial review

A blind reviewer (no access to the conversation that produced rev 3) returned NEEDS-WORK with
two blocking findings. Both were verified against source before being accepted.

1. **Rev 3's capability claim was refuted.** "Two seats of the same type cannot differ" is
   false: the policy engine is already seat-keyed (`app/domain/table/play.py:291,313`,
   `app/services/sim_session.py:188`) and nothing in postflop behaviour branches on which
   archetype a seat is. The gap sits in the export tools, persistence, and the persona-keyed
   override schema — configuration work, not architecture. This **reverses the direction of the
   inference**: it argues repair, not rebuild. Corrected in the phase-3 gate item.
2. **A claimed action had not happened — since resolved.** Rev 3 said the clone limitation
   "landed as a stated limitation of the S5 verdict"; at the time the close-out carried no such
   text and the T7 instruction was open. Corrected first to "required, not yet applied", then
   satisfied the same day: the limitation now sits in
   `poker-analytics:docs/methods/reachability-verdict-s5.md` §8, carrying the corrected
   diagnosis (a configuration limit above the engine, not an engine limit). T7 is closed.
3. **The separation floor was unfalsifiable** — no threshold, no human comparator, and the
   supporting "56 of 56" was a closed-set task with roster composition disclosed. Restated as a
   band that is not yet measurable, and the matching no-go narrowed so it bans the reflex rather
   than a future evidenced finding.
4. **The product lane's own test was circular** — it proposed hiding labels to test the value of
   hiding labels, which is the frozen slice itself, scored on one unaided impression. Replaced
   with a predict-then-reveal criterion, and the freeze's effect on it recorded openly.
5. **Size and preamble caps were breached** (280 lines against a 200 soft cap; roughly eight
   pointers before the north-star). This section, and the standing rulings above, are what moved.

## Completed slices (S1, S2a, S2b, S3, S4)

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
- [x] **S2b — Research wave** *(2026-08-06: session R delivered 3 dossiers + consumption map
      in `../research/realism-architecture/`; corpus verdict **PARTIAL**; blind cross-family
      review NEEDS-WORK → 13 findings all accepted and folded; two owner rulings recorded —
      use-and-disclose on published aggregates, and this roadmap's corpus NEXT item re-scoped.
      Headline: **the phase-3 gate is not a fix-vs-rebuild binary** — the only mechanism in the
      retrieved literature with a blind-test pass behind it is hand-authored targeting of
      human-likeness, structurally what the dial engine already is, re-aimed. See
      `COMPLETION-NOTE.md` §5. **Fan-in 2026-08-07:** director review ACCEPTED all four
      dossiers + `_raw/` audit trail; S2a-amendment check = NO amendment forced now — the
      ESTIMAND items (E1–E8, the aggregate-source swap) are deliberately carried by the
      "Population-statistics ingestion" NEXT item, whose slice owns the contract amendment
      the frozen registry requires)* **(parallel session R; launched after S1 completed — the
      session-R protocol it depends on is S1's deliverable)** — problem: architecture bet needs
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
- [x] **S4 — Batch sweep runner + counterfactual-config layer** — ✅ 2026-08-07. Shipped:
      one command (`sweep_runner`) delivering N configs → N seeded runs → N pinned scores;
      §c acceptance tests pass incl. canonicalization byte-safety; 10-config 50k smoke
      sweep complete with producer-rerun determinism check and 10/10 re-score
      byte-identity; measured capacity 404.7 configs/night loaded (program 2.58-3.03
      nights, hard cap 3.71 of 6 — §f escalation does NOT fire); S3 declared gaps closed
      (config_hash sentinel retired end-to-end with the rebuilt Σ_sim artifact
      cov-4a718ef1f6c30391, producer-rerun check, run_id collision); scores remained
      smoke-data-only throughout (stop-gate honored). — problem: no way to price N
      dial configs · outcome-link: reachability + all future tuning · pass/fail: one command:
      N configs (S2a schema) → N seeded runs → N scores, manifest-pinned (engine sha · seed ·
      config hash · scorer version · registry version); 10-config smoke batch reproduces
      byte-identical scores; one-config benchmark recorded against the S2a compute budget ·
      appetite: 2–3 days (re-costed 2026-08-07 at Gate 2: **4–6 days**, owner-approved as one
      slice — spec dual-review made the baseline covariance-artifact rebuild, the §f 5-worker
      parallel runner + raw-data retirement, and an ODCS minor-version window mandatory; see
      `docs/ai-dlc/ledger/flywheel-s4.md`) · no-gos: configs sweep the S2a-declared space only
      — no policy-code edits, no committed pack changes.

## S5 execution history (moved here 2026-08-13, unchanged in substance)

The S5 slice in the live roadmap now carries its outcome only. Its build-and-execution record
is kept here because it is finished work, and because two of its lessons outlive the study.

**Build (2026-08-09).** Tickets T0–T6 built; three dual-review rounds plus a verification pass
(33 findings, all adjudicated in `docs/ai-dlc/ledger/flywheel-s5.md`); merged as coach PR #179
and analytics PRs #16/#17. Final pins: frozen engine sha `a0de83e`, covariance artifact
`cov-525e183a12f269e3`, master seed 20260809, 2 export workers (chosen on a throughput
benchmark), 5 confirmation seeds (§g.4). A 17-run dry wave proved the pipeline end to end.

**Execution model (owner ruling 2026-08-09, rev 2).** All remaining waves ran from one
self-detecting local script, the same command every time: it reads on-disk markers, runs the
next unfinished persona wave end to end, then loops. `ONE=1` stops after a single wave. A
blocked wave does not end the night; only a mid-run engine-identity change, or a budget charge
of unknown status, stops it. **Restartable but not resumable** — a wave has no internal resume
point, so an interruption restarts it from its first config and clears the orphaned batch
directories first. Stage-1 counts: tag 130, lag 130, nit 120, maniac 110, passive_fish 120,
calling_station 120 = 730 configs plus 6 determinism re-runs.

**Two lessons worth outliving the study:**

1. **Success inferred from file existence cannot distinguish a failed wave from a clean one.**
   The sweep runner writes its manifest on partial and crash paths too, and the constraint
   checker writes its output file and exits zero even when the run fails its rules. A wave that
   failed therefore looked identical to one that succeeded: charged, evidence deleted, marked
   complete. The rule that replaced it — read the recorded status fields, never a filename —
   was found by dual review at high effort (36 candidates, 22 verifiers, 3 refuted, 10 upheld
   and fixed) and verified against nine simulated failure paths. A happy-path dry run had
   passed six times and caught none of it.
2. **Three latent defects were found only by changing something adjacent:** a shared output
   root silently overwrote five of six sweep manifests; a `set -e` shell idiom aborted the
   script immediately after a completed sweep; and a checkout that was behind its remote made
   the script's first command fail.
