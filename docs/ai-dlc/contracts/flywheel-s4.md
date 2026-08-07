# Contracts — S4 batch sweep runner + counterfactual-config layer

Mapped 2026-08-07 by contract-mapper (read-only scan of poker-coach main @ 073c5da and
poker-analytics merged state @ wt-s3-t7 tip 6aa40f5). Slice: bot-realism-flywheel S4.

## 1. Export path (poker-coach `backend/tools/export_analytics.py`)

**CLI surface** (`export_analytics.py:327-343`): `--hands` (int, default 5000), `--seed` (int, default 42), `--out` (required `Path`), `--skip-contract-test` (flag), `--lineup` (comma-separated persona names, default = `DEFAULT_LINEUP`, sorted 6-persona list wrapped to 9 seats, `:71,245-246`).

**Output**: three Parquet tables (`hands.parquet`, `seat_outcomes.parquet`, `decisions.parquet`, zstd-compressed) plus a JSON `_SUCCESS` manifest written LAST (`:268-293`). Manifest fields: `run_id, seed, n_hands, lineup, stacks_bb, git_sha, engine, generator, contract_version (="1.1.0"), schema_path_version (="v1"), exported_at, row_counts`.

- CONTRACT: `_SUCCESS` is written last as a Hadoop-manifest-committer convention — every consumer (gate.py:82-84, WORKING-AGREEMENT §2) treats its absence as "batch incomplete/never scored." Any S4 batch-writer that doesn't preserve write-order-last breaks the whole pipeline's completeness signal.

**No runtime dial/config input exists today.** Persona behavior is entirely determined by `load_persona_packs()` (`export_analytics.py:56,247`) reading `content/personas/*.json` (`backend/app/domain/personas.py:40-53`) — no CLI flag, env var, or override mechanism touches lever values; `--lineup` only selects *which* named packs occupy which seats, never their numeric levers.

- CONTRACT: dial values live exclusively in `content/personas/{nit,tag,lag,maniac,calling_station,passive_fish}.json`, validated by the pydantic model in `backend/app/domain/content/models.py` (`PersonaPack`/`PersonaPostflop`, `:147-332`) — the same model the engine loads at play time. **Both `backend/app/domain/` and `content/` must stay diff-clean per the flywheel no-go** (roadmap `:230-232`). A runtime overlay must NOT write these files or import a mutated copy in their place.
- **How a runtime overlay must enter (per estimand contract §c, `estimand-contract.md:415-462`):** S4's counterfactual-config schema is an *ephemeral* JSON document (`schema_version`, `base_pack_hash`, `overrides: {persona: {dotted.path: number}}`, `probe_declarations`) that must be **merged onto a deep copy of the base pack in memory, then re-validated from scratch through the SAME pydantic model** (`estimand-contract.md:444-446`, "never in-place attribute update — documented to bypass validation"). S4's export invocation must load baseline packs, apply the override dict, re-serialize/re-validate, and feed the *in-memory* pack objects into `play_one_hand`/`run_export` — never touch the files on disk. `run_export()` (`:240-294`) currently has no parameter for an alternate `packs` dict; **adding one is the load-bearing surface change S4 needs** (hotspot file).

## 2. The S2a-declared config space — where it is, and what it is

It exists, in full, as **`docs/methods/estimand-contract.md` §a.2 and §c** (poker-analytics, `wt-s3-t7 …/estimand-contract.md:86-462`), pinned as v2.3 and amended once (§g.1; §a.2/§c unchanged per its banner `:6-9`).

- **§a.2** (`:86-148`) declares 13 numeric axis families per persona (sizing.open_bb, threebet_mult, fourbet_mult, postflop.aggression, call_looseness, size_elasticity [station/fish only], continue_ref [frozen, probe-only], position_sensitivity [nit/TAG/LAG only], line_sensitivity, bluff_freq, spr_commit, multiway_bluff_damp, and the `postflop.sizing` truncated-simplex weights) with explicit bounds, DoF counts (d = 11–13/persona), and named exclusions (`sizing_by_node`, `stickiness`, preflop mix tables, engine constants, structural key sets).
- **§c** (`:415-462`) is the machine-checkable schema: `{schema_version, base_pack_hash, overrides: {persona: {dotted.path: number}}, probe_declarations}` — allowed paths = exactly §a.2's axis table; unknown fields rejected; `continue_ref`/`sizing_by_node` accepted only with a matching `probe_declarations` entry; explicit `null` forbidden; merge = deep-copy + set, then **full re-validation from serialized JSON**; canonical hash = sha256 of sorted-key, shortest-round-trip-float JSON bytes.

