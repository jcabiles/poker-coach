# Finding ledger — phone access + 6-max roadmap

Round 1, 2026-09-18, on roadmap rev 1. One blind reviewer per the roadmap policy: Codex is
not runnable in this sandbox (see `sandbox-tooling` notes), so Claude `refuter` (Opus) ran as
the labeled same-family fallback. Verdict FAIL: 2 blocking, 9 should-fix, 3 optional.
Report: `../reviews/phone-and-6max-roadmap-r1-claude.md`. Every finding was checked against
the code before adjudication. All 14 accepted; rev 2 folds them. Three need the owner (D1–D3
in the roadmap).

| # | Finding | Claimed | Adjudicated | Evidence checked |
|---|---|---|---|---|
| F1 | S1 names only engine/deck; the seat count is also hardcoded in `sim_session.py` (button seed/rotate, seat rows, blind-check pool), `range_estimate.py`, `play.py::assign_lineup` | blocking | **ACCEPTED** — S1 "what" lists the full surface; ease 6→4; pass/fail adds blind-check and range-panel legs | `sim_session.py:358,931,947,1532`; `range_estimate.py:58,237`; `play.py:57-61`. Verified. |
| F2 | `spot_signature()` hashes `table_size`; every Simulate spot hardcodes 9, so 6-max history merges or splits by accident | blocking | **ACCEPTED** — owner decision D1, default key as 6; signature assertion in S1 pass/fail | `srs.py:63`; `grade_map_postflop.py:127,386,455,1708`; `spot.py:100`. Verified. |
| F3 | S1's riskiest assumption is bot feel; the load-bearing claim is the position mapping, which fails for the range estimator and limped pots | should-fix | **ACCEPTED** — mapping is now S1's assumption with a headless verdict-equivalence test; bot feel moves to NEXT research | `deck.py:19-29`; `scenarios.py:73`; `grade_map_preflop.py:209-226`. Verified. |
| F4 | Hands/week rises with 6-max on its own (shorter hands) | should-fix | **ACCEPTED** — north star is occasions/week (distinct days); hands/week secondary, split by table size | Reasoning; no code needed. |
| F5 | No target and "flat is fine" makes the outcome unfalsifiable | should-fix | **ACCEPTED** — decision rule written: no rise four weeks after P1+S1 → drop LATER phone bets, cut P3 | — |
| F6 | Backend bind + CORS + API-base work is unnecessary (relative `/api/v1` proxied by Vite) and puts the unauthenticated API on the wifi | should-fix | **ACCEPTED** — P1 passes `--host` to Vite only; backend stays loopback; negative leg added | `client.ts:32`; `vite.config.ts:14-19`; `main.py:29`; `serve.sh:116,126`. Verified. |
| F7 | P4's hazard is live from P1; the two-tab test is free today | should-fix | **ACCEPTED** — P1(c) runs it; P4 reorders ahead of S1 if it corrupts | `SimulateView.tsx:456,533,617`; `sim_session.py:968-975`; `models.py:79-90`. Verified. |
| F8 | The felt-readability measurement is deferred behind S1 for a weak reason | should-fix | **ACCEPTED** — P1(d) five landscape hands; P2 gate is conditional. Owner's LAN→6-max→prototype order kept | `SimTable.tsx:42,139`. Verified. |
| F9 | P3 sits in NOW while its own text says it cannot be spec'd | should-fix | **ACCEPTED** — P3 moved to NEXT | Ordering rule §A. |
| F10 | `specs/draft-mobile-responsive.md` still says "do not build"; `.claude/CLAUDE.md` banner disagrees with the profile | should-fix | **ACCEPTED** — P1 retires the draft spec; banner is owner decision D3 (outside roadmap write authority) | Draft spec header. Verified. |
| F11 | Eight personas for eight seats; which five sit at 6-max is undecided | should-fix | **ACCEPTED** — owner decision D2, default fixed subset in the S1 spec; pass/fail leg added | `play.py:45,58-61`. Verified. |
| F12 | The owner's 6-max verdict cannot separate bot feel from 9-max grading | optional | **ACCEPTED** — one static label on the 6-max felt, in S1 | — |
| F13 | Context strip says "9-max"; ring geometry was tuned for nine pods | optional | **ACCEPTED** — label in S1; geometry left to P2's design review | `SimTable.tsx:26-40,147`. Verified. |
| F14 | Two LATER bets lead with mechanism; baseline has no query | optional | **ACCEPTED** — bets restated problem-first; SQL recorded | — |

