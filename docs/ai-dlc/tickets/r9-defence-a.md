# Tickets — R9-DEFENCE-a

```
status: approved        # Gate 2, owner, 2026-08-02 — explicit affirmative ("i approve the spec")
```

Spec `docs/ai-dlc/specs/r9-defence-a.md` **rev 2**. Base `origin/main` `8cc6c38`.
Criterion IDs (`S-1`…`S-6`, `P-1`…`P-9`) are the spec's §7 gates. Finding IDs (`R-n`) are the ledger's.

**One file = one owner.** `backend/tests/test_personas_postflop.py` is contended by T4 and T5, so those two
**serialize** — same owner, sequential, never concurrent.

## DAG

```
T1 (lever) ──► T2 (mechanism) ──┬──► T4 (node gates) ──► T5 (harness + paired run) ──┐
                                │                                                    ├──► T7 ──► T8
                                └──► T3 (estimator) ──► T6 (parity gates) ───────────┘
```

Parallel pairs: **T4∥T3**, **T5∥T6**. Everything else serializes.

---

### T1 — author the `line_sensitivity` lever
Add the bounded optional lever to `PersonaPostflop` and author it in all six packs per the §5 seed ladder.

- **Owns:** `backend/app/domain/content/models.py`, `content/personas/*.json` (six top-level packs — **not**
  `content/personas/ladders/*.json`).
- **Acceptance:** `line_sensitivity: float | None = Field(default=None, ge=0.0, le=2.0)`; an authorship
  validator keyed on `model_fields_set` rejecting explicit JSON `null` while **absence stays the legacy
  opt-out** (`_continue_ref_authorship` precedent); seeds nit 0.60 / tag 0.50 / lag 0.35 / passive_fish 0.35
  / maniac 0.20 / calling_station 0.10; version bump on every edited pack (`P-9`); `_doc` entries on the
  packs that already carry that convention.
- **Done:** `backend/.venv/bin/python -m pytest tests/test_content_packs.py -q > out.txt 2>&1; echo $?` → 0,
  read from the file.
- **Note:** `PersonaPostflop` has no `model_config`, so Pydantic's default `extra="ignore"` silently drops a
  typo'd key. Pre-existing gap, inherited — do not fix it here, but do not rely on it either.

### T2 — the mechanism
Scale the CALL and RAISE merits by `exp(−λ_p·line)` inside the facing-chips branch, before the single
normalization.

- **Owns:** `backend/app/domain/personas_postflop.py`. **Depends on:** T1.
- **Acceptance:** `_LINE_DELTA = 1.0` as a named module constant (§3.1 — **pinned, not inherited from
  `_POSITION_AGG_DELTA`**, `R-1`); helper applied **only** when `ActionType.FOLD in by_kind` (`R-7` — the
  region is common-path); scope predicate exactly
  `bucket ∈ {MIDDLE_PAIR, TOP_PAIR, ACE_HIGH, AIR} and draw is DrawCategory.NONE` (`R-6`); attach after the
  SPR/B5b block and before the N-LOGIT raise scale; **CALL and RAISE only — the FOLD merit is never
  touched** (`P-1`); runtime guard on the lever (`model_copy` bypasses validation); adds **no** rng call.
- **Comment block must state:** the fold-side projective equivalence and why C/R-only is prescribed anyway
  (`R-2`); that `_commit_transform` and B5b **cannot co-occur** with an in-scope cell, so the mechanism is
  scoped away from committed nodes rather than inert on them (`R-6`); the coded order relative to N-LOGIT.
- **Done:** `ruff check .` clean; `pytest tests/test_personas_postflop.py -q > out.txt 2>&1; echo $?` → 0.

### T2b — re-pin the two seeded-stream fixtures (added mid-build, owner-ruled 2026-08-02)
Re-pin the coverage baseline and the limper belt, which move by construction once bot behaviour changes.

- **Owns:** `backend/tests/test_coverage_baseline.py`, `backend/tests/test_limper_coverage_belt.py`.
  **Depends on:** T2. **Parallel with:** T3, T4 (disjoint files).
- **Why it exists:** `play.py` already derives and threads the barrel signal, so T2 genuinely changes live
  villain play → the shared seeded rng stream displaces → the deterministic hand stream drifts. Both files
  carry an explicit per-slice re-pin convention (11+ precedents). Spec §8 originally banned all re-records;
  that was corrected under the owner ruling.
