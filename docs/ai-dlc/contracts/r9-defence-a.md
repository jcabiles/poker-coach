# Contract map — R9-DEFENCE-a

**Base:** `origin/main` `8cc6c38`. All line numbers below verified against that commit.

> ⚠️ **Provenance note.** The `contract-mapper` scan of 2026-08-02 read the **shared working tree**, whose
> local `main` branch sat at `61efc42` — five commits behind `origin/main`. It therefore reported
> "N-LOGIT is not present in this checkout", which is **false at base**, and every line number it returned
> was against stale files. Its substantive findings survived re-verification and are kept below; its
> headline and its numbering did not. **Lesson for future scans: pin the sub-agent to a worktree at a named
> commit, or it will silently map whatever the shared tree happens to be pointing at.**

## 1. The seam

| What | Where (`backend/app/domain/personas_postflop.py` @ `8cc6c38`) |
|---|---|
| Facing-chips branch opens | `if ActionType.FOLD in by_kind` — the facing test used throughout |
| Fold / call / raise merit assembly | ends before the SPR block |
| SPR value-commit decision | `:985-995` (`value_commit` → `_commit_transform(entries)` at `:995`) |
| `_commit_transform` definition | `:684` — **zeroes the FOLD merit** while FOLD stays legal |
| B5b draw damp (subtracts absolute quantities) | `:996-1007` |
| **Proposed R9 attach point** | **after `:1007`, before `:1059`** |
| N-LOGIT raise scale (`rscale = looseness / continue_ref`) | `:1059-1068`, guarded by a range check hoisted above the facing test |
| **The single normalization** | `:1070-1076` — `max(m, 0.0)` clamp, sum, zero-total fallback |
| **First `rng.choices` — the ACTION draw** | `:1076` |
| Second `rng.choices` — the SIZING draw | `:1082`, reached only when action ∈ {BET, RAISE} |

**Ordering contract:** nothing between the facing branch and `:1076` consumes rng — the whole
assemble → commit → scale → normalize pipeline is deterministic given inputs. A pure merit multiplier
inserted at the attach point preserves "action draw is the first rng consumer" by construction. Eight
capture-rng consumers depend on that ordering.

**No-reach contract:** where `_commit_transform` fires, `F = 0.0` exactly, so `P(fold) = 0` for any defend
mass. Both N-LOGIT and R9-DEFENCE-a are arithmetically inert there, for the same reason.

## 2. Composition with N-LOGIT — commutes

Final entries with both live: `(F, C·line_mult, R·rscale·line_mult)`. `line_mult` cancels out of
`P(raise|continue)`; `rscale` cancels out of nothing R9 asserts. Both are scalar multiplies on entries
before one normalization, so **coded order cannot change the result**. Verified algebraically (§3.3 of the
spec); must still be *gated*, because a future edit could move one of them across the normalization.

## 3. The signal — already shipped, do not rebuild

| What | Where |
|---|---|
| `aggressor_barrel_run(...)` | `table/postflop_context.py:152-200` |
| Postflop-only guard | `_POSTFLOP_ORDER` `:149`; preflop early-return `:188` |
| Consecutive-run loop (not cumulative) | `:191-200` |
| Sampler kwarg (flat, not a context field) | `personas_postflop.py:732` — `aggressor_bet_prev_street: bool = False` |
| Docstring recording "read by nobody" | `personas_postflop.py:753` |
| Production derivation + threading | `table/play.py` |

**All three amendments the design pass demanded are already in.** Design-pass §8 risk 1 is **closed** —
mark that section stale.

`line = 0` on the flop is structural: the run-length loop iterates over postflop streets *preceding* the
current one, which is empty on the flop.

## 4. Integration points

- **Callers of `sample_postflop_decision`:** `table/play.py` (production — already threads the signal);
  `table/range_estimate.py:345` (`_postflop_action_dist` — **does not** thread it); ~21 direct call sites in
  `tests/test_personas_postflop.py`; `tests/node_trace.py`; `tests/test_price_tail.py`;
  `tests/test_arrival_range_ftc.py`; `tests/test_mw_catch_toppair.py`; `tests/test_bet_sizing.py`. All
  test callers default the flag to `False`.
