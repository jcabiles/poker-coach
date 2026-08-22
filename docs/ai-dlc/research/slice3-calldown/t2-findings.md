# S3-T2 is blocked — the calling dial has no room to move

**Bottom line. The calling-dial retune cannot be built as specified, and no
pack value is changed by this pull request. A guard that shipped one day
earlier with S3-T1b — the check that no persona may fold the trace node's
15-out combo draw more often than the fully protected engine did — admits
EXACTLY ZERO downward movement in any of the five affected calling dials: a cut
of one thousandth breaches it. Behind that guard sit two more caps that would
still bind if it were lifted: the nit is already within 6.5 points of the
poker-theoretic ceiling on how often a bluff-catcher may fold, and the TAG's
price-response guard on the villain-range estimator runs out at a dial of about
0.40. At the deepest dials all three caps admit, the went-to-showdown reduction
is 2.1 points for the nit, 3.3 for the TAG and MINUS 0.3 for the LAG, against
the 3.5 / 3.5 / 1.0 this ticket pre-registered. The ticket's first acceptance
criterion therefore cannot be met, with or without the blocking guard.**

Three things need an owner decision before this ticket can be rebuilt; they are
listed in §5. Everything above and below was measured, not argued.

Companion document, written and committed before any pack value was touched:
`t2-preregistration.md` in this directory. It derives the reduction floors and
the dial values this ticket was going to ship. This document reports what
happened when those values were tried.

Measured at commit `df32398` (the merge of S3-T1b), in an isolated worktree, on
the band harness inside `backend/tests/test_personas_postflop.py` at its own
pinned seed and its stable 4,000-hand sample, plus that file's own
balanced-villain and trace-node fixtures.

## 1. The blocker: the trace-node draw-fold guard admits zero dial movement

`test_s3t1b_trace_node_folds_no_more_than_the_protected_engine_did` pins, for
each of the six personas, the frequency with which it folds a 15-out combo draw
facing 4 into a live pot of 10 — a hand getting 2.5-to-1 that needs 28.6%. The
claim is that no persona may fold it more often than the fully protected engine
did, and the docstring states the claim covers dial movement explicitly:
"any upward movement is a defect whichever direction a calling dial is being
tuned."

**The guard is a strictly decreasing function of the calling dial, pinned at
exactly the incumbent dial values, so it forbids every downward retune.** At
that node the price mandates the whole of the strong draw's call bonus — the
protected share clamps at 1.0, which the test asserts on the line above — so the
bonus is dial-independent, but the bucket's base call merit is not: the call
merit is `call_base * L + 0.55`, the fold merit does not depend on `L` at all,
and so the fold frequency rises for any `L` below the pinned one.

Measured, at three depths of cut:

    dials (nit/tag/lag)   headroom under the pin: nit        tag        lag
    0.449 / 0.599 / 0.549   (a 0.2% cut)        -0.000026  -0.000019  -0.000017
    0.44  / 0.59  / 0.54    (a 2% cut)          -0.000263  -0.000193  -0.000169
    0.38  / 0.42  / 0.48   (the deepest the
                            other caps admit)   -0.001855  -0.003536  -0.001190

A negative headroom is a breach. There is no positive row and there cannot be
one: the only dial that satisfies the pin is the dial the pin was taken at.

**The engine and the test disagree about this, and that disagreement is the
thing to resolve.** The S3-T1b block in `personas_postflop.py` says of this
same residual: "S3-T2 carries it as a WATCH, not a target: that ticket tightens
calling dials, which cannot move a number the dial no longer reaches, and must
not be judged on it." That sentence is wrong on its own terms — the dial still
reaches the bucket's base call merit, only the *bonus* is protected — and the
test does judge S3-T2 on it. One of the two has to give.

The test's docstring already names the escalation route: "Whether a future
slice may raise them is exactly the question this test exists to force back to
the owner." This document is that escalation. Nothing was re-recorded and
nothing was rewritten to get around it.

## 2. The nit is already near the fold ceiling that poker allows

Independently of the blocker, the nit's dial has very little room, and the
reason is a poker law rather than a pinned number. `α = f/(1+f)` is the ceiling
on how often a bluff-catcher may fold facing a bet of `f` times the pot before a
balanced bettor's bluffs become free money;
`test_fold_to_bet_respects_alpha_ceiling` asserts it raw, with no tolerance, on
a pure bluff-catcher range at four prices.

The binding cell is the half-pot bet, where α is 0.3333:

    nit dial   fold at 1/3-pot   1/2-pot   pot      1.5x-pot   headroom at 1/2-pot
    0.45 (today)   0.1240        0.2680   0.3616   0.4728        0.0653
    0.38           0.1464        0.2896   0.3976   0.5160        0.0437
    0.31           0.1648        0.3312   0.4376   0.5584        0.0021
    0.27 (planned) breach

At its shipped dial the nit already sits 6.5 points under the ceiling, which is
the second-narrowest margin on the roster (the passive fish is narrowest at
6.2). The fixture samples 1,250 catchers, so one binomial standard error is
about 1.3 points and the file's own convention is a three-sigma margin; that
puts the nit's floor at about **0.38**, and the raw ceiling breaks at about
0.31.

