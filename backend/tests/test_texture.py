from app.domain.texture import classify


def test_dry_rainbow_unpaired_anchor():
    t = classify(["As", "Kd", "2c"])
    assert t.wetness == "dry"
    assert t.suitedness == "rainbow"
    assert t.pairing == "unpaired"
    assert t.connectedness == "disconnected"
    assert t.high_card == "A"
    assert t.high_board is True


def test_wet_monotone_connected_anchor():
    t = classify(["9h", "8h", "7h"])
    assert t.wetness == "wet"
    assert t.suitedness == "monotone"
    assert t.connectedness == "connected"
    assert t.pairing == "unpaired"


def test_paired_board():
    t = classify(["Kh", "Kd", "7c"])
    assert t.pairing == "paired"


def test_texture_class_is_board_independent():
    # Two different dry, rainbow, disconnected, unpaired flops share a class.
    a = classify(["As", "Kd", "2c"]).texture_class
    b = classify(["Ah", "Qd", "3c"]).texture_class
    assert a == b


def test_needs_three_cards():
    try:
        classify(["As", "Kd"])
    except ValueError:
        return
    raise AssertionError("expected ValueError for a 2-card board")


# --- W5-c2: street-aware classification (opt-in re-classification) ---


def test_default_street_is_flop_and_ignores_extra_cards():
    """The default (no `street=`) must stay byte-identical to the pre-W5-c2
    behavior: only the first 3 cards matter, regardless of board length."""
    flop_only = classify(["As", "Kd", "2c"])
    with_turn_river = classify(["As", "Kd", "2c", "7h", "9s"])
    assert flop_only == with_turn_river


def test_board_pairs_on_turn_differs_from_own_flop():
    board = ["As", "Kd", "2c", "2h"]  # dry unpaired flop, turn pairs the 2
    flop = classify(board[:3], street="flop")
    turn = classify(board, street="turn")
    assert flop.pairing == "unpaired"
    assert turn.pairing == "paired"
    assert flop != turn


def test_board_rivers_a_monotone_flush_differs_from_own_flop():
    board = ["Ah", "Kh", "2c", "9d", "5h"]  # two-tone flop, river brings 3rd heart
    flop = classify(board[:3], street="flop")
    river = classify(board, street="river")
    assert flop.suitedness == "two-tone"
    assert river.suitedness == "monotone"
    assert flop != river


def test_turn_street_needs_four_cards():
    try:
        classify(["As", "Kd", "2c"], street="turn")
    except ValueError:
        return
    raise AssertionError("expected ValueError for a 3-card board at street='turn'")


def test_river_street_needs_five_cards():
    try:
        classify(["As", "Kd", "2c", "7h"], street="river")
    except ValueError:
        return
    raise AssertionError("expected ValueError for a 4-card board at street='river'")
