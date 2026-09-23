# Phone review-depth measurement — recap card, session stats, hand replayer

Method copied from `phone-p3b-portrait-measurement.md`: headless Chromium at stated CSS viewports,
numbers from `getBoundingClientRect` and `getComputedStyle`, against the worktree dev stack at
`http://localhost:7791/` (backend :8131, throwaway copy of the owner's database — 1,964 stored hands,
1,343 graded decisions). Two hands played to showdown in the resumed **9-max** Training session with
Grading set to Coach (the session in the database was 9-max; resuming was preferred to sitting down
fresh, so the felt numbers below are 9-max, not the 6-max of the previous measurement). NIGHT is the
default; LIGHT checked once per surface. Screenshots named per section live outside the repo in the
session scratchpad under `rd-shots/`. Zero console errors or warnings across the whole session.

## Bottom line

1. **Post-hand review card — readable, but invisible.** Nothing is clipped, nothing overflows, and
   contrast passes in both themes. The defect is placement: in landscape the card starts at document
   y**619** on a screen whose usable height is **351px**, so when a hand ends the phone shows felt and
   a "Next hand →" button and **no sign a review exists** (`s1-land-915x412-at-rest-no-recap.png`).
   Nothing auto-scrolls. The one worst defect on this surface.
2. **Session stats and leaks — usable as-is.** Dashboard has **zero** horizontal overflow at 915/412/360,
   zero text under 11px, zero targets under 44px, zero contrast failures over 82 text nodes in both
   themes, and the KPI cards stack. Worst thing here is height: **2,530px at 360×800 (3.2 screens)**.
   There is no by-street *table* — `.dash-streets` is a `<ul>` of bar rows, so the "does the table
   scroll sideways" question has no subject.
3. **Hand replayer — not usable as-is, both entry points.** Opening a hand from deep in History lands
   the viewport **303px past the felt**, i.e. on the move list, with the felt, the header and the step
   buttons all off-screen above (`s3-histreplay-deepopen-360x800.png`); closing returns you to y762 of
   a **126,448px** list, losing ~19,000px of scroll, with focus on `<body>`. The in-session "Replay last
   hand" does the same thing in landscape (head at viewport **-189**). The worst defect on this surface.

Every control the review surfaces add is below the 44px touch floor the phone gate applied to the
session's other controls: Explain-this **93×24**, replay Back **71×39**, step buttons **42px**, move
rows **24px**.

## 1 — Post-hand review card (`.sim-recap` + `.sim-showdown`)

| viewport | h-overflow | recap doc y / height | what is between felt and card | dock | card under dock? | smallest text | smallest target | console |
|---|---|---|---|---|---|---|---|---|
| 915×412 land | 0px | **619** / 681 | `.stage` 336 + `.sim-showdown` 371 | fixed `.decisionbar.sim-nextdock` 915×**61** at y351 | no (never; scroll-padding 128px) | 11px `.sim-recap-explain-btn` | 93×24 explain ×5 | 0 |
| 412×915 port | 0px | **1048** / 798 | topbar 185 + nav 138 + stage 217 + showdown 371 | fixed 61px at y854 | no | 11px | 93×24 ×5 | 0 |
| 360×800 port | 0px | **1049** / 857 | same, stage 192 | fixed 61px at y739 | no | 11px | 93×24 ×5 | 0 |
| 1280×800 desk | 0px | 1040 / 681 | stage 432 + showdown 365 | none (phone-only) | n/a | 11px | 92.8×**24** (corrected at fan-in; first written as 93×32) | 0 |

Geometry: `.sim-side` stacks **below** `.sim-main` at all three phone sizes (same 388/336 width, at doc
y1858 / y1917) and sits beside it on desktop (x904, 360 wide). Document height in session with a recap
open: 2,391px landscape, 2,813px at 412, 2,911px at 360, 1,745px desktop. Reading the card end to end
costs a scroll of **949px landscape** and **992px at 412**.

