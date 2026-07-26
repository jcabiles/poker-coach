"""W3R-1 — maniac (+ lag) preflop range cleanup (CONFIG-ONLY) assertions.

Spec: `docs/ai-dlc/specs/persona-realism-w3r-1.md` (T1–T3). Pure content edits:
- maniac `vs_rfi` REPLACED with a 3-tier legit loose-flat range (no any-two
  cold-call); maniac + lag SB open-limps DELETED; maniac HJ/CO/BTN offsuit-ace
  opens trimmed (HJ→A7o+, CO/BTN→A5o+).

These tests pin the CONFIG behavior directly via `sample_preflop_action`; the
seeded-sim stat bands (T4) live in `test_personas.py` / `test_personas_postflop.py`.
"""

import random

import pytest

from app.domain.archetypes import VillainType
from app.domain.personas import load_persona_packs, sample_preflop_action
from app.domain.spot import Position

N = 400  # large enough to reliably observe any >0-frequency action


def _cards(hand: str) -> tuple[str, str]:
    """Hand-class token -> a concrete distinct-card pair.

    '55' -> ('5c','5d'); '87s' -> ('8h','7h'); 'A5o' -> ('Ah','5s').
    (`hole_cards_to_class` normalizes rank order, so order here is irrelevant.)
    """
    if len(hand) == 2:  # pair
        r = hand[0]
        return (r + "c", r + "d")
    r1, r2, suit = hand[0], hand[1], hand[2]
    return (r1 + "h", r2 + "h") if suit == "s" else (r1 + "h", r2 + "s")


def _actions(pack, position: Position, facing: str, hand: str, seed: int = 20260724) -> set[str]:
    rng = random.Random(seed)
    hole = _cards(hand)
    return {sample_preflop_action(pack, position, facing, hole, rng).name for _ in range(N)}


@pytest.fixture(scope="module")
def packs():
    loaded = load_persona_packs()
    if VillainType("maniac") not in loaded or VillainType("lag") not in loaded:
        pytest.skip("maniac/lag persona packs not authored yet")
    return loaded


def _find_node(pack, facing: str, position: Position):
    """Mirror the engine's node lookup: first node whose facing matches and
    whose positions is None (wildcard) or contains `position`."""
    for node in pack.preflop:
        if node.facing != facing:
            continue
        if node.positions is not None and position not in node.positions:
            continue
        return node
    return None


def _mix_shape(node) -> list[tuple[str, dict]]:
    return [(m.combos, dict(m.weights)) for m in node.mixes]


# --------------------------------------------------------------- T1 (maniac)


@pytest.mark.parametrize("hand", ["J2o", "72o", "92o", "Q4o", "K5o"])
def test_maniac_vs_rfi_offsuit_trash_folds_never_calls(packs, hand):
    # No mix matches offsuit trash -> engine default fold (never a cold-call).
    acts = _actions(packs[VillainType("maniac")], Position.CO, "vs_rfi", hand)
    assert acts == {"fold"}, f"{hand} vs_rfi actions {acts}"


@pytest.mark.parametrize("hand", ["55", "87s", "KQs"])
def test_maniac_vs_rfi_tier2_flats_and_3bets(packs, hand):
    # tier-2 {3bet:0.45, call:0.55}: both actions observed, never a lone fold.
    acts = _actions(packs[VillainType("maniac")], Position.CO, "vs_rfi", hand)
    assert "call" in acts and "3bet" in acts, f"{hand} vs_rfi actions {acts}"


@pytest.mark.parametrize("hand", ["K5s", "A5o", "T9o"])
def test_maniac_vs_rfi_tier3_flats(packs, hand):
    # tier-3 {call:0.9, fold:0.1}: flats (call) in >0 of N draws.
    acts = _actions(packs[VillainType("maniac")], Position.CO, "vs_rfi", hand)
    assert "call" in acts, f"{hand} vs_rfi actions {acts}"


@pytest.mark.parametrize("hand", ["AKo", "QQ"])
def test_maniac_vs_rfi_premiums_3bet(packs, hand):
    # tier-1 {3bet:1.0}: always 3bet.
    acts = _actions(packs[VillainType("maniac")], Position.CO, "vs_rfi", hand)
    assert acts == {"3bet"}, f"{hand} vs_rfi actions {acts}"


@pytest.mark.parametrize("hand", ["J2s", "32s", "K2o"])
def test_maniac_sb_no_open_limp(packs, hand):
    # SB open-limp mix deleted -> these fall through to fold (never limp).
    acts = _actions(packs[VillainType("maniac")], Position.SB, "unopened", hand)
    assert "limp" not in acts and acts == {"fold"}, f"{hand} SB actions {acts}"


# --------------------------------------------------------------- T2 (maniac aces)


def test_maniac_hj_ace_trim(packs):
    pack = packs[VillainType("maniac")]
    assert _actions(pack, Position.HJ, "unopened", "A6o") == {"fold"}
    assert "raise" in _actions(pack, Position.HJ, "unopened", "A7o")


