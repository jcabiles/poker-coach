"""The batch sweep runner (flywheel S4 T5) — the "one command."

N counterfactual configs (`backend/tools/counterfactual.py`) x one shared
seed list -> N validated exports (`backend/tools/export_analytics.py`) -> N
gated+scored batches in poker-analytics -> one pinned `sweep_manifest.json`.

Design (spec `docs/ai-dlc/specs/flywheel-s4.md`, "Design rulings"):

- ALL configs are validated up front (`counterfactual.load_config`) before any
  export runs — one bad config fails the whole sweep before simulation money
  is spent. Duplicate `config_hash` across configs is a sweep-spec error.
- Exports run with bounded 5-worker parallelism: a `ThreadPoolExecutor` whose
  workers each shell out to `python -m tools.export_analytics --config ...`
  (NOT `ProcessPoolExecutor` — its semaphores are sandbox-blocked). The
  `make validate` / `make score` calls that follow each export run SERIALLY
  in the driver thread (make invocations are cheap; the analytics side is
  intentionally not parallelized).
- Every batch is scored from its `OUT=` JSON file — never from stdout — and
  no success-bearing subprocess call is ever piped.
- A designated (config, seed) arm is exported a second time, to a scratch
  directory, purely to prove producer determinism (closes an S3 declared
  gap): the two batches' Parquet tables must be equal (excluding
  `exported_at`), and their score canonical payloads equal after masking
  `gate.parquet_sha256` only.
- Raw Parquet is deleted after a successful score (manifest keeps
  seed + config_hash -> any batch is reproducible on demand) unless
  `--keep-raw`.
- Any export/gate/score failure marks that run failed, the sweep continues,
  and the manifest is stamped `sweep_status: "partial"` (a nonzero process
  exit follows). "complete" only when every run — and the rerun check —
  succeeded.

Usage:
    python -m tools.sweep_runner --spec sweep.json [--keep-raw]
        [--rerun-check-index 0]
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools import counterfactual
from tools.counterfactual import CounterfactualConfigError

SCHEMA_VERSION = "1.0.0"
SCORE_AUTHORITY = (
    "scores are reproducibility smoke data only; non-authoritative for "
    "tuning (S3 stop-gate: exploratory-surrogate)"
)
PARQUET_TABLES = ("hands.parquet", "seat_outcomes.parquet", "decisions.parquet")
EXPORTED_AT_COLUMN = "exported_at"
MAX_WORKERS = 5
STDERR_TAIL_CHARS = 4000

BACKEND_DIR = Path(__file__).resolve().parent.parent  # backend/


class SweepSpecError(ValueError):
    """The sweep spec JSON is malformed, or a config/seed set is invalid."""


class SweepRunError(RuntimeError):
    """A sweep-internal invariant failed (e.g. the producer-rerun check)."""


# ---------------------------------------------------------------------------
# Spec
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SweepSpec:
    schema_version: str
    configs: tuple[Path, ...]
    seeds: tuple[int, ...]
    n_hands: int
    out_root: Path
    analytics_repo: Path
    cov_artifact: str | None
    spec_path: Path


def load_spec(path: Path | str) -> SweepSpec:
    """Parse and structurally validate a sweep-spec JSON. Does NOT validate
    the configs themselves (see `validate_configs`) — that step is separate
    so it can run with a clear "N configs validated" boundary."""
    path = Path(path)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SweepSpecError(f"{path}: not valid JSON ({exc})") from exc
    if not isinstance(document, dict):
        raise SweepSpecError(f"{path}: sweep spec must be a JSON object")

    required = ("schema_version", "configs", "seeds", "n_hands", "out_root",
                "analytics_repo")
    missing = [k for k in required if k not in document]
    if missing:
        raise SweepSpecError(f"{path}: missing required field(s): {missing}")

    configs_raw = document["configs"]
    if not isinstance(configs_raw, list) or not configs_raw:
        raise SweepSpecError(f"{path}: `configs` must be a non-empty list of paths")
    base_dir = path.resolve().parent
    configs = tuple(
        (base_dir / c).resolve() if not Path(c).is_absolute() else Path(c)
        for c in configs_raw
    )

    seeds_raw = document["seeds"]
    if not isinstance(seeds_raw, list) or not seeds_raw or not all(
        isinstance(s, int) and not isinstance(s, bool) for s in seeds_raw
    ):
        raise SweepSpecError(f"{path}: `seeds` must be a non-empty list of ints")
    if len(set(seeds_raw)) != len(seeds_raw):
        raise SweepSpecError(f"{path}: `seeds` contains duplicates")
    seeds = tuple(seeds_raw)

    n_hands = document["n_hands"]
    if not isinstance(n_hands, int) or isinstance(n_hands, bool) or n_hands <= 0:
        raise SweepSpecError(f"{path}: `n_hands` must be a positive int")

    out_root = Path(document["out_root"])
    analytics_repo = Path(document["analytics_repo"])
    cov_artifact = document.get("cov_artifact")
    if cov_artifact is not None and not isinstance(cov_artifact, str):
        raise SweepSpecError(f"{path}: `cov_artifact` must be a string when present")

    return SweepSpec(
        schema_version=document["schema_version"],
        configs=configs,
        seeds=seeds,
        n_hands=n_hands,
        out_root=out_root,
        analytics_repo=analytics_repo,
        cov_artifact=cov_artifact,
        spec_path=path,
    )


def validate_configs(configs: tuple[Path, ...]) -> list[tuple[Path, str]]:
    """Validate every config via `counterfactual.load_config` BEFORE any
    export runs. Returns `[(config_path, config_hash), ...]` in the given
    order. Raises `SweepSpecError` on the first invalid config, or on a
    duplicate `config_hash` across configs (a duplicate sweep arm)."""
    resolved: list[tuple[Path, str]] = []
    seen: dict[str, Path] = {}
    for config_path in configs:
        try:
            validated = counterfactual.load_config(config_path)
        except CounterfactualConfigError as exc:
            raise SweepSpecError(f"{config_path}: invalid counterfactual config: {exc}") from exc
        chash = validated.config_hash
        if chash in seen:
            raise SweepSpecError(
                f"{config_path}: config_hash {chash} duplicates {seen[chash]} "
                f"(duplicate sweep arm)"
            )
        seen[chash] = config_path
        resolved.append((config_path, chash))
    return resolved


# ---------------------------------------------------------------------------
# Work items
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunItem:
    index: int
    config_path: Path
    config_hash: str
    seed: int
    n_hands: int
    out_dir: Path
    kind: str = "primary"  # "primary" | "rerun_dup"


def build_items(spec: SweepSpec, resolved_configs: list[tuple[Path, str]]) -> list[RunItem]:
    """Config-major, seed-minor ordering — deterministic and used both for
    directory naming and for `--rerun-check-index` addressing."""
    items = []
    idx = 0
    for config_path, chash in resolved_configs:
        for seed in spec.seeds:
            out_dir = spec.out_root / f"run-{idx:03d}-c{chash[:12]}-s{seed}"
            items.append(RunItem(idx, config_path, chash, seed, spec.n_hands, out_dir))
            idx += 1
    return items


def build_rerun_dup_item(designated: RunItem) -> RunItem:
    scratch = designated.out_dir.parent / "_rerun_check" / (
        f"dup-c{designated.config_hash[:12]}-s{designated.seed}"
    )
    return RunItem(-1, designated.config_path, designated.config_hash,
                   designated.seed, designated.n_hands, scratch, kind="rerun_dup")


# ---------------------------------------------------------------------------
# Subprocess wrappers (mocked in unit tests — the only I/O boundary)
# ---------------------------------------------------------------------------


def _export_subprocess(item: RunItem) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable, "-m", "tools.export_analytics",
        "--hands", str(item.n_hands), "--seed", str(item.seed),
        "--out", str(item.out_dir), "--config", str(item.config_path),
        "--skip-contract-test",
    ]
    return subprocess.run(cmd, cwd=str(BACKEND_DIR), capture_output=True, text=True)


def _make_subprocess(analytics_repo: Path, args: list[str]) -> subprocess.CompletedProcess:
    cmd = ["make", *args]
    return subprocess.run(cmd, cwd=str(analytics_repo), capture_output=True, text=True)


def _make_validate(analytics_repo: Path, batch_dir: Path) -> subprocess.CompletedProcess:
    return _make_subprocess(analytics_repo, [f"DIR={batch_dir}", "validate"])


def _make_score(analytics_repo: Path, batch_dir: Path, out_file: Path,
                cov: str | None) -> subprocess.CompletedProcess:
    args = [f"DIR={batch_dir}", f"OUT={out_file}"]
    if cov is not None:
        args.append(f"COV={cov}")
    args.append("score")
    return _make_subprocess(analytics_repo, args)


def _stderr_tail(cp: subprocess.CompletedProcess) -> str:
    text = (cp.stderr or "") + (("\n" + cp.stdout) if cp.stdout else "")
    return text[-STDERR_TAIL_CHARS:]


# ---------------------------------------------------------------------------
# Parquet comparison (rerun check, part a)
# ---------------------------------------------------------------------------


def _drop_column(table: Any, column: str) -> Any:
    if column in table.column_names:
        return table.drop([column])
    return table


def tables_equal(a: Any, b: Any, drop_column: str = EXPORTED_AT_COLUMN) -> bool:
    """Two pyarrow Tables are equal after dropping `drop_column` (order and
    all other content must match)."""
    return _drop_column(a, drop_column).equals(_drop_column(b, drop_column))


def parquet_batches_equal(dir_a: Path, dir_b: Path,
                          tables: tuple[str, ...] = PARQUET_TABLES) -> bool:
    import pyarrow.parquet as pq

    for name in tables:
        ta = pq.read_table(dir_a / name)
        tb = pq.read_table(dir_b / name)
        if not tables_equal(ta, tb):
            return False
    return True


# ---------------------------------------------------------------------------
# Score-payload masking (rerun check, part b)
# ---------------------------------------------------------------------------


def mask_gate_hash(canonical: dict) -> dict:
    """Deep-copy `canonical` with `gate.parquet_sha256` masked (the ONE field
    the producer-rerun check is allowed to differ on — two independent
    exports at the same seed necessarily write different raw bytes even when
    their logical content is identical)."""
    masked = copy.deepcopy(canonical)
    gate = masked.get("gate")
    if isinstance(gate, dict) and "parquet_sha256" in gate:
        gate["parquet_sha256"] = None
    return masked


def score_payloads_equal_ignoring_gate_hash(a: dict, b: dict) -> bool:
    return mask_gate_hash(a) == mask_gate_hash(b)


# ---------------------------------------------------------------------------
# Per-run pipeline (validate -> score -> retire raw), run serially
# ---------------------------------------------------------------------------


@dataclass
class RunOutcome:
    item: RunItem
    status: str  # "ok" | "failed"
    run_id: str | None = None
    score_payload: dict | None = None
    stderr_tail: str | None = None
    wall_seconds: float = 0.0
    failed_step: str | None = None  # "export" | "validate" | "score"


def _score_batch(spec: SweepSpec, item: RunItem, export_cp: subprocess.CompletedProcess,
                 keep_raw: bool) -> RunOutcome:
    started = time.monotonic()
    if export_cp.returncode != 0:
        return RunOutcome(item, "failed", stderr_tail=_stderr_tail(export_cp),
                          wall_seconds=time.monotonic() - started, failed_step="export")

    success_path = item.out_dir / "_SUCCESS"
    try:
        manifest = json.loads(success_path.read_text(encoding="utf-8"))
        run_id = manifest["run_id"]
    except Exception as exc:  # noqa: BLE001 - fail-closed on any manifest defect
        return RunOutcome(item, "failed", stderr_tail=f"_SUCCESS unreadable: {exc}",
                          wall_seconds=time.monotonic() - started, failed_step="export")

    validate_cp = _make_validate(spec.analytics_repo, item.out_dir)
    if validate_cp.returncode != 0:
        return RunOutcome(item, "failed", run_id=run_id, stderr_tail=_stderr_tail(validate_cp),
                          wall_seconds=time.monotonic() - started, failed_step="validate")

    score_out = item.out_dir / "score.json"
    cov = spec.cov_artifact
    score_cp = _make_score(spec.analytics_repo, item.out_dir, score_out, cov)
    if score_cp.returncode != 0:
        return RunOutcome(item, "failed", run_id=run_id, stderr_tail=_stderr_tail(score_cp),
                          wall_seconds=time.monotonic() - started, failed_step="score")

    try:
        payload = json.loads(score_out.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return RunOutcome(item, "failed", run_id=run_id, stderr_tail=f"score OUT unreadable: {exc}",
                          wall_seconds=time.monotonic() - started, failed_step="score")

    outcome = RunOutcome(item, "ok", run_id=run_id, score_payload=payload,
                         wall_seconds=time.monotonic() - started)
    if not keep_raw and item.kind == "primary":
        _delete_raw_parquet(item.out_dir)
    return outcome


def _delete_raw_parquet(batch_dir: Path) -> None:
    for name in PARQUET_TABLES:
        (batch_dir / name).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


def _run_canonical_entry(outcome: RunOutcome) -> dict[str, Any]:
    item = outcome.item
    entry: dict[str, Any] = {
        "config_hash": item.config_hash,
        "seed": item.seed,
        "n_hands": item.n_hands,
        "run_id": outcome.run_id,
        "run_status": outcome.status,
    }
    payload = outcome.score_payload
    if payload is not None:
        canonical = payload["canonical"]
        entry["engine_git_sha"] = canonical["producer_run"]["engine_git_sha"]
        entry["scorer_version"] = canonical["scorer_version"]
        entry["registry_version"] = canonical["registry"]["version"]
        entry["registry_sha256"] = canonical["registry"]["content_sha256"]
        entry["stat_definition_version"] = canonical["registry"]["stat_definition_version"]
        entry["score_canonical_sha256"] = payload["canonical_sha256"]
        entry["score_status"] = canonical["score_status"]
    else:
        entry["engine_git_sha"] = None
        entry["scorer_version"] = None
        entry["registry_version"] = None
        entry["registry_sha256"] = None
        entry["stat_definition_version"] = None
        entry["score_canonical_sha256"] = None
        entry["score_status"] = None
    return entry


def build_manifest(spec: SweepSpec, resolved_configs: list[tuple[Path, str]],
                   outcomes: list[RunOutcome], rerun_check: dict[str, Any],
                   sweep_status: str) -> dict[str, Any]:
    cov_artifact_id = None
    for outcome in outcomes:
        if outcome.score_payload is not None:
            cov_artifact_id = outcome.score_payload["canonical"]["covariance_artifact"]["id"]
            break

    runs = [_run_canonical_entry(o) for o in outcomes]

    canonical = {
        "schema_version": spec.schema_version,
        "configs": [chash for _, chash in resolved_configs],
        "seeds": list(spec.seeds),
        "n_hands": spec.n_hands,
        "covariance_artifact_id": cov_artifact_id,
        "score_authority": SCORE_AUTHORITY,
        "sweep_status": sweep_status,
        "producer_rerun_check": {
            "config_hash": rerun_check["config_hash"],
            "seed": rerun_check["seed"],
            "parquet_equal": rerun_check["parquet_equal"],
            "score_equal": rerun_check["score_equal"],
            "passed": rerun_check["passed"],
        },
        "runs": runs,
    }
    canonical_bytes = counterfactual.canonical_bytes(canonical)
    import hashlib
    canonical_sha256 = hashlib.sha256(canonical_bytes).hexdigest()

    volatile_runs = []
    for outcome in outcomes:
        volatile_runs.append({
            "config_hash": outcome.item.config_hash,
            "seed": outcome.item.seed,
            "run_dir": str(outcome.item.out_dir),
            "wall_seconds": round(outcome.wall_seconds, 3),
            "stderr_tail": outcome.stderr_tail,
            "failed_step": outcome.failed_step,
        })

    volatile = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "spec_path": str(spec.spec_path),
        "out_root": str(spec.out_root),
        "analytics_repo": str(spec.analytics_repo),
        "canonical_sha256": canonical_sha256,
        "runs": volatile_runs,
        "producer_rerun_check": {
            "run_dir": str(rerun_check["run_dir"]),
            "dup_dir": str(rerun_check["dup_dir"]),
        },
    }
    return {"canonical": canonical, "volatile": volatile}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_sweep(spec: SweepSpec, keep_raw: bool = False,
             rerun_check_index: int = 0) -> dict[str, Any]:
    resolved_configs = validate_configs(spec.configs)  # fail closed, up front
    items = build_items(spec, resolved_configs)
    if not (0 <= rerun_check_index < len(items)):
        raise SweepSpecError(
            f"--rerun-check-index {rerun_check_index} out of range "
            f"(sweep has {len(items)} (config, seed) arms)"
        )
    designated = items[rerun_check_index]
    dup_item = build_rerun_dup_item(designated)

    spec.out_root.mkdir(parents=True, exist_ok=True)

    # Phase A: parallel export (bounded 5 workers), all arms + the rerun dup.
    export_results: dict[int, subprocess.CompletedProcess] = {}
    all_export_items = [*items, dup_item]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(_export_subprocess, it): it for it in all_export_items}
        for future in as_completed(futures):
            it = futures[future]
            export_results[it.index if it.kind == "primary" else -1] = future.result()
    dup_export_cp = export_results.pop(-1)

    # Phase B: serial validate + score in the driver.
    outcomes: list[RunOutcome] = []
    designated_outcome: RunOutcome | None = None
    for item in items:
        keep = keep_raw or item.index == designated.index  # keep designated raw
        # until the rerun check below has run.
        outcome = _score_batch(spec, item, export_results[item.index], keep)
        outcomes.append(outcome)
        if item.index == designated.index:
            designated_outcome = outcome

    dup_outcome = _score_batch(spec, dup_item, dup_export_cp, keep_raw=True)

    # Producer-rerun check.
    rerun_check = {
        "config_hash": designated.config_hash,
        "seed": designated.seed,
        "run_dir": designated.out_dir,
        "dup_dir": dup_item.out_dir,
        "parquet_equal": False,
        "score_equal": False,
        "passed": False,
    }
    assert designated_outcome is not None
    if designated_outcome.status == "ok" and dup_outcome.status == "ok":
        try:
            rerun_check["parquet_equal"] = parquet_batches_equal(
                designated.out_dir, dup_item.out_dir)
        except Exception as exc:  # noqa: BLE001 - fail closed
            rerun_check["parquet_equal"] = False
            rerun_check["error"] = f"parquet compare failed: {exc}"
        rerun_check["score_equal"] = score_payloads_equal_ignoring_gate_hash(
            designated_outcome.score_payload["canonical"],
            dup_outcome.score_payload["canonical"],
        )
    rerun_check["passed"] = rerun_check["parquet_equal"] and rerun_check["score_equal"]

    if not rerun_check["passed"]:
        designated_outcome.status = "failed"
        designated_outcome.failed_step = designated_outcome.failed_step or "rerun_check"

    # Raw-data retirement for the designated run (deferred until now).
    if not keep_raw:
        _delete_raw_parquet(designated.out_dir)
    if not keep_raw and dup_item.out_dir.exists():
        shutil.rmtree(dup_item.out_dir, ignore_errors=True)
        rerun_dir = dup_item.out_dir.parent
        if rerun_dir.exists() and not any(rerun_dir.iterdir()):
            rerun_dir.rmdir()

    sweep_status = (
        "complete"
        if rerun_check["passed"] and all(o.status == "ok" for o in outcomes)
        else "partial"
    )

    manifest = build_manifest(spec, resolved_configs, outcomes, rerun_check, sweep_status)
    return manifest


def write_manifest(spec: SweepSpec, manifest: dict[str, Any]) -> Path:
    out_path = spec.out_root / "sweep_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", type=Path, required=True,
                    help="sweep-spec JSON (schema_version, configs, seeds, "
                         "n_hands, out_root, analytics_repo[, cov_artifact])")
    ap.add_argument("--keep-raw", action="store_true",
                    help="do not delete raw Parquet after a successful score")
    ap.add_argument("--rerun-check-index", type=int, default=0,
                    help="index (config-major, seed-minor) of the (config, "
                         "seed) arm to export twice for the producer-rerun "
                         "determinism check")
    args = ap.parse_args()

    try:
        spec = load_spec(args.spec)
        manifest = run_sweep(spec, keep_raw=args.keep_raw,
                             rerun_check_index=args.rerun_check_index)
    except (SweepSpecError, SweepRunError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    out_path = write_manifest(spec, manifest)
    status = manifest["canonical"]["sweep_status"]
    print(f"sweep_status: {status}")
    print(f"manifest: {out_path}")
    if status != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
