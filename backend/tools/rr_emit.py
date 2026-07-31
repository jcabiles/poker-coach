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
      `tail`  — owns everything remaining in the rows it names. Note a tail
                row's treatment is the SAME AT EVERY SEAT (tier weights are
                global and slope tiers skip tail rows), so a row that needs a
                seat-varying band cannot be a tail row — the nit's pairs row
                stopped being one when T-M2 gave CO/BTN their own pair-open
                band (content/personas/ladders/nit.unopened.json `_doc`).
  - a seat may override the slope widths of a single row via `slopes`
    (row -> one width per slope tier), which is how a curve stops one class
    early in a row without perturbing the rest of the ladder.
  - `required_slopes` (optional, top level) — rows whose per-seat `slopes`
    entry is MANDATORY. A row driven entirely by overrides (the nit's pairs
    row: a per-seat open band above a "rest of the row" tier) silently
    TRUNCATES if one seat forgets its entry — the tiers fall back to their
    default widths, the row's bottom goes unplayed, and nothing downstream
    can see it (a truncated row bottom is not a row GAP, so the RR-LINT belt
    reads it as clean). Listing the row here makes the omission fail loud.

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


# The unopened node vocabulary. `call` is a response-node action; a spec that
# wants it is a response-node spec sneaking past the unopened-only scope fence.
_UNOPENED_ACTIONS = frozenset({"raise", "limp", "fold"})
_TIER_KINDS = frozenset({"core", "slope", "tail"})


def _validate(spec: dict[str, Any]) -> None:
    """Authored input is a system boundary — reject a malformed spec loudly.

    Review-hardened (RR-EMIT fan-in): the docstring's "unrepresentable defect
    classes" claim is only true for specs this gate admits, so everything the
    emit pass consumes is checked here — tier shape/kinds/weights, NON-NEGATIVE
    integer widths (a negative width rolled `taken` backwards and re-claimed
    core-owned classes into a second mix), duplicate tail ownership, and the
    unopened-only scope fence (`facing`/action vocabulary).
    """
    if spec.get("facing") != "unopened":
        raise ValueError(
            f"facing {spec.get('facing')!r}: this emitter is unopened-only "
            "(response nodes stay hand-authored, by design)"
        )
    tiers = spec.get("tiers")
    if not isinstance(tiers, list) or not tiers:
        raise ValueError("spec needs a non-empty 'tiers' list")
    kinds = []
    for i, t in enumerate(tiers):
        kind = t.get("kind")
        if kind not in _TIER_KINDS:
            raise ValueError(f"tiers[{i}]: unknown kind {kind!r}")
        kinds.append(kind)
        weights = t.get("weights")
        if not isinstance(weights, dict) or not weights:
            raise ValueError(f"tiers[{i}]: 'weights' must be a non-empty dict")
        bad = set(weights) - _UNOPENED_ACTIONS
        if bad:
            raise ValueError(f"tiers[{i}]: non-unopened action(s) {sorted(bad)}")
        for a, w in weights.items():
            if not isinstance(w, (int, float)) or not 0 < w <= 1:
                raise ValueError(f"tiers[{i}].weights[{a!r}]: {w!r} not in (0, 1]")
        if sum(weights.values()) > 1 + 1e-9:
            raise ValueError(f"tiers[{i}]: weights sum {sum(weights.values())} > 1")
        if kind == "slope":
            width = t.get("width")
            if not isinstance(width, int) or isinstance(width, bool) or width < 0:
                raise ValueError(f"tiers[{i}]: slope 'width' must be an int >= 0")
        if kind == "tail":
            rows = t.get("rows")
            if not isinstance(rows, list) or not rows:
                raise ValueError(f"tiers[{i}]: tail 'rows' must be a non-empty list")
    if kinds.count("core") != 1:
        raise ValueError("spec needs exactly one 'core' tier")
    tail_rows: set[str] = set()
    for t in tiers:
        if t["kind"] != "tail":
            continue
        for r in t["rows"]:
            if r not in ROW_CLASSES:
                raise ValueError(f"tail row {r!r} unknown")
            if r in tail_rows:
                raise ValueError(f"tail row {r!r} owned by two tail tiers")
            tail_rows.add(r)
    n_slope = kinds.count("slope")
    required_slopes = spec.get("required_slopes", [])
    if not isinstance(required_slopes, list):
        raise ValueError("'required_slopes' must be a list of row names")
    for row in required_slopes:
        if row not in ROW_CLASSES:
            raise ValueError(f"required_slopes row {row!r} unknown")
    seats = spec.get("seats")
    if not isinstance(seats, dict) or not seats:
        raise ValueError("spec needs a non-empty 'seats' dict")
    for seat, sd in seats.items():
        depths = sd.get("depths")
        if not isinstance(depths, dict) or not depths:
            raise ValueError(f"{seat}: 'depths' must be a non-empty dict")
        for row, depth in depths.items():
            if row not in ROW_CLASSES:
                raise ValueError(f"{seat}: unknown row {row!r}")
            if not isinstance(depth, int) or isinstance(depth, bool):
                raise ValueError(f"{seat}.{row}: depth {depth!r} must be an int")
            if not 0 <= depth <= len(ROW_CLASSES[row]):
                raise ValueError(f"{seat}.{row}: depth {depth} out of range")
        for row in tail_rows:
            if row not in depths:
                raise ValueError(f"{seat}: tail row {row!r} missing from depths")
        seat_slopes = sd.get("slopes", {})
        for row in required_slopes:
            if row not in seat_slopes:
                raise ValueError(
                    f"{seat}: row {row!r} needs explicit slope widths "
                    f"(required_slopes) — without them its band silently "
                    f"truncates to the tiers' default widths"
                )
        for row, widths in seat_slopes.items():
            if row not in depths:
                raise ValueError(f"{seat}: slope override for unplayed row {row!r}")
            if len(widths) != n_slope:
                raise ValueError(f"{seat}.{row}: expected {n_slope} slope widths")
            for w in widths:
                if not isinstance(w, int) or isinstance(w, bool) or w < 0:
                    raise ValueError(f"{seat}.{row}: slope width {w!r} must be an int >= 0")


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
    """The full `unopened` node list, one node per seat, in spec seat order.

    Every emitted node is round-tripped through the real `PersonaNode` model
    (review-hardened: the CLI path previously emitted unvalidated dicts), so
    the tool cannot print JSON the pack loader would reject.
    """
    _validate(spec)
    from app.domain.content.models import PersonaNode  # tool -> domain is fine

    nodes = [
        {
            "facing": spec["facing"],
            "positions": [seat],
            "mixes": emit_seat_mixes(spec, seat),
        }
        for seat in spec["seats"]
    ]
    for node in nodes:
        PersonaNode.model_validate(node)
    return nodes


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
