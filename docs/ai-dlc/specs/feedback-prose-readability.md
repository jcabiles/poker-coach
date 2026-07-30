# Delta spec — feedback-prose-readability

> Initiative: restructure + plain-language rewrite of the grading feedback prose.
> Parent roadmap: `docs/ai-dlc/roadmap/professional-teacher-rework.md` (teaching/UX pillar — N1 tiers + N3
> authored rationale are the parents; this slice fixes their readability debt).
> Contracts map: `docs/ai-dlc/contracts/feedback-prose-readability.md` (read first — pipeline + break risks).
> Owner decisions (Gate 1, 2026-07-29): structure + full rewrite · all 3 surfaces · keep terms + explain
> inline · citations demoted out of main text · rewrite all 93 authored strings + code templates.

## Goal (one line)

Feedback text on all three surfaces (Simulate "Your decisions" recap, History replayer, Drill panel) renders
as a bold topic sentence + supporting bullets, written in plain language that keeps poker terms but explains
them inline — replacing today's single jargon-dense paragraph.

## Target output shape (owner-approved sample, 33 at HJ vs limper)

> **Just call here — the chart plays 33 for 1bb every time.**
> - Small pairs like 33 "over-limp" (call the 1bb behind the limper) to see a cheap flop with several players in.
> - The payoff: flop a set (three of a kind) and win a big pot for a tiny price.
> - Raising is reserved for stronger hands (77+, big aces) that want to "isolate" — raise to get the limper heads-up while you have position.
> - Folding is the one losing option: you're giving up a hand that makes money for just 1bb.
>
> *(citations like "Upswing vs-limpers; doc 01 §9" appear only in a muted footer / the collapsed deep-dive)*

## Design

### 1. Structured seam (additive — no breaking type change)

New model `ReasoningParts { lead: str, points: list[str], sources: str | None }`.

- `compose_tiers()` (`backend/app/domain/feedback.py`) already assembles `_reasoning` from an ordered
  `parts: list[str]` before `" ".join(parts)` — the structure exists and is thrown away at the join.
  Emit it: `FeedbackTiers.reasoning_parts: ReasoningParts | None` where `lead` = first assembled clause,
  `points` = remaining clauses, `sources` = citations from structured authored content (see §3).
  **No prose parsing** — parts come from the assembly list, never from splitting a string.
- ⚠ **Refuter fix (HIGH):** today's appends are NOT one-clause-per-element — `feedback.py:158-164`
  bundles the NODE/ADV/CAT/WET mechanism into ONE multi-sentence element. Decompose the bundled
  appends into one list element per clause (NODE-context sentence, ADV, CAT, WET as separate appends;
  structured authored lead vs points as separate appends) so lead/points match the approved sample shape.
- ⚠ **Refuter fix (LOW):** the early-return branches bypass the parts list — `Coverage.NOT_FOUND`
  (`feedback.py:136-137`) returns a flat string directly. These branches emit synthetic
  `ReasoningParts(lead=<message>, points=[])` so `reasoning_parts.lead` is non-empty whenever tiers exist.
- Flat `FeedbackTiers.reasoning: str` REMAINS and equals the deterministic join of `lead + points`
  (sources excluded — demotion happens here). Every legacy consumer (coach prompt, TemplateCoach
  `" ".join`, old DB rows, FE fallback) keeps working on the flat string.
