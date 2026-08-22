"""§c counterfactual-config layer (flywheel S4 T1).

Covers the §c acceptance conditions that live on this side of the repo
boundary: the three worked-rejected examples from the estimand contract
(`docs/methods/estimand-contract.md:454-457`, poker-analytics), the §a.2 axis
bounds and per-persona restrictions, deterministic dotted-path parsing against
every authored sizing key in the committed packs, the frozen probe schema and
the axis-7 co-sweep refusal, presence-preserving merge, and canonical-hash
stability across two independent processes.

Acceptance (i) — byte-identical baseline SCORES for the canonicalized baseline
— is a cross-repo export/score test and is not this module's to run; what is
provable here is the pack-level half: an empty-override config merges to the
canonicalized baseline packs and to nothing else.
"""

from __future__ import annotations

import copy
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from tools.counterfactual import (  # noqa: E402
    SCALAR_AXES,
    SCHEMA_VERSION,
    CounterfactualConfigError,
    _apply_overrides,
    _authored_resolutions,
    _collapse_shadowing_size_mixes,
    baseline_config_hash,
    baseline_pack_hash,
    canonical_bytes,
    canonicalize,
    config_hash,
    effective_call_looseness,
    empty_override_config,
    load_baseline_packs,
    load_config,
    resolve_path,
    simplex_bounds,
    validate_config,
)


@pytest.fixture(scope="module")
def packs():
    return load_baseline_packs()


def _cfg(packs, overrides=None, probes=None, **kw):
    doc = {
        "schema_version": SCHEMA_VERSION,
        "base_pack_hash": baseline_pack_hash(packs),
        "overrides": overrides or {},
        "probe_declarations": probes or [],
    }
    doc.update(kw)
    return doc


def _probe(kind, persona, paths):
    return {
        "probe_kind": kind,
        "persona": persona,
        "paths": paths,
        "rationale": "dedicated mechanism probe",
    }


# ---------------------------------------------------------------- worked examples


def test_worked_example_valid_tag_call_looseness_and_bluff_freq(packs):
    """§c "Worked example — valid": TAG `postflop.call_looseness: 0.9`
    (shipped 0.38) + `postflop.bluff_freq: 0.30` (shipped 0.22) → merges,
    re-validates, hashes.

    The shipped calling dial was 0.6 until S3-T2 (improvement slice 3,
    2026-08-22) re-tuned it to 0.38; the assertion below reads the shipped value
    so the worked example keeps demonstrating an OVERRIDE — a counterfactual is
    only worked if the value it supplies differs from the one on disk."""
    assert packs["tag"].postflop.call_looseness == 0.38
    assert packs["tag"].postflop.bluff_freq == 0.22

    result = validate_config(
        _cfg(
            packs,
            overrides={
                "tag": {"postflop.call_looseness": 0.9, "postflop.bluff_freq": 0.30},
            },
        ),
        packs,
    )
    assert result.packs["tag"].postflop.call_looseness == 0.9
    assert result.packs["tag"].postflop.bluff_freq == 0.30
    assert len(result.config_hash) == 64
    # the baseline packs themselves are untouched (shipped 0.38 since S3-T2)
    assert packs["tag"].postflop.call_looseness == 0.38


def test_worked_rejection_1_continue_ref_without_probe(packs):
    """§c "Worked example — rejected", case 1: TAG `postflop.continue_ref: 0.9`
    with empty `probe_declarations` → rejected ("frozen calibration
    anchor…declare a dedicated probe")."""
    with pytest.raises(CounterfactualConfigError) as exc:
        validate_config(
            _cfg(packs, overrides={"tag": {"postflop.continue_ref": 0.9}}), packs
        )
    message = str(exc.value)
    assert "frozen calibration anchor" in message
    assert "declare a dedicated probe" in message


def test_worked_rejection_2_structural_preflop_path(packs):
    """§c case 2: `preflop.0.mixes.0.weights.raise` → rejected (structural path)."""
    with pytest.raises(CounterfactualConfigError) as exc:
        validate_config(
            _cfg(packs, overrides={"tag": {"preflop.0.mixes.0.weights.raise": 0.5}}), packs
        )
    message = str(exc.value)
    assert "structural" in message
    assert "§a.2 axis table" in message


def test_worked_rejection_3_explicit_null(packs):
    """§c case 3: `postflop.stickiness: null` → rejected (explicit null).

    The null rule is checked BEFORE path legality, so this example fails for
    the reason the contract states rather than for being an excluded path.
    """
    with pytest.raises(CounterfactualConfigError) as exc:
        validate_config(_cfg(packs, overrides={"tag": {"postflop.stickiness": None}}), packs)
    message = str(exc.value)
    assert "explicit null" in message
    assert "§c.4" in message


def test_stickiness_with_a_number_is_still_excluded(packs):
    """Same path with a real value fails on the §a.2 exclusion instead."""
    with pytest.raises(CounterfactualConfigError, match="frozen at baseline"):
        validate_config(_cfg(packs, overrides={"tag": {"postflop.stickiness": 0.7}}), packs)