Rejected: none.

## Fidelity pass (Director, against the interview record) + owner corrections, 2026-09-18
- Added beyond what the owner said in rev 2: the metric switch from sessions to occasions; a
  four-week scope rule; a LATER bet on phone drills; an inferred "the owner's real game is
  6-max" motive; the "acted elsewhere" acceptance detail in P4; all ICE scores; D1–D3.
- Owner ruled (rev 3): metric reverted to sessions per week; the four-week rule dropped; the
  drills bet dropped; the 6-max motive restated to the owner's words (phone fit, the format
  he sees offered); deletion of `specs/draft-mobile-responsive.md` approved (D4).
- Said but not carried: nothing found.

## Round 2, 2026-09-18 — blind dual review of the P1 spec (LAN walking skeleton)

Two blind reviewers, neither shown the requirements interview: Claude `refuter` (Opus, high
effort) and Codex `gpt-5.6-sol` (high effort). Both returned **FAIL**. Reports:
`../reviews/phone-lan-p1-r1-claude.md` (returned inline; summarised here) and
`../reviews/phone-lan-p1-r1-sol.md`. Ten findings, all verified against the code before
adjudication, all accepted. One is a **contract defect in the approved roadmap itself**, not in
the spec, and is escalated to the owner rather than folded.

**The two reviewers converged independently on the same headline defect** (C2 and S2 below),
which is the strongest signal in this round: the slice's stated security property is false.

