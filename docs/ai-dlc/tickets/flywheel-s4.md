# Tickets — S4: batch sweep runner + counterfactual-config layer

status: approved (Gate 2, owner 2026-08-07 — one slice, re-costed appetite 4–6 days)
spec: `docs/ai-dlc/specs/flywheel-s4.md` (rev 2) · findings: `docs/ai-dlc/ledger/flywheel-s4.md`
Global invariant every ticket inherits: `git diff backend/app/domain/ content/` EMPTY;
sweep configs/batches ephemeral; scores = smoke data only, stamped as such.

## DAG

```
T1 (config layer)  T2 (export identity)        T3 (analytics compat)
      \                 |            \               |
       \                |             ODCS patch →   |
        \               v                            v
         +---------→ T5 (sweep runner)        T4 (artifact rebuild, needs T2+T3)
                        \                        /
                         v                      v
                      T6 (acceptance + smoke + benchmark, needs ALL)
                              |
                              v
                      T7 (docs + bookkeeping)
```

Parallelizable: T1 ∥ T2 ∥ T3 (disjoint files, different repos for T3). T4 after
T2+T3. T5 after T1+T2. T6 after everything. T7 last.

## T1 — Counterfactual config layer (poker-coach)

Build `backend/tools/counterfactual.py`: §c validator (axis-table paths + bounds,
unknown-field/null rejection, `base_pack_hash` check, deterministic dotted-path
parse with greedy sizing-key match, frozen probe-declaration schema, continue_ref
co-sweep rejection), `exclude_unset` overlay merge + full re-validation via
`backend/app/domain/content/models.py`, §a.2 canonicalization, §c.6 canonical hash.
- Owns: `backend/tools/counterfactual.py`, `backend/tests/test_counterfactual.py`.
- Done when: the three §c worked-rejection examples fail with the stated errors;
  presence-preservation test green; hash stable across two subprocesses;
  empty-override == canonicalized baseline; `./scripts/verify.sh` + ruff green.

## T2 — Export identity + timing (poker-coach) — HOTSPOT single-owner

Modify `backend/tools/export_analytics.py`: `run_export(packs=)` (default path
simulates RAW packs; canonicalization = hash side-channel only), `_SUCCESS.config_hash`
always present, `run_id = run-s{seed}-n{n}-c{hash12}`, `_TIMING.json`
(`{schema_version, wall_seconds, n_hands, seed, run_id}`, written before `_SUCCESS`).
ODCS coach copy → 1.2.0 additive (+config_hash customProperty text, run_id
description, changelog); produce the byte-identical patch file for T3.
- Owns: `backend/tools/export_analytics.py`, `backend/tools/poker_events.odcs.yaml`,
  `backend/tests/test_export_analytics_schema.py`, patch file under
  `docs/ai-dlc/reports/`.
- Done when: schema test green at 1.2.0; a small export batch carries config_hash +
  new run_id + valid `_TIMING.json`; seed-42 fixture untouched; verify.sh + ruff green.

## T3 — Analytics-side compatibility (poker-analytics, own worktree off main)

Gate: minor-version window (same-major, batch-minor ≤ contract-minor) + optional
`config_hash` manifest key. Scorer: `producer_run.config_hash` (presence-
conditional), `validate_covariance_artifact` wave-wide rule (batch-vs-artifact
config_hash never compared; sentinel comment replaced). Covariance: thread real
config_hash from replicate manifests (one-real / all-absent-legacy / else refuse).
Apply T2's ODCS patch + changelog. CI: add `make scorer-test`.
- Owns (analytics): `ingest/validate.py`, `scorer/score_realism.py`,
  `scorer/covariance.py`, `contracts/poker_events.odcs.yaml`,
  `.github/workflows/ci.yml`, scorer tests.
- Done when: `make scorer-test` green incl. new version-window/threading/refusal
  tests; committed 1.1.0 sample still gates under the 1.2.0 contract; a pre-S4
  batch re-scores byte-identically (back-compat proof).

## T4 — Baseline covariance artifact rebuild (cross-repo; after T2+T3)

Export 5 replicate 50k baseline batches (ratified lineup, shared seed set) at the
S4 engine commit; `make covariance`; commit the artifact; re-pin
`DEFAULT_COVARIANCE_ARTIFACT`.
- Owns (analytics): `scorer/artifacts/` new artifact, the `DEFAULT_COVARIANCE_ARTIFACT`
  constant.
- Done when: artifact key carries the real baseline config_hash + S4 engine sha;
  `make score` on a fresh baseline batch succeeds with no `COV=` override.

## T5 — Sweep runner (poker-coach; after T1+T2)

Build `backend/tools/sweep_runner.py`: sweep-spec input, 5-worker bounded parallel
(threads → export subprocesses), per-run validate→export→gate→score
(`OUT=`/`COV=` always explicit, scores read from files), fail-closed partial
labeling, delete-raw-after-score + `--keep-raw`, producer-rerun check (one config
exported twice, parquet-minus-exported_at equality + masked-canonical equality),
`sweep_manifest.json` canonical/volatile split with authority stamp.
- Owns: `backend/tools/sweep_runner.py`, `backend/tests/test_sweep_manifest.py`.
- Done when: unit tests green (manifest determinism, partial labeling, stamp
  present); a 2-config mini-sweep runs end-to-end against T3's analytics branch.

## T6 — Acceptance run: §c tests + smoke sweep + benchmark (after ALL)

Execute acceptance 1(i)–(iii); 10-config smoke sweep at 50k hands/config (configs
drawn from the §a.2 space, ephemeral); re-score → byte-identical canonical
sections; one-config benchmark vs §f budget; apply §f's mechanical-revision numbers
(estimand contract — measured-benchmark update only, NOT a methods change; goes in
T7's docs commit if the contract file needs the §f number swap).
- Owns: acceptance/benchmark report `docs/ai-dlc/reports/flywheel-s4-acceptance.md`
  (+ ephemeral sweep outputs, uncommitted).
- Done when: all acceptance boxes in the spec check; report records numbers +
  score-status stamps; escalation clause explicitly evaluated (fires or not).

## T7 — Docs + bookkeeping (last)

Roadmap S4 box ticked with outcome; WORKING-AGREEMENT manifest-extension section
updated (shipped); FLYWHEEL-STATUS.md; poker-coach log.md entry; build ledger.
- Owns: the named docs files in both repos.
- Done when: docs match shipped reality; no doc cites the sentinel as current.
