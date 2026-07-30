"""N1 — tiered teaching feedback (verdict / reasoning / deep-dive).

The TieredFeedbackProvider wrapper must populate distinct, non-tautological
tiers on every provider path: preflop, postflop, exploit, and the graceful
not-found fallback. The verdict tier must carry the chosen action's freq/EV.
"""

import asyncio
import random

from factories import make_cbet_spot, make_rfi_spot

from app.domain.action import Decision
from app.domain.archetypes import VillainType
from app.domain.content.registry import build_index, load_preflop_packs
from app.domain.evaluation import Coverage
from app.domain.providers import get_provider
from app.domain.scenarios import build_spot
from app.domain.spot import ActionType, NodeContext, Position, Street

_IDX = build_index(load_preflop_packs())


def _run(coro):
    return asyncio.run(coro)


def _assert_tiers_distinct(res):
    t = res.tiers
    assert t is not None
    assert t.verdict and t.reasoning and t.deep_dive
    assert len({t.verdict, t.reasoning, t.deep_dive}) == 3  # distinct tiers


def test_preflop_tiers_carry_chosen_freq_and_ev():
    p = get_provider()
    spot = make_rfi_spot(hole_cards=("Ah", "Ks"), position=Position.CO)
    res = _run(p.evaluate(spot, Decision(action=ActionType.RAISE, size_bb=2.5)))
    _assert_tiers_distinct(res)
    # game-table F2.6: numeric detail moved out of the verdict — the chosen
    # action's freq + EV (≈ convention) now surface via the deep-dive tier
    # (and the FE's structured EV block), while the verdict stays a short
    # plain-language lede with no EV/frequency numerals.
    assert f"{round(res.chosen_eval.frequency * 100)}%" in res.tiers.deep_dive
    assert f"≈{res.chosen_eval.ev_bb}bb" in res.tiers.deep_dive
    assert "≈" not in res.tiers.verdict
    assert "%" not in res.tiers.verdict
    assert len(res.tiers.verdict) <= 120


def test_preflop_mistake_reasoning_is_non_tautological():
    p = get_provider()
    spot = make_rfi_spot(hole_cards=("Ah", "Ad"), position=Position.UTG)
    res = _run(p.evaluate(spot, Decision(action=ActionType.FOLD)))
    reasoning = res.tiers.reasoning
    assert "is the play" not in reasoning  # more than the old tautology
    assert "gives up money" in reasoning  # the over_fold mechanism phrase (plain voice)
    assert "Blunder" in res.tiers.verdict or "Mistake" in res.tiers.verdict


def test_postflop_tiers_compose_from_rich_tags():
    p = get_provider()
    spot = make_cbet_spot()  # AhKs on AcKdQh — hero is the aggressor
    res = _run(p.evaluate(spot, Decision(action=ActionType.CHECK)))
    _assert_tiers_distinct(res)
    reasoning = res.tiers.reasoning
    # composed from the 4-wide [node, adv, cat, wetness] tags, not the f-string
    assert "c-bet" in reasoning
    assert "is the play" not in reasoning
    assert any(w in reasoning for w in ("dry", "medium", "wet"))
    # deep-dive carries the full per-action mix
    for e in res.per_action:
        assert f"≈{e.ev_bb}bb" in res.tiers.deep_dive


def test_exploit_reasoning_carries_authored_rationale():
    p = get_provider()
    entry = _IDX[(NodeContext.VS_RFI, Position.BTN, Position.CO, 0, VillainType.CALLING_STATION)]
    spot = build_spot(entry, random.Random(1))
    res = _run(p.optimal(spot))
    _assert_tiers_distinct(res)
    assert res.authored_rationale  # provider surfaced the Entry.rationale
    assert "station" in res.tiers.reasoning.lower()  # authored prose reaches the tier
    assert res.tiers.reasoning != res.explanation  # composed, not the flat string


def test_rfi_baseline_authored_rationale_reaches_tiers():
    """N3: a non-exploit RFI entry's authored `rationale` populates
    `authored_rationale` and lands in tiers.reasoning as real strategic prose,
    not the tautological action restated."""
    p = get_provider()
    entry = _IDX[(NodeContext.RFI, Position.CO, None, 0, None)]
    assert entry.rationale  # sanity: the CO RFI entry is authored (N3 tranche)
    spot = build_spot(entry, random.Random(1))
    res = _run(p.optimal(spot))
    _assert_tiers_distinct(res)
    assert res.authored_rationale == entry.rationale
    assert entry.rationale in res.tiers.reasoning
    assert "is the play" not in entry.rationale


