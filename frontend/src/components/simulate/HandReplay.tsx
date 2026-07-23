import { useEffect, useMemo, useState } from "react";

import type { HandReplayView, ReplayStepView, ShowdownSeatView } from "../../api/types";
import Card from "../Card";
import { fmtEvLoss, streetLabel, tierOf } from "./simGrade";

// Simulate Hand-History + Replay (T6) — the stepped replay reader. Presentational:
// the parent (HistoryView / SimulateView) fetches the HandReplayView and hands it
// in; this component owns only the step cursor. It is NOT the live animated felt —
// no simPlayback / SimTable pacing. Instead it reads like a stepped filmstrip of a
// past hand: a gilt playhead rail across the streets, the board strip and seat
// cards for the current step, and, on hero steps, an inline verdict panel.
//
// STAGED REVEAL / NO-PEEK: villains' hole cards are structurally absent from every
// step until the terminal showdown step, where `revealed_seats` carries exactly the
// server's settle().showdown_seats. The client holds no villain card before then —
// we render only what's on the wire, so a villain pod stays face-down until reveal.
//
// FREQ+EV, NEVER BOOLEAN: the verdict panel shows tier + ≈EV-loss + coverage (and
// the persisted "why" when present) — never a pass/fail collapse. EVs are ≈approx.

// Streets in canonical order — the playhead rail draws one segment per street the
// hand actually reached, lit up to the current step's street.
const STREET_ORDER = ["preflop", "flop", "turn", "river"] as const;

function actionVerb(step: ReplayStepView): string {
  const a = step.action;
  const amt = step.amount_bb;
  switch (a) {
    case "fold":
      return "folds";
    case "check":
      return "checks";
    case "call":
      return amt <= 1 ? "limps" : `calls ${amt}bb`;
    case "bet":
      return `bets ${amt}bb`;
    case "raise":
      return `raises to ${amt}bb`;
    case "post":
      return `posts ${amt}bb`;
    default:
      return a;
  }
}

// A tidy caption for the current step: "UTG raises to 3bb" / "Hero calls 2bb".
function stepCaption(step: ReplayStepView): string {
  const who = step.is_hero ? "Hero" : step.position;
  return `${who} ${actionVerb(step)}`;
}

