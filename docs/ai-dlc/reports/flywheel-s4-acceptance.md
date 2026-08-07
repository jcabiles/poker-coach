# Flywheel S4 — Acceptance report (T6)

**Authority stamp (verbatim, header-pinned):** scores are reproducibility smoke data
only; non-authoritative for tuning (S3 stop-gate: exploratory-surrogate).

This report contains no config rankings and no realism conclusions. Where scores
appear, only their `config_hash` and `score_status` are reported — never a comparison
between two scores' numeric content.

**Scope.** This is the formal acceptance run for S4 (Batch sweep runner +
counterfactual-config layer): §c acceptance tests (i)–(iii) from the methods
contract, the 10-config smoke sweep, the §f compute-budget benchmark, and the
deferred-gap check against S3's declared gaps.

**Environment.** Engine `e7c1b38` (coach worktree `feat/flywheel-s4`); analytics
`12884db` (analytics worktree, execute-only); pinned covariance artifact
`cov-4a718ef1f6c30391` (`scorer/artifacts/cov-4a718ef1f6c30391.json`; 50k hands ×5
seeds 601–605; ratified lineup; baseline `config_hash`
`9273b753b9de041a9750557f21c72d4a7482b344d73be7d378b3df56c21375f8`). T4's five gated
baseline replicate batches reused from `/tmp/claude-501/t4-replicates/rep-601..605`.

