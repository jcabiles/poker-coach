#!/bin/zsh
# Teardown for setup_probe_access.sh — run this YOURSELF in a plain terminal.
#
# The mirror of the setup script. It:
#   1. shows you the key fingerprints and opens both provider consoles, so you
#      can revoke the exact keys without hunting;
#   2. waits until you confirm BOTH are revoked;
#   3. deletes ~/.config/s6-probe-keys.sh;
#   4. removes api.anthropic.com from the sandbox network allowlist, restoring
#      what setup_probe_access.sh changed (api.openai.com was already allowed
#      before that script ran and is left alone);
#   5. tells you to restart Claude Code.
#
# ORDER MATTERS AND THE ORDER IS: REVOKE FIRST, DELETE SECOND. Deleting the file
# does not make the keys safe. They were plaintext on disk, sourced into shells,
# and read by a sandboxed process — so they must be assumed disclosed, and only
# revocation at the provider ends that. On APFS, overwriting a file does not
# reliably destroy the old blocks either. Revocation is the fix; deletion is
# tidying up after it.
set -euo pipefail

KEYFILE=~/.config/s6-probe-keys.sh
SETTINGS=$(cd "$(dirname "$0")/.." && pwd)/.claude/settings.json

ANTHROPIC_CONSOLE="https://console.anthropic.com/settings/keys"
OPENAI_CONSOLE="https://platform.openai.com/api-keys"

# --- 1. identify the keys ----------------------------------------------------
if [[ ! -f "$KEYFILE" ]]; then
  echo "No $KEYFILE — nothing to delete."
  echo "If you have not revoked the keys, do that anyway:"
  echo "  Anthropic: $ANTHROPIC_CONSOLE"
  echo "  OpenAI:    $OPENAI_CONSOLE"
else
  echo "Keys recorded in $KEYFILE (fingerprints only — full values never printed):"
  grep -oE '(sk-ant-[A-Za-z0-9_-]+|sk-proj-[A-Za-z0-9_-]+|sk-[A-Za-z0-9_-]{20,})' "$KEYFILE" \
    | while read -r k; do
        printf '  %s...%s   (%s chars)\n' "${k:0:12}" "${k: -4}" "${#k}"
      done
  echo ""
  echo "Match those against the key list in each console and revoke them."
fi

echo ""
echo "Opening both consoles..."
open "$ANTHROPIC_CONSOLE" 2>/dev/null || echo "  (open manually: $ANTHROPIC_CONSOLE)"
open "$OPENAI_CONSOLE" 2>/dev/null || echo "  (open manually: $OPENAI_CONSOLE)"

# --- 2. confirm revocation ---------------------------------------------------
echo ""
echo "Revoke BOTH keys now. Type 'revoked' once they are gone from both consoles."
read -r CONFIRM
if [[ "$CONFIRM" != "revoked" ]]; then
  echo ""
  echo "Stopping. Nothing was deleted and the sandbox allowlist is unchanged —"
  echo "the key file is still the only record of which keys need revoking."
  echo "Re-run this script when you have revoked them."
  exit 1
fi

# --- 3. delete the key file --------------------------------------------------
if [[ -f "$KEYFILE" ]]; then
  rm -f "$KEYFILE"
  echo "Deleted $KEYFILE"
fi

# --- 4. restore the sandbox allowlist ---------------------------------------
if [[ -f "$SETTINGS" ]]; then
  cp "$SETTINGS" "$SETTINGS.bak.$(date +%Y%m%d%H%M%S)"
  python3 - "$SETTINGS" <<'PYEOF'
import json, sys
path = sys.argv[1]
with open(path) as f:
    cfg = json.load(f)
domains = cfg["sandbox"]["network"]["allowedDomains"]
# Only api.anthropic.com is removed. setup_probe_access.sh added exactly that
# one; the openai entries predate it and other workflows use them.
before = len(domains)
cfg["sandbox"]["network"]["allowedDomains"] = [d for d in domains if d != "api.anthropic.com"]
after = len(cfg["sandbox"]["network"]["allowedDomains"])
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")
print(f"allowlist: {before} -> {after} domains"
      f" ({'api.anthropic.com removed' if before != after else 'already absent'})")
PYEOF
fi

# --- 5. restart --------------------------------------------------------------
echo ""
echo "DONE. Quit Claude Code fully and relaunch it — a settings change needs a"
echo "restart to take effect."
echo ""
echo "Leftover backups you can prune once you are happy:"
ls -1 $(cd "$(dirname "$0")/.." && pwd)/.claude/settings.json.bak.* 2>/dev/null || true
