"""The 6-max baseline measurement (M1 T4): play thousands of simulated 6-max
hands with the live bots, measure every bot and the owner's real session
through the shared stat definitions in `tools/table_stats.py`, and run the
pre-registered fidelity check (does the simulation match the real hands?).

Binding rules live in `docs/ai-dlc/specs/m1-6max-baseline.md` section 2:
- Seats copy real session 4b35736f; seat 0 is a TAG standing in for the
  owner and is reported on its own row, never pooled with seats 3 and 4.
- Button rotates `i % 6`; each hand draws fresh 95-105bb stacks with
  `_draw_buyin_targets(hand_seed, 6)` (no carry-over); the hand seed is
  derived exactly as `run_export` derives it, from the same `rng` that is
  then handed to `play_one_hand`.
- Packs are the raw as-loaded `load_persona_packs()`.
- The tool writes no Parquet and never calls `run_export`, `derobo_gate`,
  `sweep_runner` or the data-contract check. It only prints Markdown.

Usage:
    python -m tools.sixmax_baseline --session <id> --max-hand-no <n>
        [--hands 6000] [--seed 20260926] [--db PATH]
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import UTC, datetime

from app.domain.archetypes import VillainType
from app.domain.personas import load_persona_packs
from tools.export_analytics import _draw_buyin_targets, play_one_hand
from tools.export_session import _git_sha
from tools.table_stats import Hand, load, replay, resolve_db_path, settle_hand, stats_for, wilson

SEATS: dict[int, str] = {
    0: VillainType.TAG.value,  # stand-in for the owner
    1: VillainType.NIT.value,
    2: VillainType.LAG.value,
    3: VillainType.TAG.value,
    4: VillainType.TAG.value,
    5: VillainType.CALLING_STATION.value,
}
SIXMAX_POSITIONS = ("BTN", "SB", "BB", "LJ", "HJ", "CO")
RFI_POSITIONS = ("LJ", "HJ", "CO", "BTN", "SB")

# Simulated groups: seats 3+4 pooled as the TAG; the seat-0 stand-in stays apart.
SIM_GROUPS: dict[str, list[int]] = {
    "nit": [1],
    "lag": [2],
    "tag": [3, 4],
    "station": [5],
    "stand-in tag (seat 0)": [0],
}
# Real rows: each bot seat alone -> (seat, simulated group it is compared with).
REAL_ROWS: dict[str, tuple[int, str]] = {
    "nit": (1, "nit"),
    "lag": (2, "lag"),
    "tag seat 3": (3, "tag"),
    "tag seat 4": (4, "tag"),
    "station": (5, "station"),
}
FIDELITY_STATS = ("VPIP", "PFR")
MIN_REAL_CHANCES = 30
MIN_ELIGIBLE = 8
MAX_MISSES_FOR_PASS = 1  # owner ruling 2026-09-26: one miss still passes


def run_baseline(n_hands: int, seed: int) -> list[Hand]:
    """Play `n_hands` 6-max hands with the live bots; deterministic per seed."""
    packs = load_persona_packs()
    rng = random.Random(seed)
    hands: list[Hand] = []
    for i in range(n_hands):
        hand_seed = rng.randrange(1_000_000_000)
        stacks = _draw_buyin_targets(hand_seed, 6)
        res = play_one_hand(rng, hand_seed, i % 6, SEATS, packs, stacks_bb=stacks)
        hands.append(Hand(i, f"sim-{i}", res["state"]))
    return hands


def measure(hands: list[Hand], seats: dict[int, str], groups: dict[str, list[int]]) -> dict:
    """{group: {stat label: (successes, chances)}}, every stat via `stats_for`."""
    replays = {h.hand_no: replay(h) for h in hands}
    settles = {h.hand_no: settle_hand(h) for h in hands}
    nets = {k: v[0] for k, v in settles.items()}
    shows = {k: v[1] for k, v in settles.items()}
    out: dict[str, dict[str, tuple[int, int]]] = {}
    for name, seat_list in groups.items():
        st, per_pos = stats_for(seat_list, seats, hands, replays, nets, shows)
        counts = {
            "VPIP": (int(st["vpip"]), int(st["hands"])),
            "PFR": (int(st["pfr"]), int(st["hands"])),
        }
        for pos in RFI_POSITIONS:
            pc = per_pos.get(pos, {})
            counts[f"RFI {pos}"] = (int(pc.get("rfi", 0)), int(pc.get("rfi_opp", 0)))
        counts["flop c-bet"] = (int(st["cbet"]), int(st["cbet_opp"]))
        counts["WTSD"] = (int(st["wtsd_num"]), int(st["saw_flop"]))
        out[name] = counts
    return out


def check_real_seats(seats: dict[int, str]) -> None:
    """The real session must seat the same bots as SEATS (seats 1-5)."""
    for seat in range(1, 6):
        if seats.get(seat) != SEATS[seat]:
            raise ValueError(
                f"real session seat {seat} is {seats.get(seat)!r}, expected {SEATS[seat]!r} "
                f"(this tool assumes the seat map of session 4b35736f)"
            )


def _within(real_rate: float, real_lo: float, real_hi: float, sim_lo: float, sim_hi: float):
    """One comparison: is the real rate inside the sim interval widened by the
    real interval's half-width? Returns (passed, lower bound, upper bound)."""
    h = (real_hi - real_lo) / 2
    lo, hi = sim_lo - h, sim_hi + h
    return lo <= real_rate <= hi, lo, hi


