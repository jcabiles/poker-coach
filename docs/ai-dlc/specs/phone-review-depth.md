# Spec — phone review depth (post-hand review card, session stats and leaks, hand replayer)

status: **rev 2, APPROVED** — pre-authorized for build by the owner's
`/ai-org:spec --auto-build phone review depth` invocation, 2026-09-22. Gate 1 (requirements playback)
was settled in the owner's frontloaded interview of 2026-09-22 (see "Owner rulings"); the measurement
below turned the roadmap's open question into numbers. Rev 2 folds the blind review (Claude refuter,
FAIL, 6 should-fix + 7 optional, all accepted; Codex did not run in the sandbox; ledger Round 6): the
Space/Enter deal key now skips the focused review wrapper, focus moves use `preventScroll`, the
per-element focus-ring opt-out is stated correctly, Esc yields to the nav sheet and the blind-check
dialog, the History rotate hint renders inside the replayer so the mount scroll cannot hide it, the
existing rotate-hint helpers are moved rather than renamed, and the dead `.sim-review-btn` floor rule
is gone.
slice of: `../roadmap/phone-and-6max.md`, NEXT lane "Phone review depth".
contract map: `../contracts/phone-review-depth.md` · measurement:
`../reviews/phone-review-depth-measurement.md` · tickets: `../tickets/phone-review-depth.md`.
Branch `feat/phone-review-depth` from `main` at c0e3269 (nothing stacked; everything earlier is merged).

## Bottom line

The three review surfaces are already readable on the phone; what is broken is REACHING them.
When a hand ends in landscape the review card starts 268px below a 351px screen and the only control
on screen says "Next hand", so nothing tells the player a review exists. Opening a hand replay from
either entry point lands the viewport past the felt (History: 303px past it, in a 126,448px list;
in-session landscape: the header 189px above the screen) because the page shrinks under the scroll
position, and closing it drops the player at a random point in the list with focus on the body.
Every control these surfaces add is under the 44px touch floor the earlier slices gave the session's
other controls. Session stats and leaks measured clean at every size and get NO change. This slice
adds one "Review" button to the pinned dock, fixes scroll and focus on replay open and close at both
entry points (and Esc to close), extends the rotate hint to the History replayer in portrait, raises
six controls to the touch floor, and lets the coach note use the card's full width. No backend, one
small shared component (the rotate hint, see "Built as"), no felt geometry.

## Owner rulings (2026-09-22, do not re-ask)

Order of value: the post-hand review card first, then session stats and leaks, then the hand replayer.
The felt in portrait is recorded, not fixed; the rotate hint is the answer. The session's control
cluster (speed, Watch, Coach/Real, Replay, Leave) stays BELOW the felt in portrait. Practice and Quiz
are do-not-break only. Desktop at 1280×800 pixel-identical. Tokens only; AA contrast and visible focus
in both themes. No check-ins until the PR is ready; the owner merges every PR.

## Director decisions inside those rulings

- **Stats and leaks: no change.** The Dashboard measured zero overflow, zero text under 11px, zero
  targets under 44px and zero contrast failures at all three phone sizes; its by-street report is a
  list of bar rows, not a table, so it cannot scroll sideways. Its only cost is height (3.2 screens at
  360×800), which is content, not a defect. Gain of doing nothing: the ruled second priority costs
  nothing. Cost: none found.
- **The review card is reached by a button, not by an automatic scroll.** An automatic scroll when the
  hand ends would take the felt (where the showdown cards are) off screen at the moment the player
  wants to see it, and nothing in the app scrolls the page on its own today. A second button in the
  dock that already exists ("Review ↓" beside "Next hand →") is discoverable, costs no new fixed
  element, and leaves the player in charge. Cost: the dock carries two buttons at hand end on a
  phone (the same 61px strip; the Practice decision bar already holds up to five).
- **Replay scroll and focus are fixed at every size, not only on the phone.** The document collapse
  that clamps the scroll happens on desktop too (104,748px list); the fix is behaviour, not pixels,
  so the desktop boxes stay identical while the behaviour improves everywhere. Cost: JSX edits in
  four files rather than one CSS block.
