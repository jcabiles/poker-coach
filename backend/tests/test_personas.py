"""Persona pack schema + engine tests, incl. the S3 closed-loop stat bands.

The four stat rows measure **AUTHORED RANGE WIDTH**, not tracker stats. The
docstring here used to claim "open-freq ~ VPIP, first-in-raise ~ PFR"; that
equivalence is FALSE at 9-max and was the root of a wrong test (see the long
note above `BANDS`). Population VPIP/PFR/gap live in metric #3 of the S4
harness (`tests/test_personas_postflop.py::_persona_stats_ext`), which plays
whole hands; this file only asks "how wide is each node as authored?"
(spec `docs/ai-dlc/specs/simulate-s3.md`).
"""

import json
import random

import pytest
from pydantic import ValidationError

from app.domain.archetypes import VillainType
from app.domain.content.models import PersonaPack
from app.domain.personas import load_persona_packs, sample_preflop_action
from app.domain.spot import ActionType, Position
from app.domain.table.deck import deal_hand, positions_for_button

# ---------------------------------------------------------------- fixtures


def _pack(preflop: list[dict], persona: str = "tag") -> dict:
    return {
        "id": f"persona_{persona}",
        "version": "1.0.0",
        "domain": "persona",
        "persona": persona,
        "display_name": persona,
        "sizing": {"open_bb": 2.5, "threebet_mult": 3.0, "fourbet_mult": 2.2},
        "preflop": preflop,
    }


FIXTURE = PersonaPack.model_validate(
    _pack(
        [
            {
                "facing": "unopened",
                "positions": ["BTN"],
                "mixes": [
                    {"combos": "AA,KK", "weights": {"raise": 1.0}},
                    {"combos": "22+", "weights": {"raise": 0.5, "limp": 0.5}},
                ],
            },
            {
                "facing": "unopened",
                "positions": None,
                "mixes": [{"combos": "QQ+", "weights": {"raise": 1.0}}],
            },
            {
                "facing": "vs_rfi",
                "positions": None,
                "mixes": [
                    {"combos": "77", "weights": {"call": 1.0}},
                    {"combos": "AA", "weights": {"3bet": 0.4}},  # remainder = implicit fold
                ],
            },
        ]
    )
)

AA = ("As", "Ad")
SEVENS = ("7c", "7d")
FIVES = ("5c", "5d")
TREY_DEUCE = ("3c", "2d")

# ------------------------------------------------------- schema validation


def test_persona_pack_rejects_bad_action_vocabulary():
    with pytest.raises(ValidationError, match="not allowed facing"):
        _validate([{"facing": "unopened", "positions": None,
                    "mixes": [{"combos": "AA", "weights": {"call": 1.0}}]}])


def test_persona_pack_rejects_weights_sum_above_one():
    with pytest.raises(ValidationError, match="sum"):
        _validate([{"facing": "unopened", "positions": None,
                    "mixes": [{"combos": "AA", "weights": {"raise": 0.7, "limp": 0.7}}]}])


def test_persona_pack_rejects_unsupported_range_token():
    with pytest.raises(ValidationError, match="range token"):
        _validate([{"facing": "unopened", "positions": None,
                    "mixes": [{"combos": "A5s-A2s", "weights": {"raise": 1.0}}]}])


def test_persona_pack_rejects_explicit_node_after_wildcard():
    with pytest.raises(ValidationError, match="after wildcard"):
        _validate([
            {"facing": "unopened", "positions": None,
             "mixes": [{"combos": "AA", "weights": {"raise": 1.0}}]},
            {"facing": "unopened", "positions": ["BTN"],
             "mixes": [{"combos": "AA", "weights": {"raise": 1.0}}]},
        ])


def test_persona_pack_rejects_second_wildcard_per_facing():
    with pytest.raises(ValidationError, match="wildcard"):
        _validate([
            {"facing": "unopened", "positions": None,
             "mixes": [{"combos": "AA", "weights": {"raise": 1.0}}]},
            {"facing": "unopened", "positions": None,
             "mixes": [{"combos": "KK", "weights": {"raise": 1.0}}]},
        ])


def test_persona_pack_rejects_overlapping_explicit_positions():
    with pytest.raises(ValidationError, match="duplicate position coverage"):
        _validate([
            {"facing": "unopened", "positions": ["BTN", "CO"],
             "mixes": [{"combos": "AA", "weights": {"raise": 1.0}}]},
            {"facing": "unopened", "positions": ["CO"],
             "mixes": [{"combos": "KK", "weights": {"raise": 1.0}}]},
        ])


