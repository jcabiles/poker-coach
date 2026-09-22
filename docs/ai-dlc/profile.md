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

updated:      2026-09-22 (always-on built; three-slice run complete) · commit: see branch feat/always-on-stack · log-entry: "2026-09-22 — Always-on stack built (launchd agent + owner-run install/uninstall), stacked on P3b"
position:     Three stacked PRs: #232 (P4, one live session across devices) → #233 (P3b, portrait
              polish) → always-on (launchd agent). Each is gated, reviewed and browser-checked where
              it has UI. Roadmap NOW is empty once these merge; NEXT holds 6-max realism research
              (needs the owner's play notes) and phone review depth (review card, stats, replayer).
merged:       #229 (P1), #230 (S1), #231 (P3a). #232, #233 and the always-on PR await the owner.
awaiting John: (a) merge in order: #232, then #233, then always-on — after each squash-merge the next
              PR shows the earlier commits until rebased; say "rebase" and a fresh branch + PR
              replaces it; (b) run `./scripts/always_on_install.sh` from the MAIN checkout after the
              merge, then confirm the stack returns within five minutes after sleep or `stop`;
              (c) one Simulate hand on the phone and the 20-hand landscape verdict; (d) stray dev servers that the sandbox cannot kill:
              `kill $(lsof -ti:7790,8127,7783)` (designer's vite; the P3b review stack); (e) `agy` login if Gemini review is wanted again.
authorized:   nothing standing. The 2026-09-22 `--auto-build` invocation is fully spent (P4, P3b,
              always-on). Owner merges every PR; Claude never merges.
next action:  after the merges: `/ai-org:spec --auto-build phone review depth` (review card → stats
              & leaks → replayer at phone size; owner ruled the order 2026-09-22) — or the 6-max
              realism research once the owner has played 6-max.
