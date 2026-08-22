# Pre-registered reduction target — S3-T2 (calling-dial retune), revision 3

**Bottom line. This ticket registers two floors and withdraws a third. The nit's
went-to-showdown rate must fall by at least 1.0 percentage point and the TAG's
by at least 3.5, measured on the band harness. The LAG's floor is WITHDRAWN and
FILED on owner ruling 11 of 2026-08-22, and the LAG stays at 0.55: its dial DOES
move it, but through cross-persona coupling, so the size and the sign depend on
where the other personas are set — §5 gives the table with both comparison bases
labelled, and whether to tune it in a follow-up is an owner decision. The dial values that follow are the nit at 0.32 and the
TAG at 0.38, and both are set by external evidence and then capped by a live
test rather than by this ticket's discretion — the nit by the α fold-ceiling
test, which at its pinned seed admits no dial below about 0.31, and the TAG by
the deterministic 1,728-cell sweep that keeps it from collapsing onto the nit.**

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

**The nit's dial floor is about 0.31, and this ticket ships 0.32.** The raw
ceiling still holds at 0.31 with 0.0021 to spare and breaks at 0.30. The margin
at the shipped value is deliberately small and deliberately stated: 0.32 leaves
0.0197 of headroom, which is about 1.5 binomial standard errors on the
1,250-catcher fixture. A larger margin was considered and rejected — an earlier
draft imposed a three-sigma rule the test does not assert, which would have
stopped the nit at 0.38 and is exactly the kind of self-imposed conservatism
that reads as a measurement but is not one. The α test itself is untouched by
this ticket: owner ruling 10 of 2026-08-22 keeps it RAW and forbids editing it
in a fix round. The question it raises — the ceiling is asserted roster-wide and
says nothing about whether a tight archetype may sit against it on purpose,
which is what a nit's defining leak actually is — is filed as a MEDIUM contract
defect in `docs/ai-dlc/ledger/flywheel-slice3-calldown.md` for a future
re-anchor slice. **Both gates are green at 0.32**; nothing here is a live
contradiction, and the two are scoped to different opponent populations by
design (see `test_fold_to_bet_respects_alpha_ceiling`'s own docstring).

**The nit's own dial does not deliver the contract's fold-to-c-bet band.** At
0.32 the nit folds to continuation bets 43.5% of the time against a band floor
of 60. The reason is the lever's SHAPE, not the size of the retune: the dial
scales the whole continue side regardless of what the bot holds, while the fold
side never reads it, so it moves air — which already folds about 0.89 of the
time at a half-pot bet — by the same odds factor as the marginal made hands
where the gap actually lives. That is filed as an engine-lever defect in the
same ledger, with a bucket-aware fold lever as the follow-up.

**The TAG is not capped by α at any dial the roster would use** — it still
holds 0.0637 of headroom at 0.31, more than the passive fish holds today
(0.0624), so tightening the TAG does not make it the roster's binding cell.
What sets the TAG is the ordering target of §1, measured directly with the nit
pinned at 0.32 and the LAG unchanged:

    tag dial   nit FtC   tag FtC   lag FtC   order nit > tag > lag?
    0.45        0.389     0.307     0.328    no  (tag still under lag)
    0.40        0.410     0.311     0.323    no
    0.38        0.435     0.326     0.319    yes, by 0.007
    0.37        0.435     0.350     0.325    yes, by 0.025
    0.34        0.429     0.419     0.301    yes, but tag is now level with nit

**That table is too noisy to set a dial on, and saying so is the point.** The
harness gives the TAG about 310 fold-to-c-bet opportunities and the LAG about
460 at this sample size, so one standard error on their difference is around
0.033 — larger than either restored margin. The direction is consistent across
the sweep; the exact crossing point is not resolvable here.

**What sets the TAG's dial is a deterministic instrument instead.** The
1,728-cell nit-versus-tag enumeration (`G-SWEEP`, the cross-persona gate the
R9-LOOSEFIT slice shipped) requires the nit to fold more than the TAG by over
0.02 in at least 650 non-degenerate cells. It has no sampling error. With the
nit pinned at 0.32 it reads:

    tag dial   0.60   0.50   0.45   0.42   0.40   0.39   0.38   0.37
    margin     910    898    826    788    730    696    668    628   (floor 650)
    strict     982    982    980    978    974    972    984    984   (floor 800)

**0.38 is the deepest dial that keeps the two archetypes separated**, and it is
where this ticket stops. Tightening to 0.37 would put the TAG's fold behaviour
inside 0.02 of the nit's in more cells than that gate allows — collapsing one
archetype onto another, which trades a defect for a defect.

⚠️ WHAT REVISION 2 GOT WRONG HERE. Revision 2 set the TAG at 0.37 on the noisy
fold-to-continuation-bet table alone, and the full suite then went red on
G-SWEEP-b. The dial moved to 0.38; the registered floors did NOT change, and the
measured fall is LARGER at 0.38 than at 0.37 (6.15 points against 5.20), which
is a composition effect rather than a contradiction. The sweep table above was
re-measured on this branch and reproduces cell for cell.

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
    tag      0.6144   0.9395      0.1624     0.60 -> 0.38  0.3667    3.44pp

## 5. The registered floors

**nit: at least 1.0 percentage point. TAG: at least 3.5 percentage points. LAG:
withdrawn.**

The TAG's floor is the §4 point estimate rounded UP to the nearest half-point (3.44 predicted, 3.5 registered) — a deliberately STRONGER registration than the estimate, so the ticket cannot pass by landing under its own prediction. The nit's is not, and the
gap needs saying plainly: the nit's flop-seen sample on the harness is the
smallest on the roster (about 980 hands of the 4,000), so one binomial standard
deviation on its went-to-showdown reading is about 1.5 points. A floor of 2.5
would be registering a number the instrument cannot resolve. **1.0 is what can
be honestly claimed**, and the shortfall against the point estimate is itself
reportable rather than hidden.

**The LAG's floor is WITHDRAWN AND FILED under owner ruling 11 of 2026-08-22.
Its pack is left alone: `call_looseness` stays at 0.55.** The reason is COUPLING,
not the absence of a lever — the dial does move the LAG, but how much and in
which direction depends on where the other personas' dials are set, so a floor
registered against it would be a floor on a quantity this ticket cannot control
on its own. Revision 2 of this document said instead that the dial "is not the
lever", which is false; the correction belongs on the record rather than in a
deleted paragraph.

**Two comparison bases exist and quoting either alone misleads, so both are
labelled everywhere.** The **all-baseline** base is the whole roster before this
ticket (LAG 0.5664) and answers "what did this pull request do to the LAG". The
**own-dial** base is the LAG at 0.55 with the nit and TAG already at their
shipped values (LAG 0.5769) and answers "what would the LAG's own dial do from
here". Measured on the band harness at its pinned seed and `_WTSD_ORDER_N` =
4,000 hands:

| nit / TAG / LAG dials | LAG went-to-showdown | vs own-dial 0.5769 | vs all-baseline 0.5664 |
|---|---|---|---|
| 0.45 / 0.60 / 0.55 (all-baseline) | 0.5664 | — | — |
| 0.32 / 0.38 / 0.55 (**shipped**) | 0.5769 | — | +1.05pp |
| 0.38 / 0.42 / 0.48 (revision 2's evidence) | 0.5696 | not comparable — different companions | +0.32pp |
| 0.32 / 0.38 / 0.48 | 0.5626 | **−1.43pp** | −0.38pp |
| 0.32 / 0.38 / 0.42 | 0.5387 | **−3.82pp** | −2.77pp |

**Revision 2's claim, corrected.** It said every dial cut tried moved the LAG's
showdown rate the wrong way. It had measured two configurations, quoted the
all-baseline column, and generalized. Read against the own-dial base — the
question a follow-up ticket would actually be asking — the LAG's dial moves its
showdown rate DOWN by 1.43 points at 0.48 and 3.82 points at 0.42.

**What is really wrong with it as a registered target is that the reduction is
bought from the other two personas.** At a LAG dial of 0.42 the TAG's own reading
goes back UP from 0.5528 to 0.5815, handing back 2.87 of the 6.15 points the
TAG's retune just won. That is the same mechanism the last two ceiling ratchets
recorded, running in the other direction: the dial scales the whole continue side
of a facing node, RAISE included through the `rscale` coupling, so a tighter LAG
raises less, the TAG meets less aggression, folds less in response, and rides
more hands to showdown.

**So the honest statement is about coupling, not about the absence of a lever.**
The LAG's showdown rate is not a function of the LAG's dial alone; it is a
function of the whole roster's dials, and the cross-persona term is the same size
as the own-dial term. The owner withdrew the floor on that basis and the LAG
stays at 0.55 in this ticket. **Whether to tune it in a follow-up is filed as an
owner decision** in the LAG's own entry in
`docs/ai-dlc/ledger/flywheel-slice3-calldown.md`.

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
`docs/ai-dlc/contracts/persona-realism-theory-contract.md` §5 and §5a.

**Revision history, and what "pre-registered" means across it.** Revision 1
derived its targets from minimum-defence frequency read as a ceiling, which is
wrong poker; §0 records that and withdraws every number it produced. Revision 2
re-derived the targets from the contract's own rows and was committed BEFORE any
pack value was touched — that is what the pre-registration claim rests on. Its
original commit was rewritten when this branch was restructured, so the
verifiable citation is **`34ef9e0`** on `feat/slice3-t2-fix-round`, which carries
revisions 2 and 3 together and is the commit immediately BEFORE the retune
(`974d962`) that changes the packs. Ordering, not authorship, is what the claim
needs, and the ordering is checkable in the branch's own history.
Revision 3 (this one) changes NO registered floor. It corrects the TAG's dial
from 0.37 to 0.38 for a gate the 0.37 breached, corrects the α floor from 0.305
to 0.31, and replaces revision 2's overstated LAG paragraph with the fuller
measurement in §5. Every figure in revisions 2 and 3 was re-measured
independently on the fix-round branch, off commit `aaaee50` (the merge of the
S3-T2 blocked-findings pull request, #213, which is itself based on `df32398`,
the merge of S3-T1b), and reproduced cell for cell.
