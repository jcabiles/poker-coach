# N-vecfit premise test — does the scalar fit loop actually zig-zag?

> Measurement report, 2026-08-03, pinned `origin/main` = **b63dfaa** (verified `git rev-parse --short HEAD`).
> Tests the claim in `docs/ai-dlc/roadmap/persona-realism.md:2001-2011` that
> `persona-realism-fit-loop.md` steps 2–4 (a **scalar**, one-lever-at-a-time loop) "zig-zags"
> on the coupled `call_looseness` / `aggression` system, and that a joint (vector) fit
> "converges in far fewer measurements".
> **No repo file was changed by this work except this report.** All scripts lived in a scratchpad.

## VERDICT — **PREMISE FAILS**

On the real harness, the scalar loop converged in **2 harness calls** (near target) and
**3 harness calls** (far target), monotonically, with **no zig-zag and no oscillation**. The
vector arm prescribed by the premise (Newton with a re-used Jacobian) took **1 call** on the near
target but **failed to converge within its 5-call cap on the far target, oscillating** with a
slowly-damped alternating AF error (+5.3, −4.2, +2.6, −2.3, +2.0 tolerance units). Counting the
4 extra calls a vector fit needs to *build* the Jacobian, the scalar loop was cheaper end-to-end on
both targets (2 vs 5; 3 vs 9).

Theory agrees with the trajectories: the Gauss–Seidel spectral radius of the measured 2×2
linearization is **ρ = 0.183 for `tag`** and **ρ = 0.021 for `nit`** — coordinate descent contracts
the coupling error **5.5×** and **48×** *per round*. For the premise to hold (ρ ≥ 1) the measured
`∂FtC/∂ln(aggression)` would have to be ~5.5× larger than measured — far outside its noise band.

**Two findings that do survive, and they are cheaper than a vector fitter:**

1. **The hazard is target *pairing*, not scalar-vs-vector.** With the levers paired to the wrong
   stats (`call_looseness`→AF, `aggression`→FtC) the same measured Jacobian predicts ρ = 5.47
   (divergent), and the empirical run **did diverge**, running both levers into their guard rails
   (`call_looseness` 0.155, `aggression` clamped at the 5.6 cap) and ending 3.4 tolerance units
   worse than it started.
2. **A *fixed* Jacobian is the fragile object here.** The harness is materially nonlinear over a
   real fit distance: local `dAF/dln(agg)` near `agg ≈ 4–5` is ≈ 1.57 versus 0.714 measured at the
   authored point — a 2.2× gain error, which is exactly what made the stale-J Newton overshoot and
   ring. The scalar loop is robust to this *because* re-measuring after each adjustment gives it a
   fresh secant slope for free. A Broyden-updated (self-correcting) vector arm, added for fairness,
   did converge — in 5 calls, still slower than scalar's 3.

## 1. Setup

| item | value |
|---|---|
| instrument | `_persona_stats(packs, persona, n, context_aware=True)` — `backend/tests/test_personas_postflop.py:2634` |
| subject | `tag` (authored `aggression` 2.4, `call_looseness` 0.6, `continue_ref` 0.6) |
| coordinates | x = (ln `call_looseness`, ln `aggression`); y = (FtC, AF) |
| lever mutation | in-memory `PersonaPostflop.model_copy(update=...)`; **`continue_ref` held at 0.6, never re-synced** (N-LOGIT frozen anchor) |
| n per call | **48,000 hands** (pilot sweeps at 6,000) |
| denominators (tag, n=48k) | FtC: 3,427 c-bet-facing opportunities · AF: 8,555 calls / 18,603 bet+raise |
| **3σ noise floor = fit tolerance** | **FtC ±0.02344 · AF ±0.08522** |
| wall time | 13.8 s/call at n=6,000; **105–138 s/call at n=48,000** |
| total cost | 46 harness calls (44 distinct), **123 CPU-minutes**, ≈ 55 min wall |

