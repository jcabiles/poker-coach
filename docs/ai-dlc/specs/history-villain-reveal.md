# Delta spec — History-page villain reveal

**Slug:** `history-villain-reveal` · **Written:** 2026-07-26
**Contract map:** `docs/ai-dlc/contracts/history-villain-reveal.md`
**Roadmap slice of:** `docs/ai-dlc/roadmap/simulate-table.md` — "Hand replayer" (`:1295`),
sibling of "Hand replayer — two-pane redesign" (`:1317`).

## Goal (one line)

On the History page's stepped replayer, let the hero reveal villain hole cards on
demand with `last-in` / `all` scopes, mirroring the Simulate page's R1 reveal.

## Why this needs a server change

NO-PEEK is **server-enforced**. `_build_replay`
(`backend/app/services/sim_session.py:1511`) emits `revealed_seats` on exactly
one step — the terminal one — and only for `settle().showdown_seats`. Every other
step ships `[]`, and the deriver `frontend/src/components/simulate/replaySeats.ts:162-183`
reproduces that faithfully. On a fold-out hand no villain card exists anywhere in
client memory, so there is nothing a frontend-only change could un-hide.

The data does exist server-side: every completed `sim_hand.state_json` deserialises
to a `HandState` whose `seats[i].hole_cards` are all populated. The existing
session-scoped `reveal()` (`:1323`) already reads exactly this. The only gap is
that it resolves its hand via `_current_hand(db, session)` — the just-completed hand
of a *live* session — while History holds a `sim_hand_id`.

> ⚠️ **Line numbers in this spec are approximate — navigate by symbol name.**
> `backend/app/services/sim_session.py` carries ~110 lines of uncommitted
> persona-realism work on branch `feat/persona-realism-wave-a-w1`, and it gained
> another 16 lines *during* this inception. Numbers below were re-verified at
> 2026-07-26 00:58 but will drift again. `grep -n "^def <name>"` before editing.

## Owner decisions (Gate 1, confirmed 2026-07-26)

| # | Decision |
|---|---|
| 1 | **New hand-scoped endpoint.** `GET /simulate/hand/{sim_hand_id}/reveal/{scope}`. `/hand/{id}/replay` stays **byte-identical** so its NO-PEEK verification remains valid. |
| 2 | **Payload = `ShowdownSeatView`** (cards **+** real settlement `delta_bb`), not `RevealedSeatView`. |
| 3 | **Revealed cards are face-up at EVERY step**, not only the terminal one. |
| 4 | **Clicking the active scope un-reveals**; clicking the other scope swaps. (Divergence from Simulate, which is one-way — accepted deliberately.) |
| 5 | **Surface = the replayer's controls row**, two buttons reusing `.sim-reveal-btn`. Not the history list rows. |
| 6 | Dual adversarial review: Claude `refuter` + Codex Sol `gpt-5.6-sol`. |
| 7 | Shares the existing global `REVEAL_ENABLED` capability gate (roadmap `:1372` wants one withholdable reveal capability for a future hidden-persona mode). |
| 8 | Off by default; **explicitly cleared** on hand open and on close. ⚠️ The `key={replay.sim_hand_id}` remount at `HistoryView.tsx:121` remounts only the *child* — it does **not** reset parent-owned state. See "Stale-response guard" below; the first draft's "resets for free" claim was wrong (Codex Sol, HIGH). |
| 9 | `HistoryView` owns fetch + state; `HandReplayTable` gains **optional** props so the clean `HandReplay` host-swap property (roadmap `:1336`) survives. |
| 10 | `getHandReveal()` goes in `frontend/src/api/client.ts` beside the existing `getReveal`. |
| 11 | `available: false` renders an honest muted line, **not** a silent no-op. |

## Out of scope

- `frontend/src/components/simulate/HandReplay.tsx` — the Simulate-route single-column
  quick-replay. It has the same terminal-only limitation and **stays asymmetric**;
  this is deliberate, not an oversight.
