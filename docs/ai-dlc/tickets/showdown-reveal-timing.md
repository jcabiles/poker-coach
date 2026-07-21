# Tickets — gate villain showdown reveal to playback completion

Spec: `docs/ai-dlc/specs/showdown-reveal-timing.md`
Small fix, 2 files, one logical change. Do sequentially (T2 depends on T1's prop). Single agent.

## T1 — SimTable: gate showdown reveal on `playbackComplete`
- File (owned): `frontend/src/components/simulate/SimTable.tsx`
- Add prop `playbackComplete: boolean` to the component's props.
- Change the reveal source so the `showdownBySeat` (public showdown) branch is used only when
  `playbackComplete` is true; `revealedBySeat` (R1 manual reveal) stays ungated.
  e.g. `const reveal = playbackComplete ? showdownBySeat.get(seat.seat_index) : undefined;`
  then `revealedCards = reveal ? reveal.hole_cards : revealedBySeat.get(seat.seat_index)`.
- Keep the privacy header comment accurate (note the showdown case now waits for playback complete).
- Acceptance: showdown cards only build `revealedCards` when `playbackComplete`; no other seat state
  changes. Done-condition: `cd frontend && npm run typecheck` clean.

## T2 — SimulateView: pass `playbackComplete={!playing}`
- File (owned): `frontend/src/components/SimulateView.tsx`
- On the `<SimTable …>` render (~line 749), add `playbackComplete={!playing}` (reuse existing
  `playing = eventCount > 0 && stagedIndex < eventCount`; no new state).
- Depends on: T1.
- Acceptance: prop wired; `cd frontend && npm run typecheck && npm run build` clean.

## T3 — Verify end-to-end + regressions
- No file owned (manual/observed per spec Verify-by).
- Confirm: hero-fold → two villains check/call to showdown stay face-down at flop/turn, flip only at
  completion; hero-in showdown still auto-reveals; pure fold-out still offers R1 reveal buttons and
  flips on click.
- Depends on: T1, T2. Done-condition: spec Verify-by steps 1–3 pass.

Notes: no backend/API/types/CSS/token changes. Fold in any refuter findings before starting.
