"""Why the postflop Simulate->Spot mapper returned None (T-REJECT).

`map_decision_point` answers `Spot | None`; a `None` is recorded as "no
baseline yet" and nothing says WHY. This module supplies the reason
*vocabulary* (`RejectReason`) that `grade_map_postflop`'s gates emit, plus a
second-pass `classify_postflop_rejection` that turns one already-rejected
decision point into exactly one reason — so `T-cover` is scoped off measured
counts instead of anecdote.

Precondition: the caller ALREADY got `None` from `map_decision_point` at a
postflop hero decision point. Nothing here re-checks that.

**No duplicated gate logic.** Per owner decision B1 the gate predicates and
spot builders in `grade_map_postflop` were refactored to report a typed
internal diagnostic alongside their value, and every mapper has an internal
`_map_*` twin returning `(spot, reason)`. The public `map_*` functions are thin
wrappers whose signature is unchanged (`Spot | None`). The classifier reads
those diagnostics; it never re-implements a gate, so the reason counts cannot
drift from what the grader actually does.

Layering: the vocabulary lives here and `grade_map_postflop` imports it, so the
gate that detects a rejection is also the thing that names it. The classifier
needs the mapper internals, so it imports `grade_map_postflop` inside the
function body — that keeps the module-level dependency one-directional.

Pure domain: no web/DB imports (enforced by test_domain_purity).
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, NamedTuple

from app.domain.spot import Street

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.domain.spot import Spot
    from app.domain.table.engine import HandState


class RejectReason(Enum):
    """One reason a postflop decision point could not be mapped.

    Declaration order IS the taxonomy order of the ticket and it is also the
    order of the mapping PIPELINE: a mapper checks the preflop entrant/action
    shape, then all-in status, then the open-size band, then hero's role, then
    this street's action sequence, then the bet fraction, then whether the
    stacks support the canonical legal-action buckets. `classify_*` therefore
    reports the DEEPEST stage any candidate mapper reached before rejecting —
    the shallow reasons are the ones that apply to the whole decision point,
    the deep ones only survive when nothing shallower was wrong.
    """

    #: No mapper exists for (this street, this preflop shape) at all — the
    #: shape IS gated, just not here. Every limped-pot turn/river lands here
    #: (`map_limped_flop_*` are flop-only), as does every turn/river of the
    #: opener-plus-one-cold-caller shape (`map_flop_vs_caller_raise` is too).
    NO_MAPPER_FOR_STREET_SHAPE = "NO_MAPPER_FOR_STREET_SHAPE"
    #: The preflop entrant/action shape matches no gated family: 3-bet pots,
    #: 5+-way single-raised pots, blind opens/entrants, limp-then-call chains,
    #: multiway limped pots, a preflop entrant who has since folded, ...
    PREFLOP_SHAPE_UNGATED = "PREFLOP_SHAPE_UNGATED"
    #: A player in the line is all-in (or made a short, all-in call).
    ALL_IN_IN_LINE = "ALL_IN_IN_LINE"
    #: The preflop open is outside the gated [2.0 .. `_OVERSIZE_OPEN_CAP`] band
    #: (station 3.5 / fish 4.0 / maniac 4.5 opens).
    OPEN_SIZE_OFF_BAND = "OPEN_SIZE_OFF_BAND"
    #: The shape is gated but hero does not hold a gated seat in it — e.g. a
    #: cold-caller inside the BB-in multiway family, or the EARLIER of two
    #: cold-callers in the no-BB family (he never closes).
    HERO_ROLE_UNGATED = "HERO_ROLE_UNGATED"
    #: This street's action sequence is not the gated one: donk/lead, probe,
    #: delayed c-bet, check-back, a caller raise, an unresolved caller, ...
    STREET_ACTION_SHAPE_UNGATED = "STREET_ACTION_SHAPE_UNGATED"
    #: A bet in the line is off the `RECOGNIZED_BET_FRACS` grid.
    BET_FRACTION_OFF_GRID = "BET_FRACTION_OFF_GRID"
    #: Stacks cannot support the canonical bet/raise buckets the Spot offers.
    STACK_TOO_SHALLOW = "STACK_TOO_SHALLOW"
    #: Catch-all, so the taxonomy is exhaustive. A live count above zero means
    #: a real rejection path has no name yet — investigate, do not widen.
    UNCLASSIFIED = "UNCLASSIFIED"


#: Taxonomy order == pipeline depth (see `RejectReason`). Index = depth.
REASON_ORDER: tuple[RejectReason, ...] = tuple(RejectReason)


class GateResult(NamedTuple):
    """A preflop-family gate's answer: its tuple payload, or why it rejected."""

    value: tuple | None
    reason: RejectReason | None


