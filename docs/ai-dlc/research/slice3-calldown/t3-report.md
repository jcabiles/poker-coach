# S3-T3 — the instrument and the contract limits ship; the lever was withdrawn

**Bottom line. S3-T3 ships a measuring instrument and a contract amendment. The
stack-to-pot damp the ticket named was built, measured, reviewed and WITHDRAWN —
it passed all five of its own acceptance criteria and should still not ship,
because three reviewers converged on a design flaw rather than an implementation
flaw: the damp points the wrong way for the buckets where it has leverage. It
made bots bet top pair and middle pair LESS often as their stacks shortened,
which is exactly when commitment says they should bet those hands MORE. Its
premise was also a raw reading: capped wagers are smaller by construction, and
the identity `s/(1+2s)` says a smaller wager warrants a smaller bluff share, so
part of the shortfall the lever was aimed at is what the theory ASKS for. The
engine is now byte-identical to `4f653ef`, every re-recorded fixture and both
ceiling ratchets are reverted, and what remains is the thing this ticket was
actually missing: an instrument, honest limits in the contract, and one new
finding — made-value betting is FLAT in stack depth, so the mechanism the engine
lacks is a commitment SLOPE, the opposite of what was built.**

S3-T3 is ticket 3 of improvement slice 3 (the calldown slice) of the bot-realism
flywheel. "Stack-to-pot ratio" (SPR) is a seat's remaining stack divided by the
pot. A "capped" or "cap-exposed" decision is one where the seat cannot wager its
own largest authored bet size. "The identity" is the theory contract §3
bluff-share formula `s / (1 + 2s)`, the share of a bettor's betting range that
should be bluffs at a wager of `s` times the pot.

Companion documents: `t3-preregistration.md` beside this file (unedited, with a
dated postscript on what pre-registration failed to catch); the contract map
`../../contracts/flywheel-slice3-t3-valueside.md`; the adjudication and the two
findings, `../../ledger/flywheel-slice3-calldown.md` filed items 5 to 7.

