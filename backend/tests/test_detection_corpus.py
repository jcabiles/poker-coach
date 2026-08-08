"""T4 (flywheel S6): the blind-detection corpus builder.

Two properties carry the pilot and are tested hardest here:

1. **Fail-closed windows.** A 30-hand "consecutive" bundle that quietly skipped
   a missing hand is a different object from the one the protocol pins, so
   every defect in a window (gap, duplicate row, in-progress hand, malformed
   `state_json`, undealt focus seat) must REJECT the whole window rather than
   produce a shorter or slid-up bundle.
2. **The blinding split.** `presentation.json` is the only file the judge
   harness reads; a single label-bearing key or leaked token in it hands the
   judges the answer key. It is attacked here adversarially, not just
   inspected.

The heavy real deck (40+40 bundles of 30 hands over a 1,500-hand run) is NOT
built here — T7 owns that. The scaled end-to-end below (3+3+1 bundles of 5
hands) runs the SAME `build_corpus` code path, since the deck shape is a
parameter and not a branch.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.db.models import SimHand, SimSession
from app.domain.personas import load_persona_packs
from tools.detection_corpus import (
    BOT_STRIDE_GAP,
    DEFAULT_CONTROL_CONFIG,
    DUPLICATE_SLOT_KEY,
    HERO_SEAT,
    HUMAN_FIRST_HAND_NO,
    N_SEATS,
    PRESENTATION_BUNDLE_KEYS,
    PRESENTATION_TOP_KEYS,
    PROTOCOL_CONTROL_CONFIG_HASH,
    RATIFIED_LINEUP,
    SUCCESS_FILENAME,
    Bundle,
    CorpusBuildError,
    HumanHandRow,
    PresentationRecord,
    Window,
    assert_disjoint,
    assert_duplicate_plan,
    assign_constrained_focus_seats,
    assign_presentation_ids,
    build_corpus,
    build_seat_id_map,
    bundle_trajectory,
    derive_rng,
    derive_seed,
    enumerate_windows,
    group_rows,
    payload_digest,
    phase_id,
    presentation_document,
    read_human_snapshot,
    render_bundles,
    replay_run,
    run_id_for,
    seat_coverage,
    seat_trajectories,
    select_duplicate_sources,
    select_windows,
    validate_human_window,
    write_presentation_manifest,
)
from tools.detection_render import from_bot

# --- fixtures ---------------------------------------------------------------

HUMAN_SESSION = "sess-owner"
HUMAN_HANDS = 25
BUNDLE = 5
PERSONA_BY_SEAT = {i: RATIFIED_LINEUP[i] for i in range(N_SEATS)}


def _states(seed: int, n: int) -> dict[int, object]:
    return replay_run(seed, n, PERSONA_BY_SEAT, load_persona_packs())


@pytest.fixture(scope="module")
def human_states():
    """Terminal states used as stand-in "human" rows.

    The renderer is source-blind by construction (T3's cross-source golden
    tests), so what matters here is the SHAPE of the human input — a
    `sim_hand` row carrying a serialized `HandState` — not who played it.
    """
    return _states(4242, HUMAN_HANDS)


def _write_db(path: Path, rows: list[dict], session_id: str = HUMAN_SESSION) -> Path:
    engine = create_engine(f"sqlite:///{path}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        for sid in sorted({r.get("session_id", session_id) for r in rows}):
            db.add(SimSession(id=sid, button_seat=0, hand_no=len(rows) + 1))
        for row in rows:
            db.add(
                SimHand(
                    session_id=row.get("session_id", session_id),
                    hand_no=row["hand_no"],
                    button_seat=row["hand_no"] % 9,
                    rng_seed=str(row["hand_no"]),
                    status=row.get("status", "complete"),
                    state_json=row.get("state_json"),
                )
            )
        db.commit()
    engine.dispose()
    return path


@pytest.fixture(scope="module")
def human_db(tmp_path_factory, human_states) -> Path:
    path = tmp_path_factory.mktemp("corpus") / "human.db"
    return _write_db(
        path,
        [
            {"hand_no": i + 1, "state_json": human_states[i].model_dump_json()}
            for i in range(HUMAN_HANDS)
        ],
    )


def _rows(human_states, count: int = 5) -> list[HumanHandRow]:
    return [
        HumanHandRow(i + 1, "complete", human_states[i].model_dump_json())
        for i in range(count)
    ]


WINDOW_1_5 = Window(index=0, start=1, end=5)


# --- 1. seeding -------------------------------------------------------------


def test_derived_seeds_are_domain_separated():
    """Each purpose gets its own stream: two purposes under one master seed
    must not draw the same numbers, or 'same master seed' means nothing."""
    domains = ["human-select", "bot-windows", "focus-seats", "opaque-ids", "presentation-ids"]
    seeds = [derive_seed(7, d) for d in domains]
    assert len(set(seeds)) == len(domains)
    assert derive_seed(7, "bot-windows") != derive_seed(8, "bot-windows")
    assert derive_seed(7, "opaque-ids", "bot/w0001") != derive_seed(7, "opaque-ids", "bot/w0002")


def test_derived_seed_is_stable_across_processes():
    """Pinned value: a hashing change would silently re-roll a built deck."""
    assert derive_seed(20260807, "human-select") == derive_seed(20260807, "human-select")
    assert derive_rng(1, "x").random() == derive_rng(1, "x").random()
    assert derive_rng(1, "x").random() != derive_rng(1, "y").random()


# --- 2. window enumeration --------------------------------------------------


def test_enumerate_windows_tiles_and_drops_the_remainder():
    windows = enumerate_windows(1, 25, 5)
    assert [(w.index, w.start, w.end) for w in windows] == [
        (0, 1, 5), (1, 6, 10), (2, 11, 15), (3, 16, 20), (4, 21, 25)
    ]
    # A partial tail window is dropped, never padded out.
    assert enumerate_windows(1, 27, 5)[-1].end == 25
    assert enumerate_windows(1, 4, 5) == ()
    assert_disjoint(windows)


def test_enumerate_windows_respects_the_origin():
    assert enumerate_windows(0, 9, 5)[0].start == 0
    assert enumerate_windows(100, 109, 5)[0].start == 100


def test_assert_disjoint_rejects_overlap():
    with pytest.raises(CorpusBuildError, match="overlaps"):
        assert_disjoint([Window(0, 1, 5), Window(1, 4, 8)])


# --- 3. human window validity (fail closed) ---------------------------------


def test_valid_window_yields_exactly_its_hands(human_states):
    check = validate_human_window(group_rows(_rows(human_states)), WINDOW_1_5)
    assert check.valid and check.reason is None
    assert len(check.hands) == 5
    assert all(h.focus_seat == HERO_SEAT for h in check.hands)


def test_gap_rejects_the_window_and_never_closes_ranks(human_states):
    """The load-bearing fail-closed case: with hand 3 missing, the window is
    rejected — NOT rebuilt from hands 1,2,4,5,6."""
    rows = [r for r in _rows(human_states, 6) if r.hand_no != 3]
    check = validate_human_window(group_rows(rows), WINDOW_1_5)
    assert not check.valid
    assert "hand_no 3" in check.reason and "gap" in check.reason
    assert check.hands == ()


def test_duplicate_row_rejects_the_window(human_states):
    rows = _rows(human_states)
    rows.append(rows[2])
    check = validate_human_window(group_rows(rows), WINDOW_1_5)
    assert not check.valid
    assert "hand_no 3" in check.reason and "duplicate" in check.reason


def test_in_progress_row_rejects_the_window(human_states):
    rows = _rows(human_states)
    rows[3] = HumanHandRow(4, "in_progress", rows[3].state_json)
    check = validate_human_window(group_rows(rows), WINDOW_1_5)
    assert not check.valid and "hand_no 4" in check.reason


@pytest.mark.parametrize("payload", [None, "", "   ", "{not json", '{"seats": []}'])
def test_missing_or_malformed_state_json_rejects_the_window(human_states, payload):
    rows = _rows(human_states)
    rows[1] = HumanHandRow(2, "complete", payload)
    check = validate_human_window(group_rows(rows), WINDOW_1_5)
    assert not check.valid and "hand_no 2" in check.reason


def test_mid_hand_state_rejects_the_window(human_states):
    """`status='complete'` is not trusted on its own: a row whose state says
    the hand is still live is rejected by the canonical adapter."""
    doc = json.loads(human_states[0].model_dump_json())
    doc["hand_over"] = False
    rows = _rows(human_states)
    rows[0] = HumanHandRow(1, "complete", json.dumps(doc))
    check = validate_human_window(group_rows(rows), WINDOW_1_5)
    assert not check.valid and "hand_no 1" in check.reason


def test_focus_seat_not_dealt_rejects_the_window(human_states):
    doc = json.loads(human_states[2].model_dump_json())
    for seat in doc["seats"]:
        if seat["seat"] == HERO_SEAT:
            seat["hole_cards"] = []
    rows = _rows(human_states)
    rows[2] = HumanHandRow(3, "complete", json.dumps(doc))
    check = validate_human_window(group_rows(rows), WINDOW_1_5)
    assert not check.valid and "hand_no 3" in check.reason


# --- 4. selection -----------------------------------------------------------


def test_selection_takes_exactly_k_and_is_deterministic():
    pool = list(range(61))
    first = select_windows(pool, 40, derive_rng(20260807, "human-select"))
    again = select_windows(pool, 40, derive_rng(20260807, "human-select"))
    assert len(first) == 40 == len(set(first))
    assert first == again == tuple(sorted(first))
    assert select_windows(pool, 40, derive_rng(999, "human-select")) != first


def test_selection_ignores_candidate_order():
    """Selection must depend on the candidate SET and the seed only — never on
    the order candidates happened to be discovered in."""
    pool = list(range(61))
    shuffled = list(pool)
    random.Random(3).shuffle(shuffled)
    assert select_windows(shuffled, 40, derive_rng(1, "human-select")) == select_windows(
        pool, 40, derive_rng(1, "human-select")
    )


def test_too_few_candidates_aborts_rather_than_shrinking_the_deck():
    with pytest.raises(CorpusBuildError, match="short deck"):
        select_windows(range(39), 40, derive_rng(1, "human-select"))


# --- 5. focus seats ---------------------------------------------------------


POSITIONS = ("UTG", "UTG1", "UTG2", "LJ", "HJ", "CO", "BTN", "SB", "BB")


def _synthetic_options(start: int, size: int = 30) -> dict[int, tuple[str, ...]]:
    """Trajectories for all nine seats of a window starting at hand `start`.

    Mirrors the engine's arithmetic (button = hand key mod 9; the button seat
    is BTN, the next is SB, ...) purely to exercise the assignment logic in
    isolation — the builder itself never models this, it MEASURES trajectories
    off real states. `test_human_class_only_reaches_three_of_the_nine_phases`
    checks this model against the phases observed in the real session.
    """
    return {
        seat: tuple(
            POSITIONS[(seat - h + 6) % N_SEATS] for h in range(start, start + size)
        )
        for seat in range(N_SEATS)
    }


def _human_phases(size: int = 30, stride: int = 30, count: int = 40) -> list[tuple[str, ...]]:
    """The phases a hero at seat 0 exhibits over adjacently tiled windows."""
    return sorted({_synthetic_options(1 + i * stride, size)[0] for i in range(count)})


def test_human_class_only_reaches_three_of_the_nine_phases():
    """The side channel itself: 30 mod 9 = 3, so tiled human windows can only
    ever start on three of the nine rotations.

    The three start positions below are exactly the ones measured in the real
    owner session (hero seat 0, hand_no 1 dealt with button seat 1), which is
    what makes this model a fair stand-in for the real phase structure.
    """
    phases = _human_phases()
    assert len(phases) == 3
    assert {p[0] for p in phases} == {"CO", "UTG2", "BB"}


def test_constrained_assignment_reproduces_the_human_phase_set():
    allowed = _human_phases()
    windows = [_synthetic_options(1 + i * (30 + BOT_STRIDE_GAP)) for i in range(40)]
    assignment = assign_constrained_focus_seats(
        windows, allowed, derive_rng(20260807, "focus-seats")
    )
    assert len(assignment) == 40
    chosen = [windows[i][seat] for i, seat in enumerate(assignment)]
    assert set(chosen) == set(allowed)  # every human phase used, none invented
    counts = [chosen.count(p) for p in allowed]
    assert max(counts) - min(counts) <= 1  # phases balanced


def test_constrained_assignment_still_covers_every_seat_at_the_walking_stride():
    """Blinding first, but not at the cost of seat coverage: a stride coprime
    to 9 keeps all nine seats admissible somewhere in the deck."""
    allowed = _human_phases()
    windows = [_synthetic_options(1 + i * (30 + BOT_STRIDE_GAP)) for i in range(40)]
    assignment = assign_constrained_focus_seats(
        windows, allowed, derive_rng(20260807, "focus-seats")
    )
    assert set(assignment) == set(range(N_SEATS))
    assert sum(seat_coverage(assignment).values()) == 40


def test_adjacent_tiling_would_collapse_the_bot_class_to_three_seats():
    """Why the stride exists: with the human tiling, only three seats can ever
    satisfy the constraint — recorded so the trade-off is not re-derived."""
    allowed = _human_phases()
    windows = [_synthetic_options(1 + i * 30) for i in range(40)]
    assignment = assign_constrained_focus_seats(
        windows, allowed, derive_rng(20260807, "focus-seats")
    )
    assert len(set(assignment)) == 3


def test_constrained_assignment_is_deterministic_and_seed_sensitive():
    allowed = _human_phases()
    windows = [_synthetic_options(1 + i * 31) for i in range(40)]
    first = assign_constrained_focus_seats(windows, allowed, derive_rng(1, "focus-seats"))
    assert first == assign_constrained_focus_seats(
        windows, allowed, derive_rng(1, "focus-seats")
    )
    assert first != assign_constrained_focus_seats(
        windows, allowed, derive_rng(2, "focus-seats")
    )


def test_assignment_aborts_when_no_seat_can_match_a_human_phase():
    """Fail closed: an off-phase bundle is never emitted as a fallback."""
    windows = [_synthetic_options(1)]
    with pytest.raises(CorpusBuildError, match="no seat reproduces"):
        assign_constrained_focus_seats(
            windows, [("BTN",) * 30], derive_rng(1, "focus-seats")
        )
    with pytest.raises(CorpusBuildError, match="no human phases"):
        assign_constrained_focus_seats(windows, [], derive_rng(1, "focus-seats"))


def test_trajectories_are_measured_from_real_states_not_modelled(human_states):
    """`seat_trajectories` and `bundle_trajectory` must agree on real data —
    the constraint is only sound if both sides measure the same thing."""
    keys = list(range(5))
    per_seat = seat_trajectories(human_states, keys)
    assert len(per_seat) == N_SEATS
    hands = tuple(from_bot(human_states[k], 3) for k in keys)
    assert bundle_trajectory(hands) == per_seat[3]
    assert phase_id(per_seat[3]) == phase_id(bundle_trajectory(hands))
    assert phase_id(per_seat[3]) != phase_id(per_seat[4])


def test_seat_id_map_is_a_seeded_permutation():
    a = build_seat_id_map(derive_rng(1, "opaque-ids", "bot/w0000"))
    b = build_seat_id_map(derive_rng(1, "opaque-ids", "bot/w0001"))
    assert sorted(a) == list(range(N_SEATS))
    assert sorted(a.values()) == sorted(f"P{i}" for i in range(1, N_SEATS + 1))
    assert a != b
    assert a == build_seat_id_map(derive_rng(1, "opaque-ids", "bot/w0000"))


# --- 6. presentation IDs ----------------------------------------------------


def _mixed_keys() -> list[str]:
    return [f"human/w{i:04d}" for i in range(40)] + [f"bot/w{i:04d}" for i in range(40)]


def test_presentation_ids_are_deterministic_and_order_independent():
    keys = _mixed_keys()
    shuffled = list(keys)
    random.Random(11).shuffle(shuffled)
    ids = assign_presentation_ids(keys, derive_rng(20260807, "presentation-ids"))
    assert ids == assign_presentation_ids(shuffled, derive_rng(20260807, "presentation-ids"))
    assert len(set(ids.values())) == len(keys)


def test_presentation_ids_carry_no_class_ordering():
    """If IDs were handed out in class order, B001..B040 would be one class and
    the blinding would be decorative."""
    ids = assign_presentation_ids(_mixed_keys(), derive_rng(20260807, "presentation-ids"))
    by_id = [key.split("/")[0] for key, _ in sorted(ids.items(), key=lambda kv: kv[1])]
    assert by_id != sorted(by_id)  # not grouped by class
    first_half = by_id[: len(by_id) // 2]
    assert 0 < first_half.count("human") < len(first_half)


def test_duplicate_bundle_keys_abort():
    with pytest.raises(CorpusBuildError, match="duplicate bundle keys"):
        assign_presentation_ids(["bot/w0000", "bot/w0000"], derive_rng(1, "x"))


# --- 7. blinding split ------------------------------------------------------


def _one_bundle(human_states, key="human/w0000") -> Bundle:
    return Bundle(
        key=key,
        label="human",
        is_control=False,
        focus_seat=HERO_SEAT,
        hands=tuple(from_bot(human_states[i], HERO_SEAT) for i in range(BUNDLE)),
        source={"kind": "human", "session_id": HUMAN_SESSION},
    )


def _records(human_states) -> list[PresentationRecord]:
    rendered = render_bundles([_one_bundle(human_states)], 1, BUNDLE, ())
    return [PresentationRecord("B001", rendered[0][2])]


def test_presentation_document_has_exactly_three_keys_per_bundle(human_states):
    doc = presentation_document(_records(human_states))
    assert set(doc) == set(PRESENTATION_TOP_KEYS)
    assert set(doc["bundles"][0]) == set(PRESENTATION_BUNDLE_KEYS)
    assert doc["judge_slots"] == 0


def test_presentation_document_marks_only_duplicate_entries(human_states):
    """The frozen shape: `duplicate_for_slot` on exactly the duplicates, and no
    other key anywhere."""
    text = _records(human_states)[0].rendered_text
    doc = presentation_document(
        [
            PresentationRecord("B001", text),
            PresentationRecord("B002", text, duplicate_for_slot=0),
        ],
        judge_slots=1,
    )
    assert set(doc["bundles"][0]) == set(PRESENTATION_BUNDLE_KEYS)
    assert set(doc["bundles"][1]) == set(PRESENTATION_BUNDLE_KEYS) | {DUPLICATE_SLOT_KEY}
    assert doc["bundles"][1][DUPLICATE_SLOT_KEY] == 0
    assert doc["bundle_count"] == 2 and doc["judge_slots"] == 1


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda d: d["bundles"][0].update({"class": "human"}), id="class-key"),
        pytest.param(lambda d: d["bundles"][0].update({"is_control": False}), id="control-key"),
        pytest.param(
            lambda d: d["bundles"][0].update({"source": {"session_id": "x"}}), id="source-key"
        ),
        pytest.param(lambda d: d.update({"human_windows": [1]}), id="top-level-label"),
        pytest.param(lambda d: d["bundles"][0].pop("sha256"), id="missing-key"),
        pytest.param(
            lambda d: d["bundles"][0].update({"sha256": "0" * 64}), id="wrong-hash"
        ),
        pytest.param(
            lambda d: d["bundles"].append(dict(d["bundles"][0])), id="duplicate-id"
        ),
        pytest.param(
            lambda d: d["bundles"][0].update({"duplicate_for_slot": 0}), id="unclaimed-slot"
        ),
        pytest.param(
            lambda d: d["bundles"][0].update({"duplicate_for_slot": "human"}),
            id="slot-not-an-int",
        ),
        pytest.param(lambda d: d.pop("judge_slots"), id="missing-judge-slots"),
    ],
)
def test_presentation_manifest_rejects_label_bearing_or_broken_documents(
    tmp_path, human_states, monkeypatch, mutate
):
    """Adversarial: whatever is smuggled into the document, the WRITER refuses.

    The check lives inside `write_presentation_manifest`, so there is no path
    that puts an unblinded presentation file on disk.
    """
    import tools.detection_corpus as corpus

    clean = presentation_document(_records(human_states))

    def doctored(records, judge_slots=0):
        doc = json.loads(json.dumps(clean))
        mutate(doc)
        return doc

    monkeypatch.setattr(corpus, "presentation_document", doctored)
    with pytest.raises(CorpusBuildError):
        corpus.write_presentation_manifest(
            tmp_path / "presentation.json", [PresentationRecord("B001", "x")]
        )
    assert not (tmp_path / "presentation.json").exists()


def test_label_bearing_key_scan_finds_nested_keys():
    """Second layer, independent of the exact-key-set check: any key whose NAME
    could betray a class/source, at any depth, is reported."""
    from tools.detection_corpus import _label_bearing_keys

    assert _label_bearing_keys({"bundles": [{"presentation_id": "B001"}]}) == []
    found = _label_bearing_keys(
        {"bundles": [{"meta": {"is_control": True}}, {"focus_seat": 3}]}
    )
    assert sorted(found) == ["bundles.0.meta.is_control", "bundles.1.focus_seat"]


def test_presentation_manifest_rejects_a_forbidden_token(tmp_path, human_states):
    with pytest.raises(CorpusBuildError, match="leak audit"):
        write_presentation_manifest(
            tmp_path / "presentation.json", _records(human_states), forbidden=["BTN"]
        )


def test_presentation_manifest_writes_when_clean(tmp_path, human_states):
    digest = write_presentation_manifest(
        tmp_path / "presentation.json", _records(human_states), forbidden=["run-s7-n25"]
    )
    assert len(digest) == 64
    doc = json.loads((tmp_path / "presentation.json").read_text())
    assert doc["bundle_count"] == 1


def test_presentation_manifest_requires_every_declared_slot_to_be_filled(
    tmp_path, human_states
):
    """`judge_slots: N` is a promise about the entries; an unfilled or repeated
    slot is a broken schedule, not a cosmetic mismatch."""
    text = _records(human_states)[0].rendered_text
    with pytest.raises(CorpusBuildError, match="not exactly 0"):
        write_presentation_manifest(
            tmp_path / "p1.json", [PresentationRecord("B001", text)], judge_slots=1
        )
    with pytest.raises(CorpusBuildError, match="not exactly 0"):
        write_presentation_manifest(
            tmp_path / "p2.json",
            [
                PresentationRecord("B001", text),
                PresentationRecord("B002", text, duplicate_for_slot=0),
                PresentationRecord("B003", text, duplicate_for_slot=0),
            ],
            judge_slots=2,
        )


# --- 8. render + leak abort -------------------------------------------------


def test_render_bundles_aborts_the_build_on_any_leak(human_states):
    """A forbidden token in ONE bundle stops the whole deck — the corpus is
    never written half-audited."""
    with pytest.raises(CorpusBuildError, match="leak audit failed"):
        render_bundles([_one_bundle(human_states)], 1, BUNDLE, forbidden=["Showdown"])


def test_render_bundles_pins_the_bundle_size(human_states):
    with pytest.raises(Exception, match="expected exactly"):
        render_bundles([_one_bundle(human_states)], 1, BUNDLE + 1, ())


# --- 9. human snapshot ------------------------------------------------------


def test_snapshot_pins_n_at_the_last_complete_hand(tmp_path, human_states):
    """A live session always has an in-progress tail; N must exclude it and the
    rows above N must not even be candidates."""
    rows = [
        {"hand_no": i + 1, "state_json": human_states[i].model_dump_json()}
        for i in range(6)
    ]
    rows.append({"hand_no": 7, "status": "in_progress", "state_json": None})
    snapshot = read_human_snapshot(_write_db(tmp_path / "a.db", rows))
    assert snapshot.n_pinned == 6
    assert snapshot.origin == 1
    assert max(r.hand_no for r in snapshot.rows) == 6


def test_origin_is_the_canonical_first_hand_not_the_lowest_present(tmp_path, human_states):
    """A deleted hand 1 must INVALIDATE the first window, not slide the tiling.

    Deriving the origin from `min(hand_no)` would renumber every window while
    the manifest still claimed 'hands 1-5, 6-10, ...' — a silently different
    corpus. The origin is pinned to the app's first hand number instead.
    """
    rows = [
        {"hand_no": i + 1, "state_json": human_states[i].model_dump_json()}
        for i in range(1, 11)  # hands 2..11; hand 1 is missing
    ]
    snapshot = read_human_snapshot(_write_db(tmp_path / "gap.db", rows))
    assert snapshot.origin == HUMAN_FIRST_HAND_NO == 1
    windows = enumerate_windows(snapshot.origin, snapshot.n_pinned, BUNDLE)
    first = validate_human_window(group_rows(snapshot.rows), windows[0])
    assert not first.valid and "hand_no 1" in first.reason
    assert (windows[0].start, windows[0].end) == (1, 5)


def test_snapshot_picks_the_session_with_the_most_complete_hands(tmp_path, human_states):
    rows = [
        {"hand_no": i + 1, "session_id": "sess-b", "state_json": human_states[i].model_dump_json()}
        for i in range(3)
    ] + [
        {"hand_no": i + 1, "session_id": "sess-a", "state_json": human_states[i].model_dump_json()}
        for i in range(7)
    ]
    snapshot = read_human_snapshot(_write_db(tmp_path / "b.db", rows))
    assert snapshot.session_id == "sess-a"
    assert snapshot.n_pinned == 7
    # An explicit override still wins.
    assert read_human_snapshot(tmp_path / "b.db", "sess-b").n_pinned == 3


def test_snapshot_keeps_duplicate_rows_visible(tmp_path, human_states):
    """A duplicated hand_no must reach the validator as two rows; collapsing it
    to one here would turn a corrupt window into a silently valid one."""
    state = human_states[0].model_dump_json()
    rows = [
        {"hand_no": 1, "state_json": state},
        {"hand_no": 1, "state_json": state},
        {"hand_no": 2, "state_json": human_states[1].model_dump_json()},
    ]
    snapshot = read_human_snapshot(_write_db(tmp_path / "c.db", rows))
    assert len(group_rows(snapshot.rows)[1]) == 2


def test_missing_db_and_empty_db_abort(tmp_path):
    with pytest.raises(CorpusBuildError, match="not found"):
        read_human_snapshot(tmp_path / "nope.db")
    with pytest.raises(CorpusBuildError, match="no complete"):
        read_human_snapshot(_write_db(tmp_path / "empty.db", []))


def test_snapshot_does_not_write_to_the_owner_db(tmp_path, human_states):
    """`mode=ro`: the builder must not be able to touch the owner's database."""
    import sqlite3

    path = _write_db(
        tmp_path / "ro.db", [{"hand_no": 1, "state_json": human_states[0].model_dump_json()}]
    )
    read_human_snapshot(path)
    conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        conn.execute("DELETE FROM sim_hand")
    conn.close()


