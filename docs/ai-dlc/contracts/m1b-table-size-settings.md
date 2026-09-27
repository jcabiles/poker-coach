# Contracts — M1b, bot settings that can differ by table size

**Bottom line:** no code that reads a bot's settings file (a "persona pack", `content/personas/*.json`)
knows the table size. The table size is known only in the live session service and the
simulation tools, one level above the pack lookup. So a 6-max override must be resolved into
"the one pack this seat uses" *before* the pack reaches the decision code; threading a
`table_size` argument into every sampler would be a far larger change. The sharpest trap is the
live session's zero-argument pack cache, which would serve one table size's values to both.

Mapped 2026-09-27 against `main` @ `7d9f575` by the `contract-mapper` agent (Sonnet); key claims
re-checked by the Director.

## 1. Pack consumers — none knows the table size

| Consumer | Where | Table size known? |
|---|---|---|
| `sample_preflop_action(pack, position, facing, hole_cards, rng, is_opener)` | `backend/app/domain/personas.py:62-111` | No — only the resolved `Position` |
| `bot_decision(state, seat, pack, rng)` | `backend/app/domain/table/play.py:234-310` | Implicitly (`len(state.seats)`), never forwarded |
| `advance_to_hero(state, seat_personas, hero_seat, rng)` | `play.py:313-351` | Same |
| `sample_postflop_decision(pack, …)` | `backend/app/domain/personas_postflop.py:1411` | No |
| `estimate_range(pack, history, seat, …)` (the villain-range view) | `backend/app/domain/table/range_estimate.py:436-459` | No |
| `preflop_raise_to` (reads `pack.sizing`) | `backend/app/domain/table/sizing.py`, called at `play.py:166` | No — per-`Position` only |

## 2. Who loads packs, at which table size

- **Live session** — `backend/app/services/sim_session.py:178-180` `_packs()`, `@cache` with **no
  arguments**: one dict for the whole process. It feeds `_seat_personas` (`:198-202`, used by the two
  `advance_to_hero` calls at `:275` and `:1089`) and the villain-range endpoint (`:1516`). The
  session's size is known in the same file (`_table_size(session)`, `:212-218`) but never reaches the
  pack lookup. Runs at both sizes.
- **`backend/tools/sixmax_baseline.py:69`** (M1's measurement tool) — 6-max only; its docstring pins
  "the raw as-loaded `load_persona_packs()`".
- **`backend/tools/export_analytics.py:359`** default path — 9-max only. `play_one_hand` (`:178`) is
  size-generic via `stacks_bb` length and takes whatever `packs` dict it is handed.
- **`backend/tools/counterfactual.py:370-372`** and six other 9-max tools; about a dozen tests call
  `load_persona_packs()` with no arguments.

## 3. Shapes and lookup rules

- **`PersonaSizing`** (`backend/app/domain/content/models.py:138-273`): three required scalars plus four
  optional mixes; `open_bb_mix_by_position` must list all nine positions. `extra="forbid"`.
- **`PersonaPostflop`** (`:303-489`): flat scalars plus two sizing dicts; nothing per position or table
  size. **Does NOT forbid extra keys** (pydantic's default ignores them) — an override that merges
  postflop keys must reject unknown names itself, or a typo is silently dropped.
- **`PersonaNode`** (`:115-135`): `facing`, `positions` (None = any seat), `role`, `mixes`. Lookup is
  first match in list order, filtered by facing; `PersonaPack._node_ordering` (`:501-539`) checks
  ordering per `(facing, role)`, so order *across* facings never affects lookup.
- **Seats:** 6-max is the 9-max rotation minus `UTG`, `UTG1`, `UTG2`
  (`backend/app/domain/table/deck.py:22-40`), leaving `BTN, SB, BB, LJ, HJ, CO`.
- `backend/tests/test_persona_pack_invariants.py::_check_position_coverage` (`:271-320`) requires every
  shipped pack to answer all nine positions for every facing it authors.

## 4. Pinned hashes and golden tests

- `counterfactual.baseline_pack_hash` / `baseline_config_hash` (`counterfactual.py:375-390, 906-916`) hash
  each pack's `model_dump(mode="json", exclude_unset=True)`; the result is stamped into every analytics
  export `run_id`. Any change to a pack file's content changes the 9-max export's hash, even if 9-max
  behaviour is unchanged.
- `content/schema/persona.schema.json` is compared byte-for-byte to `PersonaPack.model_json_schema()`
  (`backend/tests/test_preflop_size_mix.py:568-585`). Adding a field to `PersonaPack` breaks it until
  regenerated.
- **No existing test pins bot decisions against a pre-change golden output.** The byte-identical tests
  (`test_w3r1_preflop_cleanup.py:252, :350`, `test_personas_postflop.py:1079, :1469, :1836`,
  `test_export_analytics_table_size.py:74-79`) compare two paths *within* one run. The M1b check needs a
  new golden digest captured on pre-change code.

## 5. Content tooling

- `backend/tools/rr_emit.py` emits only `unopened`-facing preflop nodes from a ladder spec in
  `content/personas/ladders/` and round-trips them through `PersonaNode`. Build-time only; no notion of
  table size. `load_persona_packs` globs `content/personas/*.json` **non-recursively**, so a
  subdirectory is invisible to it.

## 6. Safe by construction

- DB rows store only `SimSeat.persona_type` (`backend/app/db/models.py:79`), never pack content: no
  migration.
- The frontend sees only persona type and display labels (`frontend/src/api/types.ts:224, 516, 565`): no
  FE type change.

## Integration risks, most severe first

1. **`sim_session._packs()`'s zero-argument `@cache`** — a size-aware loader behind it would serve
   whichever size loaded first to every session.
2. **The villain-range view** (`sim_session.py:1516`) must use the same resolved pack as the bot, or the
   range shown disagrees with how the bot plays.
3. **The sampler functions are size-blind** — resolving upstream keeps them untouched.
4. **`PersonaPostflop` ignores unknown keys** — override merges need their own unknown-key check.
5. **The nine-position coverage invariant** — a 6-max override only needs the six seated positions;
   the invariant test must not demand UTG coverage from it, nor let a 6-max gap through.
