"""Map a live Simulate POSTFLOP decision point to a canonical gradeable Spot.

Split out of `grade_map` (S10) so postflop range/coverage work (R5: the
openable call/fold/raise chart + widened postflop grading) owns this module
cleanly. Pure domain: no web/DB imports (enforced by test_domain_purity).

HEAD ships **19 postflop mappers** in five preflop-shape families (this
docstring used to claim "ONLY the HU single-raised-pot continuation line",
which went stale around M4-M7 and misread two later analyses):

  * HU single-raised pot (`_hu_srp_preflop`) — flop c-bet / vs c-bet / vs
    check-raise, turn barrel / vs turn bet, river barrel / vs river bet.
  * 3-/4-way SRP with the BB in (`_mw_srp_preflop`) — hero as BB defender
    (`map_mw_*_vs_*`) or as the opener barrelling (`map_mw_*_barrel`,
    `map_mw_flop_cbet`), flop/turn/river.
  * no-BB 3-way SRP (`_mw_nobb_srp_preflop`) — hero the LATER cold-caller
    closing, flop/turn/river (`map_mw_caller_vs_*`).
  * opener + one cold-caller [+ BB] (`_flop_caller_raise_preflop`) — hero the
    opener facing the caller's flop raise. **Flop only.**
  * HU limped pot (`_limped_flop_hu_preflop`) — lead / vs lead. **Flop only.**

So "multiway" and "limped pot" are NOT reasons a decision goes unmapped; they
are supported shapes that reject for some FURTHER reason. Anything outside
these five families returns None ("no baseline yet") — never a fabricated or
truncated postflop spot. `grade_map_reject.classify_postflop_rejection` names
the reason for a given None, reading the typed diagnostics the gates and the
internal `_map_*` twins below already produce (owner decision B1: one source of
truth, so the measured reason counts cannot drift from the live grader). Every
PUBLIC `map_*` keeps its `(state, hero_seat) -> Spot | None` signature; the
diagnostic is internal.

Canonical-shape parity: each mapper mirrors its `scenarios.py` builder
(`build_cbet_spot` / `build_turn_barrel_spot` / `build_vs_turn_bet_spot` /
`build_river_barrel_spot` / `build_vs_river_bet_spot`) field-by-field with the
live board / cards / stacks / pot substituted in and the ranges resolved
through the same content entries — so a mapped Spot is always one the existing
graders were built for. The turn/river mappers gate 2–3 SEQUENTIAL streets of
recognized bet sizing (in-band open, recognized-fraction c-bet AND called,
recognized-fraction turn barrel AND called for river — see
`RECOGNIZED_BET_FRACS`) and return None on ANY doubt.
"""

from __future__ import annotations

from app.domain.scenarios import _combos_for, _find_entry
from app.domain.spot import (
    ActionType,
    GameConfig,
    Hero,
    LegalAction,
    NodeContext,
    PlayerState,
    PlayerStatus,
    Position,
    Spot,
    Stakes,
    Street,
)
from app.domain.table.engine import HandState
from app.domain.table.grade_map_common import _BLIND_POSITIONS, _EPS, _street_actions
from app.domain.table.grade_map_preflop import _OVERSIZE_OPEN_CAP
from app.domain.table.grade_map_reject import (
    GateResult,
    MapResult,
    RejectReason,
    StreetResult,
    gate_fail,
    map_fail,
    street_fail,
)
from app.domain.table.sizing import (
    FACING_RAISE_MULTS,
    POSTFLOP_BET_FRACS,
    RECOGNIZED_BET_FRACS,
)


def map_flop_cbet(state: HandState, hero_seat: int) -> Spot | None:
    """HU flop c-bet: hero opened preflop at the canonical size, the BB (and
    only the BB) called, and the BB has checked the flop to the hero."""
    return _map_flop_cbet(state, hero_seat).spot


def _map_flop_cbet(state: HandState, hero_seat: int) -> MapResult:
    """Internal twin of `map_flop_cbet` — same gates, plus the reject reason.

    T-REJECT folded this mapper's hand-rolled preflop block onto the shared
    `_hu_srp_preflop` gate: the two were already equivalent for hero-as-opener
    (live-2 + villain-is-an-IN-BB + one in-band raise by hero + the BB's lone
    call), and one source of truth is what stops the reason counts drifting.
    """
    hero = state.seats[hero_seat]
    if len(state.board) != 3:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _hu_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, villain, open_to = gate.value
    if opener.seat != hero_seat:
        return map_fail(RejectReason.HERO_ROLE_UNGATED)  # hero isn't the PFR
    if not _bb_checked_only(state, Street.FLOP):
        return map_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)

    # Ranges come from the SAME content entries build_cbet_spot resolves —
    # never the builder's literal fallback strings (that would fabricate).
    ranges = _srp_ranges(hero.position)
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)  # content gap, not a shape
    hero_range, villain_range = ranges

    pot = _live_pot(state)
    if abs(pot - (2 * open_to + 0.5)) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)  # off-shape dead money
    _fsmall, _fbig = POSTFLOP_BET_FRACS["flop"]  # single source (shared w/ the canonical-bet gate)
    small = round(_fsmall * pot, 1)
    big = round(_fbig * pot, 1)
    hero_remaining = hero.stack_bb
    villain_remaining = villain.stack_bb
    if hero_remaining < big or villain_remaining <= 0:
        return map_fail(RejectReason.STACK_TOO_SHALLOW)
    effective = round(min(hero_remaining, villain_remaining), 2)
    spr = round(effective / pot, 1)

    players = _players(state, hero_seat)
    return MapResult(Spot(
        game=GameConfig(stakes=Stakes(sb=1.0, bb=2.0), table_size=9, max_buyin_bb=200.0),
        street=Street.FLOP,
        board=list(state.board),
        pot_bb=pot,
        hero=Hero(
            position=hero.position,
            hole_cards=hero.hole_cards,
            stack_bb=hero_remaining,
        ),
        players=players,
        effective_stack_bb=effective,
        spr=spr,
        action_history=list(state.action_history),
        to_act=hero.position,
        legal_actions=[
            LegalAction(action=ActionType.CHECK),
            LegalAction(action=ActionType.BET, min_bb=small, max_bb=hero_remaining),
            LegalAction(action=ActionType.BET, min_bb=big, max_bb=hero_remaining),
        ],
        node_context=[NodeContext.CBET],
        facing=Position.BB,
        hero_range=hero_range,
        villain_range=villain_range,
    ), None)


# --- R5: turn/river mappers (HU SRP continuation line only) -----------------
# Each mapper re-verifies the FULL prior line street by street. A recognized
# bet is any `RECOGNIZED_BET_FRACS` pot-fraction (M1-L4: the whole persona bet
# grid 0.33/0.5/0.75/1.0/1.5, every street — RES-I §3 L4 widened this from the
# street's two `POSTFLOP_BET_FRACS` hero sizes, which silently un-mapped every
# bot 0.5/1.0-pot flop c-bet). Any other size (or an uncalled bet, a raise, a
# lead, a check-back) ⇒ None. The ACTUAL bet amount always flows into the pot
# math and the built spot's CALL leg, so the graders price the TRUE live
# pot-fraction — recognition never collapses a size into another bucket
# (RES-I §5 HIGH flag).


# Fraction-recognition tolerance. Hero's offered sizes are `round(f*pot, 1)`
# (up to 0.05 off the exact fraction) but BOT bets are `round(f*pot, 2)`
# (personas_postflop, ≤0.005 off) — with the old exact-match-vs-1dp check a
# tag's 0.33-pot c-bet of 1.82bb never equalled the canonical 1.8bb, so every
# villain-bet-gated facing mapper was DEAD in live play (design-review HIGH:
# 0 postflop facing offers in 1,123 hands). 0.06bb accepts both roundings;
# the nearest wrong fraction (0.33 vs 0.5 vs 0.75 pot) is whole bbs away at
# any realistic pot, so no ambiguity.
_CANON_BET_TOL = 0.06


def _is_canonical_bet(amount_bb: float, pot_before: float, street: Street) -> bool:
    """M1-L4: recognition runs against the full persona grid on every street
    (`street` is kept for call-site documentation; the grid is street-uniform).
    Adjacent grid fractions are ≥0.17·pot apart, so at any postflop pot
    (≥4.5bb) the 0.06bb tolerance can never match two fractions at once."""
    del street
    return any(
        abs(amount_bb - f * pot_before) <= _CANON_BET_TOL
        for f in RECOGNIZED_BET_FRACS
    )