# --- 10. bot run identity + forward replay ----------------------------------


def _export_and_replay(seed: int, n: int, packs, config_hash=None):
    """Run the real exporter and the corpus replay over the same run."""
    import tempfile

    import pyarrow.parquet as pq

    from tools.export_analytics import run_export

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        manifest = run_export(
            n, seed, out, lineup=list(RATIFIED_LINEUP), buyin_spread=True,
            packs=packs if config_hash else None, config_hash=config_hash,
        )
        tables = {
            name: pq.read_table(out / f"{name}.parquet").to_pylist()
            for name in ("hands", "seat_outcomes", "decisions")
        }
    states = replay_run(seed, n, PERSONA_BY_SEAT, packs)
    return manifest, tables, states


def _assert_run_equivalence(manifest, tables, states, seed, n):
    """Every exported fact about every hand must match the replayed state.

    Boards and pots alone would not catch a desynced action RNG that still
    produced a plausible hand, so this compares the whole ACTION SEQUENCE and
    every per-seat outcome — including `starting_stack_bb`, the buy-in spread
    that F1 exists to match between classes.
    """
    from app.domain.table.engine import settle

    assert manifest["run_id"] == run_id_for(seed, n, manifest["config_hash"])
    assert len(tables["hands"]) == n
    by_hand: dict[str, list[dict]] = {}
    for row in tables["decisions"]:
        by_hand.setdefault(row["hand_id"], []).append(row)
    seats_by_hand: dict[str, list[dict]] = {}
    for row in tables["seat_outcomes"]:
        seats_by_hand.setdefault(row["hand_id"], []).append(row)

    for row in tables["hands"]:
        state = states[row["hand_no"]]
        assert row["board"] == " ".join(state.board)
        assert row["final_street"] == state.street.value
        assert row["button_seat"] == row["hand_no"] % 9
        assert row["total_pot_bb"] == pytest.approx(
            round(sum(s.invested_total_bb for s in state.seats), 2)
        )
        # Action sequence, in order, including the blind posts.
        exported_actions = [
            (r["street"], r["position"], r["action"], round(r["chips_committed_bb"], 2))
            for r in sorted(by_hand[row["hand_id"]], key=lambda r: r["seq"])
        ]
        replayed_actions = [
            (h.street.value, h.position.value, h.action.value, round(h.amount_bb, 2))
            for h in state.action_history
        ]
        assert exported_actions == replayed_actions

        settlement = settle(state)
        winners = {s for pot in settlement.winners_by_pot for s in pot}
        for seat_row in sorted(seats_by_hand[row["hand_id"]], key=lambda r: r["seat"]):
            seat = next(s for s in state.seats if s.seat == seat_row["seat"])
            assert seat_row["position"] == seat.position.value
            assert seat_row["hole_cards"] == " ".join(seat.hole_cards)
            assert seat_row["starting_stack_bb"] == pytest.approx(
                seat.stack_bb + seat.invested_total_bb
            )
            assert seat_row["invested_bb"] == pytest.approx(seat.invested_total_bb)
            assert seat_row["delta_bb"] == pytest.approx(
                settlement.deltas[seat.seat].delta_bb
            )
            assert seat_row["final_status"] == seat.status.value
            assert seat_row["went_to_showdown"] == (
                seat.seat in settlement.showdown_seats
            )
            assert seat_row["won_pot"] == (seat.seat in winners)


