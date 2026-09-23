# Spec — phone table fit: a landscape felt that fits a real phone browser (rev 2)

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
  themes, and focus is visible. Dock and page controls keep the existing 44px phone floor; seat
  buttons use the 24px AA minimum because 9-max seats are only 41px apart (§3).

## Scope

**In scope.** The rules below fire only in phone landscape,
`(max-height: 560px) and (orientation: landscape)`. That is a new block placed after the existing
phone gate and before the portrait block.

1. **Ring sizing.**
   - The ring fills the height left after the felt frame and the `.ctx` line. Its width is whatever
     the felt has once `.app` reserves the dock column's padding; the column is subtracted once,
     never twice.
   - The 9-max opt-out no longer applies in landscape.
   - The ring carries `data-seats={n}` in both tables, and every seat-count selector keys on it
     instead of `:nth-child(11)`.
     - The existing cap becomes `.simulate .tablering:not([data-seats="9"])` (and the same for
       `.history-replay`). That is specificity (0,3,0).
     - The landscape rule uses `.simulate .tablering[data-seats]`, also (0,3,0). Because it comes
       later in the file, it wins.
     - Without this, the old `:not(:has(...))` selector at (0,4,0) beats a plain (0,2,0) landscape
       rule, and the ring stays capped at ~154px (review B2).
   - Portrait and desktop behaviour of the nine-seat opt-out is unchanged.
   - Height budget at 914×290 with 9 seats, per review B1–B3: the ring is ~226px tall and ~656px
     wide. Seat centres fall at 26, 67, 128, 179 and 199px. A two-row pod is ~38px, so the
     tightest vertical gap is 41px between centres, which fits.
2. **Slim villain pods** (live table and replayer).
   - Two rows at most.
     - The position row: position, the dealer disc, the stack, and a miniature card-back marker
       while the seat is still in the hand.
     - The action row: `.sim-actrow` (verb and chips), only when there is one, at line-height 1.25.
   - Visual order is the designer's choice. `.sim-actrow` is `order: -2` today (`app.css:2974`), so
     it draws above.
   - Face-up showdown or R1 cards replace the marker at `calc(var(--card-h) * 0.32)` height. That
     is pinned so the 41px spacing between neighbouring 9-max seats holds (review S1).
   - Every value is gated exactly as today (`revealed`, the staged `folded`, `playbackComplete`).
     Nothing new may lead the event log. The stack figure is already ungated today
     (`SimTable.tsx:350-353`); that is left as is (review O3).
   - The replayer's showdown row, `.hrt-pod-delta`, counts as the action row there.
3. **Seat details on tap** (live table only; the replayer has no persona).
   - When `labelsVisible` and the seat has a persona, the position row becomes a `<button>`.
     - It sets `aria-expanded`.
     - It is `min-height: 24px`, the AA minimum. The 44px phone floor does not apply here because
       neighbouring 9-max pods are 41px apart (review S1).
     - Its accessible name contains the visible text: "<pos> <stack>bb details", plus "dealer"
       when the seat has the disc. That satisfies WCAG 2.5.3, Label in Name (review S6).
   - Pressing it expands that one pod in place. It shows the persona plate and the RANGE button,
     lifted above its neighbours on the felt-chip scrim.
   - An expanded pod grows toward the ring centre, so it is never clipped by `.stage` (review S7).
     Pods in the top half grow down; pods in the bottom half grow up.
   - One pod is expanded at a time. The expansion closes in any of these cases:
     - a second tap on the same seat;
     - a tap on another seat;
     - the hand ends;
     - the seat folds, read from the staged fold `openSeatStagedFolded` and never from raw
       `seat.status` (review S5);
     - Esc.
   - Esc is handled only on the expanded pod's own keydown, not on `window`. When an armed shove,
     the range panel or the nav sheet claimed it, it does nothing. Reuse the guard at
     `HandReplayTable.tsx:164` (review S4).
   - RANGE is a sibling of the seat button, never inside it, and it stops its click from
     propagating. It keeps its gate, label, `aria-pressed` and behaviour.
   - When RANGE opens the panel in phone landscape, the panel scrolls into view. This reuses the
     `scrollToReview` pattern from #236: `focus({preventScroll:true})` plus a transient
     `tabindex="-1"`.
   - With `labelsVisible` off (Challenge mode), row 1 is plain text and there is nothing to expand.
4. **Hero pod.**
   - The cards sit on the left. A narrow column on their right holds, in short stacked lines,
     position and dealer, the stack, "your turn", and the verdict badge. That column is about
     `calc(var(--card-w) * 2)` wide.
   - The pod is at most ~180px wide and ~64px tall at every landscape viewport, so it clears the
     9-max seats beside it at 79% height (review B3; the binding case is 800×360).
   - The verb and chips keep their meaning. The hero's cards stay at `--card-w-phone`.
