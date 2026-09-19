"""simulate-6max S1 (T7): nine-max did not move, and six-max works.

Two jobs, in this order of importance.

1. **Nine-max is byte-identical.** `test_ninemax_parity_fixture_...` replays a
   fixed-seed capture taken on `origin/main` (commit `e791399`) BEFORE any file
   in this slice was edited — deals, the position map for every button seat, a
   button rotation, bot playouts, hero grades and settlements. The fixture is
   the old code's answer, so this test compares new against old, never new
   against itself. Its recipe block (`fixtures/ninemax_parity.json` → `recipe`)
   is the contract the harness below implements; a divergence is much more
   often a harness that drifted from the recipe than a genuine parity break, so
   read the recipe first.
2. **Six-max works and grades the same.** `test_six_and_nine_max_grade_...` is
   the slice's central bet: the six 6-max positions are the six LATEST 9-max
   positions, so players-behind is identical and a hero hand must grade to the
   same frequencies and EVs at both sizes. Presence of a grade is not enough —
   equality is the claim.

Spec: `docs/ai-dlc/specs/simulate-6max-s1.md` (rev 2). Golden paths imitated:
`tests/test_table.py` (rotation/parity shape) and
`tests/test_two_mode_simulate_gate.py` (slice-gate shape).

⚠️ No test in this file may be satisfied by editing a 9-max test elsewhere. If
an existing 9-max test needs editing, 9-max moved and the CHANGE is wrong.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import random

import pytest
from sqlmodel import Session, create_engine, select, text
from test_sim_session import _play_current_hand  # drives the hero to hand end

from app.db.migrate import run_migrations
from app.db.models import SimHand, SimSeat, SimSession
from app.domain.action import Decision
from app.domain.evaluation import EvaluationResult
from app.domain.personas import load_persona_packs
from app.domain.providers import get_provider
from app.domain.spot import RANKS, SUITS, ActionType, NodeContext, Position, Spot
from app.domain.table.deck import DealtHand, deal_hand, positions_for_button
from app.domain.table.engine import HandState, apply, legal_actions, settle, start_hand
from app.domain.table.grade_map import map_decision_point
from app.domain.table.play import LINEUP, LINEUP_6MAX, advance_to_hero, assign_lineup
from app.domain.table.range_estimate import _replay_contexts
from app.services.sim_session import (
    HERO_SEAT,
    _blind_check_seats,
    _public_history,
    _sim_signature,
    create_session,
    deal_next_hand,
    restore_session,
)


@pytest.fixture
def db(tmp_path):
    url = f"sqlite:///{tmp_path / 'simulate_6max.db'}"
    run_migrations(url)
    engine = create_engine(url, connect_args={"check_same_thread": False})
    with Session(engine) as s:
        yield s


# ============================================================ 1. the fixture
#
# A faithful re-implementation of the T0 generator, which lives OUTSIDE the
# repository (scratch hygiene) — so the recipe block in the fixture, not a
# committed script, is what this harness has to match.

_FIXTURE = json.loads(
    (pathlib.Path(__file__).parent / "fixtures" / "ninemax_parity.json").read_text()
)
_HERO_SCRIPTS: list[list[str]] = _FIXTURE["recipe"]["hero_scripts"]


def _event_row(e) -> dict:
    return {
        "seat": e.seat,
        "position": e.position.value,
        "action": e.action.value,
        "amount_bb": e.amount_bb,
        "street": e.street.value,
        "all_in": e.all_in,
    }


def _history_row(h) -> dict:
    return {
        "street": h.street.value,
        "position": h.position.value,
        "action": h.action.value,
        "amount_bb": h.amount_bb,
    }


def _spot_row(spot: Spot) -> dict:
    return {
        "table_size": spot.game.table_size,
        "street": spot.street.value,
        "board": list(spot.board),
        "pot_bb": spot.pot_bb,
        "hero_position": spot.hero.position.value,
        "hero_hole_cards": list(spot.hero.hole_cards),
        "effective_stack_bb": spot.effective_stack_bb,
        "to_act": spot.to_act.value,
        "node_context": [n.value for n in spot.node_context],
        "facing": spot.facing.value if spot.facing is not None else None,
        "players": [{"position": p.position.value, "status": p.status.value} for p in spot.players],
        "action_history": [_history_row(h) for h in spot.action_history],
        "legal_actions": [
            {"action": la.action.value, "min_bb": la.min_bb, "max_bb": la.max_bb}
            for la in spot.legal_actions
        ],
    }


def _grade_row(result: EvaluationResult) -> dict:
    return {
        "per_action": [
            {
                "action": a.action.value,
                "size_bb": a.size_bb,
                "frequency": a.frequency,
                "ev_bb": a.ev_bb,
            }
            for a in result.per_action
        ],
        "best_action": result.best_action.action.value,
        "chosen": (
            None
            if result.chosen_eval is None
            else {"frequency": result.chosen_eval.frequency, "ev_bb": result.chosen_eval.ev_bb}
        ),
        "ev_loss_bb": result.ev_loss_bb,
        "correctness": result.correctness.value if result.correctness else None,
        "sizing_correctness": (
            result.sizing_correctness.value if result.sizing_correctness else None
        ),
        "coverage": result.coverage.value,
        "provider": result.provider.value,
        "leak_category": result.leak_category,
        "is_mixed": result.is_mixed,
        "rationale_tags": list(result.rationale_tags),
    }


def _scripted_hero_decision(state: HandState, ordinal: int, index: int) -> Decision:
    """The recipe's hero script: the first legal action named by
    `hero_scripts[(ordinal + index) % 4]`, sized at `min_bb` when the action
    takes a size. Three of the four scripts stay in the hand, so the capture
    reaches postflop instead of folding out preflop."""
    by_name = {la.action.value: la for la in legal_actions(state)}
    for name in _HERO_SCRIPTS[(ordinal + index) % len(_HERO_SCRIPTS)]:
        la = by_name.get(name)
        if la is None:
            continue
        if la.action in (ActionType.BET, ActionType.RAISE):
            return Decision(action=la.action, size_bb=la.min_bb)
        return Decision(action=la.action)
    raise AssertionError("no legal action matched the hero script")


async def _replay_captured_hand(seed: int, ordinal: int, provider) -> dict:
    packs = load_persona_packs()
    lineup = assign_lineup(random.Random(seed))
    seat_personas = {seat: packs[vt] for seat, vt in lineup.items()}
    dealt = deal_hand(random.Random(seed))
    button_seat = seed % 9
    stack = _FIXTURE["recipe"]["stack_bb"]
    state = start_hand(dealt, button_seat=button_seat, stacks_bb=[stack] * 9)
    state, events = advance_to_hero(state, seat_personas, HERO_SEAT, random.Random(seed ^ 0xABCDEF))
    all_events = [_event_row(e) for e in events]
    decisions: list[dict] = []
    index = 0
    while not state.hand_over and state.to_act_seat == HERO_SEAT:
        spot = map_decision_point(state, HERO_SEAT)
        decision = _scripted_hero_decision(state, ordinal, index)
        row: dict = {
            "index": index,
            "street": state.street.value,
            "hero_position": state.seats[HERO_SEAT].position.value,
            "decision": {"action": decision.action.value, "size_bb": decision.size_bb},
            "spot": None if spot is None else _spot_row(spot),
            "grade": None,
        }
        if spot is not None:
            row["grade"] = _grade_row(await provider.evaluate(spot, decision))
        decisions.append(row)
        state = apply(state, decision)
        state, events = advance_to_hero(
            state, seat_personas, HERO_SEAT, random.Random(seed ^ 0xABCDEF ^ (index + 1))
        )
        all_events.extend(_event_row(e) for e in events)
        index += 1
    settlement = settle(state) if state.hand_over else None
    return {
        "seed": seed,
        "button_seat": button_seat,
        "lineup": {str(s): vt.value for s, vt in sorted(lineup.items())},
        "bot_events": all_events,
        "hero_decisions": decisions,
        "final": {
            "street": state.street.value,
            "board": list(state.board),
            "hand_over": state.hand_over,
            "pot_bb": round(sum(s.invested_total_bb for s in state.seats), 2),
            "seats": [
                {
                    "seat": s.seat,
                    "position": s.position.value,
                    "stack_bb": s.stack_bb,
                    "invested_total_bb": s.invested_total_bb,
                    "status": s.status.value,
                }
                for s in state.seats
            ],
            "action_history": [_history_row(h) for h in state.action_history],
        },
        "settlement": (
            None
            if settlement is None
            else {
                "pots": [
                    {"amount_bb": p.amount_bb, "eligible_seats": list(p.eligible_seats)}
                    for p in settlement.pots
                ],
                "winners_by_pot": [list(w) for w in settlement.winners_by_pot],
                "deltas": [d.delta_bb for d in settlement.deltas],
                "showdown_seats": list(settlement.showdown_seats),
            }
        ),
    }


def test_ninemax_parity_fixture_from_origin_main_is_reproduced_exactly():
    recipe = _FIXTURE["recipe"]

    # A truncated fixture must not pass by having nothing to compare.
    assert len(_FIXTURE["hands"]) == len(recipe["hand_seeds"]) == 20
    assert [vt.value for vt in LINEUP] == recipe["ninemax_lineup"]

    for seed in recipe["deal_seeds"]:
        dealt = deal_hand(random.Random(seed))
        captured = _FIXTURE["deals"][str(seed)]
        assert [list(pair) for pair in dealt.hole_cards] == captured["hole_cards"], seed
        assert dealt.board == captured["board"], seed

    for button_seat in range(9):
        got = [p.value for p in positions_for_button(button_seat)]
        assert got == _FIXTURE["positions_for_button"][str(button_seat)], button_seat

    rotation = []
    button = recipe["rotation_start"]
    for _ in range(recipe["rotation_steps"]):
        rotation.append(button)
        button = (button + 1) % 9
    assert rotation == _FIXTURE["button_rotation"]

    provider = get_provider()
    for ordinal, seed in enumerate(recipe["hand_seeds"]):
        got = asyncio.run(_replay_captured_hand(seed, ordinal, provider))
        assert got == _FIXTURE["hands"][ordinal], f"hand seed {seed} (ordinal {ordinal}) diverged"


# ====================================== 2. six-max grades exactly like nine-max

# Hero is always seat 0. The button seat is chosen so the hero sits at the named
# position at BOTH table sizes, and the villain who opens sits where its
# position says it does — that is the whole trick: the six 6-max positions are
# the six LATEST 9-max positions, so LJ/HJ/CO/BTN/SB/BB have identical
# players-behind at both sizes.
# (name, button at 9, button at 6, the position that opens — None ⇒ folded to hero)
# The five RFI rows plus the blind defence cover all six 6-max positions.
_EQUAL_GRADE_NODES = [
    ("rfi_from_lj", 3, 3, None),
    ("rfi_from_hj", 2, 2, None),
    ("rfi_from_co", 1, 1, None),
    ("rfi_from_btn", 0, 0, None),
    ("rfi_from_sb", 8, 5, None),
    ("btn_faces_a_co_open", 0, 0, Position.CO),
    ("sb_faces_a_co_open", 8, 5, Position.CO),
    ("bb_defends_a_co_open", 7, 4, Position.CO),
]

_EQUAL_GRADE_HANDS = [("As", "Ks"), ("7c", "6c"), ("Qd", "Jh"), ("Th", "Td"), ("2h", "3d")]

_OPEN_TO_BB = 2.5


def _dealt_with_hero_holding(table_size: int, hero_hole: tuple[str, str]) -> DealtHand:
    """A deal the hero's cards are pinned in. Villain cards come off a fixed
    remainder of the deck in seat order, so seats 1..5 hold the same cards at
    both table sizes and only the three seats that do not exist at six differ."""
    board = ["2c", "7d", "9h", "Jc", "4s"]
    used = set(hero_hole) | set(board)
    pool = [r + s for r in RANKS for s in SUITS if r + s not in used]
    rest = iter(pool)
    holes = [hero_hole] + [(next(rest), next(rest)) for _ in range(table_size - 1)]
    return DealtHand(hole_cards=holes, board=board)


def _drive_to_hero(state: HandState, opener: Position | None) -> HandState:
    """Fold every villain to the hero, except `opener`, which raises to 2.5bb."""
    while state.to_act_seat is not None and state.to_act_seat != HERO_SEAT:
        seat = state.seats[state.to_act_seat]
        if opener is not None and seat.position is opener:
            state = apply(state, Decision(action=ActionType.RAISE, size_bb=_OPEN_TO_BB))
        else:
            state = apply(state, Decision(action=ActionType.FOLD))
    return state


def _hero_node(table_size: int, button_seat: int, hero_hole, opener) -> HandState:
    state = start_hand(
        _dealt_with_hero_holding(table_size, hero_hole),
        button_seat=button_seat,
        stacks_bb=[100.0] * table_size,
    )
    return _drive_to_hero(state, opener)


@pytest.mark.parametrize(("name", "button9", "button6", "opener"), _EQUAL_GRADE_NODES)
@pytest.mark.parametrize("hero_hole", _EQUAL_GRADE_HANDS)
def test_six_and_nine_max_grade_the_same_hero_hand_identically(
    name, button9, button6, opener, hero_hole
):
    """THE SLICE'S CENTRAL BET. Same hole cards, same hero position, same node
    ⇒ same frequency and same EV for every action, at six seats and at nine."""
    state9 = _hero_node(9, button9, hero_hole, opener)
    state6 = _hero_node(6, button6, hero_hole, opener)

    assert len(state9.seats) == 9
    assert len(state6.seats) == 6
    assert state9.seats[HERO_SEAT].position is state6.seats[HERO_SEAT].position
    assert state9.seats[HERO_SEAT].hole_cards == state6.seats[HERO_SEAT].hole_cards

    spot9 = map_decision_point(state9, HERO_SEAT)
    spot6 = map_decision_point(state6, HERO_SEAT)
    assert spot9 is not None and spot6 is not None, f"{name} must be gradeable at both sizes"

    # The two spots really are different-sized tables — otherwise the equality
    # below would be comparing a 9-max spot to another 9-max spot.
    assert spot9.game.table_size == 9
    assert spot6.game.table_size == 6
    assert spot9.node_context == spot6.node_context
    assert spot9.hero.position is spot6.hero.position

    provider = get_provider()
    decision = Decision(action=ActionType.FOLD)
    grade9 = _grade_row(asyncio.run(provider.evaluate(spot9, decision)))
    grade6 = _grade_row(asyncio.run(provider.evaluate(spot6, decision)))
    assert grade6 == grade9, f"{name} graded differently at six seats"


# ================================== 3. a six-max session deals, seeds, rotates


def test_six_max_session_deals_six_hands_and_seats_six(db):
    view = create_session(db, table_size=6)
    assert view.table_size == 6
    assert len(view.hand.seats) == 6
    rows = db.exec(select(SimSeat).where(SimSeat.session_id == view.session_id)).all()
    assert sorted(r.seat_index for r in rows) == [0, 1, 2, 3, 4, 5]
    assert len(deal_hand(random.Random(42), 6).hole_cards) == 6
    assert len(deal_hand(random.Random(42), 6).board) == 5


def test_six_max_deal_comes_off_a_six_handed_deck(db):
    """THE SILENT ONE. `deal_hand(rng)` left at nine pops eighteen hole cards
    before the board at a six-seat table, so the board comes off a different
    deck offset — no crash, no illegal action, and no other test notices.

    Caught by re-dealing from the seed the service persisted: the hand it
    actually stored must be the six-handed deal of that seed, and the
    nine-handed deal of the same seed must differ."""
    view = create_session(db, table_size=6)
    hand = db.exec(select(SimHand).where(SimHand.session_id == view.session_id)).one()
    state = HandState.model_validate_json(hand.state_json)
    seed = int(hand.rng_seed)

    six_handed = deal_hand(random.Random(seed), 6)
    assert [s.hole_cards for s in state.seats] == six_handed.hole_cards
    assert state.full_board == six_handed.board
    # Both boards come off the same shuffled deck at different offsets, so they
    # can never coincide — this is a real discriminator, not a probable one.
    assert deal_hand(random.Random(seed), 9).board != six_handed.board


def test_six_max_button_seeds_inside_zero_to_five(db):
    # `secrets.randbelow(9)` lands out of range about a third of the time at six
    # seats, and the bad value persists onto the row and out over the wire.
    seeded = {create_session(db, table_size=6).hand.button_seat for _ in range(40)}
    assert seeded <= {0, 1, 2, 3, 4, 5}


def test_six_max_button_rotates_through_six_seats_only(db):
    view = create_session(db, table_size=6)
    buttons = [view.hand.button_seat]
    for _ in range(8):
        view = _play_current_hand(db, view, fold_if_possible=True)
        view = deal_next_hand(db, view.session_id)
        buttons.append(view.hand.button_seat)
    assert set(buttons) == {0, 1, 2, 3, 4, 5}
    for before, after in zip(buttons, buttons[1:], strict=False):
        assert after == (before + 1) % 6


def test_six_max_posts_blinds_correctly_at_every_button_position():
    """Imitates `test_table.py`'s every-seat loop: walk all six buttons and
    assert the two posts land on the seats one and two past the button."""
    for button_seat in range(6):
        state = start_hand(
            _dealt_with_hero_holding(6, ("As", "Ks")),
            button_seat=button_seat,
            stacks_bb=[100.0] * 6,
        )
        sb_seat = (button_seat + 1) % 6
        bb_seat = (button_seat + 2) % 6
        assert state.seats[button_seat].position is Position.BTN
        assert state.seats[sb_seat].position is Position.SB
        assert state.seats[bb_seat].position is Position.BB
        assert state.seats[sb_seat].invested_street_bb == 0.5
        assert state.seats[bb_seat].invested_street_bb == 1.0
        posts = [h for h in state.action_history if h.action is ActionType.POST]
        assert [(h.position, h.amount_bb) for h in posts] == [
            (Position.SB, 0.5),
            (Position.BB, 1.0),
        ]
        # Three past the button opens — LJ at six seats, not UTG.
        assert state.to_act_seat == (button_seat + 3) % 6
        assert state.seats[state.to_act_seat].position is Position.LJ


def test_six_max_rotation_covers_six_positions_and_exactly_one_button():
    """`test_table.py`'s 9-max invariant, generalised: every button seat yields
    six distinct positions, exactly one BTN, and never a UTG seat."""
    six_max = {Position.BTN, Position.SB, Position.BB, Position.LJ, Position.HJ, Position.CO}
    for button_seat in range(6):
        result = positions_for_button(button_seat, 6)
        assert len(result) == 6
        assert set(result) == six_max
        assert sum(1 for p in result if p is Position.BTN) == 1
        assert result[button_seat] is Position.BTN


# ================================================== 4. the fixed 6-max roster


def test_six_max_seats_nit_tag_tag_lag_calling_station(db):
    """Owner decision D2. TWO TAGs is deliberate, not a typo — regulars are the
    most common seat at real 6-max. Which five is fixed; only seating shuffles."""
    expected = sorted(["nit", "tag", "tag", "lag", "calling_station"])
    assert sorted(vt.value for vt in LINEUP_6MAX) == expected

    seatings = set()
    for _ in range(20):
        view = create_session(db, table_size=6)
        rows = db.exec(select(SimSeat).where(SimSeat.session_id == view.session_id)).all()
        by_index = {r.seat_index: r for r in rows}
        assert by_index[HERO_SEAT].is_hero and by_index[HERO_SEAT].persona_type is None
        bots = [by_index[i].persona_type for i in range(1, 6)]
        assert sorted(bots) == expected
        seatings.add(tuple(bots))
    assert len(seatings) > 1, "the five are seated by a shuffle, not a fixed order"


# ============================================ 5. restore mid-hand at both sizes


@pytest.mark.parametrize("table_size", [6, 9])
def test_restore_mid_hand_reads_back_the_sessions_table_size(db, table_size):
    view = create_session(db, table_size=table_size)
    restored = restore_session(db, view.session_id)
    assert restored is not None
    assert restored.table_size == table_size
    assert len(restored.hand.seats) == table_size
    assert restored.hand.board == view.hand.board
    assert restored.hand.hero.hole_cards == view.hand.hero.hole_cards


def test_a_session_row_written_before_migration_0016_restores_as_nine_max(db):
    """Migration 0016 is additive-nullable with a DB-side default, so a row
    written before it has no value of its own. It must read back as nine — the
    only size that existed when it was written."""
    view = create_session(db, table_size=9)
    db.exec(
        text("UPDATE sim_session SET table_size = NULL WHERE id = :id").bindparams(
            id=view.session_id
        )
    )
    db.commit()
    db.expire_all()
    assert db.get(SimSession, view.session_id).table_size is None

    restored = restore_session(db, view.session_id)
    assert restored is not None
    assert restored.table_size == 9
    assert len(restored.hand.seats) == 9


# ================================================= 6. the Challenge blind check


def test_six_max_blind_check_names_only_seats_that_exist(db):
    for _ in range(25):
        view = create_session(db, mode="challenge", table_size=6)
        seats = _blind_check_seats(view.session_id, 6)
        assert len(set(seats)) == 3
        assert set(seats) <= {1, 2, 3, 4, 5}
        assert HERO_SEAT not in seats


def test_six_max_blind_check_discloses_the_roster_actually_seated(db):
    """The card's fairness argument is the disclosed lineup. At six seats the
    seats it can name are drawn from LINEUP_6MAX — no maniac, no passive fish."""
    view = create_session(db, mode="challenge", table_size=6)
    rows = db.exec(select(SimSeat).where(SimSeat.session_id == view.session_id)).all()
    personas = {r.seat_index: r.persona_type for r in rows if not r.is_hero}
    assert set(personas) == {1, 2, 3, 4, 5}
    assert set(personas.values()) <= {vt.value for vt in LINEUP_6MAX}
    for seat in _blind_check_seats(view.session_id, 6):
        assert personas[seat] in {vt.value for vt in LINEUP_6MAX}


# ===================================== 7. the villain-range estimator counts six


@pytest.mark.parametrize(("table_size", "expected_opponents"), [(6, 5), (9, 8)])
def test_villain_range_estimator_counts_opponents_out_of_the_real_table(
    table_size, expected_opponents
):
    """Left at nine, a 6-max hand would count three opponents never dealt in and
    every posterior would be wrong WITH NO ERROR RAISED. Silent wrongness is the
    failure this pins."""
    state = start_hand(
        _dealt_with_hero_holding(table_size, ("As", "Ks")),
        button_seat=0,
        stacks_bb=[100.0] * table_size,
    )
    opener_seat = state.to_act_seat
    state = apply(state, Decision(action=ActionType.RAISE, size_bb=_OPEN_TO_BB))

    history = _public_history(state)
    assert len(history.starting_stacks_bb) == table_size

    contexts = _replay_contexts(history, opener_seat, len(history.actions))
    assert [c.opponents for c in contexts] == [expected_opponents]


# ================================================ 8. the D1 signature assertion


def test_sim_signature_separates_six_max_from_nine_max(db):
    """Owner decision D1, asserted on `_sim_signature` — the key Simulate
    actually writes. `spot_signature()` is frozen, Simulate never calls it, and
    asserting on it would pass with no code changed and prove nothing.

    Refined by the owner on 2026-09-19: only a NON-nine size carries the seat
    count, so nine-max keeps its original `sim:rfi:LJ` shape and the history the
    owner has been building since before 6-max existed is not split at the
    change date. The asymmetry is the point, not an oversight.

    The node part is `NodeContext.RFI.value`, which is upper-case — the spec's
    illustrative `sim:rfi:LJ` is prose, the key the service writes is
    `sim:RFI:LJ`."""
    spots = {}
    for table_size, button in ((9, 3), (6, 3)):
        state = _hero_node(table_size, button, ("As", "Ks"), None)
        spot = map_decision_point(state, HERO_SEAT)
        assert spot is not None
        spots[table_size] = spot

    assert spots[9].hero.position is Position.LJ
    assert spots[6].hero.position is Position.LJ
    assert spots[9].node_context[0] is NodeContext.RFI

    assert _sim_signature(spots[9], 9) == "sim:RFI:LJ"
    assert _sim_signature(spots[6], 6) == "sim:6:RFI:LJ"
    assert _sim_signature(spots[6], 6) != _sim_signature(spots[9], 9)


# ============================== 9. a RECORDED GAP, not a passing feature


def test_recorded_gap_six_max_limped_pot_canonicalises_onto_utg_which_has_no_seat():
    """⚠️ THIS DOCUMENTS A DEFECT THE SLICE DELIBERATELY DID NOT FIX.

    `scenarios.py:73` sets `_LIMP_SEATS = [UTG, LJ, HJ, CO]` and `:215` slices
    it by limper COUNT, so the canonical shape seats the first limper at UTG —
    a position that does not exist at six seats. The real limper below is the
    CO; the graded spot says UTG limped.

    Spec §6 keeps this: the grading lookup keys on node type and hero position,
    never on which seat limped, so the verdict itself is unaffected. What IS
    affected is anything that reads the returned spot's action history as a
    picture of the table — the felt, a replay, a future coach narration. When
    that becomes a problem, this test is the record of where it comes from, and
    changing it to assert the CO is the fix, not a test edit."""
    # Button 4 at six seats puts the hero (seat 0) in the big blind: seat 3 = CO.
    state = start_hand(
        _dealt_with_hero_holding(6, ("As", "Ks")),
        button_seat=4,
        stacks_bb=[100.0] * 6,
    )
    assert state.seats[HERO_SEAT].position is Position.BB
    assert state.seats[3].position is Position.CO
    while state.to_act_seat is not None and state.to_act_seat != HERO_SEAT:
        if state.to_act_seat == 3:
            state = apply(state, Decision(action=ActionType.CALL))
        else:
            state = apply(state, Decision(action=ActionType.FOLD))

    seated = {s.position for s in state.seats}
    assert Position.UTG not in seated, "six seats never include UTG"
    limps = [h for h in state.action_history if h.action is ActionType.CALL]
    assert [h.position for h in limps] == [Position.CO], "the CO is who actually limped"

    spot = map_decision_point(state, HERO_SEAT)
    assert spot is not None
    assert spot.node_context == [NodeContext.VS_LIMPERS]
    canonical_limps = [h for h in spot.action_history if h.action is ActionType.CALL]
    # The gap: the graded spot attributes the limp to a seat that is not at the
    # table. Recorded, not fixed.
    assert [h.position for h in canonical_limps] == [Position.UTG]
