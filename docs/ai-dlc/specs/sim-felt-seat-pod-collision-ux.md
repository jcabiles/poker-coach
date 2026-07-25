# Spec — Simulate felt: villain action labels lost to seat-pod collisions (UX)

Slug: `sim-felt-seat-pod-collision-ux`
Scope: **UX/UI only** — layout + CSS. No behavior, no API, no domain, no backend.

## 1. Reported symptom

> "Simulator fails to label the decisions of the villain in certain positions. For example,
> top right and farthest left seat does not show certain actions… I just saw it with top left now too."

## 2. Diagnosis (reproduced in-browser, 2026-07-25)

Backend is **correct**. `_last_action()` (`backend/app/services/sim_session.py:326`) returns the right
verb for every seat, and `SimTable.tsx` renders `.sim-last-action` for every seat that has one. The
failure is purely **visual occlusion**.

Cause chain:

1. `.tseat` pods are `position:absolute` on the ellipse, `transform: translate(-50%,-50%)`, laid out
   as a **flex column**.
2. `.sim-last-action` has `order: -2` — it is the pod's **topmost** row.
3. A live villain pod is **127–140px tall** (chips 14 + cards 32 + pos 18 + persona 17 + stack 18 +
   range 24 + gaps 16–20).
4. On the **left/right flanks** the ellipse compresses vertically. Measured anchor `cy` at 1440px:
   41 · 106 · 204 · 284 · 317 (mirrored left/right). The two flank pairs that are ALSO close enough
   in `x` to collide sit **98px apart**.
   *(Correction: an earlier read of this spec cited 65px. That is the gap between the ring's index-3
   and index-4 anchors — but those two seats are ~196px apart horizontally and never overlap. The
   binding budget is **98px**, which is why plain de-crowding suffices and no horizontal-orientation
   rewrite is needed.)*
5. 127px of pod in a 98px slot ⇒ each flank pod's **top row (the action label) lands inside the pod
   above it**, on that seat's persona / stack / `RANGE` rows. Neither has a background and neither
   lifts a z-index, so the two texts jumble and the verb reads as absent.

Measured evidence (identical at 1024 / 1280 / 1440 — not a breakpoint bug):

| check | result |
|---|---|
| `.tseat` rect overlaps, preflop all-live | `LJ×HJ` 37×29px · `SB×BB` 10×43px |
| `document.elementFromPoint()` at HJ's "Raise" label centre | returns **CO's pod**, not the label |
| flank anchor spacing (tightest) | **65px** vs 127px pod height |

Affected seats = the two flank columns, i.e. exactly the reported ones: left column (CO / HJ / LJ)
and right column (SB / BB / UTG).

## 3. Design commitment

**Aesthetic**: unchanged — the existing felt-under-a-lamp room (gilt rail, art-deco brass, felt-chip
pucks). This is a **repair inside the committed aesthetic**, not a restyle. No new visual language.

**The one thing each seat pod must communicate**: *who is in this seat, how deep they are, and what
they just did* — the action verb is a first-class element and must never be occluded.

**Direction chosen by the owner**: *de-crowd + scrim pill*.

- **De-crowd** the pod so flank neighbours physically stop colliding.
- **Scrim pill** on the action label so it survives any residual collision.

**Anti-goals**: no new palette, no gradient blobs, no motion added, no growing the ring geometry
(wave-4.5 already grew it to clear the board; growing again re-breaks the 1024×768 density gate and
pushes the hero pod past `.stage`'s `overflow:hidden`).

## 4. Approach

The pod goes from six stacked rows to **three**, which clears the 98px budget with room to spare.
No change to pod orientation and no change to the ellipse:

1. **Verb + chips puck share one row** above the cards (`.sim-actrow`), instead of two stacked rows.
2. **Position · persona · stack · range share one row** below the cards (`.sim-meta`), instead of
   four stacked rows. The persona badge renders its **head noun** ("Calling Station" ⇒ "Station"),
   with the full archetype kept in the `title` attribute — nothing is lost, the row just fits.
3. **Action label becomes a scrim pill.** `.sim-last-action` gets an OPAQUE ground mixed from
   `--felt` + `--stage-bg` (`--felt-chip-bg` is translucent at alpha .28 and would let a neighbour's
   text bleed through), pill radius, and the pod lifts `z-index` while a label is present — so a
   future content change can never re-bury the verb.

Result: villain pods drop from **127–140px to 39–81px**. Measured zero overlap at all three widths.

## 5. Files in scope

- `frontend/src/components/simulate/SimTable.tsx` — flank detection + pod markup regrouping only.
  **No change to** `revealAt` / lockstep gating, `showdownBySeat`, `revealedBySeat`, the range-button
  gating conditions, or `slotStyle()`'s ellipse math (only the `transform` anchoring may change).
- `frontend/src/styles/app.css` — `.tseat*`, `.sim-last-action`, `.sim-persona`, `.sim-chips`,
  `.sim-vrange-btn`, plus the new flank-layout rules.

**Out of scope**: `PokerTable.tsx` (Practice/Quiz — must stay untouched), any backend file,
`SimulateView.tsx` playback logic, `simPlayback.test.ts` semantics, the hero pod's verdict badge,
mobile/375px (the 9-max ring is not designed for it), and the `sim1.png`-visible fact that folded
seats' pods shrink (correct behavior).

## 6. Constraints (from `docs/ai-dlc/profile.md`)

- CSS values come from **design tokens only** — no raw hex/px outside `tokens.css`.
- WCAG 2.2 AA contrast + visible focus, **both themes** (Day and Night). The scrim pill must clear
  4.5:1 against its own ground in both, and the `range` button keeps a visible focus ring and a
  ≥24px target.
- FE types are hand-maintained (`api/types.ts`) — this pass changes no API shape, so it must not be
  touched.
- The `.stage` `overflow:hidden` invariant holds: no pod may be clipped at any in-scope width.

## 7. Verify-by

Deterministic:
- `cd frontend && npm run typecheck && npm run build` — clean.
- `./scripts/verify.sh` — backend unchanged, must stay green.
- Raw-value grep over the diff in `app.css` — no hex/px literals introduced.

Browser, at **1440 / 1280 / 1024** (owner-chosen), Simulate with a live hand:
- **Zero-overlap assertion** — for every pair of `.tseat` pods, `getBoundingClientRect()`
  intersection is empty.
- **Label hit-test** — for every rendered `.sim-last-action`,
  `document.elementFromPoint(centreX, centreY)` returns that label (or a descendant).
- **No clipping** — every pod rect is fully inside the `.stage` rect.
- Both themes (Day + Night), contrast spot-check on the scrim pill and the dimmed
  `.tseat-folded .sim-last-action` state.
- Run across a **preflop all-live** snapshot (tallest pods, worst case) and a postflop
  bet/raise/fold snapshot.

The three browser assertions above are runnable as one `page.evaluate` — that script is the
ticket done-condition, not a subjective read.
