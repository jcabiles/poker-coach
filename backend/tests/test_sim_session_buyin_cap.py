"""W5-c3 — buy-in cap / per-hand stack normalization.

Deliberately self-contained (no imports from `test_sim_session.py`, which a
concurrent slice is editing): a small local unit test on `_apply_settlement`'s
cap-trim arithmetic, plus a short multi-hand integration run proving every
seat's carry-over stack stays inside `[_REBUY_FLOOR_BB, _STACK_CAP_BB]`
across hands. Spec: docs/ai-dlc/roadmap/persona-realism.md (W5-c3).
"""

from __future__ import annotations

import asyncio

import pytest
from sqlmodel import Session, create_engine, select

from app.db.migrate import run_migrations
from app.db.models import SimSeat
from app.domain.action import Decision
from app.domain.spot import ActionType
from app.domain.table.engine import SeatDelta, Settlement
from app.services import sim_session
from app.services.sim_session import create_session, deal_next_hand


@pytest.fixture
def db(tmp_path):
    url = f"sqlite:///{tmp_path / 'sim.db'}"
    run_migrations(url)
    engine = create_engine(url, connect_args={"check_same_thread": False})
    with Session(engine) as s:
        yield s


def apply_hero_action(*args, **kwargs):
    return asyncio.run(sim_session.apply_hero_action(*args, **kwargs))


def _hero_decision(view) -> Decision:
    kinds = {la.action for la in view.hand.legal_actions}
    if ActionType.CHECK in kinds:
        return Decision(action=ActionType.CHECK)
    if ActionType.CALL in kinds:
        return Decision(action=ActionType.CALL)
    return Decision(action=ActionType.FOLD)


def _play_current_hand(db, view):
    guard = 0
    while not view.hand.hand_over:
        guard += 1
        assert guard < 100, "hand did not terminate"
        view = apply_hero_action(db, view.session_id, _hero_decision(view))
    return view


# ----------------------------------------------------------- unit: cap-trim


def _seats():
    return [
        SimSeat(
            session_id="s", seat_index=i, is_hero=i == 0,
            persona_type=None if i == 0 else "tag",
            stack_bb=100.0, buyins_bb=100.0,
        )
        for i in range(9)
    ]


def test_cap_trims_winner_stack_and_preserves_net():
    seats = _seats()
    deltas = [0.0] * 9
    deltas[0], deltas[1] = -150.0, 150.0  # seat 1: 100 -> 250, over the 200bb cap
    settlement = Settlement(
        pots=[], winners_by_pot=[],
        deltas=[SeatDelta(seat=i, delta_bb=deltas[i]) for i in range(9)],
        showdown_seats=[0, 1],
    )
    sim_session._apply_settlement(seats, settlement)
    assert seats[1].stack_bb == sim_session._STACK_CAP_BB
    # net_bb (stack - buyins) is invariant across the cap-trim correction.
    assert round(seats[1].stack_bb - seats[1].buyins_bb, 2) == 150.0
    assert round(seats[0].stack_bb - seats[0].buyins_bb, 2) == -150.0
    # table-wide chip conservation still holds (settlement deltas sum to 0).
    net_sum = round(sum(s.stack_bb - s.buyins_bb for s in seats), 2)
    assert net_sum == 0.0


def test_cap_retriggers_on_repeated_wins():
    """The cap re-applies every settlement, not just the first time a seat
    crosses it (a seat sitting exactly at the cap must still be trimmed after
    winning again)."""
    seats = _seats()
    for _ in range(3):
        deltas = [0.0] * 9
        deltas[0], deltas[1] = -150.0, 150.0
        settlement = Settlement(
            pots=[], winners_by_pot=[],
            deltas=[SeatDelta(seat=i, delta_bb=deltas[i]) for i in range(9)],
            showdown_seats=[0, 1],
        )
        sim_session._apply_settlement(seats, settlement)
        assert seats[1].stack_bb <= sim_session._STACK_CAP_BB


def test_cap_leaves_stacks_inside_band_untouched():
    seats = _seats()
    deltas = [0.0] * 9
    deltas[0], deltas[1] = -50.0, 50.0  # seat 1: 100 -> 150, inside the band
    settlement = Settlement(
        pots=[], winners_by_pot=[],
        deltas=[SeatDelta(seat=i, delta_bb=deltas[i]) for i in range(9)],
        showdown_seats=[0, 1],
    )
    sim_session._apply_settlement(seats, settlement)
    assert seats[1].stack_bb == 150.0
    assert seats[1].buyins_bb == 100.0  # untouched: no correction applied


# ------------------------------------------------------- integration: hands


def test_stacks_stay_within_cap_across_hands(db):
    """Every seat's carry-over stack after settlement stays in
    [_REBUY_FLOOR_BB's rebuy target, _STACK_CAP_BB] across a short multi-hand
    run — the acceptance-criterion behavior, exercised at pytest speed (a
    longer 200-hand measurement is reported separately, not part of CI)."""
    view = create_session(db)
    for _ in range(20):
        view = _play_current_hand(db, view)
        seats = db.exec(select(SimSeat).where(SimSeat.session_id == view.session_id)).all()
        for s in seats:
            assert sim_session._REBUY_FLOOR_BB <= s.stack_bb <= sim_session._STACK_CAP_BB
        # chip conservation still holds with the cap correction in place.
        assert round(sum(s.stack_bb - s.buyins_bb for s in seats), 2) == 0.0
        view = deal_next_hand(db, view.session_id)
