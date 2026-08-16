"""F1 (flywheel S6 T2): `--buyin-spread` conformance + identity tests.

Three legs, per the ticket:
1. Conformance — `export_analytics._draw_buyin_targets` reproduces the live
   `sim_session._rebuy_seats` distribution/semantics exactly (same bounds,
   integer-cent granularity, nine draws in seat order, per-hand stream
   isolation), using the live implementation itself as the oracle.
2. Default-path regression — flag OFF is canonically unchanged: no spread
   fields in the manifest, no mode token in run_id, deterministic across two
   runs (canonical compare excludes `exported_at`/`_TIMING.json`, the S4
   convention).
3. Spread-run — flag ON: every hand's starting stacks land in [95,105]bb,
   not all exactly 100bb across the run, deterministic across two runs with
   the same seed, run_id carries `-bspread-`, manifest records mode+bounds.
"""
from __future__ import annotations

import hashlib
import json
import random

import pytest

pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")

from app.services import sim_session  # noqa: E402 — READ-ONLY oracle
from tools import export_analytics as ea  # noqa: E402
from tools.export_analytics import run_export  # noqa: E402
from tools.sweep_runner import tables_equal  # noqa: E402 — S4's canonical-compare helper


class _FakeSeat:
    """Minimal stand-in for `SimSeat`: `_rebuy_seats` only reads/writes
    `buyins_bb`/`stack_bb` and is iterated in the given order."""

    def __init__(self, seat_index: int) -> None:
        self.seat_index = seat_index
        self.buyins_bb = 0.0
        self.stack_bb = 100.0


def _live_targets(hand_seed: int) -> list[float]:
    """Oracle: drive the REAL `sim_session._rebuy_seats` with the same
    `seed ^ 1` derivation `_deal_and_advance` uses, and read back the nine
    resulting `stack_bb` values in seat order."""
    seats = [_FakeSeat(i) for i in range(9)]
    sim_session._rebuy_seats(seats, random.Random(hand_seed ^ 1))
    return [row.stack_bb for row in seats]


# ---------------------------------------------------------------------------
# 1. Conformance vs. the live implementation
# ---------------------------------------------------------------------------


def test_bounds_match_live_constants():
    assert ea._BUYIN_MIN_BB == sim_session._BUYIN_MIN_BB == 95.0
    assert ea._BUYIN_MAX_BB == sim_session._BUYIN_MAX_BB == 105.0


@pytest.mark.parametrize("hand_seed", [0, 1, 42, 123456789, 999999999])
def test_draw_matches_live_oracle_exactly(hand_seed):
    assert ea._draw_buyin_targets(hand_seed) == _live_targets(hand_seed)


def test_draw_is_nine_values_in_bounds_inclusive():
    targets = ea._draw_buyin_targets(7)
    assert len(targets) == 9
    for t in targets:
        assert 95.0 <= t <= 105.0
        assert round(t, 2) == t  # integer-cent granularity


def test_draw_is_per_hand_stream_isolated():
    """Same hand seed -> same targets regardless of how many other draws
    (from an unrelated RNG stream) happened first — the export's global
    `rng` must never leak into the spread stream."""
    burn = random.Random(0)
    for _ in range(1000):
        burn.random()

    baseline = ea._draw_buyin_targets(555)
    # A completely independent RNG having been exhausted elsewhere changes
    # nothing about a fresh call with the same hand_seed.
    again = ea._draw_buyin_targets(555)
    assert baseline == again == _live_targets(555)


def test_different_hand_seeds_generally_differ():
    a = ea._draw_buyin_targets(1)
    b = ea._draw_buyin_targets(2)
    assert a != b


# ---------------------------------------------------------------------------
# 2. Default-path regression (flag OFF)
# ---------------------------------------------------------------------------

_VOLATILE_MANIFEST_KEYS = {"exported_at", "git_sha"}


def _canonical_manifest(manifest: dict) -> dict:
    return {k: v for k, v in manifest.items() if k not in _VOLATILE_MANIFEST_KEYS}


def test_default_path_manifest_has_no_spread_fields(tmp_path):
    manifest = run_export(n_hands=3, seed=11, out_dir=tmp_path / "batch")
    assert "buyin_spread" not in manifest
    assert "buyin_min_bb" not in manifest
    assert "buyin_max_bb" not in manifest
    assert "-bspread-" not in manifest["run_id"]
    assert manifest["run_id"] == f"run-s11-n3-c{manifest['config_hash'][:12]}"