def _hu_srp_preflop(state: HandState) -> GateResult:
    """Gate: HU single-raised pot. One non-blind opener raised to a size in
    the open band [min-raise 2.0 .. `_OVERSIZE_OPEN_CAP`], the BB (and only the BB)
    called, everyone else folded. Returns `GateResult` whose `.value` is
    (opener_seat_state, bb_seat_state, open_to) — open_to is the ACTUAL open
    size (downstream pot math depends on it: the BB called that amount) — or
    a `.reason` (T-REJECT: the diagnostic the classifier reads, so no gate is
    ever re-implemented outside this module)."""
    live = [s for s in state.seats if s.status is not PlayerStatus.FOLDED]
    if len(live) != 2:
        # multiway (or fold-out) — never HU-canonical
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    bb = next((s for s in live if s.position is Position.BB), None)
    opener = next((s for s in live if s.position is not Position.BB), None)
    if bb is None or opener is None or opener.position in _BLIND_POSITIONS:
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    if bb.status is not PlayerStatus.IN or opener.status is not PlayerStatus.IN:
        # an all-in anywhere in the line is off-shape (live ⇒ not FOLDED)
        return gate_fail(RejectReason.ALL_IN_IN_LINE)
    pre = _street_actions(state, Street.PREFLOP)
    if any(
        h.action not in (ActionType.FOLD, ActionType.RAISE, ActionType.CALL)
        for h in pre
    ):
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    raises = [h for h in pre if h.action is ActionType.RAISE]
    calls = [h for h in pre if h.action is ActionType.CALL]
    if len(raises) != 1 or raises[0].position is not opener.position:
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    if len(calls) != 1 or calls[0].position is not Position.BB:
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    open_to = raises[0].amount_bb
    # Engine history stores the raise INCREMENT; a non-blind opener's increment
    # equals the raise-TO size. Same [min-raise 2.0 .. `_OVERSIZE_OPEN_CAP`]
    # band as grade_map_preflop._map_vs_open (R2): a tolerant band rather than an
    # exact per-seat canonical gate (2.5 for HJ/CO/BTN), which would silently
    # zero turn/river coverage at every seat where a bot's open did not match
    # the canonical to the decimal.
    # T-REJECT stale-comment fix: this used to read "[2.0 .. standard 3.0] ...
    # oversized persona opens (station 3.5 / fish 4.0 / maniac 4.5) still
    # return None". `_OVERSIZE_OPEN_CAP` is **4.5**, so EVERY persona open is
    # in band and this gate rejects none of them — measured as
    # `OPEN_SIZE_OFF_BAND == 0` over the 181-hand corpus. The comment, not the
    # code, was wrong; the band is unchanged.
    # T2b: the justification above used to say the personas open a FIXED
    # `open_bb` from every seat, and to enumerate the four sizes. Neither is
    # true any more — the three regulars draw the open from a per-seat mix and
    # the other three from a flat one, spanning 2.5 to 4.5. Still all in band,
    # so the code and the conclusion are unchanged; only the reason is, and it
    # is now the tolerance itself rather than a roster fact that keeps moving.
    if not (2.0 - _EPS <= open_to <= _OVERSIZE_OPEN_CAP + _EPS):
        return gate_fail(RejectReason.OPEN_SIZE_OFF_BAND)
    return GateResult((opener, bb, open_to), None)


def _check_bet_call(
    state: HandState, street: Street, opener_pos: Position, pot_before: float
) -> StreetResult:
    """Gate: this street went EXACTLY check(BB) → bet(opener, canonical size)
    → call(BB). `.value` is the bet size, else a `.reason`."""
    acts = _street_actions(state, street)
    if len(acts) != 3:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    chk, bet, call = acts
    if chk.action is not ActionType.CHECK or chk.position is not Position.BB:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if bet.action is not ActionType.BET or bet.position is not opener_pos:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if call.action is not ActionType.CALL or call.position is not Position.BB:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if not _is_canonical_bet(bet.amount_bb, pot_before, street):
        return street_fail(RejectReason.BET_FRACTION_OFF_GRID)
    if abs(call.amount_bb - bet.amount_bb) > _EPS:
        return street_fail(RejectReason.ALL_IN_IN_LINE)  # short call = all-in
    return StreetResult(bet.amount_bb, None)


def _check_bet(
    state: HandState, street: Street, opener_pos: Position, pot_before: float
) -> StreetResult:
    """Gate: this street went EXACTLY check(BB) → bet(opener, canonical size),
    hero (the BB) now facing it. `.value` is the bet size, else a `.reason`."""
    acts = _street_actions(state, street)
    if len(acts) != 2:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    chk, bet = acts
    if chk.action is not ActionType.CHECK or chk.position is not Position.BB:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if bet.action is not ActionType.BET or bet.position is not opener_pos:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if not _is_canonical_bet(bet.amount_bb, pot_before, street):
        return street_fail(RejectReason.BET_FRACTION_OFF_GRID)
    return StreetResult(bet.amount_bb, None)


def _check_bet_raise(
    state: HandState, street: Street, opener_pos: Position, pot_before: float
) -> StreetResult:
    """Gate: this street went EXACTLY check(BB) → bet(opener=hero, canonical
    size) → raise(BB), hero now facing the check-raise. `.value` is
    (cbet, raise_to), else a `.reason`.

    The check-raise SIZE is deliberately un-bucketed: personas raise on a
    continuous pot-fraction grid (`raise_to = bet + f*(pot+to_call)`), so a
    canonical-size gate would zero live coverage; the graders price any faced
    amount continuously. The raise must be COMPLETE — an incomplete all-in
    raise leaves the raiser ALLIN, which `_hu_srp_preflop` already rejects."""
    acts = _street_actions(state, street)
    if len(acts) != 3:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    chk, bet, cr = acts
    if chk.action is not ActionType.CHECK or chk.position is not Position.BB:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if bet.action is not ActionType.BET or bet.position is not opener_pos:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if not _is_canonical_bet(bet.amount_bb, pot_before, street):
        return street_fail(RejectReason.BET_FRACTION_OFF_GRID)
    if cr.action is not ActionType.RAISE or cr.position is not Position.BB:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    # BB checked, so nothing invested this street: the history INCREMENT is the
    # full raise-TO.
    raise_to = cr.amount_bb
    if raise_to <= bet.amount_bb + _EPS:
        # degenerate: a "raise" no bigger than the bet
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    return StreetResult((bet.amount_bb, raise_to), None)


def _bb_checked_only(state: HandState, street: Street) -> bool:
    """Gate: this street's only action so far is the BB's check to the hero."""
    acts = _street_actions(state, street)
    return (
        len(acts) == 1
        and acts[0].action is ActionType.CHECK
        and acts[0].position is Position.BB
    )


def _srp_ranges(opener_pos: Position) -> tuple[str, str] | None:
    """(opener RFI raise range, BB blind-defense call range) from the SAME
    content entries the builders resolve — never their literal fallbacks."""
    rfi_entry = _find_entry(NodeContext.RFI, opener_pos, None)
    bd_entry = _find_entry(NodeContext.BLIND_DEFENSE, Position.BB, opener_pos)
    opener_range = _combos_for(rfi_entry, ActionType.RAISE)
    bb_range = _combos_for(bd_entry, ActionType.CALL)
    if not opener_range or not bb_range:
        return None
    return opener_range, bb_range


def _players(state: HandState, hero_seat: int) -> list[PlayerState]:
    return [
        PlayerState(
            position=s.position,
            stack_bb=s.stack_bb,
            status=s.status,
            is_hero=s.seat == hero_seat,
        )
        for s in state.seats
    ]


def _live_pot(state: HandState) -> float:
    return round(sum(s.invested_total_bb for s in state.seats), 2)


def _line_status_reason(seats) -> RejectReason:
    """Name a "this entrant is not IN" gate failure. ALLIN is its own reason;
    an entrant who has since FOLDED is just a shape the family doesn't gate."""
    if any(s.status is PlayerStatus.ALLIN for s in seats):
        return RejectReason.ALL_IN_IN_LINE
    return RejectReason.PREFLOP_SHAPE_UNGATED


def _spot_or_shallow(spot: Spot | None) -> MapResult:
    """Wrap a spot BUILDER's answer. `_barrel_spot` / `_faced_bet_spot` /
    `_limped_lead_spot` are past every shape gate by the time they run and
    reject on exactly one thing: stacks too short for the canonical bet/raise
    buckets they must offer."""
    if spot is None:
        return map_fail(RejectReason.STACK_TOO_SHALLOW)
    return MapResult(spot, None)


def _barrel_spot(
    state: HandState,
    hero_seat: int,
    villain,
    pot: float,
    street: Street,
    ctx: NodeContext,
    hero_range: str,
    villain_range: str,
) -> Spot | None:
    """Hero = aggressor deciding check / bet small / bet big (mirrors
    build_turn_barrel_spot / build_river_barrel_spot legal-action shape)."""
    hero = state.seats[hero_seat]
    small_frac, big_frac = POSTFLOP_BET_FRACS[street.value]
    small = round(small_frac * pot, 1)
    big = round(big_frac * pot, 1)
    hero_remaining = hero.stack_bb
    villain_remaining = villain.stack_bb
    if hero_remaining < big or villain_remaining <= 0:
        return None  # too shallow for the canonical small/big bet buckets
    effective = round(min(hero_remaining, villain_remaining), 2)
    return Spot(
        game=GameConfig(stakes=Stakes(sb=1.0, bb=2.0), table_size=9, max_buyin_bb=200.0),
        street=street,
        board=list(state.board),
        pot_bb=pot,
        hero=Hero(
            position=hero.position, hole_cards=hero.hole_cards, stack_bb=hero_remaining
        ),
        players=_players(state, hero_seat),
        effective_stack_bb=effective,
        spr=round(effective / pot, 1),
        action_history=list(state.action_history),
        to_act=hero.position,
        legal_actions=[
            LegalAction(action=ActionType.CHECK),
            LegalAction(action=ActionType.BET, min_bb=small, max_bb=hero_remaining),
            LegalAction(action=ActionType.BET, min_bb=big, max_bb=hero_remaining),
        ],
        node_context=[ctx],
        facing=Position.BB,
        hero_range=hero_range,
        villain_range=villain_range,
    )


