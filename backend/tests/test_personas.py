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
from app.domain.content.notation import parse_range
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
    # tag rows 1-2 RE-ANCHORED by N-TAGWIDTH (2026-07-31): the width trim at
    # UTG / HJ / CO / BTN / SB (see that section below) takes the exact
    # combo-weighted seat-average from 33.8529 to 27.8867 open == first-in-raise
    # (every tag `unopened` mix is raise/fold-only, so the two rows coincide).
    # Bands = the exact value ±2.0pp per the tolerance note above; the pinned
    # seed reads 27.77 / 27.77, ~1.9pp inside both edges. Rows 3-4 are
    # UNTOUCHED — the `vs_rfi` node did not move and the two rngs are decoupled.
    "tag": ((25.8867, 29.8867), (25.8867, 29.8867), (6, 8), (15, 28)),
    # lag/maniac open-freq re-anchored (P1 M3, persona-realism-p1): M3 deleted
    # the non-SB unopened open-limps from both packs, so open-freq collapsed
    # onto first-in-raise (+~0-1pp of retained SB limps). Measured at the
    # pinned seed: lag 23.55 (raise 23.29), maniac 35.64 (raise 34.62). The
    # old floors (24 / 45) counted open-limps that no longer exist — intended
    # M3 behavior, not a range regression (first-in-raise, 3-bet and
    # vs_rfi-continue all stayed inside their existing bands).
    # W5-b1 supersedes rows 1-2 of that anchor with the authored width 43.15.
    # N-LAGLADDER (2026-07-31) re-emitted all nine `unopened` nodes from
    # content/personas/ladders/lag.unopened.json but did NOT re-anchor any lag
    # row. Rows 1-2: the reshape is a suited-for-offsuit SUBSTITUTION and the
    # combo-weighted total barely moved (43.15 -> 43.04 seat-average; pinned
    # seed 42.63), so the existing (41, 45) still is "exact ±2.0pp" — an edit
    # here would have been cosmetic. Rows 3-4: the vs_rfi AQo carve-out holds
    # 3-bet width constant by construction; pinned seed reads 9.74 / 26.75.
    "lag": ((41, 45), (41, 45), (8, 12), (25, 42)),
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
    Carlo estimates of exactly-computable quantities, and tag's snug (6, 8)
    3-bet and (15, 28) continue rows sit within ~1 sd of an edge — across a
    25-seed sweep they span 6.19-7.31 and 14.88-16.31. They pass at the pinned
    seed; a future slice that needs them robust should compute them exactly.
    ⚠️ Those two sweep spans are HISTORICAL, not current evidence: they were
    measured before RR-HOLES, R10-3BET, N-TAGCOMP and N-TAGWIDTH, each of which
    displaced the shared `rng_u` deal stream. The tag continue row reads 16.88
    at the pinned seed (17.12 before N-TAGWIDTH narrowed five `unopened` nodes),
    still ABOVE the whole span quoted above and inside its (15, 28) row — the
    move is deal-stream displacement, not a `vs_rfi` edit. Re-sweep before
    citing the spans.
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
# authored first-in ladder carried its width in DOMINATED OFFSUIT hands, worst
# in early seats — at UTG the pack raised 12.49% of all combos offsuit against
# only 7.90% suited, i.e. HALF the opening range was offsuit and the lag opened
# MORE offsuit than the TAG from every early seat. That surplus is what later
# arrives at `vs_3bet` as call mass the persona cannot defend.
#
# The repair re-emits all nine `unopened` nodes from the RR-EMIT curve spec
# `content/personas/ladders/lag.unopened.json` (proving gate: test_rr_emit.py).
#
# ⚠️ WHAT THIS SLICE DOES *NOT* DO, and why (review fold, fix 1). The first cut
# also TIGHTENED the ladder (seat-average 43.15 -> 39.22). That drove measured
# population PFR to 15.77, under the §5 LAG floor of 17. A 10-seed sweep of
# metric #3 at n=2000 then established that the PRE-SLICE pack itself measures
# PFR 17.32 ± 0.34 — sitting ON the floor with no headroom to spend — so ANY
# real width reduction breaches §5. The width was therefore restored to within
# 0.36pp of pre-slice at every seat, and the deliverable is the COMPOSITION.
# There is consequently NO per-seat authored-RFI ceiling gate: it would be
# vacuous (the pre-slice pack would pass it). The gates below are the offsuit
# ceiling and the suited floor, which is what actually changed.
# §5 provenance for "21-27 VPIP / 17-23 PFR" lives ONCE in the spec's `_doc`;
# it is deliberately not restated here and nothing below gates on it.
#
# Gates are AUTHORED-shape and deterministic — no sampling, so no CI.
# Population VPIP/PFR stays REPORTED-not-gated (the single band anchor is W4-b).

_LAG_LADDER_SEATS = ("UTG", "UTG1", "UTG2", "LJ", "HJ", "CO", "BTN")

# OFFSUIT-ONLY ceilings — the named mechanism of the finding. Gated at the six
# seats where the move is decisive (≥3.8pp below pre-slice); CO/BTN moved only
# -0.90/-0.36 and are covered by the ≥TAG preservation gate instead of a
# ceiling too thin to be meaningful. SB (-0.90) is gated by NEITHER mechanism
# (not in this dict, not in _LAG_OFFSUIT_GE_TAG_SEATS) — ungated by scope,
# delta-review L2.
#   pre-slice -> post   UTG 12.49->8.69 · UTG1 13.39->8.69 · UTG2 17.38->12.31
#                       LJ 19.55->15.38 · HJ 26.61->22.62 · BB 24.80->20.81
# Suited width rose at the SAME seats (UTG 7.90->10.50, UTG1 9.11->12.79,
# UTG2 10.92->15.51, LJ 12.19->16.35, HJ 15.20->19.13, BB 14.72->18.34): this
# is a SUBSTITUTION, so the suited FLOOR is asserted alongside the offsuit
# ceiling — a future edit cannot satisfy the ceiling by deleting the range.
#
# N-LAGCOMP2 (2026-07-31, lag.json 1.4.0) EXTENDS BOTH DICTS TO CO/BTN/SB — the
# three seats N-LAGLADDER left alone and the paragraph above explicitly declared
# ungated. What made them gateable is that they became decisive: N-LAGLADDER's
# "too thin to be meaningful" was a statement about a -0.90/-0.36 move, and this
# slice moves them -3.62/-3.62/-2.72. The defect it repairs is the one N-TAGCOMP
# exposed by fixing the tag: from CO/BTN/SB the lag opened a WIDER TOTAL range
# than the tag while covering LESS of the suited universe (17.01 vs 19.00,
# 19.91 vs 22.47, 17.01 vs 18.10) — the surplus was offsuit junk.
#   pre-slice -> post   suited  CO 17.01->20.63 · BTN 19.91->23.53 · SB 17.01->19.73
#                       offsuit CO 30.23->26.61 · BTN 40.18->36.56 · SB 28.96->26.24
# Every one of those six pre-slice values is red against the constants below,
# measured at commit e5e08b6 (`git show e5e08b6:content/personas/lag.json`).
# The TOTAL is unchanged to the last combo at all three seats (CO 704.4, BTN
# 874.8, SB 687.6 of 1326) and that neutrality is already pinned elsewhere, by
# the `raise_pct` annotations in the curve spec — 53.12 / 65.97 / 51.86, byte-
# identical across this slice and asserted by
# test_rr_emit.py::test_lag_authored_raise_pct_annotations_match_emitted_widths.
# So the ceiling here cannot be met by deleting range, twice over.
_LAG_OFFSUIT_CEILING = {
    "UTG": 10.5, "UTG1": 10.5, "UTG2": 14.5, "LJ": 17.0, "HJ": 24.5, "BB": 22.5,
    "CO": 27.5, "BTN": 37.5, "SB": 27.0,
}
_LAG_SUITED_FLOOR = {
    "UTG": 9.5, "UTG1": 11.5, "UTG2": 14.0, "LJ": 15.0, "HJ": 17.5, "BB": 17.0,
    "CO": 20.0, "BTN": 23.0, "SB": 19.0,
}

