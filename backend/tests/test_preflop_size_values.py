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
    """
    for name, pack in packs.items():
        counts = _open_sizes(pack, position)
        assert sum(counts.values()) > 50, f"{name}@{position.value}: too few opens to judge"
        top = counts.most_common(1)[0][1] / sum(counts.values())
        assert len(counts) >= 2, f"{name}@{position.value} opens one size: {counts}"
        assert top <= 0.95, (
            f"{name}@{position.value} modal open share {top:.3f} — a mix on "
            f"paper that plays as one number: {counts}")


# --- 2. the regulars move with the seat, the recreationals do not -----------

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
    """3.5x is `grade_map_preflop._THREEBET_MULT_CAP`, and hero's own open is
    offered at the canonical size for its seat, so a multiplier at or under 3.5
    is gradeable at every seat and one above it is gradeable at none.

    The cap is imported rather than written as 3.5, so a drift in the grader
    fails here instead of silently making a shipped rung ungradeable.
    """
    from app.domain.table.grade_map_preflop import _THREEBET_MULT_CAP

    for name, pack in packs.items():
        mix = pack.sizing.threebet_mult_mix
        assert mix, f"{name} authored no 3-bet mix"
        worst = max(float(k) for k in mix)
        assert worst <= _THREEBET_MULT_CAP + 1e-9, (
            f"{name}: 3-bet rung {worst} exceeds the {_THREEBET_MULT_CAP} cap")
        assert len(mix) >= 2, f"{name}: 3-bet mix {mix} is one value"


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
