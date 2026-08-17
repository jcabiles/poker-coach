# Contracts map — N-LAGWIDTH (lag late-seat unopened trim)

Read-only scan 2026-08-01 (contract-mapper), condensed. Full reasoning in the spec's gate tables.

## Load-bearing numeric gates (update in the SAME commit as the pack change)
- `backend/tests/test_personas.py:403` — `BANDS["lag"]` open-freq seat-average, exact-width ±2pp. Re-pin with in-file disclosure.
- `test_personas.py:727-734` — `_LAG_OFFSUIT_CEILING` / `_LAG_SUITED_FLOOR` per-seat pair (both legs asserted together at `:824-854`).
- `backend/tests/test_rr_emit.py:424-436` — spec `raise_pct` annotations must match emitted widths.
- `test_rr_emit.py:351-406` — lag proving gates: shipped `lag.json` must equal the spec's emission byte-for-byte (135 classes / 18 mixes pinned).

## Strict relational gates (constrain the trim's shape)
- `test_personas.py:888-953` — lag suited must be a class-by-class SUPERSET of tag's at CO/BTN/SB → **trim is offsuit-only**.
- `test_personas.py:857-881` — lag offsuit ≥ tag offsuit at LJ/HJ/CO/BTN/SB → bounds trim depth from below (verify vs actual post-#153 tag pack).
- `test_personas.py:974-991` — strict monotone UTG→BTN + SB<BTN → **CO's floor = untouched HJ width + margin** (HJ ≈ 47.x, measure first).
- `test_personas.py:615-640` / `:957-971` — maniac>lag / lag>tag at every seat (trim direction is safe for the former; verify the latter per-seat).
- `test_personas.py:546-554` — lag premium unopened never folds.

## Governance (theory contract)
- §5a per-seat RFI ruling (2026-07-31, PR #154): one-sided bounds + within-persona shape only; cross-persona orderings `[UNVERIFIED]`, never HARD; cited targets must carry the provenance anchor verbatim (`docs/ai-dlc/research/rfi-seat-provenance.md:127` — LAG BTN "50+" folklore, `[UNVERIFIED]`).
- §5 LAG ruling: VPIP+gap primary, PFR derived-DIRECTIONAL (dip below 17 allowed, disclose + W4-b watch).
- Population PFR measured 17.36 post-#152; prior lag slices kept width constant because of this floor — this slice is the first to spend it, under the owner's 2026-08-01 acceptance.

## Fixture surfaces (atomic re-record, single-recorder custom, in-file disclosures)
- `test_personas_postflop.py` golden rows · `test_coverage_baseline.py` · `test_limper_coverage_belt.py` — rng-stream displacement from the first changed lag open onward.

## Emitter constraints
- `backend/tools/rr_emit.py` — contiguous top-anchored rows only; a bottom-of-ladder offsuit cut is expressible; the wheel-ace keep-token limitation (filed) is NOT triggered by a bottom cut.
- `content/personas/ladders/lag.unopened.json` — build-time only (loader globs `content/personas/*.json` non-recursively; `ladders/` is runtime-invisible).

## Downstream
- `range_estimate.py` estimator reads the same PersonaPack at runtime → parity automatic, no mirror.
- `play.py:124 _preflop_decision` → live path; sim-session tests exercise the pack indirectly (possible fixture ripple, unconfirmed).
- ~~Instrument hazard: `_STATS_EXT_CACHE` keys are pack-blind in-process~~ **CORRECTED at review (2026-08-01):** the cache key includes `_packs_fingerprint(packs)` since wave-6 #155 (`test_personas_postflop.py:2827`) — pack-content-sensitive. Separate-process measurement kept as precaution only.

## Review corrections (2026-08-01 — see ledger/n-lagwidth.md)
- ADD: N-3BSTRATA lag gates `test_personas_postflop.py:5136` (component pin 0.6166±0.02) + `:5265` (blend band [0.43,0.53] @12000) — unopened-composition-driven; N-LAGLADDER precedent broke the floor (0.4242) and required a vs_3bet opener retune.
- ADD: `test_w3r1_preflop_cleanup.py:236` `test_lag_sb_no_open_limp` — pins SB J9o → raise exactly.
- FIX: `test_personas.py:974` is NON-DECREASING (equality passes); strictness lives in `test_rr_emit.py:414`. Proving gates are semantic (combo sets + weights), not byte-level. RR-LINT inventory at `:~147-224` + assertions `:277`, not `:101`.
- BASELINE: main 47d642d RED on 2 tests (byte-identity golden + limper belt) — prerequisite repair before this slice.
