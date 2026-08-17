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

WHAT THIS FILE IS, AND WHAT IT IS NOT
-------------------------------------
It is a REGRESSION GUARD on what the packs author. It is NOT a measurement of
the roster, and the slice must not close on it. Three separate reasons, all
found by review and all of them pushing the score in the direction that
flatters the roster:

  * The realised distribution is not the authored one. `_bluff_size_factor`
    tilts the weights on a bluff cell and the legal-bet bracket clamps some
    bets off their drawn fraction, so a persona plays a distribution it never
    authored. At the `raise` node 65% of realised sizes land off the grid
    entirely, clamped up to the minimum raise.
  * These are UNIFORM-PRIOR statistics. That is deliberate — it isolates how
    much information the SIZE carries about identity from how often each seat
    happens to bet — but it erases a base rate that matters. The maniac makes
    about 46% of the table's bets, so a size it shares with one other pack is
    far more diagnostic in play than the authored number says.
  * The nodes are weighted EQUALLY here and are nothing like equal in play.

The realised figures, which are the claim being made about the roster, live in
`docs/ai-dlc/ledger/phase3-derobotization.md`. When the two disagree, the
realised one is the answer and this file is the guard that stops a future pack
edit from quietly undoing the authored half.

THE QUOTED DEFECT IS A CLASS READ, SO THE PRIMARY GATE SCORES CLASSES
---------------------------------------------------------------------
An earlier draft of this file scored per-PERSONA accuracy and was wrong to.
Per-persona accuracy is diluted precisely by the two recreationals being
near-identical to each other and the three regulars being near-identical to
each other, so an edit that blurs the regulars AMONG THEMSELVES lowers the
number while leaving "SMALL means recreational" untouched. That is the
no-op-shaped pass §7.2 exists to prevent.

The same argument applies to a POSTERIOR, and the draft that fixed the accuracy
statistic left the posterior per-persona — so `cbet_wet @ 0.33` sat at class
posterior 1.000 while reading 0.525 per persona and passing. Both populations
are now scored at both statistics.