Showdown panel `.sim-showdown` is 371px tall at every phone size; its two Reveal buttons are 173×**44**
(412) and 164×44 (360) — on the floor, fine. `Replay last hand` is 115×44 but renders at document
y**2102** landscape / y**2553** at 412 / y**2651** at 360, because `.simulate .sim-topbar { order: 2 }`
(`app.css:6862`) keeps the session's control cluster below everything — including below the recap and
the side column — while portrait's own block deliberately leaves it there (`app.css:7164`). On desktop
the same button is at y153, beside the heading.

Coach prose width: `.sim-recap-why` keeps a desktop gutter of **margin-left 69.2px** (`app.css:3790`,
`calc(var(--card-w) * 1.1 + var(--space-3))`), so the standing coach note runs in **255px of a 388px
card** at 412 and **203px of 336px** at 360 — ~31 characters per line at 13px (`s1-recap-port-360x800.png`).
The on-demand explanation next to it does **not** have this problem: `app.css:4832` already zeroes
`.sim-recap-coach`'s indent below 640px for exactly this reason, and the expanded text measures 354px
wide. "Explain this" works on the phone: one tap swaps the label to "Explain again" and adds 322px of
prose, with no network dependency and no error state reached.

Accessibility: `section[aria-label="Decision recap"]` and `section[aria-label="Hand result"]` are real
landmarks; headings run H1 masthead, H1 page, H2 "Hand complete", H2 "Your decisions", H2 "Action",
H2 "Your record", H2 "Rail sheet" — **two H1s and no `<main>`** on Simulate (Dashboard has `main.dash`).
Focus ring is 3px solid at 2px offset; `html { scroll-padding-bottom: 128px }` (`app.css:6755`) keeps a
focused Explain button clear of the dock — measured not obscured at every position.

Contrast: 60 text nodes per theme, **zero** failures in LIGHT. The 16 NIGHT "failures" are all `.r`/`.s`
card glyphs and are a measurement artifact — the card face paints `linear-gradient(..., rgb(244,238,222) ...)`
with `background-color: transparent`, which a computed-style walk cannot see.

## 2 — Session stats and leaks (`#/dashboard`, `.sim-report`)

| viewport | h-overflow | doc height (screens) | KPI layout | by-street | smallest text | smallest target | contrast fails (night/day) |
|---|---|---|---|---|---|---|---|
| 915×412 land | 0px | 1,657 (4.0) | 2-up, 525 + 350 | `<ul>` of 4 bar rows, 539px | 11px | none <44 | 0 / 0 |
| 412×915 port | 0px | 2,469 (2.7) | stacked, 388×192 + 388×148 | 556px | 11px | none <44 | 0 / 0 |
| 360×800 port | 0px | 2,530 (3.2) | stacked, 336×192 + 336×148 | 595px | 11px | none <44 | 0 / 0 |
| 1280×800 desk | 0px | 1,584 (2.0) | 2-up, 619 + 413 | 539px | 11px | none <44 | 0 / 0 |

Largest type is `.dash-kpi-num` at **56px** ("97%") at every size — the hierarchy survives the phone.
`.dash-leaks` is 1,022px tall in portrait (5 leak cards at ~149px each); the last leak needs a scroll of
~1,730px at 360. `.dash-streets` is a `<ul class="dash-street-list">` of `.dash-street` rows, each with a
`.dash-bar` carrying `role="img"` and an aria-label ("Preflop: 97% good decisions") — it cannot scroll
sideways, wrap badly, or clip, and it does not. The only elements whose `scrollWidth` exceeds their
`clientWidth` are `.sim-sr-only` screen-reader spans, which is intended.

In-session `.sim-report` ("Your record"): 891×**95** landscape at doc y1545, 388×95 at 412 (doc y2049,
inside the stacked side column). Six text nodes, smallest 11px `.sim-report-rate-label`, biggest 22px
`.sim-report-rate-value`. No defect found.

