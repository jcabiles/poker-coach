# Phone access + 6-max Roadmap — updated 2026-09-18
status: draft

## Bottom line
- Make the trainer playable from a phone on the home wifi, and add a 6-max table option, so
  the owner plays more hands per week. The Mac stays the server; the phone is a screen.
- We are betting that the existing poker table works on a phone turned sideways without a
  redesign, and that today's bots (built for 9-seat tables) are acceptable at 6 seats until a
  research pass tunes them.
- Next: build the smallest thing that puts the app on the phone (slice P1), then the 6-max
  option (slice S1), then a throwaway five-screen phone prototype the owner plays 20 hands on.
  The prototype's verdict decides whether phone polish goes ahead or the felt gets redesigned.

## North-star outcome
- Outcome: Simulate hands played per week (count of `sim_hand` rows by `created_at` week)
  | Baseline: ~400/week (weeks 36–37 of 2026; 1,051 in week 34) → Target: owner sets after
  the first phone week; the honest expectation is "a convenience, not a fix", so a flat number
  is a real finding, not a failure.
- Why hands, not sessions: a Simulate session row is long-lived (one per week in the data), so
  it does not count playing occasions. Hands do.

## Interview record (2026-09-18, owner)
- Appetite: small per slice. No mobile-first redesign. Landscape felt, portrait everything else.
- Delivery: LAN browser + home-screen shortcut. No install, no HTTPS, no Android toolchain.
- Phone scope v1: Simulate table, post-hand review + ledger, session stats and leaks.
- Navigation: bottom tab bar, hidden by default, one button shows it.
- Sharing: one live session, resumable from either device (pointer moves to the server).
- Security: home wifi is trusted; bind to the network behind an explicit flag, off by default.
- Phone-only addition: bigger action buttons with a confirm step on all-in. Nothing else.
- 6-max: a per-session option next to 9-max, built on today's bots. Seats map to the six
  latest 9-max positions (LJ, HJ, CO, BTN, SB, BB), so ranges and grader tables change
  nothing now. Realism research for 6-max follows after the owner has played it.
- Order: LAN first, then 6-max, then the phone prototype (so it shows a 6-seat felt).
- Always-on: owner starts the stack by hand before playing (v1).
- Others: a README LAN setup anyone can repeat. APK packaging is a Later bet.
- Prototype screens (5): landscape felt mid-hand, portrait home/resume, session ledger,
  settings, showdown/hand-over.

## NOW  (ordered; ICE = impact·confidence·ease out of 10)

