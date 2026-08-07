"""The batch sweep runner (flywheel S4 T5) — the "one command."

N counterfactual configs (`backend/tools/counterfactual.py`) x one shared
seed list -> N validated exports (`backend/tools/export_analytics.py`) -> N
gated+scored batches in poker-analytics -> one pinned `sweep_manifest.json`.

Design (spec `docs/ai-dlc/specs/flywheel-s4.md`, "Design rulings"):

- ALL configs are validated up front (`counterfactual.load_config`) before any
  export runs — one bad config fails the whole sweep before simulation money
  is spent. Duplicate `config_hash` across configs is a sweep-spec error.
  `analytics_repo` (must be a directory with a `Makefile`), `cov_artifact`
  (required — every `make score` call pins an explicit covariance artifact,
  never the Makefile default), and `out_root`'s writability are also checked
  at spec-load time, before any simulation runs.
- Exports run with bounded 5-worker parallelism: a `ThreadPoolExecutor` whose
  workers each shell out to `python -m tools.export_analytics --config ...`
  (NOT `ProcessPoolExecutor` — its semaphores are sandbox-blocked). The
  `make validate` / `make score` calls that follow each export run SERIALLY
  in the driver thread (make invocations are cheap; the analytics side is
  intentionally not parallelized).
- Every batch is scored from its `OUT=` JSON file — never from stdout — and
  no success-bearing subprocess call is ever piped. `score.json` is unlinked
  before every `make score` invocation (a stale leftover file must never be
  mistaken for a fresh result), and a fresh regular file is required after.
- FAIL-CLOSED, including on UNEXPECTED failures, not just expected ones: a
  worker exception, a launch error (`make`/the analytics repo missing), a
  malformed or self-inconsistent score payload, or an identity mismatch
  between what was requested and what `_SUCCESS`/the score payload actually
  describe, all mark that one run "failed" (with a captured traceback or
  stderr tail) and let the sweep continue — never an unhandled crash with no
  manifest. `main()` carries a last-resort safety net: even an exception that
  somehow escapes every inner guard still lands a labeled, partial manifest
  before a nonzero exit.
- A designated (config, seed) arm is exported a second time, to a scratch
  directory, purely to prove producer determinism (closes an S3 declared
  gap): the two batches' Parquet tables must be equal (excluding
  `exported_at`), and their score canonical payloads equal (compared as
  canonical BYTES, not Python dict equality — `1 == 1.0` in Python but they
  serialize differently, and the byte claim is what matters) after masking
  `gate.parquet_sha256` only. The dup batch's own pipeline outcome (status,
  failed step, stderr tail) is recorded too, so a dup-side `make` failure
  reads as "dup pipeline failed" rather than a false "batches differ" verdict
  accusing the engine of nondeterminism.
- Raw Parquet is deleted after a successful score (manifest keeps
  seed + config_hash -> any batch is reproducible on demand) unless
  `--keep-raw`. Deletion of the rerun-check pair (designated + dup) is gated
  on the WHOLE check having passed — on any failure, BOTH directories are
  retained for post-mortem, never destroyed.
- `lineup` (an optional sweep-spec field, forwarded verbatim as
  `--lineup` to every export — including the rerun-dup) is
  IDENTITY-BEARING: it is resolved once (mirroring the exporter's own
  9-seat wrap) and recorded in the manifest's canonical section; every
  batch's `_SUCCESS` and score `producer_run` are cross-checked against the
  requested arm on `{config_hash, seed, n_hands, run_id, lineup}` and the run
  fails closed on any disagreement (a config edited after prevalidation, or a
  wrong-seed/wrong-lineup export, must never silently read as "complete").
  Omitted -> the exporter's own default, unchanged.
- Any export/identity/validate/score failure marks that run failed, the
  sweep continues, and the manifest is stamped `sweep_status: "partial"` (a
  nonzero process exit follows). "complete" only when every run — and the
  rerun check — succeeded.

Usage:
    python -m tools.sweep_runner --spec sweep.json [--keep-raw]
        [--rerun-check-index 0]
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
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
# Three-part semver, no leading zeros (matches counterfactual.py's §c.1 reading).
_SEMVER = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")

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
    cov_artifact: str
    lineup: str | None
    spec_path: Path


def load_spec(path: Path | str) -> SweepSpec:
    """Parse and structurally validate a sweep-spec JSON. Does NOT validate
    the configs themselves (see `validate_configs`) — that step is separate
    so it can run with a clear "N configs validated" boundary.

    Validates, up front (before ANY simulation runs): every required field is
    present and well-typed; `schema_version` is a strict three-part semver;
    `analytics_repo` is a real directory with a `Makefile` in it (a
    nonexistent/wrong repo must be caught here, not mid-sweep as a launch
    crash); `cov_artifact` is present and non-empty (the spec's own binding
    ruling: "always explicit OUT and COV" — never the Makefile default);
    `out_root`'s parent exists and is writable.
    """
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

    schema_version = document["schema_version"]
    if not isinstance(schema_version, str) or not _SEMVER.fullmatch(schema_version):
        raise SweepSpecError(
            f"{path}: `schema_version` {schema_version!r} is not a three-part "
            f"semver string MAJOR.MINOR.PATCH"
        )

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

    analytics_repo = Path(document["analytics_repo"])
    if not analytics_repo.is_dir():
        raise SweepSpecError(
            f"{path}: analytics_repo {analytics_repo} is not a directory — "
            f"refusing before any export runs"
        )
    if not (analytics_repo / "Makefile").is_file():
        raise SweepSpecError(
            f"{path}: analytics_repo {analytics_repo} has no Makefile — not a "
            f"poker-analytics checkout"
        )

    out_root = Path(document["out_root"])
    out_root_parent = out_root.parent
    if not out_root_parent.is_dir() or not os.access(out_root_parent, os.W_OK):
        raise SweepSpecError(
            f"{path}: out_root's parent {out_root_parent} does not exist or "
            f"is not writable"
        )

    cov_artifact = document.get("cov_artifact")
    if not isinstance(cov_artifact, str) or not cov_artifact:
        raise SweepSpecError(
            f"{path}: `cov_artifact` is required and must be a non-empty "
            f"string — the spec's binding ruling is \"always explicit OUT "
            f"and COV\" (never the Makefile's default artifact)"
        )

    lineup_raw = document.get("lineup")
    if lineup_raw is None:
        lineup = None
    elif isinstance(lineup_raw, str):
        lineup = lineup_raw
    elif isinstance(lineup_raw, list) and lineup_raw and all(
        isinstance(x, str) for x in lineup_raw
    ):
        # Normalize to the exporter's `--lineup` comma-separated format.
        lineup = ",".join(lineup_raw)
    else:
        raise SweepSpecError(
            f"{path}: `lineup` must be a comma-separated string or a list of "
            f"persona-name strings when present"
        )

    return SweepSpec(
        schema_version=schema_version,
        configs=configs,
        seeds=seeds,
        n_hands=n_hands,
        out_root=out_root,
        analytics_repo=analytics_repo,
        cov_artifact=cov_artifact,
        lineup=lineup,
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
    lineup: str | None = None
    kind: str = "primary"  # "primary" | "rerun_dup"


def build_items(spec: SweepSpec, resolved_configs: list[tuple[Path, str]]) -> list[RunItem]:
    """Config-major, seed-minor ordering — deterministic and used both for
    directory naming and for `--rerun-check-index` addressing."""
    items = []
    idx = 0
    for config_path, chash in resolved_configs:
        for seed in spec.seeds:
            out_dir = spec.out_root / f"run-{idx:03d}-c{chash[:12]}-s{seed}"
            items.append(RunItem(idx, config_path, chash, seed, spec.n_hands, out_dir,
                                 lineup=spec.lineup))
            idx += 1
    return items


def build_rerun_dup_item(designated: RunItem) -> RunItem:
    scratch = designated.out_dir.parent / "_rerun_check" / (
        f"dup-c{designated.config_hash[:12]}-s{designated.seed}"
    )
    return RunItem(-1, designated.config_path, designated.config_hash,
                   designated.seed, designated.n_hands, scratch,
                   lineup=designated.lineup, kind="rerun_dup")


def resolve_lineup_dict(lineup: str | None) -> dict[str, str]:
    """Mirror `export_analytics.py`'s `persona_by_seat` resolution (split on
    comma, wrap to 9 seats) so the sweep can cross-check every `_SUCCESS`
    against the SAME "what does this lineup mean" the exporter used —
    without importing/duplicating the exporter's private logic. `lineup=None`
    resolves against `DEFAULT_LINEUP`, matching the exporter's own default
    path."""
    from tools.export_analytics import DEFAULT_LINEUP

    names = lineup.split(",") if lineup else DEFAULT_LINEUP
    return {str(i): names[i % len(names)] for i in range(9)}


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
    if item.lineup is not None:
        cmd += ["--lineup", item.lineup]
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
    """Compare via CANONICAL BYTES, not Python dict equality — `1 == 1.0` is
    `True` in Python but the two serialize to different JSON, and the claim
    this function proves ("scored twice, byte-identical") is a claim about
    bytes."""
    return (counterfactual.canonical_bytes(mask_gate_hash(a))
            == counterfactual.canonical_bytes(mask_gate_hash(b)))


# ---------------------------------------------------------------------------
# Score-payload / identity validation
# ---------------------------------------------------------------------------


def _validate_score_payload(payload: Any) -> str | None:
    """Structural + self-consistency check on a `make score` OUT payload.

    "ok" must mean USABLE, not merely "parsed as JSON" — a `{}` OUT file
    parses fine but has no `canonical`, and a payload can claim a
    `canonical_sha256` that does not match its own `canonical` object (a
    truncated write, a hand-edited file, a scorer regression). Returns an
    error string on any problem, `None` when the payload is trustworthy.
    """
    if not isinstance(payload, dict):
        return f"score payload is not a JSON object (got {type(payload).__name__})"
    canonical = payload.get("canonical")
    if not isinstance(canonical, dict):
        return "score payload has no `canonical` object"
    claimed = payload.get("canonical_sha256")
    if not isinstance(claimed, str):
        return "score payload has no `canonical_sha256` string"
    recomputed = hashlib.sha256(counterfactual.canonical_bytes(canonical)).hexdigest()
    if recomputed != claimed:
        return (
            f"score payload's claimed canonical_sha256 {claimed!r} does not "
            f"match the hash recomputed over its own `canonical` object "
            f"({recomputed!r}) — the payload is internally inconsistent"
        )
    if not isinstance(canonical.get("producer_run"), dict):
        return "score payload's canonical.producer_run is missing or not an object"
    return None


def _identity_mismatches(manifest_like: dict, item: RunItem, canonical_lineup: dict[str, str],
                         source: str, expected_run_id: str | None = None) -> list[str]:
    """Cross-check a `_SUCCESS` manifest (or a score payload's
    `producer_run`) against the arm that was actually requested. A config
    edited after prevalidation, a wrong-seed export, or a stale/foreign batch
    directory must never silently read as "complete" — it must fail this one
    run, explicitly, with the disagreement named.
    """
    problems = []
    if manifest_like.get("seed") != item.seed:
        problems.append(f"{source}.seed {manifest_like.get('seed')!r} != requested {item.seed!r}")
    if manifest_like.get("n_hands") != item.n_hands:
        problems.append(
            f"{source}.n_hands {manifest_like.get('n_hands')!r} != requested {item.n_hands!r}")
    if manifest_like.get("config_hash") != item.config_hash:
        problems.append(
            f"{source}.config_hash {manifest_like.get('config_hash')!r} != "
            f"requested {item.config_hash!r}"
        )
    if manifest_like.get("lineup") != canonical_lineup:
        problems.append(
            f"{source}.lineup does not match the sweep's canonical lineup "
            f"(identity-bearing — drives the covariance artifact match)"
        )
    if expected_run_id is not None and manifest_like.get("run_id") != expected_run_id:
        problems.append(
            f"{source}.run_id {manifest_like.get('run_id')!r} != expected {expected_run_id!r}")
    return problems


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
    # "export" | "identity_mismatch" | "validate" | "score" |
    # "score_payload_invalid" | "rerun_check" | "crash"
    failed_step: str | None = None


def _score_batch(spec: SweepSpec, item: RunItem, export_cp: subprocess.CompletedProcess,
                 keep_raw: bool, canonical_lineup: dict[str, str]) -> RunOutcome:
    started = time.monotonic()
    if export_cp.returncode != 0:
        return RunOutcome(item, "failed", stderr_tail=_stderr_tail(export_cp),
                          wall_seconds=time.monotonic() - started, failed_step="export")
    try:
        return _score_batch_body(spec, item, keep_raw, canonical_lineup, started)
    except Exception:  # noqa: BLE001 - fail-closed: NO unhandled exception may abort the sweep
        return RunOutcome(
            item, "failed", stderr_tail=traceback.format_exc()[-STDERR_TAIL_CHARS:],
            wall_seconds=time.monotonic() - started, failed_step="crash")


def _score_batch_body(spec: SweepSpec, item: RunItem, keep_raw: bool,
                      canonical_lineup: dict[str, str], started: float) -> RunOutcome:
    success_path = item.out_dir / "_SUCCESS"
    try:
        success_manifest = json.loads(success_path.read_text(encoding="utf-8"))
        run_id = success_manifest["run_id"]
    except Exception as exc:  # noqa: BLE001 - fail-closed on any manifest defect
        return RunOutcome(item, "failed", stderr_tail=f"_SUCCESS unreadable: {exc}",
                          wall_seconds=time.monotonic() - started, failed_step="export")

    mismatches = _identity_mismatches(success_manifest, item, canonical_lineup, "_SUCCESS")
    if mismatches:
        return RunOutcome(item, "failed", run_id=run_id, stderr_tail="; ".join(mismatches),
                          wall_seconds=time.monotonic() - started, failed_step="identity_mismatch")

    validate_cp = _make_validate(spec.analytics_repo, item.out_dir)
    if validate_cp.returncode != 0:
        return RunOutcome(item, "failed", run_id=run_id, stderr_tail=_stderr_tail(validate_cp),
                          wall_seconds=time.monotonic() - started, failed_step="validate")

    score_out = item.out_dir / "score.json"
    score_out.unlink(missing_ok=True)  # never trust a stale leftover OUT file
    score_cp = _make_score(spec.analytics_repo, item.out_dir, score_out, spec.cov_artifact)
    if score_cp.returncode != 0:
        return RunOutcome(item, "failed", run_id=run_id, stderr_tail=_stderr_tail(score_cp),
                          wall_seconds=time.monotonic() - started, failed_step="score")
    if not score_out.is_file():
        return RunOutcome(
            item, "failed", run_id=run_id,
            stderr_tail=f"make score exited 0 but {score_out} was not written",
            wall_seconds=time.monotonic() - started, failed_step="score")

    try:
        payload = json.loads(score_out.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return RunOutcome(item, "failed", run_id=run_id, stderr_tail=f"score OUT unreadable: {exc}",
                          wall_seconds=time.monotonic() - started, failed_step="score")

    payload_error = _validate_score_payload(payload)
    if payload_error:
        return RunOutcome(item, "failed", run_id=run_id, stderr_tail=payload_error,
                          wall_seconds=time.monotonic() - started,
                          failed_step="score_payload_invalid")

    producer_run = payload["canonical"]["producer_run"]
    mismatches = _identity_mismatches(producer_run, item, canonical_lineup, "score producer_run",
                                      expected_run_id=run_id)
    if mismatches:
        return RunOutcome(item, "failed", run_id=run_id, stderr_tail="; ".join(mismatches),
                          wall_seconds=time.monotonic() - started, failed_step="identity_mismatch")

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
                   sweep_status: str, canonical_lineup: dict[str, str]) -> dict[str, Any]:
    cov_artifact_id = None
    for outcome in outcomes:
        if outcome.score_payload is not None:
            cov_artifact_id = outcome.score_payload["canonical"]["covariance_artifact"]["id"]
            break

    runs = [_run_canonical_entry(o) for o in outcomes]

    canonical = {
        # The MODULE's manifest-schema constant, never the spec author's
        # unvalidated `schema_version` value — the two are different
        # identities (what the user's spec claims to conform to vs. what
        # shape this manifest actually is).
        "schema_version": SCHEMA_VERSION,
        "configs": [chash for _, chash in resolved_configs],
        "seeds": list(spec.seeds),
        "n_hands": spec.n_hands,
        "lineup": canonical_lineup,
        "covariance_artifact_id": cov_artifact_id,
        "score_authority": SCORE_AUTHORITY,
        "sweep_status": sweep_status,
        "producer_rerun_check": {
            "config_hash": rerun_check["config_hash"],
            "seed": rerun_check["seed"],
            "parquet_equal": rerun_check["parquet_equal"],
            "score_equal": rerun_check["score_equal"],
            "passed": rerun_check["passed"],
            # "passed" | "batches_differ" | "designated_pipeline_failed" |
            # "dup_pipeline_failed" | "crash"
            "check_status": rerun_check["check_status"],
        },
        "runs": runs,
    }
    canonical_sha256 = hashlib.sha256(counterfactual.canonical_bytes(canonical)).hexdigest()

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
            "run_dir": str(rerun_check["run_dir"]) if rerun_check["run_dir"] is not None else None,
            "dup_dir": str(rerun_check["dup_dir"]) if rerun_check["dup_dir"] is not None else None,
            "dup_status": rerun_check.get("dup_status"),
            "dup_failed_step": rerun_check.get("dup_failed_step"),
            "dup_stderr_tail": rerun_check.get("dup_stderr_tail"),
        },
    }
    return {"canonical": canonical, "volatile": volatile}


def _crash_manifest(spec: SweepSpec, tb_text: str) -> dict[str, Any]:
    """Last-resort manifest for an exception that escaped `run_sweep` itself
    (every INNER failure mode is already caught closer to its source — this
    is the outermost net, for the fixed idea "no crash ever produces zero
    manifest"). Always `sweep_status: "partial"`."""
    canonical = {
        "schema_version": SCHEMA_VERSION,
        "configs": [],
        "seeds": list(spec.seeds),
        "n_hands": spec.n_hands,
        "lineup": resolve_lineup_dict(spec.lineup),
        "covariance_artifact_id": None,
        "score_authority": SCORE_AUTHORITY,
        "sweep_status": "partial",
        "producer_rerun_check": {
            "config_hash": None, "seed": None, "parquet_equal": False,
            "score_equal": False, "passed": False, "check_status": "crash",
        },
        "runs": [],
    }
    canonical_sha256 = hashlib.sha256(counterfactual.canonical_bytes(canonical)).hexdigest()
    volatile = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "spec_path": str(spec.spec_path),
        "out_root": str(spec.out_root),
        "analytics_repo": str(spec.analytics_repo),
        "canonical_sha256": canonical_sha256,
        "runs": [],
        "producer_rerun_check": {"run_dir": None, "dup_dir": None, "dup_status": None,
                                 "dup_failed_step": None, "dup_stderr_tail": None},
        "crash_traceback_tail": tb_text[-STDERR_TAIL_CHARS:],
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
    canonical_lineup = resolve_lineup_dict(spec.lineup)

    spec.out_root.mkdir(parents=True, exist_ok=True)

    # Phase A: parallel export (bounded 5 workers), all arms + the rerun dup.
    # A worker exception (not just a nonzero export) must not abort the
    # sweep — it is converted into a synthetic failed CompletedProcess so
    # phase B's ordinary "export failed" path handles it uniformly.
    export_results: dict[int, subprocess.CompletedProcess] = {}
    all_export_items = [*items, dup_item]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(_export_subprocess, it): it for it in all_export_items}
        for future in as_completed(futures):
            it = futures[future]
            try:
                cp = future.result()
            except Exception:  # noqa: BLE001 - fail-closed
                cp = subprocess.CompletedProcess(
                    args=[], returncode=1, stdout="",
                    stderr=f"export worker raised an exception:\n{traceback.format_exc()}",
                )
            export_results[it.index if it.kind == "primary" else -1] = cp
    dup_export_cp = export_results.pop(-1)

    # Phase B: serial validate + score in the driver. `_score_batch` already
    # catches everything internally (see its own try/except) — nothing here
    # can raise.
    outcomes: list[RunOutcome] = []
    for item in items:
        keep = keep_raw or item.index == designated.index  # keep designated raw
        # until the rerun check below has run.
        outcome = _score_batch(spec, item, export_results[item.index], keep, canonical_lineup)
        outcomes.append(outcome)
    designated_outcome = outcomes[rerun_check_index]

    dup_outcome = _score_batch(spec, dup_item, dup_export_cp, True, canonical_lineup)

    # Producer-rerun check — also fail-closed: an exception here (e.g. a
    # corrupt Parquet file) marks the check "crash", never propagates.
    rerun_check: dict[str, Any] = {
        "config_hash": designated.config_hash,
        "seed": designated.seed,
        "run_dir": designated.out_dir,
        "dup_dir": dup_item.out_dir,
        "parquet_equal": False,
        "score_equal": False,
        "passed": False,
        "check_status": "designated_pipeline_failed",
        "dup_status": dup_outcome.status,
        "dup_failed_step": dup_outcome.failed_step,
        "dup_stderr_tail": dup_outcome.stderr_tail,
    }
    try:
        if designated_outcome.status != "ok":
            rerun_check["check_status"] = "designated_pipeline_failed"
        elif dup_outcome.status != "ok":
            rerun_check["check_status"] = "dup_pipeline_failed"
        else:
            rerun_check["parquet_equal"] = parquet_batches_equal(
                designated.out_dir, dup_item.out_dir)
            rerun_check["score_equal"] = score_payloads_equal_ignoring_gate_hash(
                designated_outcome.score_payload["canonical"],
                dup_outcome.score_payload["canonical"],
            )
            rerun_check["check_status"] = (
                "passed" if rerun_check["parquet_equal"] and rerun_check["score_equal"]
                else "batches_differ")
    except Exception:  # noqa: BLE001 - fail-closed
        rerun_check["check_status"] = "crash"
        rerun_check["error"] = traceback.format_exc()[-STDERR_TAIL_CHARS:]
    rerun_check["passed"] = rerun_check["check_status"] == "passed"

    if not rerun_check["passed"] and designated_outcome.status == "ok":
        designated_outcome.status = "failed"
        designated_outcome.failed_step = "rerun_check"

    # Raw-data retirement: gated on the WHOLE rerun check having passed. On
    # any failure (designated failed, dup failed, batches differ, or a crash
    # comparing them), BOTH directories are retained for post-mortem —
    # deleting either would destroy the evidence needed to diagnose it.
    if rerun_check["passed"] and not keep_raw:
        _delete_raw_parquet(designated.out_dir)
        if dup_item.out_dir.exists():
            shutil.rmtree(dup_item.out_dir, ignore_errors=True)
            rerun_dir = dup_item.out_dir.parent
            if rerun_dir.exists() and not any(rerun_dir.iterdir()):
                rerun_dir.rmdir()

    sweep_status = (
        "complete"
        if rerun_check["passed"] and all(o.status == "ok" for o in outcomes)
        else "partial"
    )

    return build_manifest(spec, resolved_configs, outcomes, rerun_check, sweep_status,
                          canonical_lineup)


