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

from app.domain.action import ActionType
from app.domain.content.models import PersonaSizing
from app.domain.personas import load_persona_packs
from app.domain.spot import Card, LegalAction, Position
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


def test_an_rng_without_a_mix_consumes_nothing_from_the_stream():
    """Byte-identity is about the RNG STREAM, not just the returned number.

    The seeded harnesses hand one `random.Random` to every decision in a whole
    run, and `hand_seed` is drawn from that same stream, so consuming a single
    extra value would change which cards are dealt in every later hand. An
    implementation that drew and then discarded would pass a returned-value
    check while doing exactly that, so compare the generator's state.
    """
    sizing = _sizing()
    rng = random.Random(4)
    before = rng.getstate()
    assert set(_draw_many(sizing, "open", rng, n=200)) == {3.0}
    assert rng.getstate() == before, "the no-mix path must not touch the stream"
    assert sizing.open_bb_mix is None


def test_a_mix_does_consume_from_the_stream():
    """The mirror of the test above: without this, that one would also pass on
    a feature that never drew at all."""
    rng = random.Random(4)
    before = rng.getstate()
    _draw_many(_sizing(open_bb_mix={"2.5": 0.5, "3.5": 0.5}), "open", rng, n=1)
    assert rng.getstate() != before


def test_a_stand_in_sizing_object_must_declare_its_opt_out():
    """`sizing` is duck-typed, but the mixes are read by direct attribute
    access rather than `getattr(..., None)`.

    A default-to-None read would treat *any* missing attribute as "no mix
    authored" — including a typo in this very module — silently degrading the
    whole feature to the old fixed sizes with nothing reporting it. Requiring
    a stand-in to say `open_bb_mix = None` costs one line and removes that
    entire failure mode.
    """

    class BareSizing:
        open_bb, threebet_mult, fourbet_mult = 2.5, 3.0, 2.0

    with pytest.raises(AttributeError):
        preflop_raise_to(BareSizing(), "open", last_raise_to=3.0, limpers=0,
                         min_bb=2.0, max_bb=200.0, rng=random.Random(1))

    class DeclaredSizing(BareSizing):
        open_bb_mix = threebet_mult_mix = fourbet_mult_mix = None

    got = preflop_raise_to(DeclaredSizing(), "open", last_raise_to=3.0,
                           limpers=0, min_bb=2.0, max_bb=200.0,
                           rng=random.Random(1))
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
    {"nan": 1.0},                    # a legal JSON key that parses to NaN
    {"inf": 1.0},
    {"3.0": float("nan")},           # NaN weight
    {"3.0": float("inf")},
])
def test_a_malformed_mix_is_rejected(bad):
    """`"nan"` and `"inf"` are legal JSON object keys and `float()` accepts
    both. A NaN size would reach the engine and pass its legality comparisons,
    because every comparison against NaN is False, and poison the pot."""
    with pytest.raises(ValidationError):
        _sizing(open_bb_mix=bad)


def test_a_misspelled_mix_field_is_rejected():
    """Without `extra="forbid"` a typo loads cleanly, leaves the real field at
    None, and silently turns the whole feature into a no-op nothing reports."""
    with pytest.raises(ValidationError):
        PersonaSizing(open_bb=3.0, threebet_mult=3.5, fourbet_mult=2.4,
                      open_bb_mxi={"2.5": 1.0})


def test_a_well_formed_mix_is_accepted():
    assert _sizing(open_bb_mix={"2.5": 0.25, "3.0": 0.75}).open_bb_mix


# --- the size draw never precedes the action draw ---------------------------

class _RecordingRng(random.Random):
    """Records the population of every `choices()` call, in order."""

    def __init__(self, seed):
        super().__init__(seed)
        self.calls: list[list] = []

    def choices(self, population, weights=None, *args, **kwargs):
        self.calls.append(list(population))
        return super().choices(population, weights, *args, **kwargs)


_ACTION_NAMES = {"raise", "fold", "call", "limp", "3bet", "4bet", "5bet_shove"}


def _mixed_pack():
    """A real pack with sizing mixes authored on every lever, so the size draw
    is actually reachable. Shipped packs author none (T2b)."""
    pack = load_persona_packs()["tag"].model_copy(deep=True)
    pack.sizing.open_bb_mix = {"2.5": 0.5, "3.5": 0.5}
    pack.sizing.threebet_mult_mix = {"3.0": 0.5, "3.5": 0.5}
    pack.sizing.fourbet_mult_mix = {"2.1": 0.5, "2.4": 0.5}
    return pack


