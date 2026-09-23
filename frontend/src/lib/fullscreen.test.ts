import { describe, expect, it } from "vitest";

import { type FullscreenDocument, fullscreenControl } from "./fullscreen";

// A fake document standing in for the browser's Fullscreen API — the one true
// external here. It behaves like the real thing: a granted request sets
// `fullscreenElement` to the root, an exit clears it, and a refused request
// rejects without touching either.
function fakeDocument({ enabled = true, refuse = false } = {}) {
  const root = {} as Element;
  const calls = { request: 0, exit: 0 };
  const doc: FullscreenDocument = {
    fullscreenEnabled: enabled,
    fullscreenElement: null,
    documentElement: {
      requestFullscreen: async () => {
        calls.request += 1;
        if (refuse) throw new TypeError("Permissions check failed");
        (doc as { fullscreenElement: Element | null }).fullscreenElement = root;
      },
    },
    exitFullscreen: async () => {
      calls.exit += 1;
      if (refuse) throw new TypeError("Document not active");
      (doc as { fullscreenElement: Element | null }).fullscreenElement = null;
    },
  };
  return { doc, calls };
}

describe("fullscreenControl — support", () => {
  it("is supported where the browser allows full screen", () => {
    expect(fullscreenControl(fakeDocument().doc).supported()).toBe(true);
  });

  it("is unsupported where it does not (an iPhone, an embedded frame)", () => {
    expect(fullscreenControl(fakeDocument({ enabled: false }).doc).supported()).toBe(false);
  });
});

describe("fullscreenControl — toggle", () => {
  it("starts off, turns on, then turns off again", async () => {
    const { doc, calls } = fakeDocument();
    const fs = fullscreenControl(doc);
    expect(fs.isOn()).toBe(false);

    await fs.toggle();
    expect(fs.isOn()).toBe(true);
    expect(calls).toEqual({ request: 1, exit: 0 });

    await fs.toggle();
    expect(fs.isOn()).toBe(false);
    expect(calls).toEqual({ request: 1, exit: 1 });
  });

  it("reads the state from the document, so a full screen entered elsewhere is left, not re-entered", async () => {
    const { doc, calls } = fakeDocument();
    (doc as { fullscreenElement: Element | null }).fullscreenElement = {} as Element;
    const fs = fullscreenControl(doc);
    expect(fs.isOn()).toBe(true);

    await fs.toggle();
    expect(fs.isOn()).toBe(false);
    expect(calls).toEqual({ request: 0, exit: 1 });
  });

  it("stays off when the browser refuses the request, without throwing", async () => {
    const { doc, calls } = fakeDocument({ refuse: true });
    const fs = fullscreenControl(doc);

    await expect(fs.toggle()).resolves.toBeUndefined();
    expect(fs.isOn()).toBe(false);
    expect(calls).toEqual({ request: 1, exit: 0 });
  });

  it("stays on when the browser refuses to exit, without throwing", async () => {
    const { doc, calls } = fakeDocument({ refuse: true });
    (doc as { fullscreenElement: Element | null }).fullscreenElement = {} as Element;
    const fs = fullscreenControl(doc);

    await expect(fs.toggle()).resolves.toBeUndefined();
    expect(fs.isOn()).toBe(true);
    expect(calls).toEqual({ request: 0, exit: 1 });
  });
});
