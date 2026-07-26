"""Persona pack schema + engine tests, incl. the S3 closed-loop stat bands.

The four stat rows measure **AUTHORED RANGE WIDTH**, not tracker stats. The
docstring here used to claim "open-freq ~ VPIP, first-in-raise ~ PFR"; that
equivalence is FALSE at 9-max and was the root of a wrong test (see the long
note above `BANDS`). Population VPIP/PFR/gap live in metric #3 of the S4
harness (`tests/test_personas_postflop.py::_persona_stats_ext`), which plays
whole hands; this file only asks "how wide is each node as authored?"
(spec `docs/ai-dlc/specs/simulate-s3.md`).
"""

import json
import random

import pytest
from pydantic import ValidationError

from app.domain.archetypes import VillainType
from app.domain.content.models import PersonaPack
from app.domain.personas import load_persona_packs, sample_preflop_action
from app.domain.spot import ActionType, Position
from app.domain.table.deck import deal_hand, positions_for_button

# ---------------------------------------------------------------- fixtures


def _pack(preflop: list[dict], persona: str = "tag") -> dict:
    return {
        "id": f"persona_{persona}",
        "version": "1.0.0",
        "domain": "persona",
        "persona": persona,
        "display_name": persona,
        "sizing": {"open_bb": 2.5, "threebet_mult": 3.0, "fourbet_mult": 2.2},
        "preflop": preflop,
    }


FIXTURE = PersonaPack.model_validate(
    _pack(
        [
            {
                "facing": "unopened",
                "positions": ["BTN"],
                "mixes": [
                    {"combos": "AA,KK", "weights": {"raise": 1.0}},
                    {"combos": "22+", "weights": {"raise": 0.5, "limp": 0.5}},
                ],
            },
            {
                "facing": "unopened",
                "positions": None,
                "mixes": [{"combos": "QQ+", "weights": {"raise": 1.0}}],
            },
            {
                "facing": "vs_rfi",
                "positions": None,
                "mixes": [
                    {"combos": "77", "weights": {"call": 1.0}},
                    {"combos": "AA", "weights": {"3bet": 0.4}},  # remainder = implicit fold
                ],
            },
        ]
    )
)

AA = ("As", "Ad")
SEVENS = ("7c", "7d")
FIVES = ("5c", "5d")
TREY_DEUCE = ("3c", "2d")

# ------------------------------------------------------- schema validation


def test_persona_pack_rejects_bad_action_vocabulary():
    with pytest.raises(ValidationError, match="not allowed facing"):
        _validate([{"facing": "unopened", "positions": None,
                    "mixes": [{"combos": "AA", "weights": {"call": 1.0}}]}])


def test_persona_pack_rejects_weights_sum_above_one():
    with pytest.raises(ValidationError, match="sum"):
        _validate([{"facing": "unopened", "positions": None,
                    "mixes": [{"combos": "AA", "weights": {"raise": 0.7, "limp": 0.7}}]}])


def test_persona_pack_rejects_unsupported_range_token():
    with pytest.raises(ValidationError, match="range token"):
        _validate([{"facing": "unopened", "positions": None,
                    "mixes": [{"combos": "A5s-A2s", "weights": {"raise": 1.0}}]}])


def test_persona_pack_rejects_explicit_node_after_wildcard():
    with pytest.raises(ValidationError, match="after wildcard"):
        _validate([
            {"facing": "unopened", "positions": None,
             "mixes": [{"combos": "AA", "weights": {"raise": 1.0}}]},
            {"facing": "unopened", "positions": ["BTN"],
             "mixes": [{"combos": "AA", "weights": {"raise": 1.0}}]},
        ])


def test_persona_pack_rejects_second_wildcard_per_facing():
    with pytest.raises(ValidationError, match="wildcard"):
        _validate([
            {"facing": "unopened", "positions": None,
             "mixes": [{"combos": "AA", "weights": {"raise": 1.0}}]},
            {"facing": "unopened", "positions": None,
             "mixes": [{"combos": "KK", "weights": {"raise": 1.0}}]},
        ])


