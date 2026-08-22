# Persona-Realism Harness Fit Loop (D11)

> The repeatable loop every behavior slice runs to turn a grounded *direction*
> into a *fitted magnitude*, plus the single-re-anchor rule. Referenced from the
> W0 spec (`persona-realism-w0-foundation.md`) and the roadmap's cross-cutting
> discipline (`docs/ai-dlc/roadmap/persona-realism.md`).

## Why a loop, not a constant (the softmax law)

The engine clamps each candidate merit `≥0`, normalizes by the sum, then draws
via `rng.choices`. **A merit multiplier is therefore NOT the observed frequency
change** (theory contract §2). Dropping `×0.75` / `×0.50` into the code and
closing the slice ships a *cosmetic* change — the observed stat has not moved to
target. Every magnitude in the build spec is a **fit seed**, not an answer.

## The loop (per behavior slice)

1. **State the target as an observed stat**, not a merit. A CBet-flop split, an
   AF, a WTSD, a size-bucketed fold-to-cbet slope — a number a harness metric
   emits (theory contract §5/§6). Not "the multiplier is 0.5".
2. **Seed the multiplier** with the build-spec's directional value. When more
   than one lever feeds the same target stat pair, pair each lever with the
   stat it dominates before seeding — see "Multi-lever fitting" below (Rule 1a).
3. **Measure** the relevant metric via the harness (`_persona_stats` for the
   three HARD-today stats; `_persona_stats_ext` for the six W0-b metrics).
4. **Adjust the seed** toward the target band and re-measure. Repeat until the
   *observed* stat lands (or is provably directional if the metric is not yet
   HARD-gatable — see the Metric-DoD rule). When adjusting more than one lever
   across rounds, re-estimate the step from the last two measurements rather
   than reusing a saved slope — see "Multi-lever fitting" below (Rule 2).
5. **Check the node, not just the number** — run the seeded node-trace pack
   (`backend/tests/node_trace.py`) for the affected personas/spots and confirm
   the *shape* of the decision is coherent (e.g. a maniac hitting its aggression
   number by bluffing air, not by over-valuing made hands). This catches "right
   stat, WRONG node".

## Precedents already in the tree

- **The band fit loop** that produced the current `BANDS` is documented inline
  at `backend/tests/test_personas_postflop.py` — `BANDS` dict ~:2563,
  `_persona_stats` ~:2634 at `b63dfaa` (measure → 3σ CI → round outward).
  Reuse that method; do not invent a second.
- **The six new metrics** (`_persona_stats_ext`) are the measuring tape for the
  mechanics that were previously prose-only.
- **The node-trace pack** (`node_trace.py`) is the anti-degeneracy check.

## Multi-lever fitting — measured rules (N-vecfit, 2026-08-03)

A pre-spec measurement (`docs/ai-dlc/reports/n-vecfit-premise.md`, including
its Post-review corrections section) tested whether the scalar, one-lever-
at-a-time loop above zig-zags on the coupled `call_looseness`/`aggression`
system and found the expensive-zig-zag premise **unsupported where tested**
(tag/nit, the (FtC, AF) stat pair, context-aware/line-blind posture — see
`docs/ai-dlc/roadmap/persona-realism.md`'s N-vecfit entry for the full scope
qualifier). The measurement's transferable value is these rules, not a new
tool:

