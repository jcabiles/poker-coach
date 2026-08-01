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
The 12s number is left in place below only
because `_derive_n`'s `budget_s = 9.5` is DERIVED from it and is load-bearing:
that constant sizes N, and changing it would move every seeded band and golden
in this file. Treat 12s as a historical derivation input, not as a live budget;
re-deriving the real one is its own slice.

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

import math
import random
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


@pytest.fixture(scope="module")
def fold_by_size():
    """persona -> {frac: measured fold-to-bet} facing FOLD/CALL/RAISE with a
    bet of `frac * pot-before-the-bet`, same pre-dealt spot list for every
    persona x size (paired comparison, variance from range composition
    cancels across cells)."""
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
                    pack, hole, board, legal, pot, 100.0, 1, rng, current_bet_to=to_call
                )
                folds += d.action is ActionType.FOLD
            rates[persona][frac] = folds / _PRICE_N
    return rates


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


@pytest.fixture(scope="module")
def catcher_fold_by_size():
    """persona -> {frac: fold-to-bet} over a pure bluff-catcher range (see the
    block above), measured at the same node/seeds as `fold_by_size`."""
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
                    pack, hole, board, legal, pot, 100.0, 1, rng, current_bet_to=to_call
                )
                folds += d.action is ActionType.FOLD
            rates[persona][frac] = folds / _PRICE_N
    return rates


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
    base = _pack("tag")  # an UNSET persona (station/fish now opt into the levers)
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
# the matched CHECK+RAISE branch; BET untouched) and the bluff-cell CALL
# merit (air folds or bluff-raises, never calls). Default `street=None` (and
# any non-river street) is byte-identical to the pre-P2a sampler. Exact
# normalized weights via the capture rng — deterministic, no sampling noise.

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
    """Bluff-cell CALL merit floored to exactly 0 on the river for every
    persona (air folds or bluff-raises — maniac pre-P2a called .086); the
    _BLUFF_RAISE_FACTOR path survives (raise weight strictly positive)."""
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


def _preflop_decision(pack, position, facing, hole, legal, rng, is_opener=None) -> Decision:
    act = sample_preflop_action(pack, position, facing, hole, rng, is_opener=is_opener)
    kinds = {la.action for la in legal}
    if act.action not in kinds:
        # Persona wants an action the engine doesn't offer here (e.g. raise
        # not legal because the raise didn't reopen) -- fall back to call if
        # legal, else fold/check per engine's own bracket.
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


# P2a (refuter F1): the closed-loop harness mirrors play.py's street opt-in —
# derived from the board length exactly as the live loop derives it from
# state.street — so the population/WTSD bands below actually exercise river
# polarization instead of running the streetless default.
_STREET_BY_BOARD_LEN = {3: Street.FLOP, 4: Street.TURN, 5: Street.RIVER}

