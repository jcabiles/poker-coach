// P3b — the "turn your phone sideways" line. Passive by ruling: a line in the
// flow, never a fixed overlay and never a dialog. Rendered by SimulateView
// above the live felt and by the History replayer above its felt; both hosts
// decide WHETHER it shows through shouldShowRotateHint (rotateHint.ts) and
// only this file says WHAT it shows, so the copy, the role and the dismissal
// cannot drift between the two.

export default function SimRotateHint({ onDismiss }: { onDismiss: () => void }) {
  return (
    <p className="sim-rotate-hint" role="note">
      Turn your phone sideways for the table.{" "}
      <button type="button" className="btn sim-rotate-dismiss" onClick={onDismiss}>
        Got it
      </button>
    </p>
  );
}
