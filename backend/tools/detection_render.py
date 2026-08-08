"""Blind-detection hand renderer (flywheel S6 T3) — ONE code path, both classes.

The S6 pilot shows LLM judges 30-hand seat bundles and asks "human or bot?".
Any non-play difference between the two classes' rendered text is a free
answer, so this module is the blinding chokepoint: both sources are
normalized into ONE canonical record (`CanonicalHand`) and only that record
is ever rendered.

    human hands ─ from_human(state_json, focus_seat) ─┐
                                                      ├─► CanonicalHand ─► render_bundle()
    bot hands   ─ from_bot(state, focus_seat) ────────┘

Both adapters converge on `_canonical(state, focus_seat)` after their one
source-shaped step (parse a DB TEXT column / accept an in-memory object), so
there is no per-class rendering branch to diverge. Class-asymmetric inputs
(persona names, `hand_no`, `session_id`, `run_id`, `config_hash`, Parquet
columns, timestamps) are never parameters of any function here — they cannot
reach the renderer even by mistake.

Leak controls implemented (spec `flywheel-s6.md`, "Design rules → Renderer"):

- **Revealed board only.** The board comes from `HandState.board`, which the
  engine fills street-by-street; `full_board` (the complete runout dealt up
  front, present even on a preflop fold-out) is never read. NOTE: reveal
  depth is deliberately NOT derived from the action history — an all-in
  run-out reveals flop/turn/river with zero actions on them
  (`engine._close_street` sets `board = full_board`), and a history-derived
  depth would hide a board the players actually saw. `_check_reveal_depth`
  instead asserts the engine's own street/board invariant, which fails closed
  on any state where the two disagree.
- **Hole cards.** The focus seat's are always shown; every other seat's only
  when `settle().showdown_seats` says its hand was actually compared. The
  redaction happens in the ADAPTER, so an unrevealed hand is not merely
  unprinted — it is absent from the record the renderer receives.
- **Local re-keying.** Hands are numbered 1..N by position in the bundle.
  `CanonicalHand` has no field for a source hand number, id, or run id.
- **Opaque seats.** Raw seat indices exist only inside the record; the
  renderer maps every one through the caller's `seat_id_map`.
- **Deterministic.** Same records + same maps ⇒ byte-identical output: fixed
  position ordering, sorted map iteration, no wall-clock, no set iteration.

`leak_check` re-audits the finished text for the whole strip list and is
meant to be run by the corpus builder on every bundle of both classes.

Entry points for T4 (corpus builder):

    from_human(state_json: str, focus_seat: int) -> CanonicalHand
    from_bot(state: HandState, focus_seat: int) -> CanonicalHand
    render_bundle(hands, focus_seat_opaque_id, seat_id_map) -> str
    leak_check(rendered, forbidden=()) -> list[str]

`from_bot` takes the hand's TERMINAL `HandState`, not a seed: bot action
draws come from the export run's shared `random.Random`, whose state depends
on every preceding hand, so a single hand cannot be faithfully re-simulated
from its own `hand_seed` alone. The caller replays the run forward once
(`deal_hand`/`start_hand`/`bot_decision`/`apply`) and hands each terminal
state here.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from app.domain.archetypes import VillainType
from app.domain.spot import ActionType, PlayerStatus, Position, Street, validate_card
from app.domain.table.engine import HandState, settle

_SEATS = 9
_BOARD_CARDS = 5
# Tolerance for RECONCILING sums of 2dp-rounded amounts. Never a semantic
# threshold: it is wider than one chip, so it cannot be used to ask "does this
# seat have chips left?".
_EPS = 0.011
# "No chips behind", in a game whose money is integer cents. Half a cent:
# absorbs float residue (a real 0.01 stack arrives as 0.00999999999999801)
# while never swallowing a legal one-cent chip. Under the §A.1 buy-in spread a
# seat can legally call down to exactly 0.01bb and remain IN — the engine
# marks ALLIN only at `stack_bb <= 1e-9` (`engine._pay`), and CALL caps its
# increment at the seat's stack, so the remainder stays live. Using _EPS here
# rejected exactly one legal hand in 1,500 (T7 acceptance).
_ZERO_CHIPS = 0.005

# Fixed render order; never a dict/set iteration order.
_POSITION_ORDER: tuple[Position, ...] = (
    Position.UTG,
    Position.UTG1,
    Position.UTG2,
    Position.LJ,
    Position.HJ,
    Position.CO,
    Position.BTN,
    Position.SB,
    Position.BB,
)
_STREET_ORDER: tuple[Street, ...] = (Street.PREFLOP, Street.FLOP, Street.TURN, Street.RIVER)
_STREET_LABEL = {
    Street.PREFLOP: "Preflop",
    Street.FLOP: "Flop",
    Street.TURN: "Turn",
    Street.RIVER: "River",
}
# The engine's own invariant: a settled hand's revealed board length is fixed
# by the street it ended on (see engine._close_street).
_BOARD_LEN_BY_STREET = {Street.PREFLOP: 0, Street.FLOP: 3, Street.TURN: 4, Street.RIVER: 5}

# Bundles are pinned at 30 hands; a higher local index in rendered text means
# a source hand number leaked through.
MAX_LOCAL_HAND_INDEX = 30


class CanonicalHandError(ValueError):
    """An adapter input that must be REJECTED, never rendered.

    Raised for unparseable/incomplete/self-inconsistent source hands. The
    corpus builder's fail-closed window rule depends on this being an
    exception rather than a best-effort render.
    """


# ---------------------------------------------------------------------------
# Canonical schema — the only thing render_bundle() consumes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CanonicalAction:
    """One action. `amount_bb` is the increment this action added; `to_bb` is
    the seat's total for the street after it."""

    street: str
    seat: int
    position: str
    action: str
    amount_bb: float
    to_bb: float
    pot_before_bb: float
    all_in: bool


