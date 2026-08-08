"""T3 (flywheel S6): golden cross-source fixtures for the blind-detection renderer.

The pilot's whole validity rests on one property: a judge must not be able to
tell a human-played bundle from a bot-played bundle by anything except the
play. So the load-bearing test here is `test_cross_source_bytes_identical` —
the SAME underlying hand, fed through the human-shaped input (a serialized
`state_json` TEXT column, exactly what `sim_session` persists at
`sim_session.py:263`/`:923`) and the bot-shaped input (an in-memory terminal
`HandState` from a self-play run), must render to byte-identical text.

Every fixture is built by driving the REAL domain engine
(`start_hand`/`apply`/`settle`), never by hand-writing a `HandState`, so the
scenarios (fold-out, all-in run-out, side pot, multi-way showdown,
no-showdown river) are engine-true rather than test-author-true.
"""

from __future__ import annotations

import math
import random

import pytest

from app.domain.action import Decision
from app.domain.personas import load_persona_packs
from app.domain.spot import ActionType, PlayerStatus, Street
from app.domain.table.deck import deal_hand
from app.domain.table.engine import HandState, apply, settle, start_hand
from app.domain.table.play import bot_decision
from tools.detection_render import (
    _EPS,  # reconciliation tolerance — asserted against, never reused as one
    _ZERO_CHIPS,
    MAX_LOCAL_HAND_INDEX,
    CanonicalHandError,
    from_bot,
    from_human,
    leak_check,
    render_bundle,
)
from tools.export_analytics import DEFAULT_LINEUP, _draw_buyin_targets

# --- fixture construction ---------------------------------------------------

FOLD = Decision(action=ActionType.FOLD)
CALL = Decision(action=ActionType.CALL)
CHECK = Decision(action=ActionType.CHECK)


def raise_to(amount: float) -> Decision:
    return Decision(action=ActionType.RAISE, size_bb=amount)


def bet(amount: float) -> Decision:
    return Decision(action=ActionType.BET, size_bb=amount)


def play(seed: int, button: int, stacks: list[float], script: list[Decision]) -> HandState:
    """Drive the real engine through a scripted line; assert the hand ended."""
    state = start_hand(deal_hand(random.Random(seed)), button, stacks)
    for i, decision in enumerate(script):
        assert not state.hand_over, f"script step {i}: hand already over"
        state = apply(state, decision)
    assert state.hand_over, "script did not finish the hand"
    return state


# Button 3 => seat 6 = UTG, 7 = UTG1, 8 = UTG2, 0 = LJ, 1 = HJ, 2 = CO,
# 3 = BTN, 4 = SB, 5 = BB (engine `positions_for_button`).
BUTTON = 3
FLAT = [100.0] * 9


def hand_foldout_preflop() -> HandState:
    """Everyone folds to the BB — no board is ever revealed."""
    return play(7, BUTTON, FLAT, [FOLD] * 8)


def hand_allin_runout() -> HandState:
    """UTG jams 100bb, BTN calls: the board runs out with zero postflop action."""
    stacks = list(FLAT)
    return play(
        21,
        BUTTON,
        stacks,
        [raise_to(100.0), FOLD, FOLD, FOLD, FOLD, FOLD, CALL, FOLD, FOLD],
    )


def hand_side_pot() -> HandState:
    """Short-stacked UTG (12bb) jams; LJ and BTN call and keep betting."""
    stacks = list(FLAT)
    stacks[6] = 12.0
    return play(
        11,
        BUTTON,
        stacks,
        [
            raise_to(12.0), FOLD, FOLD, CALL, FOLD, FOLD, CALL, FOLD, FOLD,  # preflop
            bet(15.0), CALL,  # flop
            CHECK, CHECK,  # turn
            CHECK, CHECK,  # river
        ],
    )


def hand_multiway_showdown() -> HandState:
    """Three seats limp/call to a checked-down river showdown."""
    return play(
        33,
        BUTTON,
        FLAT,
        [
            CALL, FOLD, FOLD, CALL, FOLD, FOLD, FOLD, FOLD, CHECK,  # preflop
            CHECK, CHECK, CHECK,  # flop
            CHECK, CHECK, CHECK,  # turn
            CHECK, CHECK, CHECK,  # river
        ],
    )


def hand_no_showdown_river() -> HandState:
    """Full five-card board, but the river bet takes it down uncontested."""
    return play(
        5,
        BUTTON,
        FLAT,
        [
            raise_to(3.0), FOLD, FOLD, CALL, FOLD, FOLD, FOLD, FOLD, FOLD,  # preflop
            bet(4.0), CALL,  # flop
            bet(9.0), CALL,  # turn
            bet(25.0), FOLD,  # river
        ],
    )


