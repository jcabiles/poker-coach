# W3R-3 — spr_commit ladder + finish the call_looseness split (#4, #12)

> **RE-SCOPE (owner, 2026-07-24):** #5 (ace-high call base) was DROPPED from this slice mid-build. A global
> `_CALL_BASE[ACE_HIGH] 0.40→0.22` cut HARD-STOPPED — naked ace-high is ~34.6% of the fish's flop range and W3R-2
> already parked the fish ON its α fold-ceiling, so any meaningful global cut folds the fish PAST the exploitability
> ceiling (un-fishlike). The real bug (H117 naked ace-high FLOATING A RAISE) is re-routed to a facing-a-raise-scoped
> damp in W3R-6. This slice ships #4 (spr_commit ladder) + #12 (call_looseness tidy) only. The #5 sections below are
> retained for the record but are NOT built here.

## (SUPERSEDED TITLE) W3R-3 — spr_commit ladder + ace-high call base + finish the call_looseness split (#4, #5, #12)

**Slice of:** `docs/ai-dlc/roadmap/persona-realism.md` → W3R (bot-review remediation). Adjustment-plan fixes **#4**
(spr_commit ladder), **#5** (ace-high call base), **#12** (roster-wide `call_looseness` tidy). From the 2026-07-24
hand-history review (H11/H76 fish commits too early; H117 naked ace-high floats raise-wars). NOT one of the owner's
two original flags (those were hyp-1 maniac / hyp-2 fish-station, shipped W3R-1/W3R-2) — this is reviewer-found.

## Goal (one line)
Stop the fish committing its stack EARLIER than the calling-station (backwards for a "scared" bot), stop naked
ace-high floating into raise-wars, and adopt the W2-a `call_looseness` split roster-wide as an explicit no-op tidy.

## Why (the gap / root cause — from the review)
1. **#4 spr_commit backwards:** fish `spr_commit 2.0` > station `1.5` — the fish reaches its pot-commitment
   threshold at a HIGHER SPR, i.e. commits EARLIER than the supposedly-stickier station. A scared passive fish
   should commit LATER, not sooner. Fix: fish `2.0 → 1.4` (below station's 1.5). Maniac `4.0 → 3.3` (the maniac
   over-commits deep; a mild pull). Both are FIT SEEDS — re-measure AF, keep every persona's AF/WTSD in band.
