# Spec — P1, LAN walking skeleton and two cheap tests

status: **rev 2, draft, awaiting the plan gate** — written 2026-09-18, revised the same day after
both blind reviewers returned FAIL.
slice of: `../roadmap/phone-and-6max.md` (rev 3, NOW lane, slice P1), approved by the owner 2026-09-18
contract map: `../contracts/phone-lan-p1.md`
finding ledger: `../ledger/phone-and-6max.md` (round 2)
reviews: `../reviews/phone-lan-p1-r1-claude.md`, `../reviews/phone-lan-p1-r1-sol.md`

## Bottom line

Put the trainer on the owner's phone by letting the frontend dev server listen on the home wifi,
and nothing else. One flag, one launcher fix, one README section, two stale documents corrected,
and two measurements that later slices depend on. The game code is not touched.

**Rev 2 rewrites this spec after two blind reviewers independently found the same defect: the
security property rev 1 claimed is false.** Rev 1 said the unauthenticated API never appears on
the wifi. It does. The frontend dev server forwards every request whose path begins with `/api`
to the backend (`frontend/vite.config.ts:16-18`), and it does not care which network interface
that request arrived on. One reviewer proved it live, reading real rows out of the owner's
database from a phone-equivalent address on the wifi.

**What is actually true, and what this slice now says:** the backend's own port never listens on
anything but the Mac itself, so nobody can reach it directly — but the frontend port forwards the
whole API, so anything on the home wifi can use it while the flag is on. That is unavoidable: the
phone cannot play without the API, and authentication is a standing no-go for this project. It is
acceptable because the owner has ruled the home wifi trusted. It is not acceptable to write the
opposite in a public README, which is what rev 1 required.

Two further consequences, also from the reviews: the backend's loopback binding is now *enforced*
rather than merely defaulted, and the concurrency measurement is redesigned, because as specified
it could not have failed.

Owner decisions from the Gate-1 interview, 2026-09-18: serve the development build rather than a
production bundle; address the Mac by its raw IP with no configuration change; open the pull
request once the machine-checkable results are in and leave the roadmap box unticked until the
owner has played on the phone; record both measurements in the existing initiative ledger and keep
the concurrency prober out of the repository.

## Goal

One line: make `http://<mac-ip>:7777` open the trainer on a phone on the same home wifi, and
measure the two things that decide what the next two slices look like.

## What is and is not exposed — the honest boundary

This section exists because rev 1 got it wrong, and because the README and the pull request both
quote it.

- **On the wifi while `--lan` is on:** the frontend port, 7777. Through it, the entire API, with
  no authentication — anything on the home network can read training statistics and can submit
  actions into a live hand.
- **Never on the wifi:** the backend port, 8008. It is bound to `127.0.0.1` explicitly, so it
  cannot be reached from another device even when the frontend is exposed.
- **Also not exposed:** files outside `frontend/`. The dev server's filesystem guard refused
  `CLAUDE.local.md`, the log files and the database file with 403 when a reviewer tried them from
  a wifi address.
- **Off by default, and checkable:** without the flag the frontend listens on loopback only, and
  `status` reports which of the two states the running server is in.

The accepted risk is a device on the home wifi. The owner ruled that trusted on 2026-09-18, and
authentication is a global no-go for this project.

## Behaviour

### 1. `--lan` on the start script

`scripts/serve.sh` learns one option, `--lan`, valid alongside any subcommand. It appends the dev
server's `--host` argument to the frontend launch line at `scripts/serve.sh:126` and changes
nothing else about how the frontend starts.

Argument parsing avoids bash arrays. The script's `#!/usr/bin/env bash` resolves to whichever bash
comes first on the path: version 5.3 from Homebrew on this machine, but the system's 3.2 on a
machine without it, and in 3.2 an empty array expanded under `set -u` aborts the script. Two plain
string variables — one holding the subcommand, one holding either `--host` or the empty string —
cost nothing and remove the question. An unrecognised `-` option exits 2 with a usage line rather
than being passed through to the dev server.

### 2. The backend's loopback binding becomes enforced, not defaulted

The uvicorn launch at `scripts/serve.sh:116` gains an explicit `--host 127.0.0.1`.

Today it passes no host at all and relies on uvicorn's default. That default is overridable from
the environment: uvicorn's command line is declared with `auto_envvar_prefix="UVICORN"`
(`uvicorn/main.py:61`), so a stray `UVICORN_HOST=0.0.0.0` in a shell profile or a direnv file
would put the unauthenticated API on the wifi directly, with no flag and no visible change. This
was reproduced during review: with `UVICORN_HOST=127.0.0.99` set, uvicorn logged
`could not bind on any address out of [('127.0.0.99', 8099)]`, which is only possible if the
variable reached it.

One argument, and the single most important property of this slice stops depending on the shell
it was started from.

### 3. The already-running case must not lie, in either direction

`start` returns early when both servers are already up (`scripts/serve.sh:110-112`), and `status`
(`scripts/serve.sh:166-170`) prints only a process id and a port. Neither says how the frontend is
bound, so today the owner has no way to answer "is my app on the wifi right now?".

