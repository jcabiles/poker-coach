# Contracts — Simulate S10 (grading wire-in) + S11 (pacing/polish)

> Fresh read-only scan by `contract-mapper` on 2026-07-11 against HEAD of
> `feat/simulate-wave4` (S9 landed). Supersedes the FE-table sections of
> `game-table-feedback.md` / `card-room-polish-ux.md` (those predate the `Sim*`
> components). The feedback-tier composition facts in `game-table-feedback.md`
> are still valid. Consumed by `specs/simulate-s10.md` + `specs/simulate-s11.md`.

## 1. Grading reuse pattern (the seam S10 copies)

- `grade_drill` (`backend/app/api/v1/drill.py:321-349`) is the template: `await _provider.evaluate(spot, action)` on a module-singleton composite (`drill.py:60`, from `providers/factory.py:28`). Reuse the SAME singleton — do not construct a second provider.
- `EvaluationResult` (`backend/app/domain/evaluation.py:61-78`): `per_action`, `best_action`, `chosen_eval`, `ev_loss_bb`, `correctness: Correctness|None` (OPTIMAL/ACCEPTABLE/MISTAKE/BLUNDER — never boolean), `rationale_tags`, `explanation`, `provider`, `leak_category`, `coverage: Coverage` (FULL/PARTIAL/NOT_FOUND), `is_mixed`, `authored_rationale`, `tiers: FeedbackTiers|None`.
- **Coverage gate is load-bearing** (`drill.py:328`): `if result.coverage != NOT_FOUND:` guards ALL persistence. NOT_FOUND is the ONLY "no baseline yet" enforcement. A sim grade that is NOT_FOUND must surface "no baseline yet" and write NOTHING (no `sim_decision`, no `drill_attempt`).
- **`record_attempt` is the SRS write path** (`services/review.py:49-95`, only prod caller `drill.py:348`). S10 must NOT call it ("no SRS writes" invariant). Write `sim_decision` + a tagged `drill_attempt` row directly instead.

## 2. Hero-decision → Spot mapping (the hard part)

Sim state at a hero decision (`services/sim_session.py:149-222`, `HandState` `domain/table/engine.py:52-64`) exposes hole cards, board, street, live pot (derived), positions (full 9-max, maps 1:1 to `Position`), per-seat `persona_type`/`stack_bb`, and `legal_actions(state)`.

**Why most spots are unmappable:**
- Postflop graders (`scenarios.py` `build_*_spot`, `providers/postflop.py`) are **2-player HU by construction** — they compute `hero_range`/`villain_range` from fixed `(opener, caller)` position pairings + fixed 0.33/0.75 bet-fraction buckets. No function derives ranges or maps a 9-max multiway betting line to a `NodeContext` archetype from a live `HandState`.
- `postflop.py:22-26` `supports()` requires `street==FLOP` and `node_context in {CBET,VS_CBET,VS_CHECK_RAISE}`. Turn/river providers exist but are also HU-only.
- Preflop `registry.lookup()` (`content/registry.py:32-37`) keys on `(node_context, position, facing, limper_count, villain_type)` against a fixed HU content index — most live 9-max preflop lines won't match → legitimate NOT_FOUND.
- `is_multiway(spot)` (`spot.py:170-172`) is only an SRS-label binary; multiway spots still hit 2-player graders → NOT_FOUND.

**Fields sim state lacks for a mapping:** a live-line→`NodeContext` classifier; `hero_range`/`villain_range` strings; singular `facing` when >1 villain live; `limper_count` helper; a `villain_type` collapse rule when multiple personas are live.

**Rule:** the mapper cleanly succeeds ONLY for HU-shaped moments matching a canonical `NodeContext` + on-pack preflop `(position, facing, limper_count)`. Everything else → NOT_FOUND / "no baseline yet." **Never fabricate a plausible-but-wrong Spot** (guessed ranges, arbitrary villain persona) — a confidently-wrong badge is worse than none.

**Never** pass a sim-derived `Spot` to `spot_signature()` or `record_attempt()` (frozen-hash + no-SRS invariants both forbid it).

## 3. `sim_decision` — net-new table (confirmed absent)

Models in `db/models.py`: `SimSession` (`:40-51`), `SimSeat` (`:54-64`, composite PK), `SimHand` (`:67-80`, `state_json` server-only). Migration pattern `0009_sim_tables.py`: `op.create_table`, `owner_id=""` sentinel, explicit `op.create_index`, symmetric `downgrade()`. New migration chains off 0009 → **0010**, `down_revision="0009"`.

