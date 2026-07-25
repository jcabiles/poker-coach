# Tickets — `sim-felt-seat-pod-collision-ux`

Spec: `docs/ai-dlc/specs/sim-felt-seat-pod-collision-ux.md`

`app.css` is a hotspot with a **single owner per pass** — T1→T2→T3 are sequential, not parallel.
T4 is the checker and must run last (maker ≠ checker).

Shared done-condition script (used by T1–T4), run at 1440 / 1280 / 1024 on `/simulate` with a live hand:

```js
() => {
  const stage = document.querySelector('.stage').getBoundingClientRect();
  const pods = [...document.querySelectorAll('.tseat')];
  const overlaps = [], clipped = [], hidden = [];
  pods.forEach((p, i) => {
    const a = p.getBoundingClientRect();
    if (a.left < stage.left || a.right > stage.right || a.top < stage.top || a.bottom > stage.bottom)
      clipped.push(p.querySelector('.pos, .herometa')?.textContent?.trim());
    pods.slice(i + 1).forEach(q => {
      const b = q.getBoundingClientRect();
      const w = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (w > 0 && h > 0) overlaps.push([i, Math.round(w), Math.round(h)]);
    });
    const la = p.querySelector('.sim-last-action');
    if (la) {
      const r = la.getBoundingClientRect();
      const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      if (!(hit === la || la.contains(hit))) hidden.push(la.textContent);
    }
  });
  return { overlaps, clipped, hidden };  // PASS ⇔ all three arrays empty
}
```

---

## T1 — Merge the pod meta rows into one line

**Owns**: `frontend/src/components/simulate/SimTable.tsx`, `frontend/src/styles/app.css`

Collapse the villain pod's three separate meta rows (`.pos` pill, `.sim-persona`, `.stack`) plus the
`range` control into a single horizontal meta line under the cards. Keep every piece of information —
position, dealer button, persona archetype, stack, all-in flag, range affordance — nothing is dropped.

**Acceptance**
- Villain pod height at preflop all-live drops from 127–140px to **≤ 100px** at all three widths.
- Position, `D` button, persona label, stack, `all-in` flag, and the `range` button are all still
  present and still gated by exactly the same conditions as today (persona present · not staged-folded ·
  not `hand_over`).
- `range` button keeps a ≥24px hit target, visible focus ring, and its `aria-pressed` / `aria-label`.
- Hero pod (`.heroseat`) is unchanged.
- Tokens only — no raw hex/px added.

**Done-condition**: `npm run typecheck && npm run build` clean; the script above reports pod heights
≤100 (add a temporary height probe) at 1440/1280/1024.

---

## T2 — Flank pods lay out horizontally, anchored on their outer edge

**Owns**: `frontend/src/components/simulate/SimTable.tsx`, `frontend/src/styles/app.css`
**Depends on**: T1

Detect flank seats from the ring index (the seats whose ellipse angle puts them near the horizontal
extremes — left column and right column) and render those pods as a **row**: face-down cards / revealed
cards beside the T1 meta line, with the action label and chips puck in the compact column. Anchor flank
pods by their outer edge (left flank grows inward/right, right flank grows inward/left) so widening
cannot clip against `.stage`'s `overflow:hidden`.

Do **not** change `slotStyle()`'s ellipse math (`43` / `41` / `38` radii) — only the `transform`
anchoring may vary per flank.

**Acceptance**
- Flank pod height **≤ 60px** (under the measured 65px tightest anchor gap) at all three widths.
- `overlaps` array from the script is **empty** at 1440 / 1280 / 1024, in both a preflop all-live
  snapshot and a postflop bet/raise/fold snapshot.
- `clipped` array is **empty** — no pod escapes `.stage`.
- Top and bottom pods keep the current vertical layout.
- Lockstep gating, showdown reveal, and R1 `revealedBySeat` behavior are byte-for-byte unchanged.

**Done-condition**: script returns `overlaps: []` and `clipped: []` at all three widths.

---

## T3 — Action label becomes a scrim pill with a stacking lift

**Owns**: `frontend/src/styles/app.css` (+ `SimTable.tsx` only if a z-index class is needed)
**Depends on**: T2

Give `.sim-last-action` an opaque felt-chip ground, pill radius, and tight padding, and lift the pod's
stacking order while a label is present, so the verb is legible even if a future content change
reintroduces an overlap.

**Acceptance**
- `hidden` array from the script is **empty** — every rendered verb passes its own hit-test.
- Scrim pill text clears **4.5:1** against the pill ground in **both** Day and Night themes; the dimmed
  `.tseat-folded .sim-last-action` state also clears 4.5:1.
- The pill does not increase pod height past T2's ≤60px flank budget.
- Tokens only — the ground is mixed from existing felt tokens, no new raw color.

**Done-condition**: script returns `hidden: []`; contrast numbers recorded for both themes.

---

## T4 — Adversarial design review + gates

**Owns**: nothing (review only)
**Depends on**: T1, T2, T3

Fresh-context review of the finished felt against the spec's design commitment, at 1440 / 1280 / 1024,
both themes, with screenshots.

**Acceptance**
- Script returns `{overlaps: [], clipped: [], hidden: []}` at all three widths, both a preflop
  all-live and a postflop action snapshot.
- `cd frontend && npm run typecheck && npm run build` — clean.
- `./scripts/verify.sh` — green (backend untouched).
- No raw hex/px introduced in the `app.css` diff.
- `PokerTable.tsx` shows **zero** diff (Practice/Quiz unaffected).
- Final screenshots captured at each width, both themes, for the completion report.