| # | Reviewer | Finding | Claimed | Adjudicated | Evidence checked |
|---|---|---|---|---|---|
| C2/S2 | both | "The unauthenticated API never appears on the wifi" is false. Vite proxies every `/api` request it receives, including from the phone, so the whole API is reachable at `http://<mac-ip>:7777/api/...`. | blocking | **ACCEPTED — and escalated.** The claim is also in the **approved roadmap** (`roadmap/phone-and-6max.md:72-80`), which is outside this spec's authority to rewrite. Spec and tickets corrected; roadmap correction awaits the owner. | `frontend/vite.config.ts:16-18`. The Claude reviewer proved it live: `http://192.168.88.203:7791/api/v1/stats/summary` returned 200 with real data from the owner's database. Confirmed. |
| S1 | Codex | The backend's loopback binding is not enforced, only defaulted. uvicorn reads `UVICORN_*` environment variables, so `UVICORN_HOST=0.0.0.0` binds port 8008 to every interface with no flag change. | blocking | **ACCEPTED** — the uvicorn line gains an explicit `--host 127.0.0.1`. One argument, and the invariant stops depending on shell state. | `uvicorn/main.py:61` sets `auto_envvar_prefix="UVICORN"`. Reproduced: `UVICORN_HOST=127.0.0.99 uvicorn app.main:app --port 8099` logged `could not bind on any address out of [('127.0.0.99', 8099)]`, proving the variable took effect. Confirmed. |
| C1 | Claude | The concurrent-submit leg cannot fail. The request handler is `async def` whose only `await` reaches a provider with no suspension point, on a single uvicorn worker, so two requests serialize completely and the duplicate query is always clean. | blocking | **ACCEPTED** — the leg stays, but its verdict is scoped to "today's single-worker deployment serializes", and the ledger must record *why* the result came out as it did. A `--workers 2` leg was considered and rejected: it exceeds the slice's appetite and tests a deployment this app will never have, since hosting is a global no-go. | `simulate.py:92` and `sim_session.py:967` are both `async def`; the sole `await` is `_grading_provider().evaluate(...)` reaching `heuristic.py:37`, an `async def` with no await inside. Verified directly. |
| S3 | Codex | The measurement cannot detect the real hazard even in the in-turn leg: a stale client's action is applied *legally* at whatever decision point is current, producing unique ordinals and a clean query. | blocking | **ACCEPTED** — this supersedes the original query-only design. The probe now records each client's observed decision point, each HTTP result, and the resulting state, and treats an accepted stale action as a finding. | `client.ts:126` sends only a `Decision` with no state reference; `sim_session.py:970-978` reloads whatever state is current. `models.py:79-92` holds one current `state_json`, not an event line — so the roadmap's phrase "one continuous line in `sim_hand`" describes a table shape that does not exist. Confirmed. |
| C3 | Claude | The `--lan` guard is one-directional and nothing ever reports which way the frontend is bound, so a flagless `start` silently re-affirms a wifi-bound stack. | should-fix | **ACCEPTED** — `status` and the flagless early return report the binding, read from the running command line. | `scripts/serve.sh:110-112` (early return), `:166-170` (`status` prints pid and port only), `:39-47` (`_pid_matches` already reads the command line). Verified. |
| C5 | Claude | T5's isolation is justified by the wrong mechanism. The real protection is port selection, and a wrong port fails silently because the readiness probe gets 200 from the owner's already-running backend. | should-fix | **ACCEPTED** — the probe asserts `app.db.session.DB_PATH` is under the worktree and aborts otherwise, before the Alembic upgrade and before any server starts. | `scripts/serve.sh:25,122`; `backend/app/db/session.py:9-13`. The reviewer also verified that `PYTHONPATH=.` beats the editable install's `sys.meta_path` finder, so the worktree isolation itself does work. Confirmed. |
| S4 | Codex | The verification order never returns to a stopped stack, so the early-return check and the launcher check can both pass without exercising the state they claim to test. | should-fix | **ACCEPTED** — the verification steps are reordered, with an explicit stop between the loopback and launcher legs. | `specs/phone-lan-p1.md:180-189` as written. Confirmed by reading the sequence. |
| S5 | Codex | `FRONTEND_PORT=7778` does nothing when Vite is run directly; only `scripts/serve.sh` translates that variable into `--port`. | should-fix | **ACCEPTED** — the ticket now gives the literal `vite --port 7778 --strictPort` command. | `frontend/vite.config.ts:14` hardcodes 7777; `scripts/serve.sh:126` is the only translator. Verified. |
| S6 | Codex | T4's acceptance greps can never pass, because the roadmap, spec, ticket and ledger all legitimately mention both the deleted filename and the phrase "governing initiative". | should-fix | **ACCEPTED** — the checks are scoped to the two banner files and to the exact stale assertion rather than the generic phrase. | `roadmap/phone-and-6max.md:76`; `specs/phone-lan-p1.md:85`. Verified. |
| C6 | Claude | The verdict query finds duplicate positions but not gaps, while the prose calls it a "gap-free, duplicate-free" check. | optional | **ACCEPTED** — folded into the redesigned probe, which records the full ordinal sequence rather than only asking for duplicates. | `sim_decision.ordinal` and `sim_hand_id` both exist in `backend/app/db/models.py`. Verified. |
| C7 | Claude | `ipconfig getifaddr` is blocked inside this repo's sandbox, so a build agent can only ever exercise the fallback branch of the address banner. | optional | **ACCEPTED** — Vite prints `Network: http://<ip>:<port>/` to `.frontend.log` under `--host`, which is readable in the sandbox; the ticket now requires saying which branch was exercised. | Reproduced: `ipconfig getifaddr en0` and `en1` both exit 1 with `ipconfig_server_port failed`. Confirmed. |
| C8 | Claude | The contract map cites a content-hashed Vite build artifact whose filename changes with every release. | optional | **ACCEPTED** — the citation now names the behaviour and the pinned version rather than the chunk filename. | `frontend/package-lock.json` pins 5.4.21; `package.json` floors at `^5.4.0`. Verified. |
| C4 | Claude | The spec cited `scripts/serve.sh:98-100` for the already-running early return; those lines are inside `_fe_pid()`. | should-fix | **ACCEPTED — already fixed before the review landed.** The Director caught it in a citation sweep; Codex confirmed `110-112` is now correct. | `grep -n "already running (backend pid" scripts/serve.sh` returns 111. Verified. |

