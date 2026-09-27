# AI-DLC profile — poker-coach

stack:        mixed — Python/FastAPI backend + React/Vite/strict-TS frontend
artifact_dir: docs/ai-dlc

# The governing initiative. A fresh session reads this first, opens that roadmap,
# and resumes from its first unchecked slice — never from memory of what seemed
# next. This field was missing entirely until 2026-08-18, which is why the boot
# checklist in .claude/CLAUDE.md kept pointing at a key that was not there.
active:       bot-realism-6max
              # roadmap: docs/ai-dlc/roadmap/phone-and-6max.md (APPROVED 2026-09-18)
              # run of 2026-09-22 complete: P4 (#232) → P3b (#233) → always-on (PR), stacked; owner merges in order
              # prior: bot-realism-flywheel — Two-mode Simulate MERGED 2026-09-18, box unticked
              #   until the owner plays Challenge mode; slice 3 (calldown) CLOSED 2026-09-18.
              # cleanup project (docs/cleanup-project-brief.md): slice 2 done; 1 and 3 wait.
              # paused: persona-realism (see its top banner)

verify:
  check: make check                   # THE gate — format check + lint + types + tests, both halves (CI runs the same)
  test:  ./scripts/verify.sh          # leaf: backend pytest + boot probe → "BACKEND VERIFY OK" (never two at once)
  lint:  cd backend && ruff check . && ruff format --check . ; cd frontend && npm run lint   # ruff + Biome
  types: cd backend && PYTHONPATH=. .venv/bin/mypy app ; cd frontend && npm run typecheck
  build: cd frontend && npm run build
  boot:  ./scripts/serve.sh start     # backend :8008 (health GET /api/v1/health) + vite :7777, background (or: poker-coach)

conventions:                          # golden-path file per kind of thing — imitate, don't invent
  route:            backend/app/api/v1/simulate.py
  schema:           backend/app/schemas/simulate.py
  service:          backend/app/services/sim_session.py
  domain provider:  backend/app/domain/providers/turn.py
  migration:        backend/alembic/versions/0015_sim_session_mode.py
  backend test:     backend/tests/test_two_mode_simulate_gate.py
  react component:  frontend/src/components/simulate/SimGradingToggle.tsx
  pure FE module:   frontend/src/components/simulate/handCount.ts (+ handCount.test.ts)
  baselines:        BASELINE(YYYY-MM-DD) markers in backend/pyproject.toml [[tool.mypy.overrides]] and frontend/biome.jsonc

hotspots:
  - frontend/src/styles/tokens.css    # design tokens — single owner per pass
  - frontend/src/styles/app.css       # all component CSS
  - frontend/src/App.tsx              # shell, hash routing, all view state
  - frontend/src/api/types.ts         # hand-maintained FE API types
  - backend/app/domain/grading.py     # grading orchestration (was mis-listed as services/grading.py until 2026-09-18)
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

updated:      2026-09-26 (M1 build PAUSED by owner to save usage) · commit: see branch feat/m1-6max-baseline · log-entry: "2026-09-26 — M1 build paused after T1+T5; T2 stopped mid-way"
position:     M1 build (approved 2026-09-26; tickets `tickets/m1-6max-baseline.md`) is paused on
              branch `feat/m1-6max-baseline` (pushed to origin). DONE + committed: T1 (simulator
              deals any table size; Director re-ran checks, pinned 9-max digests unchanged) and
              T5 (cited 6-max ranges, 32/36 cells VERIFIED). T2 (move stats code into
              `tools/table_stats.py`) was STOPPED mid-run: its files are committed in a commit
              marked "WIP — UNVERIFIED" and must be re-verified before anything builds on them.
merged:       #236–#241. The M1 build branch has no PR yet.
awaiting John: resume the build when usage allows; (older) always-on agent fix; `git worktree prune`.
authorized:   T1–T6 of M1 (ticket file `status: approved`), building + committing + pushing
              `feat/m1-6max-baseline` + opening its PR. NOT merging; NOT M1b, M2 or R1.
next action:  `/ai-org:build M1 — measure the 6-max baseline` (resume). First: recreate a worktree
              for `feat/m1-6max-baseline` (symlink backend/.venv and frontend/node_modules from
              the main checkout), then re-run T2's done-condition from the ticket (capture the
              "before" file from origin/main first — the one in $TMPDIR may be gone), fix what
              fails, then T3 → T4 → T6 per the ticket file. Baseline: backend 2306 passed/2
              skipped, frontend 135.