def test_persona_pack_allows_one_wildcard_per_role_and_rejects_tag_after_untagged():
    """N-3BSTRATA: the wildcard/ordering laws hold PER (facing, role) — an
    `opener` and a `cold` wildcard coexist for one facing — but a role-tagged
    node may not FOLLOW an untagged one, which serves both roles and would
    shadow it dead."""
    _validate([
        {"facing": "vs_3bet", "positions": None, "role": "opener",
         "mixes": [{"combos": "AA", "weights": {"call": 1.0}}]},
        {"facing": "vs_3bet", "positions": None, "role": "cold",
         "mixes": [{"combos": "AA", "weights": {"call": 1.0}}]},
    ])
    with pytest.raises(ValidationError, match="role-tagged node after untagged"):
        _validate([
            {"facing": "vs_3bet", "positions": None,
             "mixes": [{"combos": "AA", "weights": {"call": 1.0}}]},
            {"facing": "vs_3bet", "positions": None, "role": "opener",
             "mixes": [{"combos": "AA", "weights": {"4bet": 1.0}}]},
        ])
    with pytest.raises(ValidationError, match="wildcard"):
        _validate([
            {"facing": "vs_3bet", "positions": None, "role": "opener",
             "mixes": [{"combos": "AA", "weights": {"call": 1.0}}]},
            {"facing": "vs_3bet", "positions": None, "role": "opener",
             "mixes": [{"combos": "KK", "weights": {"call": 1.0}}]},
        ])


def test_persona_pack_rejects_unknown_role():
    with pytest.raises(ValidationError):
        _validate([{"facing": "vs_3bet", "positions": None, "role": "squeezer",
                    "mixes": [{"combos": "AA", "weights": {"call": 1.0}}]}])


def _validate(preflop: list[dict]) -> PersonaPack:
    return PersonaPack.model_validate(_pack(preflop))


# ------------------------------------------------ N-3BSTRATA — role matching

_ROLE_FIXTURE = PersonaPack.model_validate(
    _pack(
        [
            {
                "facing": "vs_3bet",
                "positions": None,
                "role": "opener",
                "mixes": [{"combos": "AA", "weights": {"4bet": 1.0}}],
            },
            {
                "facing": "vs_3bet",
                "positions": None,
                "role": "cold",
                "mixes": [{"combos": "AA", "weights": {"call": 1.0}}],
            },
            {
                "facing": "vs_4bet",  # untagged: serves BOTH strata
                "positions": None,
                "mixes": [{"combos": "AA", "weights": {"call": 1.0}}],
            },
        ]
    )
)


def test_role_tagged_node_matches_only_its_stratum():
    rng = random.Random(1)
    assert sample_preflop_action(
        _ROLE_FIXTURE, Position.BTN, "vs_3bet", AA, rng, is_opener=True
    ).name == "4bet"
    assert sample_preflop_action(
        _ROLE_FIXTURE, Position.BTN, "vs_3bet", AA, rng, is_opener=False
    ).name == "call"
    # A caller that does not track the stratum selects NO tagged node — the
    # documented fail-loud contract (a stratified pack needs a stratum-aware
    # caller; both production callers pass the flag).
    assert sample_preflop_action(
        _ROLE_FIXTURE, Position.BTN, "vs_3bet", AA, rng
    ).name == "fold"


def test_untagged_node_serves_every_stratum():
    rng = random.Random(2)
    for is_opener in (True, False, None):
        assert sample_preflop_action(
            _ROLE_FIXTURE, Position.BTN, "vs_4bet", AA, rng, is_opener=is_opener
        ).name == "call"


