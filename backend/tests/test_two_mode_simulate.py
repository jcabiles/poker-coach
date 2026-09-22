"""Two-mode Simulate T2: mode accepted at creation, carried on every response.

Exercises the wire contract (`app/api/v1/simulate.py`) and the read-boundary
normalisation in `sim_session._view()`. Does not touch the 200-hand gate, the
blind-check endpoint, or the frontend — those are T3/T4/T5+.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select

from app.db.migrate import run_migrations
from app.db.models import SimSeat, SimSession
from app.db.session import get_session
from app.main import app


@pytest.fixture
def temp_engine(tmp_path):
    url = f"sqlite:///{tmp_path / 'two_mode_simulate.db'}"
    run_migrations(url)
    return create_engine(url, connect_args={"check_same_thread": False})


@pytest.fixture
def client(temp_engine):
    def _override():
        with Session(temp_engine) as s:
            yield s

    app.dependency_overrides[get_session] = _override
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_session_no_body_defaults_to_training(client: TestClient) -> None:
    resp = client.post("/api/v1/simulate/session")
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "training"
    assert body["blind_check"] is None


def test_create_session_challenge_mode_keeps_persona_type_in_db(
    client: TestClient, temp_engine
) -> None:
    resp = client.post("/api/v1/simulate/session", json={"mode": "challenge"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "challenge"

    # The archetype must never be removed from storage in either mode — the
    # spec's one non-negotiable constraint. Assert against the database, not
    # the response, since the response is not the ticket's concern here.
    session_id = body["session_id"]
    with Session(temp_engine) as s:
        villain_seats = s.exec(
            select(SimSeat).where(
                SimSeat.session_id == session_id,
                SimSeat.is_hero == False,  # noqa: E712
            )
        ).all()
        assert len(villain_seats) == 8
        assert all(row.persona_type for row in villain_seats)


def test_create_session_invalid_mode_rejected(client: TestClient) -> None:
    resp = client.post("/api/v1/simulate/session", json={"mode": "bogus"})
    assert resp.status_code == 422


def test_mode_survives_restore(client: TestClient) -> None:
    create = client.post("/api/v1/simulate/session", json={"mode": "challenge"}).json()
    session_id = create["session_id"]

    restored = client.get(f"/api/v1/simulate/session/{session_id}").json()
    assert restored["mode"] == "challenge"


def test_null_mode_normalises_to_training(client: TestClient, temp_engine) -> None:
    create = client.post("/api/v1/simulate/session").json()
    session_id = create["session_id"]

    # Simulate a hand-rolled row (or a future write path) that never set mode.
    with Session(temp_engine) as s:
        row = s.get(SimSession, session_id)
        row.mode = None
        s.add(row)
        s.commit()

    restored = client.get(f"/api/v1/simulate/session/{session_id}")
    assert restored.status_code == 200
    assert restored.json()["mode"] == "training"


def test_unrecognised_stored_mode_normalises_to_training_on_restore_and_deal(
    client: TestClient, temp_engine
) -> None:
    """An unrecognised (non-empty) stored mode is the same hand-rolled-write
    hazard as a null one — Finding 1 of the T2 review. Must not 500 on any
    route that flows through `_view()`."""
    create = client.post("/api/v1/simulate/session").json()
    session_id = create["session_id"]

    with Session(temp_engine) as s:
        row = s.get(SimSession, session_id)
        row.mode = "bogus"
        s.add(row)
        s.commit()

    restored = client.get(f"/api/v1/simulate/session/{session_id}")
    assert restored.status_code == 200
    assert restored.json()["mode"] == "training"

    dealt = client.post(
        f"/api/v1/simulate/session/{session_id}/hand",
        params={"state_token": restored.json()["state_token"]},
    )
    assert dealt.status_code == 200
    assert dealt.json()["mode"] == "training"


def test_malformed_blind_check_json_does_not_brick_the_session(
    client: TestClient, temp_engine
) -> None:
    """A corrupt or older-shape `blind_check_json` must not take the whole
    session offline — Finding 2 of the T2 review. `blind_check` degrades to
    null; the rest of the session (mode, hand) stays intact, on more than one
    route."""
    create = client.post("/api/v1/simulate/session").json()
    session_id = create["session_id"]

    with Session(temp_engine) as s:
        row = s.get(SimSession, session_id)
        row.blind_check_json = "{not valid json"
        s.add(row)
        s.commit()

    restored = client.get(f"/api/v1/simulate/session/{session_id}")
    assert restored.status_code == 200
    restored_body = restored.json()
    assert restored_body["blind_check"] is None
    assert restored_body["mode"] == "training"
    assert restored_body["session_id"] == session_id

    dealt = client.post(
        f"/api/v1/simulate/session/{session_id}/hand",
        params={"state_token": restored_body["state_token"]},
    )
    assert dealt.status_code == 200
    assert dealt.json()["blind_check"] is None
