# Spec — P3b, phone polish for the non-felt pages (portrait)

status: **rev 1, APPROVED** — pre-authorized by the owner's `/ai-org:spec --auto-build` invocation,
2026-09-22, after a frontloaded interview (rulings recorded below and in the roadmap's P3 entry).
slice of: `../roadmap/phone-and-6max.md`, P3b (promoted to NOW by the owner 2026-09-22).
contract map: `../contracts/phone-p3b-portrait.md` · measurement:
`../reviews/phone-p3b-portrait-measurement.md` · tickets: `../tickets/phone-p3b-portrait.md`.
Stacks on P4 (PR #232); its PR opens after P4 merges (owner ruling on stacked PRs).

## Bottom line

Portrait on the phone is not broken by width. The 713px minimum width the July review found is
gone: five of seven screens have zero sideways overflow at 412, 393 and 360 wide. What is broken
is stacking order. The landscape fix (P3a) moves the masthead and nav BELOW the content, which is
right when the screen is 412px tall and wrong when it is 915px tall: in portrait the brand, theme
toggle and EV ledger sit 585 to 879px below the fold while staying first in the keyboard order, so
three Tab presses scroll the page down 1203px and back. This slice adds one portrait block at the
end of the stylesheet that restores document order for the chrome, wraps what must wrap, raises
ten in-session controls to the 44px touch floor, fixes History's 12px overflow at 360 wide, stops
the stats strip clipping itself, and adds a passive rotate hint above the felt in portrait. The
felt itself in portrait is out of scope by ruling; the hint exists because of it.

## Owner rulings (2026-09-22, do not re-ask)

Portrait layouts for the sit-down/resume screen, the session ledger and history, settings, and
session stats and leaks. One app-shell breakpoint so nothing scrolls sideways in portrait. A
passive, dismissible one-line rotate hint above the felt in portrait only. Practice and Quiz get
the shared masthead/nav fixes plus a no-overflow check, nothing page-specific. Desktop at 1280px
pixel-identical. Tokens only; AA contrast and visible focus in both themes. Reviewed by the
browser-eyes design reviewer at the owner's phone size.

## Director decisions inside those rulings

- **"Settings" = a portrait pass over the existing controls, not a new screen.** No settings page
  exists: speed, Watch, Coach/Real and Labels live in the Simulate topbar cluster, theme in the
  masthead, mode is immutable after sit-down. Building a screen would move five controls out of a
  1615-line component and the single-owner `App.tsx` and must preserve three behavioural contracts
  (ref-mirrored speed and Watch, the conditional Labels mount, mode-as-stamp). The pass makes those
  controls reachable, wrapped and 44px tall in portrait. Cost: they stay scattered. A real screen
  can be a later slice if the owner wants one after playing.
- **In portrait, the nav tabs return to the flow under the masthead and the floating reveal button
  is hidden.** The hidden bottom sheet solved a HEIGHT problem in landscape; portrait has height to
  spare, and the measurement found the fixed reveal button 4px from the Raise button in session and
  covering 65% of the EV-ledger figure on History. Cost: the two orientations navigate differently.
  Landscape is untouched.
- **The felt in portrait is recorded, not fixed.** Six seats collide (8 overlapping pairs at
  412×915, 11 at 360×800, hero pod clipped 11px) and the P3a chip badge covers the context line.
  That is the case the rotate hint answers. Nothing on `.stage`, `.sim-tablering`, `.ctx` or the
  card token rebind changes here.

## Goal (one line)

On an Android phone held upright, every non-felt Simulate page and the app chrome read top-down in
document order with nothing clipped, nothing under the 44px touch floor, and a one-line hint on the
felt route to turn the phone sideways.

## What changes

All CSS goes in ONE new block appended at the very end of `frontend/src/styles/app.css`, after the
existing phone gate, so it wins the cascade against the gate and the 920px-height density gate that
also fires at 412×915:

```
@media (max-width: 560px) and (orientation: portrait) { ... }
```

The existing gate string `(max-height: 560px), (max-width: 560px)` is NOT changed in either of its
two homes (`app.css:6747`, `usePhoneLayout.ts:16`); the pinned dock and its JS control keep working
in portrait exactly as today. Rules, by selector:

1. **Chrome back in document order.** `.topbar { order: 0 }`, `.statstrip { order: 0 }`,
   `.simulate .sim-topbar { order: 0 }`. This puts the masthead at the top (document y 12 instead
   of 1320–1794), the Simulate control cluster above the felt, and makes visual order match tab
   order. The 128px reserved bottom strip stays (the dock is still pinned on the felt route).
2. **Nav in flow.** `.nav-tabs { position: static; display: flex; flex-wrap: wrap; ... }` restoring
   the desktop row's look with the 44px `.nav-tab` floor kept; `.nav-reveal { display: none }`.
   The sheet's open/closed state in JS is untouched and simply has no effect in portrait.
3. **Wrapping.** `.statstrip { flex-wrap: wrap; overflow-x: visible }` (it clips 10px of itself at
   360 today with no scrollbar); `.sim-topbar { flex-wrap: wrap }`; `.sim-heading` allowed to wrap.
4. **Touch floor** on every control the measurement found under 44px: `.sim-speed-input` (and its
   label), `.sim-watch`, `.sim-leave-btn`, `.sim-replay-btn`, `.sim-reveal-btn`, `.theme-toggle`
   (and `.tt-opt`), `.btn.history-filter`, `.mode-chip` — `min-height: calc(var(--space-8) +
   var(--space-3))`, the same expression the gate already uses. Apply these under the EXISTING
   gate (both orientations), not only portrait: in landscape they sit below the felt and cost
   nothing, and a phone-wide floor is simpler than two. Widths may grow to fit; nothing else
   changes about them.
5. **History overflow.** `.history-hand-btn { flex-wrap: wrap }` and `.history-hand-tier { min-width:
   0 }` in portrait, so the row's intrinsic minimum (372px today, from `.history-hand-tier` at
   110px) fits 360. `.history-hand-ord` / `.history-hand-hero` keep their `--card-w` widths; the
   card token rebind is not widened (that would resize the History replayer's felt).
6. **Ledger and stats type floor.** In the portrait block, no body copy or number in `SimLedger`,
   `HistoryView` or `SimDashboard` renders below `--text-xs` (11px). `.sim-chips` (felt) and
   `.cell-label` (range grid) are out of scope and recorded.
7. **Rotate hint.** New pure module `frontend/src/components/simulate/rotateHint.ts` (+ test) with
   `shouldShowRotateHint({phone, portrait, atTable, dismissed})`, and a tiny hook
   `frontend/src/lib/useOrientation.ts` mirroring `usePhoneLayout.ts` for `(orientation: portrait)`.
   `SimulateView.tsx` renders, when the hook says portrait, the phone gate is on, a table is shown
   and the hint is not dismissed: `<p class="sim-rotate-hint" role="note">Turn your phone sideways
   for the table. <button type="button">Got it</button></p>` directly above the felt (in flow, so
   it takes space and scrolls with the page; never fixed). Dismissal is `sessionStorage`
   (`simulate.rotateHint`) with the same try/catch posture the other keys use, so it returns after
   the tab is closed but not on every hand. Styled in the portrait block with tokens; z-index not
   needed because it is in flow. The dismiss button meets the 44px floor.
8. **Practice and Quiz:** item 3's `.statstrip` wrap and item 4's `.mode-chip` floor are the whole
   change. Measured overflow on those pages is otherwise zero at all three widths.

## Out of scope

The felt in portrait (ring geometry, pod overlap, the chip badge, `.sim-chips` at 9px); any change
to the landscape gate's rules or the `PHONE_LAYOUT_QUERY` string; a settings screen; a z-index or
breakpoint token ramp; `App.tsx` (the nav and masthead changes are CSS-only); Practice/Quiz
page-specific layout; anything on the backend.

## Constraints (from the profile)

CSS values from tokens only (`--space-*`, `--text-*`, `--radius-*`; the 44px floor as
`calc(var(--space-8) + var(--space-3))`). Serif floor: `--font-display` never below `--text-base`.
Motion only inside `prefers-reduced-motion: no-preference`. AA contrast and a visible 3px focus
ring in both themes (the measurement found zero contrast failures; keep it that way). The
`noDescendingSpecificity` Biome baseline (18 hits) is not widened: new rules go at the file's end
and use selectors no more specific than the gate's. `app.css`, `SimulateView.tsx` and
`tokens.css` are single-owner: one worker owns all code in this slice. `App.tsx` untouched.
The 128px dock constant is written in three places; none of them changes.

## Golden paths

The existing phone gate block (`app.css:6747` onward) for how rules compose from tokens and how
the 44px floor is expressed; `usePhoneLayout.ts` for the orientation hook; `handCount.ts` +
`handCount.test.ts` for the pure module and its test; the P3a spec's measurement method for the
before/after evidence.

## Verify-by

`make check` green. Then a browser pass on the isolated stack at 412×915, 393×851 and 360×800,
both themes: (a) on the sit-down screen and in session the masthead's top edge is within the first
viewport and the first Tab press lands on a visible control; (b) `scrollWidth == innerWidth` on
sit-down, in-session, hand-over, History, dashboard, Practice, Quiz at all three widths (History at
360 was 12px over; stats strip clip gone: `scrollWidth <= clientWidth` on `.statstrip`); (c) every
control in item 4 measures ≥ 44px tall; (d) no text in the ledger, History or dashboard below 11px;
(e) the rotate hint appears above the felt in portrait only, dismisses, stays dismissed within the
tab, and does not appear at 915×412; (f) desktop 1280×800: masthead 1248×67 at (16,12), nav row
1248×43 at (16,87) spanning 789px, room grid `416px 416px`, `.sim-main` 864×813 and `.sim-side`
360×356 at x904, History section 1048×648 at (116,146), dashboard blocks at their recorded boxes —
all unchanged from the measurement's desktop baseline; (g) landscape 915×412 in session: dock
`y=351 h=61`, buttons `y=360 h=44` unchanged (the P4 browser run's figures).

## Definition of done

Done = every Verify-by leg passes AND `make check` exits clean AND nothing outside the ticket's
owned files changed AND the roadmap's P3 entry, the ledger, `log.md` and the Resume block are
updated in the same PR.
