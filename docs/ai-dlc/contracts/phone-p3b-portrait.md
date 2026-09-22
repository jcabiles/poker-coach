# Contract map — P3b, phone polish for the non-felt pages (portrait)

Scanned 2026-09-22 by a read-only contract-mapper (Opus) on the worktree at `eb7a576` (P4 head).
Line numbers are as of that commit. Companion: the portrait measurement in
`../reviews/phone-p3b-portrait-measurement.md`.

## Bottom line

- The portrait pass is almost entirely an `app.css` job and cannot be split across two parallel
  workers: every screen plus the shell breakpoint lands in that one file, and `App.tsx` needs at
  most one small addition (the rotate hint). There are exactly two stylesheets, `app.css` (7017
  lines) and `tokens.css`; no per-component CSS exists.
- The existing phone gate `(max-height: 560px), (max-width: 560px)` DOES fire at 412×915 through
  its max-width leg, and it already takes `.nav-tabs` out of flow, so the measured 713px minimum
  width is largely defused. P3b's real job is to verify that with numbers and catch what is left.
- There is NO settings screen: speed, Watch, Coach/Real and Labels live in the Simulate topbar
  control cluster, theme in the masthead, Study/Test on Practice only, and mode is immutable after
  sit-down (rendered as a stamp, never a control).
- Nothing automated guards layout: no jsdom, no testing library, no CSS assertion. The only guard
  is the headless-Chromium measurement method from the P3a spec, which is prose, not a script.

## 1. App shell — width and the gate

`PHONE_LAYOUT_QUERY` (`frontend/src/lib/usePhoneLayout.ts:16`) and the CSS gate (`app.css:6747`)
are the same string, duplicated on purpose, with no enforcement; both files name each other
(`usePhoneLayout.ts:3-16`, `app.css:6724-6746`). The dock rendered by JS (`SimulateView.tsx:1052`,
`:1482`) depends on the two halves matching. Under the gate: `.app` becomes a column flex with a
reserved bottom strip `calc(var(--space-8) * 4)` = 128px (`app.css:6762-6770`), a constant repeated
as `html { scroll-padding-bottom }` (`:6755`) and the stale notice's `bottom` (`:6973`);
`.topbar { order: 2 }`, `.statstrip { order: 3 }` (`:6771-6778`); `.masthead-right`,
`.sim-topbar-controls`, `.sim-speed-opts` wrap with `min-width: 0` (`:6784-6789`); `.nav-tabs` is a
fixed bottom sheet, hidden when closed (`:6797-6818`), `.nav-tab` has a 44px floor (`:6819-6824`),
`.nav-reveal` is a 44×44 fixed control (`:6829-6853`).

Remaining width pressure in portrait:

| Construct | Location | Why it bites |
|---|---|---|
| `.statstrip { flex-wrap: nowrap }` + `.stat span { white-space: nowrap }` | `app.css:1474-1513` | The one remaining nowrap flex row in the shell; rendered on Practice/Quiz/Learn only (`App.tsx:428-430`). The concrete Practice/Quiz no-overflow target. |
| `.tt-track { width: 132px }` | `app.css:93-105` | Fixed width in the masthead theme toggle; `.brand` does not wrap (`:20-24`). |
| `.elw-meter { width: 132px }` | `app.css:2013-2018` | Fixed width inside the EV ledger widget. |
| `.sim-topbar` has no `flex-wrap` | `app.css:2664-2673` | Heading (`.sim-heading`, `:2674-2684`, baseline row) and controls share one non-wrapping row; only the controls child gets `min-width: 0`. The likeliest remaining overflow on the Simulate route. |
| `.grid { repeat(13, 1fr) }` + `.cell { aspect-ratio: 1 }` | `app.css:1225-1242` | Shrinks (~28px cells at 412) with 9px glyphs: legibility, not overflow. |

At 412×915 the width gates 1100 (`:3394`, `:4008`, `:5532`, `:5620`), 720 (`:6053`, `:6524`), 640
(`:4825`), 480 (`:587`) and the height gate 920 (`:2602`, `:3422`; 915 < 920) ALL fire together.
The phone gate wins only because it is last in the file (`app.css:6746`); portrait rules must go
at the end or lose the cascade.

