"""P4 — one live session across devices: the state token, the 409 refusals, the
compare-and-set, and `GET /session/current`.

Every test here drives the real HTTP routes against a temp SQLite database, the
way `test_simulate_api.py` does, because the thing under test is the wire
contract two devices share. Spec: docs/ai-dlc/specs/phone-p4-live-session.md
(Verify-by legs (a)-(f)); the corruption these prevent was measured in
docs/ai-dlc/ledger/phone-and-6max.md, "P1 measurement (c)".
"""

from __future__ import annotations

import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select

from app.db.migrate import run_migrations
from app.db.models import SimDecision, SimHand
from app.db.session import get_session
from app.domain.table.engine import HandState
from app.domain.table.grade_map import map_decision_point
from app.main import app
from app.services import sim_session
from app.services.sim_session import HERO_SEAT

BASE = "/api/v1/simulate"


@pytest.fixture
def temp_engine(tmp_path):
    url = f"sqlite:///{tmp_path / 'live_session.db'}"
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


# ------------------------------------------------------------------ helpers


def _act(client: TestClient, session_id: str, payload: dict, token: str):
    return client.post(
        f"{BASE}/session/{session_id}/action", json=payload, params={"state_token": token}
    )


def _deal(client: TestClient, session_id: str, token: str):
    return client.post(f"{BASE}/session/{session_id}/hand", params={"state_token": token})


def _leave(client: TestClient, session_id: str, token: str):
    return client.post(f"{BASE}/session/{session_id}/leave", params={"state_token": token})


def _payload(view: dict) -> dict:
    """A legal, unsized hero action for the view's current spot.

    Unsized on purpose: the probe found that `fold`/`check`/`call` are the
    actions with no self-check at all, since the legal band never rejects them.
    """
    kinds = {la["action"] for la in view["hand"]["legal_actions"]}
    return {"action": "check" if "check" in kinds else "call" if "call" in kinds else "fold"}


def _live_hero_turn_session(client: TestClient) -> dict:
    """A fresh session whose first deal has the hero to act.

    Same shape as `test_simulate_api._create_live_hero_turn_session`: a deal
    that walked to the hero's big blind is retired rather than asserted away.
    """
    for _ in range(50):
        create = client.post(f"{BASE}/session").json()
        if create["hand"]["is_hero_turn"]:
            return create
        _leave(client, create["session_id"], create["state_token"])
    raise AssertionError("no live hero-turn deal in 50 sessions")


def _play_hand_to_completion(client: TestClient, view: dict) -> dict:
    """Drive the hero to the end of the current hand, carrying each response's
    token into the next write the way a real client does."""
    session_id = view["session_id"]
    for _ in range(500):
        if view["hand"]["hand_over"]:
            return view
        resp = _act(client, session_id, _payload(view), view["state_token"])
        assert resp.status_code == 200
        view = resp.json()
    raise AssertionError("hand did not complete within 500 hero actions")


def _hand_row(engine, session_id: str, hand_no: int) -> SimHand:
    with Session(engine) as s:
        return s.exec(
            select(SimHand)
            .where(SimHand.session_id == session_id)
            .where(SimHand.hand_no == hand_no)
        ).one()


def _decisions(engine, sim_hand_id: int) -> list[SimDecision]:
    with Session(engine) as s:
        return list(s.exec(select(SimDecision).where(SimDecision.sim_hand_id == sim_hand_id)).all())


# ---------------------------------------------------- the token itself (1)


def test_the_view_carries_a_token_that_moves_when_the_hero_acts(client, temp_engine):
    create = _live_hero_turn_session(client)
    hand = _hand_row(temp_engine, create["session_id"], 1)
    state = HandState.model_validate_json(hand.state_json)
    assert create["state_token"] == f"1.{len(state.action_history)}"

    acted = _act(client, create["session_id"], _payload(create), create["state_token"])
    assert acted.status_code == 200
    assert acted.json()["state_token"] != create["state_token"]
    # Restoring the same state must produce the same token, or a reload would
    # refuse the player's next action.
    restored = client.get(f"{BASE}/session/{create['session_id']}").json()
    assert restored["state_token"] == acted.json()["state_token"]


# ------------------------------------------- (a) the other client dealt on


