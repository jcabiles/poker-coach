# Delta spec — S4: batch sweep runner + counterfactual-config layer

status: rev 2 (post dual-review; rev 1 findings adjudicated in `docs/ai-dlc/ledger/flywheel-s4.md`)
slice: bot-realism-flywheel S4 (roadmap `docs/ai-dlc/roadmap/bot-realism-flywheel.md:129-135`)
contracts: `docs/ai-dlc/contracts/flywheel-s4.md` (mapped 2026-08-07)
owner rulings inherited: scores are non-authoritative (S3 stop-gate: status
`exploratory-surrogate`) — S4 uses scores as reproducibility smoke data ONLY.

## Goal (one line)

One command in poker-coach: N counterfactual configs (§c schema) + one shared seed
list → N validated in-memory pack overlays → N seeded parallel exports → N gated
scores in poker-analytics → one manifest pinning engine sha · seed · config hash ·
scorer version · registry version per run.

## Decisions locked at Gate 1 (owner, 2026-08-07)

- Driver lives in poker-coach (working agreement: counterfactual execution → coach).
- Shared seed set across all configs (common-random-numbers / paired design, §a.6).
- Score-only: sweep batches are never loaded into the dbt warehouse.
- CI gap fix in scope: add `make scorer-test` to poker-analytics CI.

## Design rulings from the rev-1 dual review (binding)

- **Σ_sim is wave-wide (§a.3):** the covariance artifact is built ONCE from ≥5 seed
  replicates of the BASELINE config and reused for every swept config. Therefore the
  scorer does NOT require batch `config_hash` == artifact `config_hash`. The
  artifact's `config_hash` is its SOURCE identity (which config the replicates ran);
  the batch's `config_hash` is recorded in the score payload. Equality checks stay:
  engine sha, hand count, lineup, scorer version, stat-definition version.
- **Artifact rebuild is mandatory:** `validate_covariance_artifact` compares engine
  git sha, and S4's commits change the sha — so S4 rebuilds the baseline artifact at
  the S4 engine commit (5 replicate exports, shared seeds) with a REAL source
  config_hash threaded from the replicate manifests, and re-pins
  `DEFAULT_COVARIANCE_ARTIFACT`.
- **Re-export byte-identity is impossible and not claimed:** the exporter stamps
  wall-clock `exported_at` into every parquet row, and the raw-parquet hash sits
  inside the score canonical payload (gate tamper-evidence — unchanged). Identity
  claims are therefore split: (a) re-SCORING a batch is fully byte-identical;
  (b) re-EXPORTING at the same (seed, config) must produce parquet content equal
  after excluding the `exported_at` column (the producer-rerun check — closes S3's
  declared gap), and score canonical payloads equal after masking
  `gate.parquet_sha256` only.
- **The default (no-config) export path simulates the RAW as-loaded packs**;
  canonicalization runs only as a side-channel to compute the baseline
  `config_hash`. This keeps acceptance test 1(i) a real canonicalization-safety
  proof, not a tautology.
- **Parallelism + retention are §f REQUIREMENTS, not options:** bounded 5-worker
  parallel export (subprocess-level concurrency; ProcessPoolExecutor is
  sandbox-blocked — use threads driving subprocesses), and raw parquet DELETED after
  scoring (manifest keeps seed + config hash → any batch reproducible on demand),
  with an explicit `--keep-raw` debug override.

## What gets built / changed

### poker-coach

1. **NEW `backend/tools/counterfactual.py`** — the §c config layer:
   - Validate a counterfactual-config JSON against §c (`estimand-contract.md:415-462`):
     allowed override paths = exactly the §a.2 axis table with bounds; unknown fields
     rejected; explicit `null` forbidden; `base_pack_hash` must match the loaded
     baseline packs' canonical hash.
   - **Path parsing is deterministic:** dotted paths are split on `.` with greedy
     longest-match against the pack's authored key set for `postflop.sizing` weight
     keys (decimal-string keys like `0.33` are matched whole, never re-split); a
     path that cannot resolve unambiguously is a REJECTION, not a guess. Unit-tested
     against every authored sizing key in the committed packs.
   - **Probe declarations get a frozen schema:** `{probe_kind, persona, paths[],
     rationale}`; `continue_ref` / `sizing_by_node` accepted only with a matching
     entry; **a config that overrides a persona's `continue_ref` AND that persona's
     `postflop.call_looseness` is rejected** (§a.2 axis 7: never co-swept — the
     co-variation deletes the mechanism attribution).
   - Overlay merge: deep-copy baseline packs, apply overrides (SET-only), serialize
     with **`exclude_unset=True`** so absent optional fields STAY absent
     (key-absence is semantically load-bearing, §c.4 / `models.py` optional fields),
     then re-validate from serialized JSON through the SAME pydantic model
     (`backend/app/domain/content/models.py`) — never in-place attribute update,
     never a file under `content/`. A presence-preservation test asserts every
     non-overridden field keeps both value AND presence/absence state.
   - Canonicalization: materialize `call_looseness` explicitly (§a.2 rule,
     `estimand-contract.md:142-148`).
   - `config_hash` = sha256 over sorted-key, shortest-round-trip-float JSON bytes of
     the canonicalized config (§c.6). Pure functions; imports domain content models
     read-only; domain files unmodified.

