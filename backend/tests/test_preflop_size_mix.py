"""Preflop raise sizes may be drawn from a mix (de-robotization T2a).

This is the MECHANISM only. No shipped pack authors a size mix yet, so every
persona still opens its one fixed size and behaviour is byte-identical to
before — proven by `test_shipped_packs_author_no_mix_yet` below. Authoring the
values is T2b, which is blocked on an owner decision about a preregistered
protocol pin (see `docs/ai-dlc/tickets/phase3-derobotization.md`).

The two statistical gates measure action frequencies and never bet sizes, so
neither can tell whether sizing changed at all. These tests carry that burden.
"""

from __future__ import annotations

import random
from collections import Counter

import pytest
from pydantic import ValidationError

from app.domain.content.models import PersonaSizing
from app.domain.personas import load_persona_packs, sample_preflop_action
from app.domain.spot import Card, Position
from app.domain.table.sizing import preflop_raise_to

# Hero's preflop grading bands (grade_map_preflop). A villain size outside
# these is ungradeable, which shows the user "no baseline yet".
OPEN_CAP = 4.5
THREEBET_MULT_CAP = 3.5
FOURBET_MULT_CAP = 2.4


def _sizing(**overrides) -> PersonaSizing:
    base = {"open_bb": 3.0, "threebet_mult": 3.5, "fourbet_mult": 2.4}
    return PersonaSizing(**{**base, **overrides})


def _draw_many(sizing, node, rng, *, limpers=0, last_raise_to=3.0, n=600,
               min_bb=2.0, max_bb=200.0):
    return [
        preflop_raise_to(sizing, node, last_raise_to=last_raise_to,
                         limpers=limpers, min_bb=min_bb, max_bb=max_bb, rng=rng)
        for _ in range(n)
    ]


# --- the default path is byte-identical -------------------------------------

@pytest.mark.parametrize("node,expected", [
    ("open", 3.0),
    ("iso", 3.0),
    ("3bet", 10.5),
    ("4bet", 7.2),
])
def test_without_an_rng_the_scalar_is_used(node, expected):
    """Every caller that passes no rng — the statistical harness, the range
    estimator, every test predating this — must be unchanged."""
    got = preflop_raise_to(_sizing(), node, last_raise_to=3.0, limpers=0,
                           min_bb=2.0, max_bb=200.0)
    assert got == pytest.approx(expected)


def test_an_rng_without_a_mix_changes_nothing():
    """Opting a caller in must not change a pack that has not opted in."""
    sizing = _sizing()
    rng = random.Random(4)
    assert set(_draw_many(sizing, "open", rng, n=200)) == {3.0}
    assert sizing.open_bb_mix is None


def test_a_sizing_object_without_the_mix_fields_still_works():
    """`sizing` is duck-typed: the bet-sizing tests pass a minimal stand-in
    carrying only the three scalars. Reading the mixes must tolerate that."""

    class BareSizing:
        open_bb, threebet_mult, fourbet_mult = 2.5, 3.0, 2.0

    got = preflop_raise_to(BareSizing(), "open", last_raise_to=3.0, limpers=0,
                           min_bb=2.0, max_bb=200.0, rng=random.Random(1))
    assert got == pytest.approx(2.5)


def test_shipped_packs_author_no_mix_yet():
    """T2a ships the mechanism only. If this starts failing, T2b has landed
    and the pack-value assertions belong with it."""
    for name, pack in load_persona_packs().items():
        s = pack.sizing
        assert (s.open_bb_mix, s.threebet_mult_mix, s.fourbet_mult_mix) == (
            None, None, None), f"{name} authored a mix"


# --- with a mix, sizes vary as authored -------------------------------------

def test_the_drawn_size_comes_from_the_mix():
    sizing = _sizing(open_bb_mix={"2.5": 0.3, "3.0": 0.5, "3.5": 0.2})
    drawn = set(_draw_many(sizing, "open", random.Random(8), n=500))
    assert drawn == {2.5, 3.0, 3.5}


def test_observed_frequencies_track_the_authored_weights():
    mix = {"2.5": 0.3, "3.0": 0.5, "3.5": 0.2}
    counts = Counter(_draw_many(_sizing(open_bb_mix=mix), "open",
                                random.Random(1234), n=4000))
    for key, weight in mix.items():
        assert abs(counts[float(key)] / 4000 - weight) < 0.03, key


