"""Persona postflop engine (S4) — analytic strength ladder + lever-shaped
mixed decisions.

Pure domain, no Monte-Carlo in the hot loop: `strength_bucket` classifies a
hand analytically (best-5 rank tuples + rank/suit counting), and
`sample_postflop_decision` maps (bucket, draw, facing state) through a shared
merit table shaped multiplicatively by the pack's postflop levers. Mechanics
(the merit numbers) live here; every persona-differentiating number lives in
`content/personas/*.json` (PersonaPack.postflop). The rng is the HAND's
injected `random.Random` — same convention as `personas.py`.

Frozen interface + behavior rules: docs/ai-dlc/specs/simulate-s4.md.
"""

from __future__ import annotations

import itertools
import math
import random
from enum import StrEnum

from app.domain.action import Decision
from app.domain.content.models import PersonaPack, PersonaPostflop
from app.domain.equity import _RIDX, _eval5
from app.domain.spot import ActionType, Card, LegalAction, Street
from app.domain.table.postflop_context import BustedDraw, PostflopContext
from app.domain.table.sizing import postflop_node_key, pot_fraction_to_bb
from app.domain.texture import classify

_ACE = 12  # rank index of the ace in equity.RANKS
_KING = 11


class StrengthBucket(StrEnum):
    """7-rung made-hand ladder — disjoint by construction (spec-pinned):
    sets are ALWAYS monster, never two_pair_plus; straights on paired boards
    stay monster; a pocket pair below the top board card is always
    middle_pair (never overpair_tptk/top_pair)."""

    MONSTER = "monster"
    TWO_PAIR_PLUS = "two_pair_plus"
    OVERPAIR_TPTK = "overpair_tptk"
    TOP_PAIR = "top_pair"
    MIDDLE_PAIR = "middle_pair"
    ACE_HIGH = "ace_high"
    AIR = "air"


class DrawCategory(StrEnum):
    NONE = "none"
    WEAK = "weak"  # gutshot / backdoor-flush+overcard class
    STRONG = "strong"  # flush draw / OESD / combo


class SizeBucket(StrEnum):
    """RES-E size taxonomy on live pot-fraction (faced_bb / pot-before-the-bet).
    Shared vocabulary for F1 (faced defense) and F2 (chosen-size bluffing)."""

    SMALL = "small"  # <= 0.40 pot
    MEDIUM = "medium"  # 0.41 - 0.70
    LARGE = "large"  # 0.71 - 1.10
    OVERBET = "overbet"  # > 1.10


def size_bucket(pot_fraction: float) -> SizeBucket:
    """RES-E §2 cutoffs, locked: computed on the LIVE pot-fraction at decision
    time, never on the discrete authored sizing keys."""
    if pot_fraction <= 0.40:
        return SizeBucket.SMALL
    if pot_fraction <= 0.70:
        return SizeBucket.MEDIUM
    if pot_fraction <= 1.10:
        return SizeBucket.LARGE
    return SizeBucket.OVERBET


_RUNG = {
    StrengthBucket.AIR: 0,
    StrengthBucket.ACE_HIGH: 1,
    StrengthBucket.MIDDLE_PAIR: 2,
    StrengthBucket.TOP_PAIR: 3,
    StrengthBucket.OVERPAIR_TPTK: 4,
    StrengthBucket.TWO_PAIR_PLUS: 5,
    StrengthBucket.MONSTER: 6,
}


def _best5(cards: list[Card]) -> tuple:
    """Best 5-card rank tuple over 5/6/7 cards (analytic, no MC)."""
    rs = [_RIDX[c[0]] for c in cards]
    ss = [c[1] for c in cards]
    best: tuple | None = None
    for idx in itertools.combinations(range(len(cards)), 5):
        v = _eval5([rs[i] for i in idx], [ss[i] for i in idx])
        if best is None or v > best:
            best = v
    return best  # type: ignore[return-value]  # len(cards) >= 5 always


def _high_card_bucket(hole_hi: int) -> StrengthBucket:
    return StrengthBucket.ACE_HIGH if hole_hi >= _KING else StrengthBucket.AIR


def _pair_bucket(pair_rank: int, kicker: int, board_top: int) -> StrengthBucket:
    if pair_rank != board_top:
        return StrengthBucket.MIDDLE_PAIR
    # Top pair: top kicker = ace, or king when top pair IS aces.
    top_kicker = _ACE if pair_rank != _ACE else _KING
    return StrengthBucket.OVERPAIR_TPTK if kicker >= top_kicker else StrengthBucket.TOP_PAIR


def _made_bucket(hole: tuple[Card, Card], board: list[Card]) -> StrengthBucket:
    r1, r2 = _RIDX[hole[0][0]], _RIDX[hole[1][0]]
    hole_hi = max(r1, r2)
    pocket = r1 == r2
    board_ranks = {_RIDX[c[0]] for c in board}
    board_top = max(board_ranks)
    rank = _best5(list(hole) + list(board))
    cat = rank[0]

    if cat >= 4:  # straight/flush/boat/quads — monster even on paired boards
        return StrengthBucket.MONSTER
    if cat == 3:  # trips: set or trips (hole card plays) = monster; board trips: high card
        return StrengthBucket.MONSTER if rank[1] in (r1, r2) else _high_card_bucket(hole_hi)
    if cat == 2:  # two pair
        if pocket:  # pocket pair + board pair (below set strength)
            # F7 bug 1: only a real strong two pair when the POCKET is the top
            # pair of the best five (pocket above the board's paired rank —
            # TT on 883). An under-pocket-pair also reads "two pair" to _eval5
            # (22 on 883 = "eights and deuces"), but the board pair plays for
            # everyone; its true showdown class is the same pocket-underpair
            # the unpaired-board cat==1 rule maps to MIDDLE_PAIR (22 on 883
            # == 22 on K72). Pre-fix it classed TWO_PAIR_PLUS and raised a
            # 3bb-into-6bb bet at .734 with 0.375 equity while AK-high
            # (0.499 equity, same board) folded .406.
            if rank[1] == r1:
                return StrengthBucket.TWO_PAIR_PLUS
            return StrengthBucket.MIDDLE_PAIR
        if r1 in board_ranks and r2 in board_ranks:  # both hole cards playing
            return StrengthBucket.TWO_PAIR_PLUS
        if r1 in board_ranks or r2 in board_ranks:  # one pair + board pair
            pair_rank = r1 if r1 in board_ranks else r2
            kicker = r2 if pair_rank == r1 else r1
            return _pair_bucket(pair_rank, kicker, board_top)
        return _high_card_bucket(hole_hi)  # plays the board's two pair
    if cat == 1:  # one pair
        if pocket:  # can't equal board_top (that would be a set)
            return (
                StrengthBucket.OVERPAIR_TPTK if r1 > board_top else StrengthBucket.MIDDLE_PAIR
            )
        if rank[1] in (r1, r2):  # a hole card pairs the board
            pair_rank = rank[1]
            kicker = r2 if pair_rank == r1 else r1
            return _pair_bucket(pair_rank, kicker, board_top)
        return _high_card_bucket(hole_hi)  # board-paired, hero unpaired
    return _high_card_bucket(hole_hi)


def _straight_out_ranks(hole_ranks: set[int], all_ranks: set[int]) -> int:
    """Count distinct ranks that would complete a 5-high-run straight using at
    least one hole card. >=2 => OESD/double-gutter class, ==1 => gutshot."""
    outs = 0
    for out in range(13):
        if out in all_ranks:
            continue
        new = all_ranks | {out}
        for lo in range(-1, 9):  # lo == -1 is the wheel (A-2-3-4-5)
            window = {r if r >= 0 else _ACE for r in range(lo, lo + 5)}
            if window <= new and out in window and window & hole_ranks:
                outs += 1
                break
    return outs


def _draw_category(hole: tuple[Card, Card], board: list[Card]) -> DrawCategory:
    cards = list(hole) + list(board)
    suit_counts: dict[str, int] = {}
    for c in cards:
        suit_counts[c[1]] = suit_counts.get(c[1], 0) + 1
    hole_suits = {c[1] for c in hole}
    flush_draw = any(n == 4 and s in hole_suits for s, n in suit_counts.items())

    hole_ranks = {_RIDX[c[0]] for c in hole}
    all_ranks = {_RIDX[c[0]] for c in cards}
    straight_outs = _straight_out_ranks(hole_ranks, all_ranks)

    if flush_draw or straight_outs >= 2:
        return DrawCategory.STRONG
    backdoor_flush = len(board) == 3 and any(
        n == 3 and s in hole_suits for s, n in suit_counts.items()
    )
    overcard = max(hole_ranks) > max(_RIDX[c[0]] for c in board)
    if straight_outs == 1 or (backdoor_flush and overcard):
        return DrawCategory.WEAK
    return DrawCategory.NONE


def strength_bucket(
    hole: tuple[Card, Card], board: list[Card]
) -> tuple[StrengthBucket, DrawCategory]:
    """Analytic (bucket, draw) classification for hole cards on a 3/4/5-card
    board. On the RIVER (board len 5) DrawCategory is always NONE — busted
    draws land in AIR/ACE_HIGH by made strength."""
    made = _made_bucket(hole, board)
    draw = DrawCategory.NONE if len(board) >= 5 else _draw_category(hole, board)
    return made, draw


# --------------------------------------------------------------------------
# Merit tables — SHARED game mechanics (behavior rule 4). Levers from the
# pack shape these multiplicatively; no persona-specific number lives here.
# Base masses are pre-normalization merits (components > 1 are fine).
# --------------------------------------------------------------------------

