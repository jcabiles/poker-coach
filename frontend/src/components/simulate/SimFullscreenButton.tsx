import { useEffect, useState } from "react";

import { fullscreenControl } from "../../lib/fullscreen";
import { usePhoneLandscape } from "../../lib/usePhoneLandscape";

// Spec §6 — give the felt the phone's whole screen. SimulateView renders this
// only under the phone gate; it renders nothing where the browser cannot go
// full screen (an iPhone), so the button is never a control that does nothing.
//
// ONE instance, placed by CSS: in portrait it is a labelled button in the
// Simulate top bar; held sideways (app.css, the phone-landscape block) it is
// fixed in the top-right corner row beside the ☰, as a glyph whose words stay
// in the accessibility tree. It follows `fullscreenchange`, not its own
// clicks, so leaving full screen by the system back gesture updates it too.
//
// The glyph is the room's art-deco corner brackets: four brass ticks pointing
// out to enter, turned in to leave.

export default function SimFullscreenButton() {
  const fs = fullscreenControl(document);
  const [on, setOn] = useState(fs.isOn);
  const landscape = usePhoneLandscape();

  useEffect(() => {
    const onChange = () => setOn(fullscreenControl(document).isOn());
    onChange(); // it may have changed between first render and effect
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  if (!fs.supported()) return null;

  return (
    <button
      type="button"
      className="btn sim-fullscreen-btn"
      aria-pressed={on}
      onClick={() => void fs.toggle()}
    >
      <svg className="sim-fullscreen-glyph" viewBox="0 0 20 20" aria-hidden="true" fill="none">
        <path d={on ? CORNERS_IN : CORNERS_OUT} strokeWidth="1.75" strokeLinecap="square" />
      </svg>
      {/* Fixed name: aria-pressed already announces on/off, so a changing label would say it twice. */}
      <span className={landscape ? "sim-sr-only" : undefined}>Full screen</span>
    </button>
  );
}

const CORNERS_OUT = "M3 8V3h5M12 3h5v5M17 12v5h-5M8 17H3v-5";
const CORNERS_IN = "M3 8h5V3M12 3v5h5M17 12h-5v5M8 17v-5H3";
