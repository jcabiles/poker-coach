# Ledger — improvement slice 3 (calldown) of the bot-realism flywheel

**Bottom line. Fifteen things are filed here and none of them is fixed by this
slice. Two compete for most consequential. Filed 5: a bot's probability of
betting a top pair or a middle pair does not respond to its stack depth AT ALL,
when commitment says it should rise toward certainty as the stack shortens — so
the mechanism the engine is missing on the value side is a commitment SLOPE.
That finding came out of the review that WITHDREW ticket 3's lever, which was a
damp pointing the other way (filed 7). Filed 10: the α fold ceiling is a bound on
the defender's WHOLE RANGE and not on any one hand class, so the 2026-08-19
ruling that it bounds naked ace-high — and the test filed 9 built to enforce it —
apply a range identity to a bucket, which measurement shows is wrong in both
directions at once.

The fifteen in order. (1) The calling dial is hand-strength-blind, so it cannot close the
fold-to-continuation-bet gap: it moves air, which already folds almost always,
by the same odds factor as the marginal pairs where the gap actually lives —
that needs a bucket-aware fold lever, which is an ENGINE-LEVER DEFECT at MEDIUM.
(2) The α fold-ceiling is asserted RAW on every persona and is silent on the
question of whether a tight archetype is allowed to over-fold on purpose; this
slice has pinned the nit close to that wall, which makes the question live — a
CONTRACT DEFECT at MEDIUM for a future re-anchor slice. (3) The LAG's calling
dial DOES move the LAG, but through cross-persona coupling its effect depends on
where the other personas are set; the reduction floor was withdrawn on the
owner's ruling and whether to tune it is filed as an owner decision. (4) The
`_DRAW_FREE_RIVER_PROB` constant stays at 0.30 rather than the roughly 0.50 the
arithmetic suggests, filed against the contract row that owns it. (5) Made-value
betting is flat in stack depth where it should slope upward — an OPEN ITEM for
the re-anchor slice, needing an owner decision. (6) The capped-node bluff-share
shortfall that seeded ticket 3 was read RAW, and part of it is warranted by the
identity's own size term. (7) The adjudication that withdrew ticket 3's lever,
recorded so it is not re-litigated from the code alone. (8) The re-derivation of
`_ACE_HIGH_RIVER_CALL_DAMP` did not fire — the headroom bar was missed by 4.05
points on the calling station and 5.41 on the LAG — so the constant stays at 0.06
and the re-derivation is filed for a future ticket. (9) Naked ace-high breaks the
α fold ceiling at every one of the 24 heads-up river cells, filed at HIGH with a
one-way compliance tripwire shipped in its place. (10) α is a per-RANGE bound and
not a per-BUCKET one, which re-opens the provenance of the ruling behind (9) and
reshapes (2). (11) The statistic the slice used to size the checked-down problem
counts the wrong event — it cannot fall when the bot itself is the one betting —
and ticket 5 measured the two disagreeing in sign on the same run. (12) Showdown
frequency barely responds to how often the bots bet a late street, because a bet
that is called makes a showdown just as a check-down does, so the remaining
thirty-point gap will not close with another merit-layer dial. (13) No
theory-contract row governs unopened late-street betting or what that betting
range is made of, so ticket 5 had to invent a local composition rule — and the
measurement filed under it shows a LAG that bets 83-99% of its top-pair-and-
better on an unopened river while its one-pair class is floored at zero, i.e. a
river checking range nearly free of strong hands, which is a recalibration
question for the owner and not a dial. (14) The
engine's multiplier order on the aggressive path does not match the contract
text — pre-existing, harmless while every factor is a plain multiply, filed
before someone adds a bound to that chain. (15) Ticket 5 registered a reduction
floor on a configuration that did not end up shipping, which turned a
composition effect into a recorded miss.**

Slice spec: `../specs/flywheel-slice3-calldown.md` ·
Tickets: `../tickets/flywheel-slice3-calldown.md` ·
Contract map: `../contracts/flywheel-slice3-calldown.md` ·
Theory contract: `../contracts/persona-realism-theory-contract.md`.

This file is chronological within each entry. "S3-T2" is ticket 2 of this slice:
the retune of the per-persona `call_looseness` calling dials. "S3-T3" is ticket
3: the stack-to-pot multiplier on made-value betting. "S3-T4" is ticket 4: the
extension of the α fold ceiling over naked ace-high on the river, plus the
conditional re-derivation of the one constant that governs how much naked
ace-high calls there.

---

## Filed 1 — ENGINE-LEVER DEFECT (MEDIUM): the calling dial is hand-strength-blind

**Filed by S3-T2, 2026-08-22.**