- Reveal controls on the history **list** rows.
- Any persisted cross-hand reveal preference (localStorage).
- The `day_ordinal` vs `hand_no` label follow-up at roadmap `:1325`.
- Any change to the Simulate page's one-way reveal behavior.
- Refactoring `HistoryView`'s existing local `fetchJson` calls onto the shared client.

## Files to touch

### Backend
| File | Change |
|---|---|
| `backend/app/schemas/simulate.py` | New `HandRevealView { available: bool, scope: str, seats: list[ShowdownSeatView] }`. **Also fix the stale `RevealView` docstring** (`:227-233` still says hero-fold-only; the service docstring at `sim_session.py:1335` records the widening to any completed hand). This file is **unmodified** on the branch, so its line numbers are trustworthy. |
| `backend/app/services/sim_session.py` | New `reveal_hand(db, sim_hand_id, scope, owner_id) -> HandRevealView`. Reuses `_load_owned_complete_hand` (`:1470`) for the owner + completeness gate, `REVEAL_ENABLED` / `_REVEAL_SCOPES` (`:157-158`), `HERO_SEAT` (`:119`), and the already-imported `settle` / `Settlement` (`:59`, `:62`). |
| `backend/app/api/v1/simulate.py` | New route + a line in the module docstring's route table. |

### Frontend
| File | Change |
|---|---|
| `frontend/src/api/types.ts` | Hand-maintained mirror of `HandRevealView`. (`schema.d.ts` is unwired — repo invariant.) |
| `frontend/src/api/client.ts` | `getHandReveal(simHandId, scope)`. |
| `frontend/src/components/HistoryView.tsx` | Owns `revealScope` + `revealedBySeat` state, the fetch, toggle-off logic, and the `available:false` message. Clears on hand open/close. |
| `frontend/src/components/simulate/HandReplayTable.tsx` | New **optional** props (`revealScope`, `revealedBySeat`, `onReveal`, `revealUnavailable`); renders the two buttons; merges the on-demand reveal into the pod render. |
| `frontend/src/components/simulate/replaySeats.ts` | Only if the merge is done in the deriver rather than the component — see "Merge precedence" below. |
| `frontend/src/styles/app.css` | **HOTSPOT — single owner.** Layout for the reveal group inside `.hrt-controls`. |

## Behavioural contracts to preserve

1. **Availability is a 200-body concern.** `available: false` with empty `seats` when
   the capability is off or the scope is unknown. `404` stays reserved for
   `SessionNotFound` (missing / not-owned / not-complete hand) — `_load_owned_complete_hand`
   already raises exactly this.
2. **Hero is never in the payload.** Exclude `HERO_SEAT` (= `0`), same as `reveal()`.
   Hero cards already ship on `HandReplayView.hero_cards`.
3. **Scope semantics are identical to the session endpoint.** `last-in` = non-hero
   seats whose end-of-hand `PlayerStatus` is `IN` or `ALLIN`; `all` = every non-hero
   seat dealt into the hand.
4. **Reveal is additive.** It must not mutate `HandReplayView`, `settle()`, or the
   `showdown` wire shape. `/hand/{id}/replay` output must be byte-identical before
   and after this change.
5. **No fabricated cards or deltas.** Every `delta_bb` must come from
   `Settlement.deltas`, which is `len 9`, one real entry per seat, summing to 0.0
   (`backend/app/domain/table/engine.py:74, 375`).

## Route shape

Register the new route as `/hand/{sim_hand_id}/reveal/{scope}` beside the existing
`/hand/{sim_hand_id}/replay` (`api/v1/simulate.py:125`) — for organisation, not
because ordering forces it.

**Corrected by Codex Sol review (was overstated in the first draft).** The `/hand`
prefix makes collision impossible: the new route has four path segments after
`/simulate` (`hand` / id / `reveal` / scope) while the session route at `:177` has
three (session_id / `reveal` / scope). They cannot match the same request at any
declaration order. What *is* forbidden is a **bare `/{id}/reveal/{scope}`** — that
form would genuinely be swallowed by `/{session_id}/reveal/{scope}`. Do not use it.

