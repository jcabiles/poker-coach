"""Two fairness arms.

broyden  — vector fit that UPDATES its Jacobian from each new measurement
           (secant analogue of the scalar arm; the stale-J Newton of fit2 is
           handicapped against the harness's nonlinearity).
swapped  — scalar coordinate descent with the WRONG lever/stat pairing
           (call_looseness -> AF, aggression -> FtC), the pairing whose
           Gauss-Seidel spectral radius the measured J predicts is > 1.

Usage: python fit3.py <broyden|swapped> <target_label> <outfile>
"""
from __future__ import annotations

import json
import math
import sys

import jac
import lin
import vecfit_lib as V

MODE, TLABEL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
N = 48000
PERSONA = "tag"
X0 = (0.6, 2.4)
CL_RANGE = (0.10, 2.0)
AGG_RANGE = (0.20, 5.6)
MAX_LN_STEP = 0.8
CAP = 8

R = jac.load("results.jsonl")
J0, _ = jac.jacobian(R, "tag_base", "tag_cl+25", "tag_cl-25", "tag_agg+25", "tag_agg-25")
base, true = R["tag_base"], R[TLABEL]
s_ftc, s_af = jac.sigmas(base)
TOL = (3 * s_ftc, 3 * s_af)
TARGET = (true["ftc"], true["af"])
Y0 = (base["ftc"], base["af"])
_calls = {"n": 0}


def y_at(cl, agg, tag):
    _calls["n"] += 1
    af, ftc, ncall, nopp, dt = V.measure(PERSONA, cl, agg, N)
    rec = dict(mode=MODE, tag=tag, call=_calls["n"], cl=round(cl, 5), agg=round(agg, 5),
               ftc=ftc, af=af, e_ftc=(ftc - TARGET[0]) / TOL[0], e_af=(af - TARGET[1]) / TOL[1],
               secs=round(dt, 1))
    print(json.dumps(rec), flush=True)
    with open(OUT, "a") as fh:
        fh.write(json.dumps(rec) + "\n")
    return (ftc, af)


def done(y):
    return abs(y[0] - TARGET[0]) <= TOL[0] and abs(y[1] - TARGET[1]) <= TOL[1]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def broyden():
    J = [row[:] for row in J0]
    x, y = list(X0), Y0
    while not done(y) and _calls["n"] < CAP:
        r = (TARGET[0] - y[0], TARGET[1] - y[1])
        d = lin.matvec(lin.inv(J), r)
        sc = min(1.0, MAX_LN_STEP / max(abs(d[0]), abs(d[1]), 1e-12))
        dx = (d[0] * sc, d[1] * sc)
        xn = [clamp(x[0] * math.exp(dx[0]), *CL_RANGE), clamp(x[1] * math.exp(dx[1]), *AGG_RANGE)]
        dx = (math.log(xn[0] / x[0]), math.log(xn[1] / x[1]))
        yn = y_at(xn[0], xn[1], f"broyden step {_calls['n']+1}")
        dy = (yn[0] - y[0], yn[1] - y[1])
        Jdx = lin.matvec(J, dx)
        den = dx[0] * dx[0] + dx[1] * dx[1]
        if den > 1e-12:  # Broyden "good" rank-1 update
            for i in range(2):
                c = (dy[i] - Jdx[i]) / den
                J[i][0] += c * dx[0]
                J[i][1] += c * dx[1]
        x, y = xn, yn
    print(json.dumps(dict(mode=MODE, x=x, y=y, calls=_calls["n"], ok=done(y), J=J)), flush=True)


def swapped():
    """cl chases AF, agg chases FtC — the parallel-rows pairing."""
    x, y = list(X0), Y0
    for rnd in range(4):
        for coord, (si, seed, rng_) in enumerate(
            [(1, J0[1][0], CL_RANGE), (0, J0[0][1], AGG_RANGE)]
        ):
            hist = [(math.log(x[coord]), y[si])]
            it = 0
            while abs(y[si] - TARGET[si]) > TOL[si] and it < 4 and _calls["n"] < CAP:
                s = seed
                if len(hist) >= 2 and hist[-1][0] != hist[-2][0]:
                    sec = (hist[-1][1] - hist[-2][1]) / (hist[-1][0] - hist[-2][0])
                    if sec * seed > 0 and abs(sec) > 0.2 * abs(seed):
                        s = sec
                step = clamp((TARGET[si] - y[si]) / s, -MAX_LN_STEP, MAX_LN_STEP)
                x[coord] = clamp(math.exp(hist[-1][0] + step), *rng_)
                y = y_at(x[0], x[1], f"swapped r{rnd+1} {'cl->AF' if coord==0 else 'agg->FtC'}")
                hist.append((math.log(x[coord]), y[si]))
                it += 1
            if done(y) or _calls["n"] >= CAP:
                print(json.dumps(dict(mode=MODE, x=x, y=y, calls=_calls["n"], ok=done(y))), flush=True)
                return
    print(json.dumps(dict(mode=MODE, x=x, y=y, calls=_calls["n"], ok=done(y))), flush=True)


if __name__ == "__main__":
    print(f"[{MODE}->{TLABEL}] tol=({TOL[0]:.5f},{TOL[1]:.5f}) target={TARGET}", flush=True)
    broyden() if MODE == "broyden" else swapped()
