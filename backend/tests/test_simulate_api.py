"""API tests for the S9 simulate endpoints.

Exercises the wire contract, not the service internals (those are
`test_sim_session.py`, owned by T1). Depends on T1's DB-backed
`app.services.sim_session` + `app.db.models.SimSession/SimSeat/SimHand` +
migration `0009_sim_tables` — if those aren't committed yet, these tests will
fail at collection/import time (expected mid-wave; see the wave-4 ticket).
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine

from app.db.migrate import run_migrations
from app.db.session import get_session
from app.domain.spot import ActionType, validate_card
from app.main import app
from app.services.sim_session import _BUYIN_MAX_BB, _BUYIN_MIN_BB


@pytest.fixture
def temp_engine(tmp_path):
    url = f"sqlite:///{tmp_path / 'simulate_api.db'}"
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


def _assert_no_leaked_hole_cards(body: dict) -> None:
    """No non-hero, non-showdown hole cards; no state_json/full_board, ever."""
    hand = body["hand"]
    assert "state_json" not in hand
    assert "full_board" not in hand
    hero_cards = set(hand["hero"]["hole_cards"])

    showdown_cards: set[str] = set()
    for sd in hand["showdown"]:
        showdown_cards.update(sd["hole_cards"])

    def _walk(obj):
        if isinstance(obj, dict):
            assert "state_json" not in obj
            assert "full_board" not in obj
            if "hole_cards" in obj and obj is not hand["hero"] and obj not in hand["showdown"]:
                raise AssertionError(f"unexpected hole_cards field: {obj}")
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(body)

    # seats never carry a hole_cards field at all (SeatView has none).
    for seat in hand["seats"]:
        assert "hole_cards" not in seat

    for c in hero_cards:
        validate_card(c)
    for c in showdown_cards:
        validate_card(c)


def _create_live_hero_turn_session(client: TestClient) -> dict:
    """Create sessions until one deals a hand where it is genuinely hero's turn.

    PRE-EXISTING flake, fixed opportunistically — NOT a regression from the
    T-STACK buy-in spread. A bare `assert hand["is_hero_turn"]` on the first
    deal has been in this file since #31: ~0.15% of fresh deals fold around to
    the hero's big blind, so the hand arrives already `hand_over` with no hero
    turn at all, and the suite fails about 1 run in 700. Measured over 10,000
    fresh sessions: 14/10,000 with the ±5bb spread vs 16/10,000 with a fixed
    100bb stack — same rate, the spread is not involved.

    Tests that need a live hero decision call this instead of asserting the
    first deal cooperates.
    """
    for _ in range(50):
        create = client.post("/api/v1/simulate/session").json()
        if create["hand"]["is_hero_turn"]:
            return create
        # Dead end (walk to the hero's BB): retire it and deal a new one.
        client.post(f"/api/v1/simulate/session/{create['session_id']}/leave")
    raise AssertionError("no live hero-turn deal in 50 sessions")


def _play_hand_to_completion(client: TestClient, session_id: str) -> dict:
    """Drive hero actions (fold when it's hero's turn) until hand_over."""
    body = client.get(f"/api/v1/simulate/session/{session_id}").json()
    for _ in range(500):
        hand = body["hand"]
        _assert_no_leaked_hole_cards(body)
        if hand["hand_over"]:
            return body
        # Not a flake site: persisted state is always at a hero decision
        # boundary or hand-over, and the hand-over case returned above.
        # Measured 0/10,000 fresh deals with (is_hero_turn=False,
        # hand_over=False) — this is the service invariant, keep it bare.
        assert hand["is_hero_turn"]
        # Prefer check/fold to end the hand quickly.
        kinds = {la["action"] for la in hand["legal_actions"]}
        action = "check" if "check" in kinds else "fold"
        resp = client.post(
            f"/api/v1/simulate/session/{session_id}/action",
            json={"action": action},
        )
        assert resp.status_code == 200
        body = resp.json()
    raise AssertionError("hand did not complete within 500 hero actions")


def test_create_returns_valid_session(client):
    resp = client.post("/api/v1/simulate/session")
    assert resp.status_code == 200
    body = resp.json()
    assert "session_id" in body
    hand = body["hand"]
    assert hand["hand_no"] == 1
    assert len(hand["seats"]) == 9
    hero_seats = [s for s in hand["seats"] if s["is_hero"]]
    assert len(hero_seats) == 1
    assert hero_seats[0]["persona_type"] is None
    assert len(hand["hero"]["hole_cards"]) == 2
    _assert_no_leaked_hole_cards(body)


def test_create_act_showdown_happy_path(client):
    create = client.post("/api/v1/simulate/session").json()
    session_id = create["session_id"]
    final = _play_hand_to_completion(client, session_id)
    assert final["hand"]["hand_over"] is True
    _assert_no_leaked_hole_cards(final)


def test_restore_returns_live_decision_point(client):
    create = client.post("/api/v1/simulate/session").json()
    session_id = create["session_id"]

    restored = client.get(f"/api/v1/simulate/session/{session_id}")
    assert restored.status_code == 200
    body = restored.json()
    assert body["session_id"] == session_id
    assert body["hand"]["hand_no"] == create["hand"]["hand_no"]
    assert body["hand"]["to_act_seat"] == create["hand"]["to_act_seat"]
    assert body["hand"]["is_hero_turn"] == create["hand"]["is_hero_turn"]
    _assert_no_leaked_hole_cards(body)


def test_404_on_missing_session(client):
    resp = client.get("/api/v1/simulate/session/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "session not found"


def test_404_on_ended_session(client):
    create = client.post("/api/v1/simulate/session").json()
    session_id = create["session_id"]

    leave_resp = client.post(f"/api/v1/simulate/session/{session_id}/leave")
    assert leave_resp.status_code == 204

    resp = client.get(f"/api/v1/simulate/session/{session_id}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "session not found"


def test_404_on_missing_session_for_action(client):
    resp = client.post(
        "/api/v1/simulate/session/does-not-exist/action",
        json={"action": "fold"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "session not found"


def test_404_on_missing_session_for_hand(client):
    resp = client.post("/api/v1/simulate/session/does-not-exist/hand")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "session not found"


def test_illegal_hero_action_returns_400(client):
    # Guard on liveness rather than asserting the first deal is a hero turn —
    # see _create_live_hero_turn_session. The subject of the test is unchanged:
    # an out-of-range raise must return 400.
    create = _create_live_hero_turn_session(client)
    session_id = create["session_id"]
    hand = create["hand"]
    legal_kinds = {la["action"] for la in hand["legal_actions"]}
    # RAISE is never legal preflop for the first-to-act hero without a size,
    # and if it happens to be legal, an absurd out-of-range size is illegal.
    if ActionType.RAISE.value in legal_kinds:
        payload = {"action": "raise", "size_bb": 100000.0}
    else:
        payload = {"action": "raise", "size_bb": 4.0}

    resp = client.post(
        f"/api/v1/simulate/session/{session_id}/action",
        json=payload,
    )
    assert resp.status_code == 400


def test_next_hand_rebuys_inside_the_band_and_advances_button(client):
    create = client.post("/api/v1/simulate/session").json()
    session_id = create["session_id"]
    btn1 = create["hand"]["button_seat"]

    _play_hand_to_completion(client, session_id)

    resp = client.post(f"/api/v1/simulate/session/{session_id}/hand")
    assert resp.status_code == 200
    body = resp.json()
    hand2 = body["hand"]
    assert hand2["hand_no"] == 2
    assert hand2["button_seat"] == (btn1 + 1) % 9
    # T-STACK: every seat re-buys inside the band before each deal — nothing
    # carries over. Guard on LIVENESS, not street: a hand that walked to the
    # big blind comes back already `hand_over`, and its seat stacks are then
    # post-settlement, not starting stacks. Deal on until a live hand (in one,
    # the hero always has a preflop decision).
    guard = 0
    while hand2["hand_over"]:
        guard += 1
        assert guard < 20, "20 consecutive walk-outs is not a real table"
        body = client.post(f"/api/v1/simulate/session/{session_id}/hand").json()
        hand2 = body["hand"]
    assert hand2["street"] == "preflop"
    # Mid-hand the view reports chips behind, so the seat's STARTING stack is
    # stack + what it has put in; preflop is one street, so invested_street_bb
    # is its whole commitment.
    for seat in hand2["seats"]:
        starting = round(seat["stack_bb"] + seat["invested_street_bb"], 2)
        assert _BUYIN_MIN_BB <= starting <= _BUYIN_MAX_BB
    # The re-buy is chips entering/leaving play, never P&L: the table's net
    # still sums to zero. (net_bb carrying real P&L across hands is covered
    # over 20 hands in test_sim_session_buyin_cap.py.)
    assert round(sum(seat["net_bb"] for seat in hand2["seats"]), 2) == 0.0
    _assert_no_leaked_hole_cards(body)


# ------------------------------- History villain reveal (T3): wire contract


def _completed_hand_id(client: TestClient) -> int:
    """Play one hand to completion and return its sim_hand_id from history."""
    create = _create_live_hero_turn_session(client)
    _play_hand_to_completion(client, create["session_id"])
    items = client.get("/api/v1/simulate/history").json()["items"]
    assert items, "a completed hand should be filed in history"
    return items[0]["sim_hand_id"]


def test_hand_reveal_returns_cards_and_deltas(client):
    hand_id = _completed_hand_id(client)
    for scope in ("last-in", "all"):
        resp = client.get(f"/api/v1/simulate/hand/{hand_id}/reveal/{scope}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["available"] is True
        assert body["scope"] == scope
        for seat in body["seats"]:
            assert seat["seat_index"] != 0  # hero never revealed
            assert len(seat["hole_cards"]) == 2
            for c in seat["hole_cards"]:
                validate_card(c)
            assert isinstance(seat["delta_bb"], (int, float))
    # 'all' is a superset of 'last-in' — every non-hero seat was dealt in.
    last_in = client.get(f"/api/v1/simulate/hand/{hand_id}/reveal/last-in").json()
    all_seats = client.get(f"/api/v1/simulate/hand/{hand_id}/reveal/all").json()
    assert {s["seat_index"] for s in last_in["seats"]} <= {
        s["seat_index"] for s in all_seats["seats"]
    }
    assert {s["seat_index"] for s in all_seats["seats"]} == set(range(1, 9))


def test_hand_reveal_unknown_scope_is_200_body_not_404(client):
    hand_id = _completed_hand_id(client)
    resp = client.get(f"/api/v1/simulate/hand/{hand_id}/reveal/sideways")
    assert resp.status_code == 200
    assert resp.json()["available"] is False
    assert resp.json()["seats"] == []


def test_hand_reveal_404_on_unknown_hand(client):
    resp = client.get("/api/v1/simulate/hand/999999/reveal/all")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "hand not found"


def test_hand_reveal_route_does_not_shadow_session_reveal(client):
    """The two reveal routes differ in segment count and must both resolve.

    /simulate/hand/{id}/reveal/{scope}   -> 4 segments (this feature)
    /simulate/{session_id}/reveal/{scope} -> 3 segments (live R1, pre-existing)
    """
    create = _create_live_hero_turn_session(client)
    session_id = create["session_id"]
    _play_hand_to_completion(client, session_id)

    session_scoped = client.get(f"/api/v1/simulate/{session_id}/reveal/all")
    assert session_scoped.status_code == 200
    assert session_scoped.json()["available"] is True
    # Session-scoped payload keeps its original shape: cards only, no delta_bb.
    for seat in session_scoped.json()["seats"]:
        assert "delta_bb" not in seat

    hand_id = client.get("/api/v1/simulate/history").json()["items"][0]["sim_hand_id"]
    hand_scoped = client.get(f"/api/v1/simulate/hand/{hand_id}/reveal/all")
    assert hand_scoped.status_code == 200
    # Hand-scoped payload carries the delta the History felt needs.
    for seat in hand_scoped.json()["seats"]:
        assert "delta_bb" in seat


def test_replay_endpoint_still_hides_villains_after_reveal_exists(client):
    """The reveal endpoint is additive — /replay must not have widened."""
    hand_id = _completed_hand_id(client)
    steps = client.get(f"/api/v1/simulate/hand/{hand_id}/replay").json()["steps"]
    assert steps
    for step in steps:
        if not step["is_terminal"]:
            assert step["revealed_seats"] == []
