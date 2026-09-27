"""Stat definitions shared by real (`export_session.py`) and simulated
(`sixmax_baseline.py`) hands (M1 T2): every seat's per-hand tracking stats
go through one definition, `Hand` -> `replay` -> `settle_hand` -> `stats_for`,
so a real session and a simulated one are measured the same way.

Traps this module must not reintroduce (see the ticket):
- `action_history` entries carry `position`, never `seat`, and the button
  rotates every hand -> the seat<->position map is rebuilt from that hand's
  OWN `state.seats` inside `Hand.__init__`, never cached across hands.
- `SimSeat.stack_bb` is a *current* value, overwritten at every settlement —
  each hand's starting stack is reconstructed as `stack_bb + invested_total_bb`
  read from that hand's own terminal state, not from the seat ledger row.
- Bot decisions never land in `SimDecision` (hero rows only); everything
  about villain play is read from `state.action_history`.
- "Saw a flop" must be measured off `Hand.revealed` (`state.board`, the
  ACTUALLY-revealed cards), never `Hand.board` (`state.full_board`, the
  complete runout dealt up front even on a preflop fold-out) — the latter
  is always >= 3 cards, so it silently scores every steal as a flop seen.
- "Went to showdown" must be measured off `settle()`'s own `showdown_seats`
  (a real hand comparison happened), never "reached the river without
  folding" — an uncontested river bet is not a showdown.
- `state_json` is written at every hero decision point, not only at
  settlement (`sim_session.py:845`), so a row can have `hand_over=False`;
  such hands are skipped (denominators would otherwise include a hand whose
  net is silently 0).
"""

from __future__ import annotations

import math
import os
import sys
from collections import defaultdict
from pathlib import Path

from sqlmodel import Session, create_engine, select

from app.db.models import SimHand, SimSeat
from app.db.session import DB_PATH as DEFAULT_DB_PATH
from app.domain.table.engine import HandState, settle


def resolve_db_path(cli_value: str | None) -> Path:
    """--db PATH > $POKER_COACH_DB > the live app's DB (app.db.session.DB_PATH).

    Needed because the DB file this tool reads can be swapped or archived out
    from under a live session (this repo's own `backend/data/` has done exactly
    that mid-analysis) — a fixed default is not enough for reproducibility."""
    if cli_value:
        return Path(cli_value)
    env_value = os.environ.get("POKER_COACH_DB")
    if env_value:
        return Path(env_value)
    return DEFAULT_DB_PATH


class Hand:
    """One dealt hand, reconstructed entirely from its own terminal
    `state_json` — never from `SimSeat` (that row is a live carry-over
    value, overwritten at every settlement)."""

    def __init__(self, hand_no: int, hand_id: str, state: HandState) -> None:
        self.hand_no = hand_no
        self.id = hand_id
        self.state = state
        self.button = state.button_seat
        # full_board is always the complete 5-card runout (even on a
        # preflop fold-out); board only reveals up to the street reached.
        self.board = list(state.full_board) if state.full_board else list(state.board)
        # `revealed` is the ACTUALLY-revealed board (0/3/4/5 cards by street
        # reached) — the only correct signal for "did this seat see a flop".
        # `self.board` (full runout) is display-only; using it for saw_flop
        # is always-true and silently turns a preflop steal into a WWSF hit.
        self.revealed = list(state.board)
        self.seats = {s.seat: s for s in state.seats}
        self.pos_of = {s.seat: s.position for s in state.seats}
        # THE TRAP: position -> seat is per-hand only. Button rotates every
        # hand, so this map must never be reused across hands.
        self.seat_of = {s.position: s.seat for s in state.seats}
        self.history = state.action_history
        self.final_street = state.street


