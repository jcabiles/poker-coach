"""Golden fingerprint of every bot decision at 9-max and 6-max on the
unchanged codebase: any change to the digest constants below means a bot
decision changed."""

from __future__ import annotations

import hashlib
import json
import random

from app.domain.personas import load_persona_packs
from app.domain.table.engine import HandState
from tools import export_analytics as ea
from tools.sixmax_baseline import run_baseline

N_HANDS = 360
NINE_MAX_SEED = 20260927
SIX_MAX_SEED = 20260927

# Pinned 2026-09-27. A future change to bot behaviour re-pins these constants
# when a bot decision intentionally changes; diff `per_hand_digests()` between
# commits to see exactly which hands moved.
NINE_MAX_DIGEST = "e6f5e36cc81add06cf84473cc2f3f4ae7989168f319a5ff59194b704a57d67e5"
SIX_MAX_DIGEST = "e0a811d107bc0f08565b69137393e211bab08505a70e30abae631818b3548d39"


def _hand_fingerprint(state: HandState) -> str:
    """SHA-256 of the hand's ordered action history (seat, position, street,
    action, amount), blind posts included."""
    position_to_seat = {s.position: s.seat for s in state.seats}
    records = [
        {
            "seat": position_to_seat[h.position],
            "position": h.position.value,
            "street": h.street.value,
            "action": h.action.value,
            "amount_bb": h.amount_bb,
        }
        for h in state.action_history
    ]
    payload = json.dumps(records, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _combine(digests: list[str]) -> str:
    return hashlib.sha256("\n".join(digests).encode()).hexdigest()


def _nine_max_states() -> list[HandState]:
    """Derives hand seeds, button rotation and lineup exactly as
    `run_export`'s default (no buyin-spread) path does, without writing
    Parquet."""
    packs = load_persona_packs()
    persona_by_seat = {i: ea.DEFAULT_LINEUP[i % len(ea.DEFAULT_LINEUP)] for i in range(9)}
    rng = random.Random(NINE_MAX_SEED)
    states = []
    for i in range(N_HANDS):
        hand_seed = rng.randrange(1_000_000_000)
        res = ea.play_one_hand(rng, hand_seed, i % 9, persona_by_seat, packs)
        states.append(res["state"])
    return states


def per_hand_digests(table_size: int) -> list[str]:
    """Per-hand SHA-256 fingerprints backing the pinned module digest for
    `table_size` (9 or 6). Re-pinning `NINE_MAX_DIGEST`/`SIX_MAX_DIGEST` is
    expected when a bot's behaviour intentionally changes; diff this
    function's output between the old and new commit to get a per-hand
    report of exactly which hands moved."""
    if table_size == 9:
        states = _nine_max_states()
    elif table_size == 6:
        states = [hand.state for hand in run_baseline(N_HANDS, SIX_MAX_SEED)]
    else:
        raise ValueError(f"unsupported table_size {table_size!r}")
    return [_hand_fingerprint(state) for state in states]


def test_nine_max_golden_fingerprint():
    digests = per_hand_digests(9)
    assert len(digests) == N_HANDS
    assert _combine(digests) == NINE_MAX_DIGEST


def test_six_max_golden_fingerprint():
    digests = per_hand_digests(6)
    assert len(digests) == N_HANDS
    assert _combine(digests) == SIX_MAX_DIGEST