# Unopened / matched-with-option: aggressive (bet or raise) vs check merit.
_AGG_BASE = {
    StrengthBucket.MONSTER: 0.85,
    StrengthBucket.TWO_PAIR_PLUS: 0.75,
    StrengthBucket.OVERPAIR_TPTK: 0.70,
    StrengthBucket.TOP_PAIR: 0.55,
    StrengthBucket.MIDDLE_PAIR: 0.30,
    StrengthBucket.ACE_HIGH: 0.05,
    StrengthBucket.AIR: 0.05,
}
_CHECK_BASE = {
    StrengthBucket.MONSTER: 0.15,
    StrengthBucket.TWO_PAIR_PLUS: 0.25,
    StrengthBucket.OVERPAIR_TPTK: 0.30,
    StrengthBucket.TOP_PAIR: 0.45,
    StrengthBucket.MIDDLE_PAIR: 0.70,
    StrengthBucket.ACE_HIGH: 0.95,
    StrengthBucket.AIR: 0.95,
}
# Facing chips: fold / call / raise merit. Calibration (refuter round 2):
# tuned so a stickiness ~1.0 persona folds to a flop c-bet ~0.45-0.55 and
# stickiness 1.8 lands ~0.25-0.35; call floors keep low-stickiness personas
# (nit, 0.6) calling with real pairs so AF isn't call-starved. AIR call base
# dropped 0.25->0.08 (A1) so no-draw air stops floating; drawing air is
# unaffected since _DRAW_CALL_BONUS (WEAK 0.20 / STRONG 0.55) still adds on
# top. Street-aware river "air-call ~0" gate is deferred to a later slice
# (P2a) — this change is street-neutral, no street/river logic added here.
#
# ACE_HIGH stays 0.40 — a MEASURED negative result, not an oversight (W3R-3 #5,
# H117 "naked ace-high floats raise-wars", owner decision 2026-07-24). Cutting this
# GLOBAL base the way A1 cut AIR was tried and DROPPED: ACE_HIGH is ~35% of the
# passive fish's real arrival range, so any cut below ~0.30 pushes the fish's
# arrival-range fold-to-bet ABOVE the RES-D α = f/(1+f) ceiling (at base 0.22:
# 0.408 vs α+0.05 = 0.383 at ½-pot, 0.658 vs 0.650 at 1.5×), while the only
# α-clean value (0.30) moves the roster's ace-high fold by only +0.03 — cosmetic
# under the softmax law. Do NOT re-attempt a flat cut here — the global cut stays
# REFUTED, and the fish arithmetic above is the reason: it is why nobody may cut
# this global base, and it is unaffected by anything below.
#
# WHAT "REFUTED" NOW SCOPES TO, because T1 collided with it. Refuted is the FLAT
# GLOBAL cut: lowering `_CALL_BASE[ACE_HIGH]` itself, at every opponent count
# INCLUDING heads-up, on every node. That is still forbidden and the numbers
# above still forbid it. What is no longer true is the implication a reader
# would draw from them, that an effective base of 0.22 is unreachable anywhere:
# T1 (improvement slice 2, 2026-08-18) ships exactly 0.22 effective
# (0.40 × 0.55) on multiway flop and turn nodes FACING A BET — the same kind of
# node the 0.408-vs-0.383 figure above was computed on, differing only in that
# the figure was computed heads-up over the fish's arrival range.
# The two have not been reconciled by measurement and this comment does not
# claim they have. What is measured is narrower and is on the record:
# `docs/ai-dlc/research/slice2-invest-then-fold/alpha-multiway-t1.md`
# reports the naked-ace-high facing-a-bet fold rate at one, two and three
# opponents, and finds it already above α at 15 of 24
# cells at ONE opponent on the untouched engine — i.e. before T1 — which is why
# the α curve is not the instrument that settles this. Whether the W3R-3
# refutation should now be re-derived multiway is an OPEN QUESTION referred to
# the owner, not a question this comment answers.
#
# W3R-6 LANDED the scoped form instead: `_ACE_HIGH_FLOAT_RAISE_DAMP` multiplies
# this base for naked ace-high on the flop/turn (see the call-merit branch
# below). T1 (improvement slice 2, 2026-08-18) widened its predicate from
# `facing_raise` to `facing_raise or opponents > 1`.
#
# W3R-6's SAFETY ARGUMENT DIED WITH THAT WIDENING AND IS NOT REPLACED IN KIND.
# It used to read: the α-ceiling contract is measured over a facing-a-BET curve,
# so a facing-a-RAISE gate is off the measurement node by construction and every
# facing-a-BET decision stays byte-identical. The second clause is now FALSE at
# more than one opponent — that is exactly what T1 buys. What is true instead:
#
#  - HEADS-UP facing a bet is still byte-identical, and that is now a TESTED
#    property rather than a structural one
#    (`test_ace_high_multiway_damp_gate_lock`).
#  - The α = f/(1+f) fold ceiling is asserted over the one-pair no-draw
#    BLUFF-CATCHER range (`_CATCHER_BUCKETS`,
#    `test_fold_to_bet_respects_alpha_ceiling`), which EXCLUDES ace-high — the
#    stated reason being that ace-high loses to part of a balanced bettor's
#    bluff half, so it is not a catcher. Measured on a 1,250-spot naked
#    ace-high range, the fold rate exceeds α at 15 of 24 persona-and-size cells
#    ALREADY at ONE opponent on the untouched engine (nit 0.2920 vs α 0.2481
#    facing ⅓-pot, pre-T1), so α as currently written does not discriminate a
#    good tip from a bad one on this bucket. WHETHER α SHOULD BE ASSERTED OVER
#    ACE-HIGH AT ALL IS AN OPEN QUESTION referred to the owner; this comment
#    reports the measurement and does not settle the contract. Full table:
#    `docs/ai-dlc/research/slice2-invest-then-fold/alpha-multiway-t1.md`.
#  - What protects the CATCHER range is now the BUCKET gate alone, and that is
#    tested at one, two and three opponents by
#    `test_bluff_catcher_alpha_contract_untouched_at_multiple_opponents`. Widen
#    the bucket gate and that test is what fails. Note the scope honestly: that
#    test guards the catcher range, which is NARROWER than what W3R-6's prose
#    asserted — the old claim covered every facing-a-bet decision for every
#    bucket, and no test replaces it in that width.
_FOLD_BASE = {
    StrengthBucket.MONSTER: 0.0,
    StrengthBucket.TWO_PAIR_PLUS: 0.05,
    StrengthBucket.OVERPAIR_TPTK: 0.05,
    StrengthBucket.TOP_PAIR: 0.12,
    StrengthBucket.MIDDLE_PAIR: 0.35,
    StrengthBucket.ACE_HIGH: 0.60,
    StrengthBucket.AIR: 0.75,
}
_CALL_BASE = {
    StrengthBucket.MONSTER: 0.35,
    StrengthBucket.TWO_PAIR_PLUS: 0.55,
    StrengthBucket.OVERPAIR_TPTK: 0.70,
    StrengthBucket.TOP_PAIR: 0.78,
    # W3R-4 (#11): 0.60 -> 0.52. Naked middle pair was mildly over-calling; this
    # is a FIT SEED, measured (not dropped in) — every persona's AF/fold-to-cbet/
    # WTSD band was re-measured across 0.48/0.52/0.56/0.60 and stays IN its frozen
    # band at 0.52 (no re-anchor). Mirrors the A1-style base trims.
    StrengthBucket.MIDDLE_PAIR: 0.52,
    StrengthBucket.ACE_HIGH: 0.40,
    StrengthBucket.AIR: 0.08,
}
_RAISE_BASE = {
    StrengthBucket.MONSTER: 0.65,
    StrengthBucket.TWO_PAIR_PLUS: 0.40,
    StrengthBucket.OVERPAIR_TPTK: 0.25,
    StrengthBucket.TOP_PAIR: 0.10,
    StrengthBucket.MIDDLE_PAIR: 0.05,
    StrengthBucket.ACE_HIGH: 0.02,
    StrengthBucket.AIR: 0.02,
}
# Draw bonuses (semi-bluff aggression + drawing calls), added pre-lever.
_DRAW_AGG_BONUS = {DrawCategory.NONE: 0.0, DrawCategory.WEAK: 0.15, DrawCategory.STRONG: 0.35}
_DRAW_RAISE_BONUS = {DrawCategory.NONE: 0.0, DrawCategory.WEAK: 0.05, DrawCategory.STRONG: 0.15}
_DRAW_CALL_BONUS = {DrawCategory.NONE: 0.0, DrawCategory.WEAK: 0.20, DrawCategory.STRONG: 0.55}
# Structural constants (shared mechanics).
# River polarization (P2a Q1): on the river (opt-in via the `street` kwarg)
# raising is polar — value raises come from TWO_PAIR_PLUS+, bluff raises from
# the bluff cell; the one-pair middle (bluff-catchers) never raises, and air
# never calls. These buckets get their non-bluff raise merit floored to 0.0.
# OVERPAIR_TPTK is a coarse compromise: the merged bucket spans thin-value
# hands that a finer split would let raise; splitting it is a later slice.
_RIVER_RAISE_FLOOR = (
    StrengthBucket.MIDDLE_PAIR,
    StrengthBucket.TOP_PAIR,
    StrengthBucket.OVERPAIR_TPTK,
)
# W1-a (F6): the unopened river BET floor — strictly NARROWER than the raise
# floor. A middle pair on the river is a bluff-catcher, never a value bet, under
# a conservative HU/balanced-villain DEFAULT (it CAN value-bet vs capped/station
# ranges — a rank approximation, not a theorem). TOP_PAIR/OVERPAIR keep the thin
# river value bet (they are floored on the RAISE only). P2a floored the river
# raise + air-call; this closes the residual unopened-BET leak for MIDDLE_PAIR.
_RIVER_BET_FLOOR = (StrengthBucket.MIDDLE_PAIR,)
_BLUFF_RAISE_FACTOR = 0.3  # bluff-raising is structurally rarer than bluff-betting
_COMMIT_AGG_BOOST = 3.0  # SPR-commit shift toward call/jam
# W2-b (B5b, F7): the max fraction of a draw's CALL/RAISE bonus removed at full
# commitment when the draw is NOT value-committed (below T1) — a naked draw stops
# stacking off. Scaled by the commitment fraction c in [0,1]. FIT SEED.
_B5B_DRAW_DAMP = 0.7
# W3-c (B6, F4/F19/F8): street-conditional aggression. A `street_agg_mult` decays
# the BLUFF/semi-bluff merit ONLY (value never scaled) as the hand goes deeper —
# people barrel air less on later streets and give up. FLOP == 1.0 keeps the flop
# byte-identical (the invariant); an omitted/None street (harness, estimator) also
# resolves to 1.0. FIT SEEDS.
_STREET_AGG_MULT = {Street.FLOP: 1.0, Street.TURN: 0.6, Street.RIVER: 0.33}
# F19: a WEAK (thin) semi-bluff dies faster than a generic bluff — full on the flop,
# cut on the turn, ~0 by the river (a busted thin draw stops barrelling).
_STREET_WEAK_DRAW_MULT = {Street.FLOP: 1.0, Street.TURN: 0.4, Street.RIVER: 0.0}
# B7 (F8): extra RIVER bluff mass for a busted draw that BET the previous street —
# a coherent barrel-then-miss story. Busted STRAIGHT is preferred over busted FLUSH
# (the missed suit shows on board). Added AFTER the street decay so the story-bluff
# survives it. FIT SEEDS; gated on context.bet_prev_street.
_BUSTED_RIVER_BLUFF = {BustedDraw.STRAIGHT: 0.30, BustedDraw.FLUSH: 0.15}
# W3R-6 (#9, H117/H32/H107): made one-pair stops re-raising into flop/turn
# action. `_RIVER_RAISE_FLOOR` already KILLS this line on the river; pre-river it
# must be rare but alive (a protection/merge raise is real), so this is a damp,
# not a floor (A1 guardrail: a direction, never an asserted floor). Multiplies
# the `_RAISE_BASE` term ONLY — `_DRAW_RAISE_BONUS` stays outside, which IS the
# "semi-bluff raises are spared" mechanic. FIT SEED, range [0.25, 0.55].
#
# GATE = facing a RAISE — the spec's AUTHORIZED NARROWING, taken on a MEASURED
# bust, not a band move. The wider "facing chips" gate was implemented and
# measured first: it shifts one-pair raise merit onto FOLD inside the passive
# fish's real arrival range, pushing its 1.5×-overbet fold-to-bet to 0.6528 vs
# the α + 0.05 ceiling of 0.650 (undamped baseline 0.6422 — only 0.0078 of
# headroom). In-range values 0.45/0.55 scraped under by ~0.004, i.e. luck, not
# structure. Narrowing removes the interaction entirely (the arrival-range α
# curve is a facing-a-BET curve) and still covers every cited hand — H117 / H32 /
# H107 are all raise-war spots.
# OVERPAIR_TPTK is deliberately NOT damped: that bucket bundles true overpairs
# (AA on K-high) with TPTK, and damping it would damp real overpairs. H107 is
# therefore only PARTIALLY addressed here — the rest needs W3R-7's bucket split.
#
# FITTED at 0.35 (the range midpoint's shape target), measured on normalized
# P(RAISE) facing a flop/turn raise: tag MIDDLE_PAIR 0.187 → 0.075, tag TOP_PAIR
# 0.308 → 0.135, maniac MIDDLE_PAIR 0.360 → 0.165, maniac TOP_PAIR 0.528 → 0.281
# (a ~2.9× pre-normalization cut). 0.25/0.45/0.55 also clear the spot legs; 0.35
# is the value whose cut matches the "rare but alive" shape argument. With the
# narrowed gate every candidate leaves the α curve and the frozen bands untouched.
_ONE_PAIR_RAISE_DAMP = 0.35
# W3R-6 (#5, re-routed from W3R-3): naked ace-high stops FLOATING on the
# flop/turn. Multiplies the `_CALL_BASE[ACE_HIGH]` term only, gated on
# draw NONE + flop/turn + (facing a raise OR more than one opponent live). The
# FOLD merit is never boosted — the fold share rises through normalization.
# FIT SEED, range [0.35, 0.65].
#
# T1 (improvement slice 2, 2026-08-18) ADDED the `opponents > 1` half. W3R-6's
# gate was `facing_raise` alone and was justified as node-scoped — off the
# facing-a-BET α measurement node by construction. That justification is GONE;
# see the block above `_FOLD_BASE` for what replaces it. The value 0.55 is
# unchanged and was not re-fitted: T1 changed WHERE the damp fires, never how
# hard. Measured effect of the widening, 50,000 hands at seed 20260817 on the
# ratified lineup: invest-then-fold events 1,147 → 1,084, pool went-to-showdown
# 54.5% → 54.1%.
#
# The pre-existing multiway effect on this bucket is on the OTHER side of the
# decision and predates T1: `_MW_CATCH_TIGHTEN` (see `_MW_CATCH_BUCKETS`) already
# multiplies ACE_HIGH's FOLD merit by 1.15 ** (opponents - 1). So naked ace-high
# was never byte-identical across opponent counts; what T1 newly adds is a
# multiway effect on the CALL side. Any test asserting only "calls less multiway
# than heads-up" is therefore vacuous — it passed before T1.
#
# FITTED at 0.55 — effective in-node base 0.40 × 0.55 = 0.22, exactly the W3R-3
# magnitude that was directionally right and failed only on scope. Measured on
# ΔP(FOLD) facing a raise (the ≥ 0.05 target): tag flop +0.104 / turn +0.114,
# passive_fish flop +0.096 / turn +0.101, with P(CALL) falling 0.361 → 0.237 and
# 0.280 → 0.176. 0.35/0.45/0.65 also clear the ≥ 0.05 bar (+0.073 … +0.181); 0.55
# is kept because it is the anchored magnitude and the mildest one that clears it
# with margin at every measured cell.
_ACE_HIGH_FLOAT_RAISE_DAMP = 0.55


