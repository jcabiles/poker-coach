"""One harness call in its own process (ProcessPool is blocked by the sandbox).

Usage: python one.py <persona> <cl> <agg> <n> [tag]  -> prints one JSON line,
also appends it to results.jsonl.
"""
from __future__ import annotations

import json
import sys

import vecfit_lib as V

persona, cl, agg, n = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
label = sys.argv[5] if len(sys.argv) > 5 else ""
af, ftc, ncall, nopp, dt = V.measure(persona, cl, agg, n)
rec = dict(label=label, persona=persona, cl=cl, agg=agg, n=n, af=af, ftc=ftc,
           n_call=ncall, n_opp=nopp, secs=round(dt, 1))
line = json.dumps(rec)
with open("results.jsonl", "a") as fh:
    fh.write(line + "\n")
print(line)
