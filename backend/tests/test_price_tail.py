"""R10-TAIL-a1 — the piecewise absolute-price tail above the OVERBET representative.

WHAT THIS GUARDS. `_BUCKET_ALPHA`'s top bucket (`OVERBET`, `> 1.10` pot) has no
upper edge, and α is the ONLY price-carrying input the facing branch has. So at
pre-slice HEAD a 1.51x-pot raise, a 2.33x-pot raise and a 10x-pot jam were one
identical decision node. `_price_factor` now keeps climbing above 1.5x pot with
the unbounded price ratio `(f/anchor) ** _PRICE_TAIL_K`.

METHOD — the DIRECT constructed-policy grid, never a simulator-derived or
live-corpus grid (`persona-realism.md:1893-1897`). `sample_postflop_decision`'s
action draw is its FIRST `rng.choices` call and the weights it passes are already
NORMALIZED, so the capture rng below reads exact normalized PROBABILITY vectors
with zero variance and zero domain instrumentation (the `node_trace.py:51-66`
pattern). Every assertion here is on a normalized vector, never on a raw merit.
`latest_aggressor_contribution_bb` is set equal to the bet so `faced_frac` is
EXACTLY the swept `f` (the W1-b branch).

PRE-SLICE HEAD is reproducible in-test: `(f/anchor) ** 0` is exactly 1.0, so
monkeypatching `_PRICE_TAIL_K = 0.0` restores the pre-slice engine bit-for-bit.
`test_defect_gates_fail_at_pre_slice_head` uses that to DEMONSTRATE both defect
gates failing, so this file cannot pass vacuously (the R9-3 lesson).

NOT ASSERTED HERE, by design: any absolute call/fold LEVEL. No sourced
fold-to-overbet-raise frequency exists in the contract, so `K` is a directional
seed and these gates are monotonicity + direction only (design pass §D1).
"""

from __future__ import annotations

import inspect
import random

import pytest

from app.domain import personas_postflop as pp
from app.domain.action import ActionType
from app.domain.archetypes import VillainType
from app.domain.personas import load_persona_packs
from app.domain.spot import LegalAction, Street

PERSONAS = (
    "calling_station",
    "passive_fish",
    "nit",
    "tag",
    "lag",
    "maniac",
)

# The two R10-2 tail classes. Both are rung 0 with `draw is NONE`, so the SPR
# value-commit gate can never fire on them (design pass §A4) — the sweeps below
# are commit-gate-free by construction, not by choice of SPR.
FIXTURES = {
    "AIR": (("7h", "2s"), ["Ks", "Qd", "8c"]),
    "ACE_HIGH": (("Ah", "2s"), ["Ks", "Qd", "8c"]),
}

_PACKS = load_persona_packs()


class _CaptureRng:
    """Records the FIRST `choices()` call — the action draw, whose weights are
    the normalized action probabilities — and delegates to a seeded inner rng."""

    def __init__(self, seed: int = 1) -> None:
        self._rng = random.Random(seed)
        self.population: list[ActionType] | None = None
        self.weights: list[float] | None = None

    def choices(self, population, weights, k=1):  # noqa: ANN001 — rng protocol
        if self.population is None:
            self.population = list(population)
            self.weights = list(weights)
        return self._rng.choices(population, weights=weights, k=k)


def probe(
    persona: str,
    fixture: str,
    f: float,
    *,
    facing_raise: bool = True,
    spr: float = 10.0,
    opponents: int = 1,
    pot_before: float = 10.0,
) -> tuple[float, float, float]:
    """Normalized (fold, call, raise) facing a bet/raise of `f` x the
    pre-aggression pot, heads-up, flop."""
    hole, board = FIXTURES[fixture]
    bet = f * pot_before
    pot = pot_before + bet
    stack = spr * pot
    legal = [
        LegalAction(action=ActionType.FOLD),
        LegalAction(action=ActionType.CALL, min_bb=bet),
        LegalAction(action=ActionType.RAISE, min_bb=2.0 * bet, max_bb=stack),
    ]
    cap = _CaptureRng()
    pp.sample_postflop_decision(
        _PACKS[VillainType(persona)],
        hole,
        board,
        legal,
        pot,
        stack,
        opponents,
        cap,
        current_bet_to=bet,
        is_aggressor=False,
        street=Street.FLOP,
        latest_aggressor_contribution_bb=bet,
        facing_raise=facing_raise,
    )
    assert cap.weights is not None, "zero-total-merit fallback — probe is degenerate"
    probs = dict(zip(cap.population, cap.weights, strict=True))
    return (probs[ActionType.FOLD], probs[ActionType.CALL], probs[ActionType.RAISE])