class StreetResult(NamedTuple):
    """A per-street action-shape gate's answer (payload is gate-specific)."""

    value: Any | None
    reason: RejectReason | None


class MapResult(NamedTuple):
    """An internal `_map_*` twin's answer. `spot is None` iff `reason` is set."""

    spot: Spot | None
    reason: RejectReason | None


def gate_fail(reason: RejectReason) -> GateResult:
    return GateResult(None, reason)


def street_fail(reason: RejectReason) -> StreetResult:
    return StreetResult(None, reason)


def map_fail(reason: RejectReason) -> MapResult:
    return MapResult(None, reason)


def classify_postflop_rejection(state: HandState, hero_seat: int) -> RejectReason:
    """Name the single reason this postflop hero decision point is unmapped.

    Second pass — the caller has already had `None` back from
    `map_decision_point`. Runs the five preflop-family gates and the street's
    mapper twins, then reports the deepest stage reached (see `RejectReason`).
    """
    from app.domain.table import grade_map_postflop as gp

    street = state.street
    # Families that gate SOME street, and which streets they gate. A family
    # whose gate PASSES while none of its streets is hero's street means the
    # shape is recognized but simply has no mapper here.
    families = (
        (gp._hu_srp_preflop(state), _ALL_STREETS),
        (gp._mw_srp_preflop(state), _ALL_STREETS),
        (gp._mw_nobb_srp_preflop(state), _ALL_STREETS),
        (gp._flop_caller_raise_preflop(state), _FLOP_ONLY),
        (gp._limped_flop_hu_preflop(state), _FLOP_ONLY),
    )
    gated_streets = [streets for gate, streets in families if gate.value is not None]
    if gated_streets and not any(street in s for s in gated_streets):
        return RejectReason.NO_MAPPER_FOR_STREET_SHAPE

    reasons = [
        result.reason
        for result in (twin(state, hero_seat) for twin in _street_twins(gp, street))
        if result.reason is not None
    ]
    if not reasons:
        # Unreachable under the precondition (some mapper built a Spot), but the
        # taxonomy must stay total.
        return RejectReason.UNCLASSIFIED
    return max(reasons, key=REASON_ORDER.index)


_ALL_STREETS = (Street.FLOP, Street.TURN, Street.RIVER)
_FLOP_ONLY = (Street.FLOP,)


def _street_twins(gp: Any, street: Street) -> tuple:
    """The internal twins of exactly the mappers `map_decision_point`
    dispatches on `street`, in the same order."""
    if street is Street.FLOP:
        return (
            gp._map_flop_cbet,
            gp._map_flop_vs_cbet,
            gp._map_flop_vs_check_raise,
            gp._map_flop_vs_caller_raise,
            gp._map_mw_flop_vs_cbet,
            gp._map_mw_flop_cbet,
            gp._map_mw_caller_vs_cbet,
            gp._map_limped_flop_lead,
            gp._map_limped_flop_vs_lead,
        )
    if street is Street.TURN:
        return (
            gp._map_turn_barrel,
            gp._map_vs_turn_bet,
            gp._map_mw_vs_turn_bet,
            gp._map_mw_turn_barrel,
            gp._map_mw_caller_vs_turn_bet,
        )
    return (
        gp._map_river_barrel,
        gp._map_vs_river_bet,
        gp._map_mw_vs_river_bet,
        gp._map_mw_river_barrel,
        gp._map_mw_caller_vs_river_bet,
    )
