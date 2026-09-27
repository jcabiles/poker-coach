"""The live table and the 6-max measurement tool read bot settings for their
own table size.

`sim_session._packs(table_size)` is cached per size, and every reader — both
bot call sites (`_deal_and_advance` when a hand is dealt, `apply_hero_action`
after the hero acts) and the villain-range endpoint — goes through
`_seat_personas(seats, _table_size(session))`. The fixture folder's 6-max LAG
override opens only AA when the pot is unopened, so any LAG decision taken
from the 9-max pack at a 6-max table is visible as a non-AA open, and one taken
from the 6-max pack at a 9-max table is visible as a missing non-AA open.
`sixmax_baseline.run_baseline` must load the 6-max pack the same way.
Spec: docs/ai-dlc/specs/m1b-table-size-settings.md section 4, "Live session".
"""

from __future__ import annotations

import asyncio
import random

import pytest
from persona_override_fixture import (
    DEFAULT_LAG_OVERRIDE,
    PERSONAS_DIR,
    write_fixture_content,
)
from sqlmodel import Session, create_engine, select
from test_sim_session import _hero_decision

from app.db.migrate import run_migrations
from app.db.models import SimHand, SimSeat, SimSession
from app.domain import personas
from app.domain.action import Decision
from app.domain.content.models import PersonaNode
from app.domain.content.notation import hole_cards_to_class
from app.domain.personas import load_persona_packs
from app.domain.spot import ActionType, Position, Street
from app.domain.table.deck import deal_hand
from app.domain.table.engine import HandState, apply, start_hand
from app.services import sim_session
from app.services.sim_session import HERO_SEAT, create_session, deal_next_hand, villain_range
from tools import sixmax_baseline

# Unopened bot decisions to observe from EACH call site, and the hands to play
# before giving up. One observation proves a site ran; several are needed to
# catch a site reading the 9-max pack, whose LAG also folds most hands. At 30
# per site a wrong pack survives only if the base LAG folds 30 unopened hands in
# a row. Both counts fill within a few dozen hands: the LJ bot acts unopened
# before the hero whenever the hero is not LJ, and every seat after a folding
# hero acts unopened while the override LAGs fold around.
_PER_SITE = 30
_HAND_CAP = 80

_LAG_SEAT_IN_BASELINE = 2


@pytest.fixture
def db(tmp_path):
    url = f"sqlite:///{tmp_path / 'table_size_packs.db'}"
    run_migrations(url)
    engine = create_engine(url, connect_args={"check_same_thread": False})
    with Session(engine) as s:
        yield s


@pytest.fixture
def fixture_packs(tmp_path, monkeypatch):
    """Point the loader at a real folder holding the 6-max LAG override, with
    `_packs`'s per-size cache empty on entry and on exit."""
    folder = write_fixture_content(tmp_path)
    monkeypatch.setattr(personas, "PERSONA_DIR", folder)
    sim_session._packs.cache_clear()
    yield folder
    sim_session._packs.cache_clear()


@pytest.fixture
def seeded(monkeypatch):
    """Pin the service's entropy (bot draws and deal seeds) so a red run
    replays exactly; the play itself is still the real engine and service."""
    rng_seeds = iter(range(10_000))
    deal_seeds = iter(range(50_000, 60_000))
    monkeypatch.setattr(sim_session, "_fresh_rng", lambda: random.Random(next(rng_seeds)))
    monkeypatch.setattr(sim_session.secrets, "randbits", lambda _bits: next(deal_seeds))


def _unopened_nodes(pack) -> list[PersonaNode]:
    return [n for n in pack.preflop if n.facing == "unopened"]


def test_packs_is_cached_per_table_size(fixture_packs):
    nine_first = sim_session._packs(9)
    six = sim_session._packs(6)
    nine_again = sim_session._packs(9)

    override_nodes = [
        PersonaNode.model_validate(n) for n in DEFAULT_LAG_OVERRIDE["preflop"]["unopened"]
    ]
    assert _unopened_nodes(six["lag"]) == override_nodes
    base = load_persona_packs(PERSONAS_DIR)
    assert nine_first == base
    assert nine_again == base
    assert _unopened_nodes(nine_first["lag"]) != override_nodes
    assert nine_again is nine_first
    assert six is not nine_first


def _current_hand_row(db: Session, session_id: str) -> SimHand:
    session = db.get(SimSession, session_id)
    return db.exec(
        select(SimHand)
        .where(SimHand.session_id == session_id)
        .where(SimHand.hand_no == session.hand_no)
    ).one()


def _play_out(db: Session, view):
    """Hero folds (checks when fold is not legal) until the hand ends."""
    while not view.hand.hand_over:
        decision = _hero_decision(view, fold_if_possible=True)
        view = asyncio.run(sim_session.apply_hero_action(db, view.session_id, decision))
    return view