def p_call(*args, **kwargs) -> float:
    return probe(*args, **kwargs)[1]


def p_raise(*args, **kwargs) -> float:
    return probe(*args, **kwargs)[2]


@pytest.fixture
def head(monkeypatch):
    """Pre-slice HEAD: the tail factor becomes exactly 1.0 everywhere."""
    monkeypatch.setattr(pp, "_PRICE_TAIL_K", 0.0)


ANCHOR = 1.5
TAIL_GRID = (1.51, 1.80, 2.33, 4.00, 10.00)
SUB_ANCHOR_GRID = (0.30, 0.55, 0.90, 1.10, 1.11, 1.45, 1.50)

# Frozen PRE-SLICE HEAD vectors, full precision, measured on this grid before the
# mechanism landed (design pass §A2 reproduces the 4-dp rows). The `1.11`/`1.45`/
# `1.50` rows are the alpha-ceiling leg: the passive fish has only 0.0078 of
# headroom against the RES-D fold-ceiling at a faced 1.5x (`personas_postflop.py:
# 344-346`), so those cells must stay byte-identical.
#
# RE-RECORDED for the de-robotization slice's T5 (2026-08-16, slice-authorized),
# and the reason is worth stating because "a bet-SIZE ticket moved a FACING-node
# vector" reads like a bug. It is not. A persona's own size distribution scales
# its bluff rate: `personas_postflop` ~:910 multiplies `bluff_mass` by
# E_s[_bluff_size_factor(s)] over that persona's authored sizing, which is the
# F2 joint law ("bigger bets carry proportionally more bluffs"). A raise is a
# legal action at these facing nodes, so the bluff cell fires and the vector
# shifts.
#
# Exactly the two packs whose sizing moved toward LARGER are the two that moved
# here — the station (+7.1% bluff mass) and the fish (+10.0%). No other
# persona's rows are in this fixture to move, but the direction and the sign
# both match the coupling, which is what distinguishes this from a stray engine
# change.
#
# What did NOT change is the thing this file exists to demonstrate: the plateau
# below is still EXACTLY flat across all five tail prices — asserted at
# re-record time rather than assumed. The defect's level moved; the defect
# did not.
HEAD_VECTORS: dict[tuple[str, str, float, bool], tuple[float, float, float]] = {
    ("calling_station", "AIR", 0.3, True): (0.32863826529923007, 0.654348669298996, 0.017013065401773896),  # noqa: E501
    ("calling_station", "AIR", 0.55, True): (0.4442977556616227, 0.5416201211875021, 0.014082123150875054),  # noqa: E501
    ("calling_station", "AIR", 0.9, True): (0.512369577736908, 0.47527331604589856, 0.01235710621719336),  # noqa: E501
    ("calling_station", "AIR", 1.1, True): (0.512369577736908, 0.47527331604589856, 0.01235710621719336),  # noqa: E501
    ("calling_station", "AIR", 1.11, True): (0.5853964944886938, 0.4040969839291483, 0.010506521582157854),  # noqa: E501
    ("calling_station", "AIR", 1.45, True): (0.5853964944886938, 0.4040969839291483, 0.010506521582157854),  # noqa: E501
    ("calling_station", "AIR", 1.5, True): (0.5853964944886938, 0.4040969839291483, 0.010506521582157854),  # noqa: E501
    ("calling_station", "ACE_HIGH", 0.3, True): (0.1264368676453414, 0.8653813450919708, 0.008181787262687723),  # noqa: E501
    ("calling_station", "ACE_HIGH", 0.55, True): (0.1912011071454585, 0.8012236870857309, 0.007575205768810545),  # noqa: E501
    ("calling_station", "ACE_HIGH", 0.9, True): (0.23703606892350199, 0.7558180152955222, 0.007145915780975845),  # noqa: E501
    ("calling_station", "ACE_HIGH", 1.1, True): (0.23703606892350199, 0.7558180152955222, 0.007145915780975845),  # noqa: E501
    ("calling_station", "ACE_HIGH", 1.11, True): (0.2945223672964382, 0.6988701332618138, 0.006607499441748056),  # noqa: E501
    ("calling_station", "ACE_HIGH", 1.45, True): (0.2945223672964382, 0.6988701332618138, 0.006607499441748056),  # noqa: E501
    ("calling_station", "ACE_HIGH", 1.5, True): (0.2945223672964382, 0.6988701332618138, 0.006607499441748056),  # noqa: E501
    ("calling_station", "ACE_HIGH", 1.11, False): (0.18737869692917716, 0.8084175319049173, 0.004203771165905569),  # noqa: E501
    ("calling_station", "ACE_HIGH", 1.45, False): (0.18737869692917716, 0.8084175319049173, 0.004203771165905569),  # noqa: E501
    ("calling_station", "ACE_HIGH", 1.5, False): (0.18737869692917716, 0.8084175319049173, 0.004203771165905569),  # noqa: E501
    ("passive_fish", "AIR", 1.11, False): (0.9369141963528489, 0.031269910541074135, 0.03181589310607702),  # noqa: E501
    ("passive_fish", "AIR", 1.45, False): (0.9369141963528489, 0.031269910541074135, 0.03181589310607702),  # noqa: E501
    ("passive_fish", "AIR", 1.5, False): (0.9369141963528489, 0.031269910541074135, 0.03181589310607702),  # noqa: E501
    ("passive_fish", "ACE_HIGH", 1.11, False): (0.7993323159140884, 0.1667378540940706, 0.03392982999184103),  # noqa: E501
    ("passive_fish", "ACE_HIGH", 1.45, False): (0.7993323159140884, 0.1667378540940706, 0.03392982999184103),  # noqa: E501
    ("passive_fish", "ACE_HIGH", 1.5, False): (0.7993323159140884, 0.1667378540940706, 0.03392982999184103),  # noqa: E501
}