2. **#5 ace-high call base too high:** `_CALL_BASE[ACE_HIGH] = 0.40` (engine, `personas_postflop.py:256`) — naked
   ace-high (no pair, no draw) calls/floats at 0.40 base, propping up raise-war floats (H117). Mirror the A1
   precedent (`_CALL_BASE[AIR] 0.25 → 0.08`): `ACE_HIGH 0.40 → ≈0.22`. FIT SEED. **This is a GLOBAL constant** —
   it scales EVERY persona's ace-high call merit (`call_merit = (_CALL_BASE[bucket] + _DRAW_CALL_BONUS[draw]) *
   looseness`, line 708), so the blast radius is roster-wide, not one persona.
3. **#12 call_looseness not adopted roster-wide (low-value tidy):** only `passive_fish` (0.42) + `calling_station`
   (4.0) have explicit `call_looseness`; tag/nit/lag/maniac still inherit `stickiness`. Author explicit
   `call_looseness` on tag/nit/lag = **their current `stickiness` value** (tag 0.6, nit 0.6, lag 0.55) so behavior
   is BYTE-IDENTICAL — a pure documentation tidy, NOT a behavior target. (Roadmap wrote "tag≈0.55"; tag's
   stickiness is 0.6 — treat that as a slip and author 0.6 to keep #12 a true no-op. If a deliberate tag tightening
   is wanted, that's a separate behavior decision — out of scope here.) Maniac left inheriting (roadmap lists only
   tag/nit/lag).

## Scope / files to touch
- `content/personas/passive_fish.json` — `spr_commit 2.0 → 1.4`.
- `content/personas/maniac.json` — `spr_commit 4.0 → 3.3`.
- `content/personas/tag.json`, `nit.json`, `lag.json` — author explicit `call_looseness` = current `stickiness`.
- `backend/app/domain/personas_postflop.py` — `_CALL_BASE[ACE_HIGH] 0.40 → ≈0.22` (line 256). FIT SEED — the exact
  value is measured to keep AF in band + the ace-high-float test passing, not dropped in.
- `backend/tests/test_personas_postflop.py` — a NEW unit/spot test that naked ace-high folds (does not float) facing
  a raise on flop/turn (cite H117); re-record the seeded golden fixture if the base-table change moves it.
- Re-record any seeded fixtures the ace-high / spr_commit change moves (golden / coverage_baseline / limper belt),
  P1/P2a precedent — behavior IS intended to change for #4/#5.
- **NO merit-table structural change, no new lever, no new bucket.** `_CALL_BASE[ACE_HIGH]` is an existing
  fit-seed constant (A1 precedent for editing `_CALL_BASE`). `spr_commit`/`call_looseness` are existing levers.

## Pass/fail (HARD)
- **Commit order fixed:** fish `spr_commit` (1.4) < station `spr_commit` (1.5) — the fish no longer reaches
  commitment at a higher SPR than the station. A behavioral commit-order assertion if one is derivable; otherwise
  the dial-order + AF-in-band is the gate.
- **Naked ace-high stops floating:** the new spot test — ace-high (no pair/draw) facing a raise on flop/turn folds
  at a materially higher rate than at the old 0.40 base (H117). Exact normalized fold prob via the capture-weights
  path (no sampling noise), the `test_size_elasticity_steeper_*` style.
- **Every persona's AF + WTSD stays IN its existing band** (the ace-high constant is global). **HARD-STOP:** if
  lowering `_CALL_BASE[ACE_HIGH]` pushes any persona's AF/WTSD/fold-to-cbet band OUT of range, STOP and report — a
  further mid-spine band re-anchor is an owner decision (the W3R-2 exception was fish+station ONLY; §7 keeps every
  other persona frozen to W4-b).
- **#12 is byte-identical:** the tag/nit/lag `call_looseness` authoring re-records the seeded fixtures with ZERO
  behavioral drift (call_looseness == the previously-inherited stickiness). `call_looseness↑` monotonicity holds.
- `./scripts/verify.sh` green; `ruff check .` clean; `content/` JSON validates.

## Out of scope
No population band re-anchor beyond keeping personas IN their existing bands (any bust → owner STOP, NOT a
re-anchor) · no maniac opening-range change (that's the tracked Path-3 keystone follow-up) · no new mechanic / bucket
(#8/#9/#10 are W3R-5/6/7) · no grader touch (`spot_signature()` frozen) · #12 stays byte-identical (not a behavior
target) · fish/station `call_looseness` + `size_elasticity` from W3R-2 untouched.

## Invariants honored
Softmax law (`_CALL_BASE[ACE_HIGH]` is a fit-seed re-measured to target, never a cosmetic drop-in) · domain purity
(`personas_postflop.py` stays web/DB-free) · results freq+EV · `spot_signature()` frozen · `call_looseness` keeps
its W2-a direction · strategy-in-`content` for the per-persona dials (the ace-high base is a mechanics constant, not
per-persona identity, so it lives in code — consistent with `_CALL_BASE[AIR]`/A1) · frozen bands respected (in-band
or STOP).

## Verify-by
`./scripts/verify.sh` green; the new ace-high-float test passes; fish spr_commit < station; every persona's
AF/WTSD/ftc bands still pass (report the re-measured AF per persona); `ruff check .` clean; report the fitted
`_CALL_BASE[ACE_HIGH]` value + which fixtures moved + confirmation #12 is byte-identical.
