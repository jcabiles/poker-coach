"""The sweep runner (flywheel S4 T5) — unit-level coverage.

No full simulations here: the subprocess/`make` layer is monkeypatched with
tiny fakes so these tests exercise spec parsing, config validation, manifest
determinism, fail-closed partial labeling (on BOTH expected failures — a
nonzero `make` exit — and unexpected ones — a worker exception, a launch
error, a malformed score payload, an identity mismatch), the authority
stamp, the parquet-drop-column comparison, and the rerun-check masking
logic — all in milliseconds. The real end-to-end mini-sweep (actual
exports, actual `make validate`/`make score`) is a separate, manually-run
acceptance check (see the ticket), not a pytest target.
"""

from __future__ import annotations

import dataclasses
import json
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from tools import sweep_runner as sr  # noqa: E402
from tools.counterfactual import CounterfactualConfigError, ValidatedConfig  # noqa: E402

pa = pytest.importorskip("pyarrow")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _fake_analytics_repo(tmp_path: Path) -> Path:
    """A directory that passes `load_spec`'s "is this poker-analytics"
    check (real dir + `Makefile`), never a real analytics checkout."""
    repo = tmp_path / "analytics"
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "Makefile").write_text("validate:\n\ttrue\nscore:\n\ttrue\n")
    return repo


def _write_spec(tmp_path: Path, **overrides) -> Path:
    cfg_a = tmp_path / "cfg_a.json"
    cfg_b = tmp_path / "cfg_b.json"
    cfg_a.write_text("{}")
    cfg_b.write_text("{}")
    document = {
        "schema_version": "1.0.0",
        "configs": [str(cfg_a), str(cfg_b)],
        "seeds": [501, 502],
        "n_hands": 300,
        "out_root": str(tmp_path / "out"),
        "analytics_repo": str(_fake_analytics_repo(tmp_path)),
        "cov_artifact": "cov-fixture",
    }
    document.update(overrides)
    spec_path = tmp_path / "sweep.json"
    spec_path.write_text(json.dumps(document))
    return spec_path


def _fake_validated_config(config_hash: str) -> ValidatedConfig:
    return ValidatedConfig(
        schema_version="1.0.0", base_pack_hash="x" * 64, overrides={},
        probe_declarations=(), canonical={}, config_hash=config_hash, packs={},
    )


def _cp(returncode: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["x"], returncode=returncode,
                                       stdout=stdout, stderr=stderr)


def _score_payload(config_hash: str, seed: int, n_hands: int, run_id: str, lineup: dict,
                   parquet_sha256: str = "deadbeef") -> dict:
    """A score OUT payload with a REAL, self-consistent `canonical_sha256`
    (recomputed the same way `sweep_runner._validate_score_payload` does) —
    fixtures must satisfy the same self-consistency check production
    payloads do, or every stub run would (correctly) fail closed."""
    canonical = {
        "scorer_version": "1.0.0",
        "score_status": "exploratory-surrogate",
        "registry": {"version": "2.0.0", "content_sha256": "reg" * 10,
                     "stat_definition_version": "statdef-2026-08-06"},
        "covariance_artifact": {"id": "cov-abc123"},
        "producer_run": {"run_id": run_id, "seed": seed, "n_hands": n_hands,
                         "lineup": lineup, "engine_git_sha": "deadc0de",
                         "config_hash": config_hash},
        "gate": {"marker": "_GATE_OK.json", "parquet_sha256": parquet_sha256},
    }
    canonical_sha256 = sr.hashlib.sha256(sr.counterfactual.canonical_bytes(canonical)).hexdigest()
    return {"canonical": canonical, "canonical_sha256": canonical_sha256}


def _stub_pipeline(monkeypatch, config_hashes: dict[Path, str], *, fail_on: str | None = None):
    """Monkeypatch the subprocess boundary: export always "succeeds" (writes
    a fake, IDENTITY-CONSISTENT `_SUCCESS`), `make validate` succeeds,
    `make score` writes a fake, self-consistent score payload to OUT.
    `fail_on` (one of "export"/"validate"/"score") forces exactly one
    primary run (the first) to fail at that step."""
    calls = {"export": 0}

    def fake_load_config(path, packs=None):
        path = Path(path)
        if path not in config_hashes:
            raise CounterfactualConfigError(f"{path}: unknown fixture config")
        return _fake_validated_config(config_hashes[path])

    def fake_export(item: sr.RunItem) -> subprocess.CompletedProcess:
        calls["export"] += 1
        if fail_on == "export" and item.index == 0:
            return _cp(1, stderr="export exploded")
        item.out_dir.mkdir(parents=True, exist_ok=True)
        for name in sr.PARQUET_TABLES:
            (item.out_dir / name).write_bytes(b"parquet-bytes")
        run_id = f"run-s{item.seed}-n{item.n_hands}-c{item.config_hash[:12]}"
        lineup = sr.resolve_lineup_dict(item.lineup)
        success = {"run_id": run_id, "seed": item.seed, "n_hands": item.n_hands,
                  "config_hash": item.config_hash, "lineup": lineup}
        (item.out_dir / "_SUCCESS").write_text(json.dumps(success))
        return _cp(0)

    def fake_validate(analytics_repo, batch_dir) -> subprocess.CompletedProcess:
        # item.index is not visible here; use the batch dir name convention
        # from `fake_export`/dup naming to decide the injected failure.
        if fail_on == "validate" and "run-000-" in str(batch_dir):
            return _cp(1, stderr="validate exploded")
        return _cp(0)

    def fake_score(analytics_repo, batch_dir, out_file, cov) -> subprocess.CompletedProcess:
        if fail_on == "score" and "run-000-" in str(batch_dir):
            return _cp(1, stderr="score exploded")
        success = json.loads((batch_dir / "_SUCCESS").read_text())
        payload = _score_payload(success["config_hash"], success["seed"], success["n_hands"],
                                 success["run_id"], success["lineup"])
        out_file.write_text(json.dumps(payload))
        return _cp(0)

    monkeypatch.setattr(sr.counterfactual, "load_config", fake_load_config)
    monkeypatch.setattr(sr, "_export_subprocess", fake_export)
    monkeypatch.setattr(sr, "_make_validate", fake_validate)
    monkeypatch.setattr(sr, "_make_score", fake_score)
    return calls


