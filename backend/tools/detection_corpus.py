"""Blind-detection corpus builder (flywheel S6 T4) — the deck the judges see.

Assembles the §d-preregistered deck for the S6 detection pilot:

    40 human bundles   one owner Simulate session, consecutive 30-hand windows
    40 bot bundles     one fresh seeded self-play run (--buyin-spread, ratified lineup)
     1 control bundle  a second run under the T1 control config (spec appendix)

and splits it into TWO artifacts (spec `flywheel-s6.md`, "Blinding split"):

    presentation.json  presentation_id + rendered_text + sha256 (salted with
                       the id, see `payload_digest`), and NOTHING else — except
                       `duplicate_for_slot` on the one repeated entry each judge
                       gets (§A.3), which routes an entry to a judge without
                       saying anything about its class
    unblinding.json    class labels, source windows, seat maps, every corpus pin,
                       and which human bundle each judge's duplicate repeats

The judge harness takes only `presentation.json`; nothing in that file names a
class, a seat, a run, a session, or a hand number, and `_assert_presentation_blind`
enforces that at write time rather than by convention (see `write_presentation_manifest`).

Blinding is not only about what the manifest SAYS. Rendered hands name the
focus player's position, so each bundle exposes a position-rotation
trajectory, and the human class can only exhibit a few of the nine phases
(hero is always seat 0; its windows tile by 30 and 30 mod 9 = 3). Bot and
control focus seats are therefore chosen to reproduce the human phase set
measured from the built human bundles, the bot windows are laid down at a
stride coprime to 9 so all nine seats stay reachable under that constraint,
and the build refuses to write a deck whose two classes differ in phase.

Rendering is NOT done here: every bundle goes through the wave-2 renderer
(`tools/detection_render.py`), the single code path both classes share, with
`expected_count` pinned to the bundle size and `leak_check` run on the finished
text. A single leak violation aborts the whole build — the deck is never
written half-audited.

Determinism. One master seed; every purpose draws from its own
`sha256(master || domain)`-derived stream (`derive_rng`), so adding a bundle to
one class cannot shift another class's draws. Candidate enumeration, selection,
focus-seat assignment and presentation-ID assignment all consume canonically
SORTED inputs, so nothing depends on filesystem or dict order. Same master seed
+ same inputs => byte-identical `presentation.json`, and an `unblinding.json`
identical apart from the declared-volatile `built_at`.

Fail closed, everywhere. A human window is valid only if every hand number in
it is present exactly once, complete, and parses through the canonical adapter
with the focus seat dealt; a gap, a duplicate, an in-progress row or a malformed
`state_json` REJECTS the whole window — windows are never repaired by
skip-and-close-ranks, because a bundle whose "consecutive" hands silently skip a
hand is a different object from the one the protocol pins.

Bot hands come from replaying the run FORWARD from its seed
(`replay_run`), not from re-simulating hands individually: `bot_decision` draws
from the run-level RNG whose state depends on every preceding hand, so a hand
cannot be faithfully reproduced from its own `hand_seed`. The loop mirrors
`export_analytics.run_export` exactly (same per-hand seed draw, same button
rotation, same `_draw_buyin_targets` stacks), and `run_id_for` reproduces that
module's run-identity string, so a bundle is traceable to a real export run
without this build having to write Parquet.

Usage (from backend/, as a module — repo convention):

    python -m tools.detection_corpus build \\
        --master-seed 20260807 \\
        --db-path data/poker_coach.db \\
        --out-dir ../docs/ai-dlc/research/persona-realism-artifacts/detection-s6

`build` runs the bot and control self-play itself (no pre-run directory to
point at, and no Parquet is produced or needed). Outputs land under a
gitignored artifacts path — owner hand data and the unblinding manifest are
never committable. `_SUCCESS` is written LAST (S4/Hadoop manifest-committer
convention): its absence means the deck is incomplete, whatever else is there.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from app.domain.archetypes import VillainType
from app.domain.personas import load_persona_packs
from app.domain.table.deck import deal_hand
from app.domain.table.engine import HandState, apply, start_hand
from app.domain.table.play import bot_decision
from tools import counterfactual
from tools.detection_render import (
    MAX_LOCAL_HAND_INDEX,
    CanonicalHand,
    CanonicalHandError,
    from_bot,
    from_human,
    leak_check,
    render_bundle,
)

# `_draw_buyin_targets` and `_git_sha` are imported (rather than re-derived) so
# the corpus can never drift from the exporter's buy-in spread or provenance.
from tools.export_analytics import _draw_buyin_targets, _git_sha

_REPO_ROOT = Path(__file__).resolve().parents[2]

# §d pins: 30-hand bundles, 40 per class, plus one control bundle.
BUNDLE_SIZE = 30
HUMAN_BUNDLES = 40
BOT_BUNDLES = 40
N_SEATS = 9
HERO_SEAT = 0  # `app/services/sim_session.py:120` — the human is always seat 0.
# The live app opens every session at hand_no 1 (`sim_session.py:822`). This is
# the AUTHORITATIVE window origin: deriving it from `min(hand_no)` instead would
# let a deleted hand 1 slide the whole tiling by one hand, quietly producing a
# valid-looking deck of windows that are not the windows the manifest describes.
HUMAN_FIRST_HAND_NO = 1

# The spec's ratified 9-seat lineup for the bot run (seat order 0..8).
RATIFIED_LINEUP: tuple[str, ...] = (
    "tag", "tag", "calling_station", "tag", "passive_fish",
    "lag", "passive_fish", "nit", "maniac",
)

# Pinned run identities (recorded in the unblinding manifest; overridable on the
# CLI only for dry runs). 1500 hands leaves room for 40 windows at the
# phase-walking stride below and still makes the selection a real seeded choice.
BOT_RUN_SEED = 60001
BOT_RUN_HANDS = 1500
CONTROL_RUN_SEED = 60002
CONTROL_RUN_HANDS = 120

DEFAULT_CONTROL_CONFIG = _REPO_ROOT / "docs/ai-dlc/specs/flywheel-s6-control-config.json"
# The T1 control config the protocol pins (spec `flywheel-s6.md`, appendix).
# Building the real deck against anything else is an amendment, not a build.
PROTOCOL_CONTROL_CONFIG_HASH = (
    "3a64601cbe060373d06a93fd7cd285bd6b0d47b58b23c53ad2e1031ef088b3f8"
)
DEFAULT_OUT_DIR = (
    _REPO_ROOT / "docs/ai-dlc/research/persona-realism-artifacts/detection-s6"
)
DEFAULT_DB_PATH = _REPO_ROOT / "backend/data/poker_coach.db"

PRESENTATION_FILENAME = "presentation.json"
UNBLINDING_FILENAME = "unblinding.json"
SUCCESS_FILENAME = "_SUCCESS"
SCHEMA_VERSION = "1.0.0"

# The ONLY keys a presentation-manifest bundle may carry, plus the one optional
# key that appears on exactly the judge-duplicate entries (§A.3). FROZEN — the
# judge harness (T5) is written against this shape.
PRESENTATION_BUNDLE_KEYS = ("presentation_id", "rendered_text", "sha256")
DUPLICATE_SLOT_KEY = "duplicate_for_slot"
PRESENTATION_TOP_KEYS = ("bundle_count", "bundles", "judge_slots", "schema_version")
# §d.2 / owner Gate-1 decision 3: five pinned judge vendors, one duplicate each.
JUDGE_SLOTS = 5
# Substrings that would betray a class, a source, or a seed if they ever
# appeared as a KEY anywhere in the presentation manifest.
_LABEL_KEY_TOKENS = (
    "class", "label", "control", "human", "bot", "persona", "seat", "session",
    "run", "window", "focus", "source", "seed", "hand_no", "config", "villain",
)

FOCUS_SEAT_SCHEME = "human-phase-constrained-balanced-greedy"
# Bot windows are laid down every `bundle_size + BOT_STRIDE_GAP` hands so their
# start rotations walk all nine phases (31 and 9 are coprime); see
# `enumerate_windows` and `assign_constrained_focus_seats`.
BOT_STRIDE_GAP = 1


class CorpusBuildError(RuntimeError):
    """Any condition that must ABORT the build rather than degrade it."""


# ---------------------------------------------------------------------------
# Seeding: one master seed, one stream per purpose
# ---------------------------------------------------------------------------


def derive_seed(master_seed: int, domain: str, *parts: str) -> int:
    """A domain-separated child seed: `sha256(master || domain || parts)`.

    Separate purposes must NOT share an RNG stream — otherwise selecting one
    more human window silently re-rolls the bot windows, the focus seats and
    the presentation order, and "same master seed" stops meaning anything.
    """
    material = "|".join(("s6-detection-corpus", str(master_seed), domain, *parts))
    return int.from_bytes(hashlib.sha256(material.encode("utf-8")).digest()[:16], "big")


def derive_rng(master_seed: int, domain: str, *parts: str) -> random.Random:
    return random.Random(derive_seed(master_seed, domain, *parts))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def payload_digest(presentation_id: str, rendered_text: str) -> str:
    """The per-entry hash: `sha256(presentation_id + "\\n" + rendered_text)`.

    SALTED with the entry's own id, uniformly for every entry. An unsalted
    payload hash would make each judge duplicate collide exactly with its
    source, and since §A.3 pins duplicates to the HUMAN class, anyone holding
    only `presentation.json` could read up to N human bundles straight off the
    hash column — a labelled subset inside the one artifact whose job is to
    carry no labels. The rule is uniform (no duplicate-only special case), so
    the field itself signals nothing about which entries are repeats.

    Residual, accepted: a `presentation.json` holder can still spot text twins
    by comparing `rendered_text` directly. That is inherent to the §d.2
    identical-stimulus design — the duplicate MUST be the same bytes — and the
    judges never see the manifest, only one bundle's text per call.
    """
    return _sha256_text(f"{presentation_id}\n{rendered_text}")


# ---------------------------------------------------------------------------
# Windows: enumeration, validation, selection
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Window:
    """A non-overlapping, consecutive run of `size` hand keys."""

    index: int
    start: int
    end: int

    def keys(self) -> range:
        return range(self.start, self.end + 1)


@dataclass(frozen=True, slots=True)
class WindowCheck:
    window: Window
    valid: bool
    reason: str | None = None
    hands: tuple[CanonicalHand, ...] = ()


def enumerate_windows(
    origin: int, ceiling: int, size: int, stride: int | None = None
) -> tuple[Window, ...]:
    """Lay `size`-hand windows across `[origin, ceiling]`, one every `stride`.

    A trailing partial window is dropped, never padded. `stride` defaults to
    `size` (adjacent tiling — what the human class uses, since its windows are
    just the session cut into consecutive blocks). A LARGER stride leaves gaps
    between bundles, which is how the bot class buys back its position-phase
    freedom: with adjacent 30-hand tiling every window starts on a button
    rotation congruent to 30k (mod 9), so only three of the nine rotation
    phases are reachable and the seats that can satisfy the human-phase
    constraint (see `assign_constrained_focus_seats`) collapse to three. A
    stride coprime to 9 walks the start rotation through all nine phases.
    Bundles stay internally consecutive and globally disjoint either way.
    """
    if size <= 0:
        raise CorpusBuildError(f"window size must be positive, got {size}")
    stride = size if stride is None else stride
    if stride < size:
        raise CorpusBuildError(f"stride {stride} < size {size} would overlap windows")
    windows: list[Window] = []
    start = origin
    while start + size - 1 <= ceiling:
        windows.append(Window(index=len(windows), start=start, end=start + size - 1))
        start += stride
    return tuple(windows)


@dataclass(frozen=True, slots=True)
class HumanHandRow:
    """One `sim_hand` row, reduced to the three columns that decide validity."""

    hand_no: int
    status: str
    state_json: str | None


def validate_human_window(
    rows_by_hand_no: Mapping[int, Sequence[HumanHandRow]],
    window: Window,
    focus_seat: int = HERO_SEAT,
) -> WindowCheck:
    """Fail-closed validity for one human window.

    Every hand number in the window must be present EXACTLY once, marked
    complete, carry a `state_json`, and survive the canonical adapter (which is
    what enforces `hand_over`, nine dealt seats, a consistent ledger and a
    revealed board). The first failure in ascending hand order decides the
    reason; the window is rejected whole — no hand is dropped and the remaining
    hands are never slid up to close the gap.
    """
    hands: list[CanonicalHand] = []
    for hand_no in window.keys():
        rows = rows_by_hand_no.get(hand_no, ())
        if not rows:
            return WindowCheck(window, False, f"hand_no {hand_no} is missing (gap)")
        if len(rows) > 1:
            return WindowCheck(
                window, False, f"hand_no {hand_no} has {len(rows)} rows (duplicate)"
            )
        row = rows[0]
        if row.status != "complete":
            return WindowCheck(
                window, False, f"hand_no {hand_no} status is {row.status!r}, not 'complete'"
            )
        if not row.state_json:
            return WindowCheck(window, False, f"hand_no {hand_no} has no state_json")
        try:
            hands.append(from_human(row.state_json, focus_seat))
        except CanonicalHandError as exc:
            return WindowCheck(window, False, f"hand_no {hand_no} rejected: {exc}")
    return WindowCheck(window, True, None, tuple(hands))


def select_windows(candidate_indices: Iterable[int], k: int, rng: random.Random) -> tuple[int, ...]:
    """Pick EXACTLY `k` window indices from the valid candidates, seeded.

    The pool is canonically sorted before sampling so the choice depends on the
    seed and the candidate SET only — never on the order the candidates were
    discovered in. Too few candidates is a build abort, not a smaller deck.
    """
    pool = sorted(set(candidate_indices))
    if k < 0:
        raise CorpusBuildError(f"cannot select {k} windows")
    if len(pool) < k:
        raise CorpusBuildError(
            f"need {k} valid windows but only {len(pool)} are available — "
            f"refusing to ship a short deck"
        )
    return tuple(sorted(rng.sample(pool, k)))


# ---------------------------------------------------------------------------
# Position-rotation phases — the side channel a key-level audit cannot see
# ---------------------------------------------------------------------------
#
# Every rendered hand names the focus player's POSITION, so a bundle exposes the
# sequence of positions its focus player occupied — its "trajectory". The button
# rotates one seat per hand in both classes, so a trajectory is a rotation phase:
# there are exactly nine of them. The human class can only ever exhibit a few
# (the hero is always seat 0 and its windows tile by 30; 30 mod 9 = 3, so the
# real session yields three phases). Left alone, the bot class would spread over
# all nine — and six phases would occur ONLY in bot bundles, a free answer for
# any judge who noticed. So bot and control focus seats are chosen to reproduce
# the human phase set, and the build refuses to ship a deck whose classes differ
# in phase. Phases are MEASURED from the rendered records of both classes, never
# modeled from an assumed rotation rule.


def bundle_trajectory(hands: Sequence[CanonicalHand]) -> tuple[str, ...]:
    """The focus player's position in each hand — the phase, read from data."""
    return tuple(
        next(seat.position for seat in hand.seats if seat.seat == hand.focus_seat)
        for hand in hands
    )


