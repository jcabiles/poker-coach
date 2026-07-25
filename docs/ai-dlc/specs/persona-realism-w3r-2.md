# W3R-2 — Fish + station elasticity dials (fix hyp-2) — GATED on W3R-0

**Slice of:** `docs/ai-dlc/roadmap/persona-realism.md` → W3R (bot-review remediation). Adjustment-plan fixes **#2**
(fish `call_looseness`), **#3** (station `size_elasticity` + station-flat test re-pin), **#6** (station
`call_looseness`). **Fixes hyp-2** (owner flag: "passive fish and calling stations over-call, don't react
realistically to aggression"). GATED on W3R-0 (the arrival-range fold-to-bet harness — merged, PR #98).

## Goal (one line)
Make the passive bots **react to bet size**: author the fish's + station's calling dials so their fold-to-c-bet
curves hit the grounded §5 bands — station gains a **shallow price response** (was size-blind), fish **stops
over-calling** overbets — with the dial values FIT on the W3R-0 harness, and the station-flat test assertion
flipped to "shallow rise".

## Why (the gap / root cause — from the review)
Two context-blind over-call leaks the reviewer traced to DIALS (not the merit table):
1. **station `size_elasticity: 0.0`** → its price-response exponent is 0, so its per-spot fold probability is
   mathematically FLAT across bet sizes (`_price_factor` exponent `2.2 × 0 = 0`). It calls a ⅓-pot and a 1.5×
   overbet at the same rate — the price-blind leak. **Fix #3:** `size_elasticity 0.0 → ~0.55` (a shallow response;
   the station is still sticky, just no longer size-BLIND).
2. **fish + station `call_looseness` never authored** → both inherit `stickiness` (fish 1.4, station 1.8) as the
   flat CALL multiplier, over-calling. **Fix #2:** author fish `call_looseness ~0.95` (below the inherited 1.4 →
   calls less, especially the overbet it should fold). **Fix #6:** author station `call_looseness ~1.6` (explicit,
   just below its inherited 1.8 — keeps it the stickiest bot without the accidental inheritance).

## Owner decisions (2026-07-24 interview) — TO CONFIRM AT GATE 2
1. **Dial values are FIT SEEDS, not constants.** Seed with the roadmap numbers (fish `call_looseness 0.95`; station
   `size_elasticity 0.55`, `call_looseness 1.6`), then TUNE on the W3R-0 arrival-range harness until the bands
   below assert stably. (W3R-1 lesson: a-priori dial magnitudes are seeds re-measured to target, never drop-ins.)
2. **Fish SMALL band — INCLUDED (owner, 2026-07-24).** Gate the fish fold-to-c-bet at BOTH SMALL (20–38%) AND
   OVERBET (60–80%) — a two-point curve gates the *slope*, not just the ceiling, so the fish is proven to react
   across sizes. W3R-0 encoded only the OVERBET band; W3R-2 adds the SMALL band (as a live gate) + fits both.

## Owner decision (2026-07-24, POST-FIT collision) — SCOPE EXPANDED, authorized
A first fit pass (Opus, HARD-STOP) proved the arrival-harness SMALL bands are UNREACHABLE without dragging the
frozen population WTSD bands out of range, AND that station price-awareness breaks a size-blind test the original
spec did not list. **Owner ruling: re-anchor the fish + station population WTSD bands NOW (do NOT defer to W4-b),
and flip every station-size-blind assertion — take the full realism win.** Measured collisions the fit must resolve:
- **Fish:** at dials that hit arrival SMALL 20–38% + OVERBET 60–80%, fish WTSD ≈ **0.46** (frozen band floor 0.53).
- **Station:** at dials that hit arrival SMALL <15% + OVERBET 18–40%, station WTSD ≈ **0.66** (frozen ceiling 0.64).
- **Three** station-size-blind assertions codify the OLD flat behavior and must ALL flip to a shallow price rise:
  `test_fold_to_bet_monotone_in_faced_size` (the `:512`/L514 `abs(r[1.0]-r[0.33])<0.05`), the exact-weight twin
  `test_station_size_blind_fish_size_scared_content` (L245 `abs(st_over-st_small)<1e-9`), and the MEDIUM-ordering
  near-tie `test_fold_to_bet_persona_ordering_at_fixed_size` (L570, station may now fold MORE than fish/maniac at ½-pot).
- **WTSD ordering** `test_persona_wtsd_ordering_invariants` (L2350) `passive_fish > tag − 0.06` breaks (fish now
  genuinely folds more → drops BELOW tag). Re-derive as INTENTIONAL (fish is now a fold-to-big-bet persona, not the
  old near-tie) with a comment — NOT a flattening regression.
- **Fish α-ceiling** `test_fold_to_bet_respects_alpha_ceiling[passive_fish]` (L552): folding more must still stay
  under `α + 0.05` at every bucket — re-verify, do not loosen the ceiling to pass.
Re-anchor discipline = the existing P2a methodology documented in the band-table block: RE-MEASURE WTSD at the
FINAL fitted dials at both representative N, set each new band = the 3σ CI union rounded outward, and annotate the
band-table line inline (`# WTSD re-anchored W3R-2`). Bands FOLLOW the fit; never fit to a pre-chosen band.

