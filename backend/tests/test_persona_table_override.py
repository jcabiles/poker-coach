"""PersonaTableOverride model tests (M1b T2) + its schema sync test.

Nothing here loads or merges an override file into a pack yet — that is T3
(`app.domain.personas.load_persona_packs`).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.domain.archetypes import VillainType
from app.domain.content.persona_override import PersonaTableOverride


def _override(**overrides) -> dict:
    base = {
        "id": "override_lag_6max",
        "version": "1",
        "domain": "persona_override",
        "persona": "lag",
        "table_size": 6,
    }
    return {**base, **overrides}


def test_a_valid_override_validates_and_exposes_doc():
    override = PersonaTableOverride.model_validate(
        _override(
            _doc=["reason: seat count changes the LAG's open range"],
            preflop={
                "unopened": [
                    {
                        "facing": "unopened",
                        "mixes": [{"combos": "AA", "weights": {"raise": 1.0}}],
                    }
                ]
            },
            sizing={"open_bb": 2.5},
            postflop={"aggression": 1.2, "stickiness": None},
        )
    )
    assert override.doc == ["reason: seat count changes the LAG's open range"]
    assert override.persona == VillainType.LAG
    assert override.sizing == {"open_bb": 2.5}
    assert override.postflop == {"aggression": 1.2, "stickiness": None}


def test_unknown_top_level_key_rejected():
    with pytest.raises(ValidationError, match="extra"):
        PersonaTableOverride.model_validate(_override(sizing={"open_bb": 2.5}, bogus="x"))


def test_unknown_sizing_key_rejected():
    with pytest.raises(ValidationError, match="unknown keys"):
        PersonaTableOverride.model_validate(_override(sizing={"open_bxb": 2.5}))


def test_unknown_postflop_key_rejected():
    with pytest.raises(ValidationError, match="unknown keys"):
        PersonaTableOverride.model_validate(_override(postflop={"aggresion": 1.2}))


def test_facing_mismatch_rejected():
    with pytest.raises(ValidationError, match="facing"):
        PersonaTableOverride.model_validate(
            _override(
                preflop={
                    "unopened": [
                        {
                            "facing": "vs_rfi",
                            "mixes": [{"combos": "AA", "weights": {"call": 1.0}}],
                        }
                    ]
                }
            )
        )


def test_empty_facing_list_rejected():
    with pytest.raises(ValidationError, match="no nodes"):
        PersonaTableOverride.model_validate(_override(preflop={"unopened": []}))


def test_empty_override_rejected():
    with pytest.raises(ValidationError, match="changes nothing"):
        PersonaTableOverride.model_validate(_override())


def test_table_size_9_rejected():
    with pytest.raises(ValidationError):
        PersonaTableOverride.model_validate(_override(table_size=9, sizing={"open_bb": 2.5}))


def test_checked_in_persona_override_schema_matches_the_model():
    """Nothing in the app reads `persona_override.schema.json`, so drift is
    otherwise silent — same reason as `persona.schema.json`'s sync test
    (`test_preflop_size_mix.py::test_checked_in_persona_schema_matches_the_model`)."""
    committed = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "content"
            / "schema"
            / "persona_override.schema.json"
        ).read_text()
    )
    assert committed == PersonaTableOverride.model_json_schema(), (
        "content/schema/persona_override.schema.json is stale — regenerate it "
        "from PersonaTableOverride.model_json_schema()"
    )
