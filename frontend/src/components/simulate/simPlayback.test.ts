import { describe, expect, it } from "vitest";

import type { EventView } from "../../api/types";
import { stagedSeatActions, stagedTableState } from "./simPlayback";

function event(street: string, position = "BTN"): EventView {
  return {
    seat_index: 1,
    position,
    action: "call",
    amount_bb: 1,
    street,
    all_in: false,
  };
}

describe("stagedTableState", () => {
  const finalBoard = ["As", "Kd", "7c", "2h", "Jd"];

  it("keeps a preflop fold playout from revealing the final board early", () => {
    const events = [event("preflop", "BTN"), event("preflop", "SB")];

    expect(
      stagedTableState({
        finalStreet: "flop",
        finalBoard: finalBoard.slice(0, 3),
        events,
        stagedIndex: 0,
      }),
    ).toEqual({ street: "preflop", board: [] });

    expect(
      stagedTableState({
        finalStreet: "flop",
        finalBoard: finalBoard.slice(0, 3),
        events,
        stagedIndex: events.length,
      }),
    ).toEqual({ street: "flop", board: finalBoard.slice(0, 3) });
  });

  it("keeps a big-blind preflop fold face-down when the first remaining bot action is on the flop", () => {
    const events = [event("flop", "SB"), event("flop", "BTN")];

    expect(
      stagedTableState({
        startStreet: "preflop",
        finalStreet: "river",
        finalBoard,
        events,
        stagedIndex: 0,
      }),
    ).toEqual({ street: "preflop", board: [] });

    expect(
      stagedTableState({
        startStreet: "preflop",
        finalStreet: "river",
        finalBoard,
        events,
        stagedIndex: 1,
      }),
    ).toEqual({ street: "flop", board: finalBoard.slice(0, 3) });
  });

  it("reveals streets only when the narrated event prefix reaches them", () => {
    const events = [
      event("preflop", "BTN"),
      event("flop", "SB"),
      event("turn", "BB"),
      event("river", "BTN"),
    ];

    expect(stagedTableState({ finalStreet: "river", finalBoard, events, stagedIndex: 1 })).toEqual({
      street: "preflop",
      board: [],
    });
    expect(stagedTableState({ finalStreet: "river", finalBoard, events, stagedIndex: 2 })).toEqual({
      street: "flop",
      board: finalBoard.slice(0, 3),
    });
    expect(stagedTableState({ finalStreet: "river", finalBoard, events, stagedIndex: 3 })).toEqual({
      street: "turn",
      board: finalBoard.slice(0, 4),
    });
    expect(stagedTableState({ finalStreet: "river", finalBoard, events, stagedIndex: 4 })).toEqual({
      street: "river",
      board: finalBoard,
    });
  });

  it("keeps the current postflop board visible before the next bot action narrates", () => {
    const events = [event("flop", "SB"), event("flop", "BB")];

    expect(
      stagedTableState({
        finalStreet: "turn",
        finalBoard: finalBoard.slice(0, 4),
        events,
        stagedIndex: 0,
      }),
    ).toEqual({ street: "flop", board: finalBoard.slice(0, 3) });
  });
});

function act(street: string, position: string, action: string, amount_bb = 0): EventView {
  return { seat_index: 1, position, action, amount_bb, street, all_in: false };
}

describe("stagedSeatActions", () => {
  // Hero folded preflop; the bots play the flop and turn in one batch.
  const events = [
    act("preflop", "CO", "call", 2),
    act("flop", "BB", "check"),
    act("flop", "CO", "bet", 3),
    act("flop", "BB", "call", 3),
    act("turn", "BB", "check"),
    act("turn", "CO", "check"),
  ];
  const base = { startStreet: "preflop", events };
  const baseline = new Map([
    ["BTN", { verb: "raise", chips: 2.5 }],
    ["SB", { verb: "fold", chips: 0 }],
    ["BB", { verb: null, chips: 1 }],
    ["CO", { verb: null, chips: 0 }],
  ]);

  it("shows a call the moment it is narrated, though the seat acts again later", () => {
    const m = stagedSeatActions({ ...base, baseline, stagedIndex: 1 });
    expect(m?.get("CO")).toEqual({ verb: "call", chips: 2 });
  });

  it("keeps the batch-start labels and chips on the starting street", () => {
    const m = stagedSeatActions({ ...base, baseline, stagedIndex: 1 });
    expect(m?.get("BTN")).toEqual({ verb: "raise", chips: 2.5 });
    expect(m?.get("BB")).toEqual({ verb: null, chips: 1 });
  });

  it("clears verbs and chips when the street advances, but a fold persists", () => {
    const m = stagedSeatActions({ ...base, baseline, stagedIndex: 2 });
    expect(m?.get("BB")).toEqual({ verb: "check", chips: 0 });
    expect(m?.get("BTN")).toEqual({ verb: null, chips: 0 });
    expect(m?.get("SB")).toEqual({ verb: "fold", chips: 0 });
    expect(m?.get("CO")).toEqual({ verb: null, chips: 0 });
  });

  it("shows checks and calls on later streets, summing the street's chips", () => {
    const flop = stagedSeatActions({ ...base, baseline, stagedIndex: 4 });
    expect(flop?.get("CO")).toEqual({ verb: "bet", chips: 3 });
    expect(flop?.get("BB")).toEqual({ verb: "call", chips: 3 });
    const turn = stagedSeatActions({ ...base, baseline, stagedIndex: 6 });
    expect(turn).toBeNull();
    const midTurn = stagedSeatActions({ ...base, baseline, stagedIndex: 5 });
    expect(midTurn?.get("BB")).toEqual({ verb: "check", chips: 0 });
    expect(midTurn?.get("CO")).toEqual({ verb: null, chips: 0 });
  });

  it("never lets a blind post count as an action, but its chips do", () => {
    const m = stagedSeatActions({
      startStreet: "preflop",
      events: [act("preflop", "SB", "post", 0.5), act("preflop", "BB", "post", 1)],
      baseline: new Map(),
      stagedIndex: 1,
    });
    expect(m?.get("SB")).toEqual({ verb: null, chips: 0.5 });
    expect(m?.has("BB")).toBe(false);
  });

  it("returns null when there is nothing left to play, so the server's view rules", () => {
    expect(stagedSeatActions({ ...base, baseline, stagedIndex: events.length })).toBeNull();
    expect(stagedSeatActions({ ...base, events: [], baseline, stagedIndex: 0 })).toBeNull();
  });
});
