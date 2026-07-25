# W3R-4 — Shared-code base/ordering fixes (#7, #11) — #14 SPLIT OUT

**Slice of:** `docs/ai-dlc/roadmap/persona-realism.md` → W3R (bot-review remediation). Fixes **#7** (multiway
busted-river-bluff over-fire) + **#11** (`_CALL_BASE[MIDDLE_PAIR]` trim). From the 2026-07-24 hand-history review
(TAG H41 busted-flush bluff into 3 callers). Reviewer-found (NOT an owner flag).

> **SCOPE (owner, 2026-07-24):** the roadmap bundled #7/#11/#14. **#14 (shared-board false "two pair" force-commit)
> is SPLIT OUT** into its own slice — it edits the `_made_bucket` strength-taxonomy hotspot (delicate "F7 bug 1"
> logic already lives there) next to a "don't demote genuine two pair" no-go, and is taxonomy-adjacent to W3R-7.
> W3R-4 ships ONLY the two small, contained fixes below. No `_made_bucket` edit here.

## Goal (one line)
Stop multiway busted-river-bluffs over-firing (the busted add-on currently escapes the multiway damp), and trim the
middle-pair call base one notch — two small, contained shared-mechanics fixes with no taxonomy change.

## Why (the gap / root cause)
1. **#7 multiway busted-bluff over-fire:** `bluff_mass` gets the multiway decay `multiway_bluff_damp ** max(opp-1,0)`
   at `personas_postflop.py:650`, but the river busted-draw story bluff is ADDED AFTER that (line 675:
   `bluff_mass += _BUSTED_RIVER_BLUFF.get(context.busted_draw, 0.0)`), so it is NOT damped for extra opponents — a
   busted flush fires the same story-bluff into 3 callers as heads-up (TAG H41). Fix: scale the busted add-on by the
   SAME multiway factor. It must still SURVIVE the street decay (`_STREET_AGG_MULT`, line 673) — that's the busted
   bluff's whole point (a coherent river barrel) — so apply ONLY the multiway factor, not the street mult.
2. **#11 middle-pair call base slightly high:** `_CALL_BASE[MIDDLE_PAIR] = 0.60` (`personas_postflop.py:266`) — a mild
   over-call on marginal middle pair. Trim `0.60 → ≈0.52` (mild, mirrors the A1-style base trims). FIT SEED —
   re-measure AF, keep every persona in band.

## Scope / files to touch
- `backend/app/domain/personas_postflop.py` — (a) line 675: scale `_BUSTED_RIVER_BLUFF` add-on by
  `pf.multiway_bluff_damp ** max(opponents - 1, 0)`; (b) line 266: `_CALL_BASE[MIDDLE_PAIR] 0.60 → ≈0.52`. NO other
  engine edit. NO `_made_bucket` change (that's #14, split out).
- `backend/tests/test_personas_postflop.py` — a NEW test that the busted-river-bluff mass DECAYS with added opponents
  (heads-up fires more than 3-way), exact capture-weights where feasible; re-record the seeded golden if #11 moves it.
- Re-record the seeded fixtures the #11 (and any #7-visible) change moves (golden / coverage_baseline / limper belt),
  P1/P2a precedent.
- **NO new lever, no new bucket, no taxonomy/`_made_bucket` change, grader frozen.**

## Pass/fail (HARD)
- **#7 multiway decay:** the river busted-draw bluff mass at N opponents is `_BUSTED_RIVER_BLUFF[kind] ×
  multiway_bluff_damp ** (N-1)` — a new test proves it strictly decreases from heads-up to 3-way for a persona with
  `multiway_bluff_damp < 1`. Heads-up (opponents=1) stays BYTE-IDENTICAL (factor `**0 = 1.0`).
- **#7 street survival preserved:** the busted bluff still survives `_STREET_AGG_MULT[RIVER]` (it is added after the
  street decay) — do NOT regress the W3-c busted-barrel behavior; the existing busted-bluff tests stay green.
- **#11 trim:** `_CALL_BASE[MIDDLE_PAIR]` lowered; naked middle pair calls marginally less. **Every persona's
  AF/WTSD/fold-to-cbet band stays IN its existing frozen band** (no re-anchor). **HARD-STOP:** if the trim busts any
  band, STOP and report — a further re-anchor is an owner decision (§7; the W3R-2 exception was fish+station ONLY).
- `./scripts/verify.sh` green; `ruff check .` clean; `content/` JSON validates.

## Out of scope
#14 (shared-board commit inflation — its own slice) · no population band re-anchor beyond staying in-band (bust →
owner STOP) · no `_made_bucket`/taxonomy edit · no new mechanic (#8/#9/#10 are W3R-5/6/7) · no grader touch
(`spot_signature()` frozen) · fish/station/maniac dials from W3R-1/2/3 untouched.

## Invariants honored
Softmax law (`_CALL_BASE[MIDDLE_PAIR]` is a fit-seed re-measured, not cosmetic; the #7 fix is a correctness fix to
an existing multiway law, not a new lever) · domain purity · results freq+EV · `spot_signature()` frozen ·
action draw stays the FIRST `rng.choices` (the #7 fix touches `bluff_mass` BEFORE the action draw, same as today) ·
anti-sizing-tell untouched · frozen bands respected (in-band or STOP) · heads-up byte-identity for #7.

## Verify-by
`./scripts/verify.sh` green; the new multiway-busted-decay test passes; heads-up busted bluff byte-identical; every
persona's AF/WTSD/ftc band still passes (report re-measured AF); `ruff check .` clean; report the fitted
`_CALL_BASE[MIDDLE_PAIR]` + which fixtures moved.
