import { useEffect, useState } from "react";

// P3a — the ONE phone gate, shared by CSS and JS.
//
// Both halves must stay byte-identical: `app.css`'s "Phone gate" block opens
// with the same query, and the two are what make a control appear in the pinned
// dock (JS) at exactly the widths where the dock exists (CSS). There is no
// build step that can derive one from the other, so the constant is duplicated
// on purpose and each side names the other in a comment.
//
// WHY HEIGHT IS THE FIRST TERM. An Android phone in landscape — the format this
// work exists for — is 800–915px WIDE and only 360–412px TALL. A max-width gate
// never fires there, which is why the measured defect (you cannot see the table
// and your buttons at once) is a vertical one. The max-width half catches the
// same phone held in portrait. A 1280×800 desktop matches neither.
export const PHONE_LAYOUT_QUERY = "(max-height: 560px), (max-width: 560px)";

/**
 * Is the viewport phone-shaped right now? Re-renders on rotation and on a
 * desktop window resize across the gate, so a control can never be left in the
 * dock after the dock has stopped existing.
 *
 * SSR-safe by construction only in the trivial sense: this app is client-only
 * (Vite SPA), so `window` is always there — the guard is against `matchMedia`
 * being absent in a non-browser test environment, where "not a phone" is the
 * honest answer.
 */
export function usePhoneLayout(): boolean {
  const [isPhone, setIsPhone] = useState(
    () => typeof window !== "undefined" && window.matchMedia(PHONE_LAYOUT_QUERY).matches,
  );

  useEffect(() => {
    const mql = window.matchMedia(PHONE_LAYOUT_QUERY);
    const onChange = () => setIsPhone(mql.matches);
    onChange(); // the gate may have moved between first render and effect
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return isPhone;
}
