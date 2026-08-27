"""Two-mode Simulate T3: the completed-hand count and the server-side deal gate.

Covers spec paragraphs 11-12 (`docs/ai-dlc/specs/two-mode-simulate.md`): the
count is `hand_no - (0 if hand_over else 1)`, and `deal_next_hand()` refuses to
advance a Challenge session that has reached the gate with no stored blind
check. Nothing here writes `blind_check_json` for real — that is T4; the tests
store the value directly, in the shape T4 will produce.
"""

from __future__ import annotations

import pytest
from sqlmodel import Session, create_engine, select
from test_sim_session import _play_current_hand  # drives the hero to hand end

from app.db.migrate import run_migrations
from app.db.models import SimHand, SimSession
from app.schemas.simulate import BlindCheckGuess, BlindCheckView
from app.services.sim_session import (
    BLIND_CHECK_HAND_GATE,
    _completed_hands,
    create_session,
    deal_next_hand,
    restore_session,
)


@pytest.fixture
def db(tmp_path):
    url = f"sqlite:///{tmp_path / 'two_mode_gate.db'}"
    run_migrations(url)
    engine = create_engine(url, connect_args={"check_same_thread": False})
    with Session(engine) as s:
        yield s


def _stored_check(*, skipped: bool) -> str:
    """A stored blind-check result of the shape T4's endpoint will write."""
    guesses = (
        []
        if skipped
        else [
            BlindCheckGuess(seat_index=i, guess="tag", actual="tag", correct=True)
            for i in (3, 5, 7)
        ]
    )
    return BlindCheckView(
        seats=[3, 5, 7],
        submitted=True,
        skipped=skipped,
        guesses=guesses,
        score=None if skipped else 3,
    ).model_dump_json()


def _renumber(db: Session, session_id: str, hand_no: int) -> SimSession:
    """Move the session's current hand to `hand_no` without playing the hands
    before it.

    Faithful because the gate reads exactly two things — `session.hand_no` and
    the status of the row `_current_hand()` selects, the one whose `hand_no`
    equals the counter — and real play leaves precisely this pair. The only
    difference from a genuinely played-out session is the absence of the earlier
    `SimHand` rows, which no code path in `deal_next_hand()` reads. Playing 200
    real hands would take minutes per test for no extra coverage.
    """
    session = db.get(SimSession, session_id)
    hand = db.exec(
        select(SimHand)
        .where(SimHand.session_id == session_id)
        .where(SimHand.hand_no == session.hand_no)
    ).one()
    # A setup that renumbered onto an existing row would leave two hands with
    # one number and `_current_hand()` picking arbitrarily between them. Only
    # reachable if the gate is ever lowered below the hands played here.
    assert hand_no >= session.hand_no, "renumber target is already a played hand"
    hand.hand_no = hand_no
    session.hand_no = hand_no
    db.add(hand)
    db.add(session)
    db.commit()
    return session


def _settled_at(
    db: Session, hand_no: int, mode: str = "challenge", *, with_recap: bool = False
) -> SimSession:
    """A session whose hand `hand_no` has been played out and is over.

    `with_recap` keeps dealing until the hero actually made a decision in the
    settled hand, since a hand that ends before the hero ever acts has nothing
    to recap.
    """
    view = create_session(db, mode=mode)
    for _ in range(50):
        if not view.hand.hand_over:
            view = _play_current_hand(db, view, fold_if_possible=True)
        if not with_recap or view.hand.recap:
            return _renumber(db, view.session_id, hand_no)
        view = deal_next_hand(db, view.session_id)
    pytest.fail("no settled hand with a hero decision in 50 deals")


def _live_at(db: Session, hand_no: int, mode: str = "challenge") -> SimSession:
    """A session whose hand `hand_no` is dealt and still in progress."""
    view = create_session(db, mode=mode)
    for _ in range(50):
        if not view.hand.hand_over:
            return _renumber(db, view.session_id, hand_no)
        view = deal_next_hand(db, view.session_id)
    pytest.fail("no live hand in 50 deals")


def _current(db: Session, session: SimSession) -> SimHand:
    return db.exec(
        select(SimHand)
        .where(SimHand.session_id == session.id)
        .where(SimHand.hand_no == session.hand_no)
    ).one()


# ------------------------------------------------- the count at the boundary


def test_completed_hands_after_hand_199_settles_is_199(db):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE - 1)
    assert _completed_hands(session, _current(db, session)) == 199
    assert _completed_hands(session, _current(db, session)) < BLIND_CHECK_HAND_GATE


def test_completed_hands_while_hand_200_is_live_is_199(db):
    session = _live_at(db, BLIND_CHECK_HAND_GATE)
    # The hand in play is not a hand the player has completed.
    assert _completed_hands(session, _current(db, session)) == 199
    assert _completed_hands(session, _current(db, session)) < BLIND_CHECK_HAND_GATE


def test_completed_hands_after_hand_200_settles_is_200(db):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    # The counter has NOT moved on from 200 here — the naive `hand_no - 1`
    # reads 199 at this exact point and would let hand 201 be dealt.
    assert _completed_hands(session, _current(db, session)) == 200
    assert _completed_hands(session, _current(db, session)) == BLIND_CHECK_HAND_GATE


def test_completed_hands_while_hand_201_is_live_is_200(db):
    session = _live_at(db, BLIND_CHECK_HAND_GATE + 1)
    assert _completed_hands(session, _current(db, session)) == 200


