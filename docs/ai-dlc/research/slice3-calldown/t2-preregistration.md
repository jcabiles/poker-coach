# Pre-registered reduction target — S3-T2 (calling-dial retune)

**Bottom line. Before any pack value was touched, this ticket registers the
minimum went-to-showdown reduction it must deliver on the band harness: at
least 3.5 percentage points for the nit, at least 3.5 for the TAG, and at
least 1.0 for the LAG. Those three numbers are not aimed at the went-to-
showdown bands, which the calling dial cannot reach; they are what the dial's
own measured reach yields when each persona's postflop defence frequency is
brought to the minimum-defence obligation its faced prices imply. The dial
cannot deliver more than that, and this document shows why.**

"Went to showdown" is the share of hands a persona takes to showdown out of
the hands where it saw the flop. The "band harness" is the pinned population
inside the postflop persona test file (`backend/tests/test_personas_postflop.py`)
that the went-to-showdown assertions actually run against; it is the gating
instrument for this slice, and the 50,000-hand export is diagnostic only.
S3-T2 is ticket 2 of improvement slice 3 of the bot-realism flywheel: the
retune of the per-persona `call_looseness` pack values.

Authority for pre-registering after the sweep rather than at spec time:
`docs/ai-dlc/tickets/flywheel-slice3-calldown.md` §S3-T2, and the owner ruling
of 2026-08-22 that the target be a reach-scaled floor derived from S3-T1b's
arithmetic.

## 1. Why the target cannot be "close the gap to the grounded band"

The grounded bands want the nit at 20–28%, the TAG at 25–29% and the LAG at
26–31%. The measured values at this tip are 63.5%, 61.4% and 56.6%. Nothing in
the calling dial's reach closes a thirty-point gap, and three separate
measurements say so.

**First, most of a showdown is not reached through a calling decision.** On the
band harness at its pinned seed and its stable 4,000-hand sample, the share of
each persona's showdown hands in which the persona never faced a wager at all
— every postflop street checked through, or checked to it and it declined to
bet — is 47.7% for the nit, 44.1% for the TAG and 41.6% for the LAG. The
calling dial has no lever on those hands. It cannot make a bot fold a bet
nobody made.

**Second, the hands that do face a wager face very few of them.** Counting
every postflop fold, call or raise as one decision taken while facing a wager,
the mean number of such decisions per showdown hand is 0.81 for the nit, 0.94
for the TAG and 0.95 for the LAG. A dial that cuts continuation by some
fraction at each decision compounds over roughly one decision, not over three
streets.

**Third, part of the calling weight is protected from the dial by design.**
S3-T1b measured this directly: over the same harness population the
price-mandated protected share of a strong draw's call bonus is evaluated 3,849
times, 32.63% of those evaluations clamp at 1.0 (the dial reaches none of that
bonus at all), and the mean share is 0.8289 — so the dial's mean reach into the
strong-draw call bonus is 17.1%. That protection is correct poker and is not
being undone here: a hand whose raw equity already pays for the price it faces
is not folding, whatever archetype holds it.

## 2. What the dial owes, stated as poker rather than as a band

The mandate this ticket tunes against has two parts, and neither mentions the
went-to-showdown bands.

**Part one: no persona may defend more often than the minimum-defence
frequency its faced prices imply.** Minimum defence frequency is the standard
result that a defender facing a bet of `f` times the pot must continue with
`1/(1+f)` of its range to leave a pure bluff exactly break-even; continuing
more often than that is paying for cards the price does not pay for. Measured
over every facing decision on the harness, the mean faced pot fraction is 0.514
for the nit, 0.521 for the TAG and 0.535 for the LAG, so the heads-up
obligations are 0.680, 0.680 and 0.674. The measured aggregate defence
frequencies are 0.683, 0.736 and 0.699. All three sit above the obligation and
the TAG sits far above it.

This is the conservative form of the statement on purpose. Those facing
decisions are not heads-up: the mean number of live opponents is 1.86 for the
nit, 1.85 for the TAG and 1.89 for the LAG, and when several defenders share
one bettor's bluff the individual obligation drops to `1 - (f/(1+f))^(1/k)` for
`k` defenders — 0.505, 0.511 and 0.502 respectively. Tuning to the multiway
obligation would demand a dial cut of 84%, 118% and 97%, which is to say the
dial cannot reach it and the linear reach arithmetic stops being valid long
before. The heads-up obligation is used instead because it is the version no
reading of the poker disputes.

**Part two: the three must end ordered nit below TAG below LAG on defence
frequency.** Today they are inverted — the TAG defends most (0.736), then the
LAG (0.699), then the nit (0.683) — and a tight-aggressive persona that
continues against bets more often than a loose-aggressive one is not a TAG.
The ordering is the same one the grounded showdown targets encode (nit 20–28,
TAG 25–29, LAG 26–31), and went-to-showdown is downstream of defence frequency,
so the two orderings are the same claim.

**The spacing.** The LAG is placed at the ceiling of the defensible range — its
own heads-up obligation, 0.674 — because of the three it is the archetype whose
identity is the widest continuation. The other two are placed below it in the
proportion the grounded midpoints give (nit 24, TAG 27, LAG 28.5):

    LAG target  = 0.674
    TAG target  = 0.674 * 27   / 28.5 = 0.6385
    nit target  = 0.674 * 24   / 28.5 = 0.5676