def _faced_bet_spot(
    state: HandState,
    hero_seat: int,
    villain,
    pot: float,
    bet: float,
    street: Street,
    ctx: NodeContext,
    hero_range: str,
    villain_range: str,
    mults: tuple[float, float] = FACING_RAISE_MULTS["raise"],
    call_amt: float | None = None,
) -> Spot | None:
    """Hero facing a bet (or check-raise): fold / call / raise-small / raise-big
    (mirrors build_vs_turn_bet_spot / build_vs_river_bet_spot). `bet` is the
    raise-SIZING base (the faced bet, or the full raise-to for a check-raise);
    `call_amt` is the INCREMENTAL amount hero owes — defaults to `bet` (correct
    when hero has nothing invested this street), but a check-raise caller must
    pass `raise_to - hero's own bet` or pot-odds and `faced_bet_bucket` corrupt.

    N4b: two RAISE legs from `mults` (small first). Each leg clamps to hero's
    stack; legs collapse to one when big <= small after the clamp (short-stack).
    The affordability gate keys on the SMALL leg (widened from the old flat-3x
    single leg)."""
    hero = state.seats[hero_seat]
    small_mult, big_mult = mults
    raise_small = round(small_mult * bet, 1)
    raise_big = round(big_mult * bet, 1)
    hero_remaining = hero.stack_bb
    villain_remaining = villain.stack_bb
    # The legs are raise-TO totals, so affordability keys on hero's all-in-TO
    # (chips behind + already invested THIS street), not chips behind alone.
    # Zero-invested callers (vs_cbet, vs turn/river bet: hero=BB pre-decision)
    # are byte-identical; the check-raise-defense hero has the c-bet invested,
    # and gating on stack alone would silently un-map legal mid-stack raises
    # (refuter-on-diff HIGH).
    hero_raise_ceiling = round(hero.invested_street_bb + hero.stack_bb, 2)
    if hero_raise_ceiling < raise_small or villain_remaining <= 0:
        return None  # too shallow for even the small canonical raise bucket
    # Floor (not round) the clamped big leg to 1dp: stays <= the all-in ceiling
    # AND keeps both button labels at the same 1-dp precision (design-review LOW).
    raise_big = round(int(min(raise_big, hero_raise_ceiling) * 10 + 1e-9) / 10, 1)
    raise_legs = [raise_small]
    if raise_big - raise_small > _EPS:
        raise_legs.append(raise_big)
    effective = round(min(hero_remaining, villain_remaining), 2)
    return Spot(
        game=GameConfig(stakes=Stakes(sb=1.0, bb=2.0), table_size=9, max_buyin_bb=200.0),
        street=street,
        board=list(state.board),
        pot_bb=pot,
        hero=Hero(
            position=hero.position, hole_cards=hero.hole_cards, stack_bb=hero_remaining
        ),
        players=_players(state, hero_seat),
        effective_stack_bb=effective,
        spr=round(effective / pot, 1),
        action_history=list(state.action_history),
        to_act=hero.position,
        legal_actions=[
            LegalAction(action=ActionType.FOLD),
            LegalAction(action=ActionType.CALL, min_bb=call_amt if call_amt is not None else bet),
            *(
                LegalAction(action=ActionType.RAISE, min_bb=leg, max_bb=hero_raise_ceiling)
                for leg in raise_legs
            ),
        ],
        node_context=[ctx],
        facing=villain.position,
        hero_range=hero_range,
        villain_range=villain_range,
    )


def map_flop_vs_cbet(state: HandState, hero_seat: int) -> Spot | None:
    """HU vs flop c-bet (N4b): hero = BB who called a canonical open, checked
    the flop, and now faces the opener's canonical c-bet. Hero's RAISE here is
    a check-raise, so the legs use the flop-scoped check_raise mults
    (RES-B :148: 2.5x/3.5x the c-bet)."""
    return _map_flop_vs_cbet(state, hero_seat).spot


def _map_flop_vs_cbet(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 3 or hero.position is not Position.BB:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _hu_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, bb, osize = gate.value
    if bb.seat != hero_seat:
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    flop_pot = round(2 * osize + 0.5, 2)
    faced = _check_bet(state, Street.FLOP, opener.position, flop_pot)
    if faced.value is None:
        return map_fail(faced.reason)
    cbet = faced.value
    pot = _live_pot(state)
    if abs(pot - (flop_pot + cbet)) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    ranges = _srp_ranges(opener.position)
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)
    opener_range, bb_range = ranges
    return _spot_or_shallow(_faced_bet_spot(
        state, hero_seat, opener, pot, cbet,
        Street.FLOP, NodeContext.VS_CBET, bb_range, opener_range,
        mults=FACING_RAISE_MULTS["check_raise"],
    ))


def map_flop_vs_check_raise(state: HandState, hero_seat: int) -> Spot | None:
    """HU vs flop check-raise (N4b): hero opened canonically, c-bet the flop at
    a canonical size, and the BB check-raised (any complete size). Hero's
    re-raise is a plain facing-bet raise (RES-B :149: 2.5x/3.0x the raise-to).
    CALL is the INCREMENTAL amount hero owes (raise_to - cbet) — hero already
    has the c-bet invested this street (mirrors build_check_raise_spot)."""
    return _map_flop_vs_check_raise(state, hero_seat).spot


def _map_flop_vs_check_raise(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 3 or hero.position in _BLIND_POSITIONS:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _hu_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, bb, osize = gate.value
    if opener.seat != hero_seat:
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    flop_pot = round(2 * osize + 0.5, 2)
    faced = _check_bet_raise(state, Street.FLOP, hero.position, flop_pot)
    if faced.value is None:
        return map_fail(faced.reason)
    cbet, raise_to = faced.value
    pot = _live_pot(state)
    if abs(pot - (flop_pot + cbet + raise_to)) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    ranges = _srp_ranges(hero.position)
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)
    opener_range, bb_range = ranges
    return _spot_or_shallow(_faced_bet_spot(
        state, hero_seat, bb, pot, raise_to,
        Street.FLOP, NodeContext.VS_CHECK_RAISE, opener_range, bb_range,
        mults=FACING_RAISE_MULTS["raise"],
        call_amt=round(raise_to - cbet, 2),
    ))


def map_turn_barrel(state: HandState, hero_seat: int) -> Spot | None:
    """HU turn barrel: hero opened canonically, c-bet the flop at a canonical
    size and got called, and the BB has checked the turn to the hero."""
    return _map_turn_barrel(state, hero_seat).spot


def _map_turn_barrel(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 4 or hero.position in _BLIND_POSITIONS:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _hu_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, bb, osize = gate.value
    if opener.seat != hero_seat:
        # hero must be the opener; BB shapes go to map_vs_turn_bet
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    flop_pot = round(2 * osize + 0.5, 2)
    flop = _check_bet_call(state, Street.FLOP, hero.position, flop_pot)
    if flop.value is None:
        return map_fail(flop.reason)
    cbet = flop.value
    if not _bb_checked_only(state, Street.TURN):
        return map_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    pot = _live_pot(state)
    if abs(pot - (flop_pot + 2 * cbet)) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    ranges = _srp_ranges(hero.position)
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)
    return _spot_or_shallow(_barrel_spot(
        state, hero_seat, bb, pot, Street.TURN, NodeContext.TURN_BARREL, *ranges
    ))


def map_vs_turn_bet(state: HandState, hero_seat: int) -> Spot | None:
    """HU vs turn bet: hero = BB who called a canonical open and a canonical
    flop c-bet, checked the turn, and now faces the opener's canonical bet."""
    return _map_vs_turn_bet(state, hero_seat).spot


def _map_vs_turn_bet(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 4 or hero.position is not Position.BB:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _hu_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, bb, osize = gate.value
    if bb.seat != hero_seat:
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    flop_pot = round(2 * osize + 0.5, 2)
    flop = _check_bet_call(state, Street.FLOP, opener.position, flop_pot)
    if flop.value is None:
        return map_fail(flop.reason)
    cbet = flop.value
    turn_pot = round(flop_pot + 2 * cbet, 2)
    turn = _check_bet(state, Street.TURN, opener.position, turn_pot)
    if turn.value is None:
        return map_fail(turn.reason)
    tbet = turn.value
    pot = _live_pot(state)
    if abs(pot - (turn_pot + tbet)) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    ranges = _srp_ranges(opener.position)
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)
    opener_range, bb_range = ranges
    return _spot_or_shallow(_faced_bet_spot(
        state, hero_seat, opener, pot, tbet,
        Street.TURN, NodeContext.VS_TURN_BET, bb_range, opener_range,
    ))


def map_river_barrel(state: HandState, hero_seat: int) -> Spot | None:
    """HU river barrel: hero opened, c-bet the flop AND barreled the turn at
    canonical sizes, called both times; the BB has checked the river."""
    return _map_river_barrel(state, hero_seat).spot


