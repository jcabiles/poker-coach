"""Tests for the de-robotization gate runner (poker-coach side).

Scope: the plumbing this repo owns — resolving the analytics checkout, reading
the pins out of the baseline artifact rather than transcribing them, converting
the seat-keyed lineup to the seat-ordered list `run_export` wants, and failing
loudly when the subprocess misbehaves.

The rules themselves live in poker-analytics and are tested there, including
the negative cases that prove each rule can actually fail
(`analysis/tests/test_derobo_gate_check.py`). Those need duckdb and numpy,
which this environment deliberately does not carry.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import derobo_gate as dg

BASELINE_STUB = {
    "artifact_id": "a5baseline-test",
    "min_pairwise_distance": 1.792042,
    "personas": ["calling_station", "lag", "maniac", "nit", "passive_fish", "tag"],
    "stats": ["vpip", "pfr"],
    "source_batch": {
        "engine_git_sha": "a0de83eb134b071d849837835407ddafe537d805",
        "lineup": {"0": "tag", "1": "tag", "2": "calling_station", "3": "tag",
                   "4": "passive_fish", "5": "lag", "6": "passive_fish",
                   "7": "nit", "8": "maniac"},
        "n_hands": 50000,
        "run_id": "run-s601-n50000-c9273b753b9de",
        "seed": 601,
    },
}


def _fake_analytics(root: Path) -> Path:
    """A checkout-shaped directory with the three files the runner requires."""
    (root / ".venv" / "bin").mkdir(parents=True)
    (root / ".venv" / "bin" / "python").write_text("")
    (root / "analysis").mkdir()
    (root / "analysis" / "derobo_gate_check.py").write_text("")
    (root / "scorer" / "artifacts").mkdir(parents=True)
    (root / "scorer" / "artifacts" / "a5_baseline_z.json").write_text(
        json.dumps(BASELINE_STUB))
    return root


# --- locating the analytics checkout ----------------------------------------

def test_analytics_paths_returns_the_three_required_paths(tmp_path):
    root = _fake_analytics(tmp_path / "poker-analytics")
    python, checker, baseline = dg.analytics_paths(root)
    assert python.name == "python"
    assert checker.name == "derobo_gate_check.py"
    assert baseline.name == "a5_baseline_z.json"


@pytest.mark.parametrize("missing", [
    ".venv/bin/python",
    "analysis/derobo_gate_check.py",
    "scorer/artifacts/a5_baseline_z.json",
])
def test_analytics_paths_names_the_missing_file(tmp_path, missing):
    """A missing dependency must be reported here, by name, rather than
    surfacing later as an opaque subprocess failure."""
    root = _fake_analytics(tmp_path / "poker-analytics")
    (root / missing).unlink()
    with pytest.raises(dg.GateError) as exc:
        dg.analytics_paths(root)
    assert str(root / missing) in str(exc.value)
    assert "--analytics-root" in str(exc.value)


# --- pins come from the artifact, never from this file ----------------------

def test_read_pins_takes_seed_hands_and_lineup_from_the_artifact(tmp_path):
    root = _fake_analytics(tmp_path / "poker-analytics")
    pins = dg.read_pins(root / "scorer" / "artifacts" / "a5_baseline_z.json")
    assert pins["seed"] == 601
    assert pins["n_hands"] == 50000
    assert pins["lineup"]["8"] == "maniac"
    assert pins["baseline_engine_sha"].startswith("a0de83e")


def test_read_pins_stringifies_lineup_keys(tmp_path):
    """rule4_determinism builds its SQL CASE on string seat keys and
    pool_counters indexes by string seat, so an int-keyed lineup would
    silently aggregate every persona to nothing."""
    artifact = dict(BASELINE_STUB)
    artifact["source_batch"] = dict(BASELINE_STUB["source_batch"])
    artifact["source_batch"]["lineup"] = {0: "tag", 1: "nit"}
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(artifact))
    pins = dg.read_pins(path)
    assert set(pins["lineup"]) == {"0", "1"}


# --- lineup conversion ------------------------------------------------------

def test_export_candidate_rejects_a_non_contiguous_lineup(tmp_path):
    """`run_export` takes a seat-ORDERED list. A lineup missing a seat would
    otherwise shift every later persona by one, silently measuring the wrong
    bot at every seat."""
    with pytest.raises(dg.GateError) as exc:
        dg.export_candidate(tmp_path, 601, 10, {"0": "tag", "2": "nit"})
    assert "contiguous" in str(exc.value)


def test_export_candidate_orders_seats_numerically(tmp_path, monkeypatch):
    """Seat 10 must not sort before seat 2."""
    captured = {}

    def fake_run_export(**kwargs):
        captured.update(kwargs)
        return {"run_id": "r", "config_hash": "c"}

    monkeypatch.setattr(dg.export_analytics, "run_export", fake_run_export)
    lineup = {str(i): f"p{i}" for i in range(11)}
    dg.export_candidate(tmp_path, 601, 10, lineup)
    assert captured["lineup"] == [f"p{i}" for i in range(11)]
    assert captured["buyin_spread"] is False


def test_export_candidate_pins_buyin_spread_off(tmp_path, monkeypatch):
    """The baseline's run id carries no `-bspread` token, so the baseline was
    built without it and a spread candidate would not be comparable."""
    captured = {}
    monkeypatch.setattr(dg.export_analytics, "run_export",
                        lambda **kw: captured.update(kw) or {"run_id": "r"})
    dg.export_candidate(tmp_path, 601, 10,
                        {str(i): "tag" for i in range(9)})
    assert captured["buyin_spread"] is False


# --- subprocess failure modes ----------------------------------------------

def _stub_proc(monkeypatch, stdout: str, stderr: str = "", code: int = 0):
    class R:
        pass

    r = R()
    r.stdout, r.stderr, r.returncode = stdout, stderr, code
    monkeypatch.setattr(dg.subprocess, "run", lambda *a, **k: r)


def test_run_check_raises_on_empty_output(tmp_path, monkeypatch):
    _stub_proc(monkeypatch, "", "ImportError: No module named duckdb", 1)
    with pytest.raises(dg.GateError) as exc:
        dg.run_check(Path("py"), Path("ck"), Path("bl"), tmp_path, {}, self_test=False)
    assert "no output" in str(exc.value)
    assert "duckdb" in str(exc.value), "stderr must be surfaced to be diagnosable"


def test_run_check_raises_on_non_json_output(tmp_path, monkeypatch):
    _stub_proc(monkeypatch, "Traceback (most recent call last): ...", "", 1)
    with pytest.raises(dg.GateError) as exc:
        dg.run_check(Path("py"), Path("ck"), Path("bl"), tmp_path, {}, self_test=False)
    assert "not JSON" in str(exc.value)


def test_run_check_parses_json_and_passes_self_test_flag(tmp_path, monkeypatch):
    seen = {}

    class R:
        stdout, stderr, returncode = '{"pass": true}', "", 0

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        return R()

    monkeypatch.setattr(dg.subprocess, "run", fake_run)
    out = dg.run_check(Path("py"), Path("ck"), Path("bl"), tmp_path,
                       {"0": "tag"}, self_test=True)
    assert out == {"pass": True}
    assert "--self-test" in seen["cmd"]
    assert json.loads(seen["cmd"][seen["cmd"].index("--lineup") + 1]) == {"0": "tag"}


def test_run_check_omits_self_test_flag_when_judging(tmp_path, monkeypatch):
    seen = {}

    class R:
        stdout, stderr, returncode = '{"pass": false}', "", 1

    monkeypatch.setattr(dg.subprocess, "run",
                        lambda cmd, **kw: (seen.update(cmd=cmd), R())[1])
    dg.run_check(Path("py"), Path("ck"), Path("bl"), tmp_path, {}, self_test=False)
    assert "--self-test" not in seen["cmd"]


# --- the five-seed set is the one the analytics repo already retains --------

def test_seed_set_matches_the_covariance_artifact():
    assert dg.SEED_SET == (601, 602, 603, 604, 605)