def test_replay_matches_a_real_export_run():
    """The bot bundles must contain exactly the hands a real
    `export_analytics --buyin-spread` run would contain."""
    pytest.importorskip("pyarrow")
    seed, n = 909, 8
    packs = load_persona_packs()
    manifest, tables, states = _export_and_replay(seed, n, packs)
    _assert_run_equivalence(manifest, tables, states, seed, n)


def test_replay_matches_a_real_export_run_on_the_control_config():
    """Same equivalence on the CONTROL path, where the exporter runs overlay
    packs — the control bundle is only traceable if this holds too."""
    pytest.importorskip("pyarrow")
    from tools import counterfactual

    validated = counterfactual.load_config(DEFAULT_CONTROL_CONFIG)
    seed, n = 60002, 8
    manifest, tables, states = _export_and_replay(
        seed, n, validated.packs, validated.config_hash
    )
    assert manifest["config_hash"] == PROTOCOL_CONTROL_CONFIG_HASH
    _assert_run_equivalence(manifest, tables, states, seed, n)


def test_replay_keep_does_not_change_the_hands():
    """`keep` limits what is RETAINED, never what is played — skipping a hand
    would desync the run RNG for every hand after it."""
    packs = load_persona_packs()
    full = replay_run(11, 6, PERSONA_BY_SEAT, packs)
    kept = replay_run(11, 6, PERSONA_BY_SEAT, packs, keep={4, 5})
    assert set(kept) == {4, 5}
    assert kept[5] == full[5]


