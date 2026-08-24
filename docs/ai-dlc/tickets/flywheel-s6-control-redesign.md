# Ticket: S6 control redesign — a manipulation check judges can actually catch

**Status: CLOSED 2026-08-23 — SUPERSEDED, its recommended design already shipped.** The
phase-3 gate ruled A (fix the bots) on 2026-08-15, and the same day's consolidated
amendment (estimand contract §g.5 clause A) replaced the control with exactly this
ticket's candidate 1 — a rule-breaking scripted bot — implemented in PR #184 and
probe-validated 2026-08-15 (judged `bot` at confidence-human 3 with its tells named,
while the old T1 control read `human` 62). The §g amendment recording the reversal this
ticket required exists (§g.5 A states it was ratified after seeing judge output). Nothing
here remains to build; kept for the design analysis below. Readiness state for the
finale run: `docs/ai-dlc/research/slice3-calldown/finale-readiness.md`.

*(Superseded original status, kept for provenance:)* ~~BLOCKED behind the phase-3 gate
(fix-vs-overhaul, owner decision).~~ This
ticket exists so that IF the gate keeps blind-detection rate as a metric, re-running the
S6 pilot is a build task with a settled design, not a research question. Do not start it
before the gate rules; the gate may instead retire the metric, which closes this ticket
unstarted.

## The problem (one paragraph)

The S6 detection pilot's validity rule (estimand contract §d.2) requires the judge panel
to catch a planted control bot: 4 of 4 judges must label it `bot`, else the batch is
invalid. The shipped T1 control — the most degenerate configuration the frozen dial
registry can produce (decision-level degeneracy 0.54, i.e. it folds 54% of non-post
decisions and otherwise plays normally) — was judged `human` twice at the 2026-08-14
pre-screen, the second time by a full-reasoning-effort frontier judge that explicitly
noticed the mechanical tell ("always 3x opens") and still read it as a disciplined human
regular. Evidence: `poker-analytics:docs/methods/detection-pilot-s6.md` §5 and §7. Any
full run under this control is near-certain to be invalidated, so the pilot cannot
execute as designed.

## What was already rejected, and what reversing it costs

The original spec (`docs/ai-dlc/specs/flywheel-s6.md`, appendix) considered and rejected
a bespoke non-dial control generator (extra amendment machinery) and an axis-registry
extension (registry frozen, out of appetite), accepting the weak T1 control with its
pre-screen as the safety valve. The valve worked — it cost cents, not dollars. Building
a stronger control therefore REVERSES a recorded decision and requires a §g amendment
recording that reversal, its rationale, and the fact that it was made after seeing a
judge's output (a researcher degree of freedom; the disclosure chain already starts in
the write-up's §5).

## Candidate designs, ranked by evidentiary value per unit of work

1. **Rule-breaking scripted control (recommended candidate).** A small bespoke generator
   that violates poker logic outright rather than merely being degenerate: e.g. calls
   with dominated hands it should never continue with, bets into made boards it cannot
   beat, identical bet size on every street regardless of pot, instant showdown-losing
   bluffs at fixed intervals. Rationale: the shakedown showed statistical uniformity
   reads as discipline; a control must instead be *illogical*, because poker illogic is
   what a competent human judge cannot rationalize as a style. Cheap to build (single
   scripted policy, reuse the existing self-play + renderer path), and its obviousness
   can be pre-tested with the existing pre-screen mechanism at ~1¢ per probe.
2. **Graded control ladder.** Two or three controls of increasing obviousness (T1 →
   uniform-sizing bot → rule-breaker), all judged in the pre-screen phase before spend.
   More build + more §d surgery (the validity rule is written for one control), but
   converts the binary manipulation check into a sensitivity floor for the instrument —
   directly answers the phase-3 sensitivity question rather than just passing a gate.
3. **Amend the validity rule instead of the stimulus.** Keep T1, weaken §d.2 (e.g.
   majority instead of 4-of-4, or confidence-based). NOT recommended: it rescues the
   batch by lowering the bar the instrument just failed, which is indistinguishable
   from motivated reasoning after a miss — the §5 disclosure would say exactly that.

## Acceptance criteria (for whichever design the amendment adopts)

- [ ] The §g amendment records: the T1-rejection reversal, the post-output timing, and
      the chosen design's exact generator config (hash-pinned like T1 was).
- [ ] The new control passes the existing one-judge pre-screen at provider-default
      effort BEFORE any panel spend (the mechanism that caught this problem stays).
- [ ] Deck rebuild keeps the pinned master seed and the 40/40 class structure; only the
      control bundle changes (verify `counts` and `non_protocol` in `_SUCCESS`).
- [ ] The write-up's §5 chain is extended, not rewritten — the 2026-08-14 shakedown
      record is immutable history.
- [ ] Cost estimate refreshed against live pricing at execution time (adapter changes of
      2026-08-14 mean thinking tokens are now a real output-cost line for Anthropic
      slots).

## Explicitly out of scope

Re-running the pilot (owner-gated, and the 2026-08-13 "run it when there is a changed
bot worth measuring" ruling still governs timing) · touching the frozen dial-axis
registry · any change to blinding, judge count, or the §d.3 prompt.
