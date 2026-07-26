"""Export a stored Simulate session into per-persona hand packets + tracking
stats, so later tickets can say "run this and check X" (T-EXPORT).

Ports `docs/ai-dlc/research/persona-realism-artifacts/hand-analysis-181/
reference-scripts/export_hands.py` (gitignored on disk — the script that
actually produced SYNTHESIS.md and the six persona analyses) into this repo
tool. Two deliberate deviations from the reference, both required by the
ticket mechanism:

- Reads `app.db.session.engine` instead of a hardcoded DB path, so the tool
  always reads the same database the app writes.
- Each hand's `state_json` is parsed through the real domain
  `HandState.model_validate_json` (not raw `json.loads`) and wrapped in
  try/except-and-skip, since `state_json` carries no version field and a row
  from an incompatible schema should be skipped, not silently mis-parsed.
  This also means side-pot settlement reuses the actual
  `app.domain.table.engine.settle` instead of a hand-rolled replica.

Traps this script must not reintroduce (see the ticket):
- `action_history` entries carry `position`, never `seat`, and the button
  rotates every hand -> the seat<->position map is rebuilt from that hand's
  OWN `state.seats` inside `Hand.__init__`, never cached across hands.
- `SimSeat.stack_bb` is a *current* value, overwritten at every settlement —
  each hand's starting stack is reconstructed as `stack_bb + invested_total_bb`
  read from that hand's own terminal state, not from the seat ledger row.
- Bot decisions never land in `SimDecision` (hero rows only); everything
  about villain play is read from `state.action_history`.

Usage:
    python -m tools.export_session --session <session_id> [--out DIR]
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from sqlmodel import Session, select

from app.db.models import SimHand, SimSeat
from app.db.session import engine
from app.domain.postflop import _hand_category
from app.domain.table.engine import HandState, settle

RANKS = "23456789TJQKA"


def hand_class(c1: str, c2: str) -> str:
    r1, s1 = c1[0], c1[1]
    r2, s2 = c2[0], c2[1]
    if RANKS.index(r1) < RANKS.index(r2):
        r1, r2, s1, s2 = r2, r1, s2, s1
    if r1 == r2:
        return r1 + r2
    return f"{r1}{r2}{'s' if s1 == s2 else 'o'}"


def street_board(board: list[str], street: str) -> list[str]:
    return {"preflop": [], "flop": board[:3], "turn": board[:4], "river": board[:5]}[street]


class Hand:
    """One dealt hand, reconstructed entirely from its own terminal
    `state_json` — never from `SimSeat` (that row is a live carry-over
    value, overwritten at every settlement)."""

    def __init__(self, sim_hand: SimHand, state: HandState) -> None:
        self.hand_no = sim_hand.hand_no
        self.id = sim_hand.id
        self.state = state
        self.button = state.button_seat
        # full_board is always the complete 5-card runout (even on a
        # preflop fold-out); board only reveals up to the street reached.
        self.board = list(state.full_board) if state.full_board else list(state.board)
        self.seats = {s.seat: s for s in state.seats}
        self.pos_of = {s.seat: s.position for s in state.seats}
        # THE TRAP: position -> seat is per-hand only. Button rotates every
        # hand, so this map must never be reused across hands.
        self.seat_of = {s.position: s.seat for s in state.seats}
        self.history = state.action_history
        self.final_street = state.street


def load(session_id: str) -> tuple[dict[int, str], list[Hand], int]:
    """Seat->persona map + every hand whose state_json validates (NEW vs
    the reference: skip-on-failure instead of raw json.loads)."""
    with Session(engine) as db:
        seat_rows = db.exec(select(SimSeat).where(SimSeat.session_id == session_id)).all()
        seats = {r.seat_index: (r.persona_type or "HERO") for r in seat_rows}

        hand_rows = db.exec(
            select(SimHand).where(SimHand.session_id == session_id)
        ).all()

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
        hands.append(Hand(row, state))
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


def fmt_action(rec: dict, seats: dict[int, str], focus_seat: int) -> str:
    who = rec["pos"]
    persona = seats[rec["seat"]]
    tag = "**SELF**" if rec["seat"] == focus_seat else f"{persona}"
    amt = rec["amount"]
    act = rec["action"]
    if act in ("fold", "check"):
        body = act
    elif act == "post":
        body = f"post {amt}"
    else:
        to = rec["street_inv_before"] + amt
        pct_pot = round(100 * amt / rec["pot_before"]) if rec["pot_before"] > 0 else None
        pct_of_pot = f" [{pct_pot}% pot]" if pct_pot is not None else ""
        body = f"{act} {amt} (to {round(to, 2)}){pct_of_pot if act in ('bet', 'raise') else ''}"
        if act == "call" and rec["to_call"] > 0 and rec["pot_before"] > 0:
            price = round(100 * rec["to_call"] / (rec["pot_before"] + rec["to_call"]))
            body += f" [price {price}% pot odds]"
    return f"{who}({tag}) {body}"


def hand_block(
    hand: Hand,
    seats: dict[int, str],
    focus_seat: int,
    net: dict[int, float],
    showdown: list[int],
    acts: list[dict],
) -> str:
    sd = hand.seats[focus_seat]
    hc = sd.hole_cards
    lines = []
    hero_pos = hand.pos_of[focus_seat]
    lines.append(
        f"### Hand {hand.hand_no} — {hero_pos} — {hc[0]} {hc[1]} ({hand_class(*hc)}) "
        f"— stack {sd.stack_bb + sd.invested_total_bb:.0f}bb start"
    )
    b = hand.board
    lines.append(
        f"Board: {' '.join(b[:3]) if len(b) >= 3 else '(none)'}"
        + (f" | {b[3]}" if len(b) >= 4 else "")
        + (f" | {b[4]}" if len(b) >= 5 else "")
    )
    seat_line = ", ".join(
        f"{hand.pos_of[s]}={seats[s]}" for s in sorted(hand.seats, key=lambda x: hand.pos_of[x])
    )
    lines.append(f"Table: {seat_line}")
    by_street: dict[str, list[dict]] = defaultdict(list)
    for r in acts:
        by_street[r["street"]].append(r)
    for street in ("preflop", "flop", "turn", "river"):
        if street not in by_street:
            continue
        cat = ""
        if street != "preflop":
            sb = street_board(b, street)
            if len(sb) >= 3:
                cat = f"  → SELF holds: **{_hand_category(tuple(hc), sb)}**"
        pot_at = by_street[street][0]["pot_before"]
        lines.append(f"**{street.upper()}** (pot {pot_at}bb){cat}")
        lines.append("  " + " · ".join(fmt_action(r, seats, focus_seat) for r in by_street[street]))
    res = net.get(focus_seat, 0.0)
    sdw = "showdown" if focus_seat in showdown else "no showdown"
    lines.append(f"**Result:** SELF net {res:+.2f}bb ({sdw}; hand ended on {hand.final_street})")
    if showdown:
        shown = ", ".join(
            f"{hand.pos_of[s]}={seats[s]} {' '.join(hand.seats[s].hole_cards)}"
            for s in showdown
            if s != focus_seat
        )
        if shown:
            lines.append(f"  Opponents shown: {shown}")
    return "\n".join(lines)


def stats_for(seat_list, seats, hands, replays, nets):
    """Compute standard poker tracking stats for a set of seats."""
    st: dict[str, float] = defaultdict(float)
    per_pos: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for h in hands:
        acts = replays[h.hand_no]
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
            if prior_raise_before_first:
                st["faced_raise"] += 1
                if first["action"] == "raise":
                    st["3bet"] += 1
                elif first["action"] == "call":
                    st["call_vs_raise"] += 1
                else:
                    st["fold_vs_raise"] += 1
            # postflop
            saw_flop = any(a["street"] == "flop" for a in mine) or (
                h.seats[seat].status != "folded" and len(h.board) >= 3 and vpip
            )
            if saw_flop:
                st["saw_flop"] += 1
                if nets[h.hand_no].get(seat, 0) > 0:
                    st["won_after_flop"] += 1
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
            if h.seats[seat].status != "folded" and len(h.board) == 5:
                # reached the end alive on a full board
                if any(a["street"] == "river" for a in mine) or h.final_street == "river":
                    st["wtsd_num"] += 1
                    if nets[h.hand_no].get(seat, 0) > 0:
                        st["wsd_win"] += 1
    return st, per_pos


def pct(n: float, d: float) -> str:
    return f"{100 * n / d:.1f}%" if d else "n/a"


def stats_block(st: dict, per_pos: dict) -> str:
    h = st["hands"]
    sf = st["saw_flop"]
    fr = st["faced_raise"]
    lines = [
        "## Tracking stats",
        "",
        "| Stat | Value | n |",
        "|---|---|---|",
        f"| Hands dealt in | {int(h)} | |",
        f"| VPIP | {pct(st['vpip'], h)} | {int(st['vpip'])}/{int(h)} |",
        f"| PFR | {pct(st['pfr'], h)} | {int(st['pfr'])}/{int(h)} |",
        f"| Limp (unraised pot) | {pct(st['limp'], h)} | {int(st['limp'])}/{int(h)} |",
        f"| Open-raise (first in) | {pct(st['open_raise'], h)} | "
        f"{int(st['open_raise'])}/{int(h)} |",
        f"| 3bet+ (faced a raise, raised) | {pct(st['3bet'], fr)} | {int(st['3bet'])}/{int(fr)} |",
        f"| Call vs raise | {pct(st['call_vs_raise'], fr)} | "
        f"{int(st['call_vs_raise'])}/{int(fr)} |",
        f"| Fold vs raise | {pct(st['fold_vs_raise'], fr)} | "
        f"{int(st['fold_vs_raise'])}/{int(fr)} |",
        f"| Saw flop | {pct(sf, h)} | {int(sf)}/{int(h)} |",
        (
            f"| Won when saw flop (WWSF) | {pct(st['won_after_flop'], sf)} | "
            f"{int(st['won_after_flop'])}/{int(sf)} |"
        ),
        (
            f"| Went to showdown (of flops seen) (WTSD) | {pct(st['wtsd_num'], sf)} | "
            f"{int(st['wtsd_num'])}/{int(sf)} |"
        ),
        (
            f"| Won at showdown | {pct(st['wsd_win'], st['wtsd_num'])} | "
            f"{int(st['wsd_win'])}/{int(st['wtsd_num'])} |"
        ),
        "",
        "### Per-street postflop action mix",
        "",
        (
            "| Street | Actions | Bet/Raise | Call | Check | Fold | Fold-when-facing-bet | "
            "Raise-when-facing-bet | Avg bet/raise size (% pot) |"
        ),
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for s in ("flop", "turn", "river"):
        tot = st[f"{s}_agg"] + st[f"{s}_call"] + st[f"{s}_check"] + st[f"{s}_fold"]
        avg = f"{st[f'{s}_sizesum'] / st[f'{s}_sizen']:.0f}%" if st[f"{s}_sizen"] else "n/a"
        lines.append(
            f"| {s} | {int(tot)} | {int(st[f'{s}_agg'])} | {int(st[f'{s}_call'])} | "
            f"{int(st[f'{s}_check'])} | {int(st[f'{s}_fold'])} | "
            f"{pct(st[f'{s}_fold_vs_bet'], st[f'{s}_faced_bet'])} "
            f"({int(st[f'{s}_fold_vs_bet'])}/{int(st[f'{s}_faced_bet'])}) | "
            f"{pct(st[f'{s}_raise_vs_bet'], st[f'{s}_faced_bet'])} | {avg} |"
        )
    lines += ["", "### By position", "", "| Pos | Hands | VPIP | PFR |", "|---|---|---|---|"]
    order = ["UTG", "UTG1", "UTG2", "LJ", "HJ", "CO", "BTN", "SB", "BB"]
    for p in order:
        if p not in per_pos:
            continue
        d = per_pos[p]
        vpip_pct = pct(d["vpip"], d["hands"])
        pfr_pct = pct(d["pfr"], d["hands"])
        lines.append(f"| {p} | {int(d['hands'])} | {vpip_pct} | {pfr_pct} |")
    return "\n".join(lines)


def build_packets(session_id: str, seats, hands, replays, settles):
    """Returns (summary_markdown, {persona: packet_markdown})."""
    nets = {k: v[0] for k, v in settles.items()}
    shows = {k: v[1] for k, v in settles.items()}

    by_persona: dict[str, list[int]] = defaultdict(list)
    for s, p in seats.items():
        by_persona[p].append(s)

    summary_rows = []
    packets: dict[str, str] = {}
    for persona, seat_list in sorted(by_persona.items()):
        st, per_pos = stats_for(seat_list, seats, hands, replays, nets)
        played, folded = [], []
        for h in hands:
            for seat in seat_list:
                if seat not in h.seats:
                    continue
                acts = replays[h.hand_no]
                mine = [a for a in acts if a["seat"] == seat and a["action"] != "post"]
                if not mine:
                    continue
                voluntary = any(a["action"] in ("call", "raise", "bet") for a in mine)
                hc = h.seats[seat].hole_cards
                if voluntary:
                    block = hand_block(
                        h, seats, seat, nets[h.hand_no], shows[h.hand_no], acts
                    )
                    played.append(block)
                else:
                    # A LIMP ahead routes to the vs_limpers node, NOT unopened.
                    before = [
                        a
                        for a in acts[: acts.index(mine[0])]
                        if a["street"] == "preflop" and a["action"] != "post"
                    ]
                    limped = any(
                        a["action"] == "call" and a["pos"] not in ("SB", "BB") for a in before
                    )
                    if any(a["action"] in ("raise", "bet") for a in before):
                        facing = "vs_rfi+"
                    elif limped:
                        facing = "vs_limpers"
                    else:
                        facing = "unopened"
                    folded.append(
                        f"- H{h.hand_no} {h.pos_of[seat]} {hc[0]}{hc[1]} "
                        f"({hand_class(*hc)}) folded preflop ({facing})"
                    )
        title = persona if persona != "HERO" else "HERO (the human)"
        body = "\n".join(
            [
                f"# {title} — every hand from session {session_id}",
                "",
                f"Seats occupied by this persona: {sorted(seat_list)} "
                f"(9-max table, button rotates each hand).",
                f"Hands where this persona voluntarily put money in: **{len(played)}**. "
                f"Preflop folds: **{len(folded)}**.",
                "",
                "In every hand block below, **SELF** = this persona. Other actors are "
                "labelled with their own persona type. Amounts are chips ADDED by that "
                "action (increments), `to X` = total that player has in for the street. "
                "`SELF holds:` is the engine's own made-hand category for this persona's "
                "cards on that street.",
                "",
                stats_block(st, per_pos),
                "",
                "## Hands played (voluntary money in)",
                "",
                "\n\n".join(played),
                "",
                "## Preflop folds (range-width evidence — what it threw away, and from where)",
                "",
                "\n".join(folded) if folded else "(none)",
            ]
        )
        packets[persona] = body
        summary_rows.append(
            f"| {persona} | {pct(st['vpip'], st['hands'])} | {pct(st['pfr'], st['hands'])} | "
            f"{pct(st['3bet'], st['faced_raise'])} | {pct(st['limp'], st['hands'])} | "
            f"{pct(st['won_after_flop'], st['saw_flop'])} | "
            f"{pct(st['wtsd_num'], st['saw_flop'])} |"
        )

    summary = "\n".join(
        [
            f"## Per-persona summary — session {session_id} ({len(hands)} hands)",
            "",
            "| persona | VPIP | PFR | 3bet | limp | WWSF | WTSD |",
            "|---|---|---|---|---|---|---|",
            *summary_rows,
        ]
    )
    return summary, packets


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a stored Simulate session into per-persona hand "
        "packets + tracking stats (VPIP/PFR/3bet/limp/WWSF/WTSD)."
    )
    parser.add_argument("--session", required=True, help="sim_session.id (uuid4 hex)")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="directory to write one markdown packet per persona (+ a summary). "
        "Omit to print everything to stdout instead.",
    )
    args = parser.parse_args()

    seats, hands, n_skipped = load(args.session)
    if not hands:
        print(f"no hands found for session {args.session!r} (skipped {n_skipped})", file=sys.stderr)
        raise SystemExit(1)

    replays = {h.hand_no: replay(h) for h in hands}
    settles = {h.hand_no: settle_hand(h) for h in hands}

    summary, packets = build_packets(args.session, seats, hands, replays, settles)

    if n_skipped:
        print(f"skipped {n_skipped} hand(s) with unparseable state_json", file=sys.stderr)

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        for persona, body in packets.items():
            (args.out / f"{persona}.md").write_text(body)
        (args.out / "SUMMARY.md").write_text(summary)
        print(f"wrote {len(packets)} packet(s) to {args.out}")
        print()
        print(summary)
    else:
        print(summary)
        print()
        for body in packets.values():
            print(body)
            print()


if __name__ == "__main__":
    main()