# The plateau the mechanism exists to break, at pre-slice HEAD: identical at
# every price above 1.10x pot, forever.
HEAD_AIR_PLATEAU_CALL = 0.4040969839291483  # 0.4010
HEAD_ACE_HIGH_PLATEAU_CALL = 0.6988701332618138  # 0.6961 — the larger defect
# Maniac AIR raise share at f = 2.33 at HEAD. R10-2's specialist adjudication
# REFUTED the maniac's defect claim (0/15), so its tail resistance is collateral
# to be protected, not a target.
HEAD_MANIAC_RAISE_2_33 = 0.19216049312330027


# --------------------------------------------------------------------------
# (1) the two defect gates FAIL at pre-slice HEAD — this file cannot pass
#     vacuously.
# --------------------------------------------------------------------------


def test_defect_gates_fail_at_pre_slice_head(head):
    """DEMONSTRATION, not a preservation check. At pre-slice HEAD both gates in
    `test_defect_gate_*` below are FALSE: the tail is exactly flat, to the last
    bit, for both tail classes."""
    for fixture, plateau in (
        ("AIR", HEAD_AIR_PLATEAU_CALL),
        ("ACE_HIGH", HEAD_ACE_HIGH_PLATEAU_CALL),
    ):
        calls = [p_call("calling_station", fixture, f) for f in TAIL_GRID]
        assert calls == [plateau] * len(TAIL_GRID), (fixture, calls)
        # gate (1): P(call | 2.33) < P(call | 1.51) - 0.05  -> FALSE at HEAD
        assert not (calls[2] < calls[0] - 0.05)
        # gate (2): P(call | 4.00) < P(call | 2.33)         -> FALSE at HEAD
        assert not (calls[3] < calls[2])


def test_defect_gate_1_call_share_falls_across_the_tail():
    """(1) station, AIR/NONE, HU flop, facing a raise: the call share at a
    2.33x-pot raise is materially below the 1.51x one."""
    at_1_51 = p_call("calling_station", "AIR", 1.51)
    at_2_33 = p_call("calling_station", "AIR", 2.33)
    assert at_2_33 < at_1_51 - 0.05, (at_1_51, at_2_33)