def seat_trajectories(
    states: Mapping[int, HandState], hand_keys: Iterable[int]
) -> dict[int, tuple[str, ...]]:
    """What the trajectory WOULD be for each candidate focus seat of a window."""
    keys = list(hand_keys)
    return {
        seat: tuple(
            next(s.position.value for s in states[k].seats if s.seat == seat) for k in keys
        )
        for seat in range(N_SEATS)
    }


def phase_id(trajectory: Sequence[str]) -> str:
    """A short stable id for a trajectory (manifests record ids, not 30-tuples)."""
    return hashlib.sha256("|".join(trajectory).encode("utf-8")).hexdigest()[:12]


def assign_constrained_focus_seats(
    options: Sequence[Mapping[int, tuple[str, ...]]],
    allowed_phases: Sequence[tuple[str, ...]],
    rng: random.Random,
) -> tuple[int, ...]:
    """One focus seat per window, restricted to the human-observed phases.

    Scheme (`FOCUS_SEAT_SCHEME`, recorded in the manifest): walk the windows in
    a seeded order and give each the admissible seat that is scarcest so far —
    balancing PHASES first (so every human phase also occurs in the bot class,
    closing the channel in both directions) and seats second, with a seeded
    seat priority breaking the remaining ties.

    Blinding outranks seat coverage: a window with no admissible seat aborts the
    build rather than being handed an off-phase seat, and the caller records
    whichever seat coverage the constraint permitted.
    """
    allowed = set(allowed_phases)
    if not allowed:
        raise CorpusBuildError("no human phases to constrain the bot class to")
    order = list(range(len(options)))
    rng.shuffle(order)
    seat_priority = list(range(N_SEATS))
    rng.shuffle(seat_priority)
    phase_counts: dict[tuple[str, ...], int] = dict.fromkeys(allowed, 0)
    seat_counts: dict[int, int] = dict.fromkeys(range(N_SEATS), 0)
    assignment: list[int | None] = [None] * len(options)
    for index in order:
        admissible = sorted(
            seat for seat, traj in options[index].items() if traj in allowed
        )
        if not admissible:
            raise CorpusBuildError(
                f"window {index}: no seat reproduces any human position phase — "
                f"refusing to ship an off-phase bundle"
            )
        pick = min(
            admissible,
            key=lambda s: (
                phase_counts[options[index][s]], seat_counts[s], seat_priority.index(s)
            ),
        )
        assignment[index] = pick
        phase_counts[options[index][pick]] += 1
        seat_counts[pick] += 1
    return tuple(seat for seat in assignment if seat is not None)


