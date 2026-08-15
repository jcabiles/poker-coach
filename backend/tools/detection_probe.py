"""Phase-3 judge-bias probe — four known-quality stimuli, one judge, off-deck.

Spec: docs/ai-dlc/specs/phase3-probe.md · contracts: docs/ai-dlc/contracts/phase3-probe.md
Preregistered interpretation + budget: docs/ai-dlc/specs/phase3-decision-matrix.md §3.

Builds a tiny probe deck (4 bundles, 0 duplicates) in its OWN directory tree,
then judges it with ONE judge via the real harness (`detection_judge.run`), so
prompt, parsing, checkpointing and blinding guards are all the production ones.
Everything is dev/calibration work under amendment draft §G — never part of the
preregistered deck run, and structurally prevented from touching its paths.

Usage (from backend/):
    .venv/bin/python -m tools.detection_probe build --out ../docs/.../probe
    .venv/bin/python -m tools.detection_probe judge --root ../docs/.../probe --vendor stub
    .venv/bin/python -m tools.detection_probe judge --root ../docs/.../probe \
        --vendor anthropic:claude-sonnet-5
    .venv/bin/python -m tools.detection_probe report --root ../docs/.../probe
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from app.domain.personas import load_persona_packs
from tools import counterfactual, detection_judge
from tools.detection_corpus import (
    BUNDLE_SIZE,
    DEFAULT_CONTROL_CONFIG,
    DEFAULT_DB_PATH,
    HERO_SEAT,
    N_SEATS,
    PROTOCOL_CONTROL_CONFIG_HASH,
    RATIFIED_LINEUP,
    Bundle,
    CorpusBuildError,
    PresentationRecord,
    assign_constrained_focus_seats,
    bundle_trajectory,
    derive_rng,
    enumerate_windows,
    group_rows,
    read_human_snapshot,
    render_bundles,
    replay_run,
    run_id_for,
    seat_trajectories,
    validate_human_window,
    write_presentation_manifest,
)
from tools.detection_render import from_bot
from tools.export_analytics import _git_sha
from tools.probe_policies import rule_breaker_decision

# Probe run identities — DISTINCT from every deck seed (deck: bot 60001,
# control 60002; master 20260807). Off-deck by construction.
PROBE_MASTER_SEED = 70003
RULEBREAKER_SEED = 70001
T1_SEED = 70002
PRODUCTION_SEED = 70004
PROBE_RUN_HANDS = 40  # one 30-hand window + margin for the stride-free tiling
STRIDE = BUNDLE_SIZE + 1  # phase-walking parity with the deck's stride choice

# The live experiment's tree, resolved — the paths this module must never touch.
_S6_ROOT = (
    Path(__file__).resolve().parents[2]
    / "docs/ai-dlc/research/persona-realism-artifacts/detection-s6"
)
FORBIDDEN_TREES = (_S6_ROOT / "deck", _S6_ROOT / "judging")


class ProbePathError(RuntimeError):
    """Probe paths resolved into the live experiment tree — refused."""


def assert_probe_paths(*paths: Path) -> None:
    """Fail-closed guard (spec §1b): refuse any probe path inside the live
    deck/judging trees, and refuse identical paths (deck == out)."""
    resolved = [Path(p).resolve() for p in paths]
    for p in resolved:
        for tree in FORBIDDEN_TREES:
            if p == tree or tree in p.parents:
                raise ProbePathError(
                    f"probe path {p} resolves inside the live experiment tree {tree}"
                )
    if len(set(resolved)) != len(resolved):
        raise ProbePathError(f"probe paths must be distinct, got {resolved}")


# ---------------------------------------------------------------------------
# Stimulus builders (ticket P2)
# ---------------------------------------------------------------------------


def _one_window(n_hands: int):
    windows = enumerate_windows(0, n_hands - 1, BUNDLE_SIZE, stride=STRIDE)
    if not windows:
        raise CorpusBuildError(f"{n_hands} hands yield no {BUNDLE_SIZE}-hand window")
    return windows[0]


def _self_play_bundle(
    key: str,
    seed: int,
    packs: Mapping,
    human_phases: Sequence[tuple[str, ...]],
    *,
    decision_fn=None,
    provenance: Mapping | None = None,
) -> Bundle:
    """One 30-hand self-play stimulus, focus seat constrained to the human
    phase set (contract #5)."""
    window = _one_window(PROBE_RUN_HANDS)
    persona_by_seat = {i: RATIFIED_LINEUP[i % len(RATIFIED_LINEUP)] for i in range(N_SEATS)}
    if decision_fn is None:
        states = replay_run(seed, PROBE_RUN_HANDS, persona_by_seat, packs, keep=set(window.keys()))
    else:
        # Mirror replay_run's loop with a custom policy (replay_run hardcodes
        # bot_decision; detection_corpus is imports-only per the spec).
        import random as _random

        from app.domain.table.deck import deal_hand
        from app.domain.table.engine import apply, start_hand
        from tools.export_analytics import _draw_buyin_targets

        rng = _random.Random(seed)
        states = {}
        for i in range(PROBE_RUN_HANDS):
            hand_seed = rng.randrange(1_000_000_000)
            stacks = _draw_buyin_targets(hand_seed)
            state = start_hand(deal_hand(_random.Random(hand_seed)), i % N_SEATS, stacks)
            guard = 0
            while not state.hand_over:
                guard += 1
                if guard > 500:
                    raise CorpusBuildError(f"probe hand {i} did not terminate")
                state = apply(state, decision_fn(state, state.to_act_seat, None, rng))
            if i in window.keys():
                states[i] = state
    focus = assign_constrained_focus_seats(
        [seat_trajectories(states, window.keys())],
        list(human_phases),
        derive_rng(PROBE_MASTER_SEED, "probe-focus", key),
    )[0]
    return Bundle(
        key=key,
        label="bot",
        is_control=False,  # probe bundles carry no validity semantics
        focus_seat=focus,
        hands=tuple(from_bot(states[h], focus) for h in window.keys()),
        source=dict(provenance or {}),
    )


def build_human_stimulus(db_path: Path, deck_dir: Path) -> tuple[Bundle, dict]:
    """Owner human window: a VALID candidate NOT selected into the frozen deck,
    re-derived EXACTLY under the deck's recorded pins (contract #4, spec §1)."""
    unblinding = json.loads((deck_dir / "unblinding.json").read_text())
    pins = unblinding["pins"]["human"]
    snapshot = read_human_snapshot(db_path, pins["session_id"])
    if snapshot.session_id != pins["session_id"]:
        raise CorpusBuildError("snapshot session_id does not match the deck pin")
    # Filter to the pinned ceiling: read_human_snapshot has no pin parameter.
    rows = tuple(r for r in snapshot.rows if r.hand_no <= pins["n_pinned"])
    grouped = group_rows(rows)
    windows = enumerate_windows(snapshot.origin, pins["n_pinned"], BUNDLE_SIZE)
    checks = [validate_human_window(grouped, w, HERO_SEAT) for w in windows]
    derived = {
        c.window.index: {"start": c.window.start, "end": c.window.end, "valid": c.valid}
        for c in checks
    }
    recorded = {
        rec["window_index"]: {
            "start": rec["start"], "end": rec["end"], "valid": rec["valid"],
        }
        for rec in unblinding["human_windows"]["candidates"]
    }
    if derived != recorded:
        raise CorpusBuildError(
            "re-derived candidate table does not match the deck's recorded table — "
            "pins are stale or the DB mutated below the pin; refusing to continue"
        )
    selected = set(unblinding["human_windows"]["selected"])
    pool = sorted(i for i, c in derived.items() if c["valid"] and i not in selected)
    if not pool:
        raise CorpusBuildError("no valid non-selected human window exists")
    index = pool[0]  # deterministic choice
    check = next(c for c in checks if c.window.index == index)
    bundle = Bundle(
        key=f"probe-human/w{index:04d}",
        label="human",
        is_control=False,
        focus_seat=HERO_SEAT,
        hands=check.hands,
        source={"kind": "probe-human", "window_index": index},
    )
    meta = {"window_index": index, "session_id": snapshot.session_id}
    return bundle, meta


# ---------------------------------------------------------------------------
# Probe deck build (ticket P3)
# ---------------------------------------------------------------------------

STIMULUS_ORDER = ("rule-breaker", "t1-control", "production", "human-anchor")


def build_probe_deck(
    out_root: Path,
    *,
    db_path: Path = DEFAULT_DB_PATH,
    deck_dir: Path | None = None,
    control_config: Path = DEFAULT_CONTROL_CONFIG,
) -> dict:
    deck_dir = Path(deck_dir) if deck_dir else _S6_ROOT / "deck"
    out_root = Path(out_root)
    assert_probe_paths(out_root, out_root / "deck", out_root / "judging")

    human_bundle, human_meta = build_human_stimulus(Path(db_path), deck_dir)
    human_phases = [bundle_trajectory(human_bundle.hands)]

    packs = load_persona_packs()
    validated = counterfactual.load_config(Path(control_config))
    if validated.config_hash != PROTOCOL_CONTROL_CONFIG_HASH:
        raise CorpusBuildError(
            f"T1 control config hash {validated.config_hash} is not the pinned "
            f"{PROTOCOL_CONTROL_CONFIG_HASH}"
        )

    bundles = {
        "rule-breaker": _self_play_bundle(
            "probe-rb/w0000", RULEBREAKER_SEED, packs, human_phases,
            decision_fn=rule_breaker_decision,
            provenance={"kind": "probe-rule-breaker", "seed": RULEBREAKER_SEED},
        ),
        "t1-control": _self_play_bundle(
            "probe-t1/w0000", T1_SEED, validated.packs, human_phases,
            provenance={
                "kind": "probe-t1", "seed": T1_SEED, "config_hash": validated.config_hash,
            },
        ),
        "production": _self_play_bundle(
            "probe-prod/w0000", PRODUCTION_SEED, packs, human_phases,
            provenance={"kind": "probe-production", "seed": PRODUCTION_SEED},
        ),
        "human-anchor": human_bundle,
    }

    forbidden = sorted(
        {
            *RATIFIED_LINEUP,
            human_meta["session_id"],
            validated.config_hash,
            run_id_for(T1_SEED, PROBE_RUN_HANDS, validated.config_hash),
            _git_sha(),
        }
        - {""}
    )
    rendered = render_bundles(list(bundles.values()), PROBE_MASTER_SEED, BUNDLE_SIZE, forbidden)
    text_by_key = {b.key: text for b, _, text in rendered}

    # Opaque ids B001..B004 in a seeded shuffle of stimulus order — the judge
    # sees no ordering signal; the answer key stays in probe_key.json only.
    order = list(STIMULUS_ORDER)
    derive_rng(PROBE_MASTER_SEED, "probe-id-order").shuffle(order)
    records, answer_key = [], {}
    for i, name in enumerate(order):
        pid = f"B{i + 1:03d}"
        records.append(PresentationRecord(pid, text_by_key[bundles[name].key]))
        answer_key[pid] = name

    probe_deck = out_root / "deck"
    probe_deck.mkdir(parents=True, exist_ok=True)
    write_presentation_manifest(
        probe_deck / "presentation.json", records, forbidden, judge_slots=0
    )
    (out_root / "probe_key.json").write_text(
        json.dumps({"answer_key": answer_key, "human_meta": human_meta}, indent=2)
    )
    return {"deck": str(probe_deck), "stimuli": {n: bundles[n].key for n in STIMULUS_ORDER}}


# ---------------------------------------------------------------------------
# Judge + report
# ---------------------------------------------------------------------------


def judge_probe(out_root: Path, vendor: str, order_seed: int = PROBE_MASTER_SEED) -> dict:
    out_root = Path(out_root)
    deck, judging = out_root / "deck", out_root / f"judging-{vendor.replace(':', '-')}"
    assert_probe_paths(deck, judging)
    return detection_judge.run(deck, vendor, order_seed, out_dir=judging)


def report(out_root: Path) -> list[dict]:
    out_root = Path(out_root)
    key = json.loads((out_root / "probe_key.json").read_text())["answer_key"]
    rows = []
    for judging in sorted(out_root.glob("judging-*")):
        for slot_dir in sorted((judging / "responses").glob("slot-*")):
            for f in sorted(slot_dir.glob("B*.json")):
                r = json.loads(f.read_text())
                rows.append(
                    {
                        "judging": judging.name,
                        "stimulus": key[r["presentation_id"]],
                        "status": r["status"],
                        "verdict": r.get("parsed"),
                    }
                )
    return rows


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="detection_probe")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--out", required=True, type=Path)
    b.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    b.add_argument("--deck-dir", type=Path, default=None)
    j = sub.add_parser("judge")
    j.add_argument("--root", required=True, type=Path)
    j.add_argument("--vendor", required=True)
    r = sub.add_parser("report")
    r.add_argument("--root", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.cmd == "build":
        built = build_probe_deck(args.out, db_path=args.db_path, deck_dir=args.deck_dir)
        print(json.dumps(built, indent=2))
    elif args.cmd == "judge":
        print(json.dumps(judge_probe(args.root, args.vendor), indent=2))
    else:
        print(json.dumps(report(args.root), indent=2))


if __name__ == "__main__":
    main()
