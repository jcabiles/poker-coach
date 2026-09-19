# Blind review — P1 spec (LAN walking skeleton) — Claude `refuter`, Opus, high effort

2026-09-18. Blind: the reviewer was given the spec, the contract map, the roadmap slice, the
invariants and the verify commands — not the requirements interview or any Director reasoning.
The agent returns inline rather than to a file; this is its report as returned.

**verdict: FAIL** (text-level, not design-level — both blockers are fixed by editing the
spec/ticket wording and the ledger requirement; the build itself is sound)

## Blocking

**1. The slice's headline safety claim is false, and the plan mandates publishing it.**
Where: `specs/phone-lan-p1.md:16-20, 80-81, 182-184`; `tickets/phone-lan-p1.md:89, 163-165`;
`frontend/vite.config.ts:17`.
Evidence — the reviewer started `vite --port 7791 --strictPort --host` in this repo's frontend
and probed the Mac's own wifi address:

```
http://192.168.88.203:7791/                     -> 200  bytes=1669
http://192.168.88.203:7791/api/v1/health        -> 200  bytes=15
http://192.168.88.203:7791/api/v1/stats/summary -> 200  bytes=104
http://192.168.88.203:7791/api/v1/drill/next    -> 200  bytes=5014
```

The last two are real data from the owner's live database, served over the wifi with no
authentication, through the proxy rule that covers the whole `/api` prefix.
Failure scenario: any device on the home wifi reads training data, or posts to
`/api/v1/simulate/session/{id}/action` and mutates a live hand. The roadmap's no-go ("the backend
port never binds beyond localhost") is satisfied; the defect is that the spec states a security
*property* that does not hold and then requires it published. T3's own acceptance says "No claim
in it is untrue of the shipped script", so as written T3 cannot pass its own acceptance.
Fix and its price: state what is true — only port 7777 is on the wifi, the API is reachable
through it, and that is acceptable because the home wifi is trusted. Gains: the README stops
asserting a false boundary and P4 starts from the real threat model. Costs: two sentences, no
code change.

**2. The concurrent-submit leg cannot fail, so its inevitable clean result would be recorded as
evidence for a roadmap assumption it does not support.**
Where: `backend/app/api/v1/simulate.py:92-97`; `backend/app/services/sim_session.py:967-1049`;
`backend/app/domain/providers/heuristic.py:37-38`.
Evidence: both the endpoint and `apply_hero_action` are `async def`, and the only `await` in the
path resolves to `async def evaluate(...): return self._grade(spot, action)` — no suspension
point. A grep across the provider package and `sim_session.py` for `asyncio|run_in_executor|
to_thread|anyio|httpx|aiohttp` returns nothing, and `scripts/serve.sh:116` starts one worker. A
coroutine with no suspension point runs to completion, so request B cannot begin until A has
committed.
Failure scenario: the duplicate-ordinal query returns zero rows, the ledger records "the hand
stayed one continuous line", and P4 drops its version check on evidence that only proves the
current single-worker configuration cannot interleave. Leg one (two tabs in turn) is *not*
affected — a stale client view is a real thing to measure.
Fix and its price: require the ledger to record why the result came out as it did and scope the
verdict to today's deployment. One paragraph, no extra runtime. A `--workers 2` leg would make it
falsifiable, roughly twenty minutes, but exceeds the slice's appetite — not recommended.

## Should-fix

**3. The `--lan` guard is one-directional and nothing reports which way the frontend is bound.**
Where: `specs/phone-lan-p1.md:48-54`; `scripts/serve.sh:110-112`, `:166-170`; `bin/poker-coach:17`.
Failure scenario: the owner runs `poker-coach start --lan` at 9am, then a bare `poker-coach` at
2pm, sees "already running", and concludes the flagless default held — while the frontend is
still on `*:7777`. The roadmap promises "off by default" and there is no way to check it.
Fix: have `status` and the flagless early return report the binding by reading the running command
line; `_pid_matches` at `scripts/serve.sh:39-47` already does this with `ps -ww -o command=`.
Two lines of shell, one extra word of output.

