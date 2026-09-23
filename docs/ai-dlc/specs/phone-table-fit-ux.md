# Spec — phone table fit: a landscape felt that fits a real phone browser (rev 1)

**Bottom line.** On the owner's Android phone in landscape, with Chrome's address bar showing, the
page is only about 914×290 CSS pixels. At that size the table ring is squashed to 840×154 and the
seat labels pile on top of each other. The fix has three parts:

- In phone landscape, the action buttons move from a bottom bar to a column on the right edge.
- Villain seats shrink to two rows, and their player type and RANGE open on a tap.
- A full-screen button hides the browser's bars.

It covers 6-max and 9-max, on the live table and in the History replayer. Portrait and desktop do
not change.

## Why the earlier fix missed it

P3a (the phone felt fix, merged as #231) measured zero seat overlaps at 915×412, 851×393 and 800×360.
Those are whole-screen sizes. A real Chrome tab in landscape loses about 56px to the address bar and
more to the status and gesture bars. Measured on the owner's own live hand at 914×290, 2026-09-22:

| Element | Size at 914×290 |
|---|---|
| Ring | 840×154 (5.5:1; the design is 2.1:1) |
| Villain pods | ~90×95 each |
| Hero pod | 147×99 |
| Dock | 61px tall |
| LJ × BB pods | overlap by 2,670px² |
| HJ pod | above the ring's top edge, over the `.ctx` header line |

The ring's `aspect-ratio` loses to the phone gate's `max-height` cap (contracts §Bottom line 2). The
pods keep their desktop height of five stacked rows.

## Design commitment (owner, 2026-09-22 — the interview picker)

- **Approach: "Side buttons + slim seats."**
  - In phone landscape, Fold/Call/Raise stand in a column on the right edge, and the table takes
    the full remaining height.
  - A villain seat shows two rows: position and stack, then the last action (with chips) when there
    is one.
  - The player type and the RANGE button sit behind a tap on the seat.
- **Extras chosen:** a full-screen button, and 9-max fixed too.
- **Extra not chosen:** moving the `.ctx` header lines off the felt. They stay where they are, and
  no seat may cover them.
- **Aesthetic: unchanged.** This is a fit pass inside the existing night/day felt room (tokens,
  serif display, brass accents). No new colours and no new type. The named direction is the
  existing "lamp-lit card room".
- **Accessibility: WCAG 2.2 AA.** Contrast is ≥4.5:1 for text and ≥3:1 for UI on the felt in both
  themes, focus is visible, and phone touch targets keep the existing 44px floor.

## Scope

**In scope.** The rules below fire only in phone landscape,
`(max-height: 560px) and (orientation: landscape)`. That is a new block placed after the existing
phone gate and before the portrait block.

1. **Ring sizing.**
   - The ring fills the height left after the felt frame and the `.ctx` line. Its width is the felt
     width minus the dock column.
   - The 9-max opt-out no longer applies in landscape.
   - The ring carries `data-seats={n}` in both tables, and every seat-count selector keys on it
     instead of `:nth-child(11)`. The portrait and desktop behaviour of the nine-seat opt-out is
     unchanged.
2. **Slim villain pods** (live table and replayer).
   - Row 1: position, the dealer disc, and the stack, plus a miniature card-back marker while the
     seat is still in the hand.
   - Row 2: `.sim-actrow` (verb and chips), only when there is one.
   - Face-up showdown or R1 cards replace the marker at a reduced size.
   - Every value is gated exactly as today (`revealed`, the staged `folded`, `playbackComplete`).
3. **Seat details on tap** (live table only; the replayer has no persona).
   - When `labelsVisible` and the seat has a persona, row 1 becomes a `<button>` with
     `aria-expanded` and the label "<pos> details".
   - Pressing it expands that one pod in place. It shows the persona plate and the RANGE button,
     lifted above its neighbours on the felt-chip scrim.
   - One pod is expanded at a time. The expansion closes on a second tap, on Esc, on a tap on
     another seat, and when the seat folds or the hand ends.
   - The RANGE button keeps its gate, label, `aria-pressed` and behaviour.
   - When RANGE opens the panel in phone landscape, the panel scrolls into view. This reuses the
     `scrollToReview` pattern from #236: `focus({preventScroll:true})` plus a transient
     `tabindex="-1"`.
   - With `labelsVisible` off (Challenge mode), row 1 is plain text and there is nothing to expand.
4. **Hero pod.**
   - The cards and `.herometa` sit side by side instead of stacked. The verdict badge and the
     verb/chips row keep their meaning.
   - The hero's cards stay at `--card-w-phone`.
5. **Right-column dock.**
   - Both `.decisionbar.sim-actionbar` and `.decisionbar.sim-nextdock` stand as a fixed column on the
     right edge. Its padding includes `env(safe-area-inset-right)` and its buttons are stacked
     full-width.
   - The `.app` reservation moves from bottom padding to right padding. `scroll-padding-bottom`
     returns to 0 in landscape.
   - The stale-tab notice (z 21) and the armed-shove warning (z 22) re-anchor to the column's left
     edge. The z-order 20/21/22 is preserved.
   - `.nav-reveal` (☰, z 40) moves to the top of the column. The sheet it opens is unchanged.
   - `SimActionBar` takes the orientation: `aria-orientation="vertical"` in phone landscape, with
     ArrowUp and ArrowDown moving focus. ArrowLeft and ArrowRight keep working as well. The key
     mapping lives in a pure function with a vitest test.
6. **Full-screen button.**
   - Shown only when `document.fullscreenEnabled` and `usePhoneLayout()` are true, in both phone
     orientations. It sits at the top of the dock column in landscape and in the Simulate top bar
     in portrait.
   - It toggles `document.documentElement.requestFullscreen()` / `document.exitFullscreen()`,
     tracks `fullscreenchange` for its label and `aria-pressed`, and never calls
     `screen.orientation.lock()`. That call needs a secure context, and the LAN page is plain
     `http://`.
   - A rejected request leaves the button in its off state, with a code comment stating why the
     rejection is ignored.
   - The helper lives in `frontend/src/lib/fullscreen.ts` and has a vitest test that uses a fake
     `document`.

**Out of scope.**
- Portrait felt geometry. Portrait keeps the rotate hint.
- Desktop and tablet layout.
- `PokerTable.tsx` (Practice/Quiz).
- The `.ctx` lines' position.
- New colours or type.
- Orientation lock.
- A PWA manifest or service worker.
- Seat geometry math (`slotStyle`), unless the measurement below proves a collision that slim pods
  cannot remove. In that case both copies change together and the spec is revised first.
- Any backend change.

## Constraints

- CSS values come from design tokens only (`var(--space-*)`, `--card-*`, colour tokens). No raw
  hex, and no raw px outside the existing `560px` breakpoint literals.
- AA contrast and visible focus in the night and day themes.
- The lockstep rule: nothing on a pod leads the event log.
- The media-query strings keep their three homes each, byte-identical. A new
  `PHONE_LANDSCAPE_QUERY` constant is used by a hook and matches its CSS `@media` opener
  byte-for-byte.
- The new block sits after the existing phone gate, so source order wins ties.
- No new dependency. `make check` is green.
- **Review stacks never touch the owner's live stack** (`:7777` / `:8008`, where a live hand is in
  progress). Reviews run a worktree backend and frontend on new ports, with `app.db.session.DB_PATH`
  confirmed to be under the worktree.

