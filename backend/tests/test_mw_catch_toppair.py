"""R10-TAIL-b1 — TOP_PAIR joins the multiway bluff-catch class.

WHAT THIS GUARDS. `_MW_CATCH_TIGHTEN ** max(opponents-1, 0)` raises the fold
merit of bluff-catch-class hands facing aggression as the field grows, but the
class (`_MW_CATCH_BUCKETS`) stopped at MIDDLE_PAIR — so a station called a
4-way raise holding bare top pair exactly as often as a heads-up one. This
slice adds `TOP_PAIR` to the class. Base stays 1.15 (directional, unsourced —
design pass §D1); no other mechanism changes.

METHOD — the DIRECT constructed-policy grid (the `test_price_tail.py` /
`node_trace.py:51-66` capture pattern): `sample_postflop_decision`'s action
draw is its FIRST `rng.choices` call and the weights are already NORMALIZED,
so the capture rng reads exact probability vectors with zero variance. Every
assertion is on a normalized vector, never a raw merit.

PRE-SLICE HEAD is reproducible in-test: monkeypatching `_MW_CATCH_BUCKETS`
back to the 3-bucket tuple restores the pre-slice engine bit-for-bit, and
`test_defect_gates_fail_at_pre_slice_head` DEMONSTRATES both defect gates
failing there, so this file cannot pass vacuously (the R9-3 lesson).

FIXTURE CLASSIFICATION IS ASSERTED, not assumed (design pass §D5): each
constructed hand's bucket and draw category are checked in-test, so a
taxonomy drift (e.g. a fixture silently classing TWO_PAIR_PLUS) fails loudly
here instead of quietly testing the wrong rung.

NON-COVERAGE, deliberate: `OVERPAIR_TPTK` and `TWO_PAIR_PLUS` stay OUTSIDE
the catch class — their multiway pile-up defect is W4-a's (contract §4 P6),
and the byte-identity tests below prove this slice did not silently claim it.

NOT ASSERTED HERE, by design: any absolute call/fold LEVEL — no sourced
per-headcount defense frequency exists in the contract, so the gates are
monotonicity + direction only (design pass §D1).

DRAW-CARRYING TOP_PAIR (Codex review C-2, accepted): the class mechanic is
bucket-keyed, so TOP_PAIR + a live draw also tightens multiway — exactly as
the pre-existing class members always have (MIDDLE_PAIR + draw tightens too).
The draw call/raise bonuses still apply after the tighten, so a draw-carrying
combo remains looser than its bare twin at every headcount. Accepted as
inherent class semantics, not restricted to draw-NONE; on the W4-b
observation list with the base-magnitude fit.
"""

from __future__ import annotations

import random

import pytest

from app.domain import personas_postflop as pp
from app.domain.action import ActionType
from app.domain.archetypes import VillainType
from app.domain.personas import load_persona_packs
from app.domain.personas_postflop import DrawCategory, StrengthBucket
from app.domain.spot import LegalAction, Street

PERSONAS = (
    "calling_station",
    "passive_fish",
    "nit",
    "tag",
    "lag",
    "maniac",
)

# The ticket spot: TOP_PAIR / no draw (AhTh on As 7d 2c — T kicker keeps it
# below TPTK), facing a 1.37x-pot raise on the flop. Non-coverage twins:
# OVERPAIR_TPTK (KhKs on Qs 7d 2c) and TWO_PAIR_PLUS (Ah7h on As 7d 2c).
# All three are draw-NONE by construction (no flush/straight backdoor on
# these boards), so the draw bonus paths are inert.
FIXTURES = {
    "TOP_PAIR": (("Ah", "Th"), ["As", "7d", "2c"]),
    "OVERPAIR_TPTK": (("Kh", "Ks"), ["Qs", "7d", "2c"]),
    "TWO_PAIR_PLUS": (("Ah", "7h"), ["As", "7d", "2c"]),
}

_PACKS = load_persona_packs()

# Pre-slice HEAD tuple — monkeypatch target for the demonstration tests.
_HEAD_BUCKETS = (
    StrengthBucket.AIR,
    StrengthBucket.ACE_HIGH,
    StrengthBucket.MIDDLE_PAIR,
)

F_RAISE = 1.37
HEADCOUNTS = (1, 2, 3, 4)
# Every persona's spr_commit lies in [1.2, 3.3]; SPR 10 clears them all.
# The ⑤ confounder sweep needs an SPR below every spr_commit AND a legal
# raise bracket: min raise = 2*bet = 27.4 must not exceed stack = spr*pot =
# spr*23.7, so spr >= 1.156 (Codex review C-1 — at spr=1.0 the constructed
# raise node was impossible, min_bb > max_bb). 1.19 satisfies both:
# 1.156 <= 1.19 < 1.2 = min(spr_commit).
SPR_ABOVE = 10.0
SPR_BELOW = 1.19


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
    *,
    opponents: int,
    spr: float = SPR_ABOVE,
    f: float = F_RAISE,
    pot_before: float = 10.0,
) -> tuple[float, float, float]:
    """Normalized (fold, call, raise) facing a raise of `f` x the
    pre-aggression pot on the flop with `opponents` live opponents."""
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
        facing_raise=True,
    )
    assert cap.weights is not None, "zero-total-merit fallback — probe is degenerate"
    probs = dict(zip(cap.population, cap.weights, strict=True))
    return (probs[ActionType.FOLD], probs[ActionType.CALL], probs[ActionType.RAISE])


def p_fold(*args, **kwargs) -> float:
    return probe(*args, **kwargs)[0]


