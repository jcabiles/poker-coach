import type { RefObject } from "react";

import type { SimMode } from "../../api/types";

// Simulate — the sit-down screen (two-mode-simulate T6). The player is choosing
// which ROOM to sit down in, not flipping a setting: two printed reservation
// cards laid on the club's baize, one on plain stock and one foil-stamped.
//
// No pre-selection, by design — neither room is the default a player drifts
// into. Each card IS the control (a real <button>), so the choice and the
// sit-down are one act; there is no "confirm" step to leave a highlighted
// default sitting on screen.
//
// The two rooms are told apart by four cues that are NOT colour: different
// eyebrow lines, a different corner stamp numeral (1 vs 200), a single rule vs
// a double rule under the room name, and different terms lines. The gilt on
// Challenge is the accent on top of those, never the meaning.
//
// This screen names the modes in the player's terms. "Challenge" is not "hides
// persona_type" — it is a table where you work out who you are playing against
// and the names arrive at 200 hands.

type Room = {
  mode: SimMode;
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

// Order is fixed: the plain room first, then the accented one. Both cards are
// the same size and shape — equal weight as choices.
const ROOMS: readonly Room[] = [
  {
    mode: "training",
    eyebrow: "Play with the read",
    name: "Training",
    stamp: "1",
    lede: "Every seat is labelled with how that opponent plays — nit, TAG, maniac — from the very first hand. Read the label, watch what it does to you, and learn the type.",
    terms: "Names shown · from hand 1",
    cta: "Take this seat",
    spokenName: "Take this seat at the Training table",
  },
  {
    mode: "challenge",
    eyebrow: "Earn the read",
    name: "Challenge",
    stamp: "200",
    lede: "The seats keep their names to themselves. You work out who you are up against from the way they play — then at 200 hands the table asks you to name three of them, and the names come out for the rest of the session.",
    terms: "Names sealed · until hand 200",
    cta: "Take this seat",
    spokenName: "Take this seat at the Challenge table",
  },
];

export default function SimModeChoice({
  pending,
  onChoose,
  headingRef,
}: {
  /** The room whose session is being created right now, or null when idle. */
  pending: SimMode | null;
  onChoose: (mode: SimMode) => void;
  /**
   * The screen's heading, focused by SimulateView after a view swap so the
   * keyboard user is not dropped back to the top of the document. Never in the
   * tab order — see the tabIndex below.
   */
  headingRef: RefObject<HTMLHeadingElement>;
}) {
  const busy = pending !== null;
  const pendingRoom = ROOMS.find((r) => r.mode === pending);

  return (
    <section className="sim-modechoice" aria-labelledby="smc-title">
      <h2 className="smc-title" id="smc-title" ref={headingRef} tabIndex={-1}>
        Choose a table
      </h2>
      <p className="smc-intro">
        Two rooms, the same felt and the same opponents. The difference is whether the house tells
        you who you are sitting with. Your choice is fixed for the session — leaving the table is
        the only way to change rooms.
      </p>

      <div className="smc-rooms">
        {ROOMS.map((room) => (
          <button
            key={room.mode}
            type="button"
            className={`smc-room smc-room-${room.mode}`}
            onClick={() => onChoose(room.mode)}
            disabled={busy}
            aria-busy={pending === room.mode}
            // Action first, prose on request: the name is the verb and the
            // room, and the card's own copy is offered as a description the
            // reader can ask for rather than one it must sit through.
            aria-label={room.spokenName}
            aria-describedby={`smc-${room.mode}-eyebrow smc-${room.mode}-lede smc-${room.mode}-terms`}
          >
            <span className="smc-head">
              <span className="smc-eyebrow" id={`smc-${room.mode}-eyebrow`}>
                {room.eyebrow}
              </span>
              <span className="smc-stamp" aria-hidden="true">
                {room.stamp}
              </span>
            </span>
            <span className="smc-name">{room.name}</span>
            <span className="smc-rule" aria-hidden="true" />
            <span className="smc-lede" id={`smc-${room.mode}-lede`}>
              {room.lede}
            </span>
            <span className="smc-terms" id={`smc-${room.mode}-terms`}>
              {room.terms}
            </span>
            <span className="smc-cta">
              {pending === room.mode ? "Taking your seat…" : room.cta}
            </span>
          </button>
        ))}
      </div>

      {/* Loading state, announced: the buttons go disabled while the session is
          minted, so the label change inside them is not reliably read out. */}
      <p className="smc-status" role="status">
        {pendingRoom ? `Taking your seat at the ${pendingRoom.name} table…` : ""}
      </p>
    </section>
  );
}
