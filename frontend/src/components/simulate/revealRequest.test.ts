import { describe, expect, it } from "vitest";

import type { HandRevealView, ShowdownSeatView } from "../../api/types";
import {
  applyRevealError,
  applyRevealResponse,
  initialRevealState,
  resetForHand,
  toggleReveal,
} from "./revealRequest";

// Tests for the reveal state machine. The three "races" blocks below are the
// acceptance criteria for the HIGH finding both spec reviewers raised: a
// response that outlives the request must never be applied.

function seat(seat_index: number, delta_bb = 1.5): ShowdownSeatView {
  return { seat_index, hole_cards: ["Ah", "Kd"], delta_bb };
}

function ok(seats: ShowdownSeatView[], scope = "all"): HandRevealView {
  return { available: true, scope, seats };
}

describe("toggleReveal", () => {
  it("first click activates the scope and asks for a fetch", () => {
    const { state, request } = toggleReveal(initialRevealState(7), "last-in");
    expect(state.scope).toBe("last-in");
    expect(state.pending).toBe(true);
    expect(request).toEqual({ handId: 7, scope: "last-in", gen: 1 });
  });

  it("clicking the ACTIVE scope hides again and fetches nothing", () => {
    let { state } = toggleReveal(initialRevealState(7), "all");
    state = applyRevealResponse(state, ok([seat(3)]), { handId: 7, scope: "all", gen: 1 });
    expect(state.bySeat.size).toBe(1);

    const hidden = toggleReveal(state, "all");
    expect(hidden.state.scope).toBeNull();
    expect(hidden.state.bySeat.size).toBe(0);
    expect(hidden.request).toBeNull();
  });

  it("switching scope clears cards rather than showing more than it claims", () => {
    let { state } = toggleReveal(initialRevealState(7), "all");
    state = applyRevealResponse(state, ok([seat(3), seat(4)]), {
      handId: 7,
      scope: "all",
      gen: 1,
    });
    const swapped = toggleReveal(state, "last-in");
    expect(swapped.state.scope).toBe("last-in");
    expect(swapped.state.bySeat.size).toBe(0);
    expect(swapped.request).toEqual({ handId: 7, scope: "last-in", gen: 2 });
  });

  it("generation increases monotonically across every action", () => {
    const s0 = initialRevealState(7);
    const s1 = toggleReveal(s0, "all").state;
    const s2 = toggleReveal(s1, "last-in").state;
    const s3 = toggleReveal(s2, "last-in").state; // hide
    const s4 = resetForHand(s3, 99);
    expect([s0.gen, s1.gen, s2.gen, s3.gen, s4.gen]).toEqual([0, 1, 2, 3, 4]);
  });
});

describe("applyRevealResponse", () => {
  it("keys revealed seats by seat_index", () => {
    const { state, request } = toggleReveal(initialRevealState(7), "all");
    const next = applyRevealResponse(state, ok([seat(2, -3), seat(5, 8)]), request!);
    expect([...next.bySeat.keys()].sort()).toEqual([2, 5]);
    expect(next.bySeat.get(5)?.delta_bb).toBe(8);
    expect(next.pending).toBe(false);
  });

  it("available:false surfaces as unavailable, not as a silent no-op", () => {
    const { state, request } = toggleReveal(initialRevealState(7), "all");
    const next = applyRevealResponse(
      state,
      { available: false, scope: "all", seats: [] },
      request!,
    );
    expect(next.unavailable).toBe(true);
    expect(next.pending).toBe(false);
    expect(next.bySeat.size).toBe(0);
  });
});

describe("races — a response must never outlive its request", () => {
  it("CASE 1: reveal, then toggle off BEFORE the response lands", () => {
    const { state: pending, request } = toggleReveal(initialRevealState(7), "all");
    // User hides again while the fetch is still out.
    const hidden = toggleReveal(pending, "all").state;
    // The original response finally arrives.
    const after = applyRevealResponse(hidden, ok([seat(1), seat(2)]), request!);

    expect(after).toBe(hidden); // untouched, same object
    expect(after.scope).toBeNull();
    expect(after.bySeat.size).toBe(0);
  });

  it("CASE 2: last-in then all, responses arrive REVERSED", () => {
    const first = toggleReveal(initialRevealState(7), "last-in");
    const second = toggleReveal(first.state, "all");

    // The newer 'all' response lands first.
    let state = applyRevealResponse(
      second.state,
      ok([seat(1), seat(2), seat(3)], "all"),
      second.request!,
    );
    expect(state.scope).toBe("all");
    expect(state.bySeat.size).toBe(3);

    // The stale 'last-in' response lands afterwards and must be discarded.
    const after = applyRevealResponse(state, ok([seat(1)], "last-in"), first.request!);
    expect(after).toBe(state);
    expect(after.scope).toBe("all");
    expect(after.bySeat.size).toBe(3);
  });

  it("CASE 3: reveal hand A, open hand B, then A's response arrives", () => {
    const handA = toggleReveal(initialRevealState(101), "all");
    const handB = resetForHand(handA.state, 202);

    const after = applyRevealResponse(handB, ok([seat(1), seat(4), seat(6)]), handA.request!);

    expect(after).toBe(handB);
    expect(after.handId).toBe(202);
    expect(after.bySeat.size).toBe(0); // hand A's cards never reach hand B
    expect(after.scope).toBeNull();
  });

  it("a late failure cannot clear a newer request's pending flag", () => {
    const first = toggleReveal(initialRevealState(7), "last-in");
    const second = toggleReveal(first.state, "all");
    const after = applyRevealError(second.state, first.request!);
    expect(after).toBe(second.state);
    expect(after.pending).toBe(true);
  });

  it("re-revealing the SAME scope after hiding is not satisfied by the old response", () => {
    // gen is what separates these; handId and scope are identical.
    const firstAsk = toggleReveal(initialRevealState(7), "all");
    const hidden = toggleReveal(firstAsk.state, "all").state;
    const secondAsk = toggleReveal(hidden, "all");
    expect(secondAsk.request!.gen).not.toBe(firstAsk.request!.gen);

    const after = applyRevealResponse(secondAsk.state, ok([seat(1)]), firstAsk.request!);
    expect(after).toBe(secondAsk.state);
    expect(after.pending).toBe(true); // still waiting on its own answer
  });
});

describe("applyRevealError", () => {
  it("is non-fatal: clears the reveal and leaves the felt face-down", () => {
    const { state, request } = toggleReveal(initialRevealState(7), "all");
    const after = applyRevealError(state, request!);
    expect(after.scope).toBeNull();
    expect(after.pending).toBe(false);
    expect(after.unavailable).toBe(false);
    expect(after.bySeat.size).toBe(0);
  });
});

describe("resetForHand", () => {
  it("clears everything and retargets the hand", () => {
    let { state, request } = toggleReveal(initialRevealState(7), "all");
    state = applyRevealResponse(state, ok([seat(1)]), request!);
    const next = resetForHand(state, 42);
    expect(next.handId).toBe(42);
    expect(next.scope).toBeNull();
    expect(next.bySeat.size).toBe(0);
    expect(next.unavailable).toBe(false);
  });
});
