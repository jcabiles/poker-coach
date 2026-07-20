"""ActionEvent.all_in flag — the shove-legibility signal for Simulate playback.

Spec: docs/ai-dlc/specs/simulate-allin-label.md. The playout (advance_to_hero)
must flag an event `all_in=True` exactly when that action left the seat with an
empty stack, so the UI can label the shove instead of a bare BB amount.
"""

from __future__ import annotations

import random

from app.domain.personas import load_persona_packs
from app.domain.spot import ActionType, PlayerStatus
from app.domain.table import deal_hand
from app.domain.table.engine import start_hand
from app.domain.table.play import advance_to_hero, assign_lineup

HERO_SEAT = 0


def _tiny_stack_playout(seed: int):
    """Deal a hand where the 8 bots sit on ~2bb — preflop forces all-ins."""
    rng = random.Random(seed)
    dealt = deal_hand(rng)
    packs = load_persona_packs()
    lineup = assign_lineup(rng)
    personas = {seat: packs[vt] for seat, vt in lineup.items()}
    # Hero (seat 0) deep so it's never forced; bots short so they jam/call all-in.
    stacks = [100.0] + [2.0] * 8
    state = start_hand(dealt, button_seat=0, stacks_bb=stacks)
    state, events = advance_to_hero(state, personas, HERO_SEAT, rng)
    return state, events


def test_allin_flag_appears_and_is_typed():
    """Across seeds, short bots produce >=1 all-in event; all flags are bools."""
    saw_all_in = False
    for seed in range(30):
        _, events = _tiny_stack_playout(seed)
        for e in events:
            assert isinstance(e.all_in, bool)
            if e.all_in:
                saw_all_in = True
    assert saw_all_in, "tiny-stack playout never produced an all-in event"


def test_fold_and_check_never_all_in():
    """A fold or check can never exhaust a stack, so it is never flagged."""
    for seed in range(30):
        _, events = _tiny_stack_playout(seed)
        for e in events:
            if e.action in (ActionType.FOLD, ActionType.CHECK):
                assert e.all_in is False


def test_all_in_event_seat_ends_stackless():
    """A seat flagged all-in is truly stack-exhausted: once all-in it never acts
    again, so its terminal state must be ALLIN with a zero stack."""
    for seed in range(30):
        state, events = _tiny_stack_playout(seed)
        all_in_seats = {e.seat for e in events if e.all_in}
        for seat in all_in_seats:
            final = state.seats[seat]
            assert final.status is PlayerStatus.ALLIN
            assert final.stack_bb == 0.0


def test_deep_normal_open_not_flagged():
    """A standard preflop open with a deep stack is not an all-in — the flag must
    not fire for ordinary sizing."""
    rng = random.Random(7)
    dealt = deal_hand(rng)
    packs = load_persona_packs()
    lineup = assign_lineup(rng)
    personas = {seat: packs[vt] for seat, vt in lineup.items()}
    state = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    _, events = advance_to_hero(state, personas, HERO_SEAT, rng)
    # Deep stacks: any all-in flagged here must coincide with a zeroed stack
    # (e.g. a maniac 100bb jam is a legitimate all-in) — never a phantom flag.
    for e in events:
        if e.all_in:
            assert state.seats[e.seat].stack_bb == 0.0
