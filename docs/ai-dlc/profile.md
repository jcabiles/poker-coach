# AI-DLC profile — poker-coach

stack:        mixed — Python/FastAPI backend + React/Vite/strict-TS frontend
artifact_dir: docs/ai-dlc

# The governing initiative. A fresh session reads this first, opens that roadmap,
# and resumes from its first unchecked slice — never from memory of what seemed
# next. This field was missing entirely until 2026-08-18, which is why the boot
# checklist in .claude/CLAUDE.md kept pointing at a key that was not there.
active:       bot-realism-flywheel
              # roadmap: docs/ai-dlc/roadmap/bot-realism-flywheel.md
              # current slice: improvement slice 3, calldown — BUILT (#211–#218)
              #   and close-packeted 2026-08-23; OPEN until the owner's blind
              #   play session. See ## Resume below.
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

updated:      2026-08-24
commit:       5cbf6cb on branch `chore/slice3-decisions-execution` (base 2b4fefe = origin/main)
log-entry:    /ai-org:build of tickets/slice3-decisions-execution.md, Lane A + Lane B
position:     BUILD IN PROGRESS. Ticket file approved 2026-08-24 for **Lane A + Lane B only**
              — that is chain 1, tickets E1 → E2 → E3, all in poker-coach. Chain 2 (tickets
              P1–P4, the poker-analytics publication-readiness lane, which the spec calls
              Lane C) was NOT authorized in this run and is still unbuilt.
              Wave 1 (E1) CLOSED: the owner's six 2026-08-24 rulings are recorded in
              contracts/persona-realism-theory-contract.md as amendment A9, a cross-reference
              on A8 item 5, a §4 row-P8 parking note, §11 item 16, a §7 factor-order
              correction and §9 ledger entry 18. Reviewed APPROVE-WITH-FIXES, two findings
              accepted and fixed pre-commit (reviews/slice3-decisions-execution-build-e1.md).
              Wave 2 (E2, the test deletions) and wave 3 (E3, ledger and roadmap) still owed.
baseline:     before E2, `./scripts/verify.sh` is green at 2191 passed / 2 skipped / 6 xfailed;
              tests/test_personas_postflop.py alone collects 401. E2 deletes 8 cases, so a
              correct E2 lands 2189 passed / 2 skipped / 0 xfailed.
owner still owes (unchanged, NOT part of this build): the blind play session that closes
              slice 3 (research/slice3-calldown/play-session-checklist.md), then the single
              finale detection run (research/slice3-calldown/finale-readiness.md — vendor
              keys and a go-ahead are its only missing inputs).