# ---------------------------------------------------------------- document shape


def test_base_pack_hash_mismatch_rejected(packs):
    doc = _cfg(packs)
    doc["base_pack_hash"] = "0" * 64
    with pytest.raises(CounterfactualConfigError, match="does not match the loaded baseline"):
        validate_config(doc, packs)


def test_base_pack_hash_is_stable_and_pack_derived(packs):
    assert baseline_pack_hash(packs) == baseline_pack_hash(load_baseline_packs())
    mutated = copy.deepcopy(dict(packs))
    mutated["tag"] = mutated["tag"].model_copy(deep=True)
    mutated["tag"].postflop.bluff_freq = 0.99
    assert baseline_pack_hash(mutated) != baseline_pack_hash(packs)


def test_unknown_top_level_field_rejected(packs):
    with pytest.raises(CounterfactualConfigError, match="unknown top-level fields"):
        validate_config(_cfg(packs, notes="hello"), packs)


def test_missing_required_field_rejected(packs):
    doc = _cfg(packs)
    del doc["probe_declarations"]
    with pytest.raises(CounterfactualConfigError, match="missing required fields"):
        validate_config(doc, packs)


def test_unsupported_schema_major_rejected(packs):
    doc = _cfg(packs)
    doc["schema_version"] = "2.0.0"
    with pytest.raises(CounterfactualConfigError, match="unsupported major"):
        validate_config(doc, packs)


@pytest.mark.parametrize(
    "version",
    [
        "1",
        "1.0",
        "1.x",
        "1.2-beta",
        "1.2.3.4",
        "v1.0.0",
        "",
        1,
        "1.0.0\n",  # `$` also matches before a trailing newline; `fullmatch` does not
        "\n1.0.0",
        " 1.0.0",
        "1.0.0 ",
        "01.0.0",  # a second spelling of "1.0.0" — and so a second config_hash
        "1.01.0",
        "1.0.00",
    ],
)
def test_malformed_schema_version_rejected(packs, version):
    """§c.1 is semver: a version that merely STARTS with a legal major must not
    be waved through on the strength of its first component.

    The trailing-newline and leading-zero cases are identity bugs, not cosmetic
    ones: the version is hashed verbatim, so accepting "1.0.0\\n" or "01.0.0"
    alongside "1.0.0" would mint two `config_hash` values for one config and
    silently duplicate a sweep arm — the same defect class as unfolded -0.0.
    """
    doc = _cfg(packs)
    doc["schema_version"] = version
    with pytest.raises(CounterfactualConfigError, match="three-part semver"):
        validate_config(doc, packs)


@pytest.mark.parametrize("version", ["1.0.0", "1.2.3", "1.10.0"])
def test_well_formed_1x_schema_versions_accepted(packs, version):
    doc = _cfg(packs)
    doc["schema_version"] = version
    assert validate_config(doc, packs).schema_version == version


def test_unknown_persona_rejected(packs):
    with pytest.raises(CounterfactualConfigError, match="unknown persona"):
        validate_config(_cfg(packs, overrides={"whale": {"postflop.bluff_freq": 0.3}}), packs)


def test_non_numeric_override_rejected(packs):
    with pytest.raises(CounterfactualConfigError, match="must be a number"):
        validate_config(_cfg(packs, overrides={"tag": {"postflop.bluff_freq": "0.3"}}), packs)


def test_boolean_override_rejected(packs):
    with pytest.raises(CounterfactualConfigError, match="must be a number"):
        validate_config(_cfg(packs, overrides={"tag": {"postflop.bluff_freq": True}}), packs)


# ---------------------------------------------------------------- §a.2 bounds


_AXIS_PERSONA = {6: "calling_station"}


@pytest.mark.parametrize("axis", SCALAR_AXES, ids=lambda a: f"axis{a.number}-{a.path}")
def test_axis_bounds_enforced(packs, axis):
    """Every §a.2 scalar axis: the declared endpoints are accepted, anything
    outside them is rejected naming the axis."""
    persona = _AXIS_PERSONA.get(axis.number, "tag")
    probes = (
        [_probe(axis.probe_kind, persona, [axis.path])] if axis.probe_kind is not None else []
    )

    for good in (axis.lo, axis.hi):
        validate_config(_cfg(packs, overrides={persona: {axis.path: good}}, probes=probes), packs)

    for bad in (axis.lo - 0.01, axis.hi + 0.01):
        with pytest.raises(CounterfactualConfigError) as exc:
            validate_config(
                _cfg(packs, overrides={persona: {axis.path: bad}}, probes=probes), packs
            )
        assert f"§a.2 axis {axis.number}" in str(exc.value)


def test_size_elasticity_frozen_for_non_authoring_personas(packs):
    """§a.2 axis 6 is swept only for the two packs that author it."""
    validate_config(
        _cfg(packs, overrides={"passive_fish": {"postflop.size_elasticity": 1.0}}), packs
    )
    with pytest.raises(CounterfactualConfigError, match="swept only"):
        validate_config(_cfg(packs, overrides={"tag": {"postflop.size_elasticity": 1.0}}), packs)


