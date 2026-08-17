# `N-logit` — ticket plan (**for SPEC REV 3**)

**Spec:** `docs/ai-dlc/specs/n-logit.md` (rev 3) · **Contract map:** `docs/ai-dlc/contracts/n-logit.md` ·
**Ledger:** `docs/ai-dlc/ledger/n-logit.md`
**Base:** `origin/main` = `c12f773` — ⚠️ **RED**, see T0. **Branch:** `feat/persona-realism-n-logit`.

> Rev-1 and rev-2 ticket plans are superseded. Rev 3's mechanism is **two lines**, so the build collapses:
> the old T3 (six deltas) and the B5b/clamp work are gone, and the identity gate is **bit-exact**.

**Build discipline:** worktree off the fixed base; never commit in the shared tree (concurrent sessions move
HEAD); push by immutable OID — `git push origin <sha>:refs/heads/<branch>`, bare, no pipes. Single fixture
recorder. **Never read a suite result from a piped exit code** (ledger R2-4).

```
T0 (separate PR, merge first) ──> T1 ──> T2 ──> T3 ──┬──> T4 ──┐
                                                     └──> T5 ──┴──> T6
```

---

## T0 — ⚠️ SEPARATE `chore/` PR: main is red, fix it first
**Owns:** the two stale pins · **Branch:** `chore/restore-lagwidth-fixture-records` · **Blocks:** everything.

Two pinned goldens at `c12f773` were invalidated by a real behaviour change and never re-recorded:
- `tests/test_limper_coverage_belt.py::test_limper_coverage_fires_on_organic_play` — UTG2 faces-1 **84 vs 91**
- `tests/test_personas_postflop.py::test_persona_stats_byte_identical_after_log_refactor` —
  calling_station AF **0.3277777777777778 vs 0.32409972299168976**

Bisect attributes both to **#160 (N-LAGWIDTH)**: `61efc42` 🔴 → `8729e14` (#159) 🟢 → `81a5b24` (#160) 🔴 →
`c12f773` 🔴. Fourth occurrence of the lost-re-record pattern; precedent is #159.

**Before re-recording, confirm the move is the *expected* consequence of N-LAGWIDTH's width trim** — re-run
the underlying search standalone rather than assuming, so a genuine regression is not laundered into a pin.
Disclose old→new values and mechanism in-file per the `RE-RECORDED` convention.

**Done-condition:** `./scripts/verify.sh` → `BACKEND VERIFY OK` at the chore branch tip.

---

## T1 — HEAD baseline and the RED-FIRST sensitivity gates
**Owns:** `backend/tests/test_personas_postflop.py` (new tests only — **no band edits**) · **Depends on:** T0.

Grid: 6 personas × 3 streets × 9 hand classes (7 buckets + strong + **weak** draw) × 4 faced prices ×
4 stack/opponent combos × `facing_raise` ∈ {False, True} × both facing legal shapes × **river busted-draw
`PostflopContext` states**.

- **G1 (RED-FIRST, decisive)** — sweep ×0.25/×0.5/×2/×4; `P(raise)/(P(call)+P(raise))` invariant to ≤1e-12 at
  every cell **where `P(call)+P(raise) > 0`**. **Sweep maniac by authoring `call_looseness` on the probe
  copy** — its `stickiness` fallback is shared with `_price_exponent`, so a naive sweep is confounded.
- **G2 (RED-FIRST)** — routing **sign** only, per direction: multipliers < 1 ⇒ `ΔP(fold) > 0`,
  `ΔP(raise) ≤ 0`; multipliers > 1 ⇒ inverted. Strict movement only on interior cells (`0 < P(fold) < 1`).
- **G3** — bit-exact identity vs the fixed base. No rounded digest, no modal-action clause.

**Acceptance:** G1/G2 **FAIL at the fixed base**, numbers recorded in the ledger. G3 green.
**Done-condition:** `cd backend && python -m pytest tests/test_personas_postflop.py -k "orthogonal or routing or identity" -q` → G1/G2 red, G3 green.

> ⚠️ A sensitivity gate is the only kind an empty diff cannot pass. Rev 1 shipped a spec whose gates a no-op
> satisfied on 8 of 10 criteria. If G1 passes at HEAD, the gate is mis-built.

---

## T2 — The `continue_ref` lever: model, bounds, guard, packs
**Owns:** `backend/app/domain/content/models.py` · `content/personas/*.json` (six) · **Depends on:** T1.

- `continue_ref: float | None = Field(default=None, ge=0.05, le=8.0)` — **`ge=0.05`, not `gt=0.0`**: the
  dangerous end is near zero (`5e-324` validates and yields `[0.0, 0.0, nan]`).
- Document it as a **frozen calibration anchor**; a validator tying it to `call_looseness` would delete the
  feature.
- **Correct the stale `stickiness` authorship comment** (`:171-176`) and `_stickiness_authorship`'s docstring.
- Decide and document whether explicit JSON `null` is forbidden while field *absence* is the legacy opt-out.
- Author six packs (nit 0.6 · tag 0.6 · lag 0.55 · maniac 0.55 · calling_station 4.0 · passive_fish 0.42);
  bump each `version`.