Rejected: none.

**Reviewer claim corrected on adjudication.** The contract map worried that binding all interfaces
would break the readiness probe, which polls `http://localhost:<port>/`. The Claude reviewer
showed empirically that `vite --host` binds dual-stack (`lsof` reports `IPv6 ... TCP *:7791`), so
the probe still answers. That worry is withdrawn.

**Housekeeping from the review itself.** The Claude reviewer started a real Vite server on port
7791 bound to every interface to prove finding C2, and the sandbox denies it — and the Director —
permission to send signals, so it is still listening. See the session report; it needs one
`kill` from the owner in a plain terminal.

## Facts rescued from the retired mobile-responsiveness draft

`docs/ai-dlc/specs/draft-mobile-responsive.md` is deleted by this slice (T4, owner-approved
per-file, roadmap decision D4). Before deletion, its four measured facts are copied here verbatim
in substance, because slices P2 (the phone mockup prototype) and P3 (phone polish) are the readers
of these numbers and the roadmap records only the headline, not the measurements.

1. **The masthead's right-hand group does not wrap.** `.masthead-right` (the EV-ledger widget) is
   `flex-wrap: nowrap` with its right edge at roughly 574px, which forces horizontal body scroll on
   every route at widths below roughly 400px. This is pre-existing and app-shell-wide — it is not
   Simulate-specific code, so a fix needs its own design review across Practice and Quiz too.
2. **Thirty overlapping seat-pod pairs on the nine-seat felt at 375px.** At that width the felt
   collapses: 30 overlapping seat pairs were measured, hero cards sit over the pot, and persona
   metadata is chopped off.
3. **The stats strip cramps at phone widths.** This is an app-shell-level layout problem, not
   confined to Simulate.
4. **Two candidate felt strategies were identified, not chosen between:** a felt `min-width` with a
   horizontal-scroll wrapper (cheap, keeps the existing geometry), versus a sub-600px compact or
   vertical seat layout (a real redesign). The draft left the choice to a Gate-1 interview that
   never happened; P2/P3 pick between them.

## P1 measurement (b) — the bind checks, 2026-09-18

**Bottom line: every machine-checkable leg of pass/fail (b) passed.** The backend port stays on
loopback even when the environment tries to move it, the frontend goes to the wifi only when asked,
and the script now tells the truth about which state it is in. The two legs that need the owner's
phone, (a) and (d), are still outstanding.

Run from an isolated worktree on ports 8123/7778 and 8124/7779, so the owner's live stack on
8008/7777 was never touched. The isolated backend wrote to the worktree's own database
(`DB_PATH` confirmed under the worktree before anything started), never to `backend/data/poker_coach.db`.

| Leg | Result | Evidence |
|---|---|---|
| Backend binds loopback only | PASS | `Python … TCP 127.0.0.1:8123 (LISTEN)` |
| Backend resists `UVICORN_HOST=0.0.0.0` | PASS | with it exported, `restart --lan` still gave `TCP 127.0.0.1:8123 (LISTEN)` |
| Frontend loopback with the flag off | PASS | `node … TCP [::1]:7778 (LISTEN)` |
| Frontend on all interfaces with `--lan` | PASS | `node … TCP *:7778 (LISTEN)` |
| `status` reports the binding | PASS | `frontend running (pid 58925 on :7779, loopback only)` |
| `start --lan` refuses a running loopback stack | PASS | exit 1, `already running, but frontend is loopback only (pid 58925 :7779) — run: scripts/serve.sh restart --lan`, and no new socket appeared |
| Flagless `start` reports the real state | PASS | exit 0, `… frontend loopback only` |

