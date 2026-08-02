"""Analytics export: seeded persona self-play -> Parquet + JSON _SUCCESS manifest.

Producer side of the poker-analytics data contract
(`contracts/poker_events.odcs.yaml` in the consumer repo). Plays N full
9-seat hands with every seat driven by the production bot policy
(`play.bot_decision` — the same code path the live table uses, NOT the
test harness sampler) and writes three Parquet tables:

  hands          one row per hand
  seat_outcomes  one row per (hand, seat) — 9 rows per hand
  decisions      one row per action event, blind posts included

plus a JSON `_SUCCESS` marker written LAST (Hadoop manifest-committer
convention): its presence signals a complete, uncorrupted batch, and its
body carries the run manifest (git SHA, RNG seed, persona lineup, engine
version, contract version, row counts).

Reproducibility: one CLI seed drives both the deals and every persona's
action draws, so the same (seed, hands, lineup) produces byte-identical
tables modulo the `exported_at` load-timestamp column.

Usage (from backend/):
    python -m tools.export_analytics --hands 5000 --seed 42 --out /path/to/data/raw/v1
Requires the `export` extra: pip install -e '.[export]' (pyarrow).
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from app.domain.archetypes import VillainType
from app.domain.personas import load_persona_packs
from app.domain.spot import PlayerStatus
from app.domain.table.deck import deal_hand
from app.domain.table.engine import apply, settle, start_hand
from app.domain.table.play import bot_decision

CONTRACT_VERSION = "1.0.0"  # semver of the ODCS contract this export conforms to
SCHEMA_PATH_VERSION = "v1"  # data-path major; bumps only on a breaking change
STACKS_BB = 100.0  # every seat starts each hand at 100bb (reset per hand)

# Default lineup mirrors the persona test harness: the 6 personas in sorted
# order, wrapped around 9 seats. The button rotates hand-by-hand so every
# persona plays every position.
DEFAULT_LINEUP = sorted(v.value for v in VillainType)


def _git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
            cwd=Path(__file__).resolve().parent,
        ).stdout.strip()
    except Exception:
        return "unknown"


def play_one_hand(rng: random.Random, hand_seed: int, button_seat: int,
                  persona_by_seat: dict[int, str], packs) -> dict:
    """One full production-policy playout. Returns the raw rows for all
    three tables. Deliberately thin: derivations that SQL can do (facing,
    aggression, VPIP flags...) belong downstream in dbt, not here."""
    state = start_hand(deal_hand(random.Random(hand_seed)), button_seat,
                       stacks_bb=[STACKS_BB] * 9)
    decision_rows: list[dict] = []
    seq = 0
    # Blind posts happen inside start_hand; emit them as action rows so the
    # decisions table reconciles to the pot (action='post').
    for h in state.action_history:
        seat = next(s.seat for s in state.seats if s.position is h.position)
        decision_rows.append({
            "seq": seq, "seat": seat, "street": h.street.value,
            "position": h.position.value, "action": h.action.value,
            "raise_to_bb": None, "chips_committed_bb": h.amount_bb,
            "pot_before_bb": 0.0, "to_call_bb": 0.0,
        })
        seq += 1
    saw_flop: set[int] = set()
    guard = 0
    while not state.hand_over:
        guard += 1
        if guard > 500:
            raise RuntimeError(f"hand did not terminate (seed={hand_seed})")
        if len(state.board) >= 3 and not saw_flop:
            saw_flop = {s.seat for s in state.seats
                        if s.status in (PlayerStatus.IN, PlayerStatus.ALLIN)}
        seat = state.to_act_seat
        seat_state = state.seats[seat]
        pot_before = sum(s.invested_total_bb for s in state.seats)
        to_call = max(0.0, state.current_bet_bb - seat_state.invested_street_bb)
        invested_before = seat_state.invested_total_bb
        decision = bot_decision(state, seat, packs[persona_by_seat[seat]], rng)
        state = apply(state, decision)
        decision_rows.append({
            "seq": seq, "seat": seat, "street": state.action_history[-1].street.value,
            "position": seat_state.position.value,
            "action": decision.action.value,
            "raise_to_bb": decision.size_bb,
            "chips_committed_bb": round(
                state.seats[seat].invested_total_bb - invested_before, 2),
            "pot_before_bb": round(pot_before, 2),
            "to_call_bb": round(to_call, 2),
        })
        seq += 1
    # All-in run-outs can reveal the flop on the same apply() that ends the
    # hand, skipping the loop-top capture — catch that here.
    if len(state.board) >= 3 and not saw_flop:
        saw_flop = {s.seat for s in state.seats
                    if s.status in (PlayerStatus.IN, PlayerStatus.ALLIN)}
    settlement = settle(state)
    winners = {s for pot in settlement.winners_by_pot for s in pot}
    seat_rows = []
    for s in state.seats:
        delta = settlement.deltas[s.seat].delta_bb
        seat_rows.append({
            "seat": s.seat, "persona": persona_by_seat[s.seat],
            "position": s.position.value,
            "hole_cards": " ".join(s.hole_cards),
            "starting_stack_bb": STACKS_BB,
            "invested_bb": round(s.invested_total_bb, 2),
            "delta_bb": delta,
            "final_status": s.status.value,
            "saw_flop": s.seat in saw_flop,
            "went_to_showdown": s.seat in settlement.showdown_seats,
            "won_pot": s.seat in winners,
        })
    hand_row = {
        "button_seat": button_seat,
        "hand_seed": hand_seed,
        "board": " ".join(state.board),
        "final_street": state.street.value,
        "total_pot_bb": round(sum(s.invested_total_bb for s in state.seats), 2),
        "went_to_showdown": bool(settlement.showdown_seats),
        "n_saw_flop": len(saw_flop),
    }
    return {"hand": hand_row, "seats": seat_rows, "decisions": decision_rows}


def run_export(n_hands: int, seed: int, out_dir: Path,
               lineup: list[str] | None = None) -> dict:
    import pyarrow as pa
    import pyarrow.parquet as pq

    lineup = lineup or DEFAULT_LINEUP
    persona_by_seat = {i: lineup[i % len(lineup)] for i in range(9)}
    packs = load_persona_packs()
    rng = random.Random(seed)
    run_id = f"run-s{seed}-n{n_hands}"
    exported_at = datetime.now(UTC).isoformat(timespec="seconds")

    hands, seats, decisions = [], [], []
    for i in range(n_hands):
        hand_id = f"{run_id}-h{i:07d}"
        res = play_one_hand(rng, rng.randrange(1_000_000_000), i % 9,
                            persona_by_seat, packs)
        hands.append({"hand_id": hand_id, "run_id": run_id, "hand_no": i,
                      **res["hand"], "exported_at": exported_at})
        for r in res["seats"]:
            seats.append({"hand_id": hand_id, **r, "exported_at": exported_at})
        for r in res["decisions"]:
            decisions.append({"hand_id": hand_id, **r, "exported_at": exported_at})

    out_dir.mkdir(parents=True, exist_ok=True)
    success = out_dir / "_SUCCESS"
    success.unlink(missing_ok=True)  # invalidate the batch before rewriting it
    row_counts = {}
    for name, rows in (("hands", hands), ("seat_outcomes", seats),
                       ("decisions", decisions)):
        table = pa.Table.from_pylist(rows)
        pq.write_table(table, out_dir / f"{name}.parquet", compression="zstd")
        row_counts[name] = len(rows)

    manifest = {
        "run_id": run_id,
        "seed": seed,
        "n_hands": n_hands,
        "lineup": persona_by_seat,
        "stacks_bb": STACKS_BB,
        "git_sha": _git_sha(),
        "engine": "poker-coach backend/app/domain (production bot policy)",
        "generator": "backend/tools/export_analytics.py",
        "contract_version": CONTRACT_VERSION,
        "schema_path_version": SCHEMA_PATH_VERSION,
        "exported_at": exported_at,
        "row_counts": row_counts,
    }
    # Written LAST: consumers must refuse to read a directory without it.
    success.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hands", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, required=True,
                    help="target directory, e.g. <analytics-repo>/data/raw/v1/sample")
    args = ap.parse_args()
    manifest = run_export(args.hands, args.seed, args.out)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
