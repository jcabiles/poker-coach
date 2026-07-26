# Tickets — History-page villain reveal

**Spec:** `docs/ai-dlc/specs/history-villain-reveal.md`
**Contracts:** `docs/ai-dlc/contracts/history-villain-reveal.md`
**Branch:** cut a fresh `feat/history-villain-reveal` from an up-to-date `origin/main`.

> ⚠️ **Do not build on `feat/persona-realism-wave-a-w1`.** That branch has ~110 lines
> of uncommitted work in `backend/app/services/sim_session.py` — the exact file T2
> edits. Commit or stash it first. Per repo memory, `git switch -c` is broken in this
> sandbox: use `git branch --no-track <new> origin/main` then `git switch <new>` as
> two separate calls.

> **Line numbers in the spec are approximate** for `sim_session.py` only (it drifts).
> `grep -n "^def <name>"` before editing. Every other file is unmodified and stable.

## DAG

```
T0 ─┐                          (independent guard — start first)
    │
T1 ─┼─ T2 ─ T3 ─┐
    │            ├─ T7 ─ T8
T4 ─── T5 ─ T6 ─┘
```

| Wave | Tickets | Notes |
|---|---|---|
| 1 | **T0**, **T1** | fully parallel, disjoint files |
| 2 | **T2**, **T4** | T2 needs T1; T4 needs T1 |
| 3 | **T3**, **T5** | T3 needs T2; T5 needs T4 |
| 4 | **T6** | needs T5 |
| 5 | **T7** | needs T3 + T6 (first ticket that spans BE+FE) |
| 6 | **T8** | needs T7 |

`frontend/src/api/types.ts` and `frontend/src/styles/app.css` are profile **hotspots** —
single owner each. `types.ts` is owned solely by **T4**; `app.css` solely by **T8**.
No two tickets may hold either file.

---

## T0 — Characterization test: `/hand/{id}/replay` is byte-identical

**Do:** Add a regression test asserting the replay payload for a fixture hand is
unchanged by this feature — `revealed_seats == []` on every non-terminal step, and the
terminal step's `revealed_seats` exactly equals `settle().showdown_seats`.

**Why first:** it is the tripwire for the spec's #1 promise. Land it *before* any
production change so it is proven to pass on the pre-change tree.

**Owned files:** `backend/tests/test_sim_replay.py`
**Depends on:** nothing.

**Acceptance:**
- Covers at least one fold-out hand (empty `showdown_seats`) and one genuine showdown.
- Fails loudly if a later ticket adds a card to any non-terminal step.

**Done-condition:** `cd backend && .venv/bin/pytest tests/test_sim_replay.py -q`

---

## T1 — `HandRevealView` schema + fix the stale `RevealView` docstring

**Do:** Add `HandRevealView { available: bool, scope: str, seats: list[ShowdownSeatView] }`.
Correct `RevealView`'s docstring (`:227-233`), which still claims reveal is
hero-fold-only — the service docstring (`sim_session.py:1335`) records it was widened
to any completed hand.

**Owned files:** `backend/app/schemas/simulate.py`
**Depends on:** nothing.

**Acceptance:**
- Uses `ShowdownSeatView` (carries `delta_bb`), **not** `RevealedSeatView` — spec decision #2.
- `RevealView` itself is otherwise **unchanged** (the live Simulate page depends on it).
- New docstring states scope semantics and that `available` is a 200-body concern.

**Done-condition:**
`cd backend && ruff check . && .venv/bin/python -c "from app.schemas.simulate import HandRevealView; print(HandRevealView(available=False, scope='all'))"`

---

## T2 — `reveal_hand()` service

**Do:** Add `reveal_hand(db, sim_hand_id, scope, owner_id) -> HandRevealView`. Resolve
the hand with `_load_owned_complete_hand` (raises `SessionNotFound` → 404). Gate on
`REVEAL_ENABLED` and `_REVEAL_SCOPES`. Exclude `HERO_SEAT`. Build each seat from
`state.seats[i].hole_cards` plus the real `settle(state).deltas[i].delta_bb`.

