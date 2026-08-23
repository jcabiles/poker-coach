"""Villain range estimator (villain-range V1) — posterior math, replay
equivalence, NO-PEEK, dead-card granularity, through_action, perf.

Spec: docs/ai-dlc/specs/simulate-villain-range.md.
"""

from __future__ import annotations

import math
import random
import time

import pytest

from app.domain import personas_postflop
from app.domain.action import Decision
from app.domain.archetypes import VillainType
from app.domain.content.notation import parse_range
from app.domain.personas import load_persona_packs
from app.domain.personas_postflop import (
    DrawCategory,
    StrengthBucket,
    _price_exponent,
    _price_factor,
    sample_postflop_decision,
    size_bucket,
    strength_bucket,
)
from app.domain.spot import (
    RANKS,
    SUITS,
    ActionType,
    LegalAction,
    PlayerStatus,
    Position,
    Street,
)
from app.domain.table.deck import DealtHand, deal_hand, positions_for_button
from app.domain.table.engine import HandState, apply, legal_actions, start_hand
from app.domain.table.play import (
    _preflop_facing,
    _preflop_opener,
    assign_lineup,
    bot_decision,
)
from app.domain.table.postflop_context import aggressor_barrel_run
from app.domain.table.range_estimate import (
    PublicAction,
    PublicActionHistory,
    _legal_from_ctx,
    _postflop_action_dist,
    _replay_contexts,
    estimate_range,
)
from app.domain.table.sizing import last_aggressor_position, pot_before_current_aggression

_DECK = [r + s for r in RANKS for s in SUITS]
_STACKS = (100.0,) * 9
_RAISE_NAMES = ("raise", "3bet", "4bet", "5bet_shove")


@pytest.fixture(scope="module")
def packs():
    return load_persona_packs()


# ------------------------------------------------------------- helpers


def _project(state: HandState, starting_stacks=_STACKS) -> PublicActionHistory:
    """Test-side projection of a real HandState — reads ONLY public fields."""
    pos2seat = {s.position: s.seat for s in state.seats}
    return PublicActionHistory(
        button_seat=state.button_seat,
        starting_stacks_bb=tuple(starting_stacks),
        board=tuple(state.board),
        actions=tuple(
            PublicAction(
                seat=pos2seat[h.position],
                position=h.position,
                street=h.street,
                action=h.action,
                amount_bb=h.amount_bb,
            )
            for h in state.action_history
        ),
    )


def _hand_history(button: int, actions, board=()) -> PublicActionHistory:
    """Hand-built projection: blinds posted, then (seat, street, action, amount
    INCREMENT) tuples."""
    pos = positions_for_button(button)
    sb, bb = (button + 1) % 9, (button + 2) % 9
    acts = [
        PublicAction(
            seat=sb, position=pos[sb], street=Street.PREFLOP, action=ActionType.POST, amount_bb=0.5
        ),
        PublicAction(
            seat=bb, position=pos[bb], street=Street.PREFLOP, action=ActionType.POST, amount_bb=1.0
        ),
    ]
    for seat, street, action, amt in actions:
        acts.append(
            PublicAction(seat=seat, position=pos[seat], street=street, action=action, amount_bb=amt)
        )
    return PublicActionHistory(
        button_seat=button, starting_stacks_bb=_STACKS, board=tuple(board), actions=tuple(acts)
    )


def _dealt_fixed(villain_cards, board, villain_seat=3) -> DealtHand:
    """Deterministic deal: every non-villain seat gets the SAME cards across
    calls (pool excludes both villain variants + the board)."""
    reserved = set(board) | {"As", "Ad", "7c", "2d"}
    pool = [c for c in _DECK if c not in reserved]
    hole, k = [], 0
    for seat in range(9):
        if seat == villain_seat:
            hole.append(tuple(villain_cards))
        else:
            hole.append((pool[k], pool[k + 1]))
            k += 2
    return DealtHand(hole_cards=hole, board=list(board))


def _script(state: HandState, moves) -> HandState:
    """Apply (expected_seat, Decision) moves, asserting turn order."""
    for seat, decision in moves:
        assert state.to_act_seat == seat, f"expected seat {seat}, got {state.to_act_seat}"
        state = apply(state, decision)
    return state


def _raise_classes(pack, facing: str, position: Position) -> set[str]:
    """Classes with positive raise-family mass at the node — hand-computed
    from the pack json (first-match-wins mix semantics)."""
    for node in pack.preflop:
        if node.facing != facing:
            continue
        if node.positions is not None and position not in node.positions:
            continue
        covered: set[str] = set()
        out: set[str] = set()
        for mix in node.mixes:
            combos = parse_range(mix.combos) - covered
            covered |= combos
            if any(n in _RAISE_NAMES and w > 0 for n, w in mix.weights.items()):
                out |= combos
        return out
    raise AssertionError(f"no node for {facing}/{position}")


def _positive(res) -> set[str]:
    return {c for c, w in res.class_weights.items() if w > 0}


_FOLD = Decision(action=ActionType.FOLD)
_CALL = Decision(action=ActionType.CALL)
_CHECK = Decision(action=ActionType.CHECK)


def _raise_to(size: float) -> Decision:
    return Decision(action=ActionType.RAISE, size_bb=size)


def _bet(size: float) -> Decision:
    return Decision(action=ActionType.BET, size_bb=size)


# ------------------------------------------------ preflop pack posterior


def test_btn_open_matches_rfi_mix(packs):
    tag = packs[VillainType.TAG]
    # button=0: SB=1, BB=2, UTG=3 acts first; folds to the BTN who opens.
    hist = _hand_history(
        0,
        [(s, Street.PREFLOP, ActionType.FOLD, 0.0) for s in range(3, 9)]
        + [(0, Street.PREFLOP, ActionType.RAISE, 3.0)],
    )
    res = estimate_range(tag, hist, seat=0)
    assert res.exact is True
    assert _positive(res) == _raise_classes(tag, "unopened", Position.BTN)
    assert sum(res.class_weights.values()) == pytest.approx(1.0)


def _four_bet_history():
    # button=0: UTG (seat 3) opens 3bb, BTN 3-bets to 9, UTG 4-bets to 21.
    # Amounts are INCREMENTS: UTG's 4-bet adds 18 on top of the 3 invested.
    return _hand_history(
        0,
        [(3, Street.PREFLOP, ActionType.RAISE, 3.0)]
        + [(s, Street.PREFLOP, ActionType.FOLD, 0.0) for s in range(4, 9)]
        + [
            (0, Street.PREFLOP, ActionType.RAISE, 9.0),
            (1, Street.PREFLOP, ActionType.FOLD, 0.0),
            (2, Street.PREFLOP, ActionType.FOLD, 0.0),
            (3, Street.PREFLOP, ActionType.RAISE, 18.0),
        ],
    )


def test_four_bet_line_strict_subset_and_hand_computed_posterior(packs):
    tag = packs[VillainType.TAG]
    hist = _four_bet_history()
    open_res = estimate_range(tag, hist, seat=3, through_action=3)  # posts + open only
    four_res = estimate_range(tag, hist, seat=3)
    assert open_res.exact is True and four_res.exact is True
    open_set, four_set = _positive(open_res), _positive(four_res)
    assert four_set < open_set  # strict subset
    # tag.json: UTG open ∩ vs_3bet 4bet-mass. The vs_3bet 4-bet mass is
    # {AA,KK @1.0} ∪ {QQ,AKs @0.5} ∪ {AKo @0.35} ∪ {A5s,A4s @0.35} (R10-3BET,
    # 2026-07-31: QQ and AKo JOINED it — dossier 4-bet 10-18% of opportunities,
    # 1.5-3.0% of all hands — and AQo LEFT it, its 4bet 0.4 tier struck, now
    # calling 0.2 in the bottom continue tier). The intersection is decided by
    # the UTG OPEN, and that is what moved next:
    #
    # RE-PINNED TWICE, both times because the UTG OPEN moved and never because
    # the range was carved to fit the pin (repo law: update the pin).
    #  · N-TAGCOMP (2026-07-31) widened the UTG suited-ace row to the full
    #    `A2s+` at weight 1.0, which made A5s AND A4s reachable: they open, get
    #    3-bet, and enter the 4-bet mix through the wheel-ace bluff tier.
    #  · N-TAGWIDTH (2026-07-31) takes them back OUT. Its UTG recomposition
    #    retires the suited tail to pay for the restored ATo/KQo, and because
    #    the emitter's rows are top-anchored prefixes, retiring A8s-A6s
    #    necessarily retires A5s-A2s with them — the UTG open is now `A8s+`
    #    (A7s at 0.5). With zero open weight, the wheel aces cannot survive to
    #    a 4-bet no matter what vs_3bet authors, exactly as before N-TAGCOMP.
    # `vs_3bet` is byte-identical across both slices: its 4-bet mass is still
    # {AA,KK @1.0} ∪ {QQ,AKs @0.5} ∪ {AKo @0.35} ∪ {A5s,A4s @0.35}; only the
    # intersection with the open moved.
    assert four_set == {"AA", "KK", "QQ", "AKs", "AKo"}
    # Hand-computed posterior ratios: AA = 6 combos × (1.0 × 1.0);
    # AKo = 12 combos × (1.0 × 0.35) → AA/AKo = 6/4.2 = 10/7;
    # QQ = 6 combos × (1.0 × 0.5) → AA/QQ = 6/3 = 2.
    assert four_res.class_weights["AA"] / four_res.class_weights["AKo"] == pytest.approx(10 / 7)
    assert four_res.class_weights["AA"] / four_res.class_weights["QQ"] == pytest.approx(2.0)


