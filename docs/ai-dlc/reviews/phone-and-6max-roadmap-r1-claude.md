# Review R1 (Claude, blind) — phone-and-6max roadmap

## Bottom line
The roadmap is well-formed on the guardrail checklist — it passes size, pass/fail, no-gos, and per-slice assumptions — but two defects in the NOW lane must be fixed before the gate.
Slice S1 ("6-max table option") names only `engine/deck` as the code to change, while the seat count is hardcoded in at least four more places outside them, so its "1 slice" appetite is not supported by the code.
Slice S1 also walks through a one-way door it never names: `spot_signature()` already includes `table_size`, and every graded Simulate spot hardcodes `table_size=9`, so whether 6-max hands share or split the owner's spaced-repetition history is being decided by accident.

verdict: FAIL

## Findings

### 1. S1's file list is materially incomplete; the "1 slice" appetite rests on it
- id: F1
- severity: blocking
- claim: S1 says "engine/deck take the seat count from the session instead of the `_SEATS = 9` constants". The seat count is hardcoded in at least four further places that S1 does not name, two of which are directly required by S1's own pass/fail check. The slice as written would be handed to `/ai-org:spec` with a file list that misses the code the acceptance criteria exercise, and with an ease score (ICE 8·7·6) computed against that short list.
- evidence:
  - `backend/app/services/sim_session.py:1532` — `session.button_seat = (session.button_seat + 1) % 9`. S1's pass/fail requires "rotates the button through 6 seats"; this is the line that rotates it, and it is in the service, not in engine or deck.
  - `backend/app/services/sim_session.py:931` — `button_seat=secrets.randbelow(9)`. A new 6-max session can start with the button on a seat that does not exist.
  - `backend/app/services/sim_session.py:947` — `for i in range(9)` creates the `SimSeat` rows; `backend/app/db/models.py:67` documents "9 rows per session".
  - `backend/app/services/sim_session.py:358` — `pool = [seat for seat in range(9) if seat != HERO_SEAT]` picks the three seats for the Challenge-mode blind check. At 6 seats this can name seats 6, 7 or 8, which have no `SimSeat` row. This is the freshly landed two-mode-simulate feature (migration `0015_sim_session_mode.py`) and S1 does not mention it at all.
  - `backend/app/domain/table/range_estimate.py:58` — a third, independent `_SEATS = 9`, used at `range_estimate.py:237` as `opponents=sum(1 for j in range(_SEATS) if j != s and j not in folded)`. At 6 seats this counts three non-existent seats as live opponents, silently widening every estimated villain range shown in the Simulate range panel. It is not a crash, so no test would catch it.
- proposed change: Rewrite S1's "what" to name the real surface — `backend/app/domain/table/{engine,deck,range_estimate}.py`, `backend/app/services/sim_session.py` (button rotation, button seeding, seat creation, blind-check seat pool), `backend/app/domain/table/play.py::assign_lineup`, and `frontend/src/components/simulate/SimTable.tsx` — then re-score the appetite. Add "a 6-max Challenge session's blind check asks about three seats that exist" to the pass/fail check.

### 2. S1 silently decides an irreversible question about persisted grading history
- id: F2
- severity: blocking
- claim: S1's no-gos say "no change to `spot_signature()`", which correctly honours the frozen-signature invariant, but the roadmap never states the consequence. `spot_signature()` already hashes `table_size`, and every Simulate spot is constructed with `table_size=9` hardcoded. If S1 leaves those literals alone, 6-max hands merge into the owner's existing 9-max spaced-repetition items and leak statistics, permanently. If S1 changes them to 6, all 6-max spots start from an empty history and the split is permanent the other way. The roadmap's own NEXT item plans "per-format pack values with the existing `(format, pool, source)` provenance rule", which presumes the two formats are distinguishable — but by the time that research lands, the history has already been written one way or the other.
- evidence:
  - `backend/app/domain/srs.py:63` — `str(spot.game.table_size),` is one of the ten parts hashed into the preflop signature. The module docstring at `srs.py:1-9` states "Changing this function is a breaking change to persisted SRS history."
  - `backend/app/domain/table/grade_map_postflop.py:127`, `:386`, `:455`, `:1708` — every graded Simulate spot is built as `game=GameConfig(stakes=Stakes(sb=1.0, bb=2.0), table_size=9, max_buyin_bb=200.0)`. The preflop path is the same: `backend/app/domain/scenarios.py:275,442,520,611,692,770,856,946`, all `table_size=9`.
  - `backend/app/domain/spot.py:100` — `table_size: int = 9` is the model default, so an omitted value also lands on 9.
