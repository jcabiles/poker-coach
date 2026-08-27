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

updated:      2026-08-27
commit:       496557a  (branch `feat/two-mode-simulate`, in a worktree, **NEVER PUSHED**)
log-entry:    "2026-08-27 — Two-mode Simulate: all eight tickets built and reviewed"
position:     **Two-mode Simulate is BUILT and REVIEWED, and stops there.** All eight tickets
              are committed to `feat/two-mode-simulate`. Nothing is pushed, nothing is merged,
              and the roadmap box is deliberately unticked.
authorized:   The owner approved building, running migration `0015` against the local
              development database, and committing to the branch. That is spent. **Merging was
              explicitly excluded and still needs a separate confirmation.**
gates:        backend `2239 passed, 2 skipped, 0 failed`, ruff clean; frontend typecheck and
              build clean; frontend suite `60 passed` (35 when the slice started).
chain:        T1 columns+migration `e3b3cde` · T2 mode on the wire `bc40c1c` · T3 hand count +
              deal barrier `929bda1` · T4 blind-check endpoint `ca31800` · T5 frontend types
              `6672ffa` · T6 sit-down screen `982c023` · T7 display gate + Labels toggle
              `b3bef9d` · T8 hand-200 dialog `496557a`.
records:      per-barrier detail in `reviews/two-mode-simulate-build.md`; forty-four
              build-phase findings with their adjudications in `ledger/two-mode-simulate.md`.
next action:  the owner plays it. This initiative's precedent is that the play session, not the
              gate numbers, is the product verdict — the same rule keeping slice 3 open. Then a
              merge decision.
where:        the build ran in a worktree, NOT the main checkout, because another session was
              writing to the shared tree. Its Python environment and Node packages are symlinks
              into the main checkout; `PYTHONPATH=.` is mandatory or tests silently exercise the
              main checkout's source. The worktree baseline is `0 failed` — two tests that FAIL
              in the main checkout skip there for want of a machine-local data file.
carried fwd:  three items, all in the ledger, none hidden — the preflop exploit note is
              **structurally unreachable in Simulate** and always has been (pre-existing, not
              this slice's); one display helper is now duplicated three ways across files the
              slice froze; two modules stand well past the file-size guidance.
awaiting John: (a) play the slice, then decide on merging; (b) the written per-persona verdict
              that closes flywheel slice 3 — the 1050-hand session is already played, only the
              verdict is owed; (c) two theory-contract items open since 2026-08-24.