def test_completed_hands_with_no_dealt_hand_matches_a_live_one(db):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    # An undealt hand_no counts the same as a live one: hands 1..N-1 are done.
    assert _completed_hands(session, None) == BLIND_CHECK_HAND_GATE - 1


def test_server_and_wire_derivations_agree_at_the_boundary(db):
    """The client computes the count from `hand_no` and `hand_over` on the wire;
    the server computes it from the row's status. Pin them to one value."""
    for build in (_settled_at, _live_at):
        session = build(db, BLIND_CHECK_HAND_GATE)
        view = restore_session(db, session.id)
        wire = view.hand.hand_no - (0 if view.hand.hand_over else 1)
        assert _completed_hands(session, _current(db, session)) == wire


# ------------------------------------------------------------- the deal gate


def test_gate_does_not_bar_at_199_completed_hands(db):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE - 1)
    view = deal_next_hand(db, session.id)
    assert view.hand.hand_no == BLIND_CHECK_HAND_GATE


def test_gate_bars_challenge_at_the_gate_and_mutates_nothing(db):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    before = restore_session(db, session.id)
    button_seat = session.button_seat
    hand_rows = len(db.exec(select(SimHand).where(SimHand.session_id == session.id)).all())

    view = deal_next_hand(db, session.id)

    # The settled hand comes back unchanged, not an error and not a new deal.
    assert view.hand.hand_no == before.hand.hand_no == BLIND_CHECK_HAND_GATE
    assert view.hand.board == before.hand.board
    assert view.hand.hand_over
    db.expire_all()
    after = db.get(SimSession, session.id)
    assert after.hand_no == BLIND_CHECK_HAND_GATE
    assert after.button_seat == button_seat
    assert len(db.exec(select(SimHand).where(SimHand.session_id == session.id)).all()) == hand_rows


def test_gate_stays_barred_past_the_gate(db):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE + 50)
    view = deal_next_hand(db, session.id)
    assert view.hand.hand_no == BLIND_CHECK_HAND_GATE + 50


def test_gate_does_not_bar_training_at_the_gate(db):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE, mode="training")
    view = deal_next_hand(db, session.id)
    assert view.hand.hand_no == BLIND_CHECK_HAND_GATE + 1


def test_stored_check_resumes_the_deal(db):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    session.blind_check_json = _stored_check(skipped=False)
    db.add(session)
    db.commit()

    view = deal_next_hand(db, session.id)
    assert view.hand.hand_no == BLIND_CHECK_HAND_GATE + 1
    assert view.blind_check is not None and view.blind_check.score == 3


def test_skipped_check_also_resumes_the_deal(db):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    session.blind_check_json = _stored_check(skipped=True)
    db.add(session)
    db.commit()

    # A skip is a stored result: it must unbar the deal exactly as an answer
    # does, or the gate re-fires forever on the next reload.
    view = deal_next_hand(db, session.id)
    assert view.hand.hand_no == BLIND_CHECK_HAND_GATE + 1
    assert view.blind_check is not None and view.blind_check.skipped


def test_repeated_deal_at_the_gate_is_stable(db):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    views = [deal_next_hand(db, session.id) for _ in range(3)]
    assert {v.hand.hand_no for v in views} == {BLIND_CHECK_HAND_GATE}
    assert all(v.hand.board == views[0].hand.board and v.hand.hand_over for v in views)
    db.expire_all()
    assert db.get(SimSession, session.id).hand_no == BLIND_CHECK_HAND_GATE


# --------------------------------------------- what the barred response carries


def test_barred_response_carries_the_gate_hand_recap(db):
    """With Watch off the client adopts the deal response over the fold's, so a
    recap-less barred response would strip hand 200's teaching from the screen."""
    session = _settled_at(db, BLIND_CHECK_HAND_GATE, with_recap=True)
    restored = restore_session(db, session.id)
    assert restored.hand.recap, "the gate hand must have something to recap"

    view = deal_next_hand(db, session.id)
    assert view.hand.recap == restored.hand.recap


def test_gate_with_unreadable_hand_state_deals_on_instead_of_raising(db):
    """A row the gate cannot read must degrade like every other reader of
    `state_json` in the service, not raise where Training still deals."""
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    hand = _current(db, session)
    hand.state_json = None
    db.add(hand)
    db.commit()

    view = deal_next_hand(db, session.id)
    assert view.hand.hand_no == BLIND_CHECK_HAND_GATE + 1


def test_unparseable_stored_check_keeps_the_deal_barred(db):
    """The gate and the wire must read the same thing. `_view()` drops a stored
    value that will not parse, so the gate must treat it as nothing stored —
    otherwise play runs past the gate while the client re-shows its dialog."""
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    session.blind_check_json = '{"seats": [3, 5'  # truncated write
    db.add(session)
    db.commit()

    view = deal_next_hand(db, session.id)
    assert view.hand.hand_no == BLIND_CHECK_HAND_GATE
    # T4 made the barred wire carry the QUESTION rather than nothing: the gate
    # is open and nothing readable is stored, so the client is told which three
    # seats to ask about and the check reads unanswered. Same invariant as
    # before — the gate and the wire agree that nothing is stored — now stated
    # in the shape T4 emits, because a barred deal with no question on the wire
    # would leave the player unable to answer and unable to play on.
    assert view.blind_check is not None
    assert view.blind_check.submitted is False
    assert view.blind_check.skipped is False
    assert view.blind_check.guesses == []
    assert view.blind_check.score is None