ALL_FIXTURES = {
    "foldout_preflop": (hand_foldout_preflop, 4),
    "allin_runout": (hand_allin_runout, 6),
    "side_pot": (hand_side_pot, 6),
    "multiway_showdown": (hand_multiway_showdown, 6),
    "no_showdown_river": (hand_no_showdown_river, 0),
}

SEAT_ID_MAP = {
    0: "P4",
    1: "P9",
    2: "P2",
    3: "P7",
    4: "P1",
    5: "P5",
    6: "P8",
    7: "P3",
    8: "P6",
}


def render_one(state: HandState, focus_seat: int) -> str:
    return render_bundle(
        [from_bot(state, focus_seat)], SEAT_ID_MAP[focus_seat], SEAT_ID_MAP
    )


# --- 1. cross-source identity (the load-bearing test) -----------------------


@pytest.mark.parametrize("name", sorted(ALL_FIXTURES))
def test_cross_source_bytes_identical(name):
    """Human-shaped input and bot-shaped input for the SAME hand must render
    to identical bytes — the pilot's blinding rests on this."""
    build, focus = ALL_FIXTURES[name]
    state = build()
    # The human side sees exactly what `sim_session` writes to the DB column.
    human = from_human(state.model_dump_json(), focus)
    bot = from_bot(state, focus)
    assert human == bot, f"{name}: canonical records diverge across sources"
    opaque = SEAT_ID_MAP[focus]
    assert render_bundle([human], opaque, SEAT_ID_MAP) == render_bundle(
        [bot], opaque, SEAT_ID_MAP
    )


def test_cross_source_identical_for_a_whole_bundle():
    """Same property over a mixed multi-hand bundle, all focused on one seat."""
    states = [
        hand_foldout_preflop(),
        hand_allin_runout(),
        hand_side_pot(),
        hand_multiway_showdown(),
        hand_no_showdown_river(),
    ]
    focus = 6
    human_bundle = [from_human(s.model_dump_json(), focus) for s in states]
    bot_bundle = [from_bot(s, focus) for s in states]
    opaque = SEAT_ID_MAP[focus]
    assert render_bundle(human_bundle, opaque, SEAT_ID_MAP) == render_bundle(
        bot_bundle, opaque, SEAT_ID_MAP
    )


REAL_HANDS = 8


def real_bot_hands(seed: int = 905, n: int = REAL_HANDS) -> list[HandState]:
    """Replay `n` hands forward through the REAL production machinery — the
    same `deal_hand`/`start_hand`/`bot_decision`/`apply` loop and the same
    `--buyin-spread` targets `export_analytics` uses.

    Per-hand re-simulation from `hand_seed` alone would NOT be faithful:
    `bot_decision` draws from the run-level RNG, whose state depends on every
    preceding hand. So the run is replayed forward and each terminal state
    kept — exactly the interface `from_bot` is built for, and exactly what the
    corpus builder will do.
    """
    packs = load_persona_packs()
    persona_by_seat = {i: DEFAULT_LINEUP[i % len(DEFAULT_LINEUP)] for i in range(9)}
    rng = random.Random(seed)
    states = []
    for i in range(n):
        hand_seed = rng.randrange(1_000_000_000)
        state = start_hand(
            deal_hand(random.Random(hand_seed)), i % 9, _draw_buyin_targets(hand_seed)
        )
        while not state.hand_over:
            seat = state.to_act_seat
            state = apply(
                state, bot_decision(state, seat, packs[persona_by_seat[seat]], rng)
            )
        states.append(state)
    return states


def test_real_production_hands_converge_across_both_adapters():
    """The permanent version of the throwaway real-corpus probe: real
    production-policy hands, round-tripped through SQLite's storage form
    (`model_dump_json()` -> TEXT -> `from_human`) and fed live to `from_bot`,
    must produce identical records, identical bytes, and no leaks."""
    states = real_bot_hands()
    assert len(states) == REAL_HANDS
    focus = 4
    opaque = SEAT_ID_MAP[focus]

    via_db = [from_human(s.model_dump_json(), focus) for s in states]
    via_memory = [from_bot(s, focus) for s in states]
    assert via_db == via_memory

    text = render_bundle(via_db, opaque, SEAT_ID_MAP, expected_count=REAL_HANDS)
    assert text == render_bundle(via_memory, opaque, SEAT_ID_MAP)
    # Everything the bundle came from, handed to the auditor as forbidden.
    forbidden = [*DEFAULT_LINEUP, "run-s901", "901"]
    assert leak_check(text, forbidden=forbidden) == []


