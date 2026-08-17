# Ticket DAG — S5 T-probe (`continue_ref` mechanism probe)

status: DRAFT rev 2 (post-review), awaiting Gate 2 (owner).
Spec: `../specs/flywheel-s5-tprobe.md` · Review ledger: `../ledger/flywheel-s5-tprobe.md`

Five tickets. P0 blocks everything; P1 and P2 run in parallel after P0; P3 needs P1+P2;
P4 runs last, after the owner executes the waves. New simulation: 42 runs, ~45 minutes.

- [x] **P0 — Pin the materiality threshold, before anything else.** DONE 2026-08-10:
  threshold `0.054814`, with its five source replicates, its provenance and its stated
  direction of error, recorded in `../ledger/flywheel-s5-tprobe.md`. Compute the standard
  deviation of `D` across the five pinned baseline replicates and write it into the ledger
  with the artifact ids it came from, alongside the spec's statement of which direction its
  known weakness biases. This is what makes "no material improvement" a preregistered claim
  rather than a post-hoc one, so it must be recorded before any probe config exists.
  Done when: the number and its provenance are in the ledger. Owns: the ledger file.

- [x] **P1 — Probe config generator.** DONE 2026-08-10: `poker-analytics
  analysis/gen_probe_configs.py` + `analysis/tests/test_gen_probe_configs.py` (37 tests,
  green under both venvs). All 36 configs pass `counterfactual.load_config`; 36 distinct
  config hashes; no config authors both dials; a stripped `probe_declarations` entry is
  rejected with the frozen-anchor error; maniac's anchor reverts cleanly. Emit the 36 configs: per persona, the anchor (its
  best surviving stage-1 config with `postflop.call_looseness` **omitted** so it falls back
  to the shipped default, `continue_ref` untouched) plus five configs setting
  `postflop.continue_ref` to each grid level, each carrying the required
  `probe_declarations` entry. Anchors are read from the stage-1 join, never hand-copied.
  Done when: all 36 pass `counterfactual.load_config`; **no config authors both
  `continue_ref` and `call_looseness` for one persona**; a config with its
  `probe_declarations` stripped is rejected with the freeze-rationale error; and maniac's
  anchor is confirmed to revert cleanly (its pack inherits `stickiness`, which also feeds
  the raise-scaling numerator — report explicitly if it does not).
  Owns: a new generator module in poker-analytics `analysis/`, plus its tests.

- [x] **P2 — Six probe wave specs.** DONE 2026-08-10: all six load through the real
  `sweep_runner.load_spec` with 6 configs, one stage-1 seed, `workers: 2`, `n_hands: 50000`,
  the ratified lineup, the frozen covariance artifact and a per-persona `out_root`. One sweep-spec JSON per persona: that persona's six
  configs, that persona's stage-1 seed, the frozen covariance artifact, `workers: 2`, the
  ratified 9-seat lineup, and a per-persona `out_root` under `~/s5-waves/probes/<persona>`
  (the per-wave-folder rule from checklist §2 — a shared root silently destroys all but the
  last manifest). Done when: all six load through the real `load_spec` and their configs
  through `validate_configs`. Owns: the gitignored probe artifacts directory.

- [x] **P3 — Runner + checklist wiring.** DONE 2026-08-10: per-stage config counts, an
  unknown stage refused outright, the budget charge routed by stage, and raw-Parquet
  retention made a per-stage policy (probes keep it — the spec's constraints require it and
  the old code would have deleted it). Proven by a dry harness over stubbed probe waves:
  33 checks, nine scenarios, five of them failure paths, plus a no-regression check that a
  sweep-stage wave still charges `stage1` and still retires its raw data.
  **Build review 2026-08-11 (round 2, ledger): both reviewers FAILED it; 11 findings, 10
  accepted and 1 narrowed, all fixed before any run.** Two of them would have mattered on
  the night — an environment variable that could delete the probe's evidence, and a
  one-time bootstrap marker that would have killed the unattended run. Point the existing wave runner at the probe stage
  (`STAGE=probes`) with the probe personas and counts, and split the budget charge so config
  runs book to `probes` and dup arms to `rerun_checks`. The runner already handles budget
  gating, manifest-driven verification, behaviour-gate semantics, and blocked-wave rules —
  this is configuration plus one budget-routing change, not new logic. Done when: a dry
  harness run over stubbed probe waves completes and charges both stages correctly.
  Owns: the local runner copy + `../specs/flywheel-s5-execution-checklist.md`.

- [x] **P4 — Analysis + close-out.** DONE 2026-08-11. Six waves ran clean in 59 minutes;
  budget landed on exactly 800 of 1,500. Preregistered mapping returns row 3 named with
  `maniac`; no configuration came within 2.2 of the cutoff. Owner declined the range
  widening the row-3 trigger offers. Dual-reviewed (round 3 in the ledger): no verdict was
  broken, eight findings against the surrounding reasoning were all accepted, and the
  recommendation now rests on a seat-share argument the review supplied — `maniac` holds 17%
  of flops, so no dial value can carry the pooled statistic to the cutoff. The S5 ticket's
  mid-slice trigger is marked fired and resolved. Tabulate `D` against
  `continue_ref` level per persona against that persona's measured anchor; apply the spec's
  preregistered per-persona verdict mapping and its stated aggregate rule; record every
  result in the ledger; dual-review the conclusion. Done when: the probe's verdict rows are
  written and reviewed, and the S5 ticket's mid-slice trigger is marked resolved.
  Owns: the ledger + the S5 ticket file.

**Not in this DAG, by design:** widening any declared range, and any change under
`backend/`. If P4 lands on "the boundary binds", that is an owner decision on amending the
estimand contract, taken with the probe result in hand — not pre-authorized here. Changing
`backend/` at all would move the engine off the frozen study commit and end comparability
with the 730 stage-1 runs.
