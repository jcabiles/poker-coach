# Tickets — Simulate History Replayer: two-pane felt (UX)

Slug: `sim-history-replayer-twopane`
Spec: `docs/ai-dlc/specs/sim-history-replayer-twopane-ux.md`
Contracts: `docs/ai-dlc/contracts/sim-history-replayer-twopane-ux.md`

DAG: HRT-1 → HRT-2 → (HRT-3 ‖ HRT-4) → HRT-5.
`app.css` is single-owner (HRT-3 only). `HandReplayTable.tsx` is single-owner (HRT-2 only).

---

## HRT-1 — Pure seat-state deriver (`replaySeats.ts` + test)

**Files (new, sole owner):** `frontend/src/components/simulate/replaySeats.ts`,
`frontend/src/components/simulate/replaySeats.test.ts`.

**Payload semantics (verified — do NOT re-guess):** `HistoryAction.amount_bb` (`engine.py:299-304`)
is the **per-action increment**, NOT the raise-to total. `is_terminal` = terminal **showdown**, not
"hand complete" (an uncontested fold-out has no terminal step — `sim_session.py:1461-1465`).

**Do:** a pure function `deriveReplaySeats(replay: HandReplayView, cursor: number)` returning
`{ seats: ReplaySeat[]; board: string[]; potBb: number; street: string; isTerminal: boolean;
isComplete: boolean; reachedStreets: string[] }` where
`ReplaySeat = { position, seatIndex, isHero, isButton, folded, isActing, lastActionVerb: string | null, reveal?: ShowdownSeatView }`.
- Build the present-seat set from `hero_position` + the union of `steps[].position`; place via the
  shared `RING` order + hero-rotation idiom (hero at bottom).
- Fold `steps[0..cursor]`, tracking **per-seat per-street investment**: mark a seat `folded` once it
  has a `fold`; set `lastActionVerb` from its most recent action **on the cursor step's street** —
  and for BET/RAISE render **raise-to = `amount_bb` + that seat's prior street investment** (a
  `call` shows its increment; do NOT reuse `HandReplay.actionVerb` unchanged, which mislabels the
  bare increment as the to-total).
- `isButton = seatIndex === replay.button_seat` (authoritative field, not `position==="BTN"`).
- `isComplete = cursor === steps.length - 1`; `isActing` = cursor step's actor **only when not
  complete** (no glow on the final fold-out frame).
- `potBb` = sum of `amount_bb` increments to the cursor (**committed** chips).
- `board` = cursor step's board; `street` = cursor step's action street.
- `reachedStreets` = deepest of acted streets AND the terminal board length (mirror
  `HandReplay.reachedStreets`, `HandReplay.tsx:79-92`) so an all-in auto-runout yields Turn/River.
- Reveals: attach `reveal` per seat **only** when `step.is_terminal`. Never expose a villain card
  otherwise. **No `stack_bb`** — not derivable / out of scope.

**Acceptance / done-condition:** `npm run typecheck` clean; `replaySeats.test.ts` passes covering —
(a) fold propagates forward; (b) acting = cursor actor; (c) **acting suppressed on the final
fold-out frame**; (d) last-action verb resets across a street boundary; (e) **raise-to = increment
+ prior street investment** (3-bet / blind-raise); (f) pot = summed increments; (g) reveals only at
terminal, absent before; (h) hero at bottom after rotation; (i) **9-position roster present**;
(j) all-in auto-runout produces Turn/River in `reachedStreets` with the full board; (k) `isButton`
via `button_seat`.

---

## HRT-2 — Two-pane replayer component (`HandReplayTable.tsx`)

**Files (new, sole owner):** `frontend/src/components/simulate/HandReplayTable.tsx`.
**Depends:** HRT-1.

**Do:** props `{ replay: HandReplayView; onClose: () => void }` (same as `HandReplay`, so the host
swap is trivial). Owns `cursor`, consuming HRT-1's deriver. Root element carries `history-replay`
(opt-in for the wide-shell + ring-height selectors, HRT-3). Layout:
- **Left felt**: reuse `slotStyle(i, n)` geometry (copy a variant — consistent with existing
  SimTable/PokerTable duplication) and render with the **existing sim classes**
  (`stage`/`felt-staged`/`tablering sim-tablering`/`table-center`/`rail`), one `tseat sim-seat` pod
  per derived seat (position chip, dealer button on `isButton`, the **new** acting-pod ring on
  `isActing` — HRT-3, since `sim-seat-act` has no rule today, `Card faceDown` villains → burgundy
  backs, hero cards face-up, last-action chip with the corrected raise-to label). Board + committed-
  pot centered; terminal step flips revealed seats face-up with deltas.