def test_persona_pack_rejects_overlapping_explicit_positions():
    with pytest.raises(ValidationError, match="duplicate position coverage"):
        _validate([
            {"facing": "unopened", "positions": ["BTN", "CO"],
             "mixes": [{"combos": "AA", "weights": {"raise": 1.0}}]},
            {"facing": "unopened", "positions": ["CO"],
             "mixes": [{"combos": "KK", "weights": {"raise": 1.0}}]},
        ])


def _validate(preflop: list[dict]) -> PersonaPack:
    return PersonaPack.model_validate(_pack(preflop))


def test_loader_raises_on_duplicate_persona(tmp_path):
    pack = _pack([{"facing": "unopened", "positions": None,
                   "mixes": [{"combos": "AA", "weights": {"raise": 1.0}}]}])
    (tmp_path / "a.json").write_text(json.dumps(pack))
    (tmp_path / "b.json").write_text(json.dumps(pack))
    with pytest.raises(ValueError, match="duplicate persona"):
        load_persona_packs(tmp_path)


# --------------------------------------------------------------- sampling


def test_wire_translation_limp_is_call_and_3bet_is_raise():
    rng = random.Random(7)
    # BTN 55 hits the mixed 22+ row: limp draws must translate to CALL.
    names = set()
    for _ in range(200):
        act = sample_preflop_action(FIXTURE, Position.BTN, "unopened", FIVES, rng)
        names.add(act.name)
        assert act.action == (ActionType.CALL if act.name == "limp" else ActionType.RAISE)
    assert names == {"limp", "raise"}  # a mixed row genuinely mixes

    threebet = sample_preflop_action(FIXTURE, Position.SB, "vs_rfi", AA, random.Random(0))
    while threebet.name == "fold":  # 0.4 3bet / 0.6 implicit fold
        threebet = sample_preflop_action(FIXTURE, Position.SB, "vs_rfi", AA, rng)
    assert threebet == ("3bet", ActionType.RAISE)


def test_first_matching_mix_wins():
    # AA on BTN is in both mixes; the first (raise 1.0) must win every time.
    rng = random.Random(3)
    for _ in range(50):
        assert sample_preflop_action(FIXTURE, Position.BTN, "unopened", AA, rng).name == "raise"


def test_explicit_position_node_beats_wildcard_and_wildcard_covers_rest():
    rng = random.Random(11)
    # 77 unopened: BTN hits the explicit node (22+ row); CO falls to wildcard (QQ+ only) -> fold.
    assert sample_preflop_action(FIXTURE, Position.BTN, "unopened", SEVENS, rng).name != "fold"
    assert sample_preflop_action(FIXTURE, Position.CO, "unopened", SEVENS, rng).name == "fold"


def test_unmatched_hand_or_facing_folds():
    rng = random.Random(5)
    assert sample_preflop_action(FIXTURE, Position.CO, "unopened", TREY_DEUCE, rng) == (
        "fold",
        ActionType.FOLD,
    )
    assert sample_preflop_action(FIXTURE, Position.CO, "vs_4bet", AA, rng).name == "fold"


def test_same_seed_is_deterministic():
    def draw(seed):
        rng = random.Random(seed)
        return [
            sample_preflop_action(FIXTURE, Position.BTN, "unopened", FIVES, rng).name
            for _ in range(100)
        ]

    assert draw(42) == draw(42)
    assert draw(42) != draw(43)  # and the mix isn't degenerate


# ---------------------------------------------- closed-loop stat bands (S3)