**Deviation noted, not chased:** the ticket's "READ FIRST" pointer
`docs/ai-dlc/specs/flywheel-s4.md` does not exist in the coach worktree (nor on any
branch in this repo's history). The citations to it are not inherited from an older
slice — they were **authored in this slice**: `backend/tools/sweep_runner.py:7`
("Design (spec `docs/ai-dlc/specs/flywheel-s4.md`, "Design rulings")") and
`backend/tools/counterfactual.py:28` (`spec docs/ai-dlc/specs/flywheel-s4.md:63-67`),
both landed in S4's own T2/T5 commits. These are dangling citations to a spec file
that was apparently never committed; **resolve when T7 commits the spec** (or strike
the citations if T7 determines no such file was ever meant to exist as a separate
doc). §c acceptance criteria are authoritative in `docs/methods/estimand-contract.md`
(analytics worktree), which does exist and is what this report tests against; the S4
roadmap entry's pass/fail line is the second source of truth used. No spec-vs-contract
contradiction was found — the `sweep_runner.py` docstring's described behavior matches
the contract exactly everywhere checked.

---

## A. §c acceptance (i) — canonicalization safety

**Config authored:** `counterfactual.empty_override_config(load_baseline_packs())` —
`{"schema_version":"1.0.0","base_pack_hash":"6364992c9b0e7cc2e90e5b46037d7f5dd7de58f5c2ed07f7515b11e59d744c1a","overrides":{},"probe_declarations":[]}`.

**Export:** `python -m tools.export_analytics --hands 50000 --seed 601 --out
$TMPDIR/t6-acc1/empty-override --config $TMPDIR/t6-acc1/empty_override.json --lineup
tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac` (the ratified
lineup — the exporter's plain default is alphabetical, not ratified; passing it
explicitly was required to match T4's rep-601 arm). `config_hash` produced:
`9273b753b9de041a9750557f21c72d4a7482b344d73be7d378b3df56c21375f8` — identical to the
baseline config_hash pinned in the ticket and to T4 rep-601's `config_hash`.
`run_id`: `run-s601-n50000-c9273b753b9de` — identical to rep-601's. `row_counts.decisions`:
883426 — identical to rep-601's.

**(1) Parquet-table equality** (`sweep_runner.parquet_batches_equal`, which drops
`exported_at` before comparing, per its own logic — reused directly, not
reimplemented): `hands.parquet` → equal; `seat_outcomes.parquet` → equal;
`decisions.parquet` → equal. Overall `parquet_batches_equal(...) == True`.

**(2) `_SUCCESS` identity:** `run_id` A=B=`run-s601-n50000-c9273b753b9de`; `config_hash`
A=B=`9273b753b9de041a9750557f21c72d4a7482b344d73be7d378b3df56c21375f8`.

**(3) `make validate` + `make score` (no `--config` on the COV side means the
Makefile's default was NOT used — `COV=scorer/artifacts/cov-4a718ef1f6c30391.json`
explicit, per the sweep runner's own binding rule):**
- `make validate DIR=$TMPDIR/t6-acc1/empty-override` → 156/156 contract checks passed,
  gate wrote `_GATE_OK.json`.
- `make score DIR=... OUT=$TMPDIR/t6-acc1/empty-override-score.json
  COV=scorer/artifacts/cov-4a718ef1f6c30391.json` → `canonical_sha256`
  `b6f487a94ddae93ecfa319aa920075a23a086be435601746f9d77caa4db2c003`.
- Rep-601 re-scored fresh (same COV) → `canonical_sha256`
  `bb47faf6285b18e8eb3634841cb76de6d15808e1cf51953a73982afd06da3151`.
- Raw `canonical_sha256` values **differ** — expected, because they differ ONLY in
  `gate.parquet_sha256` (the export ran twice, producing two byte-distinct Parquet
  files whose row content is identical but whose file bytes are not — timestamps/
  encoder nondeterminism in Parquet writers is exactly what `gate.parquet_sha256`
  is expected to vary on across independent exports of the same logical content).
  A field-level diff of the two `canonical` payloads found **exactly one** differing
  leaf: `.gate.parquet_sha256`. `sweep_runner.score_payloads_equal_ignoring_gate_hash`
  (masks that one field, compares canonical bytes) → **`True`**. Both payloads'
  `score_status` = `exploratory-surrogate` (S3 stop-gate — expected, not a finding
  about this test).

**Reproducible invocation** (field-diff + masked-equality check, run from
`backend/` in the coach worktree):
```python
import json
from tools.sweep_runner import score_payloads_equal_ignoring_gate_hash

a = json.load(open(".../empty-override-score.json"))["canonical"]
b = json.load(open(".../rep601-rescore.json"))["canonical"]

def flatten(x, path=""):
    out = {}
    if isinstance(x, dict):
        for k, v in x.items():
            out.update(flatten(v, path + "." + k))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            out.update(flatten(v, path + f"[{i}]"))
    else:
        out[path] = x
    return out

fa, fb = flatten(a), flatten(b)
diffs = [k for k in set(fa) | set(fb) if fa.get(k) != fb.get(k)]
print(diffs)  # -> ['.gate.parquet_sha256']

print(score_payloads_equal_ignoring_gate_hash(a, b))  # -> True
```

**Verdict: A PASSES.** Canonicalizing an empty-override config reproduces
byte-identical parquet content, identical run/config identity, and identical scores
(modulo the one field the contract itself declares masked) against the raw baseline
export.

---

## B. §c acceptance (ii) — the three worked-rejected examples

Unit-test coverage (existing, cited not re-authored):
`backend/tests/test_counterfactual.py::test_worked_rejection_1_continue_ref_without_probe`
(line 104), `::test_worked_rejection_2_structural_preflop_path` (line 117),
`::test_worked_rejection_3_explicit_null` (line 128).

**Additional CLI-boundary demo (example 1, continue_ref without probe):** config
`{"overrides":{"tag":{"postflop.continue_ref":0.9}},"probe_declarations":[]}` run via
`python -m tools.export_analytics --hands 100 --seed 999 --out
$TMPDIR/t6-acc1/rejected-demo --config $TMPDIR/t6-acc1/rejected_continue_ref.json`.

**Exit code: 1.** stderr (verbatim):
```
ERROR: /tmp/claude-501/t6-acc1/rejected_continue_ref.json: tag: `postflop.continue_ref`
is a frozen calibration anchor — it is its own axis in dedicated mechanism probes only
(§a.2 axis 7 / §c.3); declare a dedicated probe ({probe_kind: 'continue_ref', persona,
paths, rationale}) to sweep it. It is frozen because the engine's facing-node raise
scale is calibrated against it: moving it with the calling dial pins their ratio and
deletes the raise-independence feature.
```
Names the freeze rationale, per §c.3.

**Verdict: B PASSES** (unit coverage confirmed present + CLI boundary independently
reproduces rejection example 1's exact failure mode and exit code).

---

## C. §c acceptance (iii) — config-hash cross-process stability

Existing subprocess test cited:
`test_counterfactual.py::test_config_hash_stable_across_two_independent_processes`
(line 813) — two child processes, `PYTHONHASHSEED` 0 and 1, assert equal hashes.

**Additional demo:** the §c-acceptance-(i) empty-override config's hash computed in
two fresh `python -c` processes (`PYTHONHASHSEED=0` and `PYTHONHASHSEED=1`),
run from `backend/` in the coach worktree:
```sh
PYTHONHASHSEED=0 python -c "
import sys
sys.path.insert(0, '.')
from tools.counterfactual import load_config
print(load_config('/tmp/claude-501/t6-acc1/empty_override.json').config_hash)
"
PYTHONHASHSEED=1 python -c "<same body>"
```
both processes returned `9273b753b9de041a9750557f21c72d4a7482b344d73be7d378b3df56c21375f8`.

**Verdict: C PASSES.**

---

## D. The 10-config smoke sweep

**Sweep spec** (`$TMPDIR/t6-smoke/sweep_spec.json`): 10 ephemeral configs, seeds
`[701]`, `n_hands` 50000, ratified lineup, `cov_artifact =
scorer/artifacts/cov-4a718ef1f6c30391.json`, `out_root = $TMPDIR/t6-smoke/out`, run
with `--keep-raw`.

**The 10 configs** (all plain overrides, no probe declarations, each validated
locally via `counterfactual.validate_config` before being written, each within its
declared §a.2 bound):

| # | Config | Override | Bound | `config_hash` (16-char prefix) |
|---|---|---|---|---|
| 1 | `01-tag-callloose` | tag `postflop.call_looseness = 1.5` | [0.2, 5.0] | `b841e294bc298c6e` |
| 2 | `02-lag-bluff` | lag `postflop.bluff_freq = 0.6` | [0.0, 1.0] | `80773c05ff7593ce` |
| 3 | `03-nit-aggression` | nit `postflop.aggression = 2.0` | [0.2, 5.6] | `00398cffeed32f8a` |
| 4 | `04-maniac-sprcommit` | maniac `postflop.spr_commit = 2.5` | [0.5, 4.0] | `a6721b1e8ba466f8` |
| 5 | `05-station-elasticity` | calling_station `postflop.size_elasticity = 2.0` | [0.0, 3.0] | `f4f5a57599f1cb9d` |
| 6 | `06-fish-linesens` | passive_fish `postflop.line_sensitivity = 1.2` | [0.0, 2.0] | `ddcbca419d32dae1` |
| 7 | `07-tag-multidial` | tag `call_looseness=1.0, bluff_freq=0.4, aggression=3.0` | all within bounds | `72ab1c2063810819` |
| 8 | `08-lag-threebetmult` | lag `sizing.threebet_mult = 3.0` | [2.0, 4.0] | `597d4d6bf4ef5aa2` |
| 9 | `09-tag-flatsizing` | tag flat-sizing, all 4 authored keys `0.25/0.25/0.25/0.25` (sum=1) | each in [0.05, 0.85] | `121d8dab7bf43fe4` |
| 10 | `10-nit-positionsens` | nit `postflop.position_sensitivity = 0.5` | [0.0, 1.0] | `126c26e36b7275f3` |

10/10 distinct `config_hash` confirmed before the sweep ran.

**Run:** `python -m tools.sweep_runner --spec sweep_spec.json --keep-raw`.

**Result:** `sweep_status: complete`. **Wall-clock for the whole sweep run: 569.3 s**
(9m 29.3s; measured by wrapping the invocation).

**Manifest (`sweep_manifest.json`) canonical summary:**

| config_hash (16c) | run_id | run_status | score_status |
|---|---|---|---|
| `b841e294bc298c6e` | `run-s701-n50000-cb841e294bc29` | ok | exploratory-surrogate |
| `80773c05ff7593ce` | `run-s701-n50000-c80773c05ff75` | ok | exploratory-surrogate |
| `00398cffeed32f8a` | `run-s701-n50000-c00398cffeed3` | ok | exploratory-surrogate |
| `a6721b1e8ba466f8` | `run-s701-n50000-ca6721b1e8ba4` | ok | exploratory-surrogate |
| `f4f5a57599f1cb9d` | `run-s701-n50000-cf4f5a57599f1` | ok | exploratory-surrogate |
| `ddcbca419d32dae1` | `run-s701-n50000-cddcbca419d32` | ok | exploratory-surrogate |
| `72ab1c2063810819` | `run-s701-n50000-c72ab1c206381` | ok | exploratory-surrogate |
| `597d4d6bf4ef5aa2` | `run-s701-n50000-c597d4d6bf4ef` | ok | exploratory-surrogate |
| `121d8dab7bf43fe4` | `run-s701-n50000-c121d8dab7bf4` | ok | exploratory-surrogate |
| `126c26e36b7275f3` | `run-s701-n50000-c126c26e36b72` | ok | exploratory-surrogate |

10/10 `run_status: ok`; 10 distinct `config_hash`; 10 distinct `run_id`.

**`producer_rerun_check` block (verbatim structure):**
```json
{
  "check_status": "passed",
  "config_hash": "b841e294bc298c6e219f119681b5a86d64f4c0d1d070e1523e8f0b506e0d88b8",
  "parquet_equal": true,
  "passed": true,
  "score_equal": true,
  "seed": 701
}
```

**`score_authority` field (verbatim, matches this report's header):** "scores are
reproducibility smoke data only; non-authoritative for tuning (S3 stop-gate:
exploratory-surrogate)".

**Re-score pass (byte-identity evidence).** The sweep runner has no score-only
re-invocation mode exposed at the CLI (`main()`'s only entry point re-runs the full
export→validate→score pipeline); per the ticket's documented fallback, per-batch
re-score equality is what is proved here. For each of the 10 kept raw batches,
`make score` was re-run a second time to a fresh `OUT=` file (same pinned COV
artifact), and each fresh `canonical_sha256` was compared against the value the
sweep's own manifest recorded for that `run_id`. Command template (run once per
batch directory `$d` from the analytics worktree):
```sh
make score DIR="$d" OUT="/tmp/claude-501/t6-smoke/rescore/$(basename "$d").json" \
  COV=scorer/artifacts/cov-4a718ef1f6c30391.json
```

| run_id | sweep-recorded `score_canonical_sha256` (16c) | fresh re-score `canonical_sha256` | match |
|---|---|---|---|
| `run-s701-n50000-cb841e294bc29` | `71db01d222bd2749` | `71db01d222bd2749...` | True |
| `run-s701-n50000-c80773c05ff75` | `734547364c2dac81` | `734547364c2dac81...` | True |
| `run-s701-n50000-c00398cffeed3` | `ce709af5fa57f13c` | `ce709af5fa57f13c...` | True |
| `run-s701-n50000-ca6721b1e8ba4` | `39e7eb6363e9e26f` | `39e7eb6363e9e26f...` | True |
| `run-s701-n50000-cf4f5a57599f1` | `c1430c0a8496c132` | `c1430c0a8496c132...` | True |
| `run-s701-n50000-cddcbca419d32` | `11057ac975eaa9a6` | `11057ac975eaa9a6...` | True |
| `run-s701-n50000-c72ab1c206381` | `c2ecadeefa28da12` | `c2ecadeefa28da12...` | True |
| `run-s701-n50000-c597d4d6bf4ef` | `3d128d44420f2d10` | `3d128d44420f2d10...` | True |
| `run-s701-n50000-c121d8dab7bf4` | `db333e084a2fc3ac` | `db333e084a2fc3ac...` | True |
| `run-s701-n50000-c126c26e36b72` | `d9eb36cc62e67a7e` | `d9eb36cc62e67a7e...` | True |

**All 10/10 match** — this is the byte-identity evidence proved: re-scoring an
already-exported batch a second time, independently of the sweep run, reproduces
the exact `canonical_sha256` the sweep recorded, for every one of the 10 configs.
(No score numeric content is compared or ranked anywhere in this table or report —
only hash equality/inequality.)

**Verdict: D PASSES.**

---

## E. Benchmark vs §f

**Revision note (post-review):** the first pass of this section applied §f's ×5
worker factor to the SERIAL, unloaded single-worker export time (125.95 s) — that
overstates capacity by treating 5 workers as if each ran at the single-worker rate
with zero contention. The smoke sweep's own per-export wall-clock under 5-way load
(194.9–217.8 s per export, see below) shows real per-worker efficiency well under 1.
This revision uses the MEASURED END-TO-END loaded throughput as the primary figure.

**T4's five serial `_TIMING.json` values (export-only wall-clock, single-core, no
parallel load — kept as the single-worker serial export benchmark ONLY, not the
capacity denominator):**

| seed | wall seconds | hands/s |
|---|---|---|
| 601 | 125.95 | 396.97 |
| 602 | 122.83 | 407.07 |
| 603 | 122.32 | 408.75 |
| 604 | 122.74 | 407.36 |
| 605 | 121.90 | 410.18 |

Mean 123.15 s (406.0 h/s); worst 125.95 s (396.97 h/s); best 121.90 s (410.18 h/s).
Matches the ticket's stated range (121.9–126.0 s, 397–410 h/s).

**Serial single-worker per-config TOTAL** (export + gate + scorer, the same
additive form §f itself uses for its 424 s / 155 s figures): worst-case export
125.95 s + gate+score bundled ~2.96 s (measured — see below) ≈ **128.9 s**. This is
context only; per-worker component splits were not separately isolated across all
runs (§A's own `make validate` + `make score` calls measured ~1.64 s + ~0.53 s ≈
2.17 s for one batch, close to but not identical to the bundled smoke-sweep average
below — the difference is subprocess/`make`-invocation overhead not visible in
isolated component timings).

**Measured 5-way-loaded per-export wall-clock** (from `_TIMING.json` inside each of
the 10 smoke-sweep batch directories, §D): 194.9–217.8 s, mean **206.55 s**.
**Per-worker efficiency at 5-way load** = serial-worst ÷ mean-loaded-export =
125.95 / 206.55 = **0.610**. If parallelism were perfect this would be 1.0 (5
workers → 5× throughput); at 0.61 the aggregate export-stage capacity multiplier is
5 × 0.610 = **3.05×** the single-worker rate (not 5×). This diagnostic figure
(0.61, 3.05×) is reported for T7's use in fixing §f's formula — it is NOT what
feeds the capacity arithmetic below, because it excludes the extra producer-rerun
dup export and the 10 serial validate+score steps that a real sweep night also
pays for.

**Gate+score bundled wall-clock** (correct field: `volatile.runs[].wall_seconds` in
`sweep_manifest.json` — NOT `volatile.wall_time_seconds`, a per-score-file field
that measures only the scorer's internal stats step, not validate+score end to
end): 10 values, 2.833–3.458 s, mean **2.963 s**.

**PRIMARY capacity figure — measured aggregate end-to-end throughput.** The smoke
sweep (§D) processed the 10 declared configs, under real 5-worker contention, one
producer-rerun dup export, and all 10 serial validate+score steps, in **569.3 s**
total wall-clock:
```
569.3 s / 10 configs = 56.93 s/config (measured, loaded, end-to-end)
28800 × 0.8 / 56.93 ≈ 404.7 configs/night
```
(No ×5 factor here — the 569.3 s figure already reflects the whole 5-worker rig's
throughput for 10 configs, so dividing by config count directly yields the loaded
per-config rate.)

- **1,045–1,225-run program:** 1045/404.7 to 1225/404.7 = **2.58–3.03 nights**.
- **1,500-run hard cap:** 1500/404.7 = **3.71 nights**.

**Reconciling the two speedup figures (both correct, different scopes — do not
transplant one for the other):**
- **End-to-end aggregate speedup** (whole sweep, incl. the dup export + serial
  validate/score overhead): `(10 × 125.95 s serial-worst) / 569.3 s = 1259.5 / 569.3
  ≈ 2.21×`.
- **Export-stage-only capacity multiplier** (workers × per-worker efficiency,
  excludes dup export and all validate/score overhead): `5 × 0.610 ≈ 3.05×`.
The gap between 2.21× and 3.05× is accounted for by the 11th (dup) export
competing for a worker slot and by ~30 s of serial validate+score work (10 ×
~2.96 s) that the export-stage multiplier does not count. **The 56.93 s/config
figure (from the 2.21×-consistent 569.3 s total) is the one used for the capacity
arithmetic above** — it is the true end-to-end measurement, not a derived multiple.

**Escalation-clause verdict: does NOT fire.** §f's clause fires only if S4's
measured time pushes the program past 6 worst-bound nights. Measured hard-cap
duration: **3.71 nights = 3.71/6 ≈ 61.8% of the 6-night threshold** — under the
threshold, but by a much smaller margin than the (wrong) 27.3% figure the
serial-denominator arithmetic implied. Escalation still does not fire, but §f's
mechanical-revision clause should carry the corrected 3.71-night figure, not a
number closer to 1.6.

**Parallelism observation, restated (informational — not a separate capacity
claim):** per-batch `_TIMING.json` export walls under this run's 5-way load ranged
194.9–217.8 s — substantially more than the "~20% slower" figure named as a known
fact in the originating ticket's brief (this run measured ~55–73% slower per
export, i.e. 0.61 efficiency, not ~0.83). Recorded as an observation per the
brief's instruction not to chase it as a defect; the MEASURED end-to-end 56.93
s/config figure above already absorbs whatever the true degradation is — the 0.61/
3.05× figures exist only to explain WHY the end-to-end number is what it is, and
to give T7 the loaded-worker component so §f's `×5` form can be repaired.

**Exact replacement numbers for §f's mechanical-revision clause (T7 applies the
doc edit; this report does not):**
- **Flag for T7:** §f's `28800×0.8×5/t` form is unsound with `t` = a serial,
  unloaded per-run time — either `t` must become the LOADED per-worker time
  (206.55 s mean, giving the 0.61-efficiency path), or the `×5` must be replaced
  outright by the measured aggregate throughput (404.7 configs/night from
  569.3 s/10 configs). **Do not let T7 transplant the existing formula with a
  serial `t` substituted in** — that reproduces this report's original,
  since-corrected error.
- Single-worker serial export benchmark (context only, not a capacity input):
  **125.95 s worst / 123.15 s mean**.
- Measured per-worker efficiency at 5-way load: **0.610** (aggregate export-stage
  capacity multiplier: 5 × 0.610 ≈ **3.05×**, diagnostic only).
- **Primary measured configs/night (loaded, end-to-end): ≈404.7/night.**
- 1,045–1,225-run program: **2.58–3.03 nights** (was 3.86–4.51 in §f's original
  arithmetic; was wrongly stated as 1.14–1.34 nights in this report's first pass).
- 1,500-run hard cap: **≈3.71 nights** (was 5.52 in §f's original arithmetic; was
  wrongly stated as ≈1.64 nights in this report's first pass).
- Escalation clause: **does not fire** (3.71 of 6 nights ≈ 61.8%).

**Verdict: E — benchmark recomputed on measured loaded throughput; escalation
clause evaluated and does not fire.**

---

## F. Deferred-gap check (against S3's declared gaps)

- **`config_hash` sentinel — CLOSED**, by T2/T3/T4. Two distinct pieces of
  evidence, correctly attributed: (1) **per-run score traceability** —
  `canonical.producer_run.config_hash` on each smoke-sweep score payload equals
  that run's own config (e.g. smoke config 1's score carries
  `producer_run.config_hash = "b841e294bc298c6e..."`, matching its `run_id`
  `run-s701-n50000-cb841e294bc29` — every score is traceable to the exact config
  that produced it). (2) **sentinel-retirement proof (the covariance artifact's
  own baseline provenance)** — `canonical.covariance_artifact.key.config_hash` is
  `"9273b753b9de041a9750557f21c72d4a7482b344d73be7d378b3df56c21375f8"` on every
  score regardless of the scored config (it is the artifact's fixed baseline
  source, not per-run identity) — this is what closes S3's gap about the
  covariance artifact itself lacking a recorded config identity, distinct from
  (1)'s per-run traceability.
- **Producer-rerun check — CLOSED**, by T5. Evidence: §D's `producer_rerun_check`
  block (`check_status: "passed"`, `parquet_equal: true`, `score_equal: true`) —
  the sweep runner now proves producer determinism as a first-class check on every
  sweep run, not a manual side exercise.
- **`run_id` collision — CLOSED for the tested arm-set**, by T2 (softened from an
  unconditional claim). Evidence: `run_id` format is
  `run-s{seed}-n{n_hands}-c{config_hash[:12]}` (e.g.
  `run-s701-n50000-cb841e294bc29` — 12 hex chars, 48 bits of the hash, confirmed
  against `export_analytics.py:303`) — no collision occurred among these ten
  configs' `run_id`s (§D: 10 distinct `config_hash` → 10 distinct `run_id`, same
  seed, same n_hands). This is a 48-bit-prefix display identifier, not the
  identity of record: **the FULL `config_hash` in `_SUCCESS` and
  `canonical.producer_run.config_hash` is the actual identity**; a 48-bit prefix
  collision between two DIFFERENT full hashes remains theoretically possible
  (astronomically unlikely at this program's scale, but not structurally
  excluded) and would need the full hash to disambiguate.
- **`lineup` not in `run_id` — REMAINS, disclosed wart.** `export_analytics.py`'s
  own comment (near its lineup-resolution code): "KNOWN WART (out of scope for T2):
  run_id still ignores `lineup`, so two runs with the same (seed, n_hands,
  config_hash) but different lineups [collide on run_id]." Not closed by any S4
  ticket; still an open, named limitation.

---

## Cleanup performed

Smoke sweep raw Parquet (`hands.parquet`, `seat_outcomes.parquet`,
`decisions.parquet` — 33 files across the 10 kept batches + the 1 rerun-dup batch)
deleted after the re-score pass above; `_SUCCESS`, `_TIMING.json`, `_GATE_OK.json`,
`score.json`, and `sweep_manifest.json` retained. T4's five replicate batches
(`/tmp/claude-501/t4-replicates/rep-601..605`) left untouched, including their raw
Parquet.

---

## Summary of verdicts

| Section | Verdict |
|---|---|
| A — §c(i) canonicalization safety | PASS |
| B — §c(ii) worked-rejected examples | PASS |
| C — §c(iii) cross-process hash stability | PASS |
| D — 10-config smoke sweep + re-score byte-identity | PASS |
| E — §f benchmark + escalation clause | Escalation does not fire; measured numbers recomputed |
| F — Deferred-gap check | 3 of 4 gaps closed; lineup/run_id wart remains, disclosed |

No acceptance check failed. No config rankings or realism conclusions are drawn
anywhere in this report.