def load(
    session_id: str,
    max_hand_no: int | None = None,
    db_path: Path | None = None,
) -> tuple[dict[int, str], list[Hand], int]:
    """Seat->persona map + every hand whose state_json validates AND is
    settled (NEW vs the reference: skip-on-failure instead of raw
    json.loads; also skip hands persisted mid-hand — state_json is written
    at every decision point, not just at settlement (sim_session.py:845),
    so a row can be `hand_over=False` and would otherwise pollute every
    denominator with a hand whose net is silently 0).

    `max_hand_no` caps to `hand_no <= max_hand_no` — a live session keeps
    growing under a concurrent writer, so this is the only way to pin a
    reproducible analysis to a known-size corpus (e.g. "the 181-hand
    session"). `db_path` defaults to `resolve_db_path(None)` — a DB file
    this tool reads can be swapped/archived out from under a session, so a
    per-call engine (never the shared `app.db.session.engine` singleton)
    is required for `--db`/`POKER_COACH_DB` to actually take effect."""
    db_path = db_path or resolve_db_path(None)
    local_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    with Session(local_engine) as db:
        seat_rows = db.exec(select(SimSeat).where(SimSeat.session_id == session_id)).all()
        seats = {r.seat_index: (r.persona_type or "HERO") for r in seat_rows}

        hand_rows = db.exec(select(SimHand).where(SimHand.session_id == session_id)).all()

    if max_hand_no is not None:
        hand_rows = [r for r in hand_rows if r.hand_no <= max_hand_no]
    hand_rows = sorted(hand_rows, key=lambda h: h.hand_no)
    hands: list[Hand] = []
    n_skipped = 0
    for row in hand_rows:
        if not row.state_json:
            n_skipped += 1
            continue
        try:
            state = HandState.model_validate_json(row.state_json)
        except Exception as exc:  # no version field on state_json; skip malformed rows
            n_skipped += 1
            print(f"skip hand {row.hand_no}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        if not state.hand_over:
            n_skipped += 1
            print(f"skip hand {row.hand_no}: not hand_over (persisted mid-hand)", file=sys.stderr)
            continue
        hands.append(Hand(row.hand_no, row.id, state))
    return seats, hands, n_skipped


def settle_hand(hand: Hand) -> tuple[dict[int, float], list[int]]:
    """net bb per seat + showdown seat list, via the real domain settle()."""
    if not hand.state.hand_over:
        return {}, []
    result = settle(hand.state)
    net = {d.seat: d.delta_bb for d in result.deltas}
    return net, result.showdown_seats


def replay(hand: Hand) -> list[dict]:
    """Walk action_history, tracking pot / to-call / street-invested per seat.

    Returns list of enriched action dicts. Asserts the increments reconcile
    with the stored invested_total_bb for every seat.
    """
    street_inv: dict[int, float] = defaultdict(float)
    total_inv: dict[int, float] = defaultdict(float)
    pot = 0.0
    cur_street = None
    out: list[dict] = []
    for a in hand.history:
        if a.street != cur_street:
            street_inv = defaultdict(float)
            cur_street = a.street
        seat = hand.seat_of[a.position]
        to_call = max(street_inv.values(), default=0.0) - street_inv[seat]
        rec = {
            "street": a.street.value,
            "seat": seat,
            "pos": a.position.value,
            "action": a.action.value,
            "amount": a.amount_bb,
            "pot_before": round(pot, 2),
            "to_call": round(to_call, 2),
            "street_inv_before": round(street_inv[seat], 2),
        }
        street_inv[seat] += a.amount_bb
        total_inv[seat] += a.amount_bb
        pot += a.amount_bb
        rec["total_after"] = round(street_inv[seat], 2)
        out.append(rec)
    for seat, sd in hand.seats.items():
        assert abs(total_inv[seat] - sd.invested_total_bb) < 0.02, (
            f"hand {hand.hand_no} seat {seat}: replay {total_inv[seat]} != {sd.invested_total_bb}"
        )
    return out


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials (default 95%)."""
    # n == 0: no evidence, so return the whole [0, 1] range rather than divide by zero.
    if n == 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return center - half, center + half


def stats_for(seat_list, seats, hands, replays, nets, shows):
    """Compute standard poker tracking stats for a set of seats."""
    st: dict[str, float] = defaultdict(float)
    per_pos: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for h in hands:
        acts = replays[h.hand_no]
        hand_showdown = shows.get(h.hand_no, [])
        for seat in seat_list:
            if seat not in h.seats:
                continue
            pos = h.pos_of[seat]
            mine = [a for a in acts if a["seat"] == seat]
            pre = [a for a in mine if a["street"] == "preflop" and a["action"] != "post"]
            if not pre:
                continue
            st["hands"] += 1
            per_pos[pos]["hands"] += 1
            # VPIP / PFR / 3bet
            vpip = any(a["action"] in ("call", "raise") for a in pre)
            pfr = any(a["action"] == "raise" for a in pre)
            if vpip:
                st["vpip"] += 1
                per_pos[pos]["vpip"] += 1
            if pfr:
                st["pfr"] += 1
                per_pos[pos]["pfr"] += 1
            # limp = first voluntary preflop action is a call with no prior raise
            first = pre[0]
            idx = acts.index(first)
            prior = [
                a
                for a in acts[:idx]
                if a["street"] == "preflop" and a["action"] in ("raise", "bet")
            ]
            prior_raise_before_first = bool(prior)
            if first["action"] == "call" and not prior_raise_before_first:
                st["limp"] += 1
            if first["action"] == "raise" and not prior_raise_before_first:
                st["open_raise"] += 1
            # RFI: folded to this seat's first decision (BB excluded; a BB walk
            # never reaches here since BB then has no non-post preflop action).
            folded_to = all(
                a["action"] == "fold"
                for a in acts[:idx]
                if a["street"] == "preflop" and a["action"] != "post"
            )
            if folded_to and pos != "BB":
                st["rfi_opp"] += 1
                per_pos[pos]["rfi_opp"] += 1
                if first["action"] == "raise":
                    st["rfi"] += 1
                    per_pos[pos]["rfi"] += 1
            if prior_raise_before_first:
                st["faced_raise"] += 1
                if first["action"] == "raise":
                    st["3bet"] += 1
                elif first["action"] == "call":
                    st["call_vs_raise"] += 1
                else:
                    st["fold_vs_raise"] += 1
            # postflop — use the ACTUALLY-revealed board, never the full
            # runout (h.board), which is always 5 cards even on a fold-out.
            # No `and vpip` term: canon (test_personas_postflop.py:1908-1916)
            # counts any live seat that sees the flop, including one that is
            # all-in from a posted blind with no voluntary preflop action.
            saw_flop = any(a["street"] == "flop" for a in mine) or (
                h.seats[seat].status != "folded" and len(h.revealed) >= 3
            )
            if saw_flop:
                st["saw_flop"] += 1
                if nets[h.hand_no].get(seat, 0) > 0:
                    st["won_after_flop"] += 1
            # Flop c-bet: last preflop raiser, first flop action taken with no
            # flop bet before it. An all-in preflop raiser has no flop action.
            pre_raises = [a for a in acts if a["street"] == "preflop" and a["action"] == "raise"]
            my_flop = [a for a in mine if a["street"] == "flop"]
            if pre_raises and pre_raises[-1]["seat"] == seat and my_flop:
                fidx = acts.index(my_flop[0])
                if not any(a["street"] == "flop" and a["action"] == "bet" for a in acts[:fidx]):
                    st["cbet_opp"] += 1
                    if my_flop[0]["action"] == "bet":
                        st["cbet"] += 1
            for street in ("flop", "turn", "river"):
                sm = [a for a in mine if a["street"] == street]
                if not sm:
                    continue
                st[f"{street}_seen"] += 1
                for a in sm:
                    if a["action"] in ("bet", "raise"):
                        st[f"{street}_agg"] += 1
                        if a["pot_before"] > 0:
                            st[f"{street}_sizesum"] += 100 * a["amount"] / a["pot_before"]
                            st[f"{street}_sizen"] += 1
                    elif a["action"] == "call":
                        st[f"{street}_call"] += 1
                    elif a["action"] == "fold":
                        st[f"{street}_fold"] += 1
                    elif a["action"] == "check":
                        st[f"{street}_check"] += 1
                    if a["action"] == "raise" and a["to_call"] > 0:
                        st[f"{street}_raise_vs_bet"] += 1
                    if a["to_call"] > 0 and a["action"] in ("call", "fold", "raise"):
                        st[f"{street}_faced_bet"] += 1
                        if a["action"] == "fold":
                            st[f"{street}_fold_vs_bet"] += 1
            # WTSD = actually compared hands at showdown (settle()'s own
            # showdown_seats, not "reached the river uncontested").
            if seat in hand_showdown:
                st["wtsd_num"] += 1
                if nets[h.hand_no].get(seat, 0) > 0:
                    st["wsd_win"] += 1
    return st, per_pos