def test_n3bstrata_estimator_routes_opener_table_for_stratified_packs(packs):
    """N-3BSTRATA parity (triple-review convergent MED): the estimator's replay
    must route the OPENER-role vs_3bet table for a stratified pack when the
    replayed seat made the hand's first raise. Discriminator: lag's OPENER
    table 4-bets TT at 0.15 while its COLD table gives TT no 4-bet mass at
    all — so TT appears in the open→3-bet→4-bet posterior iff the opener
    table was selected."""
    lag = packs[VillainType.LAG]
    hist = _four_bet_history()
    ctxs = _replay_contexts(hist, 3, len(hist.actions))
    pf = [c for c in ctxs if c.street is Street.PREFLOP]
    # At the OPEN decision no raise exists yet (flag False); at the 4-bet
    # decision seat 3 IS the hand's first raiser (flag True).
    assert [c.is_opener for c in pf] == [False, True]
    assert pf[1].facing == "vs_3bet"
    four_res = estimate_range(lag, hist, seat=3)
    assert four_res.exact is True
    four_set = _positive(four_res)
    assert "TT" in four_set, (
        "TT missing from lag's 4-bet posterior — the estimator read the COLD "
        "vs_3bet table for an opener-stratum replay"
    )
    # And the non-opener 3-bettor (seat 0, BTN cold 3-bet) must NOT be opener.
    btn_pf = [c for c in _replay_contexts(hist, 0, len(hist.actions)) if c.street is Street.PREFLOP]
    assert [c.is_opener for c in btn_pf] == [False]


# ------------------------------------------------------------- NO-PEEK


def _no_peek_state(villain_cards) -> HandState:
    dealt = _dealt_fixed(villain_cards, ["Kh", "7d", "2c", "9s", "3h"])
    state = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    moves = [(3, _raise_to(3.0))]
    moves += [(s, _FOLD) for s in (4, 5, 6, 7, 8, 0, 1)]
    moves += [(2, _CALL)]
    moves += [(2, _CHECK), (3, _bet(3.0)), (2, _CALL)]  # flop
    moves += [(2, _CHECK), (3, _bet(6.0))]  # turn (mid-street stop)
    return _script(state, moves)


def test_no_peek_identical_weights_across_villain_cards(packs):
    tag = packs[VillainType.TAG]
    res_a = estimate_range(tag, _project(_no_peek_state(("As", "Ad"))), seat=3)
    res_b = estimate_range(tag, _project(_no_peek_state(("7c", "2d"))), seat=3)
    assert res_a.exact is False
    assert res_a.class_weights == res_b.class_weights
    assert res_a.combo_weights == res_b.combo_weights


# --------------------------------------------- replay reconstruction


def _true_ctx(state: HandState, seat: int):
    """Ground-truth decision context, read the way play.bot_decision reads it."""
    legal = legal_actions(state)
    kinds = frozenset(la.action for la in legal)
    # ESTIM-PRICE ground truth: the two faced-price inputs, taken from the same
    # two production sources play.bot_decision takes them from.
    to_call = next(
        (la.min_bb or 0.0 for la in legal if la.action is ActionType.CALL), 0.0
    )
    contribution = pot_before_current_aggression(
        state.action_history, state.street
    ).latest_aggressor_contribution_bb
    facing = _preflop_facing(state) if state.street is Street.PREFLOP else None
    # N-3BSTRATA parity: the live opener flag, read exactly as play.bot_decision
    # reads it — computed on EVERY street (the postflop sampler ignores it).
    opener = _preflop_opener(state) == state.seats[seat].position
    return (
        state.street,
        tuple(state.board),
        state.seats[seat].position,
        facing,
        kinds,
        sum(s.invested_total_bb for s in state.seats),
        state.seats[seat].stack_bb,
        sum(
            1
            for s in state.seats
            if s.seat != seat and s.status in (PlayerStatus.IN, PlayerStatus.ALLIN)
        ),
        state.current_bet_bb,
        opener,
        to_call,
        contribution,
    )


def _assert_ctx_equal(ctx, truth, observed):
    street, board, position, facing, kinds, pot, stack, opp, cur, opener, to_call, contrib = truth
    assert ctx.street is street
    assert ctx.board == board
    assert ctx.position is position
    assert ctx.facing == facing
    assert ctx.kinds == kinds
    assert ctx.pot_bb == pytest.approx(pot, abs=1e-9)
    assert ctx.stack_bb == pytest.approx(stack, abs=1e-9)
    assert ctx.opponents == opp
    assert ctx.current_bet_to == pytest.approx(cur, abs=1e-9)
    assert ctx.is_opener == opener
    assert ctx.to_call_bb == pytest.approx(to_call, abs=1e-9)
    assert ctx.aggressor_contribution_bb == pytest.approx(contrib, abs=1e-9)
    assert ctx.observed is observed


def test_replay_matches_real_handstate_contexts(packs):
    """Full persona playouts: every seat's replayed contexts equal the real
    HandState contexts at each decision (facing, kinds, pot, stack, SPR inputs,
    and — ESTIM-PRICE — the faced price's numerator `to_call_bb` and denominator
    input `aggressor_contribution_bb`, against `engine.legal_actions` and
    `sizing.pot_before_current_aggression` respectively)."""
    rng = random.Random(20260712)
    priced_postflop = 0  # non-vacuity: the price fields must not be all-zero
    # Widened 6 -> 14 trials by the de-robotization slice (2026-08-15). Six
    # trials happened to yield 14 priced postflop contexts at this seed against
    # a floor of 5; once the villains' preflop ranges changed, the same six
    # yielded 4 and this guard fired — correctly, because at four contexts the
    # ESTIM-PRICE assertions barely run at all. The SAMPLE is widened rather
    # than the floor lowered: lowering it would answer a guard that says "this
    # test stopped testing much" by agreeing to test less.
    for trial in range(14):
        personas = assign_lineup(rng)
        seat_packs = {s: packs[personas.get(s, VillainType.TAG)] for s in range(9)}
        dealt = deal_hand(random.Random(rng.randrange(1_000_000_000)))
        state = start_hand(dealt, button_seat=trial % 9, stacks_bb=[100.0] * 9)
        truth: dict[int, list] = {s: [] for s in range(9)}
        guard = 0
        while not state.hand_over and state.to_act_seat is not None:
            guard += 1
            assert guard < 500
            seat = state.to_act_seat
            snapshot = _true_ctx(state, seat)
            decision = bot_decision(state, seat, seat_packs[seat], rng)
            truth[seat].append((snapshot, decision.action))
            state = apply(state, decision)
        hist = _project(state)
        for seat in range(9):
            ctxs = _replay_contexts(hist, seat, len(hist.actions))
            assert len(ctxs) == len(truth[seat])
            for ctx, (snapshot, observed) in zip(ctxs, truth[seat], strict=True):
                _assert_ctx_equal(ctx, snapshot, observed)
                if ctx.street is not Street.PREFLOP and ctx.to_call_bb > 0.0:
                    assert ctx.aggressor_contribution_bb > 0.0  # someone bet those chips
                    priced_postflop += 1
    assert priced_postflop >= 5, (
        f"only {priced_postflop} postflop facing-chips contexts in these playouts — "
        f"the ESTIM-PRICE assertions would be near-vacuous (measured 14)"
    )


def test_multiway_limp_raise_facing_reconstruction():
    """Scripted limps + raise + cold-calls: replayed preflop facing equals
    play._preflop_facing on the real state at every decision index."""
    dealt = _dealt_fixed(("As", "Ad"), ["Kh", "7d", "2c", "9s", "3h"])
    state = start_hand(dealt, button_seat=8, stacks_bb=[100.0] * 9)  # SB=0 BB=1 UTG=2
    moves = [
        (2, _CALL),  # limp -> unopened
        (3, _CALL),  # limp -> vs_limpers
        (4, _raise_to(4.0)),  # iso-raise -> vs_limpers
        (5, _CALL),  # -> vs_rfi
        (6, _FOLD),
        (7, _FOLD),
        (8, _FOLD),
        (0, _FOLD),
        (1, _CALL),
        (2, _CALL),
        (3, _raise_to(12.0)),  # limp-raise -> vs_rfi
    ]
    truth: dict[int, list[str]] = {}
    expected_facings = []
    for seat, decision in moves:
        assert state.to_act_seat == seat
        facing = _preflop_facing(state)
        expected_facings.append(facing)
        truth.setdefault(seat, []).append(facing)
        state = apply(state, decision)
    assert expected_facings[:5] == ["unopened", "vs_limpers", "vs_limpers", "vs_rfi", "vs_rfi"]
    hist = _project(state)
    for seat, facings in truth.items():
        ctxs = _replay_contexts(hist, seat, len(hist.actions))
        assert [c.facing for c in ctxs] == facings


# ------------------------------------------------- postflop narrowing


