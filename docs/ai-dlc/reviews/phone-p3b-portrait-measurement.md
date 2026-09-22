# P3b portrait measurement — the non-felt pages on an Android phone

Method copied from `../specs/phone-chrome-p3a.md` ("What was measured"): headless Chromium at stated
CSS viewports, numbers read from `getBoundingClientRect` and `getComputedStyle`, against the worktree
dev stack at `http://localhost:7782/` (backend :8126, throwaway database). Ten hands played in a
Training 6-max session so History, Dashboard and the showdown state had real content. Both themes
checked for contrast; NIGHT is the default and all screenshots are NIGHT unless named `light`.

## Bottom line

**Portrait is not broken by width. It is broken by stacking order and by the felt.** Five of the
seven screens have zero horizontal overflow at all three portrait widths, so the 713px intrinsic
minimum the previous slice found is genuinely gone. What is wrong instead:

1. **The page chrome is at the bottom but first in the tab order.** `.topbar { order: 2 }` puts the
   brand, theme toggle and EV ledger at document y **1794** on the sit-down screen and y **1320** in
   session — **585–879px below the fold** on a 915px-tall viewport. DOM order is unchanged, so
   keyboard focus lands there *first*: three Tab presses scroll the page down 1203px and straight
   back to 0. One media query, `@media (max-height: 560px), (max-width: 560px)` at
   `frontend/src/styles/app.css:6747`, serves landscape and portrait with one rule set that was
   tuned for a 412px-tall landscape screen, where "one scroll down" was cheap. In portrait it is not.

2. **The 6-max felt collides with itself in portrait.** The ring is **338×161px** at 412 wide and
   **286×136px** at 360 wide. At showdown that produces **8 overlapping pairs totalling 10,690px²**
   at 412×915 and **11 pairs totalling 18,044px²** at 360×800, with the hero pod **clipped 11px** by
   `.stage` (`overflow: hidden`). The previous slice measured **0 overlaps** for the same 6-max table
   in landscape. The portrait felt is a different, much worse layout — including the P3a §6 chip-badge
   defect, which in portrait covers **52×20px + 43×11px** of the `.ctx` context line versus the
   7.7×13.5px measured in landscape.

3. **Touch targets and type fall below floor in the session chrome.** Ten controls are under 44px in
   session; the smallest is **45×26px** (the speed radios). Numbers on the felt render at **9px**
   (`.sim-chips`), as does the Practice range grid (`.cell-label`).

Three narrower defects: History scrolls sideways **12px at 360×800**; `.statstrip` silently clips
**10px** of itself at 360 with no way to scroll; and the fixed `.nav-reveal` button covers **65%** of
the EV-ledger figure on History at rest and sits **4px** from the primary "Raise" button in session.

Contrast is clean. Across 54–65 text nodes per screen in both themes, zero confirmed failures; the
two flagged nodes (`.new-tag`, `.tt-opt`) sit on a gradient and a pill that a computed-style read
cannot see. The focus ring is **3px solid at 2px offset** everywhere and is never obscured by the
fixed dock.

## A — Simulate sit-down / resume (no session)

| viewport | h-overflow | widest element | masthead h | nav wraps? | smallest tap target | body / number font | overlaps or clipping | console |
|---|---|---|---|---|---|---|---|---|
| 412×915 | 0px | none | 181px @doc y1794 | hidden (bottom sheet) | `.theme-toggle` 132×40 | 9px `.new-tag` / 13px `.smc-stamp` | none | 0 new |
| 393×851 | 0px | none | 181px | hidden | `.theme-toggle` 132×40 | 9px / 13px | none | 0 |
| 360×800 | 0px | none | 181px | hidden | `.theme-toggle` 132×40 | 9px / 13px | none | 0 |
| 1280×800 | 0px | none | **67px @doc y12** | 1 row, 789px of tabs | `.nav-tab` 65×43 | 9px / 13px | none | 0 |

Document height 2115px at 412 and 393 (**2.31 and 2.49 screens**), 2224px at 360 (2.78 screens),
1133px at 1280. The masthead is 181px in portrait against 67px on desktop — **2.7×**.

