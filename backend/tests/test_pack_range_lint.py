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
2. INERT TOKENS — a comma token whose every combo class is already covered
   by earlier mixes of the same node OR by earlier tokens of the same mix
   (review fold: intra-mix duplicates are the same authoring failure mode):
   text that reads as intent but can never fire under first-match-wins
   (`sample_preflop_action`). Partial overlap (e.g. the R10-PRE1 premium
   carve-out peeling TT+ off a wide "55+" mix) is the sanctioned carve-out
   idiom and is NOT flagged — only tokens that are fully dead.
3. WEIGHT INTERLEAVING — within a node, a later mix whose dominant
   NON-FOLD action carries MORE weight than an earlier mix where that same
   action was dominant (e.g. a fringe tier raising 0.85 above a core tier's
   0.7). Tie semantics are explicit (review fold — `max()` over a dict is
   JSON-key-order dependent and 22 shipped mixes are exact ties): EVERY
   non-fold action within 1e-9 of the mix's non-fold maximum is tracked as
   co-dominant, and `fold` is never a dominant action (a rising fold weight
   is not an escalation). Key reordering inside a weights dict is a
   semantic no-op for the engine and cannot move this inventory. Some
   instances are deliberate (premium-first tiering with rising call
   weight; the station's limp 0.5 -> 1.0 IS its limped-aces tell); the
   inventory freezes them.

Entry identity is content-stable (review fold): position keys are SORTED
seat values, and mixes are identified by their first combos token, not
their list index — appending or reordering unrelated content does not
reshuffle entries.

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
    """N-3BSTRATA: a role-tagged node (`role: opener|cold`) is a SEPARATE node
    serving a separate arrival stratum, so its entries must not merge with (or
    silently dedupe against) the other stratum's. The role rides in the
    position key as a `@role` suffix, which leaves every UNTAGGED node's key —
    i.e. every entry frozen in the inventory below — byte-identical."""
    poskey = (
        "*"
        if node.positions is None
        else "/".join(sorted(p.value for p in node.positions))
    )
    if node.role is not None:
        poskey = f"{poskey}@{node.role}"
    return (persona, node.facing, poskey)


def _mix_id(mix) -> str:
    """Content-stable mix identifier: the first combos token."""
    return mix.combos.split(",")[0].strip()


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
            for mix in node.mixes:
                for tok in mix.combos.split(","):
                    tok = tok.strip()
                    if not tok:
                        continue
                    tset = parse_range(tok) & _ALL_CLASSES
                    if tset and tset <= covered:
                        inert.add(key + (_mix_id(mix), tok))
                    covered |= tset
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
            for mix in node.mixes:
                nonfold = {a: w for a, w in mix.weights.items() if a != "fold"}
                if not nonfold:
                    continue
                peak = max(nonfold.values())
                for act in sorted(a for a, w in nonfold.items() if w >= peak - 1e-9):
                    w = nonfold[act]
                    if act in prev_weight and w > prev_weight[act] + 1e-9:
                        interleave.add(
                            key + (_mix_id(mix), act, prev_weight[act], w)
                        )
                    prev_weight[act] = w
    return gaps, inert, interleave


# ============================ THE FROZEN INVENTORY (defects live at HEAD) ====
# Every entry below is a real, measured artifact of the committed packs at the
# time RR-LINT landed. Do not add to these lists to make a failure pass unless
# the slice EXPLICITLY authors a new exception; do remove entries in the same
# commit that fixes them.

_ROW_GAPS = {
    # --- RR-HOLES (2026-07-31): the unopened membership holes + tag's vs_rfi
    # inert tokens (all strictly-dominated typos / dead text) were FIXED —
    # missing class added next to its weaker same-mix neighbor, or dead token
    # removed. Also fixed in this slice, as ordinary dominated typos (no
    # blocker/polar reading applies to plain rank domination): calling_station
    # vs_limpers/vs_rfi 5s+4s holes (loose-caller character, low-risk widen),
    # tag vs_rfi pair/As/Ao holes (77 folded into 22-66→22-77; AQo slotted
    # next to AJo/ATo in the call mix; AQs slotted next to AJs in the
    # 3bet-0.8 mix — theory review F1: exact combo-weighted 3-bet width with
    # AQs@0.8 is 6.91%, INSIDE the (6,7) band; the band edge only trips via
    # Monte Carlo noise, so the range goes where the archetype plays it and
    # the noisy pin was re-tolerated in test_personas.py), and lag
    # vs_rfi Ao/Qs holes (AQo, QTs slotted next to their same-tier
    # neighbors). Entries removed post-fix. (maniac QJo/43s holes, K2o inert
    # token and 4 interleavings were fixed by R10-PRE2's ladder rewrite
    # (#138) — entries removed post-merge.)
    #
    # --- response-layer gaps left in place (RR-HOLES adjudication) ----------
    # lag & maniac vs_4bet As-row: thin suited aces unplayed while AKs and
    # wheel-ace blockers continue — the docstring's own canonical
    # polar/blocker construction. Same CONCEPT, different ranges (Codex
    # review: lag authors AKs + A5s only; maniac authors AKs + A5s-A2s).
    # DECLARED INTENTIONAL, not fixed.
    ("lag", "vs_4bet", "*", "As", ("AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s")),
    # (The MANIAC half of that pair — ("maniac", "vs_4bet", "*", "As",
    # ("AJs".."A6s")) — was RETIRED by N-M4BET (2026-07-31, maniac.json 1.4.0).
    # Not "fixed" in the typo sense and not silently laundered either: the
    # slice authored the node's FULL 169-class coverage (its defect was that
    # 73.6% of the range the maniac 3-bets reached this node with no mix and
    # folded 1.0), so no row of this node has a coverage gap left to record.
    # The polar/blocker construction the entry protected survives in the
    # WEIGHTS — A5s-A2s jam 0.7 with no call leg, the middle suited aces jam
    # 0.3 — and is now pinned by an assertion instead of by absence:
    # test_personas_postflop.py::
    # test_nm4bet_maniac_vs_4bet_suited_ace_construction_is_pinned. That pin
    # is STRICTER than this entry was: this one only recorded that the classes
    # were unplayed and explicitly "does not judge intent", while the pin fixes
    # the wheel tier's exact mix and the strict jam ordering between the two
    # tiers.)
    # (The maniac vs_4bet pair-row gap — 99/88/77 dead between TT/JJ at call
    # 0.5 and 55/66 at 5bet_shove 0.4, RR-HOLES finding T-F3 — was FIXED by
    # T-M2/T-F3, the EV-scale pass RR-HOLES routed it to: the three classes
    # now continue as {5bet_shove 0.25, call 0.15, fold 0.6}, below TT/JJ's
    # 0.5 continue and beside 55/66's 0.4. Entry removed in that commit; the
    # pair row is now contiguous AA-55.)
    # nit vs_limpers pair-row: nit.json is out of scope for this ticket
    # (owned by another ticket) — left untouched, FLAGGED for whoever next
    # rewrites nit.json's vs_limpers node.
    ("nit", "vs_limpers", "*", "pair", ("TT", "99", "88")),
    # R10-3BET (2026-07-31): tag's rewritten vs_3bet deliberately continues
    # ATs and 4-bet-bluffs A5s/A4s while folding A9s-A6s — polar blocker
    # construction, authored exception (dossier: fold-to-3bet 52-65%, 4-bet
    # bluffs from wheel-ace blockers). Lag's old As gap was FIXED in the same
    # rewrite (full suited-ace coverage).
    ("tag", "vs_3bet", "*", "As", ("A9s", "A8s", "A7s", "A6s")),
}

# RR-HOLES (2026-07-31): tag's three vs_rfi inert tokens (ATs/KJs shadowed by
# the earlier 3bet mix, KQo shadowed by the same) were dead text that could
# never fire under first-match-wins — removed rather than relocated, since
# making them live would have downgraded already-stronger-mixed combos
# (ATs/KJs from 3bet 0.8 to call 1.0; KQo likewise) to a weaker treatment,
# which reads as unintended. Entries removed post-fix.
# (maniac vs_rfi JTo inert token and the K2s-mix call interleaving were fixed
# by W5-b4's vs_rfi rewrite — entries removed in that slice's commit.)
_INERT_TOKENS: set[tuple] = set()

# (The four vs_3bet interleavings — nit/passive_fish KK, lag 88-JJ, tag TT-QQ —
# were fixed by R10-3BET's node rewrites: mixes are now ordered so dominant
# non-fold weights only descend; entries removed in that slice's commit.)
_WEIGHT_INTERLEAVING = {
    # limp 0.5 -> 1.0 IS the station's limped-aces tell surfacing at scale —
    # deliberate character, frozen not judged (tie-revealed by the co-dominant
    # semantics; invisible to the earlier dict-order max()).
    ("calling_station", "unopened", "*", "22+", "limp", 0.5, 1.0),
    ("calling_station", "unopened", "UTG", "22+", "limp", 0.5, 1.0),
    ("calling_station", "vs_rfi", "*", "22+", "call", 0.6, 1.0),
    ("maniac", "vs_4bet", "*", "QQ", "5bet_shove", 0.7, 1.0),
    ("nit", "vs_rfi", "*", "88-JJ", "call", 0.65, 1.0),
    ("passive_fish", "vs_4bet", "*", "KK", "call", 0.5, 1.0),
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
