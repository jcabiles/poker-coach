import type { HandRevealView, ShowdownSeatView } from "../../api/types";

// History villain reveal (T5) — the PURE state machine behind the replayer's
// "reveal villain hands" buttons. No React, no fetch, no timers, no imports
// beyond types. Same shape of module as the `replaySeats.ts` deriver: the host
// component owns effects, this owns the rules.
//
// WHY THIS IS A MODULE AND NOT COMPONENT STATE. The reveal is an async fetch
// whose response can outlive the thing that asked for it. `HistoryView` stays
// mounted across hand changes (only the keyed `HandReplayTable` child remounts),
// so without a guard this sequence leaks:
//
//   1. request reveal for hand A
//   2. close A, open hand B
//   3. A's response resolves late
//   4. A's cards render on B — matched by seat index, which always collides
//      because every hand has the same nine seats
//
// That is a NO-PEEK violation (cards the user never revealed for hand B) AND a
// fabrication (they are not seat N's cards in hand B). Two other orderings hurt
// too: a stale response can undo a toggle-off, and a slow `last-in` can overwrite
// a newer `all`.
//
// The fix is identity, not luck: every request captures {handId, scope, gen}, and
// a response is applied only if all three still match. `gen` is what makes
// same-hand/same-scope re-requests distinguishable, so toggle-off → re-reveal
// cannot be satisfied by the first response.
//
// The frontend has vitest but no React Testing Library and no jsdom, so a
// component's async behavior is untestable here. Keeping this pure is what makes
// the three race cases plain synchronous unit tests.

export type RevealScope = "last-in" | "all";

export interface RevealState {
  /** The hand these cards belong to. Part of every response's identity check. */
  readonly handId: number;
  /** Active scope, or null when nothing is revealed. Drives `aria-pressed`. */
  readonly scope: RevealScope | null;
  /** Request generation. Bumped on every user action that invalidates in-flight work. */
  readonly gen: number;
  /** seat_index -> revealed seat. Empty whenever `scope` is null. */
  readonly bySeat: ReadonlyMap<number, ShowdownSeatView>;
  /** A request is out and hasn't been answered. */
  readonly pending: boolean;
  /** The server answered `available: false` (capability off / unknown scope). */
  readonly unavailable: boolean;
}

/** The identity a caller must carry alongside its fetch and hand back on reply. */
export interface RevealRequestMeta {
  readonly handId: number;
  readonly scope: RevealScope;
  readonly gen: number;
}

const NO_SEATS: ReadonlyMap<number, ShowdownSeatView> = new Map();

export function initialRevealState(handId: number): RevealState {
  return {
    handId,
    scope: null,
    gen: 0,
    bySeat: NO_SEATS,
    pending: false,
    unavailable: false,
  };
}

/**
 * A scope button was clicked.
 *
 * Clicking the ACTIVE scope hides again (the control is a toggle, so
 * `aria-pressed` has to be truthful — a pressed button you cannot unpress lies
 * to assistive tech). Clicking the other scope swaps.
 *
 * Cards are cleared on a swap rather than held until the new set lands. Holding
 * them would let an `all` -> `last-in` swap display folded seats while the
 * pressed control claims `last-in` — showing more than the active scope admits
 * to. A brief face-down beat is the honest trade.
 *
 * Returns the next state plus the request identity to fetch with, or `null` when
 * the click resolved to "hide" and there is nothing to fetch.
 */
export function toggleReveal(
  state: RevealState,
  scope: RevealScope,
): { state: RevealState; request: RevealRequestMeta | null } {
  const gen = state.gen + 1;
  if (state.scope === scope) {
    // Hide. gen still advances so any in-flight response is now stale.
    return {
      state: { ...state, scope: null, gen, bySeat: NO_SEATS, pending: false, unavailable: false },
      request: null,
    };
  }
  return {
    state: { ...state, scope, gen, bySeat: NO_SEATS, pending: true, unavailable: false },
    request: { handId: state.handId, scope, gen },
  };
}

/** True when `meta` still describes what the user is currently asking for. */
function isCurrent(state: RevealState, meta: RevealRequestMeta): boolean {
  return (
    meta.handId === state.handId && meta.scope === state.scope && meta.gen === state.gen
  );
}

/**
 * A reveal response came back. Returns the state UNCHANGED unless `meta` still
 * matches — that single check is what closes all three races.
 */
export function applyRevealResponse(
  state: RevealState,
  response: HandRevealView,
  meta: RevealRequestMeta,
): RevealState {
  if (!isCurrent(state, meta)) return state;
  if (!response.available) {
    return { ...state, bySeat: NO_SEATS, pending: false, unavailable: true };
  }
  const bySeat = new Map<number, ShowdownSeatView>();
  for (const seat of response.seats) bySeat.set(seat.seat_index, seat);
  return { ...state, bySeat, pending: false, unavailable: false };
}

/**
 * A reveal fetch failed. Non-fatal by design (matching the live table): the felt
 * simply stays face-down. Same identity guard, so a stale failure cannot clear a
 * newer request's pending flag.
 */
export function applyRevealError(
  state: RevealState,
  meta: RevealRequestMeta,
): RevealState {
  if (!isCurrent(state, meta)) return state;
  return { ...state, scope: null, bySeat: NO_SEATS, pending: false, unavailable: false };
}

/**
 * A different hand was opened (or the replayer closed and reopened).
 *
 * `gen` deliberately carries forward rather than resetting to 0: a fresh counter
 * would let a late response from the previous hand match by coincidence when the
 * new hand happens to reach the same generation. Monotonic across the whole
 * component lifetime, so an identity can never be reused.
 */
export function resetForHand(state: RevealState, handId: number): RevealState {
  return {
    handId,
    scope: null,
    gen: state.gen + 1,
    bySeat: NO_SEATS,
    pending: false,
    unavailable: false,
  };
}
