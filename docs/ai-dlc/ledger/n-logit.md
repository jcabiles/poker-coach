# `N-logit` — finding ledger (spec-stage dual review)

**Slice:** `N-logit` — nested logit on the facing node.
**Stage:** SPEC review (Gate 2 not yet reached). **No production file has been edited.**
**Spec under review:** `docs/ai-dlc/specs/n-logit.md` rev 1 (the version reviewed; now **VOID** — see R-1).
**Reviewers:** `refuter` (Opus, fresh context) + Codex Sol (`gpt-5.6-sol`, effort `high`), run in parallel on
the same spec + contract map. Tiering per the owner's complexity ruling (spine work ⇒ Opus + Sol).
**Both returned FAIL.** They converged independently on the same HIGH.

---

## R-1 — HIGH — the re-parameterisation cancels: the spec's mechanism is a measured no-op
**Raised by:** refuter (HIGH, claim a+g) **and** Codex Sol (HIGH, claim a+g), independently.
**Status: ACCEPTED IN FULL. Spec rev 1 §3 is void.**

**The claim that failed.** Spec §3.1 asserted that setting `C' = C₀`, `R' = R₀/L` and multiplying the defend
pair by `L` makes `P(raise | continue)` independent of `L`. It does not. `R'` is *itself* a function of `L`,
so the factor cancels:

```
   P(raise | continue) = R'/(C'+R') = (R₀/L)/(C₀ + R₀/L) = R₀/(C₀·L + R₀)
```

— which is **exactly HEAD's** expression. The six deltas compose to an exact algebraic identity **in `L`**,
not merely at the authored lever values. The slice therefore reproduces HEAD for *every* `L`, delivers zero
lever semantics, and costs a 1-ulp non-bit-exact fixture risk for no behavioural gain.

**Why the cited prior art does not carry over** (refuter, and correct): `r9-defence-design.md:249-266` is
raise-neutral because its factor `exp(−λ_p·g(line))` is **exogenous** to the merits. Here the factor *is* the
lever that also defines the raise leg. The Director imported the algebraic shape without importing the
exogeneity condition that makes it work.

**Independent verification (Director, required before accepting any reviewer finding).** Patched module vs
HEAD, halving each pack's effective looseness, TOP_PAIR turn HU, raise-share delta:

| persona | HEAD | spec rev-1 design |
|---|---|---|
| lag | +0.1715 | +0.1715 |
| tag | +0.1673 | +0.1673 |
| maniac | +0.1568 | +0.1568 |
| nit | +0.0904 | +0.0904 |
| passive_fish | +0.1133 | +0.1133 |
| calling_station | +0.0153 | +0.0153 |

Bit-identical. **Three independent measurements agree.** Accepted without reservation.

**Consequence for gates:** G1 (orthogonality) and G2 (routing) are RED at HEAD *and* RED after the fix —
they are unachievable by this mechanism, not merely unmet.

**Director's own error, recorded for the initiative's benefit:** the 5,040-cell identity sweep in spec §4 was
real and correctly executed, but it measured the wrong thing. It proved *"the change alters nothing"*, which
was then read as *"the change preserves behaviour"*. Those are different claims, and only the second is
compatible with the slice having a purpose. **Lesson for successor specs: any re-parameterisation must be
gated on a SENSITIVITY measurement (does the response to the lever change?), never on an identity
measurement alone.** An identity sweep can never distinguish a behaviour-preserving fix from a no-op.

### R-1a — refuter's remedy (iii) also fails, for a reason neither reviewer identified
**Raised by:** Director. **Status: ACCEPTED (kills one of the three offered remedies).**

Both reviewers offered "re-author `aggression := aggression / L` in the packs" as a viable remedy.
**It is not behaviour-preserving:** `agg_scale` is shared between the facing branch (`:893-896`) **and the
unopened/betting branch** (`:920-922`). Dividing the authored value would change every persona's c-bet /
lead / barrel frequency at the betting node. Any compensating factor must therefore be **facing-node-scoped**,
which a pack-level `aggression` edit structurally cannot be.

This is on top of the cap collision already recorded in `contracts/n-logit.md` C4 (lag → 5.8182,
maniac → 10.1818, both over `_AGGRESSION_CAP = 5.6`).

---

## R-2 — MED — "no guard needed" is false; the division is not universally safe
**Raised by:** Codex Sol (MED, claim e). **Status: ACCEPTED.**

Spec §3.3 argued that dividing by `looseness` needs no guard because both fields are `Field(gt=0.0)` and
`_stickiness_authorship` guarantees the fallback is populated — and further, that a guard would be *dead
code*. The narrow claim (validated shipped packs are safe) holds. The **stronger claim is false**, proven by
Codex with an executed probe:

- Tests routinely build **unvalidated** postflop objects via `model_copy(update=...)` —
  `tests/test_personas_postflop.py:227` and `:5790`. A probe produced effective looseness `0.0` this way;
  the proposed division would raise `ZeroDivisionError`.
- Pydantic `gt=0.0` **accepts `inf`** and positive subnormals (`5e-324`). `(R₀/L)·L` can then evaluate to
  `0·inf = NaN` or overflow.
- Consequently **G7 as worded is not a pin at all** — inspecting the six shipped values would still pass if
  the schema constraint were deleted or an infinity were authored.

**Adjudication:** accepted on both points. Note the finding is *design-conditional* — a successor design that
removes the live division moots the `ZeroDivisionError` path — but the **G7 wording is independently wrong**
and must not be carried forward verbatim. Any successor gate must assert the *model rejects* `0`, `None`,
`NaN`, `inf` and unsafe extremes, not merely that today's packs happen to be fine.

---

