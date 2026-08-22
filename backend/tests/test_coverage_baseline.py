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

RE-RECORDED for N-DRAWLOOSE (persona-realism, 2026-08-05 — slice-authorized,
final engine tip db1f278): T1 floors the archetype calling dial at 1.0 where
it multiplies the STRONG-draw call bonus, so tightening a persona no longer
makes it fold hands nobody folds — the bots now continue with strong draws
they used to fold, which is a deliberate, authorized behavior change. THIS
ENTRY REPLACES the prior N-DRAWLOOSE entry rather than appending after it:
that entry (1288/335 -> 1233/323) was recorded against an intermediate
engine that adversarial review superseded (R1/R2 rebuilt the STRONG-draw
floor twice more), so 1233/323 never shipped anywhere and never existed
outside this branch. OLD side re-verified directly against the control
worktree at base commit `b0a6a4e` (this slice's only engine file,
`personas_postflop.py`, absent): `_measure()` there reads 1288/335,
matching the FIXTURE ON DISK at that commit exactly — confirming the "old"
side is the true base reading, not carried forward from a stale chain
entry. NEW side measured by `_measure()` at THIS tip: total 1288 -> 1195,
graded 335 -> 329 (ratio 26.01% -> 27.53%).
⚠️ Read the RATIO, not the raw counts: graded falls 335 -> 329 only because
the bots reach FEWER hero decision points at all (1288 -> 1195); the share of
what happens that the mapper can grade RISES, 26.01% -> 27.53%. CUMULATIVE vs
the immutable persona-realism-start snapshot (349/1233 = 28.30%): 329/1195 =
27.53%, -0.77pp — inside the long-adjudicated mapper-track dip that `T-cover`
owns, and the strongest recovery of that dip recorded on this fixture so far.
ATTRIBUTION PROVEN BOTH WAYS: the control worktree at base `b0a6a4e` measures
1288/335 and passes against ITS OWN on-disk fixture (also 1288/335)
unmodified; this tip measures 1195/329. The slice is the sole cause.
Seeded-fixture re-record; population bands stay frozen to W4-b.

RE-RECORDED for the de-robotization slice (2026-08-15, slice-authorized):
total 1195 -> 1274, graded 329 -> 314, ratio 27.53% -> 24.65%. (Recorded
once for the whole slice; the seat split and the edge softening each shift
the stream, and the figures below are measured at the slice tip.) The six packs
now answer `vs_rfi`, `vs_limpers` and `vs_3bet` per seat, so villains fold
less and the hand stream drifts.

⚠️ THIS FIXTURE CANNOT RESOLVE THE QUESTION IT IS BEING ASKED, and the
-3.05pp above is largely an artifact of its size. Two measurements, both made
for this re-record:

  By street, at this seed: preflop total 509 -> 510 with graded 306 -> 295;
  POSTFLOP total 686 -> 789 with graded 23 -> 23. Nearly the whole ratio drop
  is the denominator — hero reaches 103 more postflop decisions because
  villains continue more often, and postflop grading coverage is about 7%,
  which is the `T-cover` defect this repo already tracks. The mapper lost
  almost nothing; it was handed far more of the street it cannot grade.

  At 2,000 hands across three seeds (20260718/19/20) the same old-vs-new
  comparison reads: overall 26.75->25.75, 21.67->20.59, 25.84->25.72 (mean
  -0.73pp); preflop 59.45->59.61, 49.51->46.84, 62.59->62.35 (mean -0.91pp,
  bracketing zero). The preflop ratio's spread ACROSS SEEDS is about 14pp —
  an order of magnitude larger than any effect being read off one 400-hand
  seed.

The honest reading: overall coverage is down slightly and the postflop
denominator is why; preflop coverage is flat within noise. This fixture is
kept because it is a reliable STREAM tripwire, which is a different and
useful thing. Anyone using it to accept or reject a bot change should
re-measure at a larger n across several seeds first.

RE-RECORDED for the de-robotization slice's T5 (2026-08-16, slice-authorized):
postflop bet sizes re-weighted across all six packs. The bots bet different
amounts, so hands end differently and the stream displaces:
1289/331 -> 1294/339 (25.68% -> 26.20%). CUMULATIVE vs the immutable
persona-realism-start snapshot (349/1233 = 28.3%): 339/1294 = 26.20%, -2.10pp
-- inside the adjudicated mapper-track dip that T-cover owns, and a recovery
from T3/T4's -2.62pp. Graded ratchet moves UP 331 -> 339.

