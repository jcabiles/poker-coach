# Consolidated pre-finale amendment — DRAFT for §g ratification (one amendment, then freeze)

**Bottom line: every protocol change the phase-3 plan needs is gathered here as ONE
amendment, to be recorded in `poker-analytics:docs/methods/estimand-contract.md` §g on
owner ratification and then frozen until the finale. Consolidating preserves the
record's strongest property — after this amendment, nothing changes between amendment
and finale. Timing disclosure: this draft was written AFTER the 2026-08-14 shakedown
verdicts were seen; every clause below is a decision made with knowledge of judge
output, and says so.**

## A. Control replacement (reverses a recorded rejection)

*Modifies:* §d.2's control clause (the per-batch manipulation check pinned to the T1
best-effort dial config).

The finale deck contains exactly ONE control bundle, as §d.2 already pins — but the
stimulus changes: the **rule-breaking scripted bot** (engine-legal, strategically
illogical: calls with hopeless holdings, bets into boards it cannot beat, fixed
nonsense sizings), implemented as a custom action policy in `backend/tools/` (probe/
experiment code stays out of the product domain core) driven through the normal hand
loop; generator config hash-pinned in this amendment at ratification. Deck composition
and class balance (40/40 + 1 control) are unchanged.

The **T1 dial control is NOT in the deck.** It is retained solely as a pre-screen-phase
sensitivity diagnostic (judged outside the deck, in the probe/pre-screen output tree):
its verdicts are recorded as a marker of where the judges' discrimination threshold
sits, never as batch validity.

**Disclosure (post-output decision, per §g convention): the original spec rejected a
bespoke control generator on appetite; that rejection is reversed here, after seeing
the 2026-08-14 shakedown verdicts. The §5 chain records the sequence.**

## B. Bot-class construction for the finale deck (closes the ecology confound)

*Modifies:* §d's bot-class generation description (self-play under the production
roster).

**One matched ecology, pinned: shipped packs everywhere except the judged seat.** The
human class remains the existing owner corpus (sessions played against shipped-pack
villains). Bot-class bundles therefore also run shipped packs on all eight background
seats; the improved policy applies to the judged focus seat ONLY. Both classes' table
ecologies match; the improvement is isolated to the seat under judgment.

Fresh owner hands (~30+, played against the final roster) are **calibration-only
stimuli — never deck material** (they would import the improved-ecology mismatch into
the human class). The rebuilt finale deck's human bundles are verified byte-identical
to the shakedown build's where the recorded pins allow.

## C. Pre-screen strengthening

*Modifies:* §g.2's one-judge control pre-screen (operational spend-stop).

The control pre-screen runs on ALL FOUR judge slots (not slot 0 alone) immediately
before the finale. Ownership pinned: **these four calls ARE the finale run's control
checkpoints** — they execute inside the finale's own NEW launch/output tree (the
2026-08-14 shakedown tree is closed history, never reused), so the pre-screen responses
are the finale's control responses of record, §g.2-style. The 4 preflight calls are
accounted separately as connectivity checks. Before these calls: provider-resolved
model IDs are diffed against the shakedown's launch manifest; any rotation is recorded.

## D. Single-finale pre-commitment

*Modifies:* §d's "executes once" clause — sharpens it to an explicit optional-stopping
guard.

Exactly one finale run. If its result is unfavorable, the pre-written claim ladder (§F)
is used as-is; a second run would require a further recorded amendment, written before
it fires, disclosing what changed and why a re-run is not outcome-shopping.

## E. Believability acceptance — two preregistered instruments, separate claims

1. **Detection finale (text instrument):** measures whether text-judges distinguish
   bot from human hand histories. Its claims live in §F's ladder.
2. **Owner blind play-test (interactive instrument, product acceptance):** exact
   design, pinned before any improvement ships:
   - **N = 8 sessions**, each ≥30 hands. Per-session roster (improved vs pre-fix,
     frozen at the pre-fix state recorded in this amendment) assigned by a seeded
     coin flip (seed pinned at ratification); assignment concealed until after the
     session's written verdict is committed.
   - Owner records per session, before unblinding: believed roster + every specific
     tell noticed.
   - **FAIL on identification:** owner correct on ≥7 of 8 sessions (one-sided
     binomial, p≈0.035 under chance — the owner can genuinely tell them apart).
   - **FAIL on tells:** any mechanical tell named in ≥2 improved-roster sessions.
   - **PASS:** neither failure condition fires. PASS here is the "believable enough"
     verdict for the product goal.

## F. Claim ladder (pre-written, §8-compliant — the chapter may claim no rung higher
than the evidence reaches)

*Modifies:* nothing in §d — this constrains the write-up per §8's interpretation rules.

1. **Floor (always claimable, non-inferential):** the protocol's execution narrative —
   what ran, what the validity machinery decided, spend, disclosures. Inferential deck
   statistics appear ONLY on a valid completed batch (consistent with §7's fail-closed
   suppression); on an invalid batch the floor reports diagnostics and completeness
   alone.
2. **If batch valid + detection ≈ chance** (defined: the balanced-accuracy 95%
   percentile-bootstrap CI includes 0.5): "judges failed to distinguish these bots
   from this player's play at 30-hand exposure" — explicitly NOT "the bots are
   human-like" (§8 pins low detection as weak evidence; the play-test carries the
   product claim).
3. **If batch valid + detection above chance** (CI excludes 0.5): report the measured
   rate and per-judge diagnostics as the honest finding; the improvement story stands
   on the before/after defect evidence, not the detection number.
4. **If batch invalid (control missed by the panel):** the instrument result is
   reported as a second shakedown; the play-test alone carries believability.

## G. Agent-execution scoping (records the owner's operational ruling)

Preregistered deck judging: owner-only, real terminal, unchanged. Off-deck dev probes
(stimuli never drawn from the frozen deck, separate deck/output directories, stub-vendor
dry-run first): agent-runnable under this recorded deviation, budget-capped per episode
(probe episode 1 cap: $0.40), every call and verdict logged in the ledger. Key file
`~/.config/s6-probe-keys.sh` is temporary; deleted and keys rotated at probe-phase end.

## Ratification record

- [x] Owner ratified A–G as one amendment — date: **2026-08-15** · recorded in
  estimand-contract.md §g as: **(g.5) Amendment 2026-08-15-A** (which
  incorporates this document by reference; this file is the full text of record)
