"""M1 T2: characterization tests for `tools/table_stats.py`, the shared home
for `Hand`, `replay`, `settle_hand` and `stats_for` moved out of
`export_session.py` (no behaviour change) so real and simulated hands can be
measured by one definition. Section (c) (M1 T3) pins the RFI, flop c-bet
and Wilson-interval definitions on scripted hands.
"""

from __future__ import annotations

import random

from app.domain.action import Decision
from app.domain.archetypes import VillainType
from app.domain.personas import load_persona_packs
from app.domain.spot import ActionType, Street
from app.domain.table.deck import deal_hand
from app.domain.table.engine import apply, start_hand
from tools.export_analytics import play_one_hand
from tools.table_stats import Hand, replay, settle_hand, stats_for, wilson

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


# ---------------------------------------------------------------------------
# (c) RFI and flop c-bet on scripted hands; Wilson interval
# ---------------------------------------------------------------------------

# Button at seat 0 -> seat 1 SB, 2 BB, 3 LJ, 4 HJ, 5 CO. Preflop order is
# LJ, HJ, CO, BTN, SB, BB; postflop order starts at SB.
_F = Decision(action=ActionType.FOLD)
_C = Decision(action=ActionType.CALL)
_X = Decision(action=ActionType.CHECK)


def _r(size_bb: float) -> Decision:
    return Decision(action=ActionType.RAISE, size_bb=size_bb)


def _b(size_bb: float) -> Decision:
    return Decision(action=ActionType.BET, size_bb=size_bb)


def _scripted(decisions: list[Decision], stacks_bb: list[float] | None = None):
    state = start_hand(deal_hand(random.Random(7), 6), 0, stacks_bb or [100.0] * 6)
    for d in decisions:
        state = apply(state, d)
    hand = Hand(0, "scripted", state)
    replays = {0: replay(hand)}
    nets = {0: {}}
    shows = {0: []}
    return hand, replays, nets, shows


def _seat_stats(scripted, seat: int):
    hand, replays, nets, shows = scripted
    return stats_for([seat], {seat: "x"}, [hand], replays, nets, shows)


def test_rfi_folded_to_lj_raise_is_an_open():
    s = _scripted([_r(2.5), _F, _F, _F, _F, _F])
    st, per_pos = _seat_stats(s, 3)
    assert (st["rfi_opp"], st["rfi"]) == (1, 1)
    assert (per_pos["LJ"]["rfi_opp"], per_pos["LJ"]["rfi"]) == (1, 1)
    # HJ acted after a raise: no RFI chance.
    st_hj, _ = _seat_stats(s, 4)
    assert st_hj["rfi_opp"] == 0


def test_rfi_limp_is_a_chance_not_an_open():
    s = _scripted([_C, _F, _F, _F, _F, _X])
    st, per_pos = _seat_stats(s, 3)
    assert (st["rfi_opp"], st["rfi"]) == (1, 0)
    assert (per_pos["LJ"]["rfi_opp"], per_pos["LJ"]["rfi"]) == (1, 0)
    # HJ folded after a limp: not folded to, so no RFI chance.
    assert _seat_stats(s, 4)[0]["rfi_opp"] == 0


def test_rfi_bb_walk_is_no_chance_for_bb_but_is_for_sb():
    s = _scripted([_F, _F, _F, _F, _F])
    st_bb, per_pos_bb = _seat_stats(s, 2)
    assert st_bb["rfi_opp"] == 0
    assert per_pos_bb["BB"]["rfi_opp"] == 0
    st_sb, _ = _seat_stats(s, 1)
    assert (st_sb["rfi_opp"], st_sb["rfi"]) == (1, 0)


def test_cbet_raiser_checked_to_then_bets():
    # LJ opens, BB calls; flop: BB checks, LJ bets.
    s = _scripted([_r(2.5), _F, _F, _F, _F, _C, _X, _b(3.0)])
    st, _ = _seat_stats(s, 3)
    assert (st["cbet_opp"], st["cbet"]) == (1, 1)
    # The caller is not the preflop raiser: no chance.
    assert _seat_stats(s, 2)[0]["cbet_opp"] == 0


def test_cbet_donk_bet_before_raiser_is_no_chance():
    # LJ opens, BB calls; flop: BB leads, LJ calls.
    s = _scripted([_r(2.5), _F, _F, _F, _F, _C, _b(3.0), _C])
    st, _ = _seat_stats(s, 3)
    assert st["saw_flop"] == 1
    assert (st["cbet_opp"], st["cbet"]) == (0, 0)


def test_preflop_fold_out_has_no_flop_and_no_cbet_chance():
    s = _scripted([_r(2.5), _F, _F, _F, _F, _F])
    st, _ = _seat_stats(s, 3)
    assert st["saw_flop"] == 0
    assert st["cbet_opp"] == 0


def test_cbet_all_in_preflop_raiser_is_no_chance():
    # LJ (20bb stack) jams, BB calls: no flop action for either seat.
    stacks = [100.0, 100.0, 100.0, 20.0, 100.0, 100.0]
    s = _scripted([_r(20.0), _F, _F, _F, _F, _C], stacks)
    hand = s[0]
    assert len(hand.revealed) == 5  # auto-runout: the flop was seen
    st, _ = _seat_stats(s, 3)
    assert st["saw_flop"] == 1
    assert st["cbet_opp"] == 0


def test_wilson_interval():
    assert wilson(0, 0) == (0.0, 1.0)
    lo, hi = wilson(20, 100)
    assert round(lo, 3) == 0.133
    assert round(hi, 3) == 0.289