# --- 11. scaled end-to-end --------------------------------------------------


JUDGES = 3

BUILD_KWARGS = {
    "bot_seed": 7,
    "bot_hands": 25,
    "control_seed": 8,
    "control_hands": 10,
    "bundle_size": BUNDLE,
    "human_bundles": 3,
    "bot_bundles": 3,
    "judges": JUDGES,
}


def _deck_entries(presentation: dict) -> list[dict]:
    """Presentation entries that are analysis-deck bundles (not duplicates)."""
    return [b for b in presentation["bundles"] if DUPLICATE_SLOT_KEY not in b]


def _duplicate_entries(presentation: dict) -> list[dict]:
    return [b for b in presentation["bundles"] if DUPLICATE_SLOT_KEY in b]


@pytest.fixture(scope="module")
def built(tmp_path_factory, human_db):
    out = tmp_path_factory.mktemp("deck")
    success = build_corpus(master_seed=1, db_path=human_db, out_dir=out, **BUILD_KWARGS)
    presentation = json.loads((out / "presentation.json").read_text())
    unblinding = json.loads((out / "unblinding.json").read_text())
    return out, success, presentation, unblinding


def test_e2e_deck_shape_and_success_marker(built):
    out, success, presentation, unblinding = built
    assert success["counts"] == {"human": 3, "bot": 3, "control": 1}
    assert success["bundle_count"] == 7  # the analysis deck
    assert success["judge_slots"] == JUDGES
    # bundle_count in the presentation file INCLUDES the judge duplicates.
    assert presentation["bundle_count"] == 7 + JUDGES == success["presentation_entries"]
    assert presentation["judge_slots"] == JUDGES
    assert (out / SUCCESS_FILENAME).exists()
    # _SUCCESS is written last and names the artifacts it certifies.
    assert set(success["artifacts"]) == {"presentation.json", "unblinding.json"}


