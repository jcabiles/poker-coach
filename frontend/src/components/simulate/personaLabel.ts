// The one player-facing rendering of an archetype's wire value ("calling_station"
// -> "Calling Station"). The seat plate, the rail sheet and the hand-200 check all
// use this so the name a player picks from is character-for-character the name
// they later see on the plate.
export function personaLabel(persona: string): string {
  return persona
    .toLowerCase()
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
