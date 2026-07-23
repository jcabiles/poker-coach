# Tickets — Simulate Hand-History + Replay

Spec: `docs/ai-dlc/specs/sim-hand-replayer.md` · Contracts: `docs/ai-dlc/contracts/sim-hand-replayer.md`.
Refuter FAIL findings folded (2 HIGH redesigned, 3 MED/LOW). **Codex Sol review now DONE**
(`codex exec --sandbox danger-full-access -m gpt-5.6-sol`, 2026-07-23) → FAIL with 8 findings, all
folded: legacy-hand assertion softened (HIGH), `inaccuracy`→`{mistake,blunder}` (MED), per-day
ordinal = Nth-completed + UTC tzinfo normalize (MED/LOW), 0013 downgrade must `drop_index` the
`sim_hand.created_at` index (MED), replay-last-hand resolves by `(session_id, hand_no)` since live
wire has no `sim_hand_id` (MED), all-in terminal board = final `state.board` (MED), contract NO-PEEK
contradiction fixed (LOW). Graded gate + seat-map claims verified TRUE by Codex. Branch off `main`. Single-agent ticket-by-ticket
(hotspots `sim_session.py`, `app.css`, `types.ts`, `App.tsx` are single-owner → serialize, don't
parallelize across them).

## DAG
```
T1 migration+model ─┬─ T2 persist-verdict-text ─ T3 read-services+endpoints ─┬─ T4 FE types+routing ─┬─ T5 HistoryView ─┐
                    │            (both own sim_session.py — serial)          │                       ├─ T6 HandReplay ──┼─ T7 shortcut ─ T8 verify
                    └──────────────────────────────────────────────────────┘                        └──────(app.css single-owner: serial)┘
```

## Tickets

- **T1 — Migration 0013 + model fields.** Add `SimDecision.verdict_tier_text` + `reasoning_text`
  (both `str|None`) to `db/models.py`; write `alembic/versions/0013_*.py` (`down_revision="0012"`)
  adding those two nullable columns + an index on `sim_hand.created_at`. **Downgrade uses
  `op.batch_alter_table`** to drop the columns (SQLite; follow 0012 precedent) **AND an explicit
  `op.drop_index` for the `sim_hand.created_at` index (Codex MED — batch on `sim_decision` won't
  remove an index on `sim_hand`; a re-upgrade would fail).** Owns: `db/models.py`, new migration.
  **Done:** `alembic upgrade head` then `downgrade -1` then `upgrade head` clean on SQLite; index
  absent after downgrade (asserted); existing rows read NULL text; `verify.sh` green.

- **T2 — Persist verdict text (graded-gated).** In `apply_hero_action` (`sim_session.py`), when
  inserting the `SimDecision` row, also write `result.tiers` text **only when `graded`**
  (`result is not None and coverage != NOT_FOUND`), else NULL — matching the live suppression at
  `:830`. Owns: `sim_session.py` (write path only). **Done:** unit test — a graded decision
  persists non-NULL tier+reasoning; a NOT_FOUND decision persists NULL; live `_view`/recap output
  byte-unchanged (existing tests green).

