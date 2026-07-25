# W3R-2 tickets — Fish + station elasticity dials (fix hyp-2)

Spec: `docs/ai-dlc/specs/persona-realism-w3r-2.md`. GATED on W3R-0 (merged). JSON dial values + test re-pin + fit
on the W3R-0 harness; NO engine/lever CODE change. Single owner (the two persona JSONs + the two test files are
one logical change; the fit-loop must see all edits). Behavior change IS intended → seeded fixtures re-record
(P1/P2a). Dial magnitudes are FIT SEEDS — measure on the W3R-0 harness, tune to the bands, never drop-in.

Owned files: `content/personas/passive_fish.json`, `content/personas/calling_station.json`,
`backend/tests/test_arrival_range_ftc.py` (unskip bands), `backend/tests/test_personas_postflop.py` (flip ALL
station-size-blind assertions + re-anchor fish/station WTSD bands + re-derive the two ordering tests — see T5/T6),
the re-recorded fixture data files. Do NOT edit `app/domain/` or the merit table.

**SCOPE EXPANDED (owner post-fit ruling, see spec):** the first fit HARD-STOPPED — arrival SMALL bands collide with
the frozen population WTSD bands and with station-size-blind tests. Owner authorized re-anchoring fish+station WTSD
NOW + flipping every station-size-blind assertion. T5/T6 below cover the added surface. Fish `size_elasticity 1.3`
stays owner-locked; the fish fit is `call_looseness` + the authorized WTSD re-anchor.

## T1 — Make the W3R-0 bands LIVE + flip the station-flat assertion (the fit targets)
Remove the `pytest.mark.skip(reason="unskip at W3R-2")` from the W3R-0 flop band assertions in
`test_arrival_range_ftc.py` so station SMALL 3–15% → OVERBET 18–40%, fish OVERBET 60–80%, AND **fish SMALL 20–38%
(owner INCLUDED)** become LIVE gates. Add the fish SMALL band constant if W3R-0 didn't encode it (it encoded only
the fish OVERBET) — cite audit §5. In `test_personas_postflop.py:512`, FLIP the station branch from
`assert abs(r[1.0]-r[0.33]) < 0.05` (must be flat) → `assert 0 < r[1.0]-r[0.33] < 0.10` (shallow positive rise:
price-aware now, but still under the ≥0.10 bar the aggressive personas clear) — update the comment to cite W3R-2 as
the re-pin (the old assertion codified the size-blindness being removed; P5-precedent).
- **Done-condition:** the bands are collected + LIVE (not skipped); the flipped station assertion is present. (These
  will FAIL until T2/T3 fit the dials — expected mid-slice; T4 is the green gate.)
- **Owned:** both test files.

## T2 — Fish `call_looseness` fit to the fish OVERBET (+SMALL) band
Author `call_looseness` in `passive_fish.json` `postflop` (seed ~0.95; currently unset → inherits `stickiness`
1.4). MEASURE fish fold-to-c-bet on the W3R-0 harness; TUNE `call_looseness` until fish OVERBET fold ∈ 60–80%
AND SMALL ∈ 20–38% (owner INCLUDED both). Do NOT touch fish `size_elasticity` (1.3 — already size-aware).
- **Done-condition:** fish OVERBET fold ∈ 60–80% AND SMALL ∈ 20–38% on the harness, stable across seeds; report
  the fitted `call_looseness`. `call_looseness↑` monotonicity unit check still holds. **If both bands can't be hit
  with `call_looseness` alone** (the fish is already size-aware via `size_elasticity 1.3`, so the SLOPE is fixed —
  only the level shifts), STOP and report — a fish `size_elasticity` change would be an owner decision (out of scope).
- **Depends-on:** T1.

## T3 — Station `size_elasticity` + `call_looseness` fit to the station SMALL→OVERBET slope
In `calling_station.json` `postflop`: set `size_elasticity` (seed ~0.55, from 0.0) + author `call_looseness`
(seed ~1.6; currently inherits `stickiness` 1.8). MEASURE station fold-to-c-bet on the W3R-0 harness; TUNE both
until station SMALL ∈ 3–15% AND OVERBET ∈ 18–40% (a positive slope) AND the flipped `:512` shallow-rise assertion
passes.
- **Done-condition:** station SMALL ∈ 3–15%, OVERBET ∈ 18–40%, slope positive + under 0.10; the `:512` flipped
  assertion passes; report the fitted `size_elasticity` + `call_looseness`.
- **Depends-on:** T1. (T2/T3 independent personas but share the harness + the fixture re-record → same worker.)

## T4 — Fixture re-record + verify green
Re-record the seeded fixtures observing fish/station behavior (golden / coverage_baseline / limper belt). Confirm
every OTHER persona's curves + bands byte-identical (only fish/station move). Verify green end-to-end.
- **Done-condition:** `./scripts/verify.sh` green (W3R-0 bands LIVE + passing; station assertion flipped + passing);
  `content/` JSON validates; `ruff check .` clean. Report final fitted dials + the measured station SMALL/OVERBET +
  fish OVERBET(+SMALL) fold rates + which fixtures moved.
