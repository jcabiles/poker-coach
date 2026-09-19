import type { ActionType } from "../../api/types";

// P3a §5 — "is this button a shove?", alone in a module so it can be pinned.
// No React, no fetch; same shape of module as `handCount.ts`.
//
// WHY THIS IS NOT AN EXPRESSION IN THE ACTION BAR. The two halves of the answer
// come from different fields and read in different units, and getting either
// one backwards arms a confirm on the wrong button — which is worse than no
// confirm at all, because it trains the player to tap twice by reflex.
//
//   • BET and RAISE are quoted as a street TOTAL ("raise TO 12bb"), and the
//     engine publishes the ceiling of that total as `max_bb`
//     (`backend/app/domain/table/engine.py:_raise_action`, where max_bb is
//     `invested_street_bb + stack_bb`). Reaching max_bb is the shove.
//   • CALL is quoted as chips OWED, already capped at the stack
//     (`min(to_call, seat.stack_bb)`), and carries no max_bb at all. Owing the
//     whole stack is the shove.
//
// The tolerance exists because the offered sizes are rounded (1dp for the
// two-size offers, 2dp for the engine's own) while the ceiling is rounded to
// 2dp: a size clamped onto the ceiling can land a float-hair below it.

const EPS_BB = 0.01;

export interface AllInProbe {
  action: ActionType;
  /** What this button offers: a street total for bet/raise, chips owed for call. */
  offeredBb?: number | null;
  /** The engine's ceiling for this leg (bet/raise). Absent ⇒ unknown, never a shove. */
  maxBb?: number | null;
  /** Hero's chips behind, right now. */
  heroStackBb: number;
}

/**
 * Does taking this option put the hero all-in? Deliberately conservative:
 * anything it cannot prove is a shove comes back false, so a missing field
 * costs a confirm step rather than adding a spurious one.
 */
export function isAllIn({ action, offeredBb, maxBb, heroStackBb }: AllInProbe): boolean {
  if (heroStackBb <= EPS_BB) return false; // nothing left to commit
  if (offeredBb == null || offeredBb <= 0) return false;
  if (action === "call") return offeredBb >= heroStackBb - EPS_BB;
  if (action === "bet" || action === "raise") {
    if (maxBb == null) return false;
    return offeredBb >= maxBb - EPS_BB;
  }
  return false; // fold / check / post commit nothing
}
