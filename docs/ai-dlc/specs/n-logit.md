# `N-logit` — nested logit on the facing node — **SPEC REV 3**

**Slug:** `n-logit` · **Initiative:** persona-realism (roadmap NEXT, `persona-realism.md:1949-1957`)
**Status:** SPEC REV 3 — awaiting Gate-2 approval. No production file has been edited.
**Base:** `origin/main` = `c12f773`. ⚠️ **The base is RED** — see §1a. **Contract map:**
`docs/ai-dlc/contracts/n-logit.md` (rev-2 amended) · **Ledger:** `docs/ai-dlc/ledger/n-logit.md`

> **Revision history.** **Rev 1: REJECTED** — its mechanism divided the raise leg by the *live* lever and
> multiplied by the same live lever, so the two cancelled; a measured no-op (ledger R-1). **Rev 2: REJECTED**
> — mechanism correct and certified by both reviewers, but it broke 6 frozen exact-equality vectors no gate
> covered, shipped a gate a correct build could not pass, bounded the harmless end of the new lever, and
> declared a green base that is red (ledger R2-1…R2-10). **Rev 3** adopts the refuter's single-raise-scale
> reformulation, which is **bit-exact** and collapses the change to ~2 lines.

---

## 1. Goal

Make `call_looseness` control **whether** the bot continues and the raise-side calibration control **how**, so
that reducing a bot's calling lever routes freed probability mass to **FOLD** rather than **RAISE** — with
today's play preserved bit-for-bit and no band re-anchor.

## 1a. ⚠️ Blocker: the base is red — fix before this slice

Two tests fail at `c12f773` in a pristine checkout (Director re-run, unpiped):

```
FAILED tests/test_limper_coverage_belt.py::test_limper_coverage_fires_on_organic_play
        UTG2 faces-1 fire count 84 != pinned 91
FAILED tests/test_personas_postflop.py::test_persona_stats_byte_identical_after_log_refactor
        calling_station AF 0.3277777777777778 != golden 0.32409972299168976
2 failed, 1354 passed, 1 skipped
```

