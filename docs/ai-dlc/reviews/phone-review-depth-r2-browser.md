# Browser verification — phone review depth (round 2, independent checker)

VERDICT: PASS

All nine browser legs (a)–(i) of the spec's Verify-by pass on the built worktree stack
(frontend :7792, backend :8131, stylesheet freshness confirmed: the served `app.css` contains
`.sim-review`, `.sim-review-btn`, the six-selector 44px floor list and `.sim-recap-why { margin-left: 0 }`).
Method as the measurement: `getBoundingClientRect`, `getComputedStyle`, `document.activeElement`,
`window.scrollY`, `scrollWidth` vs `clientWidth`, headless Chromium at 915x412, 412x915, 360x800, 1280x800,
both themes. Resumed 9-max Training session, Grading = Coach; hands 528 and 529 played to showdown;
hand 529 carries a graded miss so the standing coach note is real, not substituted. No code was edited.
Leg (j) (`make check`, `rotateHint.test.ts`) is outside a browser pass and was not run here.

## Legs

| leg | verdict | numbers |
|---|---|---|
| (a) dock + Review | PASS | Dock 915x61 @y351. Order correct: `.sim-review-btn` "Review ↓" FIRST (x56), `.btn-primary` "Next hand →" second (x483.5). Heights 44/44 at 915, 168x44 at 412, 142x44 at 360. Tap Review: "Hand result" top = **16.0** (915), **16.0** (412), **15.8** (360); `document.activeElement` = `div.sim-review` (tabIndex −1); computed `outline-style: none`. Keyboard path: Tab lands on `.sim-review-btn` (ring solid 3px rgb(201,167,92) @2px offset, fully in view 360–404), Enter gives the same landing — `:focus-visible` matches **true** yet `outline-style` is still `none`, so the per-element opt-out works. Space on the wrapper: scrollY 344 → **608** (+264) and hand number **unchanged at 528**, dock still mounted. "Next hand →" click → hand **529**. Dock visible throughout (bottom == viewport height at all three sizes). Coach OFF: label still "Review ↓", target = settlement slip, top 15.8. "Hand complete" h2 at y34.8, `elementFromPoint` returns the heading itself; the dock is the only fixed overlay. |
| (b) History open/close | PASS | 360x800, list 126,615px / 1,966 rows, scrolled to **20,000**. Row "Replay hand 53, hero BB" at viewport y165.6 (336x79.5). Open: `.hrt-head` 336x63.7 @ **y0.1**; `.history-replay .stage` 336x170.2 @ **y174.8** (bottom 345, inside the 800 viewport); `activeElement` = `h2.hrt-title`. "← Back": scrollY **20000.00**, delta **0.00**, focus `button.history-hand-btn` aria-label "Replay hand 53, hero BB" back at **y165.6** — identical position. Esc (keyboard open, title ring solid 3px): scrollY **20000.00**, delta **0.00**, same row focused at y165.6. Landscape 915x412 with `.nav-tabs.nav-tabs-open` open over an open replayer: Esc closes the sheet only — `.hrt` still mounted, scrollY unchanged at 24. |
| (c) in-session replay | PASS (clamp recorded) | 915x412, saved scrollY **1774**: open puts `.hr-head` 891x44 @ **y0** (was −189), `activeElement` = `h2.hr-title`, document 2186 → 716. Back: **1755.5**, clamp **−18.5px**, focus `button.btn.sim-replay-btn`. Esc measured as an isolated single cycle (saved 1737): **1718.5**, clamp **−18.5px**, same focus. 412x915: head @y220.1, clamp **−18.5px**. 360x800: head @y105.1 (scroll at document maximum), clamp **0.0px**. Keyboard open rings `h2.hr-title` solid 3px rgb(201,167,92) @2px; mouse open leaves `outline-style: none`. |
| (d) rotate hint | PASS | 360x800: `p.sim-rotate-hint[role="note"]` 336x79 @ **y75.8**, parent `section.hrt.history-replay`, `previousElementSibling` = `header.hrt-head`, above `.stage` (y174.8), fully in the viewport with **no scrolling** right after open. Same nesting at 412x915. Absent at 915x412 in the History replayer, on Simulate and in the in-session replayer. "Got it" (68x44): hint removed, replayer stays mounted, `sessionStorage["simulate.rotateHint"] = "dismissed"`. Then `#/simulate` at 360x800 in the same tab: hint absent. |
| (e) 44px floor | PASS | Heights at 915x412 / 412x915 / 360x800 — `.sim-recap-explain-btn` 44/44/44 (was 24); `.hr-back` 44/44/44 (was 32); `.hrt-back` 44/44/44 (was 39); `.hr-step-btn` 44/44/44 (was 42); `.hrt-step-btn` 44/44/44 (was 42); `.hrt-move` 44/44/44 across 8 rows (was 24); `.sim-review-btn` 44/44/44. The hint's "Got it" is 68x44. |
| (f) coach note width | PASS (one caveat) | `.sim-recap-why` computed `margin-left` = **0px at 360** and **0px at 412**. At 360 the note measures **302.0px** border box / **300px** `clientWidth` in a 336px card; the text run is **288px** because `padding-left: 12px, padding-right: 0`. At 412: 354px of a 388px card. Before: 203px of 336. |
| (g) no h-overflow | PASS | `scrollWidth == clientWidth` on every named screen: Simulate at hand end 915/412/360; History list 915 (doc 104,940) / 412 (106,831) / 360 (126,615); History replayer 915/412/360; in-session replayer 915/412/360; Dashboard 915 (doc 1,657) / 412 (2,469) / 360 (2,530) — the Dashboard document heights are identical to the BEFORE measurement. |
| (h) desktop 1280x800 | PASS | `.sim-main` **864 wide @ (16, 211.5)**; `.sim-side` **360 @ x904**, docY 211.5 — both match the baseline strictly. No dock, no `.sim-review-btn`. `.sim-recap-why` keeps **margin-left 69.2px**. `.hr-step-btn` **104x42**, `.hr-back` 63.2x32 — the phone floor correctly does not reach desktop. `div.sim-review` computes `display:block, padding:0, border:0, margin:0, overflow:visible, scroll-margin-top:0px`, so it adds no desktop geometry. History `section.history` **1048 @ (116, 145.5)**. Dashboard `.dash-head` **462.2x82 @ (116,141.5)**, `.dash-kpis` **1048x223.7 @ (116,247.5)**, `.dash-streets` **1048x539.3 @ (116,495.2)**, `.dash-leaks` **1048x477.5 @ (116,1082.5)**. Document height 1,584 — identical to the baseline. Two baseline figures did not reproduce; both are explained under Issues, neither is a layout regression. |
| (i) console | PASS | Zero application errors and zero warnings across Simulate at hand end (both themes), both replayers, History list and replayer, Dashboard, at all four viewports. The only console lines in the whole session are `GET /favicon.ico 404` (pre-existing, unrelated to this slice) and React's DevTools info notice. |