**The defect.** `call_looseness` scales the whole continue side of a facing
node's merit vector regardless of what the bot is holding
(`backend/app/domain/personas_postflop.py:1384`), while the fold side is
`_FOLD_BASE[bucket] * _price_factor(...)` (`:1461`) and does not read the dial at
all. So lowering the dial multiplies the fold-versus-continue ODDS by the same
factor in every strength bucket. That is not where the fold-to-continuation-bet
gap lives.

**Measured, at a flop facing node across the three prices this repository's
price fixtures use** (the nit, before and after this ticket's retune):

| hand | dial 0.45 (before) | dial 0.32 (shipped) | change at ½-pot |
|---|---|---|---|
| air | 0.8526 / 0.9464 / 0.9860 | 0.8906 / 0.9613 / 0.9900 | +3.8 points |
| middle pair | 0.3232 / 0.5932 / 0.8537 | 0.4018 / 0.6722 / 0.8913 | +7.9 points |

**Air already folds about 0.89 of the time at a half-pot bet, so there is almost
nothing left there for the dial to win.** The aggregate gap is carried by the
marginal made hands — and those are exactly the bluff-catchers the α ceiling
binds, so pushing the dial far enough to move them drags the balanced-villain
catcher node toward α. At the shipped 0.32 the nit's ½-pot catcher fold is
0.3136 against α's 0.3333, and its aggregate fold-to-continuation-bet reading is
0.435 against a grounded band floor of 60. **The dial runs out 16 points short,
and the reason is the lever's shape, not the size of the retune.**

**The follow-up: a bucket-aware fold lever.** The fold merit is the natural
place for it, because it is already per-bucket (`_FOLD_BASE[bucket]`) and
already price-aware, and because a lever there can raise folding on marginal
made hands without touching air or the strong draws. Any such lever is owned by
theory contract §4 row **P8 elasticity split** (`stickiness → call_looseness +
size_elasticity`), which is the row that owns the calling dial itself; a third
per-bucket term is an extension of that row and must be specified there before
it is built.

**Severity MEDIUM.** Nothing is red and no gate is breached; the defect binds
only a slice that is tasked with closing the fold-to-continuation-bet gap. It
becomes HIGH the moment such a slice is opened.

---

## Filed 2 — CONTRACT DEFECT (MEDIUM): α is asserted roster-wide and is silent on archetype

**Filed by S3-T2, 2026-08-22, under owner ruling 10 of that date.**

**The defect.** `α = f/(1+f)` is the share of the time a bluff-catcher may fold
facing a bet of `f` times the pot before a balanced bettor's bluffs become free
money. `test_fold_to_bet_respects_alpha_ceiling` asserts it RAW — no tolerance —
on every one of the six personas, and the contract carries it as a roster-wide
law (theory contract §9 item 1, the RES-D A1 guardrail). **What neither the test
nor the contract says is whether a tight archetype is allowed to sit closer to
that wall than a loose one, or to cross it on purpose.**

**Why that silence now matters.** A real nit's defining leak IS over-folding
bluff-catchers — it is most of what the word means at the table. A roster that
models a nit faithfully should therefore be pressing α, and this slice has
pressed it: at the shipped dial the nit's half-pot bluff-catcher fold is 0.3136
against α's 0.3333, headroom 0.0197, which is about 1.5 binomial standard errors
on the 1,250-hand fixture. The next dial down (0.31) leaves 0.0021 and the one
after (0.30) breaches.

| nit `call_looseness` | fold at ½-pot | α headroom |
|---|---|---|
| 0.45 (before this slice) | 0.2680 | +0.0653 |
| **0.32 (shipped)** | **0.3136** | **+0.0197** |
| 0.31 | 0.3312 | +0.0021 |
| 0.30 | 0.3360 | **−0.0027 (breach)** |

**The question for the re-anchor slice, stated as a choice.** Is α a
**roster-wide law** — every persona is held to it, and an archetype that would
exceed it is simply not modelled — or is it a **balanced-bettor guardrail that
the tight archetypes may exceed by a stated, sourced margin**, in which case
that margin needs a source and a written scope before any test admits it?

**Not this slice's to resolve, and nothing was done to the test.** Owner ruling
10 keeps the α assertion RAW and forbids editing it inside a fix round; S3-T2
stopped at a dial the raw ceiling admits and filed the question rather than
touching the guard.

---

## Filed 3 — The LAG's dial: coupling, not absence of lever

**Filed by S3-T2, 2026-08-22, under owner ruling 11 of that date.**

**What happened.** S3-T2 pre-registered a reduction floor for the LAG and
withdrew it before building, on the owner's ruling. The LAG's pack is unchanged
by this ticket: `call_looseness` stays at 0.55.

**The claim that the dial "is not the LAG's lever" is FALSE and is corrected
here.** At the dials this ticket ships, the LAG's own dial moves the LAG's
went-to-showdown rate in the right direction and by a useful amount. Two
comparison bases exist and both are given, because quoting either alone
misleads: the **own-dial** base is the LAG at 0.55 with the nit and TAG already
at their shipped values (0.5769), and the **all-baseline** base is the whole
roster before this ticket (0.5664).

| nit / TAG / LAG dials | LAG WTSD | vs own-dial base 0.5769 | vs all-baseline 0.5664 |
|---|---|---|---|
| 0.45 / 0.60 / 0.55 (all-baseline) | 0.5664 | — | — |
| 0.32 / 0.38 / 0.55 (**shipped**) | 0.5769 | — | +1.05pp |
| 0.32 / 0.38 / 0.48 | 0.5626 | **−1.43pp** | −0.38pp |
| 0.32 / 0.38 / 0.42 | 0.5387 | **−3.82pp** | −2.77pp |

**What is actually true is about coupling.** The dial scales the whole continue
side of a facing node — RAISE included, through the `rscale` coupling — so a
tighter persona also raises less, and everyone it faces meets less aggression
and folds less in response. Two consequences follow. First, the LAG's reading
depends on where its companions are set, which is why an earlier draft measured
the sign as positive at one pair of companion dials and this table measures it
as negative at another. Second, the reduction is partly paid for by the others:
at a LAG dial of 0.42 the TAG's own reading goes back up from 0.5528 to 0.5815,
handing back 2.87 of the 6.15 points the TAG's retune just won.

**Filed for an owner decision:** whether to tune the LAG's dial in a follow-up
ticket, knowing that its effect is real but companion-dependent and partly
self-cancelling across the roster. Separately, per the pre-registration's §4
measurement, 41.6 percent of the LAG's showdown hands never face a wager at all
— the checked-down path, which no calling dial reaches and which needs its own
mechanism.

---

## Filed 4 — `_DRAW_FREE_RIVER_PROB` stays at 0.30

**Filed by S3-T2, 2026-08-22, under owner ruling 6 of that date.**

`_DRAW_FREE_RIVER_PROB` (`backend/app/domain/personas_postflop.py:439`) is the
probability the bot assumes it will see the river for free after calling a turn
bet — the term that decides how much of a turn draw's two-card equity it may
count. It is authored at 0.30 where the arithmetic behind it suggests something
nearer 0.50, and its own comment says plainly that it is an assumption rather
than a fit.

**It stays.** The owner ruled it out of scope for this slice, and the reason is
that its natural gate cannot bound it: G-DRAW's cap is now DERIVED from the same
price-mandated protected share, so it asserts that the engine matches the poker
the test states, and moving the constant means re-stating that poker rather than
discovering a budget.

**The contract row that owns it** is theory contract §4, row **P6/F7 draw-bonus
equity gate** — "a SEPARATE lever from the fold-side brake: gate
`_DRAW_CALL_BONUS` itself by commitment, equity and nutness at high `c`", status
DIRECTIONAL. Any slice that re-derives this constant re-derives it against that
row, and against the went-to-showdown statistic the constant's own comment names
as the thing it serves.

---

## Filed 5 — OPEN ITEM (HIGH): made-value betting is FLAT in stack depth, where commitment says it should rise

**Filed by S3-T3, 2026-08-22, out of the triple review that withdrew that
ticket's lever.** S3-T3 is ticket 3 of this slice.

**The finding.** A bot's probability of betting a TOP_PAIR or a MIDDLE_PAIR does
not respond to its stack depth at all. Measured on the merit vectors themselves,
so there is no sampling variance in it — a K-9-3 rainbow flop, pot 10 big
blinds, stack swept to give stack-to-pot ratios from 10 down to 0.3:

| bucket | TAG | LAG | maniac | nit | passive_fish | calling_station | varies with stack? |
|---|---|---|---|---|---|---|---|
| top pair | 0.7458 | 0.7964 | 0.8725 | 0.4231 | 0.4231 | 0.3793 | **no — identical to 12 decimal places at every ratio** |
| middle pair | 0.4355 | 0.5070 | 0.6429 | 0.1617 | 0.1617 | 0.1385 | **no** |
| overpair+ | 0.8485→0.9438 | 0.8819→0.9573 | 0.9289→0.9751 | 0.5833→0.8077 | 0.5833→0.8077 | 0.5385→0.7778 | one step at `spr_commit` |

**Why it is a defect and not a preference.** As the stack-to-pot ratio falls
toward zero a made hand is progressively more committed, and the poker says its
betting frequency should rise toward 1. The engine holds it flat. The only stack
response on the value side is the commit block's flat 3.0× step, which reaches
overpairs and better and never touches the two buckets above.

**The mechanism that would fix it is a continuous commitment SLOPE over
`TOP_PAIR` and `MIDDLE_PAIR` below `spr_commit`** — the opposite direction to
the damp S3-T3 built and withdrew (filed 7). It interacts with the existing
commit block, whose step it would partly subsume, so it is a re-anchor-slice
item rather than a ticket-sized one.

**The contract row that owns it** is theory contract §3 amendment A8 item 5,
where it is filed as an open item for the single designated re-anchor slice.
**Owner decision required** before any slice builds it: whether the value-side
commit slope is in scope for the re-anchor, and whether it replaces or composes
with the existing commit step.

## Filed 6 — MEASUREMENT DEFECT (MEDIUM): the capped-node bluff-share shortfall was read RAW, and part of it is size-warranted

**Filed by S3-T3, 2026-08-22.**

**The defect.** The design dossier that seeded this ticket measured capped
decisions at about 96 percent of the roster's own bluff-share calibration and
read the shortfall as a defect. That reading is **raw** — the bluff-cell share of
the betting range, not divided by the identity's own target at the size each
wager was actually made at. The theory contract's formula `s / (1 + 2s)` says
**a smaller wager warrants a smaller bluff share**, and a capped wager is smaller
by construction. So part of the shortfall is what the identity ASKS for.

**What is now measured, and what still is not.**
`backend/tools/capped_composition_probe.py` (shipped by this ticket) reports both
the raw share and the target-normalised one; the figures are in
`../research/slice3-calldown/t3-report.md` §3. **The residual after
normalisation is still NOT decomposed** into arrival — which hands reach a capped
decision, the `π` term the merit layer cannot see — versus policy, the
conditional probability of betting given the hand. That needs a `π`-by-node table
nothing in this repository builds.

**The rule this puts on future slices**, now in theory contract §3 amendment A8
item 3: a gap reported on this instrument is a gap, not a defect, and no slice
may cite it as evidence that a policy is wrong until the decomposition exists.

## Filed 7 — ADJUDICATION: S3-T3's lever was built, measured and withdrawn

**Filed by S3-T3, 2026-08-22, recording a Director adjudication so the decision
is not re-litigated from the code alone.**

**What was built.** A stack-to-pot multiplier damping made-value betting below
`spr_commit` — the design dossier's "Option 1", named in the ticket as the
approved lever. It was implemented, and every acceptance criterion the ticket
wrote passed on its own terms.

**What the three reviewers said.** The refuter PASSED it: every number
reproduced, the build was honest. The theory reviewer returned NEEDS-WORK with
two HIGH findings and the cross-family reviewer returned FAIL with one BLOCKER,
and **they converged on the same thing — a design flaw, not an implementation
flaw**:

1. **The damp's direction is backwards where it has leverage.** It lowered
   top-pair betting from 0.746 to 0.724 for the TAG and 0.423 to 0.400 for the
   nit, and middle pair by 2.5 to 2.9 percentage points, at the stack depths
   where commitment says those hands should bet MORE — and it partly counteracts
   the commit block the contract already blesses. This is filed 5 seen from the
   other side: the engine's real defect at these buckets is the absence of a
   slope, and the lever added a damp.
2. **The premise was a raw reading of a size-warranted difference** — filed 6.
3. **The report's "the gap is mostly arrival" claim was unsupported**, because
   the probe computed a raw share and the paired toggle cannot separate arrival
   from policy. The claim has been withdrawn from both the report and the
   contract amendment, and replaced by an explicit "not measured here".

**The adjudication, and the precedent it follows.** WITHDRAW the lever; ship the
instrument, the contract limits and the finding. The precedent is PR #199 in
improvement slice 2 — a lever measured, found to move play away from realism,
withdrawn, with its instrument kept. The engine is byte-identical to `4f653ef`,
every re-recorded fixture and both went-to-showdown ceiling ratchets are
reverted (with no lever there is no movement to record), and the withdrawn code
remains in this branch's git history for provenance.

**One thing worth carrying forward about process.** The ticket's acceptance
criteria were all met by a change that should not ship. Criteria that ask "did
the lever move its statistic" cannot catch "moving that statistic is wrong"; the
pre-registration's own postscript records the same lesson from the other end.

---

## Filed 8 — Re-derive `_ACE_HIGH_RIVER_CALL_DAMP` once the showdown headroom exists

**Filed by S3-T4, 2026-08-22, under owner ruling 7 of 2026-08-22 and the ratified
amendment draft's §III.2.** The ruling's source is the machine-local owner
rulings file `local/session-2026-08-22/rulings.md` (gitignored, so it is quoted
here in full rather than only cited): *"7. S3-T4 headroom condition: station AND
lag each >=5pp down on band harness vs d351150 baseline (71.1 / 57.3)."*

**What did not happen, and why.** S3-T4 carried a conditional second half: if
S3-T2 had bought enough went-to-showdown headroom, re-derive
`_ACE_HIGH_RIVER_CALL_DAMP` (`backend/app/domain/personas_postflop.py:684`, the
one constant governing how much naked ace-high calls on the river) away from its
shipped 0.06, against the then-current river price distribution. **The condition
does not hold and the re-derivation was not attempted.** Measured at S3-T4's tip:

| persona | `d351150` baseline | S3-T4 tip | change | shortfall against the 5.00pp bar |
|---|---:|---:|---:|---:|
| calling_station | 0.7105 | 0.7010 | −0.95pp | **4.05pp** |
| lag | 0.5728 | 0.5769 | **+0.41pp (UP)** | **5.41pp** |

**What the follow-up ticket must do**, per §III.2, and it may not be started
before the bar above is cleared: re-measure the minimum-defence obligation (the
game-theoretic floor on how often a defender must continue to stop bluffing being
free) at the then-current tip; read the resulting river continue rate against that
obligation; move the constant; and reapply the interim regime's ceiling ratchet
afterwards, recording the arithmetic. §III.2 also records that its ratchet forbids
upward movement past a ceiling, so ratifying the amendment did not by itself
license raising this damp.

**Two facts the follow-up should carry, both measured by S3-T4 rather than
inherited.** First, the damp value at which the whole roster becomes α-compliant
on the river MOVED AWAY this slice, from about 3.0 to **3.6** — roughly sixty
times the shipped 0.06, against the 7.5 times that the frozen went-to-showdown
bands already refused. Second, the reason it moved is S3-T2 itself: a tighter
calling dial also folds naked ace-high more often, so the nit's ⅓-pot river fold
rose 0.8432 → 0.8872 and the TAG's 0.6800 → 0.7600. The calldown slice bought
part of its showdown reduction with α headroom on this bucket. Full arithmetic:
`../research/slice3-calldown/t4-report.md`.

**Read this item together with filed 10 below.** If the owner re-rules that α is
not a per-bucket bound, this follow-up's target disappears with it — there would
be no per-bucket obligation for the damp to be re-derived against.

**Not a defect and not a blocker.** Nothing is red, the guard extension shipped
without it, and the engine is behaviourally byte-identical.

---

## Filed 9 — FINDING (HIGH, for owner ruling): naked ace-high breaks α at every river cell

**Filed by S3-T4, 2026-08-22.**

**The finding.** Extending the α fold ceiling to naked ace-high on the river, as
the 2026-08-19 owner ruling requires, produces a test that fails for **all six
personas at all four prices — 24 of 24 heads-up cells** — by between +0.2695
(the maniac facing a third of the pot) and +0.6391 (the nit facing a third of the
pot). The smallest breach is about 19 binomial standard errors at n = 1,250, so
this is not a seed artifact and there is nothing to tune around.

**What shipped instead of a tuned pass.** The guard is marked
`xfail(strict=True)`, which makes it a **one-way compliance tripwire**: it pins no
number, so no cell movement re-records anything here, and it goes red only if the
river becomes α-compliant, which is the event a fix wants announced. **State its
one-way-ness honestly — it CANNOT detect the breach widening.** Every one of the
24 cells could climb another twenty points and this test would still report a
quiet XFAIL, exactly as it does today; the movement S3-T2 already caused (nit
+0.0440, TAG +0.0800) was caught by the measurement in the report, not by this
test. Anyone who wants the widening gated needs a second, level-pinning
instrument, and this slice deliberately did not build one because filed 10 puts
the whole per-bucket obligation in question.

Strictness was verified rather than assumed, by patching the engine constant to a
compliant value and observing all six legs turn from XFAIL to FAILED.
`test_ace_high_river_alpha_guard_is_not_vacuous` proves the same assertion body
both trips (at a scratch damp of 2.5) and passes (at 5.0).

**Why this is the owner's and not a slice's.** Closing the breach needs an
ace-high river call merit near sixty times the shipped constant. The frozen
went-to-showdown bands refused 7.5 times it, and this slice exists to push
showdown frequency DOWN while calling more rivers pushes it UP. The ruling and
the bands are in direct conflict on this bucket, and reconciling them is an owner
decision. This entry does not resolve, and S3-T4 did not touch, the
α-per-archetype contract defect at filed 2 — the α assertion stays RAW, with no
tolerance, per owner ruling 10 of 2026-08-22.

**Severity HIGH** because a ratified owner ruling is unmet across an entire
street for the entire roster, and the gap widened this slice. **But see filed 10:**
the theory review of this ticket argues the ruling itself is mis-specified, in
which case the right response is to withdraw the obligation rather than to meet it.

---

## Filed 10 — CONTRACT DEFECT (MEDIUM): α is a per-RANGE bound, not a per-BUCKET bound

**Filed by S3-T4, 2026-08-22, on the persona-realism theory reviewer's finding.
File it beside filed 2 and resolve neither: this item RESHAPES that one.**

**The defect.** `α = f/(1+f)` bounds how often the DEFENDER'S WHOLE RANGE may
fold facing a bet of `f` times the pot. It says nothing whatever about how often
any individual strength bucket inside that range may fold. The 2026-08-19 owner
ruling — that α bounds the ACE_HIGH bucket — and the test S3-T4 built to enforce
it both apply a range-level identity to one bucket, and **that is wrong in BOTH
directions on this bucket**, not merely conservative.

**Measured, so the claim is arithmetic rather than assertion.** A whole-range
heads-up river probe on this file's own node (uniform deal, five-card board,
n = 2,000, seed 20260721) gives the composition below. "Beats ace-high" is every
strength bucket strictly above `ACE_HIGH`.