- **Estimator gap (confirmed at base):** `aggressor_bet_prev_street` appears in `personas_postflop.py`,
  `play.py`, and `tests/test_range_estimate.py` — **not** in `range_estimate.py`. `_Ctx` (`:92`) and
  `_replay_contexts` (`:138-252`) track `street_aggr` **within the current street only**, reset at every
  street transition (`:153`, `:175`). There is no cross-street per-seat aggressor history to pass through:
  closing this is **new logic**, not a thread-through. The design pass under-budgeted it.
- **Pack model consumers:** `personas.py` `load_persona_packs` validates every `content/personas/*.json`
  via `PersonaPack.model_validate_json`. An additive optional field is safe. Note `PersonaPostflop` has no
  `model_config` override, so Pydantic's default `extra="ignore"` applies — **a typo'd pack key is silently
  dropped**. Pre-existing repo-wide gap, inherited, not created here.
- **Lever precedent:** `position_sensitivity` at `content/models.py:230` with `_POSITION_AGG_DELTA = 0.25`
  at `personas_postflop.py:706` and its use at `:710-713` — the exact mechanic/identity split
  `line_sensitivity` should mirror.

## 5. Fixtures and bands at risk

| Fixture | Location | Exposure | Status |
|---|---|---|---|
| Balanced-villain α fixture | `tests/test_personas_postflop.py` (~`:600-668`) | none — passes no `street`, no context | HARD, protected by construction |
| Frozen price vectors (`HEAD_VECTORS`, 23 exact-equality) | `tests/test_price_tail.py:142`, asserted `:281+` | none — `street=FLOP` explicit | HARD, doubly protected (default-off **and** flop-scoped). **Do not edit this file.** |
| `BANDS` (AF / fold-to-cbet / WTSD per persona) | `tests/test_personas_postflop.py:~2432-2471`; station WTSD band `(0.66, 0.72)` derived at `:2424` | **none today** — the harness's own `_postflop_decision` wrapper (`:1914`) has no `aggressor_bet_prev_street` param in **either** `context_aware` state | ⚠️ The reason criterion 8 would be unfalsifiable. Spec §6.1 addresses it. |
| Fold-to-first-c-bet | `tests/test_personas_postflop.py:~2556-2571` | flop-only by construction (`if street != "flop": continue`) | HARD, protected by construction |
| Golden byte-identical persona stats | `tests/test_personas_postflop.py:~3396+` | same harness path, same non-exposure | Must stay byte-identical — spec §6.1 keeps the default path unchanged |
| WTSD ordering invariants | `tests/test_personas_postflop.py:~5586-5641` | same harness path | Same |

## 6. Assumptions in the design pass that are NOT true at base

1. **"Keep N-logit first"** — already satisfied; N-LOGIT is merged (#163 + #164). The dependency is
   discharged, not pending.
2. **Design §8 risk 1 ("the R9-SIGNAL preflop trap is live")** — **closed**. All three amendments shipped
   in #141. Mark stale.
3. **"New tests only, no band edits"** (design §7) — under-states the work. The population harness cannot
   observe the mechanism at all; making criterion 8 checkable requires extending the harness wrapper and
   `_play_hand`'s derivation. Resolved by spec §6.1: extend the harness, keep the default path
   byte-identical, add a paired sensitivity run.
4. **`range_estimate.py` "needs only a per-seat aggressor-seat set"** (design §7 item 6) — under-states it.
   See §4 above. Resolved by spec §6.2: in scope, budgeted as new logic.
5. **Design-pass line numbers** are against pinned commit `803e9dc`; `main` has moved far since (N-LOGIT
   alone rewrote the seam). Re-derive every anchor from base rather than copying the report's numbers.
