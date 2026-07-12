# Tickets — Simulate table size + crowding fix (wave 4.5)

> Spec: `docs/ai-dlc/specs/simulate-table-size.md` · Contracts:
> `docs/ai-dlc/contracts/simulate-table-size.md`. STRICTLY SEQUENTIAL — all four
> tickets share `app.css`/`SimTable.tsx` and the tuning loop is iterative; one
> agent owns the whole slice. S10 starts only after this merges.

## T1 — Widen the Simulate shell
Add `--content-width-wide: 1360px` to `tokens.css` and a sim-scoped
`.app:has(.simulate) { max-width: var(--content-width-wide) }` rule appended to the
`.sim-*` block in `app.css` (fallback = `app--wide` class in `App.tsx`, ask-first).
- Owns: `frontend/src/styles/tokens.css` (hotspot), `frontend/src/styles/app.css` (hotspot).
- Accept: Simulate route `.app` computed max-width 1360px; Home/Practice/Quiz stay 1080px.
- Done-condition: `npm run typecheck && npm run build` clean + Playwright
  `getComputedStyle(document.querySelector('.app')).maxWidth === '1360px'` on
  `#/simulate`, `'1080px'` on `#/practice`.

## T2 — Raise the sim ring + short-viewport companion (needs T1)
New scoped rules in `app.css`: `.simulate .tablering { max-height: calc(var(--card-h) * 5) }`
PLUS `.simulate .tablering { max-height: calc(var(--card-h) * 4) }` inside the
EXISTING `@media (max-height: 920px)` gate (refuter high-1 — the scoped rule
otherwise beats the density gate at all heights). Clearance nudges for
`.sim-chips`/pot/hero-card spacing as needed. No shared base-rule edits.
- Owns: `frontend/src/styles/app.css`.
- Accept: ring ~360px tall at 1440×900; ≤288px when viewport height ≤920px
  (1024×768 check); felt + action console fit 1440×900 without vertical scroll.
- Done-condition: Playwright bounding boxes at 1440×900 and 1024×768 confirm both
  caps; build clean.

## T3 — Spread the seat ellipse + live overlap tuning (needs T2)
Adjust `slotStyle` radii in `SimTable.tsx` (43%/38% → tuned, guide ≤~45%/41% —
refuter high-2: `.stage overflow:hidden` clips beyond that) and iterate with
Playwright measurement until zero overlap AND full containment.
- Owns: `frontend/src/components/simulate/SimTable.tsx`.
- Accept: at 1440×900, 1280×800, 1024×768 on a 9-max showdown state: zero
  bounding-box intersection among board/pot/seat pods/chip pucks/hero cards; every
  pod box fully inside `.tablering`.
- Done-condition: scripted Playwright evaluate returns `{overlaps: [], clipped: []}`
  at all three sizes; typecheck clean.

## T4 — No-bleed proof + design review + doc sync (needs T3)
Screenshot Practice + both quizzes both themes (byte-identical felt vs. pre-change),
full-page Simulate both themes, run `design-reviewer`, then update docs: mark this
slice in `roadmap/simulate-table.md`, re-base `specs/simulate-s10.md`/`simulate-s11.md`/
`contracts/simulate-s10-s11.md` line refs + ring-geometry assumptions (refuter med-2).
- Owns: `docs/ai-dlc/**` (this slice's docs), screenshots only — no code.
- Accept: no shared-class bleed; design-reviewer verdict acceptable both themes;
  `./scripts/verify.sh` green.
- Done-condition: design-reviewer `{verdict}` ≠ fail; verify.sh prints
  `BACKEND VERIFY OK`; docs updated in same PR.

Parallelizable: none (shared files, iterative tuning).