Nav sheet when opened: **412×157px, 3 rows, 17% of the viewport** at 412; **360×157px, 3 rows, 20%**
at 360. Every tab is 44px tall at 15px type. Escape closes it and `aria-expanded` returns to `false`.
The sheet has no backdrop and does not lock scroll, so it overlays two room-choice buttons that stay
clickable underneath.

## B — Felt mid-hand, 6-max Training, portrait (record-only, per brief)

| viewport | h-overflow | widest element | masthead h | nav wraps? | smallest tap target | body / number font | overlaps or clipping | console |
|---|---|---|---|---|---|---|---|---|
| 412×915 | 0px | none | 181px | hidden | `.sim-speed-input` 45×26 | 9px `.new-tag` / **9px `.sim-chips`** | 9 pod/board/ctx pairs, largest 40×25px; hero pod clipped 11px | 0 |

Geometry at 412×915: `.stage` **388×239px** starting at y8, `.sim-tablering` **338×161px**, dock
`.decisionbar.sim-actionbar` fixed **412×113px at y802**, action buttons 168×44px each. The gap
between the bottom of the felt and the top of the dock is **555px** of panel content — the felt uses
26% of the viewport height while 61% goes to panels that scroll.

`.ctx` is **338×40px at y17**, already two lines, and the CO pod's last-action badge covers
**52×20px** of it plus **43×11px** from `.sim-chips`. This is the P3a §6 defect, unfixed in portrait.

Where a rotate hint would go: there is only **8px** of headroom above `.stage`, and `.ctx` is already
collided, so the hint needs its own row as the first child of `.simulate`, above `.stage`. It would
cost roughly 28px out of the 555px of vertical slack below the felt — about 5% of the space that is
currently spent on panels.

## C — Hand-over / showdown, portrait

| viewport | h-overflow | widest element | masthead h | nav wraps? | smallest tap target | body / number font | overlaps or clipping | console |
|---|---|---|---|---|---|---|---|---|
| 412×915 fold-out | 0px | none | 181px | hidden | `.sim-speed-input` 45×26 | 9px / 9px `.sim-chips` | 9 pairs; hero pod clipped 11px | 0 |
| 412×915 showdown | 0px | none | 181px | hidden | `.sim-speed-input` 45×26 | 9px / 11px `.num` | **8 pairs, 10,690px² total**, largest 40×56px; 1 pod clipped 11px | 0 |
| 393×851 showdown | 0px | none | 181px | hidden | `.sim-speed-input` 45×26 | 9px / 11px | same mechanism | 0 |
| 360×800 showdown | 0px | none | 181px | hidden | `.sim-speed-input` 45×26 | 9px / 11px | **11 pairs, 18,044px² total**, largest 3,220px²; 1 pod clipped | 0 |

The hand-over dock is correct and needs no work: `.decisionbar.sim-nextdock` fixed **412×61px at
y854** with "Next hand →" at **344×44px**. That is P3a §1 and §2 delivered, and it holds in portrait.

Document height moves 1549 → 1711 → 1640px across a hand, but the dock is fixed so the controls do
not move.

## D — Session ledger / history

**Both exist.** The `History` tab (`#/history`) is the cross-session hand list; the in-session
"RAIL SHEET" panel (388×245px at document y751) is the per-hand ledger. The rail-sheet table does not
overflow at any portrait width (scrollWidth 354 = clientWidth 354 at 412).

| viewport | h-overflow | widest element | masthead h | nav wraps? | smallest tap target | body / number font | overlaps or clipping | console |
|---|---|---|---|---|---|---|---|---|
| 412×915 | 0px | none | 181px @doc y~740 | hidden | `.btn.history-filter` 124×32 | 9px / 11px `.history-filter-count` | `.nav-reveal` covers **65%** of `.elw-figure` "0.0" and 20% of `.elw-eyebrow` | 0 |
| 393×851 | 0px | `.history-hand-btn` fits exactly (scrollW 367 = clientW 367) | 181px | hidden | 124×32 | 9px / 11px | same | 0 |
| 360×800 | **12px** | `span.history-hand-tier` "NO BASELINE YET" **w=110, right edge 372** | 181px | hidden | 124×32 | 9px / 11px | `.statstrip` clips 10px | 0 |
| 1280×800 | 0px | none | **67px** | 1 row, 789px | `.nav-tab` 65×43 | 9px / 11px | none | 0 |

