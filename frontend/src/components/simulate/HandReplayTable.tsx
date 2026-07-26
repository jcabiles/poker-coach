import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";

import type { ReplayStepView, HandReplayView, ShowdownSeatView } from "../../api/types";
import Card from "../Card";
import { fmtBb, fmtEvLoss, streetLabel, tierOf } from "./simGrade";
import { buildReplayModel, deriveSeats } from "./replaySeats";
import type { RevealScope } from "./revealRequest";

// Simulate History Replayer (HRT-2) — the two-pane replay reader for the History
// route. Left: the LIVE Simulate felt (same stage/felt/tablering/tseat classes)
// stepping through a past hand. Right: the moves grouped by street with
// click-to-jump. Below: a dedicated "Your decision" verdict panel on hero steps.
//
// Presentational: the parent fetches the HandReplayView; this owns only the step
// cursor. All seat/board/pot/verb reconstruction lives in the pure `replaySeats`
// deriver (HRT-1) — this file never re-derives payload semantics. The shared
// single-column `HandReplay.tsx` (Simulate-route quick-replay) is untouched.
//
// NO-PEEK: villain cards are rendered ONLY from `seat.reveal`, which the deriver
// populates only at the terminal showdown step — nothing on the wire before then.

// Seat-pod geometry — copied from SimTable's slotStyle (geometry DATA, not
// styling; the same asymmetric-radius + flank-bias math, so pods sit identically
// to the live felt). See SimTable.tsx for the rationale behind the 41/38 split
// and the extreme-flank anchor bias.
const FLANK_BIAS_X = 30;
function slotStyle(i: number, n: number): CSSProperties {
  const theta = Math.PI / 2 + (i * 2 * Math.PI) / n;
  const sin = Math.sin(theta);
  const x = 50 + 43 * Math.cos(theta);
  const y = 50 + (sin < 0 ? 41 : 38) * sin;
  const tx = Math.abs(x - 50) > FLANK_BIAS_X ? x : 50;
  return { left: `${x}%`, top: `${y}%`, transform: `translate(-${tx}%, -50%)` };
}

// The full 5-slot board of the hand (deepest board any step reached), so each
// street header can show the cards that street added: flop = 0..3, turn = the
// 4th, river = the 5th. Preflop shows none.
function streetCards(finalBoard: string[], street: string): string[] {
  switch (street) {
    case "flop":
      return finalBoard.slice(0, 3);
    case "turn":
      return finalBoard.slice(3, 4);
    case "river":
      return finalBoard.slice(4, 5);
    default:
      return [];
  }
}

