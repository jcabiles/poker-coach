# Contracts Report: Simulate "Your Decisions" Feedback Prose Pipeline

> Mapped 2026-07-29 by contract-mapper for the feedback-prose-readability initiative
> (restructure + plain-language rewrite of the Simulate decisions-panel feedback text).

## Pipeline Map (file:line per hop)

1. **Content pack authoring** (raw prose, `str | None`, one field per Entry)
   - `content/preflop/{rfi,vs_rfi,vs_3bet,blind_defense,vs_limpers,exploit}.json`, `content/postflop/{cbet,turn,river,limped}.json` — each entry's `"rationale"` string.
   - Example cited in brief: `content/preflop/vs_limpers.json:38` (HJ vs 1-limper raise entry).
   - Model: `Entry.rationale: str | None` — `backend/app/domain/content/models.py:47`.
   - Schema (generated, non-enforcing at load time): `content/schema/contentpack.schema.json:81-92`.

2. **Content loading / validation**
   - `ContentPack.model_validate(...)` is the *only* runtime gate — `backend/app/domain/content/loader.py:11,15`. The checked-in `contentpack.schema.json` is descriptive only (built by `content_pack_json_schema()` at `loader.py:18-20`); nothing in the test suite re-generates or diffs it against the live Pydantic model, so it can silently drift from the real type.