2. **MODIFY `backend/tools/export_analytics.py`** (hotspot — single owner):
   - `run_export(...)` gains optional `packs=` (already-validated pack objects).
     Default path simulates RAW as-loaded packs (see ruling above).
   - `_SUCCESS` gains `config_hash` — ALWAYS present: baseline canonical config hash
     when no overrides given.
   - `run_id` becomes `run-s{seed}-n{n_hands}-c{config_hash[:12]}`. Committed seed-42
     fixture NOT regenerated; `assert_sample_regression_pins.sql` keeps binding on
     the committed fixture; a comment there already notes re-pin-on-regeneration.
   - Emit `_TIMING.json` before `_SUCCESS` (which stays last), frozen schema:
     `{schema_version, wall_seconds, n_hands, seed, run_id}` — `wall_seconds` is the
     exact key `constraints.py` rule 5(a) reads (`constraints.py:544`); validated
     against `_SUCCESS` at write time.
   - ODCS copy `backend/tools/poker_events.odcs.yaml`: version 1.1.0 → **1.2.0**
     (additive): manifest customProperty text gains `config_hash`; `run_id`
     description string updated to the new format; non-breaking changelog entry.
     Byte-identical text mirrored to the analytics copy (patch handed to the
     analytics-side ticket, S3-style).

3. **NEW `backend/tools/sweep_runner.py`** — the one command:
   - Input: sweep spec JSON (config file paths + shared seed list + n_hands +
     output root + poker-analytics repo path). Configs/outputs ephemeral, never
     committed.
   - Bounded 5-worker parallel execution (threads driving export subprocesses).
   - Per (config, seed): validate config → overlay → export to a unique dir →
     `make validate DIR=` → `make score DIR=<batch> OUT=<per-run-file>
     COV=<pinned-artifact>` (always explicit OUT and COV; scores read from the OUT
     file, never parsed from stdout; no piping of success-bearing commands) →
     delete raw parquet after a successful score (unless `--keep-raw`).
   - Fail-closed: a failed gate/score marks the run failed and the sweep PARTIAL;
     partial manifests are labeled, never silently complete.
   - **Producer-rerun check (closes S3 declared gap):** one designated (config,
     seed) in every sweep is exported twice; the two batches' parquet content must
     be equal after excluding `exported_at`, and their score canonical payloads
     equal after masking `gate.parquet_sha256`.
   - Output `sweep_manifest.json`, scorer-style canonical/volatile split:
     canonical = per-run {config_hash, seed, n_hands, run_id, engine git_sha,
     scorer_version, registry sha + version, stat_definition_version, score
     canonical_sha256, score status, run status} + sweep-level {schema_version,
     ordered config_hash list, shared seed list, covariance artifact id} — hashes
     and logical IDs only, no paths; volatile = timestamps, wall times, absolute
     paths. Canonical section byte-identical across re-scoring re-runs.
   - **Score-authority stamp:** every per-run entry carries the resolved score
     status (`exploratory-surrogate` today) and the manifest header repeats:
     "scores are reproducibility smoke data only; non-authoritative for tuning."

4. **NEW tests** `backend/tests/test_counterfactual.py`,
   `backend/tests/test_sweep_manifest.py`: §c worked-rejection cases; bounds; path
   parsing incl. decimal sizing keys; co-sweep refusal; presence preservation;
   empty-override == canonicalized-baseline pack equality; config_hash stability
   across two processes (subprocess); manifest canonical determinism (unit-level).

### poker-analytics

5. **MODIFY `ingest/validate.py` (gate version check):** exact-equality on
   `contract_version` becomes same-major + batch-minor ≤ contract-minor (matches the
   check's own error text "matching contract major" and the ODCS
   `compatibilityPolicy: BACKWARD`). Tests: legacy 1.1.0 batch and the committed
   1.1.0 sample still gate under the 1.2.0 contract; a 2.x batch refuses.
   `config_hash` accepted as an optional manifest key (absent on pre-S4 batches).