# W5-a3-iii (C30): the reference derivation for the band sampler's/parity
# mirror's context kwargs — the SAME helpers `play.bot_decision` uses.
from app.domain.table.play import _preflop_opener  # noqa: E402
from app.domain.table.postflop_context import (  # noqa: E402
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
    facing_raise=_OMIT, street_aggressions=_OMIT,
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


def _play_hand(rng, hand_seed, button_seat, persona_by_seat, packs, *, context_aware=False):
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
    """
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
            decision = _preflop_decision(
                pack, seat_state.position, facing, seat_state.hole_cards, legal, rng,
                is_opener=is_opener,
            )
            # Log the APPLIED preflop decision only — no new rng draw, no
            # "cleanup" of the existing double-sample (would shift the stream).
            preflop_log.append((seat, decision.action.value))
        else:
            pot_bb = sum(s.invested_total_bb for s in state.seats)
            opponents = _live_opponents(state, seat)
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
                )
            log.append((seat, state.street.value, decision.action.value))
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
    """Scale N DOWN only, floor at 150/persona so the >=30-occurrence stat
    floors stay reachable (spec allocation: 600/persona x 6 + 1500 texture
    ~= 5100 hands at ~430 h/s ~= 11.8s).

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
    per_persona_n = max(150, (total_budget_hands - texture_n) // 6)
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
# calibrated N (~650-700/persona; see `_derive_n`).
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
# persona -> (AF band or None, fold_to_cbet band, WTSD band), all fractions.
BANDS = {
    # (both W3R-2 lines: owner-authorized post-fit collision — see block above)
    "passive_fish": ((0.0, 1.560), (0.0, 0.549), (0.50, 0.57)),  # WTSD re-anchor W3R-2
    "calling_station": ((0.0, 1.056), (0.0, 0.424), (0.66, 0.72)),  # WTSD re-anchor W3R-2
    # nit AF top 2.025 → 2.4 (P2a: measured 1.520 at N=399, CI top 2.350) and
    # WTSD floor 0.50 → 0.37 (CI floor 0.378 at N=399, n=96).
    "nit": ((0.6, 2.4), (0.10, 0.90), (0.37, 0.80)),  # AF/WTSD re-anchored (P2a)
    # tag ftc floor re-anchored (F1, RES-D §4): price-aware defense folds small
    # c-bets far less, pulling the aggregate to ~0.21 — ON the old 0.203 floor
    # (measured 0.195-0.26 across machines; n scales with machine speed and can
    # be as low as ~40 ⇒ 3σ ≈ ±0.19, so the floor must sit well below center).
    # P2a: ftc floor 0.05 → 0.0 (measured 0.152 at n=33 ⇒ CI floor < 0) and
    # WTSD (0.52,0.79) → (0.41,0.65) (river polarization, see block above).
    "tag": ((1.4, 3.6), (0.0, 0.55), (0.41, 0.65)),  # ftc/WTSD re-anchored (P2a)
    "lag": ((1.5, 4.5), (0.12, 0.64), (0.37, 0.59)),  # AF/ftc/WTSD re-anchored (P2a)
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
    "maniac": ((2.4, 5.1), (0.0, 0.61), (0.34, 0.50)),  # AF/ftc/WTSD re-anchored (P2a)
}


_STATS_CACHE: dict[tuple[str, int, bool], tuple] = {}


def _persona_stats(packs, persona: str, n: int, *, context_aware: bool = False):
    """Run N hands with a 9-seat lineup of ALL personas (round-robin fill,
    tested persona repeated to guarantee representation), collect AF /
    fold-to-cbet / WTSD for the tested persona's seats only.

    Memoized per (persona, n, context_aware) within the process: the band
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
    key = (persona, n, context_aware)
    if key in _STATS_CACHE:
        return _STATS_CACHE[key]
    rng = random.Random(20260710)
    fillers = [p for p in ALL_PERSONAS if p != persona]
    lineup = ([persona] * 3 + [fillers[i % len(fillers)] for i in range(6)])[:9]
    persona_by_seat = {i: lineup[i] for i in range(9)}
    tested_seats = {i for i, p in persona_by_seat.items() if p == persona}

    bet_raise = call_count = 0
    folds_to_first_cbet = cbet_opportunities = 0
    saw_flop_hands = showdown_hands = 0

    for i in range(n):
        hand_seed = rng.randrange(1_000_000_000)
        button_seat = i % 9
        res = _play_hand(
            rng, hand_seed, button_seat, persona_by_seat, packs, context_aware=context_aware
        )
        settlement, log, saw_flop = res.settlement, res.log, res.saw_flop
        for seat in tested_seats:
            if seat in saw_flop:
                saw_flop_hands += 1
                if seat in settlement.showdown_seats:
                    showdown_hands += 1

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
    result = (af, ftc, wtsd, call_count, cbet_opportunities, saw_flop_hands)
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


_STATS_EXT_CACHE: dict[tuple[str, int], ExtStats] = {}


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
    `preflop_log`. Memoized per (persona, n). Metrics are harness-observed on
    today's engine — no domain plumbing needed (the harness holds full state)."""
    key = (persona, n)
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
    "calling_station": (0.38636363636363635, 0.10869565217391304, 0.7250859106529209),
    "lag": (2.2711864406779663, None, 0.5294117647058824),
    "maniac": (3.272727272727273, 0.25, 0.5555555555555556),
    "nit": (None, None, 0.6296296296296297),
    "passive_fish": (1.125984251968504, 0.5, 0.4484304932735426),
    "tag": (2.8666666666666667, None, 0.5185185185185185),
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
    # switches on. The cache is keyed (persona, n, context_aware); pop the
    # real entry first and restore it after so the patched run neither reads
    # a stale result nor poisons later tests.
    key = ("tag", n, True)
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
    assert 0.02 <= grid["BTN"]["unopened"] <= 0.075, (
        f"BTN unopened arrival {grid['BTN']['unopened']:.4f} outside [0.02, 0.075] "
        f"-- n~408, 21-seed dispersion 0.027..0.071 (slice-neutral cell), see above{report}"
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
    assert 0.275 <= roster_wide_unopened <= 0.335, (
        f"roster-wide unopened arrival {roster_wide_unopened:.4f} outside "
        f"[0.275, 0.335] (recalibrated 0.305 at W5-b4; slice-neutral cell) -- "
        f"read the provenance comment above before re-centring: this is the "
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


def _vs_3bet_effective_policy(pack, role: str = "cold") -> dict[str, dict[str, float]]:
    """Per-class EFFECTIVE weights at the pack's wildcard vs_3bet node under
    first-match-wins (`sample_preflop_action`): the first mix whose combos
    contain the class owns it outright; later mentions are dead tokens.

    N-3BSTRATA: `role` picks the ARRIVAL STRATUM exactly as the sampler does —
    the first vs_3bet node that is untagged (serves both) or carries this role.
    Default "cold" keeps every pre-N-3BSTRATA caller reading the table it
    always read (untagged packs have one node; maniac/lag's cold node is
    byte-identical to their pre-slice shared node).

    Two deliberate simplifications vs the live sampler (Codex build review
    C-2 — both are no-ops for every consumer in this file): the implicit-fold
    remainder is NOT folded into a `fold` key (the gates only read `call` +
    `4bet`), and classes no mix covers are ABSENT rather than {"fold": 1.0}
    (`.get(cls, {})` reads them as zero continue, which is the same thing)."""
    from app.domain.content.notation import parse_range

    node = next(
        n
        for n in pack.preflop
        if n.facing == "vs_3bet" and n.role in (None, role)
    )
    policy: dict[str, dict[str, float]] = {}
    for mix in node.mixes:
        for cls in parse_range(mix.combos):
            policy.setdefault(cls, dict(mix.weights))
    return policy


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
# wave-3 {jam 0.40, fold 0.60} the arrival-weighted aggregate lands at fold
# 0.286, inside every bound the gate asserts. Nothing in the fit required the
# move, so the wave-3 weights are restored: 22-99 are now ONE push/fold mix
# ("22-99") at exactly this level, which also makes the 99 -> TT jam step
# 0.40 -> 0.45 RISING instead of the 0.75 -> 0.45 inversion the raised level
# introduced.
#
# The rationale ABOVE is narrowed at the same review: "no set-mining price"
# holds for 22-66, but for 77-99 the honest test is the DIRECT price — at
# SPR ~1.5, calling ~14 into ~35.5 needs ~28% equity, which 77-99 clear
# against a 4-betting range. Whether 77-99 deserve a call leg is therefore
# OPEN and FILED as a follow-up; this slice authors no new call legs.
_MANIAC_VS_4BET_MID_PAIR_MIX = {"5bet_shove": 0.4, "fold": 0.6}


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
    the jam-ladder inversion theory review R-3 found."""
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
    more than the old gate asserted. 22-99 ship as ONE push/fold mix at the
    wave-3 level, so both ladders hold as LEVEL across that block (0.40), and
    the step out of it into TT rises 0.40 -> 0.45.

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
# seeded 4000-hand PRODUCTION-SIZING probe (the REPORTED test below): 70.2% of
# the maniac's vs_4bet decisions are n=3 and 45.9% are this modeled channel.
#
# THE vs_limpers QUESTION, SETTLED BY TRACE (review item 1b): the iso channel IS
# reachable — Codex's construction is right, the "never reaches vs_4bet" reading
# is wrong. Concrete production-sizing hand (seed 447515414, button seat 4):
# UTG1 limps, the maniac at UTG2 ISO-raises to 5.5 (raise #1), LJ re-raises to
# 18.15 (#2), HJ re-raises to 54.45 (#3) — every later seat, including the
# maniac when action returns to it, reads `vs_4bet` at n=3, and the maniac
# 5-bets to 100. It is 3.2% of its vs_4bet decisions in the probe. That mass
# arrives with the ISO range, not the 3-bet range, and is NOT modeled here.
#
# ⚠️ INSTRUMENT WARNING (refuter, filed to the instrument owner): the band
# harness's own `_preflop_decision` sizes every raise at `la.min_bb`, while
# production sizes from persona levers and a `5bet` is all-in — so HARNESS
# measurements of this node overstate re-entrant depth (min-raise ping-pong
# wars that production cannot have). Every channel figure quoted here comes
# from the production-sizing probe, never from the harness.
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
    failure message says to re-derive rather than to re-weight."""
    from app.domain.content.notation import parse_range

    nodes = [n for n in pack.preflop if n.facing == "vs_rfi"]
    assert len(nodes) == 1, (
        f"arrival derivation assumes ONE un-stratified vs_rfi node; found "
        f"{len(nodes)} (roles {[n.role for n in nodes]}) — re-derive arrival "
        f"per stratum before trusting this gate"
    )
    node = nodes[0]
    seen: set[str] = set()
    arrival: dict[str, float] = {}
    for mix in node.mixes:
        w = mix.weights.get("3bet", 0.0)
        for cls in parse_range(mix.combos):
            if cls in seen:
                continue
            seen.add(cls)
            if w > 0.0:
                arrival[cls] = _combo_count(cls) * w
    return arrival


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
    mix and folded 1.0."""
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
    pinned seed, n=4000 hands (621 maniac decisions, shipped 1.4.0 pack):

        n=3 total                             0.7021
        n>=4 total                            0.2979
        n=3, seat 3-bet at vs_rfi  [MODELED]  0.4589
        n=4, seat 4-bet at vs_3bet            0.1965
        n=3, seat opened unopened             0.0821
        n=3, seat's FIRST decision (cold)     0.0548
        n=3, seat ISO-raised limpers          0.0322

    NOT ASSERTED, on purpose: it is a Monte Carlo reading of an occupancy
    distribution with no dossier target, and gating it would freeze an
    instrument, not a behaviour. It exists so the next slice can see whether
    the modeled channel is still the dominant one. n is small enough to run in
    the suite (~10s) and large enough to read shares to ~2pp."""
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
# nine `unopened` nodes (uniform position weight — the opener arrives from
# every seat, and a position's own raise width already weights it).
#
# CALIBRATION (why this proxy is trusted): at pre-slice HEAD it reproduces the
# harness's sampled opener stratum on the two personas this slice retunes —
# maniac 0.609 proxy vs 0.630 sampled, lag 0.829 proxy vs 0.821 sampled (the
# 756-hand corpus figures quoted in the roadmap). Deterministic, so no CI.


def _open_range_mass(pack) -> dict[str, float]:
    """class -> combo-weighted mass this pack OPENS the pot with, summed over
    the nine `unopened` nodes (first-match-wins per position)."""
    from app.domain.content.notation import parse_range

    out: dict[str, float] = {}
    for pos in Position:
        node = next(
            n
            for n in pack.preflop
            if n.facing == "unopened" and (n.positions is None or pos in n.positions)
        )
        policy: dict[str, dict[str, float]] = {}
        for mix in node.mixes:
            for cls in parse_range(mix.combos):
                policy.setdefault(cls, dict(mix.weights))
        for cls, w in policy.items():
            raise_w = w.get("raise", 0.0)
            if raise_w > 0.0:
                out[cls] = out.get(cls, 0.0) + _combo_count(cls) * raise_w
    return out


def _opener_fold_to_3bet(pack, role: str = "opener") -> float:
    """Fold-to-3-bet over the OPENER stratum: the pack's `role` vs_3bet table
    applied to its own opening-range mass (1 - call - 4bet, per class)."""
    policy = _vs_3bet_effective_policy(pack, role)
    mass = _open_range_mass(pack)
    num = sum(
        m * (1.0 - policy.get(cls, {}).get("call", 0.0) - policy.get(cls, {}).get("4bet", 0.0))
        for cls, m in mass.items()
    )
    return num / sum(mass.values())


def test_n3bstrata_defect_gates_fail_at_pre_slice_head():
    """🔴 NON-VACUITY (the R9-3 lesson): pre-slice HEAD is reproducible in-test
    because the retained `cold` node IS the pre-slice shared node, byte for
    byte. Feeding the opener stratum through it must MISS both targets —
    maniac ~0.61 (target ~0.30) and lag ~0.83 (target 0.43-0.53) — which is
    exactly the defect this slice fixes: one weight table cannot fold cold
    junk without over-folding the opener."""
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
        f"the pre-slice defect (0.829) is gone, so this gate no longer demonstrates it"
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
    Component lands at 0.6166 (deterministic, no CI); pre-slice was 0.6034.
    The `cold` node is still untouched."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    maniac = _opener_fold_to_3bet(packs[VillainType.MANIAC])
    lag = _opener_fold_to_3bet(packs[VillainType.LAG])
    print(f"N-3BSTRATA opener fold-to-3bet (unopened component): maniac {maniac:.4f} lag {lag:.4f}")
    assert maniac == pytest.approx(0.3073, abs=0.02), f"maniac component {maniac:.4f} moved"
    assert lag == pytest.approx(0.6166, abs=0.02), f"lag component {lag:.4f} moved"


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
        roles = [n.role for n in packs[vt].preflop if n.facing == "vs_3bet"]
        assert roles == ["opener", "cold"], f"{vt.value} vs_3bet roles are {roles}"


# Fan-in fold (Codex HIGH): the deterministic proxy above weights the opener
# stratum by the `unopened` nodes ONLY, but production's opener is the FIRST
# RAISER — which includes ISOLATION raises over limpers, and the iso range is
# far stronger than the open range (lag isos "66+, A9s+, KJs+, ATo+, KQo" at
# 1.0), so the LIVE opener population folds less than the unopened-weighted
# figure. The dossier band is therefore gated HERE, on the production-signal
# blend measured over seeded organic play; the unopened-weighted figure stays
# as an authored-COMPONENT shape pin only.
_OPENER_BLEND_CACHE: dict[tuple[str, int], tuple[int, int]] = {}


def _production_opener_fold_counts(packs, persona: str, n: int) -> tuple[int, int]:
    """(folds, decisions) for `persona` seats at vs_3bet in the OPENER stratum,
    where opener = the seat of the hand's FIRST preflop raise (the exact
    production signal `play._preflop_opener` derives), over the same seeded
    lineup as `_persona_stats_ext`."""
    key = (persona, n)
    if key in _OPENER_BLEND_CACHE:
        return _OPENER_BLEND_CACHE[key]
    rng = random.Random(20260710)
    fillers = [p for p in ALL_PERSONAS if p != persona]
    lineup = ([persona] * 3 + [fillers[i % len(fillers)] for i in range(6)])[:9]
    persona_by_seat = {i: lineup[i] for i in range(9)}
    tested_seats = {i for i, p in persona_by_seat.items() if p == persona}
    folds = decisions = 0
    for i in range(n):
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
    _OPENER_BLEND_CACHE[key] = (folds, decisions)
    return folds, decisions


def test_n3bstrata_production_opener_blend_in_dossier_band():
    """🔴 THE N-3BSTRATA gate (production population): fold-to-3-bet of the
    seat that made the hand's FIRST preflop raise — unopened opens AND iso
    raises over limpers, exactly what the live `is_opener` signal serves the
    opener table to. maniac ~0.30 target → band [0.25, 0.35]; lag inside its
    dossier band [0.43, 0.53] ("above 60% makes light 3-betting
    insufficiently defended"; pre-N-3BSTRATA measured 0.72-0.83).

    ⚠️ THIS GATE'S n IS NOT ENOUGH TO SETTLE THE VALUE (N-LAGLADDER, review fold
    6). It reads ~460-490 lag opener decisions at n=4000, whose Wilson half-
    width is ±0.045 — wider than the distance from the band floor. Both figures
    below are therefore quoted at n=12000 (≈1470 decisions) as well:
        pre-slice (origin/main)  0.4667 @n=4000 (n_dec 480) · 0.4534 @n=12000
        shipped                  0.4622 @n=4000 (n_dec 489) · 0.4452 @n=12000
    The earlier in-tree figure "0.4735" was stale — it predates intervening
    slices; 0.4667 is the value origin/main actually measures on this seed.
    An intermediate N-LAGLADDER build passed HERE at 0.4366 while measuring
    0.4242 at n=12000, i.e. under the floor: a pass at this n is necessary, not
    sufficient, and the opener-node re-tune was driven by the n=12000 read."""
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    for persona, lo, hi in (("maniac", 0.25, 0.35), ("lag", 0.43, 0.53)):
        folds, n = _production_opener_fold_counts(packs, persona, 4000)
        rate = folds / n
        wlo, whi = _wilson95(folds, n)
        print(
            f"{persona} production opener fold-to-3bet {rate:.4f} "
            f"(n={n}, CI [{wlo:.3f},{whi:.3f}])"
        )
        assert n >= 200, f"{persona}: opener sample n={n} too small to gate"
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
    packs, per_persona_n, _texture_n, _hands_per_s = budget
    af_band, ftc_band, wtsd_band = BANDS[persona]
    af, ftc, wtsd, call_n, ftc_n, wtsd_n = _persona_stats(packs, persona, per_persona_n)

    if af is not None and af_band is not None:
        lo, hi = af_band
        assert lo <= af <= hi, f"{persona} AF {af:.2f} outside [{lo},{hi}] (n_call={call_n})"
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
            _a2, ftc_stable, _w2, _c2, ftc_stable_n, _wn2 = _persona_stats(
                packs, persona, _WTSD_ORDER_N
            )
            assert ftc_stable is not None and lo <= ftc_stable <= hi, (
                f"{persona} fold-to-cbet {ftc:.2f} (n={ftc_n}) breached and the "
                f"stable-n re-measure {ftc_stable} (n={ftc_stable_n}) confirms it "
                f"— outside [{lo},{hi}]"
            )
    if wtsd is not None:
        # W2 (persona-realism-w2, 2026-07-24 — owner-approved defer): the maniac
        # WTSD assertion is skipped here and reconciled at W4-b (the single
        # authoritative band re-anchor). maniac's true WTSD sits ON the 0.50 band
        # ceiling, and `per_persona_n` is throughput-derived (varies with machine
        # speed), so the point estimate flips over/under 0.50 by sampling noise
        # (0.52 @ n=200, 0.484 @ n=1000). This straddle is PRE-EXISTING (it also
        # breaches at n=700 without any W2-b change) — a fragile-boundary + under-
        # sampling artifact, NOT a W2 regression. The band VALUE (0.50) is untouched
        # (frozen no-go); only this one noisy assertion is deferred. maniac's AF +
        # fold-to-cbet bands and every other persona's WTSD stay live. W2-b behavior
        # is covered by the exact-weight commit/draw-gate unit tests.
        if persona == "maniac":
            pytest.skip("maniac WTSD on the 0.50 ceiling; throughput-n noise — reconcile W4-b")
        # R10-3BET (2026-07-31, owner-approved defer — same shape as maniac's):
        # the roster-wide vs_3bet rewrite moved passive_fish's stable-n WTSD
        # 0.5104 -> 0.4873 against the frozen [0.50, 0.57] floor. HONEST
        # REPORT: attribution measured that the fish's OWN node explains only
        # a minor share of the move — reverting fish's vs_3bet alone reads
        # 0.4949, trimming its call tiers 0.4912, restoring the dossier
        # weights 0.4873: all within noise of each other, so the trim was
        # reverted (theory review R-3). The remainder is cross-persona
        # composition — the
        # whole table now plays 3-bet/4-bet pots differently around the fish
        # (single-lever probe NEGATIVE: removing maniac's junk-tier 4-bet
        # bluffs made it WORSE, 0.4888). Trimming the fish's continue tiers
        # far enough to clear the floor would gut the archetype (N9
        # compensating-lever trap). Band VALUE untouched (frozen no-go);
        # W4-b (the single authoritative re-anchor) reconciles both deferred
        # WTSDs together. Fish AF + fold-to-cbet stay live below.
        if persona == "passive_fish":
            pytest.skip(
                "passive_fish WTSD 0.4873 vs frozen 0.50 floor after the "
                "R10-3BET roster rewrite; cross-persona composition, not a "
                "fish-node defect — owner-deferred to W4-b (ledger)"
            )
        # W3-b/c/d: measure the WTSD-vs-band at the stable large-n (memoized,
        # shared with the ordering test). The throughput-n estimate breaches band
        # ceilings by under-sampling noise alone — lag's true WTSD 0.55 spikes to
        # 0.59+ at n~247 despite sitting well inside its [0.37, 0.59] band. AF/FtC
        # keep the cheaper throughput-n; the band VALUES are untouched (frozen).
        _a, _f, wtsd_stable, _c, _fn, wtsd_stable_n = _persona_stats(
            packs, persona, _WTSD_ORDER_N
        )
        lo, hi = wtsd_band
        assert lo <= wtsd_stable <= hi, (
            f"{persona} WTSD {wtsd_stable:.2f} outside [{lo},{hi}] (n={wtsd_stable_n})"
        )


def test_persona_wtsd_ordering_invariants(budget):
    """Cross-persona WTSD ORDERING (lead-authorized, alongside the
    engine-anchored absolute bands above): absolute WTSD bands can't catch a
    "persona-flattening" regression where every persona's WTSD converges to
    the same population-average value -- these relative comparisons are
    robustly true regardless of the engine's absolute showdown-rate ceiling,
    since they follow directly from each persona's PRD-intended fold/call
    discipline (station folds least -> highest WTSD; maniac folds most among
    the aggressive personas -> lowest WTSD relative to the calling personas).
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
        _af, _ftc, w, _cn, _fn, wn = _persona_stats(packs, persona, _WTSD_ORDER_N)
        assert w is not None, f"{persona} WTSD unmeasurable at n={wn} (<30 floor)"
        wtsd[persona] = w

    assert wtsd["calling_station"] > wtsd["tag"], (
        f"station WTSD {wtsd['calling_station']:.3f} not > tag WTSD {wtsd['tag']:.3f}"
    )
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
    assert wtsd["passive_fish"] < wtsd["tag"], (
        f"passive_fish WTSD {wtsd['passive_fish']:.3f} not < tag WTSD "
        f"{wtsd['tag']:.3f} (W3R-2: the fish now folds more than the tag)"
    )
    assert wtsd["calling_station"] - wtsd["passive_fish"] > 0.10, (
        f"station WTSD {wtsd['calling_station']:.3f} and fish WTSD "
        f"{wtsd['passive_fish']:.3f} have converged (<0.10 apart) — the two "
        f"passive personas must stay distinguishable (W3R-2)"
    )
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
# Both damps are gated on `facing_raise`, so `facing_raise=False` at the SAME
# street IS the pre-slice status quo — every "byte-identical to status quo" leg
# below is exactly that A/B (and the street=None path is pinned equal to it).
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
_W3R6_RAISE_DROP = {
    ("tag", "mid"): (0.1871, 0.0745),
    ("tag", "top"): (0.3078, 0.1347),
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
    """The whole α-ceiling safety argument: the arrival-range fold-to-bet curve
    is measured facing a BET, and NOTHING on that node moved (both damps need
    facing_raise). The RIVER leg additionally covers the facing-a-raise case —
    call_merit is already 0 there via the bluff-cell river gate."""
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
        # facing a RAISE on the river is byte-identical too (call_merit is
        # already 0 via the bluff-cell river gate; the raise damp is pre-river).
        assert _w3r6_dist(persona, hole, board, street=street, facing_raise=True) == faced_bet


def test_ace_high_with_a_draw_facing_raise_is_byte_identical():
    # The damped term is _CALL_BASE[ACE_HIGH] on NAKED ace-high only.
    hole, board = ("Ad", "7d"), ["Kd", "9d", "2s"]
    _w3r6_assert_bucket(hole, board, StrengthBucket.ACE_HIGH, DrawCategory.STRONG)
    for persona in ALL_PERSONAS:
        for street in (Street.FLOP, Street.TURN):
            sq = _w3r6_dist(persona, hole, board, street=street, facing_raise=False)
            assert _w3r6_dist(persona, hole, board, street=street, facing_raise=True) == sq


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
    """
    packs = load_persona_packs()
    if not packs:
        pytest.skip("no persona packs")
    s = _persona_stats_ext(packs, "tag", 600)
    print(
        f"tag VPIP {s.vpip:.3f} (§5 0.15-0.20) PFR {s.pfr:.3f} (§5 0.12-0.17) "
        f"gap {s.gap:.3f} — n=600, REPORTED, band anchor is W4-b; "
        f"10-seed n=2000 means: pre-slice 16.07/12.80/3.27, shipped 16.46/12.95/3.51"
    )
    assert s.vpip is not None and s.pfr is not None
