# Contracts — R9-LOOSEFIT (fit `call_looseness` for nit/tag/lag)

> ## ⚠️ REV-2 SCAN (2026-08-04) — read this before §1–§8 below, which are INCOMPLETE
>
> The rev-1 scan (§1–§8, dated 2026-08-03) searched for tests that *name* the lever. Four
> load-bearing constraints do not name it, and the rev-2 build was halted at T1 as a result. This
> scan searched by **dependency** instead and ran six whole-suite arms at different lever values
> via a load-time patch (no file on disk edited; repo verified untouched, pack md5s unchanged).
>
> **The mechanism that defeats name-based search:** `looseness` is appended only inside
> `if ActionType.FOLD in by_kind` (`personas_postflop.py:944`, `:979`), and since N-LOGIT
> `continue_ref` also scales RAISE by `looseness/continue_ref` (`:1239-1249`). At a facing node the
> merit vector is `(F, C₀·L, R₀·L/ref)` — so **`L` moves P(fold) at every non-committed facing
> node while leaving raise:call fixed.** Any test reading a fold rate, a fold *difference*, a WTSD,
> or a cross-persona fold ordering is coupled whether or not it mentions the lever.
>
> ### Whole-suite arms (base = 1416 passed / 1 skipped)
>
> | arm | nit / tag / lag | failures |
> |---|---|---|
> | A | **0.42 / keep / keep** | **2** — both sanctioned re-records |
> | D | 0.58 / 0.58 / 0.53 | 7 |
> | B | 0.45 / 0.50 / 0.48 | 8 |
> | E | 0.32 / 0.35 / 0.33 | 10 |
> | C | 0.90 / 0.90 / 0.85 | 11 |
> | F | 1.20 / 1.20 / 1.10 | 12 |
>
> **Arm A is the headline: a nit-only move to 0.42 costs exactly two re-recordable fixtures.**
>
> ### Hard blockers (cannot be re-recorded — each encodes a deliberate claim)
>
> | id | test | binding window |
> |---|---|---|
> | H1 | `test_elasticity_split_faithful_decomposition_byte_identical` `:1321`/assert `:1338` — builds its control from the SHIPPED tag pack | **tag must equal its `stickiness` EXACTLY.** No tolerance, no literal to re-record |
> | H2 | `_W3R6_RAISE_DROP` `:6260`, asserted `:6280-6281` `abs=5e-4`, four tag cases | tag effectively frozen; **carries NO documented re-record protocol** (unlike R1–R4) |
> | H3 | R9-DEFENCE-a ladder `:9452`/assert `:9476` | **nit floor is NOT a constant.** In arm E tag's rise ROSE to 0.1343 while nit's fell to 0.0303 — tightening tag moves tag *into* the steep region, so **tightening tag raises the nit floor.** The 0.38-FAIL/0.42-pass bracket is only valid with tag held at 0.6 |
> | H4 | ½-pot fold ordering `:790`/asserts `:819-826` | four two-sided bounds: **nit ceiling ≈0.80–0.85** (`fish−nit<0.10`) · **tag floor ≈0.32–0.35** (`fish>tag`) · **lag ceiling ≈0.70–0.80** (`maniac<lag`) · `lag<tag<nit` margins today 0.0224 / 0.0760 |
> | H5 | population WTSD bands `:5641`/assert `:5746`, rows `:2576-2577` | tag and lag ceilings in (0.60, 0.90) / (0.55, 0.85), not bisected. **Explicitly NOT re-recordable** — the single re-anchor is reserved for W4-b (`contracts/persona-realism-fit-loop.md:116-121`) |
> | H6 | **estimator price-response floor** `test_range_estimate.py:640`/assert `:680` | **tag floor ≈0.39–0.40** — the strictest tag floor found. ⛔ **This directly REFUTES §1's last bullet below** ("Estimator-parity tests: zero `call_looseness` hits — not load-bearing"). The chain is analytic: fold spread `3x/((4+x)(1+x))` with `x ∝ L`, zero at both ends |
> | H7 | tag under-pocket-pair fold floor `:491`/asserts `:509-510` | **tag ceiling ≈1.0–1.2**; encodes the F7 bug-fix claim |
> | H8 | α bluff-catcher ceiling `:670`/assert `:784` | nit crosses between 0.30 and 0.35; tag and lag between 0.20 and 0.25. **Real but dominated** — H3, H4 and H6 all bind above it, which is why it never fired in any arm |
>
> ### Re-recordable fixtures (all four require attribution proven by revert)
>
> | id | fixture | protocol | red in |
> |---|---|---|---|
> | R1 | `_GOLDEN_STATS_N200` `:3449`/assert `:3545-3558` | `:3316-3448` + `:3547-3548`; two named attribution methods `:3338-3341`, `:3530-3535` | **every arm**, incl. nit-only — via the shared nine-seat rng stream; the failing cell is usually another persona's |
> | R2 | `_PRE_M3_FIRES` `test_limper_coverage_belt.py:236`/assert `:328-331` | module docstring `:44-287`, attribution `:277-287` | **every arm** |
> | R3 | `tests/data/coverage_baseline.json`, `test_coverage_baseline.py:355-363`, `_record()` `:350` | `:325-328` + `:15-274`; **carries the "compute the old side from the FIXTURE, never the prose" rule** `:245-255` | B/C/E/F only — **green in arm A** |
> | R4 | turn-barrel loop budget `test_grade_map_turn_river.py:645` | `:626-635` "re-measure the first-hit offset, never raise blindly" | none — but first hit 1746 of 2300, the one budget a stream displacement can silently exhaust |
>
> ### Ruled OUT, with reasons (negative results that matter)
>
> - **`test_price_tail.py`** — `HEAD_VECTORS` `:142-166` is station/fish only; the tail-inertness test `:294` is a self-comparison where `L` cancels. Green in all arms. (Rev-1 §1 said this correctly.)
> - **`test_node_trace.py:97-98`, `:132`** — on the unopened BET branch, where no `looseness` term exists at all. Structurally unreachable.
> - **`test_mw_catch_toppair.py`** (46 tests), **`test_arrival_range_ftc.py`** — within-persona direction or byte-identity self-comparisons. The hypothesis that a very tight nit empties its river continuation range was tested and **refuted** (green at nit 0.32).
> - **`test_r9d_s1_...effect_floor` `:8188`** — expected to be a tightening blocker; **refuted**. nit's ΔP(fold) is non-monotone and *rises* as nit tightens (0.1312@0.60 → 0.1488@0.30). It is a distant *loosening* ceiling.
> - **Every unopened / matched-with-option node** — no `looseness` term on those paths, so the whole c-bet / aggression / position / texture / bluff-frequency surface is out of reach.
> - **SPR-committed facing nodes** — `_commit_transform` zeroes FOLD so `L` cancels from the whole vector (`personas_postflop.py:1220-1231`), pinned by `:7443`. Committed share of fold-legal decisions: nit 27.9 % / tag 57.0 % / lag 65.0 %.
>
> ### ⚠️ Silent coverage loss (not a blocker — worse, a blind spot)
>
> The entire **N-LOGIT G-gate family** (`:7085-7832`) stays green at every lever value **because
> every probe overwrites the lever**: `_nlogit_probe` sets `call_looseness = _NLOGIT_ANCHORS[persona]
> * mult` (`:6899`, `:6928`), so no shipped value is ever read. `_NLOGIT_ANCHORS`'s own comment
> ("each pack's authored anchor == its effective looseness") **becomes false the moment this slice
> ships, and nothing goes red.** This generalises rev-1 finding C-10 beyond G3.
> `grep -n "model_copy(update=" backend/tests/*.py` returns 41 hits; only those touching these three
> levers were read — **the same staleness idiom may exist elsewhere, unaudited.**
>
> ### Re-scoping the two tag pins — what it actually costs (§4 of the scan)
>
> - **H1 cannot be fixed by repointing at another shipped pack — that only MOVES the pin.** `maniac`
>   is the only pack with `call_looseness` unset, so a maniac-based control pins maniac's
>   `stickiness` instead. **Only a fully synthetic `PersonaPostflop` is pin-free.**
> - **The cascade nobody had mapped:** the authorship validator (`models.py:252-276`) makes
>   `stickiness` **required** while `size_elasticity` is unset, and **forbidden (absent, not null)**
>   once both split levers are authored. So authoring `size_elasticity` on tag to escape H1 *forces
>   deleting* `stickiness` — which makes the elasticity test's `s ** (-DAMP)` (`:1329`) raise on
>   `None`. **Re-scoping that test is a PREREQUISITE of authoring `size_elasticity`, not an
>   alternative to it.** And `stickiness` sets the price exponent (`personas_postflop.py:638-655`)
>   that H4, H6 and H8 all read — so moving `stickiness` to escape H1 breaks the price tests instead.
> - H2's four floats are independently covered by three other legs at the same node (`:6300`,
>   `:6278`, `:6284`); re-recording gives up only the exact-magnitude tripwire.
>
> ### What this scan would still not bet on
>
> 1. **Per-persona attribution of H4 and H5** — every arm but A moved all three levers at once; the
>    brackets are joint, not per-lever. Needs single-persona arms at the edges (~8 min each).
> 2. **H3's true feasible (nit, tag) surface** — shown non-constant, not mapped. Needs a 2-D grid.
> 3. **H5's upper bracket** — not bisected, and WTSD at n=4,000 has documented near-band fragility
>    (`:5729-5735`); establish any boundary at more than one seed.
> 4. **Zero-margin survivors** — `test_mw_funnel_belt.py:79` (floor exactly at the measured value)
>    and R4's budget were green in all six arms but have almost no headroom. Six arms is not a proof.
> 5. **Anything outside `backend/tests/`** — the frontend and the analytics/export contract checks
>    were not exercised.


