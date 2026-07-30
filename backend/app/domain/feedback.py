"""Tiered teaching feedback — verdict / reasoning / deep-dive (N1).

`compose_tiers` is a pure post-processing pass over ANY StrategyProvider's
EvaluationResult (mounted by providers/tiered.py::TieredFeedbackProvider), so a
future solver provider inherits the teaching layer for free.

It composes ONLY from data already on the result (correctness, chosen_eval,
per_action, rationale_tags, authored_rationale, coverage, is_mixed) plus the
spot. It authors NO new content-pack prose (that is slice N3) — where authored
rationale is missing it builds the best non-tautological reasoning it can from
the rationale tags. EVs are formatted with the "≈" approximate convention.
"""

from __future__ import annotations

from app.domain.action import Decision
from app.domain.archetypes import VillainType
from app.domain.evaluation import (
    ActionEval,
    Correctness,
    Coverage,
    EvaluationResult,
    FeedbackTiers,
    ReasoningParts,
)
from app.domain.spot import Spot

# One-line plain descriptors for the exploit lede's villain prefix — the
# persona name stays (players should learn the vocabulary) with the inline
# explanation following, per the feedback-prose-readability voice rules.
_VILLAIN_DESC = {
    VillainType.CALLING_STATION: "calls far too often and rarely folds",
    VillainType.NIT: "plays only premium hands and folds to pressure",
    VillainType.LAG: "plays lots of hands and plays them aggressively",
    VillainType.PASSIVE_FISH: "plays too many hands and mostly just calls",
    VillainType.TAG: "a solid regular: tight hand selection, aggressive play",
    VillainType.MANIAC: "raises and bluffs at every opportunity",
}

# --- Preflop mistake-shape tags (grading.py::_tags) -> mechanism phrases ---
# Voice (feedback-prose-readability): plain language for a smart adult who
# knows the rules and positions but not pro vocabulary — poker terms stay,
# explained inline in parentheses on first use. Short sentences.
_PRE_SHAPE = {
    "correct": "This matches what the chart plays here.",
    "chart": (
        "The chart decides this spot from the full range of hands, "
        "not from a read on one opponent."
    ),
    "over_fold": (
        "Folding here gives up money: this hand is inside the range the chart "
        "plays, so playing it earns over time — folding takes that to zero."
    ),
    "over_aggressive": (
        "Raising puts in money with a hand that isn't strong enough to raise "
        "here — not enough value (better hands call you) and not enough fold "
        "equity (worse hands rarely fold)."
    ),
    "under_aggressive": (
        "Playing it safe costs value here: the chart raises this hand, and the "
        "quiet line lets opponents see cheap cards with hands that would have "
        "paid you."
    ),
    "loose_call": (
        "Calling with a hand this weak loses money against the range your "
        "opponent is playing — the call bleeds chips over time."
    ),
    "off_chart": "This action isn't in the chart's mix here at all.",
}

