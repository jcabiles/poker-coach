"""W0-c — the seeded node-trace pack produces a structurally valid trace.

This asserts the pack RUNS and logs the required fields for the full seed set;
it does NOT assert realism thresholds (that is each behavior slice's job). The
value is that the trace exists for later "right stat, wrong node" review.

T-TRACE adds three node assertions on top: the W3 position multiplier and the
W3-c busted-draw river bluff are now LIVE in the trace (they resolved to
identity while `build_trace` passed no `context=`), and the spots where the
context is correctly inert are pinned as such.
"""

from __future__ import annotations

from app.domain.action import ActionType
from app.domain.archetypes import VillainType
from app.domain.table.postflop_context import BustedDraw, busted_draw_kind
from tests.node_trace import SPOTS, build_trace

_ACTION_VALUES = {a.value for a in ActionType}


def _bet_probs() -> dict[tuple[str, str], dict[str, float]]:
    return {(r.persona, r.spot_id): r.action_probabilities for r in build_trace()}


def _spot(spot_id: str):
    return next(s for s in SPOTS if s.spot_id == spot_id)


def test_node_trace_pack_runs_and_is_well_formed():
    rows = build_trace()
    # One row per persona x spot.
    assert len(rows) == len(list(VillainType)) * len(SPOTS)
    for r in rows:
        assert r.persona and r.spot_id and r.bucket and r.draw_class and r.prescription
        # Chosen action is a real seeded sample from the ActionType space
        # (never a forced population[0]).
        assert r.chosen_action in _ACTION_VALUES
        probs = r.action_probabilities
        tag = f"{r.persona}/{r.spot_id}"
        assert probs, f"{tag}: empty probabilities"
        # Captured population is the ACTION draw (ActionType values), never the
        # sizing draw (Sol #8).
        assert set(probs) <= _ACTION_VALUES, f"{tag}: non-action keys {set(probs)}"
        # Normalized distribution: sums to 1 (or the deterministic fallback 1.0).
        assert abs(sum(probs.values()) - 1.0) < 1e-6, f"{tag}: sum {sum(probs.values())}"
        # The seeded chosen action is one the sampler actually weighed.
        assert r.chosen_action in probs, f"{tag}: chose {r.chosen_action} not in {set(probs)}"


def test_node_trace_no_degenerate_zero_merit_fallback():
    """Every chosen spot must exercise a real candidate set (>=2 weighted
    actions) — none may collapse to the single-action zero-total-merit fallback
    (`range_estimate`-style capture would yield len 1). Guards Sol #9 / the
    theory-reviewer's fixture-degeneracy nit."""
    for r in build_trace():
        assert len(r.action_probabilities) >= 2, (
            f"{r.persona}/{r.spot_id}: degenerate fallback {r.action_probabilities}"
        )


def test_node_trace_is_deterministic():
    """Same seed -> identical trace (seeded replay must be reproducible for the
    fit loop)."""
    assert build_trace(seed=123) == build_trace(seed=123)


def test_position_multiplier_is_live_in_the_trace():
    """T-TRACE — the IP/OOP twins must differ; the x1.25/x0.75 MERIT ratio
    lands at 1.348 in PROBABILITY space.

    `action_probabilities` is a NORMALIZED MERIT vector captured before the
    draw, so these are exact (zero sampling variance) — a tolerance is carried
    only against float formatting. nit authors `position_sensitivity=1.0` and
    `_POSITION_AGG_DELTA=0.25`, so the BET candidate is x1.25 IP / x0.75 OOP —
    a merit ratio of 1.667. The OBSERVED ratio is 0.4783/0.3548 = 1.348, and
    that is not a discrepancy: merits are clamped >=0 then normalized against an
    unchanged CHECK merit, so a merit multiplier is never the frequency change
    it produces. Do not read these as odds-space values. While `build_trace`
    passed no `context=`, BOTH read 0.4231 (identity).

    CHARACTERIZATION VALUES, not targets: the pins record what the levers do
    TODAY. Their LEVEL is unjustified — `position_sensitivity` is a FIT SEED at
    LOW confidence — so a later realism slice is EXPECTED to move them and
    should re-record, not treat 0.4783 as a bar it is breaking. What this test
    defends is that position is WIRED and DIRECTIONAL (IP > OOP), not the
    magnitude.
    """
    ip_spot, oop_spot = _spot("flop_ip_toppair_dry"), _spot("flop_oop_toppair_dry")
    # The twin varies on POSITION ALONE — everything else byte-identical.
    assert oop_spot._replace(
        spot_id=ip_spot.spot_id, prescription=ip_spot.prescription, in_position=True
    ) == ip_spot

    probs = _bet_probs()
    assert abs(probs[("nit", "flop_ip_toppair_dry")]["bet"] - 0.4783) < 0.001
    assert abs(probs[("nit", "flop_oop_toppair_dry")]["bet"] - 0.3548) < 0.001


