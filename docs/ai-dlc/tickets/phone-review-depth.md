# Tickets — phone review depth (review card, stats and leaks, hand replayer)

status: **approved (pre-authorized by --auto-build invocation, 2026-09-22)** — covers T1–T2 exactly
as written and nothing else. spec: `../specs/phone-review-depth.md` (rev 2) · contract map:
`../contracts/phone-review-depth.md` · measurement: `../reviews/phone-review-depth-measurement.md` ·
ledger: `../ledger/phone-and-6max.md` (Round 6) · roadmap: `../roadmap/phone-and-6max.md` ("Phone
review depth", NEXT lane).

## Shape of the work

One code ticket, one owner, because the CSS lands in `app.css` (single-owner hotspot) and the JSX
changes in four components share one behaviour (open/close scroll and focus) that must be built the
same way at both entry points. A fresh `refuter` reviews the diff and a fresh browser reviewer
measures the Verify-by legs (no jsdom in this repo, so the browser is the only regression net for
JSX — contract map, tests section). Then one docs ticket the Director does.

```
T1 (heavy-worker, one owner) ─→ refuter (diff) + design-reviewer (browser) ─→ T2 (docs, Director) ─→ PR
```

Worktree `$TMPDIR/wt-rd` on branch `feat/phone-review-depth` from `main` c0e3269. An isolated stack
is running from it: backend :8131, frontend :7791 (Vite hot-reloads edits; restart it before
eyeballing if it serves a stale module). Baseline `make check` on the untouched worktree: green
(refuter ran typecheck, vitest and the Biome lint at Round 6).

---

### T1 — dock "Review ↓", replay open/close scroll + focus, Esc, History rotate hint, touch floor, coach-note width

- **Owns:** `frontend/src/styles/app.css` (three existing blocks only: the 640px block at ~4832, the
  per-element focus opt-out at ~6047, the phone-gate floor list at ~7036 plus one `scroll-margin-top`
  rule in the gate), `frontend/src/components/SimulateView.tsx`, `frontend/src/components/HistoryView.tsx`,
  `frontend/src/components/simulate/HandReplay.tsx`, `frontend/src/components/simulate/HandReplayTable.tsx`,
  `frontend/src/components/simulate/rotateHint.ts` (+ its test only if the move needs an import fix).
- **Imitate:** spec "Golden paths" — `errorPanelRef` + `tabIndex={-1}` for focus moves; the existing
  keydown handlers for Esc; `HandReplayTable`'s optional reveal props for the new optional prop; the
  phone-gate floor list for CSS.
- **Do:** spec "What changes" items 1–6 exactly, including every rev-2 clause (deal-key skip list,
  `preventScroll`, focus-ring opt-out on the wrapper only, the Esc guard, the hint inside the section,
  the pending-restore guard, refs on both `HandReplay` return paths, helpers moved not renamed).
  Nothing on `App.tsx`, `types.ts`, `.stage`, `.sim-tablering`, the gate string, the portrait block,
  the Dashboard, or the backend.
- **Acceptance:** spec Verify-by (a)–(j), measured in the browser by the reviewer, not asserted by
  the worker. Desktop 1280×800 boxes unchanged. Biome baseline not widened.
- **Done-condition:** `make check` exits 0 from the worktree (`cd $TMPDIR/wt-rd && make check`), then
  the refuter's verdict on the diff is PASS and the design reviewer's browser pass is PASS.

### T2 — roadmap, ledger, log, Resume (Director, after fan-in)

- **Owns:** `docs/ai-dlc/roadmap/phone-and-6max.md` ("Phone review depth" entry: built, measured
  findings, the History pagination follow-up; tick P4 with its merge note; record #235), the ledger
  fan-in entry, `docs/ai-dlc/log.md`, the profile's Resume block, the spec's "Built as" section if the
  build deviated.
- **Done-condition:** the PR is open on `feat/phone-review-depth` with the docs in the same commit set;
  the shared main tree is clean.
