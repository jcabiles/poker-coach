"""PersonaTableOverride — the format of a 6-max-only bot-settings override file."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.archetypes import VillainType
from app.domain.content.models import PersonaFacing, PersonaNode, PersonaPostflop, PersonaSizing


class PersonaTableOverride(BaseModel):
    """One override file: the values a persona's settings carry at 6-max that
    differ from its base pack (M1b). Nothing in this repo loads or merges
    these files yet — see `app.domain.personas.load_persona_packs`."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    version: str
    domain: Literal["persona_override"]
    persona: VillainType
    table_size: Literal[6]
    doc: list[str] = Field(default_factory=list, alias="_doc")
    preflop: dict[PersonaFacing, list[PersonaNode]] = Field(default_factory=dict)
    sizing: dict[str, Any] = Field(
        default_factory=dict,
        description="Per-key overrides of PersonaSizing fields; a value of null "
        "deletes that key from the base settings when merged.",
    )
    postflop: dict[str, Any] = Field(
        default_factory=dict,
        description="Per-key overrides of PersonaPostflop fields; a value of null "
        "deletes that key from the base settings when merged.",
    )

    @model_validator(mode="after")
    def _sizing_keys_known(self) -> PersonaTableOverride:
        unknown = sorted(set(self.sizing) - set(PersonaSizing.model_fields))
        if unknown:
            raise ValueError(f"sizing has unknown keys {unknown}")
        return self

    @model_validator(mode="after")
    def _postflop_keys_known(self) -> PersonaTableOverride:
        unknown = sorted(set(self.postflop) - set(PersonaPostflop.model_fields))
        if unknown:
            raise ValueError(f"postflop has unknown keys {unknown}")
        return self

    @model_validator(mode="after")
    def _preflop_facings_consistent(self) -> PersonaTableOverride:
        for facing, nodes in self.preflop.items():
            if not nodes:
                raise ValueError(f"preflop facing {facing!r} has no nodes")
            mismatched = [node.facing for node in nodes if node.facing != facing]
            if mismatched:
                raise ValueError(
                    f"preflop facing {facing!r} lists a node with facing {mismatched[0]!r}"
                )
        return self

    @model_validator(mode="after")
    def _not_empty(self) -> PersonaTableOverride:
        if not self.preflop and not self.sizing and not self.postflop:
            raise ValueError("override changes nothing (preflop, sizing, postflop all empty)")
        return self