def _map_river_barrel(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 5 or hero.position in _BLIND_POSITIONS:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _hu_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, bb, osize = gate.value
    if opener.seat != hero_seat:
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    flop_pot = round(2 * osize + 0.5, 2)
    flop = _check_bet_call(state, Street.FLOP, hero.position, flop_pot)
    if flop.value is None:
        return map_fail(flop.reason)
    cbet = flop.value
    turn_pot = round(flop_pot + 2 * cbet, 2)
    turn = _check_bet_call(state, Street.TURN, hero.position, turn_pot)
    if turn.value is None:
        return map_fail(turn.reason)
    tbet = turn.value
    if not _bb_checked_only(state, Street.RIVER):
        return map_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    pot = _live_pot(state)
    if abs(pot - (turn_pot + 2 * tbet)) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    ranges = _srp_ranges(hero.position)
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)
    return _spot_or_shallow(_barrel_spot(
        state, hero_seat, bb, pot, Street.RIVER, NodeContext.RIVER_BARREL, *ranges
    ))


def map_vs_river_bet(state: HandState, hero_seat: int) -> Spot | None:
    """HU vs river bet: hero = BB who called the open, the flop c-bet AND the
    turn barrel (all canonical), checked the river, and now faces the opener's
    canonical river bet."""
    return _map_vs_river_bet(state, hero_seat).spot


def _map_vs_river_bet(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 5 or hero.position is not Position.BB:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _hu_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, bb, osize = gate.value
    if bb.seat != hero_seat:
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    flop_pot = round(2 * osize + 0.5, 2)
    flop = _check_bet_call(state, Street.FLOP, opener.position, flop_pot)
    if flop.value is None:
        return map_fail(flop.reason)
    cbet = flop.value
    turn_pot = round(flop_pot + 2 * cbet, 2)
    turn = _check_bet_call(state, Street.TURN, opener.position, turn_pot)
    if turn.value is None:
        return map_fail(turn.reason)
    tbet = turn.value
    river_pot = round(turn_pot + 2 * tbet, 2)
    river = _check_bet(state, Street.RIVER, opener.position, river_pot)
    if river.value is None:
        return map_fail(river.reason)
    rbet = river.value
    pot = _live_pot(state)
    if abs(pot - (river_pot + rbet)) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    ranges = _srp_ranges(opener.position)
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)
    opener_range, bb_range = ranges
    return _spot_or_shallow(_faced_bet_spot(
        state, hero_seat, opener, pot, rbet,
        Street.RIVER, NodeContext.VS_RIVER_BET, bb_range, opener_range,
    ))


# --- N5/M6: 3- and 4-way multiway BB-defense line ("minimum honest MW") ----
# ONE multiway family: hero = BB defender in a 3-way (N5) or 4-way (M6)
# single-raised pot (opener + one/two non-blind cold-callers + BB), facing
# the OPENER's canonical c-bet/barrel AFTER every cold-caller has already
# responded — hero CLOSES, verified from the ACTION ORDER of the street (the
# gates require the exact check(BB) -> bet(opener) -> respond(every caller)
# sequence; RES-H §1.2 re-proved "BB closes" is shape-dependent, never a
# positional rule). Any spot with a live player still to act behind hero, or
# a 5+-way field (RES-H §2.4 caps the calibrated tier at 4-way), stays "no
# baseline yet" (None). The cold-callers' VS_RFI call entries are mapping
# GATES only (never a grader input — grade_vs_* consume ONE villain_range,
# the aggressor's; `_apply_multiway` is the deliberate multiway correction).
# A caller folding to a bet degrades the field with his dead money correctly
# in the pot. Effective stack is min(hero, opener) — callers' stacks are
# ignored, an accepted simplification of the MW SPR. Everything else —
# limped pots, donk leads, caller raises, delayed c-bets — returns None.


def _mw_srp_preflop(state: HandState) -> GateResult:
    """Gate: 3- or 4-way single-raised pot. One non-blind opener at an in-band
    open, one or two non-blind cold-callers (M6 widened from exactly one), the
    BB called, SB folded. Entrants are derived from the PREFLOP actions (not
    current statuses — a caller may legitimately have folded to a later
    postflop bet, leaving his dead money in the pot). Opener + BB must still
    be IN; every caller must be IN or postflop-FOLDED (never all-in); nobody
    else may be live. Three-plus cold-callers (5+-way) is past the calibrated
    tier (RES-H §2.4) -> None. `.value` is (opener, callers, bb, open_to) —
    `callers` a tuple in preflop call order — else a `.reason`."""
    pre = _street_actions(state, Street.PREFLOP)
    if any(
        h.action not in (ActionType.FOLD, ActionType.RAISE, ActionType.CALL)
        for h in pre
    ):
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    raises = [h for h in pre if h.action is ActionType.RAISE]
    calls = [h for h in pre if h.action is ActionType.CALL]
    if len(raises) != 1 or len(calls) not in (2, 3):
        # not an SRP, or 5+-way (3+ cold-callers) — no baseline
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    opener_pos = raises[0].position
    caller_pos = [c.position for c in calls if c.position is not Position.BB]
    if len(caller_pos) != len(calls) - 1 or len(set(caller_pos)) != len(caller_pos):
        # BB didn't call, or a duplicate caller (limp-then-call)
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    if opener_pos in _BLIND_POSITIONS or any(
        p in _BLIND_POSITIONS for p in caller_pos
    ):
        # blind entrants (SB open/complete, BB raise) are off-shape
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    opener = next((s for s in state.seats if s.position is opener_pos), None)
    callers = tuple(
        s for p in caller_pos for s in state.seats if s.position is p
    )
    bb = next((s for s in state.seats if s.position is Position.BB), None)
    if opener is None or len(callers) != len(caller_pos) or bb is None:
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    if opener.status is not PlayerStatus.IN or bb.status is not PlayerStatus.IN:
        return gate_fail(_line_status_reason((opener, bb)))
    if any(c.status not in (PlayerStatus.IN, PlayerStatus.FOLDED) for c in callers):
        # an all-in anywhere in the line is off-shape
        return gate_fail(RejectReason.ALL_IN_IN_LINE)
    entrants = {opener.seat, bb.seat} | {c.seat for c in callers}
    if any(
        s.status is not PlayerStatus.FOLDED
        for s in state.seats
        if s.seat not in entrants
    ):
        # an extra live player — not the gated 3/4-way shape
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    open_to = raises[0].amount_bb
    if not (2.0 - _EPS <= open_to <= _OVERSIZE_OPEN_CAP + _EPS):
        return gate_fail(RejectReason.OPEN_SIZE_OFF_BAND)
    return GateResult((opener, callers, bb, open_to), None)


def _mw_check_bet_responded(
    state, street: Street, opener_pos: Position, callers, pot_before: float
) -> StreetResult:
    """Gate: this street went EXACTLY check(BB) -> bet(opener, canonical) ->
    call-or-fold(EVERY caller); hero (the BB) now faces the bet and CLOSES —
    the action-order requirement itself (all callers responded between the
    bet and hero) is the closing-seat guard. `.value` is (bet, n_called), else
    a `.reason`. A caller RAISE is a different node."""
    acts = _street_actions(state, street)
    if len(acts) != 2 + len(callers):
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    chk, bet, *resps = acts
    if chk.action is not ActionType.CHECK or chk.position is not Position.BB:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if bet.action is not ActionType.BET or bet.position is not opener_pos:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if not _is_canonical_bet(bet.amount_bb, pot_before, street):
        return street_fail(RejectReason.BET_FRACTION_OFF_GRID)
    if {r.position for r in resps} != {c.position for c in callers}:
        # a non-caller acted, or a caller hasn't responded yet
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    n_called = 0
    for resp in resps:
        if resp.action is ActionType.CALL:
            if abs(resp.amount_bb - bet.amount_bb) > _EPS:
                # short call = someone is all-in — off-shape
                return street_fail(RejectReason.ALL_IN_IN_LINE)
            n_called += 1
        elif resp.action is not ActionType.FOLD:
            # caller raised — hero faces a raise, not the bet
            return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    return StreetResult((bet.amount_bb, n_called), None)


def _mw_check_bet_call_call(
    state, street: Street, opener_pos: Position, callers, pot_before: float
) -> StreetResult:
    """Gate: a PRIOR street went EXACTLY check(BB) -> bet(opener, canonical) ->
    call(EVERY caller) -> call(BB) — the full MW continuation line stayed
    intact. `.value` is the bet size, else a `.reason`."""
    acts = _street_actions(state, street)
    if len(acts) != 3 + len(callers):
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    chk, bet, *caller_calls, bb_call = acts
    if chk.action is not ActionType.CHECK or chk.position is not Position.BB:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if bet.action is not ActionType.BET or bet.position is not opener_pos:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if not _is_canonical_bet(bet.amount_bb, pot_before, street):
        return street_fail(RejectReason.BET_FRACTION_OFF_GRID)
    if {c.position for c in caller_calls} != {c.position for c in callers}:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if bb_call.action is not ActionType.CALL or bb_call.position is not Position.BB:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    for c in (*caller_calls, bb_call):
        if c.action is not ActionType.CALL:
            return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
        if abs(c.amount_bb - bet.amount_bb) > _EPS:
            # short call = someone is all-in — off-shape
            return street_fail(RejectReason.ALL_IN_IN_LINE)
    return StreetResult(bet.amount_bb, None)