- **T3 — Read services + schemas + endpoints.** Add `list_history` (join+owner, `status=="complete"`,
  order `created_at ASC, id ASC`, UTC day-bucket **normalizing naive SQLite timestamps as UTC —
  Codex LOW**, per-day ordinal = Nth-completed) and `get_hand_replay` (scrubbed step list from
  `action_history`; `position→seat` map from `state.seats`; hero-verdict correlation via hero
  non-POST actions zipped to `_hand_decisions` sorted by ordinal — **correlate up to `min(len)` and
  treat a hero action with no decision row as ungraded rather than hard-asserting equality, for
  legacy 0009-era hands; Codex HIGH**; staged reveal = villains only at terminal showdown step for
  `settle().showdown_seats`; **terminal-step board = final `state.board` so all-in auto-runouts show
  the full runout — Codex MED**). Add view types to `schemas/simulate.py` (field-by-field, no raw
  HandState); add `GET /simulate/history` + `GET /simulate/hand/{sim_hand_id}/replay` (+ a
  `(session_id, hand_no)` resolution path for T7) to `api/v1/simulate.py`. Owns: `sim_session.py`
  (read path), `schemas/simulate.py`, `api/v1/simulate.py`. **Done:** tests — (a) NO-PEEK: no
  villain card in any pre-showdown step; (b) seat map total/correct + verdict aligns to right hero
  turn (post-0010 `len(hero_non_post)==len(decisions)`; legacy-shortfall handled as ungraded, not a
  crash); (c) per-day ordinal restarts per UTC day, stable under `created_at` tie via id, midnight
  naive+aware inputs bucket correctly; (d) mistakes filter matches `{mistake, blunder}` (NOT
  "inaccuracy"); (e) 404 on missing/not-owned/in-progress hand; (f) all-in flop→river terminal step
  shows 5-card board; (g) no endpoint emits `state_json`/`full_board`. `verify.sh` + `ruff` green.

- **T4 — FE types + routing + nav.** Manually add matching types to `api/types.ts`; add `"history"`
  to the `View` union + `parseHash`/`formatHash` (`lib/hashRoute.ts`); add nav entry + view-switch
  case in `App.tsx`. Owns: `types.ts`, `hashRoute.ts`, `App.tsx`. **Done:** `npm run typecheck` +
  `build` green; `#/history` routes to a placeholder History view.

- **T5 — HistoryView component.** Fetch `/simulate/history`; render day-grouped list (date headers,
  per-day "Hand N" labels, worst-tier chip) + a "mistakes only" toggle (client-side on tier data;
  losing set = `{mistake, blunder}`, NOT "inaccuracy" — Codex MED); select a hand → open replay.
  Owns: `HistoryView.tsx`, `app.css` (its block). Tokens only, AA + focus both themes. **Done:**
  list renders grouped by day, toggle filters to hands with a mistake/blunder decision,
  typecheck+build green.

- **T6 — HandReplay component.** Fetch `/simulate/hand/{id}/replay`; Next/Prev stepper over steps,
  board strip per street, per-seat cards under staged reveal (villains hidden until showdown step),
  inline hero verdict panel (tier + EV-loss + coverage + reasoning when present; "no baseline yet"
  when NULL). Owns: `HandReplay.tsx`, `app.css` (its block — serialize with T5). Reuse static
  card/seat presentational bits; NO live-pacing wiring. **Done:** stepping reconstructs the hand;
  no villain card visible before showdown step; verdict shows on hero steps; typecheck+build green.

- **T7 — "Replay last hand" shortcut.** In `SimulateView.tsx`, add a control (shown once a hand is
  complete) that opens the just-played hand in the replayer. **The FE has no `sim_hand_id` (live
  wire exposes only `session_id` + `hand_no`; Codex MED)** — resolve via the `(session_id, hand_no)`
  path added in T3; do NOT add `sim_hand_id` to the live `SimulateHandView` (byte-unchanged promise).
  Owns: `SimulateView.tsx`. **Done:** after a hand settles, the control opens that hand's replay via
  `(session_id, hand_no)`; typecheck+build green; existing SimulateView behavior unchanged.

- **T8 — Verify + design review.** Full pass: `verify.sh` (+ new tests), `ruff`, `typecheck`+`build`;
  migration up→down→up on SQLite; boot probe. Offer `design-reviewer` on the two new FE views
  (premium rubric + AA + focus both themes). **Done:** all green; design-review verdict recorded;
  roadmap "Hand replayer" item marked `[x]` with a done-note + any deviations.

## Parallelization
Backend chain T1→T2→T3 is strictly serial (shared `sim_session.py`). T5‖T6 could parallelize but
share `app.css` — only via worktree isolation + union-merge; default serial. T7 after T6. T8 last.
Recommended: single agent, ticket-by-ticket, in order.
