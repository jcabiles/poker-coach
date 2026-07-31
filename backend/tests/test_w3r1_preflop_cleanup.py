"""W3R-1 — maniac (+ lag) preflop range cleanup (CONFIG-ONLY) assertions.

Spec: `docs/ai-dlc/specs/persona-realism-w3r-1.md` (T1–T3). Pure content edits:
- maniac `vs_rfi` REPLACED with a 3-tier legit loose-flat range (no any-two
  cold-call); maniac + lag SB open-limps DELETED; maniac HJ/CO/BTN offsuit-ace
  opens trimmed (HJ→A7o+, CO/BTN→A5o+).
  ⚠️ The ace TRIMS were SUPERSEDED by R10-PRE2 (2026-07-30): the maniac ladder
  now opens A2o+ from HJ/CO/BTN by design (see the T2 note below). The no-limp
  invariants and the `vs_rfi` replacement remain live W3R-1 law.

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


# T1's vs_rfi invariant is "offsuit trash NEVER COLD-CALLS a raise" — that is
# what audit-F11 struck and what this test protects. W5-b4 (2026-07-31) added
# an any-two {3bet 0.05, fold 0.95} catch-all (the maniac's light cold-3bet
# tell), so trash now 3-bets occasionally — but flatting remains impossible:
# the F11 guarantee is asserted directly, not via the exact action set.
@pytest.mark.parametrize("hand", ["J2o", "72o", "92o", "Q4o", "K5o"])
def test_maniac_vs_rfi_offsuit_trash_folds_never_calls(packs, hand):
    # Deterministic form (Codex, W5-b4): resolve the AUTHORED mix exactly like
    # the sampler and assert its call weight is literally zero — a stochastic
    # probe could miss a small reintroduced call weight.
    from app.domain.content.notation import hole_cards_to_class, parse_range

    pack = packs[VillainType("maniac")]
    cls = hole_cards_to_class(*_cards(hand))
    node = next(
        n for n in pack.preflop
        if n.facing == "vs_rfi"
        and (n.positions is None or Position.CO in n.positions)
    )
    mix = next(m for m in node.mixes if cls in parse_range(m.combos))
    assert mix.weights.get("call", 0.0) == 0.0, (
        f"{hand} resolved to a calling mix: {mix.combos!r} -> {dict(mix.weights)}"
    )
    acts = _actions(pack, Position.CO, "vs_rfi", hand)
    assert "call" not in acts, f"{hand} cold-called a raise: {acts}"
    assert acts <= {"3bet", "fold"}, f"{hand} vs_rfi actions {acts}"


@pytest.mark.parametrize("hand", ["55", "87s", "KQs"])
def test_maniac_vs_rfi_tier2_flats_and_3bets(packs, hand):
    # tier-2 (W5-b4: {3bet:0.5, call:0.5}): both actions observed, never a lone fold.
    acts = _actions(packs[VillainType("maniac")], Position.CO, "vs_rfi", hand)
    assert "call" in acts and "3bet" in acts, f"{hand} vs_rfi actions {acts}"


@pytest.mark.parametrize("hand", ["K5s", "A5o", "T9o"])
def test_maniac_vs_rfi_tier3_flats(packs, hand):
    # tier-3 (W5-b4: {3bet:0.2, call:0.3, fold:0.5}): flats (call) in >0 of N draws.
    acts = _actions(packs[VillainType("maniac")], Position.CO, "vs_rfi", hand)
    assert "call" in acts, f"{hand} vs_rfi actions {acts}"


@pytest.mark.parametrize("hand", ["AKo", "QQ"])
def test_maniac_vs_rfi_premiums_3bet(packs, hand):
    # tier-1 {3bet:1.0}: always 3bet.
    acts = _actions(packs[VillainType("maniac")], Position.CO, "vs_rfi", hand)
    assert acts == {"3bet"}, f"{hand} vs_rfi actions {acts}"


# T1's SB invariant is "maniac never OPEN-LIMPS from the SB" — an ACTION-SET
# check, not a range-width check (same rule as the lag T3 note below). R10-PRE2
# widened the maniac SB `unopened` node (ladder separation above the LAG), so
# all three probes now land inside the range's fringe mix (raise 0.7/fold 0.3);
# the pins are updated to the new ranges rather than the ranges being carved to
# keep the pins. `"limp" not in acts` — the actual T1 guarantee — is unchanged.
@pytest.mark.parametrize("hand", ["J2s", "32s", "K2o"])
def test_maniac_sb_no_open_limp(packs, hand):
    acts = _actions(packs[VillainType("maniac")], Position.SB, "unopened", hand)
    assert "limp" not in acts, f"{hand} maniac SB open-limped: {acts}"
    assert acts == {"raise", "fold"}, f"{hand} SB actions {acts}"


def test_maniac_unopened_has_no_limp_weight_anywhere(packs):
    # Pack-level form of T1's invariant (R10-PRE2 refuter: the 3-hand probe
    # above is a spot-check a reintroduced limp mix could slip past): no
    # `unopened` mix in the maniac pack may carry ANY limp weight, at any seat.
    for node in packs[VillainType("maniac")].preflop:
        if node.facing != "unopened":
            continue
        for mix in node.mixes:
            assert "limp" not in mix.weights, (
                f"maniac unopened limp weight reintroduced at "
                f"{node.positions}: {mix.combos!r} -> {dict(mix.weights)}"
            )


# --------------------------------------------------------------- T2 (maniac aces)


# T2 SUPERSEDED by R10-PRE2 (2026-07-30): the W3R-1 offsuit-ace trims
# (HJ→A7o+, CO/BTN→A5o+) were authored against the old ~50%-and-under maniac
# ladder. R10-PRE2 widens the whole ladder above the LAG's (HJ 57%, CO 64%,
# BTN 73% authored RFI), and at those widths excluding A2o-A6o while raising
# 96o/86o-type junk would be a range HOLE, not a trim — the LAG itself opens
# A2o+ at HJ. The trims' original purpose (maniac not wider than its seat
# budget on weak offsuit aces) is carried by the PRE2 ladder gates in
# test_personas.py; these tests now pin the NEW behavior: weak offsuit aces
# open (with fold mass from the mix weights, never pure-fold).
def test_maniac_hj_offsuit_aces_open(packs):
    pack = packs[VillainType("maniac")]
    assert "raise" in _actions(pack, Position.HJ, "unopened", "A2o")
    assert "raise" in _actions(pack, Position.HJ, "unopened", "A7o")


@pytest.mark.parametrize("position", [Position.CO, Position.BTN])
def test_maniac_co_btn_offsuit_aces_open(packs, position):
    pack = packs[VillainType("maniac")]
    assert "raise" in _actions(pack, position, "unopened", "A2o")
    assert "raise" in _actions(pack, position, "unopened", "A5o")


@pytest.mark.parametrize("position", [Position.HJ, Position.CO, Position.BTN])
def test_maniac_suited_ace_control_still_opens(packs, position):
    # A2s (suited) still opens from every trimmed position — trim is offsuit-only.
    assert "raise" in _actions(packs[VillainType("maniac")], position, "unopened", "A2s")


# Byte-identical EP/BB opening ranges (untouched by the offsuit-ace trims).
# RE-PINNED for R10-PRE1 (slice-authorized): the premium carve-out mix
# ("TT+, AQs+, AKo" -> raise 1.0) is prepended to EVERY unopened node so the
# maniac stops folding premiums first-in (R10-1b). The wide mixes below it
# are byte-identical to the W3R-1 pins.
# RE-PINNED for R10-PRE2 (slice-authorized): the ladder-separation slice
# rewrites every maniac unopened node (core raise 0.9 / fringe raise 0.7,
# widened above the LAG at every seat) — the W3R-1-era wide mixes no longer
# exist. "Untouched" now means "pinned against drift AFTER PRE2": these five
# seats' shapes are the PRE2-authored ranges verbatim.
_MANIAC_UNTOUCHED_OPENS = {
    Position.UTG: [
        ("TT+, AQs+, AKo", {"raise": 1.0}),  # R10-PRE1 premium carve-out
        ("22+, A2s+, K4s+, Q7s+, J7s+, T7s+, 96s+, 86s+, 76s, A6o+, K9o+, QTo+, JTo",
         {"raise": 0.9, "fold": 0.1}),
        ("K2s, K3s, Q5s, Q6s, J6s, T6s, 75s, 65s, 54s, A4o, A5o, K8o, Q9o, J9o, T9o",
         {"raise": 0.7, "fold": 0.3}),
    ],
    Position.UTG1: [
        ("TT+, AQs+, AKo", {"raise": 1.0}),  # R10-PRE1 premium carve-out
        ("22+, A2s+, K4s+, Q7s+, J7s+, T7s+, 96s+, 86s+, 75s+, 65s, A6o+, K9o+, Q9o+, J9o+, T9o",
         {"raise": 0.9, "fold": 0.1}),
        ("K2s, K3s, Q5s, Q6s, J6s, T6s, 54s, A4o, A5o, K8o, Q8o, J8o, T8o, 98o",
         {"raise": 0.7, "fold": 0.3}),
    ],
    Position.UTG2: [
        ("TT+, AQs+, AKo", {"raise": 1.0}),  # R10-PRE1 premium carve-out
        ("22+, A2s+, K3s+, Q6s+, J6s+, T6s+, 96s+, 85s+, 75s+, 64s+, A5o+, K8o+, Q9o+, J9o+, T9o",
         {"raise": 0.9, "fold": 0.1}),
        ("K2s, Q4s, Q5s, J5s, T5s, 54s, A3o, A4o, K7o, Q8o, J8o, T8o, 98o",
         {"raise": 0.7, "fold": 0.3}),
    ],
    Position.LJ: [
        ("TT+, AQs+, AKo", {"raise": 1.0}),  # R10-PRE1 premium carve-out
        ("22+, A2s+, K2s+, Q4s+, J5s+, T5s+, 95s+, 85s+, 74s+, 64s+, 53s+, "
         "A4o+, K7o+, Q8o+, J8o+, T8o+, 98o",
         {"raise": 0.9, "fold": 0.1}),
        ("Q2s, Q3s, J3s, J4s, T4s, 43s, A2o, A3o, K5o, K6o, Q7o, J7o, T7o, 97o, 87o",
         {"raise": 0.7, "fold": 0.3}),
    ],
    Position.BB: [
        ("TT+, AQs+, AKo", {"raise": 1.0}),  # R10-PRE1 premium carve-out
        ("22+, A2s+, K2s+, Q3s+, J5s+, T5s+, 95s+, 85s+, 74s+, 64s+, 53s+, "
         "A3o+, K6o+, Q8o+, J8o+, T8o+, 98o",
         {"raise": 0.9, "fold": 0.1}),
        ("Q2s, J3s, J4s, T4s, 43s, A2o, K4o, K5o, Q6o, Q7o, J7o, T7o, 97o, 87o",
         {"raise": 0.7, "fold": 0.3}),
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
# UPDATED AGAIN for N-LAGLADDER (2026-07-31, same precedent): the SB node is now
# emitted from content/personas/ladders/lag.unopened.json, and its suited rows
# run deeper than the hand-authored node did, so 54s moved from the fringe mix
# into the core.
#   54s -> mix 1 via `53s+` (raise 1.0)      32s -> outside the node
#   J9o -> mix 1 via `J8o+` (raise 1.0)
@pytest.mark.parametrize(
    ("hand", "expected"),
    [("54s", {"raise"}), ("32s", {"fold"}), ("J9o", {"raise"})],
)
def test_lag_sb_no_open_limp(packs, hand, expected):
    acts = _actions(packs[VillainType("lag")], Position.SB, "unopened", hand)
    assert "limp" not in acts, f"{hand} lag SB open-limped: {acts}"
    assert acts == expected, f"{hand} lag SB actions {acts}"


# Pin UPDATED for RR-HOLES (2026-07-31), per this file's own T3 precedent
# ("pins are updated to the new ranges rather than the ranges being carved to
# keep the pins"): RR-HOLES fixed two strictly-dominated row-gap typos in this
# node — QTs (Qs row: QJs played, Q9s/Q8s played, QTs skipped) and AQo (Ao
# row: AJo/ATo 3-bet at 0.6 while the stronger AQo had NO action), both added
# to the 3bet-0.6 mix. The W3R-1 invariant this pin protects — the four-mix
# replacement shape, and "offsuit trash never cold-calls" — is unchanged.
# Pin UPDATED AGAIN for N-LAGLADDER (2026-07-31), same precedent: RR-HOLES
# flagged row T-F3 ("lag AQo fold-0.4 vs one raise is nitty") is fixed by
# CARVING AQo out of the 3bet-0.6 mix into its own {3bet 0.6, call 0.4} mix —
# the sanctioned carve-out idiom (first-match-wins peels exactly that class
# off the wider mix). The 3bet weight is deliberately IDENTICAL on both sides
# of the carve, so the pack's authored 3-bet width does not move; only the
# fold mass does, and it goes to call. The node is a FIVE-mix shape now;
# "offsuit trash never cold-calls" is unchanged (AQo is not trash) and the
# dominant non-fold weights still only descend, so RR-LINT stays clean.
_LAG_VS_RFI = [
    ("JJ+, AQs+, AKo", {"3bet": 1.0}),
    ("AQo", {"3bet": 0.6, "call": 0.4}),
    ("TT, 99, 88, AJs, ATs, A9s, A8s, A7s, A6s, A5s, A4s, A3s, KQs, KJs, KTs, QTs, QJs, "
     "JTs, AJo, ATo, KQo, KJo", {"3bet": 0.6, "fold": 0.4}),
    ("77, 66, 55, 44, 33, 22, K9s, K8s, Q9s, Q8s, J9s, J8s, T9s, T8s, 98s, 87s, 76s, 65s, "
     "54s, QJo, JTo, T9o, 98o", {"call": 1.0}),
    ("A9o, A8o, A7o, A6o, K7s, Q7s, J7s, T7s, 43s, KTo, QTo, J9o, T8o, 87o",
     {"call": 0.65, "fold": 0.35}),
]


def test_lag_vs_rfi_byte_identical(packs):
    node = _find_node(packs[VillainType("lag")], "vs_rfi", Position.CO)
    assert node is not None and _mix_shape(node) == _LAG_VS_RFI
