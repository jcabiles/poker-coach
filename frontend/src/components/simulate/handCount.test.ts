import { describe, expect, it } from "vitest";

import {
  atBlindCheckGate,
  BLIND_CHECK_HAND_GATE,
  completedHands,
  gateProgressPct,
} from "./handCount";

// The client half of the one number the client and the server must agree about
// (spec para 11). The server pins its own half in backend/tests; these are the
// cases that catch the two wrong derivations, both of which have been written
// into an approved document at some point:
//
//   • `hand_no - 1` (a hand late)  fails "hand 200 settled counts 200"
//   • `hand_no`     (a hand early) fails "hand 200 live counts 199"
//
// Every assertion below is one of those two, the gate boundary either side of
// them, or the no-session case.

function hand(hand_no: number, hand_over: boolean) {
  return { hand_no, hand_over };
}

describe("completedHands", () => {
  it("counts 199 while hand 200 is still live", () => {
    // Catches the off-by-one that bars the deal mid-hand.
    expect(completedHands(hand(200, false))).toBe(199);
  });

  it("counts 200 once hand 200 settles", () => {
    // Catches the off-by-one that fires the gate a hand late.
    expect(completedHands(hand(200, true))).toBe(200);
  });

  it("counts the first hand only after it is over", () => {
    expect(completedHands(hand(1, false))).toBe(0);
    expect(completedHands(hand(1, true))).toBe(1);
  });

  it("keeps counting past the gate", () => {
    expect(completedHands(hand(201, false))).toBe(200);
    expect(completedHands(hand(201, true))).toBe(201);
  });

  it("reports zero when there is no hand at all", () => {
    // A restoring / just-left table renders the counter before any hand exists.
    expect(completedHands(null)).toBe(0);
    expect(completedHands(undefined)).toBe(0);
  });
});

describe("atBlindCheckGate", () => {
  it("is closed at 199 completed and open at 200", () => {
    expect(atBlindCheckGate(hand(BLIND_CHECK_HAND_GATE, false))).toBe(false);
    expect(atBlindCheckGate(hand(BLIND_CHECK_HAND_GATE, true))).toBe(true);
  });

  it("is still closed on the hand before the boundary", () => {
    expect(atBlindCheckGate(hand(BLIND_CHECK_HAND_GATE - 1, true))).toBe(false);
  });

  it("stays open past the boundary, matching the server's >= predicate", () => {
    expect(atBlindCheckGate(hand(BLIND_CHECK_HAND_GATE + 5, true))).toBe(true);
  });
});

describe("gateProgressPct", () => {
  it("draws nothing before the first hand is finished", () => {
    expect(gateProgressPct(hand(1, false))).toBe(0);
  });

  it("tracks completed hands, not the hand being played", () => {
    expect(gateProgressPct(hand(5, true))).toBe(2.5);
    expect(gateProgressPct(hand(5, false))).toBe(2);
  });

  it("is full at the gate and clamps past it", () => {
    expect(gateProgressPct(hand(BLIND_CHECK_HAND_GATE, true))).toBe(100);
    expect(gateProgressPct(hand(BLIND_CHECK_HAND_GATE + 60, true))).toBe(100);
  });
});