def test_real_production_hands_exercise_more_than_one_shape():
    """Guard against the integration test silently degenerating into eight
    look-alike hands. Seed 905 was picked because eight real hands already
    span every rendering branch: a preflop fold-out (no board), a flop
    ending, rivers, showdown and no-showdown ends, and a side pot."""
    hands = [from_bot(s, 4) for s in real_bot_hands()]
    assert {len(h.board) for h in hands} == {0, 3, 5}
    assert any(h.showdown_seats for h in hands)
    assert any(not h.showdown_seats for h in hands)
    assert any(len(h.pots) > 1 for h in hands)


# --- 2. board reveal --------------------------------------------------------


def test_foldout_preflop_reveals_no_board():
    state = hand_foldout_preflop()
    assert len(state.full_board) == 5  # the runout WAS dealt...
    text = render_one(state, 4)
    for card in state.full_board:  # ...and none of it may appear
        assert card not in text
    assert "Flop" not in text and "Turn" not in text and "River" not in text


def test_allin_runout_reveals_full_board_without_postflop_action():
    """The reveal depth cannot come from the action history here: the players
    saw all five cards with zero postflop actions."""
    state = hand_allin_runout()
    hand = from_bot(state, 6)
    assert hand.board == tuple(state.full_board)
    assert not [a for a in hand.actions if a.street != "preflop"]
    text = render_one(state, 6)
    assert "River (pot" in text
    for card in state.full_board:
        assert card in text


def test_no_showdown_river_shows_board_but_no_opponent_cards():
    state = hand_no_showdown_river()
    hand = from_bot(state, 0)
    assert len(hand.board) == 5
    assert hand.showdown_seats == ()
    text = render_one(state, 0)
    assert "Showdown" not in text


# --- 3. hole-card redaction -------------------------------------------------


@pytest.mark.parametrize("name", sorted(ALL_FIXTURES))
def test_only_focus_and_showdown_cards_survive_the_adapter(name):
    build, focus = ALL_FIXTURES[name]
    state = build()
    hand = from_bot(state, focus)
    settlement = settle(state)
    revealable = {focus, *settlement.showdown_seats}
    for seat in hand.seats:
        if seat.seat in revealable:
            assert seat.hole_cards is not None
        else:
            assert seat.hole_cards is None, f"seat {seat.seat} leaked its cards"
    text = render_one(state, focus)
    for seat_state in state.seats:
        if seat_state.seat in revealable:
            continue
        assert " ".join(seat_state.hole_cards) not in text


def test_multiway_showdown_shows_every_compared_hand():
    state = hand_multiway_showdown()
    settlement = settle(state)
    assert len(settlement.showdown_seats) >= 3
    text = render_one(state, 6)
    for seat in settlement.showdown_seats:
        assert " ".join(state.seats[seat].hole_cards) in text


def test_folded_focus_seat_still_shows_its_own_cards():
    state = hand_side_pot()
    focus = 7  # UTG1: folds preflop
    assert state.seats[focus].status.value == "folded"
    text = render_one(state, focus)
    assert " ".join(state.seats[focus].hole_cards) in text


# --- 4. side pots and stacks ------------------------------------------------


def test_side_pot_renders_every_layer():
    state = hand_side_pot()
    hand = from_bot(state, 6)
    assert len(hand.pots) >= 2, "fixture must produce a genuine side pot"
    text = render_one(state, 6)
    assert "Main pot" in text and "Side pot 1" in text
    for pot in hand.pots:
        assert f"{pot.amount_bb:.2f}" in text


def test_starting_stacks_are_two_decimal_and_per_hand():
    """Spread runs and live re-buys both vary in [95,105]bb; the derivation
    (`stack_bb + invested_total_bb` off the terminal state) and the 2dp
    formatting must be identical for both classes."""
    stacks = [95.0, 97.33, 100.0, 101.5, 104.99, 100.0, 99.01, 100.0, 103.25]
    state = play(7, BUTTON, stacks, [FOLD] * 8)
    hand = from_bot(state, 4)
    assert [s.starting_stack_bb for s in hand.seats] == stacks
    text = render_one(state, 4)
    assert "104.99" in text and "97.33" in text and "95.00" in text


# --- 5. re-keying and stripping --------------------------------------------


