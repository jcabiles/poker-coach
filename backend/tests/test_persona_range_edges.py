"""Range boundaries must be ramps, not steps.

Spec §7.2 tests 2, 3 and 6. Neither statistical gate can see this: rule 1
scores ten frequency statistics that a step function satisfies as happily as a
gradient, and rule 4 groups on action type. A persona that plays a 56%-wide
block of hands one way every single time, and everything outside it never, is
the most legible machine signature on the roster — and it passes both gates.

Two claims are made here, and they are deliberately different in kind:

`test_no_wide_block_is_played_one_way_every_time` is a general invariant with
no list to maintain. It is what actually stops the defect coming back.

The declared tables below exist for the two things a general invariant cannot
express: that the specific nodes this slice softened really did get a graded
edge (rather than a token mix somewhere harmless), and that softening an edge
did not quietly rewrite the tier above it.

Why `fold` is excluded from the width rule
------------------------------------------
A range has to end somewhere, and folding the bottom 45% of hands to a 3-bet
is correct poker rather than a tell. What reads as a machine is playing a wide
band of hands the SAME way every time. The rule therefore asks only about
non-fold actions.
"""

from __future__ import annotations

import pytest

from app.domain.personas import _combos, load_persona_packs

# Above this share of the 1,326-combo deck, a single-action block stops being a
# tier a person would genuinely always play (premiums, broadways) and starts
# being a range played mechanically. The widest legitimate one on the roster is
# lag's isolation core at 10.71%; the blocks this slice softened ran 19% to 56%.
MAX_DETERMINISTIC_WIDTH = 0.15

# The emitted opening ladders are out of scope for this slice and are generated
# from `content/personas/ladders/*.json` under their own proving tests, so their
# core tiers are wide by construction. Each already carries a 0.4-0.5 tail band
# beneath it, so those boundaries are ramps too — just ones this file does not
# own.
EMITTED_LADDERS = {("tag", "unopened"), ("lag", "unopened"), ("nit", "unopened")}


def _combo_count(hand_class: str) -> int:
    return 6 if len(hand_class) == 2 else (4 if hand_class.endswith("s") else 12)


def _width(combos: str, already_seen: frozenset[str]) -> float:
    """Share of the deck a mix actually OWNS under first-match-wins."""
    fresh = _combos(combos) - already_seen
    return sum(_combo_count(c) for c in fresh) / 1326.0


@pytest.fixture(scope="module")
def packs() -> dict:
    return load_persona_packs()


def _wide_deterministic_blocks(pack) -> list[str]:
    """Deterministic mass PER NODE AND ACTION, not per mix.

    Summing matters. Review found that a per-mix rule is trivially evaded: the
    calling station's 56%-wide `call` block could be written as four separate
    14% mixes, each under any per-mix threshold, with behaviour identical to
    the step function this file exists to forbid. What makes a range read as a
    machine is the total mass answered one way, however it is spelled.
    """
    out = []
    for node in pack.preflop:
        if (pack.persona.value, node.facing) in EMITTED_LADDERS:
            continue
        seen: set[str] = set()
        deterministic: dict[str, float] = {}
        example: dict[str, str] = {}
        for mix in node.mixes:
            width = _width(mix.combos, frozenset(seen))
            seen |= _combos(mix.combos)
            actions = [a for a in mix.weights if a != "fold"]
            if len(actions) != 1 or mix.weights[actions[0]] < 0.99:
                continue
            deterministic[actions[0]] = deterministic.get(actions[0], 0.0) + width
            example.setdefault(actions[0], mix.combos[:60])
        for action, mass in deterministic.items():
            if mass > MAX_DETERMINISTIC_WIDTH:
                where = (f"{pack.persona.value} {node.facing} "
                         f"{[p.value for p in node.positions] if node.positions else '*'}")
                out.append(
                    f"{where}: {mass * 100:.2f}% of the deck always plays "
                    f"{action!r} — e.g. {example[action]}")
    return out


def test_no_wide_block_is_played_one_way_every_time(packs):
    violations = [v for pack in packs.values() for v in _wide_deterministic_blocks(pack)]
    assert not violations, "\n".join(violations)


def test_the_width_rule_can_fail(packs):
    """Negative case. Before this slice the calling station answered 56% of the
    deck with `call` at weight 1.0 facing a raise; restoring that must fail."""
    pack = packs["calling_station"].model_copy(deep=True)
    node = next(n for n in pack.preflop
                if n.facing == "vs_rfi" and n.positions is not None)
    node.mixes[1].weights = {"call": 1.0}
    violations = _wide_deterministic_blocks(pack)
    assert violations and "vs_rfi" in violations[0], violations


def test_the_width_rule_cannot_be_evaded_by_splitting_the_block(packs):
    """The evasion review found, pinned as its own case.

    Spelling one 56% deterministic block as six sub-threshold mixes changes
    nothing about how the persona plays, so it must not change the verdict.
    """
    pack = packs["calling_station"].model_copy(deep=True)
    node = next(n for n in pack.preflop
                if n.facing == "vs_rfi" and n.positions is not None)
    core = node.mixes[1]
    quarters = ["22+, A2s+, K2s+", "Q2s+, J2s+, T2s+",
                "92s+, 82s+, 72s+, 62s+, 54s, 53s, 52s, 43s, 42s, 32s",
                "A2o+", "K7o+, Q7o+", "J8o+, T8o+, 98o, 87o"]
    node.mixes = ([node.mixes[0]]
                  + [core.model_copy(update={"combos": c, "weights": {"call": 1.0}})
                     for c in quarters]
                  + list(node.mixes[2:]))
    for spelling in quarters:
        assert _width(spelling, frozenset()) < MAX_DETERMINISTIC_WIDTH, (
            f"fixture assumption: {spelling[:30]} must be under the per-mix "
            f"threshold, or this test proves nothing")
    violations = _wide_deterministic_blocks(pack)
    assert violations and "vs_rfi" in violations[0], (
        "sub-threshold mixes summing past the threshold must still fail")


