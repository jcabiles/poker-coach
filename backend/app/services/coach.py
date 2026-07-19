"""N6 — the LLM coach seam.

An on-demand "Explain this" turns a graded Simulate decision into a plain-language
concept + fix. Two interchangeable providers behind one Protocol:

- `TemplateCoach` — pure, deterministic, offline. Composes from the always-present
  structured grade fields (correctness / node / action / position / ev). Never
  depends on `ctx.reasoning` (it is None for every recap row after a reload and for
  optimal rows on the live path); when reasoning IS present it is folded in as
  enrichment. This is the default and the fallback.
- `AnthropicCoach` — calls the Claude Messages API via stdlib `urllib` (no new
  dependency — `anthropic`/`httpx` runtime would be ask-first) off the event loop.
  Active only when `ANTHROPIC_API_KEY` is set; any failure falls back to the template.

Lives in services/ (outbound HTTP) — NOT app/domain/ (domain-purity invariant).
Explanations are live-per-request only: no persistence, no migration (R7 no-go).
Privacy: `CoachContext` has no villain-card slot — hero-only by construction.
"""

from __future__ import annotations

import asyncio
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"
_DEFAULT_MODEL = "claude-haiku-4-5-20251001"  # cheap; short outputs. Override via env.
_TIMEOUT_S = 15
_MAX_TOKENS = 400

# node_context -> a plain phrase naming the spot (mirrors feedback._NODE intent).
_NODE_PHRASE = {
    "rfi": "opening the pot",
    "vs_rfi": "facing an open",
    "vs_3bet": "facing a 3-bet",
    "vs_4bet": "facing a 4-bet",
    "blind_defense": "defending your blind",
    "vs_limpers": "facing limpers",
    "cbet": "deciding whether to c-bet as the preflop aggressor",
    "vs_cbet": "defending against a c-bet",
    "vs_check_raise": "facing a check-raise of your c-bet",
    "turn_barrel": "deciding whether to barrel the turn",
    "vs_turn_bet": "facing a turn bet after calling the flop",
    "river_barrel": "deciding whether to barrel the river",
    "vs_river_bet": "facing a river bet after calling flop and turn",
}

_CORRECTNESS_LEAD = {
    "optimal": "This is the standard, highest-EV line here.",
    "acceptable": "This is a defensible line, though not the top choice.",
    "mistake": "This gives up EV against the baseline.",
    "blunder": "This is a costly error against the baseline.",
}


@dataclass(frozen=True)
class CoachContext:
    """Hero-only context for one graded decision. NO villain-card field exists —
    villain hole cards have no channel into any coach prompt."""

    street: str
    chosen_action: str
    correctness: str | None
    sizing_correctness: str | None
    ev_loss_bb: float
    coverage: str
    node_context: str | None
    position: str | None
    facing_position: str | None
    verdict: str | None
    reasoning: str | None
    hero_cards: tuple[str, str] | None
    board: tuple[str, ...]


@runtime_checkable
class CoachProvider(Protocol):
    name: str

    async def explain(self, ctx: CoachContext) -> str:
        """Plain-language concept + fix for a graded decision."""
        ...


def _node_phrase(ctx: CoachContext) -> str:
    if ctx.node_context and ctx.node_context in _NODE_PHRASE:
        return _NODE_PHRASE[ctx.node_context]
    return f"a {ctx.street} decision"


def _spot_clause(ctx: CoachContext) -> str:
    pos = ctx.position or "your seat"
    clause = f"From {pos}, {_node_phrase(ctx)}"
    if ctx.facing_position:
        clause += f" versus {ctx.facing_position}"
    if ctx.hero_cards:
        clause += f" with {ctx.hero_cards[0]}{ctx.hero_cards[1]}"
    if ctx.board:
        clause += f" on {' '.join(ctx.board)}"
    return clause + "."


