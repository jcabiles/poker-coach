import { describe, expect, it } from "vitest";

import type { HandReplayView, ReplayStepView, ShowdownSeatView } from "../../api/types";
import { buildReplayModel, deriveSeats, reachedStreets } from "./replaySeats";

// Minimal step factory — only the fields the deriver reads. Grading fields default
// to null (ungraded) unless a hero step overrides them.
function step(p: Partial<ReplayStepView> & { position: string; seat: number }): ReplayStepView {
  return {
    index: 0,
    street: "preflop",
    action: "fold",
    amount_bb: 0,
    board: [],
    is_hero: false,
    is_post: false,
    is_terminal: false,
    revealed_seats: [],
    correctness: null,
    sizing_correctness: null,
    ev_loss_bb: null,
    coverage: null,
    verdict: null,
    reasoning: null,
    ...p,
  };
}

function hand(steps: ReplayStepView[], over: Partial<HandReplayView> = {}): HandReplayView {
  return {
    sim_hand_id: 1,
    session_id: "s",
    hand_no: 1,
    button_seat: 6, // BTN
    hero_seat: 0,
    hero_position: "CO",
    hero_cards: ["As", "Ks"],
    steps: steps.map((s, i) => ({ ...s, index: i })),
    ...over,
  };
}

// A compact but realistic hand: hero (CO, seat 0) with villains. Positions map to
// seats so the ring can rotate. Blinds post, some action, a flop, hero decision.
const SB = { position: "SB", seat: 7 };
const BB = { position: "BB", seat: 8 };
const UTG = { position: "UTG", seat: 1 };
const CO = { position: "CO", seat: 0 }; // hero
const BTN = { position: "BTN", seat: 6 };

describe("deriveSeats", () => {
  it("(a) fold status propagates forward once a seat folds", () => {
    const h = hand([
      step({ ...SB, action: "post", amount_bb: 0.5, is_post: true }),
      step({ ...BB, action: "post", amount_bb: 1, is_post: true }),
      step({ ...UTG, action: "fold" }),
      step({ ...CO, action: "raise", amount_bb: 3, is_hero: true }),
    ]);
    const before = deriveSeats(h, 1); // BB post, UTG not folded yet
    expect(before.seats.find((s) => s.position === "UTG")?.folded).toBe(false);
    const after = deriveSeats(h, 3); // past UTG fold
    expect(after.seats.find((s) => s.position === "UTG")?.folded).toBe(true);
  });

  it("(b) acting seat = the cursor step's actor (mid-hand)", () => {
    const h = hand([
      step({ ...UTG, action: "raise", amount_bb: 3 }),
      step({ ...CO, action: "call", amount_bb: 3, is_hero: true }),
      step({ ...BTN, action: "fold" }), // trailing step so cursor 1 is not the final frame
    ]);
    const s0 = deriveSeats(h, 0);
    expect(s0.seats.find((s) => s.isActing)?.position).toBe("UTG");
    const s1 = deriveSeats(h, 1);
    expect(s1.seats.find((s) => s.isActing)?.position).toBe("CO");
  });

  it("(c) acting is suppressed on the final fold-out frame (no showdown)", () => {
    // Everyone folds to BB — the last step is a fold, is_terminal stays false.
    const h = hand([
      step({ ...UTG, action: "fold" }),
      step({ ...CO, action: "fold", is_hero: true }),
      step({ ...BTN, action: "fold" }),
    ]);
    const end = deriveSeats(h, 2);
    expect(end.isComplete).toBe(true);
    expect(end.isTerminal).toBe(false);
    expect(end.seats.some((s) => s.isActing)).toBe(false);
  });

  it("(d) the pod verb resets across a street boundary", () => {
    const h = hand([
      step({ ...CO, street: "flop", action: "bet", amount_bb: 4, is_hero: true }),
      step({ ...BB, street: "flop", action: "call", amount_bb: 4 }),
      step({ ...CO, street: "turn", action: "check", is_hero: true, board: ["Js", "7h", "2d", "5c"] }),
    ]);
    // At the flop bet, CO shows its flop action.
    expect(deriveSeats(h, 0).seats.find((s) => s.position === "CO")?.lastActionVerb).toBe("Bets 4bb");
    // On the turn, before CO acts again, BB (who only acted on the flop) shows no verb.
    const turn = deriveSeats(h, 2);
    expect(turn.seats.find((s) => s.position === "BB")?.lastActionVerb).toBeNull();
    expect(turn.seats.find((s) => s.position === "CO")?.lastActionVerb).toBe("Checks");
  });

  it("(g) terminal reveals appear only at the terminal step, never before", () => {
    const reveal: ShowdownSeatView = { seat_index: 1, hole_cards: ["Qd", "Qc"], delta_bb: 5 };
    const h = hand([
      step({ ...UTG, action: "call", amount_bb: 1 }),
      step({
        ...CO,
        action: "call",
        amount_bb: 1,
        is_hero: true,
        is_terminal: true,
        board: ["Js", "7h", "2d", "5c", "9s"],
        revealed_seats: [reveal],
      }),
    ]);
    expect(deriveSeats(h, 0).seats.find((s) => s.seatIndex === 1)?.reveal).toBeUndefined();
    const term = deriveSeats(h, 1);
    expect(term.isTerminal).toBe(true);
    expect(term.seats.find((s) => s.seatIndex === 1)?.reveal).toEqual(reveal);
  });

  it("(h) hero is rotated to the bottom (ring index 0)", () => {
    const h = hand([
      step({ ...UTG, action: "fold" }),
      step({ ...BTN, action: "call", amount_bb: 1 }),
      step({ ...CO, action: "raise", amount_bb: 3, is_hero: true }),
    ]);
    expect(deriveSeats(h, 2).seats[0].position).toBe("CO");
    expect(deriveSeats(h, 2).seats[0].isHero).toBe(true);
  });

  it("(i) every acted position appears in the ring", () => {
    const positions = ["UTG", "UTG1", "UTG2", "LJ", "HJ", "CO", "BTN", "SB", "BB"];
    const steps = positions.map((position, seat) =>
      step({ position, seat, action: "call", amount_bb: 1, is_hero: position === "CO" }),
    );
    const derived = deriveSeats(hand(steps), steps.length - 1);
    expect(derived.seats).toHaveLength(9);
    expect(new Set(derived.seats.map((s) => s.position))).toEqual(new Set(positions));
  });

  it("(k) isButton keys off button_seat, not the position string", () => {
    const h = hand(
      [
        step({ ...BTN, action: "call", amount_bb: 1 }),
        step({ ...CO, action: "raise", amount_bb: 3, is_hero: true }),
      ],
      { button_seat: 6 },
    );
    const btn = deriveSeats(h, 1).seats.find((s) => s.seatIndex === 6);
    expect(btn?.isButton).toBe(true);
    expect(deriveSeats(h, 1).seats.filter((s) => s.isButton)).toHaveLength(1);
  });

  it("pot is the sum of committed increments up to the cursor", () => {
    const h = hand([
      step({ ...SB, action: "post", amount_bb: 0.5, is_post: true }),
      step({ ...BB, action: "post", amount_bb: 1, is_post: true }),
      step({ ...CO, action: "raise", amount_bb: 3, is_hero: true }),
    ]);
    expect(deriveSeats(h, 2).potBb).toBeCloseTo(4.5);
  });
});

