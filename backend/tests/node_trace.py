"""W0-c — seeded node-trace realism pack (persona-realism foundation).

A lightweight, seeded replay: run each persona through a fixed set of crafted
spots and log the decision NODE — bucket, draw class, the (normalized) action
probability vector, the seeded chosen action, and the intended prescription.
Its purpose is to catch "right stat, WRONG node" later (e.g. a maniac hitting
its aggression number by over-valuing made hands instead of bluffing): a human
or a later slice reads bucket + probs + prescription and sees whether the mix
at the node is coherent.

Design notes:
- **Merits via capture, no domain edit.** `sample_postflop_decision`'s action
  draw is its FIRST `rng.choices` call, and the weights it passes are already
  NORMALIZED (`w/total`) — so a capture rng records the exact action
  *probabilities* with zero domain instrumentation. (Raw pre-clamp merits would
  need domain changes = out of scope; hence `action_probabilities`, not
  "merits".)
- **The capture rng WRAPS a seeded inner rng** and delegates every call, so the
  chosen action is a real seeded sample — not a forced `population[0]` (which
  would always be CHECK/FOLD, the first candidate).
- Reuses only the public sampler API on crafted fixtures — no dependency on the
  `_play_hand` harness and no `range_estimate` coupling (so: no parity risk).

T-TRACE: every spot now authors its own situational context (`in_position`,
`bet_prev_street`, `facing_raise`) and `build_trace` passes a real
`PostflopContext` per spot, so W3's position multiplier and busted-draw river
bluff are EXERCISED here instead of resolving to identity. `busted_draw` is
DERIVED (`busted_draw_kind`) from the spot's own hole+board — never authored —
so the trace can never disagree with production about what a busted draw is.
Note `PostflopContext()` is not a neutral value: its `in_position=False`
default applies the OOP damp, which is why each spot states its position
explicitly (the "not applicable" value would be `context=None`).
"""

from __future__ import annotations

import random
from typing import NamedTuple

from app.domain import personas_postflop
from app.domain.action import ActionType
from app.domain.archetypes import VillainType
from app.domain.personas import load_persona_packs
from app.domain.spot import LegalAction, Street
from app.domain.table.postflop_context import PostflopContext, busted_draw_kind

sample_postflop_decision = personas_postflop.sample_postflop_decision
strength_bucket = personas_postflop.strength_bucket


class _TraceRng:
    """Capture rng: records the FIRST `choices()` call (the action draw — whose
    weights are the normalized action probabilities) and delegates EVERY call
    to an inner seeded rng, so the chosen action is a real seeded sample and the
    later sizing draw still resolves normally."""

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)
        self.population: list[ActionType] | None = None
        self.weights: list[float] | None = None

    def choices(self, population, weights, k=1):  # noqa: ANN001 — rng protocol
        if self.population is None:
            self.population = list(population)
            self.weights = list(weights)
        return self._rng.choices(population, weights=weights, k=k)


class Spot(NamedTuple):
    spot_id: str
    hole: tuple[str, str]
    board: tuple[str, ...]
    legal: tuple[LegalAction, ...]
    pot_bb: float
    stack_bb: float
    opponents: int
    current_bet_to: float
    street: Street
    is_aggressor: bool
    # T-TRACE situational context. `in_position` and `bet_prev_street` become
    # `PostflopContext` fields; `facing_raise` is a separate sampler kwarg by
    # design (the range estimator must opt into it without inheriting the
    # `PostflopContext` position default). `busted_draw` is deliberately ABSENT
    # here — it is derived from hole+board in `build_trace`.
    in_position: bool
    bet_prev_street: bool
    facing_raise: bool
    prescription: str


class TraceRow(NamedTuple):
    persona: str
    spot_id: str
    bucket: str
    draw_class: str
    action_probabilities: dict[str, float]  # ActionType.value -> normalized prob
    chosen_action: str
    prescription: str


def _first_in(stack: float) -> tuple[LegalAction, ...]:
    """Unbet street: the actor can CHECK or BET (a c-bet / lead / barrel)."""
    return (
        LegalAction(action=ActionType.CHECK),
        LegalAction(action=ActionType.BET, min_bb=1.0, max_bb=stack),
    )


def _facing(to_call: float, stack: float, jam: float | None = None) -> tuple[LegalAction, ...]:
    """Facing a bet: FOLD / CALL / RAISE. `jam` forces the raise bracket to a
    single all-in value (a low-SPR shove)."""
    r_min = jam if jam is not None else to_call * 2
    r_max = jam if jam is not None else stack
    return (
        LegalAction(action=ActionType.FOLD),
        LegalAction(action=ActionType.CALL, min_bb=to_call),
        LegalAction(action=ActionType.RAISE, min_bb=r_min, max_bb=r_max),
    )


