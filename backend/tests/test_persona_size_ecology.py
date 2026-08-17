"""Bet size must not name the bettor.

Spec §7.2 test 5's companion. Grid membership is already asserted by
`test_persona_pack_invariants.py`; what that cannot see is whether the six
personas' size distributions are DISJOINT, which is the defect this ticket
exists to remove. The 2026-08-05 re-measure put it plainly
(`remeasure-2026-08-05/report_table.md` §5): "an observant hero can read the
bettor's archetype off the bet size alone with almost no error", because SMALL
meant station or fish, LARGE meant tag/lag/nit, and OVERBET meant maniac.

Neither statistical gate can see this. Rule 1 scores ten frequency statistics
and none of them is a size; rule 4 groups on action type, not size. Both pass a
roster whose six size distributions do not overlap at all.

The quoted defect is a CLASS read, so the primary gate scores classes
----------------------------------------------------------------------
An earlier draft of this file scored per-PERSONA accuracy and was wrong to.
Adversarial review found the hole: per-persona accuracy is diluted precisely by
the two recreationals being near-identical to each other and the three regulars
being near-identical to each other, so an edit that blurs the regulars AMONG
THEMSELVES lowers the number while leaving "SMALL means recreational" untouched.
That is the no-op-shaped pass §7.2 exists to prevent. `test_no_node_lets_one_
bet_size_name_the_class` is therefore the headline gate; the per-persona
version is kept beneath it as a supporting check, not as the claim.

A rare size can be a perfect tell that an average cannot see
------------------------------------------------------------
Both accuracy statistics average over sizes, so a size used by exactly ONE
persona contributes only that persona's own small weight — while being a
certain giveaway every time it occurs. Review found this true of the shipped
packs, not merely possible: the 1.5 was authored by the maniac alone at four
nodes. `test_no_single_size_names_one_persona_outright` scores the other
quantity, the confidence of the best guess GIVEN a size was seen, and it is the
gate that catches that shape.

Why these read the AUTHORED distributions
-----------------------------------------
The realised distribution differs from the authored one — `_bluff_size_factor`
tilts the size weights on a bluff cell, and the legal-bet bracket clamps some
bets off their drawn fraction. Measuring it needs thousands of self-play hands,
which does not belong in a unit test. The authored numbers are what the pack
CLAIMS to play and are what an edit changes, so they are what a regression guard
should read. The realised measurement is in the ticket ledger, where it is the
claim being made about the roster.

**These are uniform-prior statistics and are not real-world detection rates.**
A uniform prior is deliberate: it isolates how much information the SIZE carries
about identity, which is the question, from how often each seat happens to bet,
which is a base rate. An observer who simply always guessed "maniac" would be
right about 46% of the time on realised bets while learning nothing from the
size at all.
"""

from __future__ import annotations

import pytest

from app.domain.personas import load_persona_packs

# Every node key `sizing_by_node` may carry, plus the flat fallback. Kept as a
# literal rather than read from `postflop_node_key` for the usual reason: a gate
# that sources its own scope from the module under test goes green for free the
# moment that module changes its mind.
NODES = ("flat", "cbet_dry", "cbet_wet", "cbet_mono", "turn_barrel",
         "river_value", "raise")
GRID = ("0.33", "0.5", "0.75", "1.0", "1.5")

# RES-E buckets over the authored grid keys.
BANDS = {"small": ("0.33",), "medium": ("0.5",), "large": ("0.75", "1.0")}

# The three archetype classes the re-measure's finding is phrased in.
CLASSES = {
    "recreational": ("calling_station", "passive_fish"),
    "regular": ("tag", "nit", "lag"),
    "maniac": ("maniac",),
}