@dataclass(frozen=True, slots=True)
class CanonicalSeat:
    """One seat's per-hand ledger. `hole_cards` is None unless this seat's
    cards are revealable (focus seat, or a settlement-defined showdown seat)
    — unrevealed cards are absent from the record, not merely unprinted."""

    seat: int
    position: str
    starting_stack_bb: float
    net_bb: float
    hole_cards: tuple[str, str] | None


@dataclass(frozen=True, slots=True)
class CanonicalPot:
    amount_bb: float
    winners: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class CanonicalHand:
    """One normalized hand. Carries no source identity of any kind: no hand
    number, hand/session/run id, config hash, persona, or timestamp."""

    focus_seat: int
    board: tuple[str, ...]  # REVEALED cards only (0/3/4/5)
    final_street: str
    seats: tuple[CanonicalSeat, ...]  # seat order 0..8
    actions: tuple[CanonicalAction, ...]  # history order
    showdown_seats: tuple[int, ...]
    pots: tuple[CanonicalPot, ...]
    total_pot_bb: float


# ---------------------------------------------------------------------------
# Adapters
# ---------------------------------------------------------------------------


def from_human(state_json: str, focus_seat: int) -> CanonicalHand:
    """Human source: the `sim_hand.state_json` TEXT column (a serialized
    `HandState` holding all nine seats' hole cards and the full runout).

    The only human-specific step is parsing; everything after is the shared
    path. Raises `CanonicalHandError` on an unparseable or mid-hand row —
    the corpus builder rejects the whole window rather than closing ranks.
    """
    if not isinstance(state_json, str) or not state_json.strip():
        raise CanonicalHandError("state_json is empty or not a string")
    try:
        state = HandState.model_validate_json(state_json)
    except Exception as exc:  # state_json carries no version field
        raise CanonicalHandError(
            f"state_json did not validate as HandState: {type(exc).__name__}: {exc}"
        ) from exc
    return _canonical(state, focus_seat)


