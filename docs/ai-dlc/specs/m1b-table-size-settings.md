# Spec — M1b, let bot settings differ by table size (rev 1, 2026-09-27)

**Bottom line:**
- **What gets built:** a bot can carry 6-max-only values in a small separate file,
  `content/personas/six_max/<bot>.json`, holding only what differs. At 6 seats that file is
  merged over the bot's normal settings file; at 9 seats it is never opened.
- **What changes in play:** nothing. No 6-max file ships in this slice, so every bot plays exactly
  as today at both table sizes, and a golden fingerprint captured before the change proves it.
- **Why:** M2 (the LAG retune) needs a place to put 6-max values without touching 9-max.

- **Roadmap:** `../roadmap/bot-realism-6max.md`, slice M1b. Pass/fail: 9-max bot decisions
  byte-identical on a fixed seed set, and one 6-max override proved live by a test. No settings
  values change.
- **Contracts:** `../contracts/m1b-table-size-settings.md`.
- **Owner decisions (2026-09-27, do not re-ask):**
  - 6-max values live in **separate override files**, not in a block inside each settings file,
    not in per-rule table-size tags, and not in full copies.
  - An override may replace **all preflop rules for a named situation** (a "facing", e.g.
    `unopened`) and **any single sizing or post-flop dial**. Nothing finer (no per-rule patches).
  - The golden fingerprint covers **both** table sizes, beyond the roadmap's 9-max-only check.
- Review: `../ledger/m1b-table-size-settings.md`.

## 1. What changes

| File | Change |
|---|---|
| `backend/tests/test_bot_decisions_golden.py` (new) | The golden fingerprint, written and passing on **unchanged** code first (T1). |
| `backend/app/domain/content/persona_override.py` (new) | `PersonaTableOverride`, the model for one override file. Its own module because `content/models.py` is already 558 lines. |
| `content/schema/persona_override.schema.json` (new) | Generated from `PersonaTableOverride.model_json_schema()`; kept in sync by a test. |
| `backend/app/domain/personas.py` | `load_persona_packs(content_dir=None, table_size=9)`; a private merge function. |
| `backend/app/services/sim_session.py` | `_packs(table_size)` and `_seat_personas(seats, table_size)`, both with the size **required**; the two `advance_to_hero` call sites (`:275`, `:1089`) and the villain-range endpoint (`:1516`) pass the session's size. |
| `backend/tools/sixmax_baseline.py` | Loads with `table_size=6`; its docstring line about packs is updated to match. |
| `backend/tests/test_persona_table_override.py` (new) | Model, merge, error and liveness tests; the schema sync test. |
| `backend/tests/test_persona_pack_invariants.py` | 6-max coverage check over every shipped override file and over the test fixture. |
| `backend/tests/test_sim_session_table_size_packs.py` (new) | Live-session wiring tests. |
| `docs/ai-dlc/roadmap/bot-realism-6max.md` | Tick M1b when its pass/fail holds; record the assumption's status. |

## 2. Rules and the one module that owns each

- **The override file format is owned by `content/persona_override.py`** (`PersonaTableOverride`):
  - Fields: `id: str`, `version: str`, `domain: Literal["persona_override"]`,
    `persona: VillainType`, `table_size: Literal[6]`,
    `preflop: dict[PersonaFacing, list[PersonaNode]]` (default empty),
    `sizing: dict[str, Any]` (default empty), `postflop: dict[str, Any]` (default empty).
  - A `_doc` list of strings is accepted, the same convention the settings files use, because M2
    must cite a source for every value it authors. **Every other unknown top-level key is an
    error** (`extra="forbid"`).
  - **Every `sizing` key must name a `PersonaSizing` field and every `postflop` key a
    `PersonaPostflop` field**, checked against `model_fields`. This check is required because
    `PersonaPostflop` silently ignores unknown keys, so a misspelled dial would otherwise do
    nothing without any error.
  - **Each preflop node's `facing` must equal the key it is listed under,** and each listed facing
    must carry at least one node.
  - **An override that changes nothing** (all three maps empty) is an error.