@pytest.mark.parametrize("position", [Position.CO, Position.BTN])
def test_maniac_co_btn_ace_trim(packs, position):
    pack = packs[VillainType("maniac")]
    assert _actions(pack, position, "unopened", "A4o") == {"fold"}
    assert "raise" in _actions(pack, position, "unopened", "A5o")


@pytest.mark.parametrize("position", [Position.HJ, Position.CO, Position.BTN])
def test_maniac_suited_ace_control_still_opens(packs, position):
    # A2s (suited) still opens from every trimmed position — trim is offsuit-only.
    assert "raise" in _actions(packs[VillainType("maniac")], position, "unopened", "A2s")


# Byte-identical EP/BB opening ranges (untouched by the offsuit-ace trims).
_MANIAC_UNTOUCHED_OPENS = {
    Position.UTG: [
        ("55+, A6s+, K9s+, QTs+, J9s+, T9s, A9o+, KJo+", {"raise": 0.85, "fold": 0.15}),
        ("33, 44, A4s, A5s, K8s, QTo", {"raise": 0.85, "fold": 0.15}),
    ],
    Position.UTG1: [
        ("44+, A4s+, K7s+, Q9s+, J8s+, T8s+, 98s, A8o+, KTo+, QJo", {"raise": 0.85, "fold": 0.15}),
        ("22, 33, A2s, A3s, K6s, JTo", {"raise": 0.85, "fold": 0.15}),
    ],
    Position.UTG2: [
        ("33+, A2s+, K5s+, Q8s+, J7s+, T7s+, 97s+, 87s, A6o+, K9o+, QTo+, JTo",
         {"raise": 0.8, "fold": 0.2}),
        ("22, K4s, Q7s, J6s, 76s, A5o", {"raise": 0.85, "fold": 0.15}),
    ],
    Position.LJ: [
        ("22+, A2s+, K3s+, Q6s+, J6s+, T6s+, 86s+, 75s+, 64s+, A4o+, K7o+, Q9o+, J9o+, T9o",
         {"raise": 0.8, "fold": 0.2}),
        ("K2s, Q5s, J5s, 54s, A3o, K6o, Q8o", {"raise": 0.85, "fold": 0.15}),
    ],
    Position.BB: [
        ("33+, A3s+, K6s+, Q9s+, J8s+, T8s+, 98s, A7o+, K9o+, QTo+, JTo",
         {"raise": 0.8, "fold": 0.2}),
        ("22, A2s, K5s, Q8s, J7s, 87s, A6o, K8o", {"raise": 0.85, "fold": 0.15}),
    ],
}


@pytest.mark.parametrize("position", list(_MANIAC_UNTOUCHED_OPENS))
def test_maniac_untouched_opens_byte_identical(packs, position):
    node = _find_node(packs[VillainType("maniac")], "unopened", position)
    assert node is not None and _mix_shape(node) == _MANIAC_UNTOUCHED_OPENS[position]


# --------------------------------------------------------------- T3 (lag SB)


# T3's invariant is "lag never OPEN-LIMPS from the SB" — it is a check on the
# ACTION SET, not on range width. W5-b1 (2026-07-25) widened the lag SB
# `unopened` node from ~22% to 51.98% authored, so two of these three probes are
# now inside the range; the pins are updated to the new ranges rather than the
# ranges being carved to keep the pins (which would corrupt the persona to
# protect a test). `"limp" not in acts` — the actual T3 guarantee — is asserted
# for all three and is unchanged.
#   54s -> mix 2 (raise 0.4 / fold 0.6)      32s -> outside the node
#   J9o -> mix 1 via `J8o+` (raise 1.0)
@pytest.mark.parametrize(
    ("hand", "expected"),
    [("54s", {"raise", "fold"}), ("32s", {"fold"}), ("J9o", {"raise"})],
)
def test_lag_sb_no_open_limp(packs, hand, expected):
    acts = _actions(packs[VillainType("lag")], Position.SB, "unopened", hand)
    assert "limp" not in acts, f"{hand} lag SB open-limped: {acts}"
    assert acts == expected, f"{hand} lag SB actions {acts}"


_LAG_VS_RFI = [
    ("JJ+, AQs+, AKo", {"3bet": 1.0}),
    ("TT, 99, 88, AJs, ATs, A9s, A8s, A7s, A6s, A5s, A4s, A3s, KQs, KJs, KTs, QJs, JTs, "
     "AJo, ATo, KQo, KJo", {"3bet": 0.6, "fold": 0.4}),
    ("77, 66, 55, 44, 33, 22, K9s, K8s, Q9s, Q8s, J9s, J8s, T9s, T8s, 98s, 87s, 76s, 65s, "
     "54s, QJo, JTo, T9o, 98o", {"call": 1.0}),
    ("A9o, A8o, A7o, A6o, K7s, Q7s, J7s, T7s, 43s, KTo, QTo, J9o, T8o, 87o",
     {"call": 0.65, "fold": 0.35}),
]


def test_lag_vs_rfi_byte_identical(packs):
    node = _find_node(packs[VillainType("lag")], "vs_rfi", Position.CO)
    assert node is not None and _mix_shape(node) == _LAG_VS_RFI