The 360 overflow is traceable: `.history-hand-btn` is a flex row with `min-width: 0` whose
scrollWidth is **359px against a 334px client width**, and the `.history-hand-tier` badge is the child
that escapes. The row's intrinsic minimum is **372px of viewport**, so 360-wide phones scroll
sideways and 393-wide phones clear it by 1px.

Document height 1060px at 412, 1100px at 393, 1120px at 360, 817px at 1280.

## E — Session stats and leaks

The Dashboard tab (`#/dashboard`) holds the all-time and per-street report; the in-session equivalents
are `.sim-report` ("YOUR RECORD", 388×95px at document y640) and the rail sheet.

| viewport | h-overflow | widest element | masthead h | nav wraps? | smallest tap target | body / number font | overlaps or clipping | console |
|---|---|---|---|---|---|---|---|---|
| 412×915 | 0px | none | 181px | hidden | `.theme-toggle` 132×40 | 9px / 15px `.dash-rate-v` | none | 0 |
| 393×851 | 0px | none | 181px | hidden | 132×40 | 9px / 15px | none | 0 |
| 360×800 | 0px | none | 181px | hidden | 132×40 | 9px / 15px | `.statstrip` clips 10px | 0 |
| 1280×800 | 0px | none | **67px** | 1 row, 789px | `.nav-tab` 65×43 | 9px / 15px | none | 0 |

Document height 1570px at 412, 1593px at 393 and 360, 1198px at 1280. Type hierarchy here is the
strongest in the app (56px headline figure against 11px labels) and survives portrait unchanged.

## F — Settings-like controls

**There is no settings page.** The controls are split across three places:

- **In-session, `.sim-topbar`** — 388×284px at document **y1012**, carried by
  `.simulate .sim-topbar { order: 2 }` to sit below the felt and below every panel. Contents and
  measured sizes at 412×915: `.sim-speed-input` **45×26 / 60×26 / 63×26** (Normal/Fast/Instant),
  `.sim-watch` Watch **66×36**, `.sim-watch` Grading **127×36**, `.btn.sim-leave-btn` Leave table
  **88×32**, `.btn.sim-replay-btn` Replay last hand **115×32**, `.btn.sim-reveal-btn` **173×38**.
- **Masthead** — `.theme-toggle` **132×40**, at document y1320–1500 in session.
- **Nav sheet** — mode/section switching only.

**Every one of these eight controls is below the 44px touch floor in its short dimension**, and the
tallest is 40px. Reaching them requires scrolling 585px past the end of the content.

## G — Practice and the quizzes (overflow only, per brief)

Measured at 360×800, the worst case; all are 0px at 393 and 412 as well.

| screen | route | h-overflow | smallest tap target | smallest number font | clipping |
|---|---|---|---|---|---|
| Practice | `#/drill/random` | 0px | `.btn` "TEST" **66×26** | **9px** `.cell-label` | `.statstrip` 344>334 |
| Texture quiz | `#/texture` | 0px | `.theme-toggle` 132×40 | 22px | `.statstrip` 344>334 |
| Equity quiz | `#/equity` | 0px | `.input` 120×40 | 11px `.grp-count` | `.statstrip` 344>334 |
| Learn | `#/home` | 0px | `.btn` 158×42 | 22px | `.statstrip` 344>334 |

Practice has **11 controls under 44px**, the most of any screen.

