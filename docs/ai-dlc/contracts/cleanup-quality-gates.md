# Contract map — cleanup slice 2: quality gates

Scanned 2026-09-18 by a read-only contract-mapper (Sonnet) and checked by the Director. This
records what already defines "passing" in this repo and what would break if the commands moved.

## Bottom line

Three different definitions of "the checks" already exist and disagree, and none is a single
command. A root `make check` must reconcile them, not add a fourth. The tests are DB-isolated
except one guarded file, so nothing here needs to change how tests run. Every linter, formatter
and type checker this slice adds is greenfield: no config of any kind exists today.

## 1. Existing check definitions (all must converge on `make check`)

| Where | What it runs | Notes |
|---|---|---|
| `README.md` "Checks" block | `./scripts/verify.sh` · `cd backend && ruff check .` · `cd frontend && npm run typecheck && npm run build` | human-facing |
| `.claude/CLAUDE.md` Commands + `docs/ai-dlc/profile.md` `verify:` | same three, keyed `test` / `lint` / `build` | agent-facing; `verify:` is read by the ai-org skills |
| `.github/workflows/ci.yml` | backend: `pip install -e ".[dev]"`, `ruff check .`, `pytest -q` · frontend: `npm install`, `npm run typecheck`, `npm run build` | **narrower** than the docs: no boot probe, no frontend tests (`vitest` exists with 60 tests), `npm install` not `npm ci` |
| `scripts/verify.sh` | `pytest -q` then a live FastAPI boot probe printing `BACKEND VERIFY OK` | not run in CI at all; the probe runs `alembic upgrade head` against `backend/data/poker_coach.db` (the real local DB) — so it must never run concurrently with itself |

Consumers that grep or cite these strings: `docs/ai-dlc/profile.md:18-22`, `.claude/CLAUDE.md`
Commands section, `README.md`, and the `/ai-org:*` skills that read `<profile.verify>`. All are
documentation; nothing parses `BACKEND VERIFY OK` mechanically.

## 2. Test suite shape

- ~2,239 backend tests; `pytest -q` takes ~8 minutes on this machine, of which
  `tests/test_personas_postflop.py` (12.5k lines) is the largest single cost.
- DB-touching tests build a `tmp_path` SQLite engine and override `get_session`
  (`tests/test_simulate_api.py:25,34`, `test_sim_leaks.py:28,135`, `test_review.py:16`).
  The one exception, `tests/test_detection_probe.py:66-72`, opens the real
  `backend/data/poker_coach.db` and a gitignored deck, and is `skipif`-guarded.
- Frontend: `vitest run`, 6 files, 60 tests, under a second.

## 3. Type-checking surface (backend)

- No mypy/pyright config anywhere. 68 modules, ~17.3k lines under `backend/app/`.
- `mypy app --ignore-missing-imports` (mypy 2.3.1, venv Python 3.14): **~337 errors**, of which
  295 are `[arg-type]`, clustered: `app/domain/postflop.py` 210, `table/grade_map_postflop.py`
  47, `services/sim_session.py` 33, `domain/personas_postflop.py` 31, `domain/scenarios.py` 12.
  Two dominant patterns: `map_fail(reason)` called with `RejectReason | None` (45 sites) and
  `EvaluationResult(**dict[str, object])` unpacking (210 errors across 20 call sites — corrected 2026-09-18 from an earlier "~100" estimate). Two
  `[syntax]` errors are malformed `# type: ignore` comments in `table/range_estimate.py`.
- `--strict`: 455 errors in 33 files.
- Python: `.venv` is 3.14.7; CI pins 3.12; `requires-python >= 3.12`.

## 4. Frontend lint/format surface

- `tsconfig.json` is already strict (`strict`, `noUnusedLocals`, `noUnusedParameters`).
- No ESLint/Prettier/Biome config. `.editorconfig` at root: 2-space for ts/tsx/json/css/md.
- 47 `.ts`/`.tsx` files. Visible convention: semicolons, double quotes (84 vs 6 in `App.tsx`).
- Biome 2.5.14 on `src/`: **57 formatting diffs; 92 lint errors** (a11y 45: `useSemanticElements`
  20, `useAriaPropsSupportedByRole` 13, `useButtonType` 5, `useFocusableInteractive` 3,
  `noAriaHiddenOnFocusable` 3, `noSvgWithoutTitle` 1; `useTemplate` 51 infos;
  `noArrayIndexKey` 26; `noDescendingSpecificity` 18 in CSS; `noNonNullAssertion` 15;
  `useExhaustiveDependencies` 6).
- `frontend/src/api/types.ts` is hand-maintained by contract; `gen:api` exists but
  `schema.d.ts` is unwired — a linter must not treat `types.ts` as generated.

## 5. Dependencies and lockfiles

- Backend: `>=` floors only, no lockfile. `uv lock --python 3.12` resolves 31 packages in the
  sandbox (tested 2026-09-18, needs a CA bundle passed via `SSL_CERT_FILE` because `*.pem`
  reads are sandbox-denied).
- Frontend: `package-lock.json` exists; CI runs `npm install`, not `npm ci`.
- Sandbox: `npm install` from the registry now works (tested 2026-09-18, Biome installed);
  `pip` works only with `--use-deprecated=legacy-certs --cert <bundle>`.

## 6. Integration points that would break if commands move

- `.claude/CLAUDE.md`, `docs/ai-dlc/profile.md` `verify:`, `README.md` — must be updated in the
  same change (definition of done).
- `docs/ai-dlc/profile.md:29` and `.claude/CLAUDE.md` name `backend/app/services/grading.py`
  as a hotspot; **that file does not exist** — grading lives at `backend/app/domain/grading.py`.
  Stale pointer, fix in passing.
- `backend/tools/export_analytics.py` is the producer side of a cross-repo data contract
  (`poker_events.odcs.yaml` in poker-analytics); a formatter may touch it, a type fix must not
  change its output shape.

## 7. Out of this slice's scope, noted for slice 3

`RUN-THESE-COMMANDS.md` and `s3-build-handoff.md` exist at the repo root and are stale;
deleting them is cleanup slice 3 and needs the owner's per-file approval.