def seat_coverage(assignment: Sequence[int]) -> dict[str, int]:
    """Per-seat bundle counts (seats the constraint excluded are simply absent)."""
    return {str(seat): assignment.count(seat) for seat in sorted(set(assignment))}


def assert_disjoint(windows: Sequence[Window]) -> None:
    """No two bundles may share a hand. Tiling guarantees it; this proves it."""
    seen: set[int] = set()
    for window in windows:
        keys = set(window.keys())
        overlap = seen & keys
        if overlap:
            raise CorpusBuildError(
                f"window {window.index} overlaps earlier windows on {sorted(overlap)[:5]}"
            )
        seen |= keys


def build_seat_id_map(rng: random.Random, n_seats: int = N_SEATS) -> dict[int, str]:
    """Seat index -> opaque label, per bundle, from a seeded shuffle."""
    labels = [f"P{i}" for i in range(1, n_seats + 1)]
    rng.shuffle(labels)
    return {seat: labels[seat] for seat in range(n_seats)}


def assign_presentation_ids(bundle_keys: Iterable[str], rng: random.Random) -> dict[str, str]:
    """Opaque presentation IDs, shuffled across ALL bundles of ALL classes.

    IDs are handed out in shuffled order over the canonically sorted key list,
    so B001..B0NN carry no class ordering (the alternative — numbering human
    bundles first — hands the judge the answer key) and the assignment does not
    depend on the order bundles were built in.
    """
    keys = sorted(bundle_keys)
    if len(set(keys)) != len(keys):
        raise CorpusBuildError("duplicate bundle keys — presentation IDs would collide")
    order = list(keys)
    rng.shuffle(order)
    width = max(3, len(str(len(order))))
    return {key: f"B{i:0{width}d}" for i, key in enumerate(order, start=1)}


# ---------------------------------------------------------------------------
# Human source: one read snapshot, re-pinned at build time
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class HumanSnapshot:
    session_id: str
    n_pinned: int  # N: the largest COMPLETE hand_no at build time
    origin: int  # always HUMAN_FIRST_HAND_NO — the session's canonical first hand
    rows: tuple[HumanHandRow, ...]  # every row with hand_no <= n_pinned