def _draw_agg_street_mult(draw: DrawCategory, street: Street | None) -> float:
    """Street decay for a draw's SEMI-BLUFF aggression bonus (F19): WEAK draws
    decay steeply, STRONG draws on the generic bluff schedule. Flop/None → 1.0."""
    if draw is DrawCategory.WEAK:
        return _STREET_WEAK_DRAW_MULT.get(street, 1.0)
    if draw is DrawCategory.STRONG:
        return _STREET_AGG_MULT.get(street, 1.0)
    return 1.0


# W3-d (B2, F3): a vulnerable one-pair made hand slows its BETTING as overcards
# fall. Scoped to MIDDLE_PAIR / TOP_PAIR ONLY — OVERPAIR_TPTK bundles overpairs
# (which want to keep betting) and is untouched. Non-linear in the count of board
# cards ranked above the pair. FIT SEEDS.
_VULNERABLE_ONE_PAIR = (StrengthBucket.MIDDLE_PAIR, StrengthBucket.TOP_PAIR)


def _overcard_count(hole: tuple[Card, Card], board: list[Card]) -> int:
    """Board cards ranked strictly above this hand's pair. Pair rank = the pocket
    rank, or the single hole card that paired the board; ambiguous shapes (two
    pair / unpaired) fall back conservatively to max(hole) → few/no overcards."""
    r1, r2 = _RIDX[hole[0][0]], _RIDX[hole[1][0]]
    if r1 == r2:
        pair_rank = r1
    else:
        board_ranks = {_RIDX[c[0]] for c in board}
        if r1 in board_ranks and r2 not in board_ranks:
            pair_rank = r1
        elif r2 in board_ranks and r1 not in board_ranks:
            pair_rank = r2
        else:
            pair_rank = max(r1, r2)
    return sum(1 for c in board if _RIDX[c[0]] > pair_rank)


def _overcard_bet_damp(count: int) -> float:
    """B2 damp: 0 overcards → 1.00, 1 → 0.75, 2+ → 0.50 (non-linear FIT SEEDS)."""
    return 1.0 if count == 0 else 0.75 if count == 1 else 0.5


# W3-d (B3, F20): board WETNESS gates whether-to-bet one pair, not just sizing.
# Ordering asserted (dry ≥ high-two-tone ≥ low-connected ≥ monotone); magnitudes
# are FIT SEEDS. Reuses the ONE texture classifier (never a second taxonomy).
def _wetness_bet_mult(board: list[Card]) -> float:
    if len(board) < 3:
        return 1.0
    tex = classify(board)  # classifies the flop (first 3 cards)
    if tex.suitedness == "monotone":
        return 0.55
    if tex.connectedness == "connected":  # low/high connected — draw-heavy
        return 0.70
    if tex.suitedness == "two-tone":
        return 0.85
    return 1.0  # dry: rainbow + disconnected


# F3 bounded aggression (RES-D §0 saturation fix): the `aggression` lever is
# capped before it scales any merit. An uncapped maniac lever (15.0) multiplies
# one side of the un-normalized merit ratio so hard that rng.choices degenerates
# to near-argmax (top-pair unopened P(bet)=0.948, entropy 0.29 bits; with the
# SPR-commit boost the effective multiplier hit 15×3=45, monster-commit
# P(bet)=0.991, entropy 0.08 bits). The cap is a MECHANIC (shared compression
# law, lives in code per the S4 split); persona identity stays in the pack's
# lever. 5.6 = 1.75 × the highest non-maniac lever (lag 3.2), fitted by sweep
# (4.8/5.6/6.4 against the closed-loop harness): the cap is the identity map
# for every other authored persona (all ≤ 3.2 — their sampled decisions are
# byte-unchanged, F3-verified) while the maniac stays strictly the most
# aggressive persona everywhere the lever applies — per-node (exact-weight
# ordering test) AND in population AF (~3.2-3.3 vs lag ~2.1-2.5; the tighter
# 4.8 cap dropped maniac AF into lag's range). The commit interaction is
# bounded as a consequence (5.6 × 3 = 16.8, was 45). Mixing restored:
# top-pair unopened P(bet) 0.948 → 0.873 (entropy 0.29 → 0.55 bits) — see
# the F3 tests.
_AGGRESSION_CAP = 5.6

# N-LOGIT: the runtime safety range for `continue_ref`, the frozen facing-node
# calibration anchor the RAISE merit is divided by. Mirrors the model's
# `Field(ge=0.05, le=8.0)` on purpose — validation cannot protect the division
# on its own, because `model_copy(update=...)` skips it and the suite builds
# unvalidated postflop blocks that way routinely (ledger R2-5). The lower bound
# is the load-bearing one: the smallest subnormal passes a bare `> 0` test and
# turns the scale into `inf`, emitting `[0.0, 0.0, nan]`.
_CONTINUE_REF_MIN = 0.05
_CONTINUE_REF_MAX = 8.0

# F1 price-aware defense (RES-D §1a/§2 + RES-E buckets). α = B/(P+B) is the
# fold-CEILING for the bucket's representative size — an anchor the fold merit
# scales AGAINST, never a floor the engine clamps folds up to (A1 guardrail:
# no code path may assert fold >= anything derived from α/MDF).
_BUCKET_ALPHA = {
    SizeBucket.SMALL: 0.25,  # ~⅓ pot
    SizeBucket.MEDIUM: 0.375,  # ½–⅔ pot
    SizeBucket.LARGE: 0.47,  # ¾–pot
    SizeBucket.OVERBET: 0.60,  # 1.5× pot (the engine's only overbet size)
}
# Reference size for the price ratio (MEDIUM ≈ the ½–⅔-pot c-bet the merit
# tables were originally calibrated against).
_ALPHA_REF = _BUCKET_ALPHA[SizeBucket.MEDIUM]
# The three shared price constants, fitted numerically (F1 tuning harness:
# uniform-random hole + flop range, analytic fold-rate per candidate) against
# min(RES-D §2 band top, α − 0.01) per persona × bucket:
# - LEVEL: global fold-merit level at the MEDIUM reference. The pre-F1 tables
#   over-folded the α ceiling at every size (a tag folded ~0.39 to a ⅓-pot bet
#   vs α 0.25); 0.35 re-levels the whole curve under the ceiling.
# - SENSITIVITY: exponent on the α ratio — how fast fold merit grows with size.
# - STICKINESS_DAMP: the LEGACY `stickiness` price wiring, used ONLY when a pack
#   has not opted into W2-a (`size_elasticity is None`) — the effective exponent
#   is SENSITIVITY * stickiness**(-DAMP), so stickier personas (station 1.8,
#   fish 1.4) respond LESS to price than the disciplined low-stickiness ones
#   (nit/tag 0.6). W2-a splits this: an explicit `size_elasticity` bypasses this
#   branch for a DIRECT exponent (see `_price_exponent`), and the flat call-merit
#   scaling moves to the separate `call_looseness` lever.
_PRICE_LEVEL = 0.35
_PRICE_SENSITIVITY = 2.2
_PRICE_STICKINESS_DAMP = 0.15