def from_bot(state: HandState, focus_seat: int) -> CanonicalHand:
    """Bot source: the TERMINAL `HandState` of one self-play hand.

    See the module docstring for why this is a state and not a seed. No
    export-run metadata (run_id, hand_id, config_hash, persona lineup,
    Parquet rows) is accepted here — it has nowhere to go.
    """
    if not isinstance(state, HandState):
        raise CanonicalHandError(f"expected a HandState, got {type(state).__name__}")
    return _canonical(state, focus_seat)


def _canonical(state: HandState, focus_seat: int) -> CanonicalHand:
    """The single normalization path both adapters converge on."""
    if not isinstance(focus_seat, int) or isinstance(focus_seat, bool):
        raise CanonicalHandError(f"focus_seat must be an int, got {focus_seat!r}")
    if not 0 <= focus_seat < _SEATS:
        raise CanonicalHandError(f"focus_seat {focus_seat} outside 0..{_SEATS - 1}")
    _validate_terminal_state(state)

    settlement = settle(state)
    net_by_seat = {d.seat: d.delta_bb for d in settlement.deltas}
    showdown = tuple(sorted(settlement.showdown_seats))
    revealable = {focus_seat, *showdown}

    actions = _replay(state)
    invested_by_seat: dict[int, float] = dict.fromkeys(range(_SEATS), 0.0)
    for act in actions:
        invested_by_seat[act.seat] = round(invested_by_seat[act.seat] + act.amount_bb, 2)
    for seat_state in state.seats:
        if abs(invested_by_seat[seat_state.seat] - seat_state.invested_total_bb) > _EPS:
            raise CanonicalHandError(
                f"seat {seat_state.seat}: action history sums to "
                f"{invested_by_seat[seat_state.seat]} but the seat ledger says "
                f"{seat_state.invested_total_bb} — inconsistent hand"
            )

    seats = tuple(
        CanonicalSeat(
            seat=s.seat,
            position=s.position.value,
            # stack_bb is chips-behind at settlement time and settle() does not
            # mutate state, so this is exactly the seat's starting stack — the
            # same derivation for both classes (live re-buys and --buyin-spread
            # both land in [95,105]bb).
            starting_stack_bb=_r2(s.stack_bb + s.invested_total_bb),
            net_bb=_r2(net_by_seat[s.seat]),
            hole_cards=(
                (s.hole_cards[0], s.hole_cards[1]) if s.seat in revealable else None
            ),
        )
        for s in sorted(state.seats, key=lambda s: s.seat)
    )
    pots = tuple(
        CanonicalPot(amount_bb=_r2(pot.amount_bb), winners=tuple(sorted(winners)))
        for pot, winners in zip(settlement.pots, settlement.winners_by_pot, strict=True)
    )
    return CanonicalHand(
        focus_seat=focus_seat,
        board=tuple(state.board),
        final_street=state.street.value,
        seats=seats,
        actions=actions,
        showdown_seats=showdown,
        pots=pots,
        total_pot_bb=_r2(sum(s.invested_total_bb for s in state.seats)),
    )