# ---------------------------------------------------------------------------
# spec parsing / validation
# ---------------------------------------------------------------------------


def test_load_spec_happy_path(tmp_path):
    spec_path = _write_spec(tmp_path)
    spec = sr.load_spec(spec_path)
    assert spec.n_hands == 300
    assert spec.seeds == (501, 502)
    assert len(spec.configs) == 2
    assert spec.cov_artifact == "cov-fixture"


@pytest.mark.parametrize("field", ["schema_version", "configs", "seeds",
                                   "n_hands", "out_root", "analytics_repo"])
def test_load_spec_missing_field_rejected(tmp_path, field):
    spec_path = tmp_path / "sweep.json"
    document = {
        "schema_version": "1.0.0", "configs": [str(tmp_path / "a.json")],
        "seeds": [1], "n_hands": 10, "out_root": str(tmp_path / "out"),
        "analytics_repo": str(tmp_path / "an"),
    }
    del document[field]
    spec_path.write_text(json.dumps(document))
    with pytest.raises(sr.SweepSpecError):
        sr.load_spec(spec_path)


def test_load_spec_rejects_not_json(tmp_path):
    spec_path = tmp_path / "sweep.json"
    spec_path.write_text("{not json")
    with pytest.raises(sr.SweepSpecError):
        sr.load_spec(spec_path)


def test_load_spec_rejects_empty_configs(tmp_path):
    spec_path = _write_spec(tmp_path, configs=[])
    with pytest.raises(sr.SweepSpecError):
        sr.load_spec(spec_path)


def test_load_spec_rejects_duplicate_seeds(tmp_path):
    spec_path = _write_spec(tmp_path, seeds=[1, 1])
    with pytest.raises(sr.SweepSpecError):
        sr.load_spec(spec_path)


def test_load_spec_rejects_non_positive_n_hands(tmp_path):
    spec_path = _write_spec(tmp_path, n_hands=0)
    with pytest.raises(sr.SweepSpecError):
        sr.load_spec(spec_path)


def test_load_spec_accepts_explicit_cov_artifact(tmp_path):
    spec_path = _write_spec(tmp_path, cov_artifact="cov-deadbeef")
    spec = sr.load_spec(spec_path)
    assert spec.cov_artifact == "cov-deadbeef"


def test_load_spec_requires_cov_artifact_present(tmp_path):
    document = json.loads(_write_spec(tmp_path).read_text())
    del document["cov_artifact"]
    spec_path = tmp_path / "sweep2.json"
    spec_path.write_text(json.dumps(document))
    with pytest.raises(sr.SweepSpecError, match="cov_artifact"):
        sr.load_spec(spec_path)


def test_load_spec_requires_cov_artifact_non_null(tmp_path):
    spec_path = _write_spec(tmp_path, cov_artifact=None)
    with pytest.raises(sr.SweepSpecError, match="cov_artifact"):
        sr.load_spec(spec_path)


def test_load_spec_requires_cov_artifact_non_empty(tmp_path):
    spec_path = _write_spec(tmp_path, cov_artifact="")
    with pytest.raises(sr.SweepSpecError, match="cov_artifact"):
        sr.load_spec(spec_path)


def test_load_spec_rejects_nonexistent_analytics_repo(tmp_path):
    spec_path = _write_spec(tmp_path, analytics_repo=str(tmp_path / "does-not-exist"))
    with pytest.raises(sr.SweepSpecError, match="analytics_repo"):
        sr.load_spec(spec_path)


def test_load_spec_rejects_analytics_repo_without_makefile(tmp_path):
    repo = tmp_path / "repo-no-makefile"
    repo.mkdir()
    spec_path = _write_spec(tmp_path, analytics_repo=str(repo))
    with pytest.raises(sr.SweepSpecError, match="Makefile"):
        sr.load_spec(spec_path)


def test_load_spec_rejects_out_root_with_nonexistent_parent(tmp_path):
    spec_path = _write_spec(tmp_path, out_root=str(tmp_path / "no-such-dir" / "out"))
    with pytest.raises(sr.SweepSpecError):
        sr.load_spec(spec_path)


