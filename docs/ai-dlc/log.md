# AI-Org log — poker-coach

## 2026-08-05 — bot-realism-flywheel roadmap authored + dual-reviewed (AWAITING OWNER GATE)
- Owner halted all persona-fix work after the re-measure; `/ai-org:roadmap` produced
  `roadmap/bot-realism-flywheel.md` (rev 2) + `prd/bot-realism-flywheel.md` (rev 2).
  Dual review: refuter NEEDS-WORK, Codex Sol FAIL → all findings adjudicated + folded
  (`ledger/bot-realism-flywheel-roadmap-review.md`). persona-realism.md PAUSED (banner);
  profile `active:` → bot-realism-flywheel. Governing docs committed per owner ruling
  (branch `chore/flywheel-governing-docs`). Next action on owner approval: `/ai-org:spec S1`.
- Pre-compaction hardening pass (owner-approved): CLAUDE.md re-routed + boot checklist +
  misalignment tripwires; START-HERE.md orientation; supersession banners on all 7 remeasure
  reports; memory corrections; poker-analytics `docs/FLYWHEEL-STATUS.md` reconciliation
  (tickets adjudicated: keep T1–T5/T10/T11, re-scope T7/T8, remove T6/T9, park N1 + pitch).

## 2026-08-05 — realism re-measure DELIVERED (roster 4.2 → 4.8/10)
- 1,228 owner-played hands (post-#168 engine) + 50k seeded self-play sim; pre-registered
  protocol; 7 Opus assessors + 4 Codex Sol adversarial reviews + director verification.
  Blind identification 56/56 (identity layer fixed); remaining defect families: calldown
  looseness · raise-merit blindness · context-blind determinisms · sizing ecology · engine
  capability gaps (stacks re-rolled ~U(95,105) every hand — heater dynamics impossible).
  Authoritative rollup: `research/persona-realism-artifacts/remeasure-2026-08-05/SYNTHESIS.md`
  (§1 adjudicated scores; the 7 reports carry correction banners). Sol-A forced 6 measurement
  definition fixes in `stage0.py` — corrected stats match independent recomputes exactly.

## 2026-07-29 — T-ANCHOR built, triple-reviewed, shipped → PR #131 (Wave A wave 2 complete pending merge)
- /ai-org:spec re-entry: existing owner-approved spec/ticket verified current at HEAD 407a37e (line anchors exact; broken ratios reproduce to the digit); owner gate → build approved. One Opus heavy-worker, ran alone (sole fixture re-recorder), branch `feat/persona-realism-wave-a-w2` off main.
- Fix verified by all three fan-in reviewers (refuter + theory reviewer PASS on the fix; Sol clean on it too): pos_mult hoisted BET-gated, multiplied pre-complement on the bluff path, exactly once per path; IP/OOP ratio == authored to 1e-9 all six personas; `_PRE_M3_FIRES` re-pinned (authorized); coverage_baseline byte-identical (336/1215).
- Stop-the-line fired correctly: fix legitimately flipped the weak aggregate-AF C30 test (refuter A/B proved causation: old +0.164 / new −0.060 at n=1000). Owner decision: redesign now, spot-level. Worker died on 4× API-529 → Director built the redesign; Sol round-2 caught two real holes (plumbing leg couldn't isolate facing_raise; constant-referencing expectations launderable) → damp-differential leg + literal pins; damp-deletion now fails the test (verified by execution).
- Ledger: `ledger/persona-realism-wave-a-w2.md` (2 passes). Forward-filed: estimator air-cell position-parity note (metric-#5/W4); air-cell texture-blindness datum (F3/F16). Final: 1116 passed / 1 skipped, ruff clean, BACKEND VERIFY OK, zero band edits. Next: T-STICKY (wave 3) on the w2 tip after #131 merges.

## 2026-07-29 — R10 roadmap APPROVED at the gate (owner: "go")
- Roadmap + preflop-lane proposal approved as written. Build unblocked in R9-4/R10-8 order: T-ANCHOR → T-STICKY → preflop lane (R10-COUNT→PRE1→PRE2→W5-b4→R10-3BET) ∥ R9-DEFENCE+R10-TAIL design passes → fitting waves.

## 2026-07-29 — R10 roadmap correction pass written + triple-reviewed (awaiting owner gate)
- Deep re-derivation of persona-realism.md vs the 756-hand evidence: R10-1..R10-8 findings section (headline: preflop archetype collapse — EP first-in maniac 18.3% tightest of four; maniac authored below LAG every seat + premium fold 0.15–0.30; nit 29.1% wildcard), 5 restructured lane items (R10-COUNT/PRE1/PRE2/W5-b4/R10-3BET), R10-TAIL design item, R9-4 order upheld, preflop lane proposed after T-STICKY.
- Triple review (Sol guardrail + Sol plan-challenge + Claude refuter): 22 findings incl. 5 blockers — all adjudicated with Director re-verification (2 gates passed-at-HEAD caught; station elasticity 0.55 stale-citation caught; lane boundary revised), 1 partial rejection recorded (definitional ordering justification). Ledger pass 3.
- Quant layer: Wilson CIs on all cited rates; pairwise z-tests; authored pack ladders computed; EP/MP/LATE stratification. Gate presented to owner — HARD STOP, no slice work until approval.

## 2026-07-29 — persona-hand-review CLOSED: both reports delivered
- Wave 3: 2 Opus audits (AB-1..27: 3 blockers incl. lane-6 UNRELIABLE; AH-1..21: 0 blockers) → Director adjudication + ledger → 2 reports drafted → blind Opus cross-check (CC-1..34, both SHIP-WITH-FIXES) → all fixes applied → FINAL: `playstyle-research/report-bot-realism.md` + `report-hero-play.md`.
- Bot headline (triple-derived): four positional personas raise first-in 23.1–31.0% (one preflop bot); call-down claim confirmed (station tail 30/104 air-class; formal 1/229); draw-fear 76.8% barrel-through, partially confirmed; fish value-light raises ≈28 hard failures; nit folds to 3-bets 20/20.
- Hero headline: zero app-verdict overturns; 44 fresh mistakes in the app's 470-decision blind zone (4–8× covered error rate); leaks = under-stealing (10×), big-pair limps, river over-bluffing (9/24). Director report: `reports/persona-hand-review--director-report.md`.

## 2026-07-28 — persona-hand-review launched (gated plan approved w/ owner amendments) + waves 1–2 complete
- Owner amendments: graders = Codex Sol high (not Sonnet); Sonnet only for hero-preflop lane; cross-checker = Opus (cross-family flips since Codex authors).
- Wave 1: 8 Codex lanes graded all 756 hands → ~104 §5a failures (maniac 66 — mostly unopened premium folds incl. AK/JJ; fish 24; station/tag 3 each; nit 0) + ~305 policy deviations. Wave 2: draw-fear lane (76.8% barrel-through on completed draws, claim PARTIALLY CONFIRMED), call-down lane (1/229 formal §5a; station tail 30/104 air/ace-high), 3 hero lanes (app verdicts all confirmed; 7 fresh mistakes found in app's unmappable blind spot).
- Wave 3a running: 2 Opus adversarial auditors (bot lanes / hero+themed). Artifacts: playstyle-research/lane-reports/, stats_756.txt, spot extracts.

## 2026-07-28 — 500-hand review PREWORK complete (review itself NOT started)
- Spot-checks of Opus reviewer's dossier quotes: CONFIRMED both (station 60%-fold = fish sample; TAG Hand2Note AF 1.6/3bet 13%).
- 500 hands located: DB session 8c04aa55..., all complete, full hole cards + action history; tested exporter `playstyle-research/export_hands.py`; roster seat0 HERO + 8 bots. Session P/L: maniac/station +1200bb each, TAGs −500/−1000.
- Cold-start handoff written: `playstyle-research/REVIEW-HANDOFF.md` (data map, reading order, established conclusions, method, gates).

## 2026-07-28 — rubrics hardened (Opus review pass 2 → all 28 findings fixed); 500-hand analysis still NOT started
- Opus refuter (owner-directed): 3 blockers (baseline thin-value math, fish WTSD red-flag relapse, station wearing fish's elasticity) + 25 more; ALL accepted (1 modified: RES-E size ladder) → 4-agent apply wave → Director fan-in caught 3 brief-induced copy errors + re-sorted tag 5a/5b.
- New shared `rubrics/grading-protocol.md` (two-layer arrival/policy method, precedence ladder, limped-pot/BvB/check-raise/river-raise norms). Set = 8 files, 1186 lines, verification greps clean.

## 2026-07-28 — grading rubrics built (prep for 500-hand analysis; analysis NOT started)
- 4 sonnet agents (ungated wave): 6 persona rubrics + baseline-good-play reference → `research/persona-realism-artifacts/playstyle-research/rubrics/` (990 lines total), refuter caveats baked in, claims tagged [S]/[C]/[M].
- Director fan-in: fixed passive_fish rubric mislabeling dossier WTSD 20–28 as a contract anchor (contract says 33–42; engine pinned 50–57) — recorded as three-way disagreement. All other attributions verified correct.

## 2026-07-28 — persona-playstyle-research CLOSED (full Director report)
- 6 sealed Codex dossiers + 2 engine extractions + 3 refuter passes (32 ledger findings, all dossiers SOUND-WITH-FINDINGS) → `reports/persona-playstyle-research--findings.md`.
- Verdict: architecture right, numbers wrong 4 ways — tight trio opens ~2× too loose, everyone folds 84–99% to 3-bets, maniac tighter than LAG + folds AA unopened, WTSD ~2× research for station/fish.
- Director refuted one extraction claim by execution (check-raise IS reachable). 500-hand analysis still awaiting owner command.

## 2026-07-28 — persona-playstyle-research launched (gated plan approved)
- 6 sealed Codex Sol (high, web search) lanes — one per persona, 20-item template, blind to implementation, low-stakes live+online anchor.
- Wave A: 2 Claude sonnet engine-extraction agents (preflop packs / postflop merit engine) concurrent with Wave B.
- Plan: plans/persona-playstyle-research.md (approved). Review: Tier 2, 3 Claude refuters after Wave B. 500-hand analysis explicitly deferred to owner command.

## 2026-08-06 — S3 Gate 2 APPROVED (build phase starts)
Owner: go @ 5–7d appetite (roadmap 3–4d stale, sync rides T1) · floor = HARD §a.5 constraint
· no Fable · Terra pilot skipped (<10 candidates) · owner to widen sandbox: allowWrite +=
poker-analytics path, allowedDomains += bluffaces.com, then restart. Wave 1: T2 spawned
(implementer/sonnet, poker-coach-only scope; canonical ODCS deferred to post-restart).
T1/T3 blocked on sandbox widening. Plan ungated per GATE.md (≤1 Opus/wave, no foreman).

## 2026-08-06 — S3 wave 1 launched (T1, T3, T2-respawn)
Sandbox widened (owner ran patch from real terminal — settings.json applies LIVE, no
restart needed): bluffaces.com allowlisted (HTTP 200 verified), poker-analytics writable.
T1 heavy-worker/opus (amendment+registry, wt-s3-t1) · T3 implementer/sonnet (gate
param, wt-s3-t3) · T2 respawn implementer/sonnet continuing wt-s3-t2 partial (+86-line
export edit survived first restart, uncommitted). Ungated per GATE.md (1 opus, 3 workers).

## 2026-08-06 — T3 done (worker report); refuter spawned
T3 gate parameterized: --dir/--server optional w/ sample defaults; layer-3 datacontract
runs on scratch ODCS copy w/ rewritten server path; _GATE_OK.json marker (dynamic check
count, parquet sha256); negative + stale-marker tests pass. Commit 04e102a on
feat/flywheel-s3-t3-gate (wt-s3-t3). Followups: _GATE_OK.json gitignore (unowned),
T4 must verify marker hash not just presence, sim50k re-run owed at fan-in.
Refuter (sonnet/high) reviewing T3 now, pipelined while T1/T2 run.

## 2026-08-06 — T3 review adjudicated: NEEDS-WORK, 2 accepted
Refuter confirmed HIGH (fail() w/o batch arg in _SUCCESS-missing branch → stale
_GATE_OK.json survives tamper; reproduced) + MED (_GATE_OK.json not gitignored, dirties
tree). Both sent back to T3 worker (ownership +1 line: .gitignore). Deferred LOWs:
'150 checks' doc strings → T8 cleanup; marker-hash reverification → T4 brief.
Verified reviewer left worktree clean. Rest verified sound (3-model binding, dynamic
count, hash sensitivity, failure modes).

## 2026-08-06 — T3 ACCEPTED (post-rework, director spot-check)
Worker fixed both findings (2 of 12 fail() sites lacked batch arg; data/**/_GATE_OK.json
gitignore). Director re-ran stale-marker scenario in fresh process w/ repo venv:
pass→rm _SUCCESS→fail+marker-removed. Confirmed. Branch feat/flywheel-s3-t3-gate @
4c68b29 (not pushed). Owed at fan-in: gate re-run on regenerated sim50k.

## 2026-08-06 — T1 done (worker report); dual review spawned
T1 delivered: §g.1 amendment (10 subsections, ~684–1041) + registry-v2.json (40-cell
GGPoker snapshot, sha256 8d05aec6…, 7 compatible stats, NL25 9-max-ante of record) +
roadmap/PRD sync. Commit 0cd2a5b on feat/flywheel-s3-t1-amendment (based on
origin/main 56414cf). Worker flags for review/owner: (1) persona floor PERMISSIVE
(mapping σ dominates; may not honor floor=gate intent), (2) targets collapse to 2
distinct vectors, PFR separation 0, (3) anti-leakage ordering deviation (§e.1 read
before authoring; closed-form mitigation), (4) pool target swaps material. Dual review
spawned: refuter/opus + Codex Sol/high (both git-read-only).

## 2026-08-06 — T2 done (worker report); refuter spawned
T2 complete: prior partial kept (audited line-by-line), engine_node_key (preflop facing
labels export-side; postflop reuses domain postflop_node_key read-only; posts NULL) +
hand_class_bucket (preflop 5 buckets; postflop NULL — no clean domain label, documented
gap) · vendored ODCS 1.0.0→1.1.0 · canonical patch at docs/ai-dlc/reports/
t2-canonical-odcs.patch · 6 batches regenerated (39M, /private/tmp/claude-501/
t2-scratch-out) 418–431 h/s · 1432 tests pass · domain/content diff empty. Commit
820abb0 (4 files, verified clean). Refuter (sonnet/high) attacking incl. data-level
checks + determinism-context viability + postflop-NULL-bucket acceptability.

## 2026-08-06 — T1 dual review adjudicated: 14 findings → rework
Codex Sol FAIL (4H/3M) + Claude Opus NEEDS-WORK (3H/8M/5L). Convergent: floor
arithmetically vacuous on informative coordinates (only PFR/3bet can bind — the 0-sep
coords); source contradiction (recreationals def VPIP>45 vs published 35–38 —
load-bearing for fish f_p); uncited VPIP intervals (one unverifiable link; adverse-
direction mitigation verified); anti-leakage insufficient for confirmatory label.
Claude-unique: F1 remedy predictably counterproductive (raises S_p of lowest-rated
personas); delta table understates σ changes + mixed σ_target semantics; PRD n=13/
sign-agreement contradiction; missing §a.5 stub markers (T5 hazard). Arithmetic layer:
0 mismatches both reviewers; Codex refetched live, 21/21 matched. Rework sent to T1
worker (disclosure + mechanical; registry re-hash). OWNER decisions deferred to PR:
(1) floor σ redesign vs gross-departure gate, (2) confirmatory vs retrospective vs new
blinded ratings, (3) source trust despite internal contradiction.

## 2026-08-06 — T2 review adjudicated: 3H accepted → rework
Refuter NEEDS-WORK. H1: postflop hand_class_bucket NULL justified by FALSE claim —
domain strength_bucket() (personas_postflop.py:198) is pure + reusable; fix = populate
postflop via read-only reuse. H2: batches exported pre-commit → manifests stamp parent
sha 529b582; fix = regenerate from clean tree. H3: DEFAULT_LINEUP used instead of S1's
pinned 3×tag/2×fish lineup → run_id collides with reference dataset holding different
data; ruling = regenerate w/ pinned lineup, run_id format unchanged (disclosed wart).
L: throughput → committed t2-export-report.md. Fable-trailer flag adjudicated no-action
(harness signature). Clean: facing labels, invariants, purity, patch byte-identity,
determinism contexts. Expected: exact match to S1 pinned per-persona counts on regen.

## 2026-08-06 — OWNER RULINGS (4) on T1 open questions + T2 accepted
Owner ruled: (1) DELETE the executable per-persona floor gate (was §a.5 rule 6 / spec
A1.2) — floor demoted to non-gating diagnostic at most; avg(S_p) remains the per-persona
progress metric. Supersedes the morning floor=gate ruling. (2) §e validation pre-labeled
RETROSPECTIVE face-validity (not confirmatory). (3) GGPoker source: use + disclose
(contradiction + sensitivity recorded). (4) Mapping VPIP intervals: frozen as declared
constants w/ research-band discrepancy tabled. Director adjudication: §e.3 doubling
subset stays frozen at 3 rows (rationale disclosed). T1 → rev 3 fold.
T2 rework ACCEPTED: postflop bucket via domain strength_bucket read-only ('str|draw'),
pinned lineup regen, manifests git_sha=23aa44e, per-persona counts EXACT match to S1
pinned (zero drift — determinism confirmed). HEAD 05a8857. Remaining: authoritative
datacontract run (director integration check) + canonical patch application.

## 2026-08-07 — Wave-1 integration check PASS
Canonical ODCS patch (T2) applied to scratch copy of T3 gate tree; parameterized gate
run on regenerated sim50k_seed20260805: 156/156 datacontract checks pass (150→156 =
the 6 new-column checks), _GATE_OK.json written, contract_version 1.1.0, parquet
sha256 25f26a6a…. T1+T2+T3 verified working together. Awaiting T1 rev 3 (ruling fold)
+ T6 spike; T4 launches on T1 rev 3.

## 2026-08-07 — T6 spike: FEASIBLE (best case, no owner decision needed)
July/campaign-1 engine commit 1f9e799 (pinned from 250-hand-review's own provenance
table; 181-review's 1652e3d disclosed as considered) exports cleanly: zero adaptations,
zero degraded columns, isolation proven via app.__path__, smoke 1000 + scale 10k pass
(~417 h/s → 50k×5 ≈ 10 min). Recipe + patch (sha256 0d5f624e…) at docs/ai-dlc/reports/
t6-july-spike.{md,patch} (uncommitted). Followup for T7 execution: pin pyarrow version
(July pyproject didn't). One-campaign fallback amendment NOT needed.

## 2026-08-07 — T1 rev 3 in: WAVE 1 COMPLETE. T4 launching
Rev 3 commit f724e72: floor-gate deletion swept through every site (grep-verified —
five §a.5 rules, c_p demoted to yardstick, persona-gate λ-flip clause removed);
retrospective vocabulary pinned (§g.1.7 enumerates permitted statuses, confirmatory
excluded); source dissent recorded as considered-and-overruled; intervals frozen +
§e.3 3-row director adjudication; §g.1.10 now a ruled table. Registry untouched
(c56aac32… unchanged). Roadmap/PRD synced. T4 (heavy-worker/opus): worktree from T1
tip + merge T3 gate + apply T2 canonical patch, then scorer.

## 2026-08-07 — T4 done: scorer works end-to-end. 2 integration defects to fix
Scorer 0.71s/50k, byte-identical canonical (36aa8314…), 4 refusals fire, 41 tests.
First numbers (unvalidated): pool D=9.75 vs c=5.16; S_p avg −11.54, floor maniac
−18.27; λ stable no flip; maniac driven by PFR/3bet I_s exactly as §g.1.3 predicted.
Commits eaf2156 (T3 merge) 59a8091 (ODCS 1.1.0 canonical) 7a0cf5f (scorer) on
feat/flywheel-s3-t4-scorer. DEFECTS: (1) §g.1.8 + registry seat_exposure describe
DEFAULT_LINEUP (station/lag/maniac ×2) but ratified lineup = tag×3/fish×2 — bias
direction inverted; T1 fix + re-hash + scorer pin update owed. (2) committed sample
batch at ODCS 1.0.0 fails post-1.1.0 default validate — director regenerates.
Judgment calls for review: AF postflop scope, fold-to-c-bet HU scope, unittest not
pytest, config_hash sentinel.

## 2026-08-07 — Integration defect 2 fixed (director): sample fixture at 1.1.0
Regenerated seed-42/5k sample with T2 tool (worktree code proven via __file__),
swapped into t4 branch, default make validate green 156/156, committed e9c0c85.
Row counts differ from 1.0.0 fixture (engine evolved since 08-02) — honest re-stamp.
Awaiting T1 §g.1.8 lineup correction → director merges + updates scorer registry pin
→ T5 launch.

## 2026-08-07 — T1 rev 4 merged; scorer re-pinned; T5 launched
Rev 4 (6993c15): §g.1.8 corrected to ratified lineup (tag×3/fish×2), bias direction
re-derived (stricter on TAG+fish; nit alone holds both leniencies), registry hash
c56aac32→b7d59eff (only exposure fields moved, leaf-diff verified). Director: merged
into t4 branch (cc290a8), scorer pin updated (c73f6ab), tests OK, byte-identity holds
(canonical 8be98461), pool D unchanged 9.74566. T5 (implementer/sonnet) launched on
c73f6ab: five §a.5 checkers, no rule 6, floor passthrough informational only.

## 2026-08-07 — T5 done: five checkers green on both batches
constraints.py + 19 tests (60 total green). Real-data verdicts: a5_pass=true both
batches; determinism 8.8%/8.65% deterministic contexts (≤20%); AA/KK open-fold 0;
throughput 413/403 h/s. Ambiguities resolved-and-documented: rule-1 baseline derived
once from sim50k_seed20260805 → frozen artifact a5_baseline_z.json; rule-5 throughput
from producer times.txt. Commit 680a08f on feat/flywheel-s3-t5-constraints. T7 next.

## 2026-08-07 — T7 done: VALIDATION FAILED, STOP-GATE FIRED (as preregistered)
All legs FAIL under F0 AND F1, all with NEGATIVE sign (ρ=−0.204 F0, −0.377 F1 — F1
made it worse exactly as §g.1.6 pre-derived). Exact p's 0.57/0.73 (F0), 0.30/0.36 (F1);
LOPO all below 0.60 floor; BCa CI [−0.93,+0.45]. Status = exploratory-surrogate for
both triples; retrospective-fail labels; §e.3 spent (no F2); S5 may not issue
score-only verdicts; S4 smoke-data only. July campaign generated per T6 recipe
(1f9e799, 6×50k, all gated 156/156, campaign-1 Σ_sim cov-0a5f7be9). Commits 9d5a1a8/
63e4363/73b4ce3 on feat/flywheel-s3-t7-validation. Slice-level verify-by still PASSES
(deliverable was: validation executed w/ stop-gate honored + status recorded).
T8 fan-in: dual review of T4+T5+T7 spawning (refuter/opus + Codex Sol/high).

## 2026-08-07 — Codex Sol final review: NEGATIVE RESULT CONFIRMED REAL; NEEDS-WORK 2H/4M/2L
All recomputations matched (ρ to 1e-10, 720 perms re-enumerated, τ-b/LOPO/BCa, Σ full
inverse, denominators <5e-7, F1 rebuild = exactly 25 rows doubled, alignment row-by-row,
status lookup). Defects (none change current verdicts): H1 scorer accepts wrong-campaign
cov artifact (no key-vs-batch check); H2 rule-3 uses unweighted 6-persona mean not
pooled counters; M rule-1 narrowed to 7 stats (contract ambiguity); M determinism
threshold roster-wide not per-persona; M reproducibility = same-batch rescore; M
throughput proxy substitution unauthorized; L min-p misreported 1/720; L stale 'open
position' text in registry. Awaiting Opus refuter, then joint adjudication.

## 2026-08-07 — Final dual review adjudicated; hardening round launched
Opus refuter: NEEDS-WORK, result REAL (18 recomputation classes, 0 mismatches; sign
negative WITHIN each campaign independently; July control proves checkers bite —
correctly fails rules 1+2 there). Combined 16 findings adjudicated, none change any
verdict. Director committed rev 5 (1c04afb): stale registry dissent text →
considered-and-overruled; hash b7d59eff→b83043ae; known-transient test failure
(status triple awaits re-key). NOTE: director violated no-pipe rule (make|tail masked
red test pre-commit) — caught immediately, failure was the expected transient.
Parallel hardening: fix/s3-scorer-hardening (cov-artifact key enforcement +
git_sha out of canonical) ∥ fix/s3-constraints-hardening (rule-3 pooled, rule-1
10-stat rebuild, per-persona determinism+ranges, no throughput proxy, July negative
control). Then T7 rerun re-keys status + regenerates artifacts. Deferred: M5 full
producer-rerun reproducibility → S4 declared gap (T2 exact-match cited as evidence).

## 2026-08-07 — Hardening merged (6bbefdf); final rerun worker launched
Scorer hardening c7c2b03 (wrong-campaign cov refusal demonstrated live; git_sha out of
canonical) + constraints hardening 40d3fd9 (all six fixes; August still 5/5 pass; July
control: rule-2 fails as expected, rule-1 now PASSES under 10-stat baseline —
discrepancy honestly recorded, plausible cause = added aggression stats) merged into
feat/flywheel-s3-t7-validation. 71 tests, only transient red. Rerun worker: CLI
guards, min-p realized floor, known-answer validation tests, full deterministic
re-derivation under rev-5 hash (numbers must match exactly), status re-key, report
regeneration, July control refresh.

## 2026-08-07 — S3 CLOSED (T8 fan-in complete)
Rerun dcb9349: 82/82 green, all leg numbers identical, status re-keyed, byte-identical.
Ledger flywheel-s3-build.md written · roadmap S3 [x] w/ outcome · memory updated ·
FLYWHEEL-STATUS updated (da91ff3) · docs commit bc39b7e on feat/flywheel-s3-docs
(based on origin/main e0a1441). FINAL TIPS awaiting owner push: poker-analytics
feat/flywheel-s3-t7-validation @ da91ff3 · poker-coach feat/flywheel-s3-t2-export @
05a8857 + feat/flywheel-s3-docs @ bc39b7e. Reminder: feat/s2b-research-wave @ 59184c8
still unpushed (pre-S3 debt).

## 2026-08-07 — PR #12 CI fix: sample regression pins re-pinned
CI validate failed on assert_sample_regression_pins — dbt test pinning the OLD seed-42
fixture's counts; fixture was deliberately regenerated (ODCS 1.1.0, engine 05a8857).
Reproduced CI locally via ThreadPool shim (sandbox blocks ProcessPoolExecutor
semaphores); re-pinned from rebuilt agg_persona_stats; 79/79 + semantic-verify green.
Commit on feat/flywheel-s3-t7-validation — owner pushes to update PR #12.

## 2026-08-07 — S3 MERGED. Slice fully closed.
PR #12 (analytics, tip 6aa40f5 w/ CI pin fix) + poker-coach #172 (export) + #173
(docs) all merged. Local poker-coach main ff'd 529b582→073c5da (identical-content
collision handling: untracked dupes removed, newer log.md preserved as tracked-mod).
PR-BODY files cleaned. poker-analytics local main ref stale (fetch flaky) — ff before
next work there. Next per roadmap: S4 sweep runner; then S6 detection pilot informs
the phase-3 ceiling decision (S3's negative validation = primary evidence).

## 2026-08-07 — S4 CLOSED (T7 fan-in complete)
Gate 2 approved the S4 spec after dual review (refuter + Codex Sol, both
NEEDS-WORK on the pre-review spec; 15 findings adjudicated) and a re-cost from
2-3 to 4-6 days, owner-approved as one slice — dual review made the baseline
covariance-artifact rebuild, the §f 5-worker parallel runner + raw-data
retirement, and an ODCS minor-version window mandatory. Wave 1 build
(config layer + analytics compat) surfaced W1-1: the ingestion gate windows
ODCS contract versions but the scorer gate still exact-matched, citing §g.1.7 —
**owner ruling amended §g.1.7** so score validity checks a same-major
minor-version window (batch minor ≤ contract minor) while the estimand-contract
citation stays exact (formula-identity-bearing); the rest of wave 1's findings
(config_hash format validation, dotted-path parse rule, probe-declaration
schema) were fixed in place. Wave structure: wave 1 (T1 config layer, T3
analytics compat) → wave 2 (T2 export identity) → wave 3 (T5 sweep runner,
including a small-sample SVD-degeneracy scare at n=300 sized and cleared at
n=3000) → waves 4-5 (T4 artifact rebuild at the S4 engine sha — real
config_hash, S3 sentinel retired — and T6 acceptance run). Headline acceptance
(T6, `docs/ai-dlc/reports/flywheel-s4-acceptance.md`): §c(i)-(iii) all PASS
(canonicalization byte-safety, CLI-boundary rejection, cross-process hash
stability); 10-config 50k smoke sweep complete, 10/10 distinct hashes,
producer-rerun determinism check passed, 10/10 re-score byte-identity; S3's
three declared gaps closed (config_hash sentinel, producer-rerun check, run_id
collision for the tested arm-set), lineup-absent-from-run_id remains a
disclosed wart. Wave-5 dual review caught **W5-1**, the important find: the
acceptance report's first-pass §E applied §f's ×5 worker factor to the
SERIAL unloaded per-run time, contradicted by the report's own loaded
measurement (per-worker efficiency 0.61 at 5-way load) — 1.7-2.3× optimistic.
Corrected primary figures: 404.7 configs/night measured end-to-end, program
2.58-3.03 nights, 1,500-run hard cap 3.71 nights (61.8% of the 6-night
threshold) — escalation verdict unaffected (does not fire), confirmed
independently by both reviewers. T7 committed the planning docs (spec,
tickets, contract, ledger) that lived uncommitted through the build, ticked
the roadmap, and applied §f's mechanical-revision update in poker-analytics
using the corrected W5-1 figures. Tips: poker-coach feat/flywheel-s4 @ 4f52353
(T7's parent); poker-analytics feat/flywheel-s4 @ c5604e8.

## 2026-08-07 — S2b CLOSED (director fan-in complete)

Owner picked S6 (detection pilot) as the next slice and S2b fan-in first.
Fan-in: session R's four dossiers + consumption map + `_raw/` audit trail
(already committed on feat/s2b-research-wave @ 59184c8, never pushed) reviewed
and ACCEPTED — they had passed a blind Codex Sol review (13 findings, all
accepted and folded) and the completion note documents five Lead corrections
against primary sources. S2a-amendment check: NO amendment forced — the
ESTIMAND consumption items (E1–E8, GGPoker-aggregate registry swap) are
carried by the "Population-statistics ingestion + target-registry upgrade"
NEXT item, whose future slice owns the contract amendment the frozen registry
requires. Integration re-based as a fresh branch feat/s2b-fanin off main
(the old branch's roadmap edit predated the S2a/S3/S4 outcome notes; its
NEXT-item re-scope was already on main verbatim) — research dir taken from
59184c8 unchanged, roadmap S2b box ticked with the fan-in record. S6 spec
starts on owner's /ai-org:spec.

## 2026-08-07 — S6 BUILT (detection-protocol pilot; awaiting owner execution)

Full slice in one session: spec (28 dual-review findings folded pre-build, three
owner-approved §d amendments declared up front), then five build waves with dual
review at every fan-in. Shipped on feat/flywheel-s6: --buyin-spread export flag
(live re-buy mirrored exactly, default path golden-pinned), leak-proof shared
renderer (canonical schema, fail-closed invariants, one-cent fix), deck builder
(40+40+control, blinding split enforced in the writer, focus seats phase-matched
to close a position-trajectory side channel), judge harness (5 stdlib vendor
adapters, verbatim §d.3 prompt + base-rate preamble, checkpoint/resume), and the
statistics module (control invalidation fail-closed, BA/AUC/d′, stratified
bootstrap, Kish n_eff incl. per-judge tables). Protocol deck built twice at
pinned master seed 20260807, byte-identical, 86/86 payloads leak-clean. Review
system earned its keep repeatedly: Codex caught the phase side channel and the
judge-harness never-sent-the-hands bug; acceptance caught the one-cent false
reject (which was also mislabeling a seat all-in in judge-facing text). Suite
1,886 green. Analytics side (feat/flywheel-s6-docs): §g.2 amendments recorded
pre-judging, write-up scaffold, status. Remaining: owner gathers 5 vendor keys,
runs control pre-screen then full judging per
specs/flywheel-s6-execution-checklist.md; write-up fills from analysis.json.
Ledger: ledger/flywheel-s6.md (all ~46 findings with dispositions).

## 2026-08-24 — slice-3 decisions executed (Lane A + Lane B); Lane C not authorized

`/ai-org:build` of `tickets/slice3-decisions-execution.md`, scoped by the owner to Lane A
and Lane B — chain 1 only (E1 → E2 → E3, all poker-coach). Chain 2, the poker-analytics
publication-readiness lane the spec calls Lane C, was not authorized and remains unbuilt.

Three serial waves, one worker each, a fresh reviewer at every fan-in, nothing committed
before its review. E1 (Opus) recorded the owner's six 2026-08-24 rulings in the theory
contract: amendment A9 withdrawing the 2026-08-19 per-bucket α ruling in favour of a
per-range bound, a cross-reference putting the commitment slope in re-anchor scope, the
bucket-aware fold lever parked at §4 row P8, the reduction-floor rule adopted as §11 item 16
in the binding-rule-plus-reviewer-check form, the §7 factor order corrected to match the
engine, and §9 ledger entry 18 indexing all six. E2 (Sonnet) deleted the three tests built on
the withdrawn rule, their narrator block and two orphaned helpers, and corrected the engine
comments — the engine file's syntax tree is identical before and after, which is a proof of
zero behaviour change rather than an assurance. E3 (Opus) wrote eleven dated adjudication
notes with genuinely distinct dispositions (parked / dissolved / deferred / closed / still
open), resolved the two documents still asserting the withdrawn rule, marked the roadmap's
statistics-ingestion NEXT item satisfied-2026-08-06 by registry v2 with four residuals as
disclosed limitations, and swept the tree.

Ten review findings, all accepted and fixed pre-commit (ledger:
`ledger/slice3-decisions-execution.md`). Two earned their keep. The first: E1 had folded an
unratified reading of amendment A6 into a paragraph headed as an owner ruling — it is now
split out under the file's own "not owner-ratified text" convention and awaits owner
confirmation. The second, and the reason the wave-3 reviewer was routed to Opus: the roadmap
was about to claim every target in the sister repository's registry is graded low-confidence,
and three of the fifty-two are not. Verified independently against `registry-v2.json` — 49
`LOW`, 3 `C-grade literature (unchanged)`. The condition was narrowed and a fourth residual
disclosed, so nobody closes that item believing the swap off literature bands was total.

Suite 2191 passed / 2 skipped / 6 xfailed → 2189 / 2 / 0, matching a figure written into the
worker's brief before it started. `BACKEND VERIFY OK`, ruff clean. Two items only the owner
can close: confirm or overrule the A6 reading, and correct §10.2 of the 2026-07-24 audit,
which is git-excluded and reachable only in the main checkout.