- **Depends-on:** T1–T3. **If a band can't be fit within a sane dial range** (e.g. station OVERBET can't reach 18%
  without `size_elasticity` so high it breaks the SMALL floor), STOP and report — retargeting a band is an owner
  decision.

## T5 — Re-anchor the fish + station population WTSD bands (owner-authorized, P2a discipline)
In `test_personas_postflop.py` the persona band table (the `# persona -> (AF band, fold_to_cbet band, WTSD band)`
dict, ~L1886): fish WTSD `(0.53, 0.68)` and station WTSD `(0.51, 0.64)` collide with the fitted dials. RE-MEASURE
fish + station WTSD at the FINAL fitted dials at BOTH representative N, set each new band = the 3σ CI union rounded
outward (the P2a methodology documented in the band-table comment block above the dict), and annotate each moved
line inline (`# WTSD re-anchored W3R-2 (owner-authorized post-fit collision)`). Also re-anchor fish/station
fold_to_cbet band tuples if the fit moves them outside the current tuple. **Move ONLY fish + station rows** — every
other persona's WTSD/AF/ftc tuple stays byte-identical (frozen to W4-b).
- **Done-condition:** the fish/station WTSD (and ftc if needed) bands contain the measured values with the P2a 3σ
  margin; the inline annotation cites W3R-2; all OTHER persona rows unchanged; `test_persona_wtsd_bands` (or whatever
  consumes the dict) passes at both N.
- **Depends-on:** T2, T3 (needs the final fitted dials).

## T6 — Flip the three station-size-blind assertions + re-derive the two ordering legs
Station is now price-aware, so the assertions that codify its OLD flat/size-blind behavior must flip (P5 precedent):
1. `test_fold_to_bet_monotone_in_faced_size` L514 `abs(r[1.0]-r[0.33])<0.05` (the station branch) → a shallow
   POSITIVE rise under 0.10 (`0 < r[1.0]-r[0.33] < 0.10`); station now joins the monotone branch but stays under the
   ≥0.10 bar. (This is the same re-pin as the `:512` one T1 does in the arrival test's mirror — do the postflop one here.)
2. `test_station_size_blind_fish_size_scared_content` L245 `abs(st_over-st_small)<1e-9` → `0 < st_over-st_small`
   (a positive, sub-fish gap: station shallow, fish still steep >0.15). Rename the comment ("station: shallow price
   rise, no longer size-blind"). Keep the fish leg (L246) unchanged.
3. `test_fold_to_bet_persona_ordering_at_fixed_size` L570: station may now fold MORE than fish/maniac at ½-pot →
   re-derive the `calling_station <= min(fish,maniac)+0.01` leg to reflect the intended new order (station no longer
   the loosest at MEDIUM), with a comment citing W3R-2. Keep the disciplined-vs-loose legs (lag/tag/nit) strict.
4. `test_persona_wtsd_ordering_invariants` L2350 `passive_fish > tag − 0.06` → re-derive (fish now genuinely folds
   more, WTSD drops BELOW tag — INTENTIONAL, not flattening); comment must say so. Keep the station strict legs
   (station > tag, station > lag, maniac < station) — verify they still hold at the fitted dials.
5. `test_fold_to_bet_respects_alpha_ceiling[passive_fish]` (L552) — **owner decision 2:** re-scope the FISH leg to
   measure on the W3R-0 ARRIVAL range (where the band-hitting `call_looseness≈0.42` fit IS α-compliant at every
   bucket), NOT the uniform any-two fixture. Keep every OTHER persona on the uniform fixture. Document the fish as a
   second arrival-range-measured exemption alongside nit, with the arithmetic (α=0.60 at a 1.5× overbet ⇒ the
   grounded 60–80% band is only honest on a realistic arrival range). Do NOT loosen the α+0.05 tolerance itself.
6. `test_fold_to_bet_persona_ordering_at_fixed_size` (L571 `abs(fish−maniac)<0.06`, L572 `fish<lag`) — **owner
   decision 2:** the fish now correctly folds MORE at ½-pot, so it climbs the fold ordering. Re-derive the FISH legs
   to the intended new order (fish above the loose trio), documented as intentional (not flattening). Keep the
   station leg from T6.3 and the lag/tag/nit relationships strict.
- **Done-condition:** all these tests pass at the fitted dials (fish `call_looseness≈0.42`, station
  `size_elasticity 0.55`/`call_looseness 4.0`) with every re-pin documented inline citing W3R-2 + owner decision 2.
- **Depends-on:** T2, T3.

## Sequencing
T1 (make gates live) → {T2 fish, T3 station} (fit dials to gates) → {T5 WTSD re-anchor, T6 test flips} (both need
final dials) → T4 (re-record fixtures + verify green). Single owner/worker — the fit-loop + WTSD re-anchor + shared
fixture re-record can't split across workers. NO `app/domain/` engine-spine edit (test-file assertions + JSON dials
+ band-table values only), so no hotspot contention with other engine slices.