Bisect: `61efc42` 🔴 → **`8729e14` (#159) 🟢** → **`81a5b24` (#160, N-LAGWIDTH) 🔴 re-broken** → `c12f773` 🔴.
Both are pinned goldens invalidated by a real behaviour change that was never re-recorded — the **fourth**
occurrence of the lost-re-record pattern. **Fix as its own `chore/` PR before this slice** (precedent #159),
so N-logit's identity gates compare against a genuinely clean tree.

## 2. Why

At a facing-chips node three merits — FOLD, CALL, RAISE — are normalized in one pass (`:998-1004`).
`call_looseness` multiplies the CALL merit only (`:873`). Mass removed from CALL is redistributed to FOLD and
RAISE **in proportion to their existing merits**, so on aggressive personas it lands mostly on RAISE
(roadmap `R10-4`). Measured at HEAD, halving each pack's effective looseness moves raise-share the **wrong**
way for every persona: lag/tag/station **+0.1716**, maniac **+0.1715**, nit **+0.1715**, fish **+0.1691**.

**Scope honesty.** Both reviewers confirmed `R9-DEFENCE-a`'s mechanism is **exogenous** and does not need this
slice, and its own design records its magnitude as DIRECTIONAL-only (`r9-defence-design.md` §8.6). **This spec
does not claim to unblock it.** It removes a live footgun and unblocks any future *fit* on this node
(`R9-LOOSEFIT`).

## 3. Mechanism

### 3.1 Requirement

Writing final merits `(F, C_f, R_f)`, both must hold: **identity** — at `L = L₀`,
`(F, C_f, R_f) = (F, C₀·L₀, R₀)`; and **orthogonality** — `∂/∂L [ R_f/(C_f+R_f) ] = 0`. These hold iff
`C_f = C₀·L` and `R_f = R₀·L/L₀` with **`L₀` frozen**.

`L₀` cannot be a code constant (S4 split), cannot be re-derived from the live lever (that is rev 1's
cancellation), and cannot come from re-authoring `aggression` (shared with the unopened branch, `:920-922`;
ledger R-1a). It must be a **new authored pack number**.

### 3.2 The lever

```python
# N-logit: the `call_looseness` value this persona's FACING-NODE raise behaviour is
# calibrated against. FROZEN BY DESIGN — it must NOT be updated when `call_looseness`
# is tuned. Re-synchronising the two reproduces the rev-1 cancellation and silently
# deletes this feature (ledger R-1, R2-6).
continue_ref: float | None = Field(default=None, ge=0.05, le=8.0)
```

**Bounds (ledger R2-5).** `ge=0.05`, **not** `gt=0.0`: the dangerous end is near zero, not above 8. Codex
proved `gt=0.0` accepts the subnormal `5e-324`, which makes the scale `inf` and the emitted vector
`[0.0, 0.0, nan]`, and that `1e-8` validates while yielding a degenerate `P(raise) ≈ 0.99999997`. `le=8.0` is
2× the largest shipped value (station 4.0). **A runtime guard is still required at the division site** —
`model_copy(update=…)` bypasses validation entirely, as both reviewers demonstrated
(`tests/test_personas_postflop.py:227`, `:5790`).

**Authored values — each pack's current effective looseness, so play is preserved by construction:**
nit 0.6 · tag 0.6 · lag 0.55 · **maniac 0.55 (the `stickiness` fallback — it authors no `call_looseness`)** ·
calling_station 4.0 · passive_fish 0.42.

**Maniac's shared-fallback caveat (ledger R2-10).** Its anchor traces to `stickiness`, which is *also* the
`_price_exponent` fallback (`:627-644`). Consequences to state, not discover: a future slice editing maniac's
`stickiness` for price reasons silently desynchronises anchor from lever; and maniac's effective looseness
cannot be swept in isolation, so its G1/G2 probe **must author `call_looseness` on the probe copy** or the
measurement is confounded by a simultaneous fold-merit move (measured: maniac RIVER/AIR `P(raise)` moves
`0.404853 → 0.430852` under ×0.5 at HEAD, where lag and tag stay exactly flat).

### 3.3 The code delta — two lines

In the facing branch, immediately before the normalization at `:998`:

```python
ref = pf.continue_ref
if ref is not None and ActionType.FOLD in by_kind:
    rscale = looseness / ref          # exactly 1.0 while the lever sits at its anchor
    entries = [(a, m * rscale) if a is ActionType.RAISE else (a, m) for a, m in entries]
```

**Nothing else changes.** The CALL leg keeps HEAD's exact `* looseness` (`:873`); both raise legs, both B5b
subtractions (`:992`, `:994`) and `_commit_transform` are **untouched**.

**Why this beats rev 2's six deltas** (ledger R2-1): at `L == ref` the scale is *exactly* `1.0`, so the
opted-in path is **bit-exact** rather than exact-to-1-ulp. Rev 2's divide-then-multiply left a 1-ulp residue
that broke 6 of 23 frozen exact-equality vectors in `tests/test_price_tail.py:289` (a file rev 2's touch list
did not even name). It also removes the need to restate the B5b subtractions and the entire clamp-safety
proof burden that went with them.

`P(raise | continue) = R₀·L/ref / (C₀·L + R₀·L/ref) = (R₀/ref) / (C₀ + R₀/ref)` — **`L` cancels**, which is
the orthogonality property, obtained without a second `rng.choices` or a restructured normalization.

### 3.4 Disclosed behavioural coupling — the river polar-bluff cell (ledger R2-3)

On the river polar-bluff cell `call_merit` is hard-zeroed (`:874-875`), so **at HEAD the bluff-raise frequency
is exactly independent of `call_looseness`**. Under the scale it is not. Measured: lag RIVER/AIR `P(raise)`
HEAD flat at `0.271272` across ×1/×0.5/×0.25/×2 → scaled `0.271272 / 0.156920 / 0.085140 / 0.426772`.

**Adjudicated: disclose, do not exclude.** On that cell the only way to continue *is* to raise, so scaling the
continue candidate by the continue lever is the mechanism behaving correctly on a degenerate node. But it does
place `call_looseness` on a magnitude §3.6 assigns to `bluff_freq`. **This is a lever-overlap question for the
`persona-realism-theory-reviewer` at build fan-in, and it is flagged, not settled here.** G4 pins the response
so it can never move silently.

> **⚠️ BUILD-STAGE CORRECTION (2026-08-02, ledger B-9).** The magnitude above understates the class. The
> `bluff_cell` predicate is `bucket in (AIR, ACE_HIGH) and draw is NONE`, so the hard-zeroed-call class has
> **two** members, and `ACE_HIGH` at a small faced price is far larger: lag `P(raise)` **0.104207 / 0.317554 /
> 0.650504** across ×0.25/×1/×4 (base flat at 0.317554), a span of 0.546 against the AIR cell's 0.086, with
> maniac reaching **0.773** at ×4. G4 now pins **both** members for all six personas. The theory reviewer's
> answer, and the Director's counter-arguments, are recorded in the ledger under **Q1**.
>
> **OWNER RULING (2026-08-02): SHIP AS-IS; the question is handed to `N-riverair`.** The carve-out was
> declined — the anomaly is the hard-coded zero CALL weight, not the scale, and `N-riverair` is already filed
> to replace that absolute with a frequency. When it does, the node stops being degenerate and the overlap
> dissolves without a permanent special case. Accepted cost until then: a persona tuned to call more will also
> bluff-raise rivers more, which is backwards for `calling_station`. G4 pins both members of the class for all
> six personas so it cannot drift. **`N-riverair`'s builder must read this section.**

### 3.4b Second disclosed reach change — SPR-committed nodes go INERT (build stage, ledger B-10)

The mirror image of §3.4, found by the build refuter and missed by this spec. `_commit_transform` zeroes the
FOLD **merit** while FOLD stays in `by_kind`, so on a committed facing node the post-scale vector is
`(0, C₀·L, 3·R₀·L/ref)` and **`L` cancels out of the whole distribution**, not merely out of the ratio.
`call_looseness` is therefore **inert** there, where at HEAD it was the dominant lever — tag, `AhAd` on
`Kc9s3h2d` at SPR 1.0: base `P(raise)` 0.944882 / 0.810811 / 0.517241 across ×0.25/×1/×4, now flat at
0.810811.

Internally consistent — it is the same orthogonality property with no fold leg left to absorb the change —
but a real loss of reach, and no gate could see it (G2 skips those cells because P(fold) is pinned at 0; G1
is vacuously satisfied because inertness is a superset of orthogonality). **Consequence to state before it is
discovered: `R9-LOOSEFIT` has no reach over SPR-committed nodes.** Gated by **G-COMMIT**, which pins the
inertness in one direction and the base engine's sensitivity in the other.

### 3.4c What a looseness fit now moves (build stage, ledger B-14)

Because `P(fold)` responds to the lever and the continue *composition* is frozen, **absolute** `P(raise)`
moves roughly in proportion to `call_looseness` wherever the fold leg is material — with the sign FLIPPED
versus HEAD, which is the whole point (lag on a flush draw: base 0.2619 → 0.1611 as the lever rises; branch
0.0815 → 0.4345, while `P(raise | continue)` stays exactly flat at 0.6109). G2 asserts that sign at every
interior cell. The practical rule for the next slice: **a `call_looseness` fit must re-measure AF and the
barrel rates — it may not assume the raise side is inert.**

### 3.5 The `None` path

`continue_ref is None` ⇒ the block above does not execute ⇒ **HEAD's code, unmodified**. Byte-identity for
un-opted-in callers is structural, not argued.

### 3.6 No new fitted magnitude

No band, no lever value, no constant whose observed frequency effect is asserted. The one new number per pack
is a **frozen copy of an existing authored value**, chosen precisely so behaviour does not move. Softmax law
(`theory-contract.md` §2) satisfied vacuously.

## 4. Evidence at HEAD

Grid: 6 personas × 3 streets × 9 hand classes (7 buckets + strong draw + **weak draw**) × 4 faced prices ×
4 stack/opponent combos × `facing_raise` ∈ {False, True}. Patched module in `$TMPDIR`; **no repo file edited**.

| persona | identity at authored values | raise-share drift, ×0.25 / ×0.5 / ×2 / ×4 |
|---|---|---|
| calling_station | **BIT-EXACT (0 diffs)** | 1.4e-17 · 6.9e-18 · 1.4e-17 · 1.4e-17 |
| lag | **BIT-EXACT (0 diffs)** | 1.1e-16 · 1.1e-16 · 1.1e-16 · 1.1e-16 |
| maniac | **BIT-EXACT (0 diffs)** | 2.2e-16 · 1.1e-16 · 2.2e-16 · 1.1e-16 |
| nit | **BIT-EXACT (0 diffs)** | 5.6e-17 · 5.6e-17 · 5.6e-17 · 1.1e-16 |
| passive_fish | **BIT-EXACT (0 diffs)** | 5.6e-17 · 1.1e-16 · 1.1e-16 · 1.1e-16 |
| tag | **BIT-EXACT (0 diffs)** | 1.1e-16 · 1.1e-16 · 1.1e-16 · 1.1e-16 |

Corroborating independent reviewer measurements on the rev-2 form of the same mechanism: refuter 8,064 cells
(HEAD drift 0.152–0.333 → ≤2.22e-16) and **AF/FtC/WTSD identical, not merely in-band**, at N=200 for all six;
Codex ×0.25…×4 (HEAD drift 0.0563–0.5932 → ≤1.11e-16).

Probes: `/tmp/claude-501/probe_rev3.py`, `probe_optA.py`, `probe_check.py` (scratchpad, outside the repo).

## 5. Files this slice may touch

`backend/app/domain/personas_postflop.py` (the two-line block) · `backend/app/domain/content/models.py` (the
new field **and** the correction of the now-stale `stickiness` authorship comment at `:171-176` — ledger R-4,
whose recorded *reason* was itself corrected in R2-9) · `content/personas/*.json` (all six: add
`continue_ref`, bump `version`) · `backend/tests/test_personas_postflop.py` and
`backend/tests/test_range_estimate.py` (**new tests only, no band edits**).

**NOT touched:** `tests/test_price_tail.py` — and rev 3 must not need to (bit-exactness is what makes that
true; if a builder finds themselves editing it, **stop**, the implementation has diverged from this spec) ·
the `BANDS` dict · `aggression` / `_AGGRESSION_CAP` · `range_estimate.py` production code · the grader ·
`spot_signature()`.

## 6. Acceptance criteria

| id | class | criterion |
|---|---|---|
| **G1** | **HARD, RED-FIRST — the decisive gate** | **Orthogonality.** Sweep `call_looseness` over ×0.25, ×0.5, ×2, ×4; `P(raise)/(P(call)+P(raise))` invariant to ≤1e-12 at every cell **where `P(call)+P(raise) > 0`** (ledger R2-2: river-air FOLD+CALL cells compute 0/0). Maniac swept by **authoring `call_looseness` on the probe copy** (§3.2). Fails at HEAD (≈ +0.17 at ×0.5). |
| **G2** | **HARD, RED-FIRST** | **Routing SIGN only** (ledger R2-2 — rev 2 stated this on the wrong quantity). For multipliers **< 1**: `ΔP(fold) > 0` and `ΔP(raise) ≤ 0`. For multipliers **> 1**: signs invert. Strict movement required only on **interior** cells (`0 < P(fold) < 1`). G1 owns orthogonality; G2 owns direction. |
| **G3** | **HARD** | **Bit-exact identity.** At authored values the full grid — 7 buckets + **strong and weak draws**, both `facing_raise` states, **both facing legal shapes**, **and river busted-draw `PostflopContext` states** (ledger R2-7) — is **bit-identical** to the fixed base. No rounded digest and no modal-action clause are needed: bit-exactness is strictly stronger and moots ledger R2-8's tie problem. |
| **G4** | **HARD** | **Bluff-cell disclosure gate** (§3.4). Pin the river polar-bluff `P(raise)` response to the sweep, so the disclosed coupling cannot move silently. |
| **G5** | **HARD** | **Unopened branch untouched.** Exact-identity sweep over CHECK+BET and CHECK+RAISE shapes (ledger R2-7 — rev 2's §7 claimed this from a gate that covered only facing shapes). |
| **G6** | **HARD** | **One draw.** Action draw stays FIRST, sizing SECOND; all eight capture-rng consumers (contract map C1) pass **unmodified**. |
| **G7** | **HARD** | **Estimator.** Both parity tests pass unmodified, plus an assertion that `_postflop_action_dist` returns exactly the node's **legal** action set — conditioned on the legal shape, **not** hard-coded to three keys, excluding the zero-total singleton path (`range_estimate.py:364`). |
| **G8** | **HARD** | **Validation, not inspection** (ledger R2-5). Assert the model rejects `0`, `NaN`, `inf`, **the smallest subnormal**, and out-of-bound `continue_ref`; assert the **runtime guard** handles an unvalidated `model_copy` injection. Decide and pin whether explicit JSON `null` is forbidden while field *absence* remains the legacy opt-out. |
| **G9** | **HARD** | **Frozen-ness lifecycle** (ledger R2-6). A validated-JSON test that changes **only** `call_looseness` and proves `continue_ref` is unchanged, plus a maniac migration test (author both split levers, `stickiness` removed by `_stickiness_authorship`, `continue_ref` stays 0.55, orthogonality still holds). Doc line: **a looseness fit never updates the reference; only an explicit raise-calibration change may.** |
| **G10** | **NO-REGRESSION** | AF, fold-to-c-bet, WTSD pass with `BANDS` **unedited**. ⛔ If any band exits, **STOP and escalate to W4-b** — do not widen. |
| **G11** | **NO-REGRESSION** | **No NEW test failures vs the recorded base set** (ledger R2-4). Under rev 3 the base set should be **empty** once §1a's `chore/` PR lands. |
| **G12** | **REPORT** | Cumulative graded-coverage delta vs the immutable snapshot; any loss adjudicated. |

**Anti-no-op set: G1, G2, G8, G9 — G1 decisive** (ledger R2-7 corrected rev 2's false claim that only G1/G2
qualified; `content/models.py` has no `model_config`, so pydantic's default `extra='ignore'` means G8/G9 also
fail on an empty diff). **A schema-and-content-only change would pass G8/G9 but fail G1.**

## 7. Out of scope

Re-authoring `aggression` (ledger R-1a) · a two-stage `rng.choices` (contract map C1/C3) · fitting any lever
(`R9-LOOSEFIT`) · the line-keyed continue shift (`R9-DEFENCE-a`) · `N-vecfit` · `R10-TAIL` · resolving the
river bluff-cell lever overlap (§3.4 — disclosed and gated here, adjudicated by the theory reviewer).

## 8. Constraints

Domain core has no web/DB imports (test-enforced) · strategy lives in versioned `content/` data — the new
number is a **pack** value, the correct side of the S4 split · `spot_signature()` frozen · results are
frequency + EV, never boolean · grading stays behind the one async `StrategyProvider`.

## 9. Verify-by

1. `./scripts/verify.sh` → `BACKEND VERIFY OK`, **with §1a's `chore/` PR landed first**. Until then the
   criterion is "no NEW failures vs the two recorded base failures".
   **Never read a suite's result from a piped exit code** — a pipeline returns the last command's status, which
   is how rev 2 came to declare a red base green (ledger R2-4).
2. `cd backend && ruff check .` → clean.
3. G1/G2 RED-FIRST demonstration at the fixed base, failing numbers in the ledger and PR body.
4. `git diff --stat <base> -- content/` shows **only** six `continue_ref` additions and six version bumps.
5. Build from a worktree off the fixed base; the shared tree is at `61efc42` and behind.
6. Population stats measured in a **separate process** with `sys.path` pinned to the worktree. Pack ids are
   `persona_calling_station`-style, not `calling_station`.