**Owned files:** `backend/app/services/sim_session.py`, `backend/tests/test_sim_session.py`
**Depends on:** T1.

**Acceptance:**
- `last-in` → non-hero seats with end-of-hand `PlayerStatus` `IN`/`ALLIN`; `all` → all
  eight non-hero seats. (Review confirmed all 9 seats are always dealt; no sit-out status.)
- Unknown scope or `REVEAL_ENABLED = False` → `available=False`, `seats=[]`. **Not** an exception.
- `state.hand_over` false → `available=False`. An explicit branch, never a `None` deref.
- Hero seat never present in `seats`.
- Deltas come from `Settlement.deltas` only — nothing computed locally, nothing faked.
- `reveal()`, `_build_replay()`, and `settle()` are **not modified**.

**Done-condition:** `cd backend && .venv/bin/pytest tests/test_sim_session.py -q && ruff check .`

---

## T3 — Route + module docstring

**Do:** Add `GET /simulate/hand/{sim_hand_id}/reveal/{scope}` beside
`/hand/{sim_hand_id}/replay`. Map `SessionNotFound` → 404 `"hand not found"`. Add the
route to the module docstring's route table.

**Owned files:** `backend/app/api/v1/simulate.py`, `backend/tests/test_simulate_api.py`
**Depends on:** T2.

**Acceptance:**
- Path is exactly `/hand/{sim_hand_id}/reveal/{scope}` — **never** a bare
  `/{id}/reveal/{scope}`, which would collide with `/{session_id}/reveal/{scope}`.
  (Segment count makes the `/hand`-prefixed form safe at any declaration order — both
  reviewers confirmed; ordering is a readability choice, not a correctness one.)
- Unknown / not-owned / not-complete `sim_hand_id` → **404**.
- Capability off → **200** with `available: false`.
- The existing `/{session_id}/reveal/{scope}` route still resolves and still passes its tests.

**Done-condition:** `cd backend && .venv/bin/pytest tests/test_simulate_api.py tests/test_sim_replay.py -q`

---

## T4 — FE types + client function

**Do:** Hand-write the `HandRevealView` mirror in `types.ts` and add
`getHandReveal(simHandId, scope)` to `client.ts` beside the existing `getReveal`.

**Owned files:** `frontend/src/api/types.ts` *(HOTSPOT — sole owner)*, `frontend/src/api/client.ts`
**Depends on:** T1 (shape must match the Python schema exactly).

**Acceptance:**
- Field-for-field mirror of `HandRevealView`; reuses the existing `ShowdownSeatView` TS type.
- Comment notes the shape difference vs `RevealView` (which has no `delta_bb`) so the
  two are not confused later.
- `schema.d.ts` untouched — it is unwired; types are hand-maintained (repo invariant).

**Done-condition:** `cd frontend && npm run typecheck`

---

## T5 — Pure reveal-request module (**the HIGH finding**)

**Do:** Create `frontend/src/components/simulate/revealRequest.ts` — a pure,
dependency-free reducer owning reveal state and the stale-response guard. See the
spec's "The guard must be a PURE MODULE" section for the shape.

**Why it is its own ticket:** this is the one correctness defect both reviewers
flagged, and vitest-only tooling means it is *only* testable if it is pure. Do not
inline this into the component.

**Owned files:** `frontend/src/components/simulate/revealRequest.ts`,
`frontend/src/components/simulate/revealRequest.test.ts`
**Depends on:** T4.

**Acceptance — the three race cases are explicit tests:**
1. Reveal → toggle-off *before* the response lands → applying the response is a no-op;
   final state has no cards and `scope === null`.
2. `last-in` → `all`, responses arriving **reversed** → final state is `all`; the late
   `last-in` response is discarded.
3. Reveal hand A → switch to hand B → A's response arrives → hand B has **zero** cards.
- Plus: clicking the active scope clears; switching scope swaps.
- Zero imports beyond types. No React, no fetch, no timers.

**Done-condition:** `cd frontend && npx vitest run src/components/simulate/revealRequest.test.ts`

---