def test_load_spec_rejects_non_string_schema_version(tmp_path):
    spec_path = _write_spec(tmp_path, schema_version=1)
    with pytest.raises(sr.SweepSpecError):
        sr.load_spec(spec_path)


def test_load_spec_rejects_non_semver_schema_version(tmp_path):
    spec_path = _write_spec(tmp_path, schema_version="1.0")
    with pytest.raises(sr.SweepSpecError):
        sr.load_spec(spec_path)


def test_load_spec_accepts_lineup_as_string(tmp_path):
    spec_path = _write_spec(tmp_path, lineup="tag,tag,calling_station")
    spec = sr.load_spec(spec_path)
    assert spec.lineup == "tag,tag,calling_station"


def test_load_spec_accepts_lineup_as_list_and_normalizes_to_csv(tmp_path):
    spec_path = _write_spec(tmp_path, lineup=["tag", "tag", "calling_station"])
    spec = sr.load_spec(spec_path)
    assert spec.lineup == "tag,tag,calling_station"


def test_load_spec_lineup_omitted_defaults_to_none(tmp_path):
    spec_path = _write_spec(tmp_path)
    spec = sr.load_spec(spec_path)
    assert spec.lineup is None


def test_load_spec_rejects_malformed_lineup(tmp_path):
    spec_path = _write_spec(tmp_path, lineup=123)
    with pytest.raises(sr.SweepSpecError):
        sr.load_spec(spec_path)


# ---------------------------------------------------------------------------
# workers (S5 T5 — optional engine-health knob, default unchanged)
# ---------------------------------------------------------------------------


def test_load_spec_workers_omitted_defaults_to_five(tmp_path):
    spec_path = _write_spec(tmp_path)
    spec = sr.load_spec(spec_path)
    assert spec.workers == 5


@pytest.mark.parametrize("workers", [1, 2, 3, 4, 5])
def test_load_spec_accepts_workers_in_range(tmp_path, workers):
    spec_path = _write_spec(tmp_path, workers=workers)
    spec = sr.load_spec(spec_path)
    assert spec.workers == workers


@pytest.mark.parametrize("workers", [0, 6, -1, 3.5, True, False, "2", None])
def test_load_spec_rejects_invalid_workers(tmp_path, workers):
    spec_path = _write_spec(tmp_path, workers=workers)
    with pytest.raises(sr.SweepSpecError, match="workers"):
        sr.load_spec(spec_path)


def test_run_sweep_uses_spec_workers_as_max_workers(tmp_path, monkeypatch):
    spec_path = _write_spec(tmp_path, workers=2)
    spec = sr.load_spec(spec_path)
    config_hashes = {spec.configs[0]: "a" * 12, spec.configs[1]: "b" * 12}
    _stub_pipeline(monkeypatch, config_hashes)

    captured_max_workers = {}
    real_executor = sr.ThreadPoolExecutor

    class _RecordingExecutor(real_executor):
        def __init__(self, max_workers=None, *args, **kwargs):
            captured_max_workers["value"] = max_workers
            super().__init__(max_workers=max_workers, *args, **kwargs)

    monkeypatch.setattr(sr, "ThreadPoolExecutor", _RecordingExecutor)
    sr.run_sweep(spec)
    assert captured_max_workers["value"] == 2


# ---------------------------------------------------------------------------
# lineup resolution (identity-bearing, mirrors the exporter's own wrap)
# ---------------------------------------------------------------------------


def test_resolve_lineup_dict_default_matches_export_analytics_default():
    from tools.export_analytics import DEFAULT_LINEUP

    resolved = sr.resolve_lineup_dict(None)
    expected = {str(i): DEFAULT_LINEUP[i % len(DEFAULT_LINEUP)] for i in range(9)}
    assert resolved == expected


def test_resolve_lineup_dict_explicit_wraps_to_nine_seats():
    resolved = sr.resolve_lineup_dict("tag,lag,nit")
    assert resolved == {
        "0": "tag", "1": "lag", "2": "nit",
        "3": "tag", "4": "lag", "5": "nit",
        "6": "tag", "7": "lag", "8": "nit",
    }


# ---------------------------------------------------------------------------
# config validation (up front, before any export)
# ---------------------------------------------------------------------------


def test_validate_configs_all_up_front(tmp_path, monkeypatch):
    cfg_a, cfg_b = tmp_path / "a.json", tmp_path / "b.json"
    cfg_a.write_text("{}")
    cfg_b.write_text("{}")
    calls = []

    def fake_load_config(path, packs=None):
        calls.append(Path(path))
        return _fake_validated_config("hash-" + Path(path).stem)

    monkeypatch.setattr(sr.counterfactual, "load_config", fake_load_config)
    resolved = sr.validate_configs((cfg_a, cfg_b))
    assert [c for c, _ in resolved] == [cfg_a, cfg_b]
    assert calls == [cfg_a, cfg_b]


def test_validate_configs_invalid_config_raises_before_any_export(tmp_path, monkeypatch):
    cfg_a, cfg_b = tmp_path / "a.json", tmp_path / "b.json"
    cfg_a.write_text("{}")
    cfg_b.write_text("{}")

    def fake_load_config(path, packs=None):
        if Path(path) == cfg_b:
            raise CounterfactualConfigError("boom")
        return _fake_validated_config("hash-a")

    monkeypatch.setattr(sr.counterfactual, "load_config", fake_load_config)
    with pytest.raises(sr.SweepSpecError, match="boom"):
        sr.validate_configs((cfg_a, cfg_b))


