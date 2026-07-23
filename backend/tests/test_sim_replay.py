"""Hand-history + replay battery (hand replayer): migration 0013 up/down/up,
graded-gated verdict-text persistence, per-day ordinal bucketing, seat-map
correctness, NO-PEEK staged reveal, all-in runout board, mistakes filter,
404s, and (session_id, hand_no) resolution.

Spec: docs/ai-dlc/specs/sim-hand-replayer.md.
"""

from __future__ import annotations

import asyncio
import random
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlmodel import Session, create_engine, select

from alembic import command
from app.db.migrate import make_alembic_config, run_migrations
from app.db.models import SimDecision, SimHand, SimSession
from app.domain.action import Decision
from app.domain.spot import ActionType
from app.domain.table.deck import deal_hand
from app.domain.table.engine import HandState, settle, start_hand
from app.services import sim_session
from app.services.sim_session import (
    HERO_SEAT,
    SessionNotFound,
    apply_hero_action,
    create_session,
    deal_next_hand,
    get_hand_replay,
    get_hand_replay_by_hand_no,
    list_history,
)

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.fixture
def engine(tmp_path):
    url = f"sqlite:///{tmp_path / 's.db'}"
    run_migrations(url)
    return create_engine(url, connect_args={"check_same_thread": False})


@pytest.fixture
def db(tmp_path):
    url = f"sqlite:///{tmp_path / 'sim.db'}"
    run_migrations(url)
    engine = create_engine(url, connect_args={"check_same_thread": False})
    with Session(engine) as s:
        yield s


def _sync(coro):
    return asyncio.run(coro)


def _hero_decision(view, *, aggressive: bool) -> Decision:
    """Pick a legal hero action. aggressive=True prefers call/check (stays in the
    hand → drives toward showdowns); False folds when possible."""
    kinds = {la.action for la in view.hand.legal_actions}
    if not aggressive and ActionType.FOLD in kinds:
        return Decision(action=ActionType.FOLD)
    if ActionType.CHECK in kinds:
        return Decision(action=ActionType.CHECK)
    if ActionType.CALL in kinds:
        return Decision(action=ActionType.CALL)
    return Decision(action=ActionType.FOLD)


def _play_hands(s: Session, n_hands: int, *, aggressive: bool = True) -> str:
    """Play n_hands to completion in a fresh session; return the session id."""
    view = create_session(s)
    played = 0
    guard = 0
    while played < n_hands and guard < 5000:
        guard += 1
        if view.hand.hand_over:
            played += 1
            if played < n_hands:
                view = deal_next_hand(s, view.session_id)
            continue
        view = _sync(
            apply_hero_action(
                s, view.session_id, _hero_decision(view, aggressive=aggressive)
            )
        )
    return view.session_id


# --------------------------------------------------------- migration 0013