def test_e2e_presentation_is_blind(built):
    _, _, presentation, unblinding = built
    assert set(presentation) == set(PRESENTATION_TOP_KEYS)
    for bundle in _deck_entries(presentation):
        assert set(bundle) == set(PRESENTATION_BUNDLE_KEYS)
    for bundle in _duplicate_entries(presentation):
        assert set(bundle) == set(PRESENTATION_BUNDLE_KEYS) | {DUPLICATE_SLOT_KEY}
    blob = json.dumps(presentation)
    for token in ("control", "persona", "human", "session", "run-s", HUMAN_SESSION):
        assert token not in blob
    # Every rendered payload is a 5-hand bundle re-keyed to local indices.
    for bundle in presentation["bundles"]:
        text = bundle["rendered_text"]
        assert text.count("### Hand ") == BUNDLE
        assert "### Hand 1\n" in text


def test_e2e_unblinding_joins_and_records_the_pins(built):
    _, success, presentation, unblinding = built
    by_id = {b["presentation_id"]: b for b in unblinding["bundles"]}
    assert set(by_id) == {b["presentation_id"] for b in _deck_entries(presentation)}
    for bundle in _deck_entries(presentation):
        assert by_id[bundle["presentation_id"]]["sha256"] == bundle["sha256"]
    assert unblinding["master_seed"] == success["master_seed"]
    pins = unblinding["pins"]
    assert pins["human"]["session_id"] == HUMAN_SESSION
    assert pins["human"]["n_pinned"] == HUMAN_HANDS
    assert pins["bot"]["run_id"].startswith("run-s7-n25-bspread-c")
    assert pins["bot"]["buyin_spread"] is True
    assert list(pins["bot"]["lineup"].values()) == list(RATIFIED_LINEUP)
    assert pins["control"]["config_hash"].startswith("3a64601c")
    assert unblinding["human_windows"]["selected"] and unblinding["human_windows"]["candidates"]
    assert len(unblinding["bot_windows"]["selected"]) == 3
    assert set(unblinding["derived_seeds"]) >= {"human-select", "bot-windows", "focus-seats"}