def _validate_terminal_state(state: HandState) -> None:
    """Fail closed on ANY malformed terminal state, before a single character
    is rendered.

    Pydantic types the fields but does not police their joint meaning, and it
    happily parses `NaN`/`Infinity` out of a JSON column — a corrupt human
    SQLite row would otherwise render a literal `nan` stack, which is a class
    tell all by itself.

    Every invariant below is verified to hold across 1,853 real human hands
    and 1,500 spread-mode production-policy bot hands (`--buyin-spread`, run
    seed 60001) before being enforced, so it rejects corruption without
    rejecting real data. The bot number is 1,500 and not a round few hundred
    for a reason: the earlier 200-hand check passed while a legal one-cent
    residue shape occurred exactly ONCE in 1,500 hands, and the `_EPS`-based
    zero-chips test wrongly rejected it (T7 acceptance). A sample that cannot
    contain the rare shape is not evidence about the rare shape.
    """
    if len(state.seats) != _SEATS:
        raise CanonicalHandError(f"expected {_SEATS} seats, got {len(state.seats)}")
    if sorted(s.seat for s in state.seats) != list(range(_SEATS)):
        raise CanonicalHandError(
            f"seat indices {[s.seat for s in state.seats]} are not a permutation "
            f"of 0..{_SEATS - 1} (duplicate or out-of-range seat)"
        )
    if sorted(s.position for s in state.seats) != sorted(Position):
        raise CanonicalHandError(
            f"positions {[s.position.value for s in state.seats]} are not a "
            f"permutation of the nine table positions"
        )
    if not state.hand_over:
        raise CanonicalHandError("hand is not over (persisted mid-hand) — cannot render")

    amounts: list[tuple[str, float]] = [
        ("current_bet_bb", state.current_bet_bb),
        ("min_raise_to_bb", state.min_raise_to_bb),
        ("last_full_raise_bb", state.last_full_raise_bb),
    ]
    for s in state.seats:
        amounts += [
            (f"seat {s.seat} stack_bb", s.stack_bb),
            (f"seat {s.seat} invested_street_bb", s.invested_street_bb),
            (f"seat {s.seat} invested_total_bb", s.invested_total_bb),
        ]
    for i, h in enumerate(state.action_history):
        amounts.append((f"action {i} amount_bb", h.amount_bb))
    for name, value in amounts:
        if not math.isfinite(value):
            raise CanonicalHandError(f"{name} is not a finite number ({value!r})")
        if value < -_ZERO_CHIPS:
            raise CanonicalHandError(f"{name} is negative ({value!r})")

    if len(state.full_board) != _BOARD_CARDS:
        raise CanonicalHandError(
            f"expected a {_BOARD_CARDS}-card runout, got {len(state.full_board)}"
        )
    cards: list[str] = []
    for s in state.seats:
        if len(s.hole_cards) != 2:
            raise CanonicalHandError(f"seat {s.seat} was not dealt two cards")
        cards += list(s.hole_cards)
    cards += list(state.full_board)
    for card in cards:
        try:
            validate_card(card)
        except ValueError as exc:
            raise CanonicalHandError(f"malformed card: {exc}") from exc
    if len(set(cards)) != len(cards):
        duplicated = sorted({c for c in cards if cards.count(c) > 1})
        raise CanonicalHandError(f"card dealt more than once: {duplicated}")
    if list(state.board) != list(state.full_board[: len(state.board)]):
        raise CanonicalHandError(
            "revealed board is not a prefix of the runout — refusing to render "
            "cards the players may never have seen"
        )
    _check_reveal_depth(state)

    for s in state.seats:
        if s.status is PlayerStatus.ALLIN and s.stack_bb > _ZERO_CHIPS:
            raise CanonicalHandError(
                f"seat {s.seat} is all-in but still holds {s.stack_bb} behind"
            )
        if s.status is PlayerStatus.IN and s.stack_bb < _ZERO_CHIPS:
            raise CanonicalHandError(
                f"seat {s.seat} has no chips behind but is not marked all-in"
            )
        if s.invested_total_bb < s.invested_street_bb - _EPS:
            raise CanonicalHandError(
                f"seat {s.seat} invested {s.invested_street_bb} this street but "
                f"only {s.invested_total_bb} in the hand"
            )


def _check_reveal_depth(state: HandState) -> None:
    """Fail closed unless the revealed board matches the street the hand ended
    on, AND covers every street the players actually acted on.

    Both directions matter: too FEW cards would hide a run-out; too MANY would
    mean the predealt runout leaked into a hand that never reached it."""
    expected = _BOARD_LEN_BY_STREET[state.street]
    if len(state.board) != expected:
        raise CanonicalHandError(
            f"final street {state.street.value} implies {expected} revealed board "
            f"cards, state has {len(state.board)} — refusing to guess"
        )
    deepest = Street.PREFLOP
    for h in state.action_history:
        if _STREET_ORDER.index(h.street) > _STREET_ORDER.index(deepest):
            deepest = h.street
    if len(state.board) < _BOARD_LEN_BY_STREET[deepest]:
        raise CanonicalHandError(
            f"action history reaches {deepest.value} but only "
            f"{len(state.board)} board cards are revealed"
        )