def p_call(*args, **kwargs) -> float:
    return probe(*args, **kwargs)[1]


def p_raise(*args, **kwargs) -> float:
    return probe(*args, **kwargs)[2]


@pytest.fixture
def head(monkeypatch):
    """Pre-slice HEAD: TOP_PAIR back out of the catch class."""
    monkeypatch.setattr(pp, "_MW_CATCH_BUCKETS", _HEAD_BUCKETS)


# --- fixture taxonomy guard (D5) -------------------------------------------


@pytest.mark.parametrize(
    "fixture, want",
    [
        ("TOP_PAIR", StrengthBucket.TOP_PAIR),
        ("OVERPAIR_TPTK", StrengthBucket.OVERPAIR_TPTK),
        ("TWO_PAIR_PLUS", StrengthBucket.TWO_PAIR_PLUS),
    ],
)
def test_fixture_buckets_are_what_they_claim(fixture, want):
    hole, board = FIXTURES[fixture]
    assert pp._made_bucket(hole, board) is want
    assert pp._draw_category(hole, board) is DrawCategory.NONE


def test_catch_class_membership_is_exactly_the_four_buckets():
    assert pp._MW_CATCH_BUCKETS == (
        StrengthBucket.AIR,
        StrengthBucket.ACE_HIGH,
        StrengthBucket.MIDDLE_PAIR,
        StrengthBucket.TOP_PAIR,
    )


# --- HEAD demonstration (the file cannot pass vacuously) --------------------


def test_defect_gates_fail_at_pre_slice_head(head):
    """At pre-slice HEAD both defect gates FAIL: the station's call share and
    every persona's fold share are FLAT across the headcount sweep."""
    flat_call = p_call("calling_station", "TOP_PAIR", opponents=1)
    assert p_call("calling_station", "TOP_PAIR", opponents=4) == pytest.approx(
        flat_call, abs=1e-12
    )
    for persona in ("calling_station", "passive_fish", "nit"):
        folds = [p_fold(persona, "TOP_PAIR", opponents=n) for n in HEADCOUNTS]
        assert folds == pytest.approx([folds[0]] * len(HEADCOUNTS), abs=1e-12)


# --- defect gates ① ② -------------------------------------------------------


def test_defect_gate_1_station_call_share_falls_with_headcount():
    assert p_call("calling_station", "TOP_PAIR", opponents=4) < (
        p_call("calling_station", "TOP_PAIR", opponents=1) - 0.005
    )


@pytest.mark.parametrize("persona", ("calling_station", "passive_fish", "nit"))
def test_defect_gate_2_fold_share_strictly_increases_with_headcount(persona):
    folds = [p_fold(persona, "TOP_PAIR", opponents=n) for n in HEADCOUNTS]
    assert all(a < b for a, b in zip(folds, folds[1:], strict=False)), folds


# --- guards ③ ④ ⑤ -----------------------------------------------------------


@pytest.mark.parametrize("persona", PERSONAS)
def test_n_logit_raise_share_never_inflates_with_headcount(persona):
    assert p_raise(persona, "TOP_PAIR", opponents=4) <= p_raise(
        persona, "TOP_PAIR", opponents=1
    ) + 1e-12


@pytest.mark.parametrize("persona", PERSONAS)
def test_hu_vector_byte_identical_to_head(persona, monkeypatch):
    """Heads-up (opponents=1) the tighten exponent is 0, so the n=1 vector is
    byte-identical to pre-slice HEAD for every persona."""
    new = probe(persona, "TOP_PAIR", opponents=1)
    monkeypatch.setattr(pp, "_MW_CATCH_BUCKETS", _HEAD_BUCKETS)
    old = probe(persona, "TOP_PAIR", opponents=1)
    assert new == old


def test_confounder_guard_gates_hold_below_spr_commit():
    """① and ② hold with SPR below every persona's spr_commit: TOP_PAIR is
    below the OVERPAIR_TPTK commit rung and draw-NONE, so the value-commit
    gate never fires on it and the mechanism is not riding the commit gate."""
    assert p_call("calling_station", "TOP_PAIR", opponents=4, spr=SPR_BELOW) < (
        p_call("calling_station", "TOP_PAIR", opponents=1, spr=SPR_BELOW) - 0.005
    )
    for persona in ("calling_station", "passive_fish", "nit"):
        folds = [
            p_fold(persona, "TOP_PAIR", opponents=n, spr=SPR_BELOW) for n in HEADCOUNTS
        ]
        assert all(a < b for a, b in zip(folds, folds[1:], strict=False)), (
            persona,
            folds,
        )


# --- non-coverage ⑥ ---------------------------------------------------------


@pytest.mark.parametrize("persona", PERSONAS)
@pytest.mark.parametrize("fixture", ("OVERPAIR_TPTK", "TWO_PAIR_PLUS"))
@pytest.mark.parametrize("spr", (SPR_ABOVE, SPR_BELOW))
def test_non_coverage_stronger_rungs_byte_identical_at_every_headcount(
    persona, fixture, spr, monkeypatch
):
    """OVERPAIR_TPTK and TWO_PAIR_PLUS vectors are byte-identical to pre-slice
    HEAD at every headcount, above AND below spr_commit — this slice does not
    silently claim the multiway pile-up class (owner: W4-a / contract §4 P6)."""
    new = [probe(persona, fixture, opponents=n, spr=spr) for n in HEADCOUNTS]
    monkeypatch.setattr(pp, "_MW_CATCH_BUCKETS", _HEAD_BUCKETS)
    old = [probe(persona, fixture, opponents=n, spr=spr) for n in HEADCOUNTS]
    assert new == old