- **History pagination is recorded, not built.** 1,964 rows render as 126,448px at 360 wide. The
  scroll and focus restore makes the long list tolerable; a "load more" needs a backend change and is
  a separate slice. Recorded in the roadmap as a follow-up under the phone lane.
- **The "Replay last hand" button stays where the control cluster is** (document y2,102 in landscape),
  because the cluster's position is an owner ruling from the P3b slice. Cost: the replayer is one long
  scroll away on the phone; the dock's "Review ↓" halves that scroll. A shortcut from the card is a
  later slice if the owner reaches for the replayer on the phone.

## Goal (one line)

On an Android phone, a finished hand shows a way to reach its review, both hand replayers open with
their felt and controls on screen and close back to where the player was with focus on the control
they used, and every review control is at least 44px tall.

## What changes

### 1. "Review ↓" in the pinned dock (`SimulateView.tsx`, `app.css` phone gate)

The dock `div.decisionbar.sim-nextdock` (`SimulateView.tsx:1543-1553`, rendered only under the phone
gate when `hand.hand_over && revealHandEnd && !checkPending`) gets a second button BEFORE "Next hand →":

```tsx
<button type="button" className="btn decision-btn sim-review-btn" onClick={scrollToReview}>
  Review ↓
</button>
```

`scrollToReview` scrolls the `section[aria-label="Hand result"]` (`SimShowdown`, which is always
mounted under the same gate; the recap follows it when Coach mode is on) to the top of the viewport
via a ref on a wrapper `div.sim-review` placed around the `SimShowdown` + `SimRecap` fragment at
`SimulateView.tsx:1589-1607`, using `scrollIntoView({ block: "start", behavior })` where `behavior`
is `"auto"` when the existing `prefersReducedMotion()` helper (`SimulateView.tsx:192`) says so and
`"smooth"` otherwise, then moves focus to that wrapper (`tabIndex={-1}`) with `focus({ preventScroll:
true })`, so a keyboard or screen-reader user lands on the review too and the focus call cannot undo
the scroll. Two consequences the review found, both handled here:
- The global Space/Enter deal-key handler (`SimulateView.tsx:1102-1113`) is live under exactly this
  gate and skips only buttons, links and inputs; a focused `div` would make the player's next Space
  press deal the next hand and destroy the review they just reached. The wrapper joins that handler's
  `closest()` skip list (add `[tabindex="-1"]` to the selector string), which also covers the `h1`
  focus fallback in item 3.
- A scripted focus paints the 3px `:focus-visible` ring (`tokens.css:244`) when the last input was a
  key press; the app's convention is a per-element opt-out (`app.css:6047`,
  `.sim-heading[tabindex="-1"]:focus, .smc-title[tabindex="-1"]:focus { outline: none }`). Add
  `.sim-review[tabindex="-1"]:focus` to that rule so Enter on "Review ↓" does not ring the whole
  1,052px card. The replayer titles and the History title (items 2 and 3) are NOT added: a ring on a
  heading after a scripted focus is the signal a keyboard user wants.
The button is not primary (plain `btn decision-btn`; `.decision-btn` already carries the 44px floor at
`app.css:626`, so no new floor rule is needed); "Next hand →" keeps the primary plate. The label reads
"Review ↓" whether Coach mode is on or off; with it off the target is the settlement slip alone, which
is still the hand's review surface. The mount gate of `SimShowdown` / `SimRecap` (`revealHandEnd`,
`coachMode`) does not change; the wrapper is a plain `div` with no padding, border, overflow or
display change (any of those would alter the desktop boxes), and only `scroll-margin-top:
var(--space-4)` in the phone gate so the card's top edge clears the viewport edge.

### 2. Replay open: felt and controls on screen; focus on the heading (`HandReplay.tsx`, `HandReplayTable.tsx`)