- **Loading and merging are owned by `personas.py`:**
  - `load_persona_packs(content_dir=None, table_size=9)`, where `table_size` is `Literal[6, 9]`
    defined in the domain. `app/schemas/simulate.TableSize` must not be imported, because the
    domain may not import the web layer.
  - **At 9:** exactly today's code path. The `six_max/` directory is never listed or read.
  - **At 6:** load the base packs as today, then read `<content_dir>/six_max/*.json` in sorted
    order. A missing directory means no overrides. It is an error if two files name the same
    persona, or if a file names a persona with no base pack.
  - **The merge,** per override:
    - Start from `pack.model_dump(mode="json", exclude_unset=True)`.
    - For each facing in `preflop`, drop every base node with that facing and append the
      override's nodes in the order given. Lookup filters by facing first, so where they sit
      relative to other facings never changes a decision.
    - Update `sizing` and `postflop` key by key; any other key is left untouched.
    - Rebuild with `PersonaPack.model_validate`, so every existing validator runs on the merged
      result: node ordering, weight sums, and the nine-position completeness of
      `open_bb_mix_by_position`. That means an override replacing that mix must still list all
      nine positions. A failure raises at load, naming the override file.
  - The merged pack keeps the base pack's `id` and `version`.
- **The live session's cache is owned by `sim_session._packs(table_size)`:** `@cache` keyed by
  size, so the two sizes are two cached dicts. There is no default argument, because a silent 9
  at a 6-max call site is the failure this slice exists to prevent. The villain-range endpoint
  reads its pack through `_seat_personas(seats, _table_size(session))[seat_index]`, the same
  function the bots use, so the two cannot drift apart.
- **6-max coverage** is checked by `test_persona_pack_invariants.py`, using
  `_check_position_coverage` generalised to take the positions to check. For every shipped
  override (none today) and for the test fixture, the merged 6-max pack must answer every facing
  and role it authors at the six seated positions `BTN, SB, BB, LJ, HJ, CO`. The nine-position
  check on base packs is unchanged.

## 3. Contracts this slice changes, and how their dependents stay correct

- **`load_persona_packs` signature:** the new argument is additive with default 9. All ~20 existing
  zero-argument callers (tools, tests) keep today's behaviour with no edit. Only
  `sixmax_baseline.py` switches to 6.
- **`sim_session._packs` / `_seat_personas`:** private, and the size becomes required. All three
  in-file call sites are updated in the same ticket; `grep -n "_packs()\|_seat_personas(" ` must
  find no zero-size call.