# Fix 2 (theory MED): the first cut pushed lag offsuit width to at-or-below the
# TAG's at 6 of 9 seats, so the "loose" persona read offsuit-TIGHTER than the
# tag. Restored, and pinned here per seat (not as a total-width claim).
# ⚠️ The caveat this comment used to carry — "the tag's own suited/offsuit
# composition is itself suspect (36.20% offsuit vs 16.44% suited from the BTN),
# so this gate compares against a suspect baseline" — was the N-TAGCOMP filing,
# and N-TAGCOMP has since landed (section below). The tag's BTN offsuit width
# is now 29.86% against 22.47% suited, so the comparison baseline is no longer
# the shape this gate was apologising for, and every seat's slack GREW. The
# gate itself is unchanged: values, seats and logic are exactly as N-LAGLADDER
# shipped them.
# SB ADDED by N-LAGCOMP2's review (2026-07-31). The relation holds at all NINE
# seats in the shipped pack — but the GATE covers only the tuple below, so what
# is defended is these FIVE seats, not the pack-wide property. SB joins because
# N-LAGCOMP2 is the first slice to move SB offsuit materially (28.96 -> 26.24,
# against tag 22.62): the seat that was "gated by NEITHER mechanism" in the
# note above is now gated by both.
_LAG_OFFSUIT_GE_TAG_SEATS = ("LJ", "HJ", "CO", "BTN", "SB")


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


def _authored_first_in_suited_weights(pack: PersonaPack) -> dict[str, dict[str, float]]:
    """Per seat, `suited class -> authored first-in raise weight`, zero-weight
    classes dropped. Same sampler semantics as `_authored_first_in_by_kind`
    (first matching node, first matching mix) — this is the class-resolved form
    of that function's `suited` bucket, so the two can never disagree."""
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
        weights: dict[str, float] = {}
        for cls in _CLASS_COMBOS:
            if node is None:
                break
            if len(cls) == 2 or cls[2] != "s":
                continue
            for mix in node.mixes:
                if cls in _combos(mix.combos):
                    w = mix.weights.get("raise", 0.0)
                    if w > 0.0:
                        weights[cls] = w
                    break
        out[pos.value] = weights
    return out


def test_lagladder_dominated_offsuit_opens_replaced_by_suited():
    """🔴 N-LAGLADDER defect gate — the finding's named mechanism. Failed at
    pre-fix HEAD on BOTH legs at all six gated seats (offsuit 12.49 / 13.39 /
    17.38 / 19.55 / 26.61 / 24.80 all above ceiling; suited 7.90 / 9.11 /
    10.92 / 12.19 / 15.20 / 14.72 all below floor).

    🔴 N-LAGCOMP2 re-arms the same two legs at CO/BTN/SB, and both were red at
    that slice's base commit too: offsuit 30.23 / 40.18 / 28.96 above the 27.5 /
    37.5 / 27.0 ceilings, suited 17.01 / 19.91 / 17.01 below the 20.0 / 23.0 /
    19.0 floors. (Measured read-only off
    `git show e5e08b6:content/personas/lag.json`.)

    Both legs are asserted together on purpose: the ceiling alone could be
    satisfied by deleting range (which the §5 PFR floor forbids — see the
    section note above), and the floor alone could be satisfied by widening."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    kinds = _authored_first_in_by_kind(packs[VillainType.LAG])
    over = {
        pos: round(kinds[pos]["offsuit"], 2)
        for pos, cap in _LAG_OFFSUIT_CEILING.items()
        if kinds[pos]["offsuit"] > cap
    }
    assert not over, f"lag offsuit open width above ceiling: {over}"
    under = {
        pos: round(kinds[pos]["suited"], 2)
        for pos, floor in _LAG_SUITED_FLOOR.items()
        if kinds[pos]["suited"] < floor
    }
    assert not under, f"lag suited open width below floor: {under}"


def test_lag_offsuit_width_at_least_tag_preservation():
    """PRESERVATION (held at pre-slice HEAD; BROKEN by this slice's first cut
    and restored by the retune — review fix 2). Per seat, not as a total-width
    claim: the loose persona must not open a NARROWER offsuit range than the
    TAG at the seats where offsuit steals are the archetype's business.

    ⚠️ SCOPE — this defends the FIVE seats in `_LAG_OFFSUIT_GE_TAG_SEATS`, not
    the pack. The relation happens to hold at all nine, but four seats are
    ungated and a regression there would pass here. (N-LAGCOMP2's review added
    SB, taking the tuple from four seats to five; green post-slice at 26.24 vs
    tag 22.62.)

    See `_LAG_OFFSUIT_GE_TAG_SEATS` for the standing caveat that the tag's own
    offsuit-heavy composition is itself suspect and filed forward."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    lag = _authored_first_in_by_kind(packs[VillainType.LAG])
    tag = _authored_first_in_by_kind(packs[VillainType.TAG])
    bad = {
        pos: (round(lag[pos]["offsuit"], 2), round(tag[pos]["offsuit"], 2))
        for pos in _LAG_OFFSUIT_GE_TAG_SEATS
        if lag[pos]["offsuit"] < tag[pos]["offsuit"]
    }
    assert not bad, f"lag opens tighter offsuit than TAG (lag, tag): {bad}"


# N-LAGCOMP2 — the superset claim, read from BOTH packs at test time.
_LAGCOMP2_SEATS = ("CO", "BTN", "SB")


