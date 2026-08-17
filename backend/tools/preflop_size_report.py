"""Realised preflop raise sizes, per persona and per seat — a non-gating report.

Why this exists. The two statistical gates are blind to bet size by
construction (rule 1 scores ten frequency statistics; rule 4 groups on action
type), so nothing in the automated stack can see whether a preflop sizing
change did what it claimed. Worse, a persona's authored mix is not what it
plays: `preflop_raise_to` clamps every draw into the engine's legal bracket, so
a short stack collapses a mix onto its boundary and an author reading the JSON
would never know. This report measures what the table actually saw.

It reads the same production playout the analytics export uses
(`export_analytics.play_one_hand`), so a number here is a number the exporter
would have written. It asserts nothing and fails nothing; it prints.

Usage (from backend/, with PYTHONPATH=.):

    python -m tools.preflop_size_report --hands 4000 --seed 601
    python -m tools.preflop_size_report --hands 4000 --seed 601 --json out.json

The default 4,000 hands is the sample the T2b ticket's own measurements were
taken over, and gives roughly a thousand opens for the loosest persona and a
couple of hundred for the tightest.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict

from app.domain.personas import load_persona_packs
from tools.export_analytics import DEFAULT_LINEUP, play_one_hand

# The preflop nodes in the order a raise war reaches them — the DOMAIN's own
# names, from `play._preflop_facing`, which is what selects the lever.
#
# The exported `engine_node_key` is deliberately not used here. It comes from
# `export_analytics._preflop_facing_label`, which is coarser: it lumps the
# 4-bet and the forced 5-bet jam together under `vs_3bet_plus`. That is fine
# for the determinism guard, which groups on it, and useless here, where the
# whole question is which lever produced a size. The node is re-derived below
# from the raise count in the row stream, exactly as `_preflop_facing` does.
NODES = ("unopened", "vs_limpers", "vs_rfi", "vs_3bet", "vs_4bet")

# Which persona lever each node's raise is drawn from, so the report can name
# the shipped scalar a realised distribution should be compared against.
LEVER_BY_NODE = {
    "unopened": "open_bb",
    "vs_limpers": "open_bb",  # open + 1bb per limper
    "vs_rfi": "threebet_mult",
    "vs_3bet": "fourbet_mult",
    "vs_4bet": None,  # a 5-bet is a forced jam, not a lever
}

# Seat order for the per-position tables. The big blind is included even though
# it can never open, because it DOES isolate limpers off the same seat table.
# An earlier version of this file left it out on the "a BB cannot open" premise
# and, in doing so, hid the one cell where three packs were still playing a
# single fixed size.
POSITIONS = ("UTG", "UTG1", "UTG2", "LJ", "HJ", "CO", "BTN", "SB", "BB")


def _node_for(n_raises_before: int, anyone_limped: bool) -> str:
    """`play._preflop_facing`, re-derived from the exported row stream.

    Kept as a separate function so
    `tests/test_preflop_size_values.py::test_the_reports_node_derivation_matches_the_domain`
    can compare it against the domain's own version over every action prefix,
    rather than trusting that the two agree.
    """
    if n_raises_before == 0:
        return "vs_limpers" if anyone_limped else "unopened"
    return {1: "vs_rfi", 2: "vs_3bet"}.get(n_raises_before, "vs_4bet")


def collect(hands: int, seed: int) -> dict:
    """Play `hands` nine-bot hands and bucket every preflop raise.

    The raise-TO is `decision.size_bb` AFTER the engine clamp, which is the
    point — an authored 4.5 that a 3bb-deep seat could not make is recorded
    here at whatever it actually became.
    """
    packs = load_persona_packs()
    persona_by_seat = {i: DEFAULT_LINEUP[i % len(DEFAULT_LINEUP)] for i in range(9)}
    rng = random.Random(seed)

    # persona -> node -> size -> count, and persona -> position -> size -> count
    by_node: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    by_seat: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    # persona -> node -> multiplier -> count, for the nodes whose lever is a
    # multiple of the raise faced rather than an absolute bb figure.
    by_mult: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    # persona -> position -> IMPLIED open -> count, for isolation raises. The
    # raise-TO is useless here: the iso is the open plus a bb per limper, so a
    # varying limper count spreads a completely fixed open across several
    # sizes. Subtracting the limpers back out is what makes a fixed cell
    # visible, and its absence is how three packs shipped a share-1.000 big
    # blind through a review round.
    iso_by_seat: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for i in range(hands):
        hand_seed = rng.randrange(1_000_000_000)
        res = play_one_hand(rng, hand_seed, i % 9, persona_by_seat, packs)
        persona_by_row_seat = {r["seat"]: r["persona"] for r in res["seats"]}
        last_raise_to = 1.0  # the big blind, before anyone raises
        n_raises = 0
        limpers = 0
        for row in res["decisions"]:
            if row["street"] != "preflop":
                continue
            if row["action"] == "call" and n_raises == 0:
                limpers += 1
            if row["action"] != "raise":
                continue
            node = _node_for(n_raises, limpers > 0)
            n_raises += 1
            persona = persona_by_row_seat[row["seat"]]
            size = round(float(row["raise_to_bb"]), 2)
            by_node[persona][node][size] += 1
            if node == "unopened":
                by_seat[persona][row["position"]][size] += 1
            elif node == "vs_limpers":
                implied = round(size - limpers, 2)
                iso_by_seat[persona][row["position"]][implied] += 1
            if LEVER_BY_NODE.get(node) in ("threebet_mult", "fourbet_mult"):
                by_mult[persona][node][round(size / last_raise_to, 2)] += 1
            last_raise_to = size

    return {
        "hands": hands,
        "seed": seed,
        "by_node": _plain(by_node),
        "by_seat": _plain(by_seat),
        "iso_by_seat": _plain(iso_by_seat),
        "by_mult": _plain(by_mult),
        "scalars": {
            name: {
                "open_bb": pack.sizing.open_bb,
                "threebet_mult": pack.sizing.threebet_mult,
                "fourbet_mult": pack.sizing.fourbet_mult,
            }
            for name, pack in packs.items()
        },
    }


def _plain(d) -> dict:
    """defaultdict tree -> plain dicts, so `json.dumps` does not instantiate
    missing keys while serialising."""
    if isinstance(d, defaultdict) or isinstance(d, dict):
        return {str(k): _plain(v) for k, v in d.items()}
    return d


def _mean(hist: dict) -> float:
    total = sum(hist.values())
    return sum(float(k) * n for k, n in hist.items()) / total if total else 0.0


def _fmt_hist(hist: dict) -> str:
    total = sum(hist.values())
    parts = [
        f"{k}={hist[k] / total:.3f}"
        for k in sorted(hist, key=float)
    ]
    return " ".join(parts)


def render(data: dict) -> str:
    """The human report. Shares are rounded to three places; a share that reads
    1.000 with a non-trivial count is a persona playing one size, which is the
    tell this whole ticket exists to remove."""
    out: list[str] = []
    out.append(f"Realised preflop raise sizes — {data['hands']} hands, seed {data['seed']}")
    out.append("")

    for persona in sorted(data["by_node"]):
        scalars = data["scalars"][persona]
        out.append(f"## {persona}")
        for node in NODES:
            hist = data["by_node"][persona].get(node)
            if not hist:
                out.append(f"  {node:<11} (no raises)")
                continue
            n = sum(hist.values())
            line = f"  {node:<11} n={n:<5} {_fmt_hist(hist)}"
            lever = LEVER_BY_NODE[node]
            if lever == "open_bb" and node == "unopened":
                mean = _mean(hist)
                shipped = scalars["open_bb"]
                line += f"  | mean={mean:.3f} shipped={shipped} delta={mean - shipped:+.3f}"
            out.append(line)
            mult = data["by_mult"].get(persona, {}).get(node)
            if mult:
                mean = _mean(mult)
                shipped = scalars[lever]
                out.append(
                    f"  {'':<11} realised x{_fmt_hist(mult)}"
                    f"  | mean={mean:.3f} shipped={shipped} delta={mean - shipped:+.3f}"
                )
        _seat_table(out, "open by seat", data["by_seat"].get(persona, {}))
        _seat_table(out, "iso by seat (implied open, limpers subtracted)",
                    data["iso_by_seat"].get(persona, {}))
        out.append("")
    return "\n".join(out)


def _seat_table(out: list[str], title: str, seats: dict) -> None:
    out.append(f"  {title}:")
    # Anything the data has that POSITIONS does not name is printed too. The
    # first draft of this report spelled two seats "UTG+1"/"UTG+2" against an
    # enum that says "UTG1"/"UTG2", and silently dropped a third of every
    # persona's opens behind a row reading "(none)".
    unnamed = [p for p in sorted(seats) if p not in POSITIONS]
    for pos in tuple(POSITIONS) + tuple(unnamed):
        hist = seats.get(pos)
        if not hist:
            out.append(f"    {pos:<6} (none)")
            continue
        n = sum(hist.values())
        out.append(f"    {pos:<6} n={n:<5} {_fmt_hist(hist)}  mean={_mean(hist):.3f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hands", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=601)
    ap.add_argument("--json", type=str, default=None,
                    help="also write the raw counts here, for a diff against "
                         "another run")
    args = ap.parse_args()
    data = collect(args.hands, args.seed)
    print(render(data))
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
