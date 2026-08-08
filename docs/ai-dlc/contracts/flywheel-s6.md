# Contract map — S6 detection-protocol feasibility pilot

Mapped 2026-08-07 by contract-mapper (read-only scan), persisted by director.
Governing preregistration: `poker-analytics:docs/methods/estimand-contract.md` §d (lines 439–539).

## 1. Human (HERO) hand storage

- SQLite via SQLModel: `SimSession` (`backend/app/db/models.py:45-56`), `SimSeat` (`:59-69`),
  `SimHand` (`:72-85`), `SimDecision` (`:88-137`).
- `SimHand.state_json` (`models.py:84`) holds the full server-side `HandState` (all 9 seats'
  hole cards + board) — the only complete, replayable record of a human hand.
- `HERO_SEAT = 0` hard-pinned (`backend/app/services/sim_session.py:120`).
- Session boundary: `SimSession.hand_no` increments per hand within one `session_id`
  (`sim_session.py:1407-1408`) — maps directly to §d.2's "30 consecutive hands, never
  crossing a session boundary".
- The pinned 1,228-hand corpus is ONE live, still-growing session
  (`docs/ai-dlc/research/persona-realism-artifacts/remeasure-2026-08-05/PROTOCOL.md:10-11`,
  session `0650a0194ea14717b9523dfc86719639`, `hand_no<=1228`). Current count needs a live DB
  query at execution time; the pin is stale by definition.
- Stacks: every hand re-buys all seats to a RANDOMIZED target in [95,105]bb
  (`sim_session.py:148-149`, `_rebuy_seats` `:220-233`) — deliberate realism (T-STACK).

## 2. Bot self-play hands

- `backend/tools/export_analytics.py` — production-policy self-play, every seat driven by
  `bot_decision` (`:65`, `:215`), same code path as the live table.
- Seat = fixed 9-slot array; `persona_by_seat = {i: lineup[i % len(lineup)]}` (`:292`) —
  one seat = one persona for the whole run (session-analogous). `hand_no` sequential (`:307-316`).
- Every seat resets to EXACT `STACKS_BB = 100.0` every hand (`:89`, used `:163,244,334`).
- Seeding: one CLI `--seed` drives deals + all persona draws (`:18-20`);
  `run_id = run-s{seed}-n{n}-c{hash[:12]}` (`:303`).
- Blinding must strip: `seat_rows[..]["persona"]` (`:241`), manifest `lineup` (`:333`),
  `DEFAULT_LINEUP` (`:95`).
- Output is Parquet analytics rows, NOT narrative text.

## 3. Rendering — no shared byte-identical pipeline exists (new work)

- Human side: `backend/tools/export_session.py` renders markdown per hand via `hand_block()`
  (`:273-324`) + `fmt_action()` (`:252-270`) — the ONLY hand-history text renderer.
  LEAKS today: `Table:` line lists every seat's persona name (`:295-298`); `fmt_action`
  tags non-focus seats with persona strings (`:255`); showdown reveals opponent hole cards
  (`:316-323`); stack line computed `stack_bb + invested_total_bb` (`:287`).
- Bot side: NO text renderer exists. Both sources share the same domain engine
  (`start_hand`/`apply`/`settle`) so a shared renderer is buildable.
- Working-agreement constraint (`poker-analytics:docs/WORKING-AGREEMENT.md:98`): never parse
  rendered hand text for statistics — pilot statistics must come from structured data.

## 4. Leak-risk list (class tells for non-play reasons)

1. **Stack determinism (highest):** bot exactly 100.00bb every hand vs human randomized
   95–105bb — near-certain statistical tell over a 30-hand bundle. Fix = match bot buy-in
   spread (export behavior change) or normalize both in rendering.
2. **Persona-name leak** in the only existing renderer (above) — must strip; opaque IDs only.
3. **HERO_SEAT=0 always** vs bot seats 0–8 — bundle construction must re-key to opaque,
   class-blind IDs.
4. **Renderer drift:** §d pins "shared rendering code" as a leak control; today zero shared
   code exists. The renderer must be literally one code path, not two implementations.
5. **Analytics-only fields** in bot Parquet (`engine_node_key`, `hand_class_bucket`,
   `raise_to_bb`, `seq`, `config_hash`, `run_id`) have no human-side counterpart — structural
   leak if they reach rendered output.
6. **Corpus liveness:** 1,228 pin stale; re-pin `hand_no<=N` at execution
   (mirror `export_session.py --max-hand-no`, `:628-634`).
7. **Blinds/stakes:** appear symmetric via shared engine; spot-check a rendered example from
   each side before launch (§d.2 requires stakes metadata removed).
8. **Timing:** confirmed symmetric — neither side records inter-action timestamps
   (`models.py:85,137`; `export_analytics.py:304,312-316`) — consistent with §d.2.

## 5. Ownership (tripwire — surfaced to owner, not silently resolved)

- Working agreement §1 (`WORKING-AGREEMENT.md:8-21`): "Human-hand corpus (future, post S2b
  gate)" → poker-analytics — but that row means the EXTERNAL licensed multi-player corpus,
  not the owner's own hands in poker-coach's DB. Which repo owns the S6 bundle-extraction /
  judging tooling is UNSTATED.
- §7 (`:87-90`): S6 runs parallel to S5 after S2a+S3 — no S2b dependency stated for S6.
- §8 (`:92-107`): no bot-policy or committed pack changes before the phase-3 gate — relevant
  if the stack-leak fix touches `export_analytics.py` behavior (export-side, not domain
  policy; likely outside the freeze but flagged).
- Never-push boundary (`:100-101`): `persona-realism-artifacts/` is LOCAL/gitignored (owner
  hand data). S6 corpus artifacts derived from real hands belong under the same umbrella
  unless explicitly scoped otherwise.

## 6. Reusable S4 machinery

- Manifest-written-last convention (`export_analytics.py:319-361`): run_id, seed, lineup,
  config_hash, git_sha, row_counts — model for the S6 pilot manifest (bundle IDs, class
  labels, blinding map, judge outputs).
- `sweep_runner.py` fail-closed + determinism-recheck patterns (`:1-63`).
- `export_session.py --max-hand-no` — the existing reproducible-slice pin mechanism.
- Traceability rule (`WORKING-AGREEMENT.md:55-56`): every cross-repo artifact traceable to
  (engine sha, seed, config).
