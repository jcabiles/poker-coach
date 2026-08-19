"""Facing-a-BET fold rate for NAKED ACE-HIGH at 1/2/3 opponents vs the alpha
ceiling alpha = f/(1+f). Mirrors test_personas_postflop.catcher_fold_by_size's
node exactly (pot_pre 6bb, 100bb stacks, deal seed 20260721, per-cell decision
seed 20260721 + 100*persona_index + frac_index, n=1250) — the differences are
the range filter (ACE_HIGH + DrawCategory.NONE instead of the one-pair catcher
buckets), that `opponents` is swept instead of pinned to 1, and that `street` is
passed EXPLICITLY.

The street sweep is load-bearing, not decoration. `catcher_fold_by_size` and
`fold_by_size` both omit `street`, so they measure at `street=None` — which is
outside the damp's `street in (FLOP, TURN)` gate. Measured at street=None the
before/after tables are byte-identical and the measurement says nothing at all.

Run, from the backend directory, with `--pre-t1` for the neutralized arm:

    cd backend && PYTHONPATH=. python ../docs/ai-dlc/research/slice2-invest-then-fold/alpha_measure.py [--pre-t1]
"""
import random
import sys

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
STREETS = [("none", None), ("flop", Street.FLOP), ("turn", Street.TURN)]

PRE_T1 = "--pre-t1" in sys.argv
if PRE_T1:
    # The measurement is a facing-a-BET curve, so neutralizing the damp to 1.0
    # reproduces the pre-T1 engine on this node EXACTLY: before T1 the predicate
    # was `facing_raise`, which is False everywhere here, so the damp
    # contributed nothing. Same construction the T1 tests use.
    personas_postflop._ACE_HIGH_FLOAT_RAISE_DAMP = 1.0

packs = load_persona_packs()
deal_rng = random.Random(20260721)
deck0 = [r + s for r in RANKS for s in "shdc"]
spots = []
while len(spots) < N:
    deck = deck0[:]
    deal_rng.shuffle(deck)
    hole, board = (deck[0], deck[1]), deck[2:5]
    made, draw = strength_bucket(hole, board)
    if draw is DrawCategory.NONE and made is StrengthBucket.ACE_HIGH:
        spots.append((hole, board))

pot_pre = 6.0
rows = {}
for pi, persona in enumerate(ALL_PERSONAS):
    pack = packs[VillainType(persona)]
    for fi, frac in enumerate(PRICE_FRACS):
        to_call = round(frac * pot_pre, 2)
        pot = pot_pre + to_call
        legal = [
            LegalAction(action=ActionType.FOLD),
            LegalAction(action=ActionType.CALL, min_bb=to_call),
            LegalAction(action=ActionType.RAISE, min_bb=2 * to_call, max_bb=100.0),
        ]
        for sname, street in STREETS:
            for opps in OPP:
                rng = random.Random(20260721 + 100 * pi + fi)  # same per-cell seed
                folds = 0
                for hole, board in spots:
                    d = sample_postflop_decision(
                        pack, hole, board, legal, pot, 100.0, opps, rng,
                        current_bet_to=to_call, street=street,
                    )
                    folds += d.action is ActionType.FOLD
                rows[(persona, frac, sname, opps)] = folds / N

label = sys.argv[1] if len(sys.argv) > 1 else "?"
print(f"# naked ace-high (ACE_HIGH, DrawCategory.NONE) facing a BET — {label}")
print(f"# n={N} spots/cell, deal seed 20260721, node pot_pre 6bb / 100bb stacks")
print()
for sname, _ in STREETS:
    print(f"## street = {sname}"
          + ("   <- OUTSIDE the damp's street gate; nothing here can move"
             if sname == "none" else "   <- INSIDE the damp's street gate"))
    print()
    print("| persona | frac | alpha | opp=1 | opp=2 | opp=3 | head@1 | head@2 | head@3 |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    worst = None
    for persona in ALL_PERSONAS:
        for frac in PRICE_FRACS:
            a = frac / (1 + frac)
            r = [rows[(persona, frac, sname, o)] for o in OPP]
            h = [a - x for x in r]
            print(f"| {persona} | {frac} | {a:.4f} | {r[0]:.4f} | {r[1]:.4f} | "
                  f"{r[2]:.4f} | {h[0]:+.4f} | {h[1]:+.4f} | {h[2]:+.4f} |")
            for o, hh in zip(OPP, h):
                if worst is None or hh < worst[0]:
                    worst = (hh, persona, frac, o)
    print()
    print(f"MIN HEADROOM (alpha - fold): {worst[0]:+.4f} at {worst[1]} "
          f"frac={worst[2]} opponents={worst[3]}")
    print(f"CEILING RESPECTED AT ALL CELLS: {worst[0] >= 0}")
    print()
print("# raw csv: persona,frac,street,opponents,fold_rate")
for k in sorted(rows):
    print(f"{k[0]},{k[1]},{k[2]},{k[3]},{rows[k]:.6f}")