Both replayers, on mount, scroll their own `section` to the top of the viewport
(`scrollIntoView({ block: "start" })`, no smooth behaviour on mount) and focus their `h2` title
(`.hr-title` / `.hrt-title` get `tabIndex={-1}`) with `focus({ preventScroll: true })`, in a
`useEffect` that runs once per mount (the host already remounts per hand via `key={sim_hand_id}`).
This runs AFTER the host has swapped the list or the table for the replayer, which is exactly when the
browser has clamped the scroll (measurement §3: stage at viewport −303 in History, header at −189 in
session). `HandReplay` has a second return path for an empty reconstruction (`HandReplay.tsx:134-149`)
with its own `section.hr` and `h2.hr-title`; the ref and `tabIndex` go on both so the mount behaviour
is the same there. Both components keep their identical minimum signature `{ replay, onClose }`
(contract map, surface 3).

### 3. Replay close: return to the row or the button that opened it (`HistoryView.tsx`, `SimulateView.tsx`)

- `HistoryView`: `openHand` records `window.scrollY` and the opened `sim_hand_id` in a ref before
  `setReplay`. `closeReplay` sets a "restore pending" ref ONLY when a replay is open at call time
  (`closeReplay` is also the Dismiss handler for a failed replay load, `HistoryView.tsx:218`, when
  `replay` is already null; setting the ref there would leave a stale restore to fire on a later
  close). A `useLayoutEffect` that runs when `replay` becomes `null` and the ref is set restores
  `window.scrollTo(0, savedY)` and focuses the row button for that hand with `focus({ preventScroll:
  true })` (without it, the phone gate's 128px `scroll-padding-bottom` at `app.css:6755` makes a
  focus() scroll the row up by as much as 128px and the restore is lost). Row buttons register in a
  `Map<number, HTMLButtonElement>` ref via a callback ref on `button.history-hand-btn`
  (`HistoryView.tsx:267`); if the row is absent (the list reloaded), focus falls back to
  `h1.history-title` (`tabIndex={-1}`). Layout effect, not effect: the list must have re-rendered at
  full height before the scroll is set, or the browser clamps it again.
- `SimulateView`: `openLastReplay` records `window.scrollY`; `closeReplay` sets the same kind of
  pending ref under the same "only if a replay is open" guard (`SimulateView.tsx:1352` is its
  Dismiss use); a `useLayoutEffect` on `replay === null` restores the scroll and focuses
  `button.sim-replay-btn` via a ref with `preventScroll` (the button is rendered again once `!replay`,
  under the same gate it has today, `SimulateView.tsx:1301-1310`). If the button is not mounted (the
  hand advanced from another device under P4), focus goes to the page's existing `h1` in the
  Simulate heading, which gets `tabIndex={-1}` (and is covered by the deal-key skip in item 1).
  Known residual, accepted: the side column's "Your record" panel refetches after the restore, so in
  landscape the restored document can be ~18px shorter for one paint and the browser clamps by that
  much; the reviewer records the number rather than the slice chasing it.
- Esc closes both replayers: the existing window `keydown` handlers (`HandReplay.tsx:114-132`,
  `HandReplayTable.tsx:119-141`) gain an `Escape` case calling `onClose`, under the same guards (no
  modifier keys, not inside an editable element) PLUS one more: return early when
  `document.querySelector(".nav-tabs-open, dialog[open]")` matches. The phone's nav sheet closes on
  its own window Escape handler without `preventDefault` (`App.tsx:297-307`, class set at
  `App.tsx:399`), and the hand-200 blind check is a native `<dialog>` outside the replay branch
  (`SimulateView.tsx:1659`); without the guard one Esc would close the sheet AND the replayer, which
  on History throws away the place in the list this slice exists to keep. The `revealRequest` state
  machine is untouched; close already goes through `closeReplay`, whose reveal bookkeeping stays as it
  is.

### 4. Rotate hint on the History replayer in portrait (`HistoryView.tsx`, `rotateHint.ts`)

