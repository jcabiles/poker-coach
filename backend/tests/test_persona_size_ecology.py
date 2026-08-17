"""Bet size must not name the bettor.

Spec §7.2 test 5's companion. Grid membership is already asserted by
`test_persona_pack_invariants.py`; what that cannot see is whether the six
personas' size distributions are DISJOINT, which is the defect this ticket
exists to remove. The 2026-08-05 re-measure put it plainly
(`remeasure-2026-08-05/report_table.md` §5): "an observant hero can read the
bettor's archetype off the bet size alone with almost no error", because SMALL
meant station or fish, LARGE meant tag/lag/nit, and OVERBET meant maniac.

Neither statistical gate can see this. Rule 1 scores ten frequency statistics
and none of them is a size; rule 4 groups on action type, not size. Both pass
a roster whose six size distributions do not overlap at all.

Two claims, deliberately different in kind
------------------------------------------
`test_no_node_lets_one_bet_size_name_the_bettor` is the goal statistic: the
best accuracy any observer could reach guessing the persona from one bet size.
It is scale-free, needs no list to maintain, and cannot be satisfied by adding
token weights — only real overlapping mass moves it.

`test_every_persona_bets_small_medium_and_large` is the blunter structural
claim, and it catches something the first one does not: a persona that cannot
make a given size AT ALL. Before this slice the maniac's flat block was
0.75/1.0/1.5, so a maniac leading out could not make a small or a medium bet;
the nit's had no 0.33. An accuracy ceiling tolerates that as long as some other
persona is equally concentrated somewhere else.

Why these read the AUTHORED distributions
-----------------------------------------
The realised distribution differs from the authored one — `_bluff_size_factor`
tilts the size weights on a bluff cell, and the legal-bet bracket clamps some
bets off their drawn fraction entirely. Measuring it needs thousands of
self-play hands, which does not belong in a unit test. The authored numbers are
what the pack CLAIMS to play and are the thing an edit changes, so they are
what a regression guard should read. The realised measurement is reported in
the ticket ledger, where it is the claim being made about the roster.
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

# RES-E buckets over the authored grid keys (`personas_postflop.size_bucket`
# cutoffs, applied to the authored fraction rather than a live pot-fraction).
BANDS = {"small": ("0.33",), "medium": ("0.5",), "large": ("0.75", "1.0")}

# An observer who sees one bet size and names the persona. Chance is 1/6 =
# 0.167; a perfectly disjoint roster reads 1.0. Measured at the branch point
# (ed4d108) the worst node read 0.392 and the best 0.283; after this ticket the
# worst reads 0.328. The ceiling is set at 0.35 — above every post-ticket node
# with margin, below the three pre-ticket nodes that carried the tell hardest
# (`river_value` and `raise` at 0.392, `cbet_wet` and `turn_barrel` at 0.350).
#
# It is NOT set to just-fail the old packs. 0.35 is roughly twice chance, which
# is the honest reading of "a type is recognisable but not a signature" — the
# distinction the roadmap draws at bot-realism-flywheel.md:40-47 and the one
# this whole slice is gated on.
MAX_SIZE_TELL = 0.35

# Every persona must put real mass in each of small, medium and large. 0.10 is
# a "can this persona make this bet at all" line, not a fitted target: the
# tightest post-ticket value is 0.15 (the nit's and the maniac's 0.33), so the
# floor keeps 1.5x headroom.
MIN_BAND_SHARE = 0.10


@pytest.fixture(scope="module")
def packs() -> dict:
    return load_persona_packs()


def _dist_at(pack, node: str) -> dict[str, float]:
    """The engine's own fallback rule, mirrored: a node override when the pack
    authored one, else the flat block (`personas_postflop._sizing_dist`)."""
    pf = pack.postflop
    return (pf.sizing_by_node or {}).get(node, pf.sizing)


def _size_tell(packs: dict, node: str) -> float:
    """Bayes-optimal accuracy of naming the persona from one bet size at `node`,
    under a uniform prior over the six: `(1/n) * sum_s max_i p_i(s)`."""
    dists = [_dist_at(pack, node) for pack in packs.values()]
    sizes = {s for d in dists for s in d}
    return sum(max(d.get(s, 0.0) for d in dists) for s in sizes) / len(dists)


def test_no_node_lets_one_bet_size_name_the_bettor(packs):
    loud = {node: round(_size_tell(packs, node), 3) for node in NODES
            if _size_tell(packs, node) > MAX_SIZE_TELL}
    assert not loud, (
        f"bet size names the bettor at {loud} — an observer guessing the "
        f"persona from a single size beats the {MAX_SIZE_TELL} ceiling "
        f"(chance is {1 / len(packs):.3f}). Full table: "
        f"{ {n: round(_size_tell(packs, n), 3) for n in NODES} }")


def test_the_size_tell_ceiling_can_fail(packs):
    """Negative case, on the real pre-ticket numbers rather than a synthetic
    caricature. `river_value` was 0.75/1.0 for four packs and 0.33/0.5/0.75 for
    the two recreationals — two disjoint pairs, nothing shared."""
    pre = {
        "tag": {"0.75": 0.55, "1.0": 0.45},
        "nit": {"0.75": 0.4, "1.0": 0.6},
        "lag": {"0.75": 0.3, "1.0": 0.5, "1.5": 0.2},
        "maniac": {"0.75": 0.3, "1.0": 0.4, "1.5": 0.3},
        "calling_station": {"0.33": 0.6, "0.5": 0.3, "0.75": 0.1},
        "passive_fish": {"0.33": 0.6, "0.5": 0.3, "0.75": 0.1},
    }
    rebuilt = {}
    for name, dist in pre.items():
        pack = packs[name].model_copy(deep=True)
        pack.postflop.sizing_by_node = {"river_value": dist}
        rebuilt[name] = pack
    assert _size_tell(rebuilt, "river_value") > MAX_SIZE_TELL, (
        "the pre-ticket river_value distributions must fail this ceiling, or "
        "the ceiling is not measuring the defect it was set against")


def test_a_flat_roster_reads_at_chance(packs):
    """The statistic's other end, pinned so the direction cannot be misread: six
    identical distributions are unguessable, and read exactly 1/6."""
    shared = {"0.33": 0.2, "0.5": 0.2, "0.75": 0.2, "1.0": 0.2, "1.5": 0.2}
    rebuilt = {}
    for name, pack in packs.items():
        copy = pack.model_copy(deep=True)
        copy.postflop.sizing_by_node = {"river_value": dict(shared)}
        rebuilt[name] = copy
    assert _size_tell(rebuilt, "river_value") == pytest.approx(1 / len(packs))


def test_every_persona_bets_small_medium_and_large(packs):
    """No persona may be unable to make an ordinary bet size.

    Read on the flat `sizing` block, which every pack has and which no pack can
    avoid: it is the distribution used whenever the seat is not the aggressor,
    and for the station and fish — who author no `sizing_by_node` at all — it is
    the distribution used for every bet they ever make.
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
    """Negative case, again on the real pre-ticket numbers: the maniac's flat
    block was 0.75/1.0/1.5, so a maniac leading out could not make a small or a
    medium bet at all — the tell this ticket was written to remove."""
    pack = packs["maniac"].model_copy(deep=True)
    pack.postflop.sizing = {"0.75": 0.4, "1.0": 0.35, "1.5": 0.25}
    dist = pack.postflop.sizing
    missing = [band for band, keys in BANDS.items()
               if sum(dist.get(k, 0.0) for k in keys) < MIN_BAND_SHARE]
    assert missing == ["small", "medium"], missing