def test_shipped_untagged_packs_are_role_blind():
    """The default-off contract on the SHIPPED content: for every pack with no
    `role` anywhere (station/fish/nit/tag), node selection is identical for
    is_opener True/False/None at every position, facing and hand class — i.e.
    this slice cannot have moved their behaviour. Same-seed rngs make the
    comparison exact draw-for-draw, not distributional."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    ranks = "23456789TJQKA"
    facings = ("unopened", "vs_limpers", "vs_rfi", "vs_3bet", "vs_4bet")
    classes = [
        (r1 + "h", r2 + s) for i, r1 in enumerate(ranks) for j, r2 in enumerate(ranks)
        if i > j for s in ("h", "d")
    ] + [(r + "h", r + "d") for r in ranks]
    untagged = [
        vt for vt, pack in packs.items() if all(n.role is None for n in pack.preflop)
    ]
    assert len(untagged) == 4, f"expected 4 untagged packs, got {sorted(v.value for v in untagged)}"
    for vt in untagged:
        pack = packs[vt]
        for facing in facings:
            for pos in Position:
                draws = []
                for is_opener in (None, True, False):
                    rng = random.Random(4242)
                    draws.append(
                        tuple(
                            sample_preflop_action(
                                pack, pos, facing, hole, rng, is_opener=is_opener
                            ).name
                            for hole in classes
                        )
                    )
                assert draws[0] == draws[1] == draws[2], (
                    f"{vt.value} {facing} {pos.value}: role argument changed the draw"
                )


def test_loader_raises_on_duplicate_persona(tmp_path):
    pack = _pack([{"facing": "unopened", "positions": None,
                   "mixes": [{"combos": "AA", "weights": {"raise": 1.0}}]}])
    (tmp_path / "a.json").write_text(json.dumps(pack))
    (tmp_path / "b.json").write_text(json.dumps(pack))
    with pytest.raises(ValueError, match="duplicate persona"):
        load_persona_packs(tmp_path)


# --------------------------------------------------------------- sampling


def test_wire_translation_limp_is_call_and_3bet_is_raise():
    rng = random.Random(7)
    # BTN 55 hits the mixed 22+ row: limp draws must translate to CALL.
    names = set()
    for _ in range(200):
        act = sample_preflop_action(FIXTURE, Position.BTN, "unopened", FIVES, rng)
        names.add(act.name)
        assert act.action == (ActionType.CALL if act.name == "limp" else ActionType.RAISE)
    assert names == {"limp", "raise"}  # a mixed row genuinely mixes

    threebet = sample_preflop_action(FIXTURE, Position.SB, "vs_rfi", AA, random.Random(0))
    while threebet.name == "fold":  # 0.4 3bet / 0.6 implicit fold
        threebet = sample_preflop_action(FIXTURE, Position.SB, "vs_rfi", AA, rng)
    assert threebet == ("3bet", ActionType.RAISE)


def test_first_matching_mix_wins():
    # AA on BTN is in both mixes; the first (raise 1.0) must win every time.
    rng = random.Random(3)
    for _ in range(50):
        assert sample_preflop_action(FIXTURE, Position.BTN, "unopened", AA, rng).name == "raise"


def test_explicit_position_node_beats_wildcard_and_wildcard_covers_rest():
    rng = random.Random(11)
    # 77 unopened: BTN hits the explicit node (22+ row); CO falls to wildcard (QQ+ only) -> fold.
    assert sample_preflop_action(FIXTURE, Position.BTN, "unopened", SEVENS, rng).name != "fold"
    assert sample_preflop_action(FIXTURE, Position.CO, "unopened", SEVENS, rng).name == "fold"


def test_unmatched_hand_or_facing_folds():
    rng = random.Random(5)
    assert sample_preflop_action(FIXTURE, Position.CO, "unopened", TREY_DEUCE, rng) == (
        "fold",
        ActionType.FOLD,
    )
    assert sample_preflop_action(FIXTURE, Position.CO, "vs_4bet", AA, rng).name == "fold"


def test_same_seed_is_deterministic():
    def draw(seed):
        rng = random.Random(seed)
        return [
            sample_preflop_action(FIXTURE, Position.BTN, "unopened", FIVES, rng).name
            for _ in range(100)
        ]

    assert draw(42) == draw(42)
    assert draw(42) != draw(43)  # and the mix isn't degenerate


# ---------------------------------------------- closed-loop stat bands (S3)

# ============================ WHAT THESE BANDS MEASURE (read before editing) ==
# `_stats` samples EVERY seat at `facing="unopened"` and divides by DEALS*9. It
# therefore measures **AUTHORED RANGE WIDTH** — "what fraction of dealt hands
# does this pack's `unopened` node open with, averaged over the nine seats" —
# and NOT population VPIP/PFR, which is what a tracker reports.
#
# Those are DIFFERENT QUANTITIES and cannot both be satisfied by one band. At
# 9-max a seat usually arrives already FACING an open, so its decision is routed
# to `vs_rfi` / `vs_limpers` and never reaches the `unopened` node at all.
# Authored width is therefore always LARGER than realised PFR. Until W5-b1 the
# open-freq / first-in-raise rows held population-PFR numbers while the function
# computed authored width — the test was simply asking the wrong question, and
# it went unnoticed because at the old (much too narrow) widths the two happened
# to be close.
#
# ⚠ THE CONVERSION IS NOT A CONSTANT — do NOT re-derive these bands by dividing
# a §5 PFR target by ~0.5. That ratio was measured at the OLD narrow widths
# (nit x0.51, tag x0.54, lag x0.50) and **FALLS AS RANGES WIDEN**, because wider
# opens across the table mean more seats arrive facing a raise. Measured at the
# W5-b1 widths the ratio is ~0.35: nit reaches PFR 10.4 from 28.5 authored, lag
# PFR 17.1 from 43.2 authored. Anyone who "fixes" a failure here by scaling a
# §5 number will get a badly wrong range. Fit the width, then MEASURE.
#
# STATUS: these are **authored-width bands, DIRECTIONAL, never HARD**. They pin
# that the packs still say what this slice made them say; they are not evidence
# about persona realism. The population VPIP/PFR/gap check is **metric #3**
# (`tests/test_personas_postflop.py::_persona_stats_ext`), which plays whole
# hands, and it is REPORTED-not-gated until the W4-b single band re-anchor.
#
# TOLERANCE: the open-freq / first-in-raise bands below are the **exact
# combo-weighted authored width ±2.0pp**. Sizing: across a 25-seed sweep of
# `_stats` the worst per-row sd is 0.45pp and the worst full span is 2.16pp, so
# ±2.0pp is ~4.4 sd and leaves ≥0.9pp beyond the widest excursion observed; the
# pinned-seed value sits ≥1.4pp inside both edges of every row.
# =============================================================================

# persona -> (open-freq, first-in-raise, 3-bet, vs_rfi continue), all %.
# Rows 1-2 are AUTHORED `unopened` WIDTH (see above), not VPIP/PFR.
BANDS = {
    "passive_fish": ((28, 45), (3, 9), (0, 2), (35, 55)),
    "calling_station": ((40, 60), (0, 8), (0, 1), (50, 70)),
    # nit/tag/lag rows 1-2 RE-SCOPED by W5-b1 (2026-07-25) from population-PFR
    # numbers to the authored widths this slice actually ships (exact
    # combo-weighted: nit 28.45 open / 27.38 raise, tag 33.97, lag 43.15).
    # Rows 3-4 are UNTOUCHED — separate levers W5-b1 does not move.
    # nit rows 1-2 RE-ANCHORED by W5-b3 (2026-07-31): the nine-seat ladder
    # replaced the flat 13.6/29.1 pack (7.54% UTG rising to 21.42% BTN, limp
    # mixes byte-identical). Exact combo-weighted seat-average: 14.19 open /
    # 13.12 raise; bands = exact ±2.0pp per the tolerance note above
    # (pinned-seed reads 14.91 / 13.83, well inside). Rows 3-4 untouched.
    # T-M2 (2026-07-31) moved the anchor slightly and the BANDS were NOT
    # touched: CO/BTN small-pair opens (raise 0.3 out of the fold leg) take
    # the exact seat-average to 14.33 open / 13.26 raise, pinned seed 15.01 /
    # 14.01 — inside the frozen rows, ≥0.99pp clear of both ceilings.
    "nit": ((12, 16), (11, 15), (1, 2), (5, 15)),
    # tag 3-bet row (6,7)→(6,8) RE-TOLERATED by RR-HOLES (2026-07-31, theory
    # review F1): AQs joined the 3bet-0.8 mix (dominated-typo fix — tag
    # 3-bet AJs/ATs at 0.8 with NO action on the stronger AQs). Exact
    # combo-weighted width is 6.91% — inside the OLD band — but this row is a
    # Monte Carlo estimate whose 25-seed sweep already spanned 6.19-7.31
    # before the fix (docstring above); post-fix the pinned seed reads 7.10.
    # Widened one point rather than carving the range to keep a noisy pin
    # (the T3 precedent). Computing rows 3-4 exactly stays the documented
    # future fix.
    "tag": ((32, 36), (32, 36), (6, 8), (15, 28)),
    # lag/maniac open-freq re-anchored (P1 M3, persona-realism-p1): M3 deleted
    # the non-SB unopened open-limps from both packs, so open-freq collapsed
    # onto first-in-raise (+~0-1pp of retained SB limps). Measured at the
    # pinned seed: lag 23.55 (raise 23.29), maniac 35.64 (raise 34.62). The
    # old floors (24 / 45) counted open-limps that no longer exist — intended
    # M3 behavior, not a range regression (first-in-raise, 3-bet and
    # vs_rfi-continue all stayed inside their existing bands).
    # W5-b1 supersedes rows 1-2 of that anchor with the authored width 43.15.
    # lag rows 1-2 RE-ANCHORED by N-LAGLADDER (2026-07-31): all nine `unopened`
    # nodes were re-emitted from content/personas/ladders/lag.unopened.json,
    # tightening the ladder (mostly by cutting dominated offsuit opens in early
    # seats) at every seat. Exact combo-weighted seat-average: 39.22 open /
    # 39.22 raise (every lag unopened mix is raise/fold-only, so `_stats`
    # open-freq == first-in-raise); bands = exact ±2.0pp per the tolerance note
    # above, pinned seed reads 39.20 / 39.20. Rows 3-4 are NOT re-anchored: the
    # vs_rfi AQo carve-out holds 3-bet width constant by construction and the
    # pinned seed still reads 9.76 3-bet / 26.80 continue, both inside.
    "lag": ((37.2, 41.2), (37.2, 41.2), (8, 12), (25, 42)),
    # maniac rows 1-2 RE-ANCHORED by R10-PRE2 (2026-07-30): the ladder-separation
    # slice widened every maniac `unopened` node so the authored per-seat RFI
    # sits above the LAG's at every seat (R10-1a defect: it sat BELOW at all 9).
    # Exact combo-weighted authored first-in raise, seat-averaged: 51.78 (core
    # mixes raise 0.9, fringe 0.7, premium carve-out 1.0; every unopened mix is
    # raise/fold-only, so `_stats` open-freq == first-in-raise). Both rows =
    # exact +-2.0pp per the tolerance note above.
    # maniac vs_rfi-continue re-anchored (W3R-1): the old (45, 70) codified the
    # deleted any-two `vs_rfi "*"` cold-call. The `vs_rfi` node is now the
    # 3-tier legit loose-flat range (premium 3bet / strong 3bet-or-flat /
    # wide-marginal flat); continue-rate measured at 45.99% on the pinned seed
    # (hash-stable). Snug window around the measured value. The 3bet band stays
    # [12,20] (restored via tier-2 3bet:0.45, measured 12.59%) — NOT re-anchored.
    # maniac rows 3-4 RE-ANCHORED by W5-b4 (2026-07-31): the vs_rfi node was
    # rewritten (tier-2 3bet 0.45 -> 0.5, tier-3 flat {call 0.9} -> {3bet 0.2,
    # call 0.3, fold 0.5}, any-two {3bet 0.05, fold 0.95} catch-all — the
    # R10-1 73%-flat-call repair). Measured at the pinned seed: 3-bet 22.00,
    # vs_rfi-continue 38.69; both rows = measured ±2.0pp per the tolerance
    # note above. The 3-bet row is DELIBERATELY above the pool anchor
    # ("3-bet% full ring 4-7%, online micro-low NL cash, ledger #14 / §5a
    # conflict 3, DIRECTIONAL") — that anchor belongs to the other five
    # personas, whose rows are untouched here.
    "maniac": ((49.8, 53.8), (49.8, 53.8), (20.0, 24.0), (36.7, 40.7)),
}

DEALS = 1112  # pinned: 1,112 deals x 9 seats ~= 10k samples per facing


def _stats(pack: PersonaPack) -> tuple[float, float, float, float]:
    """Authored width of the `unopened` and `vs_rfi` nodes (see BANDS above).

    The two facings draw from SEPARATE rngs (`rng_u` / `rng_v`), both pinned to
    the same seed. They used to share one stream, which silently COUPLED the
    measurements: `sample_preflop_action` consumes a draw only when the hand
    matches a mix, so widening the `unopened` ranges displaced every subsequent
    `vs_rfi` draw and moved the 3-bet / vs_rfi-continue readings even though
    those nodes were untouched. W5-b1 hit exactly that — the tag and lag
    continue rows dropped to 14.97 / 24.69, grazing under their 15 / 25 floors,
    purely from stream displacement (the exact combo-weighted population values
    are 15.481 / 25.370 and never changed). Decoupling makes rows 3-4
    structurally independent of any `unopened` edit, which is what the BANDS
    comment claims they are. This is a MEASUREMENT repair: no band number in
    rows 3-4 moved, and all six personas pass them at the pinned seed.

    Residual coupling (R10-PRE2 refuter): "independent" is only true of the
    ACTION draws — the deal itself comes from `rng_u`, which `unopened`
    sampling consumes, so a widened `unopened` still displaces the dealt
    hands feeding rows 3-4. Measured for the R10-PRE2 maniac widening:
    3-bet 12.81 -> 12.67, vs_rfi-continue 46.51 -> 46.94 (both stay in
    (12, 20) / (44, 48); the maniac block's earlier 45.99 figure below is a
    pre-PRE2 reading).

    Known residual (pre-existing, NOT introduced here): rows 3-4 are still Monte
    Carlo estimates of exactly-computable quantities, and tag's snug (6, 7)
    3-bet and (15, 28) continue rows sit within ~1 sd of an edge — across a
    25-seed sweep they span 6.19-7.31 and 14.88-16.31. They pass at the pinned
    seed; a future slice that needs them robust should compute them exactly.
    """
    rng_u = random.Random(20260710)
    rng_v = random.Random(20260710)
    positions = positions_for_button(0)
    n = DEALS * 9
    opened = first_in_raised = threebet = continued = 0
    for _ in range(DEALS):
        dealt = deal_hand(rng_u)
        for seat, pos in enumerate(positions):
            hole = dealt.hole_cards[seat]
            a = sample_preflop_action(pack, pos, "unopened", hole, rng_u)
            opened += a.name != "fold"
            first_in_raised += a.name == "raise"
            b = sample_preflop_action(pack, pos, "vs_rfi", hole, rng_v)
            threebet += b.name == "3bet"
            continued += b.name != "fold"
    return tuple(100.0 * c / n for c in (opened, first_in_raised, threebet, continued))


# ------------------------------------------------ R10-PRE1 — premium no-fold
# The 756-hand R10 review's most basic correctness defect (R10-1b): the
# maniac's unopened mixes carried explicit fold 0.15-0.30 on classes that
# INCLUDE the premiums, so it folded AK/JJ first-in (minimal repros h318/h713).
# No archetype folds AA unopened; this is not an identity dial, it is a bug.
# Fixed by a premium carve-out mix ("TT+, AQs+, AKo" -> raise 1.0) prepended
# to every unopened node — first-match-wins peels exactly these classes off
# the wide mixes and changes nothing else.

# The exact premium set the roadmap enumerates: TT+, AK, AQs.
_PREMIUM_CLASSES = ("TT", "JJ", "QQ", "KK", "AA", "AQs", "AKs", "AKo")


def _premium_unopened_fold_weight(pack: PersonaPack) -> dict[tuple[str, str], float]:
    """Authored fold weight (explicit + implicit remainder) for each premium
    class at EVERY seat, resolved with the SAME semantics as
    `sample_preflop_action`: first matching node in list order (explicit
    positions or wildcard), first matching mix within it, and fold 1.0 when
    no node or mix covers the class. Iterating seats — not authored nodes —
    means a deleted seat node reads as fold 1.0 instead of silently vanishing
    from the gate (review C-1)."""
    from app.domain.personas import _combos

    out: dict[tuple[str, str], float] = {}
    for pos in Position:
        node = next(
            (
                n
                for n in pack.preflop
                if n.facing == "unopened"
                and (n.positions is None or pos in n.positions)
            ),
            None,
        )
        for cls in _PREMIUM_CLASSES:
            fold = 1.0  # the sampler's no-node / no-mix rule
            if node is not None:
                for mix in node.mixes:
                    if cls in _combos(mix.combos):
                        fold = mix.weights.get("fold", 0.0) + max(
                            0.0, 1.0 - sum(mix.weights.values())
                        )
                        break
            out[(pos.value, cls)] = fold
    return out


def test_maniac_premium_unopened_never_folds():
    """🔴 R10-PRE1 defect gate (failed at pre-fix HEAD: fold 0.15-0.30 at
    every seat). Deterministic authored-shape assertion — no sampling."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    folds = _premium_unopened_fold_weight(packs[VillainType.MANIAC])
    assert folds, "maniac has no unopened nodes?"
    bad = {k: v for k, v in folds.items() if v > 0.0}
    assert not bad, f"maniac folds premiums unopened: {bad}"


