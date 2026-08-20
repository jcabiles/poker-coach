"""The naked-ace-high fold rate against the alpha ceiling alpha = f/(1+f), on
every street and at one, two and three opponents.

WHY THIS EXISTS. The owner ruled on 2026-08-19 that the alpha bound DOES apply
to the ACE_HIGH strength bucket, closing the open question T1 referred up
(`docs/ai-dlc/ledger/phase3-invest-then-fold.md`, finding 3 and its open item).
`alpha_measure.py` beside this file answered the question T1 needed — how far
T1's damp moves the bucket at more than one opponent — and swept `street=None`,
FLOP and TURN. It never swept the RIVER, which is the street T3 then opened a
call leg on. This script sweeps all four and adds the damp sweep in section 3,
so the ruling has a full baseline rather than a partial one.

NOTHING HERE CHANGES THE ENGINE. It measures the tip it is run on.

The node is `catcher_fold_by_size`'s exactly (pot-before-bet 6bb, 100bb stacks,
fresh aggressor, deal seed 20260721, per-cell decision seed
20260721 + 100*persona_index + frac_index, n=1250), so this table and the alpha
guard's headroom table are directly comparable. Three things differ: the range
filter is ACE_HIGH + DrawCategory.NONE, `opponents` is swept rather than pinned
to 1, and `street` is passed explicitly.

Run it from the backend directory:

    cd backend && PYTHONPATH=. python \
        ../docs/ai-dlc/research/slice2-invest-then-fold/alpha_acehigh_measure.py

It prints the markdown that `alpha-acehigh-ruling.md` carries, so the committed
tables and this script cannot drift apart.
"""

import random

from app.domain import personas_postflop
from app.domain.archetypes import VillainType
from app.domain.equity import RANKS
from app.domain.personas import load_persona_packs
from app.domain.personas_postflop import (
    DrawCategory,
    StrengthBucket,
    sample_postflop_decision,
    strength_bucket,
)
from app.domain.spot import ActionType, LegalAction, Street

PRICE_FRACS = (0.33, 0.5, 1.0, 1.5)
N = 1250
ALL_PERSONAS = sorted(v.value for v in VillainType)
OPP = (1, 2, 3)
STREETS = [
    ("street = None", None),
    ("street = FLOP", Street.FLOP),
    ("street = TURN", Street.TURN),
    ("street = RIVER", Street.RIVER),
]
# Section 3 sweeps T3's shipped constant. 0.0 reproduces the pre-T3 engine
# exactly (the call merit was hard-zeroed for the whole bluff cell); 0.06 is
# what ships; 0.45 is the minimum-defence value T3 derived and did not ship;
# 1.0 is the leg with no damp at all.
DAMPS = (0.0, 0.06, 0.45, 1.0, 1.5, 2.0, 2.5, 3.0)


def deal(n_board: int) -> list:
    """n_board naked-ace-high spots at the frozen deal seed."""
    deal_rng = random.Random(20260721)
    deck0 = [r + s for r in RANKS for s in "shdc"]
    spots: list = []
    while len(spots) < N:
        deck = deck0[:]
        deal_rng.shuffle(deck)
        hole, board = (deck[0], deck[1]), deck[2 : 2 + n_board]
        made, draw = strength_bucket(hole, board)
        if draw is DrawCategory.NONE and made is StrengthBucket.ACE_HIGH:
            spots.append((hole, board))
    return spots


def fold_rate(pack, pi: int, fi: int, frac: float, opponents: int, street, spots) -> float:
    to_call = round(frac * 6.0, 2)
    legal = [
        LegalAction(action=ActionType.FOLD),
        LegalAction(action=ActionType.CALL, min_bb=to_call),
        LegalAction(action=ActionType.RAISE, min_bb=2 * to_call, max_bb=100.0),
    ]
    rng = random.Random(20260721 + 100 * pi + fi)
    folds = 0
    for hole, board in spots:
        d = sample_postflop_decision(
            pack, hole, board, legal, 6.0 + to_call, 100.0, opponents, rng,
            current_bet_to=to_call, street=street,
        )
        folds += d.action is ActionType.FOLD
    return folds / N


def main() -> None:
    packs = load_persona_packs()
    spots3 = deal(3)
    spots5 = deal(5)

    print("## 1. The violation map\n")
    counts = {}
    for label, street in STREETS:
        print(f"### {label}\n")
        print("| persona | frac | α | opp=1 | opp=2 | opp=3 |")
        print("|---|---:|---:|---:|---:|---:|")
        for pi, persona in enumerate(ALL_PERSONAS):
            pack = packs[VillainType(persona)]
            for fi, frac in enumerate(PRICE_FRACS):
                alpha = frac / (1 + frac)
                cells = []
                for opps in OPP:
                    v = fold_rate(pack, pi, fi, frac, opps, street, spots3)
                    counts[(label, opps)] = counts.get((label, opps), 0) + (v > alpha)
                    cells.append(f"**{v:.4f}**" if v > alpha else f"{v:.4f}")
                print(f"| {persona} | {frac} | {alpha:.4f} | " + " | ".join(cells) + " |")
        print()

    print("## 2. Cells above α, per street and opponent count\n")
    print("| street | opp=1 | opp=2 | opp=3 |")
    print("|---|---:|---:|---:|")
    for label, _ in STREETS:
        row = " | ".join(f"{counts[(label, o)]}/24" for o in OPP)
        print(f"| {label} | {row} |")
    print()

    print("## 3. T3's river call leg against α, swept over its constant\n")
    print("| `_ACE_HIGH_RIVER_CALL_DAMP` | cells above α at opp=1 | station ⅓-pot | nit ½-pot |")
    print("|---|---:|---:|---:|")
    shipped = personas_postflop._ACE_HIGH_RIVER_CALL_DAMP
    try:
        for damp in DAMPS:
            personas_postflop._ACE_HIGH_RIVER_CALL_DAMP = damp
            fails = 0
            probes = {}
            for pi, persona in enumerate(ALL_PERSONAS):
                pack = packs[VillainType(persona)]
                for fi, frac in enumerate(PRICE_FRACS):
                    v = fold_rate(pack, pi, fi, frac, 1, Street.RIVER, spots5)
                    fails += v > frac / (1 + frac)
                    probes[(persona, frac)] = v
            tag = " (shipped)" if damp == shipped else ""
            print(
                f"| {damp}{tag} | {fails}/24 | "
                f"{probes[('calling_station', 0.33)]:.4f} | {probes[('nit', 0.5)]:.4f} |"
            )
    finally:
        personas_postflop._ACE_HIGH_RIVER_CALL_DAMP = shipped
    print()

    print("## 4. Board length is not a variable for this bucket\n")
    diffs = []
    for pi, persona in enumerate(ALL_PERSONAS):
        pack = packs[VillainType(persona)]
        for fi, frac in enumerate(PRICE_FRACS):
            a = fold_rate(pack, pi, fi, frac, 1, Street.RIVER, spots3)
            b = fold_rate(pack, pi, fi, frac, 1, Street.RIVER, spots5)
            diffs.append(abs(a - b))
    print(
        f"Largest |3-card − 5-card| river fold-rate difference over the 24 "
        f"opp=1 cells: {max(diffs):.4f}\n"
    )


if __name__ == "__main__":
    main()
