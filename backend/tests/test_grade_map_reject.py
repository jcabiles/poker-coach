"""T-REJECT — the postflop mapper's rejection-reason taxonomy.

One test per reason, each built from a REAL engine line (never a hand-rolled
HandState), so the assertion is about the live gates rather than a fixture.

Two structural guards live here too:
  * every PUBLIC `map_*` still answers `Spot | None` — the B1 refactor put the
    typed diagnostic on internal twins ONLY, and six existing mapper test files
    must keep passing untouched;
  * the taxonomy is total — `classify_postflop_rejection` always returns a
    `RejectReason` member.

The 181-hand corpus measurement (66 decision points / 4 mapped / 62 unmapped /
`UNCLASSIFIED == 0`) is NOT asserted here — it needs the local sim DB. Run
`python -m tools.reject_counts --session <id>` for that.
"""

from __future__ import annotations

import inspect
import random

import pytest

from app.domain.action import Decision
from app.domain.spot import ActionType, PlayerStatus, Position, Spot, Street
from app.domain.table import grade_map_postflop as gp
from app.domain.table.deck import deal_hand
from app.domain.table.engine import HandState, apply, legal_actions, start_hand
from app.domain.table.grade_map import map_decision_point
from app.domain.table.grade_map_reject import (
    REASON_ORDER,
    RejectReason,
    classify_postflop_rejection,
)

HERO_SEAT = 0
_BUTTON_FOR_HERO = {
    Position.BTN: 0, Position.SB: 8, Position.BB: 7,
    Position.UTG: 6, Position.UTG1: 5, Position.UTG2: 4,
    Position.LJ: 3, Position.HJ: 2, Position.CO: 1,
}
_ORDER = [
    Position.UTG, Position.UTG1, Position.UTG2, Position.LJ, Position.HJ,
    Position.CO, Position.BTN, Position.SB, Position.BB,
]


def _state(hero_pos: Position, stacks: dict[Position, float] | None = None) -> HandState:
    """Open a hand with hero (seat 0) sitting at `hero_pos`. `stacks` overrides
    the default 100bb by POSITION."""
    button = _BUTTON_FOR_HERO[hero_pos]
    dealt = deal_hand(random.Random(7))
    base = [100.0] * 9
    state = start_hand(dealt, button_seat=button, stacks_bb=base)
    if stacks:
        seat_of = {s.position: s.seat for s in state.seats}
        for pos, amount in stacks.items():
            base[seat_of[pos]] = amount
        state = start_hand(dealt, button_seat=button, stacks_bb=base)
    return state


def _play(state: HandState, moves) -> HandState:
    for pos, dec in moves:
        seat = next(s.seat for s in state.seats if s.position is pos)
        assert state.to_act_seat == seat, (
            f"expected {pos.value} to act, engine says seat {state.to_act_seat}"
        )
        state = apply(state, dec)
    return state


def _fold(pos):
    return (pos, Decision(action=ActionType.FOLD))


def _call(pos):
    return (pos, Decision(action=ActionType.CALL))


def _check(pos):
    return (pos, Decision(action=ActionType.CHECK))


def _bet(pos, size):
    return (pos, Decision(action=ActionType.BET, size_bb=size))


def _raise(pos, size):
    return (pos, Decision(action=ActionType.RAISE, size_bb=size))


def _preflop(state: HandState, moves: dict[Position, Decision]) -> HandState:
    """Run one preflop orbit in seat order: each position takes its `moves`
    entry, or folds. Nobody acts twice (no limp-then-call lines here)."""
    return _play(state, [(p, moves.get(p, Decision(action=ActionType.FOLD))) for p in _ORDER])


def _assert_unmapped(state: HandState) -> RejectReason:
    """Every case here must be a live, unmapped HERO decision point — the
    classifier's documented precondition."""
    assert not state.hand_over and state.to_act_seat == HERO_SEAT
    assert state.street is not Street.PREFLOP
    assert map_decision_point(state, HERO_SEAT) is None
    return classify_postflop_rejection(state, HERO_SEAT)


# --- one line per reason ----------------------------------------------------