## T6 — Wire the state into `HistoryView`

**Do:** `HistoryView` holds the `revealRequest` state, calls `getHandReveal`, and
dispatches responses through `applyRevealResponse` with captured `{handId, scope, gen}`.
Clear reveal state explicitly in `openHand` and `closeReplay` (the child `key` remount
does **not** do this). Render an honest muted line when `available === false`.

**Owned files:** `frontend/src/components/HistoryView.tsx`
**Depends on:** T5.

**Acceptance:**
- Component contains **no** race logic of its own — it only fetches and dispatches.
- Reveal state explicitly cleared on hand open and on close.
- `available: false` → muted line, never a silent no-op.
- A failed fetch is non-fatal (leaves cards face-down), matching `SimulateView`'s
  handling; it must not blank the replayer.

**Done-condition:** `cd frontend && npm run typecheck && npm run build`

---

## T7 — Reveal controls + felt merge in `HandReplayTable`

**Do:** Add the two-button group and merge revealed cards into the pod render.

**Owned files:** `frontend/src/components/simulate/HandReplayTable.tsx`,
and `frontend/src/components/simulate/replaySeats.ts` + `replaySeats.test.ts` *only if*
the merge is done in the deriver.
**Depends on:** T3 + T6.

**Acceptance:**
- New props are **optional with defaults**, so `HandReplayTable` remains a clean host
  swap for `HandReplay` (roadmap `simulate-table.md:1336`).
- Cards face-up at **every** step, not only the terminal one.
- A revealed card **overrides** the `!seat.folded` guard (`:189`) so `all` shows early folders.
- Genuine showdown reveal **wins** over an on-demand reveal — mirrors
  `SimTable.tsx:181-186`; do not invent a new precedence.
- Buttons reuse `.sim-reveal-actions` / `.sim-reveal-btn`, with `role="group"`,
  `aria-label="Reveal villain hands"`, and correct `aria-pressed` that flips to
  `false` on toggle-off.
- `HandReplay.tsx`, `SimTable.tsx`, `SimShowdown.tsx`, `PokerTable.tsx` untouched.

**Done-condition:**
`cd frontend && npm run typecheck && npm run build && npx vitest run src/components/simulate/`

---

## T8 — Layout + a11y pass

**Do:** Lay the reveal group into the replayer's controls row.

**Owned files:** `frontend/src/styles/app.css` *(HOTSPOT — sole owner)*
**Depends on:** T7.

**Acceptance:**
- `.sim-reveal-btn` carries `flex: 1 1 0` (`app.css:3219`), which fights
  `.hrt-controls` (`:5417`). Fix with **History-scoped** rules — the shared
  `.sim-reveal-btn` rule must **not** be edited (the live Simulate page depends on it).
- Token values only — no raw hex/px outside `tokens.css`.
- AA contrast + visible focus in **both** themes. `[aria-pressed="true"]` is already
  styled at `:3227-3231`, so the pressed state comes free — verify, don't duplicate.
- Reflows clean at 1440 / 1024 / 375.

**Done-condition:** `./scripts/verify.sh` + `cd frontend && npm run build`, then a
`design-reviewer` pass on the replayer with reveal **on** and **off**, both themes,
at all three widths.

---

## Final gate (after T8)

Run once, by a single owner — **not** per-ticket. `./scripts/verify.sh` runs
`alembic upgrade head` against one shared SQLite file, so concurrent runs produce
phantom `database is locked` failures.

1. `./scripts/verify.sh` → `BACKEND VERIFY OK`
2. `cd backend && ruff check .`
3. `cd frontend && npm run typecheck && npm run build && npx vitest run`
4. Manual privacy check — spec Verify-by #10: with reveal **not** clicked, no villain
   hole card in the DOM or in any network response for a non-showdown seat.
5. Tick the slice in `docs/ai-dlc/roadmap/simulate-table.md` under **Hand replayer**
   (`:1295`), as a sibling of the two-pane redesign entry.

**No Alembic migration is expected.** If a ticket finds itself needing one, stop and
re-spec — it means the design drifted.
