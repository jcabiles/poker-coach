# Tickets — phone table fit (landscape felt on a real phone browser)

**Bottom line.** Six tickets, built in order. Every ticket touches `app.css`, which has one owner at
a time, so they run strictly one after another. Five are design tickets and one is the measurement
and docs close-out. Spec: `../specs/phone-table-fit-ux.md` (rev 2). Contracts:
`../contracts/phone-table-fit-ux.md`.

**Every ticket, in addition to its own done-condition:**
- `make check` is green.
- The design reviewer's pass runs on a worktree review stack on new ports, with `DB_PATH` confirmed
  under the worktree. The owner's `:7777`/`:8008` stack is never used.
- The new rules live in the `(max-height: 560px) and (orientation: landscape)` block, which sits
  after the phone gate and before the portrait block.
- CSS values come from tokens only.

## T1 — Ring sizing and the `data-seats` selector

- **Owns:** `styles/app.css`, `styles/tokens.css`, `components/simulate/SimTable.tsx`,
  `components/simulate/HandReplayTable.tsx`.
- **Does:**
  - Adds `data-seats={n}` to the ring in both tables.
  - Rewrites the nine-seat opt-out as `.tablering:not([data-seats="9"])` and updates its comment.
  - Adds `--dock-col-w`.
  - Opens the landscape block with the `.app:has(.simulate)` right padding.
  - Adds the `.simulate .tablering[data-seats]` / `.history-replay .tablering[data-seats]` height
    rule. It drops `aspect-ratio` and fills the height left after the `.ctx` line and the felt
    frame.
- **Done when:**
  - At 914×290 the ring measures ≥210px tall on both 6 and 9 seats.
  - At 412×915 portrait, 9 seats still leaves the ring unclamped and 6 seats keeps today's cap; the
    ring height matches `main` to the pixel.
  - Desktop 1440×900 and 1024×768 ring sizes are identical to `main`.

## T2 — Right-column dock and the corner cluster

- **Owns:** `styles/app.css`, `components/simulate/SimActionBar.tsx`, new
  `lib/toolbarKeys.ts` and `lib/toolbarKeys.test.ts`, new `lib/usePhoneLandscape.ts`,
  `components/simulate/SimulateView.tsx` (passes the orientation only).
- **Does:**
  - Moves both dock variants to a fixed right column, `--dock-col-w` wide.
  - Moves `.nav-reveal` to a fixed top-right corner row, leaving a slot beside it for T5's button.
  - Re-anchors the stale notice and the shove warning (explicit max-width, z 20/21/22 kept).
  - Sets `scroll-padding-bottom: 0` in landscape.
  - `SimActionBar` sets `aria-orientation` from the prop.
  - The pure `nextToolbarIndex(key, orientation, i, n)` handles Arrow keys on both axes plus
    Home/End, with vitest cases for each.
  - `PHONE_LANDSCAPE_QUERY` is byte-identical to the CSS `@media` opener, with a comment naming
    both homes.
- **Done when:**
  - At 914×290, facing a raise (four buttons), every dock button is fully inside the viewport and
    left of nothing.
  - The felt's right edge is less than or equal to the column's left edge.
  - The armed-shove warning is fully visible and does not cover a dock button.
  - ArrowUp/ArrowDown move focus in the column.
  - History, Practice and Quiz layouts at 914×290 match `main`.

## T3 — Slim villain pods and the compact hero pod

- **Owns:** `styles/app.css`, `components/simulate/SimTable.tsx`,
  `components/simulate/HandReplayTable.tsx`.
- **Does:**
  - Villain pods get at most two rows: the position row (position, dealer disc, stack, miniature
    card-back marker) and the action row (`.sim-actrow` at line-height 1.25, or `.hrt-pod-delta` in
    the replayer).
  - Showdown and R1 cards show at `calc(var(--card-h) * 0.32)`.
  - Hero: cards on the left, and a stacked meta column (~`calc(var(--card-w) * 2)`) holding
    position, stack, "your turn" and the verdict badge.
  - All gating is unchanged (`revealed`, staged `folded`, `playbackComplete`).
  - Markup changes stay inside the pod, so nothing is inserted before the seats in the ring.
