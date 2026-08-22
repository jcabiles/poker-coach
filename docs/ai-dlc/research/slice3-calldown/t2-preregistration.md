# Pre-registered reduction target — S3-T2 (calling-dial retune), revision 2

**Bottom line. This ticket registers two floors and withdraws a third. The nit's
went-to-showdown rate must fall by at least 1.0 percentage point and the TAG's
by at least 3.5, measured on the band harness. The LAG's floor is WITHDRAWN: its
dial cannot lower its showdown rate at all, which is a measurement rather than a
concession. The dial values that follow are the nit at 0.32 and the TAG at 0.37,
and both are set by external evidence and then capped by a poker law — the nit
by the α fold-ceiling, which admits no dial below about 0.305, and the TAG by
the point at which the roster's fold-to-continuation-bet ordering matches the
one the theory contract's grounded bands give.**

"Went to showdown" is the share of hands a persona takes to showdown out of the
hands where it saw the flop. The "band harness" is the pinned population inside
`backend/tests/test_personas_postflop.py` that the went-to-showdown assertions
run against; it is the gating instrument for this slice, and the 50,000-hand
export is diagnostic only. S3-T2 is ticket 2 of improvement slice 3 of the
bot-realism flywheel: the retune of the per-persona `call_looseness` pack
values.

## 0. What revision 1 got wrong, and why it is recorded rather than deleted

**Revision 1 of this document derived its targets from minimum-defence
frequency, treating it as a CEILING on how often a persona may continue. That
is backwards, and a theory review caught it.** Minimum-defence frequency is the
*floor* a defender must clear so that a bettor's pure bluff is not free money;
continuing more often than it is not automatically a leak, and against a
population that under-bluffs — which describes both real micro-stakes pools and
this roster — the exploitative response is to defend *less* than it, not to
treat it as a bound one may not exceed. The multiway form revision 1 quoted has
the same defect for the same reason. Every target that argument produced is
withdrawn.

What survives untouched is the *reach* arithmetic in §3 and §4 below — how much
of a dial change reaches the merit vector, how much of that reaches a showdown
— which the review checked and found sound. What replaces the discarded half is
the theory contract's own grounded statistics, with their provenance, per §11
item 15 of that contract (a target written into a ticket must carry the triple
that sources it).

## 1. The target comes from the contract's fold-to-continuation-bet row

The calling dial governs one thing directly: how often a persona continues when
it faces a wager. The grounded statistic that measures exactly that is the
theory contract's **Fold-to-C-bet aggregate** row, which is one of only three
statistics the contract marks HARD-today (measurable on today's harness):

| persona | grounded band | measured on the band harness |
|---|---|---|
| nit | 60–75 | 35.9 |
| tag | 50–60 | 29.3 |
| lag | 40–50 | 33.8 |

**Provenance triple** (contract §5a): format **9-max full ring** · pool
**online micro–low NL cash, NL2–NL25** · sources **S1** (BlackRain79, a
full-ring micro-stakes specialist publishing 6-max and full-ring values side by
side, fold-to-flop-c-bet 60 in both) and **S4** (the HM2 official forum's
full-ring "normal" band, 40–70), corroborated on level by **S3** (42–57) and
**S5** (~40) at unstated format. Status: VERIFIED · confidence **LOW** ·
CONFIRMED UNCHANGED · per-archetype band edges **DIRECTIONAL**.

Two things follow, and the second is the sharper one.

**All three fold far too rarely.** Every reading sits 6 to 30 points below its
band floor. The direction is unambiguous and is the same for all three: fold
more when facing a bet. Because the band edges are DIRECTIONAL rather than
certified, this ticket takes the direction and the ORDER from that row and does
not write any of its numbers into a test.

**The TAG and the LAG are inverted.** The grounded bands order the three
nit > tag > lag (60–75 above 50–60 above 40–50); the roster reads
nit 35.9 > lag 33.8 > tag 29.3. A tight-aggressive persona that folds to
continuation bets *less* often than a loose-aggressive one is not a TAG, and
that is an archetype defect independent of any level. **Restoring the order
nit > tag > lag is this ticket's primary target.** It is a statement about the
roster's shape, so it survives the LOW confidence on the band edges.

The contract's went-to-showdown row (nit 20–28, tag 25–29, lag 26–31; format
and pool as above; sources **S1 + S2**, two independent authors publishing both
formats side by side and agreeing within a point — 6-max 27 / 27–28 against
full ring 25 / 24–25; VERIFIED, confidence **MEDIUM**, band edges DIRECTIONAL)
is the statistic the slice is judged on, but it is downstream of the one above
and is not what the dial is set from.