- **Acceptance — follow the protocol those files define, not a bare re-record:**
  1. **ATTRIBUTION PROVEN, not assumed.** Revert *only* this slice's changed files at this tip and show both
     tests go green again — the method the `#160` entry used. Record it.
  2. Verify **every `_WANT_*` coverage shape still fires** (`>= 1`) — that is what distinguishes stream
     displacement from a real coverage regression. Report the fired counts.
  3. Append a dated `RE-RECORDED` / `RE-PINNED` note to each file's docstring in the established house
     style, stating cause, old → new numbers, and the ratio movement.
  4. Report the graded-coverage ratio move (27.70% → 26.01%) **as a flagged mapper-track dip owned by
     `T-cover`** — reported, never laundered.
- **Done:** both test modules pass; the full suite's only remaining failure is the pre-registered estimator
  pin that T3 fixes.
- **STOP condition:** if reverting this slice's files does **not** restore both tests, the cause is not this
  slice — stop and report rather than re-pinning.

### T3 — thread the signal into the villain-range estimator
Give the estimator's replay the current street's aggressor **seat**, and call the shipped derivation.

- **Owns:** `backend/app/domain/table/range_estimate.py`. **Depends on:** T2.
- **Acceptance:** `_Ctx` carries the derived flag; `_replay_contexts` tracks the current street's aggressor
  seat across street transitions; the flag is computed by calling **`aggressor_barrel_run`** over the
  replayed history — **re-deriving the run rule is forbidden** (`postflop_context.py:185-186` warns against
  a second taxonomy, `R-16`); `_postflop_action_dist` forwards it.
- **Done:** `pytest tests/test_range_estimate.py -q > out.txt 2>&1; echo $?` → 0.
- **Sizing note:** `PublicAction` already carries `street`/`position`/`action` — the three fields the
  derivation reads — so this is *reuse + one tracked value*, not new logic (`R-16`).

### T4 — node-grid gates
Build the S-gates and P-pins over the published cell grid.

- **Owns:** `backend/tests/test_personas_postflop.py`. **Depends on:** T2. **Blocks:** T5 (same file).
- **Acceptance:** publish the grid axes in-module (§7); `S-1` incl. the **literal** reference-node floor
  `ΔP(fold) ≥ 0.05` **not derived from `_LINE_DELTA`** (`R-1`); `S-2` anti-collapse at **both** anchor and
  tuned point with reported, floored skip counts (`R-3`); `S-3` restricted to strictly-positive-continue
  cells; `S-4` in **odds space**, ordering strict between tiers and equal within `{lag, passive_fish}`
  (`R-10`), a lever **sweep** incl. `model_copy`-injected values, and composition asserted at **relative
  `1e-12`, never bit-equality** (`R-8`) against the **production transform** (`R-12`); `P-1` structural, on
  **raw merits before normalization**; `P-2` out-of-scope byte-identity incl. non-facing nodes; `P-3` flop
  identity via the production derivation (`R-11`); `P-4`; `P-5` zero-continue inertness; `P-6`
  `test_price_tail.py` green **without edit**.
- **RED-FIRST:** every S-gate demonstrated failing at base `8cc6c38`; every P-pin demonstrated **green** at
  base (`R-5`). Capture both, unpiped, into the PR evidence file.
- **Done:** full-file pytest run → 0, read from a file.

### T5 — harness threading + the paired sensitivity run
Let the population harness see the signal without moving any pinned number, then measure the population
consequence.

- **Owns:** `backend/tests/test_personas_postflop.py`. **Depends on:** T4 (file contention — strictly after).
- **Acceptance:** the local `_postflop_decision` wrapper and `_play_hand` thread
  `aggressor_bet_prev_street`, derived via the shipped derivation, **defaulting off** so every existing band
  and golden statistic stays **byte-identical** (`P-7`); `S-5` paired run over **pre-generated immutable
  hand seeds from a dedicated deal RNG**, all non-line inputs identical across arms (`R-4` — the current
  single `random.Random(20260710)` both seeds hands and drives actions, so a naive same-seed pair diverges);
  numeric tolerances: showdown frequency falls ≥ 0.01 for nit/tag/lag/passive_fish, `|Δ| ≤ 0.005` for
  calling_station, maniac directional; a stated **occurrence floor** below which the comparison is not
  reported.
