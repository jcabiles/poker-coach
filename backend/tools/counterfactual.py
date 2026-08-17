"""Counterfactual-config layer (bot-realism flywheel S4, ticket T1).

The §c config language of the estimand contract
(`poker-analytics docs/methods/estimand-contract.md:415-462`, v2.3): an
*ephemeral* JSON document that names dial overrides on the baseline persona
packs, is validated against the §a.2 axis table (`:86-148`), merged onto an
in-memory deep copy of the packs, re-validated through the SAME pydantic model
the engine loads at play time, and hashed to a canonical `config_hash`.

Three invariants this module exists to keep:

1. **Nothing on disk moves.** `content/personas/*.json` and
   `backend/app/domain/` are read-only here (flywheel no-go; contract map
   `docs/ai-dlc/contracts/flywheel-s4.md:16,26`). The overlay is a fresh dict
   built from `model_dump(exclude_unset=True)`, never an attribute write on a
   loaded pack — §c.5 forbids in-place update because it is documented to
   bypass validation.
2. **Key ABSENCE is load-bearing.** `PersonaPostflop` reads `stickiness` only
   where a split lever is unset and *forbids* it once both are authored
   (`models.py:261-285`), and `continue_ref`/`line_sensitivity` treat an
   explicit null as a lie (`models.py:287-313`). So the merge round-trips
   through `exclude_unset=True` and explicit `null` overrides are rejected
   (§c.4).
3. **A path either resolves exactly or is refused.** Flat-sizing weight keys
   are decimal strings ("0.33"), so a naive `split(".")` would shred them.
   Resolution is greedy-longest-match against the pack's *authored* key set and
   a non-unique resolution is a rejection, never a guess (spec
   `docs/ai-dlc/specs/flywheel-s4.md:63-67`).

Canonicalization (§a.2 `:142-148`): every sweep config materializes
`call_looseness` explicitly on every persona. Exactly one shipped pack
(`maniac`) leaves it unset and falls back to `stickiness`
(`personas_postflop.py:889`), where that one number secretly drives two
mechanisms. Materializing it at its effective value is behaviour-identical by
the engine's own fallback semantics — but the contract gates that claim on
evidence: S4's acceptance test 1(i) must prove byte-identical baseline scores
before any sweep runs.

Hash identity is the WHOLE document (§c.6). That includes each probe
declaration's `rationale`: rewording a rationale changes `config_hash` and
therefore mints a new run identity. Reviewers split on this; the ruling is that
§c.6 hashes the complete document, so prose is part of the config's name — write
the rationale once, then leave it alone for the life of the sweep.

Pure functions; no I/O beyond reading the committed packs (and an explicitly
passed config path). Nothing here writes a file.

Merging is reachable ONLY through `validate_config` / `load_config`. The merge
step is deliberately private (`_apply_overrides`): it is handed the CANONICAL
overrides, which carry `call_looseness` materialized at each pack's baseline
effective value, and baseline values are not required to sit inside the §a.2
*sweep* bounds. Enforcing bounds at the merge site would therefore couple the
baseline packs to the sweep bounds and could refuse the baseline itself; the
bounds are enforced once, on the AUTHORED overrides, where they belong.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.domain.archetypes import VillainType
from app.domain.content.models import PersonaPack
from app.domain.personas import load_persona_packs

# §c.1 — semver; a breaking change is a major bump. We accept any 1.x document,
# but only if it is a well-formed three-part semver: "1", "1.2", "1.2-beta" and
# "1.2.3.4" are all rejected rather than silently read as major 1.
#
# Two subtleties, both identity bugs rather than cosmetics: the version string is
# copied verbatim into the canonical document and therefore into `config_hash`,
# so any two spellings this validator accepts become two names for one config and
# silently duplicate a sweep arm.
#   * `fullmatch`, NOT `match` against `^...$` — Python's `$` also matches before
#     a trailing newline, so `"1.0.0\n"` sails through an anchored `match`.
#   * per-component `(0|[1-9]\d*)`, NOT `\d+` — otherwise `"01.0.0"` is a second
#     spelling of `"1.0.0"`.
# poker-analytics enforces the same rule at its ingestion gate and documents the
# `fullmatch` reason identically (`ingest/validate.py:54,85-97`). Its component
# pattern is the looser `\d+`, which is harmless THERE (its `_semver()`
# normalizes to ints before comparing) and unsafe HERE (we hash the raw string),
# so this pattern is deliberately the stricter of the two.
SCHEMA_VERSION = "1.0.0"
_SUPPORTED_MAJOR = 1
_SEMVER = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")

_DOCUMENT_FIELDS = frozenset({
    "schema_version",
    "base_pack_hash",
    "overrides",
    "probe_declarations",
})
_PROBE_FIELDS = frozenset({"probe_kind", "persona", "paths", "rationale"})


class CounterfactualConfigError(ValueError):
    """A §c rejection. Every message names the rule it enforces."""


# --------------------------------------------------------------------------
# §a.2 axis table (estimand-contract.md:91-105)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Axis:
    """One row of the §a.2 declared search space.

    `personas=None` means all six author it; a set restricts the axis to the
    packs that do (axis 6 station/fish, axis 8 nit/TAG/LAG). `probe_kind` marks
    a frozen field that §c.3 accepts only under a matching probe declaration.
    """

    number: int
    path: str
    lo: float
    hi: float
    personas: frozenset[VillainType] | None = None
    probe_kind: str | None = None


_ELASTIC = frozenset({VillainType.CALLING_STATION, VillainType.PASSIVE_FISH})
_POSITIONAL = frozenset({VillainType.NIT, VillainType.TAG, VillainType.LAG})

SCALAR_AXES: tuple[Axis, ...] = (
    Axis(1, "sizing.open_bb", 2.0, 5.0),
    Axis(2, "sizing.threebet_mult", 2.0, 4.0),
    Axis(3, "sizing.fourbet_mult", 2.0, 3.5),
    Axis(4, "postflop.aggression", 0.2, 5.6),
    Axis(5, "postflop.call_looseness", 0.2, 5.0),
    Axis(6, "postflop.size_elasticity", 0.0, 3.0, personas=_ELASTIC),
    Axis(7, "postflop.continue_ref", 0.05, 8.0, probe_kind="continue_ref"),
    Axis(8, "postflop.position_sensitivity", 0.0, 1.0, personas=_POSITIONAL),
    Axis(9, "postflop.line_sensitivity", 0.0, 2.0),
    Axis(10, "postflop.bluff_freq", 0.0, 1.0),
    Axis(11, "postflop.spr_commit", 0.5, 4.0),
    Axis(12, "postflop.multiway_bluff_damp", 0.0, 1.0),
)
_AXIS_BY_PATH: dict[str, Axis] = {a.path: a for a in SCALAR_AXES}

# Axis 13 — the flat `postflop.sizing` truncated simplex, and (probe-only) the
# same shape under `postflop.sizing_by_node`.
_FLAT_SIZING = "postflop.sizing"
_NODE_SIZING = "postflop.sizing_by_node"
PROBE_KINDS = frozenset({"continue_ref", "sizing_by_node"})
# Both weight families report axis 13; a resolved path carrying it is a weight
# inside a normalized bucket distribution (see `_check_bucket_dist_completeness`).
_BUCKET_DIST_AXIS = 13

# §a.2 exclusions that deserve their own error text rather than a generic
# "unknown path" (estimand-contract.md:113-140).
_EXCLUDED_PATHS: dict[str, str] = {
    "postflop.stickiness": (
        "`stickiness` is frozen at baseline (§a.2 exclusion): sweeping it would "
        "sweep price response through a formula the packs' own docs call "
        "not-scale-equivalent to the direct lever"
    ),
}

# The call-looseness axis, needed by name in two rules (canonicalization and
# the axis-7 co-sweep refusal).
_CALL_LOOSENESS = "postflop.call_looseness"
_CONTINUE_REF = "postflop.continue_ref"


def simplex_bounds(k: int) -> tuple[float, float]:
    """Axis 13's truncated-simplex per-key bounds for a pack with `k` authored
    FLAT (`postflop.sizing`) keys: [0.05, min(0.90, 1 − (k−1)·0.05)] (§a.2 row
    13). For k = 4 the attainable per-key max is 0.85.

    The bound is per key; the simplex is also a *joint* constraint, enforced
    separately by `_check_bucket_dist_completeness`.

    These BOUNDS are NOT applied to `sizing_by_node`: §a.2 freezes that family
    in wave 1 and declares NO bounds for the probe case, so inventing them here
    would refuse probe distributions the pack model accepts (a node dist may
    legitimately carry a weight below 0.05). Until a contract amendment declares
    bounds, a probe weight's only per-key constraint is the §c.5 re-parse.

    The NORMALIZATION rule is a different matter and does apply to both families
    — normalization is structural in the pack model, not a §a.2 sweep bound.
    """
    return 0.05, min(0.90, 1.0 - (k - 1) * 0.05)


# --------------------------------------------------------------------------
# Deterministic dotted-path resolution
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ResolvedPath:
    """A dotted override path resolved to concrete container keys.

    `lo`/`hi` are the §a.2 declared sweep bounds, or `None` where the contract
    declares none (probe-only `sizing_by_node` weights) — there the pack model's
    own validation is the only constraint.
    """

    keys: tuple[str, ...]
    axis_number: int
    lo: float | None
    hi: float | None
    probe_kind: str | None


def _authored_resolutions(container: Mapping[str, Any], path: str) -> list[tuple[str, ...]]:
    """Every way `path` resolves to a leaf under `container`'s authored keys.

    Keys are tried longest-first (the greedy-longest-match rule, spec
    `flywheel-s4.md:63-67`), but *all* resolutions are collected so the caller
    can refuse an ambiguous path instead of silently taking the greedy one. A
    decimal-string key like "0.33" is matched whole and never re-split, because
    matching is by string prefix against real keys rather than by `split(".")`.
    """
    out: list[tuple[str, ...]] = []
    for key in sorted(container, key=len, reverse=True):
        value = container[key]
        if path == key:
            if not isinstance(value, Mapping):
                out.append((key,))
        elif path.startswith(key + ".") and isinstance(value, Mapping):
            out.extend((key, *rest) for rest in _authored_resolutions(value, path[len(key) + 1 :]))
    return out


def resolve_path(pack: PersonaPack, path: str) -> ResolvedPath:
    """Resolve one override path against one pack, or raise.

    Order: the §a.2 scalar axis table (exact match) → the flat-sizing simplex →
    the probe-only `sizing_by_node` weights → rejection (§c.2: allowed paths are
    exactly the axis table; anything else, including structural paths, is
    rejected with an error naming the rule).
    """
    axis = _AXIS_BY_PATH.get(path)
    if axis is not None:
        if axis.personas is not None and pack.persona not in axis.personas:
            raise CounterfactualConfigError(
                f"{pack.persona}: path {path!r} is §a.2 axis {axis.number}, which is swept "
                f"only for {sorted(p.value for p in axis.personas)} (the packs that author "
                f"it); it is frozen at baseline for {pack.persona}"
            )
        if pack.postflop is None and path.startswith("postflop."):
            raise CounterfactualConfigError(
                f"{pack.persona}: path {path!r} does not resolve — the pack authors no "
                f"`postflop` block (§c.2 allowed paths = exactly the §a.2 axis table)"
            )
        return ResolvedPath(tuple(path.split(".")), axis.number, axis.lo, axis.hi, axis.probe_kind)

    if path in _EXCLUDED_PATHS:
        raise CounterfactualConfigError(
            f"{pack.persona}: path {path!r} rejected — {_EXCLUDED_PATHS[path]}"
        )

    postflop = pack.postflop
    if postflop is not None:
        if path.startswith(_FLAT_SIZING + "."):
            rest = path[len(_FLAT_SIZING) + 1 :]
            found = _authored_resolutions(postflop.sizing, rest)
            keys = _unique_resolution(pack, path, found, "postflop.sizing")
            lo, hi = simplex_bounds(len(postflop.sizing))
            return ResolvedPath(("postflop", "sizing", *keys), 13, lo, hi, None)

        if path.startswith(_NODE_SIZING + "."):
            rest = path[len(_NODE_SIZING) + 1 :]
            by_node = postflop.sizing_by_node or {}
            found = _authored_resolutions(by_node, rest)
            keys = _unique_resolution(pack, path, found, "postflop.sizing_by_node")
            # No declared bounds: §a.2 freezes this family and states none for
            # the probe case (see `simplex_bounds`). The §c.5 re-parse is the
            # only constraint until a contract amendment declares bounds.
            return ResolvedPath(
                ("postflop", "sizing_by_node", *keys), 13, None, None, "sizing_by_node"
            )

    raise CounterfactualConfigError(
        f"{pack.persona}: path {path!r} is not in the §a.2 axis table — structural fields, "
        f"preflop mix tables and range structures, engine constants and unknown paths are "
        f"rejected (§c.2)"
    )


def _unique_resolution(
    pack: PersonaPack, path: str, found: Sequence[tuple[str, ...]], family: str
) -> tuple[str, ...]:
    if len(found) == 1:
        return found[0]
    if not found:
        raise CounterfactualConfigError(
            f"{pack.persona}: path {path!r} does not resolve against the pack's authored "
            f"{family} keys — an unresolvable path is a rejection, never a guess (§c.2)"
        )
    raise CounterfactualConfigError(
        f"{pack.persona}: path {path!r} is ambiguous against the pack's authored {family} "
        f"keys ({sorted('.'.join(f) for f in found)}) — an ambiguous path is a rejection, "
        f"never a guess (§c.2)"
    )


# --------------------------------------------------------------------------
# Canonical bytes + hashing (§c.6)
# --------------------------------------------------------------------------


def _normalize_zeros(value: Any) -> Any:
    """Fold `-0.0` to `0.0` everywhere in a document.

    IEEE gives negative zero its own bit pattern and Python's repr preserves it,
    so `{"bluff_freq": -0.0}` and `{"bluff_freq": 0.0}` would otherwise hash to
    two different `config_hash` values for one behaviour. A config's identity
    must track behaviour, so the two collapse. (`-0.0 == 0.0` is True, which is
    why the equality test below is enough.)
    """
    if isinstance(value, Mapping):
        return {k: _normalize_zeros(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_zeros(v) for v in value]
    if isinstance(value, float) and value == 0.0:
        return 0.0
    return value


def canonical_bytes(document: Mapping[str, Any]) -> bytes:
    """§c.6 canonical serialization: sorted keys, shortest-round-trip float
    repr, UTF-8, no insignificant whitespace.

    **Reading of "shortest-round-trip float repr" (ruled 2026-08-07):**
    `json.dumps` emits Python's `float.__repr__`, which since 3.1 is the
    shortest DECIMAL DIGIT STRING that round-trips — but not the shortest
    possible text, since it writes `1e-07` where `1e-7` would also round-trip.
    Python repr IS the canonical form for this pipeline: poker-analytics'
    scorer already hashes its canonical payloads through the same
    `json.dumps` convention (`scorer/canonical.py`), and one convention shared
    end-to-end is worth more than literal minimality. A future change to this
    reading is a §c.6 amendment, not an implementation detail.

    `-0.0` is folded to `0.0` first (see `_normalize_zeros`). `allow_nan=False`
    keeps non-finite values out of the hash input — they are rejected upstream
    anyway.
    """
    return json.dumps(
        _normalize_zeros(document),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def config_hash(canonical_document: Mapping[str, Any]) -> str:
    """`config_hash = sha256(canonical bytes)` (§c.6) — the config's identity in
    every manifest, score row and verdict table.

    The argument must already be canonicalized (see `canonicalize`); hashing a
    raw authored document would give two names to one behaviour.
    """
    return hashlib.sha256(canonical_bytes(canonical_document)).hexdigest()


def load_baseline_packs(content_dir: Path | None = None) -> dict[VillainType, PersonaPack]:
    """The committed baseline packs, read-only (`personas.py:40-53`)."""
    return load_persona_packs(content_dir)


def _pack_document(pack: PersonaPack) -> dict[str, Any]:
    """A JSON-shaped deep copy of a pack that preserves key PRESENCE.

    `exclude_unset=True` keeps exactly the keys the authored file set, which is
    what `PersonaPostflop`'s authorship validators read (`models.py:261-313`).
    """
    return pack.model_dump(mode="json", exclude_unset=True)


def baseline_pack_hash(packs: Mapping[VillainType, PersonaPack]) -> str:
    """§c document shape: `base_pack_hash` = "sha256 of the canonical serialized
    baseline pack set" — the §c.6 canonical bytes of {persona: pack document},
    with each pack serialized presence-preservingly.

    A config that names a different pack set than the one loaded is refused, so
    a sweep can never silently drift off its declared baseline.
    """
    return config_hash({str(name): _pack_document(pack) for name, pack in packs.items()})


# --------------------------------------------------------------------------
# Validation (§c.1-c.4) and canonicalization (§a.2)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ProbeDeclaration:
    """The frozen probe-declaration schema (spec `flywheel-s4.md:68-72`):
    `{probe_kind, persona, paths[], rationale}` — no more, no less."""

    probe_kind: str
    persona: str
    paths: tuple[str, ...]
    rationale: str

    def as_document(self) -> dict[str, Any]:
        return {
            "probe_kind": self.probe_kind,
            "persona": self.persona,
            "paths": sorted(self.paths),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class ValidatedConfig:
    """A §c config that passed validation, merge and re-validation.

    `packs` are the in-memory overlay pack objects the exporter runs — the
    result of merging onto deep copies and re-parsing through the SAME pydantic
    model (§c.5). `canonical` is the §a.2-canonicalized document whose §c.6
    hash is `config_hash`.
    """

    schema_version: str
    base_pack_hash: str
    overrides: dict[str, dict[str, float]]
    probe_declarations: tuple[ProbeDeclaration, ...]
    canonical: dict[str, Any]
    config_hash: str
    packs: dict[VillainType, PersonaPack]


def _require_number(persona: str, path: str, value: Any) -> float:
    """§c.4: overrides SET numbers. Explicit `null` is forbidden — key-absence
    is semantically load-bearing in this model and unsetting is structural."""
    if value is None:
        raise CounterfactualConfigError(
            f"{persona}: override {path!r} is an explicit null — explicit null is forbidden "
            f"(§c.4: key-absence is semantically load-bearing in this model; unsetting a key "
            f"is a structural change the schema deliberately cannot express)"
        )
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CounterfactualConfigError(
            f"{persona}: override {path!r} must be a number, got {type(value).__name__} "
            f"({value!r}) (§c document shape: overrides map dotted paths to numbers)"
        )
    number = float(value)
    if not math.isfinite(number):
        raise CounterfactualConfigError(
            f"{persona}: override {path!r} is not finite ({value!r}) (§c document shape: "
            f"overrides map dotted paths to numbers)"
        )
    # Fold -0.0 to 0.0 here as well as in `canonical_bytes`, so the MERGED PACK
    # carries the same value the hash names — otherwise two packs that hash
    # alike could differ by a sign bit.
    return number + 0.0


def _parse_probe_declarations(raw: Any) -> tuple[ProbeDeclaration, ...]:
    if not isinstance(raw, list):
        raise CounterfactualConfigError(
            f"`probe_declarations` must be a list, got {type(raw).__name__} (§c document shape)"
        )
    out: list[ProbeDeclaration] = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, Mapping):
            raise CounterfactualConfigError(
                f"probe_declarations[{i}] must be an object (frozen probe schema: "
                f"{{probe_kind, persona, paths, rationale}})"
            )
        unknown = set(entry) - _PROBE_FIELDS
        missing = _PROBE_FIELDS - set(entry)
        if unknown or missing:
            raise CounterfactualConfigError(
                f"probe_declarations[{i}] does not match the frozen probe schema "
                f"{{probe_kind, persona, paths, rationale}}: unknown {sorted(unknown)}, "
                f"missing {sorted(missing)}"
            )
        kind, persona, paths, rationale = (
            entry["probe_kind"],
            entry["persona"],
            entry["paths"],
            entry["rationale"],
        )
        if kind not in PROBE_KINDS:
            raise CounterfactualConfigError(
                f"probe_declarations[{i}]: probe_kind {kind!r} is not one of "
                f"{sorted(PROBE_KINDS)} (frozen probe schema)"
            )
        if not isinstance(persona, str):
            raise CounterfactualConfigError(
                f"probe_declarations[{i}]: persona must be a string (frozen probe schema)"
            )
        if not isinstance(paths, list) or not paths or not all(isinstance(p, str) for p in paths):
            raise CounterfactualConfigError(
                f"probe_declarations[{i}]: paths must be a non-empty list of strings "
                f"(frozen probe schema)"
            )
        if not isinstance(rationale, str) or not rationale.strip():
            raise CounterfactualConfigError(
                f"probe_declarations[{i}]: rationale must be a non-empty string — a frozen "
                f"field is unfrozen only by a stated mechanism-probe rationale (§c.3)"
            )
        out.append(ProbeDeclaration(kind, persona, tuple(paths), rationale))
    return tuple(out)


def _check_document_shape(
    document: Mapping[str, Any], packs: Mapping[VillainType, PersonaPack]
) -> None:
    unknown = set(document) - _DOCUMENT_FIELDS
    if unknown:
        raise CounterfactualConfigError(
            f"unknown top-level fields {sorted(unknown)} — unknown fields are rejected (§c.2)"
        )
    missing = _DOCUMENT_FIELDS - set(document)
    if missing:
        raise CounterfactualConfigError(
            f"missing required fields {sorted(missing)} (§c document shape: "
            f"{{schema_version, base_pack_hash, overrides, probe_declarations}})"
        )
    version = document["schema_version"]
    match = _SEMVER.fullmatch(version) if isinstance(version, str) else None
    if match is None:
        raise CounterfactualConfigError(
            f"schema_version {version!r} is not a three-part semver MAJOR.MINOR.PATCH in "
            f"non-negative integers without leading zeros (§c.1: versioned; breaking change = "
            f"major bump). The string is hashed verbatim, so a spelling this validator cannot "
            f"read exactly is not one it may interpret approximately"
        )
    if int(match.group(1)) != _SUPPORTED_MAJOR:
        raise CounterfactualConfigError(
            f"schema_version {version!r} has an unsupported major — this validator implements "
            f"§c schema major {_SUPPORTED_MAJOR} (§c.1)"
        )
    expected = baseline_pack_hash(packs)
    if document["base_pack_hash"] != expected:
        raise CounterfactualConfigError(
            f"base_pack_hash {document['base_pack_hash']!r} does not match the loaded baseline "
            f"pack set ({expected!r}) — the config declares a baseline the engine is not "
            f"running (§c document shape)"
        )


def validate_config(
    document: Mapping[str, Any], packs: Mapping[VillainType, PersonaPack] | None = None
) -> ValidatedConfig:
    """Validate a §c counterfactual config, merge it, and hash it.

    Enforces, in order: the frozen document shape and `base_pack_hash` (§c),
    explicit-null refusal (§c.4), path legality against the §a.2 axis table
    (§c.2) with per-axis bounds and per-persona restrictions, frozen-field probe
    matching (§c.3), the axis-7 co-sweep refusal (§a.2 row 7 — `continue_ref`
    is never co-swept with `call_looseness`, because co-varying them pins their
    ratio and deletes the raise-independence feature), then the §c.5 merge and
    full re-validation, then §a.2 canonicalization and the §c.6 hash.
    """
    if not isinstance(document, Mapping):
        raise CounterfactualConfigError(
            f"config must be a JSON object, got {type(document).__name__} (§c document shape)"
        )
    packs = load_baseline_packs() if packs is None else packs
    _check_document_shape(document, packs)

    declarations = _parse_probe_declarations(document["probe_declarations"])
    raw_overrides = document["overrides"]
    if not isinstance(raw_overrides, Mapping):
        raise CounterfactualConfigError(
            f"`overrides` must be an object keyed by persona, got "
            f"{type(raw_overrides).__name__} (§c document shape)"
        )

    by_name = {str(name): pack for name, pack in packs.items()}
    for decl in declarations:
        if decl.persona not in by_name:
            raise CounterfactualConfigError(
                f"probe declaration names unknown persona {decl.persona!r} "
                f"(known: {sorted(by_name)})"
            )
        for path in decl.paths:
            resolved = resolve_path(by_name[decl.persona], path)
            if resolved.probe_kind != decl.probe_kind:
                raise CounterfactualConfigError(
                    f"probe declaration for {decl.persona!r} kind {decl.probe_kind!r} lists "
                    f"path {path!r}, which is not a {decl.probe_kind!r} frozen field (§c.3)"
                )

    overrides: dict[str, dict[str, float]] = {}
    for persona_name, persona_overrides in raw_overrides.items():
        if persona_name not in by_name:
            raise CounterfactualConfigError(
                f"overrides name unknown persona {persona_name!r} (known: {sorted(by_name)})"
            )
        if not isinstance(persona_overrides, Mapping):
            raise CounterfactualConfigError(
                f"{persona_name}: overrides must be an object mapping dotted paths to numbers, "
                f"got {type(persona_overrides).__name__} (§c document shape)"
            )
        pack = by_name[persona_name]
        resolved_here: dict[str, float] = {}
        buckets: dict[tuple[str, ...], dict[str, float]] = {}
        for path, value in persona_overrides.items():
            number = _require_number(persona_name, path, value)
            resolved = resolve_path(pack, path)
            if resolved.probe_kind is not None:
                _require_probe(persona_name, path, resolved.probe_kind, declarations)
            if resolved.lo is not None and not resolved.lo <= number <= resolved.hi:
                raise CounterfactualConfigError(
                    f"{persona_name}: override {path!r} = {number!r} is outside the §a.2 axis "
                    f"{resolved.axis_number} sweep bounds [{resolved.lo}, {resolved.hi}]"
                )
            if resolved.axis_number == _BUCKET_DIST_AXIS:
                buckets.setdefault(resolved.keys[:-1], {})[resolved.keys[-1]] = number
            resolved_here[path] = number
        _check_bucket_dist_completeness(persona_name, pack, buckets)
        if _CONTINUE_REF in resolved_here and _CALL_LOOSENESS in resolved_here:
            raise CounterfactualConfigError(
                f"{persona_name}: `postflop.continue_ref` and `postflop.call_looseness` are "
                f"overridden together — §a.2 axis 7 forbids co-sweeping them (co-varying pins "
                f"their ratio and deletes the raise-independence feature, so the mechanism "
                f"attribution the probe exists to make is destroyed)"
            )
        overrides[persona_name] = resolved_here

    canonical = canonicalize(
        {
            "schema_version": document["schema_version"],
            "base_pack_hash": document["base_pack_hash"],
            "overrides": overrides,
            "probe_declarations": [d.as_document() for d in declarations],
        },
        packs,
    )
    merged = _apply_overrides(packs, canonical["overrides"])
    return ValidatedConfig(
        schema_version=document["schema_version"],
        base_pack_hash=document["base_pack_hash"],
        overrides=overrides,
        probe_declarations=declarations,
        canonical=canonical,
        config_hash=config_hash(canonical),
        packs=merged,
    )


def _check_bucket_dist_completeness(
    persona: str, pack: PersonaPack, buckets: Mapping[tuple[str, ...], Mapping[str, float]]
) -> None:
    """Weight distributions are *joint* constraints, not k independent dials.

    Both bucket-distribution families in this model — the flat `postflop.sizing`
    simplex (§a.2 axis 13) and each inner distribution of the probe-only
    `postflop.sizing_by_node` — are normalized by construction and validated by
    the SAME `_validate_bucket_dist` (`models.py:145-163`). So the rule is
    stated once and applied to both: overriding any weight of a distribution
    means overriding all of that distribution's authored keys, with the values
    summing to 1 within 1e-3 (the model's own tolerance, `models.py:161`).

    Generalizing rather than exempting the probe family is deliberate. Absent
    this, a correctly-declared single-weight `sizing_by_node` probe would die
    with the raw pydantic sum-to-1 message that names the model instead of the
    rule the author broke — the exact failure mode the rule was created to
    replace. Note this is a NORMALIZATION rule, not a bounds rule: §a.2 declares
    no per-key bounds for the probe family and none are invented (see
    `simplex_bounds`).

    `buckets` is keyed by the resolved CONTAINER path, so grouping never has to
    re-parse a dotted string.
    """
    if not buckets:
        return
    document = _pack_document(pack)
    for container_keys in sorted(buckets):
        touched = buckets[container_keys]
        authored_dist: Any = document
        for key in container_keys:
            authored_dist = authored_dist[key]
        authored = set(authored_dist)
        label = ".".join(container_keys)
        rule = (
            "§a.2 axis 13 stores the post-softmax simplex point, whose keys sum to 1 by "
            "construction"
            if container_keys == ("postflop", "sizing")
            else "a pot-fraction bucket distribution is normalized by construction "
            "(`_validate_bucket_dist`, models.py:145-163)"
        )
        if set(touched) != authored:
            raise CounterfactualConfigError(
                f"{persona}: partial `{label}` override {sorted(touched)} — {rule}, so "
                f"overriding any of its weights requires overriding all {len(authored)} "
                f"authored keys {sorted(authored)}"
            )
        total = math.fsum(touched.values())
        if abs(total - 1.0) > 1e-3:
            raise CounterfactualConfigError(
                f"{persona}: `{label}` override weights sum to {total!r}, not 1.0 within "
                f"1e-3 — {rule}"
            )


def _require_probe(
    persona: str, path: str, kind: str, declarations: Sequence[ProbeDeclaration]
) -> None:
    """§c.3 frozen-field handling: `continue_ref` (and, for sizing probes,
    `sizing_by_node` weights) are accepted ONLY with a matching declaration."""
    for decl in declarations:
        if decl.persona == persona and decl.probe_kind == kind and path in decl.paths:
            return
    if kind == "continue_ref":
        raise CounterfactualConfigError(
            f"{persona}: `{path}` is a frozen calibration anchor — it is its own axis in "
            f"dedicated mechanism probes only (§a.2 axis 7 / §c.3); declare a dedicated probe "
            f"({{probe_kind: 'continue_ref', persona, paths, rationale}}) to sweep it. It is "
            f"frozen because the engine's facing-node raise scale is calibrated against it: "
            f"moving it with the calling dial pins their ratio and deletes the "
            f"raise-independence feature."
        )
    raise CounterfactualConfigError(
        f"{persona}: `{path}` is a `sizing_by_node` weight, frozen at baseline in wave 1 "
        f"(§a.2 exclusions / §c.3) — it becomes a probe axis only under a declared sizing "
        f"probe ({{probe_kind: 'sizing_by_node', persona, paths, rationale}})"
    )


def effective_call_looseness(pack: PersonaPack) -> float:
    """The `call_looseness` this pack behaves as if it had.

    Unset means the engine reads `stickiness` instead (`personas_postflop.py:889`,
    `models.py:171-192`) — the exact fallback the §a.2 canonicalization rule
    exists to make explicit.

    Raises rather than asserts: `python -O` strips asserts, and a silent None
    here would write `call_looseness: null` into a canonical config — exactly
    the "authored key with no lever" the pack model rejects.
    """
    postflop = pack.postflop
    if postflop is None:
        raise CounterfactualConfigError(
            f"{pack.persona}: pack authors no `postflop` block, so the §a.2 canonicalization "
            f"rule (every sweep config materializes `call_looseness` on every persona) cannot "
            f"be applied"
        )
    if postflop.call_looseness is not None:
        return postflop.call_looseness
    if postflop.stickiness is None:
        raise CounterfactualConfigError(
            f"{pack.persona}: neither `call_looseness` nor its `stickiness` fallback is "
            f"authored, so the pack has no effective calling dial to materialize (§a.2 "
            f"canonicalization rule)"
        )
    return postflop.stickiness


def canonicalize(
    document: Mapping[str, Any], packs: Mapping[VillainType, PersonaPack]
) -> dict[str, Any]:
    """Apply the §a.2 canonicalization rule (`estimand-contract.md:142-148`).

    Every sweep config materializes `call_looseness` explicitly on EVERY
    persona at its effective value, so the number that controls call merit can
    never again be the same number that controls price elasticity. Explicit
    overrides win; personas the config never mentions still get the key.

    Note for probe configs: canonicalization writes `call_looseness` at its
    BASELINE value on a `continue_ref` probe persona too. That is not a
    co-sweep — the axis-7 refusal is evaluated on the AUTHORED overrides, where
    a co-sweep would actually move both dials.

    Probe declarations are sorted (and their `paths` sorted) so that authoring
    order never changes a config's identity. `rationale` is part of the sort key
    as well as of the hash: two declarations that agree on kind, persona and
    paths but differ in prose are distinct documents, and leaving prose out of
    the key would let swapping their authored order flip `config_hash`.
    """
    overrides: dict[str, dict[str, float]] = {
        persona: dict(paths) for persona, paths in document["overrides"].items()
    }
    for name, pack in packs.items():
        persona_overrides = overrides.setdefault(str(name), {})
        persona_overrides.setdefault(_CALL_LOOSENESS, float(effective_call_looseness(pack)))
    declarations = [dict(d) for d in document["probe_declarations"]]
    for decl in declarations:
        decl["paths"] = sorted(decl["paths"])
    declarations.sort(
        key=lambda d: (d["probe_kind"], d["persona"], tuple(d["paths"]), d["rationale"])
    )
    return {
        "schema_version": document["schema_version"],
        "base_pack_hash": document["base_pack_hash"],
        "overrides": {p: dict(sorted(v.items())) for p, v in sorted(overrides.items())},
        "probe_declarations": declarations,
    }


# --------------------------------------------------------------------------
# Merge (§c.4/c.5)
# --------------------------------------------------------------------------


# A preflop sizing scalar is only read when the pack authors no mix for that
# lever (`table/sizing._draw_size`). Once T2b gave every pack a mix, overriding
# the scalar changed nothing at all — axes 1 and 2 swept a value the engine
# never consulted, and produced byte-identical play. Setting the scalar
# therefore has to remove whatever shadows it.
_SIZE_MIX_SHADOWS: dict[str, tuple[str, ...]] = {
    "sizing.open_bb": ("open_bb_mix", "open_bb_mix_by_position"),
    "sizing.threebet_mult": ("threebet_mult_mix",),
    "sizing.fourbet_mult": ("fourbet_mult_mix",),
}


def _collapse_shadowing_size_mixes(document: dict, path: str, value: float) -> None:
    """Collapse onto the overridden scalar every size mix that would shadow it.

    Restores the axis's pre-T2b meaning — "this persona opens X bb" — by making
    the mix a single rung at the swept value. Collapsing rather than rescaling
    is deliberate: a swept point should differ from the baseline in the ONE
    declared quantity, and shifting a distribution would move its spread as
    well as its centre, so the sweep could not attribute what it measured.

    Collapsing rather than DELETING is also deliberate, and it is the narrower
    of the two against §c.5. Deleting the mix would change a field's
    presence/absence state, which §c.5 promises it will not; a collapsed mix is
    still present, still validates, and behaves identically to the scalar. Only
    the field's VALUE moves, and only for a field that is definitionally the
    same lever as the one being swept.

    The consequence is real and is recorded in the ticket ledger: a config that
    sweeps axis 1 or 2 gets a persona playing one fixed size at that lever, not
    the shipped distribution. That is what those axes have always meant; what
    changed at T2b is that the baseline is no longer a fixed size either.
    """
    sizing = document.get("sizing", {})
    for key in _SIZE_MIX_SHADOWS.get(path, ()):
        if key not in sizing:
            continue
        if key.endswith("_by_position"):
            sizing[key] = {seat: {str(value): 1.0} for seat in sizing[key]}
        else:
            sizing[key] = {str(value): 1.0}


def _apply_overrides(
    packs: Mapping[VillainType, PersonaPack], overrides: Mapping[str, Mapping[str, float]]
) -> dict[VillainType, PersonaPack]:
    """§c.4/§c.5: SET the overrides on deep copies, then re-validate from
    serialized JSON through the SAME pydantic model the engine loads.

    The deep copy is `model_dump(exclude_unset=True)` — a fresh nested dict that
    shares nothing with the loaded packs and carries exactly the keys the
    authored files set, so every non-overridden field keeps its value AND its
    presence/absence state. No attribute is ever assigned on a pack object:
    §c.5 rejects in-place update precisely because it bypasses validation. No
    file under `content/` is read or written here.

    PRIVATE on purpose. It takes CANONICAL overrides, which carry
    `call_looseness` materialized at each pack's baseline effective value — and
    a baseline value is not required to sit inside the §a.2 *sweep* bounds, so
    this function cannot re-check bounds without risking a refusal of the
    baseline itself. Bounds are enforced once, on the AUTHORED overrides, in
    `validate_config`; making the merge public would open a second door into
    the pack model that skips that check. `validate_config` / `load_config` are
    the supported entry points, and both hand back merged `.packs`.
    """
    merged: dict[VillainType, PersonaPack] = {}
    for name, pack in packs.items():
        document = _pack_document(pack)
        for path, value in overrides.get(str(name), {}).items():
            keys = resolve_path(pack, path).keys
            container: Any = document
            for key in keys[:-1]:
                container = container[key]
            container[keys[-1]] = float(value)
            _collapse_shadowing_size_mixes(document, path, float(value))
        try:
            merged[name] = PersonaPack.model_validate_json(json.dumps(document))
        except ValidationError as exc:
            raise CounterfactualConfigError(
                f"{name}: the merged pack failed full re-validation through the pack model "
                f"(§c.5) — {exc}"
            ) from exc
    return merged


# --------------------------------------------------------------------------
# Entry points the sweep runner and exporter use
# --------------------------------------------------------------------------


def empty_override_config(packs: Mapping[VillainType, PersonaPack]) -> dict[str, Any]:
    """The §c document with no overrides — the baseline config, whose canonical
    form is the canonicalized baseline (§c acceptance test (i))."""
    return {
        "schema_version": SCHEMA_VERSION,
        "base_pack_hash": baseline_pack_hash(packs),
        "overrides": {},
        "probe_declarations": [],
    }


def baseline_config_hash(packs: Mapping[VillainType, PersonaPack] | None = None) -> str:
    """The §c.6 hash of the canonicalized empty-override baseline config.

    This is the `config_hash` every non-counterfactual export stamps: the
    default export path simulates the RAW as-loaded packs and canonicalization
    runs only as this side-channel, which is what keeps acceptance test 1(i) a
    real safety proof rather than a tautology (spec `flywheel-s4.md:44-47`).
    """
    packs = load_baseline_packs() if packs is None else packs
    return validate_config(empty_override_config(packs), packs).config_hash


def load_config(
    path: Path | str, packs: Mapping[VillainType, PersonaPack] | None = None
) -> ValidatedConfig:
    """Read a counterfactual-config JSON file and validate it (§c).

    Configs are ephemeral by definition — never committed (WORKING-AGREEMENT §8).
    """
    text = Path(path).read_text(encoding="utf-8")
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CounterfactualConfigError(f"{path}: not valid JSON ({exc})") from exc
    return validate_config(document, packs)
