# Tickets — P3b, phone polish for the non-felt pages (portrait)

status: **approved (pre-authorized by --auto-build invocation, 2026-09-22)** — covers T1–T2 exactly
as written and nothing else. spec: `../specs/phone-p3b-portrait.md` · contract map:
`../contracts/phone-p3b-portrait.md` · measurement: `../reviews/phone-p3b-portrait-measurement.md` ·
ledger: `../ledger/phone-and-6max.md` · roadmap: `../roadmap/phone-and-6max.md` (P3b).

## Shape of the work

One code ticket, one owner, because every rule lands in `app.css` (single-owner hotspot) and the
only TSX change is the hint's markup in `SimulateView.tsx`. It runs as the designer → browser
reviewer loop (at most three iterations; the designer never marks its own work done). Then one docs
ticket the Director does.

```
T1 (designer, one owner) ─→ design-reviewer (browser, ≤3 loops) ─→ T2 (docs, Director) ─→ PR after P4 merges
```

Worktree `$TMPDIR/wt-p3b` on branch `feat/phone-p3b-portrait`, stacked on the P4 head `eb7a576`.
An isolated stack is already running from it: backend :8126, frontend :7782 (Vite hot-reloads
edits). Baseline `make check` on the untouched worktree is green (P4's fan-in).

---

### T1 — the portrait block, the touch floor, the rotate hint

- **Owns:** `frontend/src/styles/app.css` (append-only: one new block at the very end, plus the
  touch-floor rules inside the existing phone gate), `frontend/src/components/SimulateView.tsx` (hint
  markup, hook call, dismissal state only), new `frontend/src/lib/useOrientation.ts`, new
  `frontend/src/components/simulate/rotateHint.ts` + `rotateHint.test.ts`.
- **Imitate:** the existing phone gate block for token composition and the 44px floor expression;
  `usePhoneLayout.ts` for the hook; `handCount.ts`/`handCount.test.ts` for the pure module.
- **Do:** spec items 1–8 exactly. Nothing on `.stage`, `.sim-tablering`, `.ctx`, the card rebind,
  the gate string, or `App.tsx`.
- **Acceptance:** spec Verify-by (a)–(g), measured in the browser by the reviewer, not asserted by
  the designer. `rotateHint.test.ts` proves the show/hide logic for every combination of phone,
  portrait, at-table and dismissed. Biome baseline not widened; desktop boxes unchanged.
- **Done-condition:** `make check-frontend` exits 0 from the worktree, then the design reviewer's
  verdict is PASS.

### T2 — roadmap, ledger, log, Resume (Director, after the loop)

- **Owns:** `docs/ai-dlc/roadmap/phone-and-6max.md` (P3 entry: P3b built, what was measured, the
  three Director decisions, the felt-in-portrait residual), `docs/ai-dlc/ledger/phone-and-6max.md`
  (measurement summary, spec review, fan-in), `docs/ai-dlc/log.md`, `docs/ai-dlc/profile.md`.
- **Done-condition:** the P3 entry carries the build status; the ledger has the review rounds with
  every finding adjudicated; Resume points at always-on as the next action.
