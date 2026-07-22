"""M3 — BB-check node vs limpers (RES-G Slice B).

Pass/fail coverage:
(a) hero-as-BB facing 1–3 limpers maps via `map_preflop` and grades iso vs
    check with frequency + EV (never boolean): checking a range-appropriate
    hand grades OPTIMAL, iso'ing junk grades a leak (MISTAKE/BLUNDER).
(b) a BB spot NEVER offers a FOLD action — asserted over organically mapped
    spots here (and over every built spot in
    test_vs_limpers_build_spot_coherence.py); the grader also never evaluates
    a synthetic FOLD for the free-check node.
(c) SB-complete-vs-BB stays unmapped (None) — the canonical BB shape requires
    the SB folded; non-BB shapes are covered byte-unchanged by the existing
    vs_limpers tests.

Deterministic; no DB, no web.
"""

from __future__ import annotations

import random

import pytest

from app.domain.action import Decision
from app.domain.evaluation import Correctness
from app.domain.grading import grade
from app.domain.scenarios import _SEAT_ORDER, build_spot
from app.domain.spot import ActionType, Position
from app.domain.table.deck import deal_hand
from app.domain.table.engine import HandState, apply, start_hand
from app.domain.table.grade_map import _find_limp_entry, map_decision_point

HERO_SEAT = 0
_BUTTON_FOR_BB_HERO = 7  # puts seat 0 (hero) at the BB (deck._ROTATION)
_NON_BLIND = [p for p in _SEAT_ORDER if p not in (Position.SB, Position.BB)]


def _limped_to_bb(limpers: list[Position], sb_completes: bool = False, seed: int = 7) -> HandState:
    """Unraised pot to the hero-BB's option: `limpers` call 1bb at their slots,
    every other non-blind seat folds, then the SB folds (or completes)."""
    state = start_hand(
        deal_hand(random.Random(seed)),
        button_seat=_BUTTON_FOR_BB_HERO,
        stacks_bb=[100.0] * 9,
    )
    moves: list[tuple[Position, Decision]] = [
        (p, Decision(action=ActionType.CALL if p in limpers else ActionType.FOLD))
        for p in _NON_BLIND
    ]
    moves.append(
        (Position.SB, Decision(action=ActionType.CALL if sb_completes else ActionType.FOLD))
    )
    for pos, dec in moves:
        seat = next(s.seat for s in state.seats if s.position is pos)
        assert state.to_act_seat == seat, f"expected {pos} to act"
        state = apply(state, dec)
    assert state.to_act_seat == HERO_SEAT  # the BB's option
    return state


# ------------------------------------------------------------- mapping (a/b)


@pytest.mark.parametrize(
    "limpers",
    [
        [Position.UTG],
        [Position.UTG, Position.LJ],
        [Position.UTG, Position.LJ, Position.CO],
    ],
)
def test_bb_facing_limpers_maps_to_builder_spot_verbatim(limpers):
    state = _limped_to_bb(limpers)
    spot = map_decision_point(state, HERO_SEAT)
    assert spot is not None, f"BB x{len(limpers)} did not map"
    entry = _find_limp_entry(Position.BB, len(limpers))
    assert entry is not None
    expected = build_spot(
        entry, random.Random(0), eff_bb=100.0,
        hole_cards=state.seats[HERO_SEAT].hole_cards,
    )
    assert spot == expected
    assert spot.limper_count == len(limpers)
    # (b) a FOLD action is never offered to the BB — checking is free.
    kinds = [la.action for la in spot.legal_actions]
    assert ActionType.FOLD not in kinds
    assert ActionType.CHECK in kinds


def test_sb_complete_vs_bb_stays_unmapped():
    # (c) an SB complete is a blind CALL — non-canonical, byte-unchanged None.
    state = _limped_to_bb([Position.UTG], sb_completes=True)
    assert map_decision_point(state, HERO_SEAT) is None
    # Even with zero non-blind limpers (pure SB-complete-vs-BB).
    state = _limped_to_bb([], sb_completes=True)
    assert map_decision_point(state, HERO_SEAT) is None


def test_bb_off_count_stays_unmapped():
    # 4 limpers: no BB x4 entry — never fabricate.
    state = _limped_to_bb([Position.UTG, Position.UTG1, Position.LJ, Position.CO])
    assert map_decision_point(state, HERO_SEAT) is None


# ------------------------------------------------------------- grading (a/b)


def _bb_spot(count: int, hole_cards: tuple[str, str]):
    entry = _find_limp_entry(Position.BB, count)
    assert entry is not None
    return entry, build_spot(entry, random.Random(0), eff_bb=100.0, hole_cards=hole_cards)


def _grade_bb(count: int, hole_cards: tuple[str, str], decision: Decision):
    entry, spot = _bb_spot(count, hole_cards)
    return grade(spot, entry, decision)


def test_bb_check_junk_is_optimal_freq_ev():
    # 72o is in nobody's band — the free check IS the play (never fold the BB).
    res = _grade_bb(1, ("7h", "2d"), Decision(action=ActionType.CHECK))
    assert res.correctness is Correctness.OPTIMAL
    # freq + EV, never boolean.
    assert res.chosen_eval is not None and res.chosen_eval.frequency == 1.0
    assert all(isinstance(e.ev_bb, float) for e in res.per_action)
    # (b) the grader never evaluates a synthetic FOLD for the free-check node.
    assert all(e.action is not ActionType.FOLD for e in res.per_action)
    assert res.best_action.action is ActionType.CHECK


def test_bb_check_range_appropriate_hand_is_optimal():
    # 54s sits in the authored BB x1 check band (speculative, wants a free flop).
    res = _grade_bb(1, ("5h", "4h"), Decision(action=ActionType.CHECK))
    assert res.correctness is Correctness.OPTIMAL
    # 88 checks its option vs three limpers (BB x3 check band).
    res = _grade_bb(3, ("8h", "8d"), Decision(action=ActionType.CHECK))
    assert res.correctness is Correctness.OPTIMAL


def test_bb_iso_value_hand_is_optimal():
    for count, size in ((1, 5.0), (2, 6.0), (3, 7.0)):
        res = _grade_bb(count, ("Ah", "Ad"), Decision(action=ActionType.RAISE, size_bb=size))
        assert res.correctness is Correctness.OPTIMAL, f"AA iso x{count}: {res.correctness}"
        assert res.best_action.action is ActionType.RAISE


def test_bb_iso_junk_is_a_leak():
    # (a) iso'ing junk grades a leak: EV loss beyond the acceptable band.
    res = _grade_bb(1, ("7h", "2d"), Decision(action=ActionType.RAISE, size_bb=5.0))
    assert res.correctness in (Correctness.MISTAKE, Correctness.BLUNDER)
    assert res.ev_loss_bb is not None and res.ev_loss_bb > 0.5
    assert "over_aggressive" in res.rationale_tags


def test_bb_check_premium_is_not_optimal():
    # Checking AA misses value (top action is the iso) but costs only the
    # missed raise — graded down, never a fold recommendation.
    res = _grade_bb(1, ("Ah", "Ad"), Decision(action=ActionType.CHECK))
    assert res.correctness is not Correctness.OPTIMAL
    assert res.best_action.action is ActionType.RAISE
    assert "under_aggressive" in res.rationale_tags