export default function HandReplay({
  replay,
  onClose,
}: {
  replay: HandReplayView;
  // Return to the surface that opened the replayer (history list / the live table).
  onClose: () => void;
}) {
  const { steps, hero_cards, hero_position, hand_no } = replay;
  const [cursor, setCursor] = useState(0);

  // A fresh hand resets the cursor to the first step (the parent remounts on a
  // new selection via `key`, but guard anyway so a prop swap can't strand it).
  useEffect(() => {
    setCursor(0);
  }, [replay.sim_hand_id]);

  const total = steps.length;
  const step: ReplayStepView | undefined = steps[cursor];

  const atStart = cursor === 0;
  const atEnd = cursor >= total - 1;

  // Which streets the hand reached (in order) → the playhead rail segments. The
  // final board length implies the deepest street even for an all-in auto-runout,
  // so derive from the terminal step's board rather than only acted streets.
  const reachedStreets = useMemo(() => {
    let deepest = 0;
    for (const s of steps) {
      const idx = STREET_ORDER.indexOf(s.street as (typeof STREET_ORDER)[number]);
      if (idx > deepest) deepest = idx;
      // The terminal board can be deeper than any acted street (auto-runout).
      if (s.is_terminal) {
        if (s.board.length >= 5) deepest = Math.max(deepest, 3);
        else if (s.board.length === 4) deepest = Math.max(deepest, 2);
        else if (s.board.length === 3) deepest = Math.max(deepest, 1);
      }
    }
    return STREET_ORDER.slice(0, deepest + 1);
  }, [steps]);

  const currentStreetIdx = step
    ? STREET_ORDER.indexOf(step.street as (typeof STREET_ORDER)[number])
    : 0;

  // Villain reveals: only ever present on the terminal step (NO-PEEK). Keyed by
  // seat so the seat strip can flip exactly those pods face-up at showdown.
  const revealedBySeat = useMemo(() => {
    const m = new Map<number, ShowdownSeatView>();
    if (step?.is_terminal) {
      for (const r of step.revealed_seats) m.set(r.seat_index, r);
    }
    return m;
  }, [step]);

  const go = (next: number) => setCursor(Math.min(Math.max(next, 0), Math.max(total - 1, 0)));

  // ← / → step the hand (the Next/Prev buttons stay the primary control + carry
  // visible focus). Skipped when focus sits on another interactive control so a
  // key meant for a button isn't hijacked, and when a modifier is held.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.key !== "ArrowLeft" && e.key !== "ArrowRight") || e.metaKey || e.ctrlKey || e.altKey) {
        return;
      }
      const target = e.target;
      if (
        target instanceof Element &&
        target.closest('input, textarea, select, [contenteditable="true"]')
      )
        return;
      e.preventDefault();
      setCursor((c) =>
        Math.min(Math.max(c + (e.key === "ArrowRight" ? 1 : -1), 0), Math.max(total - 1, 0)),
      );
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [total]);

  if (!step) {
    // Defensive: a complete hand always has ≥1 step, but never crash on an empty
    // reconstruction — offer the way back rather than a blank frame.
    return (
      <section className="hr" aria-label="Hand replay">
        <div className="hr-head">
          <button type="button" className="btn hr-back" onClick={onClose}>
            ← Back
          </button>
          <h2 className="hr-title">Hand {hand_no}</h2>
        </div>
        <p className="hr-empty" role="status">
          No actions to replay for this hand.
        </p>
      </section>
    );
  }

  const board = step.board;

  return (
    <section className="hr" aria-label={`Replay of hand ${hand_no}`}>
      <div className="hr-head">
        <button type="button" className="btn hr-back" onClick={onClose}>
          ← Back
        </button>
        <h2 className="hr-title">
          Hand <span className="hr-title-no num">{hand_no}</span>
        </h2>
        <span className="hr-hero-note">
          Hero · <span className="hr-hero-pos">{hero_position}</span>
        </span>
      </div>

      {/* Playhead rail — one segment per street the hand reached, lit up to the
          current step's street. Decorative-of-a-state (the caption below carries
          the meaning for AT), so the rail itself is aria-hidden. */}
      <div className="hr-rail" aria-hidden="true">
        {reachedStreets.map((s, i) => (
          <span
            key={s}
            className={"hr-rail-seg" + (i <= currentStreetIdx ? " on" : "")}
          >
            <span className="hr-rail-label">{streetLabel(s)}</span>
          </span>
        ))}
      </div>

      {/* Board strip — the community cards revealed at this step (final board at the
          terminal showdown step, so an all-in runout shows all five). */}
      <div className="hr-board-wrap">
        {board.length > 0 ? (
          <div className="hr-board cards" key={cursor} aria-label="community cards">
            {board.map((c, i) => (
              <Card key={i} card={c} />
            ))}
          </div>
        ) : (
          <p className="hr-board-empty">Preflop — no board yet</p>
        )}
      </div>

      {/* Step caption — who did what, this step. The focal narration line. */}
      <div className="hr-caption-row">
        <span className="hr-caption-street">{streetLabel(step.street)}</span>
        <span
          className={"hr-caption" + (step.is_hero ? " hero" : "")}
          key={cursor}
          role="status"
          aria-live="polite"
        >
          {step.is_terminal ? "Showdown" : stepCaption(step)}
        </span>
      </div>

      {/* Showdown reveal — villain cards appear ONLY here (terminal step). Before
          this step no villain card is on the wire, so nothing to render. */}
      {step.is_terminal && revealedBySeat.size > 0 && (
        <ul className="hr-reveal-list" aria-label="Showdown hands">
          {[...revealedBySeat.values()].map((r) => {
            const tone = r.delta_bb > 0 ? "up" : r.delta_bb < 0 ? "down" : "even";
            const sign = r.delta_bb > 0 ? "+" : r.delta_bb < 0 ? "−" : "";
            return (
              <li key={r.seat_index} className="hr-reveal-row">
                <span className="hr-reveal-seat">Seat {r.seat_index}</span>
                <span className="cards hr-reveal-cards">
                  {r.hole_cards.map((c, j) => (
                    <Card key={j} card={c} />
                  ))}
                </span>
                <span className={"hr-reveal-delta num sim-net-" + tone}>
                  {sign}
                  {Math.abs(r.delta_bb).toFixed(1)}bb
                </span>
              </li>
            );
          })}
        </ul>
      )}

      {/* Hero cards — always visible (hero sees their own hand every step). */}
      <div className="hr-hero-row">
        <span className="hr-hero-label">Your hand</span>
        <span className="cards hr-hero-cards" aria-label="your hole cards">
          <Card card={hero_cards[0]} />
          <Card card={hero_cards[1]} />
        </span>
      </div>

      {/* Hero verdict panel — only on the hero's own decision steps (never a POST).
          Shows tier + ≈EV-loss + coverage always; the persisted "why" when present,
          else a "no baseline yet"/tier-only line — never fabricated prose. */}
      {step.is_hero && !step.is_post && <HeroVerdict step={step} />}

      {/* Stepper — Next/Prev over the step list. Keyboard-operable with visible
          focus; ← / → also step while the replayer has focus. */}
      <div className="hr-stepper" role="group" aria-label="Step through the hand">
        <button
          type="button"
          className="btn hr-step-btn"
          onClick={() => go(cursor - 1)}
          disabled={atStart}
        >
          ← Prev
        </button>
        <span className="hr-step-count num" aria-live="polite">
          {cursor + 1} / {total}
        </span>
        <button
          type="button"
          className="btn btn-primary hr-step-btn"
          onClick={() => go(cursor + 1)}
          disabled={atEnd}
        >
          Next →
        </button>
      </div>
    </section>
  );
}

