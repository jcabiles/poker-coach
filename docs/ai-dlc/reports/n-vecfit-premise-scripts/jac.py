"""Jacobian + conditioning + Gauss-Seidel spectral radius from measured points."""
from __future__ import annotations

import json
import math
import sys

import lin


def load(path="results.jsonl"):
    out = {}
    for line in open(path):
        r = json.loads(line)
        out[r["label"]] = r
    return out


def sigmas(r):
    ftc, nopp = r["ftc"], r["n_opp"]
    af, ncall = r["af"], r["n_call"]
    nbr = af * ncall
    s_ftc = math.sqrt(ftc * (1 - ftc) / nopp)
    s_af = af * math.sqrt(1.0 / nbr + 1.0 / ncall)
    return s_ftc, s_af


def jacobian(R, base, clp, clm, aggp, aggm, step=0.25):
    dln = math.log(1 + step) - math.log(1 - step)
    J = [
        [(R[clp]["ftc"] - R[clm]["ftc"]) / dln, (R[aggp]["ftc"] - R[aggm]["ftc"]) / dln],
        [(R[clp]["af"] - R[clm]["af"]) / dln, (R[aggp]["af"] - R[aggm]["af"]) / dln],
    ]
    return J, dln


def report(name, R, base, clp, clm, aggp, aggm):
    J, dln = jacobian(R, base, clp, clm, aggp, aggm)
    b = R[base]
    s_ftc, s_af = sigmas(b)
    # 1-sigma noise on each J entry from independent-sample binomial/delta sd
    sJ = [[math.sqrt(2) * s_ftc / dln] * 2, [math.sqrt(2) * s_af / dln] * 2]
    Js = lin.rowscale(J, [1.0 / (3 * s_ftc), 1.0 / (3 * s_af)])  # rows in tolerance units
    rho = abs(J[0][1] * J[1][0] / (J[0][0] * J[1][1]))
    print(f"--- {name} @ ({b['cl']}, {b['agg']}) n={b['n']}")
    print(f"base: FtC={b['ftc']:.5f} (n_opp={b['n_opp']})  AF={b['af']:.5f} "
          f"(n_call={b['n_call']}, n_br={b['af']*b['n_call']:.0f})")
    print(f"noise 1sigma: FtC {s_ftc:.5f} (3s={3*s_ftc:.5f})  AF {s_af:.5f} (3s={3*s_af:.5f})")
    print("J (rows FtC,AF; cols dln cl, dln agg):")
    for i, rn in enumerate(("FtC", "AF ")):
        print(f"  {rn} [{J[i][0]:+.5f} +-{sJ[i][0]:.5f}]  [{J[i][1]:+.5f} +-{sJ[i][1]:.5f}]"
              f"   |t| = {abs(J[i][0]/sJ[i][0]):.1f}, {abs(J[i][1]/sJ[i][1]):.1f}")
    print(f"off/diag: J12/J11 = {J[0][1]/J[0][0]:+.3f}   J21/J22 = {J[1][0]/J[1][1]:+.3f}")
    print(f"cond(J) raw = {lin.cond(J):.2f}   cond(J) tolerance-scaled = {lin.cond(Js):.2f}")
    print(f"Gauss-Seidel spectral radius rho = |J12*J21/(J11*J22)| = {rho:.4f}"
          f"   (error contraction per scalar round: {1/rho:.1f}x)")
    print(f"J^-1 = {lin.inv(J)}")
    return J


if __name__ == "__main__":
    R = load(sys.argv[1] if len(sys.argv) > 1 else "results.jsonl")
    J = report("tag", R, "tag_base", "tag_cl+25", "tag_cl-25", "tag_agg+25", "tag_agg-25")
    b, t = R["tag_base"], R["tag_TRUE"]
    s_ftc, s_af = sigmas(b)
    print(f"\ntarget (0.45,3.0): FtC={t['ftc']:.5f} AF={t['af']:.5f}")
    print(f"initial error: dFtC={t['ftc']-b['ftc']:+.5f} ({(t['ftc']-b['ftc'])/(3*s_ftc):+.2f} tol)"
          f"  dAF={t['af']-b['af']:+.5f} ({(t['af']-b['af'])/(3*s_af):+.2f} tol)")
    if "nit_base" in R:
        report("nit", R, "nit_base", "nit_cl+25", "nit_cl-25", "nit_agg+25", "nit_agg-25")
