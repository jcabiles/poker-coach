"""A straight or better that the five-card board makes alone is not the bot's
monster: when the hole cards add nothing, `_made_bucket` classes the hand
MIDDLE_PAIR (a bluff-catcher). Any hole card that improves the best five, and
any board of fewer than five cards, keeps MONSTER (the board-made-hand rule).

Found by the blind 200-hand review (2026-09-25): AQo on 9s 8c 6s 5c 7s and KJo
on 5s 6h 7c 9c 8s were played as monsters."""

from __future__ import annotations

import pytest

from app.domain.personas_postflop import StrengthBucket, strength_bucket


@pytest.mark.parametrize(
    "hole, board",
    [
        pytest.param(("Ah", "Qd"), ["9s", "8c", "6s", "5c", "7s"], id="AQo-on-board-straight"),
        pytest.param(("Kd", "Jh"), ["5s", "6h", "7c", "9c", "8s"], id="KJo-on-board-straight"),
        pytest.param(("6h", "2d"), ["9s", "8c", "6s", "5c", "7s"], id="hole-6-in-board-straight"),
        pytest.param(("Qd", "2h"), ["8s", "8h", "8d", "8c", "Ks"], id="board-quads-board-kicker"),
        pytest.param(("7h", "2d"), ["8s", "8h", "8d", "7c", "7s"], id="hole-7-on-board-boat"),
    ],
)
def test_board_made_hand_the_hole_cards_do_not_improve_is_middle_pair(hole, board):
    assert strength_bucket(hole, board)[0] is StrengthBucket.MIDDLE_PAIR


@pytest.mark.parametrize(
    "hole, board",
    [
        pytest.param(("Th", "2d"), ["5s", "6h", "7c", "8c", "9s"], id="hole-T-tops-board-straight"),
        pytest.param(("Ah", "3c"), ["2h", "5h", "8h", "Jh", "Kh"], id="hole-ace-of-board-flush"),
        pytest.param(("9s", "9h"), ["8s", "8h", "8d", "7c", "7s"], id="hole-99-on-board-boat"),
        pytest.param(("7d", "2h"), ["9s", "8c", "6s", "5c"], id="straight-on-four-card-board"),
    ],
)
def test_hole_cards_that_improve_the_hand_stay_monster(hole, board):
    assert strength_bucket(hole, board)[0] is StrengthBucket.MONSTER
