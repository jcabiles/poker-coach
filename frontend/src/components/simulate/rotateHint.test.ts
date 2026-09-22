import { describe, expect, it } from "vitest";

import { type RotateHintState, shouldShowRotateHint } from "./rotateHint";

// Every combination of the four flags, not a sample: the predicate is a
// conjunction, so the only bugs it can have are a dropped term or an inverted
// one, and both hide from any test that varies one flag at a time. Sixteen
// rows is the whole input space.

const FLAGS = ["phone", "portrait", "atTable", "dismissed"] as const;

/** The 16 states, built from the bits of 0–15 so none can be forgotten. */
function allStates(): RotateHintState[] {
  const states: RotateHintState[] = [];
  for (let bits = 0; bits < 16; bits += 1) {
    states.push({
      phone: (bits & 1) !== 0,
      portrait: (bits & 2) !== 0,
      atTable: (bits & 4) !== 0,
      dismissed: (bits & 8) !== 0,
    });
  }
  return states;
}

function describeState(s: RotateHintState): string {
  return FLAGS.map((f) => `${f}=${s[f]}`).join(" ");
}

describe("shouldShowRotateHint", () => {
  it("shows on a phone held upright at a table, undismissed — the one true case", () => {
    expect(
      shouldShowRotateHint({ phone: true, portrait: true, atTable: true, dismissed: false }),
    ).toBe(true);
  });

  it("is true for exactly one of the sixteen possible states", () => {
    const shown = allStates().filter(shouldShowRotateHint);
    expect(shown.map(describeState)).toEqual([
      "phone=true portrait=true atTable=true dismissed=false",
    ]);
  });

  it.each(allStates().map((s) => [describeState(s), s] as const))(
    "%s",
    (_label, state: RotateHintState) => {
      const expected = state.phone && state.portrait && state.atTable && !state.dismissed;
      expect(shouldShowRotateHint(state)).toBe(expected);
    },
  );

  it("never shows off the phone gate, however the other three fall", () => {
    // A 1280px desktop in a portrait-ish window is still a desktop.
    for (const state of allStates().filter((s) => !s.phone)) {
      expect(shouldShowRotateHint(state)).toBe(false);
    }
  });

  it("never shows in landscape — the orientation the hint is pointing at", () => {
    for (const state of allStates().filter((s) => !s.portrait)) {
      expect(shouldShowRotateHint(state)).toBe(false);
    }
  });

  it("never shows away from a table — the sit-down and restoring screens", () => {
    for (const state of allStates().filter((s) => !s.atTable)) {
      expect(shouldShowRotateHint(state)).toBe(false);
    }
  });

  it("stays gone once dismissed, even on the screen it was written for", () => {
    for (const state of allStates().filter((s) => s.dismissed)) {
      expect(shouldShowRotateHint(state)).toBe(false);
    }
  });
});
