# Ledger — improvement slice 3 (calldown) of the bot-realism flywheel

**Bottom line. Seven things are filed here and none of them is fixed by this
slice. The most consequential is filed 5: a bot's probability of betting a top
pair or a middle pair does not respond to its stack depth AT ALL, when
commitment says it should rise toward certainty as the stack shortens — so the
mechanism the engine is missing on the value side is a commitment SLOPE. That
finding came out of the review that WITHDREW ticket 3's lever, which was a damp
pointing the other way (filed 7).

The seven in order. (1) The calling dial is hand-strength-blind, so it cannot close the
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
recorded so it is not re-litigated from the code alone.**

Slice spec: `../specs/flywheel-slice3-calldown.md` ·
Tickets: `../tickets/flywheel-slice3-calldown.md` ·
Contract map: `../contracts/flywheel-slice3-calldown.md` ·
Theory contract: `../contracts/persona-realism-theory-contract.md`.

This file is chronological within each entry. "S3-T2" is ticket 2 of this slice:
the retune of the per-persona `call_looseness` calling dials. "S3-T3" is ticket
3: the stack-to-pot multiplier on made-value betting.

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