T5's SECOND review round (2026-08-17) changed the packs again -- the tag and lag
gain a third-pot bet on wet flops, lag loses a wet-flop overbet -- and this
fixture's counts did NOT move at this seed, which is itself worth knowing: 400
hands at one seed cannot see a change confined to a node that carries about 5%
of postflop aggression.

Three things about this entry that the two T5 review rounds forced, and that the
next mover should copy rather than rediscover:

(1) THIS FIXTURE IS ONE SEED AT 400 HANDS AND IT DISAGREED IN SIGN WITH THE
    REAL MEASUREMENT. Measured properly with `measure_split` below at 2,000
    hands across SIX seeds (20260718-20260723), the slice as a whole reads
    preflop 0.569755 -> 0.571013, postflop 0.032769 -> 0.032944, overall
    0.250770 -> 0.251215. Coverage did not measurably change: five readings
    across the slice gave +0.52pp, -0.34pp, +0.02pp, -0.12pp and +0.04pp, and
    the per-seed overall ratios at the tip span 0.203 to 0.279 -- a spread
    nearly two hundred times the last difference claimed.
(2) DO NOT USE "BOTH COMPONENTS MOVED THE SAME WAY" AS EVIDENCE. An earlier
    version of this docstring did, to prefer a six-seed reading over a
    three-seed one. This slice produced the counterexample at the pack values
    the second review round first tried: preflop rose to 0.570682 and postflop
    to 0.033492 while the overall ratio FELL to 0.249577. Postflop decisions
    grade at about 3% and preflop ones at about 57%, so moving decisions toward
    the postflop streets lowers the overall ratio while improving both halves
    of it -- it is a ratio over a different denominator, not an average of the
    two, so the components agreeing proves nothing.
(3) The chain entry itself was MISSING from the first T5 commit -- the sixth
    occurrence of the lost-record pattern this file already logs. It was caught
    by review rather than by anything automated. If you are re-recording the
    JSON, you are also editing this docstring.

RE-RECORDED for T2b (2026-08-17, slice-authorized): preflop raise sizes are now
drawn from a mix, keyed by seat for the three regulars. Read the paired
measurement below rather than this line; point (1) above is exactly about that.

(4) THIS SLICE'S BEFORE/AFTER ARMS MUST BE PAIRED, AND T2B IS THE FIRST CHANGE
    FOR WHICH THAT MATTERS. `measure_split` deals from the same `Random` it
    hands the bots, and T2b adds one `rng.choices` call per preflop raise, so a
    two-checkout comparison re-randomises every later deal — the arms are not
    playing the same hands at all. The fix is a control that consumes the
    IDENTICAL rng: degenerate one-key mixes at the pre-T2b scalars, which draw
    once and always return the old size. Paired, six seeds x 2,000 hands:

        preflop   0.57397 -> 0.57448   (+0.05pp)
        postflop  0.03515 -> 0.03458   (-0.06pp)
        overall   0.25387 -> 0.25125   (-0.26pp)

    Both components are flat to within a tenth of a point. The overall ratio
    moves only because the street MIX moved, which is point (2) above: hero
    postflop decisions rose 1.5% (21,624 -> 21,952) against a flat preflop
    count, and postflop grades at about 3% against preflop's 57%.

WHAT MOVED, MEASURED RATHER THAN ASSUMED. The extra postflop decisions are not
extra players: seats per flop FELL slightly (2.0241 -> 2.0185). Hands go
FURTHER instead.

AN EARLIER VERSION OF THIS ENTRY GAVE THE WRONG MECHANISM, and it is worth
naming because it was superficially plausible: "a cheaper open is called by
more seats, so more pots go multiway". That cannot happen. `sample_preflop_action`
takes no size argument and `play._preflop_facing` keys on the raise COUNT, so no
bot's calling frequency reads a bb amount -- villain preflop defence is
size-blind by construction. The measured seats-per-flop change is in the
opposite direction anyway. The route that IS open to preflop sizing is the pot:
smaller opens mean smaller pots, and `personas_postflop` (~1110, ~1123) uses
`stack_bb / pot_bb <= pf.spr_commit` for its commitment ramp, so a higher SPR
commits less often and leaves more streets to play.

