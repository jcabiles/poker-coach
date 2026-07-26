"""T-STACK — every seat resets to ~100bb at the start of every hand.

Supersedes W5-c3's carry-over buy-in cap (which only trimmed seats outside
[1bb, 200bb] and so still let the table drift deep). Deliberately
self-contained (no imports from `test_sim_session.py`, which a concurrent
slice is editing): a local unit test on `_apply_settlement`'s reset
arithmetic, plus a multi-hand integration run proving every seat starts every
hand at exactly `_STARTING_STACK_BB` while `net_bb` still carries session P&L.
Spec: docs/ai-dlc/tickets/persona-realism-wave-a.md (T-STACK).
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


# ------------------------------------------------------- unit: per-hand reset


def _seats():
    return [
        SimSeat(
            session_id="s", seat_index=i, is_hero=i == 0,
            persona_type=None if i == 0 else "tag",
            stack_bb=100.0, buyins_bb=100.0,
        )
        for i in range(9)
    ]


def _settle(seats, deltas):
    sim_session._apply_settlement(
        seats,
        Settlement(
            pots=[], winners_by_pot=[],
            deltas=[SeatDelta(seat=i, delta_bb=deltas[i]) for i in range(9)],
            showdown_seats=[0, 1],
        ),
    )


def test_winner_is_racked_back_to_starting_stack_and_net_preserved():
    seats = _seats()
    deltas = [0.0] * 9
    deltas[0], deltas[1] = -150.0, 150.0  # seat 1 would carry 250bb forward
    _settle(seats, deltas)
    assert seats[1].stack_bb == sim_session._STARTING_STACK_BB
    # net_bb (stack - buyins) is invariant across the reset correction.
    assert round(seats[1].stack_bb - seats[1].buyins_bb, 2) == 150.0
    assert round(seats[0].stack_bb - seats[0].buyins_bb, 2) == -150.0
    net_sum = round(sum(s.stack_bb - s.buyins_bb for s in seats), 2)
    assert net_sum == 0.0


def test_stack_inside_the_old_cap_band_is_reset_too():
    """The W5-c3 cap left a 150bb carry-over untouched; T-STACK does not."""
    seats = _seats()
    deltas = [0.0] * 9
    deltas[0], deltas[1] = -50.0, 50.0
    _settle(seats, deltas)
    assert seats[1].stack_bb == 100.0
    assert seats[1].buyins_bb == 50.0  # absorbed the -50 reset delta
    assert round(seats[1].stack_bb - seats[1].buyins_bb, 2) == 50.0


def test_repeated_settlements_accumulate_net_but_never_stack():
    seats = _seats()
    for _ in range(3):
        deltas = [0.0] * 9
        deltas[0], deltas[1] = -10.0, 10.0
        _settle(seats, deltas)
        assert all(s.stack_bb == 100.0 for s in seats)
    assert round(seats[0].stack_bb - seats[0].buyins_bb, 2) == -30.0
    assert round(seats[1].stack_bb - seats[1].buyins_bb, 2) == 30.0
    assert round(sum(s.stack_bb - s.buyins_bb for s in seats), 2) == 0.0


def test_reset_rounds_to_2dp():
    seats = _seats()
    deltas = [0.0] * 9
    deltas[0], deltas[1] = -99.55, 99.55
    _settle(seats, deltas)
    assert seats[0].stack_bb == 100.0 and seats[0].buyins_bb == 199.55
    assert seats[1].stack_bb == 100.0 and seats[1].buyins_bb == 0.45
    for s in seats:
        assert s.stack_bb == round(s.stack_bb, 2)
        assert s.buyins_bb == round(s.buyins_bb, 2)


# ------------------------------------------------------- integration: hands


def test_every_hand_starts_every_seat_at_100bb(db):
    """Every seat's carry-over stack is exactly the starting stack at every
    hand start across a 20-hand run, while net_bb still accumulates P&L."""
    view = create_session(db)
    saw_nonzero_net = False
    for hand_i in range(20):
        seats = db.exec(
            select(SimSeat).where(SimSeat.session_id == view.session_id)
        ).all()
        # start-of-hand: every live seat sits at exactly the starting stack.
        assert [s.stack_bb for s in seats] == [sim_session._STARTING_STACK_BB] * 9

        view = _play_current_hand(db, view)
        seats = db.exec(
            select(SimSeat).where(SimSeat.session_id == view.session_id)
        ).all()
        nets = [round(s.stack_bb - s.buyins_bb, 2) for s in seats]
        assert all(s.stack_bb == sim_session._STARTING_STACK_BB for s in seats)
        assert round(sum(nets), 2) == 0.0
        if hand_i >= 4 and any(n != 0.0 for n in nets):
            saw_nonzero_net = True
        view = deal_next_hand(db, view.session_id)
    assert saw_nonzero_net, "reset zeroed the ledger — net_bb must carry P&L"