def test_lag_premium_unopened_never_folds_preservation():
    """PRESERVATION, not a defect gate (R9-3 rule: label what already passed).
    LAG's premium unopened fold weight was already 0 at HEAD — pinned so the
    maniac fix can never be 'balanced' by loosening the LAG."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    folds = _premium_unopened_fold_weight(packs[VillainType.LAG])
    assert folds and not {k: v for k, v in folds.items() if v > 0.0}


# ------------------------------------------- R10-PRE2 — maniac ladder separation
# R10-1a: the maniac's authored first-in ladder sat BELOW the LAG's at every
# seat (and below TAG at UTG/BTN/SB) — measured EP first-in 18.3%, tightest of
# the four. The roster's DEFINITIONAL archetype ordering (theory contract 1:
# idealized-distinct caricatures, same basis as the pinned cross-persona
# bluff_freq ordering) puts the maniac's raise-first-in above the LAG's at
# every seat tier. Only maniac-vs-lag is gated here: the nit>tag inversion at
# UTG1/UTG2/LJ belongs to W5-b3 (nit-scoped), and the full nit<tag<lag<maniac
# chain becomes assertable only after that slice lands.
#
# This is an AUTHORED-shape gate (deterministic, no sampling): the exact
# combo-weighted first-in raise probability of the resolved `unopened` node
# per seat, resolved with sampler semantics. Sampled first-in rates are the
# R10-COUNT instrument's job and stay REPORTED-not-gated until R9-SEATPROV.

_CLASS_COMBOS = {
    cls: (6 if len(cls) == 2 else 4 if cls[2] == "s" else 12)
    for cls in (
        r1 + r2 + s
        for i, r1 in enumerate("23456789TJQKA")
        for j, r2 in enumerate("23456789TJQKA")
        if i > j
        for s in ("s", "o")
    )
} | {r + r: 6 for r in "23456789TJQKA"}


def _authored_first_in_raise(pack: PersonaPack) -> dict[str, float]:
    """Exact combo-weighted P(raise | first-in) per seat from the authored
    pack, resolved with the SAME semantics as `sample_preflop_action`: first
    matching `unopened` node in list order, first mix containing the class,
    no-node/no-mix => fold (contributes 0 raise). Deterministic — this is the
    quantity the R10-PRE2 ladder gate compares across personas."""
    from app.domain.personas import _combos

    out: dict[str, float] = {}
    for pos in Position:
        node = next(
            (
                n
                for n in pack.preflop
                if n.facing == "unopened"
                and (n.positions is None or pos in n.positions)
            ),
            None,
        )
        raised = 0.0
        for cls, ncombos in _CLASS_COMBOS.items():
            if node is None:
                break
            for mix in node.mixes:
                if cls in _combos(mix.combos):
                    raised += ncombos * mix.weights.get("raise", 0.0)
                    break
        out[pos.value] = raised / 1326.0
    return out


def test_maniac_first_in_ladder_above_lag():
    """🔴 R10-PRE2 defect gate (failed at pre-fix HEAD: maniac below LAG at
    all 9 seats, e.g. UTG 16.5% vs 25.1%). Authored per-seat RFI must be
    strictly above the LAG's at every seat.

    ARRIVAL context (theory review, R10-PRE2): this is an AUTHORED-shape
    gate with equal seat weight; realized first-in identity is EP-dominated —
    measured unopened-node occupancy over 400 organic hands: UTG 84.6%,
    UTG1 52.9%, UTG2 38.3%, LJ 25.0%, HJ 14.1%, CO 7.1%, BTN 3.3%, SB 1.2%,
    BB 0.0%. The BB `unopened` node is STRUCTURALLY UNREACHABLE in organic
    play (a fold-around ends the hand before BB acts; an SB limp routes BB
    to `vs_limpers`) — it is authored for pack-shape symmetry and gated here
    only as an authored-shape pin. Level seeds cited for this slice (UTG
    ≈32-45 → CO/BTN ≈52-82) are 9-max dossier rubric numbers whose source
    format is unstated — DIRECTIONAL fit seeds only, never gated (§5a)."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    maniac = _authored_first_in_raise(packs[VillainType.MANIAC])
    lag = _authored_first_in_raise(packs[VillainType.LAG])
    bad = {
        pos: (round(maniac[pos], 4), round(lag[pos], 4))
        for pos in maniac
        if maniac[pos] <= lag[pos]
    }
    assert not bad, f"maniac authored RFI not above LAG (maniac, lag): {bad}"


