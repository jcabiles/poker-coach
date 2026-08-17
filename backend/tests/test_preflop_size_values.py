"""The authored preflop size values (de-robotization T2b).

`test_preflop_size_mix.py` covers the mechanism — that a mix is drawn from, that
a seat table selects, that a malformed one is refused. This file covers the
NUMBERS the six packs ship, and it is the only automated thing that can see
them: rule 1 of the per-change gate scores ten frequency statistics and rule 4
groups on action type, so both would pass a roster that opened one fixed size
from every chair, which is what shipped before this ticket.

Two kinds of check live here and they are not equally strong.

The per-cell checks drive production's own `play._preflop_decision` over a fixed
legal bracket. That is the real sampler, the real pack, and the real seat
thread, but a synthetic bracket — no varying stacks, no varying pot. They prove
the values are wired and shaped as authored.

What a persona actually played over full hands, after the engine's legal clamp
had its say, is measured by `tools/preflop_size_report.py` and recorded in
`docs/ai-dlc/ledger/phase3-derobotization.md`. One realised check is kept here
as an anchor, at a hand count a test suite can afford; the ledger carries the
4,000-hand reading.
"""

from __future__ import annotations

import random
from collections import Counter

import pytest

from app.domain.action import ActionType
from app.domain.personas import load_persona_packs
from app.domain.spot import Card, LegalAction, Position
from app.domain.table.play import _preflop_decision

# The three personas that adjust their open to the seat, and the three that do
# not. Seat-blindness is the recreational archetype, not an oversight — see
# each pack's `_doc`.
REGULARS = ("tag", "lag", "nit")
RECREATIONALS = ("calling_station", "passive_fish", "maniac")

# scenarios._OPEN_SIZE splits the table here: 3.0bb is canonical from the four
# early seats and the small blind, 2.5bb from the hijack round.
EARLY = (Position.UTG, Position.UTG1, Position.UTG2, Position.LJ)
LATE = (Position.HJ, Position.CO, Position.BTN)

# The 0.5bb grid the rest of the roster already uses — content/preflop/rfi.json
# opens at 2.5 and 3.0, and the persona scalars are 3.0/3.5/4.0/4.5. Values off
# it (2.2, 2.8) are not amounts a live $2/$3 player picks, and a rung only one
# pack can produce is a fingerprint rather than a differentiator.
GRID_STEP = 0.5

_LEGAL_OPEN = [
    LegalAction(action=ActionType.CHECK),
    LegalAction(action=ActionType.RAISE, min_bb=2.0, max_bb=100.0),
]
_HAND = (Card("As"), Card("Ks"))  # every persona opens this from every seat


@pytest.fixture(scope="module")
def packs():
    return load_persona_packs()


def _open_sizes(pack, position: Position, n: int = 600) -> Counter:
    """The open sizes production produces for this pack from this seat.

    A fresh `Random(seed)` per call rather than one shared stream: the action
    draw comes first, so a shared stream would correlate which seeds raise with
    which sizes follow, and the histogram would be measuring the pairing rather
    than the mix.
    """
    counts: Counter = Counter()
    for seed in range(n):
        d = _preflop_decision(pack, position, "unopened", _HAND, _LEGAL_OPEN,
                              random.Random(seed), 1.0, 0, is_opener=True)
        if d.action is ActionType.RAISE:
            counts[d.size_bb] += 1
    return counts


# --- 1. no persona opens one size from any seat -----------------------------

@pytest.mark.parametrize("position", list(EARLY) + list(LATE) + [Position.SB])
def test_every_persona_mixes_its_open_at_every_seat(packs, position):
    """The measured defect this ticket exists to remove: before T2b every
    persona opened a single size with share 1.000 from all eight opening seats,
    over 4,000 hands.

    A modal share is asserted rather than merely 'two distinct values', because
    a second size drawn one time in five hundred removes the tell from a set
    and leaves it in the data.

    A REVIEWER OBJECTION WORTH RECORDING, not adopted: one rote regular who
    always opens 3bb is the most common player type in a low-stakes full-ring
    game, so requiring every pack to mix arguably forbids a realistic player.
    The assertion stays per-pack anyway, because with six seats at the table a
    persona that never varies is identifiable by that alone — "the seat that
    always opens 3.0" is the tell in a different coat. Scoping the check to the
    roster instead would let any single pack revert silently, which is the
    failure this ticket is about.
    """
    for name, pack in packs.items():
        counts = _open_sizes(pack, position)
        assert sum(counts.values()) > 50, f"{name}@{position.value}: too few opens to judge"
        top = counts.most_common(1)[0][1] / sum(counts.values())
        assert len(counts) >= 2, f"{name}@{position.value} opens one size: {counts}"
        assert top <= 0.95, (
            f"{name}@{position.value} modal open share {top:.3f} — a mix on "
            f"paper that plays as one number: {counts}")