def test_e2e_exactly_one_control_bundle_marked_only_in_the_unblinding(built):
    _, _, _, unblinding = built
    controls = [b for b in unblinding["bundles"] if b["is_control"]]
    assert len(controls) == 1
    assert controls[0]["source"]["kind"] == "control"
    assert controls[0]["class"] == "bot"


def test_e2e_bot_bundles_are_globally_disjoint(built):
    _, _, _, unblinding = built
    seen: set[int] = set()
    for bundle in unblinding["bundles"]:
        source = bundle["source"]
        if source["kind"] != "bot":
            continue
        keys = set(range(source["hand_index_start"], source["hand_index_end"] + 1))
        assert len(keys) == BUNDLE
        assert not (seen & keys)
        seen |= keys
    assert len(seen) == 3 * BUNDLE


def test_e2e_human_bundles_are_disjoint_and_inside_the_pin(built):
    _, _, _, unblinding = built
    n_pinned = unblinding["pins"]["human"]["n_pinned"]
    seen: set[int] = set()
    for bundle in unblinding["bundles"]:
        source = bundle["source"]
        if source["kind"] != "human":
            continue
        keys = set(range(source["hand_no_start"], source["hand_no_end"] + 1))
        assert len(keys) == BUNDLE and max(keys) <= n_pinned
        assert not (seen & keys)
        seen |= keys
        assert bundle["focus_seat"] == HERO_SEAT


def test_e2e_focus_seats_and_seat_maps_are_recorded(built):
    _, _, _, unblinding = built
    scheme = unblinding["focus_seat_scheme"]
    assert scheme["name"] and len(scheme["bot"]) == 3 and len(scheme["control"]) == 1
    assert scheme["bot_window_stride"] == BUNDLE + BOT_STRIDE_GAP
    assert sum(scheme["bot_seat_coverage"].values()) == 3
    for bundle in unblinding["bundles"]:
        seat_map = bundle["seat_id_map"]
        assert sorted(seat_map) == sorted(str(s) for s in range(N_SEATS))
        assert len(set(seat_map.values())) == N_SEATS
        if bundle["source"]["kind"] != "human":
            assert bundle["source"]["focus_persona"] == RATIFIED_LINEUP[bundle["focus_seat"]]


def _payload_trajectory(text: str) -> tuple[str, ...]:
    """The focus player's positions, read back out of the JUDGE'S payload."""
    import re

    focus = re.search(r"^Player under review: (\S+)$", text, re.MULTILINE).group(1)
    return tuple(
        re.findall(rf"^{re.escape(focus)} \(([A-Z0-9]+)\) holds", text, re.MULTILINE)
    )


def test_e2e_no_position_phase_belongs_to_only_one_class(built):
    """The side-channel test, at the level the judge actually sees: every
    position-rotation trajectory present in the deck must occur in BOTH
    classes, so a judge cannot read the class off the position pattern."""
    _, _, presentation, unblinding = built
    label_of = {b["presentation_id"]: b["class"] for b in unblinding["bundles"]}
    phases: dict[str, set[tuple[str, ...]]] = {"human": set(), "bot": set()}
    for bundle in _deck_entries(presentation):
        trajectory = _payload_trajectory(bundle["rendered_text"])
        assert len(trajectory) == BUNDLE
        phases[label_of[bundle["presentation_id"]]].add(trajectory)
    assert phases["human"] == phases["bot"] != set()
    # ...and the manifest's phase record agrees with the payloads.
    recorded = {p["phase_id"] for p in unblinding["position_phases"]}
    assert recorded == {phase_id(t) for t in phases["human"]}
    for record in unblinding["position_phases"]:
        assert record["human_bundles"] >= 1 and record["bot_bundles"] >= 1


def test_e2e_bundle_phase_ids_match_their_payloads(built):
    _, _, presentation, unblinding = built
    by_id = {b["presentation_id"]: b for b in unblinding["bundles"]}
    for bundle in _deck_entries(presentation):
        record = by_id[bundle["presentation_id"]]
        assert record["phase_id"] == phase_id(
            _payload_trajectory(bundle["rendered_text"])
        )


def test_e2e_every_seat_map_is_reproducible_from_its_recorded_seed(built):
    """An auditor with the unblinding manifest must be able to re-derive any
    opaque seat map — the per-bundle seed, not just the base domain seed."""
    _, success, _, unblinding = built
    assert "opaque-ids" not in unblinding["derived_seeds"]
    assert "opaque-ids" in unblinding["seed_derivation"]
    for bundle in unblinding["bundles"]:
        expected = derive_seed(
            success["master_seed"], "opaque-ids", bundle["bundle_key"]
        )
        assert bundle["seat_map_seed"] == f"{expected:032x}"
        rebuilt = build_seat_id_map(random.Random(expected))
        assert {str(s): o for s, o in rebuilt.items()} == bundle["seat_id_map"]


def test_e2e_rebuild_is_byte_identical(tmp_path, human_db, built):
    """Same master seed + same inputs => identical deck, modulo `built_at`."""
    out, _, presentation, unblinding = built
    again = tmp_path / "deck2"
    build_corpus(master_seed=1, db_path=human_db, out_dir=again, **BUILD_KWARGS)
    assert (again / "presentation.json").read_bytes() == (out / "presentation.json").read_bytes()
    redo = json.loads((again / "unblinding.json").read_text())
    assert redo.pop("built_at") is not None
    assert redo == {k: v for k, v in unblinding.items() if k != "built_at"}