**4. The one line number a builder is told to leave alone points at the wrong function.**
`specs/phone-lan-p1.md:50` and `tickets/phone-lan-p1.md:52-53` cited `scripts/serve.sh:98-100`
for the early return; `grep -n "already running (backend pid"` returns 111, and 98-100 are the
tail of `_fe_pid()`. A builder editing by cited line number would break `stop`, `status` and
`restart`. Every other cited line number in the plan is correct.
*(Director note: corrected before this report landed.)*

**5. T5 justifies its database isolation with a protection that is not the one doing the work.**
Where: `specs/phone-lan-p1.md:106-111`; `tickets/phone-lan-p1.md:124-133`;
`backend/app/db/session.py:9-13`; `scripts/serve.sh:25, :122`.
The path derivation is real, and the reviewer confirmed the module resolution works: the editable
install registers a `sys.meta_path` finder hard-mapped to the main checkout, but `install()`
appends it after `PathFinder`, so `PYTHONPATH=.` still wins — empirically `app.db.session`
resolved to the worktree copy. What it is not is *guarded*: the real protection is port
selection, and a wrong port fails silently because `_wait_ready` probes
`http://localhost:${BACKEND_PORT}/api/v1/health`, which the owner's running backend answers 200.
Failure scenario: the isolated backend is started on the default 8008 while the owner's stack is
up; uvicorn fails to bind, the probe gets 200 from the *owner's* backend, and the probe then
writes sessions into `backend/data/poker_coach.db`, inflating the north-star count.
Fix: make step 1 assert rather than observe — print `app.db.session.DB_PATH` and abort if it is
not under the worktree, before the Alembic upgrade and before any server starts. One line.

## Optional

**6.** The verdict SQL finds duplicates but not gaps, while the prose calls it a "gap-free,
duplicate-free" check; a lost update that drops a decision leaves (0,1,3) with no duplicate.

**7.** `ipconfig getifaddr en0` and `en1` both fail inside this repo's sandbox
(`ipconfig_server_port failed`), so a build agent can only exercise the fallback branch. Vite
prints `Network: http://192.168.88.203:7791/` to its own log, which is sandbox-readable.

**8.** The contract map cites `vite/dist/node/chunks/dep-BK3b2jBa.js`, a content-hashed artifact
whose filename changes on every Vite release. The underlying claim holds (5.4.21 pinned in the
lockfile, raw-IP URL served 200 live).

## Checked and sound, so it is not re-litigated

No absolute URL exists anywhere in `frontend/src` (grep for `https?://|localhost|127.0.0.1|
0.0.0.0` returns nothing). `vite --host` binds dual-stack (`lsof` shows `IPv6 ... TCP *:7791`),
so `_wait_ready`'s `localhost` probe still returns 200 under `--lan` — the contract map's worry
about this is withdrawn. Appending `--host` after `--strictPort` keeps `FE_PATTERN` matching, so
`stop`/`status`/`restart` are unaffected. Vite's `/@fs` guard refuses everything outside
`frontend/` — `CLAUDE.local.md`, `.backend.log` and the database file all returned 403 from the
wifi address — so `--host` does not expose the repository. `docs/ai-dlc/profile.md` is already
correct, and `.claude/CLAUDE.md` plus `docs/ai-dlc/START-HERE.md:7-12` are stale exactly as the
spec describes, so the scope extension to START-HERE is justified.

## Housekeeping left by the review

The live probe left a Vite dev server running and bound to every interface: `kill 38275`
(`node vite --port 7791 --strictPort --host`). The sandbox denies signalling processes, so
neither the reviewer nor the Director can stop it. It serves only the frontend and made two
read-only GETs; it wrote nothing. Log at `$TMPDIR/vite-lan-test.log`.
