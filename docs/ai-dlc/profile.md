# AI-DLC profile — poker-coach

stack:        mixed — Python/FastAPI backend + React/Vite/strict-TS frontend
artifact_dir: docs/ai-dlc

# The governing initiative. A fresh session reads this first, opens that roadmap,
# and resumes from its first unchecked slice — never from memory of what seemed
# next. This field was missing entirely until 2026-08-18, which is why the boot
# checklist in .claude/CLAUDE.md kept pointing at a key that was not there.
active:       phone-and-6max
              # roadmap: docs/ai-dlc/roadmap/phone-and-6max.md (APPROVED 2026-09-18)
              # current slice: always-on stack — P4 on PR #232, P3b built on top (PR after #232 merges)
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

updated:      2026-09-22 (P3b built) · commit: see branch feat/phone-p3b-portrait · log-entry: "2026-09-22 — P3b (portrait polish for the non-felt pages) built, stacked on P4"
position:     P4 is on PR #232 (owner merges). P3b is built, gated and design-reviewed on branch
              feat/phone-p3b-portrait, stacked on P4's head; its PR opens once #232 merges.
              Roadmap: P1, S1 ticked; P2 replaced by P3a; P3b done pending PR. Always-on is next.
merged:       #229 (P1), #230 (S1), #231 (P3a). #232 (P4) awaits the owner.
awaiting John: (a) merge #232, then say so and the P3b PR opens (rebase onto main + new branch if
              the squash makes it dirty); (b) one Simulate hand on the phone and the 20-hand
              landscape verdict; (c) a stray vite on :7790 from the designer's measurement —
              `kill $(lsof -ti:7790)` in a plain terminal; (d) `agy` login if Gemini review is wanted.
authorized:   the 2026-09-22 `--auto-build` invocation covered P4 (spent), P3b (spent) and
              always-on (next, Gate 1 already confirmed). Owner merges every PR; Claude never merges.
next action:  `/ai-org:spec --auto-build always-on stack` — launchd job + owner-run install and
              uninstall scripts; branch from the P3b head.
