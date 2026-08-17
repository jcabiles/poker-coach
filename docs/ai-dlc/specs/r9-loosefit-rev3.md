# Spec — R9-LOOSEFIT rev 3: make the nit measurably the tightest defender (nit-only, node-gated)

status: ⛔ **WITHDRAWN — dual review FAIL (2026-08-04). Do not build from this file.**
`refuter` FAIL (1 HIGH) + Codex Sol FAIL (2 HIGH / 3 MED / 2 LOW); all eight findings adjudicated
in `ledger/r9-loosefit.md` (rows S-1…S-8). **The "Measured feasibility" table below is WRONG** —
every price is mislabeled (the aggressor contribution was omitted, so the engine read a larger
faced price than the label), and at the true ½-pot price the spec's own named binding node fails
both pre-registered thresholds. The direction (nit-only, node-gated) survives review; the panel,
the thresholds and the build instruction do not. Rev 4 follows a correctly-priced re-derivation.
slice: r9-loosefit · initiative: persona-realism · code pin: `origin/main` = b63dfaa
supersedes: `specs/r9-loosefit.md` (rev 2 — build halted at T1, ten findings B-1…B-15)
contracts: `contracts/r9-loosefit.md` — **read its REV-2 SCAN block, not §1–§8, which are incomplete**
evidence: `reports/r9-loosefit-t1-measurement.md` (read WITH its corrections header) ·
`ledger/r9-loosefit.md` (B-1…B-15 + the independent verification table)
citation convention: code @ b63dfaa; ai-dlc docs @ working tree, anchors authoritative.

## One-line goal

Move **nit's `call_looseness` from 0.6 to 0.45 and nothing else**, and prove at a panel of
constructed decision points that the nit now folds materially more than it did — and more than tag
does at the identical spot — with every existing HARD gate green and `continue_ref` frozen.

## What changed from rev 2, and why

Rev 2 tried to fit **three** personas to a **population** statistic against **pre-registered
thresholds nobody had measured**. All three choices failed, each for a reason now documented:

| rev-2 choice | why it failed | rev-3 choice |
|---|---|---|
| fit nit **and** tag **and** lag | tag is pinned to its own `stickiness` by a control built from the shipped pack (H1), and escaping that cascades into the `stickiness`/`size_elasticity` validator and the price curve three other blockers read | **nit only.** Whole-suite arm at nit 0.42 breaks **2** tests, both sanctioned re-records. Every multi-persona arm breaks 7–12 |
| gate a **population** fold-rate gap | denominators are tiny at CI n (nit: 135 c-bet-facing opportunities at n=4,000), and arrival composition swamps the mechanism — the raise-side leg needed n ≈ 566,000 | **gate constructed nodes.** Exact distributions, zero sampling noise, effect measured before the threshold was written |
| thresholds chosen from theory | the symmetric 6σ rule was unreachable (needs n ≈ 75,000); the ±3σ raise-share rule was unreachable at any n | **thresholds derived from measurement, with margin**, and every one of them checked against a node that would fail it |

**The premise is also restated.** Rev 2's background said the nit "measurably folds LESS than tag —
backwards." That is false at stable sample: the independent estimate is a gap of
**+0.0087 ± 0.0063** (56 seeds plus a second large draw; ledger B-12), i.e. the nit already folds
marginally *more*. **This slice does not repair an inversion. It turns a statistical tie into a
visible identity difference** — a magnitude problem, not a sign problem.

## The binding constraint (owner-acknowledged, not resolved here)