def test_position_sensitivity_frozen_for_non_authoring_personas(packs):
    """§a.2 axis 8: nit/TAG/LAG only; absence elsewhere is an intended leak."""
    validate_config(
        _cfg(packs, overrides={"nit": {"postflop.position_sensitivity": 0.5}}), packs
    )
    with pytest.raises(CounterfactualConfigError, match="swept only"):
        validate_config(
            _cfg(packs, overrides={"maniac": {"postflop.position_sensitivity": 0.5}}), packs
        )


# ---------------------------------------------------------------- path parsing


def test_every_authored_flat_sizing_key_resolves(packs):
    """Decimal-string sizing keys ("0.33", "1.0", "1.5") are matched WHOLE
    against the pack's authored key set — never re-split on the dot."""
    seen = 0
    for name, pack in packs.items():
        for key in pack.postflop.sizing:
            resolved = resolve_path(pack, f"postflop.sizing.{key}")
            assert resolved.keys == ("postflop", "sizing", key), name
            assert resolved.axis_number == 13
            assert resolved.probe_kind is None
            assert (resolved.lo, resolved.hi) == simplex_bounds(len(pack.postflop.sizing))
            seen += 1
    assert seen >= 18  # six packs x 3-4 authored keys


def test_every_authored_sizing_by_node_key_resolves(packs):
    """Two-level decimal paths (`postflop.sizing_by_node.cbet_dry.0.33`) resolve
    uniquely too — and carry NO declared bounds (§a.2 states none for the probe
    case, so none are invented here)."""
    seen = 0
    for name, pack in packs.items():
        for node, dist in (pack.postflop.sizing_by_node or {}).items():
            for key in dist:
                resolved = resolve_path(pack, f"postflop.sizing_by_node.{node}.{key}")
                assert resolved.keys == ("postflop", "sizing_by_node", node, key), name
                assert resolved.probe_kind == "sizing_by_node"
                assert (resolved.lo, resolved.hi) == (None, None), name
                seen += 1
    assert seen > 0


@pytest.mark.parametrize(
    "path,match",
    [
        ("postflop.sizing.0", "never a guess"),  # a naive split's first fragment
        ("postflop.sizing.33", "never a guess"),  # a naive split's second fragment
        ("postflop.sizing.0.3", "never a guess"),  # a near-miss decimal
        ("postflop.sizing.0.33.extra", "never a guess"),  # past the leaf
        ("postflop.sizing", "§a.2 axis table"),  # the container itself is not an axis
    ],
)
def test_unresolvable_sizing_paths_rejected(packs, path, match):
    with pytest.raises(CounterfactualConfigError, match=match):
        resolve_path(packs["calling_station"], path)


def test_ambiguous_paths_are_refused_rather_than_guessed():
    """No committed pack can produce an ambiguous path (the exhaustive key tests
    above prove every authored key resolves uniquely), so the "never a guess"
    branch is exercised directly on the resolver: a container whose keys overlap
    yields two resolutions and must therefore be refused, not greedily taken."""
    container = {"a": {"b.c": 1.0}, "a.b": {"c": 2.0}}
    assert len(_authored_resolutions(container, "a.b.c")) == 2
    assert _authored_resolutions(container, "a.b") == []  # a Mapping is not a leaf


def test_sizing_weight_bounds_enforced(packs):
    """§a.2 row 13 truncated-simplex per-key bounds."""
    keys = list(packs["tag"].postflop.sizing)
    lo, hi = simplex_bounds(len(keys))
    assert (lo, hi) == (0.05, 0.85)  # k = 4
    for bad in (lo - 0.01, hi + 0.01):
        with pytest.raises(CounterfactualConfigError, match="§a.2 axis 13"):
            validate_config(
                _cfg(packs, overrides={"tag": {f"postflop.sizing.{keys[0]}": bad}}), packs
            )


def test_unknown_path_rejected(packs):
    with pytest.raises(CounterfactualConfigError, match="§c.2"):
        validate_config(_cfg(packs, overrides={"tag": {"postflop.made_up": 1.0}}), packs)


def test_sizing_by_node_path_on_a_pack_without_that_block_rejected(packs):
    assert packs["calling_station"].postflop.sizing_by_node is None
    with pytest.raises(CounterfactualConfigError, match="does not resolve"):
        resolve_path(packs["calling_station"], "postflop.sizing_by_node.cbet_dry.0.33")


# ---------------------------------------------------------------- probes


def test_sizing_by_node_rejected_without_probe(packs):
    with pytest.raises(CounterfactualConfigError, match="frozen at baseline in wave 1"):
        validate_config(
            _cfg(packs, overrides={"tag": {"postflop.sizing_by_node.cbet_dry.0.33": 0.4}}), packs
        )


