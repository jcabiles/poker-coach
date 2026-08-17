# N-DRAWLOOSE — contract map

**Scanned:** 2026-08-04 against `b0a6a4e`. Dependency-based, not name-based (a name-based
scan on the previous slice missed four load-bearing constraints and got a build halted at
its first ticket). Produced by the `contract-mapper` agent, then **verified by running the
full suite against the real change** — so every row below is measured, not predicted.

**Seam:** `personas_postflop.py:979` (`call_merit`) and its mirror at `:1098` (B5b damp).
`range_estimate.py` has no duplicate implementation — it calls `sample_postflop_decision`
directly (`:387`), so this is a single seam.

---

## HARD BLOCKERS — none, under the shipped design (option B)

| test | file:line | status |
|---|---|---|
| `test_nlogit_g1_orthogonality_raise_share_is_lever_invariant` | `test_personas_postflop.py:7135-7188` | ⚠️ **Blocker under rev 1 only.** Rev 1 flooring the call side alone made CALL affine in `L` while RAISE stayed proportional, so `L` stopped cancelling on draw cells. Rev 1 claimed that was unrecoverable; **both reviewers refuted it**. Coupling the raise scale to the call merit (`rscale := C(L)/C(ref)`, reducing to the literal `looseness/ref` on draw-NONE) preserves the guarantee for any call shape. **Measured green, unmodified, under the shipped variant.** It is now the gate that catches a half-implementation — ship the call-side change without the raise coupling and this fires. |

Also stale-by-consequence (prose, not a failing assertion): the N-LOGIT derivation comment
at `personas_postflop.py:1186-1231`, and `_R9LF_PANEL`'s docstring claim that "both
continue merits scale by the same factor s" — true only for draw-NONE nodes from now on.

## FIXTURES — confirmed moved

