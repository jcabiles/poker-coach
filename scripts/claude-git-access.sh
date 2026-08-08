#!/usr/bin/env bash
# One-time setup: let Claude Code run git fetch/push + gh pr create from inside
# its sandbox. Run this in a REAL terminal (it needs Keychain access, which the
# sandbox deliberately does not have):
#
#   bash ~/Documents/Github/poker-coach/scripts/claude-git-access.sh
#
# What it does (and why):
#   1. Copies your existing Claude-scoped GitHub token out of the macOS
#      Keychain into gh's plain config file (~/.config/gh/hosts.yml).
#      The sandbox can read that file; it cannot read the Keychain.
#   2. Points git at gh for GitHub credentials (gh auth setup-git).
#   3. Switches both poker repos from SSH remotes to HTTPS (the sandbox
#      blocks ~/.ssh by design, so SSH can never work inside it).
#   4. Updates poker-coach/.claude/settings.json: adds git fetch/pull/ls-remote
#      to the pre-approved list, removes the dead excludedCommands block.
#      A timestamped backup of settings.json is written next to it first.
#
# Safe to re-run: every step is idempotent.
# After it finishes: RESTART Claude Code (settings only load at startup).

set -euo pipefail

COACH=~/Documents/Github/poker-coach
ANALYTICS=~/Documents/Github/poker-analytics
SETTINGS="$COACH/.claude/settings.json"

step() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

step "0/5 Preflight"
command -v gh >/dev/null || { echo "ERROR: gh CLI not found"; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: python3 not found"; exit 1; }
[ -f "$SETTINGS" ] || { echo "ERROR: $SETTINGS not found"; exit 1; }
[ -d "$ANALYTICS/.git" ] || { echo "ERROR: $ANALYTICS is not a git repo"; exit 1; }
echo "ok"

step "1/5 Move token from Keychain to gh's plain config file"
TOKEN=$(gh auth token 2>/dev/null || true)
if [ -z "$TOKEN" ]; then
  echo "ERROR: 'gh auth token' returned nothing — run 'gh auth login' first."
  exit 1
fi
printf '%s\n' "$TOKEN" | gh auth login --with-token --insecure-storage --hostname github.com
unset TOKEN
gh auth status --hostname github.com || true
# Verify the token actually landed in the plain file (not back in the Keychain):
if grep -q "oauth_token" ~/.config/gh/hosts.yml 2>/dev/null; then
  echo "ok — token is in ~/.config/gh/hosts.yml (sandbox-readable)"
else
  echo "ERROR: token did not land in ~/.config/gh/hosts.yml — stopping."
  exit 1
fi

step "2/5 Point git at gh for GitHub credentials"
gh auth setup-git --hostname github.com
echo "ok"

step "3/5 Switch remotes to HTTPS"
git -C "$COACH" remote set-url origin https://github.com/jcabiles/poker-coach.git
git -C "$ANALYTICS" remote set-url origin https://github.com/jcabiles/poker-analytics.git
git -C "$COACH" remote -v | head -1
git -C "$ANALYTICS" remote -v | head -1

step "4/5 Update .claude/settings.json (backup first)"
cp "$SETTINGS" "$SETTINGS.bak.$(date +%Y%m%d%H%M%S)"
python3 - "$SETTINGS" <<'PYEOF'
import json, sys

path = sys.argv[1]
with open(path) as f:
    cfg = json.load(f)

allow = cfg.setdefault("permissions", {}).setdefault("allow", [])
for rule in ["Bash(git fetch:*)", "Bash(git pull origin:*)", "Bash(git ls-remote:*)"]:
    if rule not in allow:
        allow.append(rule)

# excludedCommands was meant to run these outside the sandbox, but
# allowUnsandboxedCommands: false disables the mechanism entirely — and after
# this setup everything runs INSIDE the sandbox anyway. Dead config, removed.
removed = cfg.get("sandbox", {}).pop("excludedCommands", None)

with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")

print("allow-list updated;", "excludedCommands removed" if removed else "no excludedCommands present")
PYEOF

step "5/5 Verify credentials work over HTTPS"
git -C "$COACH" ls-remote --heads origin main >/dev/null && echo "poker-coach: ok"
git -C "$ANALYTICS" ls-remote --heads origin main >/dev/null && echo "poker-analytics: ok"

printf '\n\033[1mDONE. Now RESTART Claude Code, then tell Claude: "test it".\033[0m\n'
printf 'Claude will push the two pending S6 panel-amendment branches and open both PRs itself.\n'