- When `--lan` is requested and the frontend is already running on loopback, the script says so,
  tells the owner to run `restart --lan`, and exits non-zero.
- When `--lan` is **not** requested and the frontend is already running **on the wifi**, the early
  return says so rather than implying the flagless default held.
- `status` reports the binding for the frontend on every call.

All three read the binding from the running process's command line. `_pid_matches`
(`scripts/serve.sh:39-47`) already reads it with `ps -ww -o command=`, so this is a few lines and
no new mechanism. Without this, the roadmap's promise that the network binding is "off by default"
is unverifiable by the person relying on it.

### 4. The start banner prints the address to type

Under `--lan`, after the readiness probe, the script prints the wifi address as well as the
loopback one, resolving it with `ipconfig getifaddr en0` and falling back to `en1`. If neither
answers it prints the loopback line plus a one-line hint, and does not fail.

`ipconfig` is blocked inside this repository's sandbox, so an agent building this can only ever
exercise the fallback branch and must say which branch it saw. The dev server prints the address
itself under `--host`, as a `Network: http://<ip>:<port>/` line in `.frontend.log`, and that line
is readable in the sandbox — so it is the check to use there.

### 5. The global launcher forwards every argument

`bin/poker-coach:17` currently forwards exactly one argument, so `poker-coach start --lan` would
silently drop the flag and start an ordinary loopback stack. It becomes a forward of all
arguments, with a bare call still defaulting to `start`.

### 6. README — "Play from your phone"

A new section under "Setup & run" covering: the command through both entry points; that the
address is printed by the script and must be the raw IP, because the dev server refuses names it
does not recognise; adding it to the Android home screen through Chrome's menu; that the phone
only works while the Mac runs the stack; that the router may hand the Mac a different address
later, which breaks the saved shortcut until it is recreated; and that macOS may raise an
incoming-connection prompt for Node the first time.

It states the boundary from the section above **accurately**: the backend port stays on the Mac,
but the API is reachable through the frontend port while the flag is on, which is acceptable
because the home wifi is trusted and this app has no accounts. It must not claim the API is off
the network.

### 7. Two stale documents corrected

- `docs/ai-dlc/specs/draft-mobile-responsive.md` is deleted. The owner approved this per-file on
  2026-09-18 (decision D4 in the roadmap). Its four measured facts are carried into the ledger
  first, because slices P2 and P3 are the readers and the roadmap records only the headline: the
  masthead's right-hand group not wrapping and forcing sideways scroll on every route below
  roughly 400px wide; thirty overlapping seat-pod pairs measured on the nine-seat felt at 375px;
  the stats strip cramping at phone widths; and the two candidate felt strategies.
- `.claude/CLAUDE.md` still heads its initiative section "Professional Teacher Rework" and its
  correcting line still names the bot-realism flywheel as governing. Both are stale. The section
  is rewritten to name **phone access and 6-max** as the governing initiative, to record that the
  flywheel has one box still open awaiting the owner's Challenge-mode play session, and to keep
  the persona-realism pause and its two blocked items as a short tail.

  **Scope note, beyond the roadmap's wording.** Roadmap decision D3 names only `.claude/CLAUDE.md`.
  `docs/ai-dlc/START-HERE.md:7-12` says the same stale thing, and the `.claude/CLAUDE.md` banner
  points fresh sessions at it by name, so fixing one and not the other leaves the trap in place.
  This slice corrects both. `docs/ai-dlc/profile.md` is already correct and is not touched.

### 8. Measurement (c) — two clients on one session

Run against an **isolated stack**, never the owner's training database, and record observations
rather than a single query result.

**Isolation.** The database path is derived from the source tree's own location
(`backend/app/db/session.py:9-13`) with no environment override, so a backend started from a git
worktree writes to that worktree's own file. Isolation therefore depends on starting the right
backend, and a mistake is silent: the readiness probe polls
`http://localhost:${BACKEND_PORT}/api/v1/health` (`scripts/serve.sh:25,122`), which the owner's
already-running backend answers with 200 on the default port. So the probe **asserts** its
database path — prints `app.db.session.DB_PATH`, aborts unless it is under the worktree — before
the Alembic upgrade and before any server starts. This matters because the initiative's north-star
measure counts rows in `sim_session`, baselined three days earlier.

**Why the design changed.** Rev 1 asked one question — are there duplicate decision positions
within a hand — and both reviewers showed that question cannot return a useful answer:

- The simultaneous-submit leg cannot produce a race at all. The request handler and the service
  function are both `async def`, and the only `await` in the path reaches a provider method with
  no suspension point (`simulate.py:92`, `sim_session.py:967`, `heuristic.py:37`), on a single
  worker. Request B's body cannot begin until A has committed. The clean result is a tautology,
  not evidence.
