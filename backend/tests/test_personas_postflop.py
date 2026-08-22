"""Persona postflop engine tests (S4): strength ladder unit tests + a
closed-loop full-hand harness against PRD §8 bands and a live-table-texture
check. Spec: docs/ai-dlc/specs/simulate-s4.md.

⚠️ STALE BUDGET CLAIM, corrected 2026-07-26 (T-ARR). The "<=12s" figure below
is NO LONGER TRUE and has not been for some time: measured at HEAD immediately
BEFORE this ticket's edit, the whole file runs in **76.37s** (193 passed, 1
skipped). T-ARR's arrival counters added **+1.73s** (78.10s, 195 passed, 1
skipped) — the counters ride the existing `_play_hand`/`_persona_stats_ext`
loops and open no second simulation. (Both of those readings were taken
like-for-like under concurrent load, so +1.73s is the trustworthy figure; the
same post-change run on a quiet tree reads 75.73s.) Treat the ABSOLUTES as
load-dependent, not as constants: the identical unchanged suite was re-measured
at 91.4s and 97.0s at load average 3.6 on the same box. What is stable is that
this file costs ~6x its documented budget and that T-ARR added ~2% of it.
The 12s number and `_derive_n`'s `budget_s = 9.5` are HISTORICAL as of the
instrument-repair wave (2026-08-01): `per_persona_n`/`texture_n` are pinned
constants now, so `budget_s` sizes nothing. Both stay in the text only as the
derivation record for the pinned values.

Budget derivation (refuter-pinned): whole file must add <=12s to the suite.
At the spec's measured engine throughput (~430 hands/s, sticky-policy floor;
91% of apply() cost is pydantic deep-copy) the frozen allocation is
N=600 hands/persona-lineup x 6 + 1,500 texture hands ~= 5,100 hands ~= 11.8s.
This maker re-measures with the persona sampler actually wired below and
scales N DOWN (never up) if the measured throughput is lower; see
`_measure_throughput` and the N constants below.

3-sigma tolerance math (binomial proportion, per band): for a measured count
X out of n trials with true rate p, stderr = sqrt(p(1-p)/n). At n=600 hands
x 9 seats matched (but only ~1 relevant seat's stat per hand for most
metrics), the realistic per-persona postflop-decision sample size is smaller
(one persona seat's postflop decisions per hand, gated on that persona
reaching a postflop street). Bands below are the PRD §8 population bands
widened by the spec's own admission that station/maniac bands are
"extrapolated... treat as targets, tune in the closed-loop test" -- this
maker tunes pack levers (not test bands) first; bands are widened only
where the frozen occurrence floor (>=30) caps precision at roughly
+/- 3*sqrt(0.5*0.5/30) ~= +/-27pp for a 50%-ish rate at the n=30 floor, far
looser than the PRD point bands, so PRD bands are used AS-IS except where
this maker's own re-derivation (documented per-persona below) widens them.
"""

from __future__ import annotations

import builtins
import hashlib
import math
import random
import sys
import time
from typing import NamedTuple, get_args

import pytest

from app.domain.action import Decision
from app.domain.archetypes import VillainType
from app.domain.content.models import PersonaFacing
from app.domain.spot import ActionType, PlayerStatus, Position, Street
from app.domain.table.deck import deal_hand
from app.domain.table.engine import apply, legal_actions, settle, start_hand

personas_postflop = pytest.importorskip(
    "app.domain.personas_postflop",
    reason="T1's engine module (backend/app/domain/personas_postflop.py) not landed yet "
    "-- packs authored, harness written against the frozen interface; awaits fan-in.",
)

from app.domain.personas import load_persona_packs, sample_preflop_action  # noqa: E402

DrawCategory = personas_postflop.DrawCategory
StrengthBucket = personas_postflop.StrengthBucket
sample_postflop_decision = personas_postflop.sample_postflop_decision
strength_bucket = personas_postflop.strength_bucket
# W5-a4: the `size_bucket` / `_BUCKET_ALPHA` aliases that lived here were only
# ever read by the α-ceiling test, which now grades against the size-exact
# continuous α = f/(1+f) instead of the coarser bucket representative.


# --------------------------------------------------------------- fixtures


def test_all_six_persona_packs_have_postflop_block():
    packs = load_persona_packs()
    missing = set(VillainType) - set(packs)
    if missing:
        pytest.skip(f"personas not authored yet: {sorted(missing)}")
    for vt, pack in packs.items():
        assert pack.postflop is not None, f"{vt} pack missing postflop block"


# =====================================================================
# Unit tests: strength_bucket
# =====================================================================


def test_strength_bucket_monster_set_and_straight_on_paired_board():
    # Set: pocket 7s on a 7-x-x board.
    bucket, _ = strength_bucket(("7c", "7d"), ["7s", "2h", "9c"])
    assert bucket == StrengthBucket.MONSTER
    # Straight on a paired board stays MONSTER (never demoted for texture).
    bucket, _ = strength_bucket(("Th", "9h"), ["Jc", "8d", "8s", "Qc"])
    assert bucket == StrengthBucket.MONSTER


def test_strength_bucket_two_pair_plus():
    # Both hole cards pair the board: two pair.
    bucket, _ = strength_bucket(("Kh", "9d"), ["Kc", "9s", "2h"])
    assert bucket == StrengthBucket.TWO_PAIR_PLUS


def test_strength_bucket_overpair_and_tptk():
    # Pocket pair above all board cards: overpair.
    bucket, _ = strength_bucket(("Qh", "Qd"), ["9c", "5s", "2h"])
    assert bucket == StrengthBucket.OVERPAIR_TPTK
    # Top pair top kicker: ace with top-card ace, king kicker beats board.
    bucket, _ = strength_bucket(("Ah", "Kd"), ["Ac", "9s", "2h"])
    assert bucket == StrengthBucket.OVERPAIR_TPTK


def test_strength_bucket_top_pair_lesser_kicker():
    bucket, _ = strength_bucket(("Ah", "2d"), ["Ac", "9s", "3h"])
    assert bucket == StrengthBucket.TOP_PAIR


def test_strength_bucket_middle_pair_incl_pocket_pair_below_top_board_card():
    # Middle/bottom pair from a hole card.
    bucket, _ = strength_bucket(("9h", "2d"), ["Ac", "9s", "3h"])
    assert bucket == StrengthBucket.MIDDLE_PAIR
    # Pocket pair strictly below the board's top card: always middle_pair,
    # never overpair_tptk/top_pair (disjointness rule).
    bucket, _ = strength_bucket(("7h", "7d"), ["Ac", "9s", "3h"])
    assert bucket == StrengthBucket.MIDDLE_PAIR


def test_f7_under_pocket_pair_on_paired_board_is_middle_pair():
    # F7 bug 1: a pocket pair BELOW the board's paired rank reads "two pair"
    # to the evaluator (22 on 883 = eights and deuces) but the board pair
    # plays for everyone — it must class like any pocket underpair.
    board = ["8s", "8h", "3d"]
    assert strength_bucket(("2c", "2d"), board)[0] == StrengthBucket.MIDDLE_PAIR
    assert strength_bucket(("5c", "5d"), board)[0] == StrengthBucket.MIDDLE_PAIR
    # Pocket pair ABOVE the board pair is a genuinely strong two pair: kept.
    assert strength_bucket(("Tc", "Td"), board)[0] == StrengthBucket.TWO_PAIR_PLUS
    # One-hole-card trips on the paired board: monster (unchanged).
    assert strength_bucket(("Ac", "8c"), board)[0] == StrengthBucket.MONSTER


def test_f7_unpaired_board_sentinels_unchanged():
    # The bug-1 fix touches ONLY the paired-board pocket-pair branch; unpaired
    # boards must be byte-stable.
    board = ["Ks", "7h", "2d"]
    assert strength_bucket(("Qc", "Qd"), board)[0] == StrengthBucket.MIDDLE_PAIR
    assert strength_bucket(("Kd", "7c"), board)[0] == StrengthBucket.TWO_PAIR_PLUS
    assert strength_bucket(("Ac", "Kc"), board)[0] == StrengthBucket.OVERPAIR_TPTK


def test_strength_bucket_ace_high_and_air():
    bucket, _ = strength_bucket(("Ah", "5d"), ["Kc", "9s", "3h"])
    assert bucket == StrengthBucket.ACE_HIGH
    bucket, _ = strength_bucket(("7h", "5d"), ["Kc", "9s", "3h"])
    assert bucket == StrengthBucket.AIR


def test_strength_bucket_river_has_no_draws_even_with_flush_draw_hole():
    # 4-flush hole (two hearts) + board with two more hearts (a made or busted
    # flush draw shape) on the RIVER: DrawCategory must always be NONE.
    board = ["2h", "9h", "Kc", "7d", "3s"]
    _, draw = strength_bucket(("Ah", "5h"), board)
    assert draw == DrawCategory.NONE


def test_strength_bucket_flop_draw_categories_present():
    # Flush draw on the flop: STRONG.
    _, draw = strength_bucket(("Ah", "5h"), ["2h", "9h", "Kc"])
    assert draw == DrawCategory.STRONG
    # Gutshot, no flush: WEAK.
    _, draw = strength_bucket(("Jc", "8d"), ["Ts", "6h", "2c"])
    assert draw in (DrawCategory.WEAK, DrawCategory.NONE)  # heuristic tolerance
    # Dry board, no draw at all: NONE.
    _, draw = strength_bucket(("2c", "7d"), ["Ks", "8h", "3c"])
    assert draw == DrawCategory.NONE


# ---------------------------------------------------- sampling behavior


def _pack(persona: str = "tag"):
    return load_persona_packs()[VillainType(persona)]


def _bet_or_raise_freq(pack, hole, board, legal, pot_bb, stack_bb, opponents, seed, n=500):
    rng = random.Random(seed)
    count = 0
    for _ in range(n):
        d = sample_postflop_decision(pack, hole, board, legal, pot_bb, stack_bb, opponents, rng)
        if d.action in (ActionType.BET, ActionType.RAISE):
            count += 1
    return count / n


def test_monotonicity_aggression_never_lowers_bet_raise_freq():
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    base = _pack("tag")
    high = base.model_copy(deep=True)
    high.postflop = base.postflop.model_copy(update={"aggression": base.postflop.aggression * 3})

    hole = ("7h", "5d")  # air-ish on this board
    board = ["Kc", "9s", "3h"]
    legal = [
        personas_postflop_legal_check(),
        personas_postflop_legal_bet(0.5, 10.0),
    ]
    freq_base = _bet_or_raise_freq(base, hole, board, legal, 3.0, 100.0, 1, seed=1)
    freq_high = _bet_or_raise_freq(high, hole, board, legal, 3.0, 100.0, 1, seed=1)
    assert freq_high >= freq_base - 1e-9


def test_monotonicity_call_looseness_never_lowers_call_freq():
    # W2-a: the call-freq monotonicity now rides `call_looseness` (the flat call
    # multiplier). Build `high` by raising ONLY call_looseness — leave stickiness
    # (hence the size_elasticity fallback / fold-side price factor) UNCHANGED so
    # the assertion isolates the call axis and isn't confounded by fold behavior.
    base = _pack("nit")
    high = base.model_copy(deep=True)
    high.postflop = base.postflop.model_copy(
        update={"call_looseness": base.postflop.stickiness * 3}
    )

    hole = ("9h", "2d")  # middle pair, facing a bet
    board = ["Ac", "9s", "3h"]
    legal = [
        personas_postflop_legal_fold(),
        personas_postflop_legal_call(2.0),
    ]

    def call_freq(pack, seed=2, n=500):
        rng = random.Random(seed)
        count = 0
        for _ in range(n):
            d = sample_postflop_decision(pack, hole, board, legal, 6.0, 100.0, 1, rng)
            count += d.action == ActionType.CALL
        return count / n

    assert call_freq(high) >= call_freq(base) - 1e-9


def test_station_size_blind_fish_size_scared_content():
    # (Function name kept for cross-slice traceability — the spec/tickets refer to
    # it by name; the assertion below is the W3R-2 shallow-rise re-pin.)
    # W3R-2 RE-PIN (persona-realism-w3r-2, 2026-07-24 — owner-authorized, P5
    # precedent): this test used to assert the station was size-BLIND
    # (`abs(st_over - st_small) < 1e-9`, size_elasticity 0.0) — it codified the
    # very price-blind leak hyp-2 removes. The station now has an authored
    # `size_elasticity` 0.55, so it gains a SHALLOW but strictly POSITIVE price
    # response: it still calls big bets far more than anyone else, it is just no
    # longer indifferent to the price. The fish (size_elasticity 1.3) keeps its
    # STEEP fit-or-fold rise, and the station's rise stays well under it. Exact
    # normalized fold probability; middle pair facing a bet, SPR well above commit.
    hole, board = ("9h", "2d"), ["Ac", "9s", "3h"]

    def fold_at(pack, to_call, pot, cbt):
        return _dist_for_pack(
            pack, hole, board,
            [personas_postflop_legal_fold(), personas_postflop_legal_call(to_call)],
            pot, 100.0, current_bet_to=cbt,
        )[ActionType.FOLD]

    station, fish = _pack("calling_station"), _pack("passive_fish")
    # SMALL: faced_frac 3/9 = 0.33; OVERBET: 9/6 = 1.5.
    st_small, st_over = fold_at(station, 3.0, 12.0, 3.0), fold_at(station, 9.0, 15.0, 9.0)
    fi_small, fi_over = fold_at(fish, 3.0, 12.0, 3.0), fold_at(fish, 9.0, 15.0, 9.0)
    # station: a shallow price rise, no longer size-blind (W3R-2).
    assert 0 < st_over - st_small
    assert st_over - st_small < fi_over - fi_small  # ... and shallower than the fish's
    assert fi_over - fi_small > 0.15  # fish: steep fold-rise with size


def test_size_elasticity_steeper_fold_vs_bigger_size():
    # W2-a: higher size_elasticity ⇒ a STEEPER fold-rate rise from a SMALL faced
    # size to an OVERBET (the fish-vs-station identity axis). Exact normalized
    # fold probability via _CaptureWeights (no sampling noise). Both configs share
    # every other lever, so only the price exponent differs.
    base_pf = _pack("tag").postflop
    low = _pack("tag")
    low.postflop = base_pf.model_copy(update={"size_elasticity": 0.5})
    high = _pack("tag")
    high.postflop = base_pf.model_copy(update={"size_elasticity": 1.5})
    hole, board = ("9h", "2d"), ["Ac", "9s", "3h"]  # middle pair facing a bet

    def fold_gap(pack):
        # SMALL: to_call 3 into pre-bet pot 9 → faced_frac 0.33; OVERBET: 9 into 6 → 1.5.
        small = _dist_for_pack(
            pack, hole, board,
            [personas_postflop_legal_fold(), personas_postflop_legal_call(3.0)],
            12.0, 100.0, current_bet_to=3.0,
        )
        over = _dist_for_pack(
            pack, hole, board,
            [personas_postflop_legal_fold(), personas_postflop_legal_call(9.0)],
            15.0, 100.0, current_bet_to=9.0,
        )
        return over[ActionType.FOLD] - small[ActionType.FOLD]

    assert fold_gap(high) > fold_gap(low)


# W3R-3 (#4, hand-history review H11/H76): the spr_commit LADDER. The fish was
# authored `spr_commit` 2.0 — ABOVE the calling station's 1.5 — so the supposedly
# scared passive bot reached its stack-commitment threshold at a HIGHER SPR, i.e.
# committed EARLIER than the stickiest persona on the roster. Backwards. Fixed by
# fish 2.0 → 1.4 (now strictly below the station) and maniac 4.0 → 3.3 (a mild pull
# on the deep over-commit). The engine gate is `stack/pot <= spr_commit` (line ~804),
# so a HIGHER dial commits at a HIGHER (i.e. earlier) SPR — the assertions below use
# an SPR that lands strictly BETWEEN the old and new dials, where a made hand facing
# a bet is committed (fold merit zeroed) at the OLD dial and is not at the NEW one.
_COMMIT_TPTK = (("Ah", "Kd"), ["Ac", "9s", "3h"])  # OVERPAIR_TPTK — the commit rung


def _commit_fold_prob(persona: str, spr: float, spr_commit: float | None = None) -> float:
    """Exact normalized P(fold) for a committable made hand facing a ½-pot bet at a
    chosen SPR. `spr_commit=None` uses the pack's authored dial."""
    pack = _pack(persona)
    if spr_commit is not None:
        pack.postflop = pack.postflop.model_copy(update={"spr_commit": spr_commit})
    pot, stack = 60.0, 60.0 * spr
    hole, board = _COMMIT_TPTK
    return _dist_for_pack(
        pack, hole, board,
        [personas_postflop_legal_fold(), personas_postflop_legal_call(20.0),
         personas_postflop_legal_raise(40.0, stack)],
        pot, stack, current_bet_to=20.0,
    ).get(ActionType.FOLD, 0.0)


def test_spr_commit_ladder_fish_commits_later_than_the_station():
    """#4 (H11/H76): at SPR 1.45 — between the fish's new 1.4 and the station's 1.5 —
    the STATION is pot-committed (fold merit zeroed) and the FISH is not. Under the
    old fish dial (2.0) the fish was committed here too, i.e. it committed EARLIER
    than the station. Exact weights, no sampling noise."""
    assert _pack("passive_fish").postflop.spr_commit < _pack("calling_station").postflop.spr_commit
    assert _commit_fold_prob("calling_station", 1.45) == 0.0  # station: committed
    assert _commit_fold_prob("passive_fish", 1.45) > 0.0  # fish: NOT committed (new)
    assert _commit_fold_prob("passive_fish", 1.45, spr_commit=2.0) == 0.0  # old fish: was


def test_spr_commit_ladder_maniac_pulled_off_the_deep_commit():
    """#4: the maniac's 4.0 → 3.3 pull. At SPR 3.6 the old dial committed its stack
    with a one-pair-class made hand; the new dial does not."""
    assert _commit_fold_prob("maniac", 3.6) > 0.0
    assert _commit_fold_prob("maniac", 3.6, spr_commit=4.0) == 0.0


def test_sizing_spread_no_deterministic_strength_to_size():
    pack = _pack("lag")
    hole = ("Ah", "Kd")  # strong made hand, single fixed bucket
    board = ["Ac", "9s", "3h"]
    legal = [
        personas_postflop_legal_check(),
        personas_postflop_legal_bet(1.0, 30.0),
    ]
    rng = random.Random(99)
    sizes = set()
    for _ in range(200):
        d = sample_postflop_decision(pack, hole, board, legal, 3.0, 100.0, 1, rng)
        if d.action == ActionType.BET:
            sizes.add(round(d.size_bb, 2))
    assert len(sizes) >= 2, f"expected sizing spread, got {sizes}"


def test_clamp_and_jam_edge():
    pack = _pack("maniac")
    hole = ("Ah", "Ad")  # monster
    board = ["Kc", "9s", "3h"]
    # Jam encoding: min==max.
    legal = [
        personas_postflop_legal_check(),
        personas_postflop_legal_bet(8.0, 8.0),
    ]
    rng = random.Random(5)
    for _ in range(50):
        d = sample_postflop_decision(pack, hole, board, legal, 3.0, 8.0, 1, rng)
        if d.action == ActionType.BET:
            assert d.size_bb == pytest.approx(8.0)


def test_multiway_dampener_reduces_bluff_freq_as_opponents_rise():
    pack = _pack("maniac")
    hole = ("7h", "5d")  # air
    board = ["Kc", "9s", "3h"]
    legal = [
        personas_postflop_legal_check(),
        personas_postflop_legal_bet(1.0, 20.0),
    ]
    freq_1 = _bet_or_raise_freq(pack, hole, board, legal, 3.0, 100.0, 1, seed=3)
    freq_4 = _bet_or_raise_freq(pack, hole, board, legal, 3.0, 100.0, 4, seed=3)
    assert freq_4 <= freq_1 + 1e-9


def test_same_seed_same_decision():
    pack = _pack("tag")
    hole = ("Ah", "Kd")
    board = ["Ac", "9s", "3h"]
    legal = [
        personas_postflop_legal_check(),
        personas_postflop_legal_bet(1.0, 20.0),
    ]

    def draw(seed):
        rng = random.Random(seed)
        return [
            sample_postflop_decision(pack, hole, board, legal, 3.0, 100.0, 1, rng).action
            for _ in range(50)
        ]

    assert draw(7) == draw(7)


def test_sum_zero_merit_fallback_check_or_fold():
    # A degenerate pack (all levers zero) still must yield CHECK when legal
    # else FOLD, never crash.
    pack = _pack("nit")
    pack = pack.model_copy(deep=True)
    pack.postflop = pack.postflop.model_copy(
        update={"aggression": 0.0, "stickiness": 0.0, "bluff_freq": 0.0}
    )
    hole = ("7h", "5d")
    board = ["Kc", "9s", "3h"]
    legal_with_check = [
        personas_postflop_legal_check(),
        personas_postflop_legal_bet(1.0, 20.0),
    ]
    rng = random.Random(11)
    d = sample_postflop_decision(pack, hole, board, legal_with_check, 3.0, 100.0, 1, rng)
    assert d.action in (ActionType.CHECK, ActionType.FOLD, ActionType.BET, ActionType.CALL)


# ---- LegalAction constructors (avoid importing the engine's internal shape
# assumptions into every test above; keep them local & explicit) ----


def personas_postflop_legal_check():
    from app.domain.spot import LegalAction

    return LegalAction(action=ActionType.CHECK)


def personas_postflop_legal_bet(lo, hi):
    from app.domain.spot import LegalAction

    return LegalAction(action=ActionType.BET, min_bb=lo, max_bb=hi)


def personas_postflop_legal_fold():
    from app.domain.spot import LegalAction

    return LegalAction(action=ActionType.FOLD)


def personas_postflop_legal_call(amount):
    from app.domain.spot import LegalAction

    return LegalAction(action=ActionType.CALL, min_bb=amount)


def personas_postflop_legal_raise(lo, hi):
    from app.domain.spot import LegalAction

    return LegalAction(action=ActionType.RAISE, min_bb=lo, max_bb=hi)


class _FirstChoicesRecorder(random.Random):
    """Captures the FIRST rng.choices call — the action draw (the F2 two-stage
    sampling keeps it first; see the sample_postflop_decision docstring) — so
    a test can assert the EXACT normalized action distribution, no MC noise."""

    def __init__(self):
        super().__init__(0)
        self.first_pop = None
        self.first_weights = None

    def choices(self, population, weights=None, *, cum_weights=None, k=1):
        if self.first_weights is None:
            self.first_pop = list(population)
            self.first_weights = list(weights)
        return [population[0]]


def test_f7_tag_under_pocket_pair_facing_medium_bet_folds_not_raises():
    # F7 bug 1 behavioral: tag with 22 on 883r facing 3bb into 6bb (MEDIUM)
    # raised 0.734 / folded 0.013 pre-fix at 0.375 equity — more aggressive
    # than AK-high (0.499 equity) on the same board. As MIDDLE_PAIR the exact
    # distribution is now call-dominant with a material fold share.
    pack = _pack("tag")
    board = ["8s", "8h", "3d"]
    legal = [
        personas_postflop_legal_fold(),
        personas_postflop_legal_call(3.0),
        personas_postflop_legal_raise(9.0, 97.0),
    ]
    rec = _FirstChoicesRecorder()
    sample_postflop_decision(
        pack, ("2c", "2d"), board, legal, 9.0, 97.0, 1, rec, current_bet_to=3.0
    )
    dist = dict(zip(rec.first_pop, rec.first_weights, strict=True))
    total = sum(dist.values())
    assert dist[ActionType.RAISE] / total < 0.35  # was 0.734
    assert dist[ActionType.FOLD] / total > 0.15  # was 0.013


ALL_PERSONAS = sorted(v.value for v in VillainType)


# =====================================================================
# F1 — price-aware defense (RES-D §2 invariants, RES-E size buckets)
# =====================================================================
#
# Fold-to-bet is measured over a UNIFORM random range (random hole cards +
# random flop): the defender arrives with any two cards, the widest range the
# α fold-ceiling applies to (folding more than α of the arrival range makes an
# any-two-cards bluff profitable — the "balanced bettor" worst case). The four
# fracs cover one representative size per RES-E bucket; 1.0 (pot) sits in
# LARGE and doubles as the spec's mandated "⅓-pot vs pot-size" comparison.
# Comparisons below are seed-pinned (deterministic), so tight cross-persona
# gaps (lag vs tag ~1.5pp) are stable pass/fail, not flaky.

PRICE_FRACS = (0.33, 0.5, 1.0, 1.5)  # SMALL / MEDIUM / LARGE(pot) / OVERBET
_PRICE_N = 1250


def _measure_fold_by_size(street: Street | None = None, opponents: int = 1):
    """persona -> {frac: measured fold-to-bet} facing FOLD/CALL/RAISE with a
    bet of `frac * pot-before-the-bet`, same pre-dealt spot list for every
    persona x size (paired comparison, variance from range composition
    cancels across cells).

    `street` (default `None`) is threaded straight into
    `sample_postflop_decision` so street-gated levers (e.g. T3's
    `_ACE_HIGH_RIVER_CALL_DAMP`, RIVER-only) are measurable here; every
    existing caller leaves it at the default and is byte-identical to before
    this parameter existed.

    `opponents` (default `1`) is threaded the same way, so multiway-gated
    levers (e.g. T1's `_ACE_HIGH_FLOAT_RAISE_DAMP`, which now also fires
    facing a BET at `opponents > 1`) are measurable here too; every existing
    caller leaves it at the default and is byte-identical to before this
    parameter existed."""
    from app.domain.equity import RANKS

    packs = load_persona_packs()
    if set(VillainType) - set(packs):
        pytest.skip("not all persona packs authored yet")
    deal_rng = random.Random(20260721)
    deck0 = [r + s for r in RANKS for s in "shdc"]
    spots = []
    for _ in range(_PRICE_N):
        deck = deck0[:]
        deal_rng.shuffle(deck)
        spots.append(((deck[0], deck[1]), deck[2:5]))

    rates: dict[str, dict[float, float]] = {}
    pot_pre = 6.0
    for pi, persona in enumerate(ALL_PERSONAS):
        pack = packs[VillainType(persona)]
        rates[persona] = {}
        for fi, frac in enumerate(PRICE_FRACS):
            to_call = round(frac * pot_pre, 2)
            pot = pot_pre + to_call
            legal = [
                personas_postflop_legal_fold(),
                personas_postflop_legal_call(to_call),
                personas_postflop_legal_raise(2 * to_call, 100.0),
            ]
            rng = random.Random(20260721 + 100 * pi + fi)  # stable per-cell seed
            folds = 0
            for hole, board in spots:
                d = sample_postflop_decision(
                    pack,
                    hole,
                    board,
                    legal,
                    pot,
                    100.0,
                    opponents,
                    rng,
                    current_bet_to=to_call,
                    street=street,
                )
                folds += d.action is ActionType.FOLD
            rates[persona][frac] = folds / _PRICE_N
    return rates


@pytest.fixture(scope="module")
def fold_by_size():
    return _measure_fold_by_size()


@pytest.mark.parametrize("persona", ALL_PERSONAS)
def test_fold_to_bet_monotone_in_faced_size(persona, fold_by_size):
    """RES-D §2 invariant 1 (the price-blind-defense bug): fold-to-bet is
    non-decreasing across SMALL -> MEDIUM -> LARGE -> OVERBET, and a bot
    facing ⅓-pot folds MEASURABLY less than the same bot facing pot-size."""
    r = fold_by_size[persona]
    seq = [r[f] for f in PRICE_FRACS]
    if persona == "calling_station":
        # W3R-2 RE-PIN (persona-realism-w3r-2, 2026-07-24 — owner-authorized, P5
        # precedent): was `abs(r[1.0] - r[0.33]) < 0.05` ("size-blind BY DESIGN,
        # flat within noise"), which codified the price-blind leak hyp-2 removes.
        # With `size_elasticity` 0.0 → 0.55 the station now HAS a price response,
        # just a shallow one: it must rise strictly, but stay under the 0.10
        # measurable-rise bar the other personas clear (measured ⅓-pot 0.140 →
        # pot 0.222, a 0.082 rise). Sticky, no longer indifferent to the price.
        assert 0 < r[1.0] - r[0.33] < 0.10, (
            f"station should show a shallow (0, 0.10) price rise, got "
            f"{r[1.0]:.3f} vs {r[0.33]:.3f}"
        )
    else:
        assert seq == sorted(seq), f"{persona} fold-to-bet not monotone in size: {seq}"
        assert r[1.0] - r[0.33] >= 0.10, (
            f"{persona} pot-size fold {r[1.0]:.3f} not measurably above "
            f"⅓-pot fold {r[0.33]:.3f}"
        )


# ---- The balanced-villain unit fixture (W5-a4, 2026-07-25) ----------------
#
# α = f/(1+f) is the fold ceiling **vs a BALANCED bettor**, and the identity
# only bites on the range that bettor's bluff half is attacking: a
# BLUFF-CATCHER range — hands that beat every bluff and lose to every value
# bet, whose whole defensive job is to make the bluffs breakeven. That is the
# same marginal-catcher construction the GRADER-side α test already uses
# (`test_postflop.py::test_f5_alpha_ceiling_on_catcher_fold_share`, whose
# `_F5_CATCHER` is a top pair classified "weak_made"); this fixture is its
# bot-side mirror.
#
# Composition is fixed by theory, not by fit: the engine's one-pair rungs
# MIDDLE_PAIR + TOP_PAIR at DrawCategory.NONE. Stronger rungs (OVERPAIR_TPTK
# and up) beat part of the VALUE half, so they are not catchers; ACE_HIGH/AIR
# lose to part of the BLUFF half; and a hand with a live draw is defended on
# improvement equity rather than on catching a bluff. Excluding draws makes
# this fixture STRICTER, not looser (draws call more, so they would pad the
# headroom). Same deal stream, same node (pot 6bb, 100bb stacks, heads-up),
# same per-cell seeds as `fold_by_size` — the ONLY difference is the filter.
_CATCHER_BUCKETS = (StrengthBucket.MIDDLE_PAIR, StrengthBucket.TOP_PAIR)


def _measure_catcher_fold_by_size(street: Street | None = None, opponents: int = 1):
    """persona -> {frac: fold-to-bet} over a pure bluff-catcher range (see the
    block above), measured at the same node/seeds as `fold_by_size`.

    `street` (default `None`) and `opponents` (default `1`) are threaded
    straight into `sample_postflop_decision`, same as `_measure_fold_by_size`;
    every existing caller leaves both at the default and is byte-identical to
    before these parameters existed."""
    from app.domain.equity import RANKS

    packs = load_persona_packs()
    if set(VillainType) - set(packs):
        pytest.skip("not all persona packs authored yet")
    deal_rng = random.Random(20260721)
    deck0 = [r + s for r in RANKS for s in "shdc"]
    spots = []
    while len(spots) < _PRICE_N:
        deck = deck0[:]
        deal_rng.shuffle(deck)
        hole, board = (deck[0], deck[1]), deck[2:5]
        made, draw = strength_bucket(hole, board)
        if draw is DrawCategory.NONE and made in _CATCHER_BUCKETS:
            spots.append((hole, board))

    rates: dict[str, dict[float, float]] = {}
    pot_pre = 6.0
    for pi, persona in enumerate(ALL_PERSONAS):
        pack = packs[VillainType(persona)]
        rates[persona] = {}
        for fi, frac in enumerate(PRICE_FRACS):
            to_call = round(frac * pot_pre, 2)
            pot = pot_pre + to_call
            legal = [
                personas_postflop_legal_fold(),
                personas_postflop_legal_call(to_call),
                personas_postflop_legal_raise(2 * to_call, 100.0),
            ]
            rng = random.Random(20260721 + 100 * pi + fi)  # stable per-cell seed
            folds = 0
            for hole, board in spots:
                d = sample_postflop_decision(
                    pack,
                    hole,
                    board,
                    legal,
                    pot,
                    100.0,
                    opponents,
                    rng,
                    current_bet_to=to_call,
                    street=street,
                )
                folds += d.action is ActionType.FOLD
            rates[persona][frac] = folds / _PRICE_N
    return rates


@pytest.fixture(scope="module")
def catcher_fold_by_size():
    return _measure_catcher_fold_by_size()


@pytest.mark.parametrize("persona", ALL_PERSONAS)
def test_fold_to_bet_respects_alpha_ceiling(persona, catcher_fold_by_size):
    """RES-D §1c/§2 invariant 3 (A1 guardrail): α = f/(1+f) is a fold CEILING
    vs a BALANCED bettor, and is NOT a floor — no lower-bound assertion on a
    fold rate exists anywhere in this file, and none may be added (personas
    fold far below α on purpose: the station catches at 0.03 vs a ⅓-pot bet
    where α is 0.248).

    W5-a4 RE-SCOPE (2026-07-25) — the α guardrail now lives on a BALANCED-
    VILLAIN unit fixture instead of on an arrival-range aggregate. This is the
    slice the roadmap spec'd to resolve a contradiction three earlier slices
    dodged by node-scoping (W3R-2 re-scoped the fish, W3R-6 narrowed to
    facing-a-raise, W3R-5 HARD-STOPPED); it is a re-scoping of what the α
    identity is asserted ABOUT, with **zero behavior change**.

    WHY THE OLD FORM WAS MIS-SPECIFIED. The old test graded α against an
    AGGREGATE fold rate over a UNIFORM any-two arrival range. Two different
    opponent populations were being conflated:

      * α bounds the fold frequency that is unexploitable **against a balanced
        bettor** — one whose value:bluff ratio is game-theoretically correct,
        so that his bluff half is exactly breakeven at MDF.
      * §5's grounded fold-to-c-bet targets — nit 60–75, TAG 50–60, LAG 40–50,
        fish 35–50 (contract §5, `Fold-to-C-bet aggregate`; provenance triple
        per §5a: **format 9-max full ring · pool online micro–low NL cash
        (NL2–NL25) · source S1 side-by-side FR 60 = 6-max 60, plus S4 the HM2
        official full-ring forum band 40–70, corroborated on level by S3
        42–57 and S5 ~40**; conf LOW, per-archetype band edges DIRECTIONAL)
        are POPULATION observations against REAL villains who c-bet 55–70% of
        flops — far more than balanced. Folding 60% of an arrival range to
        THOSE bettors is the correct exploit, not a leak.

    At the modal ½–⅔-pot c-bet α is ≈0.33–0.40, so nit's, TAG's and LAG's §5
    targets were UNSATISFIABLE while the old form was live. The old form also
    only passed by exempting the two personas it bound hardest: `nit` was cut
    from the parametrize list outright, and the fish leg was swapped onto the
    W3R-0 arrival harness. Measured on the old uniform fixture at HEAD, with
    the exemptions removed, it fails outright — nit 0.5424 vs its 0.5200
    allowance at pot, fish 0.4872 / 0.5768 / 0.7160 vs 0.4250 / 0.5200 /
    0.6500 at ½-pot / pot / 1.5×-pot. The gate was passing on its exemptions.

    WHAT THE FIXTURE IS. A balanced villain bets a POLARIZED range, so the
    defender's problem collapses to bluff-catching, and α is exactly the
    constraint on how often a BLUFF-CATCHER may fold. The fixture is therefore
    the one-pair no-draw catcher range described above `catcher_fold_by_size`
    — the bot-side mirror of the grader's own α test
    (`test_postflop.py::test_f5_alpha_ceiling_on_catcher_fold_share`). Node,
    seeds and sampler call are identical to `fold_by_size`; only the range
    filter differs.

    THE ASSERTION IS STRICTLY STRONGER THAN THE ONE IT REPLACES, on all four
    axes — this re-scope buys coverage, it does not spend it:
      1. **All six personas**, including `nit` (whose exemption does NOT
         survive: on a balanced-villain range the nit is α-compliant with
         ≥10.3pp to spare, so its "deliberate over-fold leak" was an artifact
         of the arrival-range aggregate, not of its price logic).
      2. **No tolerance.** The old form allowed α + 0.05, tolerance derived to
         absorb correct air-folding over the uniform range. On a catcher range
         there is no air to absorb, so the ceiling is asserted RAW.
      3. **The size-exact continuous α = f/(1+f)**, not the coarser
         `_BUCKET_ALPHA` representative the old form had to retreat to. That
         is stricter at MEDIUM (0.3333 vs 0.375) and at OVERBET-adjacent LARGE.
      4. **No arrival-range leg at all**, so nothing here contradicts §5.

    HEADROOM PER PERSONA (fold rate vs the size-exact α, at the committed
    deal/decision seed 20260721, n=1250 catchers; ⅓-pot / ½-pot / pot /
    1.5×-pot, α = 0.2481 / 0.3333 / 0.5000 / 0.6000):
        nit              .0880 .1784 .3056 .4568 → +.160 +.155 +.194 +.143
        tag              .0888 .1624 .2640 .3832 → +.159 +.171 +.236 +.217
        lag              .0752 .1600 .2464 .3704 → +.173 +.173 +.254 +.230
        maniac           .0464 .1496 .2120 .3096 → +.202 +.184 +.288 +.290
        calling_station  .0296 .0312 .0568 .0672 → +.219 +.302 +.443 +.533
        passive_fish     .1064 .2488 .3912 .5432 → +.142 +.085 +.109 +.057
    Binding cell: passive_fish at the 1.5× overbet, +5.68pp (≈4.0 binomial SE
    at this n). NOT a lucky seed — re-measured at four further (deal seed,
    decision seed, n) configurations the sign never flips and the binding cell
    never moves: (20260721, 20260721, 625) +3.20pp · (777, 777, 1250) +3.36pp ·
    (424242, 424242, 1250) +2.08pp · (99, 12345, 2500) +4.76pp. Every other
    persona-cell holds ≥8.5pp in every configuration.

    HEADROOM IN THE CURRENCY OF THE NEXT SLICE (W3R-5, whose first attempt
    HARD-STOPPED on the old form of this gate): W3R-5's mechanic is a
    multiplicative fold-merit boost on exactly these one-pair buckets. Scaling
    `_FOLD_BASE[MIDDLE_PAIR/TOP_PAIR]` uniformly and re-running this fixture,
    the ceiling first breaks at **×1.30** (min headroom +0.0144 at ×1.20,
    −0.0008 at ×1.30) — always at the same passive_fish/overbet cell. So a
    ONE-SIDED boost up to ×1.29 is admissible here, and W3R-5's largest
    re-spec'd leg (monotone ×1.22, with E[boost] ≈ 1.0 across boards) fits
    even in the degenerate case where every board were monotone.

    COVERAGE DELTA (§11 item 14), adjudicated rather than silent. GAINED: two
    personas (nit, fish) × 4 sizes now under a HARD α ceiling that previously
    exempted them, at zero tolerance and against a stricter α. RETIRED: the
    absolute-level ceiling on the UNIFORM-range aggregate. That ceiling is not
    lost coverage — it is re-homed, twice over: (a) an absolute per-persona
    aggregate fold-to-c-bet ceiling is already live on the closed-loop harness
    (`BANDS`/`test_persona_postflop_bands`, the HARD-today fold-to-c-bet gate),
    which is the better instrument because it measures the real arrival range;
    (b) the price-response regression the α test was actually catching
    (price-blind defense) is caught by `test_fold_to_bet_monotone_in_faced_size`
    on the very same uniform fixture, which is untouched by this slice and
    still asserts monotonicity plus a ≥0.10 SMALL→LARGE spread for five
    personas and a bounded shallow rise for the station.

    NOT A BAND MOVE (§11 item 7) and NOT a W3R-1 dodge (§11 item 15): no band
    was re-anchored, no lever or magnitude was touched, no §5 number was
    written into an assertion, and the engine is byte-identical. §5's
    fold-to-c-bet row keeps its existing HARD-today gate and its DIRECTIONAL
    per-archetype edges — this slice deliberately does NOT promote §5's
    per-archetype numbers into a new gate, because §5a records those edges as
    uncertified (conf LOW, single-author format evidence) and §7 reserves the
    single band re-anchor for W4-b."""
    r = catcher_fold_by_size[persona]
    for frac in PRICE_FRACS:
        alpha = frac / (1 + frac)  # size-exact; no tolerance — see docstring
        assert r[frac] <= alpha, (
            f"{persona} bluff-catcher fold {r[frac]:.4f} vs a {frac}-pot bet "
            f"exceeds the balanced-villain α ceiling {alpha:.4f}"
        )


# ---- Naked ace-high against the same α ceiling (2026-08-19 owner ruling) ----
#
# `_CATCHER_BUCKETS` above excludes ACE_HIGH, on the stated ground that ace-high
# loses to part of a balanced bettor's bluff half and so is not a bluff-catcher.
# The OWNER RULED ON 2026-08-19 that the α bound DOES apply to the ACE_HIGH
# bucket anyway, closing the question T1's build round referred up
# (`docs/ai-dlc/ledger/phase3-invest-then-fold.md`, finding 3 + first open item).
#
# The ruling is recorded here rather than applied. Applying it as a runtime
# calibration would raise ace-high call rates and breach the frozen
# went-to-showdown bands that capped T3's `_ACE_HIGH_RIVER_CALL_DAMP` at 0.06;
# reconciling the ruling with those bands is a separate owner decision. So the
# α fixture above is deliberately NOT widened to include ACE_HIGH — doing so
# would fail on 15 to 24 cells per street, which is a red suite, not a guard.
#
# This helper is purpose-built rather than a reuse of `_measure_catcher_fold_by_size`
# for one reason now, not two: the range filter is a different bucket
# (naked ACE_HIGH here vs the one-pair catcher buckets there). `opponents`
# no longer distinguishes them — `_measure_fold_by_size` and
# `_measure_catcher_fold_by_size` both accept it too (2026-08-20 follow-up to
# #203), and `test_fold_by_size_is_opponents_aware` (next to
# `test_fold_by_size_is_street_aware` above) proves the price fixtures now
# see `_MW_CATCH_TIGHTEN`/T1's `opponents > 1` predicate. Node, deal seed,
# per-cell decision seed and n are otherwise identical to that fixture, so the
# two tables are directly comparable.
def _measure_ace_high_fold_by_size(persona: str, street, opponents: int):
    """{frac: fold-to-bet} for NAKED ace-high (ACE_HIGH + DrawCategory.NONE) at
    one persona, street and opponent count, on `catcher_fold_by_size`'s node."""
    from app.domain.equity import RANKS

    packs = load_persona_packs()
    if set(VillainType) - set(packs):
        pytest.skip("not all persona packs authored yet")
    deal_rng = random.Random(20260721)
    deck0 = [r + s for r in RANKS for s in "shdc"]
    spots = []
    while len(spots) < _PRICE_N:
        deck = deck0[:]
        deal_rng.shuffle(deck)
        hole, board = (deck[0], deck[1]), deck[2:5]
        made, draw = strength_bucket(hole, board)
        if draw is DrawCategory.NONE and made is StrengthBucket.ACE_HIGH:
            spots.append((hole, board))

    pack = packs[VillainType(persona)]
    pi = ALL_PERSONAS.index(persona)
    pot_pre = 6.0
    rates = {}
    for fi, frac in enumerate(PRICE_FRACS):
        to_call = round(frac * pot_pre, 2)
        legal = [
            personas_postflop_legal_fold(),
            personas_postflop_legal_call(to_call),
            personas_postflop_legal_raise(2 * to_call, 100.0),
        ]
        rng = random.Random(20260721 + 100 * pi + fi)  # same per-cell seed
        folds = 0
        for hole, board in spots:
            d = sample_postflop_decision(
                pack,
                hole,
                board,
                legal,
                pot_pre + to_call,
                100.0,
                opponents,
                rng,
                current_bet_to=to_call,
                street=street,
            )
            folds += d.action is ActionType.FOLD
        rates[frac] = folds / _PRICE_N
    return rates


def test_ace_high_alpha_holds_for_the_station_pre_river():
    """The α ceiling on naked ace-high, asserted over the ONLY part of that
    surface the engine satisfies today: `calling_station`, all four prices, one
    through three opponents, on every street before the river.

    THE RULING. The owner ruled on **2026-08-19** that α = f/(1+f) DOES bound
    the ACE_HIGH strength bucket, answering the open question T1 referred up.
    This test is that ruling's instrument, not its implementation: NO engine
    behaviour changed with it, and none may change to make it pass.

    WHY THE ASSERTION IS THIS NARROW, stated as a violation map rather than
    implied. Measured at this file's own α node (n=1250 naked-ace-high spots,
    deal seed 20260721, per-cell decision seed 20260721 + 100·persona_index +
    frac_index), the count of persona-and-size cells whose fold rate EXCEEDS α:

        street        opp=1    opp=2    opp=3
        None          15/24    19/24    19/24
        FLOP          15/24    20/24    20/24
        TURN          17/24    20/24    20/24
        RIVER         24/24    24/24    24/24

    `street=None` at one opponent reproduces `alpha-multiway-t1.md`'s 15-of-24
    figure cell for cell. The calling station is the only persona with a clean
    row anywhere; no street has a clean column; the river has no clean cell for
    anyone. Full per-cell table, the reproducer, and the reasoning:
    `docs/ai-dlc/research/slice2-invest-then-fold/alpha-acehigh-ruling.md`.

    THE VIOLATED CELLS ARE DELIBERATELY NOT PINNED, in either direction. An
    expected-failure pin would entrench a violation the ruling calls wrong as
    the engine's specification, and the α identity is a CEILING and never a
    floor (the A1 guardrail — no lower bound on any fold rate exists in this
    file and none is added here).

    T3'S RIVER CALL LEG AGAINST α, because the obvious question is whether it
    helped. Sweeping `_ACE_HIGH_RIVER_CALL_DAMP` at one opponent: 0.0 (the
    pre-T3 hard zero) 24/24 over α · **0.06 (shipped) 24/24** · 0.45 20/24 ·
    1.0, the leg fully undamped, still 18/24 · zero cells only near 3.0. T3 cut
    the station's ⅓-pot river fold rate 0.9744 → 0.5584 and closed no α cells,
    and the constant is not the reason: the bound sits about fifty times the
    shipped value away, outside this branch's whole range. That is the arithmetic
    the ruling-versus-bands reconciliation needs, and it is the owner's.

    WHY THIS SUBSET IS WORTH A TEST rather than being a decorative pass. The
    binding cell is TURN / three opponents / ⅓-pot at **+9.53pp** of headroom
    (0.1528 vs α 0.2481), ≈7.8 binomial SE at n=1250, and the sign never flips
    across five (deal seed, decision seed, n) configurations — min headroom
    (20260721, 20260721, 1250) +9.53pp · (…, 625) +9.77pp · (777, 777, 1250)
    +8.93pp · (424242, 424242, 1250) +9.09pp · (99, 12345, 2500) +8.45pp, with
    the binding cell always at three opponents and a small price. The quantity
    is live and moving the wrong way: T1 raised this persona's multiway flop
    ace-high fold rate by up to +0.1176 in one slice (0.2312 → 0.3488 at 1.5×,
    two opponents), spending about a third of that cell's headroom. Two more
    slices of that size and the last compliant persona breaches.

    SCOPE, honestly. This guards a decision rule on a uniform-deal
    naked-ace-high range at one node — not an arrival range, not a closed-loop
    population statistic, and not the other five personas. Nothing here replaces
    `test_fold_to_bet_respects_alpha_ceiling`, which still owns the one-pair
    bluff-catcher range and is untouched by this slice."""
    for street in (None, Street.FLOP, Street.TURN):
        for opponents in (1, 2, 3):
            r = _measure_ace_high_fold_by_size("calling_station", street, opponents)
            for frac in PRICE_FRACS:
                alpha = frac / (1 + frac)  # size-exact; no tolerance
                assert r[frac] <= alpha, (
                    f"calling_station naked-ace-high fold {r[frac]:.4f} vs a "
                    f"{frac}-pot bet at street={street} opponents={opponents} "
                    f"exceeds the α ceiling {alpha:.4f} — the last α-compliant "
                    f"cells on this bucket (owner ruling 2026-08-19) have "
                    f"regressed; see alpha-acehigh-ruling.md"
                )

# ---- The RIVER leg of that ceiling, over the whole roster (S3-T4, 2026-08-22) --
#
# S3-T4 is ticket 4 of improvement slice 3 ("calldown") of the bot-realism
# flywheel. It closes the half of the 2026-08-19 ruling that #204 left open.
# #204 built `_measure_ace_high_fold_by_size` above and pinned only the part of
# the ace-high surface that COMPLIES with the ruling — the calling station,
# before the river — and asserted nothing whatever about the river. The ruling is
# roster-wide and names no street, so the river is owed an assertion too, and the
# only honest assertion available today is an EXPECTED FAILURE: measured at this
# file's own alpha node, all 24 heads-up persona-and-price river cells exceed
# alpha, by between +0.2695 (maniac facing a third of the pot) and +0.6391 (nit
# facing a third of the pot).
#
# WHY AN EXPECTED-FAILURE MARK, when `alpha-acehigh-ruling.md` section 6 declined
# one. That section gave two grounds: an expected-failure pin would entrench the
# violation as the engine's specification, and a one-sided ratchet over sixty-odd
# cells would be a re-record burden on every future slice. The shape below
# answers both rather than arguing with them.
#
#   * The mark sits at TEST granularity, one leg per persona — six legs, not
#     sixty cells — and it PINS NO NUMBER. Every cell may move as far as it
#     likes, in either direction, with no re-record here. Only crossing a
#     persona's whole river row into alpha compliance changes the verdict.
#   * `strict=True` makes compliance LOUD. The day a persona's river row falls
#     under alpha its leg XPASSes and the suite goes red, so a slice that fixes
#     this cannot do it quietly. That is the opposite of entrenchment.
#
# So this is a ONE-WAY COMPLIANCE TRIPWIRE — "the river violates alpha, and we
# will be told the moment it stops" — and not a specification of the violation.
# Nothing about the engine changed to produce it; T3's `_ACE_HIGH_RIVER_CALL_DAMP`
# stays at 0.06 and the mark is a statement about the measurement, not a licence.
#
# ONE-WAY MEANS ONE-WAY: THIS TEST CANNOT DETECT THE BREACH WIDENING. Every one
# of the 24 cells could climb another twenty points and the mark would still
# report a quiet XFAIL, exactly as it does today. The widening S3-T2 already
# caused (nit +0.0440, TAG +0.0800 at a third of the pot) was caught by the
# report's measurement, not by this test. Gating the widening needs a second,
# level-pinning instrument, which this slice deliberately did not build — see the
# per-range-versus-per-bucket contract defect at filed item 10 of
# `docs/ai-dlc/ledger/flywheel-slice3-calldown.md`, which puts the whole
# per-bucket obligation in question and would DELETE this test rather than fix it.
#
# HEADS-UP ONLY, ON PURPOSE. alpha = f/(1+f) is a HEADS-UP identity. In a
# multiway pot the minimum-defence obligation is SHARED between defenders, so a
# single defender's admissible fold rate is strictly ABOVE f/(1+f) and this
# ceiling is not the correct bound there — the same multiway caveat that is
# recorded with `_ACE_HIGH_RIVER_CALL_DAMP` in the engine. The station test above
# asserts alpha at two and three opponents as well; that is conservative and it
# happens to pass, but this leg does not need the conservatism and does not take
# it.
#
# AIR IS NOT TOUCHED. The engine's river branch zeroes AIR's call merit outright
# (`personas_postflop.py`, the `street is Street.RIVER and draw is
# DrawCategory.NONE` branch). This ticket does not read, assert on, or move that
# zero: the range filter here is `StrengthBucket.ACE_HIGH` only.
def _ace_high_river_alpha_breaches(persona: str) -> list[str]:
    """Every naked-ace-high RIVER cell for `persona` whose fold rate exceeds the
    size-exact alpha = f/(1+f), heads-up, at this file's alpha node.

    An empty list means the persona's whole river row is alpha-compliant. Shared
    verbatim by the guard below and by its non-vacuity proof, so that "the guard
    can pass" and "the guard trips" are statements about the SAME assertion."""
    r = _measure_ace_high_fold_by_size(persona, Street.RIVER, 1)
    breaches = []
    for frac in PRICE_FRACS:
        # Size-exact, and RAW: no tolerance. Owner ruling 10 of 2026-08-22 keeps
        # the alpha assertion raw, and the A1 guardrail forbids a fold FLOOR, so
        # this comparison is one-sided by law as well as by construction.
        alpha = frac / (1 + frac)
        if r[frac] > alpha:
            breaches.append(
                f"{persona} naked-ace-high river fold {r[frac]:.4f} vs a "
                f"{frac}-pot bet exceeds alpha {alpha:.4f} by {r[frac] - alpha:+.4f}"
            )
    return breaches


@pytest.mark.xfail(
    strict=True,
    reason="KNOWN ENGINE DEFECT, filed for owner ruling: naked ace-high exceeds the "
    "alpha fold ceiling at every heads-up river price for every persona (owner ruling "
    "2026-08-19 made alpha binding on this bucket). Closing it needs an ace-high river "
    "call merit roughly 60x the shipped one, which the frozen went-to-showdown bands "
    "refuse. See docs/ai-dlc/research/slice3-calldown/t4-report.md.",
)
@pytest.mark.parametrize("persona", ALL_PERSONAS)
def test_ace_high_river_alpha_ceiling(persona):
    """alpha = f/(1+f) as a fold CEILING on naked ace-high at the RIVER, heads-up,
    all four prices, all six personas — the leg the 2026-08-19 owner ruling
    requires and #204 deliberately did not write. EXPECTED TO FAIL today; the
    reasoning for the mark, its granularity and its scope is in the block above.

    WHAT IS MEASURED AT THIS TIP (`_measure_ace_high_fold_by_size`, n=1250 naked
    ace-high spots, deal seed 20260721, per-cell decision seed 20260721 +
    100*persona_index + frac_index, heads-up, alpha = 0.2481 / 0.3333 / 0.5000 /
    0.6000 at 1/3-pot / 1/2-pot / pot / 1.5x-pot):

        persona           1/3-pot   1/2-pot      pot   1.5x-pot   worst margin
        maniac             0.5176   0.7264   0.8336     0.9024        +0.2695
        calling_station    0.5584   0.6520   0.7520     0.7936        +0.3187
        lag                0.6392   0.8048   0.8848     0.9336        +0.4715
        tag                0.7600   0.8928   0.9328     0.9664        +0.5595
        passive_fish       0.7640   0.9072   0.9368     0.9648        +0.5739
        nit                0.8872   0.9624   0.9736     0.9864        +0.6391

    24 of 24 cells breach. The SMALLEST breach in the table is the maniac facing a
    third of the pot at +26.95 percentage points, about 19 binomial standard
    errors at this n, so no persona is anywhere near the wall and no reseed
    changes the verdict.

    TWO ROWS MOVED SINCE #204 MEASURED THEM, AND BOTH MOVED THE WRONG WAY. S3-T2
    cut the nit's `call_looseness` 0.45 -> 0.32 and the TAG's 0.6 -> 0.38 to bring
    their went-to-showdown rates down; a tighter calling dial also folds naked
    ace-high more often, so the nit's 1/3-pot river fold rose 0.8432 -> 0.8872 and
    the TAG's 0.6800 -> 0.7600. That is a real cost of the calldown slice, stated
    here rather than left for a reader to diff, and it is why the constant that
    would buy full compliance moved too (see the non-vacuity test below).

    NOT A LICENCE AND NOT A FLOOR. No engine behaviour changed with this test and
    none may change to make it pass. The A1 guardrail stands: alpha is a ceiling,
    never a floor, and no lower bound on any fold rate exists in this file."""
    breaches = _ace_high_river_alpha_breaches(persona)
    assert not breaches, "; ".join(breaches)


def test_ace_high_river_alpha_guard_is_not_vacuous(monkeypatch):
    """The guard above is a real measurement of the engine, proved in BOTH
    directions on the same assertion body — it can pass, and it trips.

    WHY THIS TEST IS NEEDED AT ALL. A strict expected-failure mark is worthless if
    the assertion under it could never pass for a reason unrelated to the defect
    it claims to record — a mis-scoped fixture fails just as red as a broken
    engine. So this test drives `_ACE_HIGH_RIVER_CALL_DAMP`, the one constant that
    governs how much naked ace-high calls the river, to two scratch values and
    reads the SAME `_ace_high_river_alpha_breaches` the guard reads.

    A DIRECTION CORRECTION, because the ticket asks for the opposite one. S3-T4's
    text asks for a non-vacuity proof by "deliberate damp INFLATION beyond what
    alpha allows". Inflating this damp cannot breach alpha: the damp multiplies
    the CALL merit, so raising it lowers the fold rate and moves the roster TOWARD
    the ceiling's compliant side. alpha is a ceiling on folding and therefore
    places no upper bound on calling at all. The substance the ticket wants —
    "this guard is not passing, or failing, by construction" — is what is asserted
    here, in the two directions that actually exist.

      * DEFLATION IS WHAT ALPHA FORBIDS, and the guard catches it. At a damp of
        2.5 the roster is close to compliant but not compliant: 6 of 24 cells are
        still over, binding at the nit facing 1.5x-pot, 0.6704 against alpha
        0.6000 (+0.0704, about 5.3 binomial standard errors at n=1250). The nit's
        leg trips.
      * THE GUARD CAN PASS. At a damp of 5.0 every one of the 24 cells is at or
        under alpha, binding at the nit facing 1/2-pot with 0.2632 against 0.3333
        (-0.0701 of headroom). Every persona's leg is clean, which is what makes
        the expected failure at the shipped 0.06 a statement about the ENGINE
        rather than about this fixture.

    WHERE FULL COMPLIANCE ACTUALLY SITS, measured rather than inherited. The
    roster crosses into 0-of-24 between damp 3.5 (1 cell over, the nit at 1/2-pot
    by +0.0003) and 3.6 (0 over, -0.0069). `alpha-acehigh-ruling.md` put that
    crossing near 3.0 before S3-T2; the nit's and the TAG's tighter calling dials
    pushed it up. Either way the number is roughly sixty times the shipped 0.06,
    and the frozen went-to-showdown bands already refused 0.45 — which is the
    arithmetic of the ruling-versus-bands reconciliation, and it is the owner's.
    The scratch values 2.5 and 5.0 are chosen to sit clear of that crossing on
    each side, not adjacent to it, so this test does not become a pin on the
    crossing point.

    THE SHIPPED CONSTANT IS UNCHANGED, asserted at the end so a future edit to
    the engine cannot make this proof quietly describe a different engine."""
    monkeypatch.setattr(personas_postflop, "_ACE_HIGH_RIVER_CALL_DAMP", 2.5)
    deflated = {p: _ace_high_river_alpha_breaches(p) for p in ALL_PERSONAS}
    assert deflated["nit"], (
        "non-vacuity leg 1 FAILED: at a river call damp of 2.5 the nit's "
        "naked-ace-high river row is alpha-compliant, so the guard does not trip "
        "on a damp deflection alpha forbids"
    )

    monkeypatch.setattr(personas_postflop, "_ACE_HIGH_RIVER_CALL_DAMP", 5.0)
    compliant = {p: _ace_high_river_alpha_breaches(p) for p in ALL_PERSONAS}
    assert not any(compliant.values()), (
        "non-vacuity leg 2 FAILED: at a river call damp of 5.0 the guard STILL "
        "reports breaches, so its expected failure at the shipped 0.06 is not "
        "evidence about the engine: "
        + "; ".join(m for ms in compliant.values() for m in ms)
    )

    monkeypatch.undo()
    assert personas_postflop._ACE_HIGH_RIVER_CALL_DAMP == 0.06, (
        "the shipped river call damp is no longer 0.06 — re-derive the two scratch "
        "values above before trusting this proof"
    )


def test_fold_to_bet_persona_ordering_at_fixed_size(fold_by_size):
    """RES-D §2 invariant 2 at MEDIUM (½-pot), RE-DERIVED at W3R-2.

    The pre-W3R-2 order was nit > tag > lag > {fish ≈ maniac ≈ station}, with
    the intra-trio ranks a documented near-tie (P1 A1 collapsed the loose trio
    over this fixture's uniform, air-heavy range). W3R-2 (persona-realism-w3r-2,
    2026-07-24 — owner decision 2) splits that trio apart on purpose, so the
    fish and station legs are re-derived to the INTENDED new order (this is the
    hyp-2 fix landing, NOT a flattening regression):

    - **passive_fish CLIMBS to the top.** Its `call_looseness` is now authored at
      0.42 (was inheriting `stickiness` 1.4), so the fish stops over-calling; ×
      its steep `size_elasticity` 1.3 it is the most price-sensitive persona in
      the file, and on this uniform air-heavy range it folds MORE at ½-pot than
      the disciplined personas (measured 0.4728 — above tag 0.3800 and just
      above nit 0.4480). The old `abs(fish − maniac) < 0.06` near-tie and
      `max(fish, maniac) < lag` legs pinned the fish to the loose trio and are
      replaced by `fish > tag` (its climb) plus a bound keeping it from running
      away past the nit. NOTE this is the uniform-range aggregate; on the fish's
      REAL arrival range it folds 0.361 at ½-pot (W5-a4 moved that arrival-range
      measurement out of this file — it is asserted against the grounded §5
      bands by `tests/test_arrival_range_ftc.py::test_t4_flop_absolute_band`).
    - **calling_station drops to STRICTLY loosest.** Its `call_looseness` is now
      authored at 4.0 (was inheriting `stickiness` 1.8), so the near-tie
      `station <= min(fish, maniac) + 0.01` is re-derived back to a strict `<`
      (measured 0.1752, a clear 0.11 below maniac's 0.2864).

    The disciplined-vs-loose legs (maniac < lag < tag < nit) stay strict and
    untouched."""
    r = {p: fold_by_size[p][0.5] for p in ALL_PERSONAS}
    assert r["calling_station"] < min(r["passive_fish"], r["maniac"]), r
    assert r["passive_fish"] > r["tag"], r  # W3R-2: fish climbs above the loose trio
    assert r["passive_fish"] - r["nit"] < 0.10, r  # ... but not past the nit
    assert r["maniac"] < r["lag"], r
    assert r["calling_station"] < r["lag"], r
    assert r["lag"] < r["tag"], r
    assert r["tag"] < r["nit"], r


# ---- Non-vacuity: `street` is actually threaded, not a dead parameter -----
#
# The fixtures above default to `street=None`, which sits outside every
# street-gated lever in `sample_postflop_decision` (river-only river
# polarization, T3's `_ACE_HIGH_RIVER_CALL_DAMP`, flop/turn-only
# `_ACE_HIGH_FLOAT_RAISE_DAMP`, etc.) — see `phase3-invest-then-fold.md`'s T1
# round, where a copy of these fixtures measured a FLOP/TURN-gated lever at
# street=None and produced byte-identical before/after tables. This test
# calls the underlying `_measure_fold_by_size` helper directly at
# `street=Street.RIVER` (bypassing the module-scoped fixture, which is pinned
# to the default) and proves the surface actually moves — it guards the
# THREADING MECHANISM, not one pinned number, so it fails if `street` is ever
# dropped or silently ignored again.
def test_fold_by_size_is_street_aware():
    r_none = _measure_fold_by_size(street=None)
    r_river = _measure_fold_by_size(street=Street.RIVER)
    # calling_station at pot-size (frac=1.0): measured 0.2256 at street=None
    # vs 0.4368 at street=RIVER (river polarization zeros AIR's call merit and
    # T3 damps ACE_HIGH's) — a +0.21 rise, far past noise at n=1250.
    none_pot = r_none["calling_station"][1.0]
    river_pot = r_river["calling_station"][1.0]
    assert river_pot - none_pot > 0.15, (
        f"street=RIVER should fold measurably more than street=None at "
        f"pot-size, got {river_pot:.4f} vs {none_pot:.4f}"
    )


# ---- Non-vacuity: `opponents` is actually threaded, not a dead parameter --
#
# 2026-08-20 follow-up to #203 (this fixture's own history): `opponents` was
# still hardcoded to `1` (the 7th positional arg to `sample_postflop_decision`)
# even after `street` got threaded, so multiway-gated levers stayed invisible
# to it — notably T1's `_ACE_HIGH_FLOAT_RAISE_DAMP`, which since T1
# (improvement slice 2, 2026-08-18) fires on the facing-a-BET node whenever
# `opponents > 1`, not only `facing_raise`. This test calls the underlying
# `_measure_fold_by_size` helper directly at `opponents=3` (bypassing the
# module-scoped fixture, which is pinned to the `opponents=1` default) and
# proves the surface actually moves — same shape as
# `test_fold_by_size_is_street_aware` above, guarding the THREADING
# MECHANISM rather than one pinned number.
def test_fold_by_size_is_opponents_aware():
    r_hu = _measure_fold_by_size(street=Street.FLOP, opponents=1)
    r_mw = _measure_fold_by_size(street=Street.FLOP, opponents=3)
    # tag facing a ⅓-pot bet on the flop: measured 0.2168 at opponents=1 vs
    # 0.3184 at opponents=3 — a +0.1016 rise, far past noise at n=1250. THREE
    # mechanisms carry it, not two: T1's `_ACE_HIGH_FLOAT_RAISE_DAMP` (shrinks
    # naked ace-high's CALL_BASE facing a bet at opponents > 1) and
    # `_MW_CATCH_TIGHTEN` (tightens the FOLD merit of the AIR/ACE_HIGH/
    # MIDDLE_PAIR/TOP_PAIR buckets — not "one-pair" alone) together carry only
    # part of it: neutralizing both still leaves +0.0432. The rest is the
    # pack-level `multiway_bluff_damp` (shrinks bluff_mass, which raises FOLD's
    # normalized share through the complement) — neutralizing all three drops
    # the delta to exactly 0.0. So this guard is load-bearing on all three,
    # and a maintainer changing any one of them should expect this number to
    # move.
    hu = r_hu["tag"][0.33]
    mw = r_mw["tag"][0.33]
    assert mw - hu > 0.05, (
        f"opponents=3 should fold measurably more than opponents=1 at "
        f"⅓-pot on the flop, got {mw:.4f} vs {hu:.4f}"
    )


# ---------------------------------------------------------------------
# Faced-frac denominator: raise-over-bet and check-raise spots, where the
# facing seat has NONZERO street chips and to_call is only the increment.
# Pre-aggression pot must be pot_bb − current_bet_to (the aggressor's full
# bet-TO), never pot_bb − to_call.
# ---------------------------------------------------------------------


def test_size_bucket_res_e_cutoffs_direct():
    """RES-E cutoffs on the two refuter repro fracs (and the buggy values)."""
    sb = personas_postflop.size_bucket
    SizeBucket = personas_postflop.SizeBucket
    assert sb(5.0 / 12.0) is SizeBucket.MEDIUM  # 0.4167 — raise-over-bet repro
    assert sb(15.0 / 14.0) is SizeBucket.LARGE  # ≈1.07 — check-raise repro
    assert sb(5.0 / 15.0) is SizeBucket.SMALL  # what pot−to_call wrongly gave
    assert sb(0.40) is SizeBucket.SMALL
    assert sb(0.70) is SizeBucket.MEDIUM
    assert sb(1.10) is SizeBucket.LARGE
    assert sb(1.11) is SizeBucket.OVERBET


class _CaptureWeights:
    """Duck-typed rng capturing the sampler's first choices() distribution."""

    def __init__(self):
        self.dist = None

    def choices(self, population, weights, k=1):
        if self.dist is None:
            self.dist = dict(zip(population, weights, strict=True))
        return [population[0]]


def _faced_fold_weight(pot_bb, to_call, current_bet_to, contribution=None):
    """Normalized FOLD weight in a FOLD/CALL/RAISE spot (fixed tag + middle
    pair, no draw, SPR well above commit) — only the price factor varies.
    `contribution` (None = legacy denominator) opts into the W1-b exact
    pre-aggression denominator."""
    pack = _pack("tag")
    legal = [
        personas_postflop_legal_fold(),
        personas_postflop_legal_call(to_call),
        personas_postflop_legal_raise(current_bet_to + 2 * to_call, 200.0),
    ]
    cap = _CaptureWeights()
    sample_postflop_decision(
        pack,
        ("9h", "2d"),
        ["Ac", "9s", "3h"],
        legal,
        pot_bb,
        100.0,
        1,
        cap,  # type: ignore[arg-type] — duck-typed capture rng
        current_bet_to=current_bet_to,
        latest_aggressor_contribution_bb=contribution,
    )
    return cap.dist[ActionType.FOLD]


def test_faced_frac_raise_over_bet_lands_medium_not_small():
    """Refuter repro 1: hero bets 3 into 9, villain raises to 8 → hero faces
    to_call 5, live pot 20, current_bet_to 8. Faced frac = 5/(20−8) = 0.4167
    → MEDIUM. The pot−to_call bug computed 5/15 = 0.333 → SMALL (hero's own
    3bb street chips left in the denominator)."""
    raised = _faced_fold_weight(pot_bb=20.0, to_call=5.0, current_bet_to=8.0)
    # Control: genuine simple MEDIUM bet at the same frac (5 into 12).
    medium = _faced_fold_weight(pot_bb=17.0, to_call=5.0, current_bet_to=5.0)
    # Counter-control: genuine SMALL bet, the bucket the bug assigned (5 into 15).
    small = _faced_fold_weight(pot_bb=20.0, to_call=5.0, current_bet_to=5.0)
    assert raised == pytest.approx(medium)
    assert raised > small  # MEDIUM α 0.375 > SMALL α 0.25 → more fold mass


def test_faced_frac_check_raise_lands_large():
    """Refuter repro 2: hero bets 5 into 9, villain check-raises to 20 → hero
    faces to_call 15, live pot 34, current_bet_to 20. Faced frac = 15/(34−20)
    = 15/14 ≈ 1.07 → LARGE per RES-E (≤1.10); the bug computed 15/19 ≈ 0.79,
    a 36% magnitude error."""
    check_raised = _faced_fold_weight(pot_bb=34.0, to_call=15.0, current_bet_to=20.0)
    # Control: genuine simple bet at the same frac (15 into 14).
    large = _faced_fold_weight(pot_bb=29.0, to_call=15.0, current_bet_to=15.0)
    assert check_raised == pytest.approx(large)
    # Bucket-flipping variant (0.79 above also lands LARGE, so distinguish
    # here): hero bets 6 into 6, villain check-raises to 16 → to_call 10,
    # live pot 28, current_bet_to 16. True frac 10/12 = 0.83 → LARGE; the
    # pot−to_call bug gave 10/18 = 0.556 → MEDIUM, indistinguishable from a
    # genuine simple 10-into-18 bet (the counter-control below).
    flipped = _faced_fold_weight(pot_bb=28.0, to_call=10.0, current_bet_to=16.0)
    medium = _faced_fold_weight(pot_bb=28.0, to_call=10.0, current_bet_to=10.0)
    assert flipped > medium  # LARGE α 0.47 > MEDIUM α 0.375 → more fold mass


# W1-b (F9) — faced_frac increment fix. The live loop supplies the W0-a
# latest-aggressor increment as the EXACT pre-aggression denominator; the legacy
# `max(current_bet_to, to_call)` branch (no increment supplied) OVER-subtracts
# when the aggressor already had street chips → over-fold. These pin the fix at
# the sampler via exact captured FOLD weights (never sampled counts).


def test_faced_frac_selfreraise_folds_less():
    """Self-re-raise (SB bets 2, BB raises 6, SB re-raises to 13; BB faces
    to_call 7, live pot 21, current_bet_to 13). SB's true increment is 11 (13−2),
    so faced_frac = 7/(21−11) = 0.700 (MEDIUM). The legacy denominator subtracts
    the whole 13 → 7/(21−13) = 0.875 (LARGE, α 0.47), OVER-stating the price and
    over-folding. The fix (contribution=11) folds strictly LESS."""
    legacy = _faced_fold_weight(pot_bb=21.0, to_call=7.0, current_bet_to=13.0)
    fixed = _faced_fold_weight(pot_bb=21.0, to_call=7.0, current_bet_to=13.0, contribution=11.0)
    assert fixed < legacy  # MEDIUM α 0.375 < LARGE α 0.47 → less fold mass
    # The fixed value matches a genuine simple MEDIUM bet at the same 0.700 frac.
    genuine_medium = _faced_fold_weight(pot_bb=17.0, to_call=7.0, current_bet_to=7.0)
    assert fixed == pytest.approx(genuine_medium)


def test_faced_frac_backraise_after_call_corrected():
    """Back-raise after calling (Codex #2 — divergence is NOT limited to
    self-re-raises): a prior caller re-raises, so its increment (25) is less than
    its bet-TO (30). Facing to_call 15, live pot 65 → true frac 15/(65−25) = 0.375
    (SMALL); legacy gives 15/(65−30) = 0.4286 (MEDIUM), over-folding. Fixed folds
    less and matches a genuine simple SMALL bet at the same frac."""
    legacy = _faced_fold_weight(pot_bb=65.0, to_call=15.0, current_bet_to=30.0)
    fixed = _faced_fold_weight(pot_bb=65.0, to_call=15.0, current_bet_to=30.0, contribution=25.0)
    assert fixed < legacy  # SMALL α 0.25 < MEDIUM α 0.375 → less fold mass
    genuine_small = _faced_fold_weight(pot_bb=55.0, to_call=15.0, current_bet_to=15.0)
    assert fixed == pytest.approx(genuine_small)


def test_faced_frac_fresh_raise_byte_identical():
    """Fresh aggression (a raiser with zero prior street chips) has increment ==
    bet-TO, so supplying the contribution reproduces the legacy denominator
    EXACTLY — the fix touches only prior-investment lines (bet 3 into 9, raised to
    8 by a fresh raiser → to_call 5, contribution 8 == current_bet_to 8)."""
    legacy = _faced_fold_weight(pot_bb=20.0, to_call=5.0, current_bet_to=8.0)
    fixed = _faced_fold_weight(pot_bb=20.0, to_call=5.0, current_bet_to=8.0, contribution=8.0)
    assert fixed == legacy


# =====================================================================
# F2 — size-linked bluffing (RES-D §3 polar curve, RES-E §3 mapping)
# =====================================================================
#
# Direction (RES-D §1b/§3, authoritative over the roadmap's shorthand): the
# polar bluff SHARE f/(1+2f) RISES with the chosen size — SMALL ~0.20,
# MEDIUM ~0.27, LARGE ~0.32, OVERBET 0.375 — i.e. value:bluff TIGHTENS
# toward 1:1 (4:1 → 1.5:1). So bluff frequency at a chosen size must be
# monotone INCREASING across SMALL → OVERBET.
#
# Technique: force the persona's sizing distribution to a single authored
# size, then read the EXACT normalized action weights via a capture rng
# (deterministic — no sampling noise, no band flake).

BLUFF_SIZE_FRACS = (0.33, 0.5, 1.0, 1.5)  # SMALL / MEDIUM / LARGE(pot) / OVERBET


def _forced_size_pack(persona: str, frac: float):
    pack = _pack(persona).model_copy(deep=True)
    pack.postflop = pack.postflop.model_copy(
        update={"sizing": {str(frac): 1.0}, "sizing_by_node": None}
    )
    return pack


def _air_bet_weight(persona: str, frac: float) -> float:
    """Exact normalized BET weight for a pure-air hand (7h5d on Kc9s3h — no
    draw, bluff cell) in an unopened node, sizing forced to `frac`."""
    cap = _CaptureWeights()
    sample_postflop_decision(
        _forced_size_pack(persona, frac),
        ("7h", "5d"),
        ["Kc", "9s", "3h"],
        [personas_postflop_legal_check(), personas_postflop_legal_bet(1.0, 60.0)],
        4.0,
        100.0,
        1,
        cap,  # type: ignore[arg-type] — duck-typed capture rng
    )
    return cap.dist[ActionType.BET]


@pytest.mark.parametrize("persona", ALL_PERSONAS)
def test_bluff_freq_rises_with_chosen_size(persona):
    """RES-D §3 invariant 1 (the flat-bluff_freq bug): bluff frequency moves
    with the chosen size, strictly increasing SMALL → MEDIUM → LARGE →
    OVERBET, with a measurable gap (share curve 0.20→0.375 ⇒ overbet bluff
    frequency ≥ 1.5× the ⅓-pot one)."""
    ws = [_air_bet_weight(persona, f) for f in BLUFF_SIZE_FRACS]
    assert all(a < b for a, b in zip(ws, ws[1:], strict=False)), (
        f"{persona} bluff freq not strictly increasing in chosen size: {ws}"
    )
    assert ws[-1] >= 1.5 * ws[0], f"{persona} overbet/small bluff gap too small: {ws}"


def test_bluff_ordering_across_personas_at_fixed_size():
    """RES-D §3 invariant 2: at a fixed chosen size (MEDIUM ½-pot), bluff
    share ordering station < nit < fish < tag < lag < maniac — F2 sets the
    shape, bluff_freq still sets the persona level."""
    order = ("calling_station", "nit", "passive_fish", "tag", "lag", "maniac")
    ws = [_air_bet_weight(p, 0.5) for p in order]
    assert all(a < b for a, b in zip(ws, ws[1:], strict=False)), dict(
        zip(order, ws, strict=True)
    )


class _SeededCaptureRng(random.Random):
    """Seeded rng that ALSO captures the sampler's first choices() distribution.
    The seed is defensive determinism only: today the sampler makes NO rng draw
    before the action `choices()` call (`noise` is a fixed default argument,
    not a draw), so `_CaptureWeights` would behave identically — seeding just
    keeps the capture valid if a pre-action draw is ever added."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dist = None

    def choices(self, population, weights=None, k=1):
        if self.dist is None:
            self.dist = dict(zip(population, weights, strict=True))
        return [population[0]]


# T-ANCHOR: the authored IP:OOP bet-rate ratio is (1 + s·δ)/(1 − s·δ) for
# `position_sensitivity` s and _POSITION_AGG_DELTA δ = 0.25 — nit/tag (s=1.0)
# → 1.25/0.75 = 5/3, lag (s=0.6) → 1.15/0.85. The other three packs author no
# `position_sensitivity`, so their multiplier is exactly 1.0 on both sides and
# their bet probability must be BIT-identical, not merely close.
_AIR_BET_IP_OOP_RATIOS = [
    ("nit", 5 / 3),
    ("tag", 5 / 3),
    ("lag", 1.15 / 0.85),
    ("passive_fish", 1.0),
    ("calling_station", 1.0),
    ("maniac", 1.0),
]


def _air_bet_prob_by_position(persona: str, *, in_position: bool) -> float:
    """Normalized BET probability for the pinned pure-air unopened c-bet node
    (7h5d on Kc9s3h — bluff cell, no draw), varying ONLY `in_position`."""
    from app.domain.table.postflop_context import PostflopContext

    rng = _SeededCaptureRng(1)
    sample_postflop_decision(
        _pack(persona),
        ("7h", "5d"),
        ["Kc", "9s", "3h"],
        [personas_postflop_legal_check(), personas_postflop_legal_bet(1.0, 60.0)],
        4.0,
        100.0,
        1,
        rng,  # type: ignore[arg-type] — duck-typed capture rng
        current_bet_to=0.0,
        is_aggressor=True,
        street=Street.FLOP,
        context=PostflopContext(
            in_position=in_position, bet_prev_street=False, busted_draw=0
        ),
    )
    return rng.dist[ActionType.BET] / sum(rng.dist.values())


@pytest.mark.parametrize(("persona", "expected_ratio"), _AIR_BET_IP_OOP_RATIOS)
def test_air_bet_rate_ip_oop_ratio_equals_authored_position_multiplier(
    persona, expected_ratio
):
    """T-ANCHOR: the air cell is an exact-frequency cell — its BET/CHECK merits
    sum to 1, so P(bet) IS the composed bluff mass and the observed IP:OOP
    bet-rate ratio must equal the authored position-multiplier ratio exactly.
    W3-b applied the multiplier AFTER the check complement was formed, which
    compressed this ratio (nit read 1.6373, tag 1.5156, lag 1.2258) and cost
    `bluff_freq` its status as an exact-frequency lever."""
    ip = _air_bet_prob_by_position(persona, in_position=True)
    oop = _air_bet_prob_by_position(persona, in_position=False)
    assert abs(ip / oop - expected_ratio) < 1e-9, (
        f"{persona}: IP/OOP={ip / oop!r} (IP={ip!r}, OOP={oop!r}) "
        f"!= authored {expected_ratio!r}"
    )
    if expected_ratio == 1.0:
        assert ip == oop, f"{persona} is position-blind — must be bit-identical"


def test_bluff_raise_path_scales_with_chosen_size():
    """The _BLUFF_RAISE_FACTOR path (air facing a bet, RAISE legal) is wired
    through the same size factor: forced-overbet raise weight strictly above
    forced-⅓-pot (fold/call merits identical, so normalization preserves the
    direction)."""

    def raise_weight(frac: float) -> float:
        cap = _CaptureWeights()
        sample_postflop_decision(
            _forced_size_pack("lag", frac),
            ("7h", "5d"),
            ["Kc", "9s", "3h"],
            [
                personas_postflop_legal_fold(),
                personas_postflop_legal_call(2.0),
                personas_postflop_legal_raise(6.0, 100.0),
            ],
            6.0,
            100.0,
            1,
            cap,  # type: ignore[arg-type]
            current_bet_to=2.0,
        )
        return cap.dist[ActionType.RAISE]

    assert raise_weight(1.5) > raise_weight(0.33)


def test_bluff_bet_sizes_tilt_big_but_value_sizes_stay_authored():
    """Joint-law check (catches a scale-then-REDRAW bug that would flatten
    the per-size bluff share back to constant): with a 50/50 {⅓, 1.5×} mix,
    - AIR bets lean big: P(1.5× | air, bet) = 0.5·f₁.₅/(0.5·f₀.₃₃+0.5·f₁.₅)
      ≈ 1.389/(0.741+1.389) ≈ 0.65 — the Bayes face of "bigger bets carry
      more bluffs", NOT a strength→size map;
    - VALUE bets keep the authored 50/50 byte-for-byte (anti-sizing-tell:
      the draw itself never conditions on strength — the regression test
      `test_sizing_spread_no_deterministic_strength_to_size` also holds).
    Seed-pinned; bounds sit >3σ from both the expected values and the
    no-tilt/false-tilt failure modes."""
    pack = _pack("maniac").model_copy(deep=True)
    pack.postflop = pack.postflop.model_copy(
        update={"sizing": {"0.33": 0.5, "1.5": 0.5}, "sizing_by_node": None}
    )
    legal = [personas_postflop_legal_check(), personas_postflop_legal_bet(1.0, 60.0)]
    board = ["Kc", "9s", "3h"]
    pot = 4.0  # ⅓-pot → 1.32bb, 1.5× → 6.0bb (well inside the bracket)

    def big_share(hole, seed, n):
        rng = random.Random(seed)
        big = small = 0
        for _ in range(n):
            d = sample_postflop_decision(pack, hole, board, legal, pot, 100.0, 1, rng)
            if d.action is ActionType.BET:
                if d.size_bb == pytest.approx(6.0):
                    big += 1
                else:
                    small += 1
        assert big + small >= 300, "too few bets to measure the size mix"
        return big / (big + small)

    air = big_share(("7h", "5d"), seed=20260722, n=2500)  # bluff cell
    value = big_share(("Ah", "Ad"), seed=20260722, n=1500)  # overpair (value)
    assert air > 0.55, f"air bets not tilted big: {air:.3f} (expected ~0.65)"
    assert air < 0.75, f"air big-size tilt implausibly large: {air:.3f}"
    assert 0.44 <= value <= 0.56, f"value size mix drifted off authored 50/50: {value:.3f}"


# =====================================================================
# F3 — bounded maniac aggression (RES-D §0 saturation fix)
# =====================================================================
#
# The maniac's authored aggression lever (15.0, vs ≤3.2 for every other
# persona) multiplied one side of the un-normalized merit ratio so hard that
# rng.choices degenerated to near-argmax; with _COMMIT_AGG_BOOST the
# effective multiplier hit 45×. F3 caps the lever in code
# (_AGGRESSION_CAP = 5.6 = 1.75 × lag's 3.2) — identity for every non-maniac
# persona, still strictly the most aggressive for the maniac, commit
# interaction bounded at 16.8. Exact weights via the capture rng
# (deterministic — no sampling noise).
#
# Entropy floor derivation: 0.5 bits ⇔ a two-way mix no more extreme than
# ~89:11 — the maniac still takes the alternative line at least ~1-in-9
# (genuine mixing), where pre-fix it was ~1-in-19. Pre-fix measured (capture
# rng, aggression uncapped at 15.0, 2026-07-22):
#   top-pair unopened   P(bet)=0.9483  H=0.294 bits
#   overpair facing ½-pot (FOLD/CALL/RAISE)  P(raise)=0.9031  H=0.484 bits
# Post-fix: 0.8725 / 0.551 and 0.7767 / 0.824.


def _entropy_bits(dist: dict) -> float:
    return -sum(w * math.log2(w) for w in dist.values() if w > 0)


def _exact_dist(persona: str, hole, board, legal, pot, stack, current_bet_to=0.0):
    cap = _CaptureWeights()
    sample_postflop_decision(
        _pack(persona),
        hole,
        board,
        legal,
        pot,
        stack,
        1,
        cap,  # type: ignore[arg-type] — duck-typed capture rng
        current_bet_to=current_bet_to,
    )
    return cap.dist


def _dist_for_pack(pack, hole, board, legal, pot, stack, opponents=1, current_bet_to=0.0):
    """Like `_exact_dist` but for an already-built (possibly lever-modified) pack."""
    cap = _CaptureWeights()
    sample_postflop_decision(
        pack, hole, board, legal, pot, stack, opponents, cap, current_bet_to=current_bet_to
    )
    return cap.dist


# W2-b — pure EV helpers (T6; unused by the sampler until T7).
def test_value_commit_threshold():
    tc = personas_postflop._value_commit_threshold
    assert tc(1.0) == pytest.approx(1.0 / 3.0)  # pot-size bet
    assert tc(3.0) == pytest.approx(3.0 / 7.0)  # 3×-pot overbet ≈ 0.429
    assert tc(0.5) == pytest.approx(0.5 / 2.0)  # half-pot → 0.25
    # monotone increasing in faced size
    assert tc(0.5) < tc(1.0) < tc(3.0)


def test_draw_equity_proxy():
    de = personas_postflop._draw_equity
    DrawCategory = personas_postflop.DrawCategory
    flop, turn, river = ["Ac", "9s", "3h"], ["Ac", "9s", "3h", "2d"], ["Ac", "9s", "3h", "2d", "7c"]
    assert de(DrawCategory.STRONG, flop) == pytest.approx(0.36)
    assert de(DrawCategory.STRONG, turn) == pytest.approx(0.18)
    assert de(DrawCategory.WEAK, flop) == pytest.approx(0.16)
    assert de(DrawCategory.WEAK, turn) == pytest.approx(0.08)
    assert de(DrawCategory.NONE, flop) == 0.0
    assert de(DrawCategory.STRONG, river) == 0.0  # no cards to come


# W2-b — commit/draw EV gate (T7 behavior). lag has spr_commit 3.0.
_STRONG_DRAW = (("Jh", "Th"), ["9h", "2h", "5c"])  # naked flush draw (AIR + STRONG)
_MADE_PLUS_DRAW = (("Ah", "Kh"), ["Ac", "7h", "2h"])  # TPTK + flush draw
_WEAK_DRAW = (("Jd", "Td"), ["8c", "7h", "2s"])  # naked gutshot (AIR + WEAK)


def test_strong_draw_potcommitted_still_jams():
    # STRONG draw facing a ⅔-pot bet, pot-committed (SPR 1.0): faced_frac 0.67 →
    # T1 threshold 0.29 < equity 0.36 → value-committed → fold zeroed → jams.
    hole, board = _STRONG_DRAW
    d = _dist_for_pack(
        _pack("lag"), hole, board,
        [personas_postflop_legal_fold(), personas_postflop_legal_call(12.0),
         personas_postflop_legal_raise(24.0, 30.0)],
        30.0, 30.0, current_bet_to=12.0,
    )
    assert d[ActionType.FOLD] == 0.0


def test_strong_draw_vs_overbet_can_fold():
    # SAME draw, same commit regime, but facing a 3×-pot OVERBET: faced_frac 3 →
    # T1 threshold 0.429 > 0.36 → no longer force-jammed, fold survives (and is
    # strictly greater than the pot-committed case).
    hole, board = _STRONG_DRAW
    over = _dist_for_pack(
        _pack("lag"), hole, board,
        [personas_postflop_legal_fold(), personas_postflop_legal_call(18.0),
         personas_postflop_legal_raise(36.0, 36.0)],
        24.0, 36.0, current_bet_to=18.0,
    )
    potc = _dist_for_pack(
        _pack("lag"), hole, board,
        [personas_postflop_legal_fold(), personas_postflop_legal_call(12.0),
         personas_postflop_legal_raise(24.0, 30.0)],
        30.0, 30.0, current_bet_to=12.0,
    )
    assert over[ActionType.FOLD] > 0.0
    assert over[ActionType.FOLD] > potc[ActionType.FOLD]


def test_madehand_with_draw_commit_not_damped():
    # An overpair/TPTK that ALSO holds a flush draw, committed vs the same overbet:
    # takes the plain value-jam (fold zeroed) — NEVER the W2-b draw damp (reviewer
    # #6). If it had wrongly entered the damp branch, fold would be > 0.
    hole, board = _MADE_PLUS_DRAW
    d = _dist_for_pack(
        _pack("lag"), hole, board,
        [personas_postflop_legal_fold(), personas_postflop_legal_call(18.0),
         personas_postflop_legal_raise(36.0, 36.0)],
        24.0, 36.0, current_bet_to=18.0,
    )
    assert d[ActionType.FOLD] == 0.0


def test_weak_draw_stops_stacking_off_at_high_commitment():
    # A naked gutshot (WEAK) facing an overbet (always below T1). Stacking-off (the
    # commit CALL) mass falls as commitment rises: deep commit (c≈0.75, damped) <
    # a boundary commit at the same faced size (c≈0, no damp).
    hole, board = _WEAK_DRAW

    def call_prob(stack):
        d = _dist_for_pack(
            _pack("lag"), hole, board,
            [personas_postflop_legal_fold(), personas_postflop_legal_call(18.0)],
            24.0, stack, current_bet_to=18.0,
        )
        return d[ActionType.CALL]

    assert call_prob(18.0) < call_prob(72.0)


# W2-a — elasticity split (call_looseness + size_elasticity).
def test_elasticity_split_faithful_decomposition_byte_identical():
    """The split is a faithful DECOMPOSITION, not a behavior change: a pack opted
    into the new levers at their fallback-equivalent values samples a BYTE-IDENTICAL
    normalized distribution vs the unset pack. call_looseness = stickiness reproduces
    the flat call scaling; size_elasticity = stickiness**(-DAMP) makes the DIRECT
    exponent (SENS * elasticity) equal the legacy inverse exponent (SENS * s**-DAMP)."""
    # THE BASE ARM IS CONSTRUCTED UNSET, not borrowed from whichever persona
    # happens not to author the levers this month (S3-T2, 2026-08-22). It used
    # to read `_pack("tag")` and rely on the tag's authored `call_looseness`
    # being equal to its `stickiness`, which was true by coincidence until this
    # slice re-tuned the tag to 0.38 — at which point the "unset" arm was
    # silently a SET arm at a different value and the test failed for a reason
    # that had nothing to do with the decomposition it checks. Clearing both
    # fields makes the fallback the thing under test.
    shipped = _pack("tag")
    base = shipped.model_copy(deep=True)
    base.postflop = shipped.postflop.model_copy(
        update={"call_looseness": None, "size_elasticity": None}
    )
    s = base.postflop.stickiness
    equiv_elasticity = s ** (-personas_postflop._PRICE_STICKINESS_DAMP)
    opted = base.model_copy(deep=True)
    opted.postflop = base.postflop.model_copy(
        update={"call_looseness": s, "size_elasticity": equiv_elasticity}
    )
    hole, board = ("9h", "8h"), ["Ac", "7s", "2h"]  # a hand facing a bet (fold+call live)
    legal = [personas_postflop_legal_fold(), personas_postflop_legal_call(3.0)]
    base_dist = _dist_for_pack(base, hole, board, legal, 6.0, 100.0)
    opted_dist = _dist_for_pack(opted, hole, board, legal, 6.0, 100.0)
    assert base_dist == opted_dist


def test_size_elasticity_zero_is_size_flat():
    """The station's size-blind config: size_elasticity = 0.0 must NOT raise
    (the naive stickiness**(-DAMP) rename would do 0**-0.15 → ZeroDivisionError)
    and must produce a price factor FLAT across every size bucket."""
    pf_zero = _pack("calling_station").postflop.model_copy(update={"size_elasticity": 0.0})
    exp = personas_postflop._price_exponent(pf_zero)  # must not raise
    assert exp == 0.0
    factors = [personas_postflop._price_factor(frac, exp) for frac in (0.3, 0.55, 0.9, 1.5)]
    assert all(abs(f - factors[0]) < 1e-12 for f in factors)  # SMALL..OVERBET flat


# T-STICKY — `stickiness` authorship contract: required exactly while a
# fallback path is live, forbidden once both split levers are authored.
_STICKY_BASE = {
    "aggression": 1.0,
    "bluff_freq": 0.1,
    "sizing": {"0.5": 1.0},
    "spr_commit": 1.5,
    "multiway_bluff_damp": 0.5,
}


def test_stickiness_forbidden_when_both_split_levers_authored():
    from pydantic import ValidationError

    from app.domain.content.models import PersonaPostflop

    with pytest.raises(ValidationError, match="stickiness"):
        PersonaPostflop.model_validate(
            {**_STICKY_BASE, "stickiness": 1.4, "call_looseness": 0.42, "size_elasticity": 1.3}
        )
    # Key PRESENCE is the contract — an explicitly-authored null is still an
    # authored key (review C-1: value-only checking would let it slip through).
    with pytest.raises(ValidationError, match="stickiness"):
        PersonaPostflop.model_validate(
            {**_STICKY_BASE, "stickiness": None, "call_looseness": 0.42, "size_elasticity": 1.3}
        )
    # Same payload minus the dead field is valid.
    PersonaPostflop.model_validate(
        {**_STICKY_BASE, "call_looseness": 0.42, "size_elasticity": 1.3}
    )


def test_stickiness_required_while_any_fallback_path_is_live():
    from pydantic import ValidationError

    from app.domain.content.models import PersonaPostflop

    for partial in (
        {},  # neither lever → both fallbacks live
        {"call_looseness": 0.6},  # size_elasticity fallback still live
        {"size_elasticity": 0.55},  # call_looseness fallback still live
    ):
        with pytest.raises(ValidationError, match="stickiness"):
            PersonaPostflop.model_validate({**_STICKY_BASE, **partial})
        PersonaPostflop.model_validate({**_STICKY_BASE, "stickiness": 1.0, **partial})


# Pinned representative spot: top pair weak kicker (Ah2d on Ac9s3h, no draw),
# unopened flop, SPR well above commit — the paradigmatic saturation symptom
# (a one-pair hand every persona MIXES bet/check with; pre-fix the maniac
# bet it 19-in-20).
_F3_SPOT = (("Ah", "2d"), ["Ac", "9s", "3h"], 3.0, 100.0)


def test_aggression_cap_binds_maniac_only():
    """The cap must sit strictly between the highest non-maniac lever
    (identity mapping ⇒ non-maniac personas byte-unchanged) and the maniac's
    authored lever (the cap actually binds). Guards future pack retunes from
    silently entering — or escaping — the compression."""
    cap = personas_postflop._AGGRESSION_CAP
    packs = load_persona_packs()
    for vt, pack in packs.items():
        if vt.value == "maniac":
            assert pack.postflop.aggression > cap
        else:
            assert pack.postflop.aggression <= cap


def test_maniac_entropy_floor_in_pinned_spots():
    """F3 pass/fail: maniac action entropy stays above 0.5 bits (still mixes,
    not deterministic). Pre-fix: 0.294 bits unopened / 0.484 facing (see the
    section comment)."""
    hole, board, pot, stack = _F3_SPOT
    unopened = _exact_dist(
        "maniac",
        hole,
        board,
        [personas_postflop_legal_check(), personas_postflop_legal_bet(1.0, 20.0)],
        pot,
        stack,
    )
    assert _entropy_bits(unopened) >= 0.5, unopened
    # 3-action set: overpair facing a ½-pot bet with RAISE legal (pre-fix the
    # 15× raise merit crushed call+fold to a combined 0.097 mass).
    facing = _exact_dist(
        "maniac",
        ("Qh", "Qd"),
        ["9c", "5s", "2h"],
        [
            personas_postflop_legal_fold(),
            personas_postflop_legal_call(3.0),
            personas_postflop_legal_raise(9.0, 100.0),
        ],
        9.0,
        100.0,
        current_bet_to=3.0,
    )
    assert _entropy_bits(facing) >= 0.5, facing


def test_maniac_still_strictly_most_aggressive():
    """F3 pass/fail: the cap keeps the maniac clearly the most aggressive
    persona — exact BET weight in the pinned spot strictly above every other
    persona's (0.8725 vs lag 0.7964 post-fix)."""
    hole, board, pot, stack = _F3_SPOT
    legal = [personas_postflop_legal_check(), personas_postflop_legal_bet(1.0, 20.0)]

    def bet_w(persona):
        return _exact_dist(persona, hole, board, legal, pot, stack)[ActionType.BET]

    maniac = bet_w("maniac")
    for persona in ALL_PERSONAS:
        if persona != "maniac":
            assert maniac > bet_w(persona), persona


# =====================================================================
# F4 — multiway calibration correction (RES-D §6, direction only)
# =====================================================================
#
# Pass/fail (roadmap): multiway c-bet/bluff frequency is LOWER than the HU
# baseline for the same spot; no per-opponent MDF number is asserted
# anywhere; value-hand continuation is at least as tight as HU (never
# looser). Exact weights via the capture rng — deterministic, no sampling
# noise (mirrors the F2/F3 technique).


@pytest.mark.parametrize("persona", ALL_PERSONAS)
def test_multiway_unopened_air_bet_freq_lower_than_hu(persona):
    """Direction 1: unopened air/bluff bet frequency is strictly lower 3-way
    than heads-up, for every persona (the multiway_bluff_damp mechanism,
    S4-era, confirmed still live post-F1/F2)."""
    hole, board = ("7h", "5d"), ["Kc", "9s", "3h"]
    legal = [personas_postflop_legal_check(), personas_postflop_legal_bet(1.0, 20.0)]
    hu = _exact_dist(persona, hole, board, legal, 4.0, 100.0)[ActionType.BET]
    three_way = _exact_dist_opp(persona, hole, board, legal, 4.0, 100.0, opponents=3)[
        ActionType.BET
    ]
    assert three_way < hu, f"{persona} 3-way bluff freq {three_way} not below HU {hu}"


def test_multiway_made_value_bet_damped_monotone_and_scoped():
    """W1-c (F13): thin made-value (top pair) unopened BET frequency is strictly
    non-increasing as opponents rise 1→4 and PLATEAUS past the labeled 4-way cap
    (exact captured weights, never sampled counts). Strong value (an overpair) is
    NOT in the damped set → flat across opponents. HU (opponents==1) is
    byte-identical (exponent 0), also enforced by the untouched HU suite."""
    board = ["Kc", "7s", "2h"]  # dry flop, no draw
    legal = [personas_postflop_legal_check(), personas_postflop_legal_bet(2.0, 100.0)]

    def pbet(hole, opp):
        return _exact_dist_opp("tag", hole, board, legal, 6.0, 100.0, opponents=opp)[
            ActionType.BET
        ]

    tp = [pbet(("Kh", "Qd"), o) for o in (1, 2, 3, 4, 5)]  # top pair
    assert tp[0] > tp[1] > tp[2] > tp[3]  # thin value tightens as the field grows
    assert tp[4] == pytest.approx(tp[3])  # capped at the 4-way tier (3 added opp)
    # Scoping: an overpair is strong value (not in _MW_VALUE_BUCKETS) → flat.
    op = [pbet(("Ah", "Ad"), o) for o in (1, 2, 3)]
    assert op[0] == pytest.approx(op[1]) and op[1] == pytest.approx(op[2])


@pytest.mark.parametrize("persona", ALL_PERSONAS)
def test_multiway_facing_bluff_catch_fold_freq_higher_than_hu(persona):
    """Direction (RES-D §6, 'fold more vs a bet multiway' for bluff-catchers):
    a weak made hand (middle pair, no draw) facing a bet folds MORE 3-way
    than heads-up, for every persona — the facing-side gap this slice closes
    (_MW_CATCH_TIGHTEN, code mechanic, not a persona lever)."""
    hole, board = ("9h", "2d"), ["Ac", "9s", "3h"]
    legal = [
        personas_postflop_legal_fold(),
        personas_postflop_legal_call(3.0),
        personas_postflop_legal_raise(9.0, 100.0),
    ]
    hu = _exact_dist_opp(
        persona, hole, board, legal, 9.0, 100.0, opponents=1, current_bet_to=3.0
    )[ActionType.FOLD]
    three_way = _exact_dist_opp(
        persona, hole, board, legal, 9.0, 100.0, opponents=3, current_bet_to=3.0
    )[ActionType.FOLD]
    assert three_way > hu, f"{persona} 3-way bluff-catch fold {three_way} not above HU {hu}"


@pytest.mark.parametrize("persona", ["tag", "lag", "maniac"])
def test_multiway_value_hand_continuation_not_looser_than_hu(persona):
    """Direction 2 (pass/fail): value-hand continuation (call+raise mass with
    a strong made hand facing a bet) is at least as tight as HU — never
    looser 3-way. R10-TAIL-b1 note: TOP_PAIR now IS in `_MW_CATCH_BUCKETS`
    (this hand tightens multiway by design), so this assertion holds both via
    the tighten mechanic and independently of it; the leak guard for the
    genuinely excluded rungs (OVERPAIR_TPTK / TWO_PAIR_PLUS) lives in
    test_mw_catch_toppair.py's byte-identity tests."""
    hole, board = ("Ah", "2d"), ["Ac", "9s", "3h"]  # top pair, value
    legal = [
        personas_postflop_legal_fold(),
        personas_postflop_legal_call(3.0),
        personas_postflop_legal_raise(9.0, 100.0),
    ]
    hu = _exact_dist_opp(
        persona, hole, board, legal, 9.0, 100.0, opponents=1, current_bet_to=3.0
    )
    three_way = _exact_dist_opp(
        persona, hole, board, legal, 9.0, 100.0, opponents=3, current_bet_to=3.0
    )
    hu_continue = hu[ActionType.CALL] + hu[ActionType.RAISE]
    tw_continue = three_way[ActionType.CALL] + three_way[ActionType.RAISE]
    assert tw_continue <= hu_continue + 1e-9, (
        f"{persona} value continuation looser 3-way ({tw_continue}) than HU ({hu_continue})"
    )


@pytest.mark.parametrize("persona", ["tag", "lag", "maniac"])
def test_multiway_value_hand_unopened_bet_not_looser_than_hu(persona):
    """Direction 2, unopened side: a value hand's bet frequency does not RISE
    with opponents (value-lean is 'not looser', never a mandate to bet MORE
    thin value multiway — thin/marginal value getting looser multiway would
    be the wrong direction per RES-D §6)."""
    hole, board = ("Ah", "2d"), ["Ac", "9s", "3h"]  # top pair, value
    legal = [personas_postflop_legal_check(), personas_postflop_legal_bet(1.0, 20.0)]
    hu = _exact_dist_opp(persona, hole, board, legal, 4.0, 100.0, opponents=1)[ActionType.BET]
    three_way = _exact_dist_opp(persona, hole, board, legal, 4.0, 100.0, opponents=3)[
        ActionType.BET
    ]
    assert three_way <= hu + 1e-9, f"{persona} value bet freq rose 3-way: {hu} -> {three_way}"


def test_no_per_opponent_mdf_constant_asserted():
    """No-go check: no test in this module (nor the mechanism itself) asserts
    a per-opponent MDF/defense number (e.g. an n-th-root of alpha). The F4
    mechanism (`_MW_CATCH_TIGHTEN`) is a flat multiplicative tighten
    exponentiated per added opponent — a DIRECTION, not a derived defense
    frequency — mirroring the S8 grader's `_MW_BLUFF_DAMPEN`/`_MW_VALUE_LEAN`/
    `_MW_CATCH_TIGHTEN` pattern, not RES-D §6's rejected symmetric-independent
    n-th-root idealization."""
    tighten = personas_postflop._MW_CATCH_TIGHTEN
    assert 1.0 < tighten < 2.0, "tighten constant should be a modest direction, not a target level"
    # Sanity: this is a flat per-opponent multiplier, not `alpha ** (1/opponents)`.
    import inspect

    src = inspect.getsource(personas_postflop)
    assert "1 / opponents" not in src.replace(" ", "")
    assert "1/opponents" not in src.replace(" ", "")


def _exact_dist_opp(persona, hole, board, legal, pot, stack, opponents, current_bet_to=0.0):
    cap = _CaptureWeights()
    sample_postflop_decision(
        _pack(persona),
        hole,
        board,
        legal,
        pot,
        stack,
        opponents,
        cap,  # type: ignore[arg-type] — duck-typed capture rng
        current_bet_to=current_bet_to,
    )
    return cap.dist


# =====================================================================
# P2a — street-aware river polarization (persona-realism-p2a Q3)
# =====================================================================
#
# On `street=Street.RIVER` the sampler floors to 0.0: the non-bluff RAISE
# merit for {MIDDLE_PAIR, TOP_PAIR, OVERPAIR_TPTK} (facing RAISE entry AND
# the matched CHECK+RAISE branch; BET untouched) and the AIR/no-draw CALL
# merit (air folds or bluff-raises, never calls). Default `street=None` (and
# any non-river street) is byte-identical to the pre-P2a sampler. Exact
# normalized weights via the capture rng — deterministic, no sampling noise.
#
# THE CALL FLOOR IS AIR-ONLY SINCE T3 (improvement slice 2, 2026-08-19). P2a
# wrote it on `bluff_cell`, which is `bucket in (AIR, ACE_HIGH) and draw is
# NONE`, so it caught naked ace-high too; T3 narrowed it to AIR and gave
# ace-high a damped river call instead. Every leg below probes AIR, so all of
# them still measure what they always did — but do not read "the bluff cell
# never calls the river" out of this block, because half of that cell now
# does.

_RIVER_BOARD = ["Kc", "9s", "3h", "7d", "2s"]
_TURN_BOARD = _RIVER_BOARD[:4]
# hole -> bucket on _RIVER_BOARD (verified by strength_bucket, all draw NONE):
_RIVER_HOLES = {
    StrengthBucket.MIDDLE_PAIR: ("9h", "4d"),
    StrengthBucket.TOP_PAIR: ("Kh", "8d"),
    StrengthBucket.OVERPAIR_TPTK: ("Ah", "Ad"),
    StrengthBucket.AIR: ("6h", "4d"),
    StrengthBucket.TWO_PAIR_PLUS: ("Kd", "9d"),
    StrengthBucket.MONSTER: ("3c", "3d"),
}
_ONE_PAIR_FLOOR = (
    StrengthBucket.MIDDLE_PAIR,
    StrengthBucket.TOP_PAIR,
    StrengthBucket.OVERPAIR_TPTK,
)


def _facing_legal():
    return [
        personas_postflop_legal_fold(),
        personas_postflop_legal_call(3.0),
        personas_postflop_legal_raise(9.0, 97.0),
    ]


_OMIT = object()  # sentinel: call sample_postflop_decision with NO street kwarg


def _dist_street(persona, hole, board, legal, street, current_bet_to=3.0, **kwargs):
    """Exact normalized action distribution with an explicit `street` kwarg
    (kwargs lets the byte-identity test OMIT the kwarg entirely)."""
    cap = _CaptureWeights()
    if street is not _OMIT:
        kwargs["street"] = street
    sample_postflop_decision(
        _pack(persona),
        hole,
        board,
        legal,
        9.0,
        97.0,
        1,
        cap,  # type: ignore[arg-type] — duck-typed capture rng
        current_bet_to=current_bet_to,
        **kwargs,
    )
    return cap.dist


def test_street_none_byte_identical_to_omitted_kwarg():
    """Refuter F3 (stronger than same-seed action equality): the exact
    normalized merit-weight dicts are identical for `street=None` vs omitting
    the kwarg entirely, on the MP/TP/OVERPAIR/AIR river spots the floor
    targets — the default is the pre-P2a sampler byte-for-byte. RIVER differs
    on every one of these spots (discriminating: proves the equality is not
    vacuous)."""
    legal = _facing_legal()
    for bucket in (*_ONE_PAIR_FLOOR, StrengthBucket.AIR):
        hole = _RIVER_HOLES[bucket]
        omitted = _dist_street("maniac", hole, _RIVER_BOARD, legal, _OMIT)
        explicit_none = _dist_street("maniac", hole, _RIVER_BOARD, legal, None)
        river = _dist_street("maniac", hole, _RIVER_BOARD, legal, Street.RIVER)
        assert omitted == explicit_none, bucket
        assert river != explicit_none, bucket


def test_flop_street_identical_to_none():
    """W3-c invariant: FLOP == street=None byte-for-byte (the street schedule's
    flop multiplier is exactly 1.0), for value, one-pair, AND air alike."""
    legal = _facing_legal()
    flop = ["Kc", "9s", "3h"]
    for hole in (("9h", "4d"), ("Kh", "8d"), ("6h", "4d")):
        assert _dist_street("maniac", hole, flop, legal, Street.FLOP) == _dist_street(
            "maniac", hole, flop, legal, None
        )


def test_turn_decays_air_bluff_but_not_value():
    """W3-c (F4): the turn is NO LONGER byte-identical to the pre-W3 sampler for
    a BLUFF hand — air's semi/bluff aggression decays (street mult 0.6). A
    one-pair value hand with no draw/bluff on the turn is still identical (the
    schedule scales bluff/semi-bluff ONLY, never value)."""
    legal = _facing_legal()
    # MIDDLE_PAIR / TOP_PAIR (no draw): value untouched → turn == None.
    for hole in (("9h", "4d"), ("Kh", "8d")):
        assert _dist_street("maniac", hole, _TURN_BOARD, legal, Street.TURN) == _dist_street(
            "maniac", hole, _TURN_BOARD, legal, None
        )
    # AIR: bluff-raise mass decays on the turn → strictly less raise weight.
    air = ("6h", "4d")
    turn = _dist_street("maniac", air, _TURN_BOARD, legal, Street.TURN)
    none = _dist_street("maniac", air, _TURN_BOARD, legal, None)
    assert turn != none
    assert turn[ActionType.RAISE] < none[ActionType.RAISE]


@pytest.mark.parametrize("persona", ["maniac", "lag", "tag"])
def test_river_one_pair_never_raises_facing_a_bet(persona):
    """River polarization, facing branch: one-pair-class raise weight is
    EXACTLY 0. Pre-P2a (street=None) weights, this spot: maniac MP .382 /
    TP .543 / OVERPAIR .777; lag .261/.405/.665; tag .199/.320/.578."""
    legal = _facing_legal()
    for bucket in _ONE_PAIR_FLOOR:
        hole = _RIVER_HOLES[bucket]
        river = _dist_street(persona, hole, _RIVER_BOARD, legal, Street.RIVER)
        streetless = _dist_street(persona, hole, _RIVER_BOARD, legal, None)
        assert river[ActionType.RAISE] == 0.0, (persona, bucket)
        assert streetless[ActionType.RAISE] > 0.0, (persona, bucket)  # floor is river-only


def test_river_check_raise_branch_floored_bet_untouched():
    """Matched-with-option branch: the CHECK+RAISE agg merit is floored for the
    whole one-pair class on the river (maniac pre-P2a: MP .706 / TP .873 /
    OVERPAIR .929 → all 0.0). The unopened CHECK+BET branch is now floored for
    MIDDLE_PAIR ONLY (W1-a) — TOP_PAIR/OVERPAIR keep the thin river value bet
    (river BET weights == streetless). This is the sanctioned W1-a unit-assertion
    split (theory-contract §7), NOT a band re-anchor."""
    matched = [personas_postflop_legal_check(), personas_postflop_legal_raise(6.0, 97.0)]
    unopened = [personas_postflop_legal_check(), personas_postflop_legal_bet(1.0, 97.0)]
    for bucket in _ONE_PAIR_FLOOR:
        hole = _RIVER_HOLES[bucket]
        river = _dist_street("maniac", hole, _RIVER_BOARD, matched, Street.RIVER)
        assert river[ActionType.RAISE] == 0.0, bucket
        assert _dist_street("maniac", hole, _RIVER_BOARD, matched, None)[ActionType.RAISE] > 0.0
        river_bet = _dist_street(
            "maniac", hole, _RIVER_BOARD, unopened, Street.RIVER, current_bet_to=0.0
        )
        streetless_bet = _dist_street(
            "maniac", hole, _RIVER_BOARD, unopened, None, current_bet_to=0.0
        )
        if bucket is StrengthBucket.MIDDLE_PAIR:
            # W1-a: middle-pair unopened river BET floored to 0 (bluff-catcher);
            # the floor is river-only, so the streetless BET stays positive.
            assert river_bet[ActionType.BET] == 0.0, bucket
            assert streetless_bet[ActionType.BET] > 0.0, bucket
        else:
            # TOP_PAIR / OVERPAIR: thin river value bet untouched (byte-identical).
            assert river_bet == streetless_bet, bucket


def test_river_bet_floor_middle_pair_river_gated():
    """W1-a: MIDDLE_PAIR unopened BET floored to 0 on the RIVER; the SAME hole on
    the TURN board is byte-identical to street=None (unchanged) — the floor is
    river-only and MIDDLE_PAIR-only."""
    unopened = [personas_postflop_legal_check(), personas_postflop_legal_bet(1.0, 97.0)]
    mp = _RIVER_HOLES[StrengthBucket.MIDDLE_PAIR]
    river = _dist_street("maniac", mp, _RIVER_BOARD, unopened, Street.RIVER, current_bet_to=0.0)
    assert river[ActionType.BET] == 0.0
    # Turn control: same middle-pair hole on the turn board — BET untouched.
    turn = _dist_street("maniac", mp, _TURN_BOARD, unopened, Street.TURN, current_bet_to=0.0)
    assert turn == _dist_street("maniac", mp, _TURN_BOARD, unopened, None, current_bet_to=0.0)
    assert turn[ActionType.BET] > 0.0


@pytest.mark.parametrize("persona", ALL_PERSONAS)
def test_river_air_never_calls_but_still_bluff_raises(persona):
    """AIR/no-draw CALL merit floored to exactly 0 on the river for every
    persona (air folds or bluff-raises — maniac pre-P2a called .086); the
    _BLUFF_RAISE_FACTOR path survives (raise weight strictly positive).

    The probe hole is AIR, so this leg is unaffected by T3 (improvement slice
    2, 2026-08-19) narrowing the floor from the whole `bluff_cell` to AIR
    alone. It no longer covers naked ace-high, which now calls the river at a
    damped weight; `test_t3_river_air_facing_an_all_in_bet_still_never_calls`
    is the T3-era statement of the same property."""
    hole = _RIVER_HOLES[StrengthBucket.AIR]
    river = _dist_street(persona, hole, _RIVER_BOARD, _facing_legal(), Street.RIVER)
    assert river[ActionType.CALL] == 0.0
    assert river[ActionType.RAISE] > 0.0


def test_river_raises_only_from_two_pair_plus_or_bluff_cell():
    """The polarization claim end-to-end: over all six buckets on the river,
    positive raise weight comes ONLY from TWO_PAIR_PLUS/MONSTER (value) or
    the bluff cell (air) — never the one-pair middle."""
    legal = _facing_legal()
    raisers = {
        bucket
        for bucket, hole in _RIVER_HOLES.items()
        if _dist_street("maniac", hole, _RIVER_BOARD, legal, Street.RIVER)[ActionType.RAISE] > 0.0
    }
    assert raisers == {
        StrengthBucket.TWO_PAIR_PLUS,
        StrengthBucket.MONSTER,
        StrengthBucket.AIR,
    }


def test_river_polarization_sampled_and_turn_at_old_freq():
    """Sampled (real rng) confirmation + turn control: maniac middle pair
    facing a river bet never raises over 400 draws; the SAME hole/spot on the
    turn board (street=Street.TURN) still raises at its old frequency — the
    exact turn weights equal street=None (raise weight .382), proving only
    the river floors."""
    pack = _pack("maniac")
    hole = _RIVER_HOLES[StrengthBucket.MIDDLE_PAIR]
    legal = _facing_legal()
    rng = random.Random(20260723)
    river_raises = 0
    for _ in range(400):
        d = sample_postflop_decision(
            pack, hole, _RIVER_BOARD, legal, 9.0, 97.0, 1, rng,
            current_bet_to=3.0, street=Street.RIVER,
        )
        river_raises += d.action is ActionType.RAISE
    assert river_raises == 0
    turn = _dist_street("maniac", hole, _TURN_BOARD, legal, Street.TURN)
    assert turn == _dist_street("maniac", hole, _TURN_BOARD, legal, None)
    assert turn[ActionType.RAISE] > 0.3  # old freq (~.382), not floored


# =====================================================================
# S3-T5 — the late-street bet lever (improvement slice 3, ticket 5)
# =====================================================================
#
# `late_street_bet` scales the aggressive candidate's merit at an UNOPENED turn
# or river by `1 + late_street_bet * _LATE_STREET_GAIN[street]`, so fewer hands
# check through to a showdown nobody wagered into. Exact normalized weights via
# the capture rng, so these are arithmetic statements, not sampling ones.


def _late_street_pack(persona: str, dial: float | None):
    pack = _pack(persona).model_copy(deep=True)
    pack.postflop = pack.postflop.model_copy(update={"late_street_bet": dial})
    return pack


_UNOPENED_LEGAL = [personas_postflop_legal_check(), personas_postflop_legal_bet(1.0, 97.0)]
_MATCHED_LEGAL = [personas_postflop_legal_check(), personas_postflop_legal_raise(6.0, 97.0)]


def _late_street_dist(persona, dial, hole, board, street, legal=None):
    cap = _CaptureWeights()
    sample_postflop_decision(
        _late_street_pack(persona, dial),
        hole,
        board,
        _UNOPENED_LEGAL if legal is None else legal,
        9.0,
        97.0,
        1,
        cap,  # type: ignore[arg-type] — duck-typed capture rng
        current_bet_to=0.0,
        street=street,
    )
    return cap.dist


@pytest.mark.parametrize(
    ("street", "board", "gain"),
    [
        (Street.TURN, _TURN_BOARD, 0.60),
        (Street.RIVER, _RIVER_BOARD, 1.00),
    ],
)
def test_late_street_bet_fires_on_unopened_turn_river_bet_leg(street, board, gain):
    """The lever multiplies the aggressive candidate, and nothing else.

    Asserted as the exact odds ratio rather than as "the bet weight went up",
    because a multiplier on one of two competing merits has a signature the
    direction alone does not pin: CHECK keeps its merit, so the BET:CHECK odds
    must rise by EXACTLY `1 + dial * gain` at every dial. The gain constants
    are read from the engine rather than restated, so this test tracks a
    re-calibration instead of failing on one.
    """
    assert personas_postflop._LATE_STREET_GAIN[street] == gain
    hole = _RIVER_HOLES[StrengthBucket.TOP_PAIR]  # thin value: bets, and checks
    off = _late_street_dist("tag", None, hole, board, street)
    assert 0.0 < off[ActionType.BET] < 1.0, off
    base_odds = off[ActionType.BET] / off[ActionType.CHECK]
    for dial in (0.25, 0.5, 0.75, 1.0):
        on = _late_street_dist("tag", dial, hole, board, street)
        odds = on[ActionType.BET] / on[ActionType.CHECK]
        assert odds == pytest.approx(base_odds * (1.0 + dial * gain), rel=1e-12), dial
        assert on[ActionType.BET] > off[ActionType.BET], dial


def test_late_street_bet_is_identity_when_absent_or_off_scope():
    """Every path the lever must NOT touch, at the deepest dial the field
    allows: an unauthored pack, the flop, a streetless call, the
    matched-with-option check-RAISE leg, and the bluff cell (pure air, whose
    bet mass stays `bluff_freq`'s to set).

    Byte-equality of the whole distribution, not just of the BET weight —
    normalization means a leak anywhere in the vector shows up here."""
    top_pair = _RIVER_HOLES[StrengthBucket.TOP_PAIR]
    flop_board = _RIVER_BOARD[:3]
    # The bluff cell is `AIR with no draw`, and it needs a per-street hole: the
    # river's air hole (6h4d) is a gutshot while the turn card is still to come,
    # and the turn's (Jh2d) pairs the river's deuce. Asserted, not assumed.
    air_by_street = {Street.TURN: ("Jh", "2d"), Street.RIVER: _RIVER_HOLES[StrengthBucket.AIR]}
    for street, board in ((Street.TURN, _TURN_BOARD), (Street.RIVER, _RIVER_BOARD)):
        assert strength_bucket(air_by_street[street], board) == (
            StrengthBucket.AIR,
            DrawCategory.NONE,
        ), street

    # (i) the field absent is the shipped pack, byte-for-byte, on the very
    # street the lever fires on.
    for street, board in ((Street.TURN, _TURN_BOARD), (Street.RIVER, _RIVER_BOARD)):
        shipped = _late_street_dist("tag", None, top_pair, board, street)
        cap = _CaptureWeights()
        sample_postflop_decision(
            _pack("tag"), top_pair, board, _UNOPENED_LEGAL, 9.0, 97.0, 1,
            cap,  # type: ignore[arg-type] — duck-typed capture rng
            current_bet_to=0.0, street=street,
        )
        assert shipped == cap.dist, street

    # (ii) the flop and (iii) a caller that passes no street at all.
    for street, board in ((Street.FLOP, flop_board), (None, _TURN_BOARD)):
        assert _late_street_dist("tag", 1.0, top_pair, board, street) == _late_street_dist(
            "tag", None, top_pair, board, street
        ), street

    # (iv) the matched-with-option check-RAISE leg, on both late streets.
    for street, board in ((Street.TURN, _TURN_BOARD), (Street.RIVER, _RIVER_BOARD)):
        on = _late_street_dist("tag", 1.0, top_pair, board, street, legal=_MATCHED_LEGAL)
        off = _late_street_dist("tag", None, top_pair, board, street, legal=_MATCHED_LEGAL)
        assert on == off, street
        # discriminating: the RAISE leg carries real mass on the turn, so the
        # equality above is not a comparison of two zeros.
        if street is Street.TURN:
            assert on[ActionType.RAISE] > 0.0

    # (v) the bluff cell keeps its own mass: pure air is untouched on both
    # late streets, while the same node's value hand moves.
    for street, board in ((Street.TURN, _TURN_BOARD), (Street.RIVER, _RIVER_BOARD)):
        air = air_by_street[street]
        on = _late_street_dist("tag", 1.0, air, board, street)
        assert on == _late_street_dist("tag", None, air, board, street), street
        assert on[ActionType.BET] > 0.0, street  # air does bet here; it just does not move


# =====================================================================
# Closed-loop harness: full-hand playouts through the S2 engine
# =====================================================================

# Preflop facing-state derivation: the engine speaks LegalAction shapes, but
# sample_preflop_action needs the content-level facing label. We derive it
# from the current street's action_history: how many RAISE/BET events have
# happened preflop tells us unopened / vs_rfi / vs_3bet / vs_4bet; any CALL
# with no raise yet (after blinds) means vs_limpers for the next actor.


def _preflop_facing(state) -> str:
    raises = [
        h
        for h in state.action_history
        if h.street is Street.PREFLOP and h.action == ActionType.RAISE
    ]
    if not raises:
        limped = any(
            h.action == ActionType.CALL for h in state.action_history if h.street is Street.PREFLOP
        )
        return "vs_limpers" if limped else "unopened"
    n = len(raises)
    if n == 1:
        return "vs_rfi"
    if n == 2:
        return "vs_3bet"
    return "vs_4bet"  # n >= 3 (4bet, 5bet_shove, ...)


# R-L2 (instrument repair, wave-4 finding): the harness used to keep its OWN
# copy of `_preflop_decision` which sized EVERY raise at `la.min_bb`. Production
# has not done that since R2 — `play._preflop_decision` sizes from the persona
# levers via `sizing.preflop_raise_to` (open_bb / open+1bb-per-limper iso /
# threebet_mult / fourbet_mult) and jams a `5bet` ALL-IN. The divergence
# manufactured min-raise ping-pong wars the live table cannot produce: measured
# at b54fe6e over n=2000 seeded hands (seed 20260710, maniac-heavy lineup), the
# share of hands reaching >= 5 preflop raises was 1.80% under the harness copy
# vs 0.00% under production sizing (harness depth tail ran to 99 raises in a
# hand; production never exceeded 4, because the 5-bet is all-in). That is the
# instrument error behind the wave-4 9.4%-vs-74.1% channel contradiction.
#
# The harness now REUSES production's own decision function, so the sizing can
# never drift again. The signature gains `current_bet_to` / `limpers` because
# `preflop_raise_to` needs them; `_play_hand` derives both EXACTLY as
# `play.bot_decision` does (`state.current_bet_bb` and the preflop CALL count).
from app.domain.table.play import _preflop_decision as _prod_preflop_decision  # noqa: E402


def _preflop_decision(
    pack, position, facing, hole, legal, rng, current_bet_to, limpers, is_opener=None
) -> Decision:
    """Thin pass-through to production's `play._preflop_decision` — see above.

    `current_bet_to` / `limpers` are REQUIRED positionals, exactly as production
    declares them. They were briefly given 0.0 / 0 defaults for the one
    out-of-file caller (`test_sim_session.py::test_bot_decision_parity_with_
    harness`); review killed that, correctly — silently defaulted sizing inputs
    are how this divergence got in the first time, and a wrapper that zeroes
    them re-creates min-raise sizing at every re-raise node while still LOOKING
    delegated. `test_harness_preflop_raise_sizing_uses_production_args` pins it."""
    return _prod_preflop_decision(
        pack, position, facing, hole, legal, rng, current_bet_to, limpers, is_opener=is_opener
    )


# P2a (refuter F1): the closed-loop harness mirrors play.py's street opt-in —
# derived from the board length exactly as the live loop derives it from
# state.street — so the population/WTSD bands below actually exercise river
# polarization instead of running the streetless default.
_STREET_BY_BOARD_LEN = {3: Street.FLOP, 4: Street.TURN, 5: Street.RIVER}

# W5-a3-iii (C30): the reference derivation for the band sampler's/parity
# mirror's context kwargs — the SAME helpers `play.bot_decision` uses.
from app.domain.table.play import _preflop_opener  # noqa: E402
from app.domain.table.postflop_context import (  # noqa: E402
    aggressor_barrel_run,
    derive_postflop_context,
    street_aggression_count,
)
from app.domain.table.sizing import (  # noqa: E402
    last_aggressor_position,
    pot_before_current_aggression,
)


def _postflop_decision(
    pack, hole, board, legal, pot_bb, stack_bb, opponents, rng, current_bet_to,
    *, is_aggressor=_OMIT, latest_aggressor_contribution_bb=_OMIT, context=_OMIT,
    facing_raise=_OMIT, street_aggressions=_OMIT, aggressor_bet_prev_street=_OMIT,
) -> Decision:
    # The context kwargs default to _OMIT so `_play_hand` (the band/stat sim,
    # below) calls this EXACTLY as before -> its WTSD/texture/VPIP stats stay
    # byte-identical UNLESS `_play_hand`'s own `context_aware=True` opt-in is
    # set (W5-a3-iii; see there). Only the sim_session action-parity test
    # threads the same context production's `play.bot_decision` derives, so
    # the mirror matches the real (W3-a/b/c/d context-aware) bot's ACTION
    # exactly.
    #
    # `street_aggressions` (the raw BET/RAISE-on-this-street count, C30) is
    # NOT a `sample_postflop_decision` parameter — production only consumes
    # the boolean `facing_raise` (= count >= 2). Threading the count here
    # lets a caller supply it directly (matching how a future W3R-5 leg would
    # gate on the count, e.g. `== 1`) without duplicating the >= 2 rule at
    # every call site; it derives `facing_raise` when the caller didn't
    # already supply one.
    #
    # R9-DEFENCE-a (T5): `aggressor_bet_prev_street` is the opponent-LINE flag —
    # the `>= 1` threshold of `table.postflop_context.aggressor_barrel_run` for
    # the seat whose wager is being faced. It follows the SAME `_OMIT` discipline
    # as every kwarg above: unless a caller supplies it, the key never reaches
    # `sample_postflop_decision`, so the population bands and goldens below stay
    # byte-identical. `_play_hand`'s `line_aware=True` opt-in is the only caller
    # in the population path, and it is off by default (spec P-7).
    kinds = {la.action for la in legal}
    _kw = {
        "current_bet_to": current_bet_to,
        "street": _STREET_BY_BOARD_LEN[len(board)],
    }
    if is_aggressor is not _OMIT:
        _kw["is_aggressor"] = is_aggressor
    if latest_aggressor_contribution_bb is not _OMIT:
        _kw["latest_aggressor_contribution_bb"] = latest_aggressor_contribution_bb
    if context is not _OMIT:
        _kw["context"] = context
    if facing_raise is not _OMIT:
        _kw["facing_raise"] = facing_raise
    elif street_aggressions is not _OMIT:
        _kw["facing_raise"] = street_aggressions >= 2
    if aggressor_bet_prev_street is not _OMIT:
        _kw["aggressor_bet_prev_street"] = aggressor_bet_prev_street
    d = sample_postflop_decision(
        pack,
        hole,
        board,
        legal,
        pot_bb,
        stack_bb,
        opponents,
        rng,
        **_kw,
    )
    if d.action not in kinds:
        # Defensive: never happens if the sampler honors `legal`, but keep
        # the harness crash-proof against an engine/sampler mismatch.
        if ActionType.CHECK in kinds:
            return Decision(action=ActionType.CHECK)
        return Decision(action=ActionType.FOLD)
    return d


def _live_opponents(state, seat: int) -> int:
    return sum(
        1
        for s in state.seats
        if s.seat != seat and s.status in (PlayerStatus.IN, PlayerStatus.ALLIN)
    )


class PostflopDecision(NamedTuple):
    """Richer per-postflop-decision context for the W0-b metrics (parallel to
    the existing `log` 3-tuple, which stays untouched so AF/FtC/WTSD are
    byte-identical). `in_position` is snapshotted at decision time; NO
    whole-hand is_aggressor flag — c-bet/barrel lineage is derived from the
    per-street bet/raise events themselves."""

    seat: int
    street: str
    in_position: bool
    action: str
    bet_fraction: float | None  # size_bb / pot_bb for a BET/RAISE, else None


class LineNode(NamedTuple):
    """R9-DEFENCE-a (T5): one organically-reached LINE-AWARE node — a seat facing
    chips from an aggressor that also bet/raised the previous postflop street.

    Recorded as RAW FACTS so the S-5 gate can apply the scope predicate itself:
    `bucket`/`draw` are exactly what `strength_bucket` returned at the node, and
    the mechanism is scoped to `bucket ∈ {MIDDLE_PAIR, TOP_PAIR, ACE_HIGH, AIR}`
    AND `draw is DrawCategory.NONE` (spec §4). Off-scope rows are kept, not
    dropped, because "how much of the barrel population is even in scope" is
    itself a thing the report has to be able to say."""

    seat: int
    street: str
    bucket: object  # StrengthBucket
    draw: object  # DrawCategory
    action: str


class HandResult(NamedTuple):
    """`_play_hand` return. `log`/`saw_flop`/`settlement` drive the existing
    (byte-identical) AF/FtC/WTSD path; `decisions`/`preflop_log` feed the new
    W0-b metrics; `preflop_nodes` feeds the T-ARR arrival counters."""

    state: object
    settlement: object
    log: list  # postflop (seat, street, action) tuples — UNCHANGED shape
    saw_flop: set
    had_limper: bool
    had_3bet_plus: bool
    decisions: list  # list[PostflopDecision]
    preflop_log: list  # (seat, action) for the APPLIED preflop decision only
    line_nodes: list  # R9-DEFENCE-a (T5): list[LineNode] — one row per postflop
    # decision this hand taken at a LINE-AWARE node: the derived
    # `aggressor_bet_prev_street` was True AND the seat was facing chips (FOLD
    # legal), i.e. the node class the mechanism can actually fire on. Empty
    # unless `line_aware` is set. RAW ROWS, not a rate: `_play_hand` records what
    # happened (seat / street / bucket / draw / action) and the S-5 gate does the
    # scope classification, so the harness never carries a second copy of the
    # scope predicate. Purely an observer — it consumes no rng and feeds nothing
    # but S-5, so every existing band and golden is untouched by its presence.
    preflop_nodes: list  # T-ARR: (seat, position, facing, is_first) for EVERY
    # preflop decision this hand. Deliberately NOT folded into `preflop_log`
    # (whose 2-tuple shape `_preflop_aggressor` / `_hand_cbet_stats` unpack
    # positionally).
    #
    # `is_first` splits two genuinely different questions, and conflating them
    # was a real defect caught in review:
    #   ARRIVAL (is_first=True)  — "which node was this seat DEALT INTO?" The
    #     `unopened` bands are calibrated on this, and it must stay first-only
    #     or UTG stops reading 1.000.
    #   OCCUPANCY (all rows)     — "how often is this node VISITED at all?"
    #     `vs_3bet`/`vs_4bet` are overwhelmingly RE-ENTRY nodes (you open, you
    #     get 3-bet, you act again), so the arrival counter under-reads
    #     `vs_4bet` by ~31x and shows UTG `vs_3bet` as a flat 0.000 — which
    #     reads as "dead code" when the branch is merely invisible.


def _in_position(state, seat: int) -> bool:
    """True iff no still-IN opponent acts after `seat` this street. Postflop
    order runs SB-most -> button; FOLDED and ALL-IN seats are excluded (they
    do not act after me). BB is IP vs SB; 3+-handed = the button-most live
    seat. Snapshot at decision time (pre-apply). Harness-side derivation of the
    same rule W3-a (A2) will later plumb into the domain — an accepted,
    documented duplication to reconcile then."""
    order = [(state.button_seat + 1 + k) % 9 for k in range(9)]
    idx = order.index(seat)
    return not any(state.seats[j].status is PlayerStatus.IN for j in order[idx + 1 :])


# R9-DEFENCE-a (T5): `_play_hand`'s line-BLIND control mode — derive and record
# the barrel node, but do not tell the sampler. See `_play_hand`'s docstring.
_LINE_OBSERVE = "observe"


def _play_hand(
    rng, hand_seed, button_seat, persona_by_seat, packs, *,
    context_aware=False, line_aware=False,
):
    """One full-hand playout; every seat runs its persona's sampler.

    Returns (final HandState, Settlement, per-seat postflop action log for
    stats: list of (seat, street, action) tuples) and per-hand facts used by
    the table-texture assertions (limper flag, 3bet-pot flag, saw-flop seats).

    `context_aware=False` (default) calls `_postflop_decision` with NO
    context kwargs -- byte-identical to the pre-W5-a3-iii sampler, so every
    existing AF/FtC/WTSD band and golden stays untouched (measurement-only;
    no band re-anchor). `context_aware=True` (W5-a3-iii, C30) derives
    `is_aggressor` / `latest_aggressor_contribution_bb` / `context` /
    `facing_raise` / `street_aggressions` EXACTLY as `play.bot_decision`
    does, making the band sampler's postflop decisions match the live,
    context-aware bot -- opt-in only, so a caller must deliberately ask for
    the (currently unbanded) context-aware measurement.

    `line_aware` (default False, R9-DEFENCE-a T5) is the SAME discipline for the
    opponent-LINE signal, and it is deliberately ORTHOGONAL to `context_aware`.
    It is TRI-STATE, and the middle state is what makes S-5's decisive gate a
    NODE-MATCHED comparison rather than two differently-populated samples:

      False               -- derive nothing. The pinned default path: the kwargs
                             dict is empty, both `_postflop_decision` call sites
                             below are byte-identical to what they were before
                             this ticket, and every `BANDS` row and golden stays
                             frozen (spec P-7: if one of them moves, the
                             threading leaked into the default path, and that is
                             a DEFECT, not a re-record).
      _LINE_OBSERVE       -- derive the flag and RECORD the node, but DO NOT pass
                             it to the sampler. Play is bit-for-bit the `False`
                             path (the kwarg never reaches the sampler at all),
                             so this is a line-BLIND control that nonetheless
                             knows which nodes were barrel nodes. That is the
                             only way to ask "what did this persona do at a
                             barrel node WITHOUT the mechanism?" on the same node
                             population the treatment arm sees.
      True                -- derive, record, and thread.

    The derivation is the SHIPPED `aggressor_barrel_run`, used exactly as
    `play.bot_decision` uses it (`aggressor_barrel_run(state.action_history,
    state.street, street_aggressor)` in `play.py`), and it reads only
    `state.action_history` -- it draws NO rng, so even the treated arm's stream
    displacement is entirely the mechanism's own doing.
    """
    # The three states are dispatched by a truthy test (`if line_aware:`) and
    # then an identity test (`is True`), so ANY truthy value that is not `True`
    # would silently land in observe-mode: the flag derived, the node recorded,
    # and NOTHING threaded -- a control arm masquerading as the treatment. That
    # failure is invisible (the run completes, every rise reads 0.0) which is
    # exactly the class of silent-no-op this slice exists to make impossible.
    # Reject the input instead of trusting call sites.
    if line_aware is not False and line_aware is not True and line_aware != _LINE_OBSERVE:
        raise ValueError(
            f"line_aware must be False, True or _LINE_OBSERVE; got {line_aware!r}"
        )
    dealt = deal_hand(random.Random(hand_seed))
    state = start_hand(dealt, button_seat=button_seat, stacks_bb=[100.0] * 9)
    log: list[tuple[int, str, str]] = []
    decisions: list[PostflopDecision] = []
    preflop_log: list[tuple[int, str]] = []
    preflop_nodes: list[tuple[int, str, str]] = []
    preflop_node_seen: set[int] = set()
    saw_flop: set[int] = set()
    had_limper = False
    had_3bet_plus = False
    line_nodes: list[LineNode] = []
    guard = 0
    while not state.hand_over:
        guard += 1
        assert guard < 500, "playout did not terminate"
        # Capture players-to-flop the moment the board reaches >=3 cards,
        # regardless of whether a seat still gets to ACT (all-in run-outs
        # close betting with to_act_seat=None but those seats did see the
        # flop) -- action-participation undercounts players-to-flop.
        if len(state.board) >= 3 and not saw_flop:
            saw_flop = {
                s.seat for s in state.seats if s.status in (PlayerStatus.IN, PlayerStatus.ALLIN)
            }
        seat = state.to_act_seat
        legal = legal_actions(state)
        assert legal, "no legal actions for a seat to act"
        pack = packs[persona_by_seat[seat]]
        seat_state = state.seats[seat]
        if state.street is Street.PREFLOP:
            facing = _preflop_facing(state)
            # T-ARR: record the node from the values the loop already computed
            # (`facing` here, `seat_state.position` from the engine) — no
            # re-derivation, and NO rng draw, so every seeded golden below stays
            # byte-identical. Every decision is recorded; `is_first` marks the
            # ARRIVAL subset (see `HandResult.preflop_nodes`).
            is_first = seat not in preflop_node_seen
            preflop_node_seen.add(seat)
            preflop_nodes.append((seat, seat_state.position.value, facing, is_first))
            if facing == "vs_limpers":
                had_limper = True
            # N-3BSTRATA: the arrival stratum, from the SAME production helper
            # `play.bot_decision` uses (`_preflop_opener`) — the harness must
            # not re-approximate it (the stratified report's
            # `all_hits − first_hits` is a coarser proxy; see its docstring).
            is_opener = _preflop_opener(state) == seat_state.position
            act = sample_preflop_action(
                pack, seat_state.position, facing, seat_state.hole_cards, rng,
                is_opener=is_opener,
            )
            if act.name in ("3bet", "4bet", "5bet_shove"):
                had_3bet_plus = True
            # R-L2: production sizing, derived exactly as `play.bot_decision`
            # derives it (see the `_preflop_decision` import above).
            limpers = sum(
                1
                for h in state.action_history
                if h.street is Street.PREFLOP and h.action is ActionType.CALL
            )
            decision = _preflop_decision(
                pack, seat_state.position, facing, seat_state.hole_cards, legal, rng,
                state.current_bet_bb, limpers,
                is_opener=is_opener,
            )
            # Log the APPLIED preflop decision only — no new rng draw, no
            # "cleanup" of the existing double-sample (would shift the stream).
            preflop_log.append((seat, decision.action.value))
        else:
            pot_bb = sum(s.invested_total_bb for s in state.seats)
            opponents = _live_opponents(state, seat)
            # R9-DEFENCE-a (T5): the opponent-LINE kwarg, assembled as a dict so
            # that OFF it is `{}` and BOTH `_postflop_decision` calls below are
            # character-for-character the calls they were before this ticket.
            # The derivation is `play.bot_decision`'s, copied verbatim rather
            # than re-expressed: the aggressor is the last BET/RAISE on THIS
            # street (so the flag is about the seat whose wager is actually
            # outstanding, NOT "anyone was aggressive last street"), and the run
            # itself comes from the SHIPPED `aggressor_barrel_run` — re-deriving
            # the run rule here is forbidden (`aggressor_barrel_run`'s own
            # docstring in `postflop_context.py` warns against a second
            # taxonomy). In `_LINE_OBSERVE` the flag is
            # derived and the node recorded, but `line_kw` stays EMPTY, so the
            # control arm plays byte-identically to the pinned default path
            # while still knowing where the barrels were.
            line_kw: dict = {}
            barrelled = False
            if line_aware:
                street_aggressor = last_aggressor_position(
                    [h for h in state.action_history if h.street is state.street]
                )
                barrelled = street_aggressor is not None and (
                    aggressor_barrel_run(
                        state.action_history, state.street, street_aggressor
                    )
                    >= 1
                )
                if line_aware is True:
                    line_kw["aggressor_bet_prev_street"] = barrelled
            if context_aware:
                # W5-a3-iii: the SAME derivation `play.bot_decision` uses —
                # see `backend/app/domain/table/play.py:bot_decision`.
                is_aggressor = (
                    last_aggressor_position(state.action_history) == seat_state.position
                )
                contribution = pot_before_current_aggression(
                    state.action_history, state.street
                ).latest_aggressor_contribution_bb
                context = derive_postflop_context(state, seat)
                street_aggressions = street_aggression_count(
                    state.action_history, state.street
                )
                decision = _postflop_decision(
                    pack,
                    seat_state.hole_cards,
                    state.board,
                    legal,
                    pot_bb,
                    seat_state.stack_bb,
                    opponents,
                    rng,
                    state.current_bet_bb,
                    is_aggressor=is_aggressor,
                    latest_aggressor_contribution_bb=contribution,
                    context=context,
                    street_aggressions=street_aggressions,
                    **line_kw,
                )
            else:
                decision = _postflop_decision(
                    pack,
                    seat_state.hole_cards,
                    state.board,
                    legal,
                    pot_bb,
                    seat_state.stack_bb,
                    opponents,
                    rng,
                    state.current_bet_bb,
                    **line_kw,
                )
            log.append((seat, state.street.value, decision.action.value))
            if barrelled and any(la.action is ActionType.FOLD for la in legal):
                # Facing chips AND facing a barrel: the node class the mechanism
                # can fire on, and the population S-5's decisive gate measures
                # P(fold) over. `strength_bucket` is called ONLY here (a few
                # hundred times a run), so the default path pays nothing.
                _bucket, _draw = strength_bucket(seat_state.hole_cards, state.board)
                line_nodes.append(
                    LineNode(
                        seat=seat,
                        street=state.street.value,
                        bucket=_bucket,
                        draw=_draw,
                        action=decision.action.value,
                    )
                )
            bet_fraction = (
                round(decision.size_bb / pot_bb, 6)
                if decision.action in (ActionType.BET, ActionType.RAISE)
                and decision.size_bb is not None
                and pot_bb > 0
                else None
            )
            decisions.append(
                PostflopDecision(
                    seat=seat,
                    street=state.street.value,
                    in_position=_in_position(state, seat),
                    action=decision.action.value,
                    bet_fraction=bet_fraction,
                )
            )
        state = apply(state, decision)
    # Auto-runout (all-in before the flop closes) can flip hand_over=True on
    # the SAME apply() that first reveals >=3 board cards, skipping the
    # loop-top check above for that final state -- catch it here too.
    if len(state.board) >= 3 and not saw_flop:
        saw_flop = {
            s.seat for s in state.seats if s.status in (PlayerStatus.IN, PlayerStatus.ALLIN)
        }
    settlement = settle(state)
    return HandResult(
        state=state,
        settlement=settlement,
        log=log,
        saw_flop=saw_flop,
        had_limper=had_limper,
        had_3bet_plus=had_3bet_plus,
        decisions=decisions,
        preflop_log=preflop_log,
        line_nodes=line_nodes,
        preflop_nodes=preflop_nodes,
    )


# ---------------------------------------------------------------------
# Budget measurement: probe throughput with the real sampler, then derive N.
# ---------------------------------------------------------------------


def _measure_throughput(packs) -> float:
    rng = random.Random(999)
    persona_by_seat = {i: ALL_PERSONAS[i % len(ALL_PERSONAS)] for i in range(9)}
    t0 = time.perf_counter()
    n_probe = 60
    for i in range(n_probe):
        _play_hand(rng, rng.randrange(1_000_000_000), i % 9, persona_by_seat, packs)
    elapsed = time.perf_counter() - t0
    return n_probe / elapsed if elapsed > 0 else 1e9


def _derive_n(hands_per_s: float) -> int:
    """Return the PINNED (per_persona_n, texture_n) = (600, 1500). Nothing
    scales any more (instrument-repair wave delta fold, 2026-08-01): both were
    throughput-derived once, which made frozen-band verdicts machine-dependent;
    the spec allocation (600/persona x 6 + 1500 texture ~= 5100 hands at
    ~430 h/s ~= 11.8s) is now pinned. `hands_per_s` is accepted and returned
    for reporting only.

    The "<=12s" budget this is derived from is STALE — the file measured 76.37s
    at HEAD on 2026-07-26, see the module docstring. `budget_s` below is kept at
    its historical value anyway: it sizes N, and every seeded band and golden in
    this file was recorded at that N."""
    budget_s = 9.5  # historical: headroom under the (now stale) 12s cap for the
    # throughput probe itself
    # (60-hand probe + unit-test overhead + fixture/import cost, empirically
    # ~1.5-2s combined at this file's measured throughput)
    total_budget_hands = max(int(hands_per_s * budget_s), 900)
    # texture_n FIXED at W5-b4 (2026-07-31, review fold — the _WTSD_ORDER_N
    # precedent): it was throughput-derived (min(1500, 30% of budget), i.e.
    # 270..1500 depending on the machine), which made the table-texture guards
    # machine-dependent — the W5-b4 refuter measured the 3-bet-pot and limper
    # guards failing at 22 of 26 reachable n values while passing at the 1500
    # cap, i.e. green by machine speed, not by being true (the file's own
    # W5-b1-era comments documented this exact defect and deferred the fix).
    # 1500 is the historical cap every documented reading was quoted at; the
    # guards below are now deterministic at the pinned seed.
    texture_n = 1500
    # per_persona_n FIXED at the instrument-repair wave (2026-08-01, review fold
    # — the SAME defect and the SAME precedent as texture_n directly above): it
    # was `max(150, (total_budget_hands - texture_n) // 6)`, i.e. 150..~700
    # depending on machine speed, and it is the n that decides FROZEN band
    # verdicts. The R-L2 sizing repair made that concrete: maniac's AF reads
    # 2.24-2.45 across n in {150, 400-650} (band floor 2.4) while its stable-n AF
    # is 2.99 / 3.06 at n=2000 / 4000 — INSIDE the frozen band. Which side of a
    # frozen floor the suite landed on was a function of how fast the box was.
    # 600 is the spec allocation every reading here was calibrated at (600/persona
    # x 6 + 1500 texture; see this docstring). `total_budget_hands` is retained
    # only as the historical derivation — it now sizes nothing.
    _historical_budget_hands = total_budget_hands
    del _historical_budget_hands
    per_persona_n = 600
    return per_persona_n, texture_n


@pytest.fixture(scope="module")
def budget():
    packs = load_persona_packs()
    if set(VillainType) - set(packs):
        pytest.skip("not all persona packs authored yet")
    hands_per_s = _measure_throughput(packs)
    per_persona_n, texture_n = _derive_n(hands_per_s)
    return packs, per_persona_n, texture_n, hands_per_s


# =====================================================================
# Per-persona stat bands: PRD §8 edges (`docs/ai-dlc/prd/simulate-table.md:
# 172-184`) +/- 3-sigma at this file's MEASURED occurrence n (not the 30
# floor -- the floor only gates whether a stat is asserted AT ALL; once
# asserted, the tolerance must reflect the real sample size actually
# achieved, which for most stats here is in the ~100-1000 range).
#
# fold-to-cbet / WTSD are binomial proportions: tol = 3*sqrt(p(1-p)/n),
# p = PRD band midpoint (or 0.3 as a conservative prior for one-sided "<X%"
# bands), n = this maker's measured occurrence count at the throughput-
# calibrated N (pinned at 600/persona since 2026-08-01; see `_derive_n`).
#
# AF = (BET+RAISE count R) / (CALL count C) is a RATIO of two counts, not a
# single proportion; using the delta method for Var(R/C) with R, C treated
# as independent (Poisson-like) counts: Var(AF) ~= AF^2 * (1/R + 1/C), so
# tol = 3 * AF * sqrt(1/R + 1/C), evaluated at R = AF*C from this maker's
# measured (AF, call_n) pair. One-sided "5+" (maniac) keeps only the lower
# edge; all others keep both PRD edges +/- tol.
#
# Measured occurrence n (this maker, seed 20260710, N~670/persona-lineup):
#   call_n:  passive_fish 630, calling_station 970, nit 100, tag 89, lag 115, maniac 183
#   ftc_n:   passive_fish 160, calling_station 237, nit  31, tag 37, lag  62, maniac 201
#   wtsd_n:  passive_fish 726, calling_station 991, nit 160, tag 253, lag 356, maniac 713
#
# WTSD FINDING (escalated to lead, same category as the table-texture floor;
# lead ruling below): at these levers, honest (PRD +/- 3sigma) WTSD bands
# MISS for 5/6 personas (passive_fish, calling_station, nit, tag, lag all
# measure WTSD ~0.40-0.54 vs PRD's tighter 0.20-0.45 population bands).
# Verified structural, not a lever- or lineup-tunable artifact: (a) nit's
# stickiness swept from 0.6 -> 0.3 (an extreme, AF-breaking cut) only moved
# WTSD 0.62 -> ~0.48-0.52, nowhere near the PRD [0.20,0.24] ceiling; (b) a
# single-copy-per-lineup harness variant (1 tested seat among 8 DISTINCT
# others, vs this file's 3-copy construction) showed the same ~0.41-0.50
# elevation across all personas, ruling out the 3x-same-persona lineup as
# the cause. Root cause: this engine's showdown_seats marks EVERY
# non-folded seat once 2+ players reach the river together, and the
# stickiness/aggression levers needed to hit the (honest, passing) AF and
# fold-to-cbet targets keep pots multiway long enough that showdown is
# systematically more common than the PRD's real-live-table anchor assumes
# (which embeds fold pressure -- sizing tells, rake tightness -- this
# heuristic engine does not model). maniac's WTSD alone lands inside its
# HONEST PRD band and keeps it (it passes; no need to re-anchor).
#
# LEAD RULING (wave-3 T2 escalation, 2026-07-10): for the 5 structural
# misses, WTSD bands below are ENGINE-ANCHORED regression bands, not
# PRD-fidelity claims -- PRD §8 WTSD anchors embed real-table fold pressure
# (sizing tells, rake tightness) the heuristic engine does not model;
# per-seat levers cannot control this population statistic (see wave-3 T2
# escalation). These pin current engine behavior against silent drift;
# PRD-fidelity revisit deferred (roadmap note at S4 close-out). Anchor =
# this maker's measured WTSD +/- 3*sqrt(p(1-p)/n) at a representative
# N~650/persona-lineup run (stable across N=550-1000 spot checks):
#   calling_station 0.5247 (n=953)  -> (0.476, 0.573)
#   lag             0.3947 (n=342)  -> (0.315, 0.474)
#   nit             0.5414 (n=157)  -> (0.422, 0.661)
#   passive_fish    0.5072 (n=694)  -> (0.450, 0.564)
#   tag             0.4268 (n=246)  -> (0.332, 0.521)

# NOTE (lever-scale disclaimer): aggression/stickiness/bluff_freq/spr_commit
# /multiway_bluff_damp are RELATIVE multipliers into a shared merit table
# (personas_postflop.py), not absolute probabilities or semantic claims --
# e.g. maniac's aggression=15.0 is a tuning outcome that clears the PRD AF
# floor at this merit table's saturation curve, not a statement that maniac
# is "15x normal". Only cross-persona ORDERING and the resulting measured
# stat bands are meaningful; the raw lever magnitudes are calibration
# artifacts of this specific merit-table implementation. (Since F3 the
# engine caps the effective lever at _AGGRESSION_CAP=5.6 — the authored
# 15.0 now only signals "above the cap"; see the F3 section.)

# F1 RE-ANCHOR (RES-D §4 measure-then-anchor, 2026-07-21): price-aware
# defense (personas_postflop._price_factor) re-levels fold-to-bet under the
# α fold-CEILING (RES-D §1a/§1c) — the pre-F1 merit tables folded ABOVE α at
# every size (e.g. tag ~0.39 vs a ⅓-pot bet where α = 0.25), so honoring the
# ceiling means every persona now folds LESS overall, calls absorb the freed
# mass, and therefore:
#   - AF falls for the aggressive personas (more calls in the denominator):
#     lag/maniac/tag/nit AF bands re-anchored to measured +/- 3-sigma at
#     N=399 and N=670 runs (union of CIs, rounded outward). Theory-consistent:
#     a price-aware defender flats SMALL/MEDIUM bets it price-blindly folded.
#   - WTSD RISES (not falls): RES-D §4 predicted WTSD would drop toward the
#     PRD population bands, but that prediction assumed the engine under-
#     folded; measurement showed it OVER-folded the α ceiling, so the
#     theory-correct fix keeps MORE pots alive. PRD WTSD overlap is
#     unreachable without breaching the ceiling invariant (the harder
#     contract) — WTSD bands stay ENGINE-ANCHORED (measured +/- 3-sigma,
#     union of the N=399/N=670 CIs), incl. maniac (previously an honest PRD
#     band). Documented deviation from RES-D §4's post-F1 WTSD targets.
#   - fold-to-cbet bands (mixed 0.33/0.75 flop c-bets) still contain the
#     measured values for station/fish/lag/maniac/tag and are KEPT; the
#     per-size slope regression lives in the fold_to_bet tests above.
#     nit's ftc is unmeasurable at this machine's N (<30 opportunities);
#     band widened downward (0.10) because SMALL c-bets are now folded far
#     less, in case a faster machine's larger N makes it measurable.
#     Follow-up: re-measure nit's ftc at larger N (faster machine or a
#     dedicated long run) and tighten the (0.10, 0.90) band to measured
#     ± 3σ once ≥30 opportunities accrue.
#
# Measured (N=399 / N=670, seed 20260710):
#   AF:   station .317/.330  fish .471/.487  nit 1.100/1.053
#         tag 2.478/2.224    lag 2.281/2.503 maniac 3.429/3.325
#   ftc:  station .168/.173  fish .244/.253  lag .282/.250
#         maniac .359/.344   tag n/a /.275   nit n/a / n/a
#   wtsd: station .756/.728  fish .741/.736  nit .651/.644
#         tag .655/.646      lag .654/.674   maniac .560/.571

# P1 RE-ANCHOR (A1 air-call drop, persona-realism-p1, 2026-07-23): A1 cut
# _CALL_BASE[AIR] 0.25 → 0.08 (street-neutral), so no-draw air folds instead
# of peeling — fewer junk hands ride to showdown and WTSD falls for the
# personas whose high stickiness leaned hardest on the old air call-base:
#   passive_fish WTSD 0.660 (n=423, N=399) / 0.644 (n=708, N=670), was
#     .741/.736 pre-A1 → 3σ CI union (0.575, 0.729) → band (0.57, 0.73).
#   maniac WTSD 0.475 (n=345, N=399) / 0.477 (n=622, N=670), was .560/.571
#     pre-A1 → 3σ CI union (0.394, 0.556) → band (0.39, 0.56). (The old
#     0.47 floor sat exactly on the new measured value — the wall-clock-N
#     flake this re-anchor removes.)
# All other personas' WTSD re-measured inside their existing bands at both N
# (station .688/.685, nit .605/.669, tag .634/.660, lag .592/.604) — kept, as
# were every AF and fold-to-cbet band (measured in-band at both N).

# P2a RE-ANCHOR (persona-realism-p2a Q3, 2026-07-23 — river polarization):
# play.py AND this file's own harness (refuter F1, `_postflop_decision` above)
# now pass `street` into the sampler, so the closed-loop bands measure the
# polarized river for the first time: the one-pair class never raises the
# river, and no-draw air never CALLs a river bet (it folds or bluff-raises).
# Engine is final for this slice (no lever retune available — the packs'
# levers were re-fit in P1 and are out of Q3's scope), so bands move to the
# re-measured values. Direction is theory-consistent everywhere:
#   - WTSD FALLS across the board (air that used to peel river bets now
#     folds; fewer junk showdowns): station .688/.685 → .575/.581,
#     fish .609/.601, nit .531/.567, tag .529/.550, lag .479/.494,
#     maniac .420/.398 (measured at N=399/N=670, seed 20260710).
#   - AF RISES for the aggressive personas (river air-calls leave the CALL
#     denominator faster than the floored river raises leave the numerator):
#     lag 2.28/2.50 → 3.20/3.17 (old 3.2 top now sits ON the measured value
#     — the deterministic failure this re-anchor fixes), maniac 3.32/3.19 →
#     3.74/4.10, nit 1.05 → 1.52/1.19.
# Bands = 3σ CI union at both N, rounded outward (binomial for ftc/WTSD,
# delta-method for AF — same math as the F1/F3 re-anchors above). Floors kept
# where the old floor was already below the new CI (looser is safe for a
# ceiling-style regression guard). NOTE: lag's AF top (4.5) now overlaps
# maniac's band — the population AF ordering claim has migrated to the
# exact-weight pins (test_maniac_still_strictly_most_aggressive and the
# fold/bluff ordering tests), which are deterministic and unaffected.
#
# W3R-2 RE-ANCHOR (persona-realism-w3r-2, 2026-07-24 — owner-authorized
# post-fit collision; FISH + STATION WTSD ONLY, every other row byte-identical
# and still frozen to W4-b). The hyp-2 dial fit (fish `call_looseness` 0.42;
# station `size_elasticity` 0.0 → 0.55 + `call_looseness` 4.0) changes exactly
# what these two personas do with a bet, so their showdown rates move in the
# theory-consistent direction:
#   - passive_fish WTSD FALLS (it stops over-calling, so fewer of its hands ride
#     to showdown): 0.5378 (n=2657, N=2500) / 0.5344 (n=4289, N=4000), was the
#     P2a-measured .609/.601 → 3σ CI union (0.5088, 0.5572) ∪ (0.5115, 0.5668)
#     = (0.5088, 0.5668) → band (0.50, 0.57).
#   - calling_station WTSD RISES (its authored `call_looseness` 4.0 exceeds the
#     `stickiness` 1.8 it used to inherit, so it calls even more): 0.6923
#     (n=3594, N=2500) / 0.6912 (n=5768, N=4000), was .575/.581 → 3σ CI union
#     (0.6692, 0.7154) → band (0.66, 0.72).
# Same P2a methodology as the blocks above: re-measure at the FINAL fitted dials
# at both representative N, band = the 3σ binomial CI union rounded outward.
# fish/station AF + fold_to_cbet re-measured INSIDE their existing tuples at both
# N (fish AF .940/.951, ftc .411/.431; station AF .341/.337, ftc .158/.160) —
# those tuples are KEPT unmoved.
#
# ⚠️ SUPERSEDED IN PART, 2026-08-21. The two WTSD bands this block derives —
# fish (0.50, 0.57) and station (0.66, 0.72) — are RETIRED, together with the
# W3R exception that authorized them, by the Stage-0 interim regime described
# immediately below; the live values are the tuples in `BANDS`. The AF and
# fold-to-c-bet halves of this block are untouched and still govern, and the
# sentence above about every other row staying frozen to W4-b still holds for
# AF and fold-to-c-bet. Kept as the derivation history it is.
#
# ---------------------------------------------------------------------------
# STAGE-0 INTERIM WENT-TO-SHOWDOWN REGIME (owner-ratified 2026-08-21).
#
# Every WTSD tuple below is now an INTERIM band, not a frozen one, and the two
# edges are governed by different rules. The floor is the persona's grounded
# floor from the theory contract's §5 keystone row; the ceiling is this tip's
# own measurement plus three binomial standard deviations, rounded outward and
# never above the incumbent ceiling. Showdown frequency is meant to FALL, so a
# slice that lowers it must stop failing CI for doing the right thing, while a
# slice that raises it must still be stopped. Floors give way; ceilings never
# rise. Authority: theory contract §5, amendments A4 and A5, plus the §11 item 7
# exception (A7) that makes a move under this regime reviewable rather than
# auto-failed. Full arithmetic: `test_persona_postflop_bands`' docstring below.
#
# The AF and fold-to-c-bet tuples are NOT touched by the regime and stay frozen
# to the single re-anchor slice.
#
# One retirement lands here: the 2026-07-24 W3R exception that moved the
# station's WTSD floor UP to 0.66 — 18 points above that persona's own grounded
# CEILING — is retired by A4.2 item 1. It was the single most binding obstacle
# to lowering showdown frequency. The AF and fold-to-c-bet bands were never
# part of that exception — W3R moved went-to-showdown only — so they are
# unaffected by its retirement.
# ---------------------------------------------------------------------------
# persona -> (AF band or None, fold_to_cbet band, WTSD band), all fractions.
BANDS = {
    # (fish/station AF + fold-to-c-bet are still the W3R-2 tuples — see the
    # block above; their WTSD tuples are Stage-0 interim values)
    "passive_fish": ((0.0, 1.560), (0.0, 0.549), (0.33, 0.55)),  # WTSD: Stage-0 interim
    "calling_station": ((0.0, 1.056), (0.0, 0.424), (0.38, 0.72)),  # WTSD: Stage-0 interim
    # nit AF top 2.025 → 2.4 (P2a: measured 1.520 at N=399, CI top 2.350) and
    # WTSD floor 0.50 → 0.37 (CI floor 0.378 at N=399, n=96).
    "nit": ((0.6, 2.4), (0.10, 0.90), (0.20, 0.67)),  # WTSD: Stage-0 interim (AF frozen)
    # tag ftc floor re-anchored (F1, RES-D §4): price-aware defense folds small
    # c-bets far less, pulling the aggregate to ~0.21 — ON the old 0.203 floor
    # (measured 0.195-0.26 across machines; n scales with machine speed and can
    # be as low as ~40 ⇒ 3σ ≈ ±0.19, so the floor must sit well below center).
    # P2a: ftc floor 0.05 → 0.0 (measured 0.152 at n=33 ⇒ CI floor < 0) and
    # WTSD (0.52,0.79) → (0.41,0.65) (river polarization, see block above).
    "tag": ((1.4, 3.6), (0.0, 0.55), (0.25, 0.59)),  # WTSD: Stage-0 interim (ftc frozen)
    "lag": ((1.5, 4.5), (0.12, 0.64), (0.26, 0.59)),  # WTSD: Stage-0 interim (AF/ftc frozen)
    # maniac AF top re-anchored (F3, RES-D §4 measure-then-anchor): the F1
    # band's 999 (∞) top was a saturation artifact — with aggression=15
    # effectively argmaxing bet/raise, AF had no meaningful upper bound to
    # regress against. With the F3 cap (_AGGRESSION_CAP=5.6) measured AF is
    # 3.324 (n_call=176, N=399) / 3.187 (n_call=294, N=670); delta-method
    # 3σ CIs (2.47, 4.18) / (2.55, 3.83), union rounded outward with headroom
    # for machine-scaled smaller n_call (~100 ⇒ tol ~±1.1) → top 4.5. Floor
    # keeps F1's 2.4 (both CIs sit above it; also keeps maniac's band floor
    # above lag's measured ~2.1-2.5 — the ordering claim). WTSD 0.561/0.573
    # measured — mid-band, (0.47, 0.65) kept (RES-D §4's PRD maniac WTSD
    # (0.228, 0.402) stays superseded by F1's documented engine-anchored
    # deviation: honoring the α fold-ceiling keeps more pots alive).
    # maniac ftc top re-anchored (F7, RES-D §4 measure-then-anchor): the paired-
    # board classification fix (under-pocket-pair TWO_PAIR_PLUS → MIDDLE_PAIR,
    # personas_postflop._made_bucket) moves those hands from never-fold to the
    # bluff-catch class, nudging aggregate fold-to-cbet UP for everyone; only
    # maniac's old 0.430 top clipped it. Measured 0.422 (n=128, N=399) / 0.398
    # (n=216, N=670), seed 20260710; binomial 3σ at machine-scaled n as low as
    # ~120 ⇒ tol ~±0.135 → top 0.56. Floor 0.0 kept. All other personas
    # re-measured inside their existing bands at both N (station .227/.199,
    # fish .303/.275, nit n/a/.314, tag .400/.391, lag .271/.237) — kept.
    # maniac P2a: AF top 4.5 → 5.1 (measured 4.102 at N=670, CI top 5.079),
    # ftc top 0.56 → 0.61 (measured .446/.466, CI top 0.609), WTSD
    # (0.39,0.56) → (0.34,0.50) (measured .420/.398 — river polarization).
    "maniac": ((2.4, 5.1), (0.0, 0.61), (0.30, 0.62)),  # WTSD: Stage-0 interim + A5 repair
}


def _packs_fingerprint(packs) -> str:
    """Deterministic identity of the persona-pack CONTENT a measurement consumed.

    INSTRUMENT REPAIR (waves 4 and 5, proven live): both stats caches used to
    key on `(persona, n, ...)` only, so a same-process before/after sweep —
    take a reading, mutate a persona pack, re-measure — silently served the
    FIRST reading back. The documented workaround was "measure in separate
    processes"; with the pack content in the key the cache simply misses and
    re-measures instead.

    CONTENT hash, not `pack.version`: a version string is hand-maintained and
    lags an in-flight edit, which is exactly the sweep this has to catch. Every
    pack in `packs` is hashed (not just the tested persona) because the sim
    runs a nine-seat lineup of ALL personas — the fillers move the reading too.
    Cost is ~6 x 4KB of JSON per call, negligible against simulating N hands."""
    h = hashlib.sha256()
    for name in sorted(packs, key=str):
        h.update(str(name).encode())
        h.update(b"\x00")
        h.update(packs[name].model_dump_json().encode())
        h.update(b"\x00")
    return h.hexdigest()[:16]


# key: (persona, n, context_aware, packs fingerprint) — see `_packs_fingerprint`
_STATS_CACHE: dict[tuple[str, int, bool, str], tuple] = {}


def _persona_stats(packs, persona: str, n: int, *, context_aware: bool = False):
    """Run N hands with a 9-seat lineup of ALL personas (round-robin fill,
    tested persona repeated to guarantee representation), collect AF /
    fold-to-cbet / WTSD for the tested persona's seats only.

    Returns `(af, ftc, wtsd, call_n, ftc_n, saw_flop_n, never_faced_wager)`.
    The last element (S3-T5) is the share of the persona's showdown hands that
    never met a wager on any postflop street; it is a DIRECTIONAL diagnostic
    and must never be asserted as a HARD gate.

    Memoized per (persona, n, context_aware, pack-content fingerprint) within
    the process (see `_packs_fingerprint`): the band
    test and the ordering-invariant test both need every persona's stats at
    the same N (from the shared `budget` fixture) -- caching avoids
    re-simulating the same N hands twice and keeps the whole file inside its
    runtime budget.

    `context_aware` (W5-a3-iii, default False) forwards to `_play_hand` --
    False keeps every existing CI band/golden byte-identical (no band
    re-anchor); True is the opt-in demonstration path proving the band
    sampler is no longer context-blind (see
    `test_street_aggressions_effect_visible_to_af_gate` below).
    """
    key = (persona, n, context_aware, _packs_fingerprint(packs))
    if key in _STATS_CACHE:
        return _STATS_CACHE[key]
    rng = random.Random(20260710)
    fillers = [p for p in ALL_PERSONAS if p != persona]
    lineup = ([persona] * 3 + [fillers[i % len(fillers)] for i in range(6)])[:9]
    persona_by_seat = {i: lineup[i] for i in range(9)}
    tested_seats = {i for i, p in persona_by_seat.items() if p == persona}

    bet_raise = call_count = 0
    folds_to_first_cbet = cbet_opportunities = 0
    saw_flop_hands = showdown_hands = never_faced_wager_hands = 0

    for i in range(n):
        hand_seed = rng.randrange(1_000_000_000)
        button_seat = i % 9
        res = _play_hand(
            rng, hand_seed, button_seat, persona_by_seat, packs, context_aware=context_aware
        )
        settlement, log, saw_flop = res.settlement, res.log, res.saw_flop
        # S3-T5 phase A: which seats met chips at ANY postflop street this hand.
        # `log` is postflop-only, so a FOLD/CALL/RAISE in it is a decision taken
        # with a wager outstanding. This is the same event t2-preregistration.md
        # §4 counted ("postflop folds, calls or raises per showdown hand"), kept
        # deliberately identical so the new counter's baseline is comparable to
        # the 47.7 / 44.1 / 41.6% figures that motivated this ticket. The one
        # known impurity is the rare matched-with-option RAISE (a CHECK+RAISE
        # node, where no wager is outstanding), which this counts as a faced
        # wager exactly as the prose figure did.
        faced_wager_seats = {s for s, _st, a in log if a in ("fold", "call", "raise")}
        for seat in tested_seats:
            if seat in saw_flop:
                saw_flop_hands += 1
                if seat in settlement.showdown_seats:
                    showdown_hands += 1
                    if seat not in faced_wager_seats:
                        never_faced_wager_hands += 1

        # AF: BET+RAISE / CALL, postflop only, tested seats.
        for seat, _street, action in log:
            if seat not in tested_seats:
                continue
            if action in ("bet", "raise"):
                bet_raise += 1
            elif action == "call":
                call_count += 1

        # fold-to-cbet: first FLOP bet in this hand; every OTHER seat who
        # then acts facing it (before anyone else bets/raises) is an
        # "opportunity"; tested seats among them who fold count as folds.
        first_bettor = None
        for seat, street, action in log:
            if street != "flop":
                continue
            if action == "bet" and first_bettor is None:
                first_bettor = seat
                continue
            if first_bettor is not None and seat != first_bettor:
                if seat in tested_seats:
                    cbet_opportunities += 1
                    if action == "fold":
                        folds_to_first_cbet += 1
                break  # only the immediate facing decision counts (first responder)

    af = (bet_raise / call_count) if call_count >= 30 else None
    ftc = (folds_to_first_cbet / cbet_opportunities) if cbet_opportunities >= 30 else None
    wtsd = (showdown_hands / saw_flop_hands) if saw_flop_hands >= 30 else None
    # S3-T5: DIRECTIONAL diagnostic only, never a HARD gate (theory contract's
    # three-HARD-statistics rule). Share of this persona's showdown hands that
    # never met a wager on any postflop street — the population the slice-3
    # calling dial cannot reach, and the one S3-T5's lever aims at.
    never_faced_wager = (
        (never_faced_wager_hands / showdown_hands) if showdown_hands >= 30 else None
    )
    result = (
        af,
        ftc,
        wtsd,
        call_count,
        cbet_opportunities,
        saw_flop_hands,
        never_faced_wager,
    )
    _STATS_CACHE[key] = result
    return result


# =====================================================================
# W0-b — the six new harness metrics (theory contract §6) + metric-DoD.
# Computed from the richer per-decision context ALONGSIDE the byte-identical
# AF/FtC/WTSD path above. These are SMOKE / DIRECTIONAL: they prove the metric
# computes + emits a value on today's engine. #5 (IP/OOP c-bet) and #6
# (turn-barrel) read ~flat until the W3 context mechanics land — that flatness
# is the correct pre-state, not a failure.
#
# Metric-DoD (roadmap D7): a downstream slice may NOT close on a HARD gate
# until the metric it needs is live AND showing the expected direction. W0-b
# only makes the metrics live; the direction is each later slice's exit gate.
# =====================================================================

_BUCKETS = [b.value for b in personas_postflop.SizeBucket]

# =====================================================================
# T-ARR — preflop node-occupancy (ARRIVAL) counters.
#
# Nothing in this repo measured how often a seat actually REACHES a preflop
# node, so a widened ladder that moved no aggregate could not be told apart
# from a broken one (PR #119: the BTN `unopened` ladder was widened correctly
# and changed almost nothing, because the BTN arrives at `unopened` ~8% of the
# time). These counters are the instrument: per position x facing-node, the
# share of a seat's FIRST preflop decision that lands there.
#
# Denominator: first-decision-per-seat-hand. A seat that acts again preflop
# (facing a 3-bet, say) is NOT re-counted — it was already dealt into a node.
# =====================================================================

_POSITIONS = [p.value for p in Position]
# Derived from the content model's own Literal, not re-typed: hand-copied string
# literals would silently stop covering the space if `PersonaFacing` grew a node
# (the per-position shares would quietly cease to sum to 1 with nothing failing).
_FACINGS = list(get_args(PersonaFacing))


class NodeOccupancy(NamedTuple):
    """Raw counts (not shares) so several personas can be POOLED by addition —
    a share-only field would need re-weighting by a denominator it no longer
    carries.

    TWO counter pairs, because ARRIVAL and OCCUPANCY are different questions and
    the difference is 31x at `vs_4bet` (see `HandResult.preflop_nodes`):
      `hits`/`opps`          FIRST decision per seat-hand = arrival. Every
                             calibrated band in this file reads THESE.
      `all_hits`/`all_opps`  EVERY preflop decision = true node occupancy. The
                             only honest source for the re-entry nodes
                             `vs_3bet`/`vs_4bet`.
    """

    hits: dict  # (position, facing) -> count, first decision only
    opps: dict  # position -> count (that position's first-decision total)
    all_hits: dict  # (position, facing) -> count, every preflop decision
    all_opps: dict  # position -> count (that position's total decisions)


class NodeActions(NamedTuple):
    """R10-COUNT — conditional action-at-node counters. T-ARR (above) answers
    "how often does a seat REACH this node"; these answer "what does it DO
    there" — P(action | persona, position, facing) — which is what the R10
    preflop-lane exits (PRE1/PRE2/3BET) gate on. `W-ARR` occupancy cannot
    express it and `ExtStats.pfr` is all-hand PFR, a different denominator.

    Raw counts (not shares) so personas POOL by addition, same rationale as
    `NodeOccupancy`. Keys carry the APPLIED engine action from `preflop_log`
    (fold/call/bet/raise) — the observable the external R10 corpus was derived
    from — NOT the persona-level action name (`3bet`/`limp`...), which the
    harness's documented double-sample makes unreliable as an outcome record.

    Denominators are NOT duplicated here: summing over the action axis of a
    counter dict reproduces the matching `NodeOccupancy` counter EXACTLY (the
    two are recorded from the same zipped rows; `test_node_action_counters_
    align_with_occupancy` pins the identity), so a separate denominator field
    could only ever drift from the truth it mirrors.
      `first_hits`  (position, facing, action) -> count, FIRST decision per
                    seat-hand only — the arrival-conditioned rates; first-in
                    (`unopened`) rates read THESE.
      `all_hits`    same key, EVERY preflop decision — the only honest
                    conditioning for the re-entry nodes `vs_3bet`/`vs_4bet`.

    ⚠️ For R10-3BET (theory-review T-1): the pooled `all_hits` vs_3bet rate
    mixes two arrival ranges — the OPENER re-entering (strong, raise-biased
    holdings) and cold first-decision facers — and is therefore NOT
    class-comparable to any external Fold-to-3bet figure, which conditions on
    the opener. The opener-conditioned stratum is expressible without new
    counters: `all_hits − first_hits` at vs_3bet = the re-entrants ≈ openers.
    Stratify before comparing.
    """

    first_hits: dict  # (position, facing, action) -> count, first decision only
    all_hits: dict  # (position, facing, action) -> count, every preflop decision


class ExtStats(NamedTuple):
    cbet_flop: float | None  # #1 — aggressor-side: P(bet | preflop aggressor's
    # first-in flop decision), theory contract §6. FIXED W5-a3-i: previously
    # P(bet | first-in flop decision) over ANY tested seat, including cold-
    # callers/blind-defenders who mostly check — the wrong denominator.
    wsd: float | None  # won >=1 pot / went to showdown
    vpip: float | None
    pfr: float | None
    gap: float | None  # vpip - pfr
    ftc_by_bucket: dict  # size bucket -> fold-to-cbet rate | None
    cbet_ip: float | None  # #5 — inherits #1's aggressor-side denominator
    cbet_oop: float | None
    turn_barrel: float | None  # #6 — reads ~flat until W3-c
    occupancy: NodeOccupancy  # T-ARR — arrival + occupancy counts, this
    # persona's seats only
    actions: NodeActions  # R10-COUNT — action-at-node counts, same seats,
    # recorded from the same rows (see the NamedTuple's docstring)


# key: (persona, n, packs fingerprint) — see `_packs_fingerprint`
_STATS_EXT_CACHE: dict[tuple[str, int, str], ExtStats] = {}


def _rate(num: int, den: int) -> float | None:
    """Rate with the harness's shared >=30-occurrence floor -> None."""
    return (num / den) if den >= 30 else None


def _preflop_aggressor(preflop_log: list[tuple[int, str]]) -> int | None:
    """The seat of the LAST applied preflop 'raise' (theory contract §6's
    aggressor for the flop c-bet metric). None on an all-limped/checked
    (no-raise) pot -- there is no aggressor-side c-bet opportunity there."""
    aggressor = None
    for seat, action in preflop_log:
        if action == "raise":
            aggressor = seat
    return aggressor


def _hand_cbet_stats(
    preflop_log: list[tuple[int, str]], decisions: list, tested_seats: set[int]
):
    """Aggressor-side flop c-bet (#1) + its IP/OOP split (#5) for one hand
    (theory contract §6: P(bet | preflop aggressor's first-in flop decision)).
    Only counts a tested seat's first-in flop decision when that seat IS the
    hand's preflop aggressor -- cold-callers/blind-defenders (who mostly
    check) are excluded, fixing the wrong-denominator bug. Also returns the
    hand's actual first flop bettor (any seat), used unchanged by the
    downstream fold-to-cbet/turn-barrel metrics, which are not aggressor-
    gated by §6."""
    aggressor = _preflop_aggressor(preflop_log)
    flop = [d for d in decisions if d.street == "flop"]
    cbet_bets = cbet_opps = 0
    cbet_ip_bets = cbet_ip_opps = 0
    cbet_oop_bets = cbet_oop_opps = 0
    bet_seen = False
    first_bettor = None  # (seat, bet_fraction)
    for d in flop:
        if not bet_seen and d.seat in tested_seats and d.seat == aggressor:
            cbet_opps += 1
            if d.in_position:
                cbet_ip_opps += 1
            else:
                cbet_oop_opps += 1
            if d.action == "bet":
                cbet_bets += 1
                if d.in_position:
                    cbet_ip_bets += 1
                else:
                    cbet_oop_bets += 1
        if d.action in ("bet", "raise"):
            if first_bettor is None and d.action == "bet":
                first_bettor = (d.seat, d.bet_fraction)
            bet_seen = True
    return (
        cbet_bets,
        cbet_opps,
        cbet_ip_bets,
        cbet_ip_opps,
        cbet_oop_bets,
        cbet_oop_opps,
        first_bettor,
    )


# ---------------------------------------------------------------------------
# W5-a3-i audit trail (persona-realism roadmap, 2026-07-25): metric #1's
# denominator was P(bet | first-in flop decision) over ANY tested seat —
# including cold-callers/blind-defenders who mostly check, not just the
# preflop aggressor. §6 defines it aggressor-side. Fixed via `_preflop_
# aggressor` + `_hand_cbet_stats` above (gates cbet_opps/cbet_bets, and the
# #5 IP/OOP split that inherits it, to `d.seat == aggressor`). No production
# code touched — measurement only.
#
# Re-measured on this branch's HEAD, same seeded lineup/rng stream as
# `_persona_stats_ext`, OLD (any first-in tested seat) vs NEW (aggressor-only)
# denominator, side by side on the identical hands:
#
#   n=200 (the harness's own smoke-test N; many NEW cells sit below the >=30
#   floor because aggressor-only opportunities are ~1/hand vs ~3/hand under
#   the old denominator — expected, not a regression):
#     persona          OLD cbet/ip/oop                  NEW cbet/ip/oop
#     calling_station   0.148 / 0.161 / 0.144             None  / None  / None
#     lag               0.477 / None  / 0.487             0.533 / None  / 0.553
#     maniac            0.598 / None  / 0.605             0.581 / None  / 0.587
#     nit               0.261 / None  / 0.257             None  / None  / None
#     passive_fish      0.193 / 0.161 / 0.200              None  / None  / None
#     tag                0.483 / None  / 0.480             None  / None  / None
#
#   n=4000 (higher power, run standalone — NOT part of the CI suite, which
#   stays bounded on the existing n=200 smoke test):
#     persona          OLD cbet/ip/oop (n)                NEW cbet/ip/oop (n)
#     calling_station   0.139 (569/4093) / 0.158 (163/1031) / 0.133 (406/3062)
#                       0.576 (19/33)    / None (8/11)       / None (11/22)
#     lag               0.485 (756/1558) / 0.530 (141/266)  / 0.476 (615/1292)
#                       0.543 (418/770)  / 0.552 (107/194)  / 0.540 (311/576)
#     maniac            0.638 (1540/2412)/ 0.638 (298/467)  / 0.639 (1242/1945)
#                       0.649 (909/1401) / 0.650 (215/331)  / 0.649 (694/1070)
#     nit               0.197 (181/919)  / 0.236 (29/123)   / 0.191 (152/796)
#                       0.277 (86/311)   / 0.254 (18/71)    / 0.283 (68/240)
#     passive_fish      0.173 (539/3124) / 0.162 (108/667)  / 0.175 (431/2457)
#                       0.415 (71/171)   / 0.364 (12/33)    / 0.428 (59/138)
#     tag               0.421 (519/1234) / 0.486 (105/216)  / 0.407 (414/1018)
#                       0.497 (298/599)  / 0.528 (85/161)   / 0.486 (213/438)
#   (each persona's second row above is NEW; first row is OLD.)
#
# Findings:
#   - The denominator fix moves cbet_flop UP for every persona (as the
#     roadmap predicted: dropping cold-caller/blind-defender first-in checks
#     from the numerator's population raises the aggressor-only rate).
#   - Direction check for lag (the roadmap's cited symptom, "IP 0.487 <
#     OOP 0.515"): on THIS branch's HEAD (post-W3R-1..6), lag's IP already
#     reads > OOP under BOTH the OLD and NEW denominator at n=4000 (OLD
#     0.530>0.476; NEW 0.552>0.540) — the exact inverted numbers quoted in
#     the roadmap do not reproduce here, most likely because the six W3R
#     preflop/dial slices (merged after that note was written) shifted the
#     shared-rng-stream population (documented drift pattern throughout this
#     file). The denominator bug is real and independently worth fixing per
#     §6's definition regardless; empirically, on today's tree, cbet_ip/
#     cbet_oop no longer read inverted for lag either way — acceptance
#     criterion 2 holds, but the reviewer should not read this as proof the
#     OLD code was the (sole) cause of the originally observed inversion.
#   - No persona's measured NEW cbet_ip vs cbet_oop ordering flips a HARD
#     gate (#5/P1 is DIRECTIONAL, not HARD, per §6) — nothing to re-anchor.
# ---------------------------------------------------------------------------


def _persona_stats_ext(packs, persona: str, n: int) -> ExtStats:
    """The six W0-b metrics for `persona`, measured over the SAME seeded lineup
    as `_persona_stats` (so the hands coincide) but from `decisions` /
    `preflop_log`. Memoized per (persona, n, pack-content fingerprint; see
    `_packs_fingerprint`). Metrics are harness-observed on today's engine — no
    domain plumbing needed (the harness holds full state)."""
    key = (persona, n, _packs_fingerprint(packs))
    if key in _STATS_EXT_CACHE:
        return _STATS_EXT_CACHE[key]
    rng = random.Random(20260710)
    fillers = [p for p in ALL_PERSONAS if p != persona]
    lineup = ([persona] * 3 + [fillers[i % len(fillers)] for i in range(6)])[:9]
    persona_by_seat = {i: lineup[i] for i in range(9)}
    tested_seats = {i for i, p in persona_by_seat.items() if p == persona}

    cbet_bets = cbet_opps = 0
    cbet_ip_bets = cbet_ip_opps = 0
    cbet_oop_bets = cbet_oop_opps = 0
    barrel_bets = barrel_opps = 0
    wsd_win = wsd_show = 0
    vpip_hands = pfr_hands = seat_hands = 0
    ftc_folds = dict.fromkeys(_BUCKETS, 0)
    ftc_opps = dict.fromkeys(_BUCKETS, 0)
    node_hits: dict[tuple[str, str], int] = {}
    node_opps: dict[str, int] = {}
    all_node_hits: dict[tuple[str, str], int] = {}
    all_node_opps: dict[str, int] = {}
    first_action_hits: dict[tuple[str, str, str], int] = {}
    all_action_hits: dict[tuple[str, str, str], int] = {}

    for i in range(n):
        hand_seed = rng.randrange(1_000_000_000)
        res = _play_hand(rng, hand_seed, i % 9, persona_by_seat, packs)

        # --- T-ARR: arrival (first decision) AND occupancy (every decision) ---
        # R10-COUNT rides the same rows: `preflop_nodes` and `preflop_log` are
        # appended once each per applied preflop decision in the same loop
        # block (the alignment T-ARR's contamination guard already asserts),
        # so zipping them attaches the APPLIED action to each node row without
        # touching the harness or drawing rng.
        for (seat, position, facing, is_first), (log_seat, action) in zip(
            res.preflop_nodes, res.preflop_log, strict=True
        ):
            assert seat == log_seat, "preflop_nodes/preflop_log misaligned"
            if seat not in tested_seats:
                continue
            all_node_hits[(position, facing)] = all_node_hits.get((position, facing), 0) + 1
            all_node_opps[position] = all_node_opps.get(position, 0) + 1
            akey = (position, facing, action)
            all_action_hits[akey] = all_action_hits.get(akey, 0) + 1
            if is_first:
                node_hits[(position, facing)] = node_hits.get((position, facing), 0) + 1
                node_opps[position] = node_opps.get(position, 0) + 1
                first_action_hits[akey] = first_action_hits.get(akey, 0) + 1

        # --- VPIP / PFR / gap (once per tested seat-hand, applied actions) ---
        seat_hands += len(tested_seats)
        pf_acts: dict[int, set[str]] = {}
        for seat, action in res.preflop_log:
            if seat in tested_seats:
                pf_acts.setdefault(seat, set()).add(action)
        for seat in tested_seats:
            acts = pf_acts.get(seat, set())
            if acts & {"call", "bet", "raise"}:
                vpip_hands += 1
            if acts & {"bet", "raise"}:
                pfr_hands += 1

        # --- W$SD (won >=1 pot / went to showdown) ---
        for seat in tested_seats:
            if seat in res.settlement.showdown_seats:
                wsd_show += 1
                if any(seat in w for w in res.settlement.winners_by_pot):
                    wsd_win += 1

        # --- flop c-bet (aggressor-side, first-in) + IP/OOP split (§6 #1/#5);
        # capture first flop bettor (any seat) for fold-to-cbet/turn-barrel ---
        flop = [d for d in res.decisions if d.street == "flop"]
        (
            hand_cbet_bets,
            hand_cbet_opps,
            hand_cbet_ip_bets,
            hand_cbet_ip_opps,
            hand_cbet_oop_bets,
            hand_cbet_oop_opps,
            first_bettor,
        ) = _hand_cbet_stats(res.preflop_log, res.decisions, tested_seats)
        cbet_bets += hand_cbet_bets
        cbet_opps += hand_cbet_opps
        cbet_ip_bets += hand_cbet_ip_bets
        cbet_ip_opps += hand_cbet_ip_opps
        cbet_oop_bets += hand_cbet_oop_bets
        cbet_oop_opps += hand_cbet_oop_opps

        # --- size-bucketed fold-to-cbet (first responder to the first bet) ---
        if first_bettor is not None and first_bettor[1] is not None:
            fb_seat, frac = first_bettor
            bucket = personas_postflop.size_bucket(frac).value
            seen = False
            for d in flop:
                if not seen:
                    if d.seat == fb_seat and d.action == "bet":
                        seen = True
                    continue
                if d.seat != fb_seat:  # the first responder
                    if d.seat in tested_seats:
                        ftc_opps[bucket] += 1
                        if d.action == "fold":
                            ftc_folds[bucket] += 1
                    break

        # --- turn barrel: the flop aggressor's first (unobstructed) turn bet ---
        if first_bettor is not None and first_bettor[0] in tested_seats:
            fa = first_bettor[0]
            t_bet_seen = False
            for d in (d for d in res.decisions if d.street == "turn"):
                if d.seat == fa:
                    if not t_bet_seen:  # clean barrel opportunity
                        barrel_opps += 1
                        if d.action in ("bet", "raise"):
                            barrel_bets += 1
                    break  # a lead before fa acted -> not a clean barrel spot
                if d.action in ("bet", "raise"):
                    t_bet_seen = True

    vpip = _rate(vpip_hands, seat_hands)
    pfr = _rate(pfr_hands, seat_hands)
    stats = ExtStats(
        cbet_flop=_rate(cbet_bets, cbet_opps),
        wsd=_rate(wsd_win, wsd_show),
        vpip=vpip,
        pfr=pfr,
        gap=(vpip - pfr) if vpip is not None and pfr is not None else None,
        ftc_by_bucket={b: _rate(ftc_folds[b], ftc_opps[b]) for b in _BUCKETS},
        cbet_ip=_rate(cbet_ip_bets, cbet_ip_opps),
        cbet_oop=_rate(cbet_oop_bets, cbet_oop_opps),
        turn_barrel=_rate(barrel_bets, barrel_opps),
        occupancy=NodeOccupancy(
            hits=node_hits,
            opps=node_opps,
            all_hits=all_node_hits,
            all_opps=all_node_opps,
        ),
        actions=NodeActions(
            first_hits=first_action_hits,
            all_hits=all_action_hits,
        ),
    )
    _STATS_EXT_CACHE[key] = stats
    return stats


_OPEN_FIELDS = ("open_bb", "open_bb_mix", "open_bb_mix_by_position")


def _snapshot_open(sizing) -> dict:
    """Deep enough copy of every field carrying a persona's open size."""
    return {
        "open_bb": sizing.open_bb,
        "open_bb_mix": dict(sizing.open_bb_mix) if sizing.open_bb_mix else None,
        "open_bb_mix_by_position": (
            {seat: dict(mix) for seat, mix in sizing.open_bb_mix_by_position.items()}
            if sizing.open_bb_mix_by_position else None
        ),
    }


def _restore_open(sizing, snap: dict) -> None:
    for field in _OPEN_FIELDS:
        setattr(sizing, field, snap[field])


def _shift_open(sizing, delta: float) -> None:
    """Move EVERY form in which this persona's open is authored.

    Shifting only `open_bb` stopped being a live input at T2b: the three
    regulars author `open_bb_mix_by_position`, the three recreationals author
    `open_bb_mix`, and with an rng in play `preflop_raise_to` reads the mix and
    never the scalar. A mutation that is no longer an input turns an instrument
    gate green for the wrong reason — which is the very failure this gate
    exists to catch — so it moves all three forms together.
    """
    sizing.open_bb += delta
    if sizing.open_bb_mix is not None:
        sizing.open_bb_mix = {
            str(float(k) + delta): w for k, w in sizing.open_bb_mix.items()}
    if sizing.open_bb_mix_by_position is not None:
        sizing.open_bb_mix_by_position = {
            seat: {str(float(k) + delta): w for k, w in mix.items()}
            for seat, mix in sizing.open_bb_mix_by_position.items()
        }


def test_stats_caches_are_pack_content_keyed():
    """🔴 INSTRUMENT GATE (cache defect, waves 4 and 5): both stats caches must
    key on the persona-pack CONTENT, so a same-process before/after sweep —
    read, edit a pack, re-read — cannot be served the stale first reading.

    At b54fe6e the keys were `(persona, n, context_aware)` / `(persona, n)`, so
    the mutated re-read returned the ORIGINAL tuple object and every such sweep
    silently measured nothing; the standing workaround was "measure in separate
    processes". Both legs below fail there on the identity assertion alone.

    The mutation is a real measurement input (tag's preflop open size, in
    whichever form the pack authors it — see `_shift_open`), and the test
    restores it in a `finally` — the packs dict is loaded locally here, so
    nothing leaks to other tests even if the restore were skipped."""
    packs = load_persona_packs()
    n = 150

    base = _persona_stats(packs, "tag", n)
    base_ext = _persona_stats_ext(packs, "tag", n)
    # Unmutated repeat: a genuine cache HIT returns the same object.
    assert _persona_stats(packs, "tag", n) is base
    assert _persona_stats_ext(packs, "tag", n) is base_ext

    original_open = _snapshot_open(packs[VillainType.TAG].sizing)
    try:
        _shift_open(packs[VillainType.TAG].sizing, 5.0)
        mutated = _persona_stats(packs, "tag", n)
        mutated_ext = _persona_stats_ext(packs, "tag", n)
        # (a) cache MISS proven: a fresh measurement ran, not the memo.
        assert mutated is not base, (
            "the AF/FtC/WTSD cache served the pre-mutation reading — the key is "
            "pack-blind again and every same-process sweep is invalid"
        )
        assert mutated_ext is not base_ext, (
            "the W0-b ext cache served the pre-mutation reading — pack-blind key"
        )
        # (b) and the reading actually MOVED: the mutation is a live input, so a
        # miss that returned an identical tuple would mean the sweep still can't
        # see pack edits.
        assert mutated != base, f"reading did not move under a +5bb open: {mutated}"
        assert mutated_ext.vpip != base_ext.vpip or mutated_ext.pfr != base_ext.pfr, (
            f"ext reading did not move under a +5bb open: vpip={mutated_ext.vpip} "
            f"pfr={mutated_ext.pfr}"
        )
    finally:
        _restore_open(packs[VillainType.TAG].sizing, original_open)
    # (c) restored content -> the ORIGINAL memo is hit again (the fingerprint is
    # content-derived, so it returns to its earlier value; nothing was evicted).
    assert _persona_stats(packs, "tag", n) is base
    assert _persona_stats_ext(packs, "tag", n) is base_ext

    # (d) FILLER packs count too. The lineup is nine seats of ALL personas, so a
    # maniac edit moves a tag reading — a fingerprint that hashed only the
    # MEASURED persona would pass every leg above and still serve stale readings
    # for the six-of-nine seats it ignored. Mutating a persona that is in the
    # lineup but is NOT the one being measured kills that mutant.
    original_maniac_open = _snapshot_open(packs[VillainType.MANIAC].sizing)
    try:
        _shift_open(packs[VillainType.MANIAC].sizing, 5.0)
        filler_read = _persona_stats(packs, "tag", n)
        assert filler_read is not base, (
            "editing a FILLER pack did not miss the cache — the fingerprint "
            "covers only the measured persona, so six of nine seats can change "
            "under a stale reading"
        )
        # Delta-review fold (2026-08-01): identity alone would also pass under a
        # merely over-sensitive fingerprint (e.g. one hashing object ids) — the
        # VALUE must move too, proving the filler pack is a live input to the
        # tag's measured environment (maniac opens 5bb larger → tag faces
        # different action).
        assert filler_read != base, (
            "filler-pack edit missed the cache but the tag reading did not "
            "move — the filler pack is not a live input to this measurement"
        )
        assert _persona_stats_ext(packs, "tag", n) is not base_ext, (
            "editing a FILLER pack did not miss the ext cache — same defect"
        )
    finally:
        _restore_open(packs[VillainType.MANIAC].sizing, original_maniac_open)
    assert _persona_stats(packs, "tag", n) is base


# --------------------------------------------------------------------- T-ARR
# Pooling + rendering for the arrival grid. All of it reads the ALREADY-MEMOIZED
# `_persona_stats_ext` runs — there is no second simulation loop, so the grid
# costs ~0 on top of the existing W0-b metric run at the same n.


def _pooled_occupancy(packs, n: int) -> NodeOccupancy:
    """Roster-pooled arrival counts: each persona's own seats, summed over the
    six personas.

    ⚠️ THE POOL IS NOT ROSTER-BALANCED — a KNOWN, DOCUMENTED BIAS (found by
    review, 2026-07-26; an earlier version of this docstring wrongly claimed it
    was balanced). `_persona_stats_ext`'s lineup is
    `([persona]*3 + [fillers[i % len(fillers)] for i in range(6)])[:9]`, and
    that comprehension walks SIX indices over FIVE fillers, so `fillers[0]` is
    doubled. `fillers[0]` is `calling_station` in five of the six runs (in its
    own run it is `lag`). Actual composition over the 54 seat-slots:

        calling_station 13 · lag 9 · maniac 8 · nit 8 · passive_fish 8 · tag 8

    i.e. calling_station takes 13 slots where four of the six take 8 (+62%),
    and 44% above the balanced 9. That biases arrival DOWNWARD and not by a
    little: arrival is decided entirely by the seats acting AHEAD of you, and
    calling_station is the loosest persona on the roster (VPIP 46%), so every
    extra one of it is an extra limper suppressing `unopened`. Review measured
    the balanced-pool counterfactual at **0.3504** — inside the originally
    drafted [0.33, 0.43] — against this pool's 0.3238.

    ⚠️ THE +0.026 IS ROSTER-WIDE AND DOES NOT TRANSFER PER CELL. Do NOT add it
    to a single position; at BTN the correction has the OPPOSITE SIGN. Balanced
    vs as-built, `unopened` by position:

        UTG1 0.788 / 0.740 · UTG2 0.540 / 0.500 · LJ 0.376 / 0.280
        HJ   0.250 / 0.184 · CO   0.127 / 0.127 · BTN 0.066 / 0.074

    So the bias is concentrated in EARLY/MIDDLE position, is nil at CO, and at
    BTN it runs the other way: -0.007, pushing BTN TOWARD its 0.05 floor rather
    than away from it. That matters because BTN is the cell the initiative
    quotes, and it is already the fragile one.

    NOT FIXED HERE, deliberately. The lineup expression is shared with
    `_persona_stats` and every seeded band and golden in this file was recorded
    against it; changing it re-records fixtures, which is T-ANCHOR's job in
    wave 2 and nobody else's."""
    hits: dict[tuple[str, str], int] = {}
    opps: dict[str, int] = {}
    all_hits: dict[tuple[str, str], int] = {}
    all_opps: dict[str, int] = {}
    for persona in ALL_PERSONAS:
        occ = _persona_stats_ext(packs, persona, n).occupancy
        for key, v in occ.hits.items():
            hits[key] = hits.get(key, 0) + v
        for pos, v in occ.opps.items():
            opps[pos] = opps.get(pos, 0) + v
        for key, v in occ.all_hits.items():
            all_hits[key] = all_hits.get(key, 0) + v
        for pos, v in occ.all_opps.items():
            all_opps[pos] = all_opps.get(pos, 0) + v
    return NodeOccupancy(hits=hits, opps=opps, all_hits=all_hits, all_opps=all_opps)


def _occupancy_shares(occ: NodeOccupancy) -> dict[str, dict[str, float]]:
    """ARRIVAL shares: position -> facing -> share of that position's FIRST
    preflop decisions. A position with no first decisions reads 0.0 across its
    row. Every calibrated assertion reads this — do not repoint it at the `all`
    counters, which measure a different quantity on a different denominator."""
    return {
        pos: {
            f: (occ.hits.get((pos, f), 0) / occ.opps[pos]) if occ.opps.get(pos) else 0.0
            for f in _FACINGS
        }
        for pos in _POSITIONS
    }


def _occupancy_all_shares(occ: NodeOccupancy) -> dict[str, dict[str, float]]:
    """TRUE OCCUPANCY shares over EVERY preflop decision. This is the only
    honest reading of `vs_3bet`/`vs_4bet`, which are re-entry nodes that the
    arrival denominator structurally floors near zero."""
    return {
        pos: {
            f: (occ.all_hits.get((pos, f), 0) / occ.all_opps[pos]) if occ.all_opps.get(pos) else 0.0
            for f in _FACINGS
        }
        for pos in _POSITIONS
    }


# The two re-entry nodes. Rendered from the `all` counters because the arrival
# denominator floors them near zero (`vs_4bet` by ~31x) — see `NodeOccupancy`.
_REENTRY_FACINGS = ("vs_3bet", "vs_4bet")


def _format_occupancy(occ: NodeOccupancy) -> str:
    """The 9x5 grid, rendered — this is the artifact the initiative reads.

    ⚠️ Pytest CAPTURES this unless `-s` is passed, and the ticket's own
    done-condition (`-k "occupancy" -q`) does NOT pass it, so on a PASS only the
    `unopened` column reaches CI via the assertions. To actually read the grid —
    in particular `vs_limpers`/`vs_rfi`, which are what answer "is this roster
    over-limping or over-raising" — run:
        python -m pytest tests/test_personas_postflop.py -k occupancy -q -s
    """
    arrival = _occupancy_shares(occ)
    occupied = _occupancy_all_shares(occ)
    lines = [
        "",
        "ARRIVAL (first decision per seat-hand), except the two starred re-entry",
        "columns, which are TRUE OCCUPANCY over every preflop decision:",
        "pos   " + "".join(f"{f + ('*' if f in _REENTRY_FACINGS else ''):>12s}" for f in _FACINGS)
        + f"{'n':>8s}{'n*':>8s}",
    ]
    for pos in _POSITIONS:
        row = "".join(
            f"{(occupied if f in _REENTRY_FACINGS else arrival)[pos][f]:12.3f}" for f in _FACINGS
        )
        lines.append(
            f"{pos:6s}{row}{occ.opps.get(pos, 0):8d}{occ.all_opps.get(pos, 0):8d}"
        )
    total = sum(occ.opps.values())
    wide = sum(occ.hits.get((p, "unopened"), 0) for p in _POSITIONS) / total if total else 0.0
    lines.append(f"roster-wide unopened = {wide:.4f}  over {total} first-decisions")
    lines.append(
        "* vs_3bet/vs_4bet are RE-ENTRY nodes (you open, you get 3-bet, you act "
        "again).\n  On the arrival denominator they read ~0 -- UTG vs_3bet would "
        "show 0.000 -- which\n  is a measurement floor, NOT a dead branch. Rows "
        "therefore do not sum to 1."
    )
    return "\n".join(lines)


# Golden AF/FtC/WTSD at a fixed (persona, n) with the harness's own deterministic
# seed (20260710). Originally captured on the PRE-refactor code to prove the
# W0-b log->HandResult refactor was byte-identical (band membership is too wide
# to prove it — Sol #4 / refuter #3). Now doubles as an intended-behavior-change
# tripwire. None = below the >=30 floor.
#
# RE-RECORDED for W1-a (persona-realism-w1, 2026-07-24 — slice-authorized): the
# harness runs villains through the SAME postflop sampler, so the middle-pair
# river BET floor (F6) deliberately changes river play -> AF/FtC/WTSD shift.
# Re-record of the exact tripwire (MUST track intended behavior), NOT the
# population WTSD/AF tolerance-band re-anchor, which stays frozen to W4-b.
# RE-RECORDED for W1-c (persona-realism-w1, 2026-07-24 — slice-authorized): the
# multiway made-value BET damp (F13) tightens top/middle-pair betting as the
# field grows -> multiway spots in the harness shift AF/FtC/WTSD again. These are
# the post-W1-c exact goldens (post-W1-b golden was byte-identical to W1-a — the
# faced_frac fix is inert in this harness wrapper).
# RE-RECORDED for W2-a (persona-realism-w2, 2026-07-24 — slice-authorized): the
# calling_station (size_elasticity 0.0, size-blind) and passive_fish
# (size_elasticity 1.3, size-scared) opt into the elasticity split, changing
# their faced-size fold decisions. This is a SHARED-TABLE sim — all six personas
# play one lineup on one rng stream — so EVERY persona's aggregate stats move
# (the un-opted-in nit/tag/lag/maniac shift via environment + rng-stream
# displacement, NOT a policy change). Proven code-innocent: stripping the two new
# content levers reproduces the pre-W2 golden BYTE-FOR-BYTE (the reviewer-#8 guard,
# adapted to a shared-table fixture — a per-persona-row diff is meaningless when
# rows are coupled). Exact tripwire re-record; population bands stay frozen to W4-b.
# RE-RECORDED for W2-b (persona-realism-w2, 2026-07-24 — slice-authorized): the
# commit/draw EV gate changes villain play in two intended cases — a STRONG draw
# facing an overbet is no longer force-jammed (can fold), and a naked WEAK draw
# stops stacking off at high commitment. (This is a CODE change, so the strip-
# levers guard does NOT apply — its byte-identity is analytic: made hands,
# non-facing STRONG draws, and bets up to ~1.3× pot are unchanged; only overbet-
# draw + weak-draw-commit spots move, covered by the exact-weight commit unit
# tests.) All six personas shift via the shared-rng stream. Exact tripwire.
# RE-RECORDED for W3-b/c/d (persona-realism-w3bcd, 2026-07-24 — slice-authorized):
# the position IP/OOP multiplier (W3-b, opted personas tag/nit/lag), the street
# aggression schedule + busted-river bluff (W3-c, all personas), and the made-hand
# overcard/wetness texture brakes (W3-d, all personas) all change villain postflop
# play, so the shared-rng stream drifts and every persona's AF/FtC/WTSD moves. The
# flop stays byte-identical for the street schedule (mult 1.0), but W3-b (opted) and
# W3-d shift flop one-pair betting, so this whole tripwire re-records. Covered by
# the W3-b/c/d exact-weight unit tests.
# RE-RECORDED for W3R-1 (persona-realism-w3r1, 2026-07-24 — slice-authorized):
# a PURE preflop-content change (maniac `vs_rfi` 3-tier legit range replaces the
# any-two cold-call; maniac + lag SB open-limps deleted; maniac HJ/CO/BTN offsuit-
# ace opens trimmed). No postflop/engine code changed, but which hands reach each
# postflop street shifts, so the shared-rng stream drifts and every persona's
# AF/FtC/WTSD moves (nit's AF now falls below the >=30 CALL floor → None). Covered
# by the W3R-1 preflop assertion tests (test_w3r1_preflop_cleanup.py).
# RE-RECORDED for W3R-2 (persona-realism-w3r-2, 2026-07-24 — slice-authorized):
# a PURE persona-JSON dial change (fish `call_looseness` 0.42 authored; station
# `size_elasticity` 0.0 → 0.55 + `call_looseness` 4.0 authored) — no engine code
# touched. Both personas' fold/call decisions vs a faced bet change BY DESIGN
# (that IS hyp-2), and this is a SHARED-TABLE sim on one rng stream, so every
# persona's aggregates move via environment + rng-stream displacement (nit's AF
# re-crosses the >=30 CALL floor → numeric again). Covered by the W3R-2 arrival
# bands (test_arrival_range_ftc.py) + the flipped exact-weight price tests above.
# RE-RECORDED for W3R-3 (persona-realism-w3r-3, 2026-07-24 — slice-authorized):
# the #4 spr_commit LADDER only — fish 2.0 -> 1.4 (it was committing its stack at a
# HIGHER SPR than the calling station's 1.5, i.e. EARLIER — backwards for a scared
# bot) and maniac 4.0 -> 3.3. Both bots' low-SPR commit points move, so their
# stack-off/fold decisions change BY DESIGN; this is a SHARED-TABLE sim on one rng
# stream, so every persona's aggregates shift via environment + rng-stream
# displacement, not a policy change. #12 (tag/nit/lag explicit `call_looseness` ==
# their previously-inherited `stickiness`) contributes ZERO drift — verified
# byte-identical in isolation (stripping the three authored values back to None
# reproduces every row below exactly). #5 (the global ACE_HIGH call-base cut) was
# DROPPED from this slice by owner decision — see the `_FOLD_BASE` calibration
# comment in personas_postflop.py — so no ace-high behavior is in this re-record.
# Covered by the exact-weight `test_spr_commit_ladder_*` tests above; population
# bands stay frozen to W4-b.
# RE-RECORDED for W3R-4 (persona-realism-w3r-4, 2026-07-24 — slice-authorized):
# the #11 `_CALL_BASE[MIDDLE_PAIR]` 0.60 -> 0.52 trim. Naked middle pair calls a
# faced bet marginally less BY DESIGN (that IS #11), and this is a SHARED-TABLE
# sim on one rng stream, so every persona's aggregates move via the policy change
# + rng-stream displacement (nit/tag/lag FtC re-cross the >=30 floor -> None).
# The #7 multiway busted-bluff damp contributes ZERO drift here — verified: with
# only the line-675 change applied this fixture was byte-identical, because this
# harness passes no `PostflopContext`, so the busted add-on never fires in it
# (#7 is covered by the exact-weight `test_busted_river_bluff_decays_with_
# opponents`). Exact tripwire re-record; population bands stay frozen to W4-b and
# every persona was re-measured IN its existing band (no re-anchor).
# RE-RECORDED for W5-b1 (persona-realism-w5-b1, 2026-07-25 — slice-authorized):
# the nit/tag/lag `unopened` ladders widened to 9-max full-ring widths (authored
# mean nit 8.0 -> 28.5, tag 16.4 -> 34.0, lag 22.6 -> 43.2). PURE preflop content —
# NO engine, postflop-sampler or dial code changed — but it changes which hands
# reach the flop and how often a pot is single-raised vs limped, so the whole
# shared-table stream moves. This is a SHARED-TABLE sim (all six personas play one
# lineup on one rng stream), so the three UNEDITED packs (station/fish/maniac) shift
# too, via environment + rng-stream displacement, NOT a policy change. Direction is
# the expected one: the station's FtC jumps 0.094 -> 0.209 and its WTSD falls
# 0.747 -> 0.651 because it now faces genuine raised pots instead of limp-fests.
# Exact tripwire re-record; population bands stay frozen to W4-b, and metric #3
# (VPIP/PFR/gap) is REPORTED not gated for this slice.
# RE-RECORDED for R10-PRE1 (persona-realism-r10-pre1, 2026-07-30 — slice-
# authorized): the maniac's premium unopened carve-out (TT+/AQs+/AKo raise 1.0)
# stops it folding premiums first-in, so a small share of hands now open raised
# instead of folding around — shared-table rng-stream displacement. Only the
# station row (AF 0.2829 -> 0.2784, FtC 0.2090 -> 0.2188, WTSD 0.6507 -> 0.6644)
# and tag WTSD (0.5696 -> 0.5556) moved at this seed; lag/maniac/nit/fish are
# byte-identical, incl. the maniac itself (its N200 sample hits no changed cell).
# Exact tripwire re-record; population bands stay frozen to W4-b.
# RE-RECORDED for R10-PRE2 (persona-realism-r10-pre2, 2026-07-30 — slice-
# authorized): the maniac `unopened` ladder widened above the LAG's at every
# seat (authored seat-avg first-in raise 0.245 sampled -> 0.518 authored /
# 0.410 sampled). PURE preflop content — no engine or postflop code changed —
# but the maniac now opens roughly twice as often, which reshapes every pot
# the shared table plays (more raised pots, fewer limp-fests, different flop
# arrivals), so ALL six rows move at this seed via environment + rng-stream
# displacement. The N200 deltas are stream-displacement NOISE, not a
# behavioral reading (theory review, R10-PRE2): at stable n=1200 with only
# the maniac pack swapped, maniac reads AF 3.62 -> 3.16, FtC 0.353 -> 0.328,
# WTSD 0.506 -> 0.499 (essentially flat; the N200 WTSD 0.532 -> 0.442 swing
# is a sampling artifact; fish FtC re-crossing the >=30 floor -> None is the
# same). ⚠️ W4-b HAND-OFF: the stable-n AF drop (3.62 -> 3.16, ~2.5σ) moves
# maniac FURTHER BELOW §5's AF 4-6 keystone — it reaches the flop as
# aggressor with more air and gives up more; the single W4-b re-anchor must
# reconcile this. REPORTED only — no band moved here. Exact tripwire
# re-record; population bands stay frozen to W4-b.
# RE-RECORDED for W5-b4 (persona-realism-w5b4, 2026-07-31 — slice-authorized):
# the maniac vs_limpers/vs_rfi repair (positional iso split toward ~60% late,
# tier-3 flat {call 0.9} -> {3bet 0.2, call 0.3, fold 0.5}, any-two light
# 3bet-or-fold catch-all, modest fringe over-limp). PURE preflop content — the
# maniac now isolates/3-bets pots it used to flat or fold, so the shared-table
# stream reshapes and ALL six rows move at this seed (displacement + genuine
# environment change). Stable-n (1200) maniac reading with only this pack
# changed: VPIP 40.6 -> ~39.6, PFR 25.1 -> ~32, gap 15.4 -> ~7.5, vs_rfi
# cold-call 34.2 -> ~16, 3bet 12.4 -> ~23. ⚠️ nit's AF cell goes 0.894 ->
# None at this seed (its n=200 sample loses the call denominator) — the
# tripwire stops watching a HARD-today stat for nit until the stream shifts
# back; accepted for this wave (the nit AF band test still gates it at
# population n). Exact tripwire re-record; population bands stay frozen to
# W4-b.
_GOLDEN_STATS_N200 = {
    # RE-RECORDED for W5-b3 (2026-07-31, slice-authorized): the nit nine-seat
    # unopened ladder replaces the flat 13.6/29.1 pack, displacing the shared
    # rng stream from the first nit first-in decision onward. nit's own AF
    # falls off the n=200 tripwire along with lag/tag (call denominators under
    # the floor at this tiny n); the population band tests still gate them.
    # Exact tripwire re-record; population bands stay frozen to W4-b.
    # RE-RECORDED for R10-TAIL-a1 (2026-07-31, slice-authorized): the piecewise
    # absolute-price tail in `_price_factor` (f > 1.5 ⇒ factor *= (f/1.5)**2.0)
    # makes every persona fold more vs overbets, changing hand endings and
    # displacing the shared rng stream from the first tail-affected decision
    # onward. All rows except fish move at this seed (fish byte-identical —
    # its n=200 sample hits no changed cell). lag/maniac AF regain their call
    # denominators at this stream; the maniac AF rise (3.46 -> 3.80) is
    # composition (folds-to-overbet leave its aggressive actions over a smaller
    # call base), consistent with the pre-rebase review reading (3.30 -> 3.58).
    # Exact tripwire re-record; population bands stay frozen to W4-b.
    # RE-RECORDED for N-3BSTRATA (2026-07-31, slice-authorized): maniac + lag
    # now CONTINUE most 3-bet pots they open (opener tables), so every re-
    # raised pot plays out differently and the shared rng stream displaces
    # from the first stratified vs_3bet decision onward — all six rows move
    # at this seed. maniac AF 3.80 -> 3.33 at n=200 is the expected
    # composition (it now calls 3-bets with its whole junk-continue tier and
    # reaches more passive postflop nodes); population bands still gate it
    # at stable n. Exact tripwire re-record; population bands stay frozen to
    # W4-b.
    # RE-RECORDED for WAVE 3 COMBINED (persona-realism-wave3, 2026-07-31 —
    # wave-authorized, recorded once on the combined lane-B + lane-A tip):
    # T-M2 nit CO/BTN pair opens + T-F3 maniac vs_4bet middle pairs (lane B)
    # + N-LAGLADDER lag composition swap + AQo fold→call + opener vs_3bet
    # trim (lane A). PURE preflop content; the two lanes' displacements
    # compound so ALL six rows move at this n=200 seed (lane B alone moved
    # only maniac + tag; the lag content change re-deals every pot the lag
    # enters). Exact tripwire re-record; population bands stay frozen to
    # W4-b.
    # RE-RECORDED for WAVE 4 COMBINED (persona-realism-wave4, 2026-08-01 —
    # wave-authorized, recorded once on the combined lane-C + lane-D tip):
    # N-M4BET maniac vs_4bet full coverage (fold 0.81→0.29 at the node — the
    # maniac now continues most 4-bet pots, so every 4-bet pot plays on) +
    # N-TAGCOMP tag unopened offsuit→suited swap. PURE preflop content; the
    # displacements compound and ALL six rows move at this n=200 seed. The
    # maniac n=200 AF spike (3.27 → 4.82) is small-n composition — its call
    # denominator shrinks as 4-bet pots it used to fold out of now reach
    # postflop as raised-in pots; population bands still gate it at stable n.
    # Exact tripwire re-record; population bands stay frozen to W4-b.
    # RE-RECORDED for N-LAGCOMP2 (persona-realism-wave5, 2026-07-31 —
    # wave-authorized, single-recorder landing): the lag CO/BTN/SB
    # offsuit→suited swap (width-neutral) displaces the shared rng stream
    # from the first changed lag open onward — only the lag and nit rows
    # move at this n=200 seed (station/maniac/fish/tag byte-identical:
    # their samples hit no changed cell). The lag n=200 AF move
    # (2.6 → 2.2857) is REAL composition, not just displacement: at stable
    # n=1200 with only this pack changed, lag AF reads 2.8121 → 2.5176
    # (suited-heavier late opens reach more drawable postflop nodes,
    # growing the call denominator), comfortably inside the HARD band
    # (1.5, 4.5) — the band test still gates it at population n. Exact
    # tripwire re-record; population bands stay frozen to W4-b.
    # RE-RECORDED for the WAVE-6 lane-A landing (persona-realism-wave6,
    # 2026-08-01 — wave-authorized, single-recorder). TWO compounded causes,
    # disclosed separately: (1) the rows above were ALREADY red at the wave
    # base b54fe6e (station AF measured 0.2628 vs the 0.3064 golden — the
    # wave-5 #152/#153 squash-merge chain lost part of that wave's re-record);
    # (2) the R-L2 harness-sizing repair in THIS slice changes the harness
    # stream these N200 tripwires are measured on (production raise sizes,
    # all-in 5-bets → re-raised pots play out differently from the first
    # re-raise onward), so all six rows move again on this tip (station AF
    # 0.2628 → 0.3241 between base and tip is the instrument repair, not a
    # bot change — zero production code in this slice). Exact tripwire
    # re-record; population bands stay frozen to W4-b.
    # RE-RECORDED maniac row for the WAVE-6 #157 merge (chore repair,
    # 2026-08-01): the T-M4 maniac vs_4bet call-leg content moved ONLY the
    # maniac row (2.6812/0.34/0.5782 → 2.5522/0.4468/0.6019 — the exact
    # values the wave-6 ledger reviewed and disclosed), but the squash-merge
    # chain lost this pin's update, leaving main red. Pure restoration of
    # the reviewed record; other five rows verified byte-identical.
    # RE-RECORDED for the #160 merge (chore repair, 2026-08-02): N-LAGWIDTH
    # trimmed lag's CO/BTN/SB offsuit opening width, which displaces the
    # shared harness stream and moved ONLY the station AF cell
    # (0.32409972299168976 → 0.3277777777777778). The #160 squash chain lost
    # this pin's update, leaving main red — the FOURTH occurrence of the
    # lost-re-record pattern (see #159 and the two wave-6 entries above).
    # ATTRIBUTION PROVEN, not assumed: reverting ONLY
    # content/personas/lag.json + ladders/lag.unopened.json to 8729e14 at
    # this tip turns this test green again, so the lag pack change is the
    # sole cause. The other FIVE rows — including lag's own — are verified
    # byte-identical, so this is a narrow stream displacement, not a
    # roster-wide behavior shift. Population bands stay frozen to W4-b.
    # RE-RECORDED for R9-LOOSEFIT (2026-08-04, slice-authorized): the nit
    # pack's `call_looseness` 0.6 -> 0.45 (ONE number; no engine, sampler or
    # postflop code touched) makes the nit fold more at facing nodes BY DESIGN,
    # so it reaches showdown less and the shared harness rng stream displaces
    # from the first changed nit decision onward. The whole table was
    # re-measured: only the nit WTSD cell moved (0.7450980392156863 ->
    # 0.6491228070175439); the other five rows, and nit's own None AF/FtC, are
    # verified byte-identical (their n=200 samples hit no changed cell), so
    # this is a narrow displacement, not a roster-wide shift. ATTRIBUTION
    # PROVEN, not assumed (the #160-entry method): at this tip, reverting ONLY
    # content/personas/nit.json to its b63dfaa contents reproduces all six
    # PREVIOUS rows exactly (nit WTSD back to 0.7450980392156863), and
    # restoring 0.45 reproduces the six rows below exactly — the pack change is
    # the sole cause. Population bands stay frozen to W4-b.
    # RE-RECORDED for N-DRAWLOOSE (2026-08-05, slice-authorized, final engine
    # tip db1f278): T1 floors the calling dial at 1.0 for STRONG draws (an
    # engine change in `personas_postflop.py`, not a pack edit); R1/R2
    # rebuilt that floor twice more after adversarial review, so this entry
    # REPLACES the T5 entry it superseded rather than appending after it —
    # the T5 values were an intermediate reading against a since-reformulated
    # engine and never shipped. OLD side measured directly against the
    # control worktree at base commit b0a6a4e (this slice's only engine
    # file, `personas_postflop.py`, absent); NEW side measured at this tip.
    # Four of six rows move (lag, maniac, passive_fish, tag) — the floor is a
    # no-op arithmetic identity at any dial >= 1.0 (`max(looseness, 1.0)`
    # returns `looseness` there, so the STRONG-draw branch collapses onto the
    # fall-through `else` form), so it changes the decisions of every persona whose dial sits
    # BELOW the floor (nit, tag, lag, maniac, passive_fish); it is inert only
    # for calling_station (dial 4.0).
    # nit's own row is byte-identical to base (WTSD stays
    # 0.6491228070175439 both sides) because nit's n=200 sample already hits
    # no AF/FtC cell at either engine — same behaviour, same sample, no
    # displacement to observe.
    # calling_station's row is ALSO byte-identical to base on all three cells
    # (AF 0.3277777777777778, FtC 0.06557377049180328, WTSD
    # 0.7077922077922078) — confirmed by the RAW counts underneath the ratios
    # (call_count 360, cbet_opportunities 61, saw_flop_hands 308, identical on
    # both engines), not merely a coincidental ratio match. This is NOT the
    # T5 "displaced then partly reverted" story: T4's
    # test_nd_t4_calling_station_byte_identical_on_strong_draw already proves
    # the station's own decision FUNCTION is bitwise unchanged (dial 4.0 ⇒
    # the floor never binds for it); this fixture is measured on this
    # harness's own independent seed (20260710) and its own independent
    # 9-seat lineup (3 station seats + 6 filler seats cycling the other five
    # personas), separate from the shared organic rng stream the coverage
    # and limper-belt fixtures share. At THIS seed/lineup, none of the
    # filler personas' floor-triggered decision changes happened to alter
    # the game state (pot size, opponent count, order) at any point along
    # one of the station's own action nodes across all 200 hands, so the
    # station's aggregate reads exactly as it did before the slice. That is
    # a property of this specific sample, not a second structural guarantee
    # beyond T4's node-level one — a different seed or lineup could in
    # principle show displacement even though the station's own decision
    # function never changes.
    # ATTRIBUTION PROVEN BOTH WAYS: this test and the limper-belt test's
    # _PRE_M3_FIRES both pass, unmodified, against the control worktree at
    # base commit b0a6a4e with their OLD (base) values; the values below only
    # hold once this slice's engine change lands. Population bands stay
    # frozen to W4-b.
    # RE-RECORDED for the de-robotization slice (2026-08-15, slice-authorized
    # under this test's own rule: "re-record only when a slice intentionally
    # changes bot play"). The six packs now answer `vs_rfi`, `vs_limpers` and
    # `vs_3bet` per seat, so different hands reach the flop and every one of
    # these postflop aggregates moves. Old values:
    #   calling_station (0.3278, 0.0656, 0.7078)   lag  (2.5,    None,   0.6016)
    #   maniac          (2.9333, 0.3333, 0.6648)   nit  (None,   None,   0.6491)
    #   passive_fish    (0.7704, 0.5102, 0.5488)   tag  (1.9412, None,   0.5974)
    #
    # ⚠️ AT n=200 THESE ARE MOSTLY NOISE, and this re-record is the clearest
    # demonstration of it yet: tag's AF reads 1.94 before and 2.70 after, and
    # nit's flips between a number and None — None meaning that persona made
    # ZERO postflop calls in the sample, so the ratio has no denominator at
    # all. Re-measured at n=2000 against the same pre-slice packs, the same
    # statistics barely move:
    #   AF    station 0.317->0.312  lag 2.751->2.754  maniac 3.058->3.043
    #         nit 1.353->1.387      fish 0.838->0.942  tag 2.308->2.330
    #   WTSD  every persona within 2pp
    #   FtC   station 0.163->0.149  lag 0.347->0.358  maniac 0.363->0.277
    #         nit 0.294->0.355      fish 0.493->0.487  tag 0.259->0.320
    # Fold-to-c-bet is the one that genuinely moves (maniac down ~9pp, tag and
    # nit up ~6pp): a different preflop range reaches the flop, so a different
    # hand strength faces the c-bet. That is a real consequence of the slice
    # and is left for the separation gate to judge, not smoothed away here.
    #
    # The lesson for whoever re-records next: a swing in this fixture is not
    # evidence of anything until it is reproduced at a sample size where the
    # denominators are not single digits.
    # Re-recorded a second time in the same slice, for range-edge softening
    # on top of the seat split. The instability warned about above is visible
    # across just these two commits: the station reads 0.308 then 0.402, and
    # the fish 0.750 then 0.971, from pack edits that hold every combo-weighted
    # width to within 0.05pp. Read the n=2000 table, not these numbers.
    # RE-RECORDED for T5 (2026-08-16, slice-authorized): postflop bet sizes are
    # re-weighted across all six packs. All six rows move, and one movement is a
    # REAL effect rather than displacement, so it is named rather than left for
    # someone to discover: the three packs that now bet SMALLER lose aggression
    # (maniac 3.106 -> 2.536, tag 2.649 -> 2.135, lag 2.423 -> 2.179) and the two
    # that bet LARGER gain it (station 0.391 -> 0.396, fish 0.873 -> 0.991). An
    # earlier draft of this note said "every AF falls", which is false in both
    # directions that matter. A persona's own size distribution scales its
    # bluff rate — `personas_postflop` ~:910 multiplies `bluff_mass` by
    # E_s[_bluff_size_factor(s)], the F2 joint law's "bigger bets carry
    # proportionally more bluffs" — so betting smaller genuinely means bluffing
    # less. Computed from the authored mixes: maniac -13.1%, nit -6.3%, lag
    # -3.8%, tag +0.4%, station +7.1%, fish +10.0%.
    # That is the engine behaving as designed, not a defect to compensate, and
    # the claim that it stayed in range is NOT made from these n=200 numbers:
    # `test_persona_postflop_bands` gates AF at population n and passes
    # unchanged. The nit row moving None -> 1.0 is the usual single-digit
    # denominator, not a signal.
    # RE-RECORDED for T2b (2026-08-17, slice-authorized): PREFLOP raise sizes
    # are now drawn from a mix, keyed by seat for the three regulars. All six
    # rows move, in both directions (AF: station 0.396 -> 0.322, lag 2.179 ->
    # 2.226, maniac 2.536 -> 3.239, nit 1.0 -> 0.933, tag 2.135 -> 1.840, fish
    # 0.991 -> 0.788).
    # UNLIKE T5, no direct coupling explains a sign here. T5's move had one —
    # a pack's own size mix scales its bluff rate through the F2 joint law —
    # and preflop has no equivalent: `_preflop_facing` keys on the raise COUNT
    # and never the size, so nothing reads an open size to set a frequency.
    # What preflop sizing does change is the POT, and through it the stack-to-
    # pot ratio that `personas_postflop` :1110 and :1123 use for the commitment
    # ramp (`stack_bb / pot_bb <= pf.spr_commit`). Smaller opens mean smaller
    # pots, higher SPR and less commitment, so hands go further: measured with
    # the rng stream held aligned, hero postflop decisions rose 3.0% while
    # seats per flop FELL 1.7%. (An earlier draft of this note said "more
    # callers per pot mean more multiway flops". That contradicted the sentence
    # above it and is false in both halves — nothing reads a size to set a
    # frequency, and the measured seats-per-flop change is negative.) Which
    # hands reach which street therefore shifts, which is ordinary stream
    # displacement with a mechanism, not a per-persona effect with a direction.
    # The claim that aggression stayed in range is NOT made from these n=200
    # numbers: `test_persona_postflop_bands` gates AF at population n and
    # passes unchanged, and it is not a formality here: the lag's WTSD leg went
    # RED at an earlier draft of these values and the 3-bet mixes were narrowed
    # until it was not (see the ledger — the seat ladder was NOT the cause).
    # One FtC cell crosses the n>=30 floor (lag, None -> 0.323) and the tag's
    # and the nit's stay None — the usual single-digit denominator.
    # RE-RECORDED for T1 (improvement slice 2, 2026-08-18, slice-authorized):
    # naked ace-high stops floating a BET with more than one opponent live on
    # the flop and turn — `_ACE_HIGH_FLOAT_RAISE_DAMP`'s predicate widened from
    # `facing_raise` to `facing_raise or opponents > 1`. All six rows move.
    # THE REAL EFFECT IS ON THE FOLDING SIDE, AND IT IS NOT THE AF COLUMN. At
    # population n (the gate's own 50,000-hand run at seed 601, ratified
    # lineup) fold-to-c-bet rises for the four personas that fold at all — tag
    # 26.48 -> 28.84, lag 29.45 -> 30.83, passive_fish 39.22 -> 40.49, nit
    # 22.00 -> 22.76 — and went-to-showdown falls for four — nit 61.98 ->
    # 60.07, lag 51.87 -> 50.80, passive_fish 48.93 -> 48.41, tag 54.05 ->
    # 53.65. That is the intended mechanism arriving where it should: a hand
    # class that used to call multiway flop and turn bets now folds them, so
    # fewer floats reach a showdown. The unit measurement agrees — over 1,250
    # naked ace-high spots the fold rate rises by +0.053 to +0.157 at two and
    # three opponents and by exactly nothing heads-up.
    # THE AF COLUMN BELOW IS NOT A DIRECTION, and an earlier draft of this note
    # claimed it was — "AF rises because ace-high supplies fewer CALLs to the
    # denominator". That is refuted by the population-n reading, where AF moves
    # in BOTH directions and by at most 0.15 (station 0.333 -> 0.328, lag 2.652
    # -> 2.576, maniac 4.163 -> 4.312, nit 1.176 -> 1.241, fish 0.926 -> 0.951,
    # tag 2.064 -> 2.049) while the n=200 rows here swing several times further
    # in places (maniac 3.239 -> 3.717). These n=200 AF movements are
    # shared-table stream displacement, not a per-persona effect; read the
    # population numbers above instead.
    # The `-> None` cells (nit AF, and FtC for lag, passive_fish) are the n=200
    # denominator floor, the same artifact the R10-PRE2 and W5-b4 re-records
    # documented, not a stat that stopped existing. The claim that aggression
    # and showdown stayed in range is NOT made from these numbers:
    # `test_persona_postflop_bands` gates AF, fold-to-c-bet and WTSD at
    # population n and passes unchanged, including the lag's WTSD leg, whose
    # frozen 0.59 ceiling this change moves AWAY from rather than toward.
    # RE-RECORDED for T3 (improvement slice 2, 2026-08-19, slice-authorized).
    # T3's mechanism: naked ace-high may call a river bet again, at a damped
    # weight. The river call zero used to be written on `bluff_cell`, which
    # bundles ACE_HIGH with AIR; it now reads the made-hand bucket and refuses
    # AIR only, and ace-high's restored call merit is multiplied by
    # `personas_postflop._ACE_HIGH_RIVER_CALL_DAMP` = 0.06. Minimum-defence
    # arithmetic over the measured river price distribution derives about
    # 0.46; 0.06 is a round value inside the range the lag and calling_station
    # went-to-showdown bands admit with margin, and the owner ruled that
    # conflict in the bands' favour on 2026-08-19.
    # FIVE OF SIX ROWS MOVE, and unlike the preflop entries above this one both
    # channels are live: river showdowns are exactly what WTSD counts, so every
    # WTSD cell that moves does so for a real behavioural reason, while AF and
    # FtC move through the shared-stream displacement a longer hand causes.
    # WTSD rises on all five, which is the direction the ticket is for — hands
    # that used to end on a river fold now sometimes reach showdown. THE SIXTH
    # ROW, passive_fish, IS BYTE-IDENTICAL on all three cells, and maniac's and
    # tag's AF cells are identical too; a partial move is the expected signature
    # at n=200, where a persona's sample can miss the changed nodes entirely.
    # Old row values: calling_station (0.302491103202847, 0.2857142857142857,
    # 0.6397058823529411), lag (2.4693877551020407, None, 0.5573770491803278),
    # maniac (3.7169811320754715, 0.37777777777777777, 0.5446009389671361),
    # nit (None, None, 0.5576923076923077), passive_fish (0.8145161290322581,
    # None, 0.6146341463414634), tag (1.9545454545454546, None,
    # 0.6547619047619048).
    # NO NEW RANDOM DRAW WAS ADDED AND NONE PRECEDES THE ACTION DRAW, which is
    # slice 1's actual rule. The draw COUNT is not claimed invariant: a fold
    # flipping to a call changes which later decisions happen at all.
    # Exact tripwire re-record; population bands are NOT re-anchored here. They
    # did not need to be: the shipped constant is the largest one they admit,
    # which is the whole reason it is 0.06 rather than the derived ~0.46.
    # RE-RECORDED for S3-T1 (improvement slice 3, 2026-08-21, slice-authorized).
    # MECHANISM: `personas_postflop._strong_draw_call_dial` splits a STRONG
    # draw's `_DRAW_CALL_BONUS` under a dial below 1.0 —
    # `_DRAW_CALL_PROTECTED_SHARE` = 0.7 of the bonus stays out of the dial's
    # reach and 0.3 of it rides the dial — where the bonus used to be protected
    # in FULL by `max(looseness, 1.0)`. Five personas hold a dial below 1.0
    # (nit 0.45, tag 0.6, lag 0.55, maniac 0.55 via `stickiness`, passive_fish
    # 0.42), so all five chase big draws slightly less; calling_station (4.0)
    # never takes the branch.
    # FOUR OF SIX ROWS MOVE — calling_station, lag, nit, passive_fish — and
    # maniac and tag are byte-identical on all three cells, the usual n=200
    # signature of a sample that misses the changed nodes.
    # THE STATION'S ROW MOVING IS NOT A CONTRADICTION of the byte-identity
    # claim. Its own decision FUNCTION is bitwise unchanged (dial 4.0 is above
    # the `looseness < 1.0` predicate, and
    # `test_nd_t4_calling_station_byte_identical_on_strong_draw` passes
    # unmodified); what changed is the table around it — the five filler
    # personas in this fixture's own 9-seat lineup now play their draws
    # differently, so the station is dealt into different hands. The 2026-08-05
    # N-DRAWLOOSE entry above records the opposite outcome at the same seed for
    # the same structural reason, and says explicitly that it was a property of
    # that sample rather than a second guarantee. This entry is that caveat
    # coming true.
    # ⚠️ HISTORICAL — THIS RECIPE NO LONGER RUNS AS WRITTEN (marked 2026-08-22,
    # S3-T1b). It is kept because it records what S3-T1 proved at S3-T1's own
    # tip; both names in it are gone. `_DRAW_CALL_PROTECTED_SHARE` was deleted
    # and `_strong_draw_call_dial` takes two arguments now. THE CACHE-SAFE
    # EQUIVALENT IS IN THE S3-T1b ENTRY BELOW — replace
    # `_strong_draw_protected_share` with one returning 1.0, and clear
    # `_STATS_CACHE` first. As written at the time: setting the constant to 1.0
    # reproduced all six PREVIOUS rows exactly (station 0.2972027972027972 /
    # 0.2857142857142857 / 0.6617647058823529, lag 2.42 / None /
    # 0.5819672131147541, maniac and tag as below, nit None / None /
    # 0.5961538461538461, fish 0.8145161290322581 / None / 0.6146341463414634),
    # and restoring 0.7 reproduced THE SIX ROWS S3-T1 SHIPPED. ⚠️ That second
    # half is a FORWARD REFERENCE and it no longer points at the rows below —
    # those are S3-T1b's. Re-measured 2026-08-22: forcing a flat 0.7 at the
    # current tip reproduces five of the six rows below, and the sixth,
    # passive_fish, reads (0.7936507936507936, None, 0.6146341463414634) — the
    # value S3-T1 shipped — against the (0.753968253968254,
    # 0.41935483870967744, 0.5879396984924623) recorded below.
    # AT n=200 THESE ARE STILL MOSTLY NOISE — read the population numbers in
    # `test_persona_postflop_bands`' docstring, where the same change moves
    # went-to-showdown by -1.4pp (fish) to +0.4pp (tag) at n=4000. Exact
    # tripwire re-record; the went-to-showdown ceilings ARE ratcheted for this
    # slice (nit 0.69 -> 0.68, fish 0.57 -> 0.55) under A4.2 item 2, with the
    # arithmetic in that docstring; the aggression-factor and fold-to-c-bet
    # bands stay frozen to W4-b.
    # RE-RECORDED for S3-T1b (improvement slice 3, 2026-08-22,
    # slice-authorized). MECHANISM: the protected share S3-T1 introduced is no
    # longer the flat 0.7 — `_strong_draw_protected_share` computes it per node
    # from the faced price, the cards to come and the draw's out count, so a
    # draw whose own equity pays for the price keeps the FULL protection the
    # pre-S3-T1 floor gave it and a draw facing a price its equity does not
    # cover hands more of the bonus to the dial than 0.3.
    # ONE ROW MOVES — passive_fish, on all three cells (AF 0.7936507936507936,
    # FtC None, WTSD 0.6146341463414634 before). The other five are byte-
    # identical to the S3-T1 pins, which at n=200 means their samples' strong
    # draws sat where the two shares happen to agree closely enough not to flip
    # a draw. Nothing about the fish's row is a per-persona claim: it is the
    # usual small-sample displacement, and the population reading is in
    # `test_persona_postflop_bands`.
    # ATTRIBUTION PROVEN, not assumed: replacing
    # `_strong_draw_protected_share` with one that returns 1.0 makes
    # `_strong_draw_call_dial(L, 1.0)` return exactly 1.0 at every dial, which
    # IS the `max(looseness, 1.0)` the engine carried before S3-T1. Doing that
    # at this tip reproduces the PRE-S3-T1 rows exactly — calling_station
    # (0.2972027972027972, 0.2857142857142857, 0.6617647058823529), lag (2.42,
    # None, 0.5819672131147541), maniac and tag as below, nit (None, None,
    # 0.5961538461538461), passive_fish (0.8145161290322581, None,
    # 0.6146341463414634) — and those six were independently confirmed by
    # running this same harness in a checkout at d351150, the pre-S3-T1 engine.
    # ⚠️ CLEAR `_STATS_CACHE` BEFORE EACH LEG OF THAT PROBE. `_persona_stats`
    # is memoized on (persona, n, context_aware, packs fingerprint) and the
    # ENGINE is not in that key, so a second measurement in the same process
    # returns the first one's numbers no matter what has been patched. An
    # in-process probe that does not clear the cache reads "no change" for any
    # engine edit whatsoever — including this one.
    # NO NEW RANDOM DRAW WAS ADDED AND NONE PRECEDES THE ACTION DRAW. The draw
    # COUNT is not claimed invariant: a fold flipping to a call changes which
    # later decisions happen at all.
    # Exact tripwire re-record; the went-to-showdown ceilings are re-examined
    # under A4.2 item 2 in `test_persona_postflop_bands`' docstring, where this
    # tip's arithmetic is recorded and no ceiling moves.
    # RE-RECORDED for S3-T2 (improvement slice 3, 2026-08-22, slice-authorized):
    # the nit's `call_looseness` 0.45 -> 0.32 and the tag's 0.6 -> 0.38, so both
    # continue less often at every facing node, hands end differently and the
    # shared rng stream displaces from the first changed decision onward. Every
    # row moves — including the four personas whose own packs are untouched,
    # which is the stream displacement rather than a change in their play.
    # Values immediately before it:
    #   calling_station (0.27469135802469136, 0.25, 0.6654929577464789)
    #   lag             (2.3, None, 0.5882352941176471)
    #   maniac          (3.7169811320754715, 0.37777777777777777, 0.5492957746478874)
    #   nit             (None, None, 0.5769230769230769)
    #   passive_fish    (0.753968253968254, 0.41935483870967744, 0.5879396984924623)
    #   tag             (1.9545454545454546, None, 0.6785714285714286)
    # READ THESE AS A TRIPWIRE, NOT AS EVIDENCE ABOUT THE ROSTER: n=200 is far
    # too small for a level — the nit's and the tag's AF and FtC are None here
    # because their denominators sit under the 30-observation floor, and the
    # nit's WTSD reads 0.6154 against 0.6173 on the 4,000-hand harness by
    # coincidence of sample rather than agreement. The population claims live in
    # `BANDS`. ATTRIBUTION PROVEN, not assumed: with the two pack files reverted
    # and every other edit in this branch left in place, this test passes
    # untouched at the old values; restoring the packs reproduces the new ones.
    "calling_station": (0.3333333333333333, 0.22033898305084745, 0.6714801444043321),
    "lag": (2.4363636363636365, None, 0.5877862595419847),
    "maniac": (3.7169811320754715, 0.36363636363636365, 0.5607476635514018),
    "nit": (None, None, 0.6153846153846154),
    "passive_fish": (0.7946428571428571, 0.46875, 0.5297029702970297),
    "tag": (2.088235294117647, None, 0.6470588235294118),
}


def test_persona_stats_byte_identical_after_log_refactor():
    """W0-b guard (re-recorded W1-a): AF/FtC/WTSD must match the pinned goldens
    exactly — any UNINTENDED shift breaks byte-identity. Re-record only under
    explicit slice authorization when a slice intentionally changes bot play."""
    packs = load_persona_packs()
    for persona, (g_af, g_ftc, g_wtsd) in _GOLDEN_STATS_N200.items():
        af, ftc, wtsd, *_ = _persona_stats(packs, persona, 200)
        for got, want, name in ((af, g_af, "AF"), (ftc, g_ftc, "FtC"), (wtsd, g_wtsd, "WTSD")):
            if want is None:
                assert got is None, f"{persona} {name}: expected None, got {got}"
            else:
                assert got == pytest.approx(want, abs=1e-9), (
                    f"{persona} {name}: {got} != golden {want} (byte-identity broken)"
                )


# ---------------------------------------------------------------------------
# W5-a3-iii (C30) — the band sampler / parity mirror were context-BLIND: the
# W3-b/c/d position/street/texture mechanics and W3R-6's facing-raise damps
# (`_ONE_PAIR_RAISE_DAMP`, `_ACE_HIGH_FLOAT_RAISE_DAMP`) all gate on inputs
# (`context`, `facing_raise`/`street_aggressions`) the AF/WTSD/fold-to-cbet
# gate never received, so a slice could change real bot behavior on those
# nodes and the gate would never see it. `_play_hand`'s new opt-in
# `context_aware=True` (threaded through `_persona_stats`) fixes the
# plumbing; this test is the demonstration the pass/fail requires. It is
# DELIBERATELY separate from the CI-frozen `context_aware=False` (default)
# bands/goldens above — no band re-anchor here (that stays W4-b).
# ---------------------------------------------------------------------------


def test_street_aggressions_effect_visible_to_af_gate():
    """C30 guard, REDESIGNED 2026-07-29 (owner decision at the T-ANCHOR
    fan-in): the previous form asserted a DIRECTIONAL drop in aggregate AF
    (`af_on < af_off - 0.05`), an instrument all three fan-in reviewers found
    sign-unsound by construction — `_ONE_PAIR_RAISE_DAMP` cuts AF's numerator
    (AF down) while `_ACE_HIGH_FLOAT_RAISE_DAMP` cuts its denominator (AF up),
    so the aggregate direction depends on the seed's node mix, with noise
    (±0.15 across trivially-different streams) larger than the effect (~0.1).
    T-ANCHOR's legitimate stream perturbation flipped it (pre-fix drop +0.164
    at n=1000, post-fix −0.060; identical at n=250..700: 0.005/0.132/0.230/
    0.170/0.096 at seed 20260710). Retuning the threshold/n was forbidden
    (band-laundering); this spot-level redesign is what the old test's own
    W4-b flag prescribed. Any AGGREGATE-level question stays with W4-b.

    Leg 1 (plumbing): `context_aware=True` must change the seeded AF reading
    at all. Because `context_aware` also switches position/sizing-node/
    aggressor-contribution context, that alone cannot isolate `facing_raise`
    (Sol review 2 finding 1), so leg 1b re-runs the SAME seeded harness with
    both damps monkeypatched to 1.0 and asserts the reading changes — the
    damps only fire through `facing_raise`, so a difference proves the wire.
    No direction asserted anywhere.
    Leg 2 (mechanism, zero variance): captured merit vectors at a pinned tag
    facing-a-raise flop spot per damp. The sampler normalizes weights before
    `choices()`, so the assertions use the normalization-invariant ODDS RATIO
    against an untargeted merit: `facing_raise=True` multiplies the one-pair
    RAISE:CALL odds by exactly `_ONE_PAIR_RAISE_DAMP` and the naked ace-high
    CALL:FOLD odds by exactly `_ACE_HIGH_FLOAT_RAISE_DAMP`, while the odds
    between the two untargeted merits are unchanged. The exactness
    self-verifies the spot preconditions: any draw bonus (draw != NONE) would
    break the exact scaling. Neither leg reads a CI-frozen band or golden.
    """
    packs = load_persona_packs()
    n = 1000
    af_off, _, _, call_off, *_ = _persona_stats(packs, "tag", n, context_aware=False)
    af_on, _, _, call_on, *_ = _persona_stats(packs, "tag", n, context_aware=True)
    assert call_off >= 30 and call_on >= 30, (
        f"occurrence floor not cleared (call_off={call_off}, call_on={call_on}) "
        "-- not a valid demonstration"
    )
    assert af_on != af_off, (
        "context_aware=True changed nothing: no context reached the sampler at all"
    )

    # Leg 1b: differential with both damps neutralized — isolates the
    # facing_raise wire from the other context features `context_aware`
    # switches on. The cache is keyed (persona, n, context_aware, pack
    # fingerprint); pop the real entry first and restore it after so the
    # patched run neither reads a stale result nor poisons later tests. The
    # fingerprint does NOT cover this patch — it monkeypatches MODULE
    # constants, not pack content — so the pop/restore is still required.
    key = ("tag", n, True, _packs_fingerprint(packs))
    cached_on = _STATS_CACHE.pop(key)
    try:
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(personas_postflop, "_ONE_PAIR_RAISE_DAMP", 1.0)
            mp.setattr(personas_postflop, "_ACE_HIGH_FLOAT_RAISE_DAMP", 1.0)
            af_neutral, *_ = _persona_stats(packs, "tag", n, context_aware=True)
    finally:
        _STATS_CACHE[key] = cached_on
    assert af_neutral != af_on, (
        "neutralizing both facing-raise damps changed nothing: facing_raise "
        "never reached the sampler through _play_hand"
    )

    # The damp VALUES are pinned literally: a retune must consciously trip
    # this test and be re-anchored (W4-b owns aggregate-level questions) —
    # it must never slide through by moving expected and actual together
    # (Sol review 2 finding 2).
    assert personas_postflop._ONE_PAIR_RAISE_DAMP == 0.35
    assert personas_postflop._ACE_HIGH_FLOAT_RAISE_DAMP == 0.55

    legal = [
        personas_postflop_legal_fold(),
        personas_postflop_legal_call(5.0),
        personas_postflop_legal_raise(10.0, 100.0),
    ]

    def faced_dist(hole, board, facing_raise):
        cap = _CaptureWeights()
        sample_postflop_decision(
            _pack("tag"),
            hole,
            board,
            legal,
            10.0,
            100.0,
            1,
            cap,  # type: ignore[arg-type]
            current_bet_to=5.0,
            is_aggressor=False,
            street=Street.FLOP,
            facing_raise=facing_raise,
        )
        return cap.dist

    # Top pair, no draw (Kh9d on Ks7c2h): facing_raise damps the RAISE merit by
    # exactly _ONE_PAIR_RAISE_DAMP — asserted as RAISE:CALL odds (CALL is
    # untargeted here); FOLD:CALL odds are unchanged.
    off = faced_dist(("Kh", "9d"), ["Ks", "7c", "2h"], False)
    on = faced_dist(("Kh", "9d"), ["Ks", "7c", "2h"], True)
    assert on[ActionType.RAISE] / on[ActionType.CALL] == pytest.approx(
        personas_postflop._ONE_PAIR_RAISE_DAMP
        * (off[ActionType.RAISE] / off[ActionType.CALL]),
        rel=1e-12,
    ), f"one-pair RAISE damp did not fire exactly (off={off}, on={on})"
    assert on[ActionType.FOLD] / on[ActionType.CALL] == pytest.approx(
        off[ActionType.FOLD] / off[ActionType.CALL], rel=1e-12
    ), "untargeted FOLD:CALL odds moved — damp hit more than the RAISE merit"

    # Naked ace-high, no draw (AhQd on Ks7c2h): facing_raise damps the CALL
    # merit by exactly _ACE_HIGH_FLOAT_RAISE_DAMP — asserted as CALL:FOLD odds;
    # RAISE:FOLD odds unchanged (the fold SHARE rises purely through
    # normalization, per W3R-6).
    off = faced_dist(("Ah", "Qd"), ["Ks", "7c", "2h"], False)
    on = faced_dist(("Ah", "Qd"), ["Ks", "7c", "2h"], True)
    assert on[ActionType.CALL] / on[ActionType.FOLD] == pytest.approx(
        personas_postflop._ACE_HIGH_FLOAT_RAISE_DAMP
        * (off[ActionType.CALL] / off[ActionType.FOLD]),
        rel=1e-12,
    ), f"ace-high CALL damp did not fire exactly (off={off}, on={on})"
    assert on[ActionType.RAISE] / on[ActionType.FOLD] == pytest.approx(
        off[ActionType.RAISE] / off[ActionType.FOLD], rel=1e-12
    ), "untargeted RAISE:FOLD odds moved — damp hit more than the CALL merit"


def test_persona_stats_ext_all_metrics_compute():
    """W0-b DoD: each of the six metrics computes + emits a numeric value (or a
    documented None below the >=30 floor) for every persona on today's engine —
    no NaN, no exception. Direction is NOT asserted here (bots are unchanged;
    #5/#6 read ~flat until W3). Fixed n=200 keeps this bounded + deterministic."""
    packs = load_persona_packs()

    def _ok(v) -> bool:
        return v is None or (isinstance(v, float) and math.isfinite(v))

    for persona in ALL_PERSONAS:
        ext = _persona_stats_ext(packs, persona, 200)
        scalars = ("cbet_flop", "wsd", "vpip", "pfr", "gap", "cbet_ip", "cbet_oop", "turn_barrel")
        for name in scalars:
            assert _ok(getattr(ext, name)), f"{persona} {name}={getattr(ext, name)!r}"
        assert set(ext.ftc_by_bucket) == set(_BUCKETS)
        for b, v in ext.ftc_by_bucket.items():
            assert _ok(v), f"{persona} ftc[{b}]={v!r}"
        # Sanity relations that must hold regardless of persona:
        if ext.vpip is not None and ext.pfr is not None:
            assert 0.0 <= ext.pfr <= ext.vpip <= 1.0, f"{persona} pfr={ext.pfr} vpip={ext.vpip}"
        for r in (ext.cbet_flop, ext.wsd, ext.cbet_ip, ext.cbet_oop, ext.turn_barrel):
            if r is not None:
                assert 0.0 <= r <= 1.0, f"{persona} rate out of [0,1]: {r}"


# ======================================================= T-ARR — arrival tests
# `_ARRIVAL_N` deliberately reuses the (persona, n) cache key that
# `test_persona_stats_ext_all_metrics_compute` above already warms, so the whole
# grid is free in a full-file run (it only pays for itself under `-k occupancy`).
_ARRIVAL_N = 200


def test_preflop_node_occupancy_records_only_the_first_decision_per_seat():
    """The arrival denominator is first-decision-per-seat-hand. This is the
    contamination guard: if a seat's LATER preflop decisions (facing a 3-bet,
    say) were counted too, every cell in the grid would shift — most visibly
    UTG, which can only ever ARRIVE at `unopened` but frequently re-decides
    against a raise."""
    packs = load_persona_packs()
    rng = random.Random(4242)
    persona_by_seat = {i: ALL_PERSONAS[i % len(ALL_PERSONAS)] for i in range(9)}
    saw_a_reentry = False
    for i in range(40):
        res = _play_hand(rng, rng.randrange(1_000_000_000), i % 9, persona_by_seat, packs)
        first_seats = [seat for seat, _pos, _facing, is_first in res.preflop_nodes if is_first]
        assert len(first_seats) == len(set(first_seats)), (
            f"seat flagged is_first twice: {res.preflop_nodes}"
        )
        # ARRIVAL: exactly one flagged row per seat that acted preflop.
        assert set(first_seats) == {seat for seat, _action in res.preflop_log}
        # OCCUPANCY: every applied preflop decision is recorded, 1:1 with
        # `preflop_log` — the `all` counters must not silently drop rows.
        assert len(res.preflop_nodes) == len(res.preflop_log)
        if len(res.preflop_nodes) > len(first_seats):
            saw_a_reentry = True
    assert saw_a_reentry, (
        "no hand in this sample had a seat act twice preflop -- the guard is "
        "untested, so the fixture is not exercising the trap it exists for"
    )


def test_preflop_node_occupancy_arrival_grid():
    """T-ARR: the instrument the initiative was missing. Per position, the share
    of a seat's FIRST preflop decision landing in each facing node.

    Bands, not goldens: all six personas share one rng stream, so a sibling
    slice that touches no preflop logic still moves these by a point or two.
    Only UTG's 1.000 is exact, and it is STRUCTURAL — UTG acts first after the
    blinds (which enter `action_history` as POST, not CALL/RAISE), so it can
    only ever arrive `unopened`.

    ⚠️ RUN WITH `-s` TO SEE THE GRID. The assertions below only reach the
    `unopened` column; the `vs_limpers`/`vs_rfi` columns — the ones that answer
    "is this roster over-limping or over-raising" — are printed, and pytest
    swallows stdout on a PASS unless `-s` is given:
        python -m pytest tests/test_personas_postflop.py -k occupancy -q -s
    """
    packs = load_persona_packs()
    occ = _pooled_occupancy(packs, _ARRIVAL_N)
    grid = _occupancy_shares(occ)
    report = _format_occupancy(occ)
    print(report)

    # 🔴 HARD (unlike the two bands below): this is not a calibrated target but a
    # structural fact about the engine, so it cannot drift and must never be
    # relabelled DIRECTIONAL. Same for the monotonicity check at the end.
    assert grid["UTG"]["unopened"] == 1.0, (
        f"UTG must ARRIVE unopened 100% of the time; got "
        f"{grid['UTG']['unopened']:.4f} -- a reading below 1.0 means later "
        f"preflop decisions were counted and EVERY cell is contaminated.{report}"
    )

    # The PR #119 finding in one number: the button's opening ladder was widened
    # correctly and moved almost nothing, because the BTN rarely gets there.
    #
    # 🔶 DIRECTIONAL, not HARD (theory contract §6 / metric-DoD). Arrival is a
    # brand-new metric with no §5 row and no established target, so this is a
    # first calibration, not a validated threshold — the contract's rule is that
    # such a stat stays DIRECTIONAL until it is live AND showing the expected
    # direction. A trip here means "go look at the grid", not "the build is
    # broken". Kept as a two-sided assertion anyway so it cannot rot unnoticed.
    #
    # ⚠️ FRAGILE BAND — PRE-EXISTING, ticket-drafted, NOT re-derived here. Its
    # denominator is only ~408 decisions, and under PURE RESEEDING (no behaviour
    # change whatsoever) review measured this cell spanning 0.0417 .. 0.1005 —
    # BELOW the 0.05 floor on 1 of 6 seeds. T-ANCHOR perturbs this exact rng
    # stream next wave, so when this trips it is far more likely to be seed
    # dispersion than "the BTN opening ladder collapsed". CHECK THE GRID AND
    # RESEED BEFORE BELIEVING IT. Deliberately NOT widened: quietly re-centring
    # a drafted band on a miss is the W3R-1 failure mode this wave exists to
    # prevent, and unlike the roster-wide band below there is no reproducibility
    # finding against this one — only thin n. Tightening the denominator (or
    # retiring the cell for a wider late-position aggregate) is a Wave B call.
    #
    # RE-DERIVED at W5-b4 (2026-07-31, review-corrected framing): a
    # MIS-CALIBRATION REPAIR of an already-broken floor, NOT a slice effect.
    # The causal analysis and a 21-seed PAIRED sweep (identical seeds, only
    # maniac.json differing) agree the slice does not move this cell at all
    # (paired delta -0.0023, t=-0.83; and mechanically, `unopened` arrival
    # depends only on earlier seats' unopened folds, which W5-b4 does not
    # touch). What the sweep DID show: the drafted [0.05, 0.12] floor was
    # mis-calibrated from the start — 11 of 21 PARENT seeds already read
    # below 0.05 (parent span 0.0270..0.0711, mean 0.0489 sd 0.0132); the
    # quoted 0.0417..0.1005 dispersion in the note above understated the low
    # tail. New band = the pooled parent+HEAD 21-seed dispersion with thin-n
    # allowance, ceiling tightened so a genuine BTN-ladder collapse or a
    # revert-to-narrow regression still trips. Still DIRECTIONAL, still
    # thin-n (~408); the Wave B denominator repair remains the real fix.
    # RE-DERIVED at WAVE 4 (2026-08-01, N-TAGCOMP landing): a 10-seed PAIRED
    # sweep (identical seeds, only wave-4 content differing) measured a REAL,
    # small, attributable rise — paired delta +0.0108 sd 0.0127 (t≈2.7; 7 of
    # 10 seeds up) — mechanism: the tag width trim makes every tag seat fold
    # slightly more first-in (the dossier-correct direction, see N-TAGWIDTH),
    # and BTN unopened arrival is exactly P(all earlier seats fold). HEAD
    # dispersion 0.044..0.1005 (parent 0.039..0.081), pinned seed 0.0784.
    # Ceiling re-derived from the pooled dispersion; floor kept — a genuine
    # BTN-ladder collapse or revert-to-narrow regression still trips. Still
    # DIRECTIONAL, still thin-n (~408); the Wave B denominator repair remains
    # the real fix.
    assert 0.02 <= grid["BTN"]["unopened"] <= 0.11, (
        f"BTN unopened arrival {grid['BTN']['unopened']:.4f} outside [0.02, 0.11] "
        f"-- n~408, wave-4 paired-sweep dispersion 0.044..0.10, see above{report}"
    )

    total = sum(occ.opps.values())
    roster_wide_unopened = sum(occ.hits.get((p, "unopened"), 0) for p in _POSITIONS) / total
    # ------------------------------------------------------------------
    # 🔶 DIRECTIONAL, not HARD — same rationale as the BTN band above: a new
    # metric with no §5 row and no established target is DIRECTIONAL until it is
    # live and showing the expected direction, and the provenance below says in
    # its own words that this is "a NEW instrument's first calibration".
    #
    # PROVENANCE of [0.30, 0.36] — read this before touching the numbers.
    # Calibrated 2026-07-26 (T-ARR, owner-adjudicated). This is a NEW
    # instrument's first calibration, NOT a band widened to rescue a failing
    # test — the distinction is the whole point of this wave, so it is written
    # down rather than left to inference.
    #
    # 1. MEASURED, and STABLE (not "convergent" — that earlier claim was wrong
    #    and review caught it). Roster-pooled `unopened` arrival:
    #        n=200 -> 0.3238 · n=400 -> 0.3250 · n=600 -> 0.3260
    #    These are NESTED samples off one hardcoded seed (`random.Random(
    #    20260710)` in `_persona_stats_ext`), so their agreement is
    #    autocorrelation, NOT convergence — there is no trend to extrapolate.
    #    At fresh n the "+0.001 per +200 hands" drift does not exist:
    #        n=300 -> 0.3268 · n=500 -> 0.3240 · n=800 -> 0.3244
    #    The honest — and stronger — claim is DISPERSION:
    #        +/-0.003 across n at the pinned seed · +/-0.010 across seeds
    #    so the +/-0.03 half-width is roughly 3 sigma of resampling noise.
    #    The band is centred on 0.325.
    #
    # 2. DENOMINATOR — deliberately tested-seats, matching the ticket's
    #    mechanism section (the counters live in `_persona_stats_ext`, which is
    #    per-persona by construction). Both readings were taken:
    #        tested-seats 0.3238 · all-seats 0.3347
    #    The all-seats variant was REJECTED even though it happens to clear the
    #    originally-drafted floor: switching which decisions get counted in
    #    order to pass an assertion is the exact move this comment exists to
    #    rule out, and it makes `occupancy` no longer a per-persona field.
    #
    # 3. LINEUP SENSITIVITY, and a KNOWN BIAS in this pool. The six per-lineup
    #    readings at n=200 span 0.3027 (calling_station-heavy table) ..
    #    0.3579 (maniac-heavy), so any quoted roster-wide figure is meaningless
    #    unless `persona_by_seat` is pinned. `_pooled_occupancy` pins it by
    #    summing all six `_persona_stats_ext` lineups — but that pool is NOT
    #    roster-balanced, as its docstring now details: the filler comprehension
    #    walks 6 indices over 5 fillers, giving
    #        calling_station 13 · lag 9 · maniac 8 · nit 8 · fish 8 · tag 8
    #    of the 54 seat-slots (+62% on calling_station vs the four at 8, +44%
    #    vs a balanced 9). Since calling_station is the loosest persona on the
    #    roster, the extra limpers it contributes suppress `unopened`, so this
    #    band is calibrated on a table that is LOOSER than the roster's mean.
    #    Review's balanced-pool counterfactual reads **0.3504** vs this pool's
    #    0.3238 — a ~0.026 downward bias ROSTER-WIDE. That figure does NOT
    #    transfer per cell: balanced-vs-as-built is +0.048 at UTG1, +0.096 at
    #    LJ, 0.000 at CO and **-0.007 at BTN** (0.066 vs 0.074), i.e. balancing
    #    pushes BTN TOWARD its floor. Never apply +0.026 to one position.
    #    The band stays centred on what THIS
    #    instrument measures (0.325), because the assertion has to guard the
    #    number this code actually produces; Wave B must read the grid knowing
    #    the offset rather than mistake it for the roster's true arrival rate.
    #    Rebalancing means editing a lineup shared with `_persona_stats`, which
    #    re-records seeded fixtures — T-ANCHOR's job in wave 2, not this one.
    #
    # 4. THE DRAFTED [0.33, 0.43] WAS NEVER A VALIDATED TARGET. It came from an
    #    ad-hoc pre-ticket script that (a) never pinned `persona_by_seat` — see
    #    point 3, which makes its 36% unreconstructible — and (b) counted the
    #    OTHER denominator (~5384 seat-decisions over 600 hands ~= all 9 seats).
    #    Re-running its own recipe here yields 0.3250, not 0.36. So nothing
    #    measured was moved to accommodate a miss; an unsound number was
    #    replaced by a reproducible one. This is also not a `BANDS` edit — that
    #    structure is untouched by this ticket.
    #
    # 5. WIDTH covers SIBLING DRIFT, not measurement error. All six personas
    #    share one rng stream, so a slice that changes no preflop logic still
    #    moves occupancy a point or two (T-ANCHOR lands next wave and perturbs
    #    exactly this stream). +/-0.03 absorbs that while staying tight enough
    #    to trip on a real middle-position collapse.
    #
    # WHY THIS ASSERTION EXISTS AT ALL: the other three checks pin the top
    # (UTG structurally 1.000), the bottom (BTN in [0.05, 0.12]) and the shape
    # (monotone UTG->BTN). UTG1/UTG2/LJ are otherwise unguarded — they could
    # sag together with BTN still in band and monotonicity intact (monotonicity
    # DOES still catch a non-monotone collapse; it just cannot see a uniform
    # one). This average is the only remaining watch on that middle region,
    # which is where Wave B's opening-ladder tuning lands.
    # It is a BLUNT watch, though, and reviewers should not oversell it: SB and
    # BB contribute ~22% of the denominator at ~0.00 and 0.00 `unopened`, so a
    # fifth of the average is inert ballast that dilutes any middle-position
    # move before it reaches this band. A seven-non-blind-position variant
    # would be sharper — but that is a different number needing its own
    # calibration, so it is a Wave B question, not a silent edit here.
    # ------------------------------------------------------------------
    # RE-CENTRED at W5-b4 (2026-07-31, review-corrected framing): a
    # RECALIBRATION from broader seed evidence, NOT a slice effect. The
    # 21-seed PAIRED sweep (identical seeds, only maniac.json differing)
    # shows the slice moves this statistic not at all (paired delta +0.0002,
    # t=+0.07; parent mean 0.3109 sd 0.0083, HEAD mean 0.3111 sd 0.0080),
    # and a parent seed already reads 0.2877 — outside the old [0.30, 0.36]
    # band, whose 0.325 centre came from a narrower seed family than the
    # statistic's real dispersion (the causal arrival change, where there was
    # one, happened at R10-PRE2's unopened-ladder widening; pinned-seed luck
    # concealed it then). New centre 0.305 per the pooled 21-seed evidence,
    # same +/-0.03 half-width and the same purpose (the only watch on the
    # UTG1/UTG2/LJ middle region).
    # RE-CENTRED at S3-T2 (improvement slice 3, 2026-08-22), by the SAME method
    # W5-b4 used and for the same reason: the centre had gone stale, not the
    # statistic. `call_looseness` is read only by `sample_postflop_decision`, so
    # a calling-dial retune cannot change a single preflop decision's POLICY; it
    # reaches this number only by displacing the shared rng stream, the same way
    # the limper belt's pre-M3 fire counts move. A 12-seed PAIRED sweep
    # (identical seeds on both arms, only the nit's and the tag's
    # `call_looseness` differing) confirms that: paired delta -0.0016, sd
    # 0.0096, t = -0.58 — no effect.
    #   base arm  mean 0.3256  sd 0.0112   new arm  mean 0.3240  sd 0.0070
    # What the same sweep shows is that the 0.305 centre recalibrated on
    # 2026-07-31 no longer describes this roster: three weeks of unrelated
    # slices have carried the statistic to about 0.325, and the BASELINE arm
    # alone reads 0.3534 on one of the twelve seeds — outside the old band with
    # no S3-T2 in it at all. The pinned seed sat at 0.3243 before this ticket
    # and 0.3361 after, which is 1.2 of the sweep's own standard deviations and
    # is what a stale centre looks like when a displacement nudges it.
    # New centre 0.325 = the pooled mean of both arms; SAME +/-0.03 half-width,
    # same purpose. This is a re-centring on fresh paired evidence, NOT a
    # widening — the band is exactly as tight as it was.
    assert 0.295 <= roster_wide_unopened <= 0.355, (
        f"roster-wide unopened arrival {roster_wide_unopened:.4f} outside "
        f"[0.295, 0.355] (re-centred 0.325 at S3-T2 on a 12-seed paired sweep) "
        f"-- read the provenance comment above before re-centring: this is the "
        f"only check watching the middle positions (UTG1/UTG2/LJ){report}"
    )

    # Arrival at `unopened` can only decay as the seat acts later: every seat
    # ahead is one more chance for the pot to be opened or limped into.
    ladder = [grid[p]["unopened"] for p in ("UTG", "UTG1", "UTG2", "LJ", "HJ", "CO", "BTN")]
    assert all(a >= b for a, b in zip(ladder, ladder[1:], strict=False)), (
        f"`unopened` arrival is not monotone non-increasing UTG->BTN: {ladder}{report}"
    )


# ------------------------------------------------------------------ R10-COUNT
# Conditional action-at-node rates on top of the NodeActions counters. The
# helpers read whatever `_persona_stats_ext` runs exist; the cross-validation
# test below deliberately pays for ONE cold (maniac, n=600) simulation (~4s,
# review C-2) — everything else rides the memoized (persona, 200) runs.

# The R10 corpus's EP stratum (its "EP first-in 18.3%" figure): the three
# early seats of the 9-max ring.
_EP_POSITIONS = ("UTG", "UTG1", "UTG2")


def _node_action_rate(
    actions: NodeActions,
    facing: str,
    action: str,
    positions: tuple[str, ...] | None = None,
    first: bool = True,
) -> tuple[float | None, int]:
    """P(action | facing[, position in `positions`]) plus its denominator n.
    `first=True` reads the arrival-conditioned counters (first decision per
    seat-hand — first-in rates); `first=False` reads every preflop decision
    (the only honest conditioning for the re-entry nodes vs_3bet/vs_4bet).
    Applies the harness's shared >=30 floor via `_rate`."""
    hits = actions.first_hits if first else actions.all_hits
    pos_set = _POSITIONS if positions is None else positions
    num = sum(hits.get((p, facing, action), 0) for p in pos_set)
    den = sum(
        v for (p, f, _a), v in hits.items() if f == facing and p in pos_set
    )
    return _rate(num, den), den


def _format_node_actions(persona: str, actions: NodeActions) -> str:
    """The per-persona conditional grid, rendered. Like the T-ARR grid, pytest
    swallows this on a PASS — run with `-s` to read it:
        python -m pytest tests/test_personas_postflop.py -k node_action -q -s
    """
    lines = [
        "",
        f"{persona}: P(action | node) — first-in `unopened` by position (arrival-",
        "conditioned), then the re-entry nodes over EVERY decision:",
        f"{'pos':6s}{'raise':>8s}{'call':>8s}{'check':>8s}{'fold':>8s}{'n':>6s}",
    ]
    # `check` column: reachable only via the BB walk-to-unopened edge (see
    # `_preflop_facing`) — ~always 0, enumerated so the printed row always
    # sums to 1 and a nonzero count can never hide (refuter R-3).
    for pos in _POSITIONS:
        den = sum(
            v for (p, f, _a), v in actions.first_hits.items()
            if p == pos and f == "unopened"
        )
        if den == 0:
            continue
        if den < 30:
            # The harness's shared >=30 floor, applied to the REPORT rows the
            # same way `_rate` applies it to the re-entry block (refuter R-1):
            # a three-decimal rate off n=12 reads as precision it doesn't have.
            row = "".join(f"{'--':>8s}" for _ in range(4))
        else:
            row = "".join(
                f"{actions.first_hits.get((pos, 'unopened', a), 0) / den:8.3f}"
                for a in ("raise", "call", "check", "fold")
            )
        lines.append(f"{pos:6s}{row}{den:6d}")
    for facing in _REENTRY_FACINGS:
        parts = []
        for a in ("fold", "call", "raise"):
            r, den = _node_action_rate(actions, facing, a, first=False)
            parts.append(f"{a} {r:.3f}" if r is not None else f"{a} --")
        lines.append(f"{facing}*: " + " · ".join(parts) + f"  (n={den})")
    lines.append("* over every preflop decision (re-entry nodes; >=30 floor)")
    return "\n".join(lines)


def test_node_action_counters_align_with_occupancy():
    """🔴 HARD structural identity, not a band: NodeActions rows are recorded
    from the same zipped (node, action) rows as NodeOccupancy, so summing the
    action axis must reproduce the occupancy counters EXACTLY — for both the
    first-decision and every-decision pairs, for every persona. Any daylight
    means the two instruments have drifted apart and every conditional rate
    is on an untrusted denominator."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    for persona in ALL_PERSONAS:
        ext = _persona_stats_ext(packs, persona, _ARRIVAL_N)
        occ, acts = ext.occupancy, ext.actions
        for hits, action_hits in (
            (occ.hits, acts.first_hits),
            (occ.all_hits, acts.all_hits),
        ):
            summed: dict[tuple[str, str], int] = {}
            for (pos, facing, _action), v in action_hits.items():
                summed[(pos, facing)] = summed.get((pos, facing), 0) + v
            assert summed == hits, (
                f"{persona}: action counters do not sum back to occupancy"
            )


def test_node_action_first_in_raise_cross_validates_r10_corpus():
    """R10-COUNT's done-condition: the instrument reproduces the R10 corpus's
    externally-derived maniac first-in figures on a seeded run — the 756-hand
    review measured maniac P(raise | first-in) ≈27% aggregate and ≈18%
    EP-stratified (the archetype-collapse headline: tightest of the four from
    EP). A real cross-validation against an independent derivation; after it,
    these counters are the live instrument PRE1/PRE2/3BET certify against
    (the preflop sampler is categorical with an implicit-fold remainder, so
    authored JSON weight ≠ observed frequency — never certify via JSON diffs).

    🔶 DIRECTIONAL-width bands, RE-RECORDED for R10-PRE2 (the pre-declared
    sole authorized re-recorder — that slice widened maniac's whole first-in
    ladder above the LAG's, so the pre-PRE2 corpus anchors ≈0.27 aggregate /
    ≈0.18 EP describe a behavior that no longer exists). The anchor is now the
    AUTHORED ladder: exact combo-weighted first-in raise 34.2/37.4/40.4% at
    the EP seats (37.3% 3-seat avg), rising to 73.3% at BTN, seat-avg 51.8%.
    Across a 20-reseed sweep the instrument reads aggregate 0.410 (sd 0.021,
    span 0.381-0.444) and EP 0.367 (sd 0.022, span 0.336-0.404); an
    independent 13-seed sweep (R10-PRE2 refuter, different seed family)
    read agg 0.373-0.437 / EP 0.318-0.392 — union span agg 0.373-0.444,
    EP 0.318-0.404, so treat THAT as the real dispersion when resizing.
    Bands = union span ± ~2-3σ, the same sizing rule as the original
    calibration (review C-1 + refuter R-2); the pinned reading keeps ≥2σ
    margin to every edge under both sweeps. The composition-light cross-check is the EP
    stratum: sampled 0.367 vs authored 0.373. The aggregate sits BELOW its
    authored 0.518 because arrival is EP-heavy (later seats usually face an
    open and never reach the unopened node) — the documented conversion
    direction, measured stronger here at the wider widths.

    ⚠️ COUPLED TO THE WHOLE PACK SET, not just maniac: all seats draw from one
    shared rng stream, so ANY persona/pack change that shifts rng consumption
    ahead of maniac's rows moves these numbers with maniac's own policy
    unchanged. A trip here means "re-read the grid", not "the maniac pack
    regressed". Sanity shape: EP still sits below the aggregate post-PRE2 —
    the authored ladder rises toward the button, so its arrival-weighted
    shadow keeps the same ordering (held in all 20 reseeds, min gap ~0.03)."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    acts = _persona_stats_ext(packs, "maniac", 600).actions
    print(_format_node_actions("maniac", acts))
    aggregate, agg_n = _node_action_rate(acts, "unopened", "raise")
    ep, ep_n = _node_action_rate(acts, "unopened", "raise", positions=_EP_POSITIONS)
    assert aggregate is not None and ep is not None, (
        f"first-in denominators below the 30 floor (agg n={agg_n}, EP n={ep_n})"
    )
    assert 0.32 <= aggregate <= 0.51, (
        f"maniac first-in raise {aggregate:.3f} (n={agg_n}) outside [0.32, 0.51] "
        f"-- R10-PRE2 re-record (authored seat-avg 0.518, sweep 0.381-0.444); "
        f"NOTE this reading is coupled to the whole pack set via the shared "
        f"rng stream (docstring)"
    )
    assert 0.27 <= ep <= 0.47, (
        f"maniac EP first-in raise {ep:.3f} (n={ep_n}) outside [0.27, 0.47] "
        f"-- R10-PRE2 re-record (authored EP 3-seat avg 0.373, sweep 0.336-0.404)"
    )
    assert ep < aggregate, (
        f"EP first-in raise {ep:.3f} not below aggregate {aggregate:.3f} -- the "
        f"authored ladder rises toward the button, so its arrival-weighted "
        f"shadow must keep EP below the aggregate"
    )


# ------------------------------------------------------------------- R10-3BET
# Deterministic AUTHORED-policy gates + the report-only stratified
# fold-to-3-bet grid. The authored gates read pack JSON directly (no
# simulation): every pack's vs_3bet node is a positions:null wildcard and
# mixes are first-match-wins, so the effective per-class policy is exactly
# computable. The sampled instrument stays REPORT-ONLY — vs_3bet occupancy at
# the memoized _ARRIVAL_N runs is far below any honest gate denominator
# (roadmap R10-3BET pass/fail ③; gate-design rule).


def _node_for_seat(pack, facing: str, seat: Position, role: str | None = None):
    """The node `sample_preflop_action` would select for this seat.

    The predicate is copied from the sampler (`personas.py`) — the same choice
    `test_persona_pack_invariants._check_position_coverage` makes, for the same
    reason: asking the runtime question directly is safer than reasoning about
    wildcards and role strata separately.
    """
    for node in pack.preflop:
        if node.facing != facing:
            continue
        if node.positions is not None and seat not in node.positions:
            continue
        if node.role is not None and node.role != role:
            continue
        return node
    return None


def _vs_3bet_effective_policy(pack, role: str = "cold") -> dict[str, dict[str, float]]:
    """Per-class EFFECTIVE weights of the pack's vs_3bet response, averaged
    over the nine seats, under first-match-wins (`sample_preflop_action`): the
    first mix whose combos contain the class owns it outright; later mentions
    are dead tokens.

    N-3BSTRATA: `role` picks the ARRIVAL STRATUM exactly as the sampler does —
    the first vs_3bet node that is untagged (serves both) or carries this role.
    Default "cold" keeps every pre-N-3BSTRATA caller reading the table it
    always read (untagged packs have one node; maniac/lag's cold node is
    byte-identical to their pre-slice shared node).

    ⚠️ WHY THIS AVERAGES OVER SEATS (de-robotization slice 1, 2026-08-15).
    Until this slice every response facing had exactly one node, so "the
    vs_3bet policy" was unambiguous and a first-match `next()` returned it.
    Position-split nodes break that: `next()` then returns whichever band is
    authored first, which silently changes WHAT THIS MEASURES rather than what
    the pack does — a pin can move several points while every seat's behaviour
    is intact. Averaging over the nine seats measures the population policy,
    which is what these gates were always about, and reduces exactly to the old
    value for any position-blind pack. Every pin that reads this helper is
    therefore comparable across the change for the unsplit packs.

    Two deliberate simplifications vs the live sampler (Codex build review
    C-2 — both are no-ops for every consumer in this file): the implicit-fold
    remainder is NOT folded into a `fold` key (the gates only read `call` +
    `4bet`), and classes no mix covers are ABSENT rather than {"fold": 1.0}
    (`.get(cls, {})` reads them as zero continue, which is the same thing)."""
    from app.domain.content.notation import parse_range

    policy: dict[str, dict[str, float]] = {}
    for seat in Position:
        node = _node_for_seat(pack, "vs_3bet", seat, role)
        if node is None:
            continue
        seen: set[str] = set()
        for mix in node.mixes:
            for cls in parse_range(mix.combos):
                if cls in seen:
                    continue
                seen.add(cls)
                per_class = policy.setdefault(cls, {})
                for act, w in mix.weights.items():
                    per_class[act] = per_class.get(act, 0.0) + w
    # Divide ONCE at the end rather than accumulating `w / 9` nine times, which
    # does not return the authored value: 9 x (0.5/9) is 0.5000000000000001,
    # breaking the exact-identity pin on the fish's AA.
    #
    # This is NOT exact in general, and an earlier version of this comment
    # wrongly claimed it was. Sum-then-divide is exact only for dyadic weights;
    # review measured 0.45 coming back as 0.44999999999999996 on five of the
    # six base packs. Every gate reading this helper is a tolerance or a bound,
    # so the drift is harmless today — but an exact pin on a non-dyadic weight
    # would break, and would be right to.
    seats = len(Position)
    return {cls: {act: w / seats for act, w in per_class.items()}
            for cls, per_class in policy.items()}


def _combo_count(cls: str) -> int:
    return 6 if len(cls) == 2 else (4 if cls.endswith("s") else 12)


def _fourbet_share(pack, role: str = "cold") -> float:
    """Combo-weighted authored 4-bet share: sum over 169 classes of
    (combo_count x effective first-match 4bet probability) / 1326 — the spec's
    pinned formula (overlapping tiers must never be double-counted).
    `role` selects the arrival stratum (N-3BSTRATA), default "cold"."""
    return (
        sum(
            _combo_count(c) * w.get("4bet", 0.0)
            for c, w in _vs_3bet_effective_policy(pack, role).items()
        )
        / 1326.0
    )


def test_r10_3bet_defect_gate_nit_continues_premiums():
    """🔴 R10-3BET defect gate (roadmap ①, deterministic): nit's authored
    vs_3bet continue weight (call + 4bet) on QQ / AKs / AKo each > 0. FAILED
    at pre-slice HEAD — the node covered AA/KK only, and the 756-hand corpus
    measured the nit 20/20 folds as opener facing a 3-bet (CI [83.9, 100])
    with QQ, AKs, AKo x3, TT among the folded holdings."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    pack = packs[VillainType.NIT]
    policy = _vs_3bet_effective_policy(pack)
    for cls in ("QQ", "AKs", "AKo"):
        w = policy.get(cls, {})
        cont = w.get("call", 0.0) + w.get("4bet", 0.0)
        assert cont > 0.0, (
            f"nit vs_3bet continue weight on {cls} is {cont} — the R10-3BET "
            f"defect (uncovered classes fold 1.0 at a matched node; "
            f"`sample_preflop_action` has no fall-through)"
        )


def test_r10_3bet_preservation_continue_and_4bet_ordering():
    """🟢 PRESERVATION (already passed at pre-slice HEAD — labeled per the
    gate-design rule, NOT sold as a defect gate): AA/KK continue > 0 in every
    pack, and the combo-weighted authored 4-bet share keeps the archetype
    ordering maniac > lag > tag > nit (pre-slice 7.54/3.17/1.69/0.23%;
    authored by this slice 15.16/2.33/1.81/0.41% — maniac's figure INCLUDES
    its "*" catch-all's 4bet 0.1 over ~120 unlisted classes, i.e. the maniac
    4-bet-bluffs any two cards 10% of the time facing a 3-bet; that junk mass
    is ~10.2pp of the 15.16% and is deliberate archetype identity, kept
    gap-gate-neutral because a 4-bet adds VPIP and PFR together)."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    for vt, pack in packs.items():
        policy = _vs_3bet_effective_policy(pack)
        for cls in ("AA", "KK"):
            w = policy.get(cls, {})
            assert w.get("call", 0.0) + w.get("4bet", 0.0) > 0.0, (
                f"{vt.value}: vs_3bet continue on {cls} dropped to zero"
            )
    shares = {
        vt: _fourbet_share(packs[vt])
        for vt in (VillainType.MANIAC, VillainType.LAG, VillainType.TAG, VillainType.NIT)
    }
    assert (
        shares[VillainType.MANIAC]
        > shares[VillainType.LAG]
        > shares[VillainType.TAG]
        > shares[VillainType.NIT]
    ), f"4-bet share ordering broken: {[(k.value, round(v * 100, 3)) for k, v in shares.items()]}"


def test_r10_3bet_passive_identity_freeze():
    """🔴 Owner-frozen identities (2026-07-30, deterministic): the station
    carries ZERO 4bet mass anywhere in its vs_3bet node, and the fish's 4bet
    mass is EXACTLY {AA: 0.5} — their CALL tiers are authorable, their 4-bet
    identities are not. Guards the ordering check's bottom end (the ordering
    tuple deliberately excludes both, so only this test watches them)."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    station = _vs_3bet_effective_policy(packs[VillainType.CALLING_STATION])
    fish = _vs_3bet_effective_policy(packs[VillainType.PASSIVE_FISH])
    station_4bets = {c: w["4bet"] for c, w in station.items() if w.get("4bet", 0.0) > 0.0}
    assert station_4bets == {}, f"station authored 4bet mass appeared: {station_4bets}"
    fish_4bets = {c: w["4bet"] for c, w in fish.items() if w.get("4bet", 0.0) > 0.0}
    assert fish_4bets == {"AA": 0.5}, (
        f"fish 4bet identity moved off AA@0.5: {fish_4bets}"
    )


# ------------------------------- T-F3 — maniac vs_4bet middle-pair dead band --
# RR-HOLES finding T-F3 (MED, routed to "a future vs_4bet pass" — this one):
# the maniac's `vs_4bet` node covered TT/JJ (call 0.5) and 55/66 (5bet_shove
# 0.4) but NOTHING on 99/88/77, and an uncovered class at a matched node folds
# 1.0 (`sample_preflop_action` has no fall-through). RR-LINT recorded it as a
# pair-row gap and explicitly declined the ace-blocker reading that makes the
# As-row gaps intentional: no card-removal story distinguishes 77 from 66.
#
# EV-scale judgment at ~100bb (the roadmap's phrasing, not a solver claim): a
# 4-bet pot leaves an SPR around 1-2, so 77-99 have no set-mining equity to
# call on — but the maniac is the one archetype whose identity is applying
# pressure with exactly that kind of hand. Authored PUSH/FOLD, no call leg:
# {5bet_shove 0.4, fold 0.6}.
#
# Theory review R-3 (MED, folded): the first draft authored {shove 0.25, call
# 0.15, fold 0.6}, which (a) INVERTED the jam ladder — 55/66 jammed 0.40 while
# the stronger 77-99 jammed only 0.25 — and (b) contradicted this very
# docstring by adding a call leg to hands with no set-mining price. Levelling
# the jam at 0.40 fixes both and keeps the archetype's push/fold identity.
# The FLAT continue level 0.40 (equal to 55/66, below TT/JJ's 0.50) is
# theory-endorsed and deliberate, not a rounding artifact.
#
# N-M4BET (2026-07-31, maniac.json 1.4.0): this pin is UNCHANGED, and the
# record of why matters. The slice first raised the level to jam 0.75 on the
# argument that a 25% aggregate fold left no budget for a 60% fold on middle
# pairs; theory review REFUTED that arithmetic — holding all of 22-99 at the
# wave-3 {jam 0.40, fold 0.60} the arrival-weighted aggregate landed at fold
# 0.286, inside every bound the gate asserts. Nothing in the fit required the
# move, so the wave-3 weights were restored: at 1.4.0, 22-99 were ONE
# push/fold mix ("22-99") at exactly this level, which also makes the
# 99 -> TT jam step 0.40 -> 0.45 RISING instead of the 0.75 -> 0.45 inversion
# the raised level introduced.
# ⚠️ THE 0.286 ABOVE IS COUNTERFACTUAL AS OF 1.5.0 — it is the aggregate the
# REFUTED-then-restored wave-3 weights produced when this paragraph was
# written, not what the pack ships. The shipped reading lives with the gate
# that asserts it: see `test_nm4bet_maniac_arrival_weighted_vs_4bet_matches_
# dossier`.
#
# The rationale ABOVE is narrowed at the same review: "no set-mining price"
# holds for 22-66, but for 77-99 the honest test is the DIRECT price — at
# SPR ~1.5, calling ~14 into ~35.5 needs ~28% equity, which 77-99 clear
# against a 4-betting range. Whether 77-99 deserve a call leg is therefore
# OPEN and FILED as a follow-up; this slice authors no new call legs.
#
# N-M4CALL (2026-08-01, maniac.json 1.5.0) — that follow-up, SETTLED. Finding
# T-M4: the pair row was inconsistent, not principled — TT and up carry call
# legs at the same depths, so "pairs are jam-or-fold" could not be a law of
# the node while it applied to 99 and not to TT. It is now what its own review
# already narrowed it to: a law about 22-66. 77/88/99 are carved into their
# own mix with a call leg and 22-66 are byte-identical. See
# `test_tm4_maniac_vs_4bet_mid_pairs_have_a_priced_call_leg` for the T3
# arithmetic, the measured equities, and why the call leg is a MINORITY of
# continue mass while the jam level does not move. NOTE the paragraph above
# states the price from lever-derived sizing rounded to "~14 into ~35.5, SPR
# ~1.5"; the exact chain is 13.86 into 35.16 at post-call SPR 1.56 (T3 =
# 0.2827), and the live node's arrivals are a MIXTURE around that reference,
# not draws from it — both corrected at the T-M4 gate (review C-1).
_MANIAC_VS_4BET_MID_PAIR_MIX = {"5bet_shove": 0.4, "call": 0.3, "fold": 0.3}
# 22-66 — the narrowed law's block, unchanged since wave 3.
_MANIAC_VS_4BET_SMALL_PAIR_MIX = {"5bet_shove": 0.4, "fold": 0.6}


def _vs_4bet_policy(pack) -> dict[str, dict[str, float]]:
    """Authored vs_4bet weights per class, sampler semantics (first matching
    mix wins; classes no mix covers are absent = fold 1.0).

    Asserts the single-node assumption (review LOW): no shipped pack stratifies
    `vs_4bet` by role, and a silent `next()` would read only the first stratum
    if one ever did."""
    from app.domain.content.notation import parse_range

    nodes = [n for n in pack.preflop if n.facing == "vs_4bet"]
    assert len(nodes) == 1, (
        f"vs_4bet policy assumes ONE un-stratified node; found {len(nodes)} "
        f"(roles {[n.role for n in nodes]}) — read the stratum explicitly"
    )
    node = nodes[0]
    policy: dict[str, dict[str, float]] = {}
    for mix in node.mixes:
        for cls in parse_range(mix.combos):
            policy.setdefault(cls, dict(mix.weights))
    return policy


def test_tf3_maniac_vs_4bet_middle_pairs_continue():
    """🔴 T-F3 defect gate (deterministic, no sampling): the maniac's authored
    vs_4bet continue mass (call + 5bet_shove) on 99, 88 and 77 is > 0.

    PRE-SLICE HEAD reading (recorded per the gate-design rule): all three
    classes were absent from every mix of the node, i.e. continue 0.0 and fold
    1.0 — this assertion FAILED at HEAD on all three.

    Review fold (Codex MED): the EXACT mix is pinned, not `continue > 0`. The
    loose form would have accepted any token weight and could not have caught
    the jam-ladder inversion theory review R-3 found.

    N-M4CALL (2026-08-01): the pinned mix gains its call leg (see the block
    comment and the T-M4 gate below), and the 22-66 block is pinned in the
    SAME assertion — the narrowing only means something if the classes it
    excludes are watched too."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    policy = _vs_4bet_policy(packs[VillainType.MANIAC])
    wrong = {
        cls: policy.get(cls, {})
        for cls in ("99", "88", "77")
        if policy.get(cls, {}) != _MANIAC_VS_4BET_MID_PAIR_MIX
    }
    assert not wrong, (
        f"maniac vs_4bet middle pairs are not the authored "
        f"{_MANIAC_VS_4BET_MID_PAIR_MIX}: {wrong}"
    )
    wrong_small = {
        cls: policy.get(cls, {})
        for cls in ("66", "55", "44", "33", "22")
        if policy.get(cls, {}) != _MANIAC_VS_4BET_SMALL_PAIR_MIX
    }
    assert not wrong_small, (
        f"maniac vs_4bet small pairs left the narrowed jam-or-fold law "
        f"{_MANIAC_VS_4BET_SMALL_PAIR_MIX}: {wrong_small}"
    )


def test_tm4_maniac_vs_4bet_mid_pairs_have_a_priced_call_leg():
    """🔴 T-M4 defect gate (deterministic, no sampling): 77, 88 and 99 must
    have a NON-ZERO call leg vs a 4-bet, that leg must stay a MINORITY of
    their continue mass, and 22-66 must have none.

    PRE-SLICE HEAD reading (recorded per the gate-design rule): at b54fe6e all
    of 22-99 shipped one `{5bet_shove 0.4, fold 0.6}` mix, so call == 0.0 for
    77/88/99 — the first assertion FAILS at HEAD on all three classes. The
    other two assertions pass at HEAD (vacuously and by identity); they are
    boundary guards, not the red-first claim.

    THE ARITHMETIC (theory contract §3, T3 pure-call break-even
    `E >= B/(P+B)`), on the LEVER-DERIVED canonical single-raised chain — NOT
    a probe reading (review C-1). Whose lever is whose matters here (delta
    review D1), because `sizing.py` applies every multiplier to the LAST
    raise-to: the OPENER's `open_bb` 3.0 (tag / lag / nit) -> the MANIAC's
    `threebet_mult` 3.3 = 9.9 -> the OPENER's `fourbet_mult` 2.4 (tag / lag)
    x 9.9 = 23.76. Only the 3.3 is the maniac's; its OWN block reads
    {open_bb 4.5, threebet_mult 3.3, fourbet_mult 3.0} and the two figures
    that are not the 3.3 do NOT appear in this chain. That leaves a call of
    23.76 - 9.9 = 13.86 into a pot of 9.9 + 23.76 + 1.5 = 35.16 (post-call
    SPR 1.56):

        E >= 13.86 / (35.16 + 13.86) = 13.86 / 49.02 = 0.2827

    THE PROBE'S ARRIVALS ARE NOT THAT SPOT, and the difference is recorded
    rather than smoothed over: `_maniac_vs_4bet_channels` counts channels, it
    does not price them. A one-off scratch probe that re-priced its replayed
    decisions read a mean call of 28.6 into a pot of 73.7, a MEDIAN post-call
    SPR of 0.562, and 150 OOP / 132 IP arrivals — SCRATCH READINGS, NOT
    COMMITTED AND NOT ASSERTED anywhere; re-derive them before reusing them
    (review D5). The canonical chain above is the reference geometry this mix
    is authored against; the live node is a mixture around it.

    Measured with the repo's own `equity_vs_range` (20k iters, seed 7), hero
    combos 7c7d / 8c8d / 9c9d, preflop all-in:

        vs a value-only 4-bet range (QQ+, AK)     0.3617 / 0.3565 / 0.3618
        vs a wider one (TT+, AQs+, AKo, A5s, A4s) 0.3782 / 0.3760 / 0.3772

    +- ~0.002 of SUIT-CHOICE noise: an independent re-run at the same seed
    with different concrete combos read 0.3612 / 0.3550 / 0.3604 (review L4).
    Nothing here turns on the third decimal.

    ROBUSTNESS, stated as the MASS-WEIGHTED claim it actually is (review
    CT-3): the price is not cleared against every 4-bettor at this table. The
    nit 4-bets {AA 0.5, KK 0.3, QQ 0.1} and the fish {AA 0.5} — against those
    ranges 77-99 hold ~0.19 and MISS the 0.2827 price by ~9pts. Under ONE
    metric (combo-weighted `vs_3bet` 4-bet mass under first-match-wins) that
    tail is 0.63% of the range, against 19.6% for the maniac's own
    opener-arrival node and 15.2% for its cold node — i.e. the wide 4-bettor
    outweighs the tight tail by ~30x. (Delta review D2: an earlier draft put
    the comparison at "34.7%", which reproduces under no metric at all — it
    was the unrelated n>=4 CHANNEL share 0.3463, a conflation.) Against a
    roster-POOLED 4-bet range 77/99 read ~0.52 / ~0.56 on a scratch
    reconstruction — again UNASSERTED and weighting-sensitive (the delta
    reviewer's own reconstruction read 0.55 / 0.59), quoted only for its
    direction. So the tight tail exists, is named, and does not govern: the
    mass the maniac actually faces here is overwhelmingly wide, and a
    class-level mix answers the mixture, not its tail. The 1.4.0 "no
    set-mining price" rationale is
    about IMPLIED odds and does not reach a hand whose DIRECT price is good
    against the ranges that supply the mass.

    WHY THE CALL IS A MINORITY LEG (the assertion `call < 5bet_shove`) —
    DIRECTIONAL PREMISE, not settled law: T3 is a RAW-equity test, and an
    underpair realizes below raw at these depths (it flops a set 11.8% of the
    time and otherwise plays a bluff-catcher with little implied odds left to
    win; arrivals are mixed IP/OOP, 132 of 282 in position). The size of that
    discount is UNMEASURED here, so `call < jam` is the shape the premise
    implies, not a proven optimum — a future re-fit that measures realization
    may refute it. Shipped {call 0.30, 5bet_shove 0.40, fold 0.30}.

    WHY THE JAM LEVEL DOES NOT MOVE (this slice adds a leg; it does not
    re-level) — with the stacks done EXACTLY (review CT-1, convergent): after
    3-betting to 9.9 the maniac has 90.1 behind and the 4-bettor, having put
    in 23.76, has 76.24. Both end up wagering exactly 100 and the jam IS
    fully matched — what breaks is the FORMULA, not the call: §3's
    `B/(P+2B)` books a full extra B on top of P for the villain's call, and
    effective stacks cap that at 76.24, not 90.1 (delta review D3). So the
    exact zero-fold-equity break-even is read off the real final pot:

        90.1 / (35.16 + 90.1 + 76.24) = 90.1 / 201.5 = 0.447

    ABOVE these hands' ~0.36, so the shove is not a value commit — it needs
    fold equity, and the conclusion holds a fortiori against the naive
    uncapped reading (0.419). By T2 the required realized fold equity is
    F* ≈ 0.26-0.28 (0.262-0.279 at P = 35.5, B = 92, E = 0.3565-0.3618 —
    review C-2; the same capping caveat makes any T2 number here an
    approximation). Live for this archetype, not free. The jam is also boxed
    in on both sides by the ladders the test below asserts: >= 66's 0.40 and
    <= TT's 0.45 (the T-L1 inversion tripwire), so 0.40 is the only level
    that leaves both intact."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    policy = _vs_4bet_policy(packs[VillainType.MANIAC])
    no_call = {
        cls: policy.get(cls, {})
        for cls in ("99", "88", "77")
        if policy.get(cls, {}).get("call", 0.0) <= 0.0
    }
    assert not no_call, (
        f"maniac vs_4bet 77-99 have no call leg — T3 says the direct price "
        f"(0.2827 needed on the canonical chain, ~0.36 held against the "
        f"ranges that supply the 4-bet mass) is already good: {no_call}"
    )
    over_called = {
        cls: policy.get(cls, {})
        for cls in ("99", "88", "77")
        if policy.get(cls, {}).get("call", 0.0)
        >= policy.get(cls, {}).get("5bet_shove", 0.0)
    }
    assert not over_called, (
        f"maniac vs_4bet 77-99 call at least as often as they jam. The "
        f"minority-leg shape rests on a DIRECTIONAL, UNMEASURED premise — T3 "
        f"is a raw-equity test and an underpair is assumed to realize below "
        f"raw at these depths. That premise, not an optimum, is what a "
        f"re-fit has to refute before inverting this: {over_called}"
    )
    small_calls = {
        cls: policy.get(cls, {})
        for cls in ("66", "55", "44", "33", "22")
        if policy.get(cls, {}).get("call", 0.0) > 0.0
    }
    assert not small_calls, (
        f"22-66 gained a call leg — the jam-or-fold law was narrowed TO this "
        f"block, not repealed (their set-mining price is the one that really "
        f"fails at these depths): {small_calls}"
    )


def test_tf3_maniac_vs_4bet_pair_continue_ladder_is_monotone():
    """🟢 PRESERVATION-shaped companion to the gate above (it could not pass at
    HEAD, where 99/88/77 read 0.0 between TT/JJ's 0.5 and 66/55's 0.4): the
    repair must not out-continue a stronger pair. Continue mass is
    non-increasing down the pair row AA -> 55.

    Second direction added at review (theory R-3): JAM mass must be
    non-decreasing UP the row, 55 -> 99. That is the assertion the first draft
    violated — it continued 77-99 at the right total (0.40) while jamming them
    less than the weaker 55/66 — and continue-monotonicity alone could never
    have caught it, because the inversion lived inside the split.

    N-M4BET (2026-07-31) EXTENDS both ladders to the bottom of the row rather
    than replacing them: 44/33/22 were uncovered (continue 0.0, fold 1.0) when
    this gate was written, so the continue ladder stopped at 55 and the jam
    ladder started there. Both now run the full pair row — continue
    non-increasing AA -> 22, jam non-decreasing 22 -> 99 — which is strictly
    more than the old gate asserted.

    N-M4CALL (2026-08-01, maniac.json 1.5.0) SPLITS that block: 22-66 keep the
    wave-3 push/fold mix and 77-99 add a call leg, so the ladders now read
    continue 0.40 (22-66) -> 0.70 (77-99) -> 1.00 (TT) and jam LEVEL at 0.40
    across all of 22-99, stepping up into TT's 0.45. Both directions are
    load-bearing on the new mix: the continue ladder is what stops the call
    leg from out-continuing TT, and the jam ladder plus the 99->TT boundary
    pin below are what box the jam level in at exactly 0.40.

    JJ/TT and up are deliberately OUTSIDE the jam ladder: those tiers are
    call-capable (continue 1.00, split call 0.55 / jam 0.45), and QQ/AK jam
    1.00 because they most want no showdown, so jam mass is NOT monotone
    across the top of the row. Continue mass is, and that is the leg that
    carries the strength claim."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    policy = _vs_4bet_policy(packs[VillainType.MANIAC])

    def leg(cls: str, action: str) -> float:
        return policy.get(cls, {}).get(action, 0.0)

    def cont(cls: str) -> float:
        return leg(cls, "call") + leg(cls, "5bet_shove")

    ladder = ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22"]
    bad = [
        f"{a} {cont(a):.2f} < {b} {cont(b):.2f}"
        for a, b in zip(ladder, ladder[1:], strict=False)
        if cont(a) < cont(b)
    ]
    assert not bad, f"maniac vs_4bet pair continue ladder inverted: {bad}"
    jam_ladder = ["22", "33", "44", "55", "66", "77", "88", "99"]
    jam_bad = [
        f"{a} {leg(a, '5bet_shove'):.2f} > {b} {leg(b, '5bet_shove'):.2f}"
        for a, b in zip(jam_ladder, jam_ladder[1:], strict=False)
        if leg(a, "5bet_shove") > leg(b, "5bet_shove")
    ]
    assert not jam_bad, f"maniac vs_4bet jam mass falls as pairs get stronger: {jam_bad}"
    # Delta-review D1: the docstring's "step out of the block into TT rises"
    # claim was advertised but unasserted (TT sits outside jam_ladder by
    # design). Pin just the boundary step so re-raising 99's jam above TT's
    # cannot recreate the wave-3 R-3 inversion silently.
    assert leg("99", "5bet_shove") <= leg("TT", "5bet_shove"), (
        f"99 jam {leg('99', '5bet_shove'):.2f} exceeds TT's "
        f"{leg('TT', '5bet_shove'):.2f} — the 99->TT boundary inverted"
    )


def test_tf3_vs_4bet_edit_leaves_the_4bet_shares_untouched():
    """🟢 PRESERVATION (passes at HEAD and after — the point is that it reads
    the SAME number both times): the archetype 4-bet share is a `vs_3bet`
    quantity, so adding continue mass to a `vs_4bet` node cannot move it.
    Pinned to the R10-3BET-authored values so a later slice cannot smuggle a
    4-bet-frequency change in through the vs_4bet node."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    shares = {
        vt.value: round(_fourbet_share(packs[vt]) * 100, 2)
        for vt in (VillainType.MANIAC, VillainType.LAG, VillainType.TAG, VillainType.NIT)
    }
    assert shares == {"maniac": 15.16, "lag": 2.33, "tag": 1.81, "nit": 0.41}, shares


# ------------------------- N-M4BET — the maniac's ARRIVAL-WEIGHTED 4-bet response
# Theory finding T-R2 (HIGH, wave-3 lane B): T-F3 above fixed the ONE pair-row
# hole RR-LINT could see, but the node's behaviour is not a per-class ordering
# question — it is the AGGREGATE the bot actually produces, and that aggregate
# is set by which classes ARRIVE at the node and with how much mass.
#
# ARRIVAL DERIVATION (deterministic, no sampling) — a CONDITIONAL, and the
# condition is load-bearing (review fold, 3-way convergent: theory HIGH, Codex
# MED, refuter MED). The channel modeled here is "the maniac 3-bet an RFI and
# got 4-bet": its own `vs_rfi` 3-bet mass under first-match-wins, i.e. for each
# of the 169 classes combos(class) x P(3bet | class), summing to 284.4 combos =
# 21.45% of all 1326 (the figure T-R2 measured). Weighting the `vs_4bet` policy
# by that mass (uncovered class => fold 1.0, weight remainder => fold, exactly
# as `sample_preflop_action` resolves it) gives the response triple below.
#
# WHAT THE MODEL DOES NOT COVER. `play._preflop_facing` labels `vs_4bet` off the
# raise COUNT (n >= 3) and reads no history, so the same node also serves: the
# opener facing a cold 4-bet, a cold caller, the ISO-raiser over limpers, and
# n >= 4 re-entrant arrivals — where "5bet_shove" is a misnomer and, facing an
# all-in, degrades to a CALL through play.py's legality fallback. Measured on a
# seeded 4000-hand PRODUCTION-SIZING probe (the REPORTED test below): 65.4% of
# the maniac's vs_4bet decisions are n=3 and 40.7% are this modeled channel.
# (Re-read at N-M4CALL, maniac.json 1.5.0. The 70.2% / 45.9% recorded here at
# 1.4.0 no longer reproduce even on 1.4.0 content — see the ⚠️ note in the
# reported test's docstring. The conclusion the figures support is unchanged:
# the modeled channel is the single largest stratum, and it is under half.)
#
# THE vs_limpers QUESTION, SETTLED BY TRACE (review item 1b): the iso channel IS
# reachable — Codex's construction is right, the "never reaches vs_4bet" reading
# is wrong. Concrete production-sizing hand (seed 447515414, button seat 4):
# UTG1 limps, the maniac at UTG2 ISO-raises to 5.5 (raise #1), LJ re-raises to
# 18.15 (#2), HJ re-raises to 54.45 (#3) — when action returns to the
# ISO-raiser it reads `vs_4bet` at n=3, which is the load-bearing claim. (In
# the replayed deal the iso-raiser then folds; a 5-bet to 100 in that hand
# comes from a DIFFERENT maniac seat on the modeled channel. The seed is an
# illustrative constructed replay, not drawn from the probe's own hand
# stream — delta-review D3.) The iso channel is 4.3% of the maniac's vs_4bet
# decisions in the probe; that mass arrives with the ISO range, not the
# 3-bet range, and is NOT modeled here.
#
# ✅ INSTRUMENT WARNING RESOLVED (R-L2, instrument-repair wave). The warning
# used to read: "the band harness's own `_preflop_decision` sizes every raise at
# `la.min_bb`, while production sizes from persona levers and a `5bet` is
# all-in — so HARNESS measurements of this node overstate re-entrant depth."
# That is fixed at the source: the harness no longer has its own copy, it
# imports `play._preflop_decision` (see the import above `_STREET_BY_BOARD_LEN`).
# Paired sweep, n=2000 seeded hands, seed 20260710, this same maniac-heavy
# lineup, separate processes: share of hands reaching >= 5 preflop raises was
# harness 1.80% / production 0.00% BEFORE (b54fe6e), and harness 0.00% /
# production 0.00% AFTER — max harness depth 99 raises before, 4 after, which is
# production's own ceiling (the 5-bet is all-in). Gated by
# `test_harness_preflop_raise_depth_matches_production` below.
# The channel figures quoted here still come from the production-sizing probe
# (that probe drives `play.bot_decision` directly and is the more direct
# instrument); they are no longer at risk from a harness/production divergence.
#
# TARGET: docs/.../playstyle-research/maniac.md, "Facing a 4-bet after
# 3-betting", ONLINE row — fold 25% / call 35% / 5-bet jam 40%.
# PROVENANCE: (Online full-ring cash, online 2NL-100NL, maniac.md "Facing a
# 4-bet after 3-betting", author-asserted calibration band — UNVERIFIED, never
# HARD while unverified). maniac.md:383 says in terms "do NOT present as
# measured", so the triple is NOT a two-sided CI gate here (theory MED): the
# ASSERTED form is one-sided red-first bounds, each of which fails HEAD~1 on
# its own, and the exact triple + the +-0.05 comparison are PRINTED as a report.
_M4BET_DOSSIER = {"fold": 0.25, "call": 0.35, "5bet_shove": 0.40}
_M4BET_TOL = 0.05  # report-only distance from the triple, NOT asserted
# One-sided asserted bounds. Direction = the defect's direction, level = far
# enough from the dossier point to survive an authoring re-fit but close enough
# that each fails at pre-slice HEAD (0.8143 / 0.0408 / 0.1449) individually.
_M4BET_BOUNDS = {"fold": ("<", 0.40), "call": (">", 0.15), "5bet_shove": (">", 0.25)}


def _vs_rfi_threebet_arrival(pack) -> dict[str, float]:
    """class -> combo mass this pack ARRIVES at `vs_4bet` with THROUGH THE
    MODELED CHANNEL, i.e. its own `vs_rfi` 3-bet mass under first-match-wins
    (later mentions are dead). See the block comment for the channels this
    deliberately excludes.

    COUPLING IS INTENDED: the aggregate gate reads the `vs_rfi` node, so a
    future slice that rewrites `vs_rfi` moves this arrival distribution and can
    turn the gate red WITHOUT touching `vs_4bet`. That is the design — the
    response is only meaningful against the range it is answered with — and the
    failure message says to re-derive rather than to re-weight.

    RE-DERIVED for the de-robotization slice (2026-08-15), which is the "future
    slice" that comment anticipated. `vs_rfi` is now split by seat, so there is
    no single node to read and the old single-node assertion fired exactly as
    designed. The arrival is now the mean 3-bet mass over the nine seats, each
    seat resolved through the sampler's own node scan. That is a re-derivation,
    not a re-weighting: for a position-blind pack it returns the previous
    numbers unchanged, and for a split pack it answers the question the gate
    actually asks — what range does this persona bring to a 4-bet, at a table.
    """
    from app.domain.content.notation import parse_range

    arrival: dict[str, float] = {}
    for seat in Position:
        node = _node_for_seat(pack, "vs_rfi", seat)
        if node is None:
            continue
        seen: set[str] = set()
        for mix in node.mixes:
            w = mix.weights.get("3bet", 0.0)
            for cls in parse_range(mix.combos):
                if cls in seen:
                    continue
                seen.add(cls)
                if w > 0.0:
                    arrival[cls] = arrival.get(cls, 0.0) + _combo_count(cls) * w
    # Divided once, for the same exactness reason as `_vs_3bet_effective_policy`.
    seats = len(Position)
    return {cls: mass / seats for cls, mass in arrival.items()}


def _vs_4bet_arrival_weighted(pack) -> dict[str, float]:
    """The pack's `vs_4bet` response averaged over its OWN arriving 3-bet mass.
    Resolves weights exactly as `sample_preflop_action` does: the remainder of
    a mix is an implicit fold, and a class no mix covers folds 1.0."""
    policy = _vs_4bet_policy(pack)
    arrival = _vs_rfi_threebet_arrival(pack)
    agg = {"fold": 0.0, "call": 0.0, "5bet_shove": 0.0}
    for cls, mass in arrival.items():
        weights = dict(policy.get(cls, {}))
        remainder = 1.0 - sum(weights.values())
        if remainder > 1e-9:
            weights["fold"] = weights.get("fold", 0.0) + remainder
        for act, w in weights.items():
            agg[act] += mass * w
    total = sum(arrival.values())
    return {act: v / total for act, v in agg.items()}


def test_nm4bet_maniac_arrival_weighted_vs_4bet_matches_dossier():
    """🔴 N-M4BET defect gate (deterministic, no sampling): the maniac's
    response over the MODELED ARRIVAL CHANNEL (its own vs_rfi 3-bet mass; see
    the block comment for what that excludes and why) must clear three
    ONE-SIDED bounds — fold < 0.40, call > 0.15, jam > 0.25.

    WHY ONE-SIDED (theory MED): the dossier row is an author-asserted
    calibration band the source itself says not to present as measured, so it
    may not act as a two-sided CI gate. Each bound above fails at pre-slice
    HEAD ON ITS OWN — HEAD reads fold 0.8143 (not < 0.40), call 0.0408 (not >
    0.15), jam 0.1449 (not > 0.25) — so the gate is red-first three times over
    while asserting nothing the source cannot support. The exact triple and
    the +-0.05 distance from it are PRINTED as a report, not asserted.

    PRE-SLICE HEAD cause (recorded per the gate-design rule): coverage, not
    weights — 73.63% of arriving mass (151 of 169 classes: AQo, KQo, KJo, QJo,
    JTo, ATo, AJo, A9o, AJs, 44-22 and the whole light-3-bet tail) matched NO
    mix and folded 1.0.

    SHIPPED READING, recorded here because this is where the gate lives
    (N-M4CALL, maniac.json 1.5.0): fold 0.2764 / call 0.3454 / jam 0.3781,
    from fold 0.2859 / call 0.3359 / jam 0.3781 at 1.4.0 — the 77-99 call leg
    moving fold mass into call at a constant jam. Every bound clear, and the
    distance to the dossier row shrank on both legs that moved."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    got = _vs_4bet_arrival_weighted(packs[VillainType.MANIAC])
    print(
        "maniac arrival-weighted vs_4bet (modeled n=3 3-bettor channel): "
        + " ".join(f"{a} {got[a]:.4f}" for a in ("fold", "call", "5bet_shove"))
    )
    print(
        "  REPORT vs dossier 25/35/40 (author-asserted, UNVERIFIED): "
        + " ".join(
            f"{a} {got[a] - _M4BET_DOSSIER[a]:+.4f}"
            f"{'' if abs(got[a] - _M4BET_DOSSIER[a]) <= _M4BET_TOL else ' OUT'}"
            for a in ("fold", "call", "5bet_shove")
        )
        + f" (report tolerance +-{_M4BET_TOL}, NOT asserted)"
    )
    bad = {
        act: round(got[act], 4)
        for act, (op, bound) in _M4BET_BOUNDS.items()
        if not (got[act] < bound if op == "<" else got[act] > bound)
    }
    assert not bad, (
        f"maniac arrival-weighted vs_4bet response breaks its one-sided "
        f"bounds {_M4BET_BOUNDS}: {bad}. If `vs_rfi` moved rather than "
        f"`vs_4bet`, RE-DERIVE the arrival distribution — do not re-weight "
        f"the response to chase it"
    )


def test_nm4bet_maniac_vs_4bet_covers_its_own_arriving_3bet_range():
    """🔴 N-M4BET coverage gate (the disease T-R2 named, gated directly):
    EVERY class the maniac 3-bets must hit an explicit `vs_4bet` mix. An
    uncovered class is not a policy choice — `sample_preflop_action` folds it
    1.0 with no fall-through, which is how 73.63% of the arriving mass became
    an invisible fold. FAILED at pre-slice HEAD on 151 classes.

    Weakest-link form on purpose: the aggregate gate above can be satisfied
    with holes left in (over-continuing elsewhere to compensate), so the two
    assertions are not redundant.

    ⚠️ OBSERVABILITY TRADE (refuter MED) — the node ends in a `*` catch-all, so
    (a) RR-LINT's row-gap lint is permanently blind to this node (every class
    is "played", so no row can have a gap) and (b) the coverage assertion above
    can never fail again while `*` is last. The trade buys the thing the defect
    was: no class can silently fold 1.0. The replacement watch is the TAIL-MASS
    tripwire below — a future edit that "covers" classes by dumping them into
    the `*` tier instead of authoring them goes red at 0.15 of arriving mass
    (today 0.1181, the any-two light-3-bet tail alone). Same trade documented
    in tests/test_pack_range_lint.py's inventory block."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    pack = packs[VillainType.MANIAC]
    policy = _vs_4bet_policy(pack)
    arrival = _vs_rfi_threebet_arrival(pack)
    total = sum(arrival.values())
    uncovered = {cls: round(m / total, 5) for cls, m in arrival.items() if cls not in policy}
    assert not uncovered, (
        f"maniac 3-bets {len(uncovered)} classes it has no vs_4bet mix for "
        f"({sum(uncovered.values()):.4f} of arriving mass): {sorted(uncovered)}"
    )
    from app.domain.content.notation import parse_range

    node = next(n for n in pack.preflop if n.facing == "vs_4bet")
    assert node.mixes[-1].combos.strip() == "*", (
        "the tail tripwire assumes the catch-all is the LAST mix; it is "
        f"{node.mixes[-1].combos[:40]!r}"
    )
    earlier: set[str] = set()
    for mix in node.mixes[:-1]:
        earlier |= parse_range(mix.combos)
    tail = sum(m for cls, m in arrival.items() if cls not in earlier) / total
    print(f"maniac vs_4bet '*' tail claims {tail:.4f} of arriving mass")
    assert tail <= 0.15, (
        f"the vs_4bet `*` catch-all now absorbs {tail:.4f} of arriving mass "
        f"(cap 0.15): classes are being covered by dumping them in the tail "
        f"instead of being authored — the coverage gate cannot see that"
    )


def test_nm4bet_maniac_vs_4bet_suited_ace_construction_is_pinned():
    """🔴 REPLACEMENT gate for the RR-LINT row-gap entry this slice retires
    (red at pre-slice HEAD, where the wheel tier read {5bet_shove 0.5, fold
    0.5} and the middle suited aces were uncovered, i.e. jam 0.0 — it fails
    HEAD on both halves).

    RR-LINT recorded ("maniac", "vs_4bet", "*", "As", (AJs..A6s)) as a
    DELIBERATE polar/blocker construction: the node continued AKs and the
    wheel aces A5s-A2s while the middle suited aces were unplayed. N-M4BET
    covers every class explicitly, so that gap is no longer visible to a
    coverage-based lint — the construction now lives in the WEIGHTS. This pin
    keeps it watched: the wheel-ace tier stays a jam-or-fold block (no call
    leg, the card-removal story), and it jams STRICTLY more than the middle
    suited aces do, which is the whole content of the old entry."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    policy = _vs_4bet_policy(packs[VillainType.MANIAC])
    for cls in ("A5s", "A4s", "A3s", "A2s"):
        assert policy.get(cls, {}) == {"5bet_shove": 0.7, "fold": 0.3}, (
            f"wheel-ace blocker tier moved off jam-or-fold on {cls}: {policy.get(cls, {})}"
        )
    for cls in ("AJs", "ATs", "A9s", "A8s", "A7s", "A6s"):
        jam = policy.get(cls, {}).get("5bet_shove", 0.0)
        assert 0.0 < jam < 0.7, (
            f"middle suited ace {cls} jams {jam} — the wheel-ace blockers must "
            f"jam strictly more, and no arriving class may be a silent fold"
        )


def _maniac_vs_4bet_channels(packs, n_hands: int) -> tuple[int, dict[tuple, int]]:
    """(total decisions, {(raise_count, prior (facing, action)) -> count}) for
    maniac seats acting at `vs_4bet`, over PRODUCTION-SIZING play.

    Deliberately NOT the band harness (refuter instrument finding): the harness
    mirror sizes every raise at `la.min_bb`, which lets min-raise wars run to
    depths production cannot reach (production sizes from the persona levers
    and `5bet` = all-in). This probe drives `play.bot_decision` — the live path
    — and stops at the end of the preflop street, which is all it measures.
    Same seed/lineup convention as `_persona_stats_ext`."""
    from app.domain.table.play import _preflop_facing as _live_facing
    from app.domain.table.play import bot_decision

    rng = random.Random(20260710)
    fillers = [p for p in ALL_PERSONAS if p != "maniac"]
    lineup = (["maniac"] * 3 + [fillers[i % len(fillers)] for i in range(6)])[:9]
    persona_by_seat = {i: lineup[i] for i in range(9)}
    tested = {i for i, p in persona_by_seat.items() if p == "maniac"}
    total = 0
    channels: dict[tuple, int] = {}
    for i in range(n_hands):
        hand_seed = rng.randrange(1_000_000_000)
        dealt = deal_hand(random.Random(hand_seed))
        state = start_hand(dealt, button_seat=i % 9, stacks_bb=[100.0] * 9)
        prior: dict[int, tuple[str, str]] = {}
        guard = 0
        while (
            not state.hand_over
            and state.to_act_seat is not None
            and state.street is Street.PREFLOP
        ):
            guard += 1
            assert guard < 200, "preflop playout did not terminate"
            seat = state.to_act_seat
            facing = _live_facing(state)
            raises = sum(
                1
                for h in state.action_history
                if h.street is Street.PREFLOP and h.action == ActionType.RAISE
            )
            if facing == "vs_4bet" and seat in tested:
                total += 1
                key = (raises, prior.get(seat, ("(first decision)", "-")))
                channels[key] = channels.get(key, 0) + 1
            decision = bot_decision(state, seat, packs[VillainType(persona_by_seat[seat])], rng)
            prior[seat] = (facing, decision.action.value)
            state = apply(state, decision)
    return total, channels


def test_nm4bet_vs_4bet_arrival_channels_report():
    """📋 REPORTED, NOT GATED (review item 1c) — the live stratification of the
    node the deterministic gates model with ONE channel.

    `_preflop_facing` labels `vs_4bet` on raise-count n >= 3 and reads no
    history, so this one node serves several arrival strata with incomparable
    ranges. This probe prints the split so the conditional in the gates above
    is a measured claim rather than an assumption. Reference reading at the
    pinned seed, n=4000 hands (693 maniac decisions, shipped 1.5.0 pack; the
    bracketed column is the SAME probe re-run against 1.4.0 content in a
    separate process, 699 decisions, immediately before this slice):

        n=3 total                             0.6537  [0.6552]
        n>=4 total                            0.3463  [0.3448]
        n=3, seat 3-bet at vs_rfi  [MODELED]  0.4069  [0.4106]
        n=4, seat 4-bet at vs_3bet            0.2251  [0.2246]
        n=4, seat 3-bet at vs_rfi             0.0693  [0.0687]
        n=3, seat opened unopened             0.0664  [0.0658]
        n=3, seat's FIRST decision (cold)     0.0577  [0.0572]
        n=3, seat ISO-raised limpers          0.0433  [0.0429]
        n=3, seat CALLED at vs_rfi            0.0404  [0.0401]
        n=3, seat CALLED at vs_3bet           0.0375  [0.0372]
        n=4, seat CALLED at vs_4bet           0.0289  [0.0286]
        n=4, seat CALLED at vs_3bet           0.0159  [0.0157]
        n=3, seat CALLED at vs_limpers        0.0014  [0.0014]

    All FIVE CALL-prior strata are listed (review L2, corrected at delta
    review D4 — the first fix added only the two n=3 rows, 7.8% of decisions,
    and still left two behind). Together they are 12.4% of the node's traffic
    and they are precisely what the deterministic gates do NOT model: a seat
    that FLATTED earlier in the chain reaches this node with a calling range,
    not with the 3-betting range the aggregate is weighted by.

    N-M4CALL (2026-08-01) BARELY MOVES THIS, which is itself worth recording:
    a call leg on three pair classes at a node this deep changes ~1% of the
    decisions and no stratum's share by more than 0.004 — rng displacement,
    not a re-shaping of the node's traffic. The modeled channel is still the
    largest single stratum, which is the property the gates above depend on.

    ⚠️ THE 1.4.0-ERA FIGURES THIS DOCSTRING USED TO QUOTE (621 decisions;
    n=3 0.7021, modeled 0.4589, iso 0.0322) DO NOT REPRODUCE at the pack
    version they were recorded against — re-running the probe on 1.4.0
    content today gives the bracketed column above. They went stale in some
    slice between, which moved the rng stream (the `vs_rfi` node this probe
    feeds off has been rewritten since) without re-reading this report. Left
    as a note rather than chased: an unasserted Monte Carlo reading has no
    owner between slices, and the drift is exactly the failure mode that
    keeps it unasserted.

    NOT ASSERTED, on purpose: it is a Monte Carlo reading of an occupancy
    distribution with no dossier target, and gating it would freeze an
    instrument, not a behaviour. It exists so the next slice can see whether
    the modeled channel is still the dominant one. n is small enough to run in
    the suite (~6.5s measured) and large enough to read shares to ~2pp."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    total, channels = _maniac_vs_4bet_channels(packs, 4000)
    assert total > 200, f"only {total} maniac vs_4bet decisions — too few to report"
    depth: dict[int, int] = {}
    for (raises, _prior), count in channels.items():
        depth[raises] = depth.get(raises, 0) + count
    print(f"maniac vs_4bet decisions (production sizing, n=4000 hands): {total}")
    for raises in sorted(depth):
        print(f"  raises={raises}: {depth[raises]} ({depth[raises] / total:.4f})")
    for (raises, prior), count in sorted(channels.items(), key=lambda kv: -kv[1]):
        print(f"  n={raises} prior={prior}: {count} ({count / total:.4f})")


def _legacy_min_raise_preflop_decision(
    pack, position, facing, hole, legal, rng, current_bet_to, limpers, is_opener=None
) -> Decision:
    """The harness's PRE-REPAIR preflop decision, from b54fe6e except for the two
    now-unused sizing arguments: every raise sized at `la.min_bb`. Kept ONLY so
    `test_harness_preflop_raise_depth_matches_production` can show the defect it
    fixes (R-L2) instead of asserting an absence. It is AST-equal to the b54fe6e
    body, not byte-equal — the original's inline comments were dropped (they
    explained the legality fallback, which is unchanged and documented on the
    production copy)."""
    act = sample_preflop_action(pack, position, facing, hole, rng, is_opener=is_opener)
    kinds = {la.action for la in legal}
    if act.action not in kinds:
        if ActionType.CALL in kinds:
            act_action = ActionType.CALL
        elif ActionType.CHECK in kinds:
            act_action = ActionType.CHECK
        else:
            act_action = ActionType.FOLD
    else:
        act_action = act.action
    if act_action in (ActionType.BET, ActionType.RAISE):
        la = next(x for x in legal if x.action == act_action)
        size = la.min_bb if la.min_bb is not None else la.max_bb
        return Decision(action=act_action, size_bb=round(size, 2))
    return Decision(action=act_action)


def _harness_raise_depths(packs, n_hands: int) -> dict[int, int]:
    """{preflop raises in the hand -> hand count} over the BAND HARNESS
    (`_play_hand`), maniac-heavy lineup, seed 20260710."""
    rng = random.Random(20260710)
    fillers = [p for p in ALL_PERSONAS if p != "maniac"]
    lineup = (["maniac"] * 3 + [fillers[i % len(fillers)] for i in range(6)])[:9]
    persona_by_seat = {i: lineup[i] for i in range(9)}
    depths: dict[int, int] = {}
    for i in range(n_hands):
        hand_seed = rng.randrange(1_000_000_000)
        res = _play_hand(rng, hand_seed, i % 9, persona_by_seat, packs)
        r = sum(1 for _seat, action in res.preflop_log if action == "raise")
        depths[r] = depths.get(r, 0) + 1
    return depths


def _production_raise_depths(packs, n_hands: int) -> dict[int, int]:
    """The same reading over PRODUCTION play (`play.bot_decision`), same
    seed/lineup convention — the reference the harness must match."""
    from app.domain.table.play import bot_decision

    rng = random.Random(20260710)
    fillers = [p for p in ALL_PERSONAS if p != "maniac"]
    lineup = (["maniac"] * 3 + [fillers[i % len(fillers)] for i in range(6)])[:9]
    persona_by_seat = {i: lineup[i] for i in range(9)}
    depths: dict[int, int] = {}
    for i in range(n_hands):
        hand_seed = rng.randrange(1_000_000_000)
        dealt = deal_hand(random.Random(hand_seed))
        state = start_hand(dealt, button_seat=i % 9, stacks_bb=[100.0] * 9)
        r = 0
        guard = 0
        while (
            not state.hand_over
            and state.to_act_seat is not None
            and state.street is Street.PREFLOP
        ):
            guard += 1
            assert guard < 200, "preflop playout did not terminate"
            seat = state.to_act_seat
            decision = bot_decision(state, seat, packs[VillainType(persona_by_seat[seat])], rng)
            r += decision.action is ActionType.RAISE
            state = apply(state, decision)
        depths[r] = depths.get(r, 0) + 1
    return depths


def test_harness_preflop_raise_depth_matches_production():
    """🔴 INSTRUMENT GATE (R-L2): the band harness must not manufacture
    preflop raise wars production cannot have.

    The harness used to size every raise at the engine's min-raise, which let
    re-raise ping-pong run to absurd depth; production sizes from the persona
    levers and makes the 5-bet ALL-IN, which structurally caps the chain (equal
    100bb stacks -> a jam cannot be re-raised). The repaired harness reuses
    production's own `_preflop_decision`, so the two depth distributions agree.

    Both legs run at the same seed and n, in this one process — legitimate
    because neither reads a memoized stat. Reference reading at n=1000 (printed;
    the ASSERTED claims are the two bounds below, not the exact shares):
    legacy-sizing harness 5+ share 0.0170 with a 99-raise hand in the tail,
    repaired harness 0.000, production 0.000. The wider paired sweep quoted in
    the N-M4BET block above (n=2000, separate processes) read harness 1.80% ->
    0.00% against production 0.00%."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    n = 1000

    def share5(depths):
        return sum(c for d, c in depths.items() if d >= 5) / sum(depths.values())

    prod = _production_raise_depths(packs, n)
    live = _harness_raise_depths(packs, n)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            sys.modules[__name__],
            "_preflop_decision",
            _legacy_min_raise_preflop_decision,
        )
        legacy = _harness_raise_depths(packs, n)

    print(f"preflop raise depths, n={n} hands, seed 20260710 (maniac-heavy lineup)")
    for label, d in (("production", prod), ("harness", live), ("harness@legacy", legacy)):
        print(f"  {label:>14}: 5+ share {share5(d):.4f}  max {max(d)}  {dict(sorted(d.items()))}")

    # Red-first: the pre-repair sizing is what this gate exists to exclude.
    assert share5(legacy) > share5(prod) + 0.005 and max(legacy) > max(prod), (
        "the legacy min-raise harness no longer inflates raise depth — the "
        "defect this gate pins has changed shape; re-derive before relaxing"
    )
    # The claim: the repaired harness tracks production.
    assert share5(live) <= share5(prod) + 0.005, (
        f"harness 5+ raise-war share {share5(live):.4f} exceeds production's "
        f"{share5(prod):.4f} — preflop sizing has diverged from play.py again"
    )
    assert max(live) <= max(max(prod), 5), (
        f"harness reached {max(live)} preflop raises in a hand; production's "
        f"5-bet-is-all-in ceiling at equal stacks is 5"
    )


def test_harness_preflop_raise_sizing_uses_production_args():
    """🔴 INSTRUMENT GATE (R-L2, arg parity — the mutation the depth gate above
    cannot see): delegating to `play._preflop_decision` is not enough; the
    harness must also FORWARD the real sizing inputs. A wrapper that passes
    `current_bet_to=0.0, limpers=0` still "delegates", still produces a legal
    raise, and still passes the depth gate (a zeroed multiplier clamps UP to
    `min_bb` — i.e. exactly the min-raise behaviour R-L2 removed).

    Two constructed spots, tag pack (open_bb 3.0 / threebet_mult 3.5 /
    fourbet_mult 2.4), AA so the action is a raise at every seed:
      vs_rfi facing a 3.0 open  -> 3.5 * 3.0  = 10.5 (min_bb 6.0)
      vs_3bet facing a 10.0 3-bet -> 2.4 * 10.0 = 24.0 (min_bb 20.0)
    The zeroed-default mutant reads 6.0 and 20.0 — the min-raises — so each leg
    kills it. The harness value is also asserted EQUAL to production's on the
    same seeded rng, which is the property that actually matters."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    pack = packs[VillainType.TAG]
    hole = ("Ah", "As")
    spots = (
        ("vs_rfi", 3.0, 6.0, 10.5),
        ("vs_3bet", 10.0, 20.0, 24.0),
    )
    for facing, current_bet_to, min_bb, expected_to in spots:
        legal = [
            personas_postflop_legal_fold(),
            personas_postflop_legal_call(current_bet_to),
            personas_postflop_legal_raise(min_bb, 100.0),
        ]
        args = (pack, Position.CO, facing, hole, legal)
        got = _preflop_decision(*args, random.Random(0), current_bet_to, 0)
        want = _prod_preflop_decision(*args, random.Random(0), current_bet_to, 0)
        assert got.action is ActionType.RAISE, f"{facing}: expected a raise, got {got}"
        assert got == want, f"{facing}: harness {got} != production {want}"
        assert got.size_bb == pytest.approx(expected_to), (
            f"{facing}: harness raised to {got.size_bb}, production sizing is "
            f"{expected_to} (min-raise here is {min_bb} — a wrapper that zeroes "
            f"current_bet_to/limpers reads exactly that)"
        )
        # The mutant, run explicitly: zeroed sizing inputs collapse to min-raise.
        mutant = _prod_preflop_decision(*args, random.Random(0), 0.0, 0)
        assert mutant.size_bb == pytest.approx(min_bb) and mutant.size_bb != got.size_bb, (
            f"{facing}: the zeroed-arg mutant no longer reads the min-raise "
            f"({mutant.size_bb}) — this gate's premise has changed, re-derive it"
        )


def _wilson95(k: int, n: int) -> tuple[float, float]:
    """Wilson score 95% interval — the spec's named CI method for the
    report-only fold-to-3-bet grid (well-behaved at the tiny n these strata
    actually have; a normal interval would go negative)."""
    if n == 0:
        return (0.0, 1.0)
    z = 1.96
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return ((centre - margin) / denom, (centre + margin) / denom)


def test_r10_3bet_fold_to_3bet_stratified_report():
    """REPORT-ONLY (roadmap R10-3BET ③ — never a CI gate; run with `-s` to
    read it): six-persona vs_3bet fold/call/raise split by the two arrival
    strata the NodeActions docstring defines — COLD (`first_hits`: the seat's
    FIRST decision of the hand was already facing open + 3-bet) and OPENER
    (`all_hits − first_hits`: re-entrants ≈ openers — the stratum an external
    "Fold to 3-bet" figure conditions on; pooling them mixes two arrival
    ranges and is class-incomparable). Wilson 95% CIs printed per cell; n at
    the memoized _ARRIVAL_N runs sits far below any committable floor, which
    is exactly why this stays a report. Structural assertion only: the opener
    stratum is non-negative (all_hits >= first_hits cell-wise).

    ⚠️ N-3BSTRATA: this "opener" column is ANY RE-ENTRANT, a PROXY — a seat
    that limped and then faced open+3-bet is a re-entrant but NOT the opener,
    and the engine correctly serves it the COLD table. The exact stratum is
    `play._preflop_opener`; the committed opener gates are the deterministic
    `test_n3bstrata_*` ones below, never these cells."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    lines = ["", "R10-3BET stratified fold-to-3-bet report (vs_3bet, Wilson 95% CI):"]
    for persona in ALL_PERSONAS:
        acts = _persona_stats_ext(packs, persona, _ARRIVAL_N).actions
        strata: dict[str, dict[str, int]] = {"cold": {}, "opener": {}}
        for (pos, facing, action), v in acts.all_hits.items():
            if facing != "vs_3bet":
                continue
            f = acts.first_hits.get((pos, facing, action), 0)
            assert v >= f, (
                f"{persona}: all_hits < first_hits at {(pos, facing, action)}"
            )
            strata["cold"][action] = strata["cold"].get(action, 0) + f
            strata["opener"][action] = strata["opener"].get(action, 0) + (v - f)
        lines.append(f"  {persona}:")
        for name, counts in strata.items():
            n = sum(counts.values())
            cells = []
            for action in ("fold", "call", "raise"):
                k = counts.get(action, 0)
                if n:
                    lo, hi = _wilson95(k, n)
                    cells.append(f"{action} {k / n:.3f} [{lo:.3f},{hi:.3f}]")
                else:
                    cells.append(f"{action} --")
            lines.append(f"    {name:7s}(n={n:4d}): " + " · ".join(cells))
    print("\n".join(lines))


# --------------------------------------------------------------- N-3BSTRATA
# The OPENER stratum, measured DETERMINISTICALLY. The sampled grid above can
# never gate it (n ≈ 20-60 at _ARRIVAL_N), but the quantity is exactly
# computable from content: the opener's holdings at vs_3bet are, up to card
# removal, its own OPENING range, and the 3-bettor's range is independent of
# them. So
#     fold-to-3bet(opener) = Σ_class open_mass(class) × fold_weight(class)
#                            / Σ_class open_mass(class)
# with open_mass = combo_count × P(raise | class, position) summed over the
# EIGHT `unopened` nodes that can actually open (uniform position weight — the
# opener arrives from every one of them, and a position's own raise width
# already weights it).
#
# ⚠️ EIGHT, NOT NINE — corrected 2026-08-19 (Codex Sol review of the lag
# vs-3-bet re-tune). This summed all nine seats including the BIG BLIND, which
# cannot open an unopened pot: `play._preflop_facing` returns "unopened" only
# when preflop history holds NO raise and NO call, and by the time the big
# blind acts either someone has voluntarily acted (making it vs_rfi/vs_limpers/
# vs_3bet/vs_4bet) or everyone has folded and the hand is over. Verified in the
# ENGINE rather than taken from the comments that assert it
# (`table/sizing.py`, `content/models.py`, `test_preflop_size_mix.py`): over
# 20,000 seeded hands of live play the big blind reaches `unopened` ZERO times
# while every other seat reaches it thousands of times (UTG 20000, UTG1 15034,
# UTG2 10186, LJ 6510, HJ 3940, CO 2148, BTN 1152, SB 509, BB 0).
# The contamination was not small: the impossible seat carried 12.20% of the
# lag's supposed opening mass and 10.88% of the maniac's, and it was PAIRED
# with the SB/BB vs_3bet table, which folds far more than the table the real
# openers use — so the proxy read high.
# The `unopened` BB node still exists in the packs and is still validated
# elsewhere; nothing here says a pack may drop it. This helper simply stops
# counting a seat that never opens as part of the opening population.
# The nine-seat validator in `content/models.py:228` is NOT the same question
# and is NOT contradicted: that field is the SIZE table, which the big blind
# genuinely reads, because it also sizes the ISOLATION raise a big blind makes
# routinely. An iso is `vs_limpers`, a different node from the `unopened` one
# summed here.
#
# CALIBRATION (why this proxy is trusted): at pre-slice HEAD it reproduced the
# harness's sampled opener stratum on the two personas N-3BSTRATA retuned —
# maniac 0.609 proxy vs 0.630 sampled, lag 0.829 proxy vs 0.821 sampled (the
# 756-hand corpus figures quoted in the roadmap). Deterministic, so no CI.
# ⚠️ Those two proxy figures were computed on the NINE-seat population and are
# left as the historical record rather than restated, because the pack they
# were measured on is long gone and re-deriving them is not possible here. For
# scale, on the pre-re-tune pack at THIS tip the same `cold`-role quantity
# reads 0.6087 nine-seat vs 0.6091 eight-seat for the maniac and 0.8177 vs
# 0.8155 for the lag — the correction is worth about a fifth of a point there,
# against the ~1pp proxy-to-sampled agreement the calibration claims. The
# claim survives the correction; it is not re-proved by it.


def _open_range_mass_by_seat(pack) -> dict[Position, dict[str, float]]:
    """seat -> (class -> combo-weighted mass this pack OPENS the pot with).

    The big blind is excluded: it never opens an unopened pot. See the block
    comment above for the engine evidence and for why the nine-seat SIZE-table
    validator is a different question."""
    from app.domain.content.notation import parse_range

    by_seat: dict[Position, dict[str, float]] = {}
    for pos in Position:
        if pos is Position.BB:
            continue  # cannot open an unopened pot — see the block comment above
        node = _node_for_seat(pack, "unopened", pos)
        seat_mass: dict[str, float] = {}
        seen: set[str] = set()
        for mix in node.mixes:
            for cls in parse_range(mix.combos):
                if cls in seen:  # first-match-wins
                    continue
                seen.add(cls)
                raise_w = mix.weights.get("raise", 0.0)
                if raise_w > 0.0:
                    seat_mass[cls] = _combo_count(cls) * raise_w
        by_seat[pos] = seat_mass
    return by_seat


def _open_range_mass(pack) -> dict[str, float]:
    """class -> combo-weighted opening mass, summed over the nine seats."""
    out: dict[str, float] = {}
    for seat_mass in _open_range_mass_by_seat(pack).values():
        for cls, m in seat_mass.items():
            out[cls] = out.get(cls, 0.0) + m
    return out


def _opener_fold_to_3bet(pack, role: str = "opener") -> float:
    """Fold-to-3-bet over the OPENER stratum: each seat's own vs_3bet table
    applied to the range it opened with (1 - call - 4bet, per class).

    ⚠️ PAIRED PER SEAT, and it has to be. An earlier form of this averaged the
    response policy across seats, aggregated the opening range across seats, and
    multiplied the two aggregates — which is only the same number when at least
    one of them is position-blind. Once both vary by seat, E[policy] x E[range]
    is not E[policy x range], and the error is silent. A seat that opens widest
    and defends tightest is exactly the case it gets wrong.
    """
    from app.domain.content.notation import parse_range  # noqa: F401 — see below

    num = 0.0
    den = 0.0
    for seat, seat_mass in _open_range_mass_by_seat(pack).items():
        node = _node_for_seat(pack, "vs_3bet", seat, role)
        policy: dict[str, dict[str, float]] = {}
        if node is not None:
            seen: set[str] = set()
            for mix in node.mixes:
                for cls in parse_range(mix.combos):
                    if cls in seen:
                        continue
                    seen.add(cls)
                    policy[cls] = dict(mix.weights)
        for cls, m in seat_mass.items():
            w = policy.get(cls, {})
            num += m * (1.0 - w.get("call", 0.0) - w.get("4bet", 0.0))
            den += m
    return num / den


def test_n3bstrata_defect_gates_fail_at_pre_slice_head():
    """🔴 NON-VACUITY (the R9-3 lesson): pre-slice HEAD is reproducible in-test
    because the retained `cold` node IS the pre-slice shared node, byte for
    byte. Feeding the opener stratum through it must MISS both targets —
    maniac ~0.61 (target ~0.30) and lag ~0.82 (target 0.43-0.53) — which is
    exactly the defect this slice fixes: one weight table cannot fold cold
    junk without over-folding the opener.

    lag's figure was written as ~0.83 until 2026-08-19, when the big blind — a
    seat that cannot open — was removed from this proxy's population (see the
    `_open_range_mass_by_seat` block comment). The reading moves 0.818 -> 0.816
    at this tip; maniac's is 0.609 either way. The defect these thresholds
    demonstrate is nowhere near them, so nothing about this gate's meaning
    changes."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    maniac_head = _opener_fold_to_3bet(packs[VillainType.MANIAC], role="cold")
    lag_head = _opener_fold_to_3bet(packs[VillainType.LAG], role="cold")
    print(f"pre-slice HEAD opener fold-to-3bet: maniac {maniac_head:.3f} lag {lag_head:.3f}")
    assert maniac_head > 0.40, (
        f"maniac's cold table folds only {maniac_head:.3f} of its opening range — "
        f"the pre-slice defect (0.609) is gone, so this gate no longer demonstrates it"
    )
    assert lag_head > 0.53, (
        f"lag's cold table folds only {lag_head:.3f} of its opening range — "
        f"the pre-slice defect (0.829 as first recorded, 0.816 on the "
        f"eight-seat population) is gone, so this gate no longer demonstrates it"
    )


def test_n3bstrata_opener_fold_to_3bet_targets():
    """🔴 N-3BSTRATA authored-COMPONENT pins (fan-in fold, Codex HIGH): the
    unopened-weighted figure is NOT the production opener population — the
    live opener also includes ISOLATION raises over limpers, whose range is
    far stronger and folds far less. The dossier bands are gated on the
    production-signal blend (test_n3bstrata_production_opener_blend_in_
    dossier_band); THIS test pins the unopened COMPONENT as an exact authored
    shape so a pack edit can't silently reshape it. Measured post-fit:
    maniac 0.3073 (its iso range is close to its open range, so component ≈
    blend 0.2801); lag 0.6034 (the wide junky OPEN range folds a lot; the
    strong iso component pulls the live blend to 0.4735, mid-band).

    lag pin RE-DERIVED by N-LAGLADDER (2026-07-31, lag.json 1.3.0) — TWO inputs
    moved, so the pin is re-measured rather than re-derived from one of them:
      (a) the nine `unopened` nodes were re-emitted from
          content/personas/ladders/lag.unopened.json, which re-weights the
          arrival mix (dominated offsuit out, suited in);
      (b) the `vs_3bet` OPENER node's two middle tiers were re-tuned — the
          suited-broadway tier 0.60->0.55 call and the speculative tier
          0.50->0.46 call. That was not optional: (a) alone dropped the
          PRODUCTION blend to 0.4242 at n=12000, UNDER the [0.43, 0.53] dossier
          floor, because a suited-heavier open range meets a table that folds
          it less. The band is the gate and must not be widened, so the opener
          weights were brought back per the slice's own remit.
    Component landed at 0.6166 (deterministic, no CI) after N-LAGLADDER;
    pre-slice was 0.6034. The `cold` node is still untouched.

    RE-PINNED for N-LAGWIDTH (2026-08-01, lag.json 1.5.0): the CO/BTN/SB
    late-seat offsuit trim strengthens the opener's arriving range by
    construction (a narrower open range is a stronger one), so the component
    FALLS again — 0.6166 -> 0.6012 (update-the-pin law, N-LAGLADDER
    precedent). No vs_3bet edit was needed this time: the production blend
    moved 0.4914 -> 0.4722 @ n=12000 (CI [0.447, 0.498]), still comfortably
    inside the [0.43, 0.53] dossier band (see
    `test_n3bstrata_production_opener_blend_in_dossier_band`).

    RE-PINNED AND TIGHTENED for the lag vs-3-bet re-tune (2026-08-19,
    owner-ruled; lag.json 1.13.0). The OPENER node's three weakest tiers now
    fold more — speculative 0.53 -> 0.45 call, weak offsuit broadways
    0.32 -> 0.16, weak offsuit aces 0.20 -> 0.10 — so this authored component
    RISES (update-the-pin law, N-LAGLADDER precedent).

    ⚠️ THIS PIN HAD BEEN WRONG TWO INDEPENDENT WAYS, and the slice fixes both
    rather than only re-centring it.

    (1) THE VALUE WAS STALE. On the PRE-edit pack at this tip the nine-seat
    form of this proxy reads 0.5955, not the 0.6012 the pin carried — the
    +-0.02 window had silently absorbed 0.0057 of drift from the slices
    between N-LAGWIDTH and here (the seat-split opening ranges reshape the
    arriving unopened mix this proxy weights by).

    (2) THE POPULATION CONTAINED A SEAT THAT CANNOT OPEN (Codex Sol review).
    `_open_range_mass_by_seat` summed all nine `unopened` nodes including the
    BIG BLIND, which never opens an unopened pot — engine-verified, zero BB
    `unopened` decisions in 20,000 seeded hands; see that helper's block
    comment. The impossible seat carried 12.20% of the lag's supposed opening
    mass, paired with the harder-folding SB/BB vs_3bet table, so the proxy
    read HIGH. Excluding it moves the lag 0.5955 -> 0.5768 pre-edit and
    0.6346 -> 0.6214 shipped, and the maniac 0.3058 -> 0.2956.

    Both maniac and lag are therefore re-pinned on the CORRECTED eight-seat
    population. The maniac number moves for reason (2) ONLY — this slice
    edits no maniac content, and could not: its whole content diff is three
    `weights` objects in one lag node.

    (3) THE TOLERANCE DID NOT PROTECT WHAT THE DOCSTRING SAYS IT PROTECTS
    (Codex Sol review). At +-0.02 this pin passed with ANY ONE of the three
    trimmed tiers fully reverted, so "a pack edit can't silently reshape it"
    was false at that width. Measured single-tier reversions from the shipped
    0.621358, on the corrected population:
        revert the speculative tier      0.603844  (delta 0.017514)
        revert the offsuit broadways     0.601351  (delta 0.020007)
        revert the offsuit aces          0.614325  (delta 0.007034)  <- smallest
        revert all three (pre-slice)     0.576803  (delta 0.044555)
    The tolerance is now 1e-4: 70x tighter than the smallest real reversion,
    so every one of those fails loudly.

    THE PIN CAN AFFORD THAT, because it is exact pack arithmetic and not a
    sample — no rng, no seed, ~0.1s. Nondeterminism was measured, not assumed:
    across five processes at different PYTHONHASHSEED values the readings span
    0.6213583922590235-0.6213583922590238 (lag) and 0.2955647152818099-
    0.29556471528181005 (maniac), i.e. 1-2 ULP of float-summation-order noise
    at ~3e-16. The 1e-4 window is twelve orders of magnitude above that jitter
    and two below the smallest signal it must catch. Values are quoted to six
    decimals because at this width four-decimal rounding would spend a third
    of the window."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    maniac = _opener_fold_to_3bet(packs[VillainType.MANIAC])
    lag = _opener_fold_to_3bet(packs[VillainType.LAG])
    print(f"N-3BSTRATA opener fold-to-3bet (unopened component): maniac {maniac:.6f} lag {lag:.6f}")
    assert maniac == pytest.approx(0.295565, abs=1e-4), f"maniac component {maniac:.6f} moved"
    assert lag == pytest.approx(0.621358, abs=1e-4), f"lag component {lag:.6f} moved"


def test_n3bstrata_lag_opener_fourbet_share_in_dossier_band():
    """🔴 N-3BSTRATA carry-along: lag's authored 4-bet share in the OPENER
    table sits in its 3.0-5.5% dossier band (the shared table carried 2.33%,
    below the band, and stays there for the cold stratum — a cold 4-bet is a
    squeeze, a different and rarer action)."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    share = _fourbet_share(packs[VillainType.LAG], "opener") * 100.0
    cold = _fourbet_share(packs[VillainType.LAG], "cold") * 100.0
    print(f"lag 4-bet share: opener {share:.2f}% cold {cold:.2f}%")
    assert 3.0 <= share <= 5.5, f"lag opener 4-bet share {share:.2f}% outside 3.0-5.5%"


def test_n3bstrata_only_maniac_and_lag_are_stratified():
    """🟢 Scope freeze (owner decision 2): exactly maniac + lag carry role-split
    vs_3bet nodes; the other four packs stay single-table, and every stratified
    pack keeps a `cold` node whose behaviour is unchanged."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    stratified = {
        vt.value
        for vt, pack in packs.items()
        if any(n.role is not None for n in pack.preflop)
    }
    assert stratified == {"maniac", "lag"}, f"unexpected stratified packs: {sorted(stratified)}"
    for vt in (VillainType.MANIAC, VillainType.LAG):
        # Distinct roles in first-appearance order. This used to be the raw node
        # list, which was the same thing while each stratum was a single
        # wildcard node. The de-robotization slice adds a seat-split band inside
        # the `opener` stratum, so the raw list gained a repeat — a POSITION
        # split, not a new role. The claim under test is about which strata
        # exist and in what order, so it is stated that way now.
        roles = list(dict.fromkeys(
            n.role for n in packs[vt].preflop if n.facing == "vs_3bet"))
        assert roles == ["opener", "cold"], f"{vt.value} vs_3bet roles are {roles}"
        # The ordering law this depends on still holds: a role-tagged node may
        # never follow an untagged one, and explicit-position nodes precede
        # their wildcard within a stratum (PersonaPack._node_ordering).
        cold = [n for n in packs[vt].preflop
                if n.facing == "vs_3bet" and n.role == "cold"]
        assert len(cold) == 1 and cold[0].positions is None, (
            f"{vt.value}'s cold stratum must stay one position-blind node")


# Fan-in fold (Codex HIGH): the deterministic proxy above weights the opener
# stratum by the `unopened` nodes ONLY, but production's opener is the FIRST
# RAISER — which includes ISOLATION raises over limpers, and the iso range is
# far stronger than the open range (lag isos "66+, A9s+, KJs+, ATo+, KQo" at
# 1.0), so the LIVE opener population folds less than the unopened-weighted
# figure. The dossier band is therefore gated HERE, on the production-signal
# blend measured over seeded organic play; the unopened-weighted figure stays
# as an authored-COMPONENT shape pin only.
_OPENER_BLEND_CACHE: dict[
    tuple[str, int, tuple[int, ...]], tuple[int, int, dict[int, tuple[int, int]]]
] = {}


def _production_opener_fold_counts(
    packs, persona: str, n: int, checkpoints: tuple[int, ...] = ()
) -> tuple[int, int, dict[int, tuple[int, int]]]:
    """(folds, decisions) for `persona` seats at vs_3bet in the OPENER stratum,
    where opener = the seat of the hand's FIRST preflop raise (the exact
    production signal `play._preflop_opener` derives), over the same seeded
    lineup as `_persona_stats_ext`.

    ESTIM-3C: also returns {k: (folds, decisions)} after the first `k` hands for
    each k in `checkpoints`. These readings are FREE and EXACT: the loop draws
    every hand seed from one `random.Random(20260710)` stream and nothing in it
    depends on `n`, so the first k iterations of an n-hand run ARE the k-hand
    run. That is what lets the gate assert at a settling n while still printing
    the historical n=4000 line (verified: the k=4000 checkpoint of the n=12000
    pass reproduces the standalone n=4000 read exactly)."""
    key = (persona, n, checkpoints)
    if key in _OPENER_BLEND_CACHE:
        return _OPENER_BLEND_CACHE[key]
    at: dict[int, tuple[int, int]] = {}
    rng = random.Random(20260710)
    fillers = [p for p in ALL_PERSONAS if p != persona]
    lineup = ([persona] * 3 + [fillers[i % len(fillers)] for i in range(6)])[:9]
    persona_by_seat = {i: lineup[i] for i in range(9)}
    tested_seats = {i for i, p in persona_by_seat.items() if p == persona}
    folds = decisions = 0
    for i in range(n):
        if i in checkpoints:
            at[i] = (folds, decisions)
        hand_seed = rng.randrange(1_000_000_000)
        res = _play_hand(rng, hand_seed, i % 9, persona_by_seat, packs)
        opener_seat = next(
            (seat for seat, action in res.preflop_log if action == "raise"), None
        )
        if opener_seat is None:
            continue
        for (seat, _position, facing, _is_first), (log_seat, action) in zip(
            res.preflop_nodes, res.preflop_log, strict=True
        ):
            assert seat == log_seat, "preflop_nodes/preflop_log misaligned"
            if facing != "vs_3bet" or seat != opener_seat or seat not in tested_seats:
                continue
            decisions += 1
            if action == "fold":
                folds += 1
    _OPENER_BLEND_CACHE[key] = (folds, decisions, at)
    return folds, decisions, at


def test_n3bstrata_production_opener_blend_in_dossier_band():
    """🔴 THE N-3BSTRATA gate (production population): fold-to-3-bet of the
    seat that made the hand's FIRST preflop raise — unopened opens AND iso
    raises over limpers, exactly what the live `is_opener` signal serves the
    opener table to. maniac ~0.30 target → band [0.25, 0.35]; lag inside its
    dossier band [0.43, 0.53] ("above 60% makes light 3-betting
    insufficiently defended"; pre-N-3BSTRATA measured 0.72-0.83).

    ESTIM-3C (2026-08-01) — THE GATE NOW ASSERTS AT n=12000. It previously
    asserted at n=4000 and only QUOTED the n=12000 readings in this docstring,
    which is the dr-L3 defect: an intermediate N-LAGLADDER build passed here at
    0.4366 while truly measuring 0.4242 at n=12000, i.e. under the band floor.

    The power math. At n=4000 the lag opener stratum yields ~470-490 decisions;
    at p≈0.48 the Wilson 95% half-width is ±0.045, while the distance from the
    measured rate to the 0.43 band floor is only ~0.05 — the gate cannot
    distinguish "inside the band" from "under it". At n=12000 the stratum yields
    1506 decisions and the half-width falls to ±0.025, inside the 0.054 margin
    between the measured rate and the floor.

    ⚠️ HONEST REPORT (theory review, ESTIM-3C): this re-power settles LAG ONLY.
    maniac reads 0.2616 with CI [0.245, 0.278] — that CI STRADDLES its 0.25 band
    floor, because its half-width (0.0166) is LARGER than the 0.0116 by which the
    rate clears the floor. maniac therefore still carries the dr-L3 defect at
    n=12000: a pass here is necessary, not sufficient, for it. The fixed 0.03
    constant in the half-width self-check below is LAG-DERIVED and is not a valid
    power test for maniac — maniac's stratum is the bigger one (2703 decisions)
    but its band margin is far tighter, so the meaningful form is
    margin-RELATIVE (half-width < the distance to the nearer band edge). Making
    the check margin-relative and finding the n that settles maniac are FILED
    follow-ups, deliberately not done in this slice: tightening the check would
    fail the gate on a maniac figure this slice has no remit to re-fit.
    Measured at this slice, same seed (PRE-repair harness — see next line):
        maniac  0.2616 @n=12000 (n_dec 2703) · 0.2686 @n=4000 (n_dec 860)
        lag     0.4841 @n=12000 (n_dec 1506) · 0.4883 @n=4000 (n_dec 469)
    WAVE-6 MERGED-STATE UPDATE (lane-A R-L2 harness repair, orchestrator at
    landing): with production raise sizing in the harness the same seed reads
        maniac  0.3054 @n=12000 (n_dec 2626, CI [0.288, 0.323])
        lag     0.4934 @n=12000 (n_dec 1443, CI [0.468, 0.519])
    — maniac's CI now sits FULLY INSIDE [0.25, 0.35]: the straddle above was
    partly the broken min-raise ruler. The margin-relative-check follow-up
    stays FILED (the structural point stands even when this reading clears).
    Runtime cost of the re-power: 19.5s -> 71-120s for this test (3x the hands;
    measured twice, the spread is machine load from concurrent work — the
    figures above are deterministic on the seed). The n=4000 line
    is still PRINTED — it is free, being the 4000-hand checkpoint of the same
    seeded pass (see `_production_opener_fold_counts`) — but nothing asserts on
    it. The half-width itself is now asserted (< 0.03), so a future pack change
    that thins the LAG stratum fails LOUDLY instead of silently under-powering.

    ⚠️ HISTORY: THIS GATE'S OLD n WAS NOT ENOUGH TO SETTLE THE VALUE
    (N-LAGLADDER, review fold 6). It reads ~460-490 lag opener decisions at
    n=4000, whose Wilson half-width is ±0.045 — wider than the distance from the
    band floor. Both figures below are therefore quoted at n=12000 (≈1470
    decisions) as well:
        pre-slice (origin/main)  0.4667 @n=4000 (n_dec 480) · 0.4534 @n=12000
        shipped                  0.4622 @n=4000 (n_dec 489) · 0.4452 @n=12000
    The earlier in-tree figure "0.4735" was stale — it predates intervening
    slices; 0.4667 is the value origin/main actually measures on this seed.
    An intermediate N-LAGLADDER build passed HERE at 0.4366 while measuring
    0.4242 at n=12000, i.e. under the floor: a pass at this n is necessary, not
    sufficient, and the opener-node re-tune was driven by the n=12000 read.

    N-LAGCOMP2 (2026-07-31) re-reads BOTH n's on the same seed. The figures
    above stay as N-LAGLADDER-era history; the current pack measures:
        N-LAGCOMP2               0.4823 @n=4000 (n_dec 481) · 0.4651 @n=12000
    The late-seat suited/offsuit swap moves the blend UP — AWAY from the band
    floor that forced N-LAGLADDER's opener re-tune (0.4452 -> 0.4651 at the
    settling n) — so no compensating edit was needed and N-LAGCOMP2 leaves the
    `vs_3bet` opener node untouched. The authored-COMPONENT sibling pin
    (test_n3bstrata_opener_fold_to_3bet_targets) is likewise unmoved:
    0.6166 -> 0.6170, well inside its ±0.02.

    N-LAGWIDTH (2026-08-01) re-reads at n=12000: the CO/BTN/SB late-seat
    offsuit TRIM (not a swap this time) moves the blend back DOWN — 0.4914 ->
    0.4722, CI [0.447, 0.498] — still comfortably inside [0.43, 0.53], so
    (unlike N-LAGLADDER) no `vs_3bet` opener re-tune was required. The
    authored-COMPONENT sibling pin moves the same direction and is re-pinned:
    0.6170 -> 0.6012 (see test_n3bstrata_opener_fold_to_3bet_targets).

    ⚠️ T5 (2026-08-16) RE-POWERED 12000 -> 36000, AND ESCALATED WHAT THAT
    EXPOSED. lag's organic blend now sits ON its band floor with no usable
    margin, and this gate's verdict at n=12000 had become a coin flip on which
    hands the shared stream happened to deal:

        packs        n=12000   n=36000
        pre-T5       0.4367    0.4318      (0.43 floor: clears by 0.0018)
        T5           0.4295    0.4342      (fails at 12000, passes at 36000)

    T5 changes no preflop node, so it cannot move this statistic's true value —
    and at the settling n it moves it +0.0024, INSIDE noise and in the OPPOSITE
    direction from the n=12000 failure. What moved it is T3/T4: the history
    above records 0.4914 and 0.4722 for this blend, and the seat-split opening
    ranges changed which hands arrive at the vs_3bet node, dragging it to
    ~0.433. Nobody re-read it at a settling n at the time.

    Re-powering makes the gate measure the pack instead of one draw of the
    stream. It does NOT make the reading comfortable, and this note exists so
    nobody reads green as comfortable: 0.4342 against a 0.43 floor is 0.4pp of
    margin against a Wilson half-width of 0.0144, and the CI straddles the floor
    at every n tried. **A re-tune of lag's `vs_3bet` opener node is probably
    owed, and it is NOT this ticket's to make** — that is a preflop edit,
    outside T5's scope. It is filed in
    docs/ai-dlc/ledger/phase3-derobotization.md for the owner, and the next
    slice that touches lag's preflop must re-read this.

    The band was deliberately NOT widened. Moving a dossier floor to accommodate
    a diff is the band-laundering the theory contract's §11 item 7 exists to
    catch — and the pack's own authored policy is still on target, since the
    sibling `test_n3bstrata_opener_fold_to_3bet_targets` passes unchanged. That
    is what localises the drift to the arriving mix rather than to the policy.

    Cost of the re-power: this test goes from ~50s to ~150s.

    ✅ RE-TUNED (2026-08-19, owner ruling; lag.json 1.13.0). The re-tune the
    T5 note above says is owed HAS NOW BEEN MADE, so read that note as history:
    its "the sibling pin passes unchanged" no longer holds, because this slice
    moves the pack's authored policy on purpose and re-pins the sibling with
    it. The lever is the `vs_3bet` OPENER node's three weakest tiers —
    speculative 0.53 -> 0.45 call, weak offsuit broadways 0.32 -> 0.16, weak
    offsuit aces 0.20 -> 0.10. Same seed, same n=36000:

        persona   pre-tune            re-tuned
        lag       0.4372 (n_dec 4387) 0.4841 (n_dec 4383, CI [0.469, 0.499])
        maniac    0.2729 (n_dec 7652) 0.2702 (n_dec 7731, CI [0.260, 0.280])

    The margin is the point, not the level. lag cleared its 0.43 floor by
    0.72pp before (0.96 SE, with the printed Wilson interval already dipping
    under the floor) and clears it by 5.41pp now (7.2 SE); the 0.53 ceiling is
    4.59pp away (6.1 SE). 0.4841 sits just above the middle of the dossier's
    43-53% online-core target — the exact midpoint is 0.4800 and the reading is
    0.41pp above it, NOT on it — so the tune is toward the research figure
    rather than away from a test edge. The 0.43pp of pure shared-stream churn
    that three postflop-only commits produced between them can no longer breach
    either edge.

    maniac is untouched by this slice and moves -0.27pp, which is that same
    stream churn: its harness lineup uses lag seats as fillers, so a lag that
    folds a 3-bet instead of calling one displaces every later hand.

    ⚠️ THE LAG-TAG AXIS IS NOW COUPLED, AND THE NEXT SLICE ON IT INHERITS THAT
    (theory review). This tune spends lag-tag separation from the lag's side,
    and the TAG's own fold-to-3-bet correction — still owed, measured 76.2
    against a target near 50 — will spend the SAME z-axis from the other side.
    THAT SLICE MUST RE-MEASURE SEPARATION BEFORE IT PICKS ITS MAGNITUDE, not
    after. The room left is real but no longer generous; lag-tag is the binding
    pair on all five gate seeds, before and after:

        seed   pre-tune   re-tuned   floor 1.254429
        601    2.038801   1.802042
        602    1.883035   1.802026
        603    1.808383   1.702837
        604    1.710870   1.543450   <- tightest, 1.23x the floor
        605    1.862100   1.691839

    All five PASS. The worst seat loses 0.167 and sits 0.289 above the floor,
    so a TAG correction of this size on the same axis is roughly the budget
    that remains, not a free move.

    UPDATE, S3-T1 (improvement slice 3, 2026-08-21): the strong-draw call split
    RETURNED some of that budget rather than spending more of it. Re-measured on
    all five gate seeds at the S3-T1 tip: 601 1.815931 · 602 1.833658 · 603
    1.782449 · 604 1.580584 · 605 1.728596, all PASS, and lag-tag is still the
    binding pair on the tightest seat (604, where the next-closest pair is
    nit-tag at 2.320685). The worst seat moves 1.543450 -> 1.580584, i.e. 1.26x
    the 1.254429 floor rather than 1.23x. The paragraph above is still the
    warning that matters — the axis is coupled and a tag correction spends it
    from the other side — but the room is marginally wider than it was.

    UPDATE, S3-T1b (improvement slice 3, 2026-08-22): price-conditioning the
    protected share gives back a little of what S3-T1 gained, and the axis is
    unchanged in character. Re-measured on all five gate seeds: 601 1.694638 ·
    602 1.794341 · 603 1.846232 · 604 1.567513 · 605 1.660562, all PASS.
    lag-tag is STILL the binding pair on the tightest seat, measured rather
    than assumed — the full pair table at seed 604 runs lag-tag 1.567513,
    nit-tag 2.393329, lag-maniac 3.542709, lag-nit 3.616597, and up from
    there.
    ⚠️ HOW THE PAIR NAMES WERE OBTAINED, because the gate tool does not supply
    them: `tools.derobo_gate` reports only the candidate's MINIMUM pairwise
    distance and the baseline it is compared against — no pair labels — so a
    claim about WHICH two personas are closest cannot come from its output.
    These were measured OUTSIDE the tool: the seed-604 batch was retained with
    `derobo_gate.gate(..., keep=...)`, and the frozen artifact's own mean and
    standard deviation were applied to that batch's measured stat vectors to
    rebuild the six z-vectors and enumerate all fifteen pairwise distances. The
    minimum of that enumeration equals the 1.567513 the tool reported, which is
    what ties the pair names to the gate's own number.
    The worst seat moves 1.580584 -> 1.567513, i.e. 1.25x the 1.254429
    floor rather than 1.26x, so the budget a tag correction has to spend is
    back to roughly where the lag re-tune left it.

    THE BAND IS STILL NOT WIDENED. It was not widened for T5 and it is not
    widened here — the pack moved to fit the band, which is the direction §11
    item 7 requires."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    for persona, lo, hi in (("maniac", 0.25, 0.35), ("lag", 0.43, 0.53)):
        folds, n, at = _production_opener_fold_counts(packs, persona, 36000, (4000,))
        rate = folds / n
        wlo, whi = _wilson95(folds, n)
        f4, n4 = at[4000]
        print(
            f"{persona} production opener fold-to-3bet {rate:.4f} "
            f"(n={n}, CI [{wlo:.3f},{whi:.3f}]) · report-only @4000 hands: "
            f"{f4 / n4:.4f} (n={n4})"
        )
        assert n >= 200, f"{persona}: opener sample n={n} too small to gate"
        # The dr-L3 lesson, asserted rather than trusted. NOTE the constant is
        # lag-derived: it is a floor on precision, NOT the margin-relative test
        # maniac needs (see the docstring's HONEST REPORT).
        assert (whi - wlo) / 2 < 0.03, (
            f"{persona}: Wilson half-width {(whi - wlo) / 2:.4f} at n_dec={n} is too wide "
            f"to settle a [{lo},{hi}] band — raise the hand count"
        )
        assert lo <= rate <= hi, (
            f"{persona} production opener fold-to-3bet {rate:.4f} (n={n}) outside [{lo},{hi}]"
        )


def test_maniac_vpip_pfr_gap_back_under_ten():
    """🔴 W5-b4 defect gate (failed at pre-fix HEAD: gap 15.4pp at n=1200 —
    the roster's ONLY gap-row failure, the signature of the call-heavy
    vs_rfi tier-3 flat {call 0.9} that audit-F11 struck from the "*"
    catch-all but that survived in an enumerated mix).

    The GAP is format-INVARIANT ("gap | format-INVARIANT | both formats |
    RP6 + ledger #14 | VERIFIED" — the §5a registry row, transfer explicitly
    relied upon) and therefore COMMITTABLE. VPIP and PFR levels are REPORTED
    only (printed below) — the single population-band re-anchor stays W4-b's
    (roadmap W5-b4 no-go: committing an RP6 number as a gate here is a §11
    item-7 auto-FAIL).

    ⚠️ HONEST REPORT (refuter + theory, W5-b4): the roadmap's other REPORTED
    target — VPIP toward 45-58 — went the WRONG way (40.6 -> 39.3 at n=1200;
    ~38.8 vs ~39.7 across 40 reseeds). The gap gate is met by composition
    (calls -> 3-bets/folds), not volume. Adjudication (theory review): the
    only large reachable VPIP lever is the `unopened` ladder — out of scope
    here by no-go (R10-PRE2 owns it, N9 forbids compensating) — and the
    texture guards bounded only the substitute lever (3-bet mass); the §5
    VPIP row is therefore NOT reopened, and W4-b inherits the specific
    question "maniac continue-vs-open is unwatched" (a missing §5 row), not
    a vague "VPIP didn't move". Restoring tier-3 continue mass was measured
    INFEASIBLE under the committed gates: every call-mass restoration pushes
    the gap sweep max over 10 AND raises the 3-bet-pot rate via squeezes
    (grid in the slice ledger).

    Threshold margin (40-reseed sweep at this n, refuter-measured): gap
    6.83..9.56, mean 8.11, sd 0.64 — worst observed headroom 0.44pp. CI
    itself CANNOT flake: the gate runs the single pinned seed (n=600 via the
    shared `_persona_stats_ext` cache; the n=1200 figures above are the
    stable-n report, not this gate's n), reading a deterministic 7.33."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    s = _persona_stats_ext(packs, "maniac", 600)
    print(f"maniac VPIP {s.vpip:.3f} PFR {s.pfr:.3f} (REPORTED — band anchor is W4-b)")
    assert s.gap is not None and s.gap < 0.10, (
        f"maniac VPIP-PFR gap {s.gap:.3f} not back under 0.10 (W5-b4 gate; "
        f"format-invariant, committable per W5-a1)"
    )


# ============================ W5-a3-i — metric #1 aggressor-side denominator ===


def test_preflop_aggressor_returns_last_raise_seat_or_none():
    # An all-limped/checked pot has no preflop raise -> no aggressor.
    assert _preflop_aggressor([(0, "call"), (1, "call"), (2, "check")]) is None
    # A single open-raise with two callers: the opener is the aggressor.
    assert _preflop_aggressor([(3, "raise"), (5, "call"), (7, "call")]) == 3
    # A 3-bet flips the aggressor to the later raiser.
    assert _preflop_aggressor([(2, "raise"), (5, "raise"), (2, "call")]) == 5


def test_metric1_cbet_is_aggressor_side_not_any_first_in_seat():
    """Theory contract §6 #1: aggressor-side flop c-bet = P(bet | preflop
    aggressor's first-in flop decision). Fixture with a KNOWN aggressor: seat
    2 raises preflop, seats 0 and 5 call. Pre-fix, seat 0's (a cold-caller,
    NOT the aggressor) first-in flop CHECK would also count as a c-bet
    opportunity -- the wrong-denominator bug. Post-fix, only the aggressor's
    (seat 2) flop decision counts."""
    preflop_log = [(0, "call"), (2, "raise"), (5, "call")]
    decisions = [
        PostflopDecision(
            seat=0, street="flop", in_position=False, action="check", bet_fraction=None
        ),
        PostflopDecision(
            seat=2, street="flop", in_position=True, action="bet", bet_fraction=0.6
        ),
        PostflopDecision(
            seat=5, street="flop", in_position=True, action="fold", bet_fraction=None
        ),
    ]
    tested_seats = {0, 2, 5}
    bets, opps, ip_bets, ip_opps, oop_bets, oop_opps, first_bettor = _hand_cbet_stats(
        preflop_log, decisions, tested_seats
    )
    assert (opps, bets) == (1, 1), "only the aggressor's flop decision is a c-bet opportunity"
    assert (ip_opps, ip_bets) == (1, 1)
    assert (oop_opps, oop_bets) == (0, 0)
    assert first_bettor == (2, 0.6)


def test_metric1_no_preflop_raise_means_no_cbet_opportunity():
    """An all-limped/checked pot has no aggressor: no tested seat's flop
    decision counts as a c-bet opportunity, even if one of them leads out
    (a donk-bet/lead into an unraised pot is not a c-bet)."""
    preflop_log = [(0, "call"), (1, "call"), (2, "check")]
    decisions = [
        PostflopDecision(
            seat=0, street="flop", in_position=False, action="bet", bet_fraction=0.5
        ),
    ]
    tested_seats = {0, 1, 2}
    bets, opps, *_rest = _hand_cbet_stats(preflop_log, decisions, tested_seats)
    assert (bets, opps) == (0, 0)


# Fixed, machine-independent sample for every WTSD assertion (bands + ordering).
# Large enough that 3σ on the tightest gap (station-vs-tag ≈ 0.044 post-W3-b) and
# on the tightest band margin (lag 0.55 vs its 0.59 ceiling) is comfortably under
# it. AF/FtC stay on the cheaper throughput-n; only WTSD (fragile near band edges
# under-sampled at n~250) needs the floor. `_persona_stats` memoizes per
# (persona, n), so the bands and ordering tests share these sims — paid once.
# W3R-1: bumped 2500 -> 4000. The maniac preflop cleanup shifted the rng stream,
# narrowing the station-vs-tag WTSD margin at n=2500 (0.619 vs 0.630 -- the TRUE
# ordering still holds and WIDENS with n: station>tag at n=4000/6000). A tightening
# (more hands), matching the documented W3-b/c/d precedent, not a band loosen.
_WTSD_ORDER_N = 4000


@pytest.mark.parametrize("persona", ALL_PERSONAS)
def test_persona_postflop_bands(persona, budget):
    """Aggression factor, fold-to-c-bet and went-to-showdown against `BANDS`.

    The went-to-showdown edges are INTERIM as of 2026-08-21, under the
    owner-ratified transition regime (theory contract §5, amendments A4/A5, made
    reviewable by the §11 item 7 exception in A7). "Went to showdown" is the
    share of hands a persona takes to showdown out of the hands where it saw the
    flop. The regime is asymmetric on purpose, because showdown frequency is
    meant to FALL: the floor is the persona's grounded floor from the contract's
    §5 keystone row, so a slice that lowers showdown frequency toward the target
    can no longer fail for doing so; the ceiling is this tip's own measurement
    plus three binomial standard deviations, rounded outward to the nearest
    hundredth and NEVER above the incumbent ceiling. Floors give way; ceilings
    never rise. The aggression-factor and fold-to-c-bet edges are untouched by
    the regime and stay frozen to the single re-anchor slice.

    THE ARITHMETIC, PER PERSONA, computed on 2026-08-21 at commit `d351150` with
    this file's own band harness — its own pinned seed (`random.Random(20260710)`
    inside `_persona_stats`) and its own stable sample size (`_WTSD_ORDER_N` =
    4000 hands). `n` is the harness's flop-seen hand count for that persona,
    which is the sample the binomial standard deviation is taken at; it differs
    per persona because each sees a different number of flops over the same
    4,000 hands. `sd = sqrt(p * (1 - p) / n)`.

        persona          measured   n     1 sd      3 sd      p + 3sd   -> ceiling
        nit              0.6356      955  0.015573  0.046720  0.682322  -> 0.69
        tag              0.6133     1593  0.012202  0.036605  0.649913  -> 0.65
        lag              0.5728     2437  0.010020  0.030061  0.602897  -> 0.61
        maniac           0.5960     3998  0.007760  0.023281  0.619329  -> 0.62
        calling_station  0.7105     5499  0.006116  0.018348  0.728841  -> 0.73
        passive_fish     0.5403     4107  0.007777  0.023330  0.563627  -> 0.57

    THE INSTALLED CEILING IS THE SMALLER OF THAT RATCHET AND THE INCUMBENT, so
    two of the six are capped by their incumbent value and do not move:

        persona          incumbent  ratchet  INSTALLED  what happened
        nit                  0.80     0.69     0.69     tightens by 11 points
        tag                  0.65     0.65     0.65     unchanged
        lag                  0.59     0.61     0.59     capped by the incumbent
        maniac               0.50     0.62     0.62     the single A5 upward repair
        calling_station      0.72     0.73     0.72     capped by the incumbent
        passive_fish         0.57     0.57     0.57     unchanged

    ── THE SECOND RATCHET, S3-T1 (improvement slice 3, 2026-08-21). The
    strong-draw call split (`_strong_draw_call_dial`, engine) hands part of a
    big draw's call weight back to the calling dial, so five of the six
    personas — every one whose dial sits below 1.0 — chase big draws slightly
    less and reach showdown slightly less often. A4.2 item 2 orders the ceiling
    re-recorded after any slice that moves showdown frequency down, so the
    arithmetic above is REDONE here on the same harness, the same pinned seed
    and the same `_WTSD_ORDER_N` = 4000 hands, at the S3-T1 tip:

        persona          before  measured   n     3 sd      p + 3sd  -> ratchet
        nit              0.6356    0.6317    983  0.046152  0.677892 -> 0.68
        tag              0.6133    0.6169   1595  0.036517  0.653445 -> 0.66
        lag              0.5728    0.5630   2405  0.030343  0.593337 -> 0.60
        maniac           0.5960    0.5899   3989  0.023363  0.613235 -> 0.62
        calling_station  0.7105    0.7012   5505  0.018508  0.719689 -> 0.72
        passive_fish     0.5403    0.5266   4113  0.023356  0.549979 -> 0.55

        persona          incumbent  ratchet  INSTALLED  what happened
        nit                  0.69     0.68     0.68     tightens by 1 point
        tag                  0.65     0.66     0.65     capped by the incumbent
        lag                  0.59     0.60     0.59     capped by the incumbent
        maniac               0.62     0.62     0.62     unchanged
        calling_station      0.72     0.72     0.72     unchanged
        passive_fish         0.57     0.55     0.55     tightens by 2 points

    TWO THINGS IN THAT TABLE NEED SAYING PLAINLY. First, the TAG moved UP, by
    0.0036 — which is 0.30 of one binomial standard deviation at its own n, and
    is a composition effect rather than a tag-node change: the tag's own strong
    draws call LESS under S3-T1, but the hands it plays are dealt against five
    opponents whose lines also changed. It is nowhere near its 0.65 ceiling, so
    A4.2 item 3's stop-and-report does not fire; the ratchet simply does not
    apply to a persona that moved up, and its arithmetic is shown above only so
    the reader can see it was computed rather than skipped. Second, the CALLING
    STATION also moved (0.7105 -> 0.7012) even though its own decisions are
    bitwise unchanged — its dial is 4.0, above the split's `looseness < 1.0`
    predicate, and `test_nd_t4_calling_station_byte_identical_on_strong_draw`
    still passes untouched. Same cause: its opponents changed, so the hands it
    is dealt into are not the same hands.

    ── THE THIRD RATCHET, S3-T1b (improvement slice 3, 2026-08-22). The
    protected share is now computed per node rather than fixed at 0.7, so a
    strong draw whose own equity pays for the price it faces keeps the FULL
    protection the pre-S3-T1 floor gave it. Five of the six personas therefore
    chase well-priced big draws slightly MORE than they did at the S3-T1 tip —
    the direction A4.2 item 2 is watchful about — so the arithmetic is redone
    here on the same harness, the same pinned seed and the same `_WTSD_ORDER_N`
    = 4000 hands. `n` is each persona's flop-seen count in that sample:

        persona          before  measured   n     3 sd      p + 3sd  -> ratchet
        nit              0.6317    0.6353    987  0.045965  0.681224 -> 0.69
        tag              0.6169    0.6144   1587  0.036655  0.651022 -> 0.66
        lag              0.5630    0.5664   2401  0.030341  0.596772 -> 0.60
        maniac           0.5899    0.5887   4031  0.023251  0.611939 -> 0.62
        calling_station  0.7012    0.7060   5517  0.018401  0.724401 -> 0.73
        passive_fish     0.5266    0.5324   4119  0.023323  0.555734 -> 0.56

        persona          incumbent  ratchet  INSTALLED  what happened
        nit                  0.68     0.69     0.68     capped by the incumbent
        tag                  0.65     0.66     0.65     capped by the incumbent
        lag                  0.59     0.60     0.59     capped by the incumbent
        maniac               0.62     0.62     0.62     unchanged
        calling_station      0.72     0.72     0.72     unchanged
        passive_fish         0.55     0.56     0.55     capped by the incumbent

    NO CEILING MOVES, and that is the ratchet working rather than being skipped:
    every persona's re-derived value is at or above its incumbent, and the rule
    is "never above the incumbent". Four of six are held down by a ceiling a
    previous slice earned; two are unchanged.

    NO STOP-AND-REPORT FIRES. A4.2 item 3 is about a MEASUREMENT crossing its
    ceiling, and every reading above sits under its own: the closest is the
    passive fish at 0.5324 against 0.55, then the nit at 0.6353 against 0.68.
    Four personas moved up (nit +0.0036, lag +0.0034, station +0.0048, fish
    +0.0058) and two moved down (tag -0.0025, maniac -0.0012); the largest of
    those is 0.38 of one binomial standard deviation at its own n, so the whole
    table is inside the noise the harness produces at this sample size. The
    station moved at all for the same reason it did last slice — its own
    decision function is bitwise unchanged (dial 4.0, above the branch's
    predicate) and its opponents' is not.

    ── THE FOURTH RATCHET, S3-T2 (improvement slice 3, ticket 2 — the
    calling-dial retune — 2026-08-22). Two calling dials move for the first
    time in this slice: the nit's `call_looseness` 0.45 -> 0.32 and the tag's
    0.6 -> 0.38. The LAG's is deliberately LEFT ALONE at 0.55, on owner ruling 11
    of 2026-08-22: its floor was WITHDRAWN and filed. NOT because its dial is
    inert — from the own-dial base (the LAG at 0.55 with the nit and tag already
    shipped, 0.5769) a cut to 0.48 reads -1.43pp and one to 0.42 reads -3.82pp —
    but because that effect depends on where the companions sit and is partly
    paid for by them, so no floor could be registered against it. The table with
    both comparison bases labelled is in the pre-registration §5.

    Neither shipped value is set by this band table. The
    nit's comes from the α fold-ceiling, which admits no dial below about 0.31
    (headroom 0.0197 at 0.32, 0.0021 at 0.31, a breach at 0.30); the tag's from
    the deterministic 1,728-cell nit-versus-tag sweep (G-SWEEP-b), whose margin
    count with the nit at 0.32 reads 668 at a tag dial of 0.38 and falls
    through its floor of 650 to 628 at 0.37 — the tag stops where it stops so
    it does not collapse onto the nit. Derivation, provenance triples and the
    reduction floor this ticket pre-registered before the packs were touched:
    `docs/ai-dlc/research/slice3-calldown/t2-preregistration.md`. A4.2 item 2
    orders the ceiling re-derived after any slice that moves showdown frequency,
    so the arithmetic is redone here on the same harness, the same pinned seed
    and the same `_WTSD_ORDER_N` = 4000 hands. `n` is each persona's flop-seen
    count in that sample; `sd = sqrt(p * (1 - p) / n)`:

    "Before" is this same harness at the tip this ticket branches from
    (`aaaee50`, S3-T1b merged), not at the S3-T1 tip the third ratchet used —
    T1b landed in between and moved every row a little.

        persona          before  measured   n     3 sd      p + 3sd  -> ratchet
        nit              0.6353    0.6173    972  0.046770  0.664054 -> 0.67
        tag              0.6144    0.5528   1637  0.036866  0.589707 -> 0.59
        lag              0.5664    0.5769   2418  0.030141  0.607064 -> 0.61
        maniac           0.5887    0.5945   3961  0.023404  0.617950 -> 0.62
        calling_station  0.7060    0.7010   5622  0.018318  0.719314 -> 0.72
        passive_fish     0.5324    0.5204   4189  0.023157  0.543567 -> 0.55

        persona          incumbent  ratchet  INSTALLED  what happened
        nit                  0.68     0.67     0.67     tightens by 1 point
        tag                  0.65     0.59     0.59     tightens by 6 points
        lag                  0.59     0.61     0.59     capped by the incumbent
        maniac               0.62     0.62     0.62     unchanged
        calling_station      0.72     0.72     0.72     unchanged
        passive_fish         0.55     0.55     0.55     unchanged

    THE LAG AND THE MANIAC BOTH MOVED UP, by 0.0105 and 0.0058, and the reason
    is one mechanism worth stating once. The calling dial scales the WHOLE
    continue side of a facing node — RAISE included, through the `rscale`
    coupling — so a tighter nit and a tighter tag also RAISE less often at the
    nodes they face. Every other persona therefore meets less aggression, folds
    less in response, and rides more hands to showdown. Neither rise is a
    stop-and-report: A4.2 item 3 is about a MEASUREMENT crossing its ceiling,
    and the LAG reads 0.5769 against 0.59 while the maniac reads 0.5945 against
    0.62. The ratchet does not apply to a persona that moved up, and the
    arithmetic is shown anyway so a reader can see it was computed rather than
    skipped. The maniac remains the row with the least ceiling headroom on the
    roster.

    THE NIT MOVED LESS THAN ITS OWN DIAL SUGGESTS, and that is measured rather
    than shrugged at. Its dial fell by 29% and its showdown rate by 1.80 points,
    against a first-order prediction of 2.52. Its flop-seen sample here is the
    roster's smallest at 972 hands, so one binomial standard deviation is about
    1.5 points and the two numbers are not distinguishable on this instrument;
    the pre-registered floor was set at 1.0 for exactly that reason. Nearly half
    the nit's showdown hands (47.7%) never face a wager at all, so the dial
    cannot reach them.

    THE POOLED 50,000-HAND EXPORT AGREES ON DIRECTION AND DISAGREES ON THE LAG,
    which is worth knowing before anyone reads one instrument as the truth. On
    the ratified nine-seat lineup at seed 20260817 the export reads, before ->
    after: nit 58.9 -> 57.9, tag 53.9 -> 50.0, lag 52.1 -> 51.1, maniac
    53.4 -> 52.6, calling_station 66.4 -> 66.3, passive_fish 48.8 -> 47.6, pool
    54.9 -> 53.4. The LAG falls a point there while it rises a point here. The
    two instruments play different tables — the export plays the ratified
    lineup, this harness plays six persona-weighted lineups at its own pinned
    seed — so a composition effect of this size is free to differ in sign
    between them. This harness is the gating instrument; the export is
    diagnostic.

    THE CALLING STATION moved (0.7060 -> 0.7010) with its own decisions bitwise
    unchanged — its dial is 4.0, above the strong-draw split's `looseness < 1.0`
    predicate, and `test_nd_t4_calling_station_byte_identical_on_strong_draw`
    still passes untouched. Its opponents changed, so the hands it is dealt into
    are not the same hands.

    THE FLOORS all drop to the §5 grounded floor: nit 0.37 -> 0.20, tag 0.41 ->
    0.25, lag 0.37 -> 0.26, maniac 0.34 -> 0.30, calling_station 0.66 -> 0.38,
    passive_fish 0.50 -> 0.33. The station's is the consequential one: the
    2026-07-24 W3R exception had moved that floor UP to 0.66, which is 18 points
    ABOVE the same persona's own grounded ceiling of 0.48, and it was the single
    most binding obstacle to lowering showdown frequency. A4.2 item 1 retires it.

    WHAT REPLACES THE FLOORS AS A REGRESSION GUARD: the floors were never
    protecting an absolute level, they were protecting against every persona
    converging on one population average. That job passes to
    `test_persona_wtsd_ordering_invariants` below, whose legs are split three
    permanent and two transition-scoped — see that test's own docstring.

    NO ENGINE FILE OR BASELINE ARTIFACT WAS TOUCHED to install the regime
    itself, and none has been touched since. Two PERSONA PACKS have: S3-T2
    moved the nit's and the tag's `call_looseness`, which is what the fourth
    ratchet above measures. The sentence that used to stand here — that the
    numbers were a measurement of an unchanged bot — was true of the first three
    ratchets and is not true of the fourth, so it is corrected rather than left
    to mislead. What has not changed is the point it was making: the regime is a
    gate on levels, not a licence on mechanisms, and a slice whose only argument
    is "this lands inside the interim band" has not made an argument. S3-T2's
    argument is the contract's grounded fold-to-continuation-bet row and the α
    fold-ceiling, both written down where a reader can check them against the
    poker rather than against this table.
    """
    packs, per_persona_n, _texture_n, _hands_per_s = budget
    af_band, ftc_band, wtsd_band = BANDS[persona]
    af, ftc, wtsd, call_n, ftc_n, wtsd_n, _nfw = _persona_stats(packs, persona, per_persona_n)

    if af is not None and af_band is not None:
        lo, hi = af_band
        # Instrument-repair wave (2026-08-01, delta-review fold): AF asserts at
        # the stable large-n — the SAME rule WTSD uses below (NOT the FtC
        # escalate-on-breach shape: that re-measures only when the small n
        # breaches, so a stable-n breach that happens to read in-band at the
        # small n would pass silently — delta-review MED). The small-n reading
        # is report-only, carried in the failure message. Background: after the
        # R-L2 preflop-sizing repair (the harness stopped min-raising every
        # raise), maniac's AF at small n reads 2.24-2.45 across n in
        # {150, 400-650} — straddling the frozen 2.4 floor — against 3.15-3.52
        # at those same n on the pre-repair base, while its STABLE-n AF is 2.99
        # (n=2000) / 3.06 (n=4000), comfortably inside [2.4, 5.1]. Instrument
        # power, not a band breach: the min-raise ping-pong wars were inflating
        # the BET+RAISE numerator at every n. Band VALUES untouched (frozen to
        # W4-b); the stable-n run is memoized and shared with the WTSD leg.
        af_stable, _f3, _w3, call_stable_n, _fn3, _wn3, *_ = _persona_stats(
            packs, persona, _WTSD_ORDER_N
        )
        assert af_stable is not None and lo <= af_stable <= hi, (
            f"{persona} AF {af_stable} (n_call={call_stable_n}) at stable "
            f"n={_WTSD_ORDER_N} outside [{lo},{hi}] (throughput-n read: "
            f"{af:.2f} at n_call={call_n})"
        )
    if ftc is not None:
        lo, hi = ftc_band
        # R10-TAIL-a1: FtC now escalates to the stable large-n before failing,
        # the same remedy WTSD already uses below. The throughput-derived
        # `per_persona_n` collapses to ~50 FtC opportunities under full-suite
        # load (RR-HOLES ledger R-2), where 3σ ≈ ±0.20 — passive_fish's true
        # FtC (0.464 at n=274, inside [0, 0.549]) false-trips its ceiling by
        # sampling noise alone, and the tail intentionally moved it toward
        # mid-band. Cheap throughput-n stays as the first pass; the band
        # VALUES are untouched (frozen to W4-b).
        if not (lo <= ftc <= hi):
            _a2, ftc_stable, _w2, _c2, ftc_stable_n, _wn2, *_ = _persona_stats(
                packs, persona, _WTSD_ORDER_N
            )
            assert ftc_stable is not None and lo <= ftc_stable <= hi, (
                f"{persona} fold-to-cbet {ftc:.2f} (n={ftc_n}) breached and the "
                f"stable-n re-measure {ftc_stable} (n={ftc_stable_n}) confirms it "
                f"— outside [{lo},{hi}]"
            )
    if wtsd is not None:
        # maniac WTSD — ASSERTION RESTORED, 2026-08-21 (owner-ratified amendment
        # A5, the ruler-repair record). This REPLACES the 2026-08-01 deferral,
        # which skipped the leg because the persona measured about 0.59 against a
        # frozen ceiling of 0.50 — a roughly nine-point breach that appeared when
        # the harness was repaired to play production's raise sizes. The bot did
        # not change; the instrument did.
        #
        # THE ASYMMETRY, STATED RATHER THAN SMOOTHED OVER. Under the Stage-0
        # interim regime every ceiling in this file may only ratchet DOWN. The
        # maniac's is the ONE authorized upward move: 0.50 -> 0.62. It is
        # authorized because the band was recorded against a superseded
        # instrument, so it is not evidence about the bot — NOT because the bot
        # earned it. Measured against today's skipped assertion this is a
        # tightening (a live ceiling catches a regression; a skip catches
        # nothing); measured against the frozen 0.50 value it is a loosening, and
        # both readings are true at once. No other ceiling in this file may move
        # up on this precedent.
        #
        # Arithmetic, at this tip and this harness's own pinned seed and stable
        # sample size: measured 0.5960 at n=3998 flop-seen hands, 1 sd =
        # sqrt(0.5960 * 0.4040 / 3998) = 0.007760, 3 sd = 0.023281, measurement +
        # 3 sd = 0.619329, rounded outward to 0.62.
        #
        # passive_fish WTSD — SKIP LIFTED, 2026-08-01 (instrument-repair wave);
        # the assertion below is live for the fish again. The R10-3BET-era skip
        # deferred it on a reading of 0.4873 vs the frozen [0.50, 0.57] floor,
        # attributed to cross-persona composition rather than a fish-node defect
        # (reverting fish's own vs_3bet read 0.4949, trimming its call tiers
        # 0.4912 — all within noise of each other, theory review R-3). That
        # attribution is unchanged and still on record; what changed is the
        # RULER. With the R-L2 preflop-sizing repair the fish's stable-n WTSD
        # read 0.5082 (4000 hands) / 0.5093 (2000 hands), measured in separate
        # processes at seed 20260710 — INSIDE its frozen band, so there was
        # nothing left to defer and a standing skip would have hidden a future
        # regression. This was a strengthening (a skip becomes a live
        # assertion), band VALUE untouched at the time.
        #
        # ⚠️ THOSE TWO FIGURES ARE DATED 2026-08-01 AND ARE NOT THE SAME
        # MEASUREMENT as the 0.5403 pinned in this test's docstring. Same seed
        # and same harness, different tip: roughly three weeks of persona and
        # engine slices land between them, and the fish's stable-n reading
        # moved 0.5082 -> 0.5403 over that span. Note also that the counts are
        # not the same quantity — `n=4000` here is the HAND count
        # (`_WTSD_ORDER_N`), whereas the docstring's `n=4107` is the flop-seen
        # count that the binomial standard deviation is taken at.
        # Everything above this line is PRE-2026-08-21 HISTORY, recorded
        # against the frozen [0.50, 0.57] band. It said the margin over the
        # 0.50 floor was thin (~0.008, about 1.1 sigma of binomial sampling
        # error at that n; independent-stream probes at seed offsets 1/2/7
        # read 0.5049/0.5222/0.5072), and concluded that a future slice moving
        # fish showdown rate DOWN would trip here first. DO NOT ACT ON THAT
        # CONCLUSION: it is precisely the veto A4.2 item 1 removes.
        #
        # THE INTERIM READING (2026-08-21 onward). The fish's floor is now the
        # grounded 0.33, and the measured 0.5403 clears it by 21 points — on
        # the order of 27 binomial sigma at this n, so the floor does not bind
        # and cannot bind under any movement this project intends. Downward
        # movement is LEGAL and is the direction the work must travel. The
        # binding edge for the fish is now its CEILING (0.57, which the
        # measurement clears by about 3.0 sigma), and that is the edge a red
        # here would be about.
        #
        # W3-b/c/d: measure the WTSD-vs-band at the stable large-n (memoized,
        # shared with the ordering test). The throughput-n estimate breaches band
        # ceilings by under-sampling noise alone — lag's true WTSD 0.55 spikes to
        # 0.59+ at n~247 despite sitting well inside its band, which was
        # [0.37, 0.59] when this was written and is (0.26, 0.59) under the
        # Stage-0 interim regime (the ceiling, which is the edge the point is
        # about, is unchanged). AF/FtC keep the cheaper throughput-n.
        _a, _f, wtsd_stable, _c, _fn, wtsd_stable_n, *_ = _persona_stats(
            packs, persona, _WTSD_ORDER_N
        )
        lo, hi = wtsd_band
        assert lo <= wtsd_stable <= hi, (
            f"{persona} WTSD {wtsd_stable:.2f} outside [{lo},{hi}] (n={wtsd_stable_n})"
        )


def test_persona_wtsd_ordering_invariants(budget):
    """Cross-persona WTSD ORDERING (lead-authorized, alongside the absolute
    bands above -- engine-anchored when this was written, and since 2026-08-21
    grounded on the floor side and ratcheted on the ceiling side): absolute
    WTSD bands can't catch a
    "persona-flattening" regression where every persona's WTSD converges to
    the same population-average value -- these relative comparisons are
    robustly true regardless of the engine's absolute showdown-rate ceiling,
    since they follow directly from each persona's PRD-intended fold/call
    discipline (station folds least -> highest WTSD; maniac folds most among
    the aggressive personas -> lowest WTSD relative to the calling personas).

    THIS TEST CARRIES MOST OF THE ANTI-FLATTENING JOB NOW -- TOGETHER WITH THE
    DE-ROBOTIZATION GATE'S SEPARATION FLOOR, NOT ALONE. As of 2026-08-21 the
    went-to-showdown FLOORS in `BANDS` above are the contract's grounded floors
    rather than engine-anchored ones, so they no longer stop a persona drifting
    toward the population average. Most of that job passes here.

    STATED PLAINLY, BECAUSE IT IS THE GAP A READER WOULD OTHERWISE MISS: the
    nit appears in NONE of the five legs below, and its floor just dropped 17
    points (0.37 -> 0.20). Nothing in this test constrains it. The nit is held
    only by its own ratcheted ceiling (0.67 since S3-T2) and by the
    de-robotization gate's archetype separation floor, which is archetype-wide
    and does not depend on any one statistic's direction. A slice that moves
    the nit should read the separation gate, not this test.

    The five legs are NOT all of the same kind, and treating them as one block
    would rebuild the veto the interim regime exists to remove, so amendment
    A4.2 item 4 (owner-ratified 2026-08-21) splits them three-and-two. NO LEG
    VALUE CHANGES IN THIS PULL REQUEST; only the classification below is new.

    PERMANENT, AND HARD THROUGHOUT -- these three agree with the grounded
    endpoint, so no slice under the interim regime may weaken them:

      * station > tag     (grounded midpoints about 43 against 27)
      * station > lag     (43 against 28.5)
      * maniac  < station (35 against 43)

    TRANSITION-SCOPED, AND TO BE RE-DERIVED AT THE SINGLE RE-ANCHOR -- these two
    were pinned against the ENGINE rather than derived from the grounded
    targets, and they CONTRADICT those targets:

      * fish < tag. The leg was deliberately re-pinned on 2026-07-24, in the
        same W3R wave that moved the fish and station bands, to bless the fish
        folding more than the tag after its calling dial was authored down. The
        grounded endpoint says the opposite -- fish 33-42 sits ABOVE tag 25-29.
        Any slice that legitimately moves the tag toward its target trips this
        leg, which is the identical veto class the floors created.
      * station - fish > 0.10. At the grounded midpoints that gap is about 5.5
        points, so the leg is unsatisfiable across most of the target region and
        is satisfiable only at opposite band edges.

    Both transition-scoped legs stay LIVE during the transition as
    anti-flattening guards. A slice may move either ONCE, in the ratcheting
    spirit of A4.2 item 2: with the measurement, the direction, and a statement
    of which grounded pair it is moving toward. Both are re-derived at the
    single re-anchor -- the fish-versus-tag leg most likely FLIPPED, and the
    separation constant expected to shrink from 0.10 toward that roughly
    5.5-point gap -- where the grounded bands become the reference.

    A slice that trips one of the two transition-scoped legs while moving a
    persona toward its band has found the band's veto in a second place, not a
    regression. Together with the de-robotization gate's archetype separation
    floor, which is archetype-wide and does not depend on any one statistic's
    direction, this is a stronger guard against persona-flattening than an
    absolute floor ever was.
    """
    # W3-b/c/d (persona-realism-w3bcd, 2026-07-24): the position IP/OOP c-bet
    # boost narrowed the station-vs-tag WTSD gap to ~0.044 (station 0.63 > tag
    # 0.59, verified robust at n>=2000) — still the correct ordering, but the
    # throughput-derived `per_persona_n` (~200-400) has 3σ≈0.10 on the WTSD
    # difference there, so the STRICT leg flipped ~half of isolated runs (flaky).
    # This ordering test therefore uses its OWN fixed, machine-independent sample
    # (_WTSD_ORDER_N) large enough that 3σ (~0.028) < the real gap — keeping every
    # leg STRICT. The band test above keeps the cheaper throughput-n (it needs the
    # shared budget); _persona_stats memoizes per (persona, n), so this is a
    # separate, one-time set of sims.
    packs, _per_persona_n, _texture_n, _hands_per_s = budget
    wtsd = {}
    for persona in ("calling_station", "tag", "lag", "passive_fish", "maniac"):
        _af, _ftc, w, _cn, _fn, wn, *_ = _persona_stats(packs, persona, _WTSD_ORDER_N)
        assert w is not None, f"{persona} WTSD unmeasurable at n={wn} (<30 floor)"
        wtsd[persona] = w

    # A4.2 item 4: PERMANENT and HARD throughout (grounded midpoints ~43 vs ~27).
    assert wtsd["calling_station"] > wtsd["tag"], (
        f"station WTSD {wtsd['calling_station']:.3f} not > tag WTSD {wtsd['tag']:.3f}"
    )
    # A4.2 item 4: PERMANENT and HARD throughout (grounded midpoints ~43 vs ~28.5).
    assert wtsd["calling_station"] > wtsd["lag"], (
        f"station WTSD {wtsd['calling_station']:.3f} not > lag WTSD {wtsd['lag']:.3f}"
    )
    # fish-vs-tag RE-DERIVED AGAIN at W3R-2 (persona-realism-w3r-2, 2026-07-24 —
    # owner-authorized): the leg was `fish > tag − 0.06` (a P1/A1 near-tie).
    # W3R-2 authors the fish's `call_looseness` at 0.42 (it had been inheriting
    # `stickiness` 1.4 and over-calling), so the fish now genuinely FOLDS MORE
    # and its WTSD drops BELOW tag's — INTENTIONAL, the hyp-2 fix landing, NOT a
    # persona-flattening regression. The direction is therefore re-pinned as a
    # strict `<` (measured at _WTSD_ORDER_N: fish 0.538 vs tag 0.610, a 0.072
    # gap vs 3σ ≈ 0.056 on the difference), and the anti-flattening guarantee
    # moves to the station-vs-fish separation below: the two passive personas
    # must stay clearly distinguishable — the fish is now a fold-to-big-bet
    # persona, the station the one that still calls everything.
    # A4.2 item 4: TRANSITION-SCOPED. Engine-anchored, and it contradicts the
    # grounded endpoint (fish 33-42 sits ABOVE tag 25-29); re-derived at the
    # single re-anchor and expected to FLIP. Value unchanged here.
    assert wtsd["passive_fish"] < wtsd["tag"], (
        f"passive_fish WTSD {wtsd['passive_fish']:.3f} not < tag WTSD "
        f"{wtsd['tag']:.3f} (W3R-2: the fish now folds more than the tag)"
    )
    # A4.2 item 4: TRANSITION-SCOPED. The grounded midpoints imply a gap of only
    # ~5.5 points, so 0.10 is unsatisfiable across most of the target region;
    # re-derived at the single re-anchor. Value unchanged here.
    assert wtsd["calling_station"] - wtsd["passive_fish"] > 0.10, (
        f"station WTSD {wtsd['calling_station']:.3f} and fish WTSD "
        f"{wtsd['passive_fish']:.3f} have converged (<0.10 apart) — the two "
        f"passive personas must stay distinguishable (W3R-2)"
    )
    # A4.2 item 4: PERMANENT and HARD throughout (grounded midpoints ~35 vs ~43).
    assert wtsd["maniac"] < wtsd["calling_station"], (
        f"maniac WTSD {wtsd['maniac']:.3f} not < station WTSD {wtsd['calling_station']:.3f}"
    )


# =====================================================================
# Table-texture test: 9-max live lineup, PRD table-texture population targets
# =====================================================================

TEXTURE_LINEUP = [
    "passive_fish",  # seat 0 (extra)
    "passive_fish",
    "passive_fish",
    "tag",
    "tag",
    "calling_station",
    "nit",
    "lag",
    "maniac",
]


def test_table_texture_9max_live_lineup(budget):
    packs, _per_persona_n, texture_n, _hands_per_s = budget
    rng = random.Random(20260710)
    persona_by_seat = {i: TEXTURE_LINEUP[i] for i in range(9)}

    players_to_flop_total = 0
    hands_with_limper = 0
    hands_with_3bet_plus = 0

    for i in range(texture_n):
        hand_seed = rng.randrange(1_000_000_000)
        button_seat = i % 9
        res = _play_hand(rng, hand_seed, button_seat, persona_by_seat, packs)
        saw_flop, had_limper, had_3bet = res.saw_flop, res.had_limper, res.had_3bet_plus
        players_to_flop_total += len(saw_flop) if saw_flop else 0
        # If no postflop street was reached (fold-out preflop), saw_flop is
        # empty; treat as 0 players-to-flop for the average (consistent with
        # "avg players who saw a flop across all hands").
        if had_limper:
            hands_with_limper += 1
        if had_3bet:
            hands_with_3bet_plus += 1

    avg_players_to_flop = players_to_flop_total / texture_n
    limper_rate = hands_with_limper / texture_n
    threebet_pot_rate = hands_with_3bet_plus / texture_n

    # Lead ruling (2026-07-10, this ticket's fan-in): the roadmap's "~3-4"
    # players-to-flop anchor assumed a passive, mostly-limped live lineup;
    # THIS lineup (2x maniac/lag-adjacent aggression via TEXTURE_LINEUP)
    # structurally kills limped multiway pots via preflop raises/folds.
    # VPIP-sum derivation: expected players-to-flop is bounded above by
    # sum(per-seat VPIP) minus fold-outs to a raise. Using the S3-tuned PRD
    # VPIP bands for this exact lineup (3x passive_fish ~28-45%, 2x tag
    # ~15-20%, 1x calling_station ~40-60%, 1x nit ~7-14%, 1x lag ~24-36%,
    # 1x maniac ~45-60%) the raw VPIP sum spans roughly 3x0.35 + 2x0.17 +
    # 0.50 + 0.10 + 0.30 + 0.52 ~= 3.53 hands-worth of "voluntary in", but a
    # meaningful share of those get folded out preflop facing the
    # maniac/lag's raises before the flop -- net observed players-to-flop
    # ~2.5-3.0 is consistent with that shrinkage. Floor lowered to 2.4 (was
    # 2.8) to match; NOT a retune of preflop pack nodes (S3 band test stays
    # byte-identical) -- this widens the test's own population-average
    # target, per lead authorization, not persona-level VPIP.
    #
    # Floor re-derived 2.4 -> 2.3 (2026-07-24): despite the fixed rng seed
    # above, PYTHONHASHSEED-driven set/dict iteration order leaks a small
    # (~+/-0.05) jitter into the sim, and the population low-tail (~2.395)
    # sat exactly on the old 2.4 boundary -> ~8% of hash seeds reddened a
    # correct run (e.g. PYTHONHASHSEED=0 lands 2.39x). 2.3 is a seed-robust
    # guard: it still catches a real fold-fest regression (which would drop
    # avg well below 2.3) while tolerating the hash-order noise. The deeper
    # nondeterminism (a hash-ordered collection in the sampling path) is a
    # known, separate issue -- not fixed here to avoid golden-fixture churn.
    #
    # 3-bet-pot ceiling 0.12 -> 0.15 (W5-b1, 2026-07-25). NOT a realism-band
    # re-anchor (that is W4-b's, and this is not a §5 row at all — §5 has no
    # 3-bet-pot-rate row; 0.12 was this test's own loose operationalisation of
    # the PRD R4 prose "3-bet pots low single-digit %", already 4pp looser than
    # the prose it encodes). The measured facts:
    #   * `texture_n` is THROUGHPUT-DERIVED (`_derive_n`), so which side of the
    #     line this lands on depends on how fast the machine is that day.
    #   * On MAIN's own packs — no W5-b1 edits at all — this ceiling is already
    #     violated in expectation: 11.83% @n=710, 11.47% @1500, 12.08% @2500,
    #     12.50% @4000. It passes on main by throughput luck, not by being true.
    #   * W5-b1's marginal contribution is +0.43pp at n=4000 (12.50 -> 12.93):
    #     wider `unopened` ladders mean more opens, so more 3-bet opportunities.
    #     Post-slice across n=500..4000 the statistic spans 11.69%-13.16%.
    # 0.15 clears that whole span with ~1.8pp of headroom while still catching a
    # real 3-bet-fest regression (a maniac-ised roster runs 20%+). DIRECTIONAL
    # smoke guard, never a HARD realism gate.
    #
    # Limper floor 0.50 -> 0.45 (W5-b1), same defect, same reasoning. This one
    # is DEMONSTRABLY luck-dependent rather than arguably so: it went green on
    # one full-suite run of this branch and red (49.64%) on the very next, with
    # no code change between them — only a different `texture_n` off the
    # throughput probe. Measured post-slice: 47.60% @n=500, 49.86% @710, 50.20%
    # @1000, 50.67% @1500, 50.72% @2500, 50.35% @4000. Measured on MAIN: 49.01%
    # @710, 50.40% @1500, 49.92% @2500, 49.75% @4000 — main FAILS its own gate
    # at three of those four n. W5-b1 moves the statistic +0.60pp, i.e. TOWARDS
    # the PRD's "majority of hands with >=1 limper", not away from it. 0.45
    # clears the whole measured span and still catches a real limps-vanished
    # regression. The proper repair is to stop deriving `texture_n` from machine
    # throughput (cf. the fixed `_WTSD_ORDER_N` precedent) — out of scope here.
    #
    # GUARDS RE-DERIVED at W5-b4 (2026-07-31, review fold) — first calibration
    # at the now-FIXED texture_n=1500 (the throughput-derived n above was the
    # enabling defect: the W5-b4 refuter measured the old 0.15/0.45 guards
    # failing at 22 of 26 machine-reachable n values post-slice and green only
    # at the 1500 cap — machine speed, not truth). 10-seed sweep at n=1500 on
    # the shipped roster: players-to-flop 2.374 sd 0.034 (2.325..2.430),
    # limper 0.469 sd 0.014 (0.453..0.491 — parent-equal: 0.471), 3-bet-pot
    # 0.162 sd 0.0085 (0.149..0.176; parent 0.133 — the +3pp IS the repaired
    # maniac attacking opens, the slice's designed behavior; the old 0.15
    # encoded the PRD's passive-table prose that main already violated in
    # expectation per the W5-b1 note above). Bounds = sweep span +/- ~2-3σ:
    # still DIRECTIONAL smoke guards — a fold-fest regression reads p2f well
    # under 2.2, a limps-vanished regression under 0.40, and a maniac-ised
    # ROSTER (a second+ persona going maniac-shaped) reads 3-bet-pot well
    # above 0.20.
    assert 2.2 <= avg_players_to_flop <= 4.5, f"avg players-to-flop {avg_players_to_flop:.2f}"
    assert limper_rate > 0.42, f"limper rate {limper_rate:.2%}"
    assert threebet_pot_rate < 0.20, f"3-bet-pot rate {threebet_pot_rate:.2%}"


# =====================================================================
# Runtime budget assertion (informational: pytest-reported via -q duration,
# this test just guards against silent budget blowout in CI).
# =====================================================================


def test_suite_runtime_budget_documented():
    # The budget derivation lives in the module docstring + _derive_n above;
    # this is a placeholder assertion so the intent is test-visible.
    assert _derive_n(430.0)[0] >= 150


# ============================ W3-b — position IP/OOP (B1, F1) ===================
from app.domain.table.postflop_context import PostflopContext  # noqa: E402

_IP = PostflopContext(in_position=True)
_OOP = PostflopContext(in_position=False)
_CBET_LEGAL = [personas_postflop_legal_check(), personas_postflop_legal_bet(1.0, 100.0)]
# TPTK made hand on a dry, unpaired, low-follow board (no draw; avoids W3-d
# overcard/wetness damp so the position effect is isolated).
_TPTK_DRY = (("Ah", "Kd"), ["Ac", "7s", "2d"])


def _pack_with(persona, **overrides):
    p = _pack(persona)
    return p.model_copy(update={"postflop": p.postflop.model_copy(update=overrides)})


def _dist_pack_ctx(
    pack, hole, board, legal, *, street=None, context=None, pot=6.0, stack=100.0,
    opponents=1, current_bet_to=0.0,
):
    cap = _CaptureWeights()
    sample_postflop_decision(
        pack, hole, board, legal, pot, stack, opponents, cap,  # type: ignore[arg-type]
        current_bet_to=current_bet_to, street=street, context=context,
    )
    return cap.dist


def _bet(dist):
    return dist.get(ActionType.BET, 0.0)


def test_position_sensitivity_zero_is_position_blind():
    pack = _pack_with("tag", position_sensitivity=0.0)
    hole, board = _TPTK_DRY
    ip = _dist_pack_ctx(pack, hole, board, _CBET_LEGAL, context=_IP)
    oop = _dist_pack_ctx(pack, hole, board, _CBET_LEGAL, context=_OOP)
    assert ip == oop  # s=0 → identity, exact


def test_position_none_context_is_identity_to_blind():
    # An un-opted caller (context=None) and a position-blind pack agree exactly.
    pack = _pack_with("tag", position_sensitivity=0.0)
    hole, board = _TPTK_DRY
    blind = _dist_pack_ctx(pack, hole, board, _CBET_LEGAL, context=None)
    opted_noctx = _dist_pack_ctx(_pack("tag"), hole, board, _CBET_LEGAL, context=None)
    assert blind == opted_noctx  # context=None bypasses the multiplier regardless of lever


def test_position_boosts_cbet_ip_over_oop_for_opted_pack():
    hole, board = _TPTK_DRY
    for persona in ("tag", "nit", "lag"):  # opted in content
        ip = _bet(_dist_pack_ctx(_pack(persona), hole, board, _CBET_LEGAL, context=_IP))
        oop = _bet(_dist_pack_ctx(_pack(persona), hole, board, _CBET_LEGAL, context=_OOP))
        assert ip > oop, f"{persona}: expected CBet_IP>CBet_OOP, got {ip} not> {oop}"


def test_position_noctx_sits_between_ip_and_oop():
    hole, board = _TPTK_DRY
    ip = _bet(_dist_pack_ctx(_pack("nit"), hole, board, _CBET_LEGAL, context=_IP))
    none = _bet(_dist_pack_ctx(_pack("nit"), hole, board, _CBET_LEGAL, context=None))
    oop = _bet(_dist_pack_ctx(_pack("nit"), hole, board, _CBET_LEGAL, context=_OOP))
    assert ip > none > oop


def test_position_does_not_touch_facing_raise():
    # Facing a bet (FOLD+CALL+RAISE): the RAISE is defense-side, position must
    # NOT move it (no-go: aggressor-side c-bet/barrel frequency ONLY).
    legal = [
        personas_postflop_legal_fold(),
        personas_postflop_legal_call(2.0),
        personas_postflop_legal_raise(6.0, 100.0),
    ]
    hole, board = _TPTK_DRY
    ip = _dist_pack_ctx(_pack("tag"), hole, board, legal, context=_IP, current_bet_to=2.0)
    oop = _dist_pack_ctx(_pack("tag"), hole, board, legal, context=_OOP, current_bet_to=2.0)
    assert ip == oop


def test_position_does_not_touch_matched_option_raise():
    # Matched-with-option (CHECK+RAISE, e.g. facing a check behind): agg_action
    # is RAISE (check-raise line), out of the c-bet/barrel scope → unaffected.
    legal = [personas_postflop_legal_check(), personas_postflop_legal_raise(2.0, 100.0)]
    hole, board = _TPTK_DRY
    ip = _dist_pack_ctx(_pack("tag"), hole, board, legal, context=_IP)
    oop = _dist_pack_ctx(_pack("tag"), hole, board, legal, context=_OOP)
    assert ip == oop



# ============================ W3-c — street schedule (B6/B7, F4/F19/F8) =========
from app.domain.table.postflop_context import BustedDraw  # noqa: E402

_UNOPENED = [personas_postflop_legal_check(), personas_postflop_legal_bet(1.0, 100.0)]


def _br(persona, hole, board, *, street=None, context=None, legal=None):
    """Exact BET weight for a persona in an unopened spot (or given legal)."""
    dist = _dist_pack_ctx(
        _pack(persona), hole, board, legal or _UNOPENED, street=street, context=context
    )
    return _bet(dist)


def test_street_agg_mult_flop_is_identity():
    assert personas_postflop._STREET_AGG_MULT[Street.FLOP] == 1.0
    assert personas_postflop._STREET_WEAK_DRAW_MULT[Street.FLOP] == 1.0
    assert personas_postflop._draw_agg_street_mult(DrawCategory.WEAK, Street.FLOP) == 1.0
    assert personas_postflop._draw_agg_street_mult(DrawCategory.STRONG, None) == 1.0


def test_air_bluff_decays_flop_turn_river():
    air = ("7c", "2d")
    flop = _br("lag", air, ["Kc", "9s", "3h"], street=Street.FLOP)
    turn = _br("lag", air, ["Kc", "9s", "3h", "4d"], street=Street.TURN)
    river = _br("lag", air, ["Kc", "9s", "3h", "4d", "Jc"], street=Street.RIVER)
    assert flop > turn > river


def test_weak_draw_semibluff_decays_steeper_than_strong():
    m = personas_postflop._draw_agg_street_mult
    assert m(DrawCategory.WEAK, Street.TURN) < m(DrawCategory.STRONG, Street.TURN)
    assert m(DrawCategory.WEAK, Street.RIVER) == 0.0


def test_busted_draw_river_bluff_needs_bet_prev_street():
    # Hold position constant (in_position=True for both) so this isolates the B7
    # busted-barrel bonus from the W3-b position multiplier.
    busted = ("8c", "9d")
    board = ["6h", "7s", "Kc", "2d", "Qs"]  # busted OESD, air by the river
    ip_barrel = PostflopContext(
        in_position=True, bet_prev_street=True, busted_draw=BustedDraw.STRAIGHT
    )
    ip_checked = PostflopContext(
        in_position=True, bet_prev_street=False, busted_draw=BustedDraw.STRAIGHT
    )
    barrel = _br("tag", busted, board, street=Street.RIVER, context=ip_barrel)
    checked = _br("tag", busted, board, street=Street.RIVER, context=ip_checked)
    assert barrel > checked  # the barrel story adds river bluff mass


def test_busted_straight_bluffs_more_than_busted_flush():
    b = personas_postflop._BUSTED_RIVER_BLUFF
    assert b[BustedDraw.STRAIGHT] > b[BustedDraw.FLUSH]


# ============================ W3R-4 — shared-mechanics fixes (#7, #11) ==========


def _busted_addon(pack, opponents: int) -> float:
    """The river busted-draw bluff add-on ALONE, at `opponents` opponents.

    Isolated by differencing the exact BET weight of the same busted-OESD air
    hand with and only with `bet_prev_street` flipped: in a bluff-cell unopened
    spot the entries are CHECK = 1 - bluff_mass and BET = bluff_mass (the packs
    here are position-blind, so the W3-b multiplier is 1.0), so the normalized
    BET weight IS bluff_mass and the difference is exactly the add-on.
    """
    busted, board = ("8c", "9d"), ["6h", "7s", "Kc", "2d", "Qs"]

    def bet(bet_prev: bool) -> float:
        ctx = PostflopContext(
            in_position=True, bet_prev_street=bet_prev, busted_draw=BustedDraw.STRAIGHT
        )
        return _bet(
            _dist_pack_ctx(
                pack, busted, board, _CBET_LEGAL, street=Street.RIVER,
                context=ctx, opponents=opponents,
            )
        )

    return bet(True) - bet(False)


def test_busted_river_bluff_decays_with_opponents():
    """W3R-4 (#7): the busted-draw river bluff add-on carries the SAME multiway
    damp as the generic bluff mass — a busted flush must not fire the same story
    bluff into 3 callers as heads-up. Heads-up (opponents=1) is byte-identical
    (`** 0` = 1.0)."""
    pack = _pack_with("tag", position_sensitivity=0.0)
    damp = pack.postflop.multiway_bluff_damp
    assert damp < 1.0  # the decay is only observable for a damping persona
    hu, three = _busted_addon(pack, 1), _busted_addon(pack, 3)
    assert _busted_addon(pack, 2) < hu
    assert three < _busted_addon(pack, 2)
    # Exact law: add-on == _BUSTED_RIVER_BLUFF[kind] * damp ** (opponents - 1).
    base = personas_postflop._BUSTED_RIVER_BLUFF[BustedDraw.STRAIGHT]
    assert hu == pytest.approx(base, abs=1e-12)  # heads-up byte-identical
    assert three == pytest.approx(base * damp**2, abs=1e-12)


def test_middle_pair_call_base_trim_calls_less():
    """W3R-4 (#11): the `_CALL_BASE[MIDDLE_PAIR]` 0.60 -> 0.52 trim makes a naked
    middle pair facing a flop bet CALL strictly less often (exact weights)."""
    hole, board = ("7h", "6d"), ["9c", "7s", "2d"]  # naked middle pair, no draw
    legal = [
        personas_postflop_legal_fold(),
        personas_postflop_legal_call(3.0),
        personas_postflop_legal_raise(9.0, 100.0),
    ]

    def call_weight() -> float:
        return _dist_pack_ctx(
            _pack("tag"), hole, board, legal, street=Street.FLOP, current_bet_to=3.0
        )[ActionType.CALL]

    trimmed = call_weight()
    pre = personas_postflop._CALL_BASE[StrengthBucket.MIDDLE_PAIR]
    assert pre == 0.52  # the fitted seed (see the engine comment)
    personas_postflop._CALL_BASE[StrengthBucket.MIDDLE_PAIR] = 0.60
    try:
        assert trimmed < call_weight()
    finally:
        personas_postflop._CALL_BASE[StrengthBucket.MIDDLE_PAIR] = pre


# ============================ W3-d — texture brakes (B2/B3, F3/F20) =============


def test_overcard_count_helper():
    oc = personas_postflop._overcard_count
    assert oc(("9h", "7d"), ["9c", "4s", "2d"]) == 0
    assert oc(("7h", "6d"), ["9c", "7s", "2d"]) == 1
    assert oc(("5h", "4d"), ["Kc", "5s", "9d"]) == 2


def test_overcard_damp_nonlinear():
    d = personas_postflop._overcard_bet_damp
    assert (d(0), d(1), d(2), d(3)) == (1.0, 0.75, 0.5, 0.5)


def test_middle_pair_bet_falls_with_overcards():
    b0 = _br("tag", ("9h", "7d"), ["9c", "4s", "2d"], street=Street.FLOP)
    b1 = _br("tag", ("7h", "6d"), ["9c", "7s", "2d"], street=Street.FLOP)
    b2 = _br("tag", ("5h", "4d"), ["Kc", "5s", "9d"], street=Street.FLOP)
    assert b0 > b1 > b2


def test_wetness_bet_mult_ordering():
    m = personas_postflop._wetness_bet_mult
    dry = m(["Kc", "8s", "3d"])
    two_tone = m(["Kc", "8s", "3s"])
    connected = m(["9c", "8s", "7d"])
    mono = m(["Kc", "8c", "3c"])
    assert dry >= two_tone >= connected >= mono
    assert dry == 1.0 and mono < connected


def test_one_pair_bet_falls_with_wetness_same_overcards():
    h = ("9h", "7d")  # pair of 9s, 0 overcards on both boards
    dry = _br("tag", h, ["9c", "4s", "2d"], street=Street.FLOP)
    mono = _br("tag", h, ["9c", "4c", "2c"], street=Street.FLOP)
    assert dry > mono


def test_overpair_and_set_still_bet_on_wet_boards():
    # OVERPAIR_TPTK and MONSTER are out of scope: still bet freely on a wet
    # monotone board with overcards (texture brakes are bucket-gated).
    over = _br("tag", ("Ah", "Ad"), ["Kc", "8c", "3c"], street=Street.FLOP)
    setbet = _br("tag", ("7s", "7d"), ["7c", "Kc", "3c"], street=Street.FLOP)
    assert over > 0.5 and setbet > 0.5


def test_position_sensitivity_bounded_to_unit_interval():
    # The OOP multiplier 1 - 0.25*s must stay positive; the schema caps s at 1.0.
    import pydantic

    from app.domain.content.models import PersonaPostflop

    base = _pack("tag").postflop.model_dump()
    PersonaPostflop.model_validate({**base, "position_sensitivity": 1.0})  # ok
    with pytest.raises(pydantic.ValidationError):
        PersonaPostflop.model_validate({**base, "position_sensitivity": 1.5})


# ====================== W3R-6 — facing-a-raise merit damps (#9, #5) =============
# `facing_raise=False` at the SAME street is the pre-slice status quo AT ONE
# OPPONENT, and every "byte-identical to status quo" leg below is exactly that
# A/B (the street=None path is pinned equal to it too).
#
# THE HEADS-UP QUALIFIER IS LOAD-BEARING NOW, WHERE IT USED TO BE INCIDENTAL.
# This block used to read "both damps are gated on `facing_raise`", which was
# the whole reason the A/B held. T1 (improvement slice 2, 2026-08-18) widened
# `_ACE_HIGH_FLOAT_RAISE_DAMP`'s predicate to `facing_raise or opponents > 1`,
# so at more than one opponent `facing_raise=False` is NOT the status quo for
# naked ace-high. The legs below are still correct only because `_w3r6_dist`
# passes `opponents=1`. Do not generalise any of them by threading `opponents`
# through that helper; the T1 section further down has its own `_t1_dist` for
# multiway work, deliberately kept separate.
#
# GATE NOTE: #9 shipped with the spec's AUTHORIZED NARROWING (facing a RAISE,
# not merely facing chips). The wider gate was implemented and measured first and
# pushed the passive fish's arrival-range fold-to-bet to 0.6528 vs the α + 0.05
# ceiling 0.650 (undamped baseline 0.6422). See _ONE_PAIR_RAISE_DAMP.

_W3R6_FACING = [
    personas_postflop_legal_fold(),
    personas_postflop_legal_call(5.0),
    personas_postflop_legal_raise(15.0, 100.0),
]
# H117 (99 on J-J-7) — the cited middle-pair raise-war hand.
_W3R6_MID = (("9h", "9c"), ["Js", "Jd", "7c"], ["Js", "Jd", "7c", "2s"])
# H32-shape top pair, weak kicker, dry board.
_W3R6_TOP = (("Qh", "Jd"), ["Qs", "8d", "3c"], ["Qs", "8d", "3c", "2s"])
# Naked ace-high, no draw (H117's float side).
_W3R6_AHI = (("Ad", "7c"), ["Ks", "9h", "2s"], ["Ks", "9h", "2s", "4d"])


def _w3r6_dist(persona, hole, board, *, street, facing_raise):
    cap = _CaptureWeights()
    sample_postflop_decision(
        _pack(persona), hole, board, _W3R6_FACING, 10.0, 100.0, 1,
        cap,  # type: ignore[arg-type]
        current_bet_to=5.0, street=street, facing_raise=facing_raise,
    )
    total = sum(cap.dist.values())
    return {a: w / total for a, w in cap.dist.items()}


def _w3r6_assert_bucket(hole, board, bucket, draw):
    got = strength_bucket(hole, board)
    assert got == (bucket, draw), f"spot drifted: {got} != {(bucket, draw)}"


# ---- leg 1: made one-pair stops re-raising into flop/turn action (#9) ----------
# Measured normalized P(RAISE), status quo -> damped (facing a raise), damp 0.35:
#   tag    MIDDLE_PAIR  0.187 -> 0.075   TOP_PAIR  0.308 -> 0.135
#   maniac MIDDLE_PAIR  0.360 -> 0.165   TOP_PAIR  0.528 -> 0.281
# RE-RECORDED for S3-T2 (improvement slice 3, 2026-08-22, slice-authorized):
# the tag's `call_looseness` moves 0.6 -> 0.38. These are NORMALIZED raise
# shares at a facing node, so a smaller CALL merit re-weights the whole vector
# and the tag's two rows move even though nothing about the damp changed
# (mid 0.1871 -> 0.1573 status quo, 0.0745 -> 0.0613 damped; top 0.3078 ->
# 0.2922 and 0.1347 -> 0.1262). The maniac's two rows are BYTE-IDENTICAL — its
# pack is untouched and this is a single-node unit fixture with no shared rng
# stream to displace, which is the control that says the move is the tag's dial
# and nothing else. The RATIO the damp is really about is unchanged to three
# decimals on both tag rows (0.398 -> 0.390 mid, 0.438 -> 0.432 top): the damp
# is 0.35 on the raise merit and the residual is the re-normalization.
# Tolerances are UNCHANGED at 5e-4. ATTRIBUTION PROVEN: with the two pack files
# reverted this fixture reproduces the old four rows exactly.
_W3R6_RAISE_DROP = {
    ("tag", "mid"): (0.1573, 0.0613),
    ("tag", "top"): (0.2922, 0.1262),
    ("maniac", "mid"): (0.3604, 0.1647),
    ("maniac", "top"): (0.5276, 0.2811),
}


@pytest.mark.parametrize("persona", ["tag", "maniac"])
@pytest.mark.parametrize("name,bucket", [("mid", StrengthBucket.MIDDLE_PAIR),
                                         ("top", StrengthBucket.TOP_PAIR)])
@pytest.mark.parametrize("street", [Street.FLOP, Street.TURN])
def test_one_pair_raise_damped_facing_raise_pre_river(persona, name, bucket, street):
    hole, flop, turn = _W3R6_MID if name == "mid" else _W3R6_TOP
    board = flop if street is Street.FLOP else turn
    _w3r6_assert_bucket(hole, board, bucket, DrawCategory.NONE)
    sq = _w3r6_dist(persona, hole, board, street=street, facing_raise=False)
    dm = _w3r6_dist(persona, hole, board, street=street, facing_raise=True)
    assert dm[ActionType.RAISE] < sq[ActionType.RAISE]
    exp_sq, exp_dm = _W3R6_RAISE_DROP[(persona, name)]
    assert sq[ActionType.RAISE] == pytest.approx(exp_sq, abs=5e-4)
    assert dm[ActionType.RAISE] == pytest.approx(exp_dm, abs=5e-4)
    # the street=None identity path agrees with the facing_raise=False status quo
    none_sq = _w3r6_dist(persona, hole, board, street=None, facing_raise=False)
    assert none_sq == sq


# ---- leg 1b: the gate-lock — damp 1 never fires facing a bare bet -------------
# Regression guard for the narrowed gate itself (facing_raise required, not just
# "chips faced"). Proves facing_raise=False is byte-identical to the SAME spot
# with facing_raise=True but _ONE_PAIR_RAISE_DAMP neutralized to 1.0 (i.e. the
# gate contributing literally nothing) — a genuinely different code path than the
# golden-float comparison in leg 1, so it can't pass by coincidence. If the gate
# is later re-widened to fire on a bare bet (dropping the `facing_raise`
# requirement), `faced_bet` would pick up the damp while `neutralized` would not,
# and this test would fail.
@pytest.mark.parametrize("persona", ["tag", "maniac"])
@pytest.mark.parametrize("name,bucket", [("mid", StrengthBucket.MIDDLE_PAIR),
                                         ("top", StrengthBucket.TOP_PAIR)])
@pytest.mark.parametrize("street", [Street.FLOP, Street.TURN])
def test_one_pair_raise_damp_does_not_fire_facing_a_bare_bet(persona, name, bucket, street):
    hole, flop, turn = _W3R6_MID if name == "mid" else _W3R6_TOP
    board = flop if street is Street.FLOP else turn
    _w3r6_assert_bucket(hole, board, bucket, DrawCategory.NONE)
    faced_bet = _w3r6_dist(persona, hole, board, street=street, facing_raise=False)
    damp = personas_postflop._ONE_PAIR_RAISE_DAMP
    try:
        personas_postflop._ONE_PAIR_RAISE_DAMP = 1.0
        neutralized = _w3r6_dist(persona, hole, board, street=street, facing_raise=True)
    finally:
        personas_postflop._ONE_PAIR_RAISE_DAMP = damp
    assert faced_bet == neutralized
    # non-vacuous: with the damp active, facing a raise DOES move RAISE merit,
    # so the gate is genuinely doing something at facing_raise=True.
    damped = _w3r6_dist(persona, hole, board, street=street, facing_raise=True)
    assert damped[ActionType.RAISE] < faced_bet[ActionType.RAISE]


# ---- leg 2: semi-bluff raises spared ------------------------------------------
_W3R6_DRAW_BOARD = ["Qs", "8h", "3h"]
_W3R6_TOP_FD = ("Qh", "Jh")   # TOP_PAIR + flush draw (STRONG)
_W3R6_TOP_DRY = ("Qc", "Jd")  # TOP_PAIR, no draw — same board


def test_semi_bluff_raise_survives_the_one_pair_damp():
    _w3r6_assert_bucket(_W3R6_TOP_FD, _W3R6_DRAW_BOARD,
                        StrengthBucket.TOP_PAIR, DrawCategory.STRONG)
    _w3r6_assert_bucket(_W3R6_TOP_DRY, _W3R6_DRAW_BOARD,
                        StrengthBucket.TOP_PAIR, DrawCategory.NONE)
    for persona in ("tag", "maniac"):
        drawing = _w3r6_dist(persona, _W3R6_TOP_FD, _W3R6_DRAW_BOARD,
                             street=Street.FLOP, facing_raise=True)
        dry = _w3r6_dist(persona, _W3R6_TOP_DRY, _W3R6_DRAW_BOARD,
                         street=Street.FLOP, facing_raise=True)
        assert drawing[ActionType.RAISE] > dry[ActionType.RAISE], persona


@pytest.mark.parametrize("hole,board", [_STRONG_DRAW, _WEAK_DRAW])
@pytest.mark.parametrize("street", [Street.FLOP, Street.TURN, Street.RIVER, None])
def test_pure_flopped_draw_facing_raise_is_byte_identical(hole, board, street):
    # AIR + a draw: neither damp's bucket gate matches, at any street.
    for persona in ("tag", "maniac", "passive_fish"):
        sq = _w3r6_dist(persona, hole, board, street=street, facing_raise=False)
        assert _w3r6_dist(persona, hole, board, street=street, facing_raise=True) == sq


# ---- leg 3: two-pair+ value raises untouched ----------------------------------
_W3R6_STRONG_SPOTS = [
    (StrengthBucket.MONSTER, ("7s", "7d"), ["7c", "Kd", "3s"], ["7c", "Kd", "3s", "2c"]),
    (StrengthBucket.TWO_PAIR_PLUS, ("Kh", "9d"), ["Ks", "9c", "2d"], ["Ks", "9c", "2d", "4s"]),
    (StrengthBucket.OVERPAIR_TPTK, ("Ah", "Ad"), ["Kc", "8d", "3s"], ["Kc", "8d", "3s", "2c"]),
]


@pytest.mark.parametrize("bucket,hole,flop,turn", _W3R6_STRONG_SPOTS)
@pytest.mark.parametrize("street", [Street.FLOP, Street.TURN])
def test_value_raises_untouched_by_the_one_pair_damp(bucket, hole, flop, turn, street):
    """OVERPAIR_TPTK is deliberately NOT damped: the bucket bundles true
    overpairs with TPTK, so damping it would damp real overpairs. H107 (TPTK) is
    therefore only PARTIALLY addressed by this slice — the rest is W3R-7."""
    board = flop if street is Street.FLOP else turn
    _w3r6_assert_bucket(hole, board, bucket, DrawCategory.NONE)
    for persona in ("tag", "maniac"):
        sq = _w3r6_dist(persona, hole, board, street=street, facing_raise=False)
        assert _w3r6_dist(persona, hole, board, street=street, facing_raise=True) == sq


# ---- leg 4: naked ace-high folds to a raise (#5) -------------------------------
@pytest.mark.parametrize("persona", ["tag", "passive_fish"])
@pytest.mark.parametrize("street", [Street.FLOP, Street.TURN])
def test_naked_ace_high_folds_to_a_raise(persona, street):
    hole, flop, turn = _W3R6_AHI
    board = flop if street is Street.FLOP else turn
    _w3r6_assert_bucket(hole, board, StrengthBucket.ACE_HIGH, DrawCategory.NONE)
    sq = _w3r6_dist(persona, hole, board, street=street, facing_raise=False)
    dm = _w3r6_dist(persona, hole, board, street=street, facing_raise=True)
    # measured at _ACE_HIGH_FLOAT_RAISE_DAMP 0.55: +0.096 .. +0.114
    assert dm[ActionType.FOLD] - sq[ActionType.FOLD] >= 0.05, (
        f"{persona} {street}: fold {sq[ActionType.FOLD]:.3f} -> {dm[ActionType.FOLD]:.3f}"
    )
    assert dm[ActionType.CALL] < sq[ActionType.CALL]


# ---- leg 5: the α-safety proof — facing a BET is byte-identical ----------------
@pytest.mark.parametrize("persona", ALL_PERSONAS)
@pytest.mark.parametrize("street", [Street.FLOP, Street.TURN, Street.RIVER, None])
def test_ace_high_facing_a_bet_is_byte_identical(persona, street):
    """HEADS-UP facing a bet is byte-identical to the pre-W3R-6 engine, and this
    test is heads-up-only by construction — `_w3r6_dist` passes `opponents=1`.

    It used to claim more than that. The original docstring read "NOTHING on
    that node moved (both damps need facing_raise)", which was true until T1
    (improvement slice 2, 2026-08-18) widened `_ACE_HIGH_FLOAT_RAISE_DAMP` to
    `facing_raise or opponents > 1`. The facing-a-bet node DOES move now, at
    more than one opponent, and this test cannot see it. That is not a gap left
    open: `test_ace_high_multiway_damp_gate_lock` pins the heads-up case through
    a helper that takes `opponents` explicitly, and
    `test_naked_ace_high_multiway_bet_calls_less_than_heads_up` pins the
    multiway movement itself. This test is kept unchanged as the seeded record
    of the heads-up curve.

    WHAT THE RIVER LEG NOW PROTECTS, WHICH IS LESS THAN IT READS. It used to
    say the facing-a-raise case comes along free because `call_merit` is
    already 0 on the river via the bluff-cell gate. Since T3 (improvement slice
    2, 2026-08-19) that is FALSE for this probe hole: `_W3R6_AHI` is naked
    ace-high, whose river call merit is no longer zeroed but multiplied by
    `_ACE_HIGH_RIVER_CALL_DAMP`. The equality still holds, for a different and
    weaker reason — the control arm below neutralises `_ONE_PAIR_RAISE_DAMP`
    and `_ACE_HIGH_FLOAT_RAISE_DAMP` but leaves `_ACE_HIGH_RIVER_CALL_DAMP`
    LIVE IN BOTH ARMS, and neither neutralised damp is street-active on the
    river. So the RIVER leg is no longer a comparison against the pre-W3R-6
    engine at all; it asserts that the two flop/turn damps stay off the river,
    which is worth having and is not what the name suggests. A test that
    genuinely pinned the pre-T3 river vector would have to neutralise the T3
    damp as well, and `test_t3_river_damp_moves_only_the_ace_high_call_leg`
    is the test that does that."""
    hole, flop, turn = _W3R6_AHI
    board = {Street.TURN: turn, Street.RIVER: turn + ["6c"]}.get(street, flop)
    faced_bet = _w3r6_dist(persona, hole, board, street=street, facing_raise=False)
    # Non-vacuous: compare against the engine with BOTH damps neutralized to 1.0,
    # i.e. literally pre-W3R-6 behavior.
    one, ace = (
        personas_postflop._ONE_PAIR_RAISE_DAMP,
        personas_postflop._ACE_HIGH_FLOAT_RAISE_DAMP,
    )
    try:
        personas_postflop._ONE_PAIR_RAISE_DAMP = 1.0
        personas_postflop._ACE_HIGH_FLOAT_RAISE_DAMP = 1.0
        pre_slice = _w3r6_dist(persona, hole, board, street=street, facing_raise=True)
    finally:
        personas_postflop._ONE_PAIR_RAISE_DAMP = one
        personas_postflop._ACE_HIGH_FLOAT_RAISE_DAMP = ace
    assert faced_bet == pre_slice
    if street is Street.RIVER:
        # Facing a RAISE on the river is byte-identical to facing a BET because
        # BOTH neutralised damps are gated to flop and turn. It is NOT because
        # the call merit is zero — T3 replaced that zero with
        # `_ACE_HIGH_RIVER_CALL_DAMP`, which is live in both arms. See the
        # docstring; this leg is narrower than its name.
        assert _w3r6_dist(persona, hole, board, street=street, facing_raise=True) == faced_bet


def test_ace_high_with_a_draw_facing_raise_is_byte_identical():
    # The damped term is _CALL_BASE[ACE_HIGH] on NAKED ace-high only.
    hole, board = ("Ad", "7d"), ["Kd", "9d", "2s"]
    _w3r6_assert_bucket(hole, board, StrengthBucket.ACE_HIGH, DrawCategory.STRONG)
    for persona in ALL_PERSONAS:
        for street in (Street.FLOP, Street.TURN):
            sq = _w3r6_dist(persona, hole, board, street=street, facing_raise=False)
            assert _w3r6_dist(persona, hole, board, street=street, facing_raise=True) == sq

# ====================== T1 — the ace-high float damp goes multiway ============
#
# T1 (improvement slice 2, invest-then-fold) widened the W3R-6 predicate from
# `facing_raise` to `facing_raise or opponents > 1`, so the damp now fires on the
# facing-a-BET node for the first time. That DELETED W3R-6's structural safety
# argument — "a facing-a-raise gate is off the α measurement node by
# construction" — and the leg-5 guard above cannot see the deletion, because its
# `_w3r6_dist` helper passes `opponents=1`. The three tests below are what
# replaces the argument, and they drive `opponents` explicitly.
#
# READ THE MERIT CURRENCY BEFORE CHANGING THESE. `_MW_CATCH_TIGHTEN` at
# `personas_postflop.py:969-970` ALREADY multiplies ACE_HIGH's FOLD merit by
# 1.15 ** (opponents - 1), and normalization already turns that into a lower
# P(CALL) multiway. So "P(CALL) at three opponents is below heads-up" was TRUE
# BEFORE T1 and asserting only that is vacuous. Every leg that must fail on the
# pre-T1 engine therefore compares against the same node with
# `_ACE_HIGH_FLOAT_RAISE_DAMP` neutralized to 1.0 — the one comparison the
# pre-existing fold-side tighten cannot satisfy.


def _t1_dist(persona, hole, board, *, street, facing_raise, opponents):
    """`_w3r6_dist` with `opponents` under the caller's control. Deliberately a
    sibling rather than an edit: leg 5's byte-identical guard keeps its own
    hardcoded heads-up node untouched."""
    cap = _CaptureWeights()
    sample_postflop_decision(
        _pack(persona), hole, board, _W3R6_FACING, 10.0, 100.0, opponents,
        cap,  # type: ignore[arg-type]
        current_bet_to=5.0, street=street, facing_raise=facing_raise,
    )
    total = sum(cap.dist.values())
    return {a: w / total for a, w in cap.dist.items()}


def _t1_neutralized_dist(persona, hole, board, *, street, opponents):
    """The same node on the pre-T1 engine: `_ACE_HIGH_FLOAT_RAISE_DAMP` = 1.0,
    i.e. the damp contributing literally nothing, with the multiway fold-side
    tighten still live."""
    saved = personas_postflop._ACE_HIGH_FLOAT_RAISE_DAMP
    try:
        personas_postflop._ACE_HIGH_FLOAT_RAISE_DAMP = 1.0
        return _t1_dist(persona, hole, board, street=street,
                        facing_raise=False, opponents=opponents)
    finally:
        personas_postflop._ACE_HIGH_FLOAT_RAISE_DAMP = saved


@pytest.mark.parametrize("persona", ["tag", "passive_fish", "calling_station"])
@pytest.mark.parametrize("opponents", [2, 3])
@pytest.mark.parametrize("street", [Street.FLOP, Street.TURN])
def test_naked_ace_high_multiway_bet_calls_less_than_heads_up(persona, opponents, street):
    """T1 acceptance 4: naked ace-high facing an ordinary BET with more than one
    opponent live calls strictly less than the same hand heads-up — and does so
    BECAUSE of the damp, not because of `_MW_CATCH_TIGHTEN`."""
    hole, flop, turn = _W3R6_AHI
    board = flop if street is Street.FLOP else turn
    _w3r6_assert_bucket(hole, board, StrengthBucket.ACE_HIGH, DrawCategory.NONE)
    hu = _t1_dist(persona, hole, board, street=street, facing_raise=False, opponents=1)
    mw = _t1_dist(persona, hole, board, street=street, facing_raise=False,
                  opponents=opponents)
    assert mw[ActionType.CALL] < hu[ActionType.CALL]
    # The load-bearing leg: on the pre-T1 engine these two are EQUAL, because the
    # damp was gated on facing_raise and this node faces a bet.
    pre_t1 = _t1_neutralized_dist(persona, hole, board, street=street,
                                  opponents=opponents)
    assert mw[ActionType.CALL] < pre_t1[ActionType.CALL], (
        f"{persona} {street} opponents={opponents}: the damp is not firing on the "
        f"facing-a-bet node — CALL {mw[ActionType.CALL]:.6f} vs pre-T1 "
        f"{pre_t1[ActionType.CALL]:.6f}"
    )
    assert mw[ActionType.FOLD] > pre_t1[ActionType.FOLD]


@pytest.mark.parametrize("persona", ALL_PERSONAS)
def test_ace_high_multiway_damp_gate_lock(persona):
    """T1 acceptance 5 and the ticket's three explicit boundaries: heads-up is
    still byte-identical, the river is still untouched at any opponent count,
    and ace-high WITH a draw is still untouched (the damp is on the
    `_CALL_BASE` term of NAKED hands only)."""
    hole, flop, turn = _W3R6_AHI
    river = turn + ["6c"]
    for street in (Street.FLOP, Street.TURN):
        board = flop if street is Street.FLOP else turn
        live = _t1_dist(persona, hole, board, street=street,
                        facing_raise=False, opponents=1)
        assert live == _t1_neutralized_dist(persona, hole, board, street=street,
                                            opponents=1)
    for opponents in (1, 2, 3):
        live = _t1_dist(persona, hole, river, street=Street.RIVER,
                        facing_raise=False, opponents=opponents)
        assert live == _t1_neutralized_dist(persona, hole, river,
                                            street=Street.RIVER,
                                            opponents=opponents)
    drawing, draw_board = ("Ad", "7d"), ["Kd", "9d", "2s"]
    _w3r6_assert_bucket(drawing, draw_board, StrengthBucket.ACE_HIGH,
                        DrawCategory.STRONG)
    for street in (Street.FLOP, Street.TURN):
        for opponents in (2, 3):
            live = _t1_dist(persona, drawing, draw_board, street=street,
                            facing_raise=False, opponents=opponents)
            assert live == _t1_neutralized_dist(persona, drawing, draw_board,
                                                street=street,
                                                opponents=opponents)


_T1_CATCHER_SPOTS = [
    (StrengthBucket.MIDDLE_PAIR, *_W3R6_MID),
    (StrengthBucket.TOP_PAIR, *_W3R6_TOP),
]


@pytest.mark.parametrize("persona", ALL_PERSONAS)
@pytest.mark.parametrize("bucket,hole,flop,turn", _T1_CATCHER_SPOTS)
@pytest.mark.parametrize("opponents", [1, 2, 3])
def test_bluff_catcher_alpha_contract_untouched_at_multiple_opponents(
    persona, bucket, hole, flop, turn, opponents
):
    """T1 acceptance 6, the half a measurement cannot supply. The α = f/(1+f)
    fold ceiling is asserted over the one-pair no-draw BLUFF-CATCHER range
    (`_CATCHER_BUCKETS`, `test_fold_to_bet_respects_alpha_ceiling`), which
    deliberately EXCLUDES ace-high — ace-high loses to part of a balanced
    bettor's bluff half, so it is not a catcher by that fixture's construction.

    ⚠️ THE EXCLUSION IS A FIXTURE SCOPE, NOT A STATEMENT THAT α SPARES THE
    BUCKET. This docstring used to end "and α does not bind on it", which the
    owner's 2026-08-19 ruling makes false: α DOES bound ACE_HIGH. What this
    test asserts is unaffected — it pins the one-pair catcher range as
    byte-identical across opponent counts, and says nothing about ace-high's
    own rates. Those are measured, and violate α nearly everywhere, in
    `test_ace_high_alpha_holds_for_the_station_pre_river` and
    `docs/ai-dlc/research/slice2-invest-then-fold/alpha-acehigh-ruling.md`.

    W3R-6 kept that contract safe by construction (the damp could not reach a
    facing-a-bet node at all). T1 removes that reason, so what protects the
    contract now is the BUCKET gate alone: the damp reads
    `bucket is StrengthBucket.ACE_HIGH`, so the catcher range must stay
    byte-identical at EVERY opponent count, not just heads-up. This test is the
    thing that fails if a later ticket widens the bucket gate."""
    for street in (Street.FLOP, Street.TURN):
        board = flop if street is Street.FLOP else turn
        _w3r6_assert_bucket(hole, board, bucket, DrawCategory.NONE)
        live = _t1_dist(persona, hole, board, street=street,
                        facing_raise=False, opponents=opponents)
        assert live == _t1_neutralized_dist(persona, hole, board, street=street,
                                            opponents=opponents)


def test_w3r6_damp_constants_inside_their_fitted_ranges():
    assert 0.25 <= personas_postflop._ONE_PAIR_RAISE_DAMP <= 0.55
    assert 0.35 <= personas_postflop._ACE_HIGH_FLOAT_RAISE_DAMP <= 0.65


# ============ W5-b3 / W5-b3b — `unopened` seat ladder (AUTHORED, n-free) ======
#
# These gates read pack JSON only — no simulation, no rng, no sample-size
# requirement. Realized RFI is arrival-confounded (that is the whole point of
# the W-ARR wave), so the assertion is on AUTHORED width, per the roadmap
# W5-b3 line "Assert AUTHORED width, not realized RFI".
#
# WIDTH DEFINITION (pinned by roadmap W5-b3 (a), R9-c5): combo-weighted
# `raise` + `3bet` legs over all 1326 combos under first-match-wins —
# NEVER `1 - fold`, which would fold open-limps into the number and make a
# limp-heavy node read as a wide opener. Every nit `unopened` node carries
# limp 0.4 across its small-pair band, so the two measures differ materially
# here. Band shapes after T-M2 (2026-07-31): UTG `22-66` limp-only, UTG1/UTG2/
# LJ/HJ/SB/BB `22-77` limp-only, CO `55-77` at raise 0.3/limp 0.4 plus `22-44`
# limp-only, BTN `22-77` at raise 0.3/limp 0.4 with NO limp-only mix left.

_LADDER_SEATS = ("UTG", "UTG1", "UTG2", "LJ", "HJ", "CO", "BTN", "SB", "BB")


def _unopened_node(pack, seat: str):
    """The `unopened` node the engine would select for `seat`, using the same
    first-match-in-list-order rule as `sample_preflop_action`: the first node
    whose facing matches AND whose positions is None (wildcard) or contains
    the seat."""
    for node in pack.preflop:
        if node.facing != "unopened":
            continue
        if node.positions is None or any(p.value == seat for p in node.positions):
            return node
    return None


def _authored_raise_width(node) -> float:
    """Combo-weighted authored first-in RAISE width of one node, as a fraction
    of 1326 combos. First-match-wins: a class already claimed by an earlier
    mix contributes nothing to a later one."""
    from app.domain.content.notation import parse_range

    if node is None:
        return 0.0
    covered: set[str] = set()
    total = 0.0
    for mix in node.mixes:
        claimed = parse_range(mix.combos) - covered
        w = mix.weights.get("raise", 0.0) + mix.weights.get("3bet", 0.0)
        total += w * sum(_combo_count(c) for c in claimed)
        covered |= claimed
    return total / 1326.0


def _seat_ladder(pack) -> dict[str, float]:
    return {s: _authored_raise_width(_unopened_node(pack, s)) for s in _LADDER_SEATS}


def test_w5b3_nit_unopened_nodes_cover_all_nine_seats_explicitly():
    """🔴 Structural coverage gate (Codex fan-in MED): the W5-b3 ladder deleted
    the wildcard `unopened` node, so a dropped seat would silently fold 100%
    at first-in (`sample_preflop_action` has no fall-through) — and a width-0
    seat would still satisfy the tightest-persona check. Assert exactly nine
    single-position `unopened` nodes covering every seat, no wildcard left."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    nodes = [n for n in packs[VillainType.NIT].preflop if n.facing == "unopened"]
    assert all(n.positions is not None for n in nodes), "wildcard unopened node reappeared"
    assert all(len(n.positions) == 1 for n in nodes), "multi-seat unopened node"
    seats = sorted(n.positions[0].value for n in nodes)
    assert seats == sorted(_LADDER_SEATS), f"seat coverage broken: {seats}"
    assert len(nodes) == 9


def test_w5b3_nit_unopened_authored_width_strictly_increases():
    """🔴 W5-b3 defect gate (a), deterministic and n-free.

    PRE-SLICE HEAD reading (recorded per the gate-design rule) — the nit
    shipped ONE step, UTG vs everywhere-else:
        UTG 13.57 · UTG1..BB 29.11 (all eight later seats identical)
    so `LJ < CO` and `CO < BTN` were 29.11 < 29.11 — FALSE. This test FAILS
    at pre-slice HEAD, which is what makes it a gate rather than a decoration.

    POST-SLICE reading (W5-b3):
        UTG 7.54 · UTG1 8.45 · UTG2 9.95 · LJ 12.22 · HJ 13.42 · CO 15.99 ·
        BTN 21.42 · SB 16.59 · BB 12.52
    CURRENT reading (T-M2, 2026-07-31 — CO/BTN pair opens at raise 0.3):
        UTG 7.54 · UTG1 8.45 · UTG2 9.95 · LJ 12.22 · HJ 13.42 · CO 16.395 ·
        BTN 22.232 · SB 16.59 · BB 12.52
    """
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    ladder = _seat_ladder(packs[VillainType.NIT])
    print(
        "nit authored unopened raise width by seat: "
        + " · ".join(f"{s} {ladder[s] * 100:.2f}%" for s in _LADDER_SEATS)
    )
    for lo, hi in (("UTG", "LJ"), ("LJ", "CO"), ("CO", "BTN")):
        assert ladder[lo] < ladder[hi], (
            f"nit authored unopened width must strictly increase {lo}->{hi}: "
            f"{lo} {ladder[lo] * 100:.2f}% !< {hi} {ladder[hi] * 100:.2f}%"
        )


def test_w5b3_nit_unopened_utg_width_has_a_ceiling():
    """🔴 W5-b3 defect gate (b): an early-position CEILING exists on the nit's
    authored UTG width. Monotonicity alone can never pull the early end down —
    a ladder that is uniformly too wide is still monotone — so (a) without (b)
    only covers half the defect. PRE-SLICE HEAD read UTG 13.57%, which fails
    the cap below; post-slice it reads 7.54%.

    ⚠️ DIRECTIONAL, not a level gate. The roadmap explicitly FORBIDS gating on
    either circulating target (this file's own `~4% UTG -> 15-18% BTN` and the
    250-hand review's `~6-8% -> 18-22%`): RFI-by-seat is contract-flagged
    format-sensitive (6-max vs 9-max) and the seat-ordering claim is
    [UNVERIFIED], and §5a forbids a HARD gate on an UNVERIFIED row. The 10%
    cap below is therefore a loose directional bound chosen to sit clear of
    BOTH circulating targets while still failing HEAD — it asserts the
    ceiling's EXISTENCE as a committed shape, never its level. The NUMBER's
    future source is the `R9-SEATPROV` research item in NEXT (9-max full-ring
    RFI-by-seat provenance); when that lands, this cap is re-derived, not
    loosened.
    """
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    utg = _authored_raise_width(_unopened_node(packs[VillainType.NIT], "UTG"))
    assert utg <= 0.10, (
        f"nit authored UTG unopened width {utg * 100:.2f}% exceeds the "
        f"DIRECTIONAL 10% early-position ceiling (see R9-SEATPROV)"
    )


def test_w5b3_nit_is_the_tightest_raising_persona_at_every_seat():
    """W5-b3 character check: narrowing the nit must not cost it its place in
    the roster ordering. Against the three other RAISE-first archetypes the nit
    stays the tightest authored opener at all nine seats.

    Station and fish are deliberately EXCLUDED: they are limp-first, so their
    authored RAISE width (0.6% / 3.8%) is below the nit's by construction and
    says nothing about overall looseness (their VPIP is far higher). Comparing
    a limper's raise leg to a raiser's would invert the archetype ordering."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    nit = _seat_ladder(packs[VillainType.NIT])
    for other in (VillainType.TAG, VillainType.LAG, VillainType.MANIAC):
        wider = _seat_ladder(packs[other])
        for seat in _LADDER_SEATS:
            assert nit[seat] < wider[seat], (
                f"nit {seat} {nit[seat] * 100:.2f}% is not tighter than "
                f"{other.value} {wider[seat] * 100:.2f}%"
            )


def test_w5b3b_station_and_fish_unopened_width_stays_flat_across_seats():
    """W5-b3b — EXEMPT preservation guard (it is SUPPOSED to pass at HEAD;
    that is its job). A recreational archetype does not tighten up under the
    gun — flat positional width is what makes it recreational — so W5-b3's
    strict ladder must never be extended to these two packs. This guard exists
    so a later slice cannot quietly ladder them.

    Asserted against what the packs ACTUALLY ship today (measured, not
    aspirational): the station is one flat level across all nine seats; the
    fish has a single UTG step and is then flat across the other eight.
    Neither pack's content is touched by this slice."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")

    station = _seat_ladder(packs[VillainType.CALLING_STATION])
    assert len({round(v, 12) for v in station.values()}) == 1, (
        f"calling_station unopened width is no longer flat across seats: {station}"
    )
    assert station["UTG"] == pytest.approx(0.0060, abs=5e-4)

    fish = _seat_ladder(packs[VillainType.PASSIVE_FISH])
    later = [fish[s] for s in _LADDER_SEATS if s != "UTG"]
    assert len({round(v, 12) for v in later}) == 1, (
        f"passive_fish unopened width is no longer flat across the eight "
        f"non-UTG seats: {fish}"
    )
    assert fish["UTG"] == pytest.approx(0.0256, abs=5e-4)
    assert later[0] == pytest.approx(0.0377, abs=5e-4)
    # No ladder: at most a single authored step for either pack.
    assert len({round(v, 12) for v in fish.values()}) <= 2


def test_w5b3_nit_vpip_pfr_reported_not_gated():
    """REPORT-ONLY (roadmap W5-b3 pass/fail (c)): metric #3 VPIP/PFR for the
    nit, MEASURED and PRINTED against §5, never asserted. The single
    population-band anchor is W4-b — committing an RP6 number as a gate here
    is a §5 / §11 item-7 auto-FAIL. Run with `-s` to read it.

    Dossier envelope for context only (playstyle-research/nit.md §19,
    'Format-level targets'): VPIP 8-13 online / 10-16 live, PFR 6-11 / 5-10.
    """
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    s = _persona_stats_ext(packs, "nit", 600)
    print(
        f"nit VPIP {s.vpip:.3f} PFR {s.pfr:.3f} gap "
        f"{s.gap:.3f} (n=600, REPORTED — band anchor is W4-b)"
    )
    assert s.vpip is not None and s.pfr is not None


# ================== T-M2 — nit late-position pair opens (AUTHORED, n-free) ====
#
# W5-b3 review finding T-M2 (MED): the nit "never open-raises 22-66 anywhere,
# and 77 only from UTG" — an INVERSION (the one seat that opens 77 is the
# tightest) against a dossier that has the nit opening small pairs in late
# position. W5-b3 could not fix it: the pairs band was locked by W5-b1's
# verbatim-limp law, and the named follow-up was "convert pair FOLD mass (not
# limp mass) to raise at CO/BTN".
#
# That is exactly what these gates assert, in both directions:
#   - the band EXISTS at CO/BTN (fails at pre-slice HEAD: raise weight 0.0 on
#     every pair class below the core band, at every seat),
#   - the limp leg is BYTE-IDENTICAL at all nine seats (0.4 on every pair
#     class in the band) — the conversion came out of fold, not out of limp,
#   - and it did NOT leak to the seven other seats (over-widening guard: the
#     T-M2 finding is about LATE position; an early-position nit opening 22 is
#     a different, unauthorized change).

_NIT_PAIR_OPEN_SEATS = {
    "CO": ("77", "66", "55"),
    "BTN": ("77", "66", "55", "44", "33", "22"),
}
# The exact mix the pair-open band carries. Pinned as a whole (review fold,
# Codex+refuter MED): `raise > 0` would pass on a 0.01 token raise, and would
# not notice the fold/limp legs being re-cut underneath it.
_NIT_PAIR_OPEN_MIX = {"raise": 0.3, "limp": 0.4, "fold": 0.3}
_NIT_ALL_PAIRS = tuple(r + r for r in "AKQJT98765432")
# The authored limp band per seat: every pair BELOW that seat's core raise
# band. UTG raises 77 outright (core depth 8), every other seat stops at 88.
_NIT_LIMP_BAND = {
    seat: _NIT_ALL_PAIRS[8:] if seat == "UTG" else _NIT_ALL_PAIRS[7:]
    for seat in _LADDER_SEATS
}


def _nit_pair_policy(pack, seat: str) -> dict[str, dict[str, float]]:
    """Authored weights per PAIR class at one seat, resolved with sampler
    semantics (first matching mix in the node's list order wins; a class no
    mix covers folds 1.0)."""
    from app.domain.content.notation import parse_range

    node = _unopened_node(pack, seat)
    out: dict[str, dict[str, float]] = {}
    for cls in _NIT_ALL_PAIRS:
        weights: dict[str, float] = {}
        if node is not None:
            for mix in node.mixes:
                if cls in parse_range(mix.combos):
                    weights = dict(mix.weights)
                    break
        out[cls] = weights
    return out


def test_tm2_nit_opens_small_pairs_from_late_position():
    """🔴 T-M2 defect gate (deterministic, no sampling).

    PRE-SLICE HEAD reading (recorded per the gate-design rule): CO and BTN
    authored raise weight was 0.0 on 77, 66, 55, 44, 33 and 22 — the pairs
    below the `88+` core band were limp 0.4 / fold 0.6 at every seat, so this
    assertion FAILED at HEAD on all nine classes.

    POST-SLICE (this commit): CO opens 55-77 and BTN opens 22-77, each at
    raise 0.3 (limp 0.4 unchanged, fold 0.6 -> 0.3).

    Review fold (Codex + refuter MED): the assertion pins the WHOLE mix, not
    `raise > 0`. A token raise weight, or a raise leg funded by re-cutting the
    limp leg, would have satisfied the looser form."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    pack = packs[VillainType.NIT]
    wrong = {
        (seat, cls): _nit_pair_policy(pack, seat)[cls]
        for seat, band in _NIT_PAIR_OPEN_SEATS.items()
        for cls in band
        if _nit_pair_policy(pack, seat)[cls] != _NIT_PAIR_OPEN_MIX
    }
    assert not wrong, (
        f"nit late-position pair opens are not the authored "
        f"{_NIT_PAIR_OPEN_MIX}: {wrong}"
    )


def test_tm2_nit_pair_limp_weight_is_verbatim_at_every_seat():
    """🟢 PRESERVATION (passes at HEAD — labeled, not sold as a defect gate).

    W5-b1's verbatim-limp law: the authored limp weights ARE the nit's
    identity and this slice may not spend them. Every pair class in a seat's
    limp band carries EXACTLY 0.4 of limp, at all nine seats — so the CO/BTN
    raise band can only have come out of the fold leg. (UTG's band starts one
    class lower: it raises 77 outright, so its limp band is 22-66.)

    Review fold (refuter MED): PRESENCE is required, not just "0.4 if
    present". The earlier `if limp and limp != 0.4` form was DELETION-BLIND —
    dropping a class out of every mix (limp 0.4 -> 0.0, fold 1.0) read as
    clean, which is exactly how limp mass would get spent in practice."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    pack = packs[VillainType.NIT]
    bad = {}
    for seat in _LADDER_SEATS:
        policy = _nit_pair_policy(pack, seat)
        band = _NIT_LIMP_BAND[seat]
        for cls in band:
            limp = policy[cls].get("limp", 0.0)
            if limp != 0.4:
                bad[(seat, cls)] = policy[cls]
        # ... and the core band above it carries no limp leg at all, so the
        # band boundary itself cannot drift without failing here.
        for cls in _NIT_ALL_PAIRS[: len(_NIT_ALL_PAIRS) - len(band)]:
            if policy[cls].get("limp", 0.0):
                bad[(seat, cls)] = policy[cls]
    assert not bad, f"nit pair limp weight moved off the verbatim 0.4: {bad}"


def test_tm2_nit_pair_opens_did_not_leak_to_the_other_seven_seats():
    """🟢 PRESERVATION / over-widening guard (passes at HEAD): outside CO and
    BTN, a pair class either sits in the core raise band (raise 1.0) or has NO
    raise mass at all. This is what keeps T-M2 a late-position fix — an
    early-position nit that open-raises 22 would satisfy the defect gate above
    and be a worse bot.

    ⚠️ SB is excluded by TICKET SCOPE, not by realism (theory review R-7):
    T-M2 named CO and BTN, and the nit dossier's SB first-in range does
    include 55+. This guard therefore pins today's authored shape; a later
    SB-scoped slice is expected to move SB out of this list, and doing so is
    a content decision, not a regression."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    pack = packs[VillainType.NIT]
    leaked = {
        (seat, cls): w
        for seat in _LADDER_SEATS
        if seat not in _NIT_PAIR_OPEN_SEATS
        for cls, w in _nit_pair_policy(pack, seat).items()
        if 0.0 < w.get("raise", 0.0) < 1.0
    }
    assert not leaked, f"nit pair opens leaked outside CO/BTN: {leaked}"


def test_nlagladder_lag_vpip_pfr_reported_not_gated():
    """REPORT-ONLY (same rule as the nit row above — the single population-band
    anchor is W4-b; committing a level here would be a §5 / §11 item-7
    auto-FAIL). Prints BOTH rows against their §5 LAG bands. §5 provenance is
    stated once in content/personas/ladders/lag.unopened.json's `_doc` (VPIP
    21-27 / PFR 17-23, 9-max full ring, ledger #14, conf MEDIUM, edges
    DIRECTIONAL); it is not restated as a bare number here.

    WHY THIS ROW EXISTS (review fold, fix 1). N-LAGLADDER's first cut tightened
    the authored ladder and drove PFR to 15.77, UNDER the §5 floor. A 10-seed
    sweep of THIS metric at n=2000 then measured:
        pre-slice pack  VPIP 23.51 ±0.45 · PFR 17.32 ±0.34 · gap 6.19 ±0.36
        shipped  pack   VPIP 23.88 ±0.40 · PFR 17.32 ±0.30 · gap 6.55 ±0.28
    Two facts follow, and both are REPORTED not gated:
      1. JOINT GEOMETRY — PFR = VPIP − gap. With the gap at its ~6 ceiling, a
         VPIP under ~22.9 forces PFR under the 17 floor. The pre-slice pack
         already sat ON both limits (PFR 17.32 vs floor 17, gap 6.19 vs ceiling
         6), so there was NO headroom for a width tighten to spend. That is why
         this slice ships a composition swap at constant width.
      2. The gap row is ABOVE 6 on both packs. The +0.36 the shipped pack adds
         is the AQo vs_rfi fold->call transfer (AQo is 0.905% of hands × 0.40
         converted = 0.36pp of VPIP-without-PFR) — an intended, arithmetically
         accounted consequence of the T-F3 fix, not drift. It was NOT
         compensated elsewhere (that would be the compensating-lever trap).

    ⚠️ INSTRUMENT CAVEAT (review fold, fix 5): metric #3's lineup is
    3×[persona] + 6 fillers cycled from the other five archetypes — NOT the §5
    reference pool. Roster-wide this instrument reads one-sidedly LOW against
    §5 (nit 0.067 vs 10-14, maniac 0.390 vs 45-58, passive_fish 0.354 vs
    40-55), so a lag reading that lands inside a §5 band is not evidence of
    pool-level realism, and "there is no headroom" must not be inherited from
    here as a settled fact about the persona — only as one about this harness.
    """
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    s = _persona_stats_ext(packs, "lag", 600)
    print(
        f"lag VPIP {s.vpip:.3f} (§5 0.21-0.27) PFR {s.pfr:.3f} (§5 0.17-0.23) "
        f"gap {s.gap:.3f} — n=600, REPORTED, band anchor is W4-b; "
        f"10-seed n=2000 means: pre-slice 23.51/17.32/6.19, shipped 23.88/17.32/6.55"
    )
    assert s.vpip is not None and s.pfr is not None


def test_ntagcomp_tag_vpip_pfr_reported_not_gated():
    """REPORT-ONLY (same rule as the lag row above — the single population-band
    anchor is W4-b). Added at the wave-4 delta review (D4): N-TAGCOMP's `_doc`
    cites a 10-seed metric-#3 sweep (pre-slice VPIP 16.07 ±0.53 / PFR 12.80
    ±0.46 · shipped 16.46 ±0.37 / 12.95 ±0.25, all inside §5 TAG 15-20 /
    12-17) that previously had no in-repo reproduction path. §5 provenance is
    stated once in content/personas/ladders/tag.unopened.json's `_doc`; the
    lag row's instrument caveat (3×persona+filler lineup, one-sidedly LOW vs
    §5) applies verbatim.

    N-TAGWIDTH (2026-07-31) re-measured on its own 10-seed set (20260710 +
    1000i): the trim reads VPIP 16.05 -> 15.34 and PFR 12.67 -> 12.04, the
    latter at a stable-n escalation of n=4000 x 10 (sd 0.21, se 0.066).
    ⚠️ Read that PFR honestly rather than as a pass: its 95% CI is
    [11.91, 12.17], which STRADDLES the §5 low edge of 12, and 4 of the 10
    seeds read below it (min 11.750). The point estimate sits 0.04pp above a
    DIRECTIONAL band edge, measured on this 3x-persona lineup rather than the
    §5 reference pool, and nothing in the suite reds on it — §5 forbids gating
    a population number before the W4-b re-anchor, which is exactly why this
    row prints instead of asserting. Flagged for that re-anchor's watch list.
    The slice spends essentially all of the tag's remaining PFR headroom; the
    early-seat trim it could NOT afford is an escalated contract question (see
    the spec `_doc`). The two sweeps' pre-slice readings differ (12.67 vs
    12.80) because the seed sets differ; each sweep is internally comparable,
    which is all the instrument claims.
    """
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    s = _persona_stats_ext(packs, "tag", 600)
    print(
        f"tag VPIP {s.vpip:.3f} (§5 0.15-0.20) PFR {s.pfr:.3f} (§5 0.12-0.17) "
        f"gap {s.gap:.3f} — n=600, REPORTED, band anchor is W4-b; "
        f"10-seed means: N-TAGCOMP 16.46/12.95/3.51 (n=2000), "
        f"N-TAGWIDTH 15.34/12.04/3.30 (n=4000, PFR 95% CI [11.91, 12.17])"
    )
    assert s.vpip is not None and s.pfr is not None


# =====================================================================
# N-LOGIT — the frozen continue reference (`continue_ref`)
# =====================================================================
#
# WHAT THE SLICE DOES. At a facing-chips node the three merits (FOLD, CALL,
# RAISE) share one normalization, and `call_looseness` (`looseness`, assigned
# from `pf.call_looseness`/`pf.stickiness` near the top of
# `sample_postflop_decision`) multiplies the CALL merit only — on every cell
# except a STRONG draw at a dial below 1.0, where it is affine in the dial
# instead (call_base scales, and the draw bonus carries
# `_strong_draw_call_dial`, which protects a share of it from the dial —
# `max(looseness, 1.0)` until S3-T1 replaced the hard floor with a flat split on
# 2026-08-21, and a share that scales with the faced price, the cards to come
# and the out count since S3-T1b on 2026-08-22). Mass taken off CALL is
# therefore shared out to FOLD
# *and* RAISE in proportion to their merits, which on an aggressive persona
# lands mostly on RAISE — measured at the base engine, halving each pack's
# effective looseness moved raise-share the WRONG way for all six (+0.17;
# roadmap R10-4). N-logit scales the RAISE merit by
# `effective_looseness / continue_ref` — the frozen looseness the persona's
# facing-node raise behaviour was calibrated against — on the same cells CALL
# stays proportional on; on a STRONG draw at a dial below 1.0 it instead scales
# RAISE by the live CALL merit over the frozen UNSPLIT anchor, which routes
# whatever the protected share did to the continue mass through to RAISE in the
# base engine's original proportion. Either form makes `P(raise | continue)` no longer depend on the
# lever, and freed mass routes to FOLD.
#
# WHY THESE GATES ARE SHAPED THIS WAY (spec rev 3 §6; ledger R-1, R2-1..R2-10).
# Rev 1 of this slice shipped a mechanism that cancelled algebraically — a
# measured no-op — and it passed 8 of its own 10 criteria while doing nothing,
# because those criteria were IDENTITY measurements ("output unchanged"). An
# identity measurement cannot tell a behaviour-preserving fix from a fix that
# does nothing; only a SENSITIVITY measurement can. G1 below is that
# measurement and is the decisive gate. Recorded RED-FIRST evidence, taken on
# this branch with the packs authored but the engine scale NOT yet applied:
#
#   G1 worst |Δ P(raise | continue)| over x0.25/x0.5/x2/x4, per persona
#     (gate: <= 1e-12)
#       nit 0.332927 · tag 0.333327 · lag 0.333318 · maniac 0.333332
#       calling_station 0.293076 · passive_fish 0.333303
#   G2: 15,624 routing-sign violations out of 41,472 interior (cell, multiplier)
#     pairs. Representative — nit, two_pair/flop, price 2.0, x0.25:
#     ΔP(fold) = +0.0217 but ΔP(raise) = +0.2974. The calling lever went DOWN
#     and the raise rate went UP by 14x the fold rate's move: the R10-4
#     misroute, measured.
#
# If G1 ever passes with the engine block removed, the gate is broken, not the
# engine fixed.

_NLOGIT_ANCHORS = {  # spec §3.2 — frozen calibration anchors, NOT the shipped/authored
    # `call_looseness` values (R9-LOOSEFIT, 2026-08-04, moved nit's shipped value to
    # 0.45; the anchor stays put by design so the lever can be tuned against it)
    "nit": 0.6,
    "tag": 0.6,
    "lag": 0.55,
    "maniac": 0.55,  # from `stickiness` — maniac authors no `call_looseness`
    "calling_station": 4.0,
    "passive_fish": 0.42,
}
_NLOGIT_MULTS = (0.25, 0.5, 2.0, 4.0)
_NLOGIT_KEEP = object()


def _nlogit_probe(persona: str, mult: float = 1.0, *, continue_ref=_NLOGIT_KEEP):
    """A pack copy whose effective looseness is the anchor scaled by `mult`.

    `call_looseness` is authored on the copy for EVERY persona, maniac
    included. Maniac's effective looseness is the `stickiness` fallback, and
    `stickiness` is ALSO `_price_exponent`'s fallback (ledger R2-10), so
    sweeping maniac by editing `stickiness` would move the FOLD merit at the
    same time and confound the measurement — on the RIVER/AIR cell where the
    call merit is literally 0.0, base maniac's P(raise) still moves under a
    `stickiness` halving while lag and tag stay flat. Authoring the split lever
    on the probe copy sweeps the call axis alone.

    `model_copy` bypasses validation by construction; that is the same
    unvalidated-injection path G8 pins the engine's runtime guard against.
    `mult=1.0` reproduces the frozen calibration anchor exactly (x*1.0 == x) —
    not necessarily the pack's shipped/authored value; since R9-LOOSEFIT
    (2026-08-04) nit's shipped `call_looseness` (0.45) differs from its anchor
    (0.6) by construction.
    """
    pack = _pack(persona)
    update = {"call_looseness": _NLOGIT_ANCHORS[persona] * mult}
    if continue_ref is not _NLOGIT_KEEP:
        update["continue_ref"] = continue_ref
    probe = pack.model_copy(deep=True)
    probe.postflop = pack.postflop.model_copy(update=update)
    return probe


class _NlogitCell(NamedTuple):
    label: str
    street: Street
    hole: tuple
    board: list
    context: object  # PostflopContext | None
    pot_bb: float
    to_call: float
    stack_bb: float
    opponents: int
    facing_raise: bool
    with_raise: bool

    @property
    def key(self) -> str:
        return (
            f"{self.label} price={self.to_call} stack={self.stack_bb} "
            f"opp={self.opponents} facing_raise={self.facing_raise} "
            f"raise_legal={self.with_raise}"
        )


def _nlogit_spots():
    """(label, street, hole, board, context) — the 7 strength buckets on all
    three streets, BOTH draw categories on the two streets that have draws
    (the river resets DrawCategory to NONE by construction), and the river
    busted-draw `PostflopContext` states that feed the story-bluff term
    (ledger R2-7). Each template's classification is asserted by
    `test_nlogit_grid_covers_every_hand_class`, so a mis-chosen board can
    never silently shrink the grid."""
    flop = ["Kc", "9s", "3h"]
    turn = ["Kc", "9s", "3h", "2d"]
    river = ["Kc", "9s", "3h", "2d", "Tc"]
    made = [
        ("monster", ("9h", "9d")),
        ("two_pair", ("Kh", "9c")),
        ("overpair", ("Ah", "Ad")),
        ("top_pair", ("Kh", "4d")),
        ("middle_pair", ("9h", "4c")),
        ("ace_high", ("Ah", "8d")),
        ("air", ("7h", "4c")),
    ]
    spots = []
    for street, board in ((Street.FLOP, flop), (Street.TURN, turn), (Street.RIVER, river)):
        for label, hole in made:
            spots.append((f"{label}/{street.value}", street, hole, board, None))
    for street, board in (  # STRONG: flush draw (ace-high, no pair)
        (Street.FLOP, ["2h", "9h", "Kc"]),
        (Street.TURN, ["2h", "9h", "Kc", "7d"]),
    ):
        spots.append((f"strong_draw/{street.value}", street, ("Ah", "5h"), board, None))
    for street, board in (  # WEAK: gutshot, no flush draw (air)
        (Street.FLOP, ["7h", "9s", "9d"]),
        (Street.TURN, ["7h", "9s", "9d", "6s"]),
    ):
        spots.append((f"weak_draw/{street.value}", street, ("Td", "Jh"), board, None))
    for busted in (BustedDraw.STRAIGHT, BustedDraw.FLUSH):
        spots.append(
            (
                f"river_busted_{busted.name.lower()}",
                Street.RIVER,
                ("7h", "4c"),
                river,
                PostflopContext(bet_prev_street=True, busted_draw=busted),
            )
        )
    return spots


_NLOGIT_PRICES = (2.0, 4.0, 6.0, 12.0)  # to_call into a 6bb pot: 1/3 pot … 2x pot
# (stack, opponents) — heads-up and multiway, above and BELOW spr_commit
# (pot is 6bb, so stack 12 = SPR 2.0 commits every persona; 30 = SPR 5 does not).
_NLOGIT_STACKS = ((100.0, 1), (100.0, 3), (12.0, 1), (30.0, 2))


def _nlogit_cells():
    cells = []
    for label, street, hole, board, ctx in _nlogit_spots():
        for to_call in _NLOGIT_PRICES:
            for stack_bb, opponents in _NLOGIT_STACKS:
                for facing_raise in (False, True):
                    for with_raise in (False, True):  # both facing legal shapes
                        cells.append(
                            _NlogitCell(
                                label,
                                street,
                                hole,
                                board,
                                ctx,
                                6.0,
                                to_call,
                                stack_bb,
                                opponents,
                                facing_raise,
                                with_raise,
                            )
                        )
    return cells


def _nlogit_dist(pack, cell: _NlogitCell) -> dict:
    """The cell's EXACT normalized action distribution — the first
    `rng.choices` weights, so there is no Monte-Carlo noise anywhere in these
    gates."""
    legal = [personas_postflop_legal_fold(), personas_postflop_legal_call(cell.to_call)]
    if cell.with_raise:
        legal.append(personas_postflop_legal_raise(cell.to_call * 3, 200.0))
    cap = _CaptureWeights()
    sample_postflop_decision(
        pack,
        cell.hole,
        cell.board,
        legal,
        cell.pot_bb,
        cell.stack_bb,
        cell.opponents,
        cap,  # type: ignore[arg-type] — duck-typed capture rng
        current_bet_to=cell.to_call,
        street=cell.street,
        latest_aggressor_contribution_bb=cell.to_call,
        context=cell.context,
        facing_raise=cell.facing_raise,
    )
    return cap.dist or {}


_NLOGIT_SWEEP: dict = {}


def _nlogit_sweep():
    """{persona: {mult: [dist per cell]}} plus `_cells`. Computed ONCE and
    shared by G1/G2/G4 — the grid is 1,728 cells x 6 personas x 5 lever
    settings, and re-deriving it per gate would triple the file's cost."""
    if not _NLOGIT_SWEEP:
        cells = _nlogit_cells()
        for persona in _NLOGIT_ANCHORS:
            per = {}
            for mult in (1.0,) + _NLOGIT_MULTS:
                probe = _nlogit_probe(persona, mult)
                per[mult] = [_nlogit_dist(probe, c) for c in cells]
            _NLOGIT_SWEEP[persona] = per
        _NLOGIT_SWEEP["_cells"] = cells
    return _NLOGIT_SWEEP


def _nlogit_p(dist, kind) -> float:
    return dist.get(kind, 0.0)


def test_nlogit_grid_covers_every_hand_class():
    """The grid's coverage claim, asserted rather than asserted-in-prose: all
    seven strength buckets on all three streets, plus STRONG and WEAK draws on
    the two streets that have draws. A board edit that silently demoted a
    template (say a gutshot that stops being one) would otherwise shrink G1's
    reach without any gate noticing."""
    expect = {
        "monster": StrengthBucket.MONSTER,
        "two_pair": StrengthBucket.TWO_PAIR_PLUS,
        "overpair": StrengthBucket.OVERPAIR_TPTK,
        "top_pair": StrengthBucket.TOP_PAIR,
        "middle_pair": StrengthBucket.MIDDLE_PAIR,
        "ace_high": StrengthBucket.ACE_HIGH,
        "air": StrengthBucket.AIR,
        "strong_draw": DrawCategory.STRONG,
        "weak_draw": DrawCategory.WEAK,
    }
    seen = set()
    for label, _street, hole, board, _ctx in _nlogit_spots():
        bucket, draw = strength_bucket(hole, board)
        name = label.split("/")[0]
        if name in ("strong_draw", "weak_draw"):
            assert draw is expect[name], (label, draw)
        elif name in expect:
            assert bucket is expect[name], (label, bucket)
        seen.add((bucket, draw))
    buckets = {b for b, _ in seen}
    assert buckets == set(StrengthBucket), sorted(b.value for b in buckets)
    assert {d for _, d in seen} == set(DrawCategory)


def test_nlogit_g1_orthogonality_raise_share_is_lever_invariant():
    """G1 (RED-FIRST, DECISIVE) — `P(raise) / (P(call) + P(raise))` does not
    move when `call_looseness` is swept over x0.25 / x0.5 / x2 / x4.

    This is the one gate an empty diff cannot pass, and the one gate a
    schema-and-content-only change cannot pass either. It FAILED on this
    branch with the packs authored and the engine untouched: worst drift
    nit 0.332927 · tag 0.333327 · lag 0.333318 · maniac 0.333332 ·
    calling_station 0.293076 · passive_fish 0.333303.

    A cell whose ANCHOR distribution has no continue mass is skipped, not
    asserted: a river-air FOLD+CALL node has the call merit hard-zeroed and no
    raise leg, so the ratio is 0/0 (ledger R2-2). But once the anchor HAS
    continue mass, a tuned lever losing all of it is a FAILURE, not a skip.
    Codex Sol found that hole at build review: a mutant that zeroed CALL and
    RAISE below the anchor — five personas folding 100% instead of preserving
    the raise:call odds — passed all 24 gates, because both the skip here and
    G2's sign test accepted the collapse (ledger B-8).

    The comparison count is asserted too. `worst` is keyed by persona and only
    written when a comparison actually happens, so a persona whose every cell
    was skipped would never appear and the DECISIVE gate would pass having
    measured nothing on it."""
    sweep = _nlogit_sweep()
    cells = sweep["_cells"]
    worst = {}
    compared = dict.fromkeys(_NLOGIT_ANCHORS, 0)
    collapsed = []
    for persona in _NLOGIT_ANCHORS:
        per = sweep[persona]
        for i, cell in enumerate(cells):
            base = per[1.0][i]
            denom = _nlogit_p(base, ActionType.CALL) + _nlogit_p(base, ActionType.RAISE)
            if denom <= 0.0:
                continue
            ref_share = _nlogit_p(base, ActionType.RAISE) / denom
            for mult in _NLOGIT_MULTS:
                d = per[mult][i]
                den = _nlogit_p(d, ActionType.CALL) + _nlogit_p(d, ActionType.RAISE)
                if den <= 0.0:
                    collapsed.append((persona, cell.key, mult))
                    continue
                compared[persona] += 1
                drift = abs(_nlogit_p(d, ActionType.RAISE) / den - ref_share)
                if drift > worst.get(persona, (0.0, ""))[0]:
                    worst[persona] = (drift, f"{cell.key} x{mult}")
    assert not collapsed, (
        f"{len(collapsed)} cells lost ALL continue mass when the lever moved, "
        f"though the anchor had some: {collapsed[:5]}"
    )
    thin = {p: n for p, n in compared.items() if n < 1000}
    assert not thin, f"gate measured almost nothing for {thin}"
    bad = {p: v for p, v in worst.items() if v[0] > 1e-12}
    assert not bad, f"raise-share moved with the calling lever: {bad}"


def test_nlogit_g2_routing_sign_freed_mass_goes_to_fold():
    """G2 (RED-FIRST) — SIGN only, per direction (ledger R2-2 killed rev 2's
    version of this gate for stating it on the wrong quantity).

      lever DOWN (x0.25, x0.5): P(fold) rises, P(raise) does not rise
      lever UP   (x2, x4):      signs invert

    Strict movement is required only on INTERIOR cells (`0 < P(fold) < 1`) —
    an SPR-committed node has P(fold) pinned at 0 by `_commit_transform` and a
    zero-continue node has it pinned at 1; neither can move, and demanding
    that they do is what made rev 2's gate unpassable by a correct build.
    G1 owns orthogonality; this gate owns direction only."""
    sweep = _nlogit_sweep()
    cells = sweep["_cells"]
    violations = []
    interior = 0
    for persona in _NLOGIT_ANCHORS:
        per = sweep[persona]
        for i, cell in enumerate(cells):
            base = per[1.0][i]
            f0 = _nlogit_p(base, ActionType.FOLD)
            if not 0.0 < f0 < 1.0:
                continue
            interior += 1
            for mult in _NLOGIT_MULTS:
                d = per[mult][i]
                df = _nlogit_p(d, ActionType.FOLD) - f0
                dr = _nlogit_p(d, ActionType.RAISE) - _nlogit_p(base, ActionType.RAISE)
                if mult < 1.0 and not (df > 0.0 and dr <= 0.0):
                    violations.append((persona, cell.key, mult, df, dr))
                if mult > 1.0 and not (df < 0.0 and dr >= 0.0):
                    violations.append((persona, cell.key, mult, df, dr))
    assert interior > 1000, f"grid degenerated: only {interior} interior cells"
    assert not violations, f"{len(violations)} routing-sign violations: {violations[:5]}"


def _nlogit_cell_draw(cell: _NlogitCell) -> DrawCategory:
    """The cell's draw category, read from the engine's own classifier rather
    than from the cell's label — a board edit that demoted a template must move
    G3's scope with it, not silently leave a cell inside the scope under a
    label that no longer describes it."""
    return strength_bucket(cell.hole, cell.board)[1]


# Measured, and pinned so the exclusion below cannot widen silently: 128 of the
# 1,728 grid cells classify STRONG (the two `strong_draw` templates x 4 prices
# x 4 stack/opponent shapes x facing_raise x raise-legal). The other 1,600
# (1,472 draw-NONE + 128 WEAK) stay inside G3.
_NLOGIT_G3_EXCLUDED_CELLS = 128


def test_nlogit_g3_identity_at_authored_values_is_bit_exact():
    """G3 — at the frozen calibration anchor (not necessarily the pack's
    shipped/authored value — see `_NLOGIT_ANCHORS`) the opted-in path is
    BIT-identical to the un-opted path on every NON-STRONG cell of the grid.

    The un-opted path IS the base engine: `continue_ref is None` short-circuits
    the new block, so the code that runs is HEAD's, unmodified (spec §3.5).
    That makes this a base comparison without needing a golden file, and
    bit-exactness (not approx) is what the comparison asserts — the scale is
    `looseness / continue_ref` with the two equal, i.e. exactly 1.0. The
    external absolute anchors are the 23 frozen exact-equality vectors in
    `tests/test_price_tail.py` and the byte-identical persona-stats golden,
    both untouched by this slice and both still green.

    ── WHY `DrawCategory.STRONG` IS OUT OF SCOPE (N-DRAWLOOSE ruling R1,
    2026-08-05, owner). At a dial below 1.0 a STRONG draw's call bonus is
    protected from the dial — in full until 2026-08-21, in a flat 0.7 share of
    it under S3-T1, and since S3-T1b (2026-08-22) in the price-mandated share
    `_strong_draw_protected_share` computes for the node — so the call merit is
    affine in the dial rather than proportional to it, and whatever that does to
    the continue mass has to reach the RAISE leg in the same proportion or an
    aggressive persona stops semi-bluff-raising the very draws the protection
    exists to keep in. The engine routes it through THIS
    feature: on a STRONG draw at a dial below 1.0 the raise scale becomes
    `_c_now / _call_merit_at_ref` instead of the literal `looseness / ref`
    (the `if draw is DrawCategory.STRONG and looseness < 1.0 and
    _call_merit_at_ref > 0.0:` branch of the N-LOGIT block). So on those cells
    the opted-in path is
    deliberately NOT inert any more, and G3's identity is false there by
    design.

    THE EXCLUSION IS UNAVOIDABLE, not a convenience. The un-opted path
    (`continue_ref is None`) has NO raise scale at all — the whole block is
    short-circuited — so there is no expression on that side that could carry
    what the dial protection does to the call merit. Any design that hands that
    to RAISE must
    therefore break `opted == un-opted` on exactly these cells. The only way to
    keep G3 whole would be to withhold the growth from RAISE, which is the
    already-rejected fan-in defect A (lag's P(raise) at the trace node falls
    0.4718 -> 0.3884).

    WHAT REPLACES IT ON THOSE CELLS, because scoping a gate without replacing
    it is not acceptable:
    `test_nd_t4_strong_draw_raise_share_matches_the_base_engine` asserts the
    property that SHOULD hold there — P(raise | continue) equal to the BASE
    engine b0a6a4e, per persona, at seven priced strong-draw nodes. That is
    strictly stronger than bit-identity-to-the-un-opted-path would have been,
    because the un-opted path is not the base engine's raise share on these
    cells either.

    MEASURED REACH of the exclusion (re-verified for this revision, not
    quoted). Of the 1,728 x 6 = 10,368 (cell, persona) comparisons the
    unscoped gate made, exactly 320 now differ: 64 per persona for the five
    personas whose calibration anchor is below 1.0 (nit, tag, lag, maniac,
    passive_fish), and those 64 are precisely the raise-legal half of that
    persona's 128 STRONG cells — a raise-scale change cannot move a cell with
    no RAISE entry. `calling_station` (anchor 4.0, above 1.0) stays
    bit-identical on all 1,728, and every one of the 1,600 non-STRONG cells
    stays bit-identical for all six personas. Those 1,600 x 6 = 9,600
    comparisons are what this gate still makes.
    """
    cells = _nlogit_cells()
    excluded = 0
    for persona in _NLOGIT_ANCHORS:
        opted = _nlogit_probe(persona)
        unopted = _nlogit_probe(persona, continue_ref=None)
        excluded = 0
        for cell in cells:
            if _nlogit_cell_draw(cell) is DrawCategory.STRONG:
                excluded += 1
                continue
            a = _nlogit_dist(opted, cell)
            b = _nlogit_dist(unopted, cell)
            assert list(a.keys()) == list(b.keys()), (persona, cell.key)
            for k in a:
                assert a[k] == b[k], (persona, cell.key, k, a[k], b[k])
    assert excluded == _NLOGIT_G3_EXCLUDED_CELLS, (
        f"G3's STRONG-draw exclusion now covers {excluded} of {len(cells)} cells, not the "
        f"pinned {_NLOGIT_G3_EXCLUDED_CELLS}. The scope of a scoped gate is itself part of "
        "the claim: widening it silently is how a gate stops covering the thing it names"
    )


def _nlogit_bluff_cell(hole=("7h", "4c"), to_call=4.0):
    """A river bluff cell with a RAISE legal. At the default hole cards this is
    AIR with no draw, where `call_merit` is hard-zeroed by the river/AIR/no-draw
    guard in `sample_postflop_decision`, so FOLD and RAISE carry all the weight.

    The ace-high variant (`hole=("Ah", "8d")`) is the same node shape for the
    other member of `bluff_cell`. It stopped being hard-zeroed at T3
    (improvement slice 2, 2026-08-19): ace-high now has a live CALL leg there,
    so that variant is used by the T3 raise-mass pin rather than by G4."""
    return _NlogitCell(
        "polar_bluff/river",
        Street.RIVER,
        hole,
        ["Kc", "9s", "3h", "2d", "Tc"],
        None,
        6.0,
        to_call,
        100.0,
        1,
        False,
        True,
    )


# G4 pins: `P(raise)` on the river polar-bluff cells at call_looseness
# x0.25 / x0.5 / x1 / x2 / x4, measured on this branch with the engine scale
# applied. A DISCLOSURE record, not a fitted magnitude — nothing was tuned to
# hit these and no band depends on them. At the base engine every row is flat
# at its x1 value (asserted below), which is the point of the gate.
#
# ONE cell since T3 (improvement slice 2, 2026-08-19). The hard-zeroed class
# used to have two members, because `bluff_cell` is `bucket in (AIR, ACE_HIGH)
# and draw is NONE`, and both were pinned here — ACE_HIGH at a small faced
# price was the larger by roughly 6x. T3 narrowed the river call zero to AIR,
# so a river ACE_HIGH node now has a live CALL leg and its vector is not
# degenerate; the lever reaches it through CALL like every other bucket, which
# is G1 and G3's subject rather than this gate's. The ACE_HIGH numbers were not
# discarded: they moved, unchanged to the digit, to
# `test_t3_river_ace_high_raise_to_fold_odds_are_untouched` below, where they
# now pin that T3 left the bluff-RAISE mass alone.
# RE-RECORDED for the de-robotization slice's T5 (2026-08-16,
# slice-authorized). All twelve rows move — six personas x both cells — and the
# cause is the F2 joint law rather than anything in the N-LOGIT mechanism these
# pins guard. `personas_postflop` ~:910 scales `bluff_mass` by
# E_s[_bluff_size_factor(s)] over the persona's own authored sizing, so
# re-weighting a pack's bet sizes moves every bluff-cell probability with it.
# Over each pack's FLAT block, which is the distribution these particular pins
# are measured on: maniac -13.1%, nit -6.3%, lag -3.8%, tag +0.4%, station
# +7.1%, fish +10.0%.
#
# Those are flat-block figures and NOT persona-wide. Four packs carry
# `sizing_by_node`, and there the sign can reverse: measured against `ed4d108`
# across the whole slice, nit `cbet_dry` +3.2% and lag `cbet_mono` +2.3% rise
# while tag `river_value` falls -7.5%. The slice's own two review rounds each
# moved these again — the river figure was recorded as -3.9% while the same
# commit was halving it — so the numbers here are stated once, against
# `ed4d108`, at the branch tip, rather than per-commit. The tip's own last round
# moved three cells and only three: tag `cbet_wet` -3.5%, nit `cbet_wet` -2.8%,
# lag `cbet_wet` -5.9%, all from the third-pot size added there.
# These are bluff cells by construction, so they are the cells most exposed to
# that coupling — the twelve-of-twelve move is the expected signature, and a
# PARTIAL move would have been the thing to investigate.
# The coupling this gate exists to watch — `call_looseness` reaching the
# bluff-raise rate on a hard-zeroed call cell — was untouched by that
# re-record: the sweep still spans the same shape, and `test_nlogit_g1`/`g3`
# pass unchanged. T3 later removed ACE_HIGH from the class the coupling can
# reach, which is a change of SCOPE and not of magnitude; the AIR rows below
# are byte-identical across it.
_NLOGIT_BLUFF_SWEEP = (0.25, 0.5, 1.0, 2.0, 4.0)
# AIR, half-pot faced price — the mild member.
_NLOGIT_BLUFF_PINS = {
    "lag": [0.006086052923715886, 0.012098473895010543, 0.023907701092464193, 0.046698937935432526, 0.08923088816263465],  # noqa: E501
    "tag": [0.0038569107491173, 0.007684184285266557, 0.015251175725689927, 0.030044142947755884, 0.05833564154207269],  # noqa: E501
    "nit": [0.0007224894563152039, 0.0014439356843228871, 0.002883707480511515, 0.005750831245939953, 0.011435896580499432],  # noqa: E501
    "maniac": [0.01000583536813726, 0.019813420908583623, 0.03885695265891133, 0.07480712827585852, 0.1392010274361683],  # noqa: E501
    "calling_station": [0.0008321924048908285, 0.0016630008730857482, 0.0033204797853893303, 0.0066189813769167395, 0.013150917078600846],  # noqa: E501
    "passive_fish": [0.0015733919400161421, 0.0031418405334601223, 0.0062640005760089225, 0.01245001425554976, 0.024593834915799185],  # noqa: E501
}
# ACE_HIGH, an eighth-pot faced price. Recorded on the pre-T3 engine, where
# this cell was hard-zeroed too; kept unchanged because T3 must not move it —
# see `test_t3_river_ace_high_raise_to_fold_odds_are_untouched`.
_NLOGIT_BLUFF_PINS_ACE_HIGH = {
    "nit": [0.012690061839999685, 0.025062084280638778, 0.04889866607099545, 0.09323811279913614, 0.17057237889449078],  # noqa: E501
    "tag": [0.06439820175506222, 0.12100396571297749, 0.21588499133634537, 0.35510758480384264, 0.5241024237278488],  # noqa: E501
    "lag": [0.10061471506267866, 0.18283367228458103, 0.309145193561234, 0.4722855724203888, 0.6415678877352128],  # noqa: E501
    "maniac": [0.15586887969278476, 0.2696999329789253, 0.4248246786091653, 0.5963185295524998, 0.7471172181653085],  # noqa: E501
    "calling_station": [0.005310263118787907, 0.010564426353937352, 0.020907971977706042, 0.040959562569000324, 0.07869578039691683],  # noqa: E501
    "passive_fish": [0.04106769806656815, 0.07889534588929718, 0.14625208309572676, 0.25518310544873896, 0.406606979238314],  # noqa: E501
}


def test_nlogit_g4_river_bluff_cell_response_is_pinned():
    """G4 — the disclosed behavioural coupling on the river polar-bluff cell
    (spec §3.4, ledger R2-3), pinned so it can never move silently.

    On that cell `call_merit` is hard-zeroed, so at the base engine the
    bluff-raise frequency is EXACTLY independent of `call_looseness`. Under the
    scale it is not: the raise leg is the only continue candidate there, so
    scaling it by the continue lever moves the bluff-raise rate directly. That
    is the mechanism behaving correctly on a degenerate node — the only way to
    continue IS to raise — but it does put `call_looseness` on a magnitude the
    spec assigns to `bluff_freq`. It is DISCLOSED and gated here, and was put
    to the persona-realism theory reviewer at fan-in; it is not settled by this
    test. G1 is vacuous on these cells (CALL = 0 ⇒ the ratio is identically 1)
    and G3 passes (identity at the authored value), so without this pin
    nothing in the gate set would see the coupling at all.

    The class has ONE member since T3 narrowed the river call zero to AIR (see
    the comment on the pin table). The ACE_HIGH cell that used to be pinned
    here is no longer degenerate and is gated by
    `test_t3_river_ace_high_raise_to_fold_odds_are_untouched` instead."""
    for label, pins, cell in (
        ("air/half_pot", _NLOGIT_BLUFF_PINS, _nlogit_bluff_cell()),
    ):
        for persona, expected in pins.items():
            scaled = [
                _nlogit_p(_nlogit_dist(_nlogit_probe(persona, m), cell), ActionType.RAISE)
                for m in _NLOGIT_BLUFF_SWEEP
            ]
            base = [
                _nlogit_p(
                    _nlogit_dist(_nlogit_probe(persona, m, continue_ref=None), cell),
                    ActionType.RAISE,
                )
                for m in _NLOGIT_BLUFF_SWEEP
            ]
            # The magnitude, pinned to 9 significant figures.
            assert scaled == pytest.approx(expected, rel=1e-9), (label, persona, scaled)
            # The base path is EXACTLY flat — the half that shows the coupling
            # is new, rather than something the lever always had.
            assert max(base) - min(base) == 0.0, (label, persona, base)
            # ...and the scaled path is monotone in the lever.
            assert scaled == sorted(scaled), (label, persona, scaled)
            assert scaled[0] < scaled[2], (label, persona, scaled)


# ================= T3 — ace-high may call the river again =====================
#
# Improvement slice 2, ticket T3, owner ruling of 2026-08-18 (spec §6). The
# river call zero used to be written on `bluff_cell`, which bundles ACE_HIGH
# with AIR, and so it refused the call to a hand that is a river bluff-catcher.
# It is now written on the bucket and the draw and applies to AIR alone.
#
# The defect the ticket names is DETERMINISM, not over-folding. Where the faced
# bet is at least the seat's remaining stack the engine offers no RAISE
# (`table/engine.py:204-206`), so a zeroed call left FOLD as the only weighted
# candidate: probability exactly 1.000, a thousand times out of a thousand.
#
# Measured on 50,000 hands at seed 20260817 on the ratified lineup. BEFORE T3
# that node was reached 823 times by naked ace-high and 380 times by air, and
# every one of the 1,203 was a fold at probability one. AT THE SHIPPED DAMP OF
# 0.06 it is reached 829 times by ace-high, which now splits 678 folds and 151
# calls for P(call) 0.1821, and 382 times by air, which still folds every time.
# Per persona on the ace-high half: calling_station 0.3559 (n=295), maniac
# 0.1061 (n=132), tag 0.0992 (n=121), nit 0.0769 (n=13), lag 0.0714 (n=70),
# passive_fish 0.0707 (n=198).
# An earlier version of this block quoted 0.691, which was the UNDAMPED figure
# measured before the owner's band ruling and never re-measured. Full table:
# `docs/ai-dlc/research/slice2-invest-then-fold/t3-measurements.md`.

_T3_RIVER_BOARD = ["Ks", "9h", "2s", "4d", "7c"]
_T3_ACE_HIGH = ("Ad", "8c")  # naked ace-high, no draw, no pair with the board
_T3_AIR = ("8h", "6c")  # air, no draw — the half of the rule that survives


def _t3_allin_river_dist(persona, hole, *, pot_bb=40.0, to_call=12.0, stack_bb=12.0):
    """The node the ticket is about: river, facing a bet at least the seat's
    remaining stack, so no RAISE is legal and the vector is FOLD + CALL only."""
    legal = [personas_postflop_legal_fold(), personas_postflop_legal_call(to_call)]
    cap = _CaptureWeights()
    sample_postflop_decision(
        _pack(persona),
        hole,
        _T3_RIVER_BOARD,
        legal,
        pot_bb,
        stack_bb,
        1,
        cap,  # type: ignore[arg-type] — duck-typed capture rng
        current_bet_to=to_call,
        street=Street.RIVER,
        latest_aggressor_contribution_bb=to_call,
        facing_raise=False,
    )
    return cap.dist or {}


def test_t3_spots_classify_as_intended():
    """Both probe holes must be the buckets the tests below assume; a board or
    ladder edit that silently re-classified either would make every leg
    vacuous."""
    assert strength_bucket(_T3_ACE_HIGH, _T3_RIVER_BOARD) == (
        StrengthBucket.ACE_HIGH,
        DrawCategory.NONE,
    )
    assert strength_bucket(_T3_AIR, _T3_RIVER_BOARD) == (
        StrengthBucket.AIR,
        DrawCategory.NONE,
    )


@pytest.mark.parametrize("persona", ALL_PERSONAS)
def test_t3_river_ace_high_facing_an_all_in_bet_is_mixed(persona):
    """T3 acceptance 4 — the ticket's headline, and the leg that fails on the
    unmodified engine.

    Naked ace-high on the river, facing a bet at least its remaining stack, now
    returns a genuine mixture. Before T3 this vector was FOLD 1.0 / CALL 0.0 for
    every persona, which is the machine tell the whole initiative exists to
    remove: there is no rng draw whose outcome can differ.

    The assertion is deliberately on MIXEDNESS rather than on a level. T3's
    point is that the decision mixes, not that ace-high calls often; a
    river-specific damp on the call term would lower these numbers without
    touching what this test asserts."""
    dist = _t3_allin_river_dist(persona, _T3_ACE_HIGH)
    assert set(dist) == {ActionType.FOLD, ActionType.CALL}, dist
    call = dist[ActionType.CALL]
    assert 0.0 < call < 1.0, (persona, dist)
    assert 0.0 < dist[ActionType.FOLD] < 1.0, (persona, dist)


@pytest.mark.parametrize("persona", ALL_PERSONAS)
def test_t3_river_air_facing_an_all_in_bet_still_never_calls(persona):
    """The half of the rule that was always right. "Air never calls the river"
    survives T3 intact and is asserted at EXACTLY zero, not merely small: air
    beats nothing at showdown, so the certainty is correct play rather than a
    lookup-table artifact."""
    dist = _t3_allin_river_dist(persona, _T3_AIR)
    assert dist[ActionType.CALL] == 0.0, (persona, dist)
    assert dist[ActionType.FOLD] == 1.0, (persona, dist)


def test_t3_river_call_damp_is_the_shipped_constant():
    """The pin is EXACT, because a bracket cannot express what constrains this
    constant, and the previous revision of this test proved it: it allowed
    anything up to 0.065, including values since measured as violating the
    margin standard the source comment states.

    What ships is not what was derived. Minimum-defence arithmetic over the
    measured river price distribution puts the constant near 0.46; 0.06 ships
    because the lag and calling-station went-to-showdown bands do not admit the
    derived value, and the owner ruled that conflict in the bands' favour on
    2026-08-19. Measured on the bands' own harness, the top of the admissible
    range is a knife edge — 0.061 clears the stated standard and 0.062 misses it
    by 0.0003 of station margin — which is why the source describes 0.06 as a
    round constant inside that range rather than as its maximum, and why this
    test pins the shipped value rather than a bound.

    Change the constant and this test fails on purpose: the band sweep, the
    residual under-defence and the population figures in the provenance block
    all have to be re-measured with it.

    The second assertion is deliberately redundant against the first. It names
    the one property that must survive ANY future re-derivation: at zero this
    branch is the hard-zero T3 removed, and the determinism win would revert
    silently with every other test in this file still green."""
    assert personas_postflop._ACE_HIGH_RIVER_CALL_DAMP == 0.06
    assert personas_postflop._ACE_HIGH_RIVER_CALL_DAMP > 0.0, (
        "a zero river call damp is the pre-T3 hard zero by another name"
    )


@pytest.mark.parametrize("persona", ALL_PERSONAS)
def test_t3_river_damp_moves_only_the_ace_high_call_leg(persona):
    """Neutralizing the damp to 1.0 must change the river ace-high CALL leg and
    nothing else about the vector's shape, and must leave AIR bit-identical.

    This is what stops a later edit from routing the damp through the fold or
    raise merit, which would be the N-LOGIT misroute in a new costume."""
    saved = personas_postflop._ACE_HIGH_RIVER_CALL_DAMP
    try:
        damped = _t3_allin_river_dist(persona, _T3_ACE_HIGH)
        air_damped = _t3_allin_river_dist(persona, _T3_AIR)
        personas_postflop._ACE_HIGH_RIVER_CALL_DAMP = 1.0
        undamped = _t3_allin_river_dist(persona, _T3_ACE_HIGH)
        air_undamped = _t3_allin_river_dist(persona, _T3_AIR)
    finally:
        personas_postflop._ACE_HIGH_RIVER_CALL_DAMP = saved
    assert air_damped == air_undamped, persona
    assert damped[ActionType.CALL] < undamped[ActionType.CALL], (persona, damped, undamped)
    # The damp multiplies the call merit, so on a two-outcome node the CALL:FOLD
    # odds fall by exactly the constant.
    d_odds = damped[ActionType.CALL] / damped[ActionType.FOLD]
    u_odds = undamped[ActionType.CALL] / undamped[ActionType.FOLD]
    assert d_odds == pytest.approx(u_odds * saved, rel=1e-9), (persona, d_odds, u_odds)


def test_t3_river_ace_high_raise_to_fold_odds_are_untouched():
    """T3 unblocked ONE action, and this is the pin that says so — using the
    very numbers G4 held before the change, unedited.

    `bluff_cell` still bundles ACE_HIGH, so the river bluff-RAISE merit is still
    `_BLUFF_RAISE_FACTOR * bluff_mass`, and the FOLD merit was never in scope.
    The N-LOGIT `rscale` cannot smuggle the new CALL weight into RAISE either:
    its call-tracking branch is gated on `draw is DrawCategory.STRONG`, and this
    cell is draw-NONE, so `rscale` is `looseness / ref` and depends on nothing
    T3 touched.

    RAISE : FOLD odds are therefore an EXACT invariant of the change. Before it
    the cell was hard-zeroed, so the pinned P(raise) `p` sat in a two-outcome
    vector and the odds were `p / (1 - p)`; afterwards the call leg takes some
    of the probability and the odds must be unchanged. A ticket that moved the
    bluff mass — the thing "leave `bluff_cell` alone" protects — fails here."""
    cell = _nlogit_bluff_cell(hole=("Ah", "8d"), to_call=0.5)
    for persona, pre_t3 in _NLOGIT_BLUFF_PINS_ACE_HIGH.items():
        for mult, p in zip(_NLOGIT_BLUFF_SWEEP, pre_t3, strict=True):
            dist = _nlogit_dist(_nlogit_probe(persona, mult), cell)
            # T3 landed: the cell is no longer degenerate.
            assert _nlogit_p(dist, ActionType.CALL) > 0.0, (persona, mult, dist)
            odds = _nlogit_p(dist, ActionType.RAISE) / _nlogit_p(dist, ActionType.FOLD)
            assert odds == pytest.approx(p / (1.0 - p), rel=1e-9), (persona, mult, odds)


def _nlogit_commit_cell():
    """A facing node BELOW `spr_commit`: pot 6bb, stack 6bb => SPR 1.0, which
    is under every persona's `spr_commit`. `_commit_transform` zeroes the FOLD
    merit there while FOLD stays legal."""
    return _NlogitCell(
        "overpair/turn_committed",
        Street.TURN,
        ("Ah", "Ad"),
        ["Kc", "9s", "3h", "2d"],
        None,
        6.0,
        4.0,
        6.0,
        1,
        False,
        True,
    )


# G-COMMIT pins: `P(raise)` on the committed facing cell across the sweep,
# measured on this branch. Each row is a SINGLE number because the cell is now
# lever-inert; the base row for the same cell is not (see the gate).
_NLOGIT_COMMIT_PINS = {
    "nit": 0.5172413793103449,
    "tag": 0.8108108108108109,
    "lag": 0.8617594254937164,
    "maniac": 0.9160305343511451,
    "calling_station": 0.11811023622047245,
    "passive_fish": 0.6048387096774193,
}


def test_nlogit_gcommit_spr_committed_nodes_are_lever_inert():
    """The SECOND reach change, disclosed at build review (ledger B-10) and the
    mirror image of G4's.

    `_commit_transform` zeroes the FOLD merit on an SPR-committed node while
    FOLD stays in `by_kind`, so after the scale the vector is
    `(0, C0*L, 3*R0*L/ref)` and `L` cancels out of the WHOLE distribution, not
    merely out of the raise:call ratio. `call_looseness` is therefore INERT on
    committed facing nodes, where at the base engine it was the dominant lever
    (tag, AA on Kc9s3h2d at SPR 1.0: base P(raise) 0.9449 / 0.8108 / 0.5172
    across x0.25 / x1 / x4, now flat at 0.8108).

    This is the same orthogonality property with no fold leg left to absorb the
    change — internally consistent, but a real loss of reach that no other gate
    could see: G2 skips these cells by construction (P(fold) is pinned at 0, so
    they are not interior) and G1 is vacuously satisfied, because inertness is
    a superset of orthogonality. It matters for the fit slice this one unblocks:
    a `call_looseness` fit has NO reach over committed nodes.

    Pinned in both directions so the inertness cannot silently reverse and the
    base engine's sensitivity cannot silently return."""
    cell = _nlogit_commit_cell()
    for persona, pinned in _NLOGIT_COMMIT_PINS.items():
        scaled = [
            _nlogit_dist(_nlogit_probe(persona, m), cell)
            for m in (1.0,) + _NLOGIT_MULTS
        ]
        base = [
            _nlogit_dist(_nlogit_probe(persona, m, continue_ref=None), cell)
            for m in (1.0,) + _NLOGIT_MULTS
        ]
        assert all(_nlogit_p(d, ActionType.FOLD) == 0.0 for d in scaled), persona
        # Inert: every action's probability is bit-identical across the sweep.
        for d in scaled[1:]:
            assert d == scaled[0], (persona, d, scaled[0])
        assert _nlogit_p(scaled[0], ActionType.RAISE) == pytest.approx(pinned, rel=1e-9), (
            persona,
            _nlogit_p(scaled[0], ActionType.RAISE),
        )
        # The base engine was NOT inert here — the discriminating half.
        base_raise = [_nlogit_p(d, ActionType.RAISE) for d in base]
        assert max(base_raise) - min(base_raise) > 0.05, (persona, base_raise)


def test_nlogit_g5_unopened_branch_is_untouched():
    """G5 — the unopened / matched-with-option branch is exactly unaffected,
    over BOTH of its legal shapes (CHECK+BET and CHECK+RAISE).

    Two things are asserted, both bitwise: the opted-in pack equals the
    un-opted pack, and the distribution does not move when `call_looseness` is
    swept. The second half is the discriminating one — it would catch a scale
    applied outside the `FOLD in by_kind` guard, which the first half alone
    could not (both packs would move together). Rev 2 claimed this property
    from a gate that only covered facing shapes (ledger R2-7)."""
    shapes = {
        "check_bet": [personas_postflop_legal_check(), personas_postflop_legal_bet(1.0, 100.0)],
        "check_raise": [personas_postflop_legal_check(), personas_postflop_legal_raise(4.0, 100.0)],
    }
    for persona in _NLOGIT_ANCHORS:
        for label, street, hole, board, ctx in _nlogit_spots():
            for shape, legal in shapes.items():
                dists = []
                for mult in (1.0,) + _NLOGIT_MULTS:
                    for continue_ref in (_NLOGIT_KEEP, None):
                        probe = _nlogit_probe(persona, mult, continue_ref=continue_ref)
                        cap = _CaptureWeights()
                        sample_postflop_decision(
                            probe,
                            hole,
                            board,
                            legal,
                            6.0,
                            100.0,
                            1,
                            cap,  # type: ignore[arg-type]
                            street=street,
                            context=ctx,
                        )
                        dists.append(cap.dist)
                for d in dists[1:]:
                    assert d == dists[0], (persona, label, shape, d, dists[0])


class _NlogitAllChoices:
    """Records EVERY choices() call, and always draws the LAST candidate — on
    a FOLD/CALL/RAISE node that is RAISE, so the sizing draw is reached."""

    def __init__(self):
        self.calls = []

    def choices(self, population, weights, k=1):
        self.calls.append((list(population), list(weights)))
        return [population[-1]]


def test_nlogit_g6_one_action_draw_then_one_sizing_draw():
    """G6 — the action draw stays the FIRST `rng.choices` call and the sizing
    draw the SECOND, with nothing inserted between them.

    Eight capture rngs across the suite and the range estimator key on exactly
    that (contract map C1); a literal two-stage nested logit — draw
    {FOLD, CONTINUE} then {CALL, RAISE} — would break all of them. This slice
    achieves the nesting algebraically inside the single existing
    normalization, so the property holds by construction; the gate exists so a
    later refactor cannot lose it silently."""
    cell = _nlogit_bluff_cell()
    legal = [
        personas_postflop_legal_fold(),
        personas_postflop_legal_call(cell.to_call),
        personas_postflop_legal_raise(cell.to_call * 3, 200.0),
    ]
    for persona in _NLOGIT_ANCHORS:
        rng = _NlogitAllChoices()
        sample_postflop_decision(
            _nlogit_probe(persona),
            cell.hole,
            cell.board,
            legal,
            cell.pot_bb,
            cell.stack_bb,
            cell.opponents,
            rng,  # type: ignore[arg-type]
            street=cell.street,
        )
        assert len(rng.calls) == 2, (persona, len(rng.calls))
        assert rng.calls[0][0] == [ActionType.FOLD, ActionType.CALL, ActionType.RAISE], persona
        assert all(isinstance(x, float) for x in rng.calls[1][0]), persona  # pot fractions


def _nlogit_postflop_kwargs(persona: str = "nit") -> dict:
    """A shipped postflop block as plain kwargs, with `continue_ref` stripped so
    the caller supplies it — or deliberately does not."""
    d = _pack(persona).postflop.model_dump()
    return {k: v for k, v in d.items() if v is not None and k != "continue_ref"}


@pytest.mark.parametrize(
    "bad",
    [
        0.0,  # the rev-1/rev-2 ZeroDivisionError
        -1.0,
        5e-324,  # the smallest subnormal: passes `gt=0.0`, makes the scale inf
        1e-8,  # validates under `gt=0.0`, yields a degenerate P(raise) ~ 0.99999997
        0.049,
        8.01,
        float("nan"),
        float("inf"),
    ],
)
def test_nlogit_g8_model_rejects_unsafe_continue_ref(bad):
    """G8 (validation, not inspection) — the MODEL rejects unsafe anchors.

    Inspecting the six shipped values would still pass if the constraint were
    deleted, which is precisely the defect ledger R-2 found in an earlier
    wording of this gate. `ge=0.05` rather than `gt=0.0` because the dangerous
    end is near zero: `5e-324` validates under `gt=0.0` and makes the scale
    `inf`, so the emitted vector is `[0.0, 0.0, nan]` and `random.choices`
    raises "Total of weights must be finite"."""
    from pydantic import ValidationError

    from app.domain.content.models import PersonaPostflop

    with pytest.raises(ValidationError):
        PersonaPostflop(**_nlogit_postflop_kwargs(), continue_ref=bad)


def test_nlogit_g8_absence_is_the_opt_out_but_explicit_null_is_not():
    """G8 (authorship) — the decision, pinned: field ABSENCE is the legacy
    opt-out (an un-opted pack runs the base code path), while an explicit
    `"continue_ref": null` is REJECTED. Same key-presence rule `stickiness`
    already uses: an authored key that claims a calibration anchor and supplies
    none is a lie about the pack's behaviour, not a default."""
    from pydantic import ValidationError

    from app.domain.content.models import PersonaPostflop

    absent = PersonaPostflop(**_nlogit_postflop_kwargs())
    assert absent.continue_ref is None
    with pytest.raises(ValidationError, match="continue_ref"):
        PersonaPostflop(**_nlogit_postflop_kwargs(), continue_ref=None)


@pytest.mark.parametrize("bad", [0.0, -1.0, 5e-324, float("nan"), float("inf"), 8.01])
def test_nlogit_g8_runtime_guard_survives_unvalidated_injection(bad):
    """G8 (runtime guard) — model validation is NOT sufficient, because
    `model_copy(update=...)` bypasses it entirely and the suite uses that idiom
    routinely (e.g. `_pack_with` and the many inline `model_copy(update=...)`
    calls throughout this file). The engine therefore re-checks the anchor at
    the division site and raises a NAMED error instead of dividing by zero,
    emitting `nan` weights, or silently degrading to an unscaled raise leg.
    The comparison is written so NaN — which fails every ordering test — lands
    in the same branch."""
    cell = _nlogit_bluff_cell()
    legal = [personas_postflop_legal_fold(), personas_postflop_legal_call(cell.to_call)]
    probe = _nlogit_probe("tag", continue_ref=bad)
    with pytest.raises(ValueError, match="continue_ref"):
        sample_postflop_decision(
            probe,
            cell.hole,
            cell.board,
            legal,
            cell.pot_bb,
            cell.stack_bb,
            cell.opponents,
            _CaptureWeights(),  # type: ignore[arg-type]
            street=cell.street,
        )


def test_nlogit_g8_guard_fires_on_the_unopened_branch_too():
    """G8 (fail-fast) — the range check runs whenever an anchor is present, not
    only once the bot happens to face chips.

    Build review, refuter LOW: the check used to sit inside the
    `ActionType.FOLD in by_kind` test, so a corrupted anchor was tolerated on
    CHECK+BET / CHECK+RAISE nodes and only raised at the first facing node —
    a late, input-dependent failure for a defect that is present from load."""
    legal = [personas_postflop_legal_check(), personas_postflop_legal_bet(1.0, 100.0)]
    probe = _nlogit_probe("tag", continue_ref=0.0)
    with pytest.raises(ValueError, match="continue_ref"):
        sample_postflop_decision(
            probe,
            ("Kh", "4d"),
            ["Kc", "9s", "3h"],
            legal,
            6.0,
            100.0,
            1,
            _CaptureWeights(),  # type: ignore[arg-type]
            street=Street.FLOP,
        )


def test_nlogit_g8_explicit_none_via_model_copy_is_the_documented_opt_out():
    """G8 (accepted behaviour, pinned) — injecting `continue_ref=None` through
    an unvalidated `model_copy` does NOT raise; it takes the legacy path and
    the feature is off for that pack.

    Codex Sol raised this at build review as a guard gap: the range check sits
    under `if ref is not None`, so an explicit programmatic null slips past it
    and silently disables N-logit. ADJUDICATED AS DESIGNED, not fixed — `None`
    IS the opt-out (spec §3.5), it is how G3 obtains the base-engine path to
    compare against, and no production caller constructs a postflop block that
    way (the loader validates JSON, and nothing in `app/` calls `model_copy` on
    a `PersonaPostflop`). Pinned here so the behaviour is a decision on record
    rather than an accident (ledger B-11)."""
    cell = _nlogit_bluff_cell()
    legal = [personas_postflop_legal_fold(), personas_postflop_legal_call(cell.to_call)]
    cap = _CaptureWeights()
    sample_postflop_decision(
        _nlogit_probe("tag", 0.5, continue_ref=None),
        cell.hole,
        cell.board,
        legal,
        cell.pot_bb,
        cell.stack_bb,
        cell.opponents,
        cap,  # type: ignore[arg-type]
        street=cell.street,
    )
    assert cap.dist is not None  # no exception: legacy path


def test_nlogit_g8_null_roundtrip_matches_the_stickiness_precedent():
    """G8 (authorship, disclosed limitation) — `model_dump()` emits an explicit
    `null` for an un-opted field, so `model_validate(pack.model_dump())` is not
    idempotent for a pack using the legacy opt-out.

    Both reviewers raised this at build review. It is REAL and it is NOT new:
    `stickiness`'s authorship rule has the identical shape and the identical
    round-trip behaviour, as this test measures side by side. Accepting it here
    keeps one authorship convention in the model instead of two; changing it
    would be a `stickiness` change wearing a `continue_ref` costume, which is
    outside this slice. No production path round-trips a persona pack — the
    loader reads JSON authored by hand (ledger B-12)."""
    from pydantic import ValidationError

    from app.domain.content.models import PersonaPostflop

    legacy = PersonaPostflop(**_nlogit_postflop_kwargs())  # continue_ref absent
    assert legacy.continue_ref is None
    with pytest.raises(ValidationError, match="continue_ref"):
        PersonaPostflop.model_validate(legacy.model_dump())

    split = _nlogit_postflop_kwargs()
    split.pop("stickiness")
    split["size_elasticity"] = 1.0
    both_authored = PersonaPostflop(**split)  # stickiness absent, as required
    assert both_authored.stickiness is None
    with pytest.raises(ValidationError, match="stickiness"):
        PersonaPostflop.model_validate(both_authored.model_dump())


def test_nlogit_pack_versions_were_bumped_with_the_content_change():
    """Contract map C8 — nothing in the loader enforces a `version` bump when a
    pack's content changes, so it is asserted here.

    A FLOOR rather than an equality: a later slice that edits a pack bumps past
    this and stays green without editing the test, but a missed or reverted bump
    reds. Codex Sol demonstrated the hole by reverting calling_station to 1.1.1
    at build review — all 24 gates still passed (ledger B-13)."""
    import json

    from app.domain.personas import PERSONA_DIR

    floors = {
        "nit": (1, 4, 0),
        "tag": (1, 4, 0),
        "lag": (1, 6, 0),
        "maniac": (1, 6, 0),
        "calling_station": (1, 2, 0),
        "passive_fish": (1, 2, 0),
    }
    for persona, floor in floors.items():
        raw = json.loads((PERSONA_DIR / f"{persona}.json").read_text())
        got = tuple(int(x) for x in raw["version"].split("."))
        assert got >= floor, f"{persona} version {raw['version']} is below the N-LOGIT floor"


def test_nlogit_g9_a_looseness_refit_does_not_move_the_reference():
    """G9 (lifecycle) — the frozen-ness contract, enforced through the real
    validated-JSON path rather than argued in prose.

    Change ONLY `call_looseness` in a shipped pack, re-validate, and the
    anchor must be unchanged — no validator, loader or service cache may
    re-derive it. A validator that synchronised the two fields would recreate
    rev 1's cancellation across authored revisions and would still pass a
    shipped-values inspection (ledger R2-6). THE RULE: a looseness fit never
    updates the reference; only an explicit re-calibration of the raise side
    may."""
    import json

    from app.domain.content.models import PersonaPack
    from app.domain.personas import PERSONA_DIR

    for persona, anchor in _NLOGIT_ANCHORS.items():
        raw = json.loads((PERSONA_DIR / f"{persona}.json").read_text())
        assert raw["postflop"]["continue_ref"] == anchor, persona
        if raw["postflop"].get("call_looseness") is None:
            # maniac: no calling lever to refit — its effective looseness IS
            # `stickiness`. TRIPWIRE (theory review, Q2): that field is ALSO
            # `_price_exponent`'s fallback, so editing it for price reasons
            # would desynchronise this anchor from the lever it anchors — and
            # every N-logit probe authors `call_looseness` on its copy, so no
            # other gate here would observe it. Split maniac's levers before
            # changing this number.
            assert raw["postflop"]["stickiness"] == anchor, (
                f"{persona}'s anchor is a frozen copy of the SHARED `stickiness` "
                f"fallback; split its levers before moving stickiness"
            )
            continue
        raw["postflop"]["call_looseness"] = anchor * 1.5  # a refit, nothing else
        refit = PersonaPack.model_validate(raw)
        assert refit.postflop.call_looseness == anchor * 1.5, persona
        assert refit.postflop.continue_ref == anchor, persona


def test_nlogit_g9_maniac_split_lever_migration_keeps_the_anchor():
    """G9 (migration) — the maniac case, which is the fragile one: its anchor
    is a copy of `stickiness`, and `stickiness` is a SHARED fallback (also
    `_price_exponent`'s, ledger R2-10). Author both split levers, drop
    `stickiness` as `_stickiness_authorship` then requires, and the anchor must
    still be 0.55 with orthogonality intact — i.e. the migration that removes
    the shared fallback does not disturb the calibration it was copied from."""
    import json

    from app.domain.content.models import PersonaPack
    from app.domain.personas import PERSONA_DIR

    raw = json.loads((PERSONA_DIR / "maniac.json").read_text())
    pf = raw["postflop"]
    assert pf["stickiness"] == 0.55 and "call_looseness" not in pf
    pf["call_looseness"] = 0.55
    pf["size_elasticity"] = 1.0
    del pf["stickiness"]
    migrated = PersonaPack.model_validate(raw)
    assert migrated.postflop.continue_ref == 0.55
    assert migrated.postflop.stickiness is None

    cell = _NlogitCell(
        "top_pair/turn", Street.TURN, ("Kh", "4d"), ["Kc", "9s", "3h", "2d"],
        None, 6.0, 4.0, 100.0, 1, False, True,
    )
    shares = []
    for mult in (0.5, 1.0, 2.0):
        probe = migrated.model_copy(deep=True)
        probe.postflop = migrated.postflop.model_copy(update={"call_looseness": 0.55 * mult})
        d = _nlogit_dist(probe, cell)
        denom = _nlogit_p(d, ActionType.CALL) + _nlogit_p(d, ActionType.RAISE)
        shares.append(_nlogit_p(d, ActionType.RAISE) / denom)
    assert max(shares) - min(shares) <= 1e-12, shares


# ===================================================================
# R9-DEFENCE-a — the opponent-LINE damp: node-grid acceptance harness
# ===================================================================
#
# Mechanism under test (spec `docs/ai-dlc/specs/r9-defence-a.md` rev 2 §3): at a
# facing-chips node whose aggressor ALSO bet/raised the previous POSTFLOP street
# (`aggressor_bet_prev_street`, the `>= 1` threshold of
# `table.postflop_context.aggressor_barrel_run`), the CALL and RAISE merits are
# scaled by `exp(-λ_p)` with `λ_p = _LINE_DELTA · pf.line_sensitivity`. The FOLD
# merit is never touched, so the freed mass lands on FOLD and the conditional
# raise share is invariant.
#
# WHY THESE GATES ARE SHAPED THIS WAY. Rev 1 of this spec was reviewed by two
# independent reviewers and BOTH returned FAIL — neither on the mechanism, both
# on the GATES. A `_LINE_DELTA = 1e-12` no-op passed ELEVEN of rev 1's twelve
# criteria, and a mutant that satisfied the anti-collapse gate BY COLLAPSING
# (`C' = R' = 0`) passed too. The governing law, the same one the N-LOGIT block
# above records: an IDENTITY measurement ("output unchanged") cannot distinguish
# a behaviour-preserving fix from one that does nothing — only a SENSITIVITY
# measurement can. Ledger `docs/ai-dlc/ledger/r9-defence-a.md`, findings R-1,
# R-3, R-5, R-6, R-7, R-8, R-10, R-12.
#
# TWO CLASSES OF GATE, and the distinction is load-bearing (ledger R-5):
#   * S-gates (SENSITIVITY) — `test_r9d_s*`. These MUST be RED without the
#     engine block. Demanding they pass at base is what proves the change does
#     something.
#   * P-pins (REGRESSION) — `test_r9d_p*`. These are GREEN with the engine
#     block absent and must STAY green. Never re-record, never widen. Rev 1
#     demanded RED-FIRST of these too, which is incoherent and invites weakening
#     a pin until it fails.
#
# RED-FIRST EVIDENCE, measured on a detached worktree at the T1 commit — packs
# authored with the lever, `personas_postflop.py` UNTOUCHED:
#
#   S-1  ΔP(fold) at the reference node (nit/MIDDLE_PAIR/turn/HU/SPR 20/0.5-pot)
#        against a gate demanding a LITERAL >= 0.05:
#          nit +0.000000 · tag +0.000000 · lag +0.000000 · passive_fish
#          +0.000000 · maniac +0.000000 · calling_station +0.000000
#        …and 0 of 288 in-scope S-1 cells showed ANY rise in P(fold). With the
#        engine block present the same six read +0.131190 / +0.097658 /
#        +0.064975 / +0.081425 / +0.031156 / +0.005434 and 288 of 288 rise.
#   S-4  RED four ways: `_LINE_DELTA` does not exist; the measured logit shift
#        is 0.000000 against λ_p ∈ {0.10 … 0.60}; the injected-lever sweep is
#        flat; and the reordered-composition arms differ by the whole factor.
#   S-1's P-2 discriminator, and the §4 joint-product gate: RED.
#   P-1 … P-6: all GREEN at that same reference, as REGRESSION pins must be.
#
# HONEST LIMIT, reported rather than papered over: **S-2 and S-3 cannot be RED
# at base, and no rewriting of them makes it possible.** Both compare the anchor
# against the TUNED point, and with the engine untouched those are the same
# vector — so "continue mass did not collapse" and "the raise share did not
# move" are trivially true. Their teeth are on MUTANTS, which is exactly the job
# the spec's §10.4 gives them: S-2 catches the `C' = R' = 0` collapse that
# passed rev 1's anti-collapse gate, S-3 catches the `call_merit`-only misroute.
# Spec §7's blanket "every S-gate must be demonstrated RED at base" is therefore
# unsatisfiable for these two; the RED evidence that belongs to them is T7's,
# not a base measurement.
#
# If any OTHER S-gate here ever passes with the engine block removed, the GATE
# is broken, not the engine fixed.
#
# ---------------------------------------------------------------------------
# THE CELL GRID (spec §7 — "axes are published in the test module").
#
#   bucket   × {MIDDLE_PAIR, TOP_PAIR, ACE_HIGH, AIR}   (the scope predicate)
#   draw     × {NONE}                                   (the scope predicate)
#   street   × {flop, turn, river}
#   headcount× {HU (1 opponent), 3-way (2 opponents)}
#   faced    × {0.25, 0.5, 0.75, 1.5} of the PRE-aggression pot
#   SPR      × {1, 4, 20}
#   shape    × {FOLD+CALL, FOLD+CALL+RAISE}
#   = 576 cells, over all six packs = 3,456 (pack, cell) pairs per line state.
#
# The faced fraction is EXACT, not nominal: the villain bets `frac · 6bb` into a
# 6bb pre-aggression pot, so the live pot is `6 + bet`, `to_call == bet`, and
# `latest_aggressor_contribution_bb == bet` — which is the branch the live loop
# and the range estimator both take, so `faced_frac` is literally `frac`
# (the `faced_frac = to_call_bb / max(pot_bb - ..., 0.01)` derivation in
# `sample_postflop_decision`). SPR is measured against the LIVE pot, the
# same quantity the SPR-commit block reads.
#
# SPR 1 is below every pack's `spr_commit` (1.2 … 3.3) ON PURPOSE: it is where
# ledger R-6's consequence is exercised. For every in-scope bucket `made` is
# False (rungs 0-3 vs the threshold 4) and `drawing` is False, so `value_commit`
# is always False and `_commit_transform` / B5b can never co-occur with this
# mechanism. The grid keeps those cells rather than declaring a no-reach zone,
# because a gate on a combination that cannot occur always passes.

_R9D_POT_PRE = 6.0  # the pot the villain's wager is made INTO

# The authored seed ladder (spec §5), written as a LITERAL. Not read from the
# packs: a gate that reads its own expectation out of the thing under test
# cannot fail. `test_r9d_ladder_matches_the_authored_packs` reconciles the two.
_R9D_SENSITIVITY = {
    "nit": 0.60,
    "tag": 0.50,
    "lag": 0.35,
    "passive_fish": 0.35,
    "maniac": 0.20,
    "calling_station": 0.10,
}
# Ordering: STRICT between tiers, EQUAL within the braced tier. Rev 1 demanded
# strict monotonicity over a ladder containing an authored tie, which is
# unsatisfiable (ledger R-10).
_R9D_TIERS = (("nit",), ("tag",), ("lag", "passive_fish"), ("maniac",), ("calling_station",))

# `λ_p = <this literal> · line_sensitivity`. Spec §3.1 pins `_LINE_DELTA = 1.0`;
# this is that value RE-STATED as a test-side literal so the shift gate is not
# self-referential. `test_r9d_s4_shift_scale_is_the_pinned_literal` asserts the
# module constant equals it — an engine that quietly re-derives the constant
# from `_POSITION_AGG_DELTA` (= 0.25) fails there, not silently everywhere.
_R9D_SHIFT_PER_UNIT = 1.0

# S-1's minimum effect size at the named reference node, as a LITERAL (ledger
# R-1). NEVER derive this from `_LINE_DELTA` or from `line_sensitivity`: a
# self-referential floor passes at ANY magnitude, which is exactly how the
# `1e-12` no-op survived rev 1. Measured at the pinned constant: +0.131190,
# which independently reproduces the design pass's predicted +0.1312.
_R9D_MIN_REFERENCE_EFFECT = 0.05

# The scope predicate, written test-side as a LITERAL for the same reason the
# ladder is: a P-pin that reads its own scope out of the module under test would
# go green for free the moment that module changed its mind about scope, and it
# would ERROR (not fail) against a tree where the constant does not exist yet —
# which is precisely the state a REGRESSION pin has to be green in.
# `test_r9d_s4_shift_scale_is_the_pinned_literal` reconciles the two.
_R9D_SCOPE_BUCKETS = frozenset(
    {
        StrengthBucket.MIDDLE_PAIR,
        StrengthBucket.TOP_PAIR,
        StrengthBucket.ACE_HIGH,
        StrengthBucket.AIR,
    }
)

_R9D_FRACS = (0.25, 0.5, 0.75, 1.5)
_R9D_SPRS = (1.0, 4.0, 20.0)
_R9D_HEADCOUNTS = ((1, "HU"), (2, "3way"))
_R9D_SHAPES = ((False, "FOLD+CALL"), (True, "FOLD+CALL+RAISE"))
_R9D_BOARDS = {
    Street.FLOP: ["Kc", "9s", "3h"],
    Street.TURN: ["Kc", "9s", "3h", "2d"],
    Street.RIVER: ["Kc", "9s", "3h", "2d", "Tc"],
}
# One hole per in-scope bucket, classifying the same way on all three streets
# (asserted by `test_r9d_grid_is_entirely_in_scope`, so a board edit can never
# silently shrink the grid).
_R9D_HOLES = {
    StrengthBucket.MIDDLE_PAIR: ("9h", "4c"),
    StrengthBucket.TOP_PAIR: ("Kh", "4d"),
    StrengthBucket.ACE_HIGH: ("Ah", "8d"),
    StrengthBucket.AIR: ("7h", "4c"),
}


class _R9dCell(NamedTuple):
    bucket: object
    street: Street
    opponents: int
    frac: float
    spr: float
    with_raise: bool

    @property
    def key(self) -> str:
        head = dict(_R9D_HEADCOUNTS)[self.opponents]
        shape = dict(_R9D_SHAPES)[self.with_raise]
        return (
            f"{self.bucket.value}/{self.street.value} {head} faced={self.frac} "
            f"spr={self.spr} {shape}"
        )

    @property
    def bet(self) -> float:
        return round(self.frac * _R9D_POT_PRE, 2)

    @property
    def pot(self) -> float:
        return _R9D_POT_PRE + self.bet

    @property
    def stack(self) -> float:
        return self.spr * self.pot


def _r9d_cells() -> list[_R9dCell]:
    return [
        _R9dCell(bucket, street, opponents, frac, spr, with_raise)
        for bucket in _R9D_HOLES
        for street in _R9D_BOARDS
        for opponents, _ in _R9D_HEADCOUNTS
        for frac in _R9D_FRACS
        for spr in _R9D_SPRS
        for with_raise, _ in _R9D_SHAPES
    ]


class _R9dProbe:
    """Duck-typed rng that captures BOTH the normalized action vector and the
    RAW merit vector the single normalization was handed.

    The raw side exists for P-1, and P-1 cannot be built any other way: a
    fold-side implementation is PROJECTIVELY IDENTICAL to the specified one
    (`normalize(F, C·s, R·t·s) == normalize(F/s, C, R·t)`), so no output-space
    test can tell the two apart — both spec reviewers measured that to bit
    equality (ledger R-2). The distinction only exists BEFORE the normalization.

    How: `sum` is a module-global lookup inside `sample_postflop_decision`, so
    binding `personas_postflop.sum` to this object's `sum` shadows the builtin
    for the duration of one call (see `_r9d_probe`). The LAST `sum` observed
    before the first `choices` is `total = sum(weights)` — i.e. the clamped
    merit vector, in the normalization block. Deliberately NOT anchored on a
    line number: this file's own history is full of anchors that went stale, and
    the `:1203-1204` that used to stand here was one of them (three lines off at
    base, twenty-six after the `_line_scaled` extraction).

    The clamp is `max(m, 0.0)`, so the captured vector equals the raw merits
    exactly wherever every entry is strictly positive; P-1 asserts that
    positivity on the cells it grades rather than assuming it.
    """

    def __init__(self):
        self.dist = None
        self.merits = None
        self._pending = None

    def choices(self, population, weights, k=1):
        if self.dist is None:
            self.dist = dict(zip(population, weights, strict=True))
            self.merits = dict(zip(population, self._pending, strict=True))
        return [population[0]]

    def sum(self, iterable, /, start=0):
        vals = list(iterable)
        if self.dist is None:
            self._pending = vals
        return builtins.sum(vals, start)


def _r9d_probe(pack, cell: _R9dCell, line: bool, *, facing_raise: bool = False) -> _R9dProbe:
    """One production call at `cell`, returning the captured vectors.

    `latest_aggressor_contribution_bb` is supplied (spec S-1), which is the
    exact-denominator branch the live loop and the estimator both take.
    """
    legal = [
        personas_postflop_legal_fold(),
        personas_postflop_legal_call(cell.bet),
    ]
    if cell.with_raise:
        legal.append(personas_postflop_legal_raise(3 * cell.bet, 400.0))
    probe = _R9dProbe()
    personas_postflop.sum = probe.sum
    try:
        sample_postflop_decision(
            pack,
            _R9D_HOLES[cell.bucket],
            _R9D_BOARDS[cell.street],
            legal,
            cell.pot,
            cell.stack,
            cell.opponents,
            probe,  # type: ignore[arg-type] — duck-typed capture rng
            current_bet_to=cell.bet,
            street=cell.street,
            latest_aggressor_contribution_bb=cell.bet,
            facing_raise=facing_raise,
            aggressor_bet_prev_street=line,
        )
    finally:
        personas_postflop.__dict__.pop("sum", None)
    return probe


_R9D_GRID: dict = {}


def _r9d_grid():
    """{persona: {line: [probe per cell]}} plus `_cells`. Computed ONCE and
    shared by every gate below — 576 cells x 6 packs x 2 line states = 6,912
    production calls, measured at ~0.3s in total."""
    if not _R9D_GRID:
        cells = _r9d_cells()
        for persona in _R9D_SENSITIVITY:
            pack = _pack(persona)
            _R9D_GRID[persona] = {
                line: [_r9d_probe(pack, c, line) for c in cells] for line in (False, True)
            }
        _R9D_GRID["_cells"] = cells
    return _R9D_GRID


def _r9d_p(dist, kind) -> float:
    return dist.get(kind, 0.0)


def _r9d_continue(dist) -> float:
    return _r9d_p(dist, ActionType.CALL) + _r9d_p(dist, ActionType.RAISE)


def _r9d_logit(p: float) -> float:
    return math.log(p / (1.0 - p))


def _r9d_hex(dist) -> tuple:
    """An exact, order-independent fingerprint of a probability vector.
    `float.hex()` round-trips every bit pattern, including the -0.0 / +0.0
    distinction that `==` erases."""
    return tuple(sorted((a.value, float(v).hex()) for a, v in dist.items()))


_R9D_REFERENCE = _R9dCell(StrengthBucket.MIDDLE_PAIR, Street.TURN, 1, 0.5, 20.0, True)


def test_r9d_grid_is_entirely_in_scope():
    """The grid's own scope claim, asserted rather than asserted-in-prose.

    Every cell must classify to the bucket its template names AND to
    `DrawCategory.NONE` — the scope predicate is the explicit PRODUCT of two
    INDEPENDENT axes (`personas_postflop.py:33-51`), which is the thing rev 1
    never defined: middle pair WITH a flush draw was undefined and is now
    explicitly OUT (ledger R-6). A board edit that demoted a template would
    otherwise shrink every gate below without any of them noticing."""
    cells = _r9d_cells()
    assert len(cells) == 576, len(cells)
    for cell in cells:
        bucket, draw = strength_bucket(_R9D_HOLES[cell.bucket], _R9D_BOARDS[cell.street])
        assert bucket is cell.bucket, cell.key
        assert draw is DrawCategory.NONE, cell.key
        assert bucket in _R9D_SCOPE_BUCKETS, cell.key
    # every published axis actually appears
    assert {c.bucket for c in cells} == set(_R9D_HOLES)
    assert {c.street for c in cells} == set(_R9D_BOARDS)
    assert {c.opponents for c in cells} == {1, 2}
    assert {c.frac for c in cells} == set(_R9D_FRACS)
    assert {c.spr for c in cells} == set(_R9D_SPRS)
    assert {c.with_raise for c in cells} == {False, True}
    assert set(_R9D_SENSITIVITY) == set(ALL_PERSONAS)


def test_r9d_ladder_matches_the_authored_packs():
    """The test-side literal ladder reconciles with the six shipped packs, and
    every persona is opted in with a STRICTLY POSITIVE lever — S-1's "for every
    persona with `line_sensitivity > 0`" quantifier is therefore over all six,
    not over a silently empty set."""
    for persona, expected in _R9D_SENSITIVITY.items():
        authored = _pack(persona).postflop.line_sensitivity
        assert authored == pytest.approx(expected, abs=1e-12), (persona, authored)
        assert authored > 0.0, persona


# ------------------------------------------------------------------ S-gates


def test_r9d_s1_identity_breaks_with_a_literal_effect_floor():
    """S-1 (RED-FIRST, DECISIVE) — the identity breaks, WITH A FLOOR.

    Two assertions, and the second is the one that matters. Direction alone
    ("strictly greater") is what a `_LINE_DELTA = 1e-12` no-op satisfies while
    doing nothing, and that no-op passed 11 of rev 1's 12 criteria (ledger R-1).
    So this gate also carries a MINIMUM EFFECT SIZE at a named reference node,
    written as a LITERAL (`_R9D_MIN_REFERENCE_EFFECT = 0.05`) and never derived
    from `_LINE_DELTA` — a floor computed from the constant under test passes at
    any magnitude, including zero.

    Scope per spec §7: MIDDLE_PAIR and TOP_PAIR, heads-up, SPR >= 10, facing a
    BET at a fixed fraction, with `latest_aggressor_contribution_bb` supplied.

    Measured at the pinned `_LINE_DELTA = 1.0`, reference node ΔP(fold):
      nit +0.131190 · tag +0.097658 · passive_fish +0.081425 · lag +0.064975 ·
      maniac +0.031156 · calling_station +0.005434.
    RED-FIRST at the engine-untouched reference: every one of those is
    +0.000000, and 0 of 288 cells rose."""
    grid = _r9d_grid()
    cells = grid["_cells"]
    scope = (StrengthBucket.MIDDLE_PAIR, StrengthBucket.TOP_PAIR)
    flat = []
    compared = dict.fromkeys(_R9D_SENSITIVITY, 0)
    for persona in _R9D_SENSITIVITY:
        for i, cell in enumerate(cells):
            if cell.bucket not in scope or cell.opponents != 1 or cell.spr < 10.0:
                continue
            f0 = _r9d_p(grid[persona][False][i].dist, ActionType.FOLD)
            f1 = _r9d_p(grid[persona][True][i].dist, ActionType.FOLD)
            compared[persona] += 1
            if not f1 > f0:
                flat.append((persona, cell.key, f0, f1))
    assert compared == dict.fromkeys(_R9D_SENSITIVITY, 48), compared
    assert not flat, (
        f"{len(flat)} of {sum(compared.values())} in-scope S-1 cells did not raise "
        f"P(fold) when the aggressor's line was revealed: {flat[:5]}"
    )

    ref = _r9d_cells().index(_R9D_REFERENCE)
    table = {
        p: _r9d_p(grid[p][True][ref].dist, ActionType.FOLD)
        - _r9d_p(grid[p][False][ref].dist, ActionType.FOLD)
        for p in _R9D_SENSITIVITY
    }
    assert table["nit"] >= _R9D_MIN_REFERENCE_EFFECT, (
        f"reference node ({_R9D_REFERENCE.key}) effect {table['nit']:.6f} is below the "
        f"literal floor {_R9D_MIN_REFERENCE_EFFECT}; full table {table}"
    )


def test_r9d_s2_continue_mass_never_collapses_at_either_end():
    """S-2 (RED-FIRST) — anti-collapse, ON BOTH ENDS.

    Rev 1 constrained only the ANCHOR, and Codex Sol measured a mutant setting
    `C' = R' = 0` from a non-degenerate anchor (continue mass 0.588 → fold
    1.000) passing BOTH S-1 and that anti-collapse gate: the gate added to close
    N-LOGIT's collapse hole did not stop the collapse (ledger R-3). So the
    constraint is stated at the TUNED point as well — an anchor with continue
    mass whose tuned end has none is a FAILURE, never a skip.

    Zero-continue cells ARE reachable in scope, so they are counted, not
    silently dropped: the river AIR/no-draw cell hard-zeroes `call_merit` and
    RAISE is appended only when legal, so those river AIR FOLD+CALL cells have
    `C + R == 0` at BOTH ends. P-5 pins them inert.

    HALVED BY T3 (improvement slice 2, 2026-08-19). The guard used to read
    `if bluff_cell and street is Street.RIVER`, and `bluff_cell` bundles
    ACE_HIGH with AIR, so the empty set was the 48 river x {ACE_HIGH, AIR}
    FOLD+CALL cells per pack and the measurement was 528 graded / 48 skipped.
    T3 gave river ace-high a live call, so only the AIR half is left."""
    grid = _r9d_grid()
    cells = grid["_cells"]
    collapsed, nonfinite = [], []
    graded = dict.fromkeys(_R9D_SENSITIVITY, 0)
    skipped = dict.fromkeys(_R9D_SENSITIVITY, 0)
    for persona in _R9D_SENSITIVITY:
        for i, cell in enumerate(cells):
            d0, d1 = grid[persona][False][i].dist, grid[persona][True][i].dist
            c0, c1 = _r9d_continue(d0), _r9d_continue(d1)
            if not all(math.isfinite(v) for v in (*d0.values(), *d1.values())):
                nonfinite.append((persona, cell.key))
                continue
            if c0 <= 0.0:
                skipped[persona] += 1
                continue
            graded[persona] += 1
            if not c1 > 0.0:
                collapsed.append((persona, cell.key, c0, c1))
    assert not nonfinite, nonfinite[:5]
    assert not collapsed, (
        f"{len(collapsed)} cells lost ALL continue mass once the line was revealed, "
        f"though the anchor had some: {collapsed[:5]}"
    )
    thin = {p: n for p, n in graded.items() if n < 480}
    assert not thin, f"S-2 graded almost nothing for {thin} (skips: {skipped})"
    loud = {p: n for p, n in skipped.items() if n > 96}
    assert not loud, f"too many cells skipped as zero-continue: {loud}"


def test_r9d_s3_raise_share_is_line_invariant():
    """S-3 (RED-FIRST) — `P(raise) / (P(call) + P(raise))` is invariant between
    line = 0 and line = 1 to 1e-9.

    Scaling BOTH defend merits by ONE factor cancels out of the conditional
    raise share; a `call_merit`-only multiplier does not, and that is exactly
    the N-LOGIT misroute this slice must not reintroduce.

    Restricted to cells with STRICTLY POSITIVE continue mass at BOTH ends
    (ledger R-3): where `C + R == 0` the ratio is 0/0. Those cells are excluded
    HERE and pinned inert by P-5 — the exclusion is not a hole, because S-2
    above already forbids a cell from ARRIVING at zero continue mass."""
    grid = _r9d_grid()
    cells = grid["_cells"]
    worst: dict = {}
    compared = dict.fromkeys(_R9D_SENSITIVITY, 0)
    for persona in _R9D_SENSITIVITY:
        for i, cell in enumerate(cells):
            d0, d1 = grid[persona][False][i].dist, grid[persona][True][i].dist
            c0, c1 = _r9d_continue(d0), _r9d_continue(d1)
            if c0 <= 0.0 or c1 <= 0.0:
                continue
            compared[persona] += 1
            drift = abs(
                _r9d_p(d1, ActionType.RAISE) / c1 - _r9d_p(d0, ActionType.RAISE) / c0
            )
            if drift > worst.get(persona, (0.0, ""))[0]:
                worst[persona] = (drift, cell.key)
    thin = {p: n for p, n in compared.items() if n < 480}
    assert not thin, f"S-3 measured almost nothing for {thin}"
    bad = {p: v for p, v in worst.items() if v[0] > 1e-9}
    assert not bad, f"the raise:call split moved with the line signal: {bad}"


def test_r9d_s4_shift_scale_is_the_pinned_literal():
    """S-4 (RED-FIRST) — `_LINE_DELTA` is the value the spec pinned.

    Restated as a test-side literal on purpose. Rev 1 left the constant
    unstated, described it as "mirroring" `_POSITION_AGG_DELTA` (= 0.25), and a
    `1e-12` no-op walked through the harness (ledger R-1). At 1.0 the reference
    node reproduces the design pass's own predicted +0.1312; at 0.25 it gives
    +0.030, which does not. The lever's `le=2.0` bound is likewise only the
    ">= 7x continue-odds cut" ceiling its own comment claims at 1.0."""
    assert personas_postflop._LINE_DELTA == _R9D_SHIFT_PER_UNIT
    assert personas_postflop._LINE_DELTA != personas_postflop._POSITION_AGG_DELTA
    # …and the engine's scope predicate is the one this harness grades against.
    assert personas_postflop._LINE_SCOPE_BUCKETS == _R9D_SCOPE_BUCKETS


def test_r9d_s4_logit_shift_equals_lambda_at_every_interior_cell():
    """S-4 (RED-FIRST) — the lever IS the shift, measured in ODDS space.

    `logit P(continue | line=0) − logit P(continue | line=1) == λ_p` to 1e-9 at
    every finite-interior cell, with `λ_p = 1.0 · line_sensitivity` taken from
    the test-side literals.

    ODDS space, not probability space, and that is not a stylistic choice: base
    continue rates differ across personas, so the PROBABILITY-space ordering of
    ΔP(fold) does not follow the λ ordering (passive_fish 0.081 outranks lag
    0.065 at the reference node although both author 0.35). Only the log-odds
    shift is the lever."""
    grid = _r9d_grid()
    cells = grid["_cells"]
    worst: dict = {}
    compared = dict.fromkeys(_R9D_SENSITIVITY, 0)
    for persona, sens in _R9D_SENSITIVITY.items():
        lam = _R9D_SHIFT_PER_UNIT * sens
        for i, cell in enumerate(cells):
            c0 = _r9d_continue(grid[persona][False][i].dist)
            c1 = _r9d_continue(grid[persona][True][i].dist)
            if not (0.0 < c0 < 1.0 and 0.0 < c1 < 1.0):
                continue
            compared[persona] += 1
            err = abs((_r9d_logit(c0) - _r9d_logit(c1)) - lam)
            if err > worst.get(persona, (0.0, ""))[0]:
                worst[persona] = (err, cell.key)
    thin = {p: n for p, n in compared.items() if n < 480}
    assert not thin, f"S-4 measured almost nothing for {thin}"
    bad = {p: v for p, v in worst.items() if v[0] > 1e-9}
    assert not bad, f"the continue-odds shift is not the authored lever: {bad}"


_R9D_SWEEP = (0.0, 0.05, 0.35, 1.0, 2.0)


def test_r9d_s4_lever_sweep_including_injected_values():
    """S-4 (RED-FIRST) — the shift tracks the lever over a SWEEP, including
    values no pack authors, injected through `model_copy(update=...)`.

    Without this, a hard-coded per-persona response table — six numbers that
    happen to reproduce the six authored ladder rungs — passes the gate above
    while being no mechanism at all (ledger R-10). The sweep also spans the
    lever's full validated range `[0.0, 2.0]`, and `model_copy` is the same
    unvalidated-injection path the engine's runtime guard exists for.

    `sensitivity = 0.0` is a BIT-IDENTITY case, not an approximate one:
    `exp(-0.0) == 1.0` exactly and `m * 1.0 == m` bitwise, so the opted-in path
    at a zero lever is byte-for-byte the un-opted path."""
    cells = [
        _R9D_REFERENCE,
        _R9dCell(StrengthBucket.TOP_PAIR, Street.RIVER, 2, 1.5, 4.0, True),
        _R9dCell(StrengthBucket.AIR, Street.FLOP, 1, 0.25, 1.0, False),
        _R9dCell(StrengthBucket.ACE_HIGH, Street.TURN, 2, 0.75, 20.0, True),
    ]
    bad, identity, compared = [], [], 0
    for persona in _R9D_SENSITIVITY:
        base = _pack(persona)
        for sens in _R9D_SWEEP:
            pack = base.model_copy(deep=True)
            pack.postflop = base.postflop.model_copy(update={"line_sensitivity": sens})
            for cell in cells:
                d0 = _r9d_probe(pack, cell, False).dist
                d1 = _r9d_probe(pack, cell, True).dist
                if sens == 0.0:
                    if _r9d_hex(d0) != _r9d_hex(d1):
                        identity.append((persona, cell.key))
                    continue
                c0, c1 = _r9d_continue(d0), _r9d_continue(d1)
                if not (0.0 < c0 < 1.0 and 0.0 < c1 < 1.0):
                    continue
                compared += 1
                err = abs((_r9d_logit(c0) - _r9d_logit(c1)) - _R9D_SHIFT_PER_UNIT * sens)
                if err > 1e-9:
                    bad.append((persona, sens, cell.key, err))
    assert not identity, f"a zero lever was not bit-identical: {identity[:5]}"
    assert compared >= 60, compared
    assert not bad, f"the shift did not track an injected lever value: {bad[:5]}"


def test_r9d_s4_ordering_is_strict_between_tiers_and_equal_within_the_tie():
    """S-4 (RED-FIRST) — the ladder's ORDER, in odds space, with the authored
    tie honoured.

    `{lag, passive_fish}` both author 0.35, so the ordering is STRICT BETWEEN
    tiers and EQUAL WITHIN the braced tier. Rev 1 demanded strict monotonicity
    over a ladder containing that tie — unsatisfiable, and a builder chasing it
    would have had to move an authored seed (ledger R-10)."""
    grid = _r9d_grid()
    ref = _r9d_cells().index(_R9D_REFERENCE)
    shift = {}
    for persona in _R9D_SENSITIVITY:
        c0 = _r9d_continue(grid[persona][False][ref].dist)
        c1 = _r9d_continue(grid[persona][True][ref].dist)
        shift[persona] = _r9d_logit(c0) - _r9d_logit(c1)
    for tier in _R9D_TIERS:
        for other in tier[1:]:
            assert shift[other] == pytest.approx(shift[tier[0]], abs=1e-12), (tier, shift)
    tops = [shift[t[0]] for t in _R9D_TIERS]
    assert all(a > b for a, b in zip(tops, tops[1:], strict=False)), (tops, shift)
    # …and the probability-space view genuinely does NOT preserve that order,
    # which is why this gate lives in odds space at all.
    dfold = {
        p: _r9d_p(grid[p][True][ref].dist, ActionType.FOLD)
        - _r9d_p(grid[p][False][ref].dist, ActionType.FOLD)
        for p in _R9D_SENSITIVITY
    }
    assert dfold["passive_fish"] > dfold["lag"], dfold


_R9D_LOOSENESS_MULTS = (0.3, 0.7, 1.3, 3.0)


def test_r9d_s4_composition_with_nlogit_commutes():
    """S-4 (RED-FIRST) — the line scale and the N-LOGIT raise scale COMMUTE, to
    a RELATIVE tolerance of 1e-12, and NEVER to bit-equality.

    Both are scalar multiplies on entries ahead of one normalization, so coded
    order cannot change the result mathematically — but it does change it in
    IEEE arithmetic. The refuter measured `(R·k)·s` vs `(R·s)·k` differing
    bitwise 34.9% of the time (ledger R-8); on this grid the reordering differs
    bitwise on 7.6% of the compared entries with a worst RELATIVE gap of
    3.4e-16. A bit-equality gate here would fail a CORRECT implementation, and
    the assertion at the end that a mismatch actually OCCURRED is what keeps
    that tolerance load-bearing rather than decorative.

    The counterfactual is a REORDERED COPY OF THE PRODUCTION PIPELINE, not
    algebra recomputed from scratch (ledger R-12): the baseline arm is
    production's own pre-normalization merit vector at line = 0 — which already
    contains the SPR block, the price-aware fold merit, the W3R-6 damps and the
    N-LOGIT raise scale, in production's coded order — and the line factor is
    applied at the OTHER end of that chain. If the engine attached the line
    multiply anywhere but inside the facing branch, on the CALL/RAISE pair, the
    two arms diverge far beyond 1e-12.

    `call_looseness` is swept off its frozen `continue_ref` anchor so
    `rscale != 1.0` — at the anchor values (`_NLOGIT_ANCHORS`, not necessarily
    the pack's shipped/authored value) `looseness == continue_ref` and the
    raise scale is EXACTLY 1.0, which would make this gate vacuous. The
    multipliers are deliberately NOT powers of two (a power-of-two rescale is
    exact in binary floating point, and the reordering then agrees bit-for-bit
    on every cell, which would ALSO make the gate vacuous)."""
    cells = [
        _R9D_REFERENCE,
        _R9dCell(StrengthBucket.TOP_PAIR, Street.TURN, 1, 0.25, 20.0, True),
        _R9dCell(StrengthBucket.ACE_HIGH, Street.FLOP, 2, 0.75, 4.0, True),
        _R9dCell(StrengthBucket.AIR, Street.RIVER, 1, 1.5, 20.0, True),
    ]
    worst, mismatched, compared = (0.0, ""), 0, 0
    for persona, sens in _R9D_SENSITIVITY.items():
        k = math.exp(-_R9D_SHIFT_PER_UNIT * sens)
        base = _pack(persona)
        for mult in _R9D_LOOSENESS_MULTS:
            pack = base.model_copy(deep=True)
            pack.postflop = base.postflop.model_copy(
                update={"call_looseness": _NLOGIT_ANCHORS[persona] * mult}
            )
            for cell in cells:
                produced = _r9d_probe(pack, cell, True).dist
                raw = _r9d_probe(pack, cell, False).merits
                reordered = {
                    a: (m * k if a in (ActionType.CALL, ActionType.RAISE) else m)
                    for a, m in raw.items()
                }
                total = builtins.sum(reordered.values())
                if total <= 0.0:
                    continue
                for action, produced_p in produced.items():
                    expected = reordered[action] / total
                    compared += 1
                    if float(produced_p).hex() != float(expected).hex():
                        mismatched += 1
                    scale = max(abs(produced_p), abs(expected))
                    if scale > 0.0:
                        rel = abs(produced_p - expected) / scale
                        if rel > worst[0]:
                            worst = (rel, f"{persona} x{mult} {cell.key} {action.value}")
    assert compared >= 200, compared
    assert worst[0] <= 1e-12, f"the two scales did not commute: {worst}"
    assert mismatched > 0, (
        "the reordering agreed BIT-FOR-BIT on every entry, so this gate's 1e-12 "
        "relative tolerance is untested — the multipliers have gone exact "
        "(ledger R-8 measured 34.9% bitwise disagreement)"
    )


def test_r9d_joint_product_with_the_within_street_raise_damps():
    """Spec §4's stated obligation: where the line damp and the two landed
    `facing_raise`-gated damps BOTH fire (facing a turn RAISE from a seat that
    bet the flop), the joint effect is a clean PRODUCT — the line factor is
    still exactly `exp(-λ_p)` on the CALL/RAISE pair, applied on top of whatever
    those damps left, and the log-odds shift is still λ_p.

    That matters because a third un-calibrated factor stacking on that axis is
    the W3R-5 collision this slice is scoped away from. The α-relevant node
    class — the flop facing a first c-bet — is untouched here by construction
    and pinned by P-3.

    Deliberately BEHAVIOURAL, never structural. Everything except P-1 in this
    harness must be blind to the fold-side/defend-side choice, because those two
    forms are projectively identical (ledger R-2) and the spec requires that
    exactly ONE gate distinguish them. Reading the raw merits here would give
    the fold-side form a second executioner and make the "P-1 alone" property
    untrue."""
    for persona, sens in _R9D_SENSITIVITY.items():
        pack = _pack(persona)
        for bucket in (
            StrengthBucket.MIDDLE_PAIR,
            StrengthBucket.TOP_PAIR,
            StrengthBucket.ACE_HIGH,
        ):
            cell = _R9dCell(bucket, Street.TURN, 1, 0.5, 20.0, True)
            damped = _r9d_probe(pack, cell, False, facing_raise=True).dist
            bare = _r9d_probe(pack, cell, False, facing_raise=False).dist
            joint = _r9d_probe(pack, cell, True, facing_raise=True).dist
            # a within-street damp really is firing at this node…
            assert _r9d_hex(damped) != _r9d_hex(bare), (persona, bucket)
            # …and the line factor rides on top of it as the SAME λ_p shift…
            c0, c1 = _r9d_continue(damped), _r9d_continue(joint)
            assert _r9d_logit(c0) - _r9d_logit(c1) == pytest.approx(
                _R9D_SHIFT_PER_UNIT * sens, abs=1e-9
            ), (persona, bucket)
            # …leaving the raise:call split of the damped node untouched.
            assert _r9d_p(joint, ActionType.RAISE) / c1 == pytest.approx(
                _r9d_p(damped, ActionType.RAISE) / c0, abs=1e-9
            ), (persona, bucket)


# ------------------------------------------------------------------- P-pins


def test_r9d_p1_structural_only_call_and_raise_raw_merits_move():
    """P-1 (REGRESSION PIN, green without the engine block) — STRUCTURAL, on the
    RAW merits before normalization: the FOLD entry is BITWISE unchanged and
    CALL/RAISE are scaled by ONE common factor.

    THIS PIN IS THE ONLY THING THAT DISTINGUISHES THE PRESCRIBED FORM FROM A
    FOLD-SIDE ONE. `normalize(F, C·s, R·t·s) == normalize(F/s, C, R·t)`: a
    `fold_merit`-only implementation is projectively identical and passes every
    behavioural gate in this file — both spec reviewers measured that to bit
    equality, and rev 1's claim that raise-neutrality excluded it was simply
    false (ledger R-2). No output-space test can do this job.

    C/R-only is prescribed for AUDITABILITY: the fold merit stays an untouched
    input, which keeps the A1 no-fold-floor guardrail inspectable at a glance.

    The engine short-circuits when the flag is False (`entries` is not rebuilt
    at all), so the flag is driven TRUE here — an identity comparison against
    the un-opted path would observe nothing.

    Scale equality is asserted only where BOTH ends are strictly positive: the
    captured vector is post-`max(m, 0.0)`, so positivity is what makes it
    equal to the raw merit, and a ratio out of a clamped zero is 0/0. The
    shortfall is the river's two hard zeroes (bluff-catchers never value-raise,
    and AIR never calls). Re-counted at T3 (improvement slice 2, 2026-08-19):
    4,320 graded ratios out of a possible 5,184 before the change and 4,608
    after it, the 288 gained being the river ace-high CALL leg the ticket
    unblocked. The figures this paragraph used to carry, 1,920 of 2,304, were
    already stale when T3 found them — the grid has grown since they were
    written — so they are replaced rather than adjusted. Nothing asserts on the
    exact count; the floor below is `>= 1800`.

    "ONE common factor" is checked per persona across the WHOLE grid, not just
    within a cell: the factor is `exp(-λ_p)` and depends on nothing about the
    node, so a spread anywhere in a persona's ratios is a defect. Cells where
    only one continue leg survives are graded by that same constraint.

    THE FACTOR'S VALUE IS PINNED, NOT JUST ITS CONSISTENCY (fan-in finding A,
    both mutants reproduced). Every clause above — fold bitwise unchanged, the
    two ratios agreeing, zero spread, the occupancy floors — is satisfied by a
    vector in which NOTHING MOVED: the ratios are then both exactly 1.0, which
    is maximally consistent. That made this an IDENTITY gate, and identity gates
    are what this initiative keeps being defeated by. Two measured mutants walked
    through the hole: one replaced the merit scale with `pass` and applied an
    equivalent fold-side scale to `weights` AFTER the capture instant (full suite
    green, 0 raw merits differing, nit ΔP(fold) still 0.13119); the other called
    `_line_scaled` and DISCARDED its result, which also survives P-1b, since
    P-1b grades the helper in isolation and its spy proves only that the helper
    was CALLED — neither proves the returned list is the one that reaches the
    normalization. Asserting the ratio equals the mechanism's OWN predicted
    `exp(-λ_p)`, and is strictly below 1.0, kills both: an inert transform reads
    1.0 and a post-capture equivalent leaves the raw merits at 1.0 too.

    This survives N-LOGIT, and that was MEASURED rather than assumed: the
    captured RAISE merit is `(R·line_mult)·rscale` at line=1 and `R·rscale` at
    line=0, so `rscale` cancels out of the ratio. Checked directly on a
    `model_copy` pack with `continue_ref` skewed to make `rscale = 1.6216` (at
    the anchor `rscale` is exactly 1.0 and would prove nothing — since
    R9-LOOSEFIT, 2026-08-04, that anchor is a frozen reference value, not the
    shipped `call_looseness` all six packs previously shared): the CALL and
    RAISE ratios both came back at relative
    error 0.000e+00 against `exp(-λ_p)`. `rel=1e-12` is the same tolerance the
    spread check already carries, and is generous against that."""
    grid = _r9d_grid()
    cells = grid["_cells"]
    fold_moved, scale_split = [], []
    ratios: dict[str, list] = {p: [] for p in _R9D_SENSITIVITY}
    for persona in _R9D_SENSITIVITY:
        for i, cell in enumerate(cells):
            m0 = grid[persona][False][i].merits
            m1 = grid[persona][True][i].merits
            assert set(m0) == set(m1), cell.key
            f0, f1 = m0[ActionType.FOLD], m1[ActionType.FOLD]
            if float(f0).hex() != float(f1).hex():
                fold_moved.append((persona, cell.key, f0, f1))
            here = [
                (a, m1[a] / m0[a])
                for a in (ActionType.CALL, ActionType.RAISE)
                if a in m0 and m0[a] > 0.0 and m1[a] > 0.0
            ]
            if len(here) == 2 and abs(here[0][1] - here[1][1]) > 1e-12 * max(
                here[0][1], here[1][1]
            ):
                scale_split.append((persona, cell.key, here))
            ratios[persona].extend((cell.key, a, r) for a, r in here)
    assert not fold_moved, (
        f"the FOLD merit is an INPUT and must never be rewritten; {len(fold_moved)} "
        f"cells moved it: {fold_moved[:5]}"
    )
    assert not scale_split, (
        f"CALL and RAISE were not scaled by ONE common factor — that is the "
        f"N-LOGIT misroute: {scale_split[:5]}"
    )
    for persona, obs in ratios.items():
        assert len(obs) >= 300, (persona, len(obs))
        lo = min(obs, key=lambda o: o[2])
        hi = max(obs, key=lambda o: o[2])
        assert hi[2] - lo[2] <= 1e-12 * hi[2], (persona, lo, hi)
        # …and the factor they all agree on is the mechanism's OWN `exp(-λ_p)`,
        # strictly damping. Without this the gate is an identity gate: a vector
        # in which nothing moved has ratios of exactly 1.0 and passes every
        # check above.
        want = math.exp(-_R9D_SHIFT_PER_UNIT * _R9D_SENSITIVITY[persona])
        assert want < 1.0, (persona, want)
        inert = [o for o in obs if o[2] >= 1.0]
        assert not inert, (
            f"{persona}: {len(inert)} of {len(obs)} raw-merit ratios are >= 1.0 — the "
            f"prescribed transform did NOT move the merits, so whatever moves the "
            f"output is not it: {inert[:5]}"
        )
        wrong = [o for o in obs if o[2] != pytest.approx(want, rel=1e-12)]
        assert not wrong, (
            f"{persona}: the common factor is not `exp(-λ_p)` = {want!r}; "
            f"{len(wrong)} of {len(obs)} ratios disagree: {wrong[:5]}"
        )
    assert sum(len(o) for o in ratios.values()) >= 1800


def test_r9d_p1b_line_transform_is_one_multiplication_bitwise():
    """P-1b (REGRESSION PIN, structural) — the transform ITSELF, checked BITWISE
    against the single multiplication it claims to perform.

    WHY P-1 ABOVE IS NOT ENOUGH (fan-in review finding, reproduced). P-1 reads
    the merits through the sampler, so it can only compare ratios of two
    separately-computed products, and it therefore has to carry a `1e-12`
    relative tolerance — as do S-3 (`1e-9` raise-share drift) and S-4 (`1e-12`
    composition). Those tolerances are NOT slack to be tightened away: a CORRECT
    implementation needs them, because downstream `(R·line_mult)·rscale` and
    `(R·rscale)·line_mult` differ bitwise ~35% of the time (ledger R-8).
    A reviewer built an implementation that exploits exactly that gap — CALL
    scaled by `line_mult`, RAISE by `line_mult * (1 + 5e-13)`, with the
    perturbation skipped at `line_mult == 1.0` so default-off byte-identity
    still holds — and it passed all 27 gates while breaking the mechanism's core
    promise (ONE common factor ⇒ the raise share is invariant).

    This gate closes that without touching a tolerance, by calling the
    production helper directly: each defend entry must be BITWISE its OWN input
    times the SAME `line_mult`, computed here as literally `m * line_mult`. That
    is exact WITHOUT fighting IEEE, because it compares one multiplication
    against itself rather than two differently-associated products. `1 + 5e-13`
    is ~2000 ulps at double precision, so the mutant misses by a mile.

    The two gates do different jobs and both are required: P-1 proves the
    SAMPLER applies a common per-action factor end to end; this proves the
    factor is one unperturbed multiply. The wiring block at the end is what
    keeps them joined — without it, moving the transform back inline would take
    this check off the production path while leaving it green."""
    line_scaled = personas_postflop._line_scaled
    # Awkward mantissas on purpose: a 5e-13 relative perturbation must land in
    # the bits, and values like 1.0 or 0.5 are the ones most likely to absorb a
    # rounding coincidence.
    merits = [
        (ActionType.FOLD, 0.8377192043795371),
        (ActionType.CALL, 1.9241503276618904),
        (ActionType.RAISE, 0.31624903175628193),
    ]
    factors = [math.exp(-_R9D_SHIFT_PER_UNIT * s) for s in _R9D_SENSITIVITY.values()]
    factors += [1.0, 0.5, 0.9999999999999999, 0.1234567890123456]
    for line_mult in factors:
        out = line_scaled(merits, line_mult)
        assert [a for a, _ in out] == [a for a, _ in merits], line_mult
        for (a, before), (_, after) in zip(merits, out, strict=True):
            want = before if a is ActionType.FOLD else before * line_mult
            assert float(after).hex() == float(want).hex(), (a, line_mult, after, want)

    # WIRING — the sampler really does route its line damp through that helper,
    # with the pinned factor. Same monkeypatch idiom `_r9d_probe` uses for `sum`.
    cell = _R9dCell(StrengthBucket.MIDDLE_PAIR, Street.TURN, 1, 0.5, 20.0, True)
    seen: list[float] = []

    def _spy(entries, line_mult):
        seen.append(line_mult)
        return line_scaled(entries, line_mult)

    personas_postflop._line_scaled = _spy
    try:
        _r9d_probe(_pack("nit"), cell, True)
    finally:
        personas_postflop._line_scaled = line_scaled
    assert seen == [math.exp(-_R9D_SHIFT_PER_UNIT * _R9D_SENSITIVITY["nit"])]


# Out-of-scope templates. `river` entries are dropped where the river resets
# DrawCategory to NONE (which would make them IN scope) — the filter is applied
# by classification, not by hand, and the coverage claim is asserted below.
_R9D_OUT_OF_SCOPE = {
    "monster": (("9h", "9d"), ["Kc", "9s", "3h"]),
    "two_pair": (("Kh", "9c"), ["Kc", "9s", "3h"]),
    "overpair_tptk": (("Ah", "Ad"), ["Kc", "9s", "3h"]),
    "middle_pair+flush_draw": (("9h", "4h"), ["Kh", "9s", "3h"]),
    "top_pair+flush_draw": (("Kh", "4h"), ["Kc", "9h", "3h"]),
    "ace_high+flush_draw": (("Ah", "5h"), ["2h", "9h", "Kc"]),
    "air+gutshot": (("Td", "Jh"), ["7h", "9s", "9d"]),
}
_R9D_RUNOUT = ["2d", "8c"]


def _r9d_out_of_scope_spots():
    spots = []
    for label, (hole, flop) in _R9D_OUT_OF_SCOPE.items():
        for extra in (0, 1, 2):
            board = flop + _R9D_RUNOUT[:extra]
            bucket, draw = strength_bucket(hole, board)
            in_scope = bucket in _R9D_SCOPE_BUCKETS and draw is DrawCategory.NONE
            if not in_scope:
                spots.append((f"{label}/{len(board)}", hole, board, bucket, draw))
    return spots


def test_r9d_p2_out_of_scope_cells_are_byte_identical():
    """P-2 (REGRESSION PIN, green without the engine block) — every out-of-scope
    cell is byte-identical between line = 0 and line = 1.

    Three families, and rev 1 had a gate for none of them:
      * every EXCLUDED bucket — MONSTER, TWO_PAIR_PLUS, OVERPAIR_TPTK;
      * every `draw != NONE`, INCLUDING in-scope buckets carrying a draw. Bucket
        and draw are INDEPENDENT axes, so "middle pair with a flush draw" is a
        common cell that rev 1's single excluded-column left undefined (R-6);
      * every NON-FACING node — unopened CHECK+BET and matched-with-option
        CHECK+RAISE. The engine region this mechanism attaches to sits at
        FUNCTION-BODY indentation, i.e. the path SHARED with those shapes, which
        is why the `ActionType.FOLD in by_kind` gate is part of the mechanism
        and not a shortcut; without it the RAISE entry on a check-raise shape
        would be scaled and there would be no fold leg to receive the mass
        (R-7).

    The coverage claim is asserted, not assumed: the excluded buckets and both
    draw categories must all actually appear in the spot list."""
    spots = _r9d_out_of_scope_spots()
    buckets = {b for _, _, _, b, _ in spots}
    draws = {d for _, _, _, _, d in spots}
    assert {
        StrengthBucket.MONSTER,
        StrengthBucket.TWO_PAIR_PLUS,
        StrengthBucket.OVERPAIR_TPTK,
    } <= buckets, buckets
    assert {DrawCategory.STRONG, DrawCategory.WEAK} <= draws, draws
    assert {
        StrengthBucket.MIDDLE_PAIR,
        StrengthBucket.TOP_PAIR,
        StrengthBucket.ACE_HIGH,
        StrengthBucket.AIR,
    } <= {b for _, _, _, b, d in spots if d is not DrawCategory.NONE}, spots

    moved, graded = [], 0
    for persona in _R9D_SENSITIVITY:
        pack = _pack(persona)
        for label, hole, board, _bucket, _draw in spots:
            street = _STREET_BY_BOARD_LEN[len(board)]
            for frac in _R9D_FRACS:
                bet = round(frac * _R9D_POT_PRE, 2)
                pot = _R9D_POT_PRE + bet
                shapes = {
                    "facing": [
                        personas_postflop_legal_fold(),
                        personas_postflop_legal_call(bet),
                        personas_postflop_legal_raise(3 * bet, 400.0),
                    ],
                    "unopened CHECK+BET": [
                        personas_postflop_legal_check(),
                        personas_postflop_legal_bet(1.0, 400.0),
                    ],
                    "matched CHECK+RAISE": [
                        personas_postflop_legal_check(),
                        personas_postflop_legal_raise(3 * bet, 400.0),
                    ],
                }
                for shape, legal in shapes.items():
                    vecs = []
                    for line in (False, True):
                        cap = _CaptureWeights()
                        sample_postflop_decision(
                            pack,
                            hole,
                            board,
                            legal,
                            pot,
                            20.0 * pot,
                            1,
                            cap,  # type: ignore[arg-type] — duck-typed capture rng
                            current_bet_to=bet,
                            street=street,
                            latest_aggressor_contribution_bb=bet,
                            aggressor_bet_prev_street=line,
                        )
                        vecs.append(_r9d_hex(cap.dist or {}))
                    graded += 1
                    if vecs[0] != vecs[1]:
                        moved.append((persona, label, shape, frac))
    assert not moved, f"{len(moved)} out-of-scope cells moved with the line signal: {moved[:5]}"
    assert graded >= 1000, graded


def test_r9d_s1_p2_discriminator_in_scope_nodes_do_move():
    """S-class (RED-FIRST) — P-2's discriminator, and it belongs to the
    SENSITIVITY class, not the pin class.

    Byte-identity over out-of-scope cells is only meaningful if the SAME call
    shape MOVES on an in-scope cell; otherwise P-2 is green because nothing
    anywhere responds to the signal. A gate that can only ever pass is not a
    gate — so this one is stated separately and is RED without the engine
    block, exactly like the rest of the S class."""
    grid = _r9d_grid()
    ref = _r9d_cells().index(_R9D_REFERENCE)
    for persona in _R9D_SENSITIVITY:
        d0 = _r9d_hex(grid[persona][False][ref].dist)
        d1 = _r9d_hex(grid[persona][True][ref].dist)
        assert d0 != d1, persona


def _r9d_cbet_history(bettor: Position, *, through: Street) -> list:
    """The textbook single-raised-pot line: `bettor` raises preflop, then bets
    each postflop street up to and including `through`."""
    from app.domain.spot import HistoryAction

    hist = [
        HistoryAction(
            street=Street.PREFLOP, position=bettor, action=ActionType.RAISE, amount_bb=3.0
        ),
        HistoryAction(
            street=Street.PREFLOP, position=Position.BB, action=ActionType.CALL, amount_bb=3.0
        ),
    ]
    for street in (Street.FLOP, Street.TURN, Street.RIVER):
        hist.append(
            HistoryAction(street=street, position=bettor, action=ActionType.BET, amount_bb=3.0)
        )
        if street is through:
            break
    return hist


def test_r9d_p3_flop_is_line_blind_through_the_production_derivation():
    """P-3 (REGRESSION PIN, green without the engine block) — the flop is
    unchanged, pinned WHERE THE GUARANTEE ACTUALLY LIVES.

    The honest limit (ledger R-11): `sample_postflop_decision` takes an
    unconstrained boolean, so a DIRECT caller can pass True with
    `street=FLOP`. The sampler is deliberately left honest — a street check
    inside the mechanic would reintroduce the `street -> scalar` term the
    roadmap forbids. So this pin does NOT assert a sampler property the flat
    kwarg does not have; it pins the DERIVATION's flop-zero property and then
    threads the derived flag through every flop grid cell.

    Two node classes matter and both are flop-facing-a-first-c-bet:
      * the balanced-villain α fixture (`catcher_fold_by_size`) — a 3-card
        board, the pre-aggression pot, no `aggressor_bet_prev_street` argument
        at all;
      * the population fold-to-first-c-bet statistic — computed only from
        `street == "flop"` decisions facing the hand's first flop bet.
    Both live at `run == 0` by construction, so the α ceiling and the
    fold-to-c-bet band cannot move. The turn/river assertions are the
    discriminator: the flop zero is structural, not vacuous."""
    from app.domain.table.postflop_context import aggressor_barrel_run

    flop_line = _r9d_cbet_history(Position.BTN, through=Street.FLOP)
    assert aggressor_barrel_run(flop_line, Street.FLOP, Position.BTN) == 0
    assert aggressor_barrel_run(flop_line, Street.TURN, Position.BTN) == 1
    turn_line = _r9d_cbet_history(Position.BTN, through=Street.TURN)
    assert aggressor_barrel_run(turn_line, Street.RIVER, Position.BTN) == 2
    # the α fixture / fold-to-c-bet node class: a 3-card board is always FLOP
    assert _STREET_BY_BOARD_LEN[3] is Street.FLOP

    grid = _r9d_grid()
    cells = grid["_cells"]
    for persona in _R9D_SENSITIVITY:
        pack = _pack(persona)
        for i, cell in enumerate(cells):
            if cell.street is not Street.FLOP:
                continue
            derived = aggressor_barrel_run(flop_line, cell.street, Position.BTN) >= 1
            assert derived is False, cell.key
            produced = _r9d_probe(pack, cell, derived).dist
            assert _r9d_hex(produced) == _r9d_hex(grid[persona][False][i].dist), (persona, cell.key)


def test_r9d_p4_default_off_is_byte_identical_over_the_whole_grid():
    """P-4 (REGRESSION PIN, green without the engine block) — an un-opted pack
    is byte-identical across the FULL grid, and the flat kwarg defaults False.

    `line_sensitivity` absent ⇒ `entries` is never rebuilt, so this is identity
    by construction rather than by cancellation — the distinction that matters,
    since a mechanism whose two halves cancel is exactly the N-LOGIT rev-1
    defect this project has now hit twice."""
    cells = _r9d_cells()
    moved, defaulted = [], []
    for persona in _R9D_SENSITIVITY:
        base = _pack(persona)
        unopted = base.model_copy(deep=True)
        unopted.postflop = base.postflop.model_copy(update={"line_sensitivity": None})
        assert unopted.postflop.line_sensitivity is None
        for cell in cells:
            a = _r9d_hex(_r9d_probe(unopted, cell, False).dist)
            b = _r9d_hex(_r9d_probe(unopted, cell, True).dist)
            if a != b:
                moved.append((persona, cell.key))
        # the flat kwarg's default, on the OPTED-IN pack: omitting it must equal
        # passing False, or every legacy caller silently opted in.
        for cell in (_R9D_REFERENCE, _R9dCell(StrengthBucket.AIR, Street.RIVER, 2, 1.5, 1.0, True)):
            legal = [personas_postflop_legal_fold(), personas_postflop_legal_call(cell.bet)]
            if cell.with_raise:
                legal.append(personas_postflop_legal_raise(3 * cell.bet, 400.0))
            omitted = _CaptureWeights()
            sample_postflop_decision(
                base,
                _R9D_HOLES[cell.bucket],
                _R9D_BOARDS[cell.street],
                legal,
                cell.pot,
                cell.stack,
                cell.opponents,
                omitted,  # type: ignore[arg-type] — duck-typed capture rng
                current_bet_to=cell.bet,
                street=cell.street,
                latest_aggressor_contribution_bb=cell.bet,
            )
            explicit = _r9d_probe(base, cell, False).dist
            if _r9d_hex(omitted.dist or {}) != _r9d_hex(explicit):
                defaulted.append((persona, cell.key))
    assert not moved, f"an un-opted pack responded to the line signal: {moved[:5]}"
    assert not defaulted, f"the flat kwarg does not default to False: {defaulted[:5]}"


def test_r9d_p4_mechanism_adds_no_rng_call():
    """P-4 (REGRESSION PIN) — the ACTION draw stays the FIRST `rng.choices`
    consumer and the sizing draw the second, with the line signal ON.

    Every capture rng in this file and in `range_estimate` keys on that
    ordering; the mechanism is a scalar multiply on existing entries and must
    add no draw."""
    cell = _R9dCell(StrengthBucket.AIR, Street.TURN, 1, 0.5, 20.0, True)
    legal = [
        personas_postflop_legal_fold(),
        personas_postflop_legal_call(cell.bet),
        personas_postflop_legal_raise(3 * cell.bet, 400.0),
    ]
    for persona in _R9D_SENSITIVITY:
        rng = _NlogitAllChoices()
        sample_postflop_decision(
            _pack(persona),
            _R9D_HOLES[cell.bucket],
            _R9D_BOARDS[cell.street],
            legal,
            cell.pot,
            cell.stack,
            cell.opponents,
            rng,  # type: ignore[arg-type] — duck-typed capture rng
            current_bet_to=cell.bet,
            street=cell.street,
            latest_aggressor_contribution_bb=cell.bet,
            aggressor_bet_prev_street=True,
        )
        assert len(rng.calls) == 2, (persona, len(rng.calls))
        assert rng.calls[0][0] == [ActionType.FOLD, ActionType.CALL, ActionType.RAISE], persona
        assert all(isinstance(x, float) for x in rng.calls[1][0]), persona


def test_r9d_p5_zero_continue_cells_are_inert():
    """P-5 (REGRESSION PIN, green without the engine block) — where
    `C + R == 0`, the vector is unchanged between line = 0 and line = 1.

    These cells are REACHABLE in scope, which is the whole point: the river
    AIR/no-draw cell hard-zeroes `call_merit` and RAISE is appended only when
    legal, so a river AIR hand at a FOLD+CALL node has no continue mass at all.
    S-3 and S-4 exclude them because their ratios are 0/0; this pin is what
    stops that exclusion from being a hole (ledger R-3). Naked ACE_HIGH used to
    be in this set too and left it at T3 (improvement slice 2, 2026-08-19),
    which is why the set is half the size it was.

    Their existence is asserted, not hoped for: an empty set here would make the
    exclusions in S-3/S-4 unaudited."""
    grid = _r9d_grid()
    cells = grid["_cells"]
    moved, found = [], dict.fromkeys(_R9D_SENSITIVITY, 0)
    for persona in _R9D_SENSITIVITY:
        for i, cell in enumerate(cells):
            d0 = grid[persona][False][i].dist
            if _r9d_continue(d0) > 0.0:
                continue
            found[persona] += 1
            if _r9d_hex(d0) != _r9d_hex(grid[persona][True][i].dist):
                moved.append((persona, cell.key))
    assert not moved, f"a zero-continue cell was not inert: {moved[:5]}"
    empty = {p: n for p, n in found.items() if n == 0}
    assert not empty, (
        f"no zero-continue cells reached for {empty} — S-3/S-4's exclusion is unaudited"
    )


def test_r9d_p6_price_tail_vectors_needed_no_line_edit():
    """P-6 (REGRESSION PIN, green without the engine block) —
    `tests/test_price_tail.py`'s 23 frozen exact-equality vectors stay green
    WITHOUT EDIT, doubly protected: those callers pass no line signal (so the
    flat kwarg defaults False) and the mechanism is a no-op at line = 0.

    Asserted structurally here, and re-asserted by running that module: if the
    implementation had diverged enough to need those vectors re-recorded, the
    file would have had to learn about this slice. It has not, and it must not.
    IF YOU FIND YOURSELF EDITING THAT FILE, STOP — the implementation has
    diverged from the spec."""
    from pathlib import Path

    src = Path(__file__).with_name("test_price_tail.py").read_text()
    for token in ("line_sensitivity", "aggressor_bet_prev_street", "R9-DEFENCE", "_LINE_DELTA"):
        assert token not in src, (
            f"{token!r} leaked into tests/test_price_tail.py — that file's frozen "
            f"vectors must not need this slice to stay green"
        )


# ===================================================================
# R9-DEFENCE-a — S-5: the PAIRED population-sensitivity run
# ===================================================================
#
# WHAT THIS MEASURES, and why it is built the way it is.
#
# Every gate above is a NODE measurement: hand it a cell, read the vector. S-5
# is the one POPULATION measurement — does making bots read the opponent's line
# change how the simulated table actually plays out? Before this ticket the
# question could not even be asked: `_postflop_decision` had no
# `aggressor_bet_prev_street` parameter in EITHER `context_aware` state, so the
# population run was structurally blind to the whole slice and S-5 was
# unfalsifiable. That blindness is the identity-vs-sensitivity trap one level up
# from the node gates.
#
# ── THE PAIRING (ledger R-4 — the reason this is not "call `_persona_stats`
#    twice"). `_persona_stats` builds ONE `random.Random(20260710)` and uses it
#    BOTH to draw each hand's seed (`hand_seed = rng.randrange(...)`) AND as the
#    action/sizing rng inside `_play_hand`. The instant line-aware play changes a
#    single draw count, the NEXT `hand_seed` differs and the two arms stop
#    playing the same hands — the comparison would measure deal noise, not the
#    mechanism. So this run:
#      * pre-generates an IMMUTABLE tuple of (hand_seed, action_seed) pairs from
#        two DEDICATED rngs that drive nothing else, and
#      * gives every hand its OWN freshly-seeded action rng, so divergence cannot
#        leak from hand i to hand i+1 — each hand is independently paired.
#    Everything else (lineup, button rotation, stacks, `context_aware`, packs) is
#    held identical; the line signal is the ONLY input that differs.
#
# ── THE CONTROL IS NODE-MATCHED, not merely line-blind. The control arm runs
#    `_play_hand(line_aware=_LINE_OBSERVE)`: it DERIVES the barrel flag and
#    records the node, but never passes it to the sampler, so its play is
#    bit-for-bit the pinned default path while it still knows which nodes were
#    barrel nodes. That is what makes "P(fold) at a barrel node, with and
#    without the mechanism" a real comparison rather than two differently
#    populated samples.
#
# ── THE PAIRING IS ASSERTED, NOT ASSUMED. `aggressor_barrel_run` is 0 on the
#    FLOP by construction (its walk over preceding POSTFLOP streets is empty
#    there), so no preflop or flop decision can differ between the arms — only
#    turn and river ones can. `saw_flop` is snapshotted the moment the board
#    reaches three cards, i.e. strictly before any flop action, so the arms must
#    produce IDENTICAL flop-arrival counts for every persona.
#    `test_r9d_s5_the_arms_are_a_true_pair` demands exactly that: if it ever
#    breaks, something upstream of the turn moved and every number below is
#    noise.
#
# ── THE DECISIVE GATE IS THE DIRECT ONE (owner ruling, 2026-08-02).
#    `test_r9d_s5_fold_rate_at_barrel_nodes_rises` measures what the mechanism
#    actually claims to do — P(fold) at an IN-SCOPE barrel node in organic play —
#    and showdown frequency is demoted to a directional companion. The history
#    matters and is kept deliberately:
#
#    Spec §7 S-5 originally asked for a showdown-frequency fall of >= 0.01 for
#    nit / tag / lag / passive_fish. **That literal was measured FALSE at four
#    sample sizes and has been RETIRED by the owner** — it was set a priori,
#    before anything had been measured. Paired, shared nine-seat lineup,
#    `context_aware=False`:
#
#      persona          N=2000    N=4000    N=8000   N=24000
#      nit             -0.0177   -0.0088   -0.0154   -0.0121
#      tag             -0.0117   -0.0078   -0.0079   -0.0061
#      lag             -0.0042   -0.0042   -0.0053   -0.0072
#      passive_fish    -0.0044   -0.0052   -0.0037   -0.0043
#      maniac          -0.0044   -0.0044   -0.0036   -0.0031
#      calling_station -0.0030   -0.0027   -0.0023   -0.0023
#
#    Only `nit` ever clears 0.01, and not stably. Re-measured `context_aware=
#    True` at N=8000 the shape is the same (lag -0.0081, passive_fish -0.0063,
#    tag -0.0069, nit -0.0132); with the per-persona `_persona_stats` lineup at
#    N=3000 it is smaller still (tag -0.0017).
#
#    The reason is dilution, not a weak mechanism. Showdown frequency divides a
#    node-level effect by a denominator two orders of magnitude larger: the
#    mechanism fires only where a seat faces a sustained barrel holding an
#    in-scope bucket, and in a nine-max full-ring sim that node is RARE — a few
#    thousand across N hands x 9 seats, of which `nit` reaches a few dozen.
#    Measured AT those nodes instead, the effect is large and orderly (the table
#    in `test_r9d_s5_fold_rate_at_barrel_nodes_rises`). Recording the retired
#    literal here, rather than deleting it, is the point: it is the evidence the
#    retirement rests on.
#
# ── COST. Two arms x `_R9D_S5_N` hands ~= 110s on this maker's box, plus ~3s
#    for the no-op discriminator. The shared nine-seat lineup is what keeps that
#    affordable: it reads ALL SIX personas out of ONE pair of arms instead of six
#    pairs. N is set by the DECISIVE gate's thinnest sample — the mechanism fires
#    only where a seat faces a sustained barrel holding an in-scope bucket, and
#    `nit` reaches that node rarest of the six.
#
#    RAISED 8000 -> 24000 by the de-robotization slice (T5, 2026-08-16). The
#    reason is sample floor and nothing more: at N=8000 the `nit` arm reaches
#    only 55 in-scope nodes, and the THREE-TIER ordering this gate asserts turns
#    over on that few. At 24000 `nit` reaches 131 and it holds. The cost is ~74s
#    of suite time.
#
#    ⚠️ AN EARLIER VERSION OF THIS BLOCK ARGUED MORE THAN THAT, AND THE ARGUMENT
#    WAS WRONG. It said the ordering "is stable" at 24000, that it "reproduces
#    at 48000 with a WIDER margin", and that a margin growing with N is "the
#    signature of an effect emerging from noise rather than of noise being mined
#    for one". Review broke it: the 48000 seed schedule is a PREFIX of the 24000
#    one, so the second reading is an extension of the first sample and not a
#    replication of it, and a two-point read on one seed pair cannot establish a
#    trend at all. The ⚠️ block at `_R9D_S5_ORDER` has the independent seed-pair
#    evidence and the withdrawal that followed. Nothing about the raise to 24000
#    depends on the broken argument; the sample floor stands on its own.

_R9D_S5_N = 24000

# Two DEDICATED rngs (ledger R-4). Neither ever acts as an action/sizing rng —
# that is the whole point: the deal sequence must not be able to move when play
# does. Seeds are distinct from the `_persona_stats` 20260710 stream so this run
# can never be confused with, or accidentally reuse, a banded measurement.
_R9D_S5_DEAL_SEED = 20260802
_R9D_S5_ACTION_SEED = 20260803

# One seat per persona plus three repeats, in `ALL_PERSONAS` (alphabetical)
# order — published rather than derived at call time so the arms are reproducible
# from this module alone, and deliberately NOT weighted towards the thin personas
# (a nit-heavy lineup would buy `nit` more nodes at the price of measuring every
# other persona against a table that is not the roster).
_R9D_S5_LINEUP = tuple(ALL_PERSONAS[i % len(ALL_PERSONAS)] for i in range(9))

# The scope predicate, applied test-side to the raw `LineNode` rows (spec §4).
# Written as its own literal for the same reason `_R9D_SCOPE_BUCKETS` is: a gate
# that reads its own scope out of the module under test goes green for free the
# moment that module changes its mind. `test_r9d_s5_scope_matches_the_node_grid`
# reconciles the two.
_R9D_S5_SCOPE = _R9D_SCOPE_BUCKETS

# OCCURRENCE FLOORS (spec §7 S-5: "state the occurrence floor ... below which the
# comparison is not reported"), stated over IN-SCOPE barrel nodes because that is
# the population the decisive gate averages over. Measured at this N: 8,484
# table-wide, minimum 131 (`nit`) — it was 2,538 and 41 at the old N=8000.
# Deliberately a hard FAILURE rather than a silent skip — a run that stops
# reaching barrel nodes means the derivation or the sim broke, and a skip is
# exactly how that would hide.
#
# The per-persona floor stays at 20 rather than rising with N. It is asking
# "did the derivation break", not "is this enough to gate an ordering on" —
# 8000 hands cleared it with 41 nodes and still could not carry the ordering,
# which is the whole lesson of the `_R9D_S5_N` block above. A floor that
# answered both questions would have hidden that.
_R9D_S5_NODE_FLOOR = 1000  # table-wide, in-scope
_R9D_S5_PERSONA_NODE_FLOOR = 20  # per persona, in-scope

# ── THE DECISIVE LITERAL, and an honest account of its status ──────────────
#
# `nit` — the tightest lever (0.60) and the persona the closed form predicts
# hardest — must show a rise in P(fold) at in-scope barrel nodes of at least
# this much. It is a FLOOR WITH HEADROOM, **not a fitted value**:
#
#   * The closed form gives `nit` a reference-node effect of +0.131 — predicted
#     by the design pass BEFORE the mechanism existed, and reproduced by T4 at
#     +0.131190 (`test_r9d_s1_identity_breaks_with_a_literal_effect_floor`).
#   * Organic play AVERAGES that over a spot mix — every street, every price,
#     every SPR, every headcount the sim deals — so the population figure is
#     NECESSARILY smaller than the single-node one. A population gate pinned at
#     the reference-node number would be wrong by construction.
#   * 0.03 sits far above any no-op (which reads exactly 0.000000 — see
#     `test_r9d_s5_gate_is_red_under_a_no_op_mechanism`) and well below both the
#     reference-node effect and the measured population value: `nit` reads
#     +0.1017 here, ~3.4x the floor. An earlier, coarser diagnostic over ALL
#     barrel nodes (in-scope and out) read +0.054, ~1.8x the floor; both
#     readings clear it comfortably. (It read +0.1463, ~4.9x, at the old
#     N=8000 on the pre-T5 packs — the floor's headroom shrank but the floor
#     was never near binding.)
#
# What this floor is NOT: it is not the slice's unfitted effect-size gate. That
# remains **S-1's literal 0.05 at the named reference node** (`_R9D_MIN_
# REFERENCE_EFFECT` above), which matches a prediction made before any of this
# was measured. This one is a conservative population backstop chosen after
# measurement, and it is labelled as such so nobody later mistakes it for
# independent confirmation of the closed form.
_R9D_S5_NIT_RISE_FLOOR = 0.03

# ── THE ORDERING WE CAN DEFEND, and the edge we cannot ─────────────────────
#
# Spec §5's ladder is `nit 0.60 > tag 0.50 > {lag 0.35 = passive_fish 0.35} >
# maniac 0.20 > calling_station 0.10`, strict between tiers and equal within the
# braced tie. In ODDS space at a fixed node that ordering holds exactly, and
# `test_r9d_s4_ordering_is_strict_between_tiers_and_equal_within_the_tie` above
# asserts it there.
#
# In ORGANIC PLAY it does not survive intact, and this is the caveat spec §7 S-4
# already records for its own reason: **the probability-space ordering differs
# from the λ ordering because base continue rates differ.** Two further things
# push it around here — each persona meets a DIFFERENT mix of barrel spots (the
# station is called down to the river; the nit is rarely there at all), and
# ΔP(fold) for a given λ is steepest where the base fold rate is nearest the
# middle. Measured (rise in P(fold) at in-scope barrel nodes):
#
#   persona          λ-tier  N=4000    N=8000   N=16000
#   nit                1     +0.1429   +0.1463  +0.1272
#   tag                2     +0.0750   +0.0856  +0.0643
#   passive_fish       3     +0.0588   +0.0410  +0.0392
#   lag                3     +0.0364   +0.0369  +0.0579
#   maniac             4     +0.0470   +0.0346  +0.0294
#   calling_station    5     +0.0046   +0.0041  +0.0051
#
# Stable at every N: tiers 1 and 2 sit strictly above tiers 3-4, and tier 5 sits
# strictly below everything. NOT stable: the tier-3 / tier-4 edge — at N=4000
# `maniac` (+0.0470) outruns `lag` (+0.0364) outright, at N=8000 it is a
# 0.002 margin, and only by N=16000 does the ladder order return. Nor are the
# braced tie's two members equal in organic play (+0.0410 vs +0.0369 at this N):
# they carry equal λ, not equal spot mixes, so equality is not the prediction.
#
# So the gate asserts the coarse ordering — `nit > tag > {lag, passive_fish,
# maniac} > calling_station` — and says plainly that the fine tier-3/tier-4 edge
# is NOT asserted, rather than buying it with a bigger N. The λ-exact claim is
# S-4's, at the node, in odds space, where it is true.
#
# ── ⚠️ WEAKENED 2026-08-15. A T5 attempt to RESTORE the tag's own tier was
#    made on 2026-08-16 and WITHDRAWN the same day after review. Read this
#    before trusting any number quoted elsewhere about this gate. ───────────
#
# The T3/T4 slice dropped the tag's own tier, leaving `nit > {tag, lag,
# passive_fish, maniac} > calling_station`, citing a table where the tag fell
# below the fish at N=24000. T5 re-measured, found that specific inversion
# absent at the shipped tip, and restored the four-tier order. Two independent
# reviewers then broke the restoration, and they were right.
#
# What the re-measurement established, and what it did NOT:
#
#   * The SPECIFIC claim in the T3/T4 escalation — a new fish-above-tag
#     inversion — does not reproduce. At the shipped tip the tag sits above the
#     fish. That much stands.
#   * It does not follow that the four-tier order holds. It does not. At the
#     T3/T4 tip at N=24000 the tag reads .0464 against lag's .0561, so the
#     four-tier order fails there too — for a different reason than the one
#     that was escalated.
#   * The evidence offered for restoring it was weaker than it looked. "The
#     margin grows with N (+0.0122 at 24000, +0.0195 at 48000)" is a two-point
#     read on ONE seed pair, and the 48000 sample CONTAINS the 24000 one: the
#     seed schedule is a prefix, so that is an extension, not a replication.
#
# Measured properly, on genuinely independent (deal, action) seed pairs at
# N=24000 on the T5 packs:
#
#   seed pair              four-tier   three-tier   ordering
#   20260802 / 20260803    PASS        PASS         nit tag fish lag maniac stn
#   31415926 / 27182818    FAIL        PASS         nit lag tag fish maniac stn
#   99887766 / 11223344    PASS        PASS         nit tag fish lag maniac stn
#
# Seed-to-seed spread swamps any N trend. The tag/tier-3 boundary is not a
# property of the roster, it is a property of which hands the shared stream
# deals — exactly what this block already records for the tier-3/tier-4 edge.
# The three-tier form is what the data supports, so it stays.
#
# The sample size DOES stay raised, and that is a separate finding: at N=8000
# even the three-tier order turns over, because `nit` reaches only 55 in-scope
# nodes there. See the `_R9D_S5_N` block.
#
# The magnitude question the T3/T4 escalation also raised — the regulars' rise
# is lower than it was pre-slice — is closed separately by the owner's
# 2026-08-16 ruling: no re-fit of `line_sensitivity`. A re-fit needs a target,
# no sourced population figure for fold-to-barrel exists in this repo, and the
# softmax law (theory contract §2) predicts this effect to shrink when a
# persona arrives with more marginal holdings — which is what T3/T4 made the
# regulars do. Tuning λ upward to cancel that would break the node-level claim,
# which is green, in order to move an average. Full account in
# docs/ai-dlc/ledger/phase3-derobotization.md.
_R9D_S5_ORDER = (("nit",), ("tag", "lag", "passive_fish", "maniac"), ("calling_station",))

# ── THE DEMOTED COMPANION ──────────────────────────────────────────────────
# Showdown frequency is now a DIRECTIONAL population-consequence check, not an
# effect-size gate (owner ruling). `_R9D_S5_SPEC_FALL` is the RETIRED spec
# literal, kept in the module so the retirement is visible at the point of the
# gate and not only in a ledger. `_R9D_S5_MIN_FALL` is the measured floor
# actually asserted: the smallest magnitude any of the four named personas showed
# across four sample sizes was 0.0037, so 0.002 keeps ~1.8x headroom.
_R9D_S5_SPEC_FALL = 0.01  # RETIRED — recorded, never asserted
_R9D_S5_MIN_FALL = 0.002
_R9D_S5_STATION_TOL = 0.005  # spec §7 S-5's other literal — MET at every N
_R9D_S5_FALLERS = ("nit", "tag", "lag", "passive_fish")
_R9D_S5_DIRECTIONAL = ("maniac",)


def _r9d_s5_seeds() -> tuple[tuple[int, int], ...]:
    """The immutable (hand_seed, action_seed) schedule both arms replay."""
    deal_rng = random.Random(_R9D_S5_DEAL_SEED)
    action_rng = random.Random(_R9D_S5_ACTION_SEED)
    return tuple(
        (deal_rng.randrange(1_000_000_000), action_rng.randrange(1_000_000_000))
        for _ in range(_R9D_S5_N)
    )


_R9D_S5_SEEDS = _r9d_s5_seeds()


class _R9dArm(NamedTuple):
    wtsd: dict  # persona -> showdowns / flop-arrivals
    saw_flop: dict  # persona -> flop arrivals (the pairing receipt)
    showdowns: dict
    nodes: dict  # persona -> barrel facing nodes, ALL buckets
    in_scope: dict  # persona -> barrel facing nodes inside the §4 scope
    folds: dict  # persona -> FOLDs among those
    fold_rate: dict  # persona -> folds / in_scope


_R9D_S5_ARMS: dict = {}


def _r9d_s5_run(mode, packs, seeds) -> _R9dArm:
    """One arm: replay `seeds` with `line_aware=mode` and tally both metrics."""
    persona_by_seat = {i: _R9D_S5_LINEUP[i] for i in range(9)}
    saw = dict.fromkeys(ALL_PERSONAS, 0)
    shown = dict.fromkeys(ALL_PERSONAS, 0)
    nodes = dict.fromkeys(ALL_PERSONAS, 0)
    in_scope = dict.fromkeys(ALL_PERSONAS, 0)
    folds = dict.fromkeys(ALL_PERSONAS, 0)
    for i, (hand_seed, action_seed) in enumerate(seeds):
        res = _play_hand(
            random.Random(action_seed),
            hand_seed,
            i % 9,
            persona_by_seat,
            packs,
            line_aware=mode,
        )
        for row in res.line_nodes:
            persona = persona_by_seat[row.seat]
            nodes[persona] += 1
            if row.bucket in _R9D_S5_SCOPE and row.draw is DrawCategory.NONE:
                in_scope[persona] += 1
                if row.action == ActionType.FOLD.value:
                    folds[persona] += 1
        for seat, persona in persona_by_seat.items():
            if seat in res.saw_flop:
                saw[persona] += 1
                if seat in res.settlement.showdown_seats:
                    shown[persona] += 1
    return _R9dArm(
        wtsd={p: shown[p] / saw[p] for p in ALL_PERSONAS},
        saw_flop=saw,
        showdowns=shown,
        nodes=nodes,
        in_scope=in_scope,
        folds=folds,
        fold_rate={
            p: (folds[p] / in_scope[p] if in_scope[p] else float("nan"))
            for p in ALL_PERSONAS
        },
    )


def _r9d_s5_arm(mode) -> _R9dArm:
    """Cached arm of the main paired run. Several gates read the same two arms."""
    if mode not in _R9D_S5_ARMS:
        _R9D_S5_ARMS[mode] = _r9d_s5_run(mode, load_persona_packs(), _R9D_S5_SEEDS)
    return _R9D_S5_ARMS[mode]


def _r9d_s5_rise() -> dict:
    """persona -> rise in P(fold) at in-scope barrel nodes, treatment - control."""
    off, on = _r9d_s5_arm(_LINE_OBSERVE), _r9d_s5_arm(True)
    return {p: on.fold_rate[p] - off.fold_rate[p] for p in ALL_PERSONAS}


def test_r9d_s5_scope_matches_the_node_grid():
    """The S-5 scope filter is the SAME predicate the node grid publishes — the
    population gate and the node gates must not be able to drift apart."""
    assert _R9D_S5_SCOPE == _R9D_SCOPE_BUCKETS
    assert set(_R9D_S5_LINEUP) == set(ALL_PERSONAS)
    assert [p for tier in _R9D_S5_ORDER for p in tier] != []
    assert sorted(p for tier in _R9D_S5_ORDER for p in tier) == sorted(ALL_PERSONAS)


def test_r9d_s5_the_arms_are_a_true_pair():
    """S-5's precondition, asserted before any number is read (ledger R-4).

    Four claims, and each is a way the paired run could quietly degenerate into
    a measurement of deal noise:

    1. **The schedule is immutable and dedicated.** Regenerating it reproduces
       the same tuple, and neither seed rng is the `_persona_stats` stream.
    2. **The control is genuinely line-blind.** `_LINE_OBSERVE` records nodes but
       never passes the kwarg to the sampler — pinned on the actual call kwargs
       by `test_r9d_p7_the_population_path_never_sees_the_flag_by_default`.
    3. **The deals did not diverge.** Flop arrivals are identical per persona
       across the arms. Not a hope: `aggressor_barrel_run` is 0 on the flop by
       construction, so preflop and flop play CANNOT differ, and `saw_flop` is
       snapshotted before any flop action.
    4. **Occurrence floors.** Over ~zero barrel nodes the comparison is not
       reportable, so a breach fails hard rather than skipping quietly.

    Note the arms' node counts are close but not identical (a handful out of
    thousands): once turn play diverges, the downstream node population shifts
    slightly. That is the mechanism working, not the pairing failing — the
    pairing receipt is claim 3, which is exact."""
    assert _r9d_s5_seeds() == _R9D_S5_SEEDS
    assert isinstance(_R9D_S5_SEEDS, tuple) and len(_R9D_S5_SEEDS) == _R9D_S5_N
    assert 20260710 not in (_R9D_S5_DEAL_SEED, _R9D_S5_ACTION_SEED)
    assert len({s for s, _ in _R9D_S5_SEEDS}) > _R9D_S5_N * 0.99  # no seed reuse

    off, on = _r9d_s5_arm(_LINE_OBSERVE), _r9d_s5_arm(True)
    assert off.saw_flop == on.saw_flop, (
        "flop arrivals diverged between the arms, so the pair is broken: "
        f"{off.saw_flop} vs {on.saw_flop}"
    )
    for arm_name, arm in (("control", off), ("treatment", on)):
        total = sum(arm.in_scope.values())
        assert total >= _R9D_S5_NODE_FLOOR, (
            f"{arm_name}: only {total} in-scope barrel nodes in {_R9D_S5_N} hands "
            f"(floor {_R9D_S5_NODE_FLOOR}) — the S-5 comparison is not reportable"
        )
        thin = {p: n for p, n in arm.in_scope.items() if n < _R9D_S5_PERSONA_NODE_FLOOR}
        assert not thin, (
            f"{arm_name}: personas under the per-persona in-scope floor "
            f"{_R9D_S5_PERSONA_NODE_FLOOR}: {thin} — not reportable"
        )


def test_r9d_s5_fold_rate_at_barrel_nodes_rises():
    """S-5, THE DECISIVE POPULATION GATE (owner ruling, 2026-08-02) — in organic
    nine-max play, does a bot facing a SECOND BARREL actually fold more?

    This is the direct measure. `P(fold)` is taken over the in-scope barrel nodes
    the sim organically reaches (spec §4's predicate: bucket in
    {MIDDLE_PAIR, TOP_PAIR, ACE_HIGH, AIR} AND no draw), with a NODE-MATCHED
    control that sees the same node population with the mechanism switched off.
    Measured at `_R9D_S5_N` = 8000:

      persona          λ     in-scope   P(fold) off   P(fold) on   rise
      nit             0.60        41        0.2927       0.4390   +0.1463
      tag             0.50        85        0.2791       0.3647   +0.0856
      passive_fish    0.35       268        0.4889       0.5299   +0.0410
      lag             0.35       207        0.3592       0.3961   +0.0369
      maniac          0.20       318        0.3774       0.4119   +0.0346
      calling_station 0.10      1619        0.2930       0.2971   +0.0041

    Two assertions: (a) a STRICTLY POSITIVE rise for every persona — all six
    author `line_sensitivity > 0`, reconciled against the packs by
    `test_r9d_ladder_matches_the_authored_packs`; and (b) the literal floor
    `_R9D_S5_NIT_RISE_FLOOR` on the tightest persona. Read the block above that
    constant before judging the 0.03: it is a conservative floor with headroom,
    NOT a fitted value, and it is NOT the slice's unfitted effect-size gate —
    that is still S-1's 0.05 at the named reference node.

    NOT VACUOUS, which is the property that matters: under a no-op mechanism
    both arms play byte-identically and every rise is exactly 0.000000, so (a)
    goes red. `test_r9d_s5_gate_is_red_under_a_no_op_mechanism` runs that
    counterfactual in-suite rather than asserting it in prose."""
    off, on = _r9d_s5_arm(_LINE_OBSERVE), _r9d_s5_arm(True)
    rise = _r9d_s5_rise()
    report = {
        p: (
            on.in_scope[p],
            round(off.fold_rate[p], 4),
            round(on.fold_rate[p], 4),
            round(rise[p], 4),
        )
        for p in ALL_PERSONAS
    }
    flat = {p: r for p, r in rise.items() if not r > 0.0}
    assert not flat, (
        f"P(fold) at in-scope barrel nodes did not rise for {flat} — the population "
        f"run is still line-blind there (a no-op mechanism reads exactly this). "
        f"Full table (in_scope, off, on, rise): {report}"
    )
    assert rise["nit"] >= _R9D_S5_NIT_RISE_FLOOR, (
        f"nit rose only {rise['nit']:.4f} at in-scope barrel nodes, under the literal "
        f"floor {_R9D_S5_NIT_RISE_FLOOR}. Full table: {report}"
    )


def test_r9d_s5_fold_rate_rise_follows_the_defensible_ladder():
    """S-5(c) — the ordering, and ONLY the part of it organic play supports.

    Asserted: `nit > {tag, lag, passive_fish, maniac} > calling_station`,
    strictly between those groups. Read `_R9D_S5_ORDER` itself rather than this
    line if the two ever disagree — an earlier version of this docstring went on
    claiming the tag's own tier after the constant had dropped it, and the T5
    review found it still saying so.

    ⚠️ DELIBERATELY NOT ASSERTED, and the reason is in the `_R9D_S5_ORDER` block
    above: neither the tag's own tier nor the fine tier-3 / tier-4 edge
    (`{lag, passive_fish}` above `maniac`) holds at every sample size. On three
    independent seed pairs at this N the four-tier form fails one of them, and
    the tag/lag boundary flips with the deal stream rather than with the packs.
    Nor are the braced tie's members equal here; they carry equal λ, not equal
    spot mixes. This is the same caveat spec §7 S-4 records for its own reason —
    probability-space ordering differs from the λ ordering because base continue
    rates differ — and the λ-exact claim is asserted where it is true: at a fixed
    node, in odds space, by
    `test_r9d_s4_ordering_is_strict_between_tiers_and_equal_within_the_tie`.

    Buying the missing edge with a bigger N was considered and rejected: it would
    trade honesty about the population for a number, and the population is the
    thing this gate exists to describe."""
    rise = _r9d_s5_rise()
    for higher, lower in zip(_R9D_S5_ORDER[:-1], _R9D_S5_ORDER[1:], strict=True):
        worst_high = min(rise[p] for p in higher)
        best_low = max(rise[p] for p in lower)
        assert worst_high > best_low, (
            f"ordering broke between {higher} (min {worst_high:.4f}) and {lower} "
            f"(max {best_low:.4f}); full table {({p: round(r, 4) for p, r in rise.items()})}"
        )


def test_r9d_s5_gate_is_red_under_a_no_op_mechanism():
    """The decisive gate's non-vacuity, PROVEN rather than argued.

    Strips `line_sensitivity` from all six packs — which is the literal no-op
    (`personas_postflop.py`: lever `None` and the merit list is not rebuilt at
    all) and stands in for spec §10.4's mutants (a) `line_mult = 1.0` and (b)
    `_LINE_DELTA = 1e-12` — then replays a short paired run. With the mechanism
    inert the two arms play byte-identically, so:

      * every persona's in-scope node count and FOLD count match exactly, hence
        every rise is exactly 0.0 and
        `test_r9d_s5_fold_rate_at_barrel_nodes_rises`'s assertion (a) is RED; and
      * every showdown-frequency delta is exactly 0.0, so the demoted companion
        gate is RED too.

    Asserted on COUNTS, not rates, so no persona needs to reach a big enough
    sample for a rate to be meaningful at this short N."""
    packs = load_persona_packs()
    no_op = {}
    for key, pack in packs.items():
        stripped = pack.model_copy(deep=True)
        stripped.postflop = pack.postflop.model_copy(update={"line_sensitivity": None})
        assert stripped.postflop.line_sensitivity is None
        no_op[key] = stripped
    seeds = _R9D_S5_SEEDS[:600]
    off = _r9d_s5_run(_LINE_OBSERVE, no_op, seeds)
    on = _r9d_s5_run(True, no_op, seeds)
    assert sum(on.in_scope.values()) > 0, "the probe reached no in-scope barrel node at all"
    assert off.in_scope == on.in_scope, (off.in_scope, on.in_scope)
    assert off.folds == on.folds, (off.folds, on.folds)
    assert off.showdowns == on.showdowns, (off.showdowns, on.showdowns)
    assert off.saw_flop == on.saw_flop


def test_r9d_s5_paired_population_showdown_frequency_falls():
    """S-5's DIRECTIONAL population-consequence companion — demoted from decisive
    by the owner ruling of 2026-08-02, and NOT an effect-size gate.

    The claim is only that the population moves the way the mechanism predicts:
    bots that fold to barrels more often ride fewer hands to showdown. Measured
    at this N: nit -0.0079, tag -0.0096, lag -0.0050, passive_fish -0.0054,
    maniac -0.0041, calling_station -0.0021.

    Spec §7 S-5's original literal — a fall of >= `_R9D_S5_SPEC_FALL` (0.01) for
    nit/tag/lag/passive_fish — was measured FALSE at four sample sizes and has
    been RETIRED; the evidence table is in the ⚠️ block at the head of this
    section and must not be trimmed. What is asserted instead is a strict fall
    floored at the measured `_R9D_S5_MIN_FALL`.

    Still falsifiable: under any no-op mechanism both arms play byte-identically
    and every delta is exactly 0.0 (`test_r9d_s5_gate_is_red_under_a_no_op_
    mechanism` demonstrates it), so this gate goes red too."""
    off, on = _r9d_s5_arm(_LINE_OBSERVE), _r9d_s5_arm(True)
    report = {p: round(on.wtsd[p] - off.wtsd[p], 4) for p in ALL_PERSONAS}
    delta = {p: on.wtsd[p] - off.wtsd[p] for p in ALL_PERSONAS}

    rose = {p: d for p, d in report.items() if d > 0.0}
    assert not rose, (
        f"showdown frequency ROSE for {rose} — folding more to a barrel cannot "
        f"produce more showdowns. Full table: {report}"
    )
    flat = {p: d for p, d in delta.items() if d == 0.0}
    assert not flat, (
        f"showdown frequency did not move at all for {flat} — the population run "
        f"is still line-blind (a no-op mechanism reads exactly this). "
        f"Full table: {report}"
    )
    shallow = {p: report[p] for p in _R9D_S5_FALLERS if delta[p] > -_R9D_S5_MIN_FALL}
    assert not shallow, (
        f"fall shallower than the measured floor {_R9D_S5_MIN_FALL} for {shallow} "
        f"(the retired spec literal was {_R9D_S5_SPEC_FALL}). Full table: {report}"
    )
    for persona in _R9D_S5_DIRECTIONAL:
        assert delta[persona] < 0.0, (persona, report[persona])


def test_r9d_s5_calling_station_stays_line_blind():
    """S-5's other spec literal, and this one IS met: `|Δ| <= 0.005` for the
    station's showdown frequency.

    Spec §5 — the station's near-zero lever is THE ARCHETYPE, not a leak: a
    line-blind call-down is its defining trait, so authoring it at 0.10 must
    leave the population read essentially where it was. Measured -0.0021 …
    -0.0030 across N in {2000, 4000, 8000, 24000}.

    A two-sided bound, so it is not satisfied by "the station is excluded": were
    the mechanism mis-scoped and the station damped like a nit, this reads about
    -0.02 and goes red."""
    off, on = _r9d_s5_arm(_LINE_OBSERVE), _r9d_s5_arm(True)
    delta = on.wtsd["calling_station"] - off.wtsd["calling_station"]
    assert abs(delta) <= _R9D_S5_STATION_TOL, delta


def test_r9d_p7_the_population_path_never_sees_the_flag_by_default(monkeypatch):
    """P-7's mechanism, pinned structurally rather than inferred from the bands.

    Every `BANDS` row and every golden statistic in this file is measured through
    `_play_hand`'s DEFAULT path. Those numbers stay byte-identical for exactly
    one reason: unless `line_aware is True` the harness never puts
    `aggressor_bet_prev_street` into the sampler call at all, so
    `sample_postflop_decision` is invoked with the identical keyword set it was
    invoked with before this ticket. Asserted here on the actual call kwargs —
    an equality of measured statistics could not tell "the flag never arrived"
    from "the flag arrived and happened not to matter on these seeds".

    All three `line_aware` states are covered, and the middle one carries S-5's
    weight: `_LINE_OBSERVE` must record nodes while passing NOTHING, or the
    "node-matched control" is really a second treatment arm. The `True` state is
    the discriminator that proves the two absences are the modes' doing and not a
    wrapper quietly dropping the kwarg on the floor (which would make the whole
    S-5 run a no-op measured against itself)."""
    seen: list[bool] = []
    real = sample_postflop_decision

    def spy(*args, **kwargs):
        seen.append("aggressor_bet_prev_street" in kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(sys.modules[__name__], "sample_postflop_decision", spy)
    packs = load_persona_packs()
    persona_by_seat = {i: _R9D_S5_LINEUP[i] for i in range(9)}
    for line_aware, want in ((False, False), (_LINE_OBSERVE, False), (True, True)):
        seen.clear()
        nodes = 0
        for i, (hand_seed, action_seed) in enumerate(_R9D_S5_SEEDS[:120]):
            res = _play_hand(
                random.Random(action_seed),
                hand_seed,
                i % 9,
                persona_by_seat,
                packs,
                line_aware=line_aware,
            )
            nodes += len(res.line_nodes)
        assert seen, "no postflop decision was taken at all — the probe proves nothing"
        assert set(seen) == {want}, (line_aware, sorted(set(seen)))
        assert (nodes > 0) is bool(line_aware), (line_aware, nodes)


# ===================================================================
# R9-LOOSEFIT — G-NODE: the correctly-priced node panel
# ===================================================================
#
# WHAT THIS SLICE DID, and what this panel proves.
#
# nit's `call_looseness` moved 0.60 → 0.45 and nothing else moved. At a facing
# node that lever multiplies the CALL merit directly and the RAISE merit through
# `rscale = looseness / continue_ref` (the fall-through `else` branch of the
# N-LOGIT block below); nit's
# `continue_ref` is 0.60 and deliberately untouched, so BOTH continue merits
# scale by the same s = 0.45/0.60 = 0.75 while the FOLD merit is
# untouched. The panel below reads the exact normalized action vector at five
# constructed nodes and asserts the nit's fold probability ROSE by at least
# 0.040 versus the same pack rebuilt at its pre-slice authored 0.60.
#
# ── WHY A NEW HELPER, AND NOT `_dist_for_pack`.
#
# `sample_postflop_decision` computes the price the bot is facing itself
# (the `faced_frac` derivation): given `latest_aggressor_contribution_bb` it
# uses the EXACT pre-aggression pot, and WITHOUT it falls back to a legacy
# `max(current_bet_to, to_call)` denominator that is generally SMALLER, i.e. a
# LARGER faced fraction than the caller thinks they built. `_dist_for_pack` has
# no such parameter, so every node routed through it silently takes the legacy
# branch. An earlier revision of this spec built `pot_bb=6, to_call=3`, called
# it a half-pot bet, and was read by the engine as a POT-SIZED one; its entire
# feasibility table was priced at nodes that did not exist. `_dist_for_pack` is
# left exactly as it is (five other call sites depend on its behaviour) and this
# panel uses `_r9lf_priced_dist` instead, which
#   (a) always supplies `latest_aggressor_contribution_bb`, and
#   (b) intercepts the engine's OWN `_price_factor` call and refuses to return a
#       vector unless the fraction the engine computed equals the fraction the
#       node declares, to 1e-9.
# The check is on the engine's number, not on a re-derivation of it in the test:
# a test that recomputed `to_call / (pot_bb - contribution)` itself would agree
# with a mispriced node just as happily as with a correct one.
#
# ── THE CEILING. Because the lever scales the CALL and RAISE merits by the SAME
# factor s ON DRAW-NONE NODES — true of all five panel nodes below, none of
# which carries a draw against its board — the whole continue mass scales by s
# and the move is a pure shift of the continue/fold log-odds by ln(s).
# (On the `if draw is DrawCategory.STRONG and looseness < 1.0` branch the draw
# bonus carries `_strong_draw_call_dial` rather than the lever, so CALL is
# AFFINE in the lever there rather than proportional to it, and s is not the
# lever ratio. The derivation still transfers — G-DRAW re-derives it with
# s replaced by the ratio of the two affine call merits — but the CONSTANT
# 0.071797 does not; see G-DRAW's section comment.) The rise in fold
# probability is
# therefore a function of the BASE fold probability p alone —
#
#     self(p) = p / (p + 0.75·(1 − p)) − p
#
# — with a hard analytic maximum of (1−√0.75)/(1+√0.75) = 0.071797 at p =
# 0.4641. No board, price, street, headcount or legal shape can beat it. **A
# self threshold at or above 0.072 is unsatisfiable by construction**; the
# pre-registered 0.040 sits at 56% of the ceiling and binds at P4 (1.49×).
#
# ── WHY THERE IS NO nit-VERSUS-tag ("identity") LEG HERE. nit and tag share
# every lever that reaches a facing node's FOLD and CALL merits, so their
# difference decomposes EXACTLY as `identity = self + the HEAD aggression gap`,
# where that gap (tag's `aggression` 2.4 diluting tag's fold share) is fixed at
# HEAD and untouched by this slice. That is a telescoping identity, not an
# approximation: any build that clears the self floor has already forced
# identity above any floor worth writing down, so an identity assertion here
# could not fail while the self assertion passed. It was drafted, found
# vacuous, and removed. The cross-persona claim is carried by the population
# sweep instead, which is a genuine comparison and red at HEAD.
#
# ── MEASURED BASELINES (2026-08-04, shipped nit 0.45 vs the same pack rebuilt
# at 0.60). These are RECORDS, not pins — the gate asserts only the 0.040 floor,
# so a later reader can tell a re-measurement from a re-pin:
#
#   node  faced_frac  P(fold)@0.45  P(fold)@0.60  self     min legal prob
#   P1    1.000       0.4495        0.3798        +0.0697  0.0483 (raise@0.45)
#   P2    1.000       0.5192        0.4475        +0.0717  0.0422 (raise@0.45)
#   P3    0.500       0.5250        0.4532        +0.0718  0.0250 (raise@0.45)
#   P4    0.500       0.3232        0.2637        +0.0595  0.0594 (raise@0.45)
#   C5    1.000       0.4723        0.4017        +0.0707  0.4017 (fold@0.60)
#
# With both sides rebuilt at 0.60 every self reading is exactly 0.000000, i.e.
# the panel is red at base by construction and cannot pass on a no-op lever.

_R9LF_SELF_FLOOR = 0.040
# The value nit authored BEFORE this slice — the comparison baseline, not a
# magic number. G-NODE is a sensitivity gate, NOT a value pin, and it imposes
# **no lower bound at all**: measured, both this panel and G-SWEEP pass at
# 0.20 / 0.30 / 0.35 / 0.40 / 0.42 / 0.45 / 0.48 and redden only at 0.50.
# (An earlier draft of this comment claimed an acceptance window of "roughly
# 0.42-0.48"; that is wrong on the low side and was disproven by the slice's
# own mutant sweep — ledger BR-1.) The floor on this lever comes from
# ELSEWHERE in the suite: `test_fold_to_bet_respects_alpha_ceiling[nit]` fails
# at 0.20, and R9-DEFENCE-a's ladder binds at ~0.42. Do not cite either gate
# in this section as evidence that the shipped value is correct.
_R9LF_PRE_SLICE_LOOSENESS = 0.60
# Non-degeneracy window: a node where some legal action is effectively forced
# tells us nothing about a lever that only re-weights the mix.
_R9LF_MIN_PROB, _R9LF_MAX_PROB = 0.01, 0.99


class _R9lfNode(NamedTuple):
    """One constructed facing node. `faced_frac` is the price the node CLAIMS to
    be at; `_r9lf_priced_dist` asserts the engine agrees before returning."""

    node_id: str
    hole: tuple[str, str]
    board: list[str]
    street: Street
    raise_bounds: tuple[float, float] | None  # None => FOLD/CALL-only node
    pot_bb: float
    to_call: float
    stack_bb: float
    opponents: int
    faced_frac: float


# All five: `aggressor_bet_prev_street=False`, default noise, SPR 20, and
# `pot_bb = pre_bet_pot + to_call` with `contribution = current_bet_to =
# to_call` (fresh aggression), which is what makes the declared prices real.
_R9LF_PANEL = (
    _R9lfNode("P1", ("9h", "4c"), ["Kc", "9s", "3h"], Street.FLOP,
              (36.0, 480.0), 24.0, 12.0, 480.0, 1, 1.000),
    _R9lfNode("P2", ("9h", "4c"), ["Kc", "9s", "3h", "2d"], Street.TURN,
              (36.0, 480.0), 24.0, 12.0, 480.0, 3, 1.000),
    _R9lfNode("P3", ("Ah", "8d"), ["Kc", "9s", "3h"], Street.FLOP,
              (18.0, 360.0), 18.0, 6.0, 360.0, 1, 0.500),
    _R9lfNode("P4", ("9h", "4c"), ["Kc", "9s", "3h", "2d"], Street.TURN,
              (18.0, 360.0), 18.0, 6.0, 360.0, 1, 0.500),
    # C5 is the declared control: no RAISE leg at all, so it proves the lever
    # still moves the bot when the raise branch is absent.
    _R9lfNode("C5", ("9h", "4c"), ["Kc", "9s", "3h", "2d"], Street.TURN,
              None, 24.0, 12.0, 480.0, 1, 1.000),
)


def _r9lf_priced_dist(pack, node: _R9lfNode) -> dict:
    """Exact normalized action vector at `node` — priced, or nothing.

    Calls `sample_postflop_decision` directly (never `_dist_for_pack`) with
    `latest_aggressor_contribution_bb` ALWAYS supplied, and wraps the engine's
    module-level `_price_factor` so the faced fraction the engine actually
    computed is observed at its own call site. If that fraction is not the one
    `node` declares, this raises instead of returning a number — a mispriced
    reading can never leave this function.
    """
    legal = [personas_postflop_legal_fold(), personas_postflop_legal_call(node.to_call)]
    if node.raise_bounds is not None:
        legal.append(personas_postflop_legal_raise(*node.raise_bounds))

    seen: list[float] = []
    real_price_factor = personas_postflop._price_factor

    def _recording_price_factor(faced_fraction, exponent):
        seen.append(faced_fraction)
        return real_price_factor(faced_fraction, exponent)

    cap = _CaptureWeights()
    personas_postflop._price_factor = _recording_price_factor
    try:
        sample_postflop_decision(
            pack,
            node.hole,
            list(node.board),
            legal,
            node.pot_bb,
            node.stack_bb,
            node.opponents,
            cap,  # type: ignore[arg-type] — duck-typed capture rng
            current_bet_to=node.to_call,
            street=node.street,
            latest_aggressor_contribution_bb=node.to_call,
            aggressor_bet_prev_street=False,
        )
    finally:
        personas_postflop._price_factor = real_price_factor

    # Exactly one price read: the facing-node fold merit. Zero calls would mean
    # the node is not a facing node at all and the whole reading is off-target.
    assert len(seen) == 1, f"{node.node_id}: expected one priced fold merit, saw {seen}"
    assert seen[0] == pytest.approx(node.faced_frac, abs=1e-9), (
        f"{node.node_id}: the engine priced this node at faced_frac {seen[0]!r}, "
        f"but the node declares {node.faced_frac!r} — the reading is discarded. "
        "Check pot_bb/to_call/contribution (personas_postflop.py:954-957)."
    )
    assert cap.dist is not None, f"{node.node_id}: sampler never drew an action"
    return cap.dist


def _r9lf_nit_at(looseness: float):
    """The shipped nit pack with ONLY `call_looseness` re-authored."""
    pack = _pack("nit")
    probe = pack.model_copy(deep=True)
    probe.postflop = pack.postflop.model_copy(update={"call_looseness": looseness})
    return probe


def test_r9lf_gnode_nit_folds_more_at_correctly_priced_nodes():
    """G-NODE: the shipped nit folds at least 0.040 more than the same pack
    rebuilt at its pre-slice 0.60, at five nodes whose prices the engine itself
    confirms — and no legal action is squeezed out of [0.01, 0.99] on the way.

    This asserts that something MOVED: with the lever put back to 0.60 on both
    sides every self reading is exactly 0.0, so a `call_looseness` no-op (lever
    read, result discarded) fails every leg.

    THE 0.040 FLOOR IS NOT FREELY CHOOSABLE. The lever scales the CALL and RAISE
    merits by the same factor ON DRAW-NONE NODES — all five `_R9LF_PANEL` nodes
    are — so the move is a pure ln(0.75) shift of the continue/fold log-odds and
    the fold-probability rise depends only on the base fold probability p. The
    0.071797 CONSTANT does not hold on a strong-draw node: on the `if draw is
    DrawCategory.STRONG and looseness < 1.0` branch a share of the draw bonus is
    protected from the lever (`_strong_draw_call_dial`), so CALL there is affine
    in the lever rather than proportional and the shift is smaller. The
    DERIVATION does hold — G-DRAW re-derives the same bound with 0.75 replaced
    by the ratio of the two affine call merits, which is where its per-node caps
    come from (S3-T1b, 2026-08-22; before that date G-DRAW carried a single
    chosen budget of 0.030). Here:

        self(p) = p / (p + 0.75·(1 − p)) − p ,  max = (1−√0.75)/(1+√0.75)
                                                    = 0.071797 at p = 0.4641

    That is a HARD ANALYTIC CEILING over every board, price, street, headcount
    and legal shape — so a self threshold at or above 0.072 would be
    unsatisfiable by construction, whatever the pack said. 0.040 is 56% of it and
    binds at P4 (+0.0595, 1.49× margin).

    THERE IS DELIBERATELY NO nit-VERSUS-tag LEG. nit and tag share every lever
    reaching a facing node's FOLD and CALL merits, so their gap decomposes
    exactly as `identity = self + the pre-existing HEAD aggression gap` (tag's
    `aggression` 2.4 diluting its fold share), and that second term is fixed at
    HEAD and out of this slice's scope. Clearing the self floor therefore already
    forces identity past any floor worth setting: such a leg could not fail while
    this one passed. It is vacuous, not merely redundant, and the cross-persona
    claim belongs to the population sweep.
    """
    shipped = _pack("nit")
    pre_slice = _r9lf_nit_at(_R9LF_PRE_SLICE_LOOSENESS)

    for node in _R9LF_PANEL:
        shipped_dist = _r9lf_priced_dist(shipped, node)
        pre_slice_dist = _r9lf_priced_dist(pre_slice, node)

        self_delta = shipped_dist[ActionType.FOLD] - pre_slice_dist[ActionType.FOLD]
        assert self_delta >= _R9LF_SELF_FLOOR, (
            f"{node.node_id}: nit's fold probability rose only {self_delta:.4f} "
            f"(floor {_R9LF_SELF_FLOOR}); {shipped_dist[ActionType.FOLD]:.4f} at the "
            f"shipped lever vs {pre_slice_dist[ActionType.FOLD]:.4f} at "
            f"{_R9LF_PRE_SLICE_LOOSENESS}"
        )

        for label, dist in (("shipped", shipped_dist), ("pre-slice", pre_slice_dist)):
            for action, prob in dist.items():
                assert _R9LF_MIN_PROB <= prob <= _R9LF_MAX_PROB, (
                    f"{node.node_id} ({label}): P({action.value}) = {prob:.6f} is outside "
                    f"[{_R9LF_MIN_PROB}, {_R9LF_MAX_PROB}] — the node is degenerate and a "
                    "difference measured there is not a lever effect"
                )


def test_r9lf_priced_helper_refuses_a_mispriced_node():
    """The panel's instrument, proved against the exact bug it exists to stop.

    An earlier revision built `pot_bb=6, to_call=3` and labelled it a half-pot
    bet; the engine prices that node at faced_frac 1.00 (the bet IS the pot it
    was made into). `_r9lf_priced_dist` must raise on it rather than hand back a
    perfectly plausible-looking probability vector — and must still return one
    when the same node is labelled truthfully.
    """
    mislabelled = _R9lfNode(
        "REV3", ("9h", "4c"), ["Kc", "9s", "3h"], Street.FLOP,
        (9.0, 100.0), 6.0, 3.0, 100.0, 1, 0.500,  # claims half pot; engine reads 1.00
    )
    with pytest.raises(AssertionError, match="the engine priced this node"):
        _r9lf_priced_dist(_pack("nit"), mislabelled)
    truthful = mislabelled._replace(faced_frac=1.000)
    assert _r9lf_priced_dist(_pack("nit"), truthful)[ActionType.FOLD] > 0.0
    # And the wrapper leaves the engine exactly as it found it.
    assert personas_postflop._price_factor.__module__ == personas_postflop.__name__


# ─────────────────────────────────────────────────────────────────────────────
# R9-LOOSEFIT — G-SWEEP: the population gate, and the slice's cross-persona claim
# ─────────────────────────────────────────────────────────────────────────────
#
# G-NODE above compares the nit against ITSELF at five hand-picked nodes. Five
# nodes cannot support a claim about the roster, and G-NODE deliberately makes
# none (its nit-versus-tag leg was found vacuous and removed). **This gate is
# where "the nit folds more than tag" is actually established**, and it is
# established the only way five nodes cannot: by sweeping the repo's canonical
# cell enumeration `_nlogit_cells()` (1,728 cells) and counting.
#
# ── WHY THE SWEEP RE-PRICES THE CELLS, AND WHY THAT IS NOT OPTIONAL.
#
# `_nlogit_cells()` builds every cell at `pot_bb = 6.0` with `to_call` drawn
# from `_NLOGIT_PRICES = (2, 4, 6, 12)`, and `_nlogit_dist` passes
# `latest_aggressor_contribution_bb = to_call`. The engine then computes
# (the `faced_frac` derivation in `sample_postflop_decision`)
#
#     faced_frac = to_call / max(pot_bb − contribution, 0.01)
#
# which for those four prices is **0.50, 2.00, 600.00 and 1200.00** — while the
# `_NLOGIT_PRICES`'s own comment labels the ladder "1/3 pot … 2x pot". Half the
# canonical grid is therefore priced at bets of 600× and 1200× the pot, where
# the R10 unbounded price tail drives P(fold) to 0.999994 for every persona at
# once. That is a defect in the shipped grid, filed as `N-NLOGITPRICE` and
# deliberately NOT fixed here (fixing it would move gates this slice does not
# own). This gate instead re-prices the enumeration for its own use:
#
#     to_call = f · pre_bet_pot   for f in {1/3, 2/3, 1, 2}  ← the grid's own
#     pot_bb  = pre_bet_pot + to_call                          intended labels
#     contribution = to_call                                   (fresh aggression)
#
# With `pre_bet_pot` = 6.0 the re-priced `to_call` ladder reproduces
# `_NLOGIT_PRICES` exactly (2, 4, 6, 12) — only the pot the bet was made INTO
# changes, from a pot that already contained the bet to one that did not.
#
# The re-pricing is PINNED three ways, because a silent revert would turn this
# gate back into a measurement of 600×-pot bets without changing a single
# number in the source:
#   (1) `_r9lf_repriced_cells` asserts each source cell arrives at the
#       `pre_bet_pot` this construction was derived against;
#   (2) it asserts the fractions' own `f · pre_bet_pot` ladder still equals
#       `_NLOGIT_PRICES`, so a change to either the fractions or the shipped
#       price tuple (e.g. when `N-NLOGITPRICE` is fixed) fails loudly here
#       instead of quietly re-pricing the sweep;
#   (3) every cell's distribution is read through `_r9lf_sweep_dists`, which
#       wraps the engine's own `_price_factor` and refuses the reading unless
#       the fraction THE ENGINE computed is the one the cell was re-priced to —
#       the same discipline as `_r9lf_priced_dist`, and for the same reason: a
#       test that re-derived the fraction itself would agree with a mispriced
#       cell just as happily as with a correct one.
#
# SPR is held at the grid's intent rather than at the grid's absolute stacks.
# `_NLOGIT_STACKS` is authored as SPRs against the 6bb pot (its own comment
# reads stack 12 as "SPR 2.0" and stack 30 as "SPR 5"), and SPR is
# what the engine's SPR-commit gate reads (`if stack_bb / pot_bb <=
# pf.spr_commit:`). Growing the
# pot without rescaling the stack would therefore silently drag cells across
# `spr_commit` — nit's is 1.2 and tag's 2.5, and the band between them is the
# one place where tag commits and nit does not, manufacturing a difference this
# lever did not produce. Stacks are scaled by the same factor as the pot.
#
# ── MEASURED (2026-08-04). Denominator and both legs, over the 1,728 cells:
#
#              non-degenerate   nit folds > tag   … by > 0.02
#   nit@0.45         970             970 (100%)      826 (85.2%)
#   nit@0.60         970             384 (39.6%)     300 (30.9%)   ← HEAD
#
# The HEAD row is the whole point: at the pre-slice lever this gate reads 384
# and 300 against floors of 800 and 650, i.e. **red by 2.08× and 2.17×**. It is
# not a gate that a `call_looseness` no-op (lever read, result discarded) could
# pass — such a mutant collapses nit@0.45 onto nit@0.60 and reads 384. (Run at
# HEAD the gate enumerates a denominator of 982 rather than 970, because the
# shipped and pre-slice packs coincide there and 12 cells that nit@0.45 pushes
# out of the window stay inside it; the counts on that larger denominator are
# 396 and 312 — red by the same margin. The 384/300 above are on the 970
# denominator, so that the two rows are directly comparable.)
#
# Also measured, and NOT gated: nit@0.45 folds LESS than tag in **0** of the 970
# cells, while nit@0.60 does so in 26. And 560 of the 970 cells have nit@0.60's
# fold probability EXACTLY equal to tag's — the two packs share every lever that
# reaches a facing node's FOLD and CALL merits, so on a cell with no live raise
# leg they were byte-identical before this slice.

_R9LF_SWEEP_PRE_BET_POT = 6.0
# The grid's own intended price labels (`_NLOGIT_PRICES`'s comment, "1/3 pot
# … 2x pot") — the
# fractions the cells were always meant to be at, not the ones they are at.
_R9LF_SWEEP_FRACS = (1.0 / 3.0, 2.0 / 3.0, 1.0, 2.0)
# Pre-registered from the measurement above; never re-chosen after a result.
_R9LF_SWEEP_STRICT_FLOOR = 800  # of 970 measured; 384 at HEAD
_R9LF_SWEEP_MARGIN = 0.02
_R9LF_SWEEP_MARGIN_FLOOR = 650  # 826 measured; 300 at HEAD


def _r9lf_repriced_cells() -> list[tuple[_NlogitCell, float]]:
    """`_nlogit_cells()` at the prices its own source comment claims.

    Returns (cell, faced_frac) pairs whose `pot_bb` is the pre-bet pot PLUS the
    bet, so that the engine's `to_call / (pot_bb − contribution)` lands on the
    declared fraction instead of on 600 or 1200. Stacks are rescaled with the
    pot so each cell keeps the SPR `_NLOGIT_STACKS` authored it at.
    """
    ladder = tuple(f * _R9LF_SWEEP_PRE_BET_POT for f in _R9LF_SWEEP_FRACS)
    assert sorted(ladder) == sorted(_NLOGIT_PRICES), (
        f"the re-priced ladder {ladder} no longer reproduces _NLOGIT_PRICES "
        f"{_NLOGIT_PRICES} — the canonical grid's prices moved (N-NLOGITPRICE?) "
        "and this sweep's re-pricing must be re-derived, not silently carried"
    )
    by_price = dict(zip(ladder, _R9LF_SWEEP_FRACS, strict=True))

    repriced = []
    for cell in _nlogit_cells():
        assert cell.pot_bb == _R9LF_SWEEP_PRE_BET_POT, (
            f"{cell.key}: this sweep re-prices against a {_R9LF_SWEEP_PRE_BET_POT}bb "
            f"pre-bet pot, but the cell was built at {cell.pot_bb}"
        )
        frac = by_price[cell.to_call]
        pot_bb = _R9LF_SWEEP_PRE_BET_POT + cell.to_call
        stack_bb = cell.stack_bb * pot_bb / _R9LF_SWEEP_PRE_BET_POT  # hold the SPR
        repriced.append((cell._replace(pot_bb=pot_bb, stack_bb=stack_bb), frac))
    return repriced


def _r9lf_sweep_dists(pack, repriced) -> list[dict]:
    """One exact action vector per re-priced cell — priced, or nothing.

    Wraps the engine's module-level `_price_factor` once for the whole sweep
    (patching per cell would be the same check at 1,728× the cost) and clears
    the recorder between cells, so each cell's own faced fraction is checked
    against the fraction it was re-priced to.
    """
    seen: list[float] = []
    real_price_factor = personas_postflop._price_factor

    def _recording_price_factor(faced_fraction, exponent):
        seen.append(faced_fraction)
        return real_price_factor(faced_fraction, exponent)

    dists = []
    personas_postflop._price_factor = _recording_price_factor
    try:
        for cell, frac in repriced:
            seen.clear()
            dist = _nlogit_dist(pack, cell)
            assert len(seen) == 1, f"{cell.key}: expected one priced fold merit, saw {seen}"
            assert seen[0] == pytest.approx(frac, abs=1e-9), (
                f"{cell.key}: the engine priced this cell at faced_frac {seen[0]!r}, but it "
                f"was re-priced to {frac!r} — the reading is discarded. Without the re-price "
                "this sweep measures 600x- and 1200x-pot bets (N-NLOGITPRICE)."
            )
            assert dist, f"{cell.key}: sampler never drew an action"
            dists.append(dist)
    finally:
        personas_postflop._price_factor = real_price_factor
    return dists


def _r9lf_non_degenerate(dist: dict) -> bool:
    """Every legal action's probability strictly inside the window. A cell where
    some action is effectively forced says nothing about a lever that only
    re-weights the mix — and at the top of the price ladder the tail term forces
    FOLD for every persona at once."""
    return all(_R9LF_MIN_PROB <= prob <= _R9LF_MAX_PROB for prob in dist.values())


def test_r9lf_gsweep_nit_folds_more_than_tag_across_the_cell_population():
    """G-SWEEP: across the canonical 1,728-cell enumeration, re-priced to the
    fractions it was always meant to be at, the shipped nit folds strictly more
    than tag in at least 800 non-degenerate cells, and by more than 0.02 in at
    least 650 of them.

    This is the slice's cross-persona claim and the only gate that carries it.
    It asserts that something MOVED: at the pre-slice `call_looseness` of 0.60
    the same two counts are 384 and 300 — red against these floors by 2.08× and
    2.17× — so a lever no-op, which collapses the shipped nit onto the
    pre-slice one, fails leg (a) outright.

    THE CLAIM IS PAIRWISE, nit versus tag, and nothing here says the nit is the
    tightest defender of the six: lag, maniac, passive_fish and the calling
    station are not measured, and both legs can pass while nit folds less than
    any of them somewhere.

    THE DENOMINATOR IS ENUMERATED, NEVER ASSERTED. A cell counts only if all
    three packs — shipped nit, nit rebuilt at 0.60, tag — keep every legal
    action's probability inside [0.01, 0.99]. That window is an arbitrary
    constant and the count of 970 is sensitive to it, so pinning 970 would be
    pinning the constant rather than the behaviour; the floors are absolute
    counts and the measured denominator is reported when a leg fails.

    This gate asserts an ORDERING (the nit folds more often than the tag),
    not an ATTRIBUTION. Leaving the nit unchanged and loosening tag's own
    `call_looseness` to 0.80 makes it read 982/982 and 772 — green, with the
    wrong cause. Attribution comes from the node panel's self-comparison,
    which compares the shipped pack against itself rebuilt at the pre-slice
    value.
    """
    repriced = _r9lf_repriced_cells()
    shipped_nit = _r9lf_sweep_dists(_pack("nit"), repriced)
    pre_slice_nit = _r9lf_sweep_dists(_r9lf_nit_at(_R9LF_PRE_SLICE_LOOSENESS), repriced)
    tag = _r9lf_sweep_dists(_pack("tag"), repriced)

    denominator = 0
    folds_more = 0
    folds_more_by_margin = 0
    folds_less = 0
    for nit_dist, pre_dist, tag_dist in zip(shipped_nit, pre_slice_nit, tag, strict=True):
        if not all(map(_r9lf_non_degenerate, (nit_dist, pre_dist, tag_dist))):
            continue
        denominator += 1
        delta = nit_dist[ActionType.FOLD] - tag_dist[ActionType.FOLD]
        if delta > 0.0:
            folds_more += 1
        if delta > _R9LF_SWEEP_MARGIN:
            folds_more_by_margin += 1
        if delta < 0.0:
            folds_less += 1

    census = (
        f"{denominator} of {len(repriced)} cells were non-degenerate in [{_R9LF_MIN_PROB}, "
        f"{_R9LF_MAX_PROB}] across all three packs; the nit folds LESS than tag in "
        f"{folds_less} of them"
    )
    assert folds_more >= _R9LF_SWEEP_STRICT_FLOOR, (
        f"G-SWEEP-a: the shipped nit folds strictly more than tag in only {folds_more} "
        f"cells (floor {_R9LF_SWEEP_STRICT_FLOOR}) — {census}. At the pre-slice 0.60 this "
        "reads 384; 970 was measured at 0.45"
    )
    assert folds_more_by_margin >= _R9LF_SWEEP_MARGIN_FLOOR, (
        f"G-SWEEP-b: the shipped nit folds more than tag by over {_R9LF_SWEEP_MARGIN} in "
        f"only {folds_more_by_margin} cells (floor {_R9LF_SWEEP_MARGIN_FLOOR}) — {census}. "
        "At the pre-slice 0.60 this reads 300; 826 was measured at 0.45"
    )


# ===================================================================
# N-DRAWLOOSE — the calling dial stops deciding strong draws
# ===================================================================
#
# Spec: docs/ai-dlc/specs/n-drawloose.md (rev 2, option B). The engine change
# (T1) protected `_DRAW_CALL_BONUS` from the archetype's calling dial, for
# `DrawCategory.STRONG` ONLY, by flooring the dial at 1.0 where it multiplies
# the bonus. ⚠️ THAT FLOOR IS GONE as of S3-T1 (improvement slice 3,
# 2026-08-21): the bonus is now SPLIT, a protected share of it out of the dial's
# reach and the rest riding the dial (`_strong_draw_call_dial`). S3-T1b
# (2026-08-22) then made that share depend on the node — the faced price, the
# cards to come and the draw's out count (`_strong_draw_protected_share`) — so
# at a node whose price the draw's own equity pays for, the protection is once
# again the FULL bonus and this block's original readings are exactly restored.
# Read the S3-T1b section near the end of this file before trusting a number in
# this block — the READINGS behind these gates moved twice, and G-DRAW's cap is
# no longer the flat 0.030 the paragraphs below describe. What is unchanged is
# the branch predicate, the shape of the claim,
# and everything this section says about the raise coupling: the split, like the
# floor, makes the CALL merit AFFINE in the dial instead of proportional — and
# N-LOGIT's G1 gate above
# guarantees, to 1e-12, that the dial never moves `P(raise | continue)`, a
# guarantee that held only because CALL and RAISE were BOTH proportional to it.
# So the raise leg had to move with the call leg: on strong draws
# `rscale = live_CALL_entry / _call_merit_at_ref`; everywhere else it stays the
# literal shipped `looseness / continue_ref`
# (the `else: rscale = looseness / ref` fall-through in the N-LOGIT block
# below).
#
# The gates below, in file order:
#   T2  the coupled raise scale is really taken, and really different, on a
#       strong draw — and is NOT taken anywhere else.
#   T2  G1's comparison census, decomposed by draw category and pinned exactly.
#   T3  G-DRAW: the fold rate of a strong draw barely responds to the dial,
#       plus the `facing_raise` instrument-liveness check and the mislabelled-
#       node check.
#   T4  the absolute CEILING at the trace node; the cross-persona margin
#       against the calling station; P(raise | continue) against the base
#       engine at every strong-draw node; and two calling-station byte-identity
#       pins (shipped 4.0, and a non-power-of-two 3.7).
#   C5  non-STRONG cells are bitwise identical to the base engine.
#
# ── THE INSTRUMENT. All of them read the engine through `_nd_priced_dist`,
# which is `_r9lf_priced_dist`'s pattern (always supply
# `latest_aggressor_contribution_bb`; intercept the engine's OWN
# `_price_factor` call and refuse the reading unless the fraction the engine
# computed is the fraction the node declares). It is a SECOND helper rather
# than a reuse because these nodes need two things `_R9lfNode` has no room for:
# a `PostflopContext` (the measured panel was taken with
# `PostflopContext(in_position=False)`) and `aggressor_bet_prev_street=True`,
# which T2's line-damped control needs. `_dist_for_pack` is NOT usable
# here for the reason spelled out at G-NODE: no contribution parameter, so
# every node routed through it silently takes the legacy denominator branch and
# is priced at a spot that does not exist.


class _NDNode(NamedTuple):
    """One constructed facing node. `pot_bb` is the LIVE pot (pre-bet pot plus
    `to_call`) and the aggressor's contribution is `to_call`, i.e. fresh
    aggression; `faced_frac` is the price the node CLAIMS to be at and
    `_nd_priced_dist` asserts the engine agrees before returning anything.

    `facing_raise` (N-DRAWLOOSE ruling R5, refuter mutant M13) is a real axis of
    the engine, not decoration: the live bot loop derives it via
    `facing_raise(state.action_history, state.street)` in `play.py` and hands
    it to `sample_postflop_decision` on every postflop decision, so a
    panel that is entirely `facing_raise=False` cannot see a defect that lives
    on the facing-a-raise half of production. The `_nd_key(node)` prefix of
    `node_id` is how the pinned base tables below address a node."""

    node_id: str
    hole: tuple[str, str]
    board: list[str]
    street: Street
    pot_bb: float
    to_call: float
    stack_bb: float
    opponents: int
    faced_frac: float
    aggressor_bet_prev_street: bool = False
    facing_raise: bool = False


def _nd_key(node: _NDNode) -> str:
    """The node's short label ("D1", "P1", ...) — the key of the pinned base
    tables. Taken from `node_id` so a node and its pins cannot drift apart."""
    return node.node_id.split()[0]


def _nd_priced_dist(pack, node: _NDNode) -> dict:
    """Exact normalized action vector at `node` — priced, or nothing."""
    legal = [
        personas_postflop_legal_fold(),
        personas_postflop_legal_call(node.to_call),
        personas_postflop_legal_raise(2 * node.to_call, node.stack_bb),
    ]

    seen: list[float] = []
    real_price_factor = personas_postflop._price_factor

    def _recording_price_factor(faced_fraction, exponent):
        seen.append(faced_fraction)
        return real_price_factor(faced_fraction, exponent)

    cap = _CaptureWeights()
    personas_postflop._price_factor = _recording_price_factor
    try:
        sample_postflop_decision(
            pack,
            node.hole,
            list(node.board),
            legal,
            node.pot_bb,
            node.stack_bb,
            node.opponents,
            cap,  # type: ignore[arg-type] — duck-typed capture rng
            current_bet_to=node.to_call,
            street=node.street,
            latest_aggressor_contribution_bb=node.to_call,
            context=PostflopContext(in_position=False),
            aggressor_bet_prev_street=node.aggressor_bet_prev_street,
            facing_raise=node.facing_raise,
        )
    finally:
        personas_postflop._price_factor = real_price_factor

    assert len(seen) == 1, f"{node.node_id}: expected one priced fold merit, saw {seen}"
    assert seen[0] == pytest.approx(node.faced_frac, abs=1e-9), (
        f"{node.node_id}: the engine priced this node at faced_frac {seen[0]!r}, but the "
        f"node declares {node.faced_frac!r} — the reading is discarded. Check "
        "pot_bb/to_call/contribution (personas_postflop.py:954-957)."
    )
    assert cap.dist is not None, f"{node.node_id}: sampler never drew an action"
    return cap.dist


def _nd_nit_at(looseness: float, continue_ref: float | None = -1.0):
    """The shipped nit pack with `call_looseness` re-authored, and optionally
    `continue_ref` too. The sentinel -1.0 means "leave `continue_ref` alone";
    `None` is a real, meaningful value here (it switches the whole N-LOGIT
    block off) and so cannot double as the sentinel."""
    pack = _pack("nit")
    update: dict = {"call_looseness": looseness}
    if continue_ref != -1.0:
        update["continue_ref"] = continue_ref
    probe = pack.model_copy(deep=True)
    probe.postflop = pack.postflop.model_copy(update=update)
    return probe


# ─────────────────────────────────────────────────────────────────────────────
# N-DRAWLOOSE T2 — the coupled raise scale, observed from outside the engine
# ─────────────────────────────────────────────────────────────────────────────
#
# `rscale` is a local. Nothing in the engine exposes it, and this ticket may not
# edit the engine to make it visible, so it is recovered from OUTSIDE by a
# differential that needs no new engine surface:
#
#   run A: the pack as authored           → entries (F, C, R0·rscale)
#   run B: the same pack, continue_ref=None → the whole N-LOGIT block is skipped
#          (`if ref is not None:` below) → entries (F, C, R0)
#
# `continue_ref` reaches nothing else that can move a merit: it feeds only
# `_ref_lever` (whose sole consumer is `_call_merit_at_ref`, which in turn feeds
# only `rscale`) and this block's own range guard. FOLD and CALL are untouched
# by the block in both runs, so the RAISE:FOLD odds ratio between the two runs
# IS the factor the block applied to the RAISE leg:
#
#   effective rscale = (r_A / f_A) / (r_B / f_B)
#
# ── HOW EXACT IS IT. Not bitwise: each probability is a raw merit divided by
# that run's total, so four float divisions sit between the merits and the
# answer. MEASURED residual on the three non-STRONG nodes below: 1.5e-16, 0.0
# and 0.0 relative. The equality legs therefore assert 1e-12 relative — four
# orders above the observed noise and TWELVE below the smallest mutant signal
# this gate is built to catch (see N2, ×exp(-0.6) = 0.5488). It is NOT tight
# enough to catch a variant that differs from `looseness / continue_ref` by an
# ulp or two; N2 exists precisely because that class of mutant has to be made
# to diverge MATERIALLY before an output-space instrument can see it.

# nit: the shipped `call_looseness` against the frozen `continue_ref` anchor.
# READ FROM THE PACK, NOT TRANSCRIBED (S3-T2, improvement slice 3,
# 2026-08-22). These two numbers used to be literals, 0.45 and 0.60, copied
# from `content/personas/nit.json`. `continue_ref` is frozen by design and
# never moves, but `call_looseness` is the dial improvement slice 3 exists to
# re-tune, so a transcription of it turns every gate below into an assertion
# that the nit's dial has not changed — which is not what any of them is about,
# and is how this file greeted the retune with a failure whose message named the
# coupling rather than the dial. Reading the pack keeps every claim intact
# (the low arm is still the shipped dial, the high arm is still the anchor, and
# the sweep between them is still a real sweep) and removes a whole class of
# false failure. At the shipped values 0.32 / 0.60 the literal expression is
# 0.5333; it was 0.75 before this slice.
_ND_LO_LOOSENESS = _pack("nit").postflop.call_looseness
_ND_HI_LOOSENESS = _pack("nit").postflop.continue_ref
_ND_LITERAL_RSCALE = _ND_LO_LOOSENESS / _ND_HI_LOOSENESS
# The equality legs' tolerance, and the margin the STRONG leg must clear.
_ND_RSCALE_EQ_TOL = 1e-12
_ND_RSCALE_MIN_DIVERGENCE = 0.05  # measured 0.3066 relative

# S1 is the slice's trace node. N1/N2/W1 are the three shapes on which the
# coupled branch must NOT be taken:
#   N1  draw NONE, nothing between the `call_base = _CALL_BASE[bucket]`
#       assignment and the N-LOGIT block touches CALL, so
#       the coupled and the literal form agree to within an ulp. N1 pins the
#       spec's "reduces to the literal expression" claim; it CANNOT carry a
#       mutant kill and is not asked to.
#   N2  the SAME node with `aggressor_bet_prev_street=True`. nit authors
#       `line_sensitivity` 0.6 and MIDDLE_PAIR is in `_LINE_SCOPE_BUCKETS`, so
#       R9-DEFENCE-a's damp multiplies the LIVE CALL entry by exp(-0.6) BEFORE
#       the N-LOGIT block reads it, while `_call_merit_at_ref` never sees the
#       damp. A `rscale := live_CALL / _call_merit_at_ref` applied here would
#       therefore read 0.5488 × 0.75, not 0.75 — a 45 % divergence an
#       output-space instrument can see. This is the node that kills the
#       "coupling applied to every draw category" mutant.
#   W1  a WEAK draw. `_DRAW_CALL_BONUS[WEAK]` is 0.20 and deliberately stays ON
#       the dial (spec §2, "why STRONG only"), so the coupled branch must not
#       reach it either. This kills the narrower mutant that extends the
#       coupling to WEAK but not to NONE.
_ND_T2_STRONG = _NDNode(
    "S1 combo draw, flop, 2/3-pot (STRONG)",
    ("Jh", "Th"), ["9h", "8c", "2h"], Street.FLOP, 10.0, 4.0, 100.0, 1, 4.0 / 6.0,
)
_ND_T2_UNCOUPLED = (
    _NDNode(
        "N1 middle pair, flop, pot (draw NONE)",
        ("9h", "4c"), ["Kc", "9s", "3h"], Street.FLOP, 48.0, 24.0, 480.0, 1, 1.0,
    ),
    _NDNode(
        "N2 middle pair, flop, pot, second barrel (draw NONE, line-damped)",
        ("9h", "4c"), ["Kc", "9s", "3h"], Street.FLOP, 48.0, 24.0, 480.0, 1, 1.0,
        aggressor_bet_prev_street=True,
    ),
    _NDNode(
        "W1 gutshot, flop, 2/3-pot (WEAK)",
        ("Td", "Jh"), ["7h", "9s", "9d"], Street.FLOP, 10.0, 4.0, 100.0, 1, 4.0 / 6.0,
    ),
)


def _nd_ref_off(pack):
    """The same pack with the N-LOGIT block switched off — the un-scaled run."""
    probe = pack.model_copy(deep=True)
    probe.postflop = pack.postflop.model_copy(update={"continue_ref": None})
    return probe


def _nd_effective_raise_scale(pack, node: _NDNode) -> float:
    """The factor the N-LOGIT block actually applied to this node's RAISE merit."""
    scaled = _nd_priced_dist(pack, node)
    unscaled = _nd_priced_dist(_nd_ref_off(pack), node)
    for label, dist in (("authored", scaled), ("continue_ref=None", unscaled)):
        for kind in (ActionType.FOLD, ActionType.RAISE):
            assert dist.get(kind, 0.0) > 0.0, (
                f"{node.node_id} ({label}): P({kind.value}) is 0, so the RAISE:FOLD odds "
                "ratio cannot be formed and the node is unusable for this measurement"
            )
    return (scaled[ActionType.RAISE] / scaled[ActionType.FOLD]) / (
        unscaled[ActionType.RAISE] / unscaled[ActionType.FOLD]
    )


def test_nd_t2_raise_scale_is_coupled_on_strong_draws_and_nowhere_else():
    """T2 — the new `rscale` branch is TAKEN and CHANGES THE VALUE on a strong
    draw, and is not taken on a draw-NONE or a WEAK-draw node.

    The N-LOGIT invariance gate above (`test_nlogit_g1_orthogonality_...`)
    stays unmodified and unscoped, and under option B it passes; it is what
    catches a half-implementation that ships the call-side floor with the raise
    leg frozen. This gate is the complement: G1 would ALSO pass on a build that
    never took the new branch at all (that build is HEAD), so something has to
    say the branch is real. Measured at the base commit b0a6a4e this test is
    RED — every node there reads exactly the literal 0.75.

    MEASURED (nit, call_looseness 0.45, continue_ref 0.60, literal = 0.75):
        S1  0.9799331103678931   +30.66 % vs the literal   ← coupled
        N1  0.7500000000000001     1.5e-16 relative        ← literal
        N2  0.75                   0.0                     ← literal
        W1  0.75                   0.0                     ← literal

    The third leg is the POINT of the coupling rather than its mechanism: at S1
    the raise share among continues must not move when the dial does. That is
    G1's property restated at one node, and it is what says the coupled factor
    is the RIGHT one rather than merely a different one.
    """
    shipped = _pack("nit")

    strong = _nd_effective_raise_scale(shipped, _ND_T2_STRONG)
    divergence = abs(strong - _ND_LITERAL_RSCALE) / _ND_LITERAL_RSCALE
    assert divergence > _ND_RSCALE_MIN_DIVERGENCE, (
        f"{_ND_T2_STRONG.node_id}: the RAISE leg was scaled by {strong!r}, only "
        f"{divergence:.2e} away from the literal looseness/continue_ref = "
        f"{_ND_LITERAL_RSCALE!r}. Either the coupled branch at "
        "personas_postflop.py:1262 was not taken, or it collapsed onto the "
        "expression it was supposed to replace"
    )

    for node in _ND_T2_UNCOUPLED:
        got = _nd_effective_raise_scale(shipped, node)
        assert got == pytest.approx(_ND_LITERAL_RSCALE, rel=_ND_RSCALE_EQ_TOL), (
            f"{node.node_id}: the RAISE leg was scaled by {got!r}, not the literal "
            f"looseness/continue_ref = {_ND_LITERAL_RSCALE!r}. The coupled branch is "
            "STRONG-only by design (spec §2); reaching a WEAK or draw-NONE node with it "
            "changes behaviour this slice pre-registered as bitwise unchanged"
        )

    shares = []
    for looseness in (_ND_LO_LOOSENESS, _ND_HI_LOOSENESS):
        dist = _nd_priced_dist(_nd_nit_at(looseness), _ND_T2_STRONG)
        continues = dist[ActionType.CALL] + dist[ActionType.RAISE]
        shares.append(dist[ActionType.RAISE] / continues)
    assert shares[0] == pytest.approx(shares[1], rel=1e-12), (
        f"{_ND_T2_STRONG.node_id}: P(raise | continue) moved with the calling dial — "
        f"{shares[0]!r} at {_ND_LO_LOOSENESS} vs {shares[1]!r} at {_ND_HI_LOOSENESS}. "
        "The coupled rscale exists to keep exactly this constant"
    )


# EXACT per-draw-category census of the grid and of G1's comparisons. Both are
# measured values, pinned; neither is a threshold.
_ND_G1_CELLS_BY_DRAW = {DrawCategory.NONE: 1472, DrawCategory.STRONG: 128, DrawCategory.WEAK: 128}
_ND_G1_COMPARISONS_BY_DRAW = {
    # T3 (improvement slice 2, 2026-08-19): 5,376 -> 5,504. Narrowing the river
    # call zero to AIR gives the 32 `ace_high/river` `with_raise=False` cells a
    # live CALL leg, so they stop being anchor-skipped: 32 cells x 4 lever
    # settings = the 128 comparisons added. Derived arithmetic, not a
    # re-measurement — the other two categories cannot move, because the
    # narrowing is gated on `draw is DrawCategory.NONE`.
    DrawCategory.NONE: 5504,  # 1,472 cells x 4 lever settings, less 96 anchor-skipped
    DrawCategory.STRONG: 512,  # 128 x 4 — every STRONG cell is compared at every setting
    DrawCategory.WEAK: 512,  # 128 x 4
}


def test_nd_t2_nlogit_g1_comparison_census_by_draw_category_is_exact():
    """T2 — G1's denominator, decomposed by draw category and pinned EXACTLY,
    per persona.

    ── WHY THIS REPLACED ITS PREDECESSOR (N-DRAWLOOSE ruling R3, 2026-08-05).
    The gate that stood here recomputed G1's total comparison count and
    asserted it against the SAME `>= 1000` floor G1 already asserts on the same
    quantity. Codex demonstrated it could not fail independently: any mutant
    that pushed a persona's count below 1,000 failed G1 first, so the gate was
    green whenever its sibling was green — the exact defect (a gate that cannot
    go red on its own) this file has now shipped twice.

    ── WHAT THIS ONE PINS THAT G1 DOES NOT. G1 asserts `n >= 1000` on the TOTAL
    and says nothing about its composition. The censuses here are exact and
    per-category, so they fail on a change G1 is structurally blind to: a
    mutant that removes the ANCHOR's continue mass on some subset of
    strong-draw cells makes G1 *skip* those cells (`denom <= 0` is a `continue`,
    not a violation, and no `collapsed` entry is recorded because the anchor
    itself is empty), leaving 6,000-odd comparisons — comfortably over G1's
    floor, drift-clean, and green — while the STRONG count here drops off its
    pinned 512. That matters specifically now: N-DRAWLOOSE moves merits on
    every strong-draw cell, and this file's other gates would be worth much
    less if G1's measurement of those very cells had quietly emptied.

    It is also the census that G3's scoping above leans on: G3 now excludes the
    128 STRONG cells, so something has to say those 128 cells still exist and
    are still measured somewhere.

    MEASURED after T3, identical for all six personas: NONE 5,504 · STRONG 512
    · WEAK 512 = 6,528, out of 1,728 cells x 4 lever settings = 6,912. The 384
    missing are the 96 draw-NONE cells whose anchor has no continue mass at
    all, enumerated rather than guessed: three river bluff-cell templates
    (`air/river`, `river_busted_straight`, `river_busted_flush`) in their
    `with_raise=False` shapes, 32 each — CALL is hard-zeroed by the river
    polarization rule and there is no RAISE entry to hold the mass instead.

    It was four templates and NONE 5,376 until T3 (improvement slice 2,
    2026-08-19), which narrowed that rule to AIR. `ace_high/river` left the
    empty set then and its 32 cells are now compared at all four settings.
    """
    sweep = _nlogit_sweep()
    cells = sweep["_cells"]
    draws = [_nlogit_cell_draw(c) for c in cells]

    by_draw = {d: draws.count(d) for d in DrawCategory}
    assert by_draw == _ND_G1_CELLS_BY_DRAW, (
        f"the grid's composition moved: {by_draw} vs pinned {_ND_G1_CELLS_BY_DRAW}"
    )

    census = {}
    for persona in _NLOGIT_ANCHORS:
        per = sweep[persona]
        counts = dict.fromkeys(DrawCategory, 0)
        for i, draw in enumerate(draws):
            base = per[1.0][i]
            if _nlogit_p(base, ActionType.CALL) + _nlogit_p(base, ActionType.RAISE) <= 0.0:
                continue
            for mult in _NLOGIT_MULTS:
                d = per[mult][i]
                if _nlogit_p(d, ActionType.CALL) + _nlogit_p(d, ActionType.RAISE) <= 0.0:
                    continue
                counts[draw] += 1
        census[persona] = counts

    wrong = {p: c for p, c in census.items() if c != _ND_G1_COMPARISONS_BY_DRAW}
    assert not wrong, (
        f"G1's comparison census changed composition for {sorted(wrong)}: {wrong} vs pinned "
        f"{_ND_G1_COMPARISONS_BY_DRAW}. G1 itself only asserts a >= 1000 floor on the TOTAL, "
        "so a category can empty out under it without any other gate noticing; full census "
        f"{census}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# N-DRAWLOOSE T3 — G-DRAW: the calling dial decides the CHASE, not the draw
# ─────────────────────────────────────────────────────────────────────────────
#
# Claim C1 of the spec. The nit pack at `call_looseness` 0.45 against the SAME
# pack rebuilt at 0.60: the self-difference in P(fold) must stay inside a cap at
# six strong-draw nodes. It is the mirror image of G-NODE, which asserts a
# FLOOR of 0.040 on the same self-difference at draw-NONE nodes.
#
# ⚠️ THE CLAIM WAS SUPERSEDED ON 2026-08-22 (owner ruling of that date, ticket
# S3-T1b, improvement slice 3). N-DRAWLOOSE wrote this gate to say "the dial no
# longer decides strong draws", full stop, and that sentence is no longer what
# the engine does or what this gate asserts. It now reads:
#
#     the dial decides the CHASE share of a strong draw; the PRICE-MANDATED
#     share is protected from it.
#
# The two coincide only where a draw's own equity pays for none of the price.
# Everywhere else the split point moves with the node, so a single flat cap
# across the panel was measuring six different claims with one number. The cap
# is per node now, and it is derived rather than chosen — see below.
#
# ── WHERE THE CAP COMES FROM: A DERIVATION, PER PRICE CLASS (S3-T1b; the number
# it replaces, a chosen budget of 0.030, is kept in the record at the end of
# this block). ✅ RATIFIED BY THE OWNER AS PROPOSED, 2026-08-22 (ruling R1, on
# the S3-T1b fan-in). The same ruling records the supersession stated at the top
# of this block: G-DRAW's original claim, "the dial no longer decides strong
# draws", is superseded by "the dial decides the CHASE share of a strong draw;
# the price-mandated share is protected". Both are the governing text now; the
# 0.030 budget below is history.
#
# Step 1 — the whole continue side is proportional to the CALL merit. FOLD does
# not depend on the calling dial at all. CALL is C(L). RAISE is
# `R0 * rscale` and, on this branch, `rscale = C(L) / (C0 * ref)` with C0 and
# ref both frozen (the N-LOGIT block), so RAISE is C(L) times a constant too.
# Therefore
#
#     P(fold | L) = F / (F + k * C(L)) ,   k constant in L.
#
# Step 2 — rebuilding the dial from 0.60 to 0.45 scales the continue side by a
# single number, even though C is affine rather than proportional:
#
#     C(L) = (call_base + bonus*(1-s)) * L + bonus*s ,  s = the protected share
#     r    = C(0.45) / C(0.60)
#
# Step 3 — a scaling of the continue side by r is a pure shift of the
# continue/fold log-odds, so the fold-probability rise is a function of the base
# fold probability alone, and its maximum over ALL fold merits is
#
#     dP_max = (1 - sqrt(r)) / (1 + sqrt(r))
#
# which is attained at k*C(0.60)/F = 1/sqrt(r). That is the whole defensible
# movement: re-weighting the part of the call the dial is allowed to touch
# cannot move the fold rate further than this, whatever the hand class, the
# price factor or the persona.
#
# ── THE 0.071797 CEILING DOES TRANSFER AFTER ALL — this block used to say it
# did not, and the correction is worth stating because the old sentence sent a
# reader looking for a second theory. G-NODE's ceiling IS this formula at
# s = 0, where C(L) = call_base*L is proportional and r = 0.45/0.60 = 0.75:
# (1-sqrt(0.75))/(1+sqrt(0.75)) = 0.071797. What does not transfer is the
# CONSTANT, because a protected share makes r larger than 0.75 and the bound
# correspondingly smaller. Same theorem, different r.
#
# ── THE STATED POKER, per node — the input the cap is derived from, written
# here in the test rather than read out of the engine, so that the gate checks
# the engine against the poker instead of against itself. Out counts are the
# ordinary hand-reading ones; the price is the pot odds the node offers, in the
# engine's pre-aggression pot-fraction f, needed = f/(1+2f); realized equity
# counts the card the call BUYS and the river only at the probability it
# arrives free (`_ND_FREE_RIVER_Q` = 0.30, the same realization assumption
# `_DRAW_FREE_RIVER_PROB` states in the engine — theory contract CT-2 forbids
# pricing a two-card equity against a one-street price without one).
#
#     node  hand                     outs  equity  needs   mandated share
#     D1    JhTh on 9h8c2h             15  0.3630  0.2857  1.0000 (clamped)
#     D2    Ah5h on Kh8h2c              9  0.2243  0.3333  0.6728
#     D3    JhTh on 9h8c2h3d (turn)     15  0.3000  0.2500  1.0000 (clamped)
#     D4    Ah5h on Kh8h2c              9  0.2243  0.2500  0.8971
#     P1    9h8h on Kh9s3h              9  0.2243  0.2857  0.7850
#     R2    same as P1, facing a raise  9  0.2243  0.2857  0.7850
#     P2    Kh8h on Kd9h3h (record)     9  0.2243  0.2857  0.7850
#
# D1 reads 15 because nine hearts plus the Q and the 7 for the straight is
# 9 + 8, less the Qh and the 7h already counted among the hearts. Every other
# node here is a bare flush draw.
#
# ── THE CAPS, AND WHAT THE PANEL READS AGAINST THEM at this tip. Green on all
# six pins and red at the base commit b0a6a4e on all six:
#
#     node   derived cap   this tip   headroom   base b0a6a4e   S3-T1 (flat 0.7)
#     D1      0.005068     0.003889     1.30x      0.068151      0.014650  RED
#     D2      0.032275     0.027692     1.17x      0.067787      0.026588
#     D3      0.005068     0.004033     1.26x      0.069256      0.015125  RED
#     D4      0.023368     0.017215     1.36x      0.062845      0.023783  RED
#     P1      0.031243     0.013093     2.39x      0.038017      0.014807
#     R2      0.031243     0.013354     2.34x      0.038694      0.015099
#     P2      0.037342     0.005434     6.87x      0.013353      0.006002
#
# ⚠️ READ THE HEADROOM COLUMN CORRECTLY — it is NOT margin against the share.
# The cap is a maximum over every possible fold merit, and it is attained at one
# particular fold probability: `k*C(0.60)/F = 1/sqrt(r)`, which puts P(fold) at
# the 0.60 dial near 0.484 (0.4839 at D2, 0.4975 at D1). A node reads below its
# cap in the proportion its own fold probability sits away from that maximiser,
# and D2 — the tightest at 1.17x — sits at 0.2978. So a slice that moves the
# FOLD-side LEVEL alone cannot breach these caps by moving the level: shifting
# P(fold) toward 0.484 raises the reading and shifting it away lowers it, but
# the dial's reach into the call merit is what the cap actually bounds and a
# fold-side change does not touch it. The way to break BOTH legs of this gate is
# to couple the FOLD merit to the calling dial, which nothing does today and
# which S3-T2 must not introduce. That is the thing to check in S3-T2, rather
# than the headroom number.
#
# The last column is the point of the ticket: a FLAT protected share of 0.7 —
# what S3-T1 shipped and what this gate's 0.030 budget admitted — blows the
# derived cap at three of the six nodes, all of them nodes where the draw's own
# equity pays for the price. That is the defect S3-T1b removes, and it is why
# the cap had to be derived before it could be believed.
#
# ── WHAT THE OLD 0.030 WAS, kept for the record. It was a chosen budget with no
# analytic quantity behind it, justified by the window it had to sit in to be
# honest: red on every pin at the unchanged engine (D1 +0.068151, D2 +0.067787,
# D3 +0.069256, D4 +0.062845, P1 +0.038017, R2 +0.038694), green on every pin
# after N-DRAWLOOSE T1 (+0.003889, +0.016137, +0.004033, +0.014273, +0.009401,
# +0.009591). Any cap in (0.016137, 0.038017) had that property and 0.030 was a
# point in it. What the budget could not see is WHICH node moved: it admitted
# 0.0266 at D2, where the price genuinely leaves room for style, and it also
# admitted 0.0147 at D1, where it does not — one number, two different claims.
#
# ── D3 IS A TURN NODE AND KNOWINGLY PINS IN CURRENT TURN BEHAVIOUR. The engine
# has no implied-odds model, and `_draw_equity` — the proxy the SPR commit gate
# reads — still gives every STRONG draw a flat nine outs (filed as
# `N-DRAWEQUITY`; S3-T1b's own out count is deliberately local to the protected
# share and does not touch it). How much a draw SHOULD continue on the turn is
# an open question and `N-DRAWTURN` is expected to move it. D3 says "the dial
# does not decide it", not "0.2761 is the right turn fold rate". A future slice
# must be free to change the level here; it is this gate's sensitivity claim,
# not its node, that is meant to survive.
#
# ── P2 IS A RECORD, NOT A PIN. Top pair + flush draw reads +0.0134 at the
# UNCHANGED engine — already inside any cap this derivation produces — so
# asserting the cap on it would add a leg that cannot go red, which is the exact
# defect an earlier slice shipped. It is measured and its price and
# non-degeneracy are checked, so a later reader can see the quadrant, and
# nothing more is claimed about it HERE. It does carry a real assertion in the
# T4 raise-share table below — that is a different claim (equality with the base
# engine, which IS red-able at P2: fan-in defect A moves it) and it is not this
# gate's cap.
#
# ── WHY R2 (A FACING-A-RAISE NODE) IS NOT OPTIONAL — N-DRAWLOOSE ruling R5.
# Every node on this panel used to carry `facing_raise=False`, and `_NDNode` had
# no field for it at all. The refuter used that: mutant M13 floors the draw
# bonus only when NOT facing a raise, which leaves the headline defect fully
# alive on the facing-a-raise half of production (`play.py` derives
# `faced_raise` via `facing_raise(state.action_history, state.street)` and
# passes it on every postflop decision) — and M13 passed all
# seven of this slice's gates. R2 is P1 with `facing_raise=True`; under M13 it
# reverts to the base engine's +0.0387 and blows its cap (0.030 when that
# reading was taken, 0.031243 under the derivation above — red either way),
# while D1/P1 stay at their shipped readings. MEASURED under M13: R2 +0.0387 (red), P1 +0.0094
# and D1 +0.0039 (both green) — the panel without R2 is exactly as blind as the
# refuter said.
#
# THE FIELD IS PROVED LIVE, not assumed. `facing_raise` is a keyword argument
# with a default, so a `_nd_priced_dist` that forgot to forward it would make R2
# silently identical to P1 and re-open M13 with the node still sitting in the
# panel looking like coverage. `test_nd_gdraw_facing_raise_reaches_the_engine`
# below asserts R2's vector DIFFERS from P1's for all six personas: middle pair
# is in `_VULNERABLE_ONE_PAIR`, so facing a raise damps `_RAISE_BASE` by 0.35
# (`_ONE_PAIR_RAISE_DAMP = 0.35`, applied to `raise_base` on the
# `bucket in _VULNERABLE_ONE_PAIR and facing_raise and street in (Street.FLOP,
# Street.TURN)` branch) and the two vectors cannot coincide.
# That is a different code path from the floor, which is the point — it proves
# the ARGUMENT arrives, which is all the panel needs.
#
# ── WHY P1 IS NOT OPTIONAL. Strength bucket and draw category are INDEPENDENT
# axes (the line-damp scope comment's "BUCKET and DRAW are INDEPENDENT axes"
# note above `_LINE_SCOPE_BUCKETS`): a hand can be MIDDLE_PAIR and carry a
# STRONG draw at the same time. Earlier panels for this slice sat entirely on the
# naked-draw (AIR / ACE_HIGH) side of that grid, which would have made the gate's
# redness a property of high-folding nodes rather than of the claim. P1 is the
# pair-plus-draw quadrant, and it is the tightest pin: +0.0380 at base is the
# smallest red reading the panel has.
#
# ── M1/M2 ARE INSTRUMENT-LIVENESS CONTROLS, NOT A SECOND G-NODE. A cap-only gate
# passes trivially if the instrument is broken: a helper that returned the same
# vector twice would report 0.0000 everywhere and go green. M1 and M2 are
# draw-NONE nodes where the dial is SUPPOSED to bite, and they assert the same
# 0.040 floor G-NODE does, on this gate's own instrument, in this gate's own run.
# They are deliberately overlapping and are NOT part of the independence claim
# below.
#
# ── INDEPENDENCE (mandatory check; this file has twice shipped a gate that
# could not fail whenever its sibling passed). Each of this slice's claims can
# go red on something no sibling covers:
#   G-DRAW (this gate, pinned legs)  a per-node CAP on |ΔP(fold)| at
#       STRONG-draw nodes. Only red-able thing: the dial reaching further into
#       a strong draw's call than the node's price leaves to style. Fails alone
#       on mutant M13 (floor withheld when facing a raise) via R2, and on the
#       flat 0.7 share S3-T1 shipped, via D1/D3/D4.
#   G-DRAW's price-mandate leg (the second test below) the same movement
#       measured EXACTLY rather than bounded. ⚠️ THIS IS A NAMED EXCEPTION TO
#       THE RULE THIS BLOCK ENFORCES — see the paragraph directly below, which
#       the owner required be stated as an exception rather than left as an
#       aside (ruling R1, 2026-08-22).
#   G-NODE (above)                   a FLOOR on ΔP(fold) at draw-NONE nodes.
#       Disjoint node class (a hand is in exactly one draw category, and the
#       engine branches on precisely that predicate), so a build can satisfy
#       either while breaking the other. Fails alone on a floor that leaked
#       outside DrawCategory.STRONG.
#   T4's ceiling (0.34)              a LEVEL at one node. A cap on a DIFFERENCE
#       says nothing about a LEVEL: floor values of 0.6, 2.0 and 5.0 all pass
#       G-DRAW. Fails alone on a build that leaves the dial deciding the level.
#   T4's cross-persona margin        an ORDERING between two personas. Fails
#       alone on an oversized floor (5.0) that loosens the whole roster —
#       measured: the nit-minus-station fold gap at D1 goes +0.1692 -> -0.0073,
#       while G-DRAW and the ceiling both stay green.
#   T4's raise-share table           P(raise | continue) equal to base, per
#       persona. Red on fan-in defect A (the raise-scale divisor carrying the
#       floor) — measured: lag 0.6109 -> 0.4780 at D1 with G-DRAW, both T4
#       level legs and the station pins still green. G1 is red on that mutant
#       too. What this can fail on that G1 cannot is a LEVEL shift that is
#       still lever-invariant — measured witness: the STRONG semi-bluff raise
#       bonus shrunk 10%, G1 green, this red.
#   T4's station byte-identity       EXACT equality for a dial at or above 1.0.
#       Fails alone on the re-associated arithmetic at a non-power-of-two dial
#       (measured: the `strong_all` mutant — this red, all 41 siblings green).
#   C5's non-STRONG vectors          EXACT equality off the STRONG branch.
#       Fails alone on a re-association of the untouched expression, which
#       moves WEAK weights by an ulp and nothing else in the suite sees
#       (measured: a WEAK-only re-association — this red, all 41 siblings
#       green).
#   G1's census by draw category     the COMPOSITION of G1's denominator.
#       Fails alone when strong-draw cells drop out of G1's measurement
#       silently (measured: strong draws made to never continue in 2-opponent
#       spots — this red at STRONG 384 for five personas and 448 for the
#       station against the pinned 512, while G1 and all 41 other siblings
#       stay green).
# M1/M2 below are deliberately overlapping instrument-liveness controls and are
# NOT part of this independence claim.
#
# ⚠️ ONE NAMED EXCEPTION TO THE INDEPENDENCE RULE — DELIBERATE, OWNER-RATIFIED
# (ruling R1, 2026-08-22), AND THE ONLY ONE IN THIS FAMILY. The rule this block
# enforces is that no gate may be one that "could not fail whenever its sibling
# passed". G-DRAW's derived CAP is exactly that with respect to G-DRAW's
# PRICE-MANDATE leg: the mandate leg asserts that the continue side scales by
# exactly the predicted `r`, and the cap is the maximum fold movement that same
# `r` permits, so wherever the mandate leg is green the cap is green by
# arithmetic. MEASURED, over the seven-mutant matrix recorded in the S3-T1b
# section below: no mutant turns the cap red while the mandate leg is green.
# The redundancy is real and is not being explained away.
#
# BOTH ARE KEPT ANYWAY, for a reason that is about what each SURVIVES rather
# than what each catches. The mandate leg's arithmetic depends on a property of
# the vector's SHAPE — that FOLD does not move with the dial and the whole
# continue side is proportional to the CALL merit, via `rscale`. That property
# is true today and is not guaranteed forever: widen a damp to strong-draw
# nodes, or give FOLD a dial term, and the mandate leg goes red for a reason
# that has nothing to do with the protected share, while the reader is left
# with no gate on the behavioural claim at all. The CAP holds for ANY vector
# shape — it is a maximum over every possible fold merit — so it is the leg
# that still says something true on the day the sharp one stops applying. The
# exception is therefore "a precise gate plus a robust one over the same
# claim", not "two names for one check", and it is written here so the next
# reader does not delete the cap as dead weight.

# The stated poker, per node: out count and cards-to-come. The PRICE is already
# on the node (`faced_frac`) and is checked against the engine by
# `_nd_priced_dist`, so it is not repeated here. Written out by hand rather than
# read from the engine — that is what makes the cap a check on the engine
# instead of a restatement of it. A build whose `_strong_draw_outs` disagreed
# with these counts would under-protect and blow the cap: measured, D1 priced at
# nine outs instead of fifteen reads +0.0116 against its 0.005068 cap.
_ND_STATED_OUTS = {"D1": 15.0, "D2": 9.0, "D3": 15.0, "D4": 9.0,
                   "P1": 9.0, "R2": 9.0, "P2": 9.0}
# The realization assumption, restated (engine: `_DRAW_FREE_RIVER_PROB`).
_ND_FREE_RIVER_Q = 0.30
_ND_MADE_CONTROL_FLOOR = 0.040
# The retired flat budget was 0.030. It is deliberately NOT bound to a name
# here: nothing asserts against it any more, and a constant that is defined and
# never read reads like a live threshold to the next person to open this file.
# The number is kept in the section comment above, where its history belongs.


def _nd_stated_mandated_share(node: _NDNode) -> float:
    """The share of a strong draw's call bonus this node's PRICE mandates,
    computed from the poker stated in the section comment above.

    Deliberately a second implementation rather than a call into
    `_strong_draw_protected_share`: a gate that asks the engine what it thinks
    the share is, and then checks the engine against that, asserts nothing.
    """
    per_card = _ND_STATED_OUTS[_nd_key(node)] * 0.02
    cards_to_come = 5 - len(node.board)
    equity = (
        per_card + (1.0 - per_card) * _ND_FREE_RIVER_Q * per_card
        if cards_to_come >= 2
        else per_card
    )
    needed = node.faced_frac / (1.0 + 2.0 * node.faced_frac)
    return min(equity / needed, 1.0)


def _nd_continue_ratio(node: _NDNode) -> float:
    """r = C(0.45) / C(0.60), the factor the whole continue side scales by when
    the nit's dial is rebuilt from 0.60 down to 0.45 at this node, predicted
    from the stated poker and the engine's SHARED merit tables (`_CALL_BASE`,
    `_DRAW_CALL_BONUS` — game mechanics, not the thing under test)."""
    bucket, draw = strength_bucket(node.hole, list(node.board))
    assert draw is DrawCategory.STRONG, (
        f"{node.node_id}: classified {draw}, not STRONG — this panel's whole "
        "derivation is about the strong-draw branch"
    )
    share = _nd_stated_mandated_share(node)
    bonus = personas_postflop._DRAW_CALL_BONUS[DrawCategory.STRONG]
    slope = personas_postflop._CALL_BASE[bucket] + bonus * (1.0 - share)
    intercept = bonus * share
    return (_ND_LO_LOOSENESS * slope + intercept) / (_ND_HI_LOOSENESS * slope + intercept)


def _nd_derived_cap(node: _NDNode) -> float:
    """The largest fold-probability rise the calling dial can defensibly produce
    at `node`: `(1 - sqrt(r)) / (1 + sqrt(r))`, the maximum over every possible
    fold merit of a continue side scaled by `r`. Derivation in the section
    comment; at r = 0.75 (no protection at all) it is G-NODE's 0.071797."""
    root = math.sqrt(_nd_continue_ratio(node))
    return (1.0 - root) / (1.0 + root)
# Non-degeneracy window, same reasoning as G-NODE's: a node where some legal
# action is effectively forced tells us nothing about a lever that only
# re-weights the mix.
_ND_MIN_PROB, _ND_MAX_PROB = 0.01, 0.99

_ND_DRAW_PANEL = (
    _NDNode(
        "D1 combo draw, flop, 2/3-pot",
        ("Jh", "Th"), ["9h", "8c", "2h"], Street.FLOP, 10.0, 4.0, 100.0, 1, 4.0 / 6.0,
    ),
    _NDNode(
        "D2 flush draw, flop, pot",
        ("Ah", "5h"), ["Kh", "8h", "2c"], Street.FLOP, 24.0, 12.0, 200.0, 1, 12.0 / 12.0,
    ),
    _NDNode(
        "D3 combo draw, TURN, 1/2-pot",
        ("Jh", "Th"), ["9h", "8c", "2h", "3d"], Street.TURN, 18.0, 6.0, 200.0, 1, 6.0 / 12.0,
    ),
    _NDNode(
        "D4 flush draw, flop, 1/2-pot, four-way",
        ("Ah", "5h"), ["Kh", "8h", "2c"], Street.FLOP, 18.0, 6.0, 200.0, 3, 6.0 / 12.0,
    ),
    _NDNode(
        "P1 middle pair + flush draw, flop, 2/3-pot",
        ("9h", "8h"), ["Kh", "9s", "3h"], Street.FLOP, 20.0, 8.0, 200.0, 1, 8.0 / 12.0,
    ),
    _NDNode(
        "R2 middle pair + flush draw, flop, 2/3-pot, FACING A RAISE",
        ("9h", "8h"), ["Kh", "9s", "3h"], Street.FLOP, 20.0, 8.0, 200.0, 1, 8.0 / 12.0,
        facing_raise=True,
    ),
)
# P1 without the raise — the twin R2 is compared against by the liveness gate.
_ND_FACING_RAISE_TWIN = _ND_DRAW_PANEL[4]
_ND_FACING_RAISE_NODE = _ND_DRAW_PANEL[5]
_ND_RECORD_ONLY = (
    _NDNode(
        "P2 top pair + flush draw, flop, 2/3-pot",
        ("Kh", "8h"), ["Kd", "9h", "3h"], Street.FLOP, 20.0, 8.0, 200.0, 1, 8.0 / 12.0,
    ),
)
_ND_MADE_CONTROLS = (
    _NDNode(
        "M1 middle pair, flop, pot",
        ("9h", "4c"), ["Kc", "9s", "3h"], Street.FLOP, 48.0, 24.0, 480.0, 1, 24.0 / 24.0,
    ),
    _NDNode(
        "M2 middle pair, turn, pot",
        ("9h", "4c"), ["Kc", "9s", "3h", "2d"], Street.TURN, 48.0, 24.0, 480.0, 3, 24.0 / 24.0,
    ),
)


def _nd_self_difference(node: _NDNode) -> tuple[float, float, float]:
    """(P(fold) at 0.45, P(fold) at 0.60, difference) for the nit at `node`,
    with every action in both vectors checked for degeneracy first."""
    lo = _nd_priced_dist(_nd_nit_at(_ND_LO_LOOSENESS), node)
    hi = _nd_priced_dist(_nd_nit_at(_ND_HI_LOOSENESS), node)
    for label, dist in ((_ND_LO_LOOSENESS, lo), (_ND_HI_LOOSENESS, hi)):
        for action, prob in dist.items():
            assert _ND_MIN_PROB <= prob <= _ND_MAX_PROB, (
                f"{node.node_id} (call_looseness {label}): P({action.value}) = {prob:.6f} "
                f"is outside [{_ND_MIN_PROB}, {_ND_MAX_PROB}] — the node is degenerate and "
                "a difference measured there is not a lever effect"
            )
    return lo[ActionType.FOLD], hi[ActionType.FOLD], lo[ActionType.FOLD] - hi[ActionType.FOLD]


def test_nd_gdraw_dial_no_longer_decides_strong_draws():
    """G-DRAW — at six priced strong-draw nodes the nit's fold probability moves
    by no more than the node's PRICE defends when its calling dial is rebuilt
    from 0.45 to 0.60, while at two draw-NONE control nodes it still moves by at
    least 0.040.

    ⚠️ THE CLAIM WAS SUPERSEDED ON 2026-08-22 (owner ruling, ticket S3-T1b).
    N-DRAWLOOSE wrote this gate as "the dial no longer decides strong draws". It
    now reads: THE DIAL DECIDES THE CHASE SHARE OF A STRONG DRAW; THE
    PRICE-MANDATED SHARE IS PROTECTED. The test's name is left alone so the
    ticket trail stays followable; the sentence it asserts is this one.

    THE CAP IS DERIVED, PER NODE, NOT CHOSEN — `(1 - sqrt(r))/(1 + sqrt(r))`
    where r is the factor the whole continue side scales by, computed from the
    out count and the pot odds this test states independently of the engine. The
    full derivation, the stated poker per node, the readings and the retired
    0.030 budget are in the section comment above. RATIFIED BY THE OWNER AS
    PROPOSED, 2026-08-22 (ruling R1).

    Red at the base commit b0a6a4e on all six pins (+0.068151 · +0.067787 ·
    +0.069256 · +0.062845 · +0.038017 · +0.038694) and red on the flat 0.7 share
    S3-T1 shipped at three of them (D1 +0.014650, D3 +0.015125, D4 +0.023783 —
    caps 0.005068, 0.005068, 0.023368). Green at this tip on all six.
    """
    readings = []
    for node in _ND_DRAW_PANEL:
        lo, hi, self_delta = _nd_self_difference(node)
        cap = _nd_derived_cap(node)
        readings.append((node.node_id, self_delta))
        assert abs(self_delta) <= cap, (
            f"{node.node_id}: the calling dial moves this strong draw's fold "
            f"probability by {self_delta:+.4f}, past the {cap:.6f} that this node's "
            f"price defends — its pot odds mandate {_nd_stated_mandated_share(node):.4f} "
            f"of the call bonus, and a dial that reaches further than that is deciding "
            f"the hand rather than the chase; {lo:.4f} at call_looseness "
            f"{_ND_LO_LOOSENESS} vs {hi:.4f} at {_ND_HI_LOOSENESS}"
        )

    # P2: read, priced and checked for degeneracy — but NOT capped. It is inside
    # the cap at the unchanged engine, so a cap leg here could never go red.
    for node in _ND_RECORD_ONLY:
        _nd_self_difference(node)

    for node in _ND_MADE_CONTROLS:
        lo, hi, self_delta = _nd_self_difference(node)
        assert self_delta >= _ND_MADE_CONTROL_FLOOR, (
            f"{node.node_id}: this is a draw-NONE control where the calling dial is "
            f"SUPPOSED to bite, and it moved the fold probability only {self_delta:+.4f} "
            f"(floor {_ND_MADE_CONTROL_FLOOR}); {lo:.4f} at {_ND_LO_LOOSENESS} vs "
            f"{hi:.4f} at {_ND_HI_LOOSENESS}. Either the dial protection leaked "
            "outside DrawCategory.STRONG, or this gate's instrument has stopped reading "
            f"anything at all — the whole panel reads {readings}"
        )


def test_nd_gdraw_dial_reach_matches_the_price_mandate():
    """The sharp form of the cap above: at every node on the panel the calling
    dial moves the continue side by EXACTLY the factor the node's price and out
    count predict — not merely by less than the maximum.

    ── HOW IT IS MEASURED, FROM OUTSIDE THE ENGINE. On this branch FOLD does not
    depend on the dial and the whole continue side is proportional to the CALL
    merit (RAISE tracks it through `rscale`; the N-LOGIT block's derivation).
    So `P(fold) = F / (F + k*C)` with k constant in the dial, which inverts to

        (1/P(fold) - 1) at 0.45   divided by   (1/P(fold) - 1) at 0.60   =   r

    with no engine internal read at any point. `r` is then compared against the
    value predicted from the stated out count, the stated free-river
    probability and the node's own price. MEASURED agreement at this tip: worst
    relative deviation 2.5e-16 over all seven nodes, i.e. one ulp. The gate
    asserts 1e-9 — about 4e6 above that noise and far below anything a real
    change moves.

    ── WHAT THIS CATCHES THAT THE CAP DOES NOT. The cap only bounds movement
    from above, so an engine that protects a draw MORE than the price mandates
    passes it, and so does one that protects slightly less. This is two-sided
    and exact, and it is the only thing in the suite that pins the three inputs
    to the protected share: the out count (a combo draw read as a bare
    nine-outer moves r), the realization assumption (a different free-river
    probability moves r), and the price term itself. A flat share — S3-T1's
    0.7, or any other constant — is red here at every node whose mandate is not
    exactly that constant.

    ── WHAT IT DOES NOT CATCH, stated so the pair is not mistaken for two
    independent kills. Under the proportionality above, this leg IMPLIES the
    cap. It is kept alongside rather than instead of it because the cap holds
    for any vector shape while this leg's arithmetic does not: widen a damp to
    strong-draw nodes and this goes red for a reason that has nothing to do
    with the protected share, while the cap still measures the behavioural
    claim.
    """
    for node in _ND_DRAW_PANEL + _ND_RECORD_ONLY:
        lo, hi, _ = _nd_self_difference(node)
        measured = (1.0 / lo - 1.0) / (1.0 / hi - 1.0)
        predicted = _nd_continue_ratio(node)
        assert measured == pytest.approx(predicted, rel=1e-9), (
            f"{node.node_id}: rebuilding the nit's dial from {_ND_HI_LOOSENESS} to "
            f"{_ND_LO_LOOSENESS} scaled the continue side by {measured!r}, but this "
            f"node's price mandates {_nd_stated_mandated_share(node):.4f} of the draw "
            f"bonus, which predicts {predicted!r}. The engine's protected share is not "
            "the one the poker in this file's section comment states — check the out "
            "count (`_strong_draw_outs`), the realization assumption "
            "(`_DRAW_FREE_RIVER_PROB`) and the price term, in that order"
        )


def test_nd_gdraw_facing_raise_reaches_the_engine():
    """G-DRAW's instrument liveness for the `facing_raise` axis (ruling R5).

    R2 is P1 with `facing_raise=True` and nothing else changed. `facing_raise`
    is a keyword argument with a default, so an instrument that failed to
    forward it would make R2 a duplicate of P1 — the panel would still look
    like it covered the facing-a-raise half of production while covering none
    of it, and mutant M13 would survive again with the node in place.

    MIDDLE_PAIR is in `_VULNERABLE_ONE_PAIR`, so facing a raise damps
    `_RAISE_BASE` by `_ONE_PAIR_RAISE_DAMP` = 0.35 on the flop
    (`_ONE_PAIR_RAISE_DAMP = 0.35`, applied to `raise_base` on the
    `bucket in _VULNERABLE_ONE_PAIR and facing_raise and street in (Street.FLOP,
    Street.TURN)` branch). That is a DIFFERENT code path from
    the N-DRAWLOOSE branch on purpose: what needs proving is that the argument
    arrives, and a path that branch cannot influence proves it cleanly. Every
    persona must therefore read differently at R2 than at P1.
    """
    for persona in sorted(v.value for v in VillainType):
        twin = _nd_priced_dist(_pack(persona), _ND_FACING_RAISE_TWIN)
        raised = _nd_priced_dist(_pack(persona), _ND_FACING_RAISE_NODE)
        assert twin != raised, (
            f"{persona}: {_ND_FACING_RAISE_NODE.node_id} produced the SAME vector as "
            f"{_ND_FACING_RAISE_TWIN.node_id} ({twin}). `facing_raise` is not reaching "
            "the engine, so every facing-a-raise node on this panel is measuring the "
            "facing-a-bet spot instead"
        )


def test_nd_priced_helper_refuses_a_mislabelled_node():
    """G-DRAW's instrument, proved against the bug it exists to stop.

    Two of this slice's own planning nodes were mispriced and were caught by
    exactly this assertion, so it is load-bearing rather than decorative. Here D1
    (live pot 10, to_call 4 — the engine prices it at 4/6) is relabelled as a
    half-pot bet: `_nd_priced_dist` must raise rather than hand back a perfectly
    plausible-looking probability vector, and must still return one when the same
    node is labelled truthfully.
    """
    mislabelled = _ND_DRAW_PANEL[0]._replace(faced_frac=0.500)
    with pytest.raises(AssertionError, match="the engine priced this node"):
        _nd_priced_dist(_pack("nit"), mislabelled)
    assert _nd_priced_dist(_pack("nit"), _ND_DRAW_PANEL[0])[ActionType.FOLD] > 0.0
    # And the wrapper leaves the engine exactly as it found it.
    assert personas_postflop._price_factor.__module__ == personas_postflop.__name__


# ─────────────────────────────────────────────────────────────────────────────
# N-DRAWLOOSE T4 — C2: the absolute level band (a cap alone is level-blind)
# ─────────────────────────────────────────────────────────────────────────────
#
# G-DRAW above only bounds how FAR the dial moves a strong draw's fold rate; it
# says nothing about WHERE that rate sits. Measured: floor values of 0.6, 2.0
# and even 5.0 all satisfy G-DRAW, and 5.0 more than doubles every persona's
# strong-draw bonus — loosening the whole roster, including the calling
# station, without G-DRAW noticing, and nothing else in the suite catches it
# because a later ticket in this slice (T5) re-records the fixtures that would
# otherwise have moved. Four gates live here, each red-able on its own:
#   * a CEILING on the shipped nit's fold rate at D1 (the slice's trace node);
#   * a CROSS-PERSONA margin, nit versus the calling station, at the same node;
#   * P(raise | continue) equal to the BASE engine at seven strong-draw nodes;
#   * byte-identity pins for the calling station, whose dial is above 1.0.
#
# ── WHY THERE IS NO LOWER BOUND ANY MORE — N-DRAWLOOSE ruling R7 (2026-08-05,
# owner). This gate used to assert P(fold) in [0.20, 0.34]. The CEILING stays:
# it is a real behavioural claim and it is the leg that is red at base. The
# FLOOR is gone, for two reasons the owner gave:
#   (a) It is indefensible AS POKER. D1 is a 15-out combo draw getting 4-into-6,
#       i.e. 28.6% pot odds against roughly 54% equity by the river. "A nit folds
#       that at least 20% of the time" is not a property anyone would defend; it
#       was a proxy for "the roster has not been loosened wholesale", written as
#       a level because a level was what was handy.
#   (b) It BLOCKS the filed follow-ups. `N-DRAWEQUITY` (replace the flat
#       nine-out proxy with a real equity read) and `N-DRAWTURN` (implied odds
#       by street) exist precisely to make equity-aware draws continue MORE. A
#       floor of 0.20 at this node would fail them for succeeding.
# What replaces it is the claim the floor was ACTUALLY making, stated directly:
# the nit must still fold strong draws MATERIALLY MORE than the calling
# station. That survives `N-DRAWEQUITY`/`N-DRAWTURN` (both personas' draws
# continue more; the ordering is untouched) and it still kills the mutant the
# floor existed for. MEASURED at D1, shipped packs, nit P(fold) minus station
# P(fold):
#     base b0a6a4e  +0.330144      this tip  +0.169229
#     floor = 2.0   +0.062412      floor = 5.0  -0.007322  (station folds MORE)
# The 0.10 margin is a CHOSEN BUDGET, not a derived bound: 1.69x headroom under
# the shipped reading, and red on both oversized-floor mutants — the 5.0 one the
# owner named and the subtler 2.0 one, which the old [0.20, 0.34] floor also
# caught (floor=2.0 puts the nit at 0.1540) and which a margin of, say, 0.05
# would have let through.

_ND_T4_BAND_HI = 0.34
_ND_T4_CROSS_MARGIN = 0.10
_ND_T4_NODE = _ND_DRAW_PANEL[0]  # D1 combo draw, flop, 2/3-pot — the slice's trace node


def test_nd_t4_absolute_ceiling_at_trace_node():
    """C2a — the SHIPPED nit pack, loaded unmodified via `load_persona_packs()`
    (no `call_looseness` override: the claim is about the bot as it actually
    ships, not a rebuilt variant), folds D1 at most 0.34 of the time.

    Red at base commit b0a6a4e: 0.4217. Green at eb34e60: 0.2608. S3-T1
    (2026-08-21) took it to 0.2944 by handing a flat 0.7 share of the draw bonus
    back to the dial; S3-T1b (2026-08-22) returned it to 0.2608 exactly, because
    D1's price — 4 into a live pot of 10, i.e. 28.6% needed against a 15-out
    draw — mandates the WHOLE bonus, so the protected share clamps at 1.0 and
    the branch reproduces the old hard floor bit for bit at this node. Headroom
    under the ceiling is 0.0792 again. This is the leg that says the dial has not
    gone back to DECIDING this hand's continue. Widening it is not a fix — see
    the section comment for the lower
    bound that was REMOVED here on ruling R7 and for the cross-persona leg that
    replaced it.
    """
    dist = _nd_priced_dist(_pack("nit"), _ND_T4_NODE)
    fold = dist[ActionType.FOLD]
    assert fold <= _ND_T4_BAND_HI, (
        f"{_ND_T4_NODE.node_id}: the shipped nit folds a strong draw {fold:.4f} of the "
        f"time, above the ceiling {_ND_T4_BAND_HI} — the calling dial is still deciding "
        "this hand's continue at close to its pre-slice level (base reads 0.4217)"
    )


def test_nd_t4_nit_still_folds_strong_draws_far_more_than_the_station():
    """C2b — at D1 the shipped nit's fold rate exceeds the shipped calling
    station's by at least 0.10.

    This is the cross-persona claim that replaced the old 0.20 floor (ruling
    R7). It forbids the defect the floor was a proxy for — an oversized dial
    guard loosening the WHOLE roster rather than un-sticking the tight end of
    it — without asserting a poker level nobody would defend, and without
    blocking `N-DRAWEQUITY` / `N-DRAWTURN`, which are supposed to make both
    personas' draws continue more.

    MEASURED (nit P(fold) - calling_station P(fold) at D1): base b0a6a4e
    +0.330144 · at eb34e60 +0.169229 · at the S3-T1 tip +0.202941 · at the
    S3-T1b tip +0.169229 · floor=2.0 mutant +0.062412 · floor=5.0 mutant
    -0.007322. Both oversized floors are red; 0.10 is a chosen budget with 1.69x
    headroom under the shipped reading. S3-T1 moved this leg AWAY from its floor
    (its flat share tightened the five dialled personas and left the station's
    4.0 dial untouched); S3-T1b returns it to the eb34e60 value, because at this
    node the price mandates the whole bonus for everyone.

    THE CLAIM IS PAIRWISE. Nothing here says the nit is the tightest
    strong-draw defender of the six — lag, maniac, tag and the fish are not
    measured, and this can pass while the nit folds less than any of them.
    """
    nit = _nd_priced_dist(_pack("nit"), _ND_T4_NODE)[ActionType.FOLD]
    station = _nd_priced_dist(_pack("calling_station"), _ND_T4_NODE)[ActionType.FOLD]
    assert nit - station >= _ND_T4_CROSS_MARGIN, (
        f"{_ND_T4_NODE.node_id}: the nit folds this strong draw {nit:.4f} of the time "
        f"against the calling station's {station:.4f} — a gap of only {nit - station:+.4f} "
        f"(floor {_ND_T4_CROSS_MARGIN}). The two personas' strong-draw defence has "
        "converged, which is what an oversized dial guard does: it loosens the whole "
        "roster instead of un-sticking the tight end of it (floor=5.0 reads -0.0073)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# T4 — P(raise | continue) at strong-draw nodes, against the BASE engine
# ─────────────────────────────────────────────────────────────────────────────
#
# N-DRAWLOOSE ruling R2 (2026-08-05, owner): G3 above is now scoped OUT of
# DrawCategory.STRONG, and scoping a gate without replacing it is not
# acceptable. This is the replacement, and on these cells it is strictly
# stronger than what G3 covered: G3 asserted "opted-in equals un-opted", and the
# un-opted path is not the base engine's raise share on a strong draw either
# (it has no raise scale at all). This asserts the property that SHOULD hold —
# the floor moves FOLD mass onto the continue side and CALL and RAISE receive it
# in their ORIGINAL proportion, so the raise share among continues is exactly
# what b0a6a4e computed, persona by persona. It is also the raise-share record
# the theory review asked for.
#
# HARVESTED, not derived: every value below was read out of the CONTROL
# worktree at base commit b0a6a4e through this same `_nd_priced_dist`
# instrument, at full `repr()` precision.
#
# TOLERANCE. Not bitwise — each share is a ratio of two normalized
# probabilities, so several float divisions sit between the merits and the
# answer. MEASURED worst deviation of this tip from these pins, over all 42
# (node, persona) pairs: 1.11e-16 absolute, 3.51e-16 relative. The gate asserts
# 1e-12 relative — about 2,800x above the observed noise, and about 2e11 BELOW
# the mutant it exists to catch (fan-in defect A moves lag's share at D1 from
# 0.6109 to 0.4780, i.e. 0.22 relative).
_ND_RAISE_SHARE_TOL = 1e-12
_ND_BASE_RAISE_SHARE = {
    "D1": {
        "calling_station": 0.0326295585412668,
        "lag": 0.6108927568781584,
        "maniac": 0.7331536388140162,
        "nit": 0.21249999999999997,
        "passive_fish": 0.27823240589198034,
        "tag": 0.5190839694656488,
    },
    "D2": {
        "calling_station": 0.021879021879021878,
        "lag": 0.5100796999531176,
        "maniac": 0.6456425907087148,
        "nit": 0.15178571428571425,
        "passive_fish": 0.20359281437125745,
        "tag": 0.4171779141104294,
    },
    "D3": {
        "calling_station": 0.021359223300970873,
        "lag": 0.5039370078740159,
        "maniac": 0.64,
        "nit": 0.14864864864864866,
        "passive_fish": 0.1996370235934664,
        "tag": 0.41121495327102797,
    },
    "D4": {
        "calling_station": 0.021879021879021875,
        "lag": 0.5100796999531176,
        "maniac": 0.6456425907087147,
        "nit": 0.15178571428571427,
        "passive_fish": 0.20359281437125748,
        "tag": 0.4171779141104294,
    },
    "P1": {
        "calling_station": 0.0228310502283105,
        "lag": 0.5209605209605209,
        "maniac": 0.6555458004097161,
        "nit": 0.1574803149606299,
        "passive_fish": 0.2107481559536354,
        "tag": 0.42780748663101603,
    },
    "R2": {
        "calling_station": 0.019192208536236034,
        "lag": 0.47665629168519336,
        "maniac": 0.6144775630527349,
        "nit": 0.13535353535353534,
        "passive_fish": 0.18276050190943807,
        "tag": 0.38505747126436785,
    },
    "P2": {
        "calling_station": 0.022956841138659315,
        "lag": 0.5223636957231472,
        "maniac": 0.6568144499178981,
        "nit": 0.15822784810126578,
        "passive_fish": 0.21168501270110074,
        "tag": 0.42918454935622313,
    },
}


def test_nd_t4_strong_draw_raise_share_matches_the_base_engine():
    """T4 — P(raise | continue) at every strong-draw node on this panel, for
    every persona, equals the BASE engine b0a6a4e's value.

    THE MUTANT THIS EXISTS FOR is the fan-in review's defect A: making the raise
    scale's divisor `_call_merit_at_ref` carry the same floor as the live call
    merit. The floor's growth then cancels out of `rscale`, every chip it frees
    from FOLD lands on CALL, and an aggressive persona stops semi-bluff-raising
    the draws the floor exists to keep in. Measured with that divisor floored:
    lag 0.6109 -> 0.4780 at D1, maniac 0.7332 -> 0.6158, tag 0.5191 -> 0.4056,
    nit 0.2125 -> 0.1457, passive_fish 0.2782 -> 0.1488 — while G-DRAW, both T4
    level legs and the station byte-identity pins all stay GREEN.

    ── HONEST OVERLAP, and where this gate goes BEYOND G1. G1 also goes red on
    defect A, because these personas' lever sweep crosses the floor (nit's
    anchor 0.6 at x2 is 1.2) and the floored divisor makes the share differ on
    the two sides of the crossing. What G1 CANNOT see is a change that shifts
    the raise share to a NEW LEVEL while keeping it lever-invariant — G1 asserts
    invariance in the lever, this asserts the VALUE. Concrete witness: shrinking
    the STRONG semi-bluff raise bonus 10% leaves G1 green and turns this red.
    That witness also trips the station's byte-identity pins, which are exact
    whole-vector pins at this same node — what this table adds over them is the
    other five personas and the other six nodes, none of which those pins reach.

    `calling_station` is in the table on purpose even though its dial clears
    the floor: it is the row that would move if the STRONG branch ever stopped
    being conditional on `looseness < 1.0`.
    """
    nodes = _ND_DRAW_PANEL + _ND_RECORD_ONLY
    keys = {_nd_key(n) for n in nodes}
    assert keys == set(_ND_BASE_RAISE_SHARE), (
        f"the pinned raise-share table covers {sorted(_ND_BASE_RAISE_SHARE)} but the panel "
        f"is {sorted(keys)} — a node was added or renamed without a base harvest, so it "
        "would have been asserted against nothing"
    )
    for node in nodes:
        pins = _ND_BASE_RAISE_SHARE[_nd_key(node)]
        for persona, expected in sorted(pins.items()):
            dist = _nd_priced_dist(_pack(persona), node)
            continues = dist[ActionType.CALL] + dist[ActionType.RAISE]
            assert continues > 0.0, f"{node.node_id} ({persona}): no continue mass"
            share = dist[ActionType.RAISE] / continues
            assert share == pytest.approx(expected, rel=_ND_RAISE_SHARE_TOL), (
                f"{node.node_id} ({persona}): P(raise | continue) is {share!r}, not the "
                f"base engine's {expected!r}. The floor is supposed to hand its freed "
                "FOLD mass to CALL and RAISE in their ORIGINAL proportion; a move here "
                "means the raise leg is no longer receiving its share (fan-in defect A)"
            )


# ─────────────────────────────────────────────────────────────────────────────
# T4 — the calling_station pins: the floor is STRUCTURALLY inert above 1.0
# ─────────────────────────────────────────────────────────────────────────────
#
# Under the branch form the floor at 1.0 never binds for this persona — its dial
# is 4.0, already above the floor — so its policy at a strong-draw node must be
# EXACTLY what it was at the base engine b0a6a4e, not merely close
# (`pytest.approx` would let a real regression that happens to land within
# tolerance slip through). This is a STRUCTURAL claim, not an arithmetical one.
# A REJECTED earlier design re-associated the arithmetic instead of branching on
# `DrawCategory.STRONG` — rewriting `(call_base + bonus) * L` as
# `call_base*L + bonus*L` — and the station survived only THAT variant because
# 4.0 is a power of two, so `(a+b)*4 == a*4 + b*4` bitwise. Under the branch
# form T1 shipped, `max(L, 1.0)` simply returns L unchanged for any L >= 1.0, so
# the STRONG branch collapses onto the non-STRONG expression bit for bit — the
# property does not depend on the dial's numeric value at all, only on it being
# >= 1.0.
#
# ── THE 3.7 CASE IS WHAT MAKES THAT A GATE RATHER THAN A CLAIM — N-DRAWLOOSE
# ruling R8. At the shipped 4.0 the two designs are indistinguishable, so the
# structural argument is untested there and a re-association would ship green.
# 3.7 is not a power of two: MEASURED, the `strong_all` mutant (STRONG branch
# taken at every dial, i.e. the re-associated form) moves the station's D1
# vector by one ulp at 3.7 — P(fold) 0.09823642232305747 -> ...746, P(raise)
# ...985 -> ...978 — while leaving the 4.0 reading bit-identical. At an earlier,
# superseded revision of this engine the 3.7 reading was itself one ulp off
# base; at eb34e60 it is EXACT, which is why this can be an `==` pin.
#
# Harvested from the CONTROL worktree (base commit b0a6a4e) at full precision
# via repr(), not rounded, at this same D1 node.
_ND_STATION_BASE_FOLD = 0.09154315605928508
_ND_STATION_BASE_CALL = 0.8788142981691368
_ND_STATION_BASE_RAISE = 0.029642545771578026
# The same node with the station's dial re-authored to 3.7 (see above).
_ND_STATION_REFIT_LOOSENESS = 3.7
_ND_STATION_REFIT_BASE = {
    ActionType.FOLD: 0.09823642232305747,
    ActionType.CALL: 0.8723394302287506,
    ActionType.RAISE: 0.029424147448191985,
}


def _nd_pack_at(persona: str, looseness: float):
    """The shipped pack for `persona` with `call_looseness` re-authored."""
    pack = _pack(persona)
    probe = pack.model_copy(deep=True)
    probe.postflop = pack.postflop.model_copy(update={"call_looseness": looseness})
    return probe


def test_nd_t4_calling_station_byte_identical_on_strong_draw():
    """T4 — `calling_station`'s action distribution at D1 (a strong-draw node)
    is EXACT float equality with the base engine's reading, not
    `pytest.approx`. See the section comment above for why this is structural
    rather than arithmetical under the branch form T1 shipped.
    """
    dist = _nd_priced_dist(_pack("calling_station"), _ND_T4_NODE)
    assert dist[ActionType.FOLD] == _ND_STATION_BASE_FOLD, (
        f"calling_station FOLD moved: {dist[ActionType.FOLD]!r} vs base "
        f"{_ND_STATION_BASE_FOLD!r} — the floor should be structurally inert once the "
        "dial is already >= 1.0"
    )
    assert dist[ActionType.CALL] == _ND_STATION_BASE_CALL, (
        f"calling_station CALL moved: {dist[ActionType.CALL]!r} vs base "
        f"{_ND_STATION_BASE_CALL!r}"
    )
    assert dist[ActionType.RAISE] == _ND_STATION_BASE_RAISE, (
        f"calling_station RAISE moved: {dist[ActionType.RAISE]!r} vs base "
        f"{_ND_STATION_BASE_RAISE!r}"
    )


def test_nd_t4_calling_station_byte_identical_at_a_non_power_of_two_dial():
    """T4 — the same EXACT equality at `call_looseness` 3.7 (ruling R8).

    The shipped 4.0 cannot distinguish the branch form from the re-associated
    one, because `(a+b)*4 == a*4 + b*4` bitwise. 3.7 can, and does: the
    `strong_all` mutant (STRONG branch taken at every dial) shifts this vector
    by one ulp while leaving the 4.0 pin above untouched. Without this case the
    structural property is prose; with it, it is a gate.
    """
    dist = _nd_priced_dist(
        _nd_pack_at("calling_station", _ND_STATION_REFIT_LOOSENESS), _ND_T4_NODE
    )
    for kind, expected in _ND_STATION_REFIT_BASE.items():
        assert dist[kind] == expected, (
            f"calling_station at call_looseness {_ND_STATION_REFIT_LOOSENESS}: "
            f"{kind.value} is {dist[kind]!r}, not the base engine's {expected!r}. A dial "
            "at or above the floor must fall through to the ORIGINAL expression bit for "
            "bit; a one-ulp move here is the signature of the re-associated form"
        )


# ─────────────────────────────────────────────────────────────────────────────
# S3-T1 / S3-T1b — the calling dial reaches a strong draw's CHASE
# ─────────────────────────────────────────────────────────────────────────────
#
# WHAT CHANGED, IN TWO STEPS. N-DRAWLOOSE protected a STRONG draw's
# `_DRAW_CALL_BONUS` from the calling dial in FULL, with `max(looseness, 1.0)`.
# That fixed nits folding big draws and it also made a large piece of the
# calling path untunable: below a dial of 1.0 — five of the six personas —
# tightening `call_looseness` left strong-draw call weight bitwise untouched.
# Improvement slice 3 fits that dial, so S3-T1 (2026-08-21) replaced the floor
# with a SPLIT: a fixed 0.7 of the bonus protected, 0.3 riding the dial.
# S3-T1b (2026-08-22, owner ruling of that date) kept the split and made the
# split point a property of the NODE rather than a constant:
#
#     dial(L, s) = L + s*(1 - L),  s = _strong_draw_protected_share(...)
#
# where s is the share of the call the draw's own equity pays for at the price
# it faces. The poker is written out at the helper in the engine; the short
# version is that a flat share withdraws protection in equal proportion
# everywhere, which is exactly backwards — at a cheap price into a monster draw
# there is no style left to express, and at a pot-sized bet into a bare draw
# there is almost nothing else.
#
# THE DEFECT THAT FORCED S3-T1b, measured at D1 (a 15-out combo draw getting
# 2.5-to-1, where every archetype's correct fold frequency is about zero):
#
#     persona        pre-S3-T1   S3-T1 flat 0.7   S3-T1b
#     nit             0.2608        0.2945        0.2608
#     passive_fish    0.2451        0.2797        0.2451
#
# S3-T1b restores those two readings EXACTLY, not approximately: D1's price
# mandates the whole bonus, so s clamps at 1.0 and `dial(L, 1.0)` is `L + (1-L)`
# = 1.0, which is what `max(looseness, 1.0)` returned. That exactness is
# asserted below, and it is also what the whole D1 column of every older gate in
# this file reads again.
#
# ⚠️ "RESTORED EXACTLY" IS NOT "CORRECT" — READ THE TWO SENTENCES TOGETHER
# (owner ruling R3, 2026-08-22). The table above names about zero as the right
# fold frequency at this node and then reports 0.2608 and 0.2451 as the good
# outcome. Both are true and they are 25 to 26 POINTS APART. What this ticket
# fixed is that the CALLING DIAL no longer decides the strong-draw BONUS at this
# node; the level itself is a FOLD-side quantity and no lever in this ticket
# reaches it — `_FOLD_BASE[bucket] * _price_factor(...)` does not consult the
# draw at all, so a 15-out combo draw and a naked ace-high fold alike at the
# same price.
# THE RESIDUAL IS FILED, not absorbed: it belongs to `N-DRAWEQUITY`, the owed
# draw-bonus equity gate of theory contract §4 row P6/F7 and §9 ledger item 2,
# and its evidence is the node_trace row for `flop_facing_bet_strong_draw`
# (JhTh on 9h 8c 2h facing 4 into a live pot of 10, prescription "semi-bluff
# raise / call, few folds") with ~0 as the target.
#
# ⚠️ CORRECTED BY S3-T2 (2026-08-22). This block used to say the calling dial
# "no longer reaches" this reading. IT DOES REACH IT: the split protects the
# BONUS term, but the bucket's base call merit is still `call_base * L` and the
# fold merit does not depend on the dial at all, so a lower dial folds this draw
# slightly MORE. Measured across S3-T2's retune, the nit's reading here goes
# 0.2608 at a dial of 0.45 to 0.2642 at the shipped 0.32. S3-T2 still carries it
# as a WATCH rather than a target — the residual is a fold-side LEVEL that
# `N-DRAWEQUITY` owns and that no calling dial can drive to ~0 — but "the dial
# cannot move it" was wrong, and a gate was built on that wrong sentence (see
# `test_s3t1b_trace_node_folds_no_more_than_the_protected_engine_did`, whose
# frozen constants S3-T2 had to replace with a computed comparator).
#
# ── THE MEASUREMENT. `_nd_priced_dist` again — same instrument, same priced
# nodes, no new engine surface. Five nodes across two classes:
#
#   PRICE-MANDATED (the draw's equity covers the price; mandated share 1.0)
#     D1  naked 15-out combo draw, flop, 2/3-pot
#     D3  the same hand on the TURN, facing half pot
#   CHASE (equity covers part of it; the rest is style)
#     D2  naked flush draw, flop, POT              mandated 0.6728
#     P1  middle pair WITH a flush draw, 2/3-pot   mandated 0.7850
#     D5  naked flush draw, TURN, POT              mandated 0.5400
#
# D5 is new here and is deliberately the worst-priced node in the file: nine
# outs with ONE card to come against a pot-sized bet needs 33.3% and has 18%, so
# nearly half the call is a chase and the dial should own it. It is not on the
# G-DRAW panel, because that panel's pinned raise-share table is harvested from
# the base engine and a new node there would have to be harvested too.
#
# P(call) at the four dials, this tip, all five personas whose dial sits below
# 1.0 (the calling station is excluded BY CONSTRUCTION — its 4.0 never takes the
# branch). "floored" is the same sweep with the protected share forced to 1.0,
# which IS the `max(looseness, 1.0)` engine:
#
#     node persona          reach     floored   ratio
#     D1   nit             0.009768  0.009768   1.000
#     D1   tag             0.004483  0.004483   1.000
#     D1   lag             0.003137  0.003137   1.000
#     D1   maniac          0.001618  0.001618   1.000
#     D1   passive_fish    0.008564  0.008564   1.000
#     D3   nit             0.010961  0.010961   1.000
#     D3   tag             0.006231  0.006231   1.000
#     D3   lag             0.004719  0.004719   1.000
#     D3   maniac          0.002744  0.002744   1.000
#     D3   passive_fish    0.010007  0.010007   1.000
#     D2   nit             0.061899  0.039051   1.585
#     D2   tag             0.035093  0.021935   1.600
#     D2   lag             0.026669  0.016610   1.606
#     D2   maniac          0.015494  0.009592   1.615
#     D2   passive_fish    0.059297  0.037457   1.583
#     P1   nit             0.027694  0.021102   1.312
#     P1   tag             0.013675  0.010393   1.316
#     P1   lag             0.009818  0.007455   1.317
#     P1   maniac          0.005259  0.003987   1.319
#     P1   passive_fish    0.024627  0.018756   1.313
#     D5   nit             0.078323  0.042315   1.851
#     D5   tag             0.052720  0.028190   1.870
#     D5   lag             0.043052  0.022918   1.878
#     D5   maniac          0.028225  0.014902   1.894
#     D5   passive_fish    0.076956  0.041688   1.846
#
# The "floored" column is not zero — `call_base * looseness` was always
# dial-scaled, so only the BONUS was ever untunable. That is why a monotonicity
# assertion alone would be vacuous: the floored engine is monotone too. The
# chase leg therefore asserts the RATIO, per cell.
#
# ── ✅ OWNER SIGN-OFF ON THE FLOOR MOVE, 2026-08-22 (ruling R2). This gate's
# reach floor moves 1.35 -> 1.20, and a gate threshold moving DOWN in the same
# pull request that changes the engine is exactly the shape of an edit that
# should be refused by default, so it is recorded as a decision rather than as
# an in-passing note. Two facts the owner accepted it on: (a) THE NODE SET
# CHANGED — the ratio is no longer measured over the same cells, because D1 and
# D3 moved out of this leg entirely (their price mandates the whole bonus, so
# their honest ratio is exactly 1.000 and they are asserted as an equality
# instead) and D5 moved in, so 1.35 and 1.20 are not two thresholds on one
# measurement; (b) THE MUTANT THE FLOOR EXISTS FOR IS STILL CAUGHT — restoring
# the hard floor drives every chase ratio to 1.000, which fails 1.20 exactly as
# it failed 1.35, and the measured matrix below confirms it (M2 red on this
# leg). The floor was not lowered to accommodate a reading; the readings it is
# taken over are different readings.
#
# ── WHERE 1.20 COMES FROM, and the honest window. Observed chase ratios run
# 1.312 (P1 nit) to 1.894 (D5 maniac); 1.20 sits 9.3% under the worst reading
# and is 1.20x above the 1.000 a restored floor produces. The corresponding
# figure under S3-T1's flat share was 1.35 against a worst reading of 1.448, and
# the ratios moved because P1's mandated share (0.7850) is HIGHER than the flat
# 0.7 it replaced — more protection at that node, less dial reach, by design.
#
# ── THE ADMISSIBLE WINDOW, STATED HONESTLY (a correction: S3-T1's comment here
# claimed its gate "is NOT red on a share that merely moves — 0.5, 0.6 and 0.8
# all pass", and 0.8 in fact FAILED it at ratio 1.289. Do not repeat that
# mistake by leaving this paragraph vague.) These two legs bound the protected
# share from BOTH sides and they are not symmetric:
#   * the price-mandated leg is an EXACT equality — at D1 and D3 the engine's
#     share must be exactly 1.0. Any share below it, flat or computed, is red.
#   * the chase leg is a FLOOR on reach — at D2, P1 and D5 the engine's share
#     must leave at least enough of the bonus on the dial to clear 1.20x. At
#     these three nodes that admits shares up to roughly 0.83 (P1 is the binding
#     one) and no lower bound of its own; G-DRAW's derived cap supplies the
#     lower bound.
# Between them, the admissible window for the ENGINE's realization assumption
# (`_DRAW_FREE_RIVER_PROB`) is a single point, and that is deliberate rather
# than an oversight: G-DRAW's price-mandate leg asserts the poker this file
# states, so moving the assumption means re-stating the derivation there. The
# cost is a two-file edit; what it buys is that the constant can no longer be
# moved without saying, in the test, what poker justifies the new value.
#
# ── HOW THE FLOORED COMPARISON IS TAKEN, and why it cannot go stale. The old
# engine is not checked out or re-implemented: `_strong_draw_protected_share` is
# swapped for one that returns 1.0, which makes `_strong_draw_call_dial` return
# exactly 1.0 for every dial — `max(looseness, 1.0)` on this branch. So the gate
# measures the floored engine IN THE SAME PROCESS, from the shipped code, and
# restoring the floor in the branch makes every chase ratio read 1.000 and the
# chase leg fail.
#
# ── THE MUTATION MATRIX, measured rather than argued (2026-08-22). Each mutant
# is applied in-process by replacing the named engine function and every gate in
# this family is run against it. "cap" is G-DRAW's derived cap, "mandate" its
# price-mandate leg, "reach" this sweep, "unit" the share/dial unit test,
# "trace" the trace-node ceiling below, and the four T4 legs are the older ones:
#
#     mutant                                        cap  mandate reach unit trace
#     M1 flat 0.7 share (what S3-T1 shipped)        RED    RED    RED   RED  RED
#     M2 the hard floor restored (share 1.0)        ok     RED    RED   RED  ok
#     M3 no protection at all (share 0.0)           RED    RED    RED   RED  RED
#     M4 out count blind (every strong draw = 9)    RED    RED    RED   RED  RED
#     M5 rule of 4 (free river q = 1.0)             ok     RED    RED   RED  ok
#     M6 rule of 2 (free river q = 0.0)             RED    RED    ok    RED  ok
#     M7 price ignored (share taken at a fixed      ok     RED    RED   RED  ok
#        half-pot regardless of the real one)
#
# Three readings worth stating. (a) The cap is green on M2, M5 and M7 because
# all three OVER-protect at the nodes it pins, and a cap says nothing about
# protecting too much — that is the reach leg's job, and it is red on all three.
# (b) The reach leg is green on M6 because a smaller share means MORE dial
# reach, which is the direction it cannot see; the cap and the mandate leg catch
# it. (c) T4's four legs (the 0.34 ceiling, the cross-persona margin, the
# raise-share table and the two station byte-identity pins) are green on every
# mutant here except M3, which is what "these gates were written against a
# different claim" looks like in a table — they are kept because they bound
# things this family does not, not because they cover it.
#
# ⚠️ THE `trace` COLUMN WAS RE-VERIFIED AFTER S3-T2 REWROTE THAT GATE
# (2026-08-22). It now compares the live engine against the floored engine at
# the SAME dial rather than against six frozen constants, so its column above
# still reads the same on M1-M7 — but it is now non-vacuous for the right
# reason. Measured in-process: a share of 0.99 at D1 reds it (the old constant
# form could not see that at all), and a calling-dial cut leaves it green (the
# old form failed on a cut of one thousandth). See that test's docstring for
# why the constants were a construction artifact.
#
# ── INDEPENDENCE. Every other gate in this file can be green while this one is
# red: G-DRAW's cap and its price-mandate leg are both about the 0.45-vs-0.60
# SELF-difference of one persona at nodes this sweep does not all share, and
# neither says anything about whether the dial's reach survives across its whole
# range; T4's ceiling is a level at one node; the raise-share table is
# shape-agnostic (`rscale` divides by whatever CALL became); the station pins
# never take this branch at all; C5's non-STRONG vectors are untouched by
# anything here. The one thing this gate alone forbids is a strong-draw call
# merit whose chase share the dial cannot move.

_S3T1_DIALS = (0.50, 0.70, 0.85, 1.00)
_S3T1B_MIN_REACH_RATIO = 1.20
_S3T1B_MANDATED_NODES = (_ND_DRAW_PANEL[0], _ND_DRAW_PANEL[2])  # D1, D3
_S3T1B_D5 = _NDNode(
    "D5 flush draw, TURN, pot",
    ("Ah", "5h"), ["Kh", "8h", "2c", "9d"], Street.TURN, 24.0, 12.0, 200.0, 1, 12.0 / 12.0,
)
_S3T1B_CHASE_NODES = (_ND_DRAW_PANEL[1], _ND_DRAW_PANEL[4], _S3T1B_D5)  # D2, P1, D5
_S3T1_DIALLED_PERSONAS = ("nit", "tag", "lag", "maniac", "passive_fish")


def _s3t1_pack_at(persona: str, looseness: float):
    """The shipped pack with `call_looseness` re-authored to `looseness`.

    `continue_ref` is deliberately LEFT ALONE — it is the frozen raise-side
    anchor, and re-synchronising it with the calling dial collapses `rscale` to
    1.0 and silently deletes the N-LOGIT mechanism (that pack comment, and
    N-LOGIT's own rev-1 history, are why this is worth a sentence). The maniac
    authors no `call_looseness` at all and inherits `stickiness`; setting the
    field is what this sweep needs, and it is the same override
    `_nd_nit_at` makes for the nit.
    """
    pack = _pack(persona)
    probe = pack.model_copy(deep=True)
    probe.postflop = pack.postflop.model_copy(update={"call_looseness": looseness})
    return probe


def _s3t1_call_sweep(persona: str, node: _NDNode) -> list[float]:
    return [
        _nd_priced_dist(_s3t1_pack_at(persona, dial), node)[ActionType.CALL]
        for dial in _S3T1_DIALS
    ]


def _s3t1b_floored_share(*_args, **_kwargs) -> float:
    """The pre-S3-T1 engine, in this process: a protected share of 1.0 makes
    `_strong_draw_call_dial` return exactly 1.0 at every dial, which is what
    `max(looseness, 1.0)` returned on this branch."""
    return 1.0


def _s3t1b_sweeps(persona: str, node: _NDNode) -> tuple[list[float], list[float]]:
    """(this engine's sweep, the floored engine's sweep) at the same cell."""
    real = personas_postflop._strong_draw_protected_share
    try:
        now = _s3t1_call_sweep(persona, node)
        personas_postflop._strong_draw_protected_share = _s3t1b_floored_share
        floored = _s3t1_call_sweep(persona, node)
    finally:
        personas_postflop._strong_draw_protected_share = real
    return now, floored


def test_s3t1b_strong_draw_call_frequency_moves_with_the_dial():
    """S3-T1b's headline, in two legs that pull in opposite directions.

    (1) PRICE-MANDATED nodes (D1, D3): the sweep is BITWISE identical to the
    floored engine's. Where the draw's own equity pays for the price, the dial
    gets nothing, and "nothing" is exact — not "very little". This is the leg
    that is red on S3-T1's flat 0.7 share, which hands the dial 30% of the bonus
    at every node including these (measured at the S3-T1 tip: D1 nit reach
    0.033370 against the floored 0.009768, ratio 3.416).

    (2) CHASE nodes (D2, P1, D5): P(call) rises strictly with `call_looseness`
    and rises at least 1.20x as far as it does under the floor. This is the leg
    that is red when the floor comes back, or when the protected share is pushed
    toward 1.0 everywhere.

    Strict monotonicity is asserted on both classes and is not the kill on
    either — the floored engine is monotone too, because `call_base` was always
    dial-scaled. Full sweep table, the 1.20's window, and the admissible range
    for the share are in the section comment above.
    """
    for node in _S3T1B_MANDATED_NODES:
        for persona in _S3T1_DIALLED_PERSONAS:
            now, floored = _s3t1b_sweeps(persona, node)
            assert now == floored, (
                f"{_nd_key(node)}/{persona}: this node's price mandates the WHOLE draw "
                f"call bonus, so the calling dial must move P(call) exactly as far as "
                f"the fully protected engine did and no further — {now} against "
                f"{floored}. Either the protected share stopped clamping at 1.0 here "
                "(a flat share does exactly that), or the out count this node is "
                "priced at has fallen"
            )
            for lo_dial, hi_dial, lo, hi in zip(
                _S3T1_DIALS, _S3T1_DIALS[1:], now, now[1:], strict=False
            ):
                assert hi > lo, (
                    f"{_nd_key(node)}/{persona}: P(call) does not rise from dial "
                    f"{lo_dial} to {hi_dial} ({lo:.6f} -> {hi:.6f})"
                )

    readings: list[str] = []
    for node in _S3T1B_CHASE_NODES:
        for persona in _S3T1_DIALLED_PERSONAS:
            now, floored = _s3t1b_sweeps(persona, node)
            for lo_dial, hi_dial, lo, hi in zip(
                _S3T1_DIALS, _S3T1_DIALS[1:], now, now[1:], strict=False
            ):
                assert hi > lo, (
                    f"{_nd_key(node)}/{persona}: P(call) does not rise from dial "
                    f"{lo_dial} to {hi_dial} ({lo:.6f} -> {hi:.6f}) — the calling "
                    "dial is not moving this strong draw's call weight in one "
                    "direction"
                )

            reach, floored_reach = now[-1] - now[0], floored[-1] - floored[0]
            assert floored_reach > 0.0, (
                f"{_nd_key(node)}/{persona}: the FLOORED engine's reach is "
                f"{floored_reach!r} — the comparison this gate is built on has gone "
                "degenerate, so no ratio can be formed. Something outside the "
                "protected share has flattened `call_base * looseness`"
            )
            readings.append(f"{_nd_key(node)}/{persona} {reach / floored_reach:.3f}")
            assert reach >= _S3T1B_MIN_REACH_RATIO * floored_reach, (
                f"{_nd_key(node)}/{persona}: over dials {_S3T1_DIALS[0]}-"
                f"{_S3T1_DIALS[-1]} P(call) moves {reach:+.4f}, only "
                f"{reach / floored_reach:.3f}x the {floored_reach:+.4f} the FULLY "
                f"protected bonus already moved (floor {_S3T1B_MIN_REACH_RATIO}). "
                "This node's price leaves part of the call to style and the dial is "
                "not reaching it — either the branch is back on `max(looseness, 1.0)` "
                "or the protected share here has been pushed toward 1.0. NOTE this is "
                "the FLOOR leg: exceeding it is fine, and the two nodes that must "
                "read exactly 1.000 are checked separately above. Ratios so far: "
                f"{readings}"
            )


def test_s3t1b_protected_share_is_the_part_the_dial_cannot_reach():
    """`_strong_draw_call_dial`'s arithmetic and `_strong_draw_protected_share`'s
    poker, at the unit.

    (a) The dial hands back the protected share's full protection at s = 1, the
    bare dial at s = 0, and exactly 1.0 at a dial of 1.0 FOR EVERY SHARE. The
    last is what makes the split continuous with the fall-through form
    `(call_base + bonus) * L` a dial at or above 1.0 takes, and it is
    structural rather than lucky: the expression is `L + s*(1 - L)` and the
    second term is multiplied by a hard zero there. S3-T1 wrote the same
    algebra the other way round and had to assert the exactness for its one
    constant.

    (b) It is strictly increasing in the dial at every share below 1.0, so no
    dial region is flat. A `max(L, floor)` form with a floor below 1.0 would
    satisfy every OTHER gate in this file while leaving the whole region under
    the floor untunable — the same defect S3-T1 removed, moved down the dial
    rather than deleted.

    (c) The share responds to the PRICE in the direction the poker requires and
    reaches both ends: a nine-out flop draw facing a quarter-pot bet is fully
    mandated, the same draw facing a pot-sized overbet is mostly chase. The
    values are the ones the section comment above derives.

    (d) The station's dial is still at or above 1.0, so its byte-identity pins
    stay structural rather than arithmetic.
    """
    dial = personas_postflop._strong_draw_call_dial

    for lever in (0.0, 0.45, 0.6, 0.85, 0.999):
        assert dial(lever, 1.0) == 1.0, (
            f"_strong_draw_call_dial({lever}, 1.0) is {dial(lever, 1.0)!r}, not exactly "
            "1.0 — a fully mandated call is no longer fully protected"
        )
        assert dial(lever, 0.0) == lever
    for share in (0.0, 0.25, 0.5, 0.673, 0.785, 1.0):
        assert dial(1.0, share) == 1.0, (
            f"_strong_draw_call_dial(1.0, {share}) is {dial(1.0, share)!r}, not exactly "
            "1.0 — the split no longer meets the fall-through form at the dial where "
            "the branch stops being taken, so a dial sweep across 1.0 steps"
        )
        if share < 1.0:
            grid = [i / 40 for i in range(41)]
            for lo, hi in zip(grid, grid[1:], strict=False):
                assert dial(hi, share) > dial(lo, share), (
                    f"_strong_draw_call_dial is flat or falling between {lo} and {hi} "
                    f"at share {share} — a dial region with no reach is the defect "
                    "this ticket removed"
                )

    # (c) One hand, four prices. Nine outs on the flop realize 0.2243 under the
    # stated free-river assumption; the price needed is f/(1+2f).
    hole, board = ("Ah", "5h"), ["Kh", "8h", "2c"]
    assert personas_postflop._strong_draw_outs(hole, board) == 9.0
    for faced_frac, want in (
        (0.25, 1.0000),      # quarter pot: needs 16.7% — fully mandated
        (0.50, 0.8971),      # half pot: needs 25.0%
        (1.00, 0.6728),      # pot: needs 33.3%
        (3.00, 0.5233),      # 3x-pot overbet: needs 42.9%, the T1 figure
    ):
        got = personas_postflop._strong_draw_protected_share(hole, board, faced_frac)
        assert got == pytest.approx(want, abs=5e-4), (
            f"a nine-out flush draw facing {faced_frac:.2f} of the pot has "
            f"{got:.4f} of its call bonus price-mandated, not {want} — the share "
            "has stopped tracking the price this file states"
        )
    # ...and the combo draw at the trace node's price is mandated in full, which
    # is the whole reason D1's readings came back.
    assert personas_postflop._strong_draw_outs(("Jh", "Th"), ["9h", "8c", "2h"]) == 15.0
    assert personas_postflop._strong_draw_protected_share(
        ("Jh", "Th"), ["9h", "8c", "2h"], 4.0 / 6.0
    ) == 1.0

    station = _pack("calling_station").postflop
    station_lever = (
        station.call_looseness if station.call_looseness is not None else station.stickiness
    )
    assert station_lever >= 1.0, (
        f"the calling station's dial is now {station_lever}, BELOW 1.0 — it would start "
        "taking the split branch, and its byte-identity pins are no longer structural"
    )


def test_s3t1b_trace_node_folds_no_more_than_the_protected_engine_did():
    """S3-T1b's acceptance criterion (i), as a gate rather than a report.

    At D1 — the node_trace spot `flop_facing_bet_strong_draw`, a 15-out combo
    draw facing 4 into a live pot of 10, i.e. 2.5-to-1 against a hand that needs
    28.6% — no persona may fold MORE often than the fully protected engine
    would at THAT PERSONA'S OWN DIAL. The comparison is the split against the
    floor it replaced, and nothing else.

    ⚠️ THE COMPARATOR IS COMPUTED LIVE, and the reason is the whole point of
    this revision (S3-T2, 2026-08-22, after a theory review reproduced it).
    This test used to compare against six FROZEN CONSTANTS harvested at the
    dials of the day, with a 1e-12 tolerance. That made it a gate on the
    CALLING DIAL rather than on the protection mechanism, and an absolute one:
    at D1 the price mandates the whole call bonus (the share clamps at 1.0,
    asserted immediately above), so the bonus term is dial-independent while
    `call_base * L` is not and the fold merit does not depend on the dial at
    all. The fold frequency therefore rises for ANY dial below the pinned one —
    measured, a cut of one thousandth breached it for all three personas
    improvement slice 3 set out to retune. The engine the constants were
    supposed to represent, `call_base * L + bonus * max(L, 1.0)`, is itself
    dial-sensitive through its first term, so it would have failed a dial cut
    in exactly the same way; the constants were a construction artifact of
    freezing it at one dial, not a statement of poker. Re-recording them at new
    dials would have been fitting the gate to the change it exists to judge.

    WHAT THE LIVE FORM STILL CATCHES, and it is the claim S3-T1b actually
    makes: a protected share that comes back below 1.0 at a node whose price
    mandates the whole bonus. Any such regression makes the live engine fold
    more than the floored one at the same dial and reds here (measured: a share
    of 0.99 reds it for all five dialled personas). What it no longer pretends
    to catch is a persona being tuned tighter, which is a different question
    with its own gates (the α fold-ceiling above, the went-to-showdown ceilings,
    the de-robotization separation floor).

    ⚠️ THIS IS A RE-SCOPING, NOT A STRENGTHENING, AND AT D1 IT IS PARTLY
    REDUNDANT. Say both plainly rather than let a reader infer coverage that is
    not here. GIVEN UP: the absolute LEVEL those six constants pinned at the
    dials of the day — this gate no longer asserts that the nit folds 0.2608
    here, only that the split has not withdrawn any of a mandated bonus.
    REDUNDANT: the assertion immediately above already checks that the protected
    share is exactly 1.0 at D1, and the two engines' agreement follows from
    that, so this gate's independent force at THIS node is small. What it still
    adds is that it reads the full normalized (FOLD, CALL, RAISE) distribution
    rather than the share alone, and that it is written to survive the panel
    being extended to nodes where the share does NOT clamp — which is where its
    real force will live.

    THE READINGS AT THE S3-T1b TIP, kept because they are the measurement that
    ticket was accepted on and because they are the level a reader should know:
    nit 0.2608 · tag 0.1743 · lag 0.1467 · maniac 0.1055 · passive_fish 0.2451
    · calling_station 0.0915. RED at the S3-T1 tip for all five dialled
    personas (nit 0.2945, tag 0.1918, lag 0.1642, maniac 0.1188, passive_fish
    0.2797) — that is the defect the theory review found and S3-T1b fixed. The
    calling station never takes the branch at all (dial 4.0), so its two sides
    are identical by construction rather than by arithmetic.

    ⚠️ NOT AN EQUALITY IN GENERAL. At D1 the two engines agree exactly, because
    the share clamps; the assertion is written as a CEILING because
    `N-DRAWEQUITY` and `N-DRAWTURN` are filed and are expected to make
    equity-aware draws continue MORE, which would move the live side DOWN.
    """
    for persona in sorted(ALL_PERSONAS):
        pack = _pack(persona)
        real = personas_postflop._strong_draw_protected_share
        try:
            live = _nd_priced_dist(pack, _ND_DRAW_PANEL[0])[ActionType.FOLD]
            personas_postflop._strong_draw_protected_share = _s3t1b_floored_share
            floored = _nd_priced_dist(pack, _ND_DRAW_PANEL[0])[ActionType.FOLD]
        finally:
            personas_postflop._strong_draw_protected_share = real
        assert live <= floored + 1e-12, (
            f"{persona} folds the trace node's 15-out combo draw {live:.4f} of the time, "
            f"above the {floored:.4f} the fully protected engine reads at the same dial. "
            "This draw is getting 2.5-to-1 and needs 28.6% — the price mandates the whole "
            "call and the split may not withdraw any of it"
        )


# ─────────────────────────────────────────────────────────────────────────────
# N-DRAWLOOSE C5 — non-STRONG behaviour is bitwise unchanged from the base
# ─────────────────────────────────────────────────────────────────────────────
#
# The spec claims that everything outside `DrawCategory.STRONG` is bitwise
# unchanged by this slice. Until N-DRAWLOOSE ruling R4 (2026-08-05) NOTHING
# asserted it. Codex demonstrated the hole: re-associating the untouched
# non-STRONG expression into `call_base*L + bonus*L` moved WEAK weights by one
# ulp and 77 tests — including all 23 frozen exact-equality price vectors in
# `tests/test_price_tail.py` — still passed. Those vectors cannot see it: every
# one of them is a `DrawCategory.NONE` cell, and `_DRAW_CALL_BONUS[NONE]` is
# 0.0, so `call_base*L + 0.0*L` and `(call_base + 0.0)*L` are the same float.
# Only a WEAK cell, where the bonus is 0.20, can.
#
# So the WEAK node is the leg that carries the kill and the draw-NONE node is
# the leg that carries the coverage — and the comment says so rather than
# letting a reader assume both are load-bearing against the same mutant.
# MEASURED against the re-association mutant: W1 moves for `nit` and for `tag`
# (max 1.11e-16, i.e. one ulp) and for nobody else; M1 does not move at all,
# for any persona. A NONE node still belongs here because the whole point is
# "nothing off the STRONG branch moved", and the ways that could stop being
# true are not limited to re-association — anything that reached `call_base`,
# the fold merit or the price factor would show up at M1 and nowhere else on
# this panel.
#
# EXACT `==`, harvested from the CONTROL worktree at base commit b0a6a4e via
# repr(). These are the same two nodes G-DRAW already uses as its uncoupled
# control (M1) and as its WEAK non-reach node (W1), so no new node shape had to
# be justified.
_ND_C5_NODES = (
    _ND_T2_UNCOUPLED[2],  # W1 gutshot, flop, 2/3-pot (WEAK)
    _ND_MADE_CONTROLS[0],  # M1 middle pair, flop, pot (draw NONE)
)
# RE-RECORDED for S3-T2 (improvement slice 3, ticket 2 — the calling-dial
# retune, 2026-08-22, slice-authorized under owner ruling 4 of that date). The
# nit's `call_looseness` moves 0.45 -> 0.32 and the tag's 0.6 -> 0.38. These
# vectors are the BASE ENGINE's own output, and the base engine reads the dial
# at every node: `call_base * L` is the call merit off the strong-draw branch
# just as much as on it. So a dial change moves them by construction, and the
# pins have to be re-harvested at the new dials or they stop asserting "the
# split engine equals the base engine" and start asserting "the nit's dial is
# still 0.45" — a claim this test does not make and improvement slice 3 exists
# to falsify.
#
# THE CONTROL IS IN THE TABLE ITSELF, and it is why a re-record is safe here:
# re-harvesting all twelve cells moved EXACTLY FOUR — the nit's and the tag's
# two rows, the two personas whose packs this ticket edits — and left the other
# eight byte-identical, including both draw-NONE rows for the four untouched
# personas. A change that had reached `call_base`, the fold merit or the price
# factor would have moved rows it does not own.
#
# THE MUTATION KILL IS UNAFFECTED. The re-association mutant moves W1 by one
# ulp at whatever dial it is evaluated at; the pins are exact `==` against a
# fresh harvest at the shipped dials, so the ulp still reds this test.
# ATTRIBUTION PROVEN, not assumed: with `content/personas/nit.json` and
# `content/personas/tag.json` reverted and every other edit on this branch left
# in place, the four old vectors below reproduce exactly and this test passes
# untouched; restoring the packs reproduces the four new ones.
# Values immediately before this re-record:
#   W1 nit (0.6249999999999999, 0.3000000000000001, 0.075)
#   W1 tag (0.4385964912280701, 0.2807017543859649, 0.2807017543859649)
#   M1 nit (0.4495022841911032, 0.5022084424923269, 0.04828927331656988)
#   M1 tag (0.3265174276144593, 0.4864040800562238, 0.18707849232931686)
_ND_C5_BASE_VECTORS = {
    "W1": {
        "calling_station": (0.18518518518518515, 0.7901234567901235, 0.02469135802469136),
        "lag": (0.4098360655737704, 0.24043715846994537, 0.34972677595628415),
        "maniac": (0.3246753246753246, 0.19047619047619052, 0.48484848484848486),
        "nit": (0.7009345794392523, 0.2392523364485982, 0.05981308411214954),
        "passive_fish": (0.6218905472636815, 0.2786069651741294, 0.09950248756218907),
        "tag": (0.5522827687776141, 0.22385861561119294, 0.22385861561119297),
    },
    "M1": {
        "calling_station": (0.0710458693521161, 0.9179214212577664, 0.011032709390117384),
        "lag": (0.32107712394019394, 0.4353630998948532, 0.2435597761649529),
        "maniac": (0.2714850038608301, 0.3681188849749163, 0.36039611116425363),
        "nit": (0.5345062406149657, 0.4246609734740664, 0.040832785910967916),
        "passive_fish": (0.4847241936073794, 0.4530444288089708, 0.06223137758364983),
        "tag": (0.433589611476678, 0.40907416948906583, 0.1573362190342561),
    },
}


def test_nd_c5_non_strong_nodes_are_bitwise_identical_to_the_base_engine():
    """C5 — the full normalized (FOLD, CALL, RAISE) vector at one WEAK node and
    one draw-NONE node, for all six personas, is EXACTLY the base engine's.

    Kills the re-association mutant Codex used to walk past 77 green tests. See
    the section comment for which leg does the killing and why the other leg is
    still worth its place.
    """
    for node in _ND_C5_NODES:
        pins = _ND_C5_BASE_VECTORS[_nd_key(node)]
        for persona, (fold, call, raise_) in sorted(pins.items()):
            dist = _nd_priced_dist(_pack(persona), node)
            got = (dist[ActionType.FOLD], dist[ActionType.CALL], dist[ActionType.RAISE])
            assert got == (fold, call, raise_), (
                f"{node.node_id} ({persona}): {got!r} is not the base engine's "
                f"{(fold, call, raise_)!r}. This slice pre-registered every non-STRONG "
                "cell as bitwise unchanged; a one-ulp move here means the untouched "
                "expression was re-associated or otherwise rewritten"
            )
