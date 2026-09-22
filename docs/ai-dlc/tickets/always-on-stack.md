# Tickets — Always-on stack

status: **approved (pre-authorized by --auto-build invocation, 2026-09-22)** — covers T1–T2 exactly
as written and nothing else. spec: `../specs/always-on-stack.md` · roadmap:
`../roadmap/phone-and-6max.md` (NEXT "Always-on stack", promoted 2026-09-22).

## Shape of the work

One small code ticket (shell + plist + README), one docs ticket the Director does. Worktree
`$TMPDIR/wt-ao` on branch `feat/always-on-stack`, stacked on the P3b head `2cd4782`. No contract
scan was spawned: the whole surface is `scripts/serve.sh` (242 lines, read by the Director) and the
README's phone section.

```
T1 (implementer) ─→ fan-in: bash -n + --print + plutil + make check + blind refuter ─→ T2 (docs) ─→ PR after #233 merges
```

---

### T1 — plist template, install and uninstall scripts, README section

- **Owns:** new `scripts/always-on/com.poker-coach.serve.plist.tmpl`, new
  `scripts/always_on_install.sh`, new `scripts/always_on_uninstall.sh`, `README.md` (the new
  "Always on" subsection only).
- **Imitate:** `scripts/serve.sh` for style and repo anchoring; `scripts/teardown_probe_access.sh`
  for an owner-run script's shape.
- **Do:** spec items 1–4 exactly.
- **Acceptance:** spec Verify-by, sandbox legs: `bash -n` on both scripts; `--print` renders a
  plist that passes `plutil -lint`, carries the absolute repo path, `--lan start`, and a PATH
  starting with the resolved node directory; the install script refuses when `node` is missing
  (prove with `PATH=/usr/bin:/bin` and `--print`) and when run as root (read the check; do not run
  as root); `make check` green.
- **Done-condition:** the commands above exit 0 from the worktree, in the report with their output.
- **Do not:** touch `serve.sh`; run `launchctl` or write to `~/Library` (the sandbox forbids it and
  the owner does it); add a dependency.

### T2 — roadmap, ledger, log, Resume (Director)

- **Owns:** `docs/ai-dlc/roadmap/phone-and-6max.md`, `docs/ai-dlc/ledger/phone-and-6max.md`,
  `docs/ai-dlc/log.md`, `docs/ai-dlc/profile.md`.
- **Done-condition:** the roadmap's Always-on entry carries the build note and the owed owner legs;
  the ledger has the review round; Resume points at the run's close-out.
