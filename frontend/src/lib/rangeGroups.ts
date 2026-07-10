/**
 * rangeGroups — parse a poker range descriptor (the backend's comma-separated
 * `villain_range` string) into readable, run-collapsed chip groups for display.
 *
 * The backend ships ranges like `"22-99, ATs+, KJs+, QJs, AJo+, KQo"`. Rendered
 * raw that is an unreadable comma list; this module expands it into the 169
 * starting-hand-class space, groups the classes into POCKET PAIRS / SUITED /
 * OFFSUIT, and collapses consecutive runs into single chips ("22-99",
 * "A2s-A9s"), keeping singletons as-is.
 *
 * Grammar mirrors backend/app/domain/content/notation.py exactly so the split
 * is faithful (same tokens: `*`, `77`, `77+`, `QQ-99`, `AKs`, `AKo`, `AK`,
 * `ATs+`). Losslessness is guaranteed by `expandGroups`: the union of every
 * collapsed chip re-expands to precisely the parsed class set (see
 * `isLossless`). Pure — no DOM, no side effects.
 */

// Low → high, matching notation.py's RANKS.
const RANKS = "23456789TJQKA";
const IDX: Record<string, number> = Object.fromEntries(
  [...RANKS].map((r, i) => [r, i]),
);

/** Combos per hand class (used for the "N combos" header). */
export function combosForClass(cls: string): number {
  if (cls.length === 2) return 6; // pair
  return cls.endsWith("s") ? 4 : 12; // suited / offsuit
}

// ---- expansion (compact token → set of 169 classes) -----------------------

function allHands(): Set<string> {
  const hands = new Set<string>();
  for (let i = 0; i < RANKS.length; i++) {
    for (let j = 0; j < RANKS.length; j++) {
      if (i === j) hands.add(RANKS[i] + RANKS[j]);
      else if (i > j) {
        hands.add(RANKS[i] + RANKS[j] + "s");
        hands.add(RANKS[i] + RANKS[j] + "o");
      }
    }
  }
  return hands;
}

function expandPair(rank: string, plus: boolean): string[] {
  const idx = IDX[rank];
  if (plus) {
    const out: string[] = [];
    for (let k = idx; k < RANKS.length; k++) out.push(RANKS[k] + RANKS[k]);
    return out;
  }
  return [rank + rank];
}

function expandTwo(
  r1: string,
  r2: string,
  suit: string | null,
  plus: boolean,
): string[] {
  if (IDX[r1] < IDX[r2]) [r1, r2] = [r2, r1];
  const suits = suit === "s" || suit === "o" ? [suit] : ["s", "o"];
  let kickers: string[];
  if (plus) {
    kickers = [];
    for (let k = IDX[r2]; k < IDX[r1]; k++) kickers.push(RANKS[k]);
  } else {
    kickers = [r2];
  }
  const out: string[] = [];
  for (const k of kickers) for (const s of suits) out.push(r1 + k + s);
  return out;
}

function expandPairRange(a: string, b: string): string[] {
  if (a.length === 2 && a[0] === a[1] && b.length === 2 && b[0] === b[1]) {
    const [lo, hi] = [IDX[a[0]], IDX[b[0]]].sort((x, y) => x - y);
    const out: string[] = [];
    for (let k = lo; k <= hi; k++) out.push(RANKS[k] + RANKS[k]);
    return out;
  }
  throw new Error(`unsupported range token: ${a}-${b} (only pair ranges)`);
}

function expandToken(raw: string): string[] {
  const tok = raw.trim();
  if (!tok) return [];
  if (tok === "*") return [...allHands()];
  const plus = tok.endsWith("+");
  const core = plus ? tok.slice(0, -1) : tok;
  if (core.includes("-") && !plus) {
    const [a, b] = core.split("-", 2);
    return expandPairRange(a.trim(), b.trim());
  }
  if (core.length === 2 && core[0] === core[1]) return expandPair(core[0], plus);
  if (core.length === 2 || core.length === 3) {
    const r1 = core[0];
    const r2 = core[1];
    if (!(r1 in IDX) || !(r2 in IDX))
      throw new Error(`unparseable range token: ${tok}`);
    const suit = core.length === 3 ? core[2] : null;
    if (suit !== null && suit !== "s" && suit !== "o")
      throw new Error(`bad suit in token: ${tok}`);
    return expandTwo(r1, r2, suit, plus);
  }
  throw new Error(`unparseable range token: ${tok}`);
}

/** Expand a range spec into its set of 169-space hand classes. */
export function parseRange(spec: string): Set<string> {
  const out = new Set<string>();
  for (const tok of spec.split(",")) for (const c of expandToken(tok)) out.add(c);
  return out;
}

// ---- run-collapsing --------------------------------------------------------

