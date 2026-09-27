"""M1 T2: characterization tests for `tools/table_stats.py`, the shared home
for `Hand`, `replay`, `settle_hand` and `stats_for` moved out of
`export_session.py` (no behaviour change) so real and simulated hands can be
measured by one definition.
"""

from __future__ import annotations

import random

from app.domain.archetypes import VillainType
from app.domain.personas import load_persona_packs
from app.domain.spot import ActionType, Street
from tools.export_analytics import play_one_hand
from tools.table_stats import Hand, replay, settle_hand, stats_for

# 6-max seat map used throughout: seat 0 stands in for the owner (TAG), the
# rest are the other five archetypes the ticket names.
_PERSONA_BY_SEAT = {
    0: VillainType.TAG.value,
    1: VillainType.NIT.value,
    2: VillainType.LAG.value,
    3: VillainType.TAG.value,
    4: VillainType.TAG.value,
    5: VillainType.CALLING_STATION.value,
}
_PACKS = load_persona_packs()


def _play(hand_seed: int, button_seat: int):
    state = play_one_hand(
        random.Random(hand_seed),
        hand_seed,
        button_seat,
        _PERSONA_BY_SEAT,
        _PACKS,
        stacks_bb=[100.0] * 6,
    )["state"]
    return state


def _expected_counts(hand: Hand, seat: int, showdown_seats: list[int]) -> dict[str, int]:
    """VPIP/PFR/saw_flop/WTSD for one seat, read directly off the hand's raw
    `action_history` — deliberately not reusing `stats_for`'s own logic, so
    this is an independent check on what it returns."""
    pre = [
        a
        for a in hand.history
        if a.street is Street.PREFLOP
        and a.action is not ActionType.POST
        and hand.seat_of[a.position] == seat
    ]
    if not pre:
        return {"hands": 0, "vpip": 0, "pfr": 0, "saw_flop": 0, "wtsd": 0}
    vpip = any(a.action in (ActionType.CALL, ActionType.RAISE) for a in pre)
    pfr = any(a.action is ActionType.RAISE for a in pre)
    acted_flop = any(
        a.street is Street.FLOP and hand.seat_of[a.position] == seat for a in hand.history
    )
    saw_flop = acted_flop or (hand.seats[seat].status != "folded" and len(hand.revealed) >= 3)
    return {
        "hands": 1,
        "vpip": int(vpip),
        "pfr": int(pfr),
        "saw_flop": int(saw_flop),
        "wtsd": int(seat in showdown_seats),
    }


# ---------------------------------------------------------------------------
# (a) a few seeded 6-max hands: replay reconciles, settle_hand deltas net 0
# ---------------------------------------------------------------------------


def test_replay_reconciles_and_settle_hand_deltas_sum_to_zero():
    for i in range(10):
        state = _play(hand_seed=1000 + i, button_seat=i % 6)
        hand = Hand(i, f"sim-{i}", state)

        replay(hand)  # asserts internally; raising is the failure mode

        net, showdown = settle_hand(hand)
        assert len(net) == 6
        assert abs(sum(net.values())) < 1e-6


# ---------------------------------------------------------------------------
# (b) hand-computed VPIP/PFR/saw_flop/WTSD match stats_for, for 2 hands
# ---------------------------------------------------------------------------


def test_stats_for_matches_hand_computed_counts():
    for hand_seed, button_seat in ((2001, 0), (2002, 3)):
        state = _play(hand_seed=hand_seed, button_seat=button_seat)
        hand = Hand(0, f"sim-{hand_seed}", state)
        replays = {hand.hand_no: replay(hand)}
        net, showdown = settle_hand(hand)
        nets = {hand.hand_no: net}
        shows = {hand.hand_no: showdown}

        for seat in range(6):
            expected = _expected_counts(hand, seat, showdown)
            st, _ = stats_for([seat], {seat: "x"}, [hand], replays, nets, shows)
            assert st["hands"] == expected["hands"], (hand_seed, seat)
            if expected["hands"]:
                assert st["vpip"] == expected["vpip"], (hand_seed, seat)
                assert st["pfr"] == expected["pfr"], (hand_seed, seat)
                assert st["saw_flop"] == expected["saw_flop"], (hand_seed, seat)
                assert st["wtsd_num"] == expected["wtsd"], (hand_seed, seat)
