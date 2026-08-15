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
            if combos and not (combos - covered):
                violations.append(
                    f"{pack.persona}: facing={node.facing} "
                    f"positions={node.positions} role={node.role} "
                    f"mix[{index}] is fully shadowed by earlier mixes")
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

    A facing is complete if it has a wildcard node (which answers every
    position) or if its explicit nodes together cover every position. The check
    runs per (facing, role) stratum, matching the lookup's own semantics.
    """
    strata: dict[tuple[str, str | None], set[Position]] = {}
    wildcards: set[tuple[str, str | None]] = set()
    for node in pack.preflop:
        key = (node.facing, node.role)
        if node.positions is None:
            wildcards.add(key)
        else:
            strata.setdefault(key, set()).update(node.positions)
    violations = []
    for key, covered in strata.items():
        if key in wildcards:
            continue
        # An untagged wildcard serves every role stratum of the same facing.
        if (key[0], None) in wildcards:
            continue
        missing = ALL_POSITIONS - covered
        if missing:
            names = sorted(p.value for p in missing)
            violations.append(
                f"{pack.persona}: facing={key[0]!r} role={key[1]!r} has no node "
                f"for {names} — those seats fold 100% silently")
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
