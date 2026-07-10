# Contract scan — Simulate S3 (persona packs + preflop bot play), 2026-07-10

> Read-only contract-mapper report, condensed. Feeds the S3 spec interview.

## Pack anatomy
- Runtime validation = **Pydantic only** (`ContentPack.model_validate_json`, `content/loader.py:10-15`);
  `content/schema/*.json` are generated docs (`model_json_schema()`, `loader.py:18-20`), one file
  per top-level model (naming convention for `persona.schema.json`). The real gate for S3 = a new
  Pydantic model + loader, not the schema file.
- `registry.py:15-17` loads via repo-root glob (`parents[4]` hop count — recompute for any new
  loader location). `build_index()` (`registry.py:24-29`) **silently last-wins on duplicate keys**
  — S3's persona index needs an explicit uniqueness assertion (no precedent).

## Hand-class notation — REUSE VERBATIM
- 169-grid enumeration `notation.py:23-32`; `parse_range()` (`:84-88`) is the single expansion
  entrypoint; supported tokens: `*`, pairs, `77+`, `QQ-99`, `AKs/AKo/AK`, `ATs+/ATo+`
  (`_expand_token:60-81` raises ValueError on anything else — no `A5s-A2s` style spans).
- `hole_cards_to_class()` (`notation.py:91-99`) maps a dealt pair → class (sampler keying);
  `class_to_combos`/`combos_for_range` (`equity.py:82-102`) for concrete combos.
- `ActionRange.frequency` supports mixing in the schema but **no pack exercises it and nothing
  validates per-hand-class frequencies sum ≤1 across actions** — S3 adds that validation new.

## VillainType widening (TAG + maniac) — coupled consumers
- `grading.py:96-105` `_EXPLOIT_LEAK`: unmapped types **silently fall back to
  CALLING_STATION_EXPLOIT** — needs TAG/MANIAC LeakCategory entries or explicit decision.
- `test_exploits.py:20-22` asserts exploit pack covers `set(VillainType)` — widening the enum
  FAILS this test until exploit.json gets TAG/MANIAC entries **or the test is deliberately
  decoupled** (acting personas ≠ hero-exploit archetypes — spec must decide).
- `test_api.py:66` hardcodes the 4-member set literal (under-asserts silently — update).
- Preflop `spot_signature()` includes villain_type (last component, `srs.py:65`) — additive only;
  never reinterpret existing spots. DB column is untyped string — no migration needed.
- `Spot.villain_type` stays hero-exploit-drill-scoped; do NOT dual-purpose it for "which bot".

## Action model gap — LIMP
- `ActionType` = FOLD/CHECK/CALL/BET/RAISE/POST — **no LIMP**. Convention today: limp = CALL at
  1BB first-in (`scenarios.py:207-211`). RFI-node legal actions never include a limp option
  (baseline never limps). S3 spec must decide: (a) keep limp=CALL-in-context (no schema change)
  or (b) add ActionType.LIMP (widens spot.py + schema + every 6-member pattern-match).
- `HistoryAction` (`spot.py:106-110`) = the shape bot actions must emit (S4/S9); no is_hero flag
  (cross-ref position); amounts not validated vs LegalAction bounds by the model.

## RNG
- Precedent for categorical draw: `random.Random.choices(pairs, weights, k=1)`
  (`challenge.py:184-213`). Instance-passing is the hard convention; personas.py must accept an
  injected per-hand rng (thread the hand's rng down) — never module-level (drill.py's `_RNG` is
  the one legacy exception; untouchable).

## Tests
- **No pytest markers exist; verify.sh runs the whole unmarked suite** — the 10k×6-persona
  closed-loop test needs an explicit home decision (new `slow` marker + pyproject registration,
  or reduced-N default + full run behind env var). No precedent to mirror.
- Content-test style: load via real loader, assert invariants inline (no golden files).
- No statistical test precedent exists (S2 builds the chi-square suite; S3 only needs band checks).

## Purity
- `app.domain.personas` must be added to the hardcoded allowlist in `test_domain_purity.py:11-15`
  (same mechanism as S1's `app.domain.table.deck`).
