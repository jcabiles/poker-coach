# Spec — R9-LOOSEFIT: fit `call_looseness` for nit / tag / lag (separation inside the frozen bands)

status: **rev 2 SUPERSEDED — build halted at T1, awaiting rev 3** (owner ruling 2026-08-03).
Rev 2's own instruction to measure against the real pytest gates found that no operating point
satisfies its pre-registered criteria alongside the existing HARD gates. Read the build findings
**B-1…B-10 in `ledger/r9-loosefit.md`** and `reports/r9-loosefit-t1-measurement.md` BEFORE
re-reading anything below: the seed is illegal, the gate design is unreachable, and the background
section's "nit measurably folds less than tag" is a statistical tie at stable n.
Rev-2 history (rev 1: refuter FAIL 2H/2M + Codex NEEDS-WORK 4H/6M/1L — all 15 findings
adjudicated in `ledger/r9-loosefit.md`, every accepted fix folded below)
slice: r9-loosefit · initiative: persona-realism · code pin: origin/main = b63dfaa
roadmap anchor "R9-LOOSEFIT — fit `call_looseness`" · contracts: `contracts/r9-loosefit.md` ·
feasibility: `reports/r9-loosefit-feasibility.md` (read WITH its posture caveat, added rev 2)
citation convention: code @ b63dfaa; ai-dlc docs @ working tree, anchors authoritative.

## One-line goal

Give nit, tag, and lag distinct `call_looseness` values so nit is the measurably tightest
defender — gated by a separation test with pre-registered threshold rules — while every frozen
HARD band and ordering gate stays green **at its own CI posture** and `continue_ref` never moves.

## The posture lesson (rev-2 core — Codex C-1/C-2)

The CI gates run `_persona_stats(packs, persona, per_persona_n)` with **`context_aware=False`,
`per_persona_n = 600`** (with documented escalate-to-larger-n rules; WTSD ordering at n = 4,000).
The feasibility study measured at `context_aware=True`, n = 24k/48k — **a different posture**.
A read-only review probe measured the rev-1 seed at the CI posture: nit AF ≈ 2.4167, OVER the
2.4 band ceiling. Consequence, now spec law: **a value passes only when measured at the exact
posture and n of the gate that will judge it.** The feasibility windows remain valid as
production-posture geography (slopes, coupling, direction, headroom structure); the specific
seed values are STARTING POINTS for T1's gate-posture fit, not promises.

## Background (measured; feasibility report + its rev-2 caveat)

- Defect: nit and tag both author 0.6; population FtC gap −0.0121 at 48k/True posture (tie,
  sign inverted); at the review probe's 4k/False posture the base gap is −0.063. Nit folds less
  than tag — backwards — at every posture measured.
- Separation is achievable in-band at production posture (gap +0.297 = 7.3× paired 3σ at the
  measured point); the ordering gate, not the bands, is the binding constraint (tag window
  [0.346, 0.658], lag [0.442, 0.794], others-at-anchor; windows widen jointly).
- rscale goes live for the first time (nit ≪1, tag/lag slightly >1). Measured: AF response bends
  2–4.5× below anchor → fresh secants on AF; FtC slope flat (−0.15..−0.19) → anchor-seeded FtC
  steps safe. N-LOGIT theory (verified by its own 1e-12 gate): the CONDITIONAL raise share
  RAISE/(RAISE+CALL) at a fixed facing node is **invariant** in `call_looseness` (both merits
  scale ∝ cl); the ABSOLUTE raise probability falls with cl at fold-legal nodes. G-RS is built
  on exactly this (rev-1 had the direction wrong — C-3).
- Cross-persona coupling: all 36 measured displacement deltas within own 3σ, but WTSD
  displacement (±0.011) exceeds thin loose-edge margins — hence the pre-registered margin rules.

## Seed and fit procedure (T1)

Seed nit **0.08** / tag **0.63** / lag **0.62** — production-posture starting point only. T1:

1. **Measure at the gate postures first:** run the ACTUAL pytest gates (band test, fixed-size
   ordering test, WTSD ordering) on the seeded packs, plus explicit `_persona_stats` reads at
   n = 4,000 both postures. The gates' own verdicts decide; no posture proxying.
