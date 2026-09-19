# Spec — P3a, make the phone playable: fix the page chrome, not the felt

status: **rev 1, APPROVED** — owner ruled 2026-09-19 to skip the throwaway prototype (slice P2) and
fix this for real, after a browser measurement answered P2's question without building anything.
slice of: `../roadmap/phone-and-6max.md` — promoted from the NEXT lane's **P3 (phone polish)**,
replacing slice P2.
evidence: `../ledger/phone-and-6max.md`, "P2 felt measurement, 2026-09-19".

## Bottom line

The poker felt is fine on a phone. The page around it is what makes the app unplayable, and the
problem is **vertical, not horizontal**. Fix four things and the owner can play twenty hands in
landscape without fighting the page.

A browser measurement at three Android landscape sizes found **zero seat-pod overlaps and zero
sideways scrolling at six seats**, and only grazing bounding boxes at nine. The ring geometry needs
no retune. What breaks is that you cannot see the table and the action buttons at the same time —
a shortfall of 67px at 915×412 and 115px at 800×360 — the action bar is not pinned, the page height
jumps 371px mid-hand, and the button that starts the next hand sits 229px above the viewport at a
tiny 100×32px.

**This slice replaces the planned prototype.** P2 existed to decide whether the felt needed a
redesign. The measurement decided it: no. Building five throwaway screens to re-ask an answered
question would be waste, so the owner ruled on 2026-09-19 to spend the effort on the real fix.

## What was measured, and what it means

All figures from a headless Chromium at the stated CSS viewport, against `origin/main` at `aa76605`.

| Finding | Number | Consequence |
|---|---|---|
| Seat-pod overlaps, 6-max, landscape | **0** at 915×412, 851×393, 800×360 | The ring math already handles six seats. Do not touch it. |
| Seat-pod overlaps, 9-max, landscape | 1–3 grazing pairs, text collisions ≤45px² | Usable, no margin. Leave it; 6-max is the phone format. |
| Horizontal scroll, landscape | **0 excess at every width** | There is no sideways-scroll problem in landscape. |
| Page intrinsic minimum width | **713px**, caused by the `.nav-tab` row | The masthead's own minimum is 574px. The nav row is the real culprit, and it only bites in portrait. |
| Ring top → action-bar bottom | 479px at 412 tall, 475px at 360 tall | **The core defect.** You cannot see the table and your buttons at once. |
| Document height within one hand | **1166 → 1537px** | A 371px shift under the player's thumb as verdict panels mount. |
| "Next hand →" position and size | document y=168, **100×32px** | 229px above the viewport where the player just acted, and below the 44px touch minimum. |
| Action-button targets | all **≥50px** in both dimensions | Already fine. "Bigger action buttons" is done; do not enlarge further. |
| Stacks and pot type size | **12px**, no responsive rule | The weakest readability point at arm's length. |

**Not measured, and it matters:** real Android Chrome reserves roughly another 56–100px for its URL
bar on first paint, so the vertical shortfall on the owner's actual phone is **worse** than the
numbers above, never better.

## Goal

One line: on an Android phone in landscape, the owner can see the table and act on it without
scrolling, and can start the next hand without hunting for a button.

## Behaviour

### 1. The action bar is pinned to the bottom of the viewport

`.decisionbar` computes `position: static` today, so it scrolls away with the page.

**Imitate the existing sim-scoped override at `frontend/src/styles/app.css:581`,
`.decisionbar.sim-actionbar`.** That selector already exists precisely so Simulate can diverge from
the `.decisionbar` that Practice and Quiz share. Use it; do not touch the base class.

- Pin it within a phone breakpoint only.
- **Desktop at 1280px must stay pixel-identical.** That is the roadmap's own constraint on this
  lane, and it is the acceptance test.
- The focus ring is 3px at 2px offset; when the bar sits flush against the viewport bottom its
  lower 5px is clipped today. Leave room for the ring.

### 2. Starting the next hand does not require scrolling

`frontend/src/components/SimulateView.tsx:1194` renders "Next hand →" in the topbar. At hand end in
landscape it is 229px above the viewport and 100×32px.

- It must be reachable **without scrolling** from the position the player is already in, and at
  least **44×44px**.
- The natural home is the pinned action bar from §1 — the hand is over, so the fold/call/raise
  controls have nothing to do. Reuse that space rather than adding a second fixed element.
- Do not remove the topbar control on desktop.