def fidelity_check(pairs: list[dict]) -> dict:
    """Pre-registered fidelity check (spec section 2). Each pair holds
    {bot, stat, real_k, real_n, sim_k, sim_n}. A pair is eligible iff
    real_n >= 30; fewer than 8 eligible -> CANT_TELL; else PASS with at most
    one miss, FAIL with two or more."""
    rows = []
    for p in pairs:
        real_lo, real_hi = wilson(p["real_k"], p["real_n"])
        sim_lo, sim_hi = wilson(p["sim_k"], p["sim_n"])
        real_rate = p["real_k"] / p["real_n"] if p["real_n"] else 0.0
        eligible = p["real_n"] >= MIN_REAL_CHANCES
        passed, lo, hi = _within(real_rate, real_lo, real_hi, sim_lo, sim_hi)
        rows.append(
            {
                **p,
                "real_rate": real_rate,
                "real_ci": (real_lo, real_hi),
                "sim_rate": p["sim_k"] / p["sim_n"] if p["sim_n"] else 0.0,
                "sim_ci": (sim_lo, sim_hi),
                "bounds": (lo, hi),
                "eligible": eligible,
                "passed": passed if eligible else None,
            }
        )
    eligible_rows = [r for r in rows if r["eligible"]]
    misses = sum(1 for r in eligible_rows if not r["passed"])
    if len(eligible_rows) < MIN_ELIGIBLE:
        verdict = "CANT_TELL"
    elif misses <= MAX_MISSES_FOR_PASS:
        verdict = "PASS"
    else:
        verdict = "FAIL"
    return {"verdict": verdict, "eligible": len(eligible_rows), "misses": misses, "rows": rows}


def _pct(x: float) -> str:
    text = f"{100 * x:.1f}"
    # wilson() can return a lower bound a hair below zero from float rounding.
    return ("0.0" if text == "-0.0" else text) + "%"


def _cell(k: int, n: int) -> str:
    if n == 0:
        return "n=0 · —"
    lo, hi = wilson(k, n)
    return f"n={n} · {_pct(k / n)} [{_pct(lo)}, {_pct(hi)}]"


def _stats_table(title: str, groups: dict[str, dict]) -> list[str]:
    stat_names = list(next(iter(groups.values())).keys())
    lines = [f"## {title}", "", "| stat | " + " | ".join(groups) + " |"]
    lines.append("|---|" + "---|" * len(groups))
    for stat in stat_names:
        cells = [_cell(*groups[g][stat]) for g in groups]
        lines.append(f"| {stat} | " + " | ".join(cells) + " |")
    lines.append("")
    return lines


