# Contract map — phone review depth (post-hand recap, stats and leaks, hand replayer)

Read-only scan by the `contract-mapper` agent (Sonnet), 2026-09-22, against `main` at c0e3269, for the
slice that restyles the three review surfaces for an Android phone (412×915, 393×851, 360×800
portrait; ~915×412 landscape). Persisted verbatim by the Director; adjudication lives in the spec.

## Bottom line

The four contracts most likely to break under a phone restyle:

1. **The "no-baseline" and "graded-only" aggregate rules are computed in JS, not CSS.** A layout
   change cannot touch the math, but hiding a summary line for space (for example dropping the "no
   baseline" count) silently changes what the player is told, since `correctness == null` rows are
   deliberately excluded from every rate (`SimRecap.tsx:59-65`, `SimStreetReport.tsx:14-17`,
   `SimDashboard.tsx:55-56`, `simGrade.ts:74-94`).
2. **No-peek is structural, not visual.** Villain cards are absent from the wire until showdown or
   reveal (`SimShowdown.tsx:9-18`, `HandReplay.tsx:16-18`, `replaySeats.ts:16-18,163-164`). A restyle
   is safe as long as it never introduces a "peek ahead" affordance such as pre-rendering a later
   replay step.
3. **`revealHandEnd` gates when SimRecap and SimShowdown mount at all** (`SimulateView.tsx:1071,1589`).
   Collapsing this section behind an accordion or tab on the phone must not change WHEN it appears
   relative to bot-playback pacing, or the "nothing leads the log" rule (`SimulateView.tsx:1586-1588`)
   breaks.
4. **Two independent breakpoint systems style these surfaces.** A generic `max-width: 640px` /
   `1100px` responsive layer (`app.css:4825`, `3394`, `4008`, `5532`) and the phone gate plus portrait
   block (`app.css:6747`, `7067`). The portrait block (7067–7229) touches NONE of `.sim-recap*`,
   `.sim-showdown*`, `.dash-*`, `.sim-report*`, `.hr-*`, `.hrt-*`. Any phone work on these panels lands
   in the 6747 block or a new one; the portrait block runs after and at equal specificity, so source
   order decides ties (`app.css:7056-7059`).

## Surface 1 — Post-hand review card (SimRecap + SimShowdown)

**Data contracts**
- `SimRecap` reads `GradeView[]` (`types.ts:260-282`); `correctness` and `sizing_correctness` are
  nullable tiers, `reasoning_parts` is optional with a flat `reasoning` fallback.
- Empty state: `recap.length === 0` renders `null` (`SimRecap.tsx:57`).
- Aggregate rule (frozen): summary accuracy % and ≈EV-loss count ONLY `correctness != null` rows; the
  no-baseline count is shown separately (`SimRecap.tsx:15-18,59-65`).
- "Explain this" POSTs a hero-only payload built by explicit field-picking, never a spread of `hand`
  (`SimRecap.tsx:28-30,73-89`). Moving the button must not change what is assembled.
- `SimShowdown` reads `ShowdownSeatView[]` (`types.ts:236-240`) and `SeatView[]`; `showdown.length
  === 0` is the no-showdown path whose copy differs by `heroFolded` (`SimShowdown.tsx:45,66-71`).

**Behavioural contracts a layout change could break**
- Mount gate: both render only when `hand.hand_over && revealHandEnd` (`SimulateView.tsx:1589`);
  `SimRecap` also requires `coachMode` (`SimulateView.tsx:1598`).
- `revealHandEnd = !playing` (`SimulateView.tsx:1071`): the recap and showdown are hidden behind bot
  playback. A phone-only early render (pre-mounting off screen) breaks this.
- Tier survival: `mergedRecap` merges live `last_grade` with persisted rows by `ordinal`
  (`SimulateView.tsx:1055-1064`); after a reload the persisted rows lack tier text and `SimRecap`
  degrades to numbers only (`SimRecap.tsx:20-25`). Any phone-specific variant must replicate this.
- `explains` state resets whenever `recap` identity changes (`SimRecap.tsx:52-55`), driven by the
  prop, not by mount/unmount.
- Reveal buttons (`SimShowdown.tsx:73-85`) call `onReveal` → `getReveal` → `revealedSeats`
  (`SimulateView.tsx:1132-1144`); failures are swallowed. A phone layout must not assume a tap always
  produces visible feedback inside the viewport (buttons under the fixed dock).

**CSS contracts**
- `.sim-recap` and `.sim-showdown` are plain-flow `panel` sections inside `.sim-main`; no fixed or
  sticky positioning.
- `.sim-recap-why` and `.sim-recap-coach` are indented via `margin-left: calc(var(--card-w) * 1.1 +
  var(--space-3))` (`app.css:3791,3803`); the generic 640px rule already zeroes `.sim-recap-coach`'s
  margin (`app.css:4832-4834`) but NOT `.sim-recap-why`, which may still carry the card-width indent
  at all three phone widths.
- `--card-w` is rebound to `--card-w-phone` (40px) only on `.simulate .stage` / `.history-replay
  .stage` (`app.css:6876-6880`), so `.sim-showdown-pos` min-width (`app.css:3342`) and
  `.sim-recap-street` min-width (`app.css:3758`) keep the desktop-derived value on the phone.
- No z-index or fixed position on these two components; they scroll under the fixed dock (z 20).

## Surface 2 — Session stats and leaks (SimDashboard, SimStreetReport)

**Data contracts**
- Both fetch `getStreetReport()` → `StreetReportView` (`types.ts:308-322`); `SimDashboard` also
  fetches `getLeakReport()` → `LeakReportView` (`types.ts:339-342`) independently and best-effort
  (`SimDashboard.tsx:43-49`). A leak-fetch failure leaves `leaks === null`, which renders the "not
  enough decisions" copy (`SimDashboard.tsx:206-210`), distinct from the "no data yet" state that
  gates on `report`/`hasData` (`SimDashboard.tsx:56,91-104`).
- `graded === 0` → `fmtRate` renders "—", never "0%" or NaN (`SimDashboard.tsx:18-19`;
  `simGrade.ts:62-93`, unit-tested in `simGrade.test.ts:20-34,90-104`). A truncation or ellipsis rule
  must not make "—" read as "0%".
- `SimStreetReport` refetches on the parent-owned `refreshKey` (`SimulateView.tsx:1618,1635,1648`);
  the effect is keyed on the prop, not visibility (`SimStreetReport.tsx:23-40`).
- Both fail silently to a muted note (`SimDashboard.tsx:38-42,71-75`; `SimStreetReport.tsx:32-36,42`);
  `SimStreetReport` returns `null` outright on failure with no prior report, so the whole aside slot
  can be empty. A fixed-height card chrome must handle a genuinely empty render.

**CSS contracts**
- `.dash-kpis` collapses to one column at `max-width: 640px` (`app.css:4825-4829`), which fires at all
  three portrait widths underneath the phone gate.
- `.dash-leak` stacks and gets a 44px touch floor at the same 640px rule (`app.css:4837-4849`).
  Nothing in the 6747/7067 blocks touches `.dash-*`; the Dashboard's phone behaviour today is entirely
  the generic 640px rule.
- `.sim-report` lives inside `.sim-side`, which collapses to one column via `.sim-layout` at
  `max-width: 1100px` (`app.css:3394-3396`) and again for the empty shell (`app.css:4008-4010`).

## Surface 3 — Hand replayer (HandReplay, HandReplayTable, replaySeats.ts, revealRequest.ts)

**Data contracts**
- `HandReplayView` / `ReplayStepView` (`types.ts:474-506`): `amount_bb` is a per-action increment,
  not a raise-to total (`replaySeats.ts:10-13`). Any new UI that reads `step.amount_bb` directly
  instead of `replaySeats.ts`'s `actionPhrase` / `raiseTo` renders wrong sizes.
- `revealed_seats` is `[]` on every non-terminal step; only the `is_terminal` step carries data,
  enforced in `deriveSeats` (`replaySeats.ts:162-164`).
- `is_terminal` means "the showdown step", not "hand complete": an uncontested fold-out has no
  terminal step (`replaySeats.ts:14-16`); `isComplete` is the separate `cursor === steps.length - 1`.

**Behavioural contracts**
- Step cursor: `HandReplay` uses the raw step index (`HandReplay.tsx:63`); `HandReplayTable` uses a
  visible-step-only index (`HandReplayTable.tsx:88-104`) so navigation never lands on a blind post.
  Two cursor models for one view type; a shared phone stepper must not swap one for the other.
- Keyboard: both bind `ArrowLeft` / `ArrowRight` on `window`, guarded against modifiers and editable
  targets (`HandReplay.tsx:114-132`, `HandReplayTable.tsx:119-141`). No swipe gesture exists; adding
  one is new behaviour and must not remove the keyboard path.
- `HandReplayTable`'s reveal props are all optional with defaults so its minimum signature
  (`{replay, onClose}`) equals `HandReplay`'s and the two stay swappable at the host
  (`HandReplayTable.tsx:65-72`).
- `revealRequest.ts` guards every response with `{handId, scope, gen}` identity
  (`revealRequest.ts:33-55,85-134`) because `HistoryView` stays mounted across hand changes.
- **No focus management on open or close** for any of the three surfaces or either replayer (contrast
  `errorPanelRef` / `scoreCardRef`, `SimulateView.tsx:1344,1371`). Pre-existing gap, not a contract.
- No `<dialog>` element in any of these surfaces; all are plain `<section>` / `<main>` in flow.

**CSS contracts**
- `.app:has(.simulate), .app:has(.history-replay)` opt into the wide shell (`app.css:3410-3413`) so
  the History replayer's felt is pixel-identical to the live table (`app.css:3407-3409`; reiterated at
  `app.css:7187-7189`). The phone gate rebinds `--card-w` / `--card-h` identically for `.simulate
  .stage` and `.history-replay .stage` (`app.css:6876-6880`); keep both selectors together.
