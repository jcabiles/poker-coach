"""Persona preflop engine — samples frequency-mixed bot actions from persona packs.

Pure domain: strategy lives in `content/personas/*.json` (PersonaPack); this
engine is generic. The rng is injected per call (per-hand instance, never
module-level) — same convention as `table/deck.py` and `challenge.py`.
"""

from __future__ import annotations

import random
from functools import cache
from pathlib import Path
from typing import NamedTuple

from app.domain.archetypes import VillainType
from app.domain.content.models import PersonaPack
from app.domain.content.notation import hole_cards_to_class, parse_range
from app.domain.spot import ActionType, Card, Position

# backend/app/domain/personas.py -> parents[3] == repo root
PERSONA_DIR = Path(__file__).resolve().parents[3] / "content" / "personas"

# Content action name -> wire ActionType (content never sees ActionType;
# limp is a first-class name in packs, translated to CALL on the wire).
_WIRE: dict[str, ActionType] = {
    "fold": ActionType.FOLD,
    "limp": ActionType.CALL,
    "call": ActionType.CALL,
    "raise": ActionType.RAISE,
    "3bet": ActionType.RAISE,
    "4bet": ActionType.RAISE,
    "5bet_shove": ActionType.RAISE,
}

class PersonaAction(NamedTuple):
    name: str  # the content-level action ("limp", "3bet", ...)
    action: ActionType  # wire translation


def load_persona_packs(content_dir: Path | None = None) -> dict[VillainType, PersonaPack]:
    """Load + validate all persona packs; raises on duplicate persona.

    Duplicate (facing, position) node coverage within a pack raises at model
    validation (PersonaPack._node_ordering) — no silent last-wins.
    """
    d = content_dir or PERSONA_DIR
    packs: dict[VillainType, PersonaPack] = {}
    for path in sorted(d.glob("*.json")):
        pack = PersonaPack.model_validate_json(path.read_text())
        if pack.persona in packs:
            raise ValueError(f"duplicate persona pack: {pack.persona} ({path.name})")
        packs[pack.persona] = pack
    return packs


@cache
def _combos(spec: str) -> frozenset[str]:
    return frozenset(parse_range(spec))


def sample_preflop_action(
    pack: PersonaPack,
    position: Position,
    facing: str,
    hole_cards: tuple[Card, Card],
    rng: random.Random,
    is_opener: bool | None = None,
) -> PersonaAction:
    """Draw a frequency-mixed preflop action for (position, facing, hand class).

    Node lookup (pinned): scan `pack.preflop` in LIST ORDER; the first node
    whose facing matches AND whose positions is None (wildcard) or contains
    `position` wins. Within the node, first mix containing the hand class
    wins; weight remainder is an implicit fold; no matching node/mix => fold.

    N-3BSTRATA — role matching (third filter, same first-match-wins scan):
    `is_opener` is the caller's ARRIVAL STRATUM for this decision — True when
    this seat made the FIRST preflop raise of the hand (it opened and is now
    acting again), False when it did not, None when the caller does not track
    it. An UNTAGGED node (`role is None`) matches every stratum including
    None, so a pack with no `role` anywhere behaves EXACTLY as before for
    every caller — the default-off contract. A role-TAGGED node matches only
    when the caller passes the matching stratum; a caller that passes None
    never selects one. ⚠️ That fallback is fail-SAFE, not fail-loud (triple-
    review convergent finding): a role-unaware caller reading a stratified
    pack at a fully-tagged facing degrades to the implicit-fold path (an
    all-fold table) — conservative and detectable, but silent. Both
    production callers (play.bot_decision, range_estimate) always pass a real
    boolean; any NEW caller must too.
    """
    hand = hole_cards_to_class(*hole_cards)
    want_role = None if is_opener is None else ("opener" if is_opener else "cold")
    for node in pack.preflop:
        if node.facing != facing:
            continue
        if node.positions is not None and position not in node.positions:
            continue
        if node.role is not None and node.role != want_role:
            continue
        for mix in node.mixes:
            if hand not in _combos(mix.combos):
                continue
            weights = dict(mix.weights)
            remainder = 1.0 - sum(weights.values())
            if remainder > 1e-9:
                weights["fold"] = weights.get("fold", 0.0) + remainder
            name = rng.choices(list(weights), weights=list(weights.values()), k=1)[0]
            return PersonaAction(name, _WIRE[name])
        break  # node matched but no mix covers this hand class => fold 1.0
    return PersonaAction("fold", ActionType.FOLD)
