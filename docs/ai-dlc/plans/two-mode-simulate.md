# Team plan: Two-mode Simulate (Training / Challenge)

- initiative: bot-realism-flywheel
- slice: two-mode-simulate
- status: approved            # owner, 2026-08-26, explicit affirmative at the build go-gate
- spec: `../specs/two-mode-simulate.md` (rev 2)
- tickets: `../tickets/two-mode-simulate.md` (T1–T8)
- written: 2026-08-26

## 0. Bottom line

This plan builds the eight tickets of the Two-mode Simulate slice as **eight sequential
waves, one worker each**, on a single feature branch in a dedicated worktree. Nothing in the
chain parallelises: every backend ticket owns `sim_session.py` and every frontend ticket owns
`SimulateView.tsx`, so two workers can never be in flight at once.

What you are approving: **18 agent runs** — 8 implementation workers plus 10 reviewers — and
one Alembic migration (`0015`) against the local development database. No code has been
written yet. Nothing is pushed or merged without a further explicit confirmation.

The cost is the token spend of a long sequential chain (five Opus workers, three Sonnet
workers, and a reviewer at every fan-in, two of which drive a real browser). The gain is that
each ticket is verified against its own done-condition and independently checked before the
next one builds on it — which is what the seventeen accepted review findings on rev 1 of the
spec argue for.

## 1. Objective

Ship the slice exactly as `specs/two-mode-simulate.md` rev 2 defines it: a mode chosen at
sit-down, a Challenge mode that withholds every on-screen archetype reference until 200
completed hands, a server-enforced deal barrier at that point, a blind-check dialog, and a
two-way Labels toggle afterwards. Bot behaviour, grading, and what is recorded are unchanged.

## 2. Risk level

**Medium.** Three specific risks, each with a named containment:

- **Schema change on a populated database.** Both new columns are nullable and `NULL` reads as
  Training, following the repo's documented add-column pattern. T1's acceptance is an
  upgrade test against a database populated at revision `0014` with an *active* session.
- **An off-by-one at the gate boundary.** This is the defect rev 2 of the spec was written to
  correct. T3 is routed to an Opus worker and its acceptance asserts the derivation at 199,
  at live-200 and at settled-200 separately.
- **A shared, concurrently-used working tree.** Another session is writing to this checkout.
  All work happens in a separate worktree on its own branch; nothing is staged or committed in
  the main checkout.

## 3. Roster

| Wave | Ticket | Worker agent | Model | Effort (via agent pin) | Max concurrent |
|---|---|---|---|---|---|
| 1 | T1 — two nullable columns + migration `0015` | `implementer` | sonnet | medium | 1 |
| 2 | T2 — mode at creation, carried on every response | `implementer` | sonnet | medium | 1 |
| 3 | T3 — completed-hand count + server-side deal barrier | `heavy-worker` | opus | high | 1 |
| 4 | T4 — blind-check endpoint: seat pick, scoring, idempotency | `heavy-worker` | opus | high | 1 |
| 5 | T5 — frontend types and client calls | `implementer` | sonnet | medium | 1 |
| 6 | T6 — the mode-choice screen, on all three creation paths | `ux-ui-designer` | opus | high | 1 |
| 7 | T7 — the display gate and the Labels toggle | `heavy-worker` | opus | high | 1 |
| 8 | T8 — the hand-200 dialog and its score | `ux-ui-designer` | opus | high | 1 |

Effort is delivered by the agent's pinned `effort:` frontmatter, not by a parameter on the
spawn — `implementer` is pinned medium; `heavy-worker`, `ux-ui-designer`, `refuter` and
`design-reviewer` are pinned high. No worker is routed to Fable, and none of these tickets is
the long-horizon, low-oversight kind of work Fable exists for.

The Codex Terra worker pilot is **not run**: its precondition is roughly ten genuine automation
candidates in the next thirty tickets, and this slice has zero — every ticket modifies
application source logic, which is a hard exclusion. No per-ticket routing records are emitted.

## 4. Cost line

