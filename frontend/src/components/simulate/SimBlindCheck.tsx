import { useEffect, useRef, useState } from "react";

import type {
  ArchetypeGuess,
  BlindCheckAnswer,
  BlindCheckSubmitRequest,
  SeatView,
} from "../../api/types";
import { ARCHETYPE_OPTIONS, archetypeGloss, archetypeName, HOUSE_LINEUP } from "./blindCheck";
import { fmtBb } from "./simGrade";

// Two-mode Simulate T8 — the hand-200 blind check: the moment a Challenge table
// stops dealing and asks the player to name three of the eight strangers they
// have been reading. Answering (or skipping) is what opens the archetype labels
// and lets the deal resume; the server is what enforces both.
//
// A REAL modal, built on the platform's own <dialog> + showModal(). That is not
// a stylistic preference: showModal() puts the element in the top layer and
// makes the rest of the document inert — focus is trapped, background controls
// are unreachable by pointer AND absent from the accessibility tree, and Esc
// raises `cancel` — all of which a hand-rolled scrim-and-keydown trap only
// approximates. Nothing else in this app is modal (SimVillainRange documents
// itself as explicitly non-modal), so there is no in-house trap to reuse; what
// IS reused from that panel is its overlay grammar — aria-labelledby onto a
// titled header, an explicit × close control with a spoken label, and Esc as a
// dismiss rather than a commit.
//
// NOTHING HERE SPENDS THE CHECK BY ACCIDENT. It is a one-way step (first write
// wins, server-side), so every path that would spend it takes a deliberate act:
//   • Esc and × DISMISS. They hand the player back to the barred table, which
//     is where the evidence is — the rail sheet has been printing "Seat 1"…
//     "Seat 8" against a running P&L for 200 hands, and that is the read this
//     check is asking for. SimulateView re-offers the card from the paused
//     strip, and it keeps the names already chosen.
//   • SKIP comes AFTER the primary control in the document, so a keyboard user
//     cannot tab past "score" onto "discard" — and once any seat is named it
//     asks a second time before it forfeits the work.
//
// THE SCORE IS NOT A MEASUREMENT (spec para 17). The lineup is a FIXED multiset
// (backend/app/domain/table/play.py:44-54), so the six options are not
// equiprobable and this is a closed-set task. This component's answer to that
// is to TELL the player the lineup, up front, rather than score them out of a
// constraint they were not shown — and to gloss what each archetype DOES,
// because a Challenge session has hidden all six words since hand 1, so a
// disclosed lineup is only a fair chance if the names can be mapped onto
// behaviour. Disclosure plus gloss is what makes the number visibly a keepsake:
// a player who knows the counts and the meanings cannot mistake three-from-six
// for a blind identification rate.

const TITLE_ID = "sim-blindcheck-title";
const INTRO_ID = "sim-blindcheck-intro";
const LINEUP_ID = "sim-blindcheck-lineup";

/** One seat's answer while the card is being filled in; owned by SimulateView. */
export type BlindCheckAnswers = Readonly<Record<number, ArchetypeGuess | undefined>>;

// The rail sheet's own signed figure, so the number in this card and the number
// in the sheet behind it are the same number. `fmtBb` is the shared formatter;
// only the sign prefix is applied here (SimLedger's equivalent is private to a
// file this ticket must not touch).
function fmtNet(net: number): string {
  const sign = net > 0 ? "+" : net < 0 ? "−" : "";
  return `${sign}${fmtBb(Math.abs(net))}`;
}

