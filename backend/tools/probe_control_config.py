"""Probe: measure decision-level degeneracy of a §c counterfactual config.

Flywheel S6 ticket T1 ("pin the degenerate control config"). Throwaway-quality
CLI kept for provenance, not a permanent pipeline component: given a §c
counterfactual-config JSON file (`backend/tools/counterfactual.py`), run the
export machinery for a small batch of hands and report how DEGENERATE the
resulting bot play is — the share of decisions that fall in a single
("modal") action class (fold/check/call/bet/raise).

Reuses `tools.export_analytics.run_export` programmatically (same code path
`export_analytics.py --config` uses) rather than re-implementing export or
scoring. Blind/straddle posts (`action == "post"`) are excluded from the
degeneracy statistic: they are forced, not policy decisions, and the §a.2 axis
table has no lever over them.

Usage (from backend/, as a module — see repo convention note in `main()`):
    python -m tools.probe_control_config <config.json> --seed 901 --n-hands 500 \
        [--buyin-spread]
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
import tempfile
from pathlib import Path

from tools import counterfactual
from tools.counterfactual import CounterfactualConfigError
from tools.export_analytics import run_export


def measure_degeneracy(
    config_path: Path, seed: int, n_hands: int, buyin_spread: bool = False
) -> dict:
    """Validate `config_path`, export `n_hands`, and return the degeneracy
    stats: `config_hash`, per-class decision counts (posts excluded), the
    modal class + its count, and `degeneracy` = modal_count / total.

    `buyin_spread` passes through to `run_export` (F1, flywheel S6 T2): the
    control bundle must be measured under the SAME buy-in treatment the bot
    corpus actually uses, not the flat-100bb default, since stack depth can
    alter legal actions/decisions."""
    try:
        validated = counterfactual.load_config(config_path)
    except CounterfactualConfigError as exc:
        print(f"ERROR: {config_path}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    import pyarrow.parquet as pq

    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        run_export(
            n_hands, seed, out_dir,
            packs=validated.packs, config_hash=validated.config_hash,
            buyin_spread=buyin_spread,
        )
        decisions = pq.read_table(out_dir / "decisions.parquet").to_pylist()

    non_post = [row for row in decisions if row["action"] != "post"]
    counts = collections.Counter(row["action"] for row in non_post)
    if not counts:
        raise RuntimeError("no non-post decisions were recorded — cannot measure degeneracy")
    modal_class, modal_count = counts.most_common(1)[0]
    return {
        "config_hash": validated.config_hash,
        "seed": seed,
        "n_hands": n_hands,
        "buyin_spread": buyin_spread,
        "total_decisions": len(non_post),
        "counts": dict(counts),
        "modal_class": modal_class,
        "modal_count": modal_count,
        "degeneracy": modal_count / len(non_post),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("config", type=Path, help="path to a §c counterfactual-config JSON file")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--n-hands", type=int, default=500)
    ap.add_argument("--buyin-spread", action="store_true",
                     help="export with the F1 buy-in spread (matches the corpus's "
                          "control-bundle treatment) instead of the flat-100bb default")
    args = ap.parse_args()

    result = measure_degeneracy(args.config, args.seed, args.n_hands, args.buyin_spread)
    print(f"config_hash: {result['config_hash']}")
    print(f"degeneracy: {result['degeneracy']:.4f}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