def test_no_mapper_for_street_shape_limped_turn():
    """The two limped mappers are FLOP-only, so a limped TURN is a recognized
    shape with nowhere to go — not a "shape we don't gate"."""
    state = _state(Position.BB)
    state = _preflop(state, {
        Position.SB: Decision(action=ActionType.CALL),
        Position.BB: Decision(action=ActionType.CHECK),
    })
    state = _play(state, [
        _check(Position.SB), _check(Position.BB),  # flop checks through
        _check(Position.SB),                       # turn: SB checks to hero
    ])
    assert gp._limped_flop_hu_preflop(state).value is not None
    assert _assert_unmapped(state) is RejectReason.NO_MAPPER_FOR_STREET_SHAPE


def test_preflop_shape_ungated_three_bet_pot():
    state = _state(Position.UTG)
    state = _preflop(state, {
        Position.UTG: Decision(action=ActionType.RAISE, size_bb=3.0),
        Position.BTN: Decision(action=ActionType.RAISE, size_bb=9.0),
    })
    state = _play(state, [_call(Position.UTG)])
    assert _assert_unmapped(state) is RejectReason.PREFLOP_SHAPE_UNGATED


def test_all_in_in_line_short_cold_caller():
    """A 3-way SRP whose cold-caller is all-in: the shape is gated, the all-in
    is what kills it — so ALL_IN_IN_LINE, not PREFLOP_SHAPE_UNGATED."""
    state = _state(Position.BB, stacks={Position.CO: 3.0})
    state = _preflop(state, {
        Position.UTG: Decision(action=ActionType.RAISE, size_bb=3.0),
        Position.CO: Decision(action=ActionType.CALL),
        Position.BB: Decision(action=ActionType.CALL),
    })
    assert next(s for s in state.seats if s.position is Position.CO).status is (
        PlayerStatus.ALLIN
    )
    assert _assert_unmapped(state) is RejectReason.ALL_IN_IN_LINE


def test_open_size_off_band_oversized_open():
    """`_OVERSIZE_OPEN_CAP` is 4.5, so 5.0 is the first open outside the band
    (every persona open — station 3.5 / fish 4.0 / maniac 4.5 — is INSIDE it;
    the postflop gates' old "still return None" comments were stale). The rest
    of the line is canonical, so the band is the binding gate."""
    state = _state(Position.UTG)
    state = _preflop(state, {
        Position.UTG: Decision(action=ActionType.RAISE, size_bb=5.0),
        Position.BB: Decision(action=ActionType.CALL),
    })
    state = _play(state, [_check(Position.BB)])
    assert gp._hu_srp_preflop(state).reason is RejectReason.OPEN_SIZE_OFF_BAND
    assert _assert_unmapped(state) is RejectReason.OPEN_SIZE_OFF_BAND


def test_hero_role_ungated_opener_in_the_no_bb_three_way():
    """The no-BB 3-way family gates ONLY the later cold-caller. Hero opened it,
    so the shape is gated on this street and hero simply has no seat in it."""
    state = _state(Position.UTG1)
    state = _preflop(state, {
        Position.UTG1: Decision(action=ActionType.RAISE, size_bb=3.0),
        Position.CO: Decision(action=ActionType.CALL),
        Position.BTN: Decision(action=ActionType.CALL),
    })
    assert gp._mw_nobb_srp_preflop(state).value is not None
    assert _assert_unmapped(state) is RejectReason.HERO_ROLE_UNGATED


def test_street_action_shape_ungated_donk_lead():
    """The canonical HU line wants check(BB) -> hero. The BB leading into the
    preflop raiser is the donk the taxonomy names."""
    state = _state(Position.UTG)
    state = _preflop(state, {
        Position.UTG: Decision(action=ActionType.RAISE, size_bb=3.0),
        Position.BB: Decision(action=ActionType.CALL),
    })
    state = _play(state, [_bet(Position.BB, 2.0)])
    assert gp._hu_srp_preflop(state).value is not None
    assert _assert_unmapped(state) is RejectReason.STREET_ACTION_SHAPE_UNGATED


