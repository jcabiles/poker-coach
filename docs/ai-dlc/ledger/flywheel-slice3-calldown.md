# Ledger — improvement slice 3 (calldown) of the bot-realism flywheel

**Bottom line. Four things are filed here and none of them is fixed by this
slice. (1) The calling dial is hand-strength-blind, so it cannot close the
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
arithmetic suggests, filed against the contract row that owns it.**

Slice spec: `../specs/flywheel-slice3-calldown.md` ·
Tickets: `../tickets/flywheel-slice3-calldown.md` ·
Contract map: `../contracts/flywheel-slice3-calldown.md` ·
Theory contract: `../contracts/persona-realism-theory-contract.md`.

This file is chronological within each entry. "S3-T2" is ticket 2 of this slice:
the retune of the per-persona `call_looseness` calling dials.

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