## R-3 — MED — the gate set cannot distinguish "delivered" from "did nothing"
**Raised by:** refuter (MED, claim g) and Codex Sol (MED, claim g), overlapping. **Status: ACCEPTED.**

Eight of the ten criteria (G3–G10) are passed by a **literal empty diff**. Only G1/G2 were behavioural, and
per R-1 those are unachievable. By the spec's own rule — *"a criterion that already passes proves nothing"* —
G5 and G7 were regression pins mislabelled as HARD gates.

Codex added four specific coverage holes, all accepted and all carried to the successor spec:
1. **WEAK draws omitted** from the §4 grid, although B5b modifies both draw categories
   (`personas_postflop.py:977`, `:986`). The existing weak-draw test (`test_personas_postflop.py:1302`)
   asserts only a directional call ordering, so a weak-draw arithmetic error could evade the identity gate.
2. **The FOLD+CALL-without-RAISE legal shape is unpinned**, permitting an implementation that applies the
   aggregate factor only when RAISE exists.
3. **G1 tested a single perturbation (`L/2`)** — persona-specific anchoring could satisfy it without
   establishing general lever independence. Multiple lever values required.
4. **G5 is not universal** — facing nodes may legally omit RAISE, and the estimator's zero-total path returns
   a singleton (`range_estimate.py:364`).

**Fold-in:** the successor grid must add WEAK draws and both legal shapes; the orthogonality gate must sweep
several lever values; G5 must be conditioned on the node's legal set.

---

## R-4 — MED — the `stickiness` authorship comment would become false
**Raised by:** refuter (MED, unlisted). **Status: ACCEPTED-CONDITIONAL.**

`content/models.py:171-176` states `stickiness` is "read only where a split lever is unset (call merit when
`call_looseness` is None; the price exponent when `size_elasticity` is None)". Under spec rev 1 it would also
govern the **raise-leg** magnitude for maniac. Spec §5 listed `content/models.py` as NOT-touchable, so the
now-false comment could not be corrected inside the slice.

**Adjudication:** accepted, and it bites only for a design that keeps the live lever in the raise leg. The
successor design (frozen reference) does not — but if any variant does, `content/models.py` moves onto the
touchable list and the comment + docstring are corrected in the same commit.

---

## R-5 — LOW — the working tree is behind the spec's declared base
**Raised by:** refuter (LOW, process). **Status: ACCEPTED.**

Shared tree is at `61efc42`; `origin/main` is `c12f773` (3 commits ahead). `content/personas/lag.json`
differs (1.4.0 vs 1.5.0, N-LAGWIDTH). A build from this tree would fail G6 for a reason unrelated to the
slice.

**Mitigating fact, verified by both the refuter and the Director:** `git diff 61efc42 c12f773 --
backend/app/domain/` is **empty**, and lag.json's *postflop* block is unchanged, so the §4 grid measurements
remain valid. **Action:** build from a worktree off `origin/main` `c12f773`; state the measurement tree
explicitly in any successor spec.

---

## Clean bills — load-bearing claims that survived BOTH reviewers
Recorded because they are **reusable by the successor design**, which keeps the same merit plumbing and the
same attach point:

- **(b) The six deltas are complete and correctly placed.** No double-scaled or unscaled term. The
  `bluff_cell` river `call_merit = 0.0` floor (`:874-875`), `_RIVER_RAISE_FLOOR` (`:897-898`),
  `_ACE_HIGH_FLOAT_RAISE_DAMP` (`:866-872`, inside the call leg), `_ONE_PAIR_RAISE_DAMP` (`:887-892`, inside
  the raise leg), and `_MW_CATCH_TIGHTEN` on FOLD (`:855-856`, correctly excluded) all check out. Refuter
  swept 9,216 facing cells, worst deviation 2.22e-16, zero modal flips.
- **(c) The B5b restatement is exact and clamp-safe.** `L[(A+B) − B·d] = L(A+B) − L·B·d`; because the factor
  is applied before `:999` and is strictly positive, `sign(L·m) = sign(m)`, so no merit crosses the
  `max(m, 0.0)` clamp in either direction.