# F2 size-linked bluffing (RES-D §1b/§3 + RES-E §2-§3). Polar bluff SHARE of
# the betting range at each bucket's representative chosen size, f/(1+2f)
# with value:bluff = (1+f):f — the share RISES with size (bigger bets carry
# proportionally more bluffs; value:bluff tightens toward 1:1):
#   SMALL  ⅓-pot        → 0.20
#   MEDIUM ½–⅔          → 0.25–0.286, rep 0.27
#   LARGE  ¾–pot        → 0.30–0.333, rep 0.32
#   OVERBET 1.5× (α .60) → 0.375
# Consumed as a RATIO vs the MEDIUM reference (the ½–⅔-pot class the flat
# bluff_freq levers were calibrated against, mirroring _ALPHA_REF): theory
# sets the SHAPE across sizes, the persona's bluff_freq keeps setting the
# LEVEL — so the RES-D §3 ordering station < nit < fish < tag < lag < maniac
# is preserved at every size.
_BUCKET_BLUFF_SHARE = {
    SizeBucket.SMALL: 0.20,
    SizeBucket.MEDIUM: 0.27,
    SizeBucket.LARGE: 0.32,
    SizeBucket.OVERBET: 0.375,
}
_BLUFF_SHARE_REF = _BUCKET_BLUFF_SHARE[SizeBucket.MEDIUM]


# F4 multiway calibration correction (RES-D §6, direction only): "bluff less
# + value-lean" per added opponent. The unopened/aggressor-side half of this
# is already live via `multiway_bluff_damp ** max(opponents-1, 0)` on
# `bluff_mass` (S4-era) — confirmed measurably lower 3-way vs HU in the F4
# audit. This constant closes the facing-side gap: bluff-catching (folding a
# weak made hand to a bet) was flat across `opponents` on the bot path (S8's
# `_MW_CATCH_TIGHTEN` only ever touched the GRADER). Mirrors the S8 pattern —
# a flat multiplicative tighten on the fold merit for bluff-catch-class
# buckets (AIR/ACE_HIGH/MIDDLE_PAIR facing a bet), exponentiated the same way
# as `multiway_bluff_damp` (per-added-opponent decay, NOT an n-th-root
# MDF/defense constant — no per-opponent MDF number is asserted anywhere).
# 1.15 = the grader's `_MW_VALUE_LEAN` value, reused here as "value-lean"
# framed as tightening the fold-ceiling side; kept deliberately modest (a
# direction, not a target level).
# R10-TAIL-b1: TOP_PAIR joined the catch class. One pair — even top pair —
# shrinks in value with every added opponent (someone in a 4-way field has it
# beat far more often than heads-up), yet the facing-side fold merit was flat
# across `opponents` for it: a station called a 4-way raise with bare top pair
# exactly as often as a heads-up one. Base stays 1.15 (directional, unsourced —
# design pass §D1). NON-COVERAGE, deliberate: OVERPAIR_TPTK and TWO_PAIR_PLUS
# stay outside the class — their multiway pile-up defect is W4-a's (contract §4
# P6), and this slice must not silently claim it.
_MW_CATCH_TIGHTEN = 1.15
_MW_CATCH_BUCKETS = (
    StrengthBucket.AIR,
    StrengthBucket.ACE_HIGH,
    StrengthBucket.MIDDLE_PAIR,
    StrengthBucket.TOP_PAIR,
)

# W1-c (F13, RES-D §6 direction-only): the VALUE-BET side of the multiway
# correction. `multiway_bluff_damp` already tightens bluffs and `_MW_CATCH_TIGHTEN`
# the bluff-catch folds per added opponent; made-value BETTING was flat across
# `opponents`. Damp the unopened made-value BET merit geometrically as the field
# grows — HU (opponents==1) is byte-identical (exponent 0). Scoped to the
# THIN-value buckets (top pair / middle pair — the opponent-count-sensitive ones);
# NOT monsters/two-pair+/overpairs (strong value you bet multiway regardless).
# `0.8` is an UNFIT directional SEED (no multiway made-value metric is live — a
# merit multiplier under softmax, so the observed bet-rate change is far smaller
# than 0.8**k); capped at a labeled 4-way tier (`_MW_VALUE_CAP` added opponents —
# 5+way magnitudes are unresearched → Later).
_MW_VALUE_DAMP = 0.8
_MW_VALUE_CAP = 3
_MW_VALUE_BUCKETS = (StrengthBucket.TOP_PAIR, StrengthBucket.MIDDLE_PAIR)


def _bluff_size_factor(frac: float) -> float:
    """Multiplier on the bluff mass for a chosen pot-fraction: the bucket's
    polar bluff share relative to the MEDIUM reference. Bucketed on the
    authored pot-fraction key (RES-E §3's chosen-size mapping)."""
    return _BUCKET_BLUFF_SHARE[size_bucket(frac)] / _BLUFF_SHARE_REF


def _sizing_dist(pf, board: list[Card], legal: list[LegalAction], is_aggressor: bool):
    """The sizing distribution this decision draws from (R2 node-aware
    override when authored + aggressor context supplied; else flat)."""
    if pf.sizing_by_node and is_aggressor:
        node = postflop_node_key(board, legal, is_aggressor=is_aggressor)
        return pf.sizing_by_node.get(node, pf.sizing)
    return pf.sizing


# R10-TAIL-a1 (M3) — the absolute-price tail above the OVERBET representative.
#
# `_BUCKET_ALPHA`'s top bucket has NO upper edge, so α — the only price-carrying
# input the facing branch has — is CONSTANT for every faced price above 1.10×
# pot. Measured at HEAD (station, AIR/NONE, HU flop, facing a raise): a 1.11×,
# a 2.33× and a 10× jam are one identical node, P(call) = 0.4044 at all three.
# 100% of that flatness is the open-ended bucket, 0% is `size_elasticity` — the
# exponent is applied to a ratio that has already saturated, so no value of it
# creates a slope (design pass §A1-A3, `docs/ai-dlc/reports/r10-tail-design.md`).
#
# ANCHOR — not a fit knob. 1.5× pot is (a) the engine's own maximum AUTHORED bet
# size (`content/personas/{maniac,lag}.json` `sizing_by_node` key "1.5") and (b)
# the size `_BUCKET_ALPHA[SizeBucket.OVERBET] = 0.60` represents, i.e. the node
# the RES-D α fold-ceiling contract was measured on. Anchoring strictly ABOVE it
# keeps every α-measured cell byte-identical BY CONSTRUCTION — the passive fish
# has only 0.0078 of headroom against that ceiling at a faced 1.5× (the
# `_ONE_PAIR_RAISE_DAMP` headroom measurement above), so an unconditional
# fold-merit increase there would breach it. Prices below the
# anchor are the PLATEAU-HEIGHT defect (a `call_looseness` dial question), owned
# by W4-b's single re-anchor — deliberately untouched here (§A6).
#
# K — the one new mechanic constant: the tail's steepness, ADDITIVE in the
# exponent (`e + K` via the extra `(f/anchor)**K` factor), never multiplicative
# (`e·k`). Additive keeps the tail's cross-persona dispersion equal to the head's;
# `e·k` MULTIPLIES the exponent spread the W2-a elasticity split deliberately set
# (station 1.21 vs legacy 2.41) and collapses the maniac — measured at f = 2.33,
# its AIR raise share falls to 0.15× HEAD under `e·k` vs 0.48× under `e + K`, and
# R10-2's specialist adjudication explicitly REFUTED the maniac's defect claim
# (0/15). `test_price_tail.py`'s dispersion floor is what forces the additive
# form. 2.0 is a DIRECTIONAL SEED in the range [1.5, 2.5], NOT a fitted target:
# no sourced fold-to-overbet-raise frequency exists in the contract (§D1), so
# this ticket is gated on monotonicity and direction only. It is the mildest
# seed producing a non-cosmetic slope without breaching the dispersion floor
# (K = 2.5 measures 0.0757 against a 0.0769 floor — the range top does NOT hold).
_PRICE_TAIL_ANCHOR = 1.5
_PRICE_TAIL_K = 2.0


def _price_factor(faced_fraction: float, exponent: float) -> float:
    """Multiplier on the fold merit for a faced bet at `faced_fraction` of the
    pot: LEVEL * (α_bucket/α_ref) ** exponent. Monotone non-decreasing across
    SMALL→OVERBET because _BUCKET_ALPHA is (for any exponent >= 0). The exponent
    is resolved by `_price_exponent` (W2-a).

    R10-TAIL-a1: above `_PRICE_TAIL_ANCHOR` the bucketed α saturates, so the
    factor keeps climbing with the UNBOUNDED price ratio instead —
    `(f/anchor) ** K`. Continuous at the anchor (the factor is ×1 there),
    byte-identical at and below it, strictly increasing in `f` above it. This
    only ever SCALES the fold merit: no fold floor or clamp is asserted anywhere
    (the A1 guardrail), and because the cut lands on the fold side the call mass
    it removes is redistributed by normalization to every OTHER candidate in
    proportion — P(raise) FALLS with price rather than inflating (the N-logit
    pathology, which is why the call merit is deliberately left price-blind).
    """
    alpha = _BUCKET_ALPHA[size_bucket(faced_fraction)]
    factor = _PRICE_LEVEL * (alpha / _ALPHA_REF) ** exponent
    if faced_fraction > _PRICE_TAIL_ANCHOR:
        factor *= (faced_fraction / _PRICE_TAIL_ANCHOR) ** _PRICE_TAIL_K
    return factor


def _price_exponent(pf: PersonaPostflop) -> float:
    """W2-a: the price-response exponent, driven by `size_elasticity`.

    Two branches to preserve default-off byte-identity WHILE fixing the crash +
    direction reversal a naive rename would cause:
    - `size_elasticity is None` (un-opted-in) → the LEGACY inverse formula
      `SENSITIVITY * stickiness**(-DAMP)`: stickier personas (station 1.8, fish
      1.4) respond LESS to price than the disciplined low-stickiness ones
      (nit/tag 0.6). Byte-identical to pre-W2.
    - `size_elasticity` set → a DIRECT exponent `SENSITIVITY * size_elasticity`.
      This is a DIFFERENT scale from stickiness, chosen so 0.0 is size-blind
      (exponent 0 → flat factor, no `0**-DAMP` ZeroDivisionError) and larger
      values are STEEPER (scared) — the intuitive direction. ~1.0 reproduces a
      normal price response (exponent ≈ 2.2).
    """
    if pf.size_elasticity is None:
        return _PRICE_SENSITIVITY * pf.stickiness ** (-_PRICE_STICKINESS_DAMP)
    return _PRICE_SENSITIVITY * pf.size_elasticity