def test_validate_configs_duplicate_hash_refused(tmp_path, monkeypatch):
    cfg_a, cfg_b = tmp_path / "a.json", tmp_path / "b.json"
    cfg_a.write_text("{}")
    cfg_b.write_text("{}")

    monkeypatch.setattr(
        sr.counterfactual, "load_config",
        lambda path, packs=None: _fake_validated_config("same-hash"),
    )
    with pytest.raises(sr.SweepSpecError, match="duplicate"):
        sr.validate_configs((cfg_a, cfg_b))


# ---------------------------------------------------------------------------
# full run_sweep(): success, partial-on-failure, authority stamp, determinism
# ---------------------------------------------------------------------------


def _spec_with_two_configs_one_seed(tmp_path, lineup=None) -> tuple[sr.SweepSpec, dict]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    cfg_a, cfg_b = tmp_path / "cfg_a.json", tmp_path / "cfg_b.json"
    cfg_a.write_text("{}")
    cfg_b.write_text("{}")
    spec_path = tmp_path / "sweep.json"
    document = {
        "schema_version": "1.0.0",
        "configs": [str(cfg_a), str(cfg_b)],
        "seeds": [501],
        "n_hands": 10,
        "out_root": str(tmp_path / "out"),
        "analytics_repo": str(_fake_analytics_repo(tmp_path)),
        "cov_artifact": "cov-fixture",
    }
    if lineup is not None:
        document["lineup"] = lineup
    spec_path.write_text(json.dumps(document))
    spec = sr.load_spec(spec_path)
    config_hashes = {cfg_a: "a" * 64, cfg_b: "b" * 64}
    return spec, config_hashes


def test_run_sweep_complete_on_success(tmp_path, monkeypatch):
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    _stub_pipeline(monkeypatch, config_hashes)

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=0)
    canonical = manifest["canonical"]
    assert canonical["sweep_status"] == "complete"
    assert len(canonical["runs"]) == 2
    assert all(r["run_status"] == "ok" for r in canonical["runs"])
    assert canonical["producer_rerun_check"]["passed"] is True
    assert canonical["producer_rerun_check"]["check_status"] == "passed"


def test_run_sweep_authority_stamp_present(tmp_path, monkeypatch):
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    _stub_pipeline(monkeypatch, config_hashes)

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=0)
    assert manifest["canonical"]["score_authority"] == sr.SCORE_AUTHORITY
    assert "exploratory-surrogate" in manifest["canonical"]["score_authority"]
    for run in manifest["canonical"]["runs"]:
        assert run["score_status"] == "exploratory-surrogate"


def test_run_sweep_partial_on_injected_export_failure(tmp_path, monkeypatch):
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    _stub_pipeline(monkeypatch, config_hashes, fail_on="export")

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=1)
    canonical = manifest["canonical"]
    assert canonical["sweep_status"] == "partial"
    statuses = {r["run_status"] for r in canonical["runs"]}
    assert "failed" in statuses
    failed_run = next(r for r in canonical["runs"] if r["run_status"] == "failed")
    assert failed_run["score_canonical_sha256"] is None
    volatile_run = next(r for r in manifest["volatile"]["runs"]
                        if r["config_hash"] == failed_run["config_hash"])
    assert volatile_run["stderr_tail"] and "export exploded" in volatile_run["stderr_tail"]


def test_run_sweep_partial_on_rerun_check_mismatch(tmp_path, monkeypatch):
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: False)
    _stub_pipeline(monkeypatch, config_hashes)

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=0)
    canonical = manifest["canonical"]
    assert canonical["sweep_status"] == "partial"
    assert canonical["producer_rerun_check"]["passed"] is False
    assert canonical["producer_rerun_check"]["parquet_equal"] is False
    assert canonical["producer_rerun_check"]["check_status"] == "batches_differ"


def test_run_sweep_raw_parquet_deleted_on_success(tmp_path, monkeypatch):
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    _stub_pipeline(monkeypatch, config_hashes)

    sr.run_sweep(spec, keep_raw=False, rerun_check_index=0)
    for run_dir in spec.out_root.glob("run-*"):
        if run_dir.is_dir():
            for name in sr.PARQUET_TABLES:
                assert not (run_dir / name).exists()
    # the rerun-check scratch dir must be gone entirely
    assert not (spec.out_root / "_rerun_check").exists()


def test_run_sweep_keep_raw_preserves_parquet(tmp_path, monkeypatch):
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    _stub_pipeline(monkeypatch, config_hashes)

    sr.run_sweep(spec, keep_raw=True, rerun_check_index=0)
    kept = [d for d in spec.out_root.glob("run-*") if d.is_dir()]
    assert kept
    for run_dir in kept:
        for name in sr.PARQUET_TABLES:
            assert (run_dir / name).exists()


def test_run_sweep_rerun_check_index_out_of_range(tmp_path, monkeypatch):
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    _stub_pipeline(monkeypatch, config_hashes)
    with pytest.raises(sr.SweepSpecError):
        sr.run_sweep(spec, keep_raw=False, rerun_check_index=99)


