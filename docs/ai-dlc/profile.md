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
commit:       branch `chore/slice3-decisions-execution` (base 2b4fefe = origin/main)
log-entry:    /ai-org:build of tickets/slice3-decisions-execution.md, Lane A + Lane B
position:     BUILD COMPLETE, all three tickets merged into the branch and a PR opened.
              The ticket file was approved 2026-08-24 for **Lane A + Lane B only** — chain 1,
              tickets E1 → E2 → E3, all in poker-coach. **Chain 2 (tickets P1–P4, the
              poker-analytics publication-readiness lane, which the spec calls Lane C) was
              NOT authorized and is still unbuilt** — it needs its own build run.
              E1: the six 2026-08-24 rulings recorded in the theory contract (amendment A9,
              a cross-reference on A8 item 5, a §4 row-P8 parking note, §11 item 16, the §7
              factor-order correction, §9 ledger entry 18). E2: the three tests enforcing the
              withdrawn per-bucket α rule deleted with their orphaned helpers, and the engine
              comments corrected — engine syntax tree proven identical, so zero behaviour
              change. E3: eleven dated adjudication notes in the slice-3 finding ledger, the
              two documents still asserting the withdrawn rule resolved, the roadmap's
              statistics-ingestion entry marked satisfied-2026-08-06 with four residual
              limitations, and a tree-wide sweep.
verified:     `./scripts/verify.sh` green on the branch — 2189 passed / 2 skipped / 0 xfailed,
              BACKEND VERIFY OK, ruff clean. That figure was predicted before any work started
              (baseline 2191 / 2 / 6, minus the 8 deleted cases) rather than fitted after.
reviews:      every wave reviewed by a fresh agent that never saw the maker's reasoning.
              E1 APPROVE-WITH-FIXES (2), E2 APPROVE (0), E3 APPROVE-WITH-FIXES (6, reviewer on
              Opus). All ten findings accepted and fixed before commit; ledger is
              ledger/slice3-decisions-execution.md, reports under reviews/.
owner still owes: (a) confirm or overrule ONE marked-unratified interpretation in the theory
              contract — how the commitment-slope ruling reconciles with amendment A6 (ledger
              finding B1); (b) correct §10.2 of research/persona-realism-audit-2026-07-24.md
              in the main checkout — it is git-excluded, so no branch can reach it, and it
              still carries the superseded multiplier order the contract now contradicts;
              (c) unchanged and NOT part of this build — the blind play session that closes
              slice 3, then the single finale detection run (vendor keys + go-ahead).