def write_manifest(spec: SweepSpec, manifest: dict[str, Any]) -> Path:
    spec.out_root.mkdir(parents=True, exist_ok=True)  # crash paths may predate this
    out_path = spec.out_root / "sweep_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", type=Path, required=True,
                    help="sweep-spec JSON (schema_version, configs, seeds, "
                         "n_hands, out_root, analytics_repo, cov_artifact"
                         "[, lineup])")
    ap.add_argument("--keep-raw", action="store_true",
                    help="do not delete raw Parquet after a successful score")
    ap.add_argument("--rerun-check-index", type=int, default=0,
                    help="index (config-major, seed-minor) of the (config, "
                         "seed) arm to export twice for the producer-rerun "
                         "determinism check")
    args = ap.parse_args()

    try:
        spec = load_spec(args.spec)
    except SweepSpecError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    try:
        manifest = run_sweep(spec, keep_raw=args.keep_raw,
                             rerun_check_index=args.rerun_check_index)
    except SweepSpecError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except Exception:  # noqa: BLE001 - last-resort: still land a labeled manifest
        tb_text = traceback.format_exc()
        print(f"ERROR: sweep runner crashed:\n{tb_text}", file=sys.stderr)
        manifest = _crash_manifest(spec, tb_text)

    out_path = write_manifest(spec, manifest)
    status = manifest["canonical"]["sweep_status"]
    print(f"sweep_status: {status}")
    print(f"manifest: {out_path}")
    if status != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
