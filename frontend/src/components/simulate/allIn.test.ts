import { describe, expect, it } from "vitest";

import { isAllIn } from "./allIn";

// The confirm step is only worth having if it fires on exactly one button. The
// cases below are the two ways to get that wrong:
//
//   • reading a bet/raise size as chips SPENT rather than a street TOTAL, which
//     never reaches the ceiling and so never confirms a real shove;
//   • reading a call's amount against the ceiling (calls carry no max_bb),
//     which confirms nothing or confirms everything.

describe("isAllIn — bet and raise are street totals measured against max_bb", () => {
  it("is a shove when the offered total reaches the engine's ceiling", () => {
    expect(isAllIn({ action: "raise", offeredBb: 97, maxBb: 97, heroStackBb: 95 })).toBe(true);
  });

  it("is not a shove one big blind below the ceiling", () => {
    expect(isAllIn({ action: "raise", offeredBb: 96, maxBb: 97, heroStackBb: 95 })).toBe(false);
  });

  it("tolerates a rounded size landing a hair under the ceiling", () => {
    // The two-size offers round to 1dp, the ceiling to 2dp.
    expect(isAllIn({ action: "bet", offeredBb: 42.49, maxBb: 42.5, heroStackBb: 42.5 })).toBe(true);
  });

  it("never claims a shove when the ceiling is unknown", () => {
    // A bet quoted with no max_bb: unprovable, so it costs no confirm.
    expect(isAllIn({ action: "bet", offeredBb: 40, maxBb: null, heroStackBb: 40 })).toBe(false);
  });

  it("does not mistake the stack for the ceiling on a raise", () => {
    // Hero has 95bb behind but has already put 2bb in this street, so the
    // ceiling is 97. A raise TO 95 is not a shove.
    expect(isAllIn({ action: "raise", offeredBb: 95, maxBb: 97, heroStackBb: 95 })).toBe(false);
  });
});

describe("isAllIn — a call is chips owed, measured against the stack", () => {
  it("is a shove when the call takes every chip behind", () => {
    expect(isAllIn({ action: "call", offeredBb: 40, heroStackBb: 40 })).toBe(true);
  });

  it("is not a shove when chips are left behind", () => {
    expect(isAllIn({ action: "call", offeredBb: 12, heroStackBb: 40 })).toBe(false);
  });

  it("still reads as a shove if the amount owed exceeds the stack", () => {
    // The engine caps it, so this is defence rather than a live case.
    expect(isAllIn({ action: "call", offeredBb: 60, heroStackBb: 40 })).toBe(true);
  });
});

describe("isAllIn — everything else commits nothing", () => {
  it("never confirms a fold or a check", () => {
    expect(isAllIn({ action: "fold", heroStackBb: 40 })).toBe(false);
    expect(isAllIn({ action: "check", heroStackBb: 40 })).toBe(false);
  });

  it("never confirms with no chips behind", () => {
    expect(isAllIn({ action: "call", offeredBb: 5, heroStackBb: 0 })).toBe(false);
  });

  it("never confirms an option with no size on it", () => {
    expect(isAllIn({ action: "call", offeredBb: null, heroStackBb: 40 })).toBe(false);
  });
});