/**
 * Collapse a sorted list of classes that share a "ladder" into chips, folding
 * consecutive rungs into "first-last" and leaving gaps/singletons alone.
 * `rung` maps a class to its ladder index; entries are pre-sorted ascending.
 */
function collapseLadder(
  entries: { cls: string; rung: number }[],
): string[] {
  const chips: string[] = [];
  let runStart = 0;
  for (let i = 1; i <= entries.length; i++) {
    const broken =
      i === entries.length || entries[i].rung !== entries[i - 1].rung + 1;
    if (broken) {
      const first = entries[runStart];
      const last = entries[i - 1];
      chips.push(first === last ? first.cls : `${first.cls}–${last.cls}`);
      runStart = i;
    }
  }
  return chips;
}

export interface RangeGroups {
  /** Total concrete 2-card combos across the whole range. */
  combos: number;
  pairs: string[];
  suited: string[];
  offsuit: string[];
  /** The parsed class set — the losslessness oracle. */
  classes: Set<string>;
}

/**
 * Parse a range descriptor into display groups with run-collapsed chips.
 *
 * Pairs collapse along the pair ladder (22,33,…,AA). Suited/offsuit collapse
 * along the kicker ladder within a fixed high card (A2s,A3s,…,AKs), which is
 * how shipped ranges read ("A2s-A9s"); cross-high-card runs are never merged.
 */
export function groupRange(spec: string): RangeGroups {
  const classes = parseRange(spec);

  const pairEntries: { cls: string; rung: number }[] = [];
  // suited/offsuit keyed by high card → ascending kicker entries
  const suitedBy: Record<string, { cls: string; rung: number }[]> = {};
  const offsuitBy: Record<string, { cls: string; rung: number }[]> = {};

  for (const cls of classes) {
    if (cls.length === 2) {
      pairEntries.push({ cls, rung: IDX[cls[0]] });
      continue;
    }
    const hi = cls[0];
    const lo = cls[1];
    const bucket = cls.endsWith("s") ? suitedBy : offsuitBy;
    (bucket[hi] ||= []).push({ cls, rung: IDX[lo] });
  }

  pairEntries.sort((a, b) => a.rung - b.rung);
  const pairs = collapseLadder(pairEntries);

  // Suited/offsuit chips ordered by high card (high → low, the way ranges are
  // conventionally written: aces first), kickers ascending within each.
  const collapseByHi = (
    by: Record<string, { cls: string; rung: number }[]>,
  ): string[] => {
    const out: string[] = [];
    const his = Object.keys(by).sort((a, b) => IDX[b] - IDX[a]);
    for (const hi of his) {
      by[hi].sort((a, b) => a.rung - b.rung);
      out.push(...collapseLadder(by[hi]));
    }
    return out;
  };

  const suited = collapseByHi(suitedBy);
  const offsuit = collapseByHi(offsuitBy);

  let combos = 0;
  for (const cls of classes) combos += combosForClass(cls);

  return { combos, pairs, suited, offsuit, classes };
}

// ---- losslessness guarantee ------------------------------------------------

/**
 * Re-expand a single collapsed chip (e.g. "A2s-A9s", "22-99", "KQo") back to
 * its member classes. Inverse of the collapsing above.
 */
export function expandChip(chip: string): string[] {
  const [a, b] = chip.split("–"); // en-dash separator
  if (b === undefined) return [a];
  // Pair run: "22"-"99" → same-length 2-char pairs.
  if (a.length === 2 && a[0] === a[1]) {
    const [lo, hi] = [IDX[a[0]], IDX[b[0]]].sort((x, y) => x - y);
    const out: string[] = [];
    for (let k = lo; k <= hi; k++) out.push(RANKS[k] + RANKS[k]);
    return out;
  }
  // Suited/offsuit run within a fixed high card: "A2s"-"A9s".
  const hi = a[0];
  const suit = a[2];
  const [lo, hiK] = [IDX[a[1]], IDX[b[1]]].sort((x, y) => x - y);
  const out: string[] = [];
  for (let k = lo; k <= hiK; k++) out.push(hi + RANKS[k] + suit);
  return out;
}

/** Expand grouped chips back into the flat class set. */
export function expandGroups(g: RangeGroups): Set<string> {
  const out = new Set<string>();
  for (const chip of [...g.pairs, ...g.suited, ...g.offsuit])
    for (const cls of expandChip(chip)) out.add(cls);
  return out;
}

/**
 * Lossless property: the grouped chips re-expand to exactly the parsed class
 * set (no dropped or invented classes). True for every well-formed spec.
 */
export function isLossless(spec: string): boolean {
  const g = groupRange(spec);
  const back = expandGroups(g);
  if (back.size !== g.classes.size) return false;
  for (const c of g.classes) if (!back.has(c)) return false;
  return true;
}
