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
