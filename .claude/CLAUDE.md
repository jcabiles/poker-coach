# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## What this is

Local NLHE (No-Limit Hold'em) training web app. Monorepo:
- `backend/` — FastAPI + pure domain core (`app/domain/`, no web/DB imports, enforced by `tests/test_domain_purity.py`) + SQLite/Alembic.
- `frontend/` — React + Vite + strict TypeScript; API types generated from `openapi.json`.
- `content/` — strategy content packs (versioned JSON) + JSON schema. Strategy lives in data, not code.
- `docs/` — research, roadmap, specs, tickets.

See `README.md` for setup, architecture, and status.

## Active initiative — Professional Teacher Rework (2026-07)

Turning the grader into a teacher. Read before touching anything:
- Spec (9 "Now" slices, each with pass/fail): `docs/ai-dlc/roadmap/professional-teacher-rework.md`
- PRD (goal, non-goals, constraints): `docs/ai-dlc/prd/professional-teacher-rework.md`
- Current-state contract maps: `docs/ai-dlc/contracts/{feedback-evaluation,persistence-datamodel,frontend-ia-tokens}.md`
- **181-hand review (2026-07-25) — read before any grader or persona work:** `docs/ai-dlc/research/persona-realism-artifacts/hand-analysis-181/SYNTHESIS.md`. Measured the live app end-to-end: personas score **3–4/10** realism, and **42.5% of graded decisions (105/247) return "No baseline yet"** — postflop only **4/66 = 6.1%** are graded. Two owner-flagged NEXT items came out of it: **`T-cover`** (the "No baseline yet" cause is `grade_map_postflop.py`'s *gates*, NOT the turn/river graders — ⚠️ that module's own docstring claiming "ONLY the HU single-raised-pot continuation line" is **STALE**: HEAD ships 19 postflop mappers incl. nine `map_mw_*` multiway + two limped-**flop**-only; they exist and still reject ~everything, and the reason distribution is unmeasured until `T-REJECT` lands) and **`T-agentcoach`** (LLM-agent session coaching — narrate-only, session-level first; it is also now the designated **test of the 2g–2k engine bet**). Both in `professional-teacher-rework.md` NEXT.
- ⛔ **Order of work (owner, 2026-07-25): FIX THE BOTS FIRST.** The persona-realism remediation set — filed as **R8** in `docs/ai-dlc/roadmap/persona-realism.md` (`W-ARR` + the `N-*` NEXT items) — outranks the whole teacher block above and goes through `/roadmap-ai-dlc` first. `T-agentcoach` and `T-cover` are **blocked behind it**: the coach would otherwise be trained against a 3–4/10 roster, and the mapper would be widened against a bot spot-distribution that persona-realism is actively changing.

Global no-gos: no auth/accounts/hosting/billing · no solver tables (heuristic + interim EV only, label EVs *approximate*) · no hand-history imports · no live-session logger · no browsable lessons library (point-of-need concept cards only).

~~turn/river engine deferred~~ — **REMOVED 2026-07-25, this no-go was stale by ~15 days and actively misled two analyses.** Superseded 2026-07-09/10 and recorded in `professional-teacher-rework.md:3-5` + `simulate-table.md:7-9`: turn/river graders shipped as slices **S5–S8**, `backend/app/domain/providers/{turn,river}.py` exist and are dispatched by street in `composite.py:49-50`. Turn and river ARE graded; they are simply not *reached* — see `T-cover`. Only **full-hand (2k)** remains deferred.

Invariants: domain core `backend/app/domain/` has no web/DB imports (test-enforced) · results freq+EV, never boolean · grading stays behind the one async `StrategyProvider` · strategy lives in versioned `content/` data · CSS values come from design tokens only · AA contrast + visible focus in both themes · every schema change ships an Alembic migration · `spot_signature()` is frozen (changing it orphans SRS history) · FE types are hand-maintained in `frontend/src/api/types.ts` (edit it manually to match API changes; `schema.d.ts` is unwired).

Do the simplest thing that meets the ticket's acceptance criteria — no extra features, abstractions, or future-proofing. Touch only files your ticket names.

## Commands
- Run dev stack: `poker-coach` (direnv) or `./scripts/serve.sh start` — backend :8008 + frontend :5173, background; `stop`/`restart`/`status` too.
- Backend tests + boot probe: `./scripts/verify.sh`
- Backend lint: `cd backend && ruff check .`
- Frontend typecheck/build: `cd frontend && npm run typecheck && npm run build`

## Conventions
- Grading flows through one async `StrategyProvider` interface — keep it swappable (heuristic today, solver later).
- Results are always frequency + EV, never boolean.
- Don't put web/DB imports in `app/domain/`.

## Security

`.claude/settings.json` is a hardened sandbox config:
- OS sandbox enabled (`allowUnsandboxedCommands: false`) — Bash and subprocesses are confined.
- Network allowlist: `pypi.org`, `files.pythonhosted.org`, and GitHub hosts (`github.com`, `api.github.com`, `codeload.github.com`, `objects.githubusercontent.com`) for push/PR. Widen `sandbox.network.allowedDomains` for new workflows — don't disable the sandbox.
- Writes restricted to project dir; deny list blocks `.env`, secrets, `~/.ssh`, `~/.aws`, keychains.

Restart Claude Code after editing `.claude/settings.json` to reload it.

## Git & PR authorization

Before creating a new branch, run `git fetch origin` and make sure the base branch (usually `main`) is up to date with `origin` — fast-forward the local base to `origin/main` first. Never branch from a stale base.

Claude may `git push` and open PRs (`gh pr create`) autonomously on `feat/*`/`fix/*`/`chore/*` branches without asking first. Never push to `main`, never force-push, never merge a PR — those always require explicit confirmation.
