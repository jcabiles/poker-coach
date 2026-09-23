// The phone table's full-screen switch (spec §6). Takes the document as an
// argument rather than reaching for the global, so the whole contract can be
// tested against a fake one: the browser API is the one true external here.
//
// Deliberately absent: `screen.orientation.lock()`. It needs a secure context,
// and the trainer is served to the phone over plain `http://` on the home wifi,
// so it would reject every time. Holding the phone sideways is the player's job.

/** The slice of `Document` this module touches. A real `document` satisfies it. */
export interface FullscreenDocument {
  readonly fullscreenEnabled: boolean;
  readonly fullscreenElement: Element | null;
  readonly documentElement: { requestFullscreen(): Promise<void> };
  exitFullscreen(): Promise<void>;
}

export interface FullscreenControl {
  /** The browser allows this page to go full screen (false on an iPhone). */
  supported(): boolean;
  /** The page is full screen right now, however it got there. */
  isOn(): boolean;
  /** Enter full screen when off, leave it when on. Resolves once the request settles. */
  toggle(): Promise<void>;
}

export function fullscreenControl(doc: FullscreenDocument): FullscreenControl {
  const isOn = () => doc.fullscreenElement !== null;
  return {
    supported: () => doc.fullscreenEnabled,
    isOn,
    toggle: async () => {
      try {
        if (isOn()) await doc.exitFullscreen();
        else await doc.documentElement.requestFullscreen();
      } catch {
        // Ignored on purpose: a refused request (no user gesture, a browser
        // policy) changes nothing, no `fullscreenchange` fires, and the button
        // keeps its current state — there is nothing to undo and nothing to retry.
      }
    },
  };
}
