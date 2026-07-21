# Contract map — showdown reveal timing (SimTable)

Area: simulate hand playback — when villain hole cards flip face-up on the felt.

## The leak (root cause)

`frontend/src/components/simulate/SimTable.tsx` builds `revealedCards` for each seat:

```
const reveal = showdownBySeat.get(seat.seat_index);      // from hand.showdown
const revealedCards = reveal ? reveal.hole_cards : revealedBySeat.get(seat.seat_index);
```

`showdownBySeat` comes straight from `hand.showdown` and is **ungated by staged playback**.
After a hand ends (incl. a hero fold), the server snapshot is already at showdown, so
`hand.showdown` carries the villain-vs-villain reveal (#55). `SimulateView` passes the same
whole `hand` to `SimTable` during the entire client-side staged replay, so those hole cards
render from the **first staged frame (flop)** — while the board is still being staged
street-by-street via `stagedTableState`.

## Contracts that must NOT break

- **Privacy invariant** (SimTable header comment, lines 11–14): a non-hero seat's hole cards
  render ONLY when it's in `showdown` or the hero explicitly revealed it after folding
  (`revealedBySeat`). The fix must keep this — it only delays the `showdown` case, never
  reveals more.
- **Board staging** (`simPlayback.stagedTableState`): board scopes to the narrated prefix via
  `stagedIndex`. The showdown reveal should follow the same clock (appear when playback reaches
  the end / board fully run out), not lead it.
- **R1 manual reveal** (`revealedBySeat`, hero-fold pure fold-out): triggered by buttons on the
  hand-over panel, only ever fired when `!playing`. Must stay ungated — unaffected.
- **Lockstep felt state** (`revealAt` / `isRevealed`): fold-dim, all-in, chips-in-front already
  gate on `stagedIndex`. Showdown cards are the one felt element that skipped the clock.

## Integration points

- `SimulateView.tsx` owns `playing = eventCount > 0 && stagedIndex < eventCount` (line ~289)
  and renders `<SimTable hand=… stagedIndex=… revealAt=… />` (line ~749). It is the only
  consumer of SimTable; it holds the playback-complete signal SimTable lacks.
- No backend/API/type change. `hand.showdown` shape is unchanged; only the moment we honor it
  on the felt moves.
