# Spec — Simulate History Replayer: two-pane felt (UX)

Slug: `sim-history-replayer-twopane`
Scope: **UX/UI only** — layout + CSS + a pure client-side deriver. No behavior change to the
engine, no API/domain/backend, no `api/types.ts` shape change, no new replay fields.
Contracts: `docs/ai-dlc/contracts/sim-history-replayer-twopane-ux.md`.

## 1. Problem

The History-route hand replayer (`HandReplay.tsx` rendered by `HistoryView.tsx`) shows a hand
**one move at a time** as a single-column filmstrip: board strip, one caption, Prev/Next. You
cannot see the whole hand's shape at a glance, and stepping is the only way to read it. Cumbersome.

## 2. Design commitment (owner-approved, Gate 1)

Mockup **#1 "Classic"** (artifact `e4feec80`), rendered in the **live-Simulate visual identity** —
one app identity, History-specific feature.

- **Left = full 9-seat felt, built from the live-Simulate objects verbatim**: `.felt-staged` /
  `.tablering.sim-tablering` / `.table-center` / `.rail`, `.tseat.sim-seat` pods (position chip,
  dealer button, burgundy `.card.back` face-down villains, acting-seat `--sim-live` glow), the
  `Card` component, `sim-badge`/`sim-tier-*` chips. Board + pot centered, hero pod bottom.
  Villains face-down until the terminal showdown step (NO-PEEK, inherent to the payload).
- **Right = moves grouped by street** (Preflop / Flop / Turn / River), a board mini-card cluster on
  each street header, one row per action (`position · verb · amount`), hero rows carry a tier
  chip, the current step highlighted.
- **Controls** = Prev / Next buttons + `←`/`→` keys + **click any move to jump** the felt to it.
  No autoplay.
- **Verdict** = a dedicated "Your decision" panel below the felt + controls, updating on hero
  steps: tier + ≈EV-loss + coverage + the persisted "why" (freq+EV, never boolean; never
  fabricated — reuse the current `HeroVerdict` logic).

**The one thing this view must communicate**: *the whole shape of a past hand at a glance, and,
on any hero decision, what the ruling was and why* — while looking unmistakably like the same
product as the live table.

## 3. Approach

A **new History-scoped component** `frontend/src/components/simulate/HandReplayTable.tsx`, rendered
by `HistoryView.tsx` in place of `HandReplay` **on the History route only**. The shared
`HandReplay.tsx` (used by `SimulateView.tsx` "Replay last hand") is **not touched**.

### Payload semantics that drive the deriver (verified against backend — do not re-guess)

- `HistoryAction.amount_bb` (the field the replay carries, `engine.py:299-304`) is the **per-action
  increment** — chips this seat added on this action — NOT the raise-to total. POST/blinds carry
  their increment; FOLD/CHECK carry 0. Therefore:
  - **raise-to label** must be computed: `raiseToBb = amount_bb + that seat's prior investment on
    the current street`. Rendering `raises to ${amount_bb}` (as today's `HandReplay.actionVerb`
    does) is WRONG for any re-raise / blind-raise. The deriver tracks per-seat per-street
    investment, so it emits a correct label. (`call` shows its increment as-is; `bet` on a fresh
    street has zero prior investment, so bet-to = increment.)
  - **pot** = running sum of `amount_bb` increments to the cursor = **gross committed chips**. Label
    it "committed" (not "final pot"); at terminal it may exceed the settled pot by an uncalled top
    layer settlement returns — fine for a committed-chips readout, and the label keeps it honest.
- `is_terminal` means **terminal showdown**, not "hand complete". An uncontested fold-out has NO
  terminal step (`is_terminal=false` on its last step, `sim_session.py:1461-1465`). So "complete" =
  `cursor === steps.length - 1`, a flag separate from `is_terminal`.

### Pieces

