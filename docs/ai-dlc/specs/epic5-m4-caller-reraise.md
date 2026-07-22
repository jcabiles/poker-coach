# Spec — M4: Caller-re-raises-c-bet grader (RES-H H1)

**Wave 1** (parallel with M5). Branch: `feat/epic5-m4-m5` off `main`.

## Goal
Grade hero's response (fold/call/raise) when hero opened, c-bet a canonical flop, and a **non-BB
preflop cold-caller raises** the c-bet. Most reachable uncovered postflop node (measured
16.8/1000, RES-H §1.3). Spike LAW: `RES-H-mw-extension.md` §3 (design) + §5-H1 (pass/fail).

## Files / interfaces
- `backend/app/domain/postflop.py` — **append** (do not modify existing bodies):
  - `_merits_vs_caller_raise(value, adv, price, texture, cat) -> (fold, call, raise_)` — sibling of
    `_merits_vs_check_raise` (:945) with the §3.2 asymmetry baked in: **higher fold baseline**
    (check-raise uses 1.6; cold-caller raise is more value-weighted → **≥ 1.9**, RES-H §3.1/§3.2),
    **smaller `bluffy` credit** (cold-caller raises are rarely bluffs), value/draw still continue.
  - `grade_vs_caller_raise(spot, hero_range, villain_range, decision) -> EvaluationResult` — clone
    of `grade_vs_check_raise` (:1023) structure: flop-only, `range_advantage` with the caller's pos
    as 3rd arg (NOT hero's), RAISE eval keys on `max()` big leg, composes `_apply_multiway` on the
    facing side under `if is_multiway(spot)`, freq+EV over {fold,call,raise} + `sizing_correctness`,
    `is_mixed`. **MUST NOT import or call `_calibrate_catcher_fold`** (§3.4 — α not applied).
- `backend/app/domain/table/grade_map_postflop.py` — **append** `map_flop_vs_caller_raise(state,
  hero_seat) -> Spot | None`: SRP, hero=opener, hero's flop bet canonical (`_is_canonical_bet`),
  a **non-BB** preflop caller then raised, hero faces/closes. Caller range via existing `VS_RFI`
  content gate (`_srp_ranges`/`_mw_ranges`). Degrade-to-2-live when other callers folded. Reuse the
  `_faced_bet_spot` raise-leg machinery (N4b) for the faced raise size + RES-E bucket.
  **New preflop gate helper (refuter LOW — do NOT reach for `_hu_srp_preflop`):** this node is a
  3-way SRP entrant shape (opener + non-BB caller [+ maybe BB]), so the gate is structurally closer
  to `_mw_srp_preflop` (:671) than to `_hu_srp_preflop` (:185, strict 2-live — would reject every
  arrival). The distinguishing move: the non-BB caller's FLOP action is a **RAISE**, not a call.
  Add a named `_flop_caller_raise_preflop` gate rather than overloading either existing helper.
- `backend/app/domain/table/grade_map.py` — dispatcher: +import, + one chain entry on the FLOP
  branch (after `map_flop_vs_check_raise`).
- `NodeContext.VS_CALLER_RAISE` + `LeakCategory` value — **additive** enum members.
- Tests: new `tests/domain/test_grade_map_caller_raise.py` (own file).

## Out of scope
Turn/river caller-raise (flop only v1). Donk-raise, limped-pot raise, delayed-c-bet, hero-not-opener
(all → `None`). Hero OFFERED sizing stays 2-button. No new content pack. 4-way scalar work (that's M6).

## Constraints (invariants)
- `spot_signature()`/`_postflop_signature()` byte-identical for existing nodes; `TAXONOMY_VERSION`
  bumped only if the node taxonomy genuinely gains the family (prefer not). `test_signature.py` zero diff.
- α is a CEILING, NOT applied to raise-response (§3.4) — no `_calibrate_catcher_fold`.
- Reuse `RECOGNIZED_BET_FRACS`/`_is_canonical_bet` (M1); newly faced raise size → defined RES-E bucket.
- Domain purity; freq+EV never boolean; EVs approximate; `_apply_multiway` composes MW facing side.

## Verify-by (RES-H §5-H1 verbatim)
1. Mapper **fires** non-zero, in-band (≥~5/1000; sim shows 16.8) in a seeded bot belt-test — assert
   non-zero + in-band, not an exact count.
2. `grade_vs_caller_raise` returns freq+EV over {fold,call,raise} + `sizing_correctness`; never boolean; `is_mixed` correct.
3. **Range-asymmetry test:** fixed marginal `weak_made` + texture + faced size → caller-raise FOLD
   freq **strictly ≥** `grade_vs_check_raise`'s; a `strong` hand still favors continue in both.
4. **α-not-applied test:** grader does not call `_calibrate_catcher_fold` (grep/unit) — a marginal
   hand may fold ABOVE the α ceiling for the faced size.
5. `_apply_multiway` composes when the mapped spot is still multiway (facing-side path).
6. HU/3-way existing grader outputs byte-identical (hash-pins); `verify.sh` + FE build green;
   refuter-on-diff + Codex Sol PASS.
7. Every off-shape line (donk-raise, limped, delayed-cbet, hero-not-opener) returns `None`.