# --- 1b. no size belongs to one persona, and none is off the grid -----------

def _authored_open_sizes(pack, *, blinds: bool = True) -> set[float]:
    """Every open size the pack can draw. `blinds=False` drops SB and BB, whose
    sizes no grader path caps (both capped nodes reject a blind opener first)."""
    keys = set(pack.sizing.open_bb_mix or {})
    for seat, mix in (pack.sizing.open_bb_mix_by_position or {}).items():
        if not blinds and seat in ("SB", "BB"):
            continue
        keys |= set(mix)
    return {float(k) for k in keys}


def test_no_open_size_is_producible_by_exactly_one_persona(packs):
    """The tell this ticket exists to remove, in its subtlest form.

    A first draft differentiated the three regulars by giving each a private
    off-size rung — 2.2 for the lag, 2.8 for the nit. Measured over 4,000
    hands that produced P(lag | a 2.2bb open) = P(nit | a 2.8bb open) = 1.000:
    one observation naming the seat with certainty, where before the change the
    three regulars had been perfectly anonymous to each other by size.

    Personas are separated by how OFTEN they take a shared size, never by
    owning one. The same rule is applied to the 3-bet multiplier below.
    """
    owners: dict[float, list[str]] = {}
    for name, pack in packs.items():
        for size in _authored_open_sizes(pack):
            owners.setdefault(size, []).append(name)
    sole = {s: o[0] for s, o in owners.items() if len(o) == 1}
    assert not sole, f"open sizes only one pack can produce: {sole}"


def test_no_3bet_multiplier_is_producible_by_exactly_one_persona(packs):
    owners: dict[float, list[str]] = {}
    for name, pack in packs.items():
        for key in pack.sizing.threebet_mult_mix or {}:
            owners.setdefault(float(key), []).append(name)
    sole = {s: o[0] for s, o in owners.items() if len(o) == 1}
    assert not sole, f"3-bet multipliers only one pack can produce: {sole}"


def test_every_authored_open_sits_on_the_half_bb_grid(packs):
    """2.2bb and 2.8bb are $6.60 and $8.40 at this table's stakes anchor. Nobody
    picks those. The schema docstring states the rule — sizes stay at values a
    person would actually choose — and a first draft of these values broke it.
    """
    off = {}
    for name, pack in packs.items():
        bad = sorted(s for s in _authored_open_sizes(pack)
                     if abs(round(s / GRID_STEP) * GRID_STEP - s) > 1e-9)
        if bad:
            off[name] = bad
    assert not off, f"open sizes off the {GRID_STEP}bb grid: {off}"


# --- 2. the regulars move with the seat, the recreationals do not -----------

def test_the_big_blind_isolates_at_more_than_one_size(packs):
    """The seat that cannot open still raises, and it reads the same table.

    `preflop_raise_to`'s iso branch is the open plus a bb per limper, so the
    big blind draws from `open_bb_mix_by_position` even though an unopened pot
    never reaches it. An earlier version of the field excluded the seat, and
    all three packs with a seat table isolated at exactly one size — 300 of 300
    draws — while every other check in this file passed.

    Driven through production's `_preflop_decision` at `facing="vs_limpers"`,
    which is the path `bot_decision` takes.

    Scoped to the three regulars. The recreationals author a flat mix, which
    applies at every seat including this one, so they were never at risk — and
    the station raises so rarely that 600 draws do not produce a sample worth
    judging.
    """
    legal = [
        LegalAction(action=ActionType.CHECK),
        LegalAction(action=ActionType.RAISE, min_bb=2.0, max_bb=100.0),
    ]
    for name in REGULARS:
        pack = packs[name]
        counts: Counter = Counter()
        for seed in range(600):
            d = _preflop_decision(pack, Position.BB, "vs_limpers", _HAND, legal,
                                  random.Random(seed), 1.0, 1, is_opener=False)
            if d.action is ActionType.RAISE:
                counts[d.size_bb] += 1
        assert sum(counts.values()) > 50, f"{name}: too few BB isos to judge"
        assert len(counts) >= 2, (
            f"{name} isolates from the big blind at one size: {counts}")


