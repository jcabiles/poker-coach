# Contract map — P1, LAN walking skeleton (phone access over home wifi)

read-only scan, 2026-09-18 · slice of `../roadmap/phone-and-6max.md` (P1)
method: `contract-mapper` sub-agent over the dev-server and Simulate-session surfaces, plus a
direct read of the installed Vite host-check code by the Director. Every claim below cites the
file and line it came from.

## Bottom line

- **Corrected 2026-09-18 after blind review: the frontend change needs no API change, but it does
  put the whole API on the wifi.** Every frontend request is a relative path and the dev server
  rewrites it to the backend inside its own Node process — which means the dev server forwards
  any `/api` request it receives, from any interface. The backend's own port stays on loopback;
  the API behind it does not. A reviewer read real rows from the owner's database over the wifi
  through exactly this path. See the spec's "What is and is not exposed" section.
- **The backend's loopback binding is a default, not an enforcement.** uvicorn is started with no
  host argument and its command line honours `UVICORN_*` environment variables
  (`uvicorn/main.py:61`), so a stray `UVICORN_HOST=0.0.0.0` binds port 8008 to every interface.
  Reproduced during review.
- **A hand can be corrupted by two clients today, because nothing stops it.** There is no version
  column, no row lock, and no uniqueness rule on the order of decisions within a hand. This is
  not a reason to panic — it is what makes the two-client test worth running, because a race will
  actually show up instead of being masked.
- **Vite will refuse any address that is not a raw IP or `localhost`.** This decides what the
  README tells the owner to type, and it is a behaviour of the installed version, not a setting
  anyone chose.

## Surface A — how the browser reaches the API

| Contract | Where | What breaks if violated |
|---|---|---|
| Every API call is a relative path. `const BASE = "/api/v1"`, and all ~20 `fetch()` calls build on it. No file anywhere constructs an absolute `localhost` or `127.0.0.1` URL. | `frontend/src/api/client.ts:32` | Hardcoding a host would break the phone instantly, because `localhost` on the phone means the phone. This is the single contract P1 depends on, and it currently holds. |
| Vite rewrites `/api` to the backend **server-side**, inside its own Node process. | `frontend/vite.config.ts:16-18` (mirrored for `vite preview` at `:22-27`) | If this proxy were removed the browser would have to call the backend directly, which would force the backend onto the wifi — the thing this slice must not do. |
| The backend is started with no `--host` argument, so uvicorn applies its default of `127.0.0.1`. No `--host` or `0.0.0.0` string exists anywhere under `backend/`. | `scripts/serve.sh:116` | Adding `--host` to this line would put the unauthenticated API on the home wifi. The `--lan` flag must touch only the Vite line at `scripts/serve.sh:126`. |
| Cross-origin permission is hardcoded to `http://localhost:7777` alone. | `backend/app/main.py:29` | Not exercised by phone traffic, because the phone talks to Vite and Vite talks to the backend from the Mac. Leave it narrow: it is the safety net that makes a future direct-to-backend call fail loudly instead of silently working. |
| Vite accepts a request only if the address in the browser bar is an IPv4 or IPv6 literal, `localhost`, or a name listed in `server.allowedHosts`. Anything else returns "Blocked request. This host is not allowed." | behaviour of the installed dev server, version 5.4.21 pinned in `frontend/package-lock.json`. The check lives in a content-hashed build file whose name changes with every release, so it is cited by behaviour rather than by path; confirmed live by a reviewer serving a raw-IP address successfully | `http://<mac-ip>:7777` works with zero configuration. A name such as `johns-mac.local` is refused unless `allowedHosts` is extended. The owner chose raw-IP-only on 2026-09-18, so no configuration change is needed. |
| The readiness probe in the start script polls `http://localhost:<port>/`, and the comment records that Vite binds IPv6 loopback only, which is why the probe uses the name rather than the v4 literal. | `scripts/serve.sh:25-28` | **Worry withdrawn 2026-09-18 on review evidence.** `vite --host` binds dual-stack — a reviewer's `lsof` showed `IPv6 ... TCP *:7791 (LISTEN)` — so the probe still answers under `--lan` and nothing changes here. |
| The global launcher forwards exactly one argument: `exec "$HERE/../scripts/serve.sh" "${1:-start}"`. | `bin/poker-coach:17` | `poker-coach start --lan` silently drops `--lan` and starts a normal loopback stack. The owner's habitual entry point is this launcher, so a flag that only works through `scripts/serve.sh` would appear to do nothing. |
| No WebSocket, EventSource, service worker, or Content-Security-Policy usage exists in the frontend. | repo-wide grep over `frontend/src`, no matches | Nothing else in the app assumes a fixed origin, so nothing else can break when the origin changes. |
| Browser-stored preferences are per-origin. | `frontend/src/App.tsx:70,90`, `frontend/src/components/SimulateView.tsx:57-60` | The phone browsing `http://<mac-ip>:7777` gets storage entirely separate from the Mac's `http://localhost:7777`. Theme, speed and the resume pointer will all start empty on the phone. This is expected, and it is exactly the problem slice P4 exists to solve. |

## Surface B — what two clients on one session actually touch

| Contract | Where | What breaks if violated |
|---|---|---|
| Submitting a hero action reads the hand state, checks only "is it the hero's turn", and commits once at the end. There is no row lock and no re-read. | `backend/app/services/sim_session.py:967-1048`, guard at `:977`, commit at `:1045` | Two requests that arrive together both read the same starting state, both pass the guard, and the second commit overwrites the first. This is a lost update with nothing in the schema able to detect it. |
| No version or optimistic-lock column exists on either the session row or the hand row. | `backend/app/db/models.py:45-93` | Nothing today can reject a decision submitted against a stale view of the hand. P4 is where such a check would be added. |
| The position of a decision within a hand is computed as the count of decisions already stored, and no uniqueness rule covers it. | `backend/app/services/sim_session.py:986,997`; `backend/app/db/models.py:95-144` | Two concurrent submits can both be stored at the same position. This is the measurable symptom, and it gives the test a precise query. |
| SQLite runs with no write-ahead-logging pragma and no explicit lock timeout, so Python's five-second default applies. | `backend/app/db/session.py:15` | Brief overlap is retried silently rather than failing; sustained overlap surfaces as a "database is locked" error. Either outcome is a finding, and neither is currently guarded. |
| The browser keeps the resume pointer in one browser-storage entry named `simulate.session_id`, shared by every tab of the same origin. | `frontend/src/components/SimulateView.tsx:57`, written at `:456`, cleared at `:533` | Two tabs on the Mac therefore land on the **same** session, which is what the two-client test wants. Each tab still holds its own in-memory copy of the hand, so acting in one leaves the other stale — that staleness is the thing being measured. |
| Shared singletons exist but are not written per request: the grading provider is a module-level instance and the content packs are memoised. | `backend/app/services/sim_session.py:190-202` | Nothing observed mutates them per request, so they are not a concurrency hazard for this test. Not traced exhaustively into the provider's internals. |
| Graded decisions fan out into drill-attempt rows tagged `source="simulate"`, which feed the stats and leak reports. | `backend/app/services/sim_session.py:1019-1031`; consumers in `frontend/src/api/client.ts` | A race that duplicates a decision would also double-count it in the leak and street reports, so the damage is not confined to one hand. |

## Unknowns, stated rather than guessed

- Whether real overlapping writes produce a lost update, a "database is locked" error, or both is not decidable from the code. That is precisely what the two-client test measures.
- The grading provider was not traced exhaustively for request-scoped mutable fields; the module comment asserts a single instance by design.