def test_hands_are_rekeyed_to_local_indices():
    """A hand whose source `hand_no` is 1042 renders as its LOCAL index. The
    canonical record has no field for a source hand number at all, so the
    source key cannot reach the renderer even if the caller knows it."""
    source_hand_no = 1042
    states = [hand_foldout_preflop(), hand_no_showdown_river(), hand_multiway_showdown()]
    bundle = [from_human(s.model_dump_json(), 6) for s in states]
    text = render_bundle(bundle, SEAT_ID_MAP[6], SEAT_ID_MAP)
    assert "### Hand 1" in text and "### Hand 2" in text and "### Hand 3" in text
    assert str(source_hand_no) not in text
    assert not hasattr(bundle[0], "hand_no")


def test_no_raw_seat_indices_in_output():
    state = hand_multiway_showdown()
    text = render_one(state, 6)
    assert "seat" not in text.lower()
    # Every acting player appears under its opaque ID, never a raw seat index.
    for seat in {a.seat for a in from_bot(state, 6).actions}:
        assert SEAT_ID_MAP[seat] in text


@pytest.mark.parametrize("name", sorted(ALL_FIXTURES))
def test_leak_check_clean_on_every_fixture(name):
    build, focus = ALL_FIXTURES[name]
    text = render_one(build(), focus)
    assert leak_check(text) == []


def test_leak_check_clean_on_a_full_bundle_with_forbidden_tokens_supplied():
    states = [build() for build, _ in sorted(ALL_FIXTURES.values(), key=lambda t: t[0].__name__)]
    bundle = [from_bot(s, 6) for s in states]
    text = render_bundle(bundle, SEAT_ID_MAP[6], SEAT_ID_MAP)
    forbidden = ["run-s901-n1200-bspread-c3a64601cbe06", "nit", "tag", "deadbeef"]
    assert leak_check(text, forbidden=forbidden) == []


# --- 6. the auditor itself --------------------------------------------------


@pytest.mark.parametrize(
    ("seeded", "expected_fragment"),
    [
        ("### Hand 1\nP4 (BTN) is a calling_station", "persona name"),
        ("### Hand 1\nP4 plays like a NIT here", "persona name"),
        ("### Hand 1\npersona: unknown", "persona/role label"),
        ("### Hand 1\nHERO holds As Kd", "persona/role label"),
        ("### Hand 1\nseat_index 4 acts", "seat-index field"),
        ("### Hand 1\nSeat 4 (BTN) folds", "raw seat index"),
        ("### Hand 1\nrun-s42-n1200-c0123456789ab", "run id"),
        (
            "### Hand 1\n"
            "3a64601cbe060373d06a93fd7cd285bd6b0d47b58b23c53ad2e1031ef088b3f8",
            "config-hash-like token",
        ),
        ("### Hand 1\nsession 9f2c", "session metadata"),
        ("### Hand 31\nP4 folds", "absolute hand number"),
        ("### Hand 1042\nP4 folds", "absolute hand number"),
        ("### Hand 1\nplayed 2026-08-07T14:02:11Z", "ISO timestamp"),
        ("### Hand 1\ndealt 2026-08-07", "ISO timestamp"),
    ],
)
def test_leak_check_catches_seeded_violations(seeded, expected_fragment):
    found = leak_check(seeded)
    assert found, f"auditor missed: {seeded!r}"
    assert any(v.startswith(expected_fragment) for v in found), found


def test_leak_check_catches_caller_supplied_forbidden_tokens():
    text = render_one(hand_foldout_preflop(), 4)
    found = leak_check(text, forbidden=["P4"])  # an opaque ID that IS in the text
    assert found == ["forbidden token: 'P4'"]


def test_leak_check_allows_local_indices_up_to_the_bundle_size():
    text = "\n".join(
        f"### Hand {i}\nP1 folds" for i in range(1, MAX_LOCAL_HAND_INDEX + 1)
    )
    assert leak_check(text) == []


@pytest.mark.parametrize(
    "headers",
    [
        [2, 3, 4],  # does not start at 1
        [1, 3, 4],  # gap
        [1, 2, 2],  # duplicate
        [1, 3, 2],  # out of order
        [12],  # in range, but not this bundle's local index
    ],
)
def test_leak_check_catches_broken_local_index_grammar(headers):
    """A source key can hide inside a plausible-looking small number, so the
    header sequence itself is audited, not just the magnitude."""
    text = "\n".join(f"### Hand {h}\nP1 folds" for h in headers)
    found = leak_check(text)
    assert any(v.startswith("hand header sequence") for v in found), found


@pytest.mark.parametrize(
    "field",
    ["hand_no", "hand_id", "run_id", "config_hash", "session_id", "seat_index"],
)
def test_leak_check_catches_metadata_field_names(field):
    found = leak_check(f"### Hand 1\n{field}=abc123")
    assert found, f"auditor missed {field}"


