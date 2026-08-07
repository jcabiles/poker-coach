"""T2 (flywheel S3): local schema assertion check for the analytics export.

Covers ALL `decisions` columns (including the two new T2 columns
`engine_node_key` / `hand_class_bucket`) plus the corruption case. This is a
LOCAL check only — the authoritative `datacontract test` run against the
vendored ODCS contract (tools/poker_events.odcs.yaml) is deferred to the
director per the T2 ticket.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")

from tools.export_analytics import run_export  # noqa: E402

DECISIONS_REQUIRED_COLUMNS = {
    "hand_id", "seq", "seat", "street", "position", "action",
    "raise_to_bb", "chips_committed_bb", "pot_before_bb", "to_call_bb",
    "engine_node_key", "hand_class_bucket", "exported_at",
}


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
