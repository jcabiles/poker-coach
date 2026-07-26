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

    Declaration order is the taxonomy order of the ticket and it ROUGHLY tracks
    the mapping pipeline — preflop entrant/action shape, all-in status,
    open-size band, hero's role, this street's action sequence, the bet
    fraction, then whether the stacks support the canonical legal-action
    buckets.

    **It is NOT the literal evaluation order, and this docstring used to claim
    it was.** Two gates check all-in status BEFORE finishing their shape
    checks: `_hu_srp_preflop` tests seat status at `:203-205` but is still
    emitting `PREFLOP_SHAPE_UNGATED` at `:211-217`, and `_mw_srp_preflop`
    inverts the same pair. So a gate that answers `PREFLOP_SHAPE_UNGATED` may
    already have evaluated `ALL_IN_IN_LINE`. Declaration order is a DISPLAY and
    TIE-BREAK order; it is not a claim about which line of code runs first
    (theory-reviewer MED).

    **The selection rule is three tiers, not one depth contest** — see
    `classify_postflop_rejection`, which is the single authority:

      1. DOMINANT — `NO_MAPPER_FOR_STREET_SHAPE`, `NO_MAPPER_FOR_ROLE`,
         `ALL_IN_IN_LINE`. Returned outright when they apply, because each says
         the decision tree itself is absent or destroyed; any deeper reason
         found alongside them would be an artefact.
      2. DEPTH CONTEST — `PREFLOP_SHAPE_UNGATED` .. `STACK_TOO_SHALLOW`. The
         deepest stage any candidate mapper reached wins.
      3. FALLBACK — `UNCLASSIFIED`, only when nothing named the failure.

    **Why deepest-wins and not a literal top-down first-match scan.** The
    ticket words the taxonomy as "precedence-ordered, first match wins", which
    reads naturally if each reason is a predicate on the DECISION POINT. It is
    degenerate when applied to the per-mapper fan-out we actually have, because
    the reasons are collected from 5-9 sibling mappers at once and the siblings
    of every OTHER family always report `PREFLOP_SHAPE_UNGATED` — index 1, so
    it wins essentially every scan. Measured on the 181-hand corpus, literal
    first-match collapses 55 of 62 rows into `PREFLOP_SHAPE_UNGATED` and drives
    `HERO_ROLE_UNGATED` to 0. Deepest-wins instead asks "how far did the
    best-matching mapper actually get", which is the ticket's SEMANTIC reading,
    and reproduces it on all 62 rows.

    (An earlier revision of this docstring justified the substitution by
    claiming wrong-role mappers "always emit `HERO_ROLE_UNGATED`" and so would
    swamp a first-match scan. That was backwards — `HERO_ROLE_UNGATED` is index
    4, BEHIND `PREFLOP_SHAPE_UNGATED`, so under first-match it can never win.
    The conclusion held; the stated mechanism did not. Fixed per refuter MED-3.)

    `UNCLASSIFIED` is deliberately EXCLUDED from the depth contest — see
    `classify_postflop_rejection`.
    """

    #: No mapper exists for (this street, this preflop shape) at all — the
    #: shape IS gated, just not here. Every limped-pot turn/river lands here
    #: (`map_limped_flop_*` are flop-only), as does every turn/river of the
    #: opener-plus-one-cold-caller shape (`map_flop_vs_caller_raise` is too).
    NO_MAPPER_FOR_STREET_SHAPE = "NO_MAPPER_FOR_STREET_SHAPE"
    #: The shape is gated, hero's SEAT in it is a normal aggressor/defender
    #: role that a sibling family already maps — it just has no mapper here,
    #: as a build-order gap. The live instance: hero opened, two players cold-
    #: called, both blinds folded, hero is the 3-way flop aggressor. The BB-in
    #: family maps exactly that role (`map_mw_flop_cbet`); the no-BB family
    #: does not. **Buildable — this is a `T-cover` work item.** Split out of
    #: `HERO_ROLE_UNGATED` on theory-reviewer MED: a scoper could not tell
    #: "add a mapper to an existing family" from "this seat is deliberately not
    #: graded", and the two want opposite decisions.
    #:
    #: Produced ONLY by `_refine_role_reason`, never emitted by a twin.
    NO_MAPPER_FOR_ROLE = "NO_MAPPER_FOR_ROLE"
    #: The preflop entrant/action shape matches no gated family: 3-bet pots,
    #: 5+-way single-raised pots, blind opens/entrants, limp-then-call chains,
    #: multiway limped pots, a preflop entrant who has since folded, ...
    PREFLOP_SHAPE_UNGATED = "PREFLOP_SHAPE_UNGATED"
    #: A player in the line is all-in (or made a short, all-in call). DOMINANT:
    #: an all-in means the decision tree is GONE — there is no bet/raise
    #: subtree left to grade — so reporting a deeper reason like "donk lead"
    #: would send `T-cover` to build a mapper for a spot that stays ungradeable
    #: whatever it does (theory-reviewer MED). It previously sat in the depth
    #: contest at index 2, maskable by any sibling reaching index >= 3, and
    #: that exposure grows monotonically as `T-cover` widens the gates.
    ALL_IN_IN_LINE = "ALL_IN_IN_LINE"
    #: The preflop open is outside the gated [2.0 .. `_OVERSIZE_OPEN_CAP`] band
    #: (station 3.5 / fish 4.0 / maniac 4.5 opens).
    OPEN_SIZE_OFF_BAND = "OPEN_SIZE_OFF_BAND"
    #: The shape is gated and hero's seat is DELIBERATELY outside it — the
    #: EARLIER of two cold-callers in the no-BB family, or any cold-caller in
    #: the BB-in family. Both are the same documented law: those seats never
    #: CLOSE the street (the BB always holds a live action behind them), and
    #: the multiway families gate facing nodes only where hero closes. Widening
    #: here needs new theory, not a new mapper — contrast `NO_MAPPER_FOR_ROLE`.
    HERO_ROLE_UNGATED = "HERO_ROLE_UNGATED"
    #: This street's action sequence is not the gated one: donk/lead, probe,
    #: delayed c-bet, check-back, a caller raise, an unresolved caller, ...
    STREET_ACTION_SHAPE_UNGATED = "STREET_ACTION_SHAPE_UNGATED"
    #: A bet in the line is off the `RECOGNIZED_BET_FRACS` grid.
    BET_FRACTION_OFF_GRID = "BET_FRACTION_OFF_GRID"
    #: Stacks cannot support the canonical bet/raise buckets the Spot offers.
    STACK_TOO_SHALLOW = "STACK_TOO_SHALLOW"
    #: Catch-all, so the taxonomy is exhaustive. Ranked last for TOTALITY, not
    #: for depth: it is only reported when NO sibling mapper produced a named
    #: reason (see `classify_postflop_rejection`). A live count above zero
    #: means a real rejection path has no name yet — investigate, do not widen.
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
    `map_decision_point` at a POSTFLOP hero decision point.

    THE selection rule, in three tiers (`RejectReason` documents the poker
    rationale for each):

      1. DOMINANT, in this order — `NO_MAPPER_FOR_STREET_SHAPE`,
         `ALL_IN_IN_LINE`, then `NO_MAPPER_FOR_ROLE`/`HERO_ROLE_UNGATED` via
         refinement. Each says the decision tree is absent or destroyed, so a
         deeper reason found alongside one of them is an artefact.
      2. DEPTH CONTEST — the deepest stage any candidate twin reached wins.
      3. FALLBACK — `UNCLASSIFIED` when nothing named the failure.
    """
    return classify_with_evidence(state, hero_seat).reason


