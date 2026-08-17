"""Pack-wide invariants the de-robotization slice depends on.

These guard three ways a persona-pack edit can do nothing, or do harm, while
every existing check stays green. All three pass against the six shipped packs
today; they exist to keep that true as the packs are edited.

Why these are tests rather than `PersonaPack` validators
--------------------------------------------------------
The grid invariant needs `RECOGNIZED_BET_FRACS`, which lives in
`app.domain.table.sizing`. The dependency between these layers runs one way
today — `table` imports `content`, never the reverse (`table/play.py:27`,
`table/range_estimate.py:51`) — and inverting it to reach one constant would
make the content schema depend on the grading layer it feeds. Persona packs are
static data shipped with the repo, so a test that loads all six and asserts the
invariant catches an authoring error at exactly the moment it is made, without
that inversion. The other two invariants are kept alongside it for symmetry.

The `_check_*` helpers take a pack and return the violations they find, so
later tickets can reuse them on candidate packs.
"""

from __future__ import annotations

import pytest

from app.domain.content.models import PersonaPack
from app.domain.personas import _combos, load_persona_packs
from app.domain.spot import Position
from app.domain.table.sizing import RECOGNIZED_BET_FRACS

ALL_POSITIONS = set(Position)


@pytest.fixture(scope="module")
def packs() -> dict:
    return load_persona_packs()


# --- 1. postflop sizes stay on the grader's recognised grid ------------------

def _check_grid(pack: PersonaPack) -> list[str]:
    """Authored postflop pot-fractions that hero's grader cannot recognise.

    `grade_map_postflop._is_canonical_bet` accepts a villain bet only within
    0.06bb of a `RECOGNIZED_BET_FRACS` fraction of the pot. An off-grid size
    silently un-maps the whole turn/river line — the failure its own source
    comment records as "0 postflop facing offers in 1,123 hands".
    """
    if pack.postflop is None:
        return []
    grid = {float(f) for f in RECOGNIZED_BET_FRACS}
    violations = []
    dists = [("sizing", pack.postflop.sizing)]
    for node, dist in (pack.postflop.sizing_by_node or {}).items():
        dists.append((f"sizing_by_node[{node}]", dist))
    for where, dist in dists:
        for key in dist:
            if float(key) not in grid:
                violations.append(f"{pack.persona}: {where} fraction {key!r} is off-grid")
    return violations


def test_every_authored_postflop_size_is_on_the_recognised_grid(packs):
    violations = [v for pack in packs.values() for v in _check_grid(pack)]
    assert not violations, "\n".join(violations)


def test_grid_check_catches_an_off_grid_fraction(packs):
    """Negative case — the invariant must be able to fail."""
    pack = packs["tag"].model_copy(deep=True)
    pack.postflop.sizing = {"0.66": 1.0}
    assert _check_grid(pack), "an off-grid 0.66 must be reported"


# --- 1b. authored preflop sizes stay gradeable ------------------------------

def _check_preflop_sizes(pack: PersonaPack) -> list[str]:
    """Authored preflop size-mix values that hero's grader would refuse.

    Nothing in `PersonaSizing` enforces this — it validates positivity, weight
    sum and finiteness only — so enumerating sizes *permits* safe authoring
    rather than guaranteeing it. This check is what makes the guarantee real.

    Caps are read from the grader itself, so a drift there fails here instead
    of silently widening what may be authored. They are the OUTER ENVELOPE and
    not the whole rule: hero's preflop grading is path-dependent, and in a
    hero-3-bet line the villain's own open must additionally be at most
    `_STD_OPEN_CAP` while the 3-bet cap applies to the canonical positional
    open rather than the actual one. A value passing here can still be
    ungradeable down a particular line; a value failing here is ungradeable
    everywhere.
    """
    from app.domain.table import grade_map_preflop as gmp

    caps = (
        ("open_bb_mix", gmp._OVERSIZE_OPEN_CAP, "open bb"),
        ("threebet_mult_mix", gmp._THREEBET_MULT_CAP, "3-bet multiplier"),
        ("fourbet_mult_mix", gmp._FOURBET_MULT_CAP, "4-bet multiplier"),
    )
    violations = []
    for field, cap, label in caps:
        for key in (getattr(pack.sizing, field) or {}):
            if float(key) > cap + 1e-9:
                violations.append(
                    f"{pack.persona}: {label} {key} exceeds the grading cap "
                    f"{cap} — hero would see 'no baseline yet'")
    # The seat table is the open mix in another shape and gets the same cap.
    # Reading only the flat field would let a per-seat 9bb open through the one
    # check that exists to stop it.
    for seat, mix in (pack.sizing.open_bb_mix_by_position or {}).items():
        for key in mix:
            if float(key) > gmp._OVERSIZE_OPEN_CAP + 1e-9:
                violations.append(
                    f"{pack.persona}: open bb {key} at {seat} exceeds the "
                    f"grading cap {gmp._OVERSIZE_OPEN_CAP} — hero would see "
                    f"'no baseline yet'")
    return violations


