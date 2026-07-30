# Tickets — feedback-prose-readability

> Spec: `docs/ai-dlc/specs/feedback-prose-readability.md` · Contracts: `docs/ai-dlc/contracts/feedback-prose-readability.md`
> Ledger: `docs/ai-dlc/ledger/feedback-prose-readability.md`
> DAG: T1 → T2 → { T3 → T4 } ∥ { T5 → (T6 ∥ T7) } → T8
> Hotspot ownership: `feedback.py` = T1→T2→T5 serial (one owner at a time) · `sim_session.py` +
> `schemas/simulate.py` = T2→T3 serial · `frontend/src/api/types.ts` = T3 only · content JSON = T6/T7 (disjoint files).

## T1 — Domain structured seam (walking skeleton)
`ReasoningParts` model + `FeedbackTiers.reasoning_parts` + `EvaluationResult.authored_rationale_parts`; decompose `_reasoning()`'s bundled appends (NODE/ADV/CAT/WET → separate elements — ledger R1/C5) and emit parts (lead = first element, points = rest; NOT_FOUND/early-return branches emit synthetic `lead` + empty points — ledger R7). Flat `reasoning` stays byte-identical (join of the same clauses).
- **Owned files:** `backend/app/domain/evaluation.py`, `backend/app/domain/feedback.py`, `backend/tests/test_feedback_tiers.py` (additive shape tests only)
- **Accept:** parts populated on every tiered result; flat strings unchanged (existing string tests pass UNMODIFIED).
- **Done-condition:** `./scripts/verify.sh` → `BACKEND VERIFY OK` with zero edits to existing assertions.

## T2 — Content structured rationale + every flat-field consumer (depends T1)
`Entry.rationale_parts` + derived `rationale_text` accessor; regenerate `contentpack.schema.json` + add schema-diff test (ledger R6); switch ALL `entry.rationale` consumers to `rationale_text` (`heuristic.py:47,54-68` incl. legacy `explanation` path — ledger R5/C4; `postflop.py:60`; `sim_session.py::_exploit_note`); `ExploitNoteView` gains optional `rationale_parts` (ledger R4); thread `authored_rationale_parts` through providers into `compose_tiers` with the `Versus a {villain} (…): {lead}` exploit-prefix rule + pinning test (ledger R2/C7); re-point `test_exploits.py:38` + `test_sim_preflop_chart.py` exploit-note asserts (ledger R3).
- **Owned files:** `backend/app/domain/content/models.py`, `loader.py`, `content/schema/contentpack.schema.json`, `backend/app/domain/providers/heuristic.py`, `backend/app/domain/postflop.py`, `backend/app/domain/feedback.py`, `backend/app/services/sim_session.py` (exploit-note only), `backend/app/schemas/simulate.py` (ExploitNoteView only), `backend/tests/{test_exploits,test_sim_preflop_chart,test_feedback_tiers,test_grading}.py`
- **Accept:** a fixture entry with `rationale_parts` flows lead+points into tiers; flat-only entries unchanged; exploit prefix pinned.
- **Done-condition:** `verify.sh` green + new schema-diff test fails if `contentpack.schema.json` is stale.

## T3 — Wire + persistence + reload durability (depends T2)
`GradeView.reasoning_parts` + `ReplayStepView.reasoning_parts`; Alembic migration **0014** — nullable `sim_decision.reasoning_parts_json`; write path serializes parts (service layer, domain stays JSON-free); replay read deserializes; `_grade_view()` falls back to persisted 0013/0014 columns when in-memory tiers absent (ledger C8 — fix the stale docstring); hand-edit `frontend/src/api/types.ts`.
- **Owned files:** `backend/app/schemas/simulate.py`, `backend/app/services/sim_session.py`, `backend/app/db/models.py`, `backend/alembic/versions/0014_*.py`, `frontend/src/api/types.ts`, `backend/tests/{test_sim_session,test_sim_replay}.py`
- **Accept:** new decision rows round-trip parts; pre-0014 rows return NULL parts + flat text; reloaded session recap carries prose.
- **Done-condition:** `verify.sh` green (migration applies) + FE `npm run typecheck` green.

## T4 — Render on all five components (depends T3)
Lead (bold) + `<ul>` bullets + muted sources line in `SimRecap.tsx`, `HandReplay.tsx`, `HandReplayTable.tsx` (History route — ledger C1), `FeedbackPanel.tsx` (sources → collapsed deep-dive), `SimRangeChart.tsx` (exploit note); flat-paragraph fallback when parts absent; CSS via tokens only, AA contrast + focus both themes.
- **Owned files:** the five components + `frontend/src/styles/app.css`
- **Accept:** parts render structured; parts-absent renders exactly today's paragraph; no raw px/hex.
- **Done-condition:** `npm run typecheck && npm run build` green + manual probe of all five surfaces.

## T5 — Template prose rewrite (depends T2; ∥ T3/T4)
Rewrite `feedback.py` dict VALUES (`_PRE_SHAPE`, `_NODE`, `_ADV`, `_CAT`, `_WET`, `_TURN_CLASS`, `_RIVER_CLASS`), `_verdict()` ledes, pure-node/mixed-node sentences in the approved plain voice (terms kept + explained inline); tag KEYS frozen; verdict ≤120 chars no `%`/`≈`; update the pinned string tests (`test_feedback_tiers.py`, `test_grading.py:254,258`, `test_turn_graders.py:220`) to the new voice.
- **Owned files:** `backend/app/domain/feedback.py`, `backend/tests/{test_feedback_tiers,test_grading,test_turn_graders}.py`
- **Accept:** no template sentence uses unexplained jargon; concept-card matching untouched (tag keys byte-identical).
- **Done-condition:** `verify.sh` green.

## T6 — Content rewrite: preflop, 74 strings (depends T2+T5; ∥ T7)
Convert all preflop authored rationale to `rationale_parts` in the approved voice — `rfi` (8), `vs_rfi` (21), `vs_3bet` (7), `blind_defense` (14), `vs_limpers` (12, incl. the owner's 33-at-HJ example), `exploit` (12). Citations verbatim into `sources`; lead = action + one-line why; 2–4 points; terms kept + explained inline.
- **Owned files:** `content/preflop/*.json` (6 files)
- **Accept:** zero flat `rationale` remaining in these packs; no `§`/`doc 0` in lead/points; loader validates.
- **Done-condition:** `verify.sh` green + content-validation tests pass.

## T7 — Content rewrite: postflop, 19 strings (depends T2+T5; ∥ T6)
Same conversion for `content/postflop/{cbet,turn,river,limped}.json` (3+6+6+4).
- **Owned files:** `content/postflop/*.json` (4 files)
- **Accept/Done:** same bar as T6.

## T8 — End-to-end verify + roadmap bookkeeping (depends all)
Run the spec's full Verify-by (1–6): verify.sh, ruff, typecheck/build, live probe (blunder → structured recap; new-hand replay bullets; pre-migration hand flat fallback; drill panel; exploit chart note), schema regen check. Record the slice in `roadmap/professional-teacher-rework.md` as a readability-debt slice.
- **Owned files:** none (verification) + roadmap file (one checklist line)
- **Done-condition:** all six Verify-by steps pass, evidence pasted in the PR.
