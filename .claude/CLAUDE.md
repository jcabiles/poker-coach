# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

The repo facts, commands, constraints and the ticket procedure every agent shares are in `AGENTS.md`:

@../AGENTS.md

## Security

`.claude/settings.json` is a hardened sandbox config:
- OS sandbox enabled (`allowUnsandboxedCommands: false`) — Bash and subprocesses are confined.
- Network allowlist: `pypi.org`, `files.pythonhosted.org`, and GitHub hosts (`github.com`, `api.github.com`, `codeload.github.com`, `objects.githubusercontent.com`) for push/PR. Widen `sandbox.network.allowedDomains` for new workflows — don't disable the sandbox.
- Writes restricted to project dir; deny list blocks `.env`, secrets, `~/.ssh`, `~/.aws`, keychains.

Restart Claude Code after editing `.claude/settings.json` to reload it.

## Git & PR authorization

Before creating a new branch, run `git fetch origin` and make sure the base branch (usually `main`) is up to date with `origin` — fast-forward the local base to `origin/main` first. Never branch from a stale base.

Claude may `git push` and open PRs (`gh pr create`) autonomously on `feat/*`/`fix/*`/`chore/*` branches without asking first. Never push to `main`, never force-push, never merge a PR — those always require explicit confirmation.

Every commit ends with the `Agent-Vendor:` and `Agent-Model:` trailer lines from the shared rules in `~/.claude/AGENTS.md` (for Claude: `Agent-Vendor: Anthropic` and the exact model name of the session).

## Session boot checklist + misalignment tripwires (owner-mandated, 2026-08-05)

Before picking up ANY work: (1) read `docs/ai-dlc/profile.md` `active:` and open that roadmap; (2) read its pass/fail state and resume from the first unchecked slice — never from memory of what seemed next; (3) if the work spans poker-analytics, read that repo's `docs/FLYWHEEL-STATUS.md` first (its per-directory memory knows nothing about this repo's decisions).

**Tripwires — STOP and tell the owner (do not proceed, do not silently reconcile) when:**
- a ticket/spec contradicts the active roadmap or PRD, or cites a paused/superseded doc as authority;
- poker-coach and poker-analytics artifacts disagree about interface, ownership, or priorities;
- research findings undercut a planned slice's premise;
- the work in front of you doesn't serve the north-star outcome in the active roadmap;
- you find yourself about to re-derive a decision an existing doc already records differently.

## Credentials on disk — never end a session with "you should rotate those"

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