That is a genuine tension with spec 7.1, which reads the ratio and forbids
reducing it. The ratio cannot tell "grading broke" apart from "hands went
further", and this ticket produced the second. SPEC 7.1 IS THEREFORE NOT MET
AND IS NOT CLAIMED TO BE; it is filed for the owner. Choosing a different
acceptance metric is a spec decision, and shrinking the change until the ratio
held would be fitting values to a gate -- the defect both T5 review rounds
caught. What the values WERE shrunk for is a different reason, recorded in the
ledger: the 3-bet mixes were narrowed because they pushed the lag's showdown
rate out of a frozen band, and that reduction happens to shrink this delta too.

At this one seed the fixture reads 339/1294 -> 335/1227. Cumulative against the
immutable `coverage_baseline.persona-realism-start.json` (349/1233 = 28.30%),
which every prior entry states and the first draft of this one omitted:
335/1227 = 27.30%, -1.00pp, inside the adjudicated `T-cover` mapper dip and a
recovery on T5's -2.10pp.

RE-RECORDED for T1 (improvement slice 2, 2026-08-18, slice-authorized): the
graded RATIO IMPROVED and only the `total` equality leg moved. Graded decisions
went 335 -> 341 against a total of 1,227 -> 1,236, i.e. 27.30% -> 27.59%, so
the invariant every prior entry in this chain names as the real one -- the
ratio, not the raw total -- held and gained 0.29pp. Cumulative against the
immutable `coverage_baseline.persona-realism-start.json` (349/1233 = 28.30%):
341/1236 = 27.59%, -0.71pp, a further recovery on T2b.

RE-RECORDED for T3 (improvement slice 2, 2026-08-19, slice-authorized). T3's
mechanism: naked ace-high may call a river bet again, at a damped weight. The
river call zero used to be written on `bluff_cell`, which bundles ACE_HIGH with
AIR, and it is now written on the made-hand bucket so that it refuses AIR only;
ace-high's restored call merit is multiplied by
`personas_postflop._ACE_HIGH_RIVER_CALL_DAMP` = 0.06. Minimum-defence arithmetic
over the measured river price distribution derives about 0.46; 0.06 is a round
value inside the range two frozen went-to-showdown bands admit with margin, and
the owner ruled that conflict in the bands' favour on 2026-08-19. Hands that used to end on a
river fold now sometimes reach showdown, so the hero meets a different number of
decision points in the same 400 seeded hands.

Graded decisions went 341 -> 318 against a total of 1,236 -> 1,228, i.e.
27.59% -> 25.90%. Cumulative against the immutable
`coverage_baseline.persona-realism-start.json` (349/1233 = 28.30%):
318/1228 = 25.90%, -2.40pp.

IT IS NOT THE LARGEST DIP THIS CHAIN HAS RECORDED. An earlier draft of this
entry said it was; the WAVE 3 COMBINED entry above reads 322/1314 = 24.5%,
-3.8pp, and says so of itself. -2.40pp is the third-deepest, behind wave 3 and
level with T5's -2.10pp. The claim is corrected rather than quietly dropped
because a superlative is exactly the kind of thing a reader trusts without
checking.

The reading is stream displacement, and this file already documents the pattern.
Three things support it. The wave-3 entry above records the same NON-MONOTONE
shape and names it -- lane B alone read 27.8%, lane A alone 26.4%, and the
combined tip 24.5%, "worse than either, i.e. mostly cross-lane rng displacement,
not a monotone behavioral trend". This ticket reproduces that shape within one
lever: it measured 351 graded at a river call damp of 0.45 and 318 at 0.06, a
10% swing in the numerator from a constant that only changes how often one
bucket calls one street, and 0.06 is the SMALLER behavioural change of the two.
And two independent reviewers re-measured the ratio at review, one of them at
36,000 decisions, where it is flat -- the dip is a 400-hand artifact, not a
coverage regression.

The class is the one every entry since W3-b/c/d has carried: mapper coverage is
orthogonal to persona realism, the mapper is untouched, and more realistic
villains route the hero into a different mix of spots. Treat the LEVEL as noisy
at this n and the TREND as the thing to watch.

NO NEW RANDOM DRAW WAS ADDED AND NONE PRECEDES THE ACTION DRAW, which is slice
1's actual rule. The number of draws is NOT claimed invariant: a fold flipping
to a call changes which later decisions happen at all, so stream displacement is
expected here rather than ruled out.

