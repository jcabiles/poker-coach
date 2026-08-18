# Ledger — invest-then-fold (phase-3 ruling A, improvement slice 2)

**Bottom line: the spec was reviewed before any code was written, and review
replaced its central proposal. The first draft's fix was withdrawn, two of its
numbers were wrong, one of its exclusion reasons was backwards, and both tickets
that survive were supplied by reviewers. This file records that rather than
presenting the final spec as if it arrived that way.**

Spec: `../specs/phase3-invest-then-fold.md` ·
Tickets: `../tickets/phase3-invest-then-fold.md` ·
Evidence: `../research/slice2-invest-then-fold/measurements.txt`.

## How the review was run

Two reviewers, deliberately asymmetric, because the 2026-08-17 audit found that
the reviewer given evidence without a conclusion caught more than the one given
a conclusion to critique.

- **Sealed derivation (Codex Sol, high effort).** Given the statistic's
  definition, the measurement output, and the code. Given no conclusion, no
  spec, and no hypothesis. Asked to find the node itself.
- **Adversarial (Opus, the persona-realism theory reviewer).** Given the draft
  spec and tickets and asked to break them, with the poker theory named as the
  most valuable thing it could challenge.

Both ran against the same 50,000-hand export at `d619535`, seed 20260817.

## What each reviewer found, and what was done about it

### Accepted, and it changed the slice

| # | Finding | Source | Adjudication |
|---|---|---|---|
| 1 | The money goes in as a **call** 59.6 percent of the time, a raise 24.0, a bet 16.4. The draft's two tickets targeted only the 40 percent. | Sol | **Accepted.** Verified independently from the export before acting on it — the split reproduces exactly. The draft's aim was wrong. |
| 2 | The smallest useful change is extending the existing naked-ace float damp from "facing a raise" to "facing a raise or multiway", with a measured counterfactual: 2,015 → 1,879 events, showdown flat, all-in hands down 201. | Sol | **Accepted and reproduced.** Re-ran the counterfactual independently on the same seed and got the same 1,879. It is now ticket T1, with the number pre-committed as an acceptance criterion. |
| 3 | At an all-in refusal a **raise is not legal** (`table/engine.py:204-206`), so with the river call merit already zeroed the bot has exactly one weighted action. | Opus | **Accepted, and it became the spec's headline.** Measured the consequence: 950 events, 47.1 percent of the statistic, are folds at probability 1.000. Determinism, not fold rate, is the tell. |
| 4 | The draft's evidence for bottom-bucket price saturation — "100 percent of events are in `SMALL`" — is a **tautology** of its own filter, since pot odds of 5:1 force the faced fraction below 0.25. | Opus | **Accepted and retracted in place** as spec §1.7. The code fact survives; the evidence for it did not. |
| 5 | The draft's stated reason for excluding a sub-`SMALL` price fix — that it would make air jam the river — is **refuted** by finding 3. With no legal raise it is an exact no-op there. | Opus | **Accepted.** The exclusion stands on different, honest grounds; the wrong reason is recorded rather than swapped out silently. |
| 6 | The `bluff_cell` predicate bundles ACE_HIGH with AIR although the rule's own comments say only "air", so 659 of the 985 hard-zero events are ace-high — a legitimate river bluff-catcher. | Sol and Opus, independently | **Accepted.** Promoted out of the exclusions into spec §6 as an owner decision, with the showdown cost split by holding: up to +3.66 points for the ace-high half alone. |
| 7 | Arithmetic: the calling personas' events are **851, 42.2 percent**, not the draft's "1,105, 55 percent". | Opus | **Accepted.** Straightforward error, corrected. |
| 8 | The binding separation pair is **LAG–TAG at 1.7920**; maniac–LAG is 3.7247 with a preflop-only component of 2.774, so the gate cannot see maniac damage. The draft named the wrong risk. | Opus | **Accepted.** Both tickets now require the LAG–TAG distance reported explicitly, not just the PASS line. |
| 9 | `--seeds 5` is not a real flag; the runner takes `--all-seeds`. | Opus | **Accepted.** |
| 10 | `_bluff_size_factor` is applied to the **authored** pot-fraction key while the bet is stack-clamped afterwards, so a short-stacked bot sets its bluff frequency for a bet it cannot make. | Opus | **Accepted.** Verified the two call sites. This became ticket T2, replacing the draft's own aggression lever. |

### Accepted with a bound rather than as stated

| # | Finding | Adjudication |
|---|---|---|
| 11 | Damping the bluff raise sends freed mass to FOLD at a node that satisfies the counted definition, so the ticket manufactures the statistic it targets. (Opus, measured at a synthetic node: maniac fold 0.575 / call 0.0 / raise 0.425.) | **Real but small, and largely self-limited by finding 3.** In the live 50,000 hands only 29 bluff-cell raises meet the counted precondition, 8 on the river, against 2,015 folds — because at 94 percent of the events no raise is legal. The probe node was one where the villain's bet was not all-in. Recorded as a bounded caveat in T2, worth 1.4 percent at absolute worst. |
| 12 | The "58.5 → 64.6 percent" showdown figure assumes 100 percent of folds convert to calls. | **Accepted as a labelling fault.** It was always an upper bound; it is now labelled as one everywhere it appears, and split by holding so the ace-high half can be priced separately. |

