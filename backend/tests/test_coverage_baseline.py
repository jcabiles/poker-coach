"""N5 — fixed-seed graded-decision coverage baseline (the measuring stick).

Runs a fully deterministic simulation (fixed deal seed, fixed persona lineup,
scripted hero whose choices depend ONLY on the engine's legal actions + a
seeded rng — never on mapper/display output) and measures what share of hero
decision points `map_decision_point` can grade. Because nothing in N5 touches
the engine or the bots, the played hand stream is byte-identical before and
after mapper/content changes — so `graded` may only go UP against the
recorded baseline while `total` stays fixed.

Baseline recorded in tests/data/coverage_baseline.json (pre-N5 movers, i.e.
main @ N4b). Re-record deliberately (see `_measure` docstring) only when the
slice notes say so — never to make a regression pass.

RE-RECORDED for P1 (persona-realism-p1, 2026-07-23 — slice-authorized): the
villain seats play real persona packs, so P1's pack fixes (B1/M3/N3, threebet
3.3) and A1's air-call drop deliberately change bot behavior → the played
hand stream drifts → total 1233 → 1246, graded 349 → 366. Graded coverage
HELD (ratio 28.3% → 29.4%) vs the immutable
coverage_baseline.persona-realism-start.json snapshot.

RE-RECORDED for P2a (persona-realism-p2a Q3, 2026-07-23 — slice-authorized,
operational; the ONE authoritative combined re-anchor is W5): play.py now
passes `street` into the postflop sampler, so river polarization (one-pair
class never raises the river, air never calls) changes villain river play →
the hand stream drifts → total 1246 → 1255, graded 366 → 368. Cumulative vs
the immutable persona-realism-start snapshot: total 1233 → 1255, graded
349 → 368 (ratio 28.3% → 29.3% — held).

RE-RECORDED for W1-a (persona-realism-w1, 2026-07-24 — slice-authorized): the
middle-pair river BET floor (F6) changes villain river play → the seeded hand
stream drifts (shorter checked-down rivers + rng displacement) → total
1255 → 1196, graded 368 → 363. Graded coverage RATIO held/improved
(29.3% → 30.4%) — the invariant is the ratio, not the raw total, across an
authorized bot-behavior change. This is a seeded-fixture re-record, NOT the
population WTSD/AF tolerance-band re-anchor (frozen to W4-b).

RE-RECORDED for W1-c (persona-realism-w1, 2026-07-24 — slice-authorized): the
multiway made-value BET damp (F13) changes villain postflop betting → the
stream drifts again → total 1196 → 1259, graded 363 → 371 (ratio 30.4% → 29.5%,
still well above the immutable persona-realism-start floor of 28.3% — held).
W1-b required no coverage re-record (its faced_frac fix hit no divergent spot in
this deterministic sweep).

RE-RECORDED for W2-a (persona-realism-w2, 2026-07-24 — slice-authorized): the
calling_station (size_elasticity 0.0) and passive_fish (size_elasticity 1.3) opt
into the elasticity split, changing their faced-size fold decisions in the seeded
lineup → the shared-rng hand stream drifts → total 1259 → 1270, graded 371 → 365
(ratio 29.5% → 28.7%, still above the immutable persona-realism-start floor of
28.3% — held). Seeded-fixture re-record; population bands stay frozen to W4-b.

RE-RECORDED for W2-b (persona-realism-w2, 2026-07-24 — slice-authorized): the
commit/draw EV gate (STRONG draw folds to overbets instead of force-jamming; naked
WEAK draw stops stacking off at high commitment) changes villain play → the stream
drifts again → total 1270 → 1227, graded 365 → 363 (ratio 28.7% → 29.6%, held above
the 28.3% floor). Seeded-fixture re-record; population bands stay frozen to W4-b.

RE-RECORDED for W3-b/c/d (persona-realism-w3bcd, 2026-07-24 — slice-authorized): the
position IP/OOP multiplier, the street aggression schedule + busted-river bluff, and
the made-hand texture brakes change villain postflop play across the board → the seeded
stream drifts → total 1227 → 1255, graded 363 → 345. NOTE: graded RATIO dips to 27.5%
(below the 28.3% start-snapshot floor) — this is MAPPER coverage (orthogonal to persona
realism): the more-realistic villains simply visit a different mix of hero spots, and
the mapper (unchanged) grades that mix slightly less. Flagged for the mapper-coverage
track, not a persona-realism regression. Seeded-fixture re-record; bands frozen to W4-b.

RE-RECORDED for W3R-1 (persona-realism-w3r1, 2026-07-24 — slice-authorized): a PURE
preflop-content change (maniac `vs_rfi` 3-tier legit range replaces the any-two
cold-call; maniac + lag SB open-limps deleted; maniac HJ/CO/BTN offsuit-ace opens
trimmed) shifts which hands reach hero, so the seeded stream drifts → total 1255 →
1250, graded 345 → 378 (graded coverage rose). No engine/postflop code changed.
Seeded-fixture re-record; population bands stay frozen to W4-b.

RE-RECORDED for W3R-3 (persona-realism-w3r-3, 2026-07-24 — slice-authorized): the #4
spr_commit ladder (fish 2.0 → 1.4 so it commits LATER than the station's 1.5, maniac
4.0 → 3.3) moves both bots' low-SPR stack-off points, so the played hand stream
drifts (total 1222 → 1264, graded 366 → 362). #12 (tag/nit/lag explicit
`call_looseness` == prior inherited `stickiness`) is byte-identical and contributes
nothing; #5 (the global ACE_HIGH call-base cut) was DROPPED by owner decision, so no
ace-high behavior is in this re-record. Cumulative graded-coverage ratio vs the
IMMUTABLE initiative-start snapshot: 28.6% (362/1264) vs 28.3% (349/1233) — HELD, no
cumulative loss. (Slice-over-slice this dips from W3R-2's 30.0%: the longer stream
(+42 hero decision points) is dominated by MORE ungraded points, an artifact of which
spots the mapper covers, orthogonal to persona realism — same class as the W3-b/c/d
dip.) Seeded-fixture re-record; population bands stay frozen to W4-b.

RE-RECORDED for W3R-2 (persona-realism-w3r2, 2026-07-24 — slice-authorized): a PURE
persona-JSON postflop dial change (passive_fish `call_looseness` 0.42 authored;
calling_station `size_elasticity` 0.0 → 0.55 + `call_looseness` 4.0 authored) makes
those two villains respond to BET SIZE, so hands end differently and the seeded stream
drifts → total 1250 → 1222, graded 378 → 366 (ratio 30.2% → 30.0% — held, and still
well above the immutable persona-realism-start floor of 28.3%). No engine code changed.
Seeded-fixture re-record; population bands stay frozen to W4-b (except the
owner-authorized fish/station WTSD re-anchor in test_personas_postflop.py).

RE-RECORDED for W3R-4 (persona-realism-w3r-4, 2026-07-24 — slice-authorized): the #11
`_CALL_BASE[MIDDLE_PAIR]` 0.60 → 0.52 trim makes every villain call marginally less
with a naked middle pair, so hands end differently and the seeded stream drifts →
total 1264 → 1241, graded 362 → 373. Graded-coverage ratio vs the IMMUTABLE
initiative-start snapshot: 30.1% (373/1241) vs 28.3% (349/1233) — HELD, and up
slice-over-slice from W3R-3's 28.6%. The #7 multiway busted-bluff damp contributes
nothing to this fixture (its river add-on needs a `PostflopContext`, which this
harness never passes). Seeded-fixture re-record; bands stay frozen to W4-b.

RE-RECORDED for W3R-6 (persona-realism-w3r-6, 2026-07-24 — slice-authorized): the two
facing-a-RAISE merit damps (#9 `_ONE_PAIR_RAISE_DAMP` — made MIDDLE/TOP pair stops
re-raising into flop/turn action; #5 `_ACE_HIGH_FLOAT_RAISE_DAMP` — naked ace-high
stops floating a raise) change villain play at every facing-a-raise node, so the seeded
stream drifts → total 1241 → 1290, graded 373 → 354. Isolated: with both damps set to
1.0 the sweep reproduces the pre-slice 1241/373 EXACTLY (default-off byte-identity), and
each damp alone moves it (#9 only: 1232/372; #5 only: 1268/362) — the drift is these two
mechanics, nothing else. Cumulative graded ratio vs the IMMUTABLE persona-realism-start
snapshot: 27.4% (354/1290) vs 28.3% (349/1233) — a DIP, the same class as (and no worse
than) the W3-b/c/d 27.5% dip: MAPPER coverage is orthogonal to persona realism (more
realistic villains visit a different mix of hero spots, and the unchanged mapper grades
that mix slightly less). Flagged for the mapper-coverage track, not a persona-realism
regression. Seeded-fixture re-record; population bands stay frozen to W4-b.

RE-RECORDED for W5-b1 (persona-realism-w5-b1, 2026-07-25 — slice-authorized): the
nit/tag/lag `unopened` ladders were widened to 9-max full-ring widths (authored mean
nit 8.0 → 28.5, tag 16.4 → 34.0, lag 22.6 → 43.2). PURE preflop content — no engine
or postflop code changed — but it changes which hands open, so the seeded stream
drifts → total 1290 → 1215, graded 354 → 336. Graded ratio 27.4% → 27.6% (UP
slice-over-slice). Cumulative vs the IMMUTABLE persona-realism-start snapshot:
27.6% (336/1215) vs 28.3% (349/1233) — still the same pre-existing DIP first flagged
at W3-b/c/d, unchanged in character and no worse: MAPPER coverage is orthogonal to
persona realism (the mapper is untouched; realistic villains simply route hero into a
different mix of spots). Fewer total hero decision points is the expected direction —
wider opens end more hands preflop. Flagged for the mapper-coverage track, not a
persona-realism regression. Seeded-fixture re-record; bands stay frozen to W4-b.

RE-RECORDED for R10-PRE1 (persona-realism-r10-pre1, 2026-07-30 — slice-authorized): the
maniac's premium unopened carve-out ("TT+, AQs+, AKo" → raise 1.0; was raise 0.7-0.85
with explicit fold) stops it folding premiums first-in. PURE preflop content — no engine
code changed — but more pots now open raised, so the seeded stream drifts →
total 1215 → 1176, graded 336 → 329. Graded ratio 27.6% → 28.0% (UP slice-over-slice).
Cumulative vs the IMMUTABLE persona-realism-start snapshot: 28.0% (329/1176) vs 28.3%
(349/1233) — still the same pre-existing mapper-track DIP first flagged at W3-b/c/d,
improved and no worse in character; not a persona-realism regression. Seeded-fixture
re-record; bands stay frozen to W4-b.

RE-RECORDED for R10-PRE2 (persona-realism-r10-pre2, 2026-07-30 — slice-authorized): the
maniac `unopened` ladder widened above the LAG's at every seat (authored seat-avg
first-in raise 51.8%) to fix the R10-1a first-in identity collapse. PURE preflop
content — no engine or mapper code changed — but the maniac now opens roughly twice as
often, so the seeded stream drifts → total 1176 → 1251, graded 329 → 329 (graded count
HELD exactly; more total decision points because more pots see a raise and more seats
act behind it). Graded ratio 28.0% → 26.3% (DOWN slice-over-slice — flagged, not
laundered): the extra decision points are — INFERENTIALLY, pending T-REJECT's
reject-reason distribution — dominated by non-HU-SRP shapes
(maniac-opened multiway / re-raised pots) that the mapper's gates already reject —
the pre-existing mapper-track DIP first flagged at W3-b/c/d, WIDENED here because a
realism fix routes hero into exactly the spot mix `T-cover` exists to make gradable.
Mapper coverage is orthogonal to persona realism; the remedy is the T-cover mapper
work, not narrower villains. Cumulative vs the IMMUTABLE persona-realism-start
snapshot: 26.3% (329/1251) vs 28.3% (349/1233). Seeded-fixture re-record; bands stay
frozen to W4-b.

RE-RECORDED for W5-b4 (persona-realism-w5b4, 2026-07-31 — slice-authorized): the maniac
vs_limpers/vs_rfi repair (positional iso split toward ~60% late; the 73%-flat-call tier
converted to a 3bet/call/fold split; any-two light 3bet-or-fold catch-all; modest fringe
over-limp). PURE preflop content — no engine or mapper code changed — the seeded stream
drifts → total 1251 → 1219, graded 329 → 330. Graded ratio 26.3% → 27.1% (UP
slice-over-slice — the maniac 3-betting/isolating ends more hands preflop, trimming the
ungradable multiway tail R10-PRE2 created). Cumulative vs the IMMUTABLE
persona-realism-start snapshot: 27.1% (330/1219) vs 28.3% (349/1233). Seeded-fixture
re-record; bands stay frozen to W4-b.

RE-RECORDED for RR-HOLES (persona-realism, 2026-07-31 — slice-authorized):
typo-hole + dead-token cleanup adds a few playable combos to station/fish/
tag/lag preflop nodes, displacing the shared stream: 1218/332 → 1237/325
(27.3% → 26.3%). CUMULATIVE vs the immutable persona-realism-start snapshot
(349/1233 = 28.3%): 325/1237 = 26.3%, −2.0pp — adjudicated as a continuation
of the known mapper-track dip (stream displacement; the mapper is orthogonal
and T-cover owns the ratio), NOT silently accepted. Seeded-fixture re-record;
population bands stay frozen to W4-b.

RE-RECORDED for W5-b3 (persona-realism, 2026-07-31 — slice-authorized): the
nit nine-seat unopened ladder (flat 13.6/29.1 → 7.54-21.42 by seat) changes
which pots exist at all: 1237/325 → 1256/318 (26.3% → 25.3%). CUMULATIVE vs
the immutable persona-realism-start snapshot (349/1233 = 28.3%): 318/1256 =
25.3%, −3.0pp — mapper-track dip continuation (a tighter nit folds more
first-in, so more multiway/limped pots the mapper's gates reject; T-cover
owns the ratio), reported not silent. Seeded-fixture re-record; population
bands stay frozen to W4-b.

RE-RECORDED for R10-TAIL-a1 (persona-realism, 2026-07-31 — slice-authorized):
the piecewise absolute-price tail in `_price_factor` (faced fraction > 1.5×
pot ⇒ factor *= (f/1.5)**2.0) makes every persona fold more vs true overbets,
so overbet pots end earlier and the seeded hand stream displaces: 1256/318 →
1259/324 (25.3% → 25.7%). CUMULATIVE vs the immutable persona-realism-start
snapshot (349/1233 = 28.3%): 324/1259 = 25.7%, −2.6pp — small recovery within
the adjudicated mapper-track dip (T-cover owns the ratio), reported not
silent. Seeded-fixture re-record; population bands stay frozen to W4-b.

RE-RECORDED for N-3BSTRATA (persona-realism, 2026-07-31 — slice-authorized):
the vs_3bet opener/cold arrival split (maniac + lag opener tables continue
far more after opening; lag's dominated-offsuit call mass trimmed at fan-in)
changes how 3-bet pots play out, so hands end differently and the seeded
stream displaces: 1259/324 → 1252/331 (25.7% → 26.4%). CUMULATIVE vs the
immutable persona-realism-start snapshot (349/1233 = 28.3%): 331/1252 =
26.4%, −1.9pp — further recovery within the adjudicated mapper-track dip
(T-cover owns the ratio), reported not silent. Seeded-fixture re-record;
population bands stay frozen to W4-b.
RE-RECORDED for WAVE 3 COMBINED (persona-realism-wave3, 2026-07-31 —
wave-authorized, recorded ONCE on the combined lane-B + lane-A tip): lane B =
T-M2 nit small-pair opens at CO/BTN (raise 0.3 from fold mass) + T-F3 maniac
vs_4bet 99/88/77 {5bet_shove 0.4, fold 0.6}; lane A = N-LAGLADDER lag
offsuit→suited composition swap at constant width + AQo fold→call + opener
vs_3bet call trim. PURE preflop content; the two lanes' stream displacements
COMPOUND: 1252/331 → 1314/322 (26.4% → 24.5%). Intermediate readings for
attribution: lane B alone 1179/328 = 27.8%, lane A alone 1242/328 = 26.4% —
the combined 24.5% is worse than either, i.e. mostly cross-lane rng
displacement, not a monotone behavioral trend. ⚠️ DISCLOSED (refuter L2 +
wave-3 ledger): the graded RATCHET moves DOWN 331 → 322. CUMULATIVE vs the
immutable persona-realism-start snapshot (349/1233 = 28.3%): 322/1314 =
24.5%, −3.8pp — the LARGEST cumulative dip so far, same adjudicated
mapper-track class (T-cover owns the ratio; suited-heavier lag opens + nit
late raises route hero into more non-HU-SRP shapes the mapper rejects),
reported not silent and flagged to the owner in the wave-3 ledger. Seeded-
fixture re-record; population bands stay frozen to W4-b.

RE-RECORDED for WAVE 4 COMBINED (persona-realism-wave4, 2026-08-01 —
wave-authorized, recorded once on the combined lane-C + lane-D tip):
N-M4BET maniac vs_4bet full coverage (the maniac now continues most 4-bet
pots instead of folding 81% of its arriving range) + N-TAGCOMP tag unopened
offsuit→suited swap. PURE preflop content; the stream displaces:
1314/322 → 1269/317 (24.5% → 25.0%). CUMULATIVE vs the immutable
persona-realism-start snapshot (349/1233 = 28.3%): 317/1269 = 25.0%, −3.3pp —
inside the adjudicated mapper-track dip (T-cover owns the ratio), a small
recovery from wave 3's −3.8pp, reported not silent. Graded ratchet 322 → 317
disclosed. Seeded-fixture re-record; population bands stay frozen to W4-b.

RE-RECORDED for N-LAGCOMP2 (persona-realism-wave5, 2026-07-31 —
wave-authorized, single-recorder landing): the lag CO/BTN/SB offsuit→suited
swap at exactly constant width (suited now a class-superset of the tag's at
those seats). PURE preflop content; the stream displaces:
1269/317 → 1275/338 (25.0% → 26.5%). CUMULATIVE vs the immutable
persona-realism-start snapshot (349/1233 = 28.3%): 338/1275 = 26.5%, −1.8pp —
the strongest recovery since the wave-3 −3.8pp low (graded RATCHET moves UP
317 → 338). Same adjudicated mapper-track class (T-cover owns the ratio),
reported not silent. Seeded-fixture re-record; population bands stay frozen
to W4-b.

CHAIN DISCONTINUITY, recorded 2026-08-02 (R9-DEFENCE-a integration — NOT a
re-record, no fixture change): the entry above ends at 1275/338 (26.5%), but
the fixture on disk at `origin/main` 8cc6c38 reads 1224/339 (27.70%). Cause
traced, not guessed: `6e73bbf` (wave-6 lane A, #155 — pack-keyed stats caches
+ production-faithful harness sizing) moved the fixture 1275/338 -> 1224/339
and appended NO entry here. That is the FIFTH occurrence of the lost-record
pattern this initiative has hit (see the four logged in
`test_limper_coverage_belt.py`). Recorded so the next re-pin computes its
"old" side from the FIXTURE, never from the tail of this chain — deriving it
from the prose is precisely how one of these gets lost. The entry below
therefore opens at 1224/339, the on-disk truth.

RE-PINNED for R9-DEFENCE-a (2026-08-02 — slice-authorized, owner-ruled): T2
scales the CALL/RAISE merits by `exp(-lambda_p * line)` at a facing-chips
node when the same seat also bet/raised the previous postflop street
(`line_sensitivity`, seeded per pack), so every villain that opts in folds
more to a sustained barrel — a genuine, authorized behavior change threaded
through `table/play.py`'s production path — and the seeded hand stream
displaces from the recorded fixture: total 1224 -> 1288, graded 339 -> 335
(ratio 27.70% -> 26.01%). ATTRIBUTION PROVEN, not assumed (the #160-entry
method): at this tip, restoring ONLY this slice's changed files
(`personas_postflop.py`, `content/models.py`, `content/personas/*.json`) to
their base `8cc6c38` contents made this test (and the limper belt) pass
again unmodified; putting the current files back reproduced the failure.
The slice is the sole cause. Flagged, not laundered, as a mapper-track dip
**owned by `T-cover`, not this slice**: more realistic villains (folding
more to a sustained barrel) steer hero into a different mix of spots, and
the unchanged mapper grades that mix slightly less. Not unprecedented —
`R10-PRE2` produced an equivalent dip (28.0% -> 26.3%). Seeded-fixture
re-record; population bands stay frozen to W4-b.

RE-RECORDED for N-DRAWLOOSE (persona-realism, 2026-08-04 — slice-authorized,
owner ruling R2): T1 floors the archetype calling dial at 1.0 where it
multiplies the STRONG-draw call bonus, so tightening a persona no longer makes
it fold hands nobody folds — the bots now continue with strong draws they used
to fold, which is a deliberate, authorized behavior change. The seeded stream
therefore displaces: total 1288 -> 1233, graded 335 -> 323 (ratio 26.01% ->
26.20%). OLD side read from the FIXTURE ON DISK (1288/335), never from the tail
of this chain — the discontinuity recorded above is what that rule exists for;
it agrees with the chain here. NEW side measured by `_measure()` at this tip.
This test fails on its FIRST assertion (`hand stream drifted`), not on the
graded ratchet, and 286 of 400 hands change their hero-decision signature
(measured: per-hand (street, action-count, graded) sequences diffed between
`b0a6a4e` and this tip) — so there is no small set of "lost graded decisions"
to track down; this is whole-stream displacement.
⚠️ Read the RATIO, not the raw counts: graded falls 335 -> 323 only because
the bots reach FEWER hero decision points at all (1288 -> 1233); the share of
what happens that the mapper can grade RISES, 26.01% -> 26.20%. CUMULATIVE vs
the immutable persona-realism-start snapshot (349/1233 = 28.3%): 323/1233 =
26.20%, -2.1pp — inside the long-adjudicated mapper-track dip that `T-cover`
owns, and a small recovery slice-over-slice. ATTRIBUTION PROVEN BOTH WAYS, not
assumed: a control worktree at base `b0a6a4e` (this slice's only engine file,
`personas_postflop.py`, reverted with it) measures 1288/335 and passes against
the OLD fixture unmodified; this tip measures 1233/323. The slice is the sole
cause. Seeded-fixture re-record; population bands stay frozen to W4-b.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from app.domain.action import Decision
from app.domain.personas import load_persona_packs
from app.domain.spot import ActionType, Street
from app.domain.table.deck import deal_hand
from app.domain.table.engine import apply, legal_actions, start_hand
from app.domain.table.grade_map import map_decision_point
from app.domain.table.play import advance_to_hero, assign_lineup

HERO_SEAT = 0
SEED = 20260718
HANDS = 400

_FIXTURE = Path(__file__).parent / "data" / "coverage_baseline.json"


def _hero_decision(state, rng: random.Random) -> Decision:
    """Deterministic scripted hero. Reads ONLY engine legal_actions (never
    mapper/display helpers) so the hand stream is invariant to N5 changes.
    Mixed policy to exercise raiser/caller/defender roles."""
    legal = legal_actions(state)
    kinds = {la.action for la in legal}
    roll = rng.random()
    if state.street is Street.PREFLOP:
        raise_la = next((la for la in legal if la.action is ActionType.RAISE), None)
        if raise_la is not None and raise_la.min_bb is not None and roll < 0.25:
            return Decision(action=ActionType.RAISE, size_bb=raise_la.min_bb)
        if ActionType.CALL in kinds and roll < 0.70:
            return Decision(action=ActionType.CALL)
        if ActionType.CHECK in kinds:
            return Decision(action=ActionType.CHECK)
        return Decision(action=ActionType.FOLD)
    bet_la = next((la for la in legal if la.action is ActionType.BET), None)
    if bet_la is not None and bet_la.min_bb is not None and roll < 0.30:
        return Decision(action=ActionType.BET, size_bb=bet_la.min_bb)
    if ActionType.CHECK in kinds:
        return Decision(action=ActionType.CHECK)
    if ActionType.CALL in kinds and roll < 0.80:
        return Decision(action=ActionType.CALL)
    return Decision(action=ActionType.FOLD)


def _measure() -> dict:
    """Deterministic coverage sweep. To re-record the baseline (ONLY when a
    slice deliberately moves it): run
    `python -c "from tests.test_coverage_baseline import _record; _record()"`
    from backend/ and commit the fixture with the slice."""
    rng = random.Random(SEED)
    packs = load_persona_packs()
    lineup_types = assign_lineup(rng)
    lineup = {s: packs[t.value] for s, t in lineup_types.items() if s != HERO_SEAT}
    hero_rng = random.Random(SEED + 1)
    total = 0
    graded = 0
    for hand_no in range(HANDS):
        dealt = deal_hand(rng)
        state = start_hand(dealt, button_seat=hand_no % 9, stacks_bb=[100.0] * 9)
        for _ in range(60):
            state, _ev = advance_to_hero(state, lineup, HERO_SEAT, rng)
            if state.hand_over or state.to_act_seat != HERO_SEAT:
                break
            total += 1
            if map_decision_point(state, HERO_SEAT) is not None:
                graded += 1
            state = apply(state, _hero_decision(state, hero_rng))
    return {"seed": SEED, "hands": HANDS, "total": total, "graded": graded}


def _record() -> None:
    _FIXTURE.parent.mkdir(exist_ok=True)
    _FIXTURE.write_text(json.dumps(_measure(), indent=2) + "\n")


def test_coverage_never_regresses():
    baseline = json.loads(_FIXTURE.read_text())
    current = _measure()
    # Same seed/hands => the played stream is identical; totals must match
    # exactly (a drift means the harness stopped being engine-only).
    assert current["total"] == baseline["total"], "hand stream drifted — harness invariant broken"
    assert current["graded"] >= baseline["graded"], (
        f"graded-decision coverage regressed: {current['graded']} < baseline {baseline['graded']}"
    )