5. **Right-column dock** (all rules scoped to `.app:has(.simulate)`; History, Practice and Quiz
   keep today's layout, per review S3).
   - Both `.decisionbar.sim-actionbar` and `.decisionbar.sim-nextdock` stand as a fixed column on the
     right edge, with buttons stacked full-width.
     - Its width is one new token, `--dock-col-w` in `tokens.css`, which is ~`calc(var(--space-8) * 3)`.
       That token sizes both the column and `.app`'s right padding (review S2).
     - Long labels wrap to two lines rather than widen the column.
     - No safe-area padding: `index.html` has no `viewport-fit=cover`, so the inset is always 0
       (review O2).
   - The `.app` reservation moves from bottom padding to right padding. `scroll-padding-bottom`
     returns to 0 in landscape.
   - The stale-tab notice (z 21) and the armed-shove warning (z 22) re-anchor to the column's left
     edge. The warning gets an explicit max-width. The z-order 20/21/22 is preserved.
   - **Corner cluster.** `.nav-reveal` (☰, z 40) and the full-screen button are fixed on their own,
     side by side in one row at the top-right. They stay visible while bots act and before a deal,
     when no dock is mounted (review S3). The dock column starts below them. The sheet ☰ opens is
     unchanged.
   - Height budget at 290px: the cluster row is 8+44+8, and four action buttons are 4×44+3×8, plus
     8 of padding. That totals ~268px, which fits. Stacking the two corner buttons would need
     320px (review B1).
   - `SimActionBar` takes the orientation: `aria-orientation="vertical"` in phone landscape, with
     ArrowUp and ArrowDown moving focus. ArrowLeft and ArrowRight keep working as well. The key
     mapping lives in a pure function with a vitest test.
6. **Full-screen button.**
   - Shown only on the Simulate route, when `document.fullscreenEnabled` and `usePhoneLayout()`
     are true, in both phone orientations. In landscape it sits in the corner cluster; in portrait
     it sits in the Simulate top bar.
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
- The lockstep rule: nothing new on a pod leads the event log (the stack is already ungated; see §2).
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
     - facing a raise (four dock buttons);
     - an armed shove, with its warning;
     - one seat expanded, top half and bottom half;
     - bots acting (no dock mounted);
     - History replayer: preflop step, river step, and the showdown step with `.hrt-pod-delta`.
   - Pass means all of the following:
     - zero intersecting pairs among `.tseat` pods, except the expanded pod, which may overlay by
       design;
     - zero intersections between pods and `.table-center` children or `.ctx`;
     - no pod clipped by `.stage`;
     - the felt and the dock both entirely within the viewport with no scroll;
     - the felt's right edge left of the dock column's left edge, and neither touching the corner
       cluster;
     - no horizontal scroll.
3. **Regression.**
   - Portrait 412×915 and desktop 1440×900 and 1024×768 look the same as `main`, checked by
     screenshot comparison.
   - A short desktop window, 1280×540, already gets the phone layout today. It is checked for no
     overlap and a working mouse click on the seat button (review O1).
   - The 9-max portrait opt-out still leaves the ring unclamped.
4. **Keyboard and accessibility.**
   - Tab and arrow travel through the vertical dock.
   - Esc collapses an expanded seat.
   - Focus is visible on the seat button, RANGE and the full-screen button in both themes.
   - Contrast is ≥4.5:1 for every new text on the felt.
5. **Owner check on the phone.** One 6-max and one 9-max hand in landscape, with and without full
   screen. This is the product verdict and is owed by the owner.

## Built as

**Bottom line.** All six tickets are built on `feat/phone-table-fit`. In three build rounds, a blind
browser review measured zero seat overlaps and no clipped seats at 914×290 and 800×360, 6 and 9
seats, on the live table and in the History replayer. Spot checks at 915×412 and 1280×540 were also
clean. The final gate is `make check`, green. What remains is the owner's phone check.

**Built:**
- **Ring.** At 914×290 it is 732×224, up from 840×154. It is 618×294 at 800×360. The seat-count
  selector keys on `data-seats`.
- **Dock.** A right-edge column, `--dock-col-w` = 112px rather than ~96px, so the ☰ and the
  full-screen button fit side by side in the corner row. Buttons stack from the bottom, and the
  toolbar is vertical with ArrowUp/Down (`lib/toolbarKeys.ts`, tested).
- **Seats.** Villain seats are two rows (`SimCompactSeat.tsx`, split out of `SimTable.tsx` to keep
  it under 500 lines).
  - The board is 0.85× in landscape.
  - The compact chip drops "· all-in"; the stack line carries it until the final batch has played
    out.
  - Folded seats lose their pill and use an 80% ink, measured 4.96:1 on the lamp-lit Night felt.
  - Top-centre seats open sideways so their details never cover the board.
- **Hero.** 176×64 live and ≤152 wide in the replayer, with its action text under its cards.
- **Full screen.** `lib/fullscreen.ts` (tested) and `SimFullscreenButton.tsx`. The accessible name
  is fixed, "Full screen", and `aria-pressed` carries the state. That is a Director ruling that
  overrides §6's "tracks fullscreenchange for its label", because a changing label with
  `aria-pressed` would be announced twice.

**Accepted additions beyond the spec** (reviewed and recorded in the ledger, round 7 fan-in):
- **Two portrait changes**, against the bottom line's "portrait does not change":
  - `overflow-anchor: none` on `.sim-topbar` stops the felt drifting off the top as bots act.
  - Taking a seat on any phone no longer scrolls the table off screen.
  Both are fixes to older bugs the reviews found.
- **Day-theme fixes.** The gold Raise button is a solid fill at 4.94:1. The armed-shove hover is
  5.03:1. "Your turn" and the pot line clear 4.5:1.
- **Changes on every viewport:**
  - "Raise small" / "Bet big" labels use a no-break space.
  - The Esc key while a shove is armed moved to a page-level listener. It yields to the nav sheet
    (which now claims the key with `preventDefault`), dialogs and the range panel.
- **Range panel.** Closing it in landscape returns the page to the felt, with focus on RANGE, the
  seat button, or the table heading.

**Not verified in a browser; owed by the owner's phone:**
- the ring growing when full screen adds height;
- the back gesture leaving full screen;
- the button hiding on an iPhone.

**Recorded, not built:** `useSeatDetails` (when an expanded seat closes) has no unit test.
`usePhoneLandscape` is a third copy of the `matchMedia` hook pattern. `app.css` (~7,800 lines) and
`SimulateView.tsx` (~1,700) grew; splitting the landscape block into its own stylesheet is a later
refactor.