- `.hrt-body` (two-pane History replayer) collapses to one column at `max-width: 1100px`
  (`app.css:5532-5536`).
- The nine-seat opt-out `.tablering:not(:has(> .tseat:nth-child(11)))` (`app.css:6919-6922`) relies on
  `SimTable` and `HandReplayTable` sharing the same DOM order (`app.css:6916-6918`); inserting a
  wrapper in either breaks the selector for both.
- z-index layers in use: dock 20 (`app.css:6947`), stale-tab notice 21 (`6974`), armed-shove warning
  22 (`6994`), section-rail sheet 30 (`6800`), its opener 40 (`6833`); `.hrt-street-head` is sticky
  with local `z-index: 1` (`5656-5659`). None of the review panels claim a z-index today.

## Tests that pin behaviour (and what they do not cover)

- `simGrade.test.ts` — null-on-zero-graded rate math (lines 20–104). Not rendering.
- `replaySeats.test.ts` — `deriveSeats` / `buildReplayModel` (raise-to reconstruction, fold tracking,
  terminal reveal placement). Not markup.
- `revealRequest.test.ts` — three race conditions in the reveal state machine.
- `rotateHint.test.ts` — the four-flag predicate only.
- **No test exercises `SimRecap`, `SimShowdown`, `SimDashboard`, `SimStreetReport`, `HandReplay` or
  `HandReplayTable` directly.** The repo has vitest but no React Testing Library or jsdom
  (`revealRequest.ts:29-31`), so component markup for all three surfaces is unverified by any
  automated test. The browser reviewer is the only regression net for JSX changes here.