def test_leak_check_returns_sorted_deduplicated_violations():
    text = "### Hand 40\n### Hand 40\nsession a\nseat_index 1"
    found = leak_check(text)
    assert found == sorted(found)
    assert len(found) == len(set(found))


# --- 7. determinism ---------------------------------------------------------


def test_render_is_byte_identical_across_repeat_calls():
    states = [hand_side_pot(), hand_allin_runout(), hand_no_showdown_river()]
    bundle = [from_bot(s, 6) for s in states]
    first = render_bundle(bundle, SEAT_ID_MAP[6], SEAT_ID_MAP)
    second = render_bundle(bundle, SEAT_ID_MAP[6], SEAT_ID_MAP)
    assert first == second
    # ...and re-deriving the canonical records changes nothing either.
    again = [from_bot(s, 6) for s in states]
    assert render_bundle(again, SEAT_ID_MAP[6], SEAT_ID_MAP) == first


def test_render_does_not_depend_on_seat_id_map_insertion_order():
    state = hand_multiway_showdown()
    bundle = [from_bot(state, 6)]
    shuffled = dict(sorted(SEAT_ID_MAP.items(), reverse=True))
    assert list(shuffled) != list(SEAT_ID_MAP)
    assert render_bundle(bundle, SEAT_ID_MAP[6], shuffled) == render_bundle(
        bundle, SEAT_ID_MAP[6], SEAT_ID_MAP
    )


# --- 8. malformed input must RAISE, never render ----------------------------


def test_rejects_unparseable_state_json():
    with pytest.raises(CanonicalHandError):
        from_human("{not json", 4)


def test_rejects_empty_state_json():
    with pytest.raises(CanonicalHandError):
        from_human("", 4)


def test_rejects_json_that_is_not_a_hand_state():
    with pytest.raises(CanonicalHandError):
        from_human('{"button_seat": 3}', 4)


def test_rejects_hand_persisted_mid_hand():
    """`state_json` is written at every hero decision point, not only at
    settlement — a `hand_over=False` row must be rejected, not rendered."""
    state = start_hand(deal_hand(random.Random(7)), BUTTON, FLAT)
    assert not state.hand_over
    with pytest.raises(CanonicalHandError, match="not over"):
        from_human(state.model_dump_json(), 4)
    with pytest.raises(CanonicalHandError, match="not over"):
        from_bot(state, 4)


@pytest.mark.parametrize("focus", [-1, 9, 100, "4", None, True])
def test_rejects_out_of_range_focus_seat(focus):
    state = hand_foldout_preflop()
    with pytest.raises(CanonicalHandError):
        from_bot(state, focus)


def test_rejects_non_hand_state_bot_input():
    with pytest.raises(CanonicalHandError):
        from_bot({"button_seat": 3}, 4)


def test_rejects_board_inconsistent_with_final_street():
    """A hand that ended preflop but carries a flop in `board` is a tampered
    or mis-parsed row — refuse it rather than reveal cards nobody saw."""
    state = hand_foldout_preflop()
    tampered = state.model_copy(deep=True)
    tampered.board = list(state.full_board[:3])
    with pytest.raises(CanonicalHandError, match="revealed board"):
        from_bot(tampered, 4)


def test_rejects_board_shorter_than_the_final_street():
    state = hand_no_showdown_river()
    tampered = state.model_copy(deep=True)
    tampered.board = list(state.full_board[:4])  # river street, only a turn shown
    with pytest.raises(CanonicalHandError, match="revealed board"):
        from_bot(tampered, 0)


def test_rejects_history_deeper_than_the_revealed_board():
    """Street and board agree with each other but contradict the action
    history — a hand with river action may not be rendered as a turn."""
    state = hand_no_showdown_river()
    tampered = state.model_copy(deep=True)
    tampered.street = Street.TURN
    tampered.board = list(state.full_board[:4])
    with pytest.raises(CanonicalHandError, match="reaches river"):
        from_bot(tampered, 0)


def test_rejects_ledger_history_mismatch():
    state = hand_no_showdown_river()
    tampered = state.model_copy(deep=True)
    tampered.seats[0].invested_total_bb += 5.0
    with pytest.raises(CanonicalHandError, match="inconsistent hand"):
        from_bot(tampered, 0)


# --- 8b. adversarial corruption: never render a class tell ------------------


