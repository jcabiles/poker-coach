# AI-DLC profile — poker-coach

stack:        mixed — Python/FastAPI backend + React/Vite/strict-TS frontend
artifact_dir: docs/ai-dlc

# The governing initiative. A fresh session reads this first, opens that roadmap,
# and resumes from its first unchecked slice — never from memory of what seemed
# next. This field was missing entirely until 2026-08-18, which is why the boot
# checklist in .claude/CLAUDE.md kept pointing at a key that was not there.
active:       bot-realism-flywheel
              # roadmap: docs/ai-dlc/roadmap/bot-realism-flywheel.md
              # current slice: Two-mode Simulate — MERGED 2026-09-18, box unticked
              #   until the owner plays Challenge mode.
              # slice 3 (calldown): CLOSED 2026-09-18 on the owner's verdict.
              # cleanup slice 2 (quality gates): BUILT 2026-09-18 on chore/quality-gates.
              # next: cleanup slice 3 or 1 (docs/cleanup-project-brief.md).
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

updated:      2026-09-18
commit:       branch `chore/quality-gates` (stacked on `feat/two-mode-simulate`); NEITHER PUSHED —
              no GitHub token on this machine (gh is logged out); owner re-auths, then push + PR
log-entry:    "2026-09-18 — Cleanup slice 2 built: `make check` is the gate"
position:     Two branches complete and locally committed. (1) `feat/two-mode-simulate`: built
              2026-08-27, fresh dual review 2026-09-18, fixes applied, gates green — merge
              authorized by the owner, blocked only on push. (2) `chore/quality-gates`: cleanup
              slice 2 built end to end; `make check` green on the worktree; fresh refuter review
              at the fan-in (ledger build record). Flywheel slice 3 CLOSED 2026-09-18.
merged:       nothing new this session (push blocked).
awaiting John: (a) `gh auth login --hostname github.com --git-protocol https --insecure-storage
              --with-token` in a real terminal, then any session can push both branches and open
              the PRs (two-mode first, gates second); (b) play Challenge mode to the hand-200
              check, then tick the slice; (c) three worktree dev-server processes on ports
              8018/7778 the sandbox could not kill (see the session's final report).
authorized:   Owner 2026-09-18: merge this run's PRs once gates are green and a fresh reviewer
              approves — both branches satisfy that; the merge itself still needs the push.
              Lapses at the end of the 2026-09-18 session.
next action:  push both branches, open PRs, merge two-mode then gates; then cleanup slice 3
              (code findings) or slice 1 (docs distillation, deletions owner-approved) via
              `/ai-org:spec --auto-build`.