def test_lagcomp2_late_seat_suited_covers_the_tag():
    """🔴 N-LAGCOMP2 defect gate. Failed at pre-fix HEAD at all three seats:
    lag suited 17.01 / 19.91 / 17.01 against tag 19.00 / 22.47 / 18.10 — the
    LOOSER persona covering LESS of the suited universe than the tighter one
    from the seats where suited hands are worth the most, while opening a wider
    TOTAL range (53.12 vs 48.42, 65.97 vs 58.22, 51.86 vs 46.61). A wider range
    that is a subset in suited is the shape defect T-M2 and N-TAGCOMP already
    condemned; here the lag's surplus was sitting in offsuit junk.

    ⚠️ THE TAG SIDE IS COMPUTED, NEVER HARD-CODED, and that is the point. The
    sibling lane N-TAGWIDTH is trimming the tag's late-seat width, which will
    LOWER these tag figures; a pinned number would either go stale or, worse,
    turn a legitimate tag trim into a red test in the lag's file. Reading both
    packs makes the gate the RELATION, which is what the finding is about.

    TWO LEGS, and the second is the one with teeth (review fold, Codex MED —
    convergent). Aggregate suited weight alone is satisfiable while DROPPING a
    class the tag opens, as long as some other suited class is deepened to pay
    for it; that mutation is exactly the "wider but shaped wrong" failure this
    slice exists to stop. So the class-by-class leg is asserted too: every
    suited class the tag opens, the lag opens, at >= the tag's weight. Both
    legs read both packs at test time. Post-slice: 66 / 78 / 63 tag suited
    classes at CO / BTN / SB, zero missing, zero lighter.
    At e5e08b6 (pre-slice HEAD) BOTH legs were red — aggregate as quoted above,
    and the superset leg short of 12 / 14 / 9 tag-covered classes at CO / BTN /
    SB: 6 / 9 / 3 the lag did not open AT ALL (CO 53s 84s 94s J2s T3s T4s; BTN
    the whole 32s 42s 52s 62s 72s 82s 83s 92s 93s bottom; SB 43s 84s 94s) and
    6 / 5 / 6 more it opened at the 0.4 edge weight against tag weights of
    1.0 (14 of the 17) or 0.5 (the other 3)
    (measured off `git show e5e08b6:content/personas/{lag,tag}.json`).

    The set leg's one failure mode is a tag edit that ADDS a suited class the
    lag does not open — a tag decision, not a lag defect. That is accepted: it
    is a loud, correct signal that the two packs disagree about shape, and the
    aggregate leg beside it degrades gracefully under the trim N-TAGWIDTH is
    actually doing (a trim can only make both legs easier).

    This gate does NOT forbid the lag being offsuit-wider than the tag; that is
    the archetype (see `test_lag_offsuit_width_at_least_tag_preservation`, which
    stays green — post-slice offsuit 26.61 / 36.56 / 26.24 vs tag 23.53 / 29.86
    / 22.62). The two gates together say: strictly wider on BOTH axes."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    lag = _authored_first_in_by_kind(packs[VillainType.LAG])
    tag = _authored_first_in_by_kind(packs[VillainType.TAG])
    bad = {
        pos: (round(lag[pos]["suited"], 2), round(tag[pos]["suited"], 2))
        for pos in _LAGCOMP2_SEATS
        if lag[pos]["suited"] < tag[pos]["suited"]
    }
    assert not bad, f"lag opens a NARROWER suited range than TAG (lag, tag): {bad}"

    lag_cls = _authored_first_in_suited_weights(packs[VillainType.LAG])
    tag_cls = _authored_first_in_suited_weights(packs[VillainType.TAG])
    short = {
        pos: sorted(
            (cls, round(lag_cls[pos].get(cls, 0.0), 2), round(w, 2))
            for cls, w in tag_cls[pos].items()
            if lag_cls[pos].get(cls, 0.0) < w
        )
        for pos in _LAGCOMP2_SEATS
    }
    short = {pos: v for pos, v in short.items() if v}
    assert not short, (
        f"lag suited range is not a superset of TAG's (class, lag w, tag w): {short}"
    )


def test_lag_first_in_ladder_above_tag_preservation():
    """PRESERVATION (R9-3 rule: label what already passed). The roster's
    definitional ordering tag < lag held at HEAD and must survive the reshape;
    the lag < maniac leg is gated by `test_maniac_first_in_ladder_above_lag`."""
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


# ------------------------------------------------- N-TAGCOMP — tag composition
# Theory finding T-M2 (wave-3 ledger), filed as roadmap `N-TAGCOMP`: the tag's
# opening composition was INVERTED against the shape the archetype is named
# for. A TAG plays nearly all of its suited hands and is severely selective
# offsuit; the shipped ladder did the opposite — at BTN it opened 69.9% of the
# suited universe against 51.3% of the three-times-larger offsuit universe
# (36.20% of ALL combos offsuit vs 16.44% suited). The surplus was dominated
# offsuit kicker junk (K3o, Q4o, J6o from the button).
#
# The repair re-emits all nine `unopened` nodes from the RR-EMIT curve spec
# `content/personas/ladders/tag.unopened.json` (proving gate: test_rr_emit.py).
#
# ⚠️ WHAT THIS SLICE DOES *NOT* DO, and why — the N-LAGLADDER lesson, inherited
# on purpose. It does not move total width in either direction. A 10-seed
# metric-#3 sweep at n=2000 reads the pre-slice pack at PFR 12.80 ± 0.46
# against the §5 TAG floor of 12 (provenance triple lives ONCE in the spec's
# `_doc`, deliberately not restated here, and nothing below gates on it), i.e.
# ~1.7 sd of headroom — the same "no width to spend" position that made
# N-LAGLADDER's first cut breach §5 for the lag. So the deliverable is the
# COMPOSITION, and the total may not be spent UPWARD: see
# `test_tagcomp_total_width_never_rises`, which passes at pre-slice HEAD as
# well as after, and is the belt that stops the ceiling below from being
# satisfied by widening the suited rows instead of substituting into them.
# That gate is ONE-SIDED by design — a later dossier-ward width trim
# (`N-TAGWIDTH`) must not have to delete a green test to proceed.
#
# Pairs are untouched at every seat (per-class treatment pinned by
# `test_tagcomp_pair_band_unchanged_preservation`), so `pair` is absent from
# both dicts below by construction, not by omission.
#
# Gates are AUTHORED-shape and deterministic — no sampling, so no CI.
# Population VPIP/PFR stays REPORTED-not-gated (the single band anchor is W4-b).

# Pre-slice HEAD, combo-weighted authored first-in raise %:
#   offsuit  UTG 7.24 · UTG1 8.14 · UTG2 9.95 · LJ 14.03 · HJ 19.46 ·
#            CO 29.41 · BTN 36.20 · SB 27.15 · BB 15.84
#   suited   UTG 5.43 · UTG1 5.58 · UTG2 6.49 · LJ 8.45 · HJ 11.01 ·
#            CO 13.42 · BTN 16.44 · SB 13.57 · BB 9.50
# Shipped:
#   offsuit  UTG 4.52 · UTG1 4.98 · UTG2 7.24 · LJ 9.95 · HJ 14.03 ·
#            CO 23.53 · BTN 29.86 · SB 22.62 · BB 10.86
#   suited   UTG 7.99 · UTG1 8.75 · UTG2 9.20 · LJ 12.52 · HJ 15.99 ·
#            CO 19.00 · BTN 22.47 · SB 18.10 · BB 14.18
# Every seat is gated on BOTH legs (the lag slice could only gate six because
# its CO/BTN moves were too thin to be meaningful; this one moves all nine by
# ≥2.7pp offsuit and ≥2.5pp suited). Each threshold sits ≥0.7pp inside the
# shipped value and clearly on the far side of the pre-slice value.
_TAG_OFFSUIT_CEILING = {
    "UTG": 5.5, "UTG1": 6.0, "UTG2": 8.3, "LJ": 11.0, "HJ": 15.5,
    "CO": 25.0, "BTN": 31.5, "SB": 24.0, "BB": 12.0,
}
# The suited universe is 312 of 1326 combos = 23.53%, so a suited floor of
# 21.3% at BTN IS the ticket's headline "≥90% of the suited universe" target
# (21.3 / 23.53 = 90.5%); pre-slice BTN sat at 69.9% of it. Early seats cannot
# reach a high share at any price — the whole suited universe is wider than the
# UTG range — so there the floor states the SUBSTITUTION, not a level.
# ⚠️ UTG / HJ / CO / BTN / SB LOWERED by N-TAGWIDTH (7.0 -> 4.9 · 14.8 -> 12.0
# · 17.8 -> 12.5 · 21.3 -> 15.2 · 17.0 -> 14.3), under explicit owner
# adjudication. Reason: this floor was authored while the TOTAL was frozen, and
# once the total falls it stops expressing "the tag is suited-forward" and
# starts forcing absurdity — at the shipped BTN width it would demand 90% of
# the suited universe (32s, 42s, 52s) from a range that had to fold K8o and 98o
# to pay for it, which is the shape regression the wave-5 review caught. UTG's
# is lowered for the same reason one seat earlier: its recomposition pays for
# ATo+/KQo out of the A6s-A2s / K7s / Q8s / J8s / T8s / 87s tail.
# ⚠️ DISCLOSURE (review fold): three of the new values now sit BELOW the
# PRE-N-TAGCOMP suited width the floor was originally authored to exclude —
# UTG 4.9 vs 5.43, CO 12.5 vs 13.42, BTN 15.2 vs 16.44 (HJ 12.0 vs 11.01 and
# SB 14.3 vs 13.57 still sit above theirs). So this row no longer, by itself,
# prevents a return to the pre-N-TAGCOMP composition at those seats. What
# carries that defence now is the class-level pin
# (`test_tagwidth_late_seat_suited_classes_pinned`), which a width floor never
# could: it names the classes, so the old offsuit-heavy shape cannot come back
# under any width. UTG1 / UTG2 / LJ / BB floors and the whole
# `_TAG_OFFSUIT_CEILING` row are UNCHANGED. Each new value sits ~0.2-0.7pp
# under its shipped width. UTG is deliberately ABSENT from this floor
# (theory delta-review L3, wave-5 ledger): a 4.9 floor under the shipped 5.13
# would re-impose a de-facto two-sided freeze against the one-sided
# outside-suited ceiling, and the escalated early-seat trim must not have to
# delete a green floor to move UTG — its shape defence is the exact offsuit
# block pin (`test_tagwidth_utg_offsuit_block_pinned`) instead.
_TAG_SUITED_FLOOR = {
    "UTG1": 7.7, "UTG2": 8.3, "LJ": 11.8, "HJ": 12.0,
    "CO": 12.5, "BTN": 15.2, "SB": 14.3, "BB": 13.0,
}
# Pre-slice per-seat TOTAL authored first-in raise %, frozen (measured on the
# wave-3 tip e25abde). As N-TAGCOMP shipped, the slice never rose above any of
# them and fell by at most 0.4525pp (seat-average 34.0204 -> 33.8529), which is
# why it did not re-anchor the tag rows of BANDS. ⚠️ BOTH of those statements
# are now HISTORY: N-TAGWIDTH trims five seats far below these values
# (seat-average 27.89) and DID re-anchor the BANDS rows. This dict stays as the
# one-sided rise ceiling it always was — the gate still passes, a fortiori.
_TAG_TOTAL_PRESLICE = {
    "UTG": 17.1946, "UTG1": 18.7029, "UTG2": 21.4178, "LJ": 27.9035,
    "HJ": 36.3499, "CO": 48.7179, "BTN": 58.5219, "SB": 46.6063, "BB": 30.7692,
}
# ONE-SIDED on purpose (theory review D2). The gate this slice needs is "a
# composition swap may not be used to buy WIDTH"; a two-sided ±1pp band would
# additionally freeze the width in place, and the very next filed ticket wants
# it lower — the tag's per-seat authored widths sit ~1.7x a TAG dossier
# envelope at CO/BTN, and trimming toward it is `N-TAGWIDTH` (blocked on the §5
# PFR-floor decision, not on this test). A future trim must not have to DELETE
# a green gate to proceed, so falling is unconstrained and only rising is
# capped. The 0.1pp allowance is float/rounding slack, not authoring headroom:
# one suited class at edge weight is 0.15pp, so no real widen fits under it.
_TAG_TOTAL_RISE_CEILING = 0.1


def test_tagcomp_offsuit_opens_replaced_by_suited():
    """🔴 N-TAGCOMP defect gate — the finding's named mechanism. Failed at
    pre-slice HEAD on BOTH legs at ALL NINE seats (offsuit 7.24 / 8.14 / 9.95 /
    14.03 / 19.46 / 29.41 / 36.20 / 27.15 / 15.84 all above ceiling; suited
    5.43 / 5.58 / 6.49 / 8.45 / 11.01 / 13.42 / 16.44 / 13.57 / 9.50 all below
    floor).

    Both legs are asserted together, and the one-sided rise ceiling below is
    the third leg: the floor alone could be satisfied by widening, which is not
    what T-M2 asked for. (Deleting range is deliberately NOT blocked — falling
    width is unconstrained per the N-TAGWIDTH adjudication; the suited floor
    guards the suited side of a trim, and the offsuit side is intentionally
    open — delta-review D2.)"""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    kinds = _authored_first_in_by_kind(packs[VillainType.TAG])
    over = {
        pos: round(kinds[pos]["offsuit"], 2)
        for pos, cap in _TAG_OFFSUIT_CEILING.items()
        if kinds[pos]["offsuit"] > cap
    }
    assert not over, f"tag offsuit open width above ceiling: {over}"
    under = {
        pos: round(kinds[pos]["suited"], 2)
        for pos, floor in _TAG_SUITED_FLOOR.items()
        if kinds[pos]["suited"] < floor
    }
    assert not under, f"tag suited open width below floor: {under}"


def test_tagcomp_total_width_never_rises():
    """PRESERVATION, one-sided (see `_TAG_TOTAL_RISE_CEILING`): a composition
    swap may not be spent on WIDTH. Passes at pre-slice HEAD (delta 0 by
    construction) and after (every seat ≤ pre-slice; as N-TAGCOMP shipped, the
    largest fall was 0.4525pp at HJ — N-TAGWIDTH has since taken the falls far
    deeper, which this one-sided gate is designed to allow). That is what makes
    it a belt on the composition gate — the offsuit ceiling alone could be
    satisfied by widening the suited rows instead of substituting into them.

    A future width TRIM is deliberately still green here. `_TAG_SUITED_FLOOR`
    guards only the SUITED side of a trim; offsuit deletion passes every tag
    gate by design (the one-sided trade adjudicated at the wave-4 fan-in —
    N-TAGWIDTH expects the offsuit side to shrink toward the dossier)."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    kinds = _authored_first_in_by_kind(packs[VillainType.TAG])
    rfi = {pos: sum(k.values()) for pos, k in kinds.items()}  # already in %
    bad = {
        pos: (round(rfi[pos], 4), pre)
        for pos, pre in _TAG_TOTAL_PRESLICE.items()
        if rfi[pos] > pre + _TAG_TOTAL_RISE_CEILING
    }
    assert not bad, (
        f"tag authored first-in width ROSE above pre-slice + "
        f"{_TAG_TOTAL_RISE_CEILING}pp (now, pre-slice): {bad}"
    )


