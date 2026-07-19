import { useEffect, useState } from "react";

import { explainDecision } from "../../api/client";
import type { CoachExplainRequest, GradeView } from "../../api/types";
import { fmtEvLoss, isMiss, streetLabel, tierOf } from "./simGrade";

// Simulate S10 — the coach's margin ledger. Mounts beside SimShowdown on
// hand_over: one ruled row per hero decision in ordinal order (street · action ·
// verdict · ≈EV-loss), and beneath a mistake/blunder row, the gilt-ruled "why"
// note — the teaching moment. "No baseline yet" rows (multiway / off-pack /
// unmappable spots the grader never ran on) are listed distinctly, never faked
// into a tier.
//
// AGGREGATE RULE (spec Gate-1 / refuter low-4): the SUMMARY line — accuracy and
// total ≈EV lost — counts ONLY graded rows (correctness != null). No-baseline
// rows carry ev_loss_bb 0 and no correctness; folding them in would dilute both
// figures and misreport coverage. They still appear in the per-decision list.
//
// TIER SURVIVAL: on the live path SimulateView merges each decision's live
// `last_grade` (which carries the verdict/reasoning text) into the recap by
// ordinal, so misses show their "why". After a mid-session reload the persisted
// rows have no tier text (freq/EV/correctness survive) — this component then
// degrades gracefully: the verdict word + ≈EV-loss still render, the "why" note
// just isn't there to expand.
//
// N6 — "Explain this" (on-demand LLM coach): every row gets a button that POSTs
// a HERO-ONLY context to /explain and renders the returned concept + fix. The
// payload is assembled by EXPLICIT FIELD-PICKING below — do NOT spread `hand` or
// any object that could carry villain showdown cards into it. Live-per-request;
// nothing is persisted, so the explanation clears when the hand changes.

function actionLabel(action: string): string {
  return action.charAt(0).toUpperCase() + action.slice(1);
}

type ExplainState = { loading: boolean; text: string | null; error: boolean };

export default function SimRecap({
  recap,
  sessionId,
  heroCards,
  board,
}: {
  recap: GradeView[];
  sessionId: string | null;
  heroCards: [string, string];
  board: string[];
}) {
  // Per-ordinal explanation state. Keyed by ordinal; cleared whenever the recap
  // identity changes (a new hand) so stale coaching never bleeds across hands.
  const [explains, setExplains] = useState<Record<number, ExplainState>>({});
  useEffect(() => {
    setExplains({});
  }, [recap]);

  if (recap.length === 0) return null;

  const graded = recap.filter((g) => g.correctness != null);
  const gradedCount = graded.length;
  const correct = graded.filter(
    (g) => g.correctness === "optimal" || g.correctness === "acceptable",
  ).length;
  const evLost = graded.reduce((sum, g) => sum + g.ev_loss_bb, 0);
  const noBaseline = recap.length - gradedCount;

  async function onExplain(g: GradeView) {
    if (!sessionId) return;
    setExplains((prev) => ({
      ...prev,
      [g.ordinal]: { loading: true, text: null, error: false },
    }));
    // HERO-ONLY payload — every field is picked by name from the grade row plus
    // hero's own cards / the public board. No villain data is reachable here.
    const body: CoachExplainRequest = {
      street: g.street,
      chosen_action: g.chosen_action,
      correctness: g.correctness,
      sizing_correctness: g.sizing_correctness,
      ev_loss_bb: g.ev_loss_bb,
      coverage: g.coverage,
      node_context: g.node_context,
      position: g.position,
      facing_position: g.facing_position,
      verdict: g.verdict,
      reasoning: g.reasoning,
      hero_cards: heroCards,
      board,
    };
    try {
      const res = await explainDecision(sessionId, body);
      setExplains((prev) => ({
        ...prev,
        [g.ordinal]: { loading: false, text: res.explanation, error: false },
      }));
    } catch {
      setExplains((prev) => ({
        ...prev,
        [g.ordinal]: { loading: false, text: null, error: true },
      }));
    }
  }

  return (
    <section className="sim-recap panel" aria-label="Decision recap">
      <h2 className="sim-recap-title">Your decisions</h2>

      {gradedCount > 0 ? (
        <p className="sim-recap-summary">
          <span className="sim-recap-stat">
            <span className="sim-recap-stat-val num">
              {Math.round((correct / gradedCount) * 100)}%
            </span>
            <span className="sim-recap-stat-key">on baseline</span>
          </span>
          <span className="sim-recap-stat">
            <span className="sim-recap-stat-val num">{fmtEvLoss(evLost)}</span>
            <span className="sim-recap-stat-key">given up</span>
          </span>
          {noBaseline > 0 && (
            <span className="sim-recap-stat">
              <span className="sim-recap-stat-val num">{noBaseline}</span>
              <span className="sim-recap-stat-key">no baseline</span>
            </span>
          )}
        </p>
      ) : (
        <p className="sim-recap-summary sim-recap-summary-none">
          No mapped spots this hand — nothing to grade yet.
        </p>
      )}

      <ol className="sim-recap-list">
        {recap.map((g) => {
          const meta = tierOf(g.correctness);
          const miss = isMiss(g.correctness);
          const rowGraded = g.correctness != null;
          const ex = explains[g.ordinal];
          return (
            <li key={g.ordinal} className="sim-recap-row">
              <div className="sim-recap-line">
                <span className="sim-recap-street">{streetLabel(g.street)}</span>
                <span className="sim-recap-action">{actionLabel(g.chosen_action)}</span>
                <span className={"sim-badge sim-badge-inline sim-tier-" + meta.tone}>
                  <span className="sim-badge-word">{meta.label}</span>
                </span>
                {/* N3: preflop sizing verdict — a secondary sub-note directly
                    beside the action verdict badge, never altering it. Placed
                    BEFORE the margin-left:auto EV figure so it always sits next
                    to the verdict, not stranded at the row's right edge. Only
                    when hero raised at a two-size node. */}
                {g.sizing_correctness != null && (
                  <span className="sim-recap-size">
                    · size: {tierOf(g.sizing_correctness).label}
                  </span>
                )}
                {rowGraded && g.ev_loss_bb > 0 && (
                  <span className="sim-recap-ev num">{fmtEvLoss(g.ev_loss_bb)}</span>
                )}
              </div>
              {/* The teaching moment: only misses expand their "why", and only
                  when the reasoning text survived (live path — a reload drops
                  it and the row degrades to the verdict line above). */}
              {miss && g.reasoning && (
                <p className="sim-recap-why">{g.reasoning}</p>
              )}
              {/* N6: on-demand coach. Available on every row (a good play's
                  "why it's standard" is as useful as a leak's fix). */}
              <div className="sim-recap-coach">
                <button
                  type="button"
                  className="sim-recap-explain-btn"
                  onClick={() => onExplain(g)}
                  disabled={!sessionId || ex?.loading}
                >
                  {ex?.loading ? "Thinking…" : ex?.text ? "Explain again" : "Explain this"}
                </button>
                {ex?.error && (
                  <span className="sim-recap-explain-error" role="alert">
                    Couldn’t reach the coach — try again.
                  </span>
                )}
                {ex?.text && <p className="sim-recap-explain">{ex.text}</p>}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
