# Tickets — P1, LAN walking skeleton and two cheap tests

status: **rev 2, APPROVED** — pre-authorized by John's `/ai-org:spec --auto-build` invocation,
2026-09-18. The approval covers T1–T6 exactly as written below and nothing else. The two phone
legs of the slice's pass/fail, (a) and (d), stay with John; this build does not tick the roadmap box.
spec: `../specs/phone-lan-p1.md` (rev 2) · contract map: `../contracts/phone-lan-p1.md` ·
ledger: `../ledger/phone-and-6max.md` (round 2) · roadmap: `../roadmap/phone-and-6max.md` (slice P1)

✅ **Settled 2026-09-18.** Both blind reviewers proved that this design does put the
unauthenticated API on the wifi, contradicting the roadmap. The owner ruled: accept the exposure,
because the home wifi is trusted and the phone cannot play without the API, and correct the text.
The roadmap is corrected at rev 4 and the spec at rev 2. T3 is therefore unblocked, and its job is
to state the real boundary rather than the old claim.

## Shape of the work

Six small tickets. No Python, no TypeScript, no CSS, no schema change — which is why `make check`
is expected to be unmoved, and why running it proves the claim rather than tests it.

```
T1 (serve.sh)   ─┐
T2 (launcher)   ─┼─→ T3 (README, gated on the owner's ruling) ─┐
T4 (stale docs) ─────────────────────────────────────────────  ┼─→ T5 (measurement) ─→ T6 (close-out)
```

T1, T2 and T4 are independent and may run together. The initiative ledger is written by T4, T5 and
T6 in that order, so it always has exactly one owner at a time.

**Build in a worktree.** The shared checkout is used by other sessions; branch work does not happen
there.

**Baseline first:** record what `make check` reports on a clean tree, so "unchanged" below has a
number behind it.

---

### T1 — `--lan` on the start script, and a loopback binding that is enforced

- **Owns:** `scripts/serve.sh`.
- **Imitate:** the file's own style — repo-anchored patterns, comments that explain *why*,
  `_wait_ready` for readiness. `scripts/owner-run.sh` for the register the owner reads.
- **Do:**
  1. **Add `--host 127.0.0.1` to the uvicorn launch at `scripts/serve.sh:116`.** It passes no host
     today and relies on a default that the environment can override: uvicorn's command line is
     declared with `auto_envvar_prefix="UVICORN"` (`uvicorn/main.py:61`), so a stray
     `UVICORN_HOST=0.0.0.0` would put the API on the wifi with no flag and no visible change.
  2. Parse `--lan` from anywhere in the argument list into two plain string variables — one for the
     subcommand, one holding either `--host` or the empty string. **No bash array:** the shebang
     resolves to whichever bash is first on the path, 5.3 here but the system's 3.2 elsewhere,
     where an empty array under `set -u` aborts the script. An unrecognised `-` option, or a second
     bare argument, exits 2 with the usage line.
  3. Append that variable to the frontend launch at `scripts/serve.sh:126` only.
  4. Report the binding in three places, all reading the running process's command line
     (`_pid_matches` at `scripts/serve.sh:39-47` already does this with `ps -ww -o command=`):
     `status` on every call; the `--lan`-requested early return, which must say the running server
     is on loopback, name `restart --lan`, and exit non-zero; and the flagless early return, which
     must say the running server is on the wifi rather than implying the default held.
  5. Under `--lan`, after readiness, print the wifi address via `ipconfig getifaddr en0` falling
     back to `en1`; if neither answers, print the loopback line plus a one-line hint and do not
     fail.
- **Note for a sandboxed agent:** `ipconfig getifaddr` is blocked here — both interfaces exit 1
  with `ipconfig_server_port failed` — so you can only exercise the fallback branch. Say which
  branch you saw. The dev server writes its own `Network: http://<ip>:<port>/` line into
  `.frontend.log` under `--host`, and that is readable; use it.
- **Acceptance:** `start`, `stop`, `restart`, `status` unchanged when `--lan` is absent;
  `restart --lan` brings the frontend up on all interfaces and reports ready rather than timing
  out; `start --lan` against a running loopback stack exits non-zero with the restart instruction;
  a bare `start` against a running wifi stack says so; `./scripts/serve.sh --nonsense` exits 2;
  and with `UVICORN_HOST=0.0.0.0` exported, `restart --lan` still leaves the backend on
  `127.0.0.1:8008`.
- **Done:** every command above pasted into the pull request; `make check` unchanged from baseline.