# --- the three ceilings, and why each is where it is ------------------------
#
# All three are set from PRINCIPLE and then checked for margin, never fitted to
# the diff. Review caught the previous version doing the opposite: its ceiling
# sat exactly on two measured pre-ticket values, so whether it could ever have
# caught them was decided by 3e-17 of floating-point accumulation order.
#
# The governing principle is the roadmap's distinction at
# `bot-realism-flywheel.md:40-47` — a seat being recognisable as a TYPE is
# desirable, a seat being recognisable as a MACHINE is the defect. "Twice
# chance" is the reading of that line these gates use.

# Naming the CLASS from one bet size. Chance is 1/3, so this is 2x chance.
# Measured: pre-ticket 0.533-0.756, post-ticket 0.402-0.612 (margin 0.055 at
# the worst node, `raise`). It fails four of the seven pre-ticket nodes.
MAX_CLASS_TELL = 0.667

# Naming the PERSONA from one bet size. Chance is 1/6. Supporting check only —
# see the module docstring. Measured post-ticket worst 0.328 (`raise`).
MAX_PERSONA_TELL = 0.375

# Confidence of the best guess GIVEN a size was observed. 1.0 means exactly one
# persona ever makes that bet. Measured: pre-ticket four cells at 1.000,
# post-ticket worst 0.667 outside the exemption below.
MAX_SIZE_POSTERIOR = 0.70

# The one (node, size) cell allowed to exceed it, with the ruling that permits
# it. This list IS the disclosure: any other size that becomes single-persona is
# a regression, and adding a line here is a decision, not a fix.
#
# The maniac is the only pack authoring a 1.5 in its flat block, which sizes a
# LEAD. Spreading the overbet further was considered and refused: an overbet
# lead is not a habit of any other archetype, and authoring one purely to
# flatten this statistic is the trade the slice exists to refuse. The overbet
# was shared into `cbet_wet` and `turn_barrel` instead, where lag plausibly has
# one, which removed three of the four original certainty cells.
SINGLE_PERSONA_CELLS = {("flat", "1.5")}

# Every persona must put real mass in each of small, medium and large. 0.10 is a
# "can this persona make this bet at all" line, not a fitted target.
MIN_BAND_SHARE = 0.10


@pytest.fixture(scope="module")
def packs() -> dict:
    return load_persona_packs()


def _dist_at(pack, node: str) -> dict[str, float]:
    """The engine's own fallback rule, mirrored: a node override when the pack
    authored one, else the flat block (`personas_postflop._sizing_dist`)."""
    pf = pack.postflop
    return (pf.sizing_by_node or {}).get(node, pf.sizing)


def _bayes_accuracy(dists: list[dict[str, float]]) -> float:
    """Best accuracy an observer could reach identifying which of `dists`
    produced one observed size, under a uniform prior over them."""
    return sum(max(d.get(s, 0.0) for d in dists) for s in GRID) / len(dists)


def _class_dists(packs: dict, node: str) -> list[dict[str, float]]:
    out = []
    for members in CLASSES.values():
        acc: dict[str, float] = {}
        for name in members:
            for size, w in _dist_at(packs[name], node).items():
                acc[size] = acc.get(size, 0.0) + w / len(members)
        out.append(acc)
    return out


def _class_tell(packs: dict, node: str) -> float:
    return _bayes_accuracy(_class_dists(packs, node))


def _persona_tell(packs: dict, node: str) -> float:
    return _bayes_accuracy([_dist_at(p, node) for p in packs.values()])


def _size_posterior(packs: dict, node: str, size: str) -> float | None:
    dists = [_dist_at(p, node) for p in packs.values()]
    total = sum(d.get(size, 0.0) for d in dists)
    if total <= 0.0:
        return None
    return max(d.get(size, 0.0) for d in dists) / total


# --- the headline gate ------------------------------------------------------

def test_no_node_lets_one_bet_size_name_the_class(packs):
    loud = {n: round(_class_tell(packs, n), 3) for n in NODES
            if _class_tell(packs, n) > MAX_CLASS_TELL}
    assert not loud, (
        f"bet size names the archetype CLASS at {loud} — an observer guessing "
        f"recreational/regular/maniac from a single size beats the "
        f"{MAX_CLASS_TELL} ceiling (chance {1 / len(CLASSES):.3f}). Full table: "
        f"{ {n: round(_class_tell(packs, n), 3) for n in NODES} }")


