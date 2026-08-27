# AI-DLC profile — poker-coach

stack:        mixed — Python/FastAPI backend + React/Vite/strict-TS frontend
artifact_dir: docs/ai-dlc

# The governing initiative. A fresh session reads this first, opens that roadmap,
# and resumes from its first unchecked slice — never from memory of what seemed
# next. This field was missing entirely until 2026-08-18, which is why the boot
# checklist in .claude/CLAUDE.md kept pointing at a key that was not there.
active:       bot-realism-flywheel
              # roadmap: docs/ai-dlc/roadmap/bot-realism-flywheel.md
              # current slice: Two-mode Simulate (Training / Challenge) —
              #   spec'd 2026-08-26, awaiting owner approval at the plan gate.
              # slice 3 (calldown): play session PLAYED 2026-08-25 (1050 hands);
              #   OPEN pending only the owner's written per-persona verdict.
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

updated:      2026-08-26
position:     `/ai-org:spec` complete for **Two-mode Simulate** and STOPPED at the plan gate.
              Artifacts written, nothing built, no code touched: contract map
              `contracts/persona-label-toggle.md`, spec `specs/two-mode-simulate.md` (rev 2),
              ledger `ledger/two-mode-simulate.md`, tickets `tickets/two-mode-simulate.md`
              (T1–T8, one sequential chain), and roadmap rev 9 recording the owner's
              2026-08-26 rulings. Design canvas: "Simulate — Training vs Challenge".
reviews:      Round 1 dual, both blind. Claude refuter REJECT, Codex gpt-5.6-sol REJECT.
              Seventeen findings, all seventeen accepted, none rejected — the first draft
              asserted four things about the code that were false. Folded into spec rev 2.
authorized:   NOTHING. Approval covers no ticket. The owner has not approved the plan.
              It does NOT authorize: any edit outside `docs/ai-dlc/`, any migration, any
              commit, or any of T1–T8.
awaiting John: (a) approve or amend `tickets/two-mode-simulate.md`; (b) the written
              per-persona verdict that closes flywheel slice 3 — the 1050-hand session is
              already played, only the verdict is owed; (c) two theory-contract items still
              open from 2026-08-24 (ledger finding B1, and §10.2 of the git-excluded
              persona-realism audit).
uncommitted:  Everything above is UNCOMMITTED in a shared working tree that other sessions
              are also writing to. Nothing has been staged, committed or pushed.