def _unopened_bot_decisions(state: HandState) -> list[tuple[int, str, ActionType, str]]:
    """Every non-hero preflop decision taken while the pot was unopened (every
    earlier voluntary preflop action was a fold), as (seat, call site, action,
    the seat's hand class). The call site is "deal" before seat 0's first
    preflop action and "after_hero" once it has acted."""
    seat_at = {s.position: s for s in state.seats}
    hero_position = state.seats[HERO_SEAT].position
    hero_acted = False
    opened = False
    found = []
    for h in state.action_history:
        if h.street is not Street.PREFLOP or h.action is ActionType.POST:
            continue
        if h.position is hero_position:
            hero_acted = True
        elif not opened:
            seat = seat_at[h.position]
            found.append(
                (
                    seat.seat,
                    "after_hero" if hero_acted else "deal",
                    h.action,
                    hole_cards_to_class(*seat.hole_cards),
                )
            )
        if h.action is not ActionType.FOLD:
            opened = True
    return found


def _all_lag_hands(db: Session, table_size: int):
    """Yield the terminal state of up to `_HAND_CAP` hands of a session whose
    every villain is the LAG, the hero folding (checking when fold is not
    legal) throughout."""
    view = create_session(db, table_size=table_size)
    seats = db.exec(select(SimSeat).where(SimSeat.session_id == view.session_id)).all()
    for row in seats:
        if row.persona_type is not None:
            row.persona_type = "lag"
            db.add(row)
    db.commit()
    # Hand 1 was dealt (and its pre-hero bots acted) before the rewrite.
    _play_out(db, view)
    for _ in range(_HAND_CAP):
        view = _play_out(db, deal_next_hand(db, view.session_id))
        yield HandState.model_validate_json(_current_hand_row(db, view.session_id).state_json)


def test_both_bot_call_sites_use_the_six_max_pack(db, fixture_packs, seeded):
    seen: dict[str, int] = {"deal": 0, "after_hero": 0}
    for state in _all_lag_hands(db, 6):
        for _seat, site, action, hand_class in _unopened_bot_decisions(state):
            seen[site] += 1
            assert action is ActionType.FOLD or (
                action is ActionType.RAISE and hand_class == "AA"
            ), f"{site}: LAG {action.value} with {hand_class} in an unopened pot"
        if min(seen.values()) >= _PER_SITE:
            return
    pytest.fail(f"unopened bot decisions seen per call site after {_HAND_CAP} hands: {seen}")


def test_both_bot_call_sites_use_the_nine_max_pack(db, fixture_packs, seeded):
    """The reverse direction: at 9-max the override must NOT apply, so the
    base LAG's non-AA opens must show up from each call site."""
    non_aa_opens: dict[str, int] = {"deal": 0, "after_hero": 0}
    for state in _all_lag_hands(db, 9):
        for _seat, site, action, hand_class in _unopened_bot_decisions(state):
            if action is ActionType.RAISE and hand_class != "AA":
                non_aa_opens[site] += 1
        if min(non_aa_opens.values()) >= 1:
            return
    pytest.fail(f"unopened non-AA LAG opens per call site after {_HAND_CAP} hands: {non_aa_opens}")


def test_sixmax_baseline_loads_the_six_max_pack(fixture_packs):
    assert sixmax_baseline.SEATS[_LAG_SEAT_IN_BASELINE] == "lag"
    decisions = [
        (action, hand_class)
        for hand in sixmax_baseline.run_baseline(60, 1)
        for seat, _site, action, hand_class in _unopened_bot_decisions(hand.state)
        if seat == _LAG_SEAT_IN_BASELINE
    ]
    assert decisions, "the LAG made no unopened preflop decision in 60 hands"
    for action, hand_class in decisions:
        assert action is ActionType.FOLD or (action is ActionType.RAISE and hand_class == "AA"), (
            f"baseline LAG {action.value} with {hand_class} in an unopened pot"
        )


def _store_lag_open_from_lj(db: Session, table_size: int) -> tuple[str, int]:
    """A session whose current hand has a LAG seat raising first-in from LJ
    (every seat before it folded). Returns (session id, the LAG's seat)."""
    view = create_session(db, table_size=table_size)
    button = 0
    state = start_hand(
        deal_hand(random.Random(7), table_size),
        button_seat=button,
        stacks_bb=[100.0] * table_size,
    )
    lj_seat = next(s.seat for s in state.seats if s.position is Position.LJ)
    assert lj_seat != HERO_SEAT
    while state.to_act_seat != lj_seat:
        state = apply(state, Decision(action=ActionType.FOLD))
    state = apply(state, Decision(action=ActionType.RAISE, size_bb=2.5))

    seat_row = db.exec(
        select(SimSeat)
        .where(SimSeat.session_id == view.session_id)
        .where(SimSeat.seat_index == lj_seat)
    ).one()
    seat_row.persona_type = "lag"
    hand = _current_hand_row(db, view.session_id)
    hand.button_seat = button
    hand.status = "in_progress"
    hand.state_json = state.model_dump_json()
    db.add(seat_row)
    db.add(hand)
    db.commit()
    return view.session_id, lj_seat


def test_villain_range_reads_the_table_sizes_pack(db, fixture_packs):
    session_id, seat = _store_lag_open_from_lj(db, 6)
    six = villain_range(db, session_id, seat)
    assert six.available
    assert set(six.weights) == {"AA"}

    session_id, seat = _store_lag_open_from_lj(db, 9)
    nine = villain_range(db, session_id, seat)
    assert nine.available
    assert set(nine.weights) > {"AA"}