**This is a substantive finding about the roster, not a tooling problem.** The
nit's went-to-showdown rate is 35 points above its grounded band, and the
calling dial cannot close that gap because the nit is already close to folding
bluff-catchers more often than is safe against a balanced opponent. The
went-to-showdown excess is arriving from somewhere the calling dial does not
reach — most of it from hands that never face a wager at all, which
`t2-preregistration.md` §1 measures at 47.7% of the nit's showdown hands.

## 3. The TAG's price response runs out at a dial near 0.40

`test_estimator_prices_the_faced_bet` requires the TAG's fold frequency to span
more than 0.20 between a half-pot bet and a three-times-pot bet, on both a
middle pair and an air hand, and it was written to catch an estimator that had
become price-blind. The air leg tightens as the dial falls, because the fold
frequency at the small price rises while the one at the big price is already
near 1:

    tag dial   air folds at f = 0.5 / 1.5 / 3.0    span
    0.60 (today)   0.696  0.875  0.965            0.2698
    0.50           0.733  0.893  0.971            0.2382
    0.45           0.753  0.903  0.974            0.2209
    0.42           0.765  0.909  0.976            0.2100
    0.40           0.774  0.913  0.977            0.2025
    0.37 (planned) 0.787  0.919  0.978            0.1909  (breach)

So the TAG's floor is about **0.42** with any margin at all, against the 0.37
the defence mandate asks for. The compression is a saturation effect rather
than a loss of price response, but the guard is live and asserts a span, so it
binds as written.

## 4. What the roster does at the deepest dials all three caps admit

Setting the nit to 0.38, the TAG to 0.42 and the LAG to 0.48 — the deepest
values §2 and §3 allow, and still a breach of §1 — the band harness reads:

    persona          before   after    change     ceiling  AF     fold-to-cbet
    nit              0.6353   0.6145   -2.08pp    0.68     1.426  0.365
    tag              0.6144   0.5813   -3.31pp    0.65     2.516  0.312
    lag              0.5664   0.5696   +0.32pp    0.59     2.579  0.338
    maniac           0.5887   0.5957   +0.70pp    0.62     3.130  0.326
    calling_station  0.7060   0.6999   -0.61pp    0.72     0.327  0.172
    passive_fish     0.5324   0.5162   -1.63pp    0.55     0.874  0.460

Every aggression-factor and fold-to-continuation-bet reading stays inside its
band, every ordering leg holds — the station beats the TAG and the LAG, the fish
stays under the TAG, the station-minus-fish gap is 0.184, the maniac stays under
the station — and no persona crosses its ceiling. **But the nit misses its
pre-registered 3.5-point floor, the TAG misses its 3.5-point floor, and the LAG
moves the wrong way**, so the ticket's first acceptance criterion fails even if
the blocking guard is lifted.

The LAG's rise is worth one line of its own, because it is the same composition
effect the last two ratchets recorded, now large enough to reverse the sign of
its own dial cut: a tighter nit and a tighter TAG also RAISE less at the nodes
they face, so the LAG meets less aggression, folds less in response, and rides
more hands to showdown than its own cut removes.

## 5. What the owner has to decide

1. **The trace-node guard.** Does a legitimate downward retune of a calling
   dial get to raise those pins, and if so on what re-derivation? The natural
   re-derivation is mechanical — recompute the reference under the fully
   protected engine at the shipped dials — but at this node that makes the two
   engines identical by construction, so the guard would keep its force against
   a mechanism change and lose it against a dial change. Stating that plainly is
   part of the decision rather than a detail of it.
2. **Whether S3-T2 is worth shipping at the reduced size.** Two points on the
   nit and three on the TAG is real movement, and the direction is right, but it
   is not "the bulk of the went-to-showdown reduction" the slice spec expects of
   this ticket, and it does not buy the headroom S3-T4's conditional
   re-derivation asks for (five points each on the station and the LAG).
3. **Where the rest of the reduction is supposed to come from.** The measured
   answer is that the calling dial is not the lever: 42 to 48 percent of these
   personas' showdown hands never face a wager, and the ones that do face about
   one wager each. That points at the checked-down path — how often a hand
   reaches the river with no bet in it — rather than at how a bot responds to a
   bet. It is a different mechanism and a different ticket.

## 6. What this pull request contains

The pre-registration document, this findings document, and nothing else. The
pack values, the engine and every band are byte-identical to `df32398`. The
five-seed de-robotization gate was run twice, and separation is not what stops
this ticket.

    seeds                       601       602       603       604       605
    at the planned dials     1.707875  2.043381  1.633304  1.768972  1.914468
    on the reverted tree     1.694638  1.794341  1.846232  1.567513  1.660562
    required                 1.254429 on every seed; both runs PASS 5/5

The two runs carry different configuration hashes (`c1c01706ee044` with the
retuned packs, `c3eb80f12c52c` without), which is the provenance that the first
really did measure the retune. Tightest at the planned dials is seed 603 at
1.633304; tightest on the unchanged roster is seed 604 at 1.567513 — so the
retune would have SEPARATED the roster further rather than pressing the floor.
The binding pair was recomputed by hand from the gate's own per-persona
measurements for seed 601 (the gate's JSON report does not name it) and is
LAG-TAG at 1.707875, reproducing the reported figure exactly; that is the axis
the slice spec names as the tight one.
