import type { RefObject } from "react";

import type { SimMode, TableSize } from "../../api/types";

// Simulate — the sit-down screen (two-mode-simulate T6; simulate-6max S1 T5
// added the seat-count split). The player is choosing which ROOM to sit down
// in, not flipping a setting: four printed reservation cards laid on the
// club's baize, two on plain stock and two foil-stamped.
//
// No pre-selection, by design — no room is the default a player drifts into.
// Each card IS the control (a real <button>), so the choice and the sit-down
// are one act; there is no "confirm" step to leave a highlighted default
// sitting on screen. simulate-6max S1 owner decision D3 chose four equal-weight
// cards over a mode card plus a table-size toggle for exactly this reason — a
// toggle needs a default value, which would break the no-pre-selection rule.
//
// The two modes are told apart by four cues that are NOT colour: different
// eyebrow lines, a different corner stamp numeral (1 vs 200), a single rule vs
// a double rule under the room name, and different terms lines. The gilt on
// Challenge is the accent on top of those, never the meaning. The two table
// sizes within a mode share those cues and are told apart only by the room
// name and stamp suffix ("9-max" / "6-max").
//
// This screen names the modes in the player's terms. "Challenge" is not "hides
// persona_type" — it is a table where you work out who you are playing against
// and the names arrive at 200 hands.

type Room = {
  mode: SimMode;
  tableSize: TableSize;
  eyebrow: string;
  name: string;
  stamp: string; // corner stamp numeral — decorative, echoes the terms line
  lede: string;
  terms: string;
  cta: string;
  // The button's accessible name. It REPLACES the card's prose for screen
  // readers, which otherwise announce all 42-54 words of it before reaching a
  // verb and leave an unusable rotor entry.
  //
  // ⚠️ `spokenName` and the visible text must be edited TOGETHER. WCAG "Label
  // in Name" (2.5.3) requires the visible label to appear inside the spoken
  // name, so `spokenName` has to keep containing both `name` and `cta`
  // verbatim — otherwise a voice-control user can no longer say what they can
  // read. They are declared adjacent here so the pairing is impossible to miss;
  // that coupling is the price of the short spoken name.
  spokenName: string;
};

// Order is fixed: the plain mode's two rooms first, then the accented mode's
// two rooms; within a mode, 9-max before 6-max. All four cards are the same
// size and shape — equal weight as choices.
const ROOMS: readonly Room[] = [
  {
    mode: "training",
    tableSize: 9,
    eyebrow: "Play with the read",
    name: "Training · 9-max",
    stamp: "1",
    lede: "Every seat is labelled with how that opponent plays — nit, TAG, maniac — from the very first hand. Read the label, watch what it does to you, and learn the type. Full ring, nine seats.",
    terms: "Names shown · from hand 1 · 9-max",
    cta: "Take this seat",
    spokenName: "Take this seat at the Training 9-max table",
  },
  {
    mode: "training",
    tableSize: 6,
    eyebrow: "Play with the read",
    name: "Training · 6-max",
    stamp: "1",
    lede: "Every seat is labelled with how that opponent plays — nit, TAG, maniac — from the very first hand. Read the label, watch what it does to you, and learn the type. Short-handed, six seats.",
    terms: "Names shown · from hand 1 · 6-max",
    cta: "Take this seat",
    spokenName: "Take this seat at the Training 6-max table",
  },
  {
    mode: "challenge",
    tableSize: 9,
    eyebrow: "Earn the read",
    name: "Challenge · 9-max",
    stamp: "200",
    lede: "The seats keep their names to themselves. You work out who you are up against from the way they play — then at 200 hands the table asks you to name three of them, and the names come out for the rest of the session. Full ring, nine seats.",
    terms: "Names sealed · until hand 200 · 9-max",
    cta: "Take this seat",
    spokenName: "Take this seat at the Challenge 9-max table",
  },
  {
    mode: "challenge",
    tableSize: 6,
    eyebrow: "Earn the read",
    name: "Challenge · 6-max",
    stamp: "200",
    lede: "The seats keep their names to themselves. You work out who you are up against from the way they play — then at 200 hands the table asks you to name three of them, and the names come out for the rest of the session. Short-handed, six seats.",
    terms: "Names sealed · until hand 200 · 6-max",
    cta: "Take this seat",
    spokenName: "Take this seat at the Challenge 6-max table",
  },
];

/** The room whose session is being created right now, or null when idle. Two
 *  rooms can share a `mode` (Training 9-max and Training 6-max), so identity
 *  needs both fields, not `mode` alone. */
export type PendingRoom = { mode: SimMode; tableSize: TableSize } | null;

function isPending(pending: PendingRoom, room: Room): boolean {
  return pending !== null && pending.mode === room.mode && pending.tableSize === room.tableSize;
}

export default function SimModeChoice({
  pending,
  onChoose,
  headingRef,
}: {
  pending: PendingRoom;
  onChoose: (mode: SimMode, tableSize: TableSize) => void;
  /**
   * The screen's heading, focused by SimulateView after a view swap so the
   * keyboard user is not dropped back to the top of the document. Never in the
   * tab order — see the tabIndex below.
   */
  headingRef: RefObject<HTMLHeadingElement>;
}) {
  const busy = pending !== null;
  const pendingRoom = ROOMS.find((r) => isPending(pending, r));

  return (
    <section className="sim-modechoice" aria-labelledby="smc-title">
      <h2 className="smc-title" id="smc-title" ref={headingRef} tabIndex={-1}>
        Choose a table
      </h2>
      <p className="smc-intro">
        Four rooms, the same felt and the same opponents. The difference is whether the house tells
        you who you are sitting with, and how many seats are dealt in. Your choice is fixed for the
        session — leaving the table is the only way to change rooms.
      </p>

      <div className="smc-rooms">
        {ROOMS.map((room) => {
          const roomId = `${room.mode}-${room.tableSize}`;
          return (
            <button
              key={roomId}
              type="button"
              className={`smc-room smc-room-${room.mode}`}
              onClick={() => onChoose(room.mode, room.tableSize)}
              disabled={busy}
              aria-busy={isPending(pending, room)}
              // Action first, prose on request: the name is the verb and the
              // room, and the card's own copy is offered as a description the
              // reader can ask for rather than one it must sit through.
              aria-label={room.spokenName}
              aria-describedby={`smc-${roomId}-eyebrow smc-${roomId}-lede smc-${roomId}-terms`}
            >
              <span className="smc-head">
                <span className="smc-eyebrow" id={`smc-${roomId}-eyebrow`}>
                  {room.eyebrow}
                </span>
                <span className="smc-stamp" aria-hidden="true">
                  {room.stamp}
                </span>
              </span>
              <span className="smc-name">{room.name}</span>
              <span className="smc-rule" aria-hidden="true" />
              <span className="smc-lede" id={`smc-${roomId}-lede`}>
                {room.lede}
              </span>
              <span className="smc-terms" id={`smc-${roomId}-terms`}>
                {room.terms}
              </span>
              <span className="smc-cta">
                {isPending(pending, room) ? "Taking your seat…" : room.cta}
              </span>
            </button>
          );
        })}
      </div>

      {/* Loading state, announced: the buttons go disabled while the session is
          minted, so the label change inside them is not reliably read out. */}
      <p className="smc-status" role="status">
        {pendingRoom ? `Taking your seat at the ${pendingRoom.name} table…` : ""}
      </p>
    </section>
  );
}