def test_multipliers_are_drawn_and_applied_to_the_faced_raise():
    sizing = _sizing(threebet_mult_mix={"3.0": 0.5, "3.5": 0.5})
    drawn = set(_draw_many(sizing, "3bet", random.Random(2), last_raise_to=4.0,
                           n=400))
    assert drawn == {12.0, 14.0}


def test_the_iso_moves_with_the_drawn_open():
    """The measured tell was an iso landing on exactly one number — a fixed
    open plus 1bb per limper. Drawing the open makes the iso move with it."""
    sizing = _sizing(open_bb=4.0, open_bb_mix={"3.0": 0.4, "4.0": 0.6})
    sizes = set(_draw_many(sizing, "iso", random.Random(3), limpers=1, n=400))
    assert sizes == {4.0, 5.0}


def test_draws_are_reproducible_for_a_given_seed():
    mix = {"2.5": 0.5, "3.0": 0.5}
    a = _draw_many(_sizing(open_bb_mix=mix), "open", random.Random(99), n=50)
    b = _draw_many(_sizing(open_bb_mix=mix), "open", random.Random(99), n=50)
    assert a == b


def test_a_forced_jam_bracket_collapses_and_is_not_a_variance_failure():
    """When the engine forces a jam the legal bracket is one value, so every
    draw lands there. That is correct, not a determinism defect."""
    sizing = _sizing(open_bb_mix={"2.5": 0.5, "3.5": 0.5})
    jam = set(_draw_many(sizing, "open", random.Random(2), n=50,
                         min_bb=17.0, max_bb=17.0))
    assert jam == {17.0}


def test_the_engine_clamp_is_not_a_grading_bound():
    """The existing clamp bounds the engine's legal-raise bracket, which
    reaches the whole stack. It enforces no grading cap — which is exactly why
    sizes are enumerated in the mix instead of jittered and clamped."""
    sizing = _sizing(open_bb_mix={"9.0": 1.0})
    assert set(_draw_many(sizing, "open", random.Random(1), n=20)) == {9.0}


# --- schema validation ------------------------------------------------------

@pytest.mark.parametrize("bad", [
    {"3.0": 0.5},                    # weights do not sum to 1
    {"3.0": 0.5, "3.5": 0.6},        # weights sum above 1
    {"3.0": 1.0, "-1": 0.0},         # non-positive fraction and weight
    {"not-a-number": 1.0},           # key is not a float
    {},                              # empty
])
def test_a_malformed_mix_is_rejected(bad):
    with pytest.raises(ValidationError):
        _sizing(open_bb_mix=bad)


def test_a_well_formed_mix_is_accepted():
    assert _sizing(open_bb_mix={"2.5": 0.25, "3.0": 0.75}).open_bb_mix


# --- the size draw never precedes the action draw ---------------------------

def test_the_action_is_still_the_first_rng_choice():
    """`range_estimate._CaptureRng` implements only `.choices()` and captures
    the FIRST call. A size draw placed ahead of the action draw would silently
    capture the wrong distribution, so sizing must stay downstream of it."""
    calls = []

    class RecordingRng(random.Random):
        def choices(self, population, weights=None, *args, **kwargs):
            calls.append(list(population))
            return super().choices(population, weights, *args, **kwargs)

    pack = load_persona_packs()["tag"]
    sample_preflop_action(pack, Position.BTN, "unopened",
                          (Card("As"), Card("Kd")), RecordingRng(5),
                          is_opener=None)
    assert calls, "the action draw must consume the rng"
    assert set(calls[0]) & {"raise", "fold", "call", "limp", "3bet", "4bet",
                            "5bet_shove"}, calls[0]


# --- the bands T2b's values will have to respect ----------------------------

def test_grading_band_constants_match_the_grader():
    """T2b authors sizes against these caps, so a drift in the grader must
    fail here rather than silently widening what T2b may author."""
    from app.domain.table import grade_map_preflop as gmp

    assert gmp._OVERSIZE_OPEN_CAP == OPEN_CAP
    assert gmp._THREEBET_MULT_CAP == THREEBET_MULT_CAP
    assert gmp._FOURBET_MULT_CAP == FOURBET_MULT_CAP