- **Done when:** at 914×290, 800×360 and 915×412, on 6 and 9 seats, in the live states (preflop,
  flop with chips, river, showdown, hand over, bots acting) and the History steps (preflop, river,
  showdown with delta):
  - zero pod×pod, pod×`.table-center`-child and pod×`.ctx` intersections;
  - no pod clipped by `.stage`;
  - hero pod ≤180px wide.

## T4 — Seat details on tap (live table)

- **Owns:** `components/simulate/SimTable.tsx`, `components/simulate/SimulateView.tsx`,
  `styles/app.css`.
- **Does:**
  - When `labelsVisible` and the seat has a persona, the position row is a `<button>` with
    `aria-expanded` and `min-height: 24px`. Its name is "<pos>[ dealer] <stack>bb details".
  - One seat is expanded at a time. The expanded pod shows the persona plate and RANGE, lifted, and
    grows toward the ring centre.
  - It closes on:
    - a second tap;
    - a tap on another seat;
    - the hand ending;
    - the staged fold (`openSeatStagedFolded`);
    - pod-local Esc, using the `HandReplayTable.tsx:164` guard.
  - RANGE is a sibling that stops propagation.
  - When RANGE opens the panel in phone landscape, the panel scrolls into view using the #236
    pattern.
  - With labels off, there is no button.
- **Done when:**
  - The sweep's expanded states (top half and bottom half, 6 and 9 seats) show no clipping.
  - Esc with an armed shove cancels only the shove.
  - A RANGE tap toggles only the range.
  - An expanded pod collapses exactly when its fold is narrated, not before.
  - Visible focus and ≥4.5:1 contrast hold on the button in both themes.

## T5 — Full-screen button

- **Owns:** new `lib/fullscreen.ts` and `lib/fullscreen.test.ts`, new
  `components/simulate/SimFullscreenButton.tsx`, `components/simulate/SimulateView.tsx`,
  `styles/app.css`.
- **Does:**
  - The helper takes a `Document`-shaped argument and exposes `supported`, `isOn` and `toggle`.
  - `toggle` never calls `screen.orientation.lock()`. On a rejected request it leaves the state
    off, with a one-line comment saying why the rejection is ignored.
  - The button shows only on Simulate when `usePhoneLayout()` and `fullscreenEnabled` are true.
    It sits in the corner cluster in landscape and in the Simulate top bar in portrait.
  - It sets `aria-pressed` and follows `fullscreenchange`.
- **Done when:**
  - The vitest tests cover supported and unsupported documents, the on/off toggle and a rejected
    request.
  - In the browser review, pressing the button enters and leaves full screen, and the ring grows
    with the taller viewport.
  - The button is absent on desktop 1440×900.

## T6 — Full sweep, regression, docs

- **Owns:** `docs/ai-dlc/specs/phone-table-fit-ux.md` ("Built as"),
  `docs/ai-dlc/ledger/phone-and-6max.md` (fan-in), `docs/ai-dlc/roadmap/phone-and-6max.md`,
  `docs/ai-dlc/log.md`, `docs/ai-dlc/profile.md` (Resume).
- **Does:**
  - Runs the spec's full Verify-by sweep, with every viewport × state × seat count, plus 1280×540.
  - Compares portrait and desktop screenshots against `main`.
  - Runs a blind refuter on the diff.
  - Records the results.
- **Done when:**
  - Every sweep criterion passes, or the leftovers are listed as open.
  - The PR is opened on `feat/phone-table-fit`.
  - The owner's phone check (one 6-max and one 9-max landscape hand, with and without full screen)
    is recorded as owed.
