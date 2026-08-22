# Contract map — villain-bot calldown surface (improvement slice 3)

**Bottom line: the calldown dial (`call_looseness`, a per-persona multiplier
on how readily a villain bot calls a bet) is clamped in three places so
tuning it does nothing in those cells, and one of those clamps — the
strong-draw floor — was deliberately rebuilt three times already because
re-associating its arithmetic changes bitwise results at the calling
station's dial setting. Any calldown rework must re-derive a coupled
rebalancing term (`rscale`) or the RAISE action silently absorbs or loses
probability mass. The hero-grading module is a hard boundary this slice must
not cross — a specs check already forbids it. Everything the slice touches
routes through one production caller (the live bot loop) plus one estimator
that inherits the same math for free, so estimator parity is structural, not
merely tested, for two of the three levers this map found.**

Scanned at origin/main tip d351150 (before this spec's approval; unchanged by
the approval itself, which touched only documentation and the two contract
edits recorded separately).

## 1. The `call_looseness` dial

`call_looseness` (fallback: `stickiness`, an older name for the same
persona-pack field) is a single scalar multiplier on the flat CALL merit —
`backend/app/domain/personas_postflop.py:1121`, `1245-1250`. It multiplies
`(call_base + draw_bonus)` for every made-hand bucket and draw category on
the FOLD/CALL/RAISE facing node, read exactly once per decision, never
re-read downstream.

Where its effect is clamped or floored so tuning does nothing:
- STRONG draws below dial 1.0 — overridden by `max(looseness, 1.0)` (item 2
  below).
- River, AIR, no draw — `call_merit = 0.0` unconditionally at `:1291-1293`
  regardless of the dial.
- River, ACE_HIGH, no draw — multiplied by the frozen
  `_ACE_HIGH_RIVER_CALL_DAMP = 0.06` (`:1294-1295`, constant defined at
  `:607`) after the dial applies — the dial moves this cell only inside a
  0.06 envelope.

Coupling: the RAISE leg is rescaled by `rscale` (`:1643-1646`, the term that
rebalances CALL:RAISE probability mass) to preserve the CALL:RAISE ratio when
the STRONG-draw floor fires — so `call_looseness` changes have second-order
effects on RAISE mass, not just CALL mass.

## 2. The strong-draw floor (`:1228-1250`)

Mechanism confirmed: when the draw category is STRONG and `looseness < 1.0`,
`call_merit = call_base * looseness + _DRAW_CALL_BONUS[draw] * max(looseness,
1.0)` — the bonus term is floored at 1.0 whenever the dial is tighter.
`_call_merit_at_ref` (`:1246`) computes the UNFLOORED merit at a frozen
reference point and feeds the `rscale` coupling.

Load-bearing per in-file comments (`:1230-1244`): (a) the predicate
`looseness < 1.0` makes the floor a structural no-op for dial ≥ 1.0
(`calling_station` at 4.0 — "bitwise unchanged", guarded by
`test_nd_t4_calling_station_byte_identical_on_strong_draw`); (b)
`_call_merit_at_ref` must stay the BASE engine's call merit or the `rscale`
cancellation breaks.

Routes through it: STRONG draws with a tight dial only — nit, tag, lag,
maniac, passive_fish, never calling_station. Rebuilt three times already
(internally tracked as N-DRAWLOOSE T1/R1/R2, at `:3862-3906` in the test
file) because re-associating the arithmetic changes bitwise results at
dial=4.0. Any dial-sensitive rework must re-derive the `rscale` coupling (the
block at `:1509-1646`) or RAISE silently absorbs or loses mass.

## 3. Catcher-fold — NOT in this file (a brief assumption corrected)

`_calibrate_catcher_fold` (a hero-grading calibration function) lives in
`backend/app/domain/postflop.py:759` — the HERO-GRADING module, not the
villain bot. Specs explicitly forbid newer graders importing it
(`docs/ai-dlc/specs/epic5-m4-caller-reraise.md:20,43,53`;
`docs/ai-dlc/research/RES-H-mw-extension.md:284-360`). A calldown slice
scoped to the villain bot must NOT touch it — that would be a category
error.

`_CATCHER_BUCKETS` (test-only) is defined at
`backend/tests/test_personas_postflop.py:647`: `(MIDDLE_PAIR, TOP_PAIR)` —
the α-test fixture's bucket range. It deliberately EXCLUDES ACE_HIGH
(`:308-318`, `:835-846`) even though the owner ruled 2026-08-19 that α
already bounds ACE_HIGH — the ruling is recorded but not yet applied,
because applying it would breach the frozen went-to-showdown bands that
capped the 0.06 damp (`:841-846`). This is a LIVE DISCLOSED TENSION the
calldown slice walks into; the Stage-0 interim regime changes the collision
surface, which is why S3-T4 addresses it directly.

