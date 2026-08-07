"""T2 (flywheel S3/S4): local schema assertion check for the analytics export.

Covers ALL `decisions` columns (including the two T2/S3 columns
`engine_node_key` / `hand_class_bucket`) plus the corruption case, and (S4
T2) the `packs=`/`config_hash=` pairing contract, the new `run_id` format,
the `_TIMING.json` evidence file, and its write-order-before-`_SUCCESS`
guarantee. This is a LOCAL check only — the authoritative `datacontract
test` run against the vendored ODCS contract (tools/poker_events.odcs.yaml)
is deferred to the director per the T2 ticket.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import pytest

pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")

from tools import counterfactual  # noqa: E402
from tools import export_analytics as ea  # noqa: E402
from tools.export_analytics import CONTRACT_VERSION, run_export  # noqa: E402

DECISIONS_REQUIRED_COLUMNS = {
    "hand_id", "seq", "seat", "street", "position", "action",
    "raise_to_bb", "chips_committed_bb", "pot_before_bb", "to_call_bb",
    "engine_node_key", "hand_class_bucket", "exported_at",
}

# Trailing-newline hole (T1 fixed the same class in counterfactual.py):
# `.match()` with `^...$` still accepts a trailing "\n" because `$` matches
# just before a final newline. `.fullmatch()` (no anchors needed) does not.
_CONFIG_HASH_RE = re.compile(r"[0-9a-f]{64}")
_RUN_ID_RE = re.compile(r"run-s(\d+)-n(\d+)-c([0-9a-f]{12})")

_ODCS_MIRROR_SHA256 = (
    "ee1aa3edb1915333bf465255f250ec49e567f55e65d397248272a61308e03514"
)


def _validate_batch(out_dir: Path) -> None:
    """Raise AssertionError if `out_dir` isn't a well-formed export batch.

    Checks: _SUCCESS manifest present + parses as JSON with row_counts;
    each table's Parquet file is readable and its row count matches the
    manifest; `decisions` has every required column (T2's two new ones
    included); the two T2 null invariants hold (post rows -> NULL node key;
    non-post rows -> non-NULL hand_class_bucket, preflop bucket or postflop
    `strength_bucket` reuse alike — only forced-blind posts are NULL).
    """
    success = out_dir / "_SUCCESS"
    assert success.exists(), "_SUCCESS manifest missing"
    manifest = json.loads(success.read_text())
    row_counts = manifest["row_counts"]

    assert _CONFIG_HASH_RE.fullmatch(manifest["config_hash"]), (
        f"config_hash {manifest['config_hash']!r} is not 64 lowercase hex chars"
    )
    m = _RUN_ID_RE.fullmatch(manifest["run_id"])
    assert m, f"run_id {manifest['run_id']!r} does not match run-s<seed>-n<hands>-c<12hex>"
    assert m.group(3) == manifest["config_hash"][:12], (
        "run_id's config suffix must be the first 12 hex chars of config_hash"
    )

    for name in ("hands", "seat_outcomes", "decisions"):
        path = out_dir / f"{name}.parquet"
        table = pq.read_table(path)  # raises on a corrupted/truncated file
        assert table.num_rows == row_counts[name], (
            f"{name}: row count {table.num_rows} != manifest {row_counts[name]}"
        )

    decisions = pq.read_table(out_dir / "decisions.parquet")
    cols = set(decisions.schema.names)
    missing = DECISIONS_REQUIRED_COLUMNS - cols
    assert not missing, f"decisions missing columns: {missing}"

    import pyarrow.compute as pc
    action = decisions.column("action")
    node = decisions.column("engine_node_key")
    bucket = decisions.column("hand_class_bucket")

    is_post = pc.equal(action, "post")
    mismatch_node = pc.sum(pc.not_equal(is_post, pc.is_null(node))).as_py()
    assert mismatch_node == 0, "engine_node_key must be NULL iff action='post'"

    # hand_class_bucket is populated on EVERY non-post row now: preflop rows
    # get the export-side hole-card bucket, postflop rows reuse the domain's
    # `strength_bucket` (see the module docstring / t2-export-report.md).
    mismatch_bucket = pc.sum(pc.not_equal(is_post, pc.is_null(bucket))).as_py()
    assert mismatch_bucket == 0, "hand_class_bucket must be NULL iff action='post'"


def test_schema_valid_on_fresh_batch(tmp_path):
    out_dir = tmp_path / "batch"
    run_export(n_hands=50, seed=7, out_dir=out_dir)
    _validate_batch(out_dir)  # must not raise


def test_timing_file_written_before_success_and_consistent(tmp_path):
    out_dir = tmp_path / "batch"
    manifest = run_export(n_hands=25, seed=3, out_dir=out_dir)

    timing_path = out_dir / "_TIMING.json"
    assert timing_path.exists(), "_TIMING.json missing"
    timing = json.loads(timing_path.read_text())

    assert set(timing.keys()) == {
        "schema_version", "wall_seconds", "n_hands", "seed", "run_id",
    }, "unexpected keys in _TIMING.json"
    assert timing["schema_version"] == "1.0.0"
    assert isinstance(timing["wall_seconds"], (int, float))
    assert timing["wall_seconds"] >= 0
    assert timing["n_hands"] == manifest["n_hands"] == 25
    assert timing["seed"] == manifest["seed"] == 3
    assert timing["run_id"] == manifest["run_id"]


def test_write_order_timing_before_success_all_writes(tmp_path, monkeypatch):
    """Call-order spy (not mtime, which can tie on a fast filesystem): proves
    the three parquet tables are written before `_TIMING.json`, which is
    written before `_SUCCESS` — and `_SUCCESS` is the LAST of every file this
    export writes."""
    order: list[str] = []

    orig_write_table = pq.write_table

    def spy_write_table(table, path, *args, **kwargs):
        order.append(Path(path).name)
        return orig_write_table(table, path, *args, **kwargs)

    orig_write_text = Path.write_text

    def spy_write_text(self, *args, **kwargs):
        order.append(self.name)
        return orig_write_text(self, *args, **kwargs)

    monkeypatch.setattr(pq, "write_table", spy_write_table)
    monkeypatch.setattr(Path, "write_text", spy_write_text)

    out_dir = tmp_path / "batch"
    run_export(n_hands=5, seed=2, out_dir=out_dir)

    assert order[-1] == "_SUCCESS", f"_SUCCESS must be written last of all files, got {order}"
    assert order.index("_TIMING.json") < order.index("_SUCCESS")
    for parquet_name in ("hands.parquet", "seat_outcomes.parquet", "decisions.parquet"):
        assert order.index(parquet_name) < order.index("_TIMING.json"), (
            f"{parquet_name} must be written before _TIMING.json, got {order}"
        )


def test_default_path_config_hash_matches_baseline(tmp_path):
    out_dir = tmp_path / "batch"
    manifest = run_export(n_hands=10, seed=1, out_dir=out_dir)
    assert manifest["config_hash"] == counterfactual.baseline_config_hash()


def test_packs_and_config_hash_must_both_be_given_or_both_omitted(tmp_path):
    packs = counterfactual.load_baseline_packs()
    config_hash = counterfactual.baseline_config_hash(packs)

    with pytest.raises(ValueError):
        run_export(n_hands=5, seed=1, out_dir=tmp_path / "a", packs=packs)
    with pytest.raises(ValueError):
        run_export(n_hands=5, seed=1, out_dir=tmp_path / "b", config_hash=config_hash)

    # Both given (sweep path) succeeds and stamps the given identity.
    manifest = run_export(
        n_hands=5, seed=1, out_dir=tmp_path / "c", packs=packs, config_hash=config_hash
    )
    assert manifest["config_hash"] == config_hash
    assert manifest["run_id"] == f"run-s1-n5-c{config_hash[:12]}"


def test_contract_version_is_1_2_0():
    assert CONTRACT_VERSION == "1.2.0"


def test_contract_version_matches_vendored_yaml():
    """CONTRACT_VERSION and the vendored yaml's `version:` field are derived
    from the SAME source (fix #2) — cross-checked here against an
    independent regex read straight off disk, so a hand-edit to either the
    constant or the yaml that drifts them apart fails loudly."""
    text = ea._ODCS_PATH.read_text(encoding="utf-8")
    m = re.search(r"^version:\s*(\S+)\s*$", text, re.MULTILINE)
    assert m is not None, "no top-level version: field in the vendored yaml"
    assert CONTRACT_VERSION == m.group(1) == ea._odcs_contract_version()


@pytest.mark.parametrize(
    "bad_hash",
    [
        "NOT-A-HASH",
        "a" * 63,  # too short
        "A" * 64,  # uppercase
        ("a" * 64) + "\n",  # trailing newline
    ],
    ids=["malformed", "short", "uppercase", "trailing-newline"],
)
def test_supplied_config_hash_rejected_if_malformed(tmp_path, bad_hash):
    packs = counterfactual.load_baseline_packs()
    with pytest.raises(ValueError):
        run_export(
            n_hands=3, seed=1, out_dir=tmp_path / "bad", packs=packs, config_hash=bad_hash
        )


def test_odcs_mirror_sha256_pinned():
    """Pins the mirror byte-for-byte against the analytics repo's copy — this
    pin is expected to change whenever the mirror is next refreshed from
    poker-analytics `contracts/poker_events.odcs.yaml`; a one-sided edit to
    only one side fails HERE instead of nowhere."""
    digest = hashlib.sha256(ea._ODCS_PATH.read_bytes()).hexdigest()
    assert digest == _ODCS_MIRROR_SHA256


def test_cli_config_flag_valid(tmp_path, monkeypatch):
    packs = counterfactual.load_baseline_packs()
    cfg = counterfactual.empty_override_config(packs)
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))
    out_dir = tmp_path / "out"

    monkeypatch.setattr(sys, "argv", [
        "export_analytics.py", "--hands", "3", "--seed", "9",
        "--out", str(out_dir), "--skip-contract-test", "--config", str(cfg_path),
    ])
    ea.main()

    manifest = json.loads((out_dir / "_SUCCESS").read_text())
    assert manifest["config_hash"] == counterfactual.baseline_config_hash(packs)


def test_cli_config_flag_rejected_config(tmp_path, monkeypatch, capsys):
    cfg_path = tmp_path / "bad_cfg.json"
    cfg_path.write_text(json.dumps({"schema_version": "1.0.0"}))  # missing required fields
    out_dir = tmp_path / "out"

    monkeypatch.setattr(sys, "argv", [
        "export_analytics.py", "--hands", "3", "--seed", "9",
        "--out", str(out_dir), "--skip-contract-test", "--config", str(cfg_path),
    ])
    with pytest.raises(SystemExit) as exc_info:
        ea.main()
    assert exc_info.value.code != 0
    assert "ERROR" in capsys.readouterr().err
    assert not out_dir.exists() or not (out_dir / "_SUCCESS").exists()


def test_corrupted_batch_fails_validation(tmp_path):
    src = tmp_path / "batch"
    run_export(n_hands=50, seed=7, out_dir=src)

    corrupt = tmp_path / "batch_corrupt"
    shutil.copytree(src, corrupt)
    # Corrupt one parquet file in the COPY only — truncate + overwrite with
    # garbage bytes so it is neither valid Parquet nor matches its row count.
    target = corrupt / "decisions.parquet"
    target.write_bytes(b"not a parquet file" * 10)

    with pytest.raises((AssertionError, pa.lib.ArrowInvalid, OSError)):
        _validate_batch(corrupt)

    # The original, uncorrupted batch is untouched and still validates.
    _validate_batch(src)