## Contrast on the new and changed elements (both themes)

| element | NIGHT | LIGHT |
|---|---|---|
| `.sim-review-btn` text | **15.10:1** (rgb(243,239,226) on rgb(21,28,21)) | **13.52:1** (rgb(28,36,30) on rgb(244,236,218)) |
| `.sim-rotate-hint` text and its "Got it" | **16.07:1** | **15.24:1** |
| `.hrt-title` | 16.89:1 | 14.00:1 |
| `.hrt-back` / `.hrt-move` | 16.07:1 / 16.07:1 | 15.24:1 / 15.24:1 |
| `.hrt-step-btn` | passes | **5.49:1** (lowest measured anywhere) |
| `.sim-recap-explain-btn` | 8.07:1 | 5.03:1 |

Every new or changed element clears AA for body text in both themes. `.sim-nextdock .btn-primary`
reads 1.07:1 to a computed-style walk only because its plate is a gradient over
`background-color: transparent` — the same artifact the BEFORE measurement records for the card
glyphs. It is pre-existing and untouched by this slice.

Keyboard sweep at 360x800 on Simulate at hand end: 14 tab stops, every one at least 44px tall with a
visible ring (3px solid, except `.sim-recap-explain-btn` at 2px from its own rule at `app.css:3830`),
none off-screen, none obscured by the dock except the dock's own two buttons.

## Issues, ranked

