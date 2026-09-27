"""6-max bot-settings override files: the PersonaTableOverride model, its
schema sync test, and how `load_persona_packs` merges override files over the
base packs at table size 6 (and ignores them at 9).
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest
from persona_override_fixture import (
    DEFAULT_LAG_OVERRIDE,
    OVERRIDE_AGGRESSION,
    write_fixture_content,
)
from pydantic import ValidationError

from app.domain.archetypes import VillainType
from app.domain.content.notation import all_hands
from app.domain.content.persona_override import PersonaTableOverride
from app.domain.personas import load_persona_packs, sample_preflop_action
from app.domain.spot import Position
from tools import export_analytics as ea


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


# --- loading and merging -----------------------------------------------------


def _cards_for(hand_class: str) -> tuple[str, str]:
    """One concrete pair of hole cards for a hand class like "AA", "AKs", "AKo"."""
    hi, lo = hand_class[0], hand_class[1]
    if hi == lo:
        return (hi + "s", lo + "h")
    return (hi + "s", lo + ("s" if hand_class.endswith("s") else "h"))


def _unopened_actions_from_lj(pack) -> dict[str, str]:
    rng = random.Random(7)
    return {
        hand: sample_preflop_action(
            pack, Position.LJ, "unopened", _cards_for(hand), rng, is_opener=False
        ).name
        for hand in sorted(all_hands())
    }


def test_at_six_the_override_replaces_the_lag_unopened_range_and_postflop_dial(tmp_path):
    lag = load_persona_packs(write_fixture_content(tmp_path), table_size=6)["lag"]
    actions = _unopened_actions_from_lj(lag)
    assert len(actions) == 169
    assert actions.pop("AA") == "raise"
    assert set(actions.values()) == {"fold"}
    assert lag.postflop is not None
    assert lag.postflop.aggression == OVERRIDE_AGGRESSION


def test_at_six_the_merged_pack_keeps_the_base_id_version_and_other_facings(tmp_path):
    base = load_persona_packs()["lag"]
    lag = load_persona_packs(write_fixture_content(tmp_path), table_size=6)["lag"]
    assert (lag.id, lag.version) == (base.id, base.version)
    assert [n for n in lag.preflop if n.facing != "unopened"] == [
        n for n in base.preflop if n.facing != "unopened"
    ]
    assert lag.sizing == base.sizing


def test_at_six_personas_without_an_override_equal_their_base(tmp_path):
    base = load_persona_packs()
    merged = load_persona_packs(write_fixture_content(tmp_path), table_size=6)
    assert set(merged) == set(base)
    for persona, pack in base.items():
        if persona != VillainType.LAG:
            assert merged[persona] == pack


def test_at_nine_the_override_folder_is_ignored(tmp_path):
    lag = load_persona_packs(write_fixture_content(tmp_path), table_size=9)["lag"]
    assert lag == load_persona_packs()["lag"]
    raised = [h for h, a in _unopened_actions_from_lj(lag).items() if a == "raise"]
    assert len(raised) > 20, raised


def test_played_six_max_hands_obey_the_override_from_lj(tmp_path):
    packs = load_persona_packs(write_fixture_content(tmp_path), table_size=6)
    lag_seat = 2
    # At 6 seats the rotation from the button is BTN, SB, BB, LJ, HJ, CO, so
    # seat 2 is LJ (first to act preflop, so its pot is always unopened) when
    # the button is at seat 5.
    button = 5
    lineup = ["tag", "nit", "lag", "tag", "calling_station", "tag"]
    persona_by_seat = dict(enumerate(lineup))
    # 321 and 532 are hand seeds where seat 2 is dealt AA at 6 seats; they
    # make the raise branch occur, which range(40) alone never reaches.
    hand_seeds = [*range(40), 321, 532]
    aa_hands = 0
    for hand_seed in hand_seeds:
        res = ea.play_one_hand(
            random.Random(1000 + hand_seed),
            hand_seed,
            button,
            persona_by_seat,
            packs,
            stacks_bb=[100.0] * 6,
        )
        seat_row = next(r for r in res["seats"] if r["seat"] == lag_seat)
        assert seat_row["position"] == "LJ"
        first = next(r for r in res["decisions"] if r["seat"] == lag_seat and r["action"] != "post")
        assert first["street"] == "preflop"
        assert first["position"] == "LJ"
        holds_aa = seat_row["hole_cards"][0] == "A" and seat_row["hole_cards"][3] == "A"
        if holds_aa:
            aa_hands += 1
            assert first["action"] == "raise", (hand_seed, first)
        else:
            assert first["action"] == "fold", (hand_seed, seat_row["hole_cards"], first)
    assert aa_hands == 2


def _lag_override(**fields) -> dict:
    body = {k: v for k, v in DEFAULT_LAG_OVERRIDE.items() if k not in ("preflop", "postflop")}
    return {**body, **fields}


def test_a_null_dial_deletes_it_from_the_merged_pack(tmp_path):
    folder = write_fixture_content(
        tmp_path, {"lag": _lag_override(postflop={"size_elasticity": 1.0, "stickiness": None})}
    )
    lag = load_persona_packs(folder, table_size=6)["lag"]
    assert lag.postflop is not None
    assert "stickiness" not in lag.postflop.model_fields_set
    assert "size_elasticity" in lag.postflop.model_fields_set
    assert load_persona_packs()["lag"].postflop.stickiness is not None


def test_deleting_a_required_dial_fails_naming_the_file(tmp_path):
    folder = write_fixture_content(tmp_path, {"lag": _lag_override(postflop={"aggression": None})})
    with pytest.raises(ValueError, match=r"six_max/lag\.json"):
        load_persona_packs(folder, table_size=6)


def test_an_invalid_override_file_fails_naming_the_file(tmp_path):
    folder = write_fixture_content(tmp_path, {"lag": _lag_override(sizing={"open_bxb": 2.5})})
    with pytest.raises(ValueError, match=r"six_max/lag\.json") as exc:
        load_persona_packs(folder, table_size=6)
    assert isinstance(exc.value.__cause__, ValidationError)


def test_two_overrides_for_one_persona_fail_naming_the_file(tmp_path):
    folder = write_fixture_content(
        tmp_path, {"lag": DEFAULT_LAG_OVERRIDE, "lag_again": DEFAULT_LAG_OVERRIDE}
    )
    with pytest.raises(ValueError, match=r"duplicate override.*six_max/lag_again\.json"):
        load_persona_packs(folder, table_size=6)


def test_an_override_for_a_persona_with_no_pack_fails_naming_the_file(tmp_path):
    folder = write_fixture_content(tmp_path)
    (folder / "lag.json").unlink()
    with pytest.raises(ValueError, match=r"six_max/lag\.json.*no pack"):
        load_persona_packs(folder, table_size=6)


def test_postflop_keys_against_a_pack_without_postflop_fail_naming_the_file(tmp_path):
    folder = write_fixture_content(tmp_path)
    base = json.loads((folder / "lag.json").read_text())
    del base["postflop"]
    (folder / "lag.json").write_text(json.dumps(base))
    with pytest.raises(ValueError, match=r"six_max/lag\.json.*no postflop"):
        load_persona_packs(folder, table_size=6)


def test_a_merged_pack_that_fails_validation_fails_naming_the_file(tmp_path):
    # Adding size_elasticity to the LAG without deleting stickiness is
    # rejected by PersonaPostflop's split-lever validator.
    folder = write_fixture_content(
        tmp_path, {"lag": _lag_override(postflop={"size_elasticity": 1.0})}
    )
    with pytest.raises(ValueError, match=r"six_max/lag\.json.*invalid lag pack") as exc:
        load_persona_packs(folder, table_size=6)
    assert isinstance(exc.value.__cause__, ValidationError)


def test_a_missing_override_folder_means_no_overrides(tmp_path):
    folder = write_fixture_content(tmp_path, {})
    (folder / "six_max").rmdir()
    assert load_persona_packs(folder, table_size=6) == load_persona_packs()


@pytest.mark.parametrize("table_size", [7, 0])
def test_a_table_size_other_than_six_or_nine_is_rejected(table_size):
    with pytest.raises(ValueError, match="table_size"):
        load_persona_packs(table_size=table_size)  # type: ignore[arg-type]


def test_a_non_utf8_override_file_fails_naming_the_file(tmp_path):
    folder = write_fixture_content(tmp_path)
    (folder / "six_max" / "lag.json").write_bytes(b"\xff\xfe garbage")
    with pytest.raises(ValueError, match=r"six_max/lag\.json"):
        load_persona_packs(folder, table_size=6)


def test_at_nine_an_invalid_override_file_is_never_read(tmp_path):
    folder = write_fixture_content(tmp_path)
    (folder / "six_max" / "bad.json").write_text("{ not json")
    first = load_persona_packs(folder, table_size=9)
    assert first == load_persona_packs(folder, table_size=9)
    assert first == load_persona_packs()
    with pytest.raises(ValueError, match=r"six_max/bad\.json"):
        load_persona_packs(folder, table_size=6)


def test_an_override_merges_onto_a_pack_whose_full_dump_would_not_validate(tmp_path):
    # calling_station authors size_elasticity without stickiness; a dump
    # without exclude_unset would re-add stickiness's default, which the
    # split-lever validator rejects.
    base = load_persona_packs()["calling_station"]
    assert base.postflop is not None
    new_aggression = base.postflop.aggression + 0.25
    override = {
        **_lag_override(postflop={"aggression": new_aggression}),
        "id": "override_calling_station_6max",
        "persona": "calling_station",
    }
    folder = write_fixture_content(tmp_path, {"calling_station": override})
    merged = load_persona_packs(folder, table_size=6)["calling_station"]
    assert merged.postflop is not None
    assert merged.postflop.aggression == new_aggression