## Owner decision 2 (2026-07-24, fish α-ceiling fork) — "measure fish on its REAL range"
The second fit pass proved the grounded §5 fish OVERBET band (60–80%) is arithmetically UNREACHABLE under the
α fold-ceiling *as measured on the synthetic uniform any-two `fold_by_size` fixture* — because at a 1.5× overbet
α = f/(1+f) = 0.60, so folding 60–80% sits at/above the ceiling by construction. BUT on the fish's real ARRIVAL
range the band-hitting fit (`call_looseness ≈ 0.42`) is α-compliant at EVERY bucket (arrival .206/.361/.511/.638
vs α+0.05 .298/.383/.550/.650). **Owner ruling: the uniform fixture is mis-specified FOR THE FISH; re-scope the two
fish guards to measure on the arrival range** (P5-style re-pin) and take the full realism win:
- `test_fold_to_bet_respects_alpha_ceiling[passive_fish]` — measure the FISH leg on the W3R-0 arrival range (where
  the fit is α-compliant), NOT the uniform fixture. Other personas keep the uniform fixture. Document the fish as a
  SECOND arrival-range-measured exemption alongside nit, with the arithmetic (α=0.60 at 1.5× ⇒ the grounded 60–80%
  band is only honest on a realistic arrival range, not a uniform any-two range).
- `test_fold_to_bet_persona_ordering_at_fixed_size` — the fish ½-pot legs (`abs(fish−maniac)<0.06`, `fish<lag`) are
  pinned to the uniform fixture and break once the fish correctly folds more. Re-derive the FISH legs to reflect the
  intended new order (fish now folds MORE than the loose trio at ½-pot — it climbs the fold ordering), documented as
  intentional; keep the maniac/lag/tag/nit relationships that don't involve the fish strict.
- **Final fish dials:** `call_looseness ≈ 0.42` (fit to arrival SMALL 20–38% + OVERBET 60–80%); WTSD re-anchor
  (0.53, 0.68) → measured ≈ 0.525 ⇒ new band ≈ **(0.49, 0.56)**; ftc/AF stay in their current tuples (no move).
- **Final station dials:** `size_elasticity 0.55`, `call_looseness 4.0` (cl 4.0 not the 1.6 seed — needed to keep
  the uniform rise < 0.10); WTSD re-anchor (0.51, 0.64) → measured ≈ 0.69 ⇒ new band ≈ **(0.66, 0.72)**; ftc/AF stay.
Fish `size_elasticity 1.3` STILL locked. All final numbers are FIT SEEDS — re-confirm on the harness + pytest.

## Scope / files to touch
- `content/personas/passive_fish.json` — author `call_looseness` in `postflop`.
- `content/personas/calling_station.json` — set `size_elasticity` + author `call_looseness` in `postflop`.
- `backend/tests/test_arrival_range_ftc.py` — **UNSKIP** the W3R-0 flop band assertions (remove the
  `pytest.mark.skip(reason="unskip at W3R-2")`); the bands become LIVE gates fit by this slice.
- `backend/tests/test_personas_postflop.py` — **FLIP** the station-flat assertion (`:512`, currently
  `assert abs(r[1.0]-r[0.33]) < 0.05` "must be flat") → a shallow POSITIVE rise (station now price-aware) that
  stays UNDER the ≥0.10 bar the aggressive personas clear. This is a deliberate spec re-pin (the test currently
  codifies the very size-blindness we're removing — the P5-precedent style).
- Re-record the seeded-sim fixtures that observe fish/station behavior (golden / coverage / limper belt), P1/P2a
  precedent — behavior IS intended to change.
- **NO** engine/lever CODE change (`size_elasticity` + `call_looseness` are existing W2-a levers; this only sets
  their JSON values). No merit-table edit. No new lever.

## Pass/fail (HARD — the W3R-0 harness makes these provable)
- **Station gains a shallow price response:** on the W3R-0 arrival-range harness, station fold-to-c-bet SMALL
  (⅓-pot) lands **3–15%** rising to OVERBET (1.5×) **18–40%** — a positive slope, no longer flat. The flipped
  `:512` assertion asserts the shallow rise (a bounded positive `r[1.0]-r[0.33]`, under 0.10).
- **Fish stops over-calling the overbet:** fish OVERBET fold **60–80%** (and, if owner includes it, SMALL **20–38%**)
  on the W3R-0 harness.
- **`call_looseness↑` monotonicity:** raising `call_looseness` never LOWERS a persona's call frequency (the lever
  keeps its W2-a direction) — a unit check.
- **Dials fit, not forced:** the bands assert stably across repeated seeds at the harness N (W3R-0's provability
  criterion) — report the final fitted `size_elasticity` / `call_looseness` values.
- `./scripts/verify.sh` green; `ruff check .` clean; `content/` JSON validates.

## Out of scope
Population WTSD re-anchor is **NOW IN SCOPE for fish + station ONLY** (owner post-fit ruling above) — all OTHER
personas' WTSD/AF bands stay frozen to W4-b · no maniac change (W3R-1) · no merit-table / engine-lever CODE edit ·
no NEW lever · do NOT touch the fish `size_elasticity 1.3` (still owner-locked — the fish fit is `call_looseness`
+ the authorized WTSD re-anchor, NOT a price-slope change) · no band-context re-sync (the W3R-1 follow-up / W4-b).

## Invariants honored
Strategy in versioned `content/` data · domain core untouched · softmax law untouched (JSON lever values only) ·
`spot_signature()` frozen · results freq+EV · the station-flat assertion flip + the W3R-0 band unskip + fixture
re-records are the AUTHORIZED consequence of the intended dial change (P1/P2a + the P5 assertion-split precedent) ·
`call_looseness` keeps its W2-a direction (higher = more calling).

## Verify-by
`./scripts/verify.sh` green with the W3R-0 bands now LIVE (unskipped) and passing; the station-flat assertion
flipped to a shallow-rise and passing; fish/station fold curves hit the §5 bands on the harness; every OTHER
persona's curves + bands byte-identical; `ruff check .` clean; report the final fitted dial values + the measured
station SMALL/OVERBET + fish OVERBET (+ SMALL) fold rates.
