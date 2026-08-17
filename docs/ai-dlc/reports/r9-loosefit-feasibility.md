# R9-LOOSEFIT feasibility — can `call_looseness` separate nit from tag inside the frozen bands?

> Pre-spec measurement, 2026-08-03, code pin **`b63dfaa`** (verified `git rev-parse --short HEAD`).
> Answers the two questions `contracts/r9-loosefit.md` leaves open (its §2 D11/BANDS tension).
> **No repo file was changed by this work except this report.** All scripts lived in a scratchpad;
> packs were mutated **in memory only** via `model_copy(update={"call_looseness": …})`.
> **`continue_ref` was NEVER touched** — nit/tag 0.6, lag 0.55 throughout (N-LOGIT frozen anchor, G9).

## VERDICT — **FEASIBLE IN-BAND**

A joint operating point exists at which **all three personas sit inside every HARD band, the HARD
fixed-node ordering gate still passes, and the nit-vs-tag fold-to-c-bet gap opens to 0.297 —
7.3× the paired 3σ noise band.** Today that gap is **−0.012**, i.e. nit and tag are statistically
indistinguishable on the population fold-to-c-bet statistic, *and inverted in sign* relative to the
archetype order. The separation R9-LOOSEFIT wants is available without touching the bands, so the
contract's §2 tension **resolves toward option (a): constrain the fit inside the current BANDS.**

Recommended operating point (measured jointly at n = 48,000, all three in band, ordering gate green):

| persona | `call_looseness` now | recommended | AF | FtC | WTSD |
|---|---|---|---|---|---|
| nit | 0.60 | **0.10** | 2.029 (band 0.6–2.4) | 0.5815 (0.10–0.90) | 0.5248 (0.37–0.80) |
| tag | 0.60 | **0.66** | 2.034 (1.4–3.6) | 0.2844 (0.0–0.55) | 0.6055 (0.41–0.65) |
| lag | 0.55 | **0.66** | 2.427 (1.5–4.5) | 0.2984 (0.12–0.64) | 0.5716 (0.37–0.59) |

**The binding constraint is NOT the population bands — it is the fixed-node ordering gate**
(`test_fold_to_bet_persona_ordering_at_fixed_size`, contract §1 bullet 2). The bands admit a 7–8×
range of `call_looseness` for every persona; the ordering gate cuts tag to ~2.5× and lag to ~1.4×.
Any spec written against the bands alone will pick a value that reddens CI.

---

## 1. Setup