Branch `feat/slice3-t3-spr-value`, based on `4f653ef` (the merge of S3-T2, pull
request #215). The withdrawn lever remains in this branch's git history for
provenance; it is not in the tip.

## 1. What ships, and what does not

| file | change |
|---|---|
| `backend/tools/capped_composition_probe.py` | **NEW** — the instrument criterion 1 needed and this repository did not have, reporting BOTH the raw and the target-normalised composition |
| `backend/tests/test_capped_composition_probe.py` | **NEW** — structural guard on the instrument |
| `docs/ai-dlc/contracts/persona-realism-theory-contract.md` | §3 amendment **A8**, limits only |
| `backend/app/domain/personas_postflop.py` | **no change** — byte-identical to `4f653ef` |

**Nothing else in the backend moved.** `git diff 4f653ef -- backend/app
backend/tests content` is empty except for the two new probe files. In
particular:

- **`_value_spr_mult`, `_VALUE_SPR_FLOOR` and `_VALUE_SPR_BUCKETS` are gone**,
  along with the multiplication they fed.
- **Every re-record is reverted** — `_GOLDEN_STATS_N200`, `_PRE_M3_FIRES` and
  the coverage baseline are back to their pre-ticket values, restored rather
  than re-measured, and the full suite passes against them. **With no lever
  there is no stream displacement, so there is nothing to record.**
- **Both went-to-showdown ceiling ratchets are reverted**: the nit returns to
  0.67 and the passive fish to 0.55. The ratchet fires on a slice that MOVES a
  persona's showdown frequency down; this slice moves nothing, so tightening a
  ceiling on it would have pinned the roster against a wall no change had
  earned.
- **The four `s3t3` tests are deleted.** All four asserted properties of the
  removed function, so none of them still asserts something true.

## 2. What the reviewers measured, and why it was decisive

The refuter PASSED the build — every number reproduced, the report was honest.
The theory reviewer returned NEEDS-WORK with two HIGH findings and the
cross-family reviewer returned FAIL with one BLOCKER. **They converged.**

### 2.1 Made-value betting is FLAT in stack depth — reproduced here

The reviewers' central measurement, re-run independently at the reverted tip on
the merit vectors themselves, so there is no sampling variance in it. K-9-3
rainbow flop, pot 10 big blinds, stack swept to give stack-to-pot ratios from 10
down to 0.3, probability of betting:

| bucket | TAG | LAG | maniac | nit | passive_fish | calling_station | responds to stack? |
|---|---|---|---|---|---|---|---|
| top pair | 0.7458 | 0.7964 | 0.8725 | 0.4231 | 0.4231 | 0.3793 | **no — identical to 12 decimal places at every ratio** |
| middle pair | 0.4355 | 0.5070 | 0.6429 | 0.1617 | 0.1617 | 0.1385 | **no** |
| overpair+ | 0.8485→0.9438 | 0.8819→0.9573 | 0.9289→0.9751 | 0.5833→0.8077 | 0.5833→0.8077 | 0.5385→0.7778 | one step at `spr_commit` |

**This is the finding, and it points the opposite way to the lever.** As the
stack shortens a made hand is progressively more committed, and the poker says
its betting frequency should rise toward 1. The engine holds it flat, and the
commit block's single 3.0× step reaches only overpairs and better. The mechanism
the engine is missing is a commitment SLOPE over top pair and middle pair — and
the withdrawn lever was a DAMP over exactly those buckets, taking already-flat
frequencies down further: TAG top pair 0.746 → 0.724, nit 0.423 → 0.400, middle
pair down 2.5 to 2.9 percentage points. It also partly counteracts the commit
block that theory contract §4 row P6 blesses.

### 2.2 The premise was a raw reading of a size-warranted difference

The lever was aimed at a shortfall in capped-node bluff share. That shortfall was
measured RAW — the bluff-cell share of the betting range, never divided by the
identity's own target at the size each wager was actually made at. **The identity
says a smaller wager warrants a smaller bluff share**, and a capped wager is
smaller by construction. §3 now measures how much of the gap that accounts for:
**44 percent of it.**

### 2.3 The withdrawn report's "the gap is mostly arrival" claim was unsupported

It is retracted, from this report and from the contract. The probe computed a raw
share and the paired toggle could not separate arrival from policy; "the facing
cells move by exactly 0.0" was an artefact of gating the lever to the BET arm,
not evidence that the scope was right. §3.3 now says explicitly what is not
measured.

## 3. The instrument, and what it measures at the shipped tip

`backend/tools/capped_composition_probe.py`. No fixture, test or tool in this
repository measured capped-versus-uncapped composition; the only prior
implementation lived in a design dossier that modified no repository file.

    PYTHONPATH=. .venv/bin/python -m tools.capped_composition_probe \
        --hands 20000 --seeds 601,20260817,20260818

Two statistics, and the second is the one to quote. The **raw** bluff-cell share
of the realised betting range, and the **normalised** share — `realised ÷
target`, where the target is the identity evaluated at the pot-fraction each
wager was actually made at. It also reports the exact action-probability vector
at every node, read with the capture-rng pattern from
`backend/tests/node_trace.py`, which carries zero sampling variance.

### 3.1 Pooled over 60,000 hands, three seeds, ratified nine-seat lineup

| | capped | uncapped |
|---|---|---|
| realised wagers | 19,076 | 74,413 |
| **raw** bluff-cell share | 0.0824 | 0.1356 |
| identity target at the realised size | 0.2054 | 0.2645 |
| **normalised** (realised ÷ target) | **0.4009** | **0.5128** |

| statistic | capped ÷ uncapped |
|---|---|
| raw ratio | 0.6072 |
| **normalised ratio** | **0.7817** |

**Normalising for the size actually wagered explains 44.4 percent of the raw
gap.** That is the reviewers' point, measured: capped wagers really are smaller
(target 0.2054 against 0.2645), and the identity really does ask for a lower
bluff share there. A residual of 21.8 percent below the uncapped norm survives.

Per seed, because a single seed cannot carry this statistic:

| seed | raw ratio | normalised ratio | capped normalised | uncapped normalised |
|---|---|---|---|---|
| 601 | 0.6294 | 0.8066 | 0.4155 | 0.5152 |
| 20260817 | 0.6361 | 0.8254 | 0.4224 | 0.5118 |
| 20260818 | 0.5555 | 0.7126 | 0.3644 | 0.5114 |

The uncapped normalised figure is stable across seeds (0.5114 to 0.5152) and
**independently corroborates the design dossier's uncapped reading of 0.5156 and
0.5168**, which is the check that says this instrument and that one are measuring
the same thing. The capped figure is the noisy one, spread 0.3644 to 0.4224 —
which is exactly why the ticket's own criterion could never have been read on one
seed. It is lower than the dossier's capped reading of about 0.48 because the two
use different predicates: this probe classifies a NODE as cap-exposed when the
seat could not have made its largest authored size, the dossier classified a
WAGER as capped when it landed on the bracket maximum. **The two populations are
not the same and their numbers should not be compared directly.**

### 3.2 Composition of the two betting ranges

| | capped | uncapped |
|---|---|---|
| bluff cell | 0.0824 | 0.1356 |
| draw cell | 0.1053 | 0.1590 |
| made value | 0.8124 | 0.7053 |

### 3.3 What this does NOT measure — the load-bearing caveat

**The 21.8 percent residual is a gap, not a defect.** Three things could produce
it and this repository separates none of them: the size the wager was made at
(which the normalisation handles), **arrival** — which hands the seat actually
holds at a capped decision, the `π` term in both halves of the identity, a
property of how the hand got there rather than of any policy — and **policy**,
the conditional probability of betting given the hand. Separating arrival from
policy needs a `π`-by-node table that does not exist. §3.2's composition
difference is consistent with an arrival story and does not establish one.

**The rule this puts on future slices**, now theory contract §3 amendment A8 item
3: no slice may cite a gap on this instrument as evidence that a policy is wrong
until the decomposition is built.

## 4. The record of what the withdrawn lever did

Kept because a withdrawal that deletes its own evidence cannot be reviewed. All
figures are from the lever's own branch state, now superseded.

**Paired action mix at unopened decisions**, expected probability of BET, zero
sampling variance:

| population | nodes | before | after | change |
|---|---|---|---|---|
| capped, made value | 13,211 | 0.57984 | 0.57148 | **−0.836pp** |
| capped, bluff cell | 3,942 | 0.17515 | 0.17515 | 0.000 |
| uncapped, made value | 102,686 | 0.43481 | 0.43448 | −0.033pp |
| uncapped, bluff cell | 65,605 | 0.12483 | 0.12483 | 0.000 |

**The floor constant's derivation was falsified, and the withdrawn report did not
say so.** `_VALUE_SPR_FLOOR = 0.88` was taken from the design dossier, which
sized it to deliver a **4.4 percent** cut in capped-node value wagers. Measured,
it delivered **1.44 percent** (0.57984 → 0.57148). The constant was carried
forward as "the design seed, unchanged" and presented as discipline — not tuning
to the result — which was true but incomplete: its stated derivation had already
failed by a factor of three, and a reader of that report could not have known.
**Recorded here as a reporting failure of the withdrawn round.**

Went-to-showdown under the lever moved by less than either instrument could sign
(harness: four personas down, two up; 50,000-hand export: five up, one down;
pooled export 53.4% → 53.6%, about 1.3 standard errors). The five-seed gate
passed 5 of 5 with LAG–TAG binding on every seed. None of it is load-bearing now.

## 5. Acceptance criteria, as adjudicated

The ticket's five criteria all PASSED on the withdrawn lever and are moot; the
adjudication replaces them with what the ticket actually delivers.

| # | criterion | verdict |
|---|---|---|
| 1 | pooled capped-node composition moves toward the uncapped norm | **MOOT — lever withdrawn.** What ships instead is the instrument the criterion needed and lacked, now reporting the target-normalised figure the reviewers asked for. §3. |
| 2 | LAG went-to-showdown ceiling watched explicitly | **N/A — nothing moves.** The engine is byte-identical to `4f653ef`; both ratchets are reverted. |
| 3 | five-seed de-robotization gate green | **PASS**, and it reproduces `4f653ef` — §6. |
| 4 | byte-identity preserved wherever the stack does not bind | **SUPERSEDED by total byte-identity.** The withdrawn lever's claim was also imprecise and is corrected here: it held at and above `spr_commit`, NOT at every uncapped node — uncapped made-value betting moved −0.033pp, because the ramp keyed on `spr_commit` (1.2 to 3.3) fired on a superset of capped decisions (below 1.0, or 1.5 for the maniac). |
| 5 | contract §3 amendment lands in the same pull request | **PASS** — amendment A8, rewritten as limits only. §7. |

## 6. Checks

| command | result |
|---|---|
| `./scripts/verify.sh` | **BACKEND VERIFY OK** (2185 passed, 2 skipped — the two skips are the S6 detection probe, which needs a local artifact and is unrelated) |
| `cd backend && ruff check .` | clean |
| `python -m tools.derobo_gate --check --all-seeds` | **GATE PASS 5/5**, and every seed reproduces S3-T2's reading exactly — see §6.1 |
| `pytest -k "persona_postflop_bands or wtsd_ordering or spr or capped"` | 38 passed |

### 6.1 The gate is the proof that the engine really did go back

The five-seed de-robotization gate does not merely pass — **every seed returns
the identical separation distance S3-T2 recorded at `4f653ef`**, to the last
decimal the gate prints:

| seed | this tip | S3-T2's reading at `4f653ef` | under the withdrawn lever |
|---|---|---|---|
| 601 | 1.853360 | 1.853360 | 2.052617 |
| 602 | 1.792393 | 1.792393 | 1.778670 |
| 603 | 1.765554 | 1.765554 | 1.743322 |
| 604 | 2.008972 | 2.008972 | 2.208862 |
| 605 | 1.958660 | 1.958660 | 1.861133 |

Each figure is a statistic over 50,000 simulated hands per seed, so five exact
matches is not a coincidence that a residual code difference could survive. Taken
with the empty `git diff 4f653ef -- backend/app backend/tests content` and the
restored-not-re-measured fixtures, the engine's behaviour is back to its
pre-ticket state on three independent checks.

## 7. The contract amendment

Amendment **A8** in §3, dated 2026-08-22, is now **limits only**. It records:
(1) the value side has no lever and no size or stack term — with §2.1's flatness
measurement as the evidence; (2) what was measured about capped decisions, raw
and normalised, with the warning that the raw figure is not readable alone;
(3) **what was NOT measured** — the residual is not decomposed into
size-warranted, arrival and policy, stated explicitly so no slice cites it as a
policy defect; (4) the identity is a range property, not a per-node one;
(5) the **OPEN ITEM** — a commitment slope over top pair and middle pair, for
the re-anchor slice, needing an owner decision; and (6) that the damp was built,
measured and withdrawn, with the instruction not to rebuild it.

The wording error a reviewer caught is fixed: the arm is the **unopened BET
arm**, not the "matched-with-option BET arm" — the matched-with-option arm is a
RAISE.

## 8. What a reviewer should press on

- **The withdrawal is the claim.** §2.1's flatness table is reproducible in a
  few seconds on the merit vectors and is the whole argument; if top pair is not
  flat in stack depth, the finding is wrong and so is the withdrawal.
- **The normalised statistic is new code and its target must be checked.**
  `identity_target` is `s/(1+2s)` and is unit-tested against the contract's own
  reference values; the inversion from a realised `size_bb` back to a
  pot-fraction mirrors the sampler's two sizing formulas and is the place an
  error would hide.
- **The 44 percent figure is a ratio of ratios** and depends on the cap-exposure
  predicate. §3.1 states plainly that this probe's predicate differs from the
  dossier's and that the two capped numbers are not comparable.
- **Nothing in the engine changed, so nothing in the population should have.**
  The reverted fixtures are the check: they were restored to their pre-ticket
  values rather than re-measured, and the suite passes against them.
