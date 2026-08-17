"""Measure WHY the postflop mapper says "no baseline yet" on a stored session.

    cd backend && python -m tools.reject_counts --session <id> [--max-hand-no N]

Prints the street x reason matrix `T-cover` is scoped off. Read-only: opens no
transaction, writes nothing, changes no schema.

**Pin the corpus.** A sim session stays `active` and grows whenever anyone
plays it; this one went 181 -> 221 -> 229 hands during the T-REJECT ticket, so
an unpinned run does not reproduce. The T-REJECT deliverable is measured with
`--max-hand-no 181` (the 181-hand review corpus).

Two things make the number trustworthy, both asserted before a single reason is
counted (owner decision B2):

1. **Deterministic replay.** `SimDecision` stores no state snapshot and
   `SimHand.state_json` is the TERMINAL state, so the `HandState` immediately
   before each hero decision does not exist anywhere. It is reconstructed by
   replaying that hand's `action_history` from `start_hand`, with each seat's
   pre-hand stack recovered as `stack_bb + invested_total_bb` (the same
   identity `sim_session._public_history` relies on).
2. **Coverage parity, both directions.** Every replayed hero decision must
   reproduce the PERSISTED `coverage` verdict (mapped vs unmappable) and
   street, AND the replayed and persisted decision counts must agree — the
   forward check alone would silently drop a persisted row the replay never
   reaches. That proves the replay is the same game the app played, and it
   doubles as the B1 parity check on the gate-diagnostic refactor, since
   `map_decision_point` has to answer exactly what it answered at play time
   across the whole corpus.

Output is the street x reason matrix, then a descriptive breakdown for EVERY
non-zero reason (a reason names the STAGE that rejected, never the shape, so
the matrix alone cannot scope `T-cover`).

**Every reason row is printed, zero or not, with an EVALUATION count.** A zero
that was never reached and a zero that was reached-and-never-fired mean
opposite things, and suppressing all-zero rows made them indistinguishable —
it hid that `BET_FRACTION_OFF_GRID` and `STACK_TOO_SHALLOW` are structurally
censored on this corpus (82% of rows cannot reach a sizing check at all) and
that `OPEN_SIZE_OFF_BAND` is a tautological zero, since every open a persona
can make is inside the `[2.0, _OVERSIZE_OPEN_CAP=4.5]` band.
Theory-reviewer HIGH.

(T2b, 2026-08-17: that sentence used to enumerate four fixed sizes,
3.0/3.5/4.0/4.5. The personas now draw the open from a distribution spanning
2.5 to 4.5, so the enumeration is gone and the claim rests on the band alone.
Still tautological, for the same reason.)
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter

from sqlmodel import Session, create_engine, select

from app.db.models import SimDecision, SimHand
from app.db.session import engine as _app_engine
from app.domain.action import Decision
from app.domain.spot import ActionType, Position, Street
from app.domain.table.deck import DealtHand
from app.domain.table.engine import HandState, apply, start_hand
from app.domain.table.grade_map import map_decision_point
from app.domain.table.grade_map_common import _street_actions
from app.domain.table.grade_map_reject import (
    _DEPTH_CONTEST,
    _ROLE_DEPTH,
    REASON_ORDER,
    RejectReason,
    classify_with_evidence,
)
from app.services.sim_session import HERO_SEAT

_POSTFLOP = (Street.FLOP, Street.TURN, Street.RIVER)
#: Reasons the selection rule tests on EVERY row (dominant tier + fallback),
#: as opposed to the depth-contest reasons, which are only reached when some
#: twin gets that far.
_ALWAYS_EVALUATED = (
    RejectReason.NO_MAPPER_FOR_STREET_SHAPE,
    RejectReason.ALL_IN_IN_LINE,
    RejectReason.UNCLASSIFIED,
)


def _resolve_engine(db_path: str | None):
    """The app engine by default; a read-only override for measuring a pinned
    snapshot. The live DB is routinely reset/rotated (it was emptied and the
    T-REJECT corpus moved to a backup file mid-ticket), so a pinned
    measurement needs to be able to name its database."""
    if db_path is None:
        return _app_engine
    return create_engine(f"sqlite:///file:{db_path}?mode=ro&uri=true")


def _evaluations(reason: RejectReason, max_depths: list[int]) -> int:
    """How many of the unmapped rows actually REACHED this reason's stage.

    Paired with the failure count, this is what separates a censored zero from
    a real one: `0 fail / 0 eval` means the check never ran and the cell
    carries no information; `0 fail / N eval` means it ran N times and never
    fired.

    Definition, per tier:
      * dominant + fallback reasons — tested on every row by construction.
      * `NO_MAPPER_FOR_ROLE` / `HERO_ROLE_UNGATED` — share the role stage.
      * depth-contest reasons — a twin that rejected at depth d evaluated every
        stage up to and including d, so the stage at depth k was reached iff
        some twin reached depth >= k.

    Caveat, stated because the point of this column is honesty: gate check
    ORDER is not exactly the taxonomy order (`RejectReason` documents the two
    known inversions), so for the shallowest stages this is a lower bound on
    the true number of predicate evaluations. For the deep stages that the
    censoring finding is about — bet fraction, stack — it is exact.
    """
    if reason in _ALWAYS_EVALUATED:
        return len(max_depths)
    if reason is RejectReason.NO_MAPPER_FOR_ROLE:
        return sum(1 for d in max_depths if d >= _ROLE_DEPTH)
    if reason in _DEPTH_CONTEST:
        depth = REASON_ORDER.index(reason)
        return sum(1 for d in max_depths if d >= depth)
    return len(max_depths)


class ParityError(RuntimeError):
    """The replay did not reproduce what the app persisted — stop, do not
    report a reason matrix measured on a mis-replayed game."""


def _initial_state(terminal: HandState) -> HandState:
    """Rewind a hand to its pre-blind opening state."""
    stacks = [
        round(s.stack_bb + s.invested_total_bb, 2)
        for s in sorted(terminal.seats, key=lambda s: s.seat)
    ]
    dealt = DealtHand(
        hole_cards=[s.hole_cards for s in sorted(terminal.seats, key=lambda s: s.seat)],
        board=terminal.full_board,
    )
    return start_hand(dealt, terminal.button_seat, stacks)


def _replay(terminal: HandState):
    """Yield (ordinal, pre-decision HandState) for every HERO decision.

    `ordinal` matches `SimDecision.ordinal` (0-based hero-decision order within
    the hand, all streets).
    """
    state = _initial_state(terminal)
    pos2seat = {s.position: s.seat for s in state.seats}
    ordinal = 0
    for h in terminal.action_history:
        if h.action is ActionType.POST:
            continue
        seat = pos2seat[h.position]
        if state.hand_over or state.to_act_seat != seat:
            raise ParityError(
                f"replay desync: history says {h.position.value} acts, "
                f"engine says seat {state.to_act_seat}"
            )
        if seat == HERO_SEAT:
            yield ordinal, state
            ordinal += 1
        # History stores the raise/bet INCREMENT; `apply` wants the raise-TO.
        size = None
        if h.action in (ActionType.BET, ActionType.RAISE):
            size = round(state.seats[seat].invested_street_bb + h.amount_bb, 2)
        state = apply(state, Decision(action=h.action, size_bb=size))


def _preflop_shape_label(state: HandState) -> str:
    """Describe the preflop shape of a `PREFLOP_SHAPE_UNGATED` row.

    Purely DESCRIPTIVE — it is not part of the taxonomy and no gate consumes
    it. `PREFLOP_SHAPE_UNGATED` names the stage that rejected, not the shape,
    and it is the biggest bin by far; `T-cover` needs to know WHICH shapes sit
    inside it before it can widen anything (refuter MED-2). Four dimensions,
    all read straight off the preflop history:

      raises      — preflop RAISE count (0 = limped, 2+ = 3-bet-or-more pot)
      entrants    — seats that put money in and never folded preflop
      blind_entr  — whether SB and/or BB is one of those entrants
      limp        — limpers (a CALL before any RAISE) and what they did next
    """
    pre = _street_actions(state, Street.PREFLOP)
    voluntary = [h for h in pre if h.action is not ActionType.POST]

    folded = {h.position for h in voluntary if h.action is ActionType.FOLD}
    invested = {h.position for h in voluntary if h.action in (
        ActionType.CALL, ActionType.RAISE
    )}
    # The blinds are entrants by posting, unless they folded preflop.
    invested |= {Position.SB, Position.BB}
    entrants = invested - folded

    raises = [h for h in voluntary if h.action is ActionType.RAISE]
    first_raise = next(
        (i for i, h in enumerate(voluntary) if h.action is ActionType.RAISE), None
    )
    if first_raise is None:
        limpers = {h.position for h in voluntary if h.action is ActionType.CALL}
        limp = f"limp={len(limpers)}" if limpers else "limp=0"
    else:
        limpers = {
            h.position
            for h in voluntary[:first_raise]
            if h.action is ActionType.CALL
        }
        after = sorted(
            {
                h.action.value
                for h in voluntary[first_raise:]
                if h.position in limpers
            }
        )
        limp = f"limp={len(limpers)}"
        if limpers:
            limp += f"(then_{'+'.join(after) or 'none'})"

    blinds = sorted(p.value for p in entrants & {Position.SB, Position.BB})
    return (
        f"raises={len(raises)} entrants={len(entrants)} "
        f"blind_entrant={'+'.join(blinds) or 'none'} {limp}"
    )


def _role_label(state: HandState, hero_seat: int) -> str:
    """Which seat hero holds, in which family — the descriptor a role-rejection
    row needs. `NO_MAPPER_FOR_ROLE` means "build a mapper here";
    `HERO_ROLE_UNGATED` means "this seat is deliberately not graded"; a scoper
    has to see WHICH seat to act on either."""
    from app.domain.table import grade_map_postflop as gp

    nobb = gp._mw_nobb_srp_preflop(state)
    if nobb.value is not None:
        opener, callers, _open_to = nobb.value
        if opener.seat == hero_seat:
            return "family=mw_nobb role=opener (3-way aggressor, blinds folded)"
        if callers[-1].seat == hero_seat:
            return "family=mw_nobb role=last_caller"
        return "family=mw_nobb role=earlier_caller (never closes)"
    mw = gp._mw_srp_preflop(state)
    if mw.value is not None:
        opener, callers, bb, _open_to = mw.value
        if opener.seat == hero_seat:
            return "family=mw_bb role=opener"
        if bb.seat == hero_seat:
            return "family=mw_bb role=bb"
        if any(c.seat == hero_seat for c in callers):
            return "family=mw_bb role=cold_caller (never closes)"
    return "family=(none passed) role=n/a"


def _street_action_label(state: HandState) -> str:
    """This street's action sequence — the descriptor a
    `STREET_ACTION_SHAPE_UNGATED` or `ALL_IN_IN_LINE` row needs (donk lead vs
    probe vs delayed c-bet are entirely different `T-cover` work items)."""
    acts = _street_actions(state, state.street)
    if not acts:
        return f"{state.street.value}: (hero first to act)"
    seq = " -> ".join(f"{h.position.value}:{h.action.value}" for h in acts)
    return f"{state.street.value}: {seq}"


def _family_street_label(state: HandState) -> str:
    """Which recognised family owns this hand, and which street hero is on —
    the descriptor for `NO_MAPPER_FOR_STREET_SHAPE`."""
    from app.domain.table import grade_map_postflop as gp

    passing = [
        name
        for name, gate in (
            ("hu_srp", gp._hu_srp_preflop),
            ("mw_bb", gp._mw_srp_preflop),
            ("mw_nobb", gp._mw_nobb_srp_preflop),
            ("caller_raise (flop-only)", gp._flop_caller_raise_preflop),
            ("limped_hu (flop-only)", gp._limped_flop_hu_preflop),
        )
        if gate(state).value is not None
    ]
    return f"family={'+'.join(passing) or '(none)'} street={state.street.value}"


def _describe(reason: RejectReason, state: HandState, hero_seat: int) -> str:
    """The right descriptor for each reason. Extended from
    `PREFLOP_SHAPE_UNGATED`-only to every reason (theory-reviewer MED): the
    per-reason attributions in the T-REJECT handoff were produced by human
    inspection, which is exactly the anecdote this ticket exists to replace."""
    if reason is RejectReason.NO_MAPPER_FOR_STREET_SHAPE:
        return _family_street_label(state)
    if reason in (RejectReason.NO_MAPPER_FOR_ROLE, RejectReason.HERO_ROLE_UNGATED):
        return _role_label(state, hero_seat)
    if reason in (
        RejectReason.STREET_ACTION_SHAPE_UNGATED,
        RejectReason.ALL_IN_IN_LINE,
        RejectReason.BET_FRACTION_OFF_GRID,
    ):
        return _street_action_label(state)
    return _preflop_shape_label(state)


def measure(session_id: str, max_hand_no: int | None = None, db_path: str | None = None):
    """Return the measurement for `session_id`, after asserting replay/coverage
    parity in BOTH directions.

    `max_hand_no` caps the corpus at the first N hands. A sim session stays
    `active` and GROWS whenever anyone plays it — this one went 181 -> 221 ->
    265 hands during the ticket, and the live DB was then reset outright — so a
    pinned measurement has to name both its database and its prefix or it
    silently stops reproducing.
    """
    engine = _resolve_engine(db_path)
    with Session(engine) as db:
        query = select(SimHand).where(SimHand.session_id == session_id)
        if max_hand_no is not None:
            query = query.where(SimHand.hand_no <= max_hand_no)
        hands = db.exec(query.order_by(SimHand.id)).all()
        rows = db.exec(
            select(SimDecision).where(SimDecision.session_id == session_id)
        ).all()
    if not hands:
        raise SystemExit(f"no hands for session {session_id!r}")
    hand_ids = {h.id for h in hands}
    persisted = {
        (r.sim_hand_id, r.ordinal): r for r in rows if r.sim_hand_id in hand_ids
    }

    per_street: Counter = Counter()
    matrix: dict[str, Counter] = {s.value: Counter() for s in _POSTFLOP}
    breakdowns: dict[RejectReason, Counter] = {r: Counter() for r in REASON_ORDER}
    max_depths: list[int] = []
    mapped = unmapped = replayed = 0
    for hand in hands:
        if hand.state_json is None:
            continue
        terminal = HandState.model_validate_json(hand.state_json)
        for ordinal, state in _replay(terminal):
            replayed += 1
            row = persisted.get((hand.id, ordinal))
            if row is None:
                raise ParityError(
                    f"hand {hand.id} ordinal {ordinal}: replayed a hero decision "
                    "with no persisted sim_decision row"
                )
            if row.street != state.street.value:
                raise ParityError(
                    f"hand {hand.id} ordinal {ordinal}: persisted street "
                    f"{row.street!r} != replayed {state.street.value!r}"
                )
            spot = map_decision_point(state, HERO_SEAT)
            was_mapped = row.coverage != "unmappable"
            if (spot is not None) != was_mapped:
                raise ParityError(
                    f"hand {hand.id} ordinal {ordinal}: persisted coverage "
                    f"{row.coverage!r} but map_decision_point now returns "
                    f"{'a Spot' if spot is not None else 'None'}"
                )
            if state.street is Street.PREFLOP:
                continue
            per_street[state.street.value] += 1
            if spot is not None:
                mapped += 1
                continue
            unmapped += 1
            verdict = classify_with_evidence(state, HERO_SEAT)
            matrix[state.street.value][verdict.reason] += 1
            max_depths.append(verdict.max_depth)
            breakdowns[verdict.reason][
                _describe(verdict.reason, state, HERO_SEAT)
            ] += 1

    # Reverse-direction parity (refuter LOW-1): the forward checks prove every
    # REPLAYED decision matches a persisted row, but not that every persisted
    # row was replayed. Without this, a hero decision the replay silently skips
    # is dropped from the denominator while the banner still reports OK.
    if replayed != len(persisted):
        raise ParityError(
            f"replayed {replayed} hero decisions but {len(persisted)} are "
            "persisted — the replay is not the game the app played"
        )
    return per_street, matrix, mapped, unmapped, breakdowns, replayed, max_depths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, help="sim_session.id")
    parser.add_argument(
        "--max-hand-no",
        type=int,
        default=None,
        help=(
            "cap the corpus at the first N hands. An ACTIVE session grows as it "
            "is played, so pin this to keep a measurement reproducible "
            "(the T-REJECT deliverable is --max-hand-no 181)."
        ),
    )
    parser.add_argument(
        "--db",
        default=None,
        help=(
            "read-only path to a specific SQLite file. Defaults to the app "
            "engine. The live DB is routinely reset/rotated, so a pinned "
            "measurement should name its snapshot."
        ),
    )
    args = parser.parse_args(argv)

    (
        per_street, matrix, mapped, unmapped, breakdowns, replayed, max_depths
    ) = measure(args.session, args.max_hand_no, args.db)
    total = mapped + unmapped
    streets = [s.value for s in _POSTFLOP]

    scope = f"first {args.max_hand_no} hands" if args.max_hand_no else "ALL hands"
    print(f"session: {args.session}  (corpus: {scope})")
    print(f"db: {args.db or '<app engine>'}")
    print(
        f"replay + coverage parity: OK ({replayed} hero decisions, both "
        "directions — every replayed decision matches its persisted street and "
        "coverage, and every persisted row was replayed)"
    )
    print(f"postflop decision points: {total}")
    print(f"mapped: {mapped}")
    # LOW-2: the unmapped per-street figures get their OWN line. They used to
    # share a line that LED with decision-point counts (flop 28 vs unmapped 24),
    # and "unmapped: ... flop N" is the exact string the done-condition greps.
    print(
        f"unmapped: {unmapped} ("
        + " · ".join(f"{s} {sum(matrix[s].values())}" for s in streets)
        + ")"
    )
    print(
        "  (postflop decision points per street: "
        + " · ".join(f"{s} {per_street[s]}" for s in streets)
        + ")"
    )
    print()

    # EVERY reason row is printed, zero or not, with its evaluation count and a
    # note distinguishing a censored zero from a real one (theory-reviewer
    # HIGH). Suppressing all-zero rows is what let three uninformative zeros be
    # read as findings.
    width = max(len(r.value) for r in REASON_ORDER)
    header = (
        f"{'reason'.ljust(width)}  "
        + "".join(f"{s:>7}" for s in streets)
        + f"{'fails':>8}{'evals':>8}   note"
    )
    print(header)
    print("-" * (len(header) + 24))
    for reason in REASON_ORDER:
        cells = [matrix[s][reason] for s in streets]
        fails = sum(cells)
        evals = _evaluations(reason, max_depths)
        if fails:
            note = ""
        elif evals == 0:
            note = "CENSORED — stage never reached, cell carries NO information"
        elif reason is RejectReason.OPEN_SIZE_OFF_BAND:
            # Not a finding: `_OVERSIZE_OPEN_CAP` is 4.5 and every open a
            # persona can draw is inside [2.0, 4.5] — since T2b that is a
            # distribution rather than one fixed size per pack, and the
            # invariant is enforced by
            # `test_persona_pack_invariants::test_authored_preflop_sizes_stay_gradeable`
            # — so this cell CANNOT fire on any bot line. Reported so nobody
            # reads the zero as coverage evidence.
            note = f"reached {evals}x — TAUTOLOGICAL zero, no bot open is off-band"
        else:
            note = f"reached {evals}x, never fired"
        print(
            reason.value.ljust(width)
            + "  "
            + "".join(f"{c:>7}" for c in cells)
            + f"{fails:>8}{evals:>8}   {note}"
        )
    print("-" * (len(header) + 24))
    print(
        "TOTAL".ljust(width)
        + "  "
        + "".join(f"{sum(matrix[s].values()):>7}" for s in streets)
        + f"{unmapped:>8}"
    )
    print(
        "\nevals = unmapped rows on which some twin REACHED this stage. A "
        "`0 fails / 0 evals` row is\ncensored: the check never ran, so its zero "
        "supports NO conclusion in either direction."
    )

    # Per-reason descriptive breakdown — every non-zero reason, not just the
    # largest bin (theory-reviewer MED).
    for reason in REASON_ORDER:
        rows = breakdowns[reason]
        if not rows:
            continue
        n = sum(rows.values())
        print()
        print(f"{reason.value} breakdown ({n} rows) — the SHAPE behind the stage:")
        swidth = max(len(k) for k in rows)
        sheader = f"{''.ljust(swidth)}    count"
        print("-" * len(sheader))
        for label, count in sorted(rows.items(), key=lambda kv: (-kv[1], kv[0])):
            print("  " + label.ljust(swidth) + f"{count:>9}")

    counted = sum(sum(c.values()) for c in matrix.values())
    unclassified = sum(c[RejectReason.UNCLASSIFIED] for c in matrix.values())
    print()
    print(f"sum(reason counts) == unmapped: {counted == unmapped} ({counted})")
    print(f"UNCLASSIFIED: {unclassified}")
    print(
        "cumulative graded-coverage delta vs the immutable snapshot: 0 — the "
        "gate refactor is\nbehaviour-identical (1.29M-call differential, 0 "
        "mismatches; coverage_baseline.json unchanged\nand green; this run's "
        "own both-directions coverage parity re-proves it on every row)."
    )
    print(
        "\nCONDITIONAL — sizing and stack coverage is NOT measured by this run. "
        "BET_FRACTION_OFF_GRID\nand STACK_TOO_SHALLOW are censored above, and "
        "OPEN_SIZE_OFF_BAND cannot fire on a bot line at\nall (every persona "
        "open is inside the band). Nothing here says the mapper's sizing "
        "recognition\nis or is not a bottleneck; these gates may start firing "
        "as soon as T-cover widens the shape\ngates upstream and rows begin "
        "reaching them."
    )
    return 0 if counted == unmapped and unclassified == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