1. **should-fix (documents, not code)** — two baseline numbers in the brief and the measurement do
   not reproduce, and a later reviewer will read them as regressions.
   `.dash-leaks` is quoted at **1048x92 @116,1082**; it measures **1048x477.5** at the same x and
   document y, rendering 6 leak cards, and 1082.5 + 477.5 reconciles with the 1,584px document height
   the same baseline records — 92px cannot. Separately, the measurement's §1 desktop row gives
   `.sim-recap-explain-btn` as **93x32**; it measures **92.8x24** on desktop, and `app.css:3812` sets no
   `min-height` at all, so 24 is the true unchanged desktop height (the same document's own "Defects,
   ranked" item 5 says 24). Fix: correct both figures in
   `docs/ai-dlc/reviews/phone-review-depth-measurement.md` §1 and §2.
2. **optional** — `.sim-recap-why` at 360x800: the spec asks for a text box "≥300px wide"; the element
   measures 302.0px (border box) and 300px (`clientWidth`), but the text actually runs in **288px**
   because the rule keeps `padding-left: 12px` with `padding-right: 0`. The leg passes on either
   conventional reading of "text box"; zeroing that 12px padding at the same breakpoint would buy the
   last 12px. Gain: ~2 more characters per line. Cost: the note loses its indent cue from the
   decision row above it, which is what the padding is there for — so leaving it is defensible.
3. **optional** — the in-session replayer's 18.5px scroll clamp (`SimulateView`'s "Your record"
   refetch, the spec's accepted residual) is **per cycle and cumulative**: measured 1774 → 1755.5 →
   1737 → 1718.5 over three consecutive open/close cycles at 915x412, a drift of 55.5px. One cycle is
   inside the spec's ≤20px allowance; a player who opens the replayer repeatedly walks up the page.
   Portrait 360x800 restores exactly (0.0px), so this is landscape-only.
4. **optional** — keyboard tab order at 360x800 reaches the bottom-pinned dock ("Review ↓" then
   "Next hand →", stops 6 and 7) **before** the recap content those buttons point at (Reveal and the
   four "Explain this" buttons, stops 8–13). This follows the dock's existing DOM position and is not
   introduced by this slice, but the new button makes the inversion twice as visible.
5. **optional** — the dock button's accessible name is the literal string "Review ↓"; the arrow glyph
   is not wrapped in `aria-hidden`, so a screen reader announces the character after the word. The
   sibling "Next hand →" has the same shape, so this is a consistency question, not a new defect.
6. **recorded, not tested** — two guarded paths were unreachable in a normal session and are
   unverified here: Esc yielding to `dialog[open]` (the hand-200 blind check), and the focus
   fallbacks to `h1.history-title` / Simulate's `h1` when the row or the replay button is not mounted.

## What was fine

- **The two defects this slice exists to fix are gone, measured.** The review card is now reachable in
  one tap with its top edge 16px from the viewport edge at every phone size (it used to start 268px
  below a 351px screen), and both replayers open with their header and felt on screen (`.hrt-head`
  y0.1 with the stage at y174.8, `.hr-head` y0 — previously −303 and −189).
- **Scroll restore on History is exact, not approximate.** 0.00px delta from scrollY 20,000 in a
  126,615px list, by both "← Back" and Esc, with focus landing on the same row button at the same
  viewport position it occupied before the open.
- **The focus-ring design decisions hold up under test.** The review wrapper genuinely suppresses its
  ring while still matching `:focus-visible`; both replayer headings genuinely paint a 3px ring after a
  keyboard open and stay bare after a mouse open. That is exactly the behaviour the spec argued for.
- **Every one of the seven named controls is at 44px at all three phone sizes**, and desktop keeps its
  old smaller heights — the gate is scoped correctly.
- **Desktop is unmoved.** `.sim-main` and `.sim-side` match the baseline boxes to the pixel, the wrapper
  `div` computes to no box at all, and the document height is the baseline's 1,584px. `.sim-recap`
  sits 127.3px higher than the baseline solely because this hand's showdown panel is 127.8px shorter
  (237.2 vs 365) — the two numbers reconcile, so nothing shifted.
- **Zero horizontal overflow and zero console noise** on every surface at every size, in both themes.

## Re-check after fan-in cleanups (legs a, d)

**Verdict: BLOCKED — neither leg verified. The dev server on :7792 is serving a stale
build, so the browser never executed the two changes under review.**

Evidence (all read in-browser at 915x412, NIGHT theme, after a full reload plus `touch`
of the source file):

1. Disk is new. `/private/tmp/claude-501/wt-rd/frontend/src/components/SimulateView.tsx`
   line 1645 is `<div className="sim-review" ref={reviewRef}>` — no standing `tabIndex` —
   and line 47 imports `./simulate/SimRotateHint`. `HistoryView.tsx` imports it too.
2. The served module is old. `GET /src/components/SimulateView.tsx` (bare URL, HTTP 200,
   208,746 bytes of transformed output) still contains
   `jsxDEV("div", { className: "sim-review", ref: reviewRef, tabIndex: -1, ...` and
   contains no reference to `SimRotateHint`.
3. The running app matches the old module, not disk. `div.sim-review` is inserted into the
   DOM already carrying `tabindex="-1"` (MutationObserver caught the node on mount with the
   attribute present), with `document.activeElement === body` and no Review click ever made.
   `SimRotateHint.tsx` appears nowhere in `performance.getEntriesByType('resource')`.
4. The stale transform will not invalidate. `touch` on the source at 13:38:15 changed the
   mtime but not the served bytes; `?t=<now>` and `/@fs/...` return the same stale 208,746
   bytes. Cache-busting queries return HTTP 500 (Vite error pages that embed the raw disk
   source — which is why an early probe looked fresh; that body was the error page, not a
   module). The file watcher is not firing for this `/private/tmp` worktree.
5. Console on `#/simulate`: one pre-existing `favicon.ico` 404. The only other errors were
   the two 500s my own cache-busting probes provoked.

Steps a(1)-a(6) and all of leg (d) were not exercised: measuring them here would grade the
pre-change code. Unblock by restarting the frontend dev server (clearing
`frontend/node_modules/.vite` first), then re-run both legs.

## Re-check after fan-in cleanups (legs a, d) — real run on :7793

**Supersedes the BLOCKED section above.** A fresh Vite process on :7793 serves the
post-cleanup code, so both legs were actually exercised. **Verdict: PASS, both legs.
Zero console errors and zero warnings across the whole session.**

Freshness confirmed first: `GET /src/components/SimulateView.tsx` on :7793 returns
`className: "sim-review", ref: reviewRef, children:` (no `tabIndex`), imports
`SimRotateHint`, and `SimRotateHint.tsx` appears in the page's loaded resources.

Leg (a) — PASS at 915x412 and at 360x800, NIGHT theme, Grading = Coach:
1. `div.sim-review` at rest: no `tabindex` attribute, both breakpoints, every hand.
2. Tab reaches "Review ↓" (3 stops after the grading toggle at 915x412); Enter puts the
   "Hand result" top edge at **16px** at both sizes, `document.activeElement` is
   `DIV.sim-review`, its `tabindex` is `"-1"`, computed `outline-style` is `none`.
3. Space with the wrapper focused scrolls and does not deal: 344→608px (915x412) and
   646→1298px (360x800), hand stayed 530 and 532 respectively.
4. Tab away: attribute gone — `hasAttribute("tabindex")` false at both sizes.
5. Plain click on the recap prose leaves focus on `body` with no `tabindex` on the
   wrapper, and Space then deals: 530→531 (915x412), 532→533 (360x800).
6. "Next hand →" still deals: 531→532 and 533→534.
7. Desktop 1280x800: click the recap prose, Space, hand 534→535.

Leg (d) — PASS at 412x915 portrait:
- History row tap: `p.sim-rotate-hint[role=note]` is a direct child of `section.hrt`,
  immediately after `header.hrt-head`, at top=76px in a 915px viewport (the replayer
  scrolls itself into view; no user scrolling needed). "Got it" is a 68x44px target.
- "Got it" removes the hint and writes `sessionStorage['simulate.rotateHint'] = "dismissed"`;
  `#/simulate` in the same tab then shows no hint.
- At 915x412, with sessionStorage cleared, no hint on either page — orientation gate holds.
- Cleared storage, back to 412x915: the Simulate hint returns, and its whitespace-normalised
  `outerHTML` is byte-identical to the History one (both 15px, same `role=note`).

No screenshots: the Playwright tool refuses paths outside the repo, and the brief forbids
writing into the checkout, so computed values above are the evidence.