def test_continue_ref_accepted_with_matching_probe(packs):
    result = validate_config(
        _cfg(
            packs,
            overrides={"tag": {"postflop.continue_ref": 0.9}},
            probes=[_probe("continue_ref", "tag", ["postflop.continue_ref"])],
        ),
        packs,
    )
    assert result.packs["tag"].postflop.continue_ref == 0.9


def test_probe_for_a_different_persona_does_not_unfreeze(packs):
    with pytest.raises(CounterfactualConfigError, match="frozen calibration anchor"):
        validate_config(
            _cfg(
                packs,
                overrides={"tag": {"postflop.continue_ref": 0.9}},
                probes=[_probe("continue_ref", "nit", ["postflop.continue_ref"])],
            ),
            packs,
        )


@pytest.mark.parametrize(
    "mutate,match",
    [
        (lambda d: d.pop("rationale"), "frozen probe schema"),
        (lambda d: d.update(extra=1), "frozen probe schema"),
        (lambda d: d.update(probe_kind="stickiness"), "not one of"),
        (lambda d: d.update(rationale="  "), "non-empty string"),
        (lambda d: d.update(paths=[]), "non-empty list"),
    ],
)
def test_probe_schema_is_frozen(packs, mutate, match):
    probe = _probe("continue_ref", "tag", ["postflop.continue_ref"])
    mutate(probe)
    with pytest.raises(CounterfactualConfigError, match=match):
        validate_config(
            _cfg(packs, overrides={"tag": {"postflop.continue_ref": 0.9}}, probes=[probe]), packs
        )


def test_probe_kind_must_match_the_path_family(packs):
    with pytest.raises(CounterfactualConfigError, match="not a 'sizing_by_node' frozen field"):
        validate_config(
            _cfg(
                packs,
                overrides={"tag": {"postflop.continue_ref": 0.9}},
                probes=[_probe("sizing_by_node", "tag", ["postflop.continue_ref"])],
            ),
            packs,
        )


def test_continue_ref_and_call_looseness_never_co_swept(packs):
    """§a.2 axis 7: co-varying them pins their ratio and deletes the
    raise-independence feature, so the pair is refused even under a probe."""
    with pytest.raises(CounterfactualConfigError, match="§a.2 axis 7 forbids co-sweeping"):
        validate_config(
            _cfg(
                packs,
                overrides={
                    "tag": {"postflop.continue_ref": 0.9, "postflop.call_looseness": 0.9}
                },
                probes=[_probe("continue_ref", "tag", ["postflop.continue_ref"])],
            ),
            packs,
        )


def test_co_sweep_across_two_personas_is_allowed(packs):
    """The refusal is per-persona: probing nit's anchor while moving TAG's
    calling dial keeps both attributions intact."""
    result = validate_config(
        _cfg(
            packs,
            overrides={
                "nit": {"postflop.continue_ref": 0.9},
                "tag": {"postflop.call_looseness": 0.9},
            },
            probes=[_probe("continue_ref", "nit", ["postflop.continue_ref"])],
        ),
        packs,
    )
    assert result.packs["nit"].postflop.continue_ref == 0.9
    assert result.packs["tag"].postflop.call_looseness == 0.9


# ---------------------------------------------------------------- merge semantics


def _document(pack):
    return pack.model_dump(mode="json", exclude_unset=True)


def test_empty_override_merge_equals_canonicalized_baseline(packs):
    """Acceptance (i), pack half: `overrides: {}` yields the baseline packs with
    `call_looseness` materialized (§a.2) and NOTHING else changed."""
    result = validate_config(empty_override_config(packs), packs)
    for name, pack in packs.items():
        before = _document(pack)
        after = _document(result.packs[name])
        expected = copy.deepcopy(before)
        expected["postflop"]["call_looseness"] = effective_call_looseness(pack)
        assert after == expected, name


def test_canonicalization_materializes_call_looseness_on_maniac(packs):
    """`maniac` is the pack that historically left `call_looseness` unset and
    fell back to `stickiness` — the reason the canonicalization rule exists."""
    assert packs["maniac"].postflop.call_looseness is None
    assert packs["maniac"].postflop.stickiness == 0.55

    result = validate_config(empty_override_config(packs), packs)
    merged = result.packs["maniac"].postflop
    assert merged.call_looseness == 0.55
    # the fallback source stays present: `size_elasticity` is still unset, so
    # the model still requires `stickiness` (models.py:261-285)
    assert merged.stickiness == 0.55
    assert "stickiness" in merged.model_fields_set

    canonical = result.canonical["overrides"]
    for name in packs:
        assert canonical[name]["postflop.call_looseness"] == effective_call_looseness(packs[name])


