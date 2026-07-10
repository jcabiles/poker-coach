# Delta spec — Simulate S5: turn/river routing seams + residual hazard closure

> Slice S5 of `docs/ai-dlc/roadmap/simulate-table.md`. Contract delta (at-HEAD, supersedes
> the stale map): `docs/ai-dlc/contracts/simulate-s5.md`. Interview skipped — genuinely
> narrow, all decisions pinned by the roadmap slice + fresh scan; **NO behavior change** is
> the governing constraint.

**Goal (one line):** lock today's turn/river behavior in golden tests (including the repo's
first pinned-hash signature test), harden the gate-shielded truncation sites so they fail
loud instead of silently mis-grading, and open the street-dispatch seam S6/S7 plug into —
all with zero observable behavior change.

## Why this shape (scan findings, condensed)

Commit `53c865c` already fixed the headline hazards (street gate → `NOT_FOUND`, current-street
`faced_bet_bucket`, made-hand ordering). What remains: 9 latent `board[:3]` truncation sites
shielded only by the gate; `test_signature.py` has **zero pinned-hash assertions** (a tuple
reshape that orphans all persisted SM-2 rows would pass the suite) and zero turn/river
fixtures; the dispatch is a binary street ternary. `range_advantage`'s dead param and
`_rebuild_postflop` branches are **S6/S7's**, not S5's.

## Changes (exact)

1. **Pinned-hash golden test (FIRST, highest value).** In `tests/test_signature.py`: assert
   `spot_signature(<canonical flop cbet fixture>)` equals a **literal hash string** (computed
   once at authoring, hardcoded). Any future tuple reorder/insert now fails loudly instead of
   silently orphaning SRS history. Add a second pin for a preflop spot (byte-locked branch).
2. **Turn/river signature fixtures.** New tests: a TURN copy of the flop fixture hashes
   differently than the FLOP one (street at tuple index 2 does its job); construction uses
   `model_copy(update=...)` like `test_provider.py:146` — the fixtures must NOT be run
   through the graders (`grade_cbet`/`grade_vs_cbet`/`grade_vs_check_raise`). (`classify()`
   is unavoidably and correctly invoked by `spot_signature()` itself — that's fine.)
3. **Loud guards on the shielded graders.** `grade_cbet` / `grade_vs_cbet` /
   `grade_vs_check_raise` (`domain/postflop.py:332,530,704`): replace silent
   `board = spot.board[:3]` with a street guard —
   `if spot.street != Street.FLOP: raise ValueError("flop-only grader")` — then slice.
   Unreachable today (the `supports()` gate precedes them; 3 provider tests prove it), so no
   behavior change; the moment S6 lifts the gate wrongly, it's a crash not a wrong grade.
   Leave `texture.classify()` (documented flop-only) and `drill.py:137,142,311` untouched
   (flop-only call paths, verified).
   ⚠️ **Honest exception (refuter-verified LIVE gap, deliberately NOT fixed here):**
   `services/review.py:30` and `srs.py:115` are reachable TODAY — `POST /drill/grade` with a
   client-supplied TURN/RIVER spot returns `NOT_FOUND` from the provider (gate works) but
   `grade_drill` calls `spot_signature()` + `record_attempt()` UNCONDITIONALLY (no coverage
   check, `drill.py:238-256`), persisting a truncated-texture SRS row. The app's FE cannot
   construct such a request, and gating `record_attempt` on coverage is a behavior change —
   out of S5's zero-behavior-change scope. **Assigned to S6** (which makes turn spots
   first-class and must decide the coverage-gating rule); documented here so the roadmap's
   "audit findings fixed or explicitly cleared" bar is met with an accurate reason.
4. **Dispatch seam.** `CompositeProvider._route()` (`composite.py:42-43`): binary ternary →
   a street-keyed mapping built in `__init__`
   (`{PREFLOP: preflop, FLOP: postflop, TURN: postflop, RIVER: postflop}`), same resolution
   for every input as today. S6/S7 later swap TURN/RIVER values without touching `_route`.
   Constructor signature unchanged.
5. **Append-rule documentation.** Docstring on `_postflop_signature()` (`srs.py`): field
   order is a persisted-data contract; new dims append AFTER `faced_bet_bucket` and must be
   constant for existing flop spots; pinned-hash test is the tripwire.

## Files

`backend/app/domain/providers/composite.py` · `backend/app/domain/postflop.py` (3 guard
lines) · `backend/app/domain/srs.py` (docstring only) · `backend/tests/test_signature.py`.
Single ticket, one heavy-worker.

## Out of scope (S5 no-gos)

No new grading logic, no turn/river graders (S6/S7) · no `range_advantage` rewrite (S6) · no
`_rebuild_postflop` changes (S6/S7) · no `spot_signature()` tuple changes of ANY kind — the
preflop branch is byte-locked and the postflop tuple must hash identically before/after this
slice (the new pin test proves it) · no provider interface changes · no content/FE/DB.

## Verify-by

Full `pytest -q` green with zero test modifications outside `test_signature.py` (the 3
provider NOT_FOUND tests at `test_provider.py:146,163,180` pass UNCHANGED — executable proof
of no behavior change); new pin tests + turn/river fixture tests green; a deliberate local
tuple reorder (not committed) flips the pin test red (author verifies once, notes in PR);
`./scripts/verify.sh` → `BACKEND VERIFY OK`; ruff clean.
