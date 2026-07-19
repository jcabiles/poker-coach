"""N6 — LLM coach seam. Offline-deterministic: no test hits the network.

Covers the TemplateCoach fallback (non-tautological even when reasoning is None —
the reload / optimal-row default), get_coach() provider selection by env key,
explain_decision's fallback-to-template on primary failure, the hero-only prompt
(no villain-card channel), and the /explain endpoint (404 + 200 template).
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine

from app.db.migrate import run_migrations
from app.db.session import get_session
from app.main import app
from app.services import coach as coach_mod
from app.services.coach import (
    AnthropicCoach,
    CoachContext,
    TemplateCoach,
    explain_decision,
    get_coach,
    reset_coach,
)


@pytest.fixture(autouse=True)
def _clean_coach(monkeypatch):
    """Every test starts with no API key + a fresh singleton (a real key in the
    dev environment must not leak template-only tests onto the network)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    reset_coach()
    yield
    reset_coach()


def _ctx(**over) -> CoachContext:
    base = {
        "street": "flop",
        "chosen_action": "fold",
        "correctness": "mistake",
        "sizing_correctness": None,
        "ev_loss_bb": 1.25,
        "coverage": "full",
        "node_context": "vs_cbet",
        "position": "BB",
        "facing_position": "BTN",
        "verdict": "mistake",
        "reasoning": None,
        "hero_cards": ("As", "Kd"),
        "board": ("7h", "8c", "2d"),
    }
    base.update(over)
    return CoachContext(**base)


def _run(coro):
    return asyncio.run(coro)


# --- TemplateCoach: non-tautological from structured fields alone ---


def test_template_non_tautological_reasoning_none():
    text = _run(TemplateCoach().explain(_ctx(reasoning=None)))
    low = text.lower()
    assert "c-bet" in low  # node phrase for vs_cbet
    assert "fold" in low  # the chosen action
    assert "ev" in low or "bb" in low  # the leak framing
    assert len(text) > 60


def test_template_optimal_row_reasoning_none():
    text = _run(
        TemplateCoach().explain(
            _ctx(correctness="optimal", chosen_action="call", reasoning=None)
        )
    )
    low = text.lower()
    assert "standard" in low
    assert "call" in low
    assert "range" in low


def test_template_folds_in_reasoning_when_present():
    note = "The chart flats this hand on wet flops."
    text = _run(TemplateCoach().explain(_ctx(reasoning=note)))
    assert note in text


def test_template_no_baseline_row():
    text = _run(TemplateCoach().explain(_ctx(correctness=None, node_context=None)))
    assert "approximate" in text.lower()


# --- get_coach: provider selection by env key ---


def test_get_coach_template_without_key():
    assert isinstance(get_coach(), TemplateCoach)


def test_get_coach_anthropic_with_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    reset_coach()
    provider = get_coach()
    assert isinstance(provider, AnthropicCoach)
    assert provider.name == "anthropic"


# --- explain_decision: fallback-to-template on primary failure ---


def test_explain_decision_template_source_without_key():
    text, source = _run(explain_decision(_ctx()))
    assert source == "template"
    assert text


def test_explain_decision_falls_back_on_primary_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    reset_coach()

    def _boom(self, ctx):
        raise RuntimeError("network down")

    monkeypatch.setattr(AnthropicCoach, "_call", _boom)
    text, source = _run(explain_decision(_ctx()))
    assert source == "template"
    assert text


# --- privacy: hero-only prompt, no villain channel ---


def test_anthropic_prompt_hero_only():
    prompt = AnthropicCoach("sk-test")._prompt(_ctx())
    assert "As" in prompt and "Kd" in prompt  # hero cards
    assert "7h" in prompt  # board
    # There is no villain-card attribute to leak.
    assert not hasattr(_ctx(), "villain_cards")
    assert not hasattr(_ctx(), "villain_hole_cards")


# --- endpoint: 404 + 200 template ---


@pytest.fixture
def client(tmp_path):
    url = f"sqlite:///{tmp_path / 'coach_api.db'}"
    run_migrations(url)
    engine = create_engine(url, connect_args={"check_same_thread": False})

    def _override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _override
    yield TestClient(app)
    app.dependency_overrides.clear()


def _explain_body(**over):
    body = {
        "street": "flop",
        "chosen_action": "fold",
        "correctness": "mistake",
        "ev_loss_bb": 1.0,
        "coverage": "full",
        "node_context": "vs_cbet",
        "position": "BB",
        "facing_position": "BTN",
        "board": ["7h", "8c", "2d"],
        "hero_cards": ["As", "Kd"],
    }
    body.update(over)
    return body


def test_explain_404_unknown_session(client):
    r = client.post("/api/v1/simulate/nope/explain", json=_explain_body())
    assert r.status_code == 404


def test_explain_200_template(client):
    sid = client.post("/api/v1/simulate/session").json()["session_id"]
    r = client.post(f"/api/v1/simulate/{sid}/explain", json=_explain_body())
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "template"
    assert body["explanation"]
    assert "fold" in body["explanation"].lower()


def test_grade_view_surfaces_spot_dims_for_coach():
    # The N6 coach quality depends on GradeView carrying the persisted spot dims
    # (refuter med): without them the live payload always degrades to generic.
    from app.db.models import SimDecision
    from app.services.sim_session import _grade_view

    row = SimDecision(
        owner_id="",
        session_id="s",
        sim_hand_id=1,
        street="flop",
        ordinal=0,
        chosen_action="fold",
        correctness="mistake",
        ev_loss_bb=1.0,
        coverage="full",
        position="BB",
        facing_position="BTN",
        node_context="vs_cbet",
    )
    gv = _grade_view(row)
    assert gv.node_context == "vs_cbet"
    assert gv.position == "BB"
    assert gv.facing_position == "BTN"


def test_module_singleton_reset(monkeypatch):
    # get_coach caches; reset_coach must let a later key change take effect.
    assert isinstance(get_coach(), TemplateCoach)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    assert isinstance(get_coach(), TemplateCoach)  # still cached
    reset_coach()
    assert isinstance(get_coach(), AnthropicCoach)
    assert coach_mod._coach is not None