def test_presence_preservation(packs):
    """Every non-overridden field keeps its presence/absence state, and its
    value too — with one named exception.

    THE EXCEPTION (T2b, 2026-08-17). Overriding a preflop sizing SCALAR also
    collapses whatever size mix shadows it onto the swept value. Without that
    the override changes nothing at all: `table/sizing._draw_size` reads the
    scalar only when no mix is authored, and since T2b every pack authors one,
    so axes 1 and 2 swept a number the engine never consulted. Measured before
    the fix, a tag swept from open 3.0 to 5.0 produced a byte-identical size
    histogram over 300 seeded decisions.

    The collapse is the narrowest repair available. The mix stays PRESENT, so
    the presence/absence half of §c.5 is untouched, and only its value moves —
    for a field that is definitionally the same lever as the swept scalar.
    Deleting the mix would have moved presence as well.

    FILED FOR THE OWNER: §c.5's "keeps its value" clause and the §a.2 axis
    declaration cannot both hold literally once a lever has both a scalar and a
    distribution form. The clause was written when the scalar was the only
    form. This test now encodes the reading that keeps the declared axis alive;
    the other reading keeps the clause intact and retires axes 1 and 2. That is
    a protocol choice, not a coding one.
    """
    overrides = {"tag": {"postflop.bluff_freq": 0.30}, "nit": {"sizing.open_bb": 2.5}}
    result = validate_config(_cfg(packs, overrides=overrides), packs)

    for name, pack in packs.items():
        base_pf = pack.postflop
        merged_pf = result.packs[name].postflop
        assert merged_pf.model_fields_set == base_pf.model_fields_set | {"call_looseness"}
        assert result.packs[name].model_fields_set == pack.model_fields_set

        expected = copy.deepcopy(_document(pack))
        expected["postflop"]["call_looseness"] = effective_call_looseness(pack)
        for path, value in overrides.get(name, {}).items():
            container = expected
            keys = path.split(".")
            for key in keys[:-1]:
                container = container[key]
            container[keys[-1]] = value
            _collapse_shadowing_size_mixes(expected, path, value)
        assert _document(result.packs[name]) == expected, name

    # And the collapse actually happened where it was due, rather than the loop
    # above passing because nothing shadowed anything.
    nit_sizing = _document(result.packs["nit"])["sizing"]
    assert nit_sizing["open_bb"] == 2.5
    assert set(nit_sizing["open_bb_mix_by_position"]) == {
        "UTG", "UTG1", "UTG2", "LJ", "HJ", "CO", "BTN", "SB", "BB"}
    assert all(mix == {"2.5": 1.0}
               for mix in nit_sizing["open_bb_mix_by_position"].values())

    # absent optional fields stay ABSENT, not defaulted into the document
    assert "position_sensitivity" not in _document(result.packs["maniac"])["postflop"]
    assert "size_elasticity" not in _document(result.packs["tag"])["postflop"]


def test_merge_never_mutates_the_baseline_packs(packs):
    before = {name: _document(pack) for name, pack in packs.items()}
    validate_config(_cfg(packs, overrides={"tag": {"postflop.aggression": 3.3}}), packs)
    assert {name: _document(pack) for name, pack in packs.items()} == before


def test_flat_sizing_simplex_vertex_merges(packs):
    """§a.2 row 13 bounds-testing endpoints: one key at its attainable max,
    every other at the 0.05 floor — these sum to 1 by construction."""
    keys = list(packs["tag"].postflop.sizing)
    lo, hi = simplex_bounds(len(keys))
    overrides = {keys[0]: hi, **dict.fromkeys(keys[1:], lo)}
    result = validate_config(
        _cfg(packs, overrides={"tag": {f"postflop.sizing.{k}": v for k, v in overrides.items()}}),
        packs,
    )
    assert result.packs["tag"].postflop.sizing == overrides


def test_partial_flat_sizing_override_rejected(packs):
    """§a.2 row 13 is a joint simplex constraint: move one flat sizing key and
    you must move them all. The rejection names that rule, not pydantic."""
    with pytest.raises(CounterfactualConfigError, match="requires overriding all 4 authored"):
        validate_config(_cfg(packs, overrides={"tag": {"postflop.sizing.0.33": 0.5}}), packs)


def test_complete_flat_sizing_override_must_sum_to_one(packs):
    keys = list(packs["tag"].postflop.sizing)
    overrides = {f"postflop.sizing.{k}": 0.20 for k in keys}  # 4 x 0.20 = 0.80
    with pytest.raises(CounterfactualConfigError, match="sum to 0.8.*not 1.0 within"):
        validate_config(_cfg(packs, overrides={"tag": overrides}), packs)


def test_flat_sizing_sum_tolerance_matches_the_pack_model(packs):
    """1e-3 here is the pack model's own normalization tolerance
    (`models.py:161`), so nothing this rule accepts can fail the §c.5 re-parse
    for being unnormalized."""
    keys = list(packs["tag"].postflop.sizing)
    weights = [0.2504, 0.25, 0.25, 0.25]  # sums to 1.0004
    result = validate_config(
        _cfg(
            packs,
            overrides={
                "tag": {f"postflop.sizing.{k}": w for k, w in zip(keys, weights, strict=True)}
            },
        ),
        packs,
    )
    assert result.packs["tag"].postflop.sizing[keys[0]] == 0.2504


