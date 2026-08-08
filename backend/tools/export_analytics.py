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

T2 (flywheel S3): `decisions` rows also carry `engine_node_key` and
`hand_class_bucket` (both nullable; NULL on `action='post'` rows). These are
a deliberate, narrow exception to "derivations belong downstream in dbt" —
the determinism guard needs a grouping key the engine itself would compute,
so `engine_node_key` reuses the domain's pure `postflop_node_key` (postflop)
via read-only import, or an export-side-only preflop facing-state label
(never new `backend/app/domain/` logic). `hand_class_bucket` is an
export-side-only preflop hole-card bucket for preflop rows; postflop rows
reuse the domain's pure `strength_bucket` (read-only import) — see the
`docs/ai-dlc/reports/t2-export-report.md` encoding note for the exact
"<strength>|<draw>" string format.

Producer-side contract check (ADVISORY — the consumer's ingestion gate is
the authoritative one): after writing, the script runs `datacontract test`
against the vendored copy of the consumer's ODCS contract
(tools/poker_events.odcs.yaml) if datacontract-cli is on PATH, and warns
(without failing the export) when it isn't installed. Keep the vendored
contract in sync with the consumer repo's contracts/poker_events.odcs.yaml.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from app.domain.archetypes import VillainType
from app.domain.content.models import PersonaPack
from app.domain.personas import load_persona_packs
from app.domain.personas_postflop import strength_bucket
from app.domain.spot import ActionType, PlayerStatus, Street
from app.domain.table.deck import deal_hand
from app.domain.table.engine import apply, legal_actions, settle, start_hand
from app.domain.table.play import bot_decision
from app.domain.table.sizing import last_aggressor_position, postflop_node_key
from tools import counterfactual
from tools.counterfactual import CounterfactualConfigError

_ODCS_PATH = Path(__file__).resolve().parent / "poker_events.odcs.yaml"
_ODCS_VERSION_RE = re.compile(r"^version:\s*(\S+)\s*$", re.MULTILINE)


def _odcs_contract_version(path: Path = _ODCS_PATH) -> str:
    """Derive the ODCS contract version from the vendored yaml's top-level
    `version:` field (S4 T2 fix #2), so the constant below can never drift
    silently from the file it names. No YAML parser dependency: the ODCS
    top-level `version:` key is unindented and unique in this file (verified
    by test), so a plain regex read is exact and dependency-free — `pyyaml`
    is not installed in this venv."""
    match = _ODCS_VERSION_RE.search(path.read_text(encoding="utf-8"))
    if match is None:
        raise RuntimeError(f"{path}: no top-level `version:` field found")
    return match.group(1)


CONTRACT_VERSION = _odcs_contract_version()  # derived from poker_events.odcs.yaml
SCHEMA_PATH_VERSION = "v1"  # data-path major; bumps only on a breaking change
STACKS_BB = 100.0  # every seat starts each hand at 100bb (reset per hand)
_CONFIG_HASH_RE = re.compile(r"[0-9a-f]{64}")

# F1 (flywheel S6 T2): mirrors the live table's re-buy spread EXACTLY
# (`app/services/sim_session.py:148-149` `_BUYIN_MIN_BB`/`_BUYIN_MAX_BB`) —
# same bounds, same integer-cent granularity, same per-hand-seed-derived
# stream. Kept as a distinct pair of constants (not imported from
# sim_session, a web-layer module the domain-pure export tool must not
# depend on) — cross-checked against the live values by a conformance test.
_BUYIN_MIN_BB = 95.0
_BUYIN_MAX_BB = 105.0


def _draw_buyin_targets(hand_seed: int) -> list[float]:
    """Nine per-seat buy-in targets (seat order 0..8), mirroring
    `sim_session._rebuy_seats`: integer cents drawn uniform on
    `[_BUYIN_MIN_BB, _BUYIN_MAX_BB]` from a distinct per-hand RNG stream
    (`hand_seed ^ 1`, matching sim_session.py:220-255's `seed ^ 1`
    derivation from the hand's OWN seed — never the run's global RNG
    mid-stream) so the same hand seed reproduces the same targets
    regardless of how many hands preceded it."""
    lo, hi = int(_BUYIN_MIN_BB * 100), int(_BUYIN_MAX_BB * 100)
    rng = random.Random(hand_seed ^ 1)
    return [rng.randint(lo, hi) / 100 for _ in range(9)]