// The inline verdict for one hero decision step. Reuses the shared tier
// vocabulary (tierOf) + badge classes so it reads as the same ruling the live
// table + recap show. Freq+EV, never boolean: tier + ≈EV-loss + coverage, plus
// the persisted reasoning when it survived (else tier/EV only — no fabrication).
function HeroVerdict({ step }: { step: ReplayStepView }) {
  const meta = tierOf(step.correctness);
  const graded = step.correctness != null;
  const loss = step.ev_loss_bb ?? 0;
  const showLoss = graded && loss > 0;
  const sizeMeta = step.sizing_correctness != null ? tierOf(step.sizing_correctness) : null;
  return (
    <section className="hr-verdict panel" aria-label="Your decision">
      <div className="hr-verdict-head">
        <span className="hr-verdict-eyebrow">Your decision</span>
        <span className={"sim-badge sim-badge-inline sim-tier-" + meta.tone}>
          <span className="sim-badge-word">{meta.label}</span>
        </span>
        {sizeMeta && <span className="hr-verdict-size">· size: {sizeMeta.label}</span>}
        {showLoss && <span className="hr-verdict-ev num">{fmtEvLoss(loss)}</span>}
      </div>
      <p className="hr-verdict-meta">
        {step.coverage && <span className="hr-verdict-cov">coverage: {step.coverage}</span>}
        {graded && <span className="hr-verdict-approx"> · EV ≈ approximate</span>}
      </p>
      {step.reasoning ? (
        <p className="hr-verdict-why">{step.reasoning}</p>
      ) : (
        <p className="hr-verdict-nobaseline">
          {graded
            ? "The reasoning wasn't recorded for this hand — tier and EV only."
            : "No baseline yet for this spot — nothing to grade against."}
        </p>
      )}
    </section>
  );
}