- proposed change: Make the decision explicit in S1's "what" — state whether a 6-max hand is graded and keyed as `table_size=6` or `table_size=9`, and say in one line why. Add the choice to the pass/fail check as a signature assertion (for example: the same hero hand and position at 6 and at 9 seats produce different / identical signatures, whichever was chosen). Note that this changes no code in `spot_signature()` itself, so the frozen-function invariant is honoured either way.

### 3. S1's riskiest assumption names the soft risk and omits the load-bearing code claim
- id: F3
- severity: should-fix
- claim: S1's `riskiest-assumption` is "bots playing their 9-max charts from the six latest positions feel acceptable at a 6-seat table for now" — a taste question whose answer does not change the slice's size. The claim the slice's cost actually rests on is stated as settled fact inside "what": "6-max seats carry the positions LJ, HJ, CO, BTN, SB, BB so persona packs, preflop charts and the grader are untouched". That claim is falsifiable, and it is half false. It holds for hero preflop grading and for the felt geometry; it fails for the villain-range estimator and for canonical limped-pot scenarios.
- evidence:
  - Holds: `backend/app/domain/table/deck.py:19-29` — `_ROTATION` is `[BTN, SB, BB, UTG, UTG1, UTG2, LJ, HJ, CO]`, and all six named positions exist in the `Position` enum at `backend/app/domain/spot.py:29-38`. Taking the last six preserves the number of players acting after each position, so every hero RFI and defend chart entry is genuinely the same entry.
  - Holds: `frontend/src/components/simulate/SimTable.tsx:139` filters the ring to the positions actually present, and `SimTable.tsx:42` computes `slotStyle(i, n)` from `ordered.length`, so six pods distribute evenly around the ellipse with no geometry work. The roadmap's "the felt renders a 6-seat ring" really is close to free.
  - Fails: `backend/app/domain/table/range_estimate.py:237` inflates the live-opponent count as described in F1.
  - Fails: `backend/app/domain/scenarios.py:73` — `_LIMP_SEATS = [Position.UTG, Position.LJ, Position.HJ, Position.CO]`. A 6-max limped pot is canonicalised onto a UTG limper who has no seat at the table (`backend/app/domain/table/grade_map_preflop.py:209-226`). The comment at `grade_map_preflop.py:212-213` argues limper identity is canonicalised away, so the graded verdict is probably unchanged — but "probably" is exactly what a riskiest-assumption line is for.
- proposed change: Promote the position-mapping claim to S1's `riskiest-assumption`, with `cheapest-test` = a headless run asserting that a set of 6-max hands produces the same graded verdict as the equivalent 9-max hands, and demote the bot-feel question to the NEXT research item where it already lives.

