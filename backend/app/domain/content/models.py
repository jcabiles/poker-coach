"""ContentPack models — the strategy-as-data contract.

Entry format is locked for mixed strategies from day 1: each entry's `actions`
is a list of {action, combos, frequency}. The heuristic provider sets
frequency=1.0 on its dominant action; a solver provider later fills true mixed
frequencies with NO format change.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.archetypes import VillainType
from app.domain.content.notation import parse_range
from app.domain.evaluation import ReasoningParts
from app.domain.spot import ActionType, NodeContext, Position

# The 8 frontend drill Mode values (frontend/src/api/types.ts::Mode /
# frontend/src/lib/hashRoute.ts::MODE_IDS) that a card's "drill this" link can
# navigate to via hash routing (#/drill/<mode>). Kept in sync manually with
# the FE, same convention as the rest of the hand-maintained wire types.
DrillMode = Literal[
    "random",
    "review",
    "leak_focus",
    "exploit",
    "challenge",
    "postflop",
    "vs_cbet",
    "vs_check_raise",
]


class ActionRange(BaseModel):
    action: ActionType
    combos: str  # range-notation string (see notation.parse_range)
    frequency: float = Field(default=1.0, ge=0.0, le=1.0)


class Entry(BaseModel):
    node_context: NodeContext
    position: Position
    facing: Position | None = None  # opener / 3-bettor position when relevant
    limper_count: int | None = None  # for vs_limpers entries
    villain_type: VillainType | None = None  # set for exploit-overlay entries
    rationale: str | None = None  # flat one-paragraph "why" (legacy authored prose)
    # Structured authored "why" (feedback-prose-readability): lead sentence +
    # supporting bullet points + demoted doc citations. When present it WINS
    # over the flat `rationale` — rewritten entries carry only this field.
    # Consumers never read `rationale` directly; they go through
    # `rationale_text` / `rationale_parts` so both entry generations work.
    rationale_parts: ReasoningParts | None = None
    actions: list[ActionRange]
    sizing_bb: float | None = None

    @property
    def rationale_text(self) -> str | None:
        """The flat authored prose: the join of the structured parts when
        present (sources excluded — they never enter the readable text),
        else the legacy flat `rationale`."""
        if self.rationale_parts is not None:
            return " ".join([self.rationale_parts.lead, *self.rationale_parts.points])
        return self.rationale


class ContentPack(BaseModel):
    id: str
    version: int
    domain: str
    description: str = ""
    entries: list[Entry] = Field(default_factory=list)
    sizing_rules: dict = Field(default_factory=dict)
    exploit_overlays: dict = Field(default_factory=dict)  # freeform stub in Phase 0/1


# Persona packs (Simulate S3) — bot preflop strategy as data. Action-name
# vocabulary is per node facing; names are CONTENT-level (limp/3bet/...) and
# translated to wire ActionType by the engine (app/domain/personas.py).
PersonaFacing = Literal["unopened", "vs_limpers", "vs_rfi", "vs_3bet", "vs_4bet"]

_FACING_ACTIONS: dict[str, frozenset[str]] = {
    "unopened": frozenset({"fold", "limp", "raise"}),
    "vs_limpers": frozenset({"fold", "limp", "raise"}),  # limp = over-limp
    "vs_rfi": frozenset({"fold", "call", "3bet"}),
    "vs_3bet": frozenset({"fold", "call", "4bet"}),
    "vs_4bet": frozenset({"fold", "call", "5bet_shove"}),
}


class PersonaActionMix(BaseModel):
    combos: str  # range-notation string (see notation.parse_range)
    # action-name -> probability; sum <= 1.0; remainder is an implicit fold.
    weights: dict[str, float]

    @field_validator("combos")
    @classmethod
    def _combos_parse(cls, v: str) -> str:
        parse_range(v)  # raises ValueError on unsupported notation tokens
        return v

    @field_validator("weights")
    @classmethod
    def _weights_valid(cls, v: dict[str, float]) -> dict[str, float]:
        for name, w in v.items():
            if not 0.0 <= w <= 1.0:
                raise ValueError(f"weight for {name!r} out of [0, 1]: {w}")
        if sum(v.values()) > 1.0 + 1e-9:
            raise ValueError(f"weights sum to {sum(v.values())} > 1.0")
        return v


class PersonaNode(BaseModel):
    facing: PersonaFacing
    positions: list[Position] | None = None  # None = wildcard (any position)
    # N-3BSTRATA: the ARRIVAL STRATUM this node serves. One `vs_3bet` node
    # historically served two different situations — the OPENER (this seat
    # raised, got 3-bet, acts again) and a COLD facer (never raised; faces an
    # open AND a 3-bet on its first decision) — whose ranges are not
    # comparable, so one weight table cannot fold cold junk without
    # over-folding the opener. `None` = serves BOTH strata (every untagged
    # pack keeps today's behaviour exactly; see personas.sample_preflop_action).
    role: Literal["opener", "cold"] | None = None
    mixes: list[PersonaActionMix]  # FIRST MATCH WINS; unmatched hand-class => fold 1.0

    @model_validator(mode="after")
    def _action_vocabulary(self) -> PersonaNode:
        allowed = _FACING_ACTIONS[self.facing]
        for mix in self.mixes:
            bad = set(mix.weights) - allowed
            if bad:
                raise ValueError(f"actions {sorted(bad)} not allowed facing {self.facing!r}")
        return self


class PersonaSizing(BaseModel):
    """Authored in S3, consumed in S4 (the S3 engine ignores it)."""

    open_bb: float
    threebet_mult: float
    fourbet_mult: float


def _validate_bucket_dist(v: dict[str, float]) -> dict[str, float]:
    """A pot-fraction bucket distribution: float keys > 0, weights > 0, sum ~1.0.
    Shared by the flat `sizing` field and each inner dist of `sizing_by_node`."""
    if not v:
        raise ValueError("sizing must be non-empty")
    total = 0.0
    for key, weight in v.items():
        try:
            frac = float(key)
        except ValueError:
            raise ValueError(f"sizing key {key!r} is not a float pot fraction") from None
        if frac <= 0.0:
            raise ValueError(f"sizing fraction {key!r} must be > 0")
        if weight <= 0.0:
            raise ValueError(f"sizing weight for {key!r} must be > 0")
        total += weight
    if abs(total - 1.0) > 1e-3:
        raise ValueError(f"sizing weights sum to {total}, expected ~1.0")
    return v


class PersonaPostflop(BaseModel):
    """Postflop lever block (S4) — every persona-differentiating number lives
    here; the shared mechanics live in app/domain/personas_postflop.py."""

    aggression: float = Field(gt=0.0)  # scales bet/raise merit (1.0 = neutral)
    # T-STICKY: `stickiness` is a FALLBACK, read only where a split lever is
    # unset (call merit when `call_looseness` is None; the price exponent when
    # `size_elasticity` is None). The validator below makes authorship honest:
    # required while any fallback path is live, FORBIDDEN once both split
    # levers are authored — a value there would be dead weight that lies about
    # controlling behaviour.
    #
    # N-LOGIT correction (2026-08-02, ledger R-4 / R2-9): "read only where a
    # split lever is unset" is still true of the READ, but the *reach* of the
    # call-merit read grew. The facing node now also scales the RAISE merit by
    # `effective_looseness / continue_ref` (see `continue_ref` below), and for
    # a pack whose `call_looseness` is unset the effective looseness IS
    # `stickiness` — so on `maniac` this field moves the raise leg as well as
    # the call leg. Two live consequences: editing maniac's `stickiness` for
    # price-elasticity reasons silently desynchronises its calibration anchor
    # from its lever, and maniac's effective looseness cannot be swept in
    # isolation (a sweep must author `call_looseness` on the probe copy).
    stickiness: float | None = Field(default=None, gt=0.0)
    # W2-a: the `stickiness` axis split into two independent identity levers.
    # Both OPTIONAL — unset falls back to `stickiness`, keeping un-opted-in packs
    # byte-identical (default-off contract). `call_looseness` is the flat CALL-merit
    # multiplier; `size_elasticity` drives the price-response exponent DIRECTLY
    # (0.0 = size-blind/flat, higher = steeper fold-rise with bet size) — a distinct
    # scale from stickiness, NOT the legacy inverse power. This lets a station be
    # inelastic-but-loose (calls any size) while a fish is elastic-but-scared.
    # flat call multiplier; None → stickiness
    call_looseness: float | None = Field(default=None, gt=0.0)
    # direct price exponent; 0 = size-blind; None → legacy stickiness formula
    size_elasticity: float | None = Field(default=None, ge=0.0)
    # N-LOGIT: the effective `call_looseness` this persona's FACING-NODE raise
    # behaviour was calibrated against. The engine scales the RAISE merit by
    # `effective_looseness / continue_ref` immediately before the facing-node
    # normalization, which makes `P(raise | continue)` independent of the
    # calling lever: `call_looseness` then controls WHETHER the bot continues
    # and the raise-side calibration controls HOW, so mass freed from CALL
    # routes to FOLD instead of RAISE (roadmap R10-4).
    #
    # FROZEN BY DESIGN — it must NOT be updated when `call_looseness` is tuned.
    # Re-synchronising the two pins the ratio at 1.0 forever, which reproduces
    # the rev-1 cancellation and silently deletes this feature (ledger R-1,
    # R2-6). A looseness FIT never touches this number; only an explicit
    # re-calibration of the raise side may.
    #
    # `ge=0.05`, NOT `gt=0.0`: the dangerous end is near zero, not above 8. The
    # smallest subnormal `5e-324` passes `gt=0.0` and makes the scale `inf`,
    # emitting `[0.0, 0.0, nan]`; `1e-8` validates and yields a degenerate
    # `P(raise) ≈ 0.99999997`. `le=8.0` is 2x the largest shipped value
    # (calling_station 4.0). Validation is not sufficient on its own —
    # `model_copy(update=...)` bypasses it entirely — so `personas_postflop`
    # carries a runtime guard at the division site as well.
    continue_ref: float | None = Field(default=None, ge=0.05, le=8.0)
    # W3-b (B1, F1): how strongly this persona's aggressor-side c-bet/barrel
    # frequency swings with position. 0.0 (or None) = position-blind (an intended
    # leak for stations/fish/maniac); 1.0 = full IP-boost / OOP-damp. Scales a
    # symmetric multiplier on the WHOLE aggressive candidate (bluff + value +
    # semi-bluff) in the unopened/betting branch only — the OOP continue/defense
    # damp is a separate later slice. None → 0.0, keeping un-opted packs identical.
    # Bounded to [0, 1] so the symmetric OOP multiplier 1 − 0.25·s stays strictly
    # positive — a larger s would drive it <= 0 and silently zero every OOP bet.
    position_sensitivity: float | None = Field(default=None, ge=0.0, le=1.0)
    # R9-DEFENCE-a: how strongly this persona folds to a hostile LINE
    # (repeated aggression across streets), not just the current bet's size.
    # `personas_postflop._line_scaled` scales the CALL and RAISE merits at an
    # in-scope facing-chips node by `exp(-λ·line)`, where
    # `λ = _LINE_DELTA · line_sensitivity`. Absence = line-blind
    # and byte-identical; all six shipped packs opt in, so the un-opted path
    # is for third-party packs, not for a roster archetype. A LOW seed is an
    # archetype, NOT a leak: calling_station's 0.10 IS the line-blind
    # call-down. Bounded to [0, 2] because at `_LINE_DELTA = 1.0` that ceiling
    # already cuts the continue-odds by >= 7x — far outside the fitted region,
    # which is what a bound is for.
    line_sensitivity: float | None = Field(default=None, ge=0.0, le=2.0)
    bluff_freq: float = Field(ge=0.0, le=1.0)  # baseline bet/raise rate with air
    sizing: dict[str, float]  # pot-fraction str -> weight; weights sum to ~1
    # R2: optional per-node override, keyed by postflop node name (e.g.
    # "cbet_dry") -> its own bucket distribution. Falls back to flat `sizing`
    # for any node absent here. Node-key strings are NOT pot fractions.
    sizing_by_node: dict[str, dict[str, float]] | None = None
    spr_commit: float = Field(gt=0.0)  # SPR at/below which strong+ hands commit
    multiway_bluff_damp: float = Field(ge=0.0, le=1.0)  # per extra opponent

    @model_validator(mode="after")
    def _stickiness_authorship(self) -> PersonaPostflop:
        """Both directions of the fallback contract (T-STICKY):
        (i) any unset split lever means the engine reads `stickiness` at sample
        time — it must be authored, or the fallback dereferences None;
        (ii) both split levers authored means `stickiness` is provably unread —
        it must be absent, so a dead value can never masquerade as a lever.

        N-LOGIT note: (ii) is unchanged, but "unread" now means unread by the
        call merit, the price exponent AND the facing-node raise scale, since
        that scale's numerator is the same effective looseness."""
        split_complete = self.call_looseness is not None and self.size_elasticity is not None
        if not split_complete and self.stickiness is None:
            raise ValueError(
                "stickiness is required while call_looseness or size_elasticity "
                "is unset (the engine falls back to it)"
            )
        # Key PRESENCE, not value: an explicitly-authored `"stickiness": null`
        # is still an authored key lying about being a lever (review C-1).
        if split_complete and "stickiness" in self.model_fields_set:
            raise ValueError(
                "stickiness must be absent when both call_looseness and "
                "size_elasticity are authored (it would be unread dead weight)"
            )
        return self

    @model_validator(mode="after")
    def _continue_ref_authorship(self) -> PersonaPostflop:
        """N-LOGIT: field ABSENCE is the legacy opt-out — an un-opted pack runs
        HEAD's code path unmodified. An explicit `"continue_ref": null` is an
        authored key that claims a calibration anchor and supplies none, so it
        is rejected. Key PRESENCE, not value — the same rule `stickiness`
        already uses (review C-1)."""
        if self.continue_ref is None and "continue_ref" in self.model_fields_set:
            raise ValueError(
                "continue_ref must be ABSENT rather than null when a pack does "
                "not opt in (an explicit null authors a key with no anchor)"
            )
        return self

    @model_validator(mode="after")
    def _line_sensitivity_authorship(self) -> PersonaPostflop:
        """R9-DEFENCE-a T1: field ABSENCE is the legacy opt-out — an un-opted
        pack runs line-blind. An explicit `"line_sensitivity": null` is an
        authored key that claims a dial and supplies none, so it is rejected.
        Key PRESENCE, not value — the same rule `stickiness` and
        `continue_ref` already use (review C-1)."""
        if self.line_sensitivity is None and "line_sensitivity" in self.model_fields_set:
            raise ValueError(
                "line_sensitivity must be ABSENT rather than null when a pack "
                "does not opt in (an explicit null authors a key with no dial)"
            )
        return self

    @field_validator("sizing")
    @classmethod
    def _sizing_valid(cls, v: dict[str, float]) -> dict[str, float]:
        return _validate_bucket_dist(v)

    @field_validator("sizing_by_node")
    @classmethod
    def _sizing_by_node_valid(
        cls, v: dict[str, dict[str, float]] | None
    ) -> dict[str, dict[str, float]] | None:
        if v is None:
            return v
        for dist in v.values():  # keys are node-name strings, not floats
            _validate_bucket_dist(dist)
        return v