**The `UVICORN_HOST` leg is the one that matters most.** Before this slice the launcher passed no
host at all and relied on uvicorn's default, which the environment can override
(`auto_envvar_prefix="UVICORN"`). The explicit `--host 127.0.0.1` is what makes the loopback
binding a property of the script rather than of the shell it was started from.

**What this evidence is NOT.** It shows port 8008 is not independently reachable. It does not show
the API is off the wifi — the frontend port proxies the whole API by design, and that is the
accepted boundary recorded in the roadmap and the README.

**Branch not exercised:** the wifi-address banner only ever took its fallback path. `ipconfig
getifaddr` is blocked in this sandbox and exits 1 on both `en0` and `en1`, so the success path —
printing a real address — has never run and needs the owner's first `start --lan` to confirm.

**Also observed, pre-existing and not caused by this slice:** after `stop`, the uvicorn reload child
and the vite child kept their sockets. The PID file records the launching subshell, not the server
process. `scripts/serve.sh`'s stop logic is untouched by this change, so this is a separate defect;
it is recorded here rather than fixed, because fixing it is outside P1's tickets.

---
## P1 measurement (c) — the two-client probe, 2026-09-22

**Bottom line: a stale browser tab corrupts a hand silently today, so P4 (one live session across
devices) ships a per-state token and a compare-and-set on the hand write.** Both legs of the
roadmap's two-client test found corruption, each with HTTP 200 and no warning. Run by an Opus worker
against a throwaway SQLite file under `$TMPDIR`, built the way `tests/test_two_mode_simulate_gate.py`
builds its database; the owner's `backend/data/poker_coach.db` was never opened. Full report and the
three re-runnable scripts are kept on the owner's machine under `local/p1c-probe/` (gitignored).

| Situation | What the stale tab believed | What the server held | Status | Verdict |
|---|---|---|---|---|
| (i) other tab advanced the street | hand 1 preflop, hero BTN facing 5.0bb, submits `call` | hand 1 flop, hero to act, check/bet only | 400 `illegal action` | rejected, only because `call` happened to be illegal |
| (ii) other tab finished the hand and dealt | hand 1 preflop, hero LJ, submits `call` | hand 2 preflop, hero UTG2 | **200** | **corrupt** — the call was applied to a hand the player never saw and graded as its decision |
| (iii-a) villain re-raised on the same street | call = 1.0bb, pot 1.5bb | facing HJ raise to 5.5bb, call = 4.5bb, pot 13.5bb | **200** | **corrupt** — hero charged 4.5× what the screen offered |
| (iii-b) stale raise size | min-raise 2.0bb, submits raise 2.0 | min-raise now 10.0bb | 400 `outside [10.0, 98.4]` | rejected, only because the size fell outside the new band |
| leg 2: two submits at once, same decision point | identical, both current | identical | **200 and 200**, 10 of 10 runs | **corrupt** (lost update) — two `sim_decision` rows at the same ordinal; final pots 2.5–77.5bb from one start |

**Why nothing catches it.** `SimHand` holds one mutable `state_json` and no version or `updated_at`;
`SimSession` has neither; the action body is a bare `Decision` (`action`, `size_bb?`,
`size_fraction?`) with no field saying which state the client saw. The existing guard at
`sim_session.py:1008-1009` only rejects when the hero is no longer to act. Sized actions are partly
self-checking because the legal band moves; unsized ones (`fold`/`check`/`call`) never are.

**Leg 2 caveat, as the roadmap required.** The probe used two `TestClient`s on two event loops,
which is more permissive than the one-worker, one-loop deployment. The `await` between the state
read (`:1007`) and the write (`:1067`) is at `:1023` and its provider chain does no I/O today, so
production serializes by accident. Leg 2 proves the data layer has no defence, not that today's
deployment races.