| slice of the range | share |
|---|---:|
| beats ace-high (monster · two-pair-plus · overpair/top-pair-top-kicker · top pair · middle pair) | **0.5675** |
| naked ace-high | 0.1280 |
| air | 0.3045 |

Minimum defence frequency is `1 − α`, so:

| bet | α | range must continue | supplied by hands that beat ace-high alone | what α actually requires OF ACE-HIGH |
|---|---:|---:|---:|---|
| pot | 0.5000 | 0.5000 | 0.5675 | **nothing — ace-high may fold 100% and minimum defence still holds** |
| 1.5×-pot | 0.6000 | 0.4000 | 0.5675 | nothing — same |
| ½-pot | 0.3333 | 0.6667 | 0.5675 | about 77% of ace-high must continue |
| ⅓-pot | 0.2481 | 0.7519 | 0.5675 | **about 100%, and even that is 5.6 points short — air must call too** |

So the per-bucket reading is too STRICT at the large prices, where the test
demands ace-high fold under 50% and 60% while the identity permits folding it
outright, and too LOOSE at the small prices, where the test is satisfied by a
24.81% fold rate while the identity demands ace-high continue essentially always.
The existing one-pair catcher fixture escapes this only because a one-pair
bluff-catcher sits AT the minimum-defence margin — the marginal hand the range's
last continuing units come from — so its per-bucket rate happens to coincide with
the range's. Ace-high does not sit at that margin, so the coincidence does not
transfer, and `_CATCHER_BUCKETS`' original exclusion of ace-high was right for a
better reason than the one written beside it.