**Concurrency note (instrument fact worth keeping):** running 3 measurement processes in parallel
costs nothing per process (14.0 s vs 13.8 s serial at n=6,000). Running **6** in parallel is
pathological — every process slowed ~40× (520 s each), i.e. aggregate throughput 6× *worse* than
serial. Batch measurement runs at ≤3 concurrent processes.

### Deviations from the brief's measurement design (disclosed)

- **The 5×-noise perturbation criterion could not be met at feasible n.** A ×1.3 `call_looseness`
  perturbation moves FtC by ~0.017–0.036 — about **1.5× the 3σ band**, not 5×. Reaching 5× needs
  ≈ 250k hands/call (~9 min/call, ~7 h for the study). Instead the Jacobian was taken by **central**
  differences over ±25%, whose entries resolve at |t| = 6.6 / 5.9 / 9.1σ (three entries) and 1.9σ
  (the weak off-diagonal `∂FtC/∂ln agg`) against independent-sample noise. Common random numbers
  make the true paired-difference noise smaller than that bound: a 5-point `call_looseness` ladder
  at n=6,000 (0.40/0.45/0.60/0.78/0.90 → FtC 0.380/0.340/0.297/0.279/0.250) is **strictly
  monotone** with per-step gaps of ~1.4 independent-σ, which is not what independent noise does.
- **Call budget exceeded (46 vs ~30).** The extra calls bought the two fairness arms (Broyden
  vector, swapped pairing) that make the verdict defensible rather than a strawman.
- **The measurement is LINE-BLIND.** `_persona_stats` forwards only `context_aware` to `_play_hand`
  (`:2668-2670`); `line_aware` is not reachable from it and defaults `False`. Per
  `contracts/n-vecfit.md:41-45`, a production-faithful (W4-b-grade) Jacobian needs
  `context_aware=True` **and** `line_aware=True`. The harness was **not** modified to expose it, so
  every number below is the context-aware / line-blind posture.

## 2. Measured Jacobian

Central differences at ±25% on each lever (Δln = 0.51083), n = 48,000, `context_aware=True`.
Rows = (FtC, AF); columns = (∂/∂ln `call_looseness`, ∂/∂ln `aggression`). `±` is the
independent-sample 1σ bound (conservative — CRN pairing makes the real difference noise smaller).

**`tag` @ (0.6, 2.4)** — base FtC 0.29793, AF 2.17452

|  | ∂/∂ln cl | ∂/∂ln agg |
|---|---|---|
| **FtC** | **−0.14204** ± 0.02163 (t = 6.6) | **−0.04009** ± 0.02163 (t = 1.9) |
| **AF** | **−0.46284** ± 0.07864 (t = 5.9) | **+0.71400** ± 0.07864 (t = 9.1) |

- off/diag ratios: J12/J11 = **+0.282**, J21/J22 = **−0.648**
- cond(J) raw = **6.05**; cond(J) with rows scaled to tolerance units = **1.75**
- **Gauss–Seidel spectral radius ρ = |J12·J21 / (J11·J22)| = 0.1829** → 5.5× error contraction per
  scalar round (pairing cl→FtC, agg→AF). Reversed pairing: **ρ = 5.47** (divergent).
- Independent cross-check from the wider n=6,000 sweep (cl 0.40→0.90, agg 1.80→4.00):
  J = [[−0.1597, −0.0303], [−0.3781, +0.7181]], **ρ = 0.100**. Same conclusion at a different n and
  a different step size.

**`nit` @ (0.6, 0.6)** — base FtC 0.28579, AF 1.21356 (secondary check)

|  | ∂/∂ln cl | ∂/∂ln agg |
|---|---|---|
| **FtC** | −0.16192 ± 0.02788 (t = 5.8) | **+0.01326** ± 0.02788 (t = 0.5 — statistically zero) |
| **AF** | −0.17946 ± 0.05893 (t = 3.0) | +0.69767 ± 0.05893 (t = 11.8) |