## Settlement edge case

`_load_owned_complete_hand` requires `status == "complete"`, so `state.hand_over`
should always be true and `settle(state)` always returns. Do **not** rely on that
implicitly: if `state.hand_over` is false, return `available: false` rather than
dereferencing `None`. An explicit branch, not an assertion.

## Stale-response guard (HIGH — Codex Sol review)

**This is the sharpest correctness requirement in the spec. It is a NO-PEEK
violation if skipped.**

Reveal state lives in `HistoryView`, which stays mounted across hand changes. Its
existing hand fetch (`HistoryView.tsx:89-101`) has no abort, no request generation,
and no identity check. A reveal fetch written the same way admits this sequence:

1. Request reveal for hand **A**.
2. Close A, open hand **B**.
3. A's response resolves *after* the state was cleared.
4. A's cards populate the map and render on **B**, matched by seat index.

Hand A's hole cards and deltas would appear on hand B — leaked *and* fabricated.
The same race lets a stale response silently undo a toggle-off, or let a slow
`last-in` response overwrite a newer `all`.

**Required:** an `AbortController` or a monotonically increasing request token. A
response is applied **only** if its captured `sim_hand_id`, requested `scope`, and
request generation all still match current state. Requests are invalidated/aborted
on toggle-off, scope change, hand close, and hand open.

Note this is not fixed by moving state into `HandReplayTable` — unmounting does not
cancel an in-flight fetch. The guard is required wherever the state lives.

### The guard must be a PURE MODULE (testability constraint)

`frontend/package.json` ships **vitest only** — there is no React Testing Library and
no jsdom, so a React component's async behavior **cannot** be tested here. Adding a
test dep is not an option: npm installs are blocked in this sandbox and would require
the owner to install manually.

Therefore the reveal request/apply logic must live in a **pure, dependency-free
module** — `frontend/src/components/simulate/revealRequest.ts` — following the exact
precedent of the pure deriver `replaySeats.ts` + its `replaySeats.test.ts`. Shape it
as a reducer over an explicit state, e.g.:

```
type RevealState = { scope: "last-in" | "all" | null; gen: number;
                     handId: number; bySeat: Map<number, ShowdownSeatView> }
requestReveal(state, scope, handId)   -> { state, shouldFetch, gen }
applyRevealResponse(state, resp, meta) -> state   // meta = { handId, scope, gen }
```

`applyRevealResponse` returns the state **unchanged** whenever
`meta.handId !== state.handId`, `meta.scope !== state.scope`, or
`meta.gen !== state.gen`. `HistoryView` then holds this state and does nothing but
fetch and dispatch — all three race cases become plain synchronous unit tests with no
DOM, no timers, and no new dependency.

## Merge precedence (frontend)

Mirror the rule the live felt already documents at
`frontend/src/components/simulate/SimTable.tsx:181-186`: **a genuine showdown reveal
wins over an on-demand reveal.** Do not invent a new precedence.

Two additional requirements specific to this surface:
- The merge must apply at **every** step, not only the terminal one. The deriver
  currently populates `seat.reveal` only when `isTerminal` (`replaySeats.ts:162-164`).
- A `scope: "all"` reveal includes seats that folded early. The current pod render
  hides cards entirely for folded seats (`HandReplayTable.tsx:189`, the
  `!seat.folded &&` guard) — a revealed card must **override** that guard, exactly as
  `SimTable.tsx:181-186` notes for the live felt.

## Constraints (from `docs/ai-dlc/profile.md`)

- Domain core `backend/app/domain/` takes **no** web/DB imports (test-enforced by
  `tests/test_domain_purity.py`). All new code is service + API layer; `settle()` is
  domain and must stay pure — call it, don't change it.
- **No Alembic migration.** `state_json` already holds every hole card, so no schema
  change. If a ticket finds itself wanting one, stop and re-spec.