# --- Postflop 4-wide tags [node, adv, cat, wetness] (postflop.py) -> clauses ---
# Turn nodes emit a 5-wide tag [node, adv, cat, wetness, turn_class] — the 5th
# tag is backward-compatible with the len(tags) >= 4 dispatch below (flop nodes
# never populate a 5th tag; turn nodes always do, consumed separately below).
# River nodes emit a 6-wide tag [node, adv, cat_effective, wetness, turn_class,
# river_class] — both the turn-card AND river-card sentences surface (S7).
_NODE = {
    "cbet": (
        "You raised before the flop, so the choice is whether to c-bet "
        "(keep betting as the raiser)"
    ),
    "vs_cbet": (
        "Your opponent raised preflop and now bets again — you're facing "
        "a c-bet (continuation bet)"
    ),
    "vs_check_raise": (
        "Your c-bet just got check-raised (they checked, then raised your bet) — "
        "that usually means real strength"
    ),
    "turn_barrel": (
        "You bet the flop; the choice is whether to barrel "
        "(fire a second bet) on the turn"
    ),
    "vs_turn_bet": "You called on the flop and now face a second bet on the turn",
    "river_barrel": (
        "You bet flop and turn; the choice is whether to fire the last bet "
        "on the river"
    ),
    "vs_river_bet": "You called flop and turn and now face the final bet on the river",
    "vs_caller_raise": (
        "You c-bet (kept betting as the raiser) and the preflop caller raised "
        "you — that usually means a strong hand or a big draw"
    ),
    "limped_lead": (
        "Nobody raised before the flop (a limped pot), so the choice is "
        "whether to bet first"
    ),
    "limped_vs_lead": (
        "Nobody raised before the flop (a limped pot), and your opponent "
        "bets into you"
    ),
}
_ADV = {
    "hero": (
        "the range advantage is yours (this board helps your likely hands more "
        "than theirs), so your bets are believable"
    ),
    "villain": "this board fits your opponent's likely hands better than yours, so slow down",
    "neutral": "neither player's likely hands get a clear boost from this board",
    "defender": "your calling range connects with this board better than the bettor's does",
    "aggressor": "the bettor's range hits this board harder than yours does",
}
_CAT = {
    "strong": "A strong hand wants to grow the pot while weaker hands are still willing to pay",
    "weak_made": (
        "A marginal made hand (beats some hands, loses to any real strength) "
        "plays best by keeping the pot small and calling selectively"
    ),
    "draw": (
        "A draw has real chances to improve, so betting it works as a "
        "semi-bluff (it can win the pot now or hit later)"
    ),
    "air": (
        "With no pair and no draw, don't build a pot you can only win by "
        "making better hands fold"
    ),
}
_WET = {
    "dry": (
        "Dry boards (few draws possible) rarely change on later cards, "
        "which favors small, frequent bets"
    ),
    "medium": "This medium texture keeps both players' ranges alive, so balance matters",
    "wet": (
        "Wet boards (many draws possible) can change on every card — "
        "bets get bigger and raises mean real strength"
    ),
}
# tags[4] on turn AND river nodes: the turn card's class vs the flop
# (texture.turn_card_class). River nodes keep this sentence too — a river
# barrel through a scare turn keeps that context alongside the river-card
# sentence below.
_TURN_CLASS = {
    "pairing": "The turn paired the board, so trips and full houses are now possible",
    "flush": "The turn completed a possible flush — a genuine scare card",
    "straight": "The turn completed a possible straight — a genuine scare card",
    "over": "The turn is higher than every flop card, which shifts whose likely hands it helps",
    "blank": "The turn is a blank — it changes little for either player",
}
# tags[5] on river nodes only: the river card's class vs the first four cards
# (texture.river_card_class).
_RIVER_CLASS = {
    "pairing": "The river paired the board, so trips and full houses are now possible",
    "flush": "The river completed a possible flush — a genuine scare card",
    "straight": "The river completed a possible straight — a genuine scare card",
    "over": "The river is higher than the earlier cards, which shifts whose likely hands it helps",
    "blank": "The river is a blank — it changes little for either player",
}


def _pct(freq: float) -> str:
    return f"{round(freq * 100)}%"


def _ev(ev_bb: float) -> str:
    return f"≈{ev_bb}bb"  # matches the FE's approximate-EV convention


def _fmt(e: ActionEval) -> str:
    return f"{e.action.value} {e.size_bb}bb" if e.size_bb else e.action.value


def _verdict(result: EvaluationResult, decision: Decision | None) -> str:
    """One short plain-language lede. Numeric freq/EV detail lives in the FE's
    EV-comparison block and the deep-dive tier, not here (F2.6)."""
    if result.coverage == Coverage.NOT_FOUND:
        return "No strategy content covers this spot yet, so it was graded by a fallback."
    best = result.best_action
    if decision is None or result.chosen_eval is None:
        return f"Best play: {_fmt(best)}."
    if result.correctness == Correctness.OPTIMAL:
        return f"Optimal — {decision.action.value} is the best play here."
    label = (result.correctness or Correctness.ACCEPTABLE).value.capitalize()
    return f"{label} — you chose {decision.action.value}; {_fmt(best)} earns more here."


