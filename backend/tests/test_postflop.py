from app.domain.action import Decision
from app.domain.evaluation import Correctness
from app.domain.leaks import LeakCategory
from app.domain.postflop import (
    grade_cbet,
    grade_vs_cbet,
    range_advantage,
    range_advantage_defender,
)
from app.domain.spot import (
    ActionType,
    GameConfig,
    Hero,
    HistoryAction,
    LegalAction,
    NodeContext,
    PlayerState,
    Position,
    Spot,
    Stakes,
    Street,
)
from app.domain.texture import classify

SMALL, BIG = 2.0, 4.5


def _cbet_spot(hole, board, hero_pos=Position.BTN, villain_pos=Position.BB):
    return Spot(
        game=GameConfig(stakes=Stakes(sb=0.5, bb=1.0), table_size=9),
        street=Street.FLOP,
        board=board,
        pot_bb=6.0,
        hero=Hero(position=hero_pos, hole_cards=hole, stack_bb=100),
        players=[
            PlayerState(position=hero_pos, stack_bb=100, is_hero=True),
            PlayerState(position=villain_pos, stack_bb=100),
        ],
        effective_stack_bb=100,
        spr=15.0,
        to_act=hero_pos,
        node_context=[NodeContext.CBET],
        facing=villain_pos,
        legal_actions=[
            LegalAction(action=ActionType.CHECK),
            LegalAction(action=ActionType.BET, min_bb=SMALL),
            LegalAction(action=ActionType.BET, min_bb=BIG),
        ],
        hero_range="22+, A2s+, KTs+, ATo+, KQo",
        villain_range="22-99, A2s+, KTs+, QJs, ATo+, KJo+",
    )


def test_range_advantage_high_dry_favors_hero():
    tex = classify(["As", "Kd", "2c"])
    assert range_advantage(NodeContext.CBET, Position.BTN, Position.BB, tex) == "hero"


def test_range_advantage_low_connected_favors_villain():
    tex = classify(["7h", "6h", "5c"])
    adv = range_advantage(NodeContext.CBET, Position.BTN, Position.BB, tex)
    assert adv in ("villain", "neutral")


def test_dry_range_adv_small_bet_is_optimal():
    spot = _cbet_spot(("Ah", "Qc"), ["As", "Kd", "2c"])  # top pair, dry, hero adv
    res = grade_cbet(
        spot, spot.hero_range, spot.villain_range, Decision(action=ActionType.BET, size_bb=SMALL)
    )
    assert res.correctness == Correctness.OPTIMAL
    assert res.best_action.action == ActionType.BET
    assert res.best_action.size_bb == SMALL
    assert res.leak_category == int(LeakCategory.FLOP_CBET)


def test_big_bet_oop_air_wet_is_worse():
    # CO opens, BTN calls -> hero (CO) is OOP; wet low board; pure air; barrel big.
    spot = _cbet_spot(
        ("As", "Kd"), ["9h", "8h", "6c"], hero_pos=Position.CO, villain_pos=Position.BTN
    )
    res = grade_cbet(
        spot, spot.hero_range, spot.villain_range, Decision(action=ActionType.BET, size_bb=BIG)
    )
    assert res.best_action.action == ActionType.CHECK
    assert res.correctness in (Correctness.MISTAKE, Correctness.BLUNDER)
    assert res.ev_loss_bb > POST_LOSS_FLOOR


def test_optimal_call_without_decision_has_no_chosen():
    spot = _cbet_spot(("Ah", "Qc"), ["As", "Kd", "2c"])
    res = grade_cbet(spot, spot.hero_range, spot.villain_range, None)
    assert res.chosen_eval is None
    assert res.best_action is not None
    assert {e.action for e in res.per_action} == {ActionType.CHECK, ActionType.BET}


def test_frequencies_normalized():
    spot = _cbet_spot(("Ah", "Qc"), ["As", "Kd", "2c"])
    res = grade_cbet(spot, spot.hero_range, spot.villain_range, None)
    total = sum(e.frequency for e in res.per_action)
    assert abs(total - 1.0) < 1e-6


POST_LOSS_FLOOR = 0.6


# --- Phase 2b: facing a c-bet (defense) ---
FLOP_POT = 6.0