def test_postflop_barrel_narrows_toward_strength(packs):
    """After a TAG c-bet on dry Kh7d2c, aggregate weight shifts toward strong
    classes vs the preflop-only posterior (fails under a no-op reweight)."""
    tag = packs[VillainType.TAG]
    dealt = _dealt_fixed(("As", "Ad"), ["Kh", "7d", "2c", "Qs", "3d"])
    state = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    moves = [(3, _raise_to(3.0))]
    moves += [(s, _FOLD) for s in (4, 5, 6, 7, 8, 0, 1)]
    moves += [(2, _CALL), (2, _CHECK), (3, _bet(4.5))]
    state = _script(state, moves)
    hist = _project(state)
    prior = estimate_range(tag, hist, seat=3, through_action=len(hist.actions) - 1)
    posterior = estimate_range(tag, hist, seat=3)
    assert prior.exact is True  # no villain postflop action in the prefix
    assert posterior.exact is False
    strong = {"AA", "KK", "77", "AKs", "AKo"}
    prior_share = sum(prior.class_weights[c] for c in strong)
    post_share = sum(posterior.class_weights[c] for c in strong)
    assert post_share > prior_share + 0.02


# ------------------------------------------- dead cards / through_action


def test_dead_cards_reduce_ako_zero_only_blocked_akss(packs):
    tag = packs[VillainType.TAG]
    hist = _hand_history(
        0,
        [(s, Street.PREFLOP, ActionType.FOLD, 0.0) for s in range(3, 9)]
        + [(0, Street.PREFLOP, ActionType.RAISE, 3.0)],
    )
    free = estimate_range(tag, hist, seat=0)
    dead = estimate_range(tag, hist, seat=0, dead_cards=("Ah", "Ks"))
    # Every combo containing a dead card is zero.
    for (c1, c2), w in dead.combo_weights.items():
        if "Ah" in (c1, c2) or "Ks" in (c1, c2):
            assert w == 0.0
    # AKo: reduced, not zeroed — 7 of 12 combos survive.
    ako_live = [
        c
        for c, w in dead.combo_weights.items()
        if w > 0 and {c[0][0], c[1][0]} == {"A", "K"} and c[0][1] != c[1][1]
    ]
    assert len(ako_live) == 7
    assert 0 < dead.class_weights["AKo"] < free.class_weights["AKo"]
    # AKs: drops ONLY the blocked combos (AhKh, AsKs); clubs/diamonds survive.
    assert dead.combo_weights[("Kh", "Ah")] == 0.0
    assert dead.combo_weights[("Ks", "As")] == 0.0
    assert dead.combo_weights[("Kc", "Ac")] > 0.0
    assert dead.combo_weights[("Kd", "Ad")] > 0.0


def test_through_action_prefix(packs):
    tag = packs[VillainType.TAG]
    hist = _four_bet_history()
    open_only = estimate_range(tag, hist, seat=3, through_action=3)
    assert _positive(open_only) == _raise_classes(tag, "unopened", Position.UTG)
    full = estimate_range(tag, hist, seat=3)
    assert _positive(open_only) != _positive(full)
    clamped = estimate_range(tag, hist, seat=3, through_action=len(hist.actions))
    assert clamped == full


# --------------------------------------- river parity (P2a, R1 truthfulness)


def _live_legal(ctx) -> list[LegalAction]:
    """The legal bracket the LIVE engine presents at this node, rebuilt test-side
    (deliberately NOT `range_estimate._legal_from_ctx`, so the parity assertions
    below stay independent of the module under test). ESTIM-PRICE: CALL carries
    the faced price; BET/RAISE min/max stay None because the sampler reads them
    only in the sizing draw, which a capture rng never reaches.

    THAT LAST CLAUSE IS THE ONE THIS FILE CANNOT CHECK FOR ITSELF, so do not
    read it as a guarantee. It matches `_legal_from_ctx` exactly, which means
    every parity test using this helper feeds BOTH sides a capless bracket and
    would keep passing if the sampler started reading those fields — which is
    precisely what improvement slice 2's withdrawn T2 lever did. The assumption
    is asserted instead by
    `test_no_aggressive_bracket_field_is_read_before_the_action_draw`, which
    builds its live side from `engine.legal_actions`. Keep this helper capless:
    its job is to mirror the estimator, and the other test's job is to catch the
    mirror being wrong."""
    return [
        LegalAction(action=k, min_bb=ctx.to_call_bb if k is ActionType.CALL else None)
        for k in sorted(ctx.kinds)
    ]


class _CaptureFirstChoices:
    """Duck-typed rng recording the sampler's first choices() distribution
    (the action draw) — same idiom as range_estimate._CaptureRng."""

    def __init__(self):
        self.dist = None

    def choices(self, population, weights, k=1):
        if self.dist is None:
            self.dist = dict(zip(population, weights, strict=True))
        return [population[0]]


def test_estimator_river_dist_equals_live_polarized_policy(packs):
    """P2a Q3 estimator parity (the R1-reveal truthfulness guard): on a fixed
    RIVER facing-a-bet context, the estimator's recovered action distribution
    (`_postflop_action_dist`) EQUALS a direct capture of the live policy
    (`sample_postflop_decision(..., street=Street.RIVER)`) on the same inputs
    — the estimator replays the polarized river policy, not the stale
    streetless one (the street=None distribution differs on both probe
    holes, so the equality is discriminating)."""
    tag = packs[VillainType.TAG]
    dealt = _dealt_fixed(("As", "Ad"), ["Kh", "7d", "2c", "9s", "3h"])
    state = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    moves = [(3, _raise_to(3.0))]
    moves += [(s, _FOLD) for s in (4, 5, 6, 7, 8, 0, 1)]
    moves += [(2, _CALL)]
    moves += [(2, _CHECK), (3, _bet(3.0)), (2, _CALL)]  # flop
    moves += [(2, _CHECK), (3, _bet(6.0)), (2, _CALL)]  # turn
    moves += [(2, _CHECK), (3, _bet(12.0)), (2, _CALL)]  # river: seat 2 faces a bet
    state = _script(state, moves)
    ctx = _replay_contexts(_project(state), seat=2, n=len(_project(state).actions))[-1]
    assert ctx.street is Street.RIVER
    assert ActionType.RAISE in ctx.kinds

    # Probe holes where river polarization bites: middle pair (raise floored)
    # and no-draw air (call floored) on the Kh7d2c9s3h board.
    for hole in (("9c", "4d"), ("6h", "4c")):
        estimator = _postflop_action_dist(tag, hole, ctx)
        legal = _live_legal(ctx)
        live = _CaptureFirstChoices()
        sample_postflop_decision(
            tag,
            hole,
            list(ctx.board),
            legal,
            ctx.pot_bb,
            ctx.stack_bb,
            ctx.opponents,
            live,  # type: ignore[arg-type] — duck-typed capture rng
            current_bet_to=ctx.current_bet_to,
            street=Street.RIVER,
            latest_aggressor_contribution_bb=ctx.aggressor_contribution_bb,
            aggressor_bet_prev_street=ctx.aggressor_bet_prev_street,
        )
        assert estimator == live.dist, hole
        streetless = _CaptureFirstChoices()
        sample_postflop_decision(
            tag,
            hole,
            list(ctx.board),
            legal,
            ctx.pot_bb,
            ctx.stack_bb,
            ctx.opponents,
            streetless,  # type: ignore[arg-type]
            current_bet_to=ctx.current_bet_to,
            latest_aggressor_contribution_bb=ctx.aggressor_contribution_bb,
        )
        assert estimator != streetless.dist, hole  # polarization visible in the reveal


def test_estimator_facing_raise_parity_with_live_sampler(packs):
    """W3R-6 estimator parity: on a replayed FLOP facing-a-RAISE node the
    estimator's recovered distribution equals the live sampler with
    `facing_raise=True`, and the replay-derived flag equals
    `postflop_context.facing_raise(...)` on the equivalent HandState. The
    ">= 2 postflop BET/RAISE actions on this street" rule is implemented TWICE
    (replay walk + pure helper) — this test is what pins them equal."""
    from app.domain.table.postflop_context import facing_raise as ctx_facing_raise

    tag = packs[VillainType.TAG]
    dealt = _dealt_fixed(("As", "Ad"), ["Kh", "7d", "2c"])
    state = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    moves = [(3, _raise_to(3.0))]
    moves += [(s, _FOLD) for s in (4, 5, 6, 7, 8, 0, 1)]
    moves += [(2, _CALL)]
    moves += [(2, _CHECK), (3, _bet(3.0)), (2, _raise_to(12.0))]  # flop bet-raise war
    state = _script(state, moves)

    # The live seat-3 decision point: it is facing a RAISE on the flop.
    assert state.to_act_seat == 3 and state.street is Street.FLOP
    assert ctx_facing_raise(state.action_history, state.street) is True
    # ...and a bare bet on the same street is NOT a raise (the discriminating half).
    assert ctx_facing_raise(
        [h for h in state.action_history if h.action is not ActionType.RAISE
         or h.street is not Street.FLOP],
        Street.FLOP,
    ) is False

    state = _script(state, [(3, _CALL)])
    hist = _project(state)
    ctx = _replay_contexts(hist, seat=3, n=len(hist.actions))[-1]
    assert ctx.street is Street.FLOP
    assert ActionType.RAISE in ctx.kinds
    # the replay-derived flag equals the pure helper's verdict on the live state
    assert ctx.facing_raise is True

    # Probe holes where the two damps bite: naked ace-high (#5) and a made
    # middle pair (#9) on Kh7d2c.
    for hole in (("Ah", "5c"), ("7s", "5s")):
        estimator = _postflop_action_dist(tag, hole, ctx)
        legal = _live_legal(ctx)
        live = _CaptureFirstChoices()
        sample_postflop_decision(
            tag, hole, list(ctx.board), legal, ctx.pot_bb, ctx.stack_bb, ctx.opponents,
            live,  # type: ignore[arg-type] — duck-typed capture rng
            current_bet_to=ctx.current_bet_to, street=Street.FLOP, facing_raise=True,
            latest_aggressor_contribution_bb=ctx.aggressor_contribution_bb,
        )
        assert estimator == live.dist, hole
        blind = _CaptureFirstChoices()
        sample_postflop_decision(
            tag, hole, list(ctx.board), legal, ctx.pot_bb, ctx.stack_bb, ctx.opponents,
            blind,  # type: ignore[arg-type]
            current_bet_to=ctx.current_bet_to, street=Street.FLOP, facing_raise=False,
            latest_aggressor_contribution_bb=ctx.aggressor_contribution_bb,
        )
        assert estimator != blind.dist, hole  # the damp is visible in the reveal