# ============================ WHAT THESE BANDS MEASURE (read before editing) ==
# `_stats` samples EVERY seat at `facing="unopened"` and divides by DEALS*9. It
# therefore measures **AUTHORED RANGE WIDTH** — "what fraction of dealt hands
# does this pack's `unopened` node open with, averaged over the nine seats" —
# and NOT population VPIP/PFR, which is what a tracker reports.
#
# Those are DIFFERENT QUANTITIES and cannot both be satisfied by one band. At
# 9-max a seat usually arrives already FACING an open, so its decision is routed
# to `vs_rfi` / `vs_limpers` and never reaches the `unopened` node at all.
# Authored width is therefore always LARGER than realised PFR. Until W5-b1 the
# open-freq / first-in-raise rows held population-PFR numbers while the function
# computed authored width — the test was simply asking the wrong question, and
# it went unnoticed because at the old (much too narrow) widths the two happened
# to be close.
#
# ⚠ THE CONVERSION IS NOT A CONSTANT — do NOT re-derive these bands by dividing
# a §5 PFR target by ~0.5. That ratio was measured at the OLD narrow widths
# (nit x0.51, tag x0.54, lag x0.50) and **FALLS AS RANGES WIDEN**, because wider
# opens across the table mean more seats arrive facing a raise. Measured at the
# W5-b1 widths the ratio is ~0.35: nit reaches PFR 10.4 from 28.5 authored, lag
# PFR 17.1 from 43.2 authored. Anyone who "fixes" a failure here by scaling a
# §5 number will get a badly wrong range. Fit the width, then MEASURE.
#
# STATUS: these are **authored-width bands, DIRECTIONAL, never HARD**. They pin
# that the packs still say what this slice made them say; they are not evidence
# about persona realism. The population VPIP/PFR/gap check is **metric #3**
# (`tests/test_personas_postflop.py::_persona_stats_ext`), which plays whole
# hands, and it is REPORTED-not-gated until the W4-b single band re-anchor.
#
# TOLERANCE: the open-freq / first-in-raise bands below are the **exact
# combo-weighted authored width ±2.0pp**. Sizing: across a 25-seed sweep of
# `_stats` the worst per-row sd is 0.45pp and the worst full span is 2.16pp, so
# ±2.0pp is ~4.4 sd and leaves ≥0.9pp beyond the widest excursion observed; the
# pinned-seed value sits ≥1.4pp inside both edges of every row.
# =============================================================================

# persona -> (open-freq, first-in-raise, 3-bet, vs_rfi continue), all %.
# Rows 1-2 are AUTHORED `unopened` WIDTH (see above), not VPIP/PFR.
BANDS = {
    "passive_fish": ((28, 45), (3, 9), (0, 2), (35, 55)),
    "calling_station": ((40, 60), (0, 8), (0, 1), (50, 70)),
    # nit/tag/lag rows 1-2 RE-SCOPED by W5-b1 (2026-07-25) from population-PFR
    # numbers to the authored widths this slice actually ships (exact
    # combo-weighted: nit 28.45 open / 27.38 raise, tag 33.97, lag 43.15).
    # Rows 3-4 are UNTOUCHED — separate levers W5-b1 does not move.
    "nit": ((26, 30), (25, 29), (1, 2), (5, 15)),
    "tag": ((32, 36), (32, 36), (6, 7), (15, 28)),
    # lag/maniac open-freq re-anchored (P1 M3, persona-realism-p1): M3 deleted
    # the non-SB unopened open-limps from both packs, so open-freq collapsed
    # onto first-in-raise (+~0-1pp of retained SB limps). Measured at the
    # pinned seed: lag 23.55 (raise 23.29), maniac 35.64 (raise 34.62). The
    # old floors (24 / 45) counted open-limps that no longer exist — intended
    # M3 behavior, not a range regression (first-in-raise, 3-bet and
    # vs_rfi-continue all stayed inside their existing bands).
    # W5-b1 supersedes rows 1-2 of that anchor with the authored width 43.15.
    "lag": ((41, 45), (41, 45), (8, 12), (25, 42)),
    # maniac vs_rfi-continue re-anchored (W3R-1): the old (45, 70) codified the
    # deleted any-two `vs_rfi "*"` cold-call. The `vs_rfi` node is now the
    # 3-tier legit loose-flat range (premium 3bet / strong 3bet-or-flat /
    # wide-marginal flat); continue-rate measured at 45.99% on the pinned seed
    # (hash-stable). Snug window around the measured value. The 3bet band stays
    # [12,20] (restored via tier-2 3bet:0.45, measured 12.59%) — NOT re-anchored.
    "maniac": ((30, 45), (30, 40), (12, 20), (44, 48)),
}