- The in-turn leg can corrupt a hand **without** producing a duplicate. A request carries only a
  decision, with no reference to the state it was made against (`client.ts:126`), and the server
  applies it to whatever state is current (`sim_session.py:970-978`). So a stale tab's
  preflop-intended fold is legally applied on the flop, ordinals stay unique, and the query
  reports clean.
- The roadmap's phrase "one continuous line in `sim_hand`" describes a table shape that does not
  exist: `sim_hand` holds one current `state_json`, not an event log (`models.py:79-92`).

**What the probe records instead.** For each leg: what decision point each client was showing
before it acted, what it submitted, what HTTP status came back, and what the hand state and the
decision rows looked like afterwards. An action accepted against a decision point the client was
not showing is a finding, whatever the ordinals say. The ordinal sequence is recorded in full —
not just tested for duplicates — so a gap is visible too.

**Scope the verdict honestly.** The simultaneous leg's finding is "today's single-worker
deployment serializes these requests", never "no race exists". A two-worker leg would make the
question falsifiable, and it is deliberately not in scope: it exceeds the slice's appetite and
tests a deployment this app will never have, because hosting is a global no-go.

### 9. Measurement (d) — five landscape hands, owner-run

The owner opens the printed address on the Android phone, turns it sideways, and plays five hands
on the nine-seat felt, recording whether seat pods overlap and whether the page scrolls sideways.
This gates slice P2: a clean result makes P2's felt screen a confirmation, a bad result sends the
felt to problem-framing first. The spec's job is to hand the owner a short checklist and a place
to write the answer.

## Out of scope

No authentication, PIN, or HTTPS. No restriction of which devices may use the API through the
frontend port — an address allowlist was considered and rejected as new mechanism the owner did
not ask for, brittle under a changing phone address. No layout, CSS, or component work: the
landscape measurement records problems, it does not fix them. No installable-app manifest or
offline support. No concurrency guard, version column, or migration; that is slice P4. No two-worker
concurrency leg. No 6-max work. No production-bundle serving path. No `allowedHosts` entry in the
dev server configuration. No new dependency. No deletion of rows from the owner's training
database.

## Constraints

- The domain core under `backend/app/domain/` takes no web or database imports; this slice adds no
  Python at all, so the constraint holds by construction.
- No schema change, therefore no Alembic migration. `spot_signature()` is untouched.
- No frontend source changes, therefore no edit to the hand-maintained API types.
- Design tokens, contrast and focus rules are not engaged, because no CSS changes.
- Touch only the files this spec names.
- Branch work happens in its own worktree, never the shared checkout.

## Golden-path files to imitate

- Shell script with option parsing, readiness probing and plain-English comments:
  `scripts/serve.sh` itself, and `scripts/owner-run.sh` for the register the owner reads.
- Launcher delegation: `bin/poker-coach`.
- README section shape and tone: the existing "Setup & run" block, `README.md:51-78`.
- Ledger entry shape: the round-1 and round-2 tables in `docs/ai-dlc/ledger/phone-and-6max.md`.

## Verify-by

Ordered so that each check starts from the state it claims to test. Rev 1's order let two checks
pass without exercising their states.

1. `make check` exits clean. It is expected to be unaffected — no Python, TypeScript or CSS
   changes — and running it proves that.
2. From **stopped**: `./scripts/serve.sh start`. Then `lsof -nP -iTCP -sTCP:LISTEN` shows the
   frontend on loopback only and the backend on `127.0.0.1:8008`. `status` reports the frontend as
   loopback-bound.
3. Against that running loopback stack: `./scripts/serve.sh start --lan` prints the restart
   instruction and exits non-zero.
4. `./scripts/serve.sh restart --lan`. The same socket check now shows the frontend on all
   interfaces and **the backend still on `127.0.0.1` only** — that is, port 8008 is not
   independently reachable. `status` reports the frontend as wifi-bound. A bare
   `./scripts/serve.sh start` against this state says the stack is on the wifi rather than
   implying the default held.
5. With `UVICORN_HOST=0.0.0.0` exported, `./scripts/serve.sh restart --lan` still leaves the
   backend on `127.0.0.1:8008`. This is the check that the explicit host argument works.
6. **Stop both servers.** Then `poker-coach start --lan` from the stopped state reaches the same
   sockets as step 4, proving the launcher no longer drops the flag.
7. `stop` and `status` behave unchanged with and without the flag.
8. The two-client probe runs on the isolated worktree stack, having asserted its database path
   first, and its observations are recorded whatever they show.
9. Owner leg, after merge: the phone opens the printed address, deals and grades a hand, and five
   landscape hands are played and reported.

Do not describe a probe that did not run. If the sandbox refuses an attempt to reach the Mac's own
wifi address, say so and let the socket check stand as the evidence for step 4.

## Definition of Done

Done means: every acceptance criterion in the ticket file passes; `make check` exits clean;
nothing outside the files this spec names has changed; no document shipped by this slice claims
the API is off the network; the ledger carries both measurement results and the four facts
rescued from the deleted draft; and the roadmap's P1 box stays unticked, with a dated note
recording that the machine-checkable legs passed and the phone legs are outstanding.