WHY A BOT CHANGE MOVES A LEG WHOSE STATED PURPOSE IS CATCHING A BROKEN HARNESS.
The `total` assertion exists to prove this file stayed engine-only -- that the
hero script never started reading mapper or display output, which would let the
measurement feed itself. It cannot distinguish that failure from an authorised
change in how the BOTS play, because the villain seats run real persona packs
and the hero plays until the hand ends: change what a bot does with naked
ace-high on a multiway flop and some hands end sooner, others go further, and
the number of hero decision points in 400 hands moves. Every one of the eight
entries above this one moved it for the same reason. The leg is still worth
keeping and is not being softened -- it just needs a re-record, with a written
mechanism, on any slice that intentionally changes bot play.

The mechanism at THIS tip is T3's, stated in the T3 entry above: naked ace-high
may call a river bet again, at a damped weight. The paragraph that stood here
described T1's mechanism instead -- naked ace-high ceasing to float flop and turn
bets multiway -- and was left standing when the T3 values were recorded. It is
replaced rather than appended to, because it attributed the current numbers to a
change that is not the current change. T1's own entry retains its mechanism.

NO NEW RANDOM DRAW WAS ADDED AND NONE PRECEDES THE ACTION DRAW, which is slice
1's actual rule and is what would otherwise shift every seeded test in the
repository. THE NUMBER OF DRAWS IS NOT INVARIANT, THOUGH, and an earlier version
of this entry wrongly said it was. A damp only reweights an existing merit, but
reweighting changes which action is drawn, and what runs after that action is
conditional on it -- flip a river FOLD to a CALL and the hand continues to
showdown, generating decisions that did not previously exist. So stream
displacement is EXPECTED here rather than ruled out, and point (4)'s pairing
caveat applies in principle, which is why the movement above is re-recorded
rather than explained away.

Spec 7.1 at this tip: the ratio FELL, 27.59% -> 25.90%. An earlier version of
this paragraph said it rose, which was true of T1 and is not true of T3. The
fall is the third-deepest in the chain, is attributed to displacement on the
evidence set out in the T3 entry above, and is reported rather than claimed as
compliance.
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


def measure_split(seed: int = SEED, hands: int = HANDS) -> dict:
    """The same sweep as `_measure`, at an arbitrary seed and hand count, split
    by street. Committed so a reviewer can reproduce a coverage claim instead of
    taking one on trust — review of T5 found that the slice's headline coverage
    number came from a bespoke uncommitted script.

    The split matters: preflop and postflop are graded at very different rates
    (about 0.57 against about 0.03), so a change that merely moves decisions
    between streets moves the overall ratio without either component changing.

    Reproduce T5's reading, from backend/, with PYTHONPATH=. set. All SIX
    seeds, named in full — an earlier version of this example ran three of
    them, which regenerated the reading the docstring above declares
    superseded:

        from tests.test_coverage_baseline import measure_split
        tot = {"preflop": 0, "postflop": 0}; gra = dict(tot)
        for s in (20260718, 20260719, 20260720, 20260721, 20260722, 20260723):
            r = measure_split(s, 2000)
            for k in tot: tot[k] += r["total"][k]; gra[k] += r["graded"][k]
        for k in tot: print(k, gra[k] / tot[k])

    That gives the AFTER arm only. This helper reads whatever packs are on
    disk, so the BEFORE arm needs a checkout of the base commit — there is no
    pack-set parameter and adding one would mean threading a content directory
    through `load_persona_packs` for a test-only convenience. Worth knowing
    before you quote a delta from it.
    """
    rng = random.Random(seed)
    packs = load_persona_packs()
    lineup_types = assign_lineup(rng)
    lineup = {s: packs[t.value] for s, t in lineup_types.items() if s != HERO_SEAT}
    hero_rng = random.Random(seed + 1)
    total = {"preflop": 0, "postflop": 0}
    graded = {"preflop": 0, "postflop": 0}
    for hand_no in range(hands):
        dealt = deal_hand(rng)
        state = start_hand(dealt, button_seat=hand_no % 9, stacks_bb=[100.0] * 9)
        for _ in range(60):
            state, _ev = advance_to_hero(state, lineup, HERO_SEAT, rng)
            if state.hand_over or state.to_act_seat != HERO_SEAT:
                break
            key = "preflop" if state.street is Street.PREFLOP else "postflop"
            total[key] += 1
            if map_decision_point(state, HERO_SEAT) is not None:
                graded[key] += 1
            state = apply(state, _hero_decision(state, hero_rng))
    return {"seed": seed, "hands": hands, "total": total, "graded": graded}


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
