import type { ReasoningParts } from "../api/types";

// Structured feedback prose (feedback-prose-readability): bold lead sentence +
// supporting bullets + a muted sources footer. Shared by all five prose
// surfaces (SimRecap, HandReplay, HandReplayTable, FeedbackPanel,
// SimRangeChart) so paragraph→bullets ships everywhere at once — the
// cross-surface inconsistency the spec ledger flagged (C1) can't reopen.
// Falls back to the flat paragraph when parts are absent (old persisted rows,
// unrewritten content). Renders nothing when both are empty.
export default function ReasoningText({
  parts,
  flat,
  className,
  showSources = true,
}: {
  parts?: ReasoningParts | null;
  flat?: string | null;
  className: string; // the surface's existing prose class — keeps its chrome
  showSources?: boolean; // off where sources already live in a deep-dive
}) {
  if (parts) {
    return (
      <div className={className + " reasoning-parts"}>
        <p className="reasoning-lead">{parts.lead}</p>
        {parts.points.length > 0 && (
          <ul className="reasoning-points">
            {parts.points.map((point, i) => (
              <li key={i}>{point}</li>
            ))}
          </ul>
        )}
        {showSources && parts.sources && (
          <p className="reasoning-sources">Source: {parts.sources}</p>
        )}
      </div>
    );
  }
  if (!flat) return null;
  return <p className={className}>{flat}</p>;
}