- CONTRACT: "S4's counterfactual configs are ephemeral by definition — never committed" (WORKING-AGREEMENT §8, `:104-105`; roadmap out-of-scope `:230-232`). Persisting a materialized pack JSON into `content/` (even as a disk cache) violates the frozen-content invariant.
- CONTRACT: **§c's acceptance test is explicitly S4's, stated but not executed** (`estimand-contract.md:459-462`): (i) `overrides: {}` on the canonicalized baseline must reproduce byte-identical scores vs raw baseline; (ii) all three worked-rejected examples must fail with the stated errors; (iii) canonical hash stable across two processes. No validator exists yet anywhere.
- CONTRACT: the **canonicalization rule** (`estimand-contract.md:142-148`) — every sweep config must materialize `call_looseness` explicitly, and S4's validator must *prove* byte-identical baseline scores for the canonicalized base config before any sweep runs. A second, distinct acceptance gate from the §c one.

## 3. poker-analytics scoring path (wt-s3-t7)

**Makefile targets** (`Makefile:37-87`): `make validate DIR=` (ingestion gate → `_GATE_OK.json`), `make score DIR= [OUT=] [COV=]` (refuses without current `_GATE_OK.json`), `make a5-check DIR=` (five §a.5 rules), `make covariance BATCHES="…"` (≥5 gated replicates of ONE config).

**`_GATE_OK.json` marker contract** (`scorer/gate.py:1-141`): two-layer refusal — (1) marker exists only after a fully-passing `ingest/validate.py` run (deleted on any failure); (2) marker's `parquet_sha256` is **recomputed** from on-disk Parquet via `ingest.validate.batch_content_hash` and must match (catches post-gate mutation). Plus: required manifest keys, per-table row counts vs `_SUCCESS`, `contract_version` equality with the checked-out ODCS contract, every decisions-seat present in `lineup`.

- CONTRACT: `require_gated()` is the single choke point (`score_realism.py:239`, `constraints.py:655,741,754`) — S4 batches must pass `make validate` before score/a5-check, per config, per seed.

**Registry pinning** (`scorer/registry.py:23-29,146-174`): `EXPECTED_REGISTRY_SHA256` = `b83043ae…01528c1d`, `EXPECTED_REGISTRY_VERSION="2.0.0"`, `EXPECTED_STAT_DEFINITION_VERSION="statdef-2026-08-06"`; `load_registry()` refuses on mismatch. Any edit to `data/targets/registry-v2.json` invalidates every pinned constant across `registry.py`, `analysis/validation-status.json`, and any S4 score payload citing it.

**Canonical hash split** (`scorer/canonical.py:1-24`, `score_realism.py:417-465,499-509`): `canonical_sha256` hashes only the `canonical` dict; `scored_at`, `wall_time_seconds`, `analytics_git_sha`, gate/timing seconds live in `result["volatile"]`. S4's manifest-pinning must follow the same volatile/canonical split or it will falsely register score drift on every run.

**Covariance artifact key + the `config_hash` SENTINEL** (`scorer/covariance.py:1-66,164-172`): key = `{config_hash, engine_git_sha, scorer_version, stat_definition_version, hand_count, lineup, seed_set}`; `artifact_id = "cov-" + sha256(canonical_bytes(key))[:16]`. `config_hash` currently = sentinel `CONFIG_HASH_UNAVAILABLE = "declared-gap:config_hash-arrives-with-S4"` (`covariance.py:35`). Checked at: `covariance.py:48` (build_key default), `score_realism.py:176-181` (sentinel==sentinel treated as match "until S4"), `WORKING-AGREEMENT.md:33-36` (planned batch-manifest extension).

- CONTRACT: **S4 retires this sentinel.** Once `_SUCCESS` gains a real `config_hash`, `validate_covariance_artifact` (`score_realism.py:149-186`) starts comparing real hashes — an S4 covariance build still emitting the sentinel would silently defeat the wrong-config refusal.

