# Fan-in review r2 — Always-on stack diff (fresh Claude refuter, Opus, 2026-09-22)

Returned inline and saved verbatim by the Director. Reviewed the corrected uncommitted diff (after the
r1 fixes) against spec rev 2 and `scripts/serve.sh`, on system bash 3.2.

VERDICT: PASS (two should-fix gaps; nothing blocks the owner's actual path)

The plist is correct on every point named: `plutil -lint` passes on the rendered output, and a `plistlib` type audit confirms `StartCalendarInterval` is an array of 12 dicts with integer `Minute` values, `RunAtLoad`/`KeepAlive`/`AbandonProcessGroup` are real booleans, `EnvironmentVariables` is a dict, and all four paths are absolute after rendering. Both scripts pass `bash -n` under bash 3.2; `"$@"` with zero arguments does not trip `set -u`; `$UID` resolves; the nested-quote expansion works. No XML comment contains `--`. `command -v node` resolves to `/opt/homebrew/bin/node` and its dirname is the right PATH entry. The uninstall leaves a running stack alone. The README's loopback-wedge wording matches `serve.sh:128`, and the no-coach-key claim is correct (`coach.py:211` reads the environment; the backend loads no `.env`).

1. **should-fix** — `sed`'s `&` metacharacter corrupts rendered paths silently and the result still lints clean (`always_on_install.sh:63-68`): a repo at `/Users/x/R&D/poker-coach` renders as `/Users/x/R@REPO@D/...`. Fix: reject `&` and `\` in the guard, or escape the replacement.
2. **should-fix** — a `bootstrap` failure after a successful `bootout` leaves no agent and is undetected (`:88-89`); macOS's `bootout` can return before teardown completes and the immediate `bootstrap` fails with "Input/output error". Fix: verify with `launchctl print` and retry, or exit with a re-run message.
3. **low** — the plist is written before `plutil -lint` and not removed on failure (`:80-81`); the spec prescribed that order. Fix: render to a temp file, lint, then `mv`.
4. **low** — spec item 1 still lists `/opt/homebrew/bin` in PATH while the template omits it; the template's reason is only true for a Homebrew node (nvm/fnm/Volta users get no Homebrew bin). Harmless today: every tool `serve.sh` calls lives in `/usr/bin`, `/bin` or `/usr/sbin`. Fix: match the spec to the template; soften the comment.
5. **low** — a healthy install commonly prints "not running": `RunAtLoad` fires asynchronously and `serve.sh start` can take up to 60s, while the installer's `status` runs immediately. Fix: label it a snapshot.
6. **low, optional** — `--print` claims "automated checks" that do not exist: the gate never touches `scripts/`. Fix: drop the claim, or add `bash -n` + lint to the gate.

Checks run: `bash -n` both scripts (bash 3.2.57); `--print` → `plutil -lint` OK; `plutil -convert json` + `plistlib` type audit (10 keys, expected types); bash 3.2 probes; a `sed` metacharacter experiment; an XML-comment scan; `git check-ignore` on the log path (`.gitignore:66`); grep of `backend/` for `ANTHROPIC_API_KEY`/`env_file`/`load_dotenv`; `serve.sh` read in full. Not run: `make check` (no Python/TS/CSS in the diff) and any `launchctl`.
