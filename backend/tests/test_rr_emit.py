"""RR-EMIT — the build-time `unopened` range emitter and its proving gates.

TWO SPECS ARE PROVED HERE, and they prove different things:
  - `nit.unopened.json` (W5-b3) is a RE-ENCODING of content that already
    shipped; its gate is evidence the model is lossless.
  - `lag.unopened.json` (N-LAGLADDER) is RR-EMIT's first PRODUCTION authoring
    run — the spec came first and `content/personas/lag.json`'s nine `unopened`
    nodes were generated from it. Its gate is the reverse guarantee: the
    committed pack has not drifted away from the spec that is supposed to
    generate it, so `python -m tools.rr_emit content/personas/ladders/
    lag.unopened.json` stays the way that ladder is edited.
Both are the same assertion in code, run in both directions of authorship.

THE PROVING GATE (`test_proving_gate_*`): the emitter, fed the nit curve spec
checked in at `content/personas/ladders/nit.unopened.json`, reproduces the
SHIPPED nit nine-seat `unopened` ladder (W5-b3, PR #145) semantically
identically — same node order, same seat, same mix order, same weights, and
per-mix set-equality of the parsed hand classes. Comparison is at the
`parse_range` level on purpose: the gate is "did any hand class change
treatment", not "did the text match", so a legitimate difference in token
spelling can never be mistaken for a behaviour change (and, equally, identical
text can never hide a semantic one).

The gate is evidence that the spec and the pack say the SAME thing, not a
target to force: it fails if either drifts from the other. RR-EMIT authored it
against an untouched `content/personas/nit.json`; T-M2 (2026-07-31) is the
first slice to move both TOGETHER — the CO/BTN pair-open band is authored in
the spec's tiers and hand-mirrored into the pack, and this gate is what proves
the two edits agree class-by-class and weight-by-weight.

The remaining tests pin the properties that make the emitter usable as an
authoring surface: its output satisfies the RR-LINT structural belt with ZERO
defects (holes, dead tokens and weight interleaving are unrepresentable by
construction, not merely absent here), emission is deterministic, the emitted
nodes are legal `PersonaNode`s, and the authored ladder is strictly increasing
toward the button over the seats the spec declares monotone (the blinds are
excluded — they sit on their own curve, and a ladder must never be forced on a
persona whose realism says otherwise).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_pack_range_lint import _rows

from app.domain.content.models import PersonaNode
from app.domain.content.notation import parse_range
from tools.rr_emit import emit_json, emit_nodes

CONTENT = Path(__file__).resolve().parents[2] / "content"
SPEC_PATH = CONTENT / "personas" / "ladders" / "nit.unopened.json"
# Review fold (Codex L3): the pack path is derived from the spec's own `emits`
# declaration, so the metadata is audited by the gate instead of being dead —
# repointing `emits` at another pack now fails the proving tests.
PACK_PATH = CONTENT.parent / json.loads(SPEC_PATH.read_text(encoding="utf-8"))["emits"]


def test_spec_emits_the_runtime_nit_pack():
    """Review fold (Codex MED): deriving PACK_PATH from `emits` audits the
    metadata, but it also means the whole proving suite follows `emits`
    wherever it points — a spec repointed at a scratch copy would keep every
    gate green while the pack the ENGINE loads drifted. Pin the destination to
    the file `load_persona_packs` actually globs."""
    assert PACK_PATH.resolve() == (CONTENT / "personas" / "nit.json").resolve()


def _combos(cls: str) -> int:
    """Combos in a starting-hand class: 6 for a pair, 4 suited, 12 offsuit."""
    if len(cls) == 2:
        return 6
    return 4 if cls.endswith("s") else 12


def _load_spec() -> dict:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def emitted() -> list[dict]:
    return emit_nodes(_load_spec())


@pytest.fixture(scope="module")
def shipped() -> list[dict]:
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    return [n for n in pack["preflop"] if n["facing"] == "unopened"]


def _raise_width_pct(node: dict) -> float:
    """Combo-weighted raise width of one node, in % of the 1326 combos."""
    total = 0.0
    for mix in node["mixes"]:
        weight = mix["weights"].get("raise", 0.0)
        if not weight:
            continue
        for cls in parse_range(mix["combos"]):
            total += weight * _combos(cls)
    return 100.0 * total / 1326.0


# ============================================================ THE PROVING GATE


def test_proving_gate_seat_list_matches_shipped_nit(emitted, shipped):
    assert [n["positions"] for n in emitted] == [n["positions"] for n in shipped]
    assert all(n["facing"] == "unopened" for n in emitted)


def test_proving_gate_nit_unopened_is_semantically_identical(emitted, shipped):
    """Per seat, per mix, in order: same classes (parsed) and same weights."""
    for emit_node, ship_node in zip(emitted, shipped, strict=True):
        seat = ship_node["positions"][0]
        assert len(emit_node["mixes"]) == len(ship_node["mixes"]), (
            f"{seat}: emitted {len(emit_node['mixes'])} mixes, "
            f"shipped {len(ship_node['mixes'])}"
        )
        for i, (emit_mix, ship_mix) in enumerate(
            zip(emit_node["mixes"], ship_node["mixes"], strict=True)
        ):
            emit_classes = parse_range(emit_mix["combos"])
            ship_classes = parse_range(ship_mix["combos"])
            assert emit_classes == ship_classes, (
                f"{seat} mix {i}: only-shipped={sorted(ship_classes - emit_classes)} "
                f"only-emitted={sorted(emit_classes - ship_classes)} "
                f"({ship_mix['combos']!r} -> {emit_mix['combos']!r})"
            )
            assert emit_mix["weights"] == ship_mix["weights"], f"{seat} mix {i}"


def test_proving_gate_covers_every_shipped_hand_class(emitted, shipped):
    """Belt on the gate itself: a mismatch must be impossible to pass by
    emitting an EMPTY ladder, so assert the corpus is actually non-trivial."""
    def union(nodes):
        return {
            cls
            for node in nodes
            for mix in node["mixes"]
            for cls in parse_range(mix["combos"])
        }

    played = union(shipped)
    assert len(played) == 57, "shipped nit unopened corpus changed size"
    assert union(emitted) == played
    # T-M2: 28, not 27 — seven seats emit three mixes (the pair-open tier is
    # width 0 there and drops out), CO emits four (pair-open 55-77 AND the
    # 22-44 remainder) and BTN three (its pair-open band swallows the whole
    # 22-77 remainder, so the limp-only mix drops out). The corpus above is
    # unchanged: no pair class gained or lost a treatment, three changed tier.
    assert sum(len(n["mixes"]) for n in emitted) == 28


# ================================================== STRUCTURE / LEGALITY BELTS


def test_emitted_nodes_are_legal_persona_nodes(emitted):
    for node in emitted:
        PersonaNode.model_validate(node)


def test_emitted_output_has_zero_lint_belt_defects(emitted):
    """The three RR-LINT lints, run over the emitted nodes: row gaps, inert
    tokens and weight interleaving must all be EMPTY. These are properties of
    the emitter's partition, not of the nit spec — no spec can produce them."""
    gaps: list[tuple] = []
    inert: list[tuple] = []
    interleave: list[tuple] = []
    for node in emitted:
        seat = node["positions"][0]
        covered: set[str] = set()
        for mix in node["mixes"]:
            for tok in (t.strip() for t in mix["combos"].split(",")):
                tset = parse_range(tok)
                if tset and tset <= covered:
                    inert.append((seat, tok))
                covered |= tset
        for rname, ordered in _rows():
            missing_stronger = tuple(
                cls
                for idx, cls in enumerate(ordered)
                if cls not in covered and any(c in covered for c in ordered[idx + 1 :])
            )
            if missing_stronger:
                gaps.append((seat, rname, missing_stronger))
        prev: dict[str, float] = {}
        for mix in node["mixes"]:
            nonfold = {a: w for a, w in mix["weights"].items() if a != "fold"}
            if not nonfold:
                continue
            peak = max(nonfold.values())
            for act in sorted(a for a, w in nonfold.items() if w >= peak - 1e-9):
                if act in prev and nonfold[act] > prev[act] + 1e-9:
                    interleave.append((seat, act, prev[act], nonfold[act]))
                prev[act] = nonfold[act]
    assert gaps == [], f"emitted row gaps: {gaps}"
    assert inert == [], f"emitted inert tokens: {inert}"
    assert interleave == [], f"emitted weight interleaving: {interleave}"


