# Phone access + 6-max Roadmap — updated 2026-09-22 (rev 5: P1, S1 ticked; P2 replaced by the P3a fix; P4 carries the probe verdict; P3b promoted to NOW)
status: approved — owner, 2026-09-18 (rev 4). D1–D4 decided. Rev 4 corrects P1's security claim
and its measurement (c) after a blind dual review of the P1 spec returned FAIL on both; owner ruled
2026-09-18 to accept the exposure and correct the text. Evidence: `../ledger/phone-and-6max.md`
round 2.

## Bottom line
- Make the trainer playable from a phone on the home wifi, and add a 6-max table option, so
  the owner plays more Simulate sessions per week. The Mac stays the server; the phone is a screen.
- We are betting on four things: the existing table works on a phone turned sideways without
  a redesign; six seats can borrow the six latest 9-max positions so bots and grader need no
  new charts; today's bots feel acceptable at six seats until a research pass tunes them; and
  two devices on one session do not corrupt a hand.
- Where we are (2026-09-22): the app is on the phone (P1), 6-max exists (S1), and the felt page
  is playable in landscape (P3a, which replaced the prototype). Next: one live session across
  devices (P4, in build), then portrait polish for the other pages (P3b), then an always-on
  stack. Still owed by the owner: one phone hand, the 20-hand landscape verdict, and the first
  6-max session that unlocks the realism research.

