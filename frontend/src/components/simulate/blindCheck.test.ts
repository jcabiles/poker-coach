import { describe, expect, it } from "vitest";

import type { ArchetypeGuess, BlindCheckSubmitRequest, BlindCheckView } from "../../api/types";
import {
  ARCHETYPE_OPTIONS,
  archetypeGloss,
  archetypeName,
  HOUSE_LINEUP,
  HOUSE_SEATS,
  isOwnSubmission,
} from "./blindCheck";

// Two things are pinned here.
//
// 1. THE DISCLOSED LINEUP. The card tells the player the house seats the same
//    eight every time and lists the counts. That is copied from a backend
//    roster which is not on the wire, so nothing at runtime can catch it going
//    stale — the union keys catch a NEW archetype at compile time, and the sum
//    below catches a changed COUNT, which the union cannot see. Between them
//    the card cannot quietly assert a false lineup.
// 2. THE OWNERSHIP RULE. Five scenarios a real server can return, plus the
//    re-ordering case, which exists to make the by-seat comparison a recorded
//    decision rather than an accident of the server happening to echo the order
//    it was sent.

function answer(seat_index: number, guess: ArchetypeGuess) {
  return { seat_index, guess };
}

function sent(
  ...guesses: { seat_index: number; guess: ArchetypeGuess }[]
): BlindCheckSubmitRequest {
  return { skipped: false, guesses };
}

const skipSent: BlindCheckSubmitRequest = { skipped: true, guesses: [] };

function stored(...rows: [number, ArchetypeGuess, ArchetypeGuess][]): BlindCheckView {
  const guesses = rows.map(([seat_index, guess, actual]) => ({
    seat_index,
    guess,
    actual,
    correct: guess === actual,
  }));
  return {
    seats: rows.map((r) => r[0]),
    submitted: true,
    skipped: false,
    guesses,
    score: guesses.filter((g) => g.correct).length,
  };
}

const storedSkip: BlindCheckView = {
  seats: [1, 4, 6],
  submitted: true,
  skipped: true,
  guesses: [],
  score: null,
};

describe("the six options", () => {
  it("offers every archetype the player can be scored against, in spec order", () => {
    // Order is spec para 13's; completeness is the ArchetypeGuess union's. A
    // seventh archetype fails to compile in blindCheck.ts before it reaches
    // this assertion, which is the point of the rank-map derivation.
    expect(ARCHETYPE_OPTIONS).toEqual([
      "nit",
      "tag",
      "lag",
      "maniac",
      "calling_station",
      "passive_fish",
    ]);
  });

  it("offers each name exactly once", () => {
    expect(new Set(ARCHETYPE_OPTIONS).size).toBe(ARCHETYPE_OPTIONS.length);
  });
});

describe("the disclosed house lineup", () => {
  it("adds up to the eight non-hero seats it claims", () => {
    // The assertion that catches a roster whose COUNTS changed — the case the
    // union cannot see, and the one that would leave the card asserting a false
    // lineup under a heading saying it is the truth.
    const total = Object.values(HOUSE_LINEUP).reduce((a, b) => a + b, 0);
    expect(total).toBe(HOUSE_SEATS);
  });

  it("matches the roster in backend/app/domain/table/play.py:44-54", () => {
    expect(HOUSE_LINEUP).toEqual({
      passive_fish: 2,
      tag: 2,
      calling_station: 1,
      nit: 1,
      lag: 1,
      maniac: 1,
    });
  });

  it("covers exactly the six options the player is offered", () => {
    expect(Object.keys(HOUSE_LINEUP).sort()).toEqual([...ARCHETYPE_OPTIONS].sort());
  });
});

describe("display names and glosses", () => {
  it("renders the wire values the way the felt and the rail sheet do", () => {
    // Character-for-character: the card and the table must not disagree about
    // what the answer was called.
    expect(ARCHETYPE_OPTIONS.map(archetypeName)).toEqual([
      "Nit",
      "Tag",
      "Lag",
      "Maniac",
      "Calling Station",
      "Passive Fish",
    ]);
  });

  it("gives every option a behaviour gloss, and expands the two acronyms", () => {
    for (const value of ARCHETYPE_OPTIONS) {
      expect(archetypeGloss(value).length).toBeGreaterThan(0);
    }
    // The whole reason the gloss exists: "Tag" and "Lag" are unexpanded
    // acronyms Title-Cased into ordinary words, and a Challenge player has
    // never seen either term in the app.
    expect(archetypeGloss("tag")).toContain("tight-aggressive");
    expect(archetypeGloss("lag")).toContain("loose-aggressive");
  });
});

describe("isOwnSubmission", () => {
  const mine = sent(answer(1, "nit"), answer(4, "lag"), answer(6, "maniac"));

  it("accepts the stored result when it echoes what was sent", () => {
    expect(
      isOwnSubmission(mine, stored([1, "nit", "nit"], [4, "lag", "tag"], [6, "maniac", "maniac"])),
    ).toBe(true);
  });

  it("accepts the same three names returned in a different order", () => {
    // A DECISION, not an accident. The comparison is by seat because the
    // question is "is this the same answer"; the server echoing the order it
    // was sent is an implementation detail of two independent pieces of code,
    // and a re-ordered echo of the player's own names is still their answer.
    expect(
      isOwnSubmission(mine, stored([6, "maniac", "maniac"], [1, "nit", "nit"], [4, "lag", "tag"])),
    ).toBe(true);
  });

  it("rejects a stored result whose names are all different", () => {
    expect(
      isOwnSubmission(mine, stored([1, "tag", "nit"], [4, "nit", "tag"], [6, "lag", "maniac"])),
    ).toBe(false);
  });

  it("rejects a stored result differing in a single seat", () => {
    // The tightest case: two of three match, so anything comparing counts or
    // sampling one row would wrongly claim another window's answer.
    expect(
      isOwnSubmission(mine, stored([1, "nit", "nit"], [4, "tag", "tag"], [6, "maniac", "maniac"])),
    ).toBe(false);
  });

  it("rejects another window's SKIP against this window's answers", () => {
    expect(isOwnSubmission(mine, storedSkip)).toBe(false);
  });

  it("rejects this window's skip against a check someone else answered", () => {
    expect(
      isOwnSubmission(
        skipSent,
        stored([1, "nit", "nit"], [4, "lag", "tag"], [6, "maniac", "maniac"]),
      ),
    ).toBe(false);
  });

  it("reads two identical skips as this window's own", () => {
    // Genuinely indistinguishable, and harmless: the stored result is the same
    // answer either way, so there is nothing to misattribute.
    expect(isOwnSubmission(skipSent, storedSkip)).toBe(true);
  });
});