| item | value |
|---|---|
| instrument | `_persona_stats(packs, persona, n, context_aware=True)` — `backend/tests/test_personas_postflop.py:2634` |
| posture | `context_aware=True`, **line-blind** — `_persona_stats` has no `line_aware` passthrough (contract §8 / N-vecfit handoff item 4). The harness was **not** modified. Disclosed limitation, not a blessing. |
| levers moved | `call_looseness` only, on nit / tag / lag. `continue_ref`, `aggression`, `stickiness`, `size_elasticity` untouched; station/fish/maniac packs untouched. |
| n | **24,000** for the ladders + cross-contamination (33 calls); **48,000** for the operating point and the off-anchor Jacobians (9 calls) |
| harness calls | **42** (33 × 24k, 9 × 48k) + 2 discarded n=2,000 smoke calls |
| wall / CPU | ≈ 23 min wall at ≤ 3 parallel processes (the ≤3 cap from the premise study was honoured); **60.5 CPU-minutes** |
| s/call | 58–83 s at n=24,000 · 136–149 s at n=48,000 |
| noise floors (3σ, measured per call) | n=48k: FtC ±0.017–0.033, AF ±0.072–0.147, WTSD ±0.009–0.014 · n=24k: FtC ±0.021–0.046, AF ±0.063–0.273, WTSD ±0.012–0.020 (nit's FtC/AF bands are the widest — its c-bet-facing denominator is the smallest, 1,964 at 48k vs tag's 3,516 and lag's 5,741) |
| secondary instrument | a **read-only replica of the `fold_by_size` fixture** (`test_personas_postflop.py:534`) — 1,250 pre-dealt spots × 6 personas × 4 sizes, pure decision sampling, ~1.7 s per config. Reproduces every ordering-gate leg at HEAD before use. **No pytest was run.** 93 configs evaluated (~2.6 min total). Its own sampling noise is 3σ ≈ **0.042** fold-rate points. |

### Committed-node caveat (contract §4)

`_commit_transform` zeroes the FOLD merit on SPR-committed nodes, so `call_looseness` cancels out of
the whole distribution there and the lever is **inert**. Every AF figure below **aggregates over
those committed nodes** — no exclusion is possible without new counters (contract §3: no
general facing-node fold-share/raise-share counter exists). The measured AF sensitivities are
therefore *dilated* toward zero relative to the lever's true reach on nodes it can move. Building
those counters is this slice's own scope, not something this study could work around.

---

## 2. Q1 — in-band windows vs the frozen HARD bands

Ladders swept one persona at a time, the other two at their authored anchors, `context_aware=True`,
n = 24,000. Bands from `BANDS` (`:2569-2577`), asserted by `test_persona_postflop_bands` (`:5640`).

### nit — bands AF (0.6, 2.4) · FtC (0.10, 0.90) · WTSD (0.37, 0.80)

| `cl` | rscale | AF | FtC | WTSD | verdict |
|---|---|---|---|---|---|
| 0.075† | 0.125 | 2.226 | 0.6237 | 0.5096 | in band (AF + 3σ = 2.373 < 2.4) |
| 0.08 | 0.133 | 2.139 | 0.6081 | 0.5082 | in band |
| 0.15 | 0.250 | 1.763 | 0.5406 | 0.5435 | in band |
| 0.30 | 0.500 | 1.416 | 0.4146 | 0.5903 | in band |
| **0.60** | 1.000 | 1.221 | 0.2812 | 0.6480 | in band (authored) |
| 1.05 | 1.750 | 1.132 | 0.2232 | 0.6901 | in band |
| 1.80 | 3.000 | 1.035 | 0.1719 | 0.7200 | in band |
| 3.50 | 5.833 | 0.927 | 0.1010 | 0.7603 | **at the FtC floor** (0.1010 vs 0.10) |

† n = 48,000.

**nit band window ≈ `cl` ∈ [0.060, 3.5]** (3σ-safe [0.072, 2.7]).
Binding: **AF top 2.4** on the tight side (crossing extrapolated at ≈ 0.060 from the measured
∂AF/∂ln cl = −0.808); **FtC floor 0.10** on the loose side (measured at 3.5). WTSD never binds —
nit's 0.37–0.80 band is the widest in the file.

### tag — bands AF (1.4, 3.6) · FtC (0.0, 0.55) · WTSD (0.41, 0.65)

| `cl` | rscale | AF | FtC | WTSD | verdict |
|---|---|---|---|---|---|
| 0.13 | 0.217 | 3.342 | **0.5581** | 0.4758 | **OUT — FtC top** |
| 0.15 | 0.250 | 3.206 | 0.5265 | 0.4901 | in band, within 3σ of the FtC top |
| 0.30 | 0.500 | 2.486 | 0.4173 | 0.5514 | in band |
| **0.60** | 1.000 | 2.223 | 0.2986 | 0.6014 | in band (authored) |
| 0.90 | 1.500 | 1.997 | 0.2328 | 0.6407 | in band, within 3σ of the WTSD top |
| 1.05 | 1.750 | 1.883 | 0.2045 | 0.6488 | in band, within 3σ of the WTSD top |
| 1.80 | 3.000 | 1.734 | 0.1569 | **0.6961** | **OUT — WTSD top** |

**tag band window ≈ `cl` ∈ [0.15, 1.06]** (3σ-safe [0.16, 0.85]).
Binding: **FtC top 0.55** tight side · **WTSD top 0.65** loose side. AF never binds (it stays
1.73–3.34 across a 14× lever range).

### lag — bands AF (1.5, 4.5) · FtC (0.12, 0.64) · WTSD (0.37, 0.59)

| `cl` | rscale | AF | FtC | WTSD | verdict |
|---|---|---|---|---|---|
| 0.09 | 0.164 | 4.393 | 0.6148 | 0.4140 | in band, within 3σ of **both** the AF top and the FtC top |
| 0.1375 | 0.250 | 3.964 | 0.5380 | 0.4401 | in band |
| 0.275 | 0.500 | 2.998 | 0.4337 | 0.4944 | in band |
| **0.55** | 1.000 | 2.525 | 0.3269 | 0.5561 | in band (authored) |
| 0.66 | 1.200 | 2.456 | 0.2904 | 0.5748 | in band (WTSD + 3σ = 0.587 < 0.59) |
| 0.9625 | 1.750 | 2.222 | 0.2264 | **0.6154** | **OUT — WTSD top** |
| 1.65 | 3.000 | 2.046 | 0.1709 | **0.6593** | **OUT — WTSD top** |

**lag band window ≈ `cl` ∈ [≲0.09, 0.76]** (3σ-safe [0.11, 0.68]) — 0.09 is still in band, so the
tight edge was not bracketed; it is below 0.09 and irrelevant, the ordering gate stops at 0.44.
Binding: **AF top 4.5** tight side (FtC top 0.64 arrives ~simultaneously) · **WTSD top 0.59** loose
side — lag's WTSD ceiling is the tightest in the trio, which is why lag *cannot out-loosen tag*.

### The window that actually binds — the fixed-node ordering gate

`test_fold_to_bet_persona_ordering_at_fixed_size` (`:790-826`) is HARD and asserts
`station < {fish, maniac}`, `fish > tag`, `fish − nit < 0.10`, `maniac < lag`, `station < lag`,
`lag < tag`, `tag < nit` on the ½-pot fold rate over a uniform, air-heavy fixture range. Measured on
the replica, the fixture is **separable per persona** — each persona's fold rate depends only on its
own `call_looseness`; station 0.1760, fish 0.4816, maniac 0.2928 are constants for this slice.

| persona | window from BANDS | window from the ORDERING gate (others at anchor) | binding leg |
|---|---|---|---|
| nit | [0.060, 3.5] | **(0, 0.883]** | `fish − nit < 0.10` (stricter than `tag < nit`, 0.924) |
| tag | [0.15, 1.06] | **[0.346, 0.658]** | `fish > tag` tight · `lag < tag` loose |
| lag | [≲0.09, 0.76] | **[0.442, 0.794]** | `lag < tag` tight · `maniac < lag` loose |

**Net usable window = band ∩ ordering:** nit **[0.060, 0.883]** (14.7× wide), tag **[0.346, 0.658]**
(1.9×), lag **[0.442, 0.76]** (1.7×). The ordering gate shrinks tag's usable range from 7.1× to 1.9×
and lag's from ≥8.4× to 1.7×; nit it barely touches.

Two of the ordering legs are *relative*, so the windows widen once the trio moves together. At the
recommended joint point (nit 0.10 → fold 0.7392; lag 0.66 → 0.3200) the gate re-opens to
**tag [0.346, 0.856]** and **lag [0.553, 0.794]**. This coupling is why the fit must be specified as
a *joint* triple, not three independent scalar fits.

### Cross-contamination check (shared-table rng displacement)

At the extreme point of each ladder, the other two personas were re-measured in the same
configuration (12 extra calls, n = 24,000). Deltas are against each observer's own all-anchor value.

| perturbation | observer | ΔAF (3σ) | ΔFtC (3σ) | ΔWTSD (3σ) |
|---|---|---|---|---|
| nit → 0.15 | tag | −0.049 (0.120) | −0.0133 (0.0324) | +0.0050 (0.0150) |
| nit → 0.15 | lag | −0.038 (0.115) | +0.0043 (0.0263) | −0.0003 (0.0124) |
| nit → 1.80 | tag | −0.068 (0.119) | +0.0004 (0.0321) | +0.0012 (0.0150) |
| nit → 1.80 | lag | +0.067 (0.122) | −0.0083 (0.0263) | +0.0089 (0.0124) |
| tag → 0.15 | nit | +0.025 (0.092) | +0.0064 (0.0423) | +0.0006 (0.0189) |
| tag → 0.15 | lag | +0.076 (0.123) | −0.0130 (0.0261) | −0.0095 (0.0125) |
| tag → 1.80 | nit | +0.022 (0.092) | **+0.0392** (0.0459) | +0.0023 (0.0189) |
| tag → 1.80 | lag | +0.001 (0.118) | −0.0081 (0.0261) | +0.0048 (0.0124) |
| lag → 0.1375 | nit | +0.028 (0.093) | +0.0283 (0.0446) | −0.0041 (0.0191) |
| lag → 0.1375 | tag | −0.044 (0.121) | +0.0018 (0.0333) | **−0.0097** (0.0150) |
| lag → 1.65 | nit | −0.022 (0.089) | +0.0269 (0.0437) | +0.0053 (0.0188) |
| lag → 1.65 | tag | −0.014 (0.122) | +0.0042 (0.0328) | **+0.0107** (0.0149) |

**Every one of the 36 deltas sits inside its own 3σ band** — no cross-contamination is resolvable at
n = 24,000, and none comes close to moving a persona across a band edge whose margin is healthy.

**But the caveat that matters:** the largest observed WTSD displacements (±0.010) are *bigger than
the WTSD headroom at the loose band edges* — tag at `cl` 0.90 has only 0.0093 of WTSD margin, lag at
0.66 only 0.0152. A spec that parks tag or lag at its loose WTSD edge can be pushed out of band by
another persona's refit alone. **Keep ≥ 0.02 of WTSD margin at the loose end** (i.e. tag ≤ ~0.80,
lag ≤ ~0.63 if maximum robustness is wanted; the recommended point uses tag 0.66 / lag 0.66, which
leaves 0.045 / 0.018 — lag is the thin one).

