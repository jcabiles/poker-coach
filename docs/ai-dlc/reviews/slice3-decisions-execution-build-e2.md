# Build review — E2, test deletions and comment corrections (2026-08-24)

**Bottom line.** A fresh adversarial reviewer returned **APPROVE with zero findings** on ticket E2,
the second of the three tickets in this build. It reproduced the two pieces of evidence that matter
rather than taking them on trust: the engine file's abstract syntax tree is identical before and
after the change, and the test suite lands on exactly the count predicted before any work began. The
one judgement call the worker made outside its written instructions — deleting a section-header
comment the ticket did not name — was examined and judged correct.

The reviewer was a fresh Claude `refuter` agent on Sonnet at high reasoning effort, given the
approved spec, the ticket and the theory contract as its criteria, and **not** given the worker's
report.

## What E2 did

Ticket E2 deleted the tests that enforced a poker rule the owner has withdrawn, and corrected the
comments that still described that rule as settled law.

**α (alpha)** is poker's minimum-defence identity: facing a bet of *f* times the pot, a defender who
folds more than `f/(1+f)` of its holdings makes that bet profitable with any two cards. A **bucket**
is one hand-strength class the engine reasons in, such as `ACE_HIGH`. On 2026-08-19 the owner ruled
that α bounds the `ACE_HIGH` bucket specifically; on **2026-08-24 the owner withdrew that ruling** —
α bounds a player's whole range and nothing smaller. That withdrawal is amendment A9 of the theory
contract, landed by the previous ticket.

Deleted: three tests (`test_ace_high_river_alpha_ceiling`, which collected six cases and was the
source of all six of the suite's expected-failures; `test_ace_high_river_alpha_guard_is_not_vacuous`;
and `test_ace_high_alpha_holds_for_the_station_pre_river`), a 55-line narrator comment block, and
two helper functions that lose every caller (`_ace_high_river_alpha_breaches` and
`_measure_ace_high_fold_by_size`). Corrected: one surviving docstring and the two engine comment
blocks.

## Evidence, reproduced twice

| Check | Result | Reproduced by |
|---|---|---|
| Abstract-syntax-tree comparison of `personas_postflop.py`, before against after | **identical** — a proof of zero behaviour change, stronger than reading the diff for lines starting with a hash | orchestrator, then reviewer |
| `pytest tests/test_personas_postflop.py -q` | `393 passed`, no skips, no expected-failures | reviewer (the worker's own run agreed) |
| Whole suite via `./scripts/verify.sh` | `2189 passed, 2 skipped` and `BACKEND VERIFY OK` | worker; orchestrator re-runs it as the final gate on the branch |
| `ruff check .` | `All checks passed!` | reviewer |

**The counts were predicted before the work started, not fitted afterwards.** The orchestrator
registered a baseline of 2191 passed / 2 skipped / 6 expected-failures for the whole suite and 401
collected cases for the persona test file, counted the three doomed tests at 6 + 1 + 1 = 8 collected
cases, and wrote 2189 / 2 / 0 and 393 into the worker's brief as the only acceptable outcome. Both
figures landed exactly.

## The two deviations from the written instructions, both adjudicated

**1. The spec named the wrong test — a defect in the spec, not in the build.** The approved spec
directs a docstring correction at `test_fold_to_bet_respects_alpha_ceiling`, lines 8421–8428. Those
lines actually belong to a different test,
`test_bluff_catcher_alpha_contract_untouched_at_multiple_opponents`. The worker trusted the line
numbers over the name; the reviewer and the orchestrator independently confirmed that was right —
the block at those lines does assert the withdrawn ruling and does cite a now-deleted test, while
the test the spec *named* is about the one-pair bluff-catcher range and never mentions the
per-bucket reading at all. **No block that needed correcting was missed.** This is recorded as
finding B3 in `../ledger/slice3-decisions-execution.md` so that a later reader does not "correct"
the spec's name and re-open the wrong docstring.

**2. An unlisted 7-line deletion, judged correct.** The worker also deleted a section-header comment
that introduced only the block being removed, and which asserted the withdrawn ruling as settled
fact. Keeping it would have left a factually wrong header with nothing underneath it. The reviewer
confirmed it was a genuine orphan and that nothing still referenced by surviving code went with it.

## Residue sweep

The reviewer grepped both files for the date `2026-08-19`, the phrase "per-bucket", the deleted
symbol names, and references to the older ruling document. Every surviving mention is correct
history — "this was ruled, then withdrawn", dated on both sides and citing amendment A9 — or
concerns a genuinely different and older idea: how much of a *whole range's* defence obligation the
ace-high holdings should supply, which is the arithmetic behind the river call damp and is not the
claim the owner withdrew. No surviving line asserts the withdrawn rule as live.

The engine constant `_ACE_HIGH_RIVER_CALL_DAMP` and its pinning test are untouched and still pass.
The withdrawal removes a *test*, not the lever.
