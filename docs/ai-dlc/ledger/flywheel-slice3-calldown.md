# Ledger — improvement slice 3 (calldown) of the bot-realism flywheel

**Bottom line. Three things are filed here and none of them is fixed by this
slice. (1) A poker-theoretic ceiling and a research-grounded band contradict
each other for the tightest archetypes: α says the nit may not fold a
bluff-catcher more than about a third of the time at a half-pot bet, and the
theory contract says a nit folds 60 to 75 percent of continuation bets. Both
cannot be gates on the same roster. This is a MEDIUM contract defect for a
future re-anchor slice. (2) The LAG's calling dial is not the LAG's lever for
went-to-showdown; its reduction floor was withdrawn on the owner's ruling and is
filed for a mechanism that reaches the checked-down path. (3) The
`_DRAW_FREE_RIVER_PROB` constant, which decides how much of a turn draw's river
equity the bot is allowed to count, stays at 0.30 rather than the ~0.50 the
arithmetic suggests, and is filed against the contract row that owns it.**

Slice spec: `../specs/flywheel-slice3-calldown.md` ·
Tickets: `../tickets/flywheel-slice3-calldown.md` ·
Contract map: `../contracts/flywheel-slice3-calldown.md` ·
Theory contract: `../contracts/persona-realism-theory-contract.md`.

This file is chronological within each entry. "S3-T2" is ticket 2 of this slice:
the retune of the per-persona `call_looseness` calling dials.

---

## Filed 1 — CONTRACT DEFECT (MEDIUM): α bounds an archetype the contract asks to over-fold

**Filed by S3-T2, 2026-08-22, under owner ruling 10 of that date.**

**The defect.** Two numbers this repository treats as authoritative cannot both
be satisfied by the nit.

- **α = f/(1+f)** is the share of the time a bluff-catcher may fold facing a bet
  of `f` times the pot before a balanced bettor's bluffs become free money. At
  the half-pot bet it is 0.3333. `test_fold_to_bet_respects_alpha_ceiling`
  asserts it RAW — no tolerance — on a pure bluff-catcher range of 1,250 hands,
  and owner ruling 10 keeps it raw and forbids editing it inside a fix round.
- **The theory contract's fold-to-continuation-bet row** (§5, `Fold-to-C-bet
  aggregate`) puts a nit at 60 to 75 percent and a tight-aggressive persona at
  50 to 60. Provenance triple per §5a: format **9-max full ring**, pool **online
  micro-to-low no-limit cash, NL2–NL25**, sources **S1** (a full-ring
  micro-stakes specialist publishing 6-max and full-ring values side by side,
  fold-to-flop-c-bet 60 in both) and **S4** (the HM2 official forum's full-ring
  "normal" band, 40–70), corroborated on level by **S3** (42–57) and **S5**
  (~40). Status VERIFIED, confidence LOW, per-archetype band edges DIRECTIONAL.

**The measurement that makes it live rather than theoretical.** Sweeping the
nit's calling dial on the balanced-villain fixture, its half-pot bluff-catcher
fold rate rises as the dial falls and the α headroom runs out:

| nit `call_looseness` | fold at ½-pot | α headroom |
|---|---|---|
| 0.45 (before this slice) | 0.2680 | +0.0653 |
| 0.38 | 0.2896 | +0.0437 |
| **0.32 (shipped by S3-T2)** | **0.3136** | **+0.0197** |
| 0.31 | 0.3312 | +0.0021 |
| 0.30 | 0.3360 | **−0.0027 (breach)** |

At the shipped 0.32 the nit's aggregate fold-to-continuation-bet reading is
0.435 against a band floor of 0.60. **The dial runs out of admissible travel 16
points short of the band**, so no retune of this lever can reach it.

**Why the two are not simply reconcilable by "different opponents".** The α test
and the contract row are already scoped to different populations on purpose —
α to a balanced bettor, the contract row to real pools that continuation-bet 55
to 70 percent of flops — and the α test's own docstring says so. That
reconciliation works at the LEVEL of a single node. What it does not resolve is
that the same engine produces both readings from one merit vector: the calling
dial is the only lever the roster has on either, and pushing it far enough to
satisfy the contract row pushes the balanced-villain node through α.

**Severity MEDIUM, and what would change it.** Nothing is currently breached and
no gate is red; the conflict binds only a future slice that tries to close the
fold-to-continuation-bet gap with this lever. It becomes HIGH if a slice is
tasked with reaching the contract's band.

**What a re-anchor slice has to decide.** Either the contract's per-archetype
band edges are re-anchored for the tight archetypes (they are already recorded
as DIRECTIONAL and LOW confidence, so this is admissible), or the roster gains a
second lever that folds to continuation bets without moving the bluff-catcher
node — the fold merit at a facing node is `_FOLD_BASE[bucket] *
_price_factor(...)` and consults neither the draw nor the archetype's read of
the bettor, which is where such a lever would live.

---

## Filed 2 — The LAG's went-to-showdown floor, withdrawn

**Filed by S3-T2, 2026-08-22, under owner ruling 11 of that date.**

**What was withdrawn.** S3-T2 pre-registered a reduction floor for the LAG and
withdrew it before building. The LAG's pack is unchanged by this ticket.

**Why.** The LAG's went-to-showdown reading on the band harness is not a
function of the LAG's own dial; it is a function of the whole roster's dials,
and the cross-persona term is the same size as the own-dial term. Measured
against this branch's 0.5664 baseline: tightening only the nit and the TAG moves
the LAG UP 1.05 points; adding a LAG cut to 0.48 moves it 0.38 points DOWN;
cutting the LAG to 0.42 moves it 2.77 points down but hands 2.87 points back to
the TAG, which is nearly half of what the TAG's own retune just won. The
mechanism is the `rscale` coupling: the dial scales the whole continue side of a
facing node, RAISE included, so a tighter persona also raises less, and everyone
it faces meets less aggression and folds less in response.

**Where the reduction has to come from instead.** Per the pre-registration's §4
measurement (`../research/slice3-calldown/t2-preregistration.md`, reproduced by
the theory review), 41.6 percent of the LAG's showdown hands never face a wager
at all, and the ones that do face about one. That is the checked-down path — how often a hand reaches
the river with no bet in it — and no calling dial reaches it. It needs its own
ticket and its own mechanism.

---

## Filed 3 — `_DRAW_FREE_RIVER_PROB` stays at 0.30

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

**The contract row that owns it** is theory contract §4, row **P6/F7
draw-bonus equity gate** — "a SEPARATE lever from the fold-side brake: gate
`_DRAW_CALL_BONUS` itself by commitment, equity and nutness at high `c`", status
DIRECTIONAL. Any slice that re-derives this constant re-derives it against that
row, and against the went-to-showdown statistic the constant's own comment names
as the thing it serves.
