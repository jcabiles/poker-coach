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
