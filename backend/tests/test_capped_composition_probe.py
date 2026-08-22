"""S3-T3's shipped instrument: the capped-versus-uncapped composition probe.

S3-T3 is ticket 3 of improvement slice 3 (the calldown slice) of the bot-realism
flywheel. Its lever was withdrawn on review; `backend/tools/capped_composition_
probe.py` is what the ticket ships instead, so it needs a guard of its own.

These tests are STRUCTURAL. They do not pin a measured value — the probe is a
measuring instrument and pinning its readings would make every engine change a
fixture re-record for no gain. They assert the three properties a reader of its
output has to be able to rely on: that "capped" means what the report says it
means, that the identity target is the contract's formula, and that the probe
observes the engine without perturbing it.
"""

from __future__ import annotations

import random

import pytest

from app.domain.archetypes import VillainType
from app.domain.personas import load_persona_packs
from app.domain.spot import ActionType
from app.domain.table import play as play_mod
from tools import capped_composition_probe as probe_mod

pytest.importorskip("pyarrow", reason="the probe drives tools.export_analytics")


def test_identity_target_is_the_contract_bluff_share_formula():
    """`s / (1 + 2s)` — theory contract §3. The reference values in that
    section are the test: half-pot 25%, two-thirds 28.6%, pot 33%, twice 40%."""
    assert probe_mod.identity_target(0.5) == pytest.approx(0.25, abs=1e-12)
    assert probe_mod.identity_target(2 / 3) == pytest.approx(0.2857142857, abs=1e-9)
    assert probe_mod.identity_target(1.0) == pytest.approx(1 / 3, abs=1e-12)
    assert probe_mod.identity_target(2.0) == pytest.approx(0.40, abs=1e-12)
    # Monotone and bounded — a bigger wager always warrants a bigger bluff
    # share, and never more than half the range.
    xs = [probe_mod.identity_target(s / 10) for s in range(1, 200)]
    assert xs == sorted(xs)
    assert all(0.0 < x < 0.5 for x in xs)


def test_probe_does_not_perturb_the_playout_it_measures():
    """The probe re-invokes the sampler to read its action-probability vector.
    That second call runs on a throwaway RNG, so the hands played under
    measurement must be identical to the hands played without it. If this fails,
    every figure the probe reports is of a different table than production's."""
    packs = load_persona_packs()
    persona_by_seat = {i: probe_mod.RATIFIED_LINEUP[i] for i in range(9)}

    def play(n: int, seed: int) -> list:
        rng = random.Random(seed)
        out = []
        for i in range(n):
            hand_seed = rng.randrange(1_000_000_000)
            out.append(probe_mod.play_one_hand(
                rng, hand_seed, i % 9, persona_by_seat, packs)["decisions"])
        return out

    unmeasured = play(25, 4242)

    p = probe_mod._Probe()
    original = play_mod.sample_postflop_decision
    play_mod.sample_postflop_decision = p.wrap(original)
    try:
        measured = play(25, 4242)
    finally:
        play_mod.sample_postflop_decision = original

    assert measured == unmeasured
    assert sum(p.nodes.values()) > 0, "the probe recorded nothing — it saw no postflop node"


def test_capped_means_the_seat_cannot_make_its_largest_authored_size():
    """The report's whole capped-versus-uncapped split rests on this predicate,
    so it is asserted directly rather than trusted: a seat with a deep stack is
    never capped, and one whose stack is under its own smallest authored size
    always is."""
    pack = load_persona_packs()[VillainType("tag")]
    biggest = probe_mod._largest_authored_size(pack.postflop)
    assert biggest > 0

    def f_max(stack: float, pot: float) -> float:
        legal = [type("L", (), {"action": ActionType.CHECK, "min_bb": None, "max_bb": None})(),
                 type("L", (), {"action": ActionType.BET, "min_bb": 0.5, "max_bb": stack})()]
        by_kind = {la.action: la for la in legal}
        return probe_mod._max_wagerable_fraction(by_kind, pot, 0.0)

    pot = 10.0
    deep = f_max(pot * (biggest + 1.0), pot)
    assert deep >= biggest, "a deep stack must not read as capped"
    shallow = f_max(pot * 0.1, pot)
    assert shallow < biggest, "a stack under the smallest authored size must read as capped"
