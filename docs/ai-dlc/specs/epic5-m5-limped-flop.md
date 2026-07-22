# Spec — M5: HU limped-pot flop grader (RES-G Slice C)

**Wave 1** (parallel with M4). Branch: `feat/epic5-m4-m5` off `main`.

## Goal
The app's FIRST limped-pot postflop grader — **heads-up only** (the tractable 31% of limped flops).
Grade hero leading a 0-raise HU limped flop, and hero facing a lead. Spike LAW:
`RES-G-limped-pots.md` §4b (directions) + §6-C (pass/fail). EVs approximate, heuristic-only.

## Files / interfaces
- `backend/app/domain/table/grade_map_postflop.py` — **append**:
  - a limped-flop preflop gate (`_limped_flop_hu_preflop` or similar): accepts a **0-raise** pot
    (no preflop raise — all limps + blind checks), hero in it, gated on **PREFLOP ENTRANT COUNT == 2**
    — derived from PREFLOP actions, NOT current flop statuses (mirror `_mw_srp_preflop`'s
    "derived from preflop actions" pattern). A true HU-limped shape = SB-complete-vs-BB or a single
    limper folded around to one caller (RES-G §1b defines HU-limped this way). **Explicit scope
    decision (refuter MED):** a 3+-preflop-limper pot that *degrades* to 2-live by hero's turn is
    **OUT of scope → `None`** (do NOT copy M4's degrade-to-2-live-with-dead-money pattern here; a
    limped multiway flop stays "no baseline yet" regardless of later folds). Any pot with ≥3 preflop
    entrants → `None`.
  - `map_limped_flop_lead(state, hero_seat) -> Spot | None` — hero first-to-act OOP/IP can lead.
  - `map_limped_flop_vs_lead(state, hero_seat) -> Spot | None` — hero faces a villain lead.
- `backend/app/domain/postflop.py` — **append** the limped-flop grader(s). Directions per §4b:
  **small polar lead** (bet strong + some air, check the middle), **mostly-check OOP**, texture
  decides the edge from a `score=0` no-baseline start. Reuse `range_advantage_defender`'s
  no-baseline start + the existing `_apply_multiway`/`_MW_THIN_VALUE_DAMPEN` dampeners (though HU →
  `is_multiway` is False, so dampeners are dormant here; wire the seam, don't special-case).
- `backend/app/domain/table/grade_map.py` — dispatcher: +import, +chain entries on the FLOP branch.
- `content/` — **new** limped-flop threshold content (the §4b directions as data, not hardcoded).
  Follow the existing postflop content-pack shape; bump/author a pack version.
- `NodeContext` limped-lead members — **additive** (`spot.py` StrEnum, hashes `.value` — safe).
  **Regen `content/schema/contentpack.schema.json`** as part of this slice (refuter LOW): the static
  file enumerates NodeContext strings and does NOT auto-update; real validation is pydantic
  `ContentPack.model_validate` (`content/loader.py:11`) so tests won't fail, but regen-and-diff the
  static artifact to prevent silent drift, or document accepted drift in the done-note.
- Tests: new `tests/domain/test_grade_map_limped_flop.py` (own file).

## Out of scope
**Any multiway (3+) limped flop → `None`** ("no baseline yet" — RES-G Slice D, deferred). Turn/river
(flop only v1 — extend later like S6/S7). Solver baselines. Raised-pot graders (byte-unchanged).

## Constraints (invariants)
- Explicit `len(live) != 2 → None` — the grader must **never silently HU-grade a multiway pot**.
- Raised-pot postflop pins byte-unchanged; `spot_signature()` unchanged; `TAXONOMY_VERSION` bump
  only if the grader taxonomy genuinely changes.
- Strategy lives in versioned `content/`, not code; schema-valid. EVs labeled approximate.
- Domain purity; freq+EV never boolean; `StrategyProvider` seam.

## Verify-by (RES-G §6-C verbatim)
(a) Bot-driven belt-test fires the new mappers on a HU limped flop (hero leads / hero faces lead);
    a 0-raise HU flop that returned `None` now grades freq+EV.
(b) Any multiway limped flop returns `None` — assert BOTH: a 3-preflop-entrant limped flop → None,
    AND a 3-preflop-entrant pot that degraded to 2-live by hero's turn → still None (preflop-entrant
    gate, not flop-live-count).
(c) Raised-pot postflop graders byte-unchanged (existing pins hold).
(d) EVs approximate; `spot_signature()` unchanged; `verify.sh` + FE build green; refuter + Codex Sol
    PASS; design-review offered (FE byte-untouched — grading-only slice).