def _fidelity_table(result: dict) -> list[str]:
    lines = [
        "## Fidelity check (pre-registered)",
        "",
        f"Eligible iff real chances >= {MIN_REAL_CHANCES}; fewer than {MIN_ELIGIBLE} eligible "
        f"-> CANT_TELL; PASS with at most {MAX_MISSES_FOR_PASS} miss, FAIL with more.",
        "",
        "| real bot | stat | real | sim (compared group) | pass range | eligible | result |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in result["rows"]:
        lo, hi = r["bounds"]
        outcome = "—" if r["passed"] is None else ("pass" if r["passed"] else "MISS")
        lines.append(
            f"| {r['bot']} | {r['stat']} | {_cell(r['real_k'], r['real_n'])} | "
            f"{_cell(r['sim_k'], r['sim_n'])} | [{_pct(lo)}, {_pct(hi)}] | "
            f"{'yes' if r['eligible'] else 'no'} | {outcome} |"
        )
    lines += [
        "",
        f"**Verdict: {result['verdict']}** — {result['eligible']} eligible, "
        f"{result['misses']} miss(es).",
        "",
    ]
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(
        description="6-max baseline: simulate the live bots at 6-max, measure them next to "
        "a real session, and run the pre-registered fidelity check."
    )
    parser.add_argument("--session", required=True, help="real sim_session.id (uuid4 hex)")
    parser.add_argument(
        "--max-hand-no",
        type=int,
        required=True,
        help="cap the real session to hand_no <= N (the session can still grow).",
    )
    parser.add_argument("--hands", type=int, default=6000, help="simulated hands (default 6000)")
    parser.add_argument("--seed", type=int, default=20260926, help="run seed (default 20260926)")
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="path to the sqlite DB file to read. Defaults to $POKER_COACH_DB, then "
        "the live app's DB (app.db.session.DB_PATH).",
    )
    args = parser.parse_args()

    db_path = resolve_db_path(args.db)
    real_seats, real_hands, n_skipped = load(
        args.session, max_hand_no=args.max_hand_no, db_path=db_path
    )
    if not real_hands:
        print(
            f"no hands found for session {args.session!r} in {db_path} (skipped {n_skipped})",
            file=sys.stderr,
        )
        raise SystemExit(1)
    check_real_seats(real_seats)
    if n_skipped:
        print(f"skipped {n_skipped} real hand(s) total (see above for reasons)", file=sys.stderr)

    sim_hands = run_baseline(args.hands, args.seed)
    sim = measure(sim_hands, SEATS, SIM_GROUPS)
    real_groups = {name: [seat] for name, (seat, _) in REAL_ROWS.items()}
    real = measure(real_hands, real_seats, real_groups)
    pairs = []
    for name, (_, sim_group) in REAL_ROWS.items():
        for stat in FIDELITY_STATS:
            real_k, real_n = real[name][stat]
            sim_k, sim_n = sim[sim_group][stat]
            pairs.append(
                {
                    "bot": name,
                    "stat": stat,
                    "real_k": real_k,
                    "real_n": real_n,
                    "sim_k": sim_k,
                    "sim_n": sim_n,
                }
            )
    result = fidelity_check(pairs)

    command = "python -m tools.sixmax_baseline " + " ".join(sys.argv[1:])
    lines = [
        "# 6-max baseline",
        "",
        f"- command: `{command}`",
        f"- seed: {args.seed} · simulated hands: {args.hands}",
        f"- real session: `{args.session}` · hand_no <= {args.max_hand_no} · "
        f"{len(real_hands)} hands · db=`{db_path.name}`",
        f"- git SHA: `{_git_sha()}`",
        f"- date (UTC): {datetime.now(UTC).date().isoformat()}",
        "",
        "Cells: chances n · rate [95% Wilson interval].",
        "",
    ]
    lines += _stats_table("Simulated bots (6-max)", sim)
    lines += _stats_table("Real session, per bot seat", real)
    lines += _fidelity_table(result)
    lines += [
        "## Flop c-bet — not tested against real play",
        "",
        "| real bot | c-bet chances | c-bet |",
        "|---|---|---|",
    ]
    for name in REAL_ROWS:
        k, n = real[name]["flop c-bet"]
        lines.append(f"| {name} | {n} | {_cell(k, n)} |")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
