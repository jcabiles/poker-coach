"""RR-EMIT — build-time range emitter for persona `unopened` preflop nodes.

    cd backend && python -m tools.rr_emit ../content/personas/ladders/nit.unopened.json

Reads a compact per-persona CURVE SPEC and emits the `unopened` node list a
persona pack already carries (`content/personas/<persona>.json`, `preflop[]`).
Nothing here is imported at runtime: this is a tool, `app/domain/` never sees
it, and the emitted artifact stays committed JSON that the existing loader
reads unchanged.

SCOPE — `unopened` ONLY, and this is a measurement, not a preference. First-in
ranges are 100% floor-representable (every played row is a top-anchored
contiguous segment); response nodes (`vs_rfi`/`vs_3bet`/`vs_4bet`) are not, and
their failures are the identity-bearing part — polar/blocker construction like
"shove AA/KK and A5s-A2s, only call TT/JJ" is a non-prefix set that no smooth
floor can express. Response nodes stay hand-authored, forever, by design.

NOT A PRECEDENT. Do not generalise this to postflop: postflop identity is
levers + merit composition, not ranges. There is no width scalar and no
percentile parameter in the spec, and there must never be one — floors are
authored, never fitted to a target (`raise_pct` is an ASSERTED ANNOTATION that
the emitter never reads; see the spec docs below).

THE MODEL — a smooth curve, not a cliff
---------------------------------------
Hand classes are grouped into 25 ROWS: `pairs` (AA..22) plus, for each high
card A..3, a suited and an offsuit row ordered strongest-kicker-first
(`As` = AKs, AQs, ... A2s). Per seat the author gives each played row ONE
number: the CORE DEPTH, how many classes down the row are played at full
weight. Everything else is per-persona structure:

  - `tiers` — the weight ladder, in the order the mixes are emitted. Each tier
    is one of three kinds:
      `core`  — owns classes [0, depth) of every row in `depths`.
      `slope` — owns the next `width` classes below whatever the tiers above
                took. This is the EDGE-DISCIPLINE tier and its shape is a
                per-persona identity: a nit is cliff-like (one 1-class tier at
                0.5), a station is shallow (wider and/or more tiers, decaying
                slowly). Rows owned by a `tail` tier are never extended by a
                slope tier — the tail IS their edge treatment.
      `tail`  — owns everything remaining in the rows it names (the nit's
                small-pair limp band: raise the top pairs, limp the rest).
  - a seat may override the slope widths of a single row via `slopes`
    (row -> one width per slope tier), which is how a curve stops one class
    early in a row without perturbing the rest of the ladder.

Membership is a partition by construction, so three whole defect classes are
UNREPRESENTABLE rather than merely detected: a row hole (a band is an
interval), a dead token (tiers are disjoint), and weight interleaving (tiers
are emitted strongest-first within a row).

Token synthesis is a fixed rule, not a search, so output is deterministic:
top-anchored multi-class segments become `X+` (`ATs+`, `77+`, `AQo+`), pair
spans become `22-66`, everything else is enumerated one class per token
(the notation has no suited dash-range, `app/domain/content/notation.py`).
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

RANKS = "23456789TJQKA"

# Canonical row order: pairs, then suited A-high -> 3-high, then offsuit.
# Never dict order — this is what makes emitted token order reviewable.
PAIRS_ROW = "pairs"


def _row_classes() -> dict[str, list[str]]:
    """row name -> classes ordered STRONGEST-KICKER-FIRST, canonical row order."""
    rows: dict[str, list[str]] = {PAIRS_ROW: [r + r for r in reversed(RANKS)]}
    for suit in ("s", "o"):
        for hi in reversed(RANKS[1:]):  # A..3; the 2-high row has no kickers
            hi_i = RANKS.index(hi)
            rows[hi + suit] = [hi + RANKS[j] + suit for j in range(hi_i - 1, -1, -1)]
    return rows


ROW_CLASSES = _row_classes()


def _tokens(row: str, classes: list[str], lo: int, hi: int) -> list[str]:
    """Canonical tokens for the half-open segment [lo, hi) of `row`."""
    seg = classes[lo:hi]
    if not seg:
        return []
    if len(seg) == 1:
        return [seg[0]]
    if lo == 0:
        return [seg[-1] + "+"]  # top-anchored: "77+", "ATs+", "AQo+"
    if row == PAIRS_ROW:
        return [f"{seg[-1]}-{seg[0]}"]  # the only dash form the parser accepts
    return list(seg)  # interior suited/offsuit segment: enumerate


def _validate(spec: dict[str, Any]) -> None:
    """Authored input is a system boundary — reject a malformed spec loudly."""
    kinds = [t["kind"] for t in spec["tiers"]]
    if kinds.count("core") != 1:
        raise ValueError("spec needs exactly one 'core' tier")
    tail_rows = {r for t in spec["tiers"] if t["kind"] == "tail" for r in t["rows"]}
    n_slope = kinds.count("slope")
    for seat, sd in spec["seats"].items():
        depths = sd["depths"]
        for row, depth in depths.items():
            if row not in ROW_CLASSES:
                raise ValueError(f"{seat}: unknown row {row!r}")
            if not 0 <= depth <= len(ROW_CLASSES[row]):
                raise ValueError(f"{seat}.{row}: depth {depth} out of range")
        for row in tail_rows:
            if row not in depths:
                raise ValueError(f"{seat}: tail row {row!r} missing from depths")
        for row, widths in sd.get("slopes", {}).items():
            if row not in depths:
                raise ValueError(f"{seat}: slope override for unplayed row {row!r}")
            if len(widths) != n_slope:
                raise ValueError(f"{seat}.{row}: expected {n_slope} slope widths")


def emit_seat_mixes(spec: dict[str, Any], seat: str) -> list[dict[str, Any]]:
    """The mixes of one seat's `unopened` node, in tier declaration order."""
    seat_spec = spec["seats"][seat]
    depths: dict[str, int] = seat_spec["depths"]
    slopes: dict[str, list[int]] = seat_spec.get("slopes", {})
    tiers = spec["tiers"]
    tail_rows = {r for t in tiers if t["kind"] == "tail" for r in t["rows"]}

    played = [r for r in ROW_CLASSES if r in depths]  # canonical order
    taken = dict.fromkeys(played, 0)
    owned: dict[int, list[str]] = {i: [] for i in range(len(tiers))}

    def claim(idx: int, row: str, count: int) -> None:
        classes = ROW_CLASSES[row]
        lo = taken[row]
        hi = min(lo + count, len(classes))
        owned[idx].extend(_tokens(row, classes, lo, hi))
        taken[row] = hi

    for idx, tier in enumerate(tiers):
        if tier["kind"] == "core":
            for row in played:
                claim(idx, row, depths[row])
    slope_no = 0
    for idx, tier in enumerate(tiers):
        if tier["kind"] != "slope":
            continue
        for row in played:
            if row in tail_rows:
                continue  # the tail tier is this row's edge treatment
            override = slopes.get(row)
            claim(idx, row, tier["width"] if override is None else override[slope_no])
        slope_no += 1
    for idx, tier in enumerate(tiers):
        if tier["kind"] == "tail":
            for row in tier["rows"]:
                claim(idx, row, len(ROW_CLASSES[row]))

    return [
        {"combos": ", ".join(owned[i]), "weights": dict(t["weights"])}
        for i, t in enumerate(tiers)
        if owned[i]
    ]


def emit_nodes(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """The full `unopened` node list, one node per seat, in spec seat order."""
    _validate(spec)
    return [
        {
            "facing": spec["facing"],
            "positions": [seat],
            "mixes": emit_seat_mixes(spec, seat),
        }
        for seat in spec["seats"]
    ]


def emit_json(spec: dict[str, Any]) -> str:
    """Byte-stable rendering of `emit_nodes` (2-space indent, no trailing WS)."""
    return json.dumps(emit_nodes(spec), indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spec", help="path to a <persona>.unopened.json curve spec")
    args = ap.parse_args(argv)
    with open(args.spec, encoding="utf-8") as fh:
        spec = json.load(fh)
    sys.stdout.write(emit_json(spec))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
