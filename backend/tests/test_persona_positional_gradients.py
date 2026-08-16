"""The seat splits must change behaviour, not just node structure.

Spec §7.2 test 4. The two statistical gates cannot see this: neither
`rule1_label_and_separation` nor `rule4_determinism` conditions on position, so
both would pass a split that authored nine identical nodes. The pack-invariant
suite next door proves a split cannot silently DROP a seat; this file proves a
split cannot silently SAY NOTHING.

How the distributions are obtained
----------------------------------
By driving `sample_preflop_action` itself with `range_estimate._CaptureRng`,
the duck-typed stand-in that records the distribution of the first `choices()`
call. The sampler makes exactly one such call, so what is captured is the real
authored distribution, arrived at through the real first-match-wins node scan
and mix scan.

This matters more than it looks. A test that re-implemented the scan would pass
whether or not the sampler agreed with it, which is precisely how a pack edit
can measure as working while the engine ignores it. Nothing here knows the node
layout; it asks the sampler what it would do.
"""

from __future__ import annotations

import pytest

from app.domain.content.notation import all_hands
from app.domain.personas import load_persona_packs, sample_preflop_action
from app.domain.spot import Card, Position
from app.domain.table.range_estimate import _CaptureRng

# All 169 classes, from the same parser the packs are authored against, so this
# cannot drift from what a `combos` string can name.
CLASSES = sorted(all_hands())


def _cards(hand_class: str) -> tuple[Card, Card]:
    """A representative two-card hand for a class like "AKs", "AKo" or "77".

    Any representative works: the sampler keys on `hole_cards_to_class`, which
    reduces a hand to exactly this class.
    """
    hi, lo = hand_class[0], hand_class[1]
    if len(hand_class) == 2:  # a pair cannot be suited
        return f"{hi}h", f"{lo}s"
    return (f"{hi}h", f"{lo}h") if hand_class.endswith("s") else (f"{hi}h", f"{lo}s")


def _distribution(pack, facing: str, seat: Position, hand_class: str,
                  is_opener: bool) -> dict[str, float]:
    """What the sampler would draw from for this exact decision.

    An empty capture means no mix matched and the sampler returned fold at
    weight 1.0 without drawing — the implicit-fold path, which is a real
    distribution and must be reported as one rather than skipped.
    """
    rng = _CaptureRng()
    sample_preflop_action(pack, seat, facing, _cards(hand_class), rng,
                          is_opener=is_opener)
    if rng.population is None:
        return {"fold": 1.0}
    dist = dict(zip(rng.population, rng.weights, strict=True))
    remainder = 1.0 - sum(dist.values())
    if remainder > 1e-9:
        dist["fold"] = dist.get("fold", 0.0) + remainder
    return dist


def _total_variation(a: dict[str, float], b: dict[str, float]) -> float:
    return 0.5 * sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in set(a) | set(b))


# The seat splits this ticket authored, as (persona, facing, is_opener) and the
# pair of seats whose answers must differ. NAMED pairs rather than "some two
# seats differ anywhere", so a split that varies in a corner nobody reaches
# cannot satisfy this.
DECLARED_PAIRS = [
    ("tag", "vs_rfi", False, Position.BB, Position.UTG1),
    ("tag", "vs_rfi", False, Position.BTN, Position.SB),
    ("tag", "vs_limpers", False, Position.BTN, Position.LJ),
    ("tag", "vs_3bet", True, Position.BTN, Position.SB),
    ("lag", "vs_rfi", False, Position.BB, Position.UTG2),
    ("lag", "vs_rfi", False, Position.CO, Position.SB),
    ("lag", "vs_limpers", False, Position.CO, Position.HJ),
    ("lag", "vs_3bet", True, Position.BB, Position.BTN),
    ("nit", "vs_rfi", False, Position.BB, Position.HJ),
    ("nit", "vs_rfi", False, Position.CO, Position.SB),
    ("nit", "vs_limpers", False, Position.BTN, Position.LJ),
    ("nit", "vs_3bet", False, Position.CO, Position.BB),
    ("maniac", "vs_rfi", False, Position.BB, Position.LJ),
    ("maniac", "vs_rfi", False, Position.BTN, Position.SB),
    ("maniac", "vs_3bet", True, Position.SB, Position.CO),
    ("calling_station", "vs_rfi", False, Position.BB, Position.CO),
    ("passive_fish", "vs_rfi", False, Position.SB, Position.BTN),
]

# A pair qualifies only if some hand class is played materially differently.
# Total variation, so a shift between two continuing actions counts and a
# rounding-level nudge does not.
MIN_TOTAL_VARIATION = 0.15


@pytest.fixture(scope="module")
def packs() -> dict:
    return load_persona_packs()


@pytest.mark.parametrize(
    ("persona", "facing", "is_opener", "left", "right"),
    DECLARED_PAIRS,
    ids=[f"{p}-{f}-{a.value}v{b.value}" for p, f, _, a, b in DECLARED_PAIRS],
)
def test_declared_seat_pairs_are_played_differently(
        packs, persona, facing, is_opener, left, right):
    pack = packs[persona]
    biggest = 0.0
    worst_class = None
    for hand_class in CLASSES:
        gap = _total_variation(
            _distribution(pack, facing, left, hand_class, is_opener),
            _distribution(pack, facing, right, hand_class, is_opener))
        if gap > biggest:
            biggest, worst_class = gap, hand_class
    assert biggest >= MIN_TOTAL_VARIATION, (
        f"{persona} answers {facing} the same from {left.value} and "
        f"{right.value}: the largest per-hand difference is {biggest:.3f} "
        f"(on {worst_class}), under the {MIN_TOTAL_VARIATION} floor. The nodes "
        f"were split but the numbers were not.")


def test_the_gradient_check_fails_on_a_split_that_says_nothing(packs):
    """Negative case. Copying one band's mixes over another's is the way a
    seat split looks done and does nothing; it must not pass."""
    pack = packs["tag"].model_copy(deep=True)
    nodes = [n for n in pack.preflop if n.facing == "vs_rfi"]
    assert len(nodes) > 1, "fixture assumption: tag's vs_rfi is split by seat"
    for node in nodes[1:]:
        node.mixes = [m.model_copy(deep=True) for m in nodes[0].mixes]
    biggest = max(
        _total_variation(
            _distribution(pack, "vs_rfi", Position.BB, hand_class, False),
            _distribution(pack, "vs_rfi", Position.UTG1, hand_class, False))
        for hand_class in CLASSES)
    assert biggest < MIN_TOTAL_VARIATION, (
        "flattening every band must leave no per-hand difference to find")


def test_no_seat_answers_a_split_facing_by_folding_everything(packs):
    """The omitted-seat trap from a different angle.

    `test_persona_pack_invariants` proves a node matches for every seat. This
    proves the match is not the implicit-fold path in disguise — a node that
    exists but whose mixes cover nothing leaves the seat folding 100%, which
    node validation permits and the statistical gates would never notice.
    """
    dead = []
    for persona, facing, is_opener, *_ in DECLARED_PAIRS:
        pack = packs[persona]
        for seat in Position:
            plays = any(
                sum(v for k, v in _distribution(
                    pack, facing, seat, hand_class, is_opener).items()
                    if k != "fold") > 1e-9
                for hand_class in CLASSES)
            if not plays:
                dead.append(f"{persona} folds 100% at {facing} from {seat.value}")
    assert not dead, "\n".join(dead)
