"""Phase-3 judge-bias probe: path guards, rule-breaker legality, stub e2e.

The stub end-to-end test depends on the locally built S6 deck and the owner DB
(both gitignored) and skips cleanly where they are absent.
"""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from app.domain.table.deck import deal_hand
from app.domain.table.engine import apply, start_hand
from tools import detection_probe as dp
from tools.detection_render import from_bot
from tools.probe_policies import rule_breaker_decision


class TestPathGuard:
    def test_refuses_live_deck_tree(self, tmp_path: Path) -> None:
        with pytest.raises(dp.ProbePathError):
            dp.assert_probe_paths(tmp_path, dp.FORBIDDEN_TREES[0])

    def test_refuses_paths_inside_live_trees(self) -> None:
        for tree in dp.FORBIDDEN_TREES:
            with pytest.raises(dp.ProbePathError):
                dp.assert_probe_paths(tree / "sub" / "dir")

    def test_refuses_identical_paths(self, tmp_path: Path) -> None:
        with pytest.raises(dp.ProbePathError):
            dp.assert_probe_paths(tmp_path / "x", tmp_path / "x")

    def test_accepts_distinct_outside_paths(self, tmp_path: Path) -> None:
        dp.assert_probe_paths(tmp_path / "a", tmp_path / "b")  # no raise


class TestRuleBreakerPolicy:
    def _play_hand(self, i: int, rng: random.Random):
        hand_seed = rng.randrange(1_000_000_000)
        state = start_hand(deal_hand(random.Random(hand_seed)), i % 9, [100.0] * 9)
        guard = 0
        while not state.hand_over:
            guard += 1
            assert guard <= 500, "hand did not terminate"
            state = apply(state, rule_breaker_decision(state, state.to_act_seat))
        return state

    def test_500_hands_legal_and_renderable(self) -> None:
        rng = random.Random(70001)
        for i in range(500):
            state = self._play_hand(i, rng)
            from_bot(state, i % 9)  # CanonicalHandError would fail the test

    def test_never_folds(self) -> None:
        # Terminal states must show the policy's seats reaching settlement:
        # a policy that never folds ends every hand it plays alone or at showdown.
        rng = random.Random(70002)
        state = self._play_hand(0, rng)
        folded = [s for s in state.seats if s.status.name == "FOLDED"]
        assert not folded, "rule-breaker lineup must never fold"


_DECK = dp._S6_ROOT / "deck"
_DB = Path(__file__).resolve().parents[1] / "data" / "poker_coach.db"


@pytest.mark.skipif(
    not (_DECK / "unblinding.json").exists() or not _DB.exists(),
    reason="local S6 deck / owner DB not present",
)
class TestStubEndToEnd:
    def test_build_and_stub_judge(self, tmp_path: Path) -> None:
        root = tmp_path / "probe"
        built = dp.build_probe_deck(root, db_path=_DB)
        assert set(built["stimuli"]) == set(dp.STIMULUS_ORDER)
        completion = dp.judge_probe(root, "stub:model-a")
        assert completion["per_slot"]["0"]["ok"] == 4
        rows = dp.report(root)
        assert len(rows) == 4
        assert {r["stimulus"] for r in rows} == set(dp.STIMULUS_ORDER)
        assert all(r["status"] == "ok" for r in rows)

    def test_probe_deck_is_deterministic(self, tmp_path: Path) -> None:
        a = tmp_path / "a"
        b = tmp_path / "b"
        dp.build_probe_deck(a, db_path=_DB)
        dp.build_probe_deck(b, db_path=_DB)
        assert (a / "deck" / "presentation.json").read_bytes() == (
            b / "deck" / "presentation.json"
        ).read_bytes()