def test_bet_fraction_off_grid_facing_an_unrecognized_cbet():
    """Flop pot 6.5; 2.6bb is 0.4 pot — nowhere near a RECOGNIZED_BET_FRACS
    member, and further than `_CANON_BET_TOL` from the two neighbours."""
    state = _state(Position.BB)
    state = _preflop(state, {
        Position.UTG: Decision(action=ActionType.RAISE, size_bb=3.0),
        Position.BB: Decision(action=ActionType.CALL),
    })
    state = _play(state, [_check(Position.BB), _bet(Position.UTG, 2.6)])
    assert not gp._is_canonical_bet(2.6, 6.5, Street.FLOP)
    assert _assert_unmapped(state) is RejectReason.BET_FRACTION_OFF_GRID


def test_stack_too_shallow_cannot_offer_the_big_bet_bucket():
    """Hero opens 3.0 off 7.0bb, leaving 4.0 behind; the flop's big bucket is
    0.75 * 6.5 = 4.9. Every shape gate passes — only the stack fails."""
    state = _state(Position.UTG, stacks={Position.UTG: 7.0})
    state = _preflop(state, {
        Position.UTG: Decision(action=ActionType.RAISE, size_bb=3.0),
        Position.BB: Decision(action=ActionType.CALL),
    })
    state = _play(state, [_check(Position.BB)])
    assert gp._hu_srp_preflop(state).value is not None
    assert state.seats[HERO_SEAT].stack_bb == pytest.approx(4.0)
    assert _assert_unmapped(state) is RejectReason.STACK_TOO_SHALLOW


# --- structural guards ------------------------------------------------------


_PUBLIC_MAPPERS = [
    getattr(gp, name)
    for name in dir(gp)
    if name.startswith("map_")
    and callable(getattr(gp, name))
    and getattr(gp, name).__module__ == gp.__name__
]


def test_public_mapper_signatures_are_unchanged():
    """B1's primary tripwire: the diagnostic is INTERNAL. Every public mapper
    still takes (state, hero_seat) and answers `Spot | None`."""
    assert len(_PUBLIC_MAPPERS) == 19
    for fn in _PUBLIC_MAPPERS:
        params = list(inspect.signature(fn).parameters)
        assert params == ["state", "hero_seat"], f"{fn.__name__} signature moved"
        assert inspect.signature(fn).return_annotation == "Spot | None", (
            f"{fn.__name__} return type moved"
        )


def test_public_mappers_return_spot_or_none_never_a_diagnostic():
    state = _state(Position.UTG)
    state = _preflop(state, {
        Position.UTG: Decision(action=ActionType.RAISE, size_bb=3.0),
        Position.BB: Decision(action=ActionType.CALL),
    })
    state = _play(state, [_check(Position.BB)])
    built = 0
    for fn in _PUBLIC_MAPPERS:
        got = fn(state, HERO_SEAT)
        assert got is None or isinstance(got, Spot), fn.__name__
        built += got is not None
    assert built == 1, "exactly the flop c-bet mapper should claim this line"


def test_taxonomy_is_total_and_ordered():
    assert REASON_ORDER == tuple(RejectReason)
    assert REASON_ORDER[0] is RejectReason.NO_MAPPER_FOR_STREET_SHAPE
    assert REASON_ORDER[-1] is RejectReason.UNCLASSIFIED
    assert len(set(REASON_ORDER)) == len(REASON_ORDER) == 9


def test_classifier_always_names_a_reason():
    """Sweep a wide slice of random bot-free lines: whatever the shape, the
    classifier answers with a taxonomy member (never raises, never None)."""
    seen: set[RejectReason] = set()
    for seed in range(40):
        rng = random.Random(seed)
        state = start_hand(deal_hand(rng), button_seat=seed % 9, stacks_bb=[100.0] * 9)
        while not state.hand_over and state.street is Street.PREFLOP:
            seat = state.to_act_seat
            legal = {la.action for la in legal_actions(state)}
            pick = ActionType.CALL if ActionType.CALL in legal else ActionType.CHECK
            if rng.random() < 0.4 and ActionType.FOLD in legal and seat != HERO_SEAT:
                pick = ActionType.FOLD
            state = apply(state, Decision(action=pick))
        while not state.hand_over:
            if state.to_act_seat == HERO_SEAT:
                if map_decision_point(state, HERO_SEAT) is None:
                    reason = classify_postflop_rejection(state, HERO_SEAT)
                    assert isinstance(reason, RejectReason)
                    seen.add(reason)
                break
            state = apply(state, Decision(action=ActionType.CHECK))
    assert seen, "the sweep produced no unmapped postflop hero decision"
