"""De-robotization per-change gate — the runner (poker-coach side).

Produces a candidate self-play batch and hands it to poker-analytics' two §a.5
constraint rules, which the phase-3 ruling names as the free per-change gates
for the bot-improvement work:

    separation floor    the six personas must stay distinguishable from one
                        another — nearest-centroid label preservation 6/6 and
                        minimum pairwise distance >= 0.70 x the frozen pre-fix
                        roster's
    determinism guard   per persona, the modal action's share may reach 0.98 in
                        at most 20% of decision contexts observed >= 50 times

Neither rule lives here. Both are imported unchanged by
`poker-analytics:analysis/derobo_gate_check.py`; this module only builds the
candidate batch and reports what they say.

Two properties this runner is built around
------------------------------------------
**Every pin is read from the baseline artifact, never transcribed.** Seed, hand
count and the nine-seat lineup all come out of the artifact's `source_batch`
block, so a candidate cannot silently be measured under different conditions
than the baseline it is compared against. A transcription error here would
produce a confident, meaningless verdict — the failure mode this project has
already hit twice.

**The analytics stack runs in its own interpreter.** `scorer.constraints`
imports numpy and duckdb, and the poker-coach backend environment has neither.
Rather than install the analytics dependency set here, the check runs as a
subprocess under poker-analytics' own virtual environment and returns JSON.

Usage (from backend/):
    python -m tools.derobo_gate --self-test    # prove the gate before trusting it
    python -m tools.derobo_gate --check        # judge the working tree, seed 601
    python -m tools.derobo_gate --check --all-seeds   # slice-level, seeds 601-605
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from tools import export_analytics

# backend/tools/derobo_gate.py -> parents[2] == repo root
REPO_ROOT = Path(__file__).resolve().parents[2]


# The file that proves a directory is really a usable analytics checkout.
# Testing for the DIRECTORY is not enough: an abandoned worktree leaves an
# empty directory of the right name behind, which would otherwise be selected
# and then fail with a confusing "checker not found".
_ANALYTICS_MARKER = Path("scorer") / "artifacts" / "a5_baseline_z.json"


def _looks_like_analytics(root: Path) -> bool:
    return (root / _ANALYTICS_MARKER).is_file()


def _default_analytics_root() -> Path:
    """poker-analytics as a sibling checkout, resolved from the MAIN worktree.

    Branch work in this repo happens in linked worktrees under a temp
    directory, whose parent has no analytics checkout beside it. Asking git for
    the common directory gets us back to the main checkout, so the default
    works from a worktree instead of demanding `--analytics-root` every time.

    Candidates are tried in order and each must contain the baseline artifact
    to be accepted. The first candidate is returned unconditionally as the
    fallback, so a genuine misconfiguration still reports the path a user most
    likely meant.
    """
    candidates = [REPO_ROOT.parent / "poker-analytics"]
    try:
        common = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        if common:
            # `<main checkout>/.git` -> the main checkout -> its sibling
            candidates.append(Path(common).parent.parent / "poker-analytics")
    except (OSError, subprocess.CalledProcessError):
        pass
    for candidate in candidates:
        if _looks_like_analytics(candidate):
            return candidate
    return candidates[0]


DEFAULT_ANALYTICS = _default_analytics_root()

# The five-seed robustness set retained by the analytics repo's covariance
# artifact (cov-525e183a12f269e3.json, `seed_set`). A single seed is a
# deterministic smoke gate; the slice-level verdict uses all five, because both
# rules are discontinuous at their thresholds and a candidate near the
# separation floor can otherwise flip verdict on seed noise alone.
SEED_SET = (601, 602, 603, 604, 605)

# The frozen pre-fix roster this gate compares every candidate against. Pinned
# here so a different analytics checkout cannot be substituted silently.
EXPECTED_BASELINE_ARTIFACT_ID = "a5baseline-98abd160f03a501b"

# `export_analytics.run_export` always plays a nine-seat table and wraps a
# shorter lineup to fill it, so a lineup of any other length would be measured
# under seats the checker never hears about.
EXPECTED_SEATS = tuple(str(i) for i in range(9))


class GateError(RuntimeError):
    """The gate could not be run (distinct from the gate returning FAIL)."""


def analytics_paths(analytics_root: Path) -> tuple[Path, Path, Path]:
    """(python, checker script, baseline artifact) — all validated up front.

    Fails loudly and specifically here rather than letting a subprocess die
    with an opaque error three steps later.
    """
    python = analytics_root / ".venv" / "bin" / "python"
    checker = analytics_root / "analysis" / "derobo_gate_check.py"
    baseline = analytics_root / "scorer" / "artifacts" / "a5_baseline_z.json"
    for label, path in (("interpreter", python), ("checker", checker),
                        ("baseline artifact", baseline)):
        if not path.exists():
            raise GateError(
                f"poker-analytics {label} not found at {path}. Pass "
                f"--analytics-root if the repo is not a sibling checkout.")
    return python, checker, baseline


def read_pins(baseline: Path) -> dict:
    """Seed, hand count and lineup, taken from the baseline artifact itself.

    The artifact id is checked against `EXPECTED_BASELINE_ARTIFACT_ID`. Because
    both the pins and the comparison values come from this one file, a
    different-but-plausible artifact would be internally self-consistent and
    would pass every check while silently measuring against the wrong frozen
    roster. Binding the id is what stops a stale sibling checkout doing that.
    """
    artifact = json.loads(baseline.read_text())
    got = artifact.get("artifact_id")
    if got != EXPECTED_BASELINE_ARTIFACT_ID:
        raise GateError(
            f"baseline artifact at {baseline} has id {got!r}, but this gate is "
            f"pinned to {EXPECTED_BASELINE_ARTIFACT_ID!r} — the frozen pre-fix "
            "roster it compares against. Point --analytics-root at the right "
            "checkout, or update the pin deliberately if the baseline was "
            "legitimately rebuilt.")
    source = artifact["source_batch"]
    return {
        "seed": int(source["seed"]),
        "n_hands": int(source["n_hands"]),
        "lineup": {str(k): str(v) for k, v in source["lineup"].items()},
        "baseline_engine_sha": source["engine_git_sha"],
        "artifact_id": artifact["artifact_id"],
    }


def export_candidate(out_dir: Path, seed: int, n_hands: int,
                     lineup: dict[str, str]) -> dict:
    """Export one candidate batch under the baseline's pins.

    `buyin_spread` is left False: the baseline's run id
    (`run-s601-n50000-c9273b753b9de`) carries no `-bspread` token, so the
    baseline was built without it, and a candidate that enabled it would not be
    comparable.
    """
    # `run_export` wants a seat-ORDERED list; the artifact stores a
    # seat-keyed map. Convert via sorted integer seat so a map that happens to
    # serialise out of order cannot silently reorder the lineup.
    seats = tuple(sorted(lineup, key=int))
    if seats != EXPECTED_SEATS:
        raise GateError(
            f"baseline lineup seats {list(seats)} are not exactly "
            f"{list(EXPECTED_SEATS)}. `run_export` plays nine seats and wraps a "
            "shorter lineup to fill them, so anything else would be measured "
            "under seats the checker never sees.")
    manifest = export_analytics.run_export(
        n_hands=n_hands,
        seed=seed,
        out_dir=out_dir,
        lineup=[lineup[s] for s in seats],
        buyin_spread=False,
    )
    # Confirm the exporter actually honoured the pins rather than trusting that
    # it did — the batch is worthless if it was played under different ones.
    for key, want in (("seed", seed), ("n_hands", n_hands)):
        got = manifest.get(key)
        if got is not None and got != want:
            raise GateError(
                f"export manifest reports {key}={got!r} but the pins asked for "
                f"{want!r}; the candidate is not comparable to the baseline")
    return manifest


def run_check(python: Path, checker: Path, baseline: Path, batch: Path,
              lineup: dict[str, str], *, self_test: bool) -> dict:
    cmd = [str(python), str(checker), "--batch", str(batch),
           "--lineup", json.dumps(lineup), "--baseline", str(baseline)]
    if self_test:
        cmd.append("--self-test")
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if not proc.stdout.strip():
        raise GateError(
            f"checker produced no output (exit {proc.returncode}).\n"
            f"stderr:\n{proc.stderr[-2000:]}")
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise GateError(
            f"checker output was not JSON ({e}).\n"
            f"stdout:\n{proc.stdout[-2000:]}\nstderr:\n{proc.stderr[-2000:]}"
        ) from e

    # A verdict is only believed when it is unambiguous. `{"pass": "false"}` is
    # a truthy string, and a crashed checker that still printed a stale verdict
    # would otherwise read as PASS — the one failure mode this gate must never
    # have, since a false PASS silently certifies a broken change.
    if not isinstance(result, dict):
        raise GateError(
            "checker verdict is not a JSON object with a boolean `pass` "
            f"(got a {type(result).__name__}).\n"
            f"stdout:\n{proc.stdout[-2000:]}")
    verdict = result.get("pass")
    if not isinstance(verdict, bool):
        raise GateError(
            "checker verdict is not a JSON object with a boolean `pass` "
            f"(got {verdict!r} of type {type(verdict).__name__}).\n"
            f"stdout:\n{proc.stdout[-2000:]}")
    expected_code = 0 if result["pass"] else 1
    if proc.returncode != expected_code:
        raise GateError(
            f"checker exit code {proc.returncode} disagrees with its verdict "
            f"pass={result['pass']} (expected {expected_code}) — the process "
            "did not end the way its own output claims.\n"
            f"stderr:\n{proc.stderr[-2000:]}")
    return result


def gate(analytics_root: Path, seeds: tuple[int, ...] | None,
         *, self_test: bool, keep: Path | None = None) -> dict:
    python, checker, baseline_path = analytics_paths(analytics_root)
    pins = read_pins(baseline_path)
    run_seeds = seeds if seeds is not None else (pins["seed"],)

    results = []
    for seed in run_seeds:
        with tempfile.TemporaryDirectory(prefix=f"derobo-s{seed}-") as tmp:
            out_dir = Path(keep) / f"seed-{seed}" if keep else Path(tmp)
            out_dir.mkdir(parents=True, exist_ok=True)
            manifest = export_candidate(out_dir, seed, pins["n_hands"],
                                        pins["lineup"])
            result = run_check(python, checker, baseline_path, out_dir,
                               pins["lineup"], self_test=self_test)
            result["seed"] = seed
            result["candidate_run_id"] = manifest.get("run_id")
            result["candidate_config_hash"] = manifest.get("config_hash")
            results.append(result)

    return {
        "pass": all(r["pass"] for r in results),
        "mode": "self-test" if self_test else "check",
        "pins": pins,
        "results": results,
    }


def _summarise(report: dict) -> str:
    lines = [
        f"mode              {report['mode']}",
        f"baseline artifact {report['pins']['artifact_id']}",
        f"baseline engine   {report['pins']['baseline_engine_sha'][:12]}",
        f"pins              seed(s) from artifact, {report['pins']['n_hands']} hands",
        "",
    ]
    for r in report["results"]:
        verdict = "PASS" if r["pass"] else "FAIL"
        lines.append(f"seed {r['seed']}  {verdict}   run_id={r.get('candidate_run_id')}")
        if report["mode"] == "self-test":
            for c in r["checks"]:
                mark = "ok  " if c["pass"] else "FAIL"
                lines.append(f"    {mark} {c['check']}")
        else:
            sep = r["rules"]["separation_floor"]["evidence"]["separation"]
            lab = r["rules"]["separation_floor"]["evidence"]["label_preservation"]
            det = r["rules"]["determinism_guard"]
            lines.append(
                f"    separation  min pairwise {sep['candidate_min_pairwise_distance']}"
                f" vs required {sep['required_min_distance']}"
                f"  ({'ok' if sep['pass'] else 'FAIL'})")
            lines.append(
                f"    labels      {lab['correct_assignments']}/{lab['total_personas']}"
                f"  ({'ok' if lab['pass'] else 'FAIL'})")
            lines.append(
                f"    determinism {'ok' if det['pass'] else 'FAIL'}")
    lines.append("")
    lines.append("GATE PASS" if report["pass"] else "GATE FAIL")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="judge the working tree against the pinned baseline")
    mode.add_argument("--self-test", action="store_true",
                      help="prove the gate reproduces the baseline's known answers")
    ap.add_argument("--all-seeds", action="store_true",
                    help=f"run the five-seed robustness set {SEED_SET}")
    ap.add_argument("--analytics-root", type=Path, default=DEFAULT_ANALYTICS)
    ap.add_argument("--keep", type=Path, default=None,
                    help="retain exported batches in this directory")
    ap.add_argument("--json", action="store_true", help="emit the full report")
    args = ap.parse_args()

    report = gate(args.analytics_root,
                  SEED_SET if args.all_seeds else None,
                  self_test=args.self_test,
                  keep=args.keep)
    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(_summarise(report))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
