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

updated:      2026-09-22 (phone review depth built; PR opening) · commit: see branch feat/phone-review-depth · log-entry: "2026-09-22 — Phone review depth built (review card reach, replayer open/close, touch floor)"
position:     Every phone slice in the roadmap's NOW lane is merged (#229 P1, #230 S1, #231 P3a,
              #232 P4, #235 P3b + always-on). The phone review depth slice (NEXT) is built, gated,
              blind-reviewed and browser-verified on `feat/phone-review-depth`; its PR awaits the
              owner. The roadmap's remaining code item is the 6-max realism research, which cannot
              start without the owner's 6-max play notes. The flywheel roadmap still has one box open
              (Challenge-mode session to hand 200).
merged:       #229, #230, #231, #232, #235. The review-depth PR is not.
awaiting John: (a) merge the review-depth PR; (b) run `./scripts/always_on_install.sh` from the MAIN
              checkout (accept the Node firewall prompt once by hand first); (c) one Simulate hand
              on the phone — ticks P1 leg (a) and P4's cross-device leg — and the 20-hand landscape
              verdict; on the phone, finish a hand and tap "Review ↓", open a hand from History and
              come back to the same row (this slice's pass/fail); (d) a 6-max session with play
              notes, which unlocks the realism research; (e) Challenge mode to hand 200 (closes the
              flywheel roadmap); (f) stray dev servers the sandbox cannot kill:
              `kill $(lsof -ti:7790,7783,7791,7792,8131)`; (g) `agy` login or a plain-terminal Codex
              run if a cross-family review is wanted (every review this run was Claude-only).
authorized:   nothing standing. The `/ai-org:spec --auto-build phone review depth` invocation is fully
              spent. Owner merges every PR; Claude never merges.
next action:  after the owner has played on the phone and at 6-max: `/ai-org:spec` for the 6-max
              realism research (its shape is an owner call: reopen the paused persona-realism lane
              or run it under this roadmap), or History paging if the owner reaches for History on
              the phone. Nothing else in this roadmap is buildable without owner play.
