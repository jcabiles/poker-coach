// N6: minimal hash routing — `#/<view>` plus an optional drill-mode segment
// `#/drill/<mode>`. The hash IS the persistence (deep-link + reload restore).
// Invalid or empty hashes fall back to drill/random.
import type { Mode } from "../api/types";

export type View = "drill" | "texture" | "equity";

const VIEW_IDS: readonly View[] = ["drill", "texture", "equity"];

const MODE_IDS: readonly Mode[] = [
  "random",
  "review",
  "leak_focus",
  "exploit",
  "challenge",
  "postflop",
  "vs_cbet",
  "vs_check_raise",
];

export interface Route {
  view: View;
  mode: Mode;
}

export function parseHash(hash: string): Route {
  const [rawView, rawMode] = hash.replace(/^#\/?/, "").split("/");
  const view = VIEW_IDS.find((v) => v === rawView) ?? "drill";
  const mode = (view === "drill" && MODE_IDS.find((m) => m === rawMode)) || "random";
  return { view, mode };
}

export function formatHash(view: View, mode: Mode): string {
  return view === "drill" ? `#/drill/${mode}` : `#/${view}`;
}
