# Contract map — phone table fit (landscape felt on a real phone browser)

Read-only scan by the `contract-mapper` agent (Sonnet), 2026-09-22, against `main` at f5d95e3. The
Director persisted the summary and the load-bearing contracts. The full transcript is not kept.

## Bottom line

The landscape redesign can break five things. None of them has an automated test, so each needs a
named check in the spec.

1. **Seat geometry is copied, not shared.** `slotStyle()` exists in `SimTable.tsx:42-49` and, as a
   commented copy, in `HandReplayTable.tsx:24-36`. `PokerTable.tsx:44-52` keeps a third, simpler
   copy for Practice and Quiz. A geometry change edits the first two together or not at all.
2. **The ring's shape contradicts itself on a phone.** Base `.tablering` declares
   `aspect-ratio: 2.1/1` with `width: 100%` (`app.css:275-280`). The phone gate caps only
   `max-height` (`app.css:6930-6933`), so the browser keeps the width and drops the ratio. On the
   owner's phone that gives an 840×154 ring (5.5:1).
3. **The nine-seat opt-out counts DOM children.**
   `.tablering:not(:has(> .tseat:nth-child(11)))` (`app.css:6930-6931`) assumes `.rail` and
   `.table-center` are always the ring's first two children, in both tables. Any wrapper inserted
   before the seats silently breaks it.
4. **Pod content is timed by the lockstep gate.** `isRevealed` (`SimTable.tsx:128-133`) gates the
   fold dim, the all-in flag, the chips puck and the last-action verb. The rule is that the felt
   never shows a result before the event log narrates it (`SimTable.tsx:78-94`). A slimmer pod
   must read the same `revealed` value.
5. **The fixed dock has satellites.** One rule positions both `.decisionbar.sim-actionbar` and
   `.decisionbar.sim-nextdock` (`app.css:6954-6972`). Three other things are tied to its height
   only by a shared constant, `calc(var(--space-8) * 4)`:
   - the stale-tab notice (z 21, `app.css:6981-6988`);
   - the armed-shove warning (z 22, `bottom: 100%` of the dock, `app.css:6999-7017`);
   - the `.app` bottom padding and `html { scroll-padding-bottom }` (`app.css:6766,6780`).

## Seat pods

- **Villain pod rows**, all inside `.tseat.sim-seat` (`SimTable.tsx:263-360`):
  - `.sim-actrow`: the last-action verb and the chips puck, both lockstep-gated.
  - Cards: face-down backs, or face-up `.sim-reveal` cards at a showdown or R1 reveal (showing a
    folded villain's cards after the hero folds).
  - `.sim-persona-plate`: shown only when `labelsVisible`. T7 (the Challenge-mode rule that hides
    bot archetypes) turns it off.
  - `.sim-meta`: position, the dealer disc, and the RANGE button.
  - `.sim-stack-row`: the stack figure.
- **The RANGE button is the only interactive control on a villain pod today** (`SimTable.tsx:332-347`).
  - It renders only when `labelsVisible && persona_type && !folded && !hand_over`. Here `folded` is
    the staged value, not the raw server status.
  - It sets `aria-pressed` and a "Show/Hide estimated range for <pos>" label.
  - It opens `SimVillainRange`, which mounts in document flow **below the felt**
    (`SimulateView.tsx:1529-1547`). It is not a popover.
  - A tappable pod adds a second target on the same pod, so which of the two handles a tap must be
    stated.
- **The hero pod** (`SimTable.tsx:237-260`) shows, top to bottom:
  - the verb and chips;
  - the hero's cards inside `.hero-ring`;
  - `.herometa` (position · stack · "your turn");
  - `SimVerdictBadge`.
  It is never gated.
- **The History replayer** (`HandReplayTable.tsx`) renders the same class family from `deriveSeats()`
  (`replaySeats.ts`), which reveals by step, not by the lockstep. It has no dock of its own; it uses
  `.hrt-controls` and its own ←/→/Esc keys.

## The dock

- **`SimActionBar.tsx` is a roving-tabindex toolbar.** It sets `role="toolbar"` and
  `aria-orientation="horizontal"` (`:159-161`), and only ArrowLeft, ArrowRight, Home and End move
  focus (`:134-151`). A vertical column must switch to `"vertical"` and handle ArrowUp and ArrowDown.
- **The letter shortcuts (F/C/R/K/B/V/E, `:100-125`) don't depend on layout.** No change is needed.
- **The phone-only arm-then-confirm shove** (`:57-98`) keys on `usePhoneLayout()`, not on where the
  dock sits.
- **No raise slider exists.** Sizes are discrete buttons (the S9 invariant).
- **`.decisionbar.sim-actionbar` has its own 480px grid rule** (`app.css:583-591`). It never fires
  in landscape.
- **The ☰ section-sheet opener** (`.nav-reveal`, z 40) sits at the bottom-left, on the dock strip
  (`app.css:6849-6870`). The sheet it opens (z 30) rises from the bottom.

## Orientation, portrait and full screen

- **Portrait (`app.css:7098+`) promises not to touch the felt.** It records six-pod collisions in
  portrait as known and unsolved (`:7092-7097`). The rotate hint appears when
  `phone && portrait && atTable && !dismissed`.
- **`.app:not(:has(.simulate)) { padding-bottom: 0 }`** (`:7126-7128`) assumes the dock strip is a
  bottom strip.
- **The media-query strings have three homes each.** `usePhoneLayout.ts:16` and
  `useOrientation.ts` each carry a string that must stay byte-identical to its CSS `@media`
  opener.
- **No fullscreen or orientation-lock code exists.** The LAN page is served over plain `http://`
  (`scripts/serve.sh`).
  - `requestFullscreen()` does not require a secure context.
  - `screen.orientation.lock()` does, so it would reject on the LAN origin.

## Tests

Only the pure-logic modules are tested (`rotateHint`, `handCount`, `blindCheck`, `replaySeats`,
`revealRequest`, `simGrade`, `simPlayback`, `allIn`, `staleState`). Nothing renders `SimTable`,
`HandReplayTable`, `SimActionBar` or `SimulateView`. The repo has no jsdom or React Testing
Library, and adding either is a new dependency. Layout contracts are therefore verified by a
browser bounding-box measurement, which the spec names.