**Why this re-opens the ruling's provenance, not just the test.** The W3R-1 rule
(theory contract §5a obligation 2) says that when a fit cannot reach a target
using a legitimate range or lever, the slice STOPS and re-opens that TARGET's
provenance — it does not widen the lever, widen the band, or re-scope the test.
S3-T4 is exactly that case: compliance needs a river call damp near 3.6, sixty
times the shipped 0.06, against 7.5 times that the went-to-showdown bands already
refused. Under W3R-1 the infeasibility is evidence about the target, and the
target here is the 2026-08-19 ruling.

**What happens to the test if the owner re-rules.** `test_ace_high_river_alpha_
ceiling` should then be **DELETED, not fixed**. It would not be a guard measuring
the wrong number; it would be a guard measuring a quantity the contract does not
bound, and softening or re-scoping it is the precise dodge W3R-1 exists to stop.

**How this reshapes filed 2.** Filed 2 asks whether a tight archetype may sit
closer to the α wall than a loose one, or cross it on purpose. That question
presumes α is a per-bucket bound. The live question underneath it is prior:
**is α a per-bucket bound at all?** Answer that first; filed 2's per-archetype
question only survives if the answer is yes.

**Cite the law's actual home.** α as a fold ceiling is the RES-D A1 guardrail,
implemented on the grader side as `_calibrate_catcher_fold` and asserted on the
bot side by `test_fold_to_bet_respects_alpha_ceiling` (RES-D §1c/§2 invariant 3).
It is NOT theory contract §9 item 1 — that item is the separate 60% → 42.9%
correction about the 3×-pot semi-bluff threshold, and citing it as the law's home
has been corrected in this ticket's report.