## 2. The four Simulate screens

- **Sit-down / resume:** `SimModeChoice.tsx`, mounted at `SimulateView.tsx:1566-1577` in
  `.sim-empty-shell` (grid `minmax(0,1fr) var(--sidebar-w)`, collapsing at 1100, `app.css:3999-4012`).
  CSS `:5811-6061`; four room cards in two columns (`:5831-5836`) already one column at 720
  (`:6053-6061`). Contract: `Room.spokenName` keeps `name` and `cta` verbatim (WCAG 2.5.3,
  `SimModeChoice.tsx:41-47`). Resume branch: `.simulate-empty` "Restoring your table…"
  (`SimulateView.tsx:1578-1592`).
- **Ledger / history — two things:** the per-session rail sheet `SimLedger.tsx` (3-column table,
  `:57-93`; CSS `app.css:3239-3298`; `.sim-led-seat { width: calc(var(--card-w) * 0.9) }` at
  `:3272-3277`, and `--card-w` is NOT rebound outside `.simulate .stage`), rendered in `.sim-side`
  (`SimulateView.tsx:1559`); and the cross-session register `HistoryView.tsx` (CSS `:4898-5150`)
  whose rows carry `min-width`s from `--card-w`: `.history-hand-ord` 78px (`:5042-5048`),
  `.history-hand-hero` 47px (`:5064-5070`). Its replayer opts into the felt density via
  `.app:has(.history-replay)` (`:3410-3413`, and paired gate selectors at `:6877-6927`).
- **Stats and leaks:** `SimDashboard.tsx`, CSS `:4426-4850`; `.dash-kpis` `3fr 2fr` (`:4471-4476`)
  already single-column at 640 (`:4825-4829`); leak rows stack with a 44px target at 640
  (`:4835-4849`). In-session sibling `SimStreetReport` (`:4857-4896`).
- **Hand over / showdown:** `SimShowdown` + `SimRecap`, gated on `hand.hand_over && revealHandEnd`
  (`SimulateView.tsx:1529-1547`); `revealHandEnd = !playing` (`:1045`) — nothing on screen may lead
  the event log. Under the gate `.sim-nextdock` is the fixed dock (`app.css:6943-6961`), rendered
  only when `phone` is true (`SimulateView.tsx:1482`), topbar copy suppressed by `!phone` (`:1254`).

## 3. "Settings" — the controls and their contracts

| Control | Rendered | Persistence |
|---|---|---|
| Theme | masthead, `App.tsx:358-372` | `localStorage "theme"` (`App.tsx:65-82`); pre-paint snippet in `index.html` |
| Speed | `SimSpeedPicker`, `SimulateView.tsx:1288` | `"simulate.speed"` (`:62`, `:133-141`) |
| Watch folded hands | `SimWatchToggle`, `:1277` | `"simulate.watch"` (`:63`, `:146-152`) |
| Coach vs Real | `SimGradingToggle`, `:1278` | `"simulate.coachMode"` (`:64`, `:158-164`) |
| Labels | `SimLabelsToggle`, `:1282-1287`, conditional (Challenge after unlock, `:882`) | per-session key (`:85-105`) |
| Study vs Test | `StudyTestToggle`, `App.tsx:451`, Practice only | `"studyTestMode"` |
| Mode + table size | `SimModeChoice` only; immutable; topbar stamp is "never a control" (`:1202-1208`) | server |

Speed and Watch are mirrored into refs read by the playback timer and the fold branch
(`SimulateView.tsx:245`, `:260`; a mid-playout Watch flip affects only the next fold, `:256-258`);
`coachMode` has no ref because it only gates render (`:271-274`). Every writer swallows a
`localStorage` failure with a stated reason.

## 4. Practice and Quiz — the "do not break" surface

