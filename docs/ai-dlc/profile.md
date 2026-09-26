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

updated:      2026-09-26 (M1 spec written and reviewed) · commit: see branch docs/m1-6max-baseline-spec · log-entry: "2026-09-26 — M1 (6-max baseline) spec + tickets, review adjudicated"
position:     Roadmap `roadmap/bot-realism-6max.md` is merged (#240). M1 (measure the bots on
              6,000 simulated 6-max hands and check the simulation against the owner's 200 real
              hands) is spec'd: `specs/m1-6max-baseline.md` rev 2, `tickets/m1-6max-baseline.md`
              (6 tickets, T1–T6), `ledger/m1-6max-baseline.md` (8 findings, all folded). Build has
              not started.
merged:       #236–#240. The M1 spec PR is not.
awaiting John: (a) merge the M1 spec PR; (b) approve the M1 tickets for build; (c) always-on
              agent fix (macOS Full Disk Access for /bin/bash, or move the repo); (d) `git worktree
              prune`.
authorized:   nothing standing. The ticket file says `status: proposed`; build needs the owner's
              explicit go, then `/ai-org:build` in a fresh session. Does NOT cover M1b, M2 or R1.
next action:  on approval: `/clear`, then `/ai-org:build M1 — measure the 6-max baseline`. R1
              (stack-depth research) can run alongside via `/research`.