def test_no_single_size_names_one_persona_outright(packs):
    loud = []
    for node in NODES:
        for size in GRID:
            if (node, size) in SINGLE_PERSONA_CELLS:
                continue
            post = _size_posterior(packs, node, size)
            if post is not None and post > MAX_SIZE_POSTERIOR:
                authors = sorted(n for n, p in packs.items()
                                 if _dist_at(p, node).get(size, 0.0) > 0)
                loud.append(f"{node} @ {size}: seeing this size identifies one "
                            f"persona with confidence {post:.2f} "
                            f"(authors: {authors})")
    assert not loud, "\n".join(loud)


def test_no_node_lets_one_bet_size_name_the_persona(packs):
    """Supporting check. Weaker than the class gate by construction — see the
    module docstring — and kept so a roster that separates the six INDIVIDUALLY
    while holding the classes together still fails something."""
    loud = {n: round(_persona_tell(packs, n), 3) for n in NODES
            if _persona_tell(packs, n) > MAX_PERSONA_TELL}
    assert not loud, (
        f"bet size names the persona at {loud} against a {MAX_PERSONA_TELL} "
        f"ceiling (chance {1 / len(packs):.3f}). Full table: "
        f"{ {n: round(_persona_tell(packs, n), 3) for n in NODES} }")


# --- negative cases ---------------------------------------------------------

_PRE_TICKET_RIVER_VALUE = {
    "tag": {"0.75": 0.55, "1.0": 0.45},
    "nit": {"0.75": 0.4, "1.0": 0.6},
    "lag": {"0.75": 0.3, "1.0": 0.5, "1.5": 0.2},
    "maniac": {"0.75": 0.3, "1.0": 0.4, "1.5": 0.3},
    "calling_station": {"0.33": 0.6, "0.5": 0.3, "0.75": 0.1},
    "passive_fish": {"0.33": 0.6, "0.5": 0.3, "0.75": 0.1},
}


def _rebuilt(packs, node, dists):
    out = {}
    for name, pack in packs.items():
        copy = pack.model_copy(deep=True)
        copy.postflop.sizing_by_node = {node: dict(dists[name])}
        out[name] = copy
    return out


def test_the_class_ceiling_can_fail(packs):
    """On the real pre-ticket numbers, not a synthetic caricature. Before this
    ticket no regular authored 0.33 at `river_value`, so a one-third-pot river
    bet identified `station or fish` with certainty."""
    pre = _rebuilt(packs, "river_value", _PRE_TICKET_RIVER_VALUE)
    assert _class_tell(pre, "river_value") > MAX_CLASS_TELL, (
        f"the pre-ticket river_value distributions read "
        f"{_class_tell(pre, 'river_value'):.3f}, which must exceed the ceiling "
        f"or the ceiling is not measuring the defect it was set against")


def test_the_posterior_gate_catches_a_size_only_one_persona_makes(packs):
    """The evasion an averaging statistic cannot see, pinned as its own case: a
    size that only one persona ever uses is a certain tell however rare it is,
    and stays invisible to both accuracy gates."""
    dists = dict(_PRE_TICKET_RIVER_VALUE)
    # Give the 1.5 to the maniac alone, as three nodes did before review.
    dists["lag"] = {"0.75": 0.35, "1.0": 0.65}
    pre = _rebuilt(packs, "river_value", dists)
    assert _size_posterior(pre, "river_value", "1.5") == pytest.approx(1.0)
    assert _class_tell(pre, "river_value") > 0.0
    loud = [s for s in GRID
            if (p := _size_posterior(pre, "river_value", s)) is not None
            and p > MAX_SIZE_POSTERIOR]
    assert "1.5" in loud, loud