> Contract scan 2026-08-03 (contract-mapper), code pin `b63dfaa`; docs cited at working tree.
> Builds on `contracts/n-vecfit.md` (harness/lever/pack layer — not re-derived) and
> `contracts/persona-realism-fit-loop.md` ("Multi-lever fitting — measured rules").

## 1. Blast radius of changing nit/tag/lag `call_looseness`

- Current values: nit 0.6/0.6, tag 0.6/0.6, lag 0.55/0.55 (`call_looseness`/`continue_ref`) —
  **at every one, `call_looseness == continue_ref` exactly** (load-bearing; see §8).
- **Population BANDS — HARD in CI** (`test_personas_postflop.py:5640-5749`,
  `test_persona_postflop_bands`, all personas, no skip except one named maniac WTSD case
  `:5711-5716`). Current: nit AF (0.6,2.4) FtC (0.10,0.90) WTSD (0.37,0.80) `:2569` ·
  tag AF (1.4,3.6) FtC (0.0,0.55) WTSD (0.41,0.65) `:2576` · lag AF (1.5,4.5) FtC (0.12,0.64)
  WTSD (0.37,0.59) `:2577`. A refit moves AF/FtC directly, WTSD indirectly → §2 tension.
- **Cross-persona ordering test** `test_fold_to_bet_persona_ordering_at_fixed_size` (`:790-826`):
  strict `lag < tag < nit` fold-rate at fixed ½-pot, computed off real packs. Already separates
  tag from nit today via OTHER levers despite identical `call_looseness`. A refit must not flip it.
  This is the existing pairwise-separation-gate precedent.