def _replay(state: HandState) -> tuple[CanonicalAction, ...]:
    """Walk `action_history`, deriving pot size, per-street totals, and all-in.

    `HistoryAction` carries a POSITION, and the button rotates every hand, so
    the position->seat map is rebuilt from THIS hand's own seats and never
    reused across hands.
    """
    seat_of = {s.position: s.seat for s in state.seats}
    stack_of = {s.seat: s.stack_bb + s.invested_total_bb for s in state.seats}
    street_invested: dict[int, float] = dict.fromkeys(range(_SEATS), 0.0)
    total_invested: dict[int, float] = dict.fromkeys(range(_SEATS), 0.0)
    pot = 0.0
    current_street: Street | None = None
    out: list[CanonicalAction] = []
    for h in state.action_history:
        if h.street is not current_street:
            street_invested = dict.fromkeys(range(_SEATS), 0.0)
            current_street = h.street
        if h.position not in seat_of:
            raise CanonicalHandError(f"action history position {h.position} has no seat")
        seat = seat_of[h.position]
        street_invested[seat] = round(street_invested[seat] + h.amount_bb, 2)
        total_invested[seat] = round(total_invested[seat] + h.amount_bb, 2)
        pot = round(pot + h.amount_bb, 2)
        out.append(
            CanonicalAction(
                street=h.street.value,
                seat=seat,
                position=h.position.value,
                action=h.action.value,
                amount_bb=_r2(h.amount_bb),
                to_bb=_r2(street_invested[seat]),
                pot_before_bb=_r2(pot - h.amount_bb),
                # Same one-chip rule as the validator: a seat that called down
                # to a single cent is NOT all-in, and must not be labelled so
                # in judge-facing text.
                all_in=total_invested[seat] >= stack_of[seat] - _ZERO_CHIPS,
            )
        )
    return tuple(out)


def _r2(x: float) -> float:
    """Round to 2dp and normalize -0.0 (which formats as '-0.00')."""
    v = round(x, 2)
    return 0.0 if v == 0 else v


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


def render_bundle(
    hands: Sequence[CanonicalHand],
    focus_seat_opaque_id: str,
    seat_id_map: Mapping[int, str],
    expected_count: int | None = None,
) -> str:
    """Render a bundle as judge-facing text. One code path for both classes.

    `seat_id_map` maps raw seat index -> opaque ID (e.g. {0: "P3", ...}); the
    caller (T4) owns the seeded shuffle that builds it. `focus_seat_opaque_id`
    is the opaque ID of the player under review and must be the map's label
    for every hand's focus seat — so the judge is told WHICH player to assess
    without the focus seat being formatted differently from any other.

    `expected_count` asserts the bundle size (the judging path passes 30, the
    §d-pinned bundle length). Default None keeps the smaller dry-run decks
    (6+6) renderable, so the pin lives at the call site that actually has one.
    """
    if not hands:
        raise CanonicalHandError("cannot render an empty bundle")
    if expected_count is not None and len(hands) != expected_count:
        raise CanonicalHandError(
            f"bundle has {len(hands)} hands, expected exactly {expected_count}"
        )
    if len(set(seat_id_map.values())) != len(seat_id_map):
        raise CanonicalHandError("seat_id_map has duplicate opaque IDs")
    for hand in hands:
        for seat in hand.seats:
            if seat.seat not in seat_id_map:
                raise CanonicalHandError(f"seat_id_map is missing seat {seat.seat}")
        if seat_id_map[hand.focus_seat] != focus_seat_opaque_id:
            raise CanonicalHandError(
                "every hand's focus seat must map to focus_seat_opaque_id "
                f"{focus_seat_opaque_id!r}"
            )

    lines = [
        f"Player under review: {focus_seat_opaque_id}",
        "9-handed No-Limit Hold'em. Blinds 0.50 / 1.00. All amounts in big blinds.",
        f"Hands: {len(hands)}, consecutive, in order of play.",
    ]
    for index, hand in enumerate(hands, start=1):
        lines.append("")
        lines.extend(_render_hand(hand, index, focus_seat_opaque_id, seat_id_map))
    return "\n".join(lines) + "\n"


