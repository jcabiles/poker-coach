// Arrow-key travel for a roving-tabindex toolbar (WAI-ARIA toolbar pattern).
// Pure so the mapping can be tested without rendering the toolbar.
//
// A vertical toolbar answers ArrowUp/ArrowDown AND keeps ArrowLeft/ArrowRight:
// the Simulate dock turns vertical only in phone landscape, and a keyboard
// user who learned the bar sideways should not find the old keys dead. A
// horizontal toolbar ignores ArrowUp/ArrowDown, as it always has. Travel wraps
// at both ends; Home and End jump to the first and last button.

export type ToolbarOrientation = "horizontal" | "vertical";

/**
 * The index focus should move to, or `null` when the key is not a toolbar
 * travel key here (the caller then leaves the event alone).
 */
export function nextToolbarIndex(
  key: string,
  orientation: ToolbarOrientation,
  index: number,
  count: number,
): number | null {
  if (count <= 0) return null;
  const vertical = orientation === "vertical";
  let target: number;
  if (key === "ArrowRight" || (vertical && key === "ArrowDown")) target = index + 1;
  else if (key === "ArrowLeft" || (vertical && key === "ArrowUp")) target = index - 1;
  else if (key === "Home") target = 0;
  else if (key === "End") target = count - 1;
  else return null;
  return (target + count) % count;
}
