"""T-STACK — every seat re-buys to a ~100bb spread before every hand.

Supersedes W5-c3's carry-over buy-in cap (which only trimmed seats outside
[1bb, 200bb] and so still let the table drift deep). The re-buy target is a
narrow BAND (`_BUYIN_MIN_BB`.._BUYIN_MAX_BB`), not a single constant: equal
stacks make `engine.settle` side pots structurally impossible, and a training
product cannot silently lose that situation.

Acceptance evidence for the band, measured with a PERSONA in the hero seat
(n=600): contested side pots in 6.2% of hands, up from a structural 0%. Do not
quote the ~18% figure a check/call harness hero produces — a hero that never
folds inflates it ~3x, and the hero helper in this file is exactly such a
bot. Note also that this number is a PROXY for the roster's all-in rate
(>=2 seats all-in in ~13% of hands) and will therefore FALL as the initiative
fixes the over-commitment defect; it is acceptance evidence that the situation
is reachable at all, not a durable target.

Deliberately self-contained (no imports from `test_sim_session.py`, which a
concurrent slice is editing): local unit tests on `_rebuy_seats` arithmetic,
plus a multi-hand integration run proving every seat starts every hand inside
the band while `net_bb` still carries session P&L.
Spec: docs/ai-dlc/tickets/persona-realism-wave-a.md (T-STACK).
"""

from __future__ import annotations

import asyncio
import random

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


# ------------------------------------------------------ unit: per-hand re-buy


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


def test_rebuy_lands_inside_the_band_and_preserves_net():
    """A big winner is racked back down, a busted seat topped back up, and in
    both directions `buyins_bb` absorbs the move so net_bb is untouched."""
    seats = _seats()
    deltas = [0.0] * 9
    deltas[0], deltas[1] = -99.55, 99.55  # seat 0 -> 0.45, seat 1 -> 199.55
    _settle(seats, deltas)
    sim_session._rebuy_seats(seats, random.Random(0))
    for s in seats:
        assert sim_session._BUYIN_MIN_BB <= s.stack_bb <= sim_session._BUYIN_MAX_BB
    assert round(seats[0].stack_bb - seats[0].buyins_bb, 2) == -99.55
    assert round(seats[1].stack_bb - seats[1].buyins_bb, 2) == 99.55
    assert round(sum(s.stack_bb - s.buyins_bb for s in seats), 2) == 0.0


def test_rebuy_draws_are_2dp_exact_and_not_all_equal():
    """Whole-cent draws keep the ledger exact; unequal stacks are what makes
    side pots possible at all (`engine.settle` levels on invested_total_bb)."""
    seats = _seats()
    seen = set()
    for trial in range(200):
        sim_session._rebuy_seats(seats, random.Random(trial))
        for s in seats:
            assert s.stack_bb == round(s.stack_bb, 2)
            assert s.buyins_bb == round(s.buyins_bb, 2)
            seen.add(s.stack_bb)
    assert len(seen) > 1, "an equal-stack table makes side pots impossible"
    assert all(
        sim_session._BUYIN_MIN_BB <= v <= sim_session._BUYIN_MAX_BB for v in seen
    )


def test_repeated_hands_accumulate_net_but_never_the_stack():
    seats = _seats()
    for i in range(20):
        sim_session._rebuy_seats(seats, random.Random(i))
        deltas = [0.0] * 9
        deltas[0], deltas[1] = -10.0, 10.0
        _settle(seats, deltas)
    assert round(seats[0].stack_bb - seats[0].buyins_bb, 2) == -200.0
    assert round(seats[1].stack_bb - seats[1].buyins_bb, 2) == 200.0
    assert round(sum(s.stack_bb - s.buyins_bb for s in seats), 2) == 0.0


# ------------------------------------------------------- integration: hands


def test_every_hand_starts_every_seat_inside_the_buyin_band(db):
    """No stack carries over: every seat starts every hand inside the re-buy
    band across a 20-hand run, while net_bb still accumulates P&L."""
    view = create_session(db)
    saw_nonzero_net = False
    for hand_i in range(20):
        seats = db.exec(
            select(SimSeat).where(SimSeat.session_id == view.session_id)
        ).all()
        # start-of-hand: every live seat has re-bought inside the band. The
        # hand is already dealt (blinds posted, bots advanced), but `stack_bb`
        # on the row is the pre-deal re-buy, untouched until settlement.
        for s in seats:
            assert sim_session._BUYIN_MIN_BB <= s.stack_bb <= sim_session._BUYIN_MAX_BB

        view = _play_current_hand(db, view)
        seats = db.exec(
            select(SimSeat).where(SimSeat.session_id == view.session_id)
        ).all()
        nets = [round(s.stack_bb - s.buyins_bb, 2) for s in seats]
        assert round(sum(nets), 2) == 0.0
        if hand_i >= 4 and any(n != 0.0 for n in nets):
            saw_nonzero_net = True
        view = deal_next_hand(db, view.session_id)
    assert saw_nonzero_net, "reset zeroed the ledger — net_bb must carry P&L"
