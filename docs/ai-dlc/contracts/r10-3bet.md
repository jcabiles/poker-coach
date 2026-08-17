# Contracts — R10-3BET (`vs_3bet` persona-pack node)

> Read-only scan, 2026-07-30, contract-mapper. For the slice authoring per-persona `vs_3bet`
> continue/4-bet mixes. Roadmap spec: `docs/ai-dlc/roadmap/persona-realism.md:2042-2055`.

## 1. Pack format

- Schema `content/schema/persona.schema.json` (`PersonaNode`/`PersonaActionMix`), enforced at load by
  `backend/app/domain/content/models.py:114-126` and `:92-108`.
- `facing` closed enum incl. `"vs_3bet"` — `models.py:81`. `positions: list | null`, null = wildcard —
  `models.py:116`. **Every shipped pack's `vs_3bet` node is `positions: null`.**
- `mixes`: ordered list; each `combos` = 169-class range-notation string (`notation.py:1-15` — `*`,
  `77+`, `QQ-99`, `AKs`/`AKo`/`AK`, `ATs+`) + `weights: {action: prob}`, sum ≤ 1.0, remainder = implicit fold.
- Legal actions at `vs_3bet`: exactly `{fold, call, 4bet}` — `_FACING_ACTIONS`, `models.py:87`,
  enforced `models.py:119-126`. **No jam/5bet token** (that exists only at `vs_4bet`).

Example nit (`content/personas/nit.json:61-68`): AA `{4bet .5, call .5}`, KK `{call 1.0}` — nothing else
covered. Maniac (`content/personas/maniac.json:204-218`): three tiers, widest 4-bet range on roster.

## 2. Consumer — sampler contract

- `backend/app/domain/personas.py:61-91` `sample_preflop_action`: node lookup = list order, first
  `facing` match with wildcard or containing position wins; within node, **first mix containing hand
  class wins**; weights → categorical with implicit-fold remainder (`:84-87`).
- **If node matches but no mix covers the hand class → break, fold 1.0 — no fall-through**
  (`personas.py:76-91`). So any class not enumerated in `vs_3bet` mixes folds 100% there.
- Ordering validator `PersonaPack._node_ordering` (`models.py:248-272`): **at most one** wildcard per
  facing (none is legal); explicit-position nodes must precede it.
- Caller: `backend/app/domain/table/play.py` — `_preflop_facing` (`:82-98`, 2 raises = vs_3bet),
  `_preflop_decision` (`:101-131`, illegal action falls back CALL→CHECK→FOLD). `"4bet"` →
  `ActionType.RAISE` via `_WIRE` (`personas.py:25-33`). Sizing: `sizing.py:217-226` →
  `fourbet_mult * last_raise_to`, clamped.

## 3. Content at HEAD

| Pack | continue | 4bet |
|---|---|---|
| nit | AA (4b .5/call .5), KK (call 1.0) — all else folds | AA 50% |
| tag | KK+/AKs 4b 1.0; AQo/A5s 4b .4/call .6; TT-QQ,AKo,AQs,AJs,KQs call .8 | tag.json:123-130 |
| lag | QQ+/AKs/AKo 4b 1.0; A5s,A4s,KQo 4b .4/call .6; 88-JJ,ATs+,KJs+,QJs,JTs,AJo+ call .75 | lag.json:127-134 |
| maniac | TT+/AJs+/AQo+ 4b 1.0; wide tier 4b .5; very wide tier call .5 | maniac.json:204-218 |
| station | AA,KK call 1.0; QQ,AKs,AKo call .7 — **never 4-bets** | calling_station.json:62-68 |
| fish | AA 4b .5/call .5; KK,QQ,AKs,AKo call 1.0 | passive_fish.json:62-68 |

4-bet share ordering maniac>lag>tag>nit = 7.5/3.2/1.7/0.2% — cited from roadmap `:2051-2052`, not
recomputed. "Combo-weighted" = per-class combo counts (6 pairs / 4 suited / 12 offsuit).

## 4. Tests/fixtures that break on a vs_3bet edit

- **RR-LINT `backend/tests/test_pack_range_lint.py`** — frozen-inventory tripwires; ANY change to the
  computed gap/inert/interleave set (fixing or adding) fails until constants co-edited (`:39-49`).
  Live `vs_3bet` entries: `_ROW_GAPS` lag `A9s..A6s` (`:164`), tag `ATs..A6s` (`:173`);
  `_WEIGHT_INTERLEAVING` nit KK, fish KK, lag 88-JJ, tag TT-QQ (`:184-198`).
- Pydantic validators hard-fail typos at load (`models.py:119-126`, `:248-272`).
- **Seeded fixtures re-record required** (stream displacement): `coverage_baseline.json`
  (`test_coverage_baseline.py`), golden `_GOLDEN_STATS_N200` (`test_personas_postflop.py`),
  **`_PRE_M3_FIRES` limper belt in `test_limper_coverage_belt.py:175-220`** (Codex C3 — NOT in
  test_personas_postflop.py), maniac cross-val band `test_node_action_first_in_raise_cross_validates_
  r10_corpus` (`test_personas_postflop.py:3679-3717`, rng-coupled to whole pack set per own docstring)
  — precedent R10-PRE1 ledger `:29-33`, W5-b4 ledger `:32-35`.
- **`backend/tests/test_range_estimate.py:190-198`** pins tag's EXACT vs_3bet 4-bet posterior
  ({KK+, AKs @1.0} ∪ {AQo @0.4} ∪ {A5s @0.4}) — deterministic content pin, breaks on any tag vs_3bet
  raise-mass edit; co-edit with provenance (Codex C3).
- **Frozen postflop BANDS** (`test_personas_postflop.py` `test_persona_postflop_bands`, BANDS dict
  `:2382-2400`): population AF/fold-to-cbet/WTSD recomputed live from the SAME packs. Frozen to W4-b
  re-anchor ONLY. A vs_3bet edit can breach them; breach = STOP + escalate to owner, never re-record
  (refuter R1).
- Pack `version` field: convention bump, no automated gate.
- ⚠️ Naming collision: `content/preflop/vs_3bet.json` + `test_scenarios.py:125-139` is the hero
  drill/grading system — disjoint consumer, DO NOT touch. `grading.py` has no coupling to persona packs.

## 5. R10-COUNT instrument

- Test-harness only: `NodeActions` (`test_personas_postflop.py:2561-2596`), `NodeOccupancy`
  (`:2541-2559`), via `_persona_stats_ext`. Counters computed for all six personas; asserted today only
  for maniac (`:3671-3714`).
- vs_3bet is a re-entry node — pooled `all_hits` rate mixes two arrival ranges. Strata (corrected per
  docstring `:2579-2591`, Codex C1): **cold facers = `first_hits`** (first decision of the seat-hand);
  **`all_hits − first_hits` = re-entrants ≈ OPENERS** — the opener-conditioned stratum external
  "Fold to 3-bet" figures compare to.
- Run: `python -m pytest backend/tests/test_personas_postflop.py -k node_action -q -s`.
- Integrity: `test_node_action_counters_align_with_occupancy` (`:3646-3668`).

## 6. Provenance convention

Per-slice ledger `docs/ai-dlc/ledger/persona-realism-<slug>.md` (R10-PRE1/W5-b4 template):
done-condition before/after, reviewer findings table with adjudications, fixture re-record accounting,
provenance citations quoted verbatim (W5-b4 finding T-4). No JSON comments — packs are plain .json.