def _mw_ranges(opener_pos: Position, caller_positions) -> tuple[str, str] | None:
    """(BB defense call range for hero, opener RFI raise range for villain) —
    PLUS the cold-caller gate: EVERY (caller, opener) VS_RFI call entry must
    exist or the pot carries an unmodeled range -> None. Caller ranges are
    NOT returned: no grader consumes them (see module comment)."""
    ranges = _srp_ranges(opener_pos)
    if ranges is None:
        return None
    opener_range, bb_range = ranges
    for caller_pos in caller_positions:
        entry = _find_entry(NodeContext.VS_RFI, caller_pos, opener_pos)
        if entry is None or not _combos_for(entry, ActionType.CALL):
            return None
    return bb_range, opener_range


def map_mw_flop_vs_cbet(state: HandState, hero_seat: int) -> Spot | None:
    """3/4-way vs flop c-bet: hero = BB who called a MW open, checked, the
    opener c-bet a canonical size, EVERY cold-caller responded — hero closes."""
    return _map_mw_flop_vs_cbet(state, hero_seat).spot


def _map_mw_flop_vs_cbet(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 3 or hero.position is not Position.BB:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _mw_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, callers, bb, open_to = gate.value
    if bb.seat != hero_seat:
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    flop_pot = round((2 + len(callers)) * open_to + 0.5, 2)
    faced = _mw_check_bet_responded(
        state, Street.FLOP, opener.position, callers, flop_pot
    )
    if faced.value is None:
        return map_fail(faced.reason)
    cbet, n_called = faced.value
    pot = _live_pot(state)
    expected = flop_pot + cbet * (1 + n_called)
    if abs(pot - expected) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    ranges = _mw_ranges(opener.position, [c.position for c in callers])
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)
    bb_range, opener_range = ranges
    return _spot_or_shallow(_faced_bet_spot(
        state, hero_seat, opener, pot, cbet,
        Street.FLOP, NodeContext.VS_CBET, bb_range, opener_range,
        mults=FACING_RAISE_MULTS["check_raise"],
    ))


def map_mw_vs_turn_bet(state: HandState, hero_seat: int) -> Spot | None:
    """3/4-way vs turn barrel: canonical MW flop bet-call(s)-call, then the
    opener bets the turn, EVERY caller responded — hero (BB) closes."""
    return _map_mw_vs_turn_bet(state, hero_seat).spot


def _map_mw_vs_turn_bet(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 4 or hero.position is not Position.BB:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _mw_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, callers, bb, open_to = gate.value
    if bb.seat != hero_seat:
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    n_way = 2 + len(callers)
    flop_pot = round(n_way * open_to + 0.5, 2)
    flop = _mw_check_bet_call_call(
        state, Street.FLOP, opener.position, callers, flop_pot
    )
    if flop.value is None:
        return map_fail(flop.reason)
    fbet = flop.value
    turn_pot = round(flop_pot + n_way * fbet, 2)
    faced = _mw_check_bet_responded(
        state, Street.TURN, opener.position, callers, turn_pot
    )
    if faced.value is None:
        return map_fail(faced.reason)
    tbet, n_called = faced.value
    pot = _live_pot(state)
    expected = turn_pot + tbet * (1 + n_called)
    if abs(pot - expected) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    ranges = _mw_ranges(opener.position, [c.position for c in callers])
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)
    bb_range, opener_range = ranges
    return _spot_or_shallow(_faced_bet_spot(
        state, hero_seat, opener, pot, tbet,
        Street.TURN, NodeContext.VS_TURN_BET, bb_range, opener_range,
    ))


def map_mw_vs_river_bet(state: HandState, hero_seat: int) -> Spot | None:
    """3/4-way vs river bet: canonical MW flop AND turn bet-call(s)-call, then
    the opener bets the river, EVERY caller responded — hero (BB) closes."""
    return _map_mw_vs_river_bet(state, hero_seat).spot


def _map_mw_vs_river_bet(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 5 or hero.position is not Position.BB:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _mw_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, callers, bb, open_to = gate.value
    if bb.seat != hero_seat:
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    n_way = 2 + len(callers)
    flop_pot = round(n_way * open_to + 0.5, 2)
    flop = _mw_check_bet_call_call(
        state, Street.FLOP, opener.position, callers, flop_pot
    )
    if flop.value is None:
        return map_fail(flop.reason)
    fbet = flop.value
    turn_pot = round(flop_pot + n_way * fbet, 2)
    turn = _mw_check_bet_call_call(
        state, Street.TURN, opener.position, callers, turn_pot
    )
    if turn.value is None:
        return map_fail(turn.reason)
    tbet = turn.value
    river_pot = round(turn_pot + n_way * tbet, 2)
    faced = _mw_check_bet_responded(
        state, Street.RIVER, opener.position, callers, river_pot
    )
    if faced.value is None:
        return map_fail(faced.reason)
    rbet, n_called = faced.value
    pot = _live_pot(state)
    expected = river_pot + rbet * (1 + n_called)
    if abs(pot - expected) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    ranges = _mw_ranges(opener.position, [c.position for c in callers])
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)
    bb_range, opener_range = ranges
    return _spot_or_shallow(_faced_bet_spot(
        state, hero_seat, opener, pot, rbet,
        Street.RIVER, NodeContext.VS_RIVER_BET, bb_range, opener_range,
    ))


# --- M7 (RES-I L5): hero-seat widening — opener + cold-caller MW mappers ----
# Widens the multiway family beyond hero-as-BB (RES-I §4 measured the BB-only
# scope at 0.23–2.73/1000, below the ≥5/1000 rankability threshold; §6 = GO).
# Two new hero seats, graded by the EXISTING graders + M6's opp-aware
# `_apply_multiway` scalars — no new grader, no new NodeContext:
#
#   * hero as the OPENER in the BB-in MW shape (`_mw_srp_preflop`): c-bet /
#     turn-barrel / river-barrel decisions into 2–3 live players. These are
#     AGGRESSOR nodes — hero initiates the betting, so players acting after
#     him are inherent to the node (exactly like the HU barrel mappers, where
#     the villain always still holds an action); the "hero closes" invariant
#     governs FACING nodes only. `grade_cbet`/`grade_*_barrel`'s aggressor-side
#     `_apply_multiway` (bluff dampen / value lean, geometric in opp) is the
#     deliberate model for betting into a live field.
#   * hero as a COLD-CALLER, closing. Inside the BB-in `_mw_srp_preflop`
#     shape a cold-caller can NEVER close — postflop the BB acts first, so
#     after the opener's bet the action wraps caller(s)-then-BB and the BB
#     always holds a live action behind every caller (skip-and-document:
#     those facing nodes stay None under the closing invariant, same law as
#     4-way-live-behind-hero). The caller family therefore fires in the
#     no-BB MW shape — opener + exactly TWO non-blind cold-callers, blinds
#     folded (RES-I §2: 485/10k flops, the largest previously-structural
#     kill) — with hero as the LATER caller, who genuinely closes the street
#     once the earlier caller has responded.
#
# Both families reuse `_is_canonical_bet` (M1's RECOGNIZED_BET_FRACS — never
# a private fraction set, RES-I §5) and keep every prior-street gate exact.
# Existing BB-path mappers are untouched; all new shapes are disjoint from
# every existing mapper by hero role + preflop entrant shape.


def map_mw_flop_cbet(state: HandState, hero_seat: int) -> Spot | None:
    """3/4-way flop c-bet: hero opened the MW pot (`_mw_srp_preflop` shape),
    the BB checked, hero decides check / bet small / bet big into the live
    field. Mirrors `map_flop_cbet` with the MW preflop gate + `_mw_ranges`
    content gate (every cold-caller's VS_RFI entry must exist)."""
    return _map_mw_flop_cbet(state, hero_seat).spot


def _map_mw_flop_cbet(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 3 or hero.position in _BLIND_POSITIONS:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _mw_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, callers, bb, open_to = gate.value
    if opener.seat != hero_seat:
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    if not _bb_checked_only(state, Street.FLOP):
        return map_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    flop_pot = round((2 + len(callers)) * open_to + 0.5, 2)
    pot = _live_pot(state)
    if abs(pot - flop_pot) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    ranges = _mw_ranges(opener.position, [c.position for c in callers])
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)
    bb_range, opener_range = ranges
    return _spot_or_shallow(_barrel_spot(
        state, hero_seat, bb, pot, Street.FLOP, NodeContext.CBET,
        opener_range, bb_range,
    ))


def map_mw_turn_barrel(state: HandState, hero_seat: int) -> Spot | None:
    """3/4-way turn barrel: hero opened the MW pot, the canonical flop
    bet-call(s)-call line stayed intact, and the BB has checked the turn."""
    return _map_mw_turn_barrel(state, hero_seat).spot


def _map_mw_turn_barrel(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 4 or hero.position in _BLIND_POSITIONS:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _mw_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, callers, bb, open_to = gate.value
    if opener.seat != hero_seat:
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    n_way = 2 + len(callers)
    flop_pot = round(n_way * open_to + 0.5, 2)
    flop = _mw_check_bet_call_call(
        state, Street.FLOP, hero.position, callers, flop_pot
    )
    if flop.value is None:
        return map_fail(flop.reason)
    fbet = flop.value
    if not _bb_checked_only(state, Street.TURN):
        return map_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    pot = _live_pot(state)
    if abs(pot - (flop_pot + n_way * fbet)) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    ranges = _mw_ranges(opener.position, [c.position for c in callers])
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)
    bb_range, opener_range = ranges
    return _spot_or_shallow(_barrel_spot(
        state, hero_seat, bb, pot, Street.TURN, NodeContext.TURN_BARREL,
        opener_range, bb_range,
    ))