@pytest.mark.parametrize("facing,current_bet_to,limpers", [
    ("unopened", 0.0, 0),
    ("vs_limpers", 1.0, 2),
    ("vs_rfi", 3.0, 0),
    ("vs_3bet", 10.0, 0),
])
def test_the_action_is_drawn_before_the_size_on_the_live_path(facing,
                                                              current_bet_to,
                                                              limpers):
    """Exercises `_preflop_decision`, the code the change actually wired.

    Asserting on `sample_preflop_action` alone would pass even if `rng=rng`
    were deleted from `play.py`, or if sizing were reordered ahead of the
    action — the feature would be disconnected and the test still green.
    """
    from app.domain.table.play import _preflop_decision

    legal = [
        LegalAction(action=ActionType.FOLD),
        LegalAction(action=ActionType.CALL, min_bb=max(current_bet_to, 1.0)),
        LegalAction(action=ActionType.RAISE, min_bb=2.0, max_bb=200.0),
    ]
    seen_size_draw = False
    for seed in range(40):
        rng = _RecordingRng(seed)
        _preflop_decision(_mixed_pack(), Position.BTN, facing,
                          (Card("As"), Card("Kd")), legal, rng,
                          current_bet_to, limpers, is_opener=False)
        assert rng.calls, "the action draw must consume the rng"
        assert set(rng.calls[0]) & _ACTION_NAMES, rng.calls[0]
        for population in rng.calls[1:]:
            assert not (set(population) & _ACTION_NAMES), (
                "only the first draw may be the action draw")
            seen_size_draw = True
    assert seen_size_draw, (
        f"no size draw ever happened for facing={facing}; the rng is not "
        "reaching preflop_raise_to, so this path is untested")


def test_a_forced_jam_draws_the_action_only():
    """The 5-bet node takes the jam value rather than a lever, so it must not
    consume a size draw at all."""
    from app.domain.table.play import _preflop_decision

    legal = [
        LegalAction(action=ActionType.FOLD),
        LegalAction(action=ActionType.CALL, min_bb=20.0),
        LegalAction(action=ActionType.RAISE, min_bb=100.0, max_bb=100.0),
    ]
    for seed in range(20):
        rng = _RecordingRng(seed)
        _preflop_decision(_mixed_pack(), Position.BTN, "vs_4bet",
                          (Card("As"), Card("Kd")), legal, rng, 25.0, 0,
                          is_opener=False)
        assert len(rng.calls) == 1, rng.calls


# --- the bands T2b's values will have to respect ----------------------------

def test_checked_in_persona_schema_matches_the_model():
    """Nothing in the app reads `persona.schema.json`, so drift is otherwise
    silent — the same reason its sibling `contentpack.schema.json` has a sync
    test (`test_content.py::test_checked_in_schema_matches_model`)."""
    import json
    from pathlib import Path

    from app.domain.content.models import PersonaPack

    committed = json.loads(
        (Path(__file__).resolve().parents[2] / "content" / "schema"
         / "persona.schema.json").read_text()
    )
    assert committed == PersonaPack.model_json_schema(), (
        "content/schema/persona.schema.json is stale — regenerate it from "
        "PersonaPack.model_json_schema()")


def test_a_rejected_size_mix_does_not_talk_about_pot_fractions():
    """The shared validator is also used for postflop pot fractions. A preflop
    mix's keys are bb amounts and multipliers, and borrowing the wrong noun
    sends an author looking in the wrong place."""
    with pytest.raises(ValidationError) as exc:
        _sizing(open_bb_mix={"bogus": 1.0})
    assert "pot fraction" not in str(exc.value)
    assert "size" in str(exc.value)


def test_a_preflop_mix_is_not_judged_against_the_postflop_grid():
    """The postflop grid check must never move into the shared validator.

    Preflop mix keys are bb amounts and raise multipliers; postflop keys are
    pot fractions from {0.33, 0.5, 0.75, 1.0, 1.5}. A grid check placed in
    `_validate_bucket_dist` would reject every preflop key and the two features
    would fight — so a plain 3.0bb open must stay valid.
    """
    assert _sizing(open_bb_mix={"3.0": 1.0}).open_bb_mix == {"3.0": 1.0}


def test_grading_band_constants_match_the_grader():
    """T2b authors sizes against these caps, so a drift in the grader must
    fail here rather than silently widening what T2b may author."""
    from app.domain.table import grade_map_preflop as gmp

    assert gmp._OVERSIZE_OPEN_CAP == OPEN_CAP
    assert gmp._THREEBET_MULT_CAP == THREEBET_MULT_CAP
    assert gmp._FOURBET_MULT_CAP == FOURBET_MULT_CAP