def test_busted_draw_river_bluff_is_live_in_the_trace():
    """T-TRACE — the W3-c busted-barrel story bluff fires in the trace.

    Gated on `context.bet_prev_street` + a busted draw, so it read 0.0156 (the
    street-decayed generic air bluff alone) while the context was blind. The
    draw class is DERIVED from the spot's own cards by the same helper
    production uses — the spot never asserts its own busted-ness.

    TWO legs, because nit's reading is CONFOUNDED: the spot is authored
    `in_position=True`, so nit's 0.3657 carries a x1.25 position boost on top of
    the W3-c term (which alone is ~0.3156 — the same assertion would FAIL at
    0.2570 with the spot flipped OOP). `maniac` authors NO
    `position_sensitivity`, so its multiplier short-circuits to exactly 1.0
    (measured 0.5262 both IP and OOP) — a position-free witness that the
    busted-draw term is live on its own.

    Why `maniac` and not a tighter persona: the bar 0.30 is the literal value of
    `_BUSTED_RIVER_BLUFF[STRAIGHT]`, a self-declared FIT SEED, so a tight
    persona's leg reduces to "0.30 + its own tiny bluff mass > 0.30" — no
    persona-discriminating power, and it would break on the first legitimate
    re-fit of that seed while reading as "the bluff went dead". `calling_station`
    would clear the bar by 0.0085; more to the point, "a calling station bluffs a
    busted river draw >30% of the time" is NOT a property we want held true
    (2-6% is the realistic range), so pinning it as a CI pass condition is
    backwards. `maniac` is the one archetype for which the claim is realistic,
    and it clears by 0.226.
    """
    spot = _spot("river_busted_draw")
    assert busted_draw_kind(spot.hole, list(spot.board)) is BustedDraw.STRAIGHT
    assert spot.bet_prev_street is True  # the gate; without it the bluff is dead
    probs = _bet_probs()
    assert probs[("nit", "river_busted_draw")]["bet"] > 0.30
    assert probs[("maniac", "river_busted_draw")]["bet"] > 0.30


def test_facing_spots_are_position_inert_by_design():
    """T-TRACE — the two FACING spots (and ONLY those two) do not move when
    position flips. This is CORRECT, not a plumbing failure, and is pinned here
    so nobody "repairs" it.

    `_position_agg_mult` is applied behind the `agg_action is ActionType.BET`
    gate in `personas_postflop.py`, i.e. to the aggressor's own BET candidate on
    the unopened path. It reaches neither the matched-with-option branch (that
    sets `agg_action = RAISE`, so a check-raise node is position-INERT too) nor
    the facing branch (FOLD/CALL/RAISE), which carries no position term because
    the OOP *defence* damp is a later, unbuilt slice — see the theory contract's
    P1 row, which scopes W3-b to the aggressor side. Adding one here would be an
    authored-strategy change inside a test-only ticket, in a region another
    ticket owns.

    Note the inert set is exactly two spots, not more: the multiplier is
    SYMMETRIC (`1 ± 0.25 * position_sensitivity`), so the authored-OOP unopened
    spots are damped x0.75 rather than left alone.

    So this pins TODAY'S BOUNDARY, not a permanent invariant: when the defence
    slice ships, this test is expected to be updated, not treated as a
    regression.
    """
    facing = ("flop_facing_bet_strong_draw", "flop_lowspr_commit_overpair")
    assert {s.spot_id for s in SPOTS} >= set(facing)
    # Same length + same order => same per-spot seed, so the ONLY difference is
    # the flipped field.
    flipped = tuple(
        s._replace(in_position=not s.in_position) if s.spot_id in facing else s
        for s in SPOTS
    )
    assert build_trace(spots=flipped) == build_trace()
