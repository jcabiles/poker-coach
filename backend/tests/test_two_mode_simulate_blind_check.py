"""Two-mode Simulate T4: the blind-check seat pick, scoring, idempotency, route.

Covers spec paragraphs 13-17 and the Wire contract section of
`docs/ai-dlc/specs/two-mode-simulate.md`: three digest-picked seats, scoring
against `SimSeat.persona_type`, first-write-wins storage, and the
`POST /api/v1/simulate/session/{id}/blind-check` error contract.

The gate is reached with T3's helpers (`test_two_mode_simulate_gate`), which
renumber a settled hand rather than playing 200 of them — the gate reads only
`session.hand_no` and the current hand's status, and playing them for real
would cost minutes per test for no extra coverage.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select
from test_two_mode_simulate_gate import _settled_at  # a session at/near the gate

from app.db.migrate import run_migrations
from app.db.models import SimSeat, SimSession
from app.db.session import get_session
from app.domain.archetypes import VillainType
from app.main import app
from app.schemas.simulate import BlindCheckSubmitRequest
from app.services.sim_session import (
    BLIND_CHECK_HAND_GATE,
    HERO_SEAT,
    _blind_check_seats,
    submit_blind_check,
)

# A session id fixed once, with the triple its digest picks written out here.
# Pinning the literal is the point: a test that merely called the function
# twice in one process would pass under Python's salted built-in `hash()`,
# which is the exact defect this guards (spec para 14).
_FIXED_SESSION_ID = "0123456789abcdef0123456789abcdef"
_FIXED_TRIPLE = [3, 5, 7]
_OTHER_SESSION_ID = "two-mode-simulate-t4-fixed-session"
_OTHER_TRIPLE = [3, 5, 6]

_ARCHETYPES = [t.value for t in VillainType]


@pytest.fixture
def temp_engine(tmp_path):
    url = f"sqlite:///{tmp_path / 'two_mode_blind_check.db'}"
    run_migrations(url)
    return create_engine(url, connect_args={"check_same_thread": False})


@pytest.fixture
def db(temp_engine):
    with Session(temp_engine) as s:
        yield s


@pytest.fixture
def client(temp_engine):
    def _override():
        with Session(temp_engine) as s:
            yield s

    app.dependency_overrides[get_session] = _override
    yield TestClient(app)
    app.dependency_overrides.clear()


def _personas(db: Session, session_id: str) -> dict[int, str | None]:
    rows = db.exec(select(SimSeat).where(SimSeat.session_id == session_id)).all()
    return {row.seat_index: row.persona_type for row in rows}


def _wrong_archetype(actual: str) -> str:
    return next(name for name in _ARCHETYPES if name != actual)


def _answers(db: Session, session_id: str, *, wrong: int = 0) -> list[dict]:
    """Answers for the three picked seats, `wrong` of them deliberately wrong."""
    personas = _personas(db, session_id)
    seats = _blind_check_seats(session_id)
    out = []
    for i, seat in enumerate(seats):
        actual = personas[seat]
        guess = _wrong_archetype(actual) if i < wrong else actual
        out.append({"seat_index": seat, "guess": guess})
    return out


def _post(client: TestClient, session_id: str, body: dict):
    return client.post(f"/api/v1/simulate/session/{session_id}/blind-check", json=body)


# ------------------------------------------------------------- the seat pick


def test_seat_pick_is_a_hard_coded_triple_for_a_fixed_session_id():
    assert _blind_check_seats(_FIXED_SESSION_ID) == _FIXED_TRIPLE
    assert _blind_check_seats(_OTHER_SESSION_ID) == _OTHER_TRIPLE


def test_seat_pick_is_identical_in_a_separate_process():
    """Cross-process stability, measured rather than assumed: two fresh
    interpreters under different hash seeds must agree with the pinned triple."""
    backend = Path(__file__).resolve().parents[1]
    code = (
        "from app.services.sim_session import _blind_check_seats;"
        f"print(_blind_check_seats({_FIXED_SESSION_ID!r}))"
    )
    results = set()
    for hash_seed in ("0", "1"):
        env = {**os.environ, "PYTHONPATH": str(backend), "PYTHONHASHSEED": hash_seed}
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=backend,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        results.add(proc.stdout.strip())
    assert results == {str(_FIXED_TRIPLE)}


def test_seat_pick_is_three_distinct_non_hero_seats():
    seen: set[int] = set()
    for _ in range(500):
        seats = _blind_check_seats(uuid.uuid4().hex)
        assert len(seats) == 3
        assert len(set(seats)) == 3, "sampled without replacement"
        assert all(1 <= seat <= 8 for seat in seats)
        assert HERO_SEAT not in seats
        assert seats == sorted(seats)
        seen.update(seats)
    # Every villain seat is reachable — a pick that always named the same three
    # would satisfy every assertion above.
    assert seen == set(range(1, 9))


# ------------------------------------- the question the response asks at the gate


def test_open_gate_offers_the_three_seats_before_any_submission(db, client):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    body = client.get(f"/api/v1/simulate/session/{session.id}").json()

    offer = body["blind_check"]
    assert offer is not None
    assert offer["seats"] == _blind_check_seats(session.id)
    assert offer["submitted"] is False
    assert offer["skipped"] is False
    assert offer["guesses"] == []
    assert offer["score"] is None


def test_open_gate_offer_names_no_archetype(db, client):
    """The offer must not answer its own question: every `BlindCheckGuess`
    carries the seat's ACTUAL archetype, so a populated guess list before
    submission would hand the player the answers.

    Scoped to the `blind_check` object on purpose. `SeatView.persona_type` rides
    the wire in Challenge mode by the spec's constraint (c) — the archetype is
    never nulled anywhere — and hiding it on screen is T7's job, not T4's."""
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    body = client.get(f"/api/v1/simulate/session/{session.id}").json()

    offer_json = json.dumps(body["blind_check"])
    for name in _ARCHETYPES:
        assert name not in offer_json

    # ...and the archetypes the offer withholds are still in the database.
    personas = _personas(db, session.id)
    assert all(personas[seat] in _ARCHETYPES for seat in body["blind_check"]["seats"])


def test_no_offer_before_the_gate(db, client):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE - 1)
    body = client.get(f"/api/v1/simulate/session/{session.id}").json()
    assert body["blind_check"] is None


def test_no_offer_for_a_training_session_at_the_gate(db, client):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE, mode="training")
    body = client.get(f"/api/v1/simulate/session/{session.id}").json()
    assert body["mode"] == "training"
    assert body["blind_check"] is None


# ----------------------------------------------------------------- scoring


def test_all_three_correct_scores_three(db, client):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    personas = _personas(db, session.id)

    resp = _post(client, session.id, {"guesses": _answers(db, session.id)})

    assert resp.status_code == 200
    result = resp.json()
    assert result["submitted"] is True
    assert result["skipped"] is False
    assert result["score"] == 3
    assert result["seats"] == _blind_check_seats(session.id)
    for guess in result["guesses"]:
        assert guess["correct"] is True
        assert guess["actual"] == personas[guess["seat_index"]]
        assert guess["guess"] == guess["actual"]


def test_one_wrong_of_three_scores_two(db, client):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    personas = _personas(db, session.id)

    resp = _post(client, session.id, {"guesses": _answers(db, session.id, wrong=1)})

    assert resp.status_code == 200
    result = resp.json()
    assert result["score"] == 2
    assert [g["correct"] for g in result["guesses"]] == [False, True, True]
    for guess in result["guesses"]:
        assert guess["actual"] == personas[guess["seat_index"]]


def test_all_three_wrong_scores_zero(db, client):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)

    resp = _post(client, session.id, {"guesses": _answers(db, session.id, wrong=3)})

    assert resp.status_code == 200
    result = resp.json()
    assert result["score"] == 0
    assert all(g["correct"] is False for g in result["guesses"])


def test_submission_never_writes_persona_type(db, client):
    """The one constraint in this slice that must not bend: the archetype is
    read and never removed, in the database or on the wire."""
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    before = _personas(db, session.id)

    assert _post(client, session.id, {"guesses": _answers(db, session.id)}).status_code == 200

    db.expire_all()
    assert _personas(db, session.id) == before
    assert all(before[seat] for seat in range(1, 9))


# --------------------------------------------------------- the error contract


def test_submission_before_the_gate_is_409(db, client):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE - 1)
    resp = _post(client, session.id, {"guesses": _answers(db, session.id)})
    assert resp.status_code == 409

    db.expire_all()
    assert db.get(SimSession, session.id).blind_check_json is None


def test_submission_to_a_training_session_at_the_gate_is_409(db, client):
    """Same hand count, Training: its gate never opens, so there is nothing to
    answer and nothing to store."""
    session = _settled_at(db, BLIND_CHECK_HAND_GATE, mode="training")
    resp = _post(client, session.id, {"guesses": _answers(db, session.id)})
    assert resp.status_code == 409


def test_unexpected_seats_are_400(db, client):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    answers = _answers(db, session.id)
    picked = set(_blind_check_seats(session.id))
    answers[0]["seat_index"] = next(s for s in range(1, 9) if s not in picked)

    resp = _post(client, session.id, {"guesses": answers})

    assert resp.status_code == 400
    db.expire_all()
    assert db.get(SimSession, session.id).blind_check_json is None


def test_wrong_number_of_guesses_is_rejected_by_the_schema(db, client):
    """422, not 400: the count is a property of the body, so it is settled
    before the service is reached — like an archetype outside the six."""
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    answers = _answers(db, session.id)
    assert _post(client, session.id, {"guesses": answers[:2]}).status_code == 422
    assert _post(client, session.id, {"guesses": answers + answers[:1]}).status_code == 422
    assert _post(client, session.id, {"guesses": []}).status_code == 422

    db.expire_all()
    assert db.get(SimSession, session.id).blind_check_json is None


def test_skip_carrying_guesses_is_rejected_by_the_schema(db, client):
    """A body cannot mean two things. Left to the service, the skip flag won and
    the answers vanished — including their seat indices, which were never
    checked, so a seat that is not even at the table was accepted."""
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    answers = _answers(db, session.id)

    assert _post(client, session.id, {"skipped": True, "guesses": answers}).status_code == 422
    bogus = [{"seat_index": 99, "guess": "nit"}]
    assert _post(client, session.id, {"skipped": True, "guesses": bogus}).status_code == 422

    # Nothing was stored, so the deal is still barred and the check answerable.
    db.expire_all()
    assert db.get(SimSession, session.id).blind_check_json is None


def test_repeated_seat_in_three_answers_is_400(db, client):
    """The count is right, so the schema passes it; naming the same seat twice
    is a question only the service can answer, and it is still a 400."""
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    answers = _answers(db, session.id)
    answers[1]["seat_index"] = answers[0]["seat_index"]

    assert _post(client, session.id, {"guesses": answers}).status_code == 400


def test_archetype_outside_the_six_is_rejected_by_the_schema(db, client):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    answers = _answers(db, session.id)
    answers[0]["guess"] = "whale"

    # 422, not 400: `BlindCheckAnswer.guess` is the archetype enum, so the value
    # never reaches the service.
    assert _post(client, session.id, {"guesses": answers}).status_code == 422


def test_404_on_missing_session(client):
    resp = _post(client, "nope", {"skipped": True})
    assert resp.status_code == 404
    # The route's own 404, not FastAPI's "Not Found" for an unrouted path.
    assert resp.json()["detail"] == "session not found"


def test_404_on_ended_session(db, client):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    assert client.post(f"/api/v1/simulate/session/{session.id}/leave").status_code == 204

    resp = _post(client, session.id, {"skipped": True})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "session not found"


# ------------------------------------------------------------- idempotency


def test_duplicate_submission_returns_the_first_result(db, client):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)

    first = _post(client, session.id, {"guesses": _answers(db, session.id)}).json()
    assert first["score"] == 3

    second = _post(client, session.id, {"guesses": _answers(db, session.id, wrong=3)})

    assert second.status_code == 200
    assert second.json() == first
    db.expire_all()
    assert json.loads(db.get(SimSession, session.id).blind_check_json) == first


def test_duplicate_skip_does_not_overwrite_an_answered_check(db, client):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    first = _post(client, session.id, {"guesses": _answers(db, session.id)}).json()

    resp = _post(client, session.id, {"skipped": True})

    assert resp.status_code == 200
    assert resp.json() == first
    assert resp.json()["skipped"] is False


def test_two_overlapping_submissions_agree_on_the_first_result(db, temp_engine):
    """First write wins for requests IN FLIGHT AT ONCE, not just sequential ones.

    The interleaving is real, not staged: each request gets its own database
    session, exactly as two HTTP requests do, and both load the session row
    before either writes — which is the whole race window, since the service
    reads "is anything stored?" and writes as two separate steps. Session B
    therefore reaches its write believing nothing is stored, which is precisely
    what a second request would believe. Before the conditional write, B's
    answers replaced A's and the player who submitted first was told a score the
    database no longer held."""
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    session_id = session.id
    right = BlindCheckSubmitRequest.model_validate({"guesses": _answers(db, session_id)})
    wrong = BlindCheckSubmitRequest.model_validate({"guesses": _answers(db, session_id, wrong=3)})

    with Session(temp_engine) as db_a, Session(temp_engine) as db_b:
        # Both requests read the row while it is still empty — the race window.
        # The two locals are load-bearing, not tidiness: SQLAlchemy's identity
        # map holds WEAK references, so letting these go would let B re-read
        # after A's write and the test would reproduce nothing while still
        # passing. A live request holds its row for the length of the call in
        # exactly this way.
        a_row = db_a.get(SimSession, session_id)
        b_row = db_b.get(SimSession, session_id)
        assert a_row.blind_check_json is None
        assert b_row.blind_check_json is None

        first = submit_blind_check(db_a, session_id, right)
        # The reproduction checks itself: B must still believe nothing is
        # stored, or there is no race left to lose.
        assert b_row.blind_check_json is None
        second = submit_blind_check(db_b, session_id, wrong)

    assert first.score == 3
    # The loser is told what the winner stored, not its own unstored score.
    assert second == first
    db.expire_all()
    assert json.loads(db.get(SimSession, session_id).blind_check_json) == first.model_dump()


def test_unparseable_stored_value_is_treated_as_a_first_write(db, client):
    """Ledger B10 carried forward: "already stored" is `_stored_blind_check()`,
    which counts a value that will not parse as nothing stored. Testing the
    column for raw non-emptiness instead would leave a corrupt write barring the
    deal forever — the player could never answer and could never play on."""
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    session.blind_check_json = '{"seats": [3, 5'  # truncated write
    db.add(session)
    db.commit()

    resp = _post(client, session.id, {"guesses": _answers(db, session.id)})

    assert resp.status_code == 200
    assert resp.json()["score"] == 3
    db.expire_all()
    assert json.loads(db.get(SimSession, session.id).blind_check_json)["submitted"] is True


# --------------------------------------------------- what a stored check unbars


def test_answering_unbars_the_deal_and_the_next_response_reports_the_score(db, client):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)
    assert _post(client, session.id, {"guesses": _answers(db, session.id)}).status_code == 200

    dealt = client.post(f"/api/v1/simulate/session/{session.id}/hand")

    assert dealt.status_code == 200
    body = dealt.json()
    assert body["hand"]["hand_no"] == BLIND_CHECK_HAND_GATE + 1
    assert body["blind_check"]["submitted"] is True
    assert body["blind_check"]["score"] == 3


def test_skip_stores_a_result_and_the_deal_resumes(db, client):
    session = _settled_at(db, BLIND_CHECK_HAND_GATE)

    resp = _post(client, session.id, {"skipped": True})

    assert resp.status_code == 200
    result = resp.json()
    assert result["submitted"] is True
    assert result["skipped"] is True
    assert result["guesses"] == []
    assert result["score"] is None
    assert result["seats"] == _blind_check_seats(session.id)

    # A skip that stored nothing would leave the deal barred forever.
    db.expire_all()
    assert db.get(SimSession, session.id).blind_check_json
    dealt = client.post(f"/api/v1/simulate/session/{session.id}/hand")
    assert dealt.json()["hand"]["hand_no"] == BLIND_CHECK_HAND_GATE + 1