The same `<p className="sim-rotate-hint" role="note">` line SimulateView renders above its felt
(`SimulateView.tsx:1458-1477`) renders INSIDE `section.hrt.history-replay`, as the first child after
`header.hrt-head` (`HandReplayTable.tsx:145`), when the History replayer is open, under
`shouldShowRotateHint({ phone, portrait, atTable: replay != null, dismissed })` evaluated in
`HistoryView` (which owns `usePhoneLayout()`, `useIsPortrait()` and the dismissed state) and passed
to `HandReplayTable` as one optional prop `rotateHint?: ReactNode` (optional with a default of
nothing, so the `{ replay, onClose }` minimum signature the two replayers share is unchanged). Inside
the section, not above it: item 2 scrolls the section to the viewport top on mount, so a hint placed
before the section would be scrolled off on the one screen it exists for. The existing helpers
`readRotateHintDismissed()` / `writeRotateHintDismissed()` and `ROTATE_HINT_KEY`
(`SimulateView.tsx:70,175,184`) MOVE, names unchanged, into `rotateHint.ts` and are exported;
SimulateView imports them; behaviour identical; `rotateHint.ts`'s header comment and the `atTable`
doc comment (`rotateHint.ts:22-23`) are updated to say the module now also owns the storage key and
that the History replayer counts as a table. The predicate itself is unchanged and already fully
tested; the History wiring has no unit test (no jsdom in this repo) and is browser-verified by
Verify-by leg (d). The portrait replay felt's pod overlap (13 pairs at 360×800) is not touched, per
the ruling; the hint is the answer, as it is on the live felt.

### 5. Touch floor for the review controls (`app.css`, phone gate block only)

Add to the existing floor list at `app.css:7036-7043` (the phone gate, both orientations):
`.sim-recap-explain-btn`, `.hr-back`, `.hrt-back`, `.hr-step-btn`, `.hrt-step-btn`, `.hrt-move`.
Measured today: 93×24, 63×32, 71×39, 104×42, 104×42, 24px rows. The gate rule sits later in the file
at equal (0,1,0) specificity, so it wins over the base `min-height` at `app.css:5414` (40px) and
`:5573` (32px) without a specificity bump; the portrait block after it has no `.hr-*` / `.hrt-*` /
`.sim-recap*` rule to override it. `.hrt-move` is a button row in the Moves list; 22 rows at 44px is
968px, which portrait has and landscape scrolls past below the felt (the felt stays first;
`.hrt-moves { max-height: none }` below 1100px at `app.css:5620-5623` means the rows grow in page flow).

### 6. Coach note width (`app.css`, existing `max-width: 640px` block)

Beside `.sim-recap-coach { margin-left: 0 }` at `app.css:4832-4834`, add `.sim-recap-why {
margin-left: 0 }`. Today the standing coach note keeps a 69.2px desktop gutter and runs in 203px of a
336px card at 360 wide (~31 characters per line). The 640px block already exists for exactly this
reason; no new breakpoint.

## Built as (deviations recorded at fan-in, 2026-09-22)

- The review wrapper's `tabIndex={-1}` is transient, not static: "Review ↓" sets the attribute, focuses
  the wrapper, and removes it on blur. A standing attribute made the whole card click-focusable, and
  with the deal-key skip that would have switched off Space-to-deal after any desktop click on the
  recap (fan-in refuter, optional 1, accepted). The CSS opt-out and the deal-key skip are unchanged.
- The hint markup lives once, in `frontend/src/components/simulate/SimRotateHint.tsx`, used by both
  views; the storage helpers stay in `rotateHint.ts`. `Sim*` naming because `RotateHint.tsx` and
  `rotateHint.ts` differ only in case and the typecheck refuses that on this disk.
- `HistoryView` passes `atTable: true` (inside the `if (replay)` branch, where the value is the same).
- Everything else is as specified; the browser report records the numbers.

## Out of scope

Anything on the Dashboard or "Your record" (measured clean); History pagination or virtualisation
(follow-up recorded in the roadmap); the portrait replay felt geometry and `.stage` / `.sim-tablering`
/ card token rebinds; moving the control cluster or the "Replay last hand" button; street-rail jump
buttons on the in-session replayer; the two-H1 / no-`<main>` landmark on Simulate (optional finding,
recorded); any change to the phone gate string, `PHONE_LAYOUT_QUERY`, the portrait block, or
`App.tsx`; Practice/Quiz; the backend.

## Constraints (from the profile)

