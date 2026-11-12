# AGENTS.md

Rules for every coding agent in this repo (Claude Code, Codex, Gemini). Claude also reads
`.claude/CLAUDE.md`, which imports this file. The shared rules in `~/.claude/AGENTS.md` apply too;
this file adds the repo's specifics and how to work a ticket.

- **Check command:** `make check` (format check, lint, type check and tests for the backend and the
  frontend, plus a frontend build; about 13 minutes). Run it before you stop; a red or unrun
  check means the work is not done. Never run two checks at once: the backend probe migrates the
  local database.
- **Tickets for agents** are in `docs/ai-dlc/agent-tickets.md`. Take one at a time, in its own
  worktree. Roadmap items not listed there are not ready for agents.
- **Never push, merge or check a ticket box.** A reviewer re-runs the check and records the
  review; only then can the branch be pushed.

## What this is

Local NLHE (No-Limit Hold'em) training web app. Monorepo:
- `backend/` — FastAPI + pure domain core (`app/domain/`, no web/DB imports, enforced by `tests/test_domain_purity.py`) + SQLite/Alembic.
- `frontend/` — React + Vite + strict TypeScript; API types hand-maintained in `src/api/types.ts`.
- `content/` — strategy content packs (versioned JSON) + JSON schema. Strategy lives in data, not code.
- `docs/` — research, roadmap, specs, tickets.

See `README.md` for setup, architecture, and status.

## Active initiative — Bot realism at 6-max (2026-09)

Making every bot at the 6-max table play like its type, judged by the owner in a 200-hand
Challenge session, with each bot's stats in real 6-max ranges as the supporting check. Read before
touching anything:
- Roadmap (slices, bets, pass/fail): `docs/ai-dlc/roadmap/bot-realism-6max.md`
- Evidence: `docs/ai-dlc/reviews/bot-review-200-hands-2026-09-25.md` (a blind review of the
  owner's 200 hands)
- Orientation for a fresh session: `docs/ai-dlc/START-HERE.md`

**Rules this initiative adds:** 9-max stays byte-identical, with one exception — the
board-straight bug fix, which applies at both table sizes. Tuning the other bots waits until the
owner judges the retuned LAG.

**The predecessors are closed or parked.** The phone + 6-max roadmap
(`docs/ai-dlc/roadmap/phone-and-6max.md`) is built. The bot-realism flywheel closed on
2026-09-25, when the owner played a 200-hand Challenge session. Its two parked NEXT items,
**`T-cover`** (the cause of "No baseline yet" is `grade_map_postflop.py`'s *gates*, not the
turn/river graders) and **`T-agentcoach`** (LLM session coaching, narrate-only, session-level
first), are no longer blocked by the flywheel. Neither is scheduled. The persona-realism roadmap
remains **PAUSED**.

## Commands

A ticket worktree has no `backend/.venv` or `frontend/node_modules` of its own. `make ticket` links
the main checkout's copies into the worktree (git ignores the links), so `make check` works there.

```
make check                  # the gate: both halves
make check-backend          # ruff format check, ruff, mypy, ./scripts/verify.sh
make check-frontend         # Biome format and lint, tsc, vitest, vite build
make fix                    # autofix with the formatters
make ticket ID=<id>         # claim an agent ticket (see "Working an agent ticket")
./scripts/serve.sh start    # dev stack: backend :8008 + frontend :7777 (stop/restart/status too)
./scripts/verify.sh         # backend pytest + boot probe; never two at once, it migrates the local DB
```

Leaf commands if you need one: `cd backend && ruff check .`, `cd backend && PYTHONPATH=. .venv/bin/mypy app`, `cd frontend && npm run lint` (Biome), `npm run typecheck`, `npm run build`, `npx vitest run`. The dev stack can also be started with `poker-coach` (direnv).

## Constraints that are not obvious from the code

Global no-gos: no auth/accounts/hosting/billing · no solver tables (heuristic + interim EV only, label EVs *approximate*) · no hand-history imports · no live-session logger · no browsable lessons library (point-of-need concept cards only).

**Turn and river ARE graded** — `backend/app/domain/providers/{turn,river}.py` shipped as slices S5–S8 and are dispatched by street in `composite.py:49-50`. They are simply not *reached*; see `T-cover`. Only **full-hand (2k)** remains deferred.
<!-- History (kept out of context 2026-08-01): a "turn/river engine deferred" no-go used to sit here. It was removed 2026-07-25 after being stale ~15 days and misleading two analyses; superseded 2026-07-09/10 per professional-teacher-rework.md:3-5 + simulate-table.md:7-9. Stated positively above so the retracted claim is no longer re-injected every session. -->


Invariants: domain core `backend/app/domain/` has no web/DB imports (test-enforced) · results freq+EV, never boolean · grading stays behind the one async `StrategyProvider` (keep it swappable — heuristic today, solver later) · strategy lives in versioned `content/` data · CSS values come from design tokens only · AA contrast + visible focus in both themes · every schema change ships an Alembic migration · `spot_signature()` is frozen (changing it orphans SRS history) · FE types are hand-maintained in `frontend/src/api/types.ts` (edit it manually to match API changes; there is no generated types file).

Do the simplest thing that meets the ticket's acceptance criteria — no extra features, abstractions, or future-proofing. Touch only files your ticket names.

Type-check baselines: modules listed under `[[tool.mypy.overrides]]` with `BASELINE(date)` in `backend/pyproject.toml`, and rules at `warn` with `BASELINE(date)` in `frontend/biome.jsonc`. Burn them down; never widen them silently.

### Where machine-local things go

This repository is **public**. Three tiers, and putting something in the wrong
one is how private material gets published:

- **Committed** (`.gitignore`, `CLAUDE.md`, `scripts/`) — durable rules,
  conventions and tooling. Entries in `.gitignore` must benefit *other* users
  of the repo. A personal file path here publishes that file's title.
- **`.git/info/exclude`** — personal ignore patterns. Never committed, and
  shared across linked worktrees, so it is the right home for "ignore my
  private notes" without telling the world they exist.
- **`local/` and `CLAUDE.local.md`** — machine-local *content*: scratch notes,
  run logs, current status of anything sensitive. Both are gitignored, and
  `.worktreeinclude` carries them into worktrees Claude Code creates.

⚠️ `.gitignore` is a **publication** control, not a **secrecy** control. A
gitignored file is one `git add -f` from public and is plaintext on disk either
way. Real secrets live in the provider's console and a mode-600 file you
delete — never in `local/`, and never in the repo at all.

## Working an agent ticket

**The ticket is the authority for the session.** Session-start checklists for roadmap work
elsewhere in this file or in `.claude/CLAUDE.md` do not apply to an agent ticket. Never read another
repo; if the ticket needs one, stop and say so.

1. **Pick.** Use the ticket your prompt names. Otherwise (Codex or Claude) take the first
   unchecked ticket in `docs/ai-dlc/agent-tickets.md` whose branch does not exist yet
   (`git branch --list 'ticket/*'`). If none is left, stop and say so. Gemini never picks: the
   caller names its ticket, claims it and starts Gemini inside `.worktrees/<id>`; started
   anywhere else, Gemini stops and says which ticket it would take.
2. **Claim it** from the repo root with `make ticket ID=<id>` (Codex asks the project owner's
   approval, because this writes to `.git`). It refuses a ticket whose branch already exists,
   which means another session has it. It branches from the local `main` branch, which the
   caller keeps current; Codex has no network to fetch it.
3. **Work only inside `.worktrees/<id>`.** Start Codex from the repo root. `make ticket` links
   the main checkout's `backend/.venv` and `frontend/node_modules` into the worktree; never install packages
   there, because Codex has no network.
4. **Write the failing test first.** Add a test that fails because of the bug, then fix the code,
   then confirm the test passes. Change only what the ticket needs. Gemini writes the test and
   the fix but cannot run them, and says so.
5. **Run `make check` inside the worktree** and report its last lines. Gemini cannot run it: say
   so, and the caller runs it.
6. **Commit** (Codex asks approval; Gemini never commits):
   - Subject: Conventional Commits (`fix:`, `test:`, `refactor:`, `docs:`, `chore:`),
     imperative, at most 50 characters. The body says why when it is not obvious.
   - End with the two trailer lines from the shared rules (`Agent-Vendor:`, `Agent-Model:`).
   - One logical change per commit; never commit work in progress.
7. **Stop and report:** the ticket, the commit hash and the check result (Gemini: the changed
   files and "check not run"), and anything left undone.
