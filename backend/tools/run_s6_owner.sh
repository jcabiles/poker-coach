#!/bin/zsh
# S6 owner-run judging script (checklist sections 3-6 of
# docs/ai-dlc/specs/flywheel-s6-execution-checklist.md).
#
# Owner-only: reads two API keys from the CLIPBOARD at runtime (pbpaste); keys are
# never written to any file, never appear in shell history, never echoed.
# Re-running after a failure is safe: judging checkpoints are per (bundle, judge)
# and atomic, so completed pairs are skipped and never re-billed.
set -u
cd ~/Documents/Github/poker-coach/backend || exit 1

export S6_ROOT="../docs/ai-dlc/research/persona-realism-artifacts/detection-s6"
export S6_JUDGES="anthropic:claude-sonnet-5,anthropic:claude-opus-5,openai:gpt-5.6-terra,openai:gpt-5.6-sol"

# --- keys from clipboard -----------------------------------------------------
grab_key() {
  # $1 = env var name, $2 = human label, $3 = required key prefix
  local key=""
  while true; do
    echo ""
    echo ">> Copy your $2 API key to the clipboard (Cmd-C in the browser), then press Enter here."
    read -k1 -s
    key="$(pbpaste | tr -d '[:space:]')"
    if [[ ${#key} -ge 20 && "${key[1,${#3}]}" == "$3" ]]; then
      echo "   $2 key OK: ${#key} chars, expected prefix matched."
      break
    fi
    echo "   !! Clipboard (${#key} chars) does not look like a $2 key (expect '$3...'). Copy it and press Enter again."
  done
  export "$1"="$key"
}

grab_key S6_JUDGE_ANTHROPIC_KEY "Anthropic" "sk-ant-"
grab_key S6_JUDGE_OPENAI_KEY "OpenAI" "sk-"
if printf '' | pbcopy; then
  echo "Both keys loaded. Clipboard cleared."
else
  echo "Both keys loaded. WARNING: clipboard clear failed — your OpenAI key is still on the clipboard; clear it manually (copy anything else)."
fi

# --- free model-ID probe: confirm the four pinned IDs exist before any spend --
echo "=== Model-ID probe (GET /v1/models, no cost, no judged content) ==="
if ! .venv/bin/python - <<'PYEOF'
import json, os, re, sys, urllib.error, urllib.request

def _page(url, headers):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as exc:
        # Same surface-and-redact pattern as detection_judge._post_json:
        # a bare "HTTP Error 401" is undiagnosable.
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            detail = "<error body unreadable>"
        detail = re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "[REDACTED-KEY]", detail)[:2000]
        raise RuntimeError(f"{exc}: {detail}") from exc

def listed(url, headers):
    # Follow pagination (Anthropic: has_more/last_id; OpenAI returns one page).
    ids, after = set(), None
    for _ in range(50):  # hard stop against a pathological pager
        data = _page(url + (f"?after_id={after}" if after else ""), headers)
        page = data.get("data", [])
        ids |= {m["id"] for m in page}
        if not (data.get("has_more") and page):
            break
        after = data.get("last_id") or page[-1]["id"]
    return ids

failures = []
try:
    ids = listed("https://api.anthropic.com/v1/models",
                 {"x-api-key": os.environ["S6_JUDGE_ANTHROPIC_KEY"],
                  "anthropic-version": "2023-06-01"})
    for want in ("claude-sonnet-5", "claude-opus-5"):
        if want not in ids:
            close = sorted(i for i in ids if "sonnet" in i or "opus" in i)
            failures.append(f"anthropic: {want!r} NOT listed; available: {close}")
except Exception as exc:  # noqa: BLE001 — report and stop, never proceed blind
    failures.append(f"anthropic: models probe failed: {exc}")
try:
    ids = listed("https://api.openai.com/v1/models",
                 {"Authorization": "Bearer " + os.environ["S6_JUDGE_OPENAI_KEY"]})
    for want in ("gpt-5.6-terra", "gpt-5.6-sol"):
        if want not in ids:
            close = sorted(i for i in ids if "5.6" in i or "gpt-5" in i)[:20]
            failures.append(f"openai: {want!r} NOT listed; available: {close}")
except Exception as exc:  # noqa: BLE001
    failures.append(f"openai: models probe failed: {exc}")

if failures:
    print("MODEL PROBE FAILED:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("All four pinned model IDs confirmed by both vendors.")
PYEOF
then
  echo "=== PROBE FAILED — fix the model IDs in S6_JUDGES (edit this script) before spending. Tell Claude. ==="
  exit 1
fi

# --- resolve the control bundle ID from the current deck (checklist section 5) --
CONTROL_ID="$(.venv/bin/python -c "import json;d=json.load(open('$S6_ROOT/deck/unblinding.json'));print(next(b['presentation_id'] for b in d['bundles'] if b['is_control']))")" || exit 1
echo "Control bundle: $CONTROL_ID"

# --- step 5: control pre-screen (slot 0 only; first run also fires preflight) --
echo "=== Step 5: control pre-screen (slot 0, bundle $CONTROL_ID) ==="
.venv/bin/python -m tools.detection_judge run \
  --deck "$S6_ROOT/deck" --judges "$S6_JUDGES" \
  --order-seed 20260807 --out "$S6_ROOT/judging" \
  --only-slot 0 --only-presentation-id "$CONTROL_ID" 2>&1 | tee -a "$S6_ROOT/prescreen.log"
if [[ ${pipestatus[1]} -ne 0 || ${pipestatus[2]} -ne 0 ]]; then
  echo "=== PRE-SCREEN COMMAND FAILED — see $S6_ROOT/prescreen.log. Tell Claude; do not proceed. ==="
  exit 1
fi

# --- stop rule: full run ONLY if the control was judged ok + bot ---------------
if ! CONTROL_ID="$CONTROL_ID" .venv/bin/python - <<'PYEOF'
import json, os, sys
path = os.path.join(os.environ["S6_ROOT"], "judging/responses/slot-0",
                    os.environ["CONTROL_ID"] + ".json")
r = json.load(open(path))
print("pre-screen verdict:", r["status"], r.get("parsed"))
sys.exit(0 if r["status"] == "ok" and (r.get("parsed") or {}).get("label") == "bot" else 1)
PYEOF
then
  echo "=== STOP RULE FIRED — control not labelled bot. Do NOT re-run. Tell Claude. ==="
  exit 1
fi

# --- step 6: full run ----------------------------------------------------------
echo "=== PRE-SCREEN PASS — launching full run (~328 calls) ==="
caffeinate -is .venv/bin/python -m tools.detection_judge run \
  --deck "$S6_ROOT/deck" --judges "$S6_JUDGES" \
  --order-seed 20260807 --out "$S6_ROOT/judging" 2>&1 | tee -a "$S6_ROOT/judging-run.log"
if [[ ${pipestatus[1]} -ne 0 || ${pipestatus[2]} -ne 0 ]]; then
  echo "=== FULL RUN FAILED — see $S6_ROOT/judging-run.log. Re-running this script resumes safely. ==="
  exit 1
fi
echo "=== FULL RUN COMPLETE — completion status: ==="
cat "$S6_ROOT/judging/judging_complete.json" 2>/dev/null || echo "no completion file — run exited 0 but did not finish; tell Claude"