class Classification(NamedTuple):
    """`classify_with_evidence`'s answer: the reason plus the raw twin reasons
    behind it, so a measurement tool can report which STAGES were reached
    (an unreached stage's zero and a genuinely-never-fired zero must never be
    presented alike — theory-reviewer HIGH)."""

    reason: RejectReason
    #: Every twin reason for hero's street, in dispatch order.
    twin_reasons: tuple[RejectReason, ...]
    #: Deepest depth-contest index any twin reached (-1 when none did).
    max_depth: int


def classify_with_evidence(state: HandState, hero_seat: int) -> Classification:
    """`classify_postflop_rejection` plus the evidence it selected over."""
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
    reasons = tuple(
        result.reason
        for result in (twin(state, hero_seat) for twin in _street_twins(gp, street))
        if result.reason is not None
    )
    contested = [r for r in reasons if r in _DEPTH_CONTEST]
    max_depth = max((REASON_ORDER.index(r) for r in contested), default=-1)

    def answer(reason: RejectReason) -> Classification:
        return Classification(reason, reasons, max_depth)

    # --- tier 1: dominant --------------------------------------------------
    gated_streets = [streets for gate, streets in families if gate.value is not None]
    if gated_streets and not any(street in s for s in gated_streets):
        return answer(RejectReason.NO_MAPPER_FOR_STREET_SHAPE)
    if RejectReason.ALL_IN_IN_LINE in reasons:
        # An all-in destroys the subtree; a deeper sibling reason would send
        # T-cover after a mapper for a spot that stays ungradeable regardless.
        return answer(RejectReason.ALL_IN_IN_LINE)
    if RejectReason.HERO_ROLE_UNGATED in reasons and not [
        r for r in contested if REASON_ORDER.index(r) > _ROLE_DEPTH
    ]:
        return answer(_refine_role_reason(gp, families, state, hero_seat))

    # --- tier 2: depth contest ---------------------------------------------
    # `UNCLASSIFIED` is ranked last for TOTALITY, not for depth, so it must not
    # enter the contest: it would out-rank every named sibling and one twin's
    # catch-all would erase the whole decision point's real reason. This is
    # reachable in legal play (refuter MED-1) — e.g. open-limp -> iso-raise ->
    # the limper folds, where `_mw_srp_preflop` mis-reads the folded limper as
    # a cold-caller and `_map_mw_flop_cbet`'s pot-consistency check fires
    # `UNCLASSIFIED` while all eight siblings say `PREFLOP_SHAPE_UNGATED`.
    if contested:
        return answer(max(contested, key=REASON_ORDER.index))

    # --- tier 3: fallback ---------------------------------------------------
    return answer(RejectReason.UNCLASSIFIED)