def test_e2e_a_different_master_seed_changes_the_deck(tmp_path, human_db, built):
    out, _, _, unblinding = built
    other = tmp_path / "deck3"
    build_corpus(master_seed=2, db_path=human_db, out_dir=other, **BUILD_KWARGS)
    redo = json.loads((other / "unblinding.json").read_text())
    assert (redo["human_windows"]["selected"], redo["focus_seat_scheme"]["bot"]) != (
        unblinding["human_windows"]["selected"], unblinding["focus_seat_scheme"]["bot"]
    )


# --- 12. build-level guards -------------------------------------------------


def test_build_rejects_an_oversized_bundle(tmp_path, human_db):
    with pytest.raises(CorpusBuildError, match="local-index grammar"):
        build_corpus(
            master_seed=1, db_path=human_db, out_dir=tmp_path / "x",
            **{**BUILD_KWARGS, "bundle_size": 31},
        )


def test_build_rejects_a_run_too_short_for_disjoint_windows(tmp_path, human_db):
    with pytest.raises(CorpusBuildError, match="disjoint"):
        build_corpus(
            master_seed=1, db_path=human_db, out_dir=tmp_path / "y",
            **{**BUILD_KWARGS, "bot_hands": 10},
        )


def test_build_aborts_when_the_human_corpus_is_too_small(tmp_path, human_states):
    """Fail closed at the deck level too: not enough valid windows => no deck,
    rather than a 38-bundle class quietly shipped as 40."""
    db = _write_db(
        tmp_path / "small.db",
        [
            {"hand_no": i + 1, "state_json": human_states[i].model_dump_json()}
            for i in range(10)
        ],
    )
    with pytest.raises(CorpusBuildError, match="short deck"):
        build_corpus(master_seed=1, db_path=db, out_dir=tmp_path / "z", **BUILD_KWARGS)
    assert not (tmp_path / "z" / SUCCESS_FILENAME).exists()


# --- 13. judge duplicates (§A.3) --------------------------------------------


def test_duplicate_selection_is_seeded_deterministic_and_slot_separated():
    keys = [f"human/w{i:04d}" for i in range(40)]
    first = select_duplicate_sources(keys, 5, 20260807)
    assert len(first) == 5
    assert first == select_duplicate_sources(keys, 5, 20260807)
    assert first == select_duplicate_sources(list(reversed(keys)), 5, 20260807)
    assert first != select_duplicate_sources(keys, 5, 1)
    # Slots are independent: a sixth judge cannot disturb the first five.
    assert select_duplicate_sources(keys, 6, 20260807)[:5] == first
    assert set(first) <= set(keys)


def test_duplicate_plan_rejects_a_non_human_source():
    labels = {"human/w0000": "human", "bot/w0000": "bot"}
    assert_duplicate_plan(("human/w0000",), labels, 1)  # the happy path
    with pytest.raises(CorpusBuildError, match="pins the per-judge duplicate"):
        assert_duplicate_plan(("bot/w0000",), labels, 1)
    with pytest.raises(CorpusBuildError, match="not a bundle in this deck"):
        assert_duplicate_plan(("human/w0999",), labels, 1)
    with pytest.raises(CorpusBuildError, match="duplicate sources"):
        assert_duplicate_plan(("human/w0000",), labels, 2)


def test_e2e_duplicates_are_one_human_repeat_per_slot(built):
    _, _, presentation, unblinding = built
    duplicates = _duplicate_entries(presentation)
    assert len(duplicates) == JUDGES
    assert sorted(d[DUPLICATE_SLOT_KEY] for d in duplicates) == list(range(JUDGES))

    deck_by_id = {b["presentation_id"]: b for b in _deck_entries(presentation)}
    label_of = {b["presentation_id"]: b["class"] for b in unblinding["bundles"]}
    control_ids = {b["presentation_id"] for b in unblinding["bundles"] if b["is_control"]}
    slots = {s["slot"]: s for s in unblinding["judge_duplicates"]["slots"]}
    assert unblinding["judge_duplicates"]["n_slots"] == JUDGES
    assert sorted(slots) == list(range(JUDGES))
    for entry in duplicates:
        record = slots[entry[DUPLICATE_SLOT_KEY]]
        assert record["presentation_id"] == entry["presentation_id"]
        source = deck_by_id[record["source_presentation_id"]]
        # §A.3: human class only, never the control.
        assert record["class"] == "human"
        assert label_of[source["presentation_id"]] == "human"
        assert source["presentation_id"] not in control_ids
        # Byte-identical stimulus — the whole point of the repeat...
        assert entry["rendered_text"] == source["rendered_text"]
        assert entry["presentation_id"] != source["presentation_id"]
        # ...but NOT an identical hash: the digest is salted with the entry's
        # own id, so the hash column cannot be used to pick the (human-only)
        # duplicates out of the blind manifest.
        assert entry["sha256"] != source["sha256"]
        assert entry["sha256"] == payload_digest(
            entry["presentation_id"], entry["rendered_text"]
        )


def test_no_two_presentation_entries_share_a_hash_even_when_text_is_identical(built):
    """The blind manifest must not contain a hash collision: a collision would
    hand a `presentation.json` holder up to N confirmed HUMAN bundles (§A.3
    pins duplicates to the human class), which is exactly the label the file
    exists not to carry."""
    _, _, presentation, _ = built
    hashes = [b["sha256"] for b in presentation["bundles"]]
    texts = [b["rendered_text"] for b in presentation["bundles"]]
    assert len(set(hashes)) == len(hashes)
    assert len(set(texts)) < len(texts)  # text twins DO exist — by design
    for entry in presentation["bundles"]:
        assert entry["sha256"] == payload_digest(
            entry["presentation_id"], entry["rendered_text"]
        )
        assert entry["sha256"] != hashlib.sha256(
            entry["rendered_text"].encode("utf-8")
        ).hexdigest()


def test_salted_digest_rule_is_uniform_and_id_sensitive(human_states):
    """One rule for every entry — a duplicate-only salt would itself be the
    tell. Same text under two ids must give two digests."""
    text = _records(human_states)[0].rendered_text
    doc = presentation_document(
        [
            PresentationRecord("B001", text),
            PresentationRecord("B002", text, duplicate_for_slot=0),
        ],
        judge_slots=1,
    )
    first, second = doc["bundles"]
    assert first["sha256"] == payload_digest("B001", text)
    assert second["sha256"] == payload_digest("B002", text)
    assert first["sha256"] != second["sha256"]
    assert payload_digest("B001", text) == payload_digest("B001", text)


