# Delta spec — gate villain showdown reveal to playback completion

## Goal
During staged hand playback, villain-vs-villain showdown hole cards must stay face-down until
playback reaches the end (board fully run out) — not flash face-up at the flop.

## Root cause
`SimTable` reads `hand.showdown` (`showdownBySeat`) ungated by `stagedIndex`. The server snapshot
is already at showdown, so those cards render from the first staged frame while the board is still
staging street-by-street. See `docs/ai-dlc/contracts/showdown-reveal-timing.md`.

## Change
- `frontend/src/components/SimulateView.tsx` — pass the existing playback-complete signal to
  SimTable: `playbackComplete={!playing}` (where `playing = eventCount > 0 && stagedIndex < eventCount`).
- `frontend/src/components/simulate/SimTable.tsx` — accept `playbackComplete: boolean` and gate the
  showdown-sourced reveal on it. Only `showdownBySeat` (public showdown) is gated; `revealedBySeat`
  (R1 manual hero-fold reveal) stays ungated. i.e. use the showdown reveal only when
  `playbackComplete` is true; otherwise fall through to `revealedBySeat` / face-down.

## Out of scope
- No change to the #55 reveal *rule* (which hands reach showdown / are eligible to reveal) — timing only.
- No backend, API, `types.ts`, or `stagedTableState` change. No per-seat street-level staging of the
  reveal — all showdown cards flip together at completion.
- No change to R1 manual-reveal buttons or hero cards.

## Constraints (from profile invariants + SimTable privacy contract)
- Privacy: a non-hero seat's cards still render ONLY via `showdown` (now delayed) or `revealedBySeat`.
  Never reveal more seats than today — only later.
- CSS/tokens untouched; no raw values. No auth surface (local single-user).
- FE types hand-maintained — no generated-type edits (none needed).

## Verify-by (end-to-end)
1. `cd frontend && npm run typecheck && npm run build` → clean.
2. Boot (`./scripts/serve.sh start`), Simulate a hand where the hero folds and two villains check/call
   to a genuine showdown. During staged playback the two villains stay **face-down** at flop/turn;
   their cards flip face-up only when the board finishes running out (playback complete) and the
   hand-over recap shows the same reveal.
3. Regression: a hero-in showdown still auto-reveals at completion; a pure fold-out still shows the
   R1 "Reveal Last-In / Reveal All" buttons and flips those on click.