def test_stale_action_after_the_other_client_dealt_is_refused(client, temp_engine):
    """Probe situation (ii): the stale call was applied to a hand the player
    never saw and graded as that hand's decision, with HTTP 200."""
    create = _live_hero_turn_session(client)
    session_id = create["session_id"]
    stale_token = create["state_token"]

    settled = _play_hand_to_completion(client, create)
    dealt = _deal(client, session_id, settled["state_token"])
    assert dealt.status_code == 200
    assert dealt.json()["hand"]["hand_no"] == 2

    resp = _act(client, session_id, {"action": "call"}, stale_token)

    assert resp.status_code == 409
    assert resp.json()["detail"] == "stale state"
    assert _decisions(temp_engine, _hand_row(temp_engine, session_id, 2).id) == []


# ------------------------------------------------- (b) a villain re-raised


def _hero_open_then_villain_reraise(client: TestClient) -> tuple[dict, dict]:
    """A preflop pot the hero opened and a villain re-raised, so the hero is to
    act again on the same street.

    Searched rather than constructed: a 3-bet is a real persona frequency, and
    forcing one would mean building a HandState by hand instead of exercising
    the route under test.
    """
    for _ in range(400):
        create = client.post(f"{BASE}/session").json()
        hand = create["hand"]
        opens = next(
            (la for la in hand["legal_actions"] if la["action"] == "raise" and la["min_bb"]),
            None,
        )
        if not hand["is_hero_turn"] or hand["street"] != "preflop" or opens is None:
            _leave(client, create["session_id"], create["state_token"])
            continue
        resp = _act(
            client,
            create["session_id"],
            {"action": "raise", "size_bb": opens["min_bb"]},
            create["state_token"],
        )
        assert resp.status_code == 200
        after = resp.json()
        if (
            after["hand"]["hand_no"] == hand["hand_no"]
            and after["hand"]["street"] == "preflop"
            and after["hand"]["is_hero_turn"]
        ):
            return create, after
        _leave(client, create["session_id"], after["state_token"])
    raise AssertionError("no villain re-raise in 400 opened pots")


def test_stale_action_after_a_villain_reraise_is_refused(client):
    """Probe situation (iii-a): the stale tab's `call` was 1.0bb on screen and
    4.5bb on the server, and it went through with HTTP 200."""
    before, after = _hero_open_then_villain_reraise(client)
    session_id = before["session_id"]
    stack_after_the_reraise = after["hand"]["hero"]["stack_bb"]

    resp = _act(client, session_id, {"action": "call"}, before["state_token"])

    assert resp.status_code == 409
    assert resp.json()["detail"] == "stale state"
    restored = client.get(f"{BASE}/session/{session_id}").json()
    assert restored["hand"]["hero"]["stack_bb"] == stack_after_the_reraise
    assert restored["hand"]["is_hero_turn"] is True


# -------------------------------------------------- (c) two submits at once


def _mappable_live_session(client: TestClient, engine) -> dict:
    """A live hero turn the grader can map to a Spot.

    The concurrency test only reaches the read-modify-write window if the
    awaited provider is actually called, and `apply_hero_action` skips the
    await entirely when the spot mapper returns None.
    """
    for _ in range(50):
        create = _live_hero_turn_session(client)
        hand = _hand_row(engine, create["session_id"], 1)
        state = HandState.model_validate_json(hand.state_json)
        if map_decision_point(state, HERO_SEAT) is not None:
            return create
        _leave(client, create["session_id"], create["state_token"])
    raise AssertionError("no mappable hero decision in 50 sessions")


class _GatedProvider:
    """The real grader, held at the door by a test-controlled event.

    The pause is the point: the provider chain does no I/O today, so two
    requests serialise by accident and a concurrency test without this gate
    would pass even with the compare-and-set removed (the defect the reviewer
    found in the first draft of this leg). Only the START of the grade is held —
    the grading itself is the real thing.
    """

    def __init__(self, real):
        self._real = real
        self._arrivals = 0
        self.both_inside = asyncio.Event()
        self.release = asyncio.Event()

    async def evaluate(self, spot, decision):
        self._arrivals += 1
        if self._arrivals == 2:
            self.both_inside.set()
        await self.release.wait()
        return await self._real.evaluate(spot, decision)