# (persona, facing, is the node position-explicit) -> the boundary this slice
# softened. Listed rather than inferred so a node that quietly loses its ramp
# is a failure and not just an absence.
SOFTENED = [
    ("calling_station", "unopened", ["UTG"]),
    ("calling_station", "unopened", None),
    ("calling_station", "vs_limpers", None),
    ("calling_station", "vs_rfi", ["BB"]),
    ("calling_station", "vs_rfi", ["SB"]),
    ("calling_station", "vs_rfi", None),
    ("passive_fish", "unopened", ["UTG"]),
    ("passive_fish", "unopened", None),
    ("passive_fish", "vs_limpers", None),
    ("passive_fish", "vs_rfi", ["BB"]),
    ("passive_fish", "vs_rfi", ["SB"]),
    ("passive_fish", "vs_rfi", None),
    ("maniac", "vs_limpers", ["HJ", "CO", "BTN", "SB"]),
    ("maniac", "vs_limpers", None),
]


def _node(pack, facing, positions):
    for node in pack.preflop:
        got = [p.value for p in node.positions] if node.positions else None
        if node.facing == facing and got == positions:
            return node
    return None


@pytest.mark.parametrize(("persona", "facing", "positions"), SOFTENED,
                         ids=[f"{p}-{f}-{'-'.join(x) if x else 'wildcard'}"
                              for p, f, x in SOFTENED])
def test_softened_nodes_end_in_a_graded_edge(packs, persona, facing, positions):
    """The outermost band a node plays must be a mix, and the node must offer
    at least three distinct continue probabilities — core, middle, fringe.

    Two distinct values would be satisfied by bolting one token mix onto an
    otherwise unchanged step function, which is exactly the shape this slice
    exists to remove.
    """
    node = _node(packs[persona], facing, positions)
    assert node is not None, f"{persona} lost its {facing} node for {positions}"
    continues, seen = [], set()
    for mix in node.mixes:
        if _width(mix.combos, frozenset(seen)) <= 0:
            seen |= _combos(mix.combos)
            continue
        seen |= _combos(mix.combos)
        continues.append(round(sum(w for a, w in mix.weights.items() if a != "fold"), 6))
    assert continues, f"{persona} {facing} {positions} plays nothing at all"
    assert 0.0 < continues[-1] < 1.0, (
        f"{persona} {facing} {positions}: the outermost band plays at "
        f"{continues[-1]} — the boundary is still a step")
    # Count only levels STRICTLY between 0 and 1. Counting every distinct level
    # let the untouched premium tier — always 1.0 — supply one of the three, so
    # a node that got exactly one softened step passed as a ramp. Review caught
    # this; the premium tier is pinned separately below and is not evidence of
    # a graded edge.
    graded = {c for c in continues if 0.0 < c < 1.0}
    assert len(graded) >= 2, (
        f"{persona} {facing} {positions}: continue levels {sorted(set(continues))} "
        f"contain only {sorted(graded)} strictly between 0 and 1 — that is one "
        f"step, not a ramp. The premium tier at 1.0 does not count.")


# The tier ABOVE each softened block, pinned byte-for-byte. Softening an edge
# must not reach into the range's core: these are the premium mixes that sit
# first in their node and were not touched.
PINNED_CORES = {
    ("calling_station", "unopened", "UTG"): ("AA, KK, AKs", {"raise": 0.5, "limp": 0.5}),
    ("calling_station", "unopened", "*"): ("AA, KK, AKs", {"raise": 0.5, "limp": 0.5}),
    ("calling_station", "vs_limpers", "*"): ("AA, KK", {"raise": 1.0}),
    ("calling_station", "vs_rfi", "BB"): ("AA", {"3bet": 0.4, "call": 0.6}),
    ("calling_station", "vs_rfi", "SB"): ("AA", {"3bet": 0.4, "call": 0.6}),
    ("calling_station", "vs_rfi", "*"): ("AA", {"3bet": 0.4, "call": 0.6}),
    ("passive_fish", "unopened", "UTG"): ("QQ+, AKs, AKo", {"raise": 1.0}),
    ("passive_fish", "unopened", "*"): ("TT+, AQs+, AKo", {"raise": 1.0}),
    ("passive_fish", "vs_limpers", "*"): ("QQ+, AKs, AKo", {"raise": 1.0}),
    ("passive_fish", "vs_rfi", "BB"): ("AA, KK", {"3bet": 1.0}),
    ("passive_fish", "vs_rfi", "SB"): ("AA, KK", {"3bet": 1.0}),
    ("passive_fish", "vs_rfi", "*"): ("AA, KK", {"3bet": 1.0}),
}


def test_softening_an_edge_did_not_move_the_core(packs):
    wrong = []
    for (persona, facing, pos), (combos, weights) in PINNED_CORES.items():
        positions = None if pos == "*" else pos.split(",")
        node = _node(packs[persona], facing, positions)
        assert node is not None, f"{persona} {facing} {pos} is missing"
        first = node.mixes[0]
        if first.combos != combos or dict(first.weights) != weights:
            wrong.append(f"{persona} {facing} {pos}: core is now "
                         f"{first.combos!r} {dict(first.weights)}")
    assert not wrong, "\n".join(wrong)
