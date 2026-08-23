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
# them. Re-pinned three times within that slice: the seat split, the range-edge
# softening on top of it, and the review rework that split the recreationals'
# small blind from their big blind. Each is a deliberate behaviour change.
# All four digests moving TOGETHER is the expected signature of a
# behaviour change: an export-writer regression would move the table digests
# while leaving the manifest's own fields alone, and a manifest-only change
# would leave the tables untouched.
#
# ⚠️ THESE ARE STREAM *AND IDENTITY* FINGERPRINTS, and a pack `version` bump
# alone moves them. `config_hash` covers the pack model (version included),
# `run_id` embeds `config_hash`, and `hand_id` embeds `run_id` — so bumping a
# version string re-writes an identifier column in all three tables while the
# cards and actions stay byte-identical. Verified directly: with `hand_id`
# dropped, a version-only change leaves the decisions digest unchanged. If
# this test fires and you cannot find a behaviour change, check that first
# rather than hunting a bug in the engine. Old values, for anyone bisecting:
#   manifest      24a0b5f398e619036285f7083cda5b96096720d721e47fe054dc28c39536a734
#   hands         fbb0eef5565032ae54b18c9beda824054e0778f215edd3604f09d4b77ebf7f32
#   seat_outcomes 9f9a096fc93b6341625319307b97b524168b43610016191be877efe2be54e233
#   decisions     fa3f059492a97487bc52499c5ff17df1b743d8aec8e2fab5ee7f3aa9a9660cea
# RE-PINNED for the de-robotization slice's T5 (2026-08-16, slice-authorized):
# postflop bet sizes are re-weighted across all six packs, so the bots bet
# different amounts and every byte of a seeded export changes with them. Two
# distinct causes are folded into this one re-pin, and both are deliberate:
# the behaviour change itself, and the six `version` bumps that carry it (see
# the ⚠️ note above — a version bump alone would move all four digests).
# Recorded once, at the end of the ticket, with pack content frozen.
# Pre-T5 values, kept so the move is inspectable:
#   manifest      581e42b9f6142870e8b3945c7276ec9f1be34be30816a404fdbf185599b1318d
#   hands         a25b7c339bb89291f05e773cafdd488c85149734b50ef3652869e2978e71ebab
#   seat_outcomes 2cb05b500cb04575984b00a2cfa8bfa46646351f473be2182621e498212cd9c6
#   decisions     989f630eb9010959f13e8ad6696bb10e4dbba38be6bb1df8a72e908059af6d69
# RE-RECORDED AGAIN by T5's SECOND review round (2026-08-17,
# slice-authorized): the tag and lag gain a third-pot bet on wet flops, lag
# loses the wet-flop overbet the first review round gave it, and those two pack
# versions bump with the values. Recorded once, at the end of the round, with
# pack content frozen. Values immediately before it:
#   manifest      85e07788582e358dd26575b939dbfe6bcef513aaed21351298e2eefe3d69e3b5
#   hands         2e2a1f8a7962281ad843f200b7a5bdfd09ed418939e315faae5646c018de62f9
#   seat_outcomes b7e09fb6825fb7bfcd3e067c26b2ec40b8d3c65633b4ea3ac177e8ef09ec8f1f
#   decisions     ca6a5e2191041e046acc0a7c6c713059cf83e6cb27a745c1213d0f7187b8418e
# RE-RECORDED for T2b (2026-08-17, slice-authorized): PREFLOP raise sizes are
# now drawn from a mix — keyed by seat for the three regulars, flat for the
# three recreationals — so the bots raise different amounts before the flop and
# every byte of a seeded export changes with them. Two causes are folded into
# this one re-pin and both are deliberate: the behaviour change itself, and the
# six `version` bumps that carry it (see the ⚠️ note above — a version bump
# alone moves all four digests, because `version` is inside the model that
# `config_hash` covers). Recorded once, at the end of the ticket, with pack
# content frozen. Values immediately before it:
#   manifest      72fc9c7f2948d72858de499fffd5887a128875b6c8b59de3547399bbd54083fa
#   hands         b2d04e9210ba7041bd291f1013de870de6f465c4b4e8936467d9653798568a91
#   seat_outcomes e4277183be543a7add97fe5b7e3ddf4c77bac9a10d98b9817a85b77ba66f108b
#   decisions     79b25a603987dbba08d547f3960993e85296eb751e783da30748f709f2109e79
# RE-RECORDED for T3 (improvement slice 2, 2026-08-19, slice-authorized): naked
# ace-high may call a river bet again, at a damped weight. The river call zero
# used to be written on `bluff_cell`, which bundles ACE_HIGH with AIR; it now
# reads the made-hand bucket and refuses AIR only, and ace-high's restored call
# merit is multiplied by `personas_postflop._ACE_HIGH_RIVER_CALL_DAMP` = 0.06.
# Minimum-defence arithmetic over the measured river price distribution derives
# about 0.46; 0.06 is a round value inside the range two frozen went-to-showdown
# bands admit with margin, and the owner ruled that conflict in the bands' favour
# on 2026-08-19.
# Hands that used to end on a river fold now sometimes play to showdown, so the
# seeded twenty-five-hand export contains different actions and different
# results. Recorded at the final shipped constant; the three digests below are
# the same at 0.45 and at 0.06, because in these particular twenty-five hands
# the action draw lands on the same side of the threshold at both values, which
# it need not have. Values immediately before it:
#   manifest      998cd03659012e083d7e848b06e907f476c005a74816305842f1db45ecc92482
#   hands         ab611396d45659c1a240c7b4f5f87702259c39778870f40905106dc4b5e6498b
#   seat_outcomes ae2056e0efd18e31cba73c2c8c00d6e4ea2af5b64ed53e03630ffd35926e0846
#   decisions     084bcf40a6e99dce5aad994bff51b4e0ca236ef6a03080461f61486ab8b218eb
# UNLIKE EVERY PRIOR ENTRY IN THIS CHAIN, THE MANIFEST DIGEST DOES NOT MOVE, and
# that is the expected signature rather than a partial re-record. T3 is a code
# change with no pack edit, so no `version` string bumps, so `config_hash` and
# the `run_id` and `hand_id` columns derived from it are all unchanged; only the
# cards played and the money moved differ. The three entries above this one each
# folded a behaviour change together with six version bumps, which is why they
# moved all four. A future entry that moves the manifest without a pack edit is
# the thing to investigate.
# No new random draw was added and none precedes the action draw. The draw COUNT
# is not claimed invariant: a fold flipping to a call changes which later
# decisions happen at all.
# RE-RECORDED for the lag vs-3-bet re-tune (2026-08-19, slice-authorized): the
# lag's `vs_3bet` OPENER node folds more in its three weakest tiers, so the lag
# continues fewer 3-bet pots, hands end differently and every byte of a seeded
# export changes with them. The pack `version` bumps to 1.13.0 with the values.
# Both causes are folded into this one re-pin and both are deliberate. Values
# immediately before it (measured at this tip with the old weights):
#   manifest      998cd03659012e083d7e848b06e907f476c005a74816305842f1db45ecc92482
#   hands         fe90ec8e09536723a3611eda05c299499c75ce4685a38307fdf2de33a071d06d
#   seat_outcomes 568298ef39d69726e68adbf01095978dbb18887e6ce37d773582d0500a2a17ef
#   decisions     97d0a1e279e059250b0c37616b2617df66f6d3822060cda3854d2c780fa3995d
# THE MANIFEST MOVES HERE, unlike the T3 entry immediately above, and that is
# the expected signature for a PACK edit. `config_hash` is
# `counterfactual.baseline_config_hash(packs)`, canonicalized over the loaded
# pack MODELS, so the weight change alone would move it and the `version` bump
# does too; the `run_id` and `hand_id` columns derived from it move with it.
# Measured rather than assumed: the baseline config hash goes 492ed91c908126b6
# -> 3eb80f12c52ccf70 (first 16). T3 moved only three digests because it was
# engine-only and bumped no pack.
# RE-RECORDED for S3-T1 (improvement slice 3, 2026-08-21, slice-authorized): a
# STRONG draw's call bonus is SPLIT under a calling dial below 1.0 rather than
# protected from the dial in full — `personas_postflop._strong_draw_call_dial`,
# with `_DRAW_CALL_PROTECTED_SHARE` = 0.7. The five personas whose dial sits
# below 1.0 chase big draws slightly less, so the seeded twenty-five-hand export
# contains different actions and different money. Values immediately before it:
#   manifest      c6702078ad7cc7da963e6e21e38ca4dd8b29fdffa6c937327417200c5769c3c5
#   hands         88746bc22780d45e9cb0d1f233b6eed2d510b000befa31fb5cd879567bcd04fe
#   seat_outcomes 396a96ba84469917d4fd9acf7c182f369110c65b45182c8182bead4f0537df6c
#   decisions     a62f0dec1c517ca8d84fd52630f723719e7a40933d0a93dd498391854dac2094
# THE MANIFEST MOVES WITHOUT A PACK EDIT, which the T3 entry above names as "the
# thing to investigate". It was investigated, and the cause is benign: the
# manifest carries `row_counts`, and the DECISIONS row count falls from 475 to
# 460 because hands that used to see another street now end sooner. Measured
# directly — `config_hash` is IDENTICAL on both sides
# (3eb80f12c52ccf70f8b529cb152cf2323b14f8b41d6319ac5c9629b7e7ab7692), and
# `row_counts` is the ONLY key of the canonical manifest that differs. So the
# T3 note's rule still holds in the sense it was written: no pack edit, no
# `config_hash` move, no `run_id`/`hand_id` move. What it did not anticipate is
# that a behaviour-only change can still move the manifest through a row count.
# ATTRIBUTION PROVEN, not assumed: `_DRAW_CALL_PROTECTED_SHARE = 1.0` makes
# `_strong_draw_call_dial` return exactly 1.0 for every dial, which IS the
# `max(looseness, 1.0)` the engine used to carry; setting it to 1.0 at this tip
# reproduces all four digests above exactly, and restoring 0.7 reproduces the
# four below exactly.
# No new random draw was added and none precedes the action draw. The draw COUNT
# is not claimed invariant — the row-count move above is that non-invariance
# showing up in an artifact.
# NOT RE-RECORDED for S3-T1b (improvement slice 3, 2026-08-22): that ticket
# replaced the flat `_DRAW_CALL_PROTECTED_SHARE` with a per-node function,
# `personas_postflop._strong_draw_protected_share`, and the four digests below
# do not move. Recorded because it is the surprising direction: a real
# behaviour change that this 25-hand seeded export cannot see, where the
# smaller change before it moved all four.
# ⚠️ THE MECHANISM IS NOT "THE SAMPLE HAS NO STRONG DRAWS AT A DISAGREEING
# PRICE" — an earlier draft of this entry said that and it is FALSE. MEASURED
# by instrumenting the share over this exact export (25 hands, seed 777): it is
# evaluated 5 times, and NONE of the five equals the 0.7 S3-T1 would have used
# — they read 0.7476, 0.72, 1.0, 0.5733 and 0.8008. So the call merit really
# does differ from S3-T1's at four of the five, and once at 1.0 it differs from
# S3-T1's by the full 0.3 of the bonus. The digests are unchanged because none
# of those merit shifts flipped a SAMPLED ACTION: the draw is taken against
# normalized weights, and a weight can move without the outcome moving. Nothing
# downstream of an unflipped action can differ, so the hands, the seat outcomes
# and the decisions are byte-identical. Read this as a reminder of what a
# seeded golden actually pins — sampled outcomes, not merits — rather than as
# evidence that the engine did not change.
# The reproduction recipe in the entry above no longer runs as written — the
# constant it names is gone; the equivalent probe is to replace
# `_strong_draw_protected_share` with one returning 1.0, which is the
# `max(looseness, 1.0)` engine.
# RE-RECORDED for S3-T2 (improvement slice 3, 2026-08-22, slice-authorized):
# two calling dials move — the nit's `call_looseness` 0.45 -> 0.32 and the tag's
# 0.6 -> 0.38 — so both personas continue less often at every facing node, hands
# end differently and every byte of a seeded export changes with them. Values
# immediately before it:
#   manifest      acace563f84f179ddb1b500359bdb53aebf601b8b0b98a127d8e931e31d8003a
#   hands         c66037c53a80bd9203a1c39815c8e16172c7e58ae8a7ec62c4d39dfd127112ec
#   seat_outcomes 89d2f9951ab94cdce752bb3c1e6777f3a7922958ceb0a41c0fdf5d51bb0a86c3
#   decisions     4f27cec0c09e6f2821653484c2e2e6127aab58409d1bab1e6921cc02316f7f68
# THE MANIFEST MOVES, which is the expected signature for a PACK edit and the
# rule the T3 and S3-T1 entries above left standing: `config_hash` is
# canonicalized over the loaded pack MODELS, so the two weight changes alone
# would move it and the two `version` bumps (nit 1.10.0 -> 1.11.0, tag the same)
# do too; the `run_id` and `hand_id` columns derived from it move with it.
# ATTRIBUTION PROVEN, not assumed: with the two pack files reverted and every
# other edit in this branch left in place, all four digests above reproduce
# exactly and this test passes untouched; restoring the packs reproduces the
# four below. No engine file was changed by this ticket.
# RE-RECORDED for S3-T5 (improvement slice 3, ticket 5 — the late-street bet
# lever, 2026-08-22, slice-authorized): the LAG authors the new
# `late_street_bet` field at 1.0, so it bets unopened turns and rivers more
# often and every byte of a seeded export changes with it. Values immediately
# before it:
#   manifest      e12c3358b0dfe994ccd92cb2b722a78be2ae31a8928ec7ca5f82d51b8e79b377
#   hands         b50c38ab287e0bf570ec5be261305da10fc2c47c02be2428ce4a091bffa04f18
#   seat_outcomes c7b162892d353f6d6ed643c2688771c76e2962d8689a573d10c4fd2f4667e3fe
#   decisions     f2ac4f0b69d79c938358b044106aa1315b06321ec75987f877cc69de0b70e8b9
# THE MANIFEST MOVES for the reason the S3-T2 entry above gives: `config_hash`
# is canonicalized over the loaded pack MODELS, so a newly authored field and a
# `version` bump (lag 1.13.0 -> 1.14.0) move it, and the `run_id`/`hand_id`
# columns move with it.
# ATTRIBUTION PROVEN, not assumed: with the LAG pack file reverted and every
# other edit in this branch left in place, all four digests above reproduce
# exactly and this test passes untouched; restoring the pack reproduces the four
# below. An engine file WAS changed by this ticket, unlike S3-T2 — but it is a
# true no-op for a pack that does not author the field, and the commit that
# added it left all six packs unauthored and the whole suite green.
_GOLDEN_SEED = 777
_GOLDEN_N_HANDS = 25
_GOLDEN_MANIFEST_SHA256 = (
    "7e42a6243deb532ebbf6eaca4c64347bbe79fc9c2cc9e9b4bde27ac8c52c0193"
)
_GOLDEN_HANDS_SHA256 = (
    "948372e1cfdec7b0b014b4e706210bd08af54413836d0b8b36a5353c7633d2ae"
)
_GOLDEN_SEAT_OUTCOMES_SHA256 = (
    "32b645c7bc3173c5eec90ee849abea800bcbebacae6a8a0422dfb413645cda69"
)
_GOLDEN_DECISIONS_SHA256 = (
    "e7d41831ea14007b01922e4a8b74f4e8187b9847a3c87b3653f4998db6ebdb76"
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
