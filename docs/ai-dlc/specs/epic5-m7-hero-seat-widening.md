# Spec — M7: Hero-seat widening (RES-I L5) — go/no-go = GO

**Wave 3** (after M6). Branch: `feat/epic5-m7` stacked off the M6 tip. Spike LAW:
`RES-I-mw-funnel.md` §4 (L5) + §5 (blast radius). **Go/no-go already decided GO** — M1's 30k
re-measure left graded-MW at 0.23–2.73/1000, below the ≥5/1000 threshold, so the widening is
warranted (RES-I §6; roadmap RUN-PAUSED note).

## Goal
Widen the multiway grading family beyond hero-as-BB to hero as **opener** and **cold-caller** inside
MW-shaped pots — currently unmapped decision points (RES-I §4, measured ceiling **6–11/1000** for a
tag proxy). This is the only path that lifts graded-MW past the ≥5/1000 rankability threshold. Build
the opener + caller MW mappers; grade via the existing MW graders + M6's opp-aware scalars.

## Files / interfaces
- `backend/app/domain/table/grade_map_postflop.py` — **append** opener/caller MW mappers:
  hero-as-opener c-bet/barrel MW nodes and hero-as-cold-caller MW nodes (the `_mw_ranges` /
  `VS_RFI (caller, opener)` content gate already exists — RES-I §4 line 117). Reuse
  `_mw_srp_preflop`, `_mw_check_bet_*`, `_mw_ranges`, `_is_canonical_bet`. Keep the explicit
  "hero closes / all behind acted" gate. New hero-seat shapes only — do NOT alter the existing
  BB-path mappers' outputs.
- `backend/app/domain/table/grade_map.py` — dispatcher: +imports, +chain entries.
- (Possible) small content: confirm `VS_RFI (caller, opener)` CALL-range coverage for non-blind
  openers is sufficient; if a gap blocks firing, note it (skip-and-document) rather than fabricate.
- Tests: new `tests/domain/test_mw_hero_seat_widening.py` + a **≥30k-hand re-measure** harness run.

## Out of scope
Bot-behavior changes (persona-mix / open-band levers — measured zero-effect, REJECTED, RES-I §4).
New graders (reuse MW graders + M6 scalars). 5+-way calibration. HU path (untouched).

## Constraints (invariants)
- **`_is_canonical_bet` blast radius** (RES-I §5, HIGH): it is shared by HU turn/river mappers +
  `map_mw_*` + S10/S11 display==grade. Reuse M1's `RECOGNIZED_BET_FRACS`; do NOT fork a private
  fraction set; any newly recognized faced size → defined RES-E bucket. Re-verify display==grade.
- Existing BB-path MW outputs **byte-unchanged** (hash-pins + existing MW mapper tests green).
- "No baseline yet" first-class; multiway = direction-only; `spot_signature()` frozen; domain purity.
- If the re-measure still falls short of ≥5/1000 after widening, **document the measured rate + the
  binding choke** in the done-note (skip-and-document) — do not force it with rejected levers.

## Verify-by (RES-I §6 / roadmap M7 pass/fail)
1. Opener + caller MW mappers fire on engine-driven MW states hero-as-opener / hero-as-caller that
   returned `None` before (belt-test, non-zero).
2. **≥30k-hand seeded re-measure** with the RES-I harness reports the fresh graded-MW/1000 rate +
   which hero proxy it assumes (tag / station); recorded in the done-note. Target ≥5/1000; if short,
   document the rate + choke (still a legitimate ship — the family widened honestly).
3. Existing BB-path outputs byte-unchanged (hash-pins); display==grade re-verified (S10/S11).
4. `spot_signature()` frozen; `verify.sh` + FE build green; refuter-on-diff + Codex Sol PASS.