@pytest.mark.parametrize("name", REGULARS)
def test_a_regular_opens_smaller_from_late_position(packs, name):
    """The point of the seat table. A persona-global mix would shift the whole
    distribution down and emit 2.5bb opens from under the gun; this asserts the
    ladder instead — mean open strictly lower from the hijack round than from
    early position, at every one of those seats.
    """
    pack = packs[name]

    def mean(position):
        counts = _open_sizes(pack, position)
        return sum(k * n for k, n in counts.items()) / sum(counts.values())

    early = {p: mean(p) for p in EARLY}
    late = {p: mean(p) for p in LATE}
    assert min(early.values()) > max(late.values()), (
        f"{name}: early opens {early} do not all exceed late opens {late}")


@pytest.mark.parametrize("seats", [EARLY, LATE])
def test_the_three_regulars_are_ordered_by_how_cheaply_they_open(packs, seats):
    """The differentiation that is SAFE to have: level, not alphabet.

    A LAG's edge is opening a wide range cheaply, so it should take the small
    size most often; a nit opens few hands and wants folds, so least often; the
    tag sits between. A first draft asserted exactly this in the lag's pack
    documentation and authored the reverse — lag 0.80 against tag 0.88 at the
    small size — which is why the ordering is now a test rather than a
    sentence.
    """
    def p_small(name):
        table = packs[name].sizing.open_bb_mix_by_position
        small = min(float(k) for k in table[seats[0].value])
        return sum(
            sum(w for k, w in table[s.value].items() if float(k) <= small + 1e-9)
            for s in seats
        ) / len(seats)

    lag, tag, nit = p_small("lag"), p_small("tag"), p_small("nit")
    assert lag > tag > nit, (
        f"expected lag > tag > nit at the small size; got lag={lag:.3f} "
        f"tag={tag:.3f} nit={nit:.3f}")


@pytest.mark.parametrize("name", RECREATIONALS)
def test_a_recreational_opens_the_same_from_every_seat(packs, name):
    """Seat-blindness is this archetype, and asserting it stops a later edit
    'completing' the seat tables across the roster. A player who does not
    adjust to position is the cheapest realistic source of size variety on the
    table; making all six adjust would delete that.

    The mixes are compared, not the realised means: the same mix drawn at two
    seats still gives two slightly different samples.
    """
    sizing = packs[name].sizing
    assert sizing.open_bb_mix_by_position is None, (
        f"{name} acquired a seat table; it is authored seat-blind on purpose")
    assert sizing.open_bb_mix, f"{name} authored no open mix at all"


# --- 3. the levers the ticket deliberately left alone -----------------------

def test_no_pack_authors_a_4bet_mix(packs):
    """A recorded decision, not an omission.

    Measured over 4,000 hands, four-betting is rare: 184 for the maniac, 57 for
    the lag, 27 for the tag, 2 for the fish, 0 for the nit and the station. The
    maniac's multiplier is 3.0 against a 2.4 grading cap, so its four-bets are
    already ungradeable and any rung would be a reduction; the tag's and lag's
    sit exactly ON the 2.4 cap, so a mix there could only lower the mean. That
    changes how those packs deny odds — a real behaviour change — in exchange
    for variety at a node almost nobody reaches.

    If a later slice wants 4-bet variety, this test is the place to record why
    the trade changed.
    """
    for name, pack in packs.items():
        assert pack.sizing.fourbet_mult_mix is None, (
            f"{name} authored a 4-bet mix; see this test's rationale first")


def test_every_3bet_mix_stays_at_or_under_the_grading_cap(packs):
    """3.5x is `grade_map_preflop._THREEBET_MULT_CAP`, applied to the CANONICAL
    open for hero's seat rather than to the open hero actually made.

    Hero is offered two open sizes at an RFI node, the canonical and canonical
    plus 1.0bb (`sim_session._preflop_two_sizes`). On the canonical leg any
    multiplier at or under 3.5 is inside the cap and one above it is outside;
    on the bigger leg `_map_vs_3bet` refuses the spot on hero's own open before
    the multiplier is looked at, and it refuses a blind hero opener outright.
    So this bound is what makes the villain's 3-bet gradeable wherever the spot
    is gradeable at all — not at literally every seat.

    The cap is imported rather than written as 3.5, so a drift in the grader
    fails here instead of silently making a shipped rung ungradeable.

    FILED FOR THE OWNER, not settled here: `RES-B-bet-sizing.md` §4 sources the
    maniac at a 5.5x 3-bet, and this cap makes that unreachable. Keeping the
    test hard protects hero's feedback; the cost is that a grading constant now
    bounds a persona's identity. See the ledger.
    """
    from app.domain.table.grade_map_preflop import _THREEBET_MULT_CAP

    for name, pack in packs.items():
        mix = pack.sizing.threebet_mult_mix
        assert mix, f"{name} authored no 3-bet mix"
        worst = max(float(k) for k in mix)
        assert worst <= _THREEBET_MULT_CAP + 1e-9, (
            f"{name}: 3-bet rung {worst} exceeds the {_THREEBET_MULT_CAP} cap")
        assert len(mix) >= 2, f"{name}: 3-bet mix {mix} is one value"