def test_manifest_canonical_determinism_two_builds_identical_bytes(tmp_path, monkeypatch):
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    _stub_pipeline(monkeypatch, config_hashes)
    manifest_1 = sr.run_sweep(spec, keep_raw=False, rerun_check_index=0)

    spec2, config_hashes2 = _spec_with_two_configs_one_seed(tmp_path / "again")
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    _stub_pipeline(monkeypatch, config_hashes2)
    manifest_2 = sr.run_sweep(spec2, keep_raw=False, rerun_check_index=0)

    bytes_1 = sr.counterfactual.canonical_bytes(manifest_1["canonical"])
    bytes_2 = sr.counterfactual.canonical_bytes(manifest_2["canonical"])
    assert bytes_1 == bytes_2
    assert manifest_1["volatile"]["canonical_sha256"] == manifest_2["volatile"]["canonical_sha256"]


def test_manifest_schema_version_is_module_constant_not_spec_value(tmp_path, monkeypatch):
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    spec = dataclasses.replace(spec, schema_version="9.9.9")  # still valid semver
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    _stub_pipeline(monkeypatch, config_hashes)

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=0)
    assert manifest["canonical"]["schema_version"] == sr.SCHEMA_VERSION
    assert manifest["canonical"]["schema_version"] != "9.9.9"


# ---------------------------------------------------------------------------
# lineup: identity-bearing, in canonical, cross-checked per batch
# ---------------------------------------------------------------------------


def test_run_sweep_explicit_lineup_recorded_in_canonical(tmp_path, monkeypatch):
    ratified = "tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac"
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path, lineup=ratified)
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    _stub_pipeline(monkeypatch, config_hashes)

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=0)
    assert manifest["canonical"]["lineup"] == sr.resolve_lineup_dict(ratified)
    assert manifest["canonical"]["lineup"]["0"] == "tag"
    assert manifest["canonical"]["sweep_status"] == "complete"


def test_run_sweep_default_lineup_path_unchanged(tmp_path, monkeypatch):
    from tools.export_analytics import DEFAULT_LINEUP

    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)  # no lineup field
    assert spec.lineup is None
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    _stub_pipeline(monkeypatch, config_hashes)

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=0)
    expected = {str(i): DEFAULT_LINEUP[i % len(DEFAULT_LINEUP)] for i in range(9)}
    assert manifest["canonical"]["lineup"] == expected
    assert manifest["canonical"]["sweep_status"] == "complete"


def test_run_sweep_lineup_mismatch_fails_closed(tmp_path, monkeypatch):
    """A batch whose `_SUCCESS.lineup` disagrees with the sweep's declared
    lineup (e.g. the exporter silently used a different default) must fail
    that run and drive the sweep to `partial` — lineup is identity-bearing,
    folded into the general identity cross-check."""
    spec, config_hashes = _spec_with_two_configs_one_seed(
        tmp_path, lineup="tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac")
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    calls = _stub_pipeline(monkeypatch, config_hashes)

    wrong_lineup = {str(i): "nit" for i in range(9)}
    real_fake_export = sr._export_subprocess

    def corrupting_export(item: sr.RunItem) -> subprocess.CompletedProcess:
        cp = real_fake_export(item)
        if item.index == 0:
            success = item.out_dir / "_SUCCESS"
            manifest = json.loads(success.read_text())
            manifest["lineup"] = wrong_lineup
            success.write_text(json.dumps(manifest))
        return cp

    monkeypatch.setattr(sr, "_export_subprocess", corrupting_export)

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=1)
    canonical = manifest["canonical"]
    assert canonical["sweep_status"] == "partial"
    failed = next(r for r in canonical["runs"] if r["run_status"] == "failed")
    volatile_run = next(
        r for r in manifest["volatile"]["runs"]
        if r["config_hash"] == failed["config_hash"] and r["seed"] == failed["seed"]
    )
    assert volatile_run["failed_step"] == "identity_mismatch"
    assert calls["export"] >= 1  # sanity: the stub actually ran


# ---------------------------------------------------------------------------
# identity cross-check (_SUCCESS + score producer_run vs the requested arm)
# ---------------------------------------------------------------------------


def test_identity_mismatches_empty_when_matching():
    item = sr.RunItem(0, Path("cfg.json"), "a" * 64, 501, 10, Path("/out"), lineup=None)
    lineup = sr.resolve_lineup_dict(None)
    manifest_like = {"seed": 501, "n_hands": 10, "config_hash": "a" * 64,
                     "lineup": lineup, "run_id": "run-1"}
    assert sr._identity_mismatches(manifest_like, item, lineup, "src",
                                   expected_run_id="run-1") == []


def test_identity_mismatches_flags_seed_and_config_hash():
    item = sr.RunItem(0, Path("cfg.json"), "a" * 64, 501, 10, Path("/out"), lineup=None)
    lineup = sr.resolve_lineup_dict(None)
    manifest_like = {"seed": 999, "n_hands": 10, "config_hash": "b" * 64,
                     "lineup": lineup, "run_id": "run-1"}
    problems = sr._identity_mismatches(manifest_like, item, lineup, "src")
    assert any("seed" in p for p in problems)
    assert any("config_hash" in p for p in problems)