# Per-CLASS pair treatment on the pre-slice tip e25abde, resolved with sampler
# semantics (first matching `unopened` node, first matching mix; a class in no
# mix is fold-by-rule and pins as None). Every played pair sits in the core mix
# at `{"raise": 1.0}` and the pair row is a clean top-anchored band, so the
# whole pre-slice mapping is exactly "these classes at raise 1.0, the rest
# unplayed" — recorded here as the band's weakest played class per seat.
_TAG_PAIR_BAND_PRESLICE = {
    "UTG": "55", "UTG1": "44", "UTG2": "44", "LJ": "33", "HJ": "22",
    "CO": "22", "BTN": "22", "SB": "22", "BB": "33",
}
_PAIR_CLASSES = [r + r for r in reversed("23456789TJQKA")]  # AA..22


def test_tagcomp_pair_band_unchanged_preservation():
    """PRESERVATION: the swap is offsuit-for-suited ONLY, and the pack `_doc`
    promises the pair band is byte-identical — so pin the actual per-class
    TREATMENT, not a rounded aggregate (Codex review MED). An aggregate-only
    gate is satisfiable by, say, demoting one pair to 0.5 and promoting another
    from nothing; this one is not.

    A future edit therefore cannot quietly pay for the suited floor out of the
    pair band, which would confound T-M2's measurement and is not what the
    finding named."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    from app.domain.personas import _combos

    pack = packs[VillainType.TAG]
    bad: dict[str, list[str]] = {}
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
        floor_idx = _PAIR_CLASSES.index(_TAG_PAIR_BAND_PRESLICE[pos.value])
        for idx, cls in enumerate(_PAIR_CLASSES):
            want = {"raise": 1.0} if idx <= floor_idx else None
            got = None
            if node is not None:
                for mix in node.mixes:
                    if cls in _combos(mix.combos):
                        got = dict(mix.weights)
                        break
            if got != want:
                bad.setdefault(pos.value, []).append(f"{cls}: {got} != {want}")
    assert not bad, f"tag per-class pair treatment moved: {bad}"


# --------------------------------------------- N-TAGWIDTH — tag width trim
# Filed off the wave-4 fan-in (ledger `persona-realism-wave4-m4bet-tagcomp.md`,
# finding T-D2): N-TAGCOMP held the tag's per-seat opening width, and that width
# sat far over every credible per-seat RFI reference — the button opened
# K5o / Q7o / J7o at 58.22% because a frozen total has to put its surplus
# SOMEWHERE once the suited rows saturate.
#
# WHERE THE TARGETS COME FROM, and why the gates below are shaped the way they
# are. The repo's only audited per-seat RFI source is the research
# doc `docs/ai-dlc/research/rfi-seat-provenance.md` (R9-SEATPROV). It is not
# yet tracked in git as this branch is written; the orchestrator commits it at
# landing, which is what makes the citations below resolvable. Its anchor
# triple, carried verbatim so this file does not become a second source of
# truth:
#
#   (format: 9-max full-ring cash, 100bb · pool: solver-derived SIMPLIFIED
#    charts, Preflop Wizard "Preflop Charts: Free GTO Poker Range Charts for
#    Every Position (2026)" · source: preflopwizard.app/blog/preflop-charts)
#   — VERIFIED by direct fetch 2026-07-31; APPLICABLE, the strongest triple
#   found; caveat: exact solver/config unstated, seats coarser than nine.
#
# Its synthesis row (RFI %): UTG 9-13 · UTG1 10-14 · UTG2 11-15 · LJ 12-17 ·
# HJ 14-19 · CO 20-27 · BTN 30-45 (anchor 40 VERIFIED) · SB 15-36 (anchor 30,
# the doc's own "weakest row") · BB n/a. The doc's DO-NOT list is explicit that
# **no full row is gate-grade** and that only ordinal/shape claims are safe to
# gate today. So this slice gates ONE-SIDED CEILINGS (a width may not exceed X)
# plus ORDINAL comparisons computed from the packs at test time — never a
# two-sided band. An earlier cut of this slice gated a two-sided envelope taken
# from the gitignored persona dossier; its BTN floor of 42 excluded this doc's
# own verified anchor of 40, and it is gone.
#
# WHAT MOVED: UTG, HJ, CO, BTN, SB. UTG1 / UTG2 / LJ / BB are untouched and the
# pair band is untouched everywhere (still pinned by
# `test_tagcomp_pair_band_unchanged_preservation`).
#
# UTG is a RECOMPOSITION, not an offsuit cut (17.04 -> 14.18, the whole
# reduction taken out of the SUITED tail): A6s-A2s, K7s, Q9s, Q8s, J8s, T8s and
# 87s go, K8s/A7s drop to half weight, and ATo/KQo come back at FULL weight, so
# the offsuit width is held at HEAD's 4.52. The justification is DIRECTIONAL and
# positional, not a gate: UTG's provenance band is 9-13 and its unopened arrival
# is 1.000, so it is both the furthest over its reference and the seat where
# composition matters most. An earlier cut of this slice did the opposite here —
# deleted AJo/ATo/KQo/KJo and kept 87s/Q8s/J8s/T8s — which is the same defect it
# had just repaired at the button, one seat earlier in the ladder. (Note the
# emitter's rows are top-anchored prefixes, so retiring A8s-A6s necessarily
# retires the wheel aces with them; a solver UTG keeps A5s-A2s as blockers, and
# that shape is a row GAP the model cannot express. A8s+ is the contiguous
# approximation, chosen deliberately.)
#
# THE SUITED WALK-BACK IS OWNER-ADJUDICATED, not a builder's licence. At the
# four LATE seats the junk suited tail (32s-92s bottoms, J2s-J4s, T2s-T4s, Q2s,
# 63s/73s/74s/83s/84s/93s/94s) is retired and the freed width goes back into the
# standard offsuit block. That PARTIALLY reverses N-TAGCOMP's suited push at
# those seats, so `_TAG_SUITED_FLOOR` is lowered there (see the note on that
# dict) — and, so the reversal is bounded rather than open-ended, the suited
# class SET at each of the four seats is pinned class-by-class below.
#
# WHAT IS *NOT* DONE, and why. Both are structural, and both are argued with
# numbers in `content/personas/ladders/tag.unopened.json`'s `_doc`:
#  (1) HJ and CO cannot reach 14-19 / 20-27 while LJ is frozen at 27.9035 —
#      the authored ladder must be non-decreasing UTG -> BTN, so the shipped
#      29.41 / 30.77 are the tightest values that keep LJ < HJ < CO.
#  (2) The early seats are an ESCALATED contract conflict, not an oversight.
#      Unopened arrival is early-position dominated (measured, 10 seeds x
#      n=4000: UTG 1.000, UTG1 0.781, UTG2 0.537, LJ 0.324, HJ 0.191,
#      CO 0.119, BTN 0.073, SB 0.036, BB 0.000), so population PFR is made at
#      UTG-LJ. Taking UTG1/UTG2/LJ to their provenance bands models at ~2.1pp
#      of PFR unadjusted and ~1.6pp after this slice's measured
#      self-compensation factor (0.63 measured / 0.85 modelled = 0.74);
#      against a measured pre-slice PFR of 12.67 that lands at 10.57-11.1,
#      i.e. 0.9-1.43pp under the §5 tag PFR band's low edge of 12. Even the
#      most optimistic estimate raised in review (~0.7pp) lands on it. That
#      edge is DIRECTIONAL, not frozen-hard: §5a records the PFR row VERIFIED
#      (conf MEDIUM, ledger #14) with DIRECTIONAL band edges,
#      and §5 forbids any RP6/population number becoming a gate before the
#      W4-b re-anchor — nothing in the suite reds on it. Two DIRECTIONAL
#      targets (per-seat RFI, aggregate PFR) therefore bracket that edge and
#      one of them has to move: an owner decision, escalated.
#
# Gates are AUTHORED-shape and deterministic — no sampling, so no CI.
# Population VPIP/PFR stays REPORTED-not-gated (the single band anchor is W4-b).
# ⚠️ READ THE SWEEP HONESTLY: at n=4000 x 10 the shipped pack reads PFR
# 12.04, sd 0.21, se 0.066, 95% CI [11.91, 12.17] — the interval STRADDLES the
# §5 low edge of 12, and 4 of the 10 seeds read below it (min 11.750). "PFR is
# inside §5" is therefore NOT a settled fact for this slice; what is true is
# that the point estimate sits 0.04pp above a DIRECTIONAL edge, measured on a
# non-reference instrument (3x-persona lineup, one-sidedly low vs the §5 pool),
# and that nothing in the suite reds on it — §5 forbids gating a population
# number before the W4-b re-anchor. Flagged for that re-anchor's watch list.

# Documentation only — the synthesis row above, in code, so a reader can see
# what each ceiling was derived from. NOT gated: per the source doc, no row is
# gate-grade, and the two-sided form is exactly what review rejected.
_TAG_PROVENANCE_RFI = {
    "UTG": (9, 13), "UTG1": (10, 14), "UTG2": (11, 15), "LJ": (12, 17),
    "HJ": (14, 19), "CO": (20, 27), "BTN": (30, 45), "SB": (15, 36),
}
# ONE-SIDED per-seat ceilings for the five seats this slice moves.
#   BTN 45.0 / SB 36.0 — the provenance synthesis MAXIMUM, reached: shipped
#     43.89 and 34.24 sit inside the published band (BTN also above its
#     verified anchor of 40, which the band's own low edge does not exclude).
#   HJ 29.6 / CO 31.0 — NOT the provenance maximum. Those seats cannot reach
#     14-19 / 20-27 while LJ is frozen at 27.9035 and the ladder must be
#     monotone (blocker (1) above), so they are gated one-sided AT THEIR
#     SHIPPED VALUE (+~0.2pp float slack) as no-rise ceilings. The claim is
#     "this trim cannot be quietly undone", not "this seat is in band".
#   UTG 14.3 — same treatment: 14.18 shipped, still over the 9-13 band; UTG
#     moved for composition and positional direction, not to satisfy a gate.
# ⚠️ 45.0 and 36.0 are unattributed band EDGES of the provenance synthesis (only
# the anchors 40 / 30 carry a citation). They are used here ONLY as one-sided
# no-regression bounds and never as targets: per §5a a LOW-confidence number may
# bound a regression, it may not define a pass. Nothing below rewards a seat for
# approaching them, and no floor is asserted anywhere in this dict.
_TAG_WIDTH_CEILING = {
    "UTG": 14.3, "HJ": 29.6, "CO": 31.0, "BTN": 45.0, "SB": 36.0,
}
# Per-seat OFFSUIT ceilings for the four seats whose offsuit was CUT. Pre-slice
# HEAD read HJ 14.03 · CO 23.53 · BTN 29.86 · SB 22.62; shipped 10.86 / 11.76 /
# 22.17 / 13.57, each cap ~0.7-0.9pp above the shipped value. BTN's is the
# loosest on purpose: its offsuit was RESTORED (18.10 in the first cut -> 22.17)
# and what stops it becoming junk again is the class+weight pin below, not a
# tighter number. UTG is deliberately ABSENT: its offsuit width is unchanged
# from HEAD (4.52) because that seat is a recomposition — the suited tail paid
# for the restored ATo+/KQo — so an offsuit ceiling there would assert nothing.
_TAG_MOVED_OFFSUIT_CEILING = {
    "HJ": 11.6, "CO": 12.5, "BTN": 23.0, "SB": 14.4,
}
# CLASS-LEVEL suited pin for the four seats whose suited rows were walked back
# (Codex review: an aggregate suited number cannot prove composition — a seat
# could hold its width while swapping A2s for 32s). Same discipline as the pair
# pin: the exact classes, per weight tier, as the chart reads.
_TAG_LATE_SUITED_PIN = {
    "HJ": {
        1.0: ("A2s+", "K5s+", "Q6s+", "J7s+", "T7s+", "97s+", "87s", "76s", "65s"),
        0.5: ("K4s", "Q5s", "J6s", "T6s", "96s", "86s", "75s", "64s"),
    },
    "CO": {
        1.0: ("A2s+", "K4s+", "Q6s+", "J7s+", "T7s+", "97s+", "87s", "76s", "65s"),
        0.5: ("K3s", "Q5s", "J6s", "T6s", "96s", "86s", "75s", "64s", "54s"),
    },
    "BTN": {
        1.0: ("A2s+", "K2s+", "Q4s+", "J6s+", "T6s+", "96s+", "86s+", "76s", "65s", "54s"),
        0.5: ("Q3s", "J5s", "T5s", "95s", "85s", "75s", "64s", "53s", "43s"),
    },
    # 53s is deliberately ABSENT while 43s is present at BTN: the connectedness
    # exemption in the spec's authoring rule (a true connector outranks a
    # one-gapper), already adjudicated NOT a defect — and adding it back would
    # also break the lag lane's suited class-superset gate, whose red mode is
    # exactly "the tag adds a suited class the lag does not open".
    "SB": {
        1.0: ("A2s+", "K4s+", "Q5s+", "J6s+", "T6s+", "96s+", "86s+", "76s", "65s", "54s"),
        0.5: ("K3s", "Q4s", "J5s", "T5s", "95s", "85s", "75s", "64s"),
    },
}
# ONE-SIDED leak guard for the seats outside the late-seat walk-back: their
# suited width may not RISE above the shipped value. Deliberately not an
# equality pin — the early-seat trim is an escalated OPEN question (blocker (2)
# above), and a two-sided pin here would force whoever resolves it to delete a
# green test first. UTG's entry is its post-recomposition value.
_TAG_OUTSIDE_SUITED_CEILING = {
    "UTG": 5.13, "UTG1": 8.75, "UTG2": 9.20, "LJ": 12.52, "BB": 14.18,
}
# The standard 9-max button offsuit block, pinned BY WEIGHT TIER. Both tiers
# are pinned (Codex review): the half-weight row is part of the claim "the
# standard block is restored", and pinning only the full-weight row would let a
# 98o -> 87o swap through every gate in this file. This is the class-level
# statement of the shape regression review caught in the first cut, which left
# the button folding K8o / T8o / 98o outright while opening 32s at 0.5.
_TAG_BTN_OFFSUIT_BLOCK = {
    1.0: ("A2o+", "K9o+", "Q9o+", "J9o+", "T9o"),
    0.5: ("K8o", "Q8o", "J8o", "T8o", "98o"),
}
_TAG_OFFSUIT_LADDER_SEATS = ("UTG", "UTG1", "UTG2", "LJ", "HJ", "CO", "BTN")


def _tag_suited_by_weight(pack: PersonaPack, seat: str) -> dict[float, set[str]]:
    """Suited classes of one seat's `unopened` node, grouped by raise weight
    (sampler semantics: first matching node, first matching mix)."""
    from app.domain.personas import _combos

    node = next(
        n for n in pack.preflop
        if n.facing == "unopened" and n.positions and Position(seat) in n.positions
    )
    out: dict[float, set[str]] = {}
    for cls in _CLASS_COMBOS:
        if len(cls) == 2 or cls[2] != "s":
            continue
        for mix in node.mixes:
            if cls in _combos(mix.combos):
                w = mix.weights.get("raise", 0.0)
                if w:
                    out.setdefault(w, set()).add(cls)
                break
    return out


def _tag_offsuit_by_weight(pack: PersonaPack, seat: str) -> dict[float, set[str]]:
    """Offsuit classes of one seat's `unopened` node, grouped by raise weight."""
    from app.domain.personas import _combos

    node = next(
        n for n in pack.preflop
        if n.facing == "unopened" and n.positions and Position(seat) in n.positions
    )
    out: dict[float, set[str]] = {}
    for cls in _CLASS_COMBOS:
        if len(cls) == 2 or cls[2] != "o":
            continue
        for mix in node.mixes:
            if cls in _combos(mix.combos):
                w = mix.weights.get("raise", 0.0)
                if w:
                    out.setdefault(w, set()).add(cls)
                break
    return out


