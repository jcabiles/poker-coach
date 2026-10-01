"""M1 T4: the 6-max baseline tool's fidelity check and seeded simulation.

Three legs:
1. `fidelity_check` oracle — hand-made counts for PASS (0 and 1 miss, owner
   ruling 2026-09-26), FAIL (2 misses), CANT_TELL (7 eligible), the
   30-chance cutoff, and the inclusive edge of one comparison's pass range.
2. `run_baseline` — deterministic across two calls with the same seed, and
   every hand is a 6-seat table with only 6-max position labels.
3. `build_pairs` — pins the spec's grouping rules (section 2): each real bot
   seat pairs with the right simulated group, the tag group is exactly seats
   {3, 4}, and seat 0 (the owner's stand-in) never appears in any pair.
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


def _counts(*groups: str) -> dict[str, dict[str, tuple[int, int]]]:
    """A group->{stat: (k, n)} dict with a distinct (k, n) per group so a
    mis-paired test fails loudly instead of by coincidence."""
    return {g: {"VPIP": (i + 1, 100), "PFR": (i + 1, 50)} for i, g in enumerate(groups)}


def test_sim_groups_tag_is_exactly_seats_3_and_4():
    assert sb.SIM_GROUPS["tag"] == [3, 4]


def test_seat_0_stand_in_is_never_pooled_with_a_bot_group():
    for name, seats in sb.SIM_GROUPS.items():
        if name != "stand-in tag (seat 0)":
            assert 0 not in seats


def test_build_pairs_has_exactly_ten_pairs_vpip_and_pfr_times_five_bots():
    real = _counts("nit", "lag", "tag seat 3", "tag seat 4", "station")
    sim = _counts("nit", "lag", "tag", "station", "stand-in tag (seat 0)")
    pairs = sb.build_pairs(real, sim)
    assert len(pairs) == 10
    assert {p["stat"] for p in pairs} == {"VPIP", "PFR"}
    assert {p["bot"] for p in pairs} == {
        "nit",
        "lag",
        "tag seat 3",
        "tag seat 4",
        "station",
    }


def test_build_pairs_grouping_matches_the_spec_section_2():
    real = _counts("nit", "lag", "tag seat 3", "tag seat 4", "station")
    sim = _counts("nit", "lag", "tag", "station", "stand-in tag (seat 0)")
    pairs = sb.build_pairs(real, sim)
    by_bot_stat = {(p["bot"], p["stat"]): p for p in pairs}

    # nit -> nit, lag -> lag, station -> station.
    for bot, group in [("nit", "nit"), ("lag", "lag"), ("station", "station")]:
        p = by_bot_stat[(bot, "VPIP")]
        assert (p["sim_k"], p["sim_n"]) == sim[group]["VPIP"]

    # tag seat 3 and tag seat 4 both pair with the pooled tag group, never
    # with the seat-0 stand-in's own group.
    for bot in ("tag seat 3", "tag seat 4"):
        p = by_bot_stat[(bot, "VPIP")]
        assert (p["sim_k"], p["sim_n"]) == sim["tag"]["VPIP"]
        assert (p["sim_k"], p["sim_n"]) != sim["stand-in tag (seat 0)"]["VPIP"]

    # seat 0's stand-in group never appears as a bot in any pair.
    assert "stand-in tag (seat 0)" not in {p["bot"] for p in pairs}


def test_measure_reports_the_m2_stats_for_every_group():
    hands = sb.run_baseline(120, 7)
    out = sb.measure(hands, sb.SEATS, sb.SIM_GROUPS)
    for counts in out.values():
        k_flop, n_flop = counts[sb.RAISE_RATE_FLOP]
        k_all, n_all = counts[sb.RAISE_RATE_ALL]
        assert 0 <= k_flop <= n_flop <= n_all and k_flop <= k_all <= n_all
        mult = counts[sb.RAISE_MULTIPLE]
        if mult["n"]:
            assert 1.0 <= mult["median"] and mult["p90"] >= mult["median"]
            assert 0.0 <= mult["share_4x"] <= 1.0
        assert counts[sb.NON_AGGRESSOR_BET]["n"] >= 0
    assert sum(c[sb.RAISE_MULTIPLE]["n"] for c in out.values()) > 0
    assert sum(c[sb.NON_AGGRESSOR_BET]["n"] for c in out.values()) > 0

    # Independent recomputation straight from `stats_for`, not the tool's helper.
    replays = {h.hand_no: sb.replay(h) for h in hands}
    settles = {h.hand_no: sb.settle_hand(h) for h in hands}
    nets = {k: v[0] for k, v in settles.items()}
    shows = {k: v[1] for k, v in settles.items()}
    for name, seat_list in sb.SIM_GROUPS.items():
        st, _ = sb.stats_for(seat_list, sb.SEATS, hands, replays, nets, shows)
        assert out[name][sb.RAISE_RATE_FLOP] == (
            int(st["flop_raise_vs_bet"]),
            int(st["flop_faced_bet"]),
        )
        assert out[name][sb.RAISE_RATE_ALL] == (
            int(st["flop_raise_vs_bet"] + st["turn_raise_vs_bet"] + st["river_raise_vs_bet"]),
            int(st["flop_faced_bet"] + st["turn_faced_bet"] + st["river_faced_bet"]),
        )
    assert any(c[sb.RAISE_RATE_ALL][1] > c[sb.RAISE_RATE_FLOP][1] for c in out.values())


def test_summarise_multiples_on_known_values():
    got = sb._summarise_multiples([2.0, 3.0, 4.0, 5.0])
    assert got == {"n": 4, "median": 3.5, "mean": 3.5, "p90": 5.0, "share_4x": 0.5}
    assert sb._summarise_multiples([]) == {"n": 0}
    assert sb._summarise_multiples([3.0])["p90"] == 3.0
