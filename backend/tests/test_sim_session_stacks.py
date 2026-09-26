"""Stacks carry over hand to hand; a seat below 50bb tops back up to 100bb.

Owner ruling 2026-09-25, superseding T-STACK's re-buy before every deal: the
table should read like a real cash game, so a seat that wins 20bb starts the
next hand with 120bb. Unit tests on `_top_up_seats` arithmetic plus a
multi-hand integration run proving each hand starts from the last one's
finishing stacks while `net_bb` carries session P&L.
"""

from __future__ import annotations

import asyncio

import pytest
from sqlmodel import Session, create_engine, select

from app.db.migrate import run_migrations
from app.db.models import SimHand, SimSeat
from app.domain.action import Decision
from app.domain.spot import ActionType
from app.domain.table.engine import HandState, SeatDelta, Settlement
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


# ------------------------------------------------------ unit: per-hand re-buy


def _seats():
    return [
        SimSeat(
            session_id="s",
            seat_index=i,
            is_hero=i == 0,
            persona_type=None if i == 0 else "tag",
            stack_bb=100.0,
            buyins_bb=100.0,
        )
        for i in range(9)
    ]


def _settle(seats, deltas):
    sim_session._apply_settlement(
        seats,
        Settlement(
            pots=[],
            winners_by_pot=[],
            deltas=[SeatDelta(seat=i, delta_bb=deltas[i]) for i in range(9)],
            showdown_seats=[0, 1],
        ),
    )


def test_winner_and_loser_carry_their_stacks_into_the_next_hand():
    seats = _seats()
    deltas = [0.0] * 9
    deltas[0], deltas[1] = 20.0, -20.0
    _settle(seats, deltas)
    sim_session._top_up_seats(seats)
    assert seats[0].stack_bb == 120.0
    assert seats[1].stack_bb == 80.0
    assert all(s.stack_bb == 100.0 for s in seats[2:])
    assert all(s.buyins_bb == 100.0 for s in seats)


def test_seat_below_50bb_tops_up_to_100_and_keeps_its_net():
    seats = _seats()
    deltas = [0.0] * 9
    deltas[0], deltas[1], deltas[2] = -50.01, -100.0, 150.01
    _settle(seats, deltas)
    sim_session._top_up_seats(seats)
    assert seats[0].stack_bb == 100.0  # 49.99 -> topped up
    assert seats[1].stack_bb == 100.0  # busted -> topped up
    assert seats[2].stack_bb == 250.01  # no upper cap
    assert round(seats[0].stack_bb - seats[0].buyins_bb, 2) == -50.01
    assert round(seats[1].stack_bb - seats[1].buyins_bb, 2) == -100.0
    assert round(seats[2].stack_bb - seats[2].buyins_bb, 2) == 150.01
    assert round(sum(s.stack_bb - s.buyins_bb for s in seats), 2) == 0.0


def test_seat_at_exactly_50bb_is_not_topped_up():
    seats = _seats()
    deltas = [0.0] * 9
    deltas[0], deltas[1] = -50.0, 50.0
    _settle(seats, deltas)
    sim_session._top_up_seats(seats)
    assert seats[0].stack_bb == 50.0
    assert seats[0].buyins_bb == 100.0


# ------------------------------------------------------- integration: hands


def test_each_hand_starts_from_the_previous_hands_finishing_stacks(db):
    view = create_session(db)
    seats = db.exec(select(SimSeat).where(SimSeat.session_id == view.session_id)).all()
    assert all(s.stack_bb == 100.0 for s in seats)
    saw_carry = False
    for _ in range(20):
        view = _play_current_hand(db, view)
        finished = {
            s.seat_index: s.stack_bb
            for s in db.exec(select(SimSeat).where(SimSeat.session_id == view.session_id)).all()
        }
        view = deal_next_hand(db, view.session_id)
        state = HandState.model_validate_json(
            db.exec(
                select(SimHand)
                .where(SimHand.session_id == view.session_id)
                .order_by(SimHand.hand_no.desc())  # type: ignore[attr-defined]
            )
            .first()
            .state_json
        )
        for s in state.seats:
            starting = round(s.stack_bb + s.invested_total_bb, 2)
            expected = 100.0 if finished[s.seat] < 50.0 else finished[s.seat]
            assert starting == expected
            if starting != 100.0:
                saw_carry = True
        seats = db.exec(select(SimSeat).where(SimSeat.session_id == view.session_id)).all()
        assert round(sum(s.stack_bb - s.buyins_bb for s in seats), 2) == 0.0
    assert saw_carry, "no stack ever carried over in 20 hands"
