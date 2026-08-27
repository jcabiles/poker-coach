// Simulate — "Labels" toggle (two-mode-simulate T7). A single pill governing
// whether the opponents' playing-style labels render: Shown puts back the seat
// plate, the range button, the ledger's Player column, the range panel's header
// and the preflop exploit note; Hidden withholds all five at once.
//
// Nothing about the DATA changes in either state — every seat keeps its
// persona_type on the wire and in the record, so history, replay and the
// analytics export stay attributable. This toggle gates only what renders, via
// the one `labelsVisible` boolean SimulateView computes and threads down.
//
// Challenge tables only, and only AFTER the blind check has been answered or
// skipped: spec para 20 requires the control to be ABSENT before that, not
// present-and-disabled, because a disabled control advertises that something is
// being withheld and invites the player to wonder what. SimulateView owns that
// gate; this component renders unconditionally once mounted.
//
// A real <button> with aria-pressed gives correct toggle semantics + keyboard
// for free. The gilt pressed state mirrors the Watch/Grading pills and is
// redundant twice over — with aria-pressed and with the face's own word — so
// the state is never carried by colour alone. Reuses the existing .sim-watch
// classes: same pill, same face, same focus ring, just a different setting,
// exactly as SimGradingToggle does.

export default function SimLabelsToggle({
  shown,
  onChange,
}: {
  shown: boolean;
  onChange: (next: boolean) => void;
}) {
  return (
    <button
      type="button"
      className="sim-watch"
      aria-pressed={shown}
      aria-label={shown ? "Opponent labels: shown" : "Opponent labels: hidden"}
      title="Show or hide the opponents' playing-style labels (the record keeps them either way)"
      onClick={() => onChange(!shown)}
    >
      <span className="sim-watch-face">Labels: {shown ? "Shown" : "Hidden"}</span>
    </button>
  );
}