def _draw_equity(draw: DrawCategory, board: list[Card]) -> float:
    """W2-b heuristic draw equity — rule-of-4-and-2, NO solve (interim EV; label
    approximate). Street is derived from `len(board)` so this never depends on the
    optional `street` kwarg being passed: flop (3 cards, 2 to come) uses ×4, turn
    (4 cards, 1 to come) uses ×2. STRONG ≈ 9 outs (flush/OESD), WEAK ≈ 4 outs
    (gutshot/backdoor). River (5 cards) or NONE → 0.0 (no draw equity; the made-
    hand path governs the river). Calibration is a Later item (H7)."""
    outs = {DrawCategory.STRONG: 9.0, DrawCategory.WEAK: 4.0}.get(draw, 0.0)
    if outs == 0.0:
        return 0.0
    cards_to_come = 5 - len(board)
    if cards_to_come >= 2:
        return outs * 4.0 / 100.0  # STRONG 0.36 / WEAK 0.16
    if cards_to_come == 1:
        return outs * 2.0 / 100.0  # STRONG 0.18 / WEAK 0.08
    return 0.0


def _value_commit_threshold(faced_fraction: float) -> float:
    """W2-b value-commit (T1) threshold: the equity at which calling/jamming all-in
    is +EV, e ≥ B/(P+2B). Expressed via the faced pot-fraction f = B/P (the already
    pre-aggression-corrected `faced_frac`): B/(P+2B) = f/(1+2f). f=1 (pot) → 1/3;
    f=3 (3×-pot overbet) → 3/7 = 0.429. A heuristic CALL-commit price proxy for the
    stack-off, NOT a full jam-EV solve (reviewer #3)."""
    return faced_fraction / (1.0 + 2.0 * faced_fraction)


def _commit_transform(
    entries: list[tuple[ActionType, float]],
) -> list[tuple[ActionType, float]]:
    """The SPR value-commit shift: zero FOLD mass, boost BET/RAISE by
    _COMMIT_AGG_BOOST, leave CALL/CHECK. Extracted so W2-b's gate can reuse it."""
    return [
        (
            a,
            0.0
            if a is ActionType.FOLD
            else m * (_COMMIT_AGG_BOOST if a in (ActionType.BET, ActionType.RAISE) else 1.0),
        )
        for a, m in entries
    ]


# W3-b (B1, F1): the aggressor-side position multiplier. In position → boost the
# whole aggressive candidate (bluff + value + semi-bluff), out of position → damp
# it, symmetrically about 1.0 and scaled by the persona's position_sensitivity
# (0/None = position-blind). FIT SEED; per-type LOW confidence. Applies to the
# unopened/betting BET candidate only (c-bet/barrel/lead) — the OOP defense damp
# is a later slice, and the matched-with-option check-raise is out of scope.
_POSITION_AGG_DELTA = 0.25


def _position_agg_mult(pf: PersonaPostflop, context: PostflopContext | None) -> float:
    s = pf.position_sensitivity
    if not s or context is None:  # None/0 lever, or an un-opted caller → identity
        return 1.0
    return 1.0 + _POSITION_AGG_DELTA * s if context.in_position else 1.0 - _POSITION_AGG_DELTA * s


# R9-DEFENCE-a: the opponent-LINE damp. `λ_p = _LINE_DELTA · pf.line_sensitivity`
# is the log-odds shift applied to the continue-vs-fold split at a facing node
# whose aggressor also bet/raised the previous postflop street.
#
# _LINE_DELTA is PINNED at 1.0 as a NORMALISATION, deliberately NOT derived from
# (or "mirrored on") `_POSITION_AGG_DELTA` or any other constant (ledger R-1).
# `λ_p` is a single product, so the 1.0/lever split is a choice of units: it makes
# `line_sensitivity` READ AS λ directly, which is what lets a pack author reason
# about the authored number in odds space.
#
# Honest status of the supporting numbers (theory review, ledger R-30): they are
# IMPLEMENTATION checks, NOT evidence about the constant. At 1.0 the reference
# node (nit / MIDDLE_PAIR / turn / HU / SPR 20 / faced 0.5-pot) reproduces the
# design pass's ΔP(fold) = +0.1312 — a prediction published BEFORE the build, so
# reproducing it proves the code matches arithmetic that already assumed 1.0. The
# `le=2.0` bound being a ">= 7x continue-odds cut" only at 1.0 is a consistency
# relation between two authored numbers. Neither is independent of the value; an
# earlier draft of this comment called them "two independent checks" and that was
# wrong.
#
# What IS load-bearing: rev 1 of the spec left the value unstated and a `1e-12`
# no-op passed 11 of its 12 acceptance criteria. A magnitude nobody pins is a
# magnitude that can silently be zero.
_LINE_DELTA = 1.0

# Runtime safety range for `line_sensitivity`, mirroring the model's
# `Field(ge=0.0, le=2.0)` for the same reason `_CONTINUE_REF_MIN/MAX` mirror
# theirs: `model_copy(update=...)` bypasses validation and the suite builds
# postflop blocks that way routinely. NaN fails both comparisons and lands in
# the same branch as an out-of-range lever.
_LINE_SENSITIVITY_MIN = 0.0
_LINE_SENSITIVITY_MAX = 2.0

# The scope of the line damp: BUCKET and DRAW are INDEPENDENT axes, so the
# predicate is the explicit product `bucket in _LINE_SCOPE_BUCKETS and draw is
# DrawCategory.NONE` — middle pair WITH a flush draw is out (ledger R-6).
# Excluded and why: MONSTER (`_FOLD_BASE` = 0.0 ⇒ P(fold) = 0 everywhere, a
# documented no-op); TWO_PAIR_PLUS (P(fold) 0.007-0.036 roster-wide — no room,
# and two pair does not fold to a barrel); OVERPAIR_TPTK (the bucket BUNDLES
# true overpairs, which must never fold to a barrel, with TPTK — pre-registered
# behind W3R-7's bucket split); any draw — see below, the reason is NOT the one
# an earlier draft of this comment gave.
#
# WHY DRAWS ARE OUT (corrected by theory review, ledger R-26). An earlier draft
# said "its continue is already priced by equity + the T1 threshold, and that
# machinery already moves with street". Both limbs are FALSE for the CALL leg:
# `call_merit = (call_base + _DRAW_CALL_BONUS[draw]) * looseness` — the
# fall-through form taken on the trailing `else` branch below (N-DRAWLOOSE
# floors the STRONG-draw bonus at `max(looseness, 1.0)` on the `if draw is
# DrawCategory.STRONG and looseness < 1.0` branch instead, but leaves this
# argument untouched) — consults no
# equity and no street on either branch — `_DRAW_CALL_BONUS` is a flat lookup —
# and the cited street-decay machinery (`_STREET_WEAK_DRAW_MULT`,
# `_DRAW_RAISE_BONUS`) is AGGRESSION-side only. Measured: a naked gutshot's
# P(call) facing a half-pot bet goes UP flop -> turn (nit 0.3556 -> 0.3696), not
# down.
# The exclusion still stands, for the honest reason: `_DRAW_CALL_BONUS[WEAK]` is
# the un-equity-gated F7 defect, and stacking an un-jointly-calibrated line factor
# on an already-inflated call merit compounds it (the W3R-5 mistake). STRONG draws
# are out pending joint calibration. KNOWN CONSEQUENCE, disclosed rather than
# discovered: a nit facing a second barrel now continues MORE with a naked 4-out
# gutshot (0.4224) than with ace-high (0.3932), where it was 0.4224 vs 0.5415
# before. Directionally a gutshot does gain against a narrowed range; what is
# unrealistic is that its response to the line is exactly ZERO. v2 must depend on
# F7's separate equity gate landing first.
_LINE_SCOPE_BUCKETS = frozenset(
    {
        StrengthBucket.MIDDLE_PAIR,
        StrengthBucket.TOP_PAIR,
        StrengthBucket.ACE_HIGH,
        StrengthBucket.AIR,
    }
)


def _line_scaled(
    entries: list[tuple[ActionType, float]], line_mult: float
) -> list[tuple[ActionType, float]]:
    """The line damp's transform: multiply CALL and RAISE by `line_mult`, leave
    every other entry (in scope: FOLD) exactly as handed in.

    Extracted so the ONE common factor is inspectable — like `_commit_transform`,
    which exists for the same reason. A gate can hand this known merits and
    assert BITWISE (`float.hex()`) that each defend entry is its own input times
    the SAME `line_mult`, which is exact without fighting IEEE because it
    compares one multiplication against itself. Behaviourally that is what P-1
    checks through the sampler, but only to a relative `1e-12` — it must, since
    downstream `(R·line_mult)·rscale` vs `(R·rscale)·line_mult` differ bitwise
    ~35% of the time (ledger R-8). A transform applying a per-action factor that
    differs by less than that tolerance passes every output-space gate in the
    harness; nothing but a direct bitwise check on this function excludes it.
    """
    return [
        (a, m * line_mult) if a in (ActionType.CALL, ActionType.RAISE) else (a, m)
        for a, m in entries
    ]


