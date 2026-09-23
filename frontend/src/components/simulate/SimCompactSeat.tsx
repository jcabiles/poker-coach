import type { CSSProperties, KeyboardEvent, ReactNode } from "react";
import { useEffect, useRef, useState } from "react";

// A villain's pod in phone landscape (SimTable's `compact`). Two rows: the
// action row, then the position row — position, dealer disc, stack and the
// face-down marker on one line. Face-up cards (showdown, R1) join the ACTION
// row instead, beside what the seat did: on the position row they made a flank
// pod 150px wide, and its inward reach met the river board at 800×360 (145px²
// measured). Which row is the designer's call (spec §2); the height, 0.32 of a
// card, is the spec's.
//
// SimTable builds every value shown here, gated exactly as in the full pod
// (the lockstep `revealed`, the staged fold, `playbackComplete`); this file
// only lays those nodes out and owns the tap that opens the seat's details.
// Nothing here may lead the event log, because nothing here computes a value.

// One pod's details open at a time, remembered with the hand they were opened
// in so a new deal never reopens them. `isTappable` is SimTable's answer to
// "does this seat still have a seat button" — labels shown, a persona, not
// folded by its STAGED fold, not hand_over. The details close the moment it
// turns false for the open seat, so they fold away exactly when the log
// narrates the fold (never on raw `seat.status`, which would snap them shut
// early), at hand_over, and when the labels they show are hidden.
export function useSeatDetails(handNo: number, isTappable: (seatIndex: number) => boolean) {
  const [details, setDetails] = useState<{ seat: number; hand: number } | null>(null);
  const live = details != null && details.hand === handNo && isTappable(details.seat);
  useEffect(() => {
    if (details != null && !live) setDetails(null);
  }, [details, live]);
  const openSeat = live ? details.seat : null;
  return {
    openSeat,
    toggle: (seat: number) => setDetails(openSeat === seat ? null : { seat, hand: handNo }),
    close: () => setDetails(null),
  };
}

// Which way the details grow, read from the seat's slot on the ellipse. A seat
// in the ring's middle third across (the top-centre seats) sits right over the
// board, and a panel grown down from it landed on the river (1,103px² at
// 914×290), with no room above it under the .ctx line; it opens beside its pod
// instead, on the side away from the board's centre. Every other seat grows
// toward the ring's centre — down from the top half, up from the bottom half —
// so .stage's overflow:hidden never shears it, and its panel stays inside the
// flank, clear of the cards.
function placement(style: CSSProperties): string {
  const top = Number.parseFloat(String(style.top));
  const left = Number.parseFloat(String(style.left));
  if (left > 100 / 3 && left < 200 / 3) {
    return left < 50 ? " sim-seat-beside sim-seat-west" : " sim-seat-beside sim-seat-east";
  }
  return top < 50 ? " sim-seat-top" : "";
}

// What claims Esc before an open pod does: the nav sheet, a native dialog, and
// an armed shove — its warning is on screen exactly while one is armed, and
// SimActionBar backs the shove out on that same press.
const OTHER_ESC_OWNERS = ".nav-tabs-open, dialog[open], .sim-action-warn";

export default function SimCompactSeat({
  podClass,
  style,
  seatIndex,
  position,
  name,
  actRow,
  ident,
  marker,
  details,
  tappable,
  open,
  onToggle,
  onClose,
}: {
  // SimTable's pod classes (folded, to act, labelled) — shared with the full pod.
  podClass: string;
  // The slot on the ellipse (SimTable's slotStyle); geometry, untouched here.
  style: CSSProperties;
  // `data-seat`: how SimulateView finds this pod's RANGE or seat button to hand
  // focus back to when the range panel closes.
  seatIndex: number;
  position: string;
  // The seat button's accessible name. It starts with the visible text —
  // position, dealer, stack — so it satisfies Label in Name (WCAG 2.5.3).
  name: string;
  // Verb, chips and any face-up cards; null when the seat has none of them.
  actRow: ReactNode;
  // Position, dealer disc and stack: the seat button's face.
  ident: ReactNode;
  // The face-down card marker (nothing once folded or face up).
  marker: ReactNode;
  // Persona plate and RANGE, shown while the details are open. RANGE is the
  // seat button's sibling and stops its own click (SimTable), so a RANGE tap
  // toggles the range and nothing else.
  details: ReactNode;
  // With labels shown and a persona to show, the position and stack ARE the
  // seat button; otherwise (Challenge mode, folded, hand over) plain text.
  tappable: boolean;
  open: boolean;
  onToggle: () => void;
  onClose: () => void;
}) {
  const btnRef = useRef<HTMLButtonElement>(null);

  // Esc on the OPEN pod only — the keydown of its seat button and its details
  // group, the pod's only focusable parts, never window. Whatever sits on top
  // claims the key first — the guard is HandReplayTable's (the nav sheet and a
  // native dialog), plus the armed-shove warning, whose Esc backs the shove out
  // and must not also fold this pod away. Focus goes back to the seat button,
  // which stays mounted, because RANGE is about to unmount under it.
  const onKeyDown = (e: KeyboardEvent<HTMLElement>) => {
    if (e.key !== "Escape" || e.metaKey || e.ctrlKey || e.altKey) return;
    if (document.querySelector(OTHER_ESC_OWNERS)) return;
    e.preventDefault();
    onClose();
    btnRef.current?.focus();
  };

  return (
    <div
      className={podClass + " sim-seat-compact" + (open ? " sim-seat-open" : "") + placement(style)}
      style={style}
      data-seat={seatIndex}
    >
      {actRow}
      <span className="sim-podrow">
        {tappable ? (
          <button
            type="button"
            className="sim-seat-btn"
            ref={btnRef}
            aria-expanded={open}
            aria-label={name}
            onKeyDown={open ? onKeyDown : undefined}
            onClick={onToggle}
          >
            {ident}
          </button>
        ) : (
          <span className="sim-seat-id">{ident}</span>
        )}
        {marker}
      </span>
      {open && (
        <span
          className="sim-seat-details"
          role="group"
          aria-label={`${position} details`}
          onKeyDown={onKeyDown}
        >
          {details}
        </span>
      )}
    </div>
  );
}