def test_default_path_canonically_identical_across_two_runs(tmp_path):
    m1 = run_export(n_hands=5, seed=3, out_dir=tmp_path / "a")
    m2 = run_export(n_hands=5, seed=3, out_dir=tmp_path / "b")

    assert _canonical_manifest(m1) == _canonical_manifest(m2)

    for name in ("hands", "seat_outcomes", "decisions"):
        ta = pq.read_table(tmp_path / "a" / f"{name}.parquet")
        tb = pq.read_table(tmp_path / "b" / f"{name}.parquet")
        assert tables_equal(ta, tb), f"{name}.parquet differs (excluding exported_at)"

    # _TIMING.json is fully volatile (wall_seconds) and excluded from the
    # canonical comparison entirely, per the S4 convention.
    assert (tmp_path / "a" / "_TIMING.json").exists()
    assert (tmp_path / "b" / "_TIMING.json").exists()


def test_default_path_starting_stack_is_flat_100bb(tmp_path):
    run_export(n_hands=4, seed=6, out_dir=tmp_path / "batch")
    seats = pq.read_table(tmp_path / "batch" / "seat_outcomes.parquet")
    stacks = set(seats.column("starting_stack_bb").to_pylist())
    assert stacks == {100.0}


def _hash_table(path) -> str:
    """Stable content hash: `exported_at` dropped, rows serialized as JSON
    with sorted keys (independent of parquet's internal encoding/compression
    so the digest reflects only logical content, not file bytes)."""
    table = pq.read_table(path)
    if "exported_at" in table.column_names:
        table = table.drop(["exported_at"])
    blob = json.dumps(table.to_pylist(), sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()


def _hash_manifest(manifest: dict) -> str:
    blob = json.dumps(_canonical_manifest(manifest), sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()


# Golden digests pinned against a golden-fixture run at (seed=777, n_hands=25)
# on the flag-OFF default path of the CURRENT worktree implementation, which
# the coordinator independently verified is canonically identical (same 4
# artifacts, exported_at/_TIMING.json excluded) to the PRE-change
# implementation — so this pin is valid evidence against a future default-path
# regression even though it was computed post-change (Codex review finding,
# S6 T2 dual review). NOT self-referential: unlike the two-runs-of-this-build
# comparison above, a future edit that silently changes default-path output
# fails against these hard-coded digests, not against another run of itself.
# RE-PINNED for the de-robotization slice (2026-08-15, slice-authorized). The
# six persona packs now answer `vs_rfi`, `vs_limpers` and `vs_3bet` per seat,
# so the bots play differently and every byte of a seeded export changes with
# them. Re-pinned twice within that slice: once for the seat split and once for
# the range-edge softening that landed on top of it — two commits, two stream
# shifts. All four digests moving TOGETHER is the expected signature of a
# behaviour change: an export-writer regression would move the table digests
# while leaving the manifest's own fields alone, and a manifest-only change
# would leave the tables untouched. Old values, for anyone bisecting:
#   manifest      24a0b5f398e619036285f7083cda5b96096720d721e47fe054dc28c39536a734
#   hands         fbb0eef5565032ae54b18c9beda824054e0778f215edd3604f09d4b77ebf7f32
#   seat_outcomes 9f9a096fc93b6341625319307b97b524168b43610016191be877efe2be54e233
#   decisions     fa3f059492a97487bc52499c5ff17df1b743d8aec8e2fab5ee7f3aa9a9660cea
_GOLDEN_SEED = 777
_GOLDEN_N_HANDS = 25
_GOLDEN_MANIFEST_SHA256 = (
    "177db574ae998a9f28ab3428171e3a98c4a706b9319bae2071a238c5dde57551"
)
_GOLDEN_HANDS_SHA256 = (
    "1831522fa7b31c4ae7e322fe59e527b67bc06c6876db50006b5fec59b05647aa"
)
_GOLDEN_SEAT_OUTCOMES_SHA256 = (
    "ae95e29b29200fed9100883c692834c31119a9c757e6a056936036bcbcc385e5"
)
_GOLDEN_DECISIONS_SHA256 = (
    "a0b9bb77c8876e9a8cd04d1fb9116623323c3b1dfe880b0884cf6df6b924301c"
)


def test_default_path_matches_pinned_golden_digests(tmp_path):
    manifest = run_export(
        n_hands=_GOLDEN_N_HANDS, seed=_GOLDEN_SEED, out_dir=tmp_path / "batch"
    )
    assert _hash_manifest(manifest) == _GOLDEN_MANIFEST_SHA256
    assert _hash_table(tmp_path / "batch" / "hands.parquet") == _GOLDEN_HANDS_SHA256
    assert (
        _hash_table(tmp_path / "batch" / "seat_outcomes.parquet")
        == _GOLDEN_SEAT_OUTCOMES_SHA256
    )
    assert (
        _hash_table(tmp_path / "batch" / "decisions.parquet")
        == _GOLDEN_DECISIONS_SHA256
    )


# ---------------------------------------------------------------------------
# 3. Spread-run (flag ON)
# ---------------------------------------------------------------------------


def test_spread_run_stacks_within_bounds_and_not_all_100(tmp_path):
    run_export(n_hands=20, seed=42, out_dir=tmp_path / "batch", buyin_spread=True)
    seats = pq.read_table(tmp_path / "batch" / "seat_outcomes.parquet")
    stacks = seats.column("starting_stack_bb").to_pylist()
    assert len(stacks) == 20 * 9
    for s in stacks:
        assert 95.0 <= s <= 105.0
    assert set(stacks) != {100.0}


def test_spread_run_run_id_and_manifest_fields(tmp_path):
    manifest = run_export(n_hands=3, seed=9, out_dir=tmp_path / "batch", buyin_spread=True)
    assert "-bspread-" in manifest["run_id"]
    assert manifest["run_id"] == (
        f"run-s9-n3-bspread-c{manifest['config_hash'][:12]}"
    )
    assert manifest["buyin_spread"] is True
    assert manifest["buyin_min_bb"] == 95.0
    assert manifest["buyin_max_bb"] == 105.0


def test_spread_run_deterministic_across_two_runs(tmp_path):
    m1 = run_export(n_hands=6, seed=17, out_dir=tmp_path / "a", buyin_spread=True)
    m2 = run_export(n_hands=6, seed=17, out_dir=tmp_path / "b", buyin_spread=True)

    assert _canonical_manifest(m1) == _canonical_manifest(m2)
    for name in ("hands", "seat_outcomes", "decisions"):
        ta = pq.read_table(tmp_path / "a" / f"{name}.parquet")
        tb = pq.read_table(tmp_path / "b" / f"{name}.parquet")
        assert tables_equal(ta, tb), f"{name}.parquet differs (excluding exported_at)"


def test_spread_run_targets_match_per_hand_seed_used(tmp_path):
    """The starting stacks actually written for hand `i` equal
    `_draw_buyin_targets(hand_seed)` for that hand's own `hand_seed` (the
    `hands.parquet` column) — ties the spread draw to the SAME per-hand seed
    the deal uses, not a different stream."""
    manifest = run_export(n_hands=5, seed=23, out_dir=tmp_path / "batch", buyin_spread=True)
    hands = pq.read_table(tmp_path / "batch" / "hands.parquet").to_pylist()
    seats = pq.read_table(tmp_path / "batch" / "seat_outcomes.parquet").to_pylist()
    by_hand = {}
    for row in seats:
        by_hand.setdefault(row["hand_id"], [None] * 9)
        by_hand[row["hand_id"]][row["seat"]] = row["starting_stack_bb"]

    for hand in hands:
        expected = ea._draw_buyin_targets(hand["hand_seed"])
        assert by_hand[hand["hand_id"]] == expected

    assert manifest["n_hands"] == 5


def test_cli_buyin_spread_flag(tmp_path, monkeypatch):
    import sys

    out_dir = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", [
        "export_analytics.py", "--hands", "3", "--seed", "5",
        "--out", str(out_dir), "--skip-contract-test", "--buyin-spread",
    ])
    ea.main()

    manifest = json.loads((out_dir / "_SUCCESS").read_text())
    assert manifest["buyin_spread"] is True
    assert "-bspread-" in manifest["run_id"]