def read_human_snapshot(db_path: Path, session_id: str | None = None) -> HumanSnapshot:
    """Read the owner's hands ONCE, read-only, inside a single transaction.

    One snapshot is the point: the live session keeps playing, so choosing the
    session, pinning N and reading the rows must all see the same database, or
    the manifest's pins describe a corpus that never existed. The connection is
    opened `mode=ro` — this tool must not be able to write to the owner's DB
    even by accident.
    """
    resolved = Path(db_path).resolve()
    if not resolved.exists():
        raise CorpusBuildError(f"human DB not found: {resolved}")
    conn = sqlite3.connect(f"file:{resolved}?mode=ro", uri=True)
    try:
        conn.execute("BEGIN")
        if session_id is None:
            counts = conn.execute(
                "SELECT session_id, COUNT(*) FROM sim_hand "
                "WHERE status = 'complete' GROUP BY session_id"
            ).fetchall()
            if not counts:
                raise CorpusBuildError(f"{resolved}: no complete sim_hand rows")
            session_id = sorted(counts, key=lambda r: (-r[1], r[0]))[0][0]
        raw = conn.execute(
            "SELECT hand_no, status, state_json FROM sim_hand "
            "WHERE session_id = ? ORDER BY hand_no, id",
            (session_id,),
        ).fetchall()
    finally:
        conn.execute("COMMIT")
        conn.close()

    complete = [r for r in raw if r[1] == "complete"]
    if not complete:
        raise CorpusBuildError(f"session {session_id}: no complete hands")
    n_pinned = max(r[0] for r in complete)
    rows = tuple(
        HumanHandRow(hand_no=r[0], status=r[1], state_json=r[2])
        for r in raw
        if r[0] <= n_pinned
    )
    # The origin is the app's canonical first hand number, NOT `min(hand_no)`:
    # if hand 1 were missing, deriving the origin from the data would slide
    # every window by one hand and hide the loss, where the fixed origin makes
    # the window that SHOULD contain hand 1 fail its gap check.
    below = [r.hand_no for r in rows if r.hand_no < HUMAN_FIRST_HAND_NO]
    if below:
        raise CorpusBuildError(
            f"session {session_id}: hand numbers {sorted(set(below))[:5]} are below the "
            f"expected first hand {HUMAN_FIRST_HAND_NO} — the numbering assumption is stale"
        )
    return HumanSnapshot(
        session_id=session_id,
        n_pinned=n_pinned,
        origin=HUMAN_FIRST_HAND_NO,
        rows=rows,
    )


def group_rows(rows: Iterable[HumanHandRow]) -> dict[int, list[HumanHandRow]]:
    """hand_no -> rows. A list, not a row: duplicates must stay VISIBLE so the
    window validator can reject them instead of silently keeping the last one."""
    grouped: dict[int, list[HumanHandRow]] = {}
    for row in rows:
        grouped.setdefault(row.hand_no, []).append(row)
    return grouped


# ---------------------------------------------------------------------------
# Bot source: replay the run forward
# ---------------------------------------------------------------------------


def run_id_for(seed: int, n_hands: int, config_hash: str, buyin_spread: bool = True) -> str:
    """The run identity `export_analytics.run_export` would mint for this run.

    Kept in lockstep with that module's format string (tested), so a corpus
    bundle names a run someone can actually re-export."""
    mode_token = "-bspread" if buyin_spread else ""
    return f"run-s{seed}-n{n_hands}{mode_token}-c{config_hash[:12]}"


def replay_run(
    seed: int,
    n_hands: int,
    persona_by_seat: Mapping[int, str],
    packs: Mapping,
    *,
    buyin_spread: bool = True,
    keep: set[int] | None = None,
) -> dict[int, HandState]:
    """Replay a self-play run forward and return the TERMINAL states.

    Mirrors `export_analytics.run_export`'s loop exactly — one `hand_seed` per
    hand drawn from the run RNG, button rotating `i % 9`, spread stacks from
    `_draw_buyin_targets` — because the bundles must contain the same hands a
    real export of `(seed, n_hands, lineup, config)` would contain. `keep`
    limits what is RETAINED, never what is played: skipping a hand would change
    the RNG state for every hand after it.
    """
    rng = random.Random(seed)
    kept: dict[int, HandState] = {}
    for i in range(n_hands):
        hand_seed = rng.randrange(1_000_000_000)
        stacks = _draw_buyin_targets(hand_seed) if buyin_spread else [100.0] * N_SEATS
        state = start_hand(deal_hand(random.Random(hand_seed)), i % N_SEATS, stacks)
        guard = 0
        while not state.hand_over:
            guard += 1
            if guard > 500:
                raise CorpusBuildError(f"hand {i} did not terminate (seed={hand_seed})")
            seat = state.to_act_seat
            state = apply(state, bot_decision(state, seat, packs[persona_by_seat[seat]], rng))
        if keep is None or i in keep:
            kept[i] = state
    return kept


# ---------------------------------------------------------------------------
# Bundles
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Bundle:
    """One rendered-ready bundle. `key` is the canonical sort/derivation key;
    `source` is the (secret) provenance record and never reaches the renderer."""

    key: str
    label: str  # "human" | "bot"
    is_control: bool
    focus_seat: int
    hands: tuple[CanonicalHand, ...]
    source: dict = field(default_factory=dict)


def render_bundles(
    bundles: Sequence[Bundle],
    master_seed: int,
    bundle_size: int,
    forbidden: Sequence[str],
) -> list[tuple[Bundle, dict[int, str], str]]:
    """Render + leak-audit every bundle, or abort the build.

    `expected_count` is pinned to the bundle size (30 for the real deck), and
    `leak_check` runs on the renderer's own output text — never on a wrapped or
    reformatted copy, because its header-grammar layer keys on the exact
    `### Hand N` lines the renderer emits.
    """
    rendered: list[tuple[Bundle, dict[int, str], str]] = []
    for bundle in sorted(bundles, key=lambda b: b.key):
        seat_id_map = build_seat_id_map(derive_rng(master_seed, "opaque-ids", bundle.key))
        text = render_bundle(
            bundle.hands,
            seat_id_map[bundle.focus_seat],
            seat_id_map,
            expected_count=bundle_size,
        )
        violations = leak_check(text, forbidden=forbidden)
        if violations:
            raise CorpusBuildError(
                f"bundle {bundle.key}: leak audit failed — {violations}"
            )
        rendered.append((bundle, seat_id_map, text))
    return rendered


# ---------------------------------------------------------------------------
# Judge duplicates (§A.3): one repeated bundle per judge, always HUMAN class
# ---------------------------------------------------------------------------