### 4. The north-star metric is confounded by the very slice meant to move it
- id: F4
- severity: should-fix
- claim: The outcome is "Simulate hands played per week (count of `sim_hand` rows by `created_at` week)". A 6-max hand has three fewer players to act, so it finishes faster in wall-clock time than a 9-max hand. S1 will therefore raise hands/week even if the owner plays exactly the same number of minutes and sessions. The metric cannot separate "the owner played more" from "the hands got shorter", which is the only thing the roadmap wants to learn.
- evidence: roadmap lines 15-20 (north-star definition) against roadmap line 54 (S1 introduces the 6-seat option). `backend/app/domain/table/engine.py:88` deals and seats `range(_SEATS)` players per hand, so seat count directly sets how many decisions each hand requires.
- proposed change: Either segment the metric by table size (report hands/week at 9 and at 6 separately, and compare each to its own baseline), or switch the headline count to playing occasions — distinct calendar days with at least one `sim_hand` row — which is seat-count neutral. State the chosen query in the roadmap so the baseline is reproducible.

### 5. The north-star has no target and no decision rule, so no result can change the plan
- id: F5
- severity: should-fix
- claim: The target is "owner sets after the first phone week", and the roadmap pre-declares that "a flat number is a real finding, not a failure". Together these mean every possible measurement is consistent with continuing. That is the unfalsifiable-assumption pattern from the guardrail checklist, applied to the outcome rather than to a slice. The LATER lane then stacks four more bets on a metric that cannot say no.
- evidence: roadmap lines 16-18; guardrail `~/.claude/skills/ai-org/reference/ROADMAP.md:170` ("if no result could disprove it, it's a restated goal, not a bet").
- proposed change: Write the decision rule now, before the data arrives, rather than the number. For example: "if hands/week (or occasions/week) has not risen by four weeks after P1 and S1 are both live, the LATER phone bets are dropped and P3's remaining scope is cut." A flat number can honestly be a finding, but it has to be a finding that changes something.

### 6. P1 contains two work items the code says are unnecessary, one of which widens network exposure
- id: F6
- severity: should-fix
- claim: P1's "what" says "`serve.sh start --lan` binds backend and Vite to the network; CORS origins and the API base come from config, not literals". The frontend never talks to the backend across origins: the API base is a relative path and Vite proxies it server-side. So the backend does not need to bind beyond localhost, and the CORS origin list is never consulted by this path. Binding FastAPI to the network is therefore work the slice does not need, and it puts the API — which has no authentication, by global no-go — directly on the wifi rather than behind the single Vite port.
- evidence:
  - `frontend/src/api/client.ts:32` — `const BASE = "/api/v1"; // proxied to FastAPI :8008 in dev`. Every call in that file is same-origin relative; a grep of `frontend/src/` finds no absolute backend URL, only four error strings mentioning `:8008`.
  - `frontend/vite.config.ts:14-19` — `proxy: { "/api": \`http://localhost:${backendPort}\` }`, with the comment "so the browser stays same-origin".
  - `backend/app/main.py:29` — `allow_origins=["http://localhost:7777"]`, which the browser never exercises when the request is same-origin.
  - `scripts/serve.sh:116,126` — neither `uvicorn` nor `vite` is given a host flag today, so both bind loopback by default.
- proposed change: Reduce P1's "what" to the one change the code needs — pass `--host` to Vite only (`scripts/serve.sh:126`), behind the flag, and leave uvicorn on loopback. Drop the CORS and API-base items, or replace them with the real Vite gotcha: the dev server needs the LAN IP accepted as a host. Keep P1's pass/fail as written; it already proves the right thing, and add a second negative leg — with the flag on, the backend port is still unreachable from the phone.

### 7. P4's hazard is created by P1 but its test is scheduled last, and that test costs nothing today
- id: F7
- severity: should-fix
- claim: P4 is ordered fifth, but P1 is what makes its failure mode reachable. The moment the phone can open the app, the owner has two browsers pointing at one backend, each holding its own session pointer in its own storage. P4's riskiest assumption — "two clients on one session can be serialized by the existing per-request bot resolution without a lock" — becomes live at P1, three slices before it is tested. Its cheapest test needs no phone and no code: two browser tabs on the Mac.
- evidence:
  - `frontend/src/components/SimulateView.tsx:456`, `:533`, `:617` — the session id is written to, removed from, and read back out of `window.localStorage` under `STORAGE_KEY`. P4's problem statement is accurate.
  - `backend/app/services/sim_session.py:968-975` — `submit_decision` loads the session and then `_current_hand(db, session)` with no lock, no row version and no conditional update. `backend/app/db/models.py:79-90` shows `SimHand` carries no version or etag column, so there is nothing for a second writer to collide against.