def map_mw_river_barrel(state: HandState, hero_seat: int) -> Spot | None:
    """3/4-way river barrel: hero opened the MW pot, canonical flop AND turn
    bet-call(s)-call stayed intact, and the BB has checked the river."""
    return _map_mw_river_barrel(state, hero_seat).spot


def _map_mw_river_barrel(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 5 or hero.position in _BLIND_POSITIONS:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _mw_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, callers, bb, open_to = gate.value
    if opener.seat != hero_seat:
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    n_way = 2 + len(callers)
    flop_pot = round(n_way * open_to + 0.5, 2)
    flop = _mw_check_bet_call_call(
        state, Street.FLOP, hero.position, callers, flop_pot
    )
    if flop.value is None:
        return map_fail(flop.reason)
    fbet = flop.value
    turn_pot = round(flop_pot + n_way * fbet, 2)
    turn = _mw_check_bet_call_call(
        state, Street.TURN, hero.position, callers, turn_pot
    )
    if turn.value is None:
        return map_fail(turn.reason)
    tbet = turn.value
    if not _bb_checked_only(state, Street.RIVER):
        return map_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    pot = _live_pot(state)
    if abs(pot - (turn_pot + n_way * tbet)) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    ranges = _mw_ranges(opener.position, [c.position for c in callers])
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)
    bb_range, opener_range = ranges
    return _spot_or_shallow(_barrel_spot(
        state, hero_seat, bb, pot, Street.RIVER, NodeContext.RIVER_BARREL,
        opener_range, bb_range,
    ))


def _mw_nobb_srp_preflop(state: HandState) -> GateResult:
    """Gate: no-BB 3-way single-raised pot. One non-blind opener at an in-band
    open, exactly TWO non-blind cold-callers, BOTH blinds folded. Entrants are
    derived from the PREFLOP actions (a caller may legitimately have folded to
    a later postflop bet). Opener must still be IN; callers IN or
    postflop-FOLDED (never all-in); nobody else live. `.value` is
    (opener, callers, open_to) — `callers` a tuple in preflop call order,
    which equals position/postflop-act order — else a `.reason`."""
    pre = _street_actions(state, Street.PREFLOP)
    if any(
        h.action not in (ActionType.FOLD, ActionType.RAISE, ActionType.CALL)
        for h in pre
    ):
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    raises = [h for h in pre if h.action is ActionType.RAISE]
    calls = [h for h in pre if h.action is ActionType.CALL]
    if len(raises) != 1 or len(calls) != 2:
        # not an SRP with exactly two callers
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    opener_pos = raises[0].position
    caller_pos = [c.position for c in calls]
    if opener_pos in _BLIND_POSITIONS or any(
        p in _BLIND_POSITIONS for p in caller_pos
    ):
        # a blind entrant is the `_mw_srp_preflop` family instead
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    if len(set(caller_pos)) != 2:
        # duplicate caller (limp-then-call chain)
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    opener = next((s for s in state.seats if s.position is opener_pos), None)
    callers = tuple(
        s for p in caller_pos for s in state.seats if s.position is p
    )
    if opener is None or len(callers) != 2:
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    if opener.status is not PlayerStatus.IN:
        return gate_fail(_line_status_reason((opener,)))
    if any(c.status not in (PlayerStatus.IN, PlayerStatus.FOLDED) for c in callers):
        # an all-in anywhere in the line is off-shape
        return gate_fail(RejectReason.ALL_IN_IN_LINE)
    entrants = {opener.seat} | {c.seat for c in callers}
    if any(
        s.status is not PlayerStatus.FOLDED
        for s in state.seats
        if s.seat not in entrants
    ):
        # blinds (or anyone else) must be dead
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    open_to = raises[0].amount_bb
    if not (2.0 - _EPS <= open_to <= _OVERSIZE_OPEN_CAP + _EPS):
        return gate_fail(RejectReason.OPEN_SIZE_OFF_BAND)
    return GateResult((opener, callers, open_to), None)


def _mw_nobb_bet_responded(
    state, street: Street, opener_pos: Position, prior_callers, pot_before: float
) -> StreetResult:
    """Gate: this street went EXACTLY bet(opener, canonical) ->
    call-or-fold(EVERY caller before hero); hero — the LAST caller — now
    faces the bet and CLOSES (no BB exists in this shape; the opener acts
    first postflop and holds no further action once hero responds). `.value`
    is (bet, n_called), else a `.reason`. A raise is a different node."""
    acts = _street_actions(state, street)
    if len(acts) != 1 + len(prior_callers):
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    bet, *resps = acts
    if bet.action is not ActionType.BET or bet.position is not opener_pos:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if not _is_canonical_bet(bet.amount_bb, pot_before, street):
        return street_fail(RejectReason.BET_FRACTION_OFF_GRID)
    if {r.position for r in resps} != {c.position for c in prior_callers}:
        # a non-caller acted, or a prior caller hasn't responded
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    n_called = 0
    for resp in resps:
        if resp.action is ActionType.CALL:
            if abs(resp.amount_bb - bet.amount_bb) > _EPS:
                # short call = someone is all-in — off-shape
                return street_fail(RejectReason.ALL_IN_IN_LINE)
            n_called += 1
        elif resp.action is not ActionType.FOLD:
            # a raise — hero faces a raise, not the bet
            return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    return StreetResult((bet.amount_bb, n_called), None)


def _mw_nobb_bet_call_call(
    state, street: Street, opener_pos: Position, callers, pot_before: float
) -> StreetResult:
    """Gate: a PRIOR street went EXACTLY bet(opener, canonical) -> call(EVERY
    caller) — the full no-BB MW continuation line stayed intact. `.value` is
    the bet size, else a `.reason`."""
    acts = _street_actions(state, street)
    if len(acts) != 1 + len(callers):
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    bet, *caller_calls = acts
    if bet.action is not ActionType.BET or bet.position is not opener_pos:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if not _is_canonical_bet(bet.amount_bb, pot_before, street):
        return street_fail(RejectReason.BET_FRACTION_OFF_GRID)
    if {c.position for c in caller_calls} != {c.position for c in callers}:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    for c in caller_calls:
        if c.action is not ActionType.CALL:
            return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
        if abs(c.amount_bb - bet.amount_bb) > _EPS:
            # short call = someone is all-in — off-shape
            return street_fail(RejectReason.ALL_IN_IN_LINE)
    return StreetResult(bet.amount_bb, None)


def _mw_caller_ranges(
    opener_pos: Position, hero_pos: Position, other_caller_positions
) -> tuple[str, str] | None:
    """(hero's VS_RFI call range, opener RFI raise range) for the caller
    family — PLUS the content gate on every OTHER caller's VS_RFI call entry
    (an unmodeled range in the pot -> None, same law as `_mw_ranges`). Other
    callers' ranges are gates only, never a grader input."""
    rfi_entry = _find_entry(NodeContext.RFI, opener_pos, None)
    hero_entry = _find_entry(NodeContext.VS_RFI, hero_pos, opener_pos)
    opener_range = _combos_for(rfi_entry, ActionType.RAISE)
    hero_range = _combos_for(hero_entry, ActionType.CALL)
    if not opener_range or not hero_range:
        return None
    for p in other_caller_positions:
        entry = _find_entry(NodeContext.VS_RFI, p, opener_pos)
        if entry is None or not _combos_for(entry, ActionType.CALL):
            return None
    return hero_range, opener_range


def map_mw_caller_vs_cbet(state: HandState, hero_seat: int) -> Spot | None:
    """No-BB 3-way vs flop c-bet: hero = the LATER of two non-blind
    cold-callers, the opener c-bet a canonical size, the earlier caller
    responded — hero closes. Hero's raise is a plain in-position raise (hero
    never checked), so the legs use the facing-bet mults."""
    return _map_mw_caller_vs_cbet(state, hero_seat).spot


def _map_mw_caller_vs_cbet(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 3 or hero.position in _BLIND_POSITIONS:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _mw_nobb_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, callers, open_to = gate.value
    if callers[-1].seat != hero_seat:
        # the earlier caller never closes (hero-not-closing -> None)
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    flop_pot = round(3 * open_to + 1.5, 2)  # both blinds dead
    faced = _mw_nobb_bet_responded(
        state, Street.FLOP, opener.position, callers[:-1], flop_pot
    )
    if faced.value is None:
        return map_fail(faced.reason)
    cbet, n_called = faced.value
    pot = _live_pot(state)
    if abs(pot - (flop_pot + cbet * (1 + n_called))) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    ranges = _mw_caller_ranges(
        opener.position, hero.position, [c.position for c in callers[:-1]]
    )
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)
    hero_range, opener_range = ranges
    return _spot_or_shallow(_faced_bet_spot(
        state, hero_seat, opener, pot, cbet,
        Street.FLOP, NodeContext.VS_CBET, hero_range, opener_range,
        mults=FACING_RAISE_MULTS["raise"],
    ))