def test_defect_gate_2_tail_is_strictly_monotone():
    """(2) strictly decreasing call share over the whole tail grid."""
    calls = [p_call("calling_station", "AIR", f) for f in TAIL_GRID]
    assert all(b < a for a, b in zip(calls, calls[1:], strict=False)), calls


def test_defect_gates_ace_high_twin():
    """The ace-high half of R10-2's tail class — the LARGER defect (HEAD plateau
    0.6992 vs AIR's 0.4044)."""
    at_1_51 = p_call("calling_station", "ACE_HIGH", 1.51)
    at_2_33 = p_call("calling_station", "ACE_HIGH", 2.33)
    assert at_2_33 < at_1_51 - 0.05, (at_1_51, at_2_33)
    calls = [p_call("calling_station", "ACE_HIGH", f) for f in TAIL_GRID]
    assert all(b < a for a, b in zip(calls, calls[1:], strict=False)), calls


# --------------------------------------------------------------------------
# (3) N-logit: the mass the ladder removes routes to FOLD, never to RAISE.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("k", [1.5, 2.0, 2.5])
@pytest.mark.parametrize("persona", PERSONAS)
@pytest.mark.parametrize("fixture", list(FIXTURES))
def test_n_logit_raise_share_never_inflates_with_price(monkeypatch, k, persona, fixture):
    """(3) At EVERY K in the declared range, for every persona and both tail
    classes: the raise share falls monotonically with price. This is structural —
    the mechanism raises the FOLD merit rather than cutting the CALL merit, so
    normalization lowers every other candidate's share. A call-merit-side
    mechanism inflates P(raise) instead; that is the pathology `N-logit` forbids
    and the reason the call merit is deliberately left price-blind."""
    monkeypatch.setattr(pp, "_PRICE_TAIL_K", k)
    raises = [p_raise(persona, fixture, f) for f in TAIL_GRID]
    assert all(b <= a for a, b in zip(raises, raises[1:], strict=False)), raises
    assert raises[2] <= raises[0]  # 2.33 vs 1.51, the gate as filed


# --------------------------------------------------------------------------
# (4) no fold floor: fold probability stays a strictly interior, emergent
#     normalization outcome — no branch asserts fold >= anything.
# --------------------------------------------------------------------------


def test_price_factor_contains_no_fold_clamp():
    """(4a) Static half: the mechanism only SCALES a merit. No clamp, floor or
    ceiling literal may appear in `_price_factor` (the A1 guardrail: no code path
    may assert fold >= anything derived from alpha/MDF)."""
    src = inspect.getsource(pp._price_factor)
    body = src.split('"""')[-1]
    for banned in ("min(", "max(", "if factor", ">=", "<="):
        assert banned not in body, banned


@pytest.mark.parametrize("persona", PERSONAS)
@pytest.mark.parametrize("fixture", list(FIXTURES))
def test_fold_probability_stays_strictly_interior(persona, fixture):
    """(4b) Measured half: across the whole swept range, up to a 100x-pot jam,
    0 < P(fold) < 1 for every persona and both facing kinds. The tail is
    unbounded in `f` and P(fold) still never reaches 1 — it is emergent."""
    for f in (*SUB_ANCHOR_GRID, *TAIL_GRID, 25.0, 100.0):
        for facing_raise in (True, False):
            fold, call, rai = probe(persona, fixture, f, facing_raise=facing_raise)
            assert 0.0 < fold < 1.0, (persona, fixture, f, facing_raise, fold)
            assert call > 0.0 and rai > 0.0
            assert fold + call + rai == pytest.approx(1.0)


# --------------------------------------------------------------------------
# (5) alpha-ceiling preservation: everything at and below the anchor is
#     byte-identical to pre-slice HEAD.
# --------------------------------------------------------------------------


