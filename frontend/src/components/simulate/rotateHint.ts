// P3b — is the "turn your phone sideways" line on screen right now?
//
// WHY THIS IS A MODULE AND NOT AN EXPRESSION IN THE VIEW. The predicate reads
// four independent facts, three of which come from somewhere the view cannot
// re-derive by looking at itself: a width media query, an orientation media
// query, and a sessionStorage key. Get any one of them backwards and the
// failure is silent in exactly the wrong direction — a rotate hint on a 1280px
// desktop, or nothing at all on the one screen the hint exists for — and no
// other test in the suite would go red. Same shape of module, and the same
// reason for it, as `handCount.ts`.
//
// The module also owns the STORAGE KEY and its two accessors, because the hint
// now has two hosts — SimulateView's live felt and the History replayer — and
// "dismissed" is one fact shared between them. A second copy of the key in a
// second view is how the two would silently drift apart.
//
// The hint is passive by ruling: it never blocks the felt, never moves the
// controls, and takes its space in the flow above the table like any other
// line of the page.

// The dismissal. sessionStorage, not local: the hint is worth showing again at
// a new sitting and never worth showing twice in one, so it returns when the
// tab is closed rather than on every hand.
export const ROTATE_HINT_KEY = "simulate.rotateHint";

// Has the rotate hint already been waved off in this tab? Absent or garbage
// storage ⇒ not dismissed, which is the safe direction: a hint too many, never
// a table nobody was told to turn.
export function readRotateHintDismissed(): boolean {
  try {
    return window.sessionStorage.getItem(ROTATE_HINT_KEY) === "dismissed";
  } catch {
    /* private-mode storage — unreadable means unknown, so show the hint */
    return false;
  }
}

export function writeRotateHintDismissed(): void {
  try {
    window.sessionStorage.setItem(ROTATE_HINT_KEY, "dismissed");
  } catch {
    /* private-mode storage — setting still applies this session */
  }
}

/** Everything the hint's visibility depends on, named once. */
export interface RotateHintState {
  /** The phone gate — `usePhoneLayout()`, width OR height at or under 560px. */
  phone: boolean;
  /** The orientation half of the gate — `useIsPortrait()`. */
  portrait: boolean;
  /**
   * A felt is rendered: SimulateView's `hand` branch, or the History
   * replayer, which draws the same ring of pods from a finished hand and
   * overlaps them the same way in portrait.
   */
  atTable: boolean;
  /** Dismissed for this tab — sessionStorage `simulate.rotateHint`. */
  dismissed: boolean;
}

/**
 * All four conditions, and nothing else. A desktop, a phone held sideways, the
 * sit-down screen with no table on it, and a tab where the player already
 * pressed "Got it" each answer false on their own.
 */
export function shouldShowRotateHint({
  phone,
  portrait,
  atTable,
  dismissed,
}: RotateHintState): boolean {
  return phone && portrait && atTable && !dismissed;
}