def map_mw_caller_vs_turn_bet(state: HandState, hero_seat: int) -> Spot | None:
    """No-BB 3-way vs turn barrel: canonical flop bet-call-call, then the
    opener bets the turn and the earlier caller responded — hero closes."""
    return _map_mw_caller_vs_turn_bet(state, hero_seat).spot


def _map_mw_caller_vs_turn_bet(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 4 or hero.position in _BLIND_POSITIONS:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _mw_nobb_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, callers, open_to = gate.value
    if callers[-1].seat != hero_seat:
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    flop_pot = round(3 * open_to + 1.5, 2)
    flop = _mw_nobb_bet_call_call(
        state, Street.FLOP, opener.position, callers, flop_pot
    )
    if flop.value is None:
        return map_fail(flop.reason)
    fbet = flop.value
    turn_pot = round(flop_pot + 3 * fbet, 2)
    faced = _mw_nobb_bet_responded(
        state, Street.TURN, opener.position, callers[:-1], turn_pot
    )
    if faced.value is None:
        return map_fail(faced.reason)
    tbet, n_called = faced.value
    pot = _live_pot(state)
    if abs(pot - (turn_pot + tbet * (1 + n_called))) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    ranges = _mw_caller_ranges(
        opener.position, hero.position, [c.position for c in callers[:-1]]
    )
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)
    hero_range, opener_range = ranges
    return _spot_or_shallow(_faced_bet_spot(
        state, hero_seat, opener, pot, tbet,
        Street.TURN, NodeContext.VS_TURN_BET, hero_range, opener_range,
    ))


def map_mw_caller_vs_river_bet(state: HandState, hero_seat: int) -> Spot | None:
    """No-BB 3-way vs river bet: canonical flop AND turn bet-call-call, then
    the opener bets the river and the earlier caller responded — hero closes."""
    return _map_mw_caller_vs_river_bet(state, hero_seat).spot