def test_run_sweep_identity_mismatch_wrong_seed_in_success(tmp_path, monkeypatch):
    """A config edited after prevalidation, or a wrong-seed export, must not
    silently score as "complete" — `_SUCCESS.seed` disagreeing with the
    requested arm is an identity mismatch, fail-closed."""
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    _stub_pipeline(monkeypatch, config_hashes)

    real_export = sr._export_subprocess

    def corrupting_export(item: sr.RunItem) -> subprocess.CompletedProcess:
        cp = real_export(item)
        if item.index == 0:
            success_path = item.out_dir / "_SUCCESS"
            success = json.loads(success_path.read_text())
            success["seed"] = success["seed"] + 999
            success_path.write_text(json.dumps(success))
        return cp

    monkeypatch.setattr(sr, "_export_subprocess", corrupting_export)

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=1)
    failed = next(r for r in manifest["canonical"]["runs"] if r["run_status"] == "failed")
    volatile_run = next(r for r in manifest["volatile"]["runs"]
                        if r["config_hash"] == failed["config_hash"])
    assert volatile_run["failed_step"] == "identity_mismatch"
    assert "seed" in volatile_run["stderr_tail"]


# ---------------------------------------------------------------------------
# score payload validation ("ok" must mean USABLE, not merely parsed)
# ---------------------------------------------------------------------------


def test_validate_score_payload_accepts_consistent_payload():
    lineup = sr.resolve_lineup_dict(None)
    payload = _score_payload("a" * 64, 501, 10, "run-1", lineup)
    assert sr._validate_score_payload(payload) is None


def test_validate_score_payload_rejects_non_dict():
    assert sr._validate_score_payload("not a dict") is not None


def test_validate_score_payload_rejects_missing_canonical():
    assert sr._validate_score_payload({"canonical_sha256": "x"}) is not None


def test_validate_score_payload_rejects_claimed_hash_mismatch():
    lineup = sr.resolve_lineup_dict(None)
    payload = _score_payload("a" * 64, 501, 10, "run-1", lineup)
    payload["canonical_sha256"] = "0" * 64
    error = sr._validate_score_payload(payload)
    assert error is not None and "does not match" in error


def test_run_sweep_rejects_empty_json_score_out(tmp_path, monkeypatch):
    """`{}` parses fine as JSON but has no `canonical` — "ok" must mean
    USABLE, not merely parsed."""
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    _stub_pipeline(monkeypatch, config_hashes)
    real_score = sr._make_score

    def corrupting_score(analytics_repo, batch_dir, out_file, cov):
        if "run-000-" in str(batch_dir):
            out_file.write_text("{}")
            return _cp(0)
        return real_score(analytics_repo, batch_dir, out_file, cov)

    monkeypatch.setattr(sr, "_make_score", corrupting_score)

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=1)
    assert manifest["canonical"]["sweep_status"] == "partial"
    failed = next(r for r in manifest["canonical"]["runs"] if r["run_status"] == "failed")
    volatile_run = next(r for r in manifest["volatile"]["runs"]
                        if r["config_hash"] == failed["config_hash"])
    assert volatile_run["failed_step"] == "score_payload_invalid"


def test_run_sweep_rejects_claimed_hash_mismatch(tmp_path, monkeypatch):
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    _stub_pipeline(monkeypatch, config_hashes)
    real_score = sr._make_score

    def corrupting_score(analytics_repo, batch_dir, out_file, cov):
        if "run-000-" in str(batch_dir):
            success = json.loads((batch_dir / "_SUCCESS").read_text())
            payload = _score_payload(success["config_hash"], success["seed"],
                                     success["n_hands"], success["run_id"], success["lineup"])
            payload["canonical_sha256"] = "0" * 64  # wrong on purpose
            out_file.write_text(json.dumps(payload))
            return _cp(0)
        return real_score(analytics_repo, batch_dir, out_file, cov)

    monkeypatch.setattr(sr, "_make_score", corrupting_score)

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=1)
    failed = next(r for r in manifest["canonical"]["runs"] if r["run_status"] == "failed")
    volatile_run = next(r for r in manifest["volatile"]["runs"]
                        if r["config_hash"] == failed["config_hash"])
    assert volatile_run["failed_step"] == "score_payload_invalid"
    assert "canonical_sha256" in volatile_run["stderr_tail"]


# ---------------------------------------------------------------------------
# stale-OUT hazard
# ---------------------------------------------------------------------------


def test_run_sweep_unlinks_stale_score_out_before_scoring(tmp_path, monkeypatch):
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    _stub_pipeline(monkeypatch, config_hashes)

    real_export = sr._export_subprocess

    def planting_export(item: sr.RunItem) -> subprocess.CompletedProcess:
        cp = real_export(item)
        (item.out_dir / "score.json").write_text("STALE-NOT-JSON-GARBAGE")
        return cp

    monkeypatch.setattr(sr, "_export_subprocess", planting_export)

    seen_absent = []
    real_score = sr._make_score

    def observing_score(analytics_repo, batch_dir, out_file, cov):
        seen_absent.append(not out_file.exists())
        return real_score(analytics_repo, batch_dir, out_file, cov)

    monkeypatch.setattr(sr, "_make_score", observing_score)

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=0)
    assert seen_absent and all(seen_absent)  # gone by the time `make score` ran, every time
    assert manifest["canonical"]["sweep_status"] == "complete"