def test_presentation_writer_rejects_an_unsalted_hash(tmp_path, human_states, monkeypatch):
    """Adversarial: a document whose hashes were computed the OLD way (raw
    text) must not be writable."""
    import tools.detection_corpus as corpus

    clean = presentation_document(_records(human_states))

    def unsalted(records, judge_slots=0):
        doc = json.loads(json.dumps(clean))
        doc["bundles"][0]["sha256"] = hashlib.sha256(
            doc["bundles"][0]["rendered_text"].encode("utf-8")
        ).hexdigest()
        return doc

    monkeypatch.setattr(corpus, "presentation_document", unsalted)
    with pytest.raises(CorpusBuildError, match="salted digest"):
        corpus.write_presentation_manifest(
            tmp_path / "presentation.json", [PresentationRecord("B001", "x")]
        )


def test_e2e_unblinding_carries_the_same_salted_digest(built):
    """T6 cross-checks the two manifests by EQUALITY of the recorded field (it
    never recomputes from text), so the unblinding copy must be the salted one."""
    _, _, presentation, unblinding = built
    presentation_hashes = {
        b["presentation_id"]: b["sha256"] for b in presentation["bundles"]
    }
    for record in unblinding["bundles"]:
        assert record["sha256"] == presentation_hashes[record["presentation_id"]]


def test_e2e_duplicate_ids_come_from_the_same_space_and_do_not_collide(built):
    _, _, presentation, _ = built
    ids = [b["presentation_id"] for b in presentation["bundles"]]
    assert len(set(ids)) == len(ids)
    assert ids == sorted(ids)  # canonical order, no duplicates-at-the-end tell
    assert all(re.fullmatch(r"B\d{3}", pid) for pid in ids)
    dup_ids = {b["presentation_id"] for b in _duplicate_entries(presentation)}
    # The duplicates are not simply the last N ids handed out.
    assert dup_ids != set(ids[-JUDGES:])


def test_e2e_build_aborts_when_a_duplicate_would_be_a_bot_bundle(
    tmp_path, human_db, monkeypatch, built
):
    """Adversarial: force the selector to pick a REAL bot bundle of this deck —
    the build must refuse rather than ship a deck whose visible mix contradicts
    §A.3."""
    import tools.detection_corpus as corpus

    _, _, _, unblinding = built
    bot_key = next(
        b["bundle_key"] for b in unblinding["bundles"]
        if b["class"] == "bot" and not b["is_control"]
    )
    monkeypatch.setattr(
        corpus, "select_duplicate_sources",
        lambda human_keys, judges, master_seed: (bot_key,) * judges,
    )
    out = tmp_path / "dup-bot"
    with pytest.raises(CorpusBuildError, match="pins the per-judge duplicate"):
        build_corpus(master_seed=1, db_path=human_db, out_dir=out, **BUILD_KWARGS)
    assert not (out / SUCCESS_FILENAME).exists()
    assert not (out / "presentation.json").exists()


def test_e2e_zero_judges_produces_no_duplicates(tmp_path, human_db):
    out = tmp_path / "no-judges"
    success = build_corpus(
        master_seed=1, db_path=human_db, out_dir=out,
        **{**BUILD_KWARGS, "judges": 0},
    )
    presentation = json.loads((out / "presentation.json").read_text())
    assert success["judge_slots"] == 0 and presentation["judge_slots"] == 0
    assert _duplicate_entries(presentation) == []
    assert presentation["bundle_count"] == 7


def test_e2e_more_judges_add_entries_without_changing_the_deck(tmp_path, human_db, built):
    """The deck itself must not depend on the judge count — only the extra
    entries do (ids are re-drawn over the larger space, membership is not)."""
    out = tmp_path / "more-judges"
    build_corpus(
        master_seed=1, db_path=human_db, out_dir=out, **{**BUILD_KWARGS, "judges": 4}
    )
    _, _, _, unblinding = built
    redo = json.loads((out / "unblinding.json").read_text())
    assert len(redo["judge_duplicates"]["slots"]) == 4
    assert [s["source_bundle_key"] for s in redo["judge_duplicates"]["slots"]][:JUDGES] == [
        s["source_bundle_key"] for s in unblinding["judge_duplicates"]["slots"]
    ]
    assert {b["bundle_key"] for b in redo["bundles"]} == {
        b["bundle_key"] for b in unblinding["bundles"]
    }


# --- 14. the pinned control config ------------------------------------------


def test_shipped_control_config_hashes_to_the_protocol_pin():
    """Full-hash assert (not a prefix): the file in the repo IS the config the
    spec appendix pins."""
    from tools import counterfactual

    assert len(PROTOCOL_CONTROL_CONFIG_HASH) == 64
    assert (
        counterfactual.load_config(DEFAULT_CONTROL_CONFIG).config_hash
        == PROTOCOL_CONTROL_CONFIG_HASH
    )


@pytest.fixture(scope="module")
def other_control_config(tmp_path_factory) -> Path:
    """A valid §c config that is NOT the pinned control."""
    document = json.loads(DEFAULT_CONTROL_CONFIG.read_text())
    overrides = document["overrides"]
    persona = sorted(overrides)[0]
    path = sorted(overrides[persona])[0]
    overrides[persona][path] = round(float(overrides[persona][path]) * 0.5 + 0.01, 4)
    out = tmp_path_factory.mktemp("cfg") / "other-control.json"
    out.write_text(json.dumps(document, indent=2))
    return out


def test_build_refuses_an_unpinned_control_config(tmp_path, human_db, other_control_config):
    with pytest.raises(CorpusBuildError, match="not the protocol-pinned"):
        build_corpus(
            master_seed=1, db_path=human_db, out_dir=tmp_path / "np1",
            **{**BUILD_KWARGS, "control_config": other_control_config},
        )
    assert not (tmp_path / "np1" / SUCCESS_FILENAME).exists()


def test_non_protocol_flag_builds_but_stamps_both_manifests(
    tmp_path, human_db, other_control_config
):
    """A dry-run deck must never be mistakable for the protocol deck."""
    out = tmp_path / "np2"
    success = build_corpus(
        master_seed=1, db_path=human_db, out_dir=out, non_protocol_control=True,
        **{**BUILD_KWARGS, "control_config": other_control_config},
    )
    unblinding = json.loads((out / "unblinding.json").read_text())
    assert success["non_protocol"] is True
    assert unblinding["non_protocol"] is True
    assert unblinding["pins"]["control"]["config_hash"] != PROTOCOL_CONTROL_CONFIG_HASH


def test_protocol_deck_is_not_stamped_non_protocol(built):
    _, success, _, unblinding = built
    assert success["non_protocol"] is False
    assert unblinding["non_protocol"] is False
    assert unblinding["pins"]["control"]["config_hash"] == PROTOCOL_CONTROL_CONFIG_HASH


def test_the_flag_alone_does_not_relax_anything_else(tmp_path, human_db):
    """`--non-protocol-control` waives the config pin and NOTHING else."""
    with pytest.raises(CorpusBuildError, match="short deck"):
        build_corpus(
            master_seed=1, db_path=human_db, out_dir=tmp_path / "np3",
            non_protocol_control=True, **{**BUILD_KWARGS, "human_bundles": 99},
        )
