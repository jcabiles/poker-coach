"""T5 (flywheel S6): the blind-detection judging harness.

Everything here runs against a small SYNTHETIC presentation manifest (8
bundles + 2 duplicates, one per slot) built in-test — the real 40+40 deck is
T4/T7's concern, not this module's. The properties that carry the pilot:

1. **The harness never sees an answer key.** `presentation.json` never has a
   class/label/source key; a document that does is refused before any judging
   call.
2. **Determinism.** Launch is immutable once written; per-slot order is a
   pinned seeded permutation; a duplicate is routed to exactly its own slot.
3. **Strict, no-coercion response parsing** — the §d.3 schema is exact.
4. **Resume is idempotent and byte-stable**, and never touches the order or
   the duplicate routing that launch/order already pinned.

`urllib.request.urlopen` is monkeypatched at the function boundary for the
transport-failure test — no real network anywhere in this file.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools import detection_judge as dj

# ---------------------------------------------------------------------------
# Fixture: a small synthetic presentation manifest
# ---------------------------------------------------------------------------

N_JUDGES = 2


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _bundle(
    pid: str, seat: str, extra_hands: str = "", duplicate_for_slot: int | None = None,
) -> dict:
    text = (
        f"Player under review: {seat}\n"
        "9-handed No-Limit Hold'em. Blinds 0.50 / 1.00. All amounts in big blinds.\n"
        f"Hands: 1, consecutive, in order of play.\n\nhand body {pid} {extra_hands}\n"
    )
    entry = {"presentation_id": pid, "rendered_text": text, "sha256": _sha(text)}
    if duplicate_for_slot is not None:
        entry["duplicate_for_slot"] = duplicate_for_slot
    return entry


def make_presentation_document() -> dict:
    bundles = [_bundle(f"B{i:03d}", f"P{i % 9}") for i in range(1, 9)]
    bundles.append(_bundle("B901", "P3", duplicate_for_slot=0))
    bundles.append(_bundle("B902", "P5", duplicate_for_slot=1))
    return {
        "schema_version": "1.0.0",
        "bundle_count": len(bundles),
        "judge_slots": N_JUDGES,
        "bundles": bundles,
    }


@pytest.fixture
def deck_dir(tmp_path: Path) -> Path:
    doc = make_presentation_document()
    d = tmp_path / "deck"
    d.mkdir()
    (d / "presentation.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return d


STUB_JUDGES_ARG = "stub:model-a,stub:model-b"


# ---------------------------------------------------------------------------
# Unblinding-refusal guard
# ---------------------------------------------------------------------------


class TestUnblindingGuard:
    def test_clean_document_passes(self) -> None:
        dj.assert_no_label_bearing_keys(make_presentation_document())

    @pytest.mark.parametrize(
        "poison_key", ["class", "label", "is_control", "source_window", "true_class"]
    )
    def test_label_bearing_key_rejected(self, poison_key: str) -> None:
        doc = make_presentation_document()
        doc["bundles"][0][poison_key] = "human"
        with pytest.raises(dj.HarnessError, match="label-bearing"):
            dj.assert_no_label_bearing_keys(doc)

    def test_nested_label_key_rejected(self) -> None:
        doc = make_presentation_document()
        doc["bundles"][0]["meta"] = {"is_control": False}
        with pytest.raises(dj.HarnessError, match="label-bearing"):
            dj.assert_no_label_bearing_keys(doc)

    def test_load_presentation_refuses_poisoned_file(self, tmp_path: Path) -> None:
        doc = make_presentation_document()
        doc["bundles"][0]["class"] = "bot"
        d = tmp_path / "deck"
        d.mkdir()
        (d / "presentation.json").write_text(json.dumps(doc), encoding="utf-8")
        with pytest.raises(dj.HarnessError, match="label-bearing"):
            dj.load_presentation(d)

    def test_cli_has_no_unblinding_path_argument(self) -> None:
        parser = dj.build_arg_parser()
        run = next(a for a in parser._subparsers._group_actions[0].choices.values())
        dests = {action.dest for action in run._actions}
        assert not any("unblind" in dest for dest in dests)


# ---------------------------------------------------------------------------
# Prompt verbatim check (estimand-contract.md §d.3 lines 505-513 + §A.2)
# ---------------------------------------------------------------------------

_PINNED_PROMPT_TEMPLATE = (
    "You are an experienced live low-stakes no-limit hold'em cash-game player "
    "reviewing anonymized hand histories. You will see 30 consecutive hands "
    "played by seat {SEAT_ID}. Decide whether this seat was played by a HUMAN "
    "or a BOT. Consider tendencies a human would notice: bet-sizing patterns, "
    "timing-free logic of calls and raises, consistency vs adaptability, "
    "strange folds or calls, repetitive lines. Respond in exactly this JSON "
    'format: {"label": "human"|"bot", "confidence_human": <integer 0-100>, '
    '"reason": "<≤50 words>"}.'
)

_PINNED_PREAMBLE = (
    "The set of seats you will review contains humans and bots in equal "
    "proportion: the true base rate is 50/50."
)


def test_prompt_and_preamble_are_pinned_verbatim() -> None:
    assert dj.JUDGE_PROMPT_TEMPLATE == _PINNED_PROMPT_TEMPLATE
    assert dj.BASE_RATE_PREAMBLE == _PINNED_PREAMBLE
    assert dj.JUDGE_PROMPT_TEMPLATE.replace("{SEAT_ID}", "P3").startswith(
        "You are an experienced live low-stakes no-limit hold'em cash-game player "
        "reviewing anonymized hand histories. You will see 30 consecutive hands "
        "played by seat P3."
    )


def test_extract_seat_id_reads_the_renderer_header() -> None:
    text = "Player under review: P7\nrest of bundle\n"
    assert dj.extract_seat_id(text) == "P7"


def test_extract_seat_id_rejects_missing_header() -> None:
    with pytest.raises(dj.HarnessError):
        dj.extract_seat_id("no header here\n")


# ---------------------------------------------------------------------------
# Strict response parsing — the no-coercion matrix
# ---------------------------------------------------------------------------


class TestParseJudgeResponse:
    def test_valid(self) -> None:
        raw = '{"label": "human", "confidence_human": 73, "reason": "steady sizing"}'
        assert dj.parse_judge_response(raw) == {
            "label": "human", "confidence_human": 73, "reason": "steady sizing",
        }

    def test_valid_fenced(self) -> None:
        raw = '```json\n{"label": "bot", "confidence_human": 12, "reason": "robotic lines"}\n```'
        parsed = dj.parse_judge_response(raw)
        assert parsed["label"] == "bot" and parsed["confidence_human"] == 12

    def test_valid_bare_fence(self) -> None:
        raw = '```\n{"label": "bot", "confidence_human": 5, "reason": "x"}\n```'
        assert dj.parse_judge_response(raw)["label"] == "bot"

    def test_extra_keys_rejected(self) -> None:
        raw = '{"label": "human", "confidence_human": 50, "reason": "x", "extra": 1}'
        with pytest.raises(dj.ResponseParseError):
            dj.parse_judge_response(raw)

    def test_missing_key_rejected(self) -> None:
        raw = '{"label": "human", "confidence_human": 50}'
        with pytest.raises(dj.ResponseParseError):
            dj.parse_judge_response(raw)

    def test_float_confidence_rejected(self) -> None:
        raw = '{"label": "human", "confidence_human": 50.5, "reason": "x"}'
        with pytest.raises(dj.ResponseParseError):
            dj.parse_judge_response(raw)

    def test_bool_confidence_rejected(self) -> None:
        raw = '{"label": "human", "confidence_human": true, "reason": "x"}'
        with pytest.raises(dj.ResponseParseError):
            dj.parse_judge_response(raw)

    def test_out_of_range_confidence_rejected(self) -> None:
        raw = '{"label": "human", "confidence_human": 101, "reason": "x"}'
        with pytest.raises(dj.ResponseParseError):
            dj.parse_judge_response(raw)

    def test_negative_confidence_rejected(self) -> None:
        raw = '{"label": "human", "confidence_human": -1, "reason": "x"}'
        with pytest.raises(dj.ResponseParseError):
            dj.parse_judge_response(raw)

    def test_bad_label_rejected(self) -> None:
        raw = '{"label": "maybe", "confidence_human": 50, "reason": "x"}'
        with pytest.raises(dj.ResponseParseError):
            dj.parse_judge_response(raw)

    def test_not_json_rejected(self) -> None:
        with pytest.raises(dj.ResponseParseError):
            dj.parse_judge_response("I think this is a human, 70% confident.")

    def test_not_an_object_rejected(self) -> None:
        with pytest.raises(dj.ResponseParseError):
            dj.parse_judge_response('["human", 70]')


# ---------------------------------------------------------------------------
# judge_pair: retry-then-missing, transport-failure path
# ---------------------------------------------------------------------------


SAMPLE_RENDERED_TEXT = (
    "Player under review: P1\n"
    "9-handed No-Limit Hold'em. Blinds 0.50 / 1.00. All amounts in big blinds.\n"
    "Hands: 1, consecutive, in order of play.\n\nhand body B001\n"
)


class _FakeAdapter:
    """A scripted adapter: a queue of (raise-or-text) results per `.call`.

    Records every `.call` invocation's (system_prompt, user_prompt) so tests
    can assert on the exact wire content, not just the outcome.
    """

    def __init__(self, script: list) -> None:
        self.script = list(script)
        self.calls = 0
        self.seen_calls: list[tuple[str, str]] = []

    def call(self, model, system_prompt, user_prompt, api_key, base_url, timeout, *, context=None):
        self.calls += 1
        self.seen_calls.append((system_prompt, user_prompt))
        outcome = self.script.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome, model


class TestJudgePair:
    def test_ok_first_try(self) -> None:
        adapter = _FakeAdapter(['{"label": "human", "confidence_human": 80, "reason": "x"}'])
        result = dj.judge_pair(
            adapter, "m", "key", None, "P1", SAMPLE_RENDERED_TEXT, "B001", 0,
            sleep=lambda s: None,
        )
        assert result["status"] == "ok"
        assert result["parsed"]["label"] == "human"
        assert result["raw_responses"] == [
            '{"label": "human", "confidence_human": 80, "reason": "x"}'
        ]

    def test_malformed_then_identical_retry_recovers(self) -> None:
        adapter = _FakeAdapter(
            ["not json", '{"label": "bot", "confidence_human": 5, "reason": "x"}']
        )
        result = dj.judge_pair(
            adapter, "m", "key", None, "P1", SAMPLE_RENDERED_TEXT, "B001", 0,
            sleep=lambda s: None,
        )
        assert result["status"] == "ok"
        assert adapter.calls == 2
        # "IDENTICAL prompt" retry: the second call's user prompt is byte-equal
        # to the first — the rendered hand text does not drift on retry.
        assert adapter.seen_calls[0][1] == adapter.seen_calls[1][1]

    def test_malformed_twice_becomes_recorded_missing(self) -> None:
        adapter = _FakeAdapter(["not json", "still not json"])
        result = dj.judge_pair(
            adapter, "m", "key", None, "P1", SAMPLE_RENDERED_TEXT, "B001", 0,
            sleep=lambda s: None,
        )
        assert result["status"] == "malformed-final"
        assert result["parsed"] is None
        assert len(result["raw_responses"]) == 2
        assert adapter.calls == 2

    def test_transport_failure_retried_then_recorded_distinctly(self) -> None:
        timeout_error = dj.TransportError("timeout")
        adapter = _FakeAdapter([timeout_error, timeout_error, timeout_error])
        sleeps: list[float] = []
        result = dj.judge_pair(
            adapter, "m", "key", None, "P1", SAMPLE_RENDERED_TEXT, "B001", 0,
            sleep=sleeps.append,
        )
        assert result["status"] == "transport_failed"
        assert adapter.calls == 3
        assert len(sleeps) == 2  # backoff between attempts 1->2, 2->3; none after the last

    def test_transport_recovers_within_budget(self) -> None:
        ok_text = '{"label": "human", "confidence_human": 60, "reason": "x"}'
        adapter = _FakeAdapter([dj.TransportError("blip"), ok_text])
        result = dj.judge_pair(
            adapter, "m", "key", None, "P1", SAMPLE_RENDERED_TEXT, "B001", 0,
            sleep=lambda s: None,
        )
        assert result["status"] == "ok"

    def test_wire_user_prompt_contains_template_delimiter_and_hand_text(self) -> None:
        """The refuter-found HIGH: the user prompt must carry the actual hand
        history, not just the pinned instructions."""
        adapter = _FakeAdapter(['{"label": "human", "confidence_human": 80, "reason": "x"}'])
        dj.judge_pair(
            adapter, "m", "key", None, "P1", SAMPLE_RENDERED_TEXT, "B001", 0,
            sleep=lambda s: None,
        )
        assert adapter.calls == 1
        system_prompt, user_prompt = adapter.seen_calls[0]
        assert dj.JUDGE_PROMPT_TEMPLATE.replace("{SEAT_ID}", "P1") in user_prompt
        assert dj.HAND_HISTORY_DELIMITER in user_prompt
        assert SAMPLE_RENDERED_TEXT in user_prompt
        # The rendered text must come AFTER the instructions, via the delimiter.
        assert user_prompt == (
            dj.JUDGE_PROMPT_TEMPLATE.replace("{SEAT_ID}", "P1")
            + dj.HAND_HISTORY_DELIMITER
            + SAMPLE_RENDERED_TEXT
        )
        # §A.2 base-rate preamble stays a SYSTEM message — never in the user prompt.
        assert dj.BASE_RATE_PREAMBLE not in user_prompt
        assert system_prompt == dj.BASE_RATE_PREAMBLE

    def test_build_user_prompt_matches_judge_pair_wire_content(self) -> None:
        assert dj.build_user_prompt("P1", SAMPLE_RENDERED_TEXT) == (
            dj.JUDGE_PROMPT_TEMPLATE.replace("{SEAT_ID}", "P1")
            + dj.HAND_HISTORY_DELIMITER
            + SAMPLE_RENDERED_TEXT
        )


# ---------------------------------------------------------------------------
# stub vendor determinism
# ---------------------------------------------------------------------------


def _stub_ctx(presentation_id: str, slot: int) -> dict:
    return {"presentation_id": presentation_id, "slot": slot}


def test_stub_vendor_is_deterministic_and_valid() -> None:
    ctx = _stub_ctx("B001", 0)
    raw1, resolved1 = dj.call_stub("m", "sys", "user", "key", None, 1.0, context=ctx)
    raw2, resolved2 = dj.call_stub("m", "sys", "user", "key", None, 1.0, context=ctx)
    assert raw1 == raw2 and resolved1 == resolved2
    parsed = dj.parse_judge_response(raw1)
    assert parsed["label"] in ("human", "bot")


def test_stub_vendor_varies_by_presentation_and_slot() -> None:
    raw_a, _ = dj.call_stub("m", "sys", "user", "key", None, 1.0, context=_stub_ctx("B001", 0))
    raw_b, _ = dj.call_stub("m", "sys", "user", "key", None, 1.0, context=_stub_ctx("B002", 0))
    raw_c, _ = dj.call_stub("m", "sys", "user", "key", None, 1.0, context=_stub_ctx("B001", 1))
    assert len({raw_a, raw_b, raw_c}) == 3


# ---------------------------------------------------------------------------
# End-to-end: launch immutability, order determinism + duplicate routing,
# atomic resume, byte-stable outputs
# ---------------------------------------------------------------------------


class TestEndToEnd:
    def test_run_sends_actual_rendered_text_to_vendor(
        self, deck_dir: Path, tmp_path: Path, monkeypatch,
    ) -> None:
        """End-to-end re-check of the refuter-found HIGH: `run()` must pass
        each bundle's real `rendered_text` all the way to the vendor call,
        not just the pinned instructions."""
        captured: list[tuple[str, str]] = []
        real_call_stub = dj.call_stub

        def _recording_call_stub(
            model, system_prompt, user_prompt, api_key, base_url, timeout, *, context=None,
        ):
            captured.append((system_prompt, user_prompt))
            return real_call_stub(
                model, system_prompt, user_prompt, api_key, base_url, timeout, context=context,
            )

        monkeypatch.setitem(
            dj.VENDOR_ADAPTERS, "stub",
            dj.VendorAdapter("stub", None, _recording_call_stub),
        )

        out = tmp_path / "out"
        dj.run(
            deck_dir, STUB_JUDGES_ARG, order_seed=17, out_dir=out, env={},
            only_slot=0, only_presentation_id="B002",
        )

        doc = make_presentation_document()
        expected_text = next(
            b["rendered_text"] for b in doc["bundles"] if b["presentation_id"] == "B002"
        )
        # `captured` also holds the two preflight calls (one per configured
        # judge, regardless of --only-slot); isolate the actual judging call
        # by its delimiter, which preflight's off-protocol prompt never has.
        judging_calls = [c for c in captured if dj.HAND_HISTORY_DELIMITER in c[1]]
        assert len(judging_calls) == 1
        system_prompt, user_prompt = judging_calls[0]
        assert expected_text in user_prompt
        assert dj.HAND_HISTORY_DELIMITER in user_prompt
        assert system_prompt == dj.BASE_RATE_PREAMBLE
        assert dj.BASE_RATE_PREAMBLE not in user_prompt

    def test_launch_written_and_immutable(self, deck_dir: Path) -> None:
        out = deck_dir
        completion = dj.run(deck_dir, STUB_JUDGES_ARG, order_seed=42, out_dir=out, env={})
        assert completion["total"] == 18  # 2 slots x (8 non-dup + that slot's own dup)

        launch_path = out / "launch.json"
        launch1 = json.loads(launch_path.read_text(encoding="utf-8"))
        assert launch1["presentation_sha256"]
        assert [j["slot"] for j in launch1["judges"]] == [0, 1]
        assert launch1["judges"][0]["requested_model"] == "model-a"
        assert launch1["judges"][0]["resolved_model"] == "model-a-stub-resolved"

        # Rerun: launch.json content is byte-identical (never overwritten).
        dj.run(deck_dir, STUB_JUDGES_ARG, order_seed=42, out_dir=out, env={})
        assert launch_path.read_text(encoding="utf-8") == json.dumps(
            launch1, indent=2, sort_keys=True
        ) + "\n"

    def test_launch_refuses_a_different_presentation(self, deck_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "out"
        dj.run(deck_dir, STUB_JUDGES_ARG, order_seed=1, out_dir=out, env={})

        other_doc = make_presentation_document()
        other_doc["bundles"][0]["rendered_text"] += "extra\n"
        other_doc["bundles"][0]["sha256"] = _sha(other_doc["bundles"][0]["rendered_text"])
        other_deck = tmp_path / "other-deck"
        other_deck.mkdir()
        (other_deck / "presentation.json").write_text(json.dumps(other_doc), encoding="utf-8")

        with pytest.raises(dj.HarnessError, match="different presentation"):
            dj.run(other_deck, STUB_JUDGES_ARG, order_seed=1, out_dir=out, env={})

    def test_per_slot_order_deterministic_and_duplicate_routed(
        self, deck_dir: Path, tmp_path: Path,
    ) -> None:
        out1 = tmp_path / "out1"
        out2 = tmp_path / "out2"
        dj.run(deck_dir, STUB_JUDGES_ARG, order_seed=7, out_dir=out1, env={})
        dj.run(deck_dir, STUB_JUDGES_ARG, order_seed=7, out_dir=out2, env={})

        order0_a = json.loads((out1 / "order" / "slot-0.json").read_text(encoding="utf-8"))
        order0_b = json.loads((out2 / "order" / "slot-0.json").read_text(encoding="utf-8"))
        assert order0_a["presentation_ids"] == order0_b["presentation_ids"]

        # Slot 0 sees ONLY its own duplicate (B901), never slot 1's (B902).
        assert "B901" in order0_a["presentation_ids"]
        assert "B902" not in order0_a["presentation_ids"]
        order1_a = json.loads((out1 / "order" / "slot-1.json").read_text(encoding="utf-8"))
        assert "B902" in order1_a["presentation_ids"]
        assert "B901" not in order1_a["presentation_ids"]

        # Different order_seed => (almost certainly) different permutation.
        out3 = tmp_path / "out3"
        dj.run(deck_dir, STUB_JUDGES_ARG, order_seed=999, out_dir=out3, env={})
        order0_c = json.loads((out3 / "order" / "slot-0.json").read_text(encoding="utf-8"))
        assert order0_c["presentation_ids"] != order0_a["presentation_ids"]

    def test_atomic_resume_skips_finished_pairs_byte_stable(
        self, deck_dir: Path, tmp_path: Path,
    ) -> None:
        out = tmp_path / "out"
        dj.run(deck_dir, STUB_JUDGES_ARG, order_seed=3, out_dir=out, env={})

        response_files = sorted((out / "responses" / "slot-0").glob("*.json"))
        assert response_files
        original_bytes = {p.name: p.read_bytes() for p in response_files}

        # Simulate "kill mid-run": delete the completion marker (as if the
        # process died before writing it) and rerun.
        (out / "judging_complete.json").unlink()
        dj.run(deck_dir, STUB_JUDGES_ARG, order_seed=3, out_dir=out, env={})

        for p in response_files:
            assert p.read_bytes() == original_bytes[p.name]
        assert (out / "judging_complete.json").exists()

    def test_resume_does_not_recompute_order_or_duplicate(
        self, deck_dir: Path, tmp_path: Path,
    ) -> None:
        out = tmp_path / "out"
        dj.run(deck_dir, STUB_JUDGES_ARG, order_seed=11, out_dir=out, env={})
        order_before = (out / "order" / "slot-0.json").read_bytes()

        # Delete one response so this pair is redone, but the ORDER file must
        # not be touched/regenerated.
        one_response = next((out / "responses" / "slot-0").glob("*.json"))
        one_response.unlink()
        dj.run(deck_dir, STUB_JUDGES_ARG, order_seed=11, out_dir=out, env={})

        assert (out / "order" / "slot-0.json").read_bytes() == order_before
        assert one_response.exists()

    def test_only_slot_and_only_presentation_id_control_prescreen(
        self, deck_dir: Path, tmp_path: Path,
    ) -> None:
        out = tmp_path / "out"
        completion = dj.run(
            deck_dir, STUB_JUDGES_ARG, order_seed=5, out_dir=out, env={},
            only_slot=0, only_presentation_id="B003",
        )
        assert completion["per_slot"] == {
            "0": {"ok": 1, "malformed": 0, "transport_failed": 0},
        }
        assert completion["total"] == 1
        assert (out / "responses" / "slot-0" / "B003.json").exists()
        assert not (out / "responses" / "slot-1").exists()

    def test_transport_failure_path_via_mocked_urlopen(
        self, deck_dir: Path, tmp_path: Path, monkeypatch,
    ) -> None:
        """Uses the REAL openai adapter (network path) with urlopen mocked at
        the function boundary — never touches the network."""
        out = tmp_path / "out"

        def _boom(request, timeout=None):  # noqa: ANN001
            raise dj.urllib.error.URLError("connection refused")

        monkeypatch.setattr(dj.urllib.request, "urlopen", _boom)
        env = {dj.env_var_name("openai"): "sk-test"}
        judges_arg = "openai:gpt-test,stub:model-b"

        with pytest.raises(dj.HarnessError, match="preflight failed"):
            dj.run(deck_dir, judges_arg, order_seed=1, out_dir=out, env=env, sleep=lambda s: None)


def test_env_var_names() -> None:
    assert dj.env_var_name("anthropic") == "S6_JUDGE_ANTHROPIC_KEY"
    assert dj.env_var_name("openai") == "S6_JUDGE_OPENAI_KEY"
    assert dj.env_var_name("google") == "S6_JUDGE_GOOGLE_KEY"
    assert dj.env_var_name("meta") == "S6_JUDGE_META_KEY"
    assert dj.env_var_name("deepseek") == "S6_JUDGE_DEEPSEEK_KEY"
    assert dj.base_url_env_var_name("meta") == "S6_JUDGE_META_BASE_URL"


def test_meta_requires_base_url() -> None:
    with pytest.raises(dj.TransportError, match="S6_JUDGE_META_BASE_URL"):
        dj.call_meta("m", "sys", "user", "key", None, 1.0)
