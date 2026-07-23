# Contracts — Simulate Hand-History + Replay

Read-only contract scan (contract-mapper, 2026-07-22) for the roadmap "Hand replayer"
slice (`docs/ai-dlc/roadmap/simulate-table.md:1295`). Grounds the delta spec.

## (A) Replay feasibility verdict

**`sim_hand.state_json` IS sufficient for a true step-through replay — no schema change
needed to reconstruct the hand action-by-action. But two real gaps: grading verdict/reasoning
TEXT is not persisted, and NO query path reaches a past hand today.**

- `SimHand.state_json` (`db/models.py:72-85`) = `HandState.model_dump_json()`, written on every
  hero action **including the final `hand_over=True` write** (`sim_session.py:820-826, 176-205`).
- `HandState` (`domain/table/engine.py:52-64`) carries `action_history: list[HistoryAction]` —
  FULL ordered per-street action log (`{street, position, action, amount_bb}`, `spot.py:113-117`),
  every seat incl. blinds, chronological. Plus `seats[].hole_cards` for all 9 seats +
  `full_board` (all 5). ⇒ complete street-by-street reconstruction is possible from stored data.
- Same walk `range_estimate.py` `_replay_contexts` (`:107+`) already does card-free; a replay does
  it WITHOUT stripping hole cards.

### Gaps (NOT data — integration/persistence)
1. **No hand-history endpoint/query exists.** Every service fn keys off `_current_hand`
   (`sim_session.py:208-213`, `session.hand_no`). No `list_hands` / `get_hand(id)` / cross-session
   query. New read path required. (`_hand_decisions` `:256-260` DOES generalize to any `sim_hand_id`.)
2. **Grading TEXT lost on reload.** `_grade_view` (`sim_session.py:231-253`) notes: persisted rows
   carry no tier/reasoning text (frozen S10 schema) → reload rebuilds recap with `tiers=None`.
   `SimDecision` keeps only correctness / sizing_correctness / ev_loss_bb / coverage. Prose "why"
   for a past hand ⇒ either (a) re-run grading provider at replay (drift if content packs change)
   or (b) migration persisting verdict/reasoning (flagged NEXT in-code, `sim_session.py:239`).
3. **`SimDecision.ordinal`** = 0-based decision order within hand (global, not per-street). No FK
   from a `HistoryAction` to its `SimDecision`; replay must correlate by street + hero-turn order.
4. **Bot actions not re-simulatable** (`sim_session.py:11-16`, fresh RNG/request, baked into
   state_json). Good for replay — outcomes frozen, no re-sim drift; but never "what-if".

## (B) Endpoint + service map

All existing `/simulate/*` routes (`api/v1/simulate.py`) scope to a session's CURRENT hand only:
session (POST/GET), action, hand, leave, report/streets, report/leaks, preflop-chart,
postflop-chart, villain-range/{seat}, reveal/{scope}, explain. **No list/get-by-hand/history.**
Confirmed: every handler resolves via `_current_hand(db, session)`.

- Write path: `_deal_and_advance` (`:176-205`) inserts SimHand/hand; `apply_hero_action`
  (`:768-832`) rewrites `state_json` + inserts SimDecision (+ DrillAttempt if baseline-graded),
  one `db.commit()` (atomic, `:827-829`).
- Read: `_current_hand` (`:208-213`); `_hand_decisions` (`:256-260`, by `sim_hand_id`, sorted
  ordinal — reusable for any past hand).
- `hand_no` = per-session monotonic (start 1 `:731`, +1/deal `:1299`). **No per-day numbering
  anywhere.** "2026-07-22 Hand 32" must be DERIVED from `created_at` (UTC) grouped by calendar day
  + computed per-day ordinal.
- No index on `sim_hand.created_at`; `sim_hand` has no own `owner_id` (join via `sim_session`).
  Cross-session day-grouped list ⇒ join + bucket; a migration index likely warranted (unbounded
  row growth).

## (C) FE integration map

- **Routing** (`lib/hashRoute.ts:10-12`): `View` = closed union, no parameterized segment. New
  history view ⇒ extend `Route`/`parseHash`/`formatHash` + `App.tsx:31-38` nav + `:394-400` switch.
- **`SimTable`** (rendered `SimulateView.tsx:750-761`): felt from `SessionView.hand` + client pacing
  (`stagedIndex`, `revealAt`) built for the LIVE bot-batch since last hero click; derives board from
  `hand.events` via `simPlayback.ts:19-45`. NOT past-hand aware; a replay drive needs rethink or a
  parallel "replay mode".
- **`SimEventLog`**: renders `hand.events` = rolling "since last hero turn" window, no absolute
  position, never saw hero's own actions. **Cannot repoint at a past hand** — needs new full
  `action_history` wire shape.
- **`SimRecap`**: renders `GradeView[]` from `_hand_decisions` + `_grade_view` by any `sim_hand_id`
  — **reusable largely as-is**, except verdict/reasoning text = None for any non-live hand (gap A2).
- **`SimShowdown`**: `_view` reveals all compared hole cards when `hand_over` (`:676-685`); R1
  `reveal()` (`:1244-1286`) exposes fold-outs on demand but only for current hand. **NO-PEEK
  correction (Codex LOW):** although all hole cards sit in `state_json` server-side for a completed
  hand, the LOCKED replay policy (spec §5) is staged reveal — villain hole cards stay hidden through
  every step and are emitted ONLY at the terminal showdown step, ONLY for `settle().showdown_seats`
  (folded seats never). The server must NOT ship a hidden villain's cards for the client to conceal;
  build each `ReplayStepView` field-by-field so unrevealed cards are structurally absent from the
  wire. (Earlier draft's "no privacy reason to withhold" is superseded.)

## (D) Invariants this feature must not break

| Invariant | Enforcement | Relevance |
|---|---|---|
| `domain/` no web/DB imports | `tests/test_domain_purity.py` | A reconstruction helper in domain takes plain HandState in; if it needs DB, it lives in `services/`. |
| freq+EV never boolean; EV ≈approx | `schemas/simulate.py:54,213` | Replay UI keeps correctness tier + ev_loss + coverage; never pass/fail collapse. |
| Schema change ⇒ Alembic migration | `alembic/versions/0001-0012` | New index (created_at) or persisted verdict text ⇒ migration `0013_*`. |
| `spot_signature()` frozen | `domain/srs.py:48`; sim uses `_sim_signature()` | Replay-time re-grade must not route through SRS `record_attempt()`. |
| FE types hand-maintained | `frontend/src/api/types.ts` | New endpoints ⇒ manual `types.ts` edit (no gen step). |
| Hero-only wire privacy structural | `schemas/simulate.py:1-8`; `_view` field-by-field | New history/replay view built field-by-field from state_json; never serialize HandState raw (even though all cards OK to reveal for a completed hand). |
| CSS tokens / AA / focus | project CLAUDE.md | New replay components use tokens only. |

## (E) Open decisions for the human
1. Grading "why" text: persist via migration / re-grade live / show only tiers+EV.
2. Scope: current session only vs all sessions ever (index/scale question).
3. Day-numbering "Hand 32": per-day ordinal (derive from created_at) vs per-session hand_no.
4. Replay feel: animated step-through (new action_history wire + FE replay driver) vs static
   box-score recap (reuse SimRecap) vs hybrid stepped log.
5. Reveal UX: stage the fold-suspense retroactively vs show full showdown immediately (it's history).
