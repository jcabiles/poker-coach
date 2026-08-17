"""Pure-python 2x2 linear algebra (no numpy in the backend venv)."""
from __future__ import annotations

import math


def det(J):
    return J[0][0] * J[1][1] - J[0][1] * J[1][0]


def inv(J):
    d = det(J)
    return [[J[1][1] / d, -J[0][1] / d], [-J[1][0] / d, J[0][0] / d]]


def matvec(J, v):
    return [J[0][0] * v[0] + J[0][1] * v[1], J[1][0] * v[0] + J[1][1] * v[1]]


def cond(J):
    F = sum(x * x for row in J for x in row)
    D = abs(det(J))
    disc = max(F * F - 4 * D * D, 0.0)
    s1 = math.sqrt((F + math.sqrt(disc)) / 2)
    s2 = math.sqrt((F - math.sqrt(disc)) / 2)
    return s1 / s2 if s2 > 0 else float("inf")


def rowscale(J, s):
    return [[J[0][0] * s[0], J[0][1] * s[0]], [J[1][0] * s[1], J[1][1] * s[1]]]
