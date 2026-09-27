"""T1 (M1 6-max baseline): table-size conformance for the analytics export's
single-hand primitives.

Two legs, per the ticket:
1. `_draw_buyin_targets(seed, n)` draws `n` targets from the same per-hand
   RNG stream a 9-draw uses, so a 6-max draw is exactly the first 6 of the
   9-max draw for the same seed.
2. `play_one_hand` given 6 starting stacks plays a 6-max hand: 6 seat rows
   whose positions are exactly the 6-max position set, a `"state"` whose
   seats list has length 6, and identical output across two calls with the
   same seeds (determinism).
"""

from __future__ import annotations

import random

import pytest

from app.domain.personas import load_persona_packs
from tools import export_analytics as ea

# ---------------------------------------------------------------------------
# 1. _draw_buyin_targets at n=6
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("hand_seed", [0, 1, 42, 123456789, 999999999])
def test_six_draw_is_prefix_of_nine_draw(hand_seed):
    six = ea._draw_buyin_targets(hand_seed, 6)
    nine = ea._draw_buyin_targets(hand_seed)
    assert len(six) == 6
    assert six == nine[:6]


# ---------------------------------------------------------------------------
# 2. play_one_hand at a 6-max table
# ---------------------------------------------------------------------------

_SIX_MAX_POSITIONS = {"BTN", "SB", "BB", "LJ", "HJ", "CO"}

_SIX_MAX_LINEUP = [
    ea.VillainType.TAG.value,
    ea.VillainType.NIT.value,
    ea.VillainType.LAG.value,
    ea.VillainType.TAG.value,
    ea.VillainType.TAG.value,
    ea.VillainType.CALLING_STATION.value,
]


def _play_six_max_hand():
    packs = load_persona_packs()
    persona_by_seat = {i: _SIX_MAX_LINEUP[i] for i in range(6)}
    rng = random.Random(101)
    return ea.play_one_hand(
        rng,
        hand_seed=202,
        button_seat=0,
        persona_by_seat=persona_by_seat,
        packs=packs,
        stacks_bb=[100.0] * 6,
    )


def test_six_max_hand_has_six_seats_with_six_max_positions():
    res = _play_six_max_hand()
    assert len(res["seats"]) == 6
    positions = {row["position"] for row in res["seats"]}
    assert positions == _SIX_MAX_POSITIONS
    assert len(res["state"].seats) == 6


def test_six_max_hand_is_deterministic_across_two_calls():
    res1 = _play_six_max_hand()
    res2 = _play_six_max_hand()
    assert res1["hand"] == res2["hand"]
    assert res1["seats"] == res2["seats"]
    assert res1["decisions"] == res2["decisions"]