`.statstrip` is the one clipping defect shared by every screen: `flex-wrap: nowrap` with
`overflow-x: hidden`, scrollWidth **386 = clientWidth 386 at 412**, **368 vs 367 at 393**, and
**344 vs 334 at 360**. At 360 the last child (`.leaks`, "TOP LEAKS / none yet", 77px) loses 10px off
its right edge with no scrollbar and no wrap. Its intrinsic minimum is roughly a **370px** viewport,
and real leak text will make the shortfall larger than 10px.

## Desktop baseline at 1280×800 (for the pixel-identical gate)

Zero fixed or sticky elements; `.nav-reveal` is `display: none`; masthead `order: 0`.

| screen | masthead | nav row | main content columns |
|---|---|---|---|
| A sit-down | 1248×67 @16,12 | 1248×43 @16,87, 1 row, tabs span 789px | `SECTION.simulate` 1248×967 @16,142; room grid 864×702 @x16 with `grid-template-columns: 416px 416px`; four cards 416×322 / 416×322 / 416×348 / 416×348 at x16 and x464; `aside` 360×95 @904,188 |
| A in-session | 1248×67 @16,12 | 1248×43 @16,87 | `DIV.sim-main` 864×813 @16,212; `ASIDE.sim-side` 360×356 @904,212 |
| D history | 1048×67 @116,12 | 1048×43 @116,87, 1 row, 789px | `SECTION.history` 1048×648 @116,146 |
| E dashboard | 1048×67 @116,12 | 1048×43 @116,87, 1 row, 789px | `.dash-head` 462×82 @116,142; `.dash-kpis` 1048×224 @116,248; `.dash-streets` 1048×539 @116,495; `.dash-leaks` 1048×92 @116,1082 |

Document heights: 1133px (A sit-down), 1048px (A in-session), 817px (D), 1198px (E).

## Console

**4 errors, one kind:** `GET /api/v1/simulate/session/current` returns **404** when no session exists.
It fires twice on a cold load (React StrictMode double-effect) and twice again after "Leave table".
This is the no-session path surfacing as an error rather than an empty result. Not a portrait defect,
but it is noise in every phone session that starts without a table.

## Where a portrait breakpoint must act

Named by selector, with the source line where each currently lives.

1. **`@media (max-height: 560px), (max-width: 560px)` — `frontend/src/styles/app.css:6747`.** The
   root cause. One block serves landscape (the `max-height` arm) and portrait (the `max-width` arm),
   and every rule inside it was sized for a 412px-tall screen. A portrait slice has to split this
   into two queries before touching anything else.
2. **`.topbar { order: 2 }` — `app.css:6771`.** Moves 181px of chrome to document y1320–1794 in
   portrait while leaving it first in the tab order.
3. **`.statstrip { order: 3 }` — `app.css:6776`**, plus `.statstrip`'s own `flex-wrap: nowrap` and
   `overflow-x: hidden`, which clip 10px at 360.
4. **`.simulate .sim-topbar { order: 2 }` — `app.css:6862`.** Puts speed, Watch, Grading, Replay and
   Leave at document y1012, below every panel.
5. **`.nav-reveal` — `app.css:6829`.** Fixed at `inset-inline-start: var(--space-2); bottom:
   var(--space-2)`, which is 4px from the "Raise" button in session and on top of `.elw-figure` on
   History.
6. **`.simulate .stage` / `.sim-tablering` and the `--card-w-phone` rebinding — `app.css:6876-6899`.**
   The source of the 338×161px ring and every felt overlap above.
7. **`.ctx` against `.sim-last-action` and `.sim-chips`.** The P3a §6 badge collision, 52×20px in
   portrait.
8. **`.history-hand-btn` / `.history-hand-tier`.** The only true horizontal overflow, 12px at 360.
9. **Touch floor: `.sim-speed-input`, `.sim-watch`, `.sim-leave-btn`, `.sim-replay-btn`,
   `.sim-reveal-btn`, `.theme-toggle`, `.btn.history-filter`, `.mode-chip`.** All 26–40px tall.
10. **Type floor: `.sim-chips` and `.cell-label` at 9px**, `.new-tag` at 9px. `.nav-tab` already
    carries a 15px serif floor at `app.css:6823` — the same floor is what these need.
