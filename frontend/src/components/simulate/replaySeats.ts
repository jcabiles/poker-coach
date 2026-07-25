import type { HandReplayView, ReplayStepView, ShowdownSeatView } from "../../api/types";
import { fmtBb } from "./simGrade";

// Simulate History Replayer (HRT-1) — the pure reconstruction layer for the
// two-pane felt replayer. The replay wire (HandReplayView) carries only a flat
// action log (steps[]), never a per-step SeatView[] snapshot, so the felt's
// seat state has to be DERIVED by folding the log up to the cursor. This module
// is that derivation — pure, deterministic, unit-tested, no React.
//
// VERIFIED PAYLOAD SEMANTICS (do not re-guess — see backend):
//  - HistoryAction.amount_bb (engine.py:299-304) is the per-action INCREMENT
//    (chips this seat added on this action), NOT the raise-to total. So a
//    raise's "raises to N" total is priorStreetInvestment + amount_bb.
//  - is_terminal means the terminal SHOWDOWN step — NOT "hand complete". An
//    uncontested fold-out has no terminal step (sim_session.py:1461-1465), so
//    "complete" is a separate flag: cursor === steps.length - 1.
//  - Villain reveals live only on the terminal step; NO-PEEK is inherent to the
//    wire (revealed_seats is [] on every non-terminal step).

// Canonical 9-max seating order (clockwise) — same ring SimTable/PokerTable use.
export const RING = ["UTG", "UTG1", "UTG2", "LJ", "HJ", "CO", "BTN", "SB", "BB"];

const STREET_ORDER = ["preflop", "flop", "turn", "river"] as const;
const STREET_BOARD_N: Record<number, number> = { 3: 1, 4: 2, 5: 3 }; // board len → deepest street idx

export interface ReplaySeat {
  position: string;
  seatIndex: number;
  isHero: boolean;
  isButton: boolean;
  folded: boolean;
  isActing: boolean;
  // The seat's most recent non-post action so far, as a felt-pod phrase
  // ("Checks", "Calls 3bb", "Raises to 9bb", "Folds"), or null if it has only
  // posted a blind / not yet acted.
  lastActionVerb: string | null;
  reveal?: ShowdownSeatView; // present ONLY at the terminal step
}

export interface DerivedFelt {
  seats: ReplaySeat[]; // ring order, hero at index 0 (bottom)
  board: string[];
  potBb: number; // gross COMMITTED chips up to the cursor (not the settled pot)
  street: string; // the cursor step's action street
  isTerminal: boolean;
  isComplete: boolean; // cursor is the last step (may be a fold-out, not a showdown)
}

export interface MoveRow {
  stepIndex: number; // index into replay.steps
  street: string;
  position: string;
  isHero: boolean;
  verb: string; // "raises to 9bb" / "calls 3bb" / "checks" / "folds"
  correctness: ReplayStepView["correctness"]; // hero rows only carry a graded tier
}

export interface ReplayModel {
  moves: MoveRow[]; // visible (non-post) actions, in order
  visibleSteps: number[]; // step indices that are non-post (navigation lands only on these)
  reachedStreets: string[]; // streets to render as groups (incl. auto-runout turn/river)
}

// The verb phrase for one action. `raiseTo` is the seat's post-action street
// total (priorStreetInvestment + increment) — only meaningful for RAISE.
function actionPhrase(action: string, amountBb: number, raiseTo: number): string {
  switch (action) {
    case "fold":
      return "Folds";
    case "check":
      return "Checks";
    case "call":
      return amountBb <= 1 ? "Limps" : `Calls ${fmtBb(amountBb)}bb`;
    case "bet":
      return `Bets ${fmtBb(amountBb)}bb`;
    case "raise":
      return `Raises to ${fmtBb(raiseTo)}bb`;
    case "post":
      return `Posts ${fmtBb(amountBb)}bb`;
    default:
      return action;
  }
}

// Which streets the hand reached (in order) — the deepest of any acted street
// AND the terminal board length, so an all-in auto-runout still yields turn/river
// groups even though no action step carries those streets (mirrors HandReplay).
export function reachedStreets(replay: HandReplayView): string[] {
  let deepest = 0;
  for (const s of replay.steps) {
    const idx = STREET_ORDER.indexOf(s.street as (typeof STREET_ORDER)[number]);
    if (idx > deepest) deepest = idx;
    if (s.is_terminal) {
      const byBoard = STREET_BOARD_N[s.board.length] ?? 0;
      if (byBoard > deepest) deepest = byBoard;
    }
  }
  return STREET_ORDER.slice(0, deepest + 1);
}