_BLIND_SEATS = ("SB", "BB")


def _authored_opens(pack: PersonaPack, *, blinds: bool = True) -> list[float]:
    """Every open size the pack can produce, from whichever form it authored.

    `blinds=False` drops the two blind seats, which matters because both spots
    that cap the opener's size — `_map_vs_3bet` and `_map_vs_4bet` — reject a
    blind opener outright, before any size is looked at.
    """
    seat_table = pack.sizing.open_bb_mix_by_position or {}
    keys = set(pack.sizing.open_bb_mix or {})
    for seat, mix in seat_table.items():
        if not blinds and seat in _BLIND_SEATS:
            continue
        keys |= set(mix)
    return sorted(float(k) for k in keys) or [pack.sizing.open_bb]


def test_authored_preflop_sizes_stay_gradeable(packs):
    violations = [v for pack in packs.values() for v in _check_preflop_sizes(pack)]
    assert not violations, "\n".join(violations)


def test_preflop_size_check_catches_an_ungradeable_value(packs):
    """Negative case. `PersonaSizing` itself happily accepts a 9bb open —
    which is exactly why this check has to exist."""
    pack = packs["tag"].model_copy(deep=True)
    pack.sizing.open_bb_mix_by_position = None
    pack.sizing.open_bb_mix = {"3.0": 0.5, "9.0": 0.5}
    violations = _check_preflop_sizes(pack)
    assert violations and "9.0" in violations[0], violations


def test_the_seat_table_is_checked_too(packs):
    """The same negative case, hidden one level down. A per-seat mix is the
    form the three regulars actually ship, so a check that only reads the flat
    field would be checking nobody."""
    pack = packs["tag"].model_copy(deep=True)
    assert pack.sizing.open_bb_mix_by_position, "tag is expected to ship a seat table"
    pack.sizing.open_bb_mix_by_position["BTN"] = {"2.5": 0.5, "9.0": 0.5}
    violations = _check_preflop_sizes(pack)
    assert violations and "BTN" in violations[0], violations


def test_a_regulars_open_never_exceeds_the_hero_3bet_lines_cap(packs):
    """Tighter than the outer envelope above, and for a different node.

    `_check_preflop_sizes` uses `_OVERSIZE_OPEN_CAP` (4.5), which is the band
    for hero merely FACING an open. Two other spots are stricter: when hero
    3-bets and this seat 4-bets, and when hero opens and this seat 3-bets,
    `_map_vs_4bet` and `_map_vs_3bet` both require the opener's own open to be
    at most `_STD_OPEN_CAP` (3.0). An open above that returns 'no baseline yet'
    for the whole hand.

    The three recreationals already open above 3.0 as their shipped identity
    (3.5 / 4.0 / 4.5) and are excluded — this is a guard against a REGULAR
    quietly acquiring a big-open rung to buy size variety, which would buy it
    by deleting hero's feedback. Spec 7.1 forbids that trade.

    The BLIND seats are excluded too, and that is a fact about the graders
    rather than a convenience: both `_map_vs_3bet` and `_map_vs_4bet` return
    None for a blind opener before any size is examined
    (`opener_pos in _BLIND_POSITIONS`), so no size a blind seat chooses can
    cost hero a spot at those nodes. It is also why the regulars can carry the
    +0.5bb small-blind bump RES-B 4.1 asks for.
    """
    from app.domain.table import grade_map_preflop as gmp

    offenders = []
    for name, pack in packs.items():
        if pack.sizing.open_bb > gmp._STD_OPEN_CAP + 1e-9:
            continue  # recreational: already outside, by design
        too_big = [s for s in _authored_opens(pack, blinds=False)
                   if s > gmp._STD_OPEN_CAP + 1e-9]
        if too_big:
            offenders.append(f"{name}: {too_big} above {gmp._STD_OPEN_CAP}")
    assert not offenders, "\n".join(offenders)


def test_no_authored_seat_mix_plays_as_one_size(packs):
    """The design rule the values were chosen to satisfy, stated where it can
    fail: no seat may put more than 0.90 of its mass on a single size.

    This is the AUTHORED side of
    `test_preflop_size_values.py::test_every_persona_mixes_its_open_at_every_seat`,
    which measures the same property in production's sampler. Two checks
    because they fail for different reasons: this one catches a value written
    too heavy, that one catches a value that never reaches the engine.
    """
    ceiling = 0.90
    offenders = []
    for name, pack in packs.items():
        table = pack.sizing.open_bb_mix_by_position
        mixes = table.items() if table else [("flat", pack.sizing.open_bb_mix or {})]
        for seat, mix in mixes:
            if mix and max(mix.values()) > ceiling + 1e-9:
                offenders.append(f"{name}@{seat}: {max(mix.values())} > {ceiling}")
    assert not offenders, "\n".join(offenders)


