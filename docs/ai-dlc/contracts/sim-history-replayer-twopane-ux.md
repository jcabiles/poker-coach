# Contract map — Simulate History Replayer, two-pane felt (UX)

Slug: `sim-history-replayer-twopane`
Scope: **UX/UI only** — a new History-route two-pane replayer that reuses live-Simulate
objects. No backend/API/domain/schema/type changes.
Source: read-only survey by `contract-mapper`, 2026-07-25, branch `fix/sim-felt-pod-collision`.

## 1. Current replayer — `frontend/src/components/simulate/HandReplay.tsx`

- Presentational only: props `{ replay: HandReplayView; onClose: () => void }`
  (`HandReplay.tsx:53-60`). No fetching, no live pacing.
- Step cursor: `useState(0)` (`:62`); reset effect keyed on `replay.sim_hand_id` (`:66-68`).
- `←/→` handler on `window` (`:113-131`): ignores non-arrow / modifier keys (`:115`) and keys
  targeting `input, textarea, select, [contenteditable="true"]` (`:119-123`); clamps to
  `[0, total-1]`. **A new right-hand moves list must respect the same input-guard or fight it.**
- **NO-PEEK**: `revealedBySeat` built only when `step.is_terminal` from `step.revealed_seats`
  (`:100-106`). `ReplayStepView.revealed_seats` is `[]` on every non-terminal step by server
  contract (`api/types.ts:389-391,406`) — villain cards are structurally absent from the wire
  until terminal. Preserved automatically as long as we render only what's on the wire.
- `reachedStreets` (`:79-92`): deepest street from acted steps AND the terminal board length
  (auto-runout widens the rail even with no river action step).
- `HeroVerdict` gating: `step.is_hero && !step.is_post` (`:245`). Never fabricates — shows
  `reasoning` if present else a literal tier/EV-only fallback (`:298-306`).
- `hr-*` classes are its own; reuses shared `sim-badge`, `sim-badge-inline`, `sim-badge-word`,
  `sim-tier-<tone>` + `tierOf/fmtEvLoss/streetLabel` from `simGrade.ts`.

## 2. Host wiring — TWO consumers

- `HistoryView.tsx`: `openHand(id)` → `GET /api/v1/simulate/hand/${id}/replay` → `setReplay`
  (`:89-101`); `<HandReplay key={replay.sim_hand_id} … onClose={closeReplay} />` (`:121`);
  `closeReplay` nulls replay → back to list (`:103-106`). Rendered inside `<section className="history">`.
- `SimulateView.tsx:818`: **second, independent** "Replay last hand" mount, inside
  `<section className="simulate">` — fetches `GET /api/v1/simulate/replay?...`. Inherits the
  `.app:has(.simulate)` wide-shell (`app.css:3254-3256`) and `.simulate .tablering` height
  override (`app.css:3261-3268`); **History does not** (no `.simulate` ancestor).
- Only these two files import `HandReplay`. **Decision (owner): redesign History route only.**
  The shared `HandReplay` stays as-is for the Simulate-route quick-replay.

## 3. Felt/seat geometry to reuse — `SimTable.tsx` / `PokerTable.tsx`

- `slotStyle(i, n)` exists in two deliberately-diverged copies: `PokerTable.tsx:47-52` (plain
  ellipse, `43×38` radii) and `SimTable.tsx:41-48` (asymmetric top/bottom `41/38` +
  `FLANK_BIAS_X=30` anchor switch for the four extreme-flank slots — the recent collision fix,
  commits `e2b2f64`/`47cefb6`). Both compute placement purely from `(i, n)`.
- Hero-rotation idiom (`SimTable.tsx:132-138`): `RING = [UTG,UTG1,UTG2,LJ,HJ,CO,BTN,SB,BB]`,
  filter to present positions, `heroIdx = ring.indexOf(hero.position)`, rotate so hero sits at
  bottom. **Needs each seat's `position` string + hero position — both derivable from the replay
  payload** (`hero_position` + the union of `steps[].position`); a full always-9 `SeatView[]`
  roster is NOT on the replay wire.
- Reusable base CSS (shared by both felts): `.stage` (`app.css:202-219`, `overflow:hidden`),
  `.felt-staged` (`:225-235`), `.felt` (`:243-259`), `.tablering` (`:271-277`), `.rail`
  (`:280-294`), `.table-center` (`:296-305`), `.tseat` (`:316-324`), `.tseat-cards .card`
  (`:353-361`), `.card.back` base (`:364-371`).
