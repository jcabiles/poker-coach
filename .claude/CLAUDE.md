# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## What this is

Local NLHE (No-Limit Hold'em) training web app. Monorepo:
- `backend/` — FastAPI + pure domain core (`app/domain/`, no web/DB imports, enforced by `tests/test_domain_purity.py`) + SQLite/Alembic.
- `frontend/` — React + Vite + strict TypeScript; API types hand-maintained in `src/api/types.ts`.
- `content/` — strategy content packs (versioned JSON) + JSON schema. Strategy lives in data, not code.
- `docs/` — research, roadmap, specs, tickets.

See `README.md` for setup, architecture, and status.

## Active initiative — Phone access + 6-max (2026-09)

Making the trainer playable from the owner's Android phone on the home wifi, then adding 6-max
tables. Read before touching anything:
- Roadmap (slices, decisions D1–D4, pass/fail — no separate PRD exists yet for this initiative):
  `docs/ai-dlc/roadmap/phone-and-6max.md`
- Finding ledger (review rounds, rescued facts, measurements): `docs/ai-dlc/ledger/phone-and-6max.md`
- Orientation for a fresh session: `docs/ai-dlc/START-HERE.md`

**The bot-realism flywheel initiative that preceded this one is still open, not closed.** Its
roadmap, `docs/ai-dlc/roadmap/bot-realism-flywheel.md`, has exactly one unticked box: two-mode
Simulate (Training vs Challenge) is built, and stays open until the owner plays a Challenge-mode
session and reaches its hand-200 threshold — that play session, not a ticket count, is what closes
it. Its own persona-realism predecessor roadmap remains **PAUSED**, and its two blocked NEXT items,
**`T-cover`** (cause of "No baseline yet" is `grade_map_postflop.py`'s *gates*, not the turn/river
graders) and **`T-agentcoach`** (LLM session coaching, narrate-only, session-level first), stay
blocked. The phase-3 fix-vs-overhaul question itself was decided 2026-08-15 (ruling A: fix the
current bots); what both items still wait on is the flywheel's finale — the owner's Challenge-mode
play session that closes the last open box above.

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

Invariants: domain core `backend/app/domain/` has no web/DB imports (test-enforced) · results freq+EV, never boolean · grading stays behind the one async `StrategyProvider` (keep it swappable — heuristic today, solver later) · strategy lives in versioned `content/` data · CSS values come from design tokens only · AA contrast + visible focus in both themes · every schema change ships an Alembic migration · `spot_signature()` is frozen (changing it orphans SRS history) · FE types are hand-maintained in `frontend/src/api/types.ts` (edit it manually to match API changes; there is no generated types file).

Do the simplest thing that meets the ticket's acceptance criteria — no extra features, abstractions, or future-proofing. Touch only files your ticket names.

## Commands
- Run dev stack: `poker-coach` (direnv) or `./scripts/serve.sh start` — backend :8008 + frontend :7777, background; `stop`/`restart`/`status` too.
- **The gate: `make check`** (format check + lint + type check + tests, both halves). Run it before declaring any work done. Halves: `make check-backend` / `make check-frontend`; autofix: `make fix`.
- Leaf targets if you need one: `./scripts/verify.sh` (backend pytest + boot probe — never two at once, it migrates the local DB), `cd backend && ruff check .`, `cd backend && PYTHONPATH=. .venv/bin/mypy app`, `cd frontend && npm run lint` (Biome), `npm run typecheck`, `npm run build`, `npx vitest run`.
- Type-check baselines: modules listed under `[[tool.mypy.overrides]]` with `BASELINE(date)` in `backend/pyproject.toml`, and rules at `warn` with `BASELINE(date)` in `frontend/biome.jsonc`. Burn them down; never widen them silently.

## Security

`.claude/settings.json` is a hardened sandbox config:
- OS sandbox enabled (`allowUnsandboxedCommands: false`) — Bash and subprocesses are confined.
- Network allowlist: `pypi.org`, `files.pythonhosted.org`, and GitHub hosts (`github.com`, `api.github.com`, `codeload.github.com`, `objects.githubusercontent.com`) for push/PR. Widen `sandbox.network.allowedDomains` for new workflows — don't disable the sandbox.
- Writes restricted to project dir; deny list blocks `.env`, secrets, `~/.ssh`, `~/.aws`, keychains.

Restart Claude Code after editing `.claude/settings.json` to reload it.

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

Claude cannot revoke a key — that needs a browser login at the provider. What
Claude CAN do is remove every excuse not to:

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

## Git & PR authorization

Before creating a new branch, run `git fetch origin` and make sure the base branch (usually `main`) is up to date with `origin` — fast-forward the local base to `origin/main` first. Never branch from a stale base.

Claude may `git push` and open PRs (`gh pr create`) autonomously on `feat/*`/`fix/*`/`chore/*` branches without asking first. Never push to `main`, never force-push, never merge a PR — those always require explicit confirmation.