---

### T2 — The global launcher stops dropping arguments

`bin/poker-coach:17` forwards exactly one argument, so `poker-coach start --lan` would silently
start an ordinary loopback stack.

- **Owns:** `bin/poker-coach`.
- **Do:** forward every argument; a bare call still defaults to `start`.
- **Acceptance:** `poker-coach` alone still starts the stack; `poker-coach status` still reports
  status; and **from a stopped state** `poker-coach start --lan` reaches the same sockets as
  `./scripts/serve.sh start --lan`. Testing it against an already-running stack proves nothing,
  because the early return would report success either way.
- **Done:** all three run; `make check` unchanged.

---

### T3 — README section, "Play from your phone"

- **Owns:** `README.md`. **Depends on:** T1.
- **Imitate:** the existing "Setup & run" block, `README.md:51-78` — command-first, with a block
  quote for caveats.
- **Do:** cover the command through both entry points; that the address is printed by the script
  and must be the raw IP, because the dev server refuses names it does not recognise; adding it to
  the Android home screen via Chrome's menu; that the phone only works while the Mac runs the
  stack; that a new address from the router breaks the saved shortcut until it is recreated; and
  that macOS may prompt to allow incoming connections for Node the first time.
- **State the boundary accurately**, per the spec's "What is and is not exposed" section: the
  backend port stays on the Mac, but the whole API is reachable through the frontend port while
  the flag is on, which is acceptable because the home wifi is trusted and this app has no
  accounts. **Do not write that the API is off the network** — a reviewer read real rows out of
  the live database from a wifi address through exactly this design.
- **Acceptance:** someone who has never seen this repository can follow it without asking a
  question, and no claim in it is untrue of the shipped script.
- **Done:** `make check` unchanged.

---

### T4 — Retire one stale spec, correct two stale banners

- **Owns:** `docs/ai-dlc/specs/draft-mobile-responsive.md` (deleted), `.claude/CLAUDE.md`,
  `docs/ai-dlc/START-HERE.md`, and the first new section of `docs/ai-dlc/ledger/phone-and-6max.md`.
- **Do, in this order:**
  1. Copy the four measured facts out of the draft spec into a "facts rescued from the retired
     mobile-responsiveness draft" section of the ledger: the masthead's right-hand group not
     wrapping and forcing sideways scroll on every route below roughly 400px; thirty overlapping
     seat-pod pairs on the nine-seat felt at 375px; the stats strip cramping at phone widths; and
     the two candidate felt strategies. Slices P2 and P3 are the readers.
  2. Delete the draft spec (owner-approved per-file, 2026-09-18, roadmap decision D4).
  3. Rewrite the initiative section of `.claude/CLAUDE.md` to name phone access and 6-max as the
     governing initiative, record that the bot-realism flywheel has one box still open awaiting the
     owner's Challenge-mode play session, and keep the persona-realism pause and its two blocked
     items as a short tail.
  4. Make the same correction in the first paragraph and the reading order of
     `docs/ai-dlc/START-HERE.md:7-12`. Roadmap decision D3 names only `.claude/CLAUDE.md`, but that
     file points fresh sessions at this one by name.
- **Do not:** touch `docs/ai-dlc/profile.md`, which is already correct, or any other document.
- **Acceptance, scoped to the two files being changed** — a repository-wide grep cannot pass,
  because the roadmap, this spec, these tickets and the ledger all legitimately mention both the
  deleted filename and the phrase "governing initiative":
  `grep -n "governing initiative\|Professional Teacher Rework\|bot-realism-flywheel" .claude/CLAUDE.md docs/ai-dlc/START-HERE.md`
  returns only statements that are true on the day of the change, and
  `ls docs/ai-dlc/specs/draft-mobile-responsive.md` reports no such file.
- **Done:** that grep pasted into the pull request; `make check` unchanged.

---

### T5 — Measurement (c): two clients on one session