def _reasoning_parts(spot: Spot, result: EvaluationResult) -> ReasoningParts:
    """Authored, hand-specific rationale is always sentence 1 (the lede) — in
    the postflop tag-branch, the preflop shape-branch, AND the exploit-villain
    branch — with the tag-derived mechanism template following (F2.7/R3).

    Structured contract: one clause per list element (the NODE/ADV/CAT/WET
    mechanism is deliberately decomposed, never bundled), lead = first element,
    points = the rest. The flat `reasoning` string is ALWAYS the " ".join of
    lead + points — never the other way around (no prose parsing)."""
    if result.coverage == Coverage.NOT_FOUND:
        # Early-out branches bypass clause assembly: synthetic lead, no points.
        return ReasoningParts(
            lead="No reasoning is available — this spot is outside the current strategy content.",
            points=[],
        )
    tags = result.rationale_tags
    parts: list[str] = []
    authored = result.authored_rationale_parts
    sources = authored.sources if authored is not None else None
    exploit = "exploit" in tags and spot.villain_type is not None
    if exploit:
        # exploit lede first: the villain-specific sentence IS the hand-specific
        # rationale here (authored rationale is consumed by this lede, so the
        # branches below must not repeat it).
        villain = spot.villain_type.value.replace("_", " ")
        if authored is not None:
            # Structured authored content: villain prefix survives structuring
            # (ledger C7) — the persona name + a plain inline descriptor lead,
            # then the authored bullets follow.
            desc = _VILLAIN_DESC.get(spot.villain_type)
            prefix = f"Versus a {villain} ({desc}): " if desc else f"Versus a {villain}: "
            parts.append(prefix + authored.lead)
            parts.extend(authored.points)
        elif result.authored_rationale:
            parts.append(f"Versus a {villain}: {result.authored_rationale}")
        else:
            parts.append(
                f"This is an exploit (a deliberate shift away from baseline "
                f"strategy) against a {villain}."
            )
    elif authored is not None:
        # Structured authored content (rewritten packs): lead + bullets flow in
        # as separate clauses — never re-joined, never parsed.
        parts.append(authored.lead)
        parts.extend(authored.points)
    elif result.authored_rationale:
        # N3 flat authored content (preflop baseline or postflop node) leads.
        parts.append(result.authored_rationale)
    if tags and tags[0] in _NODE and len(tags) >= 4:
        node, adv, cat, wet = tags[0], tags[1], tags[2], tags[3]
        # One clause per element (not one bundled blob) so the structured
        # renderers get real bullets; the flat join reproduces the old string.
        parts.append(
            f"{_NODE[node]} on a {wet} board: "
            f"{_ADV.get(adv, 'range advantage unclear')}."
        )
        parts.append(f"{_CAT.get(cat, 'Hand category unclear')}.")
        wet_clause = _WET.get(wet, "")
        if wet_clause:
            parts.append(f"{wet_clause}.")
        # 5th tag (turn_class) — turn AND river nodes; names the scare card so
        # the reasoning is non-tautological about what changed on the turn.
        if (
            node in ("turn_barrel", "vs_turn_bet", "river_barrel", "vs_river_bet")
            and len(tags) >= 5
        ):
            turn_class = tags[4]
            parts.append(_TURN_CLASS.get(turn_class, "The turn card shifts the board texture."))
        # 6th tag (river_class) — river nodes only; names the river card so
        # both the turn-card and river-card sentences surface together (S7).
        if node in ("river_barrel", "vs_river_bet") and len(tags) >= 6:
            river_class = tags[5]
            parts.append(_RIVER_CLASS.get(river_class, "The river card shifts the board texture."))
    else:
        shape = next((t for t in tags if t in _PRE_SHAPE), None)
        if shape is not None:
            parts.append(_PRE_SHAPE[shape])
        if result.is_mixed:
            parts.append(
                "This is a genuinely mixed spot — the chart plays more than one "
                "action here on purpose, so the overall mix matters more than "
                "any single decision."
            )
        else:
            best = result.best_action
            parts.append(
                f"The chart isn't mixing here — it plays "
                f"{_fmt(best)} {_pct(best.frequency)} of the time."
            )
    return ReasoningParts(lead=parts[0], points=parts[1:], sources=sources)


def _flat_reasoning(parts: ReasoningParts) -> str:
    """The flat `reasoning` string: deterministic join of lead + points.

    Sources are deliberately excluded (they render as a muted footer / in the
    deep-dive, never in the readable text)."""
    return " ".join([parts.lead, *parts.points])


def _deep_dive(result: EvaluationResult, decision: Decision | None) -> str:
    if result.coverage == Coverage.NOT_FOUND:
        return "No per-action data for this spot — fallback grading only."
    mix = " · ".join(
        f"{_fmt(e)} {_pct(e.frequency)} (EV {_ev(e.ev_bb)})" for e in result.per_action
    )
    parts = [f"Full mix: {mix}."]
    if result.is_mixed:
        parts.append("Mixed node: two or more actions are played at meaningful frequency.")
    if decision is not None and result.chosen_eval is not None:
        parts.append(f"Your action gave up {_ev(result.ev_loss_bb)} against the best line.")
    parts.append(
        f"Coverage: {result.coverage.value} · graded by the {result.provider.value} provider."
    )
    return " ".join(parts)


def compose_tiers(
    spot: Spot, result: EvaluationResult, decision: Decision | None = None
) -> FeedbackTiers:
    """Compose the verdict/reasoning/deep-dive tiers for a graded result.

    `reasoning` is always the flat join of `reasoning_parts` (lead + points) —
    the structured form is the source of truth, the flat string the derivation.
    """
    parts = _reasoning_parts(spot, result)
    deep = _deep_dive(result, decision)
    if parts.sources:
        # Citations demoted out of the readable text (Gate-1 decision): they
        # live on parts.sources for footer rendering AND in the deep-dive.
        deep = f"{deep} Sources: {parts.sources}."
    return FeedbackTiers(
        verdict=_verdict(result, decision),
        reasoning=_flat_reasoning(parts),
        deep_dive=deep,
        reasoning_parts=parts,
    )
