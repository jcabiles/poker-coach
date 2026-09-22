# Spec — Always-on stack (launchd keeps the trainer up for the phone)

status: **rev 1, APPROVED** — pre-authorized by the owner's `/ai-org:spec --auto-build` invocation,
2026-09-22, after a frontloaded interview (rulings below). slice of: `../roadmap/phone-and-6max.md`,
NEXT item "Always-on stack" (promoted 2026-09-22). tickets: `../tickets/always-on-stack.md`.
Stacks on P3b (PR #233); its PR opens after #233 merges.

## Bottom line

The phone only works while the Mac runs the stack, and today the owner starts it by hand. This
slice ships a launchd user agent that runs the existing launcher with `--lan` at login and re-runs
it every five minutes (which is what brings the stack back after a sleep or a crash, since the
launcher is a no-op when the stack is already up), plus an install script and an uninstall script
the owner runs once in a plain terminal. Nothing in the app changes. The one trap is that launchd
gives programs almost no PATH, and Vite's launcher needs `node` on it; the install script bakes the
owner's node directory into the plist.

## Owner rulings (2026-09-22, do not re-ask)

Start at login AND recover after wake; always start with `--lan` (the owner accepts the API being
on the home wifi whenever the Mac is up); logs under `local/`; a plist template plus owner-run
install and uninstall scripts in `scripts/`, because the sandbox cannot write to LaunchAgents; a
short "Always on" README section. Out of scope: HTTPS, auth, anything beyond the home wifi.

## What changes

1. **`scripts/always-on/com.poker-coach.serve.plist.tmpl`** — a launchd property list with
   placeholders `@REPO@` and `@NODE_DIR@`:
   - `Label` `com.poker-coach.serve`
   - `ProgramArguments`: `/bin/bash`, `@REPO@/scripts/serve.sh`, `--lan`, `start`
   - `RunAtLoad` true; `StartInterval` 300; `KeepAlive` false (the launcher backgrounds the two
     servers and exits, so keep-alive would relaunch it in a loop). The five-minute interval is what
     gives "recover after wake": launchd runs a missed interval when the machine wakes, the launcher
     finds the servers gone and starts them, or finds them alive and exits 0.
   - `WorkingDirectory` `@REPO@`
   - `EnvironmentVariables`: `PATH` = `@NODE_DIR@:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin`
     (Vite's shim is `#!/usr/bin/env node`; `ps`, `ipconfig`, `nohup` live in the defaults).
   - `StandardOutPath` / `StandardErrorPath` `@REPO@/local/always-on/launchd.log` (both to one file,
     appended by launchd).
   - `ProcessType` `Interactive` is NOT set; `Background` is the default and correct.
2. **`scripts/always_on_install.sh`** — owner-run, idempotent. Resolves the repo root from its own
   location; finds `node` with `command -v node` and refuses with a clear message if absent;
   creates `local/always-on/`; renders the template with `sed` into
   `~/Library/LaunchAgents/com.poker-coach.serve.plist`; validates it with `plutil -lint`;
   `launchctl bootout gui/$UID/com.poker-coach.serve` if already loaded (ignoring "not loaded");
   `launchctl bootstrap gui/$UID <plist>`; then prints `launchctl print gui/$UID/com.poker-coach.serve`'s
   state line and runs `scripts/serve.sh status`. `--print` renders the plist to stdout and exits
   without touching launchd (this is what the build can test in the sandbox). Refuses to run as
   root. `set -euo pipefail`, repo-anchored paths, comments only for the WHY (the PATH trap, why
   KeepAlive is off, why bootout-then-bootstrap instead of `launchctl load`).
3. **`scripts/always_on_uninstall.sh`** — `bootout`, removes the plist, and says how to stop a
   stack that is still running (`scripts/serve.sh stop`); does not stop it itself, so uninstalling
   the agent mid-session does not end the owner's game.
4. **README** — an "Always on" subsection right after "Play from your phone": the one-line install,
   what it does (login + every five minutes, `--lan`), where the log is, how to uninstall, and the
   plain statement that with this installed the unauthenticated API is on the home wifi whenever the
   Mac is awake (the ruling's accepted cost).
5. **Roadmap** — the NEXT "Always-on stack" entry becomes a built item with its build note; ledger,
   log and Resume in the same PR.

## Out of scope

HTTPS, auth, a menu-bar app, a wake-triggered hook (launchd has none; the interval covers it),
changing `serve.sh`, a `KeepAlive` daemon, anything that runs as root or as a LaunchDaemon.

## Constraints

Shell only; no new dependency. `plutil` and `launchctl` are macOS built-ins. Scripts are executable,
`bash -n` clean, and follow `serve.sh`'s style (repo-anchored paths, `set -euo pipefail`, why-only
comments). Nothing in `local/` or `~/Library` is ever committed; the rendered plist lives outside
the repo. The `.gitignore` already excludes `local/`.

## Golden paths

`scripts/serve.sh` (style, readiness probe, repo anchoring); `scripts/teardown_probe_access.sh`
(an owner-run script that shows what it will do and confirms). README "Play from your phone".

## Verify-by

In the sandbox (the build): `bash -n` on both scripts; `scripts/always_on_install.sh --print` renders
a plist whose `plutil -lint -` (or a temp file) passes, whose `ProgramArguments` are the absolute
repo path and `--lan start`, and whose PATH begins with the resolved node directory; the uninstall
script's `bash -n` passes; `make check` unchanged (no Python or TypeScript touched — run it anyway).
On the owner's machine (owed): run the install; `launchctl print gui/$UID/com.poker-coach.serve`
shows `state = running` or the last exit status 0; `scripts/serve.sh status` reports both servers
with the frontend on all interfaces; after a sleep/wake or `serve.sh stop`, the stack is back
within five minutes; the log under `local/always-on/` shows the runs.

## Definition of done

Done = the sandbox Verify-by legs pass AND `make check` exits clean AND only the named files changed
AND README, roadmap, ledger, log and Resume are updated in the same PR. The owner-machine legs stay
listed as owed in the PR body.
