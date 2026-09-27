"""Persona preflop engine — samples frequency-mixed bot actions from persona packs.

Pure domain: strategy lives in `content/personas/*.json` (PersonaPack); this
engine is generic. The rng is injected per call (per-hand instance, never
module-level) — same convention as `table/deck.py` and `challenge.py`.
"""

from __future__ import annotations

import random
from functools import cache
from pathlib import Path
from typing import Any, NamedTuple

from pydantic import ValidationError

from app.domain.archetypes import VillainType
from app.domain.content.models import PersonaPack
from app.domain.content.notation import hole_cards_to_class, parse_range
from app.domain.content.persona_override import PersonaTableOverride
from app.domain.spot import ActionType, Card, Position
from app.domain.table.deck import TableSize

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


def load_persona_packs(
    content_dir: Path | None = None, table_size: TableSize = 9
) -> dict[VillainType, PersonaPack]:
    """Load + validate all persona packs; raises on duplicate persona.

    Duplicate (facing, position) node coverage within a pack raises at model
    validation (PersonaPack._node_ordering) — no silent last-wins.

    `table_size=6` additionally merges each `six_max/*.json` override file
    (PersonaTableOverride) over its persona's base pack; at 9 that directory
    is never read. Every override problem raises naming the file.
    """
    if table_size not in (6, 9):
        raise ValueError(f"table_size must be 6 or 9, got {table_size!r}")
    d = content_dir or PERSONA_DIR
    packs: dict[VillainType, PersonaPack] = {}
    for path in sorted(d.glob("*.json")):
        pack = PersonaPack.model_validate_json(path.read_text())
        if pack.persona in packs:
            raise ValueError(f"duplicate persona pack: {pack.persona} ({path.name})")
        packs[pack.persona] = pack
    if table_size == 6:
        override_dir = d / "six_max"
        merged_from: dict[VillainType, str] = {}
        for path in sorted(override_dir.glob("*.json")):
            where = f"six_max/{path.name}"
            try:
                override = PersonaTableOverride.model_validate_json(path.read_bytes())
            except ValidationError as e:
                raise ValueError(f"invalid override file {where}: {e}") from e
            if override.persona in merged_from:
                raise ValueError(
                    f"duplicate override for {override.persona}: {where} "
                    f"(also six_max/{merged_from[override.persona]})"
                )
            if override.persona not in packs:
                raise ValueError(f"override {where} names {override.persona}, which has no pack")
            merged_from[override.persona] = path.name
            packs[override.persona] = _apply_override(packs[override.persona], override, where)
    return packs


def _apply_override(pack: PersonaPack, override: PersonaTableOverride, where: str) -> PersonaPack:
    """Merge one override over its base pack: a listed facing replaces every
    base node of that facing; sizing/postflop merge key by key, `None`
    deleting the key. The rebuild re-runs every PersonaPack validator."""
    if override.postflop and pack.postflop is None:
        raise ValueError(f"override {where} sets postflop keys but {pack.persona} has no postflop")
    data = pack.model_dump(mode="json", exclude_unset=True)
    for facing, nodes in override.preflop.items():
        data["preflop"] = [n for n in data["preflop"] if n["facing"] != facing] + [
            n.model_dump(mode="json", exclude_unset=True) for n in nodes
        ]
    for section in ("sizing", "postflop"):
        values: dict[str, Any] = getattr(override, section)
        for key, value in values.items():
            if value is None:
                data[section].pop(key, None)
            else:
                data[section][key] = value
    try:
        return PersonaPack.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"override {where} makes an invalid {pack.persona} pack: {e}") from e


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