def sample_postflop_decision(
    pack: PersonaPack,
    hole: tuple[Card, Card],
    board: list[Card],
    legal: list[LegalAction],
    pot_bb: float,
    stack_bb: float,
    opponents: int,
    rng: random.Random,
    noise: float = 1.0,
    current_bet_to: float = 0.0,
    is_aggressor: bool = False,
    street: Street | None = None,
    latest_aggressor_contribution_bb: float | None = None,
    context: PostflopContext | None = None,
    facing_raise: bool = False,
    aggressor_bet_prev_street: bool = False,
) -> Decision:
    """Draw a frequency-mixed postflop decision from the pack's levers.

    R2 sizing: when `sizing_by_node` is authored on the pack AND the caller
    passes `is_aggressor`, the pot-fraction is drawn from the node-specific
    distribution (small on dry flops, big on wet turns). The default
    `is_aggressor=False` keeps every existing caller (the statistical harness,
    the range estimator) on the flat `sizing` distribution byte-for-byte — so
    action-frequency bands are unchanged; only the live bot loop opts in.

    W3-a: `context` (in_position / bet_prev_street / busted_draw) is threaded
    end-to-end as a walking skeleton but NOT yet read — the position/street/
    texture mechanics (W3-b/c/d) consume it. Default `None` and every current
    caller are byte-identical.

    W3R-6: `facing_raise` (derived by `table.postflop_context.facing_raise`) is a
    FLAT kwarg, not a `PostflopContext` field — the range estimator opts into
    this signal alone, and building a context there would newly activate W3-b's
    `in_position=False` position damp. Default `False` is byte-identical.

    R9-SIGNAL: `aggressor_bet_prev_street` (the `>= 1` threshold of
    `table.postflop_context.aggressor_barrel_run`) is the opponent-LINE signal —
    did the seat whose wager I face also bet/raise the previous POSTFLOP street?
    R9-DEFENCE-a consumes it: see the line-damp block below, which scales the
    CALL and RAISE merits at an in-scope facing node by `exp(-λ_p)`. A pack that
    does not author `line_sensitivity` is byte-identical with it True or False,
    and so is every caller leaving it at the default `False`. Also a FLAT kwarg
    for `facing_raise`'s reason (the estimator must opt into this signal alone),
    never a `PostflopContext` field.

    Facing state is derived from the `legal` shapes (unopened: CHECK+BET;
    matched-with-option: CHECK+RAISE; facing chips: FOLD+CALL[+RAISE]).
    Merits: clamp >= 0, normalize by the sum (sum 0 => CHECK if legal else
    FOLD), then ALWAYS `rng.choices` — mixed, never argmax.

    Sizing (spec-pinned): pot-fraction `f` sampled from pack sizing weights,
    independent of bucket (F2: a pure-air bluff's frequency is linked to the
    chosen size via the joint two-stage sampling documented inline; the
    authored distribution itself never varies with strength). BET:
    `f * pot_bb`. RAISE:
    `raise_to = current_bet_to + f * (pot_bb + to_call)` where `to_call` is
    the CALL entry's min_bb and `current_bet_to` is the caller-supplied
    street current bet-TO amount (HandState.current_bet_bb; 0.0 = unopened —
    it is NOT derivable from the legal bracket, whose RAISE min_bb is
    min_raise_to, not the bet being raised). Legality is guaranteed by
    rounding 2dp then clamping into [min_bb, max_bb]; a jam bracket
    (min == max) resolves to it.
    """
    pf = pack.postflop
    if pf is None:
        raise ValueError(f"persona pack {pack.id!r} has no postflop block")
    # W2-a: the two split identity levers, each falling back to `stickiness` when
    # the pack hasn't opted in (default-off byte-identity). `looseness` scales the
    # flat CALL merit — except on a STRONG draw below N-DRAWLOOSE's calling-dial
    # floor below, where it is affine in the dial instead; the price-response
    # exponent is resolved by `_price_exponent`.
    looseness = pf.call_looseness if pf.call_looseness is not None else pf.stickiness
    bucket, draw = strength_bucket(hole, board)
    by_kind = {la.action: la for la in legal}

    bluff_cell = bucket in (StrengthBucket.AIR, StrengthBucket.ACE_HIGH) and (
        draw is DrawCategory.NONE
    )
    bluff_mass = pf.bluff_freq * noise * pf.multiway_bluff_damp ** max(opponents - 1, 0)
    agg_scale = min(pf.aggression, _AGGRESSION_CAP) * noise  # F3: bounded, see _AGGRESSION_CAP

    # F2 size-linked bluffing: the joint (action, size) law for a pure-air
    # bluff candidate is  w(s) · bluff_mass · factor(s)  — sampled in two
    # stages so the ACTION draw stays the first rng.choices call (capture
    # rngs in range_estimate and the tests key on that): (1) here, scale
    # bluff_mass by E_s[factor] over the sizing distribution; (2) below, tilt
    # the size-draw weights by factor(s). Equivalent to pre-drawing the size
    # and conditioning the bluff decision on it. Strength never steers the
    # size draw (value hands keep the authored distribution byte-for-byte —
    # the anti-sizing-tell no-go); the resulting big-size lean WITHIN the
    # bluff-bet range is the Bayes face of "bigger bets carry proportionally
    # more bluffs" (RES-D §1b), not a strength→size map.
    sizing_dist = _sizing_dist(pf, board, legal, is_aggressor)
    if bluff_cell and (ActionType.BET in by_kind or ActionType.RAISE in by_kind):
        bluff_mass *= sum(
            w * _bluff_size_factor(float(k)) for k, w in sizing_dist.items()
        ) / sum(sizing_dist.values())
    # W3-c (B6/B7): decay the generic air bluff by street (flop/None → ×1.0, so
    # byte-identical), then add the busted-draw story bluff on the river — a hand
    # that bet the prior street and missed keeps a coherent barrel (survives the
    # decay; STRAIGHT > FLUSH). Value merit is never touched here.
    #
    # W3R-4 (#7): the busted add-on is still added AFTER the street decay (that
    # survival is its whole point) but now carries the SAME multiway factor the
    # generic bluff mass gets at the line above — a busted flush must not fire the
    # same story bluff into 3 callers as heads-up (TAG H41). Heads-up is
    # byte-identical (`** 0` = 1.0).
    bluff_mass *= _STREET_AGG_MULT.get(street, 1.0)
    if street is Street.RIVER and context is not None and context.bet_prev_street:
        bluff_mass += _BUSTED_RIVER_BLUFF.get(
            context.busted_draw, 0.0
        ) * pf.multiway_bluff_damp ** max(opponents - 1, 0)

    entries: list[tuple[ActionType, float]] = []
    if ActionType.FOLD in by_kind:  # facing chips
        # F1 price-aware defense: faced pot-fraction = to_call over the pot
        # the aggressor's bet/raise was made INTO, mapped to the RES-E bucket;
        # the fold merit scales with the bucket's α relative to the MEDIUM
        # reference, damped by stickiness. Call/raise merits are untouched —
        # they absorb the complement through normalization.
        #
        # Pre-aggression pot = the pot the aggressor's bet/raise was made INTO
        # = live pot − the aggressor's own contribution (the chips their bet/raise
        # added). NUMERATOR is to_call (the facing seat's call increment — the
        # right pot-fraction numerator; only the denominator was ever wrong).
        #
        # W1-b (F9): when the live loop supplies `latest_aggressor_contribution_bb`
        # (the W0-a `pot_before_current_aggression` increment), use it — the EXACT
        # pre-aggression pot. Do NOT subtract `current_bet_to`: that is the
        # aggressor's full bet-TO, which OVER-subtracts (denominator too small →
        # faced_frac OVERSTATED → over-fold) whenever the aggressor already had
        # street chips before this action — a self-re-raise (bet→raise) OR a
        # back-raise after calling (call→raise). Fresh aggression (0 prior street
        # chips) has contribution == current_bet_to, so the two agree.
        #
        # The legacy `max(current_bet_to, to_call)` branch remains ONLY for
        # un-opted-in direct callers (unit tests) that pass no contribution —
        # byte-identical to pre-W1-b; its over-subtraction is the documented
        # approximation THERE. The estimator is NOT in that set any more
        # (ESTIM-PRICE, 2026-08-01): `range_estimate._legal_from_ctx` builds
        # CALL with the real to_call and always passes the aggressor
        # contribution, so its faced_frac is live and takes the exact branch
        # below — see `range_estimate.py` and its self-re-raise regression.
        to_call_bb = by_kind[ActionType.CALL].min_bb or 0.0
        if latest_aggressor_contribution_bb is None:
            faced_frac = to_call_bb / max(pot_bb - max(current_bet_to, to_call_bb), 0.01)
        else:
            faced_frac = to_call_bb / max(pot_bb - latest_aggressor_contribution_bb, 0.01)
        fold_merit = _FOLD_BASE[bucket] * _price_factor(faced_frac, _price_exponent(pf))
        # F4 (RES-D §6): bluff-catch-class buckets fold MORE per added
        # opponent — direction only, see _MW_CATCH_TIGHTEN above.
        if bucket in _MW_CATCH_BUCKETS:
            fold_merit *= _MW_CATCH_TIGHTEN ** max(opponents - 1, 0)
        entries.append((ActionType.FOLD, fold_merit))
        # River polarization (see _RIVER_RAISE_FLOOR): air never bluff-CALLS
        # the river — it folds or bluff-raises. Flooring happens BEFORE the
        # SPR-commit block so a floored 0 survives the commit boost.
        # W3R-6 (#5) + T1: naked ace-high stops floating pre-river, both when
        # facing a RAISE and when more than one opponent is live. Damps the
        # CALL_BASE term only (the draw bonus is untouched — naked hands only),
        # gated on flop/turn; the fold share rises purely through normalization.
        # The `opponents > 1` half is T1's, and it puts this damp on a
        # facing-a-BET node for the first time — see _ACE_HIGH_FLOAT_RAISE_DAMP
        # for why the old "off the α node by construction" argument no longer
        # applies and what is tested in its place.
        call_base = _CALL_BASE[bucket]
        if (
            bucket is StrengthBucket.ACE_HIGH
            and draw is DrawCategory.NONE
            and (facing_raise or opponents > 1)
            and street in (Street.FLOP, Street.TURN)
        ):
            call_base *= _ACE_HIGH_FLOAT_RAISE_DAMP
        # N-DRAWLOOSE: a STRONG draw's call bonus stops shrinking with a tight
        # dial (`max(looseness, 1.0)`), so nits stop folding big draws. TWO
        # properties are load-bearing and both come from the branch PREDICATE
        # carrying `looseness < 1.0`:
        #  - the floor is a no-op arithmetic identity at any dial >= 1.0
        #    (`max(L, 1.0)` returns L), so falling through to the ORIGINAL
        #    expression there makes "loose personas are bitwise unchanged"
        #    STRUCTURAL. Taking the STRONG branch instead would compute
        #    `call_base*L + bonus*L` — the re-associated form this design
        #    rejects, which is bitwise equal to `(call_base + bonus)*L` only
        #    when L happens to be a power of two (the calling station's 4.0;
        #    a refit to 3.7 shifts it by an ulp).
        #  - `_call_merit_at_ref` is the UNFLOORED merit at the frozen anchor
        #    on EVERY path, i.e. exactly the base engine's call merit at `ref`.
        #    That is what lets the coupled `rscale` below hand the floor's extra
        #    continue mass to the RAISE leg in its original proportion instead
        #    of cancelling it away — see the N-LOGIT block.
        _ref_lever = pf.continue_ref if pf.continue_ref is not None else looseness
        _call_merit_at_ref = (call_base + _DRAW_CALL_BONUS[draw]) * _ref_lever
        if draw is DrawCategory.STRONG and looseness < 1.0:
            call_merit = call_base * looseness + _DRAW_CALL_BONUS[draw] * max(looseness, 1.0)
        else:
            call_merit = (call_base + _DRAW_CALL_BONUS[draw]) * looseness
        if bluff_cell and street is Street.RIVER:
            call_merit = 0.0
        entries.append((ActionType.CALL, call_merit))
        if ActionType.RAISE in by_kind:
            if bluff_cell:
                raise_merit = _BLUFF_RAISE_FACTOR * bluff_mass  # polar bluff survives
            else:
                # W3-c: the draw's semi-bluff RAISE bonus decays by street (value
                # _RAISE_BASE unchanged); flop/None → ×1.0.
                # W3R-6 (#9): a made one-pair hand stops re-raising into
                # flop/turn action. The _RAISE_BASE term ONLY is damped, so the
                # semi-bluff raise (_DRAW_RAISE_BONUS) survives intact.
                raise_base = _RAISE_BASE[bucket]
                if (
                    bucket in _VULNERABLE_ONE_PAIR
                    and facing_raise
                    and street in (Street.FLOP, Street.TURN)
                ):
                    raise_base *= _ONE_PAIR_RAISE_DAMP
                raise_merit = (
                    raise_base
                    + _DRAW_RAISE_BONUS[draw] * _draw_agg_street_mult(draw, street)
                ) * agg_scale
                if street is Street.RIVER and bucket in _RIVER_RAISE_FLOOR:
                    raise_merit = 0.0  # bluff-catchers never value-raise the river
            entries.append((ActionType.RAISE, raise_merit))
    else:  # unopened (CHECK+BET) or matched-with-option (CHECK+RAISE)
        agg_action = ActionType.BET if ActionType.BET in by_kind else ActionType.RAISE
        # W3-b (B1, F1): position tilts the aggressor-side BET frequency (c-bet/
        # barrel/lead). Multiplicative on the whole aggressive candidate; a floored
        # 0 stays 0. The matched-with-option check-RAISE is out of scope, hence the
        # BET gate. Resolved here (not post-hoc) because the bluff cell must
        # multiply BEFORE it forms its check complement — see below.
        pos_mult = _position_agg_mult(pf, context) if agg_action is ActionType.BET else 1.0
        if bluff_cell:  # bluff_freq SETS the air bet/raise mass (rule 1)
            # T-ANCHOR: multiply THEN complement. The air cell is an exact-frequency
            # cell — its two merits sum to 1, so P(bet) == the composed bluff mass.
            # Applying position after the complement was formed (the W3-b bug) left
            # CHECK at 1 − bluff_mass while BET became mult·bluff_mass, compressing
            # the IP:OOP bet-rate ratio and breaking `bluff_freq` as a frequency lever.
            bluff_bet_mass = bluff_mass * pos_mult
            agg_merit = bluff_bet_mass
            check_merit = max(1.0 - bluff_bet_mass, 0.0)
        else:
            # W3-c: the draw's semi-bluff BET bonus decays by street (value
            # _AGG_BASE unchanged); flop/None → ×1.0.
            agg_merit = (
                _AGG_BASE[bucket] + _DRAW_AGG_BONUS[draw] * _draw_agg_street_mult(draw, street)
            ) * agg_scale
            check_merit = _CHECK_BASE[bucket]
            # W1-c (F13): tighten thin made-value BETTING as the field grows —
            # the value-side mirror of the multiway bluff damp. BET only (the
            # matched-with-option check-RAISE is out of scope); HU byte-identical.
            if agg_action is ActionType.BET and bucket in _MW_VALUE_BUCKETS:
                agg_merit *= _MW_VALUE_DAMP ** min(max(opponents - 1, 0), _MW_VALUE_CAP)
            # W3-d (B2/B3, F3/F20): a vulnerable one-pair hand slows down as
            # overcards fall and on wetter boards — whether-to-bet, not just size.
            # MIDDLE_PAIR/TOP_PAIR only; composes multiplicatively with position +
            # multiway. A set/overpair is out of scope and keeps betting.
            if agg_action is ActionType.BET and bucket in _VULNERABLE_ONE_PAIR:
                agg_merit *= _overcard_bet_damp(_overcard_count(hole, board))
                agg_merit *= _wetness_bet_mult(board)
            # River polarization: the matched-with-option RAISE (check-raise
            # line) is floored for the whole one-pair class; the unopened BET is
            # floored for MIDDLE_PAIR ONLY (W1-a) — top-pair/overpair keep the
            # thin river value bet.
            if (
                agg_action is ActionType.RAISE
                and street is Street.RIVER
                and bucket in _RIVER_RAISE_FLOOR
            ):
                agg_merit = 0.0
            elif (
                agg_action is ActionType.BET
                and street is Street.RIVER
                and bucket in _RIVER_BET_FLOOR
            ):
                agg_merit = 0.0  # middle pair never value-bets the river
            # W3-b on the non-bluff path only — the bluff path already applied
            # `pos_mult` above (pre-complement). Exactly once on each path.
            agg_merit *= pos_mult
        entries.append((ActionType.CHECK, check_merit))
        entries.append((agg_action, agg_merit))

    # SPR commit (rule 2): shift to call/jam. Live SPR only — never srs.spr_bucket
    # (frozen SRS contract).
    #
    # W2-b (F5/F7): the commit shift is EV-gated on the DRAW side (directional own-
    # action policy — no forced-F*, owner decision).
    #  - A made hand (rung >= OVERPAIR) commits exactly as before (equity ≈ 1): the
    #    value-jam path is byte-identical and is NEVER draw-damped, even when it also
    #    holds a draw (reviewer #6).
    #  - A STRONG draw NOT facing a price (unopened/betting — no fold to zero)
    #    commits as before.
    #  - A draw FACING a bet commits (zero fold) ONLY when its heuristic equity
    #    clears the value-commit threshold for the faced price (T1 = f/(1+2f)). Below
    #    T1 the fold is NOT zeroed (the price-aware fold merit stands) and the draw's
    #    CALL/RAISE bonus is damped by commitment so a naked draw stops stacking off
    #    (B5b). A draw hand is never bluff_cell (draw != NONE), so the RAISE merit is
    #    always the non-bluff value+bonus form — the bonus subtraction is exact.
    if stack_bb / pot_bb <= pf.spr_commit:
        made = _RUNG[bucket] >= _RUNG[StrengthBucket.OVERPAIR_TPTK]
        facing = ActionType.FOLD in by_kind
        drawing = draw in (DrawCategory.STRONG, DrawCategory.WEAK)
        if made or (draw is DrawCategory.STRONG and not facing):
            value_commit = True
        elif facing and drawing:
            value_commit = _draw_equity(draw, board) >= _value_commit_threshold(faced_frac)
        else:
            value_commit = False
        if value_commit:
            entries = _commit_transform(entries)
        elif facing and drawing:  # below T1 — keep fold, damp the draw's stack-off pull
            c = min(max((pf.spr_commit - stack_bb / pot_bb) / pf.spr_commit, 0.0), 1.0)
            removed = _B5B_DRAW_DAMP * c
            damped: list[tuple[ActionType, float]] = []
            for a, m in entries:
                if a is ActionType.CALL:
                    if draw is DrawCategory.STRONG and looseness < 1.0:
                        m -= _DRAW_CALL_BONUS[draw] * max(looseness, 1.0) * removed
                    else:
                        m -= _DRAW_CALL_BONUS[draw] * looseness * removed
                    # Unconditional, and unfloored, for the same reason the
                    # merit above is: the reference stays the base engine's
                    # damped call merit at the anchor, `ref*(call_base +
                    # bonus*(1-removed))`. That keeps `rscale`'s L-cancellation
                    # exact on BOTH sides of the floor even under this damp.
                    _call_merit_at_ref -= _DRAW_CALL_BONUS[draw] * _ref_lever * removed
                elif a is ActionType.RAISE:
                    m -= _DRAW_RAISE_BONUS[draw] * agg_scale * removed
                damped.append((a, m))
            entries = damped

    # R9-DEFENCE-a: the opponent-LINE damp. A bot facing a wager from a seat that
    # also bet/raised the PREVIOUS postflop street (`aggressor_bet_prev_street`,
    # derived by `table.postflop_context.aggressor_barrel_run >= 1`) continues
    # less often; the freed mass goes to FOLD.
    #
    #     line_mult = exp(-λ_p)      λ_p = _LINE_DELTA · pf.line_sensitivity
    #     C' = C · line_mult ;  R' = R · line_mult ;  F untouched
    #
    # Scaling BOTH defend merits by ONE factor is exactly a shift of the
    # continue-vs-fold LOG-ODDS by λ_p, and it leaves the conditional raise share
    # exactly invariant:
    #     P'(raise | continue) = R·s / (C·s + R·s) = R / (C + R)
    # A `call_merit`-only multiplier would NOT have that property — that is the
    # N-LOGIT misroute, which sends freed call mass to RAISE.
    #
    # WHY C/R AND NEVER FOLD, given that a fold-side form would behave the same.
    # A `fold_merit`-only implementation is *projectively identical* to this one:
    #     normalize(F, C·s, R·t·s) == normalize(F/s, C, R·t)
    # so NO output-space test can distinguish the two forms (both spec reviewers
    # measured this to bit equality; rev 1 claimed a fold-side form could not pass
    # the raise-neutrality gate and that claim was FALSE — ledger R-2). The
    # C/R-only form is prescribed for AUDITABILITY, not for behaviour: the fold
    # merit stays an untouched input, which keeps the A1 no-fold-floor guardrail
    # (no code path asserts fold >= anything derived from α/MDF) inspectable at a
    # glance. Because the choice is invisible downstream, it is pinned
    # STRUCTURALLY on the raw merits here, never behaviourally.
    #
    # THE FOLD GATE IS PART OF THE MECHANISM, not a shortcut. This region sits at
    # FUNCTION-BODY indentation — the common path shared with unopened
    # (CHECK+BET) and matched-with-option (CHECK+RAISE) nodes — which is why
    # N-LOGIT below re-guards with its own `ActionType.FOLD in by_kind`. Without
    # the gate this would scale the RAISE entry on check-raise shapes, where
    # there is no fold leg for the freed mass to reach (ledger R-7).
    #
    # SCOPE — see `_LINE_SCOPE_BUCKETS`. One consequence is worth stating because
    # rev 1 got it backwards (ledger R-6): for EVERY in-scope bucket,
    # `made = _RUNG[bucket] >= _RUNG[OVERPAIR_TPTK]` is False (in-scope rungs are
    # 0-3, the threshold is 4) and `drawing` is False, so `value_commit` above is
    # ALWAYS False on an in-scope cell. `_commit_transform` and the B5b draw damp
    # therefore can NEVER co-occur with this mechanism. It is scoped AWAY from
    # SPR-committed nodes — not inert on them, which is a different (and untested,
    # because untestable) claim.
    #
    # ORDER — coded BEFORE the N-LOGIT raise scale below, and the order does not
    # matter: both are scalar multiplies on entries ahead of the single
    # normalization, so the final vector is (F, C·line_mult, R·rscale·line_mult)
    # either way and `line_mult` cancels out of P(raise | continue). N-LOGIT's
    # orthogonality survives this damp and this damp's raise-neutrality survives
    # N-LOGIT.
    #
    # No street term lives here on purpose: `line = 0` on the flop is a property
    # of the SIGNAL's derivation (its run loop over preceding postflop streets is
    # empty on the flop), and adding a street check inside the sampler would
    # reintroduce the `street -> scalar` term the roadmap forbids (ledger R-11 /
    # R-15). The flat kwarg stays honest; the guarantee lives with the derivation.
    #
    # The range guard is not dead code, for `continue_ref`'s reason: validation
    # cannot protect λ because `model_copy(update=...)` bypasses it and the suite
    # uses that idiom routinely. Like that guard it is checked BEFORE the
    # facing-node test, so a corrupted lever fails at the persona's first decision
    # rather than at its first facing node.
    #
    # Adds no rng call: the ACTION draw stays the first `rng.choices` consumer
    # (the capture rngs in range_estimate and the tests key on that ordering).
    # Lever absent, or line = 0, and `entries` is not rebuilt at all — the
    # un-opted path is byte-identical, not merely equal.
    sens = pf.line_sensitivity
    if sens is not None:
        if not _LINE_SENSITIVITY_MIN <= sens <= _LINE_SENSITIVITY_MAX:
            raise ValueError(
                f"persona pack {pack.id!r} has line_sensitivity={sens!r}, outside "
                f"the safe range [{_LINE_SENSITIVITY_MIN}, {_LINE_SENSITIVITY_MAX}]"
            )
        if (
            aggressor_bet_prev_street
            and ActionType.FOLD in by_kind
            and bucket in _LINE_SCOPE_BUCKETS
            and draw is DrawCategory.NONE
        ):
            line_mult = math.exp(-_LINE_DELTA * sens)
            entries = _line_scaled(entries, line_mult)

    # N-LOGIT: nested-logit routing on the facing node.
    #
    # `looseness` multiplies the CALL merit only (assigned from
    # `pf.call_looseness`/`pf.stickiness` near the top of this function), so
    # mass taken off CALL
    # is shared out to FOLD *and* RAISE in proportion to their merits — which
    # on an aggressive persona lands mostly on RAISE. Measured at HEAD, halving
    # each pack's effective looseness moved raise-share the WRONG way for every
    # persona (+0.17; roadmap R10-4). Scaling the RAISE merit by
    # `looseness / continue_ref` gives
    #     P(raise | continue) = (R0·L/ref) / (C0·L + R0·L/ref)
    #                         = (R0/ref) / (C0 + R0/ref)
    # in which L CANCELS: the calling lever now controls WHETHER the bot
    # continues, the raise-side calibration controls HOW, and mass freed from
    # CALL routes to FOLD. This is the FALL-THROUGH branch below (every draw
    # NONE/WEAK cell, plus a STRONG draw whose dial already clears the floor),
    # and it keeps the ORIGINAL literal `looseness / ref` expression —
    # untouched by N-DRAWLOOSE.
    #
    # N-DRAWLOOSE COUPLING — STRONG draws at a dial BELOW the floor only (the
    # call-merit branch above and the branch below share one predicate,
    # `draw is STRONG and looseness < 1.0`). Flooring the draw bonus at
    # `max(looseness, 1.0)` makes CALL no longer proportional to the dial, so
    # the literal `looseness / ref` above would stop cancelling L and the
    # guarantee would break on those cells. `rscale` instead reads
    # `C(L) / (C0·ref)` — the LIVE call merit over the UNFLOORED merit at the
    # frozen anchor, C0 = call_base + _DRAW_CALL_BONUS[draw] — which keeps
    #     P(raise | continue) = R0·rscale / (C(L) + R0·rscale) = R0 / (C0·ref + R0)
    # independent of L for ANY call shape, not only a proportional one. On the
    # fall-through (draw NONE/WEAK, or a dial already >= 1.0) `C(L) = C0·L` and
    # the literal gives (R0/ref) / (C0 + R0/ref) = R0 / (C0·ref + R0) — THE SAME
    # VALUE. The guarantee is preserved everywhere and is continuous across
    # L = 1, so a lever sweep that crosses the floor sees no step (G1).
    #
    # WHY THE DIVISOR IS UNFLOORED (fan-in review, defect A). It used to carry
    # the same floor as the live merit, so the floor's growth cancelled out of
    # `rscale` and every chip the floor freed from FOLD landed on CALL — an
    # aggressive persona stopped semi-bluff RAISING the very draws the floor
    # exists to keep in (lag's P(raise) at the D1 trace node fell 0.4718 →
    # 0.3884, maniac 0.6099 → 0.5264, tag 0.3891 → 0.3216). Against the
    # UNFLOORED anchor, RAISE_new / RAISE_base = rscale / (L/ref) = C(L) / (C0·L)
    # — exactly the factor by which CALL grew. FOLD loses mass; CALL and RAISE
    # both gain it in their ORIGINAL proportion, which is why P(raise | continue)
    # on a strong draw now matches the base engine b0a6a4e persona for persona.
    #
    # The divisor is the FROZEN authored anchor, NEVER the live lever, on
    # EITHER branch. Rev 1 of this slice (N-LOGIT's own rev 1, a different
    # slice from N-DRAWLOOSE) divided the raise leg by the live lever and
    # multiplied the defend pair by the same live lever; the two cancelled
    # exactly, so the mechanism was a measured no-op that still passed 8 of
    # its 10 gates (ledger R-1). If `continue_ref` is ever re-synchronised
    # with `call_looseness`, `rscale` collapses to 1.0 forever on BOTH
    # branches and this feature silently disappears — which is why the pack
    # comments call it frozen and why a lifecycle test (G9) pins that it does
    # not move under a refit.
    #
    # While the lever sits at its anchor, `looseness == ref`, `rscale` is
    # EXACTLY 1.0 (float division of equal values) on the fall-through branch
    # and the opted-in path is bit-identical to the un-opted one. That
    # bit-exactness is load-bearing: rev 2 applied a divide-then-multiply pair
    # whose 1-ulp residue broke 6 of the 23 frozen exact-equality vectors in
    # tests/test_price_tail.py (ledger R2-1).
    #
    # THE ONE PLACE THAT PROPERTY NO LONGER HOLDS, disclosed and owner-accepted:
    # a STRONG draw at a persona whose anchor is itself below the floor
    # (`ref < 1`). There the coupled branch is taken even at the anchor, and
    # `rscale = C(ref) / (C0·ref)` is > 1 rather than exactly 1 — that IS the
    # mechanism (the raise leg has to receive the floor's growth; see above),
    # not a rounding artifact. Those 23 frozen vectors are unaffected because
    # every one of them is a `DrawCategory.NONE` cell, which takes the
    # fall-through branch; that was re-verified by classifying each vector's
    # (hole, board) through `strength_bucket` rather than assumed.
    #
    # TWO REACH CHANGES, both disclosed (build review, ledger B-9 / B-10) and
    # both gated so they cannot move silently. They are mirror images:
    #  - GAINED reach, river polar-bluff cell: `call_merit` is hard-zeroed there
    #    (the `if bluff_cell and street is Street.RIVER` branch above — named,
    #    not line-numbered, because the anchor that used to sit here went stale
    #    twice in one slice), so RAISE is the only continue and the lever moves the
    #    bluff-raise rate, which at HEAD it could not. Largest on ACE_HIGH at a
    #    small faced price (lag: P(raise) 0.104 / 0.318 / 0.651 over ×0.25/×1/×4
    #    against a flat HEAD 0.318). G4 pins it.
    #  - LOST reach, SPR-committed nodes: `_commit_transform` zeroes the FOLD
    #    merit while FOLD stays legal, so the vector is (0, C₀·L, 3·R₀·L/ref) and
    #    L cancels out of the WHOLE distribution — `call_looseness` is inert
    #    there, where at HEAD it was the dominant lever. That is the same
    #    orthogonality property with no fold leg left to absorb the change, but
    #    it does mean a future looseness fit has no reach over committed nodes.
    #    G-COMMIT pins it.
    #
    # The range guard is not dead code: model validation cannot protect this
    # division because `model_copy(update=...)` bypasses it, and the suite uses
    # that idiom routinely (ledger R2-5). NaN fails both comparisons and so
    # lands in the same branch as an out-of-range anchor. It is checked BEFORE
    # the facing-node test, not inside it, so a corrupted anchor fails at the
    # persona's first decision rather than at its first facing node.
    ref = pf.continue_ref
    if ref is not None:
        if not _CONTINUE_REF_MIN <= ref <= _CONTINUE_REF_MAX:
            raise ValueError(
                f"persona pack {pack.id!r} has continue_ref={ref!r}, outside the "
                f"safe range [{_CONTINUE_REF_MIN}, {_CONTINUE_REF_MAX}]"
            )
        if ActionType.FOLD in by_kind:
            # `_c_now` is the LIVE, post-damp CALL entry read out of `entries`,
            # never the pre-damp `call_merit` local. On a STRONG draw below the
            # floor that is what lets a downstream rewrite of CALL (the
            # SPR-commit block or the B5b damp above) still hand RAISE its
            # correct share: `rscale` follows the value CALL was rewritten to,
            # not the value it started at. G-COMMIT (in the test file) CANNOT
            # exercise this on a committed node — its cell is a pocket pair
            # with no draw, so it takes the non-STRONG path — so the property
            # is pinned instead by G1's orthogonality sweep, whose grid
            # includes STRONG-draw cells at an SPR that commits every persona;
            # that sweep would go red if `_c_now` stopped tracking the
            # post-commit CALL value. This silently requires this N-LOGIT block
            # to stay BELOW the commit block (the `if stack_bb / pot_bb <=
            # pf.spr_commit:` block above) — reordering them breaks the
            # guarantee with no test naming the dependency (`N-DRAWORDER` is
            # filed for a pin). It also depends on R9-DEFENCE-a's line damp
            # never reaching a STRONG-draw node: that damp only fires on `draw
            # is DrawCategory.NONE` (the `line_sensitivity` block above), so it
            # cannot contaminate `_c_now` today — but if that gate is ever
            # widened to draws, `line_mult` would already be baked into
            # `_c_now` and RAISE would receive it a second time through
            # `rscale`.
            if draw is DrawCategory.STRONG and looseness < 1.0 and _call_merit_at_ref > 0.0:
                _c_now = next((m for a, m in entries if a is ActionType.CALL), 0.0)
                rscale = _c_now / _call_merit_at_ref
            else:
                rscale = looseness / ref
            entries = [(a, m * rscale) if a is ActionType.RAISE else (a, m) for a, m in entries]

    # Normalize (rule 1, pinned): clamp >= 0, divide by sum; sum 0 fallback.
    weights = [max(m, 0.0) for _, m in entries]
    total = sum(weights)
    if total <= 0.0:
        fallback = ActionType.CHECK if ActionType.CHECK in by_kind else ActionType.FOLD
        return Decision(action=fallback)
    action = rng.choices([a for a, _ in entries], weights=[w / total for w in weights], k=1)[0]

    if action not in (ActionType.BET, ActionType.RAISE):
        return Decision(action=action)

    # Sizing draw — independent of bucket (rule 3): the distribution is the
    # persona-authored one for every strength class. F2 stage 2 (see the
    # bluff_mass comment above): a pure-air bluff bet tilts the weights by
    # the bucket factor, completing the joint law w(s)·bluff_mass·factor(s).
    fracs = [(float(k), w) for k, w in sizing_dist.items()]
    if bluff_cell:
        fracs = [(fr, w * _bluff_size_factor(fr)) for fr, w in fracs]
    f = rng.choices([fr for fr, _ in fracs], weights=[w for _, w in fracs], k=1)[0]
    to_call = by_kind[ActionType.CALL].min_bb or 0.0 if ActionType.CALL in by_kind else 0.0
    size = pot_fraction_to_bb(
        f, pot_bb, action=action, current_bet_to=current_bet_to, to_call=to_call
    )
    bracket = by_kind[action]
    size = min(max(round(size, 2), bracket.min_bb), bracket.max_bb)
    return Decision(action=action, size_bb=size)