6. **MODIFY `scorer/score_realism.py`:** canonical `producer_run` gains
   `config_hash` WHEN the manifest carries it; omitted for legacy manifests so
   pre-S4 canonical bytes are unchanged. `validate_covariance_artifact`: equality
   set unchanged (engine sha, hand count, lineup, scorer version, statdef); batch
   config_hash is NOT compared to the artifact's (wave-wide reuse, §a.3) — the
   sentinel comment block is replaced by this documented rule.
7. **MODIFY `scorer/covariance.py`:** `build_key`/`build_artifact` thread the REAL
   `config_hash` derived from the replicate manifests — exactly one distinct real
   hash across all replicates, or all-absent (legacy) → sentinel; mixed or
   multi-hash sets are a refusal.
8. **Rebuild + re-pin the baseline covariance artifact** at the S4 engine commit
   (5 replicate 50k exports on the shared seed set, ratified lineup); commit the
   artifact; update `DEFAULT_COVARIANCE_ARTIFACT`.
9. **MODIFY `.github/workflows/ci.yml`:** add `make scorer-test`.
10. **Apply the ODCS 1.2.0 patch** (byte-identical to the coach copy) + changelog;
    scorer tests updated for items 5–7 (real/real, legacy-absent, mixed-set
    refusal, version-window tests).

## Acceptance

1. §c acceptance (`estimand-contract.md:459-462`), as adjudicated: (i)
   empty-override config vs no-config baseline at the same seed: parquet content
   equal excluding `exported_at`; score canonical payloads equal after masking
   `gate.parquet_sha256` only (run_id, config_hash, scores, stats all identical);
   (ii) the three worked-rejected config examples fail with the stated errors;
   (iii) canonical config hash stable across two independent processes.
2. Canonicalization gate (`:142-148`): test 1(i) passes BEFORE any sweep runs.
3. 10-config smoke sweep at 50k hands/config (artifact hand-count equality binds it
   to 50k) via the one command; re-SCORING all batches reproduces byte-identical
   score canonical payloads and a byte-identical sweep-manifest canonical section;
   the in-sweep producer-rerun check passes.
4. One-config 50k benchmark recorded against the §f compute budget; §f's numbers
   updated from the measured manifests (mechanical revision clause — not a §e.3
   event); ≥350 hands/s evidenced via `_TIMING.json`.
5. Every sweep output stamps score status (`exploratory-surrogate` under today's
   registry triple).
6. `make scorer-test` green locally AND in the analytics CI workflow; pre-S4
   batches (no `config_hash`, contract 1.1.0) still gate + score byte-identically.
7. poker-coach `./scripts/verify.sh` + `ruff check .` green; `git diff
   backend/app/domain/ content/` EMPTY at every commit.

## Out of scope

No dbt/warehouse loading of sweep batches · no policy-code or persona-pack edits
(`backend/app/domain/` + `content/` diff-clean) · no registry or stat-definition
changes (registry sha stays `b83043ae…`) · no committed sweep configs or batches
(ephemeral only; the rebuilt covariance ARTIFACT is committed — it is a scorer
input, not a sweep output) · no score-based tuning conclusions or config rankings ·
no per-config covariance re-estimation (§a.6 stage 3 — a later slice) · no frontend
work · configs sweep the §a.2-declared space only · committed seed-42 fixture not
regenerated · no run_id backfill of existing batches · no emulator work (§f
escalation clause fires only if the measured benchmark demands it — that is a
finding to report, not to build).

## Constraints (profile + flywheel)

Domain core has no web/DB imports (test-enforced) — new tools live in
`backend/tools/`, importing domain code read-only. Strategy stays in versioned
`content/` data. Sweep artifacts under an explicit output root or $TMPDIR, never
`/tmp`, never committed. Registry edits require a contract amendment — S4 makes
none. Reviewers git-read-only. No piping of success-bearing commands. Auth: none.

## Verify-by (end-to-end, in terms of profile.verify)

- poker-coach: `./scripts/verify.sh` → "BACKEND VERIFY OK"; `cd backend && ruff
  check .` clean; `git diff --stat backend/app/domain/ content/` prints nothing.
- poker-analytics (S4 branch): `make scorer-test` green (incl. new version-window,
  threading, and refusal tests); `make validate DIR=<pre-S4 batch>` + `make score …`
  byte-identical to their S3 outputs (back-compat).
- Cross-repo: acceptance tests 1(i)–(iii) explicitly; the 10-config smoke sweep,
  then re-score and diff canonical sections; benchmark + §f mechanical update.
