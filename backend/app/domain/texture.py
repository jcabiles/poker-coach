"""Board-texture classifier (Phase 2a).

Pure, rule-based flop classification used by the c-bet grader and the
texture-classification quiz, and to derive a stable `texture_class` label for
the postflop spot signature (so same-texture boards map to one SRS bucket).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Literal

RANKS = "23456789TJQKA"
_RIDX = {r: i for i, r in enumerate(RANKS)}

# W5-c2: street-aware classification. `classify()` defaults to "flop" (the
# ORIGINAL, byte-identical board[:3] behavior every existing caller relies
# on — srs.spot_signature() and the grader included). "turn"/"river" are
# opt-in re-classification for a NEW consumer to use deliberately; no
# existing call site passes `street=`, so the default path is untouched.
_STREET_LEN: dict[str, int] = {"flop": 3, "turn": 4, "river": 5}


@dataclass(frozen=True)
class Texture:
    wetness: str  # dry | medium | wet
    pairing: str  # unpaired | paired | trips
    suitedness: str  # rainbow | two-tone | monotone
    connectedness: str  # disconnected | semi-connected | connected
    high_card: str  # rank char of the top card, e.g. "A"
    texture_class: str  # compact, board-independent label for the signature

    @property
    def high_board(self) -> bool:
        """True for broadway-topped boards (T or higher)."""
        return _RIDX[self.high_card] >= _RIDX["T"]


def classify(board: list[str], *, street: Literal["flop", "turn", "river"] = "flop") -> Texture:
    """Classifies the board texture for `street` (default "flop" — the ORIGINAL,
    byte-identical behavior: exactly the FIRST 3 cards of `board`). Every existing
    caller relies on this default; do not pass `street=` from a flop-only call site
    (`srs.spot_signature()`, the grader) — see W5-c2.

    `street="turn"`/`street="river"` are OPT-IN re-classification against the first
    4/5 board cards respectively, for a consumer that deliberately wants the texture
    to react to a card that pairs the board or completes a flush after the flop.
    Raises if `board` is shorter than the street requires."""
    n = _STREET_LEN[street]
    if len(board) < n:
        raise ValueError(
            f"texture.classify needs >={n} board cards for street={street!r}, got {len(board)}"
        )
    cards = board[:n]
    rs = [_RIDX[c[0]] for c in cards]
    ss = [c[1] for c in cards]

    distinct = sorted(set(rs), reverse=True)
    rank_counts = Counter(rs)
    max_mult = max(rank_counts.values())
    n_pairs = sum(1 for c in rank_counts.values() if c == 2)
    if max_mult >= 4:
        pairing = "quads"
    elif max_mult == 3:
        pairing = "full-house" if n_pairs >= 1 else "trips"
    elif max_mult == 2:
        pairing = "two-pair" if n_pairs >= 2 else "paired"
    else:
        pairing = "unpaired"

    suit_counts = Counter(ss)
    max_suit = max(suit_counts.values())
    if max_suit >= 3:
        suitedness = "monotone"
    elif max_suit == 2:
        suitedness = "two-tone"
    else:
        suitedness = "rainbow"

    span = distinct[0] - distinct[-1] if len(distinct) > 1 else 0
    if len(distinct) >= 3 and span <= 4:
        connectedness = "connected"
    elif len(distinct) >= 2 and span <= 2:
        connectedness = "connected"
    elif len(distinct) >= 3 and span <= 6:
        connectedness = "semi-connected"
    else:
        connectedness = "disconnected"

    high_card = RANKS[distinct[0]]

    score = 0
    if suitedness == "monotone":
        score += 2
    elif suitedness == "two-tone":
        score += 1
    if connectedness == "connected":
        score += 2
    elif connectedness == "semi-connected":
        score += 1
    if pairing == "paired":  # paired boards offer fewer draws — play drier
        score -= 1
    if score >= 2:
        wetness = "wet"
    elif score <= 0:
        wetness = "dry"
    else:
        wetness = "medium"

    texture_class = f"{wetness}|{suitedness}|{connectedness}|{pairing}"
    return Texture(
        wetness=wetness,
        pairing=pairing,
        suitedness=suitedness,
        connectedness=connectedness,
        high_card=high_card,
        texture_class=texture_class,
    )


def turn_card_class(board: list[str]) -> str:
    """Classify the turn card (board[3]) against the flop (board[:3]) into exactly
    one of "pairing" | "flush" | "straight" | "over" | "blank" (S6).

    Precedence in that order: a board-pairing card beats a flush-completing card
    beats a straight-completing card beats an overcard to the flop beats a blank.
    Raises if fewer than 4 board cards. `classify()` above stays flop-only.
    """
    if len(board) < 4:
        raise ValueError(f"texture.turn_card_class needs >=4 board cards, got {len(board)}")
    flop, turn = board[:3], board[3]
    turn_rank, turn_suit = _RIDX[turn[0]], turn[1]
    flop_ranks = [_RIDX[c[0]] for c in flop]

    # 1. pairing — the turn matches a flop rank (trips/boats now possible)
    if turn_rank in flop_ranks:
        return "pairing"

    # 2. flush-completing — the turn makes 3+ of one suit on the board
    if sum(1 for c in flop if c[1] == turn_suit) >= 2:
        return "flush"

    # 3. straight-completing — the turn plus two flop cards fit a 5-rank window,
    # so a two-card holding can now complete a straight through the turn card.
    # Aces count both high and low (wheel).
    def _straighty(ranks: list[int], t: int) -> bool:
        for i, a in enumerate(ranks):
            for b in ranks[i + 1 :]:
                if a != b and max(a, b, t) - min(a, b, t) <= 4:
                    return True
        return False

    def _low(r: int) -> int:  # ace-low remap for wheel straights
        return -1 if r == _RIDX["A"] else r

    if _straighty(flop_ranks, turn_rank) or _straighty(
        [_low(r) for r in flop_ranks], _low(turn_rank)
    ):
        return "straight"

    # 4. overcard to the flop
    if turn_rank > max(flop_ranks):
        return "over"

    return "blank"


def river_card_class(board: list[str]) -> str:
    """Classify the river card (board[4]) against the first four cards (board[:4])
    into exactly one of "pairing" | "flush" | "straight" | "over" | "blank" (S7).

    Same precedence as `turn_card_class`: pairing beats flush-completing beats
    straight-completing beats overcard beats blank. Raises if fewer than 5 board
    cards. `classify()` stays flop-only and `turn_card_class()` is untouched.
    """
    if len(board) < 5:
        raise ValueError(f"texture.river_card_class needs >=5 board cards, got {len(board)}")
    prior, river = board[:4], board[4]
    river_rank, river_suit = _RIDX[river[0]], river[1]
    prior_ranks = [_RIDX[c[0]] for c in prior]

    # 1. pairing — the river matches a rank already on board
    if river_rank in prior_ranks:
        return "pairing"

    # 2. flush-completing — the river makes 3+ of one suit on the board
    if sum(1 for c in prior if c[1] == river_suit) >= 2:
        return "flush"

    # 3. straight-completing — the river plus two prior board cards fit a 5-rank
    # window, so a two-card holding can now complete a straight through it.
    # Aces count both high and low (wheel).
    def _straighty(ranks: list[int], t: int) -> bool:
        for i, a in enumerate(ranks):
            for b in ranks[i + 1 :]:
                if a != b and max(a, b, t) - min(a, b, t) <= 4:
                    return True
        return False

    def _low(r: int) -> int:  # ace-low remap for wheel straights
        return -1 if r == _RIDX["A"] else r

    if _straighty(prior_ranks, river_rank) or _straighty(
        [_low(r) for r in prior_ranks], _low(river_rank)
    ):
        return "straight"

    # 4. overcard to the board so far
    if river_rank > max(prior_ranks):
        return "over"

    return "blank"
