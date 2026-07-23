import pytest
from pydantic import ValidationError

from app.domain.archetypes import VillainType
from app.domain.content import (
    ContentPack,
    all_hands,
    hole_cards_to_class,
    load_pack,
    parse_range,
)
from app.domain.content.models import PersonaPack
from app.domain.personas import load_persona_packs


def test_all_hands_count():
    assert len(all_hands()) == 169  # 13 pairs + 78 suited + 78 offsuit


def test_pair_plus():
    assert parse_range("77+") == {"77", "88", "99", "TT", "JJ", "QQ", "KK", "AA"}


def test_pair_range():
    assert parse_range("QQ-99") == {"99", "TT", "JJ", "QQ"}


def test_suited_plus():
    assert parse_range("ATs+") == {"ATs", "AJs", "AQs", "AKs"}


def test_offsuit_plus_non_ace():
    assert parse_range("KTo+") == {"KTo", "KJo", "KQo"}


def test_both_suits_when_unspecified():
    assert parse_range("AK") == {"AKs", "AKo"}


def test_single_hands_and_union():
    assert parse_range("AKo") == {"AKo"}
    assert parse_range("77+, ATs+, KQs") == (
        {"77", "88", "99", "TT", "JJ", "QQ", "KK", "AA"} | {"ATs", "AJs", "AQs", "AKs"} | {"KQs"}
    )


def test_star_is_everything():
    assert parse_range("*") == all_hands()


def test_bad_token_raises():
    with pytest.raises(ValueError):
        parse_range("XYZ")


@pytest.mark.parametrize(
    "c1,c2,expected",
    [
        ("Ah", "Ks", "AKo"),
        ("Ah", "Kh", "AKs"),
        ("Kd", "Ac", "AKo"),  # order-independent
        ("7c", "7d", "77"),
    ],
)
def test_hole_cards_to_class(c1, c2, expected):
    assert hole_cards_to_class(c1, c2) == expected


def test_contentpack_loads_and_validates():
    pack = load_pack(
        {
            "id": "preflop-rfi-test",
            "version": 1,
            "domain": "preflop",
            "entries": [
                {
                    "node_context": "RFI",
                    "position": "CO",
                    "actions": [
                        {"action": "raise", "combos": "77+, ATs+, KQs", "frequency": 1.0},
                    ],
                    "sizing_bb": 2.5,
                }
            ],
        }
    )
    assert isinstance(pack, ContentPack)
    assert pack.entries[0].actions[0].action.value == "raise"


def test_contentpack_rejects_bad_frequency():
    with pytest.raises(ValidationError):
        load_pack(
            {
                "id": "x",
                "version": 1,
                "domain": "preflop",
                "entries": [
                    {
                        "node_context": "RFI",
                        "position": "CO",
                        "actions": [{"action": "raise", "combos": "AA", "frequency": 2.0}],
                    }
                ],
            }
        )


def _assert_no_fully_shadowed_mix(pack) -> None:
    """Within every preflop node of `pack`, assert no mix is FULLY SHADOWED
    by earlier mixes in that node — i.e. every one of its expanded combos is
    already claimed by an earlier mix, so it could never fire under
    first-match-wins (personas.sample_preflop_action). Partial overlap is the
    legitimate specifics-then-catch-all idiom and is allowed."""
    for node in pack.preflop:
        expanded = [(mix.combos, parse_range(mix.combos)) for mix in node.mixes]
        claimed: set[str] = set()
        for i, (combos_i, set_i) in enumerate(expanded):
            fully_shadowed = i > 0 and bool(set_i) and set_i <= claimed
            assert not fully_shadowed, (
                f"fully shadowed mix in pack={pack.id!r} facing={node.facing!r} "
                f"positions={node.positions!r}: mix[{i}]={combos_i!r} is entirely "
                f"covered by earlier mixes and can never fire"
            )
            claimed |= set_i


def test_no_fully_shadowed_mix_within_node():
    # Positive case: every shipped persona pack's preflop nodes must have no
    # mix that is fully shadowed by earlier mixes (N2 — first-match-wins
    # means a fully-shadowed mix can never fire, which is always a bug).
    # Partial overlap — a specific mix followed by a wider catch-all that
    # re-covers some of the same combos — is the legitimate idiom and must
    # NOT be flagged.
    packs = load_persona_packs()
    assert packs, "expected at least one persona pack to be loaded"
    for pack in packs.values():
        _assert_no_fully_shadowed_mix(pack)

    # Negative case: a synthetic pack with a genuinely dead mix (mix1's `AA`
    # is entirely covered by mix0's `*`) must be rejected by the same check.
    shadowed_pack = PersonaPack.model_validate(
        {
            "id": "persona_test_shadowed",
            "version": "1.0.0",
            "domain": "persona",
            "persona": "tag",
            "display_name": "Shadowed Test",
            "sizing": {"open_bb": 2.5, "threebet_mult": 3.0, "fourbet_mult": 2.2},
            "preflop": [
                {
                    "facing": "unopened",
                    "positions": ["BTN"],
                    "mixes": [
                        {"combos": "*", "weights": {"raise": 1.0}},
                        {"combos": "AA", "weights": {"raise": 0.5, "fold": 0.5}},
                    ],
                }
            ],
        }
    )
    with pytest.raises(AssertionError):
        _assert_no_fully_shadowed_mix(shadowed_pack)


def test_maniac_vs4bet_jams_lighter_than_lag():
    # N3 behavioral guard: maniac's vs_4bet jam range must be a lighter,
    # trappier shove than LAG's — not merely a combo superset. Locks in
    # the T2 (N3) rebuild: maniac shoves combos LAG never shoves, and traps
    # premiums (AA/KK) with a partial call leg instead of jamming 100%.
    packs = load_persona_packs()
    maniac = packs[VillainType.MANIAC]
    lag = packs[VillainType.LAG]

    def vs_4bet_node(pack):
        for node in pack.preflop:
            if node.facing == "vs_4bet":
                return node
        raise AssertionError(f"no vs_4bet node in pack {pack.id!r}")

    def shove_combos(node) -> set[str]:
        combos: set[str] = set()
        for mix in node.mixes:
            weight = mix.weights.get("5bet_shove", 0.0)
            if weight > 0.0:
                combos |= parse_range(mix.combos)
        return combos

    def call_weight(node, hand: str) -> float:
        for mix in node.mixes:
            if hand in parse_range(mix.combos):
                return mix.weights.get("call", 0.0)
        return 0.0

    maniac_node = vs_4bet_node(maniac)
    lag_node = vs_4bet_node(lag)

    maniac_shoves = shove_combos(maniac_node)
    lag_shoves = shove_combos(lag_node)

    lighter_bluffs = maniac_shoves - lag_shoves
    assert len(lighter_bluffs) >= 3, (
        f"expected >=3 maniac 5bet_shove combos with zero LAG shove weight, "
        f"got {sorted(lighter_bluffs)}"
    )

    aa_call = call_weight(maniac_node, "AA")
    kk_call = call_weight(maniac_node, "KK")
    assert aa_call > 0.0 or kk_call > 0.0, (
        f"expected maniac vs_4bet to trap-flat AA and/or KK with nonzero call "
        f"weight, got AA={aa_call} KK={kk_call}"
    )