#: Reasons that take part in the depth contest (tier 2). The two structural
#: `NO_MAPPER_*` reasons and `ALL_IN_IN_LINE` are dominant; `UNCLASSIFIED` is
#: the fallback. Deliberately derived from the enum so a new member cannot be
#: silently omitted.
_DEPTH_CONTEST: frozenset[RejectReason] = frozenset(
    REASON_ORDER[REASON_ORDER.index(RejectReason.PREFLOP_SHAPE_UNGATED):]
) - {RejectReason.ALL_IN_IN_LINE, RejectReason.UNCLASSIFIED}


def _refine_role_reason(gp: Any, families, state: HandState, hero_seat: int):
    """Split a role rejection into "buildable" vs "deliberately excluded".

    A twin says only `HERO_ROLE_UNGATED`; whether that is a build-order gap or
    a documented exclusion depends on WHICH seat hero holds in WHICH family,
    which is poker judgement rather than a gate condition. It lives here, in
    one readable table, so the gates stay behaviour-identical.

    `buildable` = a sibling family already maps this exact poker role, so
    `T-cover` can add a mapper without new theory.
    """
    hu, mw_bb, mw_nobb, caller_raise, limped = (g for g, _streets in families)

    if mw_nobb.value is not None:
        opener, callers, _open_to = mw_nobb.value
        if opener.seat == hero_seat:
            # "I opened, two cold-called, both blinds folded, I'm the 3-way
            # flop aggressor." The BB-in family maps precisely this role
            # (`map_mw_flop_cbet` / `map_mw_*_barrel`); the no-BB family only
            # ever grew its caller side. Pure build-order gap.
            return RejectReason.NO_MAPPER_FOR_ROLE
        if any(c.seat == hero_seat for c in callers[:-1]):
            # The EARLIER cold-caller never closes — documented exclusion.
            return RejectReason.HERO_ROLE_UNGATED

    if mw_bb.value is not None:
        _opener, callers, _bb, _open_to = mw_bb.value
        if any(c.seat == hero_seat for c in callers):
            # A cold-caller inside the BB-in shape can never close: the BB acts
            # after him on every street. Same documented law.
            return RejectReason.HERO_ROLE_UNGATED

    del hu, caller_raise, limped  # no role gap observed in these families
    return RejectReason.HERO_ROLE_UNGATED


_ALL_STREETS = (Street.FLOP, Street.TURN, Street.RIVER)
_FLOP_ONLY = (Street.FLOP,)
#: Depth index of the role stage — a twin that reached deeper than this was
#: past hero's role, so a sibling's role complaint is not the binding reason.
_ROLE_DEPTH = REASON_ORDER.index(RejectReason.HERO_ROLE_UNGATED)


def _street_twins(gp: Any, street: Street) -> tuple:
    """The internal twins of exactly the mappers `map_decision_point`
    dispatches on `street`, in the same order.

    RIVER is the fall-through, so a PREFLOP state would silently be handed the
    river mappers and come back with a confident, meaningless reason. The
    classifier's precondition says postflop; say so loudly (refuter LOW-3)."""
    if street is Street.PREFLOP:
        raise ValueError(
            "classify_postflop_rejection is POSTFLOP-only; got street=preflop"
        )
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