def test_a_maximally_telling_roster_scores_near_one(packs):
    """Direction pin. The previous version asserted that six IDENTICAL
    distributions read exactly chance — which review showed is vacuous, since
    for identical normalised distributions the sum is 1 for any shape whatever,
    so it pinned that weights sum to 1 and nothing else. This pins the other
    end, where the statistic actually has to do work: give five personas their
    own private size and the score must go to the top of its range."""
    private = dict(zip(sorted(packs), GRID + ("1.5",), strict=True))
    dists = {name: {size: 1.0} for name, size in private.items()}
    telling = _rebuilt(packs, "river_value", dists)
    assert _persona_tell(telling, "river_value") > 0.8
    assert _class_tell(telling, "river_value") > MAX_CLASS_TELL


# --- structural floor -------------------------------------------------------

def test_every_persona_bets_small_medium_and_large(packs):
    """No persona may be unable to make an ordinary bet size.

    Read on the flat `sizing` block, and that scope is a deliberate limit rather
    than an oversight. Per-NODE the same floor is wrong: a `raise` node has no
    business carrying a third-pot option, and a nit betting three-quarters pot
    on a dry board 10% of the time is a target nobody should be held to. What
    catches a node-level hole is the posterior gate above, which fires when a
    missing size makes some OTHER persona's use of it diagnostic.

    The flat block is the right place for the blunt version: every pack has one,
    it is the distribution used whenever the seat is not the aggressor, and for
    the station and fish — who author no `sizing_by_node` at all — it is the
    distribution behind every bet they ever make.
    """
    thin = []
    for name, pack in packs.items():
        dist = pack.postflop.sizing
        for band, keys in BANDS.items():
            share = sum(dist.get(k, 0.0) for k in keys)
            if share < MIN_BAND_SHARE:
                thin.append(f"{name} bets {band} only {share:.2f} of the time "
                            f"(floor {MIN_BAND_SHARE}); its flat block is {dist}")
    assert not thin, "\n".join(thin)


def test_the_band_floor_catches_a_missing_size(packs):
    """Negative case on the real pre-ticket numbers: the maniac's flat block was
    0.75/1.0/1.5, so a maniac leading out could not make a small or a medium bet
    at all — the tell this ticket was written to remove."""
    dist = {"0.75": 0.4, "1.0": 0.35, "1.5": 0.25}
    missing = [band for band, keys in BANDS.items()
               if sum(dist.get(k, 0.0) for k in keys) < MIN_BAND_SHARE]
    assert missing == ["small", "medium"], missing


# The tier ABOVE each softened block, pinned byte-for-byte, so that re-weighting
# sizes cannot quietly rewrite a persona's premium range.
PINNED_CORES = {
    ("calling_station", "unopened", "UTG"): ("AA, KK, AKs", {"raise": 0.5, "limp": 0.5}),
    ("passive_fish", "vs_rfi", "BB"): ("AA, KK", {"3bet": 1.0}),
}


def test_a_sizing_change_did_not_touch_a_preflop_range(packs):
    """This ticket owns the `postflop` block and nothing else. The pack file
    also carries a TOP-LEVEL `sizing` block holding the preflop levers, one
    indentation level away from the postflop one — an early version of this
    ticket's own patcher rewrote that block by mistake, so the guard is here."""
    for name, pack in packs.items():
        s = pack.sizing
        assert s.open_bb > 0 and s.threebet_mult > 0 and s.fourbet_mult > 0, name
    wrong = []
    for (persona, facing, pos), (combos, weights) in PINNED_CORES.items():
        positions = None if pos == "*" else pos.split(",")
        node = next((n for n in packs[persona].preflop
                     if n.facing == facing
                     and ([p.value for p in n.positions] if n.positions else None) == positions),
                    None)
        assert node is not None, f"{persona} {facing} {pos} is missing"
        first = node.mixes[0]
        if first.combos != combos or dict(first.weights) != weights:
            wrong.append(f"{persona} {facing} {pos}: core is now "
                         f"{first.combos!r} {dict(first.weights)}")
    assert not wrong, "\n".join(wrong)