**Consequence for the roadmap.** P4's conditional ("if P1(c) corrupted a hand, add a per-hand version
check") fires. The owner ruled 2026-09-22 on the shape: newest active session as the server's answer
to "current"; a stale action is rejected, the client refetches and shows one line; no migration
because the token is derived from `hand_no` and the hand's action count.

---
## Round 3, 2026-09-22 — blind review of the P4 spec (one live session across devices)

Reviewers attempted: Claude `refuter` (Opus) — ran, report `../reviews/phone-p4-live-session-r1-claude.md`
(saved by the Director from the inline return; the reviewer had no Write tool). Codex `gpt-5.6-sol` —
did not run: its nested sandbox refused every command including a file read
(`../reviews/phone-p4-live-session-r1-sol.md` holds its one-line failure). Gemini via `agy` — did not
run: authentication timed out; the owner must run `agy` once in a plain terminal. **This round is
therefore same-family only**, labelled as such; a cross-family pass on the built diff is still owed
if either tool becomes available. Verdict FAIL: 4 blocking, 5 should-fix, 3 optional. All 12
checked against the code before adjudication; 11 accepted (one narrowed), 1 rejected-as-stated and
replaced by a Director refinement. Spec rev 2 and tickets rev 2 fold them.

| # | Finding | Claimed | Adjudicated | Evidence checked |
|---|---|---|---|---|
| G1 | Watch-off fold path would send the pre-fold token with its deal and refuse its own deal; at the Challenge hand-200 gate the blind check would never appear | blocking | **ACCEPTED** — spec item 9: the deal sends `folded.state_token`; T2 acceptance cites the line | `SimulateView.tsx:702-718` never adopts the fold response; `deal_next_hand` returns the gate view. Verified. |
| G2 | No ticket owns `client.ts`, where the fetchers build the URLs | blocking | **ACCEPTED** — T2 owns `client.ts`; `getCurrentSession` joins `getSession` | `client.ts:127-147`. Verified. |
| G3 | T1 omits the test files it must edit; a required query param turns the unknown-session 404 into 422 | blocking | **ACCEPTED** — route-required, service-optional token; T1 owns the three route-level test files; Verify-by (f) keeps the 404 | `test_simulate_api.py:179`; 3 route-level files found by grep. Verified. |
| G4 | The named compare-and-set golden path commits before reading `rowcount`; copied faithfully it would commit the double-graded rows | blocking | **ACCEPTED** — spec item 4: `rowcount` before commit, `rollback()` on 0; golden path is for statement shape only | `sim_session.py:1653-1662`. Verified. |
| G5 | Two TestClients on two threads never reach the interleave window, so the concurrency test passes without the compare-and-set | should-fix | **ACCEPTED** — Verify-by (c) rewritten: two tasks on one loop, gated fake provider; test must fail with the CAS removed | `:1023` awaits a pure provider; no `busy_timeout`. Reasoning verified. |
| G6 | Keeping the ORM assignment alongside the Core UPDATE makes the compare fail every time (autoflush) | should-fix | **ACCEPTED** — spec item 4: the ORM write is replaced, `status` rides the same UPDATE | Reviewer measured rowcount 0 vs 1. Accepted on that measurement. |
| G7 | "Newest active wins" lets a stray sit-down on one device hijack the other's Challenge session; proposed: prefer the stored id while active | should-fix | **NARROWED** — the sit-down screen is only reachable after Leave (which ends the session) or a 404, so the hijack is not UI-reachable once boot lands on the current session. The real residual is pre-P4 orphan sessions outranking the live one. Resolved by ordering "current" by most recent hand activity (spec item 5), a refinement inside the owner's ruling; the stored-id-first proposal is rejected because it makes browser storage primary again, which the owner ruled against | `SimulateView.tsx:641,663,677,778,926` (every `askForMode` call follows a leave or a 404); `leave_session:1676-1682`. Verified. |
| G8 | Notice placement unspecified on the phone; inside the fixed dock it would move the buttons | should-fix | **ACCEPTED** — spec item 12: in flow on desktop, fixed just above the dock under the phone gate, never inside the dock | `app.css:6732-6751, 6924-6952`. Verified. |
| G9 | Leave takes no token; a stale tab ends the live session for both devices | should-fix | **ACCEPTED** — token on leave, 409 refuses, no auto-retry | `api/v1/simulate.py:134-137`. Verified. |
| G10 | Blind-check answers do not move the token | optional | **ACCEPTED** as a documented non-goal (spec item 6a): that flow already has first-write-wins | `SimulateView.tsx:906-934`. Verified. |
| G11 | `id desc` tiebreak is arbitrary (uuid) | optional | **ACCEPTED** — superseded by the activity ordering in G7 | `models.py:50`. Verified. |
| G12 | Line count stated as 1753; it is 1962 | optional | **ACCEPTED** — corrected | `wc -l`. Verified. |

