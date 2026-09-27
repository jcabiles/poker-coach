# Tickets — M1b, bot settings that can differ by table size

status: approved (pre-authorized by --auto-build invocation, 2026-09-27) — T1–T4 are cleared to
build in order on branch `feat/m1b-table-size-settings`, and T5 is the Director's close-out. The
approval covers:
- building and running the local tests and the live-app check;
- committing to that branch, pushing it, and opening a PR.

It does **not** cover merging, shipping any 6-max override file or settings value, or starting M2
or R1.
**Baseline** (`make check` on `9d20026`, the docs-only commit on top of `main` @ `7d9f575`): recorded
at the first barrier below.
- Spec: `../specs/m1b-table-size-settings.md` (rev 2).
- Contracts: `../contracts/m1b-table-size-settings.md`.
- Ledger: `../ledger/m1b-table-size-settings.md`.

## Shape of the work

Four code tickets in a strict chain, T1 → T2 → T3 → T4, then the Director's T5. Nothing runs in
parallel, because T2 and T3 both own `test_persona_table_override.py`, and T1 must be committed
before any code changes.

- **Barrier after every ticket:** run the whole backend suite, not a name-filtered selection. Clean
  means:
  - no failure beyond the baseline;
  - no drop in the passing count;
  - T1's two digest constants unchanged since T1's commit.
- **The interpreter:** the worktree's `backend/.venv` is a symlink to the main checkout's venv.
  Run from `backend/` with `PYTHONPATH=.`.
- **No two `./scripts/verify.sh` runs at once:** it migrates the local DB.

---

### T1 — Pin a golden fingerprint of every bot decision, before any code changes
- **What:** a test that plays 360 seeded hands at each table size and compares a SHA-256 of every
  hand's full action history to a committed constant.
  - **9-max:** `export_analytics.play_one_hand` on the default 9-seat lineup, packs from
    `load_persona_packs()`.
  - **6-max:** `sixmax_baseline.run_baseline(360, seed)`.
  - **Canonical form:** JSON with sorted keys, one record per action: seat, position, street,
    action, amount.
  - Expose a helper returning the per-hand digests (spec §4) that the constants are built from.
- **Owns:** `backend/tests/test_bot_decisions_golden.py` (new).
- **Imitate:** `backend/tests/test_export_analytics_table_size.py:74-79`.
- **Done when:**
  - The test passes on unchanged code, with both hands-played counts asserted equal to 360.
  - The same digests come out of three separate processes, with `PYTHONHASHSEED` set to 0, 1 and
    12345. If they do not, stop and report the source; never loosen the fingerprint.
  - It runs in under 15 s.
  - It is committed on its own, before T2 starts.

### T2 — One home for `TableSize`, and the override file model
- **What:**
  - Move `TableSize = Literal[6, 9]` into `backend/app/domain/table/deck.py`. `schemas/simulate.py`
    then imports it instead of defining it.
  - Add `PersonaTableOverride` in a new module, with the fields and validators from spec §2:
    - `doc` with `alias="_doc"`;
    - `extra="forbid"`;
    - `sizing` keys checked against `PersonaSizing.model_fields`, and `postflop` keys against
      `PersonaPostflop.model_fields`;
    - each node's facing must equal its key, and each listed facing must be non-empty;
    - an empty override is an error;
    - `null` is allowed as a value, and the schema description says it deletes the key.
  - Generate `content/schema/persona_override.schema.json` from the model.
- **Owns:**
  - `backend/app/domain/table/deck.py`;
  - `backend/app/schemas/simulate.py`;
  - `backend/app/domain/content/persona_override.py` (new);
  - `content/schema/persona_override.schema.json` (new);
  - `backend/tests/test_persona_table_override.py` (new: model-validation tests + schema sync test).
- **Imitate:** `PersonaSizing` in `content/models.py:138-273`; the sync test at
  `tests/test_preflop_size_mix.py:568-585`.
- **Done when:**
  - `pytest tests/test_persona_table_override.py tests/test_domain_purity.py tests/test_bot_decisions_golden.py`
    passes;
  - `PYTHONPATH=. .venv/bin/mypy app` is clean;
  - `grep -rn "TableSize = " app` finds exactly one line, in `deck.py`;
  - a model test proves each validator rejects its bad case and that `_doc` is accepted.

