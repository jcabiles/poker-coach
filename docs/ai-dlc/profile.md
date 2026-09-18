# AI-DLC profile — poker-coach

stack:        mixed — Python/FastAPI backend + React/Vite/strict-TS frontend
artifact_dir: docs/ai-dlc

# The governing initiative. A fresh session reads this first, opens that roadmap,
# and resumes from its first unchecked slice — never from memory of what seemed
# next. This field was missing entirely until 2026-08-18, which is why the boot
# checklist in .claude/CLAUDE.md kept pointing at a key that was not there.
active:       phone-and-6max
              # roadmap: docs/ai-dlc/roadmap/phone-and-6max.md (APPROVED 2026-09-18)
              # current slice: P1 (LAN walking skeleton) once approved
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

updated:      2026-09-18 (roadmap drafted)
commit:       main 0e7dd2a — #222, #224, #225 merged; phone-and-6max roadmap on PR #226 (draft)
log-entry:    "2026-09-18 — Cleanup slice 2 built: `make check` is the gate"
position:     Two-mode Simulate is on main; its roadmap box stays unticked until the owner plays
              Challenge mode to the hand-200 check. Cleanup slice 2 is DONE: `make check` is the
              one gate, CI runs the same targets (frontend on Node 24 — Node 20's npm 10 fails
              `npm ci` on the npm-11 lockfile). Flywheel slice 3 CLOSED 2026-09-18.
merged:       #222 (squash de9cb71), #224 (squash 9f26713); #223 closed as superseded.
awaiting John: (a) play Challenge mode, then tick the slice; (b) two theory-contract items open
              since 2026-08-24 (ledger finding B1; §10.2 of the git-excluded audit).
authorized:   nothing standing. The 2026-09-18 merge grant is spent.
next action:  owner approves docs/ai-dlc/roadmap/phone-and-6max.md (drafted 2026-09-18 after a
              full interview), then `/ai-org:spec P1 — LAN walking skeleton`. Cleanup slices 1
              and 3 and the mypy/Biome burn-down wait behind it.