- **`sixmax_baseline.py` docstring contract** ("packs are the raw as-loaded
  `load_persona_packs()`"): reworded to "`load_persona_packs(table_size=6)`: the base packs with
  any 6-max override merged". M1's report numbers stay valid, because no override ships.
- **New content type:** its schema file is generated from the model and pinned by a sync test,
  mirroring `test_checked_in_persona_schema_matches_the_model`. `persona.schema.json` is untouched,
  because `PersonaPack` does not change.
- **Unchanged by construction:** `PersonaPack` and every base settings file; the 9-max analytics
  hash (`counterfactual.baseline_pack_hash`), which never sees the override directory; DB rows
  (they store persona type only), so no migration; frontend types.

## 4. Test seams

- **Golden fingerprint (T1), observed at the full-hand playout:**
  - **9-max:** 360 hands through `export_analytics.play_one_hand` on the default 9-seat lineup,
    with packs from `load_persona_packs()`, one fixed seed.
  - **6-max:** 360 hands through `sixmax_baseline.run_baseline(360, seed)`.
  - **The fingerprint** is the SHA-256 of a canonical JSON of every hand's full action history:
    seat, position, street, action and amount, in order. Each size's hex digest is committed as a
    constant.
  - It is captured on unchanged `main` code, and the constants must not change for the rest of the
    slice.
  - **Before committing, the worker proves the digest is stable across three separate Python
    processes** with different `PYTHONHASHSEED` values. If it is not, the worker reports the
    source of the non-determinism and stops, and does not weaken the fingerprint.
  - Runtime target: under 15 s for both sizes together.
- **Merge and liveness, at the loader and sampler, with real files.** Tests copy the real
  `content/personas/*.json` into `tmp_path` and add a fixture `six_max/lag.json` that:
  - replaces the LAG's `unopened` nodes with one wildcard node whose only mix is `AA`, weight
    `raise: 1.0`, so every other hand class folds with no random draw;
  - sets one post-flop dial (`aggression`) to a value different from the base.
  - **Assert:**
    - At 6, the LAG raises only `AA` unopened from LJ, reached through `sample_preflop_action` on
      the merged pack, and `postflop.aggression` equals the override value.
    - At 9, the LAG from the same folder equals the base pack loaded from `content/personas` with
      no override, and opens many classes from LJ.
    - At 6, a hand played with `play_one_hand` on the fixture packs shows the LAG's first action
      in an unopened pot is a fold unless it holds AA.
- **Errors, one test each:** unknown sizing key; unknown postflop key; unknown top-level key; facing
  mismatch; empty override; duplicate persona; persona with no base pack; a merged pack that fails
  `PersonaPack` validation; `table_size` not 6 or 9.
- **Live session:** point `app.domain.personas.PERSONA_DIR` at the fixture folder (monkeypatch;
  real files, not a mock) and clear `sim_session._packs`'s cache before and after.
  - **Assert:**
    - `_packs(6)` carries the override and `_packs(9)` does not, in the call order 9, 6, 9.
    - A 6-max session created through the service plays hands whose LAG unopened decisions obey
      the override.
    - The villain-range endpoint serves a 6-max session without error.
  - Session creation follows `backend/tests/test_two_mode_simulate_gate.py`.

## 5. Golden paths to imitate

- **Content model with validators:** `PersonaSizing` in `backend/app/domain/content/models.py:138-273`.
- **Schema sync test:** `backend/tests/test_preflop_size_mix.py:568-585`.
- **Backend test style and session setup:** `backend/tests/test_two_mode_simulate_gate.py`.
- **Determinism test shape:** `backend/tests/test_export_analytics_table_size.py:74-79`.

## 6. Out of scope

- **Content:** any shipped 6-max override file, and any settings value.
- **Code:** the decision code (`sample_preflop_action`, `personas_postflop`, `play.py`,
  `range_estimate.py`, `sizing.py`); the 9-max tools; teaching `rr_emit.py` to write into override
  files (M2 can paste emitted nodes).
- **Other layers:** the frontend and the database.
- **Rules left alone:** overrides for other table sizes, and relaxing the nine-position rule for
  `open_bb_mix_by_position`.

## 7. Constraints

- The domain core (`backend/app/domain/`) imports nothing from the web or DB layers; this is
  test-enforced.
- Strategy stays in versioned `content/` data; override files carry `id` and `version`.
- `spot_signature()` is frozen and untouched.
- No new dependency.
- Keep files under ~500 lines; do not grow `content/models.py`.
- No error swallowing: every override problem raises with the file name.
- Tests use real objects and real files; mock nothing.

## 8. Verify by

1. `make check` exits 0.
2. The golden test passes with its T1 constants unchanged (`git diff` of the two constants since
   T1 is empty).
3. `grep -rn "six_max" backend/app` shows the directory read only inside the table-size-6 branch of
   `load_persona_packs`.
4. Live app: `./scripts/serve.sh start`, then:
   - create a 6-max session and a 9-max session (`POST /api/v1/simulate/session`);
   - act through one hand in each;
   - call `GET /api/v1/simulate/{id}/villain-range/{seat}` on a live villain seat in the 6-max
     session.
   - All return 200, with no server errors in the log.

## 9. Definition of done

Done means all of the following:
- every acceptance criterion in the tickets passes;
- `make check` exits clean;
- the golden constants are unchanged since T1;
- nothing outside §1's file list changed;
- the roadmap is ticked with M1b's assumption status recorded.

No check here depends on a device or OS that cannot be run locally.