Confirmed sound by the reviewer and not re-opened: the token changes on every seat's action (`engine.py:303`, `play.py:333`); `db.exec(update(...)).rowcount` works inside the open transaction and `rollback()` discards the pending rows; route declaration order decides (measured on FastAPI 0.139.0); no migration is needed; `_view` is the single `SessionView` assembly point.

---
## P4 fan-in, 2026-09-22 — gate, blind refuter on the diff, and a browser walk-through

**Bottom line: the build passed its gate and both checkers on everything the slice exists for; one
UI defect (the stale notice outliving the table) was found by both checkers independently and fixed
in a mechanic pass, with two cheap hardenings folded in.** `make check` was green on the integrated
worktree (backend verify OK, 84 frontend tests, build clean) before review. Tier: behaviour-touching,
so a fresh Claude `refuter` (Opus) reviewed the diff blind
(`../reviews/phone-p4-live-session-r2-claude.md`) and a browser-eyes reviewer drove the feature on
an isolated stack (`../reviews/phone-p4-live-session-r2-browser.md`). Codex and Gemini remain
unavailable (Round 3), so this pass is same-family; the browser run is the independent evidence.

| # | Finding | Source | Claimed | Adjudicated |
|---|---|---|---|---|
| H1 | The notice survives Leave and reappears on a brand-new table | both, independently | blocking / should-fix | **ACCEPTED, FIXED** — `setNotice(null)` in `clearStored`, the teardown every table exit calls. Browser evidence: notice rendered on a fresh session with no 409 in the log. |
| H2 | `HandState` is parsed before the `status != "in_progress"` check, so corrupt JSON on a completed hand gives a pydantic 400 instead of the clean message | refuter | optional | **REJECTED** — no reachable scenario writes corrupt `state_json`; the order is what lets the token check precede the "no hand" guard, which the spec requires. |
| H3 | `_view` after the Core UPDATE relies on `expire_on_commit` defaulting to True | refuter | optional | **ACCEPTED, FIXED** — explicit `db.expire(hand)` after a successful compare-and-set; one line, immune to a future session-factory change. |
| H4 | `deal_next_hand` and `leave_session` have the token check but no compare-and-set | refuter | optional | **REJECTED for this slice, RECORDED** — unreachable on one worker with a no-I/O grader; the spec scopes the compare-and-set to the hero action. Revisit if the grader ever does I/O (an LLM coach, a solver). |
| H5 | Under the phone gate the armed all-in warning can run under the notice, which paints over it | refuter | optional | **ACCEPTED, FIXED** — the warning gets `z-index` one above the notice; it is the interactive safety cue and must win. |
| H6 | The docs ticket is absent from the diff | refuter | note | **ACCEPTED** — this entry, the roadmap, `log.md` and the Resume block ride the same PR. |

