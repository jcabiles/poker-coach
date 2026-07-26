# Contract map — History-page villain reveal (pre-scan for `/ai-dlc`)

**Scanned:** 2026-07-26 · **Intent:** give the Hand History page a toggle to reveal
villain hole cards, with the same `last-in` / `all` scopes the Simulate page offers.

**Owner decisions already taken (this scan's premises):**
- Routed to `/ai-dlc` as a **feature**, not a UX/UI pass — it needs a new backend
  endpoint, so `/ai-dlc-ux-ui` is out of scope for it.
- **Surface = inside the replayer, felt-wide.** Two buttons in `HandReplayTable`'s
  controls row; revealed cards flip the villain pods on the stepped felt. No reveal
  from the history list rows; no persisted cross-hand preference.

This document is read-only reconnaissance. No code was changed.

> ⚠️ **`backend/app/services/sim_session.py` line numbers are approximate.** That file
> carries ~110 lines of uncommitted persona-realism work on branch
> `feat/persona-realism-wave-a-w1` and gained another 16 during this scan. Numbers
> below re-verified 2026-07-26 00:58; navigate by symbol name. Every other cited file
> is unmodified on the branch, so those numbers are stable.

---

## 1. The existing Simulate reveal seam (the thing to mirror)

| Layer | Location | Shape |
| --- | --- | --- |
| Capability gate | `backend/app/services/sim_session.py:157-158` | `REVEAL_ENABLED = True` (module global, not per-session) + `_REVEAL_SCOPES = ("last-in", "all")` |
| Service | `backend/app/services/sim_session.py:1323-1367` | `reveal(db, session_id, scope, owner_id) -> RevealView` |
| Route | `backend/app/api/v1/simulate.py:177-188` | `GET /simulate/{session_id}/reveal/{scope}` |
| Wire schema | `backend/app/schemas/simulate.py:216-241` | `RevealView { available, scope, seats[] }`, `RevealedSeatView { seat_index, hole_cards }` |
| FE types | `frontend/src/api/types.ts:487-502` | hand-maintained mirrors of the above |
| FE client | `frontend/src/api/client.ts:212-217` | `getReveal(sessionId, scope)` |
| FE state | `frontend/src/components/SimulateView.tsx:237-241, 366-370, 637-663` | `revealScope`, `revealedSeats`, `revealedBySeat`, `onReveal`; cleared on new hand |
| FE control | `frontend/src/components/simulate/SimShowdown.tsx:70-88` | `.sim-reveal-actions` group, two `.sim-reveal-btn` with `aria-pressed` |
| FE render | `frontend/src/components/simulate/SimTable.tsx:177-186` | on-demand reveal overrides the face-down pod; a genuine showdown reveal wins over it |

### Behavioural contracts the current endpoint holds

1. **Availability is a 200-body concern.** `available=false` with empty `seats` when
   the capability is off, the scope is unknown, or no completed hand exists.
   `404` is reserved for `SessionNotFound` only.
2. **Hero is never in the payload.** Hero cards already ship on `Hero`.
3. **Scope semantics:** `last-in` = non-hero seats whose end-of-hand `PlayerStatus`
   is `IN` or `ALLIN`; `all` = every non-hero seat dealt into the hand.
4. **Reveal is additive** — it never mutates the wire `showdown`, so the privacy
   invariant on `_view` stays intact.
5. **Docstring drift, already present at HEAD:** `RevealView`'s schema docstring
   (`schemas/simulate.py:227-233`) still says reveal is hero-fold-only. The service
   docstring (`sim_session.py:1335`) records that this was widened to *any*
   completed hand. **The schema docstring is stale** — worth correcting in whichever
   ticket touches that file.

---

## 2. Why the History page cannot do this client-side

**NO-PEEK is server-enforced, not a frontend choice.**

`_build_replay` (`backend/app/services/sim_session.py:1511-1571`) emits
`revealed_seats` on **exactly one** step — the terminal step — and **only** for
`settle(state).showdown_seats`. Every non-terminal step carries `revealed_seats: []`.
The deriver `frontend/src/components/simulate/replaySeats.ts:162-183` faithfully
reproduces that: `reveal` is populated only when `isTerminal`.

So on a fold-out hand, or for a seat that folded before showdown, **no villain card
exists anywhere in the client's memory**. There is nothing to un-hide. A new wire
path is mandatory.

**The data does exist server-side.** Every completed `sim_hand.state_json`
deserialises to a `HandState` whose `seats[i].hole_cards` are all present — this is
exactly what the session-scoped `reveal()` already reads. The gap is purely that
`reveal()` resolves its hand via `_current_hand(db, session)` (the just-completed
hand of a *live* session), and the History page has a `sim_hand_id` instead.

---

## 3. Integration points a spec must cover

### 3.1 Hand resolution already has a helper — reuse it

`_load_owned_complete_hand(db, sim_hand_id, owner_id)`
(`sim_session.py:1470-1480`) is the exact ownership + completeness gate a hand-scoped
reveal needs, and it already raises `SessionNotFound` → 404. It is currently used by
the replay path. A new `reveal_hand(db, sim_hand_id, scope, owner_id)` is close to a
copy of `reveal()` with `_current_hand` swapped for this helper.

`GET /simulate/hand/{sim_hand_id}/reveal/{scope}` sits beside the existing
`/hand/{sim_hand_id}/replay` (`api/v1/simulate.py:125`).

**Correction (both reviewers, 2026-07-26):** this scan originally implied declaration
order matters. It does not. The new route is four segments after `/simulate`
(`hand`/id/`reveal`/scope); the session route at `:177` is three
(session_id/`reveal`/scope). Starlette matches on exact segment count, so they can
never collide at any ordering — empirically confirmed by the refuter with a minimal
FastAPI app. Placement beside `/hand/{id}/replay` is a readability convention only.
What *is* forbidden is a bare `/{id}/reveal/{scope}` — that shape would genuinely be
swallowed.

### 3.2 Type mismatch: `RevealedSeatView` vs `ShowdownSeatView`

This is the sharpest integration wrinkle.

- The session reveal returns `RevealedSeatView` — **no `delta_bb`**.
- The History felt renders from `seat.reveal`, typed `ShowdownSeatView` in
  `replaySeats.ts:37` — and **reads `reveal.delta_bb`** at
  `HandReplayTable.tsx:152-157` (tone class) and `:206-211` (the `.hrt-pod-delta`
  chip).

Reusing `RevealedSeatView` would mean either widening the deriver's type to a union
and null-guarding every `delta_bb` read, or fabricating a delta — the latter is
disallowed (no fabricated numbers).

**Recommended resolution:** have the hand-scoped endpoint return `ShowdownSeatView`
(with a real `delta_bb`) rather than `RevealedSeatView`. This is free:
`_build_replay` already calls `settle(state)`, and `Settlement.deltas` is
**`len 9`, one entry per seat, summing to 0.0** (`domain/table/engine.py:74, 375`) —
so a genuine settlement delta exists for *every* seat, not just showdown
participants. That makes the new payload a drop-in for the existing
`seat.reveal` render path with **zero type churn in `replaySeats.ts` or
`HandReplayTable.tsx`'s pod rendering**.

Caveat for the spec to decide: a hand with `state.hand_over == False` has no
settlement — but `_load_owned_complete_hand` already requires `status == "complete"`,
so this should be unreachable. Worth an explicit assertion or an `available=false`
branch rather than an uncaught `None` deref.

### 3.3 Frontend wiring (the surface owner chose)

| Concern | Where | Note |
| --- | --- | --- |
| Fetch | `HistoryView.tsx` uses its own local `fetchJson` against `/api/v1` (`:18-24`), **not** `api/client.ts` | Either add `getHandReveal()` to the shared client and use it, or follow the local pattern. Pick one; don't do both. |
| State owner | `HistoryView.tsx` holds `replay`; `HandReplayTable` is documented as **presentational, cursor-only** (`:14-17`) | **Correction (both reviewers):** this scan claimed the `key={replay.sim_hand_id}` remount at `HistoryView.tsx:121` makes a per-hand reset "free". It does not — a `key` remounts only that **child**, and it cannot reset state owned by the still-mounted **parent**. Wherever the state lives, the reset must be explicit AND an in-flight response must be identity-checked; unmounting does not cancel a fetch. See the spec's "Stale-response guard" section. |
| Merge with showdown reveals | `deriveSeats` sets `seat.reveal` only at the terminal step | The on-demand set must override/fill at **every** step, not just terminal. `SimTable.tsx:181-186` documents the live precedence rule (genuine showdown wins) — mirror it, don't invent a new one. |
| Control markup | `SimShowdown.tsx:70-88` | Two buttons, `role="group"` + `aria-label="Reveal villain hands"`, `aria-pressed` per scope, `.sim-reveal-btn-on` for the active one. Reuse the classes; the styling already exists. |
| Types | `frontend/src/api/types.ts` is **hand-maintained** (repo invariant) | `schema.d.ts` is unwired. Any new schema must be typed manually. |

### 3.4 Cross-consumer blast radius

- `replaySeats.ts` / `HandReplayTable.tsx` are **shared with nothing else** — the
  Simulate-route quick-replay uses the separate single-column `HandReplay.tsx`
  (`HandReplayTable.tsx:16-17` says so explicitly). Changing the History felt does
  not touch the Simulate felt.
- `HandReplay.tsx` (Simulate quick-replay) has the **same** NO-PEEK limitation and
  the same terminal-only reveal (`:98-106`). It is out of the chosen scope, but a
  spec should state that explicitly so the asymmetry is deliberate, not an oversight.
- Existing test coverage touching reveal: `backend/tests/test_sim_session.py`,
  `backend/tests/test_sim_replay.py`, `frontend/src/components/simulate/replaySeats.test.ts`.
  A new endpoint needs its own cases; `replaySeats.test.ts` will need cases if the
  deriver's reveal contract changes.

---

## 4. Invariants in force

- Domain core `backend/app/domain/` takes no web/DB imports (test-enforced by
  `tests/test_domain_purity.py`). All new code here is service + API layer, so this
  is satisfied by construction — but `settle()` is domain and must stay pure.
- **No schema change to any table** — `state_json` already holds everything, so this
  needs **no Alembic migration**. Confirm that stays true in the spec.
- `spot_signature()` is frozen; untouched by this work.
- FE types hand-maintained in `types.ts`.
- CSS values from design tokens only; AA contrast + visible focus in both themes.
  The reveal buttons reuse existing `.sim-reveal-btn` styling, so this is mostly
  inherited — verify the History page's surface gives the same contrast.
- Reveal must never fabricate a card or a delta.

---

## 5. Open questions for the interview

1. **Gate it?** `REVEAL_ENABLED` is a global capability flag. Does the History
   reveal share it, or get its own? Sharing is simpler and matches "one capability".
2. **Off by default, per hand?** Owner already ruled out a persisted cross-hand
   preference, so: reveal resets when a new hand is opened (free — the component
   remounts on `key`).
3. **Does reveal apply at every step, or only at the last step?** Revealing at step 1
   shows what the villain held from the start — strictly more informative for review,
   and the whole point of a history page. But it removes the "guess the range" value
   of stepping. Recommend: every step, since the user opted in explicitly.
4. **`HandReplay.tsx` (Simulate quick-replay) parity** — leave asymmetric, or follow
   up? Recommend leaving it out of this pass and noting it.
