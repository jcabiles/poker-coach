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
position:     /ai-org:spec ceremony COMPLETE for `slice3-decisions-execution` (+ publication
              readiness). Owner ruled all six slice-3 filed decisions 2026-08-24 (record:
              research/slice3-calldown/owner-decisions.md, rulings in-session: D1 α
              per-range + delete all three per-bucket tests · D2 commit slope IN re-anchor
              scope · D3 fold lever parked at §4 P8 · D4 Filed-15 rule as §11 item 16,
              W3R-1 dual pattern · D5 acknowledged · D6 parked). Lane-B discovery: the
              statistics-ingestion NEXT item was ALREADY satisfied 2026-08-06 by
              poker-analytics registry v2 — roadmap entry is stale; reconciliation is
              ticket E3. Spec dual-reviewed (refuter + Codex Terra, both
              APPROVE-WITH-FIXES, 4 findings accepted+folded: ledger/slice3-decisions-execution.md).
awaiting John: Gate-2 build approval of tickets/slice3-decisions-execution.md (then /clear
              + /ai-org:build in a fresh session). Blind play session + finale keys remain
              separately owed and are NOT part of this spec.
authorized:   artifact writes under docs/ai-dlc only (spec/contracts/tickets/ledger/reviews
              + this block). NO code, NO engine/test edits, NO PRs yet — build authorization
              comes only from tickets/slice3-decisions-execution.md reading
              `status: approved`. Comment-only personas_postflop.py corrections are inside
              the approved-spec scope ONLY once build is authorized.

--- (prior resume, 2026-08-23, kept for provenance) ---
updated:      2026-08-23
commit:       0561e8f (main; engine/packs/frontend unchanged by wave 5 — docs-only close work on top)
log-entry:    wave 5 close packet, /ai-org:build ceremony 2026-08-23 (plan: docs/ai-dlc/plans/slice3-chain-autonomy.md)
position:     improvement slice 3 (calldown) BUILT — all five tickets merged (#211, #212, #215,
              #216, #217, #218); chain-wide WTSD measured (pooled −0.98pp harness / −1.5pp
              export); close packet, owner-decision memo, finale-readiness packet, and
              play-session checklist committed under docs/ai-dlc/research/slice3-calldown/.
merged:       coach #211–#218 (the build chain). The wave-5 close docs land via the PR that
              carries this very file (`chore/slice3-close-packet`) and the analytics
              pointer-refresh PR — if you are reading this on main, both are merged.
next action:  OWNER — blind play session (research/slice3-calldown/play-session-checklist.md);
              it closes slice 3 per the 2026-08-17 ruling. Then rule on the six filed decisions
              (research/slice3-calldown/owner-decisions.md — the α per-range question first).
              After acceptance: the single finale detection run (finale-readiness.md — keys +
              go-ahead are the only missing inputs). No build work is unblocked until then.
