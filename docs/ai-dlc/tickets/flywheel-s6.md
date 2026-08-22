# Ticket DAG — S6 detection-protocol pilot

status: approved (owner, 2026-08-07 — Gate 2 + build go-gate cleared; no Fable; re-cost
4–5 days approved; Terra pilot skipped, zero eligible candidates)

**SCOPE FROZEN 2026-08-09 (owner ruling).** Adding a clone-table-versus-varied-table
comparison to this pilot was considered and REJECTED. The engine's policy core is already
seat-keyed and CAN vary same-persona seats (`backend/app/domain/table/play.py:291,313`) —
the correction the roadmap made 2026-08-13 to an earlier, wrong claim here. What is missing
sits in the caller and config layer, not the engine: the export tools bind packs by persona
name (`backend/tools/export_analytics.py:329`), a seat has nowhere to persist a variant
identity, and the counterfactual override document is persona-keyed rather than seat-keyed.
Building that means editing tooling/config outside this pilot's scope, which the roadmap's
global no-gos freeze until the phase-3 gate. The question now sits with the phase-3 gate
item as a configuration/persistence gap — see `bot-realism-flywheel.md`'s NEXT entry
"Within-archetype variation." Do not re-open it here — if a later session proposes it again,
this paragraph is the answer.

**Phase-3 gate status (added, dated):** the phase-3 gate was decided 2026-08-15 (ruling A —
fix bots, one finale, play-test is the product verdict); this S6 pilot itself ran as a
protocol shakedown on 2026-08-14, terminated at the control pre-screen rather than completing
a measurement. See `bot-realism-flywheel.md`'s S6 entry for the full record.

Spec: `../specs/flywheel-s6.md` (rev 2). All tickets honor the spec's Design rules;
hotspots: none of the profile hotspot files are touched. `export_analytics.py` is
single-owner (T2). `detection_corpus.py` is single-owner (T4); the renderer lives in its
own module `detection_render.py` (T3) to keep one file = one owner.

- **T1 — Pin the degenerate control config (de-risk first).** Find a §c-validator-accepted
  counterfactual config producing near-deterministic bad play; if the registered axes
  can't, report that (it becomes a declared amendment + tiny bespoke generator decision —
  back to director, not improvised). Acceptance: config JSON committed to the spec's
  appendix + a 500-hand probe run showing degenerate behavior (e.g. >90% of decisions a
  single action class). Done-condition: probe script exits 0 printing the config hash +
  degeneracy stat. Owned: new `backend/tools/probe_control_config.py` (throwaway-quality
  OK, kept for provenance). Depends: none.

- **T2 — `--buyin-spread` flag + run identity.** Exact live re-buy semantics (integer
  cents U[9500,10500], nine draws in seat order, per-hand stream derived from the hand's
  rng seed mirroring `_rebuy_seats`); `-bspread-` run_id mode token; conditional manifest
  fields; default path canonically unchanged. Acceptance: conformance test vs
  `sim_session._rebuy_seats` semantics + default-path canonical-identity regression test
  (volatile fields excluded) + spread-run manifest test. Done-condition:
  `pytest backend/tests/test_buyin_spread.py` green. Owned:
  `backend/tools/export_analytics.py`, `backend/tests/test_buyin_spread.py`. Depends: none.

- **T3 — Canonical hand-record schema + shared renderer.** One module normalizing BOTH
  sources (DB `state_json` replay; export-run replay) into one schema, rendered by one
  code path. Revealed-board only; settlement-defined showdowns; local 1–30 hand keys;
  full STRIPS list; opaque-ID hooks. Golden cross-source fixtures (fold-outs, all-ins,
  side pots, no-showdown rivers, malformed inputs) asserting on exact outbound payload;
  automated leak checks as a reusable function. Acceptance: fixtures + leak-check tests
  green; a human-source and bot-source rendering of an equivalent hand differ only in
  play content. Done-condition: `pytest backend/tests/test_detection_render.py` green.
  Owned: `backend/tools/detection_render.py`, `backend/tests/test_detection_render.py`.
  Depends: T2 (final conformance uses a real spread sample; developable against default
  export meanwhile).

