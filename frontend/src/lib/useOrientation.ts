import { useEffect, useState } from "react";

// P3b — the orientation half of the phone gate.
//
// THE PHONE CONSTANT NOW HAS THREE HOMES, and they must agree. The other two
// are `PHONE_LAYOUT_QUERY` (`src/lib/usePhoneLayout.ts:16`) and the phone
// gate's own `@media (max-height: 560px), (max-width: 560px)` block in
// `src/styles/app.css`. This file is the third: the portrait block appended at
// the END of that stylesheet opens with
// `@media (max-width: 560px) and (orientation: portrait)`, and the rotate hint
// is rendered by JS exactly where that block styles it. There is no build step
// that derives one from another, so each side names the others in a comment.
//
// ONLY the orientation term lives here. `usePhoneLayout()` already answers the
// width half, and the hint's predicate (`components/simulate/rotateHint.ts`)
// takes both flags — so this hook stays a single media query rather than a
// second, subtly different copy of the gate string.
export const PORTRAIT_QUERY = "(orientation: portrait)";

/**
 * Is the viewport taller than it is wide right now? Re-renders on rotation, so
 * a hint that only makes sense upright cannot survive the turn it asked for.
 *
 * Client-only by construction, like `usePhoneLayout`: this is a Vite SPA, so
 * `window` is always there and the guard is against `matchMedia` being absent
 * in a non-browser test environment, where "not portrait" is the honest answer.
 */
export function useIsPortrait(): boolean {
  const [isPortrait, setIsPortrait] = useState(
    () => typeof window !== "undefined" && window.matchMedia(PORTRAIT_QUERY).matches,
  );

  useEffect(() => {
    const mql = window.matchMedia(PORTRAIT_QUERY);
    const onChange = () => setIsPortrait(mql.matches);
    onChange(); // the phone may have turned between first render and effect
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return isPortrait;
}