# Default lineup mirrors the persona test harness: the 6 personas in sorted
# order, wrapped around 9 seats. The button rotates hand-by-hand so every
# persona plays every position.
DEFAULT_LINEUP = sorted(v.value for v in VillainType)

# T2 broadway ranks for the export-side preflop hand_class_bucket (deterministic,
# export-only — never domain logic).
_BROADWAY_RANKS = {"T", "J", "Q", "K", "A"}


def _preflop_facing_label(action_history) -> str:
    """Export-side facing-state label for `engine_node_key` on preflop rows.

    Derived from PUBLIC state only (`action_history`) — deliberately NOT a
    reuse of `app.domain.table.play._preflop_facing` (private, domain-owned);
    this is an independent export-tool derivation per spec A2 / ticket T2.
    Coarser than the domain's internal facing split (3bet and 4bet+ both
    collapse to "vs_3bet_plus") because this label is a determinism-guard
    grouping key, not a policy input.
    """
    raises = [
        h for h in action_history
        if h.street is Street.PREFLOP and h.action == ActionType.RAISE
    ]
    if not raises:
        limped = any(
            h.action == ActionType.CALL for h in action_history
            if h.street is Street.PREFLOP
        )
        return "vs_limpers" if limped else "unopened"
    return "vs_raise" if len(raises) == 1 else "vs_3bet_plus"