describe("buildReplayModel", () => {
  it("(e) raise-to = prior street investment + increment (3-bet / blind 4-bet)", () => {
    // amount_bb is the per-seat INCREMENT = size − that seat's own prior street
    // investment (engine.py:288). UTG opens to 3 (from 0 → incr 3). CO 3-bets to 9
    // (from 0 → incr 9). BB, having posted 1, 4-bets to 25 (from 1 → incr 24).
    const h = hand([
      step({ ...BB, action: "post", amount_bb: 1, is_post: true }),
      step({ ...UTG, action: "raise", amount_bb: 3 }),
      step({ ...CO, action: "raise", amount_bb: 9, is_hero: true }),
      step({ ...BB, action: "raise", amount_bb: 24 }),
    ]);
    const verbs = buildReplayModel(h).moves.map((m) => m.verb);
    expect(verbs).toEqual(["Raises to 3bb", "Raises to 9bb", "Raises to 25bb"]);
  });

  it("(post) POST steps fold into investment but are never visible rows", () => {
    const h = hand([
      step({ ...SB, action: "post", amount_bb: 0.5, is_post: true }),
      step({ ...BB, action: "post", amount_bb: 1, is_post: true }),
      step({ ...UTG, action: "fold" }),
    ]);
    const model = buildReplayModel(h);
    expect(model.visibleSteps).toEqual([2]); // only the UTG fold is visible
    expect(model.moves.map((m) => m.position)).toEqual(["UTG"]);
  });
});

describe("reachedStreets", () => {
  it("(j) an all-in auto-runout yields turn/river even with no action step for them", () => {
    // Preflop all-in + call; terminal step carries the full 5-card board but street="preflop".
    const h = hand([
      step({ ...UTG, action: "raise", amount_bb: 100 }),
      step({
        ...CO,
        action: "call",
        amount_bb: 100,
        is_hero: true,
        is_terminal: true,
        street: "preflop",
        board: ["Js", "7h", "2d", "5c", "9s"],
        revealed_seats: [{ seat_index: 1, hole_cards: ["Qd", "Qc"], delta_bb: -100 }],
      }),
    ]);
    expect(reachedStreets(h)).toEqual(["preflop", "flop", "turn", "river"]);
  });

  it("a flop-only hand reaches exactly preflop..flop", () => {
    const h = hand([
      step({ ...CO, action: "check", street: "flop", is_hero: true, board: ["Js", "7h", "2d"] }),
      step({ ...BB, action: "bet", amount_bb: 2, street: "flop", board: ["Js", "7h", "2d"] }),
    ]);
    expect(reachedStreets(h)).toEqual(["preflop", "flop"]);
  });
});