# =========================================================== DETERMINISM / FIT


def test_emission_is_byte_deterministic():
    """Same spec -> byte-identical output, and emitting does not mutate the
    spec (each run reloads from disk, so a stateful emitter would diverge)."""
    first = emit_json(_load_spec())
    assert emit_json(_load_spec()) == first
    spec = _load_spec()
    assert emit_json(spec) == first
    assert emit_json(spec) == first
    assert first.endswith("\n") and "\n \n" not in first


def test_ladder_widths_strictly_increase_toward_the_button(emitted):
    spec = _load_spec()
    by_seat = {n["positions"][0]: n for n in emitted}
    widths = [_raise_width_pct(by_seat[s]) for s in spec["monotone_seats"]]
    assert widths == sorted(widths) and len(set(widths)) == len(widths), (
        f"nit ladder not strictly increasing over {spec['monotone_seats']}: "
        f"{[round(w, 2) for w in widths]}"
    )


def test_authored_raise_pct_annotations_match_emitted_widths(emitted):
    """`raise_pct` is documentation the emitter never reads — assert it is
    honest, so it can never quietly become a fitted width parameter."""
    spec = _load_spec()
    for node in emitted:
        seat = node["positions"][0]
        assert _raise_width_pct(node) == pytest.approx(
            spec["seats"][seat]["raise_pct"], abs=0.005
        ), seat