## 2. Feasibility, computed BEFORE the floors are registered

A target that the α fold-ceiling forbids is not a target. α = f/(1+f) is the
ceiling on how often a bluff-catcher may fold facing a bet of `f` times the pot
before a balanced bettor's bluffs become free money;
`test_fold_to_bet_respects_alpha_ceiling` asserts it raw, with no tolerance, on
a pure bluff-catcher range. The binding cell for both personas is the half-pot
bet, where α is 0.3333. Headroom at that cell, measured across the dial:

    nit dial   0.45    0.42    0.40    0.38    0.36    0.34    0.33    0.32    0.31    0.30
    headroom  .0653   .0541   .0549   .0437   .0381   .0301   .0245   .0197   .0021  -.0027

    tag dial   0.60    0.45    0.40    0.37    0.34    0.31
    headroom  .1565   .1173   .1005   .0925   .0773   .0637

**The nit's dial floor is about 0.305, and this ticket ships 0.32.** The margin
is deliberately small and deliberately stated: 0.32 leaves 0.0197 of headroom,
which is about 1.5 binomial standard errors on the 1,250-catcher fixture. A
larger margin was considered and rejected — an earlier draft imposed a
three-sigma rule the test does not assert, which would have stopped the nit at
0.38 and is exactly the kind of self-imposed conservatism that reads as a
measurement but is not one.

**The nit's own dial therefore cannot deliver the contract's fold-to-c-bet
band.** At 0.32 the nit folds to continuation bets 43.5% of the time against a
band floor of 60. The gap is not closable by this lever, and §5 records why.

**The TAG is not capped by α at any dial the roster would use** — it still
holds 0.0637 of headroom at 0.31, more than the passive fish holds today
(0.0624), so tightening the TAG does not make it the roster's binding cell.
What sets the TAG is the ordering target of §1, measured directly with the nit
pinned at 0.32 and the LAG unchanged:

    tag dial   nit FtC   tag FtC   lag FtC   order nit > tag > lag?
    0.45        0.389     0.307     0.328    no  (tag still under lag)
    0.40        0.410     0.311     0.323    no
    0.37        0.435     0.350     0.325    YES
    0.34        0.429     0.419     0.301    yes, but tag is now level with nit

**0.37 is the largest dial at which the grounded ordering is restored**, and it
is where this ticket stops. Going further would start collapsing the TAG onto
the nit, which trades one archetype defect for another.

## 3. How much of a dial change reaches the merit vector

This section and the next are carried over from revision 1 unchanged; the theory
review reproduced them.

At a facing decision the dial `L` multiplies the whole continue side of the
merit vector — the call merit directly, and the raise merit through the `rscale`
coupling — while the fold merit does not depend on it. So the continue-to-fold
odds scale as `L^eta`, where `eta` is 1 at every decision except a strong-draw
decision under a dial below 1.0, where S3-T1b's protected share holds part of
the bonus back:

    eta = A*L / (A*L + B),   A = call_base + 0.55*(1 - s),   B = 0.55*s

with `s` the price-mandated protected share and 0.55 the strong-draw call bonus.
Averaged over every facing decision on the harness, `eta` is 0.9496 for the nit
and 0.9415 for the TAG — the dial is 5 to 6 percent less effective than a bare
multiplier because about a tenth of these decisions are strong-draw decisions
whose bonus is mostly protected. S3-T1b measured the same thing from the other
side: the share is evaluated 3,849 times over this population, 32.63% of those
clamp at 1.0, and the mean share is 0.8289, so the dial's mean reach into the
strong-draw call bonus is 17.1%.