cond(J) raw 4.72 / tolerance-scaled 2.29; **ρ = 0.0211**. `tag` is the *more* coupled of the two,
so the premise was tested on the harder of the two personas, not an easy one.

**Reading:** the coupling is real but **one-sided**. `call_looseness` genuinely reaches AF
(J21 = −0.463, 5.9σ — the N-LOGIT `rscale` route). `aggression` barely reaches FtC
(J12 = −0.040, 1.9σ on `tag`; ~0 on `nit`). Coordinate descent's contraction depends on the
**product** of the two off-diagonals, so one strong + one ~null = strongly convergent.

## 3. Ground-truth recoverability

Two shifted true points were measured; their stats are the targets (feasible by construction, and
the harness is deterministic, so the answer is exactly attainable). Both procedures start from the
authored point (0.6, 2.4) and are given the **same** measured slope information — the scalar arm is
seeded with J11/J22, so the comparison isolates the *coupling*, not derivative knowledge. Errors
below are in tolerance units (1.0 = the 3σ band).

### Target A = (cl 0.45, agg 3.0) → FtC 0.33802, AF 2.51054 · start error (−1.71, −3.94)

**SCALAR** (cl→FtC, then agg→AF)

| call | cl | agg | FtC | AF | e(FtC) | e(AF) |
|---|---|---|---|---|---|---|
| 1 | 0.45246 | 2.4 | 0.33939 | 2.29082 | +0.06 | −2.58 |
| 2 | 0.45246 | 3.2648 | 0.32848 | 2.49456 | −0.41 | −0.19 |

**CONVERGED in 2 calls**, first round, monotone — no overshoot beyond tolerance on either stat.

**VECTOR** (Newton, re-used J)

| call | cl | agg | FtC | AF | e(FtC) | e(AF) |
|---|---|---|---|---|---|---|
| 1 | 0.42245 | 3.06071 | 0.34028 | 2.56016 | +0.10 | +0.58 |

**CONVERGED in 1 call.** (Plus the 4 perturbation calls that produced J → 5 end-to-end.)

### Target B = (cl 0.30, agg 4.2) → FtC 0.38034, AF 3.13037 · start error (−3.52, −11.22)

A deliberately harder, more distant target — the regime where zig-zag should appear if it exists.

**SCALAR**

| call | cl | agg | FtC | AF | e(FtC) | e(AF) |
|---|---|---|---|---|---|---|
| 1 | 0.33587 | 2.4 | 0.39000 | 2.48822 | +0.41 | −7.54 |
| 2 | 0.33587 | 5.3413 | 0.35335 | 3.31614 | −1.15 | +2.18 |
| 3 | 0.33587 | 4.46365 | 0.37405 | 3.13205 | −0.27 | **+0.02** |

**CONVERGED in 3 calls**, still inside round 1. `call_looseness` was never revisited: the FtC
coordinate stayed inside tolerance while `aggression` moved 2.4 → 5.34 → 4.46, i.e. the coupling
the premise predicts would force a second cl pass **did not materialise**. Call 2 overshoots AF
(the seeded slope under-predicts the far-field gain); call 3 fixes it from the measured secant.