# --- 2. no preflop mix is shadowed dead -------------------------------------

def _check_shadowed_mixes(pack: PersonaPack) -> list[str]:
    """Mixes that can never be selected.

    `sample_preflop_action` scans a node's mixes in list order and takes the
    first whose combo set contains the hand (`personas.py:100`); combo overlap
    between mixes is not validated anywhere. A softer edge mix appended after a
    hard mix that already covers those hands is therefore dead code, and
    nothing fails — the most likely way a range-softening edit accomplishes
    exactly nothing.
    """
    violations = []
    for node in pack.preflop:
        covered: set[str] = set()
        for index, mix in enumerate(node.mixes):
            combos = _combos(mix.combos)
            where = (f"{pack.persona}: facing={node.facing} "
                     f"positions={node.positions} role={node.role} mix[{index}]")
            if not combos:
                # An empty range expands to the empty set, so the mix can never
                # match any hand — dead on arrival rather than shadowed.
                violations.append(f"{where} expands to no combos at all")
            elif not (combos - covered):
                violations.append(f"{where} is fully shadowed by earlier mixes")
            covered |= combos
    return violations


def test_no_preflop_mix_is_shadowed_by_an_earlier_one(packs):
    violations = [v for pack in packs.values() for v in _check_shadowed_mixes(pack)]
    assert not violations, "\n".join(violations)


def test_shadowing_check_catches_a_dead_mix(packs):
    """Negative case: appending a softened AQo mix behind a hard one that
    already covers AQo is precisely the mistake this guards."""
    pack = packs["tag"].model_copy(deep=True)
    node = next(n for n in pack.preflop if n.facing == "vs_rfi")
    first = node.mixes[0]
    node.mixes.append(first.model_copy(update={"weights": {"call": 0.5}}))
    assert _check_shadowed_mixes(pack), "the appended duplicate must be reported"


# --- 3. every position is answered ------------------------------------------

def _check_position_coverage(pack: PersonaPack) -> list[str]:
    """Positions that would fall through to the implicit-fold path.

    `PersonaPack._node_ordering` rejects overlap and ordering errors but never
    requires COMPLETE coverage. When no node matches, `sample_preflop_action`
    runs off the end of its scan and returns fold at weight 1.0 — so a seat
    omitted while splitting a wildcard node into per-position nodes makes that
    persona fold 100% from that seat, silently.

    Rather than reasoning about wildcards and strata separately — which is easy
    to get subtly wrong, since an UNTAGGED node answers both role strata
    whatever its position list — this asks the runtime question directly: for
    each facing the pack authors, each role a production caller can pass, and
    each seat, would any node match? That predicate is copied from
    `sample_preflop_action` and stays correct as long as it does.

    Production callers (`play.bot_decision`, `range_estimate`) always pass a
    real boolean, so the reachable strata are "opener" and "cold".
    """

    def matches(node, facing: str, position: Position, want_role: str) -> bool:
        if node.facing != facing:
            return False
        if node.positions is not None and position not in node.positions:
            return False
        return not (node.role is not None and node.role != want_role)

    violations = []
    for facing in sorted({n.facing for n in pack.preflop}):
        for want_role in ("opener", "cold"):
            missing = [
                position for position in sorted(ALL_POSITIONS, key=lambda p: p.value)
                if not any(matches(n, facing, position, want_role)
                           for n in pack.preflop)
            ]
            if missing:
                names = [p.value for p in missing]
                violations.append(
                    f"{pack.persona}: facing={facing!r} role={want_role!r} has "
                    f"no node for {names} — those seats fold 100% silently")
    return violations


def test_every_facing_answers_every_position(packs):
    violations = [v for pack in packs.values() for v in _check_position_coverage(pack)]
    assert not violations, "\n".join(violations)


def test_coverage_check_catches_a_dropped_seat(packs):
    """Negative case: drop one seat from an explicit-position facing that has
    no wildcard to catch it."""
    pack = packs["lag"].model_copy(deep=True)
    target = next(
        (n for n in pack.preflop
         if n.facing == "unopened" and n.positions and Position.BTN in n.positions),
        None)
    assert target is not None, "fixture assumption: lag has an explicit BTN open node"
    target.positions = [p for p in target.positions if p is not Position.BTN]
    violations = _check_position_coverage(pack)
    assert any("btn" in v.lower() for v in violations), violations