def test_alpha_ceiling_sub_anchor_vectors_are_byte_identical():
    """(5) Frozen pre-slice literals, exact equality (not approx). Covers leg (a)
    — f in {0.30, 0.55, 0.90, 1.10} — and leg (b), the alpha-ceiling leg at
    f in {1.11, 1.45, 1.50} where the passive fish has 0.0078 of headroom. The
    shipped gate anchors on `f > 1.5` alone, so leg (b) holds for BOTH facing
    kinds, which is the stronger of the two forms the design pass cleared."""
    for (persona, fixture, f, facing_raise), expected in HEAD_VECTORS.items():
        got = probe(persona, fixture, f, facing_raise=facing_raise)
        assert got == expected, (persona, fixture, f, facing_raise, got, expected)


@pytest.mark.parametrize("persona", PERSONAS)
@pytest.mark.parametrize("fixture", list(FIXTURES))
def test_tail_term_is_inert_at_and_below_the_anchor(monkeypatch, persona, fixture):
    """(5) Breadth twin of the literals above: at every price <= the anchor the
    shipped engine equals the pre-slice engine exactly, for every persona, both
    tail classes and both facing kinds. Also pins CONTINUITY at the anchor — the
    tail factor is exactly x1 at f = 1.5, so the curve has no step there."""
    shipped = {
        (f, fr): probe(persona, fixture, f, facing_raise=fr)
        for f in (*SUB_ANCHOR_GRID, ANCHOR)
        for fr in (True, False)
    }
    monkeypatch.setattr(pp, "_PRICE_TAIL_K", 0.0)
    for key, vec in shipped.items():
        f, fr = key
        assert vec == probe(persona, fixture, f, facing_raise=fr), (persona, fixture, key)


# --------------------------------------------------------------------------
# (6) persona dispersion: the guard that FORCES the additive-exponent form.
# --------------------------------------------------------------------------


def test_maniac_raise_dispersion_floor_forces_the_additive_form():
    """(6) The maniac keeps at least 40% of its HEAD air-raise share against a
    2.33x-pot raise.

    Additive `e + K` (shipped) keeps the tail's cross-persona dispersion equal to
    the head's and measures 0.0923 = 0.48x HEAD at K = 2.0. The multiplicative
    `e * k` alternative MULTIPLIES the exponent spread the W2-a elasticity split
    set (station 1.21 vs legacy 2.41) and BREACHES this floor — 0.0737 measured
    in-place for `exponent * 2.0` above the anchor, 0.0290 (0.15x) for the design
    pass's variant. R10-2's specialist adjudication refuted the maniac's defect
    claim (0/15), so that collateral is a real cost, not a bonus.
    """
    floor = 0.40 * HEAD_MANIAC_RAISE_2_33
    got = p_raise("maniac", "AIR", 2.33)
    assert got >= floor, (got, floor)


def test_dispersion_floor_bounds_k_inside_the_declared_range(monkeypatch):
    """Why K is 2.0 and not the top of its [1.5, 2.5] range: at K = 2.5 the
    dispersion floor above is BREACHED (measured 0.0757 vs a 0.0769 floor). The
    range top is not a safe value; this pins that fact so a later re-fit does not
    walk into it."""
    floor = 0.40 * HEAD_MANIAC_RAISE_2_33
    monkeypatch.setattr(pp, "_PRICE_TAIL_K", 2.5)
    assert p_raise("maniac", "AIR", 2.33) < floor


def test_authored_sizing_keys_never_exceed_the_tail_anchor():
    """Anchor-staleness guard (theory fan-in LOW): the byte-identity-by-
    construction argument for `_PRICE_TAIL_ANCHOR = 1.5` rests on a CONTENT
    fact — no pack authors a bet-size key above 1.5× pot — that lives in
    `content/personas/*.json` and could drift silently. Trip loudly if a
    future pack edit authors a bigger size (raise-compounding can still
    produce f > 1.5 organically; that is the tail's intended domain)."""
    from app.domain.personas import load_persona_packs

    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    for vt, pack in packs.items():
        pf = pack.postflop
        keys = set(pf.sizing or {})
        for node_sizing in (pf.sizing_by_node or {}).values():
            keys |= set(node_sizing)
        biggest = max(float(k) for k in keys)
        assert biggest <= pp._PRICE_TAIL_ANCHOR + 1e-9, (
            f"{vt.value}: authored sizing key {biggest} exceeds the tail anchor"
        )
