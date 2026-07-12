# Tickets — Simulate S10 + S11 (wave DAG)

> Specs: `specs/simulate-s10.md`, `specs/simulate-s11.md`. Contract: `contracts/simulate-s10-s11.md`.
> Refuter verdict: SHIP (4 guardrails folded into the specs).
> One file = one owner **per wave**. Hotspots (`app.css`, `types.ts`, `alembic/versions/`,
> `db/models.py`) are single-owner. Maker ≠ checker: every wave fan-in gets a fresh `refuter`;
> FE waves also get `design-reviewer`. Sub-agents never spawn sub-agents.

## Serial spine
`T0 (frozen contract) → W1 [T1 ‖ T2 ‖ T3] → W2 [T4] → W3 [T5 + final design-review]`
Peak concurrency = **3 makers in W1** (2 backend S10, 1 FE S11) — pieces of BOTH slices run at once.
The FE files (`SimulateView`/`SimTable`/`app.css`) force S10-FE (W2) and S11-polish (W3) to follow S11-pacing (W1) sequentially.

---

## T0 — Frozen contract (lead, direct — do FIRST, blocks everything)
**Does:** commit the shared schema + wire shapes so W1 makers build against a fixed target.
- `db/models.py`: new `SimDecision` model (FK `session_id`→sim_session, `sim_hand_id`→sim_hand, `street`, decision ordinal, `chosen_action`, `correctness`, `ev_loss_bb`, `leak_category`, `coverage`, `owner_id=""` sentinel); add `source: str = Field(default="practice")` to `DrillAttempt`.
- `alembic/versions/0010_sim_decision_and_source.py`: additive — create `sim_decision` (0009 pattern + indexes on `session_id`/`sim_hand_id`), add `source` to `drill_attempt`; symmetric `downgrade()`.
- `schemas/simulate.py`: add nullable `last_grade` (verdict for the just-taken decision, incl. a "no baseline yet" state) to the hand view + a recap payload (per-decision verdict list) for the hand-over branch.
- `test_domain_purity.py`: add the new mapper module (`app.domain.table.grade_map`) to the allowlist.
**Owns:** `db/models.py`, `alembic/versions/0010_*`, `schemas/simulate.py`, `test_domain_purity.py`.
**Done:** `./scripts/verify.sh` green with the migration applied + reversible; models import; no behavior change yet.

---

## W1 — three makers, disjoint files (parallel)

### T1 — Spot mapper + grade wire (heavy-worker · S10 backend)
**Does:** NEW pure-domain `domain/table/grade_map.py`: live `HandState` + hero seat → `Spot | None` (HU-canonical shapes only; returns `None` for anything not buildable with full confidence — no fabricated ranges/facing/villain). Wire into `services/sim_session.py` `apply_hero_action`: map the **pre-`apply()`** state → `evaluate()` via the `drill.py` provider singleton → coverage gate → `db.add()` a `SimDecision` row (+ tagged `DrillAttempt(source='simulate')` when non-NOT_FOUND); NOT_FOUND/unmappable ⇒ `SimDecision` "no baseline yet", NO `drill_attempt`. **All `db.add()` ride the single existing `db.commit()` (`:288`) — no separate commit.** Populate `last_grade`; add the recap read path for a finished hand's decisions.
**Acceptance:** a bad HU preflop play grades (freq+EV verdict, non-tautological); a multiway/off-pack decision → `last_grade`="no baseline yet" + no `drill_attempt`; grade reads pre-mutation state; failed `apply()` leaves zero graded rows; **mapper property test** (refuter low-3): for sampled mapped states, the Spot's `hero_range`/`villain_range`/`facing` match the equivalent `scenarios.py` builder for that canonical shape. Domain-purity green.
**Owns:** `domain/table/grade_map.py`, `services/sim_session.py`, `api/v1/simulate.py`, mapper tests.
**Depends:** T0.