Proportional spacing is an approximation and is worth naming as one. Over the
narrow range these three occupy, went-to-showdown is roughly affine in defence
frequency rather than proportional to it, because of the constant checked-down
term in §1. The approximation is used only to space three targets that the
ordering constraint already brackets, not to predict a level.

## 3. From defence target to dial value

At a facing decision the calling dial `L` multiplies the whole continue side of
the merit vector — the call merit directly, and the raise merit through the
`rscale` coupling — while the fold merit does not depend on it at all. So the
continue-to-fold odds scale as `L^eta`, where `eta` is 1 at every decision
except a strong-draw decision under a dial below 1.0, where the protected share
holds part of the bonus back:

    eta = A*L / (A*L + B),   A = call_base + 0.55*(1 - s),   B = 0.55*s

with `s` the price-mandated protected share and 0.55 the strong-draw call
bonus. Averaged over every facing decision on the harness, `eta` is 0.9496 for
the nit, 0.9415 for the TAG and 0.9302 for the LAG. That is where S3-T1b's
reach arithmetic enters the derivation: the dial is between 5% and 7% less
effective than a bare multiplier because roughly a tenth of these decisions are
strong-draw decisions whose bonus is mostly protected.

Writing `O` for the continue-to-fold odds, the dial value that lands a persona
on its target defence frequency is

    L_new / L_old = (O_target / O_measured) ^ (1 / eta)

which gives:

    persona  measured  target   O_meas  O_targ  ratio^(1/eta)  L_old -> L_new
    nit       0.6831   0.5676   2.1556  1.3127     0.5930      0.45 -> 0.267
    tag       0.7361   0.6385   2.7893  1.7663     0.6154      0.60 -> 0.369
    lag       0.6995   0.6742   2.3277  2.0694     0.8812      0.55 -> 0.485

so the planned pack values are the nit at 0.27, the TAG at 0.37 and the LAG at
0.48, and the relative dial cuts `r` are 0.407, 0.385 and 0.119.

## 4. From dial cut to the registered went-to-showdown floor

A showdown hand reaches showdown by continuing at each facing decision it met,
so its showdown probability is the product of its continue probabilities, and
the relative fall in that product under a dial cut `r` is, to first order, the
sum over its decisions of `eta * (1 - p_continue) * r`. Averaged over the
harness, weighting each decision by the continue probability (because a
showdown hand only passes through decisions it continued at), that per-decision
sensitivity is 0.1699 for the nit, 0.1624 for the TAG and 0.1856 for the LAG.
Multiplying by the mean number of facing decisions per showdown hand from §1:

    persona  WTSD    decisions  sensitivity  r      predicted fall
    nit      0.6353   0.8086      0.1699     0.407    0.0355  (3.55pp)
    tag      0.6144   0.9395      0.1624     0.385    0.0361  (3.61pp)
    lag      0.5664   0.9471      0.1856     0.119    0.0118  (1.18pp)

**Registered floors: nit at least 3.5pp, TAG at least 3.5pp, LAG at least
1.0pp, measured on the band harness at its pinned seed and its stable 4,000-hand
sample, against this tip's 63.53 / 61.44 / 56.64.**

Three reasons the floor should be cleared rather than missed, all of which the
arithmetic above deliberately leaves out:

- **The first-order term understates the response.** The odds-ratio relation is
  convex in the dial, so the true fall in continue probability is larger than
  the linear term used here.
- **All three personas move at once.** Each one's opponents also continue less,
  so hands that used to be dragged to showdown by a caller now end earlier.
  The arithmetic treats every opponent as unchanged.
- **Compounding is truncated at one decision.** Hands that face two or three
  wagers lose continuation at each of them.

If a floor is missed, the honest reading is that this model of the dial's reach
is wrong, and the miss is reported as such rather than tuned around.

## 5. What this ticket does not claim

It does not claim to move any persona into its grounded band; the residual
after this retune is the checked-down path of §1, which needs a mechanism the
calling dial does not have. It does not claim the LAG's 1.0pp floor is
sufficient for anything downstream — S3-T4's conditional damp re-derivation
asks for five points on the LAG and the station, and this derivation predicts
about one for the LAG and none by construction for the station, whose dial sits
above 1.0 and is out of this ticket's scope. It does not touch the strong-draw
protected share, the fold-side level filed against the owed draw-equity gate,
or any bet-sizing value.

## 6. Provenance

Every figure above was measured on the band harness inside
`backend/tests/test_personas_postflop.py`, at its own pinned seed
(`random.Random(20260710)`) and its stable sample size (`_WTSD_ORDER_N` = 4,000
hands), at the tip this ticket branches from — commit `df32398`, the merge of
S3-T1b. The defence frequencies, faced-price mix, opponent counts and `eta`
values come from reading the engine's own normalized action-weight vector at
every facing decision without altering it; the exposure counts come from the
harness's own postflop action log. No pack value, engine file or baseline
artifact was changed to produce any of it, and this document is committed
before the first pack edit.