def _flop_call_ctx(pot_frac: float):
    """Seat 3 opens, seat 2 calls (flop pot 6.5), seat 2 checks, seat 3 bets
    `pot_frac` × pot, seat 2 CALLS. Returns (history, seat-2's flop context)."""
    dealt = _dealt_fixed(("As", "Ad"), ["Kh", "7d", "2c", "9s", "3h"])
    state = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    moves = [(3, _raise_to(3.0))]
    moves += [(s, _FOLD) for s in (4, 5, 6, 7, 8, 0, 1)]
    moves += [(2, _CALL)]
    moves += [(2, _CHECK), (3, _bet(round(6.5 * pot_frac, 2))), (2, _CALL)]
    state = _script(state, moves)
    hist = _project(state)
    return hist, _replay_contexts(hist, seat=2, n=len(hist.actions))[-1]


def test_estimator_prices_the_faced_bet(packs):
    """🔴 ESTIM-PRICE (the deferred W1-era Codex finding): the estimator used to
    build CALL with `min_bb=None`, so `sample_postflop_decision`'s faced-price
    numerator was 0 and EVERY faced bet — half-pot or 3×-pot jam — produced the
    identical response distribution (measured at pre-fix HEAD: fold 0.4665 for
    air and 0.0977 for middle pair at all three of f = 0.5 / 1.5 / 3.0).

    Pins three things: the reconstructed price arithmetic against theory contract
    §3/§7 (f = to_call / pot-before-the-aggression), exact parity with the live
    sampler at each price, and strict monotonicity of the fold response."""
    tag = packs[VillainType.TAG]
    dists = {}
    for f in (0.5, 1.5, 3.0):
        hist, ctx = _flop_call_ctx(f)
        bet = round(6.5 * f, 2)
        # Contract §7 denominator unification: the pot the bet was made INTO is
        # the live pot minus the aggressor's own increment.
        assert ctx.to_call_bb == pytest.approx(bet)
        assert ctx.aggressor_contribution_bb == pytest.approx(bet)
        assert ctx.pot_bb == pytest.approx(6.5 + bet)
        faced_frac = ctx.to_call_bb / (ctx.pot_bb - ctx.aggressor_contribution_bb)
        assert faced_frac == pytest.approx(f), "reconstructed price != the bet's pot-fraction"

        for hole in (("7s", "5s"), ("6h", "4c")):  # middle pair / air
            estimator = _postflop_action_dist(tag, hole, ctx)
            live = _CaptureFirstChoices()
            sample_postflop_decision(
                tag, hole, list(ctx.board), _live_legal(ctx), ctx.pot_bb, ctx.stack_bb,
                ctx.opponents,
                live,  # type: ignore[arg-type] — duck-typed capture rng
                current_bet_to=ctx.current_bet_to, street=Street.FLOP,
                latest_aggressor_contribution_bb=ctx.aggressor_contribution_bb,
                facing_raise=ctx.facing_raise,
            )
            assert estimator == live.dist, (f, hole)
            dists[f, hole] = estimator

    for hole in (("7s", "5s"), ("6h", "4c")):
        folds = [dists[f, hole][ActionType.FOLD] for f in (0.5, 1.5, 3.0)]
        assert folds[0] < folds[1] < folds[2], f"{hole} fold response not monotone: {folds}"
        # SIZE OF THE RESPONSE, in log-odds rather than in probability points
        # (S3-T2 — improvement slice 3, ticket 2, the calling-dial retune —
        # 2026-08-22, after a theory review and under owner ruling 11 of that
        # date). The original form asked for 0.20 of PROBABILITY span on BOTH
        # holes, and the air leg SATURATES: at a three-times-pot bet the air
        # hand already folds 0.965, so under 0.035 of room is left above it,
        # and anything that makes the TAG fold more at the SMALL price eats the
        # margin without weakening the price response at all. Measured across
        # the TAG's plausible calling-dial range, the air probability span
        # falls 0.2698 at a dial of 0.60 to 0.2100 at 0.42 to 0.1948 at the
        # 0.38 this slice ships, crossing the old 0.20 threshold on the way —
        # so that threshold was measuring how close the ceiling was, not how
        # much the bot cares about the price.
        #
        # LOG-ODDS IS THE SCALE THE RESPONSE ACTUALLY LIVES ON, and the leg
        # REDUCES TO THE FOLD SIDE'S PRICE-FACTOR RATIO — which is why it is
        # invariant to the calling dial AND to the hand's strength bucket by a
        # model property rather than by luck. At a facing node the fold merit is
        # `_FOLD_BASE[bucket] * _price_factor(f, e)` and the continue side is
        # `L * K` with `K` price-free, so
        #     logit(fold) = ln _FOLD_BASE[bucket] + ln _price_factor(f, e)
        #                   - ln L - ln K
        # and every term except `_price_factor` is identical at both prices.
        # The bucket constant and the dial both cancel in the span, leaving a
        # closed form:
        #     span = e * ln(alpha_OVERBET / alpha_MEDIUM)
        #            + _PRICE_TAIL_K * ln(3.0 / _PRICE_TAIL_ANCHOR)
        #          = 2.375199 * ln(0.60 / 0.375) + 2 * ln(2)
        #          = 2.502646
        # at the TAG's price exponent 2.375199 (`_PRICE_SENSITIVITY *
        # stickiness ** -_PRICE_STICKINESS_DAMP`, the un-opted-in branch). The
        # measured span is 2.502646490 and the closed form is 2.5026464895 —
        # the same number, and it reads the same at every dial from 0.60 to
        # 0.30 and on both holes. So the threshold of 2.0 has a fixed 0.50 of
        # margin no retune can spend.
        # THREE PROBES SAY THE THRESHOLD IS DOING WORK. An estimator that
        # ignores the price makes all three distributions identical: 0.0. A
        # price response weakened twentyfold (the bucket-alpha exponent divided
        # by 20, tail term untouched) reads 1.442, which is RED. And no calling
        # dial reads anything but 2.502646.
        lo = [math.log(x / (1.0 - x)) for x in folds]
        assert lo[2] - lo[0] > 2.0, (
            f"{hole} price response is cosmetic: folds {folds}, log-odds span "
            f"{lo[2] - lo[0]:.3f} (the price-blind defect this test was written "
            f"for reads 0.0)"
        )
    # The probability-span form is KEPT on the middle-pair hole alone, which is
    # the leg that does not saturate: at the shipped 0.38 dial it folds 0.309
    # at a half-pot bet and 0.845 at three-times-pot, a span of 0.536 with 0.15
    # of room still above it. Dropping the probability form entirely would give
    # up a check anyone can read straight off the numbers without a transform.
    mid = [dists[f, ("7s", "5s")][ActionType.FOLD] for f in (0.5, 1.5, 3.0)]
    assert mid[2] - mid[0] > 0.2, f"middle-pair price response is cosmetic: {mid}"


