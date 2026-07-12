# Spec — Simulate table size + crowding fix

> Standalone fix slice of `docs/ai-dlc/roadmap/simulate-table.md`, scheduled BEFORE S10
> (wave 4.5) — S10/S11 own the same FE files next, so this runs alone, not parallel.
> Contract map: `docs/ai-dlc/contracts/simulate-table-size.md`.
> Outcome-link: "feels like a real game" — S9 design-review shipped a felt that gets
> <half the width of a 1440px screen and whose board cards physically overlap seats.

## Goal (one line)
Make the Simulate table big and uncrowded: the Simulate view alone widens to a
~1360px shell, the sim ring grows taller, and the seat ellipse spreads so no seat
pod, card, pot line, or chip puck overlaps another element at any width ≥1024px —
without touching Practice/Quiz's shared felt.

## Gate-1 decisions (locked 2026-07-12)
- **Direction: widen + respace** (not sidebar-below, not shrink-only).
- **Ship now as its own slice** before S10; S10/S11 land on corrected geometry.
- Board/hero cards KEEP 52×72 — bigger felt makes them proportionally right.
- De-crowding must hold independently of widening (1024–1280px has no widen room).
- **Widening the shell widens the whole Simulate route** — masthead, nav tabs, and
  stats strip are `.app` children and will reflow to ~1360px too. Accepted and
  explicit (they're flex rows; verify-by screenshots the full page, not just felt).

## Refuter findings folded in (2026-07-12, PASS-WITH-ISSUES)
- **(high) Density-gate cascade:** the existing `@media (max-height: 920px)`
  override (`app.css:2561`, `.tablering { max-height: 3.4×card-h }`) is specificity
  (0,1,0); the new `.simulate .tablering` rule is (0,2,0) and would beat it at ALL
  viewport heights. The 5× cap MUST ship with a companion sim-scoped override
  INSIDE the same `max-height: 920px` media query (≈4×card-h) so short viewports
  keep a density bound.
- **(high) Radii bounded by `.stage { overflow: hidden }`** (shared, untouchable):
  at ~46% x-radius on a ~872px ring, a 120px pod's outer edge lands ~25px past the
  container and clips. Spread conservatively (guide: ≤~45%/41%); get clearance
  primarily from the taller ring + wider felt. Verify-by includes a CONTAINMENT
  check: every pod bounding box fully inside the `.tablering` box.
- **(med) S10/S11 rebase:** after this slice merges, update the drafted
  `simulate-s10.md`/`simulate-s11.md`/`simulate-s10-s11.md` docs' `app.css` line
  references and any geometry assumptions (ring height) — a named ticket, not a
  hope.
- **(low) `:has()` silent no-op:** verify-by asserts the COMPUTED `.app` max-width
  equals the wide token on the Simulate route (Playwright), so a non-matching
  selector fails loudly instead of silently keeping 1080px.

## Files / interfaces to touch
- `frontend/src/styles/tokens.css` — add `--content-width-wide: 1360px` (one new token).
- `frontend/src/styles/app.css` — NEW sim-scoped rules only, appended to the `.sim-*`
  block: widen the shell when the Simulate view is mounted
  (`.app:has(.simulate) { max-width: var(--content-width-wide) }`; if `:has()`
  proves unworkable, fall back to an `app--wide` class set in `App.tsx` on
  `view === "simulate"` — ask-first before taking that fallback); raise the sim
  ring cap (`.simulate .tablering { max-height: calc(var(--card-h) * 5) }`) PLUS
  the companion short-viewport override inside the existing
  `@media (max-height: 920px)` gate (≈4×card-h — refuter high-1); clearance
  nudges for `.sim-chips` / pot / hero-cards spacing as measurement demands.
  **No edits inside shared `.stage/.felt/.tablering/.tseat/.pos/.card` base
  rules** (contract hazard 1).
- `frontend/src/components/simulate/SimTable.tsx` — `slotStyle` ellipse radii
  (43%/38% today) spread outward; exact values tuned live with Playwright
  bounding-box measurement until zero overlap at 1024, 1280, 1440.

## Out of scope
Mobile ≤480px felt rework (existing separate NEXT item from S9) · S10 grading UI ·
S11 pacing/stagger · sidebar redesign or relocation · any backend change · any
change visible in Practice/Quiz/Home (shell width there stays `--content-width`) ·
card-size token changes.

## Constraints (invariants)
- CSS values from design tokens only — the new width is a token; scoped rules
  calc() from existing tokens.
- AA contrast + visible focus, both themes (unchanged text styles, but verify).
- Shared felt classes cross-owned with Practice (`PokerTable.tsx`) — new scoped
  rules only; Practice/Quiz render byte-identical.
- FE-only: no `types.ts`, no domain/DB/schema change.
- One-file-one-owner: this slice is sole owner of `tokens.css`, `app.css`,
  `SimTable.tsx` for its wave; S10 starts after merge.

## Verify-by (end-to-end)
1. `cd frontend && npm run typecheck && npm run build` clean; `./scripts/verify.sh`
   still green (no backend change).
2. Playwright at 1440×900 on a live 9-max showdown state: computed `.app`
   max-width = `--content-width-wide` (catches a silent `:has()` no-op); felt ≥
   ~880px wide; **zero bounding-box intersections** between board ∪ pot ∪ every
   seat pod ∪ chip pucks ∪ hero cards (the S9 failure: HJ/CO pods overlapped the
   board at y369–384; hero cards overlapped the pot line); **containment**: every
   pod box fully inside the `.tablering` box (no `.stage` overflow clipping).
3. Same zero-overlap + containment check at 1280×800 and 1024×768 (widening
   absent, respace alone must de-crowd; short-viewport gate active at 768 —
   confirm the companion ≈4× cap applies, not the 5×); felt + hero action console
   visible without vertical scroll at 1440×900.
4. Practice + Texture/Equity quiz felts visually unchanged (screenshot compare,
   both themes) — proves no shared-class bleed. Full-page Simulate screenshot both
   themes — masthead/nav/stats strip acceptable at the wide shell.
5. `design-reviewer` verdict acceptable, both themes.
6. Post-merge doc sync: drafted S10/S11 spec/ticket/contract docs re-based
   (app.css line refs + ring-geometry assumptions).