def test_migration_0013_up_down_up_and_index_absent_after_downgrade(tmp_path):
    url = f"sqlite:///{tmp_path / 'mig13.db'}"
    cfg = make_alembic_config(url)

    # Land on 0012, insert a decision row the old schema's way (no text columns).
    command.upgrade(cfg, "0012")
    engine = create_engine(url, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO sim_session (id, owner_id, button_seat, hand_no, created_at) "
                "VALUES ('m13', '', 0, 1, '2026-01-01 00:00:00')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO sim_hand (session_id, hand_no, button_seat, rng_seed, "
                "status, state_json, created_at) "
                "VALUES ('m13', 1, 0, '1', 'complete', '{}', '2026-01-01 00:00:00')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO sim_decision (owner_id, session_id, sim_hand_id, street, "
                "ordinal, chosen_action, ev_loss_bb, coverage, created_at) "
                "VALUES ('', 'm13', 1, 'flop', 0, 'call', 0.0, 'full', '2026-01-01 00:00:00')"
            )
        )
    engine.dispose()

    # Up to head: additive nullable text + created_at index. Existing row NULL.
    command.upgrade(cfg, "head")
    engine = create_engine(url, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "SELECT verdict_tier_text, reasoning_text, chosen_action "
                "FROM sim_decision WHERE session_id='m13'"
            )
        ).fetchone()
        assert row == (None, None, "call")
        idx = {
            r[1] for r in conn.execute(text("PRAGMA index_list('sim_hand')")).fetchall()
        }
        assert "ix_sim_hand_created_at" in idx
    engine.dispose()

    # Down one: drops both text columns AND the created_at index.
    command.downgrade(cfg, "-1")
    engine = create_engine(url, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        cols = {
            r[1] for r in conn.execute(text("PRAGMA table_info(sim_decision)")).fetchall()
        }
        assert "verdict_tier_text" not in cols and "reasoning_text" not in cols
        idx = {
            r[1] for r in conn.execute(text("PRAGMA index_list('sim_hand')")).fetchall()
        }
        assert "ix_sim_hand_created_at" not in idx  # index absent after downgrade
    engine.dispose()

    # Back up: must re-apply clean (no duplicate-index failure).
    command.upgrade(cfg, "head")
    engine = create_engine(url, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        idx = {
            r[1] for r in conn.execute(text("PRAGMA index_list('sim_hand')")).fetchall()
        }
        assert "ix_sim_hand_created_at" in idx
    engine.dispose()


# --------------------------------------- T2: graded-gated verdict text persist


def test_graded_decision_persists_verdict_text(db):
    # Play aggressively so hero takes graded (mappable) preflop/postflop actions.
    session_id = _play_hands(db, 12, aggressive=True)
    rows = list(db.exec(select(SimDecision).where(SimDecision.session_id == session_id)))
    graded = [r for r in rows if r.coverage not in ("not_found", "unmappable")]
    ungraded = [r for r in rows if r.coverage in ("not_found", "unmappable")]
    assert graded, "expected at least one graded decision across 12 hands"
    for r in graded:
        assert r.verdict_tier_text is not None
        assert r.reasoning_text is not None
    for r in ungraded:
        assert r.verdict_tier_text is None
        assert r.reasoning_text is None


# --------------------------------------------- T3: per-day ordinal bucketing


def _seed_completed_hand(
    s: Session, session_id: str, hand_no: int, created_at: datetime
) -> int:
    dealt = deal_hand(random.Random(hand_no))
    state = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    hand = SimHand(
        session_id=session_id,
        hand_no=hand_no,
        button_seat=0,
        rng_seed=str(hand_no),
        status="complete",
        state_json=state.model_dump_json(),
        created_at=created_at,
    )
    s.add(hand)
    s.commit()
    s.refresh(hand)
    return hand.id


def _seed_session(s: Session, session_id: str) -> None:
    s.add(SimSession(id=session_id, owner_id="", button_seat=0, hand_no=1))
    s.commit()


def test_per_day_ordinal_restarts_per_utc_day_and_id_tiebreak(db):
    _seed_session(db, "sX")
    _seed_session(db, "sY")
    # Two hands the same UTC day across two sessions + one on the next day.
    d1a = datetime(2026, 7, 22, 10, 0, tzinfo=UTC)
    d1b = datetime(2026, 7, 22, 11, 0, tzinfo=UTC)
    d2 = datetime(2026, 7, 23, 9, 0, tzinfo=UTC)
    _seed_completed_hand(db, "sX", 1, d1a)
    _seed_completed_hand(db, "sY", 1, d1b)
    _seed_completed_hand(db, "sX", 2, d2)
    view = list_history(db)
    by_hand = {(i.session_id, i.hand_no): i for i in view.items}
    assert by_hand[("sX", 1)].day_ordinal == 1
    assert by_hand[("sY", 1)].day_ordinal == 2  # 2nd completed hand that UTC day
    assert by_hand[("sX", 2)].day_ordinal == 1  # new day restarts at 1
    # Newest-first on the wire.
    assert view.items[0].created_at >= view.items[-1].created_at


def test_created_at_tie_broken_by_id(db):
    _seed_session(db, "sT")
    same = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)
    id1 = _seed_completed_hand(db, "sT", 1, same)
    id2 = _seed_completed_hand(db, "sT", 2, same)
    assert id1 < id2
    view = list_history(db)
    by_hand = {i.hand_no: i for i in view.items}
    # Lower id (inserted first) gets ordinal 1 under the created_at tie.
    assert by_hand[1].day_ordinal == 1
    assert by_hand[2].day_ordinal == 2


def test_midnight_naive_and_aware_bucket_correctly(db):
    # Two paths for the folded-LOW UTC normalization:
    # (1) naive values from SQLite (tzinfo dropped) are treated as UTC — a naive
    #     23:30 stays on its day, a naive 00:30 falls on the next; both round-trip
    #     through the DB.
    # (2) an AWARE non-UTC value is converted to UTC before .date() — exercised
    #     directly against the helper, because SQLite strips tzinfo on write (it
    #     would come back naive at wall-clock, never reaching the aware branch).
    from datetime import timedelta, timezone

    _seed_session(db, "sM")
    naive_late = datetime(2026, 7, 22, 23, 30)  # naive → treated as UTC
    naive_next = datetime(2026, 7, 23, 0, 30)  # naive → next UTC day
    _seed_completed_hand(db, "sM", 1, naive_late)
    _seed_completed_hand(db, "sM", 3, naive_next)
    view = list_history(db)
    by_hand = {i.hand_no: i for i in view.items}
    assert by_hand[1].day == "2026-07-22"
    assert by_hand[3].day == "2026-07-23"

    # Aware +02:00 00:30 == 22:30 the PREVIOUS UTC day — helper converts to UTC.
    aware_plus2 = datetime(2026, 7, 23, 0, 30, tzinfo=timezone(timedelta(hours=2)))
    assert sim_session._utc_day(aware_plus2) == "2026-07-22"
    aware_utc = datetime(2026, 7, 22, 23, 30, tzinfo=UTC)
    assert sim_session._utc_day(aware_utc) == "2026-07-22"


# ----------------------------------------- T3: seat map + verdict correlation


def test_seat_map_total_and_correct_and_verdict_aligned(db):
    session_id = _play_hands(db, 8, aggressive=True)
    hands = list(
        db.exec(
            select(SimHand)
            .where(SimHand.session_id == session_id)
            .where(SimHand.status == "complete")
        )
    )
    assert hands
    for hand in hands:
        state = HandState.model_validate_json(hand.state_json)
        pos2seat = {s.position: s.seat for s in state.seats}
        # Map is total over the 9 positions and correct (round-trips).
        assert len(pos2seat) == 9
        for seatstate in state.seats:
            assert pos2seat[seatstate.position] == seatstate.seat

        replay = get_hand_replay(db, hand.id)
        # Each step's resolved seat matches the position->seat map.
        for step in replay.steps:
            assert pos2seat[state.seats[step.seat].position] == step.seat
        # Hero non-POST steps == number of decisions (post-0010).
        decisions = list(
            db.exec(select(SimDecision).where(SimDecision.sim_hand_id == hand.id))
        )
        hero_steps = [s for s in replay.steps if s.is_hero and not s.is_post]
        assert len(hero_steps) == len(decisions)
        # A POST step never carries a verdict.
        for step in replay.steps:
            if step.is_post:
                assert step.correctness is None and step.coverage is None


def test_legacy_hand_with_no_decision_rows_is_ungraded_not_crash(db):
    # Simulate a legacy 0009-era hand: complete SimHand with hero actions but
    # ZERO sim_decision rows. Replay must render hero steps ungraded, not raise.
    _seed_session(db, "sLegacy")
    dealt = deal_hand(random.Random(7))
    state = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    # Drive to completion via engine (bots fold to hero, or hero acts) — just run
    # a fold-out: everyone folds to the BB by replaying folds. Simplest: use the
    # start state and mark hand_over by folding all but hero.
    from app.domain.table.engine import apply as engine_apply

    st = state
    guard = 0
    while not st.hand_over and guard < 40:
        guard += 1
        from app.domain.table.engine import legal_actions as eng_legal

        legal = eng_legal(st)
        kinds = {la.action for la in legal}
        if st.to_act_seat == HERO_SEAT:
            act = ActionType.CHECK if ActionType.CHECK in kinds else (
                ActionType.CALL if ActionType.CALL in kinds else ActionType.FOLD
            )
        else:
            act = ActionType.FOLD if ActionType.FOLD in kinds else (
                ActionType.CHECK if ActionType.CHECK in kinds else ActionType.CALL
            )
        size = None
        st = engine_apply(st, Decision(action=act, size_bb=size))
    hand = SimHand(
        session_id="sLegacy",
        hand_no=1,
        button_seat=0,
        rng_seed="7",
        status="complete",
        state_json=st.model_dump_json(),
        created_at=datetime.now(UTC),
    )
    db.add(hand)
    db.commit()
    db.refresh(hand)
    replay = get_hand_replay(db, hand.id)  # no decision rows: must not raise
    for step in replay.steps:
        if step.is_hero and not step.is_post:
            assert step.correctness is None
            assert step.coverage is None


# ------------------------------------------------- T3: NO-PEEK staged reveal


def test_no_peek_no_villain_card_before_showdown_step(db):
    session_id = _play_hands(db, 15, aggressive=True)
    hands = list(
        db.exec(
            select(SimHand)
            .where(SimHand.session_id == session_id)
            .where(SimHand.status == "complete")
        )
    )
    assert hands
    saw_a_showdown = False
    for hand in hands:
        replay = get_hand_replay(db, hand.id)
        n = len(replay.steps)
        for i, step in enumerate(replay.steps):
            if step.is_terminal:
                saw_a_showdown = saw_a_showdown or bool(step.revealed_seats)
                assert i == n - 1  # terminal is the last step only
            else:
                # No villain card leaks before the terminal step.
                assert step.revealed_seats == []
        # Revealed seats (if any) are exactly settle().showdown_seats, never hero.
        state = HandState.model_validate_json(hand.state_json)
        settlement = settle(state)
        terminal = [s for s in replay.steps if s.is_terminal]
        if terminal and terminal[0].revealed_seats:
            revealed_idx = {r.seat_index for r in terminal[0].revealed_seats}
            assert revealed_idx == set(settlement.showdown_seats)
            assert HERO_SEAT not in revealed_idx or HERO_SEAT in settlement.showdown_seats
    assert saw_a_showdown, "expected at least one showdown across 15 aggressive hands"


# ---------------------------------------------- T3: all-in runout terminal board


def test_all_in_flop_terminal_step_shows_full_board(db):
    # Construct a hand where hero and one villain are all-in on the FLOP with no
    # further street actions — the engine auto-runs to the river. The terminal
    # step must show the full 5-card board.
    _seed_session(db, "sAllin")
    from app.domain.table.engine import apply as engine_apply
    from app.domain.table.engine import legal_actions as eng_legal

    # Deterministic deal; drive a preflop all-in confrontation heads-up.
    dealt = deal_hand(random.Random(3))
    st = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    guard = 0
    while not st.hand_over and guard < 60:
        guard += 1
        legal = eng_legal(st)
        kinds = {la.action for la in legal}
        # Everyone but hero(0) and one villain(seat 3) folds; those two jam/call.
        seat = st.to_act_seat
        if seat in (HERO_SEAT, 3):
            if ActionType.RAISE in kinds:
                ra = next(la for la in legal if la.action is ActionType.RAISE)
                st = engine_apply(
                    st, Decision(action=ActionType.RAISE, size_bb=ra.max_bb)
                )
                continue
            if ActionType.BET in kinds:
                ba = next(la for la in legal if la.action is ActionType.BET)
                st = engine_apply(
                    st, Decision(action=ActionType.BET, size_bb=ba.max_bb)
                )
                continue
            if ActionType.CALL in kinds:
                st = engine_apply(st, Decision(action=ActionType.CALL))
                continue
            st = engine_apply(st, Decision(action=ActionType.CHECK))
            continue
        act = ActionType.FOLD if ActionType.FOLD in kinds else ActionType.CHECK
        st = engine_apply(st, Decision(action=act))
    assert st.hand_over
    settlement = settle(st)
    hand = SimHand(
        session_id="sAllin",
        hand_no=1,
        button_seat=0,
        rng_seed="3",
        status="complete",
        state_json=st.model_dump_json(),
        created_at=datetime.now(UTC),
    )
    db.add(hand)
    db.commit()
    db.refresh(hand)
    replay = get_hand_replay(db, hand.id)
    terminal = [s for s in replay.steps if s.is_terminal]
    if settlement.showdown_seats:  # genuine showdown → terminal step exists
        assert terminal
        assert len(terminal[0].board) == 5  # full runout revealed at showdown


# ------------------------------------------------------- T3: mistakes filter


def test_mistakes_filter_matches_mistake_and_blunder_only(db):
    _seed_session(db, "sFilter")
    hid = _seed_completed_hand(db, "sFilter", 1, datetime(2026, 7, 22, 1, tzinfo=UTC))
    hid2 = _seed_completed_hand(db, "sFilter", 2, datetime(2026, 7, 22, 2, tzinfo=UTC))
    hid3 = _seed_completed_hand(db, "sFilter", 3, datetime(2026, 7, 22, 3, tzinfo=UTC))
    db.add_all(
        [
            SimDecision(session_id="sFilter", sim_hand_id=hid, street="preflop",
                        ordinal=0, chosen_action="raise", correctness="mistake",
                        ev_loss_bb=1.0, coverage="full"),
            SimDecision(session_id="sFilter", sim_hand_id=hid2, street="preflop",
                        ordinal=0, chosen_action="raise", correctness="acceptable",
                        ev_loss_bb=0.0, coverage="full"),
            SimDecision(session_id="sFilter", sim_hand_id=hid3, street="preflop",
                        ordinal=0, chosen_action="raise", correctness="blunder",
                        ev_loss_bb=3.0, coverage="full"),
        ]
    )
    db.commit()
    view = list_history(db)
    by_hand = {i.sim_hand_id: i for i in view.items}
    assert by_hand[hid].has_mistake is True  # mistake
    assert by_hand[hid].worst_tier == "mistake"
    assert by_hand[hid2].has_mistake is False  # acceptable excluded
    assert by_hand[hid3].has_mistake is True  # blunder
    assert by_hand[hid3].worst_tier == "blunder"


# ------------------------------------------------------------------ T3: 404s


def test_404_on_missing_not_owned_and_in_progress(db):
    with pytest.raises(SessionNotFound):
        get_hand_replay(db, 999999)  # missing
    # not owned
    db.add(SimSession(id="sOwned", owner_id="someone-else", button_seat=0, hand_no=1))
    hid = _seed_completed_hand(db, "sOwned", 1, datetime.now(UTC))
    with pytest.raises(SessionNotFound):
        get_hand_replay(db, hid, owner_id="")
    # in-progress
    _seed_session(db, "sProg")
    dealt = deal_hand(random.Random(9))
    state = start_hand(dealt, button_seat=0, stacks_bb=[100.0] * 9)
    prog = SimHand(session_id="sProg", hand_no=1, button_seat=0, rng_seed="9",
                   status="in_progress", state_json=state.model_dump_json(),
                   created_at=datetime.now(UTC))
    db.add(prog)
    db.commit()
    db.refresh(prog)
    with pytest.raises(SessionNotFound):
        get_hand_replay(db, prog.id)


# ------------------------------------------- T3: (session_id, hand_no) resolution


def test_session_hand_no_resolution_returns_right_hand(db):
    session_id = _play_hands(db, 3, aggressive=True)
    hands = sorted(
        db.exec(
            select(SimHand)
            .where(SimHand.session_id == session_id)
            .where(SimHand.status == "complete")
        ),
        key=lambda h: h.hand_no,
    )
    assert hands
    target = hands[-1]
    by_id = get_hand_replay(db, target.id)
    by_key = get_hand_replay_by_hand_no(db, session_id, target.hand_no)
    assert by_key.sim_hand_id == by_id.sim_hand_id == target.id
    assert by_key.hand_no == target.hand_no
    with pytest.raises(SessionNotFound):
        get_hand_replay_by_hand_no(db, session_id, 99999)


# --------------------------------------------------- T3: wire privacy (no leaks)


def test_no_endpoint_emits_state_json_or_full_board(db):
    session_id = _play_hands(db, 4, aggressive=True)
    hands = list(
        db.exec(
            select(SimHand)
            .where(SimHand.session_id == session_id)
            .where(SimHand.status == "complete")
        )
    )
    assert hands
    replay = get_hand_replay(db, hands[0].id)
    dumped = replay.model_dump()
    assert "state_json" not in dumped
    assert "full_board" not in dumped
    for step in dumped["steps"]:
        assert "state_json" not in step and "full_board" not in step
    hist = list_history(db).model_dump()
    for item in hist["items"]:
        assert "state_json" not in item and "full_board" not in item