class PersonaPack(BaseModel):
    id: str  # "persona_passive_fish" etc.
    version: str
    domain: Literal["persona"]
    persona: VillainType  # the acting identity
    display_name: str
    sizing: PersonaSizing
    preflop: list[PersonaNode]
    postflop: PersonaPostflop | None = None  # required in all 6 shipped packs

    @model_validator(mode="after")
    def _node_ordering(self) -> PersonaPack:
        """Per (facing, role): explicit-position nodes BEFORE the (at most one)
        wildcard, and explicit-position nodes may not overlap positions (lookup is
        first-match-in-list-order; see personas.sample_preflop_action).

        N-3BSTRATA: the laws above hold INDEPENDENTLY per role stratum — an
        `opener` and a `cold` node may both be position-wildcards for the same
        facing, which is the whole point of the split. One law crosses strata:
        a role-tagged node may not FOLLOW an untagged node of the same facing,
        because an untagged node serves both strata and would shadow it dead.
        """
        seen_positions: dict[tuple[str, str | None], set[Position]] = {}
        wildcard_seen: set[tuple[str, str | None]] = set()
        untagged_seen: set[str] = set()
        for node in self.preflop:
            key = (node.facing, node.role)
            if node.role is None:
                untagged_seen.add(node.facing)
            elif node.facing in untagged_seen:
                raise ValueError(
                    f"role-tagged node after untagged node facing {node.facing!r} "
                    f"(the untagged node serves both roles and shadows it)"
                )
            if node.positions is None:
                if key in wildcard_seen:
                    raise ValueError(f"more than one wildcard node facing {node.facing!r}")
                wildcard_seen.add(key)
                continue
            if key in wildcard_seen:
                raise ValueError(
                    f"explicit-position node after wildcard facing {node.facing!r}"
                )
            prior = seen_positions.setdefault(key, set())
            overlap = prior & set(node.positions)
            if overlap:
                raise ValueError(
                    f"duplicate position coverage facing {node.facing!r}: {sorted(overlap)}"
                )
            prior.update(node.positions)
        return self


class ConceptCard(BaseModel):
    """Point-of-need teaching content (N8), versioned JSON under content/cards/.

    Matching (leak_category first, rationale_tags to disambiguate) lives in
    app/services/concept_cards.py, NOT here — this model is pure content-data,
    same as ContentPack/Entry above.
    """

    id: str
    version: int
    title: str
    summary: str  # 2-3 sentences, shown collapsed
    body: str  # a few short paragraphs, shown expanded
    leak_categories: list[int]  # LeakCategory ints this card can answer
    rationale_tags: list[str] = Field(default_factory=list)  # disambiguators; [] = leak-only match
    drill_mode: DrillMode  # where "drill this" navigates (#/drill/<mode>)
    source_doc: str  # docs/research/<source_doc>-*.md this card distills