## 4. How much of that reaches went-to-showdown

A showdown hand reaches showdown by continuing at each facing decision it met,
so its showdown probability is the product of its continue probabilities, and
the relative fall in that product under a relative dial cut `r` is, to first
order, the sum over its decisions of `eta * (1 - p_continue) * r`. Weighting
each decision by its continue probability — a showdown hand only passes through
decisions it continued at — that per-decision sensitivity is 0.1699 for the nit
and 0.1624 for the TAG. Two more measured facts bound how far it can compound:

- **Most showdowns are not reached through a calling decision.** The share of
  showdown hands in which the persona never faced a wager at all — every street
  checked through, or checked to it and it declined to bet — is 47.7% for the
  nit, 44.1% for the TAG and 41.6% for the LAG. The dial has no lever there.
- **The hands that do face a wager face about one.** The mean number of
  postflop folds, calls or raises per showdown hand is 0.81 for the nit, 0.94
  for the TAG and 0.95 for the LAG.

Multiplying through at the dial cuts §2 arrives at:

    persona  WTSD    decisions  sensitivity  dial          r       predicted fall
    nit      0.6353   0.8086      0.1699     0.45 -> 0.32  0.2889    2.52pp
    tag      0.6144   0.9395      0.1624     0.60 -> 0.37  0.3833    3.59pp

## 5. The registered floors

**nit: at least 1.0 percentage point. TAG: at least 3.5 percentage points. LAG:
withdrawn.**

The TAG's floor is the §4 point estimate rounded down. The nit's is not, and the
gap needs saying plainly: the nit's flop-seen sample on the harness is the
smallest on the roster (about 980 hands of the 4,000), so one binomial standard
deviation on its went-to-showdown reading is about 1.5 points. A floor of 2.5
would be registering a number the instrument cannot resolve. **1.0 is what can
be honestly claimed**, and the shortfall against the point estimate is itself
reportable rather than hidden.

**The LAG's floor is withdrawn on measurement, not on preference.** Every dial
cut tried moved the LAG's showdown rate the WRONG WAY — +0.32 points at a dial
of 0.48, +0.87 points at 0.55 with the nit and TAG tightened around it. The
mechanism is legible and is the same composition effect the last two ceiling
ratchets recorded: the dial scales the whole continue side of a facing node,
RAISE included through the `rscale` coupling, so a tighter nit and a tighter TAG
also raise less often, the LAG meets less aggression, folds less in response,
and rides more hands to showdown than its own cut removes. **For the LAG the
calling dial is not the lever**, and its pack is left alone.

## 6. What this ticket does not claim

It does not claim to move any persona into its grounded went-to-showdown band,
and §2 shows it cannot even reach the fold-to-continuation-bet band the dial
speaks to most directly. The residual is the checked-down path of §4 — how often
a hand reaches the river with no bet in it — which needs a mechanism the calling
dial does not have. It does not claim the nit's or the TAG's movement buys the
headroom S3-T4's conditional damp re-derivation asks for (five points each on
the station and the LAG). It touches no engine constant, no bet size, no
made-hand fold, and no band floor.

## 7. Provenance

Every measured figure was taken on the band harness inside
`backend/tests/test_personas_postflop.py`, at its own pinned seed
(`random.Random(20260710)`) and its stable sample size (`_WTSD_ORDER_N` = 4,000
hands), or on that file's own balanced-villain bluff-catcher fixture (1,250
catchers, seed 20260721), at the tip this ticket branches from — commit
`df32398`, the merge of S3-T1b. The defence frequencies, faced-price mix,
opponent counts and `eta` values come from reading the engine's own normalized
action-weight vector at every facing decision without altering it. The grounded
bands and their provenance triples are quoted from
`docs/ai-dlc/contracts/persona-realism-theory-contract.md` §5 and §5a. This
revision is committed before the pack values it registers against are changed.