# --- validator hardening (RR-EMIT fan-in review folds) ----------------------
# The module docstring claims three defect classes are UNREPRESENTABLE. That
# claim is only as strong as the input gate, so the gate is negatively tested:
# each spec below was a reproduced escape (refuter: negative slope width rolled
# `taken` backwards and re-claimed core-owned classes; Codex: a vs_rfi spec
# sailed through the unopened-only fence) or a raw-KeyError crash path.


def _bad(mutate):
    spec = _load_spec()
    mutate(spec)
    with pytest.raises(ValueError):
        emit_nodes(spec)


def _tier(spec: dict, kind: str) -> dict:
    """First tier of `kind`. Addressing tiers by KIND, not list index (T-M2):
    the nit spec's tier list changed shape when the pairs row was demoted from
    `tail` to two per-seat slope tiers, and index-addressed mutations silently
    stopped testing what they named (a `width` set on the `core` tier is simply
    ignored, so the negative-width probe passed vacuously)."""
    return next(t for t in spec["tiers"] if t["kind"] == kind)


# The nit spec no longer uses a `tail` tier (T-M2), so the tail probes below
# APPEND one rather than mutating the spec's own — the emitter still supports
# the kind, and these are validator tests, not nit-content tests.
def _tail(rows: list[str]) -> dict:
    return {"kind": "tail", "rows": rows, "weights": {"fold": 1.0}}


def test_validator_rejects_negative_slope_width():
    _bad(lambda s: _tier(s, "slope").__setitem__("width", -2))


def test_validator_rejects_non_unopened_facing():
    _bad(lambda s: s.__setitem__("facing", "vs_rfi"))


def test_validator_rejects_response_action_vocabulary():
    _bad(lambda s: _tier(s, "core").__setitem__("weights", {"call": 1.0}))


def test_validator_rejects_missing_tier_keys_loudly():
    _bad(lambda s: _tier(s, "slope").pop("width"))
    _bad(lambda s: _tier(s, "core").pop("weights"))
    _bad(lambda s: s["tiers"].append({"kind": "tail", "weights": {"fold": 1.0}}))


def test_validator_rejects_duplicate_tail_ownership():
    _bad(lambda s: s["tiers"].extend([_tail(["pairs"]), _tail(["pairs"])]))


def test_validator_rejects_overweight_mix():
    _bad(lambda s: _tier(s, "core").__setitem__("weights", {"raise": 0.7, "fold": 0.7}))


def test_validator_rejects_a_seat_missing_mandatory_slope_widths():
    """🔴 Negative control for the T-M2 review fold (refuter I2): a row driven
    entirely by per-seat slope widths (`required_slopes`) TRUNCATES silently if
    one seat omits its entry — the tiers fall back to their defaults, the row's
    bottom goes unplayed, and no downstream lint can see it (a short row bottom
    is not a row gap). Dropping `slopes.pairs` from a seat must now raise.

    Pre-fold behaviour, reproduced with the validator's new check disabled:
    dropping BB's `slopes.pairs` emitted a two-mix BB node — the limp band was
    GONE (22-66 unplayed, i.e. fold 1.0) and the `edge` tier had swallowed 77
    into its raise-0.5 mix, because both tiers fell back to their default
    widths (0 and 1)."""
    _bad(lambda s: s["seats"]["BB"]["slopes"].pop("pairs"))
    _bad(lambda s: s["seats"]["CO"].pop("slopes"))


def test_validator_rejects_unknown_required_slope_row():
    _bad(lambda s: s.__setitem__("required_slopes", ["quads"]))


