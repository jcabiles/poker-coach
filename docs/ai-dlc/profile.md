# AI-DLC profile — poker-coach

stack:        mixed — Python/FastAPI backend + React/Vite/strict-TS frontend
artifact_dir: docs/ai-dlc

# The governing initiative. A fresh session reads this first, opens that roadmap,
# and resumes from its first unchecked slice — never from memory of what seemed
# next. This field was missing entirely until 2026-08-18, which is why the boot
# checklist in .claude/CLAUDE.md kept pointing at a key that was not there.
active:       phone-and-6max
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

updated:      2026-09-23 (phone table fit built; PR opening) · commit: see branch feat/phone-table-fit · log-entry: "2026-09-23 — Phone table fit built (right-edge dock, two-row seats, full screen)"
position:     Every phone slice in NOW is merged, and so is phone review depth (#236). The owner's
              first real phone session found the landscape felt crowded: a Chrome tab is 914×290,
              not the 800×360 P3a measured. The phone table fit slice (`/ai-org:design`) is built,
              gated, browser-verified in three rounds and refuted on `feat/phone-table-fit`; its PR
              awaits the owner. The 6-max realism research still needs the owner's 6-max play
              notes. The flywheel roadmap still has one box open (Challenge-mode session to hand 200).
merged:       #229, #230, #231, #232, #235, #236. The table-fit PR is not.
awaiting John: (a) merge the table-fit PR; (b) on the phone in landscape, one 6-max and one 9-max
              hand with and without the full-screen button (this slice's pass/fail), which also
              covers P1 leg (a), P4's cross-device leg and the 20-hand landscape verdict; (c) run
              `./scripts/always_on_install.sh` from the MAIN checkout; (d) a 6-max session with play
              notes; (e) Challenge mode to hand 200; (f) stray dev servers the sandbox cannot kill:
              `kill $(lsof -ti:7790,7783,7791,7792,7793,8131,8141) $(lsof -ti:7801-7860)`; (g) `git
              worktree prune` (clears the half-removed review-depth worktree record).
authorized:   nothing standing. The 2026-09-22 `/ai-org:design` phone-table fix is fully spent.
              Owner merges every PR; Claude never merges.
next action:  after the owner's phone check: fix anything it finds, or `/ai-org:spec` for the 6-max
              realism research once 6-max play notes exist. Portrait felt geometry and History paging
              remain recorded, not built.