A RARE SIZE CAN BE A PERFECT TELL THAT AN AVERAGE CANNOT SEE
-------------------------------------------------------------
Both accuracy statistics average over sizes, so a size used by exactly ONE
persona contributes only that persona's own small weight — while being a
certain giveaway every time it occurs. Review found this true of the shipped
packs, not merely possible: the 1.5 was authored by the maniac alone at three
nodes. The two posterior gates score the other quantity, the confidence of the
best guess GIVEN a size was seen.
"""

from __future__ import annotations

import pytest

from app.domain.personas import load_persona_packs

# `raise` IS NOT HERE, AND THAT IS THE POINT ─────────────────────────────────
# The packs author a `raise` block and no bot can ever use it. Proof, not
# sampling: `postflop_node_key` (`table/sizing.py:144`) returns "raise" only
# when `ActionType.CALL` is in the legal set, i.e. only when the seat is facing
# chips; `_sizing_dist` (`personas_postflop.py:572`) reaches that lookup only
# when `pf.sizing_by_node and is_aggressor`; and the live bot derives
# `is_aggressor` as "this seat made the most recent bet or raise"
# (`table/play.py:242`). A seat facing a wager cannot be the seat that made it,
# so the two conditions are mutually exclusive and the `raise` branch is dead.
# Measured to agree: over 10,834 postflop facing-a-bet decisions, zero had
# `is_aggressor` true, and of 4,557 realised raise-node bets, zero were sized
# from the `raise` block. Real raises draw from the FLAT block.
#
# Scoring it anyway inflated this file's headline: the previous draft quoted
# "0.756 -> 0.612 at the worst node" from a node no bot plays. The worst
# REACHABLE node is `cbet_wet`. The dead block is filed for the owner in the
# ledger — removing it and fixing the `is_aggressor` semantics are different
# decisions with different blast radii, and neither belongs in this ticket.
#
# Kept as a literal rather than read from `postflop_node_key` for the usual
# reason: a gate that sources its own scope from the module under test goes
# green for free the moment that module changes its mind.
NODES = ("flat", "cbet_dry", "cbet_wet", "cbet_mono", "turn_barrel",
         "river_value")

# The grader's recognised grid, canonical spelling. Sizes are CANONICALISED on
# read rather than looked up by these literals: the pack invariant compares
# `float(key)` (`test_persona_pack_invariants.py:58`), so `"0.50"`, `"1.00"` and
# `"0.330"` are all legal authored keys. A previous draft looked them up as
# strings and silently scored a maximally telling roster spelled `"0.50"` as
# 0.0 — a regression guard a future pack edit could evade by spelling.
GRID = ("0.33", "0.5", "0.75", "1.0", "1.5")

# RES-E buckets over the authored grid keys.
BANDS = {"small": ("0.33",), "medium": ("0.5",), "large": ("0.75", "1.0")}

# The three archetype classes the re-measure's finding is phrased in.
CLASSES = {
    "recreational": ("calling_station", "passive_fish"),
    "regular": ("tag", "nit", "lag"),
    "maniac": ("maniac",),
}

# --- the four ceilings, and why each is where it is -------------------------
#
# TWO DIFFERENT KINDS OF LINE, and the previous draft's comment claimed one
# principle covered all of them. It does not, and saying so was the more
# serious error of the two, because it dressed a fitted number as a derived
# one.
#
# The ACCURACY ceilings are set from chance. The governing principle is the
# roadmap's distinction at `bot-realism-flywheel.md:40-47` — a seat being
# recognisable as a TYPE is desirable, a seat being recognisable as a MACHINE
# is the defect — and "twice chance" is the reading of that line these gates
# use. Both now follow it exactly, which only became possible once the phantom
# `raise` node stopped being scored.
#
# The POSTERIOR ceilings cannot be set from chance, because a posterior's floor
# depends on how many packs author the size at all. They are CERTAINTY lines:
# they exist to stop a size being proof, not to stop it being evidence. They
# are stated here as the judgement calls they are, with the roster's distance
# from them recorded so a later reader can see whether a value was fitted.

# Naming the CLASS from one bet size. Chance is 1/3, so this is 2x chance.
# Measured: pre-ticket 0.533-0.711, post 0.402-0.556 (worst `cbet_wet`, margin
# 0.111). It fails three of the six pre-ticket nodes.
MAX_CLASS_TELL = 0.667

# Naming the PERSONA from one bet size. Chance is 1/6, so this is 2x chance.
# Supporting check — weaker than the class gate by construction, see the module
# docstring. Post-ticket worst 0.297 (`cbet_wet`), margin 0.036. The previous
# draft set this at 0.375 (2.25x chance) because the roster read 0.328 at the
# `raise` node and could not clear 2x. Dropping the phantom node removed the
# reason for the exception, so the exception is gone.
MAX_PERSONA_TELL = 0.333

# Confidence of the best guess about WHICH PERSONA, given a size was observed.
# 1.0 means exactly one persona ever makes that bet. Pre-ticket four cells at
# 1.000; post-ticket worst outside the exemptions is 0.647 (`turn_barrel` @
# 1.5, shared maniac/lag).
MAX_SIZE_POSTERIOR = 0.70

# The same quantity for CLASSES, and the gate the previous draft was missing
# entirely. It applies ONLY where the best guess is a multi-member class. The
# maniac is a class of one, so its class posterior is its persona posterior
# wearing a different hat — already gated above, with a named exemption — and
# scoring it twice would turn this gate into a list of exemptions for the one
# archetype that is SUPPOSED to be recognisable. Post-ticket worst 0.800
# (`cbet_wet` @ 0.33, recreational); next is 0.750.
MAX_CLASS_POSTERIOR = 0.85

# The (node, size) cells allowed to exceed `MAX_SIZE_POSTERIOR`, each with the
# ruling that permits it. This list IS the disclosure: any other size that
# becomes single-persona is a regression, and adding a line here is a decision,
# not a fix.
#
# Both are the maniac's overbet, and they are here for one reason: an overbet is
# the maniac's archetype and blurring it away would be the trade this slice
# exists to refuse. The flat block sizes a LEAD, and an overbet lead is not a
# habit of any other pack. `cbet_wet` is here after a reversal — T5's review
# gave lag an 8% overbet there to break the cell, and the following review was
# right that the value was fitted (the minimum weight clearing the old ceiling
# was 6.86%) and that the poker was weak: a flop overbet is a static-board,
# nut-advantage tool, and a wet coordinated board is exactly where correct
# sizing shrinks. It was withdrawn. Lag keeps its `turn_barrel` overbet, which
# is a genuine habit — turn overbets on scare cards — and shares that cell.
#
# What this costs, stated rather than hidden: the realised P(maniac | a 1.5x
# bet) is about 0.90 with real base rates. The overbet remains a maniac tell.
# The ledger records that as an open residual, not as a solved problem.
SINGLE_PERSONA_CELLS = {("flat", "1.5"), ("cbet_wet", "1.5")}

# Every persona must put real mass in each of small, medium and large. 0.10 is a
# "can this persona make this bet at all" line, not a fitted target.
MIN_BAND_SHARE = 0.10


@pytest.fixture(scope="module")
def packs() -> dict:
    return load_persona_packs()


_CANON_SPELLING = {float(s): s for s in GRID}


def _canon(dist: dict) -> dict[str, float]:
    """Size keys normalised to their canonical spelling, so `"0.50"` and
    `"0.5"` are the same cell. Duplicate spellings sum rather than collide.

    A grid size keeps the grid's own spelling — `"1.00"` becomes `"1.0"`, not
    the `"1"` that `%g` alone would give, which would stop matching `BANDS` and
    `GRID` and reintroduce the miss this function exists to prevent. Off-grid
    keys, which the pack invariant rejects but which a caller may construct,
    fall back to `%g`."""
    out: dict[str, float] = {}
    for key, weight in dist.items():
        value = float(key)
        name = _CANON_SPELLING.get(value, f"{value:g}")
        out[name] = out.get(name, 0.0) + float(weight)
    return out


def _dist_at(pack, node: str) -> dict[str, float]:
    """The engine's own fallback rule, mirrored: a node override when the pack
    authored one, else the flat block (`personas_postflop._sizing_dist`)."""
    pf = pack.postflop
    return _canon((pf.sizing_by_node or {}).get(node, pf.sizing))


def _sizes(dists: list[dict[str, float]]) -> list[str]:
    """Every size any of these distributions authors, canonical grid first so
    an off-grid key cannot be dropped by looking sizes up from a literal."""
    return sorted({s for d in dists for s in d} | set(GRID), key=float)


def _bayes_accuracy(dists: list[dict[str, float]]) -> float:
    """Best accuracy an observer could reach identifying which of `dists`
    produced one observed size, under a uniform prior over them."""
    return sum(max(d.get(s, 0.0) for d in dists)
               for s in _sizes(dists)) / len(dists)


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


def _posterior(dists: list[dict[str, float]], size: str) -> float | None:
    """Confidence that the heaviest author of `size` is the one you saw, given
    you saw it. `None` when nobody authors it."""
    total = sum(d.get(size, 0.0) for d in dists)
    if total <= 0.0:
        return None
    return max(d.get(size, 0.0) for d in dists) / total


def _size_posterior(packs: dict, node: str, size: str) -> float | None:
    return _posterior([_dist_at(p, node) for p in packs.values()], size)


def _class_posterior(packs: dict, node: str, size: str) -> tuple[float, str] | None:
    """The class version, with the winning class named — the gate only applies
    to the multi-member ones, so the caller needs to know which won."""
    dists = _class_dists(packs, node)
    total = sum(d.get(size, 0.0) for d in dists)
    if total <= 0.0:
        return None
    best = max(range(len(dists)), key=lambda i: dists[i].get(size, 0.0))
    name = list(CLASSES)[best]
    return dists[best].get(size, 0.0) / total, name


def _all_sizes(packs: dict, node: str) -> list[str]:
    return _sizes([_dist_at(p, node) for p in packs.values()])


# --- the headline gate ------------------------------------------------------

def test_no_node_lets_one_bet_size_name_the_class(packs):
    loud = {n: round(_class_tell(packs, n), 3) for n in NODES
            if _class_tell(packs, n) > MAX_CLASS_TELL}
    assert not loud, (
        f"bet size names the archetype CLASS at {loud} — an observer guessing "
        f"recreational/regular/maniac from a single size beats the "
        f"{MAX_CLASS_TELL} ceiling (chance {1 / len(CLASSES):.3f}). Full table: "
        f"{ {n: round(_class_tell(packs, n), 3) for n in NODES} }")


def test_no_single_size_names_one_class_outright(packs):
    """The gate the first rewrite was missing. A size both recreationals use and
    nobody else does is a certain CLASS tell while reading only about 0.5 per
    persona, because the two of them split the evidence between themselves."""
    loud = []
    for node in NODES:
        for size in _all_sizes(packs, node):
            got = _class_posterior(packs, node, size)
            if got is None:
                continue
            post, winner = got
            if len(CLASSES[winner]) == 1:
                continue  # singleton class — the persona gate already owns it
            if post > MAX_CLASS_POSTERIOR:
                authors = sorted(n for n, p in packs.items()
                                 if _dist_at(p, node).get(size, 0.0) > 0)
                loud.append(f"{node} @ {size}: seeing this size identifies the "
                            f"{winner} class with confidence {post:.2f} "
                            f"(authors: {authors})")
    assert not loud, "\n".join(loud)


def test_no_single_size_names_one_persona_outright(packs):
    loud = []
    for node in NODES:
        for size in _all_sizes(packs, node):
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


def test_every_exempted_cell_is_still_single_persona(packs):
    """An exemption that stops being needed must be deleted, not left lying
    where it can silently cover a future regression at the same cell."""
    stale = [cell for cell in sorted(SINGLE_PERSONA_CELLS)
             if (_size_posterior(packs, *cell) or 0.0) <= MAX_SIZE_POSTERIOR]
    assert not stale, (
        f"these cells no longer exceed {MAX_SIZE_POSTERIOR} and their "
        f"exemption should be removed: {stale}")


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
    """On the real pre-ticket numbers, not a synthetic caricature.

    The reason stated here matters, and the previous draft got it wrong: it
    blamed the 0.33, saying no regular authored one so a third-pot river bet
    named `station or fish` with certainty. That is true of the packs and is
    NOT what makes this score fail — delete the 0.33 from both recreationals
    and move the mass to 0.5 and the score does not budge (0.711 either way),
    because the recreationals still own the small-and-medium end outright while
    the regulars own the large end. The whole SHAPE was disjoint. The certainty
    cell is a separate defect, caught by the posterior gate below, and the two
    were conflated.
    """
    pre = _rebuilt(packs, "river_value", _PRE_TICKET_RIVER_VALUE)
    assert _class_tell(pre, "river_value") > MAX_CLASS_TELL, (
        f"the pre-ticket river_value distributions read "
        f"{_class_tell(pre, 'river_value'):.3f}, which must exceed the ceiling "
        f"or the ceiling is not measuring the defect it was set against")

    # And the stated cause, pinned separately so the two cannot be conflated
    # again: removing the certainty cell leaves the accuracy gate still failing.
    without = {name: dict(d) for name, d in _PRE_TICKET_RIVER_VALUE.items()}
    for rec in CLASSES["recreational"]:
        without[rec] = {"0.5": 0.9, "0.75": 0.1}
    assert _class_tell(_rebuilt(packs, "river_value", without),
                       "river_value") > MAX_CLASS_TELL


def test_the_posterior_gate_catches_what_the_accuracy_gates_cannot(packs):
    """The evasion an averaging statistic cannot see, pinned as its own case.

    The fixture is built so BOTH accuracy gates genuinely pass and only the
    posterior gate fires — which is the whole argument for having a posterior
    gate, and which the previous draft asserted in prose while shipping a
    fixture both accuracy gates caught. Five packs share one distribution; the
    maniac shaves 4% off each of its four sizes and puts it on a 1.5 nobody
    else authors. A rare private size barely moves an average and is a
    certainty every time it appears.
    """
    shared = {"0.33": 0.25, "0.5": 0.25, "0.75": 0.25, "1.0": 0.25}
    dists = {name: dict(shared) for name in packs}
    dists["maniac"] = {"0.33": 0.24, "0.5": 0.24, "0.75": 0.24, "1.0": 0.24,
                       "1.5": 0.04}
    pre = _rebuilt(packs, "river_value", dists)

    assert _class_tell(pre, "river_value") <= MAX_CLASS_TELL
    assert _persona_tell(pre, "river_value") <= MAX_PERSONA_TELL
    assert _size_posterior(pre, "river_value", "1.5") == pytest.approx(1.0)


def test_the_class_posterior_gate_catches_what_the_persona_one_cannot(packs):
    """The hole the first rewrite left. Both recreationals use a size no other
    pack does: the persona posterior reads 0.50 because they split the evidence
    between them, both accuracy gates pass, and the class is named outright."""
    dists = {name: {"0.5": 0.5, "0.75": 0.5} for name in packs}
    for rec in CLASSES["recreational"]:
        dists[rec] = {"0.33": 0.3, "0.5": 0.35, "0.75": 0.35}
    pre = _rebuilt(packs, "river_value", dists)

    assert _class_tell(pre, "river_value") <= MAX_CLASS_TELL
    assert _persona_tell(pre, "river_value") <= MAX_PERSONA_TELL
    assert _size_posterior(pre, "river_value", "0.33") == pytest.approx(0.5)

    post, winner = _class_posterior(pre, "river_value", "0.33")
    assert winner == "recreational"
    assert post == pytest.approx(1.0)


def test_a_size_spelled_differently_is_still_the_same_size(packs):
    """The evasion the string-keyed draft shipped: two packs whose sizes do not
    overlap at all, spelled off-canonical, scored 0.0 and passed every ceiling
    because every statistic looked its sizes up from a literal grid."""
    assert _canon({"0.50": 0.4, "1.00": 0.6}) == {"0.5": 0.4, "1.0": 0.6}
    assert _canon({"0.5": 0.3, "0.50": 0.2}) == {"0.5": 0.5}

    # The roster the string-keyed draft scored as 0.0: canonicalised, the two
    # packs are maximally telling and every statistic now says so.
    disjoint = [_canon({"0.50": 1.0}), _canon({"1.00": 1.0})]
    assert _bayes_accuracy(disjoint) == pytest.approx(1.0)
    assert _posterior(disjoint, "0.5") == pytest.approx(1.0)
    assert _posterior(disjoint, "1.0") == pytest.approx(1.0)


def test_a_maximally_telling_roster_scores_the_top_of_its_range(packs):
    """Direction pin. The first version asserted that six IDENTICAL
    distributions read exactly chance — which review showed is vacuous, since
    for identical normalised distributions the sum is 1 for any shape whatever,
    so it pinned that weights sum to 1 and nothing else. This pins the other
    end, where the statistic has to do work: give five personas their own
    private size and the score must reach its ceiling, which for six packs over
    a five-size grid is exactly 5/6."""
    private = dict(zip(sorted(packs), GRID + ("1.5",), strict=True))
    dists = {name: {size: 1.0} for name, size in private.items()}
    telling = _rebuilt(packs, "river_value", dists)
    assert _persona_tell(telling, "river_value") == pytest.approx(5 / 6)
    assert _class_tell(telling, "river_value") > MAX_CLASS_TELL


# --- structural floor -------------------------------------------------------

def test_every_persona_bets_small_medium_and_large(packs):
    """No persona may be unable to make an ordinary bet size.

    Read on the flat `sizing` block, and that scope is a deliberate limit rather
    than an oversight. Per-NODE the same floor is wrong: a nit betting
    three-quarters pot on a dry board 10% of the time is a target nobody should
    be held to. What catches a node-level hole is the posterior gate above,
    which fires when a missing size makes some OTHER persona's use of it
    diagnostic.

    The flat block is the right place for the blunt version: every pack has one,
    it is the distribution used whenever the seat is not the aggressor, and for
    the station and fish — who author no `sizing_by_node` at all — it is the
    distribution behind every bet they ever make. It is also, per the `NODES`
    note above, the block behind every raise anyone makes.
    """
    thin = []
    for name, pack in packs.items():
        dist = _canon(pack.postflop.sizing)
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


# The preflop levers, pinned byte-for-byte. An early version of this ticket's
# own patcher matched an unanchored `"sizing": {...}` and rewrote the TOP-LEVEL
# block — one indentation level away from the postflop one — replacing open
# sizes with pot fractions. The guard that replaced it asserted only that the
# three levers were positive, which that patcher's output would have passed.
_PREFLOP_SIZING = {
    "calling_station": (3.5, 3.0, 2.2),
    "lag": (3.0, 3.5, 2.4),
    "maniac": (4.5, 3.3, 3.0),
    "nit": (3.0, 3.5, 2.3),
    "passive_fish": (4.0, 3.0, 2.2),
    "tag": (3.0, 3.5, 2.4),
}

# The tier ABOVE each softened block, pinned byte-for-byte, so that re-weighting
# sizes cannot quietly rewrite a persona's premium range.
PINNED_CORES = {
    ("calling_station", "unopened", "UTG"): ("AA, KK, AKs", {"raise": 0.5, "limp": 0.5}),
    ("passive_fish", "vs_rfi", "BB"): ("AA, KK", {"3bet": 1.0}),
}


def test_a_sizing_change_did_not_touch_a_preflop_range(packs):
    """This ticket owns the `postflop` block and nothing else."""
    assert set(packs) == set(_PREFLOP_SIZING), "roster changed; re-pin"
    for name, pack in packs.items():
        s = pack.sizing
        assert (s.open_bb, s.threebet_mult, s.fourbet_mult) == _PREFLOP_SIZING[name], name
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