def _render_hand(
    hand: CanonicalHand,
    local_index: int,
    focus_seat_opaque_id: str,
    seat_id_map: Mapping[int, str],
) -> list[str]:
    by_position = {seat.position: seat for seat in hand.seats}
    ordered = [by_position[p.value] for p in _POSITION_ORDER if p.value in by_position]
    lines = [f"### Hand {local_index}"]
    lines.append(
        "Stacks: "
        + " | ".join(
            f"{seat_id_map[s.seat]} ({s.position}) {s.starting_stack_bb:.2f}" for s in ordered
        )
    )
    focus = next(s for s in hand.seats if s.seat == hand.focus_seat)
    lines.append(
        f"{focus_seat_opaque_id} ({focus.position}) holds "
        + " ".join(focus.hole_cards or ())
    )

    actions_by_street: dict[str, list[CanonicalAction]] = {}
    for act in hand.actions:
        actions_by_street.setdefault(act.street, []).append(act)
    revealed = {
        Street.PREFLOP.value: 0,
        Street.FLOP.value: 3,
        Street.TURN.value: 4,
        Street.RIVER.value: 5,
    }
    for street in _STREET_ORDER:
        key = street.value
        street_actions = actions_by_street.get(key, [])
        board_shown = len(hand.board) >= revealed[key] and revealed[key] > 0
        if not street_actions and not board_shown:
            continue
        pot_before = (
            street_actions[0].pot_before_bb if street_actions else hand.total_pot_bb
        )
        header = f"{_STREET_LABEL[street]} (pot {pot_before:.2f})"
        if board_shown:
            header += ": " + " ".join(hand.board[: revealed[key]])
        lines.append(header)
        for act in street_actions:
            lines.append("  " + _render_action(act, seat_id_map))

    if hand.showdown_seats:
        shown = [
            s
            for s in ordered
            if s.seat in hand.showdown_seats and s.hole_cards is not None
        ]
        lines.append(
            "Showdown: "
            + " | ".join(
                f"{seat_id_map[s.seat]} " + " ".join(s.hole_cards or ()) for s in shown
            )
        )
    lines.append(_render_result(hand, focus_seat_opaque_id, seat_id_map))
    return lines


def _render_action(act: CanonicalAction, seat_id_map: Mapping[int, str]) -> str:
    who = f"{seat_id_map[act.seat]} ({act.position})"
    if act.action == ActionType.FOLD.value:
        body = "folds"
    elif act.action == ActionType.CHECK.value:
        body = "checks"
    elif act.action == ActionType.POST.value:
        body = f"posts {act.amount_bb:.2f}"
    elif act.action == ActionType.CALL.value:
        body = f"calls {act.amount_bb:.2f}"
    elif act.action == ActionType.BET.value:
        body = f"bets {act.amount_bb:.2f}"
    else:  # RAISE
        body = f"raises to {act.to_bb:.2f}"
    if act.all_in and act.action != ActionType.FOLD.value:
        body += " (all-in)"
    return f"{who} {body}"


def _render_result(
    hand: CanonicalHand, focus_seat_opaque_id: str, seat_id_map: Mapping[int, str]
) -> str:
    parts = []
    layered = len(hand.pots) > 1
    for i, pot in enumerate(hand.pots):
        label = ("Main pot" if layered else "Pot") if i == 0 else f"Side pot {i}"
        winners = ", ".join(seat_id_map[s] for s in pot.winners)
        parts.append(f"{label} {pot.amount_bb:.2f} to {winners}")
    if not parts:  # walkover-shaped hand with no chips in
        parts.append(f"Pot {hand.total_pot_bb:.2f}")
    focus = next(s for s in hand.seats if s.seat == hand.focus_seat)
    net = f"{focus.net_bb:+.2f}" if focus.net_bb else "0.00"
    parts.append(f"{focus_seat_opaque_id} net {net}")
    return "Result: " + " | ".join(parts)