No foreman phase and no fan-out: every wave is a single worker spawned directly by the
Director, so the GATE.md cost-comparison for delegated crews does not apply. Peak concurrency
is two agents (a wave's two reviewers at a fan-in), well under the five-worker shape rule.

## 5. Mechanism

**Where the work happens.** One worktree for the whole slice, on branch
`feat/two-mode-simulate` cut from `origin/main`. The worktree gets a symlinked
`backend/.venv` and `frontend/node_modules` from the main checkout, both of which are
gitignored and therefore never committed. This was verified rather than assumed: `PYTHONPATH`
takes precedence over the venv's editable-install finder, so tests run against the worktree's
source and not the main checkout's.

**Dependency chain (read from the ticket file, not re-derived).**

`T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8`

**File ownership per wave** — one file, one owner, and no file is owned by two live workers
because only one worker is ever live:

| Wave | Owned files |
|---|---|
| 1 | `backend/app/db/models.py`, `backend/alembic/versions/0015_*.py`, its new test module |
| 2 | `backend/app/schemas/simulate.py`, `backend/app/api/v1/simulate.py`, `backend/app/services/sim_session.py` |
| 3 | `backend/app/services/sim_session.py`, its new test module |
| 4 | `backend/app/services/sim_session.py`, `backend/app/api/v1/simulate.py`, `backend/app/schemas/simulate.py`, its new test module |
| 5 | `frontend/src/api/types.ts`, `frontend/src/api/client.ts` |
| 6 | `frontend/src/components/simulate/SimModeChoice.tsx` (new), `frontend/src/components/SimulateView.tsx`, `frontend/src/styles/app.css` |
| 7 | `frontend/src/components/simulate/SimLabelsToggle.tsx` (new), `SimTable.tsx`, `SimLedger.tsx`, `SimRangeChart.tsx`, `SimulateView.tsx`, `app.css` |
| 8 | `frontend/src/components/simulate/SimBlindCheck.tsx` (new), `SimulateView.tsx`, `app.css` |

**Sealed briefs.** Each worker receives only its own ticket, the spec sections that ticket
depends on, the repo invariants, its runnable done-condition, its golden-path file to imitate,
and the engineering-standards block. No worker sees the other tickets' briefs, and no worker
spawns another worker.

**Documents.** The roadmap tick and the finding-ledger update are done by the Director at final
integration rather than by the wave-8 worker, because they need the whole chain's outcome.

## 6. Review approach

Maker is never checker. Every fan-in barrier runs the deterministic checks first
(`./scripts/verify.sh`, `ruff check .`, and for frontend waves `npm run typecheck && npm run
build`), and then a fresh reviewer that never saw the worker's reasoning:

| Wave | Reviewer(s) | Model |
|---|---|---|
| 1, 2 | `refuter` | sonnet |
| 3, 4 | `refuter` | opus — behaviour-touching |
| 5 | `refuter` | sonnet |
| 6 | `refuter` (routing logic) + `design-reviewer` (the new screen, both themes) | sonnet + opus |
| 7 | `refuter` | opus — cross-cutting display gate |
| 8 | `refuter` + `design-reviewer` (full flow, dialog, AA contrast, focus) | opus + opus |

No wave takes the Tier-0 exemption: not one of these tickets has acceptance criteria that the
deterministic checks fully cover on their own. Each fan-in records which checks ran, the
reviewer's verdict, and whether the spec or ticket needed re-amending.

**Two deliberate caps, stated rather than hidden.** The `design-reviewer` browser pass runs at
waves 6 and 8 only, not at wave 7 — wave 7's states require a session seeded to 200 hands,
which wave 8's pass reaches anyway with the seeded session it needs regardless. And the
`persona-realism-theory-reviewer` is not used: this slice changes no bot behaviour, so there is
no theory contract for it to check.

## 7. What this plan does not authorise

Pushing the branch, opening a pull request, and merging are separate steps. The repo's process
allows pushing and opening a PR on a `feat/*` branch autonomously; **merging always needs an
explicit confirmation** and is not covered here.