- Sources string is appended to `deep_dive` (Drill's collapsed section) in addition to `reasoning_parts.sources`.

### 2. Wire + persistence (additive)

- `GradeView` (`backend/app/schemas/simulate.py`) + `ReplayStepView` gain optional `reasoning_parts`.
- `sim_session.py`: `_grade_view()` passes parts through; the decision-persist path writes a new **nullable**
  `sim_decision.reasoning_parts_json` column (next sequential Alembic migration); the replay-read path
  deserializes it. Old rows are NULL → replayer falls back to the flat `reasoning_text` paragraph (graceful
  old-hand degradation — no backfill, no re-grading).
- `frontend/src/api/types.ts` hand-edited to match (hotspot — single owner ticket).

### 3. Content pack structured rationale (additive)

- `Entry` (`backend/app/domain/content/models.py`) gains optional
  `rationale_parts: RationaleParts | None` (`{ lead: str, points: list[str], sources: str | None }`).
  **Flat-field policy (refuter fix, HIGH):** rewritten entries carry ONLY `rationale_parts` (no redundant
  flat copy to drift). `Entry` gains a derived accessor `rationale_text` = join of `lead + points` when
  `rationale_parts` is set, else the flat `rationale`. EVERY consumer of `entry.rationale` switches to it:
  `heuristic.py:47` + `:63` gates, `postflop.py:60` rationale index, `sim_session.py:1113` exploit note,
  `test_exploits.py:38`. Regenerate `content/schema/contentpack.schema.json` from the model — and add a
  test that diffs `content_pack_json_schema()` against the committed file (refuter fix, MED: nothing
  enforces regeneration today).
- **Carry the structure to the composer (refuter fix, HIGH):** `compose_tiers` only sees
  `EvaluationResult`, which has no structured slot — add
  `EvaluationResult.authored_rationale_parts: RationaleParts | None`; `heuristic.py`/`postflop.py` set it
  (alongside flat `authored_rationale = entry.rationale_text` for back-compat); `compose_tiers` folds
  `lead`+`points` into the assembled parts and routes `sources` per §1.
- **4th prose surface (refuter fix, HIGH — missed by the contracts map):** the live in-hand preflop-chart
  exploit note — `sim_session.py::_exploit_note` (~`:1097-1116`) → `ExploitNoteView.rationale`
  (`schemas/simulate.py:174`, non-optional str) → `SimRangeChart.tsx:126`. In scope: `ExploitNoteView`
  gains optional `rationale_parts`; flat `rationale` becomes `entry.rationale_text`; `SimRangeChart.tsx`
  renders lead+bullets when parts present, flat fallback otherwise.

### 4. Plain-language rewrite (the authoring job)

- **All 93 authored rationale strings** across `content/preflop/{rfi,vs_rfi,vs_3bet,blind_defense,vs_limpers,exploit}.json`
  + `content/postflop/{cbet,turn,river,limped}.json` → converted to `rationale_parts` in the approved voice:
  - Audience: smart adult who knows rules/positions/actions + basic strategy; NOT pro vocabulary.
  - Keep standard terms ("over-limp", "isolate", "capped"), explain inline in parentheses on use.
  - Lead = the action + the one-line why. Points = 2–4 short supporting bullets.
  - Citations moved verbatim into `sources` — never in lead/points.
- **Code templates rewritten in the same voice** (`feedback.py` dict VALUES only — tag KEYS frozen, they
  drive concept-card matching): `_PRE_SHAPE`, `_NODE`, `_ADV`, `_CAT`, `_WET`, `_TURN_CLASS`,
  `_RIVER_CLASS`, the pure-node sentence ("essentially pure: call 1.0bb at 100%" → "the chart always calls
  here — 1bb, every time" style), and `_verdict()` ledes. Verdict contract unchanged: ≤120 chars, no `%`/`≈`.
- Chart frequency/EV info is retained as a plain final bullet (invariant: results are frequency + EV, never
  boolean) — plain wording, same numbers.
- **Exploit villain-prefix rule (Codex fix, MED):** the "Versus a {villain}: …" persona lede
  (`feedback.py:140-147`, pinned by `test_feedback_tiers.py:148,153`) survives structuring: for exploit
  spots with structured authored content, the composed `lead` = `Versus a {villain} ({one-line plain
  descriptor}): {authored lead}` — a new test pins the prefix so exploit feedback never reads like
  baseline advice.
- **Legacy `explanation` keeps its rationale (Codex fix, HIGH):** `_enrich_exploit` (`heuristic.py:54-68`)
  appends `entry.rationale` into the flat legacy `explanation` — it switches to `entry.rationale_text`
  like every other consumer (the FIELD stays; its content updates with the rewrite).
  `test_grading.py:242` (`test_exploit_explanation_carries_rationale`) is re-pointed accordingly.

### 5. Renderers (three surfaces = FIVE components — Codex fix, HIGH)

- `SimRecap.tsx` (the "Your decisions" panel), `HandReplay.tsx` (Simulate-route quick replay),
  **`HandReplayTable.tsx` (the actual History-route replayer — `HistoryView.tsx:5` mounts it; its
  `HeroVerdict` is a deliberate replica of HandReplay's, missed by the contracts map)**,
  `FeedbackPanel.tsx` (Drill), and `SimRangeChart.tsx` (live exploit note, per §3): render
  `reasoning_parts` as bold lead + `<ul>` bullets + small muted sources line (FeedbackPanel routes sources
  into its existing collapsed deep-dive instead). When `reasoning_parts` is absent (old rows / legacy
  fallback) render the flat paragraph exactly as today.
- **Reload gap (Codex fix, MED):** `_grade_view()` (`sim_session.py:299`) currently returns
  `verdict/reasoning = None` whenever in-memory tiers are absent — `restore_session()` (`:825`) rebuilds
  the recap with `tiers=None` for every row, so a reloaded session's recap loses all prose EVEN THOUGH
  migration 0013's `verdict_tier_text`/`reasoning_text` columns hold it (the docstring's "persisted rows
  carry no tier text" is stale). Fix in scope: `_grade_view` falls back to the persisted columns
  (incl. the new parts column) when tiers is None — makes the recap reload-durable and the verify-by
  fallback promise true.
- New CSS classes in `app.css` using existing design tokens only (no raw px/hex); AA contrast + visible
  focus in both themes.

### 6. Tests

- Update the ~15 literal-substring assertions pinned in the contracts map
  (`test_feedback_tiers.py:32-175`, `test_grading.py:254,258`, `test_turn_graders.py:220`) deliberately —
  they are a partial spec of the OLD prose and must be re-pointed at the new voice/shape.
- **Also (refuter fix, HIGH):** `test_exploits.py:38` (`test_each_exploit_has_rationale` asserts flat
  `e.rationale` truthy for all 12 exploit entries) — re-point at `rationale_text` so rewritten
  parts-only entries pass. Check `test_sim_preflop_chart.py` for exploit-note assumptions likewise.
- **Also (Codex fix, HIGH):** `test_sim_preflop_chart.py` exploit-note tests (~`:169`) — the chart-note
  path switches to `rationale_text`, so these assertions get re-pointed too.
- New assertions: `reasoning_parts.lead` non-empty whenever tiers exist · `points ≥ 1` on graded mistakes
  **when `coverage != NOT_FOUND`** (NOT_FOUND emits synthetic `lead` + empty points; and the §1
  decomposition guarantees the tag-template-only branch yields ≥2 elements — Codex flagged that today's
  single bundled append would otherwise produce an empty bullet list) · flat `reasoning` == join of
  lead+points · `"§"`/`"doc 0"` never appear in lead/points · verdict ≤120 chars, no `%`/`≈` (unchanged) ·
  replay fallback renders for NULL parts rows · exploit lead keeps the `Versus a {villain}` prefix.

## Files / interfaces to touch

- `backend/app/domain/feedback.py` (compose + templates — serialize edits, one owner at a time)
- `backend/app/domain/evaluation.py` (FeedbackTiers + ReasoningParts)
- `backend/app/domain/content/models.py`, `backend/app/domain/content/loader.py`, `content/schema/contentpack.schema.json`
- `backend/app/domain/providers/heuristic.py`, `backend/app/domain/postflop.py` (thread structured authored content)
- `backend/app/schemas/simulate.py`, `backend/app/services/sim_session.py`, `backend/app/db/models.py`, `backend/alembic/versions/` (new migration)
- `content/preflop/*.json` (6 files), `content/postflop/*.json` (4 files) — 93 rationale rewrites
- `frontend/src/api/types.ts` (hotspot), `frontend/src/components/simulate/SimRecap.tsx`,
  `frontend/src/components/simulate/HandReplay.tsx`, `frontend/src/components/simulate/HandReplayTable.tsx`,
  `frontend/src/components/simulate/SimRangeChart.tsx`, `frontend/src/components/FeedbackPanel.tsx`,
  `frontend/src/styles/app.css`
- `backend/tests/{test_feedback_tiers,test_grading,test_turn_graders,test_exploits,test_sim_preflop_chart,test_sim_session,test_sim_replay}.py`

## Out of scope (explicit)

No LLM prose generation (authored data only — roadmap N3 no-go stands) · no glossary/tooltip component ·
no change to grading logic, frequencies, EV numbers, thresholds, or `leak_category` · no renaming of
`rationale_tags` KEYS (concept-card matching) · no coach prompt redesign (coach keeps consuming the flat
string) · no backfill/re-grade of already-played hands · no restyling beyond the feedback text blocks ·
`spot_signature()` untouched · `EvaluationResult.explanation` legacy field untouched · no SimDashboard work
(it renders no prose).

## Constraints (from profile invariants)

Domain core `app/domain/` stays free of web/DB imports (ReasoningParts lives in domain, JSON serialization
at the service layer) · results stay frequency + EV, never boolean · grading stays behind the one async
`StrategyProvider` (`TieredFeedbackProvider` wrapper is the seam — solver provider inherits the new shape
free) · strategy prose lives in versioned `content/` data, not code · CSS values from design tokens only ·
WCAG AA + visible focus both themes · schema change ships an Alembic migration · `spot_signature()` frozen ·
FE types hand-maintained in `types.ts` · EVs labeled approximate.

## Verify-by (end-to-end)

1. `./scripts/verify.sh` → `BACKEND VERIFY OK` (includes domain-purity + migration apply).
2. `cd backend && ruff check .` clean; `cd frontend && npm run typecheck && npm run build` clean.
3. Boot `./scripts/serve.sh start`; play a Simulate hand and blunder deliberately → "Your decisions" recap
   shows bold lead + bullets + no "§"/doc citations in the readable text.
4. Open History replay of that new hand → bullets render; open a pre-migration hand → old flat paragraph
   renders (fallback, no error).
5. Grade a Drill rep → FeedbackPanel shows the new layout; citations only inside the collapsed deep-dive.
6. Content loader validates all 10 packs; `contentpack.schema.json` regenerated and committed.
