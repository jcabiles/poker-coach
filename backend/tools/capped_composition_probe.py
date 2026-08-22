"""Capped-versus-uncapped composition probe (flywheel slice 3, ticket S3-T3).

**Bottom line: this measures how the villain bots' betting range is composed at
decisions where their stack stops them making their own biggest bet size, both
RAW and NORMALISED against the theory contract's bluff-share formula at the size
actually wagered. It measures. It does not decompose the gap it finds into its
causes, and §"What this probe does NOT measure" below says so explicitly,
because an earlier draft of this ticket read a raw gap as evidence of a policy
defect and was wrong to.**

Why it exists. S3-T3's acceptance criterion 1 asked whether capped-node
composition moves toward the uncapped norm, and nothing in this repository
measured that: not the persona band harness, not the de-robotization gate, not
the analytics export. The only prior implementation lived in a design dossier
that modified no repository file. See
`docs/ai-dlc/contracts/flywheel-slice3-t3-valueside.md` §2. S3-T3's own lever was
built, measured and WITHDRAWN (see `docs/ai-dlc/research/slice3-calldown/
t3-report.md`); this instrument is what the ticket ships instead.

Terms used here, each glossed once:

- **Stack-to-pot ratio (SPR)** — the acting seat's remaining stack divided by
  the pot before it acts.
- **Cap-exposed decision** — a decision where the seat cannot wager its own
  largest authored pot-fraction, because the legal bracket's maximum is below
  it. On an unopened street the bracket maximum is the seat's whole stack, so
  this is exactly `SPR < largest authored size`.
- **Bluff cell** — an air or ace-high hand with no draw. Those hands take the
  sampler's exact-frequency bluff branch and never read the made-value table.
- **The identity** — the theory contract §3 bluff-share formula `s / (1 + 2s)`,
  where `s` is the wager as a fraction of the pot: the share of a bettor's
  betting range that should be bluffs at that size. **Smaller wagers warrant a
  SMALLER bluff share.** That is why the raw share below is not readable on its
  own: capped wagers are smaller by construction, so a lower raw bluff share at
  capped decisions is partly what the identity ASKS for.
- **The action-probability vector** — the normalized weights the sampler passes
  to its action draw. It is read with the capture-rng pattern from
  `backend/tests/node_trace.py`: the wrapper records the weights of the FIRST
  `choices()` call and delegates every call onward, so reading costs nothing and
  disturbs nothing.

Two statistics, and the second is the one to quote:

1. **RAW bluff-cell share** of the betting range, capped versus uncapped. Easy
   to compute and easy to misread, for the reason in the identity gloss above.
2. **NORMALISED share**, `realised ÷ target`, where the target is the identity
   evaluated at the pot-fraction each wager was ACTUALLY made at, averaged over
   the wagers in that population. This is the figure that is comparable between
   capped and uncapped decisions, because it has divided out the size difference
   that makes the raw figures incomparable.

What this probe does NOT measure, stated so nobody reads more out of it than is
there. It does not separate the three things that could make the normalised
figures differ: (a) the size the wager was made at, which the normalisation
handles; (b) ARRIVAL — which hands the seat actually holds at a capped decision,
`π` in the identity's numerator and denominator, which is a property of how the
hand got there and not of any policy this module can see; and (c) POLICY — the
conditional probability of betting given the hand. Separating (b) from (c) needs
a `π`-by-node table this probe does not build. **A gap reported here is a gap,
not a defect.**

Usage (from backend/):
    PYTHONPATH=. python -m tools.capped_composition_probe --hands 20000 \
        --seeds 601,20260817,20260818
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict

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
_CLASSES = ("bluff_cell", "draw_cell", "made_value")


def identity_target(frac: float) -> float:
    """Theory contract §3: the share of a betting range that should be bluffs at
    a wager of `frac` times the pot. Half-pot 0.25, pot 0.333, twice pot 0.40."""
    return frac / (1.0 + 2.0 * frac)


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


def _realised_fraction(decision, by_kind, pot_bb: float, current_bet_to: float) -> float | None:
    """The pot-fraction the wager was ACTUALLY made at, inverting the sampler's
    two sizing formulas. `None` when the action is not a wager."""
    if decision.size_bb is None:
        return None
    if decision.action is ActionType.BET:
        return decision.size_bb / pot_bb
    if decision.action is ActionType.RAISE:
        call = by_kind.get(ActionType.CALL)
        to_call = call.min_bb if call is not None and call.min_bb is not None else 0.0
        denom = pot_bb + to_call
        return (decision.size_bb - current_bet_to) / denom if denom > 0 else None
    return None


class _Probe:
    def __init__(self) -> None:
        # (shape, cap_exposed, hand_class, action) -> summed probability
        self.mass: dict[tuple, float] = defaultdict(float)
        # (shape, cap_exposed, hand_class) -> node count
        self.nodes: dict[tuple, int] = defaultdict(int)
        # realised wagers: (cap_exposed, hand_class) -> count, and summed target
        self.wagers: dict[tuple, int] = defaultdict(int)
        self.target_sum: dict[bool, float] = defaultdict(float)
        self.wager_total: dict[bool, int] = defaultdict(int)
        self.deep_nodes = 0

    def merge(self, other: _Probe) -> None:
        for store in ("mass", "nodes", "wagers", "target_sum", "wager_total"):
            for k, v in getattr(other, store).items():
                getattr(self, store)[k] += v
        self.deep_nodes += other.deep_nodes

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
        current_bet_to = kw.get("current_bet_to", 0.0)
        f_max = _max_wagerable_fraction(by_kind, pot_bb, current_bet_to)
        if f_max is None:
            return
        shape = _node_shape(by_kind)
        bucket, draw = strength_bucket(hole, board)
        klass = _hand_class(bucket, draw)
        capped = f_max < _largest_authored_size(pack.postflop) - 1e-9
        key = (shape, capped, klass)
        self.nodes[key] += 1
        if stack_bb / pot_bb >= pack.postflop.spr_commit:
            self.deep_nodes += 1

        # Zero-sampling-variance leg: the exact action distribution at this node.
        cap = _CaptureRng(random.Random(0))
        original(pack, hole, board, legal, pot_bb, stack_bb, opponents, cap, **kw)
        for action, p in zip(cap.population, cap.weights, strict=True):
            self.mass[(*key, action)] += p

        # Realised-wager leg: the composition statistic, and the identity target
        # at the size the wager was actually made at.
        frac = _realised_fraction(decision, by_kind, pot_bb, current_bet_to)
        if frac is not None and frac > 0.0:
            self.wagers[(capped, klass)] += 1
            self.wager_total[capped] += 1
            self.target_sum[capped] += identity_target(frac)


def _composition(probe: _Probe, capped: bool) -> dict:
    """Raw and target-normalised composition of the realised betting range."""
    n = probe.wager_total[capped]
    out = {"wagers": n}
    for klass in _CLASSES:
        out[klass + "_share"] = (probe.wagers[(capped, klass)] / n) if n else 0.0
    target = (probe.target_sum[capped] / n) if n else 0.0
    out["identity_target_at_realised_size"] = target
    out["normalised_bluff_share"] = (out["bluff_cell_share"] / target) if target else 0.0
    return out


def _headline(probe: _Probe) -> dict:
    out = {"capped": _composition(probe, True),
           "uncapped": _composition(probe, False),
           "deep_nodes": probe.deep_nodes}
    for field in ("bluff_cell_share", "normalised_bluff_share"):
        u = out["uncapped"][field]
        out["ratio_" + field] = (out["capped"][field] / u) if u else 0.0
    return out


def _detail(probe: _Probe) -> dict:
    detail = {}
    for (shape, capped, klass), n in sorted(probe.nodes.items()):
        tag = f"{shape}|{'capped' if capped else 'uncapped'}|{klass}"
        detail[tag] = {
            "nodes": n,
            "expected_mix": {a.value: probe.mass[(shape, capped, klass, a)] / n
                             for a in _ACTIONS},
        }
    return detail


def run(hands: int, seeds: list[int]) -> dict:
    packs = load_persona_packs()
    persona_by_seat = {i: RATIFIED_LINEUP[i] for i in range(9)}
    pooled = _Probe()
    per_seed = []
    for seed in seeds:
        probe = _Probe()
        original = play_mod.sample_postflop_decision
        play_mod.sample_postflop_decision = probe.wrap(original)
        try:
            rng = random.Random(seed)
            for i in range(hands):
                hand_seed = rng.randrange(1_000_000_000)
                play_one_hand(rng, hand_seed, i % 9, persona_by_seat, packs)
        finally:
            play_mod.sample_postflop_decision = original
        pooled.merge(probe)
        per_seed.append({"seed": seed, **_headline(probe)})
    return {"hands_per_seed": hands, "seeds": seeds, "per_seed": per_seed,
            "pooled": _headline(pooled), "pooled_detail": _detail(pooled)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hands", type=int, default=4000)
    ap.add_argument("--seeds", default="601,20260817,20260818")
    ap.add_argument("--out", default=None, help="write the full JSON here")
    args = ap.parse_args(argv)
    seeds = [int(s) for s in args.seeds.split(",")]
    result = run(args.hands, seeds)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(result, indent=2, sort_keys=True))
    p = result["pooled"]
    print(f"hands/seed={args.hands} seeds={seeds}")
    for tag in ("capped", "uncapped"):
        c = p[tag]
        print(f"  {tag:8s} wagers={c['wagers']:7d}  raw bluff share={c['bluff_cell_share']:.4f}"
              f"  identity target at realised size={c['identity_target_at_realised_size']:.4f}"
              f"  NORMALISED={c['normalised_bluff_share']:.4f}")
    print(f"  capped/uncapped   raw ratio={p['ratio_bluff_cell_share']:.4f}"
          f"   NORMALISED ratio={p['ratio_normalised_bluff_share']:.4f}")
    print(f"  nodes at or above spr_commit: {p['deep_nodes']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