---

## 3. Q2 — separation headroom (nit vs tag)

**Direction demanded by the archetypes: nit folds MORE than tag** — the fixed-node gate asserts
`tag < nit` on fold rate, so on the population fold-to-c-bet statistic the target is
**FtC(nit) > FtC(tag)**.

**Today that ordering does not hold.** At the authored anchors (n = 48,000, from the N-vecfit premise
study, same seed / posture / pack fingerprint): nit FtC 0.28579, tag FtC 0.29793 →
**gap = −0.0121**, against a paired 3σ band of ≈ 0.040. The two personas are a statistical tie on
this statistic, *with the sign pointing the wrong way*. This is the strongest quantitative statement
of R9-LOOSEFIT's motivation the measurement produced.

### Achievable gap

Measured **jointly** (both personas moved in the same pack set, lag moved too — the configuration a
spec would actually ship), n = 48,000:

| configuration | FtC nit | FtC tag | gap | in 3σ units |
|---|---|---|---|---|
| authored anchors (reference) | 0.28579 | 0.29793 | **−0.0121** | −0.3 |
| **nit 0.10 / tag 0.66 / lag 0.66** | 0.5815 | 0.2844 | **+0.2971** | **+7.3** |

Paired 3σ = 3·√(σ²_nit + σ²_tag) = **0.0404**.