def test_which_authored_opens_hero_cannot_grade_as_an_opener(packs):
    """The grandfathered exceptions, pinned so a new one is visible.

    `test_authored_preflop_sizes_stay_gradeable` in the invariants file checks
    the OUTER envelope — `_OVERSIZE_OPEN_CAP` 4.5, the band for hero merely
    facing an open — and its name reads more universal than it is. The stricter
    node is hero's vs-4-bet spot, where `_map_vs_4bet` refuses the whole hand
    unless the villain's own open was at most `_STD_OPEN_CAP` 3.0.

    Three packs open above that as their shipped identity and always have. This
    pins exactly which sizes are affected, so that adding a rung above 3.0 to a
    fourth pack fails here instead of quietly removing a hero spot.

    Blind seats are excluded: `_map_vs_4bet` rejects a blind opener before it
    looks at any size, so the regulars' 3.5bb blind opens cost nothing here.
    """
    from app.domain.table.grade_map_preflop import _STD_OPEN_CAP

    refused = {
        name: sorted(s for s in _authored_open_sizes(pack, blinds=False)
                     if s > _STD_OPEN_CAP + 1e-9)
        for name, pack in packs.items()
    }
    assert {k: v for k, v in refused.items() if v} == {
        "calling_station": [3.5, 4.0],
        "passive_fish": [3.5, 4.0, 4.5],
        "maniac": [4.0, 4.5],
    }, refused


def test_the_reports_node_derivation_matches_the_domain():
    """`preflop_size_report._node_for` re-derives the preflop node from a row
    stream instead of a `HandState`. Two copies of one rule drift, so they are
    compared here over every action prefix rather than trusted.
    """
    from itertools import product

    from tools.preflop_size_report import _node_for

    def domain_answer(actions):
        """`play._preflop_facing`, transcribed from the state it reads."""
        raises = [a for a in actions if a == "raise"]
        if not raises:
            return "vs_limpers" if "call" in actions else "unopened"
        n = len(raises)
        return {1: "vs_rfi", 2: "vs_3bet"}.get(n, "vs_4bet")

    for length in range(0, 6):
        for prefix in product(("fold", "call", "raise"), repeat=length):
            n_raises = sum(1 for a in prefix if a == "raise")
            limped = any(
                a == "call"
                for i, a in enumerate(prefix)
                if "raise" not in prefix[:i]
            )
            assert _node_for(n_raises, limped) == domain_answer(prefix), prefix


# --- 4. what full hands actually saw ----------------------------------------

def test_realised_opens_vary_over_whole_hands():
    """The anchor to real play: full nine-bot hands, the engine's own clamp,
    real stacks and real pots.

    Deliberately small — 800 hands, against the 4,000 the ledger reports — so
    the suite can afford it. At this size only the high-volume personas clear
    the sample floor, and the low-volume ones are skipped rather than asserted
    on noise. The ledger has the full roster.

    It runs through the committed report tool rather than re-deriving the
    counts, which also makes the tool itself a tested artifact. The first draft
    of this test did re-derive them, treated every raise made before the first
    raise as an open, and so counted isolation raises — 5.5bb — as open sizes.
    """
    from tools.preflop_size_report import collect

    data = collect(hands=800, seed=601)

    judged = 0
    for name, nodes in data["by_node"].items():
        counts = nodes.get("unopened", {})
        if sum(counts.values()) < 25:
            continue  # the station and the fish barely open; see the ledger
        judged += 1
        assert len(counts) >= 2, f"{name} played one open size: {counts}"
    assert judged >= 3, (
        "too few personas cleared the sample floor: "
        f"{ {k: v.get('unopened') for k, v in data['by_node'].items()} }")