# ---------------------------------------------------------------------------
# cov_artifact always passed to `make score`
# ---------------------------------------------------------------------------


def test_make_score_args_always_include_cov():
    captured = {}

    def fake_run(cmd, cwd, capture_output, text):
        captured["cmd"] = cmd
        return _cp(0)

    import subprocess as subprocess_module
    orig = subprocess_module.run
    subprocess_module.run = fake_run
    try:
        sr._make_score(Path("/repo"), Path("/batch"), Path("/out/score.json"), "cov-xyz")
    finally:
        subprocess_module.run = orig
    assert "COV=cov-xyz" in captured["cmd"]


# ---------------------------------------------------------------------------
# crash safety: worker exceptions, launch errors, main()'s last-resort net
# ---------------------------------------------------------------------------


def test_run_sweep_survives_export_worker_exception(tmp_path, monkeypatch):
    """A future.result() exception (a worker crash, not just a nonzero
    export) must not abort the sweep — it becomes a failed run."""
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)
    _stub_pipeline(monkeypatch, config_hashes)

    real_export = sr._export_subprocess

    def raising_export(item: sr.RunItem) -> subprocess.CompletedProcess:
        if item.index == 0:
            raise OSError("simulated worker crash")
        return real_export(item)

    monkeypatch.setattr(sr, "_export_subprocess", raising_export)

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=1)
    canonical = manifest["canonical"]
    assert canonical["sweep_status"] == "partial"
    failed = next(r for r in canonical["runs"] if r["run_status"] == "failed")
    volatile_run = next(r for r in manifest["volatile"]["runs"]
                        if r["config_hash"] == failed["config_hash"])
    assert volatile_run["stderr_tail"] and "simulated worker crash" in volatile_run["stderr_tail"]


def test_run_sweep_survives_nonexistent_analytics_repo_at_runtime(tmp_path, monkeypatch):
    """Defense in depth: even bypassing `load_spec`'s directory check (e.g. a
    caller constructs `SweepSpec` directly), a launch error from `make`
    against a nonexistent `analytics_repo` must not crash `run_sweep` — it
    must fail that run and still produce a well-formed manifest."""
    cfg_a = tmp_path / "cfg_a.json"
    cfg_a.write_text("{}")
    monkeypatch.setattr(sr.counterfactual, "load_config",
                        lambda path, packs=None: _fake_validated_config("a" * 64))

    def fake_export(item: sr.RunItem) -> subprocess.CompletedProcess:
        item.out_dir.mkdir(parents=True, exist_ok=True)
        for name in sr.PARQUET_TABLES:
            (item.out_dir / name).write_bytes(b"x")
        success = {"run_id": f"run-s{item.seed}-n{item.n_hands}-c{item.config_hash[:12]}",
                  "seed": item.seed, "n_hands": item.n_hands,
                  "config_hash": item.config_hash, "lineup": sr.resolve_lineup_dict(item.lineup)}
        (item.out_dir / "_SUCCESS").write_text(json.dumps(success))
        return _cp(0)

    monkeypatch.setattr(sr, "_export_subprocess", fake_export)
    # `_make_validate`/`_make_score` are NOT mocked: they genuinely try to
    # `cwd=` into a directory that does not exist, raising FileNotFoundError.

    spec = sr.SweepSpec(
        schema_version="1.0.0", configs=(cfg_a,), seeds=(501,), n_hands=10,
        out_root=tmp_path / "out", analytics_repo=tmp_path / "does-not-exist",
        cov_artifact="cov-fixture", lineup=None, workers=5, spec_path=tmp_path / "sweep.json",
    )

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=0)
    canonical = manifest["canonical"]
    assert canonical["sweep_status"] == "partial"
    assert canonical["runs"][0]["run_status"] == "failed"


def test_main_writes_partial_manifest_on_unexpected_crash(tmp_path, monkeypatch):
    """The outermost safety net: even an exception that escapes every inner
    guard still lands a labeled, partial manifest before a nonzero exit."""
    spec_path = _write_spec(tmp_path)
    monkeypatch.setattr(sys, "argv", ["sweep_runner", "--spec", str(spec_path)])

    def boom(spec, keep_raw=False, rerun_check_index=0):
        raise RuntimeError("unexpected crash deep inside")

    monkeypatch.setattr(sr, "run_sweep", boom)

    with pytest.raises(SystemExit) as exc_info:
        sr.main()
    assert exc_info.value.code == 1

    manifest_path = tmp_path / "out" / "sweep_manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["canonical"]["sweep_status"] == "partial"
    assert "crash_traceback_tail" in manifest["volatile"]
    assert "unexpected crash deep inside" in manifest["volatile"]["crash_traceback_tail"]


# ---------------------------------------------------------------------------
# evidence retention: rerun-check failure must retain BOTH directories
# ---------------------------------------------------------------------------


def test_run_sweep_retains_both_dirs_on_rerun_check_failure(tmp_path, monkeypatch):
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: False)  # force mismatch
    _stub_pipeline(monkeypatch, config_hashes)

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=0)
    assert manifest["canonical"]["sweep_status"] == "partial"
    prc = manifest["volatile"]["producer_rerun_check"]
    run_dir, dup_dir = Path(prc["run_dir"]), Path(prc["dup_dir"])
    for name in sr.PARQUET_TABLES:
        assert (run_dir / name).exists(), f"{name} deleted from the designated run"
        assert (dup_dir / name).exists(), f"{name} deleted from the dup batch"


