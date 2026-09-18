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
              # next: cleanup quality gates (docs/cleanup-project-brief.md slice 2).
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

updated:      2026-09-18
commit:       branch `feat/two-mode-simulate` — pushed and merged 2026-09-18 (see git log)
log-entry:    "2026-09-18 — Two-mode Simulate merged; slice 3 closed; next: quality gates"
position:     **Two-mode Simulate is MERGED.** Fresh dual review (refuter + browser design
              review) both APPROVE-WITH-FIXES; the four should-fix findings fixed or recorded
              (ledger round 3). The slice's box stays unticked until the owner plays Challenge
              mode. **Flywheel slice 3 (calldown) is CLOSED** on the owner's 2026-09-18 verdict,
              which closes the improvement phase.
merged:       feat/two-mode-simulate (12 build commits + this session's review fixes).
awaiting John: (a) play Challenge mode to the hand-200 check, then tick the slice; (b) the
              finale detection run needs vendor keys and a go-ahead (not scheduled); (c) two
              theory-contract items open since 2026-08-24 (ledger finding B1, and §10.2 of the
              git-excluded persona-realism audit).
authorized:   Owner, 2026-09-18: merge this run's PRs once gates are green and a fresh reviewer
              approves (spent for this branch); next slice = cleanup quality gates
              (`docs/cleanup-project-brief.md` slice 2) with its new dev dependencies
              pre-approved. Nothing else. Lapses at the end of the 2026-09-18 session.
next action:  spec → dual review → tickets → build the quality-gates slice.