def test_pydantic_really_does_parse_nan_from_a_json_column():
    """Guard for the premise of the next test: a corrupt SQLite row CAN carry
    NaN into a float field, which would render as a literal 'nan' stack."""
    state = hand_foldout_preflop()
    poisoned = state.model_dump_json().replace('"stack_bb":99.5', '"stack_bb":NaN', 1)
    assert poisoned != state.model_dump_json()
    assert math.isnan(HandState.model_validate_json(poisoned).seats[4].stack_bb)


def test_rejects_nan_stack_through_the_real_human_path():
    state = hand_foldout_preflop()
    poisoned = state.model_dump_json().replace('"stack_bb":99.5', '"stack_bb":NaN', 1)
    with pytest.raises(CanonicalHandError, match="not a finite number"):
        from_human(poisoned, 4)


@pytest.mark.parametrize("bad", [float("inf"), float("-inf"), float("nan")])
def test_rejects_non_finite_money_anywhere(bad):
    state = hand_side_pot()
    tampered = state.model_copy(deep=True)
    tampered.action_history[3].amount_bb = bad
    with pytest.raises(CanonicalHandError, match="not a finite number"):
        from_bot(tampered, 6)


def test_rejects_negative_money():
    state = hand_foldout_preflop()
    tampered = state.model_copy(deep=True)
    tampered.seats[2].invested_total_bb = -1.0
    with pytest.raises(CanonicalHandError, match="negative"):
        from_bot(tampered, 4)


def test_one_negative_cent_sits_between_the_old_and_new_thresholds():
    """Premise guard for the boundary test below: -0.01 is exactly the value
    the OLD `_EPS`-based guard tolerated and the tightened one rejects. If
    someone widens `_ZERO_CHIPS` back toward `_EPS`, this fails first and
    says why."""
    assert -_EPS < -0.01 < -_ZERO_CHIPS


def test_rejects_one_negative_cent():
    """Boundary: a single negative cent is corrupt data, not float noise. The
    original guard reused `_EPS` (0.011) and silently tolerated this — so a
    revert to `_EPS` must turn this test red, which `-1.0` alone could not
    detect."""
    state = hand_foldout_preflop()
    tampered = state.model_copy(deep=True)
    tampered.seats[2].invested_total_bb = -0.01
    with pytest.raises(CanonicalHandError, match="negative"):
        from_bot(tampered, 4)


def test_accepts_sub_half_cent_negative_residue():
    """The other side of the boundary, and deliberately NOT zero tolerance.

    Real engine float noise is ~1e-9 (see `engine._EPS`), so nothing legitimate
    lands near -0.004; this guard exists for CORRUPT data, and the tolerance is
    kept symmetric with `_ZERO_CHIPS` on purpose — the same "half a cent" line
    separates chips from residue in both directions, so there is one rule to
    reason about rather than two. A folded seat is used because a negative
    stack on a live seat would (correctly) trip the zero-chips status check
    first, which would mask what this test is measuring.
    """
    state = hand_foldout_preflop()
    assert state.seats[2].status is PlayerStatus.FOLDED
    tampered = state.model_copy(deep=True)
    tampered.seats[2].stack_bb = -0.004
    assert -_ZERO_CHIPS < -0.004
    assert from_bot(tampered, 4) is not None


def test_rejects_duplicate_seat_index():
    state = hand_foldout_preflop()
    tampered = state.model_copy(deep=True)
    tampered.seats[3].seat = 4
    with pytest.raises(CanonicalHandError, match="permutation"):
        from_bot(tampered, 4)


def test_rejects_duplicate_position():
    state = hand_foldout_preflop()
    tampered = state.model_copy(deep=True)
    tampered.seats[3].position = tampered.seats[4].position
    with pytest.raises(CanonicalHandError, match="positions"):
        from_bot(tampered, 4)


def test_rejects_a_card_dealt_twice():
    state = hand_foldout_preflop()
    tampered = state.model_copy(deep=True)
    tampered.seats[2].hole_cards = tampered.seats[5].hole_cards
    with pytest.raises(CanonicalHandError, match="more than once"):
        from_bot(tampered, 4)


def test_rejects_a_hole_card_that_collides_with_the_board():
    state = hand_no_showdown_river()
    tampered = state.model_copy(deep=True)
    tampered.seats[1].hole_cards = (state.full_board[0], state.seats[1].hole_cards[1])
    with pytest.raises(CanonicalHandError, match="more than once"):
        from_bot(tampered, 0)


def test_rejects_malformed_card():
    state = hand_foldout_preflop()
    tampered = state.model_copy(deep=True)
    tampered.seats[2].hole_cards = ("Zx", tampered.seats[2].hole_cards[1])
    with pytest.raises(CanonicalHandError, match="malformed card"):
        from_bot(tampered, 4)


