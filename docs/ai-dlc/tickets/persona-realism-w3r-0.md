# W3R-0 tickets — arrival-range fold-to-bet harness

Spec: `docs/ai-dlc/specs/persona-realism-w3r-0.md`. Measurement-only; zero bot behavior change; every existing
suite must stay byte-identical. All work lands in `backend/tests/` (+ read-only reuse of `app/domain`).

Owned files (single owner = this slice): NEW `backend/tests/test_arrival_range_ftc.py` (+ any test-support helper
under `tests/`). Do NOT edit `app/domain/personas.py`, `personas_postflop.py`, or any persona JSON.

## T1 — Arrival-range builder (replay preflop policy, CALL-ONLY)
Build a helper that, for the canonical HU single-raised pot (villain = RFI raiser, bot = `vs_rfi` caller) + ref
pool (9-max ~100bb), deals hands and runs `sample_preflop_action(pack, position, facing="vs_rfi", hole, rng)` per
persona, keeping ONLY the hands the persona **CALLS** with (flat-call an RFI) → its flop arrival range. **3bet/raise
hands are EXCLUDED** (they'd be the aggressor c-betting, not facing a c-bet — refuter HIGH).
- **Done-condition:** a unit test asserts (a) the arrival ranges are persona-ordered by tightness — nit ⊂ (roughly)
  tag ⊂ maniac; (b) **no hand that the persona 3bets vs an RFI appears in its arrival range** (call-only proof);
  (c) fixed sample size `N ≥ 1250` (mirror `_PRICE_N`; bump for tight ranges). Seed-pinned.
- **Owned:** the builder + its unit test. **No** edits to `personas.py`.

## T2 — Flop fold-to-bet-by-size over arrival ranges
Measure per-persona fold-rate facing a flop c-bet at {0.33,0.5,1.0,1.5}× pot, over each persona's T1 flop arrival
range (paired spots, seed-pinned, mirroring `fold_by_size`'s structure but arrival-range-fed).
- **Done-condition:** emits `rates[persona][frac]` for the flop; a smoke test asserts values are in [0,1] and the
  curve is produced for all 6 personas. Prints/exposes the curve for inspection.
- **Depends-on:** T1.

## T3 — Turn + river continuation ranges + fold-to-bet (HEAVY — SPLIT T3a/T3b)
Extend to turn and river: simulate each persona's continuation (which hands it keeps betting/calling on the prior
street) to derive the turn/river arrival range, then measure fold-to-bet at the same size buckets.
- **Build note (refuter MED):** do NOT reuse `_play_hand` (`test_personas_postflop.py:1585`) — it's an all-persona
  9-max table, not the controlled "villain c-bets a fixed size each street, bot responds" continuation this needs.
  Build a small **scripted 2-player continuation sim** driving `sample_postflop_decision(..., street=,
  current_bet_to=)` street by street; do NOT cross-import the private `_play_hand`.
- **Done-condition:** emits per-persona turn and river fold curves; a smoke test asserts they compute for all 6
  personas. **Turn/river are measurement-only (NO hard band).**
- **Depends-on:** T2. **Split:** T3a turn, T3b river (this is the heaviest work in the slice — the ~200-line
  continuation sim; do not fold it into T2).

## T4 — Documented target bands as xfail/skip assertions (flop)
Encode the grounded flop bands (station SMALL 3–15% → OVERBET 18–40%; fish OVERBET 60–80%; others where grounded)
as module constants + parametrized assertions **marked `pytest.mark.skip(reason="unskip at W3R-2")`** (NOT strict
xfail — refuter LOW: a coincidental in-band value under a future `xfail_strict` conftest would XPASS-redden the
suite; `skip` is immune). Turn/river: emit curves, NO hard assertion.
- **Done-condition:** the band tests exist and are collected but skipped (suite green today); a comment ties each
  band to its audit §5/F10 source and names W3R-2 as the un-skip trigger.
- **Depends-on:** T2 (flop curves).

## T5 — Byte-identity + verify wiring
Confirm the new module is a pure add: every pre-existing test stays byte-identical, `./scripts/verify.sh` green,
`ruff check .` clean. Add a short docstring/README note on how to print the curves for the manual pre-fix-shape
check (station ~flat, fish under-folding — proving the harness captures the leak W3R-2 fixes).
- **Done-condition:** `./scripts/verify.sh` green with the new module; existing suite counts unchanged (only
  additions); ruff clean.
- **Depends-on:** T2–T4.

## Sequencing
T1 → T2 → {T3, T4} → T5. Single-owner throughout (all in the new test module); no hotspot contention with the
`personas_postflop.py` spine (this slice touches no engine code), so W3R-0 can even run parallel to W3R-1.