- **Done:** full-file pytest → 0; existing `BANDS` and goldens diffed and shown **unchanged**.
- **STOP condition:** if any pinned band exits, **escalate to W4-b** — do not widen, do not re-scope.

### T6 — estimator parity gates
Prove the reveal matches the live policy at a line-aware node, with the discriminators that catch a naive
implementation.

- **Owns:** `backend/tests/test_range_estimate.py`. **Depends on:** T3. **Parallel with:** T4, T5.
- **Acceptance:** `S-6` — a fixture node with `aggressor_barrel_run(...) >= 1`; the estimator's distribution
  there **differs** from the line-blind one; and four discriminators: same-seat true · **different-seat
  false in multiway** · broken consecutive line false · flop false (`R-9`).
- **PLUS: two existing tests in this file now fail BY CONSTRUCTION and both must be resolved here.** T3
  found the second one; it was not in the original ticket and must not be lost.
  1. `test_estimator_unchanged_by_the_barrel_run_signal` (~`:836`) — asserts the estimator equals the live
     sampler with the flag **both** True and False, which is only satisfiable while the kwarg is dead. Its
     own docstring pre-registered it as the red-first failure that proves the mechanic is wired.
     **Resolution: keep the fixture, split the assertion** — `estimator == live(flag=True)` **and**
     `estimator != live(flag=False)`. That is exactly S-6's "differs from the line-blind one".
  2. `test_estimator_river_dist_equals_live_polarized_policy` (~`:507`, fails at `~:548`) — was green at
     base. Its fixture is bet-flop / bet-turn / bet-river by the same seat, so the river node has `run == 2`,
     but its live reference call omits `aggressor_bet_prev_street` and so defaults False. Its **intent is
     unchanged and still correct**; only its reference call is no longer production-faithful.
     **Resolution: one line** — pass `aggressor_bet_prev_street=ctx.aggressor_bet_prev_street` to the live
     reference call, exactly as it already threads `latest_aggressor_contribution_bb`. Its second,
     discriminating assertion (`estimator != streetless.dist`) is unaffected.
  **Neither may be deleted or weakened.** If either resolution does not restore green, that is a signal the
  replay has a real defect — stop and report rather than adjusting the test.
- **Done:** `pytest tests/test_range_estimate.py -q > out.txt 2>&1; echo $?` → 0.

### T7 — counterfactual mutants + coverage delta
Prove the harness catches every way this could be wrong.

- **Owns:** scratch only (no repo file). **Depends on:** T4, T5, T6.
- **Acceptance:** six mutants, each run against the full harness and each shown to FAIL where the spec says:
  (a) `line_mult = 1.0` forced; (b) `_LINE_DELTA = 1e-12`; (c) `call_merit`-only; (d) `C' = R' = 0`
  collapse; (e) a fold-side implementation — **must pass every behavioural gate and be caught by `P-1`
  alone**; (f) scaling every bucket regardless of scope — caught by `P-2`. Coverage delta reported against
  the immutable snapshot (`P-8`).
- **Done:** a results table in the PR body. **A harness that passes (a)–(d) or (f), or that catches (e)
  anywhere but P-1, is broken — fix the harness, not the mutant.**

### T8 — fan-in review, ledger, roadmap
Adjudicate the review and record the outcome.

- **Owns:** `docs/ai-dlc/ledger/r9-defence-a.md`, `docs/ai-dlc/roadmap/persona-realism.md`.
  **Depends on:** T7.
- **Acceptance:** fresh `refuter` + `persona-realism-theory-reviewer` + Codex Sol, all **GIT-READ-ONLY** and
  all **pinned to base explicitly** (`S-0.1` — a scan in this slice mapped a stale tree and reported the
  prerequisite missing); every central claim **reproduced against the code** before accept or reject; every
  accept **and** reject recorded with reasoning; roadmap entry updated to the shipped shape; the design
  pass's §8 risk 1 marked stale (`R9-SIGNAL` closed it).
- **Done:** ledger contains one entry per finding with an adjudicated status.

---

## Deferred, pre-registered — do NOT build here

`R9-DEFENCE-b` (stage-2 raise-share line term; `g(run) = min(run,2)` river third barrel) · draw-class
response (v2, needs joint calibration) · `OVERPAIR_TPTK` (behind W3R-7's bucket split) · the jam
discriminator (`min_bb == max_bb`, its own plumbing slice) · fixing the `extra="ignore"` typo gap.