def test_vs_rfi_baseline_authored_rationale_reaches_tiers():
    """N3: a non-exploit vs-RFI entry's authored `rationale` populates
    `authored_rationale` and lands in tiers.reasoning."""
    p = get_provider()
    entry = _IDX[(NodeContext.VS_RFI, Position.HJ, Position.UTG, 0, None)]
    assert entry.rationale
    spot = build_spot(entry, random.Random(1))
    res = _run(p.optimal(spot))
    _assert_tiers_distinct(res)
    assert res.authored_rationale == entry.rationale
    assert entry.rationale in res.tiers.reasoning
    assert "is the play" not in entry.rationale


def test_postflop_cbet_authored_rationale_reaches_tiers():
    """N3: the postflop content path — a cbet node's authored `rationale`
    (content/postflop/cbet.json, keyed by opener/caller pairing) reaches
    `authored_rationale` and tiers.reasoning without changing grading."""
    p = get_provider()
    spot = make_cbet_spot()  # BTN vs BB — matches an authored cbet.json entry
    res = _run(p.evaluate(spot, Decision(action=ActionType.CHECK)))
    _assert_tiers_distinct(res)
    assert res.authored_rationale
    assert "is the play" not in res.authored_rationale
    assert res.authored_rationale in res.tiers.reasoning


# --- game-table F2.7/R3: authored rationale is the reasoning lede in all 3 branches ---


def test_authored_rationale_leads_preflop_shape_branch():
    p = get_provider()
    entry = _IDX[(NodeContext.RFI, Position.CO, None, 0, None)]
    res = _run(p.optimal(build_spot(entry, random.Random(1))))
    assert res.authored_rationale
    assert res.tiers.reasoning.startswith(res.authored_rationale)


def test_authored_rationale_leads_postflop_tag_branch():
    p = get_provider()
    res = _run(p.evaluate(make_cbet_spot(), Decision(action=ActionType.CHECK)))
    assert res.authored_rationale
    assert res.tiers.reasoning.startswith(res.authored_rationale)
    assert "c-bet" in res.tiers.reasoning  # tag-derived mechanism template still follows


def test_exploit_villain_sentence_leads_exploit_branch():
    p = get_provider()
    entry = _IDX[(NodeContext.VS_RFI, Position.BTN, Position.CO, 0, VillainType.CALLING_STATION)]
    res = _run(p.optimal(build_spot(entry, random.Random(1))))
    assert res.authored_rationale
    assert res.tiers.reasoning.startswith(f"Versus a calling station: {res.authored_rationale}")
    # authored prose is consumed by the lede — not repeated later in the tier
    assert res.tiers.reasoning.count(res.authored_rationale) == 1


def test_not_found_tiers_degrade_gracefully():
    p = get_provider()
    spot = make_rfi_spot(position=Position.CO).model_copy(
        update={"street": Street.TURN, "board": ["As", "Kd", "2c", "7h"], "node_context": []}
    )
    res = _run(p.evaluate(spot, Decision(action=ActionType.FOLD)))
    assert res.coverage == Coverage.NOT_FOUND
    _assert_tiers_distinct(res)
    assert "No strategy content" in res.tiers.verdict


def test_optimal_call_still_populates_tiers():
    # optimal() (no Decision) — verdict falls back to the best-action summary.
    p = get_provider()
    res = _run(p.optimal(make_rfi_spot(position=Position.CO)))
    _assert_tiers_distinct(res)
    assert res.chosen_eval is None
    assert "Best play" in res.tiers.verdict


# --- structured reasoning_parts (feedback-prose-readability T1) ---


def test_reasoning_parts_present_and_flat_string_is_the_join():
    """The flat `reasoning` is ALWAYS the deterministic join of lead + points —
    the structured form is the source of truth, never parsed from prose."""
    p = get_provider()
    spot = make_rfi_spot(hole_cards=("Ah", "Ad"), position=Position.UTG)
    res = _run(p.evaluate(spot, Decision(action=ActionType.FOLD)))
    parts = res.tiers.reasoning_parts
    assert parts is not None
    assert parts.lead
    assert res.tiers.reasoning == " ".join([parts.lead, *parts.points])