def test_estimator_prices_a_self_reraise_by_the_increment_not_the_bet_to(packs):
    """🔴 ESTIM-PRICE, the discriminating case (Codex fold): on FRESH aggression
    the street's latest-aggressor INCREMENT and `current_bet_to` are equal, so
    every other test here would pass under either one. They diverge on a
    same-street self-re-raise, and that is the case theory contract §7
    ("denominator unification") legislates: the pre-aggression pot is the live
    pot minus the increment the last bet/raise ADDED, never minus its raise-TO —
    subtracting the TO double-counts the raiser's earlier street chips, shrinking
    the denominator and OVERSTATING the price.

    Line: seat 2 bets 3 into 6.5, seat 3 raises to 12, seat 2 re-raises to 60
    (its own increment is 57, not 60), seat 3 faces 48 into a live pot of 78.5.
      correct  f = 48 / (78.5 − 57) = 2.2326
      bet-TO   f = 48 / (78.5 − 60) = 2.5946   (16% too expensive)
    Both sit above the 1.5 anchor, where the R10-TAIL-a1 tail is CONTINUOUS in
    f, so the error cannot hide inside a shared α bucket. Mutation-kill: the
    estimator must equal the live sampler fed the increment and DIFFER from the
    one fed the bet-TO. Probe holes are deliberately non-drawing so the
    SPR-commit branch (live SPR 1.08 vs tag's spr_commit 2.5) is inert."""
    tag = packs[VillainType.TAG]
    dealt = _dealt_fixed(("As", "Ad"), ["Kh", "7d", "2c"])
    state = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    moves = [(3, _raise_to(3.0))]
    moves += [(s, _FOLD) for s in (4, 5, 6, 7, 8, 0, 1)]
    moves += [(2, _CALL)]
    moves += [(2, _bet(3.0)), (3, _raise_to(12.0)), (2, _raise_to(60.0)), (3, _CALL)]
    state = _script(state, moves)
    hist = _project(state)
    ctx = _replay_contexts(hist, seat=3, n=len(hist.actions))[-1]

    # The precondition that makes this test discriminating at all.
    assert ctx.street is Street.FLOP
    assert ctx.to_call_bb == pytest.approx(48.0)
    assert ctx.pot_bb == pytest.approx(78.5)
    assert ctx.current_bet_to == pytest.approx(60.0)
    assert ctx.aggressor_contribution_bb == pytest.approx(57.0)
    assert ctx.aggressor_contribution_bb != ctx.current_bet_to
    f_ok = ctx.to_call_bb / (ctx.pot_bb - ctx.aggressor_contribution_bb)
    f_bad = ctx.to_call_bb / (ctx.pot_bb - ctx.current_bet_to)
    assert f_ok == pytest.approx(48.0 / 21.5) and f_bad == pytest.approx(48.0 / 18.5)
    assert size_bucket(f_ok) is size_bucket(f_bad)  # only the tail separates them
    assert f_ok > 1.5, "below the anchor the two prices would share one flat bucket"

    for hole in (("6h", "4c"), ("7s", "5s")):  # air / middle pair, neither drawing
        estimator = _postflop_action_dist(tag, hole, ctx)
        dists = {}
        for label, contribution in (
            ("increment", ctx.aggressor_contribution_bb),
            ("bet_to", ctx.current_bet_to),
        ):
            cap = _CaptureFirstChoices()
            sample_postflop_decision(
                tag, hole, list(ctx.board), _live_legal(ctx), ctx.pot_bb, ctx.stack_bb,
                ctx.opponents,
                cap,  # type: ignore[arg-type] — duck-typed capture rng
                current_bet_to=ctx.current_bet_to, street=Street.FLOP,
                latest_aggressor_contribution_bb=contribution,
                facing_raise=ctx.facing_raise,
            )
            dists[label] = cap.dist
        assert estimator == dists["increment"], hole
        assert estimator != dists["bet_to"], hole  # the mutation must be killed
        # ...and in the diagnostic direction: the bet-TO denominator over-folds.
        assert dists["bet_to"][ActionType.FOLD] > estimator[ActionType.FOLD], hole


def test_estimator_has_the_overbet_price_tail(packs):
    """🔴 R10-TAIL-a1 parity (the filed follow-up): above the 1.5× anchor the
    bucketed α saturates, so ONLY the production tail `(f/1.5)**K` can separate a
    1.5× bet from a 3× one — and the estimator must see that separation, else the
    villain-range reveal keeps promising a 3×-pot jam is called as often as a
    1.5× bet. The estimator owns no price law: it reaches `_price_factor` through
    the production sampler, so the constant lives in exactly one place."""
    tag = packs[VillainType.TAG]
    # The saturation claim, asserted not assumed: same bucket, and the whole
    # ratio between the two prices is the tail (K=2 ⇒ (3.0/1.5)**2 = 4.0).
    assert size_bucket(1.5) is size_bucket(3.0)
    exponent = _price_exponent(tag.postflop)
    assert _price_factor(3.0, exponent) == pytest.approx(4.0 * _price_factor(1.5, exponent))

    anchor = _postflop_action_dist(tag, ("7s", "5s"), _flop_call_ctx(1.5)[1])
    tail = _postflop_action_dist(tag, ("7s", "5s"), _flop_call_ctx(3.0)[1])
    assert tail[ActionType.FOLD] > anchor[ActionType.FOLD] + 0.2, (anchor, tail)
    assert tail[ActionType.CALL] < anchor[ActionType.CALL]


def test_estimator_posterior_moves_with_the_faced_price(packs):
    """The user-facing consequence (`sim_session.estimate_range`): calling a 3×
    overbet is stronger evidence than calling a half-pot bet, so the revealed
    range must be the STRONGER one. Pre-fix all three posteriors were IDENTICAL.

    "Stronger" is measured as the mass on hands that make no pair (AIR +
    ACE_HIGH), which must fall as the price rises — NOT as concentration, which
    moves the other way here: the overbet strips the dominant ace-high offsuit
    classes and spreads mass over the pairs, so the posterior gets stronger and
    FLATTER at once (measured air share 0.5382 / 0.4656 / 0.3790 at f = 0.5 /
    1.5 / 3.0; sum-of-squares 0.0831 / 0.0764 / 0.0735)."""
    tag = packs[VillainType.TAG]
    board = ["Kh", "7d", "2c"]
    no_pair = (StrengthBucket.AIR, StrengthBucket.ACE_HIGH)
    shares = []
    for f in (0.5, 1.5, 3.0):
        res = estimate_range(tag, _flop_call_ctx(f)[0], seat=2, dead_cards=("Tc", "Td"))
        shares.append(
            sum(
                w
                for combo, w in res.combo_weights.items()
                if w > 0.0 and strength_bucket(combo, board)[0] in no_pair
            )
        )
    assert shares[0] > shares[1] > shares[2], f"no-pair share not monotone in price: {shares}"
    assert shares[0] - shares[2] > 0.1, f"posterior barely moved with price: {shares}"


def test_estimator_facing_raise_false_on_a_bare_flop_bet(packs):
    """The estimator's replay must not confuse a PREFLOP raise war with a
    postflop raise: 3-bet preflop then a single flop bet is facing_raise False."""
    dealt = _dealt_fixed(("As", "Ad"), ["Kh", "7d", "2c"])
    state = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    moves = [(3, _raise_to(3.0))]
    moves += [(s, _FOLD) for s in (4, 5, 6, 7, 8, 0, 1)]
    moves += [(2, _raise_to(9.0)), (3, _CALL)]  # preflop 3-bet war
    moves += [(2, _bet(6.0)), (3, _CALL)]  # flop: a BARE bet
    state = _script(state, moves)
    hist = _project(state)
    ctx = _replay_contexts(hist, seat=3, n=len(hist.actions))[-1]
    assert ctx.street is Street.FLOP
    assert ctx.facing_raise is False


# ---------------------------------------------------------------- perf


def test_river_depth_estimate_under_150ms(packs):
    tag = packs[VillainType.TAG]
    dealt = _dealt_fixed(("As", "Ad"), ["Kh", "7d", "2c", "Qs", "3d"])
    state = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    moves = [(3, _raise_to(3.0))]
    moves += [(s, _FOLD) for s in (4, 5, 6, 7, 8, 0, 1)]
    moves += [(2, _CALL)]
    moves += [(2, _CHECK), (3, _bet(3.0)), (2, _CALL)]  # flop
    moves += [(2, _CHECK), (3, _bet(7.0)), (2, _CALL)]  # turn
    moves += [(2, _CHECK), (3, _bet(15.0))]  # river
    state = _script(state, moves)
    hist = _project(state)
    t0 = time.perf_counter()
    res = estimate_range(tag, hist, seat=3, dead_cards=("Tc", "Td"))
    elapsed = time.perf_counter() - t0
    assert res.exact is False
    assert elapsed < 0.15, f"river-depth estimate took {elapsed * 1000:.1f}ms"


# ------------------------------------------------ R9-SIGNAL estimator parity