Practice is inline in `App.tsx:435-473`: `.mode-groups` chip rows (`app.css:1373-1420`),
`StudyTestToggle`, then `.layout` grid `1fr var(--sidebar-w)` collapsing at 820 (`:191-201`) with
`PokerTable` + `DecisionBar` + `RangeGrid`. Widest: the 13×13 `.grid` (`:1225-1242`, also in
`SimRangeChart`, `:4372`); `.statstrip` nowrap (`:1477`, shell-level); `.tablering` with inline
percentage pods (`:270-281`) — Practice does NOT get the phone card rebind (scoped to
`.simulate .stage, .history-replay .stage`, `:6876-6880`). Quiz: `.quizpanel { max-width: 55rem }`
(`:1657-1660`), `.answer-btn { min-width: 8.75rem }` (`:1813`) in a wrapping row (`:1805-1807`), a
`width: 120px` equity input (`:1878`). `.decisionbar`, `.stage`, `.felt`, `.tablering`, `.tseat`,
`.card` are shared with Practice and Quiz (P3a spec `:129-131`): base-class edits bleed app-wide.

## 5. Tokens

`tokens.css`: space 4/8/12/16/24/32 (`--space-1..8`, `:98-104`); type 9/11/12/13/15/20/22
(`--text-2xs..xl`, `:89-95`) with the serif floor: `--font-display` never below `--text-base`
(`:81-82`, `app.css:6823`, `:7002-7005`); radius 2/4/8/10/999 (`:107-112`); layout
`--content-width` 1080, `--content-width-wide` 1360, `--sidebar-w` 360, `--card-w/h` 52/72,
`--card-w-phone/--card-h-phone` 40/56 (`:114-127`); motion `--dur-1/2`, `--ease-1` (`:138-144`)
inside `prefers-reduced-motion: no-preference` only. No z-index ramp and no breakpoint token: the
gate hard-codes z 30 (nav sheet), 40 (reveal), 20 (dock), 21 (stale notice), 22 (shove warning).
The gate introduced no raw px; the 44px floor is `calc(var(--space-8) + var(--space-3))`; the one
pre-existing raw `min-height: 44px` is at `app.css:4845`.

## 6. Tests and checks

Nine vitest files, all pure logic; no CSS or position assertion. Biome lints CSS with
`style.noDescendingSpecificity` baselined at `warn` (18 hits, `BASELINE(2026-09-18)`,
`biome.jsonc:41-42`); rules added near the end of the file can add hits without failing the gate
and must not widen the baseline. The P3a measurement method is prose only (`phone-chrome-p3a.md:28`,
`:149-156`); its verify-by item 9 (portrait 412: no horizontal scroll) has no recorded figure in
the ledger. Treat the portrait pass as unverified until measured.

## 7. Ownership

Cannot be split without two owners of `app.css`. Options: one owner in sequential passes (no
conflicts, costs wall-clock) or a stylesheet split (a larger, riskier change than P3b). The only
separable piece is the rotate hint's markup and dismissal state, a handful of TSX lines that still
need a CSS rule.

## Risks the plan must handle

1. The JS and CSS halves of the phone gate can desynchronise; do not add a second, different
   app-shell breakpoint string. Portrait rules nest under the existing gate, or under
   `(orientation: portrait)` inside it.
2. The 128px dock constant lives in three places untokenised; a change to `.app` padding must
   change all three or the fixed notice detaches from the dock (WCAG 2.4.11).
3. At 412×915 the 920-height density gate also fires; new rules go at the end of the file.
4. `--card-w` is rebound only on two stages; widening it to cure History's row widths resizes the
   replayer's felt and breaks its pixel-identity promise (`app.css:3407-3413`).
5. Building a settings screen would touch `SimulateView.tsx` (1615 lines) and `App.tsx` and must
   preserve the ref-mirroring on speed and watch, the conditional Labels mount, and mode-as-stamp.
6. `.sim-topbar` does not wrap and sits below the felt under the gate; likeliest remaining
   overflow, and where "settings" live.
7. The rotate hint needs a z-index in the undocumented 20/21/22/30/40 stack; it must not paint over
   the dock, the notice, the shove warning or the nav sheet.
8. Desktop pixel-identity at 1280px has no automated check; a `.statstrip` or `.topbar` change for
   portrait can regress it unnoticed. Capture before/after by hand.