### T3 — Merge 6-max override files in the settings loader
- **What:**
  - `load_persona_packs(content_dir=None, table_size: TableSize = 9)`. At 9 the code path is
    unchanged and never touches `six_max/`. At 6 it reads `<dir>/six_max/*.json` in sorted order
    and merges each file per spec §2:
    - an override's facing replaces every base node of that facing;
    - `sizing` and `postflop` merge key by key, and `null` deletes a key;
    - postflop keys against a base pack with no postflop block are an error;
    - the result is rebuilt through `PersonaPack.model_validate`;
    - every error names the file.
  - Parametrise `test_persona_pack_invariants.py`'s `packs` fixture over 9 and 6. Generalise
    `_check_position_coverage` to take a position set: nine positions at 9, and
    `BTN, SB, BB, LJ, HJ, CO` at 6. Run each check once more on the merged test fixture.
- **Owns:**
  - `backend/app/domain/personas.py`;
  - `backend/tests/test_persona_table_override.py` (extends);
  - `backend/tests/test_persona_pack_invariants.py`.

  Fixtures are written into `tmp_path` by the tests: the real `content/personas/*.json` copied in,
  plus `six_max/lag.json`. No fixture file is committed.
- **Tests (spec §4):**
  - liveness at 6 and base behaviour at 9 through `sample_preflop_action`;
  - `play_one_hand` with the LAG pinned to LJ, asserting a LAG decision row in every hand played;
  - `{size_elasticity: 1.0, stickiness: null}` loads without `stickiness`;
  - `{aggression: null}` fails;
  - one test per error in the spec §4 list;
  - the fixture's `_doc` loads.
- **Done when:**
  - `pytest tests/test_persona_table_override.py tests/test_persona_pack_invariants.py tests/test_bot_decisions_golden.py tests/test_domain_purity.py`
    passes;
  - mypy is clean;
  - T1's constants are unchanged;
  - `grep -n "six_max" app/domain/personas.py` shows it only inside the table-size-6 branch.

### T4 — Wire the live table and the M1 tool to the table-size loader
- **What:**
  - In `sim_session.py`:
    - `_packs(table_size: TableSize)` becomes `@cache`d per size, with no default;
    - `_seat_personas(seats, table_size)`, with no default;
    - the call sites at `:275` and `:1089` pass `_table_size(session)`;
    - the villain-range endpoint (`:1516`) reads `_seat_personas(seats, _table_size(session))[seat_index]`.
  - `sixmax_baseline.run_baseline` loads with `table_size=6`, and its module docstring's packs line
    says so.
- **Owns:**
  - `backend/app/services/sim_session.py`;
  - `backend/tools/sixmax_baseline.py`;
  - `backend/tests/test_sim_session_table_size_packs.py` (new).
- **Tests (spec §4 "Live session"):**
  - `_packs(6)` and `_packs(9)` are distinct in the call order 9, 6, 9.
  - Every villain is rewritten to the LAG and the hero folds. The loop must see at least one
    unopened LAG decision from each bot call site within a fixed cap, and every such decision is a
    fold, or a raise holding AA.
  - The villain range for a stored LAG first-in raise from LJ has classes exactly `{"AA"}` at 6-max,
    and wider at 9-max.
  - Monkeypatch `app.domain.personas.PERSONA_DIR` to the fixture folder, and clear `_packs`'s cache
    before and after.
- **Imitate:** `backend/tests/test_two_mode_simulate_gate.py` (session setup and DB helpers).
- **Done when:**
  - `pytest tests/test_sim_session_table_size_packs.py tests/test_bot_decisions_golden.py` passes;
  - the whole backend suite is clean against the baseline;
  - mypy is clean;
  - planting `_packs(9)` at the villain-range line turns the range test red. The worker reports
    this was checked, then reverts the plant.

### T5 — Close-out (Director)
- `make check` exits 0, with T1's constants unchanged since T1.
- Live app (spec §8.4): create a 6-max and a 9-max session through the API, act through one hand in
  each, and call villain-range on a live villain seat in the 6-max session. All return 200, with no
  server errors in the log.
- Whole-branch review by a fresh `refuter`, with findings added to the ledger.
- Tick M1b in the roadmap, with its assumption status. Update the profile's `## Resume`. Push the
  branch and open the PR.