CSS values from tokens only (`--space-*`; the 44px floor as `calc(var(--space-8) + var(--space-3))`).
AA contrast and the 3px focus ring in both themes; the ring is `:focus-visible` at `tokens.css:244`
and the app opts single elements out per selector (`app.css:6047`), which is how the review wrapper
opts out (item 1) and why the headings do not. `noDescendingSpecificity` Biome baseline not widened
(the refuter re-linted the spec's CSS on a scratch copy: still 18 hits): new CSS goes inside the
existing blocks named above, with selectors no more specific than their neighbours. `app.css`,
`SimulateView.tsx` and `App.tsx` are single-owner hotspots: one worker owns every file in this slice;
`App.tsx` is untouched. No-peek stays structural: nothing here reads a later replay step. The
`revealHandEnd` / `coachMode` mount gates and the graded-only aggregate rules are unchanged
(contract map, bottom line 1 and 3). `--card-w` rebinds are untouched. No new dependency; no jsdom.

## Golden paths

`rotateHint.ts` for the module the storage helpers move into; `usePhoneLayout.ts` /
`useOrientation.ts` for the hooks; the dock markup at `SimulateView.tsx:1543` for the new button;
`errorPanelRef` + `tabIndex={-1}` at `SimulateView.tsx:1344` for focus moves, and `App.tsx:297-307`
for the shape of a window Escape handler (read only; `App.tsx` is not edited); the existing keydown
handlers in both replayers for the Esc case; the phone gate floor list at `app.css:7036` for the CSS;
`HandReplayTable`'s optional reveal props (`HandReplayTable.tsx:65-72`) for how an optional prop is
added without changing the shared minimum signature.

## Verify-by

`make check` green. Then a browser pass on the isolated stack (frontend :7791, backend :8131) at
915×412, 412×915 and 360×800, both themes, on the resumed session: (a) at hand end on the phone the
dock shows "Review ↓" then "Next hand →", both ≥44px tall; tapping Review puts the "Hand result"
section's top edge within the first 16px of the viewport and focus on the review wrapper with NO
outline painted; with focus there, pressing Space scrolls the page and does NOT deal; the dock stays
visible; "Next hand →" still deals; (b) in History at 360×800 scrolled ≥15,000px down, tapping a row
opens the replayer with `.hrt-head` and the felt inside the viewport and focus on `.hrt-title`;
"← Back" and Esc each return `window.scrollY` to within 1px of the saved value and focus to the same
row's button; with the nav sheet open (landscape), Esc closes the sheet and the replayer stays open;
(c) in session in landscape, "Replay last hand" opens with `.hr-head` at viewport y ≥ 0 and focus on
`.hr-title`; Back and Esc return focus to "Replay last hand" and the scroll to the saved value (record
the clamp, expected ≤ 20px, from the side panel's refetch); (d) the rotate hint shows inside the
History replayer in portrait only, below its header and above the felt, is visible right after the
open without scrolling, "Got it" there hides it on Simulate too within the tab, and it is absent at
915×412; (e) `.sim-recap-explain-btn`, `.hr-back`, `.hrt-back`, `.hr-step-btn`, `.hrt-step-btn`,
`.hrt-move` and `.sim-review-btn` measure ≥44px tall at all three phone sizes; (f) `.sim-recap-why`
`margin-left` is 0 at 360 and 412 and the note's text box is ≥300px wide at 360; (g)
`document.documentElement.scrollWidth <= clientWidth` on Simulate at hand end, History list, both
replayers, Dashboard, at all three sizes; (h) desktop 1280×800: `.sim-main` 864 wide at (16,212),
`.sim-side` 360 at x904, `.sim-recap` 681px tall at doc y1040, History section 1048 wide at (116,146),
Dashboard blocks at their recorded boxes (measurement §2), no dock, no "Review ↓", `.sim-recap-why`
keeps its 69.2px indent, `.hr-step-btn` 104×42 — all unchanged; (i) zero console errors on every
surface; (j) `npx vitest run` still passes `rotateHint.test.ts` (22 cases) after the helper move, and
`make check` is green.

## Definition of done

Done = every Verify-by leg passes AND `make check` exits clean AND nothing outside the ticket's owned
files changed AND the roadmap's "Phone review depth" entry (with the pagination follow-up), the
ledger, `log.md` and the Resume block are updated in the same PR.
