"""Scalar (coordinate-descent) vs vector (Newton) fit, both on the real harness.

Both start at tag's authored point (0.6, 2.4) and chase the stats measured at a
shifted TRUE point (0.45, 3.0). Tolerance = the 3-sigma binomial/delta noise band
at the base point. Both are seeded with the SAME measured slope information, so
the comparison isolates the COUPLING, not derivative knowledge.
"""
from __future__ import annotations

import json
import math

import jac
import lin
import vecfit_lib as V

N = 48000
PERSONA = "tag"
X0 = (0.6, 2.4)
CL_RANGE = (0.10, 2.0)
AGG_RANGE = (0.20, 5.6)
MAX_LN_STEP = 0.8
SCALAR_CAP = 12
VECTOR_CAP = 5

R = jac.load("results.jsonl")
J, _ = jac.jacobian(R, "tag_base", "tag_cl+25", "tag_cl-25", "tag_agg+25", "tag_agg-25")
Jinv = lin.inv(J)
base, true = R["tag_base"], R["tag_TRUE"]
s_ftc, s_af = jac.sigmas(base)
TOL = (3 * s_ftc, 3 * s_af)
TARGET = (true["ftc"], true["af"])
Y0 = (base["ftc"], base["af"])

_seen: set[tuple[float, float]] = set()
_calls = {"n": 0}
LOG = []


def y_at(cl, agg, tag):
    """One harness evaluation; distinct lever points are counted as cost."""
    key = (round(cl, 6), round(agg, 6))
    fresh = key not in _seen
    _seen.add(key)
    if fresh:
        _calls["n"] += 1
    af, ftc, ncall, nopp, dt = V.measure(PERSONA, cl, agg, N)
    rec = dict(tag=tag, call=_calls["n"], fresh=fresh, cl=round(cl, 5), agg=round(agg, 5),
               ftc=ftc, af=af, e_ftc=(ftc - TARGET[0]) / TOL[0], e_af=(af - TARGET[1]) / TOL[1],
               secs=round(dt, 1))
    LOG.append(rec)
    print(json.dumps(rec), flush=True)
    with open("fit_trajectory.jsonl", "a") as fh:
        fh.write(json.dumps(rec) + "\n")
    return (ftc, af)


def done(y):
    return abs(y[0] - TARGET[0]) <= TOL[0] and abs(y[1] - TARGET[1]) <= TOL[1]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def scalar_fit():
    """Doc steps 2-4, one lever at a time: cl -> FtC, then agg -> AF, repeat."""
    x = list(X0)
    y = Y0
    print(f"[scalar] start x={x} y={y}", flush=True)
    for rnd in range(4):
        for coord, (si, seed_slope, rng_) in enumerate(
            [(0, J[0][0], CL_RANGE), (1, J[1][1], AGG_RANGE)]
        ):
            hist = [(math.log(x[coord]), y[si])]
            it = 0
            while abs(y[si] - TARGET[si]) > TOL[si] and it < 4 and _calls["n"] < SCALAR_CAP:
                s = seed_slope
                if len(hist) >= 2 and hist[-1][0] != hist[-2][0]:
                    sec = (hist[-1][1] - hist[-2][1]) / (hist[-1][0] - hist[-2][0])
                    if sec * seed_slope > 0 and abs(sec) > 0.2 * abs(seed_slope):
                        s = sec
                step = clamp((TARGET[si] - y[si]) / s, -MAX_LN_STEP, MAX_LN_STEP)
                x[coord] = clamp(math.exp(hist[-1][0] + step), *rng_)
                y = y_at(x[0], x[1], f"scalar r{rnd+1} {'cl' if coord==0 else 'agg'}")
                hist.append((math.log(x[coord]), y[si]))
                it += 1
            if done(y):
                print(f"[scalar] CONVERGED after {_calls['n']} calls (round {rnd+1})", flush=True)
                return x, y, _calls["n"]
            if _calls["n"] >= SCALAR_CAP:
                print(f"[scalar] CAP {SCALAR_CAP} hit", flush=True)
                return x, y, _calls["n"]
    print(f"[scalar] exhausted rounds at {_calls['n']} calls", flush=True)
    return x, y, _calls["n"]


def vector_fit():
    x = list(X0)
    y = Y0
    print(f"[vector] start x={x} y={y}", flush=True)
    k = 0
    while not done(y) and k < VECTOR_CAP:
        r = (TARGET[0] - y[0], TARGET[1] - y[1])
        d = lin.matvec(Jinv, r)
        scale = min(1.0, MAX_LN_STEP / max(abs(d[0]), abs(d[1]), 1e-12))
        x[0] = clamp(x[0] * math.exp(d[0] * scale), *CL_RANGE)
        x[1] = clamp(x[1] * math.exp(d[1] * scale), *AGG_RANGE)
        y = y_at(x[0], x[1], f"vector step {k+1}")
        k += 1
    print(f"[vector] {'CONVERGED' if done(y) else 'CAP'} after {_calls['n']} calls", flush=True)
    return x, y, _calls["n"]


if __name__ == "__main__":
    print(f"tol=(FtC {TOL[0]:.5f}, AF {TOL[1]:.5f})  target={TARGET}  J={J}", flush=True)
    xs, ys, cs = scalar_fit()
    _seen.clear()
    _calls["n"] = 0
    xv, yv, cv = vector_fit()
    print(json.dumps(dict(scalar=dict(x=xs, y=ys, calls=cs, ok=done(ys)),
                          vector=dict(x=xv, y=yv, calls=cv, ok=done(yv)))), flush=True)
