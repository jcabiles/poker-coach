# Tickets — cleanup slice 2: quality gates (`make check`)

status: **approved (pre-authorized by --auto-build invocation, 2026-09-18)** — the owner typed
`/ai-org:spec --auto-build` in the 2026-09-18 session and pre-approved the dev dependencies;
round-1 review adjudicated the same day (ledger `../ledger/cleanup-quality-gates.md`). Approval
covers building G1–G6 on branch `chore/quality-gates` and committing; merging is covered by the
owner's separate 2026-09-18 merge ruling (green gates + fresh reviewer approval). Spec:
`../specs/cleanup-quality-gates.md` (rev 2). Contract map: `../contracts/cleanup-quality-gates.md`.

## Shape of the work

Six tickets. G2, G3 and G4 are the backend chain (they share `backend/pyproject.toml` and the
`backend/**/*.py` tree, so they run in order in one worker). G5 is the frontend and touches
nothing the backend chain touches, so it runs **in parallel** with that chain. G1 and G6 are
root-level wiring and docs that need both sides' targets to exist, so they run last, by the
Director.

```
G2 → G3 → G4  (one backend worker)
G5            (one frontend worker, parallel)
      ↓
G1 → G6       (Director)
```

Baseline before starting (branch base `f57d1c9`): backend `2239 passed, 2 skipped` via
`PYTHONPATH=. .venv/bin/python -m pytest -q`; ruff clean; frontend typecheck/build clean,
`vitest run` 60 passed. Every done-condition below means: those numbers do not drop.

---

### G2 — Backend format gate

Apply `ruff format .` to the backend once, and make `ruff format --check .` pass.

- **Owns:** `backend/**/*.py` (mechanical reformat only, one commit), nothing else.
- **Acceptance:** `cd backend && .venv/bin/ruff format --check .` exits 0; `ruff check .` still
  clean; the commit touches only `*.py`; the full backend suite count is unchanged.
- **Done:** `PYTHONPATH=. .venv/bin/python -m pytest -q` from `backend/` → 2239 passed.

### G3 — Backend type gate (mypy)

Add `[tool.mypy]` to `pyproject.toml` per spec §6, fix the two dominant error patterns and
the two malformed `# type: ignore` comments per §7, baseline the remaining modules per §8, and
make `mypy app` pass.

- **Owns:** `backend/pyproject.toml` (mypy sections), `backend/app/domain/postflop.py`,
  `backend/app/domain/table/grade_map_postflop.py`, `backend/app/domain/table/range_estimate.py`,
  plus any small module a fix reaches (list them in the return). `services/sim_session.py`,
  `domain/personas_postflop.py` and `domain/scenarios.py` are baselined by config, not edited.
- **Acceptance:** `cd backend && PYTHONPATH=. .venv/bin/mypy app` exits 0; every
  `ignore_errors` override carries `# BASELINE(2026-09-18): <n> errors, <reason>`; no
  behaviour change — the full suite count is unchanged and `tests/test_domain_purity.py`
  passes; no new `# type: ignore` lines except where a third-party stub is genuinely missing.
- **Report:** the final baseline list (module, error count) and the count fixed.
- **Depends:** G2 (so the type fixes are not mixed into the reformat diff).

### G4 — Backend lockfile

Add `mypy` and `pre-commit` to the `dev` extra in `pyproject.toml`, regenerate
`backend/uv.lock` with `uv lock --python 3.12`, commit it, and prove it installs.

- **Owns:** `backend/uv.lock`, `backend/pyproject.toml` (`[tool.uv]` only if needed).
- **Acceptance:** `SSL_CERT_FILE=<bundle> uv sync --locked --extra dev` into a fresh temporary
  project dir (`--python 3.12` if present, else the venv's 3.14) succeeds; `uv lock --check`
  reports the lock up to date.
- **Depends:** G3.

### G5 — Frontend lint + format gate (Biome)

Add `frontend/biome.json` per spec §11, `lint`/`format`/`check` scripts in `package.json`,
apply `biome check --write src` once (own commit), then make `biome ci src` pass with zero
errors by fixing the mechanical rules and downgrading the rest to `warn` per §13.

- **Owns:** `frontend/biome.json` (new), `frontend/package.json`, `frontend/package-lock.json`
  (Biome 2.5.14 is already installed in this worktree), `frontend/src/**` (mechanical commit,
  then rule-driven edits that do not change rendering).
- **Acceptance:** `cd frontend && node_modules/.bin/biome ci src` exits 0 with zero errors;
  `npm run typecheck`, `npm run build`, `npx vitest run` (60) green; no rule is set to `off`;
  every downgraded rule carries a `BASELINE(2026-09-18)` comment; `git diff` shows no change to
  rendered markup or CSS values beyond formatting.
- **Parallel with:** G2–G4 (disjoint files).

### G1 — Root Makefile

Write the `Makefile` per spec §1–§4 and prove `make check` passes.

- **Owns:** `Makefile` (new).
- **Acceptance:** `make check` exits 0 from the worktree root; `make check-backend` and
  `make check-frontend` each exit 0 alone; `make fix` runs the three formatters; a deliberately
  broken file makes the right leaf target fail and `make` names it.
- **Depends:** G3, G4, G5.

### G6 — Pre-commit, CI, docs, profile conventions

`.pre-commit-config.yaml` per §15; `ci.yml` per §16; README / `.claude/CLAUDE.md` /
`docs/ai-dlc/profile.md` per §17–§18; tick slice 2 in `docs/cleanup-project-brief.md`.

- **Owns:** `.pre-commit-config.yaml` (new), `.github/workflows/ci.yml`, `README.md`,
  `.claude/CLAUDE.md`, `docs/ai-dlc/profile.md`, `docs/cleanup-project-brief.md`,
  `docs/ai-dlc/ledger/cleanup-quality-gates.md`, `docs/ai-dlc/log.md`.
- **Acceptance:** `backend/.venv/bin/pre-commit run --all-files` passes; the CI YAML parses and
  its two jobs call `make check-backend` / `make check-frontend`; none of the three docs still
  names the stale grading hotspot; `grep -rn "verify.sh" README.md .claude/CLAUDE.md
  docs/ai-dlc/profile.md` shows it only as a leaf under `make check`.
- **Depends:** G1.

---

### Finish the slice

G6 also ticks slice 2 in `docs/cleanup-project-brief.md` and writes the ledger and log entry in
the same change.
