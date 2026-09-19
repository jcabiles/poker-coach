import { describe, expect, it } from "vitest";

import type { ArchetypeGuess, TableSize } from "../../api/types";
import {
  ARCHETYPE_OPTIONS,
  HOUSE_LINEUP,
  HOUSE_LINEUP_6MAX,
  HOUSE_SEATS,
  HOUSE_SEATS_6MAX,
  houseLineupFor,
  houseSeatsFor,
} from "./blindCheck";

// simulate-6max S1 (T7), owner decision D4. `blindCheck.test.ts` pins the 9-max
// disclosure; this file pins the 6-max one and the switch between them, and is
// separate because no existing test may be edited in this slice.
//
// WHY THIS IS PINNED AT ALL. The disclosed lineup is the blind check's fairness
// argument — the card tells the player the exact multiset it is about to score
// them against. That multiset is hand-copied from a backend roster that does
// NOT ride the wire, so nothing at runtime can notice it going stale. Before
// this slice the card asserted the nine-max lineup at every table; at six seats
// that named a maniac and two passive fish who are not seated, and scored the
// player's guesses against them.
//
// The counts below are the ONE place the 6-max roster is written down on this
// side of the wire, so they are stated as literals rather than derived from the
// thing under test. Their source is `backend/app/domain/table/play.py`'s
// `LINEUP_6MAX` — nit, TAG, TAG, LAG, calling station (two TAGs is deliberate).
const SEATED_AT_SIX: Record<ArchetypeGuess, number> = {
  nit: 1,
  tag: 2,
  lag: 1,
  maniac: 0,
  calling_station: 1,
  passive_fish: 0,
};

function total(lineup: Record<ArchetypeGuess, number>): number {
  return ARCHETYPE_OPTIONS.reduce((sum, value) => sum + lineup[value], 0);
}

describe("the 6-max disclosed roster", () => {
  it("is nit, TAG, TAG, LAG, calling station — no maniac and no passive fish", () => {
    expect(HOUSE_LINEUP_6MAX).toEqual(SEATED_AT_SIX);
  });

  it("adds up to the five non-hero seats at a six-seat table", () => {
    expect(total(HOUSE_LINEUP_6MAX)).toBe(HOUSE_SEATS_6MAX);
    expect(HOUSE_SEATS_6MAX).toBe(5);
  });

  it("names nobody who is not seated", () => {
    // The failure this catches: the card listing an archetype with count 0,
    // which reads to the player as "one of these is at your table".
    const named = ARCHETYPE_OPTIONS.filter((value) => HOUSE_LINEUP_6MAX[value] > 0);
    expect(named).toEqual(["nit", "tag", "lag", "calling_station"]);
  });
});

describe("the disclosure follows the table's seat count", () => {
  it("discloses the six-max roster at six seats", () => {
    expect(houseLineupFor(6)).toEqual(HOUSE_LINEUP_6MAX);
    expect(houseSeatsFor(6)).toBe(HOUSE_SEATS_6MAX);
  });

  it("leaves the nine-max disclosure exactly as it was", () => {
    expect(houseLineupFor(9)).toEqual(HOUSE_LINEUP);
    expect(houseSeatsFor(9)).toBe(HOUSE_SEATS);
    expect(total(HOUSE_LINEUP)).toBe(HOUSE_SEATS);
    expect(HOUSE_SEATS).toBe(8);
  });

  it("discloses a different roster at each size", () => {
    // Without this the two branches could return the same object and every
    // assertion above would still pass.
    const sizes: TableSize[] = [6, 9];
    const [six, nine] = sizes.map(houseLineupFor);
    expect(six).not.toEqual(nine);
    expect(houseSeatsFor(6)).not.toBe(houseSeatsFor(9));
  });
});