- **T4 — Corpus builder + blinding split.** Window enumeration/validation (fail-closed
  human rule, one read snapshot, re-pin `hand_no ≤ N`), exactly-40 seeded selection with
  candidates recorded, globally-disjoint bot windows + focus-seat scheme, control bundle
  (T1 config, spread treatment), master-seed domain-separated derivations, blinded
  presentation manifest vs secret unblinding manifest (harness-side schema rejects
  label-bearing files), payload hashes. Acceptance: unit tests for every rule + a dry
  build on a small fixture DB and export. Done-condition:
  `pytest backend/tests/test_detection_corpus.py` green. Owned:
  `backend/tools/detection_corpus.py`, `backend/tests/test_detection_corpus.py`.
  Depends: T1, T2, T3.

- **T5 — Judge harness.** stdlib-HTTPS vendor adapters ×5 + stub judge; credential/snapshot
  preflight; immutable launch manifest (requested vs resolved model IDs); §d.3 prompt
  verbatim + §A.2 base-rate preamble; strict no-coercion response schema, raw preserved,
  identical-prompt single retry, transport-vs-malformed distinction; atomic
  per-(bundle,judge) checkpoints, idempotent resume; per-judge seeded order + HUMAN-class
  duplicate with fresh opaque ID; schedule tests. Acceptance: stub-judge run over a
  fixture deck produces a valid judging manifest; resume-after-kill test; schedule
  determinism test. Done-condition: `pytest backend/tests/test_detection_judge.py` green.
  Owned: `backend/tools/detection_judge.py`, `backend/tests/test_detection_judge.py`.
  Depends: T4 (manifest schemas).

- **T6 — Analysis module.** Control invalidation first (usable-denominator, fail closed →
  diagnostics only); pinned BA/AUC/d′ formulas; <3-usable-judges exclusion; stratified
  bootstrap (B=10,000, 95% percentile, seeded, judge vectors fixed); Kish n_eff with all
  four registered uses + degenerate-case "unavailable"; per-judge tables,
  duplicate-consistency, completeness report. All from structured outputs. Acceptance:
  hand-computed fixture values match; invalidation and missing-response paths tested.
  Done-condition: `pytest backend/tests/test_detection_analysis.py` green. Owned:
  `backend/tools/detection_analysis.py`, `backend/tests/test_detection_analysis.py`.
  Depends: T5 (judging-manifest schema; developable against a hand-written fixture
  manifest in parallel once T4/T5 schemas are frozen).

- **T7 — Acceptance dry run + docs + amendments.** Full pipeline stub-judge dry run
  (6+6 + control + duplicates) with byte-identical seeded re-run; leak audit on the real
  deck (automated + one manual bundle per class); record §A.1–§A.3 amendments in
  `poker-analytics:docs/methods/estimand-contract.md` (bold, pre-judging);
  working-agreement ownership addendum (both repos); FLYWHEEL-STATUS entry; execution
  checklist for the owner (keys ×5, judging command, expected cost/volume ≈ 82
  presentations × 5 vendors). Acceptance: spec Verify-by items 1–5 all pass. Done-
  condition: `./scripts/verify.sh` green + dry-run script exits 0 twice with identical
  canonical outputs. Owned: docs in both repos + `backend/tools/run_s6_dryrun.sh` (or
  Python equivalent). Depends: all.

**Post-build execution step (not a ticket; owner-run):** live judging in a real terminal
(keys from env), then the pilot write-up `poker-analytics:docs/methods/detection-pilot-s6.md`
from the analysis output; roadmap S6 box ticked only after the write-up lands.

**Parallelism:** T1 ∥ T2 in wave 1; T3 after T2; T4 after T1+T3; T5, then T6 (T6 may start
against frozen schemas); T7 last. Maker ≠ checker at every fan-in per house rules.