export default function HandReplayTable({
  replay,
  onClose,
  revealScope = null,
  revealedBySeat,
  revealPending = false,
  revealUnavailable = false,
  onReveal,
}: {
  replay: HandReplayView;
  onClose: () => void;
  // ── On-demand villain reveal (History only) ────────────────────────────────
  // Every reveal prop is OPTIONAL with a default so this component's required
  // signature stays `{ replay, onClose }` — identical to the single-column
  // `HandReplay`, which is what keeps the two swappable at the host.
  //
  // The parent (HistoryView) owns the state and the fetch; the rules live in the
  // pure `revealRequest` module. Omit `onReveal` and the controls don't render at
  // all — the replayer behaves exactly as it did before this feature.
  revealScope?: RevealScope | null;
  // seat_index -> revealed seat. Unlike the terminal-step `seat.reveal` from the
  // deriver, these apply at EVERY step: the user opted in explicitly, and seeing
  // the cards during the action is the whole point of reviewing a hand.
  revealedBySeat?: ReadonlyMap<number, ShowdownSeatView>;
  revealPending?: boolean;
  revealUnavailable?: boolean;
  onReveal?: (scope: RevealScope) => void;
}) {
  const model = useMemo(() => buildReplayModel(replay), [replay]);
  const visible = model.visibleSteps.length ? model.visibleSteps : [replay.steps.length - 1];

  // Cursor tracks a position in the VISIBLE (non-post) step list, so Prev/Next/
  // arrows/click never land on a blind post (the felt still folds posts into its
  // derivation). vpos → the real step index the felt renders.
  const [vpos, setVpos] = useState(0);
  useEffect(() => {
    setVpos(0);
  }, [replay.sim_hand_id]);
  const clampedV = Math.min(Math.max(vpos, 0), visible.length - 1);
  const cursor = visible[clampedV];

  const felt = useMemo(() => deriveSeats(replay, cursor), [replay, cursor]);
  const step: ReplayStepView = replay.steps[cursor];

  const atStart = clampedV <= 0;
  const atEnd = clampedV >= visible.length - 1;
  const go = (nv: number) => setVpos(Math.min(Math.max(nv, 0), visible.length - 1));
  const jumpToStep = (stepIndex: number) => {
    const v = visible.indexOf(stepIndex);
    if (v >= 0) setVpos(v);
  };

  // The deepest board the hand reached — for the per-street header mini-cards.
  const finalBoard = useMemo(
    () => replay.steps.reduce((max, s) => (s.board.length > max.length ? s.board : max), [] as string[]),
    [replay],
  );

  // ← / → step over VISIBLE steps. Same input-guard as HandReplay: ignored on
  // form/editable targets and when a modifier is held, so a key meant for another
  // control isn't hijacked. Native <button>s keep Enter/Space for jump/step.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.key !== "ArrowLeft" && e.key !== "ArrowRight") || e.metaKey || e.ctrlKey || e.altKey) {
        return;
      }
      const target = e.target;
      if (
        target instanceof Element &&
        target.closest('input, textarea, select, [contenteditable="true"]')
      ) {
        return;
      }
      e.preventDefault();
      setVpos((v) =>
        Math.min(Math.max(v + (e.key === "ArrowRight" ? 1 : -1), 0), Math.max(visible.length - 1, 0)),
      );
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [visible.length]);

  return (
    <section className="hrt history-replay" aria-label={`Replay of hand ${replay.hand_no}`}>
      <header className="hrt-head">
        <button type="button" className="btn hrt-back" onClick={onClose}>
          ← Back
        </button>
        <h2 className="hrt-title">
          Hand <span className="hrt-title-no num">{replay.hand_no}</span>
        </h2>
        <span className="hrt-hero-note">
          Hero · <span className="hrt-hero-pos">{replay.hero_position}</span>
        </span>
        <span className="cards hrt-hero-cards" aria-label="your hole cards">
          <Card card={replay.hero_cards[0]} />
          <Card card={replay.hero_cards[1]} />
        </span>
      </header>

      <div className="hrt-body">
        {/* LEFT — the live-Simulate felt, stepped. */}
        <div className="hrt-stage-col">
          <div className="stage">
            <div className="felt felt-staged">
              <div className="tablering sim-tablering" role="group" aria-label="table seats">
                <div className="rail" aria-hidden="true" />
                <div className="table-center">
                  {felt.board.length > 0 && (
                    <div className="board" aria-label="community cards">
                      {felt.board.map((c, i) => (
                        <Card key={i} card={c} />
                      ))}
                    </div>
                  )}
                  <div className="pot">Committed {fmtBb(felt.potBb)}bb</div>
                </div>

                {felt.seats.map((seat, i) => {
                  const style = slotStyle(i, felt.seats.length);
                  // Precedence mirrors the live felt (SimTable.tsx:181-186): a
                  // genuine showdown reveal wins over an on-demand one. Because
                  // this branch renders whenever `reveal` is set, an on-demand
                  // card also overrides the `!seat.folded` face-down guard below
                  // — which is what makes "reveal all" show seats that folded
                  // preflop.
                  const reveal = seat.reveal ?? revealedBySeat?.get(seat.seatIndex);
                  const tone =
                    reveal && reveal.delta_bb > 0
                      ? "up"
                      : reveal && reveal.delta_bb < 0
                        ? "down"
                        : "even";
                  return (
                    <div
                      className={
                        "tseat sim-seat" +
                        (seat.isHero ? " hrt-hero-pod" : "") +
                        (seat.folded ? " tseat-folded" : "") +
                        (seat.isActing ? " sim-seat-act" : "") +
                        (seat.lastActionVerb ? " sim-seat-labeled" : "")
                      }
                      key={seat.seatIndex}
                      style={style}
                    >
                      {seat.lastActionVerb && (
                        <span className="sim-actrow">
                          <span className="sim-last-action" title="last action">
                            {seat.lastActionVerb}
                          </span>
                        </span>
                      )}
                      {reveal ? (
                        <span className="cards sim-reveal" aria-label={`${seat.position} shows`}>
                          {reveal.hole_cards.map((c, j) => (
                            <Card key={j} card={c} />
                          ))}
                        </span>
                      ) : seat.isHero ? (
                        <span className="tseat-cards">
                          <Card card={replay.hero_cards[0]} />
                          <Card card={replay.hero_cards[1]} />
                        </span>
                      ) : (
                        !seat.folded && (
                          <span className="tseat-cards">
                            <Card faceDown />
                            <Card faceDown />
                          </span>
                        )
                      )}
                      <span className="sim-meta">
                        <span className="pos">
                          {seat.position}
                          {seat.isButton && (
                            <span className="dealer" aria-label="dealer button">
                              D
                            </span>
                          )}
                        </span>
                      </span>
                      {reveal && (
                        <span className={"hrt-pod-delta num sim-net-" + tone}>
                          {reveal.delta_bb > 0 ? "+" : reveal.delta_bb < 0 ? "−" : ""}
                          {fmtBb(Math.abs(reveal.delta_bb))}bb
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Controls — Prev / Next over visible steps; ← / → mirror them. */}
          <div className="hrt-controls" role="group" aria-label="Step through the hand">
            <button type="button" className="btn hrt-step-btn" onClick={() => go(clampedV - 1)} disabled={atStart}>
              ← Prev
            </button>
            <span className="hrt-step-count num" aria-live="polite">
              {clampedV + 1} / {visible.length}
            </span>
            <button
              type="button"
              className="btn btn-primary hrt-step-btn"
              onClick={() => go(clampedV + 1)}
              disabled={atEnd}
            >
              Next →
            </button>
          </div>

          {/* Reveal villain hands — the two scopes the live table offers, with
              one deliberate difference: clicking the ACTIVE scope hides again,
              so `aria-pressed` is truthful. Never disabled while a request is
              out; the parent's identity guard makes a mid-flight toggle safe,
              and a control that locks up mid-click reads as broken. */}
          {onReveal && (
            <div className="hrt-reveal">
              <div
                className="sim-reveal-actions"
                role="group"
                aria-label="Reveal villain hands"
              >
                {(["last-in", "all"] as const).map((scope) => (
                  <button
                    key={scope}
                    type="button"
                    className={
                      "btn sim-reveal-btn" +
                      (revealScope === scope ? " sim-reveal-btn-on" : "")
                    }
                    aria-pressed={revealScope === scope}
                    aria-busy={revealPending && revealScope === scope}
                    onClick={() => onReveal(scope)}
                  >
                    {scope === "last-in" ? "Reveal last-in" : "Reveal all"}
                  </button>
                ))}
              </div>
              {revealUnavailable && (
                <p className="hrt-reveal-note" role="status">
                  Revealing villain hands is turned off.
                </p>
              )}
            </div>
          )}

          {/* Verdict — only on the hero's own decision steps (never a POST). */}
          {step.is_hero && !step.is_post && <HeroVerdict step={step} />}
        </div>

        {/* RIGHT — moves grouped by street, click-to-jump. */}
        <aside className="hrt-moves" aria-label="Moves">
          <div className="hrt-moves-head">
            <h3 className="hrt-moves-title">Moves</h3>
            <span className="hrt-moves-count num">{model.moves.length}</span>
          </div>
          <div className="hrt-moves-scroll">
            {model.reachedStreets.map((street) => {
              const mini = streetCards(finalBoard, street);
              const rows = model.moves.filter((m) => m.street === street);
              return (
                <section className="hrt-street" key={street}>
                  <h4 className="hrt-street-head">
                    <span className="hrt-street-lbl">{streetLabel(street)}</span>
                    {mini.length > 0 && (
                      <span className="cards hrt-street-mini" aria-hidden="true">
                        {mini.map((c, j) => (
                          <Card key={j} card={c} />
                        ))}
                      </span>
                    )}
                    <span className="hrt-street-rule" aria-hidden="true" />
                  </h4>
                  {rows.map((m) => {
                    const meta = m.isHero && m.correctness != null ? tierOf(m.correctness) : null;
                    return (
                      <button
                        type="button"
                        className={
                          "hrt-move" +
                          (m.isHero ? " hrt-move-hero" : "") +
                          (m.stepIndex === cursor ? " hrt-move-current" : "")
                        }
                        key={m.stepIndex}
                        onClick={() => jumpToStep(m.stepIndex)}
                        aria-current={m.stepIndex === cursor ? "true" : undefined}
                      >
                        <span className="hrt-move-who">{m.position}</span>
                        <span className="hrt-move-what">{m.verb}</span>
                        {meta && (
                          <span className={"sim-badge sim-badge-inline sim-tier-" + meta.tone}>
                            <span className="sim-badge-word">{meta.label}</span>
                          </span>
                        )}
                      </button>
                    );
                  })}
                </section>
              );
            })}
          </div>
        </aside>
      </div>
    </section>
  );
}

// The inline verdict for one hero decision step. Replicated from HandReplay's
// HeroVerdict (that file is the Simulate-route quick-replay and is out of scope
// to edit) — same rules: reuse the shared tier vocabulary + badge classes, freq+EV
// never boolean (tier + ≈EV-loss + coverage), persisted reasoning when it survived
// else a literal tier/EV-only line — never fabricated prose.
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