- **(d) The attach point is right.** `_commit_transform` commutes with the multiply pass (FOLD → literal
  `0.0`, unmultiplied; RAISE ×3 then ×L reproduces HEAD's `3·R₀`), and the `total <= 0.0` fallback
  (`:1001-1003`) is reachable on exactly the same cells.
- **(f) Scope is respected.** The unopened/betting branch is untouched: refuter measured 1,152 unopened
  cells, worst absolute difference **exactly 0.0**.
- **§3.2's line references are current** — all six verified by both reviewers at this checkout.

The refuter put it exactly right: claims (b)–(f) hold *because* the transformation is a perfect identity —
and that same perfection is what makes the goal unreachable.

---

## Successor design — verified before being offered to the owner

The requirement is now stated precisely. Writing final merits `(F, C_f, R_f)`, we need **both**:

1. **Identity at authored values:** at `L = L₀`, `(F, C_f, R_f) = (F, C₀·L₀, R₀)`.
2. **Orthogonality:** `∂/∂L [ R_f/(C_f+R_f) ] = 0`.

Both hold **iff** `C_f = C₀·L` and `R_f = R₀·L/L₀` with **`L₀` a frozen reference that does not move when the
lever is tuned**. Both reviewers reached this independently; it is the unique solution shape.

`L₀` cannot be a code constant (persona-differentiating numbers belong in the pack — S4 split), and it cannot
be obtained by re-authoring `aggression` (R-1a: that lever is shared with the betting node). It must be a
**new authored pack number**.

**Director verification (2026-08-02), grid extended per R-3 to include WEAK draws, both legal-shape variants
and `facing_raise` ∈ {False, True}:**

| persona | identity vs HEAD (worst abs dev) | raise-share drift when `L` halves — HEAD | — successor design |
|---|---|---|---|
| calling_station | 0.000e+00 | 0.171563 | **6.94e-18** |
| lag | 1.110e-16 | 0.171554 | **1.11e-16** |
| maniac | 1.110e-16 | 0.171537 | **1.11e-16** |
| nit | 1.110e-16 | 0.171540 | **5.55e-17** |
| passive_fish | 1.110e-16 | 0.169145 | **1.11e-16** |
| tag | 1.110e-16 | 0.171567 | **1.11e-16** |

Both properties hold simultaneously. This is the measurement spec rev 1 should have carried and did not.

**Owner decision required** before a rev-2 spec is written — see the session's decision prompt. Probes:
`/tmp/claude-501/probe_optA.py`, `probe_check.py` (scratchpad, outside the repo by initiative convention).

---

# ROUND 2 — delta re-review of spec rev 2

Both reviewers re-run on rev 2. **Both returned FAIL again — but both certified the central mechanism.**
Codex: *"The central redesign is sound … I found no HIGH defect in its core algebra."* Refuter: *"Rev 1's HIGH
is fixed for real."* Every rev-2 finding is about the spec's **packaging** — gates, bounds, touch-list,
disclosure — not its algebra.

**Independent verification of the central claim (neither reviewer trusted spec §4's table):**

| reviewer | grid | identity at authored values | `P(raise\|continue)` drift over ×0.25…×4 |
|---|---|---|---|
| refuter | 8,064 cells × 6 personas × 4 multipliers | worst 2.22e-16 | HEAD 0.152–0.333 → **rev 2 ≤ 2.22e-16** |
| Codex Sol | ×0.25/×0.5/×1/×2/×4, all six | top-pair exact for all six | HEAD 0.0563–0.5932 → **rev 2 ≤ 1.11e-16** |

The refuter additionally measured **AF / fold-to-c-bet / WTSD identical** (not merely in-band) at N=200 for
all six personas, and **48,384 cells with 0 bitwise mismatches** on the `continue_ref is None` path.

## R2-1 — HIGH — the rev-2 deltas break 6 of 23 frozen exact-equality vectors, and no gate sees it
**Raised by:** refuter. **Status: ACCEPTED — and its remedy adopted wholesale as rev 3.**

`tests/test_price_tail.py:289` (`HEAD_VECTORS`) asserts `got == expected` — **exact equality, not approx**.
Rev 2's divide-then-multiply leaves a 1-ulp residue, and for `passive_fish` (`ref = 0.42`)
`(R/0.42)*0.42 != R`, breaking **6 of 23** vectors. `test_price_tail.py` was **not on rev 2's §5 touch list**,
and G10 was scoped to "seeded fixtures" — a frozen literal in a test module is neither. **A builder following
rev 2 literally lands a red suite or an unauthorised file edit.**

Measured: base `2 failed, 1354 passed`; rev-2 patched `3 failed, 1353 passed`, the new failure being
`test_alpha_ceiling_sub_anchor_vectors_are_byte_identical`
(`0.02899645366051761` vs `0.028996453660517608`).

**Adopted remedy — a single raise-side scale.** Replace all six deltas with:
`rscale = looseness / continue_ref`, applied to the **RAISE entry only**, immediately before normalization,
when `FOLD in by_kind`. The CALL leg keeps HEAD's exact `* looseness`.

Consequences, all verified by the Director before adoption:
- At `L == ref` the scale is **exactly `1.0`** (float division of equal values), so the opted-in path is
  **BIT-EXACT**, not exact-to-1-ulp. Director measurement: **0 bitwise differences** across the full grid for
  all six personas.
- Orthogonality is retained: drift ≤ 2.2e-16 at ×0.25, ×0.5, ×2, ×4 (Director), matching the refuter's own.
- Deltas 1/2/4/5 and the CALL half of delta 6 **vanish**. The B5b "restate in pre-aggregate units" argument
  and its clamp-safety proof burden become **moot** — those merits are never touched.
- R2-8 (modal-action ties at 1 ulp) is closed outright.

## R2-2 — MED — G2 is unachievable by a *correct* implementation
**Raised by:** refuter and Codex Sol independently. **Status: ACCEPTED.**

G2 demanded `ΔP(raise) ≤ 1e-12` **and** `ΔP(fold) > 0` across a bidirectional sweep. Rev 2 deliberately moves
`P(raise)` in **absolute** terms — only the *conditional* is invariant — and above ×1 both signs invert.
Measured (calling_station, patched): ×2 `ΔP(raise)` max `+0.01880`; ×4 max `+0.05430`; `ΔP(fold) < 0` on
**2064/2064** raise-legal cells at both. Codex reproduced the same on lag TOP_PAIR.

Codex also found **undefined cells**: river-air FOLD+CALL nodes have CALL floored to zero and no RAISE, so G1
computes `0/(0+0)` and G2 cannot strictly increase an already-deterministic `P(fold) = 1`.

**This is the same genre of error that killed rev 1 — a gate stated on the wrong quantity — occurring in the
very section designated as the anti-no-op defence.** Fold: state G2 per-direction and per-leg, require strict
movement only on interior cells, and condition G1 on `P(call)+P(raise) > 0`.

## R2-3 — MED — an undisclosed behavioural coupling on the river polar-bluff cell
**Raised by:** refuter. **Status: ACCEPTED (disclose + gate, not exclude).**

On the river polar-bluff cell `call_merit` is hard-zeroed (`:874-875`), so **at HEAD the bluff-raise frequency
is exactly independent of `call_looseness`**. Under the scale it is not. Measured: lag RIVER/AIR
`P(raise)` HEAD flat at `0.271272` across ×1/×0.5/×0.25/×2 → scaled `0.271272 / 0.156920 / 0.085140 /
0.426772` (a 5× swing). tag likewise `0.179906` flat → `0.179906 / 0.098845 / 0.051992 / 0.304950`.
G1 is vacuous there (`CALL = 0` ⇒ ratio ≡ 1) and G3 passes (identity at authored values), so **nothing in rev
2's gate set sees it**. Survives the rev-3 reformulation unchanged.

**Adjudication — disclose, do not exclude.** On that cell the only way to continue *is* to raise, so scaling
the continue candidate by the continue lever is the mechanism behaving correctly on a degenerate node, not a
leak. But it does put `call_looseness` on a magnitude §3.5 assigns to `bluff_freq`, which is a **lever-overlap
question for the theory reviewer**, not something to settle silently. Rev 3 discloses it in §3.5 and adds a
gate pinning the bluff-cell response. **Flagged for `persona-realism-theory-reviewer` at build fan-in.**

## R2-4 — MED — the declared base was NOT green ⚠️
**Raised by:** refuter. **Status: ACCEPTED — Director error, independently reproduced, now escalated.**

Rev 2 §1 declared `c12f773` "verified GREEN, exit 0". **False.** Two tests fail in a pristine checkout.

**Root cause of the Director's false claim:** the verification run piped `pytest` into `tail`, so the observed
exit code was **`tail`'s**, not pytest's — a pipeline returns the last command's status. The output was then
never read. This is precisely the hazard the repo's own git rules document ("never pipe a command whose
success matters"), applied to pytest rather than git. **Standing correction: never assert a suite is green
from a piped exit code.**

Director re-run, unpiped, `backend/.venv/bin/python`: `2 failed, 1354 passed, 1 skipped`.

Director bisect across the merge chain — **not caused by this slice, and not pre-existing either**:

| commit | PR | result |
|---|---|---|
| `61efc42` | #158 (docs) | 🔴 |
| `8729e14` | #159 (fixture restore) | 🟢 |
| `81a5b24` | #160 (N-LAGWIDTH) | 🔴 **re-broken** |
| `c12f773` | #161 (analytics) | 🔴 |

- `test_limper_coverage_belt.py::test_limper_coverage_fires_on_organic_play` — UTG2 faces-1 fire count
  **84 vs pinned 91**.
- `test_personas_postflop.py::test_persona_stats_byte_identical_after_log_refactor` — calling_station AF
  **0.3277777777777778 vs golden 0.32409972299168976**.

Both are pinned goldens invalidated by a real behaviour change that was never re-recorded — the fourth
occurrence of the lost-re-record pattern. **Escalated to the owner as a separate `chore/` PR before N-logit,
per the #159 precedent.** Verify-by #1 is restated as "no NEW failures vs the recorded base set".

## R2-5 — MED — the bound guards the harmless end
**Raised by:** Codex Sol and refuter independently. **Status: ACCEPTED.**

`gt=0.0, le=8.0` rejects `0`/`NaN`/`inf` but **accepts `5e-324`**. Then the divided raise merit becomes `inf`
and the emitted vector is `[0.0, 0.0, nan]`; `random.choices` raises *"Total of weights must be finite"*. At
`1e-8` it validates and yields a degenerate `P(raise) ≈ 0.99999997`. Separately, `model_copy(update=…)`
bypasses validation for `continue_ref` **exactly as ledger R-2 proved it does for `looseness`** — so rev 2's
claim that R-2 was "closed" is wrong: the hazard was **relocated, not removed**. (Also noted: `bool True`
coerces to `1.0`.)

**Fold:** a real lower bound (`ge=0.05`), a runtime guard at the division site because model validation cannot
protect `model_copy`, and G7 extended to the subnormal and unvalidated-copy cases. Also settle whether an
explicit JSON `null` is forbidden while field *absence* remains the legacy opt-out.

## R2-6 — MED — "frozen" is true by design but not enforced by a discriminating gate
**Raised by:** Codex Sol. **Status: ACCEPTED.**

Neither the loader (`personas.py:40`) nor the service cache (`sim_session.py:168`) re-derives the reference —
verified. But G8's wording ("a later refit *updates this pin*") is **ambiguous enough to invite updating
`continue_ref` alongside `call_looseness`, which would recreate rev 1's cancellation across authored
revisions**. A validator that synchronised the fields would also pass shipped-value G8 *and* a G1 implemented
via `model_copy`, because validation would not re-run during the sweep.

**Fold:** add a validated-JSON lifecycle test that changes **only** `call_looseness` and proves `continue_ref`
is unchanged; state explicitly that a looseness fit **never** updates the reference — only an explicit
raise-calibration change may.

## R2-7 — MED/LOW — remaining gate-coverage and accounting defects
**Raised by:** Codex Sol (coverage), refuter (accounting). **Status: ACCEPTED.**

- **Coverage holes:** the §4 grid omits `PostflopContext` busted-draw river state, although the river
  story-bluff contribution (`:812`) feeds the facing bluff-raise leg; the claimed legal-shape factor is not in
  the dimension list; §7 claims G3 proves the unopened branch untouched while G3 names only facing shapes.
  Fold: add busted-straight/flush river contexts, and an opted-in exact-identity sweep for CHECK+BET and
  CHECK+RAISE.
- **Anti-no-op accounting is wrong.** `content/models.py` has no `model_config`, so pydantic's default
  `extra='ignore'` applies and `PersonaPostflop(..., continue_ref=0)` is silently accepted at HEAD — meaning
  G7 and G8 *also* fail on an empty diff. The error is in the favourable direction, but it is **a false gate
  claim in the very section that exists because rev 1 made a false gate claim.** Correct count:
  **G1, G2, G7, G8** are the anti-no-op set, with G1 decisive.

## R2-8 — LOW — G3's modal-action clause is unsatisfiable at 1-ulp precision
**Raised by:** refuter. **Status: ACCEPTED — moot under rev 3.**
`nit` has 16 grid cells where HEAD emits CALL `0.4999999999999999` / RAISE `0.5` and rev 2 emits `0.5 / 0.5` —
an exact tie, so argmax flips on a 1.11e-16 deviation. Closed outright by rev 3's bit-exactness.

## R2-9 — LOW — ledger R-4's recorded *reason* was wrong
**Raised by:** refuter. **Status: ACCEPTED — corrected below.**
R-4 was adjudicated with the reason "the successor design does not keep the live lever in the raise leg".
**That is false**: the scale multiplies the RAISE entry by `looseness / continue_ref` — the live lever is
still there, so for maniac (whose looseness *is* `stickiness`) the `content/models.py:171-176` comment becomes
false under rev 3 exactly as under rev 1. The *outcome* was right (§5 schedules the comment fix); the
reasoning was not. **R-4's reason is hereby corrected to: "accepted and folded into §5's touch list."** The
ledger is the audit trail a successor will trust, so a right answer for a wrong reason is a defect.

## R2-10 — LOW — maniac's anchor is pinned to a *shared* fallback
**Raised by:** refuter. **Status: ACCEPTED.**
Maniac's `0.55` comes from `stickiness`, which is **also** the `_price_exponent` fallback (`:627-644`). Two
undocumented consequences: (a) a future slice editing maniac's `stickiness` for price-elasticity reasons
silently desynchronises anchor from lever and moves maniac's fold/continue split with no call-lever edit;
(b) maniac's effective looseness cannot be swept in isolation, so its G1/G2 measurement is confounded by a
simultaneous fold-merit move. Evidence: on the RIVER/AIR cell where `call_merit` is literally `0.0`, HEAD's
maniac `P(raise)` still moves `0.404853 → 0.430852` under ×0.5 — the fold merit moved — while lag and tag stay
exactly flat. **Fold:** sweep maniac by authoring `call_looseness` on the probe copy; document the coupling in
§3.2 and in G8's disclosure clause.

---

## Round-2 outcome

**Adopted:** the refuter's single-raise-scale reformulation (R2-1), Director-verified bit-exact with
orthogonality retained. All ten findings folded into **spec rev 3**. Two items escalated out of the slice:
the **red base** (R2-4 → separate `chore/` PR) and the **river bluff-cell lever overlap** (R2-3 → flagged for
the theory reviewer at build fan-in).

**Process note worth keeping.** Rev 1 was a no-op; rev 2 was correct in mechanism but shipped a gate a correct
build could not pass, a bound guarding the wrong end, a touch-list that missed a real collateral break, and a
false green-base claim. Neither round's defects would have been caught by the maker. Both rounds were caught
by having **two** independent reviewers from different model families, each of which found things the other
missed — the refuter found the frozen-vector break and the reformulation; Codex found the subnormal, the
lifecycle-gate ambiguity and the contract-map staleness.

---

# BUILD STAGE (spec rev 3) — 2026-08-02

**Branch:** `feat/persona-realism-n-logit`, worktree off `origin/main` = `3bac7d2`.
**Base verified by the Director, UNPIPED, before branching:** `1356 passed, 1 skipped`, pytest exit `0`
(228s). T0's `chore/` PR landed as **#162**, so R2-4's red base is closed and G11's recorded base set is
**empty**. The base check was run as `pytest -q > file 2>&1; echo EXIT=$?` — never through a pipe, per R2-4.

## B-1 — RED-FIRST evidence for G1/G2, measured on this branch

The anti-no-op demonstration the spec requires (§6, "a schema-and-content-only change would pass G8/G9 but
fail G1"). Measured with **T2 landed and T3 not** — i.e. the six packs author `continue_ref`, the model
validates it, and the engine ignores it. That is exactly the "did nothing" build the gate must catch:

| gate | result on the pack-only build |
|---|---|
| **G1** worst \|Δ P(raise \| continue)\| over ×0.25/×0.5/×2/×4 | nit **0.332927** · tag **0.333327** · lag **0.333318** · maniac **0.333332** · calling_station **0.293076** · passive_fish **0.333303** — gate is ≤ 1e-12 |
| **G2** routing sign | **15,624 violations** across 41,472 interior (cell, multiplier) pairs. Representative: nit, two_pair/flop, price 2.0, ×0.25 — `ΔP(fold) = +0.0217` while `ΔP(raise) = +0.2974`. The calling lever went DOWN and the raise rate went UP by 14× the fold rate's move: R10-4, measured. |
| G3, G5, G6, G7, G8-model, G9-lifecycle, grid coverage | **green on the pack-only build** — as designed. They are identity and structure gates; only G1/G2 discriminate. |

After T3 (the two-line scale + the runtime guard) all 24 N-logit gates pass.

## B-2 — how G3 gets a base comparison without a golden file

G3 compares the opted-in pack against the **same pack with `continue_ref` set to `None`**, bitwise, over the
whole 1,728-cell grid. That is a real base comparison rather than a convenience: `continue_ref is None`
short-circuits the new block, so the code that executes IS HEAD's, unmodified (spec §3.5) — structural, not
argued. The **external absolute** anchors are the 23 frozen exact-equality vectors in
`tests/test_price_tail.py` and `test_persona_stats_byte_identical_after_log_refactor`, both untouched and both
green. `test_price_tail.py` was **not edited** — the check R2-1 demanded.

## B-3 — the runtime guard raises rather than degrades

Decision recorded because "handles an unvalidated injection" (G8) is ambiguous. The guard **raises
`ValueError`**, naming the pack and the offending value, rather than silently falling back to `rscale = 1.0`.
A silent fallback would be the failure mode this whole slice exists to prevent: the feature deleting itself
without a signal. The precedent is `sample_postflop_decision`'s existing
`raise ValueError(f"persona pack {pack.id!r} has no postflop block")`. The comparison is written
`not _MIN <= ref <= _MAX`, so `NaN` — which fails every ordering test — lands in the same branch.

## B-4 — explicit JSON `null` is FORBIDDEN; absence stays the opt-out

The authorship question G8 left open, decided and pinned by `_continue_ref_authorship`. Field **absence** is
the legacy opt-out and runs the base code path; an explicit `"continue_ref": null` is **rejected**. Same
key-presence rule `stickiness` already uses (review C-1): an authored key that claims a calibration anchor and
supplies none is a lie about the pack, not a default.

## B-5 — disclosed: the packs carry `_doc` entries, so the content diff is not literally "six + six"

Verify-by #4 says the content diff shows only six `continue_ref` additions and six `version` bumps. It also
shows **`_doc` prose entries in the three packs that keep a `_doc` array** (lag, maniac, tag), following those
packs' existing per-version convention. No lever value moves. Full content diff: 34 insertions, 6 deletions
across the six files.

## B-6 — G4's pins, and what they do and do not claim

The river polar-bluff response is pinned for **all six** personas at ×0.25/×0.5/×1/×2/×4, to 9 significant
figures, together with two structural assertions: the base path is **exactly flat** across the same sweep
(`max − min == 0.0`, all six), and the scaled path is monotone in the lever. The flatness half is the one that
shows the coupling is NEW rather than pre-existing. Absolute magnitudes are small — the largest, maniac at
×4, is `P(raise) = 0.157`; at the authored value the row is `lag 0.0248 · tag 0.0152 · nit 0.0031 ·
maniac 0.0445 · calling_station 0.0031 · passive_fish 0.0057`. These are a **disclosure record**: nothing was
tuned to hit them and no band depends on them.

Note the sweep is done by authoring `call_looseness` on the probe copy for **every** persona, maniac included
(R2-10). That is why maniac's base row is flat here: sweeping maniac via `stickiness` instead would move the
FOLD merit at the same time and confound the reading, which is exactly what R2-10 measured.

## B-7 — the Director's own verification, run independently of the gates

Because a gate can be wrong in the same way its author was, each central claim was re-measured
outside the test file, in a separate process with `sys.path` pinned to the worktree.

| claim | measurement | result |
|---|---|---|
| bit-exactness beyond the 1,728-cell grid | 30,000 RANDOM facing cells — random holes, 3/4/5-card boards, 4 pots × 5 prices × 5 stacks × 4 opponent counts, `facing_raise` both ways, `PostflopContext` present 40% of the time, legacy and exact price denominators — opted-in pack vs `continue_ref=None` | **0 bitwise mismatches, worst abs deviation 0.0** |
| orthogonality beyond the grid | 8,000 random cells × 4 multipliers = **30,692** ratio comparisons | worst drift **2.22e-16** (lag, river, ×0.25) |
| routing direction beyond the grid | same sweep, 6,633 interior cells × 4 multipliers | **0 sign violations** |

**Counterfactual (the anti-no-op check the initiative now requires).** A copy of the module in
`$TMPDIR` with `rscale` forced to `1.0` — a literal no-op that keeps every other line of the slice,
including the packs, the model field, the guard and all 25 tests — fails **G1, G2, G4 and the G9
migration gate**, 4 of 25. The spec predicted G1/G2/G8/G9; the true set is slightly different (G8's
model half is a pure validation gate and passes on the no-op, G4 catches it). Separately, removing
only the `ActionType.FOLD in by_kind` guard — so the scale leaks onto the unopened branch's
check-raise shape — fails **G5 alone**, which is what G5 exists for.

**Zero collateral movement.** No seeded fixture, golden JSON, or frozen literal moved:
`test_price_tail.py`'s 23 exact-equality vectors, `test_persona_stats_byte_identical_after_log_refactor`,
`tests/data/coverage_baseline.json` and the `BANDS` dict are all untouched and green. **G12** is
therefore a zero delta — the graded-coverage fixture did not drift, so there is nothing to re-record
and nothing to adjudicate. **G10** passes with `BANDS` unedited; no band came near an exit, because
population play is bit-identical.

---

# BUILD FAN-IN REVIEW — 2026-08-02

Three reviewers, all **git-read-only**, on commit `f365082`: fresh `refuter` (Opus), Codex Sol
(`gpt-5.6-sol`, effort `high`), and `persona-realism-theory-reviewer`. **No reviewer found a HIGH defect
in the mechanism.** Refuter: *"the mechanism itself survived every attack I could construct."* Codex:
*"No HIGH findings … bit exactness: no defect found. Attach point: no defect found."* Theory reviewer:
*"the most disciplined slice I have reviewed on this initiative."*

Both verdicts were nonetheless FAIL / NEEDS-WORK, and correctly so: the defects were in the **gate set and
the disclosure**, not the engine. Every finding below was **reproduced by the Director before adjudication**.

## B-8 — ACCEPTED (Codex, MED) — G1 could be satisfied by a continuation *collapse*
G1 skipped a cell when the tuned distribution had no continue mass, and G2 accepted the collapse as a
correct downward move. Codex built a mutant that, below the anchor, zeroed CALL and RAISE for five personas
— they fold 100% instead of preserving the raise:call odds — and **all 24 gates passed**.

**Director reproduction:** installed the same mutant in a `$TMPDIR` copy → `24 passed`. Confirmed.
**Fix:** a skip is now only legitimate when the ANCHOR had no continue mass either; losing all continue
mass under a tuned lever is a failure. G1 also gained a per-persona comparison-count floor (refuter LOW),
because `worst` is keyed by persona and a fully-skipped persona would have passed having measured nothing.
**Post-fix:** the mutant now fails G1 and G-COMMIT.

## B-9 — ACCEPTED (refuter, MED) — G4 pinned the WEAKEST member of the disclosed class
`bluff_cell` is `bucket in (AIR, ACE_HIGH) and draw is NONE`, so the hard-zeroed-call class has two
members. G4 pinned only AIR at a half-pot price, and its comment asserted the class maximum was maniac's
`0.157`. **False of the class.**

**Director reproduction** (lag, `Ah8d` on `Kc9s3h2dTc`, to_call 0.5 into 6):

| | ×0.25 | ×1 | ×4 |
|---|---|---|---|
| this branch | 0.104207 | 0.317554 | 0.650504 |
| base engine | 0.317554 | 0.317554 | 0.317554 |

Span 0.546 versus the pinned cell's 0.086 — **6.3×** — and maniac reaches **0.773** at ×4. The theory
reviewer was handed the mild member as the headline number. **Fix:** an ACE_HIGH / small-price pin table
for all six personas, and the false magnitude sentence corrected.

## B-10 — ACCEPTED (refuter, MED) — a SECOND, undisclosed reach change: committed nodes go INERT
`_commit_transform` zeroes the FOLD merit while FOLD stays legal, so after the scale the vector is
`(0, C₀·L, 3·R₀·L/ref)` and **`L` cancels out of the whole distribution**, not merely out of the ratio.
`call_looseness` is therefore **inert** on SPR-committed facing nodes, where at the base engine it was the
dominant lever. G2 skips those cells (P(fold) pinned at 0 ⇒ not interior) and G1 is vacuously satisfied,
because inertness is a superset of orthogonality — so nothing saw it.

**Director reproduction** (tag, `AhAd` on `Kc9s3h2d`, SPR 1.0): base P(raise) `0.944882 / 0.810811 /
0.517241` across ×0.25/×1/×4; this branch **flat at 0.810811**.

**Adjudication: correct behaviour, but a real loss of reach that must be disclosed and gated.** It is the
same orthogonality property with no fold leg left to absorb the change. The consequence to state plainly:
**`R9-LOOSEFIT` has no reach over committed nodes.** **Fix:** new gate `G-COMMIT` pinning inertness in one
direction and the base engine's sensitivity in the other, plus a paragraph in the engine comment.

## B-11 — ACCEPTED AS DESIGNED, NOW PINNED (Codex, MED) — explicit `None` via `model_copy`
An unvalidated `model_copy(update={"continue_ref": None})` slips past the range guard and silently disables
the feature. True — and it is the **documented opt-out** (spec §3.5), the mechanism G3 uses to obtain the
base-engine path, and unreachable from production (the loader validates JSON; nothing in `app/` calls
`model_copy` on a `PersonaPostflop` — verified by both the refuter and Codex). Rejected as a code change,
**accepted as a pin**: a test now asserts the legacy path is taken without raising, so it is a decision on
record rather than an accident.

## B-12 — ACCEPTED AS A DISCLOSED LIMITATION (both reviewers, LOW) — the null round-trip
`model_dump()` emits `"continue_ref": null`, so `model_validate(pack.model_dump())` raises for a pack using
the legacy opt-out. Real. **The refuter's stated reason is wrong**, and the Director measured it:
the refuter wrote that `stickiness` *"keys on the VALUE and therefore round-trips cleanly."* It does not —
`_stickiness_authorship` keys on `model_fields_set`, and a side-by-side probe shows **both fields reject
their own dump identically**. So this is not an asymmetry introduced by the slice; it is the model's
existing authorship convention. Changing it would be a `stickiness` change wearing a `continue_ref` costume.
**Fix:** a test that measures both fields side by side, so the limitation is pinned and its pre-existing
shape is on the record.

## B-13 — ACCEPTED (Codex, LOW) — no gate enforced the version bump
Contract map C8 says nothing enforces a bump on content change. Codex reverted `calling_station` to
`1.1.1` and all 24 gates still passed. **Fix:** a per-pack version FLOOR (tuple compare), so a later slice
that bumps past it stays green without editing the test while a missed or reverted bump reds.

## B-14 — PARTIALLY ACCEPTED (theory reviewer, filed HIGH) — "the coupling generalises beyond the river cell"
The reviewer measured that absolute `P(raise)` moves ~proportionally with `call_looseness` at every cell
where the FOLD leg is material, largest on the semi-bluff leg, with the sign FLIPPED versus the base engine
(lag, flush draw: base 0.2619 → 0.1611 decreasing; branch 0.0815 → 0.4345 increasing).

**Director reproduction: numbers exact.** But the framing is rejected. On that same cell
`P(raise | continue)` is **exactly flat at 0.6109** in the branch against base `0.8626 → 0.2819` — i.e. the
measurement is the mechanism working. Absolute `P(raise)` MUST move with the lever once (a) `P(fold)`
responds to it, which is the slice's stated goal, and (b) the continue composition is frozen, which is the
other half. The two cannot both hold with absolute `P(raise)` fixed. It is also not undisclosed: **G2
asserts exactly this sign at every interior cell**, and §1 of the spec states freed mass goes to FOLD
rather than RAISE, which entails it.

**What IS accepted:** the practical consequence for the next slice. A `call_looseness` fit now moves
absolute raise frequency (hence AF) roughly in proportion, so `R9-LOOSEFIT` must **re-measure AF and the
barrel rates rather than assume the raise side is inert**. Folded into the disclosure text.
Downgraded HIGH → disclosure. The reviewer's proposed contract amendment (a §4 row and a §7 ordering entry
for the facing-node raise scale) is **filed as a follow-up**, not done here: the theory contract is an
owner-level document and amending it is out of this slice's file scope.

## B-15 — ACCEPTED (theory reviewer, Q2) — maniac's anchor: keep it, add the tripwire
The reviewer's answer to spec question 2: **accept the anchor as shipped; do NOT author `call_looseness`
for maniac in this slice.** Reasoning the Director agrees with and verified: the coupling is pre-existing
(maniac's `stickiness` already drove two levers), the migration would require inventing a
`size_elasticity` value — `0.55 ** (-_PRICE_STICKINESS_DAMP)` to hold today's price response — which is a
lever change inside a slice whose whole safety argument is that no lever value moves; and G9's migration
test already proves the migration is safe when someone does it.

The reviewer's real find is that the slice's gates were **structurally blind** to a `stickiness` edit,
because every probe authors `call_looseness` on its copy (deliberately, per R2-10). So the documented
caution was enforced by prose alone. **Fix:** G9 now asserts `maniac.stickiness == 0.55` with a message
naming the hazard. Sequencing recorded: the maniac split-lever migration is a prerequisite of the first
slice that wants to fit maniac's looseness or its price response — not of this one.

## Q1 — the river polar-bluff lever overlap: ESCALATED TO THE OWNER, not settled by the build
Spec §3.4 deferred this to the theory reviewer, which recommends **a carve-out now** (skip the raise scale
where the call merit is hard-zeroed), while stating deferral is safe because G4 pins the response either way.
Its argument: on that cell the mechanism buys **zero** orthogonality (the ratio is identically 1 with or
without the scale), so its entire effect there is side-effect; and the sign is wrong for the archetype —
`calling_station` has the roster's **highest** `call_looseness` (4.0) and its **lowest** `bluff_freq`
(0.03), so a fit that loosens a station would make it bluff-raise rivers more often.

The Director's counter-arguments, recorded because they are not in the reviewer's report:
1. A carve-out makes that cell **entirely lever-inert** — at the base engine `call_looseness` has no effect
   there at all, so "restore the status quo" means "no lever reaches this node".
2. It **weakens G2**: with the carve-out, `ΔP(fold) == 0` on an interior cell, so the bluff cell must be
   excluded from G2's strict-movement set — trading a disclosed coupling for a gate exception.
3. The roadmap already carries **`N-riverair`** — "river air/ace-high `call_merit = 0.0` is an absolute
   where a frequency belongs" — a filed defect stating the hard zero is itself wrong. When that lands, the
   cell stops being degenerate and the question dissolves.

Both options are defensible and the choice changes shipped behaviour, so it goes to the owner rather than
being settled by the maker or by whichever reviewer spoke last.

## Q1 — OWNER RULING (2026-08-02): **SHIP AS-IS, revisit with `N-riverair`**

The owner declined the theory reviewer's carve-out and accepted the coupling as shipped. Rationale, in the
owner's framing: the odd part is not the scale, it is the **hard-coded zero CALL weight on that node** — and
that is already a filed defect (`N-riverair`: "river air/ace-high `call_merit = 0.0` is an absolute where a
frequency belongs"). Once a real call frequency exists there, the node stops being degenerate, the scale
behaves exactly as it does everywhere else, and the overlap question dissolves rather than needing a
permanent special case.

Accepted costs, stated rather than discovered: until `N-riverair` lands, a persona tuned to call MORE will
also bluff-raise rivers more often — backwards for `calling_station`, which carries the roster's highest
`call_looseness` (4.0) and its lowest `bluff_freq` (0.03). G4 pins the response for all six personas on both
members of the class, so it cannot drift unnoticed in the meantime.

**Sequencing consequence:** `N-riverair` now carries this question. Whoever builds it must re-read spec §3.4
and this entry — restoring a call frequency on that node is the resolution, and if it ships without one the
overlap is still live.

---

## Fan-in outcome

**Reviewers:** refuter (Opus) FAIL · Codex Sol (`gpt-5.6-sol`, high) 2 MED + 2 LOW · theory reviewer
NEEDS-WORK. **No HIGH in the mechanism from any of the three.** Nine findings, all reproduced by the Director
before adjudication: **six accepted and fixed** (B-8 · B-9 · B-10 · B-13 · B-15 · refuter's LOW on the guard
placement), **two accepted-and-pinned rather than changed** (B-11 · B-12), **one partially accepted and
downgraded** (B-14, HIGH → disclosure), **one escalated and ruled by the owner** (Q1).

Post-fix: 30 gates, `1386 passed, 1 skipped`, exit 0, ruff clean, and both counterfactuals caught — the plain
no-op fails 5 gates, the continuation-collapse mutant fails 2. Shipped play is unchanged by the review pass:
it is tests, comments, and one guard reordering.

**The process note worth keeping.** The maker's own gate set was wrong in three distinct ways that the maker
could not see: a decisive gate satisfiable by a *collapse* rather than by the property (Codex), a disclosure
gate pinning the weakest member of the class it existed to disclose (refuter), and an entire second reach
change nothing in the suite could observe (refuter). None of the three is a defect in the engine. This is the
third consecutive round on this slice where two reviewers from different model families each found something
the other missed — and the first where the maker's *evidence* was the thing under attack rather than the
design.
