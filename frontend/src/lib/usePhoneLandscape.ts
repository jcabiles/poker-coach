import { useEffect, useState } from "react";

// The phone held sideways — where the Simulate dock stands as a column on the
// right edge instead of a strip along the bottom.
//
// TWO HOMES, byte-identical: this constant and the
// `@media (max-height: 560px) and (orientation: landscape)` block in
// `src/styles/app.css`. The CSS stands the dock up; this tells the dock's
// toolbar it is now vertical, so its arrow keys and `aria-orientation` match
// what is on screen. No build step derives one from the other, so each names
// the other in a comment. It is its own query rather than
// `usePhoneLayout() && !useIsPortrait()` so that the JS reads the exact string
// the CSS opens with, instead of a combination that has to be proved equal.
export const PHONE_LANDSCAPE_QUERY = "(max-height: 560px) and (orientation: landscape)";

/**
 * Is the viewport a phone held sideways right now? Re-renders on rotation, so
 * the toolbar's orientation follows the dock across the turn.
 *
 * Client-only by construction, like `usePhoneLayout`: the guard is against
 * `matchMedia` being absent in a non-browser test environment, where "not a
 * phone in landscape" is the honest answer.
 */
export function usePhoneLandscape(): boolean {
  const [isLandscape, setIsLandscape] = useState(
    () => typeof window !== "undefined" && window.matchMedia(PHONE_LANDSCAPE_QUERY).matches,
  );

  useEffect(() => {
    const mql = window.matchMedia(PHONE_LANDSCAPE_QUERY);
    const onChange = () => setIsLandscape(mql.matches);
    onChange(); // the phone may have turned between first render and effect
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return isLandscape;
}