DEALS = 1112  # pinned: 1,112 deals x 9 seats ~= 10k samples per facing


def _stats(pack: PersonaPack) -> tuple[float, float, float, float]:
    """Authored width of the `unopened` and `vs_rfi` nodes (see BANDS above).

    The two facings draw from SEPARATE rngs (`rng_u` / `rng_v`), both pinned to
    the same seed. They used to share one stream, which silently COUPLED the
    measurements: `sample_preflop_action` consumes a draw only when the hand
    matches a mix, so widening the `unopened` ranges displaced every subsequent
    `vs_rfi` draw and moved the 3-bet / vs_rfi-continue readings even though
    those nodes were untouched. W5-b1 hit exactly that — the tag and lag
    continue rows dropped to 14.97 / 24.69, grazing under their 15 / 25 floors,
    purely from stream displacement (the exact combo-weighted population values
    are 15.481 / 25.370 and never changed). Decoupling makes rows 3-4
    structurally independent of any `unopened` edit, which is what the BANDS
    comment claims they are. This is a MEASUREMENT repair: no band number in
    rows 3-4 moved, and all six personas pass them at the pinned seed.

    Known residual (pre-existing, NOT introduced here): rows 3-4 are still Monte
    Carlo estimates of exactly-computable quantities, and tag's snug (6, 7)
    3-bet and (15, 28) continue rows sit within ~1 sd of an edge — across a
    25-seed sweep they span 6.19-7.31 and 14.88-16.31. They pass at the pinned
    seed; a future slice that needs them robust should compute them exactly.
    """
    rng_u = random.Random(20260710)
    rng_v = random.Random(20260710)
    positions = positions_for_button(0)
    n = DEALS * 9
    opened = first_in_raised = threebet = continued = 0
    for _ in range(DEALS):
        dealt = deal_hand(rng_u)
        for seat, pos in enumerate(positions):
            hole = dealt.hole_cards[seat]
            a = sample_preflop_action(pack, pos, "unopened", hole, rng_u)
            opened += a.name != "fold"
            first_in_raised += a.name == "raise"
            b = sample_preflop_action(pack, pos, "vs_rfi", hole, rng_v)
            threebet += b.name == "3bet"
            continued += b.name != "fold"
    return tuple(100.0 * c / n for c in (opened, first_in_raised, threebet, continued))


def test_all_six_persona_packs_load():
    packs = load_persona_packs()
    missing = set(VillainType) - set(packs)
    if missing:
        pytest.skip(f"personas not authored yet (T2/T3 land at fan-in): {sorted(missing)}")
    assert set(packs) == set(VillainType)
    for vt, pack in packs.items():
        assert pack.persona == vt
        assert pack.preflop


@pytest.mark.parametrize("persona", sorted(BANDS))
def test_persona_stat_bands(persona):
    packs = load_persona_packs()
    vt = VillainType(persona)
    if vt not in packs:
        pytest.skip(f"content/personas/{persona}.json not authored yet — lands at fan-in")
    stats = _stats(packs[vt])
    labels = ("open-freq", "first-in-raise", "3-bet", "vs_rfi-continue")
    for label, value, (lo, hi) in zip(labels, stats, BANDS[persona], strict=True):
        assert lo <= value <= hi, f"{persona} {label} {value:.2f}% outside [{lo}, {hi}]"
