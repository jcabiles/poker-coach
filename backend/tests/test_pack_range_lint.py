"""RR-LINT — frozen defect inventory for preflop persona packs (tripwire belt).

Three structural lints over every preflop node of every persona pack, each
compared against a COMMITTED INVENTORY of the defects live at HEAD:

1. ROW GAPS — within a hand-class "row" (the pairs row, or a fixed
   high-card+suitedness row like "Ts" = T9s..T2s), a class that is strictly
   stronger than a played class of the same row is itself unplayed. In the
   `unopened` membership layer every known instance is a strictly-dominated
   authoring typo (e.g. tag BTN plays T5s and T3s but skips T4s). In response
   nodes some instances are DELIBERATE polar/blocker poker (e.g. lag vs_4bet
   continues A5s-A2s but folds AQs-A6s) — the inventory records reality and
   forces any change to be a conscious one; it does not judge intent.
2. INERT TOKENS — a comma token in a mix whose every combo class is already
   covered by earlier mixes of the same node: text that reads as intent but
   can never fire under first-match-wins (`sample_preflop_action`). Partial
   overlap (e.g. the R10-PRE1 premium carve-out peeling TT+ off a wide "55+"
   mix) is the sanctioned carve-out idiom and is NOT flagged — only tokens
   that are fully dead.
3. WEIGHT INTERLEAVING — within a node, a later mix whose dominant action
   carries MORE weight than an earlier mix with the same dominant action
   (e.g. a fringe tier raising 0.85 above a core tier's 0.7). Some instances
   are deliberate (premium-first tiering with rising call weight); the
   inventory freezes them.

TRIPWIRE SEMANTICS (this suite PASSES at HEAD by design — it is a
PRESERVATION-plus-tripwire check, not a defect gate): the computed defect set
must EQUAL the inventory exactly. Introducing a NEW defect fails the test;
FIXING a listed defect also fails, forcing the inventory constant to be
emptied of that entry in the same commit as the fix — the anti-laundering
property. Burn-down plan (range-representation decisions, owner-adjudicated
2026-07-30): `RR-HOLES` empties the `unopened` gap + inert entries after the
R10 preflop lane closes; response-layer entries are adjudicated (fixed or
declared intentional in place) by the slices that rewrite those nodes
(W5-b4, R10-3BET). Lane slices that legitimately reshape maniac `unopened`
nodes (R10-PRE2) update the maniac entries in the same commit.

Source: docs/ai-dlc/reports/range-representation-design.md (RR-LINT sketch);
defects independently found by the 2026-07-30 range-representation review.
"""

from __future__ import annotations

import pytest

from app.domain.content.notation import parse_range
from app.domain.personas import load_persona_packs

RANKS = "23456789TJQKA"

_ALL_CLASSES: set[str] = set()
for _i, _a in enumerate(RANKS):
    for _j in range(_i):
        _ALL_CLASSES |= {_a + RANKS[_j] + "s", _a + RANKS[_j] + "o"}
    _ALL_CLASSES.add(_a + _a)


def _rows():
    """Yield (row_name, classes ordered strongest-kicker-first)."""
    yield ("pair", [r + r for r in reversed(RANKS)])
    for hi in reversed(RANKS[1:]):  # A down to 3 (2-high has no kickers)
        below = [r for r in RANKS if RANKS.index(r) < RANKS.index(hi)]
        for s in ("s", "o"):
            yield (hi + s, [hi + k + s for k in reversed(below)])


def _node_key(persona: str, node) -> tuple[str, str, str]:
    poskey = "*" if node.positions is None else "/".join(p.value for p in node.positions)
    return (persona, node.facing, poskey)


def _scan_packs():
    """Compute (gaps, inert, interleave) defect sets over all packs."""
    packs = load_persona_packs()
    gaps: set[tuple] = set()
    inert: set[tuple] = set()
    interleave: set[tuple] = set()
    for vt in sorted(packs, key=lambda v: v.value):
        pack = packs[vt]
        for node in pack.preflop:
            key = _node_key(vt.value, node)
            covered: set[str] = set()
            for mi, mix in enumerate(node.mixes):
                for tok in mix.combos.split(","):
                    tok = tok.strip()
                    if not tok:
                        continue
                    tset = parse_range(tok) & _ALL_CLASSES
                    if tset and tset <= covered:
                        inert.add(key + (mi, tok))
                covered |= parse_range(mix.combos) & _ALL_CLASSES
            played = covered
            for rname, ordered in _rows():
                missing_stronger = tuple(
                    cls
                    for idx, cls in enumerate(ordered)
                    if cls not in played
                    and any(c in played for c in ordered[idx + 1 :])
                )
                if missing_stronger:
                    gaps.add(key + (rname, missing_stronger))
            prev_weight: dict[str, float] = {}
            for mi, mix in enumerate(node.mixes):
                if not mix.weights:
                    continue
                act = max(mix.weights, key=lambda a: mix.weights[a])
                w = mix.weights[act]
                if act in prev_weight and w > prev_weight[act] + 1e-9:
                    interleave.add(key + (mi, act, prev_weight[act], w))
                prev_weight[act] = w
    return gaps, inert, interleave


