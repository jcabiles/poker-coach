# Finding ledger — persona-realism Wave A wave 3 (T-STICKY)

Slice: delete the dead `stickiness` key from `passive_fish`/`calling_station` + PersonaPostflop
authorship validator (required while a fallback is live, forbidden when both split levers authored).
Branch `feat/persona-realism-wave-a-w3-sticky`, commits `8dc2b28` (build) + `803e9dc` (C-1 fix).
Reviewers (all git-READ-ONLY): Claude `refuter`, `persona-realism-theory-reviewer`, Codex `gpt-5.6-sol`.

## Digest (done-condition)

Pre-change digest captured FIRST on branch base `58006a9` (post-T-ANCHOR main), re-captured after
every edit — identical throughout:

```
cells=216 sha256=0cf55ed157cf5ad59a08f1a717d548b4249e8b18f524a9daf23f65c9e4c1453c
```

Zero band edits, zero fixture re-records, `BACKEND VERIFY OK` (1127→1128 passed / 1 skipped), ruff clean.

## Findings

| # | Source | Severity | Finding | Adjudication |
|---|--------|----------|---------|--------------|
| C-1 | Codex Sol | LOW | Forbidden direction checked parsed value (`is not None`), so `"stickiness": null` beside both split levers slipped through — key presence is the contract, not value | **ACCEPTED — FIXED** in `803e9dc`: `"stickiness" in self.model_fields_set` + null-payload test |
| T-1 | theory-reviewer | MED (advisory) | Maniac's legacy fallback `_PRICE_SENSITIVITY · stickiness^(−DAMP)` (0.55 → exponent 2.406) makes it the roster's joint-STEEPEST price responder; theory contract §5 wants maniac low/flat across sizes. Lever-level only — metric #4 (size-bucketed FtC) doesn't exist yet | **ACCEPTED as CARRY-FORWARD** — not this slice's defect (ticket no-go defers four-pack `size_elasticity` authoring as band-moving). When that slice lands with metric #4 live, maniac is the priority case: fit its `size_elasticity` LOW |
| R-1 | refuter | LOW (informational) | Ticket digest not independently reproducible — both independent harnesses produced different hashes (recipe under-specifies repr/concatenation), though BOTH independently proved the property itself (theory reviewer: 0/216 cells differ before/after; refuter: code-trace + crash-free full grid) | **ACCEPTED — ALTERNATIVE**: exact capture script recorded below + in PR body instead of committing a new tool (owned-files discipline) |

Verdicts: refuter PASS · theory-reviewer PASS (theory adherence YES; realism = no behavior change,
independently proven) · Codex FAIL→resolved by C-1 fix.

## Exact digest capture script (R-1)

Run from `backend/` with the venv active: `python sticky_digest.py [out.json]`

```python
"""T-STICKY 216-cell merit-grid digest.

Grid per the ticket (docs/ai-dlc/tickets/persona-realism-wave-a.md):
6 personas (sorted) x 3 hands x 4 faced fractions x 3 streets = 216 cells.
Each cell: hash input = repr((population, weights)) of the FIRST rng.choices
call inside sample_postflop_decision (the action draw). Capture rng seeded 1.
Legal = [FOLD, CALL(min=bet), RAISE(min=2*bet, max=300)]; pot 20.0;
bet = frac * 20; current_bet_to = bet; board sliced to 3/4/5 from bd+['4d','3c'].
"""

import hashlib
import json
import random
import sys

from app.domain.personas import load_persona_packs
from app.domain.personas_postflop import sample_postflop_decision
from app.domain.spot import ActionType, LegalAction, Street


class FirstChoicesRecorder(random.Random):
    def __init__(self, seed):
        super().__init__(seed)
        self.first = None

    def choices(self, population, weights=None, *, cum_weights=None, k=1):
        if self.first is None:
            self.first = (list(population), list(weights) if weights else None)
        return super().choices(population, weights=weights, cum_weights=cum_weights, k=k)


HANDS = [
    (("7h", "5d"), ["Kc", "9s", "3h"]),
    (("Kh", "9d"), ["Ks", "7c", "2h"]),
    (("Ah", "Ad"), ["Ks", "7c", "2h"]),
]
FRACS = [0.30, 0.55, 0.90, 1.50]
POT = 20.0
STREETS = [("FLOP", 3, Street.FLOP), ("TURN", 4, Street.TURN), ("RIVER", 5, Street.RIVER)]


def main() -> None:
    packs = load_persona_packs()
    by_id = {p.id: p for p in packs.values()}
    assert len(by_id) == 6, f"expected 6 packs, got {sorted(by_id)}"
    cells = {}
    for pid in sorted(by_id):
        pack = by_id[pid]
        for hole, bd in HANDS:
            full = bd + ["4d", "3c"]
            for frac in FRACS:
                bet = frac * POT
                legal = [
                    LegalAction(action=ActionType.FOLD),
                    LegalAction(action=ActionType.CALL, min_bb=bet),
                    LegalAction(action=ActionType.RAISE, min_bb=2 * bet, max_bb=300.0),
                ]
                for sname, ncards, street in STREETS:
                    rng = FirstChoicesRecorder(1)
                    sample_postflop_decision(
                        pack,
                        hole,
                        full[:ncards],
                        legal,
                        POT,
                        300.0,
                        1,
                        rng,
                        current_bet_to=bet,
                        street=street,
                    )
                    assert rng.first is not None, f"no choices call in {pid}"
                    cells[f"{pid}|{hole}|{frac}|{sname}"] = repr(rng.first)
    assert len(cells) == 216, len(cells)
    blob = "\n".join(f"{k}={v}" for k, v in sorted(cells.items()))
    digest = hashlib.sha256(blob.encode()).hexdigest()
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w") as f:
            json.dump({"digest": digest, "cells": cells}, f, indent=1, sort_keys=True)
    print(f"cells=216 sha256={digest}")


if __name__ == "__main__":
    main()
```

Under-specified knobs resolved as: stack_bb=300.0, opponents=1, one recorder seeded 1 per cell,
blob = sorted `key=repr` lines joined by newline, key = `pid|hole-tuple|frac|street-name`.
