import { describe, expect, it } from "vitest";

import type { LegalAction, Spot } from "../api/types";
import { legalDecisions } from "./decisions";

const labels = (legal_actions: LegalAction[]) =>
  legalDecisions({ legal_actions } as Spot).map((d) => d.label);

describe("legalDecisions — two-size labels keep their name on one line", () => {
  it("joins Raise small / Raise big with a no-break space, and breaks before the size", () => {
    expect(
      labels([
        { action: "fold" },
        { action: "raise", min_bb: 2, size_bb: 2.5 },
        { action: "raise", min_bb: 2, size_bb: 11 },
      ]),
    ).toEqual(["Fold", "Raise\u00a0small 2.5bb", "Raise\u00a0big 11bb"]);
  });

  it("does the same for Bet small / Bet big", () => {
    expect(
      labels([{ action: "check" }, { action: "bet", min_bb: 3 }, { action: "bet", min_bb: 8 }]),
    ).toEqual(["Check", "Bet\u00a0small 3bb", "Bet\u00a0big 8bb"]);
  });

  it("leaves a single raise size as it was", () => {
    expect(
      labels([
        { action: "call", min_bb: 2 },
        { action: "raise", size_bb: 7 },
      ]),
    ).toEqual(["Call 2bb", "Raise 7bb"]);
  });
});
