# Contract delta — S5 turn/river routing seams (re-verified at HEAD, 2026-07-10)

> Supersedes `postflop-turn-river.md` for S5 scoping (that doc predates commit 53c865c).
> Read-only scan by contract-mapper. Full evidence retained below in condensed form.

## FIXED at HEAD — do not re-litigate

1. **Street gate:** `providers/postflop.py:21-26` — `supports()` requires `street == Street.FLOP`;
   a TURN/RIVER spot traces through `CompositeProvider._route()` (`composite.py:42-43`) →
   `supports()` False → `_not_found()` → `Coverage.NOT_FOUND`. Graders never reached; no
   truncation-grading bug live. Pinned by 3 tests in `tests/test_provider.py:146,163,180`.
2. **`faced_bet_bucket()`** (`srs.py:90-104`) — reads current decision point from
   `legal_actions` + street-filtered prior; whole-history scan is gone.
3. **`_hand_category()`** (`postflop.py:148-202`) — made straight/flush returned before draw
   flags, invariant documented in comments 159-162.

## STILL LIVE

4. **9 latent `board[:3]` truncation sites** — most shielded by the street gate, but
   **⚠️ CORRECTION (refuter 2026-07-10): `srs.py:115` + `services/review.py:30` are LIVE, not
   shielded.** `POST /drill/grade` with a client-supplied TURN/RIVER spot returns `NOT_FOUND`
   from the provider, yet `grade_drill` calls `spot_signature()` + `record_attempt()`
   unconditionally (no coverage check, `drill.py:238-256`) — silently persisting a
   truncated-texture SRS row today. The FE can't construct such a request; the fix
   (coverage-gating rule) is assigned to S6. Shielded/flop-only: `texture.py:37` (documented
   flop-only) · `postflop.py:332,530,704` (three graders — S5 adds loud street guards) ·
   `api/v1/drill.py:137,142,311` (flop-only call paths, verified).
5. **`range_advantage()` dead `node_context` param** (`postflop.py:103-133`) — bound, never
   read. Callers: `grade_cbet:334-335`, `grade_vs_check_raise:706-710`. (`grade_vs_cbet`
   uses the separate `range_advantage_defender`, no dead param.) Behavior-neutral to leave
   for S5; hazard only if S6 assumes tagging a new context changes output.
6. **`_rebuild_postflop()`** (`drill.py:92-148`) handles exactly `_POSTFLOP_CTX =
   (CBET, VS_CBET, VS_CHECK_RAISE)` (line 89 — currently the full postflop enum). Unknown
   context → `return None` → caller `_next_review()` (151-171) **skips that row and tries the
   next due row**; random fallback only when the whole queue exhausts. Correction vs the old
   map: per-row degradation, not immediate random fallback. Any new NodeContext without a
   matching branch silently skips those due rows.

## Golden-test baseline

7. **`_postflop_signature()` tuple** (`srs.py:107-128`), order:
   `[variant, format, street.value, ctx, hero.position, facing, tex, spr_bucket, faced_bet_bucket]`.
   Street at index 2 (turn vs flop already hash differently). `faced_bet_bucket` is LAST —
   the append point. Preflop short-circuits first (`srs.py:48-50`); flop/turn/river all flow
   through `_postflop_signature` today.
8. **`test_signature.py` = fixture-PAIR comparisons only — zero pinned hash literals.** A
   tuple change that reshapes every existing flop hash would NOT be caught. **S5 must add a
   fixed-hash pin test for at least one canonical flop spot** before touching anything near
   the tuple. Zero turn/river fixtures exist in the file — new coverage, not extension.
9. **Dispatch seam today:** binary `street == PREFLOP ? preflop : postflop`
   (`composite.py:42-43`); sub-providers constructor-injected, duck-typed
   `supports/optimal/evaluate` protocol (no ABC). Adding street providers = widen `_route()`
   + `__init__` — no interface change.
10. **Zero turn/river production code** — only the 4 test-side `model_copy` overrides
    (`test_provider.py`, `test_feedback_tiers.py:161`). No builders, no samplers, no
    NodeContext variants, no leak categories.

## Hazards for S5's no-behavior-change constraint

- Keep the 3 provider tests green — they are the executable spec of NOT_FOUND behavior.
- Signature tuple = highest-severity landmine (silent SM-2 orphaning; add the pin test FIRST).
- A real turn/river fixture built for golden tests must not be run through the 9 shielded
  truncation sites without explicit audit — else the golden test pins wrong behavior.