2. **Pre-registered acceptance criteria** (fine-tune per fit-loop rules until ALL hold —
   anchor-seeded steps on FtC, fresh secants on anything AF-coupled):
   a. every HARD gate green at its own posture/n;
   b. fixed-size ordering margins **≥ 0.035** (≈2.5 fixture-σ) on every leg touching nit/tag/lag;
   c. WTSD margin **≥ 0.02** to the loose band edge for tag and lag at the band gate's posture;
   d. separation and raise-share readings recorded (below) with denominators ≥ 30 per stat.
3. **Rule-1 conditioning deliverable (C-8):** document that the fit is one lever per persona
   paired cl→FtC (Rule 1a; no 2×2 ρ applies); MEASURE the cross-persona coupling at the gate
   posture (re-measure the other two at each mover's final value); escalation criterion: any
   cross-persona delta > its 3σ ⇒ one joint re-fit round of the trio.
4. **Threshold derivation for G-SEP/G-RS** by the pre-registered rules below — T1 outputs the
   numbers; the RULES are fixed here and are not T1's to choose.
5. Output: final trio values + full measurement table (both postures) + chosen thresholds +
   margins — verbatim into the PR body and the tickets file.

## Files to touch (complete)

1. `content/personas/nit.json` — `call_looseness` → fitted; ADD `_doc` version array (tag/lag
   convention; `_doc` is a schema-ignored extra key — legal, C-11); **pack `version` bump**;
   `continue_ref: 0.6` untouched.
2. `content/personas/tag.json` — `call_looseness` → fitted; `_doc` entry; version bump;
   `continue_ref: 0.6` untouched.
3. `content/personas/lag.json` — `call_looseness` → fitted; `_doc` entry; version bump;
   `continue_ref: 0.55` untouched.
4. `backend/tests/test_personas_postflop.py` —
   a. **Shares accessor (C-4/R-1):** `_persona_stats`'s public 6-tuple and every existing call
      site stay UNTOUCHED. Add a sibling accessor (e.g. `_persona_stats_shares(packs, persona,
      n, *, context_aware=False)`) that shares the same play loop and memoized cache internals
      (extend the cached record; slice per accessor) and returns facing-node counters: absolute
      raise probability and conditional raise share RAISE/(RAISE+CALL), counted ONLY at
      fold-legal facing nodes (excludes SPR-committed — contract §4), plus their denominators.
   b. **G-SEP (new test):** FtC(nit) − FtC(tag) > T_sep at **explicitly named posture and n**
      (n = 4,000, `context_aware=False`, both denominators asserted ≥ 30). T_sep from T1 by the
      pre-registered rule: **≥ 3σ_gap above 0 AND ≥ 3σ_gap below the measured fitted gap**
      (σ_gap = paired noise at the gate's own n; symmetric flake/false-pass protection — same
      construction the feasibility report used). Red at base by construction (base gap negative
      at both postures).
   c. **G-RS (new test, rebuilt per C-3/C-5):** two legs at the same named posture/n, per
      persona (nit/tag/lag): (i) **invariance leg** — conditional raise share within ±3σ of its
      base-pack value (σ from the gate-n noise measured in T1; band width is THIS formula, no
      wider — kills the call-only misroute mutant, which breaks proportional scaling);
      (ii) **absolute leg** — nit's absolute facing-node raise probability strictly below its
      base value by > 3σ (rscale ≈ 0.13 must show; a no-op fails this leg). Denominator floors
      ≥ 30 asserted.
   d. **G3 wording amendment (C-10):** `_nlogit_probe(mult=1)` reconstructs the CALIBRATION
      ANCHOR, no longer the shipped value — amend that test's docstring/name accordingly
      (behavioral assertions unchanged).
   e. **`_GOLDEN_STATS_N200` re-pin** — protocol re-record, "RE-RECORDED for R9-LOOSEFIT"
      block, attribution proven by revert (W3R-2 precedent).
5. `backend/tests/node_trace.py` + `backend/tests/test_node_trace.py` — **G-NODE probe
   (C-7/R-4):** add ONE crafted facing bluff-catcher node (the trace pack's own disclosure: none
   exists today) — e.g. flop OOP middle-pair facing a ½-pot bet, HU, moderate SPR — traced for
   nit and tag. Assert post-fit: nit's FOLD probability at the node exceeds its base-pack value
   by > 0.05 (sensitivity — a no-op fails), AND every legal action's probability ≥ 0.01
   (explicit ε non-degeneracy), AND the node is reached by construction (crafted spot).
   Existing pins untouched.
6. `docs/ai-dlc/roadmap/persona-realism.md` — mark built; W4-b note (lag "defends widest"
   unreachable under WTSD ceiling 0.59 — widen at W4-b or drop); **R9-DEFENCE-b rebaseline
   note (C-9):** its inherited absolute raise-frequency numbers were measured at rscale = 1 and
   are stale after this slice — rebaseline before building.
7. `docs/ai-dlc/reports/r9-loosefit-feasibility.md` — append the **posture caveat** (rev-2):
   windows/verdict measured at `context_aware=True`; CI gates judge at `False`/n=600-escalation;
   seed values are production-posture starting points (C-1). Report history preserved, caveat
   additive.

## Gates

| gate | what | base status | falsifiability |
|---|---|---|---|
| G-SEP | FtC gap > T_sep at named posture/n, denominators asserted | **RED** (gap negative at both postures) | red-at-base |
| G-ORD | existing fixed-size ordering test green; T1-reported margins ≥ 0.035 on nit/tag/lag legs | green | ordering flip kills |
| G-BAND | existing band test green at ITS posture — no band value edited | green | out-of-band kills |
| G-RS-i | conditional raise share within ±3σ of base, per persona | green-by-theory | call-only misroute mutant breaks invariance → dies |
| G-RS-ii | nit absolute raise probability < base by > 3σ | RED at base (no movement) | no-op dies |
| G-REF | G9 green; shipped `continue_ref` bytes unchanged | green | re-sync dies |
| G-GOLD | golden re-pin, revert-proven attribution | — | protocol |
| G-NODE | new facing-node probe: nit FOLD +>0.05 vs base, all legal actions ≥ 0.01 | RED at base (fold delta 0) | no-op dies; degenerate collapse dies |

## Out of scope

BANDS values (frozen until W4-b) · `line_aware` passthrough (W4-b, owner-ruled) · general
fold-share counter + committed-node AF split (W4-b) · station/fish/maniac packs (price-tail
frozen vectors pin station+fish) · `aggression` and all other levers · engine code
(`personas_postflop.py` untouched) · `_persona_stats` signature/return (sibling accessor only) ·
`spot_signature()` · estimator (`range_estimate.py` — zero cl dependency, contract §1).

## Constraints (repo + initiative law)

Strategy lives in versioned `content/` data — pack values + tests + docs only. Every gate
asserts movement or kills a named mutant; thresholds derive from pre-registered RULES, never
chosen after seeing whether they pass. Fixture law: only `_GOLDEN_STATS_N200` re-pins, under
protocol. Fit-loop rules bind (pairing cl→FtC; fresh secants on AF-coupled steps; noise budget
per stat/n; ≤3 parallel measurement processes). Git: own worktree, immutable-OID push, bare, no
pipes, absolute paths; PR on `feat/*`; never merge. Suite results read from a file, never a
piped exit code. Base verified green before branching.

## Verify-by

1. Base green (unpiped, from file) → branch from `origin/main`.
2. T1 report in PR body: both-posture measurement table, final values, thresholds via the
   pre-registered rules, all margins (2a–2d) — numbers, not adjectives.
3. `./scripts/verify.sh` → BACKEND VERIFY OK · `ruff check .` clean · full suite green unpiped ·
   `test_price_tail.py` green WITHOUT edit.
4. Sensitivity proven by revert: packs restored to 0.6/0.6/0.55 → G-SEP, G-RS-ii, G-NODE all
   red; G-RS-i stays green (invariance is value-independent — that asymmetry is itself the
   misroute discriminator).
5. Mutant check at fan-in (agent independent of the gate authors): the call-only misroute mutant
   (scale CALL merit, leave RAISE unscaled) must die on G-RS-i; a `call_looseness` no-op mutant
   must die on G-SEP + G-RS-ii + G-NODE.
6. Golden attribution: revert pack edits → old golden byte-identical.
7. Dual adversarial review of diffs (refuter + Codex Sol) + `persona-realism-theory-reviewer`
   at fan-in; findings adjudicated to `ledger/r9-loosefit.md`.
