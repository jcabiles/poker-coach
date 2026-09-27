# AI-DLC profile — poker-coach

stack:        mixed — Python/FastAPI backend + React/Vite/strict-TS frontend
artifact_dir: docs/ai-dlc

# The governing initiative. A fresh session reads this first, opens that roadmap,
# and resumes from its first unchecked slice — never from memory of what seemed
# next. This field was missing entirely until 2026-08-18, which is why the boot
# checklist in .claude/CLAUDE.md kept pointing at a key that was not there.
active:       bot-realism-6max
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

updated:      2026-09-27 (M1b spec approved via --auto-build; build started) · commit: 9d20026 · log-entry: "2026-09-27 — M1b spec rev 2 + tickets; build under --auto-build"
position:     M1 is merged (#242). M1b (bot settings that can differ by table size) has spec rev 2,
              contracts, ledger (8 findings, all adjudicated, none open) and tickets T1–T5 on
              branch `feat/m1b-table-size-settings` (worktree in this session's scratchpad). Build
              is in progress, strictly T1 → T2 → T3 → T4, then the Director's close-out T5.
merged:       #236–#242.
awaiting John: (a) Gemini login (`agy` once in a plain terminal): its fallback review timed out on
              auth, and Codex cannot reach its service from the sandbox, so M1b's reviews are
              Claude-only; (b) older items: the always-on agent fix, `git worktree prune`.
authorized:   M1b tickets T1–T5, pre-authorized by John's `--auto-build` invocation on 2026-09-27:
              build, test, live-app check, commit, push `feat/m1b-table-size-settings`, open a PR.
              NOT covered: merging, shipping any 6-max override file or settings value, M2, R1.
next action:  continue the M1b build from the first ticket without a commit on the branch; after
              the PR, John merges, then `/ai-org:spec M2 — retune the LAG at 6-max`.
