"""The sweep runner (flywheel S4 T5) — unit-level coverage.

No full simulations here: the subprocess/`make` layer is monkeypatched with
tiny fakes so these tests exercise spec parsing, config validation, manifest
determinism, fail-closed partial labeling, the authority stamp, the
parquet-drop-column comparison, and the rerun-check masking logic — all in
milliseconds. The real end-to-end mini-sweep (actual exports, actual `make
validate`/`make score`) is a separate, manually-run acceptance check (see the
ticket), not a pytest target.
"""

from __future__ import annotations

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
        "analytics_repo": str(tmp_path / "analytics"),
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


def _score_payload(config_hash: str, seed: int, run_id: str,
                   parquet_sha256: str = "deadbeef") -> dict:
    canonical = {
        "scorer_version": "1.0.0",
        "score_status": "exploratory-surrogate",
        "registry": {"version": "2.0.0", "content_sha256": "reg" * 10,
                     "stat_definition_version": "statdef-2026-08-06"},
        "covariance_artifact": {"id": "cov-abc123"},
        "producer_run": {"run_id": run_id, "seed": seed, "engine_git_sha": "deadc0de",
                         "config_hash": config_hash},
        "gate": {"marker": "_GATE_OK.json", "parquet_sha256": parquet_sha256},
    }
    return {"canonical": canonical, "canonical_sha256": "score" + "0" * 59}


def _stub_pipeline(monkeypatch, config_hashes: dict[Path, str], *, fail_on: str | None = None):
    """Monkeypatch the subprocess boundary: export always "succeeds" (writes
    a fake `_SUCCESS`), `make validate` succeeds, `make score` writes a fake
    score payload to OUT. `fail_on` (one of "export"/"validate"/"score")
    forces exactly one primary run (the first) to fail at that step."""
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
        (item.out_dir / "_SUCCESS").write_text(json.dumps({"run_id": run_id, "lineup": lineup}))
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
        run_id = success["run_id"]
        # derive config_hash/seed back out of the fake run_id
        seed = int(run_id.split("-s")[1].split("-n")[0])
        payload = _score_payload(config_hash="fake", seed=seed, run_id=run_id)
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
        "analytics_repo": str(tmp_path / "analytics"),
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
    that run and drive the sweep to `partial` — lineup is identity-bearing."""
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
    assert volatile_run["failed_step"] == "lineup_mismatch"
    assert calls["export"] >= 1  # sanity: the stub actually ran


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
# rerun-check masking logic
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
    a = _score_payload("cfg", 501, "run-a")["canonical"]
    b = _score_payload("cfg", 501, "run-a", parquet_sha256="different-hash")["canonical"]
    assert sr.score_payloads_equal_ignoring_gate_hash(a, b)


def test_score_payloads_equal_ignoring_gate_hash_false_on_real_difference():
    a = _score_payload("cfg", 501, "run-a")["canonical"]
    b = _score_payload("cfg", 502, "run-a")["canonical"]
    assert not sr.score_payloads_equal_ignoring_gate_hash(a, b)