def select_duplicate_sources(
    human_keys: Iterable[str], judges: int, master_seed: int
) -> tuple[str, ...]:
    """Which HUMAN bundle each judge slot sees twice.

    §A.3 pins the duplicate to the human class (a bot duplicate would make the
    judge-visible mix 42/40 and contradict the stated 50/50 base rate), and the
    selection needs labels — which is why it lives here, in the builder that
    has them, and not in the blind harness.

    Slots draw INDEPENDENTLY from their own domain-separated streams
    (`judge-duplicate|<slot>`), so two judges may land on the same bundle and
    adding a sixth judge cannot change the first five. Each judge's within-judge
    consistency is measured against its own repeat, so cross-slot collisions
    cost nothing.
    """
    if judges < 0:
        raise CorpusBuildError(f"judges must be >= 0, got {judges}")
    pool = sorted(human_keys)
    if judges and not pool:
        raise CorpusBuildError("no human bundles to duplicate")
    return tuple(
        derive_rng(master_seed, "judge-duplicate", str(slot)).choice(pool)
        for slot in range(judges)
    )


def assert_duplicate_plan(
    sources: Sequence[str], label_by_key: Mapping[str, str], judges: int
) -> None:
    """Fail closed on any duplicate that is not exactly one human bundle per slot."""
    if len(sources) != judges:
        raise CorpusBuildError(
            f"{len(sources)} duplicate sources for {judges} judge slots"
        )
    for slot, key in enumerate(sources):
        label = label_by_key.get(key)
        if label is None:
            raise CorpusBuildError(f"slot {slot}: {key!r} is not a bundle in this deck")
        if label != "human":
            raise CorpusBuildError(
                f"slot {slot}: duplicate source {key!r} is class {label!r} — "
                f"§A.3 pins the per-judge duplicate to the HUMAN class"
            )


def duplicate_key(slot: int) -> str:
    return f"duplicate/slot{slot:02d}"


# ---------------------------------------------------------------------------
# Blinding split
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PresentationRecord:
    """One judge-facing entry: an opaque id, the rendered text, and — only on a
    judge duplicate — the slot it is routed to."""

    presentation_id: str
    rendered_text: str
    duplicate_for_slot: int | None = None


def _label_bearing_keys(document: object, path: str = "") -> list[str]:
    """Every key anywhere in `document` whose NAME could betray a label."""
    found: list[str] = []
    if isinstance(document, Mapping):
        for key, value in document.items():
            lowered = str(key).lower()
            if any(token in lowered for token in _LABEL_KEY_TOKENS):
                found.append(f"{path}{key}")
            found.extend(_label_bearing_keys(value, f"{path}{key}."))
    elif isinstance(document, (list, tuple)):
        for i, value in enumerate(document):
            found.extend(_label_bearing_keys(value, f"{path}{i}."))
    return found


def _assert_presentation_blind(document: Mapping, forbidden: Sequence[str] = ()) -> None:
    """Schema-level guarantee that the judge-facing file carries no answer key.

    Checked structurally (exact key sets), by name (no label-bearing key
    anywhere, however nested), and by content (each payload re-audited with
    `leak_check`). Anything unexpected is an abort: this file is the one
    artifact whose leaking would invalidate the pilot outright.
    """
    if set(document) != set(PRESENTATION_TOP_KEYS):
        raise CorpusBuildError(
            f"presentation manifest top-level keys {sorted(document)} != "
            f"{sorted(PRESENTATION_TOP_KEYS)}"
        )
    bundles = document["bundles"]
    if not isinstance(bundles, list) or not bundles:
        raise CorpusBuildError("presentation manifest has no bundles")
    if document["bundle_count"] != len(bundles):
        raise CorpusBuildError("presentation manifest bundle_count does not match bundles")
    judge_slots = document["judge_slots"]
    if not isinstance(judge_slots, int) or isinstance(judge_slots, bool) or judge_slots < 0:
        raise CorpusBuildError(f"judge_slots {judge_slots!r} is not a slot count")
    seen: set[str] = set()
    slots_seen: list[int] = []
    for entry in bundles:
        allowed = (
            set(PRESENTATION_BUNDLE_KEYS),
            set(PRESENTATION_BUNDLE_KEYS) | {DUPLICATE_SLOT_KEY},
        )
        if not isinstance(entry, Mapping) or set(entry) not in allowed:
            raise CorpusBuildError(
                f"presentation bundle keys {sorted(entry)} != "
                f"{sorted(PRESENTATION_BUNDLE_KEYS)} (+ optional {DUPLICATE_SLOT_KEY!r})"
            )
        if DUPLICATE_SLOT_KEY in entry:
            slot = entry[DUPLICATE_SLOT_KEY]
            if not isinstance(slot, int) or isinstance(slot, bool) or slot < 0:
                raise CorpusBuildError(f"{DUPLICATE_SLOT_KEY} {slot!r} is not a slot index")
            slots_seen.append(slot)
        pid, text, digest = (
            entry["presentation_id"], entry["rendered_text"], entry["sha256"]
        )
        if not isinstance(pid, str) or not pid.startswith("B") or not pid[1:].isdigit():
            raise CorpusBuildError(f"presentation_id {pid!r} is not an opaque B-number")
        if pid in seen:
            raise CorpusBuildError(f"duplicate presentation_id {pid!r}")
        seen.add(pid)
        if not isinstance(text, str) or not text:
            raise CorpusBuildError(f"{pid}: rendered_text is empty")
        if digest != payload_digest(pid, text):
            raise CorpusBuildError(
                f"{pid}: sha256 is not the salted digest of its rendered_text"
            )
        violations = leak_check(text, forbidden=forbidden)
        if violations:
            raise CorpusBuildError(f"{pid}: leak audit failed at write time — {violations}")
    if sorted(slots_seen) != list(range(judge_slots)):
        raise CorpusBuildError(
            f"duplicate slots {sorted(slots_seen)} are not exactly 0..{judge_slots - 1}, "
            f"one entry each"
        )
    stray = _label_bearing_keys(document)
    if stray:
        raise CorpusBuildError(f"presentation manifest has label-bearing keys: {stray}")


def presentation_document(records: Sequence[PresentationRecord], judge_slots: int = 0) -> dict:
    """Build the judge-facing document.

    `duplicate_for_slot` is the ONLY optional key: it routes an entry to one
    judge without saying anything about its class. A duplicate's `rendered_text`
    is its source's, byte for byte — the §d.2 duplicate measures within-judge
    consistency on IDENTICAL stimulus, so re-rendering it (a different seat map,
    different opaque labels) would silently measure something else.
    """
    bundles = []
    for record in sorted(records, key=lambda r: r.presentation_id):
        entry = {
            "presentation_id": record.presentation_id,
            "rendered_text": record.rendered_text,
            # Salted with the id — see `payload_digest`. Two entries with
            # identical text (a judge duplicate and its source) therefore hash
            # differently, so the hash column carries no class information.
            "sha256": payload_digest(record.presentation_id, record.rendered_text),
        }
        if record.duplicate_for_slot is not None:
            entry[DUPLICATE_SLOT_KEY] = record.duplicate_for_slot
        bundles.append(entry)
    return {
        "schema_version": SCHEMA_VERSION,
        # Includes the duplicates: this is the count of entries a judge panel
        # will be shown, not the size of the analysis deck.
        "bundle_count": len(bundles),
        "judge_slots": judge_slots,
        "bundles": bundles,
    }