- [ ] **P1 — LAN walking skeleton.** problem: the app exists only on the Mac ·
      outcome-link: hands/week · ICE 8·9·9
      what: `serve.sh start --lan` binds backend and Vite to the network; CORS origins and the
      API base come from config, not literals; README "Play from your phone" section (flag,
      finding the Mac's IP, Chrome "Add to Home screen"); the felt renders at 9 seats untouched.
      pass/fail: on the owner's Android phone, Chrome opens `http://<mac-ip>:7777`, a Simulate
      hand deals and grades, and `make check` is green; with the flag off, nothing binds beyond
      localhost (curl from the phone fails).
      appetite: 1 slice · no-gos: no auth, no HTTPS, no layout work, no PWA manifest.
      riskiest-assumption: the phone can reach and drive the app over the LAN with no change to
      the game code · cheapest-test: this slice is the test · assumption-status: untested
      (low risk: it is a bind address and two config values).

- [ ] **S1 — 6-max table option.** problem: 9 seats is the wrong shape for the owner's game and
      for a phone screen · outcome-link: hands/week · ICE 8·7·6
      what: table size (6 or 9) chosen when a Simulate session starts and stored on the session
      (migration); engine/deck take the seat count from the session instead of the `_SEATS = 9`
      constants; 6-max seats carry the positions LJ, HJ, CO, BTN, SB, BB so persona packs,
      preflop charts and the grader are untouched; the felt renders a 6-seat ring; 9-max
      byte-identical (existing fixtures and bands unchanged).
      pass/fail: a 6-max session deals 6 hands, rotates the button through 6 seats, posts blinds
      correctly, grades hero decisions at every 6-max position, and survives restore mid-hand;
      the full 9-max suite passes unchanged; `make check` green.
      appetite: 1 slice · no-gos: no new ranges, bands, or pack values; no 6-max-specific bot
      behavior; no change to `spot_signature()`.
      riskiest-assumption: bots playing their 9-max charts from the six latest positions feel
      acceptable at a 6-seat table for now · cheapest-test: the owner's verdict after one 6-max
      session (see NEXT: 6-max realism research) · assumption-status: untested — and it does
      not block this slice, because the slice is also the cheapest test.

- [ ] **P2 — Phone prototype (throwaway branch, 5 screens).** problem: nobody has seen the app
      on a phone; the July review found the felt overlaps at ≤600px and the masthead forces
      horizontal scroll · outcome-link: hands/week · ICE 9·6·7
      what: on a `proto/` branch, never merged: (1) landscape felt mid-hand with the hidden
      bottom tab bar and its show button, bigger action buttons with confirm on all-in;
      (2) portrait home/resume; (3) session ledger; (4) settings (speed, theme, mode);
      (5) showdown/hand-over. Reuses real tokens and components; no tests required; a design
      review (browser eyes) records measurements at the owner's phone size.
      pass/fail: the owner plays 20 hands on the phone in landscape with no mis-tap, no
      horizontal scroll, and cards/stacks readable at arm's length; the owner writes a verdict
      per screen in the ledger. Fail on any of the three → the felt lane goes back to
      problem-framing (portrait/compact felt) instead of polish.
      appetite: 1 slice · no-gos: no merge of prototype code; no Practice/Quiz screens; no
      portrait felt.
      riskiest-assumption: the existing 6-seat felt is playable on a phone in landscape without
      a redesign · cheapest-test: this slice · assumption-status: untested.

- [ ] **P3 — Phone polish (from the prototype verdict).** problem: same as P2 ·
      outcome-link: hands/week · ICE 7·5·6
      what: the subset of the five screens the owner approved, built for real on `main`:
      mobile breakpoint for the app shell (masthead wrap, stats strip reflow — app-wide, so
      Practice/Quiz get a design-review pass too), hidden tab bar, action-button sizing and
      all-in confirm, landscape hint on the felt route.
      pass/fail: the P2 20-hand check repeats on `main` and passes; desktop screenshots at
      1280px are pixel-identical for the felt; AA contrast and focus in both themes; `make
      check` green.
      appetite: 1–2 slices · no-gos: no portrait felt; no iOS testing.
      riskiest-assumption: P2's assumption, now `tested-holds` · assumption-status: depends on
      P2 — do not spec until P2 reports.

- [ ] **P4 — One live session across devices.** problem: the resume pointer lives in each
      browser's storage, so the Mac and the phone cannot see the same table ·
      outcome-link: hands/week (pick up where you left off) · ICE 6·8·7
      what: the server keeps the current session id; the client asks the server on load instead
      of localStorage; localStorage stays as a fallback only for the 404 recovery path.
      pass/fail: start on the Mac, act on the phone, act again on the Mac, and the hand state is
      one continuous line in `sim_hand`; two tabs acting at once get a clear "acted elsewhere"
      message rather than a corrupt hand; `make check` green.
      appetite: 1 slice · no-gos: no accounts, no multi-user, no websockets.
      riskiest-assumption: two clients on one session can be serialized by the existing
      per-request bot resolution without a lock · cheapest-test: the two-tab check above ·
      assumption-status: untested.

## NEXT (validated problems, not yet spec'd)
- **6-max realism research.** evidence: every persona band and range was recalibrated to 9-max
  in July (persona-realism roadmap, ledger #14 and waves W5); at 6 seats the bots will be tight
  by construction · candidate slices: owner play notes from S1 → a research pass on 6-max
  population stats (VPIP/PFR/RFI by seat, c-bet, WTSD) → per-format pack values with the
  existing `(format, pool, source)` provenance rule → gates that keep 9-max byte-identical ·
  open questions: does this reopen the paused persona-realism lane or run as its own slice
  under this roadmap (owner call); is `[UNVERIFIED]` labeling acceptable in the UI meanwhile.
- **Always-on stack.** evidence: the phone only works while the Mac runs the stack; the owner
  chose "start by hand" for v1 · candidate slices: a launchd job with sleep/wake handling ·
  open questions: does forgetting to start it actually cost sessions (measure after P1).
- **Phone review depth.** evidence: v1 phone scope includes review, ledger, stats but the
  prototype covers ledger only · candidate slices: post-hand review card, stats and leaks, hand
  replayer at phone size · open questions: which the owner uses on the phone at all.

## LATER (bets, no dates)
- Bet: a portrait, compact felt makes one-handed play natural · segment: owner on the couch ·
  confidence: low · assumptions to test: P2 fails on landscape, or the owner finds rotating the
  phone a real friction · review-by: after P3.
- Bet: 6-max as the default table (9-max behind a setting) · segment: owner · confidence: med ·
  assumptions to test: the 6-max research lands and the owner stops starting 9-max sessions ·
  review-by: after the 6-max research slice.
- Bet: an installable app (PWA over HTTPS, or a Capacitor APK) lets other people run this ·
  segment: friends/portfolio · confidence: low · assumptions to test: anyone besides the owner
  wants it; the Android toolchain fits the sandbox · review-by: when a second user exists.
- Bet: Practice/Quiz/SRS drills on the phone raise drill volume · segment: owner ·
  confidence: med · assumptions to test: the owner opens them on the phone at all after P3 ·
  review-by: two weeks after P3.

## Out of scope / no-gos (global)
- Offline play or service-worker caching; the phone never works without the Mac.
- Push notifications, reminders, streaks, or any engagement mechanic.
- iOS or any device other than the owner's Android in Chrome (others may work, untested).
- Auth, PIN, accounts, hosting, billing (global no-go; home wifi is trusted).
- A mobile-first redesign of the desktop app.
- 6-max-specific range, band, or pack values inside the NOW lane; that is the NEXT research.
- The existing global no-gos: no solver tables, no hand-history import, no live-session logger,
  no browsable lessons library.
