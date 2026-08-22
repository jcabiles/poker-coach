# Ledger — invest-then-fold (phase-3 ruling A, improvement slice 2)

**Bottom line, updated 2026-08-21: the slice is CLOSED.** The owner played the
blind play session and the verdict was acceptance — see the close-out entry at
the bottom of this file. *(Superseded text below, kept for provenance — it was
accurate when written and describes the build, which did not change at
close-out.)* ~~the slice shipped three pull requests and two behaviour changes.
Naked ace-high stopped floating multiway bets (#198) and may call the river again
at a damped weight (#200); the third ticket's repricing was measured, found to
move the roster away from the target it was meant to serve, and withdrawn on the
owner's ruling, shipping a test instead (#199). Review, not the test suite, is
what caught everything that mattered: all three tickets shipped stale or false
claims past a fully green suite. The slice is NOT closed — the owner's blind play
session is the primary acceptance evidence and has not happened.~~

This file is chronological. The spec review comes first, then the contract scan,
then one build round per ticket, then the filed items and the close-out. The
close-out at the bottom is the current state; anything above it is a record of
what was true when it was written.

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

## Third review round, 2026-08-18 — the lineup error

**Both reviewers independently found that every count in this slice was measured
on the wrong table.** The diagnosis never passed `--lineup`, so it used the
exporter's alphabetical default — two calling stations, two LAGs and two maniacs
— while the gate, the frozen baseline artifact and the 2026-08-05 re-measure all
run the ratified nine seats: three TAGs, two passive fish, one each of the rest.
`../reports/flywheel-s4-acceptance.md` states the default is not ratified, in
those words.

Re-measured on the ratified lineup at the same seed. **Every mechanism finding
survived; every count changed.**

| | default (as shipped) | ratified (correct) |
|---|---:|---:|
| events | 2,015 | 1,147 |
| deterministic folds | 950 (47.1%) | 524 (45.7%) |
| river hard-zero cell | 985 (48.9%) | 550 (48.0%) |
| all-in refusals | 94.0% | 92.7% |
| hands with an all-in | 30.9% | 20.2% |
| money in as a call | 59.6% | 62.3% |
| pool went-to-showdown | 58.5% | 54.5% |
| T1 counterfactual | 1,879 (−6.7%) | 1,084 (−5.5%) |

The pre-committed acceptance number in ticket T1 was wrong as a result. The
diagnosis script now reads the export's `_SUCCESS` manifest, prints the lineup,
seed and engine SHA it ran on, and says whether that lineup is the ratified one.

**A second number was wrong, in the roadmap rather than here.** Slice 3's entry
says the roster's went-to-showdown is "near 45". That figure is 44.92 from the
S5 close-out, where it is a *counterfactual* with the maniac's showdown rate
driven to zero. The roster's actual value is **54.85**, recorded in
`poker-analytics/analysis/output/score-campaign2-august-F1.json` as
`canonical.pool_tier` with counters 59,907 over 109,214, on the ratified lineup
at seed 20260805 — the 2026-08-05 run itself. The cutoff needs roughly 42.7, so
the ceiling gap is twelve points rather than two. Slice 3 is still the largest
available move on it and still cannot close it. That correction belongs to the
roadmap and is filed separately.

### Other findings from this round

| Finding | Adjudication |
|---|---|
| "851 events belong to calldown" does not follow from persona membership — the conditional rate is flat across all six personas, and T1 already reduces those personas. | **Accepted.** The claim is removed. Spec §6.2 replaces it with a boundary drawn on the defect: slice 2 owns degenerate or mis-invested decisions, slice 3 owns continuation frequency at nodes that already mix. That boundary survives T3, which the earlier showdown-based version did not, and it assigns the ownerless draw-floor entry to slice 3 as a prerequisite. |
| The determinism finding is oversold if offered as something the finale judge will catch. 524 of 450,000 seat-hands is 0.03 events per 30-hand bundle. | **Accepted.** Both spec §6 and ticket T3 now say the direct detectability is absent and rest the case on the poker and on consistency with slice 1. |
| "84 percent of folds are correct" is a post-hoc check against the real board, not against what the bot could know, and risks reading as an acquittal. | **Accepted.** §1.3 now states both limits and names the residuals: the 16 percent that clear the price and the 264 made-pair folds. |
| T2 and T3 both act on the `bluff_cell` hand class, so calling them independent is too strong. | **Accepted with a bound.** They touch different lines and merge cleanly; their measured effects interact. The ticket now requires whichever lands second to re-measure rather than inherit its counterfactual. |
| The ceiling caveat asserted the environment causes the rate, which no counterfactual has tested. | **Accepted.** Restated as an inference. |

## Still open at the spec-review stage, 2026-08-18

Superseded by the build rounds and the close-out below; kept as the record of
what the slice looked like before any code was written.

- The roadmap needs six corrections, filed separately: slice 2's refuted
  mechanism and unrecorded status, slice 3's "near 45" figure, the missing LAG row
  in the baseline, a NOW banner that still calls both slices unspec'd, a
  self-contradiction over whether calldown is cut first, and an audit banner that
  says de-robotization touched preflop only four lines below slice 1's measured
  postflop change.
- T2 and T3 are not implemented. T3 additionally gained a hazard from T1's
  build round; see below.

## Build round — T1, 2026-08-19

**T1 shipped. It hit its pre-committed number exactly, and three independent
reviewers between them found four stale claims the implementation left standing
— the same failure class the ticket was written to prevent.**

The behavioural change is one predicate. Everything else in the pull request is
the safety work that predicate forces, and most of the review time went there
rather than to the change itself.

### What was measured

Events 1,147 → 1,084 at seed 20260817 on the ratified lineup, matching the
pre-committed acceptance figure to the digit, with every secondary number in the
ticket's table also matching. Two reviewers reproduced the full 50,000-hand
export independently rather than reading the author's output.

**One number the ticket's table does not carry: the nit rose**, 0.22 → 0.30
events per thousand hands, 11 → 15. It is the smallest sample in the table and
the only persona that moved the wrong way. Recorded because a table listing only
the three personas that fall would imply the roster moved uniformly.

### The gate, and a prediction that was wrong

**LAG–TAG moved 1.8469 → 1.9852 — apart, not together.** Spec §5 and ticket
acceptance criterion 3 both predicted this change would push the binding
separation pair together, and it did the opposite. The prediction was wrong in
the harmless direction, and the criterion that came from it — report the pair
explicitly rather than the PASS line — did its job anyway.

The second-closest pair moved the other way: nit–TAG 2.7293 → 2.5083, still well
above the 1.254429 floor. The determinism guard passes at 0.1556 against a 0.20
ceiling, label preservation is 6/6, and the LAG's frozen showdown band did not
breach.

### How the review was run

Three reviewers, all briefed to derive their own verdict from the code and the
data rather than to react to the author's conclusions — the asymmetry the
2026-08-17 audit recommended, now applied to all three rather than to two.

- **Codex Sol, high effort.** Verdict request-changes. Found three of the four
  stale claims.
- **The persona-realism theory reviewer, Opus.** Verdict GO. Found the fourth
  and sharpest, and refuted a realism worry by measurement.
- **The refuter, Sonnet at high effort.** Verdict pass. Re-ran the export and
  the gate arithmetic independently and confirmed the headline.

### Findings and adjudication

| # | Finding | Source | Adjudication |
|---|---|---|---|
| 1 | `personas_postflop.py:243-251` still says a 0.22 effective ace-high call base "stays REFUTED", quoting the fish arithmetic that refuted it. **T1 now ships exactly 0.22** (0.40 × 0.55) on every multiway flop/turn facing-a-bet node. | Theory | **Accepted; the sharpest finding of the round.** The refutation and the shipped behaviour had collided. The block is now scoped: a flat global cut stays refuted at every opponent count, and T1's multiway reach to 0.22 on that exact node is stated rather than left for a reader to discover. The fish arithmetic is kept — it is still the reason nobody may cut the global base. |
| 2 | Two comments in the test file are now false: `:6563` says both damps are gated on `facing_raise`, and `test_ace_high_facing_a_bet_is_byte_identical`'s docstring says nothing on that node moved. | Sol | **Accepted and verified independently.** Both rewritten. The legs beneath them remain correct only because the helper hardcodes one opponent, which is now stated as load-bearing rather than left incidental. |
| 3 | The implementation's own comment decrees that no α bound may be asserted on the ace-high bucket. That rules on a contract. | Sol | **Accepted on governance, not on the measurement.** The measurement is sound and is kept: naked ace-high already exceeded α at 15 of 24 cells at one opponent on the untouched engine, because it is not a bluff-catcher and `_CATCHER_BUCKETS` excludes it deliberately. But whether α should be asserted over the bucket at all is the owner's to rule, so the comment now reports and refers rather than decides. See the open item below. |
| 4 | Both re-record provenance notes claim the same number of rng draws is taken before and after. False: a CALL flipping to RAISE fires the already-existing conditional sizing draw. | Sol | **Accepted. The error was the orchestrator's**, introduced in the re-record authorization and copied into two files by the worker. Slice 1's actual rule — no new draw, and none before the action draw — is satisfied and is what the notes now say. |
| 5 | The α measurement covered `street=None` and FLOP but not TURN, although the predicate fires on both. | Sol | **Accepted.** Half the damp's surface was unmeasured. TURN added and the table regenerated. |
| 6 | No estimator parity test drives more than one opponent, so T1's new branch has no pin. | Theory | **Accepted as a missing test, not a live defect.** The reviewer verified parity holds structurally — the estimator replays the real `opponents` into the same sampler, and the capture RNG short-circuits downstream of the predicate. A multiway parity test was added anyway, because the whole lesson of this ticket is that an untested claim rots. |
| 7 | Two of the three new tests pass against the old predicate, so they are vacuous as evidence that T1 happened. | Sol | **Accepted with a correction to the framing.** They are negative scope guards and are supposed to hold on both tips; that is what a guard is. Only the claim that one of them "replaces" the deleted structural argument was too strong, since it guards a narrower property, and that wording is fixed. `test_naked_ace_high_multiway_bet_calls_less_than_heads_up` is the non-vacuous one and fails all twelve cases without the change. |
| 8 | The roster-compression worry: a calling station at looseness 4.0 and a nit at 0.45 receive the same flat 0.55 multiplier, which should push archetypes together. | Theory, raised and then answered by itself | **Refuted by measurement, and worth recording as a refutation rather than a non-finding.** P(call) spread across the roster *widened*, 0.508 → 0.547, and the max/min ratio went 2.41 → 3.32. The gate's minimum pairwise distance moved the same way. |
| 9 | Ticket criterion 3 and spec §5 say T1 "damps the LAG's 294 events and barely touches TAG's 82". | All three reviewers, independently | **Accepted; not fixed here.** The committed evidence file says LAG 124 and TAG 185, and the measurement says T1 removes more TAG (185 → 168) than LAG (124 → 114). The figures look like default-lineup survivors that the 2026-08-18 re-measure missed. Correcting a merged ticket is the owner's call. |

### What the author got wrong, for the record

Four stale claims survived a build whose entire sixth acceptance criterion was
"a comment left standing as a false claim is worse than no comment". Three were
in files the author had just edited. The instrument that caught them was three
reviewers reading the module for contradictions, not the test suite, which was
green throughout.

The orchestrator contributed two errors of its own: the rng-count claim in
finding 4, and an initial worker brief that forbade the slice re-record outright
and blocked the build until it was lifted.

### Open items from this round

- **Whether α should be asserted over the ACE_HIGH bucket at all.** The
  measurement says naked ace-high folds above α = f/(1+f) at most cells and did
  so before this slice, because it is not a bluff-catcher. The code now reports
  that and refers the question rather than settling it. Owner's.
- **T3 will strand T1's street gate.** The FLOP/TURN boundary is coherent today
  only because the river call merit is hard-zeroed for the whole bluff cell. T3
  removes that zero for ace-high and is explicitly told not to touch this damp —
  which would leave multiway river ace-high calling at full undamped weight, on
  the street where T1's own thesis is strongest. Not a T1 defect and not fixed
  here; it is input T3 must have before it is built.
- **Ticket criterion 3 and spec §5's 294/82 figures**, per finding 9.
- **The two standing price fixtures are blind to street-gated levers.**
  `fold_by_size` and `catcher_fold_by_size` both omit `street`, so they measure
  at `street=None`, outside any street gate. A first version of T1's α
  measurement copied them and produced before-and-after tables that were
  byte-identical — it measured nothing at all. Any future ticket touching a
  street-gated lever is invisible to both.

## Build round — T2, 2026-08-19 (merged as PR #199)

**T2's repricing does not ship. The build was completed, measured on the
identity the ticket cites, found to move the roster three standard errors away
from that identity's target, and withdrawn on the owner's ruling. What ships is
a test that can catch the villain-range estimator and the live sampler
disagreeing — something no test in this repository could do before — plus the
two docstrings that stop it being deleted by mistake. Engine behaviour at the
merged tip is byte-identical to the tip T2 branched from.**

T2 is the second of the slice's three tickets: pricing a bot's bluff frequency
on the bet its stack lets it make rather than on the bet its pack authored.

### What was measured, and what it showed

The ticket's premise is right per hand and wrong per range. Per hand, a seat with
20bb behind in a 258bb pot does price its bluff as though making a two-thirds-pot
bet and then make an eighth-pot one; nobody disputed that and it remains true.
But the theory contract does not state the bluff-share identity per hand. It
states that the optimal bluff share is `s/(1+2s)` **of the betting range**, so the
instrument is the realised composition of that range.

Measured that way — 40,000 hands per arm, ratified lineup, seed 601, the two arms
differing only in whether the repricing is active — the repricing moves
stack-capped nodes from 0.4762 of the identity's target to 0.4022, against the
roster's own uncapped calibration of 0.5168. In the small-bet band where the
ticket's worked example lives, the sign flips outright: 1.041 of target before,
0.839 after. The change in the capped-bet bluff share is 3.1 standard errors on
the two binomials. The full table is in PR #199 and is not repeated here.

**The cause is a missing lever, and that is a contract defect rather than a build
defect.** `_AGG_BASE` is indexed by strength bucket alone — seven entries, no size
term, no stack-to-pot term — so a value hand that would have bet two-thirds of the
pot bets an eighth of it just as often, and at capped nodes the commit block
raises the strong buckets' bet frequency further. Made-value hands bet 9.1 percent
*more* often where the cap is exposed, while the identity's target there is
smaller. The denominator of `s/(1+2s)` is enlarged exactly where the target
shrinks, so correcting the numerator alone moves the composition away from target
even though every gate passes.

No narrower version was available, and that is arithmetic rather than judgement:
`_bluff_size_factor` is monotone non-decreasing and the effective fraction is
never larger than the authored one, so the repricing can only ever lower a capped
node's bluff share — and the capped population already sat below the roster norm.
There is no subset of capped nodes where it pushes the composite up. Landing the
one band that starts above the norm would have required scaling by a fitted
constant, which the spec forbids.

### The gate

**Unmoved, because the merged tip changes no behaviour.** Minimum pairwise
separation at seed 601 is 1.985172 at both the parent and the merged tip, all
fifteen pairwise distances identical, 0 of 15 moved; LAG–TAG 1.9852; determinism
worst persona 0.155556. The invest-then-fold statistic and the 50,000-hand export
are byte-identical to the parent, and the three exact-count fixtures the build had
re-recorded were reverted and pass unmodified.

Worth recording because it nearly went unremarked: **while the repricing was live
it narrowed the binding separation pair by 12.9 percent**, 1.9852 to 1.729101, the
refuter recovering that figure independently from the pinned baseline artifact. It
still cleared the floor, so the gate would have passed a change that was moving
the roster the wrong way on the identity as well as on separation.

### How the review was run

Three reviewers, all briefed to derive their own verdict rather than react to the
author's, as in the T1 round.

- **The persona-realism theory reviewer, Opus.** Verdict NO-GO. Measured the
  range-level composition and produced the finding that killed the ticket.
- **Codex Sol, high effort.** Verdict request-changes. Found the estimator
  divergence independently and quantified it at the same node.
- **The refuter, Sonnet at high effort.** Verdict pass with two issues. Re-ran the
  suite, the gate and the separation arithmetic, and found the collapsed
  forced-jam bracket independently of Codex.

### Findings and adjudication

| # | Finding | Source | Adjudication |
|---|---|---|---|
| 1 | Measured on the betting range rather than per hand, the repricing moves capped nodes AWAY from `s/(1+2s)`, 0.4762 → 0.4022 against an uncapped 0.5168, because the identity's value side has no lever. | Theory | **Accepted, and it ended the ticket.** The worker reproduced the whole table independently, with a harness written from the analytics export's hand loop rather than from the reviewer's code, and matched every figure. The owner then ruled the repricing out. Recorded as a contract defect: the theory contract states the identity and carries no size or stack-to-pot term anywhere on the made-value bet path. |
| 2 | Estimator parity is broken. `_effective_bluff_fraction` reads `bracket.max_bb`, the estimator builds BET and RAISE with `max_bb=None`, so the villain range shown to the player kept the old pricing while the live bot used the new one — maniac P(BET) 0.5905 against a live 0.4074, and 13.0 percent of bluff-cell aggressive nodes have a binding cap. | Theory and Sol, independently | **Accepted.** It also falsified the premise the slice had inherited in three places (contract map Risk 3, ticket criterion 6, and this ledger's contract-scan entry), all of which reasoned only about the sizing draw while stage one runs before the action draw. The repricing went; the finding became the shipped test. |
| 3 | The existing parity tests are structurally blind to finding 2: both the estimator's bracket builder and the test file's live-side helper build the same capless bracket, so every parity assertion compared a capless estimator against a capless live side. | Theory | **Accepted, and this is what shipped.** `test_no_aggressive_bracket_field_is_read_before_the_action_draw` builds its live side from `engine.legal_actions` at a real short-stack node, asserts the two brackets differ materially before comparing distributions, and covers twelve legs — six personas by two node shapes. Proven non-vacuous: reintroducing a lever that reads `max_bb` before the action draw turns all twelve red while the six pre-existing parity tests stay green. |
| 4 | `_effective_bluff_fraction` mis-prices a collapsed forced-jam bracket, where the engine sets `min_bb == max_bb` and the wager is forced to the cap for every authored key. Reproduced against the shipped function at roughly a 1.9× factor error. | Refuter and Sol, independently | **Accepted as real and then measured inert, in that order.** The review sampled 1,045 key instances at forced jams over 6,000 hands and found zero bucket mispricings on the shipped packs; with the fix applied, the 50,000-hand export was byte-identical to the one without it. It is moot at the merged tip because the helper it lived in is gone. The initial write-up called it live impact, which it never was. |
| 5 | The comment claiming that moving only the weights means no bet size changes is false — weighted selection determines which authored key is drawn, so the same sizing variate can produce a different wager at a partially capped node. | Sol | **Accepted.** A false claim in a file the author had just edited, again. |
| 6 | No behavioural test drove the RAISE branch of the helper at a capped stack; all thirty-five legs ran through one unopened-BET fixture. | Refuter | **Accepted, then moot.** The branch does not ship. |

### What was dropped, and why

The repricing, on the owner's ruling, taking `_effective_bluff_fraction`, both
call sites, the whole of `test_bluff_effective_size.py` and three exact-count
re-records with it. The estimator's bracket reconstruction went too, judged on
its own: with nothing reading those fields it is production code with no
consumer, and the new test protects the next ticket better because it fails
loudly rather than hiding a divergence. The collapsed-jam fix went because the
helper it lived in is gone and it was in any case inert.

### What the author got wrong, for the record

The build was faithful to its ticket and the ticket was wrong, which is the
useful way round. Two things belong on the record beyond that.

**The build shipped a false comment about its own bet sizes** (finding 5), in the
third consecutive ticket of this slice to ship a stale or false claim past a
fully green suite. **And the safety premise the ticket inherited was never
checked** — three merged documents said an estimator fault here was impossible,
all three reasoning about the wrong stage of a two-stage law, and criterion 6
turned that error into an instruction pointing the build away from the test that
would have caught it.

The orchestrator's own error this round: it wrote the collapsed forced-jam
bracket up as live impact before the byte-identity measurement existed.

### What this round proves about the process

**A worker reproduced, against its own ticket's interest, the finding that killed
its ticket.** The theory reviewer measured it; the worker rebuilt the measurement
from a different starting point rather than re-running the reviewer's code, got
the same numbers, and reported them. That is the review loop working as designed,
and it is worth naming because the outcome — three pull requests, one of which
ships no behaviour — reads like a failure if only the diff is counted.

## Build round — T3, 2026-08-19 (merged as PR #200)

**T3 shipped at a damp of 0.06, which is not the value its own arithmetic
derives. Minimum-defence arithmetic over the measured river price distribution
gives about 0.46; two frozen went-to-showdown bands do not admit that, and the
owner ruled the conflict in the bands' favour on 2026-08-19. The determinism win
survives — folds that are probability-1.000 by construction fall from 495 to 144
— and the residual is carried rather than tuned: the river range still
under-defends its obligation by 4.8 points, on a street the contract's own
diagnosis says is not where the showdown excess comes from.**

T3 is the slice's third ticket: narrowing the river call zero so it applies to
air alone, letting naked ace-high call the river again.

### What was measured

50,000 hands, seed 20260817, ratified lineup, measured on top of T1 as the ticket
required.

| | base (T1) | shipped (damp 0.06) |
|---|---|---|
| Folds that are probability-1.000 by construction | 495 | **144** |
| `diagnose.py`'s printed count, both buckets | 495 | 444 |
| Headline node, ace-high P(call) | 0.0000 | **0.1821** (151 of 829) |
| Headline node, air P(call) | 0.0000 | **0.0000** (382 decisions) |
| Invest-then-fold events | 1,084 | 1,015 |
| Pool went-to-showdown | 54.1429% | 55.0865% (+0.9435, bound 3.78) |
| River range continue against its obligation | 0.603 / 0.678 | 0.628 / 0.676 |
| LAG–TAG separation, seed 601 | 1.9852 | **2.0388** |

The passive fish moved the wrong way, 2.54 to 2.57 events per thousand hands,
against five personas that fell. It is recorded for the same reason the nit's rise
was recorded in the T1 round: a table showing only the falls would imply the roster
moved uniformly.

### Acceptance criterion 1, unmet on its literal terms and met on the property

**Both readings ship, and the pull request carries both rather than choosing.**

- The ticket's literal statistic is the diagnosis script's printed count of river
  air-or-ace-high folds facing a bet at least the seat's stack. It reads 495 at the
  base and **444** at the shipped value. It does not fall toward "roughly 130", so
  on literal terms **criterion 1 is not met.**
- The property the criterion was written to capture is determinism. The same filter
  restricted to AIR — the only bucket still hard-zeroed — reads **144**, which is the
  "roughly 130" the ticket predicted. On this reading it is met.

The gap is the roughly 300 ace-high folds still inside the printed count. They are
not machine folds; they come out of a decision that mixes at 0.1821. The ticket's
statistic counts folds rather than certainties and cannot tell the difference, and
its text assumed ace-high would essentially stop folding — true only at a damp far
above what the bands admit. **The cause of the shortfall is the band ruling capping
the damp, not the build.**

### The gate

PASS at seed 601: minimum pairwise 2.038801 against the pinned floor 1.254429,
labels 6/6, second-closest pair nit–TAG at 2.5996. Both frozen went-to-showdown
bands clear, and they are the constraint that set the shipped value: lag 0.5793
against a 0.59 ceiling, margin +0.0107; calling station 0.7096 against 0.72,
margin +0.0104. The determinism rule's worst persona reads 0.1429.

**That rule is not evidence either way here, and the reason is not the one PR
#200 gave.** The pull request said the rule's "context key carries no hand class,
so this cell was never one of its deterministic contexts". Both halves are false:
the rule keys a context as `(persona, street, engine_node_key,
hand_class_bucket)`, and the cell **is** one of its flagged contexts — at this very
tip the nit's river `flat` / `ace_high|none` context is reported deterministic at a
0.9864 modal share over 220 observations. **The real mechanism is that the rule
counts contexts rather than decisions and allows each persona 20 percent of its
qualifying contexts to be deterministic.** Two or three flagged river contexts
among the nit's 91 qualifying ones cannot approach that allowance, before or after
T3. Compounding it: `engine_node_key` does not encode "faced a bet at least the
seat's remaining stack", so the surface T3 targets is a thin slice inside a broader
context, and a damp of 0.06 does not lift that broader context back under the 0.98
modal-share threshold. The guard therefore flags the same contexts either side of
the change. See the five-seed table in the close-out for the readings at all five
seeds, and the corrected note on spec §7's slice criterion 2.

### How the review was run

Three reviewers again, same asymmetric brief.

- **Codex Sol, high effort.** Verdict request-changes, five findings, all addressed
  before merge.
- **The persona-realism theory reviewer, Opus.** Verdict go-with-changes.
  Reproduced the entire band sweep to four decimal places including values that
  were not shipped, and referred one item to the owner rather than the implementer.
- **The refuter, Sonnet at high effort.** Verdict pass. Re-derived the gate
  distance, the band sweep and the coverage-baseline explanation independently.

### Findings and adjudication

| # | Finding | Source | Adjudication |
|---|---|---|---|
| 1 | The source claimed 0.06 is the largest damp satisfying its stated margin standard. It is not: 0.061 clears both limbs and 0.062 misses. | Sol | **Accepted; the claim was false and is withdrawn.** 0.06 is kept and now described as a round value inside the admissible range rather than its maximum. One thousandth of the constant moves the station margin three ten-thousandths across the line, so a value chosen at 0.061 would be fitted to the standard rather than endorsed by it. The knife edge is itself the useful fact and is now in the table. |
| 2 | The margin standard — clear both bands by at least one binomial sigma and 0.010 absolute — is not an existing rule. The band assertions require interval membership and nothing more, and the 0.010 limb mixes policy response with stream displacement rather than isolating jitter. | Sol | **Accepted on governance.** The standard stands as a judgement call and is now labelled as one. What it is for is refusing a margin like the +0.0002 that damp 0.10 produces, which passes today and flaps on any resampling. |
| 3 | The test block header said the ace-high half mixes at P(call) 0.691. That is the undamped figure, measured before the band ruling and never re-measured; it is 0.1821. | All three reviewers, independently | **Accepted.** Four times the true value, shipped past a green suite, and found by reading rather than by running — because there was nothing to run. The direct fix is that T3's harness and its output at all four tips are now committed under `../research/slice2-invest-then-fold/`. |
| 4 | The coverage-baseline fixture called the new 25.90 percent ratio the largest dip in its chain. The same file's wave-3 entry reads 24.5 percent and −3.8pp. | Sol | **Accepted.** 25.90 percent is third-deepest. The correction also cites the wave-3 entry's own precedent for non-monotone displacement, and two reviewers re-measured the ratio independently, one at 36,000 decisions where it is flat. |
| 5 | Stale T1 prose survived the re-record at the end of the same docstring, attributing the movement to multiway flop and turn floating and concluding the ratio rose and spec §7.1 was met — directly above T3 values that fall. | Sol | **Accepted.** Replaced; it now reports rather than claims compliance. |
| 6 | Three places still said river ace-high call merit is zero through the old `bluff_cell` gate. The worst is `test_ace_high_facing_a_bet_is_byte_identical`, whose river leg stays green only because its control neutralises two damps while leaving the new one live in both arms. | Sol | **Accepted.** The docstring now states what the test actually protects: that the two flop and turn damps stay off the river. |
| 7 | The derived value was quoted to four significant figures off an inversion the same block twice concedes is approximate. | Sol | **Accepted.** Rounded to 0.46 everywhere, with the precision stated. Shipping 0.45 landed the range at 0.688 where the arithmetic predicted 0.678, which is the size of the error the two figures support. |
| 8 | T3 obeys the theory contract faithfully and the contract is wrong here: applying the re-anchor rule to two went-to-showdown ceilings the contract itself records as inflated forced the river-defence lever down by a factor of 7.7 from its derived value. | Theory | **Adjudicated, and it cuts for the ruling rather than against it.** The pinned bands do sit far above the contract's research-grounded targets. But the roster sits near 71 percent against a 38–48 target, and the derived 0.46 would have taken it to 74.7 percent — further from the grounded target. The band stopped a change that would have widened the gap the contract wants closed. The ruling holds on firmer ground than it was made on. What survives is a filed finding: T3 under-defends the river to pay for showdown excess the contract attributes to flop and turn calldown, which is fixing the wrong street and points at slice 3. |
| 9 | The regression test encoded a bracket admitting anything through 0.065, including the 0.062 since measured as violating. | Sol | **Accepted.** It now pins the shipped constant exactly, with a deliberately redundant non-zero assertion naming the one property that must survive any re-derivation. |

### What the author got wrong, for the record

**Five stale or false claims, and the suite was fully green through all five.**
Three of them — the P(call) figure, the largest-dip claim and the stale T1 prose —
were in files the author had just edited, and one of them was a superlative about
the author's own calibration. The instrument that caught every one was readers.

The orchestrator contributed three errors of its own this round: it repeated the
worker's false "largest dip" claim rather than checking it against the same file's
own history; it wrote the T2 forced-jam finding up as live impact before the
byte-identity measurement existed; and it nearly overwrote the worker's honest
finding that criterion 1 is unmet on literal terms with the softer determinism-only
reading.

**A sixth false claim was found after merge, at close-out, and it is the most
instructive of the six because no code carried it.** PR #200's body asserted that
the gate's determinism rule "is structurally blind to the defect T3 removes — its
context key carries no hand class, so this cell was never one of its deterministic
contexts". The rule's own definition contradicts both halves, and the gate output
flags the very cell in question. Nothing in the repository ever said it; it was
written in a pull-request body, and the close-out then repeated it in three places
without checking it against the rule's source. It was caught by a reviewer whose
only brief was to check numbers against sources. **A claim about an instrument is
as checkable as a claim about the code, and it was checked by nobody until the
slice was already merged.** The worker's version is what shipped, and it was right to insist.

### Two lessons this slice earned, stated rather than smoothed over

1. **All three tickets shipped stale or false claims past a fully green test
   suite.** T1 shipped four, T2 one, T3 five in the code and a sixth in its
   pull-request body that survived merge and was caught only at close-out. Not one
   was caught by a test, because no test reads prose. The only instrument that
   works on this failure class is independent readers looking for contradictions,
   and the cost of the slice's review rounds is what buying that instrument costs.
   **The sixth adds a rider: prose outside the repository — a pull-request body —
   gets no review pass at all once it is merged, and this slice put a false claim
   about a gate's own definition there and then propagated it into three
   documents.**
2. **T2 was killed by its own worker reproducing, from scratch, a measurement
   against its own ticket's interest.** A process that only rewards shipped diffs
   would have suppressed that. Recording it is how it stays repeatable.

## Filed at slice close

Written up here so the slice has one list rather than several. Nothing below is
built, and nothing below blocks the slice.

### Carried forward from the spec's out-of-scope list

- **The all-in cascade.** 20.2 percent of hands at this tip see at least one seat
  all-in, and 93 percent of the counted events are all-in refusals in pots the
  cascade inflates — median pot 253bb. Cut by ruling A, which put engine and stack
  work out of this phase, so the largest single contributor to the statistic is out
  of reach by ruling rather than by oversight.

  **Reconciling the four figures the slice's documents quote, because two of them
  are the same statistic and two are not.** Spec §1.2's "93 percent" and the
  out-of-scope entry's "94 percent of the surface" are **one statistic on two
  lineups**: the share of counted events that are all-in refusals, which this
  ledger's own 2026-08-18 re-measure table records as **94.0 percent on the
  default lineup and 92.7 percent on the ratified one**. The out-of-scope line
  still carries the default-lineup survivor; §1.2's 93 is the ratified 92.7
  rounded. **20.2 percent is a different statistic** — the share of *hands* in
  which at least one seat finishes all-in, whose default-lineup counterpart is the
  30.9 percent an earlier version of the ticket's close-out list quoted. So: two
  statistics, four numbers, each pair a default-lineup and a ratified-lineup
  reading of the same thing.
- **The residual air-only deterministic folds.** 144 per 50,000 hands survive T3 by
  design: "air never calls the river" is the half of the rule that was always right.
  They remain probability-1.000 folds and remain a statistical signature.
- **Bottom-bucket price saturation.** A sub-`SMALL` price resolution stays out. The
  draft's original reason for excluding it was refuted — at these nodes no raise is
  legal, so the change is an exact no-op there — and it stays out on the reasons that
  do hold: off the river it converts folds into calls and pushes showdown up, and its
  blast radius is every small-bet decision in the game.
- **The maniac's preflop 4-bet catch-all.** Twelve events, the maniac calling or
  shoving any two cards in a re-entrant raise war. Real, tiny, and a pack question
  rather than an engine one.
- **The calling personas' residual continuation.** Slice 3's, under the boundary in
  spec §6.2 — arrival at nodes that already mix, driven by looseness, not a
  degenerate decision.

### New from this slice's reviews

- **`_AGG_BASE` has no size or stack-to-pot term, so the bluff-share identity has
  no value-side lever.** This killed T2 and it blocks any future work on bluff
  frequency: correcting one side of a two-sided identity moves the composition away
  from target while every gate passes. Owner's to dispose of; see PR #199.
- **The pinned went-to-showdown bands sit well above the theory contract's own
  grounded targets** — the calling station's band is 66–72 against a 38–48 target,
  a gap of 18 to 24 points, and the lag's is 37–59 against 26–31 — and the contract
  calls for a downward re-anchor that has not happened. The bands bound T3's constant at roughly a seventh of its
  derived value. Owner authorised evidence-gathering on 2026-08-19; no re-anchor is
  proposed here.
- **T3 leaves the river under-defending its obligation by about 4.8 points to
  protect a showdown ceiling whose excess the contract attributes to flop and turn
  calldown.** That is fixing the wrong street, and slice 3 — whose remit is
  continuation frequency — is where the correction lives.
- **The roster does not bluff its river often enough for ace-high's restored call to
  be profitable against this field.** It wins 8.0 percent at the shipped value
  against a mean required equity of 23.8 percent, and is under required equity in
  every faced-size band. Minimum defence is an unexploitability argument, not a
  profit one, and T3 rests on the former: the point is that the decision mixes. Said
  plainly because a fair reader could call T3 an addition of losing calls. If the
  bots bluffed the river at a defensible rate, no damp constant would need deriving
  at all.
- **Whether the α fold-ceiling should be asserted over the ACE_HIGH bucket.**
  `_CATCHER_BUCKETS` excludes ace-high because it loses to part of a balanced
  bettor's bluffing range; T3's branch restores its river call because on a finished
  board it is exactly a bluff-catcher. Both can be true of different streets and
  nothing in the code says so. **Owner ruled 2026-08-19 that α does apply to the
  bucket, and authorised a guard-extension ticket**; T3's new call leg currently sits
  outside the guard, because the guard is scoped by `_CATCHER_BUCKETS`.
- **The two standing price fixtures are blind to street-gated levers.**
  `fold_by_size` and `catcher_fold_by_size` both omit `street`, so they measure at
  `street=None`, outside any street gate; a first version of T1's α measurement
  copied them and produced before-and-after tables that were byte-identical. **Fix
  authorised 2026-08-19.**
- **The lag preflop dossier band is fragile and its re-tune is overdue.** Preflop
  policy is byte-identical across T3 by construction, yet the same unchanged policy
  reads 0.4262, 0.4301 and 0.4372 across the three damp values — a 0.011 spread on a
  0.43 floor, entirely rng-stream displacement. It passes by luck of the stream.
  Slice 1's T5 tripped it the same way, and the `vs_3bet` opener re-tune that test's
  own docstring filed is two slices overdue. Evidence-gathering authorised
  2026-08-19.

## Slice close-out

**Superseded 2026-08-21 — see the "Close-out, 2026-08-21" section at the bottom
of this file for the current state (CLOSED). What follows is the record of the
gate obligations and ticket status as they stood before the play session.**

~~The slice is OPEN. Every ticket is merged and the gate obligations are recorded
below, but the owner's blind play session has not happened, and under the
2026-08-17 ruling that session is the primary acceptance evidence for the slice
— it outranks the gate rather than supplementing it. Nothing here should be read
as the slice being finished.~~

Merged tip: `862e614`. Pull requests #198 (T1), #199 (T2), #200 (T3).

### Ticket status

| Ticket | State | What actually shipped |
|---|---|---|
| T1 — naked ace-high stops floating multiway bets | **Done**, PR #198 | One predicate, plus four tests and four rewritten comment blocks. Hit its pre-committed 1,084 events exactly. |
| T2 — bluff frequency on the bettable size | **Done as withdrawn**, PR #199 | No behaviour change. An estimator-parity test that can catch the villain range diverging from the live sampler, plus two docstrings. The repricing was withdrawn on the owner's ruling; see the T2 build round. |
| T3 — ace-high may call the river again | **Done**, PR #200 | `_ACE_HIGH_RIVER_CALL_DAMP = 0.06` and a narrowed river call zero. Criterion 1 is unmet on its literal statistic and met on the determinism property it was written to capture. |

### The five-seed gate set — discharged, PASS on all five seeds

**The slice's gate obligation is discharged. All five seeds pass both rules at
the merged tip, LAG–TAG is the binding pair on every one of them, and the
weakest reading anywhere sits comfortably inside its limit.** ~~The slice stays
OPEN regardless; the owner confirmed today that the play session has not
happened.~~ *(Superseded 2026-08-21 — the play session has since happened and the slice is CLOSED; see the "Close-out, 2026-08-21" section at the bottom of this file.)*

Run as `python -m tools.derobo_gate --check --all-seeds`, against baseline
artifact `a5baseline-98abd160f03a501b` at engine SHA `a0de83e`, with the
separation floor at `1.254429` — 0.7 of the baseline — and the determinism
ceiling at `0.20`. The baseline artifact was not rebuilt.

| seed | overall | binding pair | LAG–TAG distance | label preservation | determinism, worst persona |
|---|---|---|---:|---|---|
| 601 | PASS | lag–tag | 2.038801 | 6/6 | nit 0.142857 (13/91) |
| 602 | PASS | lag–tag | 1.883035 | 6/6 | nit 0.164706 (14/85) |
| 603 | PASS | lag–tag | 1.808383 | 6/6 | nit 0.159091 (14/88) |
| 604 | PASS | lag–tag | 1.710870 | 6/6 | calling_station 0.123894 (14/113) |
| 605 | PASS | lag–tag | 1.862100 | 6/6 | nit 0.122222 (11/90) |

Three things are worth reading off that table rather than leaving to the PASS
line, which is why the tickets required the pair to be reported explicitly.

- **The lowest pairwise minimum anywhere is 1.710870, at seed 604** — still 0.46
  above the floor, and the seed spread of 1.71 to 2.04 is a reminder that the
  single-seed 2.0388 T3 reported is the top of the range rather than the middle
  of it.
- **The worst determinism share anywhere is 0.164706, at seed 602**, against the
  0.20 ceiling. The persona carrying it moves between the nit and the calling
  station across seeds on counts of 11 to 14 out of 85 to 113, which is the same
  churn in which contexts clear the observation threshold that the T3 round
  recorded. **Read the pass as a pass and nothing more: the rule still flags a
  river naked-ace-high context on every one of the five seeds** — the nit's
  `flat` / `ace_high|none` at modal shares of 0.9851 to 0.9952, the calling
  station's at 0.9881 to 0.9966, and on seed 603 the nit's `river_value` /
  `ace_high|none` as well. It flags them because it counts contexts and allows each
  persona 20 percent of its qualifying set, so a few river entries among ninety-odd
  contexts never move it, and because a damp of 0.06 does not lift a whole
  hand-class context back under a 0.98 modal-share threshold. The guard is not
  measuring what this slice did; the diagnosis count is. See the corrected note on
  spec §7's slice criterion 2.
- **LAG–TAG is the binding pair on every seed**, so the pair the spec told this
  slice to watch is the right one to keep watching, and it was recomputed from
  the raw statistic vectors independently of the tool, matching to six decimals.
  Seed 601 reproduces the reference figure exactly.

No seed failed and there were no anomalies to escalate.

### What the slice moved

| | slice start | merged tip |
|---|---|---|
| Invest-then-fold events, 50k at seed 20260817, ratified lineup | 1,147 | 1,015 |
| Folds that are probability-1.000 by construction | 524 | 144 |
| Pool went-to-showdown | 54.5% | 55.09% |
| LAG–TAG separation, seed 601 | 1.8469 | 2.0388 |
| Hero's graded-decision coverage ratio | 27.30% | 25.90% |

**The coverage ratio fell, and spec §7.5 asks for it to be reported rather than
quietly worsened, so it is reported here.** T1 raised it to 27.59 percent and T3
took it to 25.90, a 2.40-point cumulative dip against the immutable snapshot and
the third-deepest in that fixture's chain. Two reviewers re-measured it
independently, one at 36,000 decisions where it is flat, and the same fixture's
own wave-3 entry records a deeper non-monotone dip attributed to cross-lane
random-stream displacement. The reading is consistent with displacement rather
than with lost coverage, and it is the owner's to judge.

The events fell 11.5 percent. The certainty the slice was really aimed at fell
by roughly three quarters, and what remains is air on the river, which is
correct play rather than a defect. Went-to-showdown rose by less than a point
against the 3.78-point bound the spec allowed.

### Still owed

- **The owner's blind play session.** The only outstanding acceptance item, and
  the decisive one.
- **The owner's disposition of the filed items above**, in particular the missing
  value-side lever in `_AGG_BASE`, which blocks future bluff-frequency work, and
  the went-to-showdown bands, whose distance from the theory contract's grounded
  targets bounded T3's constant.

## Close-out, 2026-08-21 — slice CLOSED

**The slice is CLOSED. The owner played the blind play session; the verdict was
acceptance.** The bots felt plausibly human at the table, and nothing stood out
as robotic. Under the 2026-08-17 ruling recorded above, that session's table
impressions are the primary acceptance evidence for this phase, outranking the
two statistical gates rather than supplementing them — so this verdict is what
closes the slice, not the ticket-merge count that was already in place. All six
close-out pull requests (#201–#206) are merged, on top of the three ticket pull
requests (#198, #199, #200) already recorded above. Full record and the ruling's
rationale: `../roadmap/bot-realism-flywheel.md`, slice 2 entry.

Two related owner rulings landed the same day, in a parallel pull request to the
theory contract, and are noted here without duplicating their detail:

- **Stage-0 interim went-to-showdown band regime — RATIFIED.** Three
  components: grounded floors, a one-way downward ceiling ratchet, and the
  maniac's went-to-showdown assertion restored at a ratcheted ceiling — it has
  been skipped since 2026-08-01. Replaces the frozen bands that T3 above was
  capped inside of. Detail: `../roadmap/bot-realism-flywheel.md`, improvement-phase
  block.
- **Stage-1 stack-commitment brake (`W4-a`) — DEFERRED** past the phase-3
  finale, as a named post-finale slice, with a reopening trigger tied to slice 3
  (calldown) stalling on commit-gated pots. Detail:
  `../roadmap/bot-realism-flywheel.md`, improvement-phase block.