**VECTOR** (Newton, re-used J — the premise's procedure)

| call | cl | agg | FtC | AF | e(FtC) | e(AF) |
|---|---|---|---|---|---|---|
| 1 | 0.27063 | 5.34130 | 0.38578 | 3.58251 | +0.23 | +5.31 |
| 2 | 0.32511 | 3.19351 | 0.37750 | 2.77281 | −0.12 | −4.20 |
| 3 | 0.28366 | 4.82344 | 0.38382 | 3.35454 | +0.15 | +2.63 |
| 4 | 0.31210 | 3.74897 | 0.37808 | 2.93069 | −0.10 | −2.34 |
| 5 | 0.28806 | 4.70764 | 0.38647 | 3.29736 | +0.26 | +1.96 |

**NOT CONVERGED at the 5-call cap — alternating AF error with a ~0.8 damping ratio.** The
oscillation is *the vector arm's*, and it is a stale-Jacobian artifact: between calls 1 and 2 the
realised local gain `dAF/dln agg` was 1.57 versus the 0.714 in J, so each Newton step over-corrects
by ~2.2×. Note the FtC coordinate is dead-on the whole time — this is a 1-D failure inside the
2-D method, not a coupling failure.

### Fairness arm 1 — VECTOR with Broyden update (J re-estimated from each measurement)

| call | cl | agg | FtC | AF | e(FtC) | e(AF) |
|---|---|---|---|---|---|---|
| 1 | 0.27063 | 5.34130 | 0.38578 | 3.58251 | +0.23 | +5.31 |
| 2 | 0.30640 | 3.74336 | 0.38821 | 3.04273 | +0.34 | −1.03 |
| 3 | 0.31323 | 4.08086 | 0.37769 | 3.03418 | −0.11 | −1.13 |
| 4 | 0.29147 | 4.48198 | 0.38713 | 3.23617 | +0.29 | +1.24 |
| 5 | 0.30488 | 4.32485 | 0.38881 | 3.16227 | +0.36 | +0.37 |

**CONVERGED in 5 calls** (+4 for the initial J = 9 end-to-end) vs scalar's 3. Self-correction fixes
the ringing; it does not make the vector method cheaper. Its final updated
J = [[−0.066, −0.130], [−1.209, +0.546]] is also badly contaminated by noise-driven rank-1 updates
— a warning for any tool that would *keep* a Broyden Jacobian.

### Fairness arm 2 — SCALAR with the WRONG pairing (cl→AF, agg→FtC), predicted ρ = 5.47

| call | cl | agg | FtC | AF | e(FtC) | e(AF) |
|---|---|---|---|---|---|---|
| 1 | 0.26960 | 2.4 | 0.41344 | 2.58168 | +1.41 | −6.44 |
| 2 | 0.12114 | 2.4 | 0.54274 | 3.47351 | +6.93 | +4.03 |
| 3 | 0.16480 | 2.4 | 0.50101 | 3.04356 | +5.15 | −1.02 |
| 4 | 0.15487 | 2.4 | 0.51159 | 3.11798 | +5.60 | −0.15 |
| 5 | 0.15487 | 5.34130 | 0.46398 | 4.29996 | +3.57 | +13.72 |
| 6–8 | 0.15487 | 5.6 (capped) | 0.46084 | 4.30272 | +3.43 | +13.76 |

**DIVERGED**, exactly as the spectral radius predicts: `call_looseness` driven to 0.155 (a quarter
of authored) chasing AF, then `aggression` pinned at the `_AGGRESSION_CAP` guard, ending **worse
than the start on both stats**. This is the failure mode the roadmap attributes to "scalar" — but
it is caused by *pairing*, and it is equally fatal to a vector fit (the same mispairing makes rows
near-parallel, which is the cond(J) = 14.3 station caveat the contract scan already flags).

## 4. What this means for the slice (evidence, not a decision)

- The premise as written — "the scalar loop zig-zags, a vector fit converges in far fewer
  measurements" — is **not supported** at `tag`'s or `nit`'s authored points, on either a near or a
  far target, with either a stale-J or a Broyden vector arm.
- The measured system is, in the units that matter (noise bands), **nearly orthogonal**:
  tolerance-scaled cond(J) = 1.75 (`tag`) / 2.29 (`nit`).
- What *is* worth writing into `persona-realism-fit-loop.md` is cheap and needs no tool:
  (a) **pair each lever with the stat it dominates** (`call_looseness`→FtC, `aggression`→AF) and
  check the pairing before fitting — mispairing provably diverges;
  (b) **re-estimate the slope from your last two measurements** (secant) instead of re-using the
  seeded slope — that is what absorbed the harness's 2.2× far-field nonlinearity in one call;
  (c) budget `n` so the 3σ band is smaller than the move you are trying to make — at n = 48,000 a
  ±25% lever move is only ~1.5 tolerance units of FtC.
- Residual risk this study does **not** cover: the line-blind posture (§1), personas other than
  `tag`/`nit` (notably `calling_station`, whose contract-scan cond(J) = 14.3, and `maniac`, which
  has no authored `call_looseness`), and target pairs other than (FtC, AF).

## Post-review corrections (2026-08-03, dual adversarial review — see ledger/n-vecfit.md)

Four findings against this report were accepted and correct it as follows. The verdict text above
is left as originally written; read it with these corrections applied.

1. **Call accounting was biased toward scalar (Codex C-2, HIGH).** The scalar arm was seeded with
   the measured diagonal slopes J11/J22, which came from the same 4 central-difference calls
   charged entirely to the vector arm. Consistent accounting: near target scalar **6** vs vector
   **5**; far target scalar **7** vs vector **9** (either arm). Corrected conclusion: scalar is
   *competitive, not dominant, on the near target; cheaper on the far target; and the stale-J
   Newton arm's failure to converge stands unchanged.* The headline "2 vs 5; 3 vs 9" margins are
   withdrawn. (A scalar loop run cold — no pre-measured slopes, first step guessed, secant after —
   was not measured; its cost lies between the two accountings.)
2. **The 2.2× far-field slope was confounded (Codex C-5, MED).** Between the two vector calls used
   for that ratio, BOTH levers moved; the ratio is not a partial derivative. The uncontaminated
   scalar secants (call_looseness fixed) give **~1.45×** the base slope (1.035/0.714, 1.026/0.714).
   Nonlinearity is real and the stale-J ringing it caused is measured fact; the magnitude is ~1.45×,
   not 2.2×.
3. **"Monotone / stayed inside tolerance" overstated (Codex C-6, MED).** ρ ≥ 1 is the threshold for
   failure to *contract*; the signed factor (−0.183) predicts rapidly *damped alternation*, which is
   what scalar showed. And on the far target, scalar call 2's FtC error was −1.15 tolerance units —
   briefly OUTSIDE tolerance — before call 3 landed both. "Converged in 3 calls" stands;
   "monotone, never left tolerance" does not.
4. **"Both lever guard rails" was wrong (Codex C-10, LOW).** In the swapped-pairing divergence,
   `aggression` hit the real 5.6 runtime cap; `call_looseness` = 0.155 hit no rail (the model bound
   is only > 0) — it is an extreme fitted value, not a clamp.

Scope statement (Codex C-3, HIGH, accepted): this study refutes the expensive-zig-zag claim **for
tag on the (FtC, AF) pair, near and far targets, context-aware/line-blind posture, with local
Jacobian corroboration for nit**. It does not measure lag, station, maniac, other stat pairs, or
the line-aware posture. Roster-wide statements must cite it with that qualifier.

## Appendix — reproduction

Scripts + trajectory logs preserved at `docs/ai-dlc/reports/n-vecfit-premise-scripts/`
(vecfit_lib.py, one.py, jac.py, lin.py, fit_drivers.py, fit2.py, fit3.py, *.jsonl trajectories,
*_log.txt). Originally scratchpad-only:
`vecfit_lib.py` (harness wrapper: sys.path shim, `model_copy` lever mutation, timing),
`one.py` (one measurement per process), `jac.py` (Jacobian/cond/ρ), `lin.py` (2×2 algebra — the
backend venv has no numpy/scipy), `fit_drivers.py` / `fit2.py` (scalar + Newton arms),
`fit3.py` (Broyden + swapped-pairing arms). Interpreter: `backend/.venv/bin/python`
(as `scripts/verify.sh` uses). No test-suite run, no fixture touched, no git operation.
