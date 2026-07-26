"""Measure WHY the postflop mapper says "no baseline yet" on a stored session.

    cd backend && python -m tools.reject_counts --session <session_id>

Prints the street x reason matrix `T-cover` is scoped off. Read-only: opens no
transaction, writes nothing, changes no schema.

Two things make the number trustworthy, both asserted before a single reason is
counted (owner decision B2):

1. **Deterministic replay.** `SimDecision` stores no state snapshot and
   `SimHand.state_json` is the TERMINAL state, so the `HandState` immediately
   before each hero decision does not exist anywhere. It is reconstructed by
   replaying that hand's `action_history` from `start_hand`, with each seat's
   pre-hand stack recovered as `stack_bb + invested_total_bb` (the same
   identity `sim_session._public_history` relies on).
2. **Coverage parity.** Every replayed hero decision must reproduce the
   PERSISTED `coverage` verdict (mapped vs unmappable) and street. That proves
   the replay is the same game the app played — and it doubles as the B1
   parity check on the gate-diagnostic refactor, since `map_decision_point` has
   to answer exactly what it answered at play time across the whole corpus.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter

from sqlmodel import Session, select

from app.db.models import SimDecision, SimHand
from app.db.session import engine
from app.domain.action import Decision
from app.domain.spot import ActionType, Street
from app.domain.table.deck import DealtHand
from app.domain.table.engine import HandState, apply, start_hand
from app.domain.table.grade_map import map_decision_point
from app.domain.table.grade_map_reject import (
    REASON_ORDER,
    RejectReason,
    classify_postflop_rejection,
)
from app.services.sim_session import HERO_SEAT

_POSTFLOP = (Street.FLOP, Street.TURN, Street.RIVER)


class ParityError(RuntimeError):
    """The replay did not reproduce what the app persisted — stop, do not
    report a reason matrix measured on a mis-replayed game."""


def _initial_state(terminal: HandState) -> HandState:
    """Rewind a hand to its pre-blind opening state."""
    stacks = [
        round(s.stack_bb + s.invested_total_bb, 2)
        for s in sorted(terminal.seats, key=lambda s: s.seat)
    ]
    dealt = DealtHand(
        hole_cards=[s.hole_cards for s in sorted(terminal.seats, key=lambda s: s.seat)],
        board=terminal.full_board,
    )
    return start_hand(dealt, terminal.button_seat, stacks)


def _replay(terminal: HandState):
    """Yield (ordinal, pre-decision HandState) for every HERO decision.

    `ordinal` matches `SimDecision.ordinal` (0-based hero-decision order within
    the hand, all streets).
    """
    state = _initial_state(terminal)
    pos2seat = {s.position: s.seat for s in state.seats}
    ordinal = 0
    for h in terminal.action_history:
        if h.action is ActionType.POST:
            continue
        seat = pos2seat[h.position]
        if state.hand_over or state.to_act_seat != seat:
            raise ParityError(
                f"replay desync: history says {h.position.value} acts, "
                f"engine says seat {state.to_act_seat}"
            )
        if seat == HERO_SEAT:
            yield ordinal, state
            ordinal += 1
        # History stores the raise/bet INCREMENT; `apply` wants the raise-TO.
        size = None
        if h.action in (ActionType.BET, ActionType.RAISE):
            size = round(state.seats[seat].invested_street_bb + h.amount_bb, 2)
        state = apply(state, Decision(action=h.action, size_bb=size))


def measure(session_id: str) -> tuple[Counter, dict[str, Counter], int, int]:
    """Return (per-street decision counts, street -> reason Counter, mapped,
    unmapped) for `session_id`, after asserting replay/coverage parity."""
    with Session(engine) as db:
        hands = db.exec(
            select(SimHand).where(SimHand.session_id == session_id).order_by(SimHand.id)
        ).all()
        rows = db.exec(
            select(SimDecision).where(SimDecision.session_id == session_id)
        ).all()
    if not hands:
        raise SystemExit(f"no hands for session {session_id!r}")
    persisted = {(r.sim_hand_id, r.ordinal): r for r in rows}

    per_street: Counter = Counter()
    matrix: dict[str, Counter] = {s.value: Counter() for s in _POSTFLOP}
    mapped = unmapped = 0
    for hand in hands:
        if hand.state_json is None:
            continue
        terminal = HandState.model_validate_json(hand.state_json)
        for ordinal, state in _replay(terminal):
            row = persisted.get((hand.id, ordinal))
            if row is None:
                raise ParityError(
                    f"hand {hand.id} ordinal {ordinal}: replayed a hero decision "
                    "with no persisted sim_decision row"
                )
            if row.street != state.street.value:
                raise ParityError(
                    f"hand {hand.id} ordinal {ordinal}: persisted street "
                    f"{row.street!r} != replayed {state.street.value!r}"
                )
            spot = map_decision_point(state, HERO_SEAT)
            was_mapped = row.coverage != "unmappable"
            if (spot is not None) != was_mapped:
                raise ParityError(
                    f"hand {hand.id} ordinal {ordinal}: persisted coverage "
                    f"{row.coverage!r} but map_decision_point now returns "
                    f"{'a Spot' if spot is not None else 'None'}"
                )
            if state.street is Street.PREFLOP:
                continue
            per_street[state.street.value] += 1
            if spot is not None:
                mapped += 1
                continue
            unmapped += 1
            matrix[state.street.value][
                classify_postflop_rejection(state, HERO_SEAT)
            ] += 1
    return per_street, matrix, mapped, unmapped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, help="sim_session.id")
    args = parser.parse_args(argv)

    per_street, matrix, mapped, unmapped = measure(args.session)
    total = mapped + unmapped
    streets = [s.value for s in _POSTFLOP]

    print(f"session: {args.session}")
    print("replay + coverage parity: OK (every hero decision reproduces its "
          "persisted street and coverage)")
    print(f"postflop decision points: {total}")
    print(f"mapped: {mapped}")
    print(
        f"unmapped: {unmapped} ("
        + " · ".join(f"{s} {per_street[s] - 0}" for s in streets)
        + " decision points; unmapped "
        + " · ".join(f"{s} {sum(matrix[s].values())}" for s in streets)
        + ")"
    )
    print()

    width = max(len(r.value) for r in REASON_ORDER)
    header = f"{'reason'.ljust(width)}  " + "".join(f"{s:>7}" for s in streets) + "    total"
    print(header)
    print("-" * len(header))
    for reason in REASON_ORDER:
        cells = [matrix[s][reason] for s in streets]
        if not sum(cells):
            continue
        print(
            reason.value.ljust(width)
            + "  "
            + "".join(f"{c:>7}" for c in cells)
            + f"{sum(cells):>9}"
        )
    print("-" * len(header))
    print(
        "TOTAL".ljust(width)
        + "  "
        + "".join(f"{sum(matrix[s].values()):>7}" for s in streets)
        + f"{unmapped:>9}"
    )

    counted = sum(sum(c.values()) for c in matrix.values())
    unclassified = sum(c[RejectReason.UNCLASSIFIED] for c in matrix.values())
    print()
    print(f"sum(reason counts) == unmapped: {counted == unmapped} ({counted})")
    print(f"UNCLASSIFIED: {unclassified}")
    return 0 if counted == unmapped and unclassified == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
