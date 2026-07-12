# Spec — S11: Pacing + table feel polish

> Slice S11 of `docs/ai-dlc/roadmap/simulate-table.md` (mark `[x]` when pass/fail holds).
> Contract map: `docs/ai-dlc/contracts/simulate-s10-s11.md`. Runs AFTER S10 (shared FE files).
> Outcome-link: "feels like a real game" — the premise of the Simulate surface.

## Goal (one line)
Make the Simulate table readable and game-like: randomized client-side bot pacing with a normal/fast/instant setting, hero-fold → instant resolution + auto-deal, and a tokens-only styling pass — touching only `.sim-*`, never Practice's shared table.

## Gate-1 decisions (locked 2026-07-11)
- **Pacing is pure client-side replay** of the already-returned `events` batch (no server hook exists; building one is out of scope).
- **Speed setting = default normal, localStorage client-only.** No wire field, no migration. Randomized ~0.5–1.5s bot delays.

## Files / interfaces to touch (all frontend)
- `frontend/src/components/simulate/SimEventLog.tsx` — the pacing seam: stagger the reveal of the returned `events` batch on a timer instead of dumping the static list at once.
- `frontend/src/components/SimulateView.tsx` — speed-setting state (read/write localStorage; normal default); gate the stagger timing; hero-fold ⇒ skip animation, immediately deal next hand.
- `frontend/src/components/simulate/SimTable.tsx` — **firm requirement (refuter med-2, not optional):** reveal bot seat state (fold-dim, chips-in, all-in) in LOCKSTEP with the staggered log lines, driven by a shared staged index in `SimulateView`. Otherwise the felt shows fully-resolved final state (server already advanced all bots) while the log narrates catch-up — a visible desync that defeats pacing. Keep it to seat status + chip reveals; no card-flip motion, no animation library.
- `frontend/src/components/simulate/SimActionBar.tsx` — disable during pacing playback so the hero can't act mid-animation.
- A small speed-picker control (normal/fast/instant) inside the Simulate view chrome (not global `App.tsx` nav).
- `frontend/src/styles/app.css` — tokens-only polish pass on the `.sim-*` block (`:2576-2986` after wave 4.5's table-size section — do not undo its wide-shell/ring-cap/1100px-gate rules): spacing rhythm, legibility, badge/recap styling coherence, motion timing. **Never edit shared `.stage/.felt/.tablering/.tseat/.pos/.card` base classes.**

## Out of scope
Server-driven / streamed pacing; any backend or migration change; sound; avatars/art beyond persona badges; an animation library (ask-first); touching Practice/Quiz's `PokerTable` or shared felt base classes; grading changes (S10).

## Constraints (invariants)
- CSS from design tokens only (no raw hex/px outside tokens.css); AA contrast + visible focus both themes.
- Respect `prefers-reduced-motion` (the app's existing motion-a11y convention) — instant/no-stagger under reduce.
- FE-only: no domain/DB/schema change; `types.ts` untouched unless a client-only speed enum is added (prefer not).
- One-file-one-owner: S11 runs after S10-FE has merged (shared `SimulateView`/`SimTable`/`SimActionBar`/`app.css`).

## Verify-by (end-to-end)
- `cd frontend && npm run typecheck && npm run build` clean; `./scripts/verify.sh` still green (no backend change).
- Speed setting observably changes pacing (normal vs fast vs instant) and persists across reload.
- Hero-fold skips ahead to the next hand without waiting out bot animation.
- During staggered playback the felt (SimTable seat state) and the event log stay in lockstep — no seat shows its final folded/all-in state before the log narrates that action.
- `design-reviewer` verdict acceptable across both themes + breakpoints (AA contrast + focus); no visual regression to Practice/Quiz's table.
- `prefers-reduced-motion` disables the stagger.
