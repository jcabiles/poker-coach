"""Late-street bet lever probe — the zero-variance paired instrument (S3-T5).

**Bottom line: this reads the bots' exact probability of betting an UNOPENED
turn or river, lever-off against lever-on, at the SAME dealt nodes — so a
difference it reports is the lever and nothing else. It also reports what the
resulting betting range is made of, which is the composition question the
S3-T5 review round said the ticket had to answer before it could ship.**

Why it exists. The first build of S3-T5 sized its lever from before/after runs of
the band harness, and those runs are NOT paired: one `random.Random` supplies
both the deal sequence and the bots' action draws, so the first decision that
flips consumes a different number of draws and every later hand is a different
hand. Differences smaller than the resulting spread were being read as effects.
Codex Sol's review caught it. This probe removes the problem rather than
estimating around it: the hands are played ONCE, and each arm is read off the
same node with the capture-rng trick from `capped_composition_probe.py` (#216),
which records the weights the sampler hands its action draw and disturbs
nothing.

What it measures, and what it does not. It measures POLICY at a FIXED node
population — "given that a bot arrives here, how often does it bet?" It does
NOT measure ARRIVAL: turning the lever on changes which nodes exist at all, and
no amount of pairing can show that, because the two worlds do not play the same
hands. Showdown frequency and the checked-down share are arrival statistics and
belong to the band harness, measured across several seeds. Read this probe for
composition and for the size of the policy change; read the harness for what
that does to a table.

Terms, glossed once:

- **Unopened node** — the acting seat may CHECK or BET; nobody has wagered on
  this street. It is the only node the lever touches.
- **Bluff cell** — an air or ace-high hand with NO draw. Those hands take the
  sampler's exact-frequency bluff branch. A gutshot is NOT in it, which matters:
  an earlier version of this ticket's composition table labelled a gutshot "air"
  and so reported the bluff side moving when it had not.
- **Realised bluff share** — of all the betting this population does at these
  nodes, the fraction contributed by bluff-cell hands. It is a probability-
  weighted share, not a count of sampled bets, so it carries no sampling noise.

Usage (from backend/):
    PYTHONPATH=. python -m tools.late_street_probe --hands 4000 \\
        --seeds 601,20260817,20260818 --dial 1.0
    PYTHONPATH=. python -m tools.late_street_probe --fit --hands 4000
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict

from app.domain import personas_postflop as pp
from app.domain.personas import load_persona_packs
from app.domain.personas_postflop import DrawCategory, StrengthBucket, strength_bucket
from app.domain.spot import ActionType, Street
from app.domain.table import play as play_mod
from tools.export_analytics import play_one_hand

RATIFIED_LINEUP = [
    "tag", "tag", "calling_station", "tag", "passive_fish",
    "lag", "passive_fish", "nit", "maniac",
]
LATE = (Street.TURN, Street.RIVER)


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

    def __getattr__(self, name):  # noqa: ANN001 — delegate the rest
        return getattr(self._rng, name)


def _hand_class(bucket, draw) -> str:
    """Strength bucket crossed with draw class. The bluff cell is named as such
    so it can never be confused with a drawing hand that happens to be air."""
    if bucket in (StrengthBucket.AIR, StrengthBucket.ACE_HIGH):
        if draw is DrawCategory.NONE:
            return f"bluff_cell/{bucket.value}"
        return f"draw/{bucket.value}/{draw.value}"
    return f"made/{bucket.value}" + ("" if draw is DrawCategory.NONE else f"+{draw.value}")


def _is_bluff_cell(bucket, draw) -> bool:
    return bucket in (StrengthBucket.AIR, StrengthBucket.ACE_HIGH) and draw is DrawCategory.NONE


def _strip(pack):
    out = pack.model_copy(deep=True)
    out.postflop = out.postflop.model_copy(update={"late_street_bet": None})
    return out


def _dialled(pack, dial: float):
    out = pack.model_copy(deep=True)
    out.postflop = out.postflop.model_copy(update={"late_street_bet": dial})
    return out


class _Arm:
    """One (dial, value gains, bluff gains) configuration to read at each node."""

    def __init__(self, label, dial, value_gains, bluff_gains):
        self.label = label
        self.dial = dial
        self.value_gains = value_gains
        self.bluff_gains = bluff_gains
        # (persona, street, position, hand_class) -> summed P(bet), node count
        self.bet_mass: dict[tuple, float] = defaultdict(float)
        self.nodes: dict[tuple, int] = defaultdict(int)
        # (persona, street) -> summed P(bet), and the bluff-cell part of it
        self.total: dict[tuple, float] = defaultdict(float)
        self.bluff: dict[tuple, float] = defaultdict(float)
        self.node_total: dict[tuple, int] = defaultdict(int)

    def merge(self, other):
        for store in ("bet_mass", "nodes", "total", "bluff", "node_total"):
            for k, v in getattr(other, store).items():
                getattr(self, store)[k] += v

    def share(self, persona, street) -> float:
        t = self.total[(persona, street)]
        return (self.bluff[(persona, street)] / t) if t else 0.0

    def bet_freq(self, persona, street) -> float:
        n = self.node_total[(persona, street)]
        return (self.total[(persona, street)] / n) if n else 0.0


class _Probe:
    def __init__(self, arms, packs):
        self.arms = arms
        self.base = packs  # lever-off packs; the carrier plays these
        self._cache: dict[tuple, object] = {}

    def _arm_pack(self, persona: str, arm: _Arm):
        key = (persona, arm.label)
        if key not in self._cache:
            base = self.base[persona]
            self._cache[key] = base if arm.dial is None else _dialled(base, arm.dial)
        return self._cache[key]

    def wrap(self, original):
        def wrapper(pack, hole, board, legal, pot_bb, stack_bb, opponents, rng, **kw):
            decision = original(pack, hole, board, legal, pot_bb, stack_bb,
                                opponents, rng, **kw)
            self._record(original, pack, hole, board, legal, pot_bb, stack_bb,
                         opponents, kw)
            return decision
        return wrapper

    def _record(self, original, pack, hole, board, legal, pot_bb, stack_bb,
                opponents, kw) -> None:
        by_kind = {la.action: la for la in legal}
        if ActionType.BET not in by_kind or ActionType.CHECK not in by_kind:
            return  # not an unopened node
        street = kw.get("street")
        if street not in LATE:
            return
        persona = pack.id.removeprefix("persona_")
        bucket, draw = strength_bucket(hole, board)
        klass = _hand_class(bucket, draw)
        ctx = kw.get("context")
        position = "unknown" if ctx is None else ("IP" if ctx.in_position else "OOP")
        bluffy = _is_bluff_cell(bucket, draw)

        for arm in self.arms:
            arm_pack = self._arm_pack(persona, arm)
            gains_v, gains_b = pp._LATE_STREET_GAIN, pp._LATE_STREET_BLUFF_GAIN
            if arm.value_gains is not None:
                pp._LATE_STREET_GAIN = dict(zip(LATE, arm.value_gains, strict=True))
            if arm.bluff_gains is not None:
                pp._LATE_STREET_BLUFF_GAIN = dict(zip(LATE, arm.bluff_gains, strict=True))
            try:
                cap = _CaptureRng(random.Random(0))
                original(arm_pack, hole, board, legal, pot_bb, stack_bb,
                         opponents, cap, **kw)
            finally:
                pp._LATE_STREET_GAIN, pp._LATE_STREET_BLUFF_GAIN = gains_v, gains_b
            p_bet = 0.0
            for action, w in zip(cap.population, cap.weights, strict=True):
                if action is ActionType.BET:
                    p_bet = w
            key = (persona, street.value, position, klass)
            arm.bet_mass[key] += p_bet
            arm.nodes[key] += 1
            tk = (persona, street.value)
            arm.total[tk] += p_bet
            arm.node_total[tk] += 1
            if bluffy:
                arm.bluff[tk] += p_bet


def run(arms, hands: int, seeds: list[int]) -> None:
    """Play `hands` per seed with the LEVER-OFF packs and read every arm at each
    unopened late-street node. The carrier is deliberately lever-off so that all
    arms are read at the SAME, pre-ticket node population."""
    packs = {vt.value if hasattr(vt, "value") else str(vt): _strip(p)
             for vt, p in load_persona_packs().items()}
    play_packs = dict(packs)
    persona_by_seat = {i: RATIFIED_LINEUP[i] for i in range(9)}
    probe = _Probe(arms, packs)
    original = play_mod.sample_postflop_decision
    play_mod.sample_postflop_decision = probe.wrap(original)
    try:
        for seed in seeds:
            rng = random.Random(seed)
            for i in range(hands):
                hand_seed = rng.randrange(1_000_000_000)
                play_one_hand(rng, hand_seed, i % 9, persona_by_seat, play_packs)
    finally:
        play_mod.sample_postflop_decision = original


def _report(arms, personas) -> dict:
    out = {}
    for persona in personas:
        for street in ("turn", "river"):
            row = {}
            for arm in arms:
                row[arm.label] = {
                    "nodes": arm.node_total[(persona, street)],
                    "bet_freq": round(arm.bet_freq(persona, street), 6),
                    "bluff_share": round(arm.share(persona, street), 6),
                }
            out[f"{persona}|{street}"] = row
    return out


def _composition(arms, persona, street) -> dict:
    """Mean P(bet) by hand class and position, one row per arm."""
    keys = sorted({k for arm in arms for k in arm.nodes if k[0] == persona and k[1] == street},
                  key=lambda k: (k[3], k[2]))
    rows = {}
    for k in keys:
        rows[f"{k[3]}|{k[2]}"] = {
            "nodes": arms[0].nodes[k],
            **{arm.label: round(arm.bet_mass[k] / arm.nodes[k], 4)
               for arm in arms if arm.nodes[k]},
        }
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hands", type=int, default=4000)
    ap.add_argument("--seeds", default="601,20260817,20260818")
    ap.add_argument("--dial", type=float, default=1.0)
    ap.add_argument("--personas", default="nit,tag,lag")
    ap.add_argument("--fit", action="store_true",
                    help="scan bluff gains for the smallest that holds the share")
    ap.add_argument("--value-grid", default=None,
                    help="semicolon-separated candidate value-gain pairs to "
                         "compare in one pass, e.g. '0.6,1.0;1.5,2.5'")
    ap.add_argument("--fit-grid", default=None,
                    help="comma-separated bluff gains to scan (default: 0.00..0.50 by 0.02)")
    ap.add_argument("--value-gains", default="0.60,1.00")
    ap.add_argument("--bluff-gains", default=None,
                    help="turn,river; default = the shipped constants")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    seeds = [int(s) for s in args.seeds.split(",")]
    personas = args.personas.split(",")
    vg = tuple(float(x) for x in args.value_gains.split(","))
    arms = [_Arm("off", None, None, None)]
    if args.value_grid:
        bg = (pp._LATE_STREET_BLUFF_GAIN[Street.TURN],
              pp._LATE_STREET_BLUFF_GAIN[Street.RIVER])
        for pair in args.value_grid.split(";"):
            gains = tuple(float(x) for x in pair.split(","))
            arms.append(_Arm(f"v{pair}", args.dial, gains, bg))
    elif args.fit:
        grid = ([float(x) for x in args.fit_grid.split(",")] if args.fit_grid
                else [round(0.02 * i, 2) for i in range(0, 26)])
        for g in grid:
            arms.append(_Arm(f"bg{g:.2f}", args.dial, vg, (g, g)))
    else:
        bg = (tuple(float(x) for x in args.bluff_gains.split(","))
              if args.bluff_gains else
              (pp._LATE_STREET_BLUFF_GAIN[Street.TURN],
               pp._LATE_STREET_BLUFF_GAIN[Street.RIVER]))
        arms.append(_Arm("on", args.dial, vg, bg))

    run(arms, args.hands, seeds)
    result = {"hands_per_seed": args.hands, "seeds": seeds, "dial": args.dial,
              "value_gains": vg, "headline": _report(arms, personas)}
    if not args.fit:
        result["composition"] = {
            f"{p}|{s}": _composition(arms, p, s)
            for p in personas for s in ("turn", "river")
        }
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(result, indent=2, sort_keys=True, default=str))
    for tag, row in result["headline"].items():
        print(tag)
        for label, v in row.items():
            print(f"    {label:9s} nodes={v['nodes']:6d} "
                  f"bet_freq={v['bet_freq']:.4f} bluff_share={v['bluff_share']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
