# Design review r2 — P3b portrait pass (design-reviewer with Playwright, Opus, 2026-09-22)

Returned inline (review-only agent) and saved verbatim by the Director. Run against a fresh
isolated stack from the worktree on :8127/:7783 serving the uncommitted diff; the owner's stack on
8008/7777 was never touched. Screenshots under `$TMPDIR/p3b-shots/`, none in the repo.

VERDICT: FAIL — one blocking leg. Everything else passes, several with exact-to-the-pixel agreement.

1. **blocking** — `.statstrip` still clips itself, worse than before, on Practice / Texture quiz / Equity quiz / Learn in portrait. Leg (b) requires `.statstrip` `scrollWidth <= clientWidth`. Observed 419 vs 386 (412 wide, 33px over), 419 vs 367 (393, 52px), 419 vs 334 (360, 85px). The third leak chip "FLOP_CBET 100%" is cut off with no scrollbar and no way to reach it (`overflow: hidden`), and the card's right rounded corner is broken. Cause: spec item 3 wraps `.statstrip` itself, but the overflowing child is `.lk-row` inside `.leaks`, which is still `flex-wrap: nowrap` — the four stat cells wrap and the leak row does not. The earlier sweep passed only because the database then had "none yet" for leaks; the measurement report (line 161) predicted exactly this. Fix, verified live in the browser: `.statstrip .lk-row { flex-wrap: wrap }` in the portrait block → 334/334 at 360. Gain: leg (b) passes with real data. Cost: the strip grows one 27px row on Practice at 360.
2. **should-fix** — portrait tab order jumps 532px down, then back up: after the 7 nav tabs, tab 9 lands on `.sim-watch` at document y1187 (auto-scrolls 532px); tab 15 returns to the rotate hint at y375. Leg (a) only asks about the first Tab, which passes, so this is inside the ruling's stated cost — but it is a WCAG 2.4.3 focus-order mismatch and should be recorded.
3. **optional** — the sit-down Simulate screen keeps 128px of dead space: `.app` padding-bottom is 128px there with nothing pinned; `:has(.simulate)` matches the route, not the dock. Other routes correctly read 0px.
4. **optional** — the hint's "Got it" button has no visible boundary contrast: its background equals the hint's (`--surface`); the only edge is `--border` at 1.63:1 dark / 1.62:1 light, under WCAG 1.4.11's 3:1. Text contrast is fine (16.07:1 / 15.24:1). Pre-existing token pattern in a new context.
5. **optional** — the hint is 79px tall at 360, not the spec's budgeted ~28px ("Got it" wraps to its own line). Leg (b2) still clears by only 16px.
6. **optional** — `.nav-tab` keeps the gate's `margin-bottom: 0` in portrait (base is `-1px`), so the active tab's brass underline no longer sits on the rail hairline. Invisible in practice because the row wraps to three lines.

| Leg | Result | Measured |
|---|---|---|
| (a) masthead in first viewport; first Tab visible | PASS | masthead top 8px on sit-down and in session at 412/393/360; first Tab = `.theme-toggle`, top 66, bottom 110, scrollY 0 |
| (b) `documentElement.scrollWidth <= clientWidth`, 7 screens × 3 widths | PASS | 21/21 equal, incl. hand-over; zero elements past the viewport edge |
| (b) `.statstrip scrollWidth <= clientWidth` | FAIL | 419 vs 386 / 367 / 334 on Practice, Texture, Equity, Learn |
| (b2) `.stage` bottom ≤ dock top @360×800 | PASS | stage bottom 671, dock top 687 |
| (c) eight controls ≥ 44px; Night/Day not clipped | PASS | speed faces 45/60/63×44; Watch 66×44, Grading 127×44; Leave 88×44; Replay 115×44; Reveal 173×44 ×2; theme 132×44; history-filter 124×44; 8 mode-chips ×44. `.tt-opt` 65×15 inside a 132×40 track, 12.8px clear |
| (d) no text < 11px in ledger / History / dashboard | PASS | 0 nodes under 11px at 360 and 412, both themes |
| (e) rotate hint | PASS | portrait in-session only: 388×54 @412, 336×79 @360, above `.stage`; `role="note"`; dismiss 68×44; sets `sessionStorage simulate.rotateHint="dismissed"`; absent after `#/history` → `#/simulate`, at 915×412, at 1280×800, and on sit-down |
| (f) desktop 1280×800 pixel identity | PASS | masthead 1248×67 @16,12; nav 1248×43 @16,87, tabs span 789; `section.simulate` 1248×967 @16,142; `.smc-rooms` `416px 416px` 864×702 @16,364; cards 416×322/322/348/348 at x16/x464; aside 360×95 @904,188; docH 1133; `.sim-main` x16 y212 w864, `.sim-side` 360 @904,212; History 1048 @116,146; `.dash-head` 462×82 @116,142, `.dash-kpis` 1048×224 @116,248, `.dash-streets` 1048×539 @116,495, `.dash-leaks` 1048×92 @116,1082, docH 1198. Zero boxes differ. At 1280 `theme-toggle min-height: auto`, `.app padding-bottom: 24px`, `.nav-tabs` static/nowrap: no new rule reaches desktop |
| (g) landscape 915×412 in session | PASS | dock y=351 h=61, buttons y=360 h=44 (hand-over and mid-hand); hint absent; `.nav-tabs` fixed, `.nav-reveal` flex, `.topbar` order 2 |
| (h) landscape Practice | PASS (no regression) | `.mode-chip` 27px unchanged; `.decisionbar` top 464 with and without the slice — delta 0. Its bottom (514) exceeds 412 identically pre- and post-slice: a pre-existing P3a condition |
| Console | PASS | only the designed `GET /session/current` 404 on boot |
| Focus ring | PASS | 3px solid, 2px offset, both themes, on nav tabs and the hint button; 27/27 in-session controls unobscured |
| `.app` padding-bottom (portrait, non-felt) | PASS | 0px on History, Dashboard, Practice, Texture, Equity, Learn; 128px retained on Simulate |
| Floating reveal button in portrait | PASS | `.nav-reveal` `display: none` at all widths, not tabbable; nav in flow, 3 rows |
| Contrast (both themes) | PASS | hint text 16.07:1 dark / 15.24:1 light; nav tab inactive 8.79 / 5.49; active 16.89 |

The reviewer started and stopped no server and edited no repository file.