class TemplateCoach:
    """Deterministic, offline fallback. Non-tautological from structured fields
    alone — safe when reasoning is None (the reload / optimal-row default)."""

    name = "template"

    async def explain(self, ctx: CoachContext) -> str:
        lead = _CORRECTNESS_LEAD.get(
            ctx.correctness or "",
            "This spot has no baseline yet, so treat the read as approximate.",
        )
        parts = [f"{_spot_clause(ctx)} You chose to {ctx.chosen_action}. {lead}"]

        if ctx.correctness in ("mistake", "blunder"):
            parts.append(
                f"Concept: {_node_phrase(ctx).capitalize()} is driven by the range for "
                "this spot, not by any single read — the leak is playing this hand class "
                "against type. Fix: take the baseline line the chart prefers here; the "
                f"give-up is about {ctx.ev_loss_bb:.2f}bb (≈ approximate)."
            )
        elif ctx.correctness in ("optimal", "acceptable"):
            parts.append(
                "Concept: this action keeps your range balanced for this node — the "
                "reason it grades well is that it matches how the whole range should play "
                "the spot, not just this holding."
            )

        if ctx.sizing_correctness:
            parts.append(f"Sizing here grades as {ctx.sizing_correctness}.")

        if ctx.reasoning:
            parts.append(ctx.reasoning)

        return " ".join(parts)


class AnthropicCoach:
    """Claude Messages API via stdlib urllib. Any failure raises; the caller
    (`explain_decision`) falls back to the template."""

    name = "anthropic"

    def __init__(self, api_key: str, model: str | None = None) -> None:
        self._api_key = api_key
        self._model = model or os.environ.get("ANTHROPIC_MODEL") or _DEFAULT_MODEL

    def _prompt(self, ctx: CoachContext) -> str:
        verdict = ctx.correctness or "no baseline yet"
        lines = [
            f"{_spot_clause(ctx)}",
            f"Hero action: {ctx.chosen_action}.",
            f"Baseline verdict: {verdict}"
            + (f", sizing {ctx.sizing_correctness}" if ctx.sizing_correctness else "")
            + f", ≈{ctx.ev_loss_bb:.2f}bb EV lost (approximate, heuristic).",
        ]
        if ctx.reasoning:
            lines.append(f"Grader note: {ctx.reasoning}")
        return "\n".join(lines)

    def _call(self, ctx: CoachContext) -> str:
        system = (
            "You are a concise $2/$3 No-Limit Hold'em coach. In <=120 words give one "
            "plain-language concept and one concrete fix (or, for a good play, why it's "
            "standard). Never claim solver precision; treat all EV figures as approximate. "
            "Use only the facts given."
        )
        body = json.dumps(
            {
                "model": self._model,
                "max_tokens": _MAX_TOKENS,
                "system": system,
                "messages": [{"role": "user", "content": self._prompt(ctx)}],
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            _ANTHROPIC_URL,
            data=body,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": _ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        blocks = payload.get("content") or []
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
        if not text:
            raise ValueError("empty coach response")
        return text

    async def explain(self, ctx: CoachContext) -> str:
        return await asyncio.to_thread(self._call, ctx)


_coach: CoachProvider | None = None


def get_coach() -> CoachProvider:
    """Singleton coach: Anthropic when a key is configured, else the template."""
    global _coach
    if _coach is None:
        key = os.environ.get("ANTHROPIC_API_KEY")
        _coach = AnthropicCoach(key) if key else TemplateCoach()
    return _coach


def reset_coach() -> None:
    """Test seam — drop the cached singleton so env changes take effect."""
    global _coach
    _coach = None


async def explain_decision(ctx: CoachContext) -> tuple[str, str]:
    """Explain a graded decision. Always returns usable text: the primary coach,
    or the template on any failure. Returns (text, source)."""
    coach = get_coach()
    try:
        return await coach.explain(ctx), coach.name
    except Exception:
        if coach.name == "template":
            raise
        return await TemplateCoach().explain(ctx), "template"