- proposed change: Move P4's two-tab check out of P4 and into P1's pass/fail as a third leg, run before the flag ships. If it corrupts a hand, P4 moves ahead of S1; if it does not, P4 stays where it is and its assumption-status becomes `tested-holds`.

### 8. The phone lane's measurement slice is deferred behind a full build slice for a weak reason
- id: F8
- severity: should-fix
- claim: The stated order is "LAN first, then 6-max, then the phone prototype (so it shows a 6-seat felt)". P2 is the measurement slice for the roadmap's single largest unknown — whether the felt is usable on a phone at all — and P3 is entirely staked on its verdict. Deferring it behind S1 buys only a nicer prototype. P1 already puts the live 9-seat felt on the phone, so most of P2's signal is available at P1 for free, and a 9-seat pass implies a 6-seat pass because six pods are strictly less crowded than nine.
- evidence: roadmap line 33 (the stated reason) against roadmap lines 46-48 (P1's pass/fail already has the owner dealing and grading a hand on the phone in Chrome); `frontend/src/components/simulate/SimTable.tsx:42` confirms the ring redistributes for any seat count, so the 6-seat felt is not a prerequisite for the readability question.
- proposed change: Add a cheap read to P1's pass/fail — "the owner plays five hands on the 9-seat felt in landscape and records whether pods overlap and whether the page scrolls horizontally" — and state P2's gate conditionally: a clean 9-seat read shortens P2 to the four non-felt screens; a bad one sends the felt lane to problem-framing before S1 spends effort on a 6-seat ring.

### 9. P3 sits in NOW while its own text says it cannot be spec'd
- id: F9
- severity: should-fix
- claim: P3's `assumption-status` reads "depends on P2 — do not spec until P2 reports". The ordering rule in section A says the rest of a lane stays in NEXT until the measurement reports `tested-holds`, and the hand-off contract in section E says a slice whose assumption-status is untested is not handed down for building. P3's note is the right instinct, filed in the wrong column. Leaving it in NOW is how a reader resuming from "the first unchecked slice" walks into it.
- evidence: roadmap lines 88-99; `~/.claude/skills/ai-org/reference/ROADMAP.md:56-62` and `:182`.
- proposed change: Move P3 to NEXT as "phone polish — evidence: P2's per-screen verdict · candidate slices: the approved subset · open questions: which screens the owner approved", and promote it back to NOW when P2 reports.

### 10. Two live documents now describe the same work, and one says "do not build"
- id: F10
- severity: should-fix
- claim: P2 and P3 cover the same ground as an existing draft spec that is still in the tree, still marked DRAFT, and still says its gate was never held. The roadmap cites that spec's measurements without naming it, and answers three of its four open questions, but leaves it standing. Separately, the committed `.claude/CLAUDE.md` still names `bot-realism-flywheel.md` as the governing initiative and the persona-realism lane as PAUSED, while `docs/ai-dlc/profile.md:10` now reads `active: phone-and-6max`.
- evidence:
  - `docs/ai-dlc/specs/draft-mobile-responsive.md:1-3` — "STATUS: DRAFT — Gate-1 interview NOT held. Do not build." Its "Known facts (measured)" section is the source of the roadmap's "overlaps at ≤600px" and masthead claims (roadmap lines 72-73), and its Gate-1 questions 1, 3 and 4 are answered by the roadmap's interview record.
  - `docs/ai-dlc/profile.md:10` versus the committed `.claude/CLAUDE.md` order-of-work banner.
  - The roadmap's own NEXT item flags this correctly for 6-max at line 121 ("does this reopen the paused persona-realism lane ... owner call"), which is the right handling — it is just not applied to the phone lane.
- proposed change: Have P3 retire `docs/ai-dlc/specs/draft-mobile-responsive.md` in the same change that supersedes it, and reconcile the governing-initiative banner in `.claude/CLAUDE.md` with `profile.md` before the roadmap is approved.

### 11. Which five personas sit at a 6-max table is undecided, and it contaminates S1's cheapest test
- id: F11
- severity: should-fix
- claim: S1 says it is "built on today's bots", but today's lineup is exactly eight bots for exactly eight non-hero seats. A 6-max table seats five, so three personas must be dropped. The roadmap does not say which, or whether the drop is fixed or redrawn per session. If it is redrawn, the owner's verdict after one 6-max session — S1's stated cheapest test — depends on which five personas happened to show up.
- evidence: `backend/app/domain/table/play.py:57-61` — `assign_lineup` shuffles `LINEUP` across seats 1..8 and returns `{seat: bots[seat - 1] for seat in range(1, 9)}`; it has no seat-count parameter and would raise or misassign at six seats.
- proposed change: Name the rule in S1's "what" — for example, a fixed five-persona subset for 6-max, chosen once and recorded — and add "a 6-max session seats five distinct personas" to the pass/fail check.

### 12. The 6-max play verdict cannot separate bot behaviour from grader mismatch
- id: F12
- severity: optional
- claim: S1's cheapest test is the owner's feel after one 6-max session, but that session grades his decisions against 9-max ranges by design, and nothing on screen says so. When a hand feels wrong he cannot tell whether the bot was unrealistic or the advice was for a different game. The roadmap defers the labelling question to NEXT (line 121, "is `[UNVERIFIED]` labeling acceptable in the UI meanwhile"), which leaves the only measurement in the 6-max lane confounded.
- evidence: roadmap lines 66-69 (the cheapest test) against lines 58-59 ("persona packs, preflop charts and the grader are untouched") and line 121 (labelling deferred).
- proposed change: Pull the minimum labelling into S1 — one static line on the 6-max felt saying the ranges shown are the 9-max ranges — so the owner's verdict is about the bots.

### 13. The felt's context strip and its geometry tuning are 9-max specific
- id: F13
- severity: optional
- claim: Two small pieces of the felt are hardcoded to nine seats and would be visibly wrong or subtly off in a 6-max session.
- evidence:
  - `frontend/src/components/simulate/SimTable.tsx:147` — the context strip renders the literal `Simulate · 0.5/1 · 9-max · hand ...`.
  - `frontend/src/components/simulate/SimTable.tsx:26-40` — the asymmetric vertical radius (41 above, 38 below) and `FLANK_BIAS_X = 30` were measured against nine pods, per the comment "measured: BTN×SB overlap in a 45-state walk at 1024". Six pods change which slots land at the flanks.
- proposed change: Add the context-strip label to S1's "what". Leave the geometry alone — P2's design review is the right place to find out whether six pods need retuning.

### 14. Two LATER entries are solutions rather than bets, and the baseline has no recorded query
- id: F14
- severity: optional
- claim: Minor template drift. "Bet: an installable app (PWA over HTTPS, or a Capacitor APK)" and "Bet: 6-max as the default table (9-max behind a setting)" lead with the mechanism; the template asks LATER to hold the customer problem. Separately the baseline "~400/week (weeks 36-37 of 2026; 1,051 in week 34)" is not reproducible from the roadmap — no query is recorded, and there is no database in the checkout to re-derive it from.
- evidence: roadmap lines 133-138; roadmap lines 15-17; `~/.claude/skills/ai-org/reference/ROADMAP.md:37-39`.
- proposed change: Restate the two LATER entries problem-first, and paste the one-line SQL that produced the baseline into the north-star block so the same number can be recomputed later.
