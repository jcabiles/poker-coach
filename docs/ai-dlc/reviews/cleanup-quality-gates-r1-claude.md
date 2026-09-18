# Review — cleanup slice 2: quality gates (r1, Claude)

Reviewer: fresh adversarial pass, read-only. Verdict: **APPROVE-WITH-FIXES**.

## Bottom line

The baseline numbers in the contract map check out against the live tools (mypy: 337 errors,
same file clustering; Biome: 149 errors matching the claimed 57 format + 92 lint split), so the
plan's premise is sound. Two things must be fixed before build: (1) the spec never says to add
`mypy` and `pre-commit` as declared dev dependencies in `backend/pyproject.toml`, so
`uv sync --locked --extra dev` in CI would not install the mypy binary and `make check-backend`
would fail on a clean checkout — this breaks the plan's own point-1 verify-by step. (2) the
"Files to touch" list puts `services/sim_session.py`, `domain/personas_postflop.py`, and
`domain/scenarios.py` under "type fixes" (implying real edits), but every one of their ~76 mypy
errors is unrelated to the two named mechanical patterns (map_fail / EvaluationResult) — they are
SQLAlchemy where-clause and Optional-handling errors in session/DB code, exactly the kind of
non-mechanical fix item 9 warns against and item 8 says to baseline instead. The spec contradicts
itself about whether these three files get fixed or baselined, and if built as "fix" it risks
behaviour changes in DB/session code, the highest-risk place in this codebase for that.

## Findings

1. **blocking** — spec §"Backend: lockfile" (item 10) / §"Files to touch": `pyproject.toml`'s
   `dev` extra currently lists only `pytest`, `httpx`, `ruff` (verified: `grep mypy\|pre-commit
   backend/pyproject.toml` → no match, `.venv/bin/pip list` shows mypy/pre-commit installed
   locally but not declared). CI's `uv sync --locked --extra dev` will not install mypy/pre-commit
   without an explicit add to `[project.optional-dependencies].dev`, which no item in the spec
   names. `make check-backend` on a clean CI checkout fails at the typecheck step.
2. **blocking** — §"Files and interfaces to touch" vs. item 8: `services/sim_session.py` (33
   errors), `domain/personas_postflop.py` (31), `domain/scenarios.py` (12) are listed as "type
   fixes" but contain zero `map_fail(`/`EvaluationResult(` occurrences (verified by grep). Their
   mypy errors are SQLAlchemy `.where()`/`.join()` boolean-vs-ColumnElement mismatches and
   Optional propagation through DB code (e.g. `sim_session.py:1641`, `:1706`) — non-mechanical,
   contradicting item 8's "baseline the rest per module" rule and risking the behaviour-change
   item 9 forbids, in the app's riskiest area (session persistence).
3. **should-fix** — Contract map §3 says EvaluationResult unpacking is "~100 errors from a few
   sites"; measured is 210 errors across 20 call sites (verified via mypy output grep). Doesn't
   change the plan's direction but understates effort by ~2x for the one item explicitly billed
   as a full fix, not a baseline.
4. **optional** — item 9's export_analytics.py caution is moot as written: `mypy app` never
   type-checks `backend/tools/` (excluded per "Out of scope"), so no type fix can reach that file
   through this slice's mechanical process; only `ruff format` (semantics-preserving) touches it.
5. **optional** — Known traps flags venv-3.14-vs-CI-3.12 lock resolution but item 10 doesn't say
   `uv lock --python 3.12` explicitly, only that contract map §5 tested it that way. Worth stating
   explicitly in the Makefile/lock step so a builder doesn't lock against 3.14 by default.

## Verified, no issue found

- mypy baseline (337 errors, per-file clustering, 45 map_fail + ~210 EvaluationResult + 2 syntax)
  matches the contract map exactly.
- Biome baseline (149 errors + 36 warnings + 51 infos on `src/`) matches the claimed 57 format +
  92 lint split.
- `.editorconfig` (2-space, LF) matches the Biome config the spec proposes.
- CI plan's job/step restructuring is consistent with the existing two-job layout and the golden
  paths named.
- `docs/ai-dlc/profile.md:29` does cite the stale `backend/app/services/grading.py` hotspot the
  spec commits to fixing; that file does not exist (verified).
- No pre-commit local hook needs network or a tool missing from the venv/node_modules as
  specified.