# ============================ THE FROZEN INVENTORY (defects live at HEAD) ====
# Every entry below is a real, measured artifact of the committed packs at the
# time RR-LINT landed. Do not add to these lists to make a failure pass unless
# the slice EXPLICITLY authors a new exception; do remove entries in the same
# commit that fixes them.

_ROW_GAPS = {
    # --- unopened membership holes: all strictly-dominated typos (RR-HOLES) --
    ("calling_station", "unopened", "*", "5s", ("54s",)),
    ("maniac", "unopened", "UTG", "Qo", ("QJo",)),
    ("maniac", "unopened", "BTN", "4s", ("43s",)),
    ("passive_fish", "unopened", "*", "5s", ("54s",)),
    ("tag", "unopened", "BTN", "Ts", ("T4s",)),
    ("tag", "unopened", "BB", "Ks", ("K4s",)),
    ("tag", "unopened", "BB", "Qs", ("Q6s",)),
    # --- response-layer gaps: recorded as-is; several are deliberate polar /
    # blocker construction (adjudicated by W5-b4 / R10-3BET when those nodes
    # are rewritten) -----------------------------------------------------------
    ("calling_station", "vs_limpers", "*", "5s", ("54s", "53s")),
    ("calling_station", "vs_limpers", "*", "4s", ("43s",)),
    ("calling_station", "vs_rfi", "*", "5s", ("54s", "53s")),
    ("calling_station", "vs_rfi", "*", "4s", ("43s",)),
    ("lag", "vs_rfi", "*", "Ao", ("AQo",)),
    ("lag", "vs_rfi", "*", "Qs", ("QTs",)),
    ("lag", "vs_3bet", "*", "As", ("A9s", "A8s", "A7s", "A6s")),
    ("lag", "vs_4bet", "*", "As", ("AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s")),
    ("maniac", "vs_4bet", "*", "pair", ("99", "88", "77")),
    ("maniac", "vs_4bet", "*", "As", ("AJs", "ATs", "A9s", "A8s", "A7s", "A6s")),
    ("nit", "vs_limpers", "*", "pair", ("TT", "99", "88")),
    ("passive_fish", "vs_rfi", "*", "5s", ("54s",)),
    ("tag", "vs_rfi", "*", "pair", ("77",)),
    ("tag", "vs_rfi", "*", "As", ("AQs",)),
    ("tag", "vs_rfi", "*", "Ao", ("AQo",)),
    ("tag", "vs_3bet", "*", "As", ("ATs", "A9s", "A8s", "A7s", "A6s")),
}

_INERT_TOKENS = {
    ("maniac", "unopened", "BTN", 2, "K2o"),
    ("maniac", "vs_rfi", "*", 2, "JTo"),
    ("tag", "vs_rfi", "*", 2, "ATs"),
    ("tag", "vs_rfi", "*", 2, "KJs"),
    ("tag", "vs_rfi", "*", 3, "KQo"),
}

_WEIGHT_INTERLEAVING = {
    ("calling_station", "vs_rfi", "*", 1, "call", 0.6, 1.0),
    ("lag", "vs_3bet", "*", 2, "call", 0.6, 0.75),
    ("maniac", "unopened", "UTG2", 2, "raise", 0.8, 0.85),
    ("maniac", "unopened", "LJ", 2, "raise", 0.8, 0.85),
    ("maniac", "unopened", "BTN", 2, "raise", 0.7, 0.85),
    ("maniac", "unopened", "BB", 2, "raise", 0.8, 0.85),
    ("maniac", "vs_rfi", "*", 2, "call", 0.55, 0.9),
    ("maniac", "vs_4bet", "*", 1, "5bet_shove", 0.7, 1.0),
    ("nit", "vs_rfi", "*", 2, "call", 0.65, 1.0),
    ("tag", "vs_3bet", "*", 2, "call", 0.6, 0.8),
}


@pytest.fixture(scope="module")
def scan():
    if not load_persona_packs():
        pytest.skip("no persona packs")
    return _scan_packs()


def _diff_message(kind: str, computed: set, inventory: set) -> str:
    new = sorted(computed - inventory)
    fixed = sorted(inventory - computed)
    parts = []
    if new:
        parts.append(
            f"NEW {kind} introduced (fix them, or explicitly author the "
            f"exception into the inventory): {new}"
        )
    if fixed:
        parts.append(
            f"{kind} FIXED but still listed (remove from the inventory in "
            f"this same commit): {fixed}"
        )
    return " || ".join(parts)


def test_row_gaps_match_frozen_inventory(scan):
    gaps, _, _ = scan
    assert gaps == _ROW_GAPS, _diff_message("row gaps", gaps, _ROW_GAPS)


def test_inert_tokens_match_frozen_inventory(scan):
    _, inert, _ = scan
    assert inert == _INERT_TOKENS, _diff_message("inert tokens", inert, _INERT_TOKENS)


def test_weight_interleaving_matches_frozen_inventory(scan):
    _, _, interleave = scan
    assert interleave == _WEIGHT_INTERLEAVING, _diff_message(
        "weight interleavings", interleave, _WEIGHT_INTERLEAVING
    )