**Done-condition:** `cd backend && python -m pytest tests/ -q -k "pack or content or persona_load"`

---

## T3 — The two-line scale
**Owns:** `backend/app/domain/personas_postflop.py` · **Depends on:** T2.

Insert before the normalization at `:998`, in the facing branch:

```python
ref = pf.continue_ref
if ref is not None and ActionType.FOLD in by_kind:
    rscale = looseness / ref          # exactly 1.0 while the lever sits at its anchor
    entries = [(a, m * rscale) if a is ActionType.RAISE else (a, m) for a, m in entries]
```

Plus the **runtime guard** for the division (model validation cannot protect `model_copy`). Nothing else
changes — the CALL leg, both raise legs, both B5b subtractions and `_commit_transform` are untouched.

Comment block must record: the R10-4 misroute this fixes; **why the divisor is frozen rather than live —
citing ledger R-1, where rev 1 died**; and that `L == ref ⇒ rscale == 1.0` is what makes the opted-in path
bit-exact.

**Acceptance:** G1/G2 pass; G3 bit-exact; **`tests/test_price_tail.py` untouched and green** — if it needs
editing, the implementation has diverged from the spec, so **stop**.
**Done-condition:** `cd backend && python -m pytest tests/test_personas_postflop.py tests/test_price_tail.py -q && ruff check .`

---

## T4 — Structural + safety gates
**Owns:** `backend/tests/test_personas_postflop.py` · **Depends on:** T3. **Parallel with T5.**

- **G4** bluff-cell disclosure gate — pin the river polar-bluff `P(raise)` response to the sweep (spec §3.4).
- **G5** unopened branch untouched — exact-identity sweep over CHECK+BET and CHECK+RAISE.
- **G6** one draw — action FIRST, sizing SECOND; all eight capture-rng consumers pass **unmodified**.
- **G8** validation not inspection — model rejects `0`, `NaN`, `inf`, **smallest subnormal**, out-of-bound;
  runtime guard survives an unvalidated `model_copy` injection.
- **G9** frozen-ness lifecycle — validated-JSON test changing **only** `call_looseness` proves `continue_ref`
  unchanged; maniac migration test (both split levers authored, `stickiness` removed, `continue_ref` stays
  0.55, orthogonality holds).

**Done-condition:** `cd backend && python -m pytest tests/test_personas_postflop.py tests/test_price_tail.py tests/test_mw_catch_toppair.py -q`

---

## T5 — Estimator gate
**Owns:** `backend/tests/test_range_estimate.py` · **Depends on:** T3. **Parallel with T4.**

**G7** — both parity tests (`:507`, `:565`) pass **unmodified**, plus an assertion that
`_postflop_action_dist` returns exactly the node's **legal** action set — conditioned on the legal shape, not
hard-coded to three keys, excluding the zero-total singleton path (`range_estimate.py:364`).

Docstring records why: the parity tests compare estimator-vs-live using the *same* capture mechanism on both
sides, so they detect divergence but **not shared corruption**.

**Done-condition:** `cd backend && python -m pytest tests/test_range_estimate.py -q`

---

## T6 — Fan-in
**Owns:** seeded fixtures (**sole recorder**) · **Depends on:** T4 and T5.

- **G10** — AF, fold-to-c-bet, WTSD pass with `BANDS` **unedited**. ⛔ Band exit ⇒ **STOP, escalate to W4-b**.
- **G11** — **no NEW failures vs the recorded base set** (empty once T0 lands).
- **G12** — cumulative graded-coverage delta vs the immutable snapshot; adjudicate any loss.
- Run the call sites the contract map left uninspected: `tests/test_bet_sizing.py:129`,
  `tests/test_arrival_range_ftc.py:{173,222}`.
- Fixtures should **not** move — the opted-in path is bit-exact. If one does, that is a signal the
  implementation diverged, not a re-record opportunity. Investigate before touching it.

**Acceptance:** `./scripts/verify.sh` → `BACKEND VERIFY OK`; `ruff check .` clean;
`git diff --stat <base> -- content/` shows only six `continue_ref` additions and six version bumps.

---

## Fan-in review (per the initiative's standing policy)

Fresh `refuter` + **`persona-realism-theory-reviewer`** + Codex Sol (behaviour-touching ⇒ Codex included), all
**git-READ-ONLY**. Two items must be put to the theory reviewer explicitly:
1. **The river polar-bluff lever overlap** (spec §3.4) — `call_looseness` now moves a magnitude §3.6 assigns
   to `bluff_freq`. Disclosed and gated, **not adjudicated**.
2. **Maniac's anchor traces to a shared fallback** (`stickiness`, also `_price_exponent`'s) — is pinning the
   anchor to it acceptable, or does maniac need `call_looseness` authored as part of this slice?

## Builder notes

- `_STATS_EXT_CACHE` is pack-fingerprint-keyed since #155. **T2 changes pack content**, so the fingerprint
  moves by design — expected, not a defect.
- Watch the two `N-3BSTRATA` lag gates (`test_personas_postflop.py` ~:5136, ~:5265); measure pre/post.
- Measure population stats in a **separate process** with `sys.path` pinned to the worktree.