def test_maniac_first_in_ladder_monotone_to_button():
    """🔴 R10-PRE2 defect gate #2 (review finding, failed at pre-fix HEAD:
    authored CO 49.7% > BTN 48.3% — the button authored TIGHTER than the
    cutoff for the loosest persona in the roster). The non-blind ladder must
    be non-decreasing UTG -> BTN; blinds are excluded (SB/BB are structurally
    different first-in spots and sit off the positional ladder).

    Declared reliance (§5a): monotonicity claims sit in the contract's
    [UNVERIFIED] blanket ordering/monotonicity licence. The claim here is
    STRUCTURAL — each later seat has strictly fewer players left to act, so
    a wider open is dominance-consistent — not a transferred source level."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    rfi = _authored_first_in_raise(packs[VillainType.MANIAC])
    ladder = ["UTG", "UTG1", "UTG2", "LJ", "HJ", "CO", "BTN"]
    bad = [
        f"{a} {rfi[a]:.4f} > {b} {rfi[b]:.4f}"
        for a, b in zip(ladder, ladder[1:], strict=False)
        if rfi[a] > rfi[b]
    ]
    assert not bad, f"maniac authored RFI ladder not monotone to the button: {bad}"


# ------------------------------------------------ N-LAGLADDER — lag ladder tighten
# Theory-HIGH finding T-H1 (wave-2 ledger, filed off N-3BSTRATA): the lag's
# authored first-in ladder was uniformly too wide for its 21-27 VPIP identity,
# and the surplus sat in DOMINATED OFFSUIT hands in early seats — at UTG the
# pack raised 12.49% of all combos offsuit against only 7.90% suited, i.e. it
# opened MORE offsuit than the TAG from every early seat. That surplus is what
# later arrives at `vs_3bet` as call mass the persona cannot defend.
#
# The repair re-emits all nine `unopened` nodes from the RR-EMIT curve spec
# `content/personas/ladders/lag.unopened.json` (proving gate: test_rr_emit.py).
# Gates below are AUTHORED-shape and deterministic — no sampling, so no CI.
# Population VPIP/PFR stays REPORTED-not-gated (the single band anchor is W4-b).

_LAG_LADDER_SEATS = ("UTG", "UTG1", "UTG2", "LJ", "HJ", "CO", "BTN")

# Per-seat authored-RFI CEILINGS. Each is the post-fix width rounded up with
# ~1pp of headroom, and EVERY ONE of them is breached by the pre-fix pack —
# the non-vacuity proof (R9-3 rule). Pre-fix / post-fix authored RFI %:
#   UTG 25.10/22.11 · UTG1 27.48/24.80 · UTG2 33.73/29.17 · LJ 37.62/33.09
#   HJ 47.69/40.63 · CO 53.24/51.61 · BTN 66.09/62.90 · SB 51.98/49.44
#   BB 45.40/39.25   (seat-average 43.15 -> 39.22)
_LAG_RFI_CEILING = {
    "UTG": 23.1, "UTG1": 25.8, "UTG2": 30.2, "LJ": 34.1, "HJ": 41.6,
    "CO": 52.6, "BTN": 63.9, "SB": 50.4, "BB": 40.2,
}

# Early-seat OFFSUIT-ONLY ceilings — the named mechanism of the finding.
# Pre-fix: UTG 12.49, UTG1 13.39, UTG2 17.38 (all breach); post-fix 7.78 /
# 8.69 / 10.50. Suited width went UP over the same seats (7.90 -> 10.08,
# 9.11 -> 11.40, 10.92 -> 13.51): this is a SUBSTITUTION, not a blanket trim,
# so the suited FLOOR is asserted alongside the offsuit ceiling — a future
# edit cannot satisfy the ceiling by simply deleting the range.
_LAG_EP_OFFSUIT_CEILING = {"UTG": 11.0, "UTG1": 11.5, "UTG2": 13.0}
_LAG_EP_SUITED_FLOOR = {"UTG": 9.0, "UTG1": 10.0, "UTG2": 12.0}


def _authored_first_in_by_kind(pack: PersonaPack) -> dict[str, dict[str, float]]:
    """Per seat, the combo-weighted authored first-in raise % split into
    pair / suited / offsuit. Same sampler semantics as
    `_authored_first_in_raise` (first matching node, first matching mix)."""
    from app.domain.personas import _combos

    out: dict[str, dict[str, float]] = {}
    for pos in Position:
        node = next(
            (
                n
                for n in pack.preflop
                if n.facing == "unopened"
                and (n.positions is None or pos in n.positions)
            ),
            None,
        )
        acc = {"pair": 0.0, "suited": 0.0, "offsuit": 0.0}
        for cls, ncombos in _CLASS_COMBOS.items():
            if node is None:
                break
            for mix in node.mixes:
                if cls in _combos(mix.combos):
                    kind = (
                        "pair" if len(cls) == 2
                        else "suited" if cls[2] == "s"
                        else "offsuit"
                    )
                    acc[kind] += ncombos * mix.weights.get("raise", 0.0)
                    break
        out[pos.value] = {k: 100.0 * v / 1326.0 for k, v in acc.items()}
    return out


def test_lagladder_authored_rfi_under_seat_ceilings():
    """🔴 N-LAGLADDER defect gate (failed at pre-fix HEAD at ALL NINE seats,
    e.g. UTG 25.10 > 23.1, HJ 47.69 > 41.6)."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    rfi = _authored_first_in_raise(packs[VillainType.LAG])
    bad = {
        pos: round(100.0 * rfi[pos], 2)
        for pos, cap in _LAG_RFI_CEILING.items()
        if 100.0 * rfi[pos] > cap
    }
    assert not bad, f"lag authored RFI above its N-LAGLADDER ceiling: {bad}"


