# Spec — cleanup slice 2: quality gates (`make check`)

status: **rev 2 — approved (pre-authorized by `--auto-build` invocation, 2026-09-18)**. Rev 1 was reviewed blind by a Claude refuter (APPROVE-WITH-FIXES, two blocking findings, all accepted — ledger `../ledger/cleanup-quality-gates.md`); Codex could not run (see the ledger). Rev 1 was Invoked as `/ai-org:spec --auto-build` by the
owner on 2026-09-18 (typed in that session's message); the owner pre-approved the new dev
dependencies (a Python type checker, Biome, pre-commit, uv) in the same session's picker.
slice of: `../../cleanup-project-brief.md` slice 2 (the cleanup project; the flywheel roadmap's
rev 10 header records the hand-over)
contract map: `../contracts/cleanup-quality-gates.md`
requirements source (Gate 1): the owner's brief, slice 2, plus the 2026-09-18 picker. The
owner asked not to be interviewed mid-run, so no separate playback was held; every choice
below that the brief leaves open is marked *Director's call* and is reversible in review.

## Bottom line

One command, `make check`, runs format check + lint + type check + tests for both halves of
the monorepo and is the only definition of "done" — locally, in CI, and for every agent. It
must pass on the day it lands, which means the backend gets formatted once, its ~337 type
errors get fixed where the fix is one pattern and baselined per module where it is not, and the
frontend gets Biome with its accessibility findings kept visible as warnings rather than
silenced. Nothing about app behaviour changes.

Gain: every later PR is gated by the same command; no more three disagreeing definitions of
"passing". Cost: two large mechanical commits (backend reformat, frontend reformat) that make
`git blame` noisier on that day, and about eight minutes per full `make check` because the
backend suite already costs that.

## Goal

Add a canonical, passing `make check` to the repo, with a backend lockfile, a Python type
checker, a frontend linter/formatter, and pre-commit wiring, and point every existing
definition of "the checks" at it.

## Shape considered (Director's call, recorded so review can challenge it)

1. **Makefile at the root calling per-side targets** — chosen. Portable, no new runtime, and
   `make check-backend` / `make check-frontend` give CI two jobs from one source of truth.
2. A `scripts/check.sh` instead of make — rejected: the brief names `make check`, and make
   gives named targets for free.
3. A task runner (`just`, `nox`, npm-scripts-at-root) — rejected: a new dependency for no gain.

## Behaviour

### The Makefile

1. Root `Makefile` with targets: `check` (= `check-backend check-frontend`), `check-backend`
   (= `fmt-check-backend lint-backend typecheck-backend test-backend`), `check-frontend`
   (= `fmt-check-frontend lint-frontend typecheck-frontend test-frontend build-frontend`),
   the leaf targets those expand to, and `fix` (= `ruff format` + `ruff check --fix` +
   `biome check --write`). `.PHONY` throughout. Every leaf target runs from its side's
   directory using the repo's existing binaries (`backend/.venv/bin/...`, `frontend/node_modules/.bin/...`).
2. `test-backend` runs `./scripts/verify.sh` unchanged (pytest plus the boot probe), so the
   probe finally becomes part of "the checks". It is never invoked concurrently with itself.
3. `test-frontend` runs `vitest run`; `build-frontend` runs `vite build` — both already exist.
4. `make check` exits non-zero on the first failing target and prints which one.

### Backend: format

5. `ruff format --check .` becomes a gate (`fmt-check-backend`). One mechanical commit applies
   `ruff format .` to the backend once. `alembic/versions` stays excluded as it is today.
   Semantics-preserving by construction; the full suite proves it.

### Backend: type check

6. `mypy app` becomes a gate (`typecheck-backend`), configured in `pyproject.toml`
   `[tool.mypy]`: `python_version = "3.12"`, `warn_unused_ignores`, `warn_redundant_casts`,
   `check_untyped_defs`, `no_implicit_optional`, `ignore_missing_imports` **only** for
   third-party modules that ship no stubs (each listed by name in `[[tool.mypy.overrides]]`,
   not globally). Not `--strict` in this slice.
7. **Fix, don't baseline, the two dominant patterns**, which live in `app/domain/postflop.py`
   and `app/domain/table/grade_map_postflop.py`: `map_fail()` called with a possibly-None
   reason (45 sites — narrow the type at the call site or make the parameter Optional and
   handle None once, whichever the code's behaviour already is), and `EvaluationResult(**dict)`
   unpacking (**210 errors across 20 call sites** — build the result with explicit keyword
   arguments or a `TypedDict`; rev 1 understated this by half). Fix the two malformed
   `# type: ignore` comments in `table/range_estimate.py`. The errors in
   `services/sim_session.py` (33), `domain/personas_postflop.py` (31) and `domain/scenarios.py`
   (12) are **not** these patterns — they are SQLAlchemy column-expression and Optional
   propagation through session code — and are **baselined per §8 in this slice**, not fixed;
   a fix there is only allowed when it is a pure annotation change with no runtime effect, and
   the worker reports each one.
8. **Baseline the rest per module**, not per line and not globally: a `[[tool.mypy.overrides]]`
   block per module that still fails, with `ignore_errors = true` and a comment
   `# BASELINE(2026-09-18): <n> errors, <reason>`. The baseline list is reported in the PR and
   recorded in the ledger. No `# type: ignore` sprinkled across files to get green.
9. The domain purity test and every behaviour test stay green; a type fix that changes
   runtime behaviour is a defect (**especially** in `backend/tools/export_analytics.py`, whose
   output is a cross-repo contract).

### Backend: lockfile

10. The `dev` extra in `pyproject.toml` gains `mypy` and `pre-commit` (pinned with `>=` floors
    like its neighbours; the lock pins them exactly), so a clean `uv sync --locked --extra dev`
    installs everything `make check-backend` runs. `backend/uv.lock` is then generated with
    `uv lock --python 3.12` (CI's interpreter; the lock also resolves for the venv's 3.14 since
    `requires-python >= 3.12`) and committed. `pyproject.toml` gains `[tool.uv]` only if needed. CI installs with `uv sync --locked --extra dev`
    via `astral-sh/setup-uv`, so the lock is load-bearing rather than decorative. Local setup
    docs mention `uv sync` as the preferred path and keep `pip install -e ".[dev]"` as the
    fallback.

### Frontend: lint + format

11. `frontend/biome.json` (Biome 2.x, pinned exact in `devDependencies`): formatter 2-space,
    double quotes, semicolons always, line width 100 (matches the visible convention and
    `.editorconfig`); linter `recommended`; `files.includes` = `src/**`. `src/api/types.ts` is
    linted and formatted like any other source (it is hand-written, not generated).
12. One mechanical commit applies `biome check --write src` (format + safe fixes) once.
13. `biome ci src` becomes the gate (`lint-frontend` + `fmt-check-frontend`), and it must pass
    with **zero errors**. Rules that still fail after safe fixes are handled in this order:
    fix if the fix is mechanical and behaviour-neutral (`useButtonType`, `useConst`,
    `useOptionalChain`, `useTemplate`); otherwise **downgrade to `warn`** in `biome.json` with a
    `// BASELINE(2026-09-18)` comment — this covers the accessibility rules
    (`useSemanticElements`, `useAriaPropsSupportedByRole`, `useFocusableInteractive`,
    `noAriaHiddenOnFocusable`, `noSvgWithoutTitle`), `noArrayIndexKey`,
    `noNonNullAssertion`, `useExhaustiveDependencies`, and `noDescendingSpecificity` (CSS).
    Warnings stay visible on every run; nothing is set to `off`.
14. No JSX or CSS change that alters rendering: the a11y findings are real product work for a
    later slice, not this one. The design tokens invariant is untouched.

### Pre-commit and CI

15. `.pre-commit-config.yaml` with **local** hooks only (no network-fetched hook repos):
    `ruff format --check`, `ruff check`, `biome ci` on staged files, plus `end-of-file-fixer`
    and `trailing-whitespace` equivalents. Type checks and tests are `make check` only (too
    slow for a commit hook). The owner installs it with `backend/.venv/bin/pre-commit install`;
    the README says so.
16. `.github/workflows/ci.yml` keeps two jobs but each becomes one step: `make check-backend`
    (after `setup-uv` + `uv sync --locked --extra dev`) and `make check-frontend` (after
    `npm ci`). CI and local therefore run the identical definition.

### Documentation and profile

17. `README.md` "Checks" block → `make check` (with the per-side targets listed once).
    `.claude/CLAUDE.md` Commands → the same. `docs/ai-dlc/profile.md` `verify:` → `make
    check` as the canonical gate with the leaf targets beneath it; the stale
    `backend/app/services/grading.py` hotspot corrected to `backend/app/domain/grading.py`.
18. `docs/ai-dlc/profile.md` gains a `conventions:` block naming one golden-path file per kind
    of thing: route (`backend/app/api/v1/simulate.py`), schema (`backend/app/schemas/simulate.py`),
    service (`backend/app/services/sim_session.py`), domain provider
    (`backend/app/domain/providers/turn.py`), migration
    (`backend/alembic/versions/0015_sim_session_mode.py`), backend test
    (`backend/tests/test_two_mode_simulate_gate.py`), React component
    (`frontend/src/components/simulate/SimGradingToggle.tsx`), pure FE module + test
    (`frontend/src/components/simulate/handCount.ts` / `.test.ts`).

## Files and interfaces to touch

- New: `Makefile`, `backend/uv.lock`, `frontend/biome.json`, `.pre-commit-config.yaml`.
- Edit: `backend/pyproject.toml` (`[tool.mypy]`, overrides; `uv` dev extra if needed),
  `frontend/package.json` + `package-lock.json` (Biome, `lint`/`format` scripts),
  `.github/workflows/ci.yml`, `README.md`, `.claude/CLAUDE.md`, `docs/ai-dlc/profile.md`.
- Mechanical, one commit each: `backend/**/*.py` via `ruff format`; `frontend/src/**` via
  `biome check --write`.
- Type fixes: `backend/app/domain/postflop.py`, `table/grade_map_postflop.py`,
  `table/range_estimate.py`, and whichever smaller modules those fixes reach. Baselined
  (config only, no edits): `services/sim_session.py`, `domain/personas_postflop.py`,
  `domain/scenarios.py`, plus any small module whose remaining errors are not the two
  patterns.
- Also in scope: `docs/ai-dlc/ledger/cleanup-quality-gates.md`, `docs/ai-dlc/log.md`,
  `docs/cleanup-project-brief.md` (tick slice 2), this spec.

## Out of scope

Cleanup slice 1 (docs distillation) and slice 3 (code findings: the test-file split, stale root
files, README Status rewrite, `backend/tools` smoke tests) · any accessibility or rendering
change in JSX/CSS · `--strict` mypy · type-checking `backend/tests/` and `backend/tools/`
(reported as a follow-up with their error counts) · CODEOWNERS or branch protection · changing
what `scripts/verify.sh` probes.

## Constraints

Every repo invariant in `docs/ai-dlc/profile.md` holds; in particular the domain purity test,
`spot_signature()`, the frozen `content/` values, and design-tokens-only CSS. No new runtime
dependency; only the four pre-approved dev dependencies. A type fix never changes behaviour.
Baselines carry the `BASELINE(2026-09-18)` marker and a reason.

## Golden paths to imitate

| New thing | Imitate |
|---|---|
| Makefile leaf targets | the commands in `scripts/verify.sh` and `README.md` Checks, verbatim |
| CI job steps | the existing two-job layout in `.github/workflows/ci.yml` |
| mypy overrides | `[tool.ruff]` block style already in `pyproject.toml` |
| Biome config | `.editorconfig` values |

## Known traps

- `scripts/verify.sh`'s boot probe migrates the real local DB; never run two at once.
- `PYTHONPATH=.` is mandatory when running backend commands from a worktree, or the main
  checkout's source is exercised instead.
- In this sandbox `pip` needs `--use-deprecated=legacy-certs --cert <bundle>`; `uv` needs
  `SSL_CERT_FILE=<bundle>`; the bundle can be dumped from Node's `tls.rootCertificates`.
- `frontend/node_modules` in a worktree is a symlink to the main checkout's; installing Biome
  there installs it for both.
- The venv is Python 3.14 while CI is 3.12; the lock must resolve for both (`requires-python`).

## Verify by

1. `make check` exits 0 from a clean checkout of the branch (this is the whole point).
2. `make check-backend` alone and `make check-frontend` alone exit 0.
3. Backend suite count unchanged from the branch base (2239 passed / 2 skipped) after the
   reformat and the type fixes; `./scripts/verify.sh` prints `BACKEND VERIFY OK`.
4. Frontend: `biome ci src` zero errors; `tsc --noEmit`, `vitest run` (60), `vite build` green.
5. `git diff --stat` of the reformat commits touches only `*.py` / `src/**` respectively.
6. `uv sync --locked --extra dev` succeeds into a fresh temporary venv (proves the lock).
7. `pre-commit run --all-files` passes.
8. `README.md`, `.claude/CLAUDE.md`, `docs/ai-dlc/profile.md` all name `make check` and none
   still names the stale grading hotspot.

## Definition of done

Every item in Verify-by passes · `make check` is green on the branch · nothing outside the
files named above changed · every baseline is marked and listed in the ledger and the PR ·
the three docs that defined "the checks" now all point at `make check` · slice 2 is ticked in
`docs/cleanup-project-brief.md`.
