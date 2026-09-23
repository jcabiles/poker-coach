import { describe, expect, it } from "vitest";

import { nextToolbarIndex } from "./toolbarKeys";

// Four buttons, the dock's tallest case (facing a raise).
const N = 4;

describe("nextToolbarIndex — horizontal (the bottom dock and desktop)", () => {
  it("moves right and left one button at a time", () => {
    expect(nextToolbarIndex("ArrowRight", "horizontal", 1, N)).toBe(2);
    expect(nextToolbarIndex("ArrowLeft", "horizontal", 1, N)).toBe(0);
  });

  it("wraps at both ends", () => {
    expect(nextToolbarIndex("ArrowRight", "horizontal", N - 1, N)).toBe(0);
    expect(nextToolbarIndex("ArrowLeft", "horizontal", 0, N)).toBe(N - 1);
  });

  it("ignores ArrowUp and ArrowDown, as the horizontal bar always has", () => {
    expect(nextToolbarIndex("ArrowUp", "horizontal", 2, N)).toBeNull();
    expect(nextToolbarIndex("ArrowDown", "horizontal", 2, N)).toBeNull();
  });
});

describe("nextToolbarIndex — vertical (the phone-landscape column)", () => {
  it("moves down and up one button at a time", () => {
    expect(nextToolbarIndex("ArrowDown", "vertical", 1, N)).toBe(2);
    expect(nextToolbarIndex("ArrowUp", "vertical", 1, N)).toBe(0);
  });

  it("wraps at both ends", () => {
    expect(nextToolbarIndex("ArrowDown", "vertical", N - 1, N)).toBe(0);
    expect(nextToolbarIndex("ArrowUp", "vertical", 0, N)).toBe(N - 1);
  });

  it("keeps ArrowRight and ArrowLeft working", () => {
    expect(nextToolbarIndex("ArrowRight", "vertical", 1, N)).toBe(2);
    expect(nextToolbarIndex("ArrowLeft", "vertical", 0, N)).toBe(N - 1);
  });
});

describe("nextToolbarIndex — both orientations", () => {
  for (const orientation of ["horizontal", "vertical"] as const) {
    it(`${orientation}: Home and End jump to the first and last button`, () => {
      expect(nextToolbarIndex("Home", orientation, 2, N)).toBe(0);
      expect(nextToolbarIndex("End", orientation, 1, N)).toBe(N - 1);
    });

    it(`${orientation}: leaves every other key to the caller`, () => {
      for (const key of ["Enter", " ", "Escape", "Tab", "f", "R"]) {
        expect(nextToolbarIndex(key, orientation, 1, N)).toBeNull();
      }
    });

    it(`${orientation}: a one-button bar keeps focus where it is`, () => {
      expect(nextToolbarIndex("ArrowRight", orientation, 0, 1)).toBe(0);
      expect(nextToolbarIndex("ArrowLeft", orientation, 0, 1)).toBe(0);
    });

    it(`${orientation}: an empty bar has nowhere to go`, () => {
      expect(nextToolbarIndex("ArrowRight", orientation, 0, 0)).toBeNull();
      expect(nextToolbarIndex("Home", orientation, 0, 0)).toBeNull();
    });
  }
});
