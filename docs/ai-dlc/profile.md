# AI-DLC profile — poker-coach

stack:        mixed — Python/FastAPI backend + React/Vite/strict-TS frontend
artifact_dir: docs/ai-dlc

# The governing initiative. A fresh session reads this first, opens that roadmap,
# and resumes from its first unchecked slice — never from memory of what seemed
# next. This field was missing entirely until 2026-08-18, which is why the boot
# checklist in .claude/CLAUDE.md kept pointing at a key that was not there.
active:       bot-realism-flywheel
              # roadmap: docs/ai-dlc/roadmap/bot-realism-flywheel.md
              # current slice: Two-mode Simulate (Training / Challenge) —
              #   spec'd 2026-08-26, awaiting owner approval at the plan gate.
              # slice 3 (calldown): play session PLAYED 2026-08-25 (1050 hands);
              #   OPEN pending only the owner's written per-persona verdict.
              # paused: persona-realism (see its top banner)

verify:
  test:  ./scripts/verify.sh          # backend pytest + boot probe → "BACKEND VERIFY OK"
  lint:  cd backend && ruff check .
  build: cd frontend && npm run typecheck && npm run build
  boot:  ./scripts/serve.sh start     # backend :8008 (health GET /api/v1/health) + vite :5173, background (or: poker-coach)

hotspots:
  - frontend/src/styles/tokens.css    # design tokens — single owner per pass
  - frontend/src/styles/app.css       # all component CSS
  - frontend/src/App.tsx              # shell, hash routing, all view state
  - frontend/src/api/types.ts         # hand-maintained FE API types
  - backend/app/services/grading.py   # grading orchestration
  - backend/alembic/versions/         # migrations — sequential, never parallel-owned

invariants:
  - domain core backend/app/domain/ has no web/DB imports (test-enforced)
  - results are frequency + EV, never boolean
  - grading stays behind the one async StrategyProvider
  - strategy lives in versioned content/ data, not code
  - CSS values come from design tokens only (no raw hex/px outside tokens.css)
  - WCAG AA contrast + visible focus, both themes
  - every schema change ships an Alembic migration
  - spot_signature() is frozen (changing it orphans SRS history)
  - FE types hand-maintained in frontend/src/api/types.ts (schema.d.ts is unwired)
  - EVs labeled approximate until solver phase

auth:         none — local single-user app; no accounts/hosting/billing

process:      may push + open PRs on feat/*|fix/*|chore/* autonomously; never push main,
              never force-push, never merge without explicit confirmation

## Resume

updated:      2026-08-26
commit:       bc40c1c   (branch `feat/two-mode-simulate`, in a worktree, UNPUSHED)
log-entry:    "2026-08-26 — Two-mode Simulate: build waves 1-2 landed"
position:     `/ai-org:build` running the **Two-mode Simulate** slice. The owner approved the
              plan at the go-gate on 2026-08-26; the ticket file, the spec and
              `plans/two-mode-simulate.md` all read `status: approved`. Approval covers
              building all eight tickets, running migration `0015` against the local
              development database, and committing to the feature branch. It does **not**
              cover merging.
merged:       nothing. The branch has never been pushed.
progress:     T1 (two nullable session columns + migration `0015`) — committed `e3b3cde`,
              review APPROVE. T2 (mode accepted at creation, carried on every response) —
              committed `bc40c1c`, review APPROVE WITH FINDINGS, both Major findings fixed
              and verified. T3 (completed-hand count + server-side deal barrier) — in flight.
              T4-T8 not started.
next action:  finish the T3 barrier, then T4 (blind-check endpoint), T5 (frontend types and
              client), T6 (mode-choice screen), T7 (display gate + Labels toggle), T8 (the
              hand-200 dialog). One ticket at a time — nothing in the chain parallelises.
where:        the build runs in a worktree, NOT the main checkout, because another session is
              writing to the shared tree. Its Python environment and Node packages are
              symlinks into the main checkout; `PYTHONPATH=.` is mandatory or tests silently
              run against the main checkout's source.
baseline:     the worktree runs `2197 passed, 2 skipped, 0 failed`. The two skips read a
              machine-local data file that is not in the worktree; in the main checkout the
              same two tests FAIL. Inside the worktree any failure is ours.
awaiting John: (a) the written per-persona verdict that closes flywheel slice 3 — the
              1050-hand session is already played, only the verdict is owed; (b) two
              theory-contract items still open from 2026-08-24 (ledger finding B1, and
              section 10.2 of the git-excluded persona-realism audit).