def _vscbet_spot(hole, board, faced, hero=Position.BB, villain=Position.BTN):
    pot = FLOP_POT + faced
    return Spot(
        game=GameConfig(stakes=Stakes(sb=0.5, bb=1.0), table_size=9),
        street=Street.FLOP,
        board=board,
        pot_bb=pot,
        hero=Hero(position=hero, hole_cards=hole, stack_bb=100),
        players=[
            PlayerState(position=hero, stack_bb=100, is_hero=True),
            PlayerState(position=villain, stack_bb=100),
        ],
        effective_stack_bb=100,
        spr=round((100 - faced) / pot, 1),
        to_act=hero,
        node_context=[NodeContext.VS_CBET],
        facing=villain,
        action_history=[
            HistoryAction(street=Street.FLOP, position=villain, action=ActionType.BET, amount_bb=faced),
        ],
        legal_actions=[
            LegalAction(action=ActionType.FOLD),
            LegalAction(action=ActionType.CALL, min_bb=faced),
            LegalAction(action=ActionType.RAISE, min_bb=round(3 * faced, 1), max_bb=100),
        ],
        hero_range="22-99, ATs+, KJs+, QJs, AJo+, KQo",
        villain_range="22+, A2s+, K9s+, Q9s+, J9s+, T8s+, AJo+, KQo",
    )


def test_defender_range_advantage_anchors():
    low_wet = classify(["8h", "7h", "6c"])
    assert range_advantage_defender(Position.BTN, Position.BB, low_wet) == "defender"
    high_dry = classify(["As", "Kd", "2c"])
    assert range_advantage_defender(Position.BTN, Position.BB, high_dry) == "aggressor"
    # high & wet (the case the 2a reuse-trick could not reach) -> not aggressor
    high_wet = classify(["Kh", "Qh", "Jh"])
    assert range_advantage_defender(Position.BTN, Position.BB, high_wet) != "aggressor"


def test_strong_never_folds_vs_cbet():
    spot = _vscbet_spot(("As", "Ac"), ["Ah", "Kd", "2c"], faced=SMALL)  # top set
    res = grade_vs_cbet(spot, spot.hero_range, spot.villain_range, None)
    assert res.best_action.action in (ActionType.CALL, ActionType.RAISE)
    assert res.leak_category == int(LeakCategory.VS_CBET)
    fold = grade_vs_cbet(spot, spot.hero_range, spot.villain_range, Decision(action=ActionType.FOLD))
    assert fold.correctness in (Correctness.MISTAKE, Correctness.BLUNDER)


def test_air_high_dry_big_bet_folds():
    spot = _vscbet_spot(("7d", "2h"), ["As", "Kd", "9c"], faced=BIG)  # pure air, aggressor board
    res = grade_vs_cbet(spot, spot.hero_range, spot.villain_range, None)
    assert res.best_action.action == ActionType.FOLD


def test_draw_wet_defender_favored_continues():
    # flush draw on a low connected wet board where the defender has the edge
    spot = _vscbet_spot(("9h", "8h"), ["7h", "6h", "2c"], faced=SMALL)
    res = grade_vs_cbet(spot, spot.hero_range, spot.villain_range, None)
    assert res.best_action.action in (ActionType.CALL, ActionType.RAISE)
    assert res.best_action.action != ActionType.FOLD
    raise_eval = next(e for e in res.per_action if e.action == ActionType.RAISE)
    assert raise_eval.frequency > 0  # semibluff raise is a defensible mix


def test_bet_size_monotonic_defense():
    hole, board = ("Qd", "Jc"), ["Qh", "8d", "3s"]  # top pair (weak-ish made hand)
    small = grade_vs_cbet(_vscbet_spot(hole, board, SMALL), None, None, None)
    big = grade_vs_cbet(_vscbet_spot(hole, board, BIG), None, None, None)

    def freq(res, action):
        return next(e.frequency for e in res.per_action if e.action == action)

    assert freq(small, ActionType.CALL) >= freq(big, ActionType.CALL)
    assert freq(small, ActionType.FOLD) <= freq(big, ActionType.FOLD)


def test_vs_cbet_frequencies_normalized_and_raise_sized():
    spot = _vscbet_spot(("As", "Ac"), ["Ah", "7d", "2c"], faced=SMALL)
    res = grade_vs_cbet(spot, spot.hero_range, spot.villain_range, None)
    assert abs(sum(e.frequency for e in res.per_action) - 1.0) < 1e-6
    # a sized raise decision grades without a Decision validation error
    sized = grade_vs_cbet(
        spot, None, None, Decision(action=ActionType.RAISE, size_bb=3 * SMALL)
    )
    assert sized.correctness is not None