def test_estimator_barrel_run_signal_is_wired_and_moves_the_reveal(packs):
    """R9-DEFENCE-a / S-6 estimator parity (a)+(b): the opponent-LINE signal is
    now READ by the live policy, so the villain-range reveal must have moved.

    Was `test_estimator_unchanged_by_the_barrel_run_signal`, pre-registered
    under R9-SIGNAL (the signal derived, plumbed, and read by nobody) to assert
    the estimator equalled the live sampler with `aggressor_bet_prev_street`
    BOTH True and False — satisfiable only while the kwarg was dead. Its own
    docstring named this the RED-FIRST failure that would prove the mechanic
    wired once R9-DEFENCE-a landed a consumer. It has now turned: on a replayed
    TURN node where the aggressor really did barrel (bet the flop, bet the
    turn — the derivation says `run == 1`, satisfying S-6's "fixture node with
    `aggressor_barrel_run(...) >= 1`"), the estimator's recovered distribution
    equals the live sampler with the flag True, and now DIFFERS from the live
    sampler with the flag False — the reveal is sensitive to the signal, which
    is exactly S-6's "differs from the line-blind one" (contrast
    `test_estimator_facing_raise_parity_with_live_sampler`, where the live
    W3R-6 signal already made the two legs differ before this slice).
    """
    from app.domain.table.postflop_context import aggressor_barrel_run

    tag = packs[VillainType.TAG]
    dealt = _dealt_fixed(("As", "Ad"), ["Kh", "7d", "2c", "9s", "3h"])
    state = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    moves = [(3, _raise_to(3.0))]
    moves += [(s, _FOLD) for s in (4, 5, 6, 7, 8, 0, 1)]
    moves += [(2, _CALL)]
    moves += [(2, _CHECK), (3, _bet(3.0)), (2, _CALL)]  # flop c-bet
    moves += [(2, _CHECK), (3, _bet(7.0))]  # turn barrel — seat 2 faces it
    state = _script(state, moves)
    assert state.to_act_seat == 2 and state.street is Street.TURN

    aggressor = state.seats[3].position
    assert aggressor_barrel_run(state.action_history, Street.TURN, aggressor) == 1
    # ...and 0 at the flop node of the SAME hand: the preflop raise never counts.
    assert aggressor_barrel_run(state.action_history, Street.FLOP, aggressor) == 0

    state = _script(state, [(2, _CALL)])
    hist = _project(state)
    ctx = _replay_contexts(hist, seat=2, n=len(hist.actions))[-1]
    assert ctx.street is Street.TURN
    legal = _live_legal(ctx)

    for hole in (("9c", "4d"), ("7s", "5s")):
        estimator = _postflop_action_dist(tag, hole, ctx)
        dists = {}
        for flag in (False, True):
            live = _CaptureFirstChoices()
            sample_postflop_decision(
                tag, hole, list(ctx.board), legal, ctx.pot_bb, ctx.stack_bb, ctx.opponents,
                live,  # type: ignore[arg-type] — duck-typed capture rng
                current_bet_to=ctx.current_bet_to, street=Street.TURN,
                latest_aggressor_contribution_bb=ctx.aggressor_contribution_bb,
                facing_raise=ctx.facing_raise, aggressor_bet_prev_street=flag,
            )
            dists[flag] = live.dist
        # the replay derived the flag True at this node (asserted above via
        # aggressor_barrel_run == 1), so the estimator must match the live
        # sampler's True leg...
        assert estimator == dists[True], hole
        # ...and DIFFER from the False (line-blind) leg — S-6's sensitivity
        # half. Without this half an estimator that always passes `False`
        # would still pass the True-leg assertion at a line-BLIND node, and
        # nothing here would prove the reveal is actually sensitive to line.
        assert estimator != dists[False], hole


def test_estimator_barrel_flag_matches_shipped_derivation_under_discriminators():
    """S-6 estimator parity discriminators (spec §7 S-6, ledger R-9): the
    replay-derived `_Ctx.aggressor_bet_prev_street` flag must equal the shipped
    derivation (`aggressor_barrel_run`) node-for-node under four cases picked
    to kill two specific wrong implementations:

    - an estimator that always passes `False` (killed by case 1: `True`)
    - an estimator reading "ANY aggression on the previous street" instead of
      the SAME SEAT's (killed by case 2: it passes heads-up-shaped case 1 but
      is wrong here, where a DIFFERENT seat bet the previous street multiway)

    Cases 1 and 2 share the same board and the same multiway (3-handed) shape,
    turn bet made by seat 4 in both — the ONLY difference is who bet the flop
    (also seat 4 in case 1, seat 5 in case 2) — so the discriminator isolates
    the SAME-SEAT requirement, not some other confound.
    """
    from app.domain.table.postflop_context import aggressor_barrel_run

    board = ["Kh", "7d", "2c", "9s", "3h"]

    # Case 1 — same-seat consecutive barrel, multiway: seat 4 bets flop AND
    # turn; seat 3 faces the turn bet. Also satisfies S-6 (a): a fixture node
    # with aggressor_barrel_run(...) >= 1.
    same_seat = _hand_history(
        0,
        [
            (3, Street.PREFLOP, ActionType.RAISE, 3.0),
            (4, Street.PREFLOP, ActionType.CALL, 3.0),
            (5, Street.PREFLOP, ActionType.CALL, 3.0),
            (1, Street.PREFLOP, ActionType.FOLD, 0.0),
            (2, Street.PREFLOP, ActionType.FOLD, 0.0),
            (4, Street.FLOP, ActionType.BET, 4.0),
            (5, Street.FLOP, ActionType.CALL, 4.0),
            (3, Street.FLOP, ActionType.CALL, 4.0),
            (4, Street.TURN, ActionType.BET, 8.0),
            (3, Street.TURN, ActionType.CALL, 8.0),
        ],
        board=board[:4],
    )
    ctx1 = _replay_contexts(same_seat, seat=3, n=len(same_seat.actions))[-1]
    assert ctx1.street is Street.TURN
    seat4_pos = next(
        a.position
        for a in same_seat.actions
        if a.street is Street.FLOP and a.action is ActionType.BET
    )
    assert (
        aggressor_barrel_run(same_seat.actions[:-1], Street.TURN, seat4_pos) >= 1
    ), "fixture must satisfy S-6(a): a node with aggressor_barrel_run(...) >= 1"
    assert ctx1.aggressor_bet_prev_street is True

    # Case 2 — DIFFERENT seat bet the previous street, multiway: seat 5 (a
    # flop CALLER, not the flop bettor) bets the turn; seat 3 faces IT
    # instead. The naive "any aggression last street" reading sees a bet on
    # the flop (by seat 4) and a bet on the turn and would say True — wrong,
    # because the turn's own aggressor (seat 5) did not bet the flop.
    diff_seat = _hand_history(
        0,
        [
            (3, Street.PREFLOP, ActionType.RAISE, 3.0),
            (4, Street.PREFLOP, ActionType.CALL, 3.0),
            (5, Street.PREFLOP, ActionType.CALL, 3.0),
            (1, Street.PREFLOP, ActionType.FOLD, 0.0),
            (2, Street.PREFLOP, ActionType.FOLD, 0.0),
            (4, Street.FLOP, ActionType.BET, 4.0),
            (5, Street.FLOP, ActionType.CALL, 4.0),
            (3, Street.FLOP, ActionType.CALL, 4.0),
            (5, Street.TURN, ActionType.BET, 8.0),
            (3, Street.TURN, ActionType.CALL, 8.0),
        ],
        board=board[:4],
    )
    ctx2 = _replay_contexts(diff_seat, seat=3, n=len(diff_seat.actions))[-1]
    assert ctx2.street is Street.TURN
    seat5_pos = next(
        a.position
        for a in diff_seat.actions
        if a.street is Street.TURN and a.action is ActionType.BET
    )
    assert aggressor_barrel_run(diff_seat.actions[:-1], Street.TURN, seat5_pos) == 0
    assert ctx2.aggressor_bet_prev_street is False

    # Case 3 — broken consecutive line: bet flop, CHECK turn, bet river. The
    # river's own bet is the wager being faced, never part of its own run;
    # the intervening check breaks it.
    broken = _hand_history(
        0,
        [
            (4, Street.PREFLOP, ActionType.RAISE, 3.0),
            (3, Street.PREFLOP, ActionType.CALL, 3.0),
            (1, Street.PREFLOP, ActionType.FOLD, 0.0),
            (2, Street.PREFLOP, ActionType.FOLD, 0.0),
            (4, Street.FLOP, ActionType.BET, 4.0),
            (3, Street.FLOP, ActionType.CALL, 4.0),
            (4, Street.TURN, ActionType.CHECK, 0.0),
            (3, Street.TURN, ActionType.CHECK, 0.0),
            (4, Street.RIVER, ActionType.BET, 9.0),
            (3, Street.RIVER, ActionType.CALL, 9.0),
        ],
        board=board,
    )
    ctx3 = _replay_contexts(broken, seat=3, n=len(broken.actions))[-1]
    assert ctx3.street is Street.RIVER
    seat4_river_pos = next(
        a.position
        for a in broken.actions
        if a.street is Street.RIVER and a.action is ActionType.BET
    )
    assert aggressor_barrel_run(broken.actions[:-1], Street.RIVER, seat4_river_pos) == 0
    assert ctx3.aggressor_bet_prev_street is False

    # Case 4 — flop node: the derivation is postflop-only, 0 by construction —
    # a preflop raise never counts as a barrel.
    flop_cbet = _hand_history(
        0,
        [
            (4, Street.PREFLOP, ActionType.RAISE, 3.0),
            (3, Street.PREFLOP, ActionType.CALL, 3.0),
            (1, Street.PREFLOP, ActionType.FOLD, 0.0),
            (2, Street.PREFLOP, ActionType.FOLD, 0.0),
            (4, Street.FLOP, ActionType.BET, 4.0),
            (3, Street.FLOP, ActionType.CALL, 4.0),
        ],
        board=board[:3],
    )
    ctx4 = _replay_contexts(flop_cbet, seat=3, n=len(flop_cbet.actions))[-1]
    assert ctx4.street is Street.FLOP
    assert ctx4.aggressor_bet_prev_street is False