def test_sizing_by_node_probe_has_no_invented_bounds(packs):
    """§a.2 declares NO bounds for probe `sizing_by_node` weights, so a weight
    below the flat-sizing 0.05 floor is accepted as long as the pack model
    validates it. (Retraction of an earlier over-strict reading.)"""
    node = "cbet_dry"
    keys = list(packs["tag"].postflop.sizing_by_node[node])
    weights = dict(zip(keys, [0.02, 0.48, 0.50], strict=True))
    paths = [f"postflop.sizing_by_node.{node}.{k}" for k in keys]
    result = validate_config(
        _cfg(
            packs,
            overrides={"tag": {p: weights[k] for p, k in zip(paths, keys, strict=True)}},
            probes=[_probe("sizing_by_node", "tag", paths)],
        ),
        packs,
    )
    assert result.packs["tag"].postflop.sizing_by_node[node] == weights


def test_partial_sizing_by_node_override_rejected_by_the_same_rule(packs):
    """The completeness rule is stated once and covers BOTH bucket-distribution
    families: a correctly-declared single-weight probe is refused by name, not
    by a raw pydantic sum-to-1 message."""
    path = "postflop.sizing_by_node.cbet_dry.0.33"
    with pytest.raises(CounterfactualConfigError) as exc:
        validate_config(
            _cfg(
                packs,
                overrides={"tag": {path: 0.9}},
                probes=[_probe("sizing_by_node", "tag", [path])],
            ),
            packs,
        )
    message = str(exc.value)
    assert "partial `postflop.sizing_by_node.cbet_dry` override" in message
    assert "requires overriding all 3 authored keys" in message
    assert "normalized by construction" in message  # the model's rule, not an §a.2 bound
    assert "re-validation" not in message


def test_complete_sizing_by_node_override_must_sum_to_one(packs):
    node = "cbet_dry"
    keys = list(packs["tag"].postflop.sizing_by_node[node])
    paths = [f"postflop.sizing_by_node.{node}.{k}" for k in keys]
    with pytest.raises(CounterfactualConfigError, match="sum to 0.6.*not 1.0 within"):
        validate_config(
            _cfg(
                packs,
                overrides={"tag": dict.fromkeys(paths, 0.2)},  # 3 x 0.2 = 0.6
                probes=[_probe("sizing_by_node", "tag", paths)],
            ),
            packs,
        )


def test_two_bucket_dists_are_checked_independently(packs):
    """Grouping is by resolved CONTAINER path, so touching two distributions in
    one config checks each against its own authored key set rather than pooling
    them into one bogus sum."""
    flat = list(packs["tag"].postflop.sizing)
    node_keys = list(packs["tag"].postflop.sizing_by_node["cbet_dry"])
    node_paths = [f"postflop.sizing_by_node.cbet_dry.{k}" for k in node_keys]
    overrides = {
        **{f"postflop.sizing.{k}": w for k, w in zip(flat, [0.25] * 4, strict=True)},
        **dict(zip(node_paths, [0.2, 0.3, 0.5], strict=True)),
    }
    result = validate_config(
        _cfg(
            packs,
            overrides={"tag": overrides},
            probes=[_probe("sizing_by_node", "tag", node_paths)],
        ),
        packs,
    )
    merged = result.packs["tag"].postflop
    assert merged.sizing == dict.fromkeys(flat, 0.25)
    assert merged.sizing_by_node["cbet_dry"] == dict(zip(node_keys, [0.2, 0.3, 0.5], strict=True))


def test_c5_reparse_still_backstops_what_no_declared_rule_covers(packs):
    """A probe distribution that is complete and sums to 1 but carries a zero
    weight passes every rule this module declares — and is still refused,
    because the §c.5 re-parse through the pack model is the final gate
    (`_validate_bucket_dist` requires every weight > 0)."""
    node = "cbet_dry"
    keys = list(packs["tag"].postflop.sizing_by_node[node])
    paths = [f"postflop.sizing_by_node.{node}.{k}" for k in keys]
    with pytest.raises(CounterfactualConfigError, match="re-validation"):
        validate_config(
            _cfg(
                packs,
                overrides={"tag": dict(zip(paths, [0.0, 0.5, 0.5], strict=True))},
                probes=[_probe("sizing_by_node", "tag", paths)],
            ),
            packs,
        )


def test_merge_is_not_a_public_entry_point():
    """5(b) ruling: the merge is private, so no caller can reach the pack model
    with dials that never passed the §a.2 bounds check. `validate_config` and
    `load_config` are the supported doors."""
    import tools.counterfactual as module

    assert not hasattr(module, "apply_overrides")
    merged = _apply_overrides(load_baseline_packs(), {"tag": {"postflop.bluff_freq": 0.4}})
    assert merged["tag"].postflop.bluff_freq == 0.4


# ---------------------------------------------------------------- canonical hash


def test_canonical_bytes_are_sorted_and_utf8():
    raw = canonical_bytes({"b": 1.5, "a": {"z": 2.0, "y": 3.0}})
    assert raw == b'{"a":{"y":3.0,"z":2.0},"b":1.5}'