def test_rejects_board_that_is_not_a_prefix_of_the_runout():
    """Same length as the street allows, but different cards — the players saw
    the runout, not whatever this row claims."""
    state = hand_no_showdown_river()
    tampered = state.model_copy(deep=True)
    tampered.board = list(reversed(state.full_board))
    assert len(tampered.board) == len(state.board)
    with pytest.raises(CanonicalHandError, match="prefix"):
        from_bot(tampered, 0)


def test_rejects_truncated_runout():
    state = hand_foldout_preflop()
    tampered = state.model_copy(deep=True)
    tampered.full_board = list(state.full_board[:3])
    with pytest.raises(CanonicalHandError, match="runout"):
        from_bot(tampered, 4)


def test_rejects_all_in_seat_that_still_has_chips():
    state = hand_allin_runout()
    tampered = state.model_copy(deep=True)
    allin = next(s for s in tampered.seats if s.status.value == "allin")
    allin.stack_bb = 10.0
    with pytest.raises(CanonicalHandError, match="all-in but still holds"):
        from_bot(tampered, 6)


def test_rejects_live_seat_with_no_chips_and_no_all_in_flag():
    state = hand_multiway_showdown()
    tampered = state.model_copy(deep=True)
    live = next(s for s in tampered.seats if s.status.value == "in")
    live.stack_bb = 0.0
    with pytest.raises(CanonicalHandError, match="not marked all-in"):
        from_bot(tampered, 6)


def test_rejects_street_investment_exceeding_hand_investment():
    state = hand_no_showdown_river()
    tampered = state.model_copy(deep=True)
    tampered.seats[0].invested_street_bb = tampered.seats[0].invested_total_bb + 5.0
    with pytest.raises(CanonicalHandError, match="this street"):
        from_bot(tampered, 0)


# --- 8c. one cent is a chip (T7 acceptance regression) ----------------------


def hand_one_cent_behind() -> HandState:
    """A seat that legally ends the hand IN with exactly 0.01bb behind.

    UTG jams 10.00; the BB (buy-in 10.01) calls. CALL caps its increment at
    `min(to_call, stack_bb)` = 9.00, leaving one cent, and `engine._pay` marks
    ALLIN only at `stack_bb <= 1e-9` — so the BB stays IN holding a live chip.
    Under the §A.1 integer-cent buy-in spread this is an ordinary outcome, not
    a corrupt state.
    """
    stacks = list(FLAT)
    stacks[6] = 10.00  # UTG
    stacks[5] = 10.01  # BB
    return play(
        13,
        BUTTON,
        stacks,
        [raise_to(10.0), FOLD, FOLD, FOLD, FOLD, FOLD, FOLD, FOLD, CALL],
    )


def test_one_cent_behind_is_a_state_the_engine_itself_produces():
    """Premise guard: assert the ENGINE's semantics, so this regression can
    never be explained away by loosening a validator against a state the
    engine would supposedly never produce."""
    state = hand_one_cent_behind()
    bb = state.seats[5]
    assert bb.status is PlayerStatus.IN
    assert bb.stack_bb == pytest.approx(0.01, abs=1e-9)
    assert bb.stack_bb > 1e-9  # the engine's own all-in threshold


def test_accepts_seat_in_with_exactly_one_cent_behind():
    """The T7 acceptance regression: `_EPS` (0.011, a RECONCILIATION
    tolerance) had been reused as a zero-chips test and rejected this legal
    hand — it occurs once per ~1,500 spread-mode hands, which was enough to
    abort most master seeds."""
    hand = from_bot(hand_one_cent_behind(), 5)
    assert hand.seats[5].starting_stack_bb == pytest.approx(10.01)


def test_one_cent_seat_is_not_labelled_all_in():
    """The same one-chip confusion also corrupted judge-facing TEXT: a seat
    with a cent behind is not all-in and must not read as such."""
    state = hand_one_cent_behind()
    hand = from_bot(state, 5)
    bb_call = next(
        a for a in hand.actions if a.seat == 5 and a.action == ActionType.CALL.value
    )
    assert not bb_call.all_in
    utg_jam = next(
        a for a in hand.actions if a.seat == 6 and a.action == ActionType.RAISE.value
    )
    assert utg_jam.all_in  # the genuinely all-in seat still reads all-in
    text = render_one(state, 5)
    assert "(all-in)" in text  # UTG's jam
    assert "calls 9.00 (all-in)" not in text