## Verify-by

1. **`make check`** is green, including the new vitest tests: the toolbar key mapping and the
   fullscreen helper.
2. **Bounding-box sweep**, run by the design reviewer with `browser_evaluate` on the review stack.
   - Viewports:
     - landscape 914×290 (owner's phone with the address bar);
     - 915×412 and 800×360 (full-screen sizes);
     - 851×393.
   - States, each at 6 seats and at 9 seats:
     - preflop, hero to act;
     - flop with chips in front;
     - river with a five-card board;
     - showdown with revealed cards;
     - hand over with the next-hand dock;
     - one seat expanded.
   - Pass means all of the following:
     - zero intersecting pairs among `.tseat` pods, except the expanded pod, which may overlay by
       design;
     - zero intersections between pods and `.table-center` children or `.ctx`;
     - no pod clipped by `.stage`;
     - the felt and the dock both entirely within the viewport with no scroll;
     - no horizontal scroll.
3. **Regression.**
   - Portrait 412×915 and desktop 1440×900 and 1024×768 look the same as `main`, checked by
     screenshot comparison.
   - The 9-max portrait opt-out still leaves the ring unclamped.
4. **Keyboard and accessibility.**
   - Tab and arrow travel through the vertical dock.
   - Esc collapses an expanded seat.
   - Focus is visible on the seat button, RANGE and the full-screen button in both themes.
   - Contrast is ≥4.5:1 for every new text on the felt.
5. **Owner check on the phone.** One 6-max and one 9-max hand in landscape, with and without full
   screen. This is the product verdict and is owed by the owner.

## Built as

(filled in after the build)