// The cursor-independent parts of the hand: the moves list (with corrected
// raise-to labels), the visible-step index map, and the reached streets. Compute
// once per hand.
export function buildReplayModel(replay: HandReplayView): ReplayModel {
  const moves: MoveRow[] = [];
  const visibleSteps: number[] = [];
  const streetInvest = new Map<string, number>(); // `${street}|${position}` → chips in this street
  replay.steps.forEach((s, i) => {
    const key = `${s.street}|${s.position}`;
    const prior = streetInvest.get(key) ?? 0;
    const raiseTo = prior + s.amount_bb;
    if (s.amount_bb > 0) streetInvest.set(key, raiseTo); // post/call/bet/raise add chips
    if (s.is_post) return; // posts fold into investment but are never a visible row
    visibleSteps.push(i);
    moves.push({
      stepIndex: i,
      street: s.street,
      position: s.position,
      isHero: s.is_hero,
      verb: actionPhrase(s.action, s.amount_bb, raiseTo),
      correctness: s.correctness,
    });
  });
  return { moves, visibleSteps, reachedStreets: reachedStreets(replay) };
}

// Fold the action log up to `cursor` into the felt's seat state at that step.
export function deriveSeats(replay: HandReplayView, cursor: number): DerivedFelt {
  const steps = replay.steps;
  const total = steps.length;
  const idx = Math.min(Math.max(cursor, 0), Math.max(total - 1, 0));
  const cur = steps[idx];
  const isComplete = idx === total - 1;
  const isTerminal = cur.is_terminal;

  // Present-seat roster: map every acted/posted position → its seat index (stable
  // across the whole hand, not just up to the cursor), plus the hero.
  const posSeat = new Map<string, number>();
  for (const s of steps) posSeat.set(s.position, s.seat);
  posSeat.set(replay.hero_position, replay.hero_seat);

  // Fold the log up to the cursor: fold status, per-street investment, and each
  // seat's most recent action phrase.
  const folded = new Set<string>();
  const lastVerb = new Map<string, string>();
  const streetInvest = new Map<string, number>();
  for (let i = 0; i <= idx; i++) {
    const s = steps[i];
    const key = `${s.street}|${s.position}`;
    const prior = streetInvest.get(key) ?? 0;
    const raiseTo = prior + s.amount_bb;
    if (s.amount_bb > 0) streetInvest.set(key, raiseTo);
    if (s.action === "fold") folded.add(s.position); // permanent across streets
    // The pod verb resets each street: show only the seat's most recent action on
    // the CURSOR's street (like the live table). `folded` carries the dim state
    // for seats that folded on an earlier street and show no verb here.
    if (!s.is_post && s.street === cur.street) {
      lastVerb.set(s.position, actionPhrase(s.action, s.amount_bb, raiseTo));
    }
  }

  // Terminal reveals keyed by seat index (NO-PEEK: only ever at the terminal step).
  const revealBySeat = new Map<number, ShowdownSeatView>();
  if (isTerminal) for (const r of cur.revealed_seats) revealBySeat.set(r.seat_index, r);

  // Ring order, hero rotated to the bottom (index 0).
  const ring = RING.filter((p) => posSeat.has(p));
  const heroAt = ring.indexOf(replay.hero_position);
  const hi = heroAt < 0 ? 0 : heroAt;
  const seats: ReplaySeat[] = ring.map((_, i) => {
    const position = ring[(hi + i) % ring.length];
    const seatIndex = posSeat.get(position) as number;
    return {
      position,
      seatIndex,
      isHero: seatIndex === replay.hero_seat,
      isButton: seatIndex === replay.button_seat,
      folded: folded.has(position),
      // Acting cue = the seat whose action this step shows — but never on the
      // terminal showdown frame or the final fold-out frame.
      isActing: seatIndex === cur.seat && !isComplete && !isTerminal,
      lastActionVerb: lastVerb.get(position) ?? null,
      reveal: revealBySeat.get(seatIndex),
    };
  });

  const potBb = steps.slice(0, idx + 1).reduce((sum, s) => sum + s.amount_bb, 0);

  return { seats, board: cur.board, potBb, street: cur.street, isTerminal, isComplete };
}