def test_canonical_bytes_use_python_repr_for_floats():
    """§c.6's "shortest-round-trip float repr", as ruled: Python's repr — the
    shortest round-tripping DIGIT string, exponent formatting included. It is
    the same convention the poker-analytics scorer hashes with, and this test
    pins it so a future divergence is a deliberate amendment, not a drift."""
    assert canonical_bytes({"x": 1e-7}) == b'{"x":1e-07}'
    assert canonical_bytes({"x": 0.1 + 0.2}) == b'{"x":0.30000000000000004}'


def test_negative_zero_is_folded(packs):
    """-0.0 and 0.0 are the same behaviour, so they must be the same config."""
    nested = {"x": -0.0, "y": [-0.0], "z": {"w": -0.0}}
    assert canonical_bytes(nested) == b'{"x":0.0,"y":[0.0],"z":{"w":0.0}}'

    negative = validate_config(_cfg(packs, overrides={"tag": {"postflop.bluff_freq": -0.0}}), packs)
    positive = validate_config(_cfg(packs, overrides={"tag": {"postflop.bluff_freq": 0.0}}), packs)
    assert negative.config_hash == positive.config_hash
    # ...and the merged pack carries the value the hash names, sign bit included
    merged = negative.packs["tag"].postflop.bluff_freq
    assert merged == 0.0 and math.copysign(1.0, merged) == 1.0


def test_probe_rationale_is_part_of_the_config_identity(packs):
    """ADJUDICATED: §c.6 hashes the complete document, so rewording a probe
    rationale mints a new run identity. Deliberate — pinned here so nobody
    "fixes" it by quietly dropping prose from the hash."""
    base = _probe("continue_ref", "tag", ["postflop.continue_ref"])
    reworded = {**base, "rationale": "a differently worded but equivalent reason"}
    overrides = {"tag": {"postflop.continue_ref": 0.9}}
    a = validate_config(_cfg(packs, overrides=overrides, probes=[base]), packs)
    b = validate_config(_cfg(packs, overrides=overrides, probes=[reworded]), packs)
    assert a.config_hash != b.config_hash


def test_probe_ordering_is_canonical_even_when_only_rationale_differs(packs):
    """The canonical sort key includes `rationale`; leaving it out would let a
    swap of two otherwise-identical declarations flip the hash."""
    first = _probe("continue_ref", "tag", ["postflop.continue_ref"])
    second = {**first, "rationale": "second reading of the same anchor"}
    overrides = {"tag": {"postflop.continue_ref": 0.9}}
    a = validate_config(_cfg(packs, overrides=overrides, probes=[first, second]), packs)
    b = validate_config(_cfg(packs, overrides=overrides, probes=[second, first]), packs)
    assert a.config_hash == b.config_hash
    assert [d["rationale"] for d in a.canonical["probe_declarations"]] == sorted(
        [first["rationale"], second["rationale"]]
    )


def test_non_object_document_rejected(packs):
    with pytest.raises(CounterfactualConfigError, match="must be a JSON object"):
        validate_config([], packs)


def test_config_hash_is_authoring_order_independent(packs):
    a = validate_config(
        _cfg(
            packs,
            overrides={
                "tag": {"postflop.bluff_freq": 0.3, "postflop.aggression": 2.0},
                "nit": {"sizing.open_bb": 2.5},
            },
        ),
        packs,
    )
    b = validate_config(
        _cfg(
            packs,
            overrides={
                "nit": {"sizing.open_bb": 2.5},
                "tag": {"postflop.aggression": 2.0, "postflop.bluff_freq": 0.3},
            },
        ),
        packs,
    )
    assert a.config_hash == b.config_hash


def test_config_hash_separates_distinct_configs(packs):
    a = validate_config(_cfg(packs, overrides={"tag": {"postflop.bluff_freq": 0.30}}), packs)
    b = validate_config(_cfg(packs, overrides={"tag": {"postflop.bluff_freq": 0.31}}), packs)
    assert a.config_hash != b.config_hash


def test_int_and_float_overrides_hash_identically(packs):
    a = validate_config(_cfg(packs, overrides={"nit": {"sizing.open_bb": 3}}), packs)
    b = validate_config(_cfg(packs, overrides={"nit": {"sizing.open_bb": 3.0}}), packs)
    assert a.config_hash == b.config_hash


def test_baseline_config_hash_is_the_empty_override_hash(packs):
    assert (
        baseline_config_hash(packs)
        == validate_config(empty_override_config(packs), packs).config_hash
        == config_hash(canonicalize(empty_override_config(packs), packs))
    )


def test_load_config_from_file(tmp_path, packs):
    path = tmp_path / "cfg.json"
    doc = _cfg(packs, overrides={"tag": {"postflop.call_looseness": 0.9}})
    path.write_text(json.dumps(doc), encoding="utf-8")
    assert load_config(path, packs).config_hash == validate_config(doc, packs).config_hash


