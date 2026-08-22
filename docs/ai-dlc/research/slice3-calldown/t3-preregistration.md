# S3-T3 pre-registration — the stack-to-pot value lever, registered before it was wired

**Bottom line. This file was written and committed BEFORE a single line of the
multiplier existed, so that the direction it predicts can be checked against the
measurement rather than fitted to it. The prediction: at decisions where the
seat's stack stops it making its own biggest authored bet size, damping made-hand
betting will move betting probability into checking for made hands only, leave
bluff-cell betting untouched, and so raise the bluff share of the betting range
at those decisions toward the level it already has where the stack does not bind.
The named risk, registered here rather than discovered later, is the LAG's
went-to-showdown ceiling: turning bets into checks sends hands to showdown, and
the LAG sits at 0.5769 against a ceiling of 0.59.**

S3-T3 is ticket 3 of improvement slice 3 (the calldown slice) of the bot-realism
flywheel. "Stack-to-pot ratio" (SPR) is the seat's remaining stack divided by the
current pot. "Made value" means a hand of middle pair or better. A "cap-exposed"
decision is one where the seat cannot wager its largest authored pot-fraction,
because the legal bracket's maximum is below it.

## 1. The instrument, and why it had to be built

Acceptance criterion 1 of the ticket asks whether cap-exposed composition moves
toward the uncapped norm. **No instrument in this repository measured that.** The
contract map for this ticket
(`../../contracts/flywheel-slice3-t3-valueside.md` §2) searched the test file,
the de-robotization gate and the analytics export and found nothing; the only
prior implementation lived in a design dossier that modified no repository file.

So this ticket builds one: `backend/tools/capped_composition_probe.py`. Its
design decision, registered here, is that **the primary comparison carries zero
sampling variance**. At every postflop decision of a seeded playout the probe
reads the sampler's normalized action-probability vector twice — once with the
lever off, once with it on — using the capture-rng pattern
(`backend/tests/node_trace.py`) that records the weights of the action draw
without disturbing it. The two readings are taken at the *same node*, so the
difference between them is the policy's exact response, not a sample of it. The
realized action counts of the two arms are reported alongside, and those do carry
sampling noise, which is why they are pooled across three seeds and never read
from one.

## 2. Registered directions

Each is a claim that can fail.

1. **Made-hand betting falls at cap-exposed decisions and the freed mass goes to
   checking.** The lever multiplies the aggressive candidate only, so under the
   softmax normalization every point it removes from betting appears at checking.
2. **Bluff-cell betting does not move at all, at any decision.** The lever is
   gated to made-value buckets, so an air or ace-high hand with no draw never
   reaches it. If `HEAD_VECTORS` in `backend/tests/test_price_tail.py` moves, the
   scope is wrong.
3. **The bluff share of the betting range rises at cap-exposed decisions**, and
   rises there by more than anywhere else — which is the direction acceptance
   criterion 1 asks for, because the design dossier measured cap-exposed nodes at
   0.960 of the roster's own bluff-share calibration, i.e. below it.
4. **Everything at a stack-to-pot ratio at or above the persona's `spr_commit` is
   bit-identical**, because the ramp returns exactly 1.0 there and multiplying by
   exactly 1.0 is the identity in floating point.
5. **The lever fires on a superset of cap-exposed decisions, and that is
   deliberate.** The ramp is keyed on `spr_commit` (1.2 to 3.3 across the six
   packs), while a decision is cap-exposed only below the largest authored size
   (1.0 for five packs, 1.5 for the maniac). Between those two the lever applies a
   partial damp at decisions that are not cap-exposed. Registered as an accepted
   side effect and measured, not claimed to be absent.
6. **Went-to-showdown rises**, because a bet that becomes a check leaves more
   hands alive to showdown. The LAG is the exposed persona at 0.5769 against a
   ceiling of 0.59, and it also has the second-widest ramp (`spr_commit` 3.0).
   **If the LAG breaches 0.59 the floor is raised toward 1.0 until it does not** —
   the ceiling is not moved, per ruling 5.
7. **Magnitude.** A weight multiplier of `x` on a two-way choice at probability
   `P` moves the frequency by about `(1 − P)·(x − 1)`. At the dossier's seed floor
   of 0.88, fully committed, that is at most 1.5 to 4 percentage points of betting
   probability depending on bucket and persona, and well under one point pooled
   over all decisions. **A change this small is why criterion 1 is registered as a
   direction with a zero-variance instrument, and not as a threshold.**

## 3. What would make this ticket ship a smaller lever than the dossier's seed

Registered in advance so that a reduction cannot be presented as the plan all
along: the floor moves up from 0.88 (a weaker damp) if, and only if, one of the
following fires — the LAG's went-to-showdown crosses 0.59, another persona
crosses its ratcheted ceiling, an aggression-factor or fold-to-continuation-bet
band leaves its range, a hard went-to-showdown ordering leg breaks, or the
five-seed de-robotization gate's separation floor binds. The separation floor
binding is a stop-and-report, not a retune (ruling 3).

## 4. What would make it a finding rather than a lever

If the probe shows the cap-exposed composition defect is smaller than one
percentage point, the honest report is that the defect is below the size of the
lever's own side effects. In that case the lever still ships — the ticket asks
for the value side to stop being a constant — but at a conservative floor, with
the measured smallness recorded as the headline rather than buried.

---

## Postscript, 2026-08-22 — the registered text above is unedited, and the lever it registers was withdrawn

**Nothing above this line has been changed.** A pre-registration that is edited
after the result is not a pre-registration, so the record stands as written,
including the parts the measurement and the review went on to contradict.

**What happened.** Every registered direction in §2 was measured and every one of
items 1 through 5 held. The lever was still WITHDRAWN, on a design flaw none of
those directions could have caught, because §2 registered only whether the lever
would move the statistic it was aimed at — never whether moving that statistic
was the right thing to do to a poker bot.

**The three things this pre-registration got wrong, recorded so the next one does
better:**

1. **It registered a direction for the statistic, not for the POKER.** Damping
   made-hand betting as the stack shortens makes a bot bet marginal made hands
   less often exactly when commitment says it should bet them more. §2 item 7
   sized the effect and §3 listed the guards that could stop it; neither asked
   whether the sign was right. A registered direction should include the
   behavioural claim, not only the metric claim.
2. **It took the target's shortfall at face value.** The registered premise was
   the design dossier's finding that capped decisions sit below the roster's
   bluff-share calibration. That reading was RAW — not normalised by
   `s/(1+2s)` at the size the wager was actually made at — and capped wagers are
   smaller by construction, so part of the shortfall is what the identity asks
   for rather than a defect. **A pre-registration that inherits a target from a
   prior document must re-derive that target before registering against it.**
3. **§4's "if the defect is small, ship at a conservative value" was an escape
   hatch.** It pre-authorized shipping regardless of what the measurement said,
   which is the opposite of what pre-registration is for. The honest form names
   the finding that would make the lever NOT ship — and here that finding
   existed: the value side's betting frequency being flat in stack depth is
   evidence for a commitment SLOPE, and evidence against a damp.

**Where the outcome is recorded:** `t3-report.md` (measurements, the reviewers'
merit-vector finding, and the withdrawal), theory contract §3 amendment A8
(the limits, and the open item this turned up), and
`../../ledger/flywheel-slice3-calldown.md` filed items 5 to 7.