**Headroom: the gap opens by 0.309 FtC points, and the fitted gap is 7.3× the 3σ band — comfortably
assertable as a HARD gate.** A conservative gate at `FtC(nit) − FtC(tag) > 0.15` sits **3.6 × 3σ
below** the measured value and **3.7 × 3σ above** zero, i.e. it has symmetric protection against
both a false pass and a flaky fail.

The reverse direction (nit loose / tag tight) is measurable too and larger in magnitude — from the
ladders at n = 24,000, nit at 1.05 (FtC 0.2232) vs tag at 0.15 (FtC 0.5265) gives −0.303 — but it is
**not available**: that configuration fails three legs of the ordering gate (`fish > tag`,
`fish − nit < 0.10`, `tag < nit`), and tag at 0.15 sits within 3σ of its FtC band top. It is recorded
only to confirm the lever is not sign-constrained.

### What the recommended point costs elsewhere

- **lag ends up folding marginally more than tag** in the population aggregate (0.2984 vs 0.2844,
  Δ = +0.014 against a paired 3σ of 0.029 — a statistical tie, not a resolvable inversion). lag
  *cannot* be pushed looser than tag because lag's WTSD ceiling (0.59) is tighter than tag's (0.65).
  **A "lag defends widest" claim is NOT reachable through `call_looseness` alone under the frozen
  bands** — that is a finding for the spec, and an argument for the W4-b re-anchor to widen lag's
  WTSD band rather than for R9-LOOSEFIT to fight it.
