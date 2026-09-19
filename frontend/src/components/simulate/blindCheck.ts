import type {
  ArchetypeGuess,
  BlindCheckSubmitRequest,
  BlindCheckView,
  TableSize,
} from "../../api/types";
import { personaLabel } from "./personaLabel";

// Two-mode Simulate (T8) — the hand-200 blind check's pure parts: the six names
// the player picks from, the lineup the card discloses, and the one rule that
// decides whether a stored result is this window's answer. No React and no
// fetch, so all of it can be pinned; the dialog owns only the markup.
//
// EVERY COLLECTION HERE IS KEYED BY THE `ArchetypeGuess` UNION, deliberately.
// A `Record<ArchetypeGuess, T>` makes a seventh archetype a COMPILE error at
// each of these three sites rather than a name silently missing from the card,
// a count silently missing from the disclosed lineup, or an option the player
// is scored against but never offered. That mattered enough to be worth the
// slightly awkward derivation of the ordered arrays below, because the lineup
// is the disclosure this screen's honesty argument rests on: it is copied from
// a backend roster that is NOT on the wire, and if the roster changes, the card
// goes on asserting a false lineup under a heading that says it is the truth.
// The union plus `blindCheck.test.ts` is the whole of what connects them —
// there is no generated type and no runtime check on the wire.

/**
 * Display order for the six options (spec para 13): the tight-to-loose
 * aggressive run first, then the two passive rooms. Written as a rank map so
 * the union's exhaustiveness is enforced; the array is derived from it, so the
 * order and the completeness cannot disagree.
 */
const OPTION_RANK: Record<ArchetypeGuess, number> = {
  nit: 0,
  tag: 1,
  lag: 2,
  maniac: 3,
  calling_station: 4,
  passive_fish: 5,
};

export const ARCHETYPE_OPTIONS: readonly ArchetypeGuess[] = (
  Object.keys(OPTION_RANK) as ArchetypeGuess[]
).sort((a, b) => OPTION_RANK[a] - OPTION_RANK[b]);

/**
 * The 9-max house roster, from `backend/app/domain/table/play.py:44-54`: eight
 * seats, fixed composition, identical at every 9-max table. Hand-copied
 * because it does not ride the wire — see the module note on why that is
 * guarded by the union and by a test rather than trusted. Pinned by
 * `blindCheck.test.ts`; unchanged by simulate-6max S1.
 */
export const HOUSE_LINEUP: Record<ArchetypeGuess, number> = {
  nit: 1,
  tag: 2,
  lag: 1,
  maniac: 1,
  calling_station: 1,
  passive_fish: 2,
};

/** Non-hero seats at a 9-max table — what HOUSE_LINEUP must add up to. */
export const HOUSE_SEATS = 8;

/**
 * The 6-max house roster (owner decision D2, 2026-09-18), from
 * `backend/app/domain/table/play.py:59-65` (`LINEUP_6MAX`): nit, TAG, TAG,
 * LAG, calling station — no passive fish, no maniac.
 */
export const HOUSE_LINEUP_6MAX: Record<ArchetypeGuess, number> = {
  nit: 1,
  tag: 2,
  lag: 1,
  maniac: 0,
  calling_station: 1,
  passive_fish: 0,
};

/** Non-hero seats at a 6-max table — what HOUSE_LINEUP_6MAX must add up to. */
export const HOUSE_SEATS_6MAX = 5;

/**
 * The roster the Challenge blind check discloses, keyed by the table's actual
 * seat count (simulate-6max S1, owner decision D4). At six seats the card
 * must not go on asserting the nine-max lineup — see the module note above.
 */
export function houseLineupFor(tableSize: TableSize): Record<ArchetypeGuess, number> {
  return tableSize === 6 ? HOUSE_LINEUP_6MAX : HOUSE_LINEUP;
}

/** What `houseLineupFor(tableSize)` must add up to. */
export function houseSeatsFor(tableSize: TableSize): number {
  return tableSize === 6 ? HOUSE_SEATS_6MAX : HOUSE_SEATS;
}

/**
 * The player-facing name of an archetype, via the same helper the seat plate and
 * the rail sheet use, so the names the player picks from are character-for-
 * character the names they see when the labels come on.
 */
export function archetypeName(value: ArchetypeGuess): string {
  return personaLabel(value);
}

/**
 * What the archetype DOES, in a handful of words.
 *
 * This is not decoration. A Challenge session has suppressed every archetype
 * label since hand 1, so at the moment this card appears the player has never
 * seen any of these six words in the application. Two of them are worse than
 * unfamiliar: "Tag" and "Lag" are unexpanded acronyms that the app-wide Title
 * Case turns into ordinary English words, differing by one letter and sitting
 * next to each other in the grid. Without a gloss the card asks for a deduction
 * in a vocabulary it never taught, which would make the disclosed lineup a
 * formality rather than a fair chance. Each gloss leads with the expansion for
 * exactly that reason.
 *
 * (The "Tag"/"Lag" casing itself comes from the two files that own the label
 * transform, which this ticket may not touch. Flagged, not fixed.)
 */
const ARCHETYPE_BEHAVIOUR: Record<ArchetypeGuess, string> = {
  nit: "ultra-tight: folds unless it is huge",
  tag: "tight-aggressive: few hands, played hard",
  lag: "loose-aggressive: many hands, played hard",
  maniac: "raises relentlessly, with almost anything",
  calling_station: "calls far too much, raises almost never",
  passive_fish: "plays too many hands, then just calls",
};

export function archetypeGloss(value: ArchetypeGuess): string {
  return ARCHETYPE_BEHAVIOUR[value];
}

/**
 * Is the result the server stored the answer THIS window sent?
 *
 * It has to be asked, because first-write-wins means a 200 is not proof the
 * submission landed: another window may have answered first, and the endpoint
 * then returns that stored result instead. Reporting it as the player's own
 * would credit them with a score they did not produce, or blame them for one.
 *
 * Compared BY SEAT, not by position. The server builds its stored list in the
 * order it received, and this dialog always sends in `blind_check.seats` order,
 * so in practice the orders match — but that is a coincidence of two
 * implementations, not a contract, and the question being asked is "is this the
 * same answer", which is about content. A re-ordered echo of the player's own
 * three names is their answer and is reported as such; anything that differs in
 * a single seat's name is not. Two windows that submit identical answers are
 * genuinely indistinguishable and read as "yours", which is harmless: the
 * stored result is the same either way.
 */
export function isOwnSubmission(sent: BlindCheckSubmitRequest, stored: BlindCheckView): boolean {
  if (stored.skipped !== sent.skipped) return false;
  if (stored.guesses.length !== sent.guesses.length) return false;
  const storedBySeat = new Map(stored.guesses.map((g) => [g.seat_index, g.guess]));
  // A repeated seat would collapse the map and let a short answer match a long
  // one; the server rejects repeats with a 400 and the dialog cannot produce
  // them, but the sizes are compared so this does not rest on that.
  if (storedBySeat.size !== stored.guesses.length) return false;
  return sent.guesses.every((a) => storedBySeat.get(a.seat_index) === a.guess);
}
