import type { EventView } from "../../api/types";

const STREET_BOARD_COUNT: Record<string, number> = {
  preflop: 0,
  flop: 3,
  turn: 4,
  river: 5,
};

export interface StagedTableState {
  street: string;
  board: string[];
}

export function boardCountForStreet(street: string): number {
  return STREET_BOARD_COUNT[street] ?? 0;
}

export function stagedTableState({
  startStreet,
  finalStreet,
  finalBoard,
  events,
  stagedIndex,
}: {
  startStreet?: string | null;
  finalStreet: string;
  finalBoard: string[];
  events: EventView[];
  stagedIndex: number;
}): StagedTableState {
  if (events.length === 0 || stagedIndex >= events.length) {
    return { street: finalStreet, board: finalBoard };
  }

  const shown = events.slice(0, Math.max(0, stagedIndex));
  const street =
    shown.length > 0
      ? shown[shown.length - 1].street
      : (startStreet ?? events[0]?.street ?? finalStreet);
  return {
    street,
    board: finalBoard.slice(0, Math.min(finalBoard.length, boardCountForStreet(street))),
  };
}

export interface SeatAction {
  verb: string | null;
  chips: number;
}

// A villain's felt label (last verb + chips in front) at the narrated point of a
// playback batch. The server's view holds only the batch's FINAL street, so a
// seat that calls the flop and acts again on the turn would otherwise show no
// flop "Call" at all. Built from the narrated events only, so it can never lead
// the log; `baseline` is each seat's label when the batch began. Null once the
// batch has fully played (or is empty): the server's view is then the truth.
export function stagedSeatActions({
  baseline,
  startStreet,
  events,
  stagedIndex,
}: {
  baseline: ReadonlyMap<string, SeatAction>;
  startStreet?: string | null;
  events: EventView[];
  stagedIndex: number;
}): Map<string, SeatAction> | null {
  if (events.length === 0 || stagedIndex >= events.length) return null;

  const shown = events.slice(0, Math.max(0, stagedIndex));
  const batchStreet = startStreet ?? events[0].street;
  const street = shown.length > 0 ? shown[shown.length - 1].street : batchStreet;

  const seats = new Map<string, SeatAction>();
  for (const [position, seat] of baseline) {
    if (street === batchStreet) seats.set(position, { ...seat });
    else seats.set(position, { verb: seat.verb === "fold" ? "fold" : null, chips: 0 });
  }
  for (const e of shown) {
    const seat = seats.get(e.position) ?? { verb: null, chips: 0 };
    if (e.action === "fold") seat.verb = "fold";
    else if (e.street === street) {
      seat.chips += e.amount_bb;
      if (e.action !== "post") seat.verb = e.action;
    }
    seats.set(e.position, seat);
  }
  return seats;
}