## North-star outcome
- Outcome: **Simulate sessions per week** (owner's choice) = `sim_session` rows by the week
  they were created. Secondary, for context only: hands per week, reported separately for
  9-max and 6-max once S1 lands (a 6-max hand is shorter, so hands rise on their own).
- Caveat the owner accepted: a session row is long-lived (the data shows one per week), so
  this counts sessions started, not days played. If that proves too coarse, the owner may
  switch the metric later; nothing in the NOW lane depends on it.
- Baseline (2026-09-18, `backend/data/poker_coach.db`, `%W` week number, Monday-based):
  sessions 1/week in weeks 34, 36, 37; hands 1,051 / 388 / 427 in those weeks.
  ```sql
  select strftime('%Y-%W', created_at) w, count(*) from sim_session group by w order by w desc;
  select strftime('%Y-%W', created_at) w, count(*) from sim_hand group by w order by w desc;
  ```
- Target: the owner sets it after the first week with the phone live. The owner said the
  phone is "a convenience, not a fix", so a flat number is an accepted outcome; there is no
  automatic scope rule tied to it (the owner dropped one on 2026-09-18).

## Interview record (2026-09-18, owner)
- Appetite: small per slice. No mobile-first redesign. Landscape felt, portrait everything else.
- Delivery: LAN browser + home-screen shortcut. No install, no HTTPS, no Android toolchain.
- Phone scope v1: Simulate table, post-hand review + ledger, session stats and leaks.
- Navigation: bottom tab bar, hidden by default, one button shows it.
- Sharing: one live session, resumable from either device (pointer moves to the server).
- Security: home wifi is trusted; bind to the network behind an explicit flag, off by default.
- Phone-only addition: bigger action buttons with a confirm step on all-in. Nothing else.
- 6-max: wanted because it fits a phone screen better and is the format the owner sees offered;
  a per-session option next to 9-max, built on today's bots. Seats map to the six
  latest 9-max positions (LJ, HJ, CO, BTN, SB, BB). Realism research for 6-max follows after
  the owner has played it; the owner expects tweaks, not a rebuild.
- Order: LAN first, then 6-max, then the phone prototype (so it shows a 6-seat felt).
- Always-on: owner starts the stack by hand before playing (v1).
- Others: a README LAN setup anyone can repeat. APK packaging is a Later bet.
- Prototype screens (5): landscape felt mid-hand, portrait home/resume, session ledger,
  settings, showdown/hand-over.

## Owner decisions (surfaced by review R1; all DECIDED 2026-09-18 — do not re-ask)
- **D1 — How 6-max hands are keyed in grading history.** `spot_signature()` already hashes
  `table_size`, and every Simulate spot hardcodes `table_size=9`. DECIDED: key 6-max spots as
  `table_size=6`, so 6-max starts its own spaced-repetition history and the later research
  can tell the formats apart. The alternative (leave 9) merges them permanently. No change to
  `spot_signature()` itself either way.
- **D2 — Which five of the eight personas sit at a 6-max table.** DECIDED: a fixed subset
  chosen in the S1 spec and recorded there, so the owner's first-session verdict is not a
  draw. Alternative: redraw per session.
- **D3 — The committed `.claude/CLAUDE.md` still names the flywheel as the governing
  initiative.** DECIDED: the P1 spec updates that banner in the same change (it is outside the
  roadmap's write authority).
- **D4 — Delete `docs/ai-dlc/specs/draft-mobile-responsive.md` in P1.** APPROVED by the owner
  2026-09-18 (per-file deletion approval, as the cleanup ruling requires).
- Resolved 2026-09-18 by the owner, recorded so they are not re-asked: the metric stays
  sessions per week (not occasions); no four-week scope rule; no Later bet on phone drills.

## NOW  (ordered; ICE = impact·confidence·ease out of 10)

- [x] **P1 — LAN walking skeleton + two cheap tests.** problem: the app exists only on the Mac ·
      outcome-link: sessions/week · ICE 8·9·9
      what: `serve.sh start --lan` passes `--host` to Vite only; the backend port stays on
      loopback because the frontend calls a relative `/api/v1` that Vite proxies server-side, so
      no CORS or API-base change is needed. **Corrected 2026-09-18 (owner ruling, after both blind
      reviewers proved the original claim false): the API IS reachable over the wifi through the
      Vite port while the flag is on** — Vite forwards every `/api` request it receives, whatever
      interface it arrived on, and a reviewer read live database rows that way. This is
      unavoidable (the phone cannot play without the API) and accepted (the home wifi is trusted,
      and auth is a global no-go). Port 8008 itself is never reachable, and P1 now binds it with an
      explicit `--host 127.0.0.1` so a stray `UVICORN_HOST` cannot change that. README
      "Play from your phone" section (flag, finding the Mac's IP, Chrome "Add to Home screen").
      Deletes `docs/ai-dlc/specs/draft-mobile-responsive.md` (superseded; D4 approved) and
      reconciles the `.claude/CLAUDE.md` initiative banner (D3). Game code untouched.
      pass/fail: (a) on the owner's Android phone, Chrome opens `http://<mac-ip>:7777`, a
      Simulate hand deals and grades; (b) with the flag off nothing binds beyond localhost, and
      with it on the backend port 8008 is still not independently reachable (this is evidence
      about that port, NOT about the API, which the Vite port proxies by design); (c) two-client
      test on the Mac: act on one session from two tabs in turn by hand, then fire two decision
      submits concurrently from a small script against the same session. **Revised 2026-09-18:
      record each client's observed decision point, its HTTP result and the resulting state — not
      just whether decision positions collide.** A stale tab's action is applied legally to
      whatever state is current, so a hand can be corrupted with no collision; and the simultaneous
      leg cannot race at all today (one worker, no suspension point in the async path), so its
      clean result is scoped to "today's deployment serializes", never "no race exists". Note
      `sim_hand` holds one current `state_json`, not a continuous event line (feeds P4's
      assumption); (d) five landscape hands
      on the 9-seat felt, recording pod overlap and horizontal scroll (feeds P2's gate);
      `make check` green.
      appetite: 1 slice · no-gos: no auth, no HTTPS, no layout work, no PWA manifest, no
      backend bind.
      riskiest-assumption: the phone can reach and drive the app through the Vite port alone ·
      cheapest-test: this slice · assumption-status: untested (low risk).
      **Build status 2026-09-18: code shipped, box deliberately left unticked.** Every
      machine-checkable leg of (b) passed on isolated ports — backend loopback-only even with
      `UVICORN_HOST=0.0.0.0` exported, frontend on all interfaces only under `--lan`, `status`
      reporting the real binding, and `start --lan` refusing a running loopback stack with exit 1.
      Evidence: `../ledger/phone-and-6max.md`, "P1 measurement (b)". **Still owed by the owner:**
      leg (a), one Simulate hand dealt and graded on the Android phone, and leg (d), five landscape
      hands recording pod overlap and horizontal scroll — which is P2's gate. Leg (c), the
      two-client concurrency probe, is not yet run. The wifi-address banner has only ever taken its
      fallback path, because `ipconfig` is blocked in the build sandbox; the owner's first
      `start --lan` confirms it.
      **Ticked 2026-09-22 on the owner's instruction, with one leg still open.** Merged as #229.
      Leg (c) ran 2026-09-22 and found silent corruption in both legs (ledger, "P1 measurement (c)");
      P4 carries the fix. Leg (d) was answered by the browser measurement that replaced P2: zero
      pod overlap and zero sideways scroll at six seats in landscape (`../specs/phone-chrome-p3a.md`).
      Leg (a), one hand dealt and graded on the owner's phone, is still owed by the owner.

- [x] **S1 — 6-max table option.** problem: 9 seats crowd a phone screen, and 6-max is the format
      the owner sees offered · outcome-link: sessions/week · ICE 8·6·4
      what: table size (6 or 9) chosen when a Simulate session starts and stored on the session
      (migration). Every hardcoded 9 takes the seat count from the session:
      `backend/app/domain/table/{engine,deck,range_estimate}.py`,
      `backend/app/services/sim_session.py` (button seeding and rotation, `SimSeat` row
      creation, the Challenge-mode blind-check seat pool), `play.py::assign_lineup` (five
      personas per D2), the felt's context strip and ring in `SimTable.tsx`. 6-max seats carry
      LJ, HJ, CO, BTN, SB, BB. Spots are keyed per D1. One static line on the 6-max felt says
      the ranges shown are 9-max ranges. 9-max byte-identical.
      pass/fail: a 6-max session deals 6 hands, seeds and rotates the button through 6 seats
      only, posts blinds correctly, seats five personas from a fixed roster, grades hero decisions at every
      6-max position, survives restore mid-hand, and a Challenge blind check names only seats
      that exist; the villain-range panel counts live opponents from 6 seats; a signature
      assertion proves D1 (same hero hand at 6 and 9 seats produces different signatures if
      D1 = 6); the full 9-max suite passes unchanged; `make check` green.
      appetite: 1 slice, the largest in this lane · no-gos: no new ranges, bands, or pack
      values; no 6-max-specific bot behavior; no change to `spot_signature()`; no felt
      geometry retuning (that is P2's design review).
      riskiest-assumption: taking the six latest 9-max positions leaves hero grading verdicts
      unchanged — known soft spots are the villain-range opponent count (fixed in "what") and
      limped pots canonicalised onto a UTG limper who has no seat · cheapest-test: a headless
      run asserting a set of 6-max hands grade identically to the equivalent 9-max hands ·
      assumption-status: untested; the test runs inside this slice, before the felt work, because
      it needs the 6-seat engine to exist — a separate measurement slice would have to build
      the same engine first.
      **Built and merged as #230 (2026-09-18); ticked 2026-09-22 on the owner's instruction.** The
      spec's blind review moved D1 to where Simulate's key actually lives (`_sim_signature`, now
      `sim:6:…` / `sim:9:…`; `spot_signature()` untouched), D2 kept the nit/TAG/TAG/LAG/station
      roster, and the table size is chosen on the sit-down screen. The owner has not yet played a
      6-max session, so the 6-max realism research in NEXT still waits on play notes.

- [x] **P2 — REPLACED 2026-09-19 by a real fix (P3a, merged as #231).** A browser measurement at
      three Android landscape sizes answered the prototype's question without building it: the felt
      is fine (zero pod overlap, zero sideways scroll at six seats); the page chrome was the problem
      (the table and the action buttons could not be seen at once). The owner ruled to spend the
      effort on the fix: pinned action dock, nav as a hidden bottom sheet, all-in confirm. Spec:
      `../specs/phone-chrome-p3a.md`. The owner's 20-hand play verdict is still owed. The original
      entry stays below for the record.
      ~~P2 — Phone prototype (throwaway branch, 5 screens).~~ problem: nobody has seen the app
      on a phone; the July review found the felt overlaps at ≤600px and the masthead forces
      horizontal scroll · outcome-link: sessions/week · ICE 9·6·7
      what: on a `proto/` branch, never merged: (1) landscape 6-seat felt mid-hand with the
      hidden bottom tab bar and its show button, bigger action buttons with confirm on all-in;
      (2) portrait home/resume; (3) session ledger; (4) settings (speed, theme, mode);
      (5) showdown/hand-over. Real tokens and components; no tests required; a design review
      (browser eyes) records measurements at the owner's phone size, including whether six
      pods need the ring geometry retuned.
      gate: if P1(d) found the 9-seat felt clean in landscape, the felt screen is confirmation
      only and the slice is mostly the four other screens; if P1(d) found overlap or scroll,
      the felt lane goes to problem-framing (portrait or compact felt) before this slice runs.
      pass/fail: the owner plays 20 hands on the phone in landscape with no mis-tap, no
      horizontal scroll, and cards/stacks readable at arm's length, and writes a verdict per
      screen in the ledger.
      appetite: 1 slice · no-gos: no merge of prototype code; no Practice/Quiz screens; no
      portrait felt.
      riskiest-assumption: the existing felt is playable on a phone in landscape without a
      redesign · cheapest-test: P1(d) first, then this slice · assumption-status: untested.

- [ ] **P4 — One live session across devices.** problem: the resume pointer lives in each
      browser's storage, so the Mac and the phone cannot see the same table ·
      outcome-link: sessions/week (pick up where you left off) · ICE 6·8·7
      what: the server keeps the current session id; the client asks the server on load instead
      of localStorage; localStorage stays as a fallback only for the 404 recovery path. If
      P1(c) corrupted a hand, this slice also adds a per-hand version check on
      `submit_decision` and moves ahead of S1.
      **P1(c) DID corrupt a hand (2026-09-22, ledger "P1 measurement (c)"), so the version check is
      in.** Owner rulings 2026-09-22: "current" = the newest session that has not ended (no stored
      pointer, no migration); a stale tab's action is refused, the client refetches and shows one
      line ("Acted elsewhere — table refreshed."), never a modal; the token is derived from the hand
      number and the hand's action count, so no schema change. Spec: `../specs/phone-p4-live-session.md`.
      pass/fail: start on the Mac, act on the phone, act again on the Mac, and the hand state is
      one continuous line in `sim_hand`; two tabs acting at once get a clear "acted elsewhere"
      message rather than a corrupt hand; `make check` green.
      appetite: 1 slice · no-gos: no accounts, no multi-user, no websockets.
      riskiest-assumption: two clients on one session can be serialized by the existing
      per-request bot resolution without a lock · cheapest-test: P1(c) ·
      assumption-status: untested until P1 reports.

## NEXT (validated problems, not yet spec'd)
- **P3 — Phone polish.** evidence: P2's per-screen verdict (not yet held) · candidate slices:
  the approved subset built for real on `main`: app-shell mobile breakpoint (masthead wrap,
  stats strip reflow — app-wide, so Practice/Quiz get a design-review pass), hidden tab bar,
  action-button sizing and all-in confirm, landscape hint on the felt route; desktop felt
  pixel-identical at 1280px; AA and focus in both themes · open questions: which screens the
  owner approved; whether six pods need geometry retuning. Promote to NOW when P2 reports.
  **Status 2026-09-22:** the felt-page half (P3a) shipped as #231; six pods need no retuning. The
  owner promoted the rest (P3b: portrait home/resume, ledger, settings, stats; the app-shell
  breakpoint that removes the 713px minimum width; a passive rotate hint; Practice/Quiz "do not
  break" only) to NOW on 2026-09-22 without waiting for the 20-hand verdict. It runs after P4.
  **P3b measured and built 2026-09-22** (spec `../specs/phone-p3b-portrait.md`, stacked on P4):
  portrait is NOT broken by width — five of seven screens have zero sideways overflow at 412, 393
  and 360 wide, so the 713px minimum is gone — but by stacking order: the landscape fix put the
  masthead 585–879px below the fold with tab order contradicting visual order. P3b returns the app
  chrome to the top in portrait only, keeps the session controls below the felt (they would push
  the table under the dock at 360×800), puts the nav tabs back in flow, wraps the stats strip,
  fixes History's 12px overflow, raises the in-session controls to 44px, and adds the rotate hint.
  Director decisions inside the rulings: "settings" is a portrait pass over the existing controls
  (no settings screen exists; building one is a later slice if wanted); the felt in portrait is
  recorded, not fixed (8–11 overlapping pod pairs; the hint is the answer). Still owed by the
  owner: the 20-hand landscape verdict.
- **6-max realism research.** evidence: every persona band and range was recalibrated to 9-max
  in July (persona-realism roadmap, ledger #14 and waves W5); at 6 seats the bots will be tight
  by construction · candidate slices: owner play notes from S1 → a research pass on 6-max
  population stats (VPIP/PFR/RFI by seat, c-bet, WTSD) → per-format pack values with the
  existing `(format, pool, source)` provenance rule → gates that keep 9-max byte-identical ·
  open questions: does this reopen the paused persona-realism lane or run as its own slice
  under this roadmap (owner call).
- **Always-on stack — BUILT 2026-09-22** (spec `../specs/always-on-stack.md`, stacked on P3b).
  evidence: the phone only works while the Mac runs the stack; the owner chose "start by hand" for
  v1, then on 2026-09-22 ruled for a launchd user agent that starts the stack with `--lan` at
  login and re-runs the launcher every five minutes (a no-op while the stack is up, which is what
  brings it back after sleep or a crash). Shipped as a plist template plus owner-run
  `scripts/always_on_install.sh` / `always_on_uninstall.sh`, because the sandbox cannot write to
  LaunchAgents. Accepted cost, recorded in the README: with it installed the unauthenticated API
  is on the home wifi whenever the Mac is awake. **Owed by the owner:** run the install once in a
  plain terminal and confirm the stack returns within five minutes after a sleep or a `stop`. The
  original open question (does forgetting to start it cost sessions) is moot once installed.
- **Phone review depth.** evidence: v1 phone scope includes review, ledger, stats but the
  prototype covers ledger only · candidate slices: post-hand review card, stats and leaks, hand
  replayer at phone size · open questions: which the owner uses on the phone at all.

## LATER (bets, no dates)
- Bet: one-handed play on the couch needs a portrait, compact felt · segment: owner ·
  confidence: low · assumptions to test: P2 fails on landscape, or rotating the phone proves a
  real friction · review-by: after P3.
- Bet: once 6-max is tuned, 9-max should stop being the default · segment: owner ·
  confidence: med · assumptions to test: the 6-max research lands and the owner stops starting
  9-max sessions · review-by: after the 6-max research slice.
- Bet: other people want to run this on their own phone · segment: friends/portfolio ·
  confidence: low · assumptions to test: a second user exists; an installable path (PWA over
  HTTPS or an APK) fits the sandbox and toolchain · review-by: when a second user exists.

## Out of scope / no-gos (global)
- Offline play or service-worker caching; the phone never works without the Mac.
- Push notifications, reminders, streaks, or any engagement mechanic.
- iOS or any device other than the owner's Android in Chrome (others may work, untested).
- Auth, PIN, accounts, hosting, billing (global no-go; home wifi is trusted). The backend
  port never binds beyond localhost. **This bounds the port, not the API:** while `--lan` is on,
  the Vite port proxies the whole unauthenticated API to anything on the home network. Corrected
  2026-09-18 by owner ruling; the earlier wording implied an access boundary that does not exist.
- A mobile-first redesign of the desktop app.
- 6-max-specific range, band, or pack values inside the NOW lane; that is the NEXT research.
- The existing global no-gos: no solver tables, no hand-history import, no live-session logger,
  no browsable lessons library.
