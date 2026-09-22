#!/usr/bin/env bash
# Install the launchd user agent that keeps this project's dev stack up — run
# this YOURSELF in a plain terminal, once.
#
# What it does: renders scripts/always-on/com.poker-coach.serve.plist.tmpl with
# this checkout's path and your node directory, writes it to
# ~/Library/LaunchAgents/, and loads it. From then on macOS runs
# `scripts/serve.sh --lan start` at login and every five minutes; the launcher
# is a no-op when the stack is already up, so the repeat is what brings it back
# after a sleep or a crash.
#
# Re-running is safe: the agent is unloaded and reloaded from the fresh plist.
#
# Usage: scripts/always_on_install.sh [--print]
#        --print renders the plist to stdout and exits, touching neither launchd
#        nor ~/Library — this renders without touching launchd so the plist can
#        be inspected or linted by hand.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

TEMPLATE="$REPO/scripts/always-on/com.poker-coach.serve.plist.tmpl"
LABEL="com.poker-coach.serve"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$REPO/local/always-on"

PRINT_ONLY=""
for arg in "$@"; do
  case "$arg" in
    --print) PRINT_ONLY="yes" ;;
    *) echo "usage: scripts/always_on_install.sh [--print]" >&2; exit 2 ;;
  esac
done

# A user agent runs as you, under your login session. As root there is no
# `gui/$UID` domain to bootstrap into and the servers would run as the wrong user.
if [ "$(id -u)" = "0" ]; then
  echo "refusing to run as root — this installs a per-user agent; run it as yourself, without sudo" >&2
  exit 1
fi

[ -f "$TEMPLATE" ] || { echo "missing template ($TEMPLATE)" >&2; exit 1; }

# In a linked worktree `.git` is a file, not a directory. Such a checkout is
# deleted once its branch merges, which would leave the agent firing at a dead
# path. ALWAYS_ON_ALLOW_WORKTREE=1 lifts the refusal so an automated `--print`
# check can render from a worktree; never set it for a real install.
if [ -f "$REPO/.git" ] && [ "${ALWAYS_ON_ALLOW_WORKTREE:-}" != "1" ]; then
  echo "refusing: $REPO is a linked worktree and is deleted when its branch merges — run this from your main checkout, e.g. ~/Documents/Github/poker-coach" >&2
  exit 1
fi

# launchd gives a job almost no PATH, and vite's launcher is a `#!/usr/bin/env
# node` shim — so the directory of the node YOU use is baked into the plist.
NODE_BIN="$(command -v node || true)"
if [ -z "$NODE_BIN" ]; then
  echo "no node on PATH — install Node (brew install node) and re-run; the agent cannot start the frontend without it" >&2
  exit 1
fi
NODE_DIR="$(cd "$(dirname "$NODE_BIN")" && pwd)"

# `|` is the sed delimiter below, so neither substituted path may contain one.
# `&` and `\` are sed replacement-side metacharacters too — `&` means "the whole
# match" and `\` escapes the next character — so a path containing either would
# render wrong while still passing plutil -lint. Rejecting is simpler and safer
# than escaping, so refuse rather than try to sanitize.
case "$REPO$NODE_DIR" in
  *"|"*) echo "refusing: a '|' in $REPO or $NODE_DIR would break the plist rendering — the path must not contain it" >&2; exit 1 ;;
  *"&"*) echo "refusing: a '&' in $REPO or $NODE_DIR would break the plist rendering — the path must not contain it" >&2; exit 1 ;;
  *"\\"*) echo "refusing: a '\\' in $REPO or $NODE_DIR would break the plist rendering — the path must not contain it" >&2; exit 1 ;;
esac

render() {
  sed -e "s|@REPO@|$REPO|g" -e "s|@NODE_DIR@|$NODE_DIR|g" "$TEMPLATE"
}

if [ -n "$PRINT_ONLY" ]; then
  render
  exit 0
fi

# launchd will not create the log directory; this does.
mkdir -p "$LOG_DIR"

# Render to a temp file and lint it before touching ~/Library, so a bad render
# never overwrites a working plist.
TMP_PLIST="$(mktemp)"
render >"$TMP_PLIST"
plutil -lint "$TMP_PLIST"

mkdir -p "$(dirname "$PLIST")"
mv "$TMP_PLIST" "$PLIST"

# `launchctl load` is deprecated and silently no-ops on an already-loaded label,
# so bootout-then-bootstrap is the way to pick up an edited plist. A first
# install has nothing to bootout and launchctl exits non-zero for that — the
# only tolerated failure here, and re-running bootstrap below would fail loudly
# if the old job were in fact still loaded.
launchctl bootout "gui/$UID/$LABEL" 2>/dev/null || true

# macOS's bootout can return before teardown actually completes, so an
# immediate bootstrap can fail with "Input/output error" — retry a few times.
BOOTSTRAP_OK=""
for _ in 1 2 3; do
  if launchctl bootstrap "gui/$UID" "$PLIST" && launchctl print "gui/$UID/$LABEL" >/dev/null 2>&1; then
    BOOTSTRAP_OK="yes"
    break
  fi
  sleep 1
done
if [ -z "$BOOTSTRAP_OK" ]; then
  echo "the agent is NOT loaded — re-run this script" >&2
  exit 1
fi

echo ""
echo "installed $PLIST"
# Informational only: grep exits 1 when launchd's wording has no matching line,
# and that must not fail an install that already succeeded above.
launchctl print "gui/$UID/$LABEL" | grep -E 'state|last exit' || true
echo ""
echo "status right now (the agent's first start can take up to a minute; run scripts/serve.sh status again shortly):"
"$REPO/scripts/serve.sh" status
echo ""
echo "log: ${LOG_DIR#"$REPO"/}/launchd.log"
echo "uninstall: scripts/always_on_uninstall.sh"