- FE API types are **hand-maintained** in `frontend/src/api/types.ts`.
- CSS values from design tokens only — no raw hex/px outside `tokens.css`.
- WCAG AA contrast + visible focus in **both** themes. `.sim-reveal-btn` already
  lifts its resting border to `--muted` for 1.4.11 3:1 (a prior design-review fix) and
  already styles `[aria-pressed="true"]` (`app.css:3215-3231`) — so the toggle-off
  pressed state is styled for free. **But** `.sim-reveal-btn` carries `flex: 1 1 0`,
  which will fight the `.hrt-controls` Prev/count/Next layout (`app.css:5417`). Solve
  with layout in the History scope; do not edit the shared `.sim-reveal-btn` rule.
- Results are frequency + EV, never boolean; EVs labeled approximate. (Not touched
  here — no grading changes.)
- `spot_signature()` frozen. Untouched.

## Verify-by (end-to-end)

Deterministic gates — all must pass:
1. `./scripts/verify.sh` → `BACKEND VERIFY OK` (pytest + boot probe).
2. `cd backend && ruff check .`
3. `cd frontend && npm run typecheck && npm run build`

Feature-level acceptance, executed against a booted stack (`./scripts/serve.sh start`):
4. **Byte-identical replay.** A regression test asserts `GET /simulate/hand/{id}/replay`
   returns an unchanged payload for a fixture hand — specifically that
   `revealed_seats` is `[]` on every non-terminal step and unchanged on the terminal step.
5. **Fold-out hand, `last-in`.** Open a hand the hero folded and that ended without a
   showdown; click `Reveal last-in` → only the seats still `IN`/`ALLIN` at hand end show
   cards; hero is not duplicated; every revealed seat shows a delta consistent with
   `Settlement.deltas`.
6. **`all` includes early folders.** Click `Reveal all` on the same hand → seats that
   folded preflop also show cards, overriding the folded-pod guard.
7. **Every step.** With reveal on, step to index 0 → villain cards are already face-up.
8. **Toggle-off.** Click the active scope again → cards return face-down;
   `aria-pressed` flips to `false`.
9. **Per-hand reset.** Back out, open a different hand → reveal is off.
10. **Privacy.** With reveal **not** clicked, no villain hole card appears anywhere in
    the DOM or in any network response for a non-showdown seat. This is the invariant
    the original replayer's refuter verified over 120 hands / 2595 steps — it must
    still hold.
11. **404 vs 200.** A non-existent / not-complete `sim_hand_id` → `404`. A valid hand
    with `REVEAL_ENABLED = False` → `200` with `available: false`, and the UI shows the
    muted unavailable line rather than failing silently.
12. **Design review** (`design-reviewer`, both themes, 1440 / 1024 / 375) on the
    replayer with reveal on and off.

Race-condition acceptance (from the stale-response guard — all three must pass):

13. **Reveal → immediate toggle-off before the response lands.** Cards stay
    face-down; `aria-pressed` stays `false`.
14. **`last-in` → `all` with responses arriving in reverse order.** The felt shows
    `all`, never the late `last-in`.
15. **Reveal hand A → close A and open hand B before A resolves.** Hand B shows
    **zero** villain cards. This is the leak case; it must be an explicit test, not
    a manual click-through.

## Claims independently verified during review (Codex Sol)

Recorded so ticket implementers don't re-derive them:

- `Settlement.deltas` is nine index-aligned entries (`domain/table/engine.py:375`),
  correct across fold-outs, walks, side pots, split pots, and all-in runouts. So
  decision #2's "truthful delta for every seat" holds on every hand-end path.
- All nine seats are always dealt in — there is **no** sit-out or undealt status. So
  `all` means exactly the eight non-hero seats, and `last-in` is reliably derivable
  from the persisted `IN`/`ALLIN` statuses.
- Checked against the live DB: 115 completed hands, every one with nine populated
  seats, `hand_over = true`, and nine zero-sum deltas.
- `_load_owned_complete_hand` checks ownership but **not** whether the session is
  still active, so hands from an ended session remain reachable. Correct for History.
- No Alembic migration needed — this adds a response schema and a route only.