- The fixed-node gate stays green at the recommended point with these margins (fixture 3σ ≈ 0.042):
  nit 0.7392 · fish 0.4816 · tag 0.3488 · lag 0.3200 · maniac 0.2928 · station 0.1760. The two thin
  legs are `lag < tag` (margin 0.029, ~2.1 fixture-σ) and `maniac < lag` (margin 0.027, ~1.9σ). A
  slightly more robust variant — **nit 0.08 / tag 0.63 / lag 0.62** — also passes every leg with
  `lag < tag` margin 0.030 and `maniac < lag` margin 0.037. **That variant was checked on the
  ordering replica only** — its band stats are interpolated between measured ladder points (all
  in band), not measured jointly on the simulator. Measure it before adopting it.
- `_GOLDEN_STATS_N200` will need the sanctioned re-pin (contract §1; W3R-2 precedent) — every row
  moves, because the sim is shared-table.

---

## 4. Q3 — off-anchor Jacobian vs the anchor Jacobian

Central differences at ±25% in `call_looseness` (Δln = 0.5108), n = 48,000, `context_aware=True`,
other personas held at their anchors (matching the premise study's protocol so the numbers are
comparable). Anchor values quoted from `reports/n-vecfit-premise.md` §2.

| persona | point | rscale | ∂FtC/∂ln cl (±1σ) | anchor value | ∂AF/∂ln cl (±1σ) | anchor value |
|---|---|---|---|---|---|---|
| nit | 0.10 | 0.167 | **−0.1520** ± 0.0347 (t = 4.4) | −0.16192 | **−0.8082** ± 0.1396 (t = 5.8) | −0.17946 |
| tag | 0.66 | 1.100 | **−0.1519** ± 0.0242 (t = 6.3) | −0.14204 | **−0.4797** ± 0.0868 (t = 5.5) | −0.46284 |
| lag | 0.66 | 1.200 | **−0.1929** ± 0.0190 (t = 10.1) | (none measured) | **−0.6394** ± 0.0845 (t = 7.6) | (none measured) |

**Answer: the FtC row does not bend; the AF row bends hard.**

- **∂FtC/∂ln cl is essentially constant** across the whole feasible range: −0.15 to −0.19 at every
  point measured, on every persona, from rscale 0.13 to 5.8 (ladder secants agree). Every off-anchor
  value is within ~1σ of its anchor value. **Rule 1a's `call_looseness`→FtC pairing and its step
  sizes transfer safely into the fit region** — a fitter can seed FtC steps from the anchor slope.
- **∂AF/∂ln cl is 4.5× larger in magnitude for nit at rscale 0.167 than at rscale 1.0**
  (−0.808 vs −0.179). Ladder secants show the same asymmetry on tag (−1.04 at rscale 0.5 vs −0.38
  near anchor) and lag (−1.39 at rscale 0.5 vs −0.38 at rscale 1.2). **Contract §8's warning is
  confirmed: rscale de-inertization materially bends the response, and it bends the AF row
  specifically.** Any AF-targeted step computed from an anchor-point slope will under-predict the
  far-field gain by a factor of ~2–4.5 below the anchor — exactly the failure mode Rule 2 exists to
  prevent. Fresh secants are mandatory on the AF row; they are optional on the FtC row.
- Practically: since `call_looseness` is paired to **FtC** (Rule 1a) and FtC's slope is flat, the fit
  itself is well behaved. The bend shows up as *collateral* AF motion, which is what the band check
  has to catch.

---

## 5. Q4 — raise-side activation (disclosure, not a gate)

N-LOGIT scales the RAISE leg by `rscale = call_looseness / continue_ref` at fold-legal facing nodes.
Below the anchor (rscale < 1) RAISE is scaled **down**, so the naive expectation is that AF falls.

**Observed: AF rises at every ladder point below the anchor, on all three personas. 100 % of the
below-anchor points move AF opposite to the naive raise-side reading.** AF is strictly decreasing in
`call_looseness` over the entire measured range for nit (2.23 → 0.93 across cl 0.075 → 3.5), tag
(3.34 → 1.73 across 0.13 → 1.8) and lag (4.39 → 2.05 across 0.09 → 1.65). No sign reversal, anywhere.

The mechanism is a denominator effect that swamps the raise leg: `looseness` scales the flat CALL
merit at **every** postflop node (`personas_postflop.py:881`), whereas `rscale` re-weights **only**
the RAISE leg and **only** where FOLD is legal (`:1239-1248`), and is inert entirely on SPR-committed
nodes (§4). AF = (BET + RAISE)/CALL, and BET is never rescaled, so the collapsing CALL denominator
dominates.