# ---------------------------------------------------------------------------
# dup diagnostics: dup pipeline failure distinguished from batches differing
# ---------------------------------------------------------------------------


def test_run_sweep_dup_pipeline_failure_distinguished_from_batches_differ(tmp_path, monkeypatch):
    spec, config_hashes = _spec_with_two_configs_one_seed(tmp_path)
    monkeypatch.setattr(sr, "parquet_batches_equal", lambda a, b: True)  # would pass if reached
    _stub_pipeline(monkeypatch, config_hashes)

    real_export = sr._export_subprocess

    def failing_dup_export(item: sr.RunItem) -> subprocess.CompletedProcess:
        if item.kind == "rerun_dup":
            return _cp(1, stderr="dup export exploded")
        return real_export(item)

    monkeypatch.setattr(sr, "_export_subprocess", failing_dup_export)

    manifest = sr.run_sweep(spec, keep_raw=False, rerun_check_index=0)
    rerun = manifest["canonical"]["producer_rerun_check"]
    assert rerun["check_status"] == "dup_pipeline_failed"
    assert rerun["passed"] is False
    volatile_rerun = manifest["volatile"]["producer_rerun_check"]
    assert volatile_rerun["dup_status"] == "failed"
    assert volatile_rerun["dup_failed_step"] == "export"
    assert "dup export exploded" in volatile_rerun["dup_stderr_tail"]


# ---------------------------------------------------------------------------
# parquet drop-column comparison
# ---------------------------------------------------------------------------


def test_tables_equal_ignores_exported_at_difference():
    a = pa.table({"x": [1, 2], "exported_at": ["2026-01-01", "2026-01-01"]})
    b = pa.table({"x": [1, 2], "exported_at": ["2026-01-02", "2026-01-02"]})
    assert sr.tables_equal(a, b)


def test_tables_equal_detects_real_content_difference():
    a = pa.table({"x": [1, 2], "exported_at": ["t", "t"]})
    b = pa.table({"x": [1, 3], "exported_at": ["t", "t"]})
    assert not sr.tables_equal(a, b)


def test_parquet_batches_equal_reads_from_disk(tmp_path):
    import pyarrow.parquet as pq

    dir_a, dir_b = tmp_path / "a", tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    for name in sr.PARQUET_TABLES:
        pq.write_table(pa.table({"v": [1], "exported_at": ["t1"]}), dir_a / name)
        pq.write_table(pa.table({"v": [1], "exported_at": ["t2"]}), dir_b / name)
    assert sr.parquet_batches_equal(dir_a, dir_b)

    pq.write_table(pa.table({"v": [2], "exported_at": ["t2"]}), dir_b / sr.PARQUET_TABLES[0])
    assert not sr.parquet_batches_equal(dir_a, dir_b)


# ---------------------------------------------------------------------------
# rerun-check masking logic (canonical BYTES, not Python dict equality)
# ---------------------------------------------------------------------------


def test_mask_gate_hash_masks_only_parquet_sha256():
    canonical = {"gate": {"marker": "_GATE_OK.json", "parquet_sha256": "abc"},
                "score_status": "exploratory-surrogate"}
    masked = sr.mask_gate_hash(canonical)
    assert masked["gate"]["parquet_sha256"] is None
    assert masked["score_status"] == "exploratory-surrogate"
    # original untouched
    assert canonical["gate"]["parquet_sha256"] == "abc"


def test_score_payloads_equal_ignoring_gate_hash_true_when_only_hash_differs():
    lineup = sr.resolve_lineup_dict(None)
    a = _score_payload("cfg-a", 501, 10, "run-a", lineup)["canonical"]
    b = _score_payload("cfg-a", 501, 10, "run-a", lineup,
                       parquet_sha256="different-hash")["canonical"]
    assert sr.score_payloads_equal_ignoring_gate_hash(a, b)


def test_score_payloads_equal_ignoring_gate_hash_false_on_real_difference():
    lineup = sr.resolve_lineup_dict(None)
    a = _score_payload("cfg-a", 501, 10, "run-a", lineup)["canonical"]
    b = _score_payload("cfg-a", 502, 10, "run-a", lineup)["canonical"]
    assert not sr.score_payloads_equal_ignoring_gate_hash(a, b)


def test_score_payloads_equal_uses_canonical_bytes_not_dict_equality():
    """`1 == 1.0` in Python but they serialize to different JSON bytes — the
    comparison must be byte-level, not `dict ==`, so a real (if numerically
    subtle) difference is not silently swallowed."""
    lineup = sr.resolve_lineup_dict(None)
    a = _score_payload("cfg-a", 501, 10, "run-a", lineup)["canonical"]
    b = _score_payload("cfg-a", 501, 10, "run-a", lineup)["canonical"]
    a["some_stat"] = 1
    b["some_stat"] = 1.0
    assert a == b  # Python dict equality is blind to this
    assert not sr.score_payloads_equal_ignoring_gate_hash(a, b)  # byte comparison is not