`test_r9d_s5_fold_rate_rise_follows_the_defensible_ladder` (`:9452`) asserts the nit shows the
**largest rise** in fold rate under a sustained barrel. A tighter nit has less rise available, so
that gate floors this lever. Measured, deterministic, twice-verified: **0.38 FAIL · 0.40 FAIL ·
0.42 pass · 0.45 pass · 0.60 pass**. Contract-scan refinement: **the floor is not a constant** —
tightening tag moves tag *into* the steep region and raises the nit floor (arm E: tag's rise rose
to 0.1343 while nit's fell to 0.0303). The bracket above holds **only while tag stays at 0.6**,
which this slice guarantees by not touching tag.

**0.45 is chosen for margin, not maximum effect.** It sits 0.03 above the measured failure point on
a deterministic gate. Whether that gate's premise is itself defensible for a genuinely tight nit is
a THEORY question filed to the roadmap (below), deliberately **out of scope here**.

## Measured feasibility (all numbers below are exact — `_dist_for_pack`, no sampling)

| constructed node | nit @0.60 | nit @0.45 | Δ self | tag @0.60 | Δ vs tag |
|---|---|---|---|---|---|
| flop middle pair vs ½-pot | 0.3798 | 0.4495 | **+0.0697** | 0.3265 | **+0.1230** |
| flop top pair vs ½-pot | 0.1197 | 0.1535 | **+0.0338** | 0.0921 | **+0.0614** |
| turn middle pair vs ⅔-pot | 0.6604 | 0.7217 | **+0.0613** | 0.6062 | **+0.1154** |
| flop ace-high vs ½-pot | 0.5863 | 0.6539 | **+0.0676** | 0.5394 | **+0.1146** |
| ~~flop middle pair vs pot-sized~~ | 1.0000 | 1.0000 | +0.0000 | 1.0000 | +0.0000 |

Full vector at the first node, nit @0.45: `{fold 0.4495, call 0.5022, raise 0.0483}`;
@0.60: `{fold 0.3798, call 0.5658, raise 0.0544}`.

**Two results that directly shape the gates:**

1. **Rev 2's proposed "+>0.05" node threshold would have failed a third build.** The top-pair node
   moves +0.0338. A threshold written before measurement picks a number the panel cannot meet.
2. **The pot-sized-bet node is DEGENERATE** — every persona reads 1.000, the fold is already
   forced, the lever has no room. It is **excluded from the panel**, and the initiative's standing
   law (a gate skipping a degenerate cell must prove its anchor was non-degenerate) is discharged
   by an explicit non-degeneracy assertion on every panel node.

## Pre-registered thresholds (derived from the table above, with margin; NOT to be re-chosen)

- **Self leg:** at every panel node, `P(fold | nit @0.45) − P(fold | nit @0.60) ≥ 0.025`.
  Binding node is top pair at +0.0338 → **1.35× margin**.
- **Identity leg:** at every panel node, `P(fold | nit @0.45) − P(fold | tag @shipped) ≥ 0.05`.
  Binding node is top pair at +0.0614 → **1.23× margin**.
- **Non-degeneracy:** at every panel node, for **both** personas and **both** lever values, every
  legal action's probability lies in `[0.01, 0.99]`.
- These are exact-arithmetic comparisons on a deterministic sampler. No σ, no sample size, no
  escalation rule — that is the point of the direction change.

## Files to touch (complete)

1. `content/personas/nit.json` — `call_looseness` 0.6 → **0.45**; **add a `_doc` version array**
   (tag/lag have one, nit does not — `_doc` is a schema-ignored extra key, legal); bump `version`
   (currently 1.5.0). **`continue_ref: 0.6` byte-untouched**, `stickiness: 0.6` byte-untouched.
2. `backend/tests/test_personas_postflop.py` —
   a. **G-NODE panel (new):** the four nodes above, both legs plus non-degeneracy, built on
      `_dist_for_pack` (`:1218`). Node definitions carry their measured baseline in a comment so a
      later reader can tell a re-measurement from a re-pin.
   b. **G-POP (new, REPORT-ONLY, must not gate):** population FtC for nit and tag at the CI posture
      (`context_aware=False`), printed with denominators. **Asserts nothing about the gap.** Carries
      a docstring stating why: at CI n the gap is inside noise, and gating it was measured to need
      n ≈ 75,000 (ledger B-4, B-11). A future W4-b re-anchor gets a baseline from this.
   c. `_GOLDEN_STATS_N200` re-record, "RE-RECORDED for R9-LOOSEFIT" block per the protocol at
      `:3316-3448`, attribution proven by revert per `:3530-3535`.
3. `backend/tests/test_limper_coverage_belt.py` — `_PRE_M3_FIRES` re-record per the protocol at
   `:44-287`, attribution proven by revert per `:277-287`.
4. `docs/ai-dlc/roadmap/persona-realism.md` — mark R9-LOOSEFIT built (nit-only, node-gated);
   record the three filings below.

## Filings (recorded, NOT built here)

- **`N-LADDER-PREMISE`** — is R9-DEFENCE-a's "the nit must show the largest fold-rate rise" premise
  defensible when the nit is genuinely tight? It is the sole constraint floring this lever, and it
  may be a saturation artifact. Route to `persona-realism-theory-reviewer` + owner ruling. If the
  premise falls, the nit window opens to ≈0.31 (H8) and a follow-up can go further.
- **`N-ANCHORSTALE`** — the N-LOGIT G-gate family (`:7085-7832`) stays green at *every* lever value
  because each probe overwrites the lever (`:6899`, `:6928`). `_NLOGIT_ANCHORS`'s comment ("each
  pack's authored anchor == its effective looseness") **becomes false when this slice ships**, and
  nothing goes red. Also: 41 `model_copy(update=` sites exist in the test tree and only the
  lever-touching ones were audited — the same staleness idiom may be elsewhere.
- **`N-TAGPIN`** — tag's `call_looseness` is immovable until `test_elasticity_split_...` (`:1321`)
  is re-scoped onto a **fully synthetic** pack (repointing at another shipped pack only moves the
  pin), which is a prerequisite of ever authoring `size_elasticity` on tag. Carries the four
  `_W3R6_RAISE_DROP` pins (`:6260`), which have **no documented re-record protocol**.

## Out of scope

tag and lag `call_looseness` (H1/H2/H6 — see `N-TAGPIN`) · `continue_ref` and `stickiness` on any
pack · BANDS values (frozen to W4-b) · re-opening R9-DEFENCE-a's ladder (see `N-LADDER-PREMISE`) ·
the N-LOGIT anchor staleness (see `N-ANCHORSTALE`) · `line_aware` passthrough · engine code
(`personas_postflop.py` untouched) · `_persona_stats`'s signature or 6-tuple · `spot_signature()` ·
the shares accessor from the halted build (commit `7736156`) — **rev 3 does not need it**, and a
decision on whether to keep, gate, or drop it is deferred to `N-ANCHORSTALE`'s ticket.

## Constraints (repo + initiative law)

Strategy lives in versioned `content/` data — one pack value, tests and docs only, zero engine
code. Domain core `backend/app/domain/` has no web/DB imports. Every gate asserts that something
MOVED or kills a named mutant — never merely that two things agree. Thresholds derive from
measurement recorded in this spec and are never re-chosen after seeing a result. Only
`_GOLDEN_STATS_N200`, `_PRE_M3_FIRES` and the coverage baseline may be re-recorded, each under its
own protocol with attribution proven by revert; **any other fixture that moves is a defect to
investigate, not a re-record.** Git: own worktree, immutable-OID push, bare git, no pipes, absolute
paths; PR on `feat/*`; never merge. **Suite results read from a file, never a piped exit code.**
Base verified green before branching.

## Verify-by

1. Base green from a file, unpiped (`1416 passed, 1 skipped` at b63dfaa) → branch.
2. `./scripts/verify.sh` → `BACKEND VERIFY OK` · `cd backend && ruff check .` clean · full suite
   green unpiped.
3. **Exactly three tests move, and no others.** Expected: `_GOLDEN_STATS_N200` and `_PRE_M3_FIRES`
   re-recorded; the new G-NODE panel green. The coverage baseline (`test_coverage_baseline.py`) was
   measured **green** at nit 0.42 in the contract scan's arm A — if it moves at 0.45, that is a
   finding to report, not a re-record to perform silently.
4. **`test_price_tail.py`, `test_node_trace.py`, `test_mw_catch_toppair.py` and
   `test_arrival_range_ftc.py` green WITHOUT edit** — all four were measured structurally unreachable
   by this lever (contract scan §3).
5. **Sensitivity proven by revert:** restore nit to 0.6 → every G-NODE leg red; golden and limper
   belt reproduce their old bytes exactly.
6. **Mutant check by an agent that did not write the gates:** a `call_looseness` no-op mutant (lever
   read but discarded) must die on the G-NODE self leg; a mutant that scales CALL but not RAISE must
   leave the self leg green and is therefore explicitly NOT what G-NODE tests — state that limit in
   the gate's docstring rather than pretending coverage it does not have.
7. Dual adversarial review of the diff (`refuter` + Codex Sol) + `persona-realism-theory-reviewer`
   at fan-in; every finding adjudicated into `ledger/r9-loosefit.md`.