**The rscale coupling is nevertheless visible — as an asymmetry about rscale = 1, not as a sign
flip.** Because d(rscale)/d(ln cl) = rscale, the raise-side term (which *opposes* the denominator
effect) is proportional to rscale itself: weak below the anchor, strong above it. So |∂AF/∂ln cl|
should be large below the anchor and small above — which is exactly the measured pattern:

| persona | \|∂AF/∂ln cl\| at rscale ≈ 0.5 | at/above rscale 1.0 | ratio |
|---|---|---|---|
| nit | 0.50 (0.50) / **0.81** (0.167) | 0.28 (1.0) → 0.16–0.18 (1.75–5.8) | 2.8–4.5× |
| tag | 1.04 (0.50) | 0.38 (1.0) → 0.28 (3.0) | 2.7× |
| lag | 1.39 (0.50) | 0.68 (1.0) → 0.33 (3.0) | 2.0–4.2× |

This is **consistent with** the rscale mechanism but not a clean isolation of it — the counterfactual
(`continue_ref` re-synced to `call_looseness`, killing rscale) is forbidden by design and was not
measured. Recorded as disclosure material.

---

## 6. Disclosed limitations

1. **Line-blind.** `_persona_stats` forwards only `context_aware`; `line_aware` is unreachable from
   it and defaults `False` (contract §8, N-vecfit handoff item 4). The harness was **not** modified.
   Every number here is context-aware / line-blind. Nothing establishes that these windows are
   invariant to line-awareness; W4-b-grade work needs the passthrough first.
2. **AF aggregates over SPR-committed nodes**, where the lever is provably inert (§1 above,
   contract §4). No exclusion is possible without the new facing-node counters that contract §3 says
   this slice must build.
3. **Ordering-gate numbers come from a replica**, not from pytest (the brief forbids test runs). The
   replica reproduces every leg's pass/fail at HEAD before use, but its fold rates differ by ≲ 0.01
   from the values quoted in the test's own docstring (those were recorded at W3R-2, several
   mechanics ago). Treat the *windows* as accurate to ~±0.02 in `call_looseness`; re-confirm the
   chosen point with a real pytest run before shipping.
4. **Window edges are interpolated**, not bracketed to convergence — measured ladder points bracket
   every edge, and log-linear interpolation supplies the crossing. Edges are quoted to 2 significant
   figures for that reason.
5. **Only `call_looseness` moved.** `aggression` is untouched, so the AF motion reported here is the
   *uncompensated* collateral effect. A joint (cl, agg) fit could hold AF fixed and would widen the
   windows further; that is a spec choice, not something this study measured.
6. **No `_GOLDEN_STATS_N200` re-pin was computed** — it is a mechanical re-record once the values are
   chosen (precedent: W3R-2, contract §1).

## 7. Handoff to the R9-LOOSEFIT spec

1. **Fit inside the current bands** (contract §2 option a). The solution space is not tight; it is
   comfortable. No band re-anchor is needed before W4-b.
2. **Specify the triple jointly, and gate on the ordering test, not just the bands.** Two of the
   three windows are set by relative fold-rate legs that move when the other personas move.
3. **Recommended point: nit 0.10 · tag 0.66 · lag 0.66** (measured in band jointly at n = 48,000);
   robustness variant **nit 0.08 · tag 0.63 · lag 0.62** if the thin `lag < tag` / `maniac < lag`
   margins (0.029 / 0.027 fold-rate points, ~2 fixture-σ) are judged too close.
4. **Proposed separation gate:** `FtC(nit) − FtC(tag) > 0.15` at the harness's band N — measured
   +0.297, i.e. 3.6 × 3σ of headroom above the gate, and the gate itself 3.7 × 3σ above zero.
5. **Do not promise "lag defends widest."** lag's WTSD ceiling (0.59) is tighter than tag's (0.65)
   and prevents it; raise it at W4-b or drop the claim.
6. **Keep ≥ 0.02 WTSD margin at the loose end** for tag and lag — cross-persona rng displacement was
   measured at up to ±0.011 WTSD, larger than the margin available at the loose band edges.
7. **Use fresh secants for anything AF-targeted** (Rule 2); the FtC row's slope is flat enough
   (−0.15 to −0.19 everywhere) that the anchor value can seed the FtC steps.
