# AI-DLC profile — poker-coach

stack:        mixed — Python/FastAPI backend + React/Vite/strict-TS frontend
artifact_dir: docs/ai-dlc

# The governing initiative. A fresh session reads this first, opens that roadmap,
# and resumes from its first unchecked slice — never from memory of what seemed
# next. This field was missing entirely until 2026-08-18, which is why the boot
# checklist in .claude/CLAUDE.md kept pointing at a key that was not there.
active:       bot-realism-flywheel
              # roadmap: docs/ai-dlc/roadmap/bot-realism-flywheel.md
              # current slice: improvement slice 2, invest-then-fold —
              #   spec/tickets/ledger under docs/ai-dlc/{specs,tickets,ledger}/
              #   phase3-invest-then-fold.md; spec'd, reviewed, NOT implemented.
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