def test_lagladder_early_seat_offsuit_opens_trimmed():
    """🔴 N-LAGLADDER defect gate #2 — the finding's named mechanism (failed at
    pre-fix HEAD at all three early seats: offsuit 12.49 / 13.39 / 17.38)."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    kinds = _authored_first_in_by_kind(packs[VillainType.LAG])
    over = {
        pos: round(kinds[pos]["offsuit"], 2)
        for pos, cap in _LAG_EP_OFFSUIT_CEILING.items()
        if kinds[pos]["offsuit"] > cap
    }
    assert not over, f"lag early-seat offsuit open width above ceiling: {over}"
    under = {
        pos: round(kinds[pos]["suited"], 2)
        for pos, floor in _LAG_EP_SUITED_FLOOR.items()
        if kinds[pos]["suited"] < floor
    }
    assert not under, f"lag early-seat suited open width below floor: {under}"


def test_lag_first_in_ladder_above_tag_preservation():
    """PRESERVATION (R9-3 rule: label what already passed). The roster's
    definitional ordering tag < lag held at HEAD and must survive the tighten;
    the lag < maniac leg is gated by `test_maniac_first_in_ladder_above_lag`,
    which the tighten can only make safer."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    lag = _authored_first_in_raise(packs[VillainType.LAG])
    tag = _authored_first_in_raise(packs[VillainType.TAG])
    bad = {
        pos: (round(lag[pos], 4), round(tag[pos], 4))
        for pos in lag
        if lag[pos] <= tag[pos]
    }
    assert not bad, f"lag authored RFI not above TAG (lag, tag): {bad}"


