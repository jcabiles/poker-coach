# Spec — Always-on stack (launchd keeps the trainer up for the phone)

status: **rev 2, APPROVED** (rev 2 folds the blind review: `AbandonProcessGroup`, calendar-interval wake firing, the loopback wedge, the worktree guard, the coach-key note, the ProcessType correction)
status history: rev 1 — pre-authorized by the owner's `/ai-org:spec --auto-build` invocation,
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
   - `RunAtLoad` true; `KeepAlive` false (the launcher backgrounds the two servers and exits, so
     keep-alive would relaunch it in a loop); `AbandonProcessGroup` true — without it launchd kills
     every process in the launcher's process group when the launcher exits, which is exactly the
     backgrounded uvicorn and vite (`launchd.plist(5)`; `nohup` changes signal disposition, not the
     group). Schedule: `StartCalendarInterval` with twelve entries, `Minute` 0, 5, …, 55. Not
     `StartInterval`: the man page says an interval that falls during sleep is missed, while a
     calendar entry missed during sleep fires on wake. That wake firing is what gives "recover
     after wake": the launcher finds the servers gone and starts them, or finds them alive and
     exits 0. Cost: twelve dictionary entries pinned to wall-clock minutes.
   - `WorkingDirectory` `@REPO@`
   - `EnvironmentVariables`: `PATH` = `@NODE_DIR@:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin`
     (Vite's shim is `#!/usr/bin/env node`; every other tool `serve.sh` calls lives in the
     defaults; `/opt/homebrew/bin` is not listed because `@NODE_DIR@` is it on a Homebrew node,
     and nothing else from Homebrew is needed).
   - `StandardOutPath` / `StandardErrorPath` `@REPO@/local/always-on/launchd.log` (both to one file,
     appended by launchd).
   - `ProcessType` is not set (unspecified = launchd's standard class with light resource
     limits; `Background` is a separate, more throttled class). The abandoned servers inherit the
     job's class; if the phone ever feels sluggish, `ProcessType` `Interactive` is the one-key lever.
2. **`scripts/always_on_install.sh`** — owner-run, idempotent. Resolves the repo root from its own
   location; finds `node` with `command -v node` and refuses with a clear message if absent;
   creates `local/always-on/`; refuses a repo or node path containing `|`, `&` or `\` (sed
   delimiter and replacement metacharacters — a corrupted path would still lint clean); renders the
   template with `sed` to a temp file, validates it with `plutil -lint`, and only then moves it to
   `~/Library/LaunchAgents/com.poker-coach.serve.plist`; after `bootstrap`, verifies the job is
   loaded with `launchctl print` and retries up to three times (bootout can return before teardown
   completes), exiting 1 with a re-run message otherwise;
   refuses when `.git` is a file rather than a directory (a linked worktree, which is deleted at
   cleanup and would leave the agent firing at a dead path — run it from the main checkout);
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
   Mac is awake (the ruling's accepted cost). Two more facts the section must state: (i) if the owner
   hand-starts the stack WITHOUT `--lan`, the launcher exits 1 ("already running, but frontend is
   loopback only") every five minutes and cannot fix that state — run `scripts/serve.sh restart
   --lan`; (ii) a launchd-started backend has no `ANTHROPIC_API_KEY` in its environment (the plist
   carries only PATH, and a key is never written to a plist), so the coach falls back to template
   prose for that process's lifetime; a hand-started stack from a shell that loaded the key keeps the
   live coach. Wording about the log directory: launchd will not create it; the installer does.
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