### T2 — Stats source-filter + persistence test battery (implementer · S10 backend, independent checker of T1)
**Does:** add `WHERE source == 'practice'` to `stats.py` `leak_stats`/`summary`/`calendar`/`recap`/`hand_error_weights` so Practice dashboards exclude sim rows. Backend test battery: zero `srs_item` rows from a Simulate session; sim attempts carry `source='simulate'` and are queryable by source yet excluded from the five Practice reads; migration 0010 up/down clean + existing rows read unchanged.
**Acceptance:** all named tests green; a sim leak is visible by source, invisible to Practice stats.
**Owns:** `services/stats.py`, `backend/tests/` (new sim-grading test file + stats-test edits).
**Depends:** T0. (Runs ‖ T1; the no-SRS/tag/unmapped tests exercise T1's wire and go green at the W1 fan-in barrier once both merge.)

### T3 — S11 pacing + fold-skip (ux-ui · S11 frontend)
**Does:** client-side replay of the returned `events` batch. `SimEventLog` staggers reveals; `SimulateView` holds a shared staged index + speed setting (localStorage, **normal default**, ~0.5–1.5s) + hero-fold ⇒ skip animation + auto-deal next; `SimTable` reveals bot seat state (fold-dim/chips/all-in) in **lockstep** with the log (refuter med-2 — firm); `SimActionBar` disabled during playback; a speed picker in the Simulate chrome. Honor `prefers-reduced-motion` (instant). `.sim-*` pacing CSS only — never shared felt base classes.
**Acceptance:** speed setting changes pacing + persists across reload; hero-fold skips ahead; felt + log stay in lockstep (no seat shows final state before its log line); reduced-motion disables stagger; typecheck/build green.
**Owns:** `SimEventLog.tsx`, `SimulateView.tsx`, `SimTable.tsx`, `SimActionBar.tsx`, `app.css` (`.sim-*` pacing subset).
**Depends:** none (S9 surface). **Checker:** `design-reviewer`.

**W1 fan-in barrier:** `./scripts/verify.sh` + `ruff` + FE typecheck/build all green; fresh `refuter` on T1+T2; `design-reviewer` on T3. Merge, then W2.

---

## W2 — one maker

### T4 — S10 badge + recap FE (ux-ui · S10 frontend)
**Does:** color badge (verdict tier / "no baseline yet") on the hero pod in `SimTable`; NEW `SimRecap.tsx` (per-street freq/EV ≈-labeled + tiered "why" expanded for mistakes/blunders) mounted beside `SimShowdown` on `hand_over`; `SimulateView` threads `last_grade` → badge and renders `SimRecap`; recap **summary** figures exclude "no baseline yet" rows (refuter low-4), per-decision list still shows them; `types.ts` mirrors the new response fields; `.sim-*` badge/recap CSS (tokens-only, AA both themes).
**Acceptance:** bad HU preflop play → red badge + blunder recap w/ reasoning; unmapped → "no baseline yet"; aggregates exclude no-baseline rows; typecheck/build green.
**Owns:** `SimTable.tsx`, `SimRecap.tsx`, `SimulateView.tsx`, `types.ts`, `app.css` (badge/recap subset).
**Depends:** T0 (response shape) + T1 (backend fills `last_grade`) + T3 merged (FE files vacated). **Checkers:** `refuter` + `design-reviewer`.

---

## W3 — one maker + final review

### T5 — S11 tokens/polish pass (implementer/ux-ui · S11 frontend, last)
**Does:** tokens-only polish across the full `.sim-*` block incl. badge/recap coherence, spacing rhythm, legibility, motion timing; final `design-reviewer` across themes + breakpoints.
**Acceptance:** design-review verdict acceptable (AA contrast + focus both themes); no regression to Practice/Quiz's table; build green.
**Owns:** `app.css` (`.sim-*`).
**Depends:** T4 merged. **Checker:** `design-reviewer` (final).

---

## Parallelizability summary
| Wave | Makers (parallel) | Slices touched |
|---|---|---|
| T0 | lead (serial root) | S10 schema |
| W1 | T1 ‖ T2 ‖ T3 | **S10 backend + S11 pacing simultaneously** |
| W2 | T4 | S10 FE |
| W3 | T5 | S11 polish |

Known deferrals (out of scope, tracked in roadmap NEXT): multiway/exploit-aware grading; turn/river teaching in Practice; SRS for sim spots; mobile responsiveness.
