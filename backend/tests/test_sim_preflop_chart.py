"""Preflop-chart slice C1 — `sim_session.preflop_chart` + the endpoint.

Fixture compares (ticket accepts): the chart grid for a mappable spot equals
the Practice drill grid for the same Spot (drill.py:317's exact pattern on the
same _INDEX singleton); unavailable cases (not hero's turn / postflop /
unmappable / hand over) return available=false with no grid; the exploit
note's villain is the ACTUAL live opponent seat (mis-pairing = fabrication,
spec med-1); a missing authored pair omits the note but keeps the grid.
"""

from __future__ import annotations

import random

import pytest
from sqlmodel import Session, create_engine, select

from app.api.v1.drill import _INDEX
from app.db.migrate import run_migrations
from app.db.models import SimHand, SimSeat, SimSession
from app.domain.action import Decision
from app.domain.content.registry import lookup
from app.domain.grading import range_grid
from app.domain.scenarios import _OPEN_SIZE, _SEAT_ORDER, _find_entry, build_spot
from app.domain.spot import ActionType, NodeContext, Position
from app.domain.table.deck import deal_hand
from app.domain.table.engine import HandState, apply, start_hand
from app.services.sim_session import HERO_SEAT, SessionNotFound, preflop_chart

_BLINDS = {Position.SB, Position.BB}
_BUTTON_FOR_HERO = {
    Position.BTN: 0, Position.SB: 8, Position.BB: 7,
    Position.UTG: 6, Position.UTG1: 5, Position.UTG2: 4,
    Position.LJ: 3, Position.HJ: 2, Position.CO: 1,
}


def _state(hero_pos: Position, seed: int = 7) -> HandState:
    dealt = deal_hand(random.Random(seed))
    return start_hand(
        dealt, button_seat=_BUTTON_FOR_HERO[hero_pos], stacks_bb=[100.0] * 9
    )


def _play(state: HandState, moves: list[tuple[Position, Decision]]) -> HandState:
    for pos, dec in moves:
        seat = next(s.seat for s in state.seats if s.position is pos)
        assert state.to_act_seat == seat, f"expected {pos} to act"
        state = apply(state, dec)
    return state


def _fold(pos: Position) -> tuple[Position, Decision]:
    return (pos, Decision(action=ActionType.FOLD))


def _before(pos: Position) -> list[Position]:
    return _SEAT_ORDER[: _SEAT_ORDER.index(pos)]


def _between(a: Position, b: Position) -> list[Position]:
    return _SEAT_ORDER[_SEAT_ORDER.index(a) + 1 : _SEAT_ORDER.index(b)]


def _folded_to(hero_pos: Position, seed: int = 7) -> HandState:
    state = _state(hero_pos, seed)
    return _play(state, [_fold(p) for p in _before(hero_pos) if p not in _BLINDS])


def _facing_open(hero_pos: Position, opener: Position, size: float, seed: int = 7) -> HandState:
    state = _state(hero_pos, seed)
    moves = [_fold(p) for p in _before(opener) if p not in _BLINDS]
    moves.append((opener, Decision(action=ActionType.RAISE, size_bb=size)))
    moves += [_fold(p) for p in _between(opener, hero_pos)]
    return _play(state, moves)


@pytest.fixture
def db(tmp_path):
    url = f"sqlite:///{tmp_path / 'chart.db'}"
    run_migrations(url)
    engine = create_engine(url, connect_args={"check_same_thread": False})
    with Session(engine) as s:
        yield s


def _persist(
    db: Session,
    state: HandState,
    personas_by_position: dict[Position, str] | None = None,
) -> str:
    """SimSession + seats + an in-progress SimHand holding `state`. Non-hero
    personas default to 'tag'; `personas_by_position` pins specific LIVE
    positions to specific personas (villain-pairing tests)."""
    by_pos = personas_by_position or {}
    session = SimSession(id="sess-chart", button_seat=state.button_seat, hand_no=1)
    db.add(session)
    for i in range(9):
        pos = state.seats[i].position
        db.add(
            SimSeat(
                session_id=session.id, seat_index=i, is_hero=i == HERO_SEAT,
                persona_type=None if i == HERO_SEAT else by_pos.get(pos, "tag"),
                stack_bb=100.0, buyins_bb=100.0,
            )
        )
    db.add(
        SimHand(
            session_id=session.id, hand_no=1, button_seat=state.button_seat,
            rng_seed="1", status="in_progress", state_json=state.model_dump_json(),
        )
    )
    db.commit()
    return session.id


# ------------------------------------------------------------ grid parity


def test_chart_grid_equals_practice_drill_grid_rfi(db):
    state = _folded_to(Position.BTN)
    session_id = _persist(db, state)
    view = preflop_chart(db, session_id)
    assert view.available is True
    # Practice's grid for the SAME Spot: drill.py:317's exact pattern.
    entry = _find_entry(NodeContext.RFI, Position.BTN, None)
    spot = build_spot(
        entry, random.Random(0), eff_bb=100.0,
        hole_cards=state.seats[HERO_SEAT].hole_cards,
    )
    assert view.grid == range_grid(lookup(_INDEX, spot))
    assert view.node_label == "BTN open (RFI)"
    assert view.exploit_note is None  # RFI has no facing seat to key a persona