**`run_id` construction + collision wart** (`export_analytics.py:253`): `run_id = f"run-s{seed}-n{n_hands}"` — ignores `lineup` AND config identity. Downstream: `models/marts/dim_runs.sql:8`, `fct_hand_seats.sql:23`, `fct_decisions.sql:28` all key `run_key = md5(run_id)`.

- CONTRACT: **for S4 this is worse than the documented lineup wart** — sweeping N different dial configs at the same seed+hand-count (likely: seed reuse = CRN/paired comparisons per §a.6, `estimand-contract.md:305-306`) produces **identical run_ids for distinct configs**, colliding in `dim_runs`, every `run_key`-keyed fact table, `assert_row_count_guard.sql`, and (if seed 42 / n 5000 is reused) `assert_sample_regression_pins.sql`. **S4 must mint `run_id` from `(seed, n_hands, config_hash)` or otherwise disambiguate before any dbt build ingests sweep batches — load-bearing, not a nice-to-have.**

**Scorer runtime constraints (§a.5 rule 5, `scorer/constraints.py:539-648`):** (a) throughput ≥350 hands/sec read from a sibling `_TIMING.json`/`times.txt`; **missing timing evidence fails closed** (`:601-612`); (b) reproducibility — scores the batch twice in-process, compares `canonical_sha256`. S4's runner must emit a real timing log per batch or every sweep a5-check fails rule 5(a).

## 4. Status/authority contracts

`analysis/validation-status.json` keyed by exact triple `(formula_id, registry_content_sha256, stat_definition_version)`; read by `score_realism.resolve_score_status()` (`score_realism.py:100-111`). Both F0 and F1 = `exploratory-surrogate` (retrospective-fail, all legs negative). Absent triple → `unvalidated` (`score_realism.py:81-97`).

- CONTRACT: **S4 must not present sweep scores as more authoritative than this status permits** — scores are reproducibility smoke data only. If S4 changed the registry file, its scores would silently become a NEW triple → `unvalidated`, not `exploratory-surrogate`; S4's manifest/report language must state score status per output, not once at the top.

## 5. Downstream consumers

- **dbt marts**: `_SUCCESS` read as a dbt source (`stg_poker__runs.sql:1-22`); all marts key off `run_key = md5(run_id)` (collision risk above). `sem_seat_hands.yml:41` references `run_key` in the semantic layer.
- **`tests/assert_sample_regression_pins.sql`**: pins exact counts for `run_key = md5('run-s42-n5000')` only — sweep batches under other seeds/configs won't trip it, but a sweep reusing seed=42/n=5000 with a different config silently merges into the pinned fixture.
- **`tests/assert_row_count_guard.sql`**: expects exactly `n_hands × 9` rows per run_key — config collision under one run_key fails CI.
- **CI** (`.github/workflows/ci.yml:1-90`): lint → data-sample → validate → sql-lint → build (dbt + tests) → semantic-verify; a second job fails PRs on breaking ODCS changes. `contracts/poker_events.odcs.yaml` is poker-analytics-owned (`WORKING-AGREEMENT.md:16`).
- **`scorer/tests/`** via `make scorer-test` — **not in CI's workflow** (only build/semantic-verify are); scorer regressions may not be caught pre-merge (gap).

## Load-bearing unknowns

- `make scorer-test` absent from CI — S4 changes to `covariance.py` key logic may merge unregressed.
- No S4 implementation exists anywhere yet; §c acceptance tests specified but unbuilt. Ownership manifest says "Counterfactual-config execution (S4) → poker-coach" (`WORKING-AGREEMENT.md:15`) but the §c validator needs the pydantic model that only exists in poker-coach `backend/app/domain/content/models.py` — cross-repo wiring unspecified beyond that ownership row.
- No existing ticket names the `run_id` disambiguation as S4 scope — documented as wart only (`export_analytics.py:249-252`).
- Overlay mechanism ruling absent: in-memory merge vs ephemeral scratch-dir packs via `load_persona_packs(content_dir=…)` (`personas.py:40`) — estimand contract wording (`:444-446`) is compatible with either.