def _tag_cliff(pack: PersonaPack) -> float:
    """BTN / UTG authored first-in raise width — the ladder's cliff ratio."""
    rfi = _authored_first_in_raise(pack)
    return rfi["BTN"] / rfi["UTG"]


def test_tagwidth_per_seat_width_under_ceiling():
    """🔴 N-TAGWIDTH defect gate. Failed at pre-slice HEAD at ALL FIVE moved
    seats: UTG 17.04 > 14.4 · HJ 35.90 > 29.6 · CO 48.42 > 31.0 ·
    BTN 58.22 > 45.0 · SB 46.61 > 36.0.

    ONE-SIDED by construction (see `_TAG_WIDTH_CEILING`): the provenance doc
    forbids gating a two-sided level, and a future slice that trims FURTHER —
    which is what the escalated early-seat conflict may license — must not have
    to delete a green test to do it."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    kinds = _authored_first_in_by_kind(packs[VillainType.TAG])
    bad = {
        pos: (round(sum(kinds[pos].values()), 2), cap)
        for pos, cap in _TAG_WIDTH_CEILING.items()
        if sum(kinds[pos].values()) > cap
    }
    assert not bad, f"tag authored first-in width above ceiling (now, cap): {bad}"


def test_tagwidth_moved_seat_offsuit_under_ceiling():
    """🔴 N-TAGWIDTH defect gate #2 — the offsuit junk. Failed at pre-slice
    HEAD at all five moved seats (UTG 4.52 / HJ 14.03 / CO 23.53 / BTN 29.86 /
    SB 22.62, every one above its cap)."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    kinds = _authored_first_in_by_kind(packs[VillainType.TAG])
    over = {
        pos: (round(kinds[pos]["offsuit"], 2), cap)
        for pos, cap in _TAG_MOVED_OFFSUIT_CEILING.items()
        if kinds[pos]["offsuit"] > cap
    }
    assert not over, f"tag offsuit open width above ceiling (now, cap): {over}"