- **Owns:** `docs/ai-dlc/ledger/phone-and-6max.md` (second new section). **Depends on:** T4.
- **Never opens `backend/data/poker_coach.db`.**
- **Do:**
  1. **Assert isolation before anything else.** From the worktree's `backend/`, with `PYTHONPATH=.`
     and the main checkout's interpreter (the worktree has no virtual environment), print
     `app.db.session.DB_PATH` and stop unless it is under the worktree. Do this *before* the
     Alembic upgrade and *before* starting any server. Observing it afterwards is not enough: if
     the isolated backend is started on the default port while the owner's stack is up, uvicorn
     fails to bind but the readiness probe gets 200 from the owner's backend
     (`scripts/serve.sh:25,122`), and the probe then writes into the real database — inflating the
     `sim_session` count the roadmap baselined on 2026-09-18.
  2. Run the Alembic upgrade against the worktree database, then start the isolated backend on a
     spare port such as 8123.
  3. Start a second dev server **from the main checkout** (it has the installed packages) with
     `BACKEND_PORT=8123 frontend/node_modules/.bin/vite --port 7778 --strictPort`.
     `FRONTEND_PORT` does nothing here: `frontend/vite.config.ts:14` hardcodes 7777 and only
     `scripts/serve.sh` translates that variable into `--port`. `BACKEND_PORT` *is* read by the
     configuration and repoints the proxy at the isolated backend.
  4. **Leg one, in turn.** Two browser tabs on that frontend, acting alternately on one session.
     Both tabs share the browser-storage entry `simulate.session_id`
     (`frontend/src/components/SimulateView.tsx:57`), so they land on the same session by design;
     each holds its own stale copy of the hand, and that staleness is what is under test.
  5. **Leg two, at once.** A throwaway script in the session scratch directory fires two
     simultaneous `POST /api/v1/simulate/session/{id}/action` requests at the same hand. Not
     committed.
  6. **Record observations, not just a query.** For each leg: what decision point each client was
     showing before it acted, what it submitted, what HTTP status came back, and the hand state and
     full ordinal sequence afterwards. An action accepted against a decision point the client was
     not showing is a finding regardless of what the ordinals say — a request carries only a
     decision with no reference to the state it was made against (`client.ts:126`) and the server
     applies it to whatever is current (`sim_session.py:970-978`), so a stale preflop fold can land
     legally on the flop with unique ordinals.
- **Scope the verdict honestly.** Leg two cannot produce a race today and its clean result is a
  tautology, not evidence: the handler and the service function are both `async def`, the only
  `await` reaches a provider method with no suspension point (`simulate.py:92`,
  `sim_session.py:967`, `heuristic.py:37`), and one worker runs it. Record that reasoning beside
  the result, and write the finding as "today's single-worker deployment serializes these
  requests", never "no race exists". Do **not** add a two-worker leg; it is out of scope.
- **Also record** that the roadmap's phrase "one continuous line in `sim_hand`" describes a table
  shape that does not exist — `sim_hand` holds one current `state_json`, not an event log
  (`models.py:79-92`) — so slice P4 is not written against a false picture.
- **Acceptance:** the ledger records each leg's observations, the full ordinal sequence, and a
  plain verdict on whether a stale client can corrupt a hand, with reproduction steps if it can.
  The roadmap moves slice P4 (one live session across devices) ahead of the 6-max slice if it can.
- **Done:** both extra servers stopped; the worktree's stray database file removed; `make check`
  unchanged.

---

### T6 — The bind checks, and closing the slice out honestly

- **Owns:** `docs/ai-dlc/roadmap/phone-and-6max.md` and the last new section of
  `docs/ai-dlc/ledger/phone-and-6max.md`. **Depends on:** T1, T2, T5.
- **Do, in this order** — each step must start from the state it claims to test:
  1. From stopped: `start`, then `lsof -nP -iTCP -sTCP:LISTEN`; record both addresses. `status`
     must report loopback.
  2. Against that: `start --lan` exits non-zero with the restart instruction.
  3. `restart --lan`, then the same socket check. The frontend must now be on all interfaces and
     **the backend must still be on `127.0.0.1` only.** Write this up as what it is: evidence that
     the backend port is not independently reachable. It is **not** evidence that the API is off
     the wifi — the frontend proxies the whole API and that is by design.
  4. With `UVICORN_HOST=0.0.0.0` exported, `restart --lan` still leaves the backend on
     `127.0.0.1:8008`.
  5. Stop everything, then run the launcher check from the stopped state.
  6. If the sandbox permits, try to reach the backend port on the Mac's wifi address and record the
     refusal. If it refuses the attempt, say so plainly; do not describe a probe that did not run.
  7. Add a dated note to the roadmap's P1 box recording that the machine-checkable legs passed and
     the two phone legs are outstanding. **Leave the box unticked** — the owner ticks it after
     playing.
- **Acceptance:** all socket outputs are in the pull request; the roadmap note is dated and names
  exactly what is still owed.
- **Done:** `make check` green, and the working tree contains nothing outside the files these six
  tickets name.