def test_chart_grid_equals_practice_drill_grid_vs_rfi(db):
    state = _facing_open(Position.BB, Position.BTN, _OPEN_SIZE[Position.BTN])
    session_id = _persist(db, state)
    view = preflop_chart(db, session_id)
    assert view.available is True
    entry = _find_entry(NodeContext.BLIND_DEFENSE, Position.BB, Position.BTN)
    spot = build_spot(
        entry, random.Random(0), eff_bb=100.0,
        hole_cards=state.seats[HERO_SEAT].hole_cards,
    )
    assert view.grid == range_grid(lookup(_INDEX, spot))
    assert view.node_label == "BB vs BTN open"


# ------------------------------------------------------------ exploit note


def test_exploit_note_villain_is_the_live_opponent_seat(db):
    # BB defends vs a BTN open; ONLY the live BTN seat is a nit (an authored
    # blind_defense/BB/BTN/nit pair exists). A mis-paired persona lookup would
    # grab 'tag' (no pair -> None) or fabricate another seat's persona.
    state = _facing_open(Position.BB, Position.BTN, _OPEN_SIZE[Position.BTN])
    session_id = _persist(db, state, personas_by_position={Position.BTN: "nit"})
    view = preflop_chart(db, session_id)
    assert view.available is True
    note = view.exploit_note
    assert note is not None
    # The note's villain == the persona of the seat ACTUALLY sitting at the
    # mapped Spot's facing position (BTN) in the live hand.
    btn_seat = next(s.seat for s in state.seats if s.position is Position.BTN)
    rows = {r.seat_index: r for r in db.exec(select(SimSeat)).all()}
    assert note.villain_label == rows[btn_seat].persona_type == "nit"
    # Rationale is the authored content line, verbatim — never generated.
    entry = _find_entry(NodeContext.BLIND_DEFENSE, Position.BB, Position.BTN)
    spot = build_spot(entry, random.Random(0), eff_bb=100.0)
    exploit = lookup(_INDEX, spot, villain_type="nit")
    assert exploit is not None
    assert note.rationale == exploit.rationale


def test_missing_exploit_pair_keeps_grid_and_omits_note(db):
    # Live BTN is a TAG: no authored blind_defense/BB/BTN/tag pair exists.
    state = _facing_open(Position.BB, Position.BTN, _OPEN_SIZE[Position.BTN])
    session_id = _persist(db, state, personas_by_position={Position.BTN: "tag"})
    view = preflop_chart(db, session_id)
    assert view.available is True
    assert view.grid  # grid still present
    assert view.exploit_note is None


# ------------------------------------------------------------ unavailable


def test_not_hero_turn_is_unavailable(db):
    state = _state(Position.BTN)  # UTG to act, hero is the BTN
    session_id = _persist(db, state)
    view = preflop_chart(db, session_id)
    assert view.available is False
    assert view.grid is None and view.exploit_note is None and view.node_label is None


def test_postflop_is_unavailable(db):
    # Hero BTN opens, BB calls, BB checks the flop: hero's turn, but postflop.
    state = _state(Position.BTN)
    moves = [_fold(p) for p in _before(Position.BTN) if p not in _BLINDS]
    moves += [
        (Position.BTN, Decision(action=ActionType.RAISE, size_bb=2.5)),
        _fold(Position.SB),
        (Position.BB, Decision(action=ActionType.CALL)),
        (Position.BB, Decision(action=ActionType.CHECK)),
    ]
    state = _play(state, moves)
    assert state.to_act_seat == HERO_SEAT and state.board
    session_id = _persist(db, state)
    assert preflop_chart(db, session_id).available is False


def test_unmappable_preflop_spot_is_unavailable(db):
    # Oversize open (4bb > canonical CO 2.5): hero's preflop turn, unmappable.
    state = _facing_open(Position.BTN, Position.CO, 4.0)
    session_id = _persist(db, state)
    assert preflop_chart(db, session_id).available is False


def test_hand_over_is_unavailable(db):
    # Everyone folds to the hero's big blind: the hand is over on arrival.
    state = _state(Position.BB)
    moves = [_fold(p) for p in _before(Position.SB) if p not in _BLINDS]
    moves.append(_fold(Position.SB))
    state = _play(state, moves)
    assert state.hand_over
    session_id = _persist(db, state)
    assert preflop_chart(db, session_id).available is False


def test_missing_session_raises_session_not_found(db):
    with pytest.raises(SessionNotFound):
        preflop_chart(db, "nope")


# ------------------------------------------------------------ HTTP shape


def test_endpoint_http_shape_and_404(db):
    from fastapi.testclient import TestClient

    from app.db.session import get_session
    from app.main import app

    def _override():
        yield db

    app.dependency_overrides[get_session] = _override
    try:
        client = TestClient(app)
        session_id = _persist(db, _folded_to(Position.BTN))
        resp = client.get(f"/api/v1/simulate/{session_id}/preflop-chart")
        assert resp.status_code == 200
        body = resp.json()
        assert body["available"] is True
        assert body["node_label"] == "BTN open (RFI)"
        assert body["grid"]["AA"]  # 13x13 grid keyed by hand class
        assert body["exploit_note"] is None
        # 404 stays SessionNotFound-only (missing session), never availability.
        assert client.get("/api/v1/simulate/nope/preflop-chart").status_code == 404
    finally:
        app.dependency_overrides.clear()