### Not accepted as stated

| # | Finding | Adjudication |
|---|---|---|
| 13 | The draft's commitment damp is **backwards poker** — real players bluff *more* when short relative to the pot, because a 20bb shove into a 258bb pot needs only about 7 percent fold equity. | **The lever was withdrawn, but not on this ground, and the poker is not settled here.** Both readings are defensible: a cheap bluff needs little fold equity, and a bluff into opponents who are already all-in has none to buy. The draft treated "short means bluff less" as settled and should not have. Ticket T2 sidesteps the question entirely by correcting an existing calculation instead of adding a lever, so this spec takes no position — which is the right outcome for a disagreement this live. |
| 14 | The reviewer's own alternative framing of the whole slice: its realism ceiling is near zero regardless, because the dominant defect is arrival and ruling A puts arrival out of reach. | **Half accepted.** The ceiling point is right and is now spec §9's first risk, stated plainly. But T1's measured 6.7 percent with showdown flat is not nothing, and "the ceiling is low" is an argument for expecting less, not for building nothing. |

## What the author got wrong, for the record

Six things, all caught by review or by checking rather than by reasoning harder:

1. Aimed the slice at the 40 percent of the money and missed the 60 percent.
2. Proposed a lever with no measured effect over one that had already been
   measured.
3. Presented a tautology as evidence (§1.7).
4. Gave a wrong reason for an exclusion, and the wrong reason would have kept a
   real fix out.
5. Added 648 + 176 + 27 to 1,105.
6. Named the maniac as the archetype-separation risk when the gate is
   structurally incapable of seeing maniac damage.

The pattern matches the 2026-08-17 audit's: the errors were not in the
measurements, which held up under two independent checks, but in the causal
stories built on top of them.

## Owner ruling, 2026-08-18 — the river call hard-zero

**Ruled: remove ACE_HIGH from the river call zero, keep AIR. Ticketed as T3.**

The spec first presented this as three options with no recommendation, on the
grounds that it traded the north-star metric (detection) against the inner-loop
one (showdown frequency). **That framing was wrong and the author corrected it
when asked to lay the options out in full.** The trade is not symmetric, because
one option is justified by poker theory independently of the realism goal:
ace-high is a river bluff-catcher and calling with it sometimes is simply correct
play. A change defensible *only* as "makes detection harder" is what the
roadmap's Goodhart guard exists to catch; this one is not in that class, and that
is what breaks the tie.

Recorded as a general principle for later calls in this phase: **when a realism
change is also independently correct poker, it is categorically safer than one
that is only realism-motivated, and that difference should be surfaced in the
options rather than left for the owner to notice.**

The rejected options, for the record. Leaving it alone costs nothing but ends the
improvement phase without touching the diagnosis's largest finding. Giving both
air and ace-high a small non-zero call merit breaks the determinism everywhere at
up to +6.1 showdown points, and makes bots call river bets with total garbage —
the named Goodhart failure.

## Contract scan, 2026-08-18 — two ticket amendments

A read-only scout mapped the callers, tests and downstream consumers of the three
touch points after the tickets were written. Full map:
`../contracts/phase3-invest-then-fold.md`. Two findings changed the tickets.

**T1 removes a safety property that only a comment asserts.**
`personas_postflop.py:253-258` argues the naked-ace damp is safe *because* it is
gated on facing a raise, so it never touches the facing-a-bet curve the α-ceiling
contract measures. T1 extends it to facing-a-bet multiway — precisely the case
the comment excludes. The guarding test hardcodes one opponent and will keep
passing while the claim stops being true. T1 gained an acceptance criterion:
re-measure the property at two and three opponents, and rewrite the comment.

**T2's tripwire fails in a way that looks like routine maintenance.**
`test_price_tail.py:301` asserts exact equality against frozen vectors encoding
stage one of the two-stage bluff-size law, and its own docstring says bet-size
tickets are expected to move them. A genuine stage-1/stage-2 mismatch therefore
presents as an expected re-record. T2 gained two criteria: move both stages
together, and justify any vector movement from the joint law rather than
re-recording it.

Also confirmed, and worth recording because each was checked rather than assumed:
SRS history cannot be orphaned, the grader is uncoupled, the bet-size grid is not
engaged, and estimator parity for T1 and T3 is structural rather than merely
tested. Against that, no estimator test can ever catch a T2 fault, because the
sizing draw never executes under estimation.

**Process note.** The scout was briefed to write the map itself and had no write
tool, so it returned the content and the session persisted it. The brief was
wrong, not the agent.

## Still open at the time of writing

- The roadmap's slice 2 entry still names a refuted mechanism, its slice 3 entry
  does not know 851 of these events are its own, and neither knows about T3. Not
  edited here — the roadmap edit is the owner's to ratify.
- No ticket is implemented. This slice is spec and tickets only.
