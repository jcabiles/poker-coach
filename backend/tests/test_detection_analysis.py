"""T6 (flywheel S6): the blind-detection analysis module.

Every pinned formula (control invalidation, balanced accuracy, AUC, d',
Kish n_eff, the stratified bootstrap) is exercised against a fixture whose
expected value is hand-derived in a comment next to the assertion — this file
is the record of "does the code compute what the spec says", not a smoke test.

Fixture shared by most of the deck-statistics tests (`MAIN_*` below): 6 human
+ 6 bot bundles, panel of 5 judges who give the SAME confidence to a bundle
(keeps every mean/AUC/d' computation exact by hand), one human bundle (H6)
and one bot bundle (B6) deliberately misclassified so balanced accuracy, AUC,
d', and the bootstrap all have real (non-trivial, non-degenerate) values.
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import NormalDist

import pytest

from tools.detection_analysis import (
    AGREEMENT_CAVEAT,
    N_EFF_POPULATION_NOTE,
    PER_JUDGE_POPULATION_NOTE,
    AnalysisError,
    BundleRecord,
    DeckBundleStat,
    DuplicateSlot,
    Judge,
    JudgeResponse,
    auc_mann_whitney,
    balanced_accuracy,
    bootstrap_deck,
    compute_deck_bundle_stats,
    d_prime,
    duplicate_consistency,
    evaluate_control,
    human_misclassification_rate,
    judge_agreement_rate,
    kish_n_eff,
    load_launch_manifest,
    load_presentation_hashes,
    load_responses,
    load_unblinding,
    per_judge_deck_stats,
    render_report,
    run_analysis,
)

# ---------------------------------------------------------------------------
# Hand-computed main fixture: 6 human + 6 bot, 5 judges, uniform per-bundle
# confidence (so panel_score == that confidence, exactly).
# ---------------------------------------------------------------------------

JUDGES5 = [Judge(i, f"vendor{i}", f"req{i}", f"res{i}") for i in range(5)]

# presentation_id -> (true class, confidence every judge gives)
MAIN_BUNDLES = {
    "h1": ("human", 80), "h2": ("human", 75), "h3": ("human", 65),
    "h4": ("human", 60), "h5": ("human", 55), "h6": ("human", 30),  # misclassified -> bot
    "b1": ("bot", 10), "b2": ("bot", 15), "b3": ("bot", 20),
    "b4": ("bot", 25), "b5": ("bot", 35), "b6": ("bot", 70),  # misclassified -> human
}


def _bundle_records(bundles=MAIN_BUNDLES) -> list[BundleRecord]:
    return [BundleRecord(pid, klass, False) for pid, (klass, _conf) in bundles.items()]


def _uniform_responses(bundles=MAIN_BUNDLES, judges=JUDGES5):
    responses = {}
    for pid, (_klass, conf) in bundles.items():
        label = "human" if conf >= 50 else "bot"
        for judge in judges:
            responses[(judge.slot, pid)] = JudgeResponse(judge.slot, pid, "ok", label, conf)
    return responses


def test_balanced_accuracy_and_misclassification_hand_computed():
    stats = compute_deck_bundle_stats(_bundle_records(), JUDGES5, _uniform_responses())
    # human_recall = 5/6 (h6 misclassified), bot_recall = 5/6 (b6 misclassified)
    # balanced_accuracy = (5/6 + 5/6) / 2 = 5/6
    assert balanced_accuracy(stats) == pytest.approx(5 / 6)
    # human_misclassification_rate = 1 - human_recall = 1/6
    assert human_misclassification_rate(stats) == pytest.approx(1 / 6)


def test_auc_mann_whitney_hand_computed():
    stats = compute_deck_bundle_stats(_bundle_records(), JUDGES5, _uniform_responses())
    # human scores [80,75,65,60,55,30] vs bot scores [10,15,20,25,35,70],
    # half-credit ties (no ties here). Wins per human score (of 6 bot scores):
    #   80 -> 6, 75 -> 6, 65 -> 5 (loses only to 70), 60 -> 5, 55 -> 5, 30 -> 4
    #   (30 beats 10,15,20,25; loses to 35,70)
    # total = 6+6+5+5+5+4 = 31 of 36 pairs
    assert auc_mann_whitney(stats) == pytest.approx(31 / 36)


def test_d_prime_hand_computed_non_extreme():
    stats = compute_deck_bundle_stats(_bundle_records(), JUDGES5, _uniform_responses())
    # hr = br = 5/6, neither extreme (not 0 or 1) so no correction applied.
    # p_human = 5/6, p_bot_false_positive = 1 - 5/6 = 1/6.
    # By antisymmetry of the standard normal quantile, z(1/6) == -z(5/6), so
    # d' = z(5/6) - z(1/6) = 2 * z(5/6).
    expected = 2 * NormalDist().inv_cdf(5 / 6)
    assert d_prime(stats) == pytest.approx(expected)


def test_d_prime_extreme_rate_correction_zero_recall():
    # 4 human bundles all mislabeled bot (hr=0), 4 bot bundles all correctly bot (br=1).
    stats = [
        DeckBundleStat(f"h{i}", "human", 5, 20.0, "bot", True) for i in range(4)
    ] + [
        DeckBundleStat(f"b{i}", "bot", 5, 10.0, "bot", True) for i in range(4)
    ]
    # hr=0 -> corrected to 1/(2*4)=0.125; br=1 -> false-positive rate 1-1=0
    # -> corrected to 1/(2*4)=0.125. Both corrected rates are equal, so
    # d' = z(0.125) - z(0.125) = 0.
    assert d_prime(stats) == pytest.approx(0.0, abs=1e-9)


def test_d_prime_extreme_rate_correction_perfect_recall():
    # Both classes perfectly recalled: hr=1, br=1.
    stats = [
        DeckBundleStat(f"h{i}", "human", 5, 90.0, "human", True) for i in range(4)
    ] + [
        DeckBundleStat(f"b{i}", "bot", 5, 10.0, "bot", True) for i in range(4)
    ]
    n = 4
    # hr=1 -> corrected 1 - 1/(2n); false-positive rate = 1-br = 0 -> corrected 1/(2n).
    # d' = z(1 - 1/(2n)) - z(1/(2n)) = 2 * z(1 - 1/(2n)) by antisymmetry.
    expected = 2 * NormalDist().inv_cdf(1 - 1 / (2 * n))
    assert d_prime(stats) == pytest.approx(expected)
    assert d_prime(stats) > 0


def test_less_than_three_usable_judges_excluded():
    bundles = _bundle_records() + [BundleRecord("h7", "human", False)]
    responses = _uniform_responses()
    # h7 only gets 2 usable responses -> excluded from inferential stats.
    responses[(0, "h7")] = JudgeResponse(0, "h7", "ok", "human", 90)
    responses[(1, "h7")] = JudgeResponse(1, "h7", "ok", "human", 90)
    stats = compute_deck_bundle_stats(bundles, JUDGES5, responses)
    h7 = next(s for s in stats if s.presentation_id == "h7")
    assert h7.n_usable == 2
    assert h7.included is False
    # excluding h7 must not change the hand-computed balanced accuracy above.
    included = [s for s in stats if s.included]
    assert balanced_accuracy(included) == pytest.approx(5 / 6)


# ---------------------------------------------------------------------------
# Kish n_eff — computable, and every degenerate case
# ---------------------------------------------------------------------------


def _abc_fixture():
    """3 judges (A,B,C), 4 bundles (x1,x2 human; x3,x4 bot), every response
    confidence pinned at 50 (irrelevant to n_eff/per-judge label stats, kept
    constant to isolate the label-vs-true-class arithmetic). Judge error
    vectors (own label != true class), chosen so Pearson correlations are
    exact fractions:  A = [0,0,0,1]   B = [0,1,0,1]   C = [1,0,1,0]
    (error = 1 on x4 for A; on x2,x4 for B; on x1,x3 for C)."""
    judges = [Judge(i, f"v{i}", "r", "r") for i in range(3)]
    bundles = [
        BundleRecord("x1", "human", False), BundleRecord("x2", "human", False),
        BundleRecord("x3", "bot", False), BundleRecord("x4", "bot", False),
    ]
    # true classes: x1=human, x2=human, x3=bot, x4=bot
    a_labels = ["human", "human", "bot", "human"]  # x4 mislabeled human -> error=1
    b_labels = ["human", "bot", "bot", "human"]  # wrong on x2 and x4
    c_labels = ["bot", "human", "human", "bot"]  # wrong on x1 and x3
    responses = {}
    pids = ["x1", "x2", "x3", "x4"]
    for slot, labels in zip((0, 1, 2), (a_labels, b_labels, c_labels), strict=True):
        for pid, label in zip(pids, labels, strict=True):
            responses[(slot, pid)] = JudgeResponse(slot, pid, "ok", label, 50)
    return judges, bundles, responses


def test_kish_n_eff_computable_hand_computed():
    judges, bundles, responses = _abc_fixture()
    result = kish_n_eff(bundles, judges, responses)
    # r(A,B) = 1/sqrt(3), r(A,C) = -1/sqrt(3), r(B,C) = -1  (Pearson, by hand
    # via the raw-score formula r = (n*Sxy - Sx*Sy) / sqrt((n*Sxx-Sx^2)(n*Syy-Sy^2)))
    # phi_bar = mean(1/sqrt3, -1/sqrt3, -1) = -1/3
    # n_eff = k / (1 + (k-1)*phi_bar) = 3 / (1 + 2*(-1/3)) = 3 / (1/3) = 9.0
    assert result["phi_bar"] == pytest.approx(-1 / 3)
    assert result["n_eff"] == pytest.approx(9.0)
    assert result["k"] == 3
    assert result["pairs_used"] == 3
    assert result["n_eff_low"] is False  # 9/3 = 3.0, not < 0.5
    assert result["population_note"] == N_EFF_POPULATION_NOTE


def test_kish_n_eff_degenerate_zero_variance_pair_unavailable():
    # Only 2 judges; judge B is always right (zero-variance error vector) ->
    # its only pair is skipped -> no computable pairs -> unavailable.
    judges = [Judge(0, "v0", "r", "r"), Judge(1, "v1", "r", "r")]
    bundles = [BundleRecord(f"x{i}", "human" if i % 2 else "bot", False) for i in range(4)]
    responses = {}
    for i, bundle in enumerate(bundles):
        responses[(0, bundle.presentation_id)] = JudgeResponse(
            0, bundle.presentation_id, "ok", "human" if i % 2 == 0 else "bot", 50
        )  # sometimes wrong -> variance
        responses[(1, bundle.presentation_id)] = JudgeResponse(
            1, bundle.presentation_id, "ok", bundle.klass, 50
        )  # always correct -> zero-variance error vector
    result = kish_n_eff(bundles, judges, responses)
    assert result["n_eff"] == "unavailable"
    assert result["pairs_used"] == 0
    assert result["population_note"] == N_EFF_POPULATION_NOTE


def test_kish_n_eff_degenerate_fewer_than_two_shared_bundles_unavailable():
    judges = [Judge(0, "v0", "r", "r"), Judge(1, "v1", "r", "r")]
    bundles = [BundleRecord("x1", "human", False), BundleRecord("x2", "bot", False)]
    responses = {
        (0, "x1"): JudgeResponse(0, "x1", "ok", "bot", 20),  # wrong
        (1, "x1"): JudgeResponse(1, "x1", "ok", "human", 80),  # right
        # x2 only judge 0 answers -> only 1 shared bundle for the (0,1) pair
        (0, "x2"): JudgeResponse(0, "x2", "ok", "bot", 20),
    }
    result = kish_n_eff(bundles, judges, responses)
    assert result["n_eff"] == "unavailable"
    assert result["population_note"] == N_EFF_POPULATION_NOTE


def test_kish_n_eff_degenerate_nonpositive_denominator_unavailable():
    # 2 judges, perfectly anti-correlated errors over 2 shared bundles ->
    # phi_bar = -1 -> denominator = 1 + (2-1)*(-1) = 0 <= 0 -> unavailable.
    judges = [Judge(0, "v0", "r", "r"), Judge(1, "v1", "r", "r")]
    bundles = [BundleRecord("x1", "human", False), BundleRecord("x2", "bot", False)]
    responses = {
        (0, "x1"): JudgeResponse(0, "x1", "ok", "human", 80),  # right -> error 0
        (0, "x2"): JudgeResponse(0, "x2", "ok", "human", 80),  # wrong -> error 1
        (1, "x1"): JudgeResponse(1, "x1", "ok", "bot", 20),  # wrong -> error 1
        (1, "x2"): JudgeResponse(1, "x2", "ok", "bot", 20),  # right -> error 0
    }
    result = kish_n_eff(bundles, judges, responses)
    assert result["n_eff"] == "unavailable"
    assert result["phi_bar"] == pytest.approx(-1.0)
    assert result["population_note"] == N_EFF_POPULATION_NOTE


def test_judge_agreement_rate_is_diagnostics_only_value():
    stats_bundles = _bundle_records()
    responses = _uniform_responses()
    # every judge gives the identical label per bundle (uniform fixture) ->
    # pairwise agreement rate is exactly 1.0.
    assert judge_agreement_rate(stats_bundles, JUDGES5, responses) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Per-judge deck performance (§d.3 "reported alongside")
# ---------------------------------------------------------------------------


def test_per_judge_deck_stats_hand_computed():
    judges, bundles, responses = _abc_fixture()
    result = per_judge_deck_stats(bundles, judges, responses)
    assert result["population_note"] == PER_JUDGE_POPULATION_NOTE
    rows = result["rows"]
    assert [row["slot"] for row in rows] == [0, 1, 2]  # deterministic, by slot

    # Judge A (slot 0): x1(human)->human OK, x2(human)->human OK,
    # x3(bot)->bot OK, x4(bot)->human WRONG.
    # human_recall = 2/2 = 1.0, bot_recall = 1/2 = 0.5
    # balanced_accuracy = (1.0 + 0.5)/2 = 0.75, human_misclass = 1 - 1.0 = 0.0
    a = rows[0]
    assert a["vendor"] == "v0"
    assert a["n_usable"] == 4
    assert a["human_recall"] == pytest.approx(1.0)
    assert a["bot_recall"] == pytest.approx(0.5)
    assert a["balanced_accuracy"] == pytest.approx(0.75)
    assert a["human_misclassification_rate"] == pytest.approx(0.0)
    # every response in this fixture is confidence=50 -> both class means are 50
    assert a["mean_confidence_human"] == {"human": pytest.approx(50.0), "bot": pytest.approx(50.0)}

    # Judge B (slot 1): x1->human OK, x2->bot WRONG, x3->bot OK, x4->human WRONG.
    # human_recall = 1/2 = 0.5, bot_recall = 1/2 = 0.5 -> balanced_accuracy = 0.5
    b = rows[1]
    assert b["human_recall"] == pytest.approx(0.5)
    assert b["bot_recall"] == pytest.approx(0.5)
    assert b["balanced_accuracy"] == pytest.approx(0.5)
    assert b["human_misclassification_rate"] == pytest.approx(0.5)

    # Judge C (slot 2): x1->bot WRONG, x2->human OK, x3->human WRONG, x4->bot OK.
    # human_recall = 1/2 = 0.5, bot_recall = 1/2 = 0.5 -> balanced_accuracy = 0.5
    c = rows[2]
    assert c["human_recall"] == pytest.approx(0.5)
    assert c["bot_recall"] == pytest.approx(0.5)
    assert c["balanced_accuracy"] == pytest.approx(0.5)


def test_per_judge_deck_stats_unusable_responses_excluded_from_n_usable():
    judges = [Judge(0, "v0", "r", "r")]
    bundles = [BundleRecord("x1", "human", False), BundleRecord("x2", "bot", False)]
    responses = {
        (0, "x1"): JudgeResponse(0, "x1", "ok", "human", 90),
        (0, "x2"): JudgeResponse(0, "x2", "malformed-final", None, None),  # unusable
    }
    result = per_judge_deck_stats(bundles, judges, responses)
    row = result["rows"][0]
    assert row["n_usable"] == 1
    assert row["human_recall"] == pytest.approx(1.0)
    assert row["bot_recall"] is None  # no usable bot responses at all
    assert row["balanced_accuracy"] is None  # undefined when either recall is None
    assert row["mean_confidence_human"] == {"human": pytest.approx(90.0), "bot": None}


# ---------------------------------------------------------------------------
# Bootstrap determinism
# ---------------------------------------------------------------------------


def test_bootstrap_same_seed_byte_identical():
    stats = compute_deck_bundle_stats(_bundle_records(), JUDGES5, _uniform_responses())
    a = bootstrap_deck(stats, seed=777, b_iterations=200)
    b = bootstrap_deck(stats, seed=777, b_iterations=200)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_bootstrap_different_seed_differs():
    stats = compute_deck_bundle_stats(_bundle_records(), JUDGES5, _uniform_responses())
    a = bootstrap_deck(stats, seed=1, b_iterations=200)
    b = bootstrap_deck(stats, seed=2, b_iterations=200)
    assert a["balanced_accuracy"]["ci_95"] != b["balanced_accuracy"]["ci_95"]


# ---------------------------------------------------------------------------
# Control invalidation matrix
# ---------------------------------------------------------------------------


def _control_responses(entries: dict[int, tuple[str, str, int | None]]):
    """slot -> (status, label, confidence); entries omitted are 'missing'."""
    out = {}
    for slot, (status, label, confidence) in entries.items():
        out[(slot, "control")] = JudgeResponse(slot, "control", status, label, confidence)
    return out


CONTROL = BundleRecord("control", "bot", True)


def test_control_invalidation_passes():
    # mean(10,10,10,10,20)=12 < 50; 4/5 label bot (slot4 labels human) -> valid
    responses = _control_responses(
        {
            0: ("ok", "bot", 10), 1: ("ok", "bot", 10), 2: ("ok", "bot", 10),
            3: ("ok", "bot", 10), 4: ("ok", "human", 20),
        }
    )
    result = evaluate_control(CONTROL, JUDGES5, responses)
    assert result["valid"] is True
    assert result["mean_below_50"] is True
    assert result["majority_bot_ok"] is True


def test_control_invalidation_fails_on_mean():
    # 4/5 label bot, but confidences push the mean to >= 50.
    responses = _control_responses(
        {
            0: ("ok", "bot", 60), 1: ("ok", "bot", 60), 2: ("ok", "bot", 60),
            3: ("ok", "bot", 60), 4: ("ok", "human", 20),
        }
    )
    result = evaluate_control(CONTROL, JUDGES5, responses)
    assert result["mean_confidence"] == pytest.approx(52.0)
    assert result["mean_below_50"] is False
    assert result["valid"] is False


def test_control_invalidation_fails_on_four_of_five():
    # mean well below 50, but only 3 of 5 label bot.
    responses = _control_responses(
        {
            0: ("ok", "bot", 5), 1: ("ok", "bot", 5), 2: ("ok", "bot", 5),
            3: ("ok", "human", 10), 4: ("ok", "human", 10),
        }
    )
    result = evaluate_control(CONTROL, JUDGES5, responses)
    assert result["bot_label_count"] == 3
    assert result["majority_bot_ok"] is False
    assert result["valid"] is False


def test_control_invalidation_missing_responses_count_against_conjunct():
    # Only 3 usable responses (2 missing); missing counts against 4-of-5, not
    # for it, so majority_bot_ok is False even though every USABLE judge
    # said "bot".
    responses = _control_responses(
        {0: ("ok", "bot", 5), 1: ("ok", "bot", 5), 2: ("ok", "bot", 5)}
    )
    result = evaluate_control(CONTROL, JUDGES5, responses)
    assert result["bot_label_count"] == 3
    assert result["valid"] is False
    assert result["k"] == 5
    assert result["threshold_required"] == 4


# ---------------------------------------------------------------------------
# Duplicate consistency
# ---------------------------------------------------------------------------


def test_duplicate_consistency():
    duplicates = [
        DuplicateSlot(0, "dup0", "h1"),
        DuplicateSlot(1, "dup1", "h2"),
    ]
    responses = dict(_uniform_responses())
    # slot0's duplicate matches its source exactly -> label_match True, delta 0
    responses[(0, "dup0")] = JudgeResponse(0, "dup0", "ok", "human", 80)
    # slot1's duplicate differs in confidence by 15, same label
    responses[(1, "dup1")] = JudgeResponse(1, "dup1", "ok", "human", 60)
    result = duplicate_consistency(duplicates, responses)
    assert result["summary"]["n_comparable"] == 2
    assert result["summary"]["label_match_rate"] == pytest.approx(1.0)
    # deltas: |80-80|=0, |60-75|=15 -> mean 7.5
    assert result["summary"]["mean_abs_confidence_delta"] == pytest.approx(7.5)


def test_duplicate_consistency_missing_response_not_comparable():
    duplicates = [DuplicateSlot(0, "dup0", "h1")]
    responses = dict(_uniform_responses())
    # no response recorded at all for the duplicate presentation
    result = duplicate_consistency(duplicates, responses)
    assert result["summary"]["n_comparable"] == 0
    assert result["per_judge"][0]["duplicate_status"] == "missing"


# ---------------------------------------------------------------------------
# Loaders — schema validation
# ---------------------------------------------------------------------------


def _write(path: Path, doc) -> None:
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_load_launch_manifest_rejects_non_contiguous_slots(tmp_path):
    _write(
        tmp_path / "launch.json",
        {
            "judges": [
                {"slot": 0, "vendor": "a", "requested_model": "x", "resolved_model": "x1"},
                {"slot": 2, "vendor": "b", "requested_model": "y", "resolved_model": "y1"},
            ]
        },
    )
    with pytest.raises(AnalysisError, match="0..1"):
        load_launch_manifest(tmp_path)


def test_load_responses_ok_status_requires_valid_parsed(tmp_path):
    (tmp_path / "responses").mkdir()
    _write(
        tmp_path / "responses" / "0-h1.json",
        {"slot": 0, "presentation_id": "h1", "raw_response": "{}", "parsed": None, "status": "ok"},
    )
    judges = [Judge(0, "v", "r", "r")]
    with pytest.raises(AnalysisError, match="parsed"):
        load_responses(tmp_path, judges)


def test_load_responses_malformed_status_allows_null_parsed(tmp_path):
    (tmp_path / "responses").mkdir()
    _write(
        tmp_path / "responses" / "0-h1.json",
        {
            "slot": 0, "presentation_id": "h1", "raw_response": "garbage",
            "parsed": None, "status": "malformed-final",
        },
    )
    judges = [Judge(0, "v", "r", "r")]
    responses = load_responses(tmp_path, judges)
    assert responses[(0, "h1")].usable is False


def test_load_responses_finds_files_nested_under_per_slot_subdirs(tmp_path):
    # `detection_judge.py` (T5) actually writes
    # `responses/slot-<k>/<presentation_id>.json`, not a flat directory.
    slot_dir = tmp_path / "responses" / "slot-0"
    slot_dir.mkdir(parents=True)
    _write(
        slot_dir / "h1.json",
        {
            "slot": 0, "presentation_id": "h1", "raw_responses": ["{}"],
            "parsed": {"label": "human", "confidence_human": 80, "reason": "r"},
            "status": "ok",
        },
    )
    judges = [Judge(0, "v", "r", "r")]
    responses = load_responses(tmp_path, judges)
    assert responses[(0, "h1")].usable is True


def test_load_unblinding_requires_duplicate_class_human(tmp_path):
    _write(
        tmp_path / "unblinding.json",
        {
            "bundles": [{"presentation_id": "h1", "class": "human", "is_control": False}],
            "judge_duplicates": {
                "slots": [
                    {
                        "slot": 0, "presentation_id": "dup0",
                        "source_presentation_id": "b1", "class": "bot",
                    }
                ]
            },
        },
    )
    with pytest.raises(AnalysisError, match="human"):
        load_unblinding(tmp_path)


def test_load_presentation_hashes(tmp_path):
    _write(
        tmp_path / "presentation.json",
        {"bundles": [{"presentation_id": "h1", "rendered_text": "t", "sha256": "abc"}]},
    )
    assert load_presentation_hashes(tmp_path) == {"h1": "abc"}


# ---------------------------------------------------------------------------
# Full-pipeline: batch-invalid path and valid path, byte-determinism
# ---------------------------------------------------------------------------


def _build_deck_dir(tmp_path: Path, control_valid: bool) -> Path:
    deck_dir = tmp_path / "deck"
    deck_dir.mkdir()
    bundles = [
        {"presentation_id": pid, "class": klass, "is_control": False}
        for pid, (klass, _conf) in MAIN_BUNDLES.items()
    ]
    bundles.append({"presentation_id": "control", "class": "bot", "is_control": True})
    unblinding = {
        "bundles": bundles,
        "judge_duplicates": {
            "slots": [
                {
                    "slot": 0, "presentation_id": "dup0",
                    "source_presentation_id": "h1", "class": "human",
                },
                {
                    "slot": 1, "presentation_id": "dup1",
                    "source_presentation_id": "h2", "class": "human",
                },
            ]
        },
    }
    _write(deck_dir / "unblinding.json", unblinding)
    presentation = {
        "bundles": [
            {"presentation_id": pid, "rendered_text": "x", "sha256": "sha-" + pid}
            for pid in list(MAIN_BUNDLES) + ["control", "dup0", "dup1"]
        ]
    }
    _write(deck_dir / "presentation.json", presentation)
    return deck_dir


def _build_judging_dir(tmp_path: Path, out_name: str, control_valid: bool) -> Path:
    judging_dir = tmp_path / out_name
    judging_dir.mkdir()
    _write(
        judging_dir / "launch.json",
        {
            "judges": [
                {"slot": i, "vendor": f"v{i}", "requested_model": "req", "resolved_model": "res"}
                for i in range(5)
            ]
        },
    )
    _write(judging_dir / "judging_complete.json", {"complete": True})
    responses_dir = judging_dir / "responses"
    responses_dir.mkdir()

    def _write_response(slot, pid, status, label, confidence):
        # Mirrors `detection_judge.py`'s actual on-disk layout:
        # responses/slot-<k>/<presentation_id>.json
        slot_dir = responses_dir / f"slot-{slot}"
        slot_dir.mkdir(exist_ok=True)
        _write(
            slot_dir / f"{pid}.json",
            {
                "slot": slot, "presentation_id": pid, "raw_response": "{}",
                "parsed": (
                    {"label": label, "confidence_human": confidence, "reason": "r"}
                    if status == "ok" else None
                ),
                "status": status,
            },
        )

    for pid, (_klass, conf) in MAIN_BUNDLES.items():
        label = "human" if conf >= 50 else "bot"
        for slot in range(5):
            _write_response(slot, pid, "ok", label, conf)

    if control_valid:
        control_confidences = [10, 10, 10, 10, 20]
        control_labels = ["bot", "bot", "bot", "bot", "human"]
    else:
        control_confidences = [60, 60, 60, 60, 60]
        control_labels = ["bot", "bot", "bot", "bot", "bot"]
    for slot in range(5):
        _write_response(slot, "control", "ok", control_labels[slot], control_confidences[slot])

    _write_response(0, "dup0", "ok", "human", 80)  # matches h1 exactly
    _write_response(1, "dup1", "ok", "human", 60)  # differs from h2 (75) by 15

    return judging_dir


def test_full_run_batch_invalid_emits_diagnostics_only(tmp_path):
    deck_dir = _build_deck_dir(tmp_path, control_valid=False)
    judging_dir = _build_judging_dir(tmp_path, "judging", control_valid=False)
    out_dir = tmp_path / "out"
    analysis = run_analysis(
        deck_dir=deck_dir, judging_dir=judging_dir, bootstrap_seed=1, out_dir=out_dir,
        bootstrap_b=50,
    )
    assert analysis["batch_valid"] is False
    assert "deck" not in analysis
    assert "bootstrap" not in analysis
    assert "n_eff" not in analysis
    # per-judge deck performance is inferential (deck-performance) — the
    # invalid branch keeps its diagnostics-only shape and never emits it.
    assert "per_judge" not in analysis
    assert analysis["completeness"]["missing_pairs"] == []
    assert (out_dir / "analysis.json").exists()
    assert (out_dir / "report.txt").exists()
    assert "Per-judge" not in (out_dir / "report.txt").read_text(encoding="utf-8")


def test_full_run_valid_batch_has_registered_n_eff_uses(tmp_path):
    deck_dir = _build_deck_dir(tmp_path, control_valid=True)
    judging_dir = _build_judging_dir(tmp_path, "judging", control_valid=True)
    out_dir = tmp_path / "out"
    analysis = run_analysis(
        deck_dir=deck_dir, judging_dir=judging_dir, bootstrap_seed=42, out_dir=out_dir,
        bootstrap_b=100,
    )
    assert analysis["batch_valid"] is True

    # Uniform-per-bundle fixture -> every judge gives identical labels, so
    # every pairwise error correlation is exactly 1.0 -> phi_bar=1.0 ->
    # n_eff = k / (1 + (k-1)*1) = k / k = 1.0 exactly, for k=5.
    assert analysis["n_eff"]["n_eff"] == pytest.approx(1.0)
    assert analysis["n_eff"]["k"] == 5
    assert analysis["n_eff"]["n_eff_low"] is True  # 1.0/5 = 0.2 < 0.5

    # (i) n_eff beside k in every results table
    for name in ("balanced_accuracy", "human_misclassification_rate", "auc", "d_prime"):
        table = analysis["deck"][name]
        assert table["k"] == 5
        assert table["n_eff"] == pytest.approx(1.0)

    # (ii) evidential_weight references n_eff, never k
    assert analysis["evidential_weight"]["basis"] == "n_eff"
    assert analysis["evidential_weight"]["value"] == pytest.approx(1.0)

    # (iii) judge-agreement rate only in diagnostics, with the fixed caveat
    assert analysis["diagnostics"]["judge_agreement"]["rate"] == pytest.approx(1.0)
    assert analysis["diagnostics"]["judge_agreement"]["caveat"] == AGREEMENT_CAVEAT
    assert "judge_agreement" not in analysis.get("deck", {})

    # (iv) n_eff_low flag present and computable
    assert analysis["n_eff"]["n_eff_low"] is True

    # n_eff/point-estimate population disclosure: n_eff is drawn from the
    # FULL analysis deck while the point estimates beside it use only
    # >=3-usable bundles — the fixed note must appear in the n_eff block,
    # the deck block, and every per-metric table (analysis.json), AND in
    # report.txt.
    assert analysis["n_eff"]["population_note"] == N_EFF_POPULATION_NOTE
    assert analysis["deck"]["n_eff_population_note"] == N_EFF_POPULATION_NOTE
    for name in ("balanced_accuracy", "human_misclassification_rate", "auc", "d_prime"):
        assert analysis["deck"][name]["n_eff_population_note"] == N_EFF_POPULATION_NOTE
    report_text_for_note = (out_dir / "report.txt").read_text(encoding="utf-8")
    assert N_EFF_POPULATION_NOTE in report_text_for_note

    # hand-computed deck stats carried through the full pipeline unchanged
    assert analysis["deck"]["balanced_accuracy"]["value"] == pytest.approx(5 / 6)
    assert analysis["deck"]["auc"]["value"] == pytest.approx(31 / 36)

    # duplicate consistency
    dup_summary = analysis["duplicate_consistency"]["summary"]
    assert dup_summary["n_comparable"] == 2
    assert dup_summary["mean_abs_confidence_delta"] == pytest.approx(7.5)

    # input hashes recorded for all three frozen inputs
    assert set(analysis["input_hashes"]) == {
        "judging_complete.json", "unblinding.json", "presentation.json",
    }
    assert all(isinstance(v, str) and len(v) == 64 for v in analysis["input_hashes"].values())
    assert analysis["bootstrap_seed"] == 42

    # report.txt renders without raising and mentions the caveat verbatim
    report_text = (out_dir / "report.txt").read_text(encoding="utf-8")
    assert AGREEMENT_CAVEAT in report_text
    assert render_report(analysis) == report_text

    # §d.3 "Per-judge statistics reported alongside": the uniform fixture
    # gives every judge the identical response per bundle, so each of the 5
    # per-judge rows reproduces the hand-computed panel-level numbers.
    #   human confidences [80,75,65,60,55,30] -> mean = 365/6
    #   bot confidences   [10,15,20,25,35,70] -> mean = 175/6
    per_judge = analysis["per_judge"]
    assert per_judge["population_note"] == PER_JUDGE_POPULATION_NOTE
    assert [row["slot"] for row in per_judge["rows"]] == [0, 1, 2, 3, 4]
    for row in per_judge["rows"]:
        assert row["n_usable"] == 12
        assert row["human_recall"] == pytest.approx(5 / 6)
        assert row["bot_recall"] == pytest.approx(5 / 6)
        assert row["balanced_accuracy"] == pytest.approx(5 / 6)
        assert row["human_misclassification_rate"] == pytest.approx(1 / 6)
        assert row["mean_confidence_human"]["human"] == pytest.approx(365 / 6)
        assert row["mean_confidence_human"]["bot"] == pytest.approx(175 / 6)
    assert "Per-judge deck performance" in report_text
    assert PER_JUDGE_POPULATION_NOTE in report_text


def test_full_run_byte_identical_same_seed(tmp_path):
    deck_dir = _build_deck_dir(tmp_path, control_valid=True)
    judging_dir = _build_judging_dir(tmp_path, "judging", control_valid=True)
    out_a = tmp_path / "out_a"
    out_b = tmp_path / "out_b"
    run_analysis(
        deck_dir=deck_dir, judging_dir=judging_dir, bootstrap_seed=99, out_dir=out_a,
        bootstrap_b=50,
    )
    run_analysis(
        deck_dir=deck_dir, judging_dir=judging_dir, bootstrap_seed=99, out_dir=out_b,
        bootstrap_b=50,
    )
    assert (out_a / "analysis.json").read_bytes() == (out_b / "analysis.json").read_bytes()
    assert (out_a / "report.txt").read_bytes() == (out_b / "report.txt").read_bytes()


def test_full_run_requires_exactly_one_control_bundle(tmp_path):
    deck_dir = _build_deck_dir(tmp_path, control_valid=True)
    unblinding = json.loads((deck_dir / "unblinding.json").read_text())
    unblinding["bundles"] = [b for b in unblinding["bundles"] if not b["is_control"]]
    _write(deck_dir / "unblinding.json", unblinding)
    judging_dir = _build_judging_dir(tmp_path, "judging", control_valid=True)
    with pytest.raises(AnalysisError, match="control bundle"):
        run_analysis(
            deck_dir=deck_dir, judging_dir=judging_dir, bootstrap_seed=1,
            out_dir=tmp_path / "out", bootstrap_b=10,
        )