def write_presentation_manifest(
    path: Path,
    records: Sequence[PresentationRecord],
    forbidden: Sequence[str] = (),
    judge_slots: int = 0,
) -> str:
    """Validate-then-write the judge-facing manifest; returns its file sha256.

    The validation is deliberately INSIDE the writer: there is no way to put a
    presentation manifest on disk without it having passed the blindness
    assertions.
    """
    document = presentation_document(records, judge_slots)
    _assert_presentation_blind(document, forbidden)
    return _write_json(path, document)


def _write_json(path: Path, document: Mapping) -> str:
    text = json.dumps(document, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")
    return _sha256_text(text)


# ---------------------------------------------------------------------------
# The build
# ---------------------------------------------------------------------------


def _window_records(checks: Sequence[WindowCheck]) -> list[dict]:
    return [
        {
            "window_index": c.window.index,
            "start": c.window.start,
            "end": c.window.end,
            "valid": c.valid,
            "reason": c.reason,
        }
        for c in checks
    ]


def build_corpus(
    *,
    master_seed: int,
    db_path: Path = DEFAULT_DB_PATH,
    out_dir: Path = DEFAULT_OUT_DIR,
    session_id: str | None = None,
    bot_seed: int = BOT_RUN_SEED,
    bot_hands: int = BOT_RUN_HANDS,
    control_seed: int = CONTROL_RUN_SEED,
    control_hands: int = CONTROL_RUN_HANDS,
    control_config: Path = DEFAULT_CONTROL_CONFIG,
    bundle_size: int = BUNDLE_SIZE,
    human_bundles: int = HUMAN_BUNDLES,
    bot_bundles: int = BOT_BUNDLES,
    lineup: Sequence[str] = RATIFIED_LINEUP,
    non_protocol_control: bool = False,
    judges: int = JUDGE_SLOTS,
) -> dict:
    """Build the whole deck and write both manifests + `_SUCCESS`.

    Returns the `_SUCCESS` body. Every parameter that is not a §d pin exists so
    the dry run can build a scaled deck through the SAME code path — the pins
    are the defaults, not a separate branch. `non_protocol_control` is the ONLY
    way to build against a control config other than the pinned one, and it
    stamps `non_protocol` on both manifests so such a deck can never be mistaken
    for the protocol deck. `judges` is the number of judge slots, each of which
    gets one extra presentation entry repeating a HUMAN bundle (§A.3).
    """
    if not 0 < bundle_size <= MAX_LOCAL_HAND_INDEX:
        raise CorpusBuildError(
            f"bundle_size {bundle_size} must be in 1..{MAX_LOCAL_HAND_INDEX} "
            f"(the renderer's local-index grammar stops there)"
        )
    bot_stride = bundle_size + BOT_STRIDE_GAP
    if bot_hands < (bot_bundles - 1) * bot_stride + bundle_size:
        raise CorpusBuildError(
            f"bot run of {bot_hands} hands cannot yield {bot_bundles} disjoint "
            f"{bundle_size}-hand windows at stride {bot_stride}"
        )
    if control_hands < bundle_size:
        raise CorpusBuildError(
            f"control run of {control_hands} hands cannot yield a {bundle_size}-hand window"
        )
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    success_path = out_dir / SUCCESS_FILENAME
    success_path.unlink(missing_ok=True)  # invalidate before rewriting

    git_sha = _git_sha()

    # --- human ------------------------------------------------------------
    snapshot = read_human_snapshot(db_path, session_id)
    grouped = group_rows(snapshot.rows)
    human_windows = enumerate_windows(snapshot.origin, snapshot.n_pinned, bundle_size)
    human_checks = [validate_human_window(grouped, w, HERO_SEAT) for w in human_windows]
    valid_human = {c.window.index: c for c in human_checks if c.valid}
    human_selected = select_windows(
        valid_human.keys(), human_bundles, derive_rng(master_seed, "human-select")
    )
    assert_disjoint([valid_human[i].window for i in human_selected])
    bundles: list[Bundle] = [
        Bundle(
            key=f"human/w{index:04d}",
            label="human",
            is_control=False,
            focus_seat=HERO_SEAT,
            hands=valid_human[index].hands,
            source={
                "kind": "human",
                "session_id": snapshot.session_id,
                "window_index": index,
                "hand_no_start": valid_human[index].window.start,
                "hand_no_end": valid_human[index].window.end,
                "focus_seat": HERO_SEAT,
            },
        )
        for index in human_selected
    ]
    # The phases the human class actually exhibits — measured, not modeled.
    human_phases = sorted({bundle_trajectory(b.hands) for b in bundles})

    # --- bot --------------------------------------------------------------
    packs = load_persona_packs()
    bot_config_hash = counterfactual.baseline_config_hash(packs)
    bot_run_id = run_id_for(bot_seed, bot_hands, bot_config_hash)
    persona_by_seat = {i: lineup[i % len(lineup)] for i in range(N_SEATS)}
    bot_windows = enumerate_windows(0, bot_hands - 1, bundle_size, stride=bot_stride)
    bot_selected = select_windows(
        (w.index for w in bot_windows), bot_bundles, derive_rng(master_seed, "bot-windows")
    )
    bot_chosen = [bot_windows[i] for i in bot_selected]
    assert_disjoint(bot_chosen)
    needed = {h for w in bot_chosen for h in w.keys()}
    bot_states = replay_run(bot_seed, bot_hands, persona_by_seat, packs, keep=needed)
    bot_focus = assign_constrained_focus_seats(
        [seat_trajectories(bot_states, w.keys()) for w in bot_chosen],
        human_phases,
        derive_rng(master_seed, "focus-seats"),
    )
    for window, focus_seat in zip(bot_chosen, bot_focus, strict=True):
        bundles.append(
            Bundle(
                key=f"bot/w{window.index:04d}",
                label="bot",
                is_control=False,
                focus_seat=focus_seat,
                hands=tuple(from_bot(bot_states[h], focus_seat) for h in window.keys()),
                source={
                    "kind": "bot",
                    "run_id": bot_run_id,
                    "run_seed": bot_seed,
                    "window_index": window.index,
                    "hand_index_start": window.start,
                    "hand_index_end": window.end,
                    "focus_seat": focus_seat,
                    "focus_persona": persona_by_seat[focus_seat],
                },
            )
        )

    # --- control ----------------------------------------------------------
    validated = counterfactual.load_config(Path(control_config))
    if validated.config_hash != PROTOCOL_CONTROL_CONFIG_HASH and not non_protocol_control:
        raise CorpusBuildError(
            f"control config hash {validated.config_hash} is not the protocol-pinned "
            f"{PROTOCOL_CONTROL_CONFIG_HASH} — pass non_protocol_control=True "
            f"(--non-protocol-control) to build a clearly-marked non-protocol deck"
        )
    is_non_protocol = validated.config_hash != PROTOCOL_CONTROL_CONFIG_HASH
    control_run_id = run_id_for(control_seed, control_hands, validated.config_hash)
    control_windows = enumerate_windows(
        0, control_hands - 1, bundle_size, stride=bot_stride
    )
    control_selected = select_windows(
        (w.index for w in control_windows), 1, derive_rng(master_seed, "control-window")
    )
    control_window = control_windows[control_selected[0]]
    control_states = replay_run(
        control_seed, control_hands, persona_by_seat, validated.packs,
        keep=set(control_window.keys()),
    )
    # The control is a bot bundle and obeys the same phase constraint.
    control_focus = assign_constrained_focus_seats(
        [seat_trajectories(control_states, control_window.keys())],
        human_phases,
        derive_rng(master_seed, "control-focus-seat"),
    )[0]
    bundles.append(
        Bundle(
            key=f"control/w{control_window.index:04d}",
            label="bot",
            is_control=True,
            focus_seat=control_focus,
            hands=tuple(
                from_bot(control_states[h], control_focus) for h in control_window.keys()
            ),
            source={
                "kind": "control",
                "run_id": control_run_id,
                "run_seed": control_seed,
                "config_path": str(Path(control_config)),
                "config_hash": validated.config_hash,
                "window_index": control_window.index,
                "hand_index_start": control_window.start,
                "hand_index_end": control_window.end,
                "focus_seat": control_focus,
                "focus_persona": persona_by_seat[control_focus],
            },
        )
    )

    # --- deck-level phase audit (fail closed) -----------------------------
    # Both directions matter: a phase only bots exhibit is a bot tell, and a
    # phase only humans exhibit is a human tell. Measured from the finished
    # bundles of both classes, so it audits what was actually built.
    phases_by_class: dict[str, set[tuple[str, ...]]] = {"human": set(), "bot": set()}
    for bundle in bundles:
        phases_by_class[bundle.label].add(bundle_trajectory(bundle.hands))
    if phases_by_class["human"] != phases_by_class["bot"]:
        only_human = sorted(phase_id(p) for p in phases_by_class["human"] - phases_by_class["bot"])
        only_bot = sorted(phase_id(p) for p in phases_by_class["bot"] - phases_by_class["human"])
        raise CorpusBuildError(
            f"position-phase leak: phases {only_human} occur only in human bundles and "
            f"{only_bot} only in bot bundles — the classes must be phase-identical"
        )
    phase_records = sorted(
        (
            {
                "phase_id": phase_id(phase),
                "start_position": phase[0],
                "human_bundles": sum(
                    1 for b in bundles
                    if b.label == "human" and bundle_trajectory(b.hands) == phase
                ),
                "bot_bundles": sum(
                    1 for b in bundles
                    if b.label == "bot" and bundle_trajectory(b.hands) == phase
                ),
            }
            for phase in phases_by_class["human"]
        ),
        key=lambda record: record["phase_id"],
    )

    # --- render, audit, split --------------------------------------------
    forbidden = sorted(
        {
            *(v.value for v in VillainType),
            *lineup,
            snapshot.session_id,
            bot_run_id,
            control_run_id,
            bot_config_hash,
            validated.config_hash,
            git_sha,
        }
        - {""}
    )
    rendered = render_bundles(bundles, master_seed, bundle_size, forbidden)
    text_by_key = {bundle.key: text for bundle, _, text in rendered}

    # --- judge duplicates (§A.3): one repeated HUMAN bundle per judge -------
    label_by_key = {bundle.key: bundle.label for bundle in bundles}
    duplicate_sources = select_duplicate_sources(
        [key for key, label in label_by_key.items() if label == "human"],
        judges,
        master_seed,
    )
    assert_duplicate_plan(duplicate_sources, label_by_key, judges)

    # Duplicates draw their ids from the SAME shuffled space as the deck, so a
    # duplicate's id is not recognisable as one (only its repeated text is, and
    # that is inherent to the design).
    presentation_ids = assign_presentation_ids(
        [b.key for b in bundles] + [duplicate_key(k) for k in range(judges)],
        derive_rng(master_seed, "presentation-ids"),
    )
    records = [
        PresentationRecord(presentation_ids[bundle.key], text)
        for bundle, _, text in rendered
    ]
    records += [
        PresentationRecord(
            presentation_ids[duplicate_key(slot)],
            text_by_key[source_key],  # byte-identical stimulus, never re-rendered
            duplicate_for_slot=slot,
        )
        for slot, source_key in enumerate(duplicate_sources)
    ]

    presentation_sha = write_presentation_manifest(
        out_dir / PRESENTATION_FILENAME, records, forbidden, judge_slots=judges
    )

    built_at = datetime.now(UTC).isoformat(timespec="seconds")
    unblinding = {
        "schema_version": SCHEMA_VERSION,
        "built_at": built_at,  # DECLARED VOLATILE: excluded from determinism checks
        "master_seed": master_seed,
        "non_protocol": is_non_protocol,
        # Every single-purpose stream's seed, plus the RULE for the one stream
        # that is parameterised per bundle (`opaque-ids` is derived with the
        # bundle key appended, and each bundle records its own seed below).
        "derived_seeds": {
            domain: f"{derive_seed(master_seed, domain):032x}"
            for domain in (
                "human-select", "bot-windows", "focus-seats", "control-window",
                "control-focus-seat", "presentation-ids",
            )
        },
        "seed_derivation": (
            "int.from_bytes(sha256('s6-detection-corpus|<master_seed>|<domain>"
            "[|<part>]').digest()[:16]); seat maps use domain 'opaque-ids' with "
            "part=<bundle_key> and record the resulting seed per bundle"
        ),
        "pins": {
            "git_sha": git_sha,
            "bundle_size": bundle_size,
            "renderer": "backend/tools/detection_render.py",
            "generator": "backend/tools/detection_corpus.py",
            "human": {
                "db_path": str(Path(db_path).resolve()),
                "session_id": snapshot.session_id,
                "n_pinned": snapshot.n_pinned,
                "window_origin": snapshot.origin,
                "focus_seat": HERO_SEAT,
                "n_bundles": len(human_selected),
            },
            "bot": {
                "run_id": bot_run_id,
                "seed": bot_seed,
                "n_hands": bot_hands,
                "buyin_spread": True,
                "lineup": {str(seat): name for seat, name in persona_by_seat.items()},
                "config_hash": bot_config_hash,
                "n_bundles": len(bot_chosen),
            },
            "control": {
                "run_id": control_run_id,
                "seed": control_seed,
                "n_hands": control_hands,
                "buyin_spread": True,
                "lineup": {str(seat): name for seat, name in persona_by_seat.items()},
                "config_path": str(Path(control_config)),
                "config_hash": validated.config_hash,
                "n_bundles": 1,
            },
        },
        "focus_seat_scheme": {
            "name": FOCUS_SEAT_SCHEME,
            "bot": list(bot_focus),
            "control": [control_focus],
            # Whatever seat coverage the phase constraint permitted — blinding
            # outranks coverage, so this is reported, not asserted.
            "bot_seat_coverage": seat_coverage(bot_focus),
            "bot_window_stride": bot_stride,
        },
        "position_phases": phase_records,
        # §A.3: the per-judge duplicate is drawn from the HUMAN class. Recorded
        # here (never in the presentation file) so analysis can join a
        # duplicate's answers back to its source bundle.
        "judge_duplicates": {
            "n_slots": judges,
            "selection": "derive_rng(master_seed, 'judge-duplicate', str(slot)).choice("
                         "sorted(human bundle keys)) — independent per slot",
            "slots": [
                {
                    "slot": slot,
                    "presentation_id": presentation_ids[duplicate_key(slot)],
                    "source_presentation_id": presentation_ids[source_key],
                    "source_bundle_key": source_key,
                    "class": "human",
                }
                for slot, source_key in enumerate(duplicate_sources)
            ],
        },
        "human_windows": {
            "candidates": _window_records(human_checks),
            "selected": list(human_selected),
        },
        "bot_windows": {
            "candidates": _window_records(
                [WindowCheck(w, True, None) for w in bot_windows]
            ),
            "selected": list(bot_selected),
        },
        "control_windows": {
            "candidates": _window_records(
                [WindowCheck(w, True, None) for w in control_windows]
            ),
            "selected": list(control_selected),
        },
        "bundles": sorted(
            (
                {
                    "presentation_id": presentation_ids[bundle.key],
                    "bundle_key": bundle.key,
                    "class": bundle.label,
                    "is_control": bundle.is_control,
                    "focus_seat": bundle.focus_seat,
                    "n_hands": len(bundle.hands),
                    # The SAME salted digest the presentation entry carries, so
                    # analysis can cross-check the two manifests by equality
                    # without ever recomputing a hash from rendered text.
                    "sha256": payload_digest(presentation_ids[bundle.key], text),
                    "phase_id": phase_id(bundle_trajectory(bundle.hands)),
                    "seat_id_map": {str(s): o for s, o in seat_id_map.items()},
                    "seat_map_seed": (
                        f"{derive_seed(master_seed, 'opaque-ids', bundle.key):032x}"
                    ),
                    "source": bundle.source,
                }
                for bundle, seat_id_map, text in rendered
            ),
            key=lambda record: record["presentation_id"],
        ),
    }
    unblinding_sha = _write_json(out_dir / UNBLINDING_FILENAME, unblinding)

    counts = {
        "human": sum(1 for b in bundles if b.label == "human"),
        "bot": sum(1 for b in bundles if b.label == "bot" and not b.is_control),
        "control": sum(1 for b in bundles if b.is_control),
    }
    success = {
        "schema_version": SCHEMA_VERSION,
        "built_at": built_at,  # DECLARED VOLATILE
        "master_seed": master_seed,
        "git_sha": git_sha,
        # Stamped here too: a reader who only ever opens _SUCCESS must still be
        # unable to mistake a non-protocol control deck for the real one.
        "non_protocol": is_non_protocol,
        # The ANALYSIS deck (duplicates and the control are excluded from deck
        # statistics); `presentation_entries` is what the panel is shown.
        "bundle_count": len(bundles),
        "presentation_entries": len(records),
        "judge_slots": judges,
        "counts": counts,
        "artifacts": {
            PRESENTATION_FILENAME: presentation_sha,
            UNBLINDING_FILENAME: unblinding_sha,
        },
    }
    # Written LAST: consumers must refuse a directory without it.
    _write_json(success_path, success)
    return success


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="build the full detection deck")
    build.add_argument("--master-seed", type=int, required=True,
                       help="the ONE seed; every purpose derives its own stream from it")
    build.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH,
                       help="owner Simulate SQLite DB (opened read-only)")
    build.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                       help="output directory (gitignored artifacts path)")
    build.add_argument("--session-id", type=str, default=None,
                       help="human session to sample; default = the one with the "
                            "most complete hands")
    build.add_argument("--bot-seed", type=int, default=BOT_RUN_SEED)
    build.add_argument("--bot-hands", type=int, default=BOT_RUN_HANDS)
    build.add_argument("--control-seed", type=int, default=CONTROL_RUN_SEED)
    build.add_argument("--control-hands", type=int, default=CONTROL_RUN_HANDS)
    build.add_argument("--control-config", type=Path, default=DEFAULT_CONTROL_CONFIG)
    build.add_argument("--non-protocol-control", action="store_true",
                       help="allow a control config other than the protocol-pinned "
                            f"{PROTOCOL_CONTROL_CONFIG_HASH[:12]}…; the resulting deck "
                            "is stamped non_protocol in both manifests")
    build.add_argument("--bundle-size", type=int, default=BUNDLE_SIZE,
                       help="hands per bundle (§d pins 30; smaller only for dry runs)")
    build.add_argument("--human-bundles", type=int, default=HUMAN_BUNDLES)
    build.add_argument("--bot-bundles", type=int, default=BOT_BUNDLES)
    build.add_argument("--judges", type=int, default=JUDGE_SLOTS,
                       help="judge slots; each gets one extra presentation entry "
                            "repeating a HUMAN bundle byte-identically (§A.3)")
    args = ap.parse_args(argv)

    success = build_corpus(
        master_seed=args.master_seed,
        db_path=args.db_path,
        out_dir=args.out_dir,
        session_id=args.session_id,
        bot_seed=args.bot_seed,
        bot_hands=args.bot_hands,
        control_seed=args.control_seed,
        control_hands=args.control_hands,
        control_config=args.control_config,
        bundle_size=args.bundle_size,
        human_bundles=args.human_bundles,
        bot_bundles=args.bot_bundles,
        non_protocol_control=args.non_protocol_control,
        judges=args.judges,
    )
    print(json.dumps(success, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
