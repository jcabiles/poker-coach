# Contracts — S5 (bot-realism reachability study)

Mapped 2026-08-08 by contract-mapper (read-only scan), persisted by director. Sources
verified against code at poker-coach main (post-#177) and poker-analytics main (post-#15).

## Sweep-runner interface (`backend/tools/sweep_runner.py`)

- **CLI:** `python -m tools.sweep_runner --spec sweep.json [--keep-raw] [--rerun-check-index N]`. Exit code nonzero unless `sweep_status == "complete"`.
- **Spec JSON (`load_spec`, sweep_runner.py:128-238):** required `schema_version` (strict semver), `configs` (non-empty list of counterfactual-config paths, resolved relative to the spec file), `seeds` (non-empty list of distinct ints), `n_hands` (positive int), `out_root` (parent must exist+be writable), `analytics_repo` (must be a dir containing a `Makefile`). `cov_artifact` is **required**, non-empty string — "always explicit OUT and COV, never the Makefile default" is enforced structurally. `lineup` optional (string or list of persona names), forwarded verbatim as `--lineup`.
- **Validation ordering (load-bearing for cost):** ALL configs validated via `counterfactual.load_config` up front, before ANY export runs — one bad config in a 100-config batch fails the whole sweep before simulation time is spent (sweep_runner.py:9-11, 241-261). Duplicate `config_hash` within one spec is a hard spec error.
- **Execution model:** Phase A = bounded 5-worker `ThreadPoolExecutor` shelling out to `python -m tools.export_analytics --config ... --skip-contract-test`; Phase B = serial `make validate` + `make score` per batch in the driver thread. **S5 must not add a second parallelism layer on top of the 5 export workers** — the throughput benchmark is keyed to this shape.
- **Determinism/identity cross-checks:** every run's `_SUCCESS` and score `producer_run` cross-checked against requested `(config_hash, seed, n_hands, run_id, lineup)`; mismatch fails that run closed (`_identity_mismatches`, sweep_runner.py:446-473). A designated `(config, seed)` arm is exported twice per sweep invocation to prove producer determinism — **every invocation costs N+1 exports, not N.**
- **Fail-closed:** any export/validate/score/identity failure marks that run `"failed"` (stderr captured) and the sweep continues. Manifest stamped `sweep_status: "partial"` unless every run AND the rerun check passed. **At 660–1,500-run scale some runs WILL fail — S5 must consume per-run `run_status`/`failed_step`, never treat a partial manifest as a wholesale failure to retry.**
- **Raw-data retirement:** Parquet deleted after successful score unless `--keep-raw`; rerun-check pair retained until the check passes. Manifest keeps `(seed, config_hash)` so any batch is reproducible on demand; ~50MB/batch if kept.
- **Manifest fields used downstream:** `canonical.runs[i]` carries `config_hash, seed, n_hands, run_id, run_status, engine_git_sha, scorer_version, registry_version, registry_sha256, stat_definition_version, score_canonical_sha256, score_status`. **`score_status` is per-run — read it per run, never assume a sweep-wide status.**
- **Ordering contract:** `build_items` is config-major, seed-minor (sweep_runner.py:281-292) — `--rerun-check-index` and any flat-index mapping must respect this.
- **Disclosed S4 wart:** `lineup` is absent from `run_id` (manifest-only), and the exporter's `DEFAULT_LINEUP` ≠ the ratified §a.6 lineup — **every sweep spec must pass `--lineup` explicitly or silently gets the wrong lineup.**

## Counterfactual-config layer (`backend/tools/counterfactual.py`)

- **Document shape:** `{schema_version, base_pack_hash, overrides: {persona: {dotted.path: number}}, probe_declarations: []}`. `base_pack_hash` must equal the hash of currently-loaded baseline packs — stale-checkout configs are refused.
- **Allowed override paths = exactly the §a.2 axis table** (12 scalar axes + axis-13 simplex weights), enforced via `resolve_path`/`_AXIS_BY_PATH` (counterfactual.py:133-147, 235-288). Anything else is rejected with a named-rule error. A typo'd path fails the WHOLE config validation.
- **Frozen fields require probe declarations:** `continue_ref` and `sizing_by_node` accepted only with a matching `{probe_kind, persona, paths, rationale}` entry. `continue_ref` may never be co-swept with `call_looseness` in the SAME config (axis-7 co-sweep refusal, counterfactual.py:619-625). **Mechanism probes cannot run through the plain sweep-config path — they need `probe_declarations` populated (config-generation path currently unbuilt).**
- **Per-persona axis restrictions:** axis 6 (`size_elasticity`) only for calling-station/passive-fish; axis 8 (`position_sensitivity`) only for nit/TAG/LAG. **Config generators must be persona-aware (d = 11–13 varies by persona); a uniform axis list is rejected outright.**
- **`rationale` prose is hash-bearing** (counterfactual.py:39-43): rewording a probe rationale mints a new `config_hash`. **Never edit a probe rationale mid-study.**
- **Canonicalization:** every config materializes `call_looseness` explicitly on every persona at baseline-effective value inside `validate_config`/`canonicalize`. Use `empty_override_config`/`load_config`; never a bespoke "no overrides" sentinel.
- **Purity invariant:** nothing under `content/` or `backend/app/domain/` is ever written; merges are in-memory deep copies re-validated through the engine's own `PersonaPack` model. **Winning configs stay ephemeral JSON — never committed into `content/personas/`.**

## Scorer interface (poker-analytics `scorer/score_realism.py` + `Makefile`)

- **Entry point:** `make score DIR=<batch> [OUT=<file>] [COV=<artifact id or path>]`. Batch must already carry a current `_GATE_OK.json` (`make validate` is a hard precondition).
- **Gate-first refusal chain (`scorer/gate.py`):** refuses without `_GATE_OK.json`; re-checks `parquet_sha256` against actual files; checks ODCS `contract_version` under the **same-major, batch-minor ≤ contract-minor window** (rev-5 ruling, §g.1.7) — not exact equality. Exports outside the window are refused at score time.
- **Covariance-artifact binding (`validate_covariance_artifact`, score_realism.py:150-195):** refuses on mismatch of `engine_git_sha`, `hand_count`, `lineup`, `scorer_version`, `stat_definition_version`. **`config_hash` is deliberately EXCLUDED** — Σ_sim is measured once from baseline replicates and reused wave-wide across swept configs BY DESIGN (§a.3). Stage-1/2 must pin ONE wave-wide artifact (currently `cov-4a718ef1f6c30391`); stage-3 confirmation needs a NEW config-specific artifact per finalist (`make covariance BATCHES=` exists generically; per-finalist scripting does not).
- **`score_status` resolution (score_realism.py:82-112, §g.1.7):** keyed to the exact triple `(formula_id="F0", registry_content_sha256, stat_definition_version)` against `analysis/validation-status.json`. Current triple resolves to `exploratory-surrogate`; any drift → `unvalidated`. **Reject a triple mismatch, never warn-and-proceed.**
- **Scorer canonical payload:** `contract` citation string (must EXACTLY equal `"estimand contract v2.3 as amended 2026-08-06-A"`; formula-identity-bearing, never reworded), `formula_id`, `scorer_version`, `score_status(/basis)`, `registry.*`, `odcs_contract_version`, `covariance_artifact.*`, `producer_run.*`, `gate.*`, `pool_tier` (D(x), cutoff, per-stat implausibilities, `distance_below_cutoff`), `persona_tier` (per-persona `D_p`/`S_p`, `avg_S_p`, `floor_S_p`/`floor_persona` — explicitly non-gating), `lambda_sensitivity` (λ∈{1.0,0.8,0.5,0.0}, `pool_verdict_flip`), `ordinal_shape_diagnostics`, `disclosures_that_must_travel`.
- **§a.5 constraint checkers (`scorer/constraints.py`, `make a5-check DIR= [OUT=] [COV=]`):** exactly the five surviving rules (label-preservation/separation, legality/absurdity, directional persona checks, determinism side-check, runtime/reproducibility). **The deleted per-persona floor gate must never be reconstructed as a gate** — `min(S_p)` is echoed as a non-gating `floor_diagnostic` only. Requires a one-time `--build-baseline` artifact (`a5_baseline_z.json`) from a designated baseline batch — **build/pin ONCE before the study; rebuilding per-candidate silently moves the z-scoring reference.**
- **NROY membership is an S5-level computation:** `D(x) < c` (pool_tier) AND all five a5 rules pass. **No existing tool computes this join.**

## Estimand-contract clauses binding S5

- **§a.4 (decision rule):** REACHABLE requires a stage-3 combination config that is NROY on its design evaluation AND remains NROY on ≥3 fresh confirmation seeds not used in selection (winner's-curse guard) with a config-specific re-estimated Σ_sim. NOT-REACHABLE requires: (i) design floor met every wave; (ii) stage-2 refinement wave still found nothing; (iii) sensitivity screening shows gap persists at declared axis bounds (mechanism probes at endpoints) OR no included axis has material leverage — if the SRRC screen is inadequate (R² < 0.3) that path collapses to INCONCLUSIVE, never NOT-REACHABLE; (iv) fresh-seed confirmation applied to the 10 closest-by-D configs, not only would-be winners.
- **§a.5:** five rules, no sixth. No per-persona `D_p < c_p` gate under any framing.
- **§a.6 (three-stage design):** stage 1 = per-persona screening, N ≥ 10×d LHD points, one persona varied at a time (others frozen at canonicalized baseline); d = 11–13 persona-dependent. SRRC is the pinned screening statistic (Morris/Sobol excluded); materiality `|SRRC| ≥ 0.10`; adequacy R² ≥ 0.3. Stage 2 = refinement LHD (≥5×d) on stage-1's top-decile box; required before any NOT-REACHABLE. Stage 3 = 20 roster-level combination configs (from per-persona top deciles, not argmax) → 10 lowest-D get ≥3-fresh-seed confirmation. **Common random numbers: one shared seed list per wave, never fresh seeds per config.**
- **§f (compute budget):** program floor ≈1,045–1,225 runs pre-probes; **hard cap 1,500 runs total** (exceeding triggers the emulator-fallback escalation clause, never silent growth). Authoritative capacity: **404.7 configs/night** (loaded 5-worker measured; the ×5-on-serial figure is a named, previously-fixed defect class — W5-1). 1,500 runs ≈ 3.71 nights; escalation threshold 6 nights.
- **§g.1.6:** validation-status vocabulary is `retrospective-pass`/`retrospective-fail`; `confirmatory` is never available for the existing rating campaigns. S5's write-up never calls the score "validated".
- **§g.1.7:** status keyed to the exact (formula, registry sha, statdef) triple; citation string exact-match; only the ODCS data-contract version gets window leniency.
- **Stop-gate carry-forward (§e.3):** score = exploratory-surrogate; **no score-only verdict** — REACHABLE/NOT-REACHABLE/INCONCLUSIVE needs convergent evidence (§a.5 pass + §a.4 sensitivity/mechanism analysis). No fix recommendations in the verdict (roadmap no-go).

## Compute / benchmark facts

- Reference platform: MacBook Air arm64, 8 cores/16GB; engine sha at artifact rebuild `e7c1b38`.
- One-config 50k-hand export: serial ≈121–126s; ingestion gate ≈2.4s; scorer ≈0.1–0.2s.
- **Loaded 5-worker throughput (T6, authoritative): 56.93s/config → 404.7 configs/night** (0.8 derating, 8h/night). Per-worker efficiency 0.61 at 5-way contention (true speedup ≈3.05×, not 5×).
- Program floor 1,045–1,225 runs ⇒ 2.58–3.03 nights; cap 1,500 ⇒ 3.71 nights; escalation at 6.
- Disk non-binding (~50MB/batch, deleted after score unless `--keep-raw`).
- N+1 exports per sweep invocation (mandatory rerun check).

## Integration risks

1. **Cost double-counting:** use 404.7 configs/night + N+1 rerun overhead; never re-derive ×5-serial (repeat of fixed defect W5-1).
2. **Covariance misuse:** per-config-rebuilt Σ_sim in stage 1/2 breaks §a.3 reuse and makes D(x) incomparable across a wave.
3. **Score-status drift:** any registry/statdef/formula bump flips scores to `unvalidated`; check `score_status` per manifest run.
4. **Partial-manifest consumption:** filter per-run `run_status`/`failed_step`; expect partials at scale.
5. **Persona-aware axis generation:** uniform axis sets are rejected (axes 6/8 persona-restricted).
6. **Mechanism-probe plumbing gap:** probe-bearing config generation path is unbuilt.
7. **No NROY/SRRC/LHD layer exists** — S5 builds the statistical join (score.json + a5.json → NROY; per-wave SRRC screening) from scratch.
8. **`lineup` omission from run_id:** pass `--lineup` explicitly on every spec.
9. **Stage-3 covariance bookkeeping unbuilt:** per-finalist `make covariance BATCHES=` invocation + artifact-id tracking needs scripting.
10. **Citation-string exactness:** never touch `CONTRACT_CITATION` in score_realism.py.

## Files read

- poker-coach: `backend/tools/sweep_runner.py`, `backend/tools/counterfactual.py`, `docs/ai-dlc/ledger/flywheel-s4.md`, `docs/ai-dlc/contracts/flywheel-s4.md`, `docs/ai-dlc/roadmap/bot-realism-flywheel.md` (lines 120–169)
- poker-analytics: `docs/methods/estimand-contract.md` (§a.1–a.6, §f, §g.1.6, §g.1.7), `Makefile`, `scorer/score_realism.py`, `scorer/gate.py`, `scorer/constraints.py`