def test_estimator_barrel_flag_matches_production_over_organic_play():
    """S-6 companion (fan-in finding B) — the barrel flag, node-for-node against
    the LIVE derivation over organic playouts, not over hand-built fixtures.

    WHY THE FOUR SCRIPTED DISCRIMINATORS ABOVE ARE NOT ENOUGH. In all four, the
    target seat acts IMMEDIATELY after the street's bettor, so nothing ever
    intervenes between the aggression and the decision. A whole bug class hides
    in that gap: `street_aggressor` being overwritten by a NON-aggressive action.
    Measured — adding `street_aggressor = a.position` to the CALL branch of
    `_replay_contexts` passes the entire suite, including all four cases above,
    while being wrong on a multiway street where seat 4 bets, seat 5 CALLS, and
    seat 3 then acts. Fixtures are blind to it because a fixture only contains
    the shapes its author thought of; organic play contains the ones nobody did.

    Ground truth is `play.bot_decision`'s own two lines, copied here for the
    same reason `_true_ctx` copies its fields — the derivation is inline in
    `bot_decision`, not extracted, so parity has to be re-stated to be checked.

    THE FLOORS ARE ANTI-VACUITY, and every one is a MEASURED count with
    headroom, not a fitted number (96 hands, seed 20260712): 1,528 nodes
    compared, 49 of them flag TRUE, 187 with an intervening caller. An
    estimator that always returns `False` dies on the second floor; the
    overwrite bug dies on node-for-node equality at the third shape (measured 5
    mismatches under that mutant, and 0 at the tip)."""
    rng = random.Random(20260712)
    packs_ = load_persona_packs()
    truth: list[tuple] = []  # (hand index, seat, flags in decision order)
    hists = []
    flagged = intervening = 0
    for trial in range(96):
        personas = assign_lineup(rng)
        seat_packs = {s: packs_[personas.get(s, VillainType.TAG)] for s in range(9)}
        dealt = deal_hand(random.Random(rng.randrange(1_000_000_000)))
        state = start_hand(dealt, button_seat=trial % 9, stacks_bb=[100.0] * 9)
        per: dict[int, list[bool]] = {s: [] for s in range(9)}
        guard = 0
        while not state.hand_over and state.to_act_seat is not None:
            guard += 1
            assert guard < 500
            seat = state.to_act_seat
            # …exactly play.bot_decision's derivation.
            this_street = [h for h in state.action_history if h.street is state.street]
            street_aggressor = last_aggressor_position(this_street)
            flag = street_aggressor is not None and (
                aggressor_barrel_run(state.action_history, state.street, street_aggressor) >= 1
            )
            per[seat].append(flag)
            flagged += flag
            if street_aggressor is not None:
                last = max(
                    i
                    for i, h in enumerate(this_street)
                    if h.action in (ActionType.BET, ActionType.RAISE)
                )
                # the shape the scripted fixtures never produce: a non-aggressive
                # action standing between the wager and this decision.
                intervening += any(h.action is ActionType.CALL for h in this_street[last + 1 :])
            state = apply(state, bot_decision(state, seat, seat_packs[seat], rng))
        truth.append(per)
        hists.append(_project(state))

    compared = 0
    mismatches = []
    for hand, (per, hist) in enumerate(zip(truth, hists, strict=True)):
        for seat in range(9):
            ctxs = _replay_contexts(hist, seat, len(hist.actions))
            for ctx, live in zip(ctxs, per[seat], strict=True):
                compared += 1
                if ctx.aggressor_bet_prev_street != live:
                    mismatches.append((hand, seat, ctx.street, ctx.position, live))
    assert not mismatches, (
        f"the replayed barrel flag disagrees with the live derivation at "
        f"{len(mismatches)} of {compared} organic nodes: {mismatches[:5]}"
    )
    assert compared >= 1000, compared  # measured 1528
    assert flagged >= 20, (
        f"only {flagged} of {compared} organic nodes carry the flag — an estimator "
        f"that always returns False would pass this comparison vacuously"
    )
    assert intervening >= 100, (
        f"only {intervening} nodes have an action standing between the street's "
        f"wager and the decision — that is the shape this gate exists for"
    )


# =====================================================================
# N-LOGIT — G7: the estimator sees the node's real legal set
# =====================================================================


def test_nlogit_g7_estimator_dist_keys_are_exactly_the_nodes_legal_set(packs):
    """G7 — `_postflop_action_dist` returns exactly the node's LEGAL action
    set, on every legal shape a postflop node can present.

    Why this gate exists at all, given the two parity tests above already pass
    unmodified: those tests compare the estimator against the live sampler
    using the SAME capture mechanism on both sides, so they detect divergence
    between the two but are structurally blind to a fault SHARED by both
    (contract map C3, trap 1). A literal two-stage nested logit — draw
    {FOLD, CONTINUE}, then {CALL, RAISE} — would hand every capture rng in the
    repo a 2-outcome vector where a 3-outcome one is expected, and the parity
    tests would keep passing while the villain-range reveal quietly reported
    a distribution over the wrong outcome space. N-logit does the nesting
    algebraically inside the existing single normalization, so the shape is
    preserved by construction; this asserts it.

    Conditioned on the node's legal set, NOT hard-coded to three keys: a facing
    node may legally omit RAISE, and unopened nodes are CHECK+BET or
    CHECK+RAISE. The zero-total-merit path (`range_estimate.py:364`) is
    excluded, since it deliberately returns a deterministic singleton rather
    than a distribution over the legal set."""
    from app.domain.table.range_estimate import _Ctx

    shapes = [
        frozenset({ActionType.FOLD, ActionType.CALL}),
        frozenset({ActionType.FOLD, ActionType.CALL, ActionType.RAISE}),
        frozenset({ActionType.CHECK, ActionType.BET}),
        frozenset({ActionType.CHECK, ActionType.RAISE}),
    ]
    holes = [("As", "Ad"), ("9c", "4d"), ("7s", "5s"), ("Ah", "5h")]
    boards = [
        (Street.FLOP, ("Kh", "7d", "2c")),
        (Street.TURN, ("Kh", "7d", "2c", "9s")),
        (Street.RIVER, ("Kh", "7d", "2c", "9s", "3h")),
    ]
    checked = 0
    for vt, pack in packs.items():
        for kinds in shapes:
            facing = ActionType.FOLD in kinds
            for street, board in boards:
                for hole in holes:
                    ctx = _Ctx(
                        street=street,
                        board=board,
                        position=Position.BB,
                        facing=None,
                        kinds=kinds,
                        pot_bb=6.0,
                        stack_bb=100.0,
                        opponents=1,
                        current_bet_to=4.0 if facing else 0.0,
                        observed=ActionType.CALL if facing else ActionType.CHECK,
                        facing_raise=False,
                        to_call_bb=4.0 if facing else 0.0,
                        aggressor_contribution_bb=4.0 if facing else 0.0,
                    )
                    dist = _postflop_action_dist(pack, hole, ctx)
                    if len(dist) == 1 and sum(dist.values()) == 1.0 and len(kinds) > 1:
                        continue  # zero-total-merit singleton (range_estimate.py:364)
                    assert set(dist) == set(kinds), (vt, kinds, street, hole, dist)
                    assert sum(dist.values()) == pytest.approx(1.0), (vt, kinds, dist)
                    checked += 1
    assert checked > 200, checked


def test_estimator_multiway_flop_bet_parity_with_live_sampler(packs):
    """T1 estimator parity at MORE THAN ONE OPPONENT — the case neither existing
    parity test reaches.

    `test_estimator_river_dist_equals_live_polarized_policy` and
    `test_estimator_facing_raise_parity_with_live_sampler` both replay heads-up
    nodes, so when T1 (improvement slice 2, 2026-08-18) widened
    `_ACE_HIGH_FLOAT_RAISE_DAMP`'s predicate from `facing_raise` to
    `facing_raise or opponents > 1`, the new branch shipped with no parity pin at
    all. Parity holds structurally — `_postflop_action_dist` passes the real
    `ctx.opponents` and `_CaptureRng` short-circuits only the action draw, which
    is downstream of the predicate — so this is a missing regression test rather
    than a repair. It is worth having anyway: the whole point of T1's ticket is
    that a claim nobody tests stops being true quietly.

    Three-handed flop, seat 1 facing a BET with two opponents live, holding naked
    ace-high. The second leg is what makes the first non-vacuous: with the damp
    neutralised to 1.0 the recovered distribution differs, so the equality above
    is genuinely reporting the new branch and not passing because the branch
    never fired.
    """
    tag = packs[VillainType.TAG]
    dealt = _dealt_fixed(("As", "Ad"), ["Kh", "7d", "2c"])
    state = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    moves = [(3, _raise_to(3.0))]
    moves += [(s, _FOLD) for s in (4, 5, 6, 7, 8, 0)]
    moves += [(1, _CALL), (2, _CALL)]                      # three-handed to the flop
    moves += [(1, _CHECK), (2, _CHECK), (3, _bet(4.0))]    # seat 1 now faces a BET
    moves += [(1, _CALL)]
    state = _script(state, moves)
    hist = _project(state)
    ctx = _replay_contexts(hist, seat=1, n=len(hist.actions))[-1]
    assert ctx.street is Street.FLOP
    assert ctx.facing_raise is False, "this node must be a bare BET, not a raise"
    assert ctx.opponents > 1, (
        f"the point of this test is opponents > 1; got {ctx.opponents}"
    )

    hole = ("Ah", "5c")  # naked ace-high, no draw, on Kh7d2c
    assert strength_bucket(hole, list(ctx.board)) == (
        StrengthBucket.ACE_HIGH, DrawCategory.NONE
    )

    estimator = _postflop_action_dist(tag, hole, ctx)
    legal = _live_legal(ctx)
    live = _CaptureFirstChoices()
    sample_postflop_decision(
        tag, hole, list(ctx.board), legal, ctx.pot_bb, ctx.stack_bb, ctx.opponents,
        live,  # type: ignore[arg-type] — duck-typed capture rng
        current_bet_to=ctx.current_bet_to, street=Street.FLOP, facing_raise=False,
        latest_aggressor_contribution_bb=ctx.aggressor_contribution_bb,
    )
    assert estimator == live.dist

    saved = personas_postflop._ACE_HIGH_FLOAT_RAISE_DAMP
    try:
        personas_postflop._ACE_HIGH_FLOAT_RAISE_DAMP = 1.0
        undamped = _postflop_action_dist(tag, hole, ctx)
    finally:
        personas_postflop._ACE_HIGH_FLOAT_RAISE_DAMP = saved
    assert estimator != undamped, (
        "the multiway damp is not reaching the estimator — this parity test is "
        "vacuous as written"
    )