- **Rule 1a — pair each lever with the stat it dominates (scalar fits).**
  `call_looseness`→FtC, `aggression`→AF. Mispairing is a *scalar-assignment*
  failure: the swapped pairing measured a spectral radius ρ = 5.47 and
  empirically diverged. Check before fitting: ρ = |J12·J21/(J11·J22)| < 1.
  **The ρ screen tolerates an approximate or previously measured Jacobian** —
  the measured margin is 5× (ρ = 0.183 vs the ρ ≥ 1 failure threshold), so a
  stale J is fine HERE (unlike Rule 2's step sizes, where it is not). New
  persona/stat-pair combinations need a one-time ~2–4-call J measurement,
  amortized across all later fits of that combination; this cost is disclosed,
  not hidden.
- **Rule 1b — target-pair conditioning (any method, including joint fits).**
  A distinct hazard from mispairing: near-parallel Jacobian ROWS (e.g. FtC +
  RaiseShare — the raise share of aggressive actions, as measured by the band
  harness) make the fit ill-conditioned for scalar AND vector methods
  alike — a joint solve is permutation-invariant, so pairing cannot rescue it;
  only re-choosing target stats can. The `calling_station`'s cond(J) = 14.3 on
  an air-heavy range (`docs/ai-dlc/contracts/n-vecfit.md`) is this hazard, not
  mispairing. If no well-conditioned target pair exists, escalate to the
  roadmap rather than fit through it.
- **Rule 2 — fresh slopes for STEP SIZES, never a saved table.** Re-estimate
  each 1-D slope by secant from the last two measurements **with all other
  levers held fixed between those two points** (moving two levers between
  measurements confounds the secant — measured post-review). The harness is
  nonlinear enough that a base-point slope under-predicts far-field gain
  ~1.45×, which is what made a fixed-Jacobian Newton arm ring past its call
  cap while the secant-based scalar loop converged. Initial slope: from the
  Rule-1a J if fresh enough, else one probe step. Caveat: a secant across a
  non-monotone region is unguarded — every stat-vs-lever curve the study
  measured was strictly monotone (5-point `call_looseness` ladder, premise
  report §1), so this regime is untested; if a slope changes sign between
  measurements, stop and measure a local J.
- **Rule 3 — budget n so the 3σ noise band is smaller than the move.** At
  n = 48,000: FtC band ±0.0234, AF ±0.0852; a ±25% `call_looseness` step moves
  FtC ≈ 0.032 (|J11|·ln 1.25) ≈ 1.35 tolerance units — barely resolvable. The
  harness is deterministic-seeded and memoized per pack-fingerprint; common
  random numbers make paired differences cleaner than the independent bound.

**Instrument facts:** ~105–138 s/call at n = 48,000; ≤3 measurement processes
in parallel (6 concurrent measured a ~40× per-process slowdown, i.e. worse
aggregate throughput than serial — batch measurement runs at ≤3 concurrent).
`_persona_stats` cannot pass `line_aware` (forwards only `context_aware`) —
**a disclosed limitation, not a blessing**: no measurement establishes lever
fits are invariant to line-awareness, and W4-b-grade work (the single
authoritative population-band re-anchor that closes the persona-realism
roadmap's `W4-b` slice) requires `context_aware=True` AND `line_aware=True`
(the adjudication record in [`R9-DEFENCE-a`'s ledger](../ledger/r9-defence-a.md),
the fan-in review file for the line-keyed continue-shift slice). The fitter
that needs the production posture must first give the harness a `line_aware`
passthrough.

**Metric-DoD (D7) reading for procedure-only slices:** a slice that changes no
pack values (like this one) moves no observed stat, so there is nothing to
HARD-gate on the loop above; the gate for a procedure-only slice is
traceability of its claims plus adversarial review, not a live metric
direction.

## Two rules that bound the loop

- **Metric-DoD (D7):** a slice may not close on a HARD gate until the metric it
  needs is *live AND showing the expected direction*. Until then the gate is
  DIRECTIONAL, not HARD (theory contract §6). W0-b made the six metrics live;
  each later slice supplies the direction.
- **Single re-anchor at the cluster end (D11):** the population WTSD/AF bands are
  moved by several mechanics (P3/P5/P6/P8). **Re-anchor them ONCE, after the
  whole cluster lands (Wave 4)** — never mid-spine. Re-anchor levers-first (tune
  pack levers before widening test bands). The only early-wave test edit is P5's
  unit-assertion split. Chasing bands across waves re-fits values that the next
  slice moves again (theory contract §7).