`_ACE_HIGH_RIVER_CALL_DAMP` and `call_looseness` compound multiplicatively
(dial first, damp after).

## 4. Multiway damps — path assignment

| Constant | Path | Evidence |
|---|---|---|
| `_MW_CATCH_TIGHTEN = 1.15` (`:770`) | Calling — multiplies fold_merit for `_MW_CATCH_BUCKETS` per added opponent | `:1201-1202` |
| `multiway_bluff_damp` (pack value) | Aggression — decays bluff_mass, not CALL | `:1128, :1161` |
| `_ACE_HIGH_FLOAT_RAISE_DAMP = 0.55` (`:458`) | Calling, despite the name — damps call_base for naked ACE_HIGH when `facing_raise or opponents>1`, flop/turn only | `:1220-1227` |

Stale-name flag: `_ACE_HIGH_FLOAT_RAISE_DAMP`'s placement on a
facing-a-bet calling node is disclosed in-file (`:1212-1219`) as a
deliberate scope change; the name no longer matches its placement.

## 5. Invisible contracts a calldown change trips

- **Bands** (`BANDS` dict, test file `:2832-2872`): per-persona 3-standard-
  deviation engine-anchored went-to-showdown/aggression-factor/
  fold-to-continuation-bet ranges; explicitly not fidelity claims against the
  research PRD (`:2712-2718`). Slice 3 measures against the interim regime
  installed by PR #208.
- **α ceiling tests** (`:713-830`; ACE_HIGH mirror `:908-978`): ceiling ONLY,
  never a floor (`:714-718`, `:935-939`) — no lower-bound fold assertion may
  be added.
- **Cross-persona ordering**
  (`test_fold_to_bet_persona_ordering_at_fixed_size`, `:981+`): re-derived at
  an earlier wave (internally tracked as W3R-2) — read the current text
  before assuming an order. Separate from the went-to-showdown ordering test
  this slice's tickets check.
- **`_GOLDEN_STATS_N200`** (`:3761+`): exact triples at n=200 on a SHARED RNG
  stream — any engine change displaces all six rows; re-record via the
  revert-to-prove-attribution protocol.
- **`_PRE_M3_FIRES`** (`backend/tests/test_limper_coverage_belt.py:236`):
  sibling pin, same stream sensitivity, re-pinned together historically.
- **LAG/maniac 1e-4 pin** (test file `:6017-6021`): `lag == 0.621358 ±1e-4`,
  `maniac == 0.295565 ±1e-4` — pure preflop pack arithmetic, no RNG; won't
  move from postflop calldown work but trips on any accidental preflop pack
  touch. (A nearby report-only stratified function at `:5754` is not the
  pin.)
- **RNG draw-order contract**: the action draw MUST stay the first
  `rng.choices` call, sizing second, nothing between
  (`test_nlogit_g6_one_action_draw_then_one_sizing_draw`, `:8730-8759`).
  Eight capture RNGs plus the range estimator's key on this order
  (`:8734-8736`) depend on it. NO new draw for calldown mixing — breaks
  every seeded test transitively.
- **De-robotization gate** (`backend/tools/derobo_gate.py`): a separation
  floor (all six persona labels must stay pairwise separated at ≥0.70× the
  frozen baseline pairwise distance of 1.254429) plus a determinism guard
  (fewer than 20% of qualifying decision contexts may have a modal action
  share ≥0.98) against the frozen `a5_baseline_z.json` artifact — never
  rebuilt.
- **Estimator parity** (PR #199 lineage): `table/range_estimate.py:54`
  imports `sample_postflop_decision` directly — the same function, capture
  RNG, so CALL/FOLD merit math changes are inherited for free. Risks are only
  (a) the RNG order contract, (b) sizing distributions (the estimator fits
  action type only, sizes are category-level, `:23-33`). Do not fork the
  logic into a separate copy.

## 6. Downstream consumers

- `backend/app/domain/table/play.py:29` — the live bot loop, sole production
  caller.
- `backend/app/domain/table/range_estimate.py:54` — the villain-range
  estimator (see above).
- `backend/tools/export_analytics.py:61` — imports only `strength_bucket`;
  calldown-only changes are low-risk here, bucket/draw-category
  classification changes would reach it.
- `backend/app/domain/table/postflop_context.py:226-227` — lazy imports to
  dodge a circular import.
- `backend/tests/test_personas_postflop.py` — roughly 9,000+ lines,
  single-owner per wave; the ownership constraint named in the tickets file
  is load-bearing.
