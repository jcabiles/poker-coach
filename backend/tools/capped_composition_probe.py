"""Capped-versus-uncapped composition probe (flywheel slice 3, ticket S3-T3).

**Bottom line: this measures whether the villain bots' betting range is
composed differently at decisions where their stack stops them making their own
biggest bet size, and how the S3-T3 stack-to-pot value damp changes that. The
primary comparison carries ZERO sampling variance, because both arms are read
at the SAME node from the same seeded playout.**

Why it exists. S3-T3's acceptance criterion 1 asks whether "pooled capped-node
composition moves toward the uncapped norm", and nothing in this repository
measured that: not the persona band harness, not the de-robotization gate, not
the analytics export. The only prior implementation lived in a design dossier
that modified no repository file. See
`docs/ai-dlc/contracts/flywheel-slice3-t3-valueside.md` §2 and
`docs/ai-dlc/research/slice3-calldown/t3-preregistration.md` §1.

Terms used here, each glossed once:

- **Stack-to-pot ratio (SPR)** — the acting seat's remaining stack divided by
  the pot before it acts.
- **Cap-exposed decision** — a decision where the seat cannot wager its own
  largest authored pot-fraction, because the legal bracket's maximum is below
  it. On an unopened street the bracket maximum is the seat's whole stack, so
  this is exactly `SPR < largest authored size`.
- **Bluff cell** — an air or ace-high hand with no draw. Those hands take the
  sampler's exact-frequency bluff branch and never read the made-value table,
  so the S3-T3 lever cannot reach them.
- **The action-probability vector** — the normalized weights the sampler passes
  to its action draw. It is read with the capture-rng pattern from
  `backend/tests/node_trace.py`: the wrapper records the weights of the FIRST
  `choices()` call and delegates every call onward, so reading costs nothing
  and disturbs nothing.

How the two arms are produced. The playout runs once per seed under the LIVE
engine. At every postflop decision the probe re-invokes the sampler twice on a
throwaway RNG — once with the value damp's floor forced to 1.0 (the lever off,
which is the pre-S3-T3 engine exactly, since a multiplier of 1.0 is the identity
in floating point) and once at the shipped floor. Neither re-invocation touches
the live RNG, so the playout itself is unchanged by being measured. The
difference between the two vectors at a node is the policy's exact response, not
a sample of it.

What still carries noise: WHICH nodes appear. That is why every statistic below
is pooled across seeds and the per-seed spread is printed, never a single seed.

Usage (from backend/):
    PYTHONPATH=. python -m tools.capped_composition_probe --hands 4000 \
        --seeds 601,20260817,20260818
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict

from app.domain import personas_postflop
from app.domain.personas import load_persona_packs
from app.domain.personas_postflop import DrawCategory, StrengthBucket, strength_bucket
from app.domain.spot import ActionType
from app.domain.table import play as play_mod
from tools.export_analytics import play_one_hand

# The ratified nine-seat lineup every flywheel measurement uses.
RATIFIED_LINEUP = [
    "tag", "tag", "calling_station", "tag", "passive_fish",
    "lag", "passive_fish", "nit", "maniac",
]

_ACTIONS = (ActionType.CHECK, ActionType.BET, ActionType.CALL,
            ActionType.RAISE, ActionType.FOLD)


class _CaptureRng:
    """Records the first `choices()` call's weights, delegates everything."""

    def __init__(self, inner: random.Random) -> None:
        self._rng = inner
        self.population: list | None = None
        self.weights: list[float] | None = None

    def choices(self, population, weights, k=1):  # noqa: ANN001 — rng protocol
        if self.population is None:
            self.population = list(population)
            self.weights = list(weights)
        return self._rng.choices(population, weights=weights, k=k)

    def __getattr__(self, name):  # noqa: ANN001 — delegate the rest of the protocol
        return getattr(self._rng, name)


def _largest_authored_size(pf) -> float:
    """The biggest pot-fraction this persona can ever author, over the flat
    sizing distribution and every node-specific override."""
    keys = [float(k) for k in pf.sizing]
    for dist in (pf.sizing_by_node or {}).values():
        keys.extend(float(k) for k in dist)
    return max(keys)


def _hand_class(bucket, draw) -> str:
    if bucket in (StrengthBucket.AIR, StrengthBucket.ACE_HIGH):
        return "bluff_cell" if draw is DrawCategory.NONE else "draw_cell"
    return "made_value"