**Verified by the checkers and not re-opened:** `rowcount` read before commit and rollback discards
the decision, attempt and settlement rows; the ORM state write is deleted, not supplemented; the
compare uses the exact string read; token checks precede every other refusal on action, deal and
leave; `GET /session/current` is one SELECT with a correlated `max(created_at)` subquery, declared
before the id route; the concurrency test fails without the compare-and-set (reproduced by both the
worker and the refuter, on a scratch copy); the Watch-off fold's deal carries the fold response's
token in the browser (`2.5` → `2.7`); phone dock and buttons do not move when the notice appears;
contrast 15–16:1 in both themes; every write carried a token.

**Left for the owner, from the browser run:** the isolated servers could not be stopped from the
sandbox. In a plain terminal: `kill 59019 59023 59027` (uvicorn reloader + worker on :8125, vite on
:7781). The owner's own stack on 8008/7777 was never touched.

---
## Round 4, 2026-09-22 — portrait measurement and blind review of the P3b spec

**Bottom line: the portrait pages are not broken by width but by stacking order, and the first
spec draft would have pushed the felt under the action dock on the narrowest phone; rev 2 keeps
the session controls below the felt and returns only the app chrome to the top.** Measurement
(`../reviews/phone-p3b-portrait-measurement.md`, headless Chromium at 412×915 / 393×851 / 360×800
+ 1280×800 baseline): five of seven screens have zero sideways overflow at every width; the
masthead sits 585–879px below the fold with tab order contradicting visual order; History overflows
12px at 360; `.statstrip` clips 10px of itself; ten in-session controls are under 44px; the 6-max
felt in portrait has 8–11 overlapping pod pairs (out of scope by ruling, the rotate hint's reason);
contrast has zero failures. Reviewer: Claude `refuter` (Opus), blind; Codex and Gemini unavailable
(Round 3), same-family round. Report `../reviews/phone-p3b-portrait-r1-claude.md`. Verdict FAIL:
2 blocking, 5 should-fix, 1 optional. All 8 checked against the code and ACCEPTED; spec rev 2 folds
them.

| # | Finding | Claimed | Adjudicated | Evidence checked |
|---|---|---|---|---|
| J1 | Returning the session control cluster above the felt stacks ~465px of chrome over a 239px table; at 360×800 the table renders under the dock | blocking | **ACCEPTED** — `.simulate .sim-topbar` keeps `order: 2` in portrait; new Verify-by (b2) | measurement figures (masthead 181, cluster 284, stage 239, dock 113). Arithmetic verified. |
| J2 | The touch floor under the whole gate grows Practice's mode chips in landscape, above the drill table | blocking | **ACCEPTED** — `.mode-chip` and `.history-filter` floors are portrait-only; new Verify-by (h) | `App.tsx:436`; `app.css:1393`. Verified. |
| J3 | `.tt-opt` is an aria-hidden span in a 40px clipped track | should-fix | **ACCEPTED** — floor on `.theme-toggle` only | `app.css:94-104`; `App.tsx:373`. Verified. |
| J4 | `.sim-speed-input` is an invisible overlay; a height makes a click-catcher | should-fix | **ACCEPTED** — floor on `.sim-speed-face` | `app.css:3491-3502`. Verified. |
| J5 | The `.nav-tabs` reset omits six gate declarations | should-fix | **ACCEPTED** — enumerated | `app.css:6797-6815`. Verified. |
| J6 | Hint placement contradicts the measurement's assumption | should-fix | **ACCEPTED** — inserted inside `.sim-main` before `<SimTable>` | `SimulateView.tsx:1330-1332`. Verified. |
| J7 | One-axis `overflow-x: visible` computes to `auto` | should-fix | **ACCEPTED** — wrap only | `app.css:1483`; CSS Overflow rule. Verified. |
| J8 | Inert `min-width: 0`; wrong overflow comparison in Verify-by | optional | **ACCEPTED** — both corrected | `app.css:5077-5080`. Verified. |

Also recorded from the review: the 9px "NEW" tag in the masthead EV widget becomes the first thing on
the portrait page and is out of scope; with the reveal button hidden in portrait the 128px strip is
dead space on non-Simulate routes, which rev 2 removes with `.app:not(:has(.simulate))`.