- **Sim-look enhancements are class-gated** and won't apply outside the Simulate route unless the
  new markup carries the classes: `.sim-seat .card.back` burgundy (`app.css:376-387`),
  `.sim-tablering .table-center` offset (`:311-313`), `.tseat.sim-seat` (`:2871`). The new felt
  MUST add `sim-seat`/`sim-tablering` to inherit the live look (owner directive: unified identity).
- **CORRECTION (refuter R2):** the acting-seat glow is NOT a reusable object. `sim-seat-act`
  (applied by `SimTable.tsx:216,255` to any acting seat) has **no CSS rule anywhere** in `app.css`;
  the only real glow is `.sim-ring-live` (`app.css:2922-2924`), applied **hero-only** via the
  `.hero-ring` wrapper (`SimTable.tsx:223`). So a non-hero acting pod has no reusable cue — the
  replayer must add ONE explicit acting-pod ring rule (in the `.hrt-*` block) to cue any acting seat.
- **CORRECTION (refuter R1 + Codex #1/#5):** the wide shell (`--content-width-wide`,
  `.app:has(.simulate)` `app.css:3254-3256`) and the ring-height ramp (`.simulate .tablering`
  `:3261-3268`) are **ancestor-gated on `.simulate`** and do NOT apply in `.history`. Reusing
  `sim-*` classes alone yields the shallow base ring in a starved column. The new felt must OPT IN
  to those sizing selectors (generalize to `.app:has(.history-replay)`) AND stack below ~1100px.
- **CORRECTION (Codex #2 / refuter R5):** `HistoryAction.amount_bb` (the replay field,
  `engine.py:299-304`) is the **per-action increment**, not the raise-to total — `HandReplay`'s
  `actionVerb` mislabels re-raises. `isButton` must key off `HandReplayView.button_seat` (`:419`).

## 4. Card — `frontend/src/components/Card.tsx`

- Union prop: face-up `{card}` → `<span class="card [red]"><span class="r"/><span class="s"/></span>`;
  face-down `{faceDown:true}` → `<span class="card back" aria-hidden>`. `T`→"10"; red = h/d.
- No size prop — sizing via CSS context overrides. Reusable as-is.

## 5. Tokens — `frontend/src/styles/tokens.css`

- All needed primitives exist: felt/felt-text/felt-chip-bg/stage-bg; primary/primary-text/
  gold-bright/gold-glow; card-bg/card-w/card-h; suit-red/suit-black; `sim-tier-*`, `sim-net-*`,
  `sim-live`; radius + space ramps. **No missing token.** The only gap is CSS-class *scoping*
  (§3), not a token gap.

## 6. Invariants at risk

- `.stage` `overflow:hidden` (`app.css:218`) — no pod may clip. Lighter replay pods (position +
  cards + last-action only, no persona plate / range button / stack row) reduce flank pressure,
  but a design-reviewer clip check is still required.
- **1024×768 density gate** (`app.css:210-213,265-270,3264-3268`): History is NOT the wide shell;
  a felt-beside-moves two-pane must be verified to fit at 1024 wide / 768 tall.
- `PokerTable.tsx` untouched (Practice/Quiz).
- FE types hand-maintained (`api/types.ts`) — this pass changes no shape.

## Reusable as-is / Needs new / Blocked-by-data

| Item | Status | Note |
|---|---|---|
| `Card` markup, `.stage/.felt/.tablering/.table-center/.tseat/.card` CSS | reuse as-is | shared base |
| `RING` + hero-rotation, `slotStyle(i,n)` | reuse (copy a variant) | third copy is consistent with existing SimTable/PokerTable duplication |
| `.sim-seat .card.back`, `.sim-tablering` offset, `.tseat.sim-seat` | reuse via **new scoping class** | new felt must carry `sim-seat`/`sim-tablering` |
| `tierOf/fmtEvLoss/streetLabel/fmtBb`, `sim-badge`/`sim-tier-*` | reuse as-is | shared grade vocabulary |
| tokens | reuse as-is | none missing |
| per-step seat state (folded/acting/last-action/board/pot) | **needs new** derivation | derive client-side from `steps[0..cursor]` — pure TS |
| live per-seat stack_bb | **blocked-by-data** | not on wire; out of scope (pods show position + last action, no stack) |
| `←/→` handler | reuse pattern | new moves list must honor the same input-guard |