## 3 — Hand replayer (History `HandReplayTable` `.hrt-*`, in-session `HandReplay` `.hr-*`)

### 3a — History list and its replayer

| viewport | h-overflow | list doc height | rows | row target | replay doc y | felt | step controls | on open focus | on close focus |
|---|---|---|---|---|---|---|---|---|---|
| 915×412 land | 0px | — | 1,964 | 49–80px tall | 24 | 891×314, **0 overlaps** | y**426**, below the 412 fold | `<body>` | `<body>`, scroll not restored |
| 412×915 port | 0px | — | 1,964 | 49–80 | 383 | 388×195, ring 338×161, **2 pairs / 96px²** step 1, **13 pairs / 9,755px²** last step | y665, above fold | `<body>` | `<body>` |
| 360×800 port | 0px (P3b's 12px is gone) | **126,448** (158 screens) | 1,964 | 49–80 | 383 | 336×170, ring 286×136, **8 pairs / 1,167px²** step 1, **13 pairs / 14,535px²** last step | y640, above fold | `<body>` | `<body>` |
| 1280×800 desk | 0px | 104,748 (131 screens) | 1,964 | 1048×49 | — | — | — | — | — |

The History list renders **every** hand: 7 day groups, the largest holding 1,050 rows. Nothing paginates,
virtualises or lazy-loads. Row targets and aria-labels are good ("Replay hand 51, hero UTG1, contains a
mistake"); the filter chip is 130×44 (`app.css:7190` region, P3b's floor).

Opening from deep in the list is the failure (`s3-histreplay-deepopen-360x800.png`): from scrollY 20,000
the document collapses 126,448 → 1,561, the browser clamps scroll to **762**, and the replayer's stage
lands at viewport **-303** — felt, hand header, Back and the step buttons all above the screen; the user
sees the "Moves" list. `← Back` then leaves scroll at 762 on the restored 126,448px list.
Esc does **not** close the replayer. Stepping works and keeps focus on the pressed button (1/20 → 2/20).

Felt readability at the river step, 360×800 (`s3-histreplay-felt-laststep-360.png`): pods sit on the
community cards (`board×tseat` 100×45 and 81×26), the pot line sits under two pods, and "COMMITTED 20.8"
overlaps the hero's hole cards — **13 pairs, 14,535px²** of overlap in a 336×170 stage, nothing clipped.
Landscape at 915×412 has **zero** overlaps in an 891×314 stage and is legible (`s3-histreplay-land-915x412.png`).
9px text on this surface: `.hrt-street-lbl` ×4, card `.r`/`.s` ×10, `.dealer` ×1.

### 3b — In-session "Replay last hand"

| viewport | h-overflow | replayer doc span | on open | Back | Prev/Next | street rail | doc height |
|---|---|---|---|---|---|---|---|
| 915×412 land | 0px | 24–383 | scroll clamps 1,690 → **213**, head at viewport **-189** | 63×**32** | 104×**42** | 4 × 220×24 spans | 702 |
| 412×915 port | 0px | 383–742 | whole component on one screen | 63×32 | 104×42 | 4 × 94×24 | 1,063 |
| 360×800 port | 0px | 383–742 | whole component on one screen | 63×32 | 104×42 | 4 × 81×24 | 1,063 |
| 1280×800 desk | 0px | 228–587 | one screen | 63×32 | 104×42 | 4 × 309×24 | 800 |

The landscape open is the defect and it is unavoidable in normal use: the button that opens the replayer
is at document y1,890, so the user must be scrolled ~1,690px down to tap it; mounting the replayer shrinks
the document to 702px and the browser clamps, leaving the hand header, the four-street playhead rail and
the board above the viewport (`s3-insession-replay-land-915x412-onopen.png`). Focus goes to `<body>` on
open and on close, both orientations. The fixed action dock is removed while the replayer is open.
`.hr-rail-seg` are `<span>`s, not buttons — the rail is a progress indicator, not a street jump, so walking
a hand costs up to **22 presses** of a 104×42 button. Landmarks here are good:
`section[aria-label="Replay of hand 527"]` and `group[aria-label="Step through the hand"]`.

## What is fine and should not be touched

- **Horizontal overflow is genuinely gone.** 0px at 915×412, 412×915 and 360×800 on every surface
  measured, including the History list P3b had scrolling 12px at 360.
- **Contrast in both themes.** Zero confirmed failures across 60 (recap) + 82 (dashboard) text nodes.
- **The focus ring and the dock.** 3px solid / 2px offset everywhere; `scroll-padding-bottom: 128px`
  keeps focused controls out from under the 61px dock — verified on the recap's Explain buttons.
- **Dashboard layout.** KPI stacking, the 56px KPI number, the bar-row by-street list, the 44px leak
  drill button (`app.css:4845`) and the 11px floor all hold at 360.
- **The landscape replay felt.** 891×314, zero pod overlaps — the wide orientation already works.
- **History row targets and labels.** 49–80px rows with descriptive aria-labels.
- **"Explain this" behaviour.** Instant, local, with a label that flips to "Explain again".

## Defects, ranked

1. **The recap is off-screen when the hand ends, and the only visible control skips it.** Landscape
   `.sim-recap` at doc y**619** vs a 351px usable viewport; portrait y**1048** vs 854. Nothing scrolls,
   nothing links. Dock `.decisionbar.sim-nextdock` (`app.css:6944`) shows only "Next hand →".
2. **Opening a replay lands you past the felt.** History from scrollY 20,000: stage at viewport **-303**
   (`.history-replay .stage`); in-session landscape: `.hr-head` at viewport **-189**. Document height
   collapses 126,448 → 1,561 (History) and 2,179 → 702 (in-session) and the browser clamps the scroll.
3. **Closing a replay discards your place in a 126,448px list.** `.hrt-back` returns to scrollY 762 with
   focus on `<body>`; the row that opened it is ~19,000px away. Esc does not close either replayer.
4. **History renders all 1,964 rows** — 126,448px at 360×800 (158 screens), 104,748px on desktop. No
   pagination, virtualisation or "load more"; only the `.history-filter` chip narrows it.
5. **Every review-surface control is under the 44px touch floor.** `.sim-recap-explain-btn` 93×**24**
   (`app.css:3812`), `.hrt-back` 71×**39** (`app.css:5494`), `.hrt-step-btn` **42px** (`app.css:5573`,
   `min-height: 32px`), `.hr-step-btn` **42px** (`app.css:5414`), `.hrt-move` rows **24px**
   (`app.css:5687`). The phone gate's floor list (`app.css:7039–7046`) names none of them.
6. **The replay felt is unreadable in portrait at the river.** `.history-replay .stage` 336×170 at 360:
   **13 overlapping pairs, 14,535px²**, including a pod 100×45 over the community cards; 9,755px² at 412.
7. **The standing coach note runs in a third of the card.** `.sim-recap-why` `margin-left: 69.2px`
   (`app.css:3790`) leaves **203px of 336** at 360 (~31 characters). `.sim-recap-coach` already has the
   fix one block away at `app.css:4832`.
8. **"Replay last hand" sits at the bottom of the page** — doc y2,102 landscape / y2,553 at 412 / y2,651
   at 360, under `.simulate .sim-topbar { order: 2 }` (`app.css:6862`, kept in portrait at `app.css:7164`).
9. *optional* — Simulate has **two H1s and no `<main>`** landmark (Dashboard has `main.dash`).
10. *optional* — the four-street rail is `<span>`s, so a 22-step hand needs 22 taps; `.hrt-move` rows are
    buttons that do jump, but at 24px.
