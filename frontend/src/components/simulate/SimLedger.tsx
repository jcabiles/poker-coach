import type { SeatView } from "../../api/types";
import { fmtBb } from "./simGrade";

// Simulate S9 ledger — the club's rail sheet. A ruled P&L book: one row per
// seat (position · persona · running net_bb), figures set in mono tabular
// numerals like a settlement slip. net_bb is stack_bb - buyins_bb, so it
// already folds in auto-rebuys — a busted-and-rebought seat reads its true
// lifetime P&L. Hero is pinned first and marked; villains follow in seat order.
// Color is redundant (a +/- sign + the word class carry the meaning), so the
// tone tint never becomes the only cue.
//
// The Player column is one of the five archetype display sites the Challenge
// mode withholds (T7): when `labelsVisible` is false it reads a neutral, stable
// seat identity instead, so the running P&L stays attributable to one opponent
// across 200 hands without naming them.

function fmtNet(net: number): string {
  const sign = net > 0 ? "+" : net < 0 ? "−" : "";
  return `${sign}${fmtBb(Math.abs(net))}`;
}

function personaLabel(persona: string | null): string {
  if (!persona) return "You";
  return persona
    .toLowerCase()
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

// Who a row is when the archetype labels are withheld (two-mode-simulate T7,
// spec para 9). The identity must be STABLE across hands, because the whole
// point of the 200 hands is to build a running read on one opponent from their
// running P&L — so it is derived from `seat_index`, the one per-seat value that
// never moves, and printed verbatim so it matches the seat numbers the hand-200
// check asks about. Two things it must not be:
//   • `seat.position` — already the adjacent Seat column, and it rotates every
//     hand as the button moves, which would scramble the attribution.
//   • `"You"` — what personaLabel() returns for a null archetype, so reaching
//     for the existing helper here would make every villain row read as hero.
// The hero keeps "You": the player is not the thing being withheld.
function hiddenLabel(seat: SeatView): string {
  return seat.is_hero ? "You" : `Seat ${seat.seat_index}`;
}

export default function SimLedger({
  seats,
  labelsVisible,
}: {
  seats: SeatView[];
  // T7: false on a Challenge table before the unlock, and whenever the player
  // has hidden the labels again. `persona_type` still arrives on every row —
  // the hiding is here, in the rendering, never in the data.
  labelsVisible: boolean;
}) {
  // Hero first, then the rest in seat order — a stable reading order.
  const ordered = [...seats].sort((a, b) => {
    if (a.is_hero !== b.is_hero) return a.is_hero ? -1 : 1;
    return a.seat_index - b.seat_index;
  });

  return (
    <section className="sim-ledger" aria-label="Session ledger">
      <h2 className="sim-ledger-title">Rail sheet</h2>
      <table className="sim-ledger-table">
        <thead>
          <tr>
            {/* "Pos", not "Seat": this column renders `seat.position`, which
                rotates every hand, and the seat NUMBERS live in the Player
                column when labels are hidden ("Seat 3") — the numbers the
                hand-200 check asks the player about. The old header was a
                mislabel before this slice and collided with those identities
                after it. */}
            <th scope="col" className="sim-led-seat">
              Pos
            </th>
            <th scope="col" className="sim-led-who">
              Player
            </th>
            <th scope="col" className="sim-led-net">
              Net bb
            </th>
          </tr>
        </thead>
        <tbody>
          {ordered.map((seat) => {
            const tone =
              seat.net_bb > 0 ? "up" : seat.net_bb < 0 ? "down" : "even";
            return (
              <tr
                key={seat.seat_index}
                className={"sim-led-row" + (seat.is_hero ? " sim-led-hero" : "")}
              >
                <td className="sim-led-seat">{seat.position}</td>
                <td className="sim-led-who">
                  {labelsVisible ? personaLabel(seat.persona_type) : hiddenLabel(seat)}
                </td>
                <td className={"sim-led-net num sim-net-" + tone}>
                  {fmtNet(seat.net_bb)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