- **Right moves pane**: render one group per `reachedStreets` entry (empty Turn/River groups still
  show their board mini-cards on an all-in runout); one focusable row per **visible (non-post)**
  action (`position · verb · amount`), hero rows carry a `sim-tier-*` chip; the row matching the
  cursor's visible step is highlighted; clicking a row jumps. Rows are focusable; Enter/Space jumps.
- **Controls + keyboard**: Prev / Next + a step counter; `←/→` mirror them. Navigation steps over
  **visible (non-post) steps only** — posts fold into derivation but are never landed on, so the
  opening frame is the first real action (a current row always exists). Keep the input-guard AND
  scope the shortcut so it doesn't hijack keys while a button / move row holds focus.
- **Verdict**: a dedicated "Your decision" panel below, only on `is_hero && !is_post` steps — reuse
  the exact tier/≈EV-loss/coverage/why rules from `HandReplay`'s `HeroVerdict` (freq+EV, never
  boolean, no fabrication, literal no-baseline fallback).
- Header: `← Back` → `onClose`, hand no., hero position, hero cards.

**Acceptance / done-condition:** `npm run typecheck && npm run build` clean. Rendering a hand: felt
uses the sim objects; moves grouped by street (incl. auto-runout Turn/River groups) with the current
row highlighted from the first frame (no blank-highlighted post); click-to-jump + Prev/Next + `←/→`
move felt + verdict over visible steps; raise-to labels correct on a 3-bet; villains face-down until
terminal; no lingering acting glow on a fold-out's last frame; verdict only on hero steps. (Visual
identity + density + a11y verified in HRT-5.)

---

## HRT-3 — `.hrt-*` styles (`app.css`)

**Files (sole owner):** `frontend/src/styles/app.css` (new `.hrt-*` block only).
**Depends:** HRT-2 markup.

**Do:**
- **Shell + ring size (density fix):** generalize the wide-shell + ring-height selectors to include
  the replayer — `.app:has(.simulate), .app:has(.history-replay) { max-width: --content-width-wide }`
  and the matching `.tablering` `max-height` ramp (`app.css:3254-3268`) — so the felt is sized
  **identically** to the live table.
- **Two-pane grid** (felt left, moves right) that **collapses to stacked below ~1100px** (felt
  above, full moves below) — matching `.sim-layout`'s own collapse (`app.css:3241-3244`), NOT 760px.
- **Acting-pod ring:** ONE new rule giving the acting `.tseat` a `--sim-live` box-shadow (the live
  `sim-seat-act` class has no rule today; the only existing glow is hero-only). Any acting seat —
  hero or villain — gets a real cue.
- **Moves list:** street headers with gilt rule + board mini-cards, focusable move rows, current-row
  highlight via `--sim-live`/brass, hero-row tier-chip spacing, dimmed folded rows; verdict panel;
  controls bar.
- Reuse the sim felt classes for the felt itself — **do not** re-declare felt colors. **Tokens only,
  no raw hex/px** (sub-token px for gap/padding/letter-spacing is precedented; **`@media`
  breakpoint px are exempt** — structural, already used at `app.css:3241`). Both themes.

**Acceptance / done-condition:** raw-value grep over the diff finds no new hex/px literals outside
`@media` conditions; the felt matches the live table's size; the two-pane **stacks below ~1100px**
and at 1024×768 renders stacked with no `.stage` clipping or starved-felt collision; both themes
render.

---

## HRT-4 — Host swap (`HistoryView.tsx`)

**Files (sole owner):** `frontend/src/components/HistoryView.tsx`.
**Depends:** HRT-2.

**Do:** render `HandReplayTable` instead of `HandReplay` in the replay branch
(`:118-124`), same `key={replay.sim_hand_id}` + `{ replay, onClose }` props. Update the import.
**Nothing else changes** — list/fetch/mistakes-filter/error paths untouched.

**Acceptance / done-condition:** `npm run typecheck && npm run build` clean; opening a hand from the
History list shows the new two-pane replayer; `← Back` returns to the list; the Simulate-route
"Replay last hand" (`SimulateView.tsx`) still shows the OLD filmstrip (unchanged).

---

## HRT-5 — Verify + design-review gate

**Depends:** HRT-2, HRT-3, HRT-4.

**Do:** run the deterministic gates and the browser review.
- `cd frontend && npm run typecheck && npm run build`; `./scripts/verify.sh` (backend green).
- `design-reviewer` on the History replayer at **1440 / 1280 / 1024 / 375**, both themes, per the
  spec §6 checklist: identity match vs live table, whole-hand shape, click-to-jump, verdict on hero
  steps, NO-PEEK, zero clipping, density gate at 1024×768, contrast on chips/verdict/dimmed rows,
  visible focus on rows + controls.

**Acceptance / done-condition:** all deterministic gates green; `design-reviewer` verdict = pass
(≤3 design→review iterations per the loop); final screenshots captured for the completion report.