**Severity MEDIUM** and not higher: nothing is red, no gate is breached, and the
tripwire shipped by filed 9 is harmless either way. It becomes the blocking item
the moment a ticket is opened to CLOSE the ace-high river breach, because that
ticket would be spending a 60× constant move to satisfy an obligation this entry
says may not exist.

---

## Filed 11 — MEASUREMENT DEFECT (MEDIUM): "never faced a wager" and "checked down" were quoted as one statistic

**Three approved documents size the checked-down problem with a number that
measures something else, and S3-T5's instrument caught it.** "Share of showdown
hands in which the persona never faced a wager" is what
`t2-preregistration.md` §4 quoted at 47.7 / 44.1 / 41.6% for the nit, the TAG
and the LAG, and it is what S3-T5's spec §1 and this slice's prose repeated as
"every street is checked through". They are not the same event. Measured on the
band harness pooled over five seeds at 4,000 hands with every pack unauthored:

| persona | never faced a wager | genuinely checked down |
|---|---|---|
| nit | 51.5% | **31.7%** |
| tag | 46.9% | **19.8%** |
| lag | 40.7% | **14.5%** |

**Why they differ, precisely.** A hand can reach showdown with the persona
having met no wager because nobody bet — the checked-down case — or because the
persona itself was the bettor and nobody raised it. The first statistic pools
both. The second isolates the first case, which is what the ticket's prose
always described.

