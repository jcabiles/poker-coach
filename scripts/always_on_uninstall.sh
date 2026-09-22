#!/usr/bin/env bash
# Remove the launchd user agent installed by scripts/always_on_install.sh — run
# this YOURSELF in a plain terminal.
#
# It unloads the agent and deletes its plist, so macOS stops starting the stack
# at login and every five minutes. It deliberately does NOT stop a stack that is
# already running: uninstalling mid-session should not end your game. The last
# line tells you how to stop it when you want to.
#
# Usage: scripts/always_on_uninstall.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

LABEL="com.poker-coach.serve"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

if [ "$(id -u)" = "0" ]; then
  echo "refusing to run as root — the agent belongs to your login session; run it as yourself, without sudo" >&2
  exit 1
fi

# launchctl exits non-zero when the label is not loaded, which is the normal
# state if the agent was already removed — the only tolerated failure here.
launchctl bootout "gui/$UID/$LABEL" 2>/dev/null || true
echo "unloaded $LABEL (if it was loaded)"

if [ -f "$PLIST" ]; then
  rm -f "$PLIST"
  echo "removed $PLIST"
else
  echo "no plist at $PLIST — nothing to remove"
fi

echo ""
echo "The servers this agent started are still running if they were up. Stop them with:"
echo "  scripts/serve.sh stop"
