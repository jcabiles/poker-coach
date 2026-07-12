# Contracts — Simulate table size/crowding fix

> Addendum to `simulate-s10-s11.md` (hazard 6: shared felt classes). Measured live
> 2026-07-12 via Playwright at 1440×900, 9-max river all-in showdown state.

## Measured problem (1440×900)
- Stage 664×317, felt 638×315, tablering 590×245 — table uses <half the viewport width.
- Board = 5 × 52×72px cards = 292px wide = **49% of ring width**; spans x382–674.
- HJ seat (x423–459, y323–384) and CO seat (x568–661, y323–384) **overlap the board**
  (board y369–441) — stack text hidden behind cards.
- Hero seat (120×126 at y471) overlaps the pot line; BB showdown reveal overlaps its
  chips-in-front puck. Side pods (LJ/UTG2/BTN/SB) crowd the rail edge.

## Size drivers (the contract surface)
- `tokens.css:115` `--content-width: 1080px` — .app shell max-width (ALL views).
- `tokens.css:116` `--sidebar-w: 360px` — sim-layout right column (`app.css:2625`).
- `tokens.css:117-118` `--card-w: 52px / --card-h: 72px` — every card face app-wide.
- `app.css:271-277` `.tablering` — aspect-ratio 2.1/1, `max-height: calc(var(--card-h) * 3.9)`
  (=280px). Comment: bound exists for the 1024×768 density gate (Practice drill).
- `app.css:2561` existing narrow-gate override `.tablering { max-height: 3.4 * card-h }`.
- `SimTable.tsx:19-24` `slotStyle` — seat ellipse radii 43%/38%, sim-OWNED copy
  (PokerTable.tsx has its own; they only share CSS classes, not code).
- `app.css:2728-2730` `.sim-reveal .card` 0.6×; `:349-351` `.tseat-cards .card` 0.45×.

## Invisible contracts / hazards
1. `.stage/.felt/.tablering/.tseat/.pos/.card` are SHARED with Practice + quizzes —
   base-class edits bleed. All sizing changes must be NEW sim-scoped rules
   (`.simulate …`, `.sim-*`) or SimTable-local geometry. Test: Practice/Quiz felt
   byte-identical rendering after change.
2. `--content-width`/`--sidebar-w`/`--card-w/h` are global tokens — changing their
   VALUES resizes every view. Widening only Simulate needs a sim-scoped override
   (e.g. `.app:has(.simulate)` or a wrapper class), values still token-derived
   (calc on existing tokens satisfies the tokens-only invariant).
3. 1024×768 density gate is a Practice constraint; Simulate has its own narrow gate
   at `app.css:2955` (one column). A taller sim ring must still fit 768px-tall
   viewports minus masthead+action bar, or degrade via media query.
4. S10 (W5) + S11 (W6) specs already own `SimulateView/SimTable/SimActionBar/app.css`
   sequentially — this fix must be wave-ordered against them, not parallel
   (one-file-one-owner).
5. S9 known deferral: mobile 375px felt collapse is a SEPARATE "NEXT" item — this fix
   targets desktop/tablet crowding; don't silently absorb the mobile rework.