**The consequence for a lever like S3-T5's, stated carefully.** The
never-faced-a-wager share does NOT fall automatically when a bot starts betting,
and it does not automatically rise either. Both channels are live: the bot's own
bet can be RAISED, which moves the hand out of the numerator, and the bot's own
bet can PRE-EMPT the wager an opponent would otherwise have made at it, which
keeps the hand in. Which dominates is a per-persona empirical question, and
S3-T5 measured both signs on the same run — the nit and the LAG fell, the TAG
rose. An earlier draft of this entry said the metric "cannot fall when the bot
is the one betting", which is too strong and is corrected here.

**What was done inside the ticket.** A second counter, `checked_down` (no seat
wagered on any postflop street), was added to the same harness function during
the sweep and before any pack value moved. Both are reported. The original was
kept: it is the statistic the earlier tickets quoted, and dropping it after
seeing its reading would be moving the goalposts.

**What is left for a later slice.** Gate on `checked_down`. The figures in
`t2-preregistration.md` §4 and S3-T5's spec §1 overstate the checked-down
population by about twenty points on the nit; S3-T5's spec now carries a dated
correction, and anyone sizing a mechanism off the older documents should use the
right-hand column above.

**Severity MEDIUM**: nothing shipped is wrong and the correction is already in
the harness. It is filed because the wrong number is quoted in documents that
will be reused.