async def _submit_twice_inside_the_window(
    session_id: str, payload: dict, token: str, gated: _GatedProvider
):
    """Two hero submits carrying the same token, as two tasks on ONE event loop,
    both parked inside the read-modify-write window before either writes."""
    url = f"{BASE}/session/{session_id}/action"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        first = asyncio.create_task(ac.post(url, json=payload, params={"state_token": token}))
        second = asyncio.create_task(ac.post(url, json=payload, params={"state_token": token}))
        await asyncio.wait_for(gated.both_inside.wait(), timeout=30)
        gated.release.set()
        return await asyncio.gather(first, second)


def test_two_concurrent_submits_grade_exactly_one_decision(client, temp_engine, monkeypatch):
    """Probe leg 2: two simultaneous submits both returned 200 in 10 of 10 runs,
    leaving two `sim_decision` rows at one ordinal and pots of 2.5-77.5bb from
    one start. The compare-and-set is what turns the second into a 409."""
    create = _mappable_live_session(client, temp_engine)
    session_id = create["session_id"]
    hand_id = _hand_row(temp_engine, session_id, 1).id
    gated = _GatedProvider(sim_session._grading_provider())
    monkeypatch.setattr(sim_session, "_grading_provider", lambda: gated)

    responses = asyncio.run(
        _submit_twice_inside_the_window(session_id, _payload(create), create["state_token"], gated)
    )

    assert sorted(r.status_code for r in responses) == [200, 409]
    stale = next(r for r in responses if r.status_code == 409)
    assert stale.json()["detail"] == "stale state"
    rows = _decisions(temp_engine, hand_id)
    assert [(r.street, r.ordinal) for r in rows] == [(create["hand"]["street"], 0)]


# --------------------------------------------------- (d) GET /session/current


def test_current_session_is_404_when_nothing_is_active(client):
    resp = client.get(f"{BASE}/session/current")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "session not found"


def test_current_session_is_404_after_leaving(client):
    create = _live_hero_turn_session(client)
    assert _leave(client, create["session_id"], create["state_token"]).status_code == 204

    assert client.get(f"{BASE}/session/current").status_code == 404


def test_current_session_is_the_one_played_most_recently(client, temp_engine):
    """An older active session with a hand outranks a newer one with none.

    A session only ends on Leave, so a pre-P4 table whose browser key was lost
    stays `active` forever; ordering by creation would let that orphan hijack
    the table actually being played. This 200 also proves the literal route is
    not shadowed by `/session/{session_id}` — an id lookup for "current" could
    only 404.
    """
    older = _live_hero_turn_session(client)
    newer = client.post(f"{BASE}/session").json()
    with Session(temp_engine) as s:
        for row in s.exec(select(SimHand).where(SimHand.session_id == newer["session_id"])).all():
            s.delete(row)
        s.commit()

    resp = client.get(f"{BASE}/session/current")

    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == older["session_id"]
    assert body["state_token"] == older["state_token"]


# ------------------------------------------------ (e) stale deal, stale leave


def test_stale_deal_and_stale_leave_are_refused(client):
    create = _live_hero_turn_session(client)
    session_id = create["session_id"]
    stale_token = create["state_token"]
    acted = _act(client, session_id, _payload(create), stale_token)
    assert acted.status_code == 200
    fresh_token = acted.json()["state_token"]

    stale_deal = _deal(client, session_id, stale_token)
    stale_leave = _leave(client, session_id, stale_token)

    assert stale_deal.status_code == 409
    assert stale_deal.json()["detail"] == "stale state"
    assert stale_leave.status_code == 409
    assert stale_leave.json()["detail"] == "stale state"
    # The refused Leave left the session for the device that is still playing.
    assert client.get(f"{BASE}/session/{session_id}").status_code == 200
    assert _leave(client, session_id, fresh_token).status_code == 204
    assert client.get(f"{BASE}/session/{session_id}").status_code == 404


# ------------------------------------------------------- (f) the 404s stand


def test_unknown_session_is_404_not_422_when_a_token_is_supplied(client):
    for resp in (
        _act(client, "does-not-exist", {"action": "fold"}, "1.0"),
        _deal(client, "does-not-exist", "1.0"),
    ):
        assert resp.status_code == 404
        assert resp.json()["detail"] == "session not found"


def test_a_missing_token_is_a_422(client):
    create = _live_hero_turn_session(client)
    session_id = create["session_id"]

    assert (
        client.post(f"{BASE}/session/{session_id}/action", json={"action": "fold"}).status_code
        == 422
    )
    assert client.post(f"{BASE}/session/{session_id}/hand").status_code == 422
    assert client.post(f"{BASE}/session/{session_id}/leave").status_code == 422