_HASH_SCRIPT = """
import json, sys
sys.path.insert(0, sys.argv[1])
from tools.counterfactual import baseline_config_hash, load_config
print(json.dumps([baseline_config_hash(), load_config(sys.argv[2]).config_hash]))
"""


def test_config_hash_stable_across_two_independent_processes(tmp_path, packs):
    """§c acceptance (iii): the canonical hash is stable across two processes.

    Different `PYTHONHASHSEED` values in the two children make any accidental
    dependence on dict/set iteration order fail loudly.
    """
    path = tmp_path / "cfg.json"
    path.write_text(
        json.dumps(
            _cfg(
                packs,
                overrides={
                    "tag": {"postflop.call_looseness": 0.9, "postflop.bluff_freq": 0.30},
                    "calling_station": {"postflop.size_elasticity": 1.25},
                },
            )
        ),
        encoding="utf-8",
    )
    outputs = []
    for seed in ("0", "1"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        proc = subprocess.run(
            [sys.executable, "-c", _HASH_SCRIPT, str(BACKEND_ROOT), str(path)],
            cwd=str(BACKEND_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        outputs.append(json.loads(proc.stdout))

    assert outputs[0] == outputs[1]
    in_process = validate_config(json.loads(path.read_text()), packs)
    assert outputs[0] == [baseline_config_hash(packs), in_process.config_hash]


# ---------------------------------------------------------------------------
# Axis liveness — a declared axis that changes nothing is worse than no axis
# ---------------------------------------------------------------------------


def test_every_preflop_sizing_axis_still_changes_realised_play(packs):
    """A swept axis must move the bots. Axes 1 and 2 stopped doing so.

    De-robotization T2b gave every pack a preflop size mix, and
    `table/sizing._draw_size` reads the scalar ONLY when no mix is authored. So
    overriding `sizing.open_bb` or `sizing.threebet_mult` became inert:
    measured before the fix, a tag swept from 3.0 to 5.0 produced a
    byte-identical size histogram over 300 seeded decisions. A sweep would have
    reported a clean null result for two of its twelve declared axes and no
    test would have said anything — the config still validated, the hashes
    still differed, and the play did not.

    `_apply_overrides` now drops whatever shadows an overridden scalar. This is
    the check that keeps that true.
    """
    import random
    from collections import Counter

    from app.domain.archetypes import VillainType
    from app.domain.spot import ActionType, Card, LegalAction, Position
    from app.domain.table.play import _preflop_decision

    facing_by_axis = {
        "sizing.open_bb": ("unopened", 1.0),
        "sizing.threebet_mult": ("vs_rfi", 3.0),
        "sizing.fourbet_mult": ("vs_3bet", 10.0),
    }
    legal = [
        LegalAction(action=ActionType.FOLD),
        LegalAction(action=ActionType.CALL, min_bb=1.0),
        LegalAction(action=ActionType.RAISE, min_bb=2.0, max_bb=300.0),
    ]

    def histogram(pack, facing, current_bet):
        counts: Counter = Counter()
        for seed in range(300):
            d = _preflop_decision(pack, Position.CO, facing,
                                  (Card("As"), Card("Ks")), legal,
                                  random.Random(seed), current_bet, 0,
                                  is_opener=False)
            if d.action is ActionType.RAISE:
                counts[d.size_bb] += 1
        return counts

    for axis in SCALAR_AXES:
        if axis.path not in facing_by_axis:
            continue
        facing, current_bet = facing_by_axis[axis.path]
        for name in ("tag", "maniac"):
            persona = VillainType(name)
            before = histogram(packs[persona], facing, current_bet)
            assert before, f"axis {axis.number}: {name} never raised at {facing}"
            # A value inside the declared bounds and far from every baseline.
            swept = axis.lo if packs[persona].sizing.open_bb > axis.lo else axis.hi
            merged = _apply_overrides(packs, {name: {axis.path: swept}})
            after = histogram(merged[persona], facing, current_bet)
            assert after != before, (
                f"axis {axis.number} ({axis.path}) is a DEAD LEVER for {name}: "
                f"sweeping it to {swept} left the size histogram identical "
                f"({dict(before)}). A mix is shadowing the scalar."
            )


def test_every_size_mix_field_is_registered_as_shadowing_its_scalar(packs):
    """The generalisation of the axis-liveness fix.

    `_clear_shadowing_size_mixes` knows which mix fields hide which scalar. A
    future mix field added to `PersonaSizing` and not registered there would
    silently kill its axis the same way — which is precisely how axes 1 and 2
    died, one slice at a time. Enumerating the model's own fields makes the
    omission fail here rather than in a sweep result.
    """
    from app.domain.content.models import PersonaSizing
    from tools.counterfactual import _SIZE_MIX_SHADOWS

    mix_fields = {f for f in PersonaSizing.model_fields if "_mix" in f}
    registered = {f for fields in _SIZE_MIX_SHADOWS.values() for f in fields}
    assert mix_fields == registered, (
        f"unregistered size-mix fields {sorted(mix_fields - registered)} / "
        f"stale entries {sorted(registered - mix_fields)}"
    )