export default function SimBlindCheck({
  seats,
  seatRows,
  handsPlayed,
  answers,
  onAnswer,
  submitting,
  error,
  onSubmit,
  onDismiss,
}: {
  /** The three seat numbers the server picked — asked about verbatim, so this
      dialog can never name a seat the server did not choose (its 400). */
  seats: number[];
  /** Every seat on the table, for the running P&L beside each question. */
  seatRows: SeatView[];
  /** Completed hands behind the player, for the card's own copy. */
  handsPlayed: number;
  /** The names chosen so far. Held by SimulateView, NOT here: setting the card
      aside to go and read the rail sheet is a flow this dialog's own copy
      invites, and unmounting must not throw the work away. */
  answers: BlindCheckAnswers;
  onAnswer: (seatIndex: number, guess: ArchetypeGuess) => void;
  submitting: boolean;
  /** A refused submission, already reduced to its status by SimulateView. */
  error: { status: number | null } | null;
  onSubmit: (body: BlindCheckSubmitRequest) => void;
  /** Set the card aside without answering — Esc and the × control. */
  onDismiss: () => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  // Skip is destructive once anything has been named, so it asks twice. Local
  // to the dialog on purpose: unlike the answers, an armed confirmation must
  // NOT survive setting the card aside and coming back.
  const [skipArmed, setSkipArmed] = useState(false);

  // Enter the top layer on mount and leave it on unmount. Focus is placed on
  // the card itself (tabIndex={-1}) rather than the first control, so the title
  // and the intro — the two things that explain why the deal stopped — are what
  // a screen reader announces before the questions start.
  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    if (!el.open) el.showModal();
    el.focus();
    return () => {
      if (el.open) el.close();
    };
  }, []);

  const named = seats.filter((s) => answers[s] != null).length;
  const complete = named === seats.length && seats.length > 0;
  const remaining = seats.length - named;

  // The ONLY two bodies this dialog can build. Neither can carry a partial set
  // and neither can carry both a skip and answers: `submit` collects strictly
  // from `seats`, drops any seat still unanswered, and refuses to send unless
  // what survived is the full set — so the 422 the backend schema returns for a
  // malformed body has no path through this UI, with the disabled control the
  // visible half of the same guarantee rather than the whole of it.
  const submit = () => {
    if (submitting) return;
    const guesses: BlindCheckAnswer[] = [];
    for (const seat of seats) {
      const guess = answers[seat];
      if (guess != null) guesses.push({ seat_index: seat, guess });
    }
    if (guesses.length !== seats.length) return;
    onSubmit({ skipped: false, guesses });
  };

  const skip = () => {
    if (submitting) return;
    // Nothing named, nothing to lose — skipping goes straight through. With
    // work on the card it forfeits the payoff of two hundred hands and cannot
    // be undone, so it asks again first.
    if (named > 0 && !skipArmed) {
      setSkipArmed(true);
      return;
    }
    onSubmit({ skipped: true, guesses: [] });
  };

  return (
    <dialog
      className="sbc"
      ref={dialogRef}
      tabIndex={-1}
      aria-labelledby={TITLE_ID}
      aria-describedby={INTRO_ID}
      aria-busy={submitting}
      onCancel={(e) => {
        // Esc. Take the default close away and route it through the parent, so
        // "dismissed" is one piece of state in one place and Esc can never be
        // mistaken for an answer. Allowed mid-flight for the same reason the ×
        // is: a hung request must not seal the player in.
        e.preventDefault();
        onDismiss();
      }}
    >
      <header className="sbc-head">
        <div className="sbc-head-text">
          <p className="sbc-eyebrow">
            <span className="num">{handsPlayed}</span> hands played · the deal is paused
          </p>
          <h2 className="sbc-title" id={TITLE_ID}>
            Name three of them
          </h2>
          <p className="sbc-intro" id={INTRO_ID}>
            You have sat with these eight all session without a single name on the felt. Say who
            these three were and the names come on — yours to show or hide from then on.
          </p>
        </div>
        {/* Stays live while a submission is in flight. Dismissing does not
            cancel the request and the result is adopted from its response
            either way, so there is nothing to protect by locking the only exit
            — and a request that never returns would otherwise leave every
            control on the card disabled with no way out but a reload. */}
        <button
          type="button"
          className="sbc-close"
          onClick={onDismiss}
          aria-label="Set the check aside and look at the table"
        >
          <span aria-hidden="true">×</span>
        </button>
      </header>

      {/* The closed set, stated. See the component note: the score is only
          honest if the player knows the constraint it is scored against. */}
      <section className="sbc-lineup" aria-labelledby={LINEUP_ID}>
        <p className="sbc-eyebrow" id={LINEUP_ID}>
          The house lineup — the same eight at every table
        </p>
        <ul className="sbc-lineup-list">
          {ARCHETYPE_OPTIONS.map((value) => (
            <li className="sbc-lineup-item" key={value}>
              <span className="sbc-lineup-name">{archetypeName(value)}</span>
              <span className="sbc-lineup-count num">×{HOUSE_LINEUP[value]}</span>
            </li>
          ))}
        </ul>
        <p className="sbc-lineup-note">
          So you are picking out of a known set, not out of six equal chances — which is exactly why
          what comes back is a souvenir of the session and not a score of your reading.
        </p>
      </section>

      <div className="sbc-seats">
        {seats.map((seatIndex) => {
          const row = seatRows.find((s) => s.seat_index === seatIndex);
          const tone =
            row == null ? "even" : row.net_bb > 0 ? "up" : row.net_bb < 0 ? "down" : "even";
          return (
            <fieldset className="sbc-seat" key={seatIndex}>
              <legend className="sbc-seat-head">
                <span className="sbc-seat-no">
                  Seat <span className="num">{seatIndex}</span>
                </span>
                {row != null && (
                  <span className={`sbc-seat-net num sim-net-${tone}`}>
                    {fmtNet(row.net_bb)}
                    <span className="sbc-seat-net-unit"> bb</span>
                    <span className="sim-sr-only"> net over the session</span>
                  </span>
                )}
              </legend>
              <div className="sbc-opts">
                {ARCHETYPE_OPTIONS.map((value) => (
                  <label className="sbc-opt" key={value}>
                    <input
                      type="radio"
                      className="sbc-opt-input"
                      name={`sim-blindcheck-seat-${seatIndex}`}
                      value={value}
                      checked={answers[seatIndex] === value}
                      disabled={submitting}
                      onChange={() => {
                        // Naming a seat disarms a pending skip: the player has
                        // just added work, so the next press of a control they
                        // armed a moment ago must not throw it away.
                        setSkipArmed(false);
                        onAnswer(seatIndex, value);
                      }}
                    />
                    <span className="sbc-opt-face">
                      <span className="sbc-opt-name">{archetypeName(value)}</span>
                      <span className="sbc-opt-gloss">{archetypeGloss(value)}</span>
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>
          );
        })}
      </div>

      {/* One message for every refusal. The endpoint has three — the gate not
          being open, seats the digest did not pick, and a malformed body — and
          none of them is reachable from a mounted card: it mounts only when the
          server itself reported the gate open, it asks about those seats
          verbatim, and it cannot build a partial or contradictory body. What
          remains reachable is the network failing, and the player's move is the
          same for all four, so four wordings would be four explanations for one
          situation they did not cause. The status is shown; the full error goes
          to the console, because the raw message carries the request URL and
          the session id with it, and this is a payoff screen, not a log. */}
      {error && (
        <p className="sbc-error" role="alert">
          That did not go through, so nothing was stored. Try again — if it keeps failing, reload
          the page.
          {error.status != null && (
            <span className="sbc-error-status"> (status {error.status})</span>
          )}
        </p>
      )}

      <footer className="sbc-foot">
        <p className="sbc-remaining" role="status">
          {complete
            ? "All three named."
            : remaining === 1
              ? "One seat still to name."
              : `${remaining} seats still to name.`}
        </p>
        {/* Primary FIRST in the document. Skip is one irreversible keystroke,
            and reaching it by tabbing off the end of the seats — before the
            control that banks the work — is how two hundred hands get thrown
            away by a stray Enter. */}
        <div className="sbc-actions">
          <button
            type="button"
            className="btn btn-primary sbc-submit"
            onClick={submit}
            disabled={submitting || !complete}
          >
            {submitting ? "Scoring…" : "Score my three"}
          </button>
        </div>
        <p className="sbc-foot-note">
          Either way the deal starts again and the names stay on. The check is asked once a session,
          so there is no second run at it.
        </p>
        <div className="sbc-skip-row">
          <button
            type="button"
            className={"btn sbc-skip" + (skipArmed ? " sbc-skip-armed" : "")}
            onClick={skip}
            disabled={submitting}
          >
            {skipArmed ? "Skip anyway, discarding your names" : "Skip, and just open the names"}
          </button>
          {skipArmed && (
            <span className="sbc-skip-warn" role="status">
              That throws away the {named === 1 ? "name" : `${named} names`} you have set, for good.
            </span>
          )}
        </div>
      </footer>
    </dialog>
  );
}