- **`_GOLDEN_STATS_N200`** (`:3449-3541`, asserted `:3545-3559`, abs=1e-9, all six personas,
  shared-table sim — ANY pack change moves EVERY row via rng displacement). Sanctioned re-pin
  protocol, 15+ documented "RE-RECORDED for <slice>" precedents incl. W3R-2 (a `call_looseness`
  edit, `:3365-3372`); attribution proven by revert per the `:3339` guard. NOT frozen.
- **`test_price_tail.py`:** `HEAD_VECTORS` (`:142-166`) pins ONLY station + fish — **nit/tag/lag
  are not among the 23 frozen vectors**. Other tests there are structural (interior/monotone/
  inert), value-safe. Station/fish packs must stay untouched.
- **node_trace pins:** two exact nit pins (`test_node_trace.py:69-98` 0.4783/0.3548; `:101-133`
  >0.30) — both on the unopened branch, which `looseness` cannot reach (∂CBet/∂ln cl = 0). Safe
  in principle; fit-loop step 5 still requires the post-fit node-trace run as confirmation.
- **G9** `test_nlogit_g9_a_looseness_refit_does_not_move_the_reference` (`:7761-7796`): asserts
  shipped `continue_ref` == anchors (0.6/0.6/0.55) and unchanged under an in-memory ×1.5 refit.
  Compatible with the slice BY CONSTRUCTION — it never reads shipped `call_looseness`.
  Constraint enforced: **only `call_looseness` may change; `continue_ref` frozen.**
- Estimator-parity tests (`test_range_estimate.py`): zero `call_looseness` hits — not load-bearing.

## 2. The D11/BANDS tension — UNRESOLVED BY THE ROADMAP (sharpest open question)