### 3. A hidden bottom tab bar, with one button to show it

The page spends **212–257px above the felt** on masthead and nav before the table starts. That is
more than half a 412px-tall viewport.

The owner asked for this shape directly in the roadmap interview: *"bottom tab bar, hidden by
default, one button shows it."* Build that, on the phone breakpoint only.

- Hidden by default on the Simulate route; one visible control reveals it.
- It replaces the top nav row's job on phones; it does not duplicate it.
- The `.nav-tab` row is what forces the 713px intrinsic minimum — reflowing or hiding it on the
  phone breakpoint is what removes the portrait sideways scroll as a side effect.

### 4. The page stops jumping mid-hand

Document height swings 1166 → 1537px inside a single hand as verdict and recap panels mount.
Combined with an unpinned bar, the controls move under the player's thumb between one action and
the next.

Pinning the bar (§1) fixes most of this by construction. What remains is that the panels mounting
below should not move what is above them. **Do not solve this by suppressing the verdict** — the
grading feedback is the product.

### 5. All-in gets a confirm step

From the owner's interview: *"bigger action buttons with a confirm step on all-in."* The buttons are
already ≥50px, so only the confirm is outstanding. A shove is the one irreversible action on the
table, and a mis-tap costs the stack.

Phone breakpoint only. Do not add a confirm to fold, call or raise.

### 6. One defect from the 6-max slice

At six seats the SB pod lands top-centre, where the context line lives, and its "0.5bb" chip badge
covers the last **7.7×13.5px** of *"ranges shown are 9-max ranges"*. Not present at nine seats,
because no pod sits there. Shipped in `aa76605`; fix it here.

## Out of scope

No change to the ring geometry or seat positions — measured clean at six seats. No portrait felt.
No responsive type scale beyond what §1–§3 require. No PWA manifest, no service worker, no offline
anything. No new dependency. No change to Practice or Quiz behaviour, though they may inherit an
app-shell breakpoint — if they do, they get a design-review pass in the same change. No touching
the paused persona-realism lane.

## Constraints

- **CSS values come from design tokens only.** No raw hex or px outside `tokens.css`.
- **WCAG AA contrast and a visible focus ring, in both themes.** The measurement covered only the
  NIGHT theme; DAY is unverified and must be checked.
- `frontend/src/styles/app.css` and `frontend/src/App.tsx` are hotspots — **single owner per pass**.
- `.decisionbar`, `.stage`, `.felt`, `.tablering`, `.tseat` and `.card` are **shared with Practice
  and Quiz**. Base-class edits bleed app-wide. Every change here is sim-scoped or
  breakpoint-scoped.
- Frontend API types are hand-maintained; this slice should need none.
- This repository is public.

## Golden-path files to imitate

| New thing | Imitate |
|---|---|
| A sim-scoped override of a shared class | `.decisionbar.sim-actionbar`, `frontend/src/styles/app.css:581` |
| A phone breakpoint | the existing narrow gates at `app.css:2551`, `:2602`, `:2622`, `:2955` |
| A pure frontend module + test | `frontend/src/components/simulate/handCount.ts` and `handCount.test.ts` |
| A confirm interaction | the existing Challenge blind-check flow in `SimBlindCheck.tsx` |

## Verify-by

1. `make check` green, both halves.
2. **Desktop at 1280px is pixel-identical to `aa76605`.** Capture before and after; this is the
   constraint the roadmap put on this lane.
3. At 915×412, 851×393 and 800×360 landscape, on a 6-max felt: the table and the action buttons are
   **both visible without scrolling**.
4. "Next hand →" is reachable with no scroll and measures at least 44×44px.
5. The bottom tab bar is hidden by default and one control reveals it.
6. Document height no longer moves the action controls between one action and the next.
7. An all-in asks for confirmation; fold, call and raise do not.
8. The SB chip badge no longer covers the 6-max context line.
9. Portrait at 412px wide: no horizontal scroll — the 713px intrinsic minimum is gone.
10. AA contrast and a visible focus ring on every new or moved control, **in both themes**.
11. Practice and Quiz are unchanged, or changed deliberately and reviewed.

## Definition of done

Every criterion above passes, `make check` exits clean, nothing outside the files this spec names
has changed, and a browser measurement at the three landscape viewports confirms items 3, 4 and 9
with numbers rather than impressions. The owner's twenty-hand play session remains the product
verdict, and the roadmap box stays unticked until he gives it.