def _node_shape(by_kind) -> str:
    if ActionType.FOLD in by_kind:
        return "facing"
    if ActionType.BET in by_kind:
        return "unopened_bet"
    return "option_raise"


def _max_wagerable_fraction(by_kind, pot_bb: float, current_bet_to: float) -> float | None:
    """The largest pot-fraction the seat could actually wager here, inverting
    the sampler's own sizing formula. Bracket fields are read HERE, in a probe
    outside the domain — never inside the merit computation, which is what
    PR #199's parity guard forbids."""
    bet = by_kind.get(ActionType.BET)
    if bet is not None and bet.max_bb is not None:
        return bet.max_bb / pot_bb
    raise_la = by_kind.get(ActionType.RAISE)
    if raise_la is not None and raise_la.max_bb is not None:
        call = by_kind.get(ActionType.CALL)
        to_call = call.min_bb if call is not None and call.min_bb is not None else 0.0
        denom = pot_bb + to_call
        return (raise_la.max_bb - current_bet_to) / denom if denom > 0 else None
    return None


class _Probe:
    def __init__(self, shipped_floor: float) -> None:
        self.shipped_floor = shipped_floor
        # (arm, shape, cap_exposed, hand_class, action) -> summed probability
        self.mass: dict[tuple, float] = defaultdict(float)
        # (shape, cap_exposed, hand_class) -> node count
        self.nodes: dict[tuple, int] = defaultdict(int)
        # realized action counts of the LIVE arm
        self.realized: dict[tuple, int] = defaultdict(int)
        self.max_abs_deep_delta = 0.0
        self.deep_nodes = 0

    def wrap(self, original):
        def wrapper(pack, hole, board, legal, pot_bb, stack_bb, opponents, rng, **kw):
            decision = original(pack, hole, board, legal, pot_bb, stack_bb,
                                opponents, rng, **kw)
            self._record(original, pack, hole, board, legal, pot_bb, stack_bb,
                         opponents, kw, decision)
            return decision
        return wrapper

    def _record(self, original, pack, hole, board, legal, pot_bb, stack_bb,
                opponents, kw, decision) -> None:
        if pot_bb <= 0:
            return
        by_kind = {la.action: la for la in legal}
        shape = _node_shape(by_kind)
        bucket, draw = strength_bucket(hole, board)
        klass = _hand_class(bucket, draw)
        f_max = _max_wagerable_fraction(by_kind, pot_bb, kw.get("current_bet_to", 0.0))
        if f_max is None:
            return
        capped = f_max < _largest_authored_size(pack.postflop) - 1e-9
        key = (shape, capped, klass)
        self.nodes[key] += 1
        self.realized[(*key, decision.action)] += 1

        vectors = {}
        saved = personas_postflop._VALUE_SPR_FLOOR
        try:
            for arm, floor in (("before", 1.0), ("after", self.shipped_floor)):
                personas_postflop._VALUE_SPR_FLOOR = floor
                cap = _CaptureRng(random.Random(0))
                original(pack, hole, board, legal, pot_bb, stack_bb, opponents,
                         cap, **kw)
                vectors[arm] = dict(zip(cap.population, cap.weights, strict=True))
        finally:
            personas_postflop._VALUE_SPR_FLOOR = saved

        for arm, vec in vectors.items():
            for action, p in vec.items():
                self.mass[(arm, *key, action)] += p
        # Byte-identity watch: at or above the persona's spr_commit the lever
        # must be the exact identity, so the two vectors must agree bit for bit.
        if stack_bb / pot_bb >= pack.postflop.spr_commit:
            self.deep_nodes += 1
            for action in vectors["before"]:
                delta = abs(vectors["after"][action] - vectors["before"][action])
                self.max_abs_deep_delta = max(self.max_abs_deep_delta, delta)


def _mix(probe: _Probe, arm: str, shape: str, capped: bool, klass: str) -> dict[str, float]:
    n = probe.nodes[(shape, capped, klass)]
    if not n:
        return {}
    return {a.value: probe.mass[(arm, shape, capped, klass, a)] / n for a in _ACTIONS}


