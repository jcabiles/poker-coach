import { describe, expect, it } from "vitest";

import { errorStatus, isStaleState, withStateToken } from "./staleState";

// The two decisions the P4 client makes about a refused write. The backend pins
// that a mismatched token answers 409 and that an illegal action still answers
// 400; these pin that the client tells those apart and that the token it sends
// survives the trip onto the URL.

describe("isStaleState", () => {
  function rejection(status: number) {
    // Exactly the shape json<T>() throws — the only thing the client sees.
    return new Error(`http://localhost/api/v1/simulate/session/abc/action -> ${status}`);
  }

  it("is true for the conflict the server answers a moved-on table with", () => {
    expect(isStaleState(rejection(409))).toBe(true);
  });

  it("is false for a lost session, an illegal action and a server fault", () => {
    // 404 has its own recovery (the sit-down screen) and 400 is the bucket for
    // every illegal action — treating either as stale would refetch and tell
    // the player the table refreshed when nothing about it had.
    expect(isStaleState(rejection(404))).toBe(false);
    expect(isStaleState(rejection(400))).toBe(false);
    expect(isStaleState(rejection(500))).toBe(false);
  });

  it("is false for anything that is not an Error", () => {
    expect(isStaleState("409")).toBe(false);
    expect(isStaleState(null)).toBe(false);
    expect(isStaleState({ status: 409 })).toBe(false);
  });

  it("reads no status out of an error that carries none", () => {
    expect(errorStatus(new Error("Failed to fetch"))).toBe(null);
  });
});

describe("withStateToken", () => {
  const PATH = "/api/v1/simulate/session/abc/action";

  it("appends the token as the first query parameter", () => {
    expect(withStateToken(PATH, "7.3")).toBe(`${PATH}?state_token=7.3`);
  });

  it("keeps an existing query string instead of replacing it", () => {
    expect(withStateToken(`${PATH}?through_action=4`, "7.3")).toBe(
      `${PATH}?through_action=4&state_token=7.3`,
    );
  });

  it("encodes a token that would otherwise change the URL's shape", () => {
    // A raw & or # would truncate the token or split it into a second
    // parameter, and the server would read a mismatch.
    expect(withStateToken(PATH, "7 &3#x/y")).toBe(`${PATH}?state_token=7%20%263%23x%2Fy`);
  });
});