# The seeded spot set — one representative per node the roadmap names. Each is
# deliberately a non-degenerate candidate set (>=2 actions with real merit) so
# the capture never hits the zero-total-merit fallback (Sol #9 / theory nit).
#
# Context authorship: `in_position` states the node's real geometry (the OOP
# twin below is the one deliberate exception — a copy varied on position ALONE).
# `bet_prev_street` is "did this seat bet/raise the street before" — for a flop
# spot that means "was the preflop raiser". `facing_raise` is False in every
# spot: none of them faces a second aggressive action on the street (the two
# facing spots face a bare BET), and the ticket forbids adding spots.
SPOTS: tuple[Spot, ...] = (
    Spot("flop_ip_toppair_dry", ("Ah", "Th"), ("As", "7d", "2c"),
         _first_in(100.0), 6.0, 100.0, 1, 0.0, Street.FLOP, True,
         in_position=True, bet_prev_street=True, facing_raise=False,
         prescription="IP c-bet, top pair dry board: value-heavy, high c-bet freq"),
    # The OOP twin of the spot above: byte-identical except `in_position=False`,
    # so the pair isolates the W3-b position multiplier as the ONLY varying term.
    Spot("flop_oop_toppair_dry", ("Ah", "Th"), ("As", "7d", "2c"),
         _first_in(100.0), 6.0, 100.0, 1, 0.0, Street.FLOP, True,
         in_position=False, bet_prev_street=True, facing_raise=False,
         prescription="OOP c-bet, top pair dry board: same node, out of position"),
    Spot("flop_oop_secondpair_overcards", ("Th", "9h"), ("9s", "Ah", "Kd"),
         _first_in(100.0), 6.0, 100.0, 1, 0.0, Street.FLOP, True,
         in_position=False, bet_prev_street=True, facing_raise=False,
         prescription="OOP middle pair + 2 overcards: vulnerable, check-heavy / thin"),
    # Facing a c-bet as the (out-of-position) preflop caller — the modal HU
    # defence node.
    Spot("flop_facing_bet_strong_draw", ("Jh", "Th"), ("9h", "8c", "2h"),
         _facing(4.0, 100.0), 10.0, 100.0, 1, 4.0, Street.FLOP, False,
         in_position=False, bet_prev_street=False, facing_raise=False,
         prescription="strong combo draw vs a bet: semi-bluff raise / call, few folds"),
    Spot("turn_barrel_toppair", ("Ah", "Th"), ("As", "7d", "2c", "4s"),
         _first_in(100.0), 12.0, 100.0, 1, 0.0, Street.TURN, True,
         in_position=True, bet_prev_street=True, facing_raise=False,
         prescription="turn barrel with top pair: continuation vs give-up"),
    # `bet_prev_street=True` is what makes this a *busted* barrel rather than a
    # random river stab — the W3-c story bluff is gated on it.
    Spot("river_busted_draw", ("Jh", "Th"), ("9h", "8c", "2s", "3d", "Kc"),
         _first_in(100.0), 18.0, 100.0, 1, 0.0, Street.RIVER, True,
         in_position=True, bet_prev_street=True, facing_raise=False,
         prescription="busted draw on the river: polarized bluff vs give-up"),
    # 4-way: the aggressor is last to act in only 1 of 4 seats, so OOP is the
    # representative multiway c-bet node.
    Spot("flop_multiway_toppair", ("Ah", "Th"), ("As", "7d", "2c"),
         _first_in(100.0), 8.0, 100.0, 3, 0.0, Street.FLOP, True,
         in_position=False, bet_prev_street=True, facing_raise=False,
         prescription="top pair 4-way: value tightens as opponents rise"),
    # A bloated 20bb pot at 15bb stacks is a raised pot; this seat raised
    # preflop and now faces a lead in position.
    Spot("flop_lowspr_commit_overpair", ("Ah", "Ad"), ("Ks", "7d", "2c"),
         _facing(10.0, 15.0, jam=15.0), 20.0, 15.0, 1, 10.0, Street.FLOP, False,
         in_position=True, bet_prev_street=True, facing_raise=False,
         prescription="overpair, low SPR facing a bet: commit / stack off"),
)


def build_trace(seed: int = 20260724, spots: tuple[Spot, ...] = SPOTS) -> list[TraceRow]:
    """Run every persona through every spot; return the node-trace rows.

    `spots` defaults to the pack above (every existing caller is unchanged); a
    caller may pass a same-length variant to isolate ONE context field — the
    per-spot seed is `seed + index`, so index-aligned variants share the rng
    stream and any difference in the trace is attributable to that field alone.
    """
    packs = load_persona_packs()
    rows: list[TraceRow] = []
    for vt in VillainType:
        pack = packs[vt]
        for i, spot in enumerate(spots):
            bucket, draw = strength_bucket(spot.hole, list(spot.board))
            cap = _TraceRng(seed + i)
            context = PostflopContext(
                in_position=spot.in_position,
                bet_prev_street=spot.bet_prev_street,
                # DERIVED, never authored — same helper production uses, so a
                # spot can never claim a busted draw its cards do not hold.
                busted_draw=busted_draw_kind(spot.hole, list(spot.board)),
            )
            decision = sample_postflop_decision(
                pack,
                spot.hole,
                list(spot.board),
                list(spot.legal),
                spot.pot_bb,
                spot.stack_bb,
                spot.opponents,
                cap,
                current_bet_to=spot.current_bet_to,
                is_aggressor=spot.is_aggressor,
                street=spot.street,
                context=context,
                facing_raise=spot.facing_raise,
            )
            if cap.population is None:  # zero-total-merit fallback (deterministic)
                probs = {decision.action.value: 1.0}
            else:
                assert cap.weights is not None
                probs = {a.value: w for a, w in zip(cap.population, cap.weights, strict=True)}
            rows.append(
                TraceRow(
                    persona=vt.value,
                    spot_id=spot.spot_id,
                    bucket=bucket.value,
                    draw_class=draw.value,
                    action_probabilities=probs,
                    chosen_action=decision.action.value,
                    prescription=spot.prescription,
                )
            )
    return rows
