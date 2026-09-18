# Adversarial review — cleanup slice 2: quality gates (`make check`)

## Bottom line

Approve. I tried to break this branch (5 commits, ~7100 insertions across 158 files, adding a
root `make check` gate: backend `ruff format`, mypy with per-module baselines, a `uv.lock`,
frontend Biome, a Makefile, local pre-commit hooks, and CI/docs updates) and could not find a
behavior change, a dishonest baseline, or a broken gate. The highest-risk claim — that the
"type-only" backend edits changed no runtime behavior — is proven, not just eyeballed: I
AST-diffed every changed `.py` file in `backend/app/` and `backend/tools/` against the base
commit. Of 20 changed files in `app/`, only the three the spec named as touched for the pattern
fix (`postflop.py`, `table/grade_map_postflop.py`, `table/grade_map_reject.py`) have any AST
difference at all, and that difference is exactly type annotations (a `TypedDict`, two
`Optional` widenings that match the fields' already-Optional declared types). All 16 changed
files in `backend/tools/` are AST-identical to base — pure `ruff format` reformatting.

## What I checked

- **Deterministic gates**: `mypy app` → 0 errors; `ruff check .` → clean; `ruff format --check .`
  → 185 files already formatted; `uv lock --check` → resolves with no drift (had to set
  `UV_CACHE_DIR` inside the sandbox, `~/.cache/uv` is write-denied there); `biome ci src` and
  `biome format src` both exit 0, and both correctly fail (exit 1) when I injected an
  unformatted line into a real file, then I restored it and re-verified clean. `make -n check`
  dry-run matches the Makefile's leaf targets 1:1. Both `.github/workflows/ci.yml` and
  `.pre-commit-config.yaml` parse as valid YAML.
- **Backend type-only edits** (the brief's top risk): `map_fail()`'s parameter widened from
  `RejectReason` to `RejectReason | None` — the field it constructs (`MapResult.reason`) was
  *already* `RejectReason | None`, and the one call site that needed it (`map_fail(gate.reason)`
  in `grade_map_postflop.py`) passes a value mypy can't narrow across the tuple unpack even
  though it's never actually None on that path. Confirmed via AST diff: no control-flow change.
  `_faced_bet_spot`/`_barrel_spot`'s `hero_range`/`villain_range` params widened from `str` to
  `str | None` — again matches `Spot.hero_range`'s already-Optional field type; every call site
  passes ranges only after an `if ranges is None: return map_fail(...)` guard, so no None
  actually flows through. The `_BaseEvalKwargs` `TypedDict` is a pure annotation on
  `base_kwargs` in eight graders, no runtime effect.
- **Frontend by-hand fixes**: no `<form>` element exists anywhere in `frontend/src`, so all five
  `type="button"` additions are inert (nothing to prevent submitting). `Home.tsx`'s
  `recap && recap.day` → `recap?.day` and `SimVillainRange.tsx`'s `range != null && range.available
  && !range.exact` → `range?.available && !range.exact` are truthiness-equivalent (verified by
  hand: both short-circuit to a falsy value under the same null/undefined condition, and the
  only consumer in each case is a `{cond && (...)}` JSX gate where `undefined` and `false`
  render identically). The `forEach` block-body rewrite and the `||=` → `if (!x) x = []` split in
  `rangeGroups.ts` are behaviorally identical (verified: `||=` treats an existing empty array as
  truthy, same as the explicit `if`).
- **CSS**: diffed `app.css` and `tokens.css` line-by-line; every changed line is re-wrapping of
  the identical value (`radial-gradient`/`linear-gradient` args, `transition` shorthand,
  `font-mono` stack) — no design-token value changed, no selector added/removed.
- **CI correctness**: `astral-sh/setup-uv@v6` with `python-version: "3.12"` is a real, documented
  input on that action version. `uv sync --locked --extra dev` runs with
  `working-directory: backend`, so it creates `backend/.venv`, which is exactly where the
  Makefile's `$(BACKEND)/.venv/bin/...` and `scripts/verify.sh`'s `.venv/bin/python` (run after a
  `cd` into `backend/`) expect it. `npm ci` against the edited lockfile is unremarkable (Biome +
  three new npm scripts only).
- **mypy baselines**: all ten `[[tool.mypy.overrides]]` blocks carry a dated
  `# BASELINE(2026-09-18)` comment with an error count and a real reason, `ignore_errors = true`
  per module (never per-line, never global), and `mypy app` is clean with them in place — I ran
  it myself. One number is stale: the spec's rev-2 text still says
  `domain/personas_postflop.py (31)` errors, but the shipped baseline (and the ledger's
  burn-down table) both say 17 — a leftover from an earlier estimate, not a live discrepancy
  (see Issue 1).
- **Biome baselines**: nine rules at `warn`, every one dated and reasoned, none set to `off`;
  the list matches the spec's §13 table and the ledger's burn-down table exactly.
  `files.includes: ["src/**"]` does not exclude anything that should be linted — the frontend's
  test files live under `src/` too, and I confirmed `biome ci` reaches a `*.test.ts` file's
  formatting.
- **Docs**: README's `Checks` block, `.claude/CLAUDE.md`'s `Commands` section, and
  `docs/ai-dlc/profile.md`'s `verify:` block all name `make check` and list the same leaf
  targets, cross-checked literally against the Makefile and `package.json`'s scripts (`lint`,
  `format`, `check` all point at the same `biome` invocations the Makefile uses directly). The
  `CLAUDE.md` dev-stack line's frontend port also changed from a stale `:5173` to `:7777` in the
  same edit — confirmed against `vite.config.ts` (`port: 7777`) and `scripts/serve.sh`
  (`FRONTEND_PORT:-7777}`), i.e. it corrects a pre-existing stale value rather than introducing a
  new inconsistency. The stale `services/grading.py` hotspot is corrected to
  `domain/grading.py`, and I confirmed the file exists at the new path. Every file named in the
  new `conventions:` block in `profile.md` exists on disk.
- **Scope**: `git diff --stat` shows only the files the spec's "Files and interfaces to touch"
  list and its ticket allow — the `backend/tools/*.py` reformatting is a direct, expected
  consequence of `ruff format .` running over the whole backend (spec §5 doesn't exclude
  `tools/`), and AST-diffing confirmed zero semantic change there.

## Issues found

1. (optional) `docs/ai-dlc/specs/cleanup-quality-gates.md` lines 76/155 still say
   `domain/personas_postflop.py (31)` errors; the shipped baseline in `pyproject.toml` and the
   ledger's burn-down table both say 17. Cosmetic — the config file is the source of truth and it
   is internally consistent with the ledger, mypy runs clean, and nothing downstream reads the
   spec's number programmatically. Cost of fixing: one line edit to the spec; no behavior is
   affected either way.

No blocking or should-fix findings.