def test_postflop_mistake_parts_have_real_bullets():
    """The tag-template mechanism is decomposed one clause per element (ledger
    R1/C5): even with no authored entry in the mix, a graded postflop mistake
    yields a lead plus at least one bullet — never an empty bullet list."""
    p = get_provider()
    res = _run(p.evaluate(make_cbet_spot(), Decision(action=ActionType.CHECK)))
    parts = res.tiers.reasoning_parts
    assert parts is not None
    assert parts.lead
    assert len(parts.points) >= 1
    assert res.tiers.reasoning == " ".join([parts.lead, *parts.points])


def test_structured_entry_parts_flow_through_provider_seam():
    """T2: an Entry carrying `rationale_parts` (no flat rationale) flows its
    lead + points into tiers.reasoning_parts as separate clauses, its sources
    into parts.sources + the deep-dive, and NEVER into the readable text."""
    from app.domain.evaluation import ReasoningParts
    from app.domain.providers import HeuristicProvider, TieredFeedbackProvider

    key = (NodeContext.RFI, Position.CO, None, 0, None)
    entry = _IDX[key].model_copy(
        update={
            "rationale": None,
            "rationale_parts": ReasoningParts(
                lead="Raise here — this hand opens from the cutoff every time.",
                points=[
                    "It is comfortably inside the opening range.",
                    "Folding gives up a profitable open.",
                ],
                sources="Upswing RFI; doc 01 §2",
            ),
        }
    )
    p = TieredFeedbackProvider(HeuristicProvider({key: entry}))
    res = _run(p.optimal(build_spot(entry, random.Random(1))))
    parts = res.tiers.reasoning_parts
    assert parts.lead.startswith("Raise here — this hand opens")
    assert "It is comfortably inside the opening range." in parts.points
    assert parts.sources == "Upswing RFI; doc 01 §2"
    # flat fields carry the joined text (back-compat for coach / old rows)
    assert res.authored_rationale == entry.rationale_text
    assert res.tiers.reasoning == " ".join([parts.lead, *parts.points])
    # citations demoted: deep-dive only, never the readable text
    assert "§" not in res.tiers.reasoning
    assert "Sources: Upswing RFI; doc 01 §2." in res.tiers.deep_dive


def test_structured_exploit_entry_keeps_villain_prefix():
    """T2 (ledger C7): structured exploit content keeps the `Versus a
    {villain} ({plain descriptor}):` lede so exploit feedback never reads
    like baseline advice."""
    from app.domain.evaluation import ReasoningParts
    from app.domain.providers import HeuristicProvider, TieredFeedbackProvider

    key = (NodeContext.VS_RFI, Position.BTN, Position.CO, 0, VillainType.CALLING_STATION)
    entry = _IDX[key].model_copy(
        update={
            "rationale": None,
            "rationale_parts": ReasoningParts(
                lead="Call wider — this player pays off too often to fold against.",
                points=["Value bets earn extra streets; bluffs lose their point."],
            ),
        }
    )
    p = TieredFeedbackProvider(HeuristicProvider({key: entry}))
    res = _run(p.optimal(build_spot(entry, random.Random(1))))
    parts = res.tiers.reasoning_parts
    assert parts.lead.startswith(
        "Versus a calling station (calls far too often and rarely folds): Call wider"
    )
    assert "Value bets earn extra streets; bluffs lose their point." in parts.points
    # the authored prose is consumed by the lede — not repeated later
    assert res.tiers.reasoning.count("Call wider") == 1


def test_not_found_parts_are_synthetic_lead_only():
    """Early-return branches (Coverage.NOT_FOUND) emit a synthetic lead with an
    empty bullet list (ledger R7/C6) — parts exist whenever tiers exist."""
    p = get_provider()
    spot = make_rfi_spot(position=Position.CO).model_copy(
        update={"street": Street.TURN, "board": ["As", "Kd", "2c", "7h"], "node_context": []}
    )
    res = _run(p.evaluate(spot, Decision(action=ActionType.FOLD)))
    assert res.coverage == Coverage.NOT_FOUND
    parts = res.tiers.reasoning_parts
    assert parts is not None
    assert parts.lead
    assert parts.points == []
    assert res.tiers.reasoning == parts.lead
