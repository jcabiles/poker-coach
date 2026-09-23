import type { KeyboardEvent } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { ActionType, LegalAction, Spot } from "../../api/types";
import { legalDecisions } from "../../lib/decisions";
import { nextToolbarIndex, type ToolbarOrientation } from "../../lib/toolbarKeys";
import { usePhoneLayout } from "../../lib/usePhoneLayout";
import { isAllIn } from "./allIn";

// Simulate S9 hero action bar. Reuses Practice's predetermined-sizing pattern:
// `legalDecisions` resolves the engine's `legal_actions` into labelled,
// keyboard-mapped fold/check/call/bet/raise options at ENGINE-provided sizes —
// there is no free-form bet input (S9 invariant). It only reads
// `spot.legal_actions`, so we pass a minimal spot-shaped view of the hand's
// legal actions (the assertion is safe: no other Spot field is dereferenced).
// The roving-tabindex toolbar wiring mirrors DecisionBar so keyboard travel and
// focus states match the rest of the app.
//
// P3a §5 — on a phone-shaped viewport this bar is pinned under the player's
// thumb (the bottom edge upright, the right edge sideways), and a shove is the one action on the table
// that cannot be taken back. All-in therefore asks twice, the same way
// SimBlindCheck's skip does: the first press arms the button and says what it
// is about to do, the second commits. Fold, call and raise never ask — a
// confirm on an action you can recover from only teaches double-tapping.
export default function SimActionBar({
  legalActions,
  heroStackBb,
  disabled,
  onDecide,
  orientation,
}: {
  legalActions: LegalAction[];
  /** Hero's chips behind — half of "is this button a shove?" (see allIn.ts). */
  heroStackBb: number;
  disabled: boolean;
  onDecide: (action: ActionType, sizeBb?: number | null) => void;
  /** "vertical" where the dock stands as a column (phone landscape). */
  orientation: ToolbarOrientation;
}) {
  // Memoized on the wire array so both the options and the shove flags below
  // hold their identity between renders — which is what lets the keyboard
  // effect below re-subscribe when the decision point moves rather than on
  // every keystroke-induced render.
  const options = useMemo(
    () => legalDecisions({ legal_actions: legalActions } as Spot),
    [legalActions],
  );
  const [activeIndex, setActiveIndex] = useState(0);
  const btnRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const activeSafe = Math.min(activeIndex, options.length - 1);
  const phone = usePhoneLayout();
  // Which button is one press from committing the stack, by index. Local and
  // deliberately short-lived — an armed shove must never survive the decision
  // point it was armed at.
  const [armedIndex, setArmedIndex] = useState<number | null>(null);

  // Which options are shoves. `legalDecisions` maps the engine's legal actions
  // one-to-one and in order, so `legalActions[i]` is the leg option `i` was
  // built from — which is where the all-in ceiling (`max_bb`) lives, since the
  // option itself only carries the size being offered.
  const shoves = useMemo(
    () =>
      options.map((d, i) =>
        phone
          ? isAllIn({
              action: d.action,
              offeredBb: d.size_bb,
              maxBb: legalActions[i]?.max_bb,
              heroStackBb,
            })
          : false,
      ),
    [options, legalActions, phone, heroStackBb],
  );

  // The decision point moved (a new street, a villain raise, a fresh hand), so
  // any armed shove belongs to a hand state that no longer exists. Keyed on the
  // wire array's IDENTITY rather than on the sizes it offers: two consecutive
  // decision points can legitimately offer the same three buttons, and an armed
  // shove surviving into the second of them is a stack lost to one tap.
  const [seenActions, setSeenActions] = useState(legalActions);
  if (seenActions !== legalActions) {
    setSeenActions(legalActions);
    setArmedIndex(null);
  }

  // The single path from "the player chose this option" to the engine. Both the
  // pointer and the keyboard go through it, so the confirm cannot be walked
  // around by pressing R instead of tapping Raise.
  const commit = useCallback(
    (i: number) => {
      const d = options[i];
      if (!d || disabled) return;
      if (shoves[i] && armedIndex !== i) {
        setArmedIndex(i);
        return;
      }
      setArmedIndex(null);
      onDecide(d.action, d.size_bb);
    },
    [options, shoves, disabled, armedIndex, onDecide],
  );

  // Global single-letter shortcuts (F/C/R/K/B/V/E — E = the bigger of two
  // preflop raise sizes, N3) — the same keyboard affordance
  // Practice powers from App.tsx (whose handler is gated to the drill view, so
  // it never fires on Simulate). Local here so the kbd hints on the buttons are
  // truthful. Ignore keys when a form control is focused (roving-tabindex
  // Enter/Space already activates a focused button) — mirrors App.tsx's guard.
  useEffect(() => {
    if (disabled) return;
    const handler = (e: globalThis.KeyboardEvent) => {
      const target = document.activeElement;
      const interactiveTags = ["BUTTON", "INPUT", "SELECT", "TEXTAREA"];
      if (
        target instanceof HTMLElement &&
        (interactiveTags.includes(target.tagName) || target.isContentEditable)
      ) {
        return;
      }
      const i = options.findIndex((d) => d.key === e.key.toUpperCase());
      if (i >= 0) {
        e.preventDefault();
        commit(i);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [options, disabled, commit]);

  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const next = nextToolbarIndex(e.key, orientation, activeSafe, options.length);
    if (next != null) {
      e.preventDefault();
      setActiveIndex(next);
      btnRefs.current[next]?.focus();
    } else if (e.key === "Escape" && armedIndex != null) {
      e.preventDefault();
      setArmedIndex(null);
    }
  };

  const armed = armedIndex != null ? options[armedIndex] : null;

  return (
    <div
      className="decisionbar sim-actionbar"
      role="toolbar"
      aria-label="Your action"
      aria-orientation={orientation}
      onKeyDown={onKeyDown}
    >
      {options.map((d, i) => {
        const isArmed = armedIndex === i;
        return (
          <button
            key={i}
            ref={(el) => {
              btnRefs.current[i] = el;
            }}
            type="button"
            className={
              "btn decision-btn" +
              (d.primary ? " btn-primary" : "") +
              (isArmed ? " sim-action-armed" : "")
            }
            disabled={disabled}
            tabIndex={i === activeSafe ? 0 : -1}
            aria-label={
              isArmed
                ? `Confirm all-in — ${d.label}`
                : `${d.label} (shortcut ${d.key})${shoves[i] ? ", all-in, asks to confirm" : ""}`
            }
            onFocus={() => setActiveIndex(i)}
            onClick={() => commit(i)}
          >
            {isArmed ? "Confirm all-in" : d.label} <kbd aria-hidden="true">{d.key}</kbd>
          </button>
        );
      })}
      {/* Announced rather than only drawn: the armed button's own name changes
          while it holds focus, which screen readers are not obliged to re-read.
          Mirrors SimBlindCheck's skip warning.
          The sentence names the button as it NOW reads: arming renames it to
          "Confirm all-in", so quoting the pre-armed label ("Bet 32.74bb")
          pointed at a word no longer on screen. The size stays in the first
          clause, where it is the thing at risk rather than a button name. */}
      {armed && (
        <p className="sim-action-warn" role="status">
          That is your whole {heroStackBb.toFixed(2)}bb. Press Confirm all-in again to put it in, or
          press Escape to back out.
        </p>
      )}
    </div>
  );
}