| constant | file:line | consumer | status |
|---|---|---|---|
| `_GOLDEN_STATS_N200` | `test_personas_postflop.py:3449-3556` | `test_persona_stats_byte_identical_after_log_refactor` | re-recordable under protocol (observed: `calling_station` AF 0.3277778 → 0.3667622 — the station's own policy is bitwise unchanged; the shared seeded rng stream re-deals it) |
| `_PRE_M3_FIRES` | `test_limper_coverage_belt.py:236-301` | `test_limper_coverage_fires_on_organic_play` | re-recordable under protocol (observed: UTG2¹ 74 → **70**; the 84 in rev 1 was the rejected variant) |
| `coverage_baseline.json` | `backend/tests/data/` | `test_coverage_baseline.py:355-363` | ⚠️ CORRECTED — the 332/"stream intact" reading was the rejected variant's. Real: `total` **1288 → 1233**, so the test fails on its FIRST assertion ("hand stream drifted"); graded 335 → 323, graded **share up 26.01 % → 26.20 %**. Open ruling R2. |

No other seeded golden exists. `test_price_tail.py`'s 23 frozen vectors were checked
individually and are all `draw is NONE` by construction (`:50-56`).

## AT-RISK — flagged statically, resolved by measurement

| test | prediction | measured |
|---|---|---|
| `test_r9lf_gsweep_nit_folds_more_than_tag_across_the_cell_population` (`:10070-10135`, floors 800/650) | exposed — draw cells are in the population and the floors are thresholds, not tolerances | **PASSES.** The contract map could not score this statically; it is now measured green. |
| `test_weak_draw_stops_stacking_off_at_high_commitment` (`:1303-1317`) | direct consumer of the coupled `:1098` site | **PASSES** — ordering assertion, same persona both sides |
| `test_strong_draw_potcommitted_still_jams` (`:1255`), `test_madehand_with_draw_commit_not_damped` (`:1289`) | assert `FOLD == 0.0` from `_commit_transform`, magnitude-independent | **PASS** |

## UNPREDICTED — found only by running the suite

| test | file:line | finding |
|---|---|---|
| `test_t4_flop_absolute_band[passive_fish-0.33-0.2-0.38]` | `test_arrival_range_ftc.py:354-372` | `passive_fish` ⅓-pot flop fold falls below its authored 0.20 floor. **The static map did not surface this**, because the band names no draw, no lever and no engine symbol — it is reached only through organic arrival. This is the residual risk the "map by dependency" rule cannot fully retire: a full-suite run is the only complete oracle. |

## SAFE — checked, with the evidence that makes them safe

- **`test_price_tail.py` (all)** — fixtures are AIR/ACE_HIGH with `draw is NONE`, stated at `:50-52` and confirmed.
- **`test_nlogit_g4_river_bluff_cell_response_is_pinned` (`:7382`), `test_nlogit_gcommit_spr_committed_nodes_are_lever_inert` (`:7463`)** — `bluff_cell` requires `draw is NONE` by definition (`personas_postflop.py:885-887`); the other uses AA (made, draw NONE).
- **`test_r9lf_gnode_...` (G-NODE, `:9830+`)** — all five `_R9LF_PANEL` nodes verified `DrawCategory.NONE`; measured self-differences byte-identical before and after (+0.0697 / +0.0717).
- **R9-DEFENCE-a S-2/S-3/S-4 line-invariance suite (`:8256-8520`)** — structurally excluded from draws by the engine's own scope predicate (`personas_postflop.py:1181`, `_LINE_SCOPE_BUCKETS` requires `draw is DrawCategory.NONE`), and `_R9D_HOLES` (`:8001-8006`) builds only draw-NONE cells. Includes `test_r9d_s4_composition_with_nlogit_commutes` (`:8466`), which does sweep `call_looseness` but only over those cells.
- **`test_elasticity_split_faithful_decomposition_byte_identical` (`:1321-1338`)** — the known "control built from a shipped pack" pin; its hole/board (`9h8h` on `Ac7s2h`) classifies `draw is NONE`. Safe **this time**. The pattern remains a hazard: the same test written against a draw-bearing hole would silently become a pin on shipped draw behaviour.
- **`test_facing_spots_are_position_inert_by_design` (`test_node_trace.py:136-167`)** — touches the strong-draw trace spot but pins no probability.

## ORGANIC CONSUMERS — reach bot decisions through simulation, name no seam

Named by Codex; all **pass** under the shipped variant, but they are the hidden-dependency
shape a static scan cannot find, so the next slice inherits the list rather than
rediscovering it: `test_mw_funnel_belt.py:36` (multiway mapper belt) ·
`test_grade_map_limped_flop.py:350` · `test_grade_map.py:703` (bot-driven facing-raise) ·
`test_grade_map_turn_river.py:604` (bot-driven turn barrel) · `test_range_estimate.py:1035`
(organic estimator parity) · R9-DEFENCE's organic S5 population run, which is distinct from
the structurally draw-free S2-S4 gates.

## BLIND SPOTS

1. The static scan missed the arrival band (see UNPREDICTED). Any future slice touching
   bot decisions should treat "the full suite is the only complete oracle" as the rule and
   the contract map as the thing that tells you *why* something broke, not *whether*.
2. ~~Attribution for the coverage decrease (335 → 332)~~ — **withdrawn as posed.** The real
   movement is `total` 1288 → 1233 with 246 of 400 hands changing shape, so there is no set
   of "three lost decisions" to attribute. It is arrival displacement; the graded *share*
   rises 26.01 % → 26.20 %. Ruling R2.
3. Arrival curves under the shipped variant were captured for `passive_fish` and `nit`;
   tag/lag/maniac rows are unmeasured (ungated, so nothing depends on them today). A builder
   re-deriving the fish band should fill the column while there.
4. **The `1e-12` invariance gate is the only thing standing between a correct
   implementation and a half-implementation.** If a future slice ever narrows or demotes it,
   the raise-leg coupling this slice adds becomes silently optional.
