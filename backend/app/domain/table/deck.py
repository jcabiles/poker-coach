"""Table dealing — seed-reproducible deck + dealer-button rotation (6 or 9 seats).

Pure domain: no web/DB imports, no shared RNG state. Callers own the
`random.Random` instance (see `docs/ai-dlc/specs/simulate-s1.md` — per-hand
`random.Random(secrets.randbits(256))`, never a module-level singleton).
"""

from __future__ import annotations

import random

from pydantic import BaseModel, field_validator

from app.domain.spot import RANKS, SUITS, Card, Position, validate_card

# Default table size for both functions below. The default is load-bearing:
# roughly 150 existing call sites pass no seat count, and no 9-max test may be
# edited. Its cost is that a missed call site fails silently rather than loudly.
_SEATS = 9

# Frozen clockwise order starting at the button (spec worked example).
_ROTATION = [
    Position.BTN,
    Position.SB,
    Position.BB,
    Position.UTG,
    Position.UTG1,
    Position.UTG2,
    Position.LJ,
    Position.HJ,
    Position.CO,
]

# 6-max is the same clockwise order with the three UTG seats removed: BTN, SB,
# BB, LJ, HJ, CO. DERIVED, never retyped — a typed second list is where a typo
# hides, and deriving is what keeps the 9-max worked example byte-identical.
_UNSEATED_AT_SIX = (Position.UTG, Position.UTG1, Position.UTG2)
_ROTATION_6MAX = [p for p in _ROTATION if p not in _UNSEATED_AT_SIX]

_ROTATIONS = {6: _ROTATION_6MAX, 9: _ROTATION}


class DealtHand(BaseModel):
    hole_cards: list[tuple[Card, Card]]  # one pair per seat, seat order
    board: list[Card]  # len 5

    @field_validator("hole_cards")
    @classmethod
    def _validate_hole_cards(cls, v):
        return [(validate_card(a), validate_card(b)) for a, b in v]

    @field_validator("board")
    @classmethod
    def _validate_board(cls, v):
        return [validate_card(c) for c in v]


def deal_hand(rng: random.Random, table_size: int = _SEATS) -> DealtHand:
    """Shuffle a fresh 52-card deck once and deal `table_size`x2 hole cards + a
    5-card board.

    Deck construction mirrors `equity.py:24`. Deal order: shuffle, pop the hole
    cards (2 per seat, in seat order), then pop 5 board cards. No reshuffling —
    so the board's deck offset depends on the seat count, and dealing a 6-max
    hand at nine would draw the board from the wrong place.
    """
    deck: list[Card] = [r + s for r in RANKS for s in SUITS]
    rng.shuffle(deck)
    hole_cards = [(deck.pop(0), deck.pop(0)) for _ in range(table_size)]
    board = [deck.pop(0) for _ in range(5)]
    return DealtHand(hole_cards=hole_cards, board=board)


def positions_for_button(button_seat: int, table_size: int = _SEATS) -> list[Position]:
    """Positions indexed by seat, given the button's seat index.

    Element `i` is seat `i`'s position. Clockwise = ascending seat index,
    wrapping mod `table_size`, starting from `BTN` at `button_seat`.
    """
    rotation = _ROTATIONS[table_size]
    return [rotation[(seat - button_seat) % table_size] for seat in range(table_size)]
