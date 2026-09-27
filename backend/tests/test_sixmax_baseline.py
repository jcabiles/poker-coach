"""M1 T4: the 6-max baseline tool's fidelity check and seeded simulation.

Two legs:
1. `fidelity_check` oracle — hand-made counts for PASS (0 and 1 miss, owner
   ruling 2026-09-26), FAIL (2 misses), CANT_TELL (7 eligible), the
   30-chance cutoff, and the inclusive edge of one comparison's pass range.
2. `run_baseline` — deterministic across two calls with the same seed, and
   every hand is a 6-seat table with only 6-max position labels.
"""

from __future__ import annotations

from tools import sixmax_baseline as sb

# real 40/200 = 20% vs sim 400/2000 = 20%: comfortably inside.
_PASS = {"real_k": 40, "real_n": 200, "sim_k": 400, "sim_n": 2000}
# real 180/200 = 90% vs sim 20%: far outside.
_MISS = {"real_k": 180, "real_n": 200, "sim_k": 400, "sim_n": 2000}


def _pairs(n_pass: int, n_miss: int, **override) -> list[dict]:
    kinds = [_PASS] * n_pass + [_MISS] * n_miss
    return [{"bot": f"bot{i}", "stat": "VPIP", **kind, **override} for i, kind in enumerate(kinds)]


def test_pass_with_zero_misses():
    result = sb.fidelity_check(_pairs(10, 0))
    assert result["verdict"] == "PASS"
    assert result["eligible"] == 10
    assert result["misses"] == 0
    assert all(r["passed"] is True for r in result["rows"])


def test_pass_with_exactly_one_miss():
    result = sb.fidelity_check(_pairs(9, 1))
    assert result["verdict"] == "PASS"
    assert result["misses"] == 1
    assert [r["passed"] for r in result["rows"]].count(False) == 1


def test_fail_with_two_misses():
    result = sb.fidelity_check(_pairs(8, 2))
    assert result["verdict"] == "FAIL"
    assert result["misses"] == 2


def test_cant_tell_with_seven_eligible():
    pairs = _pairs(7, 0) + _pairs(0, 3, real_k=9, real_n=10)
    result = sb.fidelity_check(pairs)
    assert result["eligible"] == 7
    assert result["verdict"] == "CANT_TELL"


def test_real_n_29_is_excluded_and_30_is_included():
    # Nine passing pairs plus one far-off pair: at 29 real chances the miss
    # is ignored; at 30 it counts.
    excluded = sb.fidelity_check(_pairs(9, 0) + _pairs(0, 1, real_k=27, real_n=29))
    assert excluded["eligible"] == 9
    assert excluded["misses"] == 0
    assert excluded["rows"][-1]["eligible"] is False
    assert excluded["rows"][-1]["passed"] is None
    assert excluded["verdict"] == "PASS"

    included = sb.fidelity_check(_pairs(8, 0) + _pairs(0, 2, real_k=28, real_n=30))
    assert included["eligible"] == 10
    assert included["misses"] == 2
    assert included["verdict"] == "FAIL"


def test_comparison_range_is_inclusive_at_both_edges():
    # Dyadic values so the edge is exact in floating point: h = (0.75-0.25)/2
    # = 0.25, so the pass range is [0.5-0.25, 0.25+0.25] = [0.25, 0.5].
    passed, lo, hi = sb._within(0.5, 0.25, 0.75, sim_lo=0.5, sim_hi=0.25)
    assert (lo, hi) == (0.25, 0.5)
    assert passed is True  # real rate exactly at sim_hi + h
    assert sb._within(0.25, 0.0, 0.5, sim_lo=0.5, sim_hi=0.75)[0] is True  # at sim_lo - h
    assert sb._within(0.5 + 1e-9, 0.25, 0.75, sim_lo=0.5, sim_hi=0.25)[0] is False


def test_fidelity_row_bounds_use_sim_interval_widened_by_real_half_width():
    row = sb.fidelity_check(_pairs(1, 0))["rows"][0]
    real_lo, real_hi = sb.wilson(40, 200)
    sim_lo, sim_hi = sb.wilson(400, 2000)
    h = (real_hi - real_lo) / 2
    assert row["bounds"] == (sim_lo - h, sim_hi + h)


def test_run_baseline_is_deterministic_across_two_calls():
    a = sb.run_baseline(60, 1)
    b = sb.run_baseline(60, 1)
    assert len(a) == len(b) == 60
    assert [h.history for h in a] == [h.history for h in b]
    assert [[s.hole_cards for s in h.state.seats] for h in a] == [
        [s.hole_cards for s in h.state.seats] for h in b
    ]


def test_run_baseline_is_six_max_with_rotating_button():
    hands = sb.run_baseline(60, 1)
    for i, h in enumerate(hands):
        assert sorted(h.seats) == [0, 1, 2, 3, 4, 5]
        assert set(h.pos_of.values()) == set(sb.SIXMAX_POSITIONS)
        assert h.button == i % 6
        assert h.state.hand_over