def run(hands: int, seeds: list[int]) -> dict:
    packs = load_persona_packs()
    persona_by_seat = {i: RATIFIED_LINEUP[i] for i in range(9)}
    shipped_floor = personas_postflop._VALUE_SPR_FLOOR
    per_seed = []
    pooled = _Probe(shipped_floor)
    for seed in seeds:
        probe = _Probe(shipped_floor)
        original = play_mod.sample_postflop_decision
        play_mod.sample_postflop_decision = probe.wrap(original)
        try:
            rng = random.Random(seed)
            for i in range(hands):
                hand_seed = rng.randrange(1_000_000_000)
                play_one_hand(rng, hand_seed, i % 9, persona_by_seat, packs)
        finally:
            play_mod.sample_postflop_decision = original
        for store in ("mass", "nodes", "realized"):
            for k, v in getattr(probe, store).items():
                getattr(pooled, store)[k] += v
        pooled.deep_nodes += probe.deep_nodes
        pooled.max_abs_deep_delta = max(pooled.max_abs_deep_delta,
                                        probe.max_abs_deep_delta)
        per_seed.append({"seed": seed, **_headline(probe)})
    return {"hands_per_seed": hands, "seeds": seeds,
            "shipped_floor": shipped_floor,
            "per_seed": per_seed, "pooled": _headline(pooled),
            "pooled_detail": _detail(pooled)}


def _bet_shares(probe: _Probe, arm: str, capped: bool) -> dict[str, float]:
    """Composition of the UNOPENED betting range: each hand class's share of
    the expected bets made at cap-exposed (or not) decisions."""
    totals = {}
    for klass in ("bluff_cell", "draw_cell", "made_value"):
        n = probe.nodes[("unopened_bet", capped, klass)]
        totals[klass] = probe.mass[(arm, "unopened_bet", capped, klass, ActionType.BET)]
        totals[klass + "_nodes"] = n
    bets = sum(totals[k] for k in ("bluff_cell", "draw_cell", "made_value"))
    out = {"expected_bets": bets}
    for klass in ("bluff_cell", "draw_cell", "made_value"):
        out[klass + "_share"] = totals[klass] / bets if bets else 0.0
        out[klass + "_nodes"] = totals[klass + "_nodes"]
    return out


def _headline(probe: _Probe) -> dict:
    out = {}
    for capped in (True, False):
        tag = "capped" if capped else "uncapped"
        for arm in ("before", "after"):
            out[f"{tag}_{arm}"] = _bet_shares(probe, arm, capped)
    for arm in ("before", "after"):
        c = out[f"capped_{arm}"]["bluff_cell_share"]
        u = out[f"uncapped_{arm}"]["bluff_cell_share"]
        out[f"bluff_share_ratio_{arm}"] = c / u if u else 0.0
    out["deep_nodes"] = probe.deep_nodes
    out["max_abs_deep_delta"] = probe.max_abs_deep_delta
    return out


def _detail(probe: _Probe) -> dict:
    detail = {}
    for (shape, capped, klass), n in sorted(probe.nodes.items(),
                                            key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])):
        tag = f"{shape}|{'capped' if capped else 'uncapped'}|{klass}"
        detail[tag] = {
            "nodes": n,
            "before": _mix(probe, "before", shape, capped, klass),
            "after": _mix(probe, "after", shape, capped, klass),
            "realized": {a.value: probe.realized[(shape, capped, klass, a)] for a in _ACTIONS},
        }
    return detail


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hands", type=int, default=4000)
    ap.add_argument("--seeds", default="601,20260817,20260818")
    ap.add_argument("--out", default=None, help="write the full JSON here")
    args = ap.parse_args(argv)
    seeds = [int(s) for s in args.seeds.split(",")]
    result = run(args.hands, seeds)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    p = result["pooled"]
    print(f"hands/seed={args.hands} seeds={seeds} floor={result['shipped_floor']}")
    for tag in ("capped", "uncapped"):
        for arm in ("before", "after"):
            b = p[f"{tag}_{arm}"]
            print(f"  {tag:8s} {arm:6s} bluff_share={b['bluff_cell_share']:.4f} "
                  f"made_share={b['made_value_share']:.4f} "
                  f"expected_bets={b['expected_bets']:.1f}")
    print(f"  bluff-share ratio capped/uncapped: "
          f"before={p['bluff_share_ratio_before']:.4f} "
          f"after={p['bluff_share_ratio_after']:.4f}")
    print(f"  deep (spr>=spr_commit) nodes={p['deep_nodes']} "
          f"max|delta|={p['max_abs_deep_delta']:.3e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