# ------------------------------- the estimator's capless-bracket assumption


def _short_stack_node(kind: str):
    """A real short-stack postflop node, played out on the engine, returned with
    the engine's OWN legal bracket at the moment the target seat acts.

    Seat 3 starts with 14bb, raises to 3, is re-raised to 10 and calls, so it
    reaches the flop with 4bb behind in a pot of 20.5 — far less than any
    authored sizing key would cost.

      "bet"   — checked to seat 3: CHECK + BET(min 1.0, max 4.0).
      "raise" — seat 2 bets 2: FOLD + CALL + RAISE(min 4.0, max 4.0), a bracket
                the engine COLLAPSES because the seat cannot reach a full
                min-raise. Both aggressive shapes, and both a plain cap and a
                jam, are therefore covered.
    """
    stacks = [100.0] * 9
    stacks[3] = 14.0
    dealt = _dealt_fixed(("As", "Ad"), ["Kh", "7d", "2c"])
    state = start_hand(dealt, button_seat=0, stacks_bb=stacks)
    moves = [(3, _raise_to(3.0))]
    moves += [(s, _FOLD) for s in (4, 5, 6, 7, 8, 0, 1)]
    moves += [(2, _raise_to(10.0)), (3, _CALL)]
    state = _script(state, moves)
    if kind == "bet":
        state = _script(state, [(2, _CHECK)])
        at_decision = legal_actions(state)
        state = _script(state, [(3, _CHECK)])
    else:
        state = _script(state, [(2, _bet(2.0))])
        at_decision = legal_actions(state)
        state = _script(state, [(3, _CALL)])
    hist = _project(state, starting_stacks=tuple(stacks))
    return _replay_contexts(hist, seat=3, n=len(hist.actions))[-1], at_decision


@pytest.mark.parametrize("kind", ["bet", "raise"])
@pytest.mark.parametrize("persona", ["calling_station", "passive_fish", "nit",
                                     "tag", "lag", "maniac"])
def test_no_aggressive_bracket_field_is_read_before_the_action_draw(packs, persona, kind):
    """🔴 The assumption `_legal_from_ctx` and `_live_legal` both rest on, finally
    asserted: no field of the BET/RAISE bracket reaches the merit vector.

    WHY THIS TEST EXISTS. The estimator leaves BET/RAISE min/max None on the
    argument that only the sizing draw reads them, and a capture rng never
    reaches the sizing draw. Every other parity test in this file rebuilds the
    live side the same capless way, so all of them would keep passing if that
    argument stopped being true. Improvement slice 2's T2 made it stop being
    true — it priced a bluff on the stack-capped size inside the merit
    computation, which runs before the action draw — and the villain range shown
    to the player silently diverged from the live bot by 1.2x to 1.45x at short
    stacks. The lever was withdrawn on the owner's ruling; this test is what the
    round left behind so the next one cannot land unnoticed.

    THE LIVE SIDE COMES FROM `engine.legal_actions`, which is the whole point.
    The two brackets differ materially — the engine caps the aggressive action
    at the seat's 4bb all-in-to and collapses the raise to a jam, the estimator
    supplies neither bound — so equality of the two action distributions is a
    substantive claim about the sampler rather than a comparison of a thing with
    itself. It is that difference, asserted below before the distributions are
    compared, that makes this test able to fail.

    A node with air is used because the bluff cell is where a size-linked lever
    would land; the fixture is short-stacked because that is where an
    unsupplied cap would bite hardest."""
    ctx, engine_legal = _short_stack_node(kind)
    aggressive = ActionType.BET if kind == "bet" else ActionType.RAISE
    estimator_legal = _legal_from_ctx(ctx)

    # The precondition that makes the comparison meaningful at all.
    assert ctx.street is Street.FLOP and ctx.stack_bb == pytest.approx(4.0)
    engine_bracket = {la.action: (la.min_bb, la.max_bb) for la in engine_legal}
    estimator_bracket = {la.action: (la.min_bb, la.max_bb) for la in estimator_legal}
    assert engine_bracket[aggressive] != estimator_bracket[aggressive]
    assert estimator_bracket[aggressive] == (None, None)
    assert engine_bracket[aggressive][1] == pytest.approx(4.0)
    if kind == "raise":  # the engine's jam encoding, stated rather than implied
        assert engine_bracket[ActionType.RAISE] == (4.0, 4.0)

    pack = packs[VillainType(persona)]
    hole = ("6h", "4c")  # naked air, no draw — the bluff cell
    cap = _CaptureFirstChoices()
    sample_postflop_decision(
        pack, hole, list(ctx.board), engine_legal, ctx.pot_bb, ctx.stack_bb,
        ctx.opponents,
        cap,  # type: ignore[arg-type] — duck-typed capture rng
        current_bet_to=ctx.current_bet_to, street=ctx.street,
        latest_aggressor_contribution_bb=ctx.aggressor_contribution_bb,
        facing_raise=ctx.facing_raise,
        aggressor_bet_prev_street=ctx.aggressor_bet_prev_street,
    )
    assert _postflop_action_dist(pack, hole, ctx) == cap.dist, (persona, kind)


# ---------------------------------------------- S3-T5 late-street bet lever


def _unopened_late_ctx(street: Street):
    """Seat 2's own CHECK at an UNOPENED turn or river: seat 3 opens preflop,
    seat 2 calls, and every postflop street checks through. The existing parity
    tests all sit at FACING nodes, so this is the first context in this file
    where the CHECK/BET branch of the sampler is the branch under test."""
    dealt = _dealt_fixed(("As", "Ad"), ["Kh", "7d", "2c", "9s", "3h"])
    state = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    moves = [(3, _raise_to(3.0))]
    moves += [(s, _FOLD) for s in (4, 5, 6, 7, 8, 0, 1)]
    moves += [(2, _CALL)]
    moves += [(2, _CHECK), (3, _CHECK)]  # flop checks through
    if street is Street.RIVER:
        moves += [(2, _CHECK), (3, _CHECK)]  # turn checks through
    moves += [(2, _CHECK)]  # the decision under test
    state = _script(state, moves)
    hist = _project(state)
    return _replay_contexts(hist, seat=2, n=len(hist.actions))[-1]


@pytest.mark.parametrize("street", [Street.TURN, Street.RIVER])
def test_late_street_bet_estimator_parity_unopened(packs, street):
    """S3-T5 (improvement slice 3, ticket 5 — the late-street bet lever): the
    villain range the player is shown replays the lever, because the estimator
    and the live bot call the same function.

    That is structural rather than tested-into-being, which is exactly why it
    needs a test that could fail: every other parity assertion in this file sits
    at a node where a bet is already outstanding, so none of them touches the
    unopened CHECK/BET branch the lever lives in. The lever-off distribution is
    asserted to differ from the lever-on one first, so the parity claim is not a
    comparison of two identical vectors."""
    def _dialled(value):
        pack = packs[VillainType.TAG].model_copy(deep=True)
        pack.postflop = pack.postflop.model_copy(update={"late_street_bet": value})
        return pack

    # Both sides are built explicitly. Reading the "off" side off the shipped
    # TAG pack would make this test silently vacuous the moment that pack
    # authors the field — which it now does, at 1.0.
    unlevered, levered = _dialled(None), _dialled(1.0)

    ctx = _unopened_late_ctx(street)
    assert ctx.street is street
    assert ctx.kinds == frozenset({ActionType.CHECK, ActionType.BET})
    assert ctx.to_call_bb == 0.0

    hole = ("Kd", "8d")  # top pair: bets and checks at this node, so both move
    off = _postflop_action_dist(unlevered, hole, ctx)
    on = _postflop_action_dist(levered, hole, ctx)
    assert on[ActionType.BET] > off[ActionType.BET], street

    live = _CaptureFirstChoices()
    sample_postflop_decision(
        levered, hole, list(ctx.board), _live_legal(ctx), ctx.pot_bb, ctx.stack_bb,
        ctx.opponents,
        live,  # type: ignore[arg-type] — duck-typed capture rng
        current_bet_to=ctx.current_bet_to, street=ctx.street,
        latest_aggressor_contribution_bb=ctx.aggressor_contribution_bb,
        facing_raise=ctx.facing_raise,
        aggressor_bet_prev_street=ctx.aggressor_bet_prev_street,
    )
    assert on == live.dist, street