---

## Filed 12 — OPEN ITEM: went-to-showdown barely responds to how often the bots bet late

**S3-T5 raised three personas' unopened late-street betting by a fifth to a
quarter and moved one persona's showdown frequency.** The lever's effect on
policy is large, exact and reproducible: at the shipped gains the LAG bets an
unopened turn 55.0% of the time where it used to bet 47.8%, the nit 34.2% where
it used to bet 28.4%, the TAG 47.7% where it used to bet 41.0% — the direction
is UP, and an earlier draft of this entry had the two columns the wrong way
round. The effect on showdown frequency, pooled
over five seeds at 4,000 hands each, is −1.80pp for the LAG (2.8 standard
errors) and indistinguishable from zero for the nit and the TAG.

**The mechanism, measured rather than assumed.** Betting an unopened late street
does two opposite things to showdown frequency at once: the bet sometimes takes
the pot down, which removes a showdown, and it sometimes gets called by a field
containing a calling station and two passive fish, which creates a showdown that
a check-and-fold would not have produced. The candidate-gain scan shows the net
effect saturating almost immediately — quadrupling the value gains moved
showdown frequency slightly the WRONG way while driving the betting range
value-pure.

**Consequence for the slice's north-star gap.** The nit still sits about 32
points above its grounded went-to-showdown band and does not ship this lever at
all. Across the whole slice, on the 4,000-hand harness at the pinned seed, the
nit has moved 0.6353 → 0.6173 → 0.6312 and the TAG 0.6144 → 0.5528 → 0.5732.
Two shipped levers and one withdrawn have bought roughly four points on the TAG
and nothing durable on the nit. **Whatever closes the remaining thirty is not a
merit-layer dial on decisions the bots already mix**, and the next slice should
be scoped on that basis rather than on another dial.

---

## Filed 13 — CONTRACT DEFECT (MEDIUM): no theory-contract row governs unopened late-street betting

**S3-T5 is the first mechanic this program has built at the unopened turn/river
node, and the theory contract has nothing to say about it.** Its §4 and §5 rows
cover the aggressor-side continuation bet (position, P1), the facing-chips
defence side, and the three HARD-gatable aggregates. None of them governs (a)
how often a seat should BET an unopened late street, or (b) what that betting
range should be MADE OF. The closest row, P1 position, is street-blind and is
about the c-bet.

**Why that mattered here rather than being a paperwork point.** With no row on
composition, the first build of this ticket raised the value side alone and the
review had to catch by inspection what a contract row would have caught by
construction: the unopened river bet became value-pure. The fix — a bluff-side
companion fitted so the realised share does not fall — is a LOCAL rule invented
inside this ticket, and it is defensible but it is not contract law. A future
ticket at this node will have to re-derive it or re-invent it.