3. **Backend composition — where `authored_rationale` gets set on `EvaluationResult`**
   - Preflop: `backend/app/domain/providers/heuristic.py:40-52` (`_grade`) sets `result.authored_rationale = entry.rationale` for non-exploit baseline entries; `_enrich_exploit` (`heuristic.py:54-68`) appends `entry.rationale` into the flat `explanation` *and* separately sets `authored_rationale` (comment at `:65-67` explicitly says this exists so `compose_tiers` doesn't re-parse `explanation` and double-append).
   - Postflop: `backend/app/domain/postflop.py` — `_postflop_rationale_index()`/`_postflop_rationale()` (`:47-69`) keyed by `(node_context, hero_position, counterpart_position)`; each of the 9 postflop node-graders independently looks up and assigns `result.authored_rationale = rationale` — ~18 call sites (`postflop.py:569,610,922,961,1116,1159,1338,1378,1454,1493,1679,1719,1797,1836,2012,2055,2254,2294,2359,2401`).

4. **Tier composition — the sentence-templates that append the "chart's line is essentially pure" style clauses**
   - `backend/app/domain/feedback.py` — `compose_tiers()` (`:214-222`) is the ONE place all appended template sentences live:
     - `_verdict()` (`:118-129`) — one-line lede, numeral-free by contract (tested).
     - `_reasoning()` (`:132-194`) — assembles `parts: list[str]` and joins with `" ".join(parts)` at `:194`. Order is load-bearing: exploit lede (`:140-152`) → authored rationale (`:153-155`) → tag-derived mechanism clause from `_NODE`/`_ADV`/`_CAT`/`_WET` dicts (`:156-164`) → turn/river card-class clause (`:165-177`) → preflop `_PRE_SHAPE` mistake-shape clause OR "essentially pure" pure-node sentence (`:178-193`; the exact template that produced the brief's closing sentence is `:190-193`).
     - `_deep_dive()` (`:197-211`) — full per-action mix string + coverage/provider footer.
   - `TieredFeedbackProvider` (`backend/app/domain/providers/tiered.py:18-34`) wraps ANY provider and calls `compose_tiers` on both `optimal()` and `evaluate()`, writing the result onto `EvaluationResult.tiers`. Mounted once in the provider factory — every provider (heuristic today, solver later) inherits this for free.

5. **Wire shape (backend → API)**
   - `EvaluationResult` (`backend/app/domain/evaluation.py:61-82`) — Practice/Drill surface, full object incl. `tiers: FeedbackTiers|None`, `authored_rationale`, `rationale_tags`, `per_action`. Returned as-is by `POST /drill/grade` (`backend/app/api/v1/drill.py:321-325`, `response_model=EvaluationResult`).
   - `GradeView` (`backend/app/schemas/simulate.py:45-62`) — Simulate surface, a FLATTENED per-decision shape: only `verdict: str|None` and `reasoning: str|None` (no `deep_dive`, no `tiers` object, no `per_action` mix, no `authored_rationale` — prose pre-flattened server-side).
   - `_grade_view()` (`backend/app/services/sim_session.py:299-321`) builds `GradeView` from a persisted `SimDecision` row + **in-memory** `FeedbackTiers` (only available on the live request that produced them).
   - Persistence: `SimDecision.verdict_tier_text` / `.reasoning_text` (`backend/app/db/models.py:125-131`, migration 0013) persist the SAME two strings for the **History replayer** only — `sim_session.py:872-878` writes them at play time; `sim_session.py:1603-1604` reads them back into `ReplayStepView.verdict`/`.reasoning` (`backend/app/schemas/simulate.py:337-338`). The live Simulate recap does **not** read these columns back (`sim_session.py:299-307` docstring confirms).

6. **Frontend consumers**
   - **`frontend/src/components/simulate/SimRecap.tsx`** — this IS the "Your decisions" panel (title at `:105`). Renders only `g.reasoning` as a flat `<p className="sim-recap-why">{g.reasoning}</p>` (`:163-165`), gated to `miss && g.reasoning` (mistakes/blunders only). Does NOT render `deep_dive`, `rationale_tags` chips, or `verdict` as visible text (verdict only forwarded into `CoachExplainRequest` payload at `:74-88`; the visible tier badge word comes from `tierOf(g.correctness)` in `simGrade.ts`).
   - **`frontend/src/components/FeedbackPanel.tsx`** — the Practice/Drill panel (mounted from `frontend/src/App.tsx:391`), a DIFFERENT component. Renders `result.tiers?.verdict` headline (`:87`), `RationaleTags` chips (`:136`), `result.tiers.reasoning` (`:137`), `result.tiers.deep_dive` in collapsed `<details>` (`:139-162`). Only surface showing all three tiers + chips.
   - **`frontend/src/components/simulate/HandReplay.tsx`** — a THIRD renderer, History replayer inline verdict panel. Renders `step.reasoning` as `<p className="hr-verdict-why">{step.reasoning}</p>` (`:298-299`), degrading to a "reasoning wasn't recorded" note when null (`:301-303`). No `deep_dive` (field absent on `ReplayStepView`).
   - **`frontend/src/components/simulate/SimDashboard.tsx`** — does NOT render feedback prose (aggregate rates only); not part of this pipeline.
   - **`frontend/src/api/client.ts` → `explainDecision()`** feeds `g.verdict`/`g.reasoning` into `POST /simulate/{id}/explain` (`CoachExplainRequest` at `frontend/src/api/types.ts:268-282`; route `backend/app/api/v1/simulate.py:214-242`) → `CoachContext.reasoning` (`backend/app/services/coach.py:75-76`), consumed two ways server-side:
     - `TemplateCoach.explain()` — `parts.append(ctx.reasoning)` then `" ".join(parts)` (`coach.py:138-139`) — assumes single space-joinable prose.
     - `AnthropicCoach._prompt()` — `f"Grader note: {ctx.reasoning}"` (`coach.py:163-164`) sent verbatim in the LLM prompt.

## Field-by-Field Consumer Table

| Field | Backend producer | FE / BE consumers |
|---|---|---|
| `EvaluationResult.authored_rationale` | `heuristic.py:47-67`, `postflop.py` (~18 sites) | `feedback.py::_reasoning` (`:146-155`); typed at `frontend/src/api/types.ts:69` but **not rendered anywhere in FE** — raw material for `compose_tiers` only |
| `EvaluationResult.tiers.verdict` | `feedback.py::_verdict` | `FeedbackPanel.tsx:87` (headline); `GradeView.verdict` → `SimRecap.tsx:84` (coach payload only, not rendered); replayer badge via `correctness`, not the string |
| `EvaluationResult.tiers.reasoning` | `feedback.py::_reasoning` | `FeedbackPanel.tsx:137`; `SimRecap.tsx:164` (**the brief's target text**); `HandReplay.tsx:298-299`; `coach.py` TemplateCoach + Anthropic prompt |
| `EvaluationResult.tiers.deep_dive` | `feedback.py::_deep_dive` | `FeedbackPanel.tsx:141` only — no Simulate or Replay consumer |
| `EvaluationResult.rationale_tags` | `grading.py::_tags` (preflop), `postflop.py` graders | `RationaleTags.tsx` chips (FeedbackPanel only); `concept_cards.py::match_card`; NOT rendered in SimRecap/HandReplay; NOT persisted to DB |
| `EvaluationResult.explanation` (flat, legacy) | `grading.py:241,276-281,296`; `heuristic.py:57-68` | Backward compat per `tiered.py:7`; `FeedbackPanel.tsx:87` fallback when `tiers` absent; `test_grading.py:254` asserts on it |
| `SimDecision.verdict_tier_text` / `.reasoning_text` (DB) | `sim_session.py:877-878` | `sim_session.py:1603-1604` → `ReplayStepView` → `HandReplay.tsx` ONLY — never read by live recap |

## String-Asserting Tests (grep verified)

- `backend/tests/test_feedback_tiers.py` — heaviest load-bearing file:
  - `:32` `len({verdict, reasoning, deep_dive}) == 3` (tiers stay distinct strings)
  - `:44-48` verdict: NO `"≈"`, NO `"%"`, `len(verdict) <= 120`
  - `:56-57` reasoning must NOT contain `"is the play"`, MUST contain `"range's edge"` (over_fold mechanism phrase)
  - `:68-70` reasoning must contain `"c-bet"` and one of `"dry"/"medium"/"wet"`
  - `:83` `"station" in res.tiers.reasoning.lower()`
  - `:97-99`, `:111-113` `entry.rationale in res.tiers.reasoning`; `"is the play" not in entry.rationale`
  - `:126` `res.authored_rationale in res.tiers.reasoning`
  - `:137`, `:144-145` `res.tiers.reasoning.startswith(res.authored_rationale)`
  - `:153` `reasoning.startswith(f"Versus a calling station: {res.authored_rationale}")` — exact prefix-format assertion
  - `:155` `reasoning.count(res.authored_rationale) == 1` — no double-append
  - `:166` `"No strategy content" in res.tiers.verdict`
  - `:175` `"Best play" in res.tiers.verdict`
- `backend/tests/test_grading.py:254,258` — `"station"` in `explanation` and `tiers.reasoning`
- `backend/tests/test_turn_graders.py:220` — `"straight" in tiers.reasoning.lower() or "scare" in ...`
- `test_provider.py` / `test_sim_session.py` / `test_sim_replay.py` — presence/None-ness only, no substrings.

Any prose rewrite that changes these literal substrings or the `startswith`/`count==1` concatenation order fails these tests — they are a partial spec of the current prose, not just of structure.

## Rationale Counts Per Content File (authored-prose blast radius)

| File | `"rationale"` occurrences |
|---|---|
| `content/preflop/vs_rfi.json` | 21 |
| `content/preflop/blind_defense.json` | 14 |
| `content/preflop/exploit.json` | 12 |
| `content/preflop/vs_limpers.json` | 12 |
| `content/preflop/rfi.json` | 8 |
| `content/preflop/vs_3bet.json` | 7 |
| `content/postflop/river.json` | 6 |
| `content/postflop/turn.json` | 6 |
| `content/postflop/limped.json` | 4 |
| `content/postflop/cbet.json` | 3 |
| **Total authored rationale strings** | **93** |
| `content/preflop/vs_4bet.json` | 0 (falls to tag-template path) |

(`content/cards/*.json` and `content/personas/*.json` have zero `"rationale"` — separate contracts.)

## Schema Flexibility Verdict

**Structured rationale (list/sections) is NOT possible without a breaking type change today.**

- `Entry.rationale: str | None` (`content/models.py:47`) — scalar; every consumer treats it as plain string for f-string interpolation, `.lower()`, `.startswith()`, `" ".join(parts)`: `feedback.py:147,155,190-193`; `heuristic.py:63-67`; `test_feedback_tiers.py:97-155`.
- `FeedbackTiers.reasoning: str` (`evaluation.py:57`), `GradeView.reasoning: str | None` (`schemas/simulate.py:57`, `types.ts:257`) — scalar strings to the wire and into `coach.py`.
- `contentpack.schema.json` documents `rationale` as `{"type": ["string","null"]}` but is not enforced at load — the Pydantic model is the real gate; a type change would propagate through 7+ hops plus ~15 test assertions.
- **Additive path exists (fact, not recommendation):** a NEW optional field alongside `rationale` (e.g. `rationale_parts: list[str] | None`) breaks nothing — Pydantic/JSON accept additive optional fields; nothing generically rejects unknown Entry fields.

## Shared-Renderer Answer

**No shared renderer.** Three separate components each render a subset of the same backend-composed strings:
1. `FeedbackPanel.tsx` (Drill/Practice) — verdict + tag chips + reasoning + deep_dive.
2. `SimRecap.tsx` (Simulate "Your decisions" — the brief's target) — reasoning only (mistakes/blunders).
3. `HandReplay.tsx` (History replayer) — reasoning only, from persisted DB columns.

A prose rewrite in `feedback.py::compose_tiers` propagates to **all three** surfaces; a *rendering* change (paragraph → bullets) made only in `SimRecap.tsx` JSX does NOT touch the other two — each needs its own treatment.

## N8 Concept-Card Linkage

`concept_cards.py::match_card()` (`backend/app/services/concept_cards.py:28-43`) keys on `(leak_category, rationale_tags)` tag overlap, NOT prose. Rewriting the prose VALUES of `_PRE_SHAPE`/`_NODE`/`_ADV`/`_CAT`/`_WET`/`_TURN_CLASS`/`_RIVER_CLASS` dicts is safe for card matching. Renaming/removing tag KEY strings would break `concept_cards.py` matching + `RationaleTags.tsx` `TAG_PHRASES` lookup (`:15-51`, graceful de-slug fallback) + `content/cards/*.json` tag lists.

## Top 5 Contracts a Prose Rework Is Most Likely to Break

1. **`test_feedback_tiers.py` literal-substring/format assertions** — ~15 assertions pin exact words ("is the play", "range's edge", "c-bet", "station", verdict ≤120 chars no `%`/`≈`), exact `.startswith()` concatenation order, and `count(rationale) == 1`. All need lockstep updates; some encode the exact join format.
2. **`" ".join(parts)` flat-string assumption at three join sites** — `feedback.py:194` (reasoning), `feedback.py:211` (deep_dive), `coach.py:141` (TemplateCoach). Bullets/newlines flow through these joins: TemplateCoach smashes markers into a run-on; Anthropic prompt (`coach.py:163-164`) gets raw formatting injected.
3. **Three independent render surfaces, no shared component** — updating only `SimRecap.tsx` leaves `FeedbackPanel.tsx` and `HandReplay.tsx` on flat-paragraph rendering of the same string — cross-surface inconsistency risk.
4. **Live-vs-persisted asymmetry** — live recap uses in-memory `FeedbackTiers`; History replayer reads `SimDecision.verdict_tier_text`/`.reasoning_text` (migration 0013). Changing `compose_tiers` output *shape* means DB column + replay-read path need matching changes, or old rows (plain strings) vs new rows (structured) render inconsistently in the SAME replayer — migration-compatibility hazard.
5. **`str` end-to-end typing** — paragraph → structured sections is a type change touching: `content/models.py:47`, `evaluation.py:57`, `schemas/simulate.py:57`, hand-maintained `frontend/src/api/types.ts:53,257` (hotspot), DB column `db/models.py:130-131` (Alembic migration required per invariant), and coach prompt assembly (`coach.py:75-76,138-139,163-164`) — 6+ coordinated touch-points.