# ====================================== N-LAGLADDER — the lag production spec
# Same gate, opposite direction of authorship (see the module docstring): the
# lag spec GENERATED the pack, so this asserts the committed pack is still what
# the spec emits. A hand-edit to lag.json's `unopened` nodes that forgets the
# spec fails here, which is what keeps the spec from rotting into a fiction.

LAG_SPEC_PATH = CONTENT / "personas" / "ladders" / "lag.unopened.json"
LAG_PACK_PATH = CONTENT.parent / json.loads(
    LAG_SPEC_PATH.read_text(encoding="utf-8")
)["emits"]


def _load_lag_spec() -> dict:
    return json.loads(LAG_SPEC_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def lag_emitted() -> list[dict]:
    return emit_nodes(_load_lag_spec())


@pytest.fixture(scope="module")
def lag_shipped() -> list[dict]:
    pack = json.loads(LAG_PACK_PATH.read_text(encoding="utf-8"))
    return [n for n in pack["preflop"] if n["facing"] == "unopened"]


def test_lag_proving_gate_seat_list_matches_shipped(lag_emitted, lag_shipped):
    assert [n["positions"] for n in lag_emitted] == [
        n["positions"] for n in lag_shipped
    ]
    assert all(n["facing"] == "unopened" for n in lag_emitted)


def test_lag_proving_gate_unopened_is_semantically_identical(lag_emitted, lag_shipped):
    """Per seat, per mix, in order: same classes (parsed) and same weights."""
    for emit_node, ship_node in zip(lag_emitted, lag_shipped, strict=True):
        seat = ship_node["positions"][0]
        assert len(emit_node["mixes"]) == len(ship_node["mixes"]), (
            f"{seat}: emitted {len(emit_node['mixes'])} mixes, "
            f"shipped {len(ship_node['mixes'])}"
        )
        for i, (emit_mix, ship_mix) in enumerate(
            zip(emit_node["mixes"], ship_node["mixes"], strict=True)
        ):
            emit_classes = parse_range(emit_mix["combos"])
            ship_classes = parse_range(ship_mix["combos"])
            assert emit_classes == ship_classes, (
                f"{seat} mix {i}: only-shipped={sorted(ship_classes - emit_classes)} "
                f"only-emitted={sorted(emit_classes - ship_classes)} "
                f"({ship_mix['combos']!r} -> {emit_mix['combos']!r})"
            )
            assert emit_mix["weights"] == ship_mix["weights"], f"{seat} mix {i}"


def test_lag_proving_gate_corpus_is_non_trivial(lag_emitted, lag_shipped):
    """Belt on the gate itself (the nit gate's rule): a mismatch must not be
    passable by emitting an empty ladder."""
    def union(nodes):
        return {
            cls
            for node in nodes
            for mix in node["mixes"]
            for cls in parse_range(mix["combos"])
        }

    played = union(lag_shipped)
    assert len(played) == 133, "shipped lag unopened corpus changed size"
    assert union(lag_emitted) == played
    assert sum(len(n["mixes"]) for n in lag_emitted) == 18  # 9 seats x 2 tiers


def test_lag_emitted_nodes_are_legal_persona_nodes(lag_emitted):
    for node in lag_emitted:
        PersonaNode.model_validate(node)


def test_lag_emission_is_byte_deterministic():
    first = emit_json(_load_lag_spec())
    assert emit_json(_load_lag_spec()) == first
    assert first.endswith("\n") and "\n \n" not in first


def test_lag_ladder_widths_strictly_increase_toward_the_button(lag_emitted):
    spec = _load_lag_spec()
    by_seat = {n["positions"][0]: n for n in lag_emitted}
    widths = [_raise_width_pct(by_seat[s]) for s in spec["monotone_seats"]]
    assert widths == sorted(widths) and len(set(widths)) == len(widths), (
        f"lag ladder not strictly increasing over {spec['monotone_seats']}: "
        f"{[round(w, 2) for w in widths]}"
    )


def test_lag_authored_raise_pct_annotations_match_emitted_widths(lag_emitted):
    """`raise_pct` is documentation the emitter never reads — assert it is
    honest, so it can never quietly become a fitted width parameter."""
    spec = _load_lag_spec()
    for node in lag_emitted:
        seat = node["positions"][0]
        assert _raise_width_pct(node) == pytest.approx(
            spec["seats"][seat]["raise_pct"], abs=0.005
        ), seat