def test_lag_first_in_ladder_monotone_and_sb_under_btn_preservation():
    """PRESERVATION: the non-blind ladder is non-decreasing UTG -> BTN and the
    SB opens tighter than the BTN. Both held at HEAD (same structural argument
    as `test_maniac_first_in_ladder_monotone_to_button`: each later seat has
    strictly fewer players left to act)."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    rfi = _authored_first_in_raise(packs[VillainType.LAG])
    bad = [
        f"{a} {rfi[a]:.4f} > {b} {rfi[b]:.4f}"
        for a, b in zip(_LAG_LADDER_SEATS, _LAG_LADDER_SEATS[1:], strict=False)
        if rfi[a] > rfi[b]
    ]
    assert not bad, f"lag authored RFI ladder not monotone to the button: {bad}"
    assert rfi["SB"] < rfi["BTN"], (
        f"lag SB {rfi['SB']:.4f} opens at least as wide as BTN {rfi['BTN']:.4f}"
    )


def test_lag_vs_rfi_aqo_does_not_fold_to_a_single_raise():
    """🔴 RR-HOLES T-F3 flagged-row gate (failed at pre-fix HEAD: AQo sat in the
    {3bet 0.6, fold 0.4} mix, i.e. a lag folded AQo to ONE raise 40% of the
    time). The fold mass moved to CALL, not to 3-bet, so the pack's authored
    3-bet width is unchanged by construction — this is a fold->call transfer
    on a single class, not a 3-bet-frequency edit."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    from app.domain.personas import _combos

    node = next(
        n for n in packs[VillainType.LAG].preflop
        if n.facing == "vs_rfi" and n.positions is None
    )
    mix = next(m for m in node.mixes if "AQo" in _combos(m.combos))
    fold = mix.weights.get("fold", 0.0) + max(0.0, 1.0 - sum(mix.weights.values()))
    assert fold == 0.0, (
        f"lag folds AQo to a single raise: {mix.combos!r} -> {dict(mix.weights)}"
    )


def test_all_six_persona_packs_load():
    packs = load_persona_packs()
    missing = set(VillainType) - set(packs)
    if missing:
        pytest.skip(f"personas not authored yet (T2/T3 land at fan-in): {sorted(missing)}")
    assert set(packs) == set(VillainType)
    for vt, pack in packs.items():
        assert pack.persona == vt
        assert pack.preflop


@pytest.mark.parametrize("persona", sorted(BANDS))
def test_persona_stat_bands(persona):
    packs = load_persona_packs()
    vt = VillainType(persona)
    if vt not in packs:
        pytest.skip(f"content/personas/{persona}.json not authored yet — lands at fan-in")
    stats = _stats(packs[vt])
    labels = ("open-freq", "first-in-raise", "3-bet", "vs_rfi-continue")
    for label, value, (lo, hi) in zip(labels, stats, BANDS[persona], strict=True):
        assert lo <= value <= hi, f"{persona} {label} {value:.2f}% outside [{lo}, {hi}]"