# ---------------------------------------------------------------------------
# Leak audit
# ---------------------------------------------------------------------------

_PERSONA_WORDS = tuple(sorted(v.value for v in VillainType))
_LEAK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "persona name",
        re.compile(r"\b(" + "|".join(_PERSONA_WORDS) + r")\b", re.IGNORECASE),
    ),
    ("persona/role label", re.compile(r"\b(persona|villain|hero)\b", re.IGNORECASE)),
    ("seat-index field", re.compile(r"seat_", re.IGNORECASE)),
    ("raw seat index", re.compile(r"\bseats?\s*[#:]?\s*\d\b", re.IGNORECASE)),
    ("run id", re.compile(r"run-s", re.IGNORECASE)),
    ("config-hash-like token", re.compile(r"\b[0-9a-f]{64}\b", re.IGNORECASE)),
    ("session metadata", re.compile(r"session", re.IGNORECASE)),
    ("ISO timestamp", re.compile(r"\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}|\b)")),
    (
        "metadata field name",
        re.compile(
            r"\b(hand_no|hand_id|run_id|config_hash|session_id|seat_index)\b",
            re.IGNORECASE,
        ),
    ),
)
_HAND_NUMBER_RE = re.compile(r"\bhand\s+(\d+)\b", re.IGNORECASE)
_HAND_HEADER_RE = re.compile(r"^### Hand (\d+)$", re.MULTILINE)


def leak_check(rendered: str, forbidden: Iterable[str] = ()) -> list[str]:
    """Audit rendered bundle text for every §d strip-list signal.

    Three layers: token patterns (persona names, ids, hashes, timestamps,
    metadata field names), the local-index grammar (`### Hand 1..N`, each
    once, in order), and caller-supplied literals.

    `forbidden` adds caller-supplied literals — e.g. the run id, session id,
    or persona lineup the bundle came from, which the corpus builder knows
    and the renderer must never have seen. Matched case-insensitively as
    SUBSTRINGS, deliberately over-sensitive: a false positive costs one look,
    a false negative costs the pilot.

    Returns a sorted list of violation descriptions; empty means clean. This
    is an auditor, not a sanitizer: it never edits the text.
    """
    violations: set[str] = set()
    for label, pattern in _LEAK_PATTERNS:
        for match in pattern.finditer(rendered):
            violations.add(f"{label}: {match.group(0)!r}")
    for match in _HAND_NUMBER_RE.finditer(rendered):
        value = int(match.group(1))
        if value > MAX_LOCAL_HAND_INDEX:
            violations.add(
                f"absolute hand number: {match.group(0)!r} "
                f"(local indices stop at {MAX_LOCAL_HAND_INDEX})"
            )
    # Structural grammar: a token scan can miss a source key that merely looks
    # like a plausible local index (e.g. hand 7 of a 30-hand bundle rendered as
    # "Hand 12"). Requiring the header sequence to be exactly 1..N in order
    # catches any re-keying failure, not just out-of-range ones.
    headers = [int(h) for h in _HAND_HEADER_RE.findall(rendered)]
    if headers and headers != list(range(1, len(headers) + 1)):
        violations.add(
            f"hand header sequence: {headers} is not 1..{len(headers)} in order "
            f"(hands must be re-keyed to local indices)"
        )
    lowered = rendered.lower()
    for token in forbidden:
        if token and token.lower() in lowered:
            violations.add(f"forbidden token: {token!r}")
    return sorted(violations)


__all__ = [
    "MAX_LOCAL_HAND_INDEX",
    "CanonicalAction",
    "CanonicalHand",
    "CanonicalHandError",
    "CanonicalPot",
    "CanonicalSeat",
    "from_bot",
    "from_human",
    "leak_check",
    "render_bundle",
]