def test_tagwidth_late_seat_suited_classes_pinned():
    """🔴 N-TAGWIDTH defect gate #3 — the junk suited tail, pinned CLASS BY
    CLASS. Failed at pre-slice HEAD at all four late seats, which opened the
    whole suited universe down to 32s/42s/52s (BTN), Q2s/J2s/T2s (CO/SB) and
    93s/83s (HJ).

    Two-sided on purpose, unlike the width gates: this is the bounded form of
    the owner-adjudicated walk-back of N-TAGCOMP's suited push. Retiring more
    suited, or quietly putting the tail back, both fail here."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    pack = packs[VillainType.TAG]
    bad: dict[str, str] = {}
    for seat, pin in _TAG_LATE_SUITED_PIN.items():
        got = _tag_suited_by_weight(pack, seat)
        want = {w: parse_range(", ".join(toks)) for w, toks in pin.items()}
        if got != want:
            diffs = []
            for w in sorted(set(got) | set(want)):
                only_pack = sorted(got.get(w, set()) - want.get(w, set()))
                only_pin = sorted(want.get(w, set()) - got.get(w, set()))
                if only_pack or only_pin:
                    diffs.append(f"@{w}: extra={only_pack} missing={only_pin}")
            bad[seat] = "; ".join(diffs)
    assert not bad, f"tag late-seat suited classes moved: {bad}"


def test_tagwidth_outside_seats_suited_width_never_rises():
    """🔴 ONE-SIDED (see `_TAG_OUTSIDE_SUITED_CEILING`). Red at pre-slice HEAD
    on the UTG leg (7.99 against the 5.13 this slice ships — that seat's
    recomposition is paid for out of its suited tail); the UTG1 / UTG2 / LJ /
    BB legs held at HEAD and are the leak guard: the suited walk-back is
    authorised at HJ / CO / BTN / SB only, so no seat outside that scope may
    end up with MORE suited width than it ships with here.

    Falling is deliberately unconstrained: the early-seat trim is an open,
    escalated question and must not have to delete a green test to proceed
    (the one-sided lesson N-TAGCOMP's rise ceiling taught this very slice)."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    kinds = _authored_first_in_by_kind(packs[VillainType.TAG])
    bad = {
        pos: (round(kinds[pos]["suited"], 2), cap)
        for pos, cap in _TAG_OUTSIDE_SUITED_CEILING.items()
        if kinds[pos]["suited"] > cap + 0.01
    }
    assert not bad, f"tag suited width rose outside the walk-back scope: {bad}"


def test_tagwidth_btn_offsuit_block_restored():
    """🔴 Red at pre-slice HEAD (which opened K5o+/Q7o+/J8o+/T8o+/98o — a
    SUPERSET of the standard block, which this exact-set pin rejects) and red
    again against this slice's first cut, which trimmed offsuit only and left
    the button opening 32s at 0.5 while FOLDING K8o, T8o and 98o outright.
    Between those two failure modes sits the shape this gate asserts, which is
    why it is pinned as an exact set rather than a floor.

    The second failure is the self-inflicted one (the N-LAGLADDER precedent for
    labelling a regression a slice caused itself). The block is
    pinned by WEIGHT TIER: the half-weight row carries the claim just as much
    as the full-weight one, and pinning only the latter would let a 98o -> 87o
    swap through."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    got = _tag_offsuit_by_weight(packs[VillainType.TAG], "BTN")
    bad = []
    for weight, toks in _TAG_BTN_OFFSUIT_BLOCK.items():
        want = parse_range(", ".join(toks))
        missing = sorted(want - got.get(weight, set()))
        extra = sorted(got.get(weight, set()) - want)
        if missing or extra:
            bad.append(f"@{weight}: missing={missing} extra={extra}")
    assert not bad, f"BTN offsuit block moved: {bad}"


def test_tagwidth_utg_offsuit_block_pinned():
    """Theory delta-review M1 (wave-5 ledger): UTG's rewritten offsuit shape —
    ATo+/KQo at full weight and NO other offsuit at any weight — is exactly
    the shape the v2 cut deleted (it folded AJo/ATo/KQo/KJo outright), and it
    was the one rewritten seat with no class pin on the offsuit side: with the
    one-sided width gates alone, deleting ATo+/KQo again would leave every
    gate green. Exact per-tier pin, mirroring `_TAG_BTN_OFFSUIT_BLOCK`."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    got = _tag_offsuit_by_weight(packs[VillainType.TAG], "UTG")
    want = parse_range("ATo+, KQo")
    missing = sorted(want - got.get(1.0, set()))
    extra = sorted(got.get(1.0, set()) - want)
    assert not missing and not extra, (
        f"UTG full-weight offsuit block moved: missing={missing} extra={extra}"
    )
    stray = sorted(set(got) - {1.0})
    assert not stray, f"unexpected UTG offsuit weight tiers: {stray}"


def test_tagwidth_cliff_ordering_reported_not_gated():
    """REPORT-ONLY, deliberately DEMOTED from an assertion.

    The BTN/UTG width cliff is a cross-persona ORDERING claim, and the
    provenance doc's "safe to gate today" list contains only three WITHIN-
    persona shape statements (strict seat-by-seat increase to the button, SB
    between CO and BTN, BTN the widest non-blind seat). Its cross-archetype
    cliff ordering — nit < TAG <= LAG — sits in the archetype-implications
    section, which is explicitly [UNVERIFIED] direction-only, and §5a forbids
    hard-gating an unverified row. An earlier review of this slice prescribed
    a hard gate here; that prescription is OVERRULED and the number is
    reported instead.

    Context worth reading in the printout: the tag's cliff was 3.4159 at HEAD,
    fell to 2.7257 under this slice's first cut (the button trimmed while UTG
    stood still) and is restored above the nit's now. The LAG's cliff is 2.6318
    — BELOW the tag's, which inverts the doc's own cliff(LAG) >= cliff(TAG)
    leg. That inversion PRE-DATES this slice (it was already true against the
    HEAD tag at 3.4159), is owned by the lag lane, and is being filed by the
    orchestrator; nothing here should be read as this slice causing it."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    cliffs = {
        vt.value: _tag_cliff(packs[vt])
        for vt in (VillainType.NIT, VillainType.TAG, VillainType.LAG)
    }
    print(
        "BTN/UTG authored width cliff — "
        + " · ".join(f"{k} {v:.4f}" for k, v in cliffs.items())
        + " (REPORTED, not gated: cross-persona cliff ordering is [UNVERIFIED]"
        " in rfi-seat-provenance.md; direction nit < TAG <= LAG)"
    )
    assert all(v > 0 for v in cliffs.values())


def test_tagwidth_offsuit_ladder_monotone_and_btn_above_sb():
    """PRESERVATION (held at HEAD, BROKEN by this slice's first cut at the SB
    leg: BTN offsuit 18.10 against SB 19.00). Offsuit width must be
    non-decreasing UTG -> BTN, and the BUTTON — the seat with position on
    everyone and no blind posted — must open more offsuit than the SB.

    The blinds leg is what the first cut lacked: the UTG->BTN chain alone let
    a late trim push the button's offsuit under a blind's without any gate
    noticing."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    kinds = _authored_first_in_by_kind(packs[VillainType.TAG])
    bad = [
        f"{a} {kinds[a]['offsuit']:.2f} > {b} {kinds[b]['offsuit']:.2f}"
        for a, b in zip(
            _TAG_OFFSUIT_LADDER_SEATS, _TAG_OFFSUIT_LADDER_SEATS[1:], strict=False
        )
        if kinds[a]["offsuit"] > kinds[b]["offsuit"]
    ]
    assert not bad, f"tag offsuit width not monotone to the button: {bad}"
    assert kinds["BTN"]["offsuit"] > kinds["SB"]["offsuit"], (
        f"BTN offsuit {kinds['BTN']['offsuit']:.2f} is not above SB "
        f"{kinds['SB']['offsuit']:.2f}"
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