def test_rejects_live_seat_with_true_zero_behind():
    """The tightened threshold must still catch a real zero — the fix must not
    trade a false positive for a false negative."""
    tampered = hand_one_cent_behind().model_copy(deep=True)
    tampered.seats[5].stack_bb = 0.0
    with pytest.raises(CanonicalHandError, match="not marked all-in"):
        from_bot(tampered, 5)


def test_rejects_all_in_seat_holding_a_single_cent():
    """Inverse invariant preserved: one cent is a chip, so an ALLIN seat
    holding one is still a contradiction."""
    tampered = hand_one_cent_behind().model_copy(deep=True)
    allin = next(s for s in tampered.seats if s.status is PlayerStatus.ALLIN)
    allin.stack_bb = 0.01
    with pytest.raises(CanonicalHandError, match="all-in but still holds"):
        from_bot(tampered, 5)


def test_rejects_empty_bundle():
    with pytest.raises(CanonicalHandError):
        render_bundle([], "P1", SEAT_ID_MAP)


def test_expected_count_enforces_the_pinned_bundle_size():
    bundle = [from_bot(hand_foldout_preflop(), 4), from_bot(hand_side_pot(), 4)]
    opaque = SEAT_ID_MAP[4]
    assert render_bundle(bundle, opaque, SEAT_ID_MAP, expected_count=2)
    with pytest.raises(CanonicalHandError, match="expected exactly 30"):
        render_bundle(bundle, opaque, SEAT_ID_MAP, expected_count=30)


def test_expected_count_defaults_to_flexible_for_dry_run_decks():
    """Default None keeps the 6+6 acceptance dry-run renderable."""
    bundle = [from_bot(hand_foldout_preflop(), 4)]
    assert render_bundle(bundle, SEAT_ID_MAP[4], SEAT_ID_MAP)


def test_rejects_incomplete_seat_id_map():
    hand = from_bot(hand_foldout_preflop(), 4)
    with pytest.raises(CanonicalHandError, match="missing seat"):
        render_bundle([hand], "P1", {4: "P1"})


def test_rejects_duplicate_opaque_ids():
    hand = from_bot(hand_foldout_preflop(), 4)
    dupes = dict(SEAT_ID_MAP)
    dupes[0] = dupes[1]
    with pytest.raises(CanonicalHandError, match="duplicate"):
        render_bundle([hand], SEAT_ID_MAP[4], dupes)


def test_rejects_focus_label_that_does_not_match_the_focus_seat():
    hand = from_bot(hand_foldout_preflop(), 4)
    with pytest.raises(CanonicalHandError, match="focus_seat_opaque_id"):
        render_bundle([hand], SEAT_ID_MAP[0], SEAT_ID_MAP)


def test_rejects_a_bundle_whose_hands_have_different_focus_seats():
    mixed = [from_bot(hand_foldout_preflop(), 4), from_bot(hand_side_pot(), 6)]
    with pytest.raises(CanonicalHandError):
        render_bundle(mixed, SEAT_ID_MAP[4], SEAT_ID_MAP)


# --- 9. golden text ---------------------------------------------------------


def test_golden_foldout_bundle_text():
    """Freeze the exact outbound judge payload for one bundle. If this text
    changes, the change is visible to reviewers rather than silent."""
    text = render_one(hand_foldout_preflop(), 4)
    assert text == (
        "Player under review: P1\n"
        "9-handed No-Limit Hold'em. Blinds 0.50 / 1.00. All amounts in big blinds.\n"
        "Hands: 1, consecutive, in order of play.\n"
        "\n"
        "### Hand 1\n"
        "Stacks: P8 (UTG) 100.00 | P3 (UTG1) 100.00 | P6 (UTG2) 100.00 | "
        "P4 (LJ) 100.00 | P9 (HJ) 100.00 | P2 (CO) 100.00 | P7 (BTN) 100.00 | "
        "P1 (SB) 100.00 | P5 (BB) 100.00\n"
        "P1 (SB) holds 5h Ah\n"
        "Preflop (pot 0.00)\n"
        "  P1 (SB) posts 0.50\n"
        "  P5 (BB) posts 1.00\n"
        "  P8 (UTG) folds\n"
        "  P3 (UTG1) folds\n"
        "  P6 (UTG2) folds\n"
        "  P4 (LJ) folds\n"
        "  P9 (HJ) folds\n"
        "  P2 (CO) folds\n"
        "  P7 (BTN) folds\n"
        "  P1 (SB) folds\n"
        "Result: Pot 1.50 to P5 | P1 net -0.50\n"
    )