A `sim_decision` row links to: `session_id` (FK sim_session), `sim_hand.id` (FK — robust per-hand key for recap; `hand_no` alone isn't globally unique), `street` + a decision ordinal (must be assigned at grade time — `state_json` has no decision index today), plus the persisted verdict fields (correctness, ev_loss_bb, leak_category, chosen_action, coverage) for badge + recap.

**Ordering hazard:** `apply_hero_action` (`sim_session.py:266-289`) is the ONLY server entry for a hero `Decision`. It applies immediately (`state = apply(state, decision)` `:278`). The grade must read the **pre-`apply()`** state (loaded `:275`), before mutation — not the post-advance state at `:280`.

## 4. `drill_attempt.source` (confirmed absent)

`DrillAttempt` (`db/models.py:22-37`) has no `source`. Write sites: `drill.py:337-346` (grade), `:445-453` (quiz). **Sharpest stats hazard:** `stats.py` `leak_stats` (`:39`), `summary` (`:79`), `calendar` (`:130`), `recap` (`:161`), `hand_error_weights` (`:193`) filter by `owner_id` ONLY — none discriminate source. Adding `source='simulate'` rows WITHOUT adding a `source` filter to all five silently blends sim data into every Practice dashboard. **Decision (Gate 1): add `source` (default 'practice'), write a tagged sim row, and add `WHERE source=='practice'` to all five Practice reads.**

## 5. Sim FE surface

- Mount: `App.tsx:389-390` → `SimulateView.tsx` owns `view: SessionView|null`, renders `SimTable`, `SimActionBar` (`is_hero_turn`), `SimShowdown` (`hand_over`), aside `SimEventLog`+`SimLedger`.
- Wire: `schemas/simulate.py` `SessionView{session_id, hand}`; `SimulateHandView{seats, hero, to_act_seat, is_hero_turn, legal_actions, events, hand_over, showdown}`; mirrored in `types.ts:236-255`. `events` = bot actions since last hero decision, **resets each request**.
- **Badge seam (S10):** no per-decision slot exists. Add a field on the response (e.g. `hand.last_grade`) carrying the verdict for the decision just taken; render a badge on the hero pod (`SimTable.tsx:91-124` heroseat block). "no baseline yet" is a distinct badge state.
- **Recap seam (S10):** new sibling component in the `hand_over` branch (`SimulateView.tsx:230-237`); reads `sim_decision` history for the hand. SimShowdown stays settlement-only.
- **Pacing (S11) is client-side only:** `advance_to_hero` (`domain/table/play.py:161-201`) resolves the whole bot sequence synchronously before the HTTP response; `events` arrives as one batch. Pacing = client replay/stagger over that batch (SimEventLog is the seam per its own S9 comment). Hero-fold → instant resolution = client skips animation, calls next-hand. No server streaming.
- **CSS:** the Simulate block is `app.css:2576-2986` (wave 4.5 appended the table-size section at the tail: wide-shell `.app:has(.simulate)` rule, sim ring caps 5x/4x, single-column gate raised 900->1100px; SimTable slotStyle top y-radius now 41), all `.sim-*`, tokens-only. `SimTable` reuses PokerTable's shared `.stage/.felt/.tablering/.tseat/.pos/.card` — **S11 must touch only `.sim-*` overrides**, never the shared base classes (would bleed into Practice/Quiz).

## 6. Cross-slice file contention (S10-FE vs S11-FE)

Both slices touch: `SimulateView.tsx` (render tree + `run`/`decide` callbacks), `SimTable.tsx`, `SimActionBar.tsx`, `SimEventLog.tsx`, `SimShowdown.tsx`, `types.ts`, `app.css` (`.sim-*` block). **Line-level collision in `SimulateView.tsx` is near-certain** → S10-FE and S11-FE must be sequenced, never same-wave. Lowest contention if S11 speed setting stays inside `SimulateView`/`SimEventLog` (client-only) and S10 badge/recap land in `SimTable`/new `SimRecap`.

## Sharpest hazards (ranked)

1. Silent-grade on multiway/off-archetype spots — protect the NOT_FOUND propagation; never fabricate a Spot.
2. `stats.py` corruption if tagged sim rows land without a source filter on all five reads.
3. `apply_hero_action` mutation ordering — grade the pre-`apply()` state.
4. `spot_signature()`/`record_attempt()` must never see a sim Spot.
5. S11 pacing has no server hook — client-side replay only.
6. Shared felt classes are cross-owned with Practice's `PokerTable` — S11 edits `.sim-*` only.

## Single-owner-contested files (keep one owner per wave)

`SimulateView.tsx` · `SimTable.tsx` · `SimActionBar.tsx` · `SimEventLog.tsx` · `SimShowdown.tsx` · `types.ts` · `app.css` (`.sim-*`) — S10-FE and S11-FE never share a wave on these.
