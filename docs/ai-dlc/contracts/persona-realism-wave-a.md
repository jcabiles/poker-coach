# Contract map — persona-realism Wave A (R8)

Read-only scan by `contract-mapper`, 2026-07-25, for the 8-ticket Wave A slice.
Source review: `docs/ai-dlc/research/persona-realism-artifacts/hand-analysis-181/SYNTHESIS.md`.
**Cross-checked against the three specialist ticket drafts** — where a draft's scoping
already resolves a risk below, that is noted inline.

---

## Cross-cutting flags

### 1. T-STACK reverses a recently-merged slice. This is the wave's biggest surprise.

`backend/tests/test_sim_session_buyin_cap.py` exists **specifically to pin carry-over**, and
`test_cap_leaves_stacks_inside_band_untouched:107-118` asserts a within-band stack is left
**untouched** between hands — the literal opposite of "reset every seat to ~100bb per hand."
That whole file is W5-c3 (PR #117) work. **T-STACK requires rewriting it, not re-running it.**
Owner adjudicated the deep-stack table a bug on 2026-07-25, so this reversal is authorized —
but it must be stated in the ticket, not discovered during the build.

Affected tests in that file: `test_cap_trims_winner_stack_and_preserves_net:71-87` ·
`test_cap_retriggers_on_repeated_wins:90-104` · `test_cap_leaves_stacks_inside_band_untouched:107-118`
· `test_stacks_stay_within_cap_across_hands:124-137` (passes trivially post-change; intent moot).

### 2. The `net_bb` invariant is user-facing and easy to break silently.

`_apply_settlement` (`sim_session.py:176-203`) documents the convention: whenever a correction
moves `stack_bb`, `buyins_bb` absorbs the **same delta**, so `net_bb = stack_bb - buyins_bb`
survives. `frontend/src/components/simulate/SimLedger.tsx:5-6` renders exactly that as a live
per-seat P&L. **A per-hand reset that does not absorb its delta into `buyins_bb` every hand will
make every seat's displayed net read ~0 after hand 1.** Reuse the existing pattern; do not invent one.

### 3. T-STACK will move persona behaviour even though it touches no persona file.

`spr_commit` is a **step function with zero gradient** (`personas_postflop.py:889-911`;
`_commit_transform` zeroes FOLD and ×3-boosts BET/RAISE at the threshold). A ~5bb stack change
swings raise frequency ~28 points. Resetting stacks changes every hand's SPR distribution.
**Expect AF/WTSD to move. That is not a bug — but do not let it be mistaken for one, and do not
let it be "fixed" by re-tuning a persona lever.** This is also why the roadmap sequences T-STACK
ahead of W4-a.

### 4. `backend/tools/` is a new directory with no precedent script.

No committed extraction script for the `sim_*` tables exists. Reuse `app.db.session.engine`
rather than hardcoding a DB path, so the tool reads the same DB the app writes.
**Assign `backend/tools/__init__.py` to exactly one ticket** (recommend T-EXPORT as first mover) —
T-EXPORT and T-REJECT both land files there and this is their only collision risk.

---

## Per-file contracts

### `backend/tools/` — session exporter (T-EXPORT)

- **`SimSeat.stack_bb` / `buyins_bb` are CURRENT values, overwritten on every settlement.** There is
  no per-hand historical ledger. Per-hand starting stack must be reconstructed from that hand's
  `SimHand.state_json` as `stack_bb + invested_total_bb` (existing pattern: `sim_session.py:1188-1191`).
- **`SimDecision` holds HERO rows only.** Bot decisions are never persisted; they exist only inside
  `state_json`'s `action_history`. Per-persona packets must parse `action_history`, not query `SimDecision`.
- **Seat↔position is NOT stable across hands** — `deal_next_hand` rotates `button_seat` every hand
  (`sim_session.py:1337`), and `action_history` entries carry `position`, never `seat`. Build a per-hand
  `position → seat` map from that hand's own `state.seats` (pattern: `sim_session.py:1478-1479`), then join
  `seat → persona_type` via `SimSeat`. **Skipping this silently mis-attributes every hand after the first
  button rotation.**
- `state_json` is an opaque TEXT column with **no version field**. Wrap `HandState.model_validate_json`
  in try/except-and-skip for long-lived dev DBs.
- Purity: `backend/tools/` is outside `app/domain/`, so direct `sqlmodel`/`sqlalchemy` imports are fine.
- Privacy note: `state_json` holds all nine seats' hole cards. The API path scrubs this
  (`sim_session.py:6-9`); a tool bypasses that scrub. Correct for offline analysis, but deliberate.

### `backend/app/services/sim_session.py` (T-STACK)

- `_STARTING_STACK_BB = 100.0` · `_REBUY_FLOOR_BB = 1.0` · `_STACK_CAP_BB = 200.0` (with the W5-c3
  rationale comment at `119-127` tying 200bb to the theory contract's ~100bb reference pool — that
  comment becomes stale and should be updated, not left contradicting the code).
- `_apply_settlement` is the single correction point, called from `_deal_and_advance:227-229` and
  `apply_hero_action:858-862`. Today it is **conditional** — only busted or over-cap seats are touched.
- No Alembic migration needed (existing columns, service logic only).
- Also re-verify: `test_sim_session.py:191-216` (rebuy + 2dp ledger), `:219-228` (chip conservation —
  should still hold if the net-invariant is honoured), `:96-104` (session creation — unaffected).

### `backend/tests/node_trace.py` (T-TRACE)

- `build_trace:130-151` passes `current_bet_to`, `is_aggressor`, `street` — never `context=` or
  `facing_raise=`. The live path (`play.py:147-161`) always threads both.
- Of `PostflopContext`'s three fields, only `busted_draw` is derivable from a crafted `Spot`
  (`busted_draw_kind(hole, board)` is pure). `in_position` and `bet_prev_street` need explicit fields on
  node_trace's own `Spot` NamedTuple — **the nit draft already specifies this**, with per-spot values.
- **None of the 7 current SPOTS represent "facing a raise"**, so the one-pair / ace-high facing-raise damps
  stay invisible even after this ticket. Contract-mapper flags closing that gap; the nit draft scopes it
  out and adds only an OOP twin. *Reconcile in the spec — see open question O1.*
- `test_node_trace.py` asserts structure only (well-formedness, non-degeneracy, determinism), pins no
  probability values. Low breakage risk.

### `backend/app/domain/personas_postflop.py` (T-ANCHOR)

- Bug confirmed at `826-829` (complement fixed on pre-position `bluff_mass`) vs `868-869` (multiplier
  applied to `agg_merit` after). `_position_agg_mult:635-639` is symmetric ±0.25 × `position_sensitivity`.
- **Only tag/nit/lag opt in** (`position_sensitivity` 1.0/1.0/0.6); station/fish/maniac short-circuit to 1.0.
- **The frozen golden is unaffected**: `test_persona_stats_byte_identical_after_log_refactor:2596-2609`
  runs `_persona_stats` with `context_aware=False`, so `context=None` and the multiplier is identity.
- **The two bluff-ordering tests are unaffected**: `test_bluff_freq_rises_with_chosen_size` and
  `test_bluff_ordering_across_personas_at_fixed_size:897-918` route through `_air_bet_weight:880-894`,
  which passes no `context`. **Independently confirmed by the fish draft, which converts this into the
  ticket's primary tripwire: any movement in that test proves double-application, never a legitimate
  re-anchor.**
- What *will* move: the live bot path (`play.py::bot_decision` always threads context, not opt-in) and
  `test_street_aggressions_effect_visible_to_af_gate:2626-2653` (asserts a directional inequality with
  margin — likely survives; re-verify).
- Seeded live-loop fixtures (golden, `coverage_baseline.json`, limper belt) may legitimately move.
  Report the cumulative delta vs `coverage_baseline.persona-realism-start.json` per the anti-laundering rule.

### `content/personas/*.json` + `models.py` (T-STICKY)

- `PersonaPostflop.stickiness` (`models.py:147`, **required**, `gt=0.0`) is read in exactly two places:
  the `looseness` fallback (`personas_postflop.py:702`) and `_price_exponent`'s legacy branch (`:578-579`).

| persona | `call_looseness` | `size_elasticity` | `stickiness` read? |
|---|---|---|---|
| calling_station | 4.0 | 0.55 | **never** |
| passive_fish | 0.42 | 1.3 | **never** |
| tag / nit / lag | 0.6 / 0.6 / 0.55 | — | price exponent only (`**-0.15`, tiny) |
| **maniac** | **none** | **none** | **both branches — fully load-bearing** |

- ⚠️ Contract-mapper's warning: deleting the field outright is a **behaviour change for maniac**
  (`looseness = 0.55`; `price_exponent = 2.2 × 0.55**-0.15 ≈ 2.402`). **The fish draft already resolves
  this** by making the field `| None` and deleting it only from the two provably-dead packs, leaving
  `personas_postflop.py` untouched and adding a validator that forbids the field only when both split
  levers are authored. Adopt the fish scoping.
- `content/schema/persona.schema.json` has **no `postflop` definition at all** and is referenced by no
  code — it will neither catch nor block this. Pydantic is the only enforcement.
- `load_persona_packs` (`personas.py:40-49`) loads all six eagerly and fails fast together.

### `test_personas_postflop.py` `_persona_stats_ext` (T-ARR)

- `ExtStats` is a NamedTuple accessed **by attribute everywhere**, single all-keyword construction site
  at `:2489` → appending fields is low-risk.
- ⚠️ **Do not confuse with `_persona_stats`** (`:2155`), which returns a plain tuple and **is** unpacked
  positionally at `:2602`, `:2641-2642`, `:2784-2785`, `:2816`. T-ARR must not touch it.
- Contract-mapper notes `PostflopDecision` lacks `position`/`facing_node`, making general node occupancy
  a larger change. **The nit draft avoids this entirely** by scoping T-ARR to *preflop* node occupancy,
  captured at the existing `_preflop_facing(state)` + `seat_state.position` call site where both values
  are already computed and discarded. Adopt the nit scoping.
- **Budget is frozen at ≤12s** (module docstring `:5`; `_derive_n:1920-1931`, `budget_s = 9.5`).
  `_persona_stats_ext` is memoized in `_STATS_EXT_CACHE:2263`. Counters riding the existing loop are ~free;
  **a second simulation loop would break the budget** (the nit draft makes this a no-go).
- ⚠️ Cardinality: 9 positions × 5 facings = 45 cells/persona against the `_rate` ≥30-occurrence floor
  (`:2266-2268`) at n≈150–400. The nit draft handles this by asserting on the **roster-pooled** vector
  with **bands, never goldens** — all six personas share one rng stream, so sibling tickets displace it.

### `backend/app/domain/table/grade_map_postflop.py` (T-REJECT)

- ~14–19 mapper functions returning bare `Spot | None`, each with 5–10 independent `return None` sites
  (`map_flop_cbet:48-147` alone has 9). Callers pattern-match on `is None` and chain with `or`
  (`sim_session.py:490-506`). **Changing the return type breaks every caller.**
- Transitively purity-checked: `grade_map.py` is in `test_domain_purity.py:16`'s list and imports this
  module. No web/DB imports, and ideally no module-level mutable state.
- Contract-mapper offered three shapes and disliked all three (change return type / global counters /
  parallel reimplementation that drifts). **The hero draft chose a fourth and better one:** a separate
  `grade_map_reject.py` classifier that runs as a *second pass* over the same `HandState`, **imports and
  calls the existing gate predicates** rather than reimplementing them, and never touches the mappers —
  so byte-identity for existing callers is structural, not test-enforced.
- ⚠️ Residual risk the fourth shape does not remove: the classifier still encodes **precedence ordering**
  independently of the mappers, so it can drift. The hero draft mitigates with `UNCLASSIFIED == 0` as a
  hard assertion — treat any `UNCLASSIFIED > 0` as a taxonomy-drift defect signal, not a valid outcome.
- Six test files reference these mappers: `test_grade_map_flop_facing.py`, `test_grade_map_turn_river.py`,
  `test_mw_funnel_belt.py`, `test_mw_hero_seat_widening.py`, `test_apply_multiway_opp.py`,
  `test_sim_postflop_sizing.py`. None should need edits under the fourth shape.

---

## Open questions for the spec

- **O1 — T-TRACE scope.** Contract-mapper says a "facing a raise" spot should be added so the
  facing-raise damps become visible; the nit draft scopes that out and adds only an OOP twin, arguing the
  facing-node inertness is *correct* today (the OOP defence damp is an unbuilt later slice). **Resolve:
  recommend following the nit draft and filing the facing-raise spot as a Wave B follow-on**, since adding
  it invites a worker to "fix" inertness by editing `_position_agg_mult` — a collision with T-ANCHOR.
- **O2 — `backend/tools/__init__.py` ownership.** Assign to T-EXPORT.
- **O3 — the W5-c3 rationale comment** at `sim_session.py:119-127` becomes stale under T-STACK. Update it
  in the same ticket rather than leaving code and comment contradicting.