**What a row would need.** A grounded target for unopened late-street bet
frequency by persona archetype (which today would be `[UNVERIFIED]`, like the
c-bet band); a composition obligation stated against the §3 bluff-share identity
at the size actually wagered — the quantity `tools/capped_composition_probe.py`
already computes and `tools/late_street_probe.py` now computes at these nodes;
and a CROSS-PERSONA ORDERING obligation on the value side, because the
aggregates cannot see a partial ordering break. S3-T5 produced one: shipping the
LAG's lever puts it above the maniac at river top pair in position (0.885 against
0.843), turn middle pair in position (0.531 against 0.529) and river monster in
position (0.987 against 0.985), while the maniac stays far ahead on naked air.
Every aggregate band and every ordering leg is green through that.

### The measurement this row is missing, taken at the LAG's river node

Adjudicated from Codex Sol's HIGH finding on the rework: recorded here as
evidence for the missing row, NOT actioned, because recalibrating the river leg
is outside this ticket's owner-set boundary of one bounded lever and is the
owner's call. Probability of betting an unopened river, LAG, lever-off → shipped
(12,000 hands, three seeds):

| hand class | lever off | shipped |
|---|---|---|
| middle pair, in and out of position | **0.000** | **0.000** |
| top pair, in position | 0.794 | 0.885 |
| top pair, out of position | 0.713 | 0.831 |
| two pair plus, out of position | 0.934 | 0.966 |
| monster, in position | 0.975 | 0.987 |
| monster, out of position | 0.956 | 0.977 |
| naked air, in position | 0.194 | 0.240 |
| naked air, out of position | 0.125 | 0.155 |
| naked ace-high, in position | 0.148 | 0.183 |
| **bluff share of all river bets** | **13.1%** | **15.0%** |

**Read the middle-pair row first.** A LAG's unopened river betting range
contains NO middle pair at all, at any position, before or after this ticket:
that is the pre-existing `_RIVER_BET_FLOOR` (W1-a), not something S3-T5 did.
Combined with top pair and better betting 0.83 to 0.99, it means **the LAG's
river checking range is nearly free of strong hands** — it checks middle pair
and air and bets everything else — which is a polarised, under-bluffed river
policy for this archetype BEFORE this ticket. S3-T5 raised both sides with the
bluff side rising proportionally more (bluffs 13.1% → 15.0% of river bets, naked
air ×1.24 against a monster's ×1.02), so the ticket moved the composition in the
right direction; **the absolute gap remains and the ticket does not claim to have
closed it.**

**What a contract row would therefore have to require, beyond a bluff-share
target: a credible river CHECKING range** — some strong hands that check the
river — which today's engine cannot produce at this node while the value cells
sit at 0.83 to 0.99 and the one-pair class is floored at zero. That is a
recalibration of the river leg, not a dial.

**Severity MEDIUM**: it blocks nothing today, and it becomes the blocking item
the moment a second ticket touches this node, because two tickets inventing two
local composition rules is how a contract stops meaning anything.

---

## Filed 14 — CONTRACT DEFECT (LOW): the shipped multiplier order does not match §7 as written

**The engine applies the position multiplier LAST on the non-bluff aggressive
path, after the multiway and texture damps, while theory contract §7 writes the
stacked-multiplier order the other way round.** This is PRE-EXISTING — it
predates S3-T5, which inserted its own multiply next to the position one and
deliberately reordered nothing — and it is filed because S3-T5's contract map
noticed it and no entry existed.

Nothing measurable turns on it today: the operations are all multiplications on
the same scalar, so the ORDER is arithmetically irrelevant while every factor is
a plain multiplier. It stops being irrelevant the moment any factor becomes a
clamp, a floor or a cap — and this file already contains two such floors on
adjacent paths. **Severity LOW, but fix it in the contract text or in the code
before the next ticket adds a bound to that chain.**

---

## Filed 15 — PROCESS DEFECT (MEDIUM): a reduction floor was registered on a configuration that did not ship

**S3-T5 registered the LAG's checked-down floor at 1.9 points from an arm where
all three candidate personas were dialled, then shipped the LAG alone, where the
same lever delivers 1.42.** The miss is recorded as a shortfall under the
owner's rule, and the shortfall is real — but it is an artifact of the
registration rather than of the lever. A checked-down hand requires EVERY seat
to check, so a persona's checked-down share falls partly because of what the
OTHER dialled personas do; removing two of the three bettors takes back part of
the effect the third was credited with.

**The rule this should become.** A floor is registered against the configuration
that is proposed to ship, and if the ship list changes after the floors are
written, the floors are re-derived for the new list before the values land — or
the shortfall is attributed to the change rather than to the lever, which is
what S3-T5's report does.

**Severity MEDIUM**: it produced a misleading-looking miss on a ticket that is
otherwise green, and the same pattern will recur on any slice whose ship list is
decided by a gate rather than fixed in advance.