D11: bands re-anchor ONCE at W4-b, never mid-spine; the bands are HARD in CI today. The roadmap
sequences R9-LOOSEFIT BEFORE W4-b but never says whether the fit target must sit inside the
current bands. If separating nit from tag requires leaving band → suite red, slice unmergeable.
Options: (a) constrain the fit inside current BANDS (solution space may be tight/empty);
(b) re-sequence so the fit's landing waits for W4-b's re-anchor. Structurally similar to the
R9-DEFENCE/R9-CBET "design question, not ticket" pattern. **Needs an owner ruling before fitting.**

## 3. Fold-share / raise-share derivation

Existing counters in `_persona_stats` (`:2661-2707`): `bet_raise` (conflates BET and RAISE, both
legs), `call_count`, `folds_to_first_cbet`, `cbet_opportunities` (first-flop-bet only),
`saw_flop_hands`, `showdown_hands`. **No general facing-node fold-share or raise-share
(RAISE/(CALL+RAISE)) counter exists** — new counters needed (N-vecfit handoff item 1, this
slice's scope). `_persona_stats_ext.ftc_by_bucket` (`:2814`) is a size-stratified fold-share
variant but cbet-specific, no `context_aware` kwarg, no raise-share counterpart.

## 4. Committed-node no-reach

Roadmap `:1986-1991` (N-LOGIT ledger, verbatim): `_commit_transform` zeroes the fold merit on
SPR-committed nodes → the lever is inert there (was dominant at HEAD). "R9-LOOSEFIT therefore has
no reach over committed nodes, and must re-measure AF rather than assume the raise side is
inert." → the fit's target statistic must exclude or separately report the committed subset.

## 5. Re-grep verdict (independently re-confirmed)

All `call_looseness` hits across roadmap/tickets/specs are historical (W2-a, W3R-2, W3R-3 — the
origin of today's values), N-LOGIT mechanism text, N-vecfit (measurement-only), or the
R9-LOOSEFIT entry itself. **No other filed slice plans to change nit/tag/lag `call_looseness`.**

## 6. Separation-gate precedent

Fixed-size fold ordering `:790-826` (strict, HARD, includes `tag < nit`).
`test_persona_wtsd_ordering_invariants` (`:5751-5806`) **excludes nit** — a WTSD-based nit-vs-tag
gate would be net-new.

## 7. Pack edit surface

- nit.json: `call_looseness` `:11`, `continue_ref` `:12`; **no `_doc` version-comment array**
  (tag/lag have one) — a fit edit should add one to match convention.
- tag.json `_doc:11-16` / lag.json `_doc:12-17`, verbatim: continue_ref is "a FROZEN copy of
  today's effective `call_looseness`... NEVER re-sync it with `call_looseness` — that restores
  the old coupling and deletes the feature." G9 enforces mechanically.
- No other postflop field references the 0.6/0.55 values.

## 8. Posture + the rscale de-inertization (biggest surprise)

- `_persona_stats` still has NO `line_aware` passthrough (signature `:2634`) — N-vecfit handoff
  item 4, still open. W4-b-grade posture = `context_aware=True` AND `line_aware=True`.
- **This slice is the FIRST production move of `call_looseness` off its `continue_ref` anchor
  for nit/tag/lag.** Today `rscale = looseness/continue_ref = 1.0` exactly (N-LOGIT inert;
  "bit-identical" claims contingent on it). The moment the fit moves the lever, rscale ≠ 1.0 in
  production for the first time — the fit is NOT a clean single-lever move; it de-inertizes a
  dormant raise-scale coupling. `test_r9d_s4_composition_with_nlogit_commutes` (`:8446-8489`)
  exercises the mechanism off-anchor artificially, but production never ran it at fitted values.
  Consequence: **fresh Jacobians needed at off-anchor points** — the N-vecfit premise study
  measured tag AT the anchor (rscale=1.0), so its J is a base-point value, not the fit-region
  value.

## SURPRISES

1. price_tail frozen vectors are station/fish-only — lower risk for this slice than the blanket
   invariant suggests.
2. rscale de-inertization (§8) — flag in tickets; "just move one number" is false.
3. `_GOLDEN_STATS_N200` re-pin discipline fully precedented (W3R-2 did this exact field) —
   fixture churn is de-risked.
4. D11/BANDS tension unresolved by roadmap (§2) — design-pass question, possibly R9-DEFENCE-style.
5. WTSD ordering test excludes nit — any WTSD-based separation gate is net-new.