1. **Pure deriver** `frontend/src/components/simulate/replaySeats.ts`: given `(replay, cursor)`,
   fold `steps[0..cursor]` into what the felt + moves list need:
   - per present seat `{ position, seatIndex, isHero, isButton, folded, isActing, lastActionVerb }`,
     where `isButton = seatIndex === replay.button_seat` (authoritative field, not a `position==="BTN"`
     match), and `isActing` = the cursor step's actor **only when not complete** (no glow on the
     final fold-out frame).
   - correct raise-to/bet-to labels via tracked per-seat per-street investment (above).
   - `board` = cursor step's board; `street` = cursor step's action street; `potBb` = summed
     increments; `isComplete = cursor === steps.length - 1`.
   - **reached streets** for the moves list = deepest of acted streets AND the terminal board length
     (mirror `HandReplay.reachedStreets`, `HandReplay.tsx:79-92`) so an all-in auto-runout still
     yields Turn/River groups (with board mini-cards) even though no action step carries them.
   - terminal reveals only when `step.is_terminal`; **no stack_bb** (not on wire — pods show
     position + last action only). Deterministic, unit-tested (see §6). Reuses `RING` + hero-rotation.
2. **Component** `HandReplayTable.tsx`: props unchanged from `HandReplay` (`{ replay, onClose }`) so
   the host swap is one line. Two-pane layout:
   - **Left felt** reusing `slotStyle(i,n)` + the sim felt/pod classes. Its root carries an opt-in
     class `history-replay` that the CSS wires into the **wide shell + ring-height** selectors
     (§3.4) so the felt is sized **identically** to the live table, plus `sim-tablering`/`sim-seat`
     for burgundy backs + center offset. An explicit **acting-pod ring** is added in CSS (the live
     `sim-seat-act` class has NO rule today and the only real glow is hero-only — contract §3), so
     any `isActing` pod gets a real `--sim-live` cue.
   - **Right moves pane**: street-grouped, one focusable row per **visible (non-post)** action;
     empty reached-street groups still render their board mini-cards; current row highlighted.
   - **Controls + keyboard**: Prev/Next + `←/→` step over **visible (non-post) steps only** (posts
     fold into derivation but are never landed on, so a current row always exists and the opening
     frame isn't a blank-highlighted SB/BB post). Initial cursor = first visible step. Click-to-jump
     on rows; Enter/Space activates. The `←/→` handler keeps the input-guard and is scoped so it
     does not hijack keys while a Prev/Next button or move row holds focus (native-button/roving
     semantics — §5).
   - **Verdict**: dedicated panel below, only on `is_hero && !is_post` steps — reuse `HeroVerdict`'s
     tier/≈EV-loss/coverage/why rules verbatim (freq+EV, no fabrication).
3. **CSS** `.hrt-*` in `app.css`: two-pane grid, moves list, street groups, verdict panel, acting-
   pod ring — tokens only, both themes. Felt styled by the existing sim classes, not re-themed.
4. **Shell + responsive** (density fix, owner-approved): generalize the wide-shell + ring-height
   selectors so the replayer opts in via `history-replay` — `.app:has(.simulate), .app:has(.history-replay)`
   for `--content-width-wide`, and the same for the `.tablering` `max-height` ramp
   (`app.css:3254-3268`). Below **~1100px** (the live table's own threshold, NOT 760px) collapse the
   two-pane to **stacked** (felt on top, full moves below) — how `.sim-layout` already collapses
   (`app.css:3241-3244`), avoiding the ~536-700px starved-felt collision this branch fixes.
5. **Host swap** in `HistoryView.tsx`: render `HandReplayTable` instead of `HandReplay`
   (`key={replay.sim_hand_id}`, same props). Nothing else in `HistoryView` changes.

## 4. Files in scope

- **NEW** `frontend/src/components/simulate/replaySeats.ts` + `replaySeats.test.ts` — pure deriver.
- **NEW** `frontend/src/components/simulate/HandReplayTable.tsx` — the two-pane replayer.
- `frontend/src/components/HistoryView.tsx` — swap the rendered component (History route only).
- `frontend/src/styles/app.css` — new `.hrt-*` rules only (single-owner hotspot; sequence tickets
  that touch it).

**Out of scope**: `HandReplay.tsx` (Simulate-route quick-replay — unchanged), `SimulateView.tsx`,
`SimTable.tsx`, `PokerTable.tsx` (Practice/Quiz), any backend file, `api/types.ts`,
`tokens.css` (no new token needed), `simPlayback.test.ts` semantics.

## 5. Constraints (from `docs/ai-dlc/profile.md`)

- CSS values from **design tokens only** — no raw hex/px outside `tokens.css`. Reuse the sim felt
  classes rather than re-declaring felt colors. **Media-query breakpoint literals** (e.g.
  `max-width: 1100px`) are exempt from the no-px grep — they are structural, not design values, and
  the codebase already uses raw px in `@media` (`app.css:3241`, etc.).
- **WCAG 2.2 AA** both themes: visible focus ring on every move row and control; ≥24px targets;
  the verdict panel + tier chips + moves list clear 4.5:1 on their grounds; the dimmed folded /
  ungraded states stay legible.
- **Keyboard**: `←/→` respects the `input, textarea, select, [contenteditable]` guard AND does not
  hijack keys while a Prev/Next button or a move row holds focus (scope the shortcut to the replay
  container / use native-button + roving semantics); move rows are focusable and Enter/Space jumps.
- **Acting-pod glow is NOT reusable as-is** — the live `sim-seat-act` class has no CSS rule and the
  real glow (`.sim-ring-live`) is hero-only via a `.hero-ring` wrapper (contract §3). This pass adds
  ONE explicit acting-pod ring rule (a `--sim-live` box-shadow on the acting `.tseat`) in the
  `.hrt-*` block so any acting seat — hero or villain — gets a real cue. This is the only felt-CSS
  addition; it does not alter the live table.
- **NO-PEEK**: no villain hole card rendered before the terminal step (render only wire data).
- **Freq + EV, never boolean**; EVs labeled **≈ approximate**; no fabricated reasoning. The pot
  readout is labeled **committed** (gross chips in), never presented as the settled final pot.
- `.stage` `overflow:hidden` holds — no pod clipped at any in-scope width.
- **Density (the load-bearing constraint)**: the felt must be sized identically to the live table
  (shared wide-shell + ring-height selectors) and the two-pane must **collapse to stacked below
  ~1100px** — never render a side-by-side felt in the ~536-700px starved-column zone that caused
  the live-table pod/board collision (this branch's raison d'être). Verify at 1024×768: stacked, no
  clip. Do NOT grow the ring geometry.
- FE types unchanged (`api/types.ts` untouched); no backend change.

## 6. Verify-by

Deterministic:
- `cd frontend && npm run typecheck && npm run build` — clean.
- `replaySeats.test.ts` (vitest) — covers: fold status propagates forward; acting seat = cursor
  actor; **acting suppressed on the final fold-out frame** (`is_terminal=false`, `isComplete=true`);
  last-action verb resets per street; **raise-to = increment + prior street investment** (a 3-bet /
  blind-raise renders the correct to-total, not the bare increment); pot = summed increments
  (committed); terminal reveals only at `is_terminal`, absent before; hero rotation seats hero at
  bottom; **all present seats appear (9-position roster)**; an all-in auto-runout yields Turn/River
  **reached-street groups** with board mini-cards even with no action step for those streets;
  `isButton` keys off `button_seat`; **visible-step navigation skips POST steps** (first visible
  step is the first real action, so a current row always exists).
- `./scripts/verify.sh` — backend untouched, stays green.
- Raw-value grep over the `app.css` diff — no hex/px literals introduced.

Browser (`design-reviewer`) at **1440 / 1280 / 1024 / 375**, both themes, on a real History hand:
- **Identity** — the felt, pods, cards, dealer button, and tier chips read as the same objects as
  the live Simulate table (side-by-side spot check).
- **Whole-hand shape** — the right pane shows every move grouped by street with board mini-cards;
  the current move is highlighted and stays in view as you step.
- **Click-to-jump** — clicking any move row moves the felt + verdict to that step; `←/→` and
  Prev/Next step; keyboard focus is visible throughout.
- **Verdict** — lands on a hero step → the dedicated panel shows tier + ≈EV-loss + coverage + why
  (or the literal no-baseline fallback); never on villain/post steps.
- **NO-PEEK** — no villain card appears before the terminal step; at showdown the revealed seats
  flip face-up with their deltas.
- **Density / no clipping** — every pod rect inside `.stage`; the felt matches the live table's
  size (wide shell + ring-height inherited); the two-pane **stacks below ~1100px** (felt above,
  moves below) and at **1024×768 renders stacked with no starved-felt collision or clip**.
- **Auto-runout** — an all-in hand shows Turn/River street groups (board mini-cards) in the moves
  pane, not five cards jammed under Preflop.
- **Fold-out** — an uncontested fold to the blinds ends with no lingering acting-seat glow on the
  final frame.
- Contrast spot-check on tier chips, verdict panel, folded/dimmed rows, both themes.
