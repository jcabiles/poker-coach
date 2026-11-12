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

## Session boot checklist + misalignment tripwires (owner-mandated, 2026-08-05)

Before picking up ANY work: (1) read `docs/ai-dlc/profile.md` `active:` and open that roadmap; (2) read its pass/fail state and resume from the first unchecked slice — never from memory of what seemed next; (3) if the work spans poker-analytics, read that repo's `docs/FLYWHEEL-STATUS.md` first (its per-directory memory knows nothing about this repo's decisions).

**Tripwires — STOP and tell the owner (do not proceed, do not silently reconcile) when:**
- a ticket/spec contradicts the active roadmap or PRD, or cites a paused/superseded doc as authority;
- poker-coach and poker-analytics artifacts disagree about interface, ownership, or priorities;
- research findings undercut a planned slice's premise;
- the work in front of you doesn't serve the north-star outcome in the active roadmap;
- you find yourself about to re-derive a decision an existing doc already records differently.

Global no-gos: no auth/accounts/hosting/billing · no solver tables (heuristic + interim EV only, label EVs *approximate*) · no hand-history imports · no live-session logger · no browsable lessons library (point-of-need concept cards only).

**Turn and river ARE graded** — `backend/app/domain/providers/{turn,river}.py` shipped as slices S5–S8 and are dispatched by street in `composite.py:49-50`. They are simply not *reached*; see `T-cover`. Only **full-hand (2k)** remains deferred.
<!-- History (kept out of context 2026-08-01): a "turn/river engine deferred" no-go used to sit here. It was removed 2026-07-25 after being stale ~15 days and misleading two analyses; superseded 2026-07-09/10 per professional-teacher-rework.md:3-5 + simulate-table.md:7-9. Stated positively above so the retracted claim is no longer re-injected every session. -->

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

Invariants: domain core `backend/app/domain/` has no web/DB imports (test-enforced) · results freq+EV, never boolean · grading stays behind the one async `StrategyProvider` (keep it swappable — heuristic today, solver later) · strategy lives in versioned `content/` data · CSS values come from design tokens only · AA contrast + visible focus in both themes · every schema change ships an Alembic migration · `spot_signature()` is frozen (changing it orphans SRS history) · FE types are hand-maintained in `frontend/src/api/types.ts` (edit it manually to match API changes; there is no generated types file).

Do the simplest thing that meets the ticket's acceptance criteria — no extra features, abstractions, or future-proofing. Touch only files your ticket names.

Type-check baselines: modules listed under `[[tool.mypy.overrides]]` with `BASELINE(date)` in `backend/pyproject.toml`, and rules at `warn` with `BASELINE(date)` in `frontend/biome.jsonc`. Burn them down; never widen them silently.

### Credentials on disk — never end a session with "you should rotate those"

A session that concludes a credential must be deleted or rotated **hands the
owner runnable commands, in the right order, in that same reply.** Reporting
"those keys should be rotated" and stopping is not a handoff; it is a to-do item
the owner then has to design themselves, which is why that report has been made
more than once without the cleanup ever happening.

Current status of any specific credential belongs in `CLAUDE.local.md`, not
here. This file is committed to a PUBLIC repository, so a live "these keys are
still valid at this path" note here is a signpost for anyone reading. The rule
is durable and public; the status is neither.

An agent cannot revoke a key — that needs a browser login at the provider. What
an agent CAN do is remove every excuse not to:

1. **Name the keys without printing them.** First 12 and last 4 characters plus
   the length is enough to find a key in a console, and safe to put on screen.
2. **Give the console URLs** — Anthropic `https://console.anthropic.com/settings/keys`,
   OpenAI `https://platform.openai.com/api-keys`.
3. **Point at the teardown script, or write one.** For the S6 probe keys it is
   **`./scripts/teardown_probe_access.sh`** — the mirror of
   `setup_probe_access.sh` (which lives with the gitignored research artifacts
   under `detection-s6/`). It shows fingerprints, opens both consoles, waits for
   confirmation, deletes `~/.config/s6-probe-keys.sh`, and removes
   `api.anthropic.com` from the sandbox allowlist. One command, and it aborts
   without touching anything if the owner does not confirm.
4. **State the order and why.** Revoke first, delete second. Deleting the file
   does not make a disclosed key safe, and on APFS overwriting it does not
   reliably destroy the old blocks. Revocation at the provider is the only thing
   that ends the exposure; deletion is tidying up afterwards.
5. **Say plainly that rotation is the owner's to do**, rather than implying it
   has been handled.

**Any script that writes a credential to disk ships its teardown at the same
time, in a TRACKED location.** `setup_probe_access.sh` shipped with a one-line
comment saying to clean up later, no way to do it, and inside a gitignored
directory — so nothing about it survived to another machine. Setup and teardown
are one deliverable, and the teardown belongs in `scripts/`.

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

1. **Pick.** Use the ticket your prompt names. Otherwise take the first unchecked ticket in
   `docs/ai-dlc/agent-tickets.md` whose branch does not exist yet
   (`git branch --list 'ticket/*'`). If none is left, stop and say so.
2. **Claim it** from the repo root with `make ticket ID=<id>`. It refuses a ticket whose branch
   already exists, which means another session has it.
   - Codex: this writes to `.git`, so it asks the project owner's approval.
   - Gemini (agy) cannot run commands. Work only if you were started inside that ticket's
     worktree (`.worktrees/<id>`); otherwise stop and say which ticket you would take.
3. **Work only inside `.worktrees/<id>`.** Start the session from the repo root (Codex) so the
   main checkout's `backend/.venv` and `frontend/node_modules` stay readable.
4. **Write the failing test first.** Add a test that fails because of the bug, then fix the code,
   then confirm the test passes. Change only what the ticket needs.
5. **Run `make check` inside the worktree** and report its last lines. Gemini cannot run it: say
   so, and the caller runs it.
6. **Commit** (Codex asks approval; Gemini never commits and lists its changed files instead):
   - Subject: Conventional Commits (`fix:`, `test:`, `refactor:`, `docs:`, `chore:`),
     imperative, at most 50 characters. The body says why when it is not obvious.
   - End with the two trailer lines from the shared rules (`Agent-Vendor:`, `Agent-Model:`).
   - One logical change per commit; never commit work in progress.
7. **Stop and report:** the ticket, the commit hash, the check result and anything left undone.