def _map_mw_caller_vs_river_bet(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 5 or hero.position in _BLIND_POSITIONS:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _mw_nobb_srp_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, callers, open_to = gate.value
    if callers[-1].seat != hero_seat:
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    flop_pot = round(3 * open_to + 1.5, 2)
    flop = _mw_nobb_bet_call_call(
        state, Street.FLOP, opener.position, callers, flop_pot
    )
    if flop.value is None:
        return map_fail(flop.reason)
    fbet = flop.value
    turn_pot = round(flop_pot + 3 * fbet, 2)
    turn = _mw_nobb_bet_call_call(
        state, Street.TURN, opener.position, callers, turn_pot
    )
    if turn.value is None:
        return map_fail(turn.reason)
    tbet = turn.value
    river_pot = round(turn_pot + 3 * tbet, 2)
    faced = _mw_nobb_bet_responded(
        state, Street.RIVER, opener.position, callers[:-1], river_pot
    )
    if faced.value is None:
        return map_fail(faced.reason)
    rbet, n_called = faced.value
    pot = _live_pot(state)
    if abs(pot - (river_pot + rbet * (1 + n_called))) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    ranges = _mw_caller_ranges(
        opener.position, hero.position, [c.position for c in callers[:-1]]
    )
    if ranges is None:
        return map_fail(RejectReason.UNCLASSIFIED)
    hero_range, opener_range = ranges
    return _spot_or_shallow(_faced_bet_spot(
        state, hero_seat, opener, pot, rbet,
        Street.RIVER, NodeContext.VS_RIVER_BET, hero_range, opener_range,
    ))


# --- M4 (RES-H H1): caller-re-raises-c-bet — hero = opener facing the raise --
# Hero opened an SRP, c-bet the flop at a canonical size, and the NON-BB
# preflop cold-caller raised the c-bet; hero faces/closes. Two entrant shapes
# share the family (both rejected by `_hu_srp_preflop`'s strict villain-is-BB
# 2-live gate, hence the dedicated `_flop_caller_raise_preflop` gate):
#   * opener + caller + BB (3-way): flop check(BB) → c-bet → raise(caller) →
#     BB folds (degrade-to-2-live, dead money stays in the pot) or calls
#     (still 3-live at hero's decision → `_apply_multiway` composes).
#   * opener + caller only (BB folded preflop): flop c-bet → raise(caller).
# The caller's VS_RFI call entry is the content gate AND his villain range
# (he is the aggressor hero faces). The raise size is un-bucketed (personas
# raise on a continuous grid — same rule as `_check_bet_raise`); the C-BET
# recognition reuses `_is_canonical_bet`'s RECOGNIZED_BET_FRACS grid, every
# member of which maps to a defined RES-E bucket. Donk leads, limped pots,
# delayed c-bets, BB raises and hero-not-opener all return None.


def _flop_caller_raise_preflop(state: HandState) -> GateResult:
    """Gate: SRP where a non-blind opener at an in-band open was flatted by
    exactly ONE non-blind cold-caller, plus optionally the BB; SB (and every
    other seat) folded. Structurally the `_mw_srp_preflop` entrant shape with
    the BB optional. `.value` is (opener, caller, bb_or_None, open_to) — bb is
    None when the BB folded preflop — else a `.reason`."""
    pre = _street_actions(state, Street.PREFLOP)
    if any(
        h.action not in (ActionType.FOLD, ActionType.RAISE, ActionType.CALL)
        for h in pre
    ):
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    raises = [h for h in pre if h.action is ActionType.RAISE]
    calls = [h for h in pre if h.action is ActionType.CALL]
    if len(raises) != 1 or len(calls) not in (1, 2):
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    opener_pos = raises[0].position
    if opener_pos in _BLIND_POSITIONS:
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    non_bb_calls = [c for c in calls if c.position is not Position.BB]
    if len(non_bb_calls) != 1:
        # exactly one cold-caller; two calls ⇒ the other is the BB's
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    caller_pos = non_bb_calls[0].position
    if caller_pos in _BLIND_POSITIONS:
        # an SB cold-call is off-shape
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    bb_called = len(calls) == 2  # the other call can only be the BB's
    opener = next((s for s in state.seats if s.position is opener_pos), None)
    caller = next((s for s in state.seats if s.position is caller_pos), None)
    bb = (
        next((s for s in state.seats if s.position is Position.BB), None)
        if bb_called
        else None
    )
    if opener is None or caller is None or (bb_called and bb is None):
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    if opener.status is not PlayerStatus.IN or caller.status is not PlayerStatus.IN:
        # an all-in anywhere in the line is off-shape
        return gate_fail(_line_status_reason((opener, caller)))
    if bb is not None and bb.status not in (PlayerStatus.IN, PlayerStatus.FOLDED):
        # BB may fold to the flop raise, never be all-in
        return gate_fail(RejectReason.ALL_IN_IN_LINE)
    entrants = {opener.seat, caller.seat} | ({bb.seat} if bb is not None else set())
    if any(
        s.status is not PlayerStatus.FOLDED
        for s in state.seats
        if s.seat not in entrants
    ):
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    open_to = raises[0].amount_bb
    if not (2.0 - _EPS <= open_to <= _OVERSIZE_OPEN_CAP + _EPS):
        return gate_fail(RejectReason.OPEN_SIZE_OFF_BAND)
    return GateResult((opener, caller, bb, open_to), None)


def _flop_cbet_caller_raise(
    state: HandState,
    opener_pos: Position,
    caller_pos: Position,
    bb_entrant: bool,
    pot_before: float,
) -> StreetResult:
    """Gate: the flop went EXACTLY [check(BB) →] bet(opener, canonical) →
    raise(caller) [→ fold-or-call(BB)], hero (the opener) now facing the
    caller's raise and CLOSING. `.value` is (cbet, raise_to, bb_called_raise),
    else a `.reason`. The raise size is deliberately un-bucketed (see
    `_check_bet_raise`); an incomplete raise or a short BB call is off-shape."""
    acts = _street_actions(state, Street.FLOP)
    if bb_entrant:
        if len(acts) != 4:
            return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
        chk, bet, cr, resp = acts
        if chk.action is not ActionType.CHECK or chk.position is not Position.BB:
            return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    else:
        if len(acts) != 2:
            return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
        bet, cr = acts
        resp = None
    if bet.action is not ActionType.BET or bet.position is not opener_pos:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if not _is_canonical_bet(bet.amount_bb, pot_before, Street.FLOP):
        return street_fail(RejectReason.BET_FRACTION_OFF_GRID)
    if cr.action is not ActionType.RAISE or cr.position is not caller_pos:
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    # The caller had nothing invested this street: the history INCREMENT is
    # the full raise-TO.
    raise_to = cr.amount_bb
    if raise_to <= bet.amount_bb + _EPS:
        # degenerate: a "raise" no bigger than the bet
        return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    bb_called_raise = False
    if resp is not None:
        if resp.position is not Position.BB:
            return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
        if resp.action is ActionType.CALL:
            if abs(resp.amount_bb - raise_to) > _EPS:
                # short call = someone is all-in — off-shape
                return street_fail(RejectReason.ALL_IN_IN_LINE)
            bb_called_raise = True
        elif resp.action is not ActionType.FOLD:
            # a BB re-raise is a different (unmapped) node
            return street_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    return StreetResult((bet.amount_bb, raise_to, bb_called_raise), None)


def map_flop_vs_caller_raise(state: HandState, hero_seat: int) -> Spot | None:
    """Flop caller-re-raises-c-bet (M4): hero opened an SRP at an in-band
    size, c-bet the flop canonically, and the non-BB preflop cold-caller
    raised; hero faces/closes. Hero's re-raise legs are the plain facing-bet
    mults on the raise-to; CALL is the INCREMENTAL amount (raise_to - cbet) —
    hero already has the c-bet invested this street."""
    return _map_flop_vs_caller_raise(state, hero_seat).spot


def _map_flop_vs_caller_raise(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 3 or hero.position in _BLIND_POSITIONS:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _flop_caller_raise_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    opener, caller, bb, open_to = gate.value
    if opener.seat != hero_seat:
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    flop_pot = round(
        (3 * open_to + 0.5) if bb is not None else (2 * open_to + 1.5), 2
    )
    faced = _flop_cbet_caller_raise(
        state, hero.position, caller.position, bb is not None, flop_pot
    )
    if faced.value is None:
        return map_fail(faced.reason)
    cbet, raise_to, bb_called_raise = faced.value
    pot = _live_pot(state)
    expected = flop_pot + cbet + raise_to + (raise_to if bb_called_raise else 0.0)
    if abs(pot - expected) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    # Ranges: hero = the opener's RFI raise range; villain = the CALLER's
    # VS_RFI call range (the same content entry `_mw_ranges` gates on — here
    # the caller IS the aggressor hero faces, so his range is consumed).
    rfi_entry = _find_entry(NodeContext.RFI, hero.position, None)
    caller_entry = _find_entry(NodeContext.VS_RFI, caller.position, hero.position)
    hero_range = _combos_for(rfi_entry, ActionType.RAISE)
    caller_range = _combos_for(caller_entry, ActionType.CALL)
    if not hero_range or not caller_range:
        return map_fail(RejectReason.UNCLASSIFIED)
    return _spot_or_shallow(_faced_bet_spot(
        state, hero_seat, caller, pot, raise_to,
        Street.FLOP, NodeContext.VS_CALLER_RAISE, hero_range, caller_range,
        mults=FACING_RAISE_MULTS["raise"],
        call_amt=round(raise_to - cbet, 2),
    ))


# --- M5 (Epic 5, RES-G Slice C): HU limped-pot flop mappers -----------------
# The FIRST limped-pot postflop node family, HU only (the tractable 31% of
# limped flops). The gate derives the ENTRANT COUNT from the PREFLOP actions —
# never from current flop statuses — so a 3+-entrant limped pot stays None
# even after it degrades to 2-live postflop (multiway limped is deferred
# Slice D "no baseline yet"; deliberately NOT M4's degrade-to-2-live
# pattern). Flop only; turn/river of a limped pot stays None (v1).


def _limped_flop_hu_preflop(state: HandState) -> GateResult:
    """Gate: HU limped pot (ZERO preflop raises). Entrants = every preflop
    CALLer (open-limp, or the SB completing) + the BB (posted; its option
    close is the lone legal preflop CHECK). Exactly 2 entrants, hero-agnostic;
    both must still be IN (an all-in anywhere is off-shape) and every other
    seat FOLDED. `.value` is (entrant_a, entrant_b, preflop_pot) — the preflop
    pot is 2.0 (SB completed) or 2.5 (one limper + the folded SB's dead 0.5) —
    else a `.reason`."""
    pre = _street_actions(state, Street.PREFLOP)
    if any(
        h.action not in (ActionType.FOLD, ActionType.CALL, ActionType.CHECK)
        for h in pre
    ):
        # any raise/bet: not a limped pot
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    if any(
        h.action is ActionType.CHECK and h.position is not Position.BB for h in pre
    ):
        # only the BB holds a free preflop option
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    calls = [h for h in pre if h.action is ActionType.CALL]
    entrant_pos = {c.position for c in calls} | {Position.BB}
    if len(entrant_pos) != 2:
        # 3+ preflop entrants (even if since degraded to 2-live)
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    entrants = [s for s in state.seats if s.position in entrant_pos]
    if len(entrants) != 2:
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    if any(s.status is not PlayerStatus.IN for s in entrants):
        # an all-in (or an entrant already folded) is off-shape
        return gate_fail(_line_status_reason(entrants))
    if any(
        s.status is not PlayerStatus.FOLDED
        for s in state.seats
        if s.position not in entrant_pos
    ):
        return gate_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    sb_dead = 0.0 if Position.SB in entrant_pos else 0.5
    pre_pot = round(2.0 + sb_dead, 2)
    return GateResult((entrants[0], entrants[1], pre_pot), None)


def _limped_lead_spot(
    state: HandState, hero_seat: int, villain, pot: float
) -> Spot | None:
    """Hero can lead the limped flop: check / bet small / bet big (mirrors
    `_barrel_spot`'s legal-action shape, but `facing` is the LIVE villain —
    hero may itself be the BB here). The small leg clamps up to the engine's
    1BB legal minimum (limped pots are small enough that 0.33·pot can fall
    under it)."""
    hero = state.seats[hero_seat]
    small_frac, big_frac = POSTFLOP_BET_FRACS["flop"]
    small = max(round(small_frac * pot, 1), 1.0)
    big = max(round(big_frac * pot, 1), 1.0)
    if big <= small:
        return None  # degenerate: both canonical sizes collapse onto the min bet
    hero_remaining = hero.stack_bb
    villain_remaining = villain.stack_bb
    if hero_remaining < big or villain_remaining <= 0:
        return None  # too shallow for the canonical small/big bet buckets
    effective = round(min(hero_remaining, villain_remaining), 2)
    return Spot(
        game=GameConfig(stakes=Stakes(sb=1.0, bb=2.0), table_size=9, max_buyin_bb=200.0),
        street=Street.FLOP,
        board=list(state.board),
        pot_bb=pot,
        hero=Hero(
            position=hero.position, hole_cards=hero.hole_cards, stack_bb=hero_remaining
        ),
        players=_players(state, hero_seat),
        effective_stack_bb=effective,
        spr=round(effective / pot, 1),
        action_history=list(state.action_history),
        to_act=hero.position,
        legal_actions=[
            LegalAction(action=ActionType.CHECK),
            LegalAction(action=ActionType.BET, min_bb=small, max_bb=hero_remaining),
            LegalAction(action=ActionType.BET, min_bb=big, max_bb=hero_remaining),
        ],
        node_context=[NodeContext.LIMPED_LEAD],
        facing=villain.position,
        hero_range=None,
        villain_range=None,
    )


def map_limped_flop_lead(state: HandState, hero_seat: int) -> Spot | None:
    """HU limped flop, hero can lead: zero preflop raises, exactly 2 preflop
    entrants incl. hero, and no flop bet yet (hero first to act, or the OOP
    villain checked to hero)."""
    return _map_limped_flop_lead(state, hero_seat).spot


def _map_limped_flop_lead(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 3:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _limped_flop_hu_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    a, b, pre_pot = gate.value
    if hero.seat not in (a.seat, b.seat):
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    villain = b if hero.seat == a.seat else a
    acts = _street_actions(state, Street.FLOP)
    if acts and not (
        len(acts) == 1
        and acts[0].action is ActionType.CHECK
        and acts[0].position is villain.position
    ):
        return map_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    pot = _live_pot(state)
    if abs(pot - pre_pot) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    return _spot_or_shallow(_limped_lead_spot(state, hero_seat, villain, pot))


def map_limped_flop_vs_lead(state: HandState, hero_seat: int) -> Spot | None:
    """HU limped flop, hero faces a villain lead at a recognized size: either
    the OOP villain led outright, or hero checked and the villain stabbed
    (hero's RAISE is then a check-raise, sized with the check_raise mults)."""
    return _map_limped_flop_vs_lead(state, hero_seat).spot


def _map_limped_flop_vs_lead(state: HandState, hero_seat: int) -> MapResult:
    hero = state.seats[hero_seat]
    if len(state.board) != 3:
        return map_fail(RejectReason.PREFLOP_SHAPE_UNGATED)
    gate = _limped_flop_hu_preflop(state)
    if gate.value is None:
        return map_fail(gate.reason)
    a, b, pre_pot = gate.value
    if hero.seat not in (a.seat, b.seat):
        return map_fail(RejectReason.HERO_ROLE_UNGATED)
    villain = b if hero.seat == a.seat else a
    acts = _street_actions(state, Street.FLOP)
    hero_checked = False
    if len(acts) == 2:
        if acts[0].action is not ActionType.CHECK or acts[0].position is not hero.position:
            return map_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
        hero_checked = True
        lead = acts[1]
    elif len(acts) == 1:
        lead = acts[0]
    else:
        return map_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if lead.action is not ActionType.BET or lead.position is not villain.position:
        return map_fail(RejectReason.STREET_ACTION_SHAPE_UNGATED)
    if not _is_canonical_bet(lead.amount_bb, pre_pot, Street.FLOP):
        return map_fail(RejectReason.BET_FRACTION_OFF_GRID)
    pot = _live_pot(state)
    if abs(pot - (pre_pot + lead.amount_bb)) > _EPS:
        return map_fail(RejectReason.UNCLASSIFIED)
    return _spot_or_shallow(_faced_bet_spot(
        state, hero_seat, villain, pot, lead.amount_bb,
        Street.FLOP, NodeContext.LIMPED_VS_LEAD, None, None,
        mults=FACING_RAISE_MULTS["check_raise" if hero_checked else "raise"],
    ))
