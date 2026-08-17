"""Shared harness wrapper for the N-vecfit premise measurement.

READ-ONLY on the repo: imports the test module, mutates packs IN MEMORY only.
"""
from __future__ import annotations

import math
import sys
import time

BACKEND = "/Users/johncabiles/Documents/Github/poker-coach/backend"
for p in (BACKEND, BACKEND + "/tests"):
    if p not in sys.path:
        sys.path.insert(0, p)

import test_personas_postflop as T  # noqa: E402
from app.domain.archetypes import VillainType  # noqa: E402
from app.domain.personas import load_persona_packs  # noqa: E402

_BASE = load_persona_packs()
CALLS = []  # (persona, cl, agg, n, af, ftc, ncall, ncbet, secs)


def levers(persona: str):
    pf = _BASE[VillainType(persona)].postflop
    return dict(
        aggression=pf.aggression,
        call_looseness=pf.call_looseness,
        stickiness=pf.stickiness,
        continue_ref=pf.continue_ref,
    )


def packs_at(persona: str, cl: float, agg: float):
    """Packs with ONLY (call_looseness, aggression) moved on `persona`.

    continue_ref is deliberately NOT re-synced (N-LOGIT frozen anchor).
    """
    vt = VillainType(persona)
    pack = _BASE[vt]
    pf = pack.postflop.model_copy(update={"call_looseness": cl, "aggression": agg})
    return {**_BASE, vt: pack.model_copy(update={"postflop": pf})}


def measure(persona: str, cl: float, agg: float, n: int, context_aware: bool = True):
    """One harness call -> (af, ftc, n_call, n_cbet_opps). Timed + logged."""
    t0 = time.time()
    af, ftc, wtsd, ncall, ncbet, nflop = T._persona_stats(
        packs_at(persona, cl, agg), persona, n, context_aware=context_aware
    )
    dt = time.time() - t0
    CALLS.append((persona, cl, agg, n, af, ftc, ncall, ncbet, dt))
    return af, ftc, ncall, ncbet, dt


def sigma_ftc(ftc: float, n_opp: int) -> float:
    return math.sqrt(max(ftc * (1 - ftc), 1e-9) / n_opp)


def sigma_af(af: float, n_call: int, n_br: float | None = None) -> float:
    """Delta-method sd for a ratio of two counts (BET+RAISE)/CALL.

    Treat both counts as ~Poisson in the number of postflop decisions:
    sd(af)/af ~= sqrt(1/n_br + 1/n_call).
    """
    if n_br is None:
        n_br = af * n_call
    return af * math.sqrt(1.0 / max(n_br, 1.0) + 1.0 / max(n_call, 1.0))
