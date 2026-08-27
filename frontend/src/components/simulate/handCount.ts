// Two-mode Simulate (T8) — the completed-hand derivation, alone in a module so
// it can be pinned. No React, no fetch, no types beyond the wire shape; same
// shape of module as `replaySeats.ts`.
//
// WHY THIS IS A MODULE AND NOT AN EXPRESSION IN THE VIEW. This is the one place
// the client and the server have to agree about a number, and the arithmetic is
// counter-intuitive enough that it has already been got wrong twice in approved
// documents: the spec was rewritten at rev 2 because the original derivation
// fired the gate a hand late, and the roadmap had to be corrected with it. The
// server pins its half in `backend/tests`; until this module existed the
// client's half was pinned by nothing at all, so the two could drift apart with
// every gate green.
//
// The rule (spec para 11): `deal_next_hand()` early-returns without
// incrementing while a hand is in progress and increments only once the hand
// settles, so `hand_no` counts the hand being PLAYED, not hands finished. A
// hand therefore counts only once it is over.
//   • `hand_no - 1` alone fires the gate after hand 201 is dealt, and shows the
//     counter as "Hand 201 / 200".
//   • `hand_no` alone fires it while hand 200 is still live, which bars the
//     deal mid-hand.

/** Completed hands the Challenge table counts towards its blind check. */
export const BLIND_CHECK_HAND_GATE = 200;

/** The wire fields this derivation reads — a structural subset of the hand. */
export interface HandProgress {
  hand_no: number;
  hand_over: boolean;
}

/**
 * Hands the player has FINISHED. 199 while hand 200 is live, 200 once it
 * settles. No live session (no hand yet) is zero, not NaN.
 */
export function completedHands(hand: HandProgress | null | undefined): number {
  if (hand == null) return 0;
  return hand.hand_no - (hand.hand_over ? 0 : 1);
}

/**
 * Has the table reached the point where the server bars the deal? The server's
 * own predicate is `>=`, not `==`, so a session that somehow sits past the gate
 * is still gated rather than waved through; this mirrors that.
 */
export function atBlindCheckGate(hand: HandProgress | null | undefined): boolean {
  return completedHands(hand) >= BLIND_CHECK_HAND_GATE;
}

/**
 * Distance travelled towards the check, as a percentage for the progress bar.
 * Clamped at both ends: the bar never draws negative, and never overruns its
 * own track if a session is somehow past the gate.
 */
export function gateProgressPct(hand: HandProgress | null | undefined): number {
  const done = completedHands(hand);
  if (done <= 0) return 0;
  return Math.min(100, (done / BLIND_CHECK_HAND_GATE) * 100);
}