def _hand_class_bucket(hole_cards: list[str]) -> str:
    """Coarse, deterministic preflop hole-card bucket for `hand_class_bucket`.

    Export-tool-only scheme (pair / suited-ace / suited-broadway /
    offsuit-broadway / other); no existing domain hand-class label is
    available to reuse for this purpose. Priority order below resolves
    overlapping cases (e.g. AKs is suited-ace, not suited-broadway)."""
    r1, s1 = hole_cards[0][0], hole_cards[0][1]
    r2, s2 = hole_cards[1][0], hole_cards[1][1]
    suited = s1 == s2
    if r1 == r2:
        return "pair"
    if suited and "A" in (r1, r2):
        return "suited-ace"
    if suited and r1 in _BROADWAY_RANKS and r2 in _BROADWAY_RANKS:
        return "suited-broadway"
    if not suited and r1 in _BROADWAY_RANKS and r2 in _BROADWAY_RANKS:
        return "offsuit-broadway"
    return "other"


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
                  persona_by_seat: dict[int, str], packs,
                  stacks_bb: list[float] | None = None) -> dict:
    """One full production-policy playout. Returns the raw rows for all
    three tables. Deliberately thin: derivations that SQL can do (facing,
    aggression, VPIP flags...) belong downstream in dbt, not here.

    `stacks_bb`: per-seat starting stacks (seat order 0..8). Defaults to
    the flat 100bb reset (F1 default path); `run_export`'s `--buyin-spread`
    path supplies `_draw_buyin_targets(hand_seed)` instead."""
    stacks_bb = stacks_bb if stacks_bb is not None else [STACKS_BB] * 9
    state = start_hand(deal_hand(random.Random(hand_seed)), button_seat,
                       stacks_bb=stacks_bb)
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
            # T2: forced blind posts carry no node key / hand-class bucket —
            # they are excluded from the determinism-guard contexts.
            "engine_node_key": None, "hand_class_bucket": None,
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
        # T2: compute the two new columns from the PRE-decision public state,
        # same inputs the domain uses internally (read-only reuse of the
        # existing pure functions — no new domain logic, nothing added to
        # backend/app/domain/).
        if state.street is Street.PREFLOP:
            engine_node_key = _preflop_facing_label(state.action_history)
            hand_class_bucket = _hand_class_bucket(seat_state.hole_cards)
        else:
            legal = legal_actions(state)
            is_aggressor = (
                last_aggressor_position(state.action_history) == seat_state.position
            )
            engine_node_key = postflop_node_key(
                state.board, legal, is_aggressor=is_aggressor)
            # Postflop hand_class_bucket: read-only reuse of the domain's
            # pure `strength_bucket` (made-hand ladder + draw category).
            # Encoded as "<strength>|<draw>" (e.g. "top_pair|weak",
            # "monster|none") — see docs/ai-dlc/reports/t2-export-report.md
            # for the full enum-value list and rationale.
            made, draw = strength_bucket(seat_state.hole_cards, state.board)
            hand_class_bucket = f"{made.value}|{draw.value}"
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
            "engine_node_key": engine_node_key,
            "hand_class_bucket": hand_class_bucket,
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
            "starting_stack_bb": stacks_bb[s.seat],
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
               lineup: list[str] | None = None,
               packs: dict[VillainType, PersonaPack] | None = None,
               config_hash: str | None = None,
               buyin_spread: bool = False) -> dict:
    """T2 (flywheel S4): `packs`/`config_hash` travel together — both given
    (sweep path: already-validated in-memory pack overlays + their §c.6
    hash), or both omitted (default path: simulate the RAW as-loaded packs
    UNCHANGED, and compute `config_hash` via
    `counterfactual.baseline_config_hash()` as a side-channel so the baseline
    packs fed to `play_one_hand` are never canonicalized — see spec `Design
    rulings`, "The default (no-config) export path simulates the RAW
    as-loaded packs").

    `buyin_spread` (F1, flywheel S6 T2): when True, every seat re-buys to a
    fresh per-hand target drawn by `_draw_buyin_targets` (mirrors the live
    table's `_rebuy_seats` exactly) instead of the flat 100bb reset; `run_id`
    gains a `-bspread-` mode token and the manifest records the mode +
    bounds. Default False: output is byte-identical (canonical comparison,
    per the S4 convention) to the pre-flag export — no new manifest fields,
    no run_id change."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    if (packs is None) != (config_hash is None):
        raise ValueError(
            "run_export: `packs` and `config_hash` must both be given (sweep "
            "path) or both omitted (default path) — mixed args are an error"
        )
    if config_hash is not None and not _CONFIG_HASH_RE.fullmatch(config_hash):
        raise ValueError(
            f"run_export: config_hash {config_hash!r} is not 64 lowercase hex "
            f"chars — a malformed hash would otherwise be baked into run_id "
            f"and every exported row, failing only later at the analytics gate"
        )

    lineup = lineup or DEFAULT_LINEUP
    persona_by_seat = {i: lineup[i % len(lineup)] for i in range(9)}
    if packs is None:
        packs = load_persona_packs()
        config_hash = counterfactual.baseline_config_hash(packs)
    rng = random.Random(seed)
    start = time.monotonic()
    # KNOWN WART (out of scope for T2): run_id still ignores `lineup`, so two
    # runs with the same (seed, n_hands, config_hash) but different lineups
    # collide on run_id/hand_id. S1's pinned per-persona counts reference the
    # old format — the config-hash suffix below is new; the lineup component
    # remains a disclosed wart.
    mode_token = "-bspread" if buyin_spread else ""
    run_id = f"run-s{seed}-n{n_hands}{mode_token}-c{config_hash[:12]}"
    exported_at = datetime.now(UTC).isoformat(timespec="seconds")

    hands, seats, decisions = [], [], []
    for i in range(n_hands):
        hand_id = f"{run_id}-h{i:07d}"
        hand_seed = rng.randrange(1_000_000_000)
        stacks_bb = _draw_buyin_targets(hand_seed) if buyin_spread else None
        res = play_one_hand(rng, hand_seed, i % 9,
                            persona_by_seat, packs, stacks_bb=stacks_bb)
        hands.append({"hand_id": hand_id, "run_id": run_id, "hand_no": i,
                      **res["hand"], "exported_at": exported_at})
        for r in res["seats"]:
            seats.append({"hand_id": hand_id, **r, "exported_at": exported_at})
        for r in res["decisions"]:
            decisions.append({"hand_id": hand_id, **r, "exported_at": exported_at})

    out_dir.mkdir(parents=True, exist_ok=True)
    success = out_dir / "_SUCCESS"
    success.unlink(missing_ok=True)  # invalidate the batch before rewriting it
    (out_dir / "_TIMING.json").unlink(missing_ok=True)
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
        "config_hash": config_hash,
        "exported_at": exported_at,
        "row_counts": row_counts,
    }
    # F1: spread-only fields are added ONLY when the flag is set, so the
    # default path's manifest shape is byte-identical to pre-change.
    if buyin_spread:
        manifest["buyin_spread"] = True
        manifest["buyin_min_bb"] = _BUYIN_MIN_BB
        manifest["buyin_max_bb"] = _BUYIN_MAX_BB

    wall_seconds = time.monotonic() - start
    timing = {
        "schema_version": "1.0.0",
        "wall_seconds": wall_seconds,
        "n_hands": n_hands,
        "seed": seed,
        "run_id": run_id,
    }
    if (timing["n_hands"], timing["seed"], timing["run_id"]) != (
        manifest["n_hands"], manifest["seed"], manifest["run_id"]
    ):
        raise RuntimeError("_TIMING.json/_SUCCESS n_hands/seed/run_id mismatch")
    # Written BEFORE _SUCCESS: the scorer's throughput check (§a.5 rule 5(a))
    # reads this file, and _SUCCESS must remain the LAST file written.
    (out_dir / "_TIMING.json").write_text(json.dumps(timing, indent=2) + "\n")
    # Written LAST: consumers must refuse to read a directory without it.
    success.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def _advisory_contract_test(out_dir: Path) -> None:
    """Producer-side `datacontract test` (advisory): warn, never fail the
    export. The consumer repo's ingestion gate is the authoritative check."""
    import shutil
    import tempfile

    contract = Path(__file__).resolve().parent / "poker_events.odcs.yaml"
    if shutil.which("datacontract") is None:
        print("ADVISORY: datacontract-cli not on PATH — producer-side contract "
              "check skipped (pip install 'datacontract-cli[duckdb,parquet]').")
        return
    # The vendored contract's server paths are consumer-repo-relative; point a
    # temp copy at the actual export directory instead.
    text = contract.read_text().replace(
        "./data/raw/v1/sample/{model}.parquet",
        f"{out_dir.resolve()}/{{model}}.parquet",
    )
    with tempfile.NamedTemporaryFile("w", suffix=".odcs.yaml", delete=False) as f:
        f.write(text)
        tmp = f.name
    res = subprocess.run(
        ["datacontract", "test", tmp, "--server", "local-sample"])
    Path(tmp).unlink(missing_ok=True)
    if res.returncode != 0:
        print("ADVISORY: export does NOT conform to the vendored contract — "
              "the consumer's ingestion gate will reject this batch.")
    else:
        print("Producer-side contract check passed.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hands", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, required=True,
                    help="target directory, e.g. <analytics-repo>/data/raw/v1/sample")
    ap.add_argument("--skip-contract-test", action="store_true",
                    help="skip the advisory producer-side datacontract test")
    ap.add_argument("--lineup", type=str, default=None,
                    help="comma-separated persona names for the 9 seats "
                         "(wraps if fewer than 9; default: DEFAULT_LINEUP)")
    ap.add_argument("--config", type=Path, default=None,
                    help="path to a §c counterfactual-config JSON file "
                         "(backend/tools/counterfactual.py); validated and "
                         "overlaid onto the baseline packs before export. "
                         "Omit for the default (raw baseline packs) path.")
    ap.add_argument("--buyin-spread", action="store_true",
                    help="F1: every seat re-buys to a fresh per-hand target "
                         "on [95,105]bb, mirroring the live table's re-buy "
                         "exactly, instead of the flat 100bb reset. Adds a "
                         "-bspread- run_id token + manifest fields; default "
                         "path is unaffected.")
    args = ap.parse_args()
    lineup = args.lineup.split(",") if args.lineup else None
    packs = config_hash = None
    if args.config is not None:
        try:
            validated = counterfactual.load_config(args.config)
        except CounterfactualConfigError as exc:
            print(f"ERROR: {args.config}: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        packs, config_hash = validated.packs, validated.config_hash
    manifest = run_export(args.hands, args.seed, args.out, lineup=lineup,
                          packs=packs, config_hash=config_hash,
                          buyin_spread=args.buyin_spread)
    print(json.dumps(manifest, indent=2))
    if not args.skip_contract_test:
        _advisory_contract_test(args.out)


if __name__ == "__main__":
    main()
